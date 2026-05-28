"""Phase T7 — price-confidence + cost-source-tier coverage tests.

Covers (in section order):

* :func:`price_confidence_from_similarity` — boundary semantics at
  every tier transition (0.92 / 0.75 / 0.50) + clamping for
  out-of-range similarities.
* :pyattr:`CostLine.combined_confidence` — qty × price multiplication,
  schema-default behaviour, and clamping.
* Band reassignment via combined_confidence — verifies a high-qty
  line can be demoted by a low price_confidence (the central
  Phase T7 contract).
* :pyattr:`Estimate.total_by_tier` and :pyattr:`Estimate.count_by_tier`
  aggregates — empty / single-tier / one-of-each / MISSING $0 dollar /
  reconciliation invariants.
* Backward-compat for Phase T6 — pre-T7 fixtures (no
  ``price_confidence``) still band identically to T6 because the
  default ``price_confidence=1.0`` collapses combined back to qty.
* Integration via :func:`price_takeoff` — CWICR-similarity → tier
  bridge, seed-DB → ``EXACT_MATCH``, suppressed → ``MISSING``,
  and full ``model_dump`` round-trip.

Mirrors the structure of ``tests/test_phase_t6_confidence_bands.py``
so a future T8 follow-up has the same shape to copy.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.estimator import CostDatabase, _combined_band, price_takeoff
from core.pricing.cwicr_matcher import CwicrCandidate, CwicrMatcher
from core.schemas import (
    COST_TIER_CATEGORY_MULTIPLIER,
    COST_TIER_CATEGORY_THRESHOLD,
    COST_TIER_EXACT_THRESHOLD,
    COST_TIER_INTERPOLATED_PRICE_CONFIDENCE,
    COST_TIER_INTERPOLATED_THRESHOLD,
    COST_TIER_PARAMETRIC_PRICE_CONFIDENCE,
    COST_TIER_SEED_DB_PRICE_CONFIDENCE,
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
    SiteInfo,
    TakeoffItem,
    band_for_confidence,
    price_confidence_from_similarity,
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
        project_info=ProjectInfo(name="T7 Test"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _seed_db(tmp_path: Path) -> CostDatabase:
    db = {
        "_meta": {"version": "t7-test"},
        "03 30 00": {
            "description": "Slab on grade",
            "unit": "SF",
            "unit_cost": 10.00,
            "cost_category": "subcontractor",
            "waste_factor": 1.0,
            "keywords": ["slab", "concrete"],
        },
        "09 91 23": {
            "description": "Interior painting",
            "unit": "SF",
            "unit_cost": 2.00,
            "cost_category": "subcontractor",
            "waste_factor": 1.0,
            "keywords": ["paint", "painting"],
        },
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


def _stub_matcher_with(candidate: CwicrCandidate | None) -> CwicrMatcher:
    m = MagicMock(spec=CwicrMatcher)
    m.warm.return_value = None
    m.match.return_value = [candidate] if candidate is not None else []
    return m


def _line(
    *,
    division: str = "09",
    section: str | None = "09 91 23",
    description: str = "Interior painting",
    confidence: float = 0.92,
    price_confidence: float = 1.0,
    tier: CostSourceTier = CostSourceTier.EXACT_MATCH,
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
        price_confidence=price_confidence,
        cost_source_tier=tier,
        suppressed=suppressed,
        cost_band=band if band is not None else _combined_band(
            confidence, price_confidence, suppressed=suppressed
        ),
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T7",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# Section 1 — price_confidence_from_similarity boundaries
# ---------------------------------------------------------------------------


def test_module_constants_match_phase_t7_brief() -> None:
    """Boundary numbers must match the brief; downstream callers depend on them."""
    assert COST_TIER_EXACT_THRESHOLD == 0.92
    assert COST_TIER_CATEGORY_THRESHOLD == 0.75
    assert COST_TIER_INTERPOLATED_THRESHOLD == 0.50
    assert COST_TIER_CATEGORY_MULTIPLIER == 0.85
    assert COST_TIER_INTERPOLATED_PRICE_CONFIDENCE == 0.65
    assert COST_TIER_PARAMETRIC_PRICE_CONFIDENCE == 0.45
    assert COST_TIER_SEED_DB_PRICE_CONFIDENCE == 0.95


def test_similarity_one_maps_to_exact_match_with_full_price_confidence() -> None:
    tier, conf = price_confidence_from_similarity(1.0)
    assert tier == CostSourceTier.EXACT_MATCH
    assert conf == pytest.approx(1.0)


def test_similarity_just_below_one_still_exact_match() -> None:
    tier, conf = price_confidence_from_similarity(0.99)
    assert tier == CostSourceTier.EXACT_MATCH
    assert conf == pytest.approx(0.99)


def test_similarity_at_exact_threshold_inclusive() -> None:
    """0.92 must land in EXACT_MATCH (inclusive on the upper-tier side)."""
    tier, conf = price_confidence_from_similarity(0.92)
    assert tier == CostSourceTier.EXACT_MATCH
    assert conf == pytest.approx(0.92)


def test_similarity_just_below_exact_threshold_drops_to_category() -> None:
    tier, conf = price_confidence_from_similarity(0.9199)
    assert tier == CostSourceTier.CATEGORY_MATCH
    assert conf == pytest.approx(round(0.9199 * 0.85, 4))


def test_similarity_in_category_band() -> None:
    tier, conf = price_confidence_from_similarity(0.85)
    assert tier == CostSourceTier.CATEGORY_MATCH
    assert conf == pytest.approx(round(0.85 * 0.85, 4))
    assert conf == pytest.approx(0.7225)


def test_similarity_at_category_threshold_inclusive() -> None:
    """0.75 must land in CATEGORY_MATCH (inclusive on the upper-tier side)."""
    tier, conf = price_confidence_from_similarity(0.75)
    assert tier == CostSourceTier.CATEGORY_MATCH
    assert conf == pytest.approx(round(0.75 * 0.85, 4))
    assert conf == pytest.approx(0.6375)


def test_similarity_just_below_category_threshold_drops_to_interpolated() -> None:
    tier, conf = price_confidence_from_similarity(0.7499)
    assert tier == CostSourceTier.INTERPOLATED
    assert conf == pytest.approx(0.65)


def test_similarity_in_interpolated_band() -> None:
    tier, conf = price_confidence_from_similarity(0.65)
    assert tier == CostSourceTier.INTERPOLATED
    assert conf == pytest.approx(0.65)


def test_similarity_at_interpolated_threshold_inclusive() -> None:
    """0.50 must land in INTERPOLATED (inclusive on the upper-tier side)."""
    tier, conf = price_confidence_from_similarity(0.50)
    assert tier == CostSourceTier.INTERPOLATED
    assert conf == pytest.approx(0.65)


def test_similarity_just_below_interpolated_threshold_drops_to_parametric() -> None:
    tier, conf = price_confidence_from_similarity(0.4999)
    assert tier == CostSourceTier.PARAMETRIC
    assert conf == pytest.approx(0.45)


def test_similarity_zero_lands_in_parametric() -> None:
    tier, conf = price_confidence_from_similarity(0.0)
    assert tier == CostSourceTier.PARAMETRIC
    assert conf == pytest.approx(0.45)


def test_similarity_negative_clamped_to_zero() -> None:
    """Negative inputs clamp to 0 → PARAMETRIC at the price-confidence floor."""
    tier, conf = price_confidence_from_similarity(-0.1)
    assert tier == CostSourceTier.PARAMETRIC
    assert conf == pytest.approx(0.45)


def test_similarity_above_one_clamped_to_one() -> None:
    """Out-of-range high inputs clamp to 1.0 → EXACT_MATCH @ 1.0."""
    tier, conf = price_confidence_from_similarity(1.5)
    assert tier == CostSourceTier.EXACT_MATCH
    assert conf == pytest.approx(1.0)


# ---------------------------------------------------------------------------
# Section 2 — CostLine.combined_confidence
# ---------------------------------------------------------------------------


def _bare_line(confidence: float = 0.7, price_confidence: float = 1.0) -> CostLine:
    """Minimal CostLine used by the combined_confidence property tests."""
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description="Interior painting",
        quantity=10.0,
        unit="SF",
        unit_cost=2.0,
        total_cost=20.0,
        confidence=confidence,
        price_confidence=price_confidence,
    )


def test_combined_confidence_both_one_is_one() -> None:
    li = _bare_line(confidence=1.0, price_confidence=1.0)
    assert li.combined_confidence == pytest.approx(1.0)


def test_combined_confidence_both_at_high_band() -> None:
    li = _bare_line(confidence=0.95, price_confidence=0.95)
    assert li.combined_confidence == pytest.approx(0.9025)


def test_combined_confidence_high_qty_low_price_demotes_to_hand() -> None:
    """The Phase T7 hallmark — was AUTO under T6 (qty=0.95 ≥ 0.85), now
    HAND post-T7 because combined = 0.6175 < 0.65."""
    li = _bare_line(confidence=0.95, price_confidence=0.65)
    assert li.combined_confidence == pytest.approx(0.6175)
    assert band_for_confidence(li.combined_confidence) == CostBand.HAND_TAKEOFF


def test_combined_confidence_both_at_080_lands_in_hand() -> None:
    li = _bare_line(confidence=0.80, price_confidence=0.80)
    assert li.combined_confidence == pytest.approx(0.64)
    assert band_for_confidence(li.combined_confidence) == CostBand.HAND_TAKEOFF


def test_combined_confidence_default_qty_with_full_price_returns_default() -> None:
    """Schema default ``confidence=0.7`` × default ``price_confidence=1.0``
    must collapse to 0.7 — preserves the legacy "no LLM confidence
    → OPERATOR_REVIEW" routing post-T7."""
    li = _bare_line()  # both defaults
    assert li.combined_confidence == pytest.approx(0.7)
    assert band_for_confidence(li.combined_confidence) == CostBand.OPERATOR_REVIEW


def test_combined_confidence_default_qty_with_interpolated_price_lands_in_hand() -> None:
    """Default qty (0.7) × INTERPOLATED price (0.65) = 0.455 → HAND."""
    li = _bare_line(price_confidence=0.65)
    assert li.combined_confidence == pytest.approx(0.455)
    assert band_for_confidence(li.combined_confidence) == CostBand.HAND_TAKEOFF


def test_combined_confidence_low_qty_caps_at_below_review_threshold() -> None:
    """qty=0.5 with full price still lands in HAND (0.5 < 0.65)."""
    li = _bare_line(confidence=0.5, price_confidence=1.0)
    assert li.combined_confidence == pytest.approx(0.5)
    assert band_for_confidence(li.combined_confidence) == CostBand.HAND_TAKEOFF


def test_combined_confidence_clamps_out_of_range_inputs() -> None:
    """Pydantic accepts raw floats; the property must defend the [0,1] band."""
    li = _bare_line(confidence=1.5, price_confidence=0.5)
    assert li.combined_confidence == pytest.approx(0.5)


def test_combined_band_helper_treats_none_qty_as_default_07() -> None:
    """``_combined_band`` is the price_takeoff entry-point and must
    accept ``qty_confidence is None`` (legacy LLM path) by treating
    it as the schema default 0.7."""
    assert _combined_band(None, 1.0, suppressed=False) == CostBand.OPERATOR_REVIEW
    assert _combined_band(None, 0.65, suppressed=False) == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# Section 3 — band reassignment via combined_confidence
# ---------------------------------------------------------------------------


def test_high_qty_with_borderline_low_price_demotes_band() -> None:
    li = _line(confidence=0.95, price_confidence=0.55)
    # Combined = 0.5225 → < 0.65 → HAND
    assert li.combined_confidence == pytest.approx(0.5225)
    assert li.cost_band == CostBand.HAND_TAKEOFF


def test_low_qty_with_full_price_stays_in_hand() -> None:
    """price_confidence cannot promote a low-qty line."""
    li = _line(confidence=0.55, price_confidence=1.0)
    assert li.combined_confidence == pytest.approx(0.55)
    assert li.cost_band == CostBand.HAND_TAKEOFF


def test_both_high_lands_in_auto_approve() -> None:
    li = _line(confidence=0.95, price_confidence=0.95)
    assert li.combined_confidence == pytest.approx(0.9025)
    assert li.cost_band == CostBand.AUTO_APPROVE


def test_default_price_confidence_preserves_t6_band_semantics() -> None:
    """When price_confidence defaults to 1.0, combined_confidence == qty
    so band assignment matches T6 exactly."""
    for conf, expected in [
        (1.00, CostBand.AUTO_APPROVE),
        (0.92, CostBand.AUTO_APPROVE),
        (0.85, CostBand.AUTO_APPROVE),
        (0.84, CostBand.OPERATOR_REVIEW),
        (0.70, CostBand.OPERATOR_REVIEW),
        (0.65, CostBand.OPERATOR_REVIEW),
        (0.55, CostBand.HAND_TAKEOFF),
        (0.30, CostBand.HAND_TAKEOFF),
    ]:
        li = _line(confidence=conf, price_confidence=1.0)
        assert li.cost_band == expected, f"conf={conf}: got {li.cost_band}"


def test_suppressed_line_forced_to_hand_regardless_of_combined() -> None:
    """Suppression beats band — even a perfectly-priced row goes to HAND
    when ``suppressed=True``."""
    for qty, price in [(0.99, 0.99), (0.50, 0.50), (1.0, 1.0), (0.0, 0.0)]:
        band = _combined_band(qty, price, suppressed=True)
        assert band == CostBand.HAND_TAKEOFF, f"qty={qty}, price={price}: got {band}"


def test_default_takeoff_confidence_with_seed_db_full_price_stays_in_review() -> None:
    """Default takeoff confidence (0.7) × seed-DB price_confidence (0.95)
    = 0.665 → OPERATOR_REVIEW (just above 0.65)."""
    qty = 0.7  # schema default
    price = COST_TIER_SEED_DB_PRICE_CONFIDENCE  # 0.95
    band = _combined_band(qty, price, suppressed=False)
    assert band == CostBand.OPERATOR_REVIEW
    assert round(qty * price, 4) == pytest.approx(0.665)


# ---------------------------------------------------------------------------
# Section 4 — Estimate.total_by_tier / count_by_tier
# ---------------------------------------------------------------------------


def test_empty_estimate_all_tiers_zero() -> None:
    est = _estimate([])
    counts = est.count_by_tier
    totals = est.total_by_tier
    for tier in CostSourceTier:
        assert counts[tier] == 0
        assert totals[tier] == 0.0


def test_single_exact_match_line_isolates_to_exact_bucket() -> None:
    est = _estimate([
        _line(
            description="A",
            confidence=0.95,
            price_confidence=0.95,
            tier=CostSourceTier.EXACT_MATCH,
            total=100.0,
        ),
    ])
    counts = est.count_by_tier
    totals = est.total_by_tier
    assert counts[CostSourceTier.EXACT_MATCH] == 1
    assert totals[CostSourceTier.EXACT_MATCH] == pytest.approx(100.0)
    for tier in CostSourceTier:
        if tier == CostSourceTier.EXACT_MATCH:
            continue
        assert counts[tier] == 0
        assert totals[tier] == 0.0


def test_one_line_per_tier_count_sums_to_six() -> None:
    """One of each of the six CostSourceTier values."""
    lines = []
    tier_inputs = [
        (CostSourceTier.EXACT_MATCH, 0.95, 0.95, 100.0, False),
        (CostSourceTier.CATEGORY_MATCH, 0.92, 0.78, 200.0, False),
        (CostSourceTier.INTERPOLATED, 0.92, 0.65, 300.0, False),
        (CostSourceTier.PARAMETRIC, 0.92, 0.45, 400.0, False),
        (CostSourceTier.MANUAL_OVERRIDE, 0.92, 1.0, 500.0, False),
        (CostSourceTier.MISSING, 0.92, 0.0, 0.0, True),
    ]
    for i, (tier, qty, price, total, supp) in enumerate(tier_inputs):
        lines.append(
            _line(
                description=f"L{i}",
                confidence=qty,
                price_confidence=price,
                tier=tier,
                total=total,
                suppressed=supp,
            )
        )
    est = _estimate(lines)
    counts = est.count_by_tier
    assert sum(counts.values()) == 6
    for tier in CostSourceTier:
        assert counts[tier] == 1, f"missing or duplicate tier {tier}"


def test_missing_tier_line_counted_but_zero_dollars() -> None:
    """A MISSING line contributes a count but $0 in dollars (its
    total_cost is zero by construction)."""
    est = _estimate([
        _line(
            description="missing",
            confidence=0.92,
            price_confidence=0.0,
            tier=CostSourceTier.MISSING,
            total=0.0,
            suppressed=True,
        ),
    ])
    assert est.count_by_tier[CostSourceTier.MISSING] == 1
    assert est.total_by_tier[CostSourceTier.MISSING] == 0.0


def test_count_by_tier_sums_to_total_line_count() -> None:
    """count_by_tier values must sum to ``len(line_items)`` — every line
    lands in exactly one bucket."""
    est = _estimate([
        _line(description="a", tier=CostSourceTier.EXACT_MATCH, total=1.0),
        _line(description="b", tier=CostSourceTier.EXACT_MATCH, total=2.0),
        _line(description="c", tier=CostSourceTier.CATEGORY_MATCH, total=3.0),
        _line(description="d", tier=CostSourceTier.INTERPOLATED, total=4.0),
        _line(description="e", tier=CostSourceTier.PARAMETRIC, total=5.0),
    ])
    assert sum(est.count_by_tier.values()) == len(est.line_items)


def test_total_by_tier_reconciles_to_subtotal_when_all_in_headline() -> None:
    """When every line is in AUTO+REVIEW (no HAND, no MISSING $),
    the sum across all tier dollars equals the subtotal."""
    est = _estimate([
        _line(
            description="a",
            confidence=0.95,
            price_confidence=0.95,
            tier=CostSourceTier.EXACT_MATCH,
            total=100.0,
        ),
        _line(
            description="b",
            confidence=0.92,
            price_confidence=0.78,
            tier=CostSourceTier.CATEGORY_MATCH,
            total=200.0,
        ),
    ])
    tier_dollars = round(sum(est.total_by_tier.values()), 2)
    assert tier_dollars == pytest.approx(est.subtotal)
    assert tier_dollars == pytest.approx(300.0)


# ---------------------------------------------------------------------------
# Section 5 — backward-compat for T6
# ---------------------------------------------------------------------------


def test_pre_t7_costline_without_price_confidence_defaults_to_one() -> None:
    """A CostLine constructed without explicit price_confidence (the
    pre-T7 fixture pattern) must default to 1.0 so combined == qty,
    preserving T6 band semantics."""
    li = CostLine(
        csi_division="03",
        description="Slab",
        quantity=1.0,
        unit="SF",
        unit_cost=10.0,
        total_cost=10.0,
        confidence=0.78,
    )
    assert li.price_confidence == 1.0
    assert li.cost_source_tier == CostSourceTier.EXACT_MATCH
    assert li.combined_confidence == pytest.approx(0.78)


def test_pre_t7_estimate_band_aggregates_unchanged() -> None:
    """An estimate built entirely from pre-T7 CostLines (default tier
    + default price_confidence) must produce the same T6 aggregates
    as before — verifies backward-compat of band thresholds."""
    est = _estimate([
        _line(confidence=0.92, total=1000.0, description="auto"),
        _line(confidence=0.78, total=2500.0, description="review"),
        _line(confidence=0.55, total=4000.0, description="hand"),
    ])
    # Same numbers the T6 file asserts.
    assert est.total_auto_approve == 1000.0
    assert est.total_operator_review == 2500.0
    assert est.total_hand_takeoff == 4000.0
    assert est.subtotal == 3500.0


def test_pre_t7_costline_round_trips_through_model_dump_and_validate() -> None:
    """An old payload (no T7 keys at all) must validate cleanly because
    the new fields have defaults."""
    old_payload = {
        "csi_division": "09",
        "csi_section": "09 91 23",
        "description": "Interior painting",
        "quantity": 100.0,
        "unit": "SF",
        "unit_cost": 2.0,
        "total_cost": 200.0,
        "confidence": 0.78,
    }
    rebuilt = CostLine.model_validate(old_payload)
    assert rebuilt.price_confidence == 1.0
    assert rebuilt.cost_source_tier == CostSourceTier.EXACT_MATCH
    assert rebuilt.cost_band == CostBand.AUTO_APPROVE  # field default


def test_t6_default_takeoff_confidence_07_routes_into_grand_total(
    tmp_path: Path,
) -> None:
    """T6 fixture re-asserted: default ``TakeoffItem.confidence == 0.7``
    + seed-DB hit (price_conf=0.95) → combined=0.665 → OPERATOR_REVIEW
    → still rolls into headline grand_total."""
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Slab on grade",
            quantity=100.0,
            unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    line = est.line_items[0]
    assert line.cost_band == CostBand.OPERATOR_REVIEW
    assert est.grand_total > 0


# ---------------------------------------------------------------------------
# Section 6 — integration via price_takeoff()
# ---------------------------------------------------------------------------


def test_price_takeoff_cwicr_high_similarity_lands_in_exact_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="X",
        description="Concrete slab on grade",
        unit="SF",
        unit_price=8.0,
        labor_cost=2.0,
        material_cost=5.0,
        equipment_cost=1.0,
        region="usa_usd",
        year=2025,
        similarity=0.95,
        source_row_id=1,
    )
    matcher = _stub_matcher_with(cand)

    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Slab on grade",
            quantity=100.0,
            unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.EXACT_MATCH
    assert line.price_confidence == pytest.approx(0.95)


def test_price_takeoff_cwicr_mid_similarity_lands_in_category_match(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR similarity in [0.75, 0.92) → CATEGORY_MATCH; price_confidence
    = similarity × 0.85 (the Phase T7 spec)."""
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="Y",
        description="Concrete slab",
        unit="SF",
        unit_price=8.0,
        labor_cost=2.0,
        material_cost=5.0,
        equipment_cost=1.0,
        region="usa_usd",
        year=2025,
        similarity=0.80,
        source_row_id=2,
    )
    matcher = _stub_matcher_with(cand)

    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Slab on grade",
            quantity=100.0,
            unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.CATEGORY_MATCH
    assert line.price_confidence == pytest.approx(round(0.80 * 0.85, 4))
    assert line.price_confidence == pytest.approx(0.68)


def test_price_takeoff_seed_db_hit_lands_in_exact_match_with_seed_discount(
    tmp_path: Path,
) -> None:
    """Seed-DB hit (no CWICR) → EXACT_MATCH @ the seed-DB constant 0.95."""
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Slab on grade",
            quantity=100.0,
            unit="SF",
            confidence=0.92,
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        use_cwicr=False,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.EXACT_MATCH
    assert line.price_confidence == pytest.approx(COST_TIER_SEED_DB_PRICE_CONFIDENCE)
    assert line.price_confidence == pytest.approx(0.95)


def test_price_takeoff_unit_mismatch_lands_in_missing_tier(
    tmp_path: Path,
) -> None:
    """Suppressed unit-mismatch line → tier=MISSING + price_conf=0
    (the catalog-completeness equivalent of the T6 HAND_TAKEOFF
    suppression rule)."""
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="05",
            csi_section="05 12 00",
            description="2x12 beams",
            quantity=8.0,
            unit="LF",
            confidence=0.99,
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
    assert line.cost_source_tier == CostSourceTier.MISSING
    assert line.price_confidence == 0.0
    assert line.cost_band == CostBand.HAND_TAKEOFF


def test_price_takeoff_emitted_lines_round_trip_through_model_dump(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every emitted line must round-trip through ``CostLine.model_dump()``
    and back without validation errors — guards the JSON export path."""
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="X",
        description="Concrete slab",
        unit="SF",
        unit_price=8.0,
        labor_cost=2.0,
        material_cost=5.0,
        equipment_cost=1.0,
        region="usa_usd",
        year=2025,
        similarity=0.95,
        source_row_id=1,
    )
    matcher = _stub_matcher_with(cand)
    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Slab on grade",
            quantity=100.0,
            unit="SF",
        ),
        # No-match line → MISSING.
        TakeoffItem(
            csi_division="42",
            csi_section="42 12 34",
            description="something we don't price",
            quantity=1.0,
            unit="LS",
        ),
    ]
    # Have CWICR match the first takeoff but not the second by switching
    # the stub return to empty after the first call.
    seq = [[cand], []]
    matcher.match.side_effect = lambda *a, **kw: seq.pop(0) if seq else []

    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=matcher,
    )
    for line in est.line_items:
        payload = line.model_dump()
        assert "price_confidence" in payload
        assert "cost_source_tier" in payload
        rebuilt = CostLine.model_validate(payload)
        assert rebuilt.price_confidence == line.price_confidence
        assert rebuilt.cost_source_tier == line.cost_source_tier
        assert rebuilt.cost_band == line.cost_band
