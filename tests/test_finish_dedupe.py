"""Tests for Phase T4 ``dedupe_finishes_against_synthesis``.

Mirror of :mod:`tests.test_window_dedupe` for the finish family. Pure
unit tests against the Pydantic schema (no PDF I/O), plus
integration-smoke tests that round-trip a synthesised result through
:func:`core.takeoff.reconcile`. Critically also verifies cross-
pollination safety: finish dedupe must NEVER drop door or window
rows.
"""

from __future__ import annotations

import pytest

from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.finish_dedupe import dedupe_finishes_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG,
    SYNTHESIS_SOURCE_TAG_FINISH,
    SYNTHESIS_SOURCE_TAG_WINDOW,
    synthesize_finish_takeoff_items,
)
from core.extraction.window_dedupe import dedupe_windows_against_synthesis
from core.schemas import (
    DrawingPrepassResult,
    FinishRecord,
    FinishScheduleResult,
    SheetExtraction,
    TakeoffItem,
)
from core.takeoff import reconcile


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _synthesised_floor(room: str = "101", code: str = "VCT-1",
                          section: str = "09 65 19",
                          division: str = "09") -> TakeoffItem:
    """Build a TakeoffItem mirroring what the T4 synthesiser emits for a floor row."""
    return TakeoffItem(
        csi_division=division,
        csi_section=section,
        description=f"Floor {code} \u2013 Room {room} Office",
        quantity=0.0,
        unit="SF",
        confidence=0.92,
        notes=(f"source={SYNTHESIS_SOURCE_TAG_FINISH}; room={room}; "
               f"room_name=Office; surface=floor; code={code}"),
    )


def _synthesised_wall(room: str = "101", code: str = "PT-1") -> TakeoffItem:
    return TakeoffItem(
        csi_division="09",
        csi_section="09 91 23",
        description=f"Wall {code} \u2013 Room {room} Office",
        quantity=0.0,
        unit="SF",
        confidence=0.92,
        notes=(f"source={SYNTHESIS_SOURCE_TAG_FINISH}; room={room}; "
               f"room_name=Office; surface=wall_ALL; code={code}"),
    )


def _llm_finish_aggregate(desc: str, qty: float = 500.0,
                            unit: str = "SF",
                            section: str | None = None) -> TakeoffItem:
    return TakeoffItem(
        csi_division="09",
        csi_section=section,
        description=desc,
        quantity=qty,
        unit=unit,
        confidence=0.65,
    )


def _non_finish_door(mark: str = "101") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description=f"Door {mark} \u2014 HM 3'-0\" x 7'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG}; mark={mark}; type=HM",
    )


def _non_finish_window(mark: str = "W-01") -> TakeoffItem:
    return TakeoffItem(
        csi_division="08",
        csi_section="08 51 13",
        description=f"Window {mark} \u2014 ALUM 3'-0\" x 5'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG_WINDOW}; mark={mark}; type=ALUM",
    )


def _non_finish_struct() -> TakeoffItem:
    return TakeoffItem(
        csi_division="05",
        csi_section="05 12 00",
        description="Structural steel framing",
        quantity=42.0,
        unit="TON",
        confidence=0.7,
    )


# ---------------------------------------------------------------------------
# 1. Empty / trivial input
# ---------------------------------------------------------------------------


def test_empty_input_returns_empty() -> None:
    assert dedupe_finishes_against_synthesis([]) == []


# ---------------------------------------------------------------------------
# 2. Safety rule: no synthesised finish → input unchanged
# ---------------------------------------------------------------------------


def test_no_synthesised_finishes_returns_input_unchanged() -> None:
    """Without a deterministic fallback we must keep the legacy aggregates."""
    items = [
        _llm_finish_aggregate("Carpet flooring", 250.0),
        _llm_finish_aggregate("Interior wall painting (two coats)", 1200.0),
        _non_finish_struct(),
    ]
    out = dedupe_finishes_against_synthesis(items)
    assert out == items
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 3. Legacy aggregate dedupe (the headline T4 feature)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "desc",
    [
        "Carpet flooring",
        "Carpet flooring 250 SF",
        "Tile flooring",
        "VCT flooring",
        "Vinyl plank flooring (LVT)",
        "Hardwood flooring",
        "Wood flooring",
        "Polished concrete floors",
        "Sealed concrete floor",
        "Resilient base, 4\"",
        "Interior wall painting (two coats)",
        "Acoustic ceiling tile",
        "Wallcovering",
        "Wall covering",
        "FRP panels",
        "Gypsum board ceiling",
        "Gyp bd ceiling",
        "Other flooring (terrazzo)",
        "Paint, interior walls",
    ],
)
def test_legacy_aggregate_dropped_when_any_synthesised_finish_exists(desc: str) -> None:
    items = [
        _synthesised_floor("101", "VCT-1"),
        _llm_finish_aggregate(desc),
    ]
    out = dedupe_finishes_against_synthesis(items)
    assert len(out) == 1
    assert out[0].description.startswith("Floor VCT-1")


def test_legacy_aggregate_preserved_when_no_synthesised_finishes() -> None:
    """Safety rule -- never strip aggregates when nothing else covers them."""
    items = [
        _llm_finish_aggregate("Carpet flooring", 500.0),
        _non_finish_struct(),
    ]
    assert dedupe_finishes_against_synthesis(items) == items


# ---------------------------------------------------------------------------
# 4. Cross-pollination safety: door + window rows never touched
# ---------------------------------------------------------------------------


def test_door_rows_untouched_by_finish_dedupe() -> None:
    """Synthesised + LLM door rows survive the finish dedupe pass intact."""
    items = [
        _synthesised_floor("101"),
        _non_finish_door("101"),
        TakeoffItem(  # LLM door (Division 08, NOT a finish section)
            csi_division="08", csi_section="08 11 13",
            description="Door 999 (LLM)", quantity=1.0,
            unit="EA", confidence=0.75,
        ),
        TakeoffItem(  # door aggregate -- must survive a FINISH dedupe pass
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=12.0,
            unit="EA", confidence=0.85,
        ),
    ]
    out = dedupe_finishes_against_synthesis(items)
    descs = {it.description for it in out}
    # Door rows all survived.
    assert "Hollow metal doors" in descs
    assert any("Door 101" in d for d in descs)
    assert any("Door 999" in d for d in descs)
    # Finish synth survived.
    assert any("Floor VCT-1" in d for d in descs)


def test_window_rows_untouched_by_finish_dedupe() -> None:
    """Synthesised + LLM window rows survive finish dedupe intact."""
    items = [
        _synthesised_floor("101"),
        _non_finish_window("W-01"),
        TakeoffItem(  # LLM window aggregate
            csi_division="08", csi_section="08 50 00",
            description="Aluminum windows", quantity=8.0,
            unit="EA", confidence=0.85,
        ),
    ]
    out = dedupe_finishes_against_synthesis(items)
    descs = {it.description for it in out}
    assert "Aluminum windows" in descs
    assert any("Window W-01" in d for d in descs)
    assert any("Floor VCT-1" in d for d in descs)


def test_door_dedupe_never_touches_finish_rows() -> None:
    """Door dedupe must leave finish rows alone."""
    items = [
        _non_finish_door("101"),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal doors", quantity=12.0,
            unit="EA", confidence=0.85,
        ),
        _synthesised_floor("101"),
        _llm_finish_aggregate("Carpet flooring", 250.0),
    ]
    out = dedupe_doors_against_synthesis(items)
    descs = {it.description for it in out}
    # Door aggregate dropped, both finish rows survive.
    assert "Hollow metal doors" not in descs
    assert "Carpet flooring" in descs
    assert any("Floor VCT-1" in d for d in descs)


def test_window_dedupe_never_touches_finish_rows() -> None:
    """Window dedupe must leave finish rows alone."""
    items = [
        _non_finish_window("W-01"),
        TakeoffItem(
            csi_division="08", csi_section="08 51 13",
            description="Aluminum windows", quantity=8.0,
            unit="EA", confidence=0.85,
        ),
        _synthesised_floor("101"),
        _llm_finish_aggregate("Carpet flooring", 250.0),
    ]
    out = dedupe_windows_against_synthesis(items)
    descs = {it.description for it in out}
    # Window aggregate dropped, both finish rows survive.
    assert "Aluminum windows" not in descs
    assert "Carpet flooring" in descs
    assert any("Floor VCT-1" in d for d in descs)


# ---------------------------------------------------------------------------
# 5. Combinatorial preservation
# ---------------------------------------------------------------------------


def test_combinatorial_preservation_and_drops() -> None:
    items = [
        _synthesised_floor("101", "VCT-1"),
        _synthesised_wall("101", "PT-1"),
        _synthesised_floor("102", "CPT-1", section="09 68 13"),
        _llm_finish_aggregate("Carpet flooring", 250.0),        # drop -- aggregate
        _llm_finish_aggregate("Interior wall painting (two coats)", 1200.0),  # drop
        _llm_finish_aggregate("Acoustic ceiling tile", 800.0),  # drop
        _non_finish_door("101"),                                 # keep
        _non_finish_window("W-01"),                              # keep
        _non_finish_struct(),                                    # keep
    ]
    out = dedupe_finishes_against_synthesis(items)
    descs = [it.description for it in out]
    # Aggregates dropped.
    assert "Carpet flooring" not in descs
    assert "Interior wall painting (two coats)" not in descs
    assert "Acoustic ceiling tile" not in descs
    # Synth finishes preserved.
    assert any("Floor VCT-1" in d for d in descs)
    assert any("Floor CPT-1" in d for d in descs)
    assert any("Wall PT-1" in d for d in descs)
    # Doors + windows + struct preserved.
    assert any("Door 101" in d for d in descs)
    assert any("Window W-01" in d for d in descs)
    assert any("Structural steel" in d for d in descs)


# ---------------------------------------------------------------------------
# 6. Out-of-family rows preserved
# ---------------------------------------------------------------------------


def test_non_finish_divisions_untouched() -> None:
    items = [
        _synthesised_floor("101"),
        _non_finish_struct(),                       # div 05
        TakeoffItem(                                # div 23 — HVAC
            csi_division="23", csi_section="23 00 00",
            description="Rooftop unit", quantity=2.0,
            unit="EA", confidence=0.7,
        ),
        TakeoffItem(                                # div 26 — Electrical
            csi_division="26", csi_section="26 24 16",
            description="Distribution panel",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
        TakeoffItem(                                # div 03 NON-polished concrete
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade",
            quantity=2500.0, unit="SF", confidence=0.6,
        ),
    ]
    out = dedupe_finishes_against_synthesis(items)
    # Everything survives — only the finish synth row is in-family.
    assert len(out) == len(items)


def test_03_35_polished_concrete_in_family() -> None:
    """Cross-division: floor synthesis at 03 35 43 is finish-family."""
    items = [
        TakeoffItem(
            csi_division="03", csi_section="03 35 43",
            description="Floor POL CONC \u2013 Room 101 Mech",
            quantity=0.0, unit="SF", confidence=0.92,
            notes=(f"source={SYNTHESIS_SOURCE_TAG_FINISH}; room=101; "
                   f"surface=floor; code=POL CONC"),
        ),
        _llm_finish_aggregate("Polished concrete floors", 500.0),
    ]
    out = dedupe_finishes_against_synthesis(items)
    descs = [it.description for it in out]
    assert "Polished concrete floors" not in descs


def test_06_64_frp_in_family() -> None:
    """Cross-division: wall synthesis at 06 64 00 (FRP) is finish-family."""
    items = [
        TakeoffItem(
            csi_division="06", csi_section="06 64 00",
            description="Wall FRP-1 \u2013 Room 101 Kitchen",
            quantity=0.0, unit="SF", confidence=0.92,
            notes=(f"source={SYNTHESIS_SOURCE_TAG_FINISH}; room=101; "
                   f"surface=wall_ALL; code=FRP-1"),
        ),
        _llm_finish_aggregate("FRP panels", 400.0),
    ]
    out = dedupe_finishes_against_synthesis(items)
    descs = [it.description for it in out]
    assert "FRP panels" not in descs


# ---------------------------------------------------------------------------
# 7. Ordering preserved
# ---------------------------------------------------------------------------


def test_original_order_preserved() -> None:
    items = [
        _non_finish_struct(),                            # 0 keep
        _synthesised_floor("101"),                       # 1 keep
        _llm_finish_aggregate("Carpet flooring", 250.0),  # 2 drop
        _synthesised_wall("101"),                        # 3 keep
        _llm_finish_aggregate("Acoustic ceiling tile"),  # 4 drop
        _non_finish_door("101"),                         # 5 keep
    ]
    out = dedupe_finishes_against_synthesis(items)
    assert [it.description for it in out] == [
        items[0].description,
        items[1].description,
        items[3].description,
        items[5].description,
    ]


# ---------------------------------------------------------------------------
# 8. Integration smoke tests through reconcile()
# ---------------------------------------------------------------------------


def test_integration_reconcile_dedupes_legacy_finish_aggregate() -> None:
    """End-to-end: reconcile() must apply T4 dedupe to the merged takeoffs."""
    schedule = FinishScheduleResult(
        pages=[0],
        rooms=[
            FinishRecord(
                room_number="101", room_name="Office",
                floor_finish="CPT-1", base_finish="RB-1",
                wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
            ),
            FinishRecord(
                room_number="102", room_name="Lobby",
                floor_finish="CPT-1", base_finish="RB-1",
                wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
            ),
        ],
        confidence=0.9,
    )
    legacy_aggregates = [
        TakeoffItem(
            csi_division="09", csi_section="09 68 13",
            description="Carpet flooring",
            quantity=500.0, unit="SF", confidence=0.75,
        ),
        TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior wall painting (two coats)",
            quantity=1200.0, unit="SF", confidence=0.6,
        ),
    ]
    extraction = SheetExtraction(
        sheet_id="A0.3",
        prepass=DrawingPrepassResult(finish_schedule=schedule),
        raw_takeoffs=legacy_aggregates,
    )
    project = reconcile([extraction])
    descs = [t.description for t in project.takeoffs]
    assert "Carpet flooring" not in descs
    assert "Interior wall painting (two coats)" not in descs
    synth = [t for t in project.takeoffs
             if (t.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")]
    # 2 rooms × 4 surfaces (floor + base + wall ALL + ceiling) = 8.
    assert len(synth) == 8


def test_integration_reconcile_no_synthesised_keeps_legacy_aggregates() -> None:
    """Safety rule round-tripped through reconcile()."""
    legacy = TakeoffItem(
        csi_division="09", csi_section="09 68 13",
        description="Carpet flooring",
        quantity=500.0, unit="SF", confidence=0.75,
    )
    extraction = SheetExtraction(sheet_id="A0.3", raw_takeoffs=[legacy])
    project = reconcile([extraction])
    aggregates = [t for t in project.takeoffs if t.description == "Carpet flooring"]
    assert len(aggregates) == 1


def test_integration_synthesiser_to_dedupe_round_trip() -> None:
    """Compose T4 synthesis + dedupe directly (no reconcile)."""
    schedule = FinishScheduleResult(
        pages=[0],
        rooms=[
            FinishRecord(
                room_number="101", room_name="Office",
                floor_finish="VCT-1", base_finish="RB-1",
                wall_finishes={"ALL": "PT-1"}, ceiling_finish="ACT-1",
            ),
        ],
        confidence=0.9,
    )
    synth = synthesize_finish_takeoff_items(schedule, sheet_id="A0.3")
    llm = [
        TakeoffItem(  # drop -- aggregate
            csi_division="09", csi_section="09 65 19",
            description="VCT flooring", quantity=500.0,
            unit="SF", confidence=0.7,
        ),
        TakeoffItem(  # keep -- unrelated div
            csi_division="22", csi_section="22 40 00",
            description="Plumbing fixtures", quantity=4.0,
            unit="EA", confidence=0.7,
        ),
    ]
    out = dedupe_finishes_against_synthesis(synth + llm)
    descs = [it.description for it in out]
    assert "VCT flooring" not in descs
    assert any("Plumbing fixtures" in d for d in descs)
    # 4 synth items survive: floor + base + wall + ceiling.
    synth_out = [it for it in out
                 if (it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")]
    assert len(synth_out) == 4
