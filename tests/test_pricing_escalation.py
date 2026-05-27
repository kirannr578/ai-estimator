"""Unit tests for core/pricing/escalation.py."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.pricing.escalation import (
    GENERIC_FALLBACK,
    _index_snapshots,
    compute_escalation_factor,
    escalate_cost_database,
    pick_ppi_series,
)
from core.pricing.snapshots import PricingSnapshot


def _snap(series_id: str, period: str, value: float) -> PricingSnapshot:
    return PricingSnapshot(
        source="bls_ppi",
        series_id=series_id,
        label=series_id,
        unit="index",
        value=value,
        period=period,
        fetched_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        license="x",
        source_url="x",
    )


def test_pick_ppi_series_section_override_first() -> None:
    assert pick_ppi_series("06 10 00", "Wood framing - rough carpentry") == "WPU0811"
    assert pick_ppi_series("09 29 00", "Gypsum board, 5/8\"") == "WPU102201"


def test_pick_ppi_series_keyword_fallback() -> None:
    assert pick_ppi_series("99 99 99", "Acoustical drywall panel") == "WPU102201"
    assert pick_ppi_series("99 99 99", "Painted finish") == "WPU065"


def test_pick_ppi_series_division_fallback() -> None:
    # "13 00 00" has no exact section override and no keyword hit.
    assert pick_ppi_series("13 00 00", "special construction") == "WPUSI012011"
    # "32 90 00" — landscaping — keyword "landscape" isn't in our table,
    # so we should fall through to division 32 = WPU132 (concrete proxy).
    assert pick_ppi_series("32 90 00", "Landscaping (sod + shrubs allowance)") == "WPU132"


def test_pick_ppi_series_generic_fallback_for_unknown_division() -> None:
    assert pick_ppi_series("99 99 99", "totally unknown") == GENERIC_FALLBACK


def test_compute_escalation_factor_exact_period() -> None:
    snaps = [
        _snap("WPU0811", "2026-01", 100.0),
        _snap("WPU0811", "2026-04", 110.0),
    ]
    available = _index_snapshots(snaps)
    factor, used = compute_escalation_factor("WPU0811", "2026-01", "2026-04", available)
    assert factor == pytest.approx(1.10)
    assert used == "WPU0811"


def test_compute_escalation_factor_falls_back_to_nearest_prior() -> None:
    # Only Jan and Mar are present; asking for Feb -> Apr should use Jan as
    # base (≤ Feb) and Mar as target (≤ Apr).
    snaps = [
        _snap("WPU0811", "2026-01", 100.0),
        _snap("WPU0811", "2026-03", 105.0),
    ]
    available = _index_snapshots(snaps)
    factor, used = compute_escalation_factor("WPU0811", "2026-02", "2026-04", available)
    assert factor == pytest.approx(1.05)
    assert used == "WPU0811"


def test_compute_escalation_factor_generic_fallback() -> None:
    # Series the cost-DB asks for has no data; should fall back to
    # WPUSI012011 if that one does.
    snaps = [
        _snap(GENERIC_FALLBACK, "2026-01", 200.0),
        _snap(GENERIC_FALLBACK, "2026-04", 220.0),
    ]
    available = _index_snapshots(snaps)
    factor, used = compute_escalation_factor("WPU0811", "2026-01", "2026-04", available)
    assert factor == pytest.approx(1.10)
    assert used == GENERIC_FALLBACK


def test_compute_escalation_factor_same_period_is_identity() -> None:
    factor, used = compute_escalation_factor("WPU0811", "2026-04", "2026-04", {})
    assert factor == 1.0
    assert used == "WPU0811"


def test_compute_escalation_factor_missing_data_is_identity() -> None:
    factor, used = compute_escalation_factor("WPU0811", "2026-01", "2026-04", {})
    assert factor == 1.0


def test_compute_escalation_factor_zero_base_is_identity() -> None:
    snaps = [
        _snap("WPU0811", "2026-01", 0.0),
        _snap("WPU0811", "2026-04", 110.0),
    ]
    available = _index_snapshots(snaps)
    factor, _ = compute_escalation_factor("WPU0811", "2026-01", "2026-04", available)
    assert factor == 1.0


def test_escalate_cost_database_end_to_end(tmp_path: Path) -> None:
    seed = {
        "_meta": {"version": "2026.05", "currency": "USD"},
        "06 10 00": {
            "description": "Wood framing - rough carpentry",
            "unit": "SF", "unit_cost": 8.75, "cost_category": "labor",
            "waste_factor": 1.10, "keywords": ["framing"],
        },
        "09 29 00": {
            "description": "Gypsum board, 5/8\" - one side",
            "unit": "SF", "unit_cost": 2.85, "cost_category": "subcontractor",
            "waste_factor": 1.12, "keywords": ["drywall"],
        },
        "99 99 99": {
            "description": "totally unknown item",
            "unit": "EA", "unit_cost": 100.0,
        },
    }

    input_path = tmp_path / "cost_database.json"
    output_path = tmp_path / "cost_database_escalated.json"
    input_path.write_text(json.dumps(seed), encoding="utf-8")

    snaps = [
        _snap("WPU0811", "2026-01", 100.0),
        _snap("WPU0811", "2026-04", 120.0),       # framing +20%
        _snap("WPU102201", "2026-01", 200.0),
        _snap("WPU102201", "2026-04", 210.0),     # gypsum +5%
        _snap(GENERIC_FALLBACK, "2026-01", 50.0),
        _snap(GENERIC_FALLBACK, "2026-04", 55.0), # generic  +10%
    ]

    out = escalate_cost_database(
        input_path, output_path,
        base_period="2026-01", target_period="2026-04",
        ppi_snapshots=snaps,
    )

    assert output_path.exists()
    framing = out["06 10 00"]
    assert framing["unit_cost"] == pytest.approx(8.75 * 1.20)
    assert framing["ppi_series_used"] == "WPU0811"
    assert framing["escalation_factor"] == pytest.approx(1.20)
    assert framing["escalated_from_period"] == "2026-01"
    # Original fields preserved.
    assert framing["unit"] == "SF"
    assert framing["waste_factor"] == 1.10

    gyp = out["09 29 00"]
    assert gyp["unit_cost"] == pytest.approx(2.85 * 1.05)
    assert gyp["ppi_series_used"] == "WPU102201"

    unknown = out["99 99 99"]
    assert unknown["unit_cost"] == pytest.approx(100.0 * 1.10)
    assert unknown["ppi_series_used"] == GENERIC_FALLBACK

    # _meta annotated with escalation info, original meta preserved.
    assert "escalated_at" in out["_meta"]
    assert out["_meta"]["version"] == "2026.05"


def test_escalate_cost_database_idempotent_when_periods_match(tmp_path: Path) -> None:
    seed = {
        "06 10 00": {"description": "Wood framing", "unit": "SF",
                     "unit_cost": 8.75},
    }
    input_path = tmp_path / "in.json"
    output_path = tmp_path / "out.json"
    input_path.write_text(json.dumps(seed), encoding="utf-8")

    out = escalate_cost_database(
        input_path, output_path,
        base_period="2026-04", target_period="2026-04",
        ppi_snapshots=[],
    )
    assert out["06 10 00"]["unit_cost"] == 8.75
    assert out["06 10 00"]["escalation_factor"] == 1.0
