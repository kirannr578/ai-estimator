"""Tests for Phase T2.7 ``dedupe_lighting_against_synthesis``.

Mirror of :mod:`tests.test_panel_dedupe` / :mod:`tests.test_finish_dedupe`
for the lighting-fixture family. Pure unit tests against the Pydantic
schema (no PDF I/O). Verifies the lighting-specific discriminators (CSI
prefixes ``26 51`` / ``26 55``; legacy-aggregate regex shapes) and the
cross-pollination safety guarantee: lighting dedupe must NEVER drop
door / window / finish / panel rows or other Division-26 families like
receptacles or feeders.
"""

from __future__ import annotations

from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.lighting_dedupe import dedupe_lighting_against_synthesis
from core.extraction.panel_dedupe import dedupe_panels_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_LIGHTING,
    SYNTHESIS_SOURCE_TAG_PANEL,
    synthesize_lighting_takeoff_items,
)
from core.schemas import (
    LightingFixtureRecord,
    TakeoffItem,
)


# ---------------------------------------------------------------------------
# Helpers — synthesised lighting rows (what the T2.7 synthesiser emits)
# ---------------------------------------------------------------------------


def _fixture(
    *,
    fixture_tag: str = "A1",
    description: str = "2x4 LED RECESSED TROFFER 4000K",
    manufacturer: str | None = "Lithonia",
    catalog_number: str | None = "2BLT4-40L-LP840",
    wattage: float | None = 40.0,
    voltage: str | None = "277V",
    lamp_type: str | None = "LED",
    mounting: str | None = "RECESSED",
    quantity: int | None = None,
    confidence: float = 0.9,
    source_sheet: str | None = "E2.0",
) -> LightingFixtureRecord:
    return LightingFixtureRecord(
        fixture_tag=fixture_tag,
        description=description,
        manufacturer=manufacturer,
        catalog_number=catalog_number,
        wattage=wattage,
        voltage=voltage,
        lamp_type=lamp_type,
        mounting=mounting,
        quantity=quantity,
        confidence=confidence,
        source_sheet=source_sheet,
    )


def _synthesised(*tags: str) -> list[TakeoffItem]:
    return synthesize_lighting_takeoff_items(
        [_fixture(fixture_tag=t) for t in tags]
    )


# ---------------------------------------------------------------------------
# Helpers — LLM-extracted rows (no SYNTHESIS source tag)
# ---------------------------------------------------------------------------


def _llm(desc: str, *, section: str | None = "26 51 13",
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
    assert dedupe_lighting_against_synthesis([]) == []


def test_dedupe_no_synthesis_keeps_all_llm_rows() -> None:
    """No synthesised lighting anywhere → return input unchanged."""
    llm_items = [
        _llm("LED downlights"),
        _llm("2x4 troffer fixtures"),
        _llm("Wall sconces"),
    ]
    assert dedupe_lighting_against_synthesis(llm_items) == llm_items


def test_dedupe_only_synthesis_returns_them_unchanged() -> None:
    items = _synthesised("A1")
    assert dedupe_lighting_against_synthesis(items) == items


# ---------------------------------------------------------------------------
# Per-mark suppression — synthesised fixture suppresses matching LLM line
# ---------------------------------------------------------------------------


def test_dedupe_per_mark_suppresses_llm_type_a_fixture() -> None:
    """A synthesised ``Fixture A1`` suppresses an LLM ``Type A1 fixture`` row."""
    syn = _synthesised("A1")
    llm = _llm("Type A1 fixture — LED troffer")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out
    assert all(it in out for it in syn)


def test_dedupe_legacy_aggregate_led_downlights_suppressed() -> None:
    """The legacy LLM ``"LED downlights"`` aggregate is retired."""
    syn = _synthesised("A1")
    llm = _llm("LED downlights")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_aggregate_lighting_fixtures_with_count_suppressed(
) -> None:
    """``"Lighting Fixtures: 12 EA"`` legacy form drops out."""
    syn = _synthesised("A1")
    llm = _llm("Lighting Fixtures: 12 EA")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_aggregate_luminaires_suppressed() -> None:
    """Bare ``"Luminaires"`` rolls up dropped."""
    syn = _synthesised("A1")
    llm = _llm("Luminaires")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_aggregate_recessed_troffers_suppressed() -> None:
    syn = _synthesised("A1")
    llm = _llm("Recessed troffers")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out


def test_dedupe_legacy_aggregate_wall_sconces_suppressed() -> None:
    syn = _synthesised("B")
    llm = _llm("Wall-mounted sconces", section="26 51 19")
    out = dedupe_lighting_against_synthesis(syn + [llm])
    assert llm not in out


# ---------------------------------------------------------------------------
# Cross-pollination safety — never drop other families
# ---------------------------------------------------------------------------


def test_dedupe_does_not_suppress_electrical_receptacle() -> None:
    """``26 27 26`` receptacles are outside the lighting prefix set."""
    syn = _synthesised("A1")
    receptacle = _llm("Duplex receptacles", section="26 27 26")
    out = dedupe_lighting_against_synthesis(syn + [receptacle])
    assert receptacle in out


def test_dedupe_does_not_suppress_panel_row() -> None:
    """A panel row (``26 24 16``) must survive lighting dedupe."""
    syn = _synthesised("A1")
    panel = _llm("Electrical Panel A, 200A", section="26 24 16")
    out = dedupe_lighting_against_synthesis(syn + [panel])
    assert panel in out


def test_dedupe_does_not_suppress_feeder_conductor() -> None:
    """Feeder conductors (``26 05 19``) are not lighting rows."""
    syn = _synthesised("A1")
    feeder = _llm("Feeder conductor 3/0 AWG", section="26 05 19", unit="LF")
    out = dedupe_lighting_against_synthesis(syn + [feeder])
    assert feeder in out


def test_dedupe_does_not_suppress_door_row() -> None:
    """An ``08 ...`` door row must survive lighting dedupe."""
    syn = _synthesised("A1")
    door = _llm("Hollow metal door, 3'-0\" x 7'-0\"",
                  section="08 11 13", division="08")
    out = dedupe_lighting_against_synthesis(syn + [door])
    assert door in out


def test_dedupe_does_not_suppress_finish_row() -> None:
    """A ``09 ...`` finish row must survive lighting dedupe."""
    syn = _synthesised("A1")
    finish = _llm("Carpet flooring", section="09 68 13",
                    division="09", unit="SF", quantity=1200.0)
    out = dedupe_lighting_against_synthesis(syn + [finish])
    assert finish in out


# ---------------------------------------------------------------------------
# Composition — pipeline order with sibling dedupes
# ---------------------------------------------------------------------------


def test_dedupe_lighting_then_panel_pipeline_independent() -> None:
    """Running both lighting + panel dedupes leaves the other family intact.

    Lighting dedupe pass must not consume panel rows it didn't author;
    panel dedupe pass must not consume lighting rows it didn't author.
    """
    light_syn = _synthesised("A1")
    panel_llm = _llm("Electrical Panel A, 200A", section="26 24 16")
    light_llm = _llm("LED downlights")

    intermediate = dedupe_lighting_against_synthesis(
        light_syn + [panel_llm, light_llm]
    )
    # Lighting dedupe drops the LLM lighting aggregate but leaves the
    # LLM panel row in place (panel has no synthesised row in this set,
    # so panel dedupe would be a no-op anyway).
    assert light_llm not in intermediate
    assert panel_llm in intermediate
    assert all(it in intermediate for it in light_syn)

    final = dedupe_panels_against_synthesis(intermediate)
    # Panel dedupe is a safety-no-op here (no synthesised panel row).
    assert final == intermediate


def test_dedupe_preserves_input_ordering_for_survivors() -> None:
    """Original ordering preserved for every surviving row."""
    syn = _synthesised("A1")
    door = _llm("Hollow metal door", section="08 11 13", division="08")
    light_llm = _llm("LED downlights")
    panel = _llm("Panelboard", section="26 24 16")

    inputs = [door, syn[0], light_llm, panel]
    out = dedupe_lighting_against_synthesis(inputs)
    # The dropped row is ``light_llm``; the rest keep their relative order.
    assert out == [door, syn[0], panel]
