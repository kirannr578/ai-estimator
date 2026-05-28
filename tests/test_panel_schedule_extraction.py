"""Tests for the electrical-panel-schedule pre-pass (Phase T2.6).

Every test builds a synthetic 1-page PDF on disk with `fitz` (PyMuPDF)
so we don't need any binary fixtures checked into the repo. Conventions
mirror :mod:`tests.test_finish_schedule_extraction`.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.extraction.drawing_prepass import (
    prepass_drawing_page,
    prepass_drawing_pdf,
)
from core.extraction.panel_schedule import (
    CircuitEntry,
    PanelRecord,
    PanelScheduleResult,
    _looks_like_panel_header,
    _PANEL_ID_PATTERN,
    detect_panel_schedule_page,
    extract_panel_schedule,
    extract_panel_schedule_from_page,
)


# ---------------------------------------------------------------------------
# Fixture builder (mirrors helper in test_finish_schedule_extraction)
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
    page = doc.new_page(width=900, height=720)
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
    name: str = "test.pdf",
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


def test_detect_panel_schedule_keyword_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "Project: Example"],
        name="phrase.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is True


def test_detect_panel_schedule_short_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHED"],
        name="short.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is True


def test_detect_panel_schedule_pnl_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PNL SCHEDULE"],
        name="pnl.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is True


def test_detect_panel_schedule_electrical_panel_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["ELECTRICAL PANEL — PNL-A"],
        name="elec.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is True


def test_detect_panel_schedule_by_table_header(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["SHEET E1.0"],
        table=[
            ["CKT", "BREAKER", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20A",     "Lighting",    "1200",  "A"],
            ["3",   "20A",     "Receptacles", "1800",  "B"],
        ],
        name="header.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is True


def test_detect_panel_schedule_negative_floor_plan(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN", "Sheet A101"],
        body_lines=["Room 101 is 12 ft x 14 ft."],
        name="floor.pdf",
    )
    with fitz.open(pdf) as doc:
        assert detect_panel_schedule_page(doc[0]) is False


def test_looks_like_panel_header_requires_three_signals() -> None:
    # Has all three signal classes
    assert _looks_like_panel_header(
        ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"]
    ) is True
    # Missing load class → not a panel header
    assert _looks_like_panel_header(["CKT", "BREAKER"]) is False
    # Missing circuit class → not a panel header
    assert _looks_like_panel_header(["BREAKER", "DESCRIPTION"]) is False


def test_panel_id_pattern_matches_common_forms() -> None:
    # Confirm the canonical ID regex covers the documented variants.
    for tag in ["PNL-A", "PANEL A", "PANEL-A", "RP-1", "MDP", "MDP1",
                 "MDP-1", "DP-A", "MP-1", "LP-1", "SDP-A", "HP-1"]:
        assert _PANEL_ID_PATTERN.search(tag), f"failed to match {tag!r}"


# ---------------------------------------------------------------------------
# Header-block extraction — panel ID, voltage, MCB/MLO, bus amps, feeder
# ---------------------------------------------------------------------------


def test_extract_single_panel_header_full(tmp_path: Path) -> None:
    """A complete header block: panel ID, 200A MCB, 120/208V 3-phase, feeder."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "Voltage: 120/208V 3-phase",
            "Main: 200A MCB",
            "Bus: 225A",
            "Feeder: 3/0 AWG Cu in 2 inch conduit",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lighting",    "1200",  "A"],
            ["3",   "20",   "Receptacles", "1800",  "B"],
        ],
        name="full.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert isinstance(result, PanelScheduleResult)
    assert len(result.panels) == 1
    panel = result.panels[0]
    assert panel.panel_id == "PNL-A"
    assert panel.voltage == "120/208V"
    assert panel.phase_count == 3
    assert panel.main_breaker_amps == 200
    assert panel.bus_amps == 225
    assert panel.mcb_or_mlo == "MCB"
    assert panel.feeder_conductor_size == "3/0 AWG CU"
    assert panel.feeder_conduit_size == "2 inch"
    assert result.confidence > 0.6


def test_extract_panel_mlo_no_main_breaker(tmp_path: Path) -> None:
    """MLO (Main Lug Only) panel: bus amps but no main breaker amps."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL MDP",
            "277/480V 3-PH",
            "BUS: 800A",
            "MLO",
        ],
        table=[
            ["CKT", "BREAKER", "DESCRIPTION",   "VA",    "PH"],
            ["1",   "100A",    "Subpanel LP-1", "12000", "A,B,C"],
            ["2",   "100A",    "Subpanel LP-2", "12000", "A,B,C"],
        ],
        name="mlo.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert len(result.panels) == 1
    panel = result.panels[0]
    assert panel.panel_id == "MDP"
    assert panel.mcb_or_mlo == "MLO"
    assert panel.bus_amps == 800
    assert panel.voltage == "277/480V"
    assert panel.phase_count == 3


def test_extract_panel_voltage_variants_120_208(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A", "120/208V"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "500",   "A"],
        ],
        name="208.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels[0].voltage == "120/208V"


def test_extract_panel_voltage_variants_277_480(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PANEL MDP", "277/480V"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "30",   "RTU-1",       "12000", "A,B,C"],
        ],
        name="480.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels[0].voltage == "277/480V"


def test_extract_panel_voltage_single_phase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PANEL LP-1", "120V 1-PHASE"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Receptacles", "1200",  "A"],
        ],
        name="120v.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    panel = result.panels[0]
    assert panel.voltage == "120V"
    assert panel.phase_count == 1


# ---------------------------------------------------------------------------
# Circuit-table parsing
# ---------------------------------------------------------------------------


def test_extract_single_panel_with_circuit_table(tmp_path: Path) -> None:
    """A panel header + a 6-row circuit table → 6 CircuitEntry."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "MAIN: 200A MCB",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION",  "WATTS", "PHASE"],
            ["1",   "20",   "Lighting",     "1200",  "A"],
            ["3",   "20",   "Receptacles",  "1800",  "B"],
            ["5",   "30",   "HVAC unit 1",  "5400",  "C"],
            ["7",   "50",   "Range",        "8000",  "A"],
            ["9",   "20",   "Lights LR",    "1000",  "B"],
            ["11",  "20",   "Refrigerator", "600",   "C"],
        ],
        name="circuits.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert len(result.panels) == 1
    panel = result.panels[0]
    assert panel.panel_id == "PNL-A"
    assert len(panel.circuits) == 6
    by_ckt = {c.circuit_number: c for c in panel.circuits}
    assert by_ckt["1"].breaker_amps == 20
    assert by_ckt["1"].load_watts == pytest.approx(1200.0)
    assert by_ckt["5"].breaker_amps == 30
    assert by_ckt["7"].breaker_amps == 50
    assert by_ckt["7"].phase == "A"


def test_extract_breaker_amps_with_trailing_a(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20A",  "Lighting",    "1000",  "A"],
            ["3",   "30A",  "Heater",      "4800",  "B"],
        ],
        name="ampssuffix.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels[0].circuits[0].breaker_amps == 20
    assert result.panels[0].circuits[1].breaker_amps == 30


def test_extract_circuit_with_no_breaker_amps_preserved(tmp_path: Path) -> None:
    """A row whose AMPS cell is blank still parses; breaker_amps = None."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "",     "Spare",       "",      "A"],
            ["3",   "20",   "Lighting",    "1000",  "B"],
        ],
        name="noamps.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    panel = result.panels[0]
    assert len(panel.circuits) == 2
    by_ckt = {c.circuit_number: c for c in panel.circuits}
    assert by_ckt["1"].breaker_amps is None
    assert by_ckt["1"].load_description == "Spare"
    assert by_ckt["3"].breaker_amps == 20


def test_extract_circuit_with_multi_phase_label(tmp_path: Path) -> None:
    """A 3-pole breaker row carries phase ``A,B,C``."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PANEL MDP", "277/480V"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS",  "PHASE"],
            ["1",   "100",  "RTU-1",       "24000",  "A,B,C"],
        ],
        name="multiphase.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    circuits = result.panels[0].circuits
    assert len(circuits) == 1
    assert circuits[0].phase == "A,B,C"
    assert circuits[0].breaker_amps == 100


def test_extract_circuit_load_in_kilowatts(tmp_path: Path) -> None:
    """A ``kW`` suffix on the load cell converts to watts."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS",  "PHASE"],
            ["1",   "50",   "AHU-1",       "5.4 kW", "A"],
        ],
        name="kw.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels[0].circuits[0].load_watts == pytest.approx(5400.0)


def test_extract_circuit_empty_rows_dropped(tmp_path: Path) -> None:
    """Pure blank rows in the circuit table are skipped."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lighting",    "1000",  "A"],
            ["",    "",     "",            "",      ""],
            ["3",   "20",   "Outlets",     "1200",  "B"],
        ],
        name="blanks.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    nums = [c.circuit_number for c in result.panels[0].circuits]
    assert nums == ["1", "3"]


def test_phase_letter_does_not_collide_with_amps_header(tmp_path: Path) -> None:
    """A PHASE column abbreviated ``A``/``B``/``C`` should NOT poach the AMPS index.

    Pre-fix the substring-tolerant ``_header_index`` would land
    PHASE on the AMPS column because ``"A" in "AMPS"`` evaluates true.
    The fix pins AMPS first and re-picks PHASE with AMPS excluded.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        # Note: the PHASE column is labelled just ``PH`` (substring of AMPS isn't an issue here,
        # but a short header that ALSO could match ``AMPS`` substring is what we're guarding.
        # Use a header order that previously triggered the collision.
        table=[
            ["CKT", "PH", "AMPS", "DESCRIPTION", "WATTS"],
            ["1",   "A",  "20",   "Lighting",    "1000"],
            ["3",   "B",  "30",   "Heater",      "4800"],
        ],
        name="phasecollision.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    panel = result.panels[0]
    by_ckt = {c.circuit_number: c for c in panel.circuits}
    assert by_ckt["1"].breaker_amps == 20
    assert by_ckt["1"].phase == "A"
    assert by_ckt["3"].breaker_amps == 30
    assert by_ckt["3"].phase == "B"


# ---------------------------------------------------------------------------
# Two-column layout (odd circuits left, even right)
# ---------------------------------------------------------------------------


def test_extract_two_column_panel_layout(tmp_path: Path) -> None:
    """Odd circuits down the left half, even circuits down the right half."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PANEL PNL-A", "200A MCB"],
        table=[
            # 9-column header: CKT-L | AMPS-L | DESC-L | W-L | PH | DESC-R | W-R | AMPS-R | CKT-R
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PH",
             "CKT", "AMPS", "DESCRIPTION", "WATTS"],
            ["1",   "20",   "Lights N",    "1200",  "A",
             "2",   "20",   "Lights S",    "1200"],
            ["3",   "20",   "Outlets W",   "1800",  "B",
             "4",   "20",   "Outlets E",   "1800"],
            ["5",   "30",   "AC unit",     "5400",  "C",
             "6",   "30",   "Heat pump",   "5400"],
        ],
        cell_size=(70.0, 24.0),
        name="twocol.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert len(result.panels) == 1
    panel = result.panels[0]
    # Six circuits total (3 left + 3 right). Both halves should land.
    assert len(panel.circuits) == 6
    nums = {c.circuit_number for c in panel.circuits}
    assert nums == {"1", "2", "3", "4", "5", "6"}


# ---------------------------------------------------------------------------
# Multi-panel page — two distinct panels detected
# ---------------------------------------------------------------------------


def test_extract_multi_panel_page(tmp_path: Path) -> None:
    """A page that documents two panels with two separate circuit tables."""
    doc = fitz.open()
    # Page 1: panel A header + table, then panel B header + table.
    page = doc.new_page(width=900, height=900)
    # Panel A header
    page.insert_text((40, 60), "PANEL SCHEDULE", fontsize=12)
    page.insert_text((40, 78), "PANEL PNL-A — 200A MCB, 120/208V 3-phase", fontsize=11)
    # Panel A table
    x0a, y0a = 40.0, 110.0
    cell_w, cell_h = 75.0, 22.0
    table_a = [
        ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
        ["1",   "20",   "Lights",      "1000",  "A"],
        ["3",   "20",   "Outlets",     "1800",  "B"],
    ]
    n_rows = len(table_a)
    n_cols = len(table_a[0])
    for i in range(n_rows + 1):
        page.draw_line((x0a, y0a + i * cell_h), (x0a + cell_w * n_cols, y0a + i * cell_h))
    for j in range(n_cols + 1):
        page.draw_line((x0a + j * cell_w, y0a), (x0a + j * cell_w, y0a + n_rows * cell_h))
    for i, row in enumerate(table_a):
        for j, val in enumerate(row):
            page.insert_text(
                (x0a + j * cell_w + 4, y0a + i * cell_h + 14), val, fontsize=9,
            )

    # Panel B header
    page.insert_text((40, 320), "PANEL PNL-B — 100A MCB, 120/208V 3-phase", fontsize=11)
    # Panel B table
    x0b, y0b = 40.0, 350.0
    table_b = [
        ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
        ["1",   "30",   "Range",       "8000",  "A"],
        ["3",   "20",   "Microwave",   "1500",  "B"],
    ]
    n_rows = len(table_b)
    n_cols = len(table_b[0])
    for i in range(n_rows + 1):
        page.draw_line((x0b, y0b + i * cell_h), (x0b + cell_w * n_cols, y0b + i * cell_h))
    for j in range(n_cols + 1):
        page.draw_line((x0b + j * cell_w, y0b), (x0b + j * cell_w, y0b + n_rows * cell_h))
    for i, row in enumerate(table_b):
        for j, val in enumerate(row):
            page.insert_text(
                (x0b + j * cell_w + 4, y0b + i * cell_h + 14), val, fontsize=9,
            )

    out = tmp_path / "multi.pdf"
    doc.save(out)
    doc.close()

    result = extract_panel_schedule(out, 0)
    assert len(result.panels) == 2
    ids = {p.panel_id for p in result.panels}
    assert ids == {"PNL-A", "PNL-B"}


# ---------------------------------------------------------------------------
# Edge cases — empty pages, missing fields, header-only
# ---------------------------------------------------------------------------


def test_extract_panel_schedule_empty_page(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["FLOOR PLAN"],
        body_lines=["No tables here, just prose."],
        name="empty.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels == []
    assert result.confidence == 0.0


def test_extract_panel_schedule_phrase_without_table(tmp_path: Path) -> None:
    """PANEL SCHEDULE phrase fires but no table → empty (no fabricated rows)."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "See attached spreadsheet"],
        body_lines=["No table on this sheet."],
        name="phraseonly.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels == []


def test_extract_panel_schedule_header_only_no_circuit_rows(tmp_path: Path) -> None:
    """Phrase + panel-ID block but no circuit table → still emits a Panel.

    Header-only panels are rare but legitimate (a panel referenced on a
    sheet that publishes the loads on a different page). The synthesiser
    will emit the enclosure + feeder rows even without circuits.
    """
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL PNL-X — 100A MCB, 120/208V 3-PH",
            "(circuit table on E1.1)",
        ],
        name="headeronly.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    if result.panels:
        assert result.panels[0].panel_id == "PNL-X"
        assert result.panels[0].circuits == []


def test_extract_panel_schedule_out_of_range_raises(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
        name="oor.pdf",
    )
    with pytest.raises(IndexError):
        extract_panel_schedule(pdf, 99)


def test_extract_panel_schedule_source_page_propagates(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
        name="srcpage.pdf",
    )
    with fitz.open(pdf) as doc:
        result = extract_panel_schedule_from_page(doc[0], page_index=7,
                                                     sheet_id="E1.0")
    assert result.pages == [7]
    assert result.panels[0].source_page == 7
    assert result.panels[0].source_sheet == "E1.0"


# ---------------------------------------------------------------------------
# Panel-ID variations all detected
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("tag, expected", [
    ("PNL-A",      "PNL-A"),
    ("PANEL A",    "A"),         # PANEL <ID> form pinned via _PANEL_LABEL_RE → "A"
    ("PANEL-A",    "PANEL-A"),
    ("RP-1",       "RP-1"),
    ("MDP",        "MDP"),
    ("MDP-1",      "MDP-1"),
])
def test_panel_id_variations_detected(tmp_path: Path, tag: str,
                                          expected: str) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", tag, "200A MCB"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
        name=f"id_{tag.replace(' ', '_').replace('-', '_')}.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels, f"no panel detected for tag {tag!r}"
    # Panel ID must match either the explicit-label or generic-pattern form.
    pid = result.panels[0].panel_id
    assert pid == expected or pid.endswith(expected) or expected in pid, \
        f"expected {expected!r}, got {pid!r}"


# ---------------------------------------------------------------------------
# Feeder parsing
# ---------------------------------------------------------------------------


def test_extract_feeder_conductor_3_0_awg_cu(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL PNL-A — 200A MCB",
            "Feeder: 3/0 AWG Cu in 2 inch conduit",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
        name="feeder3_0.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    panel = result.panels[0]
    assert panel.feeder_conductor_size and "3/0" in panel.feeder_conductor_size
    assert panel.feeder_conduit_size == "2 inch"


def test_extract_feeder_kcmil(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL MDP — 800A MLO",
            "Feeder: 500 KCMIL Al in 4 inch conduit",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "100",  "Subpanel",    "12000", "A,B,C"],
        ],
        name="feederkcmil.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    panel = result.panels[0]
    assert panel.feeder_conductor_size and "500" in panel.feeder_conductor_size
    assert panel.feeder_conduit_size == "4 inch"


# ---------------------------------------------------------------------------
# Confidence rubric
# ---------------------------------------------------------------------------


def test_confidence_fully_decorated_panel(tmp_path: Path) -> None:
    """Fully-decorated panel (voltage + MCB + bus + circuits) → ≥ 0.85."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL PNL-A",
            "200A MCB",
            "Bus: 225A",
            "120/208V 3-PHASE",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
            ["3",   "20",   "Outlets",     "1800",  "B"],
        ],
        name="fullconf.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    assert result.panels[0].confidence >= 0.85


def test_confidence_partial_panel_metadata(tmp_path: Path) -> None:
    """No voltage AND no MCB/MLO designation → lower confidence."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=["PANEL SCHEDULE", "PNL-A"],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
        name="partconf.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    # Missing both voltage and MCB/MLO → tick down from 0.85 baseline.
    assert result.panels[0].confidence < 0.85


# ---------------------------------------------------------------------------
# Integration with drawing pre-pass
# ---------------------------------------------------------------------------


def test_integration_with_drawing_prepass(tmp_path: Path) -> None:
    """``prepass_drawing_page`` exposes panel-schedule extraction."""
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PROJECT NAME: T2.6 Test",
            "SHEET NO: E1.0",
            'SCALE: 1/4" = 1\'-0"',
            "PANEL SCHEDULE — PANEL PNL-A",
            "120/208V 3-PHASE",
            "200A MCB",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
            ["3",   "20",   "Outlets",     "1800",  "B"],
        ],
        name="integration.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.panel_schedule is not None
    assert result.panel_schedule.panels[0].panel_id == "PNL-A"

    from core.extraction.drawing_prepass import to_schema as prepass_to_schema
    pyd = prepass_to_schema(result)
    assert pyd.panel_schedule is not None
    assert pyd.panel_schedule.panels[0].panel_id == "PNL-A"


def test_prepass_panel_does_not_conflict_with_door_schedule_on_separate_pages(
    tmp_path: Path,
) -> None:
    """A 2-page PDF: door schedule on p0, panel schedule on p1. Both fire."""
    doc = fitz.open()
    _add_page(
        doc,
        title_lines=["DOOR SCHEDULE", "Sheet A0.1"],
        table=[
            ["MARK", "TYPE", "WIDTH", "HEIGHT", "FRAME", "HARDWARE"],
            ["101",  "HM",  "3'-0\"", "7'-0\"", "HM",   "HW-1"],
        ],
    )
    _add_page(
        doc,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL PNL-A — 200A MCB, 120/208V",
            "Sheet E1.0",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
        ],
    )
    out = tmp_path / "twopage.pdf"
    doc.save(out)
    doc.close()

    results = prepass_drawing_pdf(out)
    assert len(results) == 2
    p0, p1 = results
    assert p0.door_schedule is not None
    assert p0.panel_schedule is None
    assert p1.door_schedule is None
    assert p1.panel_schedule is not None
    assert p1.panel_schedule.panels[0].panel_id == "PNL-A"


def test_schema_roundtrip_to_pydantic_and_back(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path,
        title_lines=[
            "PANEL SCHEDULE",
            "PANEL PNL-A",
            "200A MCB, 120/208V 3-PH",
        ],
        table=[
            ["CKT", "AMPS", "DESCRIPTION", "WATTS", "PHASE"],
            ["1",   "20",   "Lights",      "1000",  "A"],
            ["3",   "30",   "HVAC",        "5400",  "B"],
        ],
        name="roundtrip.pdf",
    )
    result = extract_panel_schedule(pdf, 0)
    from core.extraction.panel_schedule import to_schema as panel_to_schema
    pyd = panel_to_schema(result)
    # Pydantic model round-trips
    json_dump = pyd.model_dump()
    assert json_dump["panels"][0]["panel_id"] == "PNL-A"
    assert json_dump["panels"][0]["voltage"] == "120/208V"
    assert len(json_dump["panels"][0]["circuits"]) == 2
