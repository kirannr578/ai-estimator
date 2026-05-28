"""Deterministic door-schedule extraction (Phase T1).

A door schedule is one of the most schema-stable tabular artefacts in any
drawing set: a table on an A-series sheet that enumerates every door tag
(``101``, ``101A``, ``D-101``) with its type, size, frame, hardware, fire
rating, and remarks. This module pulls that table off a PDF page
deterministically — no LLM, no rendered image, PyMuPDF + stdlib only —
so downstream takeoff (Phase T2) can synthesise per-door ``TakeoffItem``s
with high confidence.

Architectural pattern mirrors :mod:`core.extraction.drawing_prepass`:
pure functions of a ``Path`` + page index (or a ``fitz.Page``), internal
dataclasses with a ``to_schema()`` bridge to the Pydantic models on
:mod:`core.schemas`, and a confidence rubric. Runs **alongside** (never
instead of) the existing F3 prepass.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class DoorRecord:
    """One door pulled off a schedule table."""

    mark: str
    type: str | None = None
    width_in: float | None = None
    height_in: float | None = None
    thickness_in: float | None = None
    width_raw: str | None = None
    height_raw: str | None = None
    material: str | None = None
    frame: str | None = None
    hardware_set: str | None = None
    fire_rating: str | None = None
    remarks: str | None = None
    source_page: int = 0


@dataclass
class DoorScheduleResult:
    """Aggregate door-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    doors: list[DoorRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Door-tag pattern: optional D-/D_ prefix, 2-4 digits, optional A-Z suffix.
_DOOR_TAG_RE = re.compile(r"^\s*(?:D[-_]?)?\d{2,4}[A-Z]?\s*$")


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_door_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a door-schedule header row?

    Requires three signals together to avoid false-positives on neighbouring
    window schedules that share ``MARK / TYPE / WIDTH / HEIGHT``:

    1. a tag column (``MARK`` / ``NO`` / ``NUMBER`` / ``DOOR`` / ``TAG``),
    2. at least one door-specific column (``DOOR`` / ``FRAME`` /
       ``HARDWARE`` / ``HDW`` / ``RATING`` / ``FIRE``),
    3. at least one dimensional column (``TYPE`` / ``SIZE`` / ``WIDTH`` /
       ``HEIGHT`` / ``THICKNESS`` / ``THK`` / ``MATERIAL`` / ``MATL``).
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    has_tag = bool(words & {"MARK", "NO", "NUMBER", "DOOR", "TAG", "ID"})
    door_specific = words & {"DOOR", "FRAME", "HARDWARE", "HDW", "RATING", "FIRE"}
    dimensional = words & {"TYPE", "SIZE", "WIDTH", "HEIGHT",
                            "THICKNESS", "THK", "MATERIAL", "MATL"}
    return has_tag and bool(door_specific) and bool(dimensional)


def detect_door_schedule(page: "fitz.Page") -> bool:
    """True when the page very likely contains a door schedule.

    Two cheap signals: literal ``DOOR SCHEDULE`` in page text, OR a
    door-shaped header row on any detected table. Either suffices.
    """
    text = page.get_text("text") or ""
    if "DOOR SCHEDULE" in text.upper():
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
        if _looks_like_door_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Dimension parsing
# ---------------------------------------------------------------------------


_DIM_FT_IN_RE = re.compile(
    # 3'-0", 3' 0", 3'0", 3' - 0", 3'-0 1/2", 3'
    r"^\s*(\d+)\s*'\s*(?:-?\s*(\d+)\s*(?:(\d+)/(\d+))?\s*\"?)?\s*$"
)
_DIM_IN_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*\"\s*$")
_DIM_FT_IN_WORDS_RE = re.compile(
    r"^\s*(\d+)\s*(?:ft|feet)\s*(?:(\d+)\s*(?:in|inch|inches)?)?\s*$",
    re.IGNORECASE,
)
_SIZE_SPLIT_RE = re.compile(r"\s*(?:x|×|X|by)\s*", re.IGNORECASE)


def parse_dimension(raw: str | None) -> float | None:
    """Parse a door-schedule dimension cell into inches.

    Accepts ``3'0"``, ``3'-0"``, ``3' - 0 1/2"``, ``36"``, ``3 ft 0 in``,
    ``3 ft``. Returns ``None`` (never raises) when the input is empty,
    malformed, or non-numeric so callers can keep extraction running on
    partial rows. Plain bare integers are intentionally rejected —
    ambiguous in a schedule context.
    """
    if not raw:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if (m := _DIM_FT_IN_RE.match(text)):
        feet = float(m.group(1))
        inches = float(m.group(2) or 0)
        if m.group(3) and m.group(4):
            inches += float(m.group(3)) / (float(m.group(4)) or 1.0)
        return feet * 12.0 + inches
    if (m := _DIM_IN_RE.match(text)):
        return float(m.group(1))
    if (m := _DIM_FT_IN_WORDS_RE.match(text)):
        return float(m.group(1)) * 12.0 + float(m.group(2) or 0)
    return None


def _parse_size_cell(raw: str | None) -> tuple[float | None, float | None,
                                                 str | None, str | None]:
    """Parse a combined SIZE cell like ``3'-0" x 7'-0"`` into (w, h, w_raw, h_raw)."""
    if not raw:
        return None, None, None, None
    parts = _SIZE_SPLIT_RE.split(raw.strip(), maxsplit=2)
    if len(parts) < 2:
        return None, None, None, None
    w_raw, h_raw = parts[0].strip(), parts[1].strip()
    return parse_dimension(w_raw), parse_dimension(h_raw), w_raw, h_raw


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


_HEADERS = {
    "mark":     ("MARK", "NO", "NUMBER", "DOOR", "ID", "TAG"),
    "type":     ("TYPE",),
    "size":     ("SIZE",),
    "width":    ("WIDTH",),
    "height":   ("HEIGHT",),
    "thick":    ("THICKNESS", "THK"),
    "material": ("MATERIAL", "MATL", "MAT"),
    "frame":    ("FRAME",),
    "hdw":      ("HARDWARE", "HDW", "HW"),
    "rating":   ("RATING", "FIRE"),
    "remarks":  ("REMARKS", "NOTES", "COMMENTS"),
}


def _records_from_table(headers: list[str], data_rows: list[list[str]],
                          page_index: int) -> list[DoorRecord]:
    """Convert one table's rows to :class:`DoorRecord` instances."""
    idx = {k: _header_index(headers, v) for k, v in _HEADERS.items()}
    records: list[DoorRecord] = []
    for row in data_rows:
        if not row:
            continue
        mark = _cell(row, idx["mark"])
        if not mark:
            continue
        # Filter out rows whose first column is obviously not a door tag
        # (sub-headers and continuation rows that survive grid extraction).
        if not _DOOR_TAG_RE.match(mark) and " " in mark:
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

        records.append(DoorRecord(
            mark=mark,
            type=_cell(row, idx["type"]),
            width_in=width_in,
            height_in=height_in,
            thickness_in=parse_dimension(_cell(row, idx["thick"])),
            width_raw=width_raw,
            height_raw=height_raw,
            material=_cell(row, idx["material"]),
            frame=_cell(row, idx["frame"]),
            hardware_set=_cell(row, idx["hdw"]),
            fire_rating=_cell(row, idx["rating"]),
            remarks=_cell(row, idx["remarks"]),
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Text-cluster fallback (used when find_tables() yields no door table)
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
        if header_row is None and _looks_like_door_header(cells):
            header_row = cells
            continue
        if header_row is not None and cells and any(_DOOR_TAG_RE.match(c) for c in cells[:2]):
            data_rows.append(cells)
    if header_row and data_rows:
        return header_row, data_rows
    return None


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _score(has_phrase: bool, tables_found: int, records: list[DoorRecord]) -> float:
    """0.40 for the phrase; 0.30 for a door-shaped table; 0.20 if any record
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


def extract_door_schedule_from_page(page: "fitz.Page",
                                       page_index: int = 0) -> DoorScheduleResult:
    """Extract the door schedule (if any) from a single PyMuPDF page."""
    text = page.get_text("text") or ""
    has_phrase = "DOOR SCHEDULE" in text.upper()

    all_records: list[DoorRecord] = []
    header_debug: list[str] = []
    door_tables_found = 0

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
        if not _looks_like_door_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if records:
            door_tables_found += 1
            header_debug.append(" | ".join(headers))
            all_records.extend(records)

    if not all_records:
        fallback = _cluster_lines_to_table(page)
        if fallback is not None:
            headers, data_rows = fallback
            records = _records_from_table(headers, data_rows, page_index)
            if records:
                door_tables_found += 1
                header_debug.append(" | ".join(headers))
                all_records.extend(records)

    return DoorScheduleResult(
        pages=[page_index] if all_records else [],
        doors=all_records,
        confidence=round(_score(has_phrase, door_tables_found, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_door_schedule(pdf_path: Path, page_index: int) -> DoorScheduleResult:
    """Run the door-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_door_schedule_from_page(doc[page_index], page_index)


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: DoorScheduleResult):
    """Return a :class:`core.schemas.DoorScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.DoorScheduleResult(
        pages=list(result.pages),
        doors=[
            S.DoorRecord(
                mark=d.mark,
                type=d.type,
                width_in=d.width_in,
                height_in=d.height_in,
                thickness_in=d.thickness_in,
                width_raw=d.width_raw,
                height_raw=d.height_raw,
                material=d.material,
                frame=d.frame,
                hardware_set=d.hardware_set,
                fire_rating=d.fire_rating,
                remarks=d.remarks,
                source_page=d.source_page,
            )
            for d in result.doors
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
