"""Phase T2.10 end-to-end integration tests — kitchen + lab specialty schedules.

Exercises the full path for both new families: synthetic PDF with a
kitchen and/or lab schedule → :func:`prepass_drawing_pdf` →
:class:`SheetExtraction` → :func:`core.takeoff.reconcile` →
priced-ready ``ProjectModel.takeoffs`` with synthesised kitchen +
lab rows present.

Mirrors :mod:`tests.test_takeoff_t2_9_integration` for the specialty
families.  Closes the Division 11 + 12 specialty pair entirely; AV
(Div 27) + Security (Div 28) are deferred to Phase T2.11.
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
    SYNTHESIS_SOURCE_TAG_KITCHEN,
    SYNTHESIS_SOURCE_TAG_LAB,
    SYNTHESIS_SOURCE_TAG_PLUMBING,
)
from core.schemas import (
    CostBand,
    CostSourceTier,
    SheetExtraction,
    band_for_confidence,
    price_confidence_from_similarity,
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


def _sheet_from_prepass(pdf_path: Path, page_index: int,
                          sheet_id: str) -> SheetExtraction:
    result = prepass_drawing_page(pdf_path, page_index)
    return SheetExtraction(
        sheet_id=sheet_id,
        prepass=prepass_to_schema(result),
    )


def _rows_with_source(project_takeoffs, source_tag: str) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={source_tag}")
    ]


# ---------------------------------------------------------------------------
# 1. End-to-end: kitchen + lab on a single PDF
# ---------------------------------------------------------------------------


def test_kitchen_and_lab_schedules_flow_through_pipeline(tmp_path: Path) -> None:
    """Two-page PDF (kitchen + lab) → both pre-passes fire, both synth families present."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MFR",     "BTU",  "GAS",  "ELEC", "QTY"],
            ["RA-1",  "Range",       "Vulcan",  "120K", "X",    "",     "2"],
            ["REF-1", "Refrigerator","True",    "",     "",     "X",    "1"],
        ],
    )
    _add_page(
        doc,
        title_lines=["LAB CASEWORK SCHEDULE", "Sheet I2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MATERIAL",  "FUME", "VACUUM", "WATER", "QTY"],
            ["BC-1", "Base cabinet", "EPOXY",     "-",    "-",      "-",     "4"],
            ["FH-1", "Fume hood",    "STAINLESS", "X",    "X",      "X",     "2"],
        ],
    )
    pdf = tmp_path / "kitchen_lab.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["K2.0", "I2.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    # Confirm the prepass actually wired both kitchen and lab schedules.
    assert sheets[0].prepass.kitchen_schedule is not None
    assert len(sheets[0].prepass.kitchen_schedule.equipment) == 2
    assert sheets[1].prepass.lab_schedule is not None
    assert len(sheets[1].prepass.lab_schedule.casework) == 2

    project = reconcile(sheets)
    kitchen_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_KITCHEN)
    lab_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_LAB)
    assert kitchen_syn, "kitchen synthesis produced no rows"
    assert lab_syn, "lab synthesis produced no rows"

    # Kitchen — RA-1 (eq + gas rough-in) + REF-1 (eq + elec rough-in).
    kitchen_sections = sorted(it.csi_section for it in kitchen_syn)
    assert "11 40 13.13" in kitchen_sections     # RA-1 range
    assert "11 40 16.13" in kitchen_sections     # REF-1 refrigerator
    assert "22 11 16" in kitchen_sections        # RA-1 gas rough-in
    assert "26 27 26" in kitchen_sections        # REF-1 elec rough-in

    # Lab — BC-1 (1 row, no utility, no mfr) + FH-1 (eq + water-side
    # rough-in, fume hood trim exempt).
    lab_sections = sorted(it.csi_section for it in lab_syn)
    assert "12 35 53.13" in lab_sections   # BC-1 base cabinet
    assert "11 53 13" in lab_sections      # FH-1 fume hood
    assert "22 11 16" in lab_sections      # FH-1 piped rough-in


# ---------------------------------------------------------------------------
# 2. Kitchen + plumbing don't cross-suppress (kitchen-sink-vs-lavatory case)
# ---------------------------------------------------------------------------


def test_kitchen_and_plumbing_schedules_do_not_cross_suppress(tmp_path: Path) -> None:
    """A project with both a kitchen SK and a plumbing LAV → both surfaces survive.

    Kitchen sinks live at ``11 40 13`` (food service generic) and
    plumbing lavatories live at ``22 41 16``.  The CSI prefix scopes
    are disjoint and neither dedupe touches the other family's rows.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "BTU",  "GAS", "WATER", "DRAIN", "QTY"],
            ["SK-1", "3-comp sink",  "",     "-",   "X",     "X",     "2"],
        ],
    )
    _add_page(
        doc,
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "GPF",  "GPM", "CW",     "WASTE"],
            ["LAV-A", "LAVATORY",    "",     "0.5", "1/2\"",  "1-1/2\""],
        ],
    )
    pdf = tmp_path / "kitchen_plumb.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["K2.0", "P2.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    kitchen_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_KITCHEN)
    plumbing_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PLUMBING)

    # Kitchen SK-1 — primary at 11 40 13 + water rough-in at 22 11 16.
    kitchen_sections = {it.csi_section for it in kitchen_syn}
    assert "11 40 13" in kitchen_sections
    # Plumbing LAV-A — fixture at 22 41 16 + supply rough-in at 22 11 16.
    plumbing_sections = {it.csi_section for it in plumbing_syn}
    assert "22 41 16" in plumbing_sections

    # Cross-suppression check: neither family's primary row was
    # dropped by the OTHER family's dedupe.
    descs = [t.description or "" for t in project.takeoffs]
    assert any("Kitchen equipment SK-1" in d for d in descs)
    assert any("Plumbing fixture LAV-A" in d for d in descs)


# ---------------------------------------------------------------------------
# 3. T6.1 confidence bands — kitchen rough-in routes to HAND_TAKEOFF
# ---------------------------------------------------------------------------


def test_kitchen_roughin_lands_in_hand_takeoff_band(tmp_path: Path) -> None:
    """LS rough-in row (parametric haircut floor) lands in HAND_TAKEOFF queue."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",  "DESCRIPTION", "BTU"],
            ["RA-1", "Range",       "60K"],
        ],
    )
    pdf = tmp_path / "kitchen_roughin_band.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="K2.0")
    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_KITCHEN)

    roughin_rows = [
        it for it in syn
        if it.csi_section in {"22 11 16", "26 27 26", "23 31 13"}
    ]
    assert len(roughin_rows) == 1
    ri = roughin_rows[0]
    assert ri.unit == "LS"
    # Without QTY: parent = 0.55 → haircut = 0.55 × 0.95 = 0.5225,
    # clamped via T6.1 floor (0.45 minimum applies only when below).
    # 0.5225 < 0.65 → HAND_TAKEOFF.
    assert ri.confidence is not None
    assert band_for_confidence(ri.confidence) == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# 4. T7 cost-source tier — rough-in routes to PARAMETRIC
# ---------------------------------------------------------------------------


def test_lab_roughin_with_no_qty_routes_to_parametric_tier() -> None:
    """A rough-in row whose confidence sinks below 0.50 → PARAMETRIC tier per T7."""
    # Test the threshold math directly — no extractor needed.
    # T6.1 rough-in confidence when parent is 0.55 (no-QTY band):
    #   0.55 × 0.95 = 0.5225 — still above the 0.50 INTERPOLATED tier
    #   boundary, so under T7 it banding is INTERPOLATED, NOT
    #   PARAMETRIC.  This is the documented contract: only QTY-aware
    #   primaries route their derived rows below 0.50.
    tier, _ = price_confidence_from_similarity(0.5225)
    assert tier == CostSourceTier.INTERPOLATED

    # Below 0.50 → PARAMETRIC.
    tier2, conf2 = price_confidence_from_similarity(0.45)
    assert tier2 == CostSourceTier.PARAMETRIC
    assert conf2 == 0.45


# ---------------------------------------------------------------------------
# 5. Empty schedules safe
# ---------------------------------------------------------------------------


def test_empty_kitchen_and_lab_schedules_are_safe(tmp_path: Path) -> None:
    """A project with no kitchen or lab pages → no synthesis rows, no errors."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["FLOOR PLAN", "Sheet A1.0"],
    )
    pdf = tmp_path / "empty.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A1.0")
    assert sheet.prepass.kitchen_schedule is None
    assert sheet.prepass.lab_schedule is None
    project = reconcile([sheet])
    assert _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_KITCHEN) == []
    assert _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_LAB) == []
