"""Phase T6.1 — MANUAL_OVERRIDE end-to-end tests.

Covers :func:`apply_manual_override` from ``core.estimator``:

* Override an INTERPOLATED line → tier=MANUAL_OVERRIDE, price_conf=1.0
* Override a MISSING line → no longer suppressed, total_cost recomputed
* Override preserves entity-level fields (description, qty, csi, etc.)
* Operator note appended via the ``MANUAL_OVERRIDE_NOTE_PREFIX`` sentinel
* Idempotency under same-arguments re-application
* Aggregate recomputation (subtotal, total_by_tier, count_by_tier)
* Round-trip through ``model_dump`` / ``model_validate``
* line_id resolution (int / cost_source / description / disambiguation)

The Streamlit UI wiring is intentionally deferred (T6.2 follow-up) per
the brief; these tests pin the public function only.
"""

from __future__ import annotations

import pytest

from core.estimator import (
    MANUAL_OVERRIDE_NOTE_PREFIX,
    apply_manual_override,
)
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _line(
    *,
    description: str = "Interior painting",
    csi_division: str = "09",
    csi_section: str = "09 91 23",
    quantity: float = 100.0,
    unit: str = "SF",
    unit_cost: float = 2.0,
    confidence: float = 0.92,
    price_confidence: float = 0.65,
    tier: CostSourceTier = CostSourceTier.INTERPOLATED,
    band: CostBand = CostBand.OPERATOR_REVIEW,
    cost_source: str = "cwicr:42",
    suppressed: bool = False,
    notes: str | None = None,
) -> CostLine:
    return CostLine(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit=unit,
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        price_confidence=price_confidence,
        cost_source_tier=tier,
        cost_band=band,
        suppressed=suppressed,
        cost_source=cost_source,
        notes=notes,
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.1 manual override",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# Core override behaviour
# ---------------------------------------------------------------------------


def test_override_interpolated_line_stamps_manual_override_tier_and_full_conf() -> None:
    """An INTERPOLATED line gets tier=MANUAL_OVERRIDE + price_confidence=1.0."""
    est = _estimate([_line()])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    li = out.line_items[0]
    assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert li.price_confidence == pytest.approx(1.0)


def test_override_recomputes_total_cost() -> None:
    est = _estimate([_line(quantity=100.0, unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    li = out.line_items[0]
    assert li.unit_cost == pytest.approx(3.50)
    assert li.total_cost == pytest.approx(350.0)


def test_override_preserves_entity_fields() -> None:
    """Description, qty, unit, csi_division, csi_section, cost_source must
    pass through unchanged — only unit_cost / tier / band / price_conf
    / total_cost / suppressed / notes are modified by the override."""
    original = _line(
        description="Interior painting walls",
        csi_division="09",
        csi_section="09 91 23",
        quantity=500.0,
        unit="SF",
        cost_source="cwicr:777",
    )
    est = _estimate([original])
    out = apply_manual_override(est, 0, new_unit_cost=2.25)
    li = out.line_items[0]
    assert li.description == "Interior painting walls"
    assert li.csi_division == "09"
    assert li.csi_section == "09 91 23"
    assert li.quantity == pytest.approx(500.0)
    assert li.unit == "SF"
    assert li.cost_source == "cwicr:777"


def test_override_missing_line_clears_suppression_and_prices() -> None:
    """A MISSING / suppressed line becomes priced + un-suppressed after
    override — hand-pricing IS the resolution to a unit-mismatch."""
    line = _line(
        unit_cost=0.0,
        price_confidence=0.0,
        tier=CostSourceTier.MISSING,
        band=CostBand.HAND_TAKEOFF,
        suppressed=True,
    )
    est = _estimate([line])
    out = apply_manual_override(est, 0, new_unit_cost=4.20)
    li = out.line_items[0]
    assert li.suppressed is False
    assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert li.price_confidence == pytest.approx(1.0)
    assert li.total_cost == pytest.approx(4.20 * 100.0)
    # Override clears HAND_TAKEOFF: 0.92 qty × 1.0 price = 0.92 → AUTO_APPROVE.
    assert li.cost_band == CostBand.AUTO_APPROVE


def test_override_band_recomputed_from_combined_confidence() -> None:
    """A 0.70 qty + 1.0 price = 0.70 → OPERATOR_REVIEW band post-override."""
    est = _estimate([_line(confidence=0.70)])
    out = apply_manual_override(est, 0, new_unit_cost=2.5)
    assert out.line_items[0].cost_band == CostBand.OPERATOR_REVIEW


# ---------------------------------------------------------------------------
# Operator notes
# ---------------------------------------------------------------------------


def test_operator_note_appended_with_sentinel_prefix() -> None:
    est = _estimate([_line(notes="originally cwicr 0.65")])
    out = apply_manual_override(
        est, 0, new_unit_cost=3.0,
        operator_note="hand-priced from supplier quote 12345",
    )
    notes = out.line_items[0].notes or ""
    assert "originally cwicr 0.65" in notes
    assert MANUAL_OVERRIDE_NOTE_PREFIX in notes
    assert "supplier quote 12345" in notes


def test_no_operator_note_still_stamps_minimal_sentinel() -> None:
    """When operator_note is None, the sentinel itself is still appended
    so a downstream reader can detect the override — but only on the
    FIRST override, to keep the notes blob bounded under retries."""
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    assert out.line_items[0].notes == MANUAL_OVERRIDE_NOTE_PREFIX


def test_operator_note_appended_to_empty_notes_field() -> None:
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(
        est, 0, new_unit_cost=3.0, operator_note="from RSMeans 2025",
    )
    assert out.line_items[0].notes == (
        f"{MANUAL_OVERRIDE_NOTE_PREFIX}: from RSMeans 2025"
    )


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


def test_override_idempotent_under_same_args_no_note() -> None:
    """Applying the same override twice without an operator_note retry
    arg yields a CostLine whose unit_cost / total_cost / tier match
    the single-application result."""
    est = _estimate([_line()])
    once = apply_manual_override(est, 0, new_unit_cost=3.50)
    twice = apply_manual_override(once, 0, new_unit_cost=3.50)
    a = once.line_items[0]
    b = twice.line_items[0]
    assert b.unit_cost == a.unit_cost
    assert b.total_cost == a.total_cost
    assert b.cost_source_tier == a.cost_source_tier
    assert b.price_confidence == a.price_confidence
    assert b.cost_band == a.cost_band


def test_override_does_not_mutate_input_estimate() -> None:
    """Returns a new Estimate; the input is preserved for rollback / diff."""
    line = _line(unit_cost=2.0)
    est = _estimate([line])
    _ = apply_manual_override(est, 0, new_unit_cost=99.0)
    assert est.line_items[0].unit_cost == pytest.approx(2.0)
    assert est.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED


# ---------------------------------------------------------------------------
# Aggregate recomputation
# ---------------------------------------------------------------------------


def test_subtotal_reflects_new_unit_cost_after_override() -> None:
    est = _estimate([
        _line(quantity=100.0, unit_cost=2.0,  # 200 total
               confidence=0.92,
               tier=CostSourceTier.EXACT_MATCH,
               price_confidence=0.95,
               band=CostBand.AUTO_APPROVE),
    ])
    pre_subtotal = est.subtotal
    out = apply_manual_override(est, 0, new_unit_cost=5.0)  # 500 total
    assert out.subtotal != pre_subtotal
    assert out.subtotal == pytest.approx(500.0)


def test_count_by_tier_reflects_new_manual_override_bucket() -> None:
    est = _estimate([
        _line(tier=CostSourceTier.INTERPOLATED, price_confidence=0.65),
        _line(tier=CostSourceTier.EXACT_MATCH, price_confidence=0.95,
              description="other"),
    ])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    counts = out.count_by_tier
    assert counts[CostSourceTier.MANUAL_OVERRIDE] == 1
    assert counts[CostSourceTier.INTERPOLATED] == 0
    assert counts[CostSourceTier.EXACT_MATCH] == 1


def test_total_by_tier_aggregates_overridden_line_into_manual_bucket() -> None:
    est = _estimate([_line(quantity=100.0, unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=4.50)
    totals = out.total_by_tier
    assert totals[CostSourceTier.MANUAL_OVERRIDE] == pytest.approx(450.0)
    assert totals[CostSourceTier.INTERPOLATED] == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Round-trip
# ---------------------------------------------------------------------------


def test_overridden_line_round_trips_via_model_dump_validate() -> None:
    est = _estimate([_line()])
    out = apply_manual_override(est, 0, new_unit_cost=2.5)
    payload = out.model_dump()
    rebuilt = Estimate.model_validate(payload)
    li = rebuilt.line_items[0]
    assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert li.price_confidence == pytest.approx(1.0)
    assert li.unit_cost == pytest.approx(2.5)


# ---------------------------------------------------------------------------
# line_id resolution
# ---------------------------------------------------------------------------


def test_line_id_int_index_works() -> None:
    est = _estimate([
        _line(description="A", cost_source="cwicr:1"),
        _line(description="B", cost_source="cwicr:2"),
    ])
    out = apply_manual_override(est, 1, new_unit_cost=9.99)
    assert out.line_items[0].unit_cost == pytest.approx(2.0)  # unchanged
    assert out.line_items[1].unit_cost == pytest.approx(9.99)


def test_line_id_negative_int_index_works() -> None:
    est = _estimate([
        _line(description="A"),
        _line(description="B"),
    ])
    out = apply_manual_override(est, -1, new_unit_cost=9.99)
    assert out.line_items[1].unit_cost == pytest.approx(9.99)


def test_line_id_cost_source_string_works() -> None:
    est = _estimate([
        _line(description="A", cost_source="cwicr:1"),
        _line(description="B", cost_source="09 91 23"),
    ])
    out = apply_manual_override(est, "cwicr:1", new_unit_cost=8.88)
    assert out.line_items[0].unit_cost == pytest.approx(8.88)


def test_line_id_description_string_works() -> None:
    est = _estimate([
        _line(description="Slab on grade", cost_source="cwicr:1"),
        _line(description="Interior painting", cost_source="cwicr:2"),
    ])
    out = apply_manual_override(est, "Interior painting", new_unit_cost=8.88)
    assert out.line_items[1].unit_cost == pytest.approx(8.88)


def test_line_id_ambiguous_string_raises() -> None:
    est = _estimate([
        _line(description="Interior painting", cost_source="X"),
        _line(description="Interior painting", cost_source="Y"),
    ])
    with pytest.raises(ValueError, match="matched 2 lines"):
        apply_manual_override(est, "Interior painting", new_unit_cost=1.0)


def test_line_id_missing_string_raises() -> None:
    est = _estimate([_line()])
    with pytest.raises(ValueError, match="no line item matched"):
        apply_manual_override(est, "nope", new_unit_cost=1.0)


def test_line_id_out_of_range_int_raises() -> None:
    est = _estimate([_line()])
    with pytest.raises(ValueError, match="out of range"):
        apply_manual_override(est, 99, new_unit_cost=1.0)


def test_empty_estimate_raises() -> None:
    est = _estimate([])
    with pytest.raises(ValueError, match="no line items"):
        apply_manual_override(est, 0, new_unit_cost=1.0)


def test_negative_unit_cost_raises() -> None:
    est = _estimate([_line()])
    with pytest.raises(ValueError, match="≥ 0"):
        apply_manual_override(est, 0, new_unit_cost=-5.0)
