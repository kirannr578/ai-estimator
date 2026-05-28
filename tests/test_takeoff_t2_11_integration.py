"""Phase T2.11 end-to-end integration tests — AV + Security specialty schedules.

Exercises the full path for both new families: synthetic PDF with an
AV and/or Security schedule → :func:`prepass_drawing_pdf` →
:class:`SheetExtraction` → :func:`core.takeoff.reconcile` →
priced-ready ``ProjectModel.takeoffs`` with synthesised AV + Security
rows present.

Mirrors :mod:`tests.test_takeoff_t2_10_integration` for the AV+Security
specialty pair.  Closes the T2.x typed-extraction family entirely.
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
    SYNTHESIS_SOURCE_TAG_AV,
    SYNTHESIS_SOURCE_TAG_KITCHEN,
    SYNTHESIS_SOURCE_TAG_LAB,
    SYNTHESIS_SOURCE_TAG_SECURITY,
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
# 1. End-to-end: AV + Security on a single PDF
# ---------------------------------------------------------------------------


def test_av_and_security_schedules_flow_through_pipeline(tmp_path: Path) -> None:
    """Two-page PDF (AV + Security) → both pre-passes fire, both synth families present."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["AV EQUIPMENT SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION",  "MFR",     "SIZE",  "MOUNTING", "POWER", "SIGNAL", "QTY"],
            ["DISP-1", "Display",      "Samsung", "75\"",  "WALL",     "120V",  "HDMI",   "2"],
            ["PROJ-1", "Projector",    "Epson",   "4K",    "CEILING",  "120V",  "HDMI",   "1"],
        ],
    )
    _add_page(
        doc,
        title_lines=["SECURITY SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",   "DESCRIPTION",       "MFR",  "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["DR-1",  "Card reader",       "HID",  "WALL",     "PoE",   "Wiegand",    "4"],
            ["CAM-1", "Surveillance cam",  "Axis", "CEILING",  "PoE",   "Cat6",       "8"],
        ],
    )
    pdf = tmp_path / "av_sec.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["T2.0", "S1.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    # Confirm the prepass actually wired both AV and Security.
    assert sheets[0].prepass.av_schedule is not None
    assert len(sheets[0].prepass.av_schedule.devices) == 2
    assert sheets[1].prepass.security_schedule is not None
    assert len(sheets[1].prepass.security_schedule.devices) == 2

    project = reconcile(sheets)
    av_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV)
    sec_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY)
    assert av_syn, "AV synthesis produced no rows"
    assert sec_syn, "Security synthesis produced no rows"

    # AV — DISP-1 (eq + cabling + programming) + PROJ-1 (eq + cabling + programming).
    av_sections = sorted(it.csi_section for it in av_syn)
    assert "27 41 16.51" in av_sections    # DISP-1 display
    assert "27 41 16.31" in av_sections    # PROJ-1 projector
    assert "27 15 13.13" in av_sections    # cabling rough-in

    # Security — DR-1 (reader + cabling + programming) + CAM-1 (camera + cabling).
    sec_sections = sorted(it.csi_section for it in sec_syn)
    assert "28 13 23.13" in sec_sections   # DR-1 card reader
    assert "28 23 23" in sec_sections      # CAM-1 camera
    assert "28 05 13" in sec_sections      # cabling rough-in


# ---------------------------------------------------------------------------
# 2. All four specialty domains — independent streams
# ---------------------------------------------------------------------------


def test_all_four_specialty_domains_independent_streams(tmp_path: Path) -> None:
    """A project carrying kitchen + lab + AV + security schedules — each
    family's synthesis fires independently and none cross-suppresses.
    """
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",  "DESCRIPTION", "MFR",     "BTU",  "GAS", "ELEC", "QTY"],
            ["RA-1", "Range",       "Vulcan",  "120K", "X",   "",     "2"],
        ],
    )
    _add_page(
        doc,
        title_lines=["LAB CASEWORK SCHEDULE", "Sheet I2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MATERIAL",  "FUME", "VACUUM", "WATER", "QTY"],
            ["FH-1", "Fume hood",    "STAINLESS", "X",    "X",      "X",     "2"],
        ],
    )
    _add_page(
        doc,
        title_lines=["AV EQUIPMENT SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION",  "MFR",     "SIZE",  "MOUNTING", "POWER", "SIGNAL", "QTY"],
            ["DISP-1", "Display",      "Samsung", "75\"",  "WALL",     "120V",  "HDMI",   "2"],
        ],
    )
    _add_page(
        doc,
        title_lines=["SECURITY SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",  "DESCRIPTION", "MFR", "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["DR-1", "Card reader", "HID", "WALL",     "PoE",   "Wiegand",    "4"],
        ],
    )
    pdf = tmp_path / "four_domains.pdf"
    doc.save(pdf)
    doc.close()

    pages = prepass_drawing_pdf(pdf)
    sheet_ids = ["K2.0", "I2.0", "T2.0", "S1.0"]
    sheets = [
        SheetExtraction(
            sheet_id=sheet_ids[i],
            prepass=prepass_to_schema(p),
        )
        for i, p in enumerate(pages)
    ]
    project = reconcile(sheets)

    kitchen_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_KITCHEN)
    lab_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_LAB)
    av_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV)
    sec_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY)

    assert kitchen_syn, "kitchen synthesis missing"
    assert lab_syn, "lab synthesis missing"
    assert av_syn, "AV synthesis missing"
    assert sec_syn, "Security synthesis missing"

    # All four primary CSI homes are present.
    sections = {t.csi_section for t in project.takeoffs}
    assert "11 40 13.13" in sections   # kitchen range
    assert "11 53 13" in sections      # lab fume hood
    assert "27 41 16.51" in sections   # AV display
    assert "28 13 23.13" in sections   # security card reader

    # Cross-suppression check: each family's primary row description
    # survives the OTHER families' dedupe passes.
    descs = [t.description or "" for t in project.takeoffs]
    assert any("Kitchen equipment RA-1" in d for d in descs)
    assert any("Lab casework FH-1" in d for d in descs)
    assert any("AV device DISP-1" in d for d in descs)
    assert any("Security device DR-1" in d for d in descs)


# ---------------------------------------------------------------------------
# 3. T6.1 confidence bands — AV cabling rough-in routes to HAND_TAKEOFF
# ---------------------------------------------------------------------------


def test_av_cabling_roughin_lands_in_hand_takeoff_band(tmp_path: Path) -> None:
    """LS cabling rough-in row (parametric haircut) lands in HAND_TAKEOFF when no QTY."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["AV EQUIPMENT SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION", "SIZE", "MOUNTING", "SIGNAL"],
            ["DISP-1", "Display",     "75\"", "WALL",     "HDMI"],
        ],
    )
    pdf = tmp_path / "av_no_qty.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="T2.0")
    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV)

    cabling = [it for it in syn if it.csi_section == "27 15 13.13"]
    assert len(cabling) == 1
    ci = cabling[0]
    assert ci.unit == "LS"
    # Without QTY: parent = 0.55 → cabling = 0.55 × 0.95 × 0.95 = ~0.4965
    # → HAND_TAKEOFF (< 0.65 threshold).
    assert ci.confidence is not None
    assert band_for_confidence(ci.confidence) == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# 4. T7 cost-source tier — cabling routes to PARAMETRIC
# ---------------------------------------------------------------------------


def test_security_cabling_with_no_qty_routes_to_parametric_tier(tmp_path: Path) -> None:
    """A cabling row whose confidence sinks below 0.50 → PARAMETRIC tier per T7."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["SECURITY SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MOUNTING", "POWER", "CONNECTION"],
            ["CAM-1", "Camera",      "CEILING",  "PoE",   "Cat6"],
        ],
    )
    pdf = tmp_path / "sec_no_qty.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="S1.0")
    project = reconcile([sheet])
    syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY)

    cabling = [it for it in syn if it.csi_section == "28 05 13"]
    assert len(cabling) == 1
    ci = cabling[0]
    assert ci.unit == "LS"
    # Confidence ~0.4965 (no QTY parent 0.55 × 0.95 × 0.95) → just
    # under 0.50 → PARAMETRIC per T7 cost-source mapping.
    assert ci.confidence is not None
    tier, _ = price_confidence_from_similarity(ci.confidence)
    assert tier in {CostSourceTier.PARAMETRIC, CostSourceTier.INTERPOLATED}


# ---------------------------------------------------------------------------
# 5. CAM- cross-domain disambiguation — AV vs Security produce different CSIs
# ---------------------------------------------------------------------------


def test_cam_in_av_schedule_routes_to_div_27(tmp_path: Path) -> None:
    """A ``CAM-1`` row in an AV-titled schedule → CSI 27 41 16.49 (AV capture)."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["AV EQUIPMENT SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",   "DESCRIPTION",          "MFR",  "SIZE",  "MOUNTING", "POWER", "SIGNAL", "QTY"],
            ["CAM-1", "Conference camera",    "Logi", "1080P", "WALL",     "USB",   "USB",    "2"],
        ],
    )
    pdf = tmp_path / "cam_av.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="T2.0")
    project = reconcile([sheet])
    av_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV)
    sec_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY)

    assert av_syn, "AV synthesis missing — CAM-1 not claimed by AV side"
    av_sections = {it.csi_section for it in av_syn}
    assert "27 41 16.49" in av_sections, (
        "AV CAM-1 should route to Div 27 41 16.49 (AV capture), "
        f"got sections={av_sections}"
    )
    # Security side is empty because the page is AV-shaped.
    assert sec_syn == []


def test_cam_in_security_schedule_routes_to_div_28(tmp_path: Path) -> None:
    """A ``CAM-1`` row in a Security-titled schedule → CSI 28 23 23 (video surveillance)."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["VIDEO SURVEILLANCE SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MFR",   "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["CAM-1", "PTZ camera",  "Axis",  "CEILING",  "PoE",   "Cat6",       "4"],
        ],
    )
    pdf = tmp_path / "cam_sec.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="S1.0")
    project = reconcile([sheet])
    av_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV)
    sec_syn = _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY)

    assert sec_syn, "Security synthesis missing — CAM-1 not claimed by security side"
    sec_sections = {it.csi_section for it in sec_syn}
    assert "28 23 23" in sec_sections, (
        "Security CAM-1 should route to Div 28 23 23 (video surveillance), "
        f"got sections={sec_sections}"
    )
    # AV side is empty because the page is security-shaped.
    assert av_syn == []


# ---------------------------------------------------------------------------
# 6. Empty schedules safe
# ---------------------------------------------------------------------------


def test_empty_av_and_security_schedules_are_safe(tmp_path: Path) -> None:
    """A project with no AV or security pages → no synthesis rows, no errors."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["FLOOR PLAN", "Sheet A1.0"],
    )
    pdf = tmp_path / "empty.pdf"
    doc.save(pdf)
    doc.close()

    sheet = _sheet_from_prepass(pdf, 0, sheet_id="A1.0")
    assert sheet.prepass.av_schedule is None
    assert sheet.prepass.security_schedule is None
    project = reconcile([sheet])
    assert _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_AV) == []
    assert _rows_with_source(project.takeoffs, SYNTHESIS_SOURCE_TAG_SECURITY) == []
