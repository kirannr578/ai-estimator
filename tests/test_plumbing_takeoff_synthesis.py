"""Tests for the Phase T2.9 plumbing-takeoff synthesis.

Builds in-memory ``PlumbingFixtureRecord`` instances and confirms the
fan-out shape: 1 fixture row + 1 rough-in row (water-supply or
waste-dominant depending on type) + optional 1 trim/hardware row
(emitted only when manufacturer AND model_number are both populated).
"""

from __future__ import annotations

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_PLUMBING,
    synthesize_plumbing_takeoff_items,
)
from core.schemas import PlumbingFixtureRecord, PlumbingScheduleResult


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _wc(*, qty: int | None = None, mfr: str | None = None,
        model: str | None = None) -> PlumbingFixtureRecord:
    return PlumbingFixtureRecord(
        fixture_tag="WC-1",
        fixture_type="WATER_CLOSET",
        description="Wall-hung water closet",
        manufacturer=mfr,
        model_number=model,
        mounting="WALL",
        flow_rate_value=1.28,
        flow_rate_unit="GPF",
        cold_water_size="1/2\"",
        waste_size="4\"",
        quantity=qty,
    )


def _lav(*, qty: int | None = None, mfr: str | None = None,
         model: str | None = None) -> PlumbingFixtureRecord:
    return PlumbingFixtureRecord(
        fixture_tag="LAV-A",
        fixture_type="LAVATORY",
        description="Counter-mount lavatory",
        manufacturer=mfr,
        model_number=model,
        mounting="COUNTER",
        flow_rate_value=0.5,
        flow_rate_unit="GPM",
        cold_water_size="1/2\"",
        hot_water_size="1/2\"",
        waste_size="1-1/2\"",
        quantity=qty,
    )


# ---------------------------------------------------------------------------
# Shape + count tests
# ---------------------------------------------------------------------------


def test_synthesize_empty_input_returns_empty() -> None:
    assert synthesize_plumbing_takeoff_items(None) == []
    assert synthesize_plumbing_takeoff_items([]) == []
    assert synthesize_plumbing_takeoff_items(
        PlumbingScheduleResult(fixtures=[])
    ) == []


def test_synthesize_wc_with_qty_and_mfr_emits_three_rows() -> None:
    """WC with QTY and (mfr+model) → 3 rows: fixture, rough-in, trim."""
    items = synthesize_plumbing_takeoff_items([
        _wc(qty=8, mfr="American Standard", model="3461.001"),
    ])
    assert len(items) == 3
    fixture, roughin, trim = items
    assert fixture.unit == "EA"
    assert fixture.quantity == 8.0
    assert fixture.confidence == 0.90  # QTY-published
    assert fixture.csi_section == "22 41 13"
    assert roughin.unit == "LS"
    assert roughin.confidence == 0.45  # parametric
    assert roughin.csi_section == "22 13 16"  # waste-dominant for WC
    assert trim.unit == "LS"
    assert trim.confidence == 0.70


def test_synthesize_wc_with_qty_no_mfr_emits_two_rows() -> None:
    """WC with QTY but no mfr/model → fixture + rough-in (no trim)."""
    items = synthesize_plumbing_takeoff_items([
        _wc(qty=8),
    ])
    assert len(items) == 2
    fixture, roughin = items
    assert fixture.confidence == 0.90
    assert roughin.csi_section == "22 13 16"


def test_synthesize_lav_without_qty_lands_in_hand_takeoff_band() -> None:
    """LAV without QTY → fixture confidence 0.55 (HAND_TAKEOFF)."""
    items = synthesize_plumbing_takeoff_items([_lav()])
    assert len(items) == 2  # no trim (no mfr/model)
    fixture, roughin = items
    assert fixture.quantity == 1.0
    assert fixture.confidence == 0.55
    assert fixture.csi_section == "22 41 16"
    assert roughin.csi_section == "22 11 16"  # supply-dominant for LAV


def test_synthesize_shower_with_mfr_emits_three_rows() -> None:
    """Shower with mfr+model → fixture + rough-in + trim."""
    record = PlumbingFixtureRecord(
        fixture_tag="SH-1",
        fixture_type="SHOWER",
        description="Shower",
        manufacturer="Symmons",
        model_number="TempControl-1",
        flow_rate_value=1.5,
        flow_rate_unit="GPM",
        quantity=2,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert len(items) == 3
    fixture, roughin, trim = items
    assert fixture.csi_section == "22 41 23"
    assert fixture.quantity == 2.0
    assert roughin.csi_section == "22 11 16"  # supply-dominant for SHOWER
    assert trim.csi_section == "22 41 23"  # trim shares fixture section


def test_synthesize_water_heater_no_trim_when_mfr_only() -> None:
    """Water heater with mfr but no model → 2 rows (no trim)."""
    record = PlumbingFixtureRecord(
        fixture_tag="WH-1",
        fixture_type="WATER_HEATER",
        description="Electric water heater",
        manufacturer="A.O. Smith",
        model_number=None,
        quantity=1,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert len(items) == 2
    fixture, roughin = items
    assert fixture.csi_section == "22 33 00"
    assert roughin.csi_section == "22 11 16"


def test_synthesize_floor_drain_routes_to_waste_roughin() -> None:
    """Floor drain → waste-dominant rough-in (22 13 16)."""
    record = PlumbingFixtureRecord(
        fixture_tag="FD-1",
        fixture_type="FLOOR_DRAIN",
        description="2-inch floor drain",
        waste_size="2\"",
        quantity=4,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert len(items) == 2  # no trim (no mfr/model)
    fixture, roughin = items
    assert fixture.csi_section == "22 13 19"
    assert roughin.csi_section == "22 13 16"


def test_synthesize_urinal_routes_to_waste_roughin() -> None:
    """Urinal → waste-dominant rough-in (22 13 16); shares WC section."""
    record = PlumbingFixtureRecord(
        fixture_tag="URN-1",
        fixture_type="URINAL",
        description="Wall-hung urinal",
        flow_rate_value=0.5,
        flow_rate_unit="GPF",
        quantity=2,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert items[0].csi_section == "22 41 13"  # shares WC section
    assert items[1].csi_section == "22 13 16"  # waste-dominant


def test_synthesize_ewc_routes_to_supply_roughin() -> None:
    record = PlumbingFixtureRecord(
        fixture_tag="EWC-1",
        fixture_type="EWC",
        description="ADA drinking fountain",
        manufacturer="Elkay",
        model_number="LZS8L",
        quantity=1,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert len(items) == 3
    assert items[0].csi_section == "22 47 13"
    assert items[1].csi_section == "22 11 16"  # supply-dominant


def test_synthesize_hose_bibb_routes_to_supply_roughin() -> None:
    record = PlumbingFixtureRecord(
        fixture_tag="HD-1",
        fixture_type="HOSE_BIBB",
        description="Exterior hose bibb",
        quantity=4,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert items[0].csi_section == "22 11 23"
    assert items[1].csi_section == "22 11 16"


def test_synthesize_mop_sink_csi_mapping() -> None:
    record = PlumbingFixtureRecord(
        fixture_tag="MS-1",
        fixture_type="MOP_SINK",
        description="Mop sink",
        quantity=1,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert items[0].csi_section == "22 41 19"


def test_synthesize_other_falls_back_to_generic_section() -> None:
    record = PlumbingFixtureRecord(
        fixture_tag="ICE-1",
        fixture_type="OTHER",
        description="Ice maker",
        quantity=1,
    )
    items = synthesize_plumbing_takeoff_items([record])
    assert items[0].csi_section == "22 00 00"
    # OTHER falls into the supply-dominant rough-in bucket
    assert items[1].csi_section == "22 11 16"


def test_synthesize_skips_blank_tags() -> None:
    record = PlumbingFixtureRecord(
        fixture_tag="",
        fixture_type="WATER_CLOSET",
        description="Should be skipped",
    )
    assert synthesize_plumbing_takeoff_items([record]) == []


def test_synthesize_notes_carry_source_tag() -> None:
    """Every emitted row's notes start with ``source=plumbing_schedule_prepass``."""
    items = synthesize_plumbing_takeoff_items([
        _wc(qty=2, mfr="Kohler", model="K-1234"),
    ])
    for item in items:
        assert item.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_PLUMBING}")
    # Trim row carries the trim role marker.
    assert "role=trim" in items[2].notes


def test_synthesize_description_prefix_is_plumbing_fixture() -> None:
    """Description uses ``Plumbing fixture <TAG>`` to disambiguate from lighting."""
    items = synthesize_plumbing_takeoff_items([
        _wc(qty=2, mfr="Kohler", model="K-1234"),
    ])
    for item in items:
        assert item.description.startswith("Plumbing fixture WC-1")


def test_synthesize_sheet_id_threads_into_source_sheet_ids() -> None:
    items = synthesize_plumbing_takeoff_items(
        [_wc(qty=2)],
        sheet_id="P2.0",
    )
    for item in items:
        assert item.source_sheet_ids == ["P2.0"]
