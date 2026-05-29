"""QA pass — Subsystem 4: Takeoff synthesis + dedupe (2026-05-28).

Spot-checks the synthesis → dedupe pipeline that turns deterministic
schedule records into priced-ready :class:`TakeoffItem` rows. Door
synthesis is the canonical reference (Phase T2 origin); the same shape
is reused across all 11 typed schedule extractors.
"""

from __future__ import annotations

import re

import pytest

from core.extraction.dedupe import (
    dedupe_against_synthesis,
    extract_mark_from_synthesized,
)
from core.extraction.door_dedupe import dedupe_doors_against_synthesis
from core.extraction.takeoff_synthesis import (
    DERIVATION_FLOOR_CONFIDENCE,
    DERIVATION_HAIRCUT_MULTIPLIER,
    SYNTHESIS_SOURCE_TAG,
    inherit_with_haircut,
    synthesize_door_takeoff_items,
)
from core.schemas import DoorRecord, DoorScheduleResult, TakeoffItem


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _door(**kw) -> DoorRecord:
    base = {"mark": "101", "type": "HM", "width_in": 36.0, "height_in": 84.0}
    base.update(kw)
    return DoorRecord(**base)


def _schedule(*doors: DoorRecord) -> DoorScheduleResult:
    return DoorScheduleResult(pages=[1], doors=list(doors), confidence=0.85)


def _llm_door_takeoff(description: str, csi_division: str = "08",
                        csi_section: str | None = None) -> TakeoffItem:
    """Synthesise an LLM-style takeoff (no synthesis source-tag in notes)."""
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=1.0,
        unit="EA",
        confidence=0.7,
        notes=None,
    )


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_qa_pos_synthesize_doors_emits_one_takeoff_per_record() -> None:
    schedule = _schedule(
        _door(mark="101A", type="HM", width_in=36.0, height_in=84.0),
        _door(mark="102",  type="WD", width_in=36.0, height_in=84.0),
        _door(mark="103",  type="WD", width_in=36.0, height_in=84.0),
    )
    items = synthesize_door_takeoff_items(schedule, sheet_id="A-601")
    assert len(items) == 3
    assert all(it.unit == "EA" and it.quantity == 1.0 for it in items)
    # Notes must start with the canonical synthesis tag — the dedupe
    # passes downstream rely on this prefix.
    assert all((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}") for it in items)
    # Source-sheet stamp survives end-to-end.
    assert all("A-601" in it.source_sheet_ids for it in items)


def test_qa_pos_synthesize_door_with_full_fields_high_confidence() -> None:
    """Mark + type populated → confidence at 0.92 floor (auto-approve band)."""
    schedule = _schedule(_door(mark="101", type="HM"))
    items = synthesize_door_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].confidence == 0.92


def test_qa_pos_dedupe_drops_legacy_aggregate_when_synth_present() -> None:
    """Legacy ``Hollow metal doors`` aggregate is dropped when a synth row exists."""
    synth = synthesize_door_takeoff_items(_schedule(_door(mark="101", type="HM")))
    legacy = _llm_door_takeoff("Hollow metal doors", csi_division="08", csi_section="08 11 13")
    project = synth + [legacy]
    out = dedupe_doors_against_synthesis(project)
    descs = [it.description for it in out]
    # Synth row preserved.
    assert any("Door 101" in d for d in descs)
    # Legacy aggregate dropped.
    assert not any("Hollow metal doors" in d for d in descs)


# ---------------------------------------------------------------------------
# Negative
# ---------------------------------------------------------------------------


def test_qa_neg_synthesize_doors_handles_none_schedule() -> None:
    """``None`` schedule → empty list, no exception."""
    assert synthesize_door_takeoff_items(None) == []
    # And a schedule with no records.
    assert synthesize_door_takeoff_items(_schedule()) == []


def test_qa_neg_dedupe_no_op_when_no_synth_present() -> None:
    """Safety rule: never drop aggregates when no replacement synth row exists."""
    legacy = _llm_door_takeoff("Hollow metal doors", csi_division="08", csi_section="08 11 13")
    other = _llm_door_takeoff("Generic non-door item", csi_division="03", csi_section="03 30 00")
    out = dedupe_doors_against_synthesis([legacy, other])
    # Both rows preserved — no synthesis row, nothing to retire against.
    assert len(out) == 2


def test_qa_neg_dedupe_does_not_touch_other_families() -> None:
    """Window rows / non-Division-08 rows pass through untouched even with door synth present."""
    synth = synthesize_door_takeoff_items(_schedule(_door(mark="101", type="HM")))
    win_row = _llm_door_takeoff("Aluminum windows", csi_division="08", csi_section="08 51 13")
    non_div8 = _llm_door_takeoff("Concrete slabs", csi_division="03", csi_section="03 30 00")
    project = synth + [win_row, non_div8]
    out = dedupe_doors_against_synthesis(project)
    descs = [it.description for it in out]
    # The non-Division-08 row is preserved (out of family).
    assert "Concrete slabs" in descs
    # The window row IS in Division 08 — but is not a legacy aggregate
    # and the synthesised marks ({"101"}) don't appear in its description,
    # so it should also pass through untouched.
    assert "Aluminum windows" in descs


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_qa_edge_inherit_with_haircut_floor_pinned() -> None:
    """A ridiculously low source confidence floors at ``DERIVATION_FLOOR_CONFIDENCE``."""
    assert inherit_with_haircut(0.10) == DERIVATION_FLOOR_CONFIDENCE
    # Sanity: a high source confidence applies the multiplier.
    assert inherit_with_haircut(1.0) == DERIVATION_HAIRCUT_MULTIPLIER


def test_qa_edge_inherit_with_haircut_clamps_out_of_range() -> None:
    """Out-of-band inputs are clamped to [0, 1] before the multiplier."""
    # Above 1.0 clamps to 1.0 → DERIVATION_HAIRCUT_MULTIPLIER.
    assert inherit_with_haircut(1.5) == DERIVATION_HAIRCUT_MULTIPLIER
    # Below 0 clamps to 0 → floor.
    assert inherit_with_haircut(-0.2) == DERIVATION_FLOOR_CONFIDENCE


def test_qa_edge_extract_mark_from_synth_returns_none_for_non_synth() -> None:
    """Helper is a no-op on rows that don't carry the synthesis prefix."""
    item = _llm_door_takeoff("Some other description")
    mark = extract_mark_from_synthesized(item, source_tag=SYNTHESIS_SOURCE_TAG)
    assert mark is None


def test_qa_edge_synthesize_doors_unmarked_yields_unknown_mark() -> None:
    """Unmarked doors don't break — description shows ``Door (unmarked)``."""
    schedule = _schedule(_door(mark="", type="HM"))
    items = synthesize_door_takeoff_items(schedule)
    assert len(items) == 1
    assert "(unmarked)" in items[0].description


def test_qa_edge_dedupe_per_mark_drops_llm_when_synth_mark_present() -> None:
    """An LLM row whose description references a synthesised mark is dropped."""
    synth = synthesize_door_takeoff_items(_schedule(_door(mark="101A", type="HM")))
    # LLM row whose description mentions "101A" — must be dropped.
    llm = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Door 101A — extra description from LLM",
        quantity=1.0,
        unit="EA",
        confidence=0.7,
    )
    out = dedupe_doors_against_synthesis(synth + [llm])
    descs = [it.description for it in out]
    # Synth row preserved (it also contains "101A"), LLM row dropped.
    synth_count = sum(1 for d in descs if "Door 101A" in d)
    assert synth_count == 1


def test_qa_edge_dedupe_against_synthesis_short_mark_not_promiscuous() -> None:
    """Marks shorter than 2 chars don't trigger description match (avoids false positives)."""
    # Build a synth row with a 1-char mark and a non-matching LLM row that
    # incidentally contains that single character.
    short_synth = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Door 1 — Hollow Metal Door 3'-0\" x 7'-0\"",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={SYNTHESIS_SOURCE_TAG}; mark=1; type=HM",
    )
    other = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Hollow metal door, 1 hour fire rating",  # contains lone "1"
        quantity=1.0,
        unit="EA",
        confidence=0.7,
    )
    out = dedupe_doors_against_synthesis([short_synth, other])
    # Both rows preserved — the 1-char mark is below the 2-char min.
    assert len(out) == 2


# ---------------------------------------------------------------------------
# Positive — explicit CSI mapping coverage (brief: 12 DoorRecords → 12 items)
# ---------------------------------------------------------------------------


def test_qa_pos_twelve_doors_csi_mapping_correct() -> None:
    """12-door fixture exercises every CSI mapping branch.

    Brief calls out: "12 DoorRecords → 12 TakeoffItems with correct
    CSI mapping". One row per material so we lock the keyword
    heuristic against drift.
    """
    schedule = _schedule(
        _door(mark="101", type="HM"),               # 08 11 13
        _door(mark="102", type="HM"),               # 08 11 13
        _door(mark="103", type="WD"),               # 08 14 13
        _door(mark="104", type="WD"),               # 08 14 13
        _door(mark="105", type="SCWD"),             # 08 14 13 (wood family)
        _door(mark="106", type="ALUM"),             # 08 11 16
        _door(mark="107", type="STOREFRONT"),       # 08 11 16 (alum family)
        _door(mark="108", type="GLASS"),            # 08 80 00
        _door(mark="109", type="GLAZED"),           # 08 80 00
        _door(mark="110", type="HOLLOW METAL"),     # 08 11 13
        # An unknown type must still land in 08 10 00 (generic door) —
        # the heuristic never drops a row.
        _door(mark="111", type="MYSTERY"),          # 08 10 00
        # No type but the frame field carries the family signal.
        _door(mark="112", type=None, frame="HM"),   # 08 11 13
    )
    items = synthesize_door_takeoff_items(schedule, sheet_id="A-601")
    assert len(items) == 12

    by_mark = {it.notes.split("mark=", 1)[1].split(";", 1)[0]: it for it in items}
    expected = {
        "101": "08 11 13", "102": "08 11 13", "110": "08 11 13", "112": "08 11 13",
        "103": "08 14 13", "104": "08 14 13", "105": "08 14 13",
        "106": "08 11 16", "107": "08 11 16",
        "108": "08 80 00", "109": "08 80 00",
        "111": "08 10 00",
    }
    for mark, section in expected.items():
        assert by_mark[mark].csi_section == section, (
            f"door {mark}: expected {section}, got {by_mark[mark].csi_section}"
        )
    # Every row is unit=EA and quantity=1.
    assert all(it.unit == "EA" and it.quantity == 1.0 for it in items)
    # Division is always 08 for the door family.
    assert all(it.csi_division == "08" for it in items)


def test_qa_pos_finish_backfill_with_room_and_door_opening_deduction() -> None:
    """Full backfill chain: finish synth → room area → wall SF with opening deduction.

    Constructs a single room with a known area + perimeter + ceiling
    height, plus one door that opens INTO that room. The wall back-fill
    must:

    1. Compute raw wall SF = perimeter * height * share
    2. Deduct the door opening area (width * height / 144)
    3. Stamp the deduction count and SF on the row's notes
    """
    from core.extraction.takeoff_backfill import backfill_finish_quantities
    from core.extraction.takeoff_synthesis import (
        SYNTHESIS_SOURCE_TAG_FINISH,
    )
    from core.schemas import (
        DoorRecord,
        DoorScheduleResult,
        RoomRecord,
        RoomScheduleResult,
    )

    # Single room: 10' x 10' = 100 SF, perimeter 40', ceiling 9'.
    # Raw wall_ALL = 40 * 9 = 360 SF.
    room = RoomRecord(
        room_number="101",
        room_name="OFFICE",
        area_sf=100.0,
        perimeter_lf=40.0,
        ceiling_height_ft=9.0,
    )
    room_schedule = RoomScheduleResult(pages=[1], rooms=[room], confidence=0.9)

    # One 3'-0" x 7'-0" = 21 SF door opening into room 101.
    door = DoorRecord(
        mark="101",
        type="HM",
        width_in=36.0,
        height_in=84.0,
        room_number="101",
        source_page=1,
    )
    door_schedule = DoorScheduleResult(pages=[1], doors=[door], confidence=0.9)

    # Synthesised wall_ALL finish row — quantity=0 by construction; the
    # back-fill is what fills it. Notes carry the canonical room +
    # surface tags the back-fill greps for.
    wall_synth = TakeoffItem(
        csi_division="09",
        csi_section="09 91 23",
        description="Paint — Office walls",
        quantity=0.0,
        unit="SF",
        confidence=0.80,
        notes=(
            f"source={SYNTHESIS_SOURCE_TAG_FINISH}; "
            f"room=101; surface=wall_ALL; finish_code=P-1"
        ),
    )
    floor_synth = TakeoffItem(
        csi_division="09",
        csi_section="09 65 19",
        description="VCT — Office floor",
        quantity=0.0,
        unit="SF",
        confidence=0.80,
        notes=(
            f"source={SYNTHESIS_SOURCE_TAG_FINISH}; "
            f"room=101; surface=floor; finish_code=VCT-1"
        ),
    )

    out = backfill_finish_quantities(
        [wall_synth, floor_synth],
        room_schedule,
        door_schedule=door_schedule,
    )
    by_surface = {("wall_ALL" if "wall_ALL" in it.notes else "floor"): it for it in out}

    # Floor: full 100 SF.
    assert by_surface["floor"].quantity == 100.0
    # Wall: 360 - 21 = 339 SF (door deducted).
    assert by_surface["wall_ALL"].quantity == 339.0
    # Notes audit trail surfaces the deduction.
    wall_notes = by_surface["wall_ALL"].notes or ""
    assert "openings_deducted=1" in wall_notes
    assert "opening_sf=21.0" in wall_notes
    assert "wall_ALL_deduction=21.0" in wall_notes


# ---------------------------------------------------------------------------
# Edge — unit default and zero-quantity behaviour
# ---------------------------------------------------------------------------


def test_qa_edge_takeoff_synth_unit_default_is_ea() -> None:
    """Door synthesis always emits ``unit="EA"`` regardless of source fields.

    The brief flagged "Record with missing unit_of_measure → defensive
    default". For the door synthesis path the unit is constant ``EA``
    by construction — the schema doesn't carry a per-record unit at
    the synthesis layer. Pin that contract.
    """
    schedule = _schedule(_door(mark="101", type="HM"))
    items = synthesize_door_takeoff_items(schedule)
    assert items[0].unit == "EA"


def test_qa_edge_coerce_takeoff_missing_unit_defaults_to_ea() -> None:
    """LLM-side ``_coerce_takeoff`` defaults a missing ``unit`` to ``EA``.

    Mirror coverage of the synthesis-side default at the LLM ingestion
    boundary. Together these two tests pin "no row ever lands without
    a unit" across both pathways.
    """
    from core.extractors import _coerce_takeoff

    item = _coerce_takeoff(
        {"description": "Some takeoff", "quantity": 4, "csi_division": "08"},
        "S-001",
    )
    assert item is not None
    assert item.unit == "EA"


def test_qa_edge_synth_zero_quantity_record_filters_via_mark_guard() -> None:
    """A DoorRecord without a mark IS still synthesised (quantity stays 1 EA).

    Today's synthesis never drops a record on the mark check — an
    unmarked door becomes "Door (unmarked)" with confidence 0.60. The
    brief asked "Zero-quantity record → TakeoffItem with qty=0 or
    skipped (document choice)". We document the current contract:
    synthesis emits qty=1 EA per record, regardless of mark, and
    confidence drops to 0.60 when neither mark nor type are populated.
    """
    schedule = _schedule(_door(mark="", type=None, width_in=None, height_in=None))
    items = synthesize_door_takeoff_items(schedule)
    assert len(items) == 1
    assert items[0].quantity == 1.0
    assert items[0].unit == "EA"
    assert items[0].confidence == 0.60
