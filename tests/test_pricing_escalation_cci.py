"""Unit tests for the macro CCI multiplier hook in core/pricing/escalation.py.

These tests cover the Phase C closing slice that layers an ENR / AGC /
Turner CCI macro multiplier on top of the per-CSI BLS PPI escalation.
The companion tests for the per-CSI engine live in
``tests/test_pricing_escalation.py``.

No network calls: all snapshots are injected via the
``snapshots_by_source`` parameter so the tests run offline.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.pricing.escalation import (
    EscalationMissingBaseline,
    apply_macro_cci_multiplier,
    escalate_cost_database,
)
from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import PricingSourceUnavailable


def _cci_snap(
    source: str,
    series_id: str,
    period: str,
    value: float,
) -> PricingSnapshot:
    return PricingSnapshot(
        source=source,
        series_id=series_id,
        label=f"{source} {series_id}",
        unit="index",
        value=value,
        region="US",
        csi_division=None,
        naics="23",
        period=period,
        fetched_at=datetime(2026, 5, 27, tzinfo=timezone.utc),
        license="test",
        source_url=f"https://example.test/{source}",
    )


def _write_seed_db(path: Path) -> dict:
    seed = {
        "_meta": {"version": "2026.05", "currency": "USD"},
        "06 10 00": {
            "description": "Wood framing — rough carpentry",
            "unit": "SF", "unit_cost": 10.00,
        },
        "09 29 00": {
            "description": "Gypsum board, 5/8\"",
            "unit": "SF", "unit_cost": 4.00,
        },
        "26 05 00": {
            "description": "Branch wiring — copper",
            "unit": "LF", "unit_cost": 6.00,
        },
    }
    path.write_text(json.dumps(seed), encoding="utf-8")
    return seed


# --- 1. Multiplier computation from synthetic CCI snapshot pair ---------

def test_multiplier_computed_from_baseline_and_latest(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 14_000.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),
        ],
    }

    out = apply_macro_cci_multiplier(
        db_path,
        base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=tmp_path / "escalated_with_cci.json",
    )

    # 14_700 / 14_000 = 1.05 exactly
    assert out["_meta"]["macro_cci_multiplier"] == pytest.approx(1.05)
    framing = out["06 10 00"]
    assert framing["macro_cci_multiplier"] == pytest.approx(1.05)
    assert framing["unit_cost"] == pytest.approx(10.00 * 1.05)
    assert framing["macro_cci_source"] == "enr_cci"
    assert framing["macro_cci_baseline_period"] == "2024-01"
    assert framing["macro_cci_latest_period"] == "2026-04"


# --- 2. Uniform application across all entries -------------------------

def test_uniform_application_across_all_entries(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    seed = _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 100.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 110.0),
        ],
    }

    out = apply_macro_cci_multiplier(
        db_path,
        base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )

    multiplier = 110.0 / 100.0
    for section in ("06 10 00", "09 29 00", "26 05 00"):
        assert out[section]["unit_cost"] == pytest.approx(
            seed[section]["unit_cost"] * multiplier
        )
        assert out[section]["macro_cci_multiplier"] == pytest.approx(multiplier)
        assert out[section]["macro_cci_source"] == "enr_cci"


# --- 3. Missing baseline raises EscalationMissingBaseline ---------------

def test_missing_baseline_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    # Only have snapshots AFTER 2024-01; no period ≤ "2020-01" exists.
    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2025-01", 14_500.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),
        ],
    }

    with pytest.raises(EscalationMissingBaseline):
        apply_macro_cci_multiplier(
            db_path,
            base_period="2020-01",
            snapshots_by_source=snaps,
            out_path=tmp_path / "out.json",
        )


def test_missing_baseline_zero_value_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 0.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),
        ],
    }

    with pytest.raises(EscalationMissingBaseline):
        apply_macro_cci_multiplier(
            db_path,
            base_period="2024-01",
            snapshots_by_source=snaps,
            out_path=tmp_path / "out.json",
        )


# --- 4. Missing latest raises PricingSourceUnavailable ------------------

def test_missing_all_sources_raises_pricing_source_unavailable(
    tmp_path: Path,
) -> None:
    """When every source in the fallback chain has zero snapshots."""
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps: dict = {
        "enr_cci": [],
        "agc_cci": [],
        "turner_cci": [],
    }

    with pytest.raises(PricingSourceUnavailable):
        apply_macro_cci_multiplier(
            db_path,
            base_period="2024-01",
            snapshots_by_source=snaps,
            out_path=tmp_path / "out.json",
        )


def test_empty_dict_falls_through_all_sources(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    with pytest.raises(PricingSourceUnavailable):
        apply_macro_cci_multiplier(
            db_path,
            base_period="2024-01",
            snapshots_by_source={},
            out_path=tmp_path / "out.json",
        )


# --- 5. AGC + Turner fallback when ENR unavailable ----------------------

def test_agc_fallback_when_enr_unavailable(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [],  # ENR unavailable
        "agc_cci": [
            _cci_snap("agc_cci", "national", "2024-01", 300.0),
            _cci_snap("agc_cci", "national", "2026-04", 315.0),
        ],
    }

    out = apply_macro_cci_multiplier(
        db_path,
        base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    framing = out["06 10 00"]
    assert framing["macro_cci_source"] == "agc_cci"
    assert framing["macro_cci_multiplier"] == pytest.approx(315.0 / 300.0)


def test_turner_fallback_when_enr_and_agc_unavailable(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    # Turner is quarterly — baseline must be in YYYY-QN format.
    snaps = {
        "enr_cci": [],
        "agc_cci": [],
        "turner_cci": [
            _cci_snap("turner_cci", "national", "2024-Q1", 1500.0),
            _cci_snap("turner_cci", "national", "2026-Q1", 1575.0),
        ],
    }

    out = apply_macro_cci_multiplier(
        db_path,
        base_period="2024-Q1",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    framing = out["06 10 00"]
    assert framing["macro_cci_source"] == "turner_cci"
    assert framing["macro_cci_multiplier"] == pytest.approx(1575.0 / 1500.0)
    assert framing["macro_cci_baseline_period"] == "2024-Q1"


def test_explicit_cci_source_override(tmp_path: Path) -> None:
    """If the caller explicitly picks turner_cci, ENR availability does
    not preempt the choice."""
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 14_000.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),
        ],
        "turner_cci": [
            _cci_snap("turner_cci", "national", "2024-Q1", 1500.0),
            _cci_snap("turner_cci", "national", "2026-Q1", 1650.0),
        ],
    }

    out = apply_macro_cci_multiplier(
        db_path,
        base_period="2024-Q1",
        cci_source="turner_cci",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    assert out["06 10 00"]["macro_cci_source"] == "turner_cci"
    assert out["06 10 00"]["macro_cci_multiplier"] == pytest.approx(1.10)


# --- 6. Output file written to the expected path -----------------------

def test_default_out_path_appends_with_cci_suffix(tmp_path: Path) -> None:
    db_path = tmp_path / "cost_database_escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 100.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 110.0),
        ],
    }

    apply_macro_cci_multiplier(
        db_path,
        base_period="2024-01",
        snapshots_by_source=snaps,
    )

    expected = tmp_path / "cost_database_escalated_with_cci.json"
    assert expected.exists()
    assert db_path.exists()  # Input untouched.
    # And the per-CSI escalated input differs from the CCI-multiplied
    # output by exactly the multiplier on at least one entry.
    out = json.loads(expected.read_text(encoding="utf-8"))
    assert out["06 10 00"]["unit_cost"] == pytest.approx(10.00 * 1.10)


def test_explicit_out_path_respected(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)
    out_path = tmp_path / "custom_subdir" / "result.json"

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 100.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 110.0),
        ],
    }

    apply_macro_cci_multiplier(
        db_path,
        base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=out_path,
    )
    assert out_path.exists()


# --- 7. Idempotency — same input + same snapshots → same output ---------

def test_idempotent_same_inputs_same_output(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 100.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 110.0),
        ],
    }
    out1_path = tmp_path / "out1.json"
    out2_path = tmp_path / "out2.json"

    out1 = apply_macro_cci_multiplier(
        db_path, base_period="2024-01",
        snapshots_by_source=snaps, out_path=out1_path,
    )
    out2 = apply_macro_cci_multiplier(
        db_path, base_period="2024-01",
        snapshots_by_source=snaps, out_path=out2_path,
    )

    # Ignore _meta fields that may be unstable (none here, but defensive).
    for k in ("06 10 00", "09 29 00", "26 05 00"):
        assert out1[k]["unit_cost"] == pytest.approx(out2[k]["unit_cost"])
        assert out1[k]["macro_cci_multiplier"] == out2[k]["macro_cci_multiplier"]


def test_same_period_baseline_equals_latest_multiplier_is_one(
    tmp_path: Path,
) -> None:
    """Degenerate case: when baseline and latest are the same snapshot,
    the multiplier is 1.0 (cost-DB passes through unchanged save for
    audit fields)."""
    db_path = tmp_path / "escalated.json"
    seed = _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 14_000.0),
        ],
    }
    out = apply_macro_cci_multiplier(
        db_path, base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    assert out["_meta"]["macro_cci_multiplier"] == pytest.approx(1.0)
    assert out["06 10 00"]["unit_cost"] == pytest.approx(
        seed["06 10 00"]["unit_cost"]
    )


# --- 8. Integration smoke — full BLS PPI + macro CCI chain --------------

def test_full_bls_ppi_plus_macro_cci_chain_composes(tmp_path: Path) -> None:
    """End-to-end: per-CSI BLS PPI escalation followed by macro CCI
    multiplication produces a cumulative escalated unit_cost that is
    the product of the two factors."""
    seed = {
        "_meta": {"version": "2026.05"},
        "06 10 00": {
            "description": "Wood framing", "unit": "SF", "unit_cost": 10.00,
        },
    }
    seed_path = tmp_path / "cost_database.json"
    escalated_path = tmp_path / "cost_database_escalated.json"
    final_path = tmp_path / "cost_database_escalated_with_cci.json"
    seed_path.write_text(json.dumps(seed), encoding="utf-8")

    ppi_snaps = [
        PricingSnapshot(
            source="bls_ppi", series_id="WPU0811", label="Softwood lumber",
            unit="index", value=100.0, period="2024-01",
            fetched_at=datetime.now(timezone.utc),
            license="public", source_url="https://example.test/bls",
        ),
        PricingSnapshot(
            source="bls_ppi", series_id="WPU0811", label="Softwood lumber",
            unit="index", value=120.0, period="2026-04",  # +20%
            fetched_at=datetime.now(timezone.utc),
            license="public", source_url="https://example.test/bls",
        ),
    ]

    escalate_cost_database(
        seed_path, escalated_path,
        base_period="2024-01", target_period="2026-04",
        ppi_snapshots=ppi_snaps,
    )
    assert escalated_path.exists()
    intermediate = json.loads(escalated_path.read_text(encoding="utf-8"))
    # Sanity: per-CSI step scaled 10.00 by 1.20.
    assert intermediate["06 10 00"]["unit_cost"] == pytest.approx(12.00)

    cci_snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 14_000.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),  # +5%
        ],
    }
    final = apply_macro_cci_multiplier(
        escalated_path, base_period="2024-01",
        snapshots_by_source=cci_snaps,
        out_path=final_path,
    )
    assert final_path.exists()
    # Cumulative: 10.00 * 1.20 (PPI) * 1.05 (CCI) = 12.60
    assert final["06 10 00"]["unit_cost"] == pytest.approx(10.00 * 1.20 * 1.05)
    assert final["06 10 00"]["macro_cci_multiplier"] == pytest.approx(1.05)
    # And the per-CSI audit fields survive the macro pass.
    assert final["06 10 00"]["escalation_factor"] == pytest.approx(1.20)
    assert final["06 10 00"]["ppi_series_used"] == "WPU0811"
    # Input file (the per-CSI escalated DB) is NOT modified.
    intermediate_after = json.loads(escalated_path.read_text(encoding="utf-8"))
    assert intermediate_after["06 10 00"]["unit_cost"] == pytest.approx(12.00)


# --- Additional invariants --------------------------------------------

def test_meta_records_provenance(tmp_path: Path) -> None:
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2024-01", 100.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 110.0),
        ],
    }
    out = apply_macro_cci_multiplier(
        db_path, base_period="2024-01",
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    meta = out["_meta"]
    assert meta["macro_cci_source"] == "enr_cci"
    assert meta["macro_cci_baseline_value"] == pytest.approx(100.0)
    assert meta["macro_cci_latest_value"] == pytest.approx(110.0)
    assert "macro_cci_applied_at" in meta
    # The original meta field survives.
    assert meta["version"] == "2026.05"


def test_baseline_falls_back_to_nearest_prior_period(tmp_path: Path) -> None:
    """If exact base_period isn't present but an earlier snapshot is,
    use the most-recent snapshot ≤ base_period as the baseline."""
    db_path = tmp_path / "escalated.json"
    _write_seed_db(db_path)

    snaps = {
        "enr_cci": [
            _cci_snap("enr_cci", "national-20city", "2023-06", 14_000.0),
            _cci_snap("enr_cci", "national-20city", "2026-04", 14_700.0),
        ],
    }
    out = apply_macro_cci_multiplier(
        db_path, base_period="2024-01",  # no exact match
        snapshots_by_source=snaps,
        out_path=tmp_path / "out.json",
    )
    # Nearest prior is 2023-06.
    assert out["06 10 00"]["macro_cci_baseline_period"] == "2023-06"
    assert out["06 10 00"]["macro_cci_multiplier"] == pytest.approx(14_700.0 / 14_000.0)
