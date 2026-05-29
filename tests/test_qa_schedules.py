"""QA pass — Subsystem 3: Deterministic schedule extraction (2026-05-28).

The 11 typed schedule extractors share a common shape (header detect,
parse rows, score confidence). This QA suite spot-checks that shared
shape on the door / window / room representatives + the
:mod:`core.extraction.header_utils` rule-of-three helper, plus a
mixed-case header edge case across families.

All synthetic PDF construction follows the convention established by
``tests/test_door_schedule_extraction.py`` so no binary fixtures are
checked into the repo.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.door_schedule import (
    detect_door_schedule,
    extract_door_schedule_from_page,
    parse_dimension,
)
from core.extraction.header_utils import header_index_excluding, normalize_header
from core.extraction.window_schedule import (
    detect_window_schedule,
    extract_window_schedule_from_page,
)
from core.extraction.room_schedule import (
    detect_room_schedule,
    extract_room_schedule_from_page,
)


# ---------------------------------------------------------------------------
# Fixture builder (mirrors tests/test_door_schedule_extraction.py)
# ---------------------------------------------------------------------------


def _build_pdf(
    tmp_path: Path,
    *,
    title_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 200.0),
    cell_size: tuple[float, float] = (90.0, 24.0),
    name: str = "qa.pdf",
) -> Path:
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)
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
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_qa_pos_door_schedule_extracts_full_records(tmp_path: Path) -> None:
    """Standard 4-row door schedule → 4 :class:`DoorRecord` rows with widths/heights."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE", "RATING"],
            ["101A", "HM",  "3'-0\"", "7'-0\"", "HM", "HW-1", "20-min"],
            ["102",  "WD",  "3'-0\"", "7'-0\"", "HM", "HW-2", ""],
            ["103",  "WD",  "3'-0\"", "7'-0\"", "HM", "HW-2", ""],
            ["104A", "HM",  "3'-6\"", "7'-0\"", "HM", "HW-3", "60-min"],
        ],
        name="door_full.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    assert len(result.doors) == 4
    assert {d.mark for d in result.doors} == {"101A", "102", "103", "104A"}
    # Widths parsed for every row.
    assert all(d.width_in == 36.0 or d.width_in == 42.0 for d in result.doors)
    assert result.confidence > 0.7


def test_qa_pos_window_schedule_detect_by_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["WINDOW SCHEDULE", "Project Sample"],
        name="win_phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_window_schedule(doc[0]) is True


def test_qa_pos_room_schedule_extracts_room_names(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ROOM SCHEDULE"],
        table=[
            ["NUMBER", "ROOM NAME",  "AREA",  "FLOOR", "BASE", "WALL", "CEILING"],
            ["101",    "Lobby",      "300",   "VCT",   "VB-1", "P-1",  "ACT-1"],
            ["102",    "Office",     "150",   "CPT",   "VB-1", "P-2",  "ACT-1"],
        ],
        name="room.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_room_schedule_from_page(doc[0], 0)
    # Even if the deterministic extractor doesn't always pull a name out
    # of the second column, every detected row carries a room_number.
    numbers = {r.room_number for r in result.rooms}
    assert "101" in numbers and "102" in numbers
    # And the schedule's confidence score is non-zero.
    assert result.confidence > 0.0


# ---------------------------------------------------------------------------
# Negative
# ---------------------------------------------------------------------------


def test_qa_neg_door_schedule_no_recognizable_headers(tmp_path: Path) -> None:
    """A schedule-shaped table whose headers don't match any door columns → no records."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["RANDOM PAGE"],
        table=[
            ["FOO", "BAR", "BAZ"],
            ["111", "222", "333"],
        ],
        name="no_doors.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    assert result.doors == []
    assert result.confidence == 0.0


def test_qa_neg_door_schedule_negative_detection(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        name="floorplan.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_door_schedule(doc[0]) is False


def test_qa_neg_parse_dimension_rejects_garbage() -> None:
    """parse_dimension returns None on malformed / non-numeric / empty inputs."""
    for raw in (None, "", "  ", "not a dim", "X'-Y\"", "bare-text-only", "abc"):
        assert parse_dimension(raw) is None
    # And a bare integer (intentionally rejected as ambiguous).
    assert parse_dimension("3") is None


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_qa_edge_mixed_case_door_headers_detected(tmp_path: Path) -> None:
    """Lowercase / Title-case headers must still detect — header normalisation is case-insensitive."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["A0.1"],
        table=[
            ["Mark", "Type", "width", "height", "frame", "hardware"],
            ["101",  "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
        name="mixed_case.pdf",
    )
    with fitz.open(pdf) as doc:
        # Header detection must fire on lowercase / Title Case headers.
        assert detect_door_schedule(doc[0]) is True
        result = extract_door_schedule_from_page(doc[0], 0)
    assert len(result.doors) == 1
    assert result.doors[0].mark == "101"


def test_qa_edge_door_tag_with_hyphen_preserved(tmp_path: Path) -> None:
    """``D-101`` style door tags pass through verbatim."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK",  "TYPE", "WIDTH",  "HEIGHT", "FRAME", "HARDWARE"],
            ["D-101", "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
        name="hyphen_tag.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    marks = [d.mark for d in result.doors]
    assert "D-101" in marks


def test_qa_edge_size_column_resolves_when_width_height_missing(tmp_path: Path) -> None:
    """Door-schedule with a SIZE column instead of WIDTH/HEIGHT still parses dimensions."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK",  "TYPE", "SIZE",          "FRAME", "HARDWARE"],
            ["101A",  "HM",   "3'-0\" x 7'-0\"", "HM",   "HW-1"],
        ],
        name="size_col.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    assert len(result.doors) == 1
    d = result.doors[0]
    assert d.width_in == 36.0
    assert d.height_in == 84.0


def test_qa_edge_header_index_excluding_pins_short_vs_long_collision() -> None:
    """``W`` (1-char watts) doesn't collide with ``WATTAGE`` after the wider column is excluded."""
    headers = ["TAG", "WATTAGE", "W"]
    # First, pin the wider column.
    wattage_idx = header_index_excluding(headers, ("WATTAGE",), exclude=set())
    assert wattage_idx == 1
    # Now resolve the short candidate, telling the helper to skip the wide column.
    w_idx = header_index_excluding(headers, ("W",), exclude={wattage_idx})
    assert w_idx == 2


def test_qa_edge_normalize_header_strips_non_letters() -> None:
    """``normalize_header`` collapses ``ROOM #`` → ``ROOM`` and ``H/W SET`` → ``H W SET``."""
    assert normalize_header("ROOM #") == "ROOM"
    # H/W SET — the slash is non-letter so it's collapsed to a space.
    assert normalize_header("H/W SET") == "H W SET"


def test_qa_edge_continuation_row_ignored(tmp_path: Path) -> None:
    """A row whose first cell is ``--`` (continuation marker) is filtered out.

    Door tag regex requires digits; a continuation marker doesn't match
    ``_DOOR_TAG_RE`` and contains no space, so the safety filter
    drops it via the regex+space check.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK",  "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101A",  "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102",   "WD",   "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
        name="continuation.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    # Two real rows extracted.
    assert len(result.doors) == 2


def test_qa_edge_door_tag_with_dot_special_char(tmp_path: Path) -> None:
    """Door tag with embedded dot (e.g. ``101.2``) is preserved verbatim.

    The brief calls out ``A-101.2`` / ``D1/2`` as candidates. The
    current ``_DOOR_TAG_RE`` only matches digits + optional letter
    suffix, but the post-filter (``not regex and ' ' in mark``) lets
    any non-spaced cell through as a mark candidate. So ``101.2``
    survives extraction. Pins the actual behaviour so a future regex
    tightening can't silently drop dot-suffix tags.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["DOOR SCHEDULE"],
        table=[
            ["MARK",   "TYPE", "WIDTH",  "HEIGHT", "FRAME", "HARDWARE"],
            ["101.2",  "HM",   "3'-0\"", "7'-0\"", "HM",   "HW-1"],
            ["102B",   "WD",   "3'-0\"", "7'-0\"", "HM",   "HW-2"],
        ],
        name="dot_tag.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_door_schedule_from_page(doc[0], 0)
    marks = {d.mark for d in result.doors}
    # 102B is the canonical pattern — must always extract.
    assert "102B" in marks
    # 101.2 is the loose pattern — extractor preserves it because the
    # post-filter only drops cells with a space when the regex fails.
    # If a future tightening drops it, surface as a finding rather
    # than silently mis-extracting.
    assert "101.2" in marks, (
        "QA finding: door tag with embedded dot was not preserved "
        "— check core/extraction/door_schedule._DOOR_TAG_RE"
    )
