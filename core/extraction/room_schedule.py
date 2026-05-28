"""Deterministic room-schedule extraction (Phase T5).

Room schedules enumerate every room on a project with its **area**,
**perimeter** (when given), **ceiling height**, and optional occupancy
classification. They are the missing link between the finish schedule
(:mod:`core.extraction.finish_schedule`, Phase T4) — which tells us
*which* finishes go on *which* surfaces but emits ``quantity=0.0`` —
and a priced takeoff that needs the real square-footage to multiply.

Combined-schedule discriminator (Option A in the brief). Many
architects bundle ROOM + FINISH columns into a single
``ROOM FINISH SCHEDULE``. Rather than extending the finish extractor
to also carry ``area_sf``, this module runs **alongside** the finish
extractor: BOTH detectors fire on the same combined-schedule page and
contribute records independently. The two record sets are joined at
back-fill time (:mod:`core.extraction.takeoff_backfill`) by
``room_number``. This keeps the two extractors independently testable
and matches the door-vs-window precedence pattern (separate extractors
with disjoint responsibilities).

Detection signals (need ≥3):

1. Phrase ``ROOM SCHEDULE`` (rare) OR ``ROOM FINISH SCHEDULE`` on the
   page.
2. A ``ROOM #`` / ``ROOM NO`` / ``NUMBER`` column.
3. A ``ROOM NAME`` / ``NAME`` column.
4. An ``AREA`` / ``SF`` / ``AREA (SF)`` column — the primary
   deliverable that finish schedules without geometry don't carry.
5. A ``CLG HT`` / ``CEILING HEIGHT`` / ``HEIGHT`` column.

The ``AREA`` / ``SF`` column is the strongest discriminator: a finish
schedule does not normally carry area, so its presence is the cheap
signal that a room schedule (or combined room+finish schedule) is
present.

Architectural pattern mirrors :mod:`core.extraction.finish_schedule`:
pure functions of a ``Path`` + page index (or a ``fitz.Page``),
internal dataclasses with a ``to_schema()`` bridge to the Pydantic
models on :mod:`core.schemas`, and a confidence rubric.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF

from .door_schedule import _header_index_excluding, parse_dimension

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class RoomRecord:
    """One room's geometry pulled off a room-schedule table.

    ``area_sf`` is the primary deliverable that the T5 back-fill
    consumes. ``perimeter_lf`` is optional — many schedules don't
    publish it but when present it lets us bypass the ``4 * sqrt(area)``
    square-room fallback for base and wall computations.
    """

    room_number: str
    room_name: str | None = None
    area_sf: float | None = None
    perimeter_lf: float | None = None
    ceiling_height_ft: float | None = None
    ceiling_height_raw: str | None = None
    occupancy_type: str | None = None
    notes: str | None = None
    raw_cells: dict[str, str] = field(default_factory=dict)
    source_page: int = 0


@dataclass
class RoomScheduleResult:
    """Aggregate room-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    rooms: list[RoomRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


_ROOM_TAG_RE = re.compile(r"^\s*[A-Z]{0,2}\d{1,4}[A-Z]?\s*$")


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_room_header(headers: Iterable[str]) -> bool:
    """Does this row look like a room-schedule header?

    Requires ≥3 signals together. ``AREA`` / ``SF`` is treated as the
    primary discriminator — a finish-only schedule does not carry it,
    so its presence is the cheap signal that distinguishes a room
    schedule (or combined room+finish schedule) from a pure finish
    schedule.

    Door-specific (``HARDWARE`` / ``FRAME`` / ``HDW``) and
    window-specific (``GLAZING`` / ``OPERATION`` / ``SHGC`` /
    ``SILL``) signals actively disqualify the header — a row carrying
    those is a door or window schedule even if it happens to overlap
    on ``ROOM`` keywords (rare but seen).
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    disqualifiers = {
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "OPER",
        "SHGC", "UFACTOR", "UVALUE", "SILL", "RATING",
    }
    if words & disqualifiers:
        return False

    has_room = bool(words & {"ROOM", "RM", "NUMBER", "NO"})
    has_name = bool(words & {"NAME", "DESCRIPTION", "DESC"})
    has_area = bool(words & {"AREA", "SF", "SQFT", "SQ", "FT", "FOOTAGE"})
    has_height = bool(words & {"HEIGHT", "HT", "CLG", "CEILING"})
    has_occupancy = bool(words & {"OCCUPANCY", "OCC", "USE", "TYPE"})

    signals = sum((has_room, has_name, has_area, has_height, has_occupancy))
    return signals >= 3 and has_room and has_area


def detect_room_schedule(page: "fitz.Page") -> bool:
    """True when the page very likely contains a room schedule.

    Two cheap signals: literal ``ROOM SCHEDULE`` in page text (rare;
    ``ROOM FINISH SCHEDULE`` also counts because combined schedules
    are common), OR a room-shaped header row on any detected table.
    Either suffices.
    """
    text = (page.get_text("text") or "").upper()
    if "ROOM SCHEDULE" in text or "ROOM FINISH SCHEDULE" in text:
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
        if _looks_like_room_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Cell parsing
# ---------------------------------------------------------------------------


# Area cells are bare numbers, optionally with a unit suffix:
# ``180``, ``180.5``, ``180 SF``, ``180 sq ft``, ``180.5 SQFT``,
# ``1,234.5``. We strip commas + the unit suffix and parse.
_AREA_RE = re.compile(
    r"^\s*([\d,]+(?:\.\d+)?)\s*(?:SF|SQ\s*FT|SQFT|FT2|FT\^2|S\.F\.)?\s*$",
    re.IGNORECASE,
)
# Perimeter cells: ``54 LF``, ``54.5 LF``, ``54`` bare. Same shape.
_PERIM_RE = re.compile(
    r"^\s*([\d,]+(?:\.\d+)?)\s*(?:LF|LIN\s*FT|LINFT|L\.F\.)?\s*$",
    re.IGNORECASE,
)


def _parse_area(raw: str | None) -> float | None:
    """Parse an area cell (``180``, ``180.5``, ``180 SF``) to float square-feet."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _AREA_RE.match(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:  # pragma: no cover - defensive
        return None


def _parse_perimeter(raw: str | None) -> float | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _PERIM_RE.match(text)
    if not m:
        return None
    try:
        return float(m.group(1).replace(",", ""))
    except ValueError:  # pragma: no cover - defensive
        return None


# Ceiling-height parsing — supports the common shapes seen on real
# schedules: ``9'-0"``, ``10'``, ``9.5``, ``9.5 FT``. Reuses
# :func:`core.extraction.door_schedule.parse_dimension` (returns
# **inches**) and converts to feet, then falls back to a decimal
# parser for the bare-number / FT-suffix case which parse_dimension
# does not accept (intentionally rejects bare integers).
_CLG_DECIMAL_RE = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:'|FT|FEET)?\s*$", re.IGNORECASE,
)


def _parse_ceiling_height(raw: str | None) -> float | None:
    """Parse a ceiling-height cell to feet.

    Strategy: try :func:`parse_dimension` first (handles ``9'-0"``,
    ``9'``, ``9' - 6 1/2"``); converts the inches return value to
    feet. Falls back to a bare-decimal parser for the ``9.5`` /
    ``9.5 FT`` shapes that ``parse_dimension`` deliberately rejects
    in a schedule context.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    inches = parse_dimension(text)
    if inches is not None:
        return round(inches / 12.0, 3)
    m = _CLG_DECIMAL_RE.match(text)
    if m:
        try:
            return round(float(m.group(1)), 3)
        except ValueError:  # pragma: no cover - defensive
            return None
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "room_number":     ("ROOM", "RM", "NUMBER", "NO"),
    "room_name":       ("NAME", "DESCRIPTION", "DESC"),
    "area":            ("AREA", "SF", "SQFT", "FOOTAGE"),
    "perimeter":       ("PERIMETER", "PERIM", "LF"),
    "ceiling_height":  ("HEIGHT", "HT", "CEILING HEIGHT", "CLG HT", "CEILING", "CLG"),
    "occupancy":       ("OCCUPANCY", "OCC", "USE", "TYPE"),
    "notes":           ("REMARKS", "NOTES", "COMMENTS"),
}


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


def _records_from_table(headers: list[str], data_rows: list[list[str]],
                          page_index: int) -> list[RoomRecord]:
    """Convert one table's rows to :class:`RoomRecord` instances.

    Phase T5.1 propagation: when a schedule orders ``ROOM NAME``
    BEFORE the room-number column, the substring ``ROOM`` candidate
    on ``_HEADERS["room_number"]`` used to land ``room_number`` on
    the ``ROOM NAME`` column. Fix: pin ``room_name`` first; re-pick
    ``room_number`` with the room-name column excluded so each field
    maps to its own column.
    """
    idx = {k: _header_index(headers, v) for k, v in _HEADERS.items()}
    if idx["room_name"] is not None and idx["room_number"] == idx["room_name"]:
        idx["room_number"] = _header_index_excluding(
            headers, _HEADERS["room_number"],
            exclude={idx["room_name"]},
        )
    records: list[RoomRecord] = []
    for row in data_rows:
        if not row:
            continue
        room_number = _cell(row, idx["room_number"])
        if not room_number:
            continue
        # Filter out rows whose first column is obviously not a room
        # tag (sub-headers / continuation rows that survive grid extraction).
        if not _ROOM_TAG_RE.match(room_number) and " " in room_number:
            continue

        raw_cells: dict[str, str] = {}
        for h_idx, h in enumerate(headers):
            v = _cell(row, h_idx)
            if h and v:
                raw_cells[h] = v

        ceiling_raw = _cell(row, idx["ceiling_height"])

        records.append(RoomRecord(
            room_number=room_number,
            room_name=_cell(row, idx["room_name"]),
            area_sf=_parse_area(_cell(row, idx["area"])),
            perimeter_lf=_parse_perimeter(_cell(row, idx["perimeter"])),
            ceiling_height_ft=_parse_ceiling_height(ceiling_raw),
            ceiling_height_raw=ceiling_raw,
            occupancy_type=_cell(row, idx["occupancy"]),
            notes=_cell(row, idx["notes"]),
            raw_cells=raw_cells,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Text-cluster fallback
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
        if header_row is None and _looks_like_room_header(cells):
            header_row = cells
            continue
        if header_row is not None and cells and any(_ROOM_TAG_RE.match(c) for c in cells[:2]):
            data_rows.append(cells)
    if header_row and data_rows:
        return header_row, data_rows
    return None


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _score(has_phrase: bool, tables_found: int, records: list[RoomRecord]) -> float:
    """0.40 for the phrase; 0.30 for a room-shaped table; 0.20 if any record
    has area + ceiling height populated; 0.10 for >= 5 records. Clamped to 1.0."""
    if not records and tables_found == 0:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    if tables_found >= 1:
        score += 0.30
    if any(r.area_sf is not None and r.ceiling_height_ft is not None for r in records):
        score += 0.20
    if len(records) >= 5:
        score += 0.10
    return min(score, 1.0)


def extract_room_schedule_from_page(page: "fitz.Page",
                                       page_index: int = 0) -> RoomScheduleResult:
    """Extract the room schedule (if any) from a single PyMuPDF page."""
    text = (page.get_text("text") or "").upper()
    has_phrase = "ROOM SCHEDULE" in text or "ROOM FINISH SCHEDULE" in text

    all_records: list[RoomRecord] = []
    header_debug: list[str] = []
    room_tables_found = 0

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
        if not _looks_like_room_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if records:
            room_tables_found += 1
            header_debug.append(" | ".join(headers))
            all_records.extend(records)

    if not all_records:
        fallback = _cluster_lines_to_table(page)
        if fallback is not None:
            headers, data_rows = fallback
            records = _records_from_table(headers, data_rows, page_index)
            if records:
                room_tables_found += 1
                header_debug.append(" | ".join(headers))
                all_records.extend(records)

    return RoomScheduleResult(
        pages=[page_index] if all_records else [],
        rooms=all_records,
        confidence=round(_score(has_phrase, room_tables_found, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_room_schedule(pdf_path: Path, page_index: int) -> RoomScheduleResult:
    """Run the room-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_room_schedule_from_page(doc[page_index], page_index)


# ---------------------------------------------------------------------------
# Multi-page merge helper (used by core.takeoff.reconcile)
# ---------------------------------------------------------------------------


def merge_room_schedules(results: Iterable[Any]) -> Any:
    """Combine room schedules from multiple pages / sheets into one.

    Accepts a mix of internal dataclass and Pydantic-schema room
    schedules — fields read are common to both via duck-typing
    (``rooms``, ``pages``, ``confidence``, ``raw_table_text``; each
    room has ``room_number``, ``room_name``, ``area_sf``,
    ``perimeter_lf``, ``ceiling_height_ft``, ``ceiling_height_raw``,
    ``occupancy_type``, ``notes``, ``raw_cells``, ``source_page``).

    Returns the **Pydantic** ``core.schemas.RoomScheduleResult`` so the
    output is suitable for downstream callers that work in the schema
    layer (the Phase T5 back-fill). When the input contains zero rooms
    after merging, the return is still a valid empty
    ``RoomScheduleResult``.

    Per-room dedupe rule: when the same ``room_number`` appears in
    more than one schedule, the record with more populated fields
    wins; ties keep the first-seen order so output is deterministic.
    The merged result's ``pages`` list is the deduped union of the
    inputs; ``confidence`` is the max across inputs;
    ``raw_table_text`` is the joined non-empty debug strings.

    Records WITHOUT a room number are dropped (defensive — should
    never happen because the extractor requires the room-number cell).
    """
    from core import schemas as S

    by_room: dict[str, Any] = {}
    order: list[str] = []
    pages: list[int] = []
    confidence = 0.0
    debug: list[str] = []

    for r in results:
        if r is None:
            continue
        confidence = max(confidence, float(getattr(r, "confidence", 0.0) or 0.0))
        for pg in (getattr(r, "pages", None) or []):
            if pg not in pages:
                pages.append(pg)
        text = getattr(r, "raw_table_text", "") or ""
        if text:
            debug.append(text)
        for room in (getattr(r, "rooms", None) or []):
            key = (getattr(room, "room_number", "") or "").strip()
            if not key:
                continue
            existing = by_room.get(key)
            if existing is None:
                by_room[key] = room
                order.append(key)
                continue
            if _populated_score(room) > _populated_score(existing):
                by_room[key] = room

    return S.RoomScheduleResult(
        pages=pages,
        rooms=[_to_schema_room(by_room[k]) for k in order],
        confidence=round(confidence, 4),
        raw_table_text="\n".join(debug),
    )


def _populated_score(record: Any) -> int:
    """How many useful fields does this room carry? Duck-typed."""
    return sum(
        1 for v in (
            getattr(record, "room_name", None),
            getattr(record, "area_sf", None),
            getattr(record, "perimeter_lf", None),
            getattr(record, "ceiling_height_ft", None),
            getattr(record, "occupancy_type", None),
        ) if v is not None and v != ""
    )


def _to_schema_room(room: Any) -> Any:
    """Coerce an internal dataclass OR Pydantic RoomRecord to the schema model."""
    from core import schemas as S

    if isinstance(room, S.RoomRecord):
        return room
    return S.RoomRecord(
        room_number=getattr(room, "room_number", ""),
        room_name=getattr(room, "room_name", None),
        area_sf=getattr(room, "area_sf", None),
        perimeter_lf=getattr(room, "perimeter_lf", None),
        ceiling_height_ft=getattr(room, "ceiling_height_ft", None),
        ceiling_height_raw=getattr(room, "ceiling_height_raw", None),
        occupancy_type=getattr(room, "occupancy_type", None),
        notes=getattr(room, "notes", None),
        raw_cells=dict(getattr(room, "raw_cells", None) or {}),
        source_page=getattr(room, "source_page", 0),
    )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: RoomScheduleResult):
    """Return a :class:`core.schemas.RoomScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.RoomScheduleResult(
        pages=list(result.pages),
        rooms=[
            S.RoomRecord(
                room_number=r.room_number,
                room_name=r.room_name,
                area_sf=r.area_sf,
                perimeter_lf=r.perimeter_lf,
                ceiling_height_ft=r.ceiling_height_ft,
                ceiling_height_raw=r.ceiling_height_raw,
                occupancy_type=r.occupancy_type,
                notes=r.notes,
                raw_cells=dict(r.raw_cells),
                source_page=r.source_page,
            )
            for r in result.rooms
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
