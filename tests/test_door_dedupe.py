"""Tests for Phase T3 ``dedupe_doors_against_synthesis``.

Mirrors the conventions in :mod:`tests.test_takeoff_synthesis`: pure unit
tests against the Pydantic schema (no PDF I/O), plus one integration-smoke
test that round-trips a synthesised result through
:func:`core.takeoff.reconcile`.
"""

from __future__ import annotations

import pytest

from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG,
    synthesize_door_takeoff_items,
)
from core.schemas import (
    DoorRecord,
    DoorScheduleResult,
    DrawingPrepassResult,
    SheetExtraction,
    TakeoffItem,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthesised(mark: str, section: str = "08 11 13") -> TakeoffItem:
    """Build a TakeoffItem mirroring what the T2 synthesiser emits."""
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=f"Door {mark} \u2014 HM 3'-0\" x 7'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG}; mark={mark}; type=HM",
    )


def _llm_aggregate(desc: str, qty: int = 12, section: str = "08 11 13") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=desc,
        quantity=float(qty),
        unit="EA",
        confidence=0.85,
    )


def _llm_door_with_mark(mark: str, section: str = "08 11 13") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=f"Door {mark} (LLM-extracted, hollow metal)",
        quantity=1.0,
        unit="EA",
        confidence=0.75,
    )


def _non_door(
    division: str = "09",
    section: str = "09 91 23",
    desc: str = "Interior wall painting (two coats)",
    unit: str = "SF",
) -> TakeoffItem:
    return TakeoffItem(
        csi_division=division,
        csi_section=section,
        description=desc,
        quantity=500.0,
        unit=unit,
        confidence=0.65,
    )


# ---------------------------------------------------------------------------
# 1. Empty / trivial input
# ---------------------------------------------------------------------------


def test_empty_input_returns_empty() -> None:
    assert dedupe_doors_against_synthesis([]) == []


# ---------------------------------------------------------------------------
# 2. Safety rule: no synthesised doors -> input unchanged
# ---------------------------------------------------------------------------


def test_no_synthesised_doors_returns_input_unchanged() -> None:
    """Without a deterministic fallback we must keep the legacy aggregates."""
    items = [
        _llm_aggregate("Hollow metal doors", 12),
        _llm_door_with_mark("D101"),
        _non_door(),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert out == items
    # Identity preserved -- pure function returns the same rows.
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 3. Same-mark dedupe
# ---------------------------------------------------------------------------


def test_synthesised_with_matching_mark_drops_llm_door() -> None:
    items = [
        _synthesised("101A"),
        _llm_door_with_mark("101A"),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert len(out) == 1
    assert (out[0].notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}")


def test_synthesised_and_non_matching_llm_door_both_kept() -> None:
    items = [
        _synthesised("101A"),
        _llm_door_with_mark("999Z"),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert len(out) == 2
    assert any((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}")
               for it in out)
    assert any("999Z" in (it.description or "") for it in out)


# ---------------------------------------------------------------------------
# 4. Legacy-aggregate dedupe
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "desc",
    [
        "Hollow metal doors",
        "Hollow metal doors: 12 EA",
        "Solid-core wood doors",
        "Solid core wood doors",
        "Wood doors",
        "Steel doors",
        "Aluminum doors",
        "Glass doors",
        "Doors (type unspecified)",
    ],
)
def test_legacy_aggregate_dropped_when_any_synthesised_door_exists(desc: str) -> None:
    items = [
        _synthesised("101A"),
        _llm_aggregate(desc),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert len(out) == 1
    assert out[0].description.startswith("Door 101A")


def test_legacy_aggregate_preserved_when_no_synthesised_doors() -> None:
    """Safety rule -- don't strip aggregates when nothing else covers them."""
    items = [
        _llm_aggregate("Hollow metal doors", 12),
        _non_door(),
    ]
    assert dedupe_doors_against_synthesis(items) == items


# ---------------------------------------------------------------------------
# 5. Non-door rows are never touched
# ---------------------------------------------------------------------------


def test_non_door_division_items_untouched() -> None:
    items = [
        _synthesised("101A"),
        _llm_door_with_mark("101A"),                        # dropped (mark match)
        _non_door("09", "09 91 23", "Painting"),            # kept
        _non_door("06", "06 10 00", "Rough carpentry"),     # kept
        _non_door("23", "23 00 00", "Rooftop unit", "EA"),  # kept
    ]
    out = dedupe_doors_against_synthesis(items)
    divs = sorted(it.csi_division for it in out)
    assert divs == ["06", "08", "09", "23"]
    assert sum(1 for it in out if it.csi_division == "08") == 1


# ---------------------------------------------------------------------------
# 6. Combinatorial: multiple synthesised + multiple LLM rows
# ---------------------------------------------------------------------------


def test_combinatorial_preservation_and_drops() -> None:
    items = [
        _synthesised("101A"),
        _synthesised("102B"),
        _synthesised("103"),
        _llm_door_with_mark("101A"),                            # drop (mark)
        _llm_door_with_mark("102B"),                            # drop (mark)
        _llm_door_with_mark("D999"),                            # keep
        _llm_aggregate("Hollow metal doors", 3),                # drop (aggregate)
        _llm_aggregate("Solid-core wood doors", 2),             # drop (aggregate)
        _non_door(),                                            # keep
    ]
    out = dedupe_doors_against_synthesis(items)

    descs = [it.description for it in out]
    assert "Hollow metal doors" not in descs
    assert "Solid-core wood doors" not in descs
    assert any("D999" in d for d in descs)
    assert any("Door 101A" in d for d in descs)
    assert any("Door 102B" in d for d in descs)
    assert any("Door 103" in d for d in descs)
    synth = [it for it in out
             if (it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}")]
    assert len(synth) == 3


# ---------------------------------------------------------------------------
# 7. Conservative dedupe: no recognisable mark -> preserved
# ---------------------------------------------------------------------------


def test_llm_door_with_no_recognisable_mark_preserved() -> None:
    """Unparseable LLM rows survive -- don't drop what we cannot match."""
    items = [
        _synthesised("101A"),
        TakeoffItem(
            csi_division="08",
            csi_section="08 14 13",
            description="Wood door, custom oak veneer, single leaf",
            quantity=1.0,
            unit="EA",
            confidence=0.70,
        ),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# 8. All synthesised, no LLM rows
# ---------------------------------------------------------------------------


def test_all_synthesised_no_llm_returns_unchanged() -> None:
    items = [_synthesised("101A"), _synthesised("102B")]
    out = dedupe_doors_against_synthesis(items)
    assert out == items
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 9. Ordering is preserved for survivors
# ---------------------------------------------------------------------------


def test_original_order_preserved() -> None:
    items = [
        _non_door(),
        _synthesised("101A"),
        _llm_door_with_mark("D999"),
        _llm_door_with_mark("101A"),  # dropped (mark match)
        _synthesised("102B"),
        _llm_aggregate("Hollow metal doors"),  # dropped (aggregate)
    ]
    out = dedupe_doors_against_synthesis(items)
    assert [it.description for it in out] == [
        items[0].description,  # non-door
        items[1].description,  # synthesised 101A
        items[2].description,  # llm D999 (kept)
        items[4].description,  # synthesised 102B
    ]


# ---------------------------------------------------------------------------
# 10. Short marks are not dedupe candidates
# ---------------------------------------------------------------------------


def test_short_mark_does_not_cause_false_positive_drop() -> None:
    """A single-char mark would be too promiscuous; LLM row survives."""
    items = [
        _synthesised("A"),
        # LLM row whose description coincidentally contains the letter "A".
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal frame ALUM kerf",
            quantity=1.0, unit="EA", confidence=0.70,
        ),
    ]
    out = dedupe_doors_against_synthesis(items)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# 11. Word-boundary safety -- mark "10" must not match "1010"
# ---------------------------------------------------------------------------


def test_mark_token_boundary_prevents_substring_collision() -> None:
    items = [
        _synthesised("10"),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Door 1010 (LLM) hollow metal",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
    ]
    out = dedupe_doors_against_synthesis(items)
    # Both kept -- "10" is not a token in "1010".
    assert len(out) == 2


# ---------------------------------------------------------------------------
# 12. Integration smoke test through reconcile()
# ---------------------------------------------------------------------------


def test_integration_reconcile_dedupes_llm_aggregate_when_synthesised_exists() -> None:
    """End-to-end: reconcile() must apply T3 dedupe to the merged takeoffs."""
    schedule = DoorScheduleResult(
        pages=[0],
        doors=[
            DoorRecord(mark="101", type="HM", width_in=36.0, height_in=84.0),
            DoorRecord(mark="102", type="HM", width_in=36.0, height_in=84.0),
        ],
        confidence=0.9,
    )
    llm_aggregate = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Hollow metal doors",
        quantity=12.0,
        unit="EA",
        confidence=0.85,
    )
    extraction = SheetExtraction(
        sheet_id="A0.1",
        prepass=DrawingPrepassResult(door_schedule=schedule),
        raw_takeoffs=[llm_aggregate],
    )
    project = reconcile([extraction])

    aggregates = [t for t in project.takeoffs if t.description == "Hollow metal doors"]
    assert aggregates == [], "Phase T3 should retire the legacy LLM aggregate"

    synthesised = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}")
    ]
    assert len(synthesised) == 2
    descs = " ".join(t.description for t in synthesised)
    assert "101" in descs
    assert "102" in descs


def test_integration_reconcile_no_synthesised_keeps_llm_aggregate() -> None:
    """Safety rule round-tripped through reconcile()."""
    llm_aggregate = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Hollow metal doors",
        quantity=7.0,
        unit="EA",
        confidence=0.85,
    )
    extraction = SheetExtraction(
        sheet_id="A0.1",
        raw_takeoffs=[llm_aggregate],
    )
    project = reconcile([extraction])
    aggregates = [t for t in project.takeoffs if t.description == "Hollow metal doors"]
    assert len(aggregates) == 1
    assert aggregates[0].quantity == 7.0


def test_integration_synthesiser_to_dedupe_round_trip() -> None:
    """Compose T2 synthesis + T3 dedupe directly (no reconcile)."""
    schedule = DoorScheduleResult(
        pages=[0],
        doors=[
            DoorRecord(mark="101A", type="HM", width_in=36.0, height_in=84.0),
            DoorRecord(mark="102",  type="WD", width_in=32.0, height_in=80.0),
        ],
        confidence=0.9,
    )
    synth = synthesize_door_takeoff_items(schedule, sheet_id="A0.1")
    llm = [
        _llm_door_with_mark("101A"),                  # drop -- same mark
        _llm_aggregate("Solid-core wood doors", 5),   # drop -- legacy
        _llm_door_with_mark("D-200"),                 # keep -- different mark
    ]
    out = dedupe_doors_against_synthesis(synth + llm)

    # 2 synthesised + 1 surviving LLM = 3.
    assert len(out) == 3
    descs = [it.description for it in out]
    assert any("Door 101A" in d for d in descs)
    assert any("Door 102" in d for d in descs)
    assert any("D-200" in d for d in descs)
    assert "Solid-core wood doors" not in descs
