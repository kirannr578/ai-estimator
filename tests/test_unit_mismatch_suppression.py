"""Tests for unit-mismatch cost suppression (Bug C from calibration v2).

Calibration v2 found two of the four cost-DB hits in the run shipped with
unit-mismatch warnings in `notes` but still rolled their `total_cost` into
the grand total — a single $34,608 phantom line that was 78% of the $44 K
headline.

These tests confirm:

  * `CostLine.suppressed` exists and defaults to False
  * `price_takeoff` flags unit-mismatched lines as `suppressed=True` with
    zero cost values and a clear notes message
  * suppressed lines are kept in `Estimate.line_items` (visibility) but
    excluded from `Estimate.subtotal`, `by_division`, `by_cost_category`,
    contingency / overhead / profit / grand_total, AND `priced_line_items`
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.estimator import CostDatabase, price_takeoff
from core.schemas import (
    CostLine,
    Estimate,
    SiteInfo,
    TakeoffItem,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


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
        project_info=ProjectInfo(name="Unit Mismatch Test"),
        scope_matrix=ScopeMatrix(packages=[], by_division={}, all_alternates=[], coverage_warnings=[]),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _write_cost_db(tmp_path: Path) -> Path:
    """Two entries: 05 12 00 priced per TON, 03 30 00 priced per SF."""
    db = {
        "_meta": {"version": "test"},
        "05 12 00": {
            "description": "Structural steel framing",
            "unit": "TON",
            "unit_cost": 4200,
            "cost_category": "subcontractor",
            "waste_factor": 1.03,
            "keywords": ["beam", "structural steel"],
        },
        "03 30 00": {
            "description": "Slab on grade",
            "unit": "SF",
            "unit_cost": 7.25,
            "cost_category": "subcontractor",
            "waste_factor": 1.07,
            "keywords": ["slab", "concrete"],
        },
    }
    path = tmp_path / "cost_database.json"
    path.write_text(json.dumps(db), encoding="utf-8")
    return path


# ---- schema-level invariants ----------------------------------------------


def test_costline_suppressed_defaults_false() -> None:
    line = CostLine(
        csi_division="03",
        description="Slab",
        quantity=100,
        unit="SF",
        unit_cost=7.25,
        total_cost=725.0,
    )
    assert line.suppressed is False


def test_estimate_subtotal_excludes_suppressed_lines() -> None:
    """`subtotal` ignores suppressed lines even when they carry totals."""
    est = Estimate(
        project_name="x",
        line_items=[
            CostLine(
                csi_division="03", description="Slab", quantity=100, unit="SF",
                unit_cost=7.25, total_cost=725.0,
            ),
            CostLine(
                csi_division="05", description="Beams (mismatch)", quantity=8, unit="LF",
                unit_cost=0.0, total_cost=0.0, suppressed=True,
            ),
            # Even if a suppressed line *somehow* still carries a total_cost
            # value (e.g. a hand-edited row in the Streamlit grid), the
            # rollup must still ignore it.
            CostLine(
                csi_division="05", description="Phantom", quantity=8, unit="LF",
                unit_cost=4200, total_cost=34608.0, suppressed=True,
            ),
        ],
    )
    assert est.subtotal == 725.0
    assert est.by_division == {"03": 725.0}
    assert est.grand_total == pytest.approx(
        round(725 * 1.10 * 1.10 * 1.05, 2)
    )
    assert len(est.line_items) == 3       # all three preserved for visibility
    assert len(est.priced_line_items) == 1
    assert len(est.suppressed_line_items) == 2


# ---- estimator-level integration ------------------------------------------


def test_price_takeoff_suppresses_unit_mismatch_lines(tmp_path: Path) -> None:
    """A LF beam takeoff against a TON cost-DB entry must end up
    `suppressed=True`, with zero unit_cost / total_cost, and must NOT
    contribute to any totals."""
    db = CostDatabase(_write_cost_db(tmp_path))

    takeoffs = [
        TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade",
            quantity=1000.0, unit="SF",
        ),
        TakeoffItem(
            csi_division="05", csi_section="05 12 00",
            description="2x12 beams",
            quantity=8.0, unit="LF",  # mismatch vs DB unit TON
        ),
    ]
    project = _make_project(takeoffs)
    est = price_takeoff(project, project_name="t", cost_db=db)

    assert len(est.line_items) == 2

    # Find the suppressed one by description.
    suppressed = [li for li in est.line_items if li.suppressed]
    priced = [li for li in est.line_items if not li.suppressed]
    assert len(suppressed) == 1
    assert len(priced) == 1

    sup = suppressed[0]
    assert sup.description == "2x12 beams"
    assert sup.unit_cost == 0.0
    assert sup.total_cost == 0.0
    assert sup.notes and "unit mismatch" in sup.notes.lower()
    assert "lf" in sup.notes.lower() and "ton" in sup.notes.lower()

    # Phantom line must NOT be in the headline subtotal.
    assert est.subtotal == priced[0].total_cost
    assert "05" not in est.by_division        # entire division dropped (it had only the suppressed line)
    assert est.by_cost_category.get("subcontractor", 0.0) == priced[0].total_cost
