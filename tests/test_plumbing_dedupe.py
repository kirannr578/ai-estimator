"""Tests for the Phase T2.9 plumbing-vs-synthesis dedupe pass.

Mirrors ``test_hvac_dedupe`` for plumbing: builds a small list of
``TakeoffItem`` rows mixing synthesised plumbing fixtures (carrying
the ``source=plumbing_schedule_prepass`` tag in their notes) with
legacy LLM aggregate rows under Division 22 (and a few non-22 rows
to confirm the dedupe never touches them).  Asserts which survive.
"""

from __future__ import annotations

from core.extraction.plumbing_dedupe import dedupe_plumbing_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_PLUMBING,
    synthesize_plumbing_takeoff_items,
)
from core.schemas import PlumbingFixtureRecord, TakeoffItem


def _synth_wc(tag: str = "WC-1") -> list[TakeoffItem]:
    return synthesize_plumbing_takeoff_items([
        PlumbingFixtureRecord(
            fixture_tag=tag,
            fixture_type="WATER_CLOSET",
            description="Water closet",
            manufacturer="American Standard",
            model_number="3461.001",
            flow_rate_value=1.28,
            flow_rate_unit="GPF",
            quantity=2,
        ),
    ])


def _llm(description: str, *, csi_section: str | None = "22 40 00",
         csi_division: str = "22") -> TakeoffItem:
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=1.0,
        unit="EA",
        confidence=0.7,
    )


def test_dedupe_suppresses_llm_aggregate_when_synthesis_present() -> None:
    """LLM 'Plumbing Fixtures' aggregate dropped when synthesised WCs exist."""
    items = _synth_wc() + [
        _llm("Plumbing Fixtures"),
        _llm("Water closets"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    # Synthesised rows survive.
    assert any("Plumbing fixture WC-1" in d for d in descriptions)
    # Aggregate descriptions dropped.
    assert "Plumbing Fixtures" not in descriptions
    assert "Water closets" not in descriptions


def test_dedupe_suppresses_per_mark_llm_row() -> None:
    """LLM 'WC-1 toilet installation' dropped when WC-1 was synthesised."""
    items = _synth_wc() + [
        _llm("WC-1 toilet installation"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    assert "WC-1 toilet installation" not in descriptions


def test_dedupe_preserves_unrelated_plumbing_llm_rows() -> None:
    """LLM rows for a different mark are KEPT (only WC-1 was synthesised)."""
    items = _synth_wc(tag="WC-1") + [
        # Different mark, generic description shape that doesn't
        # match the legacy aggregate regex.
        _llm("Janitor closet trap primer", csi_section="22 14 26"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    assert "Janitor closet trap primer" in descriptions


def test_dedupe_does_not_touch_division_26_electrical() -> None:
    """Electrical (CSI 26) rows are NEVER touched by the plumbing dedupe."""
    items = _synth_wc() + [
        _llm("Electrical receptacle, 20A", csi_section="26 27 26",
              csi_division="26"),
        _llm("LED downlight fixture", csi_section="26 51 13",
              csi_division="26"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    assert "Electrical receptacle, 20A" in descriptions
    assert "LED downlight fixture" in descriptions


def test_dedupe_does_not_touch_division_23_hvac() -> None:
    """HVAC (CSI 23) rows are NEVER touched by the plumbing dedupe."""
    items = _synth_wc() + [
        _llm("AHU-1 installation", csi_section="23 73 13",
              csi_division="23"),
        _llm("HVAC ductwork allowance", csi_section="23 31 00",
              csi_division="23"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    assert "AHU-1 installation" in descriptions
    assert "HVAC ductwork allowance" in descriptions


def test_dedupe_does_not_touch_division_08_doors() -> None:
    """Door (CSI 08) rows are NEVER touched by the plumbing dedupe."""
    items = _synth_wc() + [
        _llm("Hollow metal door 3'-0\" x 7'-0\"",
              csi_section="08 11 13", csi_division="08"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    descriptions = [s.description for s in survivors]
    assert "Hollow metal door 3'-0\" x 7'-0\"" in descriptions


def test_dedupe_no_op_when_no_synthesis_present() -> None:
    """Safety rule: no synthesised plumbing → input returned unchanged."""
    items = [
        _llm("Plumbing Fixtures"),
        _llm("Water closets"),
        _llm("Floor drains"),
    ]
    survivors = dedupe_plumbing_against_synthesis(items)
    assert len(survivors) == 3
    descriptions = [s.description for s in survivors]
    assert "Plumbing Fixtures" in descriptions
    assert "Water closets" in descriptions
    assert "Floor drains" in descriptions


def test_dedupe_preserves_synthesised_rows() -> None:
    """All synthesised rows survive the dedupe pass."""
    synth = _synth_wc()
    items = synth + [_llm("Plumbing Fixtures")]
    survivors = dedupe_plumbing_against_synthesis(items)
    # Every synthesised row (carrying the source tag in notes) must
    # appear in survivors.
    survivor_notes = [s.notes for s in survivors if s.notes]
    synth_tag_count = sum(
        1 for n in survivor_notes
        if n.startswith(f"source={SYNTHESIS_SOURCE_TAG_PLUMBING}")
    )
    assert synth_tag_count == len(synth)
