"""Phase T6.4.c.2 — ``[manual-override]`` source-tag stamping tests.

Closes the last loose end from the T6.4.c source-tag propagation
contract: every override path — batch (T6.3), sub-quote tabular
(T8.1), sub-quote LLM-vision (T8.2), AND the T6.1 single-line manual
override primitive — now stamps its canonical source tag at
**position 0** of :attr:`CostLine.notes`.

This module pins the new contract for the manual primitive:

* The :func:`core.estimator.format_manual_override_note` helper as a
  pure function (bracketed-field rendering, idempotency, prior-notes
  suffix).
* :func:`core.estimator.apply_manual_override` end-to-end (writes the
  formatter's output into ``CostLine.notes`` while preserving every
  pre-T6.4.c.2 T6.1 behaviour — ``CostSourceTier.MANUAL_OVERRIDE``
  stamping, ``price_confidence`` reset, ``combined_confidence``
  recomputation, immutability of the input estimate).

The 4 existing T6.1 / T6.4.c tests that pinned the legacy
``operator override`` -only note shape (`test_manual_override.py`
×2, `test_streamlit_override_ui.py` ×1,
`test_subquote_tag_propagation.py` ×1) are updated in-place to
expect the new tag-at-position-0 contract; this file is the new
ground-truth for the contract.
"""

from __future__ import annotations

import re

import pytest

from core.estimator import (
    MANUAL_OVERRIDE_NOTE_PREFIX,
    SOURCE_TAG_MANUAL_OVERRIDE as ESTIMATOR_SOURCE_TAG_MANUAL_OVERRIDE,
    apply_manual_override,
    format_manual_override_note,
)
from core.pricing.batch_override import (
    SOURCE_TAG_BATCH,
    SOURCE_TAG_MANUAL_OVERRIDE,
    SOURCE_TAG_PATTERN,
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
)
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


# ---------------------------------------------------------------------------
# Fixtures (mirror :mod:`tests.test_manual_override` so the test surface
# is consistent with the T6.1 ground-truth file)
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
        project_name="T6.4.c.2 manual-override tag",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# Canonical-constant alignment — guards the circular-import-driven
# local mirror in ``core.estimator``.
# ---------------------------------------------------------------------------


def test_local_tag_constant_matches_canonical() -> None:
    """``core.estimator.SOURCE_TAG_MANUAL_OVERRIDE`` is a mirror of
    ``core.pricing.batch_override.SOURCE_TAG_MANUAL_OVERRIDE``
    (the project-wide canonical source-of-truth). The mirror exists
    because ``batch_override`` imports ``apply_manual_override`` from
    ``estimator`` at module load time, which would cause a circular
    import the other direction. The two constants MUST hold the same
    string literal; this test is the canary."""
    assert ESTIMATOR_SOURCE_TAG_MANUAL_OVERRIDE == SOURCE_TAG_MANUAL_OVERRIDE
    assert SOURCE_TAG_MANUAL_OVERRIDE == "[manual-override]"


# ---------------------------------------------------------------------------
# format_manual_override_note — pure-function unit tests
# ---------------------------------------------------------------------------


def test_formatter_bare_no_args_yields_minimal_tag_and_sentinel() -> None:
    """No ``unit_cost`` / ``qty`` / ``reason`` / ``prior_notes`` → minimal
    head: ``"[manual-override] operator override"`` (no trailing
    whitespace, no orphan colon)."""
    out = format_manual_override_note()
    assert out == f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}"
    assert not out.endswith(" ")
    assert not out.endswith(":")


def test_formatter_unit_cost_only_renders_bracketed_field() -> None:
    """``unit_cost=12.5`` → ``"[unit_cost: $12.50]"`` (2-decimal currency
    rendering, no orphan ``[qty: …]`` bracket)."""
    out = format_manual_override_note(unit_cost=12.5)
    assert out == (
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [unit_cost: $12.50]"
    )
    assert "[qty:" not in out


def test_formatter_qty_only_renders_bracketed_field() -> None:
    """``qty=42`` → ``"[qty: 42]"`` (``:g`` formatting strips trailing
    zeros; no orphan ``[unit_cost: …]`` bracket)."""
    out = format_manual_override_note(qty=42)
    assert out == (
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [qty: 42]"
    )
    assert "[unit_cost:" not in out


def test_formatter_both_fields_set_renders_both() -> None:
    """``unit_cost`` + ``qty`` together → both brackets in order."""
    out = format_manual_override_note(unit_cost=3.50, qty=100.0)
    assert out == (
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: "
        f"[unit_cost: $3.50] [qty: 100]"
    )


def test_formatter_neither_field_nor_reason_yields_bare_sentinel() -> None:
    out = format_manual_override_note(unit_cost=None, qty=None, reason="")
    assert out == f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}"


def test_formatter_empty_reason_no_trailing_whitespace() -> None:
    """An empty ``reason`` (after strip) does not introduce a trailing
    space or orphan colon — the head sits flush against the last
    bracket field."""
    out = format_manual_override_note(unit_cost=2.0, reason="   ")
    assert out == (
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [unit_cost: $2.00]"
    )
    assert not out.endswith(" ")


def test_formatter_reason_appears_verbatim() -> None:
    """The ``reason`` string is preserved verbatim (post-strip)."""
    out = format_manual_override_note(
        unit_cost=1.0,
        reason="Vendor will not warranty if quantity exceeds 100 LF",
    )
    assert "Vendor will not warranty if quantity exceeds 100 LF" in out
    assert out.endswith(
        "Vendor will not warranty if quantity exceeds 100 LF"
    )


def test_formatter_prior_notes_preserved_in_previous_suffix() -> None:
    """A non-empty ``prior_notes`` lands in the ``| previous: …`` suffix
    so an auditor can walk back through the override chain."""
    out = format_manual_override_note(
        unit_cost=4.0,
        prior_notes="[sub-quote] operator override: [csv-row: 3] Q-99",
    )
    assert out.startswith(
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [unit_cost: $4.00]"
    )
    assert (
        " | previous: [sub-quote] operator override: [csv-row: 3] Q-99"
        in out
    )


def test_formatter_idempotent_when_prior_equals_new_head() -> None:
    """When ``prior_notes`` already equals the new head string, the
    formatter short-circuits and returns ``prior_notes`` unchanged —
    no growing ``| previous: <same head>`` chain."""
    head = format_manual_override_note(unit_cost=3.0)
    again = format_manual_override_note(unit_cost=3.0, prior_notes=head)
    assert again == head
    assert " | previous: " not in again


def test_formatter_idempotent_when_prior_extends_same_head() -> None:
    """When ``prior_notes`` already starts with ``head + " | previous: "``,
    re-applying with the SAME head does not double-stamp the chain."""
    first = format_manual_override_note(
        unit_cost=3.0, prior_notes="legacy notes from CWICR"
    )
    second = format_manual_override_note(unit_cost=3.0, prior_notes=first)
    assert second == first


def test_formatter_chain_preserving_when_args_change() -> None:
    """Re-applying with DIFFERENT args → new head at position 0; the
    prior head moves to the ``| previous: …`` suffix (most-recent-
    wins with chain preservation)."""
    first = format_manual_override_note(unit_cost=3.0)
    second = format_manual_override_note(unit_cost=4.0, prior_notes=first)
    assert second.startswith(
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [unit_cost: $4.00]"
    )
    assert second.endswith(first)
    assert " | previous: " in second


def test_formatter_custom_source_tag_lands_at_position_0() -> None:
    """The ``source_tag`` kwarg is parametrised so a future calibration
    tier could pass e.g. ``"[manual-override-llm]"`` without a code
    change. The default lands ``SOURCE_TAG_MANUAL_OVERRIDE``."""
    out = format_manual_override_note(
        unit_cost=1.0, source_tag="[manual-override-llm]"
    )
    assert out.startswith("[manual-override-llm] ")


def test_formatter_default_source_tag_is_canonical_constant() -> None:
    """The formatter's default tag is the canonical
    :data:`SOURCE_TAG_MANUAL_OVERRIDE` constant (single source of
    truth across the override pipeline)."""
    assert SOURCE_TAG_MANUAL_OVERRIDE == "[manual-override]"
    out = format_manual_override_note()
    assert out.startswith(SOURCE_TAG_MANUAL_OVERRIDE + " ")


# ---------------------------------------------------------------------------
# apply_manual_override — integration with the new formatter
# ---------------------------------------------------------------------------


def test_apply_on_fresh_line_stamps_tag_at_position_0() -> None:
    """Bare ``apply_manual_override`` on a notes-less line → notes
    starts with ``"[manual-override] "``."""
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(est, 0, new_unit_cost=3.50)
    notes = out.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")


def test_apply_preserves_prior_batch_tag_in_previous_suffix() -> None:
    """When the prior ``notes`` already carries a ``[batch]`` tag (from
    a previous T6.3 batch apply), the manual override now stamps
    ``[manual-override]`` at position 0 and pushes the ``[batch]``
    head into the ``| previous: …`` suffix."""
    prior = f"{SOURCE_TAG_BATCH} {MANUAL_OVERRIDE_NOTE_PREFIX}: [csv-row: 5]"
    est = _estimate([_line(notes=prior)])
    out = apply_manual_override(est, 0, new_unit_cost=4.0)
    notes = out.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")
    assert f" | previous: {prior}" in notes


def test_apply_preserves_prior_subquote_tag_in_previous_suffix() -> None:
    """Same as above but with a ``[sub-quote]`` prior tag (T8.1
    propagation). The ``[sub-quote]`` head appears in the suffix
    only, never at position 0."""
    prior = (
        f"{SOURCE_TAG_SUBQUOTE_TABULAR} {MANUAL_OVERRIDE_NOTE_PREFIX}: "
        f"[vendor: Acme] [csv-row: 2]"
    )
    est = _estimate([_line(notes=prior)])
    out = apply_manual_override(est, 0, new_unit_cost=5.0)
    notes = out.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")
    head, sep, suffix = notes.partition(" | previous: ")
    assert sep == " | previous: "
    assert SOURCE_TAG_SUBQUOTE_TABULAR not in head
    assert suffix == prior


def test_apply_preserves_prior_subquote_llm_tag_in_previous_suffix() -> None:
    """Same shape with the T8.2 LLM-vision sub-quote tag."""
    prior = (
        f"{SOURCE_TAG_SUBQUOTE_LLM} {MANUAL_OVERRIDE_NOTE_PREFIX}: "
        f"[csv-row: 1]"
    )
    est = _estimate([_line(notes=prior)])
    out = apply_manual_override(est, 0, new_unit_cost=6.0)
    notes = out.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")
    assert f" | previous: {prior}" in notes


def test_apply_preserves_prior_vendor_csv_tag_in_previous_suffix() -> None:
    """Same shape with the T6.4.c.1 ``[vendor-csv]`` tag."""
    prior = (
        f"{SOURCE_TAG_VENDOR_CSV} {MANUAL_OVERRIDE_NOTE_PREFIX}: "
        f"[csv-row: 7]"
    )
    est = _estimate([_line(notes=prior)])
    out = apply_manual_override(est, 0, new_unit_cost=7.0)
    notes = out.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")
    assert f" | previous: {prior}" in notes


def test_reapply_over_prior_manual_override_keeps_tag_once_at_position_0() -> None:
    """Re-applying a manual override over a prior manual override yields
    a single ``[manual-override]`` at position 0; the prior head is
    captured in the ``| previous: …`` suffix (most-recent-wins,
    chain-preserving)."""
    est = _estimate([_line()])
    once = apply_manual_override(est, 0, new_unit_cost=3.00)
    twice = apply_manual_override(
        once, 0, new_unit_cost=4.00, operator_note="bumped"
    )
    notes = twice.line_items[0].notes or ""
    assert notes.startswith("[manual-override] ")
    # The tag may appear twice in the full string — once at position 0,
    # once inside the | previous: suffix — but the head BEFORE the
    # " | previous: " separator must contain it exactly once.
    head, _, _ = notes.partition(" | previous: ")
    assert head.count("[manual-override]") == 1


def test_reapply_same_args_is_idempotent_on_notes() -> None:
    """Applying the same override twice in a row yields byte-identical
    notes (the formatter's idempotency short-circuit fires)."""
    est = _estimate([_line(notes=None)])
    once = apply_manual_override(est, 0, new_unit_cost=3.50)
    twice = apply_manual_override(once, 0, new_unit_cost=3.50)
    assert twice.line_items[0].notes == once.line_items[0].notes


def test_apply_empty_reason_no_trailing_whitespace() -> None:
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(
        est, 0, new_unit_cost=3.0, operator_note=""
    )
    notes = out.line_items[0].notes or ""
    assert not notes.endswith(" ")
    assert not notes.endswith(":")


def test_apply_reason_appears_verbatim_in_notes() -> None:
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(
        est, 0, new_unit_cost=3.0,
        operator_note="Vendor will not warranty if quantity exceeds 100 LF",
    )
    notes = out.line_items[0].notes or ""
    assert "Vendor will not warranty if quantity exceeds 100 LF" in notes


def test_apply_unit_cost_renders_two_decimal_currency() -> None:
    """``new_unit_cost=12.5`` → ``"[unit_cost: $12.50]"`` in the notes
    (currency rendering matches the formatter's contract)."""
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(est, 0, new_unit_cost=12.5)
    notes = out.line_items[0].notes or ""
    assert "[unit_cost: $12.50]" in notes


def test_apply_notes_match_canonical_source_tag_pattern() -> None:
    """The notes string starts with a token matching the project-wide
    canonical :data:`SOURCE_TAG_PATTERN` regex (``r"^\\[[a-z][a-z\\-]*\\] "``).
    This pins the structural contract independently of which specific
    tag is in use, so a future tag rename is caught."""
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    notes = out.line_items[0].notes or ""
    assert re.match(SOURCE_TAG_PATTERN, notes) is not None


def test_apply_tag_appears_exactly_once_at_position_0() -> None:
    """For a single override on a clean line, ``[manual-override]``
    appears exactly once in the notes string and it is at position 0
    (no duplication from defensive double-stamping)."""
    est = _estimate([_line(notes=None)])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    notes = out.line_items[0].notes or ""
    assert notes.count("[manual-override]") == 1
    assert notes.startswith("[manual-override] ")


# ---------------------------------------------------------------------------
# T6.1 contract preservation — the new tag stamping must NOT regress
# any pre-T6.4.c.2 behaviour of :func:`apply_manual_override`.
# ---------------------------------------------------------------------------


def test_apply_still_stamps_manual_override_tier() -> None:
    """Post-T6.4.c.2 the line tier is still
    :attr:`CostSourceTier.MANUAL_OVERRIDE` (pinned by T6.1)."""
    est = _estimate([_line()])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    assert out.line_items[0].cost_source_tier == CostSourceTier.MANUAL_OVERRIDE


def test_apply_still_forces_price_confidence_to_one() -> None:
    """Manual override still forces ``price_confidence`` to 1.0 — the
    operator vouches for the number (pinned by T6.1)."""
    est = _estimate([_line(price_confidence=0.42)])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    assert out.line_items[0].price_confidence == pytest.approx(1.0)


def test_apply_still_recomputes_combined_band() -> None:
    """``cost_band`` is still recomputed from the new
    ``combined_confidence`` (qty × 1.0) post-override; suppressed
    flag still cleared. Pinned by T6.1."""
    est = _estimate([_line(
        confidence=0.92,
        tier=CostSourceTier.MISSING,
        band=CostBand.HAND_TAKEOFF,
        suppressed=True,
    )])
    out = apply_manual_override(est, 0, new_unit_cost=4.20)
    li = out.line_items[0]
    assert li.suppressed is False
    # 0.92 qty × 1.0 price = 0.92 → AUTO_APPROVE.
    assert li.cost_band == CostBand.AUTO_APPROVE
