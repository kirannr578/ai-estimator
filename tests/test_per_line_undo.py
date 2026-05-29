"""Phase T6.4.d — per-line override undo via snapshot store.

Covers the new ``CostLineOverrideSnapshot`` schema, the
``_capture_line_snapshot`` / ``revert_last_override`` /
``revert_last_override_in_estimate`` primitives in
``core.estimator``, and the snapshot capture wired into every
override path:

* T6.1 ``apply_manual_override`` (single-line manual override)
* T6.3 ``apply_batch_plan`` (vendor CSV / xlsx batch apply)
* T8.1 / T8.2 ``apply_subquote_plan`` (sub-quote PDF apply)

Why a snapshot store and not parsing the ``| previous: ...``
suffix? The notes string is human-readable and does not preserve
actual numeric values (``unit_cost`` / ``qty`` / ``total_cost`` /
``price_confidence`` / ``cost_band``); a notes-only undo would be
lossy. The brief acknowledged this and recommended Option A
(snapshot store) over Option C (notes parse). These tests pin
that contract.

Key invariants:

* Snapshot capture is bounded at :data:`MAX_OVERRIDE_SNAPSHOTS`
  (10 entries / line, FIFO drop) so a pathological re-apply loop
  can't grow memory without bound.
* Default empty list keeps every pre-T6.4.d estimate
  backwards-compatible (those lines simply have nothing to revert).
* ``apply_manual_override`` is the SHARED snapshot-capture point —
  batch / sub-quote both flow through this primitive so they get
  snapshots for free.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from core.estimator import (
    _capture_line_snapshot,
    _extract_leading_source_tag,
    apply_manual_override,
    revert_last_override,
    revert_last_override_in_estimate,
)
from core.pricing.batch_override import (
    SOURCE_TAG_BATCH,
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    BatchOverrideRow,
    apply_batch_plan,
)
from core.pricing.subquote_parser import apply_subquote_plan
from core.schemas import (
    MAX_OVERRIDE_SNAPSHOTS,
    CostBand,
    CostCategory,
    CostLine,
    CostLineOverrideSnapshot,
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
        project_name="T6.4.d per-line undo",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _matched_plan_for(
    *,
    line_index: int,
    description: str,
    unit_cost: float,
    csv_row: int = 2,
    vendor: str | None = "Acme",
    quote_ref: str | None = "Q-99",
    unit_of_measure: str | None = "SF",
) -> BatchOverridePlan:
    """Return a 1-row :class:`BatchOverridePlan` that auto-matches one line."""
    row = BatchOverrideRow(
        row_index=csv_row,
        description=description,
        unit_cost=unit_cost,
        vendor=vendor,
        quote_ref=quote_ref,
        unit_of_measure=unit_of_measure,
    )
    result = BatchMatchResult(
        row=row,
        status=BatchMatchStatus.MATCHED,
        best_match_index=line_index,
        best_match_similarity=1.0,
        runner_up_index=None,
        runner_up_similarity=0.0,
        candidate_lines=[(line_index, 1.0)],
    )
    return BatchOverridePlan(
        total_rows=1,
        matched=[result],
        ambiguous=[],
        no_match=[],
        low_similarity=[],
        similarity_threshold=0.65,
        ambiguity_margin=0.10,
    )


# ---------------------------------------------------------------------------
# Schema sanity
# ---------------------------------------------------------------------------


def test_cap_constant_is_ten() -> None:
    """Cap is pinned at 10 — calibration intent: typical chain depth 1-3."""
    assert MAX_OVERRIDE_SNAPSHOTS == 10


def test_costline_default_override_snapshots_is_empty_list() -> None:
    """Backwards-compat: every pre-T6.4.d CostLine has empty stack."""
    li = _line()
    assert li.override_snapshots == []
    # Must be a fresh list per instance (not a shared default mutable).
    li2 = _line()
    assert li.override_snapshots is not li2.override_snapshots


def test_snapshot_model_round_trips_through_model_dump() -> None:
    """Snapshot survives JSON serialization for save / load."""
    snap = CostLineOverrideSnapshot(
        unit_cost=3.50, qty=100.0, total_cost=350.0,
        notes="[batch] operator override: [unit_cost: $3.50]",
        cost_source_tier=CostSourceTier.INTERPOLATED,
        price_confidence=0.65, combined_confidence=0.598,
        cost_band=CostBand.OPERATOR_REVIEW, suppressed=False,
        applied_at=datetime(2026, 5, 28, 14, 32, 0, tzinfo=timezone.utc),
        source_tag="[batch]",
    )
    dumped = snap.model_dump()
    restored = CostLineOverrideSnapshot.model_validate(dumped)
    assert restored.unit_cost == snap.unit_cost
    assert restored.notes == snap.notes
    assert restored.source_tag == "[batch]"
    assert restored.cost_band == CostBand.OPERATOR_REVIEW


def test_costline_with_snapshots_round_trips() -> None:
    """CostLine serialises + restores with non-empty override_snapshots."""
    snap = CostLineOverrideSnapshot(
        unit_cost=2.0, qty=100.0, total_cost=200.0,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        price_confidence=0.65, combined_confidence=0.598,
        cost_band=CostBand.OPERATOR_REVIEW,
        applied_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )
    li = _line()
    li.override_snapshots = [snap]
    dumped = li.model_dump()
    restored = CostLine.model_validate(dumped)
    assert len(restored.override_snapshots) == 1
    assert restored.override_snapshots[0].unit_cost == 2.0


# ---------------------------------------------------------------------------
# _extract_leading_source_tag
# ---------------------------------------------------------------------------


def test_extract_tag_returns_empty_for_none_or_empty() -> None:
    assert _extract_leading_source_tag(None) == ""
    assert _extract_leading_source_tag("") == ""


def test_extract_tag_handles_each_canonical_tag() -> None:
    cases = {
        "[batch] operator override: foo": "[batch]",
        "[vendor-csv] operator override: foo": "[vendor-csv]",
        "[sub-quote] operator override: foo": "[sub-quote]",
        "[sub-quote-llm] operator override: foo": "[sub-quote-llm]",
        "[manual-override] operator override: foo": "[manual-override]",
    }
    for notes, expected in cases.items():
        assert _extract_leading_source_tag(notes) == expected


def test_extract_tag_returns_empty_when_no_leading_bracket() -> None:
    """Pre-T6.4.c notes (no source tag) → empty string."""
    assert _extract_leading_source_tag("operator override: foo") == ""
    assert _extract_leading_source_tag("Some narrative line") == ""


# ---------------------------------------------------------------------------
# _capture_line_snapshot
# ---------------------------------------------------------------------------


def test_capture_line_snapshot_records_all_fields() -> None:
    """Snapshot captures every field needed for byte-identical restore."""
    li = _line(
        unit_cost=4.50, quantity=120.0,
        price_confidence=0.65,
        tier=CostSourceTier.INTERPOLATED,
        band=CostBand.OPERATOR_REVIEW,
        notes="[batch] operator override: [unit_cost: $4.50]",
    )
    snap = _capture_line_snapshot(li)
    assert snap.unit_cost == 4.50
    assert snap.qty == 120.0
    assert snap.total_cost == round(4.50 * 120.0, 2)
    assert snap.notes == "[batch] operator override: [unit_cost: $4.50]"
    assert snap.cost_source_tier == CostSourceTier.INTERPOLATED
    assert snap.price_confidence == 0.65
    assert snap.combined_confidence == pytest.approx(0.92 * 0.65, abs=1e-3)
    assert snap.cost_band == CostBand.OPERATOR_REVIEW
    assert snap.suppressed is False
    assert snap.source_tag == "[batch]"


def test_capture_line_snapshot_uses_now_utc_when_applied_at_omitted() -> None:
    """Default ``applied_at`` is current UTC time within ~5s window."""
    li = _line()
    before = datetime.now(timezone.utc)
    snap = _capture_line_snapshot(li)
    after = datetime.now(timezone.utc)
    assert before - timedelta(seconds=2) <= snap.applied_at <= after + timedelta(seconds=2)
    # tzinfo must be set (UTC) so cross-timezone reload doesn't shift.
    assert snap.applied_at.tzinfo is not None


def test_capture_line_snapshot_accepts_explicit_applied_at() -> None:
    """Test injection: caller passes a fixed timestamp for deterministic tests."""
    fixed = datetime(2026, 5, 28, 14, 32, 0, tzinfo=timezone.utc)
    snap = _capture_line_snapshot(_line(), applied_at=fixed)
    assert snap.applied_at == fixed


def test_capture_snapshot_preserves_priced_default_source_tag_empty() -> None:
    """A fresh priced-from-cost-DB line has no leading tag → source_tag=''."""
    li = _line(notes=None)
    snap = _capture_line_snapshot(li)
    assert snap.source_tag == ""


def test_capture_snapshot_handles_suppressed_line() -> None:
    """suppressed flag is captured for restoration."""
    li = _line(suppressed=True, band=CostBand.HAND_TAKEOFF)
    snap = _capture_line_snapshot(li)
    assert snap.suppressed is True
    assert snap.cost_band == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# apply_manual_override snapshot integration
# ---------------------------------------------------------------------------


def test_apply_manual_override_captures_snapshot() -> None:
    """Single override appends one snapshot before mutation."""
    est = _estimate([_line(unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    assert len(out.line_items[0].override_snapshots) == 1
    snap = out.line_items[0].override_snapshots[0]
    assert snap.unit_cost == 2.0  # PRE-mutation
    assert snap.cost_source_tier == CostSourceTier.INTERPOLATED


def test_apply_manual_override_does_not_mutate_input() -> None:
    """Input estimate is untouched (immutable contract preserved)."""
    est = _estimate([_line()])
    pre_snapshot_count = len(est.line_items[0].override_snapshots)
    apply_manual_override(est, 0, new_unit_cost=3.50)
    assert len(est.line_items[0].override_snapshots) == pre_snapshot_count


def test_apply_manual_override_then_revert_byte_identical_state() -> None:
    """Apply + revert returns the line to its exact pre-override fields."""
    original_line = _line(
        unit_cost=2.0, quantity=100.0,
        price_confidence=0.65,
        tier=CostSourceTier.INTERPOLATED,
        band=CostBand.OPERATOR_REVIEW,
    )
    est = _estimate([original_line])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    reverted, popped = revert_last_override_in_estimate(out, 0)
    li = reverted.line_items[0]
    assert li.unit_cost == 2.0
    assert li.total_cost == 200.0
    assert li.cost_source_tier == CostSourceTier.INTERPOLATED
    assert li.price_confidence == 0.65
    assert li.cost_band == CostBand.OPERATOR_REVIEW
    assert li.suppressed is False
    assert li.notes is None
    assert popped is not None


def test_reapply_after_revert_grows_snapshot_list_again() -> None:
    """Round-trip: apply → revert → apply → snapshot list has 1 entry again."""
    est = _estimate([_line(unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    reverted, _ = revert_last_override_in_estimate(out, 0)
    assert len(reverted.line_items[0].override_snapshots) == 0
    re_applied = apply_manual_override(reverted, 0, new_unit_cost=4.00)
    assert len(re_applied.line_items[0].override_snapshots) == 1
    assert re_applied.line_items[0].unit_cost == 4.00


def test_repeat_apply_grows_snapshot_stack() -> None:
    """Each apply adds one snapshot; stack grows linearly."""
    est = _estimate([_line(unit_cost=2.0)])
    out = est
    for new_uc in (3.0, 4.0, 5.0):
        out = apply_manual_override(out, 0, new_unit_cost=new_uc)
    assert len(out.line_items[0].override_snapshots) == 3
    assert out.line_items[0].unit_cost == 5.0


def test_snapshot_stack_capped_at_max_with_fifo_drop() -> None:
    """Cap at 10; older snapshots drop FIFO; pathological loop bounded."""
    est = _estimate([_line(unit_cost=1.0)])
    out = est
    # Apply 15 distinct overrides — first 5 should drop.
    for i in range(15):
        out = apply_manual_override(out, 0, new_unit_cost=float(i + 2))
    snaps = out.line_items[0].override_snapshots
    assert len(snaps) == MAX_OVERRIDE_SNAPSHOTS == 10
    # First retained snapshot's pre-state is the unit_cost AFTER the
    # 5th apply (i.e. 6.0 — overrides set unit_cost to 2..16, so post-5th
    # = 6.0, captured as pre-6th = 6.0 input for the 6th apply).
    # Verify the oldest retained snap holds the 6th apply's pre-state.
    assert snaps[0].unit_cost == 6.0
    # Most-recent snap's pre-state is the unit_cost after the 14th apply (=15.0).
    assert snaps[-1].unit_cost == 15.0


# ---------------------------------------------------------------------------
# revert_last_override
# ---------------------------------------------------------------------------


def test_revert_empty_returns_none_no_mutation() -> None:
    """Line with empty stack → returns None; line untouched."""
    li = _line(unit_cost=2.0)
    pre_uc = li.unit_cost
    popped = revert_last_override(li)
    assert popped is None
    assert li.unit_cost == pre_uc
    assert li.override_snapshots == []


def test_revert_single_snapshot_pops_and_restores() -> None:
    """Single revert: stack empties; line at pre-override state."""
    est = _estimate([_line(unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    line_copy = out.line_items[0].model_copy(deep=True)
    popped = revert_last_override(line_copy)
    assert popped is not None
    assert line_copy.unit_cost == 2.0
    assert line_copy.override_snapshots == []


def test_revert_multi_layer_pops_one_layer() -> None:
    """Multi-layer chain: first revert restores stack-top only."""
    est = _estimate([_line(unit_cost=2.0)])
    layer1 = apply_manual_override(est, 0, new_unit_cost=3.0)
    layer2 = apply_manual_override(layer1, 0, new_unit_cost=4.0)
    layer3 = apply_manual_override(layer2, 0, new_unit_cost=5.0)
    assert len(layer3.line_items[0].override_snapshots) == 3
    r1, _ = revert_last_override_in_estimate(layer3, 0)
    assert r1.line_items[0].unit_cost == 4.0
    assert len(r1.line_items[0].override_snapshots) == 2
    r2, _ = revert_last_override_in_estimate(r1, 0)
    assert r2.line_items[0].unit_cost == 3.0
    assert len(r2.line_items[0].override_snapshots) == 1
    r3, _ = revert_last_override_in_estimate(r2, 0)
    assert r3.line_items[0].unit_cost == 2.0
    assert len(r3.line_items[0].override_snapshots) == 0


def test_revert_returned_snapshot_carries_popped_values() -> None:
    """Returned snapshot is exactly the popped one."""
    est = _estimate([_line(unit_cost=2.0)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    captured = out.line_items[0].override_snapshots[-1]
    _, popped = revert_last_override_in_estimate(out, 0)
    assert popped is not None
    assert popped.unit_cost == captured.unit_cost
    assert popped.total_cost == captured.total_cost
    assert popped.notes == captured.notes
    assert popped.cost_source_tier == captured.cost_source_tier


def test_revert_restores_each_field_exactly() -> None:
    """All snapshotted fields restore exactly."""
    line = _line(
        unit_cost=2.0, quantity=100.0,
        confidence=0.85, price_confidence=0.65,
        tier=CostSourceTier.CATEGORY_MATCH,
        band=CostBand.OPERATOR_REVIEW,
        suppressed=False,
    )
    est = _estimate([line])
    after = apply_manual_override(est, 0, new_unit_cost=4.00)
    reverted, _ = revert_last_override_in_estimate(after, 0)
    li = reverted.line_items[0]
    assert li.unit_cost == 2.0
    assert li.quantity == 100.0
    assert li.total_cost == 200.0
    assert li.notes is None
    assert li.cost_source_tier == CostSourceTier.CATEGORY_MATCH
    assert li.price_confidence == 0.65
    assert li.cost_band == CostBand.OPERATOR_REVIEW
    assert li.suppressed is False


def test_revert_in_estimate_does_not_mutate_input() -> None:
    """Estimate-level wrapper preserves the immutable contract."""
    est = _estimate([_line(unit_cost=2.0)])
    after = apply_manual_override(est, 0, new_unit_cost=3.50)
    after_pre_snapshots = len(after.line_items[0].override_snapshots)
    revert_last_override_in_estimate(after, 0)
    # Input ``after`` unchanged.
    assert len(after.line_items[0].override_snapshots) == after_pre_snapshots
    assert after.line_items[0].unit_cost == 3.50


def test_revert_in_estimate_returns_input_when_empty() -> None:
    """Estimate-level wrapper: empty stack → returns same estimate + None."""
    est = _estimate([_line(unit_cost=2.0)])
    new_est, popped = revert_last_override_in_estimate(est, 0)
    assert popped is None
    assert new_est is est


def test_revert_in_estimate_resolves_line_id_by_string() -> None:
    """``line_id`` matching reuses _resolve_override_index — by description works."""
    est = _estimate([_line(description="Painting", unit_cost=2.0)])
    after = apply_manual_override(est, 0, new_unit_cost=3.50)
    reverted, popped = revert_last_override_in_estimate(after, "Painting")
    assert popped is not None
    assert reverted.line_items[0].unit_cost == 2.0


# ---------------------------------------------------------------------------
# apply_batch_plan snapshot integration
# ---------------------------------------------------------------------------


def test_apply_batch_plan_captures_snapshot_per_matched_line() -> None:
    """Each MATCHED row's targeted line gets one snapshot."""
    lines = [
        _line(description="Painting walls", unit_cost=2.0),
        _line(description="Carpet flooring", unit_cost=5.0),
        _line(description="Drywall installation", unit_cost=1.5),
    ]
    est = _estimate(lines)

    rows = [
        BatchOverrideRow(row_index=2, description="Painting walls",
                         unit_cost=4.0, vendor="Acme", unit_of_measure="SF"),
        BatchOverrideRow(row_index=3, description="Carpet flooring",
                         unit_cost=8.0, vendor="Acme", unit_of_measure="SF"),
    ]
    matched_results = [
        BatchMatchResult(
            row=rows[0], status=BatchMatchStatus.MATCHED,
            best_match_index=0, best_match_similarity=1.0,
            runner_up_index=None, runner_up_similarity=0.0,
        ),
        BatchMatchResult(
            row=rows[1], status=BatchMatchStatus.MATCHED,
            best_match_index=1, best_match_similarity=1.0,
            runner_up_index=None, runner_up_similarity=0.0,
        ),
    ]
    plan = BatchOverridePlan(
        total_rows=2, matched=matched_results,
        ambiguous=[], no_match=[], low_similarity=[],
        similarity_threshold=0.65, ambiguity_margin=0.10,
    )
    out, _ = apply_batch_plan(est, plan)
    assert len(out.line_items[0].override_snapshots) == 1
    assert len(out.line_items[1].override_snapshots) == 1
    # Untouched line has no snapshot.
    assert out.line_items[2].override_snapshots == []


def test_apply_batch_plan_no_snapshot_for_no_match_rows() -> None:
    """NO_MATCH rows never mutate any line → no snapshot anywhere."""
    est = _estimate([_line(description="Painting walls")])
    nomatch_row = BatchOverrideRow(
        row_index=2, description="Completely unrelated thing", unit_cost=99.0,
    )
    nomatch_result = BatchMatchResult(
        row=nomatch_row, status=BatchMatchStatus.NO_MATCH,
        best_match_index=None, best_match_similarity=0.0,
        runner_up_index=None, runner_up_similarity=0.0,
    )
    plan = BatchOverridePlan(
        total_rows=1, matched=[], ambiguous=[],
        no_match=[nomatch_result], low_similarity=[],
        similarity_threshold=0.65, ambiguity_margin=0.10,
    )
    out, _ = apply_batch_plan(est, plan)
    assert out.line_items[0].override_snapshots == []


def test_apply_batch_plan_no_snapshot_for_ambiguous_rows_unresolved() -> None:
    """AMBIGUOUS without operator resolution → skipped → no snapshot."""
    est = _estimate([
        _line(description="Painting walls"),
        _line(description="Painting ceiling"),
    ])
    ambig_row = BatchOverrideRow(
        row_index=2, description="Painting", unit_cost=4.0,
    )
    ambig_result = BatchMatchResult(
        row=ambig_row, status=BatchMatchStatus.AMBIGUOUS,
        best_match_index=0, best_match_similarity=0.85,
        runner_up_index=1, runner_up_similarity=0.84,
    )
    plan = BatchOverridePlan(
        total_rows=1, matched=[], ambiguous=[ambig_result],
        no_match=[], low_similarity=[],
        similarity_threshold=0.65, ambiguity_margin=0.10,
    )
    out, _ = apply_batch_plan(est, plan)
    assert out.line_items[0].override_snapshots == []
    assert out.line_items[1].override_snapshots == []


def test_apply_batch_plan_revert_restores_pre_batch_state() -> None:
    """Apply batch → revert → state byte-identical to pre-apply."""
    line = _line(description="Painting", unit_cost=2.0)
    est = _estimate([line])
    plan = _matched_plan_for(line_index=0, description="Painting", unit_cost=4.0)
    after, _ = apply_batch_plan(est, plan, source_tag=SOURCE_TAG_VENDOR_CSV)
    reverted, popped = revert_last_override_in_estimate(after, 0)
    li = reverted.line_items[0]
    assert li.unit_cost == 2.0
    assert li.cost_source_tier == CostSourceTier.INTERPOLATED
    assert li.notes is None
    assert popped is not None
    # Snapshot's source_tag is the PRE-batch state's leading tag — empty
    # (line was at priced-from-cost-DB defaults).
    assert popped.source_tag == ""


def test_bulk_re_apply_grows_snapshot_layer() -> None:
    """Apply same plan twice → 2 snapshots → revert once → state matches first apply."""
    line = _line(description="Painting", unit_cost=2.0)
    est = _estimate([line])
    plan = _matched_plan_for(line_index=0, description="Painting", unit_cost=4.0)
    after_1, _ = apply_batch_plan(est, plan, source_tag=SOURCE_TAG_VENDOR_CSV)
    after_2, _ = apply_batch_plan(after_1, plan, source_tag=SOURCE_TAG_VENDOR_CSV)
    assert len(after_2.line_items[0].override_snapshots) == 2
    reverted, popped = revert_last_override_in_estimate(after_2, 0)
    # After 1 revert: state matches post-first-apply (unit_cost=4.0).
    assert reverted.line_items[0].unit_cost == 4.0
    assert len(reverted.line_items[0].override_snapshots) == 1


# ---------------------------------------------------------------------------
# apply_subquote_plan snapshot integration
# ---------------------------------------------------------------------------


def test_apply_subquote_plan_tabular_captures_snapshot() -> None:
    """T8.1 sub-quote PDF tabular path snapshots correctly with [sub-quote] tag."""
    line = _line(description="HVAC ductwork", unit_cost=10.0)
    est = _estimate([line])
    plan = _matched_plan_for(
        line_index=0, description="HVAC ductwork", unit_cost=15.0,
    )
    after, _ = apply_subquote_plan(est, plan, llm=False)
    assert len(after.line_items[0].override_snapshots) == 1
    assert after.line_items[0].notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR)


def test_apply_subquote_plan_llm_captures_snapshot() -> None:
    """T8.2 sub-quote PDF LLM-vision path snapshots correctly with [sub-quote-llm]."""
    line = _line(description="HVAC ductwork", unit_cost=10.0)
    est = _estimate([line])
    plan = _matched_plan_for(
        line_index=0, description="HVAC ductwork", unit_cost=15.0,
    )
    after, _ = apply_subquote_plan(est, plan, llm=True)
    assert len(after.line_items[0].override_snapshots) == 1
    assert after.line_items[0].notes.startswith(SOURCE_TAG_SUBQUOTE_LLM)


def test_subquote_over_batch_chain_snapshot_carries_pre_batch_tag() -> None:
    """Snapshot's source_tag reflects the layer being buried, not the new one."""
    line = _line(description="HVAC ductwork", unit_cost=10.0)
    est = _estimate([line])
    # Layer 1: vendor CSV apply.
    plan1 = _matched_plan_for(line_index=0, description="HVAC ductwork", unit_cost=12.0)
    after_csv, _ = apply_batch_plan(est, plan1, source_tag=SOURCE_TAG_VENDOR_CSV)
    # Layer 2: sub-quote PDF apply on top of the CSV-tagged line.
    plan2 = _matched_plan_for(line_index=0, description="HVAC ductwork", unit_cost=15.0)
    after_subquote, _ = apply_subquote_plan(after_csv, plan2, llm=False)
    snaps = after_subquote.line_items[0].override_snapshots
    assert len(snaps) == 2
    # First snapshot (oldest) — pre-batch state, no tag.
    assert snaps[0].source_tag == ""
    # Second snapshot — pre-subquote state, vendor-csv tag at head.
    assert snaps[1].source_tag == SOURCE_TAG_VENDOR_CSV


# ---------------------------------------------------------------------------
# End-to-end multi-layer scenarios
# ---------------------------------------------------------------------------


def test_e2e_batch_then_manual_then_two_reverts_returns_to_pre_batch() -> None:
    """Apply batch + manual + revert + revert → pre-batch state."""
    line = _line(description="Painting", unit_cost=2.0)
    est = _estimate([line])
    plan = _matched_plan_for(line_index=0, description="Painting", unit_cost=4.0)
    after_batch, _ = apply_batch_plan(est, plan)
    after_manual = apply_manual_override(after_batch, 0, new_unit_cost=5.0)
    r1, _ = revert_last_override_in_estimate(after_manual, 0)
    assert r1.line_items[0].unit_cost == 4.0  # post-batch, pre-manual
    r2, _ = revert_last_override_in_estimate(r1, 0)
    assert r2.line_items[0].unit_cost == 2.0  # cost-DB defaults
    assert r2.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED
    assert r2.line_items[0].notes is None


def test_e2e_total_cost_recomputes_after_revert() -> None:
    """Aggregate (subtotal) reflects reverted line's total."""
    line = _line(description="Painting", unit_cost=2.0, quantity=100.0)
    est = _estimate([line])
    after = apply_manual_override(est, 0, new_unit_cost=10.0)
    assert after.line_items[0].total_cost == 1000.0
    # Subtotal computed off headline lines including the override.
    pre_revert_subtotal = after.subtotal
    reverted, _ = revert_last_override_in_estimate(after, 0)
    assert reverted.line_items[0].total_cost == 200.0
    assert reverted.subtotal != pre_revert_subtotal
    assert reverted.subtotal == round(200.0, 2)


def test_e2e_aggregate_count_by_tier_recomputes_after_revert() -> None:
    """count_by_tier reflects post-revert state — manual_override count drops."""
    line = _line(unit_cost=2.0, tier=CostSourceTier.INTERPOLATED)
    est = _estimate([line])
    after = apply_manual_override(est, 0, new_unit_cost=4.0)
    assert after.count_by_tier[CostSourceTier.MANUAL_OVERRIDE] == 1
    assert after.count_by_tier[CostSourceTier.INTERPOLATED] == 0
    reverted, _ = revert_last_override_in_estimate(after, 0)
    assert reverted.count_by_tier[CostSourceTier.MANUAL_OVERRIDE] == 0
    assert reverted.count_by_tier[CostSourceTier.INTERPOLATED] == 1


# ---------------------------------------------------------------------------
# Backwards compatibility
# ---------------------------------------------------------------------------


def test_estimate_loaded_without_override_snapshots_field_works() -> None:
    """Estimate JSON missing override_snapshots field deserialises fine."""
    # Simulate a pre-T6.4.d JSON dump by hand-building a CostLine dict
    # without override_snapshots and validating.
    raw_line = {
        "csi_division": "09",
        "csi_section": "09 91 23",
        "description": "Pre-T6.4.d painting",
        "quantity": 100.0,
        "unit": "SF",
        "unit_cost": 2.0,
        "total_cost": 200.0,
    }
    line = CostLine.model_validate(raw_line)
    assert line.override_snapshots == []
    # Revert on a no-snapshot line returns None — feature unavailable
    # (graceful) rather than crashing.
    popped = revert_last_override(line)
    assert popped is None
    assert line.unit_cost == 2.0  # unchanged


def test_pre_t64d_estimate_can_still_apply_override_and_revert_normally() -> None:
    """Pre-T6.4.d estimate loaded from JSON can apply + revert with full snapshot semantics."""
    raw_line = {
        "csi_division": "09", "csi_section": "09 91 23",
        "description": "x", "quantity": 50.0, "unit": "SF",
        "unit_cost": 3.0, "total_cost": 150.0,
    }
    line = CostLine.model_validate(raw_line)
    est = _estimate([line])
    after = apply_manual_override(est, 0, new_unit_cost=5.0)
    assert len(after.line_items[0].override_snapshots) == 1
    reverted, popped = revert_last_override_in_estimate(after, 0)
    assert popped is not None
    assert reverted.line_items[0].unit_cost == 3.0
