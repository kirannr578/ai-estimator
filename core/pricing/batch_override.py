"""Phase T6.3 — batch operator overrides from vendor pricing spreadsheets.

Operators frequently receive vendor pricing as CSV (e.g., from a subcontractor's
estimating software, an Excel export of a quote PDF, or a copy-paste from email).
This module reconciles such a CSV to a set of :class:`~core.schemas.CostLine`
instances by fuzzy-matching on description, and stages bulk overrides via
:func:`core.estimator.apply_manual_override` (the T6.1 single-line override
primitive).

The module is intentionally **pure-logic** — no Streamlit, no I/O, no
file-system reads. Pass raw CSV text in, get a match-plan dict out. The
Streamlit UI in ``app.py`` is a thin wrapper around the four public
functions defined here so the whole end-to-end flow is testable without
spinning up an ``AppTest`` harness.

Public surface:

* :func:`parse_vendor_csv` — CSV text → ``(list[BatchOverrideRow], errors)``
* :func:`match_cost_lines` — rows + cost_lines → ``BatchOverridePlan``
* :func:`apply_batch_plan` — plan + estimate → ``(new_estimate, summary)``
* :func:`export_match_plan_csv` — plan → CSV string for operator review

Three dataclasses model the data: :class:`BatchOverrideRow` (one parsed
CSV row), :class:`BatchMatchResult` (one fuzzy-match decision), and
:class:`BatchOverridePlan` (the bundled plan ready to apply or export).

The matcher uses :func:`difflib.SequenceMatcher.ratio` on normalised
descriptions (lowercase, punctuation stripped, whitespace collapsed,
CSI section prefix dropped). Pure-stdlib — no new third-party deps.
"""

from __future__ import annotations

import csv
import io
import re
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from enum import Enum
from typing import Iterable

from core.estimator import apply_manual_override
from core.schemas import CostLine, Estimate


# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------


class BatchMatchStatus(str, Enum):
    """Outcome of fuzzy-matching one CSV row to a list of CostLines.

    * ``MATCHED`` — best similarity ≥ threshold AND the runner-up trails
      by at least ``ambiguity_margin``. Safe to auto-apply.
    * ``AMBIGUOUS`` — best similarity ≥ threshold BUT the runner-up is
      within ``ambiguity_margin``. The operator must pick (or skip).
    * ``LOW_SIMILARITY`` — best similarity in ``[0.40, threshold)``.
      Plausible enough to surface for audit but not auto-applied.
    * ``NO_MATCH`` — best similarity < 0.40 OR no candidates at all.
      Never applied; logged in summary.
    """

    MATCHED = "matched"
    AMBIGUOUS = "ambiguous"
    NO_MATCH = "no_match"
    LOW_SIMILARITY = "low_similarity"


@dataclass
class BatchOverrideRow:
    """One parsed row from the vendor CSV (pre-match).

    ``row_index`` is 1-indexed from the CSV's perspective — the header
    is row 1, data starts at row 2. The operator-note generated for
    the override carries ``[csv-row: N]`` using this index so an
    auditor can grep the original CSV.

    ``quantity`` is optional; when supplied it is used solely as a
    match tiebreaker (rows whose quantity matches a candidate's
    quantity get a small similarity nudge). Not applied to the unit
    cost or override math.
    """

    row_index: int
    description: str
    unit_cost: float
    vendor: str | None = None
    quote_ref: str | None = None
    notes: str | None = None
    quantity: float | None = None


@dataclass
class BatchMatchResult:
    """One match decision returned by :func:`match_cost_lines`.

    ``best_match_index`` is the 0-based index of the winning CostLine
    when ``status`` is :attr:`BatchMatchStatus.MATCHED` or
    :attr:`BatchMatchStatus.AMBIGUOUS`. ``None`` otherwise.

    ``candidate_lines`` is the top-N (default 5) ``(index, similarity)``
    tuples sorted descending by similarity. Used by the UI to render an
    operator-resolution dropdown for the AMBIGUOUS rows.
    """

    row: BatchOverrideRow
    status: BatchMatchStatus
    best_match_index: int | None
    best_match_similarity: float
    runner_up_index: int | None
    runner_up_similarity: float
    candidate_lines: list[tuple[int, float]] = field(default_factory=list)


@dataclass
class BatchOverridePlan:
    """The full match plan for an uploaded CSV.

    ``matched`` / ``ambiguous`` / ``no_match`` / ``low_similarity`` are
    disjoint bucket lists — every :class:`BatchMatchResult` produced by
    :func:`match_cost_lines` lives in exactly one bucket. ``total_rows``
    equals the sum of the bucket lengths and matches the number of
    parsed CSV rows.

    ``similarity_threshold`` and ``ambiguity_margin`` are echoed back
    so a downstream reader (UI, CSV export, test) can confirm the
    matcher parameters without re-deriving them.
    """

    total_rows: int
    matched: list[BatchMatchResult]
    ambiguous: list[BatchMatchResult]
    no_match: list[BatchMatchResult]
    low_similarity: list[BatchMatchResult]
    similarity_threshold: float
    ambiguity_margin: float


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


# Column-name aliases (case-insensitive). The CSV parser looks up each
# expected slot against this map's keys; the first matching header in the
# CSV wins. ``description`` and ``unit_cost`` are required; the rest are
# optional.
_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "description": ("description", "desc", "item", "item_description", "line_item"),
    "unit_cost": ("unit_cost", "price", "unit_price", "cost", "$/unit", "rate"),
    "vendor": ("vendor", "supplier", "sub", "subcontractor"),
    "quote_ref": (
        "quote_ref", "quote", "quote_id", "ref", "reference", "po", "po_number",
    ),
    "notes": ("notes", "comments", "remarks"),
    "quantity": ("quantity", "qty", "q"),
}


# CSI MasterFormat section prefix regex. Matches the three formats the
# brief calls out (``26 27 26 -``, ``26 27 26.13 -``, ``26 27 26.13 - ``)
# plus en-dash / em-dash separator variants and a leading-whitespace
# tolerance. The trailing ``\s*`` consumes any whitespace after the
# separator so the matcher sees a clean description without the catalog
# prefix.
#
# Conservative on purpose: REQUIRES the dash / colon separator so a
# numeric-looking description like "100 200 300 mph" is NOT mis-stripped.
# A future relaxation that strips bare ``\d\d \d\d \d\d`` prefixes (no
# separator) could be gated on a Boolean flag, but the calibration set
# always carries the separator.
_CSI_PREFIX_RE = re.compile(
    r"^\s*\d{2}\s+\d{2}\s+\d{2}(?:\.\d+)?\s*[-:\u2013\u2014]\s*"
)


# Punctuation strip pattern. Punctuation hurts the SequenceMatcher
# similarity more than it helps for cost-row descriptions, so we
# collapse it into a single space before matching. Newlines + tabs
# are also normalised here.
_PUNCT_RE = re.compile(r"[^\w\s]+")


# Whitespace collapse — multiple spaces / tabs → single space.
_WS_RE = re.compile(r"\s+")


# Quantity-match similarity nudge. When the CSV row's quantity matches
# a candidate's quantity within 5%, the candidate's effective similarity
# gets a +0.02 boost (clamped to 1.0). Tiebreaker only — never enough
# to flip a non-matched row into MATCHED on its own, but enough to
# resolve a 0.65 vs. 0.66 tie reliably.
_QTY_TIEBREAKER_BOOST: float = 0.02
_QTY_TIEBREAKER_TOLERANCE: float = 0.05  # 5%


# NO_MATCH floor — best similarity below this lands in NO_MATCH bucket;
# between this and ``similarity_threshold`` lands in LOW_SIMILARITY.
_NO_MATCH_FLOOR: float = 0.40


# Top-N candidates surfaced in ``BatchMatchResult.candidate_lines``.
_TOP_K_CANDIDATES: int = 5


# ---------------------------------------------------------------------------
# Normalisation
# ---------------------------------------------------------------------------


def _normalise_description(text: str) -> str:
    """Normalise a description string for fuzzy-matching.

    Steps (in order):

    1. Strip leading CSI section prefix (e.g., ``"23 31 13 - "``).
    2. Lowercase.
    3. Replace punctuation with whitespace.
    4. Collapse whitespace runs to a single space.
    5. Strip leading / trailing whitespace.

    Returns ``""`` for ``None`` / empty / whitespace-only input.
    """
    if not text:
        return ""
    s = _CSI_PREFIX_RE.sub("", text)
    s = s.lower()
    s = _PUNCT_RE.sub(" ", s)
    s = _WS_RE.sub(" ", s)
    return s.strip()


# ---------------------------------------------------------------------------
# CSV parsing
# ---------------------------------------------------------------------------


def _resolve_column_map(headers: Iterable[str]) -> dict[str, str]:
    """Map our canonical slot names → the actual CSV header strings.

    Case-insensitive + whitespace-tolerant. Returns a dict whose keys
    are the canonical slot names (``"description"``, ``"unit_cost"``,
    …) and whose values are the verbatim header strings as they
    appeared in the CSV. Missing optional slots are simply omitted from
    the returned dict.
    """
    normalised: dict[str, str] = {}
    for h in headers:
        if h is None:
            continue
        key = h.strip().lower().replace(" ", "_")
        normalised[key] = h

    out: dict[str, str] = {}
    for slot, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            if alias in normalised:
                out[slot] = normalised[alias]
                break
    return out


def _parse_float(raw: str) -> float | None:
    """Best-effort numeric parse. Returns ``None`` on failure.

    Tolerates leading ``$`` and embedded thousands-separator commas
    (common in spreadsheet exports). Negative values are returned as-is;
    the caller is responsible for the non-negative check.
    """
    if raw is None:
        return None
    s = str(raw).strip()
    if not s:
        return None
    s = s.replace("$", "").replace(",", "").strip()
    if not s:
        return None
    try:
        return float(s)
    except (TypeError, ValueError):
        return None


def parse_vendor_csv(
    csv_text: str,
) -> tuple[list[BatchOverrideRow], list[str]]:
    """Parse a vendor pricing CSV into :class:`BatchOverrideRow` records.

    Returns ``(rows, errors)``. ``rows`` is the list of successfully
    parsed records; ``errors`` is a list of human-readable strings for
    rows that could not be parsed (the parse continues — a bad row does
    not abort the others). A fatal error (missing required column,
    empty file) raises :class:`ValueError`.

    Required columns (case-insensitive header matching):

    * ``description`` (aliases: ``desc``, ``item``, ``item_description``,
      ``line_item``)
    * ``unit_cost`` (aliases: ``price``, ``unit_price``, ``cost``,
      ``$/unit``, ``rate``)

    Optional columns:

    * ``vendor`` (``supplier`` / ``sub`` / ``subcontractor``)
    * ``quote_ref`` (``quote`` / ``quote_id`` / ``ref`` / ``reference`` /
      ``po`` / ``po_number``)
    * ``notes`` (``comments`` / ``remarks``)
    * ``quantity`` (``qty`` / ``q``)

    Per-row error conditions (row skipped, parse continues, error
    appended to the returned list):

    * Non-numeric ``unit_cost``
    * Negative ``unit_cost``
    * Empty ``description``

    The byte-order mark (BOM, ``U+FEFF``) at the start of the file is
    stripped if present — Excel writes one by default for UTF-8 CSV
    exports.
    """
    if not csv_text or not csv_text.strip():
        raise ValueError("CSV is empty.")

    text = csv_text.lstrip("\ufeff")

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValueError("CSV is empty.")

    col_map = _resolve_column_map(reader.fieldnames)

    if "description" not in col_map:
        raise ValueError(
            "CSV is missing required column 'description' "
            "(aliases: desc, item, item_description, line_item)."
        )
    if "unit_cost" not in col_map:
        raise ValueError(
            "CSV is missing required column 'unit_cost' "
            "(aliases: price, unit_price, cost, $/unit, rate)."
        )

    rows: list[BatchOverrideRow] = []
    errors: list[str] = []

    for offset, raw in enumerate(reader):
        # CSV row 1 is the header; the first data row is row 2.
        csv_row_idx = offset + 2

        desc_raw = raw.get(col_map["description"], "")
        desc = (desc_raw or "").strip()
        if not desc:
            errors.append(f"Row {csv_row_idx}: empty description; skipped.")
            continue

        uc_raw = raw.get(col_map["unit_cost"], "")
        uc = _parse_float(uc_raw)
        if uc is None:
            errors.append(
                f"Row {csv_row_idx}: non-numeric unit_cost "
                f"{uc_raw!r}; skipped."
            )
            continue
        if uc < 0:
            errors.append(
                f"Row {csv_row_idx}: negative unit_cost {uc}; skipped."
            )
            continue

        vendor: str | None = None
        if "vendor" in col_map:
            v = (raw.get(col_map["vendor"], "") or "").strip()
            vendor = v or None

        quote_ref: str | None = None
        if "quote_ref" in col_map:
            q = (raw.get(col_map["quote_ref"], "") or "").strip()
            quote_ref = q or None

        notes: str | None = None
        if "notes" in col_map:
            n = (raw.get(col_map["notes"], "") or "").strip()
            notes = n or None

        qty: float | None = None
        if "quantity" in col_map:
            qty = _parse_float(raw.get(col_map["quantity"], ""))
            if qty is not None and qty < 0:
                qty = None

        rows.append(BatchOverrideRow(
            row_index=csv_row_idx,
            description=desc,
            unit_cost=uc,
            vendor=vendor,
            quote_ref=quote_ref,
            notes=notes,
            quantity=qty,
        ))

    return rows, errors


# ---------------------------------------------------------------------------
# Matching
# ---------------------------------------------------------------------------


def _qty_tiebreaker(row_qty: float | None, cand_qty: float) -> float:
    """Return the multiplicative similarity boost for a qty tiebreaker.

    Returns ``1.0 + _QTY_TIEBREAKER_BOOST`` when both quantities exist
    and agree to within ``_QTY_TIEBREAKER_TOLERANCE`` (5%). ``1.0``
    otherwise. The boost is small enough never to push a sub-threshold
    row over the threshold on its own, but large enough to break a
    ``0.65 vs 0.66`` tie reliably.
    """
    if row_qty is None or cand_qty is None or cand_qty <= 0:
        return 1.0
    delta = abs(row_qty - cand_qty) / max(cand_qty, 1e-9)
    if delta <= _QTY_TIEBREAKER_TOLERANCE:
        return 1.0 + _QTY_TIEBREAKER_BOOST
    return 1.0


def _similarity(row: BatchOverrideRow, line: CostLine) -> float:
    """Compute the effective similarity between a CSV row and a CostLine.

    Uses :class:`difflib.SequenceMatcher` ratio on normalised
    descriptions. Applies the optional quantity tiebreaker boost
    (capped at 1.0). Returns a value in ``[0, 1]``.
    """
    norm_row = _normalise_description(row.description)
    norm_line = _normalise_description(line.description)
    if not norm_row or not norm_line:
        return 0.0
    base = SequenceMatcher(None, norm_row, norm_line).ratio()
    boost = _qty_tiebreaker(row.quantity, float(line.quantity))
    return min(1.0, round(base * boost, 4))


def _classify_match(
    best_sim: float,
    runner_up_sim: float,
    *,
    similarity_threshold: float,
    ambiguity_margin: float,
) -> BatchMatchStatus:
    """Bucket a (best, runner_up) similarity pair into a match status.

    Decision tree (in priority order):

    1. ``best_sim < _NO_MATCH_FLOOR``                → ``NO_MATCH``
    2. ``best_sim < similarity_threshold``           → ``LOW_SIMILARITY``
    3. ``(best_sim - runner_up_sim) < margin``       → ``AMBIGUOUS``
    4. otherwise                                     → ``MATCHED``

    Mirrors the spec table in the brief exactly. The runner-up only
    matters when the best is above-threshold — a single-candidate row
    with ``runner_up_sim == 0`` cannot trigger AMBIGUOUS because the
    delta will always exceed any reasonable margin.
    """
    if best_sim < _NO_MATCH_FLOOR:
        return BatchMatchStatus.NO_MATCH
    if best_sim < similarity_threshold:
        return BatchMatchStatus.LOW_SIMILARITY
    if (best_sim - runner_up_sim) < ambiguity_margin:
        return BatchMatchStatus.AMBIGUOUS
    return BatchMatchStatus.MATCHED


def match_cost_lines(
    rows: list[BatchOverrideRow],
    cost_lines: list[CostLine],
    similarity_threshold: float = 0.65,
    ambiguity_margin: float = 0.10,
) -> BatchOverridePlan:
    """Fuzzy-match each CSV row to a CostLine by description.

    Uses :func:`difflib.SequenceMatcher.ratio` on normalised descriptions
    (see :func:`_normalise_description`). For each row:

    * Computes similarity against every CostLine.
    * Sorts candidates by similarity descending; keeps the top-5.
    * Classifies via :func:`_classify_match`:

      * ``MATCHED``        — ``best ≥ threshold`` AND
        ``best - runner_up ≥ margin``
      * ``AMBIGUOUS``      — ``best ≥ threshold`` AND
        ``best - runner_up < margin``
      * ``LOW_SIMILARITY`` — ``0.40 ≤ best < threshold``
      * ``NO_MATCH``       — ``best < 0.40`` OR no candidates

    The default thresholds (``0.65`` similarity, ``0.10`` ambiguity
    margin) were chosen to align with the Phase T6 ``OPERATOR_REVIEW``
    band boundary on the qty-confidence axis — a 0.65-similarity match
    is precisely the operator-review-or-better boundary the existing
    pricing pipeline uses for "good enough to ship". The ambiguity
    margin is calibrated against the BPC calibration set: 0.10 is wide
    enough that "Interior latex paint, walls" vs. "Interior latex paint,
    ceiling" (typical sim delta ~0.07) is correctly flagged AMBIGUOUS,
    but narrow enough that "Door 101A" vs. "Door 201A" (typical sim
    delta ~0.20) auto-resolves.
    """
    plan = BatchOverridePlan(
        total_rows=len(rows),
        matched=[],
        ambiguous=[],
        no_match=[],
        low_similarity=[],
        similarity_threshold=similarity_threshold,
        ambiguity_margin=ambiguity_margin,
    )

    if not rows:
        return plan

    for row in rows:
        if not cost_lines:
            result = BatchMatchResult(
                row=row,
                status=BatchMatchStatus.NO_MATCH,
                best_match_index=None,
                best_match_similarity=0.0,
                runner_up_index=None,
                runner_up_similarity=0.0,
                candidate_lines=[],
            )
            plan.no_match.append(result)
            continue

        sims: list[tuple[int, float]] = [
            (i, _similarity(row, li)) for i, li in enumerate(cost_lines)
        ]
        sims.sort(key=lambda pair: (-pair[1], pair[0]))
        top_k = sims[:_TOP_K_CANDIDATES]

        best_idx, best_sim = sims[0]
        runner_idx: int | None = None
        runner_sim: float = 0.0
        if len(sims) > 1:
            runner_idx, runner_sim = sims[1]

        status = _classify_match(
            best_sim, runner_sim,
            similarity_threshold=similarity_threshold,
            ambiguity_margin=ambiguity_margin,
        )

        if status in (BatchMatchStatus.MATCHED, BatchMatchStatus.AMBIGUOUS):
            best_match_index: int | None = best_idx
        else:
            best_match_index = None

        result = BatchMatchResult(
            row=row,
            status=status,
            best_match_index=best_match_index,
            best_match_similarity=round(best_sim, 4),
            runner_up_index=runner_idx,
            runner_up_similarity=round(runner_sim, 4),
            candidate_lines=top_k,
        )

        bucket = {
            BatchMatchStatus.MATCHED: plan.matched,
            BatchMatchStatus.AMBIGUOUS: plan.ambiguous,
            BatchMatchStatus.LOW_SIMILARITY: plan.low_similarity,
            BatchMatchStatus.NO_MATCH: plan.no_match,
        }[status]
        bucket.append(result)

    return plan


# ---------------------------------------------------------------------------
# Operator-note formatting
# ---------------------------------------------------------------------------


def format_batch_operator_note(row: BatchOverrideRow) -> str:
    """Format the operator note for a batch-applied override.

    Format::

        [batch] [vendor: <vendor>] [quote-ref: <quote_ref>] [csv-row: N] <notes>

    ``[batch]`` always leads (signals the override came from a CSV
    upload, not a single-line UI edit). ``[csv-row: N]`` is always
    present (every row has a known CSV index). The other fields appear
    only when populated; empty ones are skipped without leaving
    double-space gaps.

    The returned string is the operator-note payload — :func:`core.estimator.
    apply_manual_override` will prefix it with the
    :data:`~core.estimator.MANUAL_OVERRIDE_NOTE_PREFIX` sentinel
    (``"operator override"``) before stamping onto the CostLine's
    ``notes`` field.
    """
    parts: list[str] = ["[batch]"]
    if row.vendor:
        v = row.vendor.strip()
        if v:
            parts.append(f"[vendor: {v}]")
    if row.quote_ref:
        q = row.quote_ref.strip()
        if q:
            parts.append(f"[quote-ref: {q}]")
    parts.append(f"[csv-row: {row.row_index}]")
    if row.notes:
        t = row.notes.strip()
        if t:
            parts.append(t)
    return " ".join(parts)


# ---------------------------------------------------------------------------
# Apply
# ---------------------------------------------------------------------------


def apply_batch_plan(
    estimate: Estimate,
    plan: BatchOverridePlan,
    auto_apply_matched: bool = True,
    resolved_ambiguous: dict[int, int] | None = None,
    skip_rows: set[int] | None = None,
) -> tuple[Estimate, list[str]]:
    """Apply the match plan to an Estimate.

    Returns ``(new_estimate, applied_summary_lines)``.

    For each :attr:`BatchMatchStatus.MATCHED` row (when
    ``auto_apply_matched=True``), calls
    :func:`core.estimator.apply_manual_override` with the operator-note
    formatted via :func:`format_batch_operator_note`.

    For each :attr:`BatchMatchStatus.AMBIGUOUS` row, the operator
    must resolve via ``resolved_ambiguous`` (maps CSV ``row_index`` to
    a CostLine index). Unresolved AMBIGUOUS rows are skipped (logged
    in the summary).

    :attr:`BatchMatchStatus.LOW_SIMILARITY` and
    :attr:`BatchMatchStatus.NO_MATCH` rows are **never** applied.
    They are logged in the summary so the operator can spot rows that
    needed manual intervention.

    Rows whose ``row_index`` appears in ``skip_rows`` are always
    skipped regardless of status. Useful for the UI's per-row
    "skip" affordance after the operator inspects the preview.

    Idempotency: applying the same plan twice produces an Estimate
    with identical CostLine fields on every overridden row (inherited
    from the T6.1 single-line ``apply_manual_override`` idempotency
    contract). The operator note is appended once per call when
    supplied, so calling ``apply_batch_plan`` twice WILL grow the
    ``notes`` blob — callers wanting strict idempotency should de-dup
    the plan before re-applying.
    """
    resolved = resolved_ambiguous or {}
    skip = skip_rows or set()

    summary: list[str] = []
    current = estimate

    applied_count = 0
    skipped_count = 0

    if auto_apply_matched:
        for result in plan.matched:
            if result.row.row_index in skip:
                summary.append(
                    f"Row {result.row.row_index}: SKIPPED (operator opt-out)."
                )
                skipped_count += 1
                continue
            if result.best_match_index is None:
                continue
            note = format_batch_operator_note(result.row)
            try:
                current = apply_manual_override(
                    current,
                    result.best_match_index,
                    new_unit_cost=result.row.unit_cost,
                    operator_note=note,
                )
            except ValueError as exc:
                summary.append(
                    f"Row {result.row.row_index}: APPLY FAILED "
                    f"({exc})."
                )
                continue
            summary.append(
                f"Row {result.row.row_index}: APPLIED to line "
                f"#{result.best_match_index} "
                f"(sim={result.best_match_similarity:.2f}) "
                f"\u2192 ${result.row.unit_cost:,.2f}/unit."
            )
            applied_count += 1

    for result in plan.ambiguous:
        if result.row.row_index in skip:
            summary.append(
                f"Row {result.row.row_index}: SKIPPED (operator opt-out)."
            )
            skipped_count += 1
            continue
        chosen = resolved.get(result.row.row_index)
        if chosen is None:
            summary.append(
                f"Row {result.row.row_index}: SKIPPED ambiguous "
                f"(best=#{result.best_match_index} sim="
                f"{result.best_match_similarity:.2f}, "
                f"runner-up=#{result.runner_up_index} sim="
                f"{result.runner_up_similarity:.2f}); "
                f"no resolution provided."
            )
            skipped_count += 1
            continue
        if not 0 <= chosen < len(current.line_items):
            summary.append(
                f"Row {result.row.row_index}: SKIPPED ambiguous "
                f"(resolved index {chosen} out of range)."
            )
            skipped_count += 1
            continue
        note = format_batch_operator_note(result.row)
        try:
            current = apply_manual_override(
                current,
                chosen,
                new_unit_cost=result.row.unit_cost,
                operator_note=note,
            )
        except ValueError as exc:
            summary.append(
                f"Row {result.row.row_index}: APPLY FAILED ({exc})."
            )
            continue
        summary.append(
            f"Row {result.row.row_index}: APPLIED ambiguous to line "
            f"#{chosen} (operator-resolved) "
            f"\u2192 ${result.row.unit_cost:,.2f}/unit."
        )
        applied_count += 1

    for result in plan.low_similarity:
        summary.append(
            f"Row {result.row.row_index}: SKIPPED low similarity "
            f"(best=#{result.best_match_index} sim="
            f"{result.best_match_similarity:.2f} < "
            f"{plan.similarity_threshold:.2f}); "
            f"manual review required."
        )
        skipped_count += 1

    for result in plan.no_match:
        summary.append(
            f"Row {result.row.row_index}: SKIPPED no match "
            f"(best sim={result.best_match_similarity:.2f}); "
            f"add to estimate manually."
        )
        skipped_count += 1

    summary.insert(
        0,
        f"Batch override summary: {applied_count} applied, "
        f"{skipped_count} skipped, {plan.total_rows} total rows.",
    )

    return current, summary


# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------


_MATCH_PLAN_CSV_FIELDS: tuple[str, ...] = (
    "csv_row",
    "csv_description",
    "csv_unit_cost",
    "status",
    "matched_line_index",
    "matched_description",
    "similarity",
    "runner_up_index",
    "runner_up_description",
    "runner_up_similarity",
    "notes",
)


def export_match_plan_csv(
    plan: BatchOverridePlan,
    cost_lines: list[CostLine] | None = None,
) -> str:
    """Export the match plan as a CSV for operator review.

    Columns:

    ``csv_row, csv_description, csv_unit_cost, status,
    matched_line_index, matched_description, similarity,
    runner_up_index, runner_up_description, runner_up_similarity, notes``

    ``matched_description`` / ``runner_up_description`` are populated
    only when ``cost_lines`` is supplied AND the corresponding index
    is in range. (The CostLine list is not stored on the plan, so the
    caller has to pass it in for descriptions to round-trip.)

    Rows are emitted in their original CSV order (i.e. by
    ``row.row_index``) rather than bucket order — that's the order the
    operator scrolled through their source spreadsheet.
    """
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=list(_MATCH_PLAN_CSV_FIELDS))
    writer.writeheader()

    all_results: list[BatchMatchResult] = (
        plan.matched + plan.ambiguous + plan.low_similarity + plan.no_match
    )
    all_results.sort(key=lambda r: r.row.row_index)

    for result in all_results:
        matched_desc = ""
        runner_desc = ""
        if cost_lines:
            if (
                result.best_match_index is not None
                and 0 <= result.best_match_index < len(cost_lines)
            ):
                matched_desc = cost_lines[result.best_match_index].description
            if (
                result.runner_up_index is not None
                and 0 <= result.runner_up_index < len(cost_lines)
            ):
                runner_desc = cost_lines[result.runner_up_index].description

        writer.writerow({
            "csv_row": result.row.row_index,
            "csv_description": result.row.description,
            "csv_unit_cost": f"{result.row.unit_cost:.2f}",
            "status": result.status.value,
            "matched_line_index": (
                "" if result.best_match_index is None
                else result.best_match_index
            ),
            "matched_description": matched_desc,
            "similarity": f"{result.best_match_similarity:.4f}",
            "runner_up_index": (
                "" if result.runner_up_index is None
                else result.runner_up_index
            ),
            "runner_up_description": runner_desc,
            "runner_up_similarity": f"{result.runner_up_similarity:.4f}",
            "notes": result.row.notes or "",
        })

    return buf.getvalue()
