"""Integration tests for the CWICR ↔ seed-DB layered cost lookup (F1).

Covers:

* When CWICR returns a candidate ≥ `CWICR_MIN_SIMILARITY`, the resulting
  `CostLine` has `cost_source = "cwicr:<row_id>"` and the seed DB lookup
  is **not** consulted.
* When CWICR's best candidate is below threshold, the seed-DB fallback
  fires and the line carries the seed-DB CSI key as `cost_source`.
* When CWICR is disabled (env var or explicit flag), no CWICR lookup
  ever happens — the run is identical to the pre-F1 estimator.
* Unit-mismatched CWICR matches are still suppressed (no $34 K phantom).
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock

import pytest

from core.estimator import CostDatabase, price_takeoff
from core.pricing.cwicr_matcher import CwicrCandidate, CwicrMatcher
from core.schemas import SiteInfo, TakeoffItem
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Helpers
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
        project_info=ProjectInfo(name="CWICR Integration Test"),
        scope_matrix=ScopeMatrix(packages=[], by_division={}, all_alternates=[], coverage_warnings=[]),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _seed_db(tmp_path: Path) -> CostDatabase:
    """Tiny seed DB used as the fallback layer in these tests."""
    db = {
        "_meta": {"version": "test"},
        "03 30 00": {
            "description": "Slab on grade",
            "unit": "SF",
            "unit_cost": 7.25,
            "cost_category": "subcontractor",
            "waste_factor": 1.07,
            "keywords": ["slab", "concrete"],
        },
        "09 91 23": {
            "description": "Interior painting",
            "unit": "SF",
            "unit_cost": 1.65,
            "cost_category": "subcontractor",
            "waste_factor": 1.10,
            "keywords": ["paint", "painting"],
        },
    }
    path = tmp_path / "cost_database.json"
    path.write_text(json.dumps(db), encoding="utf-8")
    return CostDatabase(path)


def _stub_matcher_with(candidate: CwicrCandidate | None) -> CwicrMatcher:
    """Build a matcher that always returns the same candidate (or empty)."""
    m = MagicMock(spec=CwicrMatcher)
    m.warm.return_value = None
    m.match.return_value = [candidate] if candidate is not None else []
    return m


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


def test_cwicr_winning_match_sets_cost_source_and_skips_seed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The CWICR layer should win and the seed DB layer must NOT be hit.

    We assert `cost_source` starts with `cwicr:`, the unit_cost is the
    CWICR candidate's `unit_price * region_multiplier`, and the seed-DB
    mock's `lookup` method is never called.
    """
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    monkeypatch.delenv("CWICR_MIN_SIMILARITY", raising=False)

    cwicr_cand = CwicrCandidate(
        code="CONC_SLAB_4IN",
        description="Concrete slab on grade 4 inch (CWICR)",
        unit="SF",
        unit_price=8.10,
        labor_cost=3.00,
        material_cost=4.50,
        equipment_cost=0.60,
        region="usa_usd",
        year=2025,
        similarity=0.81,
        source_row_id=42,
    )
    matcher = _stub_matcher_with(cwicr_cand)

    # A real seed DB exists but we'll spy on its lookup to confirm it's
    # never called for the CWICR-matched takeoff.
    db = _seed_db(tmp_path)
    db.lookup = MagicMock(wraps=db.lookup)  # type: ignore[method-assign]

    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 00",
            description="Concrete slab on grade",
            quantity=1000.0,
            unit="SF",
        ),
    ]
    project = _make_project(takeoffs)

    est = price_takeoff(
        project,
        project_name="t",
        region_multiplier=1.0,
        cost_db=db,
        cwicr_matcher=matcher,
    )

    assert len(est.line_items) == 1
    line = est.line_items[0]
    assert line.cost_source == "cwicr:42"
    assert line.suppressed is False
    assert line.unit_cost == pytest.approx(8.10)
    # quantity = raw * waste(1.07 for div 03) = 1070
    assert line.quantity == pytest.approx(1070.0)
    assert line.total_cost == pytest.approx(round(8.10 * 1070.0, 2))
    # The confidence carries the matcher's similarity, not the takeoff's.
    assert line.confidence == pytest.approx(0.81)

    # The seed DB lookup MUST NOT have been called for this takeoff.
    db.lookup.assert_not_called()


def test_below_threshold_cwicr_match_falls_back_to_seed_db(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "0.55")

    weak_cand = CwicrCandidate(
        code="UNRELATED",
        description="Definitely-not-painting Russian-origin pavement",
        unit="m2",
        unit_price=99.0,
        labor_cost=0.0,
        material_cost=0.0,
        equipment_cost=0.0,
        region="usa_usd",
        year=2025,
        similarity=0.20,  # well below 0.55
        source_row_id=99,
    )
    matcher = _stub_matcher_with(weak_cand)
    db = _seed_db(tmp_path)

    takeoffs = [
        TakeoffItem(
            csi_division="09",
            csi_section="09 91 23",
            description="Interior painting walls",
            quantity=2500.0,
            unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        cwicr_matcher=matcher,
    )

    line = est.line_items[0]
    assert line.cost_source == "09 91 23"
    assert line.suppressed is False
    assert line.unit_cost == pytest.approx(1.65)


def test_unit_mismatch_on_cwicr_match_is_suppressed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR wins the description match, but the candidate's unit is
    metric (m3) and the takeoff is CY → must be suppressed (no $34K
    phantom)."""
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "0.55")

    cand = CwicrCandidate(
        code="CONC_FOOT_M3",
        description="Concrete spread footings",
        unit="m3",  # metric — does not match CY takeoff
        unit_price=220.0,
        labor_cost=60.0,
        material_cost=140.0,
        equipment_cost=20.0,
        region="usa_usd",
        year=2025,
        similarity=0.88,
        source_row_id=7,
    )
    matcher = _stub_matcher_with(cand)
    db = _seed_db(tmp_path)

    takeoffs = [
        TakeoffItem(
            csi_division="03",
            csi_section="03 30 53",
            description="Concrete footings",
            quantity=12.0,
            unit="CY",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        cwicr_matcher=matcher,
    )

    assert len(est.line_items) == 1
    line = est.line_items[0]
    assert line.cost_source == "cwicr:7"
    assert line.suppressed is True
    assert line.unit_cost == 0.0
    assert line.total_cost == 0.0
    assert line.notes is not None and "unit mismatch" in line.notes.lower()
    assert est.subtotal == 0.0


def test_cwicr_disabled_flag_skips_matcher_entirely(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`use_cwicr=False` keeps `matcher.match` from ever being called."""
    monkeypatch.delenv("CWICR_DISABLED", raising=False)

    matcher = _stub_matcher_with(CwicrCandidate(
        code="X", description="x", unit="EA", unit_price=1.0,
        labor_cost=0.0, material_cost=0.0, equipment_cost=0.0,
        region="usa_usd", year=2025, similarity=0.99, source_row_id=0,
    ))
    db = _seed_db(tmp_path)

    takeoffs = [
        TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior painting walls",
            quantity=100.0, unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        cwicr_matcher=matcher,
        use_cwicr=False,
    )

    matcher.match.assert_not_called()
    assert est.line_items[0].cost_source == "09 91 23"


def test_cwicr_disabled_env_var_overrides_default(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CWICR_DISABLED", "true")

    matcher = _stub_matcher_with(CwicrCandidate(
        code="X", description="x", unit="EA", unit_price=1.0,
        labor_cost=0.0, material_cost=0.0, equipment_cost=0.0,
        region="usa_usd", year=2025, similarity=0.99, source_row_id=0,
    ))
    db = _seed_db(tmp_path)

    takeoffs = [
        TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior painting walls",
            quantity=100.0, unit="SF",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=db,
        cwicr_matcher=matcher,
    )

    matcher.match.assert_not_called()
    assert est.line_items[0].cost_source == "09 91 23"


# ---------------------------------------------------------------------------
# Phase T7 — price-confidence + cost-source-tier integration
# ---------------------------------------------------------------------------
#
# These tests verify that ``price_takeoff`` populates BOTH the T6
# ``cost_band`` axis AND the new T7 ``cost_source_tier`` /
# ``price_confidence`` axes on every emitted line, and that the band
# assignment now uses ``combined_confidence = qty × price`` instead of
# qty alone.


def test_t7_cwicr_similarity_095_lands_in_exact_match_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR similarity ≥ 0.92 → EXACT_MATCH; price_confidence == similarity."""
    from core.schemas import CostBand, CostSourceTier
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="X", description="Concrete slab", unit="SF",
        unit_price=8.0, labor_cost=2.0, material_cost=5.0, equipment_cost=1.0,
        region="usa_usd", year=2025, similarity=0.95, source_row_id=11,
    )
    matcher = _stub_matcher_with(cand)
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
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.EXACT_MATCH
    assert line.price_confidence == pytest.approx(0.95)
    # combined = 0.95 × 0.95 = 0.9025 → AUTO_APPROVE
    assert line.cost_band == CostBand.AUTO_APPROVE


def test_t7_cwicr_similarity_080_lands_in_category_match_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR similarity in [0.75, 0.92) → CATEGORY_MATCH;
    price_confidence = similarity × 0.85."""
    from core.schemas import CostSourceTier
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="Y", description="Concrete", unit="SF",
        unit_price=8.0, labor_cost=2.0, material_cost=5.0, equipment_cost=1.0,
        region="usa_usd", year=2025, similarity=0.80, source_row_id=12,
    )
    matcher = _stub_matcher_with(cand)
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
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.CATEGORY_MATCH
    assert line.price_confidence == pytest.approx(round(0.80 * 0.85, 4))
    assert line.price_confidence == pytest.approx(0.68)


def test_t7_cwicr_similarity_060_lands_in_interpolated_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """CWICR similarity in [0.50, 0.75) → INTERPOLATED;
    price_confidence = 0.65 (the per-tier constant)."""
    from core.schemas import CostSourceTier
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "0.55")
    cand = CwicrCandidate(
        code="Z", description="Concrete (loose match)", unit="SF",
        unit_price=8.0, labor_cost=2.0, material_cost=5.0, equipment_cost=1.0,
        region="usa_usd", year=2025, similarity=0.60, source_row_id=13,
    )
    matcher = _stub_matcher_with(cand)
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
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.cost_source_tier == CostSourceTier.INTERPOLATED
    assert line.price_confidence == pytest.approx(0.65)


def test_t7_seed_db_hit_lands_in_exact_match_with_seed_constant(
    tmp_path: Path,
) -> None:
    """Seed-DB-only hit → tier=EXACT_MATCH @ price_confidence=0.95
    (the ``COST_TIER_SEED_DB_PRICE_CONFIDENCE`` discount)."""
    from core.schemas import COST_TIER_SEED_DB_PRICE_CONFIDENCE, CostSourceTier
    db = _seed_db(tmp_path)
    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade", quantity=100.0, unit="SF",
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


def test_t7_unit_mismatch_suppressed_lands_in_missing_tier(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Suppressed unit-mismatch line → tier=MISSING + price_conf=0,
    even when the upstream CWICR / seed candidate had a usable
    similarity. Mirrors the T6 HAND_TAKEOFF suppression rule on the
    T7 axis."""
    from core.schemas import CostSourceTier
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="MISMATCH", description="Concrete footings",
        unit="m3",  # metric — does not match CY
        unit_price=220.0, labor_cost=60.0, material_cost=140.0,
        equipment_cost=20.0, region="usa_usd", year=2025,
        similarity=0.95, source_row_id=99,
    )
    matcher = _stub_matcher_with(cand)
    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 53",
            description="Concrete footings", quantity=12.0, unit="CY",
        ),
    ]
    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=matcher,
    )
    line = est.line_items[0]
    assert line.suppressed is True
    assert line.cost_source_tier == CostSourceTier.MISSING
    assert line.price_confidence == 0.0


def test_t7_price_takeoff_populates_both_cost_band_and_tier_on_every_line(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every emitted line carries BOTH ``cost_band`` (T6) AND
    ``cost_source_tier`` + ``price_confidence`` (T7). Sanity guard
    against future regressions where one axis silently stops being
    populated."""
    from core.schemas import CostBand, CostSourceTier
    monkeypatch.delenv("CWICR_DISABLED", raising=False)
    cand = CwicrCandidate(
        code="X", description="Concrete", unit="SF",
        unit_price=8.0, labor_cost=2.0, material_cost=5.0, equipment_cost=1.0,
        region="usa_usd", year=2025, similarity=0.95, source_row_id=1,
    )
    matcher = _stub_matcher_with(cand)
    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade", quantity=100.0, unit="SF",
        ),
        # No-match → MISSING.
        TakeoffItem(
            csi_division="42", csi_section="42 12 34",
            description="something exotic", quantity=1.0, unit="LS",
        ),
    ]
    seq = [[cand], []]
    matcher.match.side_effect = lambda *a, **kw: seq.pop(0) if seq else []

    est = price_takeoff(
        _make_project(takeoffs),
        project_name="t",
        cost_db=_seed_db(tmp_path),
        cwicr_matcher=matcher,
    )
    for line in est.line_items:
        assert isinstance(line.cost_band, CostBand)
        assert isinstance(line.cost_source_tier, CostSourceTier)
        assert 0.0 <= line.price_confidence <= 1.0


def test_t7_band_uses_combined_confidence_not_qty_alone() -> None:
    """High qty (0.95) × low price_conf (0.5) → combined=0.475 → HAND.
    Demonstrates that the band-assignment input is the COMBINED value,
    not qty alone (would have been AUTO under T6 with qty=0.95)."""
    from core.estimator import _combined_band
    from core.schemas import CostBand
    band = _combined_band(0.95, 0.5, suppressed=False)
    assert band == CostBand.HAND_TAKEOFF
    # Sanity: under T6 (price=1.0), 0.95 was AUTO_APPROVE.
    assert _combined_band(0.95, 1.0, suppressed=False) == CostBand.AUTO_APPROVE
