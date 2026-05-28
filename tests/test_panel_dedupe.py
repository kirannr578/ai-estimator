"""Tests for Phase T2.6 ``dedupe_panels_against_synthesis``.

Mirror of :mod:`tests.test_finish_dedupe` / :mod:`tests.test_window_dedupe`
for the electrical-panel family. Pure unit tests against the Pydantic
schema (no PDF I/O). Verifies the panel-specific discriminators
(CSI prefixes ``26 24`` / ``26 28``; legacy-aggregate regex shapes) and
the cross-pollination safety guarantee: panel dedupe must NEVER drop
door / window / finish rows, and must NEVER drop other Division-26
families like receptacles or lighting.
"""

from __future__ import annotations

from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.finish_dedupe import dedupe_finishes_against_synthesis
from core.extraction.panel_dedupe import dedupe_panels_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG,
    SYNTHESIS_SOURCE_TAG_FINISH,
    SYNTHESIS_SOURCE_TAG_PANEL,
    SYNTHESIS_SOURCE_TAG_WINDOW,
    synthesize_panel_takeoff_items,
)
from core.schemas import (
    CircuitEntry,
    PanelRecord,
    TakeoffItem,
)


# ---------------------------------------------------------------------------
# Helpers — synthesised panel rows (what the T2.6 synthesiser emits)
# ---------------------------------------------------------------------------


def _panel(panel_id: str = "PNL-A", *, bus_amps: int = 225,
            main_breaker_amps: int = 200, mcb_or_mlo: str = "MCB",
            voltage: str = "120/208V", phase_count: int = 3,
            circuits: list[CircuitEntry] | None = None) -> PanelRecord:
    return PanelRecord(
        panel_id=panel_id,
        voltage=voltage,
        phase_count=phase_count,
        main_breaker_amps=main_breaker_amps,
        bus_amps=bus_amps,
        mcb_or_mlo=mcb_or_mlo,
        feeder_conductor_size="3/0 AWG CU",
        feeder_conduit_size="2 inch",
        circuits=circuits or [],
        confidence=0.9,
        source_sheet="E1.0",
    )


def _synthesised_panel_items(panel_id: str = "PNL-A",
                                *, circuits: list[CircuitEntry] | None = None,
                                ) -> list[TakeoffItem]:
    return synthesize_panel_takeoff_items(
        [_panel(panel_id=panel_id, circuits=circuits)],
    )


# ---------------------------------------------------------------------------
# Helpers — LLM-extracted rows (no SYNTHESIS source tag)
# ---------------------------------------------------------------------------


def _llm(desc: str, *, section: str | None = "26 24 16",
           division: str = "26", quantity: float = 1.0, unit: str = "EA",
           confidence: float = 0.65, notes: str | None = None) -> TakeoffItem:
    return TakeoffItem(
        csi_division=division,
        csi_section=section,
        description=desc,
        quantity=quantity,
        unit=unit,
        confidence=confidence,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# Empty input — safety / no-op cases
# ---------------------------------------------------------------------------


def test_dedupe_empty_list_returns_empty() -> None:
    assert dedupe_panels_against_synthesis([]) == []


def test_dedupe_no_synthesis_keeps_all_llm_rows() -> None:
    """When no synthesised panel exists anywhere → return input unchanged."""
    llm_items = [
        _llm("Electrical Panel A, 200A"),
        _llm("Panelboard PNL-B"),
    ]
    assert dedupe_panels_against_synthesis(llm_items) == llm_items


def test_dedupe_only_synthesis_returns_them_unchanged() -> None:
    items = _synthesised_panel_items("PNL-A")
    assert dedupe_panels_against_synthesis(items) == items


# ---------------------------------------------------------------------------
# Per-mark suppression — synthesised panel suppresses matching LLM line
# ---------------------------------------------------------------------------


def test_dedupe_per_mark_suppresses_llm_panel_aggregate() -> None:
    """A synthesised ``Panel PNL-A`` suppresses an LLM ``Panel PNL-A`` row."""
    syn = _synthesised_panel_items("PNL-A")
    llm = _llm("Panel PNL-A — 200A MCB")
    out = dedupe_panels_against_synthesis(syn + [llm])
    assert llm not in out
    assert all(it in out for it in syn)


def test_dedupe_per_mark_suppresses_llm_panel_a_with_main_breaker() -> None:
    """LLM ``Electrical Panel A, 200A`` is suppressed by synthesised PNL-A.

    The legacy-aggregate regex catches the ``Electrical Panel`` heading
    prefix so even without a panel-mark match the row drops.
    """
    syn = _synthesised_panel_items("PNL-A")
    llm = _llm("Electrical Panel A, 200A")
    out = dedupe_panels_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_panelboard_aggregate_suppressed() -> None:
    """Bare ``Panelboard`` legacy aggregate drops when synthesis present."""
    syn = _synthesised_panel_items("PNL-A")
    llm = _llm("Panelboard")
    out = dedupe_panels_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_switchboard_aggregate_suppressed() -> None:
    """Bare ``Switchboard`` legacy aggregate also drops."""
    syn = _synthesised_panel_items("PNL-A")
    llm = _llm("Switchboard", section="26 24 13")
    out = dedupe_panels_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_branch_breakers_aggregate_suppressed() -> None:
    """``Branch Circuit Breakers`` aggregate drops when breaker synthesis exists."""
    syn = synthesize_panel_takeoff_items([
        _panel(panel_id="PNL-A", circuits=[
            CircuitEntry(circuit_number="1", breaker_amps=20,
                          load_description="Lighting", phase="A"),
            CircuitEntry(circuit_number="3", breaker_amps=20,
                          load_description="Outlets", phase="B"),
        ]),
    ])
    llm = _llm("Branch Circuit Breakers: 2 EA", section="26 28 16")
    out = dedupe_panels_against_synthesis(syn + [llm])
    assert llm not in out


# ---------------------------------------------------------------------------
# Other Division-26 families NOT suppressed (cross-pollination safety)
# ---------------------------------------------------------------------------


def test_dedupe_receptacles_not_suppressed() -> None:
    """Receptacles (26 27 26) are not in the panel-prefix set → preserved."""
    syn = _synthesised_panel_items("PNL-A")
    receptacle = _llm("Duplex receptacle", section="26 27 26",
                        quantity=24.0)
    out = dedupe_panels_against_synthesis(syn + [receptacle])
    assert receptacle in out


def test_dedupe_lighting_not_suppressed() -> None:
    """Lighting fixtures (26 51 ...) are preserved."""
    syn = _synthesised_panel_items("PNL-A")
    light = _llm("LED 2x4 troffer", section="26 51 19",
                   quantity=12.0)
    out = dedupe_panels_against_synthesis(syn + [light])
    assert light in out


def test_dedupe_grounding_not_suppressed() -> None:
    """Grounding bus / electrodes (26 05 26) preserved."""
    syn = _synthesised_panel_items("PNL-A")
    ground = _llm("Ground bus", section="26 05 26",
                    quantity=1.0)
    out = dedupe_panels_against_synthesis(syn + [ground])
    assert ground in out


def test_dedupe_feeder_wire_llm_row_preserved() -> None:
    """LLM feeder-wire rows (26 05 19) are kept — synthesis is parametric.

    The synthesised feeder rows ship a parametric 50 LF default at 0.55
    confidence; we want the LLM's run-length estimate (when present) to
    land in the worklist so the estimator can compare, not be silently
    suppressed.
    """
    syn = _synthesised_panel_items("PNL-A")
    feeder = _llm("3/0 AWG Cu feeder", section="26 05 19",
                    quantity=85.0, unit="LF")
    out = dedupe_panels_against_synthesis(syn + [feeder])
    assert feeder in out


# ---------------------------------------------------------------------------
# Cross-pollination — door / window / finish rows must NEVER be touched
# ---------------------------------------------------------------------------


def test_dedupe_does_not_drop_door_rows() -> None:
    """An LLM door row (08 14 16) is preserved even with panel synthesis present."""
    syn = _synthesised_panel_items("PNL-A")
    door = TakeoffItem(
        csi_division="08", csi_section="08 14 16",
        description="HM door 3'-0\" × 7'-0\"", quantity=12.0,
        unit="EA", confidence=0.7,
    )
    out = dedupe_panels_against_synthesis(syn + [door])
    assert door in out


def test_dedupe_does_not_drop_window_rows() -> None:
    syn = _synthesised_panel_items("PNL-A")
    window = TakeoffItem(
        csi_division="08", csi_section="08 51 13",
        description="AL window 6'-0\" × 4'-0\"", quantity=8.0,
        unit="EA", confidence=0.7,
    )
    out = dedupe_panels_against_synthesis(syn + [window])
    assert window in out


def test_dedupe_does_not_drop_finish_rows() -> None:
    syn = _synthesised_panel_items("PNL-A")
    floor = TakeoffItem(
        csi_division="09", csi_section="09 65 19",
        description="VCT-1 floor finish — Room 101", quantity=400.0,
        unit="SF", confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG_FINISH}; surface=floor",
    )
    out = dedupe_panels_against_synthesis(syn + [floor])
    assert floor in out


# ---------------------------------------------------------------------------
# Idempotency + multi-panel
# ---------------------------------------------------------------------------


def test_dedupe_is_idempotent() -> None:
    """Calling dedupe twice yields the same result."""
    syn = _synthesised_panel_items("PNL-A")
    llm = _llm("Electrical Panel A, 200A")
    out1 = dedupe_panels_against_synthesis(syn + [llm])
    out2 = dedupe_panels_against_synthesis(out1)
    assert out1 == out2


def test_dedupe_multi_panel_only_matching_mark_suppressed() -> None:
    """Synthesis for PNL-A suppresses ``Panel PNL-A`` but keeps ``Panel PNL-B``."""
    syn = (
        _synthesised_panel_items("PNL-A")
        + _synthesised_panel_items("PNL-B")
    )
    llm_a = _llm("Panel PNL-A — 200A MCB")
    llm_b_orphan = _llm("Panel PNL-C — 100A MCB")  # no synthesis
    out = dedupe_panels_against_synthesis(syn + [llm_a, llm_b_orphan])
    assert llm_a not in out
    # PNL-C has no synthesised counterpart → preserved.
    assert llm_b_orphan in out


# ---------------------------------------------------------------------------
# Interaction with door + finish dedupe (cross-family safety)
# ---------------------------------------------------------------------------


def test_dedupe_panel_then_door_no_cross_contamination() -> None:
    """Running panel dedupe + door dedupe in sequence preserves expected rows."""
    syn_panel = _synthesised_panel_items("PNL-A")
    door_aggregate = TakeoffItem(
        csi_division="08", csi_section="08 14 16",
        description="Doors", quantity=12.0, unit="EA",
        confidence=0.6,
    )
    items = syn_panel + [door_aggregate]
    out = dedupe_panels_against_synthesis(items)
    # Panel dedupe MUST leave the door alone (it has no panel synthesis match).
    assert door_aggregate in out
    # And the panel rows are all preserved (they ARE the synthesis).
    assert all(s in out for s in syn_panel)
