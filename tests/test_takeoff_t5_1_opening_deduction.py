"""Phase T5.1 end-to-end integration tests — door / window opening
deduction in the wall SF back-fill.

These tests exercise the FULL path: synthetic PDFs (room schedule +
finish schedule + door schedule + window schedule) → drawing prepass →
SheetExtraction → reconcile() → priced-ready ProjectModel.takeoffs
with wall SF reduced by the right per-room opening total. They prove
that:

* ``DoorRecord.room_number`` and ``WindowRecord.room_number`` are
  populated by the schedule extractors when the source table carries
  a ``ROOM`` / ``RM`` / ``LOCATION`` column.
* ``backfill_finish_quantities`` consumes those room numbers and
  subtracts opening SF from the matching room's wall rows.
* The Pydantic schema round-trip preserves ``room_number`` through
  :mod:`core.extraction.drawing_prepass.to_schema`.

Pure unit tests for the deduction math live in
:mod:`tests.test_takeoff_backfill`; door / window ROOM-column parsing
unit tests live in :mod:`tests.test_door_schedule_extraction` and
:mod:`tests.test_window_schedule_extraction`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    to_schema as prepass_to_schema,
)
from core.extraction.takeoff_backfill import (
    DOOR_DEFAULT_OPENING_SF,
    WINDOW_DEFAULT_OPENING_SF,
    backfill_finish_quantities,
)
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_FINISH
from core.schemas import (
    DoorRecord,
    DoorScheduleResult,
    FinishRecord,
    FinishScheduleResult,
    RoomRecord,
    RoomScheduleResult,
    SheetExtraction,
    WindowRecord,
    WindowScheduleResult,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders — mirror tests/test_takeoff_t5_integration.py
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 200.0),
    cell_size: tuple[float, float] = (75.0, 24.0),
) -> None:
    page = doc.new_page(width=900, height=612)
    if title_lines:
        y = 60.0
        for line in title_lines:
            page.insert_text((40, y), line, fontsize=12)
            y += 16
    if table:
        n_rows = len(table)
        n_cols = max(len(r) for r in table)
        x0, y0 = table_origin
        cell_w, cell_h = cell_size
        x1 = x0 + cell_w * n_cols
        y1 = y0 + cell_h * n_rows
        for i in range(n_rows + 1):
            page.draw_line((x0, y0 + i * cell_h), (x1, y0 + i * cell_h))
        for j in range(n_cols + 1):
            page.draw_line((x0 + j * cell_w, y0), (x0 + j * cell_w, y1))
        for i, row in enumerate(table):
            for j, val in enumerate(row):
                page.insert_text(
                    (x0 + j * cell_w + 4, y0 + i * cell_h + 16),
                    str(val), fontsize=9,
                )


def _build_pdf(tmp_path: Path, name: str, **kw) -> Path:
    doc = fitz.open()
    _add_page(doc, **kw)
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


def _sheet_from_prepass(pdf_path: Path, page_index: int,
                         sheet_id: str) -> SheetExtraction:
    """Run the deterministic prepass on one page; wrap in a SheetExtraction."""
    result = prepass_drawing_page(pdf_path, page_index)
    return SheetExtraction(
        sheet_id=sheet_id,
        prepass=prepass_to_schema(result),
    )


def _surface_of(item) -> str | None:
    notes = item.notes or ""
    for part in notes.split(";"):
        part = part.strip()
        if part.startswith("surface="):
            return part[len("surface="):].strip()
    return None


# ---------------------------------------------------------------------------
# 1. Pure-Pydantic integration — direct backfill call
# ---------------------------------------------------------------------------


def test_inmem_two_rooms_with_doors_reduces_wall_sf() -> None:
    """A 2-room schedule + a door schedule that places one 3'-0\" × 7'-0\"
    door in each room → both rooms' wall_ALL quantities drop by 21 SF."""
    from core.extraction.takeoff_synthesis import synthesize_finish_takeoff_items

    finish = FinishScheduleResult(
        pages=[0],
        rooms=[
            FinishRecord(room_number="101", wall_finishes={"ALL": "PT-1"}),
            FinishRecord(room_number="102", wall_finishes={"ALL": "PT-2"}),
        ],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[
            RoomRecord(room_number="101", perimeter_lf=54.0, ceiling_height_ft=9.0),
            RoomRecord(room_number="102", perimeter_lf=62.0, ceiling_height_ft=10.0),
        ],
        confidence=0.9,
    )
    doors = DoorScheduleResult(
        pages=[0],
        doors=[
            DoorRecord(mark="101A", room_number="101", width_in=36, height_in=84),
            DoorRecord(mark="102A", room_number="102", width_in=36, height_in=84),
        ],
        confidence=0.9,
    )

    items = synthesize_finish_takeoff_items(finish, sheet_id="A0.3")
    out = backfill_finish_quantities(items, rooms, door_schedule=doors)

    by_room = {}
    for it in out:
        for part in (it.notes or "").split(";"):
            part = part.strip()
            if part.startswith("room="):
                by_room[part[len("room="):]] = it
                break

    assert by_room["101"].quantity == pytest.approx(54.0 * 9.0 - 21.0, abs=0.01)
    assert by_room["102"].quantity == pytest.approx(62.0 * 10.0 - 21.0, abs=0.01)
    assert "openings_deducted=1" in (by_room["101"].notes or "")
    assert "openings_deducted=1" in (by_room["102"].notes or "")


def test_inmem_room_with_door_and_window_combined() -> None:
    """Per-room: 1 door (21 SF) + 1 window (15 SF) = 36 SF combined wall_ALL deduction."""
    from core.extraction.takeoff_synthesis import synthesize_finish_takeoff_items

    finish = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(
            room_number="101", room_name="Office",
            floor_finish="VCT-1", base_finish="RB-1",
            wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
        )],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(
            room_number="101", area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
        )],
        confidence=0.9,
    )
    doors = DoorScheduleResult(
        pages=[0],
        doors=[DoorRecord(
            mark="101A", room_number="101", width_in=36, height_in=84,
        )],
        confidence=0.9,
    )
    windows = WindowScheduleResult(
        pages=[0],
        windows=[WindowRecord(
            mark="W1", room_number="101", width_in=36, height_in=60,
        )],
        confidence=0.9,
    )

    items = synthesize_finish_takeoff_items(finish, sheet_id="A0.3")
    out = backfill_finish_quantities(
        items, rooms, door_schedule=doors, window_schedule=windows,
    )
    wall = next(it for it in out if _surface_of(it) == "wall_ALL")
    expected = 54.0 * 9.0 - (21.0 + 15.0)
    assert wall.quantity == pytest.approx(expected, abs=0.01)

    # Floor / ceiling / base unchanged by opening deduction.
    floor = next(it for it in out if _surface_of(it) == "floor")
    ceiling = next(it for it in out if _surface_of(it) == "ceiling")
    base = next(it for it in out if _surface_of(it) == "base")
    assert floor.quantity == 180.0
    assert ceiling.quantity == 180.0
    assert base.quantity == 54.0


def test_inmem_compass_walls_distribute_deduction_proportionally() -> None:
    """Door (21 SF) in a room with 4 compass walls → each wall deducts 5.25 SF."""
    from core.extraction.takeoff_synthesis import synthesize_finish_takeoff_items

    finish = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(
            room_number="101",
            wall_finishes={"N": "PT-1", "S": "PT-2", "E": "PT-3", "W": "PT-4"},
        )],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(
            room_number="101", perimeter_lf=80.0, ceiling_height_ft=10.0,
        )],
        confidence=0.9,
    )
    doors = DoorScheduleResult(
        pages=[0],
        doors=[DoorRecord(
            mark="101A", room_number="101", width_in=36, height_in=84,
        )],
        confidence=0.9,
    )

    items = synthesize_finish_takeoff_items(finish, sheet_id="A0.3")
    out = backfill_finish_quantities(items, rooms, door_schedule=doors)

    raw_per_wall = 80.0 * 10.0 / 4.0
    expected_per_wall = raw_per_wall - (21.0 / 4.0)
    for it in out:
        assert it.quantity == pytest.approx(expected_per_wall, abs=0.01)


# ---------------------------------------------------------------------------
# 2. End-to-end PDF path through reconcile()
# ---------------------------------------------------------------------------


def test_full_pipeline_pdf_with_door_room_number_reduces_wall_sf(tmp_path: Path) -> None:
    """Synthetic 2-sheet PDF set (combined room+finish schedule + door
    schedule with ROOM column) → reconcile → finish wall rows have
    quantities reduced by exactly each room's door SF total."""
    combined = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "BASE", "WALL", "CEILING", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",    "Lobby",  "240",  "62",        "VCT-1", "RB-1", "PT-2", "ACT-1",   "10'-0\""],
        ],
    )
    doors_pdf = _build_pdf(
        tmp_path, "doors.pdf",
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "FRAME", "HARDWARE"],
            ["101A", "101",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
            ["102A", "102",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
            ["102B", "102",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-2"],
        ],
    )

    sheets = [
        _sheet_from_prepass(combined, 0, sheet_id="A0.3"),
        _sheet_from_prepass(doors_pdf, 0, sheet_id="A0.1"),
    ]
    # Sanity: door schedule parsed room_number correctly.
    door_sched = sheets[1].prepass.door_schedule
    assert door_sched is not None
    by_mark = {d.mark: d for d in door_sched.doors}
    assert by_mark["101A"].room_number == "101"
    assert by_mark["102A"].room_number == "102"
    assert by_mark["102B"].room_number == "102"

    project = reconcile(sheets)
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and _surface_of(t) == "wall_ALL"
    ]
    by_room: dict[str, object] = {}
    for it in finishes:
        for part in (it.notes or "").split(";"):
            part = part.strip()
            if part.startswith("room="):
                by_room[part[len("room="):]] = it
                break

    # Room 101: 54 * 9 = 486 raw - 21 (1 door) = 465 SF.
    assert by_room["101"].quantity == pytest.approx(486.0 - 21.0, abs=0.01)
    # Room 102: 62 * 10 = 620 raw - 42 (2 doors) = 578 SF.
    assert by_room["102"].quantity == pytest.approx(620.0 - 42.0, abs=0.01)
    assert "openings_deducted=1" in (by_room["101"].notes or "")
    assert "openings_deducted=2" in (by_room["102"].notes or "")


def test_full_pipeline_pdf_with_window_room_number_reduces_wall_sf(tmp_path: Path) -> None:
    """Same as above but for windows — window schedule with ROOM column
    flows through prepass and lands as wall SF deduction in reconcile."""
    combined = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "WALL", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "PT-1", "9'-0\""],
        ],
    )
    windows_pdf = _build_pdf(
        tmp_path, "windows.pdf",
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "101",  "ALUM", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "101",  "ALUM", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
        ],
    )
    sheets = [
        _sheet_from_prepass(combined, 0, sheet_id="A0.3"),
        _sheet_from_prepass(windows_pdf, 0, sheet_id="A0.2"),
    ]
    win_sched = sheets[1].prepass.window_schedule
    assert win_sched is not None
    for w in win_sched.windows:
        assert w.room_number == "101"

    project = reconcile(sheets)
    walls = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and _surface_of(t) == "wall_ALL"
    ]
    assert len(walls) == 1
    # 54 * 9 = 486 raw - 2 * (3*5) = 486 - 30 = 456 SF.
    assert walls[0].quantity == pytest.approx(456.0, abs=0.01)
    assert "openings_deducted=2" in (walls[0].notes or "")


# ---------------------------------------------------------------------------
# 3. Schedule extractor → schema bridge preserves room_number
# ---------------------------------------------------------------------------


def test_door_schedule_room_number_survives_pydantic_round_trip(tmp_path: Path) -> None:
    """``DoorRecord.room_number`` is preserved through the prepass-to-schema
    Pydantic bridge (no field gets silently dropped during conversion)."""
    pdf = _build_pdf(
        tmp_path, "doors_with_room.pdf",
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "FRAME", "HARDWARE"],
            ["101A", "101",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.1")
    door_sched = sheet.prepass.door_schedule
    assert door_sched is not None
    assert door_sched.doors[0].room_number == "101"


def test_window_schedule_room_number_survives_pydantic_round_trip(tmp_path: Path) -> None:
    """Mirror of the door case for windows."""
    pdf = _build_pdf(
        tmp_path, "windows_with_room.pdf",
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "201",  "ALUM", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.2")
    win_sched = sheet.prepass.window_schedule
    assert win_sched is not None
    assert win_sched.windows[0].room_number == "201"


# ---------------------------------------------------------------------------
# 4. Cross-pollination: T5.1 must not perturb the existing T5 path on
#    PDFs that lack door / window schedules
# ---------------------------------------------------------------------------


def test_pipeline_without_door_or_window_schedules_unchanged(tmp_path: Path) -> None:
    """A PDF with just a ROOM FINISH SCHEDULE (no doors / windows) →
    behaves exactly as T5: wall SF is gross, BACKFILL_NOTE_NO_OPENINGS
    appears."""
    from core.extraction.takeoff_backfill import BACKFILL_NOTE_NO_OPENINGS

    pdf = _build_pdf(
        tmp_path, "rooms_only.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "WALL", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "PT-1", "9'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.3")
    project = reconcile([sheet])
    walls = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and _surface_of(t) == "wall_ALL"
    ]
    assert len(walls) == 1
    assert walls[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    assert BACKFILL_NOTE_NO_OPENINGS in (walls[0].notes or "")


def test_pipeline_door_without_room_column_is_orphan(tmp_path: Path) -> None:
    """A door schedule without a ROOM column → records have room_number=None
    → all doors are orphans → no deduction; wall SF remains gross."""
    combined = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "WALL", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "PT-1", "9'-0\""],
        ],
    )
    doors_pdf = _build_pdf(
        tmp_path, "doors_no_room.pdf",
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH",  "HEIGHT", "FRAME", "HARDWARE"],
            ["101A", "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
        ],
    )
    sheets = [
        _sheet_from_prepass(combined, 0, sheet_id="A0.3"),
        _sheet_from_prepass(doors_pdf, 0, sheet_id="A0.1"),
    ]
    # The door has no room_number.
    assert sheets[1].prepass.door_schedule.doors[0].room_number is None

    project = reconcile(sheets)
    walls = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and _surface_of(t) == "wall_ALL"
    ]
    assert walls[0].quantity == pytest.approx(54.0 * 9.0, abs=0.01)
    assert "openings_deducted=" not in (walls[0].notes or "")


# ---------------------------------------------------------------------------
# 5. Defaults sanity — confirm the documented SF values
# ---------------------------------------------------------------------------


def test_documented_default_opening_sizes() -> None:
    """The published defaults (DOOR=21 SF, WINDOW=12 SF) are stable —
    any change here ripples into every wall row on every project that
    has dimension-less openings, so we pin them deliberately."""
    assert DOOR_DEFAULT_OPENING_SF == 21.0     # 3'-0" × 7'-0"
    assert WINDOW_DEFAULT_OPENING_SF == 12.0   # 3'-0" × 4'-0"
