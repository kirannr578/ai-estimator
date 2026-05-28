"""Tests for the finish-schedule pre-pass (Phase T4).

Every test builds a synthetic 1-page PDF on disk with `fitz` (PyMuPDF) so
we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_window_schedule_extraction`; the discriminator
tests on the bottom assert door + window precedence (a single page
with door OR window content suppresses the finish extractor).
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import prepass_drawing_page, prepass_drawing_pdf
from core.extraction.finish_schedule import (
    FinishRecord,
    FinishScheduleResult,
    detect_finish_schedule,
    extract_finish_schedule,
    extract_finish_schedule_from_page,
    parse_finish_code,
)


# ---------------------------------------------------------------------------
# Fixture builder (kept local — mirrors helper in test_window_schedule_extraction)
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
    """Append a 1-page PDF with optional title text, body text, and a grid table."""
    page = doc.new_page(width=900, height=612)   # wider so 8+ columns fit

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
    table_origin: tuple[float, float] = (40.0, 200.0),
    cell_size: tuple[float, float] = (75.0, 24.0),
    name: str = "test.pdf",
) -> Path:
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=title_lines,
        body_lines=body_lines,
        table=table,
        table_origin=table_origin,
        cell_size=cell_size,
    )
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# parse_finish_code unit tests
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw, expected",
    [
        ("VCT-1",     ("VCT", "1")),
        ("VCT 1",     ("VCT", "1")),
        ("vct-1",     ("VCT", "1")),
        ("CPT-2A",    ("CPT", "2A")),
        ("PT-1",      ("PT", "1")),
        ("ACT-1",     ("ACT", "1")),
        ("RB-1",      ("RB", "1")),
        ("POL-CONC",  ("POL", "CONC")),
        ("POL CONC",  ("POL", "CONC")),
        ("ACT",       ("ACT", None)),
        ("VCT",       ("VCT", None)),
        ("",          (None, None)),
        (None,        (None, None)),
        ("   ",       (None, None)),
    ],
)
def test_parse_finish_code(raw, expected) -> None:
    assert parse_finish_code(raw) == expected


# ---------------------------------------------------------------------------
# Detection heuristic
# ---------------------------------------------------------------------------


def test_detect_finish_schedule_by_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM FINISH SCHEDULE", "Project: Example"],
        name="phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_finish_schedule(doc[0]) is True


def test_detect_finish_schedule_by_short_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        name="short_phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_finish_schedule(doc[0]) is True


def test_detect_finish_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["Sheet A0.3"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING", "HEIGHT"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",  "Lobby",  "TILE-1","CB-1", "PT-2", "ACT-1",   "9'-0\""],
        ],
        name="header.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_finish_schedule(doc[0]) is True


def test_detect_finish_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=[
            "This page is a floor plan with prose and a few callouts.",
            "Room 101 is 12'-0\" x 14'-0\".",
        ],
        name="negative.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_finish_schedule(doc[0]) is False


def test_detect_finish_schedule_rejects_door_table(tmp_path: Path) -> None:
    """A door schedule on the same page must NOT detect as finish."""
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
        # Door-specific HARDWARE column actively disqualifies the
        # finish header heuristic; phrase trigger is also absent.
        assert detect_finish_schedule(doc[0]) is False


def test_detect_finish_schedule_rejects_window_table(tmp_path: Path) -> None:
    """A window schedule must NOT detect as finish."""
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
        assert detect_finish_schedule(doc[0]) is False


# ---------------------------------------------------------------------------
# End-to-end extraction
# ---------------------------------------------------------------------------


def test_extract_finish_schedule_parses_records(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",     "FLOOR",  "BASE", "WALL", "CEILING", "HEIGHT"],
            ["101",  "Office",   "VCT-1",  "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",  "Lobby",    "TILE-1", "CB-1", "WC-1", "ACT-1",   "10'-0\""],
            ["103",  "Storage",  "SC",     "RB-1", "PT-1", "EXPOSED", "12'-0\""],
        ],
        name="happy.pdf",
    )
    result = extract_finish_schedule(pdf, 0)

    assert isinstance(result, FinishScheduleResult)
    assert result.pages == [0]
    nums = [r.room_number for r in result.rooms]
    assert nums == ["101", "102", "103"]

    by_num = {r.room_number: r for r in result.rooms}
    assert by_num["101"].room_name == "Office"
    assert by_num["101"].floor_finish == "VCT-1"
    assert by_num["101"].base_finish == "RB-1"
    assert by_num["101"].ceiling_finish == "ACT-1"
    assert by_num["101"].wall_finishes == {"ALL": "PT-1"}
    assert by_num["101"].ceiling_height_ft == pytest.approx(9.0)

    assert by_num["102"].floor_finish == "TILE-1"
    assert by_num["102"].wall_finishes == {"ALL": "WC-1"}
    assert by_num["102"].ceiling_height_ft == pytest.approx(10.0)

    assert by_num["103"].floor_finish == "SC"
    assert by_num["103"].ceiling_finish == "EXPOSED"

    assert result.confidence > 0.6
    assert "ROOM" in result.raw_table_text


def test_extract_finish_schedule_compass_wall_columns(tmp_path: Path) -> None:
    """Schedules that break wall finishes into N/S/E/W columns."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "N",    "S",    "E",    "W",    "CEILING"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "PT-1", "WC-1", "PT-1", "ACT-1"],
            ["102",  "Lobby",  "TILE-1","CB-1", "PT-2", "PT-2", "PT-2", "PT-2", "ACT-1"],
        ],
        cell_size=(70.0, 24.0),
        name="compass.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    by_num = {r.room_number: r for r in result.rooms}
    assert by_num["101"].wall_finishes == {"N": "PT-1", "S": "PT-1",
                                              "E": "WC-1", "W": "PT-1"}
    assert by_num["102"].wall_finishes == {"N": "PT-2", "S": "PT-2",
                                              "E": "PT-2", "W": "PT-2"}


def test_extract_finish_schedule_missing_cells(tmp_path: Path) -> None:
    """Empty cells must yield ``None`` / empty dict without breaking the row."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME", "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",  "Hall", "VCT-1", "",     "",     "ACT-1"],
        ],
        name="missing.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert len(result.rooms) == 1
    r = result.rooms[0]
    assert r.room_number == "101"
    assert r.floor_finish == "VCT-1"
    assert r.base_finish is None
    assert r.wall_finishes == {}
    assert r.ceiling_finish == "ACT-1"


def test_extract_finish_schedule_empty_page(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN"],
        body_lines=["No tables here, just prose."],
        name="empty.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert result.rooms == []
    assert result.pages == []
    assert result.confidence == 0.0


def test_extract_finish_schedule_preserves_raw_cells(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING", "REMARKS"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1",   "see note 3"],
        ],
        name="raw.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert len(result.rooms) == 1
    r = result.rooms[0]
    assert r.raw_cells["ROOM"] == "101"
    assert r.raw_cells["FLOOR"] == "VCT-1"
    assert r.raw_cells["REMARKS"] == "see note 3"
    assert r.remarks == "see note 3"


def test_extract_finish_schedule_ceiling_height_decimal(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING", "HEIGHT"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1",   "9.5"],
        ],
        name="height_dec.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert result.rooms[0].ceiling_height_ft == pytest.approx(9.5)


def test_extract_finish_schedule_ceiling_height_feet_inches(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING", "HEIGHT"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-6\""],
        ],
        name="height_ftin.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert result.rooms[0].ceiling_height_ft == pytest.approx(9.5)


def test_extract_finish_schedule_skips_pure_door_table(tmp_path: Path) -> None:
    """A door-only table on the same page must not be mistaken for finish."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
        name="door_only_extract.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert result.rooms == []


def test_extract_finish_schedule_alphanumeric_room_numbers(tmp_path: Path) -> None:
    """Room numbers like ``M101`` (mezzanine 101) parse correctly."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM",  "NAME",       "FLOOR", "BASE", "WALL", "CEILING"],
            ["M101",  "Mez Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
            ["B101",  "Basement",   "SC",    "RB-1", "PT-1", "EXPOSED"],
        ],
        name="alphanumeric.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    nums = {r.room_number for r in result.rooms}
    assert "M101" in nums
    assert "B101" in nums


# ---------------------------------------------------------------------------
# Discriminator vs door + window precedence
# ---------------------------------------------------------------------------


def test_discriminator_finish_skipped_when_door_present(tmp_path: Path) -> None:
    """A page with both a door schedule and a finish schedule: door wins."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE", "(see also FINISH SCHEDULE below)"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
        name="door_plus_finish_phrase.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.door_schedule is not None
    assert len(result.door_schedule.doors) == 1
    # Door-precedence: finish must be None even though the phrase fired.
    assert result.finish_schedule is None


def test_discriminator_finish_skipped_when_window_present(tmp_path: Path) -> None:
    """A page with both a window schedule and the finish phrase: window wins."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE", "(see also FINISH SCHEDULE below)"],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
        ],
        name="window_plus_finish_phrase.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.window_schedule is not None
    assert len(result.window_schedule.windows) == 1
    # Window-precedence: finish must be None even though the phrase fired.
    assert result.finish_schedule is None


def test_discriminator_three_page_pdf_each_extractor_isolated(tmp_path: Path) -> None:
    """3-page PDF: page 0 door, page 1 window, page 2 finish. Each fires only on its page."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["DOOR SCHEDULE", "SHEET A0.1"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
    )
    _add_page(
        doc,
        title_lines=["WINDOW SCHEDULE", "SHEET A0.2"],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
        ],
    )
    _add_page(
        doc,
        title_lines=["ROOM FINISH SCHEDULE", "SHEET A0.3"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
            ["102",  "Lobby",  "TILE-1","CB-1", "WC-1", "ACT-1"],
        ],
    )
    out = tmp_path / "three_page.pdf"
    doc.save(out)
    doc.close()

    results = prepass_drawing_pdf(out)
    assert len(results) == 3
    p0, p1, p2 = results

    # Door page: only door fires.
    assert p0.door_schedule is not None and len(p0.door_schedule.doors) == 1
    assert p0.window_schedule is None
    assert p0.finish_schedule is None

    # Window page: only window fires.
    assert p1.door_schedule is None
    assert p1.window_schedule is not None and len(p1.window_schedule.windows) == 1
    assert p1.finish_schedule is None

    # Finish page: only finish fires.
    assert p2.door_schedule is None
    assert p2.window_schedule is None
    assert p2.finish_schedule is not None
    nums = {r.room_number for r in p2.finish_schedule.rooms}
    assert nums == {"101", "102"}


# ---------------------------------------------------------------------------
# Integration with the existing drawing pre-pass
# ---------------------------------------------------------------------------


def test_integration_with_drawing_prepass(tmp_path: Path) -> None:
    """``prepass_drawing_page`` exposes the finish-schedule extraction."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PROJECT NAME: T4 Test",
            "SHEET NO: A0.3",
            'SCALE: 1/4" = 1\'-0"',
            "ROOM FINISH SCHEDULE",
        ],
        table=[
            ["ROOM", "NAME",     "FLOOR", "BASE", "WALL", "CEILING", "HEIGHT"],
            ["101",  "Office",   "VCT-1", "RB-1", "PT-1", "ACT-1",   "9'-0\""],
            ["102",  "Lobby",    "TILE-1","CB-1", "PT-2", "ACT-1",   "10'-0\""],
            ["103",  "Restroom", "TILE-1","CB-1", "TILE-1","ACT-1",  "9'-0\""],
        ],
        name="integration.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.finish_schedule is not None
    room_nums = [r.room_number for r in result.finish_schedule.rooms]
    assert set(room_nums) == {"101", "102", "103"}
    assert result.finish_schedule.confidence > 0.0

    # Schema bridge round-trip.
    from core.extraction.drawing_prepass import to_schema as prepass_to_schema
    pyd = prepass_to_schema(result)
    assert pyd.finish_schedule is not None
    assert [r.room_number for r in pyd.finish_schedule.rooms] == room_nums


def test_extract_from_page_directly(tmp_path: Path) -> None:
    """``extract_finish_schedule_from_page`` accepts a live ``fitz.Page``
    and populates ``pages`` to ``[page_index]`` when records are found."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
            ["102",  "Lobby",  "TILE-1","CB-1", "PT-2", "ACT-1"],
        ],
        name="direct.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_finish_schedule_from_page(doc[0], page_index=7)
    assert result.pages == [7]
    assert all(r.source_page == 7 for r in result.rooms)


def test_extract_finish_schedule_out_of_range_raises(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE"],
        table=[
            ["ROOM", "NAME",   "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",  "Office", "VCT-1", "RB-1", "PT-1", "ACT-1"],
        ],
        name="oor.pdf",
    )
    with pytest.raises(IndexError):
        extract_finish_schedule(pdf, 99)


def test_record_attached_with_phrase_only_when_table_unavailable(tmp_path: Path) -> None:
    """Phrase fires but no table is detected → result empty (no fabricated rows)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FINISH SCHEDULE", "See attached spreadsheet"],
        body_lines=["No table on this sheet -- spreadsheet only."],
        name="phrase_only.pdf",
    )
    result = extract_finish_schedule(pdf, 0)
    assert result.rooms == []
