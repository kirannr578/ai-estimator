"""Phase T6.3 — `app.py` batch-override UI helper tests.

Two helpers added to ``app.py`` by Phase T6.3:

* :func:`app._summarize_batch_plan` — aggregates a
  :class:`~core.pricing.batch_override.BatchOverridePlan` into UI-friendly
  counts + total adjustment estimate.
* :func:`app._format_batch_csv_for_history` — turns applied
  :class:`~core.pricing.batch_override.BatchMatchResult` records into a
  CSV body with ``[batch]``-prefixed operator notes, compatible with the
  T6.2 override-history CSV format.

Streamlit-free; all interesting code paths are exercised through the
pure helpers. The Streamlit form wiring is covered by the smoke
``import app`` check in the verification step.
"""

from __future__ import annotations

import csv
import io

import pytest

from app import _format_batch_csv_for_history, _summarize_batch_plan
from core.pricing.batch_override import (
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    BatchOverrideRow,
    match_cost_lines,
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
    description: str = "Interior latex paint walls",
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
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.3 batch UI",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _empty_plan() -> BatchOverridePlan:
    return BatchOverridePlan(
        total_rows=0,
        matched=[],
        ambiguous=[],
        no_match=[],
        low_similarity=[],
        similarity_threshold=0.65,
        ambiguity_margin=0.10,
    )


# ---------------------------------------------------------------------------
# _summarize_batch_plan
# ---------------------------------------------------------------------------


def test_summarize_empty_plan_returns_all_zero_counts() -> None:
    summary = _summarize_batch_plan(_empty_plan())
    assert summary["total_rows"] == 0
    assert summary["matched_count"] == 0
    assert summary["ambiguous_count"] == 0
    assert summary["no_match_count"] == 0
    assert summary["low_similarity_count"] == 0
    assert summary["estimated_total_adjustment"] == 0.0


def test_summarize_aggregates_each_bucket_correctly() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 3.0),
        BatchOverrideRow(3, "Interior latex paint", 4.0),
        BatchOverrideRow(4, "qrx pqw mnop zzy", 9.0),
    ]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
        _line(description="Interior latex paint ceiling", unit_cost=2.5),
    ]
    plan = match_cost_lines(rows, lines)
    summary = _summarize_batch_plan(plan)
    assert summary["total_rows"] == 3
    assert summary["matched_count"] == len(plan.matched)
    assert summary["ambiguous_count"] == len(plan.ambiguous)
    assert summary["no_match_count"] == len(plan.no_match)
    assert summary["low_similarity_count"] == len(plan.low_similarity)
    bucket_sum = (
        summary["matched_count"] + summary["ambiguous_count"]
        + summary["no_match_count"] + summary["low_similarity_count"]
    )
    assert bucket_sum == summary["total_rows"]


def test_summarize_total_adjustment_for_all_matched() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 5.0),
        BatchOverrideRow(3, "Slab on grade 3000psi", 10.0),
    ]
    lines = [
        _line(description="Interior latex paint walls",
              quantity=100.0, unit_cost=2.0),       # 200 → 500, +300
        _line(description="Slab on grade 3000psi",
              csi_section="03 30 00",
              quantity=50.0, unit_cost=8.0),         # 400 → 500, +100
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    summary = _summarize_batch_plan(plan, est)
    assert summary["estimated_total_adjustment"] == pytest.approx(400.0)


def test_summarize_total_adjustment_skips_unmatched_rows() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 5.0),
        BatchOverrideRow(3, "qrx pqw mnop zzy", 999.0),
    ]
    lines = [
        _line(description="Interior latex paint walls",
              quantity=100.0, unit_cost=2.0),  # only this matches → +300
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    summary = _summarize_batch_plan(plan, est)
    assert summary["estimated_total_adjustment"] == pytest.approx(300.0)


def test_summarize_no_estimate_returns_zero_adjustment() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 5.0)]
    lines = [
        _line(description="Interior latex paint walls",
              quantity=100.0, unit_cost=2.0),
    ]
    plan = match_cost_lines(rows, lines)
    summary = _summarize_batch_plan(plan)
    # No estimate passed → adjustment defaults to 0.0
    assert summary["estimated_total_adjustment"] == 0.0


def test_summarize_echoes_threshold_and_margin() -> None:
    plan = BatchOverridePlan(
        total_rows=0, matched=[], ambiguous=[],
        no_match=[], low_similarity=[],
        similarity_threshold=0.77,
        ambiguity_margin=0.22,
    )
    summary = _summarize_batch_plan(plan)
    assert summary["similarity_threshold"] == pytest.approx(0.77)
    assert summary["ambiguity_margin"] == pytest.approx(0.22)


def test_summarize_negative_adjustment_when_vendor_price_drops() -> None:
    """A vendor quote BELOW the auto-priced line yields a negative
    subtotal adjustment — the savings should be visible to the operator."""
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 1.0)]
    lines = [
        _line(description="Interior latex paint walls",
              quantity=100.0, unit_cost=2.0),  # 200 → 100, −100
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    summary = _summarize_batch_plan(plan, est)
    assert summary["estimated_total_adjustment"] == pytest.approx(-100.0)


# ---------------------------------------------------------------------------
# _format_batch_csv_for_history
# ---------------------------------------------------------------------------


def test_format_batch_history_empty_emits_header_only() -> None:
    csv_text = _format_batch_csv_for_history(_empty_plan(), [])
    reader = csv.DictReader(io.StringIO(csv_text))
    assert reader.fieldnames == [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    assert list(reader) == []


def test_format_batch_history_includes_batch_prefix_in_notes() -> None:
    rows = [BatchOverrideRow(
        2, "Interior latex paint walls", 3.50,
        vendor="Sherwin", quote_ref="Q-1",
    )]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    plan = match_cost_lines(rows, lines)
    csv_text = _format_batch_csv_for_history(plan, plan.matched)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(parsed) == 1
    note = parsed[0]["operator_note"]
    assert note.startswith("[batch]")
    assert "[vendor: Sherwin]" in note
    assert "[quote-ref: Q-1]" in note
    assert "[csv-row: 2]" in note


def test_format_batch_history_rows_ordered_by_csv_row() -> None:
    import re

    rows = [
        BatchOverrideRow(7, "Interior latex paint walls", 3.0),
        BatchOverrideRow(2, "Slab on grade 3000psi", 9.0),
        BatchOverrideRow(5, "Steel column W12x26", 200.0),
    ]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Slab on grade 3000psi", csi_section="03 30 00"),
        _line(description="Steel column W12x26", csi_section="05 12 00"),
    ]
    plan = match_cost_lines(rows, lines)
    csv_text = _format_batch_csv_for_history(plan, plan.matched)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    # The CSV rows should come back in csv_row order, not match-bucket order.
    csv_rows_in_output: list[int] = []
    for r in parsed:
        m = re.search(r"\[csv-row:\s*(\d+)\]", r["operator_note"])
        assert m is not None
        csv_rows_in_output.append(int(m.group(1)))
    assert csv_rows_in_output == sorted(csv_rows_in_output)
    assert csv_rows_in_output == [2, 5, 7]


def test_format_batch_history_carries_new_unit_cost() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 7.77)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    plan = match_cost_lines(rows, lines)
    csv_text = _format_batch_csv_for_history(plan, plan.matched)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert float(parsed[0]["new_unit_cost"]) == pytest.approx(7.77)


def test_format_batch_history_handles_all_matched_plan() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 3.0),
        BatchOverrideRow(3, "Slab on grade 3000psi", 9.0),
    ]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Slab on grade 3000psi", csi_section="03 30 00"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 2
    csv_text = _format_batch_csv_for_history(plan, plan.matched)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert len(parsed) == 2


def test_format_batch_history_handles_unmatched_plan_safely() -> None:
    """An all-unmatched plan (nothing to apply) → empty CSV body."""
    rows = [BatchOverrideRow(2, "qrx pqw mnop zzy", 50.0)]
    lines = [_line(description="Interior latex paint walls")]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 0
    csv_text = _format_batch_csv_for_history(plan, plan.matched)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert parsed == []
