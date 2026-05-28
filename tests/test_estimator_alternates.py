"""Phase T9.0 — estimator alternates pricing tests.

Covers :func:`core.estimator.price_alternates` resolution paths:

* ``cost_delta`` populated → ``EXTRACTED_FROM_BID_FORM`` basis
* ``related_takeoff_items`` populated → ``SYNTHESIZED_FROM_TAKEOFF``
* neither → ``MISSING``

Plus the ``Estimate.alternates`` rollup helpers and the
``attach_alternates_to_estimate`` convenience wrapper.
"""

from __future__ import annotations

import pytest

from core.estimator import (
    attach_alternates_to_estimate,
    price_alternates,
)
from core.schemas import (
    AlternateLine,
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CostCategory,
    CostLine,
    Estimate,
    SiteInfo,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _project_with_alts(alts: list[AlternateLine]) -> ProjectModel:
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=[],
        sheet_summaries={},
        warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(name="T9 Alts"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=alts,
    )


def _line(
    *,
    section: str = "09 91 23",
    description: str = "Interior painting",
    total: float = 1000.0,
) -> CostLine:
    return CostLine(
        csi_division=section.split()[0],
        csi_section=section,
        description=description,
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


# ---------------------------------------------------------------------------
# Resolution paths
# ---------------------------------------------------------------------------


class TestPriceAlternatesCostDeltaPath:
    def test_extracted_from_bid_form_when_cost_delta_present(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add foo",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=5000.0,
        )
        result = price_alternates(_project_with_alts([alt]))
        assert len(result) == 1
        ale = result[0]
        assert ale.cost_delta == 5000.0
        assert ale.pricing_basis == AlternatePricingBasis.EXTRACTED_FROM_BID_FORM

    def test_extracted_preserves_signs(self) -> None:
        ded = AlternateLine(
            alternate_id="Alt 2",
            description="Deduct bar",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-2500.0,
        )
        result = price_alternates(_project_with_alts([ded]))
        assert result[0].cost_delta == -2500.0

    def test_extracted_applies_region_multiplier(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add foo",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=1000.0,
        )
        result = price_alternates(
            _project_with_alts([alt]), region_multiplier=1.15
        )
        assert result[0].cost_delta == 1150.0


class TestPriceAlternatesSynthesisPath:
    def test_synthesizes_from_takeoff_csi_match(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Substitute painting",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            related_takeoff_items=["09 91 23"],
        )
        line_items = [
            _line(section="09 91 23", total=1500.0),
            _line(section="03 30 00", description="Concrete", total=8000.0),
        ]
        result = price_alternates(_project_with_alts([alt]), line_items)
        assert len(result) == 1
        ale = result[0]
        assert ale.cost_delta == 1500.0
        assert ale.pricing_basis == AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF

    def test_synthesizes_from_description_substring(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 2",
            description="Painting alternate",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            related_takeoff_items=["painting"],
        )
        line_items = [_line(description="Interior painting", total=1200.0)]
        result = price_alternates(_project_with_alts([alt]), line_items)
        assert result[0].cost_delta == 1200.0
        assert result[0].pricing_basis == AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF

    def test_synthesis_for_deductive_flips_sign(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 3",
            description="Deduct painting scope",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=None,
            related_takeoff_items=["09 91 23"],
        )
        line_items = [_line(section="09 91 23", total=1500.0)]
        result = price_alternates(_project_with_alts([alt]), line_items)
        # DEDUCTIVE: synthesis flips to negative.
        assert result[0].cost_delta == -1500.0

    def test_synthesis_for_ve_flips_sign(self) -> None:
        alt = AlternateLine(
            alternate_id="VE-1",
            description="VE alternate roofing",
            alternate_type=AlternateType.VE,
            cost_delta=None,
            related_takeoff_items=["09 91 23"],
        )
        line_items = [_line(section="09 91 23", total=2000.0)]
        result = price_alternates(_project_with_alts([alt]), line_items)
        assert result[0].cost_delta == -2000.0

    def test_synthesis_confidence_includes_haircut(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Painting",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            related_takeoff_items=["09 91 23"],
            confidence=0.90,
        )
        line_items = [_line(section="09 91 23", total=1000.0)]
        result = price_alternates(_project_with_alts([alt]), line_items)
        # 0.90 * 0.85 = 0.765
        assert result[0].confidence == pytest.approx(0.765, abs=0.01)


class TestPriceAlternatesMissingPath:
    def test_missing_when_no_cost_no_synthesis(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add foo",
            cost_delta=None,
        )
        result = price_alternates(_project_with_alts([alt]))
        assert result[0].cost_delta is None
        assert result[0].pricing_basis == AlternatePricingBasis.MISSING

    def test_missing_when_synthesis_matches_nothing(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add foo",
            cost_delta=None,
            related_takeoff_items=["nonexistent csi"],
        )
        line_items = [_line(section="09 91 23", total=1500.0)]
        result = price_alternates(_project_with_alts([alt]), line_items)
        assert result[0].cost_delta is None
        assert result[0].pricing_basis == AlternatePricingBasis.MISSING

    def test_missing_confidence_capped_at_half(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="x",
            cost_delta=None,
            confidence=0.90,
        )
        result = price_alternates(_project_with_alts([alt]))
        # MISSING basis caps confidence at 0.50.
        assert result[0].confidence <= 0.50

    def test_missing_when_line_items_none(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="x",
            cost_delta=None,
            related_takeoff_items=["09 91 23"],
        )
        result = price_alternates(_project_with_alts([alt]), line_items=None)
        assert result[0].pricing_basis == AlternatePricingBasis.MISSING


# ---------------------------------------------------------------------------
# Estimate.alternates rollup
# ---------------------------------------------------------------------------


class TestAttachAlternatesToEstimate:
    def test_subtotal_base_only_excludes_alternates(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add foo",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=5000.0,
        )
        line_items = [_line(total=1000.0)]
        est = Estimate(project_name="T9", line_items=line_items)
        updated = attach_alternates_to_estimate(est, _project_with_alts([alt]))
        # Base subtotal unaffected by the alternate.
        assert updated.subtotal_base_only == 1000.0
        assert updated.subtotal == 1000.0
        # Alternate is rolled up in the priced list.
        assert len(updated.alternates) == 1
        assert updated.alternates[0].cost_delta == 5000.0

    def test_select_one_alternate_via_id(self) -> None:
        alts = [
            AlternateLine(
                alternate_id="Alt 1",
                description="Add A",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
            ),
            AlternateLine(
                alternate_id="Alt 2",
                description="Add B",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=300.0,
            ),
        ]
        line_items = [_line(total=1000.0)]
        est = Estimate(project_name="T9", line_items=line_items)
        updated = attach_alternates_to_estimate(est, _project_with_alts(alts))
        assert updated.subtotal_with_alternates_selected({"Alt 1"}) == 1500.0

    def test_select_multiple_alternates_sums(self) -> None:
        alts = [
            AlternateLine(
                alternate_id="Alt 1",
                description="Add A",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
            ),
            AlternateLine(
                alternate_id="Alt 2",
                description="Add B",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=300.0,
            ),
        ]
        est = Estimate(project_name="T9", line_items=[_line(total=1000.0)])
        updated = attach_alternates_to_estimate(est, _project_with_alts(alts))
        assert updated.subtotal_with_alternates_selected({"Alt 1", "Alt 2"}) == 1800.0

    def test_deductive_alternate_decreases_subtotal(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Deduct foo",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-500.0,
        )
        est = Estimate(project_name="T9", line_items=[_line(total=1000.0)])
        updated = attach_alternates_to_estimate(est, _project_with_alts([alt]))
        assert updated.subtotal_with_alternates_selected({"Alt 1"}) == 500.0

    def test_ve_alternate_behaves_like_deductive_numerically(self) -> None:
        ve = AlternateLine(
            alternate_id="VE-1",
            description="VE saving",
            alternate_type=AlternateType.VE,
            cost_delta=-200.0,
        )
        est = Estimate(project_name="T9", line_items=[_line(total=1000.0)])
        updated = attach_alternates_to_estimate(est, _project_with_alts([ve]))
        assert updated.subtotal_with_alternates_selected({"VE-1"}) == 800.0
        # And VE rolls into deductive total.
        assert updated.alternates_total_deductive == -200.0

    def test_included_by_default_populates_selected_default(self) -> None:
        alts = [
            AlternateLine(
                alternate_id="Alt 1",
                description="Pre-included",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
                included_by_default=True,
            ),
            AlternateLine(
                alternate_id="Alt 2",
                description="Optional",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=300.0,
                included_by_default=False,
            ),
        ]
        est = Estimate(project_name="T9", line_items=[])
        updated = attach_alternates_to_estimate(est, _project_with_alts(alts))
        assert updated.alternates_selected_default == {"Alt 1"}

    def test_region_multiplier_baked_into_cost_delta(self) -> None:
        alt = AlternateLine(
            alternate_id="Alt 1",
            description="Add",
            cost_delta=1000.0,
        )
        est = Estimate(
            project_name="T9", region_multiplier=1.10, line_items=[_line(total=1000.0)]
        )
        updated = attach_alternates_to_estimate(est, _project_with_alts([alt]))
        assert updated.alternates[0].cost_delta == 1100.0

    def test_attach_returns_new_estimate(self) -> None:
        alt = AlternateLine(alternate_id="Alt 1", description="x", cost_delta=100.0)
        est = Estimate(project_name="T9", line_items=[])
        updated = attach_alternates_to_estimate(est, _project_with_alts([alt]))
        # Original estimate not mutated.
        assert est.alternates == []
        # Returned estimate has the priced alternates.
        assert len(updated.alternates) == 1


# ---------------------------------------------------------------------------
# Mixed-type integration
# ---------------------------------------------------------------------------


def test_mixed_types_compose_correctly() -> None:
    alts = [
        AlternateLine(
            alternate_id="Alt 1",
            description="Add epoxy",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=5000.0,
        ),
        AlternateLine(
            alternate_id="Alt 2",
            description="Deduct skylight",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-2000.0,
        ),
        AlternateLine(
            alternate_id="Alt 3",
            description="Substitute LVT",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=300.0,
        ),
        AlternateLine(
            alternate_id="VE-1",
            description="VE roofing membrane",
            alternate_type=AlternateType.VE,
            cost_delta=-1200.0,
        ),
        AlternateLine(
            alternate_id="Alt 4",
            description="Missing",
            cost_delta=None,
        ),
    ]
    est = Estimate(
        project_name="T9",
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            CostLine(
                csi_division="09",
                csi_section="09 91 23",
                description="Base",
                quantity=100.0,
                unit="SF",
                unit_cost=100.0,
                total_cost=10000.0,
                cost_category=CostCategory.SUBCONTRACTOR,
                confidence=0.92,
            )
        ],
    )
    project = _project_with_alts(alts)
    updated = attach_alternates_to_estimate(est, project)

    assert updated.alternates_total_additive == 5000.0
    assert updated.alternates_total_deductive == -3200.0  # ded + VE
    assert updated.alternates_total_substitution == 300.0
    assert updated.alternates_count_missing == 1

    # All in: 10000 + 5000 - 2000 + 300 - 1200 = 12100 (Alt 4 missing → 0)
    all_ids = {"Alt 1", "Alt 2", "Alt 3", "VE-1", "Alt 4"}
    assert updated.subtotal_with_alternates_selected(all_ids) == 12100.0
