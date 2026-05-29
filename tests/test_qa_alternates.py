"""QA-2 subsystem 7 — bid alternates extraction + estimate rollup.

Worker YY-2 / Pair 25 / subsystem 7 of the QA decomposition. Covers:

* Deterministic regex extraction from bid-form text:
  ADDITIVE / DEDUCTIVE / SUBSTITUTION / VE classification, signed
  ``cost_delta`` convention, blank-fillable-line ($_______) →
  ``cost_delta=None`` semantics.
* :func:`detect_alternates_section` page-level detection.
* :func:`should_invoke_llm_fallback` predicate (regex pass returns
  empty → caller invokes LLM).
* :func:`reconcile_alternate_sources` cross-source dedupe across
  non-canonical id formats ("Alt #1" / "Alternate No. 1" / "Bid
  Alternate 1") via :func:`_normalize_id_for_dedupe`.
* :class:`Estimate` rollup helpers — ``subtotal_with_alternates_selected``,
  ``alternates_total_additive`` / ``…_deductive`` /
  ``…_substitution``, zero-alternates safety.

LLM fallback is mocked at the boundary — tests construct
:class:`AlternateLine` records directly that simulate the LLM-fallback
return and pass them to :func:`reconcile_alternate_sources`. NO
:mod:`core.extractors` imports, NO LLM client, NO network — same
mocking pattern as ``tests/test_bid_form_alternates_extraction.py``.
"""

from __future__ import annotations

import pytest

from core.estimator import attach_alternates_to_estimate
from core.extraction.bid_form_alternates import (
    classify_alternate_type,
    detect_alternates_section,
    extract_alternates_from_page,
    parse_cost_delta,
    reconcile_alternate_sources,
    should_invoke_llm_fallback,
)
from core.schemas import (
    AlternateLine,
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
        project_info=ProjectInfo(name="QA-2 Alternates"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=alts,
    )


def _line(total: float = 1000.0, description: str = "Base scope") -> CostLine:
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description=description,
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


# ---------------------------------------------------------------------------
# Positive scenarios
# ---------------------------------------------------------------------------


class TestQAAlternatesPositive:
    """Two positive scenarios — happy paths through extraction + selection."""

    def test_qa_alternates_p1_three_additive_alternates_extracted(
        self,
    ) -> None:
        """POS-1: a bid-form section with 3 ADDITIVE alternates parses
        cleanly. Each alternate carries a positive ``cost_delta``, the
        ADDITIVE type, and a deterministic-tier confidence (>= 0.55)."""
        page = (
            "BID ALTERNATES\n"
            "\n"
            "Alternate No. 1: Add epoxy floor coating to mechanical "
            "rooms 101 and 102. ........ $5,000\n"
            "Alternate No. 2: Add stainless steel countertops in lab. "
            "................................ $12,500\n"
            "Alternate No. 3: Additional roof ladder access hatch with "
            "stairs. .......................... $3,750\n"
        )
        assert detect_alternates_section(page) is True
        alts = extract_alternates_from_page(
            page, bid_package_id="bid-form-1", source_sheet="Bid Form p.3"
        )
        assert len(alts) == 3
        for alt in alts:
            assert alt.alternate_type == AlternateType.ADDITIVE
            assert alt.cost_delta is not None and alt.cost_delta > 0
            assert alt.confidence >= 0.55
            assert alt.bid_package_id == "bid-form-1"
            assert alt.source_sheet == "Bid Form p.3"
        # Specific deltas match the printed amounts.
        deltas = sorted(alt.cost_delta for alt in alts)
        assert deltas == [3750.0, 5000.0, 12500.0]
        # Ids are stable + human-readable.
        ids = sorted(alt.alternate_id for alt in alts)
        assert ids == ["Alternate 1", "Alternate 2", "Alternate 3"]

    def test_qa_alternates_p2_selection_toggle_reflects_subset(self) -> None:
        """POS-2: ``subtotal_with_alternates_selected({A1, A2})`` includes
        ONLY the selected ADDITIVE alternates' deltas; A3 is excluded.
        The base subtotal is unchanged regardless of selection."""
        alts = [
            AlternateLine(
                alternate_id="Alternate 1",
                description="Add A",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
            ),
            AlternateLine(
                alternate_id="Alternate 2",
                description="Add B",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=300.0,
            ),
            AlternateLine(
                alternate_id="Alternate 3",
                description="Add C",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=200.0,
            ),
        ]
        est = Estimate(project_name="QA-2 P2", line_items=[_line(total=1000.0)])
        updated = attach_alternates_to_estimate(est, _project_with_alts(alts))
        assert updated.subtotal_base_only == 1000.0
        # Empty selection → just the base.
        assert updated.subtotal_with_alternates_selected(set()) == 1000.0
        # Two of three selected → base + 500 + 300.
        assert (
            updated.subtotal_with_alternates_selected({"Alternate 1", "Alternate 2"})
            == 1800.0
        )
        # All three selected → base + 1000.
        assert (
            updated.subtotal_with_alternates_selected(
                {"Alternate 1", "Alternate 2", "Alternate 3"}
            )
            == 2000.0
        )
        # Total (with markups) recomputed against the adjusted subtotal.
        # base 1800, cont 10% = 180, oh on (1800+180)*10% = 198, profit 5%
        # on (1800+180+198) = 108.90 → grand 2286.90.
        total_two = updated.total_with_alternates_selected(
            {"Alternate 1", "Alternate 2"}
        )
        assert total_two == pytest.approx(2286.90, abs=0.05)


# ---------------------------------------------------------------------------
# Negative scenarios
# ---------------------------------------------------------------------------


class TestQAAlternatesNegative:
    """Two negative scenarios — pages without parseable alternates."""

    def test_qa_alternates_n1_no_section_header_extracts_zero(self) -> None:
        """NEG-1: a bid form whose text contains no alternates section
        keyword extracts zero alternates AND
        :func:`should_invoke_llm_fallback` returns ``False``. The LLM
        fallback path is NEVER triggered for an out-of-scope page."""
        page = (
            "GENERAL CONDITIONS\n\n"
            "The Contractor shall provide all labour, materials, and "
            "equipment to complete the Work as described in the "
            "Drawings and Specifications. Payment shall be made monthly "
            "based on the Schedule of Values.\n"
        )
        assert detect_alternates_section(page) is False
        alts = extract_alternates_from_page(page)
        assert alts == []
        # And the predicate refuses to suggest LLM fallback for this page.
        assert should_invoke_llm_fallback(page, alts) is False

    def test_qa_alternates_n2_section_present_unparseable_invokes_llm(
        self,
    ) -> None:
        """NEG-2: a page with the section header but no regex-matchable
        line bodies returns zero alternates from the deterministic pass
        AND :func:`should_invoke_llm_fallback` returns ``True``. The
        caller would then invoke the LLM; we mock that LLM result as
        empty and confirm :func:`reconcile_alternate_sources` produces
        zero alternates without crashing."""
        # Section keyword present but nothing the regex line-parser
        # recognises (no "Alternate N:" / "Alt #N" / "VE Item N" prefix).
        page = (
            "BID ALTERNATES SECTION\n\n"
            "The schedule of alternates is to be supplied by the bidder "
            "on the attached blank form. Refer to the architect for "
            "scoping clarifications.\n"
        )
        assert detect_alternates_section(page) is True
        deterministic = extract_alternates_from_page(page)
        assert deterministic == []
        assert should_invoke_llm_fallback(page, deterministic) is True
        # Mock the LLM-fallback result as empty (the model also failed to
        # find a structured alternate). Reconciliation must produce zero.
        mocked_llm: list[AlternateLine] = []
        reconciled = reconcile_alternate_sources(deterministic, mocked_llm)
        assert reconciled == []


# ---------------------------------------------------------------------------
# Edge scenarios
# ---------------------------------------------------------------------------


class TestQAAlternatesEdge:
    """Three edge scenarios — sign coercion, id dedupe, zero-alternates."""

    def test_qa_alternates_e1_deductive_positive_amount_sign_coerced(
        self,
    ) -> None:
        """EDGE-1: a DEDUCTIVE alternate printed with a positive magnitude
        (``$1,500`` instead of ``-$1,500``) — bid forms commonly print the
        magnitude alongside a separate ``DEDUCT`` label. The extractor's
        ``_apply_type_sign`` coerces to negative so the math composes
        naturally with :pyattr:`Estimate.alternates_total_deductive`."""
        page = (
            "BID ALTERNATES\n"
            "Alternate No. 2 (DEDUCT): Skylight system at corridor 200. "
            "................................. $1,500\n"
        )
        alts = extract_alternates_from_page(page)
        assert len(alts) == 1
        alt = alts[0]
        assert alt.alternate_type == AlternateType.DEDUCTIVE
        # Sign coerced: parser saw +1500.0 in the text, applied negative
        # for DEDUCTIVE per the schema sign convention.
        assert alt.cost_delta == pytest.approx(-1500.0, abs=0.01)
        # And the schema sign-warning validator does NOT fire on the
        # coerced (negative) value — it only fires on a mismatched
        # construction. Confirm operator_notes is clean.
        assert alt.operator_notes is None or "[sign-warning]" not in (
            alt.operator_notes or ""
        )
        # Soft-warn behaviour pinned: a hand-constructed DEDUCTIVE with a
        # mistakenly-positive cost_delta DOES emit the [sign-warning]
        # marker (validator runs on the as-given values).
        bad = AlternateLine(
            alternate_id="Alternate 99",
            description="Skylight",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=1500.0,  # mismatched: positive on DEDUCTIVE
        )
        assert bad.operator_notes is not None
        assert "[sign-warning]" in bad.operator_notes

    def test_qa_alternates_e2_non_canonical_ids_dedupe_correctly(
        self,
    ) -> None:
        """EDGE-2: cross-source dedupe collapses ``"Alt #1"`` /
        ``"Alternate No. 1"`` / ``"Alternate 1"`` to a single canonical
        record (per :func:`_normalize_id_for_dedupe`). The deterministic
        record (higher confidence) wins; LLM-only records pass through.

        Pinned VE-family separation: ``"VE-3"`` does NOT collapse into
        the alternate-family bucket — different naming conventions stay
        distinct."""
        deterministic = [
            AlternateLine(
                alternate_id="Alt #1",
                description="Add deterministic detail A",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
                confidence=0.85,
            ),
            AlternateLine(
                alternate_id="VE-3",
                description="Substitute roofing membrane",
                alternate_type=AlternateType.VE,
                cost_delta=-1200.0,
                confidence=0.85,
            ),
        ]
        # LLM fallback returned the SAME alternate as #1 with an
        # alternate id format ("Alternate No. 1") plus a fresh #2.
        llm_extracted = [
            AlternateLine(
                alternate_id="Alternate No. 1",
                description="Add LLM detail A (less complete)",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=500.0,
                confidence=0.70,
            ),
            AlternateLine(
                alternate_id="Bid Alternate 2",
                description="Add B - LLM-only",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=300.0,
                confidence=0.70,
            ),
        ]
        reconciled = reconcile_alternate_sources(deterministic, llm_extracted)
        # Three distinct records: the merged-#1 (deterministic wins), VE-3,
        # and the LLM-only Bid Alternate 2.
        assert len(reconciled) == 3
        ids = [alt.alternate_id for alt in reconciled]
        # The deterministic record wins for the merged #1.
        assert "Alt #1" in ids
        # VE-3 stays distinct (VE family is separate from alternate family).
        assert "VE-3" in ids
        # And Bid Alternate 2 carries through from the LLM list.
        assert "Bid Alternate 2" in ids
        # Pin: the merged deterministic record kept its description.
        merged_one = next(a for a in reconciled if a.alternate_id == "Alt #1")
        assert "deterministic" in merged_one.description.lower()

    def test_qa_alternates_e3_zero_alternates_project_safe(self) -> None:
        """EDGE-3: a project with zero alternates exposes the rollup
        helpers without crashing and they return safe zero / empty
        defaults. Pins the "no alternates worksheet, no PDF section, no
        empty-state explosion" contract called out in the QA brief."""
        est = Estimate(project_name="QA-2 E3", line_items=[_line(total=2000.0)])
        updated = attach_alternates_to_estimate(est, _project_with_alts([]))
        assert updated.alternates == []
        assert updated.alternates_selected_default == set()
        # Helper getters return zero across every type bucket.
        assert updated.alternates_total_additive == 0.0
        assert updated.alternates_total_deductive == 0.0
        assert updated.alternates_total_substitution == 0.0
        assert updated.alternates_count_missing == 0
        # Selection helpers tolerate empty / None inputs and return base.
        assert updated.subtotal_with_alternates_selected(set()) == 2000.0
        assert updated.subtotal_with_alternates_selected(None) == 2000.0
        # And selecting non-existent ids still returns base (no KeyError).
        assert (
            updated.subtotal_with_alternates_selected({"Phantom Alt"})
            == 2000.0
        )
        # The selection delta helper is also zero for empty / unknown ids.
        assert updated.alternates_delta_for_selection({"x"}) == 0.0


# ---------------------------------------------------------------------------
# Module-level pin: cost-delta parsing utility
# ---------------------------------------------------------------------------


def test_qa_alternates_parse_cost_delta_blank_field_returns_none() -> None:
    """Pin: a printed blank fillable line ($_____) returns None — the
    extractor must NOT fabricate a $0 cost_delta when the bid form is
    asking the bidder to fill it in. Caller emits MISSING in that case."""
    assert parse_cost_delta("Alternate No. 1: Add foo $______ ADD") is None
    assert parse_cost_delta("Alternate No. 2: Add bar $1,234.56") == 1234.56
    assert parse_cost_delta("Alternate No. 3: ($1,500)") == -1500.0  # parens negative


def test_qa_alternates_classify_type_keywords() -> None:
    """Pin: classifier disambiguates VE / SUBSTITUTION / DEDUCTIVE /
    ADDITIVE keywords. VE patterns checked before DEDUCTIVE per the
    code comment ('VE = savings' wording often contains 'deduct')."""
    assert classify_alternate_type("VE proposal: substitute LVT for VCT") == (
        AlternateType.VE
    )
    assert classify_alternate_type("Deduct skylight system") == (
        AlternateType.DEDUCTIVE
    )
    assert classify_alternate_type("Substitute LVT in lieu of VCT") == (
        AlternateType.SUBSTITUTION
    )
    assert classify_alternate_type("Add epoxy floor coating") == (
        AlternateType.ADDITIVE
    )


# ---------------------------------------------------------------------------
# Pricing-basis MISSING tier pin (alternates extracted with no $ amount)
# ---------------------------------------------------------------------------


def test_qa_alternates_missing_pricing_basis_for_blank_field() -> None:
    """Pin: a bid alternate with a blank fillable line ($_______) flows
    through ``price_alternates`` with ``pricing_basis = MISSING`` and
    ``cost_delta = None``. Confidence floor enforced at ≤ 0.50."""
    page = (
        "BID ALTERNATES\n"
        "Alternate No. 5: Add epoxy paint to all toilet rooms. $______ ADD\n"
    )
    alts = extract_alternates_from_page(page)
    assert len(alts) == 1
    assert alts[0].cost_delta is None
    est = Estimate(project_name="QA-2 missing-pin", line_items=[_line(total=1000.0)])
    updated = attach_alternates_to_estimate(est, _project_with_alts(alts))
    assert len(updated.alternates) == 1
    priced = updated.alternates[0]
    assert priced.pricing_basis == AlternatePricingBasis.MISSING
    assert priced.cost_delta is None
    assert priced.confidence <= 0.50
    assert updated.alternates_count_missing == 1
