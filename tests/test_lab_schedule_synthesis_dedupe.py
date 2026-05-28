"""Tests for Phase T2.10 lab casework — extraction + synthesis + dedupe.

Combined file because the lab side is structurally simpler than the
kitchen side (no BTU / voltage axes, no hood ductwork bifurcation):
covering extraction, synthesis fan-out, and dedupe in one place keeps
the lab story readable.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.lab_casework_schedule import (
    LabCaseworkRecord,
    LabScheduleResult,
    _classify_item_type,
    _flag_from_cell,
    _normalize_material,
    _parse_inches,
    _parse_quantity,
    _parse_size_triple,
    detect_lab_schedule_page,
    extract_lab_schedule_from_page,
    to_schema,
)
from core.extraction.lab_dedupe import dedupe_lab_against_synthesis
from core.extraction.takeoff_synthesis import (
    DERIVATION_HAIRCUT_MULTIPLIER,
    SYNTHESIS_SOURCE_TAG_LAB,
    inherit_with_haircut,
    synthesize_lab_takeoff_items,
)
from core.schemas import CostBand, TakeoffItem, band_for_confidence


# ---------------------------------------------------------------------------
# Synthetic PDF helpers
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


def _extract_one(pdf: Path) -> LabScheduleResult:
    with fitz.open(pdf) as d:
        return extract_lab_schedule_from_page(d[0], 0)


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------


def _base_cabinet() -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="BC-1",
        item_type="BASE_CABINET",
        description="36\" base cabinet",
        material="EPOXY",
        quantity=4,
    )


def _wall_cabinet() -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="WC-1",
        item_type="WALL_CABINET",
        description="36\" wall cabinet",
        material="EPOXY",
        quantity=4,
    )


def _fume_hood(mfr: str | None = None, model: str | None = None) -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="FH-1",
        item_type="FUME_HOOD",
        description="6' bench-top fume hood",
        manufacturer=mfr,
        model_number=model,
        utility_gas=True,
        utility_vacuum=True,
        utility_water=True,
        utility_electric=True,
        quantity=2,
    )


def _eyewash() -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="EW-1",
        item_type="EYEWASH_STATION",
        description="Wall-mount combination eyewash/drench",
        utility_water=True,
        quantity=1,
    )


def _safety_cabinet() -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="SC-1",
        item_type="SAFETY_CABINET",
        description="Flammable storage cabinet",
        quantity=2,
    )


def _lab_bench() -> LabCaseworkRecord:
    return LabCaseworkRecord(
        tag="LB-1",
        item_type="LAB_BENCH",
        description="Lab bench, phenolic top",
        material="PHENOLIC",
        utility_electric=True,
        quantity=3,
    )


def _llm(description: str, *, csi_section: str | None = "12 35 53",
         csi_division: str = "12") -> TakeoffItem:
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=1.0,
        unit="EA",
        confidence=0.7,
    )


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


def test_detect_lab_casework_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_lab_phrase.pdf",
        title_lines=["LAB CASEWORK SCHEDULE", "Sheet I2.0"],
        table=[
            ["TAG",  "DESCRIPTION", "MATERIAL", "FUME", "VACUUM"],
            ["BC-1", "Base cab",    "EPOXY",    "-",    "-"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_lab_schedule_page(d[0]) is True


def test_detect_laboratory_furniture_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_lab_furniture.pdf",
        title_lines=["LABORATORY FURNITURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "MATERIAL", "FUME"],
            ["LB-1", "Lab bench",   "EPOXY",    "-"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_lab_schedule_page(d[0]) is True


def test_detect_fume_hood_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_fume_hood.pdf",
        title_lines=["FUME HOOD SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "MFR",       "FUME", "VACUUM"],
            ["FH-1", "6' Fume hood","Labconco",  "X",    "X"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_lab_schedule_page(d[0]) is True


def test_detect_rejects_plumbing_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_plumbing_lab.pdf",
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "GPF",  "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "1.28", "1/2\"",  "4\""],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_lab_schedule_page(d[0]) is False


# ---------------------------------------------------------------------------
# Classifier
# ---------------------------------------------------------------------------


def test_classify_base_cabinet_prefix() -> None:
    assert _classify_item_type("BC-1") == "BASE_CABINET"
    assert _classify_item_type("BCAB-1") == "BASE_CABINET"


def test_classify_wall_cabinet_prefix() -> None:
    assert _classify_item_type("WC-1") == "WALL_CABINET"


def test_classify_tall_cabinet_prefix() -> None:
    assert _classify_item_type("TC-1") == "TALL_CABINET"
    assert _classify_item_type("TCAB-1") == "TALL_CABINET"


def test_classify_fume_hood_prefix() -> None:
    assert _classify_item_type("FH-1") == "FUME_HOOD"


def test_classify_lab_bench_prefix() -> None:
    assert _classify_item_type("LB-1") == "LAB_BENCH"


def test_classify_safety_cabinet_prefix() -> None:
    assert _classify_item_type("SC-1") == "SAFETY_CABINET"


def test_classify_eyewash_prefix() -> None:
    assert _classify_item_type("EW-1") == "EYEWASH_STATION"


def test_classify_fallback_to_description() -> None:
    assert _classify_item_type("X-1", "Fume hood") == "FUME_HOOD"
    assert _classify_item_type("X-2", "Eyewash station") == "EYEWASH_STATION"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


def test_parse_inches_simple_lab() -> None:
    assert _parse_inches("36") == 36.0
    assert _parse_inches('36"') == 36.0


def test_parse_size_triple_lab() -> None:
    w, d, h = _parse_size_triple("36 x 22 x 35")
    assert w == 36.0 and d == 22.0 and h == 35.0


def test_parse_quantity_lab() -> None:
    assert _parse_quantity("3") == 3


def test_flag_from_cell_lab() -> None:
    assert _flag_from_cell("X") is True
    assert _flag_from_cell("VACUUM") is True
    assert _flag_from_cell("-") is False
    assert _flag_from_cell(None) is None


def test_material_normalizer() -> None:
    assert _normalize_material("epoxy") == "EPOXY"
    assert _normalize_material("PHENOLIC") == "PHENOLIC"
    assert _normalize_material("Stainless") == "STAINLESS"
    assert _normalize_material("-") is None


# ---------------------------------------------------------------------------
# Extractor end-to-end
# ---------------------------------------------------------------------------


def test_extract_single_base_cabinet(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "single_bc.pdf",
        title_lines=["LAB CASEWORK SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",   "MATERIAL", "WIDTH", "DEPTH"],
            ["BC-1", "Base cabinet",  "EPOXY",    "36",    "22"],
        ],
    )
    r = _extract_one(pdf).casework
    assert len(r) == 1
    rec = r[0]
    assert rec.tag == "BC-1"
    assert rec.item_type == "BASE_CABINET"
    assert rec.material == "EPOXY"
    assert rec.width_in == 36.0


def test_extract_multi_record_lab(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "multi_lab.pdf",
        title_lines=["LAB CASEWORK SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "MATERIAL",  "FUME", "VACUUM", "WATER", "QTY"],
            ["BC-1", "Base cabinet", "EPOXY",     "-",    "-",      "-",     "4"],
            ["WC-1", "Wall cabinet", "EPOXY",     "-",    "-",      "-",     "4"],
            ["FH-1", "6' Fume hood", "STAINLESS", "X",    "X",      "X",     "2"],
            ["LB-1", "Lab bench",    "PHENOLIC",  "-",    "-",      "-",     "3"],
        ],
    )
    recs = _extract_one(pdf).casework
    by_type = {r.item_type for r in recs}
    assert by_type == {"BASE_CABINET", "WALL_CABINET", "FUME_HOOD", "LAB_BENCH"}


# ---------------------------------------------------------------------------
# Schema round-trip
# ---------------------------------------------------------------------------


def test_to_schema_round_trip() -> None:
    rec = LabCaseworkRecord(
        tag="FH-1", item_type="FUME_HOOD",
        description="6' bench-top",
        manufacturer="Labconco", model_number="1166000",
        material="STAINLESS",
        utility_gas=True, utility_vacuum=True,
        quantity=2, confidence=0.9, source_page=4,
    )
    bridge = to_schema(LabScheduleResult(
        pages=[4], casework=[rec], confidence=0.85, raw_table_text="",
    ))
    assert bridge.pages == [4]
    assert bridge.casework[0].tag == "FH-1"
    assert bridge.casework[0].item_type == "FUME_HOOD"
    assert bridge.casework[0].manufacturer == "Labconco"


# ---------------------------------------------------------------------------
# Synthesis — shape + CSI mapping
# ---------------------------------------------------------------------------


def test_synthesize_empty_returns_empty() -> None:
    assert synthesize_lab_takeoff_items(None) == []
    assert synthesize_lab_takeoff_items([]) == []
    assert synthesize_lab_takeoff_items(LabScheduleResult(casework=[])) == []


def test_synthesize_base_cabinet_routes_to_12_35_53_13() -> None:
    items = synthesize_lab_takeoff_items([_base_cabinet()])
    assert items[0].csi_section == "12 35 53.13"
    # No utilities → no rough-in; no mfr/model → no trim.
    assert len(items) == 1


def test_synthesize_wall_cabinet_routes_to_12_35_53_13() -> None:
    items = synthesize_lab_takeoff_items([_wall_cabinet()])
    assert items[0].csi_section == "12 35 53.13"


def test_synthesize_lab_bench_with_electric_routes_to_26_27_26_roughin() -> None:
    items = synthesize_lab_takeoff_items([_lab_bench()])
    assert len(items) == 2
    eq, roughin = items
    assert eq.csi_section == "12 35 53.13"
    assert roughin.csi_section == "26 27 26"


def test_synthesize_fume_hood_routes_to_11_53_13_with_water_roughin() -> None:
    """Fume hood with utilities → 3 items: hood + utility rough-in + NO trim line.

    FUME_HOOD is in _LAB_TRIM_EXCLUDED — even with mfr+model the trim
    row is intentionally skipped (integrated trim per the brief).
    """
    items = synthesize_lab_takeoff_items([
        _fume_hood(mfr="Labconco", model="1166000"),
    ])
    assert len(items) == 2
    eq, roughin = items
    assert eq.csi_section == "11 53 13"
    assert roughin.csi_section == "22 11 16"  # piped utilities
    # No trim line — FUME_HOOD exclusion is exercised here.
    assert not any("trim" in (it.description or "").lower() for it in items)


def test_synthesize_safety_cabinet_routes_to_11_53_43() -> None:
    items = synthesize_lab_takeoff_items([_safety_cabinet()])
    assert items[0].csi_section == "11 53 43"


def test_synthesize_eyewash_routes_to_22_45_19_cross_division() -> None:
    items = synthesize_lab_takeoff_items([_eyewash()])
    assert items[0].csi_section == "22 45 19"
    assert items[0].csi_division == "22"
    # EYEWASH_STATION is trim-excluded, so even with mfr+model no trim.
    eyewash_with_mfr = LabCaseworkRecord(
        tag="EW-2", item_type="EYEWASH_STATION",
        description="Eyewash", manufacturer="Bradley", model_number="S19-220",
        utility_water=True, quantity=1,
    )
    items2 = synthesize_lab_takeoff_items([eyewash_with_mfr])
    # eyewash + water-side rough-in, but NO trim.
    assert not any("trim" in (it.description or "").lower() for it in items2)


def test_synthesize_other_falls_back_to_12_35_53() -> None:
    rec = LabCaseworkRecord(
        tag="X-1", item_type="OTHER", description="Mystery lab item",
    )
    items = synthesize_lab_takeoff_items([rec])
    assert items[0].csi_section == "12 35 53"


# ---------------------------------------------------------------------------
# Confidence inheritance — T6.1 verify
# ---------------------------------------------------------------------------


def test_lab_roughin_inherits_t61_haircut() -> None:
    items = synthesize_lab_takeoff_items([_lab_bench()])
    _, roughin = items
    assert roughin.confidence == inherit_with_haircut(0.90)


def test_lab_trim_inherits_double_haircut() -> None:
    """Trim row on a non-excluded type uses the 0.95 × 0.70 multiplier."""
    rec = LabCaseworkRecord(
        tag="BC-9", item_type="BASE_CABINET",
        description="Specialty base",
        manufacturer="ACME", model_number="ABC-100",
        utility_electric=True, quantity=1,
    )
    items = synthesize_lab_takeoff_items([rec])
    trim = [it for it in items if "trim" in (it.description or "").lower()]
    assert len(trim) == 1
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.70,
    )
    assert trim[0].confidence == expected


def test_lab_no_qty_lands_in_hand_takeoff_band() -> None:
    rec = LabCaseworkRecord(
        tag="BC-9", item_type="BASE_CABINET", description="Loose cab",
    )
    eq = synthesize_lab_takeoff_items([rec])[0]
    assert eq.confidence == 0.55
    assert band_for_confidence(eq.confidence) == CostBand.HAND_TAKEOFF


def test_lab_with_qty_lands_in_auto_approve_band() -> None:
    eq = synthesize_lab_takeoff_items([_base_cabinet()])[0]
    assert eq.confidence == 0.90
    assert band_for_confidence(eq.confidence) == CostBand.AUTO_APPROVE


# ---------------------------------------------------------------------------
# Notes / source tag
# ---------------------------------------------------------------------------


def test_lab_notes_carry_source_tag() -> None:
    items = synthesize_lab_takeoff_items([_lab_bench()])
    for it in items:
        assert (it.notes or "").startswith(
            f"source={SYNTHESIS_SOURCE_TAG_LAB}"
        )


def test_lab_description_prefix() -> None:
    items = synthesize_lab_takeoff_items([_lab_bench()])
    for it in items:
        assert (it.description or "").lower().startswith("lab casework")


# ---------------------------------------------------------------------------
# Dedupe
# ---------------------------------------------------------------------------


def _synth_fh() -> list[TakeoffItem]:
    return synthesize_lab_takeoff_items([_fume_hood()])


def test_dedupe_suppresses_lab_casework_aggregate() -> None:
    items = synthesize_lab_takeoff_items([_base_cabinet()]) + [
        _llm("Lab Casework"),
        _llm("Laboratory Furniture"),
        _llm("Laboratory Equipment"),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Lab Casework" not in descs
    assert "Laboratory Furniture" not in descs
    assert "Laboratory Equipment" not in descs


def test_dedupe_suppresses_fume_hood_aggregate() -> None:
    items = _synth_fh() + [
        _llm("Fume Hoods", csi_section="11 53 13", csi_division="11"),
        _llm("Laboratory Fume Hoods", csi_section="11 53 13", csi_division="11"),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Fume Hoods" not in descs
    assert "Laboratory Fume Hoods" not in descs


def test_dedupe_suppresses_per_mark_llm_row() -> None:
    items = synthesize_lab_takeoff_items([_base_cabinet()]) + [
        _llm("BC-1 base cabinet installation"),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "BC-1 base cabinet installation" not in descs


def test_dedupe_preserves_general_div_6_millwork() -> None:
    """Generic Div 6 millwork rows survive — no 'lab' qualifier in the row."""
    items = synthesize_lab_takeoff_items([_base_cabinet()]) + [
        TakeoffItem(
            csi_division="06", csi_section="06 41 16",
            description="Custom millwork",
            quantity=1500.0, unit="SF", confidence=0.7,
        ),
        TakeoffItem(
            csi_division="06", csi_section="06 41 16",
            description="Plastic-laminate cabinets",
            quantity=20.0, unit="EA", confidence=0.75,
        ),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Custom millwork" in descs
    assert "Plastic-laminate cabinets" in descs


def test_dedupe_preserves_plumbing_water_closet_marked_wc() -> None:
    """A plumbing WC-1 row (CSI 22 41 13) is NEVER touched by lab dedupe.

    WC-1 is both a lab wall-cabinet tag AND a plumbing water-closet
    tag.  The CSI prefix discriminator + the absence of WC-\\d+ in
    the lab regex keep the two scopes disjoint.
    """
    items = synthesize_lab_takeoff_items([_base_cabinet()]) + [
        TakeoffItem(
            csi_division="22", csi_section="22 41 13",
            description="WC-1 water closet installation",
            quantity=1.0, unit="EA", confidence=0.8,
        ),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "WC-1 water closet installation" in descs


def test_dedupe_preserves_eyewash_division_22_row() -> None:
    """Eyewash CSI 22 45 19 is OUTSIDE lab dedupe scope.

    The lab synthesiser sends eyewashes to ``22 45 19``, but the
    lab dedupe scope is ``12 35`` + ``11 53`` only — Division 22
    rows are owned by the plumbing dedupe upstream and the lab
    dedupe never touches them.
    """
    items = synthesize_lab_takeoff_items([_eyewash()]) + [
        TakeoffItem(
            csi_division="22", csi_section="22 45 19",
            description="Eyewash equipment, contractor allowance",
            quantity=1.0, unit="LS", confidence=0.65,
        ),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Eyewash equipment, contractor allowance" in descs


def test_dedupe_no_op_when_no_lab_synthesis_present() -> None:
    items = [
        _llm("Lab Casework"),
        _llm("Fume Hoods"),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    assert len(survivors) == 2


def test_dedupe_preserves_doors_panels_lighting() -> None:
    items = synthesize_lab_takeoff_items([_base_cabinet()]) + [
        TakeoffItem(csi_division="08", csi_section="08 11 13",
                    description="Hollow metal door", quantity=1.0,
                    unit="EA", confidence=0.85),
        TakeoffItem(csi_division="26", csi_section="26 24 16.13",
                    description="Panelboard PNL-A", quantity=1.0,
                    unit="EA", confidence=0.85),
        TakeoffItem(csi_division="26", csi_section="26 51 13",
                    description="LED troffer", quantity=20.0,
                    unit="EA", confidence=0.85),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Hollow metal door" in descs
    assert "Panelboard PNL-A" in descs
    assert "LED troffer" in descs


def test_dedupe_preserves_kitchen_rows() -> None:
    """Division 11 40 (kitchen) is OUTSIDE lab dedupe scope (lab is 11 53)."""
    items = synthesize_lab_takeoff_items([_fume_hood()]) + [
        TakeoffItem(csi_division="11", csi_section="11 40 13.13",
                    description="Kitchen equipment RA-1 — Food Cooking",
                    quantity=1.0, unit="EA", confidence=0.9),
    ]
    survivors = dedupe_lab_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert any("Kitchen equipment RA-1" in d for d in descs)
