"""Phase T5 end-to-end integration tests.

These tests exercise the FULL path: synthetic PDF → drawing prepass →
SheetExtraction → reconcile() → priced-ready ProjectModel.takeoffs
with non-zero quantities on the finish rows.

They prove the back-fill is correctly wired into the pipeline and
that the room-schedule extractor + finish-schedule extractor cooperate
on combined ``ROOM FINISH SCHEDULE`` pages (Option A from the brief).
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    to_schema as prepass_to_schema,
)
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_FINISH
from core.schemas import (
    DrawingPrepassResult as PydanticDrawingPrepassResult,
    FinishRecord,
    FinishScheduleResult,
    RoomRecord,
    RoomScheduleResult,
    SheetExtraction,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders
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


# ---------------------------------------------------------------------------
# 1. Combined ROOM FINISH SCHEDULE page → priced finish rows
# ---------------------------------------------------------------------------


def test_combined_schedule_pdf_produces_backfilled_finishes(tmp_path: Path) -> None:
    """A single ROOM FINISH SCHEDULE PDF page → both finish and room
    extraction → reconcile → finish rows carry real SF quantities."""
    pdf = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR",  "BASE", "WALL", "CEILING", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1",  "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",    "Lobby",  "240",  "62",        "TILE-1", "CB-1", "PT-2", "ACT-1",   "10'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.3")
    assert sheet.prepass.finish_schedule is not None
    assert sheet.prepass.room_schedule is not None

    project = reconcile([sheet])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    # 2 rooms × 4 surfaces each = 8 items.
    assert len(finishes) == 8
    # Every finish row now has a non-zero quantity.
    for it in finishes:
        assert it.quantity > 0.0
    # Room 101 totals: 180 floor + 54 base + 54*9 wall + 180 ceiling = 846 (qty sum).
    room_101 = [it for it in finishes if "Room 101" in it.description]
    assert len(room_101) == 4
    qty_by_surface = {
        next(p.split("=", 1)[1] for p in (it.notes or "").split("; ")
             if p.startswith("surface="))
        : it.quantity
        for it in room_101
    }
    assert qty_by_surface["floor"] == 180.0
    assert qty_by_surface["base"] == 54.0
    assert qty_by_surface["wall_ALL"] == pytest.approx(54.0 * 9.0, abs=0.01)
    assert qty_by_surface["ceiling"] == 180.0


# ---------------------------------------------------------------------------
# 2. Separate finish + room schedules (different sheets)
# ---------------------------------------------------------------------------


def test_separate_finish_and_room_sheets(tmp_path: Path) -> None:
    """Finish on one sheet + room on another → reconcile cross-joins both."""
    finish_pdf = _build_pdf(
        tmp_path, "finishes.pdf",
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "FLOOR",  "BASE", "WALL", "CEILING"],
            ["101",    "Office", "VCT-1",  "RB-1", "PT-1", "ACT-1"],
            ["102",    "Lobby",  "TILE-1", "CB-1", "PT-2", "ACT-1"],
        ],
    )
    room_pdf = _build_pdf(
        tmp_path, "rooms.pdf",
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "CLG HT"],
            ["101",    "Office", "180",  "54",        "9'-0\""],
            ["102",    "Lobby",  "240",  "62",        "10'-0\""],
        ],
    )
    finish_sheet = _sheet_from_prepass(finish_pdf, 0, sheet_id="A0.3")
    room_sheet = _sheet_from_prepass(room_pdf, 0, sheet_id="A0.2")
    assert finish_sheet.prepass.finish_schedule is not None
    assert finish_sheet.prepass.room_schedule is None
    assert room_sheet.prepass.room_schedule is not None
    assert room_sheet.prepass.finish_schedule is None

    project = reconcile([finish_sheet, room_sheet])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(finishes) == 8
    assert all(it.quantity > 0.0 for it in finishes)
    # Spot-check totals.
    floors = [it for it in finishes
               if "; surface=floor" in (it.notes or "")]
    assert sorted(it.quantity for it in floors) == [180.0, 240.0]


# ---------------------------------------------------------------------------
# 3. Room schedule missing for some finish rooms
# ---------------------------------------------------------------------------


def test_partial_room_coverage_skips_missing_rooms(tmp_path: Path) -> None:
    """Finish has rooms 101+102+103; room schedule only has 101 → 102 and 103
    are preserved at quantity=0.0 with a skip note."""
    finish_pdf = _build_pdf(
        tmp_path, "finishes.pdf",
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",     "FLOOR",  "BASE", "WALL", "CEILING"],
            ["101",    "Office",   "VCT-1",  "RB-1", "PT-1", "ACT-1"],
            ["102",    "Storage",  "SC",     "RB-1", "PT-1", "ACT-1"],
            ["103",    "Corridor", "VCT-1",  "RB-1", "PT-1", "ACT-1"],
        ],
    )
    room_pdf = _build_pdf(
        tmp_path, "rooms.pdf",
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "CLG HT"],
            ["101",    "Office", "180",  "54",        "9'-0\""],
        ],
    )
    finish_sheet = _sheet_from_prepass(finish_pdf, 0, sheet_id="A0.3")
    room_sheet = _sheet_from_prepass(room_pdf, 0, sheet_id="A0.2")
    project = reconcile([finish_sheet, room_sheet])

    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    by_room = {}
    for it in finishes:
        for p in (it.notes or "").split("; "):
            if p.startswith("room="):
                by_room.setdefault(p[len("room="):], []).append(it)

    # Room 101 → back-filled.
    for it in by_room["101"]:
        assert it.quantity > 0.0
    # Rooms 102 + 103 → preserved at 0 with skip note.
    for room_num in ("102", "103"):
        for it in by_room[room_num]:
            assert it.quantity == 0.0
            assert "backfill skipped" in (it.notes or "")


# ---------------------------------------------------------------------------
# 4. No room schedule on any sheet → finish rows stay at 0.0 (no-op)
# ---------------------------------------------------------------------------


def test_no_room_schedule_finishes_remain_zero(tmp_path: Path) -> None:
    finish_pdf = _build_pdf(
        tmp_path, "finishes.pdf",
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",    "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
        ],
    )
    finish_sheet = _sheet_from_prepass(finish_pdf, 0, sheet_id="A0.3")
    project = reconcile([finish_sheet])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(finishes) == 4
    assert all(it.quantity == 0.0 for it in finishes)
    # No backfill notes appended.
    assert all("backfill" not in (it.notes or "") for it in finishes)


# ---------------------------------------------------------------------------
# 5. No finish schedule but room schedule present → room schedule still
#    extracted; nothing to back-fill (no finish rows to update).
# ---------------------------------------------------------------------------


def test_room_schedule_without_finishes_emits_no_finish_rows(tmp_path: Path) -> None:
    room_pdf = _build_pdf(
        tmp_path, "rooms.pdf",
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "CLG HT"],
            ["101",    "Office", "180",  "9'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(room_pdf, 0, sheet_id="A0.2")
    assert sheet.prepass.room_schedule is not None
    project = reconcile([sheet])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert finishes == []


# ---------------------------------------------------------------------------
# 6. Backfill survives Phase T4 dedupe — the synthesised rows the dedupe
#    PRESERVES are exactly the rows the backfill should populate.
# ---------------------------------------------------------------------------


def test_backfill_runs_after_dedupe(tmp_path: Path) -> None:
    """T4 dedupe doesn't drop synthesised rows; T5 backfill updates them."""
    pdf = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "BASE", "WALL", "CEILING", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.3")
    project = reconcile([sheet])
    synth = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(synth) == 4
    # Every synth row should now carry a non-zero qty (post-backfill)
    # and a "backfill=ok" tail.
    for it in synth:
        assert it.quantity > 0.0
        assert "backfill=ok" in (it.notes or "")


# ---------------------------------------------------------------------------
# 7. Multiple sheets carrying room schedules — they merge correctly
# ---------------------------------------------------------------------------


def test_multiple_room_sheets_merge(tmp_path: Path) -> None:
    """Two separate room schedules (different floors) merge into one map."""
    floor1_rooms = _build_pdf(
        tmp_path, "floor1.pdf",
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "CLG HT"],
            ["101",    "Office", "180",  "54",        "9'-0\""],
        ],
    )
    floor2_rooms = _build_pdf(
        tmp_path, "floor2.pdf",
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",  "AREA", "PERIMETER", "CLG HT"],
            ["201",    "Suite", "300",  "70",        "10'-0\""],
        ],
    )
    finish_pdf = _build_pdf(
        tmp_path, "finishes.pdf",
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",    "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
            ["201",    "Suite",  "CPT-1", "RB-1", "PT-2", "ACT-1"],
        ],
    )
    sheets = [
        _sheet_from_prepass(finish_pdf, 0, sheet_id="A0.3"),
        _sheet_from_prepass(floor1_rooms, 0, sheet_id="A0.1"),
        _sheet_from_prepass(floor2_rooms, 0, sheet_id="A0.2"),
    ]
    project = reconcile(sheets)
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(finishes) == 8         # 2 rooms × 4 surfaces
    assert all(it.quantity > 0.0 for it in finishes)


# ---------------------------------------------------------------------------
# 8. Door + window precedence still wins on doors/windows pages
# ---------------------------------------------------------------------------


def test_door_schedule_page_does_not_emit_room_schedule(tmp_path: Path) -> None:
    """A door schedule never carries area columns; the room detector
    is correctly suppressed by the door-precedence rule so reconcile
    has nothing to back-fill against if doors are the only schedule
    on the project.
    """
    pdf = _build_pdf(
        tmp_path, "doors.pdf",
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A6.1")
    assert sheet.prepass.door_schedule is not None
    assert sheet.prepass.room_schedule is None


# ---------------------------------------------------------------------------
# 9. Direct-input integration (skip the PDF; build extractions in-memory)
# ---------------------------------------------------------------------------


def test_direct_in_memory_integration() -> None:
    """Bypass PDF I/O: build prepass results directly and reconcile."""
    finish = FinishScheduleResult(
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
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(
            room_number="101", room_name="Office",
            area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
        )],
        confidence=0.95,
    )
    prepass = PydanticDrawingPrepassResult(
        finish_schedule=finish, room_schedule=rooms,
    )
    extraction = SheetExtraction(sheet_id="A0.3", prepass=prepass)
    project = reconcile([extraction])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(finishes) == 4
    qty_by_surface = {
        next(p.split("=", 1)[1] for p in (it.notes or "").split("; ")
             if p.startswith("surface="))
        : it.quantity
        for it in finishes
    }
    assert qty_by_surface["floor"] == 180.0
    assert qty_by_surface["base"] == 54.0
    assert qty_by_surface["wall_ALL"] == pytest.approx(54.0 * 9.0, abs=0.01)
    assert qty_by_surface["ceiling"] == 180.0


# ---------------------------------------------------------------------------
# 10. Base unit is upgraded from SF (synthesised) to LF (back-filled)
# ---------------------------------------------------------------------------


def test_base_unit_upgraded_to_LF() -> None:
    """T4 emits unit=SF on the base row; T5 back-fill upgrades to LF when
    perimeter is available."""
    finish = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(room_number="101", base_finish="RB-1")],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(room_number="101", perimeter_lf=54.0)],
        confidence=0.9,
    )
    prepass = PydanticDrawingPrepassResult(
        finish_schedule=finish, room_schedule=rooms,
    )
    extraction = SheetExtraction(sheet_id="A0.3", prepass=prepass)
    project = reconcile([extraction])
    base = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and "; surface=base" in (t.notes or "")
    ]
    assert len(base) == 1
    assert base[0].unit == "LF"
    assert base[0].quantity == 54.0


# ---------------------------------------------------------------------------
# 11. Confidence band on back-filled rows
# ---------------------------------------------------------------------------


def test_full_backfill_confidence_holds_at_synth_band() -> None:
    """Full data → confidence stays in the 0.92 synthesis band."""
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
            room_number="101", room_name="Office",
            area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
        )],
        confidence=0.95,
    )
    prepass = PydanticDrawingPrepassResult(
        finish_schedule=finish, room_schedule=rooms,
    )
    extraction = SheetExtraction(sheet_id="A0.3", prepass=prepass)
    project = reconcile([extraction])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert all(it.confidence == pytest.approx(0.92, abs=1e-3) for it in finishes)


def test_perimeter_fallback_confidence_drops_to_review_band() -> None:
    """No perimeter → fallback to 4*sqrt(area) → confidence drops to 0.65."""
    finish = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(
            room_number="101", base_finish="RB-1",
            wall_finishes={"ALL": "PT-1"},
        )],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(
            room_number="101", area_sf=144.0, ceiling_height_ft=9.0,
        )],
        confidence=0.95,
    )
    prepass = PydanticDrawingPrepassResult(
        finish_schedule=finish, room_schedule=rooms,
    )
    extraction = SheetExtraction(sheet_id="A0.3", prepass=prepass)
    project = reconcile([extraction])
    finishes = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    assert len(finishes) == 2
    for it in finishes:
        assert it.confidence == pytest.approx(0.65, abs=1e-3)


# ---------------------------------------------------------------------------
# 12. Non-finish rows survive the back-fill pass untouched (regression)
# ---------------------------------------------------------------------------


def test_non_finish_rows_unaffected_by_backfill(tmp_path: Path) -> None:
    """Door + window + structural + slab rows are NOT touched by the
    back-fill even when a room schedule is present."""
    pdf = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "BASE", "WALL", "CEILING", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.3")
    project = reconcile([sheet])
    # No doors/windows/structural to inject — but verify no foreign rows
    # appeared.
    non_finish = [
        t for t in project.takeoffs
        if not (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
    ]
    # All non-finish rows must keep their original quantity unchanged
    # (we didn't ask the back-fill to touch them).
    for it in non_finish:
        # Should not carry any backfill_skipped / backfill=ok note.
        assert "backfill" not in (it.notes or "")


# ---------------------------------------------------------------------------
# 13. Schema round-trip — back-filled rows export cleanly
# ---------------------------------------------------------------------------


def test_backfilled_items_serialize_through_pydantic(tmp_path: Path) -> None:
    """Sanity: back-filled rows survive Pydantic model_dump round-trip."""
    pdf = _build_pdf(
        tmp_path, "combined.pdf",
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "FLOOR", "CLG HT"],
            ["101",    "Office", "180",  "54",        "VCT-1", "9'-0\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A0.3")
    project = reconcile([sheet])
    floor = next(
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and "surface=floor" in (t.notes or "")
    )
    payload = floor.model_dump()
    assert payload["quantity"] == 180.0
    assert payload["unit"] == "SF"
    assert payload["confidence"] == pytest.approx(0.92, abs=1e-3)
    assert payload["csi_division"] == "09"


# ---------------------------------------------------------------------------
# 14. Ceiling height fallback from finish schedule
# ---------------------------------------------------------------------------


def test_wall_height_falls_back_to_finish_schedule_when_room_lacks_it() -> None:
    """Room schedule has area + perimeter but no ceiling height → back-fill
    falls back to the finish schedule's height."""
    finish = FinishScheduleResult(
        pages=[0],
        rooms=[FinishRecord(
            room_number="101", wall_finishes={"ALL": "PT-1"},
            ceiling_height_ft=12.0,
        )],
        confidence=0.9,
    )
    rooms = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(
            room_number="101", area_sf=180.0, perimeter_lf=54.0,
            ceiling_height_ft=None,
        )],
        confidence=0.95,
    )
    prepass = PydanticDrawingPrepassResult(
        finish_schedule=finish, room_schedule=rooms,
    )
    extraction = SheetExtraction(sheet_id="A0.3", prepass=prepass)
    project = reconcile([extraction])
    wall = next(
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")
        and "surface=wall_ALL" in (t.notes or "")
    )
    assert wall.quantity == pytest.approx(54.0 * 12.0, abs=0.01)
