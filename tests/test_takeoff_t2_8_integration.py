"""Phase T2.8 end-to-end integration tests.

Exercises the full path: synthetic PDF with a mechanical equipment
schedule → :func:`prepass_drawing_page` → :class:`SheetExtraction` →
:func:`core.takeoff.reconcile` → priced-ready ``ProjectModel.takeoffs``
with the synthesised HVAC rows present.

Mirrors :mod:`tests.test_takeoff_t2_7_integration` for the HVAC family.
Proves the HVAC pre-pass + synthesis + dedupe are correctly wired into
the pipeline, validates that the LS rough-in row (conf=0.45) lands in
the HAND_TAKEOFF queue, and demonstrates that HVAC + lighting + panel
can coexist on the same project.
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
    SYNTHESIS_SOURCE_TAG_HVAC,
    SYNTHESIS_SOURCE_TAG_LIGHTING,
    SYNTHESIS_SOURCE_TAG_PANEL,
)
from core.schemas import (
    CostBand,
    SheetExtraction,
    band_for_confidence,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders (mirror T2.7 with auto-sizing)
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


def _hvac_synthesis_rows(project_takeoffs) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_HVAC}")
    ]


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
# 1. End-to-end: a synthetic HVAC PDF → priced rows with the right count
# ---------------------------------------------------------------------------


def test_single_hvac_pdf_produces_synthesised_rows(tmp_path: Path) -> None:
    """A 3-equipment HVAC schedule → 8 synthesised rows.

    Two motorised rows (AHU, RTU) → 3 items each (equipment + rough-in
    + disconnect). One VAV → 2 items (equipment + rough-in only; no
    disconnect because VAVs are duct-fed). 3+3+2 = 8.
    """
    pdf = _build_pdf(
        tmp_path, "single_hvac.pdf",
        title_lines=[
            "MECHANICAL EQUIPMENT SCHEDULE",
            "Sheet M2.0",
        ],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP",  "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",   "480V/3PH"],
            ["RTU-A", "ROOFTOP",     "Carrier",      "3000", "7.5", "480V/3PH"],
            ["VAV-1", "VAV BOX",     "Titus",        "400",  "0",   ""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="M2.0")
    assert sheet.prepass.hvac_schedule is not None
    assert len(sheet.prepass.hvac_schedule.equipment) == 3

    project = reconcile([sheet])
    syn = _hvac_synthesis_rows(project.takeoffs)

    assert len(syn) == 8
    sections = sorted(it.csi_section for it in syn)
    # 1× AHU (23 73 13), 1× RTU (23 74 13), 1× VAV (23 36 00),
    # 3× rough-in (23 05 00), 2× disconnect (26 28 16).
    assert sections == [
        "23 05 00", "23 05 00", "23 05 00",
        "23 36 00",
        "23 73 13",
        "23 74 13",
        "26 28 16", "26 28 16",
    ]
    assert all("M2.0" in (it.source_sheet_ids or []) for it in syn)


# ---------------------------------------------------------------------------
# 2. HVAC + lighting + panel coexist on a single project
# ---------------------------------------------------------------------------


def test_hvac_lighting_and_panel_schedules_coexist(tmp_path: Path) -> None:
    """A 3-page PDF (HVAC on M2.0, lighting on E2.0, panel on E1.0).

    Validates the disjoint-detector posture: HVAC pre-pass, lighting
    pre-pass, and panel pre-pass each pick up their own sheet without
    crossover or suppression — all three synthesis streams land in the
    same priced output with their own CSI prefixes intact.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["AHU SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",  "480V/3PH"],
        ],
    )
    _add_page(
        doc,
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER 4000K", "40",    "277V",    "RECESSED"],
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
    pdf = tmp_path / "tri_disc.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["M2.0", "E2.0", "E1.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    hvac_syn = _hvac_synthesis_rows(project.takeoffs)
    lighting_syn = _lighting_synthesis_rows(project.takeoffs)
    panel_syn = _panel_synthesis_rows(project.takeoffs)

    assert hvac_syn, "hvac synthesis produced no rows"
    assert lighting_syn, "lighting synthesis produced no rows"
    assert panel_syn, "panel synthesis produced no rows"

    # HVAC: AHU with HP+voltage → 3 rows (equipment + rough-in + disconnect).
    assert len(hvac_syn) == 3
    hvac_sections = {it.csi_section for it in hvac_syn}
    assert "23 73 13" in hvac_sections   # AHU equipment
    assert "23 05 00" in hvac_sections   # MEP rough-in
    assert "26 28 16" in hvac_sections   # Disconnect + flex

    # No cross-contamination: each family stays in its own CSI bucket
    # (lighting → 26 51/55; panel → 26 24/28/05; HVAC equipment → 23,
    # plus its disconnect → 26 28 16).
    for it in lighting_syn:
        assert it.csi_section.startswith(("26 51", "26 55"))
    for it in panel_syn:
        assert it.csi_section.startswith(("26 24", "26 28", "26 05"))


# ---------------------------------------------------------------------------
# 3. T6 banding — LS rough-in (conf=0.45) routes to HAND_TAKEOFF queue
# ---------------------------------------------------------------------------


def test_roughin_rows_route_to_hand_takeoff_band(tmp_path: Path) -> None:
    """The LS rough-in row (conf=0.45) lands in the HAND_TAKEOFF queue.

    Rationale: rough-in is intentionally parametric — the actual ductwork
    / piping length depends on a plan-walk that synthesis can't perform.
    T6 banding correctly routes it to the hand-takeoff worklist so the
    estimator must walk the floor plan before pricing.
    """
    pdf = _build_pdf(
        tmp_path, "roughin_band.pdf",
        title_lines=["AHU SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",  "480V/3PH"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="M2.0")
    project = reconcile([sheet])
    syn = _hvac_synthesis_rows(project.takeoffs)

    roughin_rows = [it for it in syn if it.csi_section == "23 05 00"]
    assert len(roughin_rows) == 1
    ri = roughin_rows[0]
    assert ri.unit == "LS"
    assert ri.confidence == 0.45
    assert band_for_confidence(ri.confidence) == CostBand.HAND_TAKEOFF

    # The disconnect row at conf=0.70 should NOT be in HAND_TAKEOFF.
    disconnect_rows = [it for it in syn if it.csi_section == "26 28 16"]
    assert len(disconnect_rows) == 1
    assert band_for_confidence(disconnect_rows[0].confidence) == CostBand.OPERATOR_REVIEW


# ---------------------------------------------------------------------------
# 4. QTY-aware confidence — equipment row WITH qty lands in AUTO_APPROVE
# ---------------------------------------------------------------------------


def test_with_qty_equipment_rows_route_above_hand_takeoff(
    tmp_path: Path,
) -> None:
    """Schedule WITH QTY column → equipment row conf=0.90 → AUTO_APPROVE band.

    A QTY column raises the equipment row's confidence above the
    AUTO_APPROVE gate (≥0.85), so it bypasses the worklist entirely.
    The rough-in row is still routed to HAND_TAKEOFF — that's by design.
    """
    pdf = _build_pdf(
        tmp_path, "with_qty.pdf",
        title_lines=["FAN SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG", "DESCRIPTION", "CFM",  "HP", "VOLTAGE",  "QTY"],
            ["F-1", "EXHAUST FAN", "1500", "2",  "208V/3PH", "4"],
            ["F-2", "SUPPLY FAN",  "2500", "3",  "208V/3PH", "2"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="M2.0")
    assert all(
        eq.quantity is not None and eq.quantity > 0
        for eq in sheet.prepass.hvac_schedule.equipment
    )

    project = reconcile([sheet])
    syn = _hvac_synthesis_rows(project.takeoffs)

    # 2 fans × (equipment + rough-in + disconnect) = 6 rows.
    assert len(syn) == 6
    fan_eq_rows = [it for it in syn if it.csi_section == "23 34 00"]
    assert len(fan_eq_rows) == 2
    fan_qtys = sorted(int(it.quantity) for it in fan_eq_rows)
    assert fan_qtys == [2, 4]
    for row in fan_eq_rows:
        # 0.90 lands in AUTO_APPROVE (≥ 0.85 threshold).
        assert row.confidence == 0.90
        assert band_for_confidence(row.confidence) == CostBand.AUTO_APPROVE
