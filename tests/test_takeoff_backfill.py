"""Tests for Phase T5 quantity back-fill (:mod:`core.extraction.takeoff_backfill`).

Pure unit tests against the Pydantic schema models — no PDF I/O. The
T5 integration tests in :mod:`tests.test_takeoff_t5_integration` cover
the end-to-end PDF → priced takeoff path.
"""

from __future__ import annotations

import math

import pytest

from core.extraction.takeoff_backfill import (
    BACKFILL_NOTE_FALLBACK_PERIM,
    BACKFILL_NOTE_NO_HEIGHT,
    BACKFILL_NOTE_NO_OPENINGS,
    BACKFILL_NOTE_OK,
    BACKFILL_NOTE_SKIP_ROOM,
    DOOR_DEFAULT_OPENING_SF,
    WINDOW_DEFAULT_OPENING_SF,
    backfill_finish_quantities,
)
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_FINISH,
    synthesize_finish_takeoff_items,
)
from core.schemas import (
    DoorRecord,
    DoorScheduleResult,
    FinishRecord,
    FinishScheduleResult,
    RoomRecord,
    RoomScheduleResult,
    TakeoffItem,
    WindowRecord,
    WindowScheduleResult,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _finish_items_for(*records: FinishRecord) -> list[TakeoffItem]:
    """Run the T4 synthesiser; return the per-surface TakeoffItems."""
    sched = FinishScheduleResult(
        pages=[0] if records else [],
        rooms=list(records),
        confidence=0.9 if records else 0.0,
    )
    return synthesize_finish_takeoff_items(sched, sheet_id="A0.3")


def _room_schedule(*rooms: RoomRecord) -> RoomScheduleResult:
    return RoomScheduleResult(
        pages=[0] if rooms else [],
        rooms=list(rooms),
        confidence=0.9 if rooms else 0.0,
    )


def _surface_of(item: TakeoffItem) -> str | None:
    notes = item.notes or ""
    for part in notes.split(";"):
        part = part.strip()
        if part.startswith("surface="):
            return part[len("surface="):].strip()
    return None


# ---------------------------------------------------------------------------
# 1. Safety / empty inputs
# ---------------------------------------------------------------------------


def test_empty_items_returns_empty() -> None:
    assert backfill_finish_quantities([], _room_schedule()) == []


def test_no_room_schedule_returns_input_unchanged() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", room_name="Office",
        floor_finish="VCT-1", base_finish="RB-1",
        wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
    ))
    assert all(it.quantity == 0.0 for it in items)
    out = backfill_finish_quantities(items, None)
    assert out == items                                # unchanged
    out2 = backfill_finish_quantities(items, _room_schedule())
    assert out2 == items                               # empty schedule → unchanged


def test_non_finish_items_passthrough_untouched() -> None:
    """A door synth row, a room area row, a manual LLM line — all untouched."""
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    door = TakeoffItem(
        csi_division="08", csi_section="08 11 13",
        description="Door 101 — HM 3'-0\" x 7'-0\"",
        quantity=1.0, unit="EA", confidence=0.92,
        notes="source=door_schedule_prepass; mark=101",
    )
    llm = TakeoffItem(
        csi_division="03", csi_section="03 30 00",
        description="Slab on grade",
        quantity=500.0, unit="SF", confidence=0.7,
    )
    out = backfill_finish_quantities([door, llm], sched)
    assert out == [door, llm]


# ---------------------------------------------------------------------------
# 2. Floor / ceiling back-fill (area_sf)
# ---------------------------------------------------------------------------


def test_floor_backfilled_to_area_sf() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1",
    ))
    assert items[0].quantity == 0.0
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    assert len(out) == 1
    assert out[0].quantity == 180.0
    assert out[0].unit == "SF"
    assert out[0].confidence == pytest.approx(0.92, abs=1e-3)
    assert BACKFILL_NOTE_OK in (out[0].notes or "")


def test_ceiling_backfilled_to_area_sf() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", ceiling_finish="ACT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=240.0))
    out = backfill_finish_quantities(items, sched)
    assert len(out) == 1
    assert out[0].quantity == 240.0
    assert out[0].unit == "SF"


def test_floor_and_ceiling_share_same_area() -> None:
    """1 floor + 1 ceiling row both get the same area value."""
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1", ceiling_finish="ACT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    assert len(out) == 2
    assert all(it.quantity == 180.0 for it in out)


def test_area_missing_skips_floor_with_note() -> None:
    """Room exists but area_sf is None → preserve quantity=0.0, add note."""
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=None))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == 0.0
    assert "no area" in (out[0].notes or "")


# ---------------------------------------------------------------------------
# 3. Base back-fill (perimeter_lf, with fallback)
# ---------------------------------------------------------------------------


def test_base_backfilled_to_perimeter_lf() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", base_finish="RB-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", perimeter_lf=54.0))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == 54.0
    assert out[0].unit == "LF"          # unit was upgraded from SF to LF
    assert out[0].confidence == pytest.approx(0.92, abs=1e-3)
    assert BACKFILL_NOTE_OK in (out[0].notes or "")


def test_base_fallback_uses_4_sqrt_area() -> None:
    """No perimeter → fallback = ``4 * sqrt(area)`` with reduced confidence."""
    items = _finish_items_for(FinishRecord(
        room_number="101", base_finish="RB-1",
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=144.0,    # 12' x 12' room
    ))
    out = backfill_finish_quantities(items, sched)
    # 4 * sqrt(144) = 48 LF
    assert out[0].quantity == pytest.approx(48.0, abs=0.01)
    assert out[0].unit == "LF"
    assert out[0].confidence == pytest.approx(0.65, abs=1e-3)
    assert BACKFILL_NOTE_FALLBACK_PERIM in (out[0].notes or "")


def test_base_no_perimeter_no_area_skips() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", base_finish="RB-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101"))   # nothing populated
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == 0.0
    assert out[0].unit == "SF"                              # NOT upgraded
    assert "no perimeter or area" in (out[0].notes or "")


# ---------------------------------------------------------------------------
# 4. Wall back-fill (perimeter × height × share)
# ---------------------------------------------------------------------------


def test_wall_all_backfilled_full_perimeter_times_height() -> None:
    """Single WALL column → wall_ALL → full perimeter × height area."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    assert _surface_of(items[0]) == "wall_ALL"
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    assert out[0].unit == "SF"
    assert BACKFILL_NOTE_OK in (out[0].notes or "")
    assert BACKFILL_NOTE_NO_OPENINGS in (out[0].notes or "")


def test_wall_compass_backfilled_quarter_share() -> None:
    """Compass walls each get 1/4 of perimeter × height."""
    items = _finish_items_for(FinishRecord(
        room_number="101",
        wall_finishes={"N": "PT-1", "S": "PT-2", "E": "PT-3", "W": "PT-4"},
    ))
    assert len(items) == 4
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=80.0, ceiling_height_ft=10.0,
    ))
    out = backfill_finish_quantities(items, sched)
    expected = 80.0 * 10.0 / 4.0
    for it in out:
        assert it.quantity == pytest.approx(expected, abs=0.01)
        assert it.unit == "SF"


def test_wall_uses_finish_schedule_height_fallback() -> None:
    """Room schedule lacks ceiling height → fall back to finish schedule height."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
        ceiling_height_ft=12.0,                              # on finish record
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=None,
    ))
    finish_sched = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(
            room_number="101", wall_finishes={"ALL": "PT-1"},
            ceiling_height_ft=12.0,
        )],
        confidence=0.9,
    )
    out = backfill_finish_quantities(items, sched, finish_schedule=finish_sched)
    assert out[0].quantity == pytest.approx(54.0 * 12.0, abs=0.01)


def test_wall_no_ceiling_height_skips_with_note() -> None:
    """Neither schedule has ceiling height → preserve 0.0 + add note."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=None,
    ))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == 0.0
    assert BACKFILL_NOTE_NO_HEIGHT in (out[0].notes or "")


def test_wall_fallback_perimeter_reduces_confidence() -> None:
    """Wall back-fill with perimeter fallback drops confidence to 0.65."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=100.0, ceiling_height_ft=9.0,
        # 4 * sqrt(100) = 40 LF perimeter approximation
    ))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == pytest.approx(40.0 * 9.0, abs=0.01)
    assert out[0].confidence == pytest.approx(0.65, abs=1e-3)
    assert BACKFILL_NOTE_FALLBACK_PERIM in (out[0].notes or "")


# ---------------------------------------------------------------------------
# 5. Per-room expansion — multi-surface room
# ---------------------------------------------------------------------------


def test_full_room_backfilled_all_surfaces() -> None:
    """1 record (floor + base + wall_ALL + ceiling) → 4 items all back-filled."""
    items = _finish_items_for(FinishRecord(
        room_number="101", room_name="Office",
        floor_finish="VCT-1", base_finish="RB-1",
        wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
    ))
    assert len(items) == 4
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    out = backfill_finish_quantities(items, sched)
    qty_by_surface = {_surface_of(it): it.quantity for it in out}
    assert qty_by_surface["floor"] == 180.0
    assert qty_by_surface["base"] == 54.0
    assert qty_by_surface["wall_ALL"] == pytest.approx(54.0 * 9.0, abs=0.01)
    assert qty_by_surface["ceiling"] == 180.0


# ---------------------------------------------------------------------------
# 6. Room-not-in-schedule skip
# ---------------------------------------------------------------------------


def test_room_not_in_schedule_preserves_zero_with_skip_note() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="999", floor_finish="VCT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == 0.0
    assert BACKFILL_NOTE_SKIP_ROOM in (out[0].notes or "")


def test_mixed_rooms_some_found_some_missing() -> None:
    """Three rooms in finishes; only one in the room schedule → other two skipped."""
    items = (
        _finish_items_for(FinishRecord(room_number="101", floor_finish="VCT-1"))
        + _finish_items_for(FinishRecord(room_number="102", floor_finish="CPT-1"))
        + _finish_items_for(FinishRecord(room_number="103", floor_finish="TILE-1"))
    )
    sched = _room_schedule(RoomRecord(room_number="102", area_sf=240.0))
    out = backfill_finish_quantities(items, sched)
    by_desc = {it.description: it for it in out}

    found = [it for it in out if "Room 102" in it.description]
    assert found[0].quantity == 240.0

    missed = [it for it in out if "Room 101" in it.description]
    assert missed[0].quantity == 0.0
    assert BACKFILL_NOTE_SKIP_ROOM in (missed[0].notes or "")


# ---------------------------------------------------------------------------
# 7. Immutability — input rows are not mutated
# ---------------------------------------------------------------------------


def test_input_items_are_not_mutated() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1",
    ))
    original_qty = items[0].quantity
    original_notes = items[0].notes
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    # The originals are untouched.
    assert items[0].quantity == original_qty
    assert items[0].notes == original_notes
    # The output is a different instance.
    assert out[0] is not items[0]
    assert out[0].quantity == 180.0


def test_ordering_preserved() -> None:
    """Output order matches input order across multiple items."""
    items = _finish_items_for(
        FinishRecord(room_number="101", floor_finish="VCT-1"),
        FinishRecord(room_number="102", floor_finish="CPT-1"),
        FinishRecord(room_number="103", floor_finish="TILE-1"),
    )
    sched = _room_schedule(
        RoomRecord(room_number="101", area_sf=100.0),
        RoomRecord(room_number="102", area_sf=200.0),
        RoomRecord(room_number="103", area_sf=300.0),
    )
    out = backfill_finish_quantities(items, sched)
    assert [it.quantity for it in out] == [100.0, 200.0, 300.0]


# ---------------------------------------------------------------------------
# 8. Room# duplicates in the room schedule
# ---------------------------------------------------------------------------


def test_duplicate_room_records_most_populated_wins() -> None:
    """Two RoomRecords for the same number — the better-populated wins."""
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1", base_finish="RB-1",
        wall_finishes={"ALL": "PT-1"},
    ))
    sched = RoomScheduleResult(
        pages=[0, 1],
        rooms=[
            RoomRecord(room_number="101", area_sf=180.0),
            RoomRecord(
                room_number="101", area_sf=200.0, perimeter_lf=60.0,
                ceiling_height_ft=10.0,
            ),
        ],
        confidence=0.9,
    )
    out = backfill_finish_quantities(items, sched)
    by_surface = {_surface_of(it): it.quantity for it in out}
    # Better-populated record (area=200, perim=60, height=10) wins.
    assert by_surface["floor"] == 200.0
    assert by_surface["base"] == 60.0
    assert by_surface["wall_ALL"] == pytest.approx(60.0 * 10.0, abs=0.01)


# ---------------------------------------------------------------------------
# 9. CSI / description preserved through back-fill
# ---------------------------------------------------------------------------


def test_csi_division_section_and_description_preserved() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", room_name="Office", floor_finish="VCT-1",
    ))
    original_desc = items[0].description
    original_section = items[0].csi_section
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    assert out[0].description == original_desc
    assert out[0].csi_section == original_section
    assert out[0].csi_division == "09"


# ---------------------------------------------------------------------------
# 10. Door / window schedule params — orphan openings (no room_number)
# ---------------------------------------------------------------------------


def test_orphan_openings_without_room_number_are_not_deducted() -> None:
    """Doors / windows passed without ``room_number`` (orphans) cannot be
    attributed to any room — the wall row stays GROSS and carries no
    ``openings_deducted=`` audit note.
    """
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    door_sched = DoorScheduleResult(
        pages=[0],
        # No room_number → orphan; cannot be attributed.
        doors=[DoorRecord(mark="101", type="HM", width_in=36, height_in=84)],
        confidence=0.9,
    )
    window_sched = WindowScheduleResult(
        pages=[0],
        windows=[WindowRecord(mark="W1", type="ALUM", width_in=36, height_in=60)],
        confidence=0.9,
    )
    out = backfill_finish_quantities(
        items, sched, door_schedule=door_sched, window_schedule=window_sched,
    )
    # Wall area stays GROSS — orphan doors / windows can't be attributed.
    assert out[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    # No `openings_deducted=` audit note because nothing was deducted.
    assert "openings_deducted=" not in (out[0].notes or "")
    # And the legacy "no openings" hint is suppressed because we DID
    # have schedules — they just had no usable rows.
    assert BACKFILL_NOTE_NO_OPENINGS not in (out[0].notes or "")


# ---------------------------------------------------------------------------
# 11. Synth source-tag guard
# ---------------------------------------------------------------------------


def test_non_finish_synth_with_zero_quantity_untouched() -> None:
    """A row whose notes don't start with the finish source tag is untouched
    even if its description looks finish-shaped."""
    fake = TakeoffItem(
        csi_division="09", csi_section="09 65 19",
        description="Floor VCT-1 — Room 101 Office",
        quantity=0.0, unit="SF", confidence=0.7,
        notes="source=some_other_thing; room=101; surface=floor",
    )
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities([fake], sched)
    assert out[0] is fake
    assert out[0].quantity == 0.0


def test_finish_synth_without_room_in_notes_passthrough() -> None:
    """Synthesised row whose notes lack ``room=...`` passes through untouched
    (defensive — should never happen; T4 synth always emits room=)."""
    bogus = TakeoffItem(
        csi_division="09", csi_section="09 65 19",
        description="Floor VCT-1 — Room ???",
        quantity=0.0, unit="SF", confidence=0.7,
        notes=f"source={SYNTHESIS_SOURCE_TAG_FINISH}; surface=floor",
    )
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities([bogus], sched)
    assert out[0] is bogus
    assert out[0].quantity == 0.0


# ---------------------------------------------------------------------------
# 12. Notes get appended cleanly (preserving original synth metadata)
# ---------------------------------------------------------------------------


def test_notes_preserve_original_synthesis_metadata() -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", room_name="Office", floor_finish="VCT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    out = backfill_finish_quantities(items, sched)
    notes = out[0].notes or ""
    # Original synth tag still at the front.
    assert notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    # Original metadata preserved.
    assert "room=101" in notes
    assert "surface=floor" in notes
    assert "code=VCT-1" in notes
    # Backfill appended at the end.
    assert notes.endswith(BACKFILL_NOTE_OK)


# ---------------------------------------------------------------------------
# 13. Idempotence — re-running the back-fill is a no-op
# ---------------------------------------------------------------------------


def test_backfill_idempotent_with_same_schedule() -> None:
    """Running backfill twice with the same schedule gives the same quantities
    (note text doubles up; quantities and confidences don't)."""
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=180.0))
    once = backfill_finish_quantities(items, sched)
    twice = backfill_finish_quantities(once, sched)
    assert twice[0].quantity == once[0].quantity == 180.0
    assert twice[0].confidence == once[0].confidence


# ---------------------------------------------------------------------------
# 14. Sanity checks for the 4 * sqrt(area) helper
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "area, expected_perim",
    [
        (100.0, 40.0),       # 10x10
        (144.0, 48.0),       # 12x12
        (400.0, 80.0),       # 20x20
        (180.0, round(4 * math.sqrt(180.0), 2)),
    ],
)
def test_perimeter_fallback_square_room_assumption(area, expected_perim) -> None:
    items = _finish_items_for(FinishRecord(
        room_number="101", base_finish="RB-1",
    ))
    sched = _room_schedule(RoomRecord(room_number="101", area_sf=area))
    out = backfill_finish_quantities(items, sched)
    assert out[0].quantity == pytest.approx(expected_perim, abs=0.01)


# ---------------------------------------------------------------------------
# 15. Wall fan-out edge cases
# ---------------------------------------------------------------------------


def test_three_compass_walls_each_gets_quarter_share() -> None:
    """Three different compass walls (one direction missing) → each gets 1/4."""
    items = _finish_items_for(FinishRecord(
        room_number="101",
        wall_finishes={"N": "PT-1", "S": "PT-2", "E": "PT-3"},
    ))
    assert len(items) == 3
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=80.0, ceiling_height_ft=10.0,
    ))
    out = backfill_finish_quantities(items, sched)
    expected = 80.0 * 10.0 / 4.0
    for it in out:
        assert it.quantity == pytest.approx(expected, abs=0.01)


# ---------------------------------------------------------------------------
# 16. Phase T5.1 — door / window opening deduction
# ---------------------------------------------------------------------------


def _door_sched(*doors: DoorRecord) -> DoorScheduleResult:
    return DoorScheduleResult(
        pages=[0] if doors else [],
        doors=list(doors),
        confidence=0.9 if doors else 0.0,
    )


def _window_sched(*windows: WindowRecord) -> WindowScheduleResult:
    return WindowScheduleResult(
        pages=[0] if windows else [],
        windows=list(windows),
        confidence=0.9 if windows else 0.0,
    )


def test_single_door_in_room_reduces_wall_all_by_full_opening_sf() -> None:
    """A single 3'-0\" × 7'-0\" door (21 SF) in a room with a single
    ``WALL`` column → wall_ALL deduction = 21 SF × share(1.0) = 21 SF."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    raw = 54.0 * 9.0           # 486 SF
    door_sf = (36 * 84) / 144.0  # 21 SF
    assert out[0].quantity == pytest.approx(raw - door_sf, abs=0.01)
    notes = out[0].notes or ""
    assert "openings_deducted=1" in notes
    assert "opening_sf=21.0" in notes
    assert "wall_ALL_deduction=21.0" in notes


def test_single_door_in_compass_walls_distributes_quarter_share() -> None:
    """A 21 SF door with 4 compass walls → each wall deducts 21/4 = 5.25 SF."""
    items = _finish_items_for(FinishRecord(
        room_number="101",
        wall_finishes={"N": "PT-1", "S": "PT-2", "E": "PT-3", "W": "PT-4"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=80.0, ceiling_height_ft=10.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    raw_per_wall = 80.0 * 10.0 / 4.0     # 200 SF
    deduction_per_wall = 21.0 / 4.0      # 5.25 SF
    for it in out:
        assert it.quantity == pytest.approx(raw_per_wall - deduction_per_wall, abs=0.01)
        notes = it.notes or ""
        assert "openings_deducted=1" in notes
        # The per-wall deduction note references this surface specifically.
        surface = _surface_of(it)
        assert f"{surface}_deduction=5.25" in notes


def test_multiple_doors_same_room_accumulate_deduction() -> None:
    """Two doors in the same room → wall_ALL deduction = 21 + 21 = 42 SF."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
        DoorRecord(mark="101B", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    raw = 54.0 * 9.0
    assert out[0].quantity == pytest.approx(raw - 42.0, abs=0.01)
    assert "openings_deducted=2" in (out[0].notes or "")
    assert "opening_sf=42.0" in (out[0].notes or "")


def test_door_with_room_not_in_schedule_is_silently_skipped() -> None:
    """Door references room ``999`` but the room schedule only carries
    room ``101`` → door is skipped (logged at debug); wall ``101`` stays gross.
    """
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="999A", room_number="999", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    assert out[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    assert "openings_deducted=" not in (out[0].notes or "")


def test_door_without_dimensions_uses_default_opening_sf() -> None:
    """Door with ``room_number`` but missing dimensions → fall back to
    :data:`DOOR_DEFAULT_OPENING_SF` (21 SF).
    """
    assert DOOR_DEFAULT_OPENING_SF == 21.0
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101"),  # no width / height
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    assert out[0].quantity == pytest.approx(54.0 * 9.0 - DOOR_DEFAULT_OPENING_SF, abs=0.01)


def test_window_without_dimensions_uses_default_opening_sf() -> None:
    """Window with ``room_number`` but missing dimensions → fall back to
    :data:`WINDOW_DEFAULT_OPENING_SF` (12 SF, ~3'-0\" × 4'-0\")."""
    assert WINDOW_DEFAULT_OPENING_SF == 12.0
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    windows = _window_sched(
        WindowRecord(mark="W1", room_number="101"),  # no width / height
    )
    out = backfill_finish_quantities(items, sched, window_schedule=windows)
    assert out[0].quantity == pytest.approx(
        54.0 * 9.0 - WINDOW_DEFAULT_OPENING_SF, abs=0.01,
    )


def test_window_with_dimensions_overrides_default() -> None:
    """A 3'-0\" × 5'-0\" window (15 SF) deducts 15 SF, not the 12 SF default."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    windows = _window_sched(
        WindowRecord(mark="W1", room_number="101", width_in=36, height_in=60),
    )
    out = backfill_finish_quantities(items, sched, window_schedule=windows)
    expected_window_sf = (36 * 60) / 144.0    # 15 SF
    assert out[0].quantity == pytest.approx(54.0 * 9.0 - expected_window_sf, abs=0.01)
    assert "opening_sf=15.0" in (out[0].notes or "")


def test_opening_sf_exceeds_wall_sf_caps_at_raw_wall_sf() -> None:
    """A door bigger than the wall → quantity floors at 0; cap firing
    is surfaced in the audit note."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    # Tiny room: perimeter 8 LF × height 8 ft = 64 SF wall total.
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=8.0, ceiling_height_ft=8.0,
    ))
    # Absurd 100 SF "door".
    doors = _door_sched(
        DoorRecord(mark="HUGE", room_number="101", width_in=120, height_in=120),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    assert out[0].quantity == 0.0
    notes = out[0].notes or ""
    assert "openings_overflow" in notes
    assert "wall_ALL" in notes  # cap mentions the specific surface


def test_overflow_cap_on_one_compass_wall_only() -> None:
    """When deduction exceeds raw SF on a per-direction basis, only the
    affected wall caps — other walls remain partially-deducted."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"N": "PT-1", "S": "PT-2"},
    ))
    # 16 LF × 8 ft = 128 SF total; per compass wall (2-wall room) =
    # 128 / 4 = 32 SF. (Yes, the share is 0.25 even with only 2 walls
    # configured — the synthesiser collapsed to compass mode.)
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=16.0, ceiling_height_ft=8.0,
    ))
    doors = _door_sched(
        # 200 SF opening: per-wall share at 0.25 = 50 SF, exceeds 32 SF.
        DoorRecord(mark="HUGE", room_number="101", width_in=120, height_in=240),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    for it in out:
        assert it.quantity == 0.0
        assert "openings_overflow" in (it.notes or "")


def test_mixed_doors_some_with_room_some_orphan() -> None:
    """Mixed: one door with room=101 (deductible), one orphan (skipped),
    one referencing room=999 (skipped) → only the deductible one applies."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
        DoorRecord(mark="ORPHAN", width_in=36, height_in=84),
        DoorRecord(mark="MISMATCH", room_number="999", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    # Only the room=101 door (21 SF) gets deducted.
    assert out[0].quantity == pytest.approx(54.0 * 9.0 - 21.0, abs=0.01)
    assert "openings_deducted=1" in (out[0].notes or "")


def test_door_plus_window_combined_deduction() -> None:
    """Door (21 SF) + Window (15 SF) = 36 SF combined deduction on wall_ALL."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    windows = _window_sched(
        WindowRecord(mark="W1", room_number="101", width_in=36, height_in=60),
    )
    out = backfill_finish_quantities(
        items, sched, door_schedule=doors, window_schedule=windows,
    )
    assert out[0].quantity == pytest.approx(54.0 * 9.0 - (21.0 + 15.0), abs=0.01)
    assert "openings_deducted=2" in (out[0].notes or "")


def test_backfill_with_openings_idempotent() -> None:
    """Running the back-fill twice with the same schedules produces the
    same quantity and confidence — the function recomputes from the
    inputs and doesn't double-subtract."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    once = backfill_finish_quantities(items, sched, door_schedule=doors)
    twice = backfill_finish_quantities(once, sched, door_schedule=doors)
    assert twice[0].quantity == once[0].quantity
    assert twice[0].confidence == once[0].confidence


def test_non_finish_rows_untouched_by_opening_deduction() -> None:
    """T5.1 must not perturb door / structural / MEP rows even with opening data."""
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    door_takeoff = TakeoffItem(
        csi_division="08", csi_section="08 11 13",
        description="Door 101A — HM 3'-0\" x 7'-0\"",
        quantity=1.0, unit="EA", confidence=0.92,
        notes="source=door_schedule_prepass; mark=101A",
    )
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities([door_takeoff], sched, door_schedule=doors)
    assert out == [door_takeoff]


def test_opening_only_finish_no_walls_untouched_by_openings() -> None:
    """Floor / ceiling rows don't take an opening deduction even when
    doors exist for the room — openings only affect wall rows."""
    items = _finish_items_for(FinishRecord(
        room_number="101", floor_finish="VCT-1", ceiling_finish="ACT-1",
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    for it in out:
        # Floor / ceiling get area_sf unchanged.
        assert it.quantity == 180.0
        assert "openings_deducted" not in (it.notes or "")


def test_room_number_with_alphanumeric_suffix() -> None:
    """``room_number=\"101A\"`` is preserved as a string and matches a
    room schedule entry keyed by the same alphanumeric value."""
    items = _finish_items_for(FinishRecord(
        room_number="101A", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101A", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    doors = _door_sched(
        DoorRecord(mark="D1", room_number="101A", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    assert out[0].quantity == pytest.approx(54.0 * 9.0 - 21.0, abs=0.01)


def test_no_openings_note_only_when_both_schedules_missing() -> None:
    """The legacy ``BACKFILL_NOTE_NO_OPENINGS`` fires when neither door
    nor window schedule was passed — surfaces "we have no data" to
    the auditor distinct from "we have data but no matches"."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    out_none = backfill_finish_quantities(items, sched)
    assert BACKFILL_NOTE_NO_OPENINGS in (out_none[0].notes or "")

    # Now pass at least one schedule, even an empty one — the legacy
    # hint is suppressed.
    out_empty = backfill_finish_quantities(
        items, sched, door_schedule=_door_sched(),
    )
    assert BACKFILL_NOTE_NO_OPENINGS not in (out_empty[0].notes or "")


def test_window_for_unknown_room_silently_skipped() -> None:
    """Same as the door equivalent — window referencing a room not
    in the schedule is logged at debug and contributes nothing."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0,
    ))
    windows = _window_sched(
        WindowRecord(mark="W999", room_number="999", width_in=36, height_in=60),
    )
    out = backfill_finish_quantities(items, sched, window_schedule=windows)
    assert out[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    assert "openings_deducted=" not in (out[0].notes or "")


def test_opening_deduction_with_fallback_perimeter_keeps_low_confidence() -> None:
    """When the wall back-fill is already on the perimeter fallback
    (confidence drops to 0.65), opening deduction still applies on top
    and the confidence stays at the fallback band, not bumped back up."""
    items = _finish_items_for(FinishRecord(
        room_number="101", wall_finishes={"ALL": "PT-1"},
    ))
    sched = _room_schedule(RoomRecord(
        room_number="101", area_sf=100.0, ceiling_height_ft=9.0,
        # No perimeter_lf → triggers 4 * sqrt(100) = 40 LF fallback.
    ))
    doors = _door_sched(
        DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
    )
    out = backfill_finish_quantities(items, sched, door_schedule=doors)
    raw = 40.0 * 9.0
    assert out[0].quantity == pytest.approx(raw - 21.0, abs=0.01)
    assert out[0].confidence == pytest.approx(0.65, abs=1e-3)
    notes = out[0].notes or ""
    assert BACKFILL_NOTE_FALLBACK_PERIM in notes
    assert "openings_deducted=1" in notes
