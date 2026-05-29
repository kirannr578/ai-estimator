"""Streamlit UI for the Construction Plan Estimator.

Run with:

    streamlit run app.py

Workflow:
  1. Upload one or more PDFs (drag and drop in sidebar).
  2. Configure provider, region multiplier, OH&P, contingency.
  3. Click 'Analyze plan set' - the app:
     - splits each PDF into sheets and renders them,
     - classifies each sheet (discipline + type),
     - extracts structured takeoffs in parallel,
     - reconciles cross-sheet duplicates,
     - prices everything against the cost database.
  4. Review results across tabs (Estimate, Sheets, Rooms, Doors/Windows,
     Specs, Raw takeoffs, Warnings).
  5. Edit unit costs / quantities / OH&P live and re-price.
  6. Download Excel and JSON.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from collections import OrderedDict
from collections.abc import Mapping
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from core.estimator import (
    MANUAL_OVERRIDE_NOTE_PREFIX,
    CostDatabase,
    apply_manual_override,
    attach_alternates_to_estimate,
    price_takeoff,
    revert_last_override_in_estimate,
)
from core.exporter import export_estimate_json, export_estimate_xlsx
from core.extractors import extract_bundle, extract_sheet
from core.llm_client import LLMClient
from core.pdf_processor import DocumentBundle, process_pdfs
from core.pricing.batch_override import (
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    apply_batch_plan,
    export_match_plan_csv,
    format_batch_operator_note,
    match_cost_lines,
    parse_vendor_csv,
)
from core.pricing.subquote_parser import (
    SubquoteLLMError,
    SubquoteMetadata,
    SubquoteParseError,
    SubquoteParseResult,
    apply_subquote_plan,
    parse_subquote_pdf,
    parse_subquote_pdf_with_llm,
)
from core.pricing.xlsx_parser import (
    merge_xlsx_plans,
    parse_vendor_xlsx,
)
from core.schemas import (
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    ClientInfo,
    CompanyInfo,
    CostLine,
    CostLineOverrideSnapshot,
    CostSourceTier,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    Sheet,
    SheetExtraction,
)


# Phase T7 — display labels for the catalog-completeness tiers, mirroring
# ``core.exporter._TIER_LABELS`` so the UI and Excel export agree exactly
# on user-visible strings.
_T7_TIER_LABELS: dict[CostSourceTier, str] = {
    CostSourceTier.EXACT_MATCH: "Exact Match",
    CostSourceTier.CATEGORY_MATCH: "Category Match",
    CostSourceTier.INTERPOLATED: "Interpolated",
    CostSourceTier.PARAMETRIC: "Parametric",
    CostSourceTier.MANUAL_OVERRIDE: "Manual Override",
    CostSourceTier.MISSING: "Missing",
}


def _t7_tier_label(li) -> str:
    """Resolve the display label for a CostLine's ``cost_source_tier``."""
    tier = getattr(li, "cost_source_tier", CostSourceTier.EXACT_MATCH)
    if isinstance(tier, CostSourceTier):
        return _T7_TIER_LABELS[tier]
    try:
        return _T7_TIER_LABELS[CostSourceTier(tier)]
    except Exception:
        return str(tier)


# ---------------------------------------------------------------------------
# Phase T6.2 — Operator override UI helpers (pure functions, easy to test)
# ---------------------------------------------------------------------------
#
# The helpers below back the "Operator price overrides" affordance in the
# Estimate tab. They are intentionally pure (no Streamlit calls, no
# session-state reads) so the test suite can exercise them without
# spinning up an ``AppTest`` harness — Streamlit's testing facility does
# not yet cleanly support form-submit round-trips against a heavy app
# like this one. The Streamlit form below is a thin wrapper that
# (1) collects the operator's input, (2) hands it to ``_apply_operator_override``,
# and (3) renders the result.

# Sort order for the line-selector dropdown. MANUAL_OVERRIDE first so an
# operator who already touched a row can find it immediately, then the
# remaining tiers in descending catalog-completeness quality (EXACT first,
# MISSING last). Any unknown tier falls through to the bottom.
_TIER_SORT_ORDER: dict[CostSourceTier, int] = {
    CostSourceTier.MANUAL_OVERRIDE: 0,
    CostSourceTier.EXACT_MATCH: 1,
    CostSourceTier.CATEGORY_MATCH: 2,
    CostSourceTier.INTERPOLATED: 3,
    CostSourceTier.PARAMETRIC: 4,
    CostSourceTier.MISSING: 5,
}


def _format_operator_note(
    vendor: str | None,
    quote_ref: str | None,
    free_text: str | None,
) -> str | None:
    """Combine vendor / quote-ref / free-text into one operator-note string.

    Format::

        [vendor: <vendor>] [quote-ref: <quote_ref>] <free_text>

    Empty / whitespace-only fields are skipped. If all three are empty
    the function returns ``None`` so the caller can pass it straight to
    ``apply_manual_override`` (which treats ``None`` as "no note" but
    still stamps the ``MANUAL_OVERRIDE`` sentinel).
    """
    parts: list[str] = []
    v = (vendor or "").strip()
    q = (quote_ref or "").strip()
    t = (free_text or "").strip()
    if v:
        parts.append(f"[vendor: {v}]")
    if q:
        parts.append(f"[quote-ref: {q}]")
    if t:
        parts.append(t)
    if not parts:
        return None
    return " ".join(parts)


def _select_line_label(idx: int, line: CostLine) -> str:
    """Human-readable label for the override line-selector dropdown.

    Format: ``#<idx> | <description, truncated> | $<unit_cost>/<unit> | <tier>``.

    The leading ``#<idx>`` is the stable line identifier the override
    pass uses (CostLine has no ``entity_id`` field per the T7 schema),
    so the operator can always disambiguate two visually-similar rows
    by their position.
    """
    desc = (line.description or "").strip() or "(no description)"
    if len(desc) > 60:
        desc = desc[:57] + "..."
    tier_label = _t7_tier_label(line)
    unit = (line.unit or "").strip() or "?"
    return f"#{idx} | {desc} | ${line.unit_cost:,.2f}/{unit} | {tier_label}"


def _sort_lines_by_tier(
    lines: list[CostLine],
) -> list[tuple[int, CostLine]]:
    """Stable-sort ``(index, line)`` pairs by tier preference.

    MANUAL_OVERRIDE first (so an operator who already touched a row
    finds it at the top), then EXACT → CATEGORY → INTERPOLATED →
    PARAMETRIC → MISSING. Stable-sorted on the original index so two
    rows in the same tier preserve their physical order in the
    estimate.
    """
    indexed = list(enumerate(lines))
    indexed.sort(
        key=lambda pair: (
            _TIER_SORT_ORDER.get(pair[1].cost_source_tier, 99),
            pair[0],
        )
    )
    return indexed


def _format_override_delta(
    old_estimate: Estimate,
    new_estimate: Estimate,
    line_idx: int,
) -> str:
    """Human-readable delta string for an override application.

    Surfaces three deltas the operator wants to see post-submit: the
    line's unit-cost change, the line's total-cost change, and the
    estimate-level subtotal change. Money formatted with thousands
    separators + 2dp; uses an arrow glyph (``→``) so the diff reads
    naturally.
    """
    old_line = old_estimate.line_items[line_idx]
    new_line = new_estimate.line_items[line_idx]
    return (
        f"Unit cost: ${old_line.unit_cost:,.2f} \u2192 ${new_line.unit_cost:,.2f}  |  "
        f"Line total: ${old_line.total_cost:,.2f} \u2192 ${new_line.total_cost:,.2f}  |  "
        f"Subtotal: ${old_estimate.subtotal:,.2f} \u2192 ${new_estimate.subtotal:,.2f}"
    )


def _apply_operator_override(
    estimate: Estimate,
    line_idx: int,
    new_unit_cost: float,
    vendor: str | None = None,
    quote_ref: str | None = None,
    free_text: str | None = None,
) -> tuple[Estimate, str | None]:
    """Format the operator-note + apply the override; returns ``(new_estimate, note)``.

    Pure wrapper around :func:`core.estimator.apply_manual_override`.
    Factored out of the Streamlit form so the round-trip can be tested
    without an ``AppTest`` harness. Re-raises ``ValueError`` from the
    underlying override pass unchanged so the UI layer can surface a
    clean ``st.error`` rather than a stack trace.
    """
    note = _format_operator_note(vendor, quote_ref, free_text)
    new_est = apply_manual_override(
        estimate,
        line_idx,
        new_unit_cost=new_unit_cost,
        operator_note=note,
    )
    return new_est, note


def _build_override_history_csv(history: list[dict[str, Any]]) -> str:
    """Serialise the override-history list to CSV for download.

    Empty history → header-only CSV (still a valid file, downloaded
    artifact tells the operator there are no overrides yet).
    """
    fieldnames = [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in history:
        writer.writerow(row)
    return buf.getvalue()


def _initialize_override_session_state(estimate: Estimate) -> None:
    """Populate the override-related session-state keys for a fresh estimate.

    Called once when a new estimate is built (analyze run) — captures
    a deep copy of the pre-override estimate for delta / reset, and
    seeds an empty history. Idempotent under repeat calls when an
    estimate already has snapshots: the brief specifies "populate once",
    but repeat calls (e.g. on an analysis re-run with the same run-id)
    overwrite the snapshot with the current estimate, which is the
    expected behaviour for a fresh analyze pass.
    """
    st.session_state["estimate_original"] = estimate.model_copy(deep=True)
    st.session_state["override_history"] = []


# ---------------------------------------------------------------------------
# Phase T6.4.d — per-line undo UI helpers (pure functions, easy to test)
# ---------------------------------------------------------------------------
#
# Per-line revert lets an operator who clicked "Apply" on a 200-row
# vendor batch roll back line 47 alone, without resetting the whole
# estimate via the T6.2 global "Reset all overrides" button. The
# affordance is rendered as a "↶ revert" button next to every line
# whose ``override_snapshots`` stack is non-empty; clicking it pops
# the stack-top snapshot via :func:`revert_last_override_in_estimate`
# and re-renders.
#
# The helpers below are pure (no Streamlit calls, no session-state
# reads) so the test suite can exercise them without an ``AppTest``
# harness — same convention as the T6.2 / T6.3 helpers above.


def _format_snapshot_label(snapshot: CostLineOverrideSnapshot) -> str:
    """Human-readable single-line label for one override snapshot.

    Used by the revert toast and the per-line "show undo history"
    expander. Format::

        ``<source-tag> @ <HH:MM UTC> $<unit_cost>/unit``

    Empty source tag (no leading provenance — i.e. the snapshot
    captures the priced-from-cost-DB defaults) renders as
    ``"(priced default)"`` so an operator never sees a bare ``@``.
    The timestamp is formatted as HH:MM (UTC) — the operator's
    mental model is "I clicked Apply about 5 minutes ago", not
    "I clicked Apply on 2026-05-28T19:15:42".
    """
    tag = snapshot.source_tag or "(priced default)"
    ts = snapshot.applied_at
    try:
        when = ts.strftime("%H:%M UTC")
    except Exception:
        when = "?"
    return f"{tag} @ {when}  \u2014  ${snapshot.unit_cost:,.2f}/unit"


def _build_revert_history_rows(
    line: CostLine,
    line_index: int,
) -> list[dict[str, Any]]:
    """Project the line's snapshot stack into UI-renderable dict rows.

    Returns one dict per snapshot in stack order (oldest first). The
    Streamlit "show undo history" expander renders this list as a
    table; the test suite asserts the projection matches the
    underlying snapshots exactly.
    """
    rows: list[dict[str, Any]] = []
    for depth, snap in enumerate(line.override_snapshots):
        rows.append({
            "Line #": line_index,
            "Depth": depth,
            "Source tag": snap.source_tag or "(priced default)",
            "Captured (UTC)": snap.applied_at.isoformat(timespec="seconds"),
            "Unit cost": round(float(snap.unit_cost), 2),
            "Total cost": round(float(snap.total_cost), 2),
            "Tier": (
                snap.cost_source_tier.value
                if isinstance(snap.cost_source_tier, CostSourceTier)
                else str(snap.cost_source_tier)
            ),
        })
    return rows


def _apply_per_line_revert(
    estimate: Estimate,
    line_index: int,
) -> tuple[Estimate, CostLineOverrideSnapshot | None]:
    """Pure wrapper around :func:`revert_last_override_in_estimate`.

    Same signature contract as the T6.2 ``_apply_operator_override``
    helper: takes an estimate + a target index, returns
    ``(new_estimate, popped_snapshot)``. Returns ``(estimate, None)``
    when the targeted line has no snapshots — the UI uses ``None`` as
    the "nothing to revert" signal and skips the toast.

    Pure — no Streamlit calls. Tested directly in
    ``tests/test_streamlit_undo_ui.py``.
    """
    return revert_last_override_in_estimate(estimate, line_index)


def _revertable_line_indices(estimate: Estimate) -> list[int]:
    """Return the 0-based indices of every line with at least one snapshot.

    Used by the bulk-revert affordance to iterate "every line that
    can be rolled back" without redundantly checking the snapshot
    list inside the apply loop. Stable order — matches
    ``estimate.line_items``.
    """
    return [
        i for i, li in enumerate(estimate.line_items)
        if li.override_snapshots
    ]


def _bulk_revert_all(
    estimate: Estimate,
) -> tuple[Estimate, list[CostLineOverrideSnapshot]]:
    """Revert the most-recent override on every line that has one.

    Returns the new estimate plus the list of popped snapshots in
    the order the reverts ran. Lines without snapshots are
    untouched. Useful when an operator applied the wrong CSV to
    200 lines and wants to undo all of them in one click.

    Reverts are idempotent in aggregate: applying the same plan
    twice + bulk-revert reverts only the SECOND apply layer; the
    first layer's snapshots stay intact and are recoverable via a
    second bulk-revert call.
    """
    current = estimate
    popped: list[CostLineOverrideSnapshot] = []
    for idx in _revertable_line_indices(current):
        current, snap = revert_last_override_in_estimate(current, idx)
        if snap is not None:
            popped.append(snap)
    return current, popped


# ---------------------------------------------------------------------------
# Phase T6.3 — Batch operator override helpers
# ---------------------------------------------------------------------------
#
# Two pure helpers wrap the ``core.pricing.batch_override`` module for the
# Streamlit UI. The first summarises a match plan (counts + dollar adjustment
# estimate) for the preview pane. The second turns a list of applied
# ``BatchMatchResult`` into history rows compatible with the existing T6.2
# override-history download.


def _summarize_batch_plan(
    plan: BatchOverridePlan,
    estimate: Estimate | None = None,
) -> dict[str, Any]:
    """Aggregate a :class:`BatchOverridePlan` into UI-friendly counts + totals.

    Returns a dict with::

        total_rows            int   — sum of every bucket
        matched_count         int
        ambiguous_count       int
        no_match_count        int
        low_similarity_count  int
        similarity_threshold  float
        ambiguity_margin      float
        estimated_total_adjustment  float   — when ``estimate`` is supplied;
                                              0.0 otherwise. The dollar
                                              delta that auto-applying every
                                              MATCHED row would land, NOT
                                              including operator-resolved
                                              ambiguous rows.

    Pure / side-effect-free so the unit tests don't need a Streamlit
    harness. The Streamlit caller uses the same dict to render the
    summary metrics row in the preview pane.
    """
    out: dict[str, Any] = {
        "total_rows": plan.total_rows,
        "matched_count": len(plan.matched),
        "ambiguous_count": len(plan.ambiguous),
        "no_match_count": len(plan.no_match),
        "low_similarity_count": len(plan.low_similarity),
        "similarity_threshold": plan.similarity_threshold,
        "ambiguity_margin": plan.ambiguity_margin,
        "estimated_total_adjustment": 0.0,
    }
    if estimate is None:
        return out

    adj = 0.0
    for result in plan.matched:
        if result.best_match_index is None:
            continue
        if not 0 <= result.best_match_index < len(estimate.line_items):
            continue
        line = estimate.line_items[result.best_match_index]
        old_total = round(float(line.unit_cost) * float(line.quantity), 2)
        new_total = round(float(result.row.unit_cost) * float(line.quantity), 2)
        adj += new_total - old_total
    out["estimated_total_adjustment"] = round(adj, 2)
    return out


def _format_batch_csv_for_history(
    plan: BatchOverridePlan,
    applied_rows: list[BatchMatchResult],
) -> str:
    """Serialise applied batch rows into a CSV body with [batch]-tagged notes.

    Format mirrors :func:`_build_override_history_csv` (same eight
    column names) so a downstream auditor can concatenate the batch
    history block with the single-line history block without juggling
    schemas. The ``operator_note`` column always starts with
    ``[batch] ...`` via :func:`format_batch_operator_note`.

    ``applied_rows`` should be the subset of ``plan.matched`` (plus any
    operator-resolved ``plan.ambiguous`` rows) that were actually
    applied — not the full plan. Rows are emitted in ``row.row_index``
    order so the CSV reads the same direction as the source spreadsheet.
    """
    fieldnames = [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    ordered = sorted(applied_rows, key=lambda r: r.row.row_index)
    for result in ordered:
        note = format_batch_operator_note(result.row)
        writer.writerow({
            "timestamp": "",
            "line_index": (
                result.best_match_index
                if result.best_match_index is not None
                else ""
            ),
            "description": result.row.description,
            "csi_division": "",
            "csi_section": "",
            "original_unit_cost": "",
            "new_unit_cost": round(float(result.row.unit_cost), 2),
            "operator_note": note,
        })
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Phase T8.1 — Sub-quote PDF ingestion helpers
# ---------------------------------------------------------------------------
#
# Two pure helpers wrap the ``core.pricing.subquote_parser`` module for
# the Streamlit Sub-quote PDF expander. The first renders the parsed
# metadata banner; the second produces a CSV-string preview of the
# extracted rows so the operator can save → re-import as CSV via the
# T6.3 uploader if they want to. Pure / Streamlit-free / unit-testable.


def _render_subquote_metadata(metadata: SubquoteMetadata) -> str:
    """Render a sub-quote metadata block as Markdown.

    Returns a Markdown string ready to drop into ``st.markdown(...)``.
    Pure — no Streamlit dependency, fully unit-testable.

    The block always starts with a "**Sub-quote metadata**" heading so
    the UI can render the same block in two places (preview pane,
    history download) without duplicating the layout. Empty / unknown
    fields are omitted entirely rather than rendered as "Unknown" — a
    too-noisy fallback would obscure the fields that ARE present.
    """
    lines: list[str] = ["**Sub-quote metadata**"]
    if metadata.vendor_name:
        lines.append(f"- Vendor: `{metadata.vendor_name}`")
    if metadata.quote_number:
        lines.append(f"- Quote #: `{metadata.quote_number}`")
    if metadata.quote_date:
        lines.append(f"- Date: `{metadata.quote_date}`")
    if metadata.project_reference:
        lines.append(f"- Project: `{metadata.project_reference}`")
    if metadata.total_quoted is not None:
        lines.append(f"- Quote total: `${metadata.total_quoted:,.2f}`")
    if metadata.detected_pages:
        page_list = ", ".join(str(p) for p in metadata.detected_pages)
        lines.append(f"- Table pages: `{page_list}`")
    lines.append(
        f"- Metadata confidence: `{metadata.confidence:.0%}`"
    )
    return "\n".join(lines)


def _subquote_to_csv_preview(result: SubquoteParseResult) -> str:
    """Render the parsed sub-quote rows as a CSV string.

    Column order is the canonical T6.3 vendor-CSV layout
    (``description, unit_cost, quantity, vendor, quote_ref, notes``)
    so an operator who wants to save the PDF parse to disk can
    re-import via the existing T6.3 CSV uploader without column
    fiddling. Round-tripping the CSV string through
    :func:`core.pricing.batch_override.parse_vendor_csv` reproduces
    the same :class:`BatchOverrideRow` list this helper started with
    (pinned by ``test_subquote_csv_roundtrip_through_csv_parser``).

    Empty :class:`SubquoteParseResult` returns the header-only CSV.
    """
    buf = io.StringIO()
    fieldnames = [
        "description",
        "unit_cost",
        "quantity",
        "vendor",
        "quote_ref",
        "notes",
    ]
    writer = csv.DictWriter(buf, fieldnames=fieldnames)
    writer.writeheader()
    for row in result.rows:
        writer.writerow({
            "description": row.description,
            "unit_cost": f"{row.unit_cost:.4f}",
            "quantity": "" if row.quantity is None else f"{row.quantity:g}",
            "vendor": row.vendor or "",
            "quote_ref": row.quote_ref or "",
            "notes": row.notes or "",
        })
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Phase T8.2 — LLM-vision fallback UI helpers
# ---------------------------------------------------------------------------
#
# Two pure helpers wrap the T8.2 LLM-vision fallback path for the
# Streamlit Sub-quote PDF expander. The first builds the cost-estimate
# disclosure shown above the "Try LLM extraction" button — it's the
# only LLM-spending button in the override flow, so operator awareness
# matters and the text needs to be reproducible. The second renders a
# short banner identifying the LLM-extracted result so an operator
# reviewing the preview-table can tell it came from the vision model
# rather than the deterministic table parse.
#
# Cost figures derive from the actual 2026-Q2 pricing of the two
# vision providers ``core.llm_client.LLMClient`` supports:
#
#   * Anthropic Claude Sonnet vision: input $3/MTok, output $15/MTok.
#     A 200-DPI US Letter page renders to ~1.7 megapixels which the
#     Anthropic tokenizer charges as ~5,000 input tokens. Output is
#     ~500 tokens of JSON. Per-page: ~$0.018 in + $0.008 out = ~$0.03.
#   * OpenAI GPT-4o vision: input $2.5/MTok, output $10/MTok. A
#     200-DPI page at "high" detail tokenises to ~1,200 input tokens;
#     output is ~500 tokens. Per-page: ~$0.003 in + $0.005 out = ~$0.01.
#
# The displayed range $0.02-$0.10 / page covers both providers AND
# bounds the worst-case (a dense numerical schedule that pushes the
# output-token count high). The 10-page cap means the operator's
# absolute worst case is ~$1.00 per click.


def _render_subquote_llm_cost_estimate(
    *,
    max_pages: int = 10,
    per_page_low_usd: float = 0.02,
    per_page_high_usd: float = 0.10,
) -> str:
    """Render the cost-estimate caption for the "Try LLM extraction" button.

    Returns a one-line string ready to drop into ``st.caption(...)``.
    Pure — no Streamlit dependency, no LLM call, fully unit-testable.

    The string spells out per-page cost AND the absolute worst-case
    upper bound (``per_page_high_usd * max_pages``) so the operator
    sees both numbers before clicking. The button is the only LLM-
    spending affordance in the override flow, so this disclosure is
    a hard UX requirement, not a "nice-to-have".

    Args:
        max_pages: The page cap honoured by
            :func:`core.pricing.subquote_parser.parse_subquote_pdf_with_llm`
            (defaults to 10 — same as the parser default).
        per_page_low_usd: Lower bound of the per-page cost estimate.
            Defaults to $0.02 (calibrated against GPT-4o input pricing).
        per_page_high_usd: Upper bound of the per-page cost estimate.
            Defaults to $0.10 (calibrated against Claude Sonnet output
            pricing on dense numerical pages).
    """
    low_total = per_page_low_usd * max_pages
    high_total = per_page_high_usd * max_pages
    return (
        f"Estimated cost: ~${per_page_low_usd:.2f}\u2013${per_page_high_usd:.2f} "
        f"per page, capped at {max_pages} pages "
        f"(worst case ~${low_total:.2f}\u2013${high_total:.2f} per click)."
    )


def _render_subquote_llm_source_banner(
    metadata: SubquoteMetadata | None = None,
) -> str:
    """Render a one-line banner identifying an LLM-extracted result.

    Returns a short Markdown string the UI prepends to the standard
    metadata block when the active :class:`SubquoteParseResult` came
    from :func:`parse_subquote_pdf_with_llm` rather than the
    deterministic table parse. Distinguishing the two in the UI
    matters because (a) the LLM result has a different confidence
    profile (page-share vs. metadata-share) and (b) the operator
    should know the audit trail will tag rows as ``[sub-quote-llm]``
    rather than ``[sub-quote]``.

    Pure — no Streamlit, no LLM, no I/O. ``metadata`` is accepted but
    optional; the banner does not currently format any metadata fields
    into the line, but the parameter is wired so future calibration
    can surface page count / confidence next to the source label
    without changing the UI call site.
    """
    return (
        "**LLM-extracted (page-by-page vision).** The deterministic "
        "table parser failed; rows below were extracted by the vision "
        "LLM. Audit-trail rows will be tagged `[sub-quote-llm]`."
    )


# ---------------------------------------------------------------------------
# Phase T9.1 — Streamlit "Bid Alternates" review tab helpers
# ---------------------------------------------------------------------------
#
# Pure helpers wrapping the T9.0 backend so the alternates review tab can be
# tested without a Streamlit harness. Same pattern as T6.2 (override UI):
# every Streamlit-side function delegates to a pure helper that takes the
# raw Pydantic model in and emits a string / dict / list out — the
# Streamlit form glue (``st.checkbox``, ``st.number_input``, ...) is
# transitively unit-tested via the helpers, and a smoke import of
# ``app.py`` confirms the form wiring parses.
#
# Public surface:
#
# * :func:`_alternate_type_label` / :func:`_alternate_basis_label` —
#   user-visible labels matching ``core.exporter`` exactly.
# * :func:`_format_alternate_type_badge` — type badge with a colour hint
#   for the Streamlit markdown surface.
# * :func:`_format_cost_delta` — signed dollar string with proper sign
#   per ``AlternateType``; em-dash for MISSING (None) deltas.
# * :func:`_compute_alternates_summary` — by-type aggregates (count + sum
#   of resolved deltas) for the header banner.
# * :func:`_alternates_to_csv` — CSV export including selection state and
#   in-session operator notes overlay.
# * :func:`_resolve_bid_package_title` — FK resolution from
#   ``bid_package_id`` to a human-readable title; handles None / unknown.
# * :func:`_initialize_alternates_session_state` — idempotent seeding of
#   the three new session-state keys; resets on a new estimate identity.
# * :func:`_apply_alternate_operator_entry` — pure functional update for
#   a MISSING-basis alternate: returns a new list with the entered delta
#   applied + ``OPERATOR_ENTERED`` basis. Sign mismatch (ADDITIVE with
#   negative delta, DEDUCTIVE with positive delta) emits a soft warning
#   string but still applies, mirroring the T9.0 backend
#   ``AlternateLine._validate_sign_consistency`` behaviour.

_ALTERNATE_TYPE_LABELS_UI: dict[AlternateType, str] = {
    AlternateType.ADDITIVE: "Additive",
    AlternateType.DEDUCTIVE: "Deductive",
    AlternateType.SUBSTITUTION: "Substitution",
    AlternateType.VE: "Value Engineering",
}

# Streamlit native ``:colour[text]`` markdown spans (Streamlit ≥1.27)
# render coloured pills in regular markdown. Falling back to plain
# parenthesised tags if the host Streamlit is older still produces a
# usable label — the colour is purely cosmetic.
_ALTERNATE_TYPE_BADGE_COLOURS: dict[AlternateType, str] = {
    AlternateType.ADDITIVE: "green",
    AlternateType.DEDUCTIVE: "red",
    AlternateType.SUBSTITUTION: "orange",
    AlternateType.VE: "blue",
}

_ALTERNATE_BASIS_LABELS_UI: dict[AlternatePricingBasis, str] = {
    AlternatePricingBasis.EXTRACTED_FROM_BID_FORM: "Extracted (bid form)",
    AlternatePricingBasis.OPERATOR_ENTERED: "Operator entered",
    AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF: "Synthesized (takeoff)",
    AlternatePricingBasis.MISSING: "Missing — review",
}

_ALTERNATE_BASIS_TOOLTIPS: dict[AlternatePricingBasis, str] = {
    AlternatePricingBasis.EXTRACTED_FROM_BID_FORM: (
        "Cost delta was printed on the bid form and parsed verbatim."
    ),
    AlternatePricingBasis.OPERATOR_ENTERED: (
        "Cost delta was hand-entered by an operator (this UI or a "
        "vendor / sub quote outside the bid-form path)."
    ),
    AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF: (
        "Cost delta was computed by summing priced takeoff items "
        "referenced by the alternate (related_takeoff_items)."
    ),
    AlternatePricingBasis.MISSING: (
        "No cost delta and no related takeoff items — operator "
        "review required before submitting the bid."
    ),
}


def _alternate_type_label(t: AlternateType | str) -> str:
    """Title-case label for an :class:`AlternateType` (mirrors exporter)."""
    if isinstance(t, AlternateType):
        return _ALTERNATE_TYPE_LABELS_UI[t]
    try:
        return _ALTERNATE_TYPE_LABELS_UI[AlternateType(t)]
    except (ValueError, KeyError):
        return str(t)


def _alternate_basis_label(basis: AlternatePricingBasis | str) -> str:
    """Title-case label for an :class:`AlternatePricingBasis` (mirrors exporter)."""
    if isinstance(basis, AlternatePricingBasis):
        return _ALTERNATE_BASIS_LABELS_UI[basis]
    try:
        return _ALTERNATE_BASIS_LABELS_UI[AlternatePricingBasis(basis)]
    except (ValueError, KeyError):
        return str(basis)


def _format_alternate_type_badge(t: AlternateType | str) -> str:
    """Render a colour-coded ``:colour[Title]`` Streamlit markdown badge.

    Returns a single-line markdown string suitable for ``st.markdown``.
    Falls back to plain ``[Label]`` when the type is not a known
    :class:`AlternateType` value.
    """
    try:
        atype = t if isinstance(t, AlternateType) else AlternateType(t)
    except (ValueError, KeyError):
        return f"[{t}]"
    label = _ALTERNATE_TYPE_LABELS_UI[atype]
    colour = _ALTERNATE_TYPE_BADGE_COLOURS[atype]
    return f":{colour}[{label}]"


def _format_cost_delta(
    delta: float | None,
    alt_type: AlternateType | str | None = None,
) -> str:
    """Format a signed dollar amount per :class:`AlternateType` convention.

    * ``None`` → ``"$_____"`` (the bid-form blank placeholder; signals
      MISSING basis to the operator).
    * Positive  → ``"+$X,XXX.XX"``
    * Negative  → ``"-$X,XXX.XX"`` (the unary minus and `$` flip so the
      sign reads as "$-X" colloquially; we use `-$X` for readability).
    * Zero      → ``"$0.00"`` (no sign prefix).

    ``alt_type`` is accepted for API symmetry with the brief but does not
    change the formatting — the sign is taken from the resolved delta
    itself, matching the T9.0 backend convention where every cost_delta
    is already signed.
    """
    if delta is None:
        return "$_____"
    try:
        amount = float(delta)
    except (TypeError, ValueError):
        return "$_____"
    if amount > 0:
        return f"+${amount:,.2f}"
    if amount < 0:
        return f"-${abs(amount):,.2f}"
    return "$0.00"


def _compute_alternates_summary(
    alternates: list[AlternateLineEstimate],
) -> dict[str, dict[str, Any]]:
    """Aggregate priced alternates into UI-friendly per-type metrics.

    Returns a dict keyed by the :class:`AlternateType` *string value* so
    the Streamlit caller can iterate without re-importing the enum::

        {
            "additive": {"count": int, "total_delta": float, "missing_count": int},
            "deductive": {...},
            "substitution": {...},
            "value_engineering": {...},
            "all": {"count": int, "total_delta": float, "missing_count": int},
        }

    ``total_delta`` is the sum of *resolved* (non-None) ``cost_delta``
    values for that bucket; ``missing_count`` is the number of priced
    alternates whose pricing basis is ``MISSING`` (which always implies
    ``cost_delta is None``).
    """
    out: dict[str, dict[str, Any]] = {
        t.value: {"count": 0, "total_delta": 0.0, "missing_count": 0}
        for t in AlternateType
    }
    out["all"] = {"count": 0, "total_delta": 0.0, "missing_count": 0}

    for a in alternates or []:
        atype = a.alternate_type
        if isinstance(atype, AlternateType):
            key = atype.value
        else:
            try:
                key = AlternateType(atype).value
            except (ValueError, KeyError):
                continue
        out[key]["count"] += 1
        out["all"]["count"] += 1

        if a.cost_delta is not None:
            out[key]["total_delta"] = round(
                out[key]["total_delta"] + float(a.cost_delta), 2
            )
            out["all"]["total_delta"] = round(
                out["all"]["total_delta"] + float(a.cost_delta), 2
            )

        # ``MISSING`` basis is the canonical "needs operator attention"
        # signal — surfaced separately from cost_delta-is-None because a
        # future basis (OPERATOR_ENTERED with a still-None delta) would
        # not necessarily mean "missing".
        basis = a.pricing_basis
        if isinstance(basis, AlternatePricingBasis):
            is_missing = basis == AlternatePricingBasis.MISSING
        else:
            try:
                is_missing = (
                    AlternatePricingBasis(basis) == AlternatePricingBasis.MISSING
                )
            except (ValueError, KeyError):
                is_missing = False
        if is_missing:
            out[key]["missing_count"] += 1
            out["all"]["missing_count"] += 1

    return out


def _alternates_to_csv(
    alternates: list[AlternateLineEstimate],
    selected_ids: set[str] | None = None,
    operator_notes_map: dict[str, str] | None = None,
) -> str:
    """Render priced alternates + selection state as a CSV string.

    Columns (stable contract; tested by ``test_alternates_to_csv_*``)::

        alternate_id, type, description, cost_delta, pricing_basis,
        confidence, bid_package_id, source_sheet, related_csi,
        selected, operator_notes

    ``selected_ids`` defaults to the empty set; ``operator_notes_map``
    is an in-session overlay keyed by ``alternate_id`` — when present
    its value supersedes the ``AlternateLineEstimate.operator_notes``
    on disk (mirrors the T9.1 UI's "edit notes inline" affordance).
    """
    sel = selected_ids or set()
    notes_map = operator_notes_map or {}

    buf = io.StringIO()
    writer = csv.writer(buf, lineterminator="\n")
    writer.writerow([
        "alternate_id",
        "type",
        "description",
        "cost_delta",
        "pricing_basis",
        "confidence",
        "bid_package_id",
        "source_sheet",
        "related_csi",
        "selected",
        "operator_notes",
    ])
    for a in alternates or []:
        atype = (
            a.alternate_type.value
            if isinstance(a.alternate_type, AlternateType)
            else str(a.alternate_type)
        )
        basis = (
            a.pricing_basis.value
            if isinstance(a.pricing_basis, AlternatePricingBasis)
            else str(a.pricing_basis)
        )
        delta_str = "" if a.cost_delta is None else f"{a.cost_delta:.2f}"
        notes = notes_map.get(a.alternate_id, a.operator_notes or "")
        writer.writerow([
            a.alternate_id,
            atype,
            a.description,
            delta_str,
            basis,
            f"{a.confidence:.2f}",
            a.bid_package_id or "",
            a.source_sheet or "",
            ", ".join(a.related_csi or []),
            "yes" if a.alternate_id in sel else "no",
            notes,
        ])
    return buf.getvalue()


def _resolve_bid_package_title(
    bid_package_id: str | None,
    project: ProjectModel | None,
) -> str:
    """Resolve a ``bid_package_id`` foreign key to a human-readable title.

    Match order against ``project.bid_packages``:

    1. ``BidPackage.pdf_name`` (the canonical FK target used by T9.0
       extraction).
    2. ``BidPackage.package_number`` (e.g. ``"03.00"``).

    Returns the package's ``trade_name`` (preferred), falling back to
    ``pdf_name`` when the trade name is empty. ``None`` / empty
    ``bid_package_id`` returns ``"(general)"``; an unknown id returns
    the id itself prefixed with ``"(unknown:`` so an operator can spot
    the broken FK without crashing the UI.
    """
    if not bid_package_id:
        return "(general)"
    if project is None:
        return bid_package_id
    bid_packages = getattr(project, "bid_packages", None) or []
    needle = str(bid_package_id).strip()
    for p in bid_packages:
        if p.pdf_name == needle or (p.package_number and p.package_number == needle):
            return p.trade_name or p.pdf_name or needle
    return f"(unknown: {bid_package_id})"


# Session-state keys — kept namespaced under ``alternates_*`` so they
# don't collide with the T6.2 (``override_history``,
# ``estimate_original``), T6.3 (``batch_override_*``), or T8
# (``subquote_*``) keys.
_ALTERNATES_SS_SELECTED = "alternates_selected_ids"
_ALTERNATES_SS_NOTES = "alternates_operator_notes"
_ALTERNATES_SS_DELTAS = "alternates_operator_deltas"
_ALTERNATES_SS_ESTIMATE_FP = "alternates_estimate_fingerprint"


def _alternates_estimate_fingerprint(estimate: Estimate) -> tuple:
    """Return a hashable fingerprint that changes when a new estimate loads.

    Two estimates "look the same" to the alternates session if they
    carry the same project name + line-item count + alternates list
    (alternate_id + cost_delta tuple). A fresh analyze run regenerates
    the line-item list so the fingerprint flips and the session
    re-initialises; an in-session edit (e.g. T6.2 override) preserves
    the alternates list and keeps the operator's selection / notes.
    """
    alts = list(getattr(estimate, "alternates", None) or [])
    alt_fp = tuple((a.alternate_id, a.cost_delta) for a in alts)
    return (
        getattr(estimate, "project_name", "") or "",
        len(getattr(estimate, "line_items", []) or []),
        alt_fp,
    )


def _initialize_alternates_session_state(estimate: Estimate) -> None:
    """Idempotent seed of the three new alternates session-state keys.

    Called once per render of the Bid Alternates tab. On a fresh
    estimate (different fingerprint) the function:

    * seeds ``alternates_selected_ids`` from
      ``estimate.alternates_selected_default``,
    * resets ``alternates_operator_notes`` and
      ``alternates_operator_deltas`` to empty dicts,
    * stamps the new fingerprint so subsequent calls during the same
      estimate are no-ops.

    On a same-fingerprint re-call the function is a no-op — the
    operator's in-progress selection / notes / deltas survive a
    simple re-render (every checkbox toggle re-runs the script).
    """
    fp = _alternates_estimate_fingerprint(estimate)
    if st.session_state.get(_ALTERNATES_SS_ESTIMATE_FP) == fp:
        return

    default_selected = set(
        getattr(estimate, "alternates_selected_default", None) or set()
    )
    st.session_state[_ALTERNATES_SS_SELECTED] = default_selected
    st.session_state[_ALTERNATES_SS_NOTES] = {}
    st.session_state[_ALTERNATES_SS_DELTAS] = {}
    st.session_state[_ALTERNATES_SS_ESTIMATE_FP] = fp


def _apply_alternate_operator_entry(
    alternate_id: str,
    new_delta: float,
    alternates: list[AlternateLineEstimate],
) -> tuple[list[AlternateLineEstimate], str | None]:
    """Apply an operator-entered ``cost_delta`` to a MISSING-basis alternate.

    Returns ``(updated_alternates, warning_or_none)``. The list is a new
    list — the input is never mutated. The warning is non-None only when
    the entered ``new_delta``'s sign disagrees with the alternate's type
    (ADDITIVE with negative delta, DEDUCTIVE with positive delta).

    Mirrors the T9.0 backend ``AlternateLine._validate_sign_consistency``
    behaviour: the entry IS APPLIED regardless — real bid forms
    occasionally publish a positive absolute value with the ADD/DEDUCT
    label printed separately, and downstream callers must tolerate
    both conventions.

    Raises :class:`ValueError` if ``alternate_id`` is not present in
    ``alternates``. Pre-existing OPERATOR_ENTERED / EXTRACTED entries
    are also overwritable (the operator can correct an extraction
    error); the basis is set to OPERATOR_ENTERED on the way through.
    """
    if not alternate_id:
        raise ValueError(
            "_apply_alternate_operator_entry: alternate_id must be non-empty."
        )
    try:
        delta_f = float(new_delta)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"_apply_alternate_operator_entry: new_delta {new_delta!r} "
            f"must be numeric."
        ) from exc

    out: list[AlternateLineEstimate] = []
    matched = False
    warning: str | None = None
    for a in alternates or []:
        if a.alternate_id != alternate_id:
            out.append(a)
            continue
        matched = True
        atype = a.alternate_type
        if isinstance(atype, str):
            try:
                atype = AlternateType(atype)
            except (ValueError, KeyError):
                atype = AlternateType.ADDITIVE
        if atype == AlternateType.ADDITIVE and delta_f < 0:
            warning = (
                f"Sign mismatch: ADDITIVE alternate {alternate_id!r} "
                f"received negative delta {delta_f:+,.2f}. Applied as-given; "
                "verify the bid-form printed sign convention."
            )
        elif atype == AlternateType.DEDUCTIVE and delta_f > 0:
            warning = (
                f"Sign mismatch: DEDUCTIVE alternate {alternate_id!r} "
                f"received positive delta {delta_f:+,.2f}. Applied as-given; "
                "verify the bid-form printed sign convention."
            )
        out.append(
            a.model_copy(
                update={
                    "cost_delta": round(delta_f, 2),
                    "pricing_basis": AlternatePricingBasis.OPERATOR_ENTERED,
                }
            )
        )

    if not matched:
        raise ValueError(
            f"_apply_alternate_operator_entry: alternate_id "
            f"{alternate_id!r} not found in {len(alternates or [])} priced "
            "alternates."
        )
    return out, warning


from core.sheet_classifier import classify_sheet
from core.takeoff import ProjectModel, reconcile

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT / "uploads"
CACHE_DIR = ROOT / ".cache" / "renders"
EXPORT_DIR = ROOT / "exports"
CSI_TITLES_PATH = ROOT / "config" / "csi_divisions.json"
CLIENT_QUOTE_CFG_PATH = ROOT / "config" / "client_quote.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _load_quote_config() -> QuoteConfig:
    """Read the client-quote config from disk, falling back to defaults."""
    if CLIENT_QUOTE_CFG_PATH.is_file():
        try:
            raw = json.loads(CLIENT_QUOTE_CFG_PATH.read_text(encoding="utf-8"))
            return QuoteConfig.model_validate(raw)
        except Exception as exc:
            logging.warning("client_quote.json failed to parse: %s", exc)
    return QuoteConfig()


def _save_quote_config(cfg: QuoteConfig) -> None:
    """Atomically replace the client-quote config on disk."""
    CLIENT_QUOTE_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLIENT_QUOTE_CFG_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(cfg.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, CLIENT_QUOTE_CFG_PATH)


def _load_alternates_section_config() -> dict:
    """Read the ``alternates_section`` block from ``client_quote.json``.

    Phase T9.3 — ``QuoteConfig`` (Pydantic) does NOT model the
    ``alternates_section`` block (T9.2 added the keys to the JSON file
    but kept the schema additive-only), so the block is silently
    dropped on the ``_load_quote_config()`` round-trip. To honour
    operator overrides for ``enabled`` / ``intro_paragraph`` /
    ``footer_note`` set in ``config/client_quote.json``, we re-parse
    the raw JSON here and surface the block as a dict.

    Returns ``{}`` on any error (missing file, invalid JSON, missing
    block, or block not a JSON object). Never raises — a malformed
    config must not block PDF generation.
    """
    if not CLIENT_QUOTE_CFG_PATH.is_file():
        return {}
    try:
        raw = json.loads(CLIENT_QUOTE_CFG_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        logging.warning(
            "client_quote.json alternates_section parse failed: %s", exc
        )
        return {}
    section = raw.get("alternates_section") if isinstance(raw, dict) else None
    return dict(section) if isinstance(section, dict) else {}


def _resolve_alternates_config_for_pdf(
    session_state: Mapping[str, Any] | None,
    base_config: dict | None = None,
) -> dict:
    """Resolve the ``alternates_config`` dict to pass into ``build_quote_pdf``.

    Phase T9.3 — glue between T9.1's ``alternates_selected_ids``
    session-state selection (populated by the "Bid Alternates" tab)
    and T9.2's ``build_quote_pdf(..., alternates_config=...)`` PDF
    renderer.

    Operator-wins semantics: the operator's tab selection (a
    ``set[str]`` in ``session_state["alternates_selected_ids"]``) is
    the authoritative source for ``default_selection``. The
    ``base_config`` dict (typically loaded from
    ``config/client_quote.json``'s ``alternates_section`` block via
    :func:`_load_alternates_section_config`) provides the other keys
    (``enabled`` / ``intro_paragraph`` / ``footer_note``).

    Empty selection convention: ``{}`` from the session state means
    "operator deselected everything" — the PDF renders the section
    with a $0.00 selected delta. There is intentionally NO fallback
    to ``Estimate.alternates_selected_default`` from this helper —
    once T9.1 seeds the session state on tab init (which it does),
    every subsequent PDF render must reflect what the operator sees.
    Falling back to estimate defaults would silently disagree with
    the on-screen tally and is the bug T9.3 is designed to prevent.
    Missing key (``alternates_selected_ids`` never populated) is
    treated identically to an empty selection — the operator can
    re-enable items on the tab; the PDF will reflect the next render.

    Determinism: selection coerced to a sorted ``list[str]`` so two
    PDFs rendered with identical inputs are byte-identical.

    Mutation safety: ``base_config`` is shallow-copied; the caller's
    dict is never mutated. ``session_state`` is read-only.

    Args:
        session_state: a Mapping (typically ``st.session_state``)
            providing the ``alternates_selected_ids`` key. ``None``
            is tolerated (treated as missing key).
        base_config: optional dict of pre-existing alternates_config
            keys (e.g. from ``alternates_section`` in
            ``client_quote.json``). ``None`` is treated as ``{}``.

    Returns:
        A new dict suitable to pass as ``alternates_config=...`` into
        :func:`core.exporter_pdf.build_quote_pdf`. Always carries a
        ``default_selection`` key (possibly ``[]``).
    """
    resolved: dict = dict(base_config) if base_config else {}

    raw_selection: Any = None
    if session_state is not None:
        getter = getattr(session_state, "get", None)
        if callable(getter):
            try:
                raw_selection = getter("alternates_selected_ids")
            except Exception:
                raw_selection = None

    selection: list[str]
    if raw_selection is None:
        selection = []
    else:
        try:
            selection = sorted(str(s) for s in raw_selection)
        except TypeError:
            selection = []

    resolved["default_selection"] = selection
    return resolved


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _load_csi_titles() -> dict[str, str]:
    return json.loads(CSI_TITLES_PATH.read_text(encoding="utf-8"))


def _save_uploaded_pdfs(uploaded_files) -> list[Path]:
    paths: list[Path] = []
    for f in uploaded_files:
        target = UPLOAD_DIR / f.name
        target.write_bytes(f.getbuffer())
        paths.append(target)
    return paths


def _detect_provider() -> str | None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return None


def _process_sheet(args: tuple[Sheet, str, str | None]) -> tuple[Sheet, SheetExtraction]:
    """Classifier + extractor for a single drawing sheet (thread-pool task)."""
    sheet, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    sheet = classify_sheet(sheet, llm)
    extraction = extract_sheet(sheet, llm)
    return sheet, extraction


def _process_bundle(args: tuple[DocumentBundle, str, str | None]) -> tuple[DocumentBundle, SheetExtraction]:
    """Document-level extractor for a whole text PDF (thread-pool task)."""
    bundle, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    extraction = extract_bundle(bundle, llm)
    return bundle, extraction


def _run_pipeline(
    pdf_paths: list[Path],
    provider: str,
    model: str | None,
    region_mult: float,
    contingency_pct: float,
    overhead_pct: float,
    profit_pct: float,
    project_name: str,
    dpi: int,
    max_workers: int,
    progress_cb,
) -> tuple[list[Sheet], list[DocumentBundle], list[SheetExtraction], ProjectModel, Estimate]:
    progress_cb(0.02, "Splitting PDFs and rendering sheets...")
    sheets, bundles = process_pdfs(pdf_paths, cache_dir=CACHE_DIR, dpi=dpi)
    if not sheets and not bundles:
        raise RuntimeError("No usable pages found in the uploaded PDFs.")

    total_units = len(sheets) + len(bundles)
    progress_cb(
        0.08,
        f"Found {len(sheets)} drawing sheet(s) and {len(bundles)} text document(s). "
        f"Classifying and extracting...",
    )

    extractions: list[SheetExtraction] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        sheet_futures = {
            pool.submit(_process_sheet, (s, provider, model)): ("sheet", s) for s in sheets
        }
        bundle_futures = {
            pool.submit(_process_bundle, (b, provider, model)): ("bundle", b) for b in bundles
        }
        all_futures = {**sheet_futures, **bundle_futures}

        new_sheets: list[Sheet] = list(sheets)

        for fut in as_completed(all_futures):
            kind, src = all_futures[fut]
            try:
                if kind == "sheet":
                    sheet, ex = fut.result()
                    # Replace original sheet object with the (possibly mutated) one.
                    for i, s in enumerate(new_sheets):
                        if s is src:
                            new_sheets[i] = sheet
                            break
                else:
                    _, ex = fut.result()
            except Exception as exc:
                logging.error("Unit %s failed: %s", getattr(src, "pdf_name", src), exc)
                sheet_id = getattr(src, "sheet_id", None) or getattr(src, "pdf_name", "unknown")
                ex = SheetExtraction(
                    sheet_id=sheet_id,
                    summary=f"Pipeline error: {exc}",
                    warnings=[f"pipeline error: {exc}"],
                )
            extractions.append(ex)
            completed += 1
            progress_cb(
                0.08 + 0.78 * completed / max(total_units, 1),
                f"Analyzed {completed}/{total_units} document units...",
            )

        sheets = new_sheets

    progress_cb(0.88, "Reconciling cross-document data...")
    project = reconcile(extractions)

    progress_cb(0.94, "Pricing takeoffs against cost database...")
    final_project_name = project.project_info.name or project_name
    estimate = price_takeoff(
        project,
        project_name=final_project_name,
        region_multiplier=region_mult,
        contingency_pct=contingency_pct,
        overhead_pct=overhead_pct,
        profit_pct=profit_pct,
        cost_db=CostDatabase(),
    )

    # Phase T9.1 — attach priced bid alternates so the new "Bid Alternates"
    # tab has data to render. Pure-additive: ``attach_alternates_to_estimate``
    # returns a fresh ``Estimate`` with ``alternates`` + ``alternates_selected_default``
    # populated and leaves every other field (including ``line_items`` and
    # the headline ``grand_total``) untouched. No-op when the project
    # has zero ``AlternateLine`` records.
    estimate = attach_alternates_to_estimate(
        estimate, project, region_multiplier=region_mult
    )

    progress_cb(1.0, "Done.")
    return sheets, bundles, extractions, project, estimate


def _render_client_quote_tab(
    estimate: Estimate, project: ProjectModel, csi_titles: dict[str, str]
) -> None:
    """Edit `config/client_quote.json` and generate the proposal PDF (F12/F15)."""
    st.subheader("Client-ready quote (F12) + payment schedule (F15)")
    st.caption(
        "Edits below are saved to `config/client_quote.json`. The PDF reads "
        "from that file every time it's generated, so the CLI (`analyze.py "
        "--client-pdf`) and the UI stay in sync."
    )

    cfg = _load_quote_config()

    # ----- Branding sections -----
    with st.expander("Company info", expanded=False):
        cc1, cc2 = st.columns(2)
        company = CompanyInfo(
            name=cc1.text_input("Company name", cfg.company.name),
            license_number=cc2.text_input("License #", cfg.company.license_number),
            address_line_1=cc1.text_input("Address line 1", cfg.company.address_line_1),
            address_line_2=cc2.text_input("Address line 2", cfg.company.address_line_2),
            phone=cc1.text_input("Phone", cfg.company.phone),
            email=cc2.text_input("Email", cfg.company.email),
            website=cc1.text_input("Website", cfg.company.website),
            logo_path=cc2.text_input(
                "Logo path (optional)",
                cfg.company.logo_path,
                help="Absolute path or workspace-relative path to PNG/JPG. Leave blank to skip.",
            ),
        )

    with st.expander("Client info", expanded=False):
        kc1, kc2 = st.columns(2)
        client = ClientInfo(
            name=kc1.text_input("Client name", cfg.client.name),
            contact_name=kc2.text_input("Primary contact", cfg.client.contact_name),
            address_line_1=kc1.text_input("Client address line 1", cfg.client.address_line_1),
            address_line_2=kc2.text_input("Client address line 2", cfg.client.address_line_2),
            phone=kc1.text_input("Client phone", cfg.client.phone),
            email=kc2.text_input("Client email", cfg.client.email),
        )

    with st.expander("Quote meta", expanded=True):
        mc1, mc2 = st.columns([1, 1])
        quote_number = mc1.text_input(
            "Quote number", cfg.quote_meta.quote_number,
            help="Use 'AUTO' to derive from the project name + today's date at build time.",
        )
        valid_until_days = mc2.number_input(
            "Valid for (days)", value=int(cfg.quote_meta.valid_until_days),
            min_value=1, max_value=365, step=1,
        )
        scope_blurb = st.text_area(
            "Scope-of-work blurb (executive summary paragraph)",
            cfg.quote_meta.scope_blurb,
            height=100,
        )
        payment_terms_text = st.text_area(
            "Payment terms footer (rendered under the payment schedule)",
            cfg.quote_meta.payment_terms_text,
            height=70,
        )
        meta = QuoteMeta(
            quote_number=quote_number,
            valid_until_days=int(valid_until_days),
            scope_blurb=scope_blurb,
            payment_terms_text=payment_terms_text,
        )

    # ----- Payment schedule -----
    st.markdown("##### Payment schedule")
    st.caption(
        "Percentage mode auto-computes dollar amounts against the estimate's "
        "grand total. Milestone mode lets you set fixed dollar amounts."
    )
    sched_mode = st.radio(
        "Mode",
        options=["percentage", "milestone"],
        index=0 if cfg.payment_schedule.mode == "percentage" else 1,
        horizontal=True,
    )

    existing_rows = [
        {
            "label": m.label,
            "percentage": m.percentage if m.percentage is not None else 0.0,
            "amount": m.amount if m.amount is not None else 0.0,
            "notes": m.notes or "",
        }
        for m in cfg.payment_schedule.milestones
    ] or [{"label": "", "percentage": 0.0, "amount": 0.0, "notes": ""}]

    if sched_mode == "percentage":
        col_cfg = {
            "label":      st.column_config.TextColumn("Milestone", required=True),
            "percentage": st.column_config.NumberColumn("% of contract", min_value=0.0, max_value=100.0, step=0.5, format="%.1f"),
            "amount":     None,
            "notes":      st.column_config.TextColumn("Notes"),
        }
    else:
        col_cfg = {
            "label":      st.column_config.TextColumn("Milestone", required=True),
            "percentage": None,
            "amount":     st.column_config.NumberColumn("$ amount", min_value=0.0, step=100.0, format="$%.2f"),
            "notes":      st.column_config.TextColumn("Notes"),
        }
    edited = st.data_editor(
        pd.DataFrame(existing_rows),
        column_config=col_cfg,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="payment_schedule_editor",
    )

    milestones: list[PaymentMilestone] = []
    for _, r in edited.iterrows():
        label = str(r.get("label", "") or "").strip()
        if not label:
            continue
        if sched_mode == "percentage":
            milestones.append(PaymentMilestone(
                label=label,
                percentage=float(r.get("percentage") or 0.0),
                amount=None,
                notes=str(r.get("notes", "") or ""),
            ))
        else:
            milestones.append(PaymentMilestone(
                label=label,
                percentage=None,
                amount=float(r.get("amount") or 0.0),
                notes=str(r.get("notes", "") or ""),
            ))

    # Build the candidate schedule WITHOUT raising — we want to show validation
    # errors inline instead of crashing the tab.
    schedule_valid = True
    schedule_err = ""
    try:
        schedule = PaymentSchedule(mode=sched_mode, milestones=milestones)
    except Exception as exc:
        schedule_valid = False
        schedule_err = str(exc)
        schedule = cfg.payment_schedule  # fall back so downstream code has something usable

    if not schedule_valid:
        st.warning(f"Payment schedule is invalid and will not be saved:\n\n{schedule_err}")
    elif sched_mode == "milestone":
        warns = schedule.validate_against_total(estimate.grand_total or 0.0)
        for w in warns:
            st.info(w)

    # ----- Terms -----
    with st.expander("Terms and conditions (optional)", expanded=False):
        terms_text = st.text_area(
            "Full T&Cs (blank to omit the page)",
            cfg.terms_text,
            height=240,
            help="Paragraph breaks are preserved (separate with a blank line).",
        )

    candidate_cfg = QuoteConfig(
        company=company,
        client=client,
        quote_meta=meta,
        payment_schedule=schedule,
        terms_text=terms_text,
    )

    # ----- Action buttons -----
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button(
            "Save configuration",
            type="secondary",
            use_container_width=True,
            disabled=not schedule_valid,
        ):
            try:
                _save_quote_config(candidate_cfg)
                st.success(f"Saved to {CLIENT_QUOTE_CFG_PATH.relative_to(ROOT)}.")
            except Exception as exc:
                st.error(f"Could not save: {exc}")

    with ac2:
        # Generate the PDF in-memory so the download works without writing
        # a (potentially client-identifying) file to disk by accident.
        pdf_bytes: bytes | None = None
        if schedule_valid:
            try:
                from core.exporter_pdf import build_quote_pdf  # local import for friendlier error
                tmp_pdf = EXPORT_DIR / "_quote_preview.pdf"
                # Phase T9.3 — thread the operator's "Bid Alternates"
                # tab selection (T9.1's session-state set) into T9.2's
                # PDF renderer so the rendered "Base + selected
                # alternates" tally row reflects what the operator
                # sees on-screen. Other alternates_config keys
                # (enabled / intro_paragraph / footer_note) come from
                # client_quote.json's alternates_section block.
                alternates_pdf_config = _resolve_alternates_config_for_pdf(
                    st.session_state,
                    _load_alternates_section_config(),
                )
                build_quote_pdf(
                    estimate=estimate,
                    project=project,
                    quote_config=candidate_cfg,
                    out_path=tmp_pdf,
                    csi_titles=csi_titles,
                    alternates_config=alternates_pdf_config,
                )
                pdf_bytes = tmp_pdf.read_bytes()
            except ImportError:
                st.error(
                    "`reportlab` is not installed. Run "
                    "`pip install 'reportlab>=4.0,<5.0'` in the venv."
                )
            except Exception as exc:
                st.error(f"PDF render failed: {exc}")

        st.download_button(
            "Generate & download PDF",
            data=pdf_bytes or b"",
            file_name=f"{estimate.project_name.replace(' ', '_')}_quote.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
        )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


st.set_page_config(
    page_title="Construction Plan Estimator",
    page_icon="\U0001F3D7",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Construction Plan Estimator")
st.caption(
    "Upload a multi-PDF plan set; the app reads every sheet, builds a "
    "CSI-organized takeoff, and produces a priced estimate with full "
    "traceability back to the source drawings."
)

# --- Sidebar -----------------------------------------------------------------

with st.sidebar:
    st.header("Project")
    project_name = st.text_input("Project name", value="New Project")

    detected = _detect_provider()
    provider_choice = st.selectbox(
        "AI provider",
        options=[
            ("auto", "Auto-detect from .env"),
            ("anthropic", "Anthropic (Claude)"),
            ("openai", "OpenAI (GPT-4o)"),
        ],
        format_func=lambda x: x[1],
        index=0,
    )
    chosen_provider = detected if provider_choice[0] == "auto" else provider_choice[0]
    if chosen_provider:
        st.success(f"Using {chosen_provider}")
    else:
        st.error(
            "No API key found. Copy `.env.example` to `.env` and add either "
            "`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`."
        )

    custom_model = st.text_input(
        "Model override (optional)",
        value="",
        placeholder="e.g. claude-sonnet-4-5 or gpt-4o",
    ).strip() or None

    st.divider()
    st.header("Estimating settings")
    region_mult = st.number_input(
        "Region cost multiplier", value=float(os.getenv("REGION_MULTIPLIER", "1.00")),
        min_value=0.5, max_value=2.5, step=0.01, format="%.2f",
    )
    contingency_pct = st.slider("Contingency %", 0.0, 25.0, 10.0, 0.5)
    overhead_pct = st.slider("Overhead %", 0.0, 25.0, 10.0, 0.5)
    profit_pct = st.slider("Profit %", 0.0, 20.0, 5.0, 0.5)

    st.divider()
    st.header("Performance")
    dpi = st.slider("Render DPI", 100, 300, int(os.getenv("RENDER_DPI", "200")), 25,
                    help="Higher = better OCR but more tokens. 200 is a good default.")
    max_workers = st.slider("Parallel sheets", 1, 8, int(os.getenv("MAX_CONCURRENCY", "4")))

    st.divider()
    st.subheader("Input")

    input_mode = st.radio(
        "Source",
        options=["Upload files", "Local folder"],
        horizontal=True,
        index=0,
        help="Use 'Local folder' to point at a directory with many PDFs (e.g. an entire GMP set) without dragging each file.",
    )

    uploaded_files = []
    folder_pdfs: list[Path] = []
    if input_mode == "Upload files":
        uploaded_files = st.file_uploader(
            "Upload plan-set PDF(s)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Drag in any number of PDFs. Each page is treated as one sheet.",
        )
    else:
        folder_str = st.text_input(
            "Folder path",
            value="",
            placeholder=r"e.g. C:\Users\you\Project\GMP#003-Permit-Set",
        ).strip()
        recursive = st.checkbox("Recurse into subfolders", value=True)
        skip_large = st.checkbox(
            "Skip large PDFs (> 5 MB) - cheap text-only run",
            value=False,
            help="Useful for processing only the bid packages / specs without burning vision tokens on huge drawing sets.",
        )
        if folder_str:
            folder = Path(folder_str)
            if folder.exists() and folder.is_dir():
                pattern = "**/*.pdf" if recursive else "*.pdf"
                folder_pdfs = sorted(p for p in folder.glob(pattern) if p.is_file())
                if skip_large:
                    folder_pdfs = [p for p in folder_pdfs if p.stat().st_size <= 5 * 1024 * 1024]
                st.success(f"Found {len(folder_pdfs)} PDF(s).")
                with st.expander("Preview file list", expanded=False):
                    for p in folder_pdfs[:200]:
                        st.caption(f"\u2022 {p.relative_to(folder)}  ({p.stat().st_size / 1024:.0f} KB)")
                    if len(folder_pdfs) > 200:
                        st.caption(f"... and {len(folder_pdfs) - 200} more.")
            elif folder.exists():
                st.error("That path is a file, not a folder.")
            else:
                st.error("Folder not found.")

    run_disabled = not chosen_provider or (
        (input_mode == "Upload files" and not uploaded_files)
        or (input_mode == "Local folder" and not folder_pdfs)
    )
    run_clicked = st.button(
        "Analyze plan set",
        type="primary",
        use_container_width=True,
        disabled=run_disabled,
    )

# --- Main area --------------------------------------------------------------


def _render_proposal_panel() -> None:
    """Render-bid-proposal panel — picks a bid workspace, renders the four
    tier-appropriate artifacts (executive-summary PDF, full proposal PDF,
    internal workbook PDF, pitch-deck PPTX), and surfaces download
    buttons. Independent of the analyze flow above; safe to use without
    an active estimate in session state.
    """
    from core.proposal_renderer import (
        build_client_pdfs,
        build_internal_workbook,
        build_pitch_deck,
        load_firm_profile,
    )

    bids_root = ROOT / "bids"
    bid_dirs = sorted(
        p for p in bids_root.iterdir()
        if p.is_dir() and (p / "proposal").is_dir()
    ) if bids_root.is_dir() else []

    if not bid_dirs:
        st.info(
            "No `bids/<slug>/proposal/` workspaces found. Add a bid workspace "
            "before using the proposal renderer."
        )
        return

    bid_choice = st.selectbox(
        "Bid workspace",
        options=[p.name for p in bid_dirs],
        index=0,
        help="Each option corresponds to a `bids/<slug>/proposal/` directory.",
    )

    show_placeholders = st.checkbox(
        "Show `[USER TO FILL]` markers in red on client outputs",
        value=False,
        help=(
            "Default is to neutralize markers to a fillable underline on "
            "client-facing PDFs and the pitch deck. Toggle this on for "
            "your own internal review. The internal workbook always "
            "shows markers in red."
        ),
    )

    render_clicked = st.button(
        "Re-render proposal package",
        type="primary",
        help=(
            "Re-renders all four artifacts: client executive-summary PDF, "
            "full proposal PDF, internal workbook PDF, and pitch-deck PPTX."
        ),
    )

    state_key = f"proposal_render__{bid_choice}"
    if render_clicked:
        bid_dir = bids_root / bid_choice
        bid_slug = bid_dir.name
        out_dir = bid_dir / "proposal" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            firm_profile = load_firm_profile()
        except Exception as exc:
            st.error(f"Could not load firm/firm-profile.json: {exc}")
            return

        artifacts: dict[str, Path] = {}
        errors: list[str] = []

        try:
            client = build_client_pdfs(
                bid_dir, out_dir, firm_profile,
                show_placeholders=show_placeholders,
            )
            artifacts["executive_summary"] = client["executive_summary"]
            artifacts["full_proposal"] = client["full_proposal"]
        except Exception as exc:
            errors.append(f"Client PDF render failed: {exc}")

        try:
            internal_path = out_dir / f"{bid_slug}-internal-workbook.pdf"
            build_internal_workbook(bid_dir, internal_path, firm_profile)
            artifacts["internal_workbook"] = internal_path
        except Exception as exc:
            errors.append(f"Internal workbook render failed: {exc}")

        try:
            pitch_path = out_dir / f"{bid_slug}-pitch-deck.pptx"
            build_pitch_deck(
                bid_dir, pitch_path, firm_profile,
                show_placeholders=show_placeholders,
            )
            artifacts["pitch_deck"] = pitch_path
        except Exception as exc:
            errors.append(f"Pitch-deck render failed: {exc}")

        st.session_state[state_key] = {"artifacts": artifacts, "errors": errors}

    rendered = st.session_state.get(state_key)
    if not rendered:
        st.caption(
            "Click **Re-render proposal package** to (re-)generate the four "
            "tier-appropriate artifacts under "
            "`bids/<slug>/proposal/exports/`. If existing artifacts are on "
            "disk from a prior run, the download buttons below will surface "
            "them on next render."
        )
        # Try to surface previously rendered artifacts on disk so the user
        # doesn't have to re-render every reload.
        bid_dir = bids_root / bid_choice
        out_dir = bid_dir / "proposal" / "exports"
        bid_slug = bid_dir.name
        existing = {
            "executive_summary": out_dir / f"{bid_slug}-client-executive-summary.pdf",
            "full_proposal": out_dir / f"{bid_slug}-full-proposal.pdf",
            "internal_workbook": out_dir / f"{bid_slug}-internal-workbook.pdf",
            "pitch_deck": out_dir / f"{bid_slug}-pitch-deck.pptx",
        }
        existing = {k: v for k, v in existing.items() if v.exists()}
        if not existing:
            return
        rendered = {"artifacts": existing, "errors": []}

    for err in rendered["errors"]:
        st.error(err)

    artifacts = rendered["artifacts"]
    if not artifacts:
        return

    st.success(
        f"{len(artifacts)} artifact(s) ready under "
        f"`bids/{bid_choice}/proposal/exports/`."
    )

    pdf_mime = "application/pdf"
    pptx_mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    label_map = {
        "executive_summary": ("Executive summary (PDF)", pdf_mime),
        "full_proposal": ("Full proposal (PDF)", pdf_mime),
        "internal_workbook": ("Internal workbook (PDF)", pdf_mime),
        "pitch_deck": ("Pitch deck (PPTX)", pptx_mime),
    }
    # Stable display order: client deliverables first, then internal,
    # then pitch deck — matches the four-tier brief.
    order = ["executive_summary", "full_proposal", "internal_workbook", "pitch_deck"]
    ordered = [(k, artifacts[k]) for k in order if k in artifacts]
    cols = st.columns(len(ordered))
    for col, (key, path) in zip(cols, ordered):
        label, mime = label_map.get(key, (path.name, "application/octet-stream"))
        with col:
            st.download_button(
                label,
                data=path.read_bytes(),
                file_name=path.name,
                mime=mime,
                use_container_width=True,
            )
            st.caption(f"{path.stat().st_size:,} bytes")


with st.expander(
    "Bid Proposals — render client PDFs, internal workbook, and pitch deck",
    expanded=False,
):
    st.caption(
        "Independent of the plan-set analyzer above. Picks a bid workspace "
        "under `bids/`, reads its `proposal/*.md` files, and produces four "
        "tier-appropriate artifacts under `bids/<slug>/proposal/exports/`: "
        "client executive-summary PDF, full proposal PDF, internal workbook "
        "PDF, and pitch-deck PPTX."
    )
    _render_proposal_panel()


if run_clicked:
    if input_mode == "Upload files":
        pdf_paths = _save_uploaded_pdfs(uploaded_files)
    else:
        pdf_paths = folder_pdfs   # use the on-disk paths directly; no copy needed
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    def update_progress(p: float, msg: str) -> None:
        progress_bar.progress(min(max(p, 0.0), 1.0))
        status_text.info(msg)

    started = time.time()
    try:
        sheets, bundles, extractions, project, estimate = _run_pipeline(
            pdf_paths=pdf_paths,
            provider=chosen_provider,
            model=custom_model,
            region_mult=region_mult,
            contingency_pct=contingency_pct,
            overhead_pct=overhead_pct,
            profit_pct=profit_pct,
            project_name=project_name,
            dpi=dpi,
            max_workers=max_workers,
            progress_cb=update_progress,
        )
    except Exception as exc:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Pipeline failed: {exc}")
        st.stop()

    elapsed = time.time() - started
    status_text.success(
        f"Analyzed {len(sheets)} drawing sheet(s) and {len(bundles)} document(s) in {elapsed:.1f}s."
    )

    st.session_state["sheets"] = sheets
    st.session_state["bundles"] = bundles
    st.session_state["extractions"] = extractions
    st.session_state["project"] = project
    st.session_state["estimate"] = estimate
    # Phase T6.2 — seed the override snapshot + history for the operator-
    # override UI in the Estimate tab. Done here (immediately after the
    # estimate is committed to session state) so a fresh analyze run
    # always starts with an empty override history regardless of any
    # prior session activity.
    _initialize_override_session_state(estimate)

# --- Results -----------------------------------------------------------------

if "estimate" in st.session_state:
    csi_titles = _load_csi_titles()
    project: ProjectModel = st.session_state["project"]
    estimate: Estimate = st.session_state["estimate"]
    sheets: list[Sheet] = st.session_state["sheets"]
    bundles: list[DocumentBundle] = st.session_state.get("bundles", [])
    extractions: list[SheetExtraction] = st.session_state["extractions"]
    pi = project.project_info

    # --- Project header banner ---
    if pi and (pi.name or pi.number):
        bits = []
        if pi.name:        bits.append(f"**{pi.name}**")
        if pi.number:      bits.append(f"#{pi.number}")
        if pi.location:    bits.append(pi.location)
        if pi.contractor:  bits.append(f"GC: {pi.contractor}")
        if pi.bid_due:     bits.append(f"Bid due: {pi.bid_due}")
        st.info(" \u2022 ".join(bits))

    # --- KPI row ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Drawing sheets", len(sheets))
    k2.metric("Bid packages", len(project.bid_packages))
    k3.metric("Line items", len(estimate.line_items))
    k4.metric("Subtotal", f"${estimate.subtotal:,.0f}")
    k5.metric("Grand total", f"${estimate.grand_total:,.0f}")

    tabs = st.tabs([
        "Project", "Bid Packages", "Scope Matrix", "Scope Coverage", "Alternates",
        "Estimate", "By Division", "Sheets", "Rooms",
        "Doors / Windows", "Structural / MEP", "Specs",
        "Raw takeoffs", "Warnings", "Client Quote", "Bid Alternates",
    ])

    # --- Project tab ---
    with tabs[0]:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Project information")
            st.write(f"**Name:** {pi.name or '(not detected)'}")
            st.write(f"**Number:** {pi.number or '(not detected)'}")
            st.write(f"**Location:** {pi.location or '(not detected)'}")
            st.write(f"**Owner:** {pi.owner or '(not detected)'}")
            st.write(f"**General contractor:** {pi.contractor or '(not detected)'}")
            st.write(f"**Bid due:** {pi.bid_due or '(not detected)'}")
            if pi.sources:
                st.caption(f"Source PDFs: {', '.join(pi.sources)}")
        with c2:
            st.subheader("Document inventory")
            inventory = [
                {"Type": "Drawing sheet", "Count": len(sheets)},
                {"Type": "Bid package",   "Count": sum(1 for b in bundles if b.sheet_type.endswith("bid_package") or "bid_package" in str(b.sheet_type))},
                {"Type": "Project manual / flyer / questionnaire",
                 "Count": sum(1 for b in bundles if "project_manual" in str(b.sheet_type) or "bid_form" in str(b.sheet_type))},
            ]
            st.dataframe(pd.DataFrame(inventory), hide_index=True, use_container_width=True)

            st.subheader("Coverage by CSI division")
            sm_rows = []
            for div in sorted(project.scope_matrix.by_division):
                pkgs = project.scope_matrix.by_division[div]
                sm_rows.append({
                    "Div":      div,
                    "Title":    csi_titles.get(div, ""),
                    "# Packages": len(pkgs),
                    "Trades":   ", ".join(p.trade_name or p.pdf_name for p in pkgs),
                })
            if sm_rows:
                st.dataframe(pd.DataFrame(sm_rows), hide_index=True, use_container_width=True)
            else:
                st.caption("No bid-package coverage detected.")

    # --- Bid Packages tab ---
    # Split into two sub-sections: trade packages (the existing view, filtered
    # to `document_kind == 'trade_package'`) and supporting documents (wage
    # determinations, sample agreements, tax-exemption certificates, HSP
    # templates, UGSC, etc.). Pre-calibration-v3 these all landed in the same
    # table with `trade_name='other'`, polluting the export.
    with tabs[1]:
        trade_packages = [p for p in project.bid_packages if p.document_kind == "trade_package"]
        supporting_docs = [p for p in project.bid_packages if p.document_kind == "supporting_document"]

        st.subheader("Trade Packages")
        if not trade_packages:
            st.info("No trade packages detected. Upload Beck-style scope/bid PDFs to populate this view.")
        else:
            for p in sorted(trade_packages, key=lambda x: x.package_number or x.pdf_name):
                title_bits = filter(None, [
                    f"#{p.package_number}" if p.package_number else None,
                    p.trade_name,
                    f"({p.pdf_name})",
                ])
                with st.expander(" \u2022 ".join(title_bits), expanded=False):
                    cols = st.columns([1, 2])
                    with cols[0]:
                        st.write(f"**Project:** {p.project_name or '?'}  (#{p.project_number or '?'})")
                        # Owner / GC split — owner is the agency/institution
                        # paying (USFWS, ASU, TAMU); gc is the construction
                        # manager running the bid (Beck, JE Dunn). On
                        # government direct solicitations gc is typically None.
                        st.write(f"**Owner:** {p.owner or '—'}")
                        st.write(f"**General contractor:** {p.gc or '—'}")
                        st.write(f"**CSI divisions:** {', '.join(p.csi_divisions) or '?'}")
                        if p.csi_sections:
                            st.caption("Sections: " + ", ".join(p.csi_sections))
                        if p.referenced_drawings:
                            st.caption("Refd drawings: " + ", ".join(p.referenced_drawings))
                        if p.referenced_specs:
                            st.caption("Refd specs: " + ", ".join(p.referenced_specs))
                    with cols[1]:
                        if p.summary:
                            st.write(p.summary)
                    if p.inclusions:
                        st.markdown(f"**Inclusions ({len(p.inclusions)}):**")
                        for it in p.inclusions:
                            st.markdown(f"- {it}")
                    if p.exclusions:
                        st.markdown(f"**Exclusions ({len(p.exclusions)}):**")
                        for it in p.exclusions:
                            st.markdown(f"- {it}")
                    if p.alternates:
                        st.markdown(f"**Alternates ({len(p.alternates)}):**")
                        st.dataframe(
                            pd.DataFrame([a.model_dump() for a in p.alternates]),
                            hide_index=True, use_container_width=True,
                        )
                    if p.unit_prices:
                        st.markdown(f"**Unit prices ({len(p.unit_prices)}):**")
                        st.dataframe(
                            pd.DataFrame([u.model_dump() for u in p.unit_prices]),
                            hide_index=True, use_container_width=True,
                        )

        st.divider()
        st.subheader("Supporting Documents")
        if not supporting_docs:
            st.caption("No supporting documents extracted yet.")
        else:
            # Reuse the exporter's classifier so the UI matches the Excel
            # "Kind" column exactly.
            from core.exporter import _classify_supporting_doc
            sd_rows = []
            for p in sorted(supporting_docs, key=lambda x: x.pdf_name):
                sd_rows.append({
                    "Filename": p.pdf_name,
                    "Kind": _classify_supporting_doc(p),
                    "Owner": p.owner or "",
                    "Summary": (p.summary or "")[:300],
                })
            st.dataframe(
                pd.DataFrame(sd_rows),
                hide_index=True, use_container_width=True,
            )

    # --- Scope Matrix tab ---
    with tabs[2]:
        if not project.scope_matrix.by_division:
            st.info("No CSI division coverage to display yet.")
        else:
            rows = []
            for div in sorted(project.scope_matrix.by_division):
                for p in project.scope_matrix.by_division[div]:
                    rows.append({
                        "Div":     div,
                        "Title":   csi_titles.get(div, ""),
                        "Pkg #":   p.package_number or "",
                        "Trade":   p.trade_name or "",
                        "PDF":     p.pdf_name,
                        "Inclusions": len(p.inclusions),
                        "Exclusions": len(p.exclusions),
                        "Alternates": len(p.alternates),
                        "Unit prices": len(p.unit_prices),
                    })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            if project.scope_matrix.coverage_warnings:
                st.warning(
                    "Potential scope overlaps:\n\n- " +
                    "\n- ".join(project.scope_matrix.coverage_warnings)
                )

    # --- Scope Coverage tab ---
    with tabs[3]:
        agg_inc = project.aggregated_inclusions
        agg_exc = project.aggregated_exclusions
        if not agg_inc and not agg_exc:
            st.info("No aggregated inclusions or exclusions detected. Upload bid-package PDFs to populate this view.")
        else:
            st.caption(
                "Deduplicated across all bid packages using fuzzy text match. "
                "'# Packages' counts how many bid packages contributed an "
                "equivalent line; expand a row to see which ones."
            )

            c1, c2 = st.columns(2)
            with c1:
                st.subheader(f"Inclusions ({len(agg_inc)})")
                if agg_inc:
                    inc_rows = [{
                        "Inclusion": it.text,
                        "# Packages": len(it.source_packages),
                        "Source Packages": ", ".join(it.source_packages),
                    } for it in agg_inc]
                    st.dataframe(pd.DataFrame(inc_rows), hide_index=True, use_container_width=True)
                else:
                    st.info("No aggregated inclusions.")
            with c2:
                st.subheader(f"Exclusions ({len(agg_exc)})")
                if agg_exc:
                    exc_rows = [{
                        "Exclusion": it.text,
                        "# Packages": len(it.source_packages),
                        "Source Packages": ", ".join(it.source_packages),
                    } for it in agg_exc]
                    st.dataframe(pd.DataFrame(exc_rows), hide_index=True, use_container_width=True)
                else:
                    st.info("No aggregated exclusions.")

    # --- Alternates tab ---
    with tabs[4]:
        if not project.scope_matrix.all_alternates:
            st.info("No alternates detected.")
        else:
            st.dataframe(
                pd.DataFrame([a.model_dump() for a in project.scope_matrix.all_alternates]),
                hide_index=True, use_container_width=True,
            )

    # --- Estimate tab ---
    with tabs[5]:
        # Phase T6 — surface the manual-takeoff worklist at the top of
        # the tab BEFORE the cost breakdown, so an estimator's first
        # signal is "do you have hand-takeoff work to do?".
        if estimate.hand_takeoff_count > 0:
            st.warning(
                f"\u26A0 {estimate.hand_takeoff_count} line"
                f"{'s' if estimate.hand_takeoff_count != 1 else ''} need "
                f"manual takeoff — see Review Queues below.",
                icon="\u26A0\uFE0F",
            )

        st.subheader("Confidence band breakdown (Phase T6)")
        st.caption(
            "Auto-Approve (\u2265 0.85) rolls into the headline grand total. "
            "Operator-Review (0.65\u20130.85) also rolls in but needs a manual "
            "eyeball before submitting. Hand-Takeoff (< 0.65, or unit-mismatch "
            "suppressed) is excluded from the grand total and surfaced below "
            "as a worklist."
        )
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric(
            "Auto-Approve",
            f"${estimate.total_auto_approve:,.0f}",
            f"{estimate.auto_approve_count} line"
            f"{'s' if estimate.auto_approve_count != 1 else ''}",
        )
        bc2.metric(
            "Operator-Review",
            f"${estimate.total_operator_review:,.0f}",
            f"{estimate.operator_review_count} line"
            f"{'s' if estimate.operator_review_count != 1 else ''}",
        )
        bc3.metric(
            "Hand-Takeoff",
            f"${estimate.total_hand_takeoff:,.0f}",
            f"{estimate.hand_takeoff_count} line"
            f"{'s' if estimate.hand_takeoff_count != 1 else ''} (not in total)",
            delta_color="off",
        )

        gtc1, gtc2 = st.columns(2)
        gtc1.metric(
            "Grand Total (Auto + Review)",
            f"${estimate.grand_total_with_review:,.0f}",
            help="Headline number — the 'if reviewer signs off' total.",
        )
        gtc2.metric(
            "Grand Total (Auto-Only)",
            f"${estimate.grand_total_auto_only:,.0f}",
            help="Conservative floor — markups computed against the AUTO-only subtotal.",
        )

        # Phase T7 — Cost Source Mix expander. Sits BELOW the T6 band
        # tiles so the reader's mental flow is "qty-side confidence
        # (band) → price-side confidence (tier)". Auto-collapsed by
        # default; opens on demand for the operator who wants to see
        # which CSI rows came from CWICR / seed-DB / no match.
        with st.expander(
            "Cost Source Mix (Phase T7)",
            expanded=False,
        ):
            st.caption(
                "Catalog-completeness breakdown of every line, regardless of "
                "band. **Exact Match** = direct CWICR hit at \u2265 0.92 sim or "
                "any seed-DB hit. **Category Match** = CWICR sim 0.75\u20130.92 "
                "(same CSI family, slightly off description). **Interpolated** "
                "= CWICR sim 0.50\u20130.75 (region-adjusted neighbour). "
                "**Parametric** = CWICR sim < 0.50 (rare). **Manual Override** "
                "= operator-set unit cost. **Missing** = no cost data found."
            )
            tier_counts = estimate.count_by_tier
            tier_totals = estimate.total_by_tier
            tier_rows = [
                {
                    "Tier": _T7_TIER_LABELS[tier],
                    "Lines": tier_counts.get(tier, 0),
                    "Total $": tier_totals.get(tier, 0.0),
                }
                for tier in CostSourceTier
            ]
            tier_df = pd.DataFrame(tier_rows)
            st.dataframe(
                tier_df, hide_index=True, use_container_width=True,
                column_config={
                    "Total $": st.column_config.NumberColumn(format="$%.2f"),
                },
            )

        with st.expander(
            "Review Queues "
            f"(Review: {estimate.operator_review_count}, "
            f"Hand: {estimate.hand_takeoff_count})",
            expanded=estimate.hand_takeoff_count > 0,
        ):
            # Phase T7 — tier-filter dropdown applied to BOTH queues.
            # Default "All" preserves the pre-T7 behaviour exactly.
            tier_filter_options = ["All"] + list(_T7_TIER_LABELS.values())
            queue_tier_filter = st.selectbox(
                "Filter queues by Cost Source Tier",
                options=tier_filter_options,
                index=0,
                key="t7_queue_tier_filter",
                help=(
                    "Narrow both queues to lines from a single catalog-"
                    "completeness tier. Useful for triaging the Missing / "
                    "Interpolated rows separately from the Category-Match ones."
                ),
            )

            def _matches_tier_filter(li) -> bool:
                if queue_tier_filter == "All":
                    return True
                return _t7_tier_label(li) == queue_tier_filter

            st.markdown("##### Operator Review Queue")
            st.caption(
                "Confidence 0.65\u20130.84 — included in totals but flagged "
                "for an eyeball before submitting."
            )
            review_lines = [
                li for li in estimate.operator_review_line_items
                if _matches_tier_filter(li)
            ]
            if not review_lines:
                if queue_tier_filter == "All":
                    st.caption("(empty — every priced row cleared the 0.85 auto-approve threshold.)")
                else:
                    st.caption(f"(no operator-review lines match tier '{queue_tier_filter}'.)")
            else:
                review_df = pd.DataFrame([
                    {
                        "CSI": li.csi_section or li.csi_division,
                        "Description": li.description,
                        "Qty": li.quantity,
                        "Unit": li.unit,
                        "Unit Cost": li.unit_cost,
                        "Total": li.total_cost,
                        "Conf": li.confidence,
                        "Tier": _t7_tier_label(li),
                        "Source": ", ".join(li.source_sheet_ids),
                        "Notes": li.notes or "",
                    }
                    for li in review_lines
                ])
                st.dataframe(
                    review_df, hide_index=True, use_container_width=True,
                    column_config={
                        "Unit Cost": st.column_config.NumberColumn(format="$%.2f"),
                        "Total":     st.column_config.NumberColumn(format="$%.2f"),
                        "Conf":      st.column_config.NumberColumn(format="%.2f"),
                        "Qty":       st.column_config.NumberColumn(format="%.2f"),
                    },
                )

            st.markdown("##### Hand Takeoff Queue")
            st.caption(
                "Confidence < 0.65 (or unit-mismatch suppressed) \u2014 excluded "
                "from the grand total. Each row needs an in-person takeoff."
            )
            hand_lines = [
                li for li in estimate.hand_takeoff_line_items
                if _matches_tier_filter(li)
            ]
            if not hand_lines:
                if queue_tier_filter == "All":
                    st.caption("(empty \u2014 no rows under 0.65 confidence and no unit-mismatch suppression.)")
                else:
                    st.caption(f"(no hand-takeoff lines match tier '{queue_tier_filter}'.)")
            else:
                hand_df = pd.DataFrame([
                    {
                        "CSI": li.csi_section or li.csi_division,
                        "Description": li.description,
                        "Qty": li.quantity,
                        "Unit": li.unit,
                        "Unit Cost": li.unit_cost,
                        "Total": li.total_cost,
                        "Conf": li.confidence,
                        "Tier": _t7_tier_label(li),
                        "Source": ", ".join(li.source_sheet_ids),
                        "Action": "Manual takeoff required",
                        "Notes": li.notes or "",
                    }
                    for li in hand_lines
                ])
                st.dataframe(
                    hand_df, hide_index=True, use_container_width=True,
                    column_config={
                        "Unit Cost": st.column_config.NumberColumn(format="$%.2f"),
                        "Total":     st.column_config.NumberColumn(format="$%.2f"),
                        "Conf":      st.column_config.NumberColumn(format="%.2f"),
                        "Qty":       st.column_config.NumberColumn(format="%.2f"),
                    },
                )

        st.divider()
        by_cat = estimate.by_cost_category
        if by_cat:
            st.subheader("Labor / material / sub split")
            cat_subtotal = estimate.subtotal or 0.0

            def _cat_tile(col, label: str, key: str) -> None:
                amount = by_cat.get(key, 0.0)
                pct = (amount / cat_subtotal * 100.0) if cat_subtotal else 0.0
                col.metric(label, f"${amount:,.0f}", f"{pct:.1f}% of subtotal")

            tile_cols = st.columns(5)
            _cat_tile(tile_cols[0], "Labor",          "labor")
            _cat_tile(tile_cols[1], "Material",       "material")
            _cat_tile(tile_cols[2], "Equipment",      "equipment")
            _cat_tile(tile_cols[3], "Subcontractor",  "subcontractor")
            _cat_tile(tile_cols[4], "Other",          "other")
            st.divider()

        # ----- Cost database breakdown (F1) -----
        st.subheader("Cost database")
        st.caption(
            "Where each line's unit cost came from. **cwicr** = matched against "
            "the 55k-row CWICR open dataset (CC-BY-4.0). **seed** = bundled "
            "47-entry seed `config/cost_database.json`. **no match** = neither "
            "layer found a unit cost; the line shows $0 and needs manual entry."
        )

        src_counts: dict[str, int] = {"cwicr": 0, "seed": 0, "no match": 0}
        cwicr_sims: list[float] = []
        for li in estimate.line_items:
            src = li.cost_source or ""
            if src.startswith("cwicr:"):
                src_counts["cwicr"] += 1
                cwicr_sims.append(float(li.confidence))
            elif src in ("", "(no match)"):
                src_counts["no match"] += 1
            else:
                src_counts["seed"] += 1

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("CWICR",     src_counts["cwicr"])
        sc2.metric("Seed DB",   src_counts["seed"])
        sc3.metric("No match",  src_counts["no match"])
        avg_sim = (sum(cwicr_sims) / len(cwicr_sims)) if cwicr_sims else 0.0
        sc4.metric("Avg CWICR sim", f"{avg_sim:.2f}" if cwicr_sims else "—")

        # Pie / bar chart of the breakdown.
        breakdown_df = pd.DataFrame(
            [{"source": k, "lines": v} for k, v in src_counts.items() if v > 0]
        )
        if not breakdown_df.empty:
            st.bar_chart(breakdown_df.set_index("source"))

        # Session-scoped toggle to disable CWICR + a re-price button.
        cwicr_off_now = st.session_state.get("cwicr_disabled_session", False)
        new_disabled = st.checkbox(
            "Disable CWICR for this session (use seed DB only)",
            value=cwicr_off_now,
            help=(
                "Toggle to re-price with the seed DB only — useful for "
                "before/after comparisons. Affects this Streamlit session "
                "only; does not write to `.env`."
            ),
            key="cwicr_disabled_session",
        )
        if st.button("Re-price with current CWICR setting", use_container_width=True):
            with st.spinner("Re-pricing…"):
                new_estimate = price_takeoff(
                    project,
                    project_name=estimate.project_name,
                    region_multiplier=estimate.region_multiplier,
                    contingency_pct=estimate.contingency_pct,
                    overhead_pct=estimate.overhead_pct,
                    profit_pct=estimate.profit_pct,
                    cost_db=CostDatabase(),
                    use_cwicr=not new_disabled,
                )
            st.session_state["estimate"] = new_estimate
            st.rerun()

        st.divider()
        st.subheader("Priced line items")
        priced = estimate.priced_line_items
        suppressed = estimate.suppressed_line_items
        df = pd.DataFrame([li.model_dump() for li in priced])
        if df.empty:
            st.info("No priced line items yet.")
        else:
            df["source_sheet_ids"] = df["source_sheet_ids"].apply(lambda xs: ", ".join(xs))

            def _src_family(s: str) -> str:
                if not s or s == "(no match)":
                    return "no match"
                if s.startswith("cwicr:"):
                    return "cwicr"
                return "seed"

            df["src_family"] = df["cost_source"].apply(_src_family)
            # CWICR similarity is the same as `confidence` for CWICR rows;
            # show it as a separate column for at-a-glance match quality.
            df["cwicr_sim"] = [
                float(li.confidence) if (li.cost_source or "").startswith("cwicr:") else None
                for li in priced
            ]
            edited = st.data_editor(
                df[
                    [
                        "csi_division", "csi_section", "cost_category", "description",
                        "raw_quantity", "waste_factor", "quantity", "unit",
                        "unit_cost", "total_cost",
                        "confidence", "src_family", "cwicr_sim",
                        "source_sheet_ids", "cost_source", "notes",
                    ]
                ].rename(columns={
                    "csi_division": "Div", "csi_section": "Section",
                    "cost_category": "Category",
                    "description": "Description",
                    "raw_quantity": "Raw Qty", "waste_factor": "Waste",
                    "quantity": "Qty",
                    "unit": "Unit", "unit_cost": "Unit Cost",
                    "total_cost": "Total", "confidence": "Conf",
                    "src_family": "Cost Source",
                    "cwicr_sim": "CWICR Sim",
                    "source_sheet_ids": "Source Sheets",
                    "cost_source": "Cost Key", "notes": "Notes",
                }),
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Unit Cost":  st.column_config.NumberColumn(format="$%.2f"),
                    "Total":      st.column_config.NumberColumn(format="$%.2f"),
                    "Conf":       st.column_config.NumberColumn(format="%.2f"),
                    "Qty":        st.column_config.NumberColumn(format="%.2f"),
                    "Raw Qty":    st.column_config.NumberColumn(format="%.2f"),
                    "Waste":      st.column_config.NumberColumn(format="%.2f"),
                    "CWICR Sim":  st.column_config.NumberColumn(format="%.2f"),
                },
            )
            if st.button("Recalculate totals from edited table", use_container_width=True):
                edited["Total"] = (edited["Qty"].fillna(0) * edited["Unit Cost"].fillna(0)).round(2)
                # Update only the priced (non-suppressed) lines in place, in
                # the same order they were rendered.
                for i, li in enumerate(priced):
                    if i >= len(edited):
                        break
                    li.quantity = float(edited.iloc[i]["Qty"] or 0)
                    li.unit_cost = float(edited.iloc[i]["Unit Cost"] or 0)
                    li.total_cost = round(li.quantity * li.unit_cost, 2)
                st.session_state["estimate"] = estimate
                st.rerun()

        if suppressed:
            with st.expander(
                f"Unmatched / suppressed lines ({len(suppressed)}) — not in totals",
                expanded=False,
            ):
                st.caption(
                    "These takeoff lines were detected but couldn't be priced "
                    "safely (typically unit mismatch between the takeoff and the "
                    "cost-DB entry). They are listed here for visibility and are "
                    "excluded from every total / rollup."
                )
                sup_df = pd.DataFrame([li.model_dump() for li in suppressed])
                sup_df["source_sheet_ids"] = sup_df["source_sheet_ids"].apply(
                    lambda xs: ", ".join(xs)
                )
                st.dataframe(
                    sup_df[
                        [
                            "csi_division", "csi_section", "description",
                            "raw_quantity", "quantity", "unit", "cost_source", "notes",
                        ]
                    ].rename(columns={
                        "csi_division": "Div", "csi_section": "Section",
                        "description": "Description",
                        "raw_quantity": "Raw Qty", "quantity": "Qty",
                        "unit": "Unit", "cost_source": "Cost Key", "notes": "Notes",
                    }),
                    hide_index=True,
                    use_container_width=True,
                )

        # ------------------------------------------------------------------
        # Phase T6.2 — Operator price overrides
        # ------------------------------------------------------------------
        #
        # Wires ``apply_manual_override`` (T6.1) into the Streamlit
        # round-trip with vendor / quote-ref attribution and an
        # operator-note field. Sits after the suppressed expander so
        # the operator's mental flow is "look at table → spot a row
        # that needs a hand-priced number → apply override → see new
        # totals". Snapshot + history live in session-state, seeded
        # by ``_initialize_override_session_state`` at analyze time.

        # Defensive: if a session predates T6.2 (estimate already in
        # session_state from a pre-T6.2 run), seed the snapshot now so
        # the rest of the section works cleanly.
        if "estimate_original" not in st.session_state:
            st.session_state["estimate_original"] = estimate.model_copy(deep=True)
        if "override_history" not in st.session_state:
            st.session_state["override_history"] = []

        estimate_original: Estimate = st.session_state["estimate_original"]
        override_history: list[dict[str, Any]] = st.session_state["override_history"]

        # Top-of-section banner for context — only shown when overrides exist.
        manual_override_lines = [
            li for li in estimate.line_items
            if li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
        ]
        if manual_override_lines:
            adj_total = sum(
                li.total_cost - estimate_original.line_items[i].total_cost
                for i, li in enumerate(estimate.line_items)
                if li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
                and i < len(estimate_original.line_items)
            )
            adj_sign = "+" if adj_total >= 0 else "\u2212"
            st.info(
                f"\U0001F4DD {len(manual_override_lines)} manual override"
                f"{'s' if len(manual_override_lines) != 1 else ''} applied "
                f"\u2014 {adj_sign}${abs(adj_total):,.2f} total adjustment "
                f"vs. original."
            )

        with st.expander(
            "Operator price overrides (Phase T6.2)",
            expanded=False,
        ):
            st.caption(
                "Hand-price a single line by entering a vendor-quote unit "
                "cost. Overrides stamp ``cost_source_tier = MANUAL_OVERRIDE`` "
                "and ``price_confidence = 1.0`` on the line, force "
                "``suppressed = False`` (manual pricing IS the resolution "
                "to a unit-mismatch suppression), and recompute the band "
                "against the new combined confidence. A vendor / "
                "quote-ref / free-text note is stamped onto the line's "
                "``notes`` field with the ``operator override`` sentinel "
                "so downstream readers (Excel / PDF / CSV) can detect the "
                "override."
            )

            all_lines = list(estimate.line_items)
            if not all_lines:
                st.info("No line items to override.")
            else:
                indexed_sorted = _sort_lines_by_tier(all_lines)
                label_to_idx: dict[str, int] = {}
                labels: list[str] = []
                for orig_idx, li in indexed_sorted:
                    label = _select_line_label(orig_idx, li)
                    # Disambiguate the rare collision (same desc / unit /
                    # cost / tier on two indices) by appending the index.
                    if label in label_to_idx:
                        label = f"{label} (idx={orig_idx})"
                    label_to_idx[label] = orig_idx
                    labels.append(label)

                with st.form("operator_override_form", clear_on_submit=False):
                    selected_label = st.selectbox(
                        "Line to override",
                        options=labels,
                        index=0,
                        help=(
                            "Lines are sorted MANUAL_OVERRIDE first, then "
                            "EXACT \u2192 CATEGORY \u2192 INTERPOLATED \u2192 "
                            "PARAMETRIC \u2192 MISSING. The leading #N is "
                            "the stable line index used by the override "
                            "pass."
                        ),
                    )
                    selected_idx = label_to_idx.get(selected_label, 0)
                    selected_line = all_lines[selected_idx]

                    new_unit_cost = st.number_input(
                        "New unit cost",
                        min_value=0.0,
                        value=float(selected_line.unit_cost),
                        step=0.01,
                        format="%.2f",
                        help="Per-unit cost. Multiplied by the line's quantity to recompute total.",
                    )
                    vendor = st.text_input(
                        "Vendor (optional)",
                        value="",
                        placeholder="e.g., Ferguson Plumbing, Home Depot Pro",
                        help="Stamped onto the operator note as ``[vendor: ...]``.",
                    )
                    quote_ref = st.text_input(
                        "Quote / PO reference (optional)",
                        value="",
                        placeholder="e.g., Q-2026-0428, PO#12345",
                        help="Stamped onto the operator note as ``[quote-ref: ...]``.",
                    )
                    operator_free_text = st.text_area(
                        "Operator note (optional)",
                        value="",
                        placeholder="Free-form reason / context for the override",
                        height=80,
                    )
                    submitted = st.form_submit_button(
                        "Apply override",
                        use_container_width=True,
                    )

                if submitted:
                    pre_override = estimate
                    try:
                        new_estimate, formatted_note = _apply_operator_override(
                            estimate,
                            selected_idx,
                            new_unit_cost=float(new_unit_cost),
                            vendor=vendor,
                            quote_ref=quote_ref,
                            free_text=operator_free_text,
                        )
                    except ValueError as exc:
                        st.error(f"Override failed: {exc}")
                    else:
                        old_line = pre_override.line_items[selected_idx]
                        new_line = new_estimate.line_items[selected_idx]
                        # Append to history BEFORE rerun so the CSV
                        # download (rendered on the next pass) includes
                        # this entry.
                        override_history.append({
                            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                            "line_index": selected_idx,
                            "description": old_line.description,
                            "csi_division": old_line.csi_division,
                            "csi_section": old_line.csi_section or "",
                            "original_unit_cost": round(float(old_line.unit_cost), 2),
                            "new_unit_cost": round(float(new_line.unit_cost), 2),
                            "operator_note": formatted_note or "",
                        })
                        st.session_state["override_history"] = override_history
                        st.session_state["estimate"] = new_estimate
                        st.success(
                            f"Override applied to line #{selected_idx} "
                            f"(``{_t7_tier_label(new_line)}``, band "
                            f"``{new_line.cost_band.value}``). "
                            f"New total: ${new_line.total_cost:,.2f}."
                        )
                        st.caption(
                            _format_override_delta(
                                pre_override, new_estimate, selected_idx
                            )
                        )
                        st.rerun()

            # ----- Override history (read-only) ---------------------------

            if override_history or manual_override_lines:
                st.markdown("##### Override history")
                history_rows = []
                for entry in override_history:
                    history_rows.append({
                        "Timestamp (UTC)": entry["timestamp"],
                        "Line #": entry["line_index"],
                        "Description": entry["description"],
                        "Orig $": entry["original_unit_cost"],
                        "New $": entry["new_unit_cost"],
                        "Note": entry["operator_note"],
                    })
                if history_rows:
                    hist_df = pd.DataFrame(history_rows)
                    st.dataframe(
                        hist_df,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Orig $": st.column_config.NumberColumn(format="$%.2f"),
                            "New $": st.column_config.NumberColumn(format="$%.2f"),
                        },
                    )
                else:
                    st.caption(
                        "No overrides applied in this session yet. (Manual "
                        "Override-tier rows below are from a prior pass.)"
                    )

                # CSV export — every MANUAL_OVERRIDE-tier line in the current
                # estimate, with the original unit cost pulled from the snapshot
                # when the index aligns. Audit-trail artefact for the project file.
                csv_rows: list[dict[str, Any]] = []
                history_by_idx = {
                    e["line_index"]: e for e in reversed(override_history)
                }
                for idx, li in enumerate(estimate.line_items):
                    if li.cost_source_tier != CostSourceTier.MANUAL_OVERRIDE:
                        continue
                    orig_uc: float = 0.0
                    if idx < len(estimate_original.line_items):
                        orig_uc = round(
                            float(estimate_original.line_items[idx].unit_cost), 2
                        )
                    last_entry = history_by_idx.get(idx)
                    csv_rows.append({
                        "timestamp": last_entry["timestamp"] if last_entry else "",
                        "line_index": idx,
                        "description": li.description,
                        "csi_division": li.csi_division,
                        "csi_section": li.csi_section or "",
                        "original_unit_cost": orig_uc,
                        "new_unit_cost": round(float(li.unit_cost), 2),
                        "operator_note": li.notes or "",
                    })
                csv_text = _build_override_history_csv(csv_rows)
                st.download_button(
                    "Download override history CSV",
                    data=csv_text,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_overrides.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    disabled=not csv_rows,
                    help=(
                        "Exports every ``MANUAL_OVERRIDE``-tier line "
                        "with original \u2192 new unit cost + operator note. "
                        "Disabled when no overrides are present."
                    ),
                )

                # Reset strategy: SINGLE GLOBAL "Reset all overrides"
                # button (per the brief's "pick the simpler option"
                # guidance). Restores the pre-override snapshot
                # captured at analyze time. A per-line stack-based
                # reset would require tracking the prior estimate per
                # override application and would push session-state
                # complexity past the simplification line for this
                # slice.
                if st.button(
                    "Reset all overrides (restore original estimate)",
                    use_container_width=True,
                    help=(
                        "Restores the pre-override estimate snapshot "
                        "captured when this analyze run completed. "
                        "Clears the override history."
                    ),
                ):
                    st.session_state["estimate"] = estimate_original.model_copy(
                        deep=True
                    )
                    st.session_state["override_history"] = []
                    st.success("All overrides reverted; history cleared.")
                    st.rerun()

            # ------------------------------------------------------------------
            # Phase T6.4.d — per-line override undo
            # ------------------------------------------------------------------
            #
            # Stack-pop revert affordance for every line whose
            # ``override_snapshots`` is non-empty. Lives inside the existing
            # operator-override expander so all override-related controls
            # cluster in one place. Two surfaces:
            #
            #   1. Per-line ``↶ revert`` button — one per revertable line.
            #      Pops the stack-top snapshot via the pure helper
            #      ``_apply_per_line_revert`` and re-renders.
            #   2. Bulk ``↶ Revert all batch applies`` button — iterates
            #      every revertable line and pops one snapshot each.
            #      Useful when an operator applied the wrong vendor CSV
            #      to 200 lines and wants to undo every line in one click.
            #
            # Distinct from the global "Reset all overrides" button above:
            # that one wipes the entire override history back to the
            # pre-override snapshot. Per-line undo is a single layer pop
            # — multi-layer chains (priced default → batch → manual)
            # require multiple clicks to fully unwind.

            revertable_indices = _revertable_line_indices(estimate)
            if revertable_indices:
                st.markdown("##### Per-line override undo (Phase T6.4.d)")
                st.caption(
                    "Each row below has at least one captured pre-override "
                    "snapshot. Click ``\u21B6 revert`` to pop the most "
                    "recent override on that line and restore it to the "
                    "previous state. Multi-layer chains (e.g. priced "
                    "default \u2192 vendor batch \u2192 manual override) "
                    "require one click per layer."
                )

                if st.button(
                    "\u21B6 Revert all batch applies (in reverse order)",
                    use_container_width=True,
                    key="bulk_revert_all_button",
                    help=(
                        f"Pops the most recent snapshot on every "
                        f"revertable line ({len(revertable_indices)} "
                        f"line(s) currently have at least one snapshot). "
                        f"Useful when the wrong CSV was applied. "
                        f"This cannot be undone."
                    ),
                ):
                    new_estimate, popped_list = _bulk_revert_all(estimate)
                    st.session_state["estimate"] = new_estimate
                    st.success(
                        f"\u21B6 Reverted {len(popped_list)} override(s) "
                        f"across {len(revertable_indices)} line(s). The "
                        f"earlier override layer (if any) is preserved "
                        f"and can be reverted with another click."
                    )
                    st.rerun()

                # Per-line revert table. Columns: line #, description,
                # current unit cost, depth (snapshot count), revert button.
                # Streamlit doesn't support a native per-row button column
                # in dataframes, so we render rows as a simple repeating
                # 5-column layout — survives narrow widths and is
                # accessible to keyboard users.
                for idx in revertable_indices:
                    li = estimate.line_items[idx]
                    snap_top = li.override_snapshots[-1]
                    col_idx, col_desc, col_uc, col_depth, col_btn = st.columns(
                        [0.6, 4.0, 1.2, 0.8, 1.4]
                    )
                    col_idx.write(f"#{idx}")
                    desc_short = (
                        (li.description[:60] + "\u2026")
                        if len(li.description) > 60
                        else li.description
                    )
                    col_desc.write(desc_short)
                    col_uc.write(f"${li.unit_cost:,.2f}/{li.unit}")
                    col_depth.write(f"{len(li.override_snapshots)} layer(s)")
                    if col_btn.button(
                        "\u21B6 revert",
                        key=f"per_line_revert_button_{idx}",
                        help=(
                            f"Roll back to: {_format_snapshot_label(snap_top)}"
                        ),
                        use_container_width=True,
                    ):
                        new_estimate, popped = _apply_per_line_revert(
                            estimate, idx
                        )
                        st.session_state["estimate"] = new_estimate
                        if popped is not None:
                            st.success(
                                f"\u21B6 Reverted line #{idx} to "
                                f"{popped.source_tag or '(priced default)'} "
                                f"(captured "
                                f"{popped.applied_at.strftime('%H:%M UTC')}; "
                                f"unit_cost ${popped.unit_cost:,.2f})."
                            )
                        else:
                            st.warning(
                                f"Line #{idx} had no snapshot to revert."
                            )
                        st.rerun()

                with st.expander(
                    f"Show full undo history "
                    f"({sum(len(estimate.line_items[i].override_snapshots) for i in revertable_indices)} "
                    f"snapshot(s) across {len(revertable_indices)} line(s))",
                    expanded=False,
                ):
                    history_rows: list[dict[str, Any]] = []
                    for idx in revertable_indices:
                        history_rows.extend(
                            _build_revert_history_rows(
                                estimate.line_items[idx], idx
                            )
                        )
                    if history_rows:
                        hist_df = pd.DataFrame(history_rows)
                        st.dataframe(
                            hist_df,
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Unit cost": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                                "Total cost": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                            },
                        )

        # ------------------------------------------------------------------
        # Phase T6.3 — Batch operator overrides from vendor CSV
        # ------------------------------------------------------------------
        #
        # Wires ``core.pricing.batch_override`` into the Streamlit Estimate
        # tab as the bulk-CSV analogue of the T6.2 single-line affordance.
        # Two-stage flow (preview → apply) is mandatory: the operator must
        # see the match plan BEFORE any override is applied, because a
        # batch op touches many lines at once and a mismatch in the fuzzy
        # matcher could otherwise nuke the entire estimate silently.
        #
        # Session-state keys consumed (already seeded by T6.2):
        #   - ``estimate_original`` — pre-override snapshot (for the
        #     reset path; this section does not touch it).
        #   - ``override_history``  — appended to on each successful
        #     batch apply so the existing T6.2 history download stays
        #     authoritative.
        #
        # New (transient) session-state keys this section introduces:
        #   - ``batch_override_plan`` — the most recent
        #     :class:`BatchOverridePlan` for preview rendering.
        #   - ``batch_override_csv_lines`` — the parsed
        #     :class:`BatchOverrideRow` list (kept for plan re-derivation
        #     when the operator re-runs with different thresholds).
        #   - ``batch_override_resolved`` — dict mapping CSV row index
        #     to operator-chosen CostLine index for AMBIGUOUS rows.
        with st.expander(
            "Batch operator overrides from vendor CSV (Phase T6.3)",
            expanded=False,
        ):
            st.caption(
                "Upload a vendor pricing CSV (description + unit_cost "
                "columns required; optional vendor / quote_ref / notes / "
                "quantity). The matcher fuzzy-aligns each row to a "
                "CostLine by description and surfaces a preview before "
                "any override is committed. MATCHED rows auto-apply; "
                "AMBIGUOUS rows wait for operator resolution; "
                "LOW_SIMILARITY and NO_MATCH rows are flagged for "
                "manual review and never auto-applied."
            )

            uploaded_csv = st.file_uploader(
                "Vendor pricing CSV or xlsx workbook",
                type=["csv", "xlsx"],
                key="batch_override_csv_uploader",
                help=(
                    "Required columns (any of the case-insensitive "
                    "aliases): description / desc / item / "
                    "item_description / line_item AND unit_cost / price / "
                    "unit_price / cost / $/unit / rate. Optional: "
                    "vendor, quote_ref, notes, quantity, "
                    "unit_of_measure. "
                    "Phase T6.4.a: .xlsx workbooks are accepted too — "
                    "each sheet is treated as a separate vendor table "
                    "and the operator picks which sheets to merge "
                    "before applying."
                ),
            )

            with st.expander("Matching settings (advanced)", expanded=False):
                similarity_threshold = st.slider(
                    "Similarity threshold",
                    min_value=0.40,
                    max_value=0.95,
                    value=0.65,
                    step=0.01,
                    key="batch_override_threshold",
                    help=(
                        "Minimum description-similarity for a row to "
                        "be considered MATCHED or AMBIGUOUS. Below this "
                        "and above 0.40 lands in LOW_SIMILARITY (manual "
                        "review). Below 0.40 lands in NO_MATCH. Default "
                        "0.65 aligns with the Phase T6 OPERATOR_REVIEW "
                        "band boundary."
                    ),
                )
                ambiguity_margin = st.slider(
                    "Ambiguity margin",
                    min_value=0.05,
                    max_value=0.30,
                    value=0.10,
                    step=0.01,
                    key="batch_override_margin",
                    help=(
                        "Two CostLines whose similarities to the same "
                        "CSV row are within this margin are flagged "
                        "AMBIGUOUS and require operator resolution. "
                        "Default 0.10 distinguishes 'walls vs. ceiling' "
                        "(amb.) from 'Door 101A vs. 201A' (auto-resolved)."
                    ),
                )

            preview_clicked = st.button(
                "Preview match plan",
                use_container_width=True,
                disabled=uploaded_csv is None,
                key="batch_override_preview_btn",
                help=(
                    "Parse the CSV + build the match plan. Does NOT "
                    "apply any overrides. Required before the Apply "
                    "button activates."
                ),
            )

            if preview_clicked and uploaded_csv is not None:
                # Phase T6.4.a — branch on the upload extension. The
                # ``.xlsx`` path produces a dict of per-sheet plans and
                # routes through the sheet-selector UI below; the
                # ``.csv`` path is the legacy T6.3 flow unchanged.
                uploaded_name = (uploaded_csv.name or "").lower()
                if uploaded_name.endswith(".xlsx"):
                    try:
                        raw_bytes = uploaded_csv.getvalue()
                    except Exception as exc:
                        st.error(f"Could not read xlsx bytes: {exc}")
                    else:
                        try:
                            xlsx_plans = parse_vendor_xlsx(raw_bytes)
                        except ValueError as exc:
                            st.error(f"xlsx parse failed: {exc}")
                        else:
                            st.session_state["batch_override_xlsx_plans"] = (
                                xlsx_plans
                            )
                            st.session_state[
                                "batch_override_xlsx_selected"
                            ] = list(xlsx_plans.keys())
                            st.session_state.pop("batch_override_plan", None)
                            st.session_state.pop(
                                "batch_override_csv_lines", None
                            )
                            st.session_state["batch_override_resolved"] = {}
                else:
                    try:
                        raw_bytes = uploaded_csv.getvalue()
                        csv_text = raw_bytes.decode("utf-8-sig")
                    except Exception as exc:
                        st.error(f"Could not decode CSV: {exc}")
                    else:
                        # Drop any stale xlsx state so the sheet-selector
                        # UI doesn't render alongside a CSV-only flow.
                        st.session_state.pop(
                            "batch_override_xlsx_plans", None
                        )
                        st.session_state.pop(
                            "batch_override_xlsx_selected", None
                        )
                        try:
                            parsed_rows, parse_errors = parse_vendor_csv(
                                csv_text
                            )
                        except ValueError as exc:
                            st.error(f"CSV parse failed: {exc}")
                            parsed_rows, parse_errors = [], []
                        if parse_errors:
                            for err in parse_errors:
                                st.warning(err)
                        if parsed_rows:
                            plan = match_cost_lines(
                                parsed_rows,
                                list(estimate.line_items),
                                similarity_threshold=float(
                                    similarity_threshold
                                ),
                                ambiguity_margin=float(ambiguity_margin),
                            )
                            st.session_state["batch_override_plan"] = plan
                            st.session_state["batch_override_csv_lines"] = (
                                parsed_rows
                            )
                            st.session_state["batch_override_resolved"] = {}

            # Phase T6.4.a — xlsx multi-sheet selector + merge + match.
            # Renders when a workbook has been parsed (session-state
            # carries ``batch_override_xlsx_plans``) so a deselect /
            # re-select triggers a rerun → re-merge → re-match against
            # the current threshold + margin without re-parsing the
            # workbook bytes. The downstream preview / apply block
            # consumes whatever lands in ``batch_override_plan``, so
            # the rest of the section is xlsx-agnostic.
            xlsx_plans = st.session_state.get(
                "batch_override_xlsx_plans"
            )
            if xlsx_plans:
                sheet_names = list(xlsx_plans.keys())
                summary_rows = []
                for sheet_name, sheet_plan in xlsx_plans.items():
                    plan_rows = [
                        r.row for r in sheet_plan.no_match
                    ]
                    if plan_rows:
                        sample = plan_rows[0]
                        sample_bits = [
                            sample.description[:40],
                            sample.vendor or "",
                            sample.unit_of_measure or "",
                        ]
                        sample_header = " | ".join(
                            bit for bit in sample_bits if bit
                        )
                    else:
                        sample_header = "(no data rows)"
                    summary_rows.append({
                        "Sheet": sheet_name,
                        "Row count": sheet_plan.total_rows,
                        "Sample row": sample_header,
                    })
                st.markdown("##### Workbook sheet summary")
                st.dataframe(
                    pd.DataFrame(summary_rows),
                    hide_index=True,
                    use_container_width=True,
                )

                default_selection = st.session_state.get(
                    "batch_override_xlsx_selected", sheet_names
                )
                # Defensive: drop stale entries if the workbook changed.
                default_selection = [
                    s for s in default_selection if s in sheet_names
                ]
                selected_sheets = st.multiselect(
                    "Sheets to apply",
                    options=sheet_names,
                    default=default_selection,
                    key="batch_override_xlsx_selector",
                    help=(
                        "Deselect cover sheets / summary tabs / sheets "
                        "you don't want to apply. Selected sheets are "
                        "merged into a single match plan; sheet "
                        "provenance is preserved in each row's notes "
                        "field via the '[sheet: <name>]' prefix."
                    ),
                )
                st.session_state["batch_override_xlsx_selected"] = (
                    selected_sheets
                )

                if not selected_sheets:
                    st.info(
                        "No sheets selected — choose at least one "
                        "sheet to build the match plan."
                    )
                    st.session_state.pop("batch_override_plan", None)
                    st.session_state.pop(
                        "batch_override_csv_lines", None
                    )
                else:
                    filtered_plans = OrderedDict(
                        (name, xlsx_plans[name])
                        for name in selected_sheets
                    )
                    try:
                        merged = merge_xlsx_plans(filtered_plans)
                    except ValueError as exc:
                        st.error(f"xlsx merge failed: {exc}")
                    else:
                        merged_rows = [
                            r.row for r in merged.no_match
                        ]
                        if merged_rows:
                            plan = match_cost_lines(
                                merged_rows,
                                list(estimate.line_items),
                                similarity_threshold=float(
                                    similarity_threshold
                                ),
                                ambiguity_margin=float(
                                    ambiguity_margin
                                ),
                            )
                            st.session_state[
                                "batch_override_plan"
                            ] = plan
                            st.session_state[
                                "batch_override_csv_lines"
                            ] = merged_rows
                        else:
                            st.info(
                                "Selected sheets contain no priceable "
                                "rows (all sheets had only a header)."
                            )
                            st.session_state.pop(
                                "batch_override_plan", None
                            )

            plan: BatchOverridePlan | None = st.session_state.get(
                "batch_override_plan"
            )
            if plan is not None:
                summary = _summarize_batch_plan(plan, estimate)
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Total rows", summary["total_rows"])
                m2.metric("Matched", summary["matched_count"])
                m3.metric("Ambiguous", summary["ambiguous_count"])
                m4.metric("Low similarity", summary["low_similarity_count"])
                m5.metric("No match", summary["no_match_count"])
                adj = summary["estimated_total_adjustment"]
                adj_sign = "+" if adj >= 0 else "\u2212"
                st.caption(
                    f"Estimated subtotal adjustment if all MATCHED rows "
                    f"are applied: {adj_sign}${abs(adj):,.2f}."
                )

                if plan.matched:
                    st.markdown("##### Matched rows (auto-apply)")
                    matched_rows = []
                    for result in plan.matched:
                        if result.best_match_index is None:
                            continue
                        line = estimate.line_items[result.best_match_index]
                        matched_rows.append({
                            "CSV row": result.row.row_index,
                            "CSV description": result.row.description,
                            "Cost line #": result.best_match_index,
                            "Cost line description": line.description,
                            "Sim": round(result.best_match_similarity, 3),
                            "Old $/unit": round(float(line.unit_cost), 2),
                            "New $/unit": round(float(result.row.unit_cost), 2),
                        })
                    if matched_rows:
                        st.dataframe(
                            pd.DataFrame(matched_rows),
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Old $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                                "New $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                            },
                        )

                if plan.ambiguous:
                    st.markdown("##### Ambiguous rows (operator resolution required)")
                    resolved: dict[int, int] = st.session_state.get(
                        "batch_override_resolved", {}
                    )
                    for result in plan.ambiguous:
                        candidates: list[tuple[str, int | None]] = [
                            ("Skip this row", None),
                        ]
                        for idx, sim in result.candidate_lines:
                            if 0 <= idx < len(estimate.line_items):
                                desc = estimate.line_items[idx].description[:60]
                                candidates.append(
                                    (f"#{idx} | {desc} | sim={sim:.2f}", idx)
                                )
                        labels = [label for label, _ in candidates]
                        current_choice = resolved.get(result.row.row_index)
                        default_index = 0
                        for i, (_, idx) in enumerate(candidates):
                            if idx == current_choice:
                                default_index = i
                                break
                        chosen_label = st.selectbox(
                            f"Row {result.row.row_index}: "
                            f"{result.row.description[:80]}",
                            options=labels,
                            index=default_index,
                            key=f"batch_amb_resolve_{result.row.row_index}",
                        )
                        chosen_idx = dict(candidates)[chosen_label]
                        if chosen_idx is None:
                            resolved.pop(result.row.row_index, None)
                        else:
                            resolved[result.row.row_index] = chosen_idx
                    st.session_state["batch_override_resolved"] = resolved

                unmatched = list(plan.low_similarity) + list(plan.no_match)
                if unmatched:
                    st.markdown("##### Unmatched rows (read-only audit)")
                    unmatched_rows = []
                    for result in unmatched:
                        unmatched_rows.append({
                            "CSV row": result.row.row_index,
                            "CSV description": result.row.description,
                            "Best sim": round(result.best_match_similarity, 3),
                            "Status": result.status.value,
                            "Notes": result.row.notes or "",
                        })
                    st.dataframe(
                        pd.DataFrame(unmatched_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

                plan_csv = export_match_plan_csv(plan, list(estimate.line_items))
                st.download_button(
                    "Download match plan CSV",
                    data=plan_csv,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_batch_match_plan.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    key="batch_override_plan_download",
                    help=(
                        "Audit-trail snapshot of the match plan: per-row "
                        "status, best + runner-up similarity, candidate "
                        "descriptions. Useful for offline review before "
                        "committing the batch."
                    ),
                )

                apply_clicked = st.button(
                    "Apply batch overrides",
                    use_container_width=True,
                    type="primary",
                    key="batch_override_apply_btn",
                    disabled=(
                        len(plan.matched) == 0
                        and not st.session_state.get(
                            "batch_override_resolved", {}
                        )
                    ),
                    help=(
                        "Applies every MATCHED row + every operator-"
                        "resolved AMBIGUOUS row. LOW_SIMILARITY and "
                        "NO_MATCH rows are always skipped. Updates the "
                        "estimate in place and appends to the override "
                        "history."
                    ),
                )

                if apply_clicked:
                    resolved_map: dict[int, int] = st.session_state.get(
                        "batch_override_resolved", {}
                    )
                    pre_apply = estimate
                    try:
                        new_estimate, apply_summary = apply_batch_plan(
                            estimate,
                            plan,
                            auto_apply_matched=True,
                            resolved_ambiguous=resolved_map,
                            source_tag=SOURCE_TAG_VENDOR_CSV,
                        )
                    except Exception as exc:
                        st.error(f"Batch apply failed: {exc}")
                    else:
                        applied_results: list[BatchMatchResult] = list(plan.matched)
                        for result in plan.ambiguous:
                            if result.row.row_index in resolved_map:
                                # Forge a synthesised result with the
                                # resolved index in best_match_index so
                                # the history row points at the line the
                                # override actually touched.
                                applied_results.append(BatchMatchResult(
                                    row=result.row,
                                    status=BatchMatchStatus.MATCHED,
                                    best_match_index=resolved_map[
                                        result.row.row_index
                                    ],
                                    best_match_similarity=(
                                        result.best_match_similarity
                                    ),
                                    runner_up_index=result.runner_up_index,
                                    runner_up_similarity=(
                                        result.runner_up_similarity
                                    ),
                                    candidate_lines=result.candidate_lines,
                                ))

                        now_ts = datetime.utcnow().isoformat(timespec="seconds")
                        for result in applied_results:
                            if result.best_match_index is None:
                                continue
                            if not 0 <= result.best_match_index < len(
                                pre_apply.line_items
                            ):
                                continue
                            old_line = pre_apply.line_items[
                                result.best_match_index
                            ]
                            new_line = new_estimate.line_items[
                                result.best_match_index
                            ]
                            note = format_batch_operator_note(
                                result.row,
                                source_tag=SOURCE_TAG_VENDOR_CSV,
                            )
                            override_history.append({
                                "timestamp": now_ts,
                                "line_index": result.best_match_index,
                                "description": old_line.description,
                                "csi_division": old_line.csi_division,
                                "csi_section": old_line.csi_section or "",
                                "original_unit_cost": round(
                                    float(old_line.unit_cost), 2
                                ),
                                "new_unit_cost": round(
                                    float(new_line.unit_cost), 2
                                ),
                                "operator_note": note,
                            })

                        st.session_state["override_history"] = override_history
                        st.session_state["estimate"] = new_estimate
                        st.session_state.pop("batch_override_plan", None)
                        st.session_state.pop("batch_override_csv_lines", None)
                        st.session_state.pop("batch_override_resolved", None)
                        # Phase T6.4.a — also clear xlsx-specific state
                        # so the next upload starts fresh and the sheet
                        # selector doesn't render against a stale dict.
                        st.session_state.pop(
                            "batch_override_xlsx_plans", None
                        )
                        st.session_state.pop(
                            "batch_override_xlsx_selected", None
                        )

                        applied_count = sum(
                            1 for line in apply_summary
                            if line.startswith("Row") and "APPLIED" in line
                        )
                        st.success(
                            f"Batch override applied: {applied_count} line"
                            f"{'s' if applied_count != 1 else ''} updated. "
                            f"Subtotal: ${pre_apply.subtotal:,.2f} "
                            f"\u2192 ${new_estimate.subtotal:,.2f}."
                        )
                        with st.expander("Apply summary (full log)", expanded=False):
                            for line in apply_summary:
                                st.text(line)
                        st.rerun()

        # ------------------------------------------------------------------
        # Phase T8.1 — Sub-quote PDF ingestion (tabular)
        # ------------------------------------------------------------------
        #
        # Wires ``core.pricing.subquote_parser.parse_subquote_pdf`` into
        # the Streamlit Estimate tab as the PDF-quote analogue of the T6.3
        # vendor-CSV uploader. The parser converts tabular sub-quote PDFs
        # into the same ``list[BatchOverrideRow]`` shape T6.3 produces from
        # CSV, so the downstream
        # ``match_cost_lines`` + ``apply_batch_plan`` pipeline runs
        # unchanged from this point on — the only sub-quote-specific
        # delta is the ``source_tag="[sub-quote]"`` flag passed to
        # ``format_batch_operator_note`` when populating the
        # ``override_history`` audit trail.
        #
        # T8.2 (LLM-vision fallback for scanned / free-form quotes) is
        # explicitly deferred. The parser raises ``SubquoteParseError``
        # on non-tabular input; the UI surfaces the message verbatim
        # and points the operator at the T6.3 CSV uploader above.
        #
        # New (transient) session-state keys:
        #   - ``subquote_parse_result`` — most recent
        #     :class:`SubquoteParseResult` (rows + metadata + warnings).
        #   - ``subquote_plan`` — most recent
        #     :class:`BatchOverridePlan` (same dataclass as T6.3) for
        #     preview rendering.
        #   - ``subquote_resolved`` — dict mapping CSV row index to
        #     operator-chosen CostLine index for AMBIGUOUS rows
        #     (mirrors the T6.3 ``batch_override_resolved`` key).
        with st.expander(
            "Sub-quote PDF ingestion (Phase T8.1)",
            expanded=False,
        ):
            st.caption(
                "Upload a TABULAR vendor sub-quote PDF (mechanical / "
                "electrical / plumbing / glass / drywall). The parser "
                "extracts line items from the embedded table(s) into the "
                "same shape T6.3 ingests from CSV, then the matcher "
                "fuzzy-aligns each row to a CostLine. Scanned / free-form "
                "PDFs are NOT supported yet (T8.2) — convert those to CSV "
                "and use the uploader above. Preview-before-apply is "
                "mandatory: MATCHED rows auto-apply; AMBIGUOUS rows wait "
                "for operator resolution; LOW_SIMILARITY and NO_MATCH "
                "rows are flagged for manual review and never auto-applied."
            )

            uploaded_pdf = st.file_uploader(
                "Vendor sub-quote PDF",
                type=["pdf"],
                key="subquote_pdf_uploader",
                help=(
                    "Tabular sub-quote PDFs only (T8.1). The parser "
                    "looks for at least 'description' + one of "
                    "'unit_cost' / 'unit_price' / 'extended' columns. "
                    "Scanned or free-form quotes raise an error; convert "
                    "to CSV (see Vendor CSV uploader above) or wait for "
                    "T8.2 LLM-vision fallback."
                ),
            )

            parse_clicked = st.button(
                "Parse PDF + preview match plan",
                use_container_width=True,
                disabled=uploaded_pdf is None,
                key="subquote_parse_btn",
                help=(
                    "Extract line items from the PDF, then run the same "
                    "T6.3 matcher against the current estimate's "
                    "CostLines. Does NOT apply any overrides — preview "
                    "only. Required before Apply activates."
                ),
            )

            if parse_clicked and uploaded_pdf is not None:
                try:
                    pdf_bytes = uploaded_pdf.getvalue()
                except Exception as exc:
                    st.error(f"Could not read uploaded PDF: {exc}")
                    pdf_bytes = b""

                if pdf_bytes:
                    try:
                        sq_result = parse_subquote_pdf(pdf_bytes)
                    except SubquoteParseError as exc:
                        st.error(str(exc))
                        st.session_state.pop("subquote_parse_result", None)
                        st.session_state.pop("subquote_plan", None)
                        st.session_state.pop("subquote_resolved", None)
                        st.session_state.pop("subquote_source", None)
                        # T8.2 — keep the original PDF bytes so the
                        # "Try LLM extraction" button rendered below
                        # can route the same payload through the
                        # vision-LLM fallback without making the
                        # operator re-upload.
                        st.session_state["subquote_failed_pdf_bytes"] = (
                            pdf_bytes
                        )
                        st.session_state["subquote_failed_pdf_name"] = (
                            uploaded_pdf.name
                            if uploaded_pdf is not None
                            else "uploaded.pdf"
                        )
                        st.session_state["subquote_failed_error"] = str(exc)
                    else:
                        # Reuse the same T6.3 thresholds the operator
                        # tuned in the CSV expander above — single
                        # source of truth for "good-enough match" across
                        # both ingestion paths.
                        sq_threshold = float(
                            st.session_state.get(
                                "batch_override_threshold", 0.65
                            )
                        )
                        sq_margin = float(
                            st.session_state.get(
                                "batch_override_margin", 0.10
                            )
                        )
                        sq_plan = match_cost_lines(
                            sq_result.rows,
                            list(estimate.line_items),
                            similarity_threshold=sq_threshold,
                            ambiguity_margin=sq_margin,
                        )
                        st.session_state["subquote_parse_result"] = sq_result
                        st.session_state["subquote_plan"] = sq_plan
                        st.session_state["subquote_resolved"] = {}
                        st.session_state["subquote_source"] = "table"
                        # Successful tabular parse clears any stashed
                        # failure-state from a prior PDF.
                        st.session_state.pop(
                            "subquote_failed_pdf_bytes", None
                        )
                        st.session_state.pop(
                            "subquote_failed_pdf_name", None
                        )
                        st.session_state.pop(
                            "subquote_failed_error", None
                        )

            # ----------------------------------------------------------
            # T8.2 — "Try LLM extraction" button (vision-LLM fallback)
            # ----------------------------------------------------------
            #
            # Rendered only when the most recent T8.1 parse attempt
            # raised SubquoteParseError (the original error message
            # is already on screen via the st.error above). This is
            # the only LLM-spending button in the override flow, so
            # the cost estimate is shown verbatim BEFORE the click.
            sq_failed_pdf_bytes: bytes | None = st.session_state.get(
                "subquote_failed_pdf_bytes"
            )
            if sq_failed_pdf_bytes:
                st.caption(_render_subquote_llm_cost_estimate())
                llm_clicked = st.button(
                    "Try LLM extraction",
                    use_container_width=True,
                    key="subquote_llm_extract_btn",
                    help=(
                        "Render each PDF page to a PNG and send it "
                        "through the vision LLM (T8.2 fallback). Use "
                        "this when the deterministic table parser "
                        "above failed on a scanned or free-form quote. "
                        "Costs are real LLM-provider charges; review "
                        "the cost estimate above before clicking."
                    ),
                )
                if llm_clicked:
                    with st.spinner(
                        "Rendering pages and calling vision LLM..."
                    ):
                        try:
                            sq_result = parse_subquote_pdf_with_llm(
                                sq_failed_pdf_bytes
                            )
                        except SubquoteLLMError as exc:
                            st.error(
                                f"LLM extraction failed: {exc}"
                            )
                        except Exception as exc:
                            # Unexpected exception type — surface
                            # generically so operator can report it.
                            st.error(
                                f"Unexpected LLM extraction error "
                                f"({type(exc).__name__}): {exc}"
                            )
                        else:
                            sq_threshold = float(
                                st.session_state.get(
                                    "batch_override_threshold", 0.65
                                )
                            )
                            sq_margin = float(
                                st.session_state.get(
                                    "batch_override_margin", 0.10
                                )
                            )
                            sq_plan = match_cost_lines(
                                sq_result.rows,
                                list(estimate.line_items),
                                similarity_threshold=sq_threshold,
                                ambiguity_margin=sq_margin,
                            )
                            st.session_state[
                                "subquote_parse_result"
                            ] = sq_result
                            st.session_state["subquote_plan"] = sq_plan
                            st.session_state["subquote_resolved"] = {}
                            st.session_state["subquote_source"] = "llm"
                            # Successful LLM parse clears the
                            # failure-state stash.
                            st.session_state.pop(
                                "subquote_failed_pdf_bytes", None
                            )
                            st.session_state.pop(
                                "subquote_failed_pdf_name", None
                            )
                            st.session_state.pop(
                                "subquote_failed_error", None
                            )

            sq_result: SubquoteParseResult | None = st.session_state.get(
                "subquote_parse_result"
            )
            sq_plan: BatchOverridePlan | None = st.session_state.get(
                "subquote_plan"
            )
            if sq_result is not None and sq_plan is not None:
                sq_source = st.session_state.get("subquote_source", "table")
                if sq_source == "llm":
                    st.markdown(
                        _render_subquote_llm_source_banner(sq_result.metadata)
                    )
                st.markdown(_render_subquote_metadata(sq_result.metadata))
                st.caption(
                    f"Extracted **{len(sq_result.rows)}** line item"
                    f"{'s' if len(sq_result.rows) != 1 else ''} from the PDF."
                )
                if sq_result.warnings:
                    with st.expander(
                        f"Parser warnings ({len(sq_result.warnings)})",
                        expanded=False,
                    ):
                        for w in sq_result.warnings:
                            st.text(w)

                sq_summary = _summarize_batch_plan(sq_plan, estimate)
                s1, s2, s3, s4, s5 = st.columns(5)
                s1.metric("Total rows", sq_summary["total_rows"])
                s2.metric("Matched", sq_summary["matched_count"])
                s3.metric("Ambiguous", sq_summary["ambiguous_count"])
                s4.metric("Low similarity", sq_summary["low_similarity_count"])
                s5.metric("No match", sq_summary["no_match_count"])
                sq_adj = sq_summary["estimated_total_adjustment"]
                sq_sign = "+" if sq_adj >= 0 else "\u2212"
                st.caption(
                    f"Estimated subtotal adjustment if all MATCHED rows "
                    f"are applied: {sq_sign}${abs(sq_adj):,.2f}."
                )

                if sq_plan.matched:
                    st.markdown("##### Matched rows (auto-apply)")
                    sq_matched_rows = []
                    for result in sq_plan.matched:
                        if result.best_match_index is None:
                            continue
                        line = estimate.line_items[result.best_match_index]
                        sq_matched_rows.append({
                            "PDF row": result.row.row_index,
                            "PDF description": result.row.description,
                            "Cost line #": result.best_match_index,
                            "Cost line description": line.description,
                            "Sim": round(result.best_match_similarity, 3),
                            "Old $/unit": round(float(line.unit_cost), 2),
                            "New $/unit": round(
                                float(result.row.unit_cost), 2
                            ),
                        })
                    if sq_matched_rows:
                        st.dataframe(
                            pd.DataFrame(sq_matched_rows),
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Old $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                                "New $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                            },
                        )

                if sq_plan.ambiguous:
                    st.markdown(
                        "##### Ambiguous rows (operator resolution required)"
                    )
                    sq_resolved: dict[int, int] = st.session_state.get(
                        "subquote_resolved", {}
                    )
                    for result in sq_plan.ambiguous:
                        candidates: list[tuple[str, int | None]] = [
                            ("Skip this row", None),
                        ]
                        for idx, sim in result.candidate_lines:
                            if 0 <= idx < len(estimate.line_items):
                                desc = estimate.line_items[idx].description[:60]
                                candidates.append(
                                    (f"#{idx} | {desc} | sim={sim:.2f}", idx)
                                )
                        labels = [label for label, _ in candidates]
                        current_choice = sq_resolved.get(result.row.row_index)
                        default_index = 0
                        for i, (_, idx) in enumerate(candidates):
                            if idx == current_choice:
                                default_index = i
                                break
                        chosen_label = st.selectbox(
                            f"PDF row {result.row.row_index}: "
                            f"{result.row.description[:80]}",
                            options=labels,
                            index=default_index,
                            key=f"subquote_amb_resolve_{result.row.row_index}",
                        )
                        chosen_idx = dict(candidates)[chosen_label]
                        if chosen_idx is None:
                            sq_resolved.pop(result.row.row_index, None)
                        else:
                            sq_resolved[result.row.row_index] = chosen_idx
                    st.session_state["subquote_resolved"] = sq_resolved

                sq_unmatched = (
                    list(sq_plan.low_similarity) + list(sq_plan.no_match)
                )
                if sq_unmatched:
                    st.markdown("##### Unmatched rows (read-only audit)")
                    sq_unmatched_rows = []
                    for result in sq_unmatched:
                        sq_unmatched_rows.append({
                            "PDF row": result.row.row_index,
                            "PDF description": result.row.description,
                            "Best sim": round(
                                result.best_match_similarity, 3
                            ),
                            "Status": result.status.value,
                            "Notes": result.row.notes or "",
                        })
                    st.dataframe(
                        pd.DataFrame(sq_unmatched_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

                sq_preview_csv = _subquote_to_csv_preview(sq_result)
                st.download_button(
                    "Download extracted rows as CSV (for re-import)",
                    data=sq_preview_csv,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_subquote_rows.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    key="subquote_preview_csv_download",
                    help=(
                        "Save the parsed rows as a vendor-CSV-shaped file. "
                        "Round-trips through the T6.3 CSV uploader above "
                        "so the operator can hand-edit + re-import without "
                        "re-parsing the PDF."
                    ),
                )

                sq_plan_csv = export_match_plan_csv(
                    sq_plan, list(estimate.line_items)
                )
                st.download_button(
                    "Download match plan CSV",
                    data=sq_plan_csv,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_subquote_match_plan.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    key="subquote_plan_download",
                    help=(
                        "Audit-trail snapshot of the match plan — same "
                        "shape as the T6.3 batch export."
                    ),
                )

                sq_apply_clicked = st.button(
                    "Apply sub-quote overrides",
                    use_container_width=True,
                    type="primary",
                    key="subquote_apply_btn",
                    disabled=(
                        len(sq_plan.matched) == 0
                        and not st.session_state.get(
                            "subquote_resolved", {}
                        )
                    ),
                    help=(
                        "Applies every MATCHED row + every operator-"
                        "resolved AMBIGUOUS row via the same T6.3 "
                        "apply_batch_plan backend. LOW_SIMILARITY and "
                        "NO_MATCH rows are always skipped. Override "
                        "history rows are tagged [sub-quote] for "
                        "audit-trail provenance."
                    ),
                )

                if sq_apply_clicked:
                    sq_resolved_map: dict[int, int] = st.session_state.get(
                        "subquote_resolved", {}
                    )
                    pre_apply = estimate
                    # T6.4.c.1 — route through ``apply_subquote_plan`` so the
                    # canonical ``[sub-quote]`` / ``[sub-quote-llm]`` tag
                    # lands at position 0 of every overridden line's
                    # ``CostLine.notes`` (not just in the Streamlit
                    # session-state ``override_history``). The boolean
                    # ``llm`` flag picks the right tag for the active
                    # ingestion path (table parser vs vision LLM).
                    sq_is_llm = (
                        st.session_state.get("subquote_source") == "llm"
                    )
                    try:
                        new_estimate, sq_apply_summary = apply_subquote_plan(
                            estimate,
                            sq_plan,
                            llm=sq_is_llm,
                            auto_apply_matched=True,
                            resolved_ambiguous=sq_resolved_map,
                        )
                    except Exception as exc:
                        st.error(f"Sub-quote apply failed: {exc}")
                    else:
                        sq_applied_results: list[BatchMatchResult] = list(
                            sq_plan.matched
                        )
                        for result in sq_plan.ambiguous:
                            if result.row.row_index in sq_resolved_map:
                                sq_applied_results.append(BatchMatchResult(
                                    row=result.row,
                                    status=BatchMatchStatus.MATCHED,
                                    best_match_index=sq_resolved_map[
                                        result.row.row_index
                                    ],
                                    best_match_similarity=(
                                        result.best_match_similarity
                                    ),
                                    runner_up_index=result.runner_up_index,
                                    runner_up_similarity=(
                                        result.runner_up_similarity
                                    ),
                                    candidate_lines=result.candidate_lines,
                                ))

                        # T8.2 wires a second source tag — the
                        # operator-history audit trail distinguishes
                        # deterministic table-parse rows ([sub-quote])
                        # from vision-LLM rows ([sub-quote-llm]) so a
                        # post-mortem can attribute downstream pricing
                        # discrepancies to the right ingestion path.
                        # T6.4.c.1 — derive from the same ``sq_is_llm``
                        # flag we passed to ``apply_subquote_plan`` above
                        # so the session-state log and the canonical
                        # ``CostLine.notes`` tag stay in lockstep (single
                        # source of truth for the active path).
                        sq_source_tag = (
                            SOURCE_TAG_SUBQUOTE_LLM
                            if sq_is_llm
                            else SOURCE_TAG_SUBQUOTE_TABULAR
                        )

                        now_ts = datetime.utcnow().isoformat(timespec="seconds")
                        for result in sq_applied_results:
                            if result.best_match_index is None:
                                continue
                            if not 0 <= result.best_match_index < len(
                                pre_apply.line_items
                            ):
                                continue
                            old_line = pre_apply.line_items[
                                result.best_match_index
                            ]
                            new_line = new_estimate.line_items[
                                result.best_match_index
                            ]
                            note = format_batch_operator_note(
                                result.row,
                                source_tag=sq_source_tag,
                            )
                            override_history.append({
                                "timestamp": now_ts,
                                "line_index": result.best_match_index,
                                "description": old_line.description,
                                "csi_division": old_line.csi_division,
                                "csi_section": old_line.csi_section or "",
                                "original_unit_cost": round(
                                    float(old_line.unit_cost), 2
                                ),
                                "new_unit_cost": round(
                                    float(new_line.unit_cost), 2
                                ),
                                "operator_note": note,
                            })

                        st.session_state["override_history"] = override_history
                        st.session_state["estimate"] = new_estimate
                        st.session_state.pop("subquote_parse_result", None)
                        st.session_state.pop("subquote_plan", None)
                        st.session_state.pop("subquote_resolved", None)
                        st.session_state.pop("subquote_source", None)

                        sq_applied_count = sum(
                            1 for line in sq_apply_summary
                            if line.startswith("Row") and "APPLIED" in line
                        )
                        st.success(
                            f"Sub-quote override applied: "
                            f"{sq_applied_count} line"
                            f"{'s' if sq_applied_count != 1 else ''} "
                            f"updated. Subtotal: "
                            f"${pre_apply.subtotal:,.2f} "
                            f"\u2192 ${new_estimate.subtotal:,.2f}."
                        )
                        with st.expander(
                            "Apply summary (full log)", expanded=False
                        ):
                            for line in sq_apply_summary:
                                st.text(line)
                        st.rerun()

        st.divider()
        st.subheader("Project totals")
        c1, c2 = st.columns(2)
        c1.write(
            f"**Subtotal:** ${estimate.subtotal:,.2f}\n\n"
            f"**Contingency ({estimate.contingency_pct:.1f}%):** ${estimate.contingency:,.2f}\n\n"
            f"**Overhead ({estimate.overhead_pct:.1f}%):** ${estimate.overhead:,.2f}\n\n"
            f"**Profit ({estimate.profit_pct:.1f}%):** ${estimate.profit:,.2f}\n\n"
            f"### **GRAND TOTAL: ${estimate.grand_total:,.2f}**"
        )
        with c2:
            st.write("**Download**")
            xlsx_bytes = export_estimate_xlsx(estimate, project, csi_titles, extractions)
            st.download_button(
                "Download Excel (.xlsx)",
                data=xlsx_bytes,
                file_name=f"{estimate.project_name.replace(' ', '_')}_estimate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            json_str = export_estimate_json(estimate, project)
            st.download_button(
                "Download JSON",
                data=json_str,
                file_name=f"{estimate.project_name.replace(' ', '_')}_estimate.json",
                mime="application/json",
                use_container_width=True,
            )

    # --- By Division ---
    with tabs[6]:
        rows = []
        for div, total in sorted(estimate.by_division.items()):
            rows.append({
                "Div": div,
                "Title": csi_titles.get(div, ""),
                "Subtotal": total,
                "% of subtotal": (total / estimate.subtotal * 100) if estimate.subtotal else 0.0,
            })
        df_div = pd.DataFrame(rows)
        if df_div.empty:
            st.info("No priced lines.")
        else:
            st.dataframe(
                df_div,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Subtotal":     st.column_config.NumberColumn(format="$%.2f"),
                    "% of subtotal": st.column_config.ProgressColumn(
                        format="%.1f%%", min_value=0.0, max_value=100.0,
                    ),
                },
            )
            st.bar_chart(df_div.set_index("Div")["Subtotal"])

    # --- Sheets ---
    with tabs[7]:
        st.subheader("Sheet inventory")

        # F3 — drawing-prepass coverage tile. Only meaningful when there
        # are drawing sheets in the run; the bundle path is unaffected.
        sheet_extractions = [
            e for e in extractions
            if any(e.sheet_id == s.sheet_id for s in sheets)
        ]
        if sheet_extractions:
            skipped = sum(1 for e in sheet_extractions if e.lm_skipped)
            total = len(sheet_extractions)
            pct = (skipped / total * 100.0) if total else 0.0
            qt1, qt2, qt3 = st.columns(3)
            qt1.metric("Prepass-only (LLM skipped)", f"{skipped} / {total}", f"{pct:.0f}%")
            qt2.metric("LLM-augmented", str(total - skipped))
            qt3.caption(
                "\u26A1 = deterministic pre-pass cleared the confidence "
                "threshold; \U0001F916 = vision-LLM ran with pre-pass "
                "context. The pre-pass extracts title block, dimensions "
                "and schedule tables straight from the PDF's vector text."
            )

        for sheet in sheets:
            extraction = next(
                (e for e in extractions if e.sheet_id == sheet.sheet_id),
                None,
            )
            icon = "\u26A1" if (extraction and extraction.lm_skipped) else "\U0001F916"
            with st.expander(
                f"{icon} {sheet.sheet_id} - {sheet.title or '(no title)'} "
                f"[{sheet.discipline} / {sheet.sheet_type}]",
                expanded=False,
            ):
                cols = st.columns([2, 3])
                with cols[0]:
                    if sheet.image_path and Path(sheet.image_path).exists():
                        st.image(sheet.image_path, use_container_width=True)
                with cols[1]:
                    summary = extraction.summary if extraction else ""
                    st.write(f"**Source PDF:** {sheet.pdf_name} (page {sheet.page_index + 1})")
                    st.write(f"**Discipline:** {sheet.discipline}")
                    st.write(f"**Sheet type:** {sheet.sheet_type}")
                    st.write(f"**Scale:** {sheet.scale or 'unknown'}")
                    if extraction:
                        if extraction.lm_skipped:
                            st.success(
                                "\u26A1 LLM skipped — deterministic "
                                "pre-pass extracted this sheet."
                            )
                        elif extraction.prepass is not None:
                            st.caption(
                                "\U0001F916 LLM ran with pre-pass context "
                                f"(confidence {extraction.prepass.confidence:.2f})."
                            )
                    st.write("**Summary:**")
                    st.write(summary or "(no summary)")
                    if extraction and extraction.prepass is not None:
                        with st.popover("Prepass details"):
                            tb = extraction.prepass.title_block
                            st.write(f"**Title block:** {tb.model_dump()}")
                            st.write(f"**Confidence:** {extraction.prepass.confidence:.2f}")
                            st.write(f"**Dimensions:** {len(extraction.prepass.dimensions)}")
                            st.write(f"**Schedules:** {len(extraction.prepass.schedules)}")
                            if extraction.prepass.quality_issues:
                                st.warning("\n".join(
                                    f"- {q}" for q in extraction.prepass.quality_issues
                                ))

    # --- Rooms ---
    with tabs[8]:
        if not project.rooms:
            st.info("No rooms identified.")
        else:
            st.dataframe(
                pd.DataFrame([r.model_dump() for r in project.rooms]),
                hide_index=True,
                use_container_width=True,
            )

    # --- Doors / Windows ---
    with tabs[9]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Doors ({len(project.doors)})")
            if project.doors:
                st.dataframe(
                    pd.DataFrame([d.model_dump() for d in project.doors]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No doors identified.")
        with c2:
            st.subheader(f"Windows ({len(project.windows)})")
            if project.windows:
                st.dataframe(
                    pd.DataFrame([w.model_dump() for w in project.windows]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No windows identified.")

    # --- Structural / MEP ---
    with tabs[10]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Structural ({len(project.structural)})")
            if project.structural:
                st.dataframe(
                    pd.DataFrame([s.model_dump() for s in project.structural]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No structural items identified.")
        with c2:
            st.subheader(f"MEP ({len(project.mep)})")
            if project.mep:
                st.dataframe(
                    pd.DataFrame([m.model_dump() for m in project.mep]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No MEP items identified.")

    # --- Specs ---
    with tabs[11]:
        if not project.spec_sections:
            st.info("No specification sections identified.")
        else:
            for spec in sorted(project.spec_sections, key=lambda s: s.csi_section):
                with st.expander(f"{spec.csi_section} - {spec.title}", expanded=False):
                    if spec.summary:
                        st.write(spec.summary)
                    if spec.requirements:
                        st.write("**Requirements:**")
                        for req in spec.requirements:
                            st.write(f"- {req}")
                    if spec.source_sheet_id:
                        st.caption(f"Source: {spec.source_sheet_id}")

    # --- Raw takeoffs ---
    with tabs[12]:
        if not project.takeoffs:
            st.info("No raw takeoffs.")
        else:
            df_t = pd.DataFrame([t.model_dump() for t in project.takeoffs])
            df_t["source_sheet_ids"] = df_t["source_sheet_ids"].apply(lambda xs: ", ".join(xs))
            st.dataframe(df_t, hide_index=True, use_container_width=True)

    # --- Warnings ---
    with tabs[13]:
        if not project.warnings:
            st.success("No warnings.")
        else:
            for w in project.warnings:
                st.warning(w)

    # --- Client Quote (F12 + F15) ---
    with tabs[14]:
        _render_client_quote_tab(estimate, project, csi_titles)

    # --- Bid Alternates (T9.1) -------------------------------------------
    # Pure-UI surface on top of the T9.0 backend. Lets an operator
    # review every priced ``AlternateLineEstimate`` on ``estimate``,
    # toggle each in/out of the bid via a per-row checkbox, hand-enter
    # ``cost_delta`` for MISSING-basis lines (which flips the basis
    # to OPERATOR_ENTERED), and watch the live "base vs with-selected"
    # tally re-render on every toggle. The tab is self-contained:
    # session state lives under the ``alternates_*`` namespace and
    # never collides with the T6.* / T8.* keys.
    with tabs[15]:
        # Lazy seed of the session-state keys; idempotent under repeat
        # renders so a checkbox toggle (which re-runs the script) is
        # cheap.
        _initialize_alternates_session_state(estimate)

        priced_alts: list[AlternateLineEstimate] = list(
            getattr(estimate, "alternates", None) or []
        )

        # In-session operator override of the priced alternates list:
        # any operator-entered cost_delta replaces the corresponding
        # priced row before we render the tally / rows. Stored as a
        # delta-only map so the original priced list (which is the
        # single source of truth on disk / Excel / JSON) is never
        # mutated by the UI.
        operator_deltas: dict[str, float] = (
            st.session_state.get(_ALTERNATES_SS_DELTAS) or {}
        )
        live_alts: list[AlternateLineEstimate] = list(priced_alts)
        for alt_id, delta_val in operator_deltas.items():
            try:
                live_alts, _w = _apply_alternate_operator_entry(
                    alt_id, float(delta_val), live_alts
                )
            except ValueError:
                # Stale entry referencing an alternate that no longer
                # exists (e.g. after a re-analyze). Drop it silently —
                # the next session-state init will reset.
                continue

        # ---- Header banner (counts + by-type aggregates) -------------
        bid_pkg_count = len(getattr(project, "bid_packages", None) or [])
        st.subheader("Bid Alternates")
        st.caption(
            "Operator-driven alternate selection. Toggle rows to roll "
            "alternates in/out of the base; the live tally on the "
            "right shows the base vs with-selected total. Excel / "
            "JSON exports remain pinned to the *base* bid; this tab "
            "is the operator's working scenario."
        )

        if not priced_alts:
            st.info(
                "No alternates extracted yet. Alternates appear "
                "automatically when bid forms contain Alternate / Bid "
                "Alternate / VE sections."
            )
        else:
            summary = _compute_alternates_summary(live_alts)
            banner_bits = [
                f"**{summary['all']['count']}** alternates extracted "
                f"from **{bid_pkg_count}** bid packages"
            ]
            sub_bits: list[str] = []
            add_total = summary[AlternateType.ADDITIVE.value]["total_delta"]
            ded_total = summary[AlternateType.DEDUCTIVE.value]["total_delta"]
            sub_total = summary[AlternateType.SUBSTITUTION.value]["total_delta"]
            ve_count = summary[AlternateType.VE.value]["count"]
            if summary[AlternateType.ADDITIVE.value]["count"]:
                sub_bits.append(
                    f"{summary[AlternateType.ADDITIVE.value]['count']} additive "
                    f"(potential {_format_cost_delta(add_total)})"
                )
            if summary[AlternateType.DEDUCTIVE.value]["count"]:
                sub_bits.append(
                    f"{summary[AlternateType.DEDUCTIVE.value]['count']} deductive "
                    f"(potential {_format_cost_delta(ded_total)})"
                )
            if summary[AlternateType.SUBSTITUTION.value]["count"]:
                sub_bits.append(
                    f"{summary[AlternateType.SUBSTITUTION.value]['count']} substitution "
                    f"(net {_format_cost_delta(sub_total)})"
                )
            if ve_count:
                sub_bits.append(f"{ve_count} VE")
            st.info(banner_bits[0])
            if sub_bits:
                st.caption(" | ".join(sub_bits))
            if summary["all"]["missing_count"]:
                st.warning(
                    f"{summary['all']['missing_count']} alternate(s) "
                    "have no resolvable cost_delta — enter a value "
                    "below to flip them to OPERATOR_ENTERED basis."
                )

            # ---- Bulk-action buttons ---------------------------------
            ba1, ba2, ba3, ba4 = st.columns(4)
            with ba1:
                if st.button("Select all additive", key="alt_select_all_additive"):
                    sel = set(st.session_state.get(_ALTERNATES_SS_SELECTED, set()))
                    sel.update(
                        a.alternate_id for a in live_alts
                        if a.alternate_type == AlternateType.ADDITIVE
                    )
                    st.session_state[_ALTERNATES_SS_SELECTED] = sel
                    st.rerun()
            with ba2:
                if st.button("Select all deductive", key="alt_select_all_deductive"):
                    sel = set(st.session_state.get(_ALTERNATES_SS_SELECTED, set()))
                    sel.update(
                        a.alternate_id for a in live_alts
                        if a.alternate_type
                        in (AlternateType.DEDUCTIVE, AlternateType.VE)
                    )
                    st.session_state[_ALTERNATES_SS_SELECTED] = sel
                    st.rerun()
            with ba3:
                if st.button("Reset to default", key="alt_reset_default"):
                    st.session_state[_ALTERNATES_SS_SELECTED] = set(
                        getattr(estimate, "alternates_selected_default", None) or set()
                    )
                    st.rerun()
            with ba4:
                if st.button("Clear all", key="alt_clear_all"):
                    st.session_state[_ALTERNATES_SS_SELECTED] = set()
                    st.rerun()

            # ---- Two-column layout: rows on the left, tally on the right
            row_col, tally_col = st.columns([3, 1])

            current_selected: set[str] = set(
                st.session_state.get(_ALTERNATES_SS_SELECTED, set())
            )
            notes_map: dict[str, str] = (
                st.session_state.get(_ALTERNATES_SS_NOTES) or {}
            )

            with row_col:
                st.markdown("#### Alternates")
                for a in live_alts:
                    with st.container(border=True):
                        head_cols = st.columns([0.7, 0.6, 1.6, 0.9])
                        with head_cols[0]:
                            checked = st.checkbox(
                                "Include",
                                value=a.alternate_id in current_selected,
                                key=f"alt_sel_{a.alternate_id}",
                                help="Roll this alternate into the with-selected total.",
                            )
                            if checked:
                                current_selected.add(a.alternate_id)
                            else:
                                current_selected.discard(a.alternate_id)
                        with head_cols[1]:
                            st.markdown(f"**{a.alternate_id}**")
                            st.markdown(_format_alternate_type_badge(a.alternate_type))
                        with head_cols[2]:
                            desc = a.description or "(no description)"
                            if len(desc) > 120:
                                st.write(desc[:117] + "…")
                                with st.expander("Full description"):
                                    st.write(desc)
                            else:
                                st.write(desc)
                        with head_cols[3]:
                            st.markdown(
                                f"**{_format_cost_delta(a.cost_delta, a.alternate_type)}**"
                            )
                            basis_label = _alternate_basis_label(a.pricing_basis)
                            st.caption(
                                basis_label,
                                help=_ALTERNATE_BASIS_TOOLTIPS.get(
                                    a.pricing_basis
                                    if isinstance(a.pricing_basis, AlternatePricingBasis)
                                    else AlternatePricingBasis.MISSING,
                                    "",
                                ),
                            )
                            st.caption(f"Confidence: {a.confidence:.0%}")

                        meta_cols = st.columns([1.2, 1.2, 1.6])
                        with meta_cols[0]:
                            st.caption(
                                "Bid package: "
                                + _resolve_bid_package_title(a.bid_package_id, project)
                            )
                        with meta_cols[1]:
                            st.caption(f"Source: {a.source_sheet or '—'}")
                        with meta_cols[2]:
                            note_default = notes_map.get(
                                a.alternate_id, a.operator_notes or ""
                            )
                            new_note = st.text_input(
                                "Operator notes",
                                value=note_default,
                                key=f"alt_note_{a.alternate_id}",
                                placeholder="(in-session notes; not persisted to disk)",
                            )
                            if new_note != note_default:
                                notes_map[a.alternate_id] = new_note

                        # Operator entry for MISSING-basis lines.
                        if (
                            isinstance(a.pricing_basis, AlternatePricingBasis)
                            and a.pricing_basis == AlternatePricingBasis.MISSING
                        ) or a.cost_delta is None:
                            st.markdown(
                                ":orange[**Missing cost — enter operator value:**]"
                            )
                            entry_cols = st.columns([1, 1, 2])
                            with entry_cols[0]:
                                entered = st.number_input(
                                    "Cost delta ($)",
                                    value=float(operator_deltas.get(a.alternate_id, 0.0)),
                                    step=100.0,
                                    format="%.2f",
                                    key=f"alt_delta_{a.alternate_id}",
                                )
                            with entry_cols[1]:
                                if st.button(
                                    "Apply",
                                    key=f"alt_apply_{a.alternate_id}",
                                ):
                                    try:
                                        _new_alts, warn = _apply_alternate_operator_entry(
                                            a.alternate_id,
                                            float(entered),
                                            live_alts,
                                        )
                                        deltas = dict(
                                            st.session_state.get(
                                                _ALTERNATES_SS_DELTAS, {}
                                            )
                                            or {}
                                        )
                                        deltas[a.alternate_id] = float(entered)
                                        st.session_state[_ALTERNATES_SS_DELTAS] = deltas
                                        if warn:
                                            st.warning(warn)
                                        else:
                                            st.success(
                                                f"Applied {_format_cost_delta(float(entered))} "
                                                f"to {a.alternate_id}."
                                            )
                                        st.rerun()
                                    except ValueError as exc:
                                        st.error(str(exc))

                # Persist the (possibly-edited) selection + notes maps.
                st.session_state[_ALTERNATES_SS_SELECTED] = current_selected
                st.session_state[_ALTERNATES_SS_NOTES] = notes_map

            # ---- Live tally panel ---------------------------------------
            with tally_col:
                st.markdown("#### Tally")
                # Compute the with-selected total against the *live*
                # alternates list (i.e. operator-entered deltas already
                # applied via the live_alts overlay above). We do this
                # by building a temporary Estimate ``model_copy`` with
                # ``alternates=live_alts`` so the existing
                # ``subtotal_with_alternates_selected`` / ``total_with_alternates_selected``
                # methods work unchanged.
                live_estimate = estimate.model_copy(
                    update={"alternates": live_alts}
                )
                base_subtotal = live_estimate.subtotal_base_only
                selected_delta = live_estimate.alternates_delta_for_selection(
                    current_selected
                )
                with_subtotal = live_estimate.subtotal_with_alternates_selected(
                    current_selected
                )
                with_total = live_estimate.total_with_alternates_selected(
                    current_selected
                )

                st.metric("Base bid", f"${base_subtotal:,.0f}")
                st.metric(
                    "Selected delta",
                    _format_cost_delta(selected_delta),
                    help=(
                        f"Sum of cost_delta over the {len(current_selected)} "
                        "selected alternate(s)."
                    ),
                )
                st.metric(
                    "Subtotal w/ selected",
                    f"${with_subtotal:,.0f}",
                )
                st.metric(
                    "Grand total w/ selected",
                    f"${with_total:,.0f}",
                    help=(
                        "Includes contingency / overhead / profit "
                        "applied against the selection-aware subtotal."
                    ),
                )
                st.caption(f"Selected: {len(current_selected)} of {len(live_alts)}")

            # ---- CSV download (full, regardless of selection) ---------
            csv_string = _alternates_to_csv(
                live_alts,
                selected_ids=current_selected,
                operator_notes_map=notes_map,
            )
            st.download_button(
                "Download alternates summary CSV",
                csv_string,
                file_name="bid_alternates_summary.csv",
                mime="text/csv",
                key="alt_csv_download",
                help=(
                    "Includes every priced alternate with the current "
                    "selection state and any in-session operator notes."
                ),
            )

else:
    st.info(
        "Upload one or more plan-set PDFs in the sidebar and click "
        "**Analyze plan set** to begin."
    )
    with st.expander("How it works", expanded=True):
        st.markdown(
            """
            1. **Split + render.** Each PDF page becomes one sheet, rendered at the
               configured DPI for the vision model.
            2. **Classify.** A title-block heuristic (sheet number / keyword in
               embedded text) handles the easy cases; the vision LLM picks up the
               rest.
            3. **Extract.** Each sheet is routed to a discipline-specific
               extractor (architectural, structural, MEP, schedule, spec, site).
               Returns strict JSON matching our schema.
            4. **Reconcile.** Rooms, doors, windows, fixtures and specs are
               de-duplicated across sheets - the floor plan and the schedule
               agree on one row per item.
            5. **Price.** Each takeoff is matched against
               `config/cost_database.json` (exact CSI section first, then
               keyword fallback within the same division).
            6. **Review and edit.** Every line is editable in the table.
               Recalculate totals and download Excel / JSON when you're happy.
            """
        )
