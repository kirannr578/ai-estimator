"""Tests for the plumbing fixture schedule pre-pass (Phase T2.9).

Every test builds a synthetic 1-page PDF on disk with ``fitz`` (PyMuPDF)
so we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_hvac_schedule_extraction`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import prepass_drawing_pdf
from core.extraction.plumbing_schedule import (
    PlumbingFixtureRecord,
    PlumbingScheduleResult,
    _PLUMBING_SCHEDULE_KEYWORDS,
    _classify_fixture_type,
    _detect_ada,
    _detect_sensor,
    _fixture_indices,
    _looks_like_plumbing_header,
    _parse_flow_rate,
    _parse_quantity,
    detect_plumbing_schedule_page,
    extract_plumbing_schedule,
    extract_plumbing_schedule_from_page,
    to_schema,
)


# ---------------------------------------------------------------------------
# Fixture builder (auto-sized — mirrors helper in hvac test module)
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
    name: str = "plumbing.pdf",
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


@pytest.mark.parametrize("phrase", list(_PLUMBING_SCHEDULE_KEYWORDS))
def test_detect_plumbing_schedule_keyword_variants(
    tmp_path: Path, phrase: str
) -> None:
    """Each plumbing keyword variant flips the page-level signal.

    Includes ``FIXTURE SCHEDULE`` and ``FIXTURE TYPE`` which the
    lighting detector also accepts — we still expect the plumbing
    detector to fire on the bare phrase when no disqualifying header
    is present.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=[phrase, "Project: Demo"],
        name=f"phrase_{phrase[:10].strip().replace(' ', '_')}.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_plumbing_schedule_page(doc[0]) is True


def test_detect_plumbing_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["SHEET P2.0"],
        table=[
            ["TAG", "DESCRIPTION", "MANUFACTURER", "GPF", "CW", "WASTE"],
            ["WC-1", "WATER CLOSET", "American Standard", "1.28", "1/2\"", "4\""],
        ],
        name="header_only.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_plumbing_schedule_page(doc[0]) is True


def test_detect_plumbing_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=["Room 101 is 12 ft x 14 ft."],
        name="floor.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_plumbing_schedule_page(doc[0]) is False


def test_detect_plumbing_schedule_negative_lighting_schedule(tmp_path: Path) -> None:
    """A lighting-schedule page using 'FIXTURE SCHEDULE' must NOT light up plumbing."""
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
        # The phrase trigger fires, but the rejection path catches the
        # WATTS / VOLTAGE / MOUNTING header (lighting / electrical
        # discriminators) and refuses to claim the page.
        assert detect_plumbing_schedule_page(doc[0]) is False


def test_detect_plumbing_schedule_negative_hvac_schedule(tmp_path: Path) -> None:
    """An HVAC schedule page must NOT light up the plumbing detector."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["AHU SCHEDULE", "Sheet M2.0"],
        table=[
            ["TAG",   "DESCRIPTION", "MANUFACTURER", "CFM",  "HP",  "VOLTAGE"],
            ["AHU-1", "AIR HANDLER", "Trane",        "2000", "5",   "480V/3PH"],
        ],
        name="hvac.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_plumbing_schedule_page(doc[0]) is False


def test_looks_like_plumbing_header_requires_three_signals() -> None:
    """Tag + (desc/mfr/model) + (GPF/GPM/CW/HW/WASTE/VENT/FLOW) all present."""
    assert _looks_like_plumbing_header(
        ["TAG", "DESCRIPTION", "GPF", "CW"]
    ) is True
    assert _looks_like_plumbing_header(
        ["MARK", "MANUFACTURER", "MODEL", "WASTE"]
    ) is True
    # Missing spec column → not a plumbing header
    assert _looks_like_plumbing_header(["TAG", "DESCRIPTION"]) is False
    # Missing tag class → not a plumbing header
    assert _looks_like_plumbing_header(["DESCRIPTION", "GPF"]) is False


def test_looks_like_plumbing_header_rejects_lighting_disqualifier() -> None:
    """A lighting-schedule header carrying WATTS / LUMENS must NOT pass."""
    assert _looks_like_plumbing_header(
        ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"]
    ) is False


def test_looks_like_plumbing_header_rejects_hvac_disqualifier() -> None:
    """An HVAC-schedule header carrying CFM / HP must NOT pass."""
    assert _looks_like_plumbing_header(
        ["TAG", "DESCRIPTION", "CFM", "HP", "VOLTAGE"]
    ) is False


def test_looks_like_plumbing_header_allows_mounting_column() -> None:
    """MOUNTING is a legitimate plumbing column (FLOOR/WALL/COUNTER/...)."""
    assert _looks_like_plumbing_header(
        ["TAG", "DESCRIPTION", "MOUNTING", "GPF", "CW"]
    ) is True


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("raw,expected_value,expected_unit", [
    ("1.28 GPF", 1.28, "GPF"),
    ("0.5 GPM", 0.5, "GPM"),
    ("1.5 GPM", 1.5, "GPM"),
    ("1.28", 1.28, None),
    ("1.28GPF", 1.28, "GPF"),
])
def test_parse_flow_rate_forms(raw: str, expected_value: float,
                                  expected_unit: str | None) -> None:
    value, unit = _parse_flow_rate(raw)
    assert value == expected_value
    assert unit == expected_unit


def test_parse_flow_rate_returns_none_for_blank() -> None:
    assert _parse_flow_rate("") == (None, None)
    assert _parse_flow_rate(None) == (None, None)


def test_parse_quantity_strips_ea() -> None:
    assert _parse_quantity("3") == 3
    assert _parse_quantity("3 EA") == 3
    assert _parse_quantity("12") == 12
    assert _parse_quantity("0") == 0


def test_parse_quantity_rejects_non_numeric() -> None:
    assert _parse_quantity("a few") is None
    assert _parse_quantity("") is None
    assert _parse_quantity(None) is None


# ---------------------------------------------------------------------------
# ADA + sensor detection
# ---------------------------------------------------------------------------


def test_detect_ada_keywords() -> None:
    assert _detect_ada("ADA-compliant water closet") is True
    assert _detect_ada(None, "Barrier-free accessible") is True
    assert _detect_ada("WHEELCHAIR mounting height") is True


def test_detect_ada_none_when_silent() -> None:
    assert _detect_ada("Standard wall-hung WC") is None
    assert _detect_ada(None, None) is None


def test_detect_sensor_keywords() -> None:
    assert _detect_sensor("Touchless sensor faucet") is True
    assert _detect_sensor(None, "Infrared automatic flush valve") is True
    assert _detect_sensor("Motion-activated lavatory") is True


def test_detect_sensor_none_when_silent() -> None:
    assert _detect_sensor("Manual lever flush") is None


# ---------------------------------------------------------------------------
# Fixture-type detection from tag prefix
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag,expected", [
    ("WC-1",  "WATER_CLOSET"),
    ("WC-A",  "WATER_CLOSET"),
    ("LAV-1", "LAVATORY"),
    ("LAV-A", "LAVATORY"),
    ("URN-1", "URINAL"),
    ("UR-1",  "URINAL"),
    ("SH-1",  "SHOWER"),
    ("SHU-1", "SHOWER"),
    ("EWC-1", "EWC"),
    ("DF-1",  "EWC"),
    ("MS-1",  "MOP_SINK"),
    ("SK-1",  "SINK"),
    ("WH-1",  "WATER_HEATER"),
    ("HD-1",  "HOSE_BIBB"),
    ("HB-1",  "HOSE_BIBB"),
    ("FD-1",  "FLOOR_DRAIN"),
])
def test_classify_fixture_type_from_tag(tag: str, expected: str) -> None:
    assert _classify_fixture_type(tag) == expected


def test_classify_fixture_type_other_for_unknown() -> None:
    """A tag with no recognized prefix falls back to OTHER."""
    assert _classify_fixture_type("XYZ-99") == "OTHER"


def test_classify_fixture_type_description_fallback() -> None:
    """When the tag is uninformative, the description disambiguates."""
    assert _classify_fixture_type("X-1", "Water closet, wall-hung") == "WATER_CLOSET"
    assert _classify_fixture_type("Y-1", "Drinking fountain ADA") == "EWC"
    assert _classify_fixture_type("Z-1", "Floor drain 2-inch") == "FLOOR_DRAIN"


# ---------------------------------------------------------------------------
# Header collision — _header_index_excluding reuse (FIFTH validation)
# ---------------------------------------------------------------------------


def test_header_collision_d_does_not_collide_with_description() -> None:
    """Single-letter ``D`` must not steal the longer ``DESCRIPTION`` header."""
    headers = ["TAG", "DESCRIPTION", "D", "GPF"]
    idx = _fixture_indices(headers)
    # DESCRIPTION wins for the description slot.
    assert idx["desc"] == 1
    # D survives in long_exclude — neither slot should grab it twice.
    assert idx["tag"] == 0


def test_header_collision_short_d_only() -> None:
    """When only ``D`` is present (no long form), it IS the description column."""
    headers = ["TAG", "D", "GPF"]
    idx = _fixture_indices(headers)
    assert idx["desc"] == 1


def test_header_collision_dia_does_not_collide_with_description() -> None:
    """``DIA`` must not steal the ``DESCRIPTION`` header (substring trap)."""
    headers = ["TAG", "DESCRIPTION", "DIA", "WASTE"]
    idx = _fixture_indices(headers)
    assert idx["desc"] == 1


def test_header_collision_t_does_not_collide_with_type() -> None:
    """Single-letter ``T`` must not steal the longer ``TYPE`` header."""
    headers = ["TAG", "TYPE", "T", "GPF"]
    idx = _fixture_indices(headers)
    # TYPE wins for the type slot
    assert idx["type"] == 1


def test_header_collision_temp_distinct_from_type() -> None:
    """``TEMP`` substring-collides with ``TYPE`` — both must claim distinct columns."""
    headers = ["TAG", "TYPE", "TEMP", "GPF"]
    idx = _fixture_indices(headers)
    # TYPE wins for the type slot
    assert idx["type"] == 1


def test_header_collision_q_does_not_collide_with_quantity() -> None:
    headers = ["TAG", "DESCRIPTION", "GPF", "QUANTITY", "Q"]
    idx = _fixture_indices(headers)
    assert idx["qty"] == 3


def test_header_collision_cw_hw_claim_distinct_columns() -> None:
    """CW and HW connection-size columns each claim distinct slots."""
    headers = ["TAG", "DESCRIPTION", "CW", "HW", "WASTE", "VENT"]
    idx = _fixture_indices(headers)
    assert idx["cw"] == 2
    assert idx["hw"] == 3
    assert idx["waste"] == 4
    assert idx["vent"] == 5
    # Sanity: CW and HW are different indices
    assert idx["cw"] != idx["hw"]


# ---------------------------------------------------------------------------
# Single + multi-fixture extraction
# ---------------------------------------------------------------------------


def test_extract_single_wc_all_fields(tmp_path: Path) -> None:
    """One fully-decorated WC row → every field populated."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG", "DESCRIPTION",       "MANUFACTURER", "MODEL",
             "MOUNTING", "GPF",  "CW",     "WASTE"],
            ["WC-1", "WALL-HUNG TOILET", "American Standard", "3461.001",
             "WALL", "1.28", "1/2\"",  "4\""],
        ],
        cell_size=(110.0, 24.0),
        name="single_wc.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    assert isinstance(result, PlumbingScheduleResult)
    assert len(result.fixtures) == 1
    f = result.fixtures[0]
    assert f.fixture_tag == "WC-1"
    assert f.fixture_type == "WATER_CLOSET"
    assert f.description == "WALL-HUNG TOILET"
    assert f.manufacturer == "American Standard"
    assert f.model_number == "3461.001"
    assert f.mounting == "WALL"
    assert f.flow_rate_value == 1.28
    assert f.flow_rate_unit == "GPF"
    assert f.cold_water_size == "1/2\""
    assert f.waste_size == "4\""


def test_extract_multi_fixture_schedule(tmp_path: Path) -> None:
    """A 5-row mixed-type schedule lands 5 fixture records."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",       "MANUFACTURER",      "MOUNTING", "GPF",  "GPM",  "CW",   "WASTE"],
            ["WC-1",  "WATER CLOSET",      "American Standard", "WALL",     "1.28", "",     "1/2\"", "4\""],
            ["LAV-A", "LAVATORY",          "Kohler",            "COUNTER",  "",     "0.5",  "1/2\"", "1-1/2\""],
            ["URN-1", "URINAL",            "Sloan",             "WALL",     "0.5",  "",     "3/4\"", "2\""],
            ["SH-1",  "SHOWER",            "Symmons",           "WALL",     "",     "1.5",  "1/2\"", "2\""],
            ["FD-1",  "FLOOR DRAIN",       "Zurn",              "FLOOR",    "",     "",     "",      "2\""],
        ],
        cell_size=(95.0, 24.0),
        name="multi.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    assert len(result.fixtures) == 5
    tags = {f.fixture_tag for f in result.fixtures}
    assert tags == {"WC-1", "LAV-A", "URN-1", "SH-1", "FD-1"}
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["WC-1"].fixture_type == "WATER_CLOSET"
    assert by_tag["LAV-A"].fixture_type == "LAVATORY"
    assert by_tag["URN-1"].fixture_type == "URINAL"
    assert by_tag["SH-1"].fixture_type == "SHOWER"
    assert by_tag["FD-1"].fixture_type == "FLOOR_DRAIN"


def test_extract_schedule_with_qty_column(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "GPF",  "CW",     "WASTE", "QTY"],
            ["WC-1", "WATER CLOSET", "1.28", "1/2\"",  "4\"",    "8"],
            ["LAV-1","LAVATORY",     "",     "1/2\"",  "1-1/2\"", "4"],
        ],
        name="qty.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    assert len(result.fixtures) == 2
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["WC-1"].quantity == 8
    assert by_tag["LAV-1"].quantity == 4


def test_extract_schedule_without_qty_column_quantity_is_none(
    tmp_path: Path,
) -> None:
    """No QTY column → ``quantity`` stays None (signals hand-takeoff need)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",  "MANUFACTURER", "GPF",  "CW",     "WASTE"],
            ["WC-1",  "WATER CLOSET", "American Std", "1.28", "1/2\"",  "4\""],
        ],
        name="noqty.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    assert result.fixtures[0].quantity is None


def test_extract_connection_sizes_round_trip(tmp_path: Path) -> None:
    """CW / HW / WASTE / VENT preserve their original cell strings."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "MANUFACTURER", "GPM", "CW",     "HW",    "WASTE",  "VENT"],
            ["LAV-1", "LAVATORY",  "Kohler",        "0.5", "1/2\"",  "1/2\"", "1-1/2\"", "1-1/4\""],
        ],
        cell_size=(95.0, 24.0),
        name="connection.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    f = result.fixtures[0]
    assert f.cold_water_size == "1/2\""
    assert f.hot_water_size == "1/2\""
    assert f.waste_size == "1-1/2\""
    assert f.vent_size == "1-1/4\""


def test_extract_mounting_variants_preserved(tmp_path: Path) -> None:
    """MOUNTING column round-trips multiple variants verbatim."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",  "MOUNTING",     "GPF",   "GPM", "CW"],
            ["WC-1",  "WATER CLOSET", "FLOOR",        "1.28",  "",    "1/2\""],
            ["WC-2",  "WATER CLOSET", "WALL",         "1.28",  "",    "1/2\""],
            ["LAV-A", "LAVATORY",     "COUNTER",      "",      "0.5", "1/2\""],
            ["SH-1",  "SHOWER",       "DECK",         "",      "1.5", "1/2\""],
        ],
        cell_size=(95.0, 24.0),
        name="mounting.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["WC-1"].mounting == "FLOOR"
    assert by_tag["WC-2"].mounting == "WALL"
    assert by_tag["LAV-A"].mounting == "COUNTER"
    assert by_tag["SH-1"].mounting == "DECK"


def test_extract_ada_from_notes(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",        "GPF",   "CW",      "WASTE", "NOTES"],
            ["WC-1", "WATER CLOSET",       "1.28",  "1/2\"",   "4\"",   "ADA-compliant"],
            ["WC-2", "WATER CLOSET",       "1.28",  "1/2\"",   "4\"",   "barrier-free, wheelchair height"],
            ["LAV-A","LAVATORY",           "",      "1/2\"",   "1-1/2\"", "Standard"],
        ],
        cell_size=(95.0, 24.0),
        name="ada.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["WC-1"].ada_compliant is True
    assert by_tag["WC-2"].ada_compliant is True
    assert by_tag["LAV-A"].ada_compliant is None


def test_extract_sensor_from_notes(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "GPM",  "CW",      "WASTE",  "NOTES"],
            ["LAV-A", "LAVATORY",    "0.5",  "1/2\"",   "1-1/2\"", "sensor-operated faucet"],
            ["LAV-B", "LAVATORY",    "0.5",  "1/2\"",   "1-1/2\"", "infrared touchless"],
            ["LAV-C", "LAVATORY",    "0.5",  "1/2\"",   "1-1/2\"", "manual lever"],
        ],
        cell_size=(95.0, 24.0),
        name="sensor.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    by_tag = {f.fixture_tag: f for f in result.fixtures}
    assert by_tag["LAV-A"].sensor_operated is True
    assert by_tag["LAV-B"].sensor_operated is True
    assert by_tag["LAV-C"].sensor_operated is None


def test_extract_manufacturer_slash_split(tmp_path: Path) -> None:
    """``"Kohler / K-2210"`` in the MANUFACTURER cell splits mfr + model."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION", "MANUFACTURER",        "GPM",  "CW"],
            ["LAV-1", "LAVATORY",   "Kohler / K-2210",     "0.5",  "1/2\""],
        ],
        cell_size=(120.0, 24.0),
        name="slash.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    f = result.fixtures[0]
    assert f.manufacturer == "Kohler"
    assert f.model_number == "K-2210"


def test_extract_via_prepass_drawing_pdf(tmp_path: Path) -> None:
    """The drawing prepass wires through to the plumbing extractor end-to-end."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE", "Sheet P2.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MANUFACTURER", "GPF",  "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "American Std", "1.28", "1/2\"",  "4\""],
        ],
        cell_size=(110.0, 24.0),
        name="prepass.pdf",
    )
    results = prepass_drawing_pdf(pdf)
    assert len(results) == 1
    assert results[0].plumbing_schedule is not None
    assert len(results[0].plumbing_schedule.fixtures) == 1
    assert results[0].plumbing_schedule.fixtures[0].fixture_tag == "WC-1"
    assert results[0].plumbing_schedule.fixtures[0].fixture_type == "WATER_CLOSET"


def test_to_schema_bridges_to_pydantic(tmp_path: Path) -> None:
    """``to_schema`` produces a Pydantic ``PlumbingScheduleResult``."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "MANUFACTURER", "GPF",  "CW",     "WASTE"],
            ["WC-1", "WATER CLOSET", "American Std", "1.28", "1/2\"",  "4\""],
        ],
        cell_size=(110.0, 24.0),
        name="schema.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    pyd = to_schema(result)
    from core.schemas import PlumbingScheduleResult as PydanticResult
    assert isinstance(pyd, PydanticResult)
    assert len(pyd.fixtures) == 1
    assert pyd.fixtures[0].fixture_tag == "WC-1"
    assert pyd.fixtures[0].fixture_type == "WATER_CLOSET"


def test_extract_returns_empty_when_no_table(tmp_path: Path) -> None:
    """A page with the phrase but no fixture table → empty result."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PLUMBING FIXTURE SCHEDULE"],
        body_lines=["See sheet P2.0 for fixture details."],
        name="empty.pdf",
    )
    result = extract_plumbing_schedule(pdf, 0)
    assert result.fixtures == []
    assert result.confidence == 0.0


def test_extract_record_confidence_decorated() -> None:
    """A fully-decorated fixture record lands above AUTO_APPROVE threshold."""
    from core.extraction.plumbing_schedule import _fixture_confidence
    score = _fixture_confidence(
        tag="WC-1", has_description=True, has_manufacturer=True,
        has_model=True, has_flow=True, has_connections=True, has_mounting=True,
    )
    assert score >= 0.85  # AUTO_APPROVE threshold


def test_extract_record_confidence_tag_only() -> None:
    """A tag-only record lands at 0.65 (HAND_TAKEOFF cusp)."""
    from core.extraction.plumbing_schedule import _fixture_confidence
    score = _fixture_confidence(
        tag="WC-1", has_description=False, has_manufacturer=False,
        has_model=False, has_flow=False, has_connections=False, has_mounting=False,
    )
    assert score == 0.65
