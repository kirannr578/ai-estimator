"""Phase T6.4.b — unit-aware matching tests.

The T6.3 batch-override matcher worked off description text alone, which
allowed silently-wrong cross-UoM matches: a "$45/LF" vendor row could
land on a "$95/SF" cost line, double-billing the project. T6.4.b adds
unit-of-measure normalisation, an explicit compatibility relation, and
an ``enforce_uom_compatibility`` matcher kwarg (default ``True``) that
rejects unsafe matches before they reach :func:`apply_batch_plan`.

Bucketed:

* **normalize_uom** (11 tests) — case / whitespace / punctuation /
  alias coverage of every UoM family in :data:`UOM_CANONICAL`, plus the
  ``None`` / empty / unknown branches.
* **uoms_compatible** (10 tests) — the ``None`` defensive convention,
  same-canonical, every published compat group, and the strict
  cross-dimension rejection (LF/SF, LF/CY, LB/LF).
* **match_cost_lines (enforce=True default)** (8 tests) — same-UoM
  match, cross-UoM rejection, AMBIGUOUS → MATCHED via UoM filter,
  defensive ``None`` on either side, compat-group acceptance, and the
  ``unit mismatch:`` warning string format on the rejection path.
* **match_cost_lines (enforce=False)** (3 tests) — pre-T6.4.b
  description-only behaviour preserved, with the new
  :attr:`BatchMatchResult.uom_mismatch_warning` populated when the
  matcher would otherwise have rejected the match.
* **apply_batch_plan integration** (3 tests) — enforce=True path leaves
  the cost line untouched; enforce=False path stamps the line *and*
  carries the warning into the operator note. Backwards-compat
  signature pin (no kwarg = safe behaviour).

All call sites that worked pre-T6.4.b keep working — every test that
calls :func:`match_cost_lines` without the kwarg either has compatible
UoMs or has no UoM info on the row, both of which the safe default
allows.
"""

from __future__ import annotations

import pytest

from core.pricing.batch_override import (
    UOM_CANONICAL,
    UOM_COMPATIBILITY_GROUPS,
    BatchMatchStatus,
    BatchOverrideRow,
    apply_batch_plan,
    match_cost_lines,
    normalize_uom,
    uoms_compatible,
)
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


def _line(
    *,
    description: str = "Interior latex paint walls",
    csi_division: str = "09",
    csi_section: str = "09 91 23",
    quantity: float = 100.0,
    unit: str = "SF",
    unit_cost: float = 2.0,
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
        confidence=0.92,
        price_confidence=0.65,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        suppressed=False,
        cost_source="cwicr:42",
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.4.b unit-aware",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# normalize_uom
# ---------------------------------------------------------------------------


def test_normalize_uom_canonical_passthrough() -> None:
    assert normalize_uom("LF") == "LF"


def test_normalize_uom_lowercase_input() -> None:
    assert normalize_uom("lf") == "LF"


def test_normalize_uom_strips_whitespace() -> None:
    assert normalize_uom(" lf ") == "LF"


def test_normalize_uom_length_alias() -> None:
    assert normalize_uom("linear ft") == "LF"
    assert normalize_uom("LIN FT") == "LF"


def test_normalize_uom_area_alias() -> None:
    assert normalize_uom("square feet") == "SF"
    assert normalize_uom("sq ft") == "SF"
    assert normalize_uom("sqft") == "SF"


def test_normalize_uom_strips_punctuation() -> None:
    # Operators paste "sq. ft." / "cu. yd." liberally — the matcher
    # must collapse those to the canonical form.
    assert normalize_uom("sq. ft.") == "SF"
    assert normalize_uom("cu. yd.") == "CY"


def test_normalize_uom_volume_alias() -> None:
    assert normalize_uom("cubic yards") == "CY"
    assert normalize_uom("cu yd") == "CY"


def test_normalize_uom_weight_alias() -> None:
    assert normalize_uom("pounds") == "LB"
    assert normalize_uom("tons") == "TON"


def test_normalize_uom_count_alias() -> None:
    assert normalize_uom("each") == "EA"
    assert normalize_uom("lump sum") == "LS"


def test_normalize_uom_time_alias() -> None:
    assert normalize_uom("hours") == "HR"
    assert normalize_uom("month") == "MO"


def test_normalize_uom_returns_none_for_empty_or_unknown() -> None:
    assert normalize_uom(None) is None
    assert normalize_uom("") is None
    assert normalize_uom("   ") is None
    assert normalize_uom("xyz") is None


def test_normalize_uom_canonical_map_is_non_empty() -> None:
    # Pin a healthy variant count — protects against accidental
    # truncation of the map during refactors.
    assert len(UOM_CANONICAL) >= 50


# ---------------------------------------------------------------------------
# uoms_compatible
# ---------------------------------------------------------------------------


def test_uoms_compatible_both_none_is_true() -> None:
    # Defensive: no UoM info at all → fall back to description match.
    assert uoms_compatible(None, None) is True


def test_uoms_compatible_one_none_is_true() -> None:
    # Defensive: only one side knows → trust the description match.
    assert uoms_compatible("LF", None) is True
    assert uoms_compatible(None, "SF") is True


def test_uoms_compatible_same_canonical_is_true() -> None:
    assert uoms_compatible("LF", "LF") is True
    assert uoms_compatible("SF", "SF") is True


def test_uoms_compatible_same_canonical_via_alias() -> None:
    # Both sides normalise to the same canonical → compatible.
    assert uoms_compatible("linear ft", "LF") is True
    assert uoms_compatible("sq ft", "square feet") is True


def test_uoms_compatible_lf_vs_sf_is_false() -> None:
    # The whole reason this phase exists.
    assert uoms_compatible("LF", "SF") is False


def test_uoms_compatible_lb_vs_lf_is_false() -> None:
    assert uoms_compatible("LB", "LF") is False


def test_uoms_compatible_cy_vs_cf_is_false() -> None:
    # Volume-units differ even though both are "cubic" — without an
    # explicit conversion the matcher must reject.
    assert uoms_compatible("CY", "CF") is False


def test_uoms_compatible_ls_lot_compat_group() -> None:
    # Lump-sum and lot are interchangeable in published practice.
    assert uoms_compatible("LS", "LOT") is True
    assert uoms_compatible("LOT", "LS") is True


def test_uoms_compatible_ea_set_compat_group() -> None:
    assert uoms_compatible("EA", "SET") is True
    assert uoms_compatible("SET", "EA") is True


def test_uoms_compatible_unknown_uom_is_treated_as_none() -> None:
    # An unrecognisable string normalises to None and falls through to
    # the defensive ``None`` branch (one None → True).
    assert uoms_compatible("xyz", "LF") is True
    assert uoms_compatible("LF", "qrs") is True


def test_uoms_compatible_groups_are_published() -> None:
    # Pin the compat group surface so a reviewer can see which UoMs are
    # treated as interchangeable today.
    flat = [g for g in UOM_COMPATIBILITY_GROUPS]
    assert {"LS", "LOT"} in flat
    assert {"EA", "SET"} in flat


# ---------------------------------------------------------------------------
# match_cost_lines — enforce_uom_compatibility=True (default)
# ---------------------------------------------------------------------------


def test_enforce_default_lf_row_vs_lf_line_matches() -> None:
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="LF")]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1
    assert plan.matched[0].uom_mismatch_warning is None


def test_enforce_default_lf_row_vs_sf_line_lands_no_match() -> None:
    # The bug T6.4.b fixes: pre-T6.4.b this matched. Now it must land
    # in NO_MATCH because the UoM filter strips the only candidate.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="SF")]
    plan = match_cost_lines(rows, lines)
    assert plan.matched == []
    assert len(plan.no_match) == 1
    result = plan.no_match[0]
    # Explicit warning explaining *why* the match was rejected.
    assert result.uom_mismatch_warning is not None
    assert "LF" in result.uom_mismatch_warning
    assert "SF" in result.uom_mismatch_warning
    assert "unit mismatch" in result.uom_mismatch_warning.lower()


def test_enforce_default_ambiguous_collapses_to_match_via_uom_filter() -> None:
    # Two near-identical descriptions → AMBIGUOUS pre-T6.4.b. With UoM
    # enforcement, the SF candidate is filtered out and the LF row
    # matches the LF line cleanly.
    rows = [BatchOverrideRow(
        2, "Interior trim", 12.0, unit_of_measure="LF",
    )]
    lines = [
        _line(description="Interior trim", unit="SF"),
        _line(description="Interior trim", unit="LF",
              csi_section="06 22 13"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1
    assert plan.matched[0].best_match_index == 1


def test_enforce_default_ls_row_matches_lot_line_via_compat_group() -> None:
    rows = [BatchOverrideRow(
        2, "Site mobilization", 5000.0, unit_of_measure="LS",
    )]
    lines = [_line(
        description="Site mobilization", unit="LOT",
        csi_section="01 50 00", unit_cost=4500.0,
    )]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1


def test_enforce_default_no_uom_on_row_still_matches() -> None:
    # Row has no UoM (None). The defensive convention keeps the match.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure=None,
    )]
    lines = [_line(description="Stainless guardrail", unit="LF")]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1


def test_enforce_default_no_uom_on_line_still_matches() -> None:
    # Cost line has empty unit. Treated as None → defensive match.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="")]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1


def test_enforce_default_unknown_uom_on_row_still_matches() -> None:
    # Row UoM is gibberish → normalises to None → defensive match.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="qrx",
    )]
    lines = [_line(description="Stainless guardrail", unit="LF")]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1


def test_enforce_default_warning_string_format() -> None:
    # Pin the rejection-message format so operators / log scrapers can
    # rely on it. Format: "unit mismatch: row=<X> vs line=<Y>".
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="SF")]
    plan = match_cost_lines(rows, lines)
    msg = plan.no_match[0].uom_mismatch_warning
    assert msg is not None
    assert msg.startswith("unit mismatch:")
    assert "row=LF" in msg
    assert "line=SF" in msg


# ---------------------------------------------------------------------------
# match_cost_lines — enforce_uom_compatibility=False (safety-off)
# ---------------------------------------------------------------------------


def test_enforce_off_lf_row_vs_sf_line_matches_with_warning() -> None:
    # With the safety off, the matcher returns the description-only
    # match — but flags it via uom_mismatch_warning so operators can
    # see at a glance that something is fishy.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="SF")]
    plan = match_cost_lines(rows, lines, enforce_uom_compatibility=False)
    assert len(plan.matched) == 1
    result = plan.matched[0]
    assert result.uom_mismatch_warning is not None
    assert "LF" in result.uom_mismatch_warning
    assert "SF" in result.uom_mismatch_warning


def test_enforce_off_compatible_match_has_no_warning() -> None:
    # When everything aligns, the safety-off path is byte-identical to
    # pre-T6.4.b: no warning, plain MATCHED.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="LF")]
    plan = match_cost_lines(rows, lines, enforce_uom_compatibility=False)
    assert len(plan.matched) == 1
    assert plan.matched[0].uom_mismatch_warning is None


def test_enforce_off_no_uom_on_row_has_no_warning() -> None:
    # No UoM on row → defensive convention says "compatible" → no
    # warning even with the safety off.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure=None,
    )]
    lines = [_line(description="Stainless guardrail", unit="SF")]
    plan = match_cost_lines(rows, lines, enforce_uom_compatibility=False)
    assert len(plan.matched) == 1
    assert plan.matched[0].uom_mismatch_warning is None


# ---------------------------------------------------------------------------
# apply_batch_plan — integration with the new safety
# ---------------------------------------------------------------------------


def test_apply_enforce_default_skips_uom_mismatched_line() -> None:
    # The cross-UoM row is rejected at match time → apply leaves the
    # line untouched. This is the whole point of the phase.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(
        description="Stainless guardrail", unit="SF", unit_cost=95.0,
    )]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    new_est, summary = apply_batch_plan(est, plan)
    assert new_est.line_items[0].unit_cost == pytest.approx(95.0)
    assert new_est.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED
    # And the operator-facing summary mentions it.
    assert any("no match" in s.lower() or "no_match" in s.lower()
               for s in summary)


def test_apply_enforce_off_stamps_line_and_carries_warning() -> None:
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(
        description="Stainless guardrail", unit="SF", unit_cost=95.0,
    )]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines, enforce_uom_compatibility=False)
    new_est, _ = apply_batch_plan(est, plan)
    line = new_est.line_items[0]
    assert line.unit_cost == pytest.approx(45.0)
    assert line.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    # The warning rides along in the operator note so it survives any
    # downstream PDF / CSV export.
    notes = line.notes or ""
    assert "unit mismatch" in notes.lower()
    assert "LF" in notes
    assert "SF" in notes


def test_match_cost_lines_default_kwarg_is_safe() -> None:
    # Backwards-compat pin: every pre-T6.4.b call site that omitted the
    # new kwarg automatically gets the safer behaviour. Same call as
    # T6.3 / T6.4.c → cross-UoM is now NO_MATCH.
    rows = [BatchOverrideRow(
        2, "Stainless guardrail", 45.0, unit_of_measure="LF",
    )]
    lines = [_line(description="Stainless guardrail", unit="SF")]
    plan = match_cost_lines(rows, lines)
    assert plan.matched == []
    assert len(plan.no_match) == 1
