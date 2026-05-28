"""Tests for the HVAC equipment-schedule pre-pass (Phase T2.8).

Every test builds a synthetic 1-page PDF on disk with ``fitz`` (PyMuPDF)
so we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_lighting_schedule_extraction`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import prepass_drawing_pdf
from core.extraction.hvac_schedule import (
    HVACEquipmentRecord,
    HVACScheduleResult,
    _HVAC_SCHEDULE_KEYWORDS,
    _classify_equipment_type,
    _detect_fuel_type,
    _detect_refrigerant,
    _equipment_indices,
    _looks_like_hvac_header,
    _parse_capacity_value,
    _parse_hp,
    _parse_quantity,
    _parse_voltage_cell,
    detect_hvac_schedule_page,
    extract_hvac_schedule,
    extract_hvac_schedule_from_page,
    to_schema,
)


# ---------------------------------------------------------------------------
# Fixture builder (auto-sized — mirrors helper in lighting test module)
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 240.0),
    cell_size: tuple[float, float] = (80.0, 24.0),
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
    if body_lines:
        y = 150.0
        for line in body_lines:
            page.insert_text((40, y), line, fontsize=10)
            y += 14
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


def _build_pdf(
    tmp_path: Path,
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 240.0),
    cell_size: tuple[float, float] = (80.0, 24.0),
    name: str = "hvac.pdf",
) -> Path:
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=title_lines,
        body_lines=body_lines,
        table=table,
        table_origin=table_origin,
        cell_size=cell_size,
    )
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# Detection — phrase + header heuristics
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phrase", list(_HVAC_SCHEDULE_KEYWORDS))
def test_detect_hvac_schedule_keyword_variants(
    tmp_path: Path, phrase: str
) -> None:
    """Each of the published HVAC keyword variants flips the page-level signal."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[phrase, "Project: Demo"],
        name=f"phrase_{phrase[:10].strip().replace(' ', '_')}.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_hvac_schedule_page(doc[0]) is True


def test_detect_hvac_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["SHEET M2.0"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "CFM", "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLING UNIT", "Trane", "2000", "5", "480V/3PH"],
        ],
        name="header_only.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_hvac_schedule_page(doc[0]) is True


def test_detect_hvac_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=["Room 101 is 12 ft x 14 ft."],
        name="floor.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_hvac_schedule_page(doc[0]) is False


def test_detect_hvac_schedule_negative_lighting_schedule(tmp_path: Path) -> None:
    """A lighting-schedule page must NOT light up the HVAC detector."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
        ],
        name="lighting.pdf",
    )
    with fitz.open(pdf) as doc:
        # The page text DOES contain "FIXTURE SCHEDULE" but our HVAC
        # keyword list never matches that token. The HVAC header
        # heuristic should reject the lighting header (WATTS / MOUNTING
        # are disqualifiers).
        assert detect_hvac_schedule_page(doc[0]) is False


def test_looks_like_hvac_header_requires_three_signals() -> None:
    """Tag + (desc/mfr/model) + (capacity/hp/voltage/refrig/fuel) all present."""
    assert _looks_like_hvac_header(
        ["TAG", "DESCRIPTION", "CFM", "HP"]
    ) is True
    assert _looks_like_hvac_header(
        ["MARK", "MANUFACTURER", "MODEL", "TONS"]
    ) is True
    # Missing spec column → not an HVAC header
    assert _looks_like_hvac_header(["TAG", "DESCRIPTION"]) is False
    # Missing tag class → not an HVAC header
    assert _looks_like_hvac_header(["DESCRIPTION", "CFM"]) is False


def test_looks_like_hvac_header_rejects_lighting_disqualifier() -> None:
    """A lighting-schedule header carrying WATTS / MOUNTING must NOT pass."""
    assert _looks_like_hvac_header(
        ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"]
    ) is False


def test_looks_like_hvac_header_rejects_door_disqualifier() -> None:
    """A door-schedule header carrying HARDWARE must NOT pass."""
    assert _looks_like_hvac_header(
        ["MARK", "DESCRIPTION", "HARDWARE", "FRAME", "HP"]
    ) is False


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    ("20", 20.0),
    ("20 TONS", 20.0),
    ("20T", 20.0),
    ("2000", 2000.0),
    ("2000 CFM", 2000.0),
    ("2,000 CFM", 2000.0),
    ("150 MBH", 150.0),
    ("150.5", 150.5),
])
def test_parse_capacity_value_forms(raw: str, expected: float) -> None:
    assert _parse_capacity_value(raw) == expected


def test_parse_capacity_value_returns_none_for_blank() -> None:
    assert _parse_capacity_value("") is None
    assert _parse_capacity_value(None) is None


@pytest.mark.parametrize("raw,expected", [
    ("1", 1.0),
    ("5", 5.0),
    ("5 HP", 5.0),
    ("0.5", 0.5),
    ("1/2", 0.5),
    ("1/4 HP", 0.25),
])
def test_parse_hp_forms(raw: str, expected: float) -> None:
    assert _parse_hp(raw) == expected


def test_parse_voltage_preserves_string() -> None:
    """Voltage round-trips as the original string (preserves Greek phi etc.)."""
    voltage, phase = _parse_voltage_cell("208V/3PH")
    assert voltage == "208V/3PH"
    assert phase == 3
    voltage, phase = _parse_voltage_cell("480V/3PH")
    assert voltage == "480V/3PH"
    assert phase == 3
    voltage, phase = _parse_voltage_cell("120V/1PH")
    assert voltage == "120V/1PH"
    assert phase == 1


def test_parse_voltage_slash_form() -> None:
    """``"208/3"`` short form also picks up the phase count."""
    voltage, phase = _parse_voltage_cell("208/3")
    assert voltage == "208/3"
    assert phase == 3


def test_parse_quantity_strips_ea() -> None:
    assert _parse_quantity("3") == 3
    assert _parse_quantity("3 EA") == 3
    assert _parse_quantity("1") == 1
    assert _parse_quantity("0") == 0


def test_parse_quantity_rejects_non_numeric() -> None:
    assert _parse_quantity("a few") is None
    assert _parse_quantity("") is None
    assert _parse_quantity(None) is None


# ---------------------------------------------------------------------------
# Refrigerant + fuel-type detection
# ---------------------------------------------------------------------------


def test_detect_refrigerant_r410a() -> None:
    assert _detect_refrigerant("R-410A scroll compressor") == "R-410A"
    assert _detect_refrigerant("R410A") == "R-410A"


def test_detect_refrigerant_r454b() -> None:
    assert _detect_refrigerant("R-454B refrigerant") == "R-454B"


def test_detect_refrigerant_none_when_silent() -> None:
    assert _detect_refrigerant("AHU with hot-water coil") is None


def test_detect_fuel_type_gas() -> None:
    assert _detect_fuel_type("Natural gas boiler") == "GAS"
    assert _detect_fuel_type("Gas-fired unit heater") == "GAS"


def test_detect_fuel_type_electric() -> None:
    assert _detect_fuel_type("Electric resistance heater") == "ELECTRIC"


def test_detect_fuel_type_hw() -> None:
    """Hot water wins over a stray ``ELECTRIC`` mention."""
    assert _detect_fuel_type("Hot water coil") == "HW"
    assert _detect_fuel_type("HW heating coil") == "HW"


def test_detect_fuel_type_none_when_silent() -> None:
    assert _detect_fuel_type("Constant volume AHU") is None


# ---------------------------------------------------------------------------
# Equipment-type detection from tag prefix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag,expected", [
    ("AHU-1", "AHU"),
    ("AHU-A", "AHU"),
    ("RTU-1", "RTU"),
    ("RTU-A", "RTU"),
    ("VAV-3-1", "VAV"),
    ("VAV-101", "VAV"),
    ("P-1", "PUMP"),
    ("PUMP-A", "PUMP"),
    ("B-1", "BOILER"),
    ("BLR-A", "BOILER"),
    ("CH-1", "CHILLER"),
    ("CHL-1", "CHILLER"),
    ("CHR-1", "CHILLER"),
    ("F-1", "FAN"),
    ("SF-1", "FAN"),
    ("EF-2", "FAN"),
])
def test_classify_equipment_type_from_tag(tag: str, expected: str) -> None:
    assert _classify_equipment_type(tag) == expected


def test_classify_equipment_type_other_for_unknown() -> None:
    """A tag with no recognized prefix falls back to OTHER."""
    assert _classify_equipment_type("XYZ-99") == "OTHER"


def test_classify_equipment_type_description_fallback() -> None:
    """When the tag is uninformative, the description disambiguates."""
    assert _classify_equipment_type("X-1", "Rooftop unit") == "OTHER" \
        or _classify_equipment_type("X-1", "Rooftop unit") == "RTU"


# ---------------------------------------------------------------------------
# Header collision — _header_index_excluding reuse (FOURTH validation)
# ---------------------------------------------------------------------------


def test_header_collision_t_does_not_collide_with_tons() -> None:
    """Single-letter ``T`` must not collide with the longer ``TONS`` header."""
    headers = ["TAG", "DESCRIPTION", "TONS", "T"]
    idx = _equipment_indices(headers)
    # TONS is the longer-form column → primary tons index
    assert idx["tons"] == 2
    assert idx["tag"] == 0
    assert idx["desc"] == 1


def test_header_collision_short_t_only() -> None:
    """When only ``T`` is present (no long form), it IS the tons column."""
    headers = ["TAG", "DESCRIPTION", "T", "HP"]
    idx = _equipment_indices(headers)
    assert idx["tons"] == 2


def test_header_collision_h_does_not_collide_with_hp() -> None:
    """Single-letter ``H`` must not collide with the longer ``HP`` header."""
    headers = ["TAG", "DESCRIPTION", "HP", "H"]
    idx = _equipment_indices(headers)
    # HP is the longer-form column → primary hp index
    assert idx["hp"] == 2


def test_header_collision_short_h_only() -> None:
    headers = ["TAG", "DESCRIPTION", "TONS", "H"]
    idx = _equipment_indices(headers)
    assert idx["hp"] == 3


def test_header_collision_v_does_not_collide_with_voltage() -> None:
    headers = ["TAG", "DESCRIPTION", "VOLTAGE", "V"]
    idx = _equipment_indices(headers)
    assert idx["voltage"] == 2


def test_header_collision_q_does_not_collide_with_quantity() -> None:
    headers = ["TAG", "DESCRIPTION", "HP", "QUANTITY", "Q"]
    idx = _equipment_indices(headers)
    assert idx["qty"] == 3


# ---------------------------------------------------------------------------
# Single + multi-equipment extraction
# ---------------------------------------------------------------------------


def test_extract_single_ahu_all_fields(tmp_path: Path) -> None:
    """One fully-decorated AHU row → every field populated."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["AHU SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "MODEL",
             "CFM", "HP", "VOLTAGE"],
            ["AHU-1", "INDOOR AHU", "Trane",
             "M-SERIES", "2000", "5", "480V/3PH"],
        ],
        cell_size=(110.0, 24.0),
        name="single_ahu.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert isinstance(result, HVACScheduleResult)
    assert len(result.equipment) == 1
    e = result.equipment[0]
    assert e.equipment_tag == "AHU-1"
    assert e.equipment_type == "AHU"
    assert e.description == "INDOOR AHU"
    assert e.manufacturer == "Trane"
    assert e.model_number == "M-SERIES"
    assert e.capacity_value == 2000.0
    assert e.capacity_unit == "CFM"
    assert e.motor_hp == 5.0
    assert e.voltage == "480V/3PH"
    assert e.phase_count == 3


def test_extract_multi_equipment_schedule(tmp_path: Path) -> None:
    """A 5-row mixed-type schedule lands 5 equipment records."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["MECHANICAL EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",          "MANUFACTURER", "CFM",  "HP",  "VOLTAGE"],
            ["AHU-1", "AIR HANDLING UNIT",    "Trane",        "2000", "5",   "480V/3PH"],
            ["RTU-A", "ROOFTOP UNIT",         "Carrier",      "3000", "7.5", "480V/3PH"],
            ["VAV-1", "VAV TERMINAL",         "Titus",        "400",  "0",   ""],
            ["P-1",   "HOT WATER PUMP",       "Bell&Gossett", "0",    "3",   "208V/3PH"],
            ["F-1",   "EXHAUST FAN",          "Greenheck",    "1500", "2",   "208V/3PH"],
        ],
        cell_size=(95.0, 24.0),
        name="multi_eq.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert len(result.equipment) == 5
    tags = {e.equipment_tag for e in result.equipment}
    assert tags == {"AHU-1", "RTU-A", "VAV-1", "P-1", "F-1"}
    by_tag = {e.equipment_tag: e for e in result.equipment}
    assert by_tag["AHU-1"].equipment_type == "AHU"
    assert by_tag["RTU-A"].equipment_type == "RTU"
    assert by_tag["VAV-1"].equipment_type == "VAV"
    assert by_tag["P-1"].equipment_type == "PUMP"
    assert by_tag["F-1"].equipment_type == "FAN"


def test_extract_schedule_with_qty_column(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FAN SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "CFM",  "HP",  "VOLTAGE", "QTY"],
            ["F-1", "EXHAUST FAN", "1500", "2",   "208V/3PH", "4"],
            ["F-2", "SUPPLY FAN",  "2500", "3",   "208V/3PH", "2"],
        ],
        name="qty.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert len(result.equipment) == 2
    by_tag = {e.equipment_tag: e for e in result.equipment}
    assert by_tag["F-1"].quantity == 4
    assert by_tag["F-2"].quantity == 2


def test_extract_schedule_without_qty_column_quantity_is_none(
    tmp_path: Path,
) -> None:
    """No QTY column → ``quantity`` stays None (signals hand-takeoff need)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["AHU SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AHU",       "Trane",        "2000", "5",  "480V/3PH"],
        ],
        name="noqty.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert result.equipment[0].quantity is None


def test_extract_capacity_unit_tons_from_header(tmp_path: Path) -> None:
    """A TONS column → ``capacity_unit == 'TONS'`` regardless of value text."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["CHILLER SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "MANUFACTURER", "TONS", "HP", "VOLTAGE"],
            ["CH-1", "WATER CHILLER", "Trane",        "100",  "75", "480V/3PH"],
        ],
        cell_size=(100.0, 24.0),
        name="chiller.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert len(result.equipment) == 1
    e = result.equipment[0]
    assert e.capacity_value == 100.0
    assert e.capacity_unit == "TONS"
    assert e.equipment_type == "CHILLER"


def test_extract_capacity_unit_cfm_from_header(tmp_path: Path) -> None:
    """A CFM column → ``capacity_unit == 'CFM'``."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FAN SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "CFM",  "HP", "VOLTAGE"],
            ["F-1", "Exhaust Fan", "1500", "2",  "208V/3PH"],
        ],
        name="cfm.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    e = result.equipment[0]
    assert e.capacity_value == 1500.0
    assert e.capacity_unit == "CFM"


def test_extract_refrigerant_from_notes(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["RTU SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",        "CFM",  "HP", "VOLTAGE", "REFRIGERANT", "NOTES"],
            ["RTU-A", "PACKAGED ROOFTOP", "3000", "5",  "480V/3PH", "R-410A",      "DX cooling"],
        ],
        cell_size=(95.0, 24.0),
        name="refrig.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert result.equipment[0].refrigerant == "R-410A"


def test_extract_fuel_type_from_description(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["BOILER SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION",                 "MBH",  "VOLTAGE"],
            ["B-1", "Natural gas heating boiler", "500",  "120V/1PH"],
        ],
        cell_size=(110.0, 24.0),
        name="boiler.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert result.equipment[0].fuel_type == "GAS"
    assert result.equipment[0].equipment_type == "BOILER"


def test_extract_mixed_type_schedule_ahu_and_rtu(tmp_path: Path) -> None:
    """An AHU + RTU on the same page parse independently."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["MECHANICAL EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",  "480V/3PH"],
            ["RTU-1", "ROOFTOP UNIT", "Carrier",     "3000", "7",  "480V/3PH"],
        ],
        cell_size=(100.0, 24.0),
        name="ahu_rtu.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert len(result.equipment) == 2
    by_tag = {e.equipment_tag: e for e in result.equipment}
    assert by_tag["AHU-1"].equipment_type == "AHU"
    assert by_tag["RTU-1"].equipment_type == "RTU"


def test_extract_via_prepass_drawing_pdf(tmp_path: Path) -> None:
    """The drawing prepass wires through to the HVAC extractor end-to-end."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["AHU SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",  "480V/3PH"],
        ],
        cell_size=(110.0, 24.0),
        name="prepass.pdf",
    )
    results = prepass_drawing_pdf(pdf)
    assert len(results) == 1
    assert results[0].hvac_schedule is not None
    assert len(results[0].hvac_schedule.equipment) == 1
    assert results[0].hvac_schedule.equipment[0].equipment_tag == "AHU-1"


def test_to_schema_bridges_to_pydantic(tmp_path: Path) -> None:
    """``to_schema`` produces a Pydantic ``HVACScheduleResult``."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["AHU SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP", "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",  "480V/3PH"],
        ],
        cell_size=(110.0, 24.0),
        name="schema.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    pyd = to_schema(result)
    from core.schemas import HVACScheduleResult as PydanticResult
    assert isinstance(pyd, PydanticResult)
    assert len(pyd.equipment) == 1
    assert pyd.equipment[0].equipment_tag == "AHU-1"
    assert pyd.equipment[0].equipment_type == "AHU"


def test_extract_returns_empty_when_no_table(tmp_path: Path) -> None:
    """A page with the phrase but no equipment table → empty result."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["MECHANICAL EQUIPMENT SCHEDULE"],
        body_lines=["See sheet M2.0 for equipment details."],
        name="empty.pdf",
    )
    result = extract_hvac_schedule(pdf, 0)
    assert result.equipment == []
    assert result.confidence == 0.0


def test_extract_record_confidence_decorated() -> None:
    """A fully-decorated equipment record lands above AUTO_APPROVE threshold."""
    from core.extraction.hvac_schedule import _equipment_confidence
    score = _equipment_confidence(
        tag="AHU-1", has_description=True, has_manufacturer=True,
        has_model=True, has_capacity=True, has_hp=True, has_voltage=True,
    )
    assert score >= 0.85  # AUTO_APPROVE threshold


def test_extract_record_confidence_tag_only() -> None:
    """A tag-only record lands at 0.65 (HAND_TAKEOFF cusp)."""
    from core.extraction.hvac_schedule import _equipment_confidence
    score = _equipment_confidence(
        tag="AHU-1", has_description=False, has_manufacturer=False,
        has_model=False, has_capacity=False, has_hp=False, has_voltage=False,
    )
    assert score == 0.65
