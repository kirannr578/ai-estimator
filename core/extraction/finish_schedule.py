"""Deterministic finish-schedule extraction (Phase T4).

Finish schedules are the highest-leverage schedule artefact on an
A-series sheet: a table that enumerates every interior room and its
floor / base / wall / ceiling finishes (``VCT-1``, ``RB-1``, ``PT-1``,
``ACT-1``, ``GYP``...). Unlike door + window schedules where each row
maps 1:1 to a ``TakeoffItem``, each ``FinishRecord`` fans out into
**3-7 TakeoffItems** downstream (one per finished surface) — so this
extractor is the input gate for floor finishes (CSI 09 6x), wall
finishes (09 7x and 09 91 paint), and ceiling finishes (09 5x).

A typical commercial finish schedule has columns:
``ROOM #, ROOM NAME, FLOOR, BASE, WALL N/S/E/W (or single ``WALL``),
CEILING, CEILING HEIGHT, REMARKS``. Some schedules use a single
``WALL`` column when finishes are uniform; the extractor accepts both
shapes.

Architectural pattern mirrors :mod:`core.extraction.window_schedule`:
pure functions of a ``Path`` + page index (or a ``fitz.Page``), internal
dataclasses with a ``to_schema()`` bridge to the Pydantic models on
:mod:`core.schemas`, and a confidence rubric. Runs **alongside** (never
instead of) the existing F3 prepass, and **after** the door + window
extractors per the discriminator rule below.

Door-vs-window-vs-finish discriminator (critical):
Finish schedules share the ``ROOM`` keyword with room schedules but the
distinguishing signal is unique ``FLOOR`` + ``CEILING`` columns. Door
schedules carry ``HARDWARE`` / ``FRAME``; window schedules carry
``GLAZING`` / ``OPERATION`` / ``SHGC``. The header heuristic in
:func:`_looks_like_finish_header` requires a finish-specific signal
(``FLOOR`` or ``CEILING``). When a page matches both the door OR window
detector AND the finish detector, door/window precedence wins (the
older, more-validated extractors fired first; the hook in
:mod:`core.extraction.drawing_prepass` skips the finish pass for that
page).
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

from .door_schedule import _header_index_excluding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class FinishRecord:
    """One room's finishes pulled off a finish-schedule table.

    ``wall_finishes`` is a dict keyed by compass direction (``"N"`` /
    ``"S"`` / ``"E"`` / ``"W"``). When the schedule uses a single
    ``WALL`` column the dict is populated with a single ``"ALL"`` key,
    which the synthesiser collapses into one wall TakeoffItem rather
    than four. Empty / missing wall cells are omitted (no ``None``
    entries land in the dict).
    """

    room_number: str
    room_name: str | None = None
    floor_finish: str | None = None
    base_finish: str | None = None
    wall_finishes: dict[str, str] = field(default_factory=dict)
    ceiling_finish: str | None = None
    ceiling_height_ft: float | None = None
    ceiling_height_raw: str | None = None
    area_sf: float | None = None     # rarely on the finish schedule itself; left
                                       # optional so a future room-area cross-ref
                                       # (Phase T5) can populate without breaking
                                       # the dataclass shape.
    remarks: str | None = None
    raw_cells: dict[str, str] = field(default_factory=dict)
    source_page: int = 0


@dataclass
class FinishScheduleResult:
    """Aggregate finish-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    rooms: list[FinishRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Room-number tag pattern. Real-world room numbers are 1-4 digits with
# optional single-letter suffix (e.g. ``101``, ``101A``, ``M101``).
# Accept a 1-2 character leading prefix (``M101``, ``LL101``) and an
# optional trailing single-letter suffix.
_ROOM_TAG_RE = re.compile(r"^\s*[A-Z]{0,2}\d{1,4}[A-Z]?\s*$")


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_finish_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a finish-schedule header row?

    Requires three signals together to avoid false-positives on
    neighbouring door / window / room schedules:

    1. a room column (``ROOM`` / ``RM`` / ``NUMBER`` / ``NO``),
    2. at least one **finish-specific** column (``FLOOR`` / ``CEILING``
       / ``BASE`` / ``WALLS``) — the discriminator vs door/window,
    3. at least one supporting column (``FINISH`` / ``WALL`` /
       ``REMARKS`` / ``HEIGHT`` / ``NAME``).

    Door-specific (``HARDWARE`` / ``FRAME``) and window-specific
    (``GLAZING`` / ``OPERATION`` / ``SHGC`` / ``SILL``) signals
    actively disqualify the header even when the other classes match —
    this is the belt-and-braces discriminator on top of the
    door/window-precedence rule at the dispatcher level.
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    # Hard-reject if the row carries a door-/window-specific column.
    disqualifiers = {
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "OPER",
        "SHGC", "UFACTOR", "UVALUE", "SILL", "RATING",
    }
    if words & disqualifiers:
        return False
    has_room = bool(words & {"ROOM", "RM", "NUMBER", "NO"})
    finish_specific = words & {"FLOOR", "CEILING", "CLG", "BASE"}
    supporting = words & {
        "FINISH", "FINISHES", "WALL", "WALLS", "REMARKS", "NOTES",
        "HEIGHT", "NAME",
    }
    return has_room and bool(finish_specific) and bool(supporting)


def detect_finish_schedule(page: "fitz.Page") -> bool:
    """True when the page very likely contains a finish schedule.

    Two cheap signals: literal ``FINISH SCHEDULE`` or
    ``ROOM FINISH SCHEDULE`` in page text, OR a finish-shaped header
    row on any detected table. Either suffices.
    """
    text = (page.get_text("text") or "").upper()
    if "ROOM FINISH SCHEDULE" in text or "FINISH SCHEDULE" in text:
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
        if _looks_like_finish_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Finish-code parsing
# ---------------------------------------------------------------------------


# A finish code is one or more letters optionally followed by a digit
# suffix (``VCT``, ``VCT-1``, ``PT-1``, ``ACT-1``, ``CPT-2A``, ``POL CONC``).
# We split on the first ``-`` / ``_`` / whitespace to separate category
# from variant.
_FINISH_CODE_RE = re.compile(r"^\s*([A-Z][A-Z\s]*?)[\s\-_]+([A-Z0-9]+)\s*$",
                              re.IGNORECASE)


def parse_finish_code(s: str | None) -> tuple[str | None, str | None]:
    """Best-effort split of a finish code into ``(category, variant)``.

    Returns ``(None, None)`` for empty input. Returns
    ``(category, None)`` when the cell is a bare family token with no
    variant suffix (``"VCT"`` → ``("VCT", None)``). Used downstream by
    the synthesiser for CSI family mapping.

    Examples::

        "VCT-1"     → ("VCT", "1")
        "VCT 1"     → ("VCT", "1")
        "POL-CONC"  → ("POL", "CONC")
        "PT-1A"     → ("PT", "1A")
        "ACT"       → ("ACT", None)
        ""          → (None, None)
    """
    if s is None:
        return None, None
    text = str(s).strip()
    if not text:
        return None, None
    m = _FINISH_CODE_RE.match(text)
    if m:
        category = re.sub(r"\s+", " ", m.group(1).strip()).upper()
        variant = m.group(2).strip().upper()
        return category, variant
    # No variant suffix — return the whole token as the category.
    return text.upper(), None


# ---------------------------------------------------------------------------
# Numeric (ceiling height) parsing
# ---------------------------------------------------------------------------


_FT_DECIMAL_RE = re.compile(r"^\s*(\d+(?:\.\d+)?)\s*(?:'|FT|FEET)?\s*$",
                              re.IGNORECASE)
_FT_INCH_RE = re.compile(r"^\s*(\d+)\s*'\s*-?\s*(\d+)?\s*(?:\"|IN)?\s*$",
                          re.IGNORECASE)


def _parse_ceiling_height(raw: str | None) -> float | None:
    """Parse a ceiling-height cell (``9'-0"``, ``9'``, ``9.5``) to feet."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if (m := _FT_INCH_RE.match(text)):
        feet = float(m.group(1))
        inches = float(m.group(2) or 0)
        return round(feet + inches / 12.0, 3)
    if (m := _FT_DECIMAL_RE.match(text)):
        return round(float(m.group(1)), 3)
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    # Room identification
    "room_number": ("ROOM", "RM", "NUMBER", "NO"),
    "room_name":   ("NAME", "DESCRIPTION", "DESC"),
    # Surfaces
    "floor":   ("FLOOR", "FLR", "FL"),
    "base":    ("BASE", "BS"),
    "wall":    ("WALL", "WALLS"),
    "wall_n":  ("N", "NORTH"),
    "wall_s":  ("S", "SOUTH"),
    "wall_e":  ("E", "EAST"),
    "wall_w":  ("W", "WEST"),
    "ceiling": ("CEILING", "CLG", "CEIL"),
    # Misc
    "ceiling_height": ("HEIGHT", "HT", "CEILING HEIGHT", "CLG HT"),
    "remarks":        ("REMARKS", "NOTES", "COMMENTS"),
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


def _wall_compass_indices(headers: list[str]) -> dict[str, int]:
    """Locate compass-direction wall sub-columns by an exact-token rule.

    ``WALL`` (parent) often appears as a top-row span over four
    sub-columns labelled simply ``N`` / ``S`` / ``E`` / ``W`` (or
    ``NORTH`` / ``SOUTH`` / ...). We accept either form. The returned
    dict only contains directions whose header was found.
    """
    out: dict[str, int] = {}
    candidates: dict[str, tuple[str, ...]] = {
        "N": ("N", "NORTH"),
        "S": ("S", "SOUTH"),
        "E": ("E", "EAST"),
        "W": ("W", "WEST"),
    }
    for direction, words in candidates.items():
        for i, h in enumerate(headers):
            tokens = set(re.findall(r"[A-Z]+", (h or "").upper()))
            if any(w in tokens for w in words):
                out[direction] = i
                break
    return out


def _cell(row: list[str], idx: int | None) -> str | None:
    if idx is None or idx < 0 or idx >= len(row):
        return None
    return (row[idx] or "").strip() or None


def _records_from_table(headers: list[str], data_rows: list[list[str]],
                          page_index: int) -> list[FinishRecord]:
    """Convert one table's rows to :class:`FinishRecord` instances.

    Phase T5.1 propagation: two known substring-collision classes are
    fixed here using the :func:`_header_index_excluding` helper Worker
    U introduced in :mod:`core.extraction.door_schedule`:

    1. ``CEILING HEIGHT`` (or ``CLG HT``) carries both the substring
       ``CEILING`` (a candidate of ``_HEADERS["ceiling"]``) and the
       substring ``HEIGHT`` (a candidate of
       ``_HEADERS["ceiling_height"]``). Without the fix the
       substring-tolerant matcher landed ``ceiling`` on the
       ceiling-height column whenever it appeared first in the row.
       Fix: pin ``ceiling_height`` first; re-pick ``ceiling`` with the
       ceiling-height column excluded.

    2. ``ROOM NAME`` ordered BEFORE ``ROOM NUMBER`` used to land
       ``room_number`` on the ``ROOM NAME`` column because the
       substring ``ROOM`` (a candidate of ``_HEADERS["room_number"]``)
       matched both. Fix: pin ``room_name`` first; re-pick
       ``room_number`` with the room-name column excluded.
    """
    # 1. Pin the columns whose names provide their own discriminator
    # word (``NAME``, ``HEIGHT``/``HT``) — these are the ones that
    # could later "steal" their column via substring match by the
    # less-specific candidates.
    room_name_idx = _header_index(headers, _HEADERS["room_name"])
    ceiling_height_idx = _header_index(headers, _HEADERS["ceiling_height"])

    # 2. Pick everything else with the collision-prone columns excluded
    # so the room/ceiling candidates don't accidentally land on the
    # name/height columns they were already pinned to.
    room_number_idx = _header_index_excluding(
        headers, _HEADERS["room_number"],
        exclude={i for i in (room_name_idx, ceiling_height_idx) if i is not None},
    )
    ceiling_idx = _header_index_excluding(
        headers, _HEADERS["ceiling"],
        exclude={i for i in (ceiling_height_idx,) if i is not None},
    )

    idx = {
        "room_number": room_number_idx,
        "room_name":   room_name_idx,
        "floor":       _header_index(headers, _HEADERS["floor"]),
        "base":        _header_index(headers, _HEADERS["base"]),
        "wall":        _header_index(headers, _HEADERS["wall"]),
        "ceiling":     ceiling_idx,
        "ceiling_height": ceiling_height_idx,
        "remarks":     _header_index(headers, _HEADERS["remarks"]),
    }
    compass = _wall_compass_indices(headers)

    records: list[FinishRecord] = []
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

        wall_finishes: dict[str, str] = {}
        if compass:
            # Compass-direction wall sub-columns take precedence over the
            # single ``WALL`` column when both are present.
            for direction, col_idx in compass.items():
                v = _cell(row, col_idx)
                if v:
                    wall_finishes[direction] = v
        if not wall_finishes:
            wall_all = _cell(row, idx["wall"])
            if wall_all:
                wall_finishes["ALL"] = wall_all

        raw_cells: dict[str, str] = {}
        for h_idx, h in enumerate(headers):
            v = _cell(row, h_idx)
            if h and v:
                raw_cells[h] = v

        ceiling_raw = _cell(row, idx["ceiling_height"])

        records.append(FinishRecord(
            room_number=room_number,
            room_name=_cell(row, idx["room_name"]),
            floor_finish=_cell(row, idx["floor"]),
            base_finish=_cell(row, idx["base"]),
            wall_finishes=wall_finishes,
            ceiling_finish=_cell(row, idx["ceiling"]),
            ceiling_height_ft=_parse_ceiling_height(ceiling_raw),
            ceiling_height_raw=ceiling_raw,
            remarks=_cell(row, idx["remarks"]),
            raw_cells=raw_cells,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Text-cluster fallback (used when find_tables() yields no finish table)
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
        if header_row is None and _looks_like_finish_header(cells):
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


def _score(has_phrase: bool, tables_found: int, records: list[FinishRecord]) -> float:
    """0.40 for the phrase; 0.30 for a finish-shaped table; 0.20 if any record
    has at least 3 of (floor, base, wall, ceiling) populated; 0.10 for >= 5
    records. Clamped to 1.0."""
    if not records and tables_found == 0:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    if tables_found >= 1:
        score += 0.30
    has_full = any(
        sum(bool(x) for x in (
            r.floor_finish, r.base_finish, r.wall_finishes, r.ceiling_finish,
        )) >= 3
        for r in records
    )
    if has_full:
        score += 0.20
    if len(records) >= 5:
        score += 0.10
    return min(score, 1.0)


def extract_finish_schedule_from_page(page: "fitz.Page",
                                         page_index: int = 0) -> FinishScheduleResult:
    """Extract the finish schedule (if any) from a single PyMuPDF page."""
    text = (page.get_text("text") or "").upper()
    has_phrase = "FINISH SCHEDULE" in text  # also catches "ROOM FINISH SCHEDULE"

    all_records: list[FinishRecord] = []
    header_debug: list[str] = []
    finish_tables_found = 0

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
        if not _looks_like_finish_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if records:
            finish_tables_found += 1
            header_debug.append(" | ".join(headers))
            all_records.extend(records)

    if not all_records:
        fallback = _cluster_lines_to_table(page)
        if fallback is not None:
            headers, data_rows = fallback
            records = _records_from_table(headers, data_rows, page_index)
            if records:
                finish_tables_found += 1
                header_debug.append(" | ".join(headers))
                all_records.extend(records)

    return FinishScheduleResult(
        pages=[page_index] if all_records else [],
        rooms=all_records,
        confidence=round(_score(has_phrase, finish_tables_found, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_finish_schedule(pdf_path: Path, page_index: int) -> FinishScheduleResult:
    """Run the finish-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_finish_schedule_from_page(doc[page_index], page_index)


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: FinishScheduleResult):
    """Return a :class:`core.schemas.FinishScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.FinishScheduleResult(
        pages=list(result.pages),
        rooms=[
            S.FinishRecord(
                room_number=r.room_number,
                room_name=r.room_name,
                floor_finish=r.floor_finish,
                base_finish=r.base_finish,
                wall_finishes=dict(r.wall_finishes),
                ceiling_finish=r.ceiling_finish,
                ceiling_height_ft=r.ceiling_height_ft,
                ceiling_height_raw=r.ceiling_height_raw,
                area_sf=r.area_sf,
                remarks=r.remarks,
                raw_cells=dict(r.raw_cells),
                source_page=r.source_page,
            )
            for r in result.rooms
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
