"""Deterministic pre-pass for drawing PDFs (F3).

The drawing pipeline historically dispatches every architectural / structural
page to the vision LLM, which is expensive *and* less reliable than just
reading the vector text when the vector text is already there. This module
walks each page with PyMuPDF and pulls out the three things that are
unambiguously present in most real construction drawings:

  * **Title block** — `PROJECT NAME`, `SHEET NO`, `SCALE`, `DATE`, ...
  * **Dimensions** — feet-inches, decimal feet, plain inches, metric
  * **Schedule tables** — door / window / room-finish / generic

The result is bundled into a :class:`DrawingPrepassResult` together with a
heuristic confidence score (0..1). When confidence clears the configured
threshold (`CONFIDENCE_THRESHOLD`, default 0.65), :func:`extract_sheet` in
``core.extractors`` builds a `SheetExtraction` directly from the snapshot
and skips the vision-LLM call entirely; when it doesn't, the snapshot is
fed to the LLM as "deterministic context" so the model doesn't re-extract
what we already know.

Design notes:

* Uses PyMuPDF (`fitz`) exclusively — already a project dep, no new ones.
* All public helpers are pure functions of a `Path`; no LLM, no network,
  no global state. Easy to test with a synthetic in-memory PDF.
* Patterns inspired by the `datadrivenconstruction/drawing-analyzer` skill
  (MIT) but reimplemented in this project's style.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable

import fitz  # PyMuPDF

logger = logging.getLogger(__name__)

CONFIDENCE_THRESHOLD: float = 0.65


# ---------------------------------------------------------------------------
# Public dataclasses — mirrored by Pydantic models in `core.schemas`
# ---------------------------------------------------------------------------


@dataclass
class TitleBlockData:
    project_name: str | None = None
    project_number: str | None = None
    sheet_number: str | None = None        # e.g. "A101"
    sheet_title: str | None = None
    discipline: str | None = None          # "Architectural", "Structural", ...
    scale: str | None = None               # e.g. "1/4\" = 1'-0\""
    scale_factor: float | None = None      # paper inches per real-world inch
    date: str | None = None
    revision: str | None = None
    drawn_by: str | None = None
    checked_by: str | None = None


@dataclass
class Dimension:
    raw_text: str
    inches: float                          # normalized to inches
    kind: str                              # "feet-inches", "decimal-feet", "metric"


@dataclass
class ScheduleRow:
    columns: dict[str, str] = field(default_factory=dict)


@dataclass
class Schedule:
    kind: str                              # "door", "window", "room", "finish", "unknown"
    headers: list[str] = field(default_factory=list)
    rows: list[ScheduleRow] = field(default_factory=list)
    source_page: int = 0


@dataclass
class DrawingPrepassResult:
    title_block: TitleBlockData = field(default_factory=TitleBlockData)
    dimensions: list[Dimension] = field(default_factory=list)
    schedules: list[Schedule] = field(default_factory=list)
    quality_issues: list[str] = field(default_factory=list)
    confidence: float = 0.0                # 0..1
    # T1 — typed door-schedule pre-pass (populated alongside `schedules`
    # whenever a door schedule was detected on this page; None otherwise).
    # Typed `Any` here to avoid a circular import; concretely a
    # ``core.extraction.door_schedule.DoorScheduleResult`` or ``None``.
    door_schedule: Any = None
    # T2.5 — typed window-schedule pre-pass. Populated alongside the
    # door-schedule attachment whenever a window schedule was detected
    # AND the page wasn't already claimed by the door detector (the
    # door-precedence rule documented in ``window_schedule`` module).
    # Concretely a ``core.extraction.window_schedule.WindowScheduleResult``
    # or ``None``.
    window_schedule: Any = None
    # T4 — typed finish-schedule pre-pass. Populated alongside the
    # door/window attachments whenever a finish schedule was detected
    # AND the page wasn't already claimed by the door or window
    # detectors (door/window-precedence rule documented in
    # ``finish_schedule`` module). Concretely a
    # ``core.extraction.finish_schedule.FinishScheduleResult`` or
    # ``None``.
    finish_schedule: Any = None
    # T5 — typed room-schedule pre-pass. Populated whenever a room
    # schedule was detected. Runs in parallel with the finish detector
    # WITHOUT a precedence ordering (Option A from the T5 brief): a
    # combined ``ROOM FINISH SCHEDULE`` produces BOTH a finish and a
    # room result so the back-fill can join them by ``room_number``.
    # Door/window precedence still applies (a page already claimed by
    # the door/window detectors won't run the room detector).
    # Concretely a ``core.extraction.room_schedule.RoomScheduleResult``
    # or ``None``.
    room_schedule: Any = None
    # T2.6 — typed electrical-panel-schedule pre-pass. Populated
    # whenever an electrical panel schedule was detected on the page.
    # Runs INDEPENDENTLY of door / window / finish / room precedence:
    # panel schedules live on E-series sheets that those upstream
    # detectors never claim, so there is no scheduling conflict to
    # resolve. Concretely a
    # ``core.extraction.panel_schedule.PanelScheduleResult`` or
    # ``None``.
    panel_schedule: Any = None
    # T2.7 — typed lighting-fixture-schedule pre-pass. Populated
    # whenever a lighting-fixture schedule was detected on the page.
    # Runs INDEPENDENTLY of door / window / finish / room precedence
    # for the same reason as panel schedules (E-series sheets that
    # upstream detectors never claim). Runs ALONGSIDE the panel
    # detector — they target different table shapes on the same
    # sheet, so a combined ``Panel + Fixture Schedule`` page
    # produces both results. Concretely a
    # ``core.extraction.lighting_schedule.LightingScheduleResult``
    # or ``None``.
    lighting_schedule: Any = None
    # T2.8 — typed HVAC equipment-schedule pre-pass. Populated whenever
    # an HVAC equipment schedule was detected on the page. Runs
    # INDEPENDENTLY of door / window / finish / room precedence —
    # mechanical schedules live on M-series / H-series / MH-series
    # sheets that those upstream detectors never claim, same posture
    # as panels + lighting. Runs ALONGSIDE the panel + lighting
    # detectors (different table shapes, different sheets). Concretely
    # a ``core.extraction.hvac_schedule.HVACScheduleResult`` or
    # ``None``.
    hvac_schedule: Any = None
    # T2.9 — typed plumbing-fixture-schedule pre-pass. Populated
    # whenever a plumbing fixture schedule was detected on the page.
    # Runs INDEPENDENTLY of door / window / finish / room precedence
    # — plumbing schedules live on P-series sheets that those
    # upstream detectors never claim, same posture as panels +
    # lighting + HVAC.  Runs ALONGSIDE the panel + lighting + HVAC
    # detectors (different table shapes, different sheets → no
    # scheduling conflict).  Closes the Division 22+23+26 typed-
    # schedule trifecta entirely.  Concretely a
    # ``core.extraction.plumbing_schedule.PlumbingScheduleResult``
    # or ``None``.
    plumbing_schedule: Any = None


# ---------------------------------------------------------------------------
# Title-block extraction
# ---------------------------------------------------------------------------

# Field-label regexes. The label is matched case-insensitively and we accept
# either `:` or `-` (or whitespace alone) as the separator. The captured
# group is stripped and cleaned by the caller.
#
# Order matters: longer / more-specific labels first so e.g. "PROJECT NO"
# wins over the bare "PROJECT" prefix in `PROJECT NAME`.
_TITLE_BLOCK_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("project_number", re.compile(r"PROJECT\s+NO\.?\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("project_number", re.compile(r"PROJECT\s+#\s*[:\-]?\s*([^\n\r]+)", re.IGNORECASE)),
    ("project_number", re.compile(r"\bJOB\s+NO\.?\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("project_name",   re.compile(r"PROJECT(?:\s+NAME)?\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("sheet_number",   re.compile(r"SHEET\s+(?:NO\.?|NUMBER|#)\s*[:\-]?\s*([A-Z]{1,3}[-]?\d+(?:\.\d+)?[A-Z]?)", re.IGNORECASE)),
    ("sheet_title",    re.compile(r"SHEET\s+TITLE\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("scale",          re.compile(r"\bSCALE\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("date",           re.compile(r"\bDATE\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("revision",       re.compile(r"REVISION\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("revision",       re.compile(r"\bREV\.?\s+NO\.?\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("drawn_by",       re.compile(r"DRAWN\s+BY\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
    ("checked_by",     re.compile(r"CHECKED\s+BY\s*[:\-]\s*([^\n\r]+)", re.IGNORECASE)),
]

_DISCIPLINE_FROM_PREFIX = {
    "A":  "Architectural",
    "I":  "Interior",
    "S":  "Structural",
    "M":  "Mechanical",
    "E":  "Electrical",
    "P":  "Plumbing",
    "C":  "Civil",
    "L":  "Landscape",
    "F":  "Fire Protection",
    "FP": "Fire Protection",
    "T":  "Telecom",
    "G":  "General",
}


def _clean_field(raw: str) -> str:
    """Trim, collapse interior whitespace, and strip stray label tails."""
    text = raw.strip()
    # Many title blocks pack two fields on one line ("PROJECT NAME: Foo
    # SHEET NO: A101"); chop at the next ALL-CAPS label.
    text = re.split(r"\s{2,}[A-Z][A-Z ]{2,}\s*[:\-]", text)[0]
    return re.sub(r"\s+", " ", text).strip(" :-,;")


def _discipline_from_sheet_number(sheet_number: str | None) -> str | None:
    if not sheet_number:
        return None
    m = re.match(r"^([A-Z]{1,2})", sheet_number.strip().upper())
    if not m:
        return None
    prefix = m.group(1)
    # Prefer the two-letter prefix when it's known (e.g. "FP" for fire
    # protection); otherwise fall back to the one-letter form.
    if prefix in _DISCIPLINE_FROM_PREFIX:
        return _DISCIPLINE_FROM_PREFIX[prefix]
    return _DISCIPLINE_FROM_PREFIX.get(prefix[0])


# Scale-string parsing. Supports the conventions actually seen in the
# field; anything we can't parse is left as `scale_factor=None` and the
# raw string is preserved on `scale`.

_SCALE_FRAC_RE = re.compile(
    r"(\d+)\s*/\s*(\d+)\s*\"\s*=\s*(\d+)\s*'(?:\s*-?\s*(\d+)\s*\")?",
)
_SCALE_INCH_EQ_FT_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*\"\s*=\s*(\d+(?:\.\d+)?)\s*'",
)
_SCALE_METRIC_RE = re.compile(r"\b1\s*:\s*(\d+)\b")


def _parse_scale_factor(scale_text: str) -> float | None:
    """Return paper-inches-per-real-world-inch for a scale string, or None."""
    if not scale_text:
        return None
    text = scale_text.strip()

    m = _SCALE_FRAC_RE.search(text)
    if m:
        num = float(m.group(1))
        den = float(m.group(2))
        feet = float(m.group(3))
        inches = float(m.group(4) or 0)
        real_inches = feet * 12.0 + inches
        if den == 0 or real_inches == 0:
            return None
        return (num / den) / real_inches

    m = _SCALE_INCH_EQ_FT_RE.search(text)
    if m:
        paper_inches = float(m.group(1))
        real_feet = float(m.group(2))
        if real_feet == 0:
            return None
        return paper_inches / (real_feet * 12.0)

    m = _SCALE_METRIC_RE.search(text)
    if m:
        denom = float(m.group(1))
        if denom == 0:
            return None
        # Metric scale 1:N means 1 unit on paper = N units in real life,
        # so paper-units-per-real-unit = 1/N. The unit is the same on both
        # sides (typically mm or m), so the ratio is unitless and
        # equivalent to paper-inches-per-real-inch.
        return 1.0 / denom

    return None


def _extract_title_block(page_text: str) -> tuple[TitleBlockData, list[str]]:
    """Pull title-block fields from a page's plain text.

    Returns the populated block plus a list of quality issues (e.g.
    "scale unparseable") that the confidence scorer can read off.
    """
    tb = TitleBlockData()
    quality_issues: list[str] = []

    for attr, pattern in _TITLE_BLOCK_PATTERNS:
        if getattr(tb, attr):
            continue  # keep the first match (which is the most specific)
        m = pattern.search(page_text)
        if not m:
            continue
        cleaned = _clean_field(m.group(1))
        if not cleaned:
            continue
        setattr(tb, attr, cleaned)

    # Discipline: sheet-number prefix is authoritative.
    inferred = _discipline_from_sheet_number(tb.sheet_number)
    if inferred:
        tb.discipline = inferred

    # Scale numeric factor.
    if tb.scale:
        tb.scale_factor = _parse_scale_factor(tb.scale)
        if tb.scale_factor is None:
            quality_issues.append(f"scale unparseable: {tb.scale!r}")

    return tb, quality_issues


# ---------------------------------------------------------------------------
# Dimension extraction
# ---------------------------------------------------------------------------

# Pattern catalog — applied longest-match-first so e.g. `10'-6"` does not
# get partial-matched as just `10'` and then `6"`. Each pattern returns the
# tuple of capture groups and a `kind` tag. Order is critical.

_FEET_INCH_FRACTION_RE = re.compile(
    # 10'-6 1/2"  or  10' - 6 1/2"  or  10'-6"
    r"(\d+)\s*'\s*-?\s*(\d+)(?:\s+(\d+)/(\d+))?\s*(?:\.(\d+))?\s*\"",
)
_FEET_DECIMAL_RE = re.compile(r"(?<![\d\.])(\d+(?:\.\d+)?)\s*'(?!')")
_INCH_FRACTION_RE = re.compile(
    # 6 1/2"  or  6.5"  or  6"
    r"(?<![\d\.])(\d+)(?:\s+(\d+)/(\d+))?(?:\.(\d+))?\s*\"",
)
_METRIC_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(mm|cm|m)\b", re.IGNORECASE)

# After matching a dimension we delete it from the working buffer so the
# shorter sub-patterns don't double-count. We mark matches with this token.
_MATCH_MARK = "\x00"


def _parse_fraction_inches(int_part: str, num: str | None, den: str | None,
                            dec: str | None) -> float:
    inches = float(int_part)
    if num and den:
        inches += float(num) / float(den)
    if dec:
        inches += float(f"0.{dec}")
    return inches


def _extract_dimensions(page_text: str) -> list[Dimension]:
    """Pull every dimension off the page, normalized to inches."""
    results: list[Dimension] = []
    buf = page_text

    # 1. feet-inches mixed (longest)
    def _ftin(m: re.Match[str]) -> str:
        feet = float(m.group(1))
        inches = _parse_fraction_inches(
            m.group(2), m.group(3), m.group(4), m.group(5),
        )
        total = feet * 12.0 + inches
        results.append(Dimension(raw_text=m.group(0), inches=total, kind="feet-inches"))
        return _MATCH_MARK * len(m.group(0))

    buf = _FEET_INCH_FRACTION_RE.sub(_ftin, buf)

    # 2. metric (mm / cm / m)
    def _met(m: re.Match[str]) -> str:
        val = float(m.group(1))
        unit = m.group(2).lower()
        if unit == "mm":
            inches = val / 25.4
        elif unit == "cm":
            inches = val / 2.54
        else:  # m
            inches = val * 39.3700787
        results.append(Dimension(raw_text=m.group(0), inches=inches, kind="metric"))
        return _MATCH_MARK * len(m.group(0))

    buf = _METRIC_RE.sub(_met, buf)

    # 3. just feet (decimal feet like `10.5'`)
    def _ft(m: re.Match[str]) -> str:
        feet = float(m.group(1))
        results.append(Dimension(
            raw_text=m.group(0), inches=feet * 12.0, kind="decimal-feet",
        ))
        return _MATCH_MARK * len(m.group(0))

    buf = _FEET_DECIMAL_RE.sub(_ft, buf)

    # 4. just inches (shortest)
    def _in(m: re.Match[str]) -> str:
        inches = _parse_fraction_inches(
            m.group(1), m.group(2), m.group(3), m.group(4),
        )
        results.append(Dimension(raw_text=m.group(0), inches=inches, kind="feet-inches"))
        return _MATCH_MARK * len(m.group(0))

    buf = _INCH_FRACTION_RE.sub(_in, buf)

    # Drop obviously-spurious matches:
    #   * exactly 0 inches (usually a callout like `0"` on a detail)
    #   * > 5000 inches (~416 ft; in practice OCR garbage)
    filtered = [d for d in results if 0.0 < d.inches <= 5000.0]
    return filtered


# ---------------------------------------------------------------------------
# Schedule-table extraction
# ---------------------------------------------------------------------------

_SCHEDULE_KEYWORDS: dict[str, set[str]] = {
    "door":   {"DOOR", "MARK", "TYPE", "SIZE", "FRAME", "HARDWARE", "WIDTH", "HEIGHT", "RATING"},
    "window": {"WINDOW", "MARK", "TYPE", "SIZE", "GLAZING", "WIDTH", "HEIGHT"},
    "room":   {"ROOM", "NAME", "NUMBER", "FLOOR", "WALL", "CEILING", "BASE"},
    "finish": {"FINISH", "MATERIAL", "LOCATION", "COLOR", "MANUFACTURER"},
}


def _classify_schedule(headers: list[str]) -> str:
    """Best-fit kind for a header row based on keyword overlap."""
    header_words: set[str] = set()
    for h in headers:
        if not h:
            continue
        header_words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not header_words:
        return "unknown"

    best_kind = "unknown"
    best_score = 0
    for kind, kw in _SCHEDULE_KEYWORDS.items():
        score = len(header_words & kw)
        # Bias toward door/window when their *primary* keyword is present
        # (a "DOOR" header is a near-certain door schedule even if the
        # rest of the columns don't overlap with the dictionary).
        if kind in {"door", "window"} and kind.upper() in header_words:
            score += 2
        if score > best_score:
            best_score = score
            best_kind = kind
    return best_kind if best_score >= 2 else "unknown"


def _extract_schedules(page: "fitz.Page", page_index: int) -> list[Schedule]:
    """Find tables on the page and convert them to `Schedule` rows.

    PyMuPDF's `find_tables()` is text-based; on purely-scanned pages it
    returns nothing, which is the correct behaviour here — the LLM still
    owns those.
    """
    schedules: list[Schedule] = []
    try:
        finder = page.find_tables()
    except Exception as exc:  # pragma: no cover - PyMuPDF internal
        logger.debug("find_tables failed on page %d: %s", page_index, exc)
        return schedules

    tables = getattr(finder, "tables", None) or []
    for table in tables:
        try:
            extracted = table.extract()
        except Exception as exc:  # pragma: no cover - PyMuPDF internal
            logger.debug("table.extract failed on page %d: %s", page_index, exc)
            continue
        if not extracted or len(extracted) < 3:
            # Need a header row + at least 2 data rows.
            continue

        headers_raw = extracted[0]
        headers = [str(h).strip() if h is not None else "" for h in headers_raw]
        if not any(headers):
            # Maybe the first row is data; skip these in practice.
            continue

        rows: list[ScheduleRow] = []
        for raw_row in extracted[1:]:
            if not raw_row:
                continue
            cells = [str(c).strip() if c is not None else "" for c in raw_row]
            if not any(cells):
                continue
            cols: dict[str, str] = {}
            for i, val in enumerate(cells):
                key = headers[i] if i < len(headers) and headers[i] else f"col_{i + 1}"
                cols[key] = val
            rows.append(ScheduleRow(columns=cols))

        if len(rows) < 2:
            # Drop tables with < 2 data rows (layout artefacts).
            continue

        schedules.append(Schedule(
            kind=_classify_schedule(headers),
            headers=headers,
            rows=rows,
            source_page=page_index,
        ))

    return schedules


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------


def _score(result: DrawingPrepassResult) -> float:
    """Heuristic 0..1 confidence; see module docstring for the rubric."""
    score = 0.0
    tb = result.title_block

    if tb.sheet_number and tb.discipline:
        score += 0.30
    if tb.project_name:
        score += 0.20
    if tb.scale_factor is not None:
        score += 0.15
    if len(result.schedules) >= 1:
        score += 0.20
    if len(result.dimensions) >= 5:
        score += 0.15

    return min(score, 1.0)


# ---------------------------------------------------------------------------
# Public entry points
# ---------------------------------------------------------------------------


def _page_text(page: "fitz.Page") -> str:
    """Layout-aware plain-text extraction.

    PyMuPDF's `get_text("text")` already preserves reading order well
    enough for title blocks and inline dimensions, and is a lot more
    forgiving than `get_text("dict")` when we just want a string buffer
    to regex over.
    """
    return page.get_text("text") or ""


def _maybe_extract_door_schedule(page: "fitz.Page", page_index: int,
                                    schedules: list[Schedule]):
    """T1 hook: run the door-schedule extractor when this page may have one.

    Imported lazily so the door-schedule module is optional at load time —
    keeps the existing prepass independent of T1's extraction path.
    Returns a ``DoorScheduleResult`` dataclass or ``None``.
    """
    has_door_schedule = any(s.kind == "door" for s in schedules)
    text_has_phrase = "DOOR SCHEDULE" in (page.get_text("text") or "").upper()
    if not (has_door_schedule or text_has_phrase):
        return None
    try:
        from .door_schedule import extract_door_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("door_schedule import failed: %s", exc)
        return None
    try:
        result = extract_door_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("door_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.doors else None


def _maybe_extract_window_schedule(page: "fitz.Page", page_index: int,
                                      schedules: list[Schedule],
                                      door_schedule: Any) -> Any:
    """T2.5 hook: run the window-schedule extractor when this page may have one.

    Imported lazily so the window-schedule module stays optional at load
    time. Respects the door-precedence rule: if a door schedule has
    already been detected on this page (``door_schedule is not None``
    AND it actually has door records) we skip the window pass entirely
    to avoid mis-attributing door rows to window CSI sections.
    Returns a ``WindowScheduleResult`` dataclass or ``None``.
    """
    # Door-precedence: if a door schedule was extracted on this page,
    # the older, more-validated extractor wins and we never run the
    # window detector against the same content.
    if door_schedule is not None and getattr(door_schedule, "doors", None):
        return None

    has_window_schedule = any(s.kind == "window" for s in schedules)
    text_has_phrase = "WINDOW SCHEDULE" in (page.get_text("text") or "").upper()
    if not (has_window_schedule or text_has_phrase):
        return None
    try:
        from .window_schedule import extract_window_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("window_schedule import failed: %s", exc)
        return None
    try:
        result = extract_window_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("window_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.windows else None


def _maybe_extract_finish_schedule(page: "fitz.Page", page_index: int,
                                      schedules: list[Schedule],
                                      door_schedule: Any,
                                      window_schedule: Any) -> Any:
    """T4 hook: run the finish-schedule extractor when this page may have one.

    Imported lazily so the finish-schedule module stays optional at
    load time. Respects the door + window precedence rule: if either
    of those has already been detected on this page we skip the finish
    pass entirely. Returns a ``FinishScheduleResult`` dataclass or
    ``None``.
    """
    # Door / window precedence: if either schedule was extracted on
    # this page, the older, more-validated extractor wins and we never
    # run the finish detector against the same content.
    if door_schedule is not None and getattr(door_schedule, "doors", None):
        return None
    if window_schedule is not None and getattr(window_schedule, "windows", None):
        return None

    has_finish_schedule = any(s.kind == "finish" for s in schedules)
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = (
        "ROOM FINISH SCHEDULE" in text_upper
        or "FINISH SCHEDULE" in text_upper
    )
    if not (has_finish_schedule or text_has_phrase):
        return None
    try:
        from .finish_schedule import extract_finish_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("finish_schedule import failed: %s", exc)
        return None
    try:
        result = extract_finish_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("finish_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.rooms else None


def _maybe_extract_room_schedule(page: "fitz.Page", page_index: int,
                                    schedules: list[Schedule],
                                    door_schedule: Any,
                                    window_schedule: Any) -> Any:
    """T5 hook: run the room-schedule extractor when this page may have one.

    Imported lazily so the room-schedule module stays optional at load
    time. **No precedence vs. the finish detector** (Option A from the
    T5 brief): a combined ``ROOM FINISH SCHEDULE`` produces BOTH a
    finish result AND a room result so the Phase T5 back-fill can join
    them by ``room_number``. Door/window precedence DOES apply — if
    either of those has already been detected on this page we skip the
    room pass entirely (defensive — a door / window schedule never
    carries area / ceiling-height columns so this is unlikely to fire
    in practice, but it preserves the invariant that the upstream
    detectors win on ambiguous pages). Returns a
    ``RoomScheduleResult`` dataclass or ``None``.
    """
    if door_schedule is not None and getattr(door_schedule, "doors", None):
        return None
    if window_schedule is not None and getattr(window_schedule, "windows", None):
        return None

    has_room_schedule = any(s.kind == "room" for s in schedules)
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = (
        "ROOM SCHEDULE" in text_upper
        or "ROOM FINISH SCHEDULE" in text_upper
    )
    if not (has_room_schedule or text_has_phrase):
        # One more cheap signal — a detected generic schedule whose
        # headers look room-shaped. Avoids missing room schedules on
        # pages whose phrase trigger uses non-standard wording.
        try:
            from .room_schedule import _looks_like_room_header  # type: ignore
        except Exception:  # pragma: no cover - defensive
            return None
        any_room_header = any(
            _looks_like_room_header(s.headers) for s in schedules
        )
        if not any_room_header:
            return None
    try:
        from .room_schedule import extract_room_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("room_schedule import failed: %s", exc)
        return None
    try:
        result = extract_room_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("room_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.rooms else None


def _maybe_extract_panel_schedule(page: "fitz.Page", page_index: int,
                                     schedules: list[Schedule]) -> Any:
    """T2.6 hook: run the panel-schedule extractor when this page may have one.

    Imported lazily so the panel-schedule module stays optional at
    load time. **Runs independently of door / window / finish / room
    precedence** — electrical panel schedules live on E-series sheets
    those upstream detectors never claim, so there's no scheduling
    conflict to resolve. Returns a ``PanelScheduleResult`` dataclass
    or ``None``.
    """
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = any(
        kw in text_upper
        for kw in (
            "PANEL SCHEDULE", "PANEL SCHED",
            "PNL SCHEDULE", "PNL SCHED",
            "ELECTRICAL PANEL",
        )
    )
    if not text_has_phrase:
        try:
            from .panel_schedule import _looks_like_panel_header  # type: ignore
        except Exception:  # pragma: no cover - defensive
            return None
        if not any(_looks_like_panel_header(s.headers) for s in schedules):
            return None
    try:
        from .panel_schedule import extract_panel_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("panel_schedule import failed: %s", exc)
        return None
    try:
        result = extract_panel_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("panel_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.panels else None


def _maybe_extract_lighting_schedule(page: "fitz.Page", page_index: int,
                                        schedules: list[Schedule]) -> Any:
    """T2.7 hook: run the lighting-fixture-schedule extractor when present.

    Imported lazily so the lighting_schedule module stays optional
    at load time. **Runs independently of door / window / finish /
    room precedence** — lighting-fixture schedules live on E-series
    sheets those upstream detectors never claim, same posture as the
    panel-schedule hook. Runs ALONGSIDE the panel hook (different
    table shapes on the same sheet → both can fire). Returns a
    ``LightingScheduleResult`` dataclass or ``None``.
    """
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = any(
        kw in text_upper
        for kw in (
            "LIGHTING FIXTURE SCHEDULE", "LIGHTING FIXTURE",
            "LUMINAIRE SCHEDULE", "FIXTURE SCHEDULE",
            "LIGHT FIXTURE SCHEDULE", "LTG FIXTURE",
            "FIXTURE TYPE",
        )
    )
    if not text_has_phrase:
        try:
            from .lighting_schedule import _looks_like_lighting_header  # type: ignore
        except Exception:  # pragma: no cover - defensive
            return None
        if not any(_looks_like_lighting_header(s.headers) for s in schedules):
            return None
    try:
        from .lighting_schedule import extract_lighting_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("lighting_schedule import failed: %s", exc)
        return None
    try:
        result = extract_lighting_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("lighting_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.fixtures else None


def _maybe_extract_hvac_schedule(page: "fitz.Page", page_index: int,
                                    schedules: list[Schedule]) -> Any:
    """T2.8 hook: run the HVAC-equipment-schedule extractor when present.

    Imported lazily so the hvac_schedule module stays optional at
    load time. **Runs independently of door / window / finish /
    room precedence** — mechanical schedules live on M-series /
    H-series / MH-series sheets those upstream detectors never
    claim, same posture as the panel + lighting hooks.  Runs
    ALONGSIDE the panel + lighting hooks (different table shapes,
    different sheets → no scheduling conflict).  Returns an
    ``HVACScheduleResult`` dataclass or ``None``.
    """
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = any(
        kw in text_upper
        for kw in (
            "AHU SCHEDULE", "RTU SCHEDULE", "VAV SCHEDULE",
            "PUMP SCHEDULE", "BOILER SCHEDULE", "CHILLER SCHEDULE",
            "FAN SCHEDULE", "MECHANICAL EQUIPMENT SCHEDULE",
            "MECHANICAL SCHEDULE", "HVAC SCHEDULE",
            "MECHANICAL EQUIPMENT",
        )
    )
    if not text_has_phrase:
        try:
            from .hvac_schedule import _looks_like_hvac_header  # type: ignore
        except Exception:  # pragma: no cover - defensive
            return None
        if not any(_looks_like_hvac_header(s.headers) for s in schedules):
            return None
    try:
        from .hvac_schedule import extract_hvac_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("hvac_schedule import failed: %s", exc)
        return None
    try:
        result = extract_hvac_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("hvac_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.equipment else None


def _maybe_extract_plumbing_schedule(page: "fitz.Page", page_index: int,
                                        schedules: list[Schedule]) -> Any:
    """T2.9 hook: run the plumbing-fixture-schedule extractor when present.

    Imported lazily so the plumbing_schedule module stays optional at
    load time. **Runs independently of door / window / finish / room
    precedence** — plumbing fixture schedules live on P-series sheets
    those upstream detectors never claim, same posture as the panel
    + lighting + HVAC hooks.  Runs ALONGSIDE the panel + lighting +
    HVAC hooks (different table shapes, different sheets → no
    scheduling conflict).  Closes the Division 22+23+26 typed-
    schedule trifecta entirely.  Returns a ``PlumbingScheduleResult``
    dataclass or ``None``.
    """
    text_upper = (page.get_text("text") or "").upper()
    text_has_phrase = any(
        kw in text_upper
        for kw in (
            "PLUMBING FIXTURE SCHEDULE",
            "PLUMBING SCHEDULE",
            "PLUMBING FIXTURES",
            "FIXTURE SCHEDULE",
            "FIXTURE TYPE",
        )
    )
    if not text_has_phrase:
        try:
            from .plumbing_schedule import _looks_like_plumbing_header  # type: ignore
        except Exception:  # pragma: no cover - defensive
            return None
        if not any(_looks_like_plumbing_header(s.headers) for s in schedules):
            return None
    try:
        from .plumbing_schedule import extract_plumbing_schedule_from_page
    except Exception as exc:  # pragma: no cover - defensive
        logger.debug("plumbing_schedule import failed: %s", exc)
        return None
    try:
        result = extract_plumbing_schedule_from_page(page, page_index)
    except Exception as exc:  # pragma: no cover - defensive
        logger.warning("plumbing_schedule extraction failed on page %d: %s",
                       page_index, exc)
        return None
    return result if result.fixtures else None


def prepass_drawing_page(pdf_path: Path, page_index: int) -> DrawingPrepassResult:
    """Run the deterministic pre-pass on a single page of a drawing PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        page = doc[page_index]
        text = _page_text(page)
        title_block, quality_issues = _extract_title_block(text)
        dimensions = _extract_dimensions(text)
        schedules = _extract_schedules(page, page_index)
        door_schedule = _maybe_extract_door_schedule(page, page_index, schedules)
        window_schedule = _maybe_extract_window_schedule(
            page, page_index, schedules, door_schedule,
        )
        finish_schedule = _maybe_extract_finish_schedule(
            page, page_index, schedules, door_schedule, window_schedule,
        )
        room_schedule = _maybe_extract_room_schedule(
            page, page_index, schedules, door_schedule, window_schedule,
        )
        panel_schedule = _maybe_extract_panel_schedule(
            page, page_index, schedules,
        )
        lighting_schedule = _maybe_extract_lighting_schedule(
            page, page_index, schedules,
        )
        hvac_schedule = _maybe_extract_hvac_schedule(
            page, page_index, schedules,
        )
        plumbing_schedule = _maybe_extract_plumbing_schedule(
            page, page_index, schedules,
        )

    if not text.strip():
        quality_issues.append("page has no embedded text (likely scanned)")

    result = DrawingPrepassResult(
        title_block=title_block,
        dimensions=dimensions,
        schedules=schedules,
        quality_issues=quality_issues,
        confidence=0.0,
        door_schedule=door_schedule,
        window_schedule=window_schedule,
        finish_schedule=finish_schedule,
        room_schedule=room_schedule,
        panel_schedule=panel_schedule,
        lighting_schedule=lighting_schedule,
        hvac_schedule=hvac_schedule,
        plumbing_schedule=plumbing_schedule,
    )
    result.confidence = round(_score(result), 4)
    return result


def prepass_drawing_pdf(pdf_path: Path) -> list[DrawingPrepassResult]:
    """Run the deterministic pre-pass on every page of a drawing PDF."""
    pdf_path = Path(pdf_path)
    results: list[DrawingPrepassResult] = []
    with fitz.open(pdf_path) as doc:
        for i in range(len(doc)):
            page = doc[i]
            text = _page_text(page)
            title_block, quality_issues = _extract_title_block(text)
            dimensions = _extract_dimensions(text)
            schedules = _extract_schedules(page, i)
            door_schedule = _maybe_extract_door_schedule(page, i, schedules)
            window_schedule = _maybe_extract_window_schedule(
                page, i, schedules, door_schedule,
            )
            finish_schedule = _maybe_extract_finish_schedule(
                page, i, schedules, door_schedule, window_schedule,
            )
            room_schedule = _maybe_extract_room_schedule(
                page, i, schedules, door_schedule, window_schedule,
            )
            panel_schedule = _maybe_extract_panel_schedule(
                page, i, schedules,
            )
            lighting_schedule = _maybe_extract_lighting_schedule(
                page, i, schedules,
            )
            hvac_schedule = _maybe_extract_hvac_schedule(
                page, i, schedules,
            )
            plumbing_schedule = _maybe_extract_plumbing_schedule(
                page, i, schedules,
            )
            if not text.strip():
                quality_issues.append("page has no embedded text (likely scanned)")

            r = DrawingPrepassResult(
                title_block=title_block,
                dimensions=dimensions,
                schedules=schedules,
                quality_issues=quality_issues,
                confidence=0.0,
                door_schedule=door_schedule,
                window_schedule=window_schedule,
                finish_schedule=finish_schedule,
                room_schedule=room_schedule,
                panel_schedule=panel_schedule,
                lighting_schedule=lighting_schedule,
                hvac_schedule=hvac_schedule,
                plumbing_schedule=plumbing_schedule,
            )
            r.confidence = round(_score(r), 4)
            results.append(r)
    return results


# ---------------------------------------------------------------------------
# Schema bridge — convert internal dataclasses to the Pydantic models on
# `core.schemas` so the result can be serialised onto `SheetExtraction`.
# ---------------------------------------------------------------------------


def to_schema(result: DrawingPrepassResult):
    """Return a `core.schemas.DrawingPrepassResult` Pydantic model.

    Imported lazily to avoid a top-level circular import (schemas →
    extraction → drawing_prepass → schemas would loop without this).
    """
    from core import schemas as S

    tb = result.title_block
    schedules = [
        S.Schedule(
            kind=s.kind,
            headers=list(s.headers),
            rows=[S.ScheduleRow(columns=dict(r.columns)) for r in s.rows],
            source_page=s.source_page,
        )
        for s in result.schedules
    ]
    door_schedule = None
    if result.door_schedule is not None:
        from .door_schedule import to_schema as door_to_schema
        door_schedule = door_to_schema(result.door_schedule)
    window_schedule = None
    if result.window_schedule is not None:
        from .window_schedule import to_schema as window_to_schema
        window_schedule = window_to_schema(result.window_schedule)
    finish_schedule = None
    if result.finish_schedule is not None:
        from .finish_schedule import to_schema as finish_to_schema
        finish_schedule = finish_to_schema(result.finish_schedule)
    room_schedule = None
    if result.room_schedule is not None:
        from .room_schedule import to_schema as room_to_schema
        room_schedule = room_to_schema(result.room_schedule)
    panel_schedule = None
    if result.panel_schedule is not None:
        from .panel_schedule import to_schema as panel_to_schema
        panel_schedule = panel_to_schema(result.panel_schedule)
    lighting_schedule = None
    if result.lighting_schedule is not None:
        from .lighting_schedule import to_schema as lighting_to_schema
        lighting_schedule = lighting_to_schema(result.lighting_schedule)
    hvac_schedule = None
    if result.hvac_schedule is not None:
        from .hvac_schedule import to_schema as hvac_to_schema
        hvac_schedule = hvac_to_schema(result.hvac_schedule)
    plumbing_schedule = None
    if result.plumbing_schedule is not None:
        from .plumbing_schedule import to_schema as plumbing_to_schema
        plumbing_schedule = plumbing_to_schema(result.plumbing_schedule)
    return S.DrawingPrepassResult(
        title_block=S.TitleBlockData(
            project_name=tb.project_name,
            project_number=tb.project_number,
            sheet_number=tb.sheet_number,
            sheet_title=tb.sheet_title,
            discipline=tb.discipline,
            scale=tb.scale,
            scale_factor=tb.scale_factor,
            date=tb.date,
            revision=tb.revision,
            drawn_by=tb.drawn_by,
            checked_by=tb.checked_by,
        ),
        dimensions=[
            S.Dimension(raw_text=d.raw_text, inches=d.inches, kind=d.kind)
            for d in result.dimensions
        ],
        schedules=schedules,
        quality_issues=list(result.quality_issues),
        confidence=result.confidence,
        door_schedule=door_schedule,
        window_schedule=window_schedule,
        finish_schedule=finish_schedule,
        room_schedule=room_schedule,
        panel_schedule=panel_schedule,
        lighting_schedule=lighting_schedule,
        hvac_schedule=hvac_schedule,
        plumbing_schedule=plumbing_schedule,
    )


def iter_dimension_models(dims: Iterable[Dimension]):
    """Yield `core.schemas.Dimension` Pydantic models."""
    from core import schemas as S

    for d in dims:
        yield S.Dimension(raw_text=d.raw_text, inches=d.inches, kind=d.kind)
