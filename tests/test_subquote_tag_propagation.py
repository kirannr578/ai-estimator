"""Phase T6.4.c — source-tag propagation into CostLine.notes.

End-to-end tests confirming the four batch-apply paths (T6.3 vendor CSV,
T8.1 tabular sub-quote PDF, T8.2 LLM-vision sub-quote PDF, T6.4.c
re-apply with a different source) all stamp the right
``[<source-tag>]`` token at position 0 of every overridden
:class:`~core.schemas.CostLine`'s ``notes`` field — visible at a
glance in the Excel exporter Notes column and the client PDF cost
breakdown without needing to scan the full notes string.

Bucketed:

* **Constants** — the five ``SOURCE_TAG_*`` module-level constants
  defined in :mod:`core.pricing.batch_override` carry the expected
  string values and are wired into the canonical set + regex pattern.
* **Backend propagation** — every call site of
  :func:`~core.pricing.batch_override.apply_batch_plan` correctly
  threads ``source_tag`` through to :func:`_rewrite_notes_with_tag_first`
  so the tag lands at position 0 of ``CostLine.notes``.
* **Sub-quote wrapper** —
  :func:`core.pricing.subquote_parser.apply_subquote_plan` picks the
  right tag for tabular vs. LLM-vision paths.
* **Re-apply semantics** — most-recent-wins on the leading tag; the
  prior tag is preserved as part of the ``| previous: ...`` suffix.
* **Idempotency** — applying the same plan twice does NOT accumulate
  duplicate tags.
* **Regex pattern** — every note after apply matches
  :data:`SOURCE_TAG_PATTERN`.
"""

from __future__ import annotations

import re

import pytest

from core.estimator import MANUAL_OVERRIDE_NOTE_PREFIX, apply_manual_override
from core.pricing.batch_override import (
    SOURCE_TAG_BATCH,
    SOURCE_TAG_MANUAL_OVERRIDE,
    SOURCE_TAG_PATTERN,
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
    SOURCE_TAGS_CANONICAL,
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    BatchOverrideRow,
    _rewrite_notes_with_tag_first,
    apply_batch_plan,
    format_batch_operator_note,
    match_cost_lines,
)
from core.pricing.subquote_parser import apply_subquote_plan
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
        confidence=0.92,
        price_confidence=0.65,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        suppressed=False,
        cost_source="cwicr:42",
        notes=notes,
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.4.c source-tag propagation",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _plan_one_matched(
    description: str,
    unit_cost: float,
    *,
    row_index: int = 2,
    vendor: str | None = "Sherwin",
    quote_ref: str | None = "Q-1",
    notes: str | None = "includes primer",
) -> tuple[BatchOverridePlan, BatchOverrideRow]:
    """Build a single-row MATCHED plan against the given description.

    Returns ``(plan, row)`` so a test can re-inspect the row that
    was matched. Targets a single CostLine; ``match_cost_lines`` is
    invoked so the bucket bookkeeping matches a real run.
    """
    row = BatchOverrideRow(
        row_index=row_index,
        description=description,
        unit_cost=unit_cost,
        vendor=vendor,
        quote_ref=quote_ref,
        notes=notes,
    )
    return (
        BatchOverridePlan(
            total_rows=1,
            matched=[
                BatchMatchResult(
                    row=row,
                    status=BatchMatchStatus.MATCHED,
                    best_match_index=0,
                    best_match_similarity=1.0,
                    runner_up_index=None,
                    runner_up_similarity=0.0,
                    candidate_lines=[(0, 1.0)],
                )
            ],
            ambiguous=[],
            no_match=[],
            low_similarity=[],
            similarity_threshold=0.65,
            ambiguity_margin=0.10,
        ),
        row,
    )


# ---------------------------------------------------------------------------
# Source-tag constants
# ---------------------------------------------------------------------------


def test_source_tag_constants_string_values() -> None:
    """The five canonical constants carry the expected literal values."""
    assert SOURCE_TAG_BATCH == "[batch]"
    assert SOURCE_TAG_VENDOR_CSV == "[vendor-csv]"
    assert SOURCE_TAG_SUBQUOTE_TABULAR == "[sub-quote]"
    assert SOURCE_TAG_SUBQUOTE_LLM == "[sub-quote-llm]"
    assert SOURCE_TAG_MANUAL_OVERRIDE == "[manual-override]"


def test_source_tags_canonical_set_contents() -> None:
    """``SOURCE_TAGS_CANONICAL`` enumerates every defined source tag."""
    assert SOURCE_TAGS_CANONICAL == frozenset({
        "[batch]",
        "[vendor-csv]",
        "[sub-quote]",
        "[sub-quote-llm]",
        "[manual-override]",
    })


def test_source_tag_pattern_matches_every_canonical_tag() -> None:
    """The regex pattern matches every canonical tag followed by a space."""
    pat = re.compile(SOURCE_TAG_PATTERN)
    for tag in SOURCE_TAGS_CANONICAL:
        sample = f"{tag} operator override: foo"
        assert pat.match(sample) is not None, f"pattern failed on tag {tag}"


# ---------------------------------------------------------------------------
# _rewrite_notes_with_tag_first — pure helper unit tests
# ---------------------------------------------------------------------------


def test_rewrite_notes_empty_prior_no_leading_whitespace() -> None:
    """No prior notes → tag at position 0, no leading whitespace."""
    payload = "[sub-quote] [vendor: Trane] [csv-row: 2]"
    result = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes=None,
    )
    assert result.startswith("[sub-quote] operator override: ")
    assert not result.startswith(" ")
    assert "| previous:" not in result


def test_rewrite_notes_with_prior_appends_previous_suffix() -> None:
    """Non-empty prior notes → tag at start, prior preserved as suffix."""
    payload = "[sub-quote] [vendor: Trane] [csv-row: 2]"
    result = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes="Hand-priced on 2026-05-01",
    )
    assert result.startswith("[sub-quote] operator override: ")
    assert result.endswith("| previous: Hand-priced on 2026-05-01")


def test_rewrite_notes_idempotent_same_tag_same_payload() -> None:
    """Re-rewriting with the same tag+payload does NOT accumulate."""
    payload = "[sub-quote] [csv-row: 2]"
    first = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes=None,
    )
    second = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes=first,
    )
    assert second == first


def test_rewrite_notes_idempotent_when_chain_already_present() -> None:
    """An existing tag+previous chain doesn't double up on re-rewrite."""
    payload = "[sub-quote] [csv-row: 2]"
    first = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes="hand-priced",
    )
    second = _rewrite_notes_with_tag_first(
        source_tag="[sub-quote]",
        note_payload=payload,
        prior_notes=first,
    )
    assert second == first


# ---------------------------------------------------------------------------
# apply_batch_plan — source_tag propagation through MATCHED rows
# ---------------------------------------------------------------------------


def test_apply_batch_plan_default_uses_batch_tag() -> None:
    """Default ``source_tag`` → ``[batch]`` at position 0 (T6.3 byte-compat)."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(estimate, plan)
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_BATCH + " ")


def test_apply_batch_plan_explicit_vendor_csv_tag() -> None:
    """Explicit ``source_tag=SOURCE_TAG_VENDOR_CSV`` → ``[vendor-csv]`` first."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_VENDOR_CSV
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_VENDOR_CSV + " ")


def test_apply_batch_plan_subquote_tabular_tag() -> None:
    """T8.1 tabular sub-quote → ``[sub-quote]`` at position 0."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")


def test_apply_batch_plan_subquote_llm_tag() -> None:
    """T8.2 LLM-vision sub-quote → ``[sub-quote-llm]`` at position 0."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_LLM
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_LLM + " ")


def test_apply_batch_plan_notes_format_includes_override_sentinel() -> None:
    """After apply, notes carry the ``operator override`` sentinel
    immediately after the source tag so a downstream reader can both
    grep by provenance AND detect the override path."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    # Tag → space → "operator override: " → body
    head = f"{SOURCE_TAG_SUBQUOTE_TABULAR} {MANUAL_OVERRIDE_NOTE_PREFIX}:"
    assert notes.startswith(head)


def test_apply_batch_plan_preserves_prior_notes_in_suffix() -> None:
    """A CostLine with prior notes keeps them as ``| previous: ...``."""
    estimate = _estimate([_line(notes="LL@$45/hr; sub-by-AeroMech")])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")
    assert "| previous: LL@$45/hr; sub-by-AeroMech" in notes


def test_apply_batch_plan_tag_visible_at_position_zero() -> None:
    """A pattern-match against ``^\\[...\\] `` succeeds for every applied line."""
    estimate = _estimate([
        _line(description="Lavatory P-1", unit_cost=500.0),
        _line(description="Water closet WC-1", unit_cost=400.0),
    ])
    rows = [
        BatchOverrideRow(2, "Lavatory P-1", 450.0),
        BatchOverrideRow(3, "Water closet WC-1", 525.0),
    ]
    plan = match_cost_lines(rows, list(estimate.line_items))
    new_estimate, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_LLM
    )
    pat = re.compile(SOURCE_TAG_PATTERN)
    for li in new_estimate.line_items:
        assert li.notes is not None
        assert pat.match(li.notes) is not None, f"no tag at start: {li.notes!r}"


def test_apply_batch_plan_ambiguous_resolved_carries_source_tag() -> None:
    """AMBIGUOUS rows resolved via ``resolved_ambiguous`` also get the tag."""
    rows = [BatchOverrideRow(5, "Interior latex paint", 3.50)]
    lines = [
        _line(description="Interior latex paint walls", unit_cost=2.0),
        _line(description="Interior latex paint ceiling", unit_cost=2.10),
    ]
    estimate = _estimate(lines)
    plan = match_cost_lines(rows, list(estimate.line_items))
    assert len(plan.ambiguous) == 1
    new_estimate, _ = apply_batch_plan(
        estimate,
        plan,
        resolved_ambiguous={5: 0},
        source_tag=SOURCE_TAG_SUBQUOTE_TABULAR,
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")


def test_apply_batch_plan_default_signature_byte_compat() -> None:
    """Pre-T6.4.c positional call (no source_tag) still works and tags ``[batch]``."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, summary = apply_batch_plan(
        estimate, plan, True, None, None
    )
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_BATCH + " ")
    # Summary header preserved.
    assert summary[0].startswith("Batch override summary:")


# ---------------------------------------------------------------------------
# Re-apply / most-recent-wins / override-history chain
# ---------------------------------------------------------------------------


def test_reapply_subquote_then_llm_tag_swaps_at_front() -> None:
    """Apply T8.1 then T8.2 on the same line: ``[sub-quote-llm]`` lands at
    position 0; ``[sub-quote]`` preserved inside the ``| previous: ...`` chain
    so an auditor can recover the full override history."""
    estimate = _estimate([_line()])
    plan_a, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    estimate_after_a, _ = apply_batch_plan(
        estimate, plan_a, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    plan_b, _ = _plan_one_matched(
        "Interior latex paint walls", 3.75, row_index=4, vendor="GraphicsCo"
    )
    estimate_after_b, _ = apply_batch_plan(
        estimate_after_a, plan_b, source_tag=SOURCE_TAG_SUBQUOTE_LLM
    )
    notes = estimate_after_b.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_LLM + " ")
    # Prior provenance preserved in the chain.
    assert "| previous: " in notes
    assert SOURCE_TAG_SUBQUOTE_TABULAR in notes


def test_reapply_idempotent_same_plan_no_duplicate_tags() -> None:
    """Re-applying the exact same plan twice does NOT grow the tag chain.

    Idempotency contract: ``_rewrite_notes_with_tag_first`` detects that
    the prior_notes already starts with the same head it's about to
    write and short-circuits, so the second apply produces a notes
    string with EXACTLY ONE leading ``[sub-quote]`` token — no
    ``| previous: [sub-quote] ...`` chain accumulating.
    """
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    e1, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    e2, _ = apply_batch_plan(
        e1, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    notes = e2.line_items[0].notes
    assert notes is not None
    # Tag appears exactly once at position 0.
    assert notes.count(SOURCE_TAG_SUBQUOTE_TABULAR) == 1


def test_reapply_vendor_csv_after_subquote_swaps_tag() -> None:
    """A vendor-CSV apply after a sub-quote apply moves ``[vendor-csv]`` to
    the front and preserves the prior ``[sub-quote]`` tag in the chain."""
    estimate = _estimate([_line()])
    plan_a, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    estimate_after_a, _ = apply_batch_plan(
        estimate, plan_a, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    plan_b, _ = _plan_one_matched(
        "Interior latex paint walls", 3.75, row_index=4
    )
    estimate_after_b, _ = apply_batch_plan(
        estimate_after_a, plan_b, source_tag=SOURCE_TAG_VENDOR_CSV
    )
    notes = estimate_after_b.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_VENDOR_CSV + " ")
    assert SOURCE_TAG_SUBQUOTE_TABULAR in notes  # preserved in previous chain


# ---------------------------------------------------------------------------
# apply_subquote_plan wrapper
# ---------------------------------------------------------------------------


def test_apply_subquote_plan_default_uses_tabular_tag() -> None:
    """Default ``llm=False`` → ``[sub-quote]`` propagates."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_subquote_plan(estimate, plan)
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")


def test_apply_subquote_plan_llm_flag_uses_llm_tag() -> None:
    """``llm=True`` → ``[sub-quote-llm]`` propagates."""
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, _ = apply_subquote_plan(estimate, plan, llm=True)
    notes = new_estimate.line_items[0].notes
    assert notes is not None
    assert notes.startswith(SOURCE_TAG_SUBQUOTE_LLM + " ")


def test_apply_subquote_plan_threads_other_kwargs() -> None:
    """The wrapper passes ``skip_rows`` / ``resolved_ambiguous`` through."""
    estimate = _estimate([
        _line(description="Interior latex paint walls", unit_cost=2.0),
    ])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    new_estimate, summary = apply_subquote_plan(
        estimate, plan, skip_rows={2}
    )
    # Skipped — unit_cost unchanged.
    assert new_estimate.line_items[0].unit_cost == 2.0
    assert any("SKIPPED (operator opt-out)" in s for s in summary)


# ---------------------------------------------------------------------------
# Production-code call sites use SOURCE_TAG_* constants, not literals
# ---------------------------------------------------------------------------


def test_no_inline_source_tag_literals_in_production_paths() -> None:
    """The ``apply_batch_plan`` source code references the
    ``SOURCE_TAG_BATCH`` constant for its default, not the raw
    ``"[batch]"`` literal — so a future rename of the default value
    only touches the constant.

    This guards against drift between the constant and the inline
    default; if a future contributor changes the default to a fresh
    literal without updating the constant, this test catches it.
    """
    import inspect
    from core.pricing import batch_override

    src = inspect.getsource(batch_override.apply_batch_plan)
    # The default must reference the constant by name.
    assert "source_tag: str = SOURCE_TAG_BATCH" in src
    # Both call sites of format_batch_operator_note must thread source_tag.
    assert src.count("format_batch_operator_note(result.row, source_tag=source_tag)") == 2


# ---------------------------------------------------------------------------
# Manual-override interplay (documented out-of-scope)
# ---------------------------------------------------------------------------


def test_manual_override_after_batch_apply_stamps_manual_override_tag() -> None:
    """Phase T6.4.c.2 — :func:`apply_manual_override` now routes through
    ``format_manual_override_note`` so the canonical
    :data:`SOURCE_TAG_MANUAL_OVERRIDE` (``"[manual-override]"``) tag
    lands at **position 0** of the post-override notes string, even
    when the prior notes already carried a ``[sub-quote]`` /
    ``[sub-quote-llm]`` / ``[vendor-csv]`` / ``[batch]`` tag from an
    earlier batch apply.

    The prior batch-applied tag is preserved verbatim in the
    ``" | previous: ..."`` suffix so an auditor can walk back through
    the full provenance chain. This closes the loose end flagged in
    T6.4.c's "Edge cases NOT handled" section.
    """
    estimate = _estimate([_line()])
    plan, _ = _plan_one_matched("Interior latex paint walls", 3.50)
    after_batch, _ = apply_batch_plan(
        estimate, plan, source_tag=SOURCE_TAG_SUBQUOTE_TABULAR
    )
    after_manual = apply_manual_override(
        after_batch, 0, new_unit_cost=4.00, operator_note="bumped per Q-99"
    )
    notes = after_manual.line_items[0].notes
    assert notes is not None
    # T6.4.c.2 contract: [manual-override] at position 0.
    assert notes.startswith("[manual-override] ")
    # Free-text reason verbatim.
    assert "bumped per Q-99" in notes
    # Prior [sub-quote] tag preserved in the | previous: ... suffix.
    assert " | previous: " in notes
    assert SOURCE_TAG_SUBQUOTE_TABULAR in notes
    # Prior batch tag lives in the suffix, not the head.
    head, _, suffix = notes.partition(" | previous: ")
    assert SOURCE_TAG_SUBQUOTE_TABULAR not in head
    assert suffix.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")


# ---------------------------------------------------------------------------
# T6.3 backward compatibility — pre-T6.4.c snapshots stay byte-identical
# ---------------------------------------------------------------------------


def test_format_batch_operator_note_default_still_batch_tag() -> None:
    """The pre-T6.4.c default of ``[batch]`` is preserved for byte-compat
    with every snapshot test in :mod:`tests.test_batch_override_core`."""
    row = BatchOverrideRow(7, "Interior paint", 3.0)
    note = format_batch_operator_note(row)
    assert note.startswith("[batch]")
