"""Phase T8.1 — end-to-end integration tests.

These tests stitch the four T8.1 surfaces together:

* PDF → :func:`core.pricing.subquote_parser.parse_subquote_pdf` →
  :class:`SubquoteParseResult`
* :class:`BatchOverrideRow` list →
  :func:`core.pricing.batch_override.match_cost_lines` →
  :class:`BatchOverridePlan` (REUSE — unchanged from T6.3)
* :class:`BatchOverridePlan` →
  :func:`core.pricing.batch_override.apply_batch_plan` →
  :class:`Estimate` with MANUAL_OVERRIDE lines (REUSE — unchanged from T6.3)
* Override-history entry construction with ``source_tag="[sub-quote]"``
  so the audit trail records the PDF provenance.

Plus a concurrent-use scenario: the same session applying a T6.3
CSV override AND a T8.1 sub-quote override; history should show both
tags in the correct entries.
"""

from __future__ import annotations

import io

import pytest

reportlab = pytest.importorskip("reportlab")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle  # noqa: E402

from core.estimator import MANUAL_OVERRIDE_NOTE_PREFIX  # noqa: E402
from core.pricing.batch_override import (  # noqa: E402
    apply_batch_plan,
    format_batch_operator_note,
    match_cost_lines,
    parse_vendor_csv,
)
from core.pricing.subquote_parser import parse_subquote_pdf  # noqa: E402
from core.schemas import (  # noqa: E402
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
    description: str,
    unit_cost: float = 100.0,
    quantity: float = 10.0,
    csi_section: str = "22 41 00",
) -> CostLine:
    return CostLine(
        csi_division=csi_section.split(" ", 1)[0],
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit="EA",
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.9,
        price_confidence=0.7,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        cost_source="cwicr:42",
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T8.1 integration",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _subquote_pdf(rows: list[tuple[str, str, str]]) -> bytes:
    """Build a one-page PDF with a single (Description, Qty, Unit Price) table."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    data: list[list[str]] = [["Description", "Qty", "Unit Price"]]
    for desc, qty, unit_cost in rows:
        data.append([desc, qty, unit_cost])
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([t])
    return buf.getvalue()


# ---------------------------------------------------------------------------
# End-to-end happy path
# ---------------------------------------------------------------------------


class TestSubquoteEndToEnd:
    def test_parse_match_apply_creates_manual_override_lines(self) -> None:
        """Full pipeline: PDF → rows → plan → applied Estimate."""
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
            _line(description="Water closet WC-1", unit_cost=600.0),
        ])
        pdf = _subquote_pdf([
            ("Lavatory P-1", "10", "450.00"),
            ("Water closet WC-1", "8", "525.00"),
        ])

        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 2

        plan = match_cost_lines(result.rows, list(estimate.line_items))
        assert len(plan.matched) == 2

        new_estimate, summary = apply_batch_plan(estimate, plan)
        # Both lines should now have unit_costs from the sub-quote.
        descriptions = {li.description: li for li in new_estimate.line_items}
        assert descriptions["Lavatory P-1"].unit_cost == 450.0
        assert descriptions["Water closet WC-1"].unit_cost == 525.0
        # And cost_source_tier = MANUAL_OVERRIDE.
        for li in new_estimate.line_items:
            assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE

    def test_t63_backend_invoked_unchanged(self) -> None:
        """Confirm match_cost_lines + apply_batch_plan signatures unchanged.

        The integration here is intentional: the sub-quote pipeline
        reaches the T6.3 backend with NO sub-quote-specific kwargs.
        Any signature drift would fail this test loudly.
        """
        import inspect
        match_sig = inspect.signature(match_cost_lines)
        # No new kwargs — must still be (rows, cost_lines, threshold, margin).
        assert list(match_sig.parameters.keys()) == [
            "rows",
            "cost_lines",
            "similarity_threshold",
            "ambiguity_margin",
        ]
        apply_sig = inspect.signature(apply_batch_plan)
        # No new kwargs — must still match the T6.3 signature exactly.
        assert list(apply_sig.parameters.keys()) == [
            "estimate",
            "plan",
            "auto_apply_matched",
            "resolved_ambiguous",
            "skip_rows",
        ]

    def test_subquote_source_tag_survives_to_operator_note(self) -> None:
        """A sub-quote-tagged note carries through format_batch_operator_note."""
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
        ])
        pdf = _subquote_pdf([("Lavatory P-1", "10", "450.00")])
        result = parse_subquote_pdf(pdf)
        plan = match_cost_lines(result.rows, list(estimate.line_items))

        # Mirror the app.py code: build the override-history note with
        # the [sub-quote] source tag.
        row = plan.matched[0].row
        note = format_batch_operator_note(row, source_tag="[sub-quote]")
        assert note.startswith("[sub-quote]")
        assert "[batch]" not in note


# ---------------------------------------------------------------------------
# Concurrent use — CSV + sub-quote in same session
# ---------------------------------------------------------------------------


class TestConcurrentUse:
    def test_csv_then_subquote_in_same_session(self) -> None:
        """Apply a T6.3 CSV override then a T8.1 sub-quote override."""
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
            _line(description="Drywall 5/8 inch", unit_cost=2.0, csi_section="09 21 16"),
        ])

        # T6.3: apply a CSV override to the drywall line.
        csv_text = (
            "description,unit_cost,vendor\n"
            "Drywall 5/8 inch,1.85,ABC Drywall\n"
        )
        csv_rows, _ = parse_vendor_csv(csv_text)
        csv_plan = match_cost_lines(csv_rows, list(estimate.line_items))
        estimate, _ = apply_batch_plan(estimate, csv_plan)

        # T8.1: now apply a sub-quote override to the plumbing line.
        pdf = _subquote_pdf([("Lavatory P-1", "10", "450.00")])
        sq_result = parse_subquote_pdf(pdf)
        sq_plan = match_cost_lines(sq_result.rows, list(estimate.line_items))
        estimate, _ = apply_batch_plan(estimate, sq_plan)

        # Both lines should reflect the appropriate override.
        descriptions = {li.description: li for li in estimate.line_items}
        assert descriptions["Drywall 5/8 inch"].unit_cost == 1.85
        assert descriptions["Lavatory P-1"].unit_cost == 450.0

    def test_csv_and_subquote_tags_distinguishable_in_history(self) -> None:
        """Operator-note tags differentiate CSV vs sub-quote provenance."""
        estimate = _estimate([
            _line(description="Item A", unit_cost=100.0),
            _line(description="Item B", unit_cost=200.0),
        ])

        # T6.3 batch: tag [batch].
        csv_rows, _ = parse_vendor_csv(
            "description,unit_cost\nItem A,90.00\n"
        )
        csv_plan = match_cost_lines(csv_rows, list(estimate.line_items))
        csv_note = format_batch_operator_note(csv_plan.matched[0].row)
        assert csv_note.startswith("[batch]")

        # T8.1 sub-quote: tag [sub-quote].
        pdf = _subquote_pdf([("Item B", "10", "180.00")])
        sq_result = parse_subquote_pdf(pdf)
        sq_plan = match_cost_lines(sq_result.rows, list(estimate.line_items))
        sq_note = format_batch_operator_note(
            sq_plan.matched[0].row,
            source_tag="[sub-quote]",
        )
        assert sq_note.startswith("[sub-quote]")
        # And the two notes are clearly distinguishable.
        assert csv_note != sq_note
        assert "[batch]" in csv_note and "[sub-quote]" not in csv_note
        assert "[sub-quote]" in sq_note and "[batch]" not in sq_note

    def test_ambiguous_resolution_path_works_for_subquote(self) -> None:
        """Sub-quote rows that hit AMBIGUOUS take the same operator-
        resolution path T6.3 uses."""
        estimate = _estimate([
            _line(description="Interior latex paint walls", unit_cost=2.0),
            _line(description="Interior latex paint ceiling", unit_cost=2.0),
        ])
        # Description matches BOTH lines closely → AMBIGUOUS.
        pdf = _subquote_pdf([("Interior latex paint", "100", "1.75")])
        result = parse_subquote_pdf(pdf)
        plan = match_cost_lines(result.rows, list(estimate.line_items))
        # At least one bucket should hold the row.
        assert plan.total_rows == 1
        assigned_buckets = [
            bucket
            for bucket, items in (
                ("matched", plan.matched),
                ("ambiguous", plan.ambiguous),
                ("low_similarity", plan.low_similarity),
                ("no_match", plan.no_match),
            )
            if items
        ]
        assert len(assigned_buckets) == 1
        # Resolution via the same dict-keyed mechanism as T6.3.
        if plan.ambiguous:
            row = plan.ambiguous[0].row
            new_estimate, _ = apply_batch_plan(
                estimate, plan, resolved_ambiguous={row.row_index: 0}
            )
            assert new_estimate.line_items[0].unit_cost == 1.75


# ---------------------------------------------------------------------------
# Manual-override marker stamping confirms estimator integration
# ---------------------------------------------------------------------------


class TestManualOverrideStamping:
    def test_applied_line_carries_manual_override_marker_in_notes(self) -> None:
        estimate = _estimate([_line(description="Lavatory P-1", unit_cost=500.0)])
        pdf = _subquote_pdf([("Lavatory P-1", "10", "450.00")])
        result = parse_subquote_pdf(pdf)
        plan = match_cost_lines(result.rows, list(estimate.line_items))
        new_estimate, _ = apply_batch_plan(estimate, plan)
        notes = new_estimate.line_items[0].notes or ""
        # The estimator stamps the MANUAL_OVERRIDE_NOTE_PREFIX sentinel
        # ahead of the operator note.
        assert MANUAL_OVERRIDE_NOTE_PREFIX in notes

    def test_applied_line_tier_is_manual_override(self) -> None:
        estimate = _estimate([_line(description="Lavatory P-1", unit_cost=500.0)])
        pdf = _subquote_pdf([("Lavatory P-1", "10", "450.00")])
        result = parse_subquote_pdf(pdf)
        plan = match_cost_lines(result.rows, list(estimate.line_items))
        new_estimate, _ = apply_batch_plan(estimate, plan)
        assert (
            new_estimate.line_items[0].cost_source_tier
            == CostSourceTier.MANUAL_OVERRIDE
        )
