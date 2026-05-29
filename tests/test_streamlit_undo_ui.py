"""Phase T6.4.d — Streamlit per-line override-undo UI helpers.

Same pattern as ``tests/test_streamlit_override_ui.py`` (T6.2): the
heavy ``app.py`` form wiring is impractical to drive via Streamlit's
``AppTest`` harness because the analyze pipeline path requires real
PDFs / LLM calls / pricing. So the per-line undo UI is structured as
a thin Streamlit layer over pure helper functions:

* :func:`app._format_snapshot_label` — single-line "tag @ time $cost"
  label for the revert button tooltip + toast.
* :func:`app._build_revert_history_rows` — projection of a line's
  snapshot stack into UI-renderable dict rows for the
  "show full undo history" expander.
* :func:`app._apply_per_line_revert` — pure wrapper around
  :func:`core.estimator.revert_last_override_in_estimate` that the
  per-line button click handler uses.
* :func:`app._revertable_line_indices` — list of indices with
  non-empty ``override_snapshots``, used by the bulk-revert button
  and the per-line affordance loop.
* :func:`app._bulk_revert_all` — pops the most recent snapshot on
  every revertable line in one call. Backs the bulk-revert button.

The Streamlit form itself (``st.button``, ``st.columns``,
``st.dataframe``) is unit-tested transitively by the helpers; a
smoke-import of ``app.py`` (in the verification step) confirms the
form wiring parses cleanly.
"""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

import app as app_module
from app import (
    _apply_per_line_revert,
    _build_revert_history_rows,
    _bulk_revert_all,
    _format_snapshot_label,
    _revertable_line_indices,
)
from core.estimator import apply_manual_override
from core.pricing.batch_override import (
    SOURCE_TAG_VENDOR_CSV,
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    BatchOverrideRow,
    apply_batch_plan,
)
from core.schemas import (
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
        cost_source=cost_source,
        notes=notes,
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.4.d UI",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# _format_snapshot_label
# ---------------------------------------------------------------------------


def test_format_snapshot_label_full_tag_and_time() -> None:
    snap = CostLineOverrideSnapshot(
        unit_cost=4.50, qty=100.0, total_cost=450.0,
        applied_at=datetime(2026, 5, 28, 14, 32, 0, tzinfo=timezone.utc),
        source_tag="[batch]",
    )
    label = _format_snapshot_label(snap)
    assert "[batch]" in label
    assert "14:32 UTC" in label
    assert "$4.50/unit" in label


def test_format_snapshot_label_empty_tag_renders_priced_default() -> None:
    """Snapshot of a priced-from-cost-DB line has no leading tag."""
    snap = CostLineOverrideSnapshot(
        unit_cost=2.0, qty=100.0, total_cost=200.0,
        applied_at=datetime(2026, 5, 28, 14, 32, 0, tzinfo=timezone.utc),
        source_tag="",
    )
    label = _format_snapshot_label(snap)
    assert "(priced default)" in label


def test_format_snapshot_label_handles_thousand_dollar_cost() -> None:
    """High-dollar unit cost gets thousands separator."""
    snap = CostLineOverrideSnapshot(
        unit_cost=12345.67, qty=1.0, total_cost=12345.67,
        applied_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
        source_tag="[manual-override]",
    )
    label = _format_snapshot_label(snap)
    assert "$12,345.67/unit" in label


# ---------------------------------------------------------------------------
# _build_revert_history_rows
# ---------------------------------------------------------------------------


def test_build_revert_history_rows_empty_for_clean_line() -> None:
    """A line with no snapshots returns an empty list."""
    rows = _build_revert_history_rows(_line(), line_index=3)
    assert rows == []


def test_build_revert_history_rows_one_row_per_snapshot() -> None:
    """3 snapshots → 3 rows, all carrying the same line_index."""
    li = _line()
    li.override_snapshots = [
        CostLineOverrideSnapshot(
            unit_cost=2.0, qty=100.0, total_cost=200.0,
            cost_source_tier=CostSourceTier.INTERPOLATED,
            applied_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
            source_tag="",
        ),
        CostLineOverrideSnapshot(
            unit_cost=4.0, qty=100.0, total_cost=400.0,
            cost_source_tier=CostSourceTier.MANUAL_OVERRIDE,
            applied_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
            source_tag="[batch]",
        ),
        CostLineOverrideSnapshot(
            unit_cost=5.0, qty=100.0, total_cost=500.0,
            cost_source_tier=CostSourceTier.MANUAL_OVERRIDE,
            applied_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
            source_tag="[manual-override]",
        ),
    ]
    rows = _build_revert_history_rows(li, line_index=7)
    assert len(rows) == 3
    assert all(r["Line #"] == 7 for r in rows)
    # Depth tracks stack order (oldest first).
    assert [r["Depth"] for r in rows] == [0, 1, 2]
    assert rows[0]["Source tag"] == "(priced default)"
    assert rows[1]["Source tag"] == "[batch]"
    assert rows[2]["Source tag"] == "[manual-override]"


def test_build_revert_history_rows_carries_unit_and_total_cost() -> None:
    """Numeric columns round to 2dp."""
    li = _line()
    li.override_snapshots = [
        CostLineOverrideSnapshot(
            unit_cost=2.345, qty=100.0, total_cost=234.50,
            applied_at=datetime(2026, 5, 28, tzinfo=timezone.utc),
        ),
    ]
    rows = _build_revert_history_rows(li, line_index=0)
    assert rows[0]["Unit cost"] == 2.35  # rounded
    assert rows[0]["Total cost"] == 234.50


# ---------------------------------------------------------------------------
# _revertable_line_indices
# ---------------------------------------------------------------------------


def test_revertable_indices_empty_when_no_snapshots() -> None:
    est = _estimate([_line(), _line(description="x")])
    assert _revertable_line_indices(est) == []


def test_revertable_indices_includes_only_lines_with_snapshots() -> None:
    """Stable order; line indices match estimate.line_items."""
    lines = [_line(description=f"line {i}") for i in range(5)]
    est = _estimate(lines)
    after = apply_manual_override(est, 1, new_unit_cost=3.0)
    after = apply_manual_override(after, 3, new_unit_cost=4.0)
    assert _revertable_line_indices(after) == [1, 3]


def test_revertable_indices_unchanged_after_revert_until_stack_empties() -> None:
    """Apply 2 layers + revert 1 → still revertable."""
    est = _estimate([_line(unit_cost=2.0)])
    after_1 = apply_manual_override(est, 0, new_unit_cost=3.0)
    after_2 = apply_manual_override(after_1, 0, new_unit_cost=4.0)
    assert _revertable_line_indices(after_2) == [0]
    new_est, _ = _apply_per_line_revert(after_2, 0)
    assert _revertable_line_indices(new_est) == [0]
    new_est, _ = _apply_per_line_revert(new_est, 0)
    assert _revertable_line_indices(new_est) == []


# ---------------------------------------------------------------------------
# _apply_per_line_revert
# ---------------------------------------------------------------------------


def test_apply_per_line_revert_returns_estimate_and_snapshot() -> None:
    est = _estimate([_line(unit_cost=2.0)])
    after = apply_manual_override(est, 0, new_unit_cost=3.50)
    new_est, popped = _apply_per_line_revert(after, 0)
    assert popped is not None
    assert popped.unit_cost == 2.0  # pre-override state
    assert new_est.line_items[0].unit_cost == 2.0


def test_apply_per_line_revert_returns_none_for_clean_line() -> None:
    """Line with empty snapshot list → snapshot=None, estimate unchanged."""
    est = _estimate([_line(unit_cost=2.0)])
    new_est, popped = _apply_per_line_revert(est, 0)
    assert popped is None
    assert new_est is est


def test_apply_per_line_revert_does_not_mutate_input_estimate() -> None:
    """Pure functional: input unchanged after call."""
    est = _estimate([_line(unit_cost=2.0)])
    after = apply_manual_override(est, 0, new_unit_cost=3.50)
    pre_snap_count = len(after.line_items[0].override_snapshots)
    _apply_per_line_revert(after, 0)
    assert len(after.line_items[0].override_snapshots) == pre_snap_count
    assert after.line_items[0].unit_cost == 3.50


def test_apply_per_line_revert_only_touches_target_line() -> None:
    """Other lines' snapshots untouched."""
    est = _estimate([_line(description="A"), _line(description="B")])
    after = apply_manual_override(est, 0, new_unit_cost=3.0)
    after = apply_manual_override(after, 1, new_unit_cost=4.0)
    new_est, _ = _apply_per_line_revert(after, 0)
    # Line 0 reverted, line 1 untouched.
    assert new_est.line_items[0].override_snapshots == []
    assert len(new_est.line_items[1].override_snapshots) == 1


# ---------------------------------------------------------------------------
# _bulk_revert_all
# ---------------------------------------------------------------------------


def test_bulk_revert_all_pops_one_layer_per_revertable_line() -> None:
    """3 lines with 2 snapshots each → bulk revert pops 1 layer per line."""
    lines = [_line(description=f"L{i}", unit_cost=2.0) for i in range(3)]
    est = _estimate(lines)
    out = est
    for i in range(3):
        out = apply_manual_override(out, i, new_unit_cost=3.0)
        out = apply_manual_override(out, i, new_unit_cost=4.0)
    assert all(len(li.override_snapshots) == 2 for li in out.line_items)
    new_est, popped_list = _bulk_revert_all(out)
    assert len(popped_list) == 3
    # Each line has 1 snapshot left and unit_cost back to 3.0
    # (the post-first-apply, pre-second-apply state).
    for li in new_est.line_items:
        assert len(li.override_snapshots) == 1
        assert li.unit_cost == 3.0


def test_bulk_revert_all_skips_clean_lines() -> None:
    """Lines with empty snapshot list are not iterated."""
    est = _estimate([
        _line(description="A", unit_cost=2.0),
        _line(description="B", unit_cost=5.0),  # never overridden
        _line(description="C", unit_cost=8.0),
    ])
    after = apply_manual_override(est, 0, new_unit_cost=3.0)
    after = apply_manual_override(after, 2, new_unit_cost=10.0)
    new_est, popped = _bulk_revert_all(after)
    assert len(popped) == 2
    # B was never touched.
    assert new_est.line_items[1].unit_cost == 5.0
    # A and C reverted.
    assert new_est.line_items[0].unit_cost == 2.0
    assert new_est.line_items[2].unit_cost == 8.0


def test_bulk_revert_all_empty_when_no_snapshots() -> None:
    """Estimate with no override snapshots → no-op."""
    est = _estimate([_line(), _line(description="x")])
    new_est, popped = _bulk_revert_all(est)
    assert popped == []
    assert new_est is est


def test_bulk_revert_after_batch_apply() -> None:
    """The 200-row scenario: batch apply + single bulk-revert click → pre-batch state."""
    lines = [_line(description=f"Item {i}", unit_cost=2.0) for i in range(5)]
    est = _estimate(lines)
    # Build a 5-row matched plan.
    matched = [
        BatchMatchResult(
            row=BatchOverrideRow(
                row_index=i + 2,
                description=f"Item {i}",
                unit_cost=4.0,
                vendor="Acme",
                unit_of_measure="SF",
            ),
            status=BatchMatchStatus.MATCHED,
            best_match_index=i,
            best_match_similarity=1.0,
            runner_up_index=None,
            runner_up_similarity=0.0,
        )
        for i in range(5)
    ]
    plan = BatchOverridePlan(
        total_rows=5, matched=matched, ambiguous=[],
        no_match=[], low_similarity=[],
        similarity_threshold=0.65, ambiguity_margin=0.10,
    )
    after, _ = apply_batch_plan(est, plan, source_tag=SOURCE_TAG_VENDOR_CSV)
    # Every line carries a snapshot now.
    assert all(len(li.override_snapshots) == 1 for li in after.line_items)
    new_est, popped = _bulk_revert_all(after)
    assert len(popped) == 5
    # Every line is back at the original unit_cost.
    assert all(li.unit_cost == 2.0 for li in new_est.line_items)
    assert all(li.cost_source_tier == CostSourceTier.INTERPOLATED for li in new_est.line_items)
    assert all(li.notes is None for li in new_est.line_items)


# ---------------------------------------------------------------------------
# Smoke: app module exports the helpers
# ---------------------------------------------------------------------------


def test_app_module_exports_per_line_undo_helpers() -> None:
    """The Streamlit form imports these by name; a typo would crash import."""
    assert hasattr(app_module, "_format_snapshot_label")
    assert hasattr(app_module, "_build_revert_history_rows")
    assert hasattr(app_module, "_apply_per_line_revert")
    assert hasattr(app_module, "_revertable_line_indices")
    assert hasattr(app_module, "_bulk_revert_all")
