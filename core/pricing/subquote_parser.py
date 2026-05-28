"""Phase T8.1 + T8.2 — sub-quote PDF ingestion.

Subs (mechanical, electrical, plumbing, glass, drywall, etc.) commonly
deliver priced sub-quotes as PDF documents. This module covers both
ingestion paths:

* **T8.1 — tabular path** (:func:`parse_subquote_pdf`). Deterministic
  PyMuPDF table extraction; no LLM call, fully reproducible.
* **T8.2 — LLM-vision fallback** (:func:`parse_subquote_pdf_with_llm`).
  Renders each page to PNG, sends through the project's vision LLM
  (``core.llm_client.LLMClient``), parses the structured JSON response.
  Use when T8.1 raises :class:`SubquoteParseError` — i.e. on scanned
  image-only PDFs and free-form letter-style quotes that have no
  deterministic table structure.

Both paths return the same :class:`SubquoteParseResult` shape — a
``list[BatchOverrideRow]`` plus a :class:`SubquoteMetadata` blob and
warnings — so the downstream
:func:`~core.pricing.batch_override.match_cost_lines` and
:func:`~core.pricing.batch_override.apply_batch_plan` pipeline can
consume the output unchanged regardless of which ingestion path
produced it. The only caller-visible difference between the two paths
is the ``source_tag`` the Streamlit UI passes to
:func:`~core.pricing.batch_override.format_batch_operator_note` —
``"[sub-quote]"`` for the deterministic T8.1 path,
``"[sub-quote-llm]"`` for the LLM-vision T8.2 path — so the audit
trail records the provenance distinctly.

Architecture (T8.1 — tabular)::

    PDF bytes
       │
       ▼
    fitz.open(stream=…, filetype="pdf")    ← PyMuPDF (already a project dep)
       │
       ▼
    per-page page.find_tables()            ← native PyMuPDF table detection
       │
       ▼
    header detection (column-alias map shared with T6.3 CSV parser)
       │
       ▼
    row parsing + normalisation
       │
       ▼
    list[BatchOverrideRow]                 ← same shape as the CSV parser

Architecture (T8.2 — LLM-vision fallback)::

    PDF bytes
       │
       ▼
    fitz Page.get_pixmap(matrix=DPI)       ← render to PNG (in-memory)
       │
       ▼
    per-page LLMClient.analyze_image()     ← vision model + JSON-only prompt
       │
       ▼
    JSON response → schema validation
       │
       ▼
    list[BatchOverrideRow]                 ← same shape as the CSV parser

Public surface:

* :class:`SubquoteParseError`     — recoverable + non-recoverable failures.
* :class:`SubquoteLLMError`       — subclass; raised from the T8.2 path
  when the LLM call or its JSON response fails.
* :class:`SubquoteMetadata`       — optional vendor / quote-# / date /
  total scraped from page text (regex-only on the T8.1 path; from the
  vision-LLM JSON on the T8.2 path).
* :class:`SubquoteParseResult`    — combined ``(rows, metadata, warnings)``.
* :func:`parse_subquote_pdf`      — T8.1 entry point; bytes in, result out.
* :func:`parse_subquote_pdf_with_llm` — T8.2 entry point; bytes in,
  result out via vision LLM.

The T8.1 parser is intentionally **conservative**: when header
detection is ambiguous we raise rather than silently emit garbage rows
that would then misroute through the fuzzy matcher and quietly mangle
the estimate. The T8.2 parser is the same shape — bad rows are dropped
with warnings, not silently corrected.

No new third-party dependencies — uses ``fitz`` (PyMuPDF, already in
``requirements.txt`` for the drawing PDF processor), the existing
:class:`core.llm_client.LLMClient`, and stdlib only.
"""

from __future__ import annotations

import io
import json
import logging
import os
import re
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

import fitz

from core.pricing.batch_override import (
    _COLUMN_ALIASES,
    BatchOverrideRow,
)

if TYPE_CHECKING:  # pragma: no cover — typing only
    from core.llm_client import LLMClient


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Exceptions + result types
# ---------------------------------------------------------------------------


class SubquoteParseError(Exception):
    """Raised when the PDF can't be parsed deterministically into rows.

    Recoverable cases (these are T8.2 — LLM-vision fallback — territory,
    handled by :func:`parse_subquote_pdf_with_llm`):

    * PDF is a scanned image (no extractable text layer).
    * PDF has text but no detectable table structure (free-form layout).
    * PDF has tables but no recognisable column header.

    Non-recoverable cases (the operator must fix the source):

    * Encrypted PDF.
    * Corrupted / unreadable PDF.
    * Empty / zero-page PDF.

    The exception message always includes a one-line operator hint
    ("convert to CSV", "remove encryption", etc.) so the Streamlit UI
    can pass it straight to ``st.error`` without re-formatting.
    """


class SubquoteLLMError(SubquoteParseError):
    """Raised by :func:`parse_subquote_pdf_with_llm` on LLM-path failures.

    Subclass of :class:`SubquoteParseError` so a UI handler can keep a
    single ``except SubquoteParseError`` block when neither path matters
    in detail. Raised when:

    * The PDF can't be rendered to PNGs (corrupted / encrypted / empty —
      same triggers :func:`parse_subquote_pdf` raises on, but surfaced
      under the LLM-path exception type so the UI can disambiguate).
    * The LLM returns malformed JSON for every page even after the
      single repair-attempt the underlying client performs.
    * The LLM client raises any non-recoverable exception (auth error,
      persistent 5xx, retry budget exhausted) that bubbles past the
      retry loop in :class:`core.llm_client.LLMClient`.

    Like its parent, the message text is operator-facing — the UI can
    surface it verbatim via ``st.error(str(exc))``.
    """


@dataclass
class SubquoteMetadata:
    """Optional metadata scraped from the PDF's pre-table text.

    All fields are best-effort and optional. Regex-only extraction
    (no LLM call) so behaviour is deterministic across runs and
    cheap to test. ``confidence`` is a 0-1 scalar indicating how many
    of the metadata slots were filled (1.0 = every slot found, 0.0 =
    no slots matched).
    """

    vendor_name: str | None = None
    quote_number: str | None = None
    quote_date: str | None = None
    project_reference: str | None = None
    total_quoted: float | None = None
    detected_pages: list[int] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class SubquoteParseResult:
    """Combined output of :func:`parse_subquote_pdf`.

    * ``rows``     — successfully parsed :class:`BatchOverrideRow`
                      records, ready for
                      :func:`~core.pricing.batch_override.match_cost_lines`.
    * ``metadata`` — best-effort vendor / quote-number / date / total.
    * ``warnings`` — human-readable per-row warnings (skipped rows,
                      computed unit costs, etc.) for the UI to surface.
    """

    rows: list[BatchOverrideRow]
    metadata: SubquoteMetadata
    warnings: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


# A row whose description contains any of these tokens is treated as a
# subtotal / tax / total summary line and skipped. Match is
# case-insensitive on the normalised description (whitespace-collapsed,
# lowercase). The tokens are anchored as standalone words so a legit
# line like "Total replacement of subfloor" still parses.
_SUBTOTAL_TOKENS: tuple[str, ...] = (
    "subtotal",
    "sub total",
    "sub-total",
    "grand total",
    "total",
    "tax",
    "sales tax",
    "shipping",
    "freight",
    "handling",
)


# Metadata extraction regexes. Compiled once at import time; each
# regex captures one named slot. All are deliberately loose — the
# parser treats every metadata slot as best-effort.
_QUOTE_NUMBER_RE = re.compile(
    r"\b(?:quote|quotation|estimate|proposal|bid)\s*(?:no\.?|number|#|num\.?)?\s*[:\-]?\s*([A-Z0-9][\w\-/]{1,30})",
    re.IGNORECASE,
)

_VENDOR_PREFIX_RE = re.compile(
    r"\b(?:from|vendor|supplier|company|prepared by|quoted by)\s*[:\-]\s*([A-Z][A-Za-z0-9 &.,'\-]{2,80})",
    re.IGNORECASE,
)

_DATE_RE = re.compile(
    r"\b(?:date|dated|quote date)\s*[:\-]\s*([0-9]{1,4}[\-/.][0-9]{1,2}[\-/.][0-9]{1,4})",
    re.IGNORECASE,
)

_PROJECT_REF_RE = re.compile(
    r"\b(?:project|re|ref|reference|job)\s*[:\-]\s*([A-Z0-9][\w\- ,]{2,80})",
    re.IGNORECASE,
)

_TOTAL_RE = re.compile(
    r"\b(?:grand total|total)\s*[:\-]?\s*\$?\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)",
    re.IGNORECASE,
)


# Header-keyword set: cells whose normalised text matches one of these
# tokens get treated as a column header. Mirrors ``_COLUMN_ALIASES`` so
# both the CSV and PDF parsers honour the same canonical column names.
def _build_header_keyword_set() -> set[str]:
    """Flatten ``_COLUMN_ALIASES`` into one lowercase keyword set.

    Used by :func:`_detect_header_row` to score candidate header rows.
    Underscores in aliases are stripped so "unit_cost" matches a PDF
    cell rendered as "Unit Cost" or "unit cost".
    """
    out: set[str] = set()
    for aliases in _COLUMN_ALIASES.values():
        for alias in aliases:
            out.add(alias.lower())
            out.add(alias.lower().replace("_", " "))
            out.add(alias.lower().replace("_", ""))
    return out


_HEADER_KEYWORDS: set[str] = _build_header_keyword_set()


# Minimum number of recognised header tokens in a candidate header row.
# Two is conservative — a row with just one keyword (e.g. only
# "Description") is more likely a section heading than a real table
# header. Two keywords (e.g. "Description" + "Qty") rules out almost
# every false positive in the calibration set.
_MIN_HEADER_TOKENS: int = 2


# Maximum number of pages scanned for metadata. Vendor PDFs put
# header / letterhead text on page 1; scanning beyond saves nothing
# and adds noise. Cap is generous so a quote-summary on page 2 still
# gets picked up.
_METADATA_SCAN_PAGES: int = 3


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------


def _normalise_cell(text: str | None) -> str:
    """Collapse whitespace + strip the cell. Returns ``""`` on ``None``.

    Used both for header-keyword matching (where we lowercase further
    downstream) and for description fields (which preserve case for
    display). The CSV parser does NOT need this because ``csv.DictReader``
    has already split on commas — sub-quote tables come straight from
    PyMuPDF as Python strings with embedded newlines + extra spaces.
    """
    if text is None:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def _parse_number(raw: str | None) -> float | None:
    """Best-effort numeric parse — tolerates ``$``, commas, units.

    Returns ``None`` when no number can be extracted. Strips the most
    common decorations:

    * Currency symbol (``$``)
    * Thousands separator (``,``)
    * Trailing unit codes (``EA``, ``LF``, ``SF``, ``CY``, …) when
      preceded by whitespace.

    Negative values are returned as-is; the caller is responsible for
    the non-negative check.
    """
    if raw is None:
        return None
    s = _normalise_cell(raw)
    if not s:
        return None
    # Strip dollar sign and thousands separators.
    s = s.replace("$", "").replace(",", "").strip()
    # Drop a trailing unit suffix like "100 EA" or "12.5 LF" — split
    # off the leading number and discard the rest.
    m = re.match(r"^([\-+]?\d+(?:\.\d+)?)", s)
    if m:
        try:
            return float(m.group(1))
        except (TypeError, ValueError):
            return None
    return None


def _is_subtotal_row(desc: str) -> bool:
    """Return True if ``desc`` looks like a subtotal / tax / total line.

    Match is **conservative** — we only skip rows whose description is
    *clearly* a summary, not a legitimate line item that incidentally
    contains a summary word. Specifically:

    1. The exact normalised description (lowercase, punctuation
       stripped, whitespace collapsed) equals a token in
       :data:`_SUBTOTAL_TOKENS`. So ``"Subtotal"`` / ``"Sub-Total:"``
       / ``"GRAND TOTAL"`` all flag, but ``"Subfloor underlayment"``
       (3 words, none of them a token) does not.
    2. The normalised description starts with a token + ``:`` or ``=``
       (e.g. ``"Total: 12,345"`` / ``"Subtotal = $5,000"``).

    This rules out false positives like ``"Tax-exempt purchasing"``
    (becomes ``"tax exempt purchasing"`` after normalisation — 3 words,
    no clean equality, no trailing colon).
    """
    if not desc:
        return False
    # Replace punctuation EXCEPT colon / equals with space — those two
    # serve as summary-row separators ("Total: $X" / "Subtotal = $X").
    cleaned = re.sub(r"[^\w\s:=]+", " ", desc.lower())
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    if not cleaned:
        return False
    # Strip a trailing colon / equals BEFORE the exact-match check so
    # "Subtotal:" matches "subtotal".
    stripped = cleaned.rstrip(":= ").strip()
    for token in _SUBTOTAL_TOKENS:
        if stripped == token:
            return True
        # "<token>: ..." or "<token> = ..." pattern.
        if cleaned.startswith(token + ":") or cleaned.startswith(token + " :"):
            return True
        if cleaned.startswith(token + " ="):
            return True
    return False


# ---------------------------------------------------------------------------
# Header + table detection
# ---------------------------------------------------------------------------


def _detect_header_row(rows: list[list[str | None]]) -> int | None:
    """Find the index of the row that looks like a table header.

    Walks the first ~5 rows of the table and counts how many cells
    match a header keyword in :data:`_HEADER_KEYWORDS` (case-insensitive,
    underscore-tolerant). The first row with at least
    :data:`_MIN_HEADER_TOKENS` keyword hits wins.

    Returns the 0-based row index, or ``None`` if no header could be
    detected. The caller should skip the table entirely on ``None``.
    """
    scan_limit = min(5, len(rows))
    for row_idx in range(scan_limit):
        hits = 0
        for cell in rows[row_idx]:
            normalised = _normalise_cell(cell).lower()
            if not normalised:
                continue
            # Try the raw cell first, then with underscores in case the
            # vendor PDF rendered "unit_cost" verbatim.
            candidates = (
                normalised,
                normalised.replace(" ", "_"),
                normalised.replace(" ", ""),
            )
            for cand in candidates:
                if cand in _HEADER_KEYWORDS:
                    hits += 1
                    break
        if hits >= _MIN_HEADER_TOKENS:
            return row_idx
    return None


def _resolve_column_map(header_row: list[str | None]) -> dict[str, int]:
    """Map our canonical slot names → the cell-index in this header row.

    Mirrors :func:`core.pricing.batch_override._resolve_column_map` but
    returns column *indices* (PDF tables are positional, unlike a CSV
    dict). Missing optional slots are simply omitted from the result.
    """
    normalised: dict[str, int] = {}
    for col_idx, cell in enumerate(header_row):
        text = _normalise_cell(cell).lower()
        if not text:
            continue
        # Index every variant the cell could match.
        for variant in (text, text.replace(" ", "_"), text.replace(" ", "")):
            if variant not in normalised:
                normalised[variant] = col_idx

    out: dict[str, int] = {}
    for slot, aliases in _COLUMN_ALIASES.items():
        for alias in aliases:
            for variant in (
                alias.lower(),
                alias.lower().replace("_", " "),
                alias.lower().replace("_", ""),
            ):
                if variant in normalised:
                    out[slot] = normalised[variant]
                    break
            if slot in out:
                break
    return out


# ---------------------------------------------------------------------------
# Metadata extraction
# ---------------------------------------------------------------------------


def _extract_metadata(text: str) -> SubquoteMetadata:
    """Scrape vendor / quote-# / date / total from the PDF's pre-table text.

    Pure regex (see module-level ``_*_RE`` constants). Every slot is
    best-effort — a missing match leaves the slot ``None``. ``confidence``
    is the proportion of slots filled (4 slots total + ``total_quoted``).
    """
    md = SubquoteMetadata()
    if not text:
        return md

    m = _QUOTE_NUMBER_RE.search(text)
    if m:
        md.quote_number = m.group(1).strip()

    m = _VENDOR_PREFIX_RE.search(text)
    if m:
        candidate = m.group(1).strip()
        # Trim at the next newline — the regex's character class
        # accepts spaces but the vendor name typically ends at EOL.
        candidate = candidate.split("\n", 1)[0].strip()
        if candidate:
            md.vendor_name = candidate

    m = _DATE_RE.search(text)
    if m:
        md.quote_date = m.group(1).strip()

    m = _PROJECT_REF_RE.search(text)
    if m:
        md.project_reference = m.group(1).split("\n", 1)[0].strip()

    # ``total`` is the last numeric "Total: $X" occurrence in the
    # pre-table text — vendor letterheads sometimes contain the word
    # "total" in boilerplate copy, so we keep the LAST match.
    matches = list(_TOTAL_RE.finditer(text))
    if matches:
        val = _parse_number(matches[-1].group(1))
        if val is not None:
            md.total_quoted = val

    filled = sum(
        1
        for slot in (
            md.vendor_name,
            md.quote_number,
            md.quote_date,
            md.project_reference,
            md.total_quoted,
        )
        if slot
    )
    md.confidence = round(filled / 5.0, 2)
    return md


# ---------------------------------------------------------------------------
# Row parsing
# ---------------------------------------------------------------------------


def _parse_table_rows(
    table_rows: list[list[str | None]],
    column_map: dict[str, int],
    header_idx: int,
    next_row_index: int,
) -> tuple[list[BatchOverrideRow], list[str], int]:
    """Parse rows below the header into :class:`BatchOverrideRow` records.

    Returns ``(rows, warnings, next_row_index)``. ``next_row_index`` is
    monotonically incremented across calls (the caller threads it
    through multi-table / multi-page tables) so every emitted row gets
    a stable global index for the audit trail.

    Per-row skip + warning rules (mirror the CSV parser):

    * Empty description → skipped (warning emitted).
    * Subtotal / tax / total row → skipped (no warning — expected).
    * Negative unit cost → skipped (warning).
    * Missing unit cost AND missing extended → skipped (warning).

    When the ``unit_cost`` column is missing but ``extended`` + ``quantity``
    are present, ``unit_cost`` is computed as ``extended / quantity``
    (warning emitted noting the derivation).
    """
    out: list[BatchOverrideRow] = []
    warnings: list[str] = []
    row_index = next_row_index

    desc_col = column_map.get("description")
    unit_col = column_map.get("unit_cost")
    qty_col = column_map.get("quantity")
    ext_col = column_map.get("extended")
    vendor_col = column_map.get("vendor")
    quote_col = column_map.get("quote_ref")
    notes_col = column_map.get("notes")

    if desc_col is None:
        # No description column — the table is unparseable. The caller
        # should have raised SubquoteParseError before reaching here,
        # but the guard is cheap and prevents a confusing IndexError.
        return [], ["Table has no description column; skipped."], row_index

    for data_row in table_rows[header_idx + 1:]:
        row_index += 1

        if desc_col >= len(data_row):
            warnings.append(
                f"Row {row_index}: cell index out of range; skipped."
            )
            continue
        desc = _normalise_cell(data_row[desc_col])
        if not desc:
            warnings.append(f"Row {row_index}: empty description; skipped.")
            continue
        if _is_subtotal_row(desc):
            # Silent skip — subtotal / total rows are expected.
            continue

        qty: float | None = None
        if qty_col is not None and qty_col < len(data_row):
            qty = _parse_number(data_row[qty_col])
            if qty is not None and qty < 0:
                qty = None

        unit_cost: float | None = None
        if unit_col is not None and unit_col < len(data_row):
            unit_cost = _parse_number(data_row[unit_col])

        if unit_cost is None and ext_col is not None and ext_col < len(data_row):
            extended = _parse_number(data_row[ext_col])
            if extended is not None and qty is not None and qty > 0:
                unit_cost = round(extended / qty, 4)
                warnings.append(
                    f"Row {row_index}: unit_cost derived from "
                    f"extended/qty = {extended}/{qty} = "
                    f"${unit_cost:.4f}."
                )
            elif extended is not None and (qty is None or qty == 0):
                warnings.append(
                    f"Row {row_index}: extended {extended} present but "
                    f"qty is missing/zero; cannot derive unit_cost; "
                    f"skipped."
                )
                continue

        if unit_cost is None:
            warnings.append(
                f"Row {row_index}: no unit_cost or derivable "
                f"extended/qty; skipped."
            )
            continue
        if unit_cost < 0:
            warnings.append(
                f"Row {row_index}: negative unit_cost {unit_cost}; skipped."
            )
            continue

        vendor = None
        if vendor_col is not None and vendor_col < len(data_row):
            v = _normalise_cell(data_row[vendor_col])
            vendor = v or None

        quote_ref = None
        if quote_col is not None and quote_col < len(data_row):
            q = _normalise_cell(data_row[quote_col])
            quote_ref = q or None

        notes = None
        if notes_col is not None and notes_col < len(data_row):
            n = _normalise_cell(data_row[notes_col])
            notes = n or None

        out.append(BatchOverrideRow(
            row_index=row_index,
            description=desc,
            unit_cost=unit_cost,
            vendor=vendor,
            quote_ref=quote_ref,
            notes=notes,
            quantity=qty,
        ))

    return out, warnings, row_index


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def parse_subquote_pdf(pdf_bytes: bytes) -> SubquoteParseResult:
    """Parse a tabular vendor sub-quote PDF.

    Pipeline:

    1. Open the PDF via :func:`fitz.open` with ``stream`` mode (no
       filesystem touch).
    2. Reject encrypted / corrupted / empty PDFs with
       :class:`SubquoteParseError`.
    3. For each page: call ``page.find_tables()`` (PyMuPDF's native
       table detector) to get candidate tables.
    4. For each table: detect the header row via
       :func:`_detect_header_row`, resolve the column map via
       :func:`_resolve_column_map`, then parse the data rows via
       :func:`_parse_table_rows`.
    5. Extract metadata from the first ``_METADATA_SCAN_PAGES`` pages
       of text via :func:`_extract_metadata`.
    6. Raise :class:`SubquoteParseError` if NO tables produced rows
       AND the PDF is text-bearing (free-form quote) OR scanned (no
       text layer).
    7. Otherwise return a :class:`SubquoteParseResult` with every
       parsed row.

    Args:
        pdf_bytes: Raw PDF bytes (e.g. from a Streamlit ``file_uploader``).

    Returns:
        A :class:`SubquoteParseResult` with the parsed rows + metadata.

    Raises:
        SubquoteParseError: When the PDF can't be parsed deterministically.
    """
    if not pdf_bytes:
        raise SubquoteParseError(
            "PDF is empty (0 bytes). Re-export the sub-quote and re-upload."
        )

    try:
        doc = fitz.open(stream=io.BytesIO(pdf_bytes).getvalue(), filetype="pdf")
    except Exception as exc:
        raise SubquoteParseError(
            f"Could not open PDF (corrupted or unsupported format): {exc}. "
            f"Re-export the sub-quote and re-upload."
        ) from exc

    try:
        if doc.is_encrypted:
            raise SubquoteParseError(
                "PDF is encrypted / password-protected. Remove encryption "
                "in Acrobat (File → Properties → Security) and re-upload."
            )
        if len(doc) == 0:
            raise SubquoteParseError(
                "PDF has zero pages. Re-export the sub-quote and re-upload."
            )

        # ----- Metadata scrape from the first few pages -----
        metadata_text = ""
        for i in range(min(_METADATA_SCAN_PAGES, len(doc))):
            try:
                metadata_text += "\n" + (doc[i].get_text("text") or "")
            except Exception:
                continue
        metadata = _extract_metadata(metadata_text)

        # ----- Table-by-table parse -----
        rows: list[BatchOverrideRow] = []
        warnings: list[str] = []
        detected_pages: list[int] = []
        running_row_index = 1  # 1-indexed; 1 is reserved (mirrors CSV row 1 = header)
        total_tables = 0
        any_text = False

        for page_idx in range(len(doc)):
            page = doc[page_idx]
            try:
                page_text = page.get_text("text") or ""
            except Exception:
                page_text = ""
            if page_text.strip():
                any_text = True

            try:
                table_finder = page.find_tables()
                page_tables = list(table_finder.tables)
            except Exception:
                page_tables = []

            for tbl in page_tables:
                try:
                    extracted = tbl.extract()
                except Exception:
                    continue
                if not extracted:
                    continue
                total_tables += 1

                header_idx = _detect_header_row(extracted)
                if header_idx is None:
                    continue
                column_map = _resolve_column_map(extracted[header_idx])
                if "description" not in column_map:
                    continue
                if "unit_cost" not in column_map and "extended" not in column_map:
                    continue

                page_rows, page_warnings, running_row_index = _parse_table_rows(
                    extracted,
                    column_map,
                    header_idx,
                    running_row_index,
                )
                if page_rows:
                    detected_pages.append(page_idx + 1)
                rows.extend(page_rows)
                warnings.extend(page_warnings)

        metadata.detected_pages = sorted(set(detected_pages))

        if not rows:
            # Three failure shapes:
            #   1. No text at all → scanned PDF (T8.2 territory).
            #   2. Text present but no detectable tables.
            #   3. Tables present but no recognised header.
            # All three deliver the same operator-facing message; the
            # exception type signals "not for T8.1; try CSV or wait for T8.2".
            if not any_text:
                raise SubquoteParseError(
                    "PDF appears to be a scanned image (no extractable "
                    "text layer). T8.2 LLM-vision fallback will handle "
                    "this; for now, convert the quote to CSV (see Vendor "
                    "CSV uploader above) and re-upload."
                )
            if total_tables == 0:
                raise SubquoteParseError(
                    "PDF has text but no detectable tables (likely a "
                    "free-form / letter-style quote). T8.2 LLM-vision "
                    "fallback will handle this; for now, convert to CSV "
                    "(see Vendor CSV uploader above) and re-upload."
                )
            raise SubquoteParseError(
                "PDF contains tables but none have a recognisable column "
                "header (expected at least 'description' + one of "
                "'unit_cost' / 'unit_price' / 'extended'). Check the "
                "column titles and re-upload, or convert to CSV."
            )

        return SubquoteParseResult(
            rows=rows,
            metadata=metadata,
            warnings=warnings,
        )
    finally:
        doc.close()


# ---------------------------------------------------------------------------
# Phase T8.2 — LLM-vision fallback
# ---------------------------------------------------------------------------
#
# When :func:`parse_subquote_pdf` raises :class:`SubquoteParseError` the
# operator is offered a second-chance "Try LLM extraction" button that
# routes through :func:`parse_subquote_pdf_with_llm`. This path renders
# each PDF page to a PNG and feeds it to the project's standard vision
# LLM (``core.llm_client.LLMClient``), which is already used by
# ``core.extractors.extract_sheet`` for drawing-page extraction — so
# the vendor / model / retry policy / cost profile is identical.
#
# The output type is :class:`SubquoteParseResult` — the same shape T8.1
# emits — so the downstream ``match_cost_lines`` + ``apply_batch_plan``
# pipeline runs unchanged. The only caller-visible difference is the
# ``source_tag="[sub-quote-llm]"`` flag the Streamlit UI passes to
# ``format_batch_operator_note``, which lands in ``override_history``
# rows so an auditor can grep PDF-table parses (``[sub-quote]``) vs
# LLM-vision parses (``[sub-quote-llm]``) at a glance.

# Maximum pages rendered + sent to the LLM. Sub-quote PDFs are
# typically 1-3 pages; the cap defends against accidentally feeding
# a 50-page document and burning operator $$$ on a misclick.
_LLM_DEFAULT_MAX_PAGES: int = 10

# Default render DPI. 200 is the sweet spot for vision LLMs in 2026
# Q2: clear text recognition at a reasonable token cost (Anthropic
# bills ~1.59 tokens / pixel; 200 DPI on US Letter is ~1.7 MP per
# page, ~2.7k tokens — well under both providers' input limits).
# Lift to 300 for dense numerical content if accuracy drops in
# calibration; 200 is the verified-working default.
_LLM_DEFAULT_DPI: int = 200

# Per-page notes-field cap. Mirrors the prompt's instruction so a
# misbehaving model that emits a multi-paragraph note can't blow up
# the operator-history CSV cell. Trim is silent (the model is
# already instructed to cap at 100; we only enforce as a safety net).
_LLM_NOTES_MAX_CHARS: int = 100


# System prompt used for every per-page LLM call. Pinned to JSON-only
# output. The full extraction-rule prompt lives in
# ``prompts/subquote_vision.txt`` and is loaded as the user prompt.
_LLM_SYSTEM_PROMPT: str = (
    "You are a vision-extraction estimator. You read one rendered page "
    "of a vendor sub-quote PDF and emit a single JSON object with the "
    "schema described in the user prompt. Output ONLY the JSON object — "
    "no commentary, no markdown fences, no explanation."
)


def _load_subquote_vision_prompt() -> str:
    """Load the user prompt for the vision LLM call.

    Reads ``prompts/subquote_vision.txt`` from the repo root. Cached
    after first load — the prompt is constant across calls in a single
    process. Pure I/O helper, no LLM dependency.
    """
    if _load_subquote_vision_prompt._cache is None:  # type: ignore[attr-defined]
        # ``__file__`` is core/pricing/subquote_parser.py; up two parents
        # is the repo root, then ``prompts/subquote_vision.txt``.
        prompt_path = (
            Path(__file__).resolve().parent.parent.parent
            / "prompts"
            / "subquote_vision.txt"
        )
        _load_subquote_vision_prompt._cache = prompt_path.read_text(  # type: ignore[attr-defined]
            encoding="utf-8"
        )
    return _load_subquote_vision_prompt._cache  # type: ignore[attr-defined]


_load_subquote_vision_prompt._cache = None  # type: ignore[attr-defined]


def _render_pdf_pages_to_png(
    pdf_bytes: bytes,
    max_pages: int = _LLM_DEFAULT_MAX_PAGES,
    dpi: int = _LLM_DEFAULT_DPI,
) -> list[bytes]:
    """Render the first ``max_pages`` pages of a PDF to PNG bytes.

    Pure helper — no LLM, no network. Accepts the same PDF bytes
    :func:`parse_subquote_pdf` does, returns a list of PNG byte
    strings (one per page, in document order). Mirrors the
    rendering pattern from
    :mod:`core.extraction.drawing_prepass`: a 72-DPI base scaled by
    ``dpi/72`` via :class:`fitz.Matrix`.

    Raises:
        SubquoteLLMError: When the PDF is empty / corrupted / encrypted
            / zero-page. Mirrors :func:`parse_subquote_pdf`'s pre-flight
            checks but raises under the LLM-path exception type so the
            UI can disambiguate which entry point failed.
    """
    if max_pages < 1:
        raise SubquoteLLMError(
            f"max_pages must be >= 1; got {max_pages}."
        )
    if dpi < 36 or dpi > 600:
        # 36 DPI is the floor where text is still legible to the model;
        # 600 is the ceiling before token cost spirals. Calibrated.
        raise SubquoteLLMError(
            f"dpi must be in [36, 600]; got {dpi}."
        )
    if not pdf_bytes:
        raise SubquoteLLMError(
            "PDF is empty (0 bytes). Re-export the sub-quote and re-upload."
        )

    try:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    except Exception as exc:
        raise SubquoteLLMError(
            f"Could not open PDF for LLM extraction "
            f"(corrupted or unsupported format): {exc}. Re-export the "
            f"sub-quote and re-upload."
        ) from exc

    try:
        if doc.is_encrypted:
            raise SubquoteLLMError(
                "PDF is encrypted / password-protected. Remove encryption "
                "in Acrobat (File \u2192 Properties \u2192 Security) "
                "and re-upload."
            )
        if len(doc) == 0:
            raise SubquoteLLMError(
                "PDF has zero pages. Re-export the sub-quote and re-upload."
            )

        page_count = min(max_pages, len(doc))
        scale = float(dpi) / 72.0
        matrix = fitz.Matrix(scale, scale)
        out: list[bytes] = []
        for i in range(page_count):
            page = doc[i]
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            out.append(pix.tobytes("png"))
        return out
    finally:
        doc.close()


def _parse_llm_json_response(raw_text: str) -> dict[str, Any]:
    """Parse a raw LLM text response into a dict.

    Tolerates the three response shapes the calibration set has
    actually seen from both Anthropic and OpenAI vision models:

    1. Plain JSON object: ``{"line_items": [...], ...}``
    2. JSON inside a markdown fence (triple-backtick ``json`` block).
    3. JSON object with chatty prose around it (model violated the
       JSON-only instruction).

    Returns a parsed ``dict``. Raises :class:`SubquoteLLMError` when no
    JSON object is recoverable from the input.
    """
    if raw_text is None:
        raise SubquoteLLMError(
            "LLM returned no response text (None)."
        )
    text = str(raw_text).strip()
    if not text:
        raise SubquoteLLMError(
            "LLM returned an empty response."
        )

    # First try: parse the whole thing.
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        parsed = None

    if not isinstance(parsed, dict):
        # Second try: pull a JSON object out of a markdown fence
        # ``json ... `` or pick up the substring between the first
        # ``{`` and last ``}``.
        fence_match = re.search(
            r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL
        )
        if fence_match:
            try:
                parsed = json.loads(fence_match.group(1))
            except json.JSONDecodeError:
                parsed = None

    if not isinstance(parsed, dict):
        start = text.find("{")
        end = text.rfind("}")
        if 0 <= start < end:
            try:
                parsed = json.loads(text[start : end + 1])
            except json.JSONDecodeError:
                parsed = None

    if not isinstance(parsed, dict):
        preview = text[:200].replace("\n", " ")
        raise SubquoteLLMError(
            f"LLM returned malformed JSON (could not recover an object). "
            f"First 200 chars: {preview!r}"
        )
    return parsed


def _call_vision_llm_for_page(
    page_png: bytes,
    llm_client: "LLMClient",
    user_prompt: str,
    system_prompt: str = _LLM_SYSTEM_PROMPT,
) -> dict[str, Any]:
    """Send one page's PNG bytes to the vision LLM; return parsed JSON.

    The :class:`core.llm_client.LLMClient.analyze_image` entry point
    accepts a *file path*, not bytes — so we drop the PNG into a
    NamedTemporaryFile for the duration of the call, then delete it.
    No filesystem leak in the success or failure path.

    The LLM client itself owns:

    * 429 / rate-limit retry with header-aware backoff (12 attempts,
      5-minute wall-clock ceiling).
    * One JSON-repair re-prompt when the first response is malformed.

    Both behaviours are inherited unchanged. This wrapper only adds the
    PNG-to-tempfile conversion and translates the client's
    ``ValueError`` (raised after both repair attempts fail) into a
    :class:`SubquoteLLMError`.
    """
    if not page_png:
        raise SubquoteLLMError(
            "Empty PNG payload for LLM call (rendering returned 0 bytes)."
        )
    if llm_client is None:
        raise SubquoteLLMError(
            "No LLM client provided to parse_subquote_pdf_with_llm; "
            "configure ANTHROPIC_API_KEY or OPENAI_API_KEY in .env."
        )

    tmp_path: str | None = None
    try:
        with tempfile.NamedTemporaryFile(
            suffix=".png", delete=False
        ) as tmp:
            tmp.write(page_png)
            tmp_path = tmp.name
        try:
            resp = llm_client.analyze_image(
                image_path=tmp_path,
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
        except ValueError as exc:
            # LLMClient raises ValueError("LLM did not return JSON…")
            # after both its repair attempts fail. Map to the
            # subquote-specific exception type so the UI can surface
            # it as an LLM-path failure rather than a generic crash.
            raise SubquoteLLMError(
                f"LLM returned malformed JSON after repair attempt: {exc}"
            ) from exc

        parsed = resp.parsed
        if isinstance(parsed, dict):
            return parsed
        # The LLM client's ``parsed`` field is normally a dict but
        # nothing in its type signature pins this; on the off chance
        # the model emitted a JSON list (against our prompt), fall
        # back to parsing the raw text.
        text = getattr(resp, "text", "") or ""
        return _parse_llm_json_response(text)
    finally:
        if tmp_path is not None:
            try:
                os.unlink(tmp_path)
            except OSError:
                # Tempfile already cleaned up (Windows AV / parallel
                # GC race). Not fatal — best-effort cleanup.
                pass


def _coerce_optional_float(raw: Any) -> float | None:
    """Best-effort numeric coercion shared by the LLM-row validator.

    The vision LLM occasionally returns numbers as strings ("450.00")
    or with leftover decoration ("$450"). We accept all of those by
    routing through :func:`_parse_number`, which is the same number
    parser the T8.1 tabular path uses for column cells. Returns
    ``None`` on un-coercible input.
    """
    if raw is None:
        return None
    if isinstance(raw, (int, float)):
        try:
            f = float(raw)
        except (TypeError, ValueError):
            return None
        if f != f:  # NaN
            return None
        return f
    return _parse_number(str(raw))


def _validate_and_build_row(
    raw_item: dict[str, Any],
    page_num: int,
    row_index: int,
) -> tuple[BatchOverrideRow | None, str | None]:
    """Validate one raw LLM line-item dict; build a :class:`BatchOverrideRow`.

    Returns ``(row, None)`` on success, ``(None, warning)`` on validated
    skip. The validation rules mirror the T8.1 :func:`_parse_table_rows`
    contract:

    * ``description`` must be a non-empty string after whitespace
      collapse.
    * ``unit_cost`` must be a non-negative number (or derivable from
      ``extended_price / quantity`` when both are present).
    * ``notes`` is truncated to :data:`_LLM_NOTES_MAX_CHARS`.

    Any other field that fails coercion is silently dropped (the row
    still emits with the salvageable parts).
    """
    if not isinstance(raw_item, dict):
        return None, (
            f"Page {page_num} row {row_index}: not a JSON object; skipped."
        )

    description = raw_item.get("description")
    if not isinstance(description, str):
        description = "" if description is None else str(description)
    description = _normalise_cell(description)
    if not description:
        return None, (
            f"Page {page_num} row {row_index}: empty description; skipped."
        )
    # Skip subtotal / tax / total rows the LLM may have included
    # despite the prompt instruction. Cheap defense in depth.
    if _is_subtotal_row(description):
        return None, None  # silent skip — expected

    quantity = _coerce_optional_float(raw_item.get("quantity"))
    if quantity is not None and quantity < 0:
        quantity = None

    unit_cost = _coerce_optional_float(raw_item.get("unit_cost"))
    extended = _coerce_optional_float(raw_item.get("extended_price"))

    if unit_cost is None and extended is not None and quantity is not None and quantity > 0:
        unit_cost = round(extended / quantity, 4)

    if unit_cost is None:
        return None, (
            f"Page {page_num} row {row_index}: no unit_cost or "
            f"derivable extended/qty; skipped."
        )
    if unit_cost < 0:
        return None, (
            f"Page {page_num} row {row_index}: negative unit_cost "
            f"{unit_cost}; skipped."
        )

    raw_notes = raw_item.get("notes")
    notes: str | None = None
    if isinstance(raw_notes, str):
        n = _normalise_cell(raw_notes)
        if n:
            notes = n[:_LLM_NOTES_MAX_CHARS]

    raw_unit = raw_item.get("unit")
    if isinstance(raw_unit, str):
        unit = _normalise_cell(raw_unit)
        if unit:
            # Append the unit hint to notes (compact provenance) so
            # the downstream matcher / UI can show it without growing
            # the BatchOverrideRow schema.
            unit_hint = f"unit: {unit}"
            if notes:
                combined = f"{notes} ({unit_hint})"
                notes = combined[:_LLM_NOTES_MAX_CHARS]
            else:
                notes = unit_hint[:_LLM_NOTES_MAX_CHARS]

    row = BatchOverrideRow(
        row_index=row_index,
        description=description,
        unit_cost=float(unit_cost),
        vendor=None,         # vendor goes on metadata, not per-row
        quote_ref=None,      # ditto for quote-ref
        notes=notes,
        quantity=quantity,
    )
    return row, None


def _build_metadata_from_llm_pages(
    per_page_results: list[dict[str, Any]],
    detected_pages: list[int],
    pages_with_items: int,
    pages_processed: int,
) -> SubquoteMetadata:
    """Aggregate metadata across pages: first non-null wins per slot.

    Confidence is the share of pages that yielded at least one line
    item, which is a useful proxy for "did the LLM see what we
    asked it to see". When zero pages are processed (degenerate),
    confidence is 0.0.
    """
    md = SubquoteMetadata(detected_pages=sorted(set(detected_pages)))
    for page in per_page_results:
        if not isinstance(page, dict):
            continue
        meta = page.get("metadata")
        if not isinstance(meta, dict):
            continue
        if md.vendor_name is None:
            v = meta.get("vendor_name")
            if isinstance(v, str) and v.strip():
                md.vendor_name = v.strip()
        if md.quote_number is None:
            q = meta.get("quote_number")
            if isinstance(q, str) and q.strip():
                md.quote_number = q.strip()
        if md.quote_date is None:
            d = meta.get("quote_date")
            if isinstance(d, str) and d.strip():
                md.quote_date = d.strip()
        if md.project_reference is None:
            p = meta.get("project_reference")
            if isinstance(p, str) and p.strip():
                md.project_reference = p.strip()
        if md.total_quoted is None:
            t = _coerce_optional_float(meta.get("total_quoted"))
            if t is not None:
                md.total_quoted = t

    if pages_processed > 0:
        md.confidence = round(pages_with_items / float(pages_processed), 2)
    else:
        md.confidence = 0.0
    return md


def _merge_llm_pages_to_result(
    per_page_results: list[dict[str, Any]],
    total_pages: int,
) -> SubquoteParseResult:
    """Aggregate per-page LLM responses into a single :class:`SubquoteParseResult`.

    Pure transformation — no LLM, no I/O. Each entry in
    ``per_page_results`` is the parsed JSON dict the model emitted for
    one page, in document order. ``total_pages`` is the number of pages
    we *actually* sent to the LLM (may be less than the PDF's page
    count when ``max_pages`` was capped) — used to compute confidence.

    Output:

    * ``rows`` — every validated :class:`BatchOverrideRow` across all
      pages, with ``row_index`` monotonically increasing.
    * ``metadata`` — first non-null value across pages for each
      metadata slot; ``confidence`` = pages_with_items / pages_processed.
    * ``warnings`` — per-page-skip reasons (when the LLM returned
      ``is_subquote_page=false``) plus per-row drop reasons (empty
      description, negative unit_cost, etc.).
    """
    rows: list[BatchOverrideRow] = []
    warnings: list[str] = []
    detected_pages: list[int] = []
    pages_with_items = 0
    running_row_index = 1  # 1-indexed; mirrors T8.1 + CSV row 1 = header

    for page_idx, page_result in enumerate(per_page_results, start=1):
        if not isinstance(page_result, dict):
            warnings.append(
                f"Page {page_idx}: LLM response was not a JSON object; "
                f"page skipped."
            )
            continue

        # Honour the prompt's page-skip protocol explicitly.
        if page_result.get("is_subquote_page") is False:
            reason = page_result.get("page_skipped_reason")
            reason_str = (
                str(reason).strip()
                if isinstance(reason, str) and reason.strip()
                else "LLM flagged page as not a sub-quote line-item page."
            )
            warnings.append(f"Page {page_idx}: {reason_str}")
            continue

        raw_items = page_result.get("line_items")
        if not isinstance(raw_items, list):
            warnings.append(
                f"Page {page_idx}: 'line_items' missing or not a list; "
                f"page skipped."
            )
            continue

        page_emitted = 0
        for raw_item in raw_items:
            running_row_index += 1
            row, warning = _validate_and_build_row(
                raw_item, page_idx, running_row_index
            )
            if warning is not None:
                warnings.append(warning)
            if row is not None:
                rows.append(row)
                page_emitted += 1

        if page_emitted > 0:
            detected_pages.append(page_idx)
            pages_with_items += 1

    metadata = _build_metadata_from_llm_pages(
        per_page_results=per_page_results,
        detected_pages=detected_pages,
        pages_with_items=pages_with_items,
        pages_processed=total_pages,
    )

    return SubquoteParseResult(
        rows=rows,
        metadata=metadata,
        warnings=warnings,
    )


def parse_subquote_pdf_with_llm(
    pdf_bytes: bytes,
    *,
    llm_client: "LLMClient | None" = None,
    max_pages: int = _LLM_DEFAULT_MAX_PAGES,
    dpi: int = _LLM_DEFAULT_DPI,
    user_prompt: str | None = None,
) -> SubquoteParseResult:
    """LLM-vision fallback for scanned / free-form sub-quote PDFs.

    Use when :func:`parse_subquote_pdf` raises
    :class:`SubquoteParseError` — i.e. the PDF has no extractable
    table structure (scanned image, free-form letter, unusual column
    titles). Renders each page to a PNG and sends it through the
    project's standard vision LLM, then parses the structured JSON
    response back into the same :class:`BatchOverrideRow` shape T8.1
    emits so the downstream pipeline is unchanged.

    Args:
        pdf_bytes: Raw PDF bytes (same as :func:`parse_subquote_pdf`).
        llm_client: Vision-capable :class:`core.llm_client.LLMClient`.
            When ``None`` (default), a client is constructed lazily
            from the environment (``ANTHROPIC_API_KEY`` /
            ``OPENAI_API_KEY``). Pass an explicit client in tests so
            no network call is made.
        max_pages: Cap on pages sent to the LLM. Defaults to 10.
            Sub-quote PDFs are typically 1-3 pages; the cap defends
            against accidentally feeding a 50-page document.
        dpi: Render DPI. Defaults to 200 — the calibrated sweet spot
            for vision LLMs (clear text at reasonable token cost).
            Bump to 300 if accuracy drops on dense numerical tables.
        user_prompt: Override the default prompt loaded from
            ``prompts/subquote_vision.txt``. Almost always ``None``
            in production; useful in tests that want to verify the
            prompt routes through.

    Returns:
        :class:`SubquoteParseResult` — same shape as
        :func:`parse_subquote_pdf`. ``metadata.detected_pages`` lists
        the 1-indexed pages from which line items were extracted;
        ``metadata.confidence`` is ``pages_with_items / pages_processed``.

    Raises:
        SubquoteLLMError: When the PDF can't be rendered (empty,
            corrupted, encrypted, zero-page), or the LLM call fails
            (auth error, retry budget exhausted, malformed JSON on
            every page).
    """
    # Pre-flight: render pages first so we fail fast on a bad PDF
    # before incurring any LLM cost.
    page_pngs = _render_pdf_pages_to_png(
        pdf_bytes, max_pages=max_pages, dpi=dpi
    )
    if not page_pngs:
        raise SubquoteLLMError(
            "PDF rendered to zero PNG pages. Re-export and re-upload."
        )

    # Lazy-construct the LLM client only when one wasn't injected.
    # Keeps the import fast for callers that pass their own client
    # (e.g. the test suite) and avoids touching env vars unless
    # absolutely necessary.
    client = llm_client
    if client is None:
        from core.llm_client import LLMClient as _LLMClient

        try:
            client = _LLMClient()
        except RuntimeError as exc:
            raise SubquoteLLMError(
                f"Could not construct vision LLM client: {exc}"
            ) from exc

    prompt = user_prompt if user_prompt is not None else _load_subquote_vision_prompt()

    per_page_results: list[dict[str, Any]] = []
    pages_failed: list[tuple[int, str]] = []
    for page_idx, png in enumerate(page_pngs, start=1):
        try:
            parsed = _call_vision_llm_for_page(
                page_png=png,
                llm_client=client,
                user_prompt=prompt,
            )
        except SubquoteLLMError as exc:
            pages_failed.append((page_idx, str(exc)))
            logger.warning(
                "subquote-llm: page %d extraction failed: %s",
                page_idx, exc,
            )
            continue
        except Exception as exc:
            # Anything the LLM client raises that isn't a JSON-parse
            # error — auth failure, persistent 5xx, retry-budget
            # exhaustion. Surface the first such failure verbatim;
            # subsequent pages are not attempted because the same
            # client config will fail the same way.
            raise SubquoteLLMError(
                f"LLM call failed on page {page_idx} "
                f"({type(exc).__name__}): {exc}"
            ) from exc
        per_page_results.append(parsed)

    if not per_page_results:
        # Every page failed. Surface the first failure so the operator
        # has a real error message instead of an empty result.
        first_msg = pages_failed[0][1] if pages_failed else "unknown error"
        raise SubquoteLLMError(
            f"LLM extraction failed on every page ({len(pages_failed)} "
            f"page(s) attempted). First error: {first_msg}"
        )

    result = _merge_llm_pages_to_result(
        per_page_results=per_page_results,
        total_pages=len(per_page_results),
    )

    # Attach per-page failure messages as warnings so they survive
    # to the operator UI (the result still went through because
    # other pages succeeded; the operator should know which were
    # dropped).
    for page_idx, msg in pages_failed:
        result.warnings.append(
            f"Page {page_idx}: LLM extraction failed and the page was "
            f"dropped from the result. ({msg})"
        )

    return result
