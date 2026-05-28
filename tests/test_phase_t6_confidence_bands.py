"""Phase T6 — confidence-aware pricing band tests.

Covers:

* ``band_for_confidence`` threshold logic at every edge (0.85 / 0.65 /
  0.0 / 1.0 / None / suppressed).
* ``CostLine.cost_band`` defaults + round-trip via Pydantic.
* ``Estimate`` band-aware aggregates: ``total_auto_approve``,
  ``total_operator_review``, ``total_hand_takeoff``,
  ``grand_total_with_review``, ``grand_total_auto_only``,
  ``hand_takeoff_count``, ``operator_review_count``, ``auto_approve_count``.
* ``price_takeoff`` populates ``cost_band`` on every emitted line and
  respects the suppression-forces-HAND_TAKEOFF rule.
* Backward-compat: ``grand_total`` is an alias for
  ``grand_total_with_review``.
* Empty / all-auto / all-hand edge cases.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.estimator import CostDatabase, price_takeoff
from core.pricing.cwicr_matcher import CwicrCandidate, CwicrMatcher
from core.schemas import (
    COST_BAND_AUTO_THRESHOLD,
    COST_BAND_REVIEW_THRESHOLD,
    CostBand,
    CostCategory,
    CostLine,
    Estimate,
    SiteInfo,
    TakeoffItem,
    band_for_confidence,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


def _make_project(takeoffs: list[TakeoffItem]) -> ProjectModel:
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=takeoffs,
        sheet_summaries={},
        warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(name="T6 Test"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _seed_db(tmp_path: Path) -> CostDatabase:
    """Generic seed DB with broad keyword coverage for the band tests."""
    db = {
        "_meta": {"version": "t6-test"},
        "03 30 00": {
            "description": "Slab on grade",
            "unit": "SF",
            "unit_cost": 10.00,
            "cost_category": "subcontractor",
            "waste_factor": 1.0,
            "keywords": ["slab", "concrete", "footing"],
        },
        "09 91 23": {
            "description": "Interior painting",
            "unit": "SF",
            "unit_cost": 2.00,
            "cost_category": "subcontractor",
            "waste_factor": 1.0,
            "keywords": ["paint", "painting"],
        },
        "08 11 13": {
            "description": "Hollow metal doors",
            "unit": "EA",
            "unit_cost": 500.00,
            "cost_category": "material",
            "waste_factor": 1.0,
            "keywords": ["door", "hollow metal", "hm"],
        },
        # Used by the suppression test.
        "05 12 00": {
            "description": "Structural steel framing",
            "unit": "TON",
            "unit_cost": 4200.0,
            "cost_category": "subcontractor",
            "waste_factor": 1.03,
            "keywords": ["beam", "steel"],
        },
    }
    path = tmp_path / "cost_database.json"
    path.write_text(json.dumps(db), encoding="utf-8")
    return CostDatabase(path)


def _line(
    *,
    division: str = "09",
    section: str | None = "09 91 23",
    description: str = "Interior painting",
    confidence: float = 0.92,
    total: float = 1000.0,
    suppressed: bool = False,
    band: CostBand | None = None,
) -> CostLine:
    return CostLine(
        csi_division=division,
        csi_section=section,
        description=description,
        quantity=100.0,
        unit="SF",
        unit_cost=round(total / 100.0, 2),
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        suppressed=suppressed,
        cost_band=band if band is not None else band_for_confidence(
            confidence, suppressed=suppressed
        ),
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# band_for_confidence — threshold edges
# ---------------------------------------------------------------------------


def test_thresholds_exposed_as_module_constants() -> None:
    """The boundary numbers must be importable so callers stay in sync."""
    assert COST_BAND_AUTO_THRESHOLD == 0.85
    assert COST_BAND_REVIEW_THRESHOLD == 0.65


@pytest.mark.parametrize(
    "conf,expected",
    [
        (1.0, CostBand.AUTO_APPROVE),
        (0.95, CostBand.AUTO_APPROVE),
        (0.86, CostBand.AUTO_APPROVE),
        # Inclusive at 0.85
        (0.85, CostBand.AUTO_APPROVE),
        # Just below the auto threshold
        (0.8499, CostBand.OPERATOR_REVIEW),
        (0.84, CostBand.OPERATOR_REVIEW),
        (0.75, CostBand.OPERATOR_REVIEW),
        (0.70, CostBand.OPERATOR_REVIEW),
        (0.66, CostBand.OPERATOR_REVIEW),
        # Inclusive at 0.65
        (0.65, CostBand.OPERATOR_REVIEW),
        # Just below the review threshold
        (0.6499, CostBand.HAND_TAKEOFF),
        (0.64, CostBand.HAND_TAKEOFF),
        (0.50, CostBand.HAND_TAKEOFF),
        (0.10, CostBand.HAND_TAKEOFF),
        (0.0, CostBand.HAND_TAKEOFF),
    ],
)
def test_band_for_confidence_edges(conf: float, expected: CostBand) -> None:
    assert band_for_confidence(conf) == expected


def test_band_for_confidence_none_defaults_to_operator_review() -> None:
    """Conservative: an unknown-confidence row (legacy LLM path) goes to
    REVIEW rather than auto-approve."""
    assert band_for_confidence(None) == CostBand.OPERATOR_REVIEW


def test_band_for_confidence_suppressed_always_hand_takeoff() -> None:
    """Suppression always wins, even on a high-confidence row."""
    for conf in (0.0, 0.5, 0.65, 0.85, 0.99, 1.0, None):
        assert band_for_confidence(conf, suppressed=True) == CostBand.HAND_TAKEOFF, (
            f"suppressed=True must force HAND_TAKEOFF for conf={conf}"
        )


# ---------------------------------------------------------------------------
# CostLine schema round-trip
# ---------------------------------------------------------------------------


def test_costline_cost_band_defaults_to_auto_approve() -> None:
    """Backward-compat: hand-constructed CostLine with no band defaults to AUTO."""
    li = CostLine(
        csi_division="03", description="x", quantity=1.0, unit="EA",
        unit_cost=1.0, total_cost=1.0,
    )
    assert li.cost_band == CostBand.AUTO_APPROVE


def test_costline_cost_band_round_trips_via_model_dump_and_validate() -> None:
    original = _line(confidence=0.78, band=CostBand.OPERATOR_REVIEW)
    payload = original.model_dump()
    assert payload["cost_band"] == CostBand.OPERATOR_REVIEW
    rebuilt = CostLine.model_validate(payload)
    assert rebuilt.cost_band == CostBand.OPERATOR_REVIEW


def test_costline_cost_band_accepts_string_value() -> None:
    """JSON round-trip can deliver the enum's string form."""
    li = CostLine(
        csi_division="09", description="paint", quantity=1.0, unit="SF",
        unit_cost=2.0, total_cost=2.0,
        cost_band="hand_takeoff",  # type: ignore[arg-type]
    )
    assert li.cost_band == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# Estimate aggregates
# ---------------------------------------------------------------------------


def test_empty_estimate_band_aggregates_are_zero() -> None:
    est = _estimate([])
    assert est.total_auto_approve == 0.0
    assert est.total_operator_review == 0.0
    assert est.total_hand_takeoff == 0.0
    assert est.auto_approve_count == 0
    assert est.operator_review_count == 0
    assert est.hand_takeoff_count == 0
    assert est.subtotal == 0.0
    assert est.grand_total == 0.0
    assert est.grand_total_with_review == 0.0
    assert est.grand_total_auto_only == 0.0


def test_all_auto_estimate_grand_totals_match() -> None:
    """When every line is AUTO, ``grand_total_auto_only`` == ``grand_total``."""
    est = _estimate([
        _line(confidence=0.92, total=1000.0, description="A"),
        _line(confidence=0.99, total=2000.0, description="B"),
    ])
    assert est.auto_approve_count == 2
    assert est.operator_review_count == 0
    assert est.hand_takeoff_count == 0
    assert est.total_auto_approve == 3000.0
    assert est.total_operator_review == 0.0
    assert est.total_hand_takeoff == 0.0
    assert est.subtotal == 3000.0
    assert est.grand_total == est.grand_total_auto_only


def test_all_hand_estimate_grand_total_is_zero_but_informational_total_is_not() -> None:
    est = _estimate([
        _line(confidence=0.30, total=5000.0, description="low-conf-A"),
        _line(confidence=0.50, total=7500.0, description="low-conf-B"),
    ])
    assert est.auto_approve_count == 0
    assert est.operator_review_count == 0
    assert est.hand_takeoff_count == 2
    assert est.total_hand_takeoff == 12500.0
    assert est.subtotal == 0.0
    assert est.grand_total == 0.0
    assert est.grand_total_with_review == 0.0
    assert est.grand_total_auto_only == 0.0


def test_mixed_band_aggregation_sums_to_total_line_count() -> None:
    """auto + review + hand counts must equal total line count."""
    est = _estimate([
        _line(confidence=0.92, total=100.0),
        _line(confidence=0.88, total=200.0),
        _line(confidence=0.78, total=300.0),
        _line(confidence=0.70, total=400.0),
        _line(confidence=0.55, total=500.0),
        _line(confidence=0.20, total=600.0),
    ])
    assert (
        est.auto_approve_count
        + est.operator_review_count
        + est.hand_takeoff_count
    ) == len(est.line_items)


def test_mixed_band_totals_at_common_confidence_values() -> None:
    """Confirm 0.92 / 0.78 / 0.55 round-trip into the right buckets."""
    est = _estimate([
        _line(confidence=0.92, total=1000.0, description="auto"),
        _line(confidence=0.78, total=2500.0, description="review"),
        _line(confidence=0.55, total=4000.0, description="hand"),
    ])
    assert est.total_auto_approve == 1000.0
    assert est.total_operator_review == 2500.0
    assert est.total_hand_takeoff == 4000.0
    # subtotal excludes hand-takeoff
    assert est.subtotal == 3500.0
    # grand_total = with_review = 3500 * 1.10 * 1.10 * 1.05
    expected_gt = round(3500.0 * 1.10 * 1.10 * 1.05, 2)
    assert est.grand_total == pytest.approx(expected_gt)
    assert est.grand_total_with_review == pytest.approx(expected_gt)


def test_grand_total_alias_for_grand_total_with_review() -> None:
    """Backward-compat check: ``grand_total`` and ``grand_total_with_review``
    return identical values for every band mix."""
    cases = [
        [],
        [_line(confidence=0.92, total=1000.0)],
        [_line(confidence=0.78, total=2500.0)],
        [_line(confidence=0.55, total=4000.0)],
        [_line(confidence=0.92, total=1000.0), _line(confidence=0.55, total=500.0)],
    ]
    for lines in cases:
        est = _estimate(lines)
        assert est.grand_total == est.grand_total_with_review, (
            f"grand_total alias broken for {lines!r}"
        )


def test_grand_total_auto_only_uses_auto_subtotal_for_markups() -> None:
    """Markups must compound off the AUTO subtotal, not the AUTO+REVIEW one."""
    est = _estimate([
        _line(confidence=0.92, total=1000.0, description="auto"),
        _line(confidence=0.78, total=5000.0, description="review"),
    ])
    # Auto-only subtotal = 1000; with markups 10/10/5%:
    expected_auto = round(1000.0 * 1.10 * 1.10 * 1.05, 2)
    assert est.grand_total_auto_only == pytest.approx(expected_auto)
    # The with-review total should be strictly larger (review adds dollars).
    assert est.grand_total_with_review > est.grand_total_auto_only


def test_hand_takeoff_total_excluded_from_grand_totals() -> None:
    """The HAND total is informational only — never in any grand_total."""
    est = _estimate([
        _line(confidence=0.92, total=1000.0),
        _line(confidence=0.40, total=999_999.0, description="phantom"),
    ])
    # The $999,999 phantom must NOT show up in any headline number.
    assert est.subtotal == 1000.0
    assert est.grand_total == est.grand_total_auto_only
    assert est.total_hand_takeoff == 999_999.0


def test_by_division_excludes_hand_takeoff_lines() -> None:
    est = _estimate([
        _line(division="09", section="09 91 23", confidence=0.92, total=100.0),
        _line(division="03", section="03 30 00", confidence=0.40, total=50_000.0),
    ])
    assert est.by_division == {"09": 100.0}


def test_by_cost_category_excludes_hand_takeoff_lines() -> None:
    est = _estimate([
        _line(confidence=0.92, total=100.0),
        _line(confidence=0.40, total=50_000.0),
    ])
    assert est.by_cost_category == {"subcontractor": 100.0}


# ---------------------------------------------------------------------------
# price_takeoff integration
# ---------------------------------------------------------------------------


def test_price_takeoff_assigns_band_from_takeoff_confidence(
    tmp_path: Path,
) -> None:
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade", quantity=100.0, unit="SF",
            confidence=0.92,  # AUTO
        ),
        TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior painting", quantity=500.0, unit="SF",
            confidence=0.78,  # REVIEW
        ),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=4.0, unit="EA",
            confidence=0.40,  # HAND
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    bands = {li.description: li.cost_band for li in est.line_items}
    assert bands["Slab on grade"] == CostBand.AUTO_APPROVE
    assert bands["Interior painting"] == CostBand.OPERATOR_REVIEW
    assert bands["Hollow metal doors"] == CostBand.HAND_TAKEOFF


def test_price_takeoff_default_takeoff_confidence_lands_in_operator_review(
    tmp_path: Path,
) -> None:
    """The schema default ``TakeoffItem.confidence == 0.7`` must land in
    OPERATOR_REVIEW — the brief's "no confidence → REVIEW" contract is
    satisfied by the default value already.
    """
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior painting", quantity=500.0, unit="SF",
            # confidence defaulted to 0.7
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    assert est.line_items[0].cost_band == CostBand.OPERATOR_REVIEW
    # And the line still rolls into grand_total (REVIEW is in headline).
    assert est.grand_total > 0


def test_price_takeoff_suppressed_line_forced_to_hand_takeoff(
    tmp_path: Path,
) -> None:
    """Unit-mismatch lines (suppressed=True) must land in HAND_TAKEOFF
    regardless of the source takeoff confidence."""
    db = _seed_db(tmp_path)
    # LF beam takeoff against a TON cost-DB entry → mismatch → suppressed.
    takeoffs = [
        TakeoffItem(
            csi_division="05", csi_section="05 12 00",
            description="2x12 beams", quantity=8.0, unit="LF",
            confidence=0.99,  # would otherwise be AUTO
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    line = est.line_items[0]
    assert line.suppressed is True
    assert line.cost_band == CostBand.HAND_TAKEOFF
    # Suppressed line carries total_cost=0 — no double-counting risk in
    # total_hand_takeoff even though it shows up there.
    assert line.total_cost == 0.0
    # Sanity: confirm the suppressed line shows up in hand_takeoff_line_items.
    assert line in est.hand_takeoff_line_items
    # And the grand-total stays zero (no other lines).
    assert est.grand_total == 0.0


def test_price_takeoff_no_match_low_confidence_lands_in_hand_takeoff(
    tmp_path: Path,
) -> None:
    """A no-match line at $0 still surfaces in the band — exercise the
    no-match branch so the band column on a $0 row is meaningful."""
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="42", csi_section="42 12 34",
            description="something exotic we don't price",
            quantity=1.0, unit="LS",
            confidence=0.30,  # HAND
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    line = est.line_items[0]
    assert line.cost_source == "(no match)"
    assert line.suppressed is False  # no-match is not a suppression
    assert line.cost_band == CostBand.HAND_TAKEOFF


def test_price_takeoff_cwicr_match_inherits_similarity_band(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR confidence == similarity; verify it bands accordingly."""
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="X", description="Concrete slab on grade", unit="SF",
        unit_price=8.0, labor_cost=2.0, material_cost=5.0, equipment_cost=1.0,
        region="usa_usd", year=2025, similarity=0.95, source_row_id=1,
    )
    m = MagicMock(spec=CwicrMatcher)
    m.warm.return_value = None
    m.match.return_value = [cand]

    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade", quantity=100.0, unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=m,
    )
    line = est.line_items[0]
    assert line.cost_source == "cwicr:1"
    assert line.confidence == pytest.approx(0.95)
    assert line.cost_band == CostBand.AUTO_APPROVE


# ---------------------------------------------------------------------------
# Suppression × band double-counting guard
# ---------------------------------------------------------------------------


def test_suppressed_hand_takeoff_line_total_cost_is_zero() -> None:
    """The suppression code path zeroes total_cost — even though the line
    shows up in hand_takeoff_line_items it contributes $0 to the
    informational total, so there's no double-counting against the
    grand_total (which excludes HAND anyway)."""
    est = _estimate([
        # Real HAND line with non-zero cost (low-confidence but priced).
        _line(confidence=0.40, total=1000.0, description="low-conf"),
        # Suppressed line forced to HAND with total_cost=0.
        _line(
            confidence=0.99, total=0.0, suppressed=True,
            description="unit mismatch", band=CostBand.HAND_TAKEOFF,
        ),
    ])
    # Both show up in the queue.
    assert est.hand_takeoff_count == 2
    # But only the priced low-confidence line contributes dollars.
    assert est.total_hand_takeoff == 1000.0


# ---------------------------------------------------------------------------
# Headline / queue interaction
# ---------------------------------------------------------------------------


def test_headline_line_items_excludes_hand_only() -> None:
    est = _estimate([
        _line(confidence=0.92, total=1.0, description="auto"),
        _line(confidence=0.70, total=2.0, description="review"),
        _line(confidence=0.40, total=4.0, description="hand"),
    ])
    descriptions = {li.description for li in est.headline_line_items}
    assert descriptions == {"auto", "review"}


def test_operator_review_queue_isolates_review_band() -> None:
    est = _estimate([
        _line(confidence=0.92, total=1.0, description="auto"),
        _line(confidence=0.70, total=2.0, description="review"),
        _line(confidence=0.40, total=4.0, description="hand"),
    ])
    descriptions = {li.description for li in est.operator_review_line_items}
    assert descriptions == {"review"}


def test_hand_takeoff_queue_includes_suppressed_lines() -> None:
    """Suppressed lines (always HAND) must show in hand_takeoff_line_items
    even though they're filtered out of priced_line_items."""
    est = _estimate([
        _line(confidence=0.40, total=100.0, description="low-conf"),
        _line(
            confidence=0.99, total=0.0, suppressed=True,
            description="mismatch", band=CostBand.HAND_TAKEOFF,
        ),
    ])
    descriptions = {li.description for li in est.hand_takeoff_line_items}
    assert descriptions == {"low-conf", "mismatch"}


# ---------------------------------------------------------------------------
# Backward-compat with existing semantics
# ---------------------------------------------------------------------------


def test_priced_line_items_still_means_non_suppressed() -> None:
    """The long-standing contract of ``priced_line_items`` (non-suppressed)
    must NOT change in T6 — only the headline subtotal moved."""
    est = _estimate([
        _line(confidence=0.92, total=1.0, description="auto-priced"),
        _line(confidence=0.40, total=2.0, description="hand-priced"),
        _line(
            confidence=0.99, total=0.0, suppressed=True,
            description="mismatch", band=CostBand.HAND_TAKEOFF,
        ),
    ])
    # priced_line_items = non-suppressed (regardless of band)
    descriptions = {li.description for li in est.priced_line_items}
    assert descriptions == {"auto-priced", "hand-priced"}
    # suppressed_line_items mirror
    assert {li.description for li in est.suppressed_line_items} == {"mismatch"}


def test_default_confidence_07_priced_line_remains_in_grand_total(
    tmp_path: Path,
) -> None:
    """Regression guard for the dominant pre-T6 test pattern: a
    CostLine with default confidence (0.7) still rolls into grand_total
    after T6 because 0.7 lands in OPERATOR_REVIEW."""
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade", quantity=100.0, unit="SF",
            # confidence defaulted to 0.7
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    assert est.grand_total > 0
    assert est.line_items[0].cost_band == CostBand.OPERATOR_REVIEW


# ---------------------------------------------------------------------------
# Markup compounding invariants
# ---------------------------------------------------------------------------


def test_with_review_grand_total_matches_existing_markup_formula() -> None:
    """grand_total_with_review must use the same compounding as the legacy
    formula: subtotal × (1+cont%) × (1+oh%) × (1+profit%)."""
    est = Estimate(
        project_name="m",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            _line(confidence=0.92, total=10_000.0),
        ],
    )
    expected = round(10_000.0 * 1.10 * 1.10 * 1.05, 2)
    assert est.grand_total_with_review == pytest.approx(expected)
    assert est.grand_total == pytest.approx(expected)


def test_auto_only_grand_total_matches_independent_markup_formula() -> None:
    est = Estimate(
        project_name="m",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            _line(confidence=0.92, total=1000.0, description="auto"),
            _line(confidence=0.70, total=5000.0, description="review"),
        ],
    )
    base = 1000.0
    cont = round(base * 0.10, 2)
    oh = round((base + cont) * 0.10, 2)
    prof = round((base + cont + oh) * 0.05, 2)
    expected = round(base + cont + oh + prof, 2)
    assert est.grand_total_auto_only == pytest.approx(expected)
