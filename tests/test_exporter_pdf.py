"""Smoke test for the client-quote PDF builder (F12/F15).

Builds a PDF against a hand-crafted minimal `Estimate` + `ProjectModel` and
asserts that:
  * the file is non-empty (reportlab actually wrote bytes)
  * the byte stream starts with the PDF magic header `%PDF-`

This is intentionally a single, fast test — the full layout is exercised
visually by the user via the Streamlit "Client Quote" tab.
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")  # skip cleanly if not installed

from core.exporter_pdf import (  # noqa: E402
    _band_subscript_text,
    _render_band_tiles,
    build_quote_pdf,
)
from core.schemas import (  # noqa: E402
    CostBand,
    CostCategory,
    CostLine,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    SiteInfo,
    band_for_confidence,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix  # noqa: E402


def _minimal_project() -> ProjectModel:
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
            name="Sample Renovation",
            number="2026-001",
            location="Austin, TX",
        ),
        scope_matrix=ScopeMatrix(packages=[], by_division={}, all_alternates=[], coverage_warnings=[]),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _minimal_estimate() -> Estimate:
    return Estimate(
        project_name="Sample Renovation",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            CostLine(
                csi_division="03",
                csi_section="03 30 00",
                description="Slab on grade",
                quantity=1000.0,
                unit="SF",
                unit_cost=8.50,
                total_cost=8500.0,
                cost_category=CostCategory.MATERIAL,
            ),
            CostLine(
                csi_division="06",
                csi_section="06 10 00",
                description="Wood framing",
                quantity=1000.0,
                unit="SF",
                unit_cost=12.00,
                total_cost=12000.0,
                cost_category=CostCategory.LABOR,
            ),
            CostLine(
                csi_division="22",
                csi_section="22 40 00",
                description="Plumbing fixtures",
                quantity=8.0,
                unit="EA",
                unit_cost=950.0,
                total_cost=7600.0,
                cost_category=CostCategory.SUBCONTRACTOR,
            ),
        ],
    )


def _default_config() -> QuoteConfig:
    return QuoteConfig(
        quote_meta=QuoteMeta(scope_blurb="Test scope blurb.", payment_terms_text="Net 30."),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="Mobilization", percentage=30.0, notes="At NTP"),
                PaymentMilestone(label="Rough-in",     percentage=30.0, notes="At rough-in"),
                PaymentMilestone(label="Finish",       percentage=30.0, notes="Substantial completion"),
                PaymentMilestone(label="Retainage",    percentage=10.0, notes="After acceptance"),
            ],
        ),
    )


def test_build_quote_pdf_writes_non_empty_file(tmp_path: Path) -> None:
    out = tmp_path / "quote.pdf"
    result = build_quote_pdf(
        estimate=_minimal_estimate(),
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
        csi_titles={"03": "Concrete", "06": "Wood, Plastics, and Composites", "22": "Plumbing"},
    )
    assert result == out
    assert out.is_file()
    size = out.stat().st_size
    assert size > 5000, f"PDF suspiciously small ({size} bytes)"
    head = out.read_bytes()[:5]
    assert head == b"%PDF-", f"output is not a valid PDF (header={head!r})"


def test_payment_schedule_percentage_validator() -> None:
    """Sum-to-100 invariant must fail on bad percentages."""
    with pytest.raises(ValueError, match="must sum to 100"):
        PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="A", percentage=40.0),
                PaymentMilestone(label="B", percentage=40.0),
            ],
        )


def test_payment_schedule_milestone_total_warning() -> None:
    sched = PaymentSchedule(
        mode="milestone",
        milestones=[
            PaymentMilestone(label="Deposit", amount=1000.0),
            PaymentMilestone(label="Final",   amount=1000.0),
        ],
    )
    warns = sched.validate_against_total(5000.0)
    assert warns, "Expected a warning when amounts don't cover contract total"


# ---------------------------------------------------------------------------
# Phase T6 — banded coverage tiles in the PDF executive summary
# ---------------------------------------------------------------------------


def _t6_line(
    *,
    description: str,
    confidence: float,
    total: float,
    suppressed: bool = False,
) -> CostLine:
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description=description,
        quantity=100.0,
        unit="SF",
        unit_cost=round(total / 100.0, 4),
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        suppressed=suppressed,
        cost_band=band_for_confidence(confidence, suppressed=suppressed),
    )


def _t6_estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6 PDF",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _mixed_t6_estimate() -> Estimate:
    """One per band, plus a suppressed line."""
    return _t6_estimate([
        _t6_line(description="auto", confidence=0.92, total=10_000.0),
        _t6_line(description="review", confidence=0.78, total=5_000.0),
        _t6_line(description="hand", confidence=0.40, total=2_000.0),
        _t6_line(description="mismatch", confidence=0.99, total=0.0, suppressed=True),
    ])


def _styles_for_test():
    """Cheap re-derivation of the PDF style sheet for unit tests."""
    from core.exporter_pdf import _styles
    return _styles()


def test_band_subscript_text_contains_all_three_segments_on_mixed_estimate() -> None:
    text = _band_subscript_text(_mixed_t6_estimate())
    assert "auto-approved" in text
    assert "pending review" in text
    assert "need manual takeoff" in text


def test_band_subscript_text_omits_review_when_review_count_zero() -> None:
    est = _t6_estimate([
        _t6_line(description="auto", confidence=0.92, total=1000.0),
        _t6_line(description="hand", confidence=0.40, total=500.0),
    ])
    text = _band_subscript_text(est)
    assert "auto-approved" in text
    assert "pending review" not in text
    assert "need manual takeoff" in text


def test_band_subscript_text_omits_hand_when_hand_count_zero() -> None:
    est = _t6_estimate([
        _t6_line(description="auto", confidence=0.92, total=1000.0),
        _t6_line(description="review", confidence=0.78, total=500.0),
    ])
    text = _band_subscript_text(est)
    assert "auto-approved" in text
    assert "pending review" in text
    assert "manual takeoff" not in text


def test_render_band_tiles_returns_none_when_only_auto() -> None:
    """Clean path: no row outside AUTO → omit the breakdown row entirely."""
    est = _t6_estimate([
        _t6_line(description="auto-only", confidence=0.92, total=10_000.0),
    ])
    assert _render_band_tiles(est, _styles_for_test()) is None


def test_render_band_tiles_renders_three_tiles_on_mixed_estimate() -> None:
    tbl = _render_band_tiles(_mixed_t6_estimate(), _styles_for_test())
    assert tbl is not None
    # reportlab Table stores the data grid in ``_cellvalues``; the band
    # row is a single-row table with one column per visible tile.
    assert len(tbl._cellvalues) == 1
    assert len(tbl._cellvalues[0]) == 3  # auto, review, hand


def test_render_band_tiles_renders_two_tiles_when_hand_zero() -> None:
    est = _t6_estimate([
        _t6_line(description="auto", confidence=0.92, total=1000.0),
        _t6_line(description="review", confidence=0.78, total=500.0),
    ])
    tbl = _render_band_tiles(est, _styles_for_test())
    assert tbl is not None
    assert len(tbl._cellvalues[0]) == 2  # auto + review only


def test_render_band_tiles_renders_two_tiles_when_review_zero() -> None:
    """Auto + hand → render two tiles (AUTO and HAND); review is hidden."""
    est = _t6_estimate([
        _t6_line(description="auto", confidence=0.92, total=1000.0),
        _t6_line(description="hand", confidence=0.40, total=500.0),
    ])
    tbl = _render_band_tiles(est, _styles_for_test())
    assert tbl is not None
    assert len(tbl._cellvalues[0]) == 2  # auto + hand


def test_build_quote_pdf_renders_with_mixed_bands(tmp_path: Path) -> None:
    """Smoke test: a mixed-band estimate must still produce a valid PDF."""
    out = tmp_path / "t6_quote.pdf"
    build_quote_pdf(
        estimate=_mixed_t6_estimate(),
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
        csi_titles={"09": "Finishes"},
    )
    assert out.is_file()
    assert out.read_bytes().startswith(b"%PDF-")


# ---------------------------------------------------------------------------
# Phase T7 — tier-subscript suppression + percentage rounding invariants
# ---------------------------------------------------------------------------


from core.exporter_pdf import _tier_subscript_text  # noqa: E402
from core.schemas import CostSourceTier  # noqa: E402


def _t7_line(
    *,
    description: str,
    confidence: float,
    price_confidence: float,
    tier: CostSourceTier,
    total: float,
    suppressed: bool = False,
) -> CostLine:
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description=description,
        quantity=100.0,
        unit="SF",
        unit_cost=round(total / 100.0, 4) if total > 0 else 0.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        price_confidence=price_confidence,
        cost_source_tier=tier,
        suppressed=suppressed,
        cost_band=band_for_confidence(
            round(confidence * price_confidence, 4),
            suppressed=suppressed,
        ),
    )


def _t7_all_exact_estimate() -> Estimate:
    return Estimate(
        project_name="all-exact",
        line_items=[
            _t7_line(
                description="A",
                confidence=0.95, price_confidence=0.95,
                tier=CostSourceTier.EXACT_MATCH, total=10_000.0,
            ),
            _t7_line(
                description="B",
                confidence=0.92, price_confidence=0.95,
                tier=CostSourceTier.EXACT_MATCH, total=5_000.0,
            ),
        ],
    )


def _t7_mixed_tier_estimate() -> Estimate:
    """One line per tier — exercises the full subscript phrasing."""
    return Estimate(
        project_name="mixed-tier",
        line_items=[
            _t7_line(
                description="exact",
                confidence=0.95, price_confidence=0.95,
                tier=CostSourceTier.EXACT_MATCH, total=600.0,
            ),
            _t7_line(
                description="interpolated",
                confidence=0.95, price_confidence=0.65,
                tier=CostSourceTier.INTERPOLATED, total=300.0,
            ),
            _t7_line(
                description="parametric",
                confidence=0.95, price_confidence=0.45,
                tier=CostSourceTier.PARAMETRIC, total=100.0,
            ),
        ],
    )


def _t7_all_missing_estimate() -> Estimate:
    return Estimate(
        project_name="all-missing",
        line_items=[
            _t7_line(
                description="m1",
                confidence=0.95, price_confidence=0.0,
                tier=CostSourceTier.MISSING, total=0.0, suppressed=True,
            ),
            _t7_line(
                description="m2",
                confidence=0.95, price_confidence=0.0,
                tier=CostSourceTier.MISSING, total=0.0, suppressed=True,
            ),
        ],
    )


def test_t7_subscript_appears_when_at_least_one_interpolated_line() -> None:
    """Mixed-tier estimate (≥ 1 INTERPOLATED line) → subscript must
    surface and carry the brief's three-bucket phrasing."""
    text = _tier_subscript_text(_t7_mixed_tier_estimate())
    assert text is not None
    assert "from exact catalog matches" in text
    assert "interpolated" in text
    assert "parametric defaults" in text


def test_t7_subscript_format_matches_brief_phrasing() -> None:
    """Phrase shape: 'of which X% from exact catalog matches, Y% interpolated,
    Z% parametric defaults' — fixed by the Phase T7 brief."""
    text = _tier_subscript_text(_t7_mixed_tier_estimate())
    assert text is not None
    assert text.startswith("of which ")
    assert "% from exact catalog matches" in text
    assert "% interpolated" in text
    assert "% parametric defaults" in text


def test_t7_subscript_hidden_when_all_lines_are_exact() -> None:
    """Clean output for a fully-exact run — no INTERPOLATED, no
    PARAMETRIC → suppress the subscript entirely."""
    assert _tier_subscript_text(_t7_all_exact_estimate()) is None


def test_t7_subscript_percentages_sum_to_100_within_rounding() -> None:
    """The three figures must sum to 100 (± rounding tolerance) per the
    Phase T7 brief — exact/interpolated/parametric are the full picture
    of the headline subtotal."""
    import re
    text = _tier_subscript_text(_t7_mixed_tier_estimate())
    assert text is not None
    pcts = [int(m) for m in re.findall(r"(\d+)%", text)]
    assert len(pcts) == 3, f"expected 3 percentages, found {pcts}"
    assert abs(sum(pcts) - 100) <= 1, (
        f"percentages must sum to 100 (±1); got {pcts} → {sum(pcts)}"
    )


def test_t7_subscript_suppressed_when_all_lines_missing_zero_subtotal() -> None:
    """Edge case: every line is MISSING / suppressed → subtotal = 0 →
    denominator is 0 → suppress the subscript gracefully (no
    divide-by-zero placeholder, no NaN%)."""
    est = _t7_all_missing_estimate()
    assert est.subtotal == 0.0
    assert _tier_subscript_text(est) is None
