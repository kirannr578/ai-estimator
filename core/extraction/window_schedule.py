"""Deterministic window-schedule extraction (Phase T2.5).

Window schedules are the second-most schema-stable tabular artefact on an
A-series sheet (after the door schedule landed in Phase T1): a table that
enumerates every window tag (``W-01``, ``W101``, ``A``) alongside its type,
size, glazing, operation, frame, and (often) thermal performance
(``U-FACTOR`` / ``SHGC``). This module pulls that table off a PDF page
deterministically -- no LLM, no rendered image, PyMuPDF + stdlib only --
so downstream takeoff (Phase T2.5 synthesis) can synthesise per-window
``TakeoffItem``s with high confidence.

Architectural pattern mirrors :mod:`core.extraction.door_schedule`:
pure functions of a ``Path`` + page index (or a ``fitz.Page``), internal
dataclasses with a ``to_schema()`` bridge to the Pydantic models on
:mod:`core.schemas`, and a confidence rubric. Runs **alongside** (never
instead of) the existing F3 prepass.

Door-vs-window discriminator (critical):
Window schedules and door schedules SHARE ``MARK / TYPE / WIDTH / HEIGHT``
column headers. The discriminator is window-specific column names
(``GLAZING`` / ``OPERATION`` / ``SILL`` / ``U-FACTOR`` / ``SHGC``) vs
door-specific (``HARDWARE`` / ``HDW`` / ``FIRE`` / ``RATING``). The header
heuristic in :func:`_looks_like_window_header` requires a window-specific
signal. When a page matches BOTH the door and window detector, the door
detector wins (older, more-validated, and the integration hook in
:mod:`core.extraction.drawing_prepass` skips the window pass for that page).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

from .door_schedule import parse_dimension  # reused verbatim — see module docstring

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class WindowRecord:
    """One window pulled off a schedule table."""

    mark: str
    type: str | None = None
    width_in: float | None = None
    height_in: float | None = None
    sill_height_in: float | None = None
    width_raw: str | None = None
    height_raw: str | None = None
    sill_height_raw: str | None = None
    glazing: str | None = None
    operation: str | None = None
    frame: str | None = None
    material: str | None = None
    u_factor: float | None = None
    shgc: float | None = None
    remarks: str | None = None
    raw_cells: dict[str, str] = field(default_factory=dict)
    source_page: int = 0


@dataclass
class WindowScheduleResult:
    """Aggregate window-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    windows: list[WindowRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Window-tag pattern: optional W-/W_ prefix, 1-4 digits OR a single
# alphanumeric label (some offices use A/B/C tags for window types).
# Tolerates trailing single-letter suffix (``W-01A``).
_WINDOW_TAG_RE = re.compile(r"^\s*(?:W[-_]?)?[A-Z]?\d{1,4}[A-Z]?\s*$")


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_window_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a window-schedule header row?

    Requires three signals together to avoid false-positives on
    neighbouring door schedules that share ``MARK / TYPE / WIDTH / HEIGHT``:

    1. a tag column (``MARK`` / ``NO`` / ``NUMBER`` / ``WINDOW`` / ``TAG``),
    2. at least one **window-specific** column
       (``GLAZING`` / ``GLASS`` / ``OPERATION`` / ``OPER`` / ``SILL`` /
       ``UFACTOR`` / ``SHGC``),
    3. at least one dimensional column (``TYPE`` / ``SIZE`` / ``WIDTH`` /
       ``HEIGHT`` / ``MATERIAL`` / ``MATL`` / ``FRAME``).

    The window-specific requirement is the discriminator vs door schedules
    that share the other two signal classes.
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    has_tag = bool(words & {"MARK", "NO", "NUMBER", "WINDOW", "TAG", "ID"})
    window_specific = words & {
        "GLAZING", "GLASS", "OPERATION", "OPER", "SILL",
        "UFACTOR", "SHGC", "UVALUE",
    }
    dimensional = words & {
        "TYPE", "SIZE", "WIDTH", "HEIGHT",
        "MATERIAL", "MATL", "FRAME",
    }
    return has_tag and bool(window_specific) and bool(dimensional)


def detect_window_schedule(page: "fitz.Page") -> bool:
    """True when the page very likely contains a window schedule.

    Two cheap signals: literal ``WINDOW SCHEDULE`` in page text, OR a
    window-shaped header row on any detected table. Either suffices.
    """
    text = page.get_text("text") or ""
    if "WINDOW SCHEDULE" in text.upper():
        return True
    try:
        tables = getattr(page.find_tables(), "tables", None) or []
    except Exception:  # pragma: no cover - PyMuPDF internal
        return False
    for table in tables:
        try:
            extracted = table.extract()
        except Exception:  # pragma: no cover - PyMuPDF internal
            continue
        if not extracted:
            continue
        headers = [str(h or "") for h in (extracted[0] or [])]
        if _looks_like_window_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Dimension parsing
# ---------------------------------------------------------------------------
#
# ``parse_dimension`` is imported from :mod:`core.extraction.door_schedule`
# to keep the two extractors in lock-step on what a "valid feet-inches"
# cell looks like. Combined ``SIZE`` cells (``3'-0" x 5'-0"``) are split
# locally because window schedules sometimes use a slightly different
# separator (``X`` / ``by`` / ``×``); the helper below covers both.

_SIZE_SPLIT_RE = re.compile(r"\s*(?:x|×|X|by)\s*", re.IGNORECASE)


def _parse_size_cell(raw: str | None) -> tuple[float | None, float | None,
                                                 str | None, str | None]:
    """Parse a combined SIZE cell like ``3'-0" x 5'-0"`` into (w, h, w_raw, h_raw)."""
    if not raw:
        return None, None, None, None
    parts = _SIZE_SPLIT_RE.split(raw.strip(), maxsplit=2)
    if len(parts) < 2:
        return None, None, None, None
    w_raw, h_raw = parts[0].strip(), parts[1].strip()
    return parse_dimension(w_raw), parse_dimension(h_raw), w_raw, h_raw


# ---------------------------------------------------------------------------
# Numeric (U-factor / SHGC) parsing
# ---------------------------------------------------------------------------


_FLOAT_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*$")


def _parse_float(raw: str | None) -> float | None:
    """Parse a plain decimal cell (e.g. ``0.32``) or return None.

    Tolerates a trailing ``BTU/HR.SF.F`` or similar tail seen on some
    schedule cells by extracting the leading number; returns ``None`` if
    the cell starts with anything non-numeric.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if (m := _FLOAT_RE.match(text)):
        return float(m.group(1))
    leading = re.match(r"\s*(\d+(?:\.\d+)?)", text)
    if leading:
        return float(leading.group(1))
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


def _header_index(headers: list[str], candidates: tuple[str, ...]) -> int | None:
    """Index of the first header matching any candidate (word- or substring-)."""
    for i, h in enumerate(headers):
        norm = _normalize_header(h)
        norm_words = set(norm.split())
        if any(c in norm_words for c in candidates):
            return i
        if any(c in norm for c in candidates):
            return i
    return None


def _cell(row: list[str], idx: int | None) -> str | None:
    if idx is None or idx < 0 or idx >= len(row):
        return None
    return (row[idx] or "").strip() or None


_HEADERS: dict[str, tuple[str, ...]] = {
    "mark":     ("MARK", "NO", "NUMBER", "WINDOW", "ID", "TAG"),
    "type":     ("TYPE",),
    "size":     ("SIZE",),
    "width":    ("WIDTH",),
    "height":   ("HEIGHT",),
    "sill":     ("SILL",),
    "material": ("MATERIAL", "MATL", "MAT"),
    "frame":    ("FRAME",),
    "glazing":  ("GLAZING", "GLASS"),
    "operation":("OPERATION", "OPER", "OPERABLE"),
    # ``U-FACTOR`` normalises to ``U FACTOR``, ``U VALUE`` to ``U VALUE``
    # — match the distinctive right-side token rather than the joined
    # form so the cell is found regardless of separator. ``FACTOR`` /
    # ``UVALUE`` are kept as fall-backs.
    "u_factor": ("FACTOR", "UFACTOR", "UVALUE"),
    "shgc":     ("SHGC",),
    "remarks":  ("REMARKS", "NOTES", "COMMENTS"),
}


def _records_from_table(headers: list[str], data_rows: list[list[str]],
                          page_index: int) -> list[WindowRecord]:
    """Convert one table's rows to :class:`WindowRecord` instances."""
    idx = {k: _header_index(headers, v) for k, v in _HEADERS.items()}
    records: list[WindowRecord] = []
    for row in data_rows:
        if not row:
            continue
        mark = _cell(row, idx["mark"])
        if not mark:
            continue
        # Filter out rows whose first column is obviously not a window
        # tag (sub-headers / continuation rows that survive grid extraction).
        if not _WINDOW_TAG_RE.match(mark) and " " in mark:
            continue

        width_raw = _cell(row, idx["width"])
        height_raw = _cell(row, idx["height"])
        width_in = parse_dimension(width_raw)
        height_in = parse_dimension(height_raw)
        if (width_in is None or height_in is None) and idx["size"] is not None:
            sw, sh, swr, shr = _parse_size_cell(_cell(row, idx["size"]))
            width_in = width_in or sw
            height_in = height_in or sh
            width_raw = width_raw or swr
            height_raw = height_raw or shr

        sill_raw = _cell(row, idx["sill"])
        raw_cells: dict[str, str] = {}
        for h_idx, h in enumerate(headers):
            v = _cell(row, h_idx)
            if h and v:
                raw_cells[h] = v

        records.append(WindowRecord(
            mark=mark,
            type=_cell(row, idx["type"]),
            width_in=width_in,
            height_in=height_in,
            sill_height_in=parse_dimension(sill_raw),
            width_raw=width_raw,
            height_raw=height_raw,
            sill_height_raw=sill_raw,
            glazing=_cell(row, idx["glazing"]),
            operation=_cell(row, idx["operation"]),
            frame=_cell(row, idx["frame"]),
            material=_cell(row, idx["material"]),
            u_factor=_parse_float(_cell(row, idx["u_factor"])),
            shgc=_parse_float(_cell(row, idx["shgc"])),
            remarks=_cell(row, idx["remarks"]),
            raw_cells=raw_cells,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Text-cluster fallback (used when find_tables() yields no window table)
# ---------------------------------------------------------------------------


def _cluster_lines_to_table(page: "fitz.Page") -> tuple[list[str], list[list[str]]] | None:
    """Cluster page text spans into rows by y-coord; return ``(headers, rows)`` or ``None``."""
    try:
        data = page.get_text("dict") or {}
    except Exception:  # pragma: no cover
        return None
    spans: list[tuple[float, float, str]] = []
    for block in data.get("blocks", []):
        for line in block.get("lines", []):
            for sp in line.get("spans", []):
                txt = (sp.get("text") or "").strip()
                if not txt:
                    continue
                bbox = sp.get("bbox") or [0, 0, 0, 0]
                spans.append((bbox[1], bbox[0], txt))
    if not spans:
        return None
    spans.sort(key=lambda t: (round(t[0] / 4) * 4, t[1]))

    rows: list[list[tuple[float, str]]] = []
    bucket: list[tuple[float, str]] = []
    current_y: float | None = None
    for y, x, txt in spans:
        if current_y is None or abs(y - current_y) <= 4.0:
            bucket.append((x, txt))
            if current_y is None:
                current_y = y
        else:
            bucket.sort(key=lambda t: t[0])
            rows.append(bucket)
            bucket = [(x, txt)]
            current_y = y
    if bucket:
        bucket.sort(key=lambda t: t[0])
        rows.append(bucket)

    header_row: list[str] | None = None
    data_rows: list[list[str]] = []
    for row in rows:
        cells = [t for _, t in row]
        if header_row is None and _looks_like_window_header(cells):
            header_row = cells
            continue
        if header_row is not None and cells and any(_WINDOW_TAG_RE.match(c) for c in cells[:2]):
            data_rows.append(cells)
    if header_row and data_rows:
        return header_row, data_rows
    return None


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _score(has_phrase: bool, tables_found: int, records: list[WindowRecord]) -> float:
    """0.40 for the phrase; 0.30 for a window-shaped table; 0.20 if any record
    has both width and height parsed; 0.10 for >= 5 records. Clamped to 1.0."""
    if not records and tables_found == 0:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    if tables_found >= 1:
        score += 0.30
    if any(r.width_in is not None and r.height_in is not None for r in records):
        score += 0.20
    if len(records) >= 5:
        score += 0.10
    return min(score, 1.0)


def extract_window_schedule_from_page(page: "fitz.Page",
                                         page_index: int = 0) -> WindowScheduleResult:
    """Extract the window schedule (if any) from a single PyMuPDF page."""
    text = page.get_text("text") or ""
    has_phrase = "WINDOW SCHEDULE" in text.upper()

    all_records: list[WindowRecord] = []
    header_debug: list[str] = []
    window_tables_found = 0

    try:
        tables = getattr(page.find_tables(), "tables", None) or []
    except Exception as exc:  # pragma: no cover - PyMuPDF internal
        logger.debug("find_tables failed on page %d: %s", page_index, exc)
        tables = []

    for table in tables:
        try:
            extracted = table.extract()
        except Exception as exc:  # pragma: no cover - PyMuPDF internal
            logger.debug("table.extract failed on page %d: %s", page_index, exc)
            continue
        if not extracted or len(extracted) < 2:
            continue
        headers = [str(h).strip() if h is not None else "" for h in (extracted[0] or [])]
        if not _looks_like_window_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if records:
            window_tables_found += 1
            header_debug.append(" | ".join(headers))
            all_records.extend(records)

    if not all_records:
        fallback = _cluster_lines_to_table(page)
        if fallback is not None:
            headers, data_rows = fallback
            records = _records_from_table(headers, data_rows, page_index)
            if records:
                window_tables_found += 1
                header_debug.append(" | ".join(headers))
                all_records.extend(records)

    return WindowScheduleResult(
        pages=[page_index] if all_records else [],
        windows=all_records,
        confidence=round(_score(has_phrase, window_tables_found, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_window_schedule(pdf_path: Path, page_index: int) -> WindowScheduleResult:
    """Run the window-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_window_schedule_from_page(doc[page_index], page_index)


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: WindowScheduleResult):
    """Return a :class:`core.schemas.WindowScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.WindowScheduleResult(
        pages=list(result.pages),
        windows=[
            S.WindowRecord(
                mark=w.mark,
                type=w.type,
                width_in=w.width_in,
                height_in=w.height_in,
                sill_height_in=w.sill_height_in,
                width_raw=w.width_raw,
                height_raw=w.height_raw,
                sill_height_raw=w.sill_height_raw,
                glazing=w.glazing,
                operation=w.operation,
                frame=w.frame,
                material=w.material,
                u_factor=w.u_factor,
                shgc=w.shgc,
                remarks=w.remarks,
                raw_cells=dict(w.raw_cells),
                source_page=w.source_page,
            )
            for w in result.windows
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
