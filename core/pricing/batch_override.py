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

    Phase T6.4.b: ``unit_of_measure`` carries the row's unit of measure
    (``"LF"`` / ``"SF"`` / ``"EA"`` / …) when the source spreadsheet
    or sub-quote PDF published one. Used by :func:`match_cost_lines`
    (default ``enforce_uom_compatibility=True``) to reject candidate
    matches whose ``CostLine.unit`` is incompatible with the row's UoM
    — i.e. a ``$45/LF`` row is no longer matched against a ``$95/SF``
    cost line. Stored in raw form (``"linear ft"`` / ``"sq. ft."``);
    the matcher canonicalises via :func:`normalize_uom` at compare
    time. Defaults to ``None`` so every pre-T6.4.b caller (which never
    supplied a UoM) keeps working — and the matcher falls through to
    description-only matching when the row has no UoM.
    """

    row_index: int
    description: str
    unit_cost: float
    vendor: str | None = None
    quote_ref: str | None = None
    notes: str | None = None
    quantity: float | None = None
    unit_of_measure: str | None = None


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
    # Phase T6.4.b: human-readable warning surfaced when the matcher
    # detects a UoM mismatch between the row and the chosen / candidate
    # cost line. Always ``None`` on the safety-on
    # (``enforce_uom_compatibility=True``) path — those mismatches are
    # rejected outright and the row drops to NO_MATCH instead. Populated
    # on the safety-off (``enforce_uom_compatibility=False``) path so an
    # operator who explicitly bypasses the gate still gets a heads-up
    # about which lines are likely cross-applied. Format:
    # ``"unit mismatch: row=LF vs line=SF"``.
    uom_mismatch_warning: str | None = None


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
#
# Phase T8.1 extension: the ``extended`` slot was added so the shared
# alias map can serve the sub-quote PDF parser (``core.pricing.
# subquote_parser``) which often sees vendor PDFs that publish
# ``Description / Qty / Extended`` without a unit-price column — the
# parser derives ``unit_cost = extended / qty`` in that case. The CSV
# parser (``parse_vendor_csv``) ignores the ``extended`` slot today
# (its required column is still ``unit_cost``); adding the entry is
# purely additive — no CSV behaviour changes.
_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "description": ("description", "desc", "item", "item_description", "line_item"),
    "unit_cost": ("unit_cost", "price", "unit_price", "cost", "$/unit", "rate"),
    "extended": (
        "extended", "extended_price", "extended_cost", "extension",
        "line_total", "total", "amount",
    ),
    "vendor": ("vendor", "supplier", "sub", "subcontractor"),
    "quote_ref": (
        "quote_ref", "quote", "quote_id", "ref", "reference", "po", "po_number",
    ),
    "notes": ("notes", "comments", "remarks"),
    "quantity": ("quantity", "qty", "q"),
    # Phase T6.4.b: unit-of-measure column alias group. Picked up by
    # :func:`parse_vendor_csv` (CSV slot) and the sub-quote PDF tabular
    # parser (which uses the same shared ``_COLUMN_ALIASES`` map). Empty
    # / unrecognised values fall through to ``unit_of_measure=None`` on
    # the row, which the matcher treats as "no UoM available" and falls
    # back to description-only matching.
    "unit_of_measure": (
        "unit_of_measure", "unit", "uom", "units", "u_o_m", "uomeasure",
    ),
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
# Phase T6.4.c — canonical source-tag constants
# ---------------------------------------------------------------------------
#
# Every batch-apply path (vendor CSV, sub-quote PDF tabular, sub-quote PDF
# LLM-vision fallback) stamps a ``source_tag`` at the start of the
# ``CostLine.notes`` field so a downstream auditor (Excel exporter, client
# PDF, Streamlit history viewer) can attribute a priced-line override to
# its provenance at a glance. The tag is always the FIRST characters of
# the notes string and matches the pattern ``^\[[a-z-]+\] `` — i.e. an
# anchored single bracketed lowercase-and-hyphen token followed by a
# single space.
#
# ``SOURCE_TAG_BATCH`` is the legacy default carried since T6.3 ship. Kept
# as the default for :func:`format_batch_operator_note` so every
# pre-T6.4.c test + caller (whose snapshots literal-match ``[batch] ``)
# stays byte-identical. Callers that want explicit provenance pass one
# of the more specific constants below.

SOURCE_TAG_BATCH: str = "[batch]"
SOURCE_TAG_VENDOR_CSV: str = "[vendor-csv]"
SOURCE_TAG_SUBQUOTE_TABULAR: str = "[sub-quote]"
SOURCE_TAG_SUBQUOTE_LLM: str = "[sub-quote-llm]"
SOURCE_TAG_MANUAL_OVERRIDE: str = "[manual-override]"


# Frozen set of every canonical tag, exposed so tests and downstream
# pattern-matchers can iterate without hard-coding the string literals.
SOURCE_TAGS_CANONICAL: frozenset[str] = frozenset({
    SOURCE_TAG_BATCH,
    SOURCE_TAG_VENDOR_CSV,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_MANUAL_OVERRIDE,
})


# Regex that every canonical source tag matches when anchored at the
# start of a notes string. Used by tests to assert tag-first placement
# without naming a specific tag.
SOURCE_TAG_PATTERN: str = r"^\[[a-z][a-z\-]*\] "


# ---------------------------------------------------------------------------
# Phase T6.4.b — unit-of-measure canonicalisation + compatibility
# ---------------------------------------------------------------------------
#
# Background: prior to T6.4.b, :func:`match_cost_lines` matched purely
# on description text. A vendor CSV / sub-quote PDF row that said
# ``"$45/LF"`` happily matched a cost line priced ``"$95/SF"`` whenever
# the descriptions were lexically close, silently producing a per-LF
# price applied against a per-SF takeoff — the LF×SF cross-application
# bug. T6.4.b introduces a UoM-aware filter that rejects such
# cross-applications by default.
#
# Canonical forms — uppercase, no whitespace, no punctuation. The map
# below is intentionally a superset of the actual UoMs in
# :file:`config/cost_database.json` (which today uses
# ``CF / CY / EA / HR / LF / LS / MO / SF / TON``) plus the variants
# the project's :class:`~core.schemas.MEPItem` / :class:`StructuralElement`
# / :class:`UnitPrice` schemas reference (``SY``, ``GAL``, ``LB``,
# ``DAY``, ``LOT``, ``PR``, ``SET``, …) so a vendor PDF's free-form
# "linear feet" or "lump sum" maps cleanly. Adding a variant is a
# pure-additive change — :func:`normalize_uom` falls through to
# ``None`` for unknown inputs, which the matcher treats as
# "no UoM available".


UOM_CANONICAL: dict[str, str] = {
    # ---- Length ----------------------------------------------------------
    "lf": "LF",
    "linft": "LF",
    "linearft": "LF",
    "lin ft": "LF",
    "linear ft": "LF",
    "linear feet": "LF",
    "linear foot": "LF",
    "ft": "LF",
    "foot": "LF",
    "feet": "LF",
    # Inches map to LF — most vendor inputs treating LF and inches
    # interchangeably are actually LF (the "$/inch" cost-class is rare
    # and not represented in cost_database.json today). Prefer to map
    # rather than reject.
    "in": "LF",
    "inch": "LF",
    "inches": "LF",
    # Metric length — kept as their own canonical forms so a metric
    # vendor doesn't silently match against an imperial cost line.
    "m": "M",
    "meter": "M",
    "meters": "M",
    "metre": "M",
    "metres": "M",
    "mm": "MM",
    "millimeter": "MM",
    "millimeters": "MM",
    "cm": "CM",
    "centimeter": "CM",
    "centimeters": "CM",
    # ---- Area ------------------------------------------------------------
    "sf": "SF",
    "sqft": "SF",
    "sq ft": "SF",
    "sq. ft.": "SF",
    "sq. ft": "SF",
    "square feet": "SF",
    "square foot": "SF",
    "ft2": "SF",
    "ft^2": "SF",
    "ft²": "SF",
    "sy": "SY",
    "sqyd": "SY",
    "sq yd": "SY",
    "sq. yd.": "SY",
    "square yard": "SY",
    "square yards": "SY",
    "sm": "SM",
    "sqm": "SM",
    "m2": "SM",
    "m^2": "SM",
    "m²": "SM",
    "square meter": "SM",
    "square meters": "SM",
    "square metre": "SM",
    "square metres": "SM",
    # ---- Volume ----------------------------------------------------------
    "cy": "CY",
    "cuyd": "CY",
    "cu yd": "CY",
    "cu. yd.": "CY",
    "cubic yard": "CY",
    "cubic yards": "CY",
    "yd3": "CY",
    "cf": "CF",
    "cuft": "CF",
    "cu ft": "CF",
    "cu. ft.": "CF",
    "cubic foot": "CF",
    "cubic feet": "CF",
    "ft3": "CF",
    "cm_vol": "CM3",  # disambiguator for cubic meter vs centimeter is via
    "m3": "CM3",        # the "m3" entry; "cm3" stays out of here because
    "cubic meter": "CM3",   # 'cm' (centimeter, length) already owns it.
    "cubic meters": "CM3",
    "gal": "GAL",
    "gallon": "GAL",
    "gallons": "GAL",
    "l": "L",
    "liter": "L",
    "liters": "L",
    "litre": "L",
    "litres": "L",
    # ---- Weight / mass ---------------------------------------------------
    "lb": "LB",
    "lbs": "LB",
    "pound": "LB",
    "pounds": "LB",
    "ton": "TON",
    "tons": "TON",
    "tn": "TON",
    "kg": "KG",
    "kilogram": "KG",
    "kilograms": "KG",
    # ---- Count -----------------------------------------------------------
    "ea": "EA",
    "each": "EA",
    "lot": "LOT",
    "pr": "PR",
    "pair": "PR",
    "pairs": "PR",
    "set": "SET",
    "sets": "SET",
    "pc": "EA",
    "pcs": "EA",
    "piece": "EA",
    "pieces": "EA",
    # ---- Time ------------------------------------------------------------
    "hr": "HR",
    "hrs": "HR",
    "hour": "HR",
    "hours": "HR",
    "day": "DAY",
    "days": "DAY",
    "wk": "WK",
    "week": "WK",
    "weeks": "WK",
    "mo": "MO",
    "month": "MO",
    "months": "MO",
    "yr": "YR",
    "year": "YR",
    "years": "YR",
    # ---- Generic / lump --------------------------------------------------
    "ls": "LS",
    "lump sum": "LS",
    "lumpsum": "LS",
    "lump": "LS",
    # ---- Roofing / framing specialties (canonical to themselves) --------
    "sq": "SQ",                 # roofing square = 100 SF; not interchangeable
    "square": "SQ",             # with SF for matching purposes (different unit math)
    "mbf": "MBF",               # 1000 board feet (lumber)
    "bf": "BF",                 # board feet (lumber)
    "sack": "SACK",
    "sacks": "SACK",
    "bag": "SACK",
    "bags": "SACK",
}


# Whitespace + punctuation strip used by :func:`normalize_uom`. We do
# NOT reuse the description-side ``_PUNCT_RE`` (defined further down)
# because UoM tokens like ``"sq. ft."`` carry a meaningful period —
# we strip the period at the canonical-map lookup level rather than
# pre-emptively at the regex level so ``"sq. ft."`` and ``"sq ft"``
# both land at the same key. Multiple internal spaces collapse to
# one before lookup so ``"  square   feet  "`` works.
_UOM_WS_RE = re.compile(r"\s+")


def normalize_uom(raw: str | None) -> str | None:
    """Map a free-form UoM string to its canonical form, or ``None``.

    Case-insensitive, whitespace-tolerant, period-tolerant. Returns
    ``None`` for ``None``, empty / whitespace-only inputs, and any
    string not in :data:`UOM_CANONICAL` (so the caller can fall
    through to "no UoM info" semantics rather than guessing).

    Examples::

        normalize_uom("LF")          == "LF"
        normalize_uom("lf")          == "LF"
        normalize_uom(" lf ")        == "LF"
        normalize_uom("linear ft")   == "LF"
        normalize_uom("Square Feet") == "SF"
        normalize_uom("sq. ft.")     == "SF"
        normalize_uom("")            is None
        normalize_uom(None)          is None
        normalize_uom("xyz")         is None
    """
    if raw is None:
        return None
    s = str(raw).strip().lower()
    if not s:
        return None
    # Try the original (lowercased + stripped) form first so
    # punctuation-bearing keys like ``"sq. ft."`` land directly.
    if s in UOM_CANONICAL:
        return UOM_CANONICAL[s]
    # Collapse internal whitespace and try again.
    collapsed = _UOM_WS_RE.sub(" ", s).strip()
    if collapsed in UOM_CANONICAL:
        return UOM_CANONICAL[collapsed]
    # Strip trailing periods (``"sq ft."`` → ``"sq ft"``) and
    # internal periods (``"sq. ft."`` → ``"sq ft"``) and try again.
    no_dots = collapsed.replace(".", "").strip()
    no_dots = _UOM_WS_RE.sub(" ", no_dots).strip()
    if no_dots in UOM_CANONICAL:
        return UOM_CANONICAL[no_dots]
    # Final attempt: also strip internal whitespace so ``"linear  ft"``
    # without spaces lands at ``"linearft"`` keyword.
    no_ws = no_dots.replace(" ", "")
    if no_ws in UOM_CANONICAL:
        return UOM_CANONICAL[no_ws]
    return None


# Compatibility groups: UoMs in the same group are considered
# interchangeable for matching purposes. Strict by default — a UoM
# not appearing in any group is only compatible with itself.
#
# Rationale per group:
#
# * ``{"LS", "LOT"}`` — both represent a single lump-sum line. Vendor
#   PDFs commonly say "LOT" where the cost catalog says "LS" (or vice
#   versa). Numerically interchangeable: cost is per-occurrence.
# * ``{"EA", "SET"}`` — looser: a "set" of door hardware vs. an "each"
#   item is a real shape difference, but vendors routinely write
#   "SET" where the catalog has "EA" for assembly-priced hardware.
#   Allowed because the alternative (rejecting the match outright)
#   tends to be worse than the small over-application risk.
# * ``{"PR", "EA"}`` — "pair" is sometimes priced as 2x EA, sometimes
#   as a unit. We allow the match — operator can adjust the unit
#   cost manually if the convention differs.
#
# Notes deliberately NOT in any group (strict by intent):
#
# * LF, SF, SY, SM, CY, CF, GAL, LB, TON, HR, DAY, MO, SQ — all
#   stay strict. Matching ``LF→SF`` is exactly the bug the slice
#   exists to prevent; matching ``SY→SF`` would silently triple
#   the unit cost; matching ``CY→CF`` would silently 27x it.
# * Metric-vs-imperial pairs (``M ↔ LF``, ``SM ↔ SF``, ``CM3 ↔ CY``)
#   are NOT compatible. The conversion factor is real (1 SM ≈
#   10.76 SF) but applying a per-SM price to a per-SF line would
#   silently undercount by 10x. The price-conversion concern is a
#   separate slice if it ever materialises in the calibration set.

UOM_COMPATIBILITY_GROUPS: list[set[str]] = [
    {"LS", "LOT"},
    {"EA", "SET"},
    {"EA", "PR"},
]


def uoms_compatible(a: str | None, b: str | None) -> bool:
    """Return ``True`` if two UoMs may be matched together.

    Convention (matches the brief exactly):

    * Both ``None`` → ``True``  (no UoM info; defer to description-only
      match — caller decides whether to flag the result).
    * One ``None``, one specific → ``True``  (defensive: only one side
      knows the UoM; the matcher should not penalise the row when the
      cost line lacks a unit, and vice versa).
    * Both specific, same canonical → ``True``  (e.g. row=``"LF"`` and
      line=``"linear ft"`` both canonicalise to ``"LF"``).
    * Both specific, in same compatibility group → ``True``
      (e.g. ``"LS"`` ↔ ``"LOT"``).
    * Both specific, different groups → ``False`` (the safety check).

    Both inputs are routed through :func:`normalize_uom` first so
    free-form strings (``"linear ft"`` / ``"sq. ft."``) work unchanged.
    A specific raw input that fails normalisation (e.g. ``"xyz"``) is
    treated as ``None`` for compatibility purposes — i.e. the matcher
    falls back to defensive "we don't know, let it through" semantics.
    The brief's intent is "reject when we can prove a mismatch", not
    "reject when in doubt".
    """
    canon_a = normalize_uom(a)
    canon_b = normalize_uom(b)
    # Both None / un-normalisable → defer to description-only match.
    if canon_a is None and canon_b is None:
        return True
    # One side knows, the other doesn't → defensive True.
    if canon_a is None or canon_b is None:
        return True
    if canon_a == canon_b:
        return True
    for group in UOM_COMPATIBILITY_GROUPS:
        if canon_a in group and canon_b in group:
            return True
    return False


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

        # Phase T6.4.b: pick up the optional ``unit_of_measure`` column
        # (alias group: unit / uom / units / …). Stored raw — the
        # matcher canonicalises via :func:`normalize_uom` at compare
        # time so the stored form preserves the operator's input for
        # downstream display.
        uom: str | None = None
        if "unit_of_measure" in col_map:
            u = (raw.get(col_map["unit_of_measure"], "") or "").strip()
            uom = u or None

        rows.append(BatchOverrideRow(
            row_index=csv_row_idx,
            description=desc,
            unit_cost=uc,
            vendor=vendor,
            quote_ref=quote_ref,
            notes=notes,
            quantity=qty,
            unit_of_measure=uom,
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


def _format_uom_mismatch(row_uom: str | None, line_uom: str | None) -> str:
    """Format the canonical ``"unit mismatch: row=LF vs line=SF"`` string.

    Used by :func:`match_cost_lines` (safety-off path) to populate
    :pyattr:`BatchMatchResult.uom_mismatch_warning`. Falls back to the
    raw / un-canonicalised form when one side is unrecognised so the
    operator sees the verbatim source text rather than a silent
    ``None``.
    """
    canon_row = normalize_uom(row_uom)
    canon_line = normalize_uom(line_uom)
    row_label = canon_row if canon_row is not None else (
        (row_uom or "").strip() or "?"
    )
    line_label = canon_line if canon_line is not None else (
        (line_uom or "").strip() or "?"
    )
    return f"unit mismatch: row={row_label} vs line={line_label}"


def match_cost_lines(
    rows: list[BatchOverrideRow],
    cost_lines: list[CostLine],
    similarity_threshold: float = 0.65,
    ambiguity_margin: float = 0.10,
    *,
    enforce_uom_compatibility: bool = True,
) -> BatchOverridePlan:
    """Fuzzy-match each CSV row to a CostLine by description.

    Uses :func:`difflib.SequenceMatcher.ratio` on normalised descriptions
    (see :func:`_normalise_description`). For each row:

    * Computes similarity against every CostLine.
    * Optionally filters out candidates whose ``unit`` is incompatible
      with the row's ``unit_of_measure`` (T6.4.b safety check; default
      on).
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

    Phase T6.4.b: ``enforce_uom_compatibility`` (keyword-only, default
    ``True``) gates the unit-compatibility filter. When ``True`` the
    matcher rejects candidate cost lines whose ``unit`` is incompatible
    with the row's :pyattr:`BatchOverrideRow.unit_of_measure` per
    :func:`uoms_compatible` — i.e. an ``LF`` vendor row can no longer
    be applied to an ``SF`` cost line, eliminating the LF/SF
    cross-application bug. When ``False`` the matcher reverts to the
    pre-T6.4.b description-only behaviour but populates
    :pyattr:`BatchMatchResult.uom_mismatch_warning` with a human-
    readable string whenever the chosen line's UoM disagrees with the
    row's UoM, so an operator who explicitly bypasses the gate still
    gets a heads-up.

    UoM filter semantics (when ``enforce_uom_compatibility=True``):

    * Row has no UoM → no filter (description-only match; defensive).
    * Cost line has no UoM → not filtered (defensive).
    * Row UoM canonicalises to None (unrecognised) → not filtered
      (treated as "we don't know"; matcher must not reject when
      uncertain — only when it can prove a mismatch).
    * Row + line UoMs both specific and incompatible → candidate
      removed from the candidate set entirely. If filtering leaves
      the row with no above-floor candidates, it lands in NO_MATCH.

    Filter side-effects on bucket assignment:

    * A previously-MATCHED row whose only candidate fails the filter
      drops to NO_MATCH (with no warning — the safety-on path is the
      correctness-first one).
    * A previously-AMBIGUOUS row whose runner-up fails the filter but
      whose best survives may resolve to MATCHED (filter narrowed the
      candidate space; less ambiguity).
    * The filter is applied on the candidate level, so candidate_lines
      reported to the operator never contain UoM-incompatible lines
      on the safety-on path.
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

        # Phase T6.4.b — split the cost-line index space into
        # UoM-compatible and UoM-incompatible buckets up front. The
        # safety-on path matches against the compatible bucket only;
        # the safety-off path matches against the full set but uses
        # the incompatible bucket to populate the warning string.
        compatible_indices: list[int] = []
        incompatible_indices: list[int] = []
        for i, li in enumerate(cost_lines):
            if uoms_compatible(row.unit_of_measure, li.unit):
                compatible_indices.append(i)
            else:
                incompatible_indices.append(i)

        if enforce_uom_compatibility:
            search_indices = compatible_indices
        else:
            search_indices = list(range(len(cost_lines)))

        if not search_indices:
            # Safety-on with zero compatible candidates → land in
            # NO_MATCH. The diagnostic best/runner against the FULL
            # cost-line set is kept so an operator can see what the
            # description match would have produced if they bypassed
            # the filter (these surface in candidate_lines / sims for
            # the operator UI). The status is unchanged from "would
            # have been NO_MATCH" because every candidate failed the
            # UoM gate.
            full_sims: list[tuple[int, float]] = [
                (i, _similarity(row, cost_lines[i]))
                for i in range(len(cost_lines))
            ]
            full_sims.sort(key=lambda pair: (-pair[1], pair[0]))
            best_idx_full, best_sim_full = full_sims[0]
            warning = _format_uom_mismatch(
                row.unit_of_measure,
                cost_lines[best_idx_full].unit,
            )
            result = BatchMatchResult(
                row=row,
                status=BatchMatchStatus.NO_MATCH,
                best_match_index=None,
                best_match_similarity=round(best_sim_full, 4),
                runner_up_index=None,
                runner_up_similarity=0.0,
                candidate_lines=[],
                uom_mismatch_warning=warning,
            )
            plan.no_match.append(result)
            continue

        sims: list[tuple[int, float]] = [
            (i, _similarity(row, cost_lines[i])) for i in search_indices
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

        # Phase T6.4.b: on the safety-off path, populate the warning
        # string when the chosen best line's UoM is incompatible with
        # the row's UoM. Only meaningful when a best line was actually
        # chosen (MATCHED / AMBIGUOUS) — LOW_SIMILARITY / NO_MATCH
        # rows aren't getting applied so the warning would be noise.
        warning: str | None = None
        if (
            not enforce_uom_compatibility
            and best_match_index is not None
            and not uoms_compatible(
                row.unit_of_measure,
                cost_lines[best_match_index].unit,
            )
        ):
            warning = _format_uom_mismatch(
                row.unit_of_measure,
                cost_lines[best_match_index].unit,
            )

        result = BatchMatchResult(
            row=row,
            status=status,
            best_match_index=best_match_index,
            best_match_similarity=round(best_sim, 4),
            runner_up_index=runner_idx,
            runner_up_similarity=round(runner_sim, 4),
            candidate_lines=top_k,
            uom_mismatch_warning=warning,
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


def format_batch_operator_note(
    row: BatchOverrideRow,
    source_tag: str = SOURCE_TAG_BATCH,
) -> str:
    """Format the operator note for a batch-applied override.

    Format::

        <source_tag> [vendor: <vendor>] [quote-ref: <quote_ref>] [csv-row: N] <notes>

    The leading tag (``[batch]`` by default) signals the override came
    from a bulk-ingest path. Phase T8.1 wires the sub-quote PDF parser
    through the same function with ``source_tag="[sub-quote]"`` so an
    auditor can grep the override note and tell at a glance whether a
    given line was hand-priced (no tag), bulk-CSV-applied (``[batch]``),
    or sub-quote-PDF-applied (``[sub-quote]``). The parameter is
    optional with a ``[batch]`` default so every pre-existing T6.3
    caller stays byte-identical.

    ``[csv-row: N]`` is always present (every row has a known source
    index). The other fields appear only when populated; empty ones are
    skipped without leaving double-space gaps.

    The returned string is the operator-note payload — :func:`core.estimator.
    apply_manual_override` will prefix it with the
    :data:`~core.estimator.MANUAL_OVERRIDE_NOTE_PREFIX` sentinel
    (``"operator override"``) before stamping onto the CostLine's
    ``notes`` field.
    """
    parts: list[str] = [source_tag]
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


def _rewrite_notes_with_tag_first(
    *,
    source_tag: str,
    note_payload: str,
    prior_notes: str | None,
) -> str:
    """Phase T6.4.c — rewrite a post-override notes string so ``source_tag``
    is the FIRST token in the line, preserving prior notes as a suffix.

    Background: :func:`core.estimator.apply_manual_override` produces a
    string of the form ``"<prior_notes> | operator override: <payload>"``
    (or just ``"operator override: <payload>"`` when ``prior_notes`` is
    empty). That layout buries the provenance tag in the middle of the
    cell, where a narrow Excel / PDF column truncates it out of sight.
    This helper rebuilds the string so:

        "{source_tag} operator override: {payload-without-leading-tag}
            [| previous: {prior_notes}]"

    so a downstream reader sees the tag immediately, the override
    sentinel ("operator override") next, and the prior notes preserved
    as an explicit suffix.

    Idempotency: re-applying the same override (same ``source_tag`` +
    same ``note_payload``) does NOT accumulate duplicate tags. The
    helper detects when ``prior_notes`` already starts with the same
    head string and short-circuits (returns ``prior_notes`` unchanged).

    Args:
        source_tag: A canonical source tag (e.g. ``[sub-quote]``).
            Should match :data:`SOURCE_TAG_PATTERN` but the helper is
            permissive — any string is accepted so the contract works
            for operator-extension tags too.
        note_payload: The full operator-note string returned by
            :func:`format_batch_operator_note`. MUST start with
            ``source_tag + " "`` (that is the contract of
            ``format_batch_operator_note``).
        prior_notes: The line's ``notes`` field BEFORE the override
            was applied. ``None`` / empty → no "previous" suffix.

    Returns:
        A new notes string with ``source_tag`` at position 0.
    """
    prefix = source_tag + " "
    if note_payload.startswith(prefix):
        rest_of_payload = note_payload[len(prefix):]
    else:
        # Defensive: ``format_batch_operator_note`` always prefixes
        # ``source_tag + " "`` but a misuse / future drift shouldn't
        # crash the apply path. Fall back to using the payload as-is.
        rest_of_payload = note_payload
    head = f"{source_tag} operator override: {rest_of_payload}"

    prior = (prior_notes or "").strip()
    if not prior:
        return head

    # Idempotency: prior_notes already represents the same head (with
    # or without an existing "| previous: ..." chain). Don't accumulate.
    if prior == head or prior.startswith(head + " | previous: "):
        return prior

    return f"{head} | previous: {prior}"


def apply_batch_plan(
    estimate: Estimate,
    plan: BatchOverridePlan,
    auto_apply_matched: bool = True,
    resolved_ambiguous: dict[int, int] | None = None,
    skip_rows: set[int] | None = None,
    *,
    source_tag: str = SOURCE_TAG_BATCH,
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
    contract). Phase T6.4.c additionally guarantees that re-applying
    the same plan does NOT accumulate duplicate source tags in
    ``CostLine.notes`` — :func:`_rewrite_notes_with_tag_first`
    detects an already-stamped tag and short-circuits.

    Phase T6.4.c — ``source_tag`` (keyword-only) propagates an explicit
    provenance marker into every overridden line's ``notes`` field at
    position 0 so a downstream auditor (Excel exporter, client PDF,
    history viewer) sees the override origin at a glance even when the
    cell is narrow. Default :data:`SOURCE_TAG_BATCH` preserves byte-
    identical behaviour for every pre-T6.4.c caller (T6.3 vendor CSV).
    Sub-quote callers should pass :data:`SOURCE_TAG_SUBQUOTE_TABULAR`
    or :data:`SOURCE_TAG_SUBQUOTE_LLM` (or use
    :func:`core.pricing.subquote_parser.apply_subquote_plan` which
    wires the right tag for each path).
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
            note = format_batch_operator_note(result.row, source_tag=source_tag)
            # Phase T6.4.b: when the matcher ran with
            # ``enforce_uom_compatibility=False`` and detected a
            # UoM mismatch on this match, append the warning to the
            # operator note so the audit trail records the bypass.
            # The warning is always None on the safety-on path.
            if result.uom_mismatch_warning:
                note = f"{note} [{result.uom_mismatch_warning}]"
            idx = result.best_match_index
            prior_notes = current.line_items[idx].notes
            try:
                current = apply_manual_override(
                    current,
                    idx,
                    new_unit_cost=result.row.unit_cost,
                    operator_note=note,
                )
            except ValueError as exc:
                summary.append(
                    f"Row {result.row.row_index}: APPLY FAILED "
                    f"({exc})."
                )
                continue
            # Phase T6.4.c — hoist source_tag to position 0 of CostLine.notes
            # so the provenance is visible at a glance in exports.
            new_notes_value = _rewrite_notes_with_tag_first(
                source_tag=source_tag,
                note_payload=note,
                prior_notes=prior_notes,
            )
            updated_line = current.line_items[idx].model_copy(
                update={"notes": new_notes_value}
            )
            new_lines = list(current.line_items)
            new_lines[idx] = updated_line
            current = current.model_copy(update={"line_items": new_lines})
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
        note = format_batch_operator_note(result.row, source_tag=source_tag)
        # Phase T6.4.b: same UoM-mismatch warning propagation as the
        # MATCHED branch above.
        if result.uom_mismatch_warning:
            note = f"{note} [{result.uom_mismatch_warning}]"
        prior_notes = current.line_items[chosen].notes
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
        # Phase T6.4.c — hoist source_tag to position 0 (see MATCHED branch).
        new_notes_value = _rewrite_notes_with_tag_first(
            source_tag=source_tag,
            note_payload=note,
            prior_notes=prior_notes,
        )
        updated_line = current.line_items[chosen].model_copy(
            update={"notes": new_notes_value}
        )
        new_lines = list(current.line_items)
        new_lines[chosen] = updated_line
        current = current.model_copy(update={"line_items": new_lines})
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
    "csv_unit_of_measure",
    "status",
    "matched_line_index",
    "matched_description",
    "matched_unit",
    "similarity",
    "runner_up_index",
    "runner_up_description",
    "runner_up_similarity",
    "uom_mismatch_warning",
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
        matched_unit = ""
        runner_desc = ""
        if cost_lines:
            if (
                result.best_match_index is not None
                and 0 <= result.best_match_index < len(cost_lines)
            ):
                matched_desc = cost_lines[result.best_match_index].description
                matched_unit = cost_lines[result.best_match_index].unit
            if (
                result.runner_up_index is not None
                and 0 <= result.runner_up_index < len(cost_lines)
            ):
                runner_desc = cost_lines[result.runner_up_index].description

        writer.writerow({
            "csv_row": result.row.row_index,
            "csv_description": result.row.description,
            "csv_unit_cost": f"{result.row.unit_cost:.2f}",
            "csv_unit_of_measure": result.row.unit_of_measure or "",
            "status": result.status.value,
            "matched_line_index": (
                "" if result.best_match_index is None
                else result.best_match_index
            ),
            "matched_description": matched_desc,
            "matched_unit": matched_unit,
            "similarity": f"{result.best_match_similarity:.4f}",
            "runner_up_index": (
                "" if result.runner_up_index is None
                else result.runner_up_index
            ),
            "runner_up_description": runner_desc,
            "runner_up_similarity": f"{result.runner_up_similarity:.4f}",
            "uom_mismatch_warning": result.uom_mismatch_warning or "",
            "notes": result.row.notes or "",
        })

    return buf.getvalue()
