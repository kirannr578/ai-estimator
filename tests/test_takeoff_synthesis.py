"""Tests for Phase T2 door-schedule → :class:`TakeoffItem` synthesis.

Mirrors the conventions in :mod:`tests.test_door_schedule_extraction`:
pure unit tests against the Pydantic schema models (no PDF I/O), plus
one integration-smoke test that round-trips a synthesised result through
:func:`core.takeoff.reconcile`.
"""

from __future__ import annotations

import pytest

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


def _make_schedule(*doors: DoorRecord) -> DoorScheduleResult:
    return DoorScheduleResult(
        pages=[0] if doors else [],
        doors=list(doors),
        confidence=0.9 if doors else 0.0,
        raw_table_text="MARK | TYPE | WIDTH | HEIGHT" if doors else "",
    )


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------


def test_happy_path_three_doors_all_complete() -> None:
    """3 records, all with mark + type + dimensions → 3 items @ conf 0.92."""
    schedule = _make_schedule(
        DoorRecord(mark="101",  type="HM",   width_in=36.0, height_in=84.0),
        DoorRecord(mark="102",  type="WD",   width_in=32.0, height_in=80.0),
        DoorRecord(mark="103",  type="ALUM", width_in=72.0, height_in=84.0),
    )
    items = synthesize_door_takeoff_items(schedule, sheet_id="A0.1")

    assert len(items) == 3
    assert all(isinstance(it, TakeoffItem) for it in items)
    assert all(it.confidence == pytest.approx(0.92) for it in items)
    assert all(it.quantity == 1.0 for it in items)
    assert all(it.unit == "EA" for it in items)
    assert all(it.csi_division == "08" for it in items)
    assert all(it.source_sheet_ids == ["A0.1"] for it in items)
    assert all((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG}")
               for it in items)
    # CSI sections match the three families exercised in the fixture.
    assert {it.csi_section for it in items} == {"08 11 13", "08 14 13", "08 11 16"}
    # Each mark appears in its row's description.
    joined = " ".join(it.description for it in items)
    for mark in ("101", "102", "103"):
        assert mark in joined


# ---------------------------------------------------------------------------
# 2. CSI mapping (parametrised over the five-family heuristic)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_str, expected_section",
    [
        # Hollow metal — 08 11 13
        ("HM",                "08 11 13"),
        ("Hollow Metal",      "08 11 13"),
        # Wood — 08 14 13
        ("WD",                "08 14 13"),
        ("SCWD",              "08 14 13"),
        ("Wood",              "08 14 13"),
        # Aluminum frame / storefront — 08 11 16
        ("ALUM",              "08 11 16"),
        ("Aluminum",          "08 11 16"),
        ("Storefront",        "08 11 16"),
        # Glass / glazed — 08 80 00
        ("Glass",             "08 80 00"),
        ("Glazed",            "08 80 00"),
        # Unknown / unmatched → generic Doors and Frames (08 10 00)
        ("Mystery",           "08 10 00"),
    ],
)
def test_csi_mapping_by_type(type_str: str, expected_section: str) -> None:
    schedule = _make_schedule(DoorRecord(mark="X1", type=type_str))
    items = synthesize_door_takeoff_items(schedule)
    assert items[0].csi_section == expected_section
    assert items[0].csi_division == "08"


def test_csi_mapping_falls_back_to_generic_when_type_missing() -> None:
    """``type`` and ``material`` both empty → 08 10 00 generic Doors/Frames."""
    schedule = _make_schedule(DoorRecord(mark="X1"))
    items = synthesize_door_takeoff_items(schedule)
    assert items[0].csi_section == "08 10 00"


def test_csi_mapping_uses_material_when_type_blank() -> None:
    """A schedule that only records material still routes to the right family."""
    schedule = _make_schedule(
        DoorRecord(mark="X1", type=None, material="HOLLOW METAL")
    )
    items = synthesize_door_takeoff_items(schedule)
    assert items[0].csi_section == "08 11 13"


# ---------------------------------------------------------------------------
# 3. Confidence rubric
# ---------------------------------------------------------------------------


def test_confidence_mark_and_type_present_is_0_92() -> None:
    schedule = _make_schedule(DoorRecord(mark="101", type="HM"))
    assert synthesize_door_takeoff_items(schedule)[0].confidence == pytest.approx(0.92)


def test_confidence_mark_only_is_0_80() -> None:
    schedule = _make_schedule(DoorRecord(mark="101"))
    assert synthesize_door_takeoff_items(schedule)[0].confidence == pytest.approx(0.80)


def test_confidence_type_only_is_0_80() -> None:
    """``mark`` is required-str on the schema; empty-string counts as missing."""
    schedule = _make_schedule(DoorRecord(mark="", type="HM"))
    assert synthesize_door_takeoff_items(schedule)[0].confidence == pytest.approx(0.80)


def test_confidence_neither_mark_nor_type_is_0_60() -> None:
    schedule = _make_schedule(DoorRecord(mark=""))
    assert synthesize_door_takeoff_items(schedule)[0].confidence == pytest.approx(0.60)


# ---------------------------------------------------------------------------
# 4. Empty schedule edge-cases
# ---------------------------------------------------------------------------


def test_empty_schedule_returns_empty_list() -> None:
    assert synthesize_door_takeoff_items(_make_schedule()) == []


def test_none_schedule_returns_empty_list() -> None:
    assert synthesize_door_takeoff_items(None) == []


# ---------------------------------------------------------------------------
# 5. Dimension rendering
# ---------------------------------------------------------------------------


def test_dimensions_rendered_as_feet_inches() -> None:
    schedule = _make_schedule(
        DoorRecord(mark="101", type="HM", width_in=36.0, height_in=84.0)
    )
    desc = synthesize_door_takeoff_items(schedule)[0].description
    assert "3'-0\"" in desc
    assert "7'-0\"" in desc


def test_missing_dimensions_does_not_crash_and_omits_size() -> None:
    """``DoorRecord`` with no width/height → readable description, no error."""
    schedule = _make_schedule(DoorRecord(mark="101", type="HM"))
    items = synthesize_door_takeoff_items(schedule)
    desc = items[0].description
    assert desc.startswith("Door 101")
    assert "HM" in desc
    assert "x" not in desc  # no size segment when dimensions missing
    # Confidence still 0.92 — dimensions are not part of the rubric.
    assert items[0].confidence == pytest.approx(0.92)


def test_partial_dimensions_only_emits_size_when_both_present() -> None:
    schedule = _make_schedule(
        DoorRecord(mark="101", type="HM", width_in=36.0, height_in=None)
    )
    desc = synthesize_door_takeoff_items(schedule)[0].description
    # Width alone is intentionally not shown; description still readable.
    assert "3'-0\"" not in desc
    assert "HM" in desc


def test_fractional_inches_render_cleanly() -> None:
    """``36.5`` inches → ``3'-0.5"`` (no infinite-precision float noise)."""
    schedule = _make_schedule(
        DoorRecord(mark="101", type="HM", width_in=36.5, height_in=84.0)
    )
    desc = synthesize_door_takeoff_items(schedule)[0].description
    assert "3'-0.5\"" in desc


# ---------------------------------------------------------------------------
# 6. Integration with reconcile()
# ---------------------------------------------------------------------------


def test_integration_reconcile_includes_synthesised_door_items() -> None:
    """A SheetExtraction with ``prepass.door_schedule`` populated must yield
    synthesised TakeoffItems on the returned ProjectModel.takeoffs list."""
    schedule = DoorScheduleResult(
        pages=[0],
        doors=[
            DoorRecord(mark="101", type="HM", width_in=36.0, height_in=84.0),
            DoorRecord(mark="102", type="WD", width_in=32.0, height_in=80.0),
        ],
        confidence=0.9,
    )
    extraction = SheetExtraction(
        sheet_id="A0.1",
        prepass=DrawingPrepassResult(door_schedule=schedule),
    )
    project = reconcile([extraction])

    synthesized = [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG}")
    ]
    assert len(synthesized) == 2
    for t in synthesized:
        assert t.source_sheet_ids == ["A0.1"]
        assert t.quantity == 1.0
        assert t.unit == "EA"
        assert t.confidence == pytest.approx(0.92)
    descs = " ".join(t.description for t in synthesized)
    assert "101" in descs
    assert "102" in descs


def test_integration_reconcile_no_door_schedule_yields_no_synthesised_items() -> None:
    """An extraction without ``prepass.door_schedule`` produces no T2 rows."""
    extraction = SheetExtraction(
        sheet_id="A0.1",
        prepass=DrawingPrepassResult(door_schedule=None),
    )
    project = reconcile([extraction])
    assert not [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG}")
    ]


def test_integration_reconcile_preserves_existing_llm_takeoffs() -> None:
    """Synthesised rows are *additive* — they never replace LLM takeoffs."""
    llm_row = TakeoffItem(
        csi_division="08",
        csi_section="08 11 13",
        description="Hollow metal doors (LLM-counted)",
        quantity=42.0,
        unit="EA",
        confidence=0.75,
        notes="source=llm",
    )
    schedule = DoorScheduleResult(
        pages=[0],
        doors=[DoorRecord(mark="101", type="HM", width_in=36.0, height_in=84.0)],
        confidence=0.9,
    )
    extraction = SheetExtraction(
        sheet_id="A0.1",
        prepass=DrawingPrepassResult(door_schedule=schedule),
        raw_takeoffs=[llm_row],
    )
    project = reconcile([extraction])

    # The LLM-style row survives (qty=42 EA) AND the synthesised row appears.
    llm_survivors = [
        t for t in project.takeoffs
        if t.description == "Hollow metal doors (LLM-counted)"
    ]
    synthesised = [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG}")
    ]
    assert len(llm_survivors) == 1
    assert llm_survivors[0].quantity == pytest.approx(42.0)
    assert len(synthesised) == 1
