"""Tests for Phase T2.5 ``dedupe_windows_against_synthesis``.

Mirror of :mod:`tests.test_door_dedupe` for the window side of the
pipeline. Pure unit tests against the Pydantic schema (no PDF I/O),
plus integration-smoke tests that round-trip a synthesised result
through :func:`core.takeoff.reconcile`. Critically also verifies the
cross-pollination safety: window dedupe must NEVER drop door rows,
and door dedupe must NEVER drop window rows.
"""

from __future__ import annotations

import pytest

from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG,
    SYNTHESIS_SOURCE_TAG_WINDOW,
    synthesize_window_takeoff_items,
)
from core.extraction.window_dedupe import dedupe_windows_against_synthesis
from core.schemas import (
    DrawingPrepassResult,
    SheetExtraction,
    TakeoffItem,
    WindowRecord,
    WindowScheduleResult,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthesised(mark: str, section: str = "08 51 13") -> TakeoffItem:
    """Build a TakeoffItem mirroring what the T2.5 synthesiser emits."""
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=f"Window {mark} \u2014 ALUM 3'-0\" x 5'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG_WINDOW}; mark={mark}; type=ALUM",
    )


def _llm_aggregate(desc: str, qty: int = 8, section: str = "08 50 00") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=desc,
        quantity=float(qty),
        unit="EA",
        confidence=0.85,
    )


def _llm_window_with_mark(mark: str, section: str = "08 51 13") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section=section,
        description=f"Window {mark} (LLM-extracted, aluminum)",
        quantity=1.0,
        unit="EA",
        confidence=0.75,
    )


def _non_window_door(mark: str = "101") -> TakeoffItem:
    """A door row that lives in Division 08 but must never be touched."""
    return TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description=f"Door {mark} \u2014 HM 3'-0\" x 7'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG}; mark={mark}; type=HM",
    )


def _non_door_non_window(
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
    assert dedupe_windows_against_synthesis([]) == []


# ---------------------------------------------------------------------------
# 2. Safety rule: no synthesised windows -> input unchanged
# ---------------------------------------------------------------------------


def test_no_synthesised_windows_returns_input_unchanged() -> None:
    """Without a deterministic fallback we must keep the legacy aggregates."""
    items = [
        _llm_aggregate("Aluminum windows", 8),
        _llm_window_with_mark("W101"),
        _non_door_non_window(),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert out == items
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 3. Same-mark dedupe
# ---------------------------------------------------------------------------


def test_synthesised_with_matching_mark_drops_llm_window() -> None:
    items = [
        _synthesised("W-01"),
        _llm_window_with_mark("W-01"),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert len(out) == 1
    assert (out[0].notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")


def test_synthesised_and_non_matching_llm_window_both_kept() -> None:
    items = [
        _synthesised("W-01"),
        _llm_window_with_mark("Z999"),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert len(out) == 2
    assert any((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
               for it in out)
    assert any("Z999" in (it.description or "") for it in out)


# ---------------------------------------------------------------------------
# 4. Legacy-aggregate dedupe
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "desc",
    [
        "Windows",
        "Windows: 8 EA",
        "Aluminum windows",
        "Aluminum windows: 12 EA",
        "Vinyl windows",
        "Wood windows",
        "Steel windows",
        "Metal-clad windows",
        "Metal clad windows",
        "Storefront windows",
        "Glass windows",
    ],
)
def test_legacy_aggregate_dropped_when_any_synthesised_window_exists(desc: str) -> None:
    items = [
        _synthesised("W-01"),
        _llm_aggregate(desc),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert len(out) == 1
    assert out[0].description.startswith("Window W-01")


def test_legacy_aggregate_preserved_when_no_synthesised_windows() -> None:
    """Safety rule -- don't strip aggregates when nothing else covers them."""
    items = [
        _llm_aggregate("Windows", 8),
        _non_door_non_window(),
    ]
    assert dedupe_windows_against_synthesis(items) == items


# ---------------------------------------------------------------------------
# 5. Door rows are NEVER touched by window dedupe
# ---------------------------------------------------------------------------


def test_door_rows_untouched_by_window_dedupe() -> None:
    """Synthesised + LLM door rows survive the window dedupe pass intact."""
    items = [
        _synthesised("W-01"),
        _non_window_door("101"),
        TakeoffItem(  # LLM-extracted door (Division 08, NOT a window section)
            csi_division="08", csi_section="08 11 13",
            description="Door 999 (LLM)", quantity=1.0, unit="EA", confidence=0.75,
        ),
        TakeoffItem(  # door aggregate -- must survive a WINDOW dedupe pass
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=12.0, unit="EA", confidence=0.85,
        ),
    ]
    out = dedupe_windows_against_synthesis(items)
    # All non-window rows survive: 1 synth window + 1 synth door + 1 LLM door + 1 door aggregate.
    assert len(out) == 4
    desc_set = {it.description for it in out}
    assert "Hollow metal doors" in desc_set
    assert any("Door 101" in d for d in desc_set)
    assert any("Door 999" in d for d in desc_set)


def test_non_division_08_rows_untouched() -> None:
    items = [
        _synthesised("W-01"),
        _llm_window_with_mark("W-01"),                  # dropped (mark match)
        _non_door_non_window("09", "09 91 23", "Painting"),
        _non_door_non_window("06", "06 10 00", "Rough carpentry"),
        _non_door_non_window("23", "23 00 00", "Rooftop unit", "EA"),
    ]
    out = dedupe_windows_against_synthesis(items)
    divs = sorted(it.csi_division for it in out)
    assert divs == ["06", "08", "09", "23"]
    # Only the synthesised window survives in Division 08.
    assert sum(1 for it in out if it.csi_division == "08") == 1


# ---------------------------------------------------------------------------
# 6. Combinatorial: multiple synthesised + multiple LLM rows
# ---------------------------------------------------------------------------


def test_combinatorial_preservation_and_drops() -> None:
    items = [
        _synthesised("W-01"),
        _synthesised("W-02", section="08 53 13"),       # vinyl
        _synthesised("W-03", section="08 52 13"),       # wood
        _llm_window_with_mark("W-01"),                  # drop (mark)
        _llm_window_with_mark("W-02"),                  # drop (mark)
        _llm_window_with_mark("Z999"),                  # keep
        _llm_aggregate("Aluminum windows", 3),          # drop (aggregate)
        _llm_aggregate("Vinyl windows", 2),             # drop (aggregate)
        _non_door_non_window(),                         # keep
        _non_window_door("101"),                        # keep (door)
    ]
    out = dedupe_windows_against_synthesis(items)

    descs = [it.description for it in out]
    assert "Aluminum windows" not in descs
    assert "Vinyl windows" not in descs
    assert any("Z999" in d for d in descs)
    assert any("Window W-01" in d for d in descs)
    assert any("Window W-02" in d for d in descs)
    assert any("Window W-03" in d for d in descs)
    assert any("Door 101" in d for d in descs)        # door survived
    synth = [it for it in out
             if (it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")]
    assert len(synth) == 3


# ---------------------------------------------------------------------------
# 7. Conservative dedupe: no recognisable mark -> preserved
# ---------------------------------------------------------------------------


def test_llm_window_with_no_recognisable_mark_preserved() -> None:
    """Unparseable LLM rows survive -- don't drop what we cannot match."""
    items = [
        _synthesised("W-01"),
        TakeoffItem(
            csi_division="08",
            csi_section="08 51 13",
            description="Window, custom oak veneer, single",
            quantity=1.0,
            unit="EA",
            confidence=0.70,
        ),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert len(out) == 2


# ---------------------------------------------------------------------------
# 8. All synthesised, no LLM rows
# ---------------------------------------------------------------------------


def test_all_synthesised_no_llm_returns_unchanged() -> None:
    items = [_synthesised("W-01"), _synthesised("W-02")]
    out = dedupe_windows_against_synthesis(items)
    assert out == items
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 9. Ordering is preserved for survivors
# ---------------------------------------------------------------------------


def test_original_order_preserved() -> None:
    items = [
        _non_door_non_window(),                         # 0 keep
        _synthesised("W-01"),                           # 1 keep
        _llm_window_with_mark("Z999"),                  # 2 keep
        _llm_window_with_mark("W-01"),                  # 3 drop (mark match)
        _synthesised("W-02"),                           # 4 keep
        _llm_aggregate("Aluminum windows"),             # 5 drop (aggregate)
    ]
    out = dedupe_windows_against_synthesis(items)
    assert [it.description for it in out] == [
        items[0].description,  # non-window
        items[1].description,  # synthesised W-01
        items[2].description,  # llm Z999 (kept)
        items[4].description,  # synthesised W-02
    ]


# ---------------------------------------------------------------------------
# 10. Short marks are not dedupe candidates
# ---------------------------------------------------------------------------


def test_short_mark_does_not_cause_false_positive_drop() -> None:
    """A single-char mark would be too promiscuous; LLM row survives."""
    items = [
        _synthesised("A"),
        TakeoffItem(
            csi_division="08", csi_section="08 51 13",
            description="Aluminum frame", quantity=1.0, unit="EA", confidence=0.70,
        ),
    ]
    out = dedupe_windows_against_synthesis(items)
    assert len(out) == 2


def test_mark_token_boundary_prevents_substring_collision() -> None:
    items = [
        _synthesised("W1"),
        TakeoffItem(
            csi_division="08", csi_section="08 51 13",
            description="Window W101 (LLM) aluminum",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
    ]
    out = dedupe_windows_against_synthesis(items)
    # Both kept -- "W1" is not a token in "W101".
    assert len(out) == 2


# ---------------------------------------------------------------------------
# 11. Integration smoke tests through reconcile()
# ---------------------------------------------------------------------------


def test_integration_reconcile_dedupes_llm_aggregate_when_synthesised_exists() -> None:
    """End-to-end: reconcile() must apply T2.5 dedupe to the merged takeoffs."""
    schedule = WindowScheduleResult(
        pages=[0],
        windows=[
            WindowRecord(mark="W-01", type="ALUM", width_in=36.0, height_in=60.0),
            WindowRecord(mark="W-02", type="ALUM", width_in=36.0, height_in=60.0),
        ],
        confidence=0.9,
    )
    llm_aggregate = TakeoffItem(
        csi_division="08",
        csi_section="08 51 13",
        description="Aluminum windows",
        quantity=8.0,
        unit="EA",
        confidence=0.85,
    )
    extraction = SheetExtraction(
        sheet_id="A0.2",
        prepass=DrawingPrepassResult(window_schedule=schedule),
        raw_takeoffs=[llm_aggregate],
    )
    project = reconcile([extraction])

    aggregates = [t for t in project.takeoffs if t.description == "Aluminum windows"]
    assert aggregates == [], "Phase T2.5 should retire the legacy LLM aggregate"

    synthesised = [
        t for t in project.takeoffs
        if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
    ]
    assert len(synthesised) == 2
    descs = " ".join(t.description for t in synthesised)
    assert "W-01" in descs
    assert "W-02" in descs


def test_integration_reconcile_no_synthesised_keeps_llm_aggregate() -> None:
    """Safety rule round-tripped through reconcile()."""
    llm_aggregate = TakeoffItem(
        csi_division="08",
        csi_section="08 51 13",
        description="Aluminum windows",
        quantity=5.0,
        unit="EA",
        confidence=0.85,
    )
    extraction = SheetExtraction(
        sheet_id="A0.2",
        raw_takeoffs=[llm_aggregate],
    )
    project = reconcile([extraction])
    aggregates = [t for t in project.takeoffs if t.description == "Aluminum windows"]
    assert len(aggregates) == 1
    assert aggregates[0].quantity == 5.0


def test_integration_synthesiser_to_dedupe_round_trip() -> None:
    """Compose T2.5 synthesis + dedupe directly (no reconcile)."""
    schedule = WindowScheduleResult(
        pages=[0],
        windows=[
            WindowRecord(mark="W-01", type="ALUM", width_in=36.0, height_in=60.0),
            WindowRecord(mark="W-02", type="VINYL", width_in=32.0, height_in=56.0),
        ],
        confidence=0.9,
    )
    synth = synthesize_window_takeoff_items(schedule, sheet_id="A0.2")
    llm = [
        _llm_window_with_mark("W-01"),                  # drop -- same mark
        _llm_aggregate("Vinyl windows", 5),             # drop -- legacy
        _llm_window_with_mark("Z200"),                  # keep -- different mark
    ]
    out = dedupe_windows_against_synthesis(synth + llm)

    # 2 synthesised + 1 surviving LLM = 3.
    assert len(out) == 3
    descs = [it.description for it in out]
    assert any("Window W-01" in d for d in descs)
    assert any("Window W-02" in d for d in descs)
    assert any("Z200" in d for d in descs)
    assert "Vinyl windows" not in descs


def test_door_dedupe_never_touches_window_rows() -> None:
    """Cross-pollination safety: door dedupe must leave windows alone."""
    items = [
        # Synthesised door + LLM door aggregate -- door dedupe should drop the aggregate.
        _non_window_door("101"),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=12.0, unit="EA", confidence=0.85,
        ),
        # Synthesised window + LLM window aggregate -- both must survive.
        _synthesised("W-01"),
        _llm_aggregate("Aluminum windows", 8),
    ]
    out = dedupe_doors_against_synthesis(items)
    descs = {it.description for it in out}
    # Door aggregate dropped, both window rows survive.
    assert "Hollow metal doors" not in descs
    assert "Aluminum windows" in descs
    assert any("Window W-01" in d for d in descs)


def test_window_dedupe_never_touches_door_rows() -> None:
    """Cross-pollination safety: window dedupe must leave doors alone."""
    items = [
        _non_window_door("101"),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=12.0, unit="EA", confidence=0.85,
        ),
        _synthesised("W-01"),
        _llm_aggregate("Aluminum windows", 8),
    ]
    out = dedupe_windows_against_synthesis(items)
    descs = {it.description for it in out}
    # Window aggregate dropped, both door rows survive.
    assert "Aluminum windows" not in descs
    assert "Hollow metal doors" in descs
    assert any("Door 101" in d for d in descs)
