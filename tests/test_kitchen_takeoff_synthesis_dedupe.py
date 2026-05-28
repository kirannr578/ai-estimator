"""Tests for the Phase T2.10 kitchen synthesis + dedupe wrappers.

Combined coverage for ``synthesize_kitchen_takeoff_items`` (fan-out
shape, CSI mapping, confidence inheritance) and
``dedupe_kitchen_against_synthesis`` (LLM aggregate suppression,
cross-division safety).
"""

from __future__ import annotations

from core.extraction.kitchen_dedupe import dedupe_kitchen_against_synthesis
from core.extraction.takeoff_synthesis import (
    DERIVATION_HAIRCUT_MULTIPLIER,
    SYNTHESIS_SOURCE_TAG_KITCHEN,
    inherit_with_haircut,
    synthesize_kitchen_takeoff_items,
)
from core.schemas import (
    CostBand,
    KitchenEquipmentRecord,
    KitchenScheduleResult,
    TakeoffItem,
    band_for_confidence,
)


# ---------------------------------------------------------------------------
# Record builders
# ---------------------------------------------------------------------------


def _range(*, qty: int | None = None, mfr: str | None = None,
            model: str | None = None) -> KitchenEquipmentRecord:
    return KitchenEquipmentRecord(
        tag="RA-1",
        item_type="RANGE",
        description="6-burner range",
        manufacturer=mfr,
        model_number=model,
        btu_rating=120000,
        utility_gas=True,
        quantity=qty,
    )


def _refrigerator(*, mfr: str | None = None,
                    model: str | None = None) -> KitchenEquipmentRecord:
    return KitchenEquipmentRecord(
        tag="REF-1",
        item_type="REFRIGERATOR",
        description="Reach-in refrigerator",
        manufacturer=mfr,
        model_number=model,
        utility_electric=True,
        voltage="120V",
        quantity=1,
    )


def _walkin() -> KitchenEquipmentRecord:
    return KitchenEquipmentRecord(
        tag="WI-1",
        item_type="WALK_IN",
        description="8x10 walk-in cooler",
        utility_electric=True,
        utility_water=True,
        utility_drain=True,
        quantity=1,
    )


def _hood() -> KitchenEquipmentRecord:
    return KitchenEquipmentRecord(
        tag="HD-1",
        item_type="HOOD",
        description="10' island canopy hood",
        utility_electric=True,
        quantity=1,
    )


def _llm(description: str, *, csi_section: str | None = "11 40 00",
         csi_division: str = "11") -> TakeoffItem:
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=1.0,
        unit="EA",
        confidence=0.7,
    )


# ---------------------------------------------------------------------------
# Synthesis — shape + count
# ---------------------------------------------------------------------------


def test_synthesize_empty_input_returns_empty() -> None:
    assert synthesize_kitchen_takeoff_items(None) == []
    assert synthesize_kitchen_takeoff_items([]) == []
    assert synthesize_kitchen_takeoff_items(
        KitchenScheduleResult(equipment=[])
    ) == []


def test_synthesize_range_with_qty_and_mfr_emits_three_rows() -> None:
    """RANGE with QTY and (mfr+model) → 3 rows: equipment, gas rough-in, trim."""
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan", model="VHP660"),
    ])
    assert len(items) == 3
    eq, roughin, trim = items
    assert eq.unit == "EA"
    assert eq.quantity == 2.0
    assert eq.confidence == 0.90
    assert eq.csi_section == "11 40 13.13"
    assert roughin.unit == "LS"
    assert roughin.csi_section == "22 11 16"  # gas/water-side
    assert trim.unit == "LS"
    assert trim.csi_section == "11 40 13.13"


def test_synthesize_refrigerator_without_mfr_emits_two_rows() -> None:
    """REFRIGERATOR with no mfr/model → 2 rows (equipment + electrical rough-in)."""
    items = synthesize_kitchen_takeoff_items([_refrigerator()])
    assert len(items) == 2
    eq, roughin = items
    assert eq.csi_section == "11 40 16.13"
    assert roughin.csi_section == "26 27 26"  # electrical-only


def test_synthesize_walkin_routes_to_water_dominant_roughin() -> None:
    """WALK_IN with water+drain+electric → water-dominant rough-in (22 11 16)."""
    items = synthesize_kitchen_takeoff_items([_walkin()])
    assert len(items) == 2
    eq, roughin = items
    assert eq.csi_section == "11 40 16.13"
    assert roughin.csi_section == "22 11 16"


def test_synthesize_hood_routes_to_ductwork_roughin() -> None:
    """HOOD always routes the rough-in to 23 31 13 ductwork regardless of other utilities."""
    items = synthesize_kitchen_takeoff_items([_hood()])
    assert len(items) == 2
    eq, roughin = items
    assert eq.csi_section == "11 40 13.16"
    assert roughin.csi_section == "23 31 13"
    assert roughin.csi_division == "23"


def test_synthesize_dishwasher_csi() -> None:
    record = KitchenEquipmentRecord(
        tag="DW-1", item_type="DISHWASHER",
        description="High-temp dishwasher", utility_water=True, quantity=1,
    )
    items = synthesize_kitchen_takeoff_items([record])
    assert items[0].csi_section == "11 40 19.13"


def test_synthesize_sink_csi() -> None:
    record = KitchenEquipmentRecord(
        tag="SK-1", item_type="SINK",
        description="3-compartment sink", utility_water=True, utility_drain=True,
        quantity=1,
    )
    items = synthesize_kitchen_takeoff_items([record])
    assert items[0].csi_section == "11 40 13"


def test_synthesize_other_falls_back_to_generic_section() -> None:
    record = KitchenEquipmentRecord(
        tag="K-9", item_type="OTHER",
        description="Mystery appliance",
    )
    items = synthesize_kitchen_takeoff_items([record])
    assert items[0].csi_section == "11 40 00"


def test_synthesize_skips_blank_tags() -> None:
    record = KitchenEquipmentRecord(
        tag="", item_type="RANGE", description="Unmarked",
    )
    assert synthesize_kitchen_takeoff_items([record]) == []


def test_synthesize_no_utilities_skips_roughin() -> None:
    """Equipment with all-None utility flags → 1 row (no rough-in)."""
    record = KitchenEquipmentRecord(
        tag="PT-1", item_type="PREP_TABLE", description="SS prep table",
    )
    items = synthesize_kitchen_takeoff_items([record])
    assert len(items) == 1
    assert items[0].csi_section == "11 40 13"


# ---------------------------------------------------------------------------
# Confidence inheritance — T6.1 verify
# ---------------------------------------------------------------------------


def test_roughin_inherits_haircut_from_parent_confidence() -> None:
    """Verify rough-in confidence == inherit_with_haircut(0.90)."""
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan", model="VHP660"),
    ])
    _, roughin, _ = items
    assert roughin.confidence == inherit_with_haircut(0.90)
    # Sanity: 0.90 × 0.95 = 0.855 floored at 0.45 → 0.855.
    assert roughin.confidence == 0.855


def test_trim_inherits_double_haircut_from_parent_confidence() -> None:
    """Trim confidence == max(0.45, parent × 0.95 × 0.70)."""
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan", model="VHP660"),
    ])
    _, _, trim = items
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.70,
    )
    assert trim.confidence == expected
    # 0.90 × 0.95 × 0.70 = 0.5985 floored at 0.45 → 0.5985.
    assert trim.confidence == 0.5985


def test_no_qty_lands_in_hand_takeoff_band() -> None:
    """No QTY → confidence 0.55 → HAND_TAKEOFF queue."""
    items = synthesize_kitchen_takeoff_items([_range(mfr="Vulcan", model="VHP660")])
    eq = items[0]
    assert eq.confidence == 0.55
    assert band_for_confidence(eq.confidence) == CostBand.HAND_TAKEOFF


def test_qty_lands_in_auto_approve_band() -> None:
    """QTY published → confidence 0.90 → AUTO_APPROVE queue."""
    items = synthesize_kitchen_takeoff_items([_range(qty=3)])
    eq = items[0]
    assert eq.confidence == 0.90
    assert band_for_confidence(eq.confidence) == CostBand.AUTO_APPROVE


# ---------------------------------------------------------------------------
# Trim conditional — mfr+model gating
# ---------------------------------------------------------------------------


def test_trim_skipped_when_manufacturer_missing() -> None:
    """No mfr → 2 rows (equipment + rough-in), no trim."""
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, model="VHP660"),
    ])
    assert len(items) == 2


def test_trim_skipped_when_model_missing() -> None:
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan"),
    ])
    assert len(items) == 2


def test_trim_included_when_both_mfr_and_model_present() -> None:
    items = synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan", model="VHP660"),
    ])
    assert len(items) == 3
    assert any("trim" in (it.description or "").lower() for it in items)


# ---------------------------------------------------------------------------
# Notes / source-tag wiring
# ---------------------------------------------------------------------------


def test_notes_carry_kitchen_source_tag() -> None:
    items = synthesize_kitchen_takeoff_items([_range(qty=1)])
    for it in items:
        assert (it.notes or "").startswith(
            f"source={SYNTHESIS_SOURCE_TAG_KITCHEN}"
        )


def test_description_prefix_is_kitchen_equipment() -> None:
    items = synthesize_kitchen_takeoff_items([_range(qty=1)])
    for it in items:
        assert (it.description or "").lower().startswith("kitchen equipment")


def test_sheet_id_threads_into_source_sheet_ids() -> None:
    items = synthesize_kitchen_takeoff_items(
        [_range(qty=1)], sheet_id="K2.0",
    )
    for it in items:
        assert "K2.0" in (it.source_sheet_ids or [])


# ---------------------------------------------------------------------------
# Dedupe — basic
# ---------------------------------------------------------------------------


def _synth_range() -> list[TakeoffItem]:
    return synthesize_kitchen_takeoff_items([
        _range(qty=2, mfr="Vulcan", model="VHP660"),
    ])


def test_dedupe_suppresses_kitchen_equipment_aggregate() -> None:
    items = _synth_range() + [
        _llm("Kitchen Equipment"),
        _llm("Food Service Equipment installation"),
        _llm("Commercial Kitchen Equipment"),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Kitchen Equipment" not in descs
    assert "Food Service Equipment installation" not in descs
    assert "Commercial Kitchen Equipment" not in descs
    # The synth rows survive.
    assert any("Kitchen equipment RA-1" in d for d in descs)


def test_dedupe_suppresses_per_mark_llm_row() -> None:
    items = _synth_range() + [
        _llm("RA-1 range installation"),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "RA-1 range installation" not in descs


def test_dedupe_preserves_plumbing_fixture_rows() -> None:
    """Plumbing CSI rows are NEVER touched even when 'kitchen sink'-ish text appears."""
    items = _synth_range() + [
        TakeoffItem(
            csi_division="22", csi_section="22 41 16",
            description="Lavatory faucet", quantity=4.0, unit="EA",
            confidence=0.8,
        ),
        TakeoffItem(
            csi_division="22", csi_section="22 13 16",
            description="Sanitary waste piping", quantity=1.0, unit="LS",
            confidence=0.6,
        ),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Lavatory faucet" in descs
    assert "Sanitary waste piping" in descs


def test_dedupe_preserves_lighting_rows() -> None:
    items = _synth_range() + [
        TakeoffItem(
            csi_division="26", csi_section="26 51 13",
            description="LED downlight fixture", quantity=10.0, unit="EA",
            confidence=0.8,
        ),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "LED downlight fixture" in descs


def test_dedupe_preserves_doors() -> None:
    items = _synth_range() + [
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal door 3'-0\" x 7'-0\"",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Hollow metal door 3'-0\" x 7'-0\"" in descs


def test_dedupe_no_op_when_no_kitchen_synthesis_present() -> None:
    """Without any synthesised kitchen row, every input survives unchanged."""
    items = [
        _llm("Kitchen Equipment"),
        _llm("Food Service Equipment"),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    assert len(survivors) == 2


def test_dedupe_preserves_unrelated_kitchen_section_row() -> None:
    """LLM row in the kitchen division with a different mark survives."""
    items = _synth_range() + [
        TakeoffItem(
            csi_division="11", csi_section="11 40 00",
            description="Beverage cart, lobby",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Beverage cart, lobby" in descs


def test_dedupe_suppresses_walkin_cooler_aggregate() -> None:
    syn = synthesize_kitchen_takeoff_items([_walkin()])
    items = syn + [
        _llm("Walk-in cooler installation", csi_section="11 40 16.13"),
        _llm("Walk-in freezer", csi_section="11 40 16.13"),
    ]
    survivors = dedupe_kitchen_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Walk-in cooler installation" not in descs
    assert "Walk-in freezer" not in descs
