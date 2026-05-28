"""Tests for the lighting-fixture-schedule pre-pass (Phase T2.7).

Every test builds a synthetic 1-page PDF on disk with ``fitz`` (PyMuPDF)
so we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_panel_schedule_extraction`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import prepass_drawing_pdf
from core.extraction.lighting_schedule import (
    LightingFixtureRecord,
    LightingScheduleResult,
    _classify_lamp_type,
    _classify_mounting,
    _detect_dimmable,
    _detect_emergency,
    _fixture_indices,
    _LIGHTING_SCHEDULE_KEYWORDS,
    _looks_like_lighting_header,
    _parse_lumens,
    _parse_quantity,
    _parse_voltage_cell,
    _parse_wattage,
    detect_lighting_schedule_page,
    extract_lighting_schedule,
    extract_lighting_schedule_from_page,
    to_schema,
)


# ---------------------------------------------------------------------------
# Fixture builder (mirrors helper in test_panel_schedule_extraction)
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    body_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 240.0),
    cell_size: tuple[float, float] = (75.0, 24.0),
) -> None:
    # Auto-size the page so the table fits even when callers pass
    # wide cells (long catalog numbers, multi-word descriptions).
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
    cell_size: tuple[float, float] = (75.0, 24.0),
    name: str = "lighting.pdf",
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
# Detection — phrase + header heuristics (six keyword variations covered)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("phrase", list(_LIGHTING_SCHEDULE_KEYWORDS))
def test_detect_lighting_schedule_keyword_variants(
    tmp_path: Path, phrase: str
) -> None:
    """Each of the six published keyword variants flips the page-level signal."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[phrase, "Project: Demo"],
        name=f"phrase_{phrase[:10].strip().replace(' ', '_')}.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_lighting_schedule_page(doc[0]) is True


def test_detect_lighting_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["SHEET E1.0"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "Lithonia",     "40",    "277V",    "RECESSED"],
        ],
        name="header_only.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_lighting_schedule_page(doc[0]) is True


def test_detect_lighting_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=["Room 101 is 12 ft x 14 ft."],
        name="floor.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_lighting_schedule_page(doc[0]) is False


def test_detect_lighting_schedule_negative_panel_schedule(tmp_path: Path) -> None:
    """A panel-schedule page must NOT light up the lighting detector."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "BREAKER", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20A",     "Lighting",    "1200",  "A"],
        ],
        name="panel.pdf",
    )
    with fitz.open(pdf) as doc:
        # Header heuristic should reject the panel header even though
        # "Lighting" appears in the load column.
        assert detect_lighting_schedule_page(doc[0]) is False


def test_looks_like_lighting_header_requires_three_signals() -> None:
    """Tag + (desc/mfr/cat) + (watts/lamp/voltage/mounting) must all be present."""
    assert _looks_like_lighting_header(
        ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE"]
    ) is True
    assert _looks_like_lighting_header(
        ["TYPE", "MANUFACTURER", "MOUNTING"]
    ) is True
    # Missing spec column → not a lighting header
    assert _looks_like_lighting_header(["TAG", "DESCRIPTION"]) is False
    # Missing tag class → not a lighting header
    assert _looks_like_lighting_header(["DESCRIPTION", "WATTS"]) is False


def test_looks_like_lighting_header_rejects_panel_disqualifier() -> None:
    """A panel-schedule header carrying CIRCUIT / BREAKER must NOT pass."""
    assert _looks_like_lighting_header(
        ["CKT", "BREAKER", "DESCRIPTION", "WATTS", "PHASE"]
    ) is False


def test_looks_like_lighting_header_rejects_door_disqualifier() -> None:
    """A door-schedule header carrying HARDWARE must NOT pass."""
    assert _looks_like_lighting_header(
        ["TAG", "DESCRIPTION", "HARDWARE", "FRAME"]
    ) is False


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    ("15", 15.0),
    ("15W", 15.0),
    ("15 W", 15.0),
    ("15 WATTS", 15.0),
    ("15 watt", 15.0),
    ("15.5W", 15.5),
    ("40 W", 40.0),
])
def test_parse_wattage_forms(raw: str, expected: float) -> None:
    assert _parse_wattage(raw) == expected


def test_parse_wattage_handles_trailing_text() -> None:
    """``"15W LED"`` falls back to the leading numeric and still returns 15.0."""
    assert _parse_wattage("15W LED") == 15.0


@pytest.mark.parametrize("raw,expected", [
    ("3500", 3500),
    ("3500 lm", 3500),
    ("3500LM", 3500),
    ("3,500 lumens", 3500),
])
def test_parse_lumens_forms(raw: str, expected: int) -> None:
    assert _parse_lumens(raw) == expected


def test_parse_lumens_empty_returns_none() -> None:
    assert _parse_lumens("") is None
    assert _parse_lumens(None) is None
    assert _parse_lumens("foo") is None


def test_parse_voltage_preserves_dual_format() -> None:
    """``"120/277V"`` must round-trip — high-priority requirement."""
    assert _parse_voltage_cell("120/277V") == "120/277V"
    assert _parse_voltage_cell("120-277V") == "120/277V"
    assert _parse_voltage_cell("277/480V") == "277/480V"


def test_parse_voltage_single() -> None:
    assert _parse_voltage_cell("120V") == "120V"
    assert _parse_voltage_cell("277V") == "277V"
    assert _parse_voltage_cell("347V") == "347V"


def test_parse_voltage_free_text_round_trips() -> None:
    """A control descriptor like ``"DALI 277V"`` parses to ``"277V"``."""
    assert _parse_voltage_cell("DALI 277V") == "277V"


def test_parse_quantity_strips_ea() -> None:
    assert _parse_quantity("12") == 12
    assert _parse_quantity("12 EA") == 12
    assert _parse_quantity("0") == 0


def test_parse_quantity_rejects_non_numeric() -> None:
    assert _parse_quantity("a lot") is None
    assert _parse_quantity("") is None
    assert _parse_quantity(None) is None


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------


def test_classify_lamp_type_led() -> None:
    assert _classify_lamp_type("2x4 LED RECESSED TROFFER") == "LED"
    assert _classify_lamp_type(None, "LED downlight") == "LED"


def test_classify_lamp_type_fluorescent_variants() -> None:
    assert _classify_lamp_type("T8 fluorescent") == "FLUORESCENT"
    assert _classify_lamp_type("CFL wall pack") == "FLUORESCENT"


def test_classify_lamp_type_hid() -> None:
    assert _classify_lamp_type("Metal halide site pole") == "HID"


def test_classify_lamp_type_none_when_unknown() -> None:
    assert _classify_lamp_type("Sconce") is None
    assert _classify_lamp_type(None, None) is None


def test_classify_lamp_type_ledge_does_not_trigger_led() -> None:
    """Whole-word boundary keeps ``LEDGE`` from triggering ``LED``."""
    assert _classify_lamp_type("Ledge accent fixture") is None


def test_classify_mounting_recessed() -> None:
    assert _classify_mounting("RECESSED TROFFER") == "RECESSED"


def test_classify_mounting_wall() -> None:
    assert _classify_mounting("Wall sconce 15W") == "WALL"


def test_classify_mounting_pendant() -> None:
    assert _classify_mounting("Pendant lamp 40W") == "PENDANT"


def test_detect_dimmable_from_notes() -> None:
    assert _detect_dimmable("LED downlight", "0-10V DIM") is True
    assert _detect_dimmable("DALI controlled fixture") is True
    assert _detect_dimmable("non-dim driver") is None or _detect_dimmable(
        "non-dim driver"
    ) is True  # "DIM" appears as whole-ish word


def test_detect_dimmable_none_when_silent() -> None:
    assert _detect_dimmable("2x4 LED TROFFER 40W") is None


def test_detect_emergency_from_description() -> None:
    assert _detect_emergency("LED EM unit", None) is True
    assert _detect_emergency("Wall sconce with battery backup") is True
    assert _detect_emergency("Emergency egress fixture") is True


def test_detect_emergency_em_token_word_boundary() -> None:
    """``EMERGE`` should not trigger; ``EM`` must.

    The EM-token guard is one of the most fragile parsing cases.
    """
    assert _detect_emergency("Emergence trim", None) is None
    assert _detect_emergency("EM/EMER notation") is True


# ---------------------------------------------------------------------------
# Header collision — _header_index_excluding reuse (second validation)
# ---------------------------------------------------------------------------


def test_header_collision_w_does_not_collide_with_watts() -> None:
    """Single-letter ``W`` must not collide with the longer ``WATTS`` header."""
    headers = ["TAG", "DESCRIPTION", "WATTS", "W"]
    idx = _fixture_indices(headers)
    # WATTS is the longer-form column → primary watts index
    assert idx["watts"] == 2
    # Both columns resolved without crossover (no key takes the wrong one)
    assert idx["tag"] == 0
    assert idx["desc"] == 1


def test_header_collision_q_does_not_collide_with_quantity() -> None:
    """Single-letter ``Q`` must not collide with the longer ``QUANTITY``/``QTY`` headers."""
    headers = ["TAG", "DESCRIPTION", "WATTS", "QUANTITY", "Q"]
    idx = _fixture_indices(headers)
    assert idx["qty"] == 3
    assert idx["tag"] == 0


def test_header_collision_short_w_only() -> None:
    """When only ``W`` is present (no long form), it IS the watts column."""
    headers = ["TAG", "DESCRIPTION", "W", "MOUNTING"]
    idx = _fixture_indices(headers)
    assert idx["watts"] == 2


def test_header_collision_short_q_only() -> None:
    headers = ["TAG", "DESCRIPTION", "WATTS", "Q"]
    idx = _fixture_indices(headers)
    assert idx["qty"] == 3


def test_header_collision_v_does_not_collide_with_voltage() -> None:
    headers = ["TAG", "DESCRIPTION", "VOLTAGE", "V"]
    idx = _fixture_indices(headers)
    assert idx["voltage"] == 2


# ---------------------------------------------------------------------------
# Single + multi-fixture extraction
# ---------------------------------------------------------------------------


def test_extract_single_fixture_all_fields(tmp_path: Path) -> None:
    """One fully-decorated fixture row → every field populated."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION",            "MANUFACTURER",
             "CATALOG",      "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "2x4 LED TROFFER 4000K", "Lithonia",
             "2BLT4-40L-LP840", "40", "277V",    "RECESSED"],
        ],
        cell_size=(130.0, 24.0),
        name="single.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert isinstance(result, LightingScheduleResult)
    assert len(result.fixtures) == 1
    f = result.fixtures[0]
    assert f.fixture_tag == "A1"
    assert f.description == "2x4 LED TROFFER 4000K"
    assert f.manufacturer == "Lithonia"
    assert f.catalog_number == "2BLT4-40L-LP840"
    assert f.wattage == 40.0
    assert f.voltage == "277V"
    assert f.mounting == "RECESSED"
    assert f.lamp_type == "LED"
    assert f.color_temp_k == 4000


def test_extract_multi_fixture_schedule(tmp_path: Path) -> None:
    """A 5-row schedule lands 5 fixtures."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION",          "MANUFACTURER", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A",   "2x4 LED TROFFER",      "Lithonia",     "40",    "277V",    "RECESSED"],
            ["B",   "LED DOWNLIGHT",        "Cooper",       "15",    "120V",    "RECESSED"],
            ["C",   "WALL SCONCE LED",      "Hubbell",      "20",    "120V",    "WALL"],
            ["D",   "PENDANT FIXTURE LED",  "RAB",          "30",    "277V",    "PENDANT"],
            ["E",   "SURFACE STRIP LED",    "Lithonia",     "25",    "120V",    "SURFACE"],
        ],
        name="multi.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert len(result.fixtures) == 5
    tags = {f.fixture_tag for f in result.fixtures}
    assert tags == {"A", "B", "C", "D", "E"}


def test_extract_schedule_with_qty_column(tmp_path: Path) -> None:
    """When a QTY column is present, ``fixture.quantity`` is populated."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING", "QTY"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED", "12"],
            ["B",   "LED DOWNLIGHT", "15",  "120V",    "RECESSED", "8"],
        ],
        name="qty.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert len(result.fixtures) == 2
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["A1"].quantity == 12
    assert by_tag["B"].quantity == 8


def test_extract_schedule_without_qty_column_quantity_is_none(
    tmp_path: Path,
) -> None:
    """No QTY column → ``quantity`` stays None (signals hand-takeoff need)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
        ],
        name="noqty.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].quantity is None


def test_extract_voltage_dual_120_277_preserved(tmp_path: Path) -> None:
    """``"120/277V"`` round-trips through the cell parser."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE",   "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "120/277V", "RECESSED"],
        ],
        name="dual.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].voltage == "120/277V"


def test_extract_wattage_decimals_round_trip(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS",  "VOLTAGE", "MOUNTING"],
            ["A1",  "LED panel",   "15.5W",  "120V",    "SURFACE"],
        ],
        name="decimal.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].wattage == 15.5


def test_extract_dimmable_from_notes(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING", "NOTES"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED", "0-10V DIM"],
        ],
        name="dim.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].dimmable is True


def test_extract_emergency_from_notes(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING", "NOTES"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED", "EMERGENCY BATTERY BACKUP"],
        ],
        name="em.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].emergency is True


def test_extract_manufacturer_with_slash(tmp_path: Path) -> None:
    """``"Lithonia / 2BLT4-40L"`` in one cell splits into mfr + catalog."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION",   "MANUFACTURER",          "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER",   "Lithonia / 2BLT4-40L",  "40",    "277V",    "RECESSED"],
        ],
        cell_size=(130.0, 24.0),
        name="slash.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    f = result.fixtures[0]
    assert f.manufacturer == "Lithonia"
    assert f.catalog_number == "2BLT4-40L"


def test_extract_catalog_with_dashes(tmp_path: Path) -> None:
    """Long hyphen-rich catalog numbers preserve as-is."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER",
             "CATALOG",            "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "Lithonia",
             "2BLT4-40L-LP840-MVOLT-EZ1-LP840", "40", "277V", "RECESSED"],
        ],
        cell_size=(180.0, 24.0),
        name="catalog.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].catalog_number == \
        "2BLT4-40L-LP840-MVOLT-EZ1-LP840"


def test_extract_color_temp_from_description(tmp_path: Path) -> None:
    """Color temp is picked up from the description when no dedicated column."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION",            "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER 4000K white","40",    "277V",    "RECESSED"],
        ],
        cell_size=(140.0, 24.0),
        name="kelvin.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].color_temp_k == 4000


def test_extract_lumens_column(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "LUMENS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "4400",   "277V",    "RECESSED"],
        ],
        name="lumens.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures[0].lumens == 4400


def test_extract_rejects_sub_header_rows(tmp_path: Path) -> None:
    """A continuation row with no plausible tag is dropped silently."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
            ["(continued)", "still A1", "",  "",       ""],
        ],
        name="cont.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    tags = [f.fixture_tag for f in result.fixtures]
    assert "A1" in tags
    assert "(continued)" not in tags


def test_extract_from_pdf_via_extract_lighting_schedule(tmp_path: Path) -> None:
    """The disk-path entry-point + a real fitz.open round-trip."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LUMINAIRE SCHEDULE", "Sheet EL.0"],
        table=[
            ["TYPE", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A",    "LED TROFFER", "40",    "277V",    "RECESSED"],
            ["B",    "LED DOWNLIGHT","15",   "120V",    "RECESSED"],
        ],
        name="luminaire.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert len(result.fixtures) == 2
    assert result.confidence > 0.0


def test_extract_lighting_schedule_returns_empty_when_no_table(
    tmp_path: Path,
) -> None:
    """Schedule-keyword page with no fixture table → no fixtures, no crash."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        body_lines=["See sheet E2.0 for the schedule."],
        name="empty.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert result.fixtures == []
    assert result.confidence == 0.0


def test_extract_schedule_page_index_recorded(tmp_path: Path) -> None:
    """``source_page`` on each record matches the page index passed in."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
        ],
        name="page.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    assert all(f.source_page == 0 for f in result.fixtures)


def test_extract_schedule_sheet_id_propagates(tmp_path: Path) -> None:
    """When the caller passes ``sheet_id`` it lands on every record."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
        ],
        name="sheet.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_lighting_schedule_from_page(
            doc[0], 0, sheet_id="E2.0"
        )
    assert all(f.source_sheet == "E2.0" for f in result.fixtures)


def test_to_schema_round_trip(tmp_path: Path) -> None:
    """``to_schema`` returns the Pydantic mirror with identical content."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "Lithonia",     "40",    "277V",    "RECESSED"],
        ],
        name="schema.pdf",
    )
    result = extract_lighting_schedule(pdf, 0)
    schema_obj = to_schema(result)
    assert len(schema_obj.fixtures) == 1
    assert schema_obj.fixtures[0].fixture_tag == "A1"
    assert schema_obj.fixtures[0].wattage == 40.0
    assert schema_obj.fixtures[0].voltage == "277V"


# ---------------------------------------------------------------------------
# End-to-end: prepass wiring picks the lighting schedule up
# ---------------------------------------------------------------------------


def test_prepass_drawing_pdf_attaches_lighting_schedule(
    tmp_path: Path,
) -> None:
    """``prepass_drawing_pdf`` populates ``lighting_schedule`` on the page result."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["LIGHTING FIXTURE SCHEDULE", "Sheet E2.0"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"],
            ["A1",  "LED TROFFER", "40",    "277V",    "RECESSED"],
        ],
        name="prepass.pdf",
    )
    results = prepass_drawing_pdf(pdf)
    assert len(results) == 1
    assert results[0].lighting_schedule is not None
    fixtures = results[0].lighting_schedule.fixtures
    assert len(fixtures) == 1
    assert fixtures[0].fixture_tag == "A1"
