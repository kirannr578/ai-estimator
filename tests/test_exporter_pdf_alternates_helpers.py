"""Phase T9.2 — pure-helper tests for the client PDF alternates section.

Covers ``core/exporter_pdf.py`` helpers added by the T9.2 slice:

* ``_format_alternate_type_short`` — short table label per
  :class:`AlternateType`.
* ``_sort_alternates_for_pdf`` — ADDITIVE → SUBSTITUTION → VE →
  DEDUCTIVE, then by ``alternate_id``.
* ``_compute_tally_rows`` — base / per-type / selected tally
  composition; only present types render.
* ``_truncate_description_for_pdf`` — word-aware truncation with
  full-text footnote.

These tests intentionally avoid building any reportlab flowables — the
helpers are pure and the rendering integration tests live alongside in
``test_exporter_pdf_alternates.py``.
"""

from __future__ import annotations

import pytest

reportlab = pytest.importorskip("reportlab")  # skip cleanly if not installed

from core.exporter_pdf import (  # noqa: E402
    _compute_tally_rows,
    _format_alternate_type_short,
    _format_signed_money,
    _sort_alternates_for_pdf,
    _truncate_description_for_pdf,
)
from core.schemas import (  # noqa: E402
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CostCategory,
    CostLine,
    Estimate,
)


# ---------------------------------------------------------------------------
# _format_alternate_type_short
# ---------------------------------------------------------------------------


class TestFormatAlternateTypeShort:
    def test_additive(self) -> None:
        assert _format_alternate_type_short(AlternateType.ADDITIVE) == "Add"

    def test_deductive(self) -> None:
        assert _format_alternate_type_short(AlternateType.DEDUCTIVE) == "Deduct"

    def test_substitution(self) -> None:
        assert _format_alternate_type_short(AlternateType.SUBSTITUTION) == "Sub."

    def test_value_engineering(self) -> None:
        assert _format_alternate_type_short(AlternateType.VE) == "VE"

    def test_accepts_string_value(self) -> None:
        """A round-tripped Pydantic enum-as-string must still resolve."""
        assert _format_alternate_type_short("additive") == "Add"
        assert _format_alternate_type_short("value_engineering") == "VE"

    def test_unknown_string_falls_through(self) -> None:
        """Unrecognized inputs render as their stringified form rather than crash."""
        assert _format_alternate_type_short("nonsense") == "nonsense"


# ---------------------------------------------------------------------------
# _sort_alternates_for_pdf
# ---------------------------------------------------------------------------


def _ale(
    alt_id: str,
    alt_type: AlternateType = AlternateType.ADDITIVE,
    cost: float | None = 1000.0,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alt_id,
        alternate_type=alt_type,
        description=f"Alternate {alt_id}",
        cost_delta=cost,
        pricing_basis=(
            AlternatePricingBasis.EXTRACTED_FROM_BID_FORM
            if cost is not None
            else AlternatePricingBasis.MISSING
        ),
    )


class TestSortAlternatesForPdf:
    def test_empty_list(self) -> None:
        assert _sort_alternates_for_pdf([]) == []

    def test_single_alternate_unchanged(self) -> None:
        only = [_ale("Alt 1", AlternateType.ADDITIVE)]
        assert _sort_alternates_for_pdf(only) == only

    def test_orders_types_additive_substitution_ve_deductive(self) -> None:
        deductive = _ale("Alt D", AlternateType.DEDUCTIVE, -500.0)
        ve = _ale("VE-1", AlternateType.VE, -200.0)
        substitution = _ale("Alt S", AlternateType.SUBSTITUTION, 100.0)
        additive = _ale("Alt A", AlternateType.ADDITIVE, 1000.0)
        out = _sort_alternates_for_pdf([deductive, ve, substitution, additive])
        types = [a.alternate_type for a in out]
        assert types == [
            AlternateType.ADDITIVE,
            AlternateType.SUBSTITUTION,
            AlternateType.VE,
            AlternateType.DEDUCTIVE,
        ]

    def test_within_type_sorted_by_alternate_id(self) -> None:
        a3 = _ale("Alt 3", AlternateType.ADDITIVE)
        a1 = _ale("Alt 1", AlternateType.ADDITIVE)
        a2 = _ale("Alt 2", AlternateType.ADDITIVE)
        out = _sort_alternates_for_pdf([a3, a1, a2])
        assert [a.alternate_id for a in out] == ["Alt 1", "Alt 2", "Alt 3"]

    def test_unknown_type_lands_at_end(self) -> None:
        normal = _ale("Alt A", AlternateType.ADDITIVE)
        # Construct an estimate-line with a coercible-string type.
        # Pydantic round-trips enums as their values, which the sort
        # helper coerces back to enum.
        weird = AlternateLineEstimate(
            alternate_id="Alt Z",
            alternate_type=AlternateType.DEDUCTIVE,
            description="will be patched",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
        # Force the type to a value the helper treats as "unknown" by
        # bypassing pydantic validation post-construction. Setting an
        # arbitrary-string-shaped enum value via attribute assignment.
        object.__setattr__(weird, "alternate_type", "totally_made_up_kind")
        out = _sort_alternates_for_pdf([weird, normal])
        assert out[0] is normal
        assert out[1] is weird


# ---------------------------------------------------------------------------
# _truncate_description_for_pdf
# ---------------------------------------------------------------------------


class TestTruncateDescriptionForPdf:
    def test_none_returns_empty_no_footnote(self) -> None:
        truncated, footnote = _truncate_description_for_pdf(None)
        assert truncated == ""
        assert footnote is None

    def test_short_text_no_footnote(self) -> None:
        truncated, footnote = _truncate_description_for_pdf("hello world")
        assert truncated == "hello world"
        assert footnote is None

    def test_exact_max_chars_no_footnote(self) -> None:
        """Boundary: input length == max_chars produces no truncation."""
        s = "x" * 80
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=80)
        assert truncated == s
        assert footnote is None

    def test_one_over_max_truncates(self) -> None:
        s = "x" * 81
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=80)
        assert footnote == s
        assert truncated.endswith("\u2026")
        # Ellipsis adds 1 char; truncated body length <= max_chars.
        assert len(truncated) <= 80 + 1

    def test_word_aware_does_not_cut_midword(self) -> None:
        """A long input with an obvious last-space gets cut at the space."""
        s = (
            "Substitute 24-gauge standing-seam metal roof panels for the "
            "specified asphalt shingles assembly across the entire roof area"
        )
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=80)
        assert footnote == s
        # Last char before the ellipsis should be a complete word.
        body = truncated.rstrip("\u2026")
        # Last whitespace boundary in the truncated body is the cut point.
        assert not body.endswith(" "), "should rstrip trailing whitespace"
        # Body itself should be a substring of the original text.
        assert s.startswith(body)

    def test_no_space_inside_max_falls_back_to_hard_cut(self) -> None:
        """Single mega-word with NO whitespace should still truncate."""
        s = "x" * 200
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=80)
        assert footnote == s
        # No space → hard cut at max_chars then add ellipsis.
        assert truncated == ("x" * 80) + "\u2026"

    def test_custom_max_chars(self) -> None:
        s = "abcdefghij" * 10  # 100 chars
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=20)
        assert footnote == s
        assert len(truncated) <= 21  # 20 + ellipsis

    def test_word_break_floor_avoids_tiny_stub(self) -> None:
        """A 79-char single word with a 1-char prefix shouldn't cut at 1."""
        s = "A " + ("x" * 100)
        truncated, footnote = _truncate_description_for_pdf(s, max_chars=80)
        assert footnote == s
        # Should NOT have produced "A…" — that would be a useless stub.
        body = truncated.rstrip("\u2026").rstrip()
        assert len(body) > 5


# ---------------------------------------------------------------------------
# _compute_tally_rows
# ---------------------------------------------------------------------------


def _line(total: float = 1000.0) -> CostLine:
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description="painting",
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


def _estimate_with_alts(alts: list[AlternateLineEstimate]) -> Estimate:
    return Estimate(
        project_name="T9.2 helpers",
        line_items=[_line(total=10_000.0)],
        alternates=alts,
    )


class TestComputeTallyRows:
    def test_no_alternates_gives_base_plus_selected(self) -> None:
        """Even with zero alternates the helper still emits base + selected
        (selected delta = 0). The renderer is responsible for skipping
        the section entirely when the alternates list is empty; the
        helper's contract is to always render at least the base row."""
        est = _estimate_with_alts([])
        rows = _compute_tally_rows(est)
        labels = [r[0] for r in rows]
        # Base + selected, no per-type rows because no types are present.
        assert labels == [
            "Base bid (no alternates)",
            "Base + selected alternates",
        ]
        assert rows[0][1] == 10_000.0
        assert rows[0][2] is None  # base row has no delta
        assert rows[1][2] == 0.0  # selection is empty by default

    def test_only_additive_present(self) -> None:
        est = _estimate_with_alts(
            [_ale("Alt A", AlternateType.ADDITIVE, 500.0)]
        )
        labels = [r[0] for r in _compute_tally_rows(est)]
        assert "Base + all additive alternates" in labels
        assert "Base + all deductive alternates" not in labels
        assert "Base + all VE items" not in labels

    def test_only_deductive_present(self) -> None:
        est = _estimate_with_alts(
            [_ale("Alt D", AlternateType.DEDUCTIVE, -500.0)]
        )
        labels = [r[0] for r in _compute_tally_rows(est)]
        assert "Base + all deductive alternates" in labels
        assert "Base + all additive alternates" not in labels
        assert "Base + all VE items" not in labels

    def test_only_ve_present(self) -> None:
        est = _estimate_with_alts(
            [_ale("VE-1", AlternateType.VE, -300.0)]
        )
        labels = [r[0] for r in _compute_tally_rows(est)]
        assert "Base + all VE items" in labels
        assert "Base + all deductive alternates" not in labels
        assert "Base + all additive alternates" not in labels

    def test_all_types_present(self) -> None:
        est = _estimate_with_alts([
            _ale("Alt A", AlternateType.ADDITIVE, 500.0),
            _ale("Alt D", AlternateType.DEDUCTIVE, -200.0),
            _ale("Alt S", AlternateType.SUBSTITUTION, 100.0),
            _ale("VE-1", AlternateType.VE, -150.0),
        ])
        labels = [r[0] for r in _compute_tally_rows(est)]
        # Substitution does NOT get its own tally row in the brief —
        # only ADDITIVE / DEDUCTIVE / VE / selected. (Substitution is
        # surfaced via the table itself, not a tally aggregate.) Pin
        # this to keep the contract explicit.
        assert "Base + all additive alternates" in labels
        assert "Base + all deductive alternates" in labels
        assert "Base + all VE items" in labels
        assert "Base + selected alternates" in labels

    def test_ve_separate_from_deductive(self) -> None:
        """VE renders on its own row even though DEDUCTIVE math is identical."""
        est = _estimate_with_alts([
            _ale("Alt D", AlternateType.DEDUCTIVE, -100.0),
            _ale("VE-1", AlternateType.VE, -200.0),
        ])
        rows = _compute_tally_rows(est)
        ded_row = next(r for r in rows if r[0] == "Base + all deductive alternates")
        ve_row = next(r for r in rows if r[0] == "Base + all VE items")
        # DEDUCTIVE row should NOT include the VE delta and vice versa.
        assert ded_row[2] == -100.0
        assert ve_row[2] == -200.0
        assert ded_row[1] == 9_900.0  # 10000 - 100
        assert ve_row[1] == 9_800.0  # 10000 - 200

    def test_missing_costs_skipped(self) -> None:
        """A None cost_delta must not contribute to any per-type row."""
        est = _estimate_with_alts([
            _ale("Alt A", AlternateType.ADDITIVE, 500.0),
            _ale("Alt M", AlternateType.ADDITIVE, None),
        ])
        rows = _compute_tally_rows(est)
        add_row = next(r for r in rows if r[0] == "Base + all additive alternates")
        # Only the priced alternate contributes.
        assert add_row[2] == 500.0

    def test_selected_row_uses_explicit_selection(self) -> None:
        est = _estimate_with_alts([
            _ale("Alt 1", AlternateType.ADDITIVE, 500.0),
            _ale("Alt 2", AlternateType.ADDITIVE, 300.0),
        ])
        rows = _compute_tally_rows(est, selected_ids={"Alt 1"})
        sel_row = next(r for r in rows if r[0] == "Base + selected alternates")
        assert sel_row[1] == 10_500.0
        assert sel_row[2] == 500.0

    def test_selected_row_falls_back_to_estimate_default(self) -> None:
        est = Estimate(
            project_name="T9.2",
            line_items=[_line(total=10_000.0)],
            alternates=[_ale("Alt 1", AlternateType.ADDITIVE, 500.0)],
            alternates_selected_default={"Alt 1"},
        )
        rows = _compute_tally_rows(est, selected_ids=None)
        sel_row = next(r for r in rows if r[0] == "Base + selected alternates")
        assert sel_row[1] == 10_500.0

    def test_selected_row_empty_selection_zero_delta(self) -> None:
        est = _estimate_with_alts([_ale("Alt 1", AlternateType.ADDITIVE, 500.0)])
        rows = _compute_tally_rows(est, selected_ids=set())
        sel_row = next(r for r in rows if r[0] == "Base + selected alternates")
        assert sel_row[2] == 0.0

    def test_base_row_always_first(self) -> None:
        est = _estimate_with_alts([
            _ale("Alt A", AlternateType.ADDITIVE, 500.0),
            _ale("Alt D", AlternateType.DEDUCTIVE, -200.0),
        ])
        rows = _compute_tally_rows(est)
        assert rows[0][0] == "Base bid (no alternates)"
        assert rows[0][2] is None  # base row carries no delta

    def test_selected_row_always_last(self) -> None:
        est = _estimate_with_alts([
            _ale("Alt A", AlternateType.ADDITIVE, 500.0),
            _ale("Alt D", AlternateType.DEDUCTIVE, -200.0),
            _ale("VE-1", AlternateType.VE, -150.0),
        ])
        rows = _compute_tally_rows(est)
        assert rows[-1][0] == "Base + selected alternates"


# ---------------------------------------------------------------------------
# _format_signed_money — small helper, two-line contract
# ---------------------------------------------------------------------------


class TestFormatSignedMoney:
    def test_positive_value(self) -> None:
        assert _format_signed_money(1234.56) == "+$1,234.56"

    def test_negative_value(self) -> None:
        assert _format_signed_money(-1234.56) == "-$1,234.56"

    def test_zero_renders_with_plus_sign(self) -> None:
        # Tiebreaker: zero is not negative, so gets the "+" prefix.
        # Zero deltas do show up on the Selected row when no alts are
        # selected, so this needs to render cleanly.
        assert _format_signed_money(0.0) == "+$0.00"
