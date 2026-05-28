"""Tests for the door-schedule pre-pass (Phase T1).

Every test builds a synthetic 1-page PDF on disk with `fitz` (PyMuPDF) so
we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_drawing_prepass`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.door_schedule import (
    DoorScheduleResult,
    detect_door_schedule,
    extract_door_schedule,
    extract_door_schedule_from_page,
    parse_dimension,
)
from core.extraction.drawing_prepass import prepass_drawing_page


# ---------------------------------------------------------------------------
# Fixture builder (kept local — mirrors the helper in test_drawing_prepass)
# ---------------------------------------------------------------------------


def _build_pdf(
    tmp_path: Path,
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 200.0),
    cell_size: tuple[float, float] = (90.0, 24.0),
    name: str = "test.pdf",
) -> Path:
    """Create a 1-page PDF with optional title text, body text, and a grid table.

    The table is drawn as a real grid (lines + cell text) so PyMuPDF's
    ``find_tables()`` reliably detects it.
    """
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)   # US-Letter landscape

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

    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# Detection heuristic
# ---------------------------------------------------------------------------


def test_detect_door_schedule_by_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE", "Project: Example"],
        name="phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_door_schedule(doc[0]) is True


def test_detect_door_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["Sheet A0.1"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101", "HM", "3'-0\"", "7'-0\"", "HM", "HW-1"],
            ["102", "WD", "3'-0\"", "7'-0\"", "HM", "HW-2"],
        ],
        name="header.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_door_schedule(doc[0]) is True


def test_detect_door_schedule_negative(tmp_path: Path) -> None:
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
        assert detect_door_schedule(doc[0]) is False


# ---------------------------------------------------------------------------
# Dimension parsing (no PDF needed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("3'0\"",        36.0),
        ("3'-0\"",       36.0),
        ("3' - 0\"",     36.0),
        ("3'",           36.0),
        ("3'-6\"",       42.0),
        ("3'-0 1/2\"",   36.5),
        ("36\"",         36.0),
        ("84\"",         84.0),
        ("3 ft 0 in",    36.0),
        ("3 ft",         36.0),
        ("3 feet 6 inches", 42.0),
    ],
)
def test_parse_dimension_happy_path(text: str, expected: float) -> None:
    got = parse_dimension(text)
    assert got is not None
    assert abs(got - expected) < 1e-3


@pytest.mark.parametrize(
    "text",
    ["", None, "abc", "3x6", "3 m", "tbd", "   "],
)
def test_parse_dimension_returns_none_for_garbage(text) -> None:
    assert parse_dimension(text) is None


# ---------------------------------------------------------------------------
# End-to-end extraction
# ---------------------------------------------------------------------------


def test_extract_door_schedule_parses_door_records(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE", "RATING"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1",     "20-min"],
            ["101A", "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1",     ""],
            ["102",  "WD",  "2'-8\"", "6'-8\"", "HM",   "HW-2",     ""],
            ["103",  "ALUM","6'-0\"", "7'-0\"", "ALUM", "HW-3",     ""],
        ],
        name="happy.pdf",
    )
    result = extract_door_schedule(pdf, 0)

    assert isinstance(result, DoorScheduleResult)
    assert result.pages == [0]
    marks = [d.mark for d in result.doors]
    assert marks == ["101", "101A", "102", "103"]

    by_mark = {d.mark: d for d in result.doors}
    assert by_mark["101"].type == "HM"
    assert by_mark["101"].width_in == pytest.approx(36.0)
    assert by_mark["101"].height_in == pytest.approx(84.0)
    assert by_mark["101"].hardware_set == "HW-1"
    assert by_mark["101"].fire_rating == "20-min"

    assert by_mark["102"].width_in == pytest.approx(32.0)
    assert by_mark["102"].height_in == pytest.approx(80.0)

    assert by_mark["103"].type == "ALUM"
    assert by_mark["103"].width_in == pytest.approx(72.0)

    assert result.confidence > 0.6
    assert "MARK" in result.raw_table_text


def test_extract_door_schedule_combined_size_column(tmp_path: Path) -> None:
    """SIZE: '3'-0" x 7'-0"' style cells split into width + height."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "SIZE",           "HARDWARE"],
            ["201",  "HM",  "3'-0\" x 7'-0\"", "HW-1"],
            ["202",  "WD",  "2'-8\" x 6'-8\"", "HW-2"],
        ],
        name="size_col.pdf",
    )
    result = extract_door_schedule(pdf, 0)
    by_mark = {d.mark: d for d in result.doors}
    assert by_mark["201"].width_in == pytest.approx(36.0)
    assert by_mark["201"].height_in == pytest.approx(84.0)
    assert by_mark["202"].width_in == pytest.approx(32.0)
    assert by_mark["202"].height_in == pytest.approx(80.0)


def test_extract_door_schedule_empty_page(tmp_path: Path) -> None:
    """A page with no schedule yields an empty result with confidence 0.0."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN"],
        body_lines=["No tables here, just prose."],
        name="empty.pdf",
    )
    result = extract_door_schedule(pdf, 0)
    assert result.doors == []
    assert result.pages == []
    assert result.confidence == 0.0


def test_extract_door_schedule_skips_non_door_tables(tmp_path: Path) -> None:
    """A window-schedule table on the same page must not be mistaken for doors."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE", "GLAZING", "WIDTH", "HEIGHT"],
            ["W1",   "ALUM", "INSUL",   "3'-0\"", "5'-0\""],
            ["W2",   "ALUM", "INSUL",   "3'-0\"", "5'-0\""],
        ],
        name="window.pdf",
    )
    result = extract_door_schedule(pdf, 0)
    # Window-only schedule lacks the DOOR/MARK+HARDWARE/FRAME combination
    # that the heuristic requires.
    assert result.doors == []


# ---------------------------------------------------------------------------
# Integration with the existing drawing pre-pass
# ---------------------------------------------------------------------------


def test_integration_with_drawing_prepass(tmp_path: Path) -> None:
    """`prepass_drawing_page` exposes the door-schedule extraction alongside
    the existing schedule rows without replacing them."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PROJECT NAME: T1 Test",
            "SHEET NO: A0.1",
            'SCALE: 1/4" = 1\'-0"',
            "DOOR SCHEDULE",
        ],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",  "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["103",  "WD",   "2'-8\"", "6'-8\"", "HM",   "HW-2"],
        ],
        name="integration.pdf",
    )
    result = prepass_drawing_page(pdf, 0)

    # Existing schedule extraction still fires.
    door_kinds = [s for s in result.schedules if s.kind == "door"]
    assert door_kinds, "existing prepass must still detect the door schedule"

    # The new T1 typed result is attached alongside, not replacing, it.
    assert result.door_schedule is not None
    door_marks = [d.mark for d in result.door_schedule.doors]
    assert set(door_marks) == {"101", "102", "103"}
    assert result.door_schedule.confidence > 0.0

    # And the schema bridge round-trips it through the Pydantic models.
    from core.extraction.drawing_prepass import to_schema as prepass_to_schema
    pyd = prepass_to_schema(result)
    assert pyd.door_schedule is not None
    assert [d.mark for d in pyd.door_schedule.doors] == door_marks


def test_extract_from_page_directly(tmp_path: Path) -> None:
    """`extract_door_schedule_from_page` accepts a live `fitz.Page` and
    populates ``pages`` to ``[page_index]`` when records are found."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HW-1"],
            ["102",  "HM",  "3'-0\"", "7'-0\"", "HW-1"],
        ],
        name="direct.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], page_index=7)
    assert result.pages == [7]
    assert all(r.source_page == 7 for r in result.doors)
