"""Tests for Phase T4 finish-schedule → :class:`TakeoffItem` synthesis.

Pure unit tests against the Pydantic schema models (no PDF I/O), plus
one integration-smoke test that round-trips a synthesised result
through :func:`core.takeoff.reconcile`. Mirrors
:mod:`tests.test_window_takeoff_synthesis` but exercises the per-room
fan-out (1 record → 3-7 items) that's unique to the finish family.
"""

from __future__ import annotations

import pytest

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_FINISH,
    synthesize_finish_takeoff_items,
)
from core.schemas import (
    DrawingPrepassResult,
    FinishRecord,
    FinishScheduleResult,
    SheetExtraction,
    TakeoffItem,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_schedule(*rooms: FinishRecord) -> FinishScheduleResult:
    return FinishScheduleResult(
        pages=[0] if rooms else [],
        rooms=list(rooms),
        confidence=0.9 if rooms else 0.0,
        raw_table_text="ROOM | NAME | FLOOR | BASE | WALL | CEILING" if rooms else "",
    )


# ---------------------------------------------------------------------------
# 1. Happy path: 1 record → 4 items (floor + base + wall + ceiling)
# ---------------------------------------------------------------------------


def test_happy_path_single_room_full_surfaces() -> None:
    """One full record → 4 items (floor + base + wall ALL + ceiling)."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            room_name="Office",
            floor_finish="VCT-1",
            base_finish="RB-1",
            wall_finishes={"ALL": "PT-1"},
            ceiling_finish="ACT-1",
            ceiling_height_ft=9.0,
        ),
    )
    items = synthesize_finish_takeoff_items(schedule, sheet_id="A0.3")

    assert len(items) == 4
    assert all(isinstance(it, TakeoffItem) for it in items)
    assert all(it.confidence == pytest.approx(0.92) for it in items)
    assert all(it.quantity == 0.0 for it in items)
    assert all(it.unit == "SF" for it in items)
    assert all(it.source_sheet_ids == ["A0.3"] for it in items)
    assert all((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
               for it in items)
    # Each surface present + each code in some description.
    desc = " ".join(it.description for it in items)
    assert "Floor VCT-1" in desc
    assert "Base RB-1" in desc
    assert "Wall PT-1" in desc
    assert "Ceiling ACT-1" in desc
    assert "Room 101 Office" in desc


def test_happy_path_no_finishes_emits_zero_items() -> None:
    """A record with no floor/base/wall/ceiling → 0 items."""
    schedule = _make_schedule(
        FinishRecord(room_number="999", room_name="Stub")
    )
    items = synthesize_finish_takeoff_items(schedule, sheet_id="A0.3")
    assert items == []


def test_empty_schedule_returns_empty() -> None:
    items = synthesize_finish_takeoff_items(_make_schedule(), sheet_id="A0.3")
    assert items == []


def test_none_schedule_returns_empty() -> None:
    items = synthesize_finish_takeoff_items(None, sheet_id="A0.3")
    assert items == []


# ---------------------------------------------------------------------------
# 2. Per-room expansion — wall fan-out
# ---------------------------------------------------------------------------


def test_uniform_walls_collapse_to_one_item() -> None:
    """When all 4 compass walls share a code, emit ONE wall item."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            wall_finishes={"N": "PT-1", "S": "PT-1", "E": "PT-1", "W": "PT-1"},
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].description.startswith("Wall PT-1")
    assert "surface=wall_ALL" in (items[0].notes or "")


def test_mixed_walls_fan_out_to_per_direction_items() -> None:
    """N/S/E/W with different codes → 4 items, stable N→S→E→W order."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            wall_finishes={"N": "PT-1", "S": "PT-2", "E": "WC-1", "W": "PT-1"},
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 4
    descs = [it.description for it in items]
    assert descs[0].startswith("Wall N PT-1")
    assert descs[1].startswith("Wall S PT-2")
    assert descs[2].startswith("Wall E WC-1")
    assert descs[3].startswith("Wall W PT-1")
    # Each surface token reflects the direction.
    tokens = [next(p.split("=", 1)[1] for p in (it.notes or "").split("; ")
                   if p.startswith("surface=")) for it in items]
    assert tokens == ["wall_N", "wall_S", "wall_E", "wall_W"]


def test_partial_compass_walls() -> None:
    """Only N + S populated → 2 wall items, no W/E."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            wall_finishes={"N": "PT-1", "S": "WC-1"},
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 2
    descs = [it.description for it in items]
    assert any("Wall N PT-1" in d for d in descs)
    assert any("Wall S WC-1" in d for d in descs)


def test_all_key_overrides_compass_dict() -> None:
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            wall_finishes={"ALL": "PT-1", "N": "PT-2"},
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].description.startswith("Wall PT-1")


# ---------------------------------------------------------------------------
# 3. CSI mapping — FLOOR
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected_section",
    [
        # VCT / vinyl tile → 09 65 19
        ("VCT-1",   "09 65 19"),
        ("VCT",     "09 65 19"),
        ("VINYL-1", "09 65 19"),
        ("LVT-1",   "09 65 19"),
        ("LVP-2",   "09 65 19"),
        # Sheet vinyl → 09 65 16
        ("SHEET VINYL", "09 65 16"),
        ("SHT VINYL",   "09 65 16"),
        # Carpet → 09 68 13
        ("CPT-1",   "09 68 13"),
        ("CARPET",  "09 68 13"),
        # Ceramic tile → 09 30 13
        ("TILE-1",  "09 30 13"),
        ("CT-1",    "09 30 13"),
        ("CER-1",   "09 30 13"),
        ("PORC-1",  "09 30 13"),
        # Hardwood → 09 64 29
        ("HW-1",    "09 64 29"),
        ("WD-1",    "09 64 29"),
        ("WOOD",    "09 64 29"),
        # Polished concrete (cross-division 03) → 03 35 43
        ("POL CONC",  "03 35 43"),
        ("POL-CONC",  "03 35 43"),
        ("POLISHED",  "03 35 43"),
        ("SC",        "03 35 43"),
        ("SEAL CONC", "03 35 43"),
        # Unknown → 09 60 00
        ("MYSTERY",   "09 60 00"),
    ],
)
def test_csi_mapping_floor(code, expected_section) -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", floor_finish=code),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].csi_section == expected_section


# ---------------------------------------------------------------------------
# 4. CSI mapping — BASE
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected_section",
    [
        # Resilient base → 09 65 13
        ("RB-1",     "09 65 13"),
        ("RUBBER",   "09 65 13"),
        ("RES-1",    "09 65 13"),
        # Ceramic base → 09 30 13
        ("CB-1",     "09 30 13"),
        ("CER-1",    "09 30 13"),
        # Wood base → 09 64 33
        ("WB-1",     "09 64 33"),
        ("WOOD",     "09 64 33"),
        # Unknown → 09 60 00
        ("MYSTERY",  "09 60 00"),
    ],
)
def test_csi_mapping_base(code, expected_section) -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", base_finish=code),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].csi_section == expected_section


# ---------------------------------------------------------------------------
# 5. CSI mapping — WALL
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected_section, expected_division",
    [
        # Paint → 09 91 23
        ("PT-1",         "09 91 23", "09"),
        ("PAINT",        "09 91 23", "09"),
        # Wall covering → 09 72 00
        ("WC-1",         "09 72 00", "09"),
        ("VWC-1",        "09 72 00", "09"),
        ("WALLCOVERING", "09 72 00", "09"),
        # FRP (cross-division 06) → 06 64 00
        ("FRP-1",        "06 64 00", "06"),
        ("FRP",          "06 64 00", "06"),
        # Ceramic wall tile → 09 30 13
        ("TILE-1",       "09 30 13", "09"),
        ("CT-1",         "09 30 13", "09"),
        # Unknown → 09 70 00
        ("MYSTERY",      "09 70 00", "09"),
    ],
)
def test_csi_mapping_wall(code, expected_section, expected_division) -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", wall_finishes={"ALL": code}),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].csi_section == expected_section
    assert items[0].csi_division == expected_division


# ---------------------------------------------------------------------------
# 6. CSI mapping — CEILING
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "code, expected_section",
    [
        # ACT → 09 51 13
        ("ACT-1",    "09 51 13"),
        ("ACOUSTIC", "09 51 13"),
        ("ACP-1",    "09 51 13"),
        # Gypsum board → 09 29 00
        ("GYP",      "09 29 00"),
        ("GWB",      "09 29 00"),
        ("GYP BD",   "09 29 00"),
        # Wood ceiling → 09 64 29
        ("WD CEIL",  "09 64 29"),
        # Exposed / open → 09 00 00 marker
        ("EXPOSED",  "09 00 00"),
        ("OPEN",     "09 00 00"),
        # Unknown → 09 50 00
        ("MYSTERY",  "09 50 00"),
    ],
)
def test_csi_mapping_ceiling(code, expected_section) -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", ceiling_finish=code),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].csi_section == expected_section


# ---------------------------------------------------------------------------
# 7. Confidence rubric
# ---------------------------------------------------------------------------


def test_confidence_full_room_and_code_is_092() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", room_name="Office", floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert all(it.confidence == pytest.approx(0.92) for it in items)


def test_confidence_code_only_no_room_is_080() -> None:
    """Code present, room number + name both missing → 0.80."""
    schedule = _make_schedule(
        FinishRecord(room_number="", room_name="",
                       floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].confidence == pytest.approx(0.80)


# ---------------------------------------------------------------------------
# 8. Description shape
# ---------------------------------------------------------------------------


def test_description_includes_room_and_name() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", room_name="Lobby",
                       floor_finish="TILE-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert items[0].description == "Floor TILE-1 – Room 101 Lobby"


def test_description_room_number_only() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert items[0].description == "Floor VCT-1 – Room 101"


def test_description_unmarked_room() -> None:
    """Room with no number AND no name → ``Room (unmarked)``."""
    schedule = _make_schedule(
        FinishRecord(room_number="", room_name="",
                       floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert items[0].description == "Floor VCT-1 – Room (unmarked)"


# ---------------------------------------------------------------------------
# 9. Notes payload shape
# ---------------------------------------------------------------------------


def test_notes_format() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", room_name="Office",
                       floor_finish="VCT-1", ceiling_height_ft=9.5),
    )
    items = synthesize_finish_takeoff_items(schedule)
    notes = items[0].notes or ""
    assert notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    assert "room=101" in notes
    assert "room_name=Office" in notes
    assert "surface=floor" in notes
    assert "code=VCT-1" in notes


def test_notes_ceiling_height_only_on_ceiling_row() -> None:
    schedule = _make_schedule(
        FinishRecord(
            room_number="101",
            floor_finish="VCT-1",
            ceiling_finish="ACT-1",
            ceiling_height_ft=10.0,
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    floor = next(it for it in items if "Floor" in (it.description or ""))
    ceil = next(it for it in items if "Ceiling" in (it.description or ""))
    assert "ceiling_height_ft" not in (floor.notes or "")
    assert "ceiling_height_ft=10" in (ceil.notes or "")


# ---------------------------------------------------------------------------
# 10. Multi-room expansion
# ---------------------------------------------------------------------------


def test_two_rooms_expansion() -> None:
    """2 rooms × (floor + base + 1 wall + ceiling) = 8 items."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101", room_name="Office",
            floor_finish="VCT-1", base_finish="RB-1",
            wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
        ),
        FinishRecord(
            room_number="102", room_name="Lobby",
            floor_finish="TILE-1", base_finish="CB-1",
            wall_finishes={"ALL": "WC-1"}, ceiling_finish="ACT-1",
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 8
    rooms_in_items = {p.split("=", 1)[1] for it in items
                      for p in (it.notes or "").split("; ")
                      if p.startswith("room=")}
    assert rooms_in_items == {"101", "102"}


def test_mixed_walls_room_expansion_count() -> None:
    """1 room with 4 distinct compass walls → 1 floor + 1 base + 4 walls + 1 ceiling = 7."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="101", room_name="Office",
            floor_finish="VCT-1", base_finish="RB-1",
            wall_finishes={"N": "PT-1", "S": "PT-2", "E": "WC-1", "W": "PT-1"},
            ceiling_finish="ACT-1",
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert len(items) == 7


# ---------------------------------------------------------------------------
# 11. Edge case: exposed ceiling marker
# ---------------------------------------------------------------------------


def test_exposed_ceiling_emits_marker_row() -> None:
    """``EXPOSED`` ceiling routes to the 09 00 00 marker section."""
    schedule = _make_schedule(
        FinishRecord(
            room_number="103", room_name="Mech",
            floor_finish="SC", ceiling_finish="EXPOSED",
        ),
    )
    items = synthesize_finish_takeoff_items(schedule)
    ceiling = next(it for it in items if "Ceiling" in it.description)
    assert ceiling.csi_section == "09 00 00"
    assert "EXPOSED" in ceiling.description


# ---------------------------------------------------------------------------
# 12. Source-tag constant export
# ---------------------------------------------------------------------------


def test_source_tag_constant() -> None:
    assert SYNTHESIS_SOURCE_TAG_FINISH == "finish_schedule_prepass"


# ---------------------------------------------------------------------------
# 13. Sheet-ID propagation
# ---------------------------------------------------------------------------


def test_sheet_id_threaded_into_source_sheet_ids() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule, sheet_id="A0.3")
    assert all(it.source_sheet_ids == ["A0.3"] for it in items)


def test_no_sheet_id_yields_empty_source_sheet_ids() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", floor_finish="VCT-1"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert all(it.source_sheet_ids == [] for it in items)


# ---------------------------------------------------------------------------
# 14. Integration round-trip through reconcile()
# ---------------------------------------------------------------------------


def test_integration_synthesised_rows_survive_reconcile() -> None:
    schedule = FinishScheduleResult(
        pages=[0],
        rooms=[
            FinishRecord(
                room_number="101", room_name="Office",
                floor_finish="VCT-1", base_finish="RB-1",
                wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
            ),
        ],
        confidence=0.9,
    )
    extraction = SheetExtraction(
        sheet_id="A0.3",
        prepass=DrawingPrepassResult(finish_schedule=schedule),
    )
    project = reconcile([extraction])
    synth = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    # 4 items: floor + base + wall ALL + ceiling.
    assert len(synth) == 4


# ---------------------------------------------------------------------------
# 15. Cross-division mappings sanity check
# ---------------------------------------------------------------------------


def test_polished_concrete_lands_on_division_03() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", floor_finish="POL CONC"),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert items[0].csi_division == "03"
    assert items[0].csi_section == "03 35 43"


def test_frp_wall_lands_on_division_06() -> None:
    schedule = _make_schedule(
        FinishRecord(room_number="101", wall_finishes={"ALL": "FRP-1"}),
    )
    items = synthesize_finish_takeoff_items(schedule)
    assert items[0].csi_division == "06"
    assert items[0].csi_section == "06 64 00"
