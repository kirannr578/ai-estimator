"""Phase T2.7 end-to-end integration tests.

These tests exercise the FULL path: synthetic PDF with a lighting-
fixture schedule → :func:`prepass_drawing_page` → :class:`SheetExtraction`
→ :func:`core.takeoff.reconcile` → priced-ready
``ProjectModel.takeoffs`` with the synthesised lighting rows present.

Mirrors :mod:`tests.test_takeoff_t2_6_integration` for the lighting
family. Proves the lighting pre-pass + synthesis + dedupe are correctly
wired into the pipeline, and that without-QTY fixtures route to the
HAND_TAKEOFF queue (0.55 default is intentionally below 0.65 so the
estimator walks the floor plan).
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    prepass_drawing_pdf,
    to_schema as prepass_to_schema,
)
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_LIGHTING,
    SYNTHESIS_SOURCE_TAG_PANEL,
)
from core.schemas import (
    SheetExtraction,
    band_for_confidence,
    CostBand,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders (mirror test_takeoff_t2_6_integration with auto-sizing)
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 220.0),
    cell_size: tuple[float, float] = (110.0, 24.0),
) -> None:
    if table:
        n_cols = max(len(r) for r in table)
        needed_w = table_origin[0] + cell_size[0] * n_cols + 40.0
        width = max(900.0, needed_w)
    else:
        width = 900.0
    page = doc.new_page(width=width, height=720)
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


def _lighting_synthesis_rows(project_takeoffs) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_LIGHTING}")
    ]


def _panel_synthesis_rows(project_takeoffs) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_PANEL}")
    ]


# ---------------------------------------------------------------------------
# 1. End-to-end: a synthetic lighting PDF → priced rows with the right count
# ---------------------------------------------------------------------------


def test_single_lighting_pdf_produces_synthesised_rows(tmp_path: Path) -> None:
    """A 3-fixture lighting schedule (LED, LED, FLUOR) → 4 synthesised rows.

    3 fixtures × 1 EA each + 1 lamp/driver LS for the fluorescent = 4
    rows in the project takeoffs.
    """
    pdf = _build_pdf(
        tmp_path, "single_lighting.pdf",
        title_lines=[
            "LIGHTING FIXTURE SCHEDULE",
            "Sheet E2.0",
        ],
        table=[
            ["TAG", "DESCRIPTION",            "MANUFACTURER", "WATTS",
             "VOLTAGE", "MOUNTING"],
            ["A1",  "2x4 LED TROFFER 4000K", "Lithonia",     "40",
             "277V",    "RECESSED"],
            ["B",   "LED DOWNLIGHT",         "Cooper",       "15",
             "120V",    "RECESSED"],
            ["C",   "T8 FLUOR TROFFER",      "Lithonia",     "32",
             "120V",    "RECESSED"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E2.0")
    assert sheet.prepass.lighting_schedule is not None
    assert len(sheet.prepass.lighting_schedule.fixtures) == 3

    project = reconcile([sheet])
    syn = _lighting_synthesis_rows(project.takeoffs)

    # 3 fixture EA rows + 1 lamp LS row for the fluorescent.
    assert len(syn) == 4
    units = sorted(it.unit for it in syn)
    assert units == ["EA", "EA", "EA", "LS"]
    # All routed to interior lighting (no WALL-mounted fixture in this set).
    sections = {it.csi_section for it in syn}
    assert sections == {"26 51 13", "26 55 53"}
    # Sheet ID propagates.
    assert all("E2.0" in (it.source_sheet_ids or []) for it in syn)


# ---------------------------------------------------------------------------
# 2. Lighting + panel schedules on same project → BOTH extracted
# ---------------------------------------------------------------------------


def test_lighting_and_panel_schedules_extracted_together(
    tmp_path: Path,
) -> None:
    """A 2-page PDF (lighting on p0, panel on p1) → both pre-passes fire.

    Validates the disjoint-detector posture: lighting pre-pass and
    panel pre-pass each pick up their own sheet without crossover or
    suppression.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER 4000K", "40",    "277V",    "RECESSED"],
            ["B",   "WALL SCONCE LED",   "15",    "120V",    "WALL"],
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
            ["1",   "20",   "Lights",      "1200",  "A"],
        ],
    )
    pdf = tmp_path / "mixed.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheets = [
        SheetExtraction(
            sheet_id=("E2.0" if i == 0 else "E1.0"),
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    lighting_syn = _lighting_synthesis_rows(project.takeoffs)
    panel_syn = _panel_synthesis_rows(project.takeoffs)

    assert lighting_syn, "lighting synthesis produced no rows"
    assert panel_syn, "panel synthesis produced no rows"

    # Lighting: 2 fixture rows (LED, LED → no lamp lines).
    assert len(lighting_syn) == 2
    # Sections cover both interior and wall-mounted lighting.
    lighting_sections = {it.csi_section for it in lighting_syn}
    assert lighting_sections == {"26 51 13", "26 51 19"}

    # No cross-contamination: lighting rows stay in 26 51 / 26 55,
    # panel rows stay in 26 24 / 26 28 / 26 05.
    for it in lighting_syn:
        assert it.csi_section.startswith(("26 51", "26 55"))
    for it in panel_syn:
        assert it.csi_section.startswith(("26 24", "26 28", "26 05"))


# ---------------------------------------------------------------------------
# 3. Without-QTY fixtures route to HAND_TAKEOFF queue via T6 banding
# ---------------------------------------------------------------------------


def test_without_qty_fixtures_route_to_hand_takeoff_band(
    tmp_path: Path,
) -> None:
    """Schedule without QTY column → 0.55 confidence → HAND_TAKEOFF band.

    The synthesiser emits each fixture at quantity=1.0 / confidence=0.55
    because the schedule didn't publish a count. T6 banding routes
    these rows to the hand-takeoff worklist so the estimator can't
    miss them.
    """
    pdf = _build_pdf(
        tmp_path, "no_qty.pdf",
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER 4000K", "40",    "277V",    "RECESSED"],
            ["B",   "WALL SCONCE LED",   "15",    "120V",    "WALL"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E2.0")
    # None of the fixtures should have a quantity from the schedule.
    assert all(
        f.quantity is None
        for f in sheet.prepass.lighting_schedule.fixtures
    )

    project = reconcile([sheet])
    syn = _lighting_synthesis_rows(project.takeoffs)
    assert len(syn) == 2
    for row in syn:
        assert row.quantity == 1.0
        assert band_for_confidence(row.confidence) == CostBand.HAND_TAKEOFF


def test_with_qty_fixtures_route_above_hand_takeoff_band(
    tmp_path: Path,
) -> None:
    """Schedule WITH QTY column → 0.90 confidence → OPERATOR_REVIEW band.

    A QTY column raises the confidence above the HAND_TAKEOFF gate so
    the row lands in the headline cost (still flagged for operator
    review since it's below 0.95 AUTO_APPROVE).
    """
    pdf = _build_pdf(
        tmp_path, "with_qty.pdf",
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "WATTS", "VOLTAGE", "MOUNTING", "QTY"],
            ["A1",  "LED TROFFER 4000K", "40",    "277V",    "RECESSED", "12"],
            ["B",   "LED DOWNLIGHT",     "15",    "120V",    "RECESSED", "8"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="E2.0")
    assert all(
        f.quantity is not None and f.quantity > 0
        for f in sheet.prepass.lighting_schedule.fixtures
    )

    project = reconcile([sheet])
    syn = _lighting_synthesis_rows(project.takeoffs)
    assert len(syn) == 2
    by_tag_qty = sorted(int(it.quantity) for it in syn)
    assert by_tag_qty == [8, 12]
    for row in syn:
        # 0.90 lands strictly above HAND_TAKEOFF (< 0.65 threshold).
        assert band_for_confidence(row.confidence) != CostBand.HAND_TAKEOFF
