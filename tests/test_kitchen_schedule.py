"""Tests for the Phase T2.10 kitchen-equipment-schedule extractor.

Builds synthetic PDFs against ``extract_kitchen_schedule_from_page``
plus a handful of unit-level tests against the cell / header parsers.
Mirrors :mod:`tests.test_plumbing_schedule` for the kitchen family.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.kitchen_schedule import (
    KitchenEquipmentRecord,
    KitchenScheduleResult,
    _classify_item_type,
    _detect_utilities_from_text,
    _flag_from_cell,
    _kitchen_indices,
    _looks_like_kitchen_header,
    _parse_btu,
    _parse_inches,
    _parse_quantity,
    _parse_size_triple,
    _parse_voltage,
    detect_kitchen_schedule_page,
    extract_kitchen_schedule_from_page,
    to_schema,
)


# ---------------------------------------------------------------------------
# Synthetic-PDF helpers
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


def _extract_one(pdf: Path) -> KitchenScheduleResult:
    with fitz.open(pdf) as d:
        return extract_kitchen_schedule_from_page(d[0], 0)


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


def test_detect_page_with_kitchen_equipment_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_kitchen_phrase.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "GAS",  "BTU",   "ELEC", "QTY"],
            ["RA-1",  "RANGE",       "X",    "120K",  "120V", "1"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_kitchen_schedule_page(d[0]) is True


def test_detect_page_with_food_service_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_foodservice.pdf",
        title_lines=["FOOD SERVICE EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "GAS",  "ELEC", "BTU"],
            ["FRY-1", "FRYER",       "X",    "",     "90K"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_kitchen_schedule_page(d[0]) is True


def test_detect_page_with_foodservice_one_word(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_oneword.pdf",
        title_lines=["FOODSERVICE EQUIPMENT"],
        table=[
            ["TAG", "DESCRIPTION", "GAS", "BTU"],
            ["K-1", "RANGE", "X", "60K"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_kitchen_schedule_page(d[0]) is True


def test_detect_rejects_lighting_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_lighting.pdf",
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "WATTS", "LUMENS", "MOUNTING"],
            ["A1",  "LED TROFFER 4000K", "40",    "4000",   "RECESSED"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_kitchen_schedule_page(d[0]) is False


def test_detect_rejects_plumbing_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_plumbing.pdf",
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "GPF",  "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "1.28", "1/2\"",  "4\""],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_kitchen_schedule_page(d[0]) is False


# ---------------------------------------------------------------------------
# Item-type classifier
# ---------------------------------------------------------------------------


def test_classify_range_prefix() -> None:
    assert _classify_item_type("RA-1") == "RANGE"
    assert _classify_item_type("RANGE-2") == "RANGE"


def test_classify_fryer_prefix() -> None:
    assert _classify_item_type("FRY-1") == "FRYER"
    assert _classify_item_type("FRYER-2") == "FRYER"
    assert _classify_item_type("FR-3") == "FRYER"


def test_classify_oven_prefix() -> None:
    assert _classify_item_type("OV-1") == "OVEN"
    assert _classify_item_type("OVEN-2") == "OVEN"


def test_classify_refrigerator_prefix() -> None:
    assert _classify_item_type("REF-1") == "REFRIGERATOR"
    assert _classify_item_type("RF-2") == "REFRIGERATOR"


def test_classify_freezer_prefix() -> None:
    assert _classify_item_type("FZ-1") == "FREEZER"
    assert _classify_item_type("FRZ-2") == "FREEZER"


def test_classify_walkin_prefix() -> None:
    assert _classify_item_type("WI-1") == "WALK_IN"
    assert _classify_item_type("WIC-2") == "WALK_IN"
    assert _classify_item_type("WIF-3") == "WALK_IN"


def test_classify_ice_machine_prefix() -> None:
    assert _classify_item_type("IM-1") == "ICE_MACHINE"


def test_classify_dishwasher_prefix() -> None:
    assert _classify_item_type("DW-1") == "DISHWASHER"
    assert _classify_item_type("DSH-2") == "DISHWASHER"


def test_classify_hood_prefix() -> None:
    assert _classify_item_type("HD-1") == "HOOD"
    assert _classify_item_type("HOOD-2") == "HOOD"


def test_classify_exhaust_fan_prefix() -> None:
    assert _classify_item_type("EF-1") == "EXHAUST_FAN"


def test_classify_sink_prefix() -> None:
    assert _classify_item_type("SK-1") == "SINK"


def test_classify_generic_kitchen_prefix() -> None:
    assert _classify_item_type("K-1") == "OTHER"


def test_classify_fallback_to_description() -> None:
    assert _classify_item_type("X-1", "Walk-in cooler") == "WALK_IN"
    assert _classify_item_type("X-2", "Refrigerated case") == "REFRIGERATOR"
    assert _classify_item_type("X-3", "Ice machine") == "ICE_MACHINE"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


def test_parse_btu_plain_integer() -> None:
    assert _parse_btu("50000") == 50000


def test_parse_btu_comma_thousands() -> None:
    assert _parse_btu("120,000 BTU/H") == 120000
    assert _parse_btu("120,000 BTUH") == 120000
    assert _parse_btu("120,000") == 120000


def test_parse_btu_k_shorthand() -> None:
    assert _parse_btu("120K BTU") == 120000
    assert _parse_btu("60K") == 60000


def test_parse_btu_returns_none_for_garbage() -> None:
    assert _parse_btu(None) is None
    assert _parse_btu("") is None
    assert _parse_btu("N/A") is None


def test_parse_quantity_plain_integer() -> None:
    assert _parse_quantity("4") == 4
    assert _parse_quantity("10 EA") == 10


def test_parse_quantity_returns_none_for_blank() -> None:
    assert _parse_quantity(None) is None
    assert _parse_quantity("") is None
    assert _parse_quantity("N/A") is None


def test_parse_inches_simple() -> None:
    assert _parse_inches("36") == 36.0
    assert _parse_inches('36"') == 36.0


def test_parse_size_triple_with_height() -> None:
    w, d, h = _parse_size_triple("60 x 30 x 36")
    assert w == 60.0 and d == 30.0 and h == 36.0


def test_parse_size_triple_without_height() -> None:
    w, d, h = _parse_size_triple("48 x 30")
    assert w == 48.0 and d == 30.0 and h is None


def test_parse_voltage_120v() -> None:
    v = _parse_voltage("120V")
    assert v == "120V"


def test_parse_voltage_208v_phase() -> None:
    v = _parse_voltage("208V/1PH")
    assert v == "208V/1PH"


def test_parse_voltage_480v_3phase() -> None:
    v = _parse_voltage("480V/3PH")
    assert v == "480V/3PH"


def test_parse_voltage_returns_none_for_blank() -> None:
    assert _parse_voltage(None) is None
    assert _parse_voltage("") is None
    assert _parse_voltage("-") is None


def test_flag_from_cell_x_means_true() -> None:
    assert _flag_from_cell("X") is True
    assert _flag_from_cell("Y") is True
    assert _flag_from_cell("yes") is True


def test_flag_from_cell_dash_means_false() -> None:
    assert _flag_from_cell("-") is False
    assert _flag_from_cell("N/A") is False
    assert _flag_from_cell("NO") is False


def test_flag_from_cell_empty_means_unknown() -> None:
    assert _flag_from_cell(None) is None
    assert _flag_from_cell("") is None


def test_detect_utilities_from_text() -> None:
    flags = _detect_utilities_from_text("Gas connection required", None)
    assert flags["gas"] is True
    assert flags["water"] is None
    flags2 = _detect_utilities_from_text(None, "Water + drain rough-in")
    assert flags2["water"] is True
    assert flags2["drain"] is True


# ---------------------------------------------------------------------------
# Header heuristic
# ---------------------------------------------------------------------------


def test_looks_like_kitchen_header_accepts_btu_gas() -> None:
    assert _looks_like_kitchen_header(
        ["TAG", "DESCRIPTION", "BTU", "GAS", "ELEC"]
    ) is True


def test_looks_like_kitchen_header_rejects_lighting_headers() -> None:
    assert _looks_like_kitchen_header(
        ["TAG", "DESCRIPTION", "WATTS", "LUMENS"]
    ) is False


def test_looks_like_kitchen_header_rejects_lab_headers() -> None:
    assert _looks_like_kitchen_header(
        ["TAG", "DESCRIPTION", "FUME", "VACUUM"]
    ) is False


# ---------------------------------------------------------------------------
# Header-collision audit (T3.6 two-pass picker)
# ---------------------------------------------------------------------------


def test_header_picker_resolves_h_vs_height_collision() -> None:
    """``H`` substring-collides with ``HEIGHT``; long form must win.

    Audit decision: kept the local ``_header_index`` helper for the
    initial unrestricted tag lookup, and routed all collision-prone
    headers through the shared ``header_index_excluding`` helper.
    Verified here that ``HEIGHT`` claims its slot before ``H`` can.
    """
    headers = ["TAG", "DESCRIPTION", "WIDTH", "DEPTH", "HEIGHT", "H"]
    idx = _kitchen_indices(headers)
    assert idx["height"] == 4  # HEIGHT, not H


def test_header_picker_resolves_w_vs_width_collision() -> None:
    headers = ["TAG", "DESCRIPTION", "W", "WIDTH", "DEPTH"]
    idx = _kitchen_indices(headers)
    assert idx["width"] == 3  # WIDTH, not W


def test_header_picker_resolves_b_vs_btu_collision() -> None:
    headers = ["TAG", "DESCRIPTION", "B", "BTU"]
    idx = _kitchen_indices(headers)
    assert idx["btu"] == 3  # BTU, not B


def test_header_picker_resolves_q_vs_qty_collision() -> None:
    headers = ["TAG", "DESCRIPTION", "Q", "QTY"]
    idx = _kitchen_indices(headers)
    assert idx["qty"] == 3  # QTY, not Q


def test_header_picker_falls_back_to_short_form_when_long_missing() -> None:
    """When only ``H`` is present (no ``HEIGHT``), the short form wins."""
    headers = ["TAG", "DESCRIPTION", "W", "D", "H"]
    idx = _kitchen_indices(headers)
    assert idx["height"] == 4
    assert idx["width"] == 2
    # depth long-only — short form not configured for depth in this picker.
    assert idx["depth"] is None


# ---------------------------------------------------------------------------
# End-to-end extraction
# ---------------------------------------------------------------------------


def test_extract_single_range_record(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "single_range.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE", "Sheet K2.0"],
        table=[
            ["TAG",  "DESCRIPTION", "MFR",    "MODEL",   "BTU",  "GAS"],
            ["RA-1", "6-burner",    "Vulcan", "VHP660",  "120K", "X"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.equipment) == 1
    r = result.equipment[0]
    assert r.tag == "RA-1"
    assert r.item_type == "RANGE"
    assert r.manufacturer == "Vulcan"
    assert r.model_number == "VHP660"
    assert r.btu_rating == 120000
    assert r.utility_gas is True


def test_extract_multi_record_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "multi_record.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",   "MFR",      "BTU",  "GAS",  "ELEC", "QTY"],
            ["RA-1",  "Range",         "Vulcan",   "120K", "X",    "",     "1"],
            ["FRY-1", "Fryer",         "Pitco",    "150K", "X",    "",     "2"],
            ["REF-1", "Refrigerator",  "True",     "",     "",     "X",    "1"],
            ["WI-1",  "Walk-in cooler","Norlake",  "",     "",     "X",    "1"],
            ["DW-1",  "Dishwasher",    "Hobart",   "",     "",     "X",    "1"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.equipment) == 5
    by_type = {r.item_type for r in result.equipment}
    assert by_type == {
        "RANGE", "FRYER", "REFRIGERATOR", "WALK_IN", "DISHWASHER",
    }


def test_extract_qty_column_populates_quantity(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "qty.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "BTU", "GAS", "QTY"],
            ["RA-1", "Range",       "60K", "X",   "3"],
        ],
    )
    result = _extract_one(pdf)
    assert result.equipment[0].quantity == 3


def test_extract_voltage_implies_electric(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "voltage.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "VOLTAGE", "BTU", "GAS"],
            ["REF-1", "Refrigerator","120V",    "",    "-"],
        ],
    )
    result = _extract_one(pdf)
    r = result.equipment[0]
    assert r.voltage == "120V"
    assert r.utility_electric is True


def test_extract_btu_implies_gas(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "btu_gas.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "BTU"],
            ["RA-1", "Range",       "60K"],
        ],
    )
    result = _extract_one(pdf)
    assert result.equipment[0].utility_gas is True


def test_extract_notes_with_gas_keyword(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "notes_gas.pdf",
        title_lines=["KITCHEN EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "BTU", "GAS", "NOTES"],
            ["FR-1", "Fryer",       "",    "",    "Gas connection required"],
        ],
    )
    result = _extract_one(pdf)
    r = result.equipment[0]
    assert r.utility_gas is True


# ---------------------------------------------------------------------------
# to_schema round-trip
# ---------------------------------------------------------------------------


def test_to_schema_preserves_all_fields() -> None:
    rec = KitchenEquipmentRecord(
        tag="RA-1",
        item_type="RANGE",
        description="6-burner",
        manufacturer="Vulcan",
        model_number="VHP660",
        width_in=60.0,
        depth_in=30.0,
        height_in=36.0,
        btu_rating=120000,
        utility_gas=True,
        utility_electric=None,
        utility_water=None,
        utility_drain=None,
        voltage=None,
        quantity=2,
        notes="2-yr warranty",
        confidence=0.9,
        source_sheet="K2.0",
        source_page=3,
    )
    result = KitchenScheduleResult(
        pages=[3], equipment=[rec], confidence=0.85, raw_table_text="X",
    )
    bridge = to_schema(result)
    assert bridge.pages == [3]
    assert len(bridge.equipment) == 1
    b = bridge.equipment[0]
    assert b.tag == "RA-1"
    assert b.item_type == "RANGE"
    assert b.manufacturer == "Vulcan"
    assert b.model_number == "VHP660"
    assert b.width_in == 60.0
    assert b.btu_rating == 120000
    assert b.utility_gas is True
    assert b.quantity == 2
    assert b.confidence == 0.9
    assert b.source_sheet == "K2.0"
    assert bridge.confidence == 0.85
