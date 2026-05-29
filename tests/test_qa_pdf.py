"""QA pair 25 / worker YY-3 / subsystem 9 — client-PDF renderer QA pass.

Designed scenarios (2 POS + 2 NEG + 3 EDGE = 7 scenarios; some scenarios
exercise more than one assertion). Cover, executive summary tiles, cost
breakdown, bid alternates section toggle, branding from
``config/client_quote.json``, empty-state ("No priced lines yet"), and
section toggle config are the surface of interest.

Findings discovered while writing these tests are filed as
``pytest.mark.xfail(reason="QA-3 finding #N: ...")`` per the brief — no
bug fixes ship in this slice.

Findings surfaced (cross-ref docs/QA_REPORT_EXPORTS_2026-05-28.md):

* **B3-2** — ``QuoteConfig`` schema (core.schemas) does NOT declare an
  ``alternates_section`` field. ``QuoteConfig.model_validate(raw)``
  therefore drops the ``alternates_section`` block from
  ``config/client_quote.json`` silently. The renderer accepts an
  ``alternates_config`` kwarg on ``build_quote_pdf`` (see
  :func:`core.exporter_pdf._render_alternates_section`) but there is no
  ergonomic way to thread the JSON config through ``QuoteConfig`` —
  callers must parse the JSON twice. Severity: LOW (workaround exists)
  but it is a UX-shaped foot-gun.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")
fitz = pytest.importorskip("fitz")  # PyMuPDF

from core.exporter_pdf import (  # noqa: E402
    ALTERNATES_SECTION_TITLE,
    EMPTY_STATE_BANNER_TEXT,
    build_quote_pdf,
)
from core.schemas import (  # noqa: E402
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CompanyInfo,
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


def _project(
    *,
    project_info: ProjectInfo | None = None,
) -> ProjectModel:
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
        project_info=project_info or ProjectInfo(
            name="QA-3 PDF Project", number="2026-QA3", location="Austin, TX"
        ),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _line(
    *,
    description: str = "Painting",
    confidence: float = 0.92,
    total: float = 10_000.0,
    suppressed: bool = False,
    cost_category: CostCategory = CostCategory.LABOR,
) -> CostLine:
    qty = 100.0
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description=description,
        quantity=qty,
        unit="SF",
        unit_cost=total / qty if total else 0.0,
        total_cost=total,
        cost_category=cost_category,
        confidence=confidence,
        suppressed=suppressed,
    )


def _ale(
    alt_id: str,
    alt_type: AlternateType = AlternateType.ADDITIVE,
    cost: float | None = 1_000.0,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alt_id,
        alternate_type=alt_type,
        description=f"Alternate {alt_id}",
        cost_delta=cost,
        pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
    )


def _quote_config(*, company_name: str = "Quality Builders LLC") -> QuoteConfig:
    return QuoteConfig(
        company=CompanyInfo(name=company_name),
        quote_meta=QuoteMeta(
            scope_blurb="Furnish all labor and materials.",
            payment_terms_text="Net 30.",
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


def _pdf_text(path: Path) -> str:
    with fitz.open(path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _pdf_text_flat(path: Path) -> str:
    return " ".join(_pdf_text(path).split())


def _build(
    estimate: Estimate,
    out: Path,
    *,
    project: ProjectModel | None = None,
    config: QuoteConfig | None = None,
    alternates_config: dict | None = None,
) -> Path:
    return build_quote_pdf(
        estimate=estimate,
        project=project or _project(),
        quote_config=config or _quote_config(),
        out_path=out,
        csi_titles={"09": "Finishes"},
        alternates_config=alternates_config,
    )


# ---------------------------------------------------------------------------
# Subsystem 9 — Client PDF renderer
# ---------------------------------------------------------------------------


class TestQAPdfPositive:
    """Scenario QA9-P-1, QA9-P-2 — full estimate + alternate-bearing
    estimate must render the canonical sections."""

    def test_qa_pdf_p1_full_estimate_renders_cover_tiles_breakdown_payment(
        self, tmp_path: Path
    ) -> None:
        """QA9-P-1: priced estimate renders cover (company name, project
        name), three cost-category tiles, CSI breakdown, and the payment
        schedule heading."""
        est = Estimate(
            project_name="QA-3 Full",
            line_items=[
                _line(description="Labor 1", total=5_000.0,
                      cost_category=CostCategory.LABOR),
                _line(description="Material 1", total=3_000.0,
                      cost_category=CostCategory.MATERIAL),
                _line(description="Sub 1", total=2_000.0,
                      cost_category=CostCategory.SUBCONTRACTOR),
            ],
        )
        out = _build(est, tmp_path / "p1_full.pdf")
        assert out.is_file()
        text = _pdf_text(out)
        flat = _pdf_text_flat(out)

        # Header: project + company
        assert "QA-3 Full" in text
        assert "Quality Builders LLC" in text
        # Three tiles
        assert "LABOR" in text
        assert "MATERIAL" in text
        assert "SUBCONTRACTOR" in text
        # Cost breakdown
        assert "Cost breakdown by CSI division" in text
        assert "Cost breakdown by category" in flat
        # Payment schedule
        assert "Payment schedule" in text
        # No empty-state banner
        assert EMPTY_STATE_BANNER_TEXT not in text

    def test_qa_pdf_p2_alternates_section_renders_between_breakdown_and_payment(
        self, tmp_path: Path
    ) -> None:
        """QA9-P-2: when the estimate carries alternates, the Bid Alternates
        section must land AFTER 'Cost breakdown by CSI division' and
        BEFORE 'Payment schedule' (per Phase T9.2 insertion contract)."""
        est = Estimate(
            project_name="QA-3 Alts",
            line_items=[_line(total=10_000.0)],
            alternates=[_ale("Alt 1", AlternateType.ADDITIVE, 1_000.0)],
            alternates_selected_default={"Alt 1"},
        )
        out = _build(est, tmp_path / "p2_alts.pdf")
        text = _pdf_text(out)
        cost_idx = text.find("Cost breakdown by CSI division")
        alts_idx = text.find(ALTERNATES_SECTION_TITLE)
        pay_idx = text.find("Payment schedule")
        assert cost_idx >= 0
        assert alts_idx >= 0
        assert pay_idx >= 0
        assert cost_idx < alts_idx < pay_idx, (
            f"section order incorrect: cost={cost_idx} alts={alts_idx} pay={pay_idx}"
        )
        assert "Alt 1" in text


class TestQAPdfNegative:
    """Scenario QA9-N-1, QA9-N-2 — degraded inputs."""

    def test_qa_pdf_n1_all_suppressed_renders_empty_state_banner_not_zero_tiles(
        self, tmp_path: Path
    ) -> None:
        """QA9-N-1: every CostLine suppressed → the exec summary swaps in
        the empty-state banner. Crucially: no ``$0.00`` tiles in the
        rendered text (which would look broken to a client)."""
        est = Estimate(
            project_name="QA-3 Suppressed",
            line_items=[
                _line(description="bad-1", total=0.0, suppressed=True),
                _line(description="bad-2", total=0.0, suppressed=True),
            ],
        )
        out = _build(est, tmp_path / "n1_suppressed.pdf")
        text = _pdf_text(out)
        assert EMPTY_STATE_BANNER_TEXT in text
        # The three tile labels (LABOR / MATERIAL / SUBCONTRACTOR) live
        # ONLY on the three-tile flow; the empty-state banner replaces
        # them entirely. If any of the labels appear in the rendered
        # text, the renderer failed to swap them out and the client
        # would see misleading $0.00 tiles.
        for tile_label in ("LABOR", "MATERIAL", "SUBCONTRACTOR"):
            assert tile_label not in text, (
                f"tile label {tile_label!r} present despite all-suppressed "
                f"state; empty-state banner failed to suppress the tile flow"
            )

    def test_qa_pdf_n2_missing_client_quote_json_falls_back_to_defaults(
        self, tmp_path: Path
    ) -> None:
        """QA9-N-2: the renderer accepts a default-constructed ``QuoteConfig``
        (the analyze.py fallback path when ``config/client_quote.json`` is
        missing) and produces a valid PDF without crash."""
        default_cfg = QuoteConfig()  # all skeleton defaults
        est = Estimate(
            project_name="QA-3 Default",
            line_items=[_line(total=1_234.0)],
        )
        out = build_quote_pdf(
            estimate=est,
            project=_project(),
            quote_config=default_cfg,
            out_path=tmp_path / "n2_default.pdf",
            csi_titles={"09": "Finishes"},
        )
        assert out.is_file()
        head = out.read_bytes()[:5]
        assert head == b"%PDF-", "PDF did not get a valid file header"


class TestQAPdfEdge:
    """Scenario QA9-E-1, QA9-E-2, QA9-E-3 — branding asset missing,
    section toggle, special chars in project name."""

    def test_qa_pdf_e1_missing_logo_path_does_not_crash(
        self, tmp_path: Path
    ) -> None:
        """QA9-E-1: ``CompanyInfo.logo_path`` pointing at a non-existent
        file must NOT crash the render. The logger emits a warning and
        the cover renders without the logo."""
        cfg = _quote_config()
        cfg.company.logo_path = str(tmp_path / "this-file-does-not-exist.png")
        est = Estimate(
            project_name="QA-3 Logo Missing",
            line_items=[_line(total=5_000.0)],
        )
        out = _build(est, tmp_path / "e1_logo.pdf", config=cfg)
        assert out.is_file()
        text = _pdf_text(out)
        # Company name still surfaces on the cover.
        assert "Quality Builders LLC" in text

    def test_qa_pdf_e2_alternates_section_disabled_via_config_omits_section(
        self, tmp_path: Path
    ) -> None:
        """QA9-E-2: ``alternates_config={'enabled': False}`` omits the
        section even when the estimate carries priced alternates. This
        is the renderer-side toggle; see B3-1 (separate finding) for
        the analyze.py CLI wiring gap that prevents
        ``config/client_quote.json`` from reaching this kwarg today."""
        est = Estimate(
            project_name="QA-3 Alts Off",
            line_items=[_line(total=10_000.0)],
            alternates=[_ale("Alt 1", AlternateType.ADDITIVE, 1_000.0)],
        )
        out = _build(
            est,
            tmp_path / "e2_alts_off.pdf",
            alternates_config={"enabled": False},
        )
        text = _pdf_text(out)
        assert ALTERNATES_SECTION_TITLE not in text
        assert "Alt 1" not in text

    def test_qa_pdf_e3_reserved_chars_in_project_name_escaped(
        self, tmp_path: Path
    ) -> None:
        """QA9-E-3: project name with PDF/HTML-reserved chars (``&`` /
        ``<`` / ``(`` / ``)``) must render without crashing the
        ReportLab Paragraph parser AND must round-trip through the
        cover page text extraction.

        ReportLab's Paragraph engine treats raw ``<`` / ``&`` as XML
        markers; our cover renderer hands the project name to
        Paragraph via the project_tbl row, so an unescaped ``&`` would
        raise. This test ensures the renderer is hardened.
        """
        wild = "Quote <2026> & Co. (Q3) — \u00a9"
        est = Estimate(
            project_name=wild,
            line_items=[_line(total=2_500.0)],
        )
        out = _build(est, tmp_path / "e3_chars.pdf")
        text = _pdf_text(out)
        # All four reserved tokens must appear in the rendered text
        # (escaped on the way in, rendered as-is on the way out).
        for token in ("<2026>", "&", "(Q3)", "\u00a9"):
            assert token in text, f"missing {token!r} in rendered PDF text"

    @pytest.mark.xfail(
        reason=(
            "QA-3 finding B3-2: QuoteConfig schema lacks an "
            "'alternates_section' field. Pydantic model_validate(raw) "
            "silently drops the block from config/client_quote.json — "
            "any downstream caller that loads the config and assumes "
            "cfg.alternates_section.enabled is reachable will fail. "
            "Workaround exists (parse the JSON twice), but the schema "
            "should accept the block natively. Fix: add an "
            "AlternatesSectionConfig nested model on QuoteConfig."
        ),
        strict=True,
    )
    def test_qa_pdf_e4_quote_config_carries_alternates_section_field(self) -> None:
        """QA9-E-4: ``config/client_quote.json`` ships an
        ``alternates_section`` block. Loading the file through
        ``QuoteConfig.model_validate`` should preserve that block as a
        first-class field. Currently FAILS — Pydantic silently drops
        unknown keys, so the section config never reaches the renderer
        through the normal load path."""
        raw_path = Path("config/client_quote.json")
        assert raw_path.is_file(), "config/client_quote.json should ship with the repo"
        raw = json.loads(raw_path.read_text(encoding="utf-8"))
        assert "alternates_section" in raw, "fixture sanity"
        cfg = QuoteConfig.model_validate(raw)
        # The strict-mode XFAIL fires here: the field does not exist on
        # the model. We hasattr-check rather than attribute-access so the
        # AttributeError doesn't itself short-circuit before the assert.
        assert hasattr(cfg, "alternates_section"), (
            "QuoteConfig should declare an 'alternates_section' field"
        )
