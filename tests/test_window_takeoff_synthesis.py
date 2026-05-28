"""Tests for Phase T2.5 window-schedule → :class:`TakeoffItem` synthesis.

Mirror of :mod:`tests.test_takeoff_synthesis` for the window-schedule
pipeline. Pure unit tests against the Pydantic schema models (no PDF
I/O), plus one integration-smoke test that round-trips a synthesised
result through :func:`core.takeoff.reconcile`.
"""

from __future__ import annotations

import pytest

from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_WINDOW,
    synthesize_window_takeoff_items,
)
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


def _make_schedule(*windows: WindowRecord) -> WindowScheduleResult:
    return WindowScheduleResult(
        pages=[0] if windows else [],
        windows=list(windows),
        confidence=0.9 if windows else 0.0,
        raw_table_text="MARK | TYPE | WIDTH | HEIGHT | GLAZING" if windows else "",
    )


# ---------------------------------------------------------------------------
# 1. Happy path
# ---------------------------------------------------------------------------


def test_happy_path_three_windows_all_complete() -> None:
    """3 records, all with mark + type + dimensions → 3 items @ conf 0.92."""
    schedule = _make_schedule(
        WindowRecord(mark="W1", type="ALUM", width_in=36.0, height_in=60.0),
        WindowRecord(mark="W2", type="VINYL", width_in=32.0, height_in=56.0),
        WindowRecord(mark="W3", type="WOOD", width_in=48.0, height_in=60.0),
    )
    items = synthesize_window_takeoff_items(schedule, sheet_id="A0.2")

    assert len(items) == 3
    assert all(isinstance(it, TakeoffItem) for it in items)
    assert all(it.confidence == pytest.approx(0.92) for it in items)
    assert all(it.quantity == 1.0 for it in items)
    assert all(it.unit == "EA" for it in items)
    assert all(it.csi_division == "08" for it in items)
    assert all(it.source_sheet_ids == ["A0.2"] for it in items)
    assert all((it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
               for it in items)
    # CSI sections match the three families exercised in the fixture.
    assert {it.csi_section for it in items} == {"08 51 13", "08 53 13", "08 52 13"}
    # Each mark appears in its row's description.
    joined = " ".join(it.description for it in items)
    for mark in ("W1", "W2", "W3"):
        assert mark in joined


# ---------------------------------------------------------------------------
# 2. CSI mapping — six families plus generic
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "type_str, expected_section",
    [
        # Aluminum windows — 08 51 13
        ("ALUM",                "08 51 13"),
        ("Aluminum",            "08 51 13"),
        ("Aluminum window",     "08 51 13"),
        # Vinyl windows — 08 53 13
        ("VINYL",               "08 53 13"),
        ("Vinyl-clad",          "08 53 13"),
        # Wood windows — 08 52 13
        ("WOOD",                "08 52 13"),
        ("WD",                  "08 52 13"),
        # Metal-clad wood — 08 52 19
        ("METAL CLAD",          "08 52 19"),
        ("Metal-Clad Wood",     "08 52 19"),
        ("ALCLAD",              "08 52 19"),
        # Steel windows — 08 51 23
        ("STEEL",               "08 51 23"),
        ("Steel window",        "08 51 23"),
        # Unknown / unmatched → 08 50 00 generic Windows
        ("Mystery",             "08 50 00"),
    ],
)
def test_csi_mapping_by_type(type_str: str, expected_section: str) -> None:
    schedule = _make_schedule(WindowRecord(mark="X1", type=type_str))
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == expected_section
    assert items[0].csi_division == "08"


def test_csi_mapping_storefront_default_is_aluminum_entrance() -> None:
    """``STOREFRONT`` with small dimensions → 08 41 13 (entrance/storefront)."""
    schedule = _make_schedule(
        WindowRecord(mark="SF1", type="STOREFRONT",
                     width_in=72.0, height_in=84.0),
    )
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 41 13"


def test_csi_mapping_storefront_upgrades_to_curtain_wall_on_large_dim() -> None:
    """A storefront-tagged record with any dimension > 96 in. → 08 44 13."""
    schedule = _make_schedule(
        WindowRecord(mark="CW1", type="STOREFRONT",
                     width_in=144.0, height_in=84.0),
    )
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 44 13"


def test_csi_mapping_explicit_curtain_wall_wins_even_at_small_dim() -> None:
    """``CURTAIN WALL`` keyword → 08 44 13 regardless of dimensions."""
    schedule = _make_schedule(
        WindowRecord(mark="CW2", type="CURTAIN WALL",
                     width_in=36.0, height_in=60.0),
    )
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 44 13"


def test_csi_mapping_metal_clad_wins_over_bare_wood_or_aluminum() -> None:
    """``METAL CLAD`` must take precedence over the bare ``WOOD`` / ``ALUM`` matchers."""
    schedule = _make_schedule(
        WindowRecord(mark="W4", type="METAL CLAD WOOD", material="WOOD")
    )
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 52 19"


def test_csi_mapping_falls_back_to_generic_when_all_fields_blank() -> None:
    """``type`` + ``frame`` + ``material`` all empty → 08 50 00 generic Windows."""
    schedule = _make_schedule(WindowRecord(mark="X1"))
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 50 00"


def test_csi_mapping_uses_frame_when_type_blank() -> None:
    """A schedule that only records ``frame`` still routes to the right family."""
    schedule = _make_schedule(
        WindowRecord(mark="X1", type=None, frame="VINYL")
    )
    items = synthesize_window_takeoff_items(schedule)
    assert items[0].csi_section == "08 53 13"


# ---------------------------------------------------------------------------
# 3. Confidence rubric
# ---------------------------------------------------------------------------


def test_confidence_mark_and_type_present_is_0_92() -> None:
    schedule = _make_schedule(WindowRecord(mark="W1", type="ALUM"))
    assert synthesize_window_takeoff_items(schedule)[0].confidence == pytest.approx(0.92)


def test_confidence_mark_only_is_0_80() -> None:
    schedule = _make_schedule(WindowRecord(mark="W1"))
    assert synthesize_window_takeoff_items(schedule)[0].confidence == pytest.approx(0.80)


def test_confidence_type_only_is_0_80() -> None:
    """``mark`` is required-str on the schema; empty-string counts as missing."""
    schedule = _make_schedule(WindowRecord(mark="", type="ALUM"))
    assert synthesize_window_takeoff_items(schedule)[0].confidence == pytest.approx(0.80)


def test_confidence_neither_mark_nor_type_is_0_60() -> None:
    schedule = _make_schedule(WindowRecord(mark=""))
    assert synthesize_window_takeoff_items(schedule)[0].confidence == pytest.approx(0.60)


# ---------------------------------------------------------------------------
# 4. Empty schedule edge-cases
# ---------------------------------------------------------------------------


def test_empty_schedule_returns_empty_list() -> None:
    assert synthesize_window_takeoff_items(_make_schedule()) == []


def test_none_schedule_returns_empty_list() -> None:
    assert synthesize_window_takeoff_items(None) == []


# ---------------------------------------------------------------------------
# 5. Dimension rendering
# ---------------------------------------------------------------------------


def test_dimensions_rendered_as_feet_inches() -> None:
    schedule = _make_schedule(
        WindowRecord(mark="W1", type="ALUM", width_in=36.0, height_in=60.0)
    )
    desc = synthesize_window_takeoff_items(schedule)[0].description
    assert "3'-0\"" in desc
    assert "5'-0\"" in desc


def test_missing_dimensions_does_not_crash_and_omits_size() -> None:
    """``WindowRecord`` with no width/height → readable description, no error."""
    schedule = _make_schedule(WindowRecord(mark="W1", type="ALUM"))
    items = synthesize_window_takeoff_items(schedule)
    desc = items[0].description
    assert desc.startswith("Window W1")
    assert "ALUM" in desc
    assert "x" not in desc.lower()  # no size segment when dimensions missing
    # Confidence still 0.92 — dimensions are not part of the rubric.
    assert items[0].confidence == pytest.approx(0.92)


def test_partial_dimensions_only_emits_size_when_both_present() -> None:
    schedule = _make_schedule(
        WindowRecord(mark="W1", type="ALUM", width_in=36.0, height_in=None)
    )
    desc = synthesize_window_takeoff_items(schedule)[0].description
    assert "3'-0\"" not in desc
    assert "ALUM" in desc


# ---------------------------------------------------------------------------
# 6. Source-tagging
# ---------------------------------------------------------------------------


def test_notes_carry_window_specific_source_tag() -> None:
    """Notes must start with ``source=window_schedule_prepass`` (not door)."""
    schedule = _make_schedule(
        WindowRecord(mark="W1", type="ALUM", width_in=36.0, height_in=60.0,
                     glazing="INSUL", operation="FIXED",
                     u_factor=0.32, shgc=0.28, sill_height_in=30.0),
    )
    item = synthesize_window_takeoff_items(schedule)[0]
    notes = item.notes or ""
    assert notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
    # Window-specific keys appear in the notes for downstream audit.
    assert "mark=W1" in notes
    assert "type=ALUM" in notes
    assert "glazing=INSUL" in notes
    assert "operation=FIXED" in notes
    assert "u_factor=0.32" in notes
    assert "shgc=0.28" in notes
    assert "sill_height_in=30" in notes


def test_unmarked_window_description_renders_cleanly() -> None:
    schedule = _make_schedule(
        WindowRecord(mark="", type="ALUM", width_in=36.0, height_in=60.0)
    )
    desc = synthesize_window_takeoff_items(schedule)[0].description
    assert desc.startswith("Window (unmarked)")
    assert "ALUM" in desc


# ---------------------------------------------------------------------------
# 7. Integration with reconcile()
# ---------------------------------------------------------------------------


def test_integration_reconcile_includes_synthesised_window_items() -> None:
    """A SheetExtraction with ``prepass.window_schedule`` populated must yield
    synthesised TakeoffItems on the returned ProjectModel.takeoffs list."""
    schedule = WindowScheduleResult(
        pages=[0],
        windows=[
            WindowRecord(mark="W1", type="ALUM", width_in=36.0, height_in=60.0),
            WindowRecord(mark="W2", type="VINYL", width_in=32.0, height_in=56.0),
        ],
        confidence=0.9,
    )
    extraction = SheetExtraction(
        sheet_id="A0.2",
        prepass=DrawingPrepassResult(window_schedule=schedule),
    )
    project = reconcile([extraction])

    synthesized = [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
    ]
    assert len(synthesized) == 2
    for t in synthesized:
        assert t.source_sheet_ids == ["A0.2"]
        assert t.quantity == 1.0
        assert t.unit == "EA"
        assert t.confidence == pytest.approx(0.92)
    descs = " ".join(t.description for t in synthesized)
    assert "W1" in descs
    assert "W2" in descs


def test_integration_reconcile_no_window_schedule_yields_no_synthesised_items() -> None:
    """An extraction without ``prepass.window_schedule`` produces no T2.5 rows."""
    extraction = SheetExtraction(
        sheet_id="A0.2",
        prepass=DrawingPrepassResult(window_schedule=None),
    )
    project = reconcile([extraction])
    assert not [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
    ]


def test_integration_reconcile_preserves_existing_llm_window_descriptions() -> None:
    """Synthesised window rows live alongside un-aggregated LLM rows.

    The T2.5 dedupe pass retires *legacy aggregates* (matching the
    ``Aluminum windows`` / ``Windows`` pattern) but a free-form LLM row
    with no recognisable aggregate shape (e.g. ``"Window, custom oak veneer, single"``)
    must survive untouched.
    """
    llm_row = TakeoffItem(
        csi_division="08",
        csi_section="08 51 13",
        description="Window, custom oak veneer, single",
        quantity=1.0,
        unit="EA",
        confidence=0.70,
        notes="source=llm",
    )
    schedule = WindowScheduleResult(
        pages=[0],
        windows=[WindowRecord(mark="W1", type="ALUM",
                              width_in=36.0, height_in=60.0)],
        confidence=0.9,
    )
    extraction = SheetExtraction(
        sheet_id="A0.2",
        prepass=DrawingPrepassResult(window_schedule=schedule),
        raw_takeoffs=[llm_row],
    )
    project = reconcile([extraction])

    llm_survivors = [
        t for t in project.takeoffs
        if t.description == "Window, custom oak veneer, single"
    ]
    synthesised = [
        t for t in project.takeoffs
        if t.notes and t.notes.startswith(f"source={SYNTHESIS_SOURCE_TAG_WINDOW}")
    ]
    assert len(llm_survivors) == 1
    assert len(synthesised) == 1
