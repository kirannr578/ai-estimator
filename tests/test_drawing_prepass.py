"""Tests for the deterministic drawing pre-pass (F3).

Every test builds a synthetic 1-page PDF on disk with `fitz` (PyMuPDF) so
we don't need any binary fixtures checked into the repo.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import (
    CONFIDENCE_THRESHOLD,
    _extract_dimensions,
    _extract_title_block,
    _parse_scale_factor,
    prepass_drawing_page,
    prepass_drawing_pdf,
)


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _build_title_block_pdf(
    tmp_path: Path,
    title_block_lines: list[str],
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    name: str = "test.pdf",
) -> Path:
    """Create a 1-page PDF with the given title-block + optional body + table.

    Title-block lines are placed in the bottom-right corner of a US-Letter
    landscape page. The optional `table` is drawn as a real grid using
    `draw_line` + `insert_text` so PyMuPDF's `find_tables()` picks it up.
    """
    doc = fitz.open()
    # 11"x8.5" landscape Letter at 72 DPI = 792x612 points.
    page = doc.new_page(width=792, height=612)

    if body_lines:
        y = 60.0
        for line in body_lines:
            page.insert_text((40, y), line, fontsize=11)
            y += 16

    if table:
        # Render a real grid so find_tables() detects it.
        n_rows = len(table)
        n_cols = max(len(r) for r in table)
        x0, y0 = 40.0, 300.0
        cell_w, cell_h = 110.0, 22.0
        x1 = x0 + cell_w * n_cols
        y1 = y0 + cell_h * n_rows
        for i in range(n_rows + 1):
            page.draw_line((x0, y0 + i * cell_h), (x1, y0 + i * cell_h))
        for j in range(n_cols + 1):
            page.draw_line((x0 + j * cell_w, y0), (x0 + j * cell_w, y1))
        for i, row in enumerate(table):
            for j, val in enumerate(row):
                page.insert_text(
                    (x0 + j * cell_w + 5, y0 + i * cell_h + 15),
                    str(val), fontsize=9,
                )

    # Title block bottom-right.
    tb_x = 520.0
    tb_y = 530.0
    for line in title_block_lines:
        page.insert_text((tb_x, tb_y), line, fontsize=10)
        tb_y += 14

    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# End-to-end happy path
# ---------------------------------------------------------------------------


def test_prepass_extracts_title_block_dimensions_and_door_schedule(tmp_path: Path) -> None:
    pdf = _build_title_block_pdf(
        tmp_path,
        title_block_lines=[
            "PROJECT NAME: Test Building",
            "PROJECT NO: 2026-001",
            "SHEET NO: A101",
            "SHEET TITLE: First Floor Plan",
            'SCALE: 1/4" = 1\'-0"',
            "DATE: 2026-05-22",
        ],
        body_lines=[
            "ROOM A WALL LENGTH: 10'-6\"",
            "ROOM B WIDTH: 2.5 m",
            "OPENING HEIGHT: 8 1/2\"",
            "CORRIDOR LENGTH: 24'-0\"",
            "STAIR RISER: 7 3/4\"",
            "STAIR TREAD: 11\"",
        ],
        table=[
            ["MARK", "DOOR TYPE", "WIDTH", "HEIGHT", "HARDWARE"],
            ["101A", "SC HM",  "3'-0\"", "7'-0\"", "HW-1"],
            ["101B", "SC HM",  "3'-0\"", "7'-0\"", "HW-1"],
            ["102",  "WD",     "2'-8\"", "6'-8\"", "HW-2"],
        ],
        name="happy.pdf",
    )
    result = prepass_drawing_page(pdf, 0)

    tb = result.title_block
    assert tb.project_name == "Test Building"
    assert tb.project_number == "2026-001"
    assert tb.sheet_number == "A101"
    assert tb.discipline == "Architectural"
    assert tb.scale and "1/4" in tb.scale
    assert tb.scale_factor is not None
    assert abs(tb.scale_factor - (0.25 / 12.0)) < 1e-6

    # Dimensions: should pick up 10'-6", 2.5 m, 8 1/2", 24'-0", 7 3/4", 11"
    # plus the dimensions inside the schedule cells. So we expect ≥ 5.
    assert len(result.dimensions) >= 5
    kinds = {d.kind for d in result.dimensions}
    assert "feet-inches" in kinds
    assert "metric" in kinds

    # Door schedule was detected.
    door_scheds = [s for s in result.schedules if s.kind == "door"]
    assert door_scheds, f"expected a door schedule, got: {[s.kind for s in result.schedules]}"
    assert len(door_scheds[0].rows) >= 2

    assert result.confidence >= CONFIDENCE_THRESHOLD


# ---------------------------------------------------------------------------
# Discipline inference
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "sheet_no, expected",
    [
        ("S301", "Structural"),
        ("A101", "Architectural"),
        ("M201", "Mechanical"),
        ("E101", "Electrical"),
        ("P401", "Plumbing"),
        ("C100", "Civil"),
        ("L501", "Landscape"),
        ("I201", "Interior"),
        ("FP301", "Fire Protection"),
    ],
)
def test_discipline_inferred_from_sheet_number(tmp_path: Path, sheet_no: str, expected: str) -> None:
    pdf = _build_title_block_pdf(
        tmp_path,
        title_block_lines=[
            "PROJECT NAME: Discipline Test",
            f"SHEET NO: {sheet_no}",
            'SCALE: 1/8" = 1\'-0"',
        ],
        name=f"disc_{sheet_no}.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.title_block.sheet_number == sheet_no
    assert result.title_block.discipline == expected


# ---------------------------------------------------------------------------
# Scale parsing (table-driven, no PDF needed)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "scale, expected",
    [
        ('1/4" = 1\'-0"',  0.25 / 12.0),
        ('1/8" = 1\'-0"',  0.125 / 12.0),
        ('3/16" = 1\'-0"', (3.0 / 16.0) / 12.0),
        ('1" = 10\'',      1.0 / 120.0),
        ('1:50',           1.0 / 50.0),
        ('1:100',          1.0 / 100.0),
    ],
)
def test_scale_factor_parsing(scale: str, expected: float) -> None:
    got = _parse_scale_factor(scale)
    assert got is not None
    assert abs(got - expected) < 1e-6


def test_scale_factor_returns_none_for_garbage() -> None:
    assert _parse_scale_factor("NOT A SCALE") is None
    assert _parse_scale_factor("") is None


# ---------------------------------------------------------------------------
# Feet-inches dimension parsing (table-driven)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected_inches, expected_kind",
    [
        ("10'-6\"",       10 * 12 + 6,      "feet-inches"),
        ("10' - 6 1/2\"", 10 * 12 + 6.5,    "feet-inches"),
        ("10'-6 1/2\"",   10 * 12 + 6.5,    "feet-inches"),
        ("6 1/2\"",       6.5,              "feet-inches"),
        ("8 1/2\"",       8.5,              "feet-inches"),
        ("11\"",          11,               "feet-inches"),
        ("10.5'",         10.5 * 12,        "decimal-feet"),
        ("250 mm",        250 / 25.4,       "metric"),
        ("2.5 m",         2.5 * 39.3700787, "metric"),
        ("100cm",         100 / 2.54,       "metric"),
    ],
)
def test_dimension_parsing(text: str, expected_inches: float, expected_kind: str) -> None:
    dims = _extract_dimensions(text)
    assert dims, f"no dimensions extracted from {text!r}"
    matching = [d for d in dims if d.kind == expected_kind]
    assert matching, (
        f"expected kind {expected_kind!r} from {text!r}, got "
        f"{[(d.raw_text, d.kind) for d in dims]}"
    )
    assert abs(matching[0].inches - expected_inches) < 1e-3


def test_dimension_filters_spurious_values() -> None:
    # 0" is filtered (callouts), 99999" is filtered (OCR garbage).
    dims = _extract_dimensions('0"  99999"  6"')
    inches = [d.inches for d in dims]
    assert 0.0 not in inches
    assert 99999.0 not in inches
    assert 6.0 in inches


# ---------------------------------------------------------------------------
# No-table page → confidence below threshold
# ---------------------------------------------------------------------------


def test_prose_only_page_has_low_confidence(tmp_path: Path) -> None:
    pdf = _build_title_block_pdf(
        tmp_path,
        title_block_lines=[],   # no title block
        body_lines=[
            "This page is just running prose with no labels and no schedule.",
            "It mentions a wall and a door but has no dimensions or table.",
            "The deterministic pre-pass should not be confident enough to skip "
            "the LLM call.",
        ],
        name="prose.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.confidence < CONFIDENCE_THRESHOLD
    assert result.schedules == []


# ---------------------------------------------------------------------------
# Whole-PDF entry point
# ---------------------------------------------------------------------------


def test_prepass_drawing_pdf_iterates_all_pages(tmp_path: Path) -> None:
    """The PDF-level entry point should return one result per page."""
    doc = fitz.open()
    for i in range(3):
        page = doc.new_page(width=612, height=792)
        page.insert_text((40, 60), f"PROJECT NAME: Project {i}", fontsize=11)
        page.insert_text((40, 80), f"SHEET NO: A10{i}", fontsize=11)
        page.insert_text((40, 100), 'SCALE: 1/4" = 1\'-0"', fontsize=11)
    pdf = tmp_path / "multi.pdf"
    doc.save(pdf)
    doc.close()

    results = prepass_drawing_pdf(pdf)
    assert len(results) == 3
    sheet_numbers = [r.title_block.sheet_number for r in results]
    assert sheet_numbers == ["A100", "A101", "A102"]


# ---------------------------------------------------------------------------
# Direct title-block extractor (no PDF needed)
# ---------------------------------------------------------------------------


def test_title_block_extractor_direct() -> None:
    text = (
        "PROJECT NAME: Carr EFA Dressing Room Renovation\n"
        "PROJECT NO: 26-007\n"
        "SHEET NO: S301\n"
        "SHEET TITLE: Foundation Plan\n"
        'SCALE: 1/4" = 1\'-0"\n'
        "DATE: 6/22/2026\n"
        "REVISION: 2\n"
        "DRAWN BY: JKR\n"
        "CHECKED BY: BPM\n"
    )
    tb, issues = _extract_title_block(text)
    assert tb.project_name == "Carr EFA Dressing Room Renovation"
    assert tb.project_number == "26-007"
    assert tb.sheet_number == "S301"
    assert tb.discipline == "Structural"   # from sheet-number prefix
    assert tb.sheet_title == "Foundation Plan"
    assert tb.scale_factor is not None and tb.scale_factor > 0
    assert tb.date == "6/22/2026"
    assert tb.revision == "2"
    assert tb.drawn_by == "JKR"
    assert tb.checked_by == "BPM"
    assert issues == []
