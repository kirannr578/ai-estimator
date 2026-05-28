"""Tests for Phase T2.6 electrical-panel-schedule → :class:`TakeoffItem` synthesis.

Pure unit tests against the Pydantic schema models (no PDF I/O); the
extraction layer is exercised separately in
:mod:`tests.test_panel_schedule_extraction`. Mirrors the shape of
:mod:`tests.test_finish_takeoff_synthesis`: build a synthetic
``PanelRecord`` (or short list), call
:func:`synthesize_panel_takeoff_items`, assert on the four families of
``TakeoffItem`` it produces (panel enclosure / branch breakers / feeder
conductor / feeder conduit).
"""

from __future__ import annotations

import pytest

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_PANEL,
    _FEEDER_CONFIDENCE,
    _FEEDER_PARAMETRIC_LF,
    _PANEL_BOARD_BUS_THRESHOLD_A,
    synthesize_panel_takeoff_items,
)
from core.schemas import (
    CircuitEntry,
    PanelRecord,
    PanelScheduleResult,
    TakeoffItem,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _panel(
    *,
    panel_id: str = "PNL-A",
    voltage: str | None = "120/208V",
    phase_count: int | None = 3,
    main_breaker_amps: int | None = 200,
    bus_amps: int | None = 225,
    mcb_or_mlo: str | None = "MCB",
    feeder_conductor_size: str | None = "3/0 AWG CU",
    feeder_conduit_size: str | None = "2 inch",
    location: str | None = None,
    circuits: list[CircuitEntry] | None = None,
    confidence: float = 0.85,
    source_sheet: str | None = "E1.0",
) -> PanelRecord:
    return PanelRecord(
        panel_id=panel_id,
        voltage=voltage,
        phase_count=phase_count,
        main_breaker_amps=main_breaker_amps,
        bus_amps=bus_amps,
        mcb_or_mlo=mcb_or_mlo,
        feeder_conductor_size=feeder_conductor_size,
        feeder_conduit_size=feeder_conduit_size,
        location=location,
        circuits=circuits or [],
        confidence=confidence,
        source_sheet=source_sheet,
    )


def _circuit(num: str, amps: int | None, *, watts: float | None = None,
              phase: str | None = "A",
              desc: str = "Lighting") -> CircuitEntry:
    return CircuitEntry(
        circuit_number=num,
        breaker_amps=amps,
        load_description=desc,
        load_watts=watts,
        phase=phase,
    )


def _by_section(items: list[TakeoffItem]) -> dict[str, list[TakeoffItem]]:
    out: dict[str, list[TakeoffItem]] = {}
    for it in items:
        out.setdefault(it.csi_section or "", []).append(it)
    return out


# ---------------------------------------------------------------------------
# Happy path: a 21-circuit panel → 1 enclosure + N breaker groups + 2 feeders
# ---------------------------------------------------------------------------


def test_synthesize_single_panel_basic_shape() -> None:
    """A panel with no circuits → exactly 1 + 0 + 2 = 3 items."""
    items = synthesize_panel_takeoff_items([_panel()])
    assert len(items) == 3  # enclosure + feeder wire + feeder conduit
    sections = {it.csi_section for it in items}
    assert sections == {"26 24 16", "26 05 19", "26 05 33"}
    assert all(it.csi_division == "26" for it in items)
    assert all(isinstance(it, TakeoffItem) for it in items)


def test_synthesize_single_panel_with_circuits() -> None:
    """Standard 21-circuit panel: 1 enclosure + 4 breaker groups + 2 feeders."""
    circuits = [
        # 12 × 20A + 4 × 30A + 4 × 50A + 1 × 100A = 21 circuits, 4 amp sizes
        *[_circuit(str(n), 20) for n in range(1, 13)],
        *[_circuit(str(n), 30) for n in range(13, 17)],
        *[_circuit(str(n), 50) for n in range(17, 21)],
        _circuit("21", 100),
    ]
    items = synthesize_panel_takeoff_items([_panel(circuits=circuits)])
    assert len(items) == 1 + 4 + 2  # enclosure + 4 breaker groups + 2 feeders


def test_synthesize_returns_empty_for_empty_input() -> None:
    assert synthesize_panel_takeoff_items([]) == []
    assert synthesize_panel_takeoff_items(None) == []


def test_synthesize_accepts_panel_schedule_result() -> None:
    """The function accepts a PanelScheduleResult OR a plain list."""
    result = PanelScheduleResult(
        pages=[0], panels=[_panel()], confidence=0.9, raw_table_text="",
    )
    items = synthesize_panel_takeoff_items(result)
    assert len(items) == 3


def test_synthesize_skips_panels_with_no_id() -> None:
    panel = _panel(panel_id="")
    assert synthesize_panel_takeoff_items([panel]) == []


# ---------------------------------------------------------------------------
# Panel-enclosure row
# ---------------------------------------------------------------------------


def test_enclosure_panelboard_for_small_panel() -> None:
    """A 200A bus panel routes to 26 24 16 panelboards."""
    items = synthesize_panel_takeoff_items([_panel(bus_amps=200)])
    enc = next(it for it in items if it.csi_section == "26 24 16")
    assert enc.unit == "EA"
    assert enc.quantity == 1.0
    assert "Panelboard" in enc.description


def test_enclosure_switchboard_above_400a() -> None:
    """Bus amps > 400A routes to 26 24 13 switchboards."""
    items = synthesize_panel_takeoff_items([_panel(bus_amps=800,
                                                       main_breaker_amps=None,
                                                       mcb_or_mlo="MLO")])
    sections = {it.csi_section for it in items}
    assert "26 24 13" in sections
    assert "26 24 16" not in sections
    enc = next(it for it in items if it.csi_section == "26 24 13")
    assert "Switchboard" in enc.description


def test_enclosure_threshold_is_strict_above_400a() -> None:
    """Exactly 400A bus is panelboard (boundary is > 400A → switchboard)."""
    boundary_items = synthesize_panel_takeoff_items(
        [_panel(bus_amps=_PANEL_BOARD_BUS_THRESHOLD_A,
                  main_breaker_amps=_PANEL_BOARD_BUS_THRESHOLD_A)]
    )
    over_items = synthesize_panel_takeoff_items(
        [_panel(bus_amps=_PANEL_BOARD_BUS_THRESHOLD_A + 1,
                  main_breaker_amps=_PANEL_BOARD_BUS_THRESHOLD_A + 1)]
    )
    assert any(it.csi_section == "26 24 16" for it in boundary_items)
    assert any(it.csi_section == "26 24 13" for it in over_items)


def test_enclosure_falls_back_to_main_breaker_amps_for_classification() -> None:
    """When bus_amps is None we use main_breaker_amps for the class."""
    items = synthesize_panel_takeoff_items(
        [_panel(bus_amps=None, main_breaker_amps=600, mcb_or_mlo="MCB")]
    )
    assert any(it.csi_section == "26 24 13" for it in items)


def test_enclosure_default_panelboard_when_no_rating() -> None:
    """No bus_amps + no main_breaker_amps → defaults to panelboard."""
    items = synthesize_panel_takeoff_items(
        [_panel(bus_amps=None, main_breaker_amps=None, mcb_or_mlo=None)]
    )
    assert any(it.csi_section == "26 24 16" for it in items)


def test_enclosure_confidence_matches_panel_confidence() -> None:
    panel = _panel(confidence=0.91)
    items = synthesize_panel_takeoff_items([panel])
    enc = next(it for it in items if it.csi_section.startswith("26 24"))
    assert enc.confidence == pytest.approx(0.91)


def test_enclosure_description_contains_panel_id_and_rating() -> None:
    panel = _panel(panel_id="PNL-A", main_breaker_amps=200,
                    mcb_or_mlo="MCB", voltage="120/208V", phase_count=3)
    items = synthesize_panel_takeoff_items([panel])
    enc = next(it for it in items if it.csi_section == "26 24 16")
    desc = enc.description
    assert "PNL-A" in desc
    assert "200A" in desc
    assert "MCB" in desc
    assert "120/208V" in desc


# ---------------------------------------------------------------------------
# Branch-breaker rows
# ---------------------------------------------------------------------------


def test_branch_breakers_grouped_by_amp_size() -> None:
    """20A × 12 + 30A × 4 + 50A × 2 → 3 distinct rows, EA-unit, summed counts."""
    circuits = (
        [_circuit(str(n), 20) for n in range(1, 13)]
        + [_circuit(str(n), 30) for n in range(13, 17)]
        + [_circuit(str(n), 50) for n in range(17, 19)]
    )
    items = synthesize_panel_takeoff_items([_panel(circuits=circuits)])
    breaker_rows = [it for it in items if it.csi_section == "26 28 16"]
    assert len(breaker_rows) == 3
    by_amps = {}
    for row in breaker_rows:
        # description carries the amp size: "Branch breakers 20A (...)"
        for amps in (20, 30, 50, 100):
            if f"{amps}A" in row.description:
                by_amps[amps] = row.quantity
                break
    assert by_amps == {20: 12.0, 30: 4.0, 50: 2.0}


def test_branch_breakers_confidence_is_panel_data_high() -> None:
    """Branch-breaker rows synthesise at 0.85 (panel data is reliable)."""
    circuits = [_circuit("1", 20), _circuit("3", 30)]
    items = synthesize_panel_takeoff_items([_panel(circuits=circuits)])
    breaker_rows = [it for it in items if it.csi_section == "26 28 16"]
    assert all(row.confidence == pytest.approx(0.85) for row in breaker_rows)
    assert all(row.unit == "EA" for row in breaker_rows)


def test_branch_breakers_skip_circuits_without_amps() -> None:
    """Circuits whose breaker_amps is None are skipped (no fabricated rows)."""
    circuits = [
        _circuit("1", 20),
        _circuit("3", None, desc="Spare"),
        _circuit("5", 20),
    ]
    items = synthesize_panel_takeoff_items([_panel(circuits=circuits)])
    breaker_rows = [it for it in items if it.csi_section == "26 28 16"]
    assert len(breaker_rows) == 1
    assert breaker_rows[0].quantity == 2.0


def test_branch_breakers_ordered_ascending_by_amps() -> None:
    """Stable ordering: 20A row appears before 50A row before 100A row."""
    circuits = [
        _circuit("1", 100), _circuit("3", 20), _circuit("5", 50),
        _circuit("7", 30),
    ]
    items = synthesize_panel_takeoff_items([_panel(circuits=circuits)])
    breaker_rows = [it for it in items if it.csi_section == "26 28 16"]
    seen_amps: list[int] = []
    for row in breaker_rows:
        for amps in (20, 30, 50, 100):
            if f"{amps}A" in row.description:
                seen_amps.append(amps)
                break
    assert seen_amps == [20, 30, 50, 100]


def test_branch_breakers_empty_panel_emits_no_breaker_rows() -> None:
    """A panel with zero circuits still emits enclosure + 2 feeders, but no breakers."""
    items = synthesize_panel_takeoff_items([_panel(circuits=[])])
    breaker_rows = [it for it in items if it.csi_section == "26 28 16"]
    assert breaker_rows == []


# ---------------------------------------------------------------------------
# Feeder conductor + conduit rows (parametric defaults)
# ---------------------------------------------------------------------------


def test_feeder_conductor_emits_parametric_default() -> None:
    """Always emits one feeder-wire row at 50 LF / 0.55 confidence."""
    items = synthesize_panel_takeoff_items([_panel()])
    wire_rows = [it for it in items if it.csi_section == "26 05 19"]
    assert len(wire_rows) == 1
    row = wire_rows[0]
    assert row.unit == "LF"
    assert row.quantity == pytest.approx(_FEEDER_PARAMETRIC_LF)
    assert row.confidence == pytest.approx(_FEEDER_CONFIDENCE)


def test_feeder_conduit_emits_parametric_default() -> None:
    items = synthesize_panel_takeoff_items([_panel()])
    raceway_rows = [it for it in items if it.csi_section == "26 05 33"]
    assert len(raceway_rows) == 1
    row = raceway_rows[0]
    assert row.unit == "LF"
    assert row.quantity == pytest.approx(_FEEDER_PARAMETRIC_LF)
    assert row.confidence == pytest.approx(_FEEDER_CONFIDENCE)


def test_feeder_rows_emit_even_without_size_information() -> None:
    """A panel with no feeder size still gets the parametric 50 LF rows."""
    items = synthesize_panel_takeoff_items(
        [_panel(feeder_conductor_size=None, feeder_conduit_size=None)]
    )
    sections = [it.csi_section for it in items]
    assert "26 05 19" in sections
    assert "26 05 33" in sections


def test_feeder_conductor_description_includes_size_when_known() -> None:
    items = synthesize_panel_takeoff_items(
        [_panel(feeder_conductor_size="3/0 AWG CU")]
    )
    wire_rows = [it for it in items if it.csi_section == "26 05 19"]
    assert "3/0 AWG CU" in wire_rows[0].description


def test_feeder_confidence_routes_to_hand_takeoff_band() -> None:
    """The 0.55 default lands the row in HAND_TAKEOFF / OPERATOR_REVIEW band (< 0.65)."""
    items = synthesize_panel_takeoff_items([_panel()])
    feeder_rows = [it for it in items
                   if it.csi_section in {"26 05 19", "26 05 33"}]
    assert all(row.confidence < 0.65 for row in feeder_rows)


# ---------------------------------------------------------------------------
# Multi-panel + sheet propagation
# ---------------------------------------------------------------------------


def test_two_panels_double_the_item_count() -> None:
    """A two-panel input doubles the per-panel synthesis output."""
    panels = [_panel(panel_id="PNL-A"), _panel(panel_id="PNL-B")]
    items = synthesize_panel_takeoff_items(panels)
    assert len(items) == 6  # 2 × (1 enclosure + 2 feeders), no circuits


def test_multi_panel_unique_descriptions() -> None:
    """Each panel's rows are tagged with its own ID."""
    panels = [_panel(panel_id="PNL-A"), _panel(panel_id="MDP", bus_amps=600,
                                                  main_breaker_amps=None)]
    items = synthesize_panel_takeoff_items(panels)
    descriptions = " ".join(it.description for it in items)
    assert "PNL-A" in descriptions
    assert "MDP" in descriptions


def test_source_sheet_propagates_from_panel_record() -> None:
    """source_sheet on the PanelRecord flows into each TakeoffItem."""
    items = synthesize_panel_takeoff_items([_panel(source_sheet="E2.0")])
    assert all(it.source_sheet_ids == ["E2.0"] for it in items)


def test_explicit_sheet_id_override_takes_precedence() -> None:
    """Caller-supplied sheet_id wins over panel.source_sheet."""
    items = synthesize_panel_takeoff_items([_panel(source_sheet="E1.0")],
                                                sheet_id="E2.5")
    assert all(it.source_sheet_ids == ["E2.5"] for it in items)


# ---------------------------------------------------------------------------
# Notes / source-tag for downstream dedupe
# ---------------------------------------------------------------------------


def test_notes_carry_source_tag_first() -> None:
    """Notes always lead with ``source=panel_schedule_prepass``."""
    items = synthesize_panel_takeoff_items([_panel()])
    for it in items:
        assert (it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_PANEL}")


def test_notes_carry_panel_mark() -> None:
    """Notes include ``mark=<panel_id>`` so per-mark dedupe can grep."""
    items = synthesize_panel_takeoff_items([_panel(panel_id="MDP-1")])
    for it in items:
        assert "mark=MDP-1" in (it.notes or "")


def test_notes_distinguish_each_role() -> None:
    """Notes carry the synthesis role token (enclosure / breakers / feeder_wire / feeder_conduit)."""
    items = synthesize_panel_takeoff_items(
        [_panel(circuits=[_circuit("1", 20)])]
    )
    role_rows: dict[str, list[TakeoffItem]] = {}
    for it in items:
        notes = it.notes or ""
        for role in ("enclosure", "breakers", "feeder_wire", "feeder_conduit"):
            if f"role={role}" in notes:
                role_rows.setdefault(role, []).append(it)
    # All four roles surface for a panel with at least one branch breaker.
    assert set(role_rows) == {"enclosure", "breakers", "feeder_wire",
                                "feeder_conduit"}
    assert len(role_rows["enclosure"]) == 1
    assert len(role_rows["feeder_wire"]) == 1
    assert len(role_rows["feeder_conduit"]) == 1
