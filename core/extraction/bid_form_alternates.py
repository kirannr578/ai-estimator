"""Bid-form alternates / value-engineering extraction (Phase T9.0).

Bid forms enumerate alternate line items the bidder must price as
additions, deductions, substitutions, or value-engineering suggestions.
Pre-T9.0 the pipeline carried these as the informational
:class:`core.schemas.Alternate` records on each :class:`BidPackage`
(narrative description + optional dollar amount, no signed-cost
semantics). T9.0 introduces a parallel, priceable
:class:`core.schemas.AlternateLine` shape and this module is the
extractor for it.

Two extraction paths, both feeding the same reconciliation step:

1. **Deterministic** (preferred): regex + heuristic parsing for the
   common bid-form formats:

   * ``Alternate No. 1: <description> ........ $______ ADD``
   * ``Alternate #1 (DEDUCT): <description>``
   * ``Bid Alternate A: <description> | Cost delta: $______``
   * ``Add Alternate 2: ...``
   * ``VE Item 3: substitute X for Y, save $Z``

2. **LLM fallback**: when :func:`detect_alternates_section` says a
   page contains alternates but :func:`extract_alternates_from_page`
   returns an empty list (the regex pass missed a non-standard
   layout), the caller may invoke :func:`extract_alternates_via_llm`
   (lives in :mod:`core.extractors` to keep the LLM-client wiring in
   one place) and pass the result back to
   :func:`reconcile_alternate_sources` for merging.

The reconciler dedupes alternates that the deterministic and LLM
paths both extracted, prefers the deterministic record (higher
confidence), and tags every emitted :class:`AlternateLine` with a
``pricing_basis`` hint via its description / scope_summary fields so
downstream consumers can audit provenance.

This module is **read-only** with respect to LLM clients — the LLM
fallback path lives in :mod:`core.extractors` and is invoked
explicitly by the caller. Keeps this module unit-testable without
any LLM mocks for the deterministic surface.
"""

from __future__ import annotations

import logging
import re
from typing import Iterable

from ..schemas import AlternateLine, AlternateType

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Page-level detection
# ---------------------------------------------------------------------------
#
# Section-header keywords. Case-insensitive substring matches over the
# raw page text. Generous on purpose: a single false-positive routes
# the page through the regex parser (which emits zero alternates on a
# non-alternates page anyway) and an LLM fallback (which a thoughtful
# prompt also turns into an empty list for a non-alternates page) —
# the cost is one extra parse attempt, the value is never missing a
# real alternate because the section header was atypical.

_SECTION_KEYWORDS: tuple[str, ...] = (
    "bid alternate",
    "bid alternates",
    "add alternate",
    "deduct alternate",
    "deductive alternate",
    "additive alternate",
    "alternates",
    "alternative bid",
    "alternative bids",
    "alternative pricing",
    "alternate pricing",
    "alternate proposal",
    "alternate price",
    "alternate item",
    "alternate add",
    "alternate deduct",
    "voluntary alternate",
    "voluntary alternates",
    # CSI section labels for the Schedule of Alternates (Texas-State /
    # TTUS / federal architectural specifications). T10 F-4: the Carr
    # EFA RFCSP main file labels its alternates page "01220 Schedule of
    # Alternates" rather than "BID ALTERNATES SECTION", so the bare
    # keyword scan misses it.
    "schedule of alternates",
    "section 01220",
    "section 01 22 00",
    "section 01 23 00",
    "01 23 00 - alternates",
    "01 22 00 - alternates",
    # CLIN-Option pattern (federal SF18/SF1449 evaluation options per FAR
    # 52.217-5). T10 F-4: the PAIS Cabin solicitation enumerates two
    # alternates as "Option 001 / Option 002" in the Price/Bid Schedule
    # without using the word "alternate".
    "option no",
    "clin option",
    "value engineering",
    "ve item",
    "ve items",
    "ve alternate",
    "ve alternates",
    "ve proposal",
    "substitution alternate",
    "alternate no.",
    "alternate #",
    "alt #",
    "alt no.",
)


# Additional regex-based section detectors for patterns that need digit
# disambiguation (so they don't fire on narrative phrases). T10 F-4: the
# PAIS Cabin solicitation enumerates alternates as bare ``Option 001`` /
# ``Option 002`` lines with no other "alternate" wording on the page.
_SECTION_REGEXES: tuple[re.Pattern[str], ...] = (
    re.compile(r"\boption\s+(?:no\.?\s*)?\d", re.IGNORECASE),
    re.compile(r"\bclin\s+(?:option|alt)", re.IGNORECASE),
)


def detect_alternates_section(page_text: str) -> bool:
    """Return True if ``page_text`` looks like it contains a bid-alternates section.

    Keyword-substring scan against :data:`_SECTION_KEYWORDS` plus a
    short regex pass over :data:`_SECTION_REGEXES` for patterns that
    need digit-disambiguation (e.g. ``Option 001`` vs the narrative
    phrase ``"option to extend"``). All matching is case-insensitive.

    False positives are tolerated — see the module docstring rationale.
    False negatives are the real risk; extend :data:`_SECTION_KEYWORDS`
    or :data:`_SECTION_REGEXES` when calibration surfaces a new
    section-header variant.
    """
    if not page_text:
        return False
    needle = page_text.lower()
    if any(kw in needle for kw in _SECTION_KEYWORDS):
        return True
    return any(rx.search(page_text) for rx in _SECTION_REGEXES)


# ---------------------------------------------------------------------------
# Type classification
# ---------------------------------------------------------------------------

# Keyword groups that classify a single alternate line into one of the four
# :class:`AlternateType` values. First match wins; VE patterns are checked
# before DEDUCTIVE because "VE = savings" wording often contains "deduct".
_TYPE_PATTERNS: tuple[tuple[AlternateType, tuple[str, ...]], ...] = (
    (
        AlternateType.VE,
        ("value engineering", "value-engineering", "ve item", "ve-item", "ve proposal"),
    ),
    (
        AlternateType.SUBSTITUTION,
        ("substitute", "substitution", "alternate to", "in lieu of", "swap", "replace with"),
    ),
    (
        AlternateType.DEDUCTIVE,
        ("deduct", "deductive", "omit", "delete", "remove", "savings", "credit"),
    ),
    (
        AlternateType.ADDITIVE,
        ("add", "additive", "additional", "include"),
    ),
)


def classify_alternate_type(text: str) -> AlternateType:
    """Map free-text wording to one of the four :class:`AlternateType` values.

    Falls back to :attr:`AlternateType.ADDITIVE` when no keyword fires
    (ADDITIVE is the dominant form in federal / state bid forms, so
    it's the safest default).

    Defensive case: "ve" as a bare token would false-match a word like
    "investigate"; the patterns above use multi-character anchors
    (``"ve item"``, ``"ve proposal"``) so a 2-char "ve" substring
    can't fire by itself.
    """
    if not text:
        return AlternateType.ADDITIVE
    needle = text.lower()
    for atype, patterns in _TYPE_PATTERNS:
        for pat in patterns:
            if pat in needle:
                return atype
    return AlternateType.ADDITIVE


# ---------------------------------------------------------------------------
# Cost-delta parsing
# ---------------------------------------------------------------------------

# Match a printed dollar amount on a bid-form line. Requires either a
# ``$`` sign OR a trailing ``USD`` suffix so bare numbers embedded in
# the description (e.g. "rooms 101, 102, and 103" or CSI codes like
# "09 65 19") don't accidentally match as the alternate's cost.
# Tolerates:
#   $1,234,567.89  $1234.56  $ 1,234  ($1,234) (parens → negative)
#   1234.56 USD   1,234 usd
_DOLLAR_RE = re.compile(
    r"""
    (?P<paren>\()?                                  # optional opening paren
    \s*
    (?:
        \$                                          # REQUIRED $ sign, OR
        \s*
        (?P<num_after_dollar>
            \d{1,3}(?:,\d{3})+(?:\.\d{1,2})?        # 1,234,567.89
            |
            \d+(?:\.\d{1,2})?                       # 1234.56
        )
        |
        (?P<num_with_usd>                           # plain number + USD
            \d{1,3}(?:,\d{3})+(?:\.\d{1,2})?
            |
            \d+(?:\.\d{1,2})?
        )
        \s+
        (?:USD|usd)
    )
    \s*
    (?P<paren_close>\))?                            # optional closing paren
    """,
    re.VERBOSE,
)

# Detect a blank fillable line ($_______, $______, $ ___, $____)
# common to printed federal / state bid forms. When matched, the line
# carries no extractable cost_delta — the LLM fallback won't help here
# either (the value isn't anywhere), so the line is emitted with
# ``cost_delta=None`` for downstream operator-entry.
_BLANK_FIELD_RE = re.compile(r"\$\s*_{2,}", re.IGNORECASE)


def parse_cost_delta(raw: str) -> float | None:
    """Extract a signed dollar amount from a bid-form line snippet.

    Returns ``None`` when no dollar amount is found OR when the field
    is a printed blank (``$______``). Parenthesized amounts are
    interpreted as negative (accounting convention).

    Caller is responsible for combining this with the
    :class:`AlternateType` classification to apply the final sign — for
    example, an ADDITIVE line printed as "$1,234" returns +1234.0 here
    and the caller keeps the sign positive; a DEDUCTIVE line printed
    as "$1,234" returns +1234.0 here and the caller flips to -1234.0.
    """
    if not raw:
        return None
    if _BLANK_FIELD_RE.search(raw):
        return None
    m = _DOLLAR_RE.search(raw)
    if not m:
        return None
    num_str = m.group("num_after_dollar") or m.group("num_with_usd")
    if not num_str:
        return None
    try:
        num = float(num_str.replace(",", ""))
    except (TypeError, ValueError):
        return None
    if m.group("paren") and m.group("paren_close"):
        num = -num
    return num


def _apply_type_sign(value: float | None, atype: AlternateType) -> float | None:
    """Flip ``value`` to the natural sign for ``atype`` (DEDUCTIVE / VE only).

    ADDITIVE and SUBSTITUTION values pass through unchanged (SUBSTITUTION
    is signed by the extractor's reading of the line). DEDUCTIVE and VE
    force the magnitude to a non-positive number — bid forms typically
    print the savings as a positive magnitude alongside a "DEDUCT" label,
    and the AlternateType-sign convention (`schemas.AlternateType`
    docstring) wants the delta to be negative so the math composes
    naturally.
    """
    if value is None:
        return None
    if atype in (AlternateType.DEDUCTIVE, AlternateType.VE):
        return -abs(value)
    return value


# ---------------------------------------------------------------------------
# Line-level parsing
# ---------------------------------------------------------------------------

# Match a line starting an alternate. Captures the identifier (the
# right-hand side of "Alternate"/"Alt"/"Bid Alternate"/"VE Item" plus
# the number / letter / token that follows), and the rest of the line
# as the description body.
_ALT_LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<prefix>
        (?:add\s+|deduct\s+|deductive\s+|additive\s+|alternative\s+|substitution\s+)?
        (?:bid\s+alternates?\b|alternate\b|alt\b|ve\s+item|ve\b|alternative\b)
    )
    # T10 F-4: allow a hyphen separator between the prefix word and
    # the id (e.g. ``ALT-A``, ``Alternate-3``, ``VE-1.2``). Without
    # this the regex required whitespace between the prefix and id,
    # missing a common shorthand seen on smaller bid forms.
    \s*[-]?\s*
    (?:no\.\s*|number\s*|num\s*|\#\s*|num\.\s*)?       # optional "No." / "#"
    (?P<id>[A-Z0-9]+(?:[-\.][A-Z0-9]+)?)               # 1 / 2 / A / B / 1A / VE-3
    \s*
    (?:\((?P<paren_label>[^)]+)\))?                    # optional "(DEDUCT)" or similar
    \s*
    [:\-—\.]?                                          # optional separator
    \s*
    (?P<body>.*)
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


# T10 F-4. CLIN-Option / FAR-52.217-5 evaluation-option pattern. Federal
# SF18 / SF1449 bid schedules (e.g. NPS PAIS Cabin RFQ) enumerate
# alternates as ``Option 001`` / ``Option 002`` lines inside the
# Price/Bid Schedule, without using the word "alternate" anywhere on
# the page. The id MUST start with a digit so narrative phrases like
# ``Option to extend the contract`` do not match (the alphabetic
# next-token would otherwise be captured as a phantom id).
_CLIN_OPTION_LINE_RE = re.compile(
    r"""
    ^\s*
    (?P<prefix>option)\b
    \s+
    (?:no\.\s*|number\s*|\#\s*)?                       # optional "No." / "#"
    (?P<id>\d{1,4}[A-Z0-9\-\.]*)                       # MUST start with a digit
    \s*
    (?:\((?P<paren_label>[^)]+)\))?                    # optional "(ADD)" / "(DEDUCT)"
    \s*
    [:\-—\.]?                                          # optional separator
    \s*
    (?P<body>.*)
    $
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _normalize_alternate_id(prefix: str, raw_id: str) -> str:
    """Produce a stable, human-friendly identifier from the regex captures.

    The dedupe key uses this normalized form so "Alt #1", "Alternate
    No. 1", and "Alternate 1" all collapse to the same key. VE / Bid
    Alternate / Add Alternate / Deduct Alternate / CLIN-Option
    prefixes are preserved (different alternate families with
    overlapping numeric ids — VE-1, Alternate #1, and Option 001 are
    each distinct items even when their raw id strings collide).
    """
    p = prefix.strip().lower()
    raw = raw_id.strip().upper()
    if "ve" in p:
        return f"VE-{raw}"
    if "bid alternate" in p:
        return f"Bid Alternate {raw}"
    if "add alternate" in p or "additive alternate" in p:
        return f"Add Alternate {raw}"
    if "deduct alternate" in p or "deductive alternate" in p:
        return f"Deduct Alternate {raw}"
    # T10 F-4: CLIN-Option pattern keeps its own family — "Option 001"
    # is semantically distinct from "Alternate 1" on the same form
    # (federal solicitations sometimes carry both shapes on adjacent
    # pages).
    if "option" in p:
        return f"Option {raw}"
    if "substitution" in p or "alternative" in p:
        return f"Alternate {raw}"
    return f"Alternate {raw}"


# Trailing "$_______ ADD" / "$_______ (DEDUCT)" labels that occasionally
# appear at the end of a bid-form line and need to be stripped from the
# description body before we use it for the scope summary.
# Single-letter ids and bare section-header / column-header tokens
# (e.g. "S" from "BID ALTERNATES SECTION", "PRICING" from "BID
# ALTERNATES PRICING", "BIDS" from "ALTERNATIVE BIDS") must not become
# alternate line items. T10 F-4 broadens the stopword list to cover
# additional header / column-header fragments surfaced by the
# RFCSP-style bundles in the v4 calibration corpus.
_ALT_ID_HEADER_STOPWORDS: frozenset[str] = frozenset(
    {
        "SECTION",
        "SCHEDULE",
        "FORM",
        "PAGE",
        "NOTE",
        "NOTES",
        "ITEM",
        "ITEMS",
        "ALTERNATE",
        "ALTERNATES",
        # T10 F-4 additions — header / column-header fragments from
        # Texas-State RFCSP and federal SF18/SF1449 bundles.
        "ALTERNATIVE",
        "ALTERNATIVES",
        "PRICING",
        "PRICE",
        "PROPOSAL",
        "PROPOSALS",
        "BID",
        "BIDS",
        "TABLE",
        "LIST",
        "REQUEST",
        "REQUESTS",
        "OPTION",
        "OPTIONS",
        "ADDITION",
        "ADDITIONS",
        "DEDUCTION",
        "DEDUCTIONS",
        "DESCRIPTION",
        "DESC",
        "AMOUNT",
        "AMOUNTS",
        "TOTAL",
        "TOTALS",
        "QUANTITY",
        "UNIT",
        "BIDDER",
        "OFFEROR",
        "RESPONDENT",
    }
)


def _is_valid_alternate_id_token(raw_id: str) -> bool:
    """Return True iff ``raw_id`` is a plausible alternate identifier.

    Accepts:

    * any token containing at least one digit (``"1"``, ``"01"``,
      ``"VE-3"``, ``"1A"``)
    * any single-letter alphabetic token (``"A"``, ``"B"``, ``"C"``)
    * any multi-character alphanumeric token that is NOT in the
      header / column-header stopword set
      (:data:`_ALT_ID_HEADER_STOPWORDS`)

    The stopword set is the B2-1 false-positive guard from QA Pair 25
    extended in T10 F-4 with additional column-header fragments that
    leaked through on RFCSP-style bundles ("PRICING", "BID", "OPTION",
    etc.). The guard rejects the literal "BID ALTERNATES SECTION"
    style headers so they don't synthesise phantom alternates, while
    keeping the genuinely valid letter-only ids ("Alt A", "Alternate
    One") flowing.
    """
    token = (raw_id or "").strip().upper()
    if not token:
        return False
    if token in _ALT_ID_HEADER_STOPWORDS:
        return False
    if any(ch.isdigit() for ch in token):
        return True
    # Single-letter ids (A, B, C) are common on bid forms.
    if len(token) == 1 and token.isalpha():
        return True
    return len(token) >= 2


_TRAIL_LABEL_RE = re.compile(
    r"""
    [\s\.\$_]+
    (?P<label>add|deduct|deductive|additive)
    \s*$
    """,
    re.IGNORECASE | re.VERBOSE,
)


def _confidence_for_parse(
    cost_delta: float | None,
    type_keyword_hit: bool,
    body_chars: int,
) -> float:
    """Heuristic confidence score for a deterministic alternate parse.

    The signal sources:

    * ``cost_delta`` resolved (printed number found, not blank) → +0.20
    * type keyword present in the body (ADD / DEDUCT / SUBSTITUTE /
      VE / etc.) → +0.10
    * body length ≥ 25 chars (real description, not noise) → +0.05

    Floor of 0.55 (above the AUTO_APPROVE threshold of 0.85 only when
    every signal fires) ensures even a low-signal regex hit isn't
    auto-approved without operator review.
    """
    score = 0.55
    if cost_delta is not None:
        score += 0.20
    if type_keyword_hit:
        score += 0.10
    if body_chars >= 25:
        score += 0.05
    return min(0.95, score)


def extract_alternates_from_page(
    page_text: str,
    *,
    bid_package_id: str | None = None,
    source_sheet: str | None = None,
) -> list[AlternateLine]:
    """Deterministic regex parse of a single page of bid-form text.

    Splits the page into lines, matches each line against
    :data:`_ALT_LINE_RE`, and emits one :class:`AlternateLine` per
    match. Sometimes a single alternate spans multiple lines (a long
    description wrapped across the page width) — the parser folds the
    NEXT line into the current alternate's body when the next line
    does NOT itself match :data:`_ALT_LINE_RE` and is non-empty.

    Returns an empty list when no lines match. A caller that has
    :func:`detect_alternates_section` returning True but gets an
    empty list back is exactly the trigger for the LLM fallback
    path — pass the same page through :func:`extract_alternates_via_llm`
    in :mod:`core.extractors` and merge via
    :func:`reconcile_alternate_sources`.
    """
    if not page_text:
        return []
    lines = page_text.splitlines()
    out: list[AlternateLine] = []
    i = 0
    while i < len(lines):
        line = lines[i].rstrip()
        # T10 F-4: try the canonical alternate regex first, then fall
        # back to the CLIN-Option regex for federal SF18/SF1449
        # solicitations that enumerate alternates as ``Option 001``.
        # `_ALT_LINE_RE` matches first when both could fire so the
        # canonical id family ("Alternate", "VE", "Add Alternate")
        # takes precedence over the CLIN-Option family.
        m = _ALT_LINE_RE.match(line) or _CLIN_OPTION_LINE_RE.match(line)
        if not m:
            i += 1
            continue
        prefix = m.group("prefix") or ""
        raw_id = m.group("id") or ""
        if not _is_valid_alternate_id_token(raw_id):
            i += 1
            continue
        paren_label = m.group("paren_label") or ""
        body = (m.group("body") or "").strip()

        # Fold continuation lines into the body until we hit a blank
        # line OR the next alternate header. Cap at 4 continuations so
        # a malformed page can't slurp the entire document.
        cont_count = 0
        j = i + 1
        while j < len(lines) and cont_count < 4:
            nxt = lines[j].rstrip()
            if not nxt.strip():
                break
            if _ALT_LINE_RE.match(nxt) or _CLIN_OPTION_LINE_RE.match(nxt):
                break
            body = f"{body} {nxt.strip()}".strip() if body else nxt.strip()
            cont_count += 1
            j += 1

        # Classify the type from the union of prefix + paren label + body —
        # bid forms put the ADD/DEDUCT label in any of those three slots.
        classify_input = " ".join(s for s in (prefix, paren_label, body) if s)
        atype = classify_alternate_type(classify_input)

        # Extract the printed dollar amount from the body, then strip the
        # trailing ADD / DEDUCT label so the scope_summary is clean.
        cost_raw = parse_cost_delta(body)
        cost_delta = _apply_type_sign(cost_raw, atype)
        cleaned_body = _TRAIL_LABEL_RE.sub("", body).rstrip(" .$_")

        if not cleaned_body:
            # Strictly a header / divider line ("Alternate #1 ...") with
            # no description content. Skip — we don't have a real
            # AlternateLine to emit and the next extractor pass (LLM)
            # will catch it if there's real content downstream.
            i = j
            continue

        type_keyword_hit = any(
            kw in classify_input.lower()
            for kw, *_ in (
                ("add",), ("deduct",), ("substitut",),
                ("value engineering",), ("ve item",),
                ("omit",), ("delete",), ("remove",),
            )
        )
        conf = _confidence_for_parse(
            cost_delta,
            type_keyword_hit,
            body_chars=len(cleaned_body),
        )

        alt_id = _normalize_alternate_id(prefix, raw_id)
        out.append(
            AlternateLine(
                alternate_id=alt_id,
                alternate_type=atype,
                description=cleaned_body,
                scope_summary=cleaned_body[:160] if len(cleaned_body) > 160 else cleaned_body,
                cost_delta=cost_delta,
                included_by_default=False,
                bid_package_id=bid_package_id,
                source_sheet=source_sheet,
                confidence=conf,
            )
        )
        i = j

    return out


def extract_alternates_from_pages(
    pages: Iterable[str],
    *,
    bid_package_id: str | None = None,
    source_sheet_template: str | None = None,
) -> list[AlternateLine]:
    """Run :func:`extract_alternates_from_page` across multiple pages.

    Convenience wrapper. ``source_sheet_template`` may contain a
    ``{page}`` placeholder which is substituted with the 1-based page
    number; useful for emitting traceable source references like
    ``"Bid Form p.3"`` when the caller knows the page numbering.
    """
    out: list[AlternateLine] = []
    for idx, page in enumerate(pages, start=1):
        if not page:
            continue
        if not detect_alternates_section(page):
            continue
        sheet = (
            source_sheet_template.format(page=idx)
            if source_sheet_template and "{page}" in source_sheet_template
            else source_sheet_template
        )
        out.extend(
            extract_alternates_from_page(
                page,
                bid_package_id=bid_package_id,
                source_sheet=sheet,
            )
        )
    return out


# ---------------------------------------------------------------------------
# Reconciliation: deterministic + LLM-fallback merge
# ---------------------------------------------------------------------------


def _normalize_id_for_dedupe(alternate_id: str) -> str:
    """Canonical form for cross-source dedupe.

    Lowercases, strips whitespace + punctuation, collapses internal
    spaces. ``"Alt #1"`` / ``"Alternate No. 1"`` / ``"Alternate 1"``
    all collapse to ``"alternate 1"``. ``"VE-3"`` / ``"VE 3"`` /
    ``"VE Item 3"`` all collapse to ``"ve 3"``.
    """
    if not alternate_id:
        return ""
    s = alternate_id.lower()
    # Collapse VE-family prefix variants
    s = re.sub(r"\bve\b[\s\-_\.]*item\b[\s\-_\.]*", "ve ", s)
    s = re.sub(r"\bve\b[\s\-_\.]+", "ve ", s)
    # Collapse alternate-family prefix variants
    s = re.sub(r"\balt(ernate)?\b[\s\-_\.]*(no\.?|number|num\.?|#)?[\s\-_\.]*", "alternate ", s)
    s = re.sub(r"\b(add|deduct(?:ive)?|additive|bid)\b[\s\-_\.]+alternate[\s\-_\.]+", "alternate ", s)
    # Collapse separators around the id
    s = re.sub(r"[\#\.\-_]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def _completeness_score(alt: AlternateLine) -> int:
    """Heuristic completeness score for choosing one alternate over another.

    Each populated field contributes 1 point; ``cost_delta`` weighs
    extra (2 points) because a numeric delta is the value an estimator
    actually wants. Used by :func:`reconcile_alternate_sources` to
    pick the "most-detailed" instance when the same alternate appears
    in both the deterministic and LLM-extracted lists.
    """
    score = 0
    if alt.description:
        score += 1
    if alt.scope_summary:
        score += 1
    if alt.cost_delta is not None:
        score += 2
    if alt.related_takeoff_items:
        score += 1
    if alt.related_csi:
        score += 1
    if alt.bid_package_id:
        score += 1
    if alt.source_sheet:
        score += 1
    return score


def reconcile_alternate_sources(
    deterministic: list[AlternateLine],
    llm_extracted: list[AlternateLine],
) -> list[AlternateLine]:
    """Merge deterministic + LLM-extracted alternates, preferring the higher-completeness record.

    Dedupe key is :func:`_normalize_id_for_dedupe` over
    ``alternate_id``. When both lists contain the same key, the
    record with the higher :func:`_completeness_score` wins; ties
    favour the deterministic record (which by construction has
    confidence ≥ 0.55).

    Records present in only one list pass through untouched.

    The return order preserves the deterministic list's ordering
    first, then appends LLM-only records, so a stable downstream
    reading order is preserved across runs.
    """
    out: list[AlternateLine] = []
    seen: dict[str, int] = {}  # normalized id -> index in out

    for alt in deterministic:
        key = _normalize_id_for_dedupe(alt.alternate_id)
        if key in seen:
            # Two deterministic records with the same id — keep the
            # higher-completeness one (rare; would mean the page had
            # a typo where the same line appeared twice).
            existing_idx = seen[key]
            if _completeness_score(alt) > _completeness_score(out[existing_idx]):
                out[existing_idx] = alt
            continue
        seen[key] = len(out)
        out.append(alt)

    for alt in llm_extracted:
        key = _normalize_id_for_dedupe(alt.alternate_id)
        if key in seen:
            existing_idx = seen[key]
            if _completeness_score(alt) > _completeness_score(out[existing_idx]):
                out[existing_idx] = alt
            continue
        seen[key] = len(out)
        out.append(alt)

    return out


def should_invoke_llm_fallback(
    page_text: str,
    deterministic_result: list[AlternateLine],
) -> bool:
    """Return True if the caller should run the LLM fallback for this page.

    Contract per the T9.0 brief: LLM fallback fires when the
    deterministic parser returned zero alternates AND the page
    detection said yes. This helper centralises the predicate so
    callers don't reimplement the boolean themselves and so the
    contract is unit-testable.
    """
    if deterministic_result:
        return False
    return detect_alternates_section(page_text)


# ---------------------------------------------------------------------------
# BidPackage helpers
# ---------------------------------------------------------------------------


def alternates_from_bid_package_legacy(
    legacy_alternates: list,
    *,
    bid_package_id: str | None = None,
    source_sheet: str | None = None,
) -> list[AlternateLine]:
    """Convert the legacy :class:`core.schemas.Alternate` records to the new shape.

    The pre-T9.0 :class:`Alternate` records carry just ``number``,
    ``description``, ``add_or_deduct``, and ``amount``. T9.0's
    :class:`AlternateLine` is the priceable shape — when the
    extraction pipeline only managed to emit legacy records (e.g. an
    older fixture or a bid form whose alternates section the new
    extractor missed but the broader bid_package prompt caught), this
    helper bridges them so the alternates rollup still shows them.

    Behaviour:

    * Number → ``alternate_id`` (with a "Alternate " prefix when bare).
    * ``add_or_deduct`` → ``alternate_type`` (ADD → ADDITIVE,
      DEDUCT → DEDUCTIVE, else ADDITIVE as the dominant default).
    * ``amount`` → ``cost_delta`` with the type-sign convention applied.
    * ``confidence=0.65`` — slightly below the deterministic-regex
      confidence floor because the legacy shape carries less context
      than the new extractor.
    """
    out: list[AlternateLine] = []
    for a in legacy_alternates:
        desc = getattr(a, "description", None) or ""
        if not desc.strip():
            continue
        raw_id = (getattr(a, "number", None) or "").strip() or f"({len(out) + 1})"
        if not raw_id.lower().startswith(("alt", "ve", "bid alternate", "add alternate", "deduct alternate")):
            alt_id = f"Alternate {raw_id}".replace("#", "").strip()
        else:
            alt_id = raw_id
        label = (getattr(a, "add_or_deduct", None) or "").lower()
        if "deduct" in label:
            atype = AlternateType.DEDUCTIVE
        elif "add" in label:
            atype = AlternateType.ADDITIVE
        else:
            atype = classify_alternate_type(desc)
        raw_amount = getattr(a, "amount", None)
        cost_delta = _apply_type_sign(
            float(raw_amount) if raw_amount is not None else None,
            atype,
        )
        out.append(
            AlternateLine(
                alternate_id=alt_id,
                alternate_type=atype,
                description=desc.strip(),
                scope_summary=desc.strip()[:160] if len(desc.strip()) > 160 else desc.strip(),
                cost_delta=cost_delta,
                included_by_default=False,
                bid_package_id=bid_package_id,
                source_sheet=source_sheet,
                confidence=0.65,
            )
        )
    return out
