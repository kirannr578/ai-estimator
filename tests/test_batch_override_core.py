"""Phase T6.3 — `core/pricing/batch_override.py` core tests.

Covers the pure-logic batch-override module: CSV parsing, fuzzy
matching, match-plan application, and CSV export. No Streamlit and
no file-system I/O — the module takes CSV text in and returns
plans / new Estimates out.

Bucketed:

* **CSV parsing** (12 tests) — required column detection, alias
  resolution, BOM stripping, embedded commas, per-row error skip.
* **Matching** (13 tests) — exact / rephrased / ambiguous / no-match
  / low-similarity, threshold + margin honoured, CSI prefix stripping,
  empty-input edge cases.
* **Apply** (8 tests) — MATCHED auto-apply, AMBIGUOUS resolution path,
  skip_rows honoured, operator-note format, LOW_SIMILARITY +
  NO_MATCH never applied, idempotency.
* **Export** (5 tests) — CSV column shape, status round-trip, with /
  without cost_lines descriptions.
"""

from __future__ import annotations

import csv
import io

import pytest

from core.estimator import MANUAL_OVERRIDE_NOTE_PREFIX
from core.pricing.batch_override import (
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    BatchOverrideRow,
    apply_batch_plan,
    export_match_plan_csv,
    format_batch_operator_note,
    match_cost_lines,
    parse_vendor_csv,
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
        project_name="T6.3 batch override",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# parse_vendor_csv — happy path / aliases / required columns
# ---------------------------------------------------------------------------


def test_parse_standard_csv_with_all_columns() -> None:
    csv_text = (
        "description,unit_cost,vendor,quote_ref,notes,quantity\n"
        "Interior paint,2.50,Sherwin,Q-1,walls only,100\n"
        "Slab on grade,8.00,RMS,PO#5,3000psi,250\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert len(rows) == 2
    assert rows[0].row_index == 2
    assert rows[0].description == "Interior paint"
    assert rows[0].unit_cost == pytest.approx(2.50)
    assert rows[0].vendor == "Sherwin"
    assert rows[0].quote_ref == "Q-1"
    assert rows[0].notes == "walls only"
    assert rows[0].quantity == pytest.approx(100.0)
    assert rows[1].row_index == 3


def test_parse_required_only_csv() -> None:
    csv_text = (
        "description,unit_cost\n"
        "Interior paint,2.50\n"
        "Slab on grade,8.00\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert len(rows) == 2
    assert all(r.vendor is None and r.quote_ref is None for r in rows)
    assert all(r.notes is None and r.quantity is None for r in rows)


def test_parse_column_aliases_desc_price_supplier_qty() -> None:
    csv_text = (
        "desc,price,supplier,quote,comments,qty\n"
        "Interior paint,2.50,Sherwin,Q-1,walls only,100\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].description == "Interior paint"
    assert rows[0].unit_cost == pytest.approx(2.50)
    assert rows[0].vendor == "Sherwin"
    assert rows[0].quote_ref == "Q-1"
    assert rows[0].notes == "walls only"
    assert rows[0].quantity == pytest.approx(100.0)


def test_parse_column_aliases_item_rate() -> None:
    csv_text = "item,rate\nInterior paint,2.50\n"
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].description == "Interior paint"
    assert rows[0].unit_cost == pytest.approx(2.50)


def test_parse_case_insensitive_headers() -> None:
    csv_text = "DESCRIPTION,UNIT_COST,VENDOR\nInterior paint,2.50,Sherwin\n"
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].vendor == "Sherwin"


def test_parse_empty_file_raises() -> None:
    with pytest.raises(ValueError, match="empty"):
        parse_vendor_csv("")
    with pytest.raises(ValueError, match="empty"):
        parse_vendor_csv("   \n  \n")


def test_parse_missing_required_description_raises() -> None:
    csv_text = "vendor,unit_cost\nSherwin,2.50\n"
    with pytest.raises(ValueError, match="description"):
        parse_vendor_csv(csv_text)


def test_parse_missing_required_unit_cost_raises() -> None:
    csv_text = "description,vendor\nInterior paint,Sherwin\n"
    with pytest.raises(ValueError, match="unit_cost"):
        parse_vendor_csv(csv_text)


def test_parse_non_numeric_unit_cost_skips_row_others_parsed() -> None:
    csv_text = (
        "description,unit_cost\n"
        "Interior paint,abc\n"
        "Slab on grade,8.00\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].description == "Slab on grade"
    assert len(errors) == 1
    assert "non-numeric" in errors[0].lower()
    assert "row 2" in errors[0].lower()


def test_parse_negative_unit_cost_skips_row() -> None:
    csv_text = (
        "description,unit_cost\n"
        "Interior paint,-5.00\n"
        "Slab on grade,8.00\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].description == "Slab on grade"
    assert any("negative" in e.lower() for e in errors)


def test_parse_embedded_commas_in_description() -> None:
    csv_text = (
        'description,unit_cost\n'
        '"Interior paint, walls only",2.50\n'
        '"Slab on grade, 3000psi",8.00\n'
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].description == "Interior paint, walls only"
    assert rows[1].description == "Slab on grade, 3000psi"


def test_parse_bom_is_stripped() -> None:
    csv_text = "\ufeffdescription,unit_cost\nInterior paint,2.50\n"
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].description == "Interior paint"
    assert rows[0].unit_cost == pytest.approx(2.50)


def test_parse_dollar_signs_and_thousands_separators_tolerated() -> None:
    csv_text = (
        "description,unit_cost\n"
        "Interior paint,$2.50\n"
        'Big ticket,"$1,250.00"\n'
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert errors == []
    assert rows[0].unit_cost == pytest.approx(2.50)
    assert rows[1].unit_cost == pytest.approx(1250.00)


def test_parse_empty_description_skips_row() -> None:
    csv_text = (
        "description,unit_cost\n"
        ",2.50\n"
        "Slab on grade,8.00\n"
    )
    rows, errors = parse_vendor_csv(csv_text)
    assert len(rows) == 1
    assert rows[0].description == "Slab on grade"
    assert any("empty description" in e.lower() for e in errors)


# ---------------------------------------------------------------------------
# match_cost_lines — happy path / threshold / ambiguity / normalisation
# ---------------------------------------------------------------------------


def test_exact_description_match_lands_in_matched() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Slab on grade", csi_section="03 30 00"),
    ]
    plan = match_cost_lines(rows, lines)
    assert plan.total_rows == 1
    assert len(plan.matched) == 1
    assert plan.matched[0].best_match_index == 0
    assert plan.matched[0].best_match_similarity >= 0.95


def test_slight_rephrasing_above_threshold_matched() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint to walls", 3.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Roofing membrane TPO", csi_section="07 54 23"),
    ]
    plan = match_cost_lines(rows, lines, similarity_threshold=0.65)
    assert len(plan.matched) == 1
    assert plan.matched[0].best_match_similarity >= 0.65


def test_two_costlines_tied_lands_ambiguous() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint", 3.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Interior latex paint ceiling"),
    ]
    plan = match_cost_lines(rows, lines, ambiguity_margin=0.10)
    assert len(plan.ambiguous) == 1
    res = plan.ambiguous[0]
    assert res.best_match_index in (0, 1)
    assert res.runner_up_index in (0, 1)
    assert res.best_match_index != res.runner_up_index
    assert abs(res.best_match_similarity - res.runner_up_similarity) < 0.10


def test_description_not_in_any_costline_lands_no_match() -> None:
    # Pure-gibberish input pinned at < 0.40 sim against any cost line.
    rows = [BatchOverrideRow(2, "qrx pqw mnop zzy", 50.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Steel column W12x26", csi_section="05 12 00"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.no_match) == 1
    assert plan.no_match[0].best_match_similarity < 0.40


def test_sub_threshold_but_plausible_lands_low_similarity() -> None:
    # "Paint walls" vs. "Interior latex paint walls" sims to ~0.60 —
    # below the 0.65 default but well above the 0.40 NO_MATCH floor.
    rows = [BatchOverrideRow(2, "Paint walls", 3.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Steel column", csi_section="05 12 00"),
    ]
    plan = match_cost_lines(rows, lines, similarity_threshold=0.80)
    # With a 0.80 threshold the genuine paint match drops out of MATCHED
    # but stays above the 0.40 NO_MATCH floor.
    assert len(plan.matched) == 0
    assert len(plan.low_similarity) == 1


def test_csi_prefix_stripped_before_match() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [
        _line(description="09 91 23 - Interior latex paint walls"),
        _line(description="Slab on grade", csi_section="03 30 00"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1
    # With CSI stripped, similarity should be effectively 1.0.
    assert plan.matched[0].best_match_similarity >= 0.95


def test_csi_prefix_with_extension_stripped() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [
        _line(description="09 91 23.13 - Interior latex paint walls"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1
    assert plan.matched[0].best_match_similarity >= 0.95


def test_csi_prefix_with_trailing_space_stripped() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [
        _line(description="09 91 23.13 -  Interior latex paint walls"),
    ]
    plan = match_cost_lines(rows, lines)
    assert len(plan.matched) == 1
    assert plan.matched[0].best_match_similarity >= 0.95


def test_custom_threshold_honoured() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint to walls", 3.0)]
    lines = [_line(description="Interior latex paint walls")]
    # 0.65 default → MATCHED
    plan_loose = match_cost_lines(rows, lines, similarity_threshold=0.65)
    assert len(plan_loose.matched) == 1
    # 0.99 strict → can't possibly hit (rephrased input)
    plan_strict = match_cost_lines(rows, lines, similarity_threshold=0.99)
    assert len(plan_strict.matched) == 0


def test_custom_ambiguity_margin_honoured() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint", 3.0)]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Interior latex paint ceiling"),
    ]
    # Tight 0.05 margin: similarities are ~equal → AMBIGUOUS.
    tight = match_cost_lines(rows, lines, ambiguity_margin=0.05)
    assert len(tight.ambiguous) == 1
    # Loose 0.50 margin: still AMBIGUOUS (two near-identical descs).
    loose = match_cost_lines(rows, lines, ambiguity_margin=0.50)
    assert len(loose.ambiguous) == 1


def test_no_candidates_lands_no_match() -> None:
    rows = [BatchOverrideRow(2, "Interior paint", 3.0)]
    plan = match_cost_lines(rows, [])
    assert len(plan.no_match) == 1
    assert plan.no_match[0].best_match_index is None


def test_empty_rows_returns_empty_plan() -> None:
    lines = [_line()]
    plan = match_cost_lines([], lines)
    assert plan.total_rows == 0
    assert plan.matched == []
    assert plan.ambiguous == []


def test_candidate_lines_top5_returned() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [_line(description=f"Variant {i}") for i in range(10)] + [
        _line(description="Interior latex paint walls"),
    ]
    plan = match_cost_lines(rows, lines)
    # The single matched row should have 5 candidates returned.
    matched = plan.matched + plan.low_similarity + plan.ambiguous
    assert len(matched) == 1
    assert len(matched[0].candidate_lines) == 5


# ---------------------------------------------------------------------------
# apply_batch_plan
# ---------------------------------------------------------------------------


def test_apply_matched_stamps_manual_override_tier() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.50)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    new_est, summary = apply_batch_plan(est, plan)
    assert new_est.line_items[0].cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert new_est.line_items[0].unit_cost == pytest.approx(3.50)
    assert any("APPLIED" in line for line in summary)


def test_apply_skips_ambiguous_when_unresolved() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint", 3.50)]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
        _line(description="Interior latex paint ceiling", unit_cost=2.5),
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    assert len(plan.ambiguous) == 1
    new_est, summary = apply_batch_plan(est, plan)
    # Neither line was touched.
    assert new_est.line_items[0].unit_cost == pytest.approx(2.0)
    assert new_est.line_items[1].unit_cost == pytest.approx(2.5)
    assert any("ambiguous" in s.lower() for s in summary)


def test_apply_ambiguous_with_resolved_dict() -> None:
    rows = [BatchOverrideRow(5, "Interior latex paint", 3.50)]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
        _line(description="Interior latex paint ceiling", unit_cost=2.5),
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    assert len(plan.ambiguous) == 1
    # Resolve row 5 to line index 1 (ceiling)
    new_est, summary = apply_batch_plan(
        est, plan, resolved_ambiguous={5: 1}
    )
    assert new_est.line_items[1].cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert new_est.line_items[1].unit_cost == pytest.approx(3.50)
    # Walls untouched
    assert new_est.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED


def test_apply_respects_skip_rows_set() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 3.50),
        BatchOverrideRow(3, "Slab on grade 3000psi", 9.00),
    ]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
        _line(description="Slab on grade 3000psi", csi_section="03 30 00",
              unit_cost=8.0),
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    new_est, summary = apply_batch_plan(est, plan, skip_rows={3})
    # Row 2 applied, row 3 skipped.
    assert new_est.line_items[0].unit_cost == pytest.approx(3.50)
    assert new_est.line_items[1].unit_cost == pytest.approx(8.0)
    assert any("Row 3" in s and "SKIPPED" in s for s in summary)


def test_apply_operator_note_carries_batch_prefix() -> None:
    rows = [BatchOverrideRow(
        2, "Interior latex paint walls", 3.50,
        vendor="Sherwin", quote_ref="Q-1", notes="includes primer",
    )]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    new_est, _ = apply_batch_plan(est, plan)
    notes = new_est.line_items[0].notes or ""
    assert "[batch]" in notes
    assert "[vendor: Sherwin]" in notes
    assert "[quote-ref: Q-1]" in notes
    assert "[csv-row: 2]" in notes
    assert "includes primer" in notes
    assert MANUAL_OVERRIDE_NOTE_PREFIX in notes


def test_apply_low_similarity_never_applied() -> None:
    rows = [BatchOverrideRow(2, "Paint walls", 3.0)]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
    ]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines, similarity_threshold=0.80)
    assert len(plan.low_similarity) == 1
    new_est, summary = apply_batch_plan(est, plan)
    assert new_est.line_items[0].unit_cost == pytest.approx(2.0)
    assert any("low similarity" in s.lower() for s in summary)


def test_apply_no_match_never_applied() -> None:
    rows = [BatchOverrideRow(2, "qrx pqw mnop zzy", 50.0)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    assert len(plan.no_match) == 1
    new_est, summary = apply_batch_plan(est, plan)
    assert new_est.line_items[0].unit_cost == pytest.approx(2.0)
    assert any("no match" in s.lower() for s in summary)


def test_apply_idempotent_same_plan_same_result() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.50)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    once, _ = apply_batch_plan(est, plan)
    twice, _ = apply_batch_plan(once, plan)
    a = once.line_items[0]
    b = twice.line_items[0]
    assert a.unit_cost == b.unit_cost
    assert a.total_cost == b.total_cost
    assert a.cost_source_tier == b.cost_source_tier


def test_apply_does_not_mutate_input_estimate() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 9.99)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    _ = apply_batch_plan(est, plan)
    # Input unchanged
    assert est.line_items[0].unit_cost == pytest.approx(2.0)
    assert est.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED


def test_apply_summary_includes_count_header() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.50)]
    lines = [_line(description="Interior latex paint walls", unit_cost=2.0)]
    est = _estimate(lines)
    plan = match_cost_lines(rows, lines)
    _, summary = apply_batch_plan(est, plan)
    assert summary[0].startswith("Batch override summary:")
    assert "1 applied" in summary[0]


# ---------------------------------------------------------------------------
# export_match_plan_csv
# ---------------------------------------------------------------------------


def test_export_match_plan_csv_columns_present() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [_line(description="Interior latex paint walls")]
    plan = match_cost_lines(rows, lines)
    csv_text = export_match_plan_csv(plan, lines)
    reader = csv.DictReader(io.StringIO(csv_text))
    # Phase T6.4.b added three columns: ``csv_unit_of_measure`` (the
    # row's UoM), ``matched_unit`` (the chosen cost line's unit), and
    # ``uom_mismatch_warning`` (populated only on the safety-off path).
    # Previous columns retained in their original positions.
    assert reader.fieldnames == [
        "csv_row", "csv_description", "csv_unit_cost", "csv_unit_of_measure",
        "status",
        "matched_line_index", "matched_description", "matched_unit",
        "similarity",
        "runner_up_index", "runner_up_description",
        "runner_up_similarity",
        "uom_mismatch_warning",
        "notes",
    ]


def test_export_match_plan_status_string_per_row() -> None:
    rows = [
        BatchOverrideRow(2, "Interior latex paint walls", 3.0),
        BatchOverrideRow(3, "qrx pqw mnop zzy", 50.0),
    ]
    lines = [_line(description="Interior latex paint walls")]
    plan = match_cost_lines(rows, lines)
    csv_text = export_match_plan_csv(plan, lines)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    by_row = {int(r["csv_row"]): r for r in parsed}
    assert by_row[2]["status"] == BatchMatchStatus.MATCHED.value
    assert by_row[3]["status"] == BatchMatchStatus.NO_MATCH.value


def test_export_match_plan_includes_descriptions_when_costlines_provided() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [_line(description="Interior latex paint walls")]
    plan = match_cost_lines(rows, lines)
    csv_text = export_match_plan_csv(plan, lines)
    assert "Interior latex paint walls" in csv_text


def test_export_match_plan_handles_missing_costlines() -> None:
    rows = [BatchOverrideRow(2, "Interior latex paint walls", 3.0)]
    lines = [_line(description="Interior latex paint walls")]
    plan = match_cost_lines(rows, lines)
    csv_text = export_match_plan_csv(plan, cost_lines=None)
    # Should still produce valid CSV; matched_description column blank.
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert parsed[0]["matched_description"] == ""


def test_export_match_plan_rows_sorted_by_csv_row() -> None:
    rows = [
        BatchOverrideRow(5, "Slab on grade 3000psi", 9.0),
        BatchOverrideRow(2, "Interior latex paint walls", 3.0),
        BatchOverrideRow(3, "asbestos removal", 50.0),
    ]
    lines = [
        _line(description="Interior latex paint walls"),
        _line(description="Slab on grade 3000psi", csi_section="03 30 00"),
    ]
    plan = match_cost_lines(rows, lines)
    csv_text = export_match_plan_csv(plan, lines)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    csv_rows = [int(r["csv_row"]) for r in parsed]
    assert csv_rows == sorted(csv_rows)


# ---------------------------------------------------------------------------
# format_batch_operator_note
# ---------------------------------------------------------------------------


def test_format_batch_operator_note_all_fields() -> None:
    row = BatchOverrideRow(
        7, "Interior paint", 3.0,
        vendor="Sherwin", quote_ref="Q-1", notes="includes primer",
    )
    note = format_batch_operator_note(row)
    assert note == (
        "[batch] [vendor: Sherwin] [quote-ref: Q-1] "
        "[csv-row: 7] includes primer"
    )


def test_format_batch_operator_note_minimal_only_required_fields() -> None:
    row = BatchOverrideRow(2, "Interior paint", 3.0)
    note = format_batch_operator_note(row)
    assert note == "[batch] [csv-row: 2]"


def test_format_batch_operator_note_starts_with_batch_marker() -> None:
    row = BatchOverrideRow(99, "x", 1.0, vendor="V", quote_ref="Q", notes="N")
    assert format_batch_operator_note(row).startswith("[batch]")
