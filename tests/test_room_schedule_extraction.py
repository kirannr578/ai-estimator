"""Tests for the room-schedule pre-pass (Phase T5).

Every test builds a synthetic 1-page PDF on disk with ``fitz``
(PyMuPDF) so we don't need any binary fixtures checked into the repo.
Conventions mirror :mod:`tests.test_finish_schedule_extraction`; the
combined-schedule discriminator tests at the bottom assert Option A —
a single ``ROOM FINISH SCHEDULE`` page produces BOTH a
``FinishScheduleResult`` AND a ``RoomScheduleResult`` because the two
detectors run without precedence vs. each other.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    prepass_drawing_pdf,
    to_schema as prepass_to_schema,
)
from core.extraction.room_schedule import (
    RoomRecord,
    RoomScheduleResult,
    _parse_area,
    _parse_ceiling_height,
    _parse_perimeter,
    detect_room_schedule,
    extract_room_schedule,
    extract_room_schedule_from_page,
    merge_room_schedules,
    to_schema,
)
from core.schemas import RoomScheduleResult as PydanticRoomScheduleResult


# ---------------------------------------------------------------------------
# Fixture builder
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
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
    if body_lines:
        y = 130.0
        for line in body_lines:
            page.insert_text((40, y), line, fontsize=10)
            y += 14
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


def _build_pdf(
    tmp_path: Path,
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    name: str = "test.pdf",
) -> Path:
    doc = fitz.open()
    _add_page(doc, title_lines=title_lines, body_lines=body_lines, table=table)
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# 1. Area / perimeter / ceiling-height parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("180",        180.0),
        ("180.5",      180.5),
        ("180 SF",     180.0),
        ("180.5 SF",   180.5),
        ("180 sq ft",  180.0),
        ("180 SQFT",   180.0),
        ("180 ft2",    180.0),
        ("180 S.F.",   180.0),
        ("1,234",      1234.0),
        ("1,234.5",    1234.5),
        ("",           None),
        (None,         None),
        ("   ",        None),
        ("abc",        None),
        ("180m",       None),       # ambiguous unit — reject
    ],
)
def test_parse_area(raw, expected) -> None:
    assert _parse_area(raw) == expected


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("54",        54.0),
        ("54 LF",     54.0),
        ("54.5 LF",   54.5),
        ("54 LIN FT", 54.0),
        ("54 L.F.",   54.0),
        ("",          None),
        (None,        None),
        ("abc",       None),
    ],
)
def test_parse_perimeter(raw, expected) -> None:
    assert _parse_perimeter(raw) == expected


@pytest.mark.parametrize(
    "raw, expected_ft",
    [
        ("9'-0\"", 9.0),
        ("9'",     9.0),
        ("10'",    10.0),
        ("9.5",    9.5),
        ("9.5 FT", 9.5),
        ("9.5'",   9.5),
        ("9' - 6\"", 9.5),
        ("12'-0\"", 12.0),
        ("",       None),
        (None,     None),
        ("abc",    None),
    ],
)
def test_parse_ceiling_height(raw, expected_ft) -> None:
    got = _parse_ceiling_height(raw)
    if expected_ft is None:
        assert got is None
    else:
        assert got == pytest.approx(expected_ft, abs=1e-3)


# ---------------------------------------------------------------------------
# 2. Detection heuristic
# ---------------------------------------------------------------------------


def test_detect_room_schedule_by_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE", "Project: Example"],
        name="phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is True


def test_detect_room_schedule_by_room_finish_phrase(tmp_path: Path) -> None:
    """Combined ROOM FINISH SCHEDULE phrase also triggers the room detector."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM FINISH SCHEDULE"],
        name="combined_phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is True


def test_detect_room_schedule_by_table_header(tmp_path: Path) -> None:
    """Standalone room-schedule table with AREA + CLG HT columns."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["Sheet A0.2"],
        table=[
            ["ROOM #", "NAME",   "AREA",  "CLG HT", "OCCUPANCY"],
            ["101",    "Office", "180",   "9'-0\"", "OFFICE"],
            ["102",    "Lobby",  "240",   "10'-0\"", "ASSEMBLY"],
        ],
        name="header.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is True


def test_detect_room_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=["Room 101 is 12'-0\" x 14'-0\"."],
        name="negative.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is False


def test_detect_room_schedule_rejects_door_table(tmp_path: Path) -> None:
    """A door schedule must NOT detect as room (HARDWARE disqualifies)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",  "WD",  "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
        name="door_only.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is False


def test_detect_room_schedule_rejects_window_table(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "VINYL", "2'-8\"", "4'-8\"", "LOW-E",   "DH"],
        ],
        name="window_only.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is False


def test_detect_room_schedule_rejects_finish_only_no_area(tmp_path: Path) -> None:
    """A finish schedule without an AREA column must NOT detect as room.

    The AREA column is the primary discriminator: without it we can't
    do anything useful at back-fill time.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["Sheet A0.3"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
            ["102",  "Lobby",  "TILE-1","CB-1", "PT-2", "ACT-1"],
        ],
        name="finish_no_area.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_room_schedule(doc[0]) is False


# ---------------------------------------------------------------------------
# 3. End-to-end extraction
# ---------------------------------------------------------------------------


def test_extract_room_schedule_parses_records(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",     "AREA",    "PERIMETER", "CLG HT",  "OCCUPANCY"],
            ["101",    "Office",   "180",     "54",        "9'-0\"",  "OFFICE"],
            ["102",    "Lobby",    "240 SF",  "62 LF",     "10'-0\"", "ASSEMBLY"],
            ["103",    "Corridor", "120.5",   "",          "9.5",     "CORRIDOR"],
        ],
        name="standalone.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    assert isinstance(result, RoomScheduleResult)
    assert len(result.rooms) == 3
    by_num = {r.room_number: r for r in result.rooms}
    assert by_num["101"].room_name == "Office"
    assert by_num["101"].area_sf == 180.0
    assert by_num["101"].perimeter_lf == 54.0
    assert by_num["101"].ceiling_height_ft == pytest.approx(9.0, abs=1e-3)
    assert by_num["101"].occupancy_type == "OFFICE"
    assert by_num["102"].area_sf == 240.0
    assert by_num["102"].perimeter_lf == 62.0
    assert by_num["102"].ceiling_height_ft == pytest.approx(10.0, abs=1e-3)
    assert by_num["103"].area_sf == 120.5
    assert by_num["103"].perimeter_lf is None     # blank cell
    assert by_num["103"].ceiling_height_ft == pytest.approx(9.5, abs=1e-3)


def test_extract_room_schedule_handles_missing_cells(tmp_path: Path) -> None:
    """Rows with partial data still produce a record; missing fields → None."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME", "AREA", "CLG HT"],
            ["101",    "Office", "180", "9'-0\""],
            ["102",    "",       "240", ""],          # name + height missing
            ["103",    "Storage", "",   "9.5"],       # area missing
        ],
        name="partial.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    assert len(result.rooms) == 3
    by_num = {r.room_number: r for r in result.rooms}
    assert by_num["102"].room_name is None
    assert by_num["102"].ceiling_height_ft is None
    assert by_num["103"].area_sf is None
    assert by_num["103"].ceiling_height_ft == pytest.approx(9.5, abs=1e-3)


def test_extract_room_schedule_no_table_returns_empty(tmp_path: Path) -> None:
    """Page with no detectable room schedule → empty result."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN"],
        body_lines=["No tables here."],
        name="empty.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    assert result.rooms == []
    assert result.confidence == 0.0


def test_extract_room_schedule_preserves_raw_cells(tmp_path: Path) -> None:
    """``raw_cells`` is populated with non-empty values keyed by header text."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME", "AREA", "CLG HT"],
            ["101", "Office", "180 SF", "9'-0\""],
        ],
        name="raw.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    assert len(result.rooms) == 1
    raw = result.rooms[0].raw_cells
    # Header keys present (PyMuPDF sometimes lowercases; we just check
    # the values came through).
    values = set(raw.values())
    assert "101" in values
    assert "Office" in values
    assert "180 SF" in values


def test_extract_room_schedule_confidence_scoring(tmp_path: Path) -> None:
    """≥5 records + has phrase + table + area+height → confidence near 1.0."""
    rows = [["ROOM #", "NAME", "AREA", "CLG HT"]] + [
        [str(100 + i), f"Room {i}", str(100 + i * 10), "9'-0\""] for i in range(1, 7)
    ]
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=rows,
        name="conf.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    assert len(result.rooms) == 6
    assert result.confidence == pytest.approx(1.0, abs=1e-3)


def test_extract_room_schedule_filters_out_non_room_tags(tmp_path: Path) -> None:
    """Rows whose first cell has spaces (sub-headers) are filtered out."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #",       "NAME",   "AREA", "CLG HT"],
            ["First Floor",  "",       "",     ""],          # sub-header — drop
            ["101",          "Office", "180",  "9'-0\""],
            ["102",          "Lobby",  "240",  "10'-0\""],
        ],
        name="subheader.pdf",
    )
    result = extract_room_schedule(pdf, 0)
    nums = {r.room_number for r in result.rooms}
    assert "101" in nums
    assert "102" in nums
    assert "First Floor" not in nums


# ---------------------------------------------------------------------------
# 4. Combined-schedule discriminator (Option A): BOTH detectors fire
# ---------------------------------------------------------------------------


def test_combined_schedule_both_detectors_fire(tmp_path: Path) -> None:
    """A combined ROOM FINISH SCHEDULE produces BOTH FinishScheduleResult
    AND RoomScheduleResult (Option A — no precedence vs. each other).
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA",   "FLOOR",  "BASE", "WALL", "CEILING", "CLG HT"],
            ["101",    "Office", "180",    "VCT-1",  "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",    "Lobby",  "240",    "TILE-1", "CB-1", "PT-2", "ACT-1",   "10'-0\""],
        ],
        name="combined.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.finish_schedule is not None, "finish detector should fire"
    assert result.room_schedule is not None, "room detector should fire"
    assert len(result.finish_schedule.rooms) == 2
    assert len(result.room_schedule.rooms) == 2

    # The two record sets carry the same room numbers — that's the
    # join key the back-fill uses.
    finish_nums = {r.room_number for r in result.finish_schedule.rooms}
    room_nums = {r.room_number for r in result.room_schedule.rooms}
    assert finish_nums == room_nums == {"101", "102"}

    # Finish schedule carries finish codes but NOT areas.
    finish_by_num = {r.room_number: r for r in result.finish_schedule.rooms}
    assert finish_by_num["101"].floor_finish == "VCT-1"
    # Room schedule carries areas.
    room_by_num = {r.room_number: r for r in result.room_schedule.rooms}
    assert room_by_num["101"].area_sf == 180.0
    assert room_by_num["102"].area_sf == 240.0


def test_combined_schedule_door_precedence_skips_room(tmp_path: Path) -> None:
    """If a door schedule was already extracted on a page, the room
    detector skips that page entirely (defensive — a door schedule
    never carries AREA so this should never fire in practice).
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",  "WD",  "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
        name="door_with_room_phrase.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.door_schedule is not None
    assert result.room_schedule is None


def test_standalone_room_schedule_separate_sheet(tmp_path: Path) -> None:
    """A pure room-only schedule on its own sheet produces only a
    RoomScheduleResult (no finish_schedule fires)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME",   "AREA", "PERIMETER", "CLG HT", "OCCUPANCY"],
            ["101",    "Office", "180",  "54",        "9'-0\"", "OFFICE"],
            ["102",    "Lobby",  "240",  "62",        "10'",    "ASSEMBLY"],
        ],
        name="room_only.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.room_schedule is not None
    assert len(result.room_schedule.rooms) == 2
    # Finish detector should NOT fire: no floor/base/wall/ceiling cols.
    assert result.finish_schedule is None


# ---------------------------------------------------------------------------
# 5. prepass_drawing_pdf integration
# ---------------------------------------------------------------------------


def test_prepass_drawing_pdf_wires_room_schedule(tmp_path: Path) -> None:
    """``prepass_drawing_pdf`` populates ``room_schedule`` per page."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME", "AREA", "CLG HT"],
            ["101", "Office", "180", "9'-0\""],
        ],
    )
    _add_page(
        doc,
        title_lines=["FLOOR PLAN A101"],
        body_lines=["No tables here."],
    )
    pdf = tmp_path / "multi.pdf"
    doc.save(pdf)
    doc.close()
    results = prepass_drawing_pdf(pdf)
    assert len(results) == 2
    assert results[0].room_schedule is not None
    assert len(results[0].room_schedule.rooms) == 1
    assert results[1].room_schedule is None


# ---------------------------------------------------------------------------
# 6. to_schema bridge
# ---------------------------------------------------------------------------


def test_to_schema_roundtrip() -> None:
    """Internal dataclass result round-trips to the Pydantic schema model."""
    src = RoomScheduleResult(
        pages=[0],
        rooms=[
            RoomRecord(
                room_number="101",
                room_name="Office",
                area_sf=180.0,
                perimeter_lf=54.0,
                ceiling_height_ft=9.0,
                ceiling_height_raw="9'-0\"",
                occupancy_type="OFFICE",
                notes=None,
                raw_cells={"ROOM #": "101", "AREA": "180"},
                source_page=0,
            )
        ],
        confidence=0.95,
        raw_table_text="ROOM # | NAME | AREA | CLG HT",
    )
    pyd = to_schema(src)
    assert isinstance(pyd, PydanticRoomScheduleResult)
    assert pyd.confidence == 0.95
    assert pyd.rooms[0].room_number == "101"
    assert pyd.rooms[0].area_sf == 180.0
    assert pyd.rooms[0].ceiling_height_ft == 9.0


def test_prepass_to_schema_includes_room_schedule(tmp_path: Path) -> None:
    """The drawing-prepass to_schema bridge populates room_schedule on
    the schema-side DrawingPrepassResult."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["ROOM #", "NAME", "AREA", "CLG HT"],
            ["101", "Office", "180", "9'-0\""],
        ],
        name="bridge.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    pyd = prepass_to_schema(result)
    assert pyd.room_schedule is not None
    assert pyd.room_schedule.rooms[0].room_number == "101"


# ---------------------------------------------------------------------------
# 7. merge_room_schedules helper
# ---------------------------------------------------------------------------


def test_merge_room_schedules_empty() -> None:
    merged = merge_room_schedules([])
    assert isinstance(merged, PydanticRoomScheduleResult)
    assert merged.rooms == []
    assert merged.confidence == 0.0


def test_merge_room_schedules_concats_distinct_rooms() -> None:
    a = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(room_number="101", room_name="Office", area_sf=180.0)],
        confidence=0.9,
    )
    b = RoomScheduleResult(
        pages=[1],
        rooms=[RoomRecord(room_number="102", room_name="Lobby", area_sf=240.0)],
        confidence=0.85,
    )
    merged = merge_room_schedules([a, b])
    nums = {r.room_number for r in merged.rooms}
    assert nums == {"101", "102"}
    assert merged.confidence == 0.9       # max across inputs
    assert 0 in merged.pages and 1 in merged.pages


def test_merge_room_schedules_dedupes_by_room_number() -> None:
    """Duplicate room# across sheets → the more-populated record wins."""
    sparse = RoomScheduleResult(
        pages=[0],
        rooms=[RoomRecord(room_number="101", area_sf=None)],
        confidence=0.5,
    )
    full = RoomScheduleResult(
        pages=[1],
        rooms=[RoomRecord(
            room_number="101", room_name="Office",
            area_sf=180.0, perimeter_lf=54.0, ceiling_height_ft=9.0,
        )],
        confidence=0.9,
    )
    merged = merge_room_schedules([sparse, full])
    assert len(merged.rooms) == 1
    assert merged.rooms[0].area_sf == 180.0
    assert merged.rooms[0].room_name == "Office"


def test_merge_room_schedules_accepts_pydantic_inputs() -> None:
    """Merge must duck-type Pydantic schema inputs (what prepass returns)."""
    from core.schemas import RoomRecord as S_RoomRecord
    from core.schemas import RoomScheduleResult as S_RoomScheduleResult

    a = S_RoomScheduleResult(
        pages=[0],
        rooms=[S_RoomRecord(
            room_number="101", room_name="Office", area_sf=180.0,
        )],
        confidence=0.9,
    )
    merged = merge_room_schedules([a])
    assert len(merged.rooms) == 1
    assert merged.rooms[0].area_sf == 180.0
