"""Deterministic electrical-panel-schedule extraction (Phase T2.6).

Electrical panel schedules are the highest-dollar single artefact in a
construction set (Division 26 consistently leads BPC's calibration cost
distribution). A typical panel schedule on an E-series sheet (E1.0 /
E2.0 / E3.0) carries three structural pieces:

1. **Header block** — Panel ID (``PNL-A`` / ``MDP`` / ``RP-1``),
   voltage (``120/208V`` / ``277/480V``), phase count (1 or 3), main
   breaker / bus amps with MCB vs MLO designation, and the feeder
   size (conductor + conduit).
2. **Circuit table** — per-circuit rows with circuit number, breaker
   amps, load description, load watts (or VA), and phase (A/B/C). Many
   schedules use a two-column layout where odd-numbered circuits run
   down the left half of the table and even-numbered down the right
   half; the parser handles both shapes.
3. **Footer** — total connected load, demand factor, sometimes a
   restated feeder size.

The synthesiser downstream (:mod:`core.extraction.takeoff_synthesis`)
fans each ``PanelRecord`` out into four families of ``TakeoffItem``:
panel enclosure (26 24 16 panelboards ≤ 400A or 26 24 13 switchboards
> 400A), branch breakers grouped by amp size (26 28 16), feeder
conductor (26 05 19, parametric default 50 LF), feeder conduit
(26 05 33, parametric default 50 LF).

Architectural pattern mirrors :mod:`core.extraction.door_schedule` /
:mod:`core.extraction.finish_schedule`: pure functions of a ``Path`` +
page index (or a ``fitz.Page``), internal dataclasses with a
``to_schema()`` bridge to the Pydantic models on :mod:`core.schemas`,
and a confidence rubric. Runs **alongside** (never instead of) the
existing F3 prepass and the door / window / finish / room extractors;
panel sheets typically live on E-series pages that those upstream
detectors leave untouched.

Substring-collision note: the PHASE column on a circuit table is often
labelled simply ``A`` / ``B`` / ``C`` (one letter), which collides via
substring with the ``AMPS`` header. This module pins the AMPS column
first and finds the PHASE column with the AMPS index excluded — the
same pattern Worker U promoted out of :mod:`door_schedule` and into
:mod:`finish_schedule`.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

# Phase T3.6 promoted ``_header_index_excluding`` from ``door_schedule``
# to a shared ``header_utils`` module once the helper became load-bearing
# across three extractors (door, panel, lighting).  Imported under the
# legacy underscore-prefixed name to keep this module's internal
# call-sites unchanged from their T2.6 shape.
from .header_utils import header_index_excluding as _header_index_excluding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class CircuitEntry:
    """One row in an electrical panel schedule's circuit table."""

    circuit_number: str
    breaker_amps: int | None = None
    load_description: str = ""
    load_watts: float | None = None
    phase: str | None = None


@dataclass
class PanelRecord:
    """One electrical panel pulled off a panel schedule.

    ``confidence`` defaults to ``0.85`` — panel data is well-structured
    and the parser is deterministic, so a clean extraction is high
    confidence by construction. Partial extractions (panel ID without
    a voltage, or a voltage without an MCB/MLO designation) tick the
    confidence down slightly via :func:`_panel_confidence`.
    """

    panel_id: str
    voltage: str | None = None
    phase_count: int | None = None
    main_breaker_amps: int | None = None
    bus_amps: int | None = None
    mcb_or_mlo: str | None = None
    feeder_conductor_size: str | None = None
    feeder_conduit_size: str | None = None
    location: str | None = None
    circuits: list[CircuitEntry] = field(default_factory=list)
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class PanelScheduleResult:
    """Aggregate panel-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    panels: list[PanelRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Page-level phrase signals. Any of these in the page text triggers the
# extractor; the absence of all five does not exclude the page because a
# circuit-table header is sufficient on its own.
_PANEL_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "PANEL SCHEDULE",
    "PANEL SCHED",
    "PNL SCHEDULE",
    "PNL SCHED",
    "ELECTRICAL PANEL",
)


# Tokens that identify a circuit-table header row. Requires a CKT/CIRCUIT
# column AND at least one breaker-side column AND at least one
# load-side column — the same three-signal pattern used by door /
# window / finish detection so a non-electrical table never fires.
_PANEL_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "CIRCUIT", "CKT", "CIR",
    "BREAKER", "BKR", "AMPS", "AMP",
    "DESCRIPTION", "DESC", "LOAD",
    "WATTS", "W", "VA",
    "PHASE", "PH",
})


# Tokens that may follow ``PANEL`` in the schedule text but are NEVER
# valid panel IDs. Used by :func:`_all_panel_id_matches` to filter the
# broad pattern below — without this blocklist, ``PANEL SCHEDULE`` and
# ``PANEL SCHED`` would leak through as panel IDs of "SCHEDULE" /
# "SCHED" because the short-tail regex happily matches both.
_PANEL_NON_ID_WORDS: frozenset[str] = frozenset({
    "SCHEDULE", "SCHED", "SCHEDULES", "LIST", "SUMMARY",
    "BREAKER", "BREAKERS", "FEEDER", "FEEDERS", "BOARD", "BOARDS",
    "ID", "NO", "NUMBER", "NAME", "TAG", "DESIGNATION",
    "LOAD", "LOADS", "DETAIL", "DETAILS", "NOTES", "NOTE",
    "TYPE", "VOLTAGE", "VOLTS", "AMPS", "PHASE", "PHASES",
    "BUS", "MAIN", "MCB", "MLO", "RATING", "RATINGS",
    "CIRCUIT", "CIRCUITS", "SECTION", "SECTIONS",
})


# Panel-ID pattern (BROAD form). Accepts every plausible panel-ID shape
# in real BPC bid sets: ``PNL-A`` / ``PANEL A`` / ``PANEL-A`` /
# ``PANEL_A`` / ``MDP`` / ``MDP1`` / ``MDP-1`` / ``RP-1`` / ``DP-A`` /
# ``MP-1`` / ``LP-1`` / ``SDP-A`` / ``HP-1``. The optional tail
# (``(?:[\s\-_]?[A-Z0-9]{1,6})?``) accommodates bare-prefix IDs like
# ``MDP``. Used by the public API + the panel-id-pattern unit test;
# the broad nature means downstream callers MUST filter against
# :data:`_PANEL_NON_ID_WORDS` (see :func:`_all_panel_id_matches`).
_PANEL_ID_PATTERN: re.Pattern[str] = re.compile(
    r"\b(?:PNL|PANEL|RP|DP|MP|MDP|LP|SDP|HP)(?:[\s\-_]?[A-Z0-9]{1,6})?\b",
    re.IGNORECASE,
)

# Internal: short-prefix-anchored pattern. These prefixes never collide
# with English words and so don't need the noun blocklist — the bare
# form (``MDP``) is accepted as a complete ID. Capture groups are
# (prefix, optional-tail).
#
# Separator class is intentionally ``[ \t\-_]?`` (horizontal whitespace
# + hyphen / underscore) — NOT ``\s`` — so ``MDP\n277/480V`` does not
# spuriously fuse into ``MDP-277`` across a line break.
_PANEL_SHORT_ID_RE: re.Pattern[str] = re.compile(
    r"\b(PNL|MDP|RP|DP|MP|LP|SDP|HP)(?:[ \t\-_]?([A-Z0-9]{1,6}))?\b",
    re.IGNORECASE,
)

# Internal: long-prefix pattern (``PANEL <X>`` / ``PANEL-X``). Requires
# a tail of 1-6 alphanumerics, then runs that tail through the noun
# blocklist before accepting. This is what distinguishes
# ``PANEL PNL-A`` (valid, tail = "PNL" which we'll prefer to anchor at
# its own short-prefix match) from ``PANEL SCHEDULE`` (rejected by
# blocklist). Same horizontal-only separator class as the short form.
_PANEL_LONG_ID_RE: re.Pattern[str] = re.compile(
    r"\bPANEL[ \t\-_]+([A-Z0-9]{1,6})\b",
    re.IGNORECASE,
)

# Single-word context anchors that indicate the following token is a
# CROSS-REFERENCE to another panel (a child / served / fed-by
# relationship), not a panel ID for THIS schedule. Without this filter,
# a circuit row whose load description reads ``"Subpanel LP-1"`` would
# leak ``LP-1`` as a distinct panel on the same page.
_PANEL_CROSSREF_WORDS: frozenset[str] = frozenset({
    "SUBPANEL", "SUB-PANEL", "SUB",
    "TO", "FROM", "VIA", "FEEDS",
    "SERVES", "SERVING", "SERVED",
})

# Two-word context anchors (parts[-2] + parts[-1]) for the same purpose.
_PANEL_CROSSREF_BIGRAMS: frozenset[tuple[str, str]] = frozenset({
    ("FED", "BY"), ("FED", "FROM"), ("FROM", "PNL"),
})


def _is_crossref_context(text: str, position: int) -> bool:
    """True when ``text[:position]`` ends with a panel cross-ref anchor.

    Walks back from ``position`` to the start of the current line and
    inspects the last whitespace-delimited token (or last two, to catch
    ``FED BY`` / ``FED FROM``). When the trailing word(s) are a known
    cross-reference anchor (``SUBPANEL`` / ``TO`` / ``FED BY`` / etc.)
    the candidate is a load-row description reference and must be
    skipped.
    """
    if position <= 0:
        return False
    line_start = text.rfind("\n", 0, position) + 1
    window_start = max(line_start, position - 30)
    window = text[window_start:position].upper().rstrip()
    if not window:
        return False
    parts = window.split()
    if not parts:
        return False
    last = parts[-1]
    if last in _PANEL_CROSSREF_WORDS:
        return True
    if len(parts) >= 2 and (parts[-2], last) in _PANEL_CROSSREF_BIGRAMS:
        return True
    return False


def _looks_like_panel_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a circuit-table header row?

    Requires three signals together to avoid false-positives on
    neighbouring door / window / finish schedules:

    1. a circuit column (``CIRCUIT`` / ``CKT`` / ``CIR``),
    2. at least one breaker-side column (``BREAKER`` / ``BKR`` /
       ``AMPS`` / ``AMP``),
    3. at least one load-side column (``DESCRIPTION`` / ``DESC`` /
       ``LOAD`` / ``WATTS`` / ``VA``).

    A single header row may legitimately repeat (two-column layout has
    two CKT columns); the heuristic only checks for **presence**, not
    uniqueness.
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    has_circuit = bool(words & {"CIRCUIT", "CKT", "CIR"})
    has_breaker = bool(words & {"BREAKER", "BKR", "AMPS", "AMP"})
    has_load = bool(words & {"DESCRIPTION", "DESC", "LOAD", "WATTS", "VA"})
    return has_circuit and has_breaker and has_load


def detect_panel_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains an electrical panel schedule.

    Two cheap signals: any of :data:`_PANEL_SCHEDULE_KEYWORDS` in the
    page text, OR a panel-shaped circuit-table header on any detected
    table. Either suffices.
    """
    text = (page.get_text("text") or "").upper()
    for kw in _PANEL_SCHEDULE_KEYWORDS:
        if kw in text:
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
        if _looks_like_panel_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Header-block (panel ID / voltage / MCB / MLO / bus amps / feeder) parsing
# ---------------------------------------------------------------------------


_VOLTAGE_RE: re.Pattern[str] = re.compile(
    r"\b(\d{2,3})\s*/\s*(\d{3})\s*V\b",
    re.IGNORECASE,
)
_VOLTAGE_SINGLE_RE: re.Pattern[str] = re.compile(
    r"\b(120|208|240|277|480|600)\s*V\b",
    re.IGNORECASE,
)
_PHASE_COUNT_RE: re.Pattern[str] = re.compile(
    r"\b([13])\s*(?:PH|PHASE|\xc6|PH\.|-PHASE)\b",
    re.IGNORECASE,
)
# Main breaker variants: "200A MCB", "MCB 200A", "MAIN 200A", "MAIN CB 200A"
_MAIN_BREAKER_RE: re.Pattern[str] = re.compile(
    r"\b(?:MAIN\s*(?:CB|BREAKER|BKR)?|MCB)\s*[:\-]?\s*(\d{2,4})\s*A\b",
    re.IGNORECASE,
)
_MAIN_BREAKER_TRAIL_RE: re.Pattern[str] = re.compile(
    r"\b(\d{2,4})\s*A\s*(?:MCB|MAIN(?:\s*BREAKER|\s*BKR)?)\b",
    re.IGNORECASE,
)
# Bus amps variants: "400A BUS", "BUS 400A", "400A MLO"
_BUS_AMPS_RE: re.Pattern[str] = re.compile(
    r"\b(?:BUS|MLO)\s*[:\-]?\s*(\d{2,4})\s*A\b",
    re.IGNORECASE,
)
_BUS_AMPS_TRAIL_RE: re.Pattern[str] = re.compile(
    r"\b(\d{2,4})\s*A\s*(?:BUS|MLO)\b",
    re.IGNORECASE,
)
_MCB_FLAG_RE: re.Pattern[str] = re.compile(r"\bMCB\b", re.IGNORECASE)
_MLO_FLAG_RE: re.Pattern[str] = re.compile(r"\bMLO\b", re.IGNORECASE)
# Feeder conductor: "3/0 AWG Cu", "#4/0 AL", "500 MCM", "350 KCMIL".
_FEEDER_CONDUCTOR_RE: re.Pattern[str] = re.compile(
    r"\b(\#?\d+(?:/\d+)?\s*(?:AWG|MCM|KCMIL)(?:\s*(?:CU|AL|COPPER|ALUMINUM))?)\b",
    re.IGNORECASE,
)
# Feeder conduit: 'in 2"', '2" C', '2 inch conduit', '2-IN', '2" EMT'.
_FEEDER_CONDUIT_RE: re.Pattern[str] = re.compile(
    r"\b(\d+(?:[\.\-/]\d+)?)\s*[\"]?\s*(?:IN(?:CH)?(?:ES)?)?\s*"
    r"(?:CONDUIT|EMT|RGS|IMC|GRC|PVC|C\b)",
    re.IGNORECASE,
)
def _all_panel_id_matches(text: str) -> list[tuple[int, str]]:
    """Find every ``(start_position, normalised_panel_id)`` in ``text``.

    Two-pass strategy: short, unambiguous prefixes (``PNL``, ``MDP``,
    ``RP``, ``DP``, ``MP``, ``LP``, ``SDP``, ``HP``) first because they
    don't collide with English words and we can accept the bare form
    (``MDP``) as a complete ID. Then a softer ``PANEL <X>`` pass for
    the long-prefix form (``PANEL A`` / ``PANEL-A``), filtered against
    :data:`_PANEL_NON_ID_WORDS` so titles like ``PANEL SCHEDULE`` /
    ``PANEL SCHED`` don't leak through as panel IDs of "SCHEDULE" /
    "SCHED".

    Matches whose ranges overlap a short-prefix hit are dropped so the
    ``PANEL PNL-A`` form pins on ``PNL-A`` (the more specific token)
    and not on ``PANEL PNL`` (less specific).
    """
    if not text:
        return []
    results: list[tuple[int, str]] = []
    short_ranges: list[tuple[int, int]] = []
    for m in _PANEL_SHORT_ID_RE.finditer(text):
        prefix = m.group(1).upper()
        tail = (m.group(2) or "").upper()
        if tail and tail in _PANEL_NON_ID_WORDS:
            continue
        if _is_crossref_context(text, m.start()):
            continue
        pid = f"{prefix}-{tail}" if tail else prefix
        results.append((m.start(), pid))
        short_ranges.append((m.start(), m.end()))
    for m in _PANEL_LONG_ID_RE.finditer(text):
        if any(m.start() < e and m.end() > s for s, e in short_ranges):
            continue
        candidate = m.group(1).upper()
        if candidate in _PANEL_NON_ID_WORDS:
            continue
        if _is_crossref_context(text, m.start()):
            continue
        results.append((m.start(), f"PANEL-{candidate}"))
    results.sort(key=lambda t: t[0])
    return results


def _first_panel_id(text: str) -> str | None:
    """Return the first plausible, blocklist-filtered panel ID in ``text``.

    Thin wrapper over :func:`_all_panel_id_matches` so the two-pass
    short-then-long strategy lives in exactly one place. Returns
    ``None`` when the text contains no plausible ID (``PANEL SCHEDULE``
    alone on a page returns ``None``).
    """
    matches = _all_panel_id_matches(text)
    return matches[0][1] if matches else None


def _parse_voltage(text: str) -> tuple[str | None, int | None]:
    """Pull a voltage string + phase count from ``text``.

    Returns ``("120/208V", 3)`` style for 120/208V three-phase, or
    ``("277/480V", 3)`` for 277/480V, or ``("120V", 1)`` for a bare
    120V single-phase. Phase count comes from an explicit ``3-PHASE``
    / ``1PH`` token when present; otherwise the dual-voltage format
    (``120/208V``) implies 3-phase by convention.
    """
    if not text:
        return None, None
    voltage_str: str | None = None
    phase: int | None = None
    m = _VOLTAGE_RE.search(text)
    if m:
        voltage_str = f"{m.group(1)}/{m.group(2)}V"
        phase = 3  # 120/208 + 277/480 split-secondary is always 3-phase
    else:
        m = _VOLTAGE_SINGLE_RE.search(text)
        if m:
            voltage_str = f"{m.group(1)}V"
            phase = 1
    m = _PHASE_COUNT_RE.search(text)
    if m:
        phase = int(m.group(1))
    return voltage_str, phase


def _parse_main_breaker(text: str) -> tuple[int | None, str | None]:
    """Pull the main breaker / MLO size and the MCB/MLO designation.

    Returns ``(amps, "MCB" | "MLO" | None)``. ``amps`` is ``None`` when
    the schedule didn't publish the value; the designation falls back to
    a bare ``MCB`` / ``MLO`` flag token when no sized header exists.
    """
    if not text:
        return None, None
    amps: int | None = None
    m = _MAIN_BREAKER_RE.search(text)
    if m:
        amps = int(m.group(1))
    if amps is None:
        m = _MAIN_BREAKER_TRAIL_RE.search(text)
        if m:
            amps = int(m.group(1))
    designation: str | None = None
    if _MCB_FLAG_RE.search(text):
        designation = "MCB"
    elif _MLO_FLAG_RE.search(text):
        designation = "MLO"
    return amps, designation


def _parse_bus_amps(text: str) -> int | None:
    """Pull the bus amp rating from ``text`` (e.g. ``400A BUS`` / ``BUS 400A``)."""
    if not text:
        return None
    m = _BUS_AMPS_RE.search(text)
    if m:
        return int(m.group(1))
    m = _BUS_AMPS_TRAIL_RE.search(text)
    if m:
        return int(m.group(1))
    return None


def _parse_feeder_conductor(text: str) -> str | None:
    """Pull a feeder conductor descriptor (``3/0 AWG Cu``) or ``None``."""
    if not text:
        return None
    m = _FEEDER_CONDUCTOR_RE.search(text)
    if not m:
        return None
    return re.sub(r"\s+", " ", m.group(1).strip().upper())


def _parse_feeder_conduit(text: str) -> str | None:
    """Pull a feeder conduit size (``2 inch``) or ``None``.

    The matched form is normalised to a single ``N inch`` string so
    downstream consumers see ``2 inch`` regardless of whether the page
    used ``2"``, ``2 IN``, ``2-INCH``, etc.
    """
    if not text:
        return None
    m = _FEEDER_CONDUIT_RE.search(text)
    if not m:
        return None
    size = m.group(1).strip()
    return f"{size} inch"


# ---------------------------------------------------------------------------
# Circuit-table parsing
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "ckt":   ("CKT", "CIRCUIT", "CIR", "NO", "NUMBER"),
    "amps":  ("AMPS", "AMP", "BREAKER", "BKR"),
    "desc":  ("DESCRIPTION", "DESC", "LOAD"),
    "watts": ("WATTS", "VA", "W"),
    "phase": ("PHASE", "PH"),
}


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


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


def _parse_int(raw: str | None) -> int | None:
    """Parse an integer cell (e.g. ``"20"`` / ``"20A"``) → 20."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"\s*(\d+)\s*A?\s*$", text, re.IGNORECASE)
    if m:
        return int(m.group(1))
    leading = re.match(r"\s*(\d+)", text)
    if leading:
        return int(leading.group(1))
    return None


def _parse_watts(raw: str | None) -> float | None:
    """Parse a load cell (``"1800"`` / ``"1.8 kW"`` / ``"180 VA"``) → float in watts.

    Accepts plain integers, decimals, ``kW`` suffix (multiplied by 1000),
    ``VA`` suffix (passed through; for resistive loads watts == VA which
    is a safe default for synthesis). Returns ``None`` on empty / non-
    numeric / negative input.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    is_kw = "KW" in upper
    leading = re.match(r"\s*(\d+(?:\.\d+)?)", text)
    if not leading:
        return None
    value = float(leading.group(1))
    if value < 0:
        return None
    if is_kw:
        value *= 1000.0
    return value


def _cell(row: list[str], idx: int | None) -> str | None:
    if idx is None or idx < 0 or idx >= len(row):
        return None
    return (row[idx] or "").strip() or None


def _circuit_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick the circuit-table column indices for ONE half of a panel table.

    Pins AMPS first (specific) and re-picks PHASE with AMPS excluded so
    the bare ``A`` / ``B`` / ``C`` phase header can't be stolen by the
    substring-tolerant matcher for ``AMPS``. Pins CKT first too so a
    ``BREAKER`` candidate at index 1 doesn't poach the CKT column on
    schedules that put the circuit number AFTER the breaker rating.
    """
    ckt_idx = _header_index(headers, _HEADERS["ckt"])
    amps_idx = _header_index_excluding(
        headers, _HEADERS["amps"],
        exclude={i for i in (ckt_idx,) if i is not None},
    )
    desc_idx = _header_index_excluding(
        headers, _HEADERS["desc"],
        exclude={i for i in (ckt_idx, amps_idx) if i is not None},
    )
    watts_idx = _header_index_excluding(
        headers, _HEADERS["watts"],
        exclude={i for i in (ckt_idx, amps_idx, desc_idx) if i is not None},
    )
    phase_idx = _header_index_excluding(
        headers, _HEADERS["phase"],
        exclude={i for i in (ckt_idx, amps_idx, desc_idx, watts_idx)
                  if i is not None},
    )
    return {
        "ckt": ckt_idx,
        "amps": amps_idx,
        "desc": desc_idx,
        "watts": watts_idx,
        "phase": phase_idx,
    }


def _ckt_column_positions(headers: list[str]) -> list[int]:
    """Return EVERY column index whose header reads as a CKT/CIRCUIT column."""
    positions: list[int] = []
    for i, h in enumerate(headers):
        norm = _normalize_header(h)
        norm_words = set(norm.split())
        if norm_words & {"CKT", "CIRCUIT", "CIR"}:
            positions.append(i)
            continue
        # substring fallback — matches "CKT#", "CKT.", "CKT NO" etc.
        if any(c in norm for c in ("CKT", "CIRCUIT")):
            positions.append(i)
    return positions


def _split_two_column_table(headers: list[str], data_rows: list[list[str]]
                              ) -> tuple[tuple[list[str], list[list[str]]],
                                          tuple[list[str], list[list[str]]]] | None:
    """If the table is a two-column panel layout, return both halves.

    A two-column layout has CKT columns at index ``i_left`` and
    ``i_right`` with ``i_right > i_left``. The split point is the
    column **before** ``i_right`` (so the left half includes columns
    ``[0..i_right-1]`` and the right half includes ``[i_right..end]``).

    Returns ``None`` when the table is a single-column layout.
    """
    ckt_positions = _ckt_column_positions(headers)
    if len(ckt_positions) < 2:
        return None
    split = ckt_positions[1]
    left_headers = headers[:split]
    right_headers = headers[split:]
    left_rows = [row[:split] for row in data_rows]
    right_rows = [row[split:] for row in data_rows]
    return (left_headers, left_rows), (right_headers, right_rows)


def _records_from_table_half(headers: list[str], data_rows: list[list[str]]
                                ) -> list[CircuitEntry]:
    """Convert one half of a circuit table to ``CircuitEntry`` instances."""
    idx = _circuit_indices(headers)
    records: list[CircuitEntry] = []
    for row in data_rows:
        if not row:
            continue
        ckt = _cell(row, idx["ckt"])
        desc = _cell(row, idx["desc"])
        amps_raw = _cell(row, idx["amps"])
        watts_raw = _cell(row, idx["watts"])
        phase = _cell(row, idx["phase"])
        # Skip rows that have neither a circuit number nor a meaningful
        # description (continuation / blank rows from grid extraction).
        if not ckt and not desc and not amps_raw:
            continue
        # Skip rows whose circuit "number" is a non-digit token (panel
        # sub-header rows that survive table extraction).
        if ckt and not re.search(r"\d", ckt):
            continue
        records.append(CircuitEntry(
            circuit_number=(ckt or "").strip(),
            breaker_amps=_parse_int(amps_raw),
            load_description=(desc or "").strip(),
            load_watts=_parse_watts(watts_raw),
            phase=phase,
        ))
    return records


def _circuits_from_table(headers: list[str], data_rows: list[list[str]]
                            ) -> list[CircuitEntry]:
    """Convert one circuit-table to ``CircuitEntry`` instances.

    Handles both single-column layouts (one CKT column) and the common
    two-column layout (odd circuits left, even right). The two-column
    case is detected by counting CKT-shaped headers in the row.
    """
    split = _split_two_column_table(headers, data_rows)
    if split is None:
        return _records_from_table_half(headers, data_rows)
    (lh, lr), (rh, rr) = split
    out = _records_from_table_half(lh, lr)
    out.extend(_records_from_table_half(rh, rr))
    return out


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _panel_confidence(panel_id: str | None, has_voltage: bool,
                        has_mcb_mlo: bool, has_bus_amps: bool,
                        circuits: list[CircuitEntry]) -> float:
    """0.85 baseline; tick up to 0.92 when fully decorated, down to 0.65 partial.

    The 0.85 default lands every clean panel solidly in
    :attr:`core.schemas.CostBand.AUTO_APPROVE`. Headers that lose either
    voltage OR the MCB/MLO designation drop to 0.78 (OPERATOR_REVIEW),
    headers that lose both drop to 0.65 (still REVIEW). A panel with a
    plausible ID and a real circuit table but otherwise sparse meta-
    data still beats the 0.5 default an LLM would attach.
    """
    if not panel_id:
        return 0.5
    score = 0.85
    decoration_score = (
        (0.05 if has_voltage else 0.0)
        + (0.05 if has_mcb_mlo else 0.0)
        + (0.05 if has_bus_amps else 0.0)
        + (0.05 if circuits else 0.0)
    )
    # Penalise missing voltage + MCB/MLO together (operator review)
    missing = (0 if has_voltage else 1) + (0 if has_mcb_mlo else 1)
    if missing == 2:
        score -= 0.20
    elif missing == 1:
        score -= 0.07
    score = min(score + decoration_score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, panels: list[PanelRecord]) -> float:
    """Aggregate 0..1 confidence for the page-level result."""
    if not panels:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30  # we did find at least one panel
    if any(p.circuits for p in panels):
        score += 0.20
    if len(panels) >= 2 or any(len(p.circuits) >= 6 for p in panels):
        score += 0.10
    return min(score, 1.0)


def _split_panel_blocks(text: str) -> list[str]:
    """Split a page's text into one block per panel ID.

    Pages with multiple panels typically separate them with a fresh
    ``PANEL`` heading. Split points come from :func:`_all_panel_id_matches`
    so the same blocklist-aware logic that powers :func:`_first_panel_id`
    keeps ``PANEL SCHEDULE`` from being treated as a split boundary on
    its own. When the text yields zero panel IDs we return the whole
    text as a single block so the caller can still pair it with the
    first circuit table found.

    Near-duplicate split positions (within 10 chars of an earlier one)
    are collapsed so a heading line and its body don't produce a
    spurious empty block.
    """
    raw_starts = [pos for pos, _ in _all_panel_id_matches(text)]
    if not raw_starts:
        return [text]
    starts: list[int] = []
    for pos in raw_starts:
        if starts and pos - starts[-1] < 10:
            continue
        starts.append(pos)
    blocks: list[str] = []
    for i, start in enumerate(starts):
        end = starts[i + 1] if i + 1 < len(starts) else len(text)
        blocks.append(text[start:end])
    return blocks


def _panel_from_text_block(block_text: str, sheet_id: str | None,
                              page_index: int,
                              circuits: list[CircuitEntry]) -> PanelRecord | None:
    """Build a ``PanelRecord`` from a header-text block + a circuit list."""
    panel_id = _first_panel_id(block_text)
    if not panel_id:
        return None
    voltage, phase_count = _parse_voltage(block_text)
    main_amps, designation = _parse_main_breaker(block_text)
    bus_amps = _parse_bus_amps(block_text)
    feeder_conductor = _parse_feeder_conductor(block_text)
    feeder_conduit = _parse_feeder_conduit(block_text)
    # Bus amps fallback: when only MCB is published, the bus typically
    # matches the main breaker rating (NEC convention).
    if bus_amps is None and main_amps is not None and designation == "MCB":
        bus_amps = main_amps
    confidence = _panel_confidence(
        panel_id=panel_id,
        has_voltage=voltage is not None,
        has_mcb_mlo=designation is not None,
        has_bus_amps=bus_amps is not None,
        circuits=circuits,
    )
    return PanelRecord(
        panel_id=panel_id,
        voltage=voltage,
        phase_count=phase_count,
        main_breaker_amps=main_amps,
        bus_amps=bus_amps,
        mcb_or_mlo=designation,
        feeder_conductor_size=feeder_conductor,
        feeder_conduit_size=feeder_conduit,
        location=None,
        circuits=list(circuits),
        confidence=confidence,
        source_sheet=sheet_id,
        source_page=page_index,
    )


def extract_panel_schedule_from_page(page: "fitz.Page", page_index: int = 0,
                                        *, sheet_id: str | None = None
                                        ) -> PanelScheduleResult:
    """Extract every panel schedule (if any) from a single PyMuPDF page.

    Multi-panel pages: each detected circuit table is paired with the
    nearest panel-ID block in the page text. When the page text yields
    fewer panel IDs than circuit tables we attach the surviving tables
    to the last-seen panel block (a "second panel, same heading" layout
    that some offices use); when it yields more IDs than tables, the
    leftover panel IDs land as panels with zero circuits so the header
    fields still surface.
    """
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _PANEL_SCHEDULE_KEYWORDS)

    header_debug: list[str] = []
    circuit_tables: list[tuple[list[str], list[list[str]]]] = []
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
        if not _looks_like_panel_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        circuit_tables.append((headers, data_rows))
        header_debug.append(" | ".join(headers))

    blocks = _split_panel_blocks(text)
    if not blocks:
        blocks = [text]
    # When the phrase fired but no real panel-ID was extracted, log a warning
    # and return empty so downstream code doesn't fabricate a row.
    if has_phrase and not any(_first_panel_id(b) for b in blocks):
        logger.debug("panel_schedule phrase fired on page %d but no panel ID parsed",
                     page_index)

    panels: list[PanelRecord] = []
    # Pair each circuit table with a panel block. When we have fewer
    # blocks than tables, reuse the last block (single-panel page where
    # the heading text is above the table; or a "continued" table).
    for i, (h, rows) in enumerate(circuit_tables):
        block = blocks[i] if i < len(blocks) else (blocks[-1] if blocks else text)
        circuits = _circuits_from_table(h, rows)
        panel = _panel_from_text_block(block, sheet_id, page_index, circuits)
        if panel:
            panels.append(panel)
    # Any extra panel-id blocks left over (more headings than tables)
    # land as panels with no circuits — their header metadata still
    # round-trips and the synthesiser will emit the panel enclosure +
    # feeder rows.
    for i in range(len(circuit_tables), len(blocks)):
        panel = _panel_from_text_block(blocks[i], sheet_id, page_index, [])
        if panel:
            panels.append(panel)

    # Dedup panels by panel_id within the page (keep the first; the
    # _split_panel_blocks can produce a heading-line block and a body
    # block for the same panel).
    seen: dict[str, PanelRecord] = {}
    for p in panels:
        existing = seen.get(p.panel_id)
        if existing is None:
            seen[p.panel_id] = p
            continue
        # Merge: keep the one with more circuits; otherwise the more
        # decorated header.
        if len(p.circuits) > len(existing.circuits):
            seen[p.panel_id] = p
            continue
        # Fold any fields the existing row left empty.
        merged = PanelRecord(
            panel_id=existing.panel_id,
            voltage=existing.voltage or p.voltage,
            phase_count=existing.phase_count or p.phase_count,
            main_breaker_amps=existing.main_breaker_amps or p.main_breaker_amps,
            bus_amps=existing.bus_amps or p.bus_amps,
            mcb_or_mlo=existing.mcb_or_mlo or p.mcb_or_mlo,
            feeder_conductor_size=existing.feeder_conductor_size or p.feeder_conductor_size,
            feeder_conduit_size=existing.feeder_conduit_size or p.feeder_conduit_size,
            location=existing.location or p.location,
            circuits=existing.circuits if existing.circuits else p.circuits,
            confidence=max(existing.confidence, p.confidence),
            source_sheet=existing.source_sheet or p.source_sheet,
            source_page=existing.source_page,
        )
        seen[p.panel_id] = merged

    final_panels = list(seen.values())
    if not final_panels and has_phrase:
        logger.debug("panel_schedule on page %d found no parseable panels", page_index)

    return PanelScheduleResult(
        pages=[page_index] if final_panels else [],
        panels=final_panels,
        confidence=round(_score(has_phrase, final_panels), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_panel_schedule(pdf_path: Path, page_index: int,
                              *, sheet_id: str | None = None
                              ) -> PanelScheduleResult:
    """Run the panel-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_panel_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: PanelScheduleResult):
    """Return a :class:`core.schemas.PanelScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.PanelScheduleResult(
        pages=list(result.pages),
        panels=[
            S.PanelRecord(
                panel_id=p.panel_id,
                voltage=p.voltage,
                phase_count=p.phase_count,
                main_breaker_amps=p.main_breaker_amps,
                bus_amps=p.bus_amps,
                mcb_or_mlo=p.mcb_or_mlo,
                feeder_conductor_size=p.feeder_conductor_size,
                feeder_conduit_size=p.feeder_conduit_size,
                location=p.location,
                circuits=[
                    S.CircuitEntry(
                        circuit_number=c.circuit_number,
                        breaker_amps=c.breaker_amps,
                        load_description=c.load_description,
                        load_watts=c.load_watts,
                        phase=c.phase,
                    )
                    for c in p.circuits
                ],
                confidence=p.confidence,
                source_sheet=p.source_sheet,
                source_page=p.source_page,
            )
            for p in result.panels
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
