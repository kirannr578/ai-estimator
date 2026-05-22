"""Integration test: high-confidence pre-pass should bypass the LLM call.

When `prepass_drawing_page` produces a result whose confidence ≥
`CONFIDENCE_THRESHOLD`, `extract_sheet` must build the `SheetExtraction`
straight from the deterministic snapshot and skip the vision-LLM call
entirely. This guards against the silent regression where someone wires
the LLM call back in unconditionally.
"""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import fitz

from core.extractors import extract_sheet
from core.schemas import Discipline, Sheet, SheetType


class _LLMStub:
    """Tracks `analyze_image` calls so the test can assert it wasn't called."""

    def __init__(self) -> None:
        self.image_calls: list[dict] = []
        self.text_calls: list[tuple[str, str]] = []

    def analyze_image(self, *args, **kwargs):
        self.image_calls.append({"args": args, "kwargs": kwargs})
        return SimpleNamespace(text="", parsed={}, provider="stub", model="stub")

    def analyze_text(self, *args, **kwargs):  # pragma: no cover - unused
        self.text_calls.append((args, kwargs))
        return SimpleNamespace(text="", parsed={}, provider="stub", model="stub")


def _build_high_confidence_pdf(tmp_path: Path) -> Path:
    """A page with a full title block, multiple dimensions, and a door
    schedule table — should clear the 0.65 confidence threshold."""
    doc = fitz.open()
    page = doc.new_page(width=792, height=612)

    page.insert_text((40, 60), "ROOM A WALL LENGTH: 10'-6\"", fontsize=11)
    page.insert_text((40, 78), "ROOM B WIDTH: 12'-0\"", fontsize=11)
    page.insert_text((40, 96), "OPENING HEIGHT: 8 1/2\"", fontsize=11)
    page.insert_text((40, 114), "STAIR RISER: 7 3/4\"", fontsize=11)
    page.insert_text((40, 132), "CORRIDOR LENGTH: 24'-0\"", fontsize=11)
    page.insert_text((40, 150), "DOOR WIDTH: 3'-0\"", fontsize=11)

    n_rows, n_cols = 4, 5
    x0, y0 = 40.0, 300.0
    cell_w, cell_h = 110.0, 22.0
    x1 = x0 + cell_w * n_cols
    y1 = y0 + cell_h * n_rows
    for i in range(n_rows + 1):
        page.draw_line((x0, y0 + i * cell_h), (x1, y0 + i * cell_h))
    for j in range(n_cols + 1):
        page.draw_line((x0 + j * cell_w, y0), (x0 + j * cell_w, y1))
    table_rows = [
        ["MARK", "DOOR TYPE", "WIDTH", "HEIGHT", "HARDWARE"],
        ["101A", "SC HM",     "3'-0\"", "7'-0\"", "HW-1"],
        ["101B", "SC HM",     "3'-0\"", "7'-0\"", "HW-1"],
        ["102",  "WD",        "2'-8\"", "6'-8\"", "HW-2"],
    ]
    for i, row in enumerate(table_rows):
        for j, val in enumerate(row):
            page.insert_text(
                (x0 + j * cell_w + 5, y0 + i * cell_h + 15),
                val, fontsize=9,
            )

    tb_x, tb_y = 520.0, 510.0
    for line in [
        "PROJECT NAME: Integration Test Project",
        "PROJECT NO: 2026-IT",
        "SHEET NO: A101",
        "SHEET TITLE: First Floor Plan",
        'SCALE: 1/4" = 1\'-0"',
        "DATE: 2026-05-22",
    ]:
        page.insert_text((tb_x, tb_y), line, fontsize=10)
        tb_y += 14

    out = tmp_path / "integration.pdf"
    doc.save(out)
    doc.close()
    return out


def test_extract_sheet_skips_llm_on_high_confidence_prepass(tmp_path: Path) -> None:
    pdf = _build_high_confidence_pdf(tmp_path)
    sheet = Sheet(
        pdf_name="integration.pdf",
        pdf_path=str(pdf),
        page_index=0,
        sheet_number="A101",
        title="First Floor Plan",
        discipline=Discipline.ARCHITECTURAL,
        sheet_type=SheetType.FLOOR_PLAN,
        image_path=str(pdf),  # not used on the skip path
        embedded_text="(prepass owns the text)",
    )

    stub = _LLMStub()
    ex = extract_sheet(sheet, stub)

    assert ex.lm_skipped is True, "high-confidence prepass must skip the LLM"
    assert stub.image_calls == [], "vision-LLM must not be invoked"
    assert ex.prepass is not None
    assert ex.prepass.confidence >= 0.65

    # The snapshot's title block round-tripped onto the extraction.
    assert ex.prepass.title_block.sheet_number == "A101"
    assert ex.prepass.title_block.discipline == "Architectural"
    assert ex.dimensions, "high-confidence path should persist dimensions"
    # And the door schedule was wired through to the doors[] field.
    assert len(ex.doors) >= 2, f"expected door rows, got {ex.doors!r}"
    assert any(d.mark.startswith("101") for d in ex.doors)


def test_extract_sheet_runs_llm_when_prepass_low_confidence(tmp_path: Path) -> None:
    """A page with no title block and no schedule should drop confidence
    below the threshold and let the LLM run (with prepass as context)."""
    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((40, 60), "Just some prose with no useful fields.", fontsize=11)
    pdf = tmp_path / "low_conf.pdf"
    doc.save(pdf)
    doc.close()

    sheet = Sheet(
        pdf_name="low_conf.pdf",
        pdf_path=str(pdf),
        page_index=0,
        discipline=Discipline.ARCHITECTURAL,
        sheet_type=SheetType.FLOOR_PLAN,
        image_path=str(pdf),
        embedded_text="prose",
    )

    stub = _LLMStub()
    ex = extract_sheet(sheet, stub)

    assert ex.lm_skipped is False
    assert len(stub.image_calls) == 1, "LLM must be invoked on low-confidence prepass"
    # Pre-pass snapshot is still persisted for downstream debugging.
    assert ex.prepass is not None
    # And the deterministic context is injected into the prompt.
    extra = stub.image_calls[0]["kwargs"].get("extra_context", "")
    assert "DETERMINISTIC CONTEXT" in extra
