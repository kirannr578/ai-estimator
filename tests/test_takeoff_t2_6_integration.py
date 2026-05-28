"""Phase T2.6 end-to-end integration tests.

These tests exercise the FULL path: synthetic PDF with an electrical
panel schedule → :func:`prepass_drawing_page` → :class:`SheetExtraction`
→ :func:`core.takeoff.reconcile` → priced-ready
``ProjectModel.takeoffs`` with the synthesised panel rows present.

Mirrors :mod:`tests.test_takeoff_t5_integration` for the finish family.
Proves the panel pre-pass + synthesis + dedupe are correctly wired into
the pipeline, and that downstream T6-style cost-banding routes the
parametric feeder rows to the HAND_TAKEOFF queue (their 0.55 default
is intentionally below 0.65 so the estimator supplies a real LF).
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    prepass_drawing_pdf,
    to_schema as prepass_to_schema,
)
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_PANEL
from core.schemas import (
    SheetExtraction,
    band_for_confidence,
    CostBand,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders (mirror test_takeoff_t5_integration)
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 220.0),
    cell_size: tuple[float, float] = (75.0, 24.0),
) -> None:
    page = doc.new_page(width=900, height=720)
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
    """Run the deterministic pre-pass on one page; wrap in a SheetExtraction."""
    result = prepass_drawing_page(pdf_path, page_index)
    return SheetExtraction(
        sheet_id=sheet_id,
        prepass=prepass_to_schema(result),
    )


def _panel_synthesis_rows(project_takeoffs) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_PANEL}")
    ]


# ---------------------------------------------------------------------------
# 1. Single-panel PDF → synthesised panel rows in the reconcile output
# ---------------------------------------------------------------------------


def test_single_panel_pdf_produces_synthesised_rows(tmp_path: Path) -> None:
    """A single-panel PDF → reconcile emits 4 panel-family takeoff rows.

    Shape for a 21-circuit, 200A MCB panel with one breaker amp size:
    1 enclosure + 1 breaker group + 1 feeder wire + 1 feeder conduit.
    """
    pdf = _build_pdf(
        tmp_path, "single_panel.pdf",
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
            "BUS: 225A",
            "Feeder: 3/0 AWG Cu in 2 inch conduit",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lighting",    "1200",  "A"],
            ["3",   "20",   "Outlets",     "1800",  "B"],
            ["5",   "20",   "HVAC ckts",   "2400",  "C"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E1.0")
    assert sheet.prepass.panel_schedule is not None
    assert sheet.prepass.panel_schedule.panels[0].panel_id == "PNL-A"

    project = reconcile([sheet])
    syn = _panel_synthesis_rows(project.takeoffs)

    # 1 enclosure + 1 breaker group (all 20A) + 1 feeder wire + 1 feeder conduit
    assert len(syn) == 4
    sections = {it.csi_section for it in syn}
    assert sections == {"26 24 16", "26 28 16", "26 05 19", "26 05 33"}
    # Every synthesised row carries the sheet ID.
    assert all("E1.0" in (it.source_sheet_ids or []) for it in syn)


# ---------------------------------------------------------------------------
# 2. Multi-panel PDF → each panel's rows appear in the priced output
# ---------------------------------------------------------------------------


def test_multi_panel_pdf_produces_per_panel_rows(tmp_path: Path) -> None:
    """A 2-page PDF (panel A on p0, panel B on p1) → both panels' rows surface."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lighting",    "1200",  "A"],
            ["3",   "30",   "HVAC",        "5400",  "B"],
        ],
    )
    _add_page(
        doc,
        title_lines=[
            "PANEL SCHEDULE — PANEL MDP",
            "277/480V 3-PHASE",
            "BUS: 800A MLO",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS",  "PHASE"],
            ["1",   "100",  "Subpanel A",  "12000",  "A,B,C"],
            ["2",   "100",  "Subpanel B",  "12000",  "A,B,C"],
        ],
    )
    pdf = tmp_path / "multi_panel.pdf"
    doc.save(pdf)
    doc.close()

    # Pre-pass both pages, wrap in SheetExtractions.
    pages = prepass_drawing_pdf(pdf)
    sheets = [
        SheetExtraction(
            sheet_id=f"E{1+i}.0",
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)
    syn = _panel_synthesis_rows(project.takeoffs)

    # Each panel produces (1 enclosure + branch breaker groups + 2 feeders).
    # PNL-A has 2 distinct amp sizes (20A, 30A), MDP has 1 (100A).
    # Total: (1 + 2 + 2) + (1 + 1 + 2) = 5 + 4 = 9 panel synthesis rows.
    assert len(syn) == 9

    # Both marks land in the synthesised notes.
    notes_text = " ".join((it.notes or "") for it in syn)
    assert "mark=PNL-A" in notes_text
    assert "mark=MDP" in notes_text

    # Enclosure class selection: PNL-A → panelboard, MDP (800A) → switchboard.
    enclosures = [it for it in syn
                  if it.csi_section in {"26 24 16", "26 24 13"}]
    pnl_a = next(it for it in enclosures if "PNL-A" in (it.notes or ""))
    mdp = next(it for it in enclosures if "mark=MDP" in (it.notes or ""))
    assert pnl_a.csi_section == "26 24 16"  # panelboard
    assert mdp.csi_section == "26 24 13"    # switchboard (> 400A)


# ---------------------------------------------------------------------------
# 3. T6-style banding: feeder rows route to HAND_TAKEOFF queue
# ---------------------------------------------------------------------------


def test_feeder_rows_route_to_hand_takeoff_band(tmp_path: Path) -> None:
    """Feeder confidence of 0.55 → HAND_TAKEOFF band (< 0.65 threshold).

    The synthesiser emits feeder conductor + conduit at 0.55 confidence
    because their 50 LF quantity is a parametric default — the
    estimator needs to supply the real run length. T6 banding routes
    these rows to the hand-takeoff worklist so they're never silently
    auto-approved.
    """
    pdf = _build_pdf(
        tmp_path, "feeder_bands.pdf",
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E1.0")
    project = reconcile([sheet])
    syn = _panel_synthesis_rows(project.takeoffs)

    feeder_rows = [it for it in syn
                   if it.csi_section in {"26 05 19", "26 05 33"}]
    assert len(feeder_rows) == 2  # one wire + one conduit
    for row in feeder_rows:
        assert band_for_confidence(row.confidence) == CostBand.HAND_TAKEOFF


def test_panel_enclosure_routes_to_auto_approve_band(tmp_path: Path) -> None:
    """A clean, fully-decorated panel synthesises ≥ 0.85 → AUTO_APPROVE band."""
    pdf = _build_pdf(
        tmp_path, "auto_approve.pdf",
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
            "BUS: 225A",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
            ["3",   "30",   "Heater",      "4800",  "B"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E1.0")
    project = reconcile([sheet])
    syn = _panel_synthesis_rows(project.takeoffs)
    enclosure = next(it for it in syn if it.csi_section == "26 24 16")
    assert band_for_confidence(enclosure.confidence) == CostBand.AUTO_APPROVE


# ---------------------------------------------------------------------------
# 4. Dedupe interaction: LLM panel aggregate gone when synthesis present
# ---------------------------------------------------------------------------


def test_panel_synthesis_does_not_collide_with_other_extractors(
    tmp_path: Path,
) -> None:
    """A 2-page PDF (door schedule + panel schedule) → both pass without conflict.

    Door extraction on page 0 must NOT trigger the panel extractor and
    vice versa; running reconcile yields door rows AND panel synthesis
    rows side-by-side with no cross-suppression.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["DOOR SCHEDULE", "Sheet A0.1"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
            ["102",  "HM",   "3'-0\"", "7'-0\"", "HM",    "HW-1"],
        ],
    )
    _add_page(
        doc,
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
    )
    pdf = tmp_path / "mixed.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheets = [
        SheetExtraction(
            sheet_id=("A0.1" if i == 0 else "E1.0"),
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    door_section_rows = [
        t for t in project.takeoffs
        if (t.csi_division or "") == "08"
    ]
    panel_syn = _panel_synthesis_rows(project.takeoffs)

    assert door_section_rows, "door extractor produced no rows"
    assert panel_syn, "panel synthesis produced no rows"
    # No panel-family rows accidentally appear in division 08; no door
    # rows accidentally appear in division 26.
    for it in panel_syn:
        assert it.csi_division == "26"
    for it in door_section_rows:
        assert it.csi_division == "08"
