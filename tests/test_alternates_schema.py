"""Phase T9.0 — bid-alternates schema tests.

Covers:

* :class:`AlternateLine` validation: required fields, sign-warning
  validator behaviour.
* :class:`AlternateType` serialisation round-trip.
* :class:`AlternateLineEstimate` build from a priced source.
* :meth:`Estimate.subtotal_with_alternates_selected` math.
* :meth:`Estimate.total_with_alternates_selected` applies markups
  against the adjusted subtotal.
* ``included_by_default`` semantics flow to
  ``alternates_selected_default`` via the estimator attach.
"""

from __future__ import annotations

import json

import pytest

from core.schemas import (
    AlternateLine,
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CostCategory,
    CostLine,
    Estimate,
)


# ---------------------------------------------------------------------------
# AlternateLine
# ---------------------------------------------------------------------------


class TestAlternateLineConstruction:
    def test_minimum_fields(self) -> None:
        al = AlternateLine(alternate_id="Alternate 1", description="foo")
        assert al.alternate_id == "Alternate 1"
        assert al.alternate_type == AlternateType.ADDITIVE  # default
        assert al.cost_delta is None
        assert al.confidence == 0.7
        assert al.included_by_default is False

    def test_missing_required_fields_raises(self) -> None:
        with pytest.raises(Exception):
            AlternateLine()  # type: ignore[call-arg]
        with pytest.raises(Exception):
            AlternateLine(alternate_id="Alt 1")  # type: ignore[call-arg]

    def test_confidence_out_of_range_raises(self) -> None:
        with pytest.raises(Exception):
            AlternateLine(
                alternate_id="Alt 1", description="x", confidence=1.5
            )
        with pytest.raises(Exception):
            AlternateLine(
                alternate_id="Alt 1", description="x", confidence=-0.1
            )

    def test_sign_warning_additive_negative(self) -> None:
        """An ADDITIVE alternate with a negative cost_delta warns."""
        al = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=-500.0,
        )
        # Validator does NOT raise but stamps a note.
        assert al.cost_delta == -500.0
        assert al.operator_notes is not None
        assert "sign-warning" in al.operator_notes.lower()

    def test_sign_warning_deductive_positive(self) -> None:
        """A DEDUCTIVE alternate with a positive cost_delta warns."""
        al = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=500.0,
        )
        assert al.cost_delta == 500.0
        assert al.operator_notes is not None
        assert "sign-warning" in al.operator_notes.lower()

    def test_no_warning_when_signs_consistent(self) -> None:
        al = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=500.0,
        )
        assert al.operator_notes is None

    def test_no_warning_when_cost_delta_none(self) -> None:
        al = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=None,
        )
        assert al.operator_notes is None

    def test_substitution_signs_are_both_allowed(self) -> None:
        """SUBSTITUTION can carry either positive or negative delta."""
        pos = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=500.0,
        )
        neg = AlternateLine(
            alternate_id="Alt 2",
            description="bar",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=-500.0,
        )
        assert pos.operator_notes is None
        assert neg.operator_notes is None


# ---------------------------------------------------------------------------
# AlternateType serialisation
# ---------------------------------------------------------------------------


class TestAlternateTypeSerialisation:
    def test_round_trips_via_value(self) -> None:
        assert AlternateType("additive") == AlternateType.ADDITIVE
        assert AlternateType("deductive") == AlternateType.DEDUCTIVE
        assert AlternateType("substitution") == AlternateType.SUBSTITUTION
        assert AlternateType("value_engineering") == AlternateType.VE

    def test_model_dump_emits_string(self) -> None:
        al = AlternateLine(
            alternate_id="Alt 1",
            description="foo",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-100.0,
        )
        dumped = al.model_dump(mode="json")
        assert dumped["alternate_type"] == "deductive"
        # Round-trip via JSON.
        round_trip = AlternateLine(**json.loads(json.dumps(dumped)))
        assert round_trip.alternate_type == AlternateType.DEDUCTIVE


# ---------------------------------------------------------------------------
# AlternateLineEstimate
# ---------------------------------------------------------------------------


class TestAlternateLineEstimate:
    def test_minimum_fields(self) -> None:
        ale = AlternateLineEstimate(
            alternate_id="Alt 1",
            alternate_type=AlternateType.ADDITIVE,
            description="foo",
        )
        assert ale.cost_delta is None
        assert ale.pricing_basis == AlternatePricingBasis.MISSING
        assert ale.included_in_base is False

    def test_includes_pricing_basis(self) -> None:
        ale = AlternateLineEstimate(
            alternate_id="Alt 1",
            alternate_type=AlternateType.ADDITIVE,
            description="foo",
            cost_delta=500.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        )
        assert ale.cost_delta == 500.0
        assert ale.pricing_basis == AlternatePricingBasis.EXTRACTED_FROM_BID_FORM


# ---------------------------------------------------------------------------
# Estimate helpers
# ---------------------------------------------------------------------------


def _line(total: float, *, division: str = "09") -> CostLine:
    return CostLine(
        csi_division=division,
        csi_section=f"{division} 91 23",
        description="Test line",
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


def _ale(
    alt_id: str,
    *,
    cost: float | None = 1000.0,
    atype: AlternateType = AlternateType.ADDITIVE,
    basis: AlternatePricingBasis = AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
    included: bool = False,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alt_id,
        alternate_type=atype,
        description=f"desc {alt_id}",
        cost_delta=cost,
        pricing_basis=basis,
        included_in_base=included,
    )


class TestEstimateHelpers:
    def test_subtotal_base_only_equals_subtotal(self) -> None:
        est = Estimate(
            project_name="T9 base",
            line_items=[_line(1000.0), _line(2000.0)],
        )
        assert est.subtotal_base_only == est.subtotal == 3000.0

    def test_alternates_total_additive_sums_only_additive(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[],
            alternates=[
                _ale("A1", cost=500.0, atype=AlternateType.ADDITIVE),
                _ale("A2", cost=200.0, atype=AlternateType.ADDITIVE),
                _ale("A3", cost=-300.0, atype=AlternateType.DEDUCTIVE),
            ],
        )
        assert est.alternates_total_additive == 700.0

    def test_alternates_total_deductive_includes_ve(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[],
            alternates=[
                _ale("A1", cost=-500.0, atype=AlternateType.DEDUCTIVE),
                _ale("VE-1", cost=-200.0, atype=AlternateType.VE),
                _ale("A2", cost=300.0, atype=AlternateType.ADDITIVE),
            ],
        )
        assert est.alternates_total_deductive == -700.0

    def test_alternates_count_missing(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[],
            alternates=[
                _ale("A1", cost=500.0),
                _ale("A2", cost=None, basis=AlternatePricingBasis.MISSING),
                _ale("A3", cost=None, basis=AlternatePricingBasis.MISSING),
            ],
        )
        assert est.alternates_count_missing == 2

    def test_subtotal_with_selected_single(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[_line(1000.0)],
            alternates=[
                _ale("A1", cost=500.0, atype=AlternateType.ADDITIVE),
                _ale("A2", cost=-200.0, atype=AlternateType.DEDUCTIVE),
            ],
        )
        # Base + A1
        assert est.subtotal_with_alternates_selected({"A1"}) == 1500.0
        # Base + A2 (negative delta)
        assert est.subtotal_with_alternates_selected({"A2"}) == 800.0

    def test_subtotal_with_selected_multiple(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[_line(1000.0)],
            alternates=[
                _ale("A1", cost=500.0, atype=AlternateType.ADDITIVE),
                _ale("A2", cost=300.0, atype=AlternateType.ADDITIVE),
                _ale("A3", cost=-200.0, atype=AlternateType.DEDUCTIVE),
            ],
        )
        # Base + A1 + A2 + A3 = 1000 + 500 + 300 - 200
        assert est.subtotal_with_alternates_selected({"A1", "A2", "A3"}) == 1600.0

    def test_subtotal_with_empty_selection_equals_base(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[_line(1000.0)],
            alternates=[_ale("A1", cost=500.0)],
        )
        assert est.subtotal_with_alternates_selected(set()) == 1000.0
        assert est.subtotal_with_alternates_selected(None) == 1000.0

    def test_subtotal_skips_alternates_with_no_cost(self) -> None:
        est = Estimate(
            project_name="T9",
            line_items=[_line(1000.0)],
            alternates=[_ale("A1", cost=None, basis=AlternatePricingBasis.MISSING)],
        )
        # Selecting an unpriced alternate contributes 0.0 — not None.
        assert est.subtotal_with_alternates_selected({"A1"}) == 1000.0

    def test_total_with_alternates_applies_markups(self) -> None:
        # subtotal 1000, +500 alt = 1500; cont 10% → 150; oh 10% on 1650 → 165;
        # profit 5% on 1815 → 90.75; total 1905.75.
        est = Estimate(
            project_name="T9",
            contingency_pct=10.0,
            overhead_pct=10.0,
            profit_pct=5.0,
            line_items=[_line(1000.0)],
            alternates=[_ale("A1", cost=500.0, atype=AlternateType.ADDITIVE)],
        )
        result = est.total_with_alternates_selected({"A1"})
        assert result == pytest.approx(1905.75, abs=0.01)

    def test_total_with_no_alternates_matches_grand_total(self) -> None:
        est = Estimate(
            project_name="T9",
            contingency_pct=10.0,
            overhead_pct=10.0,
            profit_pct=5.0,
            line_items=[_line(1000.0)],
            alternates=[_ale("A1", cost=500.0)],
        )
        # Empty selection → base bid only.
        assert est.total_with_alternates_selected(set()) == pytest.approx(
            est.grand_total, abs=0.01
        )


class TestIncludedByDefaultSemantics:
    def test_alternates_selected_default_field_exists(self) -> None:
        est = Estimate(project_name="T9")
        assert est.alternates_selected_default == set()

    def test_alternates_selected_default_set_explicitly(self) -> None:
        est = Estimate(
            project_name="T9",
            alternates_selected_default={"A1", "A2"},
        )
        assert est.alternates_selected_default == {"A1", "A2"}

    def test_included_in_base_attribute_preserved(self) -> None:
        ale = _ale("A1", included=True)
        assert ale.included_in_base is True
