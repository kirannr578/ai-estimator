"""Phase T9.2 — client PDF Bid Alternates section integration tests.

Builds a real PDF via :func:`core.exporter_pdf.build_quote_pdf` and
inspects the rendered text via PyMuPDF (``fitz``) — same pattern
``tests/test_pdf_empty_state.py`` uses. PyMuPDF is already a project
dependency so we get reliable Type-1-font-aware text extraction (the
section text contains an em-dash and a Unicode ellipsis that a naive
byte scan would miss).

Coverage:

* zero alternates → section omitted entirely
* single ADDITIVE → section + base/with-additive tally render
* mixed types → table sorted, all relevant tally rows present
* MISSING-basis → ``"$_____"`` placeholder
* selected vs default → tally reflects selection set
* long description → truncated body in table + full text in footnote
* operator notes appear in Notes column
* section appears between Cost Breakdown and Payment Schedule
* VE rendered with negative delta (same as DEDUCTIVE numerically)
* region multiplier baked into tally
* footer note rendered
* ``alternates_section.enabled = False`` skips the section
* custom intro / footer / default_selection from config
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")
fitz = pytest.importorskip("fitz")  # PyMuPDF; already a project dep

from core.estimator import attach_alternates_to_estimate  # noqa: E402
from core.exporter_pdf import (  # noqa: E402
    ALTERNATES_SECTION_TITLE,
    ALTERNATES_TALLY_HEADING,
    DEFAULT_ALTERNATES_FOOTER_NOTE,
    DEFAULT_ALTERNATES_INTRO_PARAGRAPH,
    build_quote_pdf,
)
from core.schemas import (  # noqa: E402
    AlternateLine,
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CostCategory,
    CostLine,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    SiteInfo,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _project(alternates: list[AlternateLine] | None = None) -> ProjectModel:
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=[],
        sheet_summaries={},
        warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(
            name="T9.2 Sample", number="2026-099", location="Austin, TX"
        ),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=alternates or [],
    )


def _line(total: float = 10_000.0, division: str = "09") -> CostLine:
    return CostLine(
        csi_division=division,
        csi_section=f"{division} 91 23",
        description="Painting",
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


def _ale(
    alt_id: str,
    alt_type: AlternateType = AlternateType.ADDITIVE,
    cost: float | None = 1000.0,
    description: str = "",
    notes: str | None = None,
    pricing_basis: AlternatePricingBasis = AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alt_id,
        alternate_type=alt_type,
        description=description or f"Alternate {alt_id}",
        cost_delta=cost,
        pricing_basis=pricing_basis,
        operator_notes=notes,
    )


def _estimate(
    alts: list[AlternateLineEstimate],
    *,
    region_multiplier: float = 1.0,
    selected_default: set[str] | None = None,
) -> Estimate:
    return Estimate(
        project_name="T9.2 Sample",
        region_multiplier=region_multiplier,
        line_items=[_line(total=10_000.0)],
        alternates=alts,
        alternates_selected_default=selected_default or set(),
    )


def _config() -> QuoteConfig:
    return QuoteConfig(
        quote_meta=QuoteMeta(
            scope_blurb="Test scope blurb.", payment_terms_text="Net 30."
        ),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="Mobilization", percentage=30.0),
                PaymentMilestone(label="Rough-in", percentage=30.0),
                PaymentMilestone(label="Finish", percentage=30.0),
                PaymentMilestone(label="Retainage", percentage=10.0),
            ],
        ),
    )


def _build(
    estimate: Estimate,
    out_path: Path,
    *,
    alternates_config: dict | None = None,
) -> Path:
    return build_quote_pdf(
        estimate=estimate,
        project=_project(),
        quote_config=_config(),
        out_path=out_path,
        csi_titles={"09": "Finishes"},
        alternates_config=alternates_config,
    )


def _pdf_text(pdf_path: Path) -> str:
    """Return ALL extracted text concatenated.

    PyMuPDF preserves layout newlines, which fragment paragraphs and
    table cells across line-wrap boundaries. Tests that search for a
    multi-word phrase should use :func:`_pdf_text_flat` instead, which
    collapses every whitespace run to a single space so the phrase
    survives the wrap.
    """
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _pdf_text_flat(pdf_path: Path) -> str:
    """Whitespace-collapsed text for substring matching across line wraps."""
    raw = _pdf_text(pdf_path)
    return " ".join(raw.split())


# ---------------------------------------------------------------------------
# Visibility / skip rules
# ---------------------------------------------------------------------------


class TestSectionVisibility:
    def test_zero_alternates_section_omitted(self, tmp_path: Path) -> None:
        est = _estimate([])
        out = _build(est, tmp_path / "no_alts.pdf")
        text = _pdf_text(out)
        assert ALTERNATES_SECTION_TITLE not in text
        # Sanity: the unrelated content still rendered.
        assert "Cost breakdown" in text or "Payment" in text

    def test_single_additive_renders_section(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", AlternateType.ADDITIVE, 5000.0)])
        out = _build(est, tmp_path / "single.pdf")
        text = _pdf_text(out)
        assert ALTERNATES_SECTION_TITLE in text
        assert "Alt 1" in text

    def test_section_renders_subtitle(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "subtitle.pdf")
        text = _pdf_text(out)
        assert "Owner-option items priced separately from the base bid" in text

    def test_section_renders_default_intro(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "intro.pdf")
        # Use flat text — paragraph wraps at column boundaries.
        text = _pdf_text_flat(out)
        # Distinct sentinel from the default intro paragraph.
        assert "owner may elect to include any combination" in text

    def test_section_renders_default_footer_note(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "footer.pdf")
        text = _pdf_text_flat(out)
        assert "expire 60 days from this proposal date" in text

    def test_section_renders_tally_heading(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "tally_h.pdf")
        text = _pdf_text(out)
        assert ALTERNATES_TALLY_HEADING in text

    def test_section_disabled_via_config(self, tmp_path: Path) -> None:
        """``alternates_section.enabled = False`` skips the entire section."""
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "off.pdf", alternates_config={"enabled": False})
        text = _pdf_text(out)
        assert ALTERNATES_SECTION_TITLE not in text


# ---------------------------------------------------------------------------
# Section ordering (Cost Breakdown → Bid Alternates → Payment Schedule)
# ---------------------------------------------------------------------------


def test_section_appears_between_cost_breakdown_and_payment_schedule(
    tmp_path: Path,
) -> None:
    """Bid Alternates must appear AFTER 'Cost breakdown' and BEFORE 'Payment schedule'."""
    est = _estimate([
        _ale("Alt 1", AlternateType.ADDITIVE, 1000.0),
    ])
    out = _build(est, tmp_path / "order.pdf")
    text = _pdf_text(out)
    cost_idx = text.find("Cost breakdown by CSI division")
    alts_idx = text.find(ALTERNATES_SECTION_TITLE)
    pay_idx = text.find("Payment schedule")
    assert cost_idx >= 0, "Cost breakdown heading missing"
    assert alts_idx >= 0, "Bid Alternates heading missing"
    assert pay_idx >= 0, "Payment schedule heading missing"
    assert cost_idx < alts_idx < pay_idx, (
        f"Section order incorrect: cost={cost_idx} alts={alts_idx} pay={pay_idx}"
    )


# ---------------------------------------------------------------------------
# Table content
# ---------------------------------------------------------------------------


class TestAlternatesTable:
    def test_renders_short_type_label_add(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", AlternateType.ADDITIVE, 1000.0)])
        out = _build(est, tmp_path / "label_add.pdf")
        text = _pdf_text(out)
        # Short "Add" appears in the Type column. Use a fairly specific
        # check by anchoring on the alternate ID being on the same page.
        assert "Add" in text
        assert "Alt 1" in text

    def test_table_sorted_by_type(self, tmp_path: Path) -> None:
        """Mixed types must surface in ADDITIVE → SUBSTITUTION → VE → DEDUCTIVE order."""
        est = _estimate([
            _ale("Alt-DED", AlternateType.DEDUCTIVE, -1000.0),
            _ale("Alt-VE", AlternateType.VE, -500.0),
            _ale("Alt-SUB", AlternateType.SUBSTITUTION, 200.0),
            _ale("Alt-ADD", AlternateType.ADDITIVE, 800.0),
        ])
        out = _build(est, tmp_path / "sorted.pdf")
        text = _pdf_text(out)
        # The IDs land in column-0 in sort order; check first-occurrence indices.
        idx_add = text.find("Alt-ADD")
        idx_sub = text.find("Alt-SUB")
        idx_ve = text.find("Alt-VE")
        idx_ded = text.find("Alt-DED")
        assert 0 < idx_add < idx_sub < idx_ve < idx_ded, (
            f"Order wrong: add={idx_add} sub={idx_sub} ve={idx_ve} ded={idx_ded}"
        )

    def test_missing_basis_renders_placeholder(self, tmp_path: Path) -> None:
        est = _estimate([
            _ale(
                "Alt M",
                AlternateType.ADDITIVE,
                cost=None,
                pricing_basis=AlternatePricingBasis.MISSING,
            ),
        ])
        out = _build(est, tmp_path / "missing.pdf")
        text = _pdf_text(out)
        assert "$_____" in text

    def test_long_description_truncated_with_footnote(self, tmp_path: Path) -> None:
        long_desc = (
            "Substitute 24-gauge standing-seam metal roof panels for the "
            "specified asphalt shingles assembly across the entire roof "
            "area on all three buildings, with all flashings and trims as "
            "needed."
        )
        est = _estimate([
            _ale(
                "Alt 1",
                AlternateType.SUBSTITUTION,
                300.0,
                description=long_desc,
            )
        ])
        out = _build(est, tmp_path / "trunc.pdf")
        text = _pdf_text_flat(out)
        # Full description must appear in the footnote even when truncated.
        assert long_desc in text
        # The truncated form (containing the ellipsis) should also appear —
        # check raw text since the ellipsis itself is a single character.
        assert "\u2026" in _pdf_text(out)
        # The "full description" footnote sentinel must be present.
        assert "full description" in text

    def test_short_description_no_footnote(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0, description="Short add")])
        out = _build(est, tmp_path / "short.pdf")
        text = _pdf_text(out)
        # No "full description:" footnote phrase when nothing was truncated.
        assert "full description" not in text

    def test_operator_notes_appear_in_notes_column(self, tmp_path: Path) -> None:
        est = _estimate([
            _ale(
                "Alt 1",
                AlternateType.ADDITIVE,
                500.0,
                notes="Owner verbal preference; confirm before submittal.",
            )
        ])
        out = _build(est, tmp_path / "notes.pdf")
        text = _pdf_text_flat(out)
        assert "Owner verbal preference" in text
        assert "confirm before submittal" in text

    def test_cost_delta_signed_format_positive(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", AlternateType.ADDITIVE, 1234.56)])
        out = _build(est, tmp_path / "pos.pdf")
        text = _pdf_text(out)
        assert "+$1,234.56" in text

    def test_cost_delta_signed_format_negative(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", AlternateType.DEDUCTIVE, -987.65)])
        out = _build(est, tmp_path / "neg.pdf")
        text = _pdf_text(out)
        assert "-$987.65" in text

    def test_ve_renders_negative_delta(self, tmp_path: Path) -> None:
        est = _estimate([_ale("VE-1", AlternateType.VE, -1500.00)])
        out = _build(est, tmp_path / "ve.pdf")
        text = _pdf_text(out)
        # VE displays as a separate type label (not "Deduct").
        assert "VE" in text
        assert "-$1,500.00" in text


# ---------------------------------------------------------------------------
# Tally section
# ---------------------------------------------------------------------------


class TestTallySection:
    def test_tally_includes_base_bid_row(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "tally_base.pdf")
        text = _pdf_text(out)
        assert "Base bid (no alternates)" in text

    def test_tally_includes_selected_row(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "tally_sel.pdf")
        text = _pdf_text(out)
        assert "Base + selected alternates" in text

    def test_tally_omits_deductive_when_absent(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", AlternateType.ADDITIVE, 500.0)])
        out = _build(est, tmp_path / "tally_no_ded.pdf")
        text = _pdf_text(out)
        assert "Base + all additive alternates" in text
        assert "Base + all deductive alternates" not in text
        assert "Base + all VE items" not in text

    def test_tally_includes_ve_row_when_present(self, tmp_path: Path) -> None:
        est = _estimate([_ale("VE-1", AlternateType.VE, -300.0)])
        out = _build(est, tmp_path / "tally_ve.pdf")
        text = _pdf_text(out)
        assert "Base + all VE items" in text

    def test_tally_default_selection_uses_estimate_default(
        self, tmp_path: Path
    ) -> None:
        """The estimate's `alternates_selected_default` drives the Selected row."""
        est = _estimate(
            [
                _ale("Alt 1", AlternateType.ADDITIVE, 500.0),
                _ale("Alt 2", AlternateType.ADDITIVE, 300.0),
            ],
            selected_default={"Alt 1"},
        )
        out = _build(est, tmp_path / "tally_default.pdf")
        text = _pdf_text(out)
        # Selection delta = +$500.00 (only Alt 1 selected).
        assert "+$500.00" in text

    def test_tally_default_selection_overridden_by_config(
        self, tmp_path: Path
    ) -> None:
        """``alternates_section.default_selection`` overrides the estimate default."""
        est = _estimate(
            [
                _ale("Alt 1", AlternateType.ADDITIVE, 500.0),
                _ale("Alt 2", AlternateType.ADDITIVE, 300.0),
            ],
            selected_default={"Alt 1"},
        )
        out = _build(
            est,
            tmp_path / "tally_override.pdf",
            alternates_config={"default_selection": ["Alt 1", "Alt 2"]},
        )
        text = _pdf_text(out)
        # With both selected, delta = +$800.00.
        assert "+$800.00" in text


# ---------------------------------------------------------------------------
# Region multiplier integration
# ---------------------------------------------------------------------------


def test_region_multiplier_applied_to_tally_via_attach(tmp_path: Path) -> None:
    """`attach_alternates_to_estimate` already bakes the region multiplier
    into each `cost_delta`, so the rendered tally must reflect the
    scaled deltas without the renderer doing any extra scaling."""
    base_est = Estimate(
        project_name="T9.2",
        region_multiplier=1.10,
        line_items=[_line(total=10_000.0)],
    )
    project = _project(
        alternates=[
            AlternateLine(
                alternate_id="Alt 1",
                description="Add foo",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=1000.0,
            )
        ]
    )
    est = attach_alternates_to_estimate(base_est, project)
    # Sanity: 1000 × 1.10 = 1100.
    assert est.alternates[0].cost_delta == 1100.0

    out = build_quote_pdf(
        estimate=est,
        project=project,
        quote_config=_config(),
        out_path=tmp_path / "region.pdf",
        csi_titles={"09": "Finishes"},
    )
    text = _pdf_text(out)
    assert "+$1,100.00" in text


# ---------------------------------------------------------------------------
# Custom text overrides via alternates_config
# ---------------------------------------------------------------------------


class TestCustomConfigOverrides:
    def test_custom_intro_paragraph_replaces_default(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(
            est,
            tmp_path / "custom_intro.pdf",
            alternates_config={
                "intro_paragraph": "CUSTOM intro paragraph specific to this proposal."
            },
        )
        text = _pdf_text(out)
        assert "CUSTOM intro paragraph specific to this proposal." in text
        # Default intro must NOT appear.
        assert (
            DEFAULT_ALTERNATES_INTRO_PARAGRAPH not in text
        ), "Custom intro should replace the default, not append"

    def test_custom_footer_note_replaces_default(self, tmp_path: Path) -> None:
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(
            est,
            tmp_path / "custom_footer.pdf",
            alternates_config={"footer_note": "CUSTOM footer note for legal review."},
        )
        text = _pdf_text(out)
        assert "CUSTOM footer note for legal review." in text
        assert DEFAULT_ALTERNATES_FOOTER_NOTE not in text

    def test_empty_config_uses_defaults(self, tmp_path: Path) -> None:
        """An empty dict (no overrides) still renders the section with defaults."""
        est = _estimate([_ale("Alt 1", cost=500.0)])
        out = _build(est, tmp_path / "empty_cfg.pdf", alternates_config={})
        assert ALTERNATES_SECTION_TITLE in _pdf_text(out)
        assert "owner may elect to include any combination" in _pdf_text_flat(out)


# ---------------------------------------------------------------------------
# End-to-end smoke
# ---------------------------------------------------------------------------


def test_build_quote_pdf_renders_with_full_alternates_set(tmp_path: Path) -> None:
    """All four alternate types + a MISSING line + multiple per type — the
    PDF must build cleanly and surface every section element."""
    est = _estimate(
        [
            _ale("Alt 1", AlternateType.ADDITIVE, 5000.0, description="Add epoxy"),
            _ale("Alt 2", AlternateType.ADDITIVE, 3000.0, description="Add doors"),
            _ale("Alt 3", AlternateType.DEDUCTIVE, -2000.0, description="Deduct skylight"),
            _ale(
                "Alt 4",
                AlternateType.SUBSTITUTION,
                300.0,
                description="LVT for VCT",
            ),
            _ale("VE-1", AlternateType.VE, -1200.0, description="VE roofing"),
            _ale(
                "Alt 5",
                AlternateType.ADDITIVE,
                cost=None,
                description="Owner-priced option",
                pricing_basis=AlternatePricingBasis.MISSING,
            ),
        ],
        selected_default={"Alt 1"},
    )
    out = _build(est, tmp_path / "full_smoke.pdf")
    assert out.is_file()
    head = out.read_bytes()[:5]
    assert head == b"%PDF-"
    text = _pdf_text(out)
    flat = _pdf_text_flat(out)
    for alt_id in ["Alt 1", "Alt 2", "Alt 3", "Alt 4", "VE-1", "Alt 5"]:
        assert alt_id in text, f"missing {alt_id} in PDF"
    assert "Base + all additive alternates" in flat
    assert "Base + all deductive alternates" in flat
    assert "Base + all VE items" in flat
    assert "Base + selected alternates" in flat
    assert "$_____" in text
    assert "expire 60 days from this proposal date" in flat
