"""Deterministic plumbing fixture schedule extraction (Phase T2.9).

Plumbing fixture schedules live on P-series sheets (``P1.0`` / ``P2.0``
/ ``PL-1``) and close out the Division 22+23+26 typed-schedule trifecta
alongside the panel (T2.6), lighting (T2.7), and HVAC (T2.8) extractors.
Each schedule typically carries:

1. **Fixture tag** — letter+digit identifier with a family prefix
   (``WC-1`` water closet / ``LAV-A`` lavatory / ``URN-1`` urinal /
   ``SH-1`` shower / ``EWC-1`` electric water cooler / ``MS-1`` mop
   sink / ``WH-1`` water heater / ``HD-1`` hose bibb / ``FD-1`` floor
   drain / ``SK-1`` sink).
2. **Description** — free text describing the fixture.
3. **Manufacturer / model** — sometimes one cell joined by ``/``,
   sometimes two distinct columns.
4. **Mounting / type** — ``FLOOR`` / ``WALL`` / ``COUNTER`` / ``DECK``
   / ``FREESTANDING``; preserved as the original string.
5. **Flow rate** — ``1.28 GPF`` (water closets), ``0.5 GPM``
   (lavatory aerators), ``1.5 GPM`` (showerheads).  Eco / efficiency
   specs that drive a meaningful share of the unit's first cost.
6. **Connection sizes** — ``CW`` (cold water), ``HW`` (hot water),
   ``WASTE``, ``VENT``.  Round-trip as the original cell string
   (``"1/2\""`` / ``"3/4\""`` / ``"1-1/2\""`` / ``"2\""``).
7. **Notes** — ADA / ACCESSIBLE / BARRIER-FREE / WHEELCHAIR for
   accessible fixtures; SENSOR / MOTION / AUTOMATIC / TOUCHLESS /
   INFRARED for sensor-operated fixtures.
8. **Optional QTY column** — when present flows through to a high-
   confidence synthesised count (0.90); when absent the synthesiser
   falls back to 0.55 → HAND_TAKEOFF.

The synthesiser downstream
(:func:`core.extraction.takeoff_synthesis.synthesize_plumbing_takeoff_items`)
fans each :class:`PlumbingFixtureRecord` out into 2-3
``TakeoffItem`` families: the fixture itself (CSI per type — WC →
``22 41 13``, LAV → ``22 41 16``, EWC → ``22 47 13``, FD →
``22 13 19``, ...), a parametric MEP rough-in line (``22 11 16`` for
water-supply-dominant fixtures or ``22 13 16`` for waste-dominant),
and optionally a trim / installation-hardware line at 0.70 when both
manufacturer and model_number are populated.

Architectural pattern mirrors :mod:`core.extraction.hvac_schedule`:
pure functions of a ``Path`` + page index (or a ``fitz.Page``),
internal dataclasses with a ``to_schema()`` bridge to the Pydantic
models on :mod:`core.schemas`, and a confidence rubric.  Runs
**independently** of door / window / finish / room precedence —
plumbing schedules live on P-series sheets that those upstream
detectors never claim, same posture as panels + lighting + HVAC.

Substring-collision note: plumbing schedules carry four classes of
single-letter / short-name collision the longest-header-first picker
must resolve:

* ``DESCRIPTION`` (or ``DESC`` / ``D`` / ``DIA``) — bare ``D`` is a
  substring of every ``D``-containing token, so the long form must
  be pinned first and the short form excluded.
* ``TYPE`` / ``TAG`` (or ``T`` / ``TEMP``) — bare ``T`` collides
  with both, and ``TEMP`` (temperature) is a distinct column on
  some schedules.
* ``QUANTITY`` (or ``QTY`` / ``Q``) — same shape as the HVAC /
  lighting / panel collisions.
* ``CW`` / ``HW`` — two-letter connection-size headers that
  substring-match nothing else but must each claim a single column.

Phase T2.9 is the FIFTH downstream consumer of the shared
``header_index_excluding`` helper promoted in Phase T3.6 (Worker CC,
commit ``cb979e6``); doors / panel / lighting / HVAC are the prior
four.  It closes the Division 22+23+26 trifecta entirely.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

from .header_utils import header_index_excluding as _header_index_excluding

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Dataclasses — mirrored by Pydantic models in core.schemas
# ---------------------------------------------------------------------------


@dataclass
class PlumbingFixtureRecord:
    """One plumbing-fixture record pulled off a P-series fixture schedule.

    ``confidence`` defaults to ``0.85`` — fixture rows are well-
    structured and the parser is deterministic, so a clean extraction
    is high confidence by construction.  Partial extractions (tag
    without flow rate, or flow rate without connection sizes) tick
    the confidence down slightly via :func:`_fixture_confidence`.
    """

    fixture_tag: str
    fixture_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    mounting: str | None = None
    flow_rate_value: float | None = None
    flow_rate_unit: str | None = None
    cold_water_size: str | None = None
    hot_water_size: str | None = None
    waste_size: str | None = None
    vent_size: str | None = None
    ada_compliant: bool | None = None
    sensor_operated: bool | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class PlumbingScheduleResult:
    """Aggregate plumbing-fixture-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    fixtures: list[PlumbingFixtureRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Page-level phrase signals.  Any of these in the page text triggers
# the extractor; the absence of all of them does not exclude the page
# because a fixture-table header is sufficient on its own.
_PLUMBING_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "PLUMBING FIXTURE SCHEDULE",
    "PLUMBING SCHEDULE",
    "FIXTURE SCHEDULE",
    "PLUMBING FIXTURES",
    "FIXTURE TYPE",
)


# Tokens that identify a plumbing fixture-table header row.  Requires
# a TAG column AND at least one description-side column AND at least
# one plumbing-specific spec column (GPF / GPM / CW / HW / WASTE /
# VENT / FLOW) — the same three-signal pattern used by door / window
# / finish / panel / lighting / HVAC detection.
_PLUMBING_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "MARK", "TYPE",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "MOUNTING", "MTG",
    "FLOW", "GPF", "GPM",
    "CW", "HW", "WASTE", "VENT",
    "SIZE",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
    "DIA", "D",
    "TEMP", "T",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_plumbing_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a plumbing fixture-table header?

    Requires three signals together to avoid false-positives on
    neighbouring door / window / finish / panel / lighting / HVAC
    schedules:

    1. a tag column (``TAG`` / ``MARK`` / ``TYPE``),
    2. at least one description / spec column (``DESCRIPTION`` /
       ``DESC`` / ``MANUFACTURER`` / ``MFG`` / ``MFR`` / ``MODEL``),
    3. at least one plumbing-specific spec column (``GPF`` / ``GPM``
       / ``CW`` / ``HW`` / ``WASTE`` / ``VENT`` / ``FLOW``).

    Door / window / finish / panel / lighting / HVAC-specific signals
    (``HARDWARE`` / ``GLAZING`` / ``CEILING`` / ``CIRCUIT`` /
    ``BREAKER`` / ``LAMP`` / ``LUMENS`` / ``WATTS`` / ``WATTAGE`` /
    ``CFM`` / ``MBH`` / ``BTUH`` / ``TONS`` / ``REFRIG`` / ``FUEL``)
    actively disqualify the header even when the other classes match
    — this is the belt-and-braces discriminator on top of the
    door/window/finish/panel precedence rules at the dispatcher
    level.  ``MOUNTING`` is intentionally NOT in the disqualifier
    set because plumbing schedules carry a mounting column (FLOOR /
    WALL / COUNTER / DECK / FREESTANDING).
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    disqualifiers = {
        # Door / window
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "OPER",
        "SHGC", "UFACTOR", "UVALUE", "SILL", "FRAME",
        # Panel
        "CIRCUIT", "CKT", "CIR", "BREAKER", "BKR", "AMPS", "AMP",
        # Lighting
        "LAMP", "LAMPS", "LUMENS", "LM",
        "WATTS", "WATTAGE", "BALLAST", "DRIVER",
        "COLOR", "COLOUR", "PAINT",
        # Finish
        "CEILING", "CLG", "BASE",
        # HVAC
        "CFM", "MBH", "BTUH", "BTU", "TONS",
        "REFRIG", "REFRIGERANT", "FUEL", "MOTOR",
        "HP", "PHASE", "VOLTAGE", "VOLTS",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "MARK", "TYPE"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL",
    })
    has_spec = bool(words & {
        "GPF", "GPM", "CW", "HW", "WASTE", "VENT", "FLOW",
    })
    return has_tag and has_desc and has_spec


def detect_plumbing_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains a plumbing fixture schedule.

    Two cheap signals: any of :data:`_PLUMBING_SCHEDULE_KEYWORDS` in
    the page text, OR a plumbing-shaped fixture-table header on any
    detected table.  Either suffices; the header detector ensures we
    catch pages whose phrase trigger uses non-standard wording.
    """
    text = (page.get_text("text") or "").upper()
    for kw in _PLUMBING_SCHEDULE_KEYWORDS:
        if kw in text:
            # Phrase fired — but if a stronger non-plumbing header is
            # actually on the page (e.g. a lighting fixture schedule
            # using the bare "FIXTURE SCHEDULE" phrase), the header
            # check below must still gate.  Only accept the phrase
            # signal when no detected table header looks like a
            # disqualifying schedule.
            try:
                tables = getattr(page.find_tables(), "tables", None) or []
            except Exception:  # pragma: no cover - PyMuPDF internal
                return True
            if not tables:
                return True
            for table in tables:
                try:
                    extracted = table.extract()
                except Exception:  # pragma: no cover - PyMuPDF internal
                    continue
                if not extracted:
                    continue
                headers = [str(h or "") for h in (extracted[0] or [])]
                if _looks_like_plumbing_header(headers):
                    return True
            # Phrase fired with no plumbing-shaped header AND at
            # least one other shape detected.  Reject — the phrase
            # is a coincidence (e.g. lighting / HVAC fixture).
            for table in tables:
                try:
                    extracted = table.extract()
                except Exception:  # pragma: no cover - PyMuPDF internal
                    continue
                if not extracted:
                    continue
                headers = [str(h or "") for h in (extracted[0] or [])]
                words = set()
                for h in headers:
                    if h:
                        words.update(re.findall(r"[A-Za-z]+", h.upper()))
                # Disqualifying header families.
                if words & {"WATTS", "LUMENS", "LAMP", "CFM", "MBH",
                              "TONS", "CIRCUIT", "BREAKER", "HARDWARE"}:
                    return False
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
        if _looks_like_plumbing_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Fixture-type detection from tag prefix
# ---------------------------------------------------------------------------


# Order matters: more-specific / longer prefixes BEFORE shorter ones.
# ``SHU-`` (shower unit / assembly) is checked before bare ``SH-`` so
# a tag ``SHU-1`` doesn't classify as plain SHOWER twice; ``URN-``
# before ``UR-``; ``EWC-`` and ``DF-`` (drinking fountain) both map
# to EWC; ``MS-`` (mop sink) is distinct from ``SK-`` (sink).
_FIXTURE_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("WC",),               "WATER_CLOSET"),
    (("LAV",),              "LAVATORY"),
    (("URN", "UR"),         "URINAL"),
    (("SHU",),              "SHOWER"),
    (("SH",),               "SHOWER"),
    (("EWC", "DF"),         "EWC"),
    (("MS",),               "MOP_SINK"),
    (("SK",),               "SINK"),
    (("WH",),               "WATER_HEATER"),
    (("HD", "HB"),          "HOSE_BIBB"),
    (("FD",),               "FLOOR_DRAIN"),
    (("ICE",),              "OTHER"),
    (("FT",),               "OTHER"),
)


def _classify_fixture_type(tag: str, description: str | None = None) -> str:
    """Classify fixture family from a tag (``WC-1``) or fallback to desc.

    Multi-letter prefixes (``WC`` / ``LAV`` / ``URN`` / ``EWC`` /
    ``SHU``) win when both could match; ``OTHER`` is the fallback.
    """
    raw = (tag or "").strip().upper()
    if not raw:
        if description:
            return _classify_fixture_type(description)
        return "OTHER"
    head = re.split(r"[-_/\s]", raw, maxsplit=1)[0]
    for keywords, label in _FIXTURE_TYPE_PREFIXES:
        for kw in keywords:
            if head == kw:
                return label
    for keywords, label in _FIXTURE_TYPE_PREFIXES:
        for kw in keywords:
            if raw.startswith(kw) and (
                len(raw) == len(kw) or not raw[len(kw)].isalpha()
            ):
                return label
    if description:
        desc_upper = description.upper()
        # Description-based fallback only when the tag was uninformative.
        desc_hints = (
            ("WATER CLOSET",       "WATER_CLOSET"),
            ("TOILET",             "WATER_CLOSET"),
            ("LAVATORY",           "LAVATORY"),
            ("URINAL",             "URINAL"),
            ("SHOWER",             "SHOWER"),
            ("DRINKING FOUNTAIN",  "EWC"),
            ("WATER COOLER",       "EWC"),
            ("MOP SINK",           "MOP_SINK"),
            ("SERVICE SINK",       "MOP_SINK"),
            ("SINK",               "SINK"),
            ("WATER HEATER",       "WATER_HEATER"),
            ("HOSE BIBB",          "HOSE_BIBB"),
            ("HOSE HYDRANT",       "HOSE_BIBB"),
            ("FLOOR DRAIN",        "FLOOR_DRAIN"),
        )
        for kw, label in desc_hints:
            if kw in desc_upper:
                return label
    return "OTHER"


# ---------------------------------------------------------------------------
# Cell-level parsing helpers
# ---------------------------------------------------------------------------


# Flow rate: ``1.28 GPF`` / ``0.5 GPM`` / ``1.5GPM`` / ``1.28``.  When
# the unit suffix is absent the cell is treated as numeric-only; the
# caller can fall back to the column header for the unit.
_FLOW_RATE_RE: re.Pattern[str] = re.compile(
    r"^\s*([\d.]+)\s*(GPF|GPM)?\s*$",
    re.IGNORECASE,
)


def _parse_flow_rate(raw: str | None) -> tuple[float | None, str | None]:
    """Parse a flow-rate cell.  Returns ``(value, unit_or_None)``."""
    if raw is None:
        return None, None
    text = str(raw).strip()
    if not text:
        return None, None
    m = _FLOW_RATE_RE.match(text)
    if m:
        try:
            value = float(m.group(1))
        except ValueError:
            return None, None
        unit = (m.group(2) or "").upper() or None
        return value, unit
    # Fallback: ``"1.28 GPF (low-flow)"`` shape — scrape leading
    # number and any GPF / GPM token nearby.
    leading = re.match(r"\s*([\d.]+)", text)
    if not leading:
        return None, None
    try:
        value = float(leading.group(1))
    except ValueError:
        return None, None
    unit_match = re.search(r"\b(GPF|GPM)\b", text, re.IGNORECASE)
    unit = unit_match.group(1).upper() if unit_match else None
    return value, unit


def _flow_unit_from_header(header: str | None) -> str | None:
    """Infer flow-rate unit from the column header text."""
    if not header:
        return None
    norm = _normalize_header(header)
    if not norm:
        return None
    if "GPF" in norm:
        return "GPF"
    if "GPM" in norm:
        return "GPM"
    return None


def _parse_quantity(raw: str | None) -> int | None:
    """Parse a QTY cell.  Plain integer expected; non-numeric → None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"^\s*(\d+)\s*(?:EA)?\s*$", text, re.IGNORECASE)
    if not m:
        return None
    return int(m.group(1))


def _normalise_connection_size(raw: str | None) -> str | None:
    """Strip whitespace; preserve fractions and inch-marks.

    The connection size round-trips as the original cell string so
    ``"1-1/2\""`` and ``"3/4\""`` survive untouched.  ``""`` / ``"-"``
    / ``"N/A"`` collapse to ``None`` so callers don't see spurious
    placeholders.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    if text.upper() in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    return text


# Notes-side feature detectors.  ADA / SENSOR detection scans every
# free-text field on the row (description + notes) for a small
# allowlist of established phrasings.
_ADA_KEYWORDS: tuple[str, ...] = (
    "ADA", "ACCESSIBLE", "BARRIER-FREE", "BARRIER FREE",
    "WHEELCHAIR", "HANDICAP", "HC",
)
_SENSOR_KEYWORDS: tuple[str, ...] = (
    "SENSOR", "MOTION", "AUTOMATIC", "TOUCHLESS",
    "INFRARED", "IR", "HANDS-FREE", "HANDS FREE",
)


def _detect_ada(*texts: str | None) -> bool | None:
    """Return True when any text mentions an ADA / accessibility marker."""
    blob = " ".join(t for t in texts if t)
    if not blob:
        return None
    upper = blob.upper()
    for kw in _ADA_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", upper):
            return True
    return None


def _detect_sensor(*texts: str | None) -> bool | None:
    """Return True when any text mentions a sensor-operated marker."""
    blob = " ".join(t for t in texts if t)
    if not blob:
        return None
    upper = blob.upper()
    for kw in _SENSOR_KEYWORDS:
        if re.search(rf"\b{re.escape(kw)}\b", upper):
            return True
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


# Header candidate lists.  The order of the inner tuples does NOT
# express priority — the picking logic always pins the LONGEST /
# most-specific candidate first to avoid substring collisions
# (``DESCRIPTION`` before ``DESC``/``D``; ``TYPE``/``TAG`` before
# ``T``; ``QUANTITY`` before ``QTY`` before ``Q``).
_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":          ("TAG", "MARK"),
    "type_col":     ("TYPE",),
    "desc_long":    ("DESCRIPTION", "DESC"),
    "desc_short":   ("D", "DIA"),
    "mfr":          ("MANUFACTURER", "MFR", "MFG", "MAKER"),
    "model":        ("MODEL", "MODEL NO", "PART"),
    "mounting":     ("MOUNTING", "MTG", "MOUNT"),
    "flow":         ("FLOW", "GPF", "GPM"),
    "cw":           ("CW", "COLD"),
    "hw":           ("HW", "HOT"),
    "waste":        ("WASTE", "DRAIN"),
    "vent":         ("VENT",),
    "size":         ("SIZE",),
    "qty_long":     ("QUANTITY", "QTY"),
    "qty_short":    ("Q",),
    "notes":        ("NOTES", "REMARKS", "COMMENTS"),
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


def _fixture_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick the plumbing fixture-table column indices for ONE schedule.

    Resolves the plumbing-specific class of single-letter / short-name
    collision by a TWO-PASS strategy: pin every LONG-FORM column
    first (so each multi-letter header claims its proper slot), then
    run the SHORT-FORM lookups with EVERY long-form index in the
    exclusion set.  Structurally identical to the HVAC two-pass
    picker but with plumbing-specific collisions:

    1. ``DESCRIPTION`` before bare ``D`` / ``DIA`` (``D`` substring-
       collides with every other ``D``-containing word).
    2. ``TYPE`` / ``TAG`` before bare ``T`` (``T`` substring-
       collides with ``TYPE`` / ``TEMP`` if not excluded).
    3. ``QUANTITY`` / ``QTY`` before bare ``Q``.
    4. ``CW`` / ``HW`` once their respective columns are claimed —
       the two-letter forms substring-match nothing else but each
       must claim a distinct column.

    This is the FIFTH downstream consumer of
    :func:`_header_index_excluding` from :mod:`header_utils` — door /
    panel / lighting / HVAC are the prior four.
    """
    # ---- Pin TAG (and TYPE as a tag fallback) ----
    tag_idx = _header_index(headers, _HEADERS["tag"])
    # Some schedules use a ``TYPE`` column as the primary tag; pin it
    # second so a real ``TAG`` column wins when both are present.
    type_idx = _header_index_excluding(
        headers, _HEADERS["type_col"],
        exclude={i for i in (tag_idx,) if i is not None},
    )

    # ---- DESCRIPTION (long) before D / DIA (short) ----
    desc_long_idx = _header_index_excluding(
        headers, _HEADERS["desc_long"],
        exclude={i for i in (tag_idx, type_idx) if i is not None},
    )

    mfr_idx = _header_index_excluding(
        headers, _HEADERS["mfr"],
        exclude={i for i in (tag_idx, type_idx, desc_long_idx)
                  if i is not None},
    )
    model_idx = _header_index_excluding(
        headers, _HEADERS["model"],
        exclude={i for i in (tag_idx, type_idx, desc_long_idx, mfr_idx)
                  if i is not None},
    )
    mounting_idx = _header_index_excluding(
        headers, _HEADERS["mounting"],
        exclude={i for i in (tag_idx, type_idx, desc_long_idx, mfr_idx,
                              model_idx) if i is not None},
    )

    # ---- Pin connection-size + flow columns BEFORE short forms ----
    long_exclude: set[int] = {
        i for i in (tag_idx, type_idx, desc_long_idx, mfr_idx, model_idx,
                     mounting_idx) if i is not None
    }
    flow_idx = _header_index_excluding(
        headers, _HEADERS["flow"], exclude=set(long_exclude),
    )
    if flow_idx is not None:
        long_exclude.add(flow_idx)
    cw_idx = _header_index_excluding(
        headers, _HEADERS["cw"], exclude=set(long_exclude),
    )
    if cw_idx is not None:
        long_exclude.add(cw_idx)
    hw_idx = _header_index_excluding(
        headers, _HEADERS["hw"], exclude=set(long_exclude),
    )
    if hw_idx is not None:
        long_exclude.add(hw_idx)
    waste_idx = _header_index_excluding(
        headers, _HEADERS["waste"], exclude=set(long_exclude),
    )
    if waste_idx is not None:
        long_exclude.add(waste_idx)
    vent_idx = _header_index_excluding(
        headers, _HEADERS["vent"], exclude=set(long_exclude),
    )
    if vent_idx is not None:
        long_exclude.add(vent_idx)
    size_idx = _header_index_excluding(
        headers, _HEADERS["size"], exclude=set(long_exclude),
    )
    if size_idx is not None:
        long_exclude.add(size_idx)
    qty_long_idx = _header_index_excluding(
        headers, _HEADERS["qty_long"], exclude=set(long_exclude),
    )
    if qty_long_idx is not None:
        long_exclude.add(qty_long_idx)
    notes_idx = _header_index_excluding(
        headers, _HEADERS["notes"], exclude=set(long_exclude),
    )
    if notes_idx is not None:
        long_exclude.add(notes_idx)

    # ---- Now pin SHORT-FORM columns with every long form excluded ----
    desc_short_idx = _header_index_excluding(
        headers, _HEADERS["desc_short"], exclude=set(long_exclude),
    )
    if desc_short_idx is not None:
        long_exclude.add(desc_short_idx)
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"], exclude=set(long_exclude),
    )
    if qty_short_idx is not None:
        long_exclude.add(qty_short_idx)

    # Resolve final indices: long-form wins when both are present;
    # short-form supplies the value when no long-form column exists.
    desc_idx = desc_long_idx if desc_long_idx is not None else desc_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":      tag_idx,
        "type":     type_idx,
        "desc":     desc_idx,
        "mfr":      mfr_idx,
        "model":    model_idx,
        "mounting": mounting_idx,
        "flow":     flow_idx,
        "cw":       cw_idx,
        "hw":       hw_idx,
        "waste":    waste_idx,
        "vent":     vent_idx,
        "size":     size_idx,
        "qty":      qty_idx,
        "notes":    notes_idx,
    }


# Fixture-tag pattern.  Accepts a letter prefix (1-6 chars) optionally
# followed by digits / dashes / letters: ``WC-1``, ``LAV-A``, ``URN-1``,
# ``EWC-1``, ``SH-2``, ``SHU-1``, ``FD-1``, ``WH-1``.
_FIXTURE_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[PlumbingFixtureRecord]:
    """Convert one fixture table's rows to ``PlumbingFixtureRecord`` instances."""
    idx = _fixture_indices(headers)
    # Determine the flow unit at the table level — the header wins.
    flow_header_idx = idx["flow"]
    flow_header = (
        headers[flow_header_idx] if flow_header_idx is not None else None
    )
    flow_header_unit = _flow_unit_from_header(flow_header)

    records: list[PlumbingFixtureRecord] = []
    for row in data_rows:
        if not row:
            continue
        tag = _cell(row, idx["tag"])
        if not tag and idx["type"] is not None:
            # Some plumbing schedules use the ``TYPE`` column as the
            # primary tag; fall back to it when ``TAG`` is empty.
            tag = _cell(row, idx["type"])
        if not tag:
            continue
        tag = tag.strip().strip(".,:")
        if not tag:
            continue
        if not _FIXTURE_TAG_RE.match(tag):
            stripped = re.sub(r"^(?:TAG|MARK|TYPE)\s+", "", tag,
                                 flags=re.IGNORECASE)
            if _FIXTURE_TAG_RE.match(stripped):
                tag = stripped
            else:
                continue

        desc = _cell(row, idx["desc"])
        mfr = _cell(row, idx["mfr"])
        model = _cell(row, idx["model"])
        mounting = _cell(row, idx["mounting"])
        flow_raw = _cell(row, idx["flow"])
        cw_raw = _cell(row, idx["cw"])
        hw_raw = _cell(row, idx["hw"])
        waste_raw = _cell(row, idx["waste"])
        vent_raw = _cell(row, idx["vent"])
        size_raw = _cell(row, idx["size"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        # Manufacturer / model number may live in the same cell joined
        # by ``/`` (``"American Standard / 3461.001"``).
        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

        flow_value, flow_unit = _parse_flow_rate(flow_raw)
        if flow_value is not None and flow_unit is None:
            flow_unit = flow_header_unit

        cold_water_size = _normalise_connection_size(cw_raw)
        hot_water_size = _normalise_connection_size(hw_raw)
        waste_size = _normalise_connection_size(waste_raw)
        vent_size = _normalise_connection_size(vent_raw)
        # Generic ``SIZE`` column without a CW/HW header → assume cold
        # water (the dominant supply on most fixtures) if cw_idx
        # didn't fire.
        if cold_water_size is None and size_raw and idx["cw"] is None:
            cold_water_size = _normalise_connection_size(size_raw)

        quantity = _parse_quantity(qty_raw)
        fixture_type = _classify_fixture_type(tag, desc)
        ada = _detect_ada(desc, notes_raw)
        sensor = _detect_sensor(desc, notes_raw)

        confidence = _fixture_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_flow=flow_value is not None,
            has_connections=any(s is not None for s in (
                cold_water_size, hot_water_size, waste_size, vent_size,
            )),
            has_mounting=bool(mounting),
        )

        records.append(PlumbingFixtureRecord(
            fixture_tag=tag,
            fixture_type=fixture_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            mounting=(mounting.strip() if mounting else None),
            flow_rate_value=flow_value,
            flow_rate_unit=flow_unit,
            cold_water_size=cold_water_size,
            hot_water_size=hot_water_size,
            waste_size=waste_size,
            vent_size=vent_size,
            ada_compliant=ada,
            sensor_operated=sensor,
            quantity=quantity,
            notes=notes_raw,
            confidence=confidence,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _fixture_confidence(*, tag: str, has_description: bool,
                          has_manufacturer: bool, has_model: bool,
                          has_flow: bool, has_connections: bool,
                          has_mounting: bool) -> float:
    """0.85 baseline; ticks up to ~0.95 fully decorated, down to 0.65 partial.

    Tag alone (no description, no specs) lands at 0.65.  Every
    additional piece (description, manufacturer, model, flow rate,
    connection size, mounting) ticks the row up so a fully-decorated
    fixture row lands above the AUTO_APPROVE threshold (0.85).
    """
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_model,
        has_flow, has_connections, has_mounting,
    ]
    score += 0.05 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, fixtures: list[PlumbingFixtureRecord]) -> float:
    """Aggregate 0..1 confidence for the page-level result."""
    if not fixtures:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30  # at least one fixture extracted
    if any(f.flow_rate_value is not None for f in fixtures):
        score += 0.15
    if len(fixtures) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_plumbing_schedule_from_page(
    page: "fitz.Page", page_index: int = 0,
    *, sheet_id: str | None = None,
) -> PlumbingScheduleResult:
    """Extract every plumbing fixture schedule (if any) from a single page.

    Multi-table pages: every table whose header passes
    :func:`_looks_like_plumbing_header` contributes its records to
    the aggregate result so a page with separate fixture / floor-drain
    tables produces records from both.
    """
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _PLUMBING_SCHEDULE_KEYWORDS)

    all_records: list[PlumbingFixtureRecord] = []
    header_debug: list[str] = []

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
        if not _looks_like_plumbing_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if not records:
            continue
        for r in records:
            r.source_sheet = sheet_id
            r.source_page = page_index
        all_records.extend(records)
        header_debug.append(" | ".join(headers))

    if not all_records and has_phrase:
        logger.debug(
            "plumbing_schedule phrase fired on page %d but no fixtures parsed",
            page_index,
        )

    return PlumbingScheduleResult(
        pages=[page_index] if all_records else [],
        fixtures=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_plumbing_schedule(pdf_path: Path, page_index: int,
                                  *, sheet_id: str | None = None,
                                  ) -> PlumbingScheduleResult:
    """Run the plumbing-fixture-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_plumbing_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: PlumbingScheduleResult):
    """Return a :class:`core.schemas.PlumbingScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.PlumbingScheduleResult(
        pages=list(result.pages),
        fixtures=[
            S.PlumbingFixtureRecord(
                fixture_tag=f.fixture_tag,
                fixture_type=f.fixture_type,
                description=f.description,
                manufacturer=f.manufacturer,
                model_number=f.model_number,
                mounting=f.mounting,
                flow_rate_value=f.flow_rate_value,
                flow_rate_unit=f.flow_rate_unit,
                cold_water_size=f.cold_water_size,
                hot_water_size=f.hot_water_size,
                waste_size=f.waste_size,
                vent_size=f.vent_size,
                ada_compliant=f.ada_compliant,
                sensor_operated=f.sensor_operated,
                quantity=f.quantity,
                notes=f.notes,
                confidence=f.confidence,
                source_sheet=f.source_sheet,
                source_page=f.source_page,
            )
            for f in result.fixtures
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
