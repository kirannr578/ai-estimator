"""Phase T9.0 — bid-form alternates extraction tests.

Covers the deterministic regex parser, page detection, type
classification, cost-delta parsing, multi-alternate / multi-page
pages, the LLM-fallback predicate + wiring, and confidence scoring.
"""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from core.extraction.bid_form_alternates import (
    classify_alternate_type,
    detect_alternates_section,
    extract_alternates_from_page,
    extract_alternates_from_pages,
    parse_cost_delta,
    reconcile_alternate_sources,
    should_invoke_llm_fallback,
    _normalize_id_for_dedupe,
)
from core.schemas import AlternateLine, AlternateType


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


class TestDetectAlternatesSection:
    def test_detects_bid_alternate_header(self) -> None:
        text = "Section 5: BID ALTERNATES\nAlternate No. 1: Add epoxy floor"
        assert detect_alternates_section(text) is True

    def test_detects_add_alternate_header(self) -> None:
        assert detect_alternates_section("ADD ALTERNATE PRICING\n...") is True

    def test_detects_deduct_alternate_header(self) -> None:
        assert detect_alternates_section("DEDUCT ALTERNATE pricing schedule") is True

    def test_detects_alternate_no_prefix(self) -> None:
        assert detect_alternates_section("Alternate No. 1: foo bar") is True

    def test_detects_alternate_hash_prefix(self) -> None:
        assert detect_alternates_section("Alternate #2: substitute LVT") is True

    def test_detects_value_engineering_header(self) -> None:
        assert detect_alternates_section("VALUE ENGINEERING PROPOSALS\n") is True

    def test_detects_ve_item_label(self) -> None:
        assert detect_alternates_section("VE Item 3: save $12,000") is True

    def test_detects_substitution_alternate(self) -> None:
        assert detect_alternates_section("SUBSTITUTION ALTERNATE table") is True

    def test_returns_false_on_plain_text(self) -> None:
        assert detect_alternates_section("This is just the base bid schedule.") is False

    def test_returns_false_on_empty_text(self) -> None:
        assert detect_alternates_section("") is False

    def test_returns_false_on_none_safely(self) -> None:
        # The function tolerates falsy input without raising.
        assert detect_alternates_section(None) is False  # type: ignore[arg-type]

    def test_detection_is_case_insensitive(self) -> None:
        assert detect_alternates_section("alternate no. 5: foo") is True
        assert detect_alternates_section("AlTeRnAtE nO. 5: foo") is True


# ---------------------------------------------------------------------------
# Type classification
# ---------------------------------------------------------------------------


class TestClassifyAlternateType:
    def test_classifies_additive(self) -> None:
        assert classify_alternate_type("ADD epoxy coating to mech rooms") == AlternateType.ADDITIVE

    def test_classifies_deductive_via_deduct(self) -> None:
        assert classify_alternate_type("DEDUCT skylight system") == AlternateType.DEDUCTIVE

    def test_classifies_deductive_via_omit(self) -> None:
        assert classify_alternate_type("OMIT exterior tile cladding") == AlternateType.DEDUCTIVE

    def test_classifies_substitution(self) -> None:
        assert classify_alternate_type("SUBSTITUTE LVT for VCT") == AlternateType.SUBSTITUTION

    def test_classifies_substitution_via_in_lieu_of(self) -> None:
        assert classify_alternate_type("in lieu of carpet, use polished concrete") == AlternateType.SUBSTITUTION

    def test_classifies_ve(self) -> None:
        assert classify_alternate_type("VALUE ENGINEERING proposal: switch HVAC vendor") == AlternateType.VE

    def test_classifies_ve_item(self) -> None:
        assert classify_alternate_type("VE Item 4: alternate roof membrane") == AlternateType.VE

    def test_falls_back_to_additive_on_unknown(self) -> None:
        assert classify_alternate_type("xyzzy plugh") == AlternateType.ADDITIVE

    def test_empty_input_returns_additive(self) -> None:
        assert classify_alternate_type("") == AlternateType.ADDITIVE


# ---------------------------------------------------------------------------
# Cost-delta parsing
# ---------------------------------------------------------------------------


class TestParseCostDelta:
    def test_parses_simple_dollar_amount(self) -> None:
        assert parse_cost_delta("Add this for $1234") == 1234.0

    def test_parses_amount_with_commas(self) -> None:
        assert parse_cost_delta("$1,234,567.89 ADD") == 1234567.89

    def test_parses_amount_without_dollar_sign(self) -> None:
        assert parse_cost_delta("Pricing: 12,500 USD") == 12500.0

    def test_parses_parenthesized_negative(self) -> None:
        # Accounting convention: parens → negative.
        assert parse_cost_delta("($5,000)") == -5000.0

    def test_returns_none_on_blank_field(self) -> None:
        # $______ is the printed-fillable pattern.
        assert parse_cost_delta("Total: $______ ADD") is None
        assert parse_cost_delta("Cost: $___") is None

    def test_returns_none_on_no_match(self) -> None:
        assert parse_cost_delta("no dollar amount here") is None

    def test_returns_none_on_empty(self) -> None:
        assert parse_cost_delta("") is None

    def test_parses_decimal_amount(self) -> None:
        assert parse_cost_delta("$12.50") == 12.50

    def test_handles_whitespace_inside(self) -> None:
        assert parse_cost_delta("$ 1,234") == 1234.0


# ---------------------------------------------------------------------------
# Single-line parsing
# ---------------------------------------------------------------------------


class TestExtractAlternatesFromPage:
    def test_extracts_alternate_no_prefix(self) -> None:
        text = "Alternate No. 1: Add epoxy floor coating to mechanical rooms — $5,000 ADD"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].alternate_id == "Alternate 1"
        assert alts[0].alternate_type == AlternateType.ADDITIVE
        assert alts[0].cost_delta == 5000.0
        assert "epoxy" in alts[0].description.lower()

    def test_extracts_alternate_hash_prefix_with_paren_deduct(self) -> None:
        text = "Alternate #2 (DEDUCT): Omit skylight system — $7,500"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.DEDUCTIVE
        # DEDUCTIVE convention: cost_delta is signed negative.
        assert alts[0].cost_delta == -7500.0

    def test_extracts_bid_alternate_letter(self) -> None:
        text = "Bid Alternate A: Substitute LVT flooring for VCT in corridors. Net delta: $2,300"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.SUBSTITUTION
        assert alts[0].cost_delta == 2300.0

    def test_extracts_add_alternate_prefix(self) -> None:
        text = "Add Alternate 2: Provide additional epoxy at toilet rooms — $1,250"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.ADDITIVE
        assert alts[0].cost_delta == 1250.0
        # Add Alternate id is preserved as a separate family.
        assert "Alternate 2" in alts[0].alternate_id or "Add Alternate 2" in alts[0].alternate_id

    def test_extracts_ve_item(self) -> None:
        text = "VE Item 3: Substitute alternate roofing membrane, save $12,000"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.VE
        # VE convention: cost_delta is signed negative (savings).
        assert alts[0].cost_delta == -12000.0
        assert alts[0].alternate_id.startswith("VE")

    def test_extracts_blank_amount_as_none(self) -> None:
        text = "Alternate No. 4: Add interior signage package — $_____ ADD"
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert alts[0].cost_delta is None

    def test_returns_empty_on_no_alternates(self) -> None:
        assert extract_alternates_from_page("This is just narrative scope text.") == []

    def test_returns_empty_on_empty_input(self) -> None:
        assert extract_alternates_from_page("") == []

    def test_extracts_multiple_alternates_on_one_page(self) -> None:
        text = (
            "Section 5 — BID ALTERNATES\n"
            "Alternate No. 1: Add epoxy floor coating — $5,000 ADD\n"
            "Alternate No. 2: Deduct skylight system — $7,500 DEDUCT\n"
            "Alternate No. 3: Substitute LVT for VCT — $2,300\n"
        )
        alts = extract_alternates_from_page(text)
        assert len(alts) == 3
        types = [a.alternate_type for a in alts]
        assert AlternateType.ADDITIVE in types
        assert AlternateType.DEDUCTIVE in types
        # Type-keyword precedence: "substitute" wins over implicit ADD.
        assert AlternateType.SUBSTITUTION in types

    def test_folds_continuation_line_into_description(self) -> None:
        text = (
            "Alternate No. 1: Provide additional epoxy floor coating throughout\n"
            "mechanical rooms 101, 102, and 103 — $5,000 ADD\n"
        )
        alts = extract_alternates_from_page(text)
        assert len(alts) == 1
        assert "mechanical rooms" in alts[0].description.lower()
        assert alts[0].cost_delta == 5000.0

    def test_stops_folding_at_next_alternate_header(self) -> None:
        text = (
            "Alternate No. 1: Add epoxy floor coating — $5,000\n"
            "Alternate No. 2: Deduct skylight — $7,500\n"
        )
        alts = extract_alternates_from_page(text)
        assert len(alts) == 2
        assert alts[0].cost_delta == 5000.0
        assert alts[1].cost_delta == -7500.0

    def test_carries_bid_package_and_source_sheet(self) -> None:
        text = "Alternate No. 1: Add epoxy — $5,000 ADD"
        alts = extract_alternates_from_page(
            text,
            bid_package_id="bidform.pdf",
            source_sheet="Bid Form p.3",
        )
        assert alts[0].bid_package_id == "bidform.pdf"
        assert alts[0].source_sheet == "Bid Form p.3"

    def test_scope_summary_truncated_to_160_chars(self) -> None:
        long = "x" * 300
        text = f"Alternate No. 1: {long} — $1,000 ADD"
        alts = extract_alternates_from_page(text)
        assert alts[0].scope_summary is not None
        assert len(alts[0].scope_summary) <= 160


# ---------------------------------------------------------------------------
# Multi-page extraction
# ---------------------------------------------------------------------------


class TestExtractAlternatesFromPages:
    def test_aggregates_across_pages(self) -> None:
        pages = [
            "Base bid schedule:\n line 1\n line 2",  # no alternates
            "BID ALTERNATES\nAlternate No. 1: Add foo — $1,000",
            "Continued ALTERNATES\nAlternate No. 2: Deduct bar — $2,000",
        ]
        alts = extract_alternates_from_pages(pages)
        assert len(alts) == 2

    def test_skips_pages_without_alternates(self) -> None:
        pages = ["random text", "Alternate No. 1: Add foo — $500"]
        alts = extract_alternates_from_pages(pages)
        assert len(alts) == 1

    def test_source_sheet_template_substitution(self) -> None:
        pages = ["Alternate No. 1: Add foo — $500"]
        alts = extract_alternates_from_pages(
            pages, source_sheet_template="Bid Form p.{page}"
        )
        assert alts[0].source_sheet == "Bid Form p.1"

    def test_handles_empty_pages_list(self) -> None:
        assert extract_alternates_from_pages([]) == []


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


class TestConfidenceScoring:
    def test_high_confidence_clean_parse(self) -> None:
        text = "Alternate No. 1: Add epoxy floor coating to mechanical rooms — $5,000 ADD"
        alts = extract_alternates_from_page(text)
        assert alts[0].confidence >= 0.85

    def test_low_confidence_no_amount(self) -> None:
        text = "Alternate No. 1: Add scope X"
        alts = extract_alternates_from_page(text)
        # Floor 0.55 + body_chars >= 25 (no — too short) + no cost: low.
        assert alts[0].confidence <= 0.75

    def test_confidence_floor_at_0_55(self) -> None:
        text = "Alternate No. 1: x"
        alts = extract_alternates_from_page(text)
        assert alts[0].confidence >= 0.55


# ---------------------------------------------------------------------------
# Reconciliation
# ---------------------------------------------------------------------------


class TestReconcileAlternateSources:
    def _alt(self, alt_id: str, *, cost: float | None = None, conf: float = 0.85) -> AlternateLine:
        return AlternateLine(
            alternate_id=alt_id,
            alternate_type=AlternateType.ADDITIVE,
            description=f"desc for {alt_id}",
            cost_delta=cost,
            confidence=conf,
        )

    def test_deterministic_only_passes_through(self) -> None:
        det = [self._alt("Alternate 1", cost=1000.0), self._alt("Alternate 2", cost=2000.0)]
        merged = reconcile_alternate_sources(det, [])
        assert len(merged) == 2
        assert {m.alternate_id for m in merged} == {"Alternate 1", "Alternate 2"}

    def test_llm_only_passes_through(self) -> None:
        llm = [self._alt("Alternate 5", cost=500.0)]
        merged = reconcile_alternate_sources([], llm)
        assert len(merged) == 1
        assert merged[0].alternate_id == "Alternate 5"

    def test_same_id_dedupes_to_higher_completeness(self) -> None:
        det = [self._alt("Alternate 1", cost=None)]   # no cost → score 4
        llm = [self._alt("Alternate 1", cost=1000.0)]  # cost set → score 6
        merged = reconcile_alternate_sources(det, llm)
        assert len(merged) == 1
        # LLM record wins because it has cost_delta populated.
        assert merged[0].cost_delta == 1000.0

    def test_tie_breaks_favour_deterministic(self) -> None:
        det = [self._alt("Alternate 1", cost=1000.0)]
        llm = [self._alt("Alternate 1", cost=999.0)]
        merged = reconcile_alternate_sources(det, llm)
        assert len(merged) == 1
        # Same score: deterministic wins (no replace).
        assert merged[0].cost_delta == 1000.0

    def test_normalize_id_collapses_variants(self) -> None:
        # Same alternate emitted in different "shape" variants:
        assert _normalize_id_for_dedupe("Alt #1") == _normalize_id_for_dedupe("Alternate No. 1")
        assert _normalize_id_for_dedupe("Alt #1") == _normalize_id_for_dedupe("Alternate 1")


# ---------------------------------------------------------------------------
# LLM-fallback predicate + wiring
# ---------------------------------------------------------------------------


class TestLLMFallbackPredicate:
    def test_fallback_triggers_when_detection_says_yes_and_parser_empty(self) -> None:
        text = "BID ALTERNATES section header here but no parseable lines"
        assert should_invoke_llm_fallback(text, []) is True

    def test_fallback_skipped_when_parser_non_empty(self) -> None:
        text = "Alternate No. 1: Add foo — $500"
        det_result = extract_alternates_from_page(text)
        assert det_result  # parser got something
        assert should_invoke_llm_fallback(text, det_result) is False

    def test_fallback_skipped_when_no_alternates_section(self) -> None:
        assert should_invoke_llm_fallback("totally unrelated text", []) is False


class TestExtractAlternatesViaLLM:
    """LLM-fallback wiring test (uses a mock LLM client)."""

    def test_llm_fallback_emits_alternate_lines(self) -> None:
        from core.extractors import extract_alternates_via_llm

        mock_llm = MagicMock()
        mock_resp = MagicMock()
        mock_resp.parsed = {
            "alternates": [
                {
                    "number": "1",
                    "description": "Add epoxy floor coating to mechanical rooms",
                    "add_or_deduct": "Add",
                    "amount": 5000.0,
                }
            ]
        }
        mock_llm.analyze_text.return_value = mock_resp

        page_text = "BID ALTERNATES section with unusual layout the regex missed"
        alts = extract_alternates_via_llm(
            page_text,
            mock_llm,
            bid_package_id="bidform.pdf",
            source_sheet="Bid Form p.3",
        )
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.ADDITIVE
        assert alts[0].cost_delta == 5000.0
        assert alts[0].bid_package_id == "bidform.pdf"
        # Confidence is capped at 0.70 because LLM-fallback path runs only
        # on unusual layouts that the regex couldn't parse.
        assert alts[0].confidence <= 0.70

    def test_llm_fallback_returns_empty_on_short_text(self) -> None:
        from core.extractors import extract_alternates_via_llm

        mock_llm = MagicMock()
        # Should not even reach the LLM call.
        result = extract_alternates_via_llm("short", mock_llm)
        assert result == []
        mock_llm.analyze_text.assert_not_called()

    def test_llm_fallback_returns_empty_on_llm_error(self) -> None:
        from core.extractors import extract_alternates_via_llm

        mock_llm = MagicMock()
        mock_llm.analyze_text.side_effect = RuntimeError("api down")

        result = extract_alternates_via_llm("a" * 100, mock_llm)
        assert result == []

    def test_llm_fallback_handles_deduct_label_sign(self) -> None:
        from core.extractors import extract_alternates_via_llm

        mock_llm = MagicMock()
        mock_resp = MagicMock()
        mock_resp.parsed = {
            "alternates": [
                {
                    "number": "2",
                    "description": "Omit skylight system",
                    "add_or_deduct": "Deduct",
                    "amount": 7500.0,
                }
            ]
        }
        mock_llm.analyze_text.return_value = mock_resp

        alts = extract_alternates_via_llm("a" * 100, mock_llm)
        assert len(alts) == 1
        assert alts[0].alternate_type == AlternateType.DEDUCTIVE
        # Sign convention: DEDUCTIVE → negative cost_delta.
        assert alts[0].cost_delta == -7500.0


# ---------------------------------------------------------------------------
# Combined / regression
# ---------------------------------------------------------------------------


def test_full_bid_form_alternates_section_end_to_end() -> None:
    """A realistic federal-RFP-style alternates section."""
    text = """
    SECTION 5 — BID ALTERNATES

    Alternate No. 1: Add epoxy floor coating to all mechanical rooms,
    rooms 101 through 105.
                                                          $______ ADD

    Alternate No. 2 (DEDUCT): Omit the skylight system in the lobby
    atrium. Provide bituminous roofing in lieu.
                                                          $______ DEDUCT

    Alternate No. 3: Substitute LVT flooring (Spec 09 65 19) for VCT
    in corridors.
                                                          $2,300

    VE Item 1: Alternate roofing membrane TPO 60mil in lieu of PVC.
    Savings: $12,500.
    """
    alts = extract_alternates_from_page(text)
    assert len(alts) == 4
    types = [a.alternate_type for a in alts]
    assert AlternateType.ADDITIVE in types
    assert AlternateType.DEDUCTIVE in types
    assert AlternateType.SUBSTITUTION in types
    assert AlternateType.VE in types

    # Blank fields → None cost_delta.
    alt1 = next(a for a in alts if "epoxy" in a.description.lower())
    assert alt1.cost_delta is None

    alt3 = next(a for a in alts if "lvt" in a.description.lower())
    assert alt3.cost_delta == 2300.0

    ve = next(a for a in alts if a.alternate_type == AlternateType.VE)
    assert ve.cost_delta is not None
    assert ve.cost_delta < 0  # VE: savings → negative
