"""Phase T8.1 — sub-quote PDF ingestion (tabular).

Subs (mechanical, electrical, plumbing, glass, drywall, etc.) commonly
deliver priced sub-quotes as PDF documents. This module parses *tabular*
sub-quote PDFs (structured tables with consistent columns) into a list
of :class:`~core.pricing.batch_override.BatchOverrideRow` records — the
identical shape :func:`core.pricing.batch_override.parse_vendor_csv`
produces — so the downstream
:func:`~core.pricing.batch_override.match_cost_lines` and
:func:`~core.pricing.batch_override.apply_batch_plan` pipeline can
consume the output unchanged.

Phase T8.2 (LLM-vision fallback for *scanned* / free-form quotes) is
explicitly **out of scope** here. PDFs that don't yield deterministic
table structure raise :class:`SubquoteParseError` with a clear message
pointing the operator at the T6.3 CSV uploader (or a future T8.2 path).

Architecture::

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

Public surface:

* :class:`SubquoteParseError` — recoverable + non-recoverable failures.
* :class:`SubquoteMetadata`   — optional vendor / quote-# / date / total
  scraped from page text (regex-only; no LLM).
* :class:`SubquoteParseResult` — combined ``(rows, metadata, warnings)``.
* :func:`parse_subquote_pdf`  — main entry point; bytes in, result out.

The parser is intentionally **conservative**: when header detection is
ambiguous we raise rather than silently emit garbage rows that would
then misroute through the fuzzy matcher and quietly mangle the estimate.

No new third-party dependencies — uses ``fitz`` (PyMuPDF, already in
``requirements.txt`` for the drawing PDF processor) and stdlib only.
"""

from __future__ import annotations

import io
import re
from dataclasses import dataclass, field

import fitz

from core.pricing.batch_override import (
    _COLUMN_ALIASES,
    BatchOverrideRow,
)


# ---------------------------------------------------------------------------
# Exceptions + result types
# ---------------------------------------------------------------------------


class SubquoteParseError(Exception):
    """Raised when the PDF can't be parsed deterministically into rows.

    Recoverable cases (these are T8.2 — LLM-vision fallback — territory):

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
