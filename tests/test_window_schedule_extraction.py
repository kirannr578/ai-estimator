"""Tests for the window-schedule pre-pass (Phase T2.5).

Every test builds a synthetic 1-page PDF on disk with `fitz` (PyMuPDF) so
we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_door_schedule_extraction`; the discriminator
test on the bottom asserts that a multi-page PDF with both a door
schedule (page 0) and a window schedule (page 1) only fires the window
extractor on the window page, never the door page.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import prepass_drawing_page, prepass_drawing_pdf
from core.extraction.window_schedule import (
    WindowScheduleResult,
    detect_window_schedule,
    extract_window_schedule,
    extract_window_schedule_from_page,
)


# ---------------------------------------------------------------------------
# Fixture builder (kept local — mirrors the helper in test_door_schedule_extraction)
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 200.0),
    cell_size: tuple[float, float] = (90.0, 24.0),
) -> None:
    """Append a 1-page PDF with optional title text, body text, and a grid table."""
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
# Detection heuristic
# ---------------------------------------------------------------------------


def test_detect_window_schedule_by_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE", "Project: Example"],
        name="phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_window_schedule(doc[0]) is True


def test_detect_window_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["Sheet A0.2"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM-S", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "ALUM-S", "3'-0\"", "5'-0\"", "INSUL",   "CASEMENT"],
        ],
        name="header.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_window_schedule(doc[0]) is True


def test_detect_window_schedule_negative_floor_plan(tmp_path: Path) -> None:
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
        assert detect_window_schedule(doc[0]) is False


def test_detect_window_schedule_rejects_bare_door_schedule(tmp_path: Path) -> None:
    """A door-only schedule (no window-specific columns) must NOT detect as window."""
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
        # NOTE: ``detect_window_schedule`` is permissive on the phrase
        # ("WINDOW SCHEDULE" in text); on a door-only page the phrase is
        # absent and the header heuristic must fail.
        assert detect_window_schedule(doc[0]) is False


# ---------------------------------------------------------------------------
# End-to-end extraction
# ---------------------------------------------------------------------------


def test_extract_window_schedule_parses_window_records(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",   "WIDTH",  "HEIGHT", "GLAZING", "OPERATION", "FRAME"],
            ["W1",   "ALUM-S", "3'-0\"", "5'-0\"", "INSUL",   "FIXED",     "ALUM"],
            ["W1A",  "ALUM-S", "3'-0\"", "5'-0\"", "INSUL",   "FIXED",     "ALUM"],
            ["W2",   "VINYL",  "2'-8\"", "4'-8\"", "LOW-E",   "DH",        "VINYL"],
            ["W3",   "WOOD",   "4'-0\"", "5'-0\"", "CLEAR",   "CASEMENT",  "WOOD"],
        ],
        name="happy.pdf",
    )
    result = extract_window_schedule(pdf, 0)

    assert isinstance(result, WindowScheduleResult)
    assert result.pages == [0]
    marks = [w.mark for w in result.windows]
    assert marks == ["W1", "W1A", "W2", "W3"]

    by_mark = {w.mark: w for w in result.windows}
    assert by_mark["W1"].type == "ALUM-S"
    assert by_mark["W1"].width_in == pytest.approx(36.0)
    assert by_mark["W1"].height_in == pytest.approx(60.0)
    assert by_mark["W1"].glazing == "INSUL"
    assert by_mark["W1"].operation == "FIXED"
    assert by_mark["W1"].frame == "ALUM"

    assert by_mark["W2"].width_in == pytest.approx(32.0)
    assert by_mark["W2"].height_in == pytest.approx(56.0)
    assert by_mark["W2"].glazing == "LOW-E"

    assert by_mark["W3"].type == "WOOD"
    assert by_mark["W3"].width_in == pytest.approx(48.0)

    assert result.confidence > 0.6
    assert "MARK" in result.raw_table_text


def test_extract_window_schedule_combined_size_column(tmp_path: Path) -> None:
    """SIZE: '3'-0" x 5'-0"' style cells split into width + height."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",   "SIZE",            "GLAZING"],
            ["W1",   "ALUM",   "3'-0\" x 5'-0\"", "INSUL"],
            ["W2",   "VINYL",  "2'-8\" x 4'-8\"", "LOW-E"],
        ],
        name="size_col.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w for w in result.windows}
    assert by_mark["W1"].width_in == pytest.approx(36.0)
    assert by_mark["W1"].height_in == pytest.approx(60.0)
    assert by_mark["W2"].width_in == pytest.approx(32.0)
    assert by_mark["W2"].height_in == pytest.approx(56.0)


def test_extract_window_schedule_captures_sill_height(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",   "WIDTH",  "HEIGHT", "SILL",   "GLAZING"],
            ["W1",   "ALUM",   "3'-0\"", "5'-0\"", "2'-6\"", "INSUL"],
            ["W2",   "VINYL",  "2'-8\"", "4'-8\"", "3'-0\"", "LOW-E"],
        ],
        name="sill.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w for w in result.windows}
    assert by_mark["W1"].sill_height_in == pytest.approx(30.0)
    assert by_mark["W2"].sill_height_in == pytest.approx(36.0)
    assert by_mark["W1"].sill_height_raw == "2'-6\""


def test_extract_window_schedule_captures_u_factor_and_shgc(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",   "WIDTH",  "HEIGHT", "GLAZING", "U-FACTOR", "SHGC"],
            ["W1",   "ALUM",   "3'-0\"", "5'-0\"", "INSUL",   "0.32",     "0.28"],
            ["W2",   "VINYL",  "2'-8\"", "4'-8\"", "LOW-E",   "0.28",     "0.25"],
        ],
        cell_size=(70.0, 24.0),  # narrower cells -- 7 columns fit in 792pt page
        name="thermal.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w for w in result.windows}
    assert by_mark["W1"].u_factor == pytest.approx(0.32)
    assert by_mark["W1"].shgc == pytest.approx(0.28)
    assert by_mark["W2"].u_factor == pytest.approx(0.28)


def test_extract_window_schedule_empty_page(tmp_path: Path) -> None:
    """A page with no schedule yields an empty result with confidence 0.0."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN"],
        body_lines=["No tables here, just prose."],
        name="empty.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert result.windows == []
    assert result.pages == []
    assert result.confidence == 0.0


def test_extract_window_schedule_preserves_raw_cells(tmp_path: Path) -> None:
    """``raw_cells`` should capture every populated column for audit."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",   "WIDTH",  "HEIGHT", "GLAZING", "REMARKS"],
            ["W1",   "ALUM",   "3'-0\"", "5'-0\"", "INSUL",   "Tempered"],
        ],
        name="raw.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert len(result.windows) == 1
    w = result.windows[0]
    # Every populated header lands in raw_cells with its original column label.
    assert w.raw_cells["MARK"] == "W1"
    assert w.raw_cells["TYPE"] == "ALUM"
    assert w.raw_cells["GLAZING"] == "INSUL"
    assert w.raw_cells["REMARKS"] == "Tempered"
    assert w.remarks == "Tempered"


def test_extract_window_schedule_skips_pure_door_table(tmp_path: Path) -> None:
    """A door-only table on the same page must not be mistaken for a window."""
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
    # The window detector header heuristic requires a window-specific
    # column; a door-only table has none. The phrase trigger ("WINDOW
    # SCHEDULE") is also absent on this page.
    result = extract_window_schedule(pdf, 0)
    assert result.windows == []


# ---------------------------------------------------------------------------
# Door-vs-window discriminator
# ---------------------------------------------------------------------------


def test_discriminator_only_window_page_yields_window_extraction(tmp_path: Path) -> None:
    """A 2-page PDF with door schedule on p0 and window schedule on p1.

    Page 0 (door schedule) → ``door_schedule`` populated, ``window_schedule``
    stays None (door-precedence rule).
    Page 1 (window schedule) → ``window_schedule`` populated, no doors.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["DOOR SCHEDULE", "SHEET A0.1"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",  "WD",  "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
    )
    _add_page(
        doc,
        title_lines=["WINDOW SCHEDULE", "SHEET A0.2"],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "VINYL", "2'-8\"", "4'-8\"", "LOW-E",   "DH"],
        ],
    )
    out = tmp_path / "discriminator.pdf"
    doc.save(out)
    doc.close()

    results = prepass_drawing_pdf(out)
    assert len(results) == 2

    p0, p1 = results
    # Door page: door extraction fires, window extraction is suppressed
    # by the door-precedence rule (window_schedule must be None).
    assert p0.door_schedule is not None
    assert len(p0.door_schedule.doors) == 2
    assert p0.window_schedule is None

    # Window page: window extraction fires; door schedule must be None.
    assert p1.window_schedule is not None
    marks = {w.mark for w in p1.window_schedule.windows}
    assert marks == {"W1", "W2"}
    assert p1.door_schedule is None


def test_discriminator_door_precedence_when_both_phrases_present(tmp_path: Path) -> None:
    """A single page with both ``DOOR SCHEDULE`` and ``WINDOW SCHEDULE`` text but
    only door-shaped table rows: door wins, window is skipped."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE", "(see also WINDOW SCHEDULE below)"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
        name="both_phrases.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.door_schedule is not None
    assert len(result.door_schedule.doors) == 1
    # Door-precedence rule: window extraction is suppressed even though
    # the phrase trigger fired.
    assert result.window_schedule is None


# ---------------------------------------------------------------------------
# Integration with the existing drawing pre-pass
# ---------------------------------------------------------------------------


def test_integration_with_drawing_prepass(tmp_path: Path) -> None:
    """`prepass_drawing_page` exposes the window-schedule extraction alongside
    the existing schedule rows without replacing them."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PROJECT NAME: T2.5 Test",
            "SHEET NO: A0.2",
            'SCALE: 1/4" = 1\'-0"',
            "WINDOW SCHEDULE",
        ],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W3",   "VINYL", "2'-8\"", "4'-8\"", "LOW-E",   "DH"],
        ],
        name="integration.pdf",
    )
    result = prepass_drawing_page(pdf, 0)

    # The new T2.5 typed result is attached on the prepass.
    assert result.window_schedule is not None
    window_marks = [w.mark for w in result.window_schedule.windows]
    assert set(window_marks) == {"W1", "W2", "W3"}
    assert result.window_schedule.confidence > 0.0

    # And the schema bridge round-trips it through the Pydantic models.
    from core.extraction.drawing_prepass import to_schema as prepass_to_schema
    pyd = prepass_to_schema(result)
    assert pyd.window_schedule is not None
    assert [w.mark for w in pyd.window_schedule.windows] == window_marks


def test_extract_from_page_directly(tmp_path: Path) -> None:
    """`extract_window_schedule_from_page` accepts a live `fitz.Page` and
    populates ``pages`` to ``[page_index]`` when records are found."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE",  "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
            ["W2",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="direct.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_window_schedule_from_page(doc[0], page_index=5)
    assert result.pages == [5]
    assert all(r.source_page == 5 for r in result.windows)


def test_extract_window_schedule_out_of_range_raises(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "GLAZING"],
            ["W1",   "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="oor.pdf",
    )
    with pytest.raises(IndexError):
        extract_window_schedule(pdf, 99)


def test_window_tag_regex_accepts_common_variants(tmp_path: Path) -> None:
    """The window-tag regex must accept ``W1``, ``W-01``, ``101``, and ``A``."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK",  "TYPE",  "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",    "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
            ["W-01",  "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
            ["101",   "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
            ["A",     "ALUM",  "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="tag_variants.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    marks = {w.mark for w in result.windows}
    assert {"W1", "W-01", "101", "A"} <= marks


def test_record_attached_with_phrase_only_when_table_unavailable(tmp_path: Path) -> None:
    """When the phrase fires but no table is detected, the result is empty
    (the extractor refuses to fabricate records)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE", "See attached spreadsheet"],
        body_lines=["No table on this sheet -- spreadsheet only."],
        name="phrase_only.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert result.windows == []


# ---------------------------------------------------------------------------
# Phase T5.1 — ``ROOM`` / ``RM`` / ``LOCATION`` column parsing
# ---------------------------------------------------------------------------


def test_window_schedule_parses_room_column(tmp_path: Path) -> None:
    """``ROOM`` header → records get ``room_number`` populated."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "GLAZING", "OPERATION"],
            ["W1",   "101",  "ALUM", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
            ["W2",   "102",  "ALUM", "3'-0\"", "5'-0\"", "INSUL",   "FIXED"],
        ],
        name="room_col.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w for w in result.windows}
    assert by_mark["W1"].room_number == "101"
    assert by_mark["W2"].room_number == "102"


def test_window_schedule_parses_rm_column(tmp_path: Path) -> None:
    """``RM`` header populates ``room_number`` without colliding with
    ``FRAME`` (word-level match only)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "RM",  "TYPE", "WIDTH",  "HEIGHT", "FRAME", "GLAZING"],
            ["W1",   "101", "ALUM", "3'-0\"", "5'-0\"", "ALUM",  "INSUL"],
        ],
        name="rm_col.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert result.windows[0].room_number == "101"
    assert result.windows[0].frame == "ALUM"


def test_window_schedule_parses_location_column(tmp_path: Path) -> None:
    """``LOCATION`` is the alternate convention some offices use."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "LOCATION", "TYPE", "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",   "201",      "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="location_col.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert result.windows[0].room_number == "201"


def test_window_schedule_without_room_column_returns_none(tmp_path: Path) -> None:
    """A window schedule with no ROOM / RM / LOCATION header → every
    record's ``room_number`` is ``None`` (typical: window schedules
    often omit this column)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",   "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
            ["W2",   "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="no_room.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert all(w.room_number is None for w in result.windows)


def test_window_schedule_alphanumeric_room_number(tmp_path: Path) -> None:
    """Alphanumeric room numbers (``"101A"``, ``"M-101"``) survive as strings."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "ROOM",  "TYPE", "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",   "101A",  "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
            ["W2",   "M-101", "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="alpha_room.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w.room_number for w in result.windows}
    assert by_mark["W1"] == "101A"
    assert by_mark["W2"] == "M-101"


def test_window_schedule_empty_room_cell_is_none(tmp_path: Path) -> None:
    """An empty ROOM cell on a per-row basis → that record's
    ``room_number`` is ``None`` rather than the empty string."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "ROOM", "TYPE", "WIDTH",  "HEIGHT", "GLAZING"],
            ["W1",   "101",  "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
            ["W2",   "",     "ALUM", "3'-0\"", "5'-0\"", "INSUL"],
        ],
        name="mixed_room.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    by_mark = {w.mark: w.room_number for w in result.windows}
    assert by_mark["W1"] == "101"
    assert by_mark["W2"] is None


def test_window_schedule_room_column_does_not_collide_with_frame(tmp_path: Path) -> None:
    """Regression: ``FRAME`` contains the substring ``RM`` — the room
    matcher must not falsely claim FRAME as the room column."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH",  "HEIGHT", "FRAME", "GLAZING"],
            ["W1",   "ALUM", "3'-0\"", "5'-0\"", "ALUM",  "INSUL"],
        ],
        name="frame_only.pdf",
    )
    result = extract_window_schedule(pdf, 0)
    assert result.windows[0].room_number is None
    assert result.windows[0].frame == "ALUM"
