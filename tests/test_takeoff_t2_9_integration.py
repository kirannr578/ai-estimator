"""Phase T2.9 end-to-end integration tests.

Exercises the full path: synthetic PDF with a plumbing fixture
schedule → :func:`prepass_drawing_page` → :class:`SheetExtraction` →
:func:`core.takeoff.reconcile` → priced-ready ``ProjectModel.takeoffs``
with the synthesised plumbing rows present.

Mirrors :mod:`tests.test_takeoff_t2_8_integration` for the plumbing
family.  Proves the plumbing pre-pass + synthesis + dedupe are
correctly wired into the pipeline, validates that the LS rough-in
row (conf=0.45) lands in the HAND_TAKEOFF queue, and demonstrates
that plumbing + HVAC + lighting + panel can coexist on the same
project (closing the Division 22+23+26 typed-schedule trifecta).
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
    SYNTHESIS_SOURCE_TAG_PLUMBING,
)
from core.schemas import (
    CostBand,
    SheetExtraction,
    band_for_confidence,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Fixture builders (mirror T2.8 with auto-sizing)
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


def _rows_with_source(project_takeoffs, source_tag: str) -> list:
    return [
        t for t in project_takeoffs
        if (t.notes or "").startswith(f"source={source_tag}")
    ]


# ---------------------------------------------------------------------------
# 1. End-to-end: a synthetic plumbing PDF → priced rows with the right shape
# ---------------------------------------------------------------------------


def test_single_plumbing_pdf_produces_synthesised_rows(tmp_path: Path) -> None:
    """A 3-fixture plumbing schedule with mfr+model → 9 synthesised rows.

    Each fixture (mfr + model published) → 3 rows (fixture + rough-in
    + trim). 3 × 3 = 9.  WC routes to waste-dominant rough-in;
    LAV + EWC route to supply-dominant rough-in.
    """
    pdf = _build_pdf(
        tmp_path, "single_plumbing.pdf",
        title_lines=[
            "PLUMBING FIXTURE SCHEDULE",
            "Sheet P2.0",
        ],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER",      "MODEL",
             "MOUNTING", "GPF",  "GPM", "CW",     "WASTE"],
            ["WC-1",  "WATER CLOSET", "American Standard", "3461.001",
             "WALL", "1.28", "",    "1/2\"",  "4\""],
            ["LAV-A", "LAVATORY",     "Kohler",            "K-2210",
             "COUNTER", "",    "0.5", "1/2\"",  "1-1/2\""],
            ["EWC-1", "DRINKING FT",  "Elkay",             "LZS8L",
             "WALL", "",    "",    "1/2\"",  "1-1/4\""],
        ],
        cell_size=(95.0, 24.0),
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="P2.0")
    assert sheet.prepass.plumbing_schedule is not None
    assert len(sheet.prepass.plumbing_schedule.fixtures) == 3

    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PLUMBING)

    assert len(syn) == 9
    sections = sorted(it.csi_section for it in syn)
    # 1× WC (22 41 13) + 1× LAV (22 41 16) + 1× EWC (22 47 13);
    # 1× WC trim (22 41 13) + 1× LAV trim (22 41 16) + 1× EWC trim (22 47 13);
    # 1× WC waste rough-in (22 13 16) + 2× supply rough-ins (22 11 16).
    assert sections == [
        "22 11 16", "22 11 16",
        "22 13 16",
        "22 41 13", "22 41 13",
        "22 41 16", "22 41 16",
        "22 47 13", "22 47 13",
    ]
    assert all("P2.0" in (it.source_sheet_ids or []) for it in syn)


# ---------------------------------------------------------------------------
# 2. Plumbing + HVAC + lighting + panel coexist on a single project
# ---------------------------------------------------------------------------


def test_plumbing_hvac_lighting_and_panel_schedules_coexist(
    tmp_path: Path,
) -> None:
    """A 4-page PDF closes the Division 22+23+26 trifecta entirely.

    Plumbing on P2.0, HVAC on M2.0, lighting on E2.0, panel on E1.0.
    Validates the disjoint-detector posture: every pre-pass picks up
    its own sheet without crossover or suppression — all four
    synthesis streams land in the same priced output with their own
    CSI prefixes intact.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MANUFACTURER", "GPF",   "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "American Std", "1.28",  "1/2\"",  "4\""],
        ],
    )
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
    pdf = tmp_path / "quad_disc.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["P2.0", "M2.0", "E2.0", "E1.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    plumbing_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PLUMBING)
    hvac_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_HVAC)
    lighting_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_LIGHTING)
    panel_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PANEL)

    assert plumbing_syn, "plumbing synthesis produced no rows"
    assert hvac_syn, "hvac synthesis produced no rows"
    assert lighting_syn, "lighting synthesis produced no rows"
    assert panel_syn, "panel synthesis produced no rows"

    # Plumbing: WC with no mfr-only (American Std but no model) → 2 rows.
    assert len(plumbing_syn) == 2
    plumbing_sections = {it.csi_section for it in plumbing_syn}
    assert "22 41 13" in plumbing_sections  # WC fixture
    assert "22 13 16" in plumbing_sections  # waste-dominant rough-in

    # No cross-contamination: each family stays in its own CSI bucket.
    for it in plumbing_syn:
        assert it.csi_section.startswith("22 "), \
            f"plumbing row leaked outside Division 22: {it.csi_section}"
    for it in hvac_syn:
        # HVAC equipment lives in 23; HVAC disconnect lives in 26 28.
        assert it.csi_section.startswith(("23 ", "26 28")), \
            f"hvac row landed outside expected sections: {it.csi_section}"
    for it in lighting_syn:
        assert it.csi_section.startswith(("26 51", "26 55"))
    for it in panel_syn:
        assert it.csi_section.startswith(("26 24", "26 28", "26 05"))


# ---------------------------------------------------------------------------
# 3. T6 banding — LS rough-in (conf=0.45) routes to HAND_TAKEOFF queue
# ---------------------------------------------------------------------------


def test_plumbing_roughin_rows_route_to_hand_takeoff_band(
    tmp_path: Path,
) -> None:
    """The LS rough-in row (conf=0.45) lands in the HAND_TAKEOFF queue.

    Rationale: rough-in is intentionally parametric — the actual
    piping length and connection scope depend on a plan-walk that
    synthesis can't perform.  T6 banding correctly routes it to the
    hand-takeoff worklist so the estimator must walk the floor plan
    before pricing.
    """
    pdf = _build_pdf(
        tmp_path, "roughin_band.pdf",
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MANUFACTURER", "GPF",  "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "American Std", "1.28", "1/2\"",  "4\""],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="P2.0")
    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PLUMBING)

    roughin_rows = [
        it for it in syn if it.csi_section in {"22 11 16", "22 13 16"}
    ]
    assert len(roughin_rows) == 1
    ri = roughin_rows[0]
    assert ri.unit == "LS"
    assert ri.confidence == 0.45
    assert band_for_confidence(ri.confidence) == CostBand.HAND_TAKEOFF
    # Confirms T7 PARAMETRIC tier: 0.45 < 0.50 places it in the
    # PARAMETRIC band on the T7 confidence tier rollup as well.
    assert ri.confidence < 0.50


# ---------------------------------------------------------------------------
# 4. QTY-aware confidence — fixture row WITH qty lands in AUTO_APPROVE
# ---------------------------------------------------------------------------


def test_plumbing_with_qty_fixture_rows_route_to_auto_approve(
    tmp_path: Path,
) -> None:
    """Schedule WITH QTY column → fixture row conf=0.90 → AUTO_APPROVE band.

    A QTY column raises the fixture row's confidence above the
    AUTO_APPROVE gate (≥0.85), so it bypasses the worklist entirely.
    The rough-in row is still routed to HAND_TAKEOFF — that's by
    design.
    """
    pdf = _build_pdf(
        tmp_path, "with_qty.pdf",
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG",   "DESCRIPTION",  "GPF",   "GPM", "CW",     "WASTE", "QTY"],
            ["WC-1",  "WATER CLOSET", "1.28",  "",    "1/2\"",  "4\"",    "8"],
            ["LAV-A", "LAVATORY",     "",      "0.5", "1/2\"",  "1-1/2\"", "4"],
        ],
    )
    sheet = _sheet_from_prepass(pdf, 0, sheet_id="P2.0")
    assert all(
        f.quantity is not None and f.quantity > 0
        for f in sheet.prepass.plumbing_schedule.fixtures
    )

    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_PLUMBING)

    # 2 fixtures × (fixture EA + rough-in LS) = 4 rows (no mfr/model →
    # no trim line).
    assert len(syn) == 4
    fixture_rows = [it for it in syn if it.unit == "EA"]
    assert len(fixture_rows) == 2
    fixture_qtys = sorted(int(it.quantity) for it in fixture_rows)
    assert fixture_qtys == [4, 8]
    for row in fixture_rows:
        # 0.90 lands in AUTO_APPROVE (≥ 0.85 threshold).
        assert row.confidence == 0.90
        assert band_for_confidence(row.confidence) == CostBand.AUTO_APPROVE
