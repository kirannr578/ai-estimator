"""Tests for HVAC TakeoffItem synthesis (Phase T2.8).

Validates the per-record fan-out shape:
* 1 EA equipment row + 1 LS rough-in row + (optional) 1 EA disconnect
* CSI mapping per equipment family
* Confidence calibration (QTY-present=0.90, absent=0.55, rough-in=0.45,
  disconnect=0.70)
"""

from __future__ import annotations

import pytest

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_HVAC,
    synthesize_hvac_takeoff_items,
)
from core.schemas import HVACEquipmentRecord, HVACScheduleResult


def _make_record(**overrides) -> HVACEquipmentRecord:
    """Helper: build an HVACEquipmentRecord with sensible defaults."""
    defaults = dict(
        equipment_tag="AHU-1",
        equipment_type="AHU",
        description="Indoor air handler",
        manufacturer="Trane",
        model_number="M-Series",
        capacity_value=2000.0,
        capacity_unit="CFM",
        motor_hp=5.0,
        voltage="480V/3PH",
        phase_count=3,
        quantity=None,
    )
    defaults.update(overrides)
    return HVACEquipmentRecord(**defaults)


# ---------------------------------------------------------------------------
# Per-record fan-out shape
# ---------------------------------------------------------------------------


def test_ahu_with_qty_emits_three_items() -> None:
    """AHU with QTY column → 3 items (equipment + rough-in + disconnect)."""
    rec = _make_record(equipment_tag="AHU-1", equipment_type="AHU",
                         quantity=2)
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 3
    # Equipment row
    eq = items[0]
    assert eq.csi_section == "23 73 13"
    assert eq.unit == "EA"
    assert eq.quantity == 2.0
    assert eq.confidence == 0.90
    # Rough-in row
    ri = items[1]
    assert ri.csi_section == "23 05 00"
    assert ri.unit == "LS"
    assert ri.confidence == 0.45
    # Disconnect row — Phase T6.1: inherits QTY-published equipment
    # confidence (0.90) with 5% derivation haircut → 0.855.
    dc = items[2]
    assert dc.csi_section == "26 28 16"
    assert dc.unit == "EA"
    assert dc.confidence == pytest.approx(0.855)


def test_rtu_without_qty_emits_three_items_low_conf() -> None:
    """RTU without QTY → equipment row at 0.55 confidence (HAND_TAKEOFF)."""
    rec = _make_record(equipment_tag="RTU-A", equipment_type="RTU",
                         quantity=None)
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 3
    eq = items[0]
    assert eq.csi_section == "23 74 13"
    assert eq.quantity == 1.0
    assert eq.confidence == 0.55  # HAND_TAKEOFF default


def test_vav_emits_two_items_no_disconnect() -> None:
    """VAV → 2 items (equipment + rough-in); no disconnect (duct-fed)."""
    rec = _make_record(
        equipment_tag="VAV-3-1", equipment_type="VAV",
        capacity_value=400.0, capacity_unit="CFM",
        motor_hp=None, voltage=None, quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 2
    assert items[0].csi_section == "23 36 00"
    assert items[1].csi_section == "23 05 00"
    # Verify no disconnect row landed
    assert all(i.csi_section != "26 28 16" for i in items)


def test_boiler_emits_two_items_no_disconnect() -> None:
    """BOILER → 2 items (equipment + rough-in); no disconnect (integrated)."""
    rec = _make_record(
        equipment_tag="B-1", equipment_type="BOILER",
        description="Gas boiler", capacity_value=500.0, capacity_unit="MBH",
        motor_hp=None, voltage="120V/1PH",
        fuel_type="GAS", quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 2
    assert items[0].csi_section == "23 52 00"
    assert items[1].csi_section == "23 05 00"
    assert all(i.csi_section != "26 28 16" for i in items)


def test_pump_with_hp_and_voltage_emits_three_items() -> None:
    """PUMP with motor HP + voltage → 3 items (equipment + rough-in + disconnect)."""
    rec = _make_record(
        equipment_tag="P-1", equipment_type="PUMP",
        description="Hot water circulating pump",
        capacity_value=100.0, capacity_unit="GPM",
        motor_hp=3.0, voltage="208V/3PH", quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 3
    assert items[0].csi_section == "23 22 23"
    assert items[1].csi_section == "23 05 00"
    assert items[2].csi_section == "26 28 16"


def test_chiller_emits_three_items() -> None:
    """CHILLER → 3 items (equipment + rough-in + disconnect)."""
    rec = _make_record(
        equipment_tag="CH-1", equipment_type="CHILLER",
        description="Water-cooled chiller", capacity_value=100.0,
        capacity_unit="TONS", motor_hp=75.0, voltage="480V/3PH",
        refrigerant="R-410A", quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 3
    assert items[0].csi_section == "23 64 23"
    assert items[1].csi_section == "23 05 00"
    assert items[2].csi_section == "26 28 16"


def test_fan_emits_three_items() -> None:
    """FAN → 3 items (equipment + rough-in + disconnect)."""
    rec = _make_record(
        equipment_tag="F-1", equipment_type="FAN",
        description="Exhaust fan", capacity_value=1500.0, capacity_unit="CFM",
        motor_hp=2.0, voltage="208V/3PH", quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert len(items) == 3
    assert items[0].csi_section == "23 34 00"
    assert items[2].csi_section == "26 28 16"


# ---------------------------------------------------------------------------
# CSI mapping per equipment family
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("etype,expected_section", [
    ("AHU",     "23 73 13"),
    ("RTU",     "23 74 13"),
    ("VAV",     "23 36 00"),
    ("PUMP",    "23 22 23"),
    ("BOILER",  "23 52 00"),
    ("CHILLER", "23 64 23"),
    ("FAN",     "23 34 00"),
    ("OTHER",   "23 00 00"),
])
def test_csi_mapping_per_equipment_type(
    etype: str, expected_section: str,
) -> None:
    rec = _make_record(
        equipment_tag=f"X-{etype}", equipment_type=etype,
        motor_hp=None, voltage=None, quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert items[0].csi_section == expected_section


# ---------------------------------------------------------------------------
# Confidence calibration
# ---------------------------------------------------------------------------


def test_confidence_qty_present_lands_at_090() -> None:
    rec = _make_record(equipment_tag="F-1", equipment_type="FAN",
                         motor_hp=None, voltage=None, quantity=4)
    items = synthesize_hvac_takeoff_items([rec])
    assert items[0].confidence == 0.90


def test_confidence_qty_absent_lands_at_055() -> None:
    rec = _make_record(equipment_tag="F-1", equipment_type="FAN",
                         motor_hp=None, voltage=None, quantity=None)
    items = synthesize_hvac_takeoff_items([rec])
    assert items[0].confidence == 0.55


def test_roughin_confidence_lands_at_045() -> None:
    """MEP rough-in row always lands at 0.45 (PARAMETRIC tier)."""
    rec = _make_record()
    items = synthesize_hvac_takeoff_items([rec])
    roughin = [i for i in items if i.csi_section == "23 05 00"][0]
    assert roughin.confidence == 0.45


def test_disconnect_confidence_inherits_equipment_haircut() -> None:
    """Disconnect EA row inherits the equipment row's confidence with the
    Phase T6.1 5% derivation haircut.

    The default ``_make_record`` fixture omits ``quantity`` so the
    parent equipment row lands at 0.55 (HAND_TAKEOFF default). The
    disconnect therefore lands at max(0.45, 0.55 × 0.95) = 0.5225 →
    HAND_TAKEOFF (correctly: a hand-takeoff parent should NOT
    AUTO_APPROVE its derived disconnect).

    Pre-T6.1 the disconnect was a hard-coded 0.70 regardless of
    parent confidence — see ``inherit_with_haircut`` rationale in
    ``core.extraction.takeoff_synthesis``.
    """
    rec = _make_record()  # AHU with HP+voltage → disconnect emitted
    items = synthesize_hvac_takeoff_items([rec])
    disc = [i for i in items if i.csi_section == "26 28 16"][0]
    assert disc.confidence == pytest.approx(0.5225)


# ---------------------------------------------------------------------------
# Notes-tag + source attribution
# ---------------------------------------------------------------------------


def test_notes_tagged_with_source_prefix() -> None:
    """Every synthesised row starts with ``source=hvac_schedule_prepass``."""
    rec = _make_record()
    items = synthesize_hvac_takeoff_items([rec])
    for item in items:
        assert item.notes is not None
        assert item.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_HVAC}")


def test_notes_carry_role_token() -> None:
    """Each row carries a distinct role= token for dedupe disambiguation."""
    rec = _make_record()
    items = synthesize_hvac_takeoff_items([rec])
    roles = {item.notes.split("role=")[1].split(";")[0].strip() for item in items}
    assert roles == {"equipment", "roughin", "disconnect"}


def test_sheet_id_propagates_to_source_sheet_ids() -> None:
    rec = _make_record()
    items = synthesize_hvac_takeoff_items([rec], sheet_id="M-2.0")
    for item in items:
        assert item.source_sheet_ids == ["M-2.0"]


def test_accepts_schedule_result_wrapper() -> None:
    """The synthesiser accepts an ``HVACScheduleResult`` directly."""
    result = HVACScheduleResult(
        pages=[3], equipment=[_make_record(equipment_tag="AHU-1")],
    )
    items = synthesize_hvac_takeoff_items(result)
    assert len(items) == 3
    assert items[0].csi_section == "23 73 13"


def test_empty_input_returns_empty_list() -> None:
    assert synthesize_hvac_takeoff_items(None) == []
    assert synthesize_hvac_takeoff_items([]) == []
    assert synthesize_hvac_takeoff_items(HVACScheduleResult()) == []


def test_record_without_tag_is_skipped() -> None:
    """Defensive: an empty-tag record is silently dropped."""
    rec = HVACEquipmentRecord(equipment_tag="", equipment_type="AHU")
    items = synthesize_hvac_takeoff_items([rec])
    assert items == []


def test_pump_without_voltage_or_hp_skips_disconnect() -> None:
    """A PUMP with no motor and no voltage → no disconnect row."""
    rec = _make_record(
        equipment_tag="P-2", equipment_type="PUMP",
        motor_hp=None, voltage=None, quantity=None,
    )
    items = synthesize_hvac_takeoff_items([rec])
    assert all(i.csi_section != "26 28 16" for i in items)
    assert len(items) == 2
