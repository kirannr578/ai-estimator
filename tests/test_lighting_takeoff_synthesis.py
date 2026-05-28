"""Tests for Phase T2.7 lighting-fixture-schedule → :class:`TakeoffItem` synthesis.

Pure unit tests against the Pydantic schema models (no PDF I/O); the
extraction layer is exercised separately in
:mod:`tests.test_lighting_schedule_extraction`. Mirrors the shape of
:mod:`tests.test_panel_takeoff_synthesis`.
"""

from __future__ import annotations

import pytest

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_LIGHTING,
    _LIGHTING_HAND_TAKEOFF_CONFIDENCE,
    _LIGHTING_QTY_CONFIDENCE,
    synthesize_lighting_takeoff_items,
)
from core.schemas import (
    LightingFixtureRecord,
    LightingScheduleResult,
    TakeoffItem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fixture(
    *,
    fixture_tag: str = "A1",
    description: str = "2x4 LED RECESSED TROFFER 4000K",
    manufacturer: str | None = "Lithonia",
    catalog_number: str | None = "2BLT4-40L-LP840",
    wattage: float | None = 40.0,
    lumens: int | None = 4400,
    color_temp_k: int | None = 4000,
    voltage: str | None = "277V",
    lamp_type: str | None = "LED",
    mounting: str | None = "RECESSED",
    dimmable: bool | None = True,
    emergency: bool | None = None,
    quantity: int | None = None,
    notes: str | None = None,
    confidence: float = 0.85,
    source_sheet: str | None = "E2.0",
) -> LightingFixtureRecord:
    return LightingFixtureRecord(
        fixture_tag=fixture_tag,
        description=description,
        manufacturer=manufacturer,
        catalog_number=catalog_number,
        wattage=wattage,
        lumens=lumens,
        color_temp_k=color_temp_k,
        voltage=voltage,
        lamp_type=lamp_type,
        mounting=mounting,
        dimmable=dimmable,
        emergency=emergency,
        quantity=quantity,
        notes=notes,
        confidence=confidence,
        source_sheet=source_sheet,
    )


def _by_section(items: list[TakeoffItem]) -> dict[str, list[TakeoffItem]]:
    out: dict[str, list[TakeoffItem]] = {}
    for it in items:
        out.setdefault(it.csi_section or "", []).append(it)
    return out


# ---------------------------------------------------------------------------
# Empty + degenerate input
# ---------------------------------------------------------------------------


def test_synthesize_returns_empty_for_empty_input() -> None:
    assert synthesize_lighting_takeoff_items([]) == []
    assert synthesize_lighting_takeoff_items(None) == []


def test_synthesize_accepts_lighting_schedule_result() -> None:
    """Accept the schema container OR a list — same shape used by panel."""
    schedule = LightingScheduleResult(fixtures=[_fixture()])
    items = synthesize_lighting_takeoff_items(schedule)
    assert len(items) == 1


def test_synthesize_skips_fixtures_with_blank_tag() -> None:
    fixture = _fixture(fixture_tag="   ")
    assert synthesize_lighting_takeoff_items([fixture]) == []


# ---------------------------------------------------------------------------
# Basic shape: 1 EA per fixture; no lamp line for LED
# ---------------------------------------------------------------------------


def test_synthesize_single_led_fixture_produces_one_row() -> None:
    """An LED fixture: exactly one row (no lamp/driver line)."""
    items = synthesize_lighting_takeoff_items([_fixture(lamp_type="LED")])
    assert len(items) == 1
    item = items[0]
    assert item.csi_division == "26"
    assert item.csi_section == "26 51 13"
    assert item.unit == "EA"


def test_synthesize_five_led_fixtures_all_qty_present() -> None:
    """5 fixtures with QTY column → 5 EA rows, every confidence 0.90."""
    fixtures = [
        _fixture(fixture_tag=f"F{n}", quantity=n * 4)
        for n in range(1, 6)
    ]
    items = synthesize_lighting_takeoff_items(fixtures)
    assert len(items) == 5  # no lamp lines for LED
    assert all(it.unit == "EA" for it in items)
    assert all(
        it.confidence == _LIGHTING_QTY_CONFIDENCE for it in items
    )
    # Quantities pass-through verbatim.
    quantities = sorted(int(it.quantity) for it in items)
    assert quantities == [4, 8, 12, 16, 20]


def test_synthesize_five_led_fixtures_no_qty_hand_takeoff() -> None:
    """5 fixtures without QTY → 5 EA rows, quantity=1.0, confidence=0.55."""
    fixtures = [
        _fixture(fixture_tag=f"F{n}", quantity=None) for n in range(1, 6)
    ]
    items = synthesize_lighting_takeoff_items(fixtures)
    assert len(items) == 5
    assert all(it.quantity == 1.0 for it in items)
    assert all(
        it.confidence == _LIGHTING_HAND_TAKEOFF_CONFIDENCE for it in items
    )


# ---------------------------------------------------------------------------
# Lamp/driver fan-out for non-LED technologies
# ---------------------------------------------------------------------------


def test_synthesize_fluorescent_fixture_emits_lamp_line() -> None:
    """Fluorescent fixture → fixture EA + lamp LS (1 + 1 = 2 rows)."""
    fixture = _fixture(
        lamp_type="FLUORESCENT",
        description="2x4 T8 FLUORESCENT TROFFER",
    )
    items = synthesize_lighting_takeoff_items([fixture])
    assert len(items) == 2
    sections = sorted(it.csi_section for it in items)
    assert sections == ["26 51 13", "26 55 53"]
    by_unit = {it.unit for it in items}
    assert by_unit == {"EA", "LS"}


def test_synthesize_hid_fixture_emits_lamp_line() -> None:
    """HID (metal-halide) site fixture → fixture EA + lamp LS."""
    fixture = _fixture(
        lamp_type="HID",
        description="POLE LIGHT METAL HALIDE 400W",
        mounting=None,
    )
    items = synthesize_lighting_takeoff_items([fixture])
    assert len(items) == 2
    assert any(it.csi_section == "26 55 53" for it in items)


def test_synthesize_incan_fixture_emits_lamp_line() -> None:
    """Incandescent (legacy) fixture → fixture EA + lamp LS."""
    fixture = _fixture(
        lamp_type="INCAN",
        description="WALL SCONCE INCANDESCENT 60W",
        mounting="WALL",
    )
    items = synthesize_lighting_takeoff_items([fixture])
    assert len(items) == 2


def test_synthesize_led_fixture_does_not_emit_lamp_line() -> None:
    """LED integrated → NO lamp/driver LS row."""
    items = synthesize_lighting_takeoff_items([_fixture(lamp_type="LED")])
    sections = {it.csi_section for it in items}
    assert "26 55 53" not in sections


# ---------------------------------------------------------------------------
# CSI mapping by mounting
# ---------------------------------------------------------------------------


def test_synthesize_wall_mounted_routes_to_26_51_19() -> None:
    """WALL mounting → ``26 51 19``."""
    fixture = _fixture(mounting="WALL", description="WALL SCONCE LED 15W")
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 51 19"


def test_synthesize_recessed_routes_to_26_51_13() -> None:
    fixture = _fixture(mounting="RECESSED")
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 51 13"


def test_synthesize_pendant_routes_to_26_51_13() -> None:
    fixture = _fixture(mounting="PENDANT", description="LED pendant 30W")
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 51 13"


def test_synthesize_surface_routes_to_26_51_13() -> None:
    fixture = _fixture(mounting="SURFACE", description="LED surface strip 25W")
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 51 13"


def test_synthesize_no_mounting_defaults_to_interior() -> None:
    """When mounting is unknown the row routes to the interior section."""
    fixture = _fixture(mounting=None, description="LED FIXTURE 40W")
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 51 13"


def test_synthesize_exterior_keyword_routes_to_26_56_00() -> None:
    """An EXTERIOR / WALL PACK hint in the description routes to site lighting."""
    fixture = _fixture(
        mounting=None,
        description="LED WALL PACK EXTERIOR 50W",
        lamp_type="LED",
    )
    items = synthesize_lighting_takeoff_items([fixture])
    assert items[0].csi_section == "26 56 00"


# ---------------------------------------------------------------------------
# Mixed batches + source tag + sheet propagation
# ---------------------------------------------------------------------------


def test_synthesize_mixed_batch_correct_lamp_line_count() -> None:
    """LED + LED + FLUORESCENT + HID = 4 fixtures + 2 lamp lines = 6 rows."""
    fixtures = [
        _fixture(fixture_tag="A", lamp_type="LED"),
        _fixture(fixture_tag="B", lamp_type="LED", mounting="WALL"),
        _fixture(fixture_tag="C", lamp_type="FLUORESCENT",
                 description="T8 fluorescent troffer"),
        _fixture(fixture_tag="D", lamp_type="HID",
                 description="Metal halide high-bay"),
    ]
    items = synthesize_lighting_takeoff_items(fixtures)
    assert len(items) == 6
    by_section = _by_section(items)
    # 1 wall sconce (B) + 3 interior (A/C/D) + 2 lamps (C/D)
    assert len(by_section.get("26 51 19", [])) == 1
    assert len(by_section.get("26 51 13", [])) == 3
    assert len(by_section.get("26 55 53", [])) == 2


def test_synthesize_source_tag_in_notes() -> None:
    """Every row carries ``source=lighting_schedule_prepass`` in notes."""
    items = synthesize_lighting_takeoff_items([_fixture()])
    for it in items:
        assert it.notes is not None
        assert it.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_LIGHTING}")


def test_synthesize_notes_carry_role_token() -> None:
    """Fixture row → role=fixture; lamp row → role=lamp."""
    items = synthesize_lighting_takeoff_items([
        _fixture(lamp_type="FLUORESCENT",
                 description="T8 fluorescent troffer"),
    ])
    notes_by_section = {it.csi_section: it.notes for it in items}
    assert "role=fixture" in notes_by_section["26 51 13"]
    assert "role=lamp" in notes_by_section["26 55 53"]


def test_synthesize_sheet_id_override_takes_precedence() -> None:
    """When ``sheet_id=`` is passed to the synthesiser it overrides the per-record sheet."""
    items = synthesize_lighting_takeoff_items(
        [_fixture(source_sheet="E1.0")],
        sheet_id="E2.0",
    )
    assert items[0].source_sheet_ids == ["E2.0"]


def test_synthesize_sheet_id_falls_back_to_record() -> None:
    """When no ``sheet_id`` is passed, the record's sheet is used."""
    items = synthesize_lighting_takeoff_items([
        _fixture(source_sheet="E2.0"),
    ])
    assert items[0].source_sheet_ids == ["E2.0"]


def test_synthesize_description_includes_tag_and_mfr() -> None:
    """Description format ``"Fixture <TAG> — <body> (<mfr> <catalog>) ..."``."""
    items = synthesize_lighting_takeoff_items([
        _fixture(fixture_tag="A1", manufacturer="Lithonia",
                 catalog_number="2BLT4-40L"),
    ])
    desc = items[0].description
    assert "Fixture A1" in desc
    assert "Lithonia" in desc
    assert "2BLT4-40L" in desc


def test_synthesize_qty_column_zero_treated_as_missing() -> None:
    """``quantity=0`` is treated like ``None`` — defaults to 1 + HAND_TAKEOFF."""
    items = synthesize_lighting_takeoff_items([_fixture(quantity=0)])
    assert items[0].quantity == 1.0
    assert items[0].confidence == _LIGHTING_HAND_TAKEOFF_CONFIDENCE


def test_synthesize_lamp_inherits_fixture_ea_row_confidence_with_haircut() -> None:
    """The lamp/driver LS line inherits the fixture EA row's confidence
    (the QTY-aware value) with the Phase T6.1 5% haircut.

    Pre-T6.1 the lamp used the fixture record's raw ``confidence``
    field; T6.1 propagates the EA row's effective confidence
    (0.55 hand-takeoff or 0.90 QTY-published) one derivation step
    down.

    With ``quantity=None`` (default), the EA row sits at the
    HAND_TAKEOFF 0.55 floor → lamp at max(0.45, 0.55 × 0.95) = 0.5225.
    """
    fixture = _fixture(
        lamp_type="FLUORESCENT",
        description="T8 fluorescent troffer",
        confidence=0.78,  # ignored by synthesis (no QTY column)
    )
    items = synthesize_lighting_takeoff_items([fixture])
    lamp_items = [it for it in items if it.csi_section == "26 55 53"]
    assert len(lamp_items) == 1
    assert lamp_items[0].confidence == pytest.approx(0.5225)
