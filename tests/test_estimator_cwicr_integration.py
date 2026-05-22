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
