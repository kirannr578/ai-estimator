"""Deterministic lighting-fixture-schedule extraction (Phase T2.7).

Lighting-fixture schedules live on electrical sheets (E1.0 / E2.0 /
EL.0 / E-1) and are the second-highest single Division 26 line item
after panel hardware in BPC's calibration cost distribution.  A
typical lighting-fixture schedule on a commercial bid set carries:

1. **Fixture tag** — short letter or letter+digit identifier
   (``A1`` / ``B`` / ``C2`` / ``F1``).
2. **Description** — free text describing the fixture
   (``"2x4 LED RECESSED TROFFER 4000K"``).
3. **Manufacturer + catalog number** — sometimes one cell
   (``"Lithonia / 2BLT4-40L-LP840"``) sometimes two columns.
4. **Lamp / LED specs** — wattage, lumens, color temperature, lamp
   technology family (``LED`` / ``FLUORESCENT`` / ``HID`` / ``INCAN``).
5. **Voltage** — ``120V`` / ``277V`` / ``120/277V`` / ``0-10V dim`` /
   ``DALI``.
6. **Mounting** — ``RECESSED`` / ``SURFACE`` / ``SUSPENDED`` /
   ``PENDANT`` / ``WALL``.
7. **Notes** — emergency, dimmable, occupancy sensor, etc.
8. **Optional QTY column** — less common, but when present feeds the
   synthesised quantity at high confidence.

The synthesiser downstream (:mod:`core.extraction.takeoff_synthesis`)
fans each ``LightingFixtureRecord`` out into 1-2 families of
``TakeoffItem``: the fixture itself (EA at ``26 51 13`` interior or
``26 51 19`` wall-mounted) and, when the lamp technology is
fluorescent or HID, a lamp/driver LS line at ``26 55 53``.  LED
integrated fixtures emit only the fixture row.

Architectural pattern mirrors :mod:`core.extraction.panel_schedule` /
:mod:`core.extraction.finish_schedule`: pure functions of a ``Path`` +
page index (or a ``fitz.Page``), internal dataclasses with a
``to_schema()`` bridge to the Pydantic models on :mod:`core.schemas`,
and a confidence rubric.  Runs **alongside** (never instead of) the
existing F3 prepass and the door / window / finish / room / panel
extractors; lighting-fixture schedules typically live on E-series
pages that those upstream detectors leave untouched (same precedence
posture as panel schedules).

Substring-collision note: the WATTAGE column is often labelled simply
``W`` (one letter), which collides via substring with the full
``WATTS`` header on schedules that publish a separate footnote column
also tagged ``WATTS``.  The QUANTITY column is sometimes abbreviated
to ``Q`` (one letter) and substring-collides with ``QTY`` /
``QUANTITY``.  This module pins the longer-name column first and
re-picks the short form with the longer index excluded — the same
``_header_index_excluding`` pattern Worker U promoted out of
``door_schedule`` and that Worker Z reused for ``panel_schedule``
(this is the second downstream validation of the shared helper).
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
class LightingFixtureRecord:
    """One lighting fixture pulled off a lighting-fixture schedule.

    ``confidence`` defaults to ``0.85`` — fixture rows are well-
    structured and the parser is deterministic, so a clean extraction
    is high confidence by construction.  Partial extractions (a tag
    without a description, or a description without a manufacturer)
    tick the confidence down slightly via :func:`_fixture_confidence`.
    """

    fixture_tag: str
    description: str
    manufacturer: str | None = None
    catalog_number: str | None = None
    wattage: float | None = None
    lumens: int | None = None
    color_temp_k: int | None = None
    voltage: str | None = None
    lamp_type: str | None = None
    mounting: str | None = None
    dimmable: bool | None = None
    emergency: bool | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class LightingScheduleResult:
    """Aggregate lighting-fixture-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    fixtures: list[LightingFixtureRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Page-level phrase signals.  Any of these in the page text triggers
# the extractor; the absence of all six does not exclude the page
# because a fixture-table header is sufficient on its own.
_LIGHTING_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "LIGHTING FIXTURE SCHEDULE",
    "LIGHTING FIXTURE",
    "LUMINAIRE SCHEDULE",
    "FIXTURE SCHEDULE",
    "LIGHT FIXTURE SCHEDULE",
    "LTG FIXTURE",
    "FIXTURE TYPE",
)


# Tokens that identify a fixture-table header row.  Requires a TAG
# column AND at least one description-side column AND at least one
# spec-side column (manufacturer / catalog / wattage / voltage /
# mounting) — the same three-signal pattern used by door / window /
# finish / panel detection so a non-lighting table never fires.
_LIGHTING_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "TYPE", "MARK", "FIXTURE", "SYMBOL", "SYM",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "CATALOG", "CAT",
    "WATTS", "W", "WATTAGE",
    "LAMP", "LAMPS",
    "LUMENS", "LM",
    "VOLTAGE", "V", "VOLTS",
    "MOUNTING", "MTG", "MOUNT",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_lighting_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like a lighting-fixture header row?

    Requires three signals together to avoid false-positives on
    neighbouring door / window / finish / panel schedules:

    1. a tag column (``TAG`` / ``TYPE`` / ``MARK`` / ``FIXTURE`` /
       ``SYMBOL``),
    2. at least one description / spec column (``DESCRIPTION`` /
       ``DESC`` / ``MANUFACTURER`` / ``MFG`` / ``MFR`` / ``CATALOG`` /
       ``CAT``),
    3. at least one electrical-spec column (``WATTS`` / ``W`` /
       ``WATTAGE`` / ``LAMP`` / ``LUMENS`` / ``LM`` / ``VOLTAGE`` /
       ``V`` / ``MOUNTING`` / ``MTG``).

    Door-/window-/finish-/panel-specific signals (``HARDWARE`` /
    ``GLAZING`` / ``CEILING`` / ``CIRCUIT`` / ``BREAKER``) actively
    disqualify the header even when the other classes match — this
    is the belt-and-braces discriminator on top of the
    door/window/finish/panel-precedence rules at the dispatcher level.
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    # Hard-reject if the row carries a discriminating column from
    # another schedule family.
    disqualifiers = {
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "OPER",
        "SHGC", "UFACTOR", "UVALUE", "SILL", "FRAME",
        "CIRCUIT", "CKT", "CIR", "BREAKER", "BKR", "PHASE",
        "CEILING", "CLG", "BASE", "FLOOR",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "TYPE", "MARK", "FIXTURE", "SYMBOL", "SYM"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR",
        "CATALOG", "CAT", "MODEL",
    })
    has_spec = bool(words & {
        "WATTS", "W", "WATTAGE", "LAMP", "LAMPS", "LUMENS", "LM",
        "VOLTAGE", "V", "VOLTS", "MOUNTING", "MTG", "MOUNT",
    })
    return has_tag and has_desc and has_spec


def detect_lighting_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains a lighting-fixture schedule.

    Two cheap signals: any of :data:`_LIGHTING_SCHEDULE_KEYWORDS` in
    the page text, OR a lighting-shaped fixture-table header on any
    detected table.  Either suffices.
    """
    text = (page.get_text("text") or "").upper()
    for kw in _LIGHTING_SCHEDULE_KEYWORDS:
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
        if _looks_like_lighting_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Cell-level parsing helpers
# ---------------------------------------------------------------------------


# Wattage: accept "15", "15W", "15 W", "15 WATTS", "15 watt", "15.5W".
_WATTAGE_RE: re.Pattern[str] = re.compile(
    r"^\s*(\d+(?:\.\d+)?)\s*(?:W(?:ATT(?:S)?)?|w(?:att(?:s)?)?)?\s*$",
    re.IGNORECASE,
)
# Lumens: "3500", "3500 lm", "3500LM", "3,500 lumens".
_LUMENS_RE: re.Pattern[str] = re.compile(
    r"^\s*([\d,]+)\s*(?:L(?:M|UMEN(?:S)?)?)?\s*$",
    re.IGNORECASE,
)
# Color temp K: "4000K", "4000 K", "4000Kelvin", "3000K".
_COLOR_TEMP_RE: re.Pattern[str] = re.compile(
    r"\b(\d{4,5})\s*K(?:ELVIN)?\b",
    re.IGNORECASE,
)
# Voltage: "120V", "277V", "120/277V", "120-277V".
_VOLTAGE_DUAL_RE: re.Pattern[str] = re.compile(
    r"\b(120|208|240|277|347|480)\s*[/\-]\s*(120|208|240|277|347|480)\s*V\b",
    re.IGNORECASE,
)
_VOLTAGE_SINGLE_RE: re.Pattern[str] = re.compile(
    r"\b(120|208|240|277|347|480|600)\s*V\b",
    re.IGNORECASE,
)


def _parse_wattage(raw: str | None) -> float | None:
    """Parse a wattage cell (``15`` / ``15W`` / ``15 W`` / ``15 WATTS``)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _WATTAGE_RE.match(text)
    if m:
        try:
            value = float(m.group(1))
        except ValueError:
            return None
        return value if value >= 0 else None
    # Fall back to leading number — covers ``15W LED`` and similar.
    leading = re.match(r"\s*(\d+(?:\.\d+)?)", text)
    if leading:
        try:
            value = float(leading.group(1))
        except ValueError:
            return None
        return value if value >= 0 else None
    return None


def _parse_lumens(raw: str | None) -> int | None:
    """Parse a lumens cell (``3500`` / ``3500 lm`` / ``3,500 LM``)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _LUMENS_RE.match(text)
    if not m:
        return None
    digits = m.group(1).replace(",", "")
    if not digits.isdigit():
        return None
    return int(digits)


def _parse_color_temp(text: str | None) -> int | None:
    """Pull a Kelvin temperature out of free text (``"4000K"`` / ``"3000K LED"``)."""
    if not text:
        return None
    m = _COLOR_TEMP_RE.search(str(text))
    if not m:
        return None
    return int(m.group(1))


def _parse_voltage_cell(raw: str | None) -> str | None:
    """Parse a voltage cell.  Preserves the dual format (``120/277V``)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    m = _VOLTAGE_DUAL_RE.search(upper)
    if m:
        return f"{m.group(1)}/{m.group(2)}V"
    m = _VOLTAGE_SINGLE_RE.search(upper)
    if m:
        return f"{m.group(1)}V"
    # Free-text fallback (``"DALI 277V"`` / ``"0-10V DIM"``) — return
    # the stripped original so the spec round-trips intact.
    return text


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


# Lamp-technology keywords used by :func:`_classify_lamp_type`.  Order
# matters: ``LED`` checked first because it appears in many modern
# fixture descriptions; ``METAL HALIDE`` / ``HPS`` map onto ``HID``.
_LAMP_TYPE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("LED",), "LED"),
    (("FLUORESCENT", "FLUOR", "T8", "T5", "CFL"), "FLUORESCENT"),
    (("METAL HALIDE", "MH", "HPS", "HID"), "HID"),
    (("INCANDESCENT", "INCAN", "HALOGEN"), "INCAN"),
)


def _classify_lamp_type(*texts: str | None) -> str | None:
    """Heuristic-classify lamp technology from any concatenated text."""
    blob = " ".join(t for t in texts if t).upper()
    if not blob:
        return None
    for keywords, label in _LAMP_TYPE_KEYWORDS:
        for kw in keywords:
            # Whole-word boundary to keep ``LEDGE`` from triggering ``LED``.
            if re.search(rf"\b{re.escape(kw)}\b", blob):
                return label
    return None


_MOUNTING_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("RECESSED", "RECESS", "RECESS-MTD"), "RECESSED"),
    (("SUSPENDED", "SUSPEND"), "SUSPENDED"),
    (("PENDANT",), "PENDANT"),
    (("WALL", "WALL-MOUNTED", "WALL MOUNT", "WALL MTD"), "WALL"),
    (("SURFACE", "SURF-MTD", "SURFACE-MOUNTED"), "SURFACE"),
)


def _classify_mounting(*texts: str | None) -> str | None:
    """Heuristic-classify mounting from any concatenated text."""
    blob = " ".join(t for t in texts if t).upper()
    if not blob:
        return None
    for keywords, label in _MOUNTING_KEYWORDS:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", blob):
                return label
    return None


# Dimmable triggers from description / notes.  Tested as case-
# insensitive whole-word / phrase matches; the order of the tuple
# doesn't matter (any hit fires).
_DIMMABLE_KEYWORDS: tuple[str, ...] = (
    "DIM", "DIMMABLE", "DIMMING",
    "0-10V", "0-10 V",
    "DALI", "DALI-2",
    "TRIAC", "ELV", "MLV", "PHASE-CUT", "PHASE CUT",
)


def _detect_dimmable(*texts: str | None) -> bool | None:
    """True/False/None for dimmable based on description / notes text."""
    blob = " ".join(t for t in texts if t).upper()
    if not blob:
        return None
    for kw in _DIMMABLE_KEYWORDS:
        if re.search(rf"(?<![A-Z]){re.escape(kw)}(?![A-Z])", blob):
            return True
    # No positive signal — return None rather than False because the
    # schedule simply didn't say (vs. published-as-non-dim).
    return None


_EMERGENCY_KEYWORDS: tuple[str, ...] = (
    "EMERG", "EMERGENCY", "BATTERY BACKUP", "BATT BACKUP", "EMER",
    "EM/EMER",
)
# Stand-alone "EM" needs a word-boundary that tolerates a leading
# slash (``EM/EMER``) and trailing slash / digit but rejects letter
# continuations like ``EMERGE``.
_EM_TOKEN_RE: re.Pattern[str] = re.compile(
    r"(?<![A-Z])EM(?![A-Z])",
    re.IGNORECASE,
)


def _detect_emergency(*texts: str | None) -> bool | None:
    """True/False/None for emergency based on description / notes text."""
    blob = " ".join(t for t in texts if t).upper()
    if not blob:
        return None
    for kw in _EMERGENCY_KEYWORDS:
        if re.search(rf"(?<![A-Z]){re.escape(kw)}(?![A-Z])", blob):
            return True
    if _EM_TOKEN_RE.search(blob):
        return True
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


# Header candidate lists. The order of the inner tuples does NOT
# express priority — the picking logic always pins the LONGEST /
# most-specific candidate first to avoid substring collisions
# (``WATTS`` before ``W``, ``QUANTITY`` / ``QTY`` before ``Q``,
# ``VOLTAGE`` / ``VOLTS`` before ``V``).
_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":        ("TAG", "TYPE", "MARK", "FIXTURE", "SYMBOL", "SYM"),
    "desc":       ("DESCRIPTION", "DESC"),
    "mfr":        ("MANUFACTURER", "MFR", "MFG", "MAKER"),
    "catalog":    ("CATALOG", "CAT", "MODEL", "PART"),
    "watts_long": ("WATTAGE", "WATTS"),
    "watts_short":("W",),
    "lamp":       ("LAMP", "LAMPS"),
    "lumens":     ("LUMENS", "LM"),
    "voltage_long": ("VOLTAGE", "VOLTS"),
    "voltage_short":("V",),
    "mounting":   ("MOUNTING", "MTG", "MOUNT"),
    "qty_long":   ("QUANTITY", "QTY"),
    "qty_short":  ("Q",),
    "notes":      ("NOTES", "REMARKS", "COMMENTS"),
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
    """Pick the fixture-table column indices for ONE schedule.

    Resolves three classes of single-letter / short-name collision
    by pinning the longer form first and re-picking the short form
    with the longer index excluded:

    1. ``WATTAGE`` / ``WATTS`` before bare ``W`` (``W`` is a
       substring of ``WATTS`` AND ``WATTAGE``, so a row with both
       columns would otherwise land ``W`` on the wider header).
    2. ``VOLTAGE`` / ``VOLTS`` before bare ``V``.
    3. ``QUANTITY`` / ``QTY`` before bare ``Q``.

    This is the SECOND downstream validation of
    :func:`_header_index_excluding` from :mod:`door_schedule` — the
    first reuse was Worker Z's panel_schedule landing in T2.6.
    """
    tag_idx = _header_index(headers, _HEADERS["tag"])
    desc_idx = _header_index_excluding(
        headers, _HEADERS["desc"],
        exclude={i for i in (tag_idx,) if i is not None},
    )
    mfr_idx = _header_index_excluding(
        headers, _HEADERS["mfr"],
        exclude={i for i in (tag_idx, desc_idx) if i is not None},
    )
    catalog_idx = _header_index_excluding(
        headers, _HEADERS["catalog"],
        exclude={i for i in (tag_idx, desc_idx, mfr_idx) if i is not None},
    )

    # WATTAGE / WATTS pinned first; bare W picked with the longer
    # index excluded.  When the row has BOTH columns the bare W
    # column lands on its own header; when the row has only the
    # short W, the long-form lookup is None and the short-form
    # lookup finds it.
    watts_long_idx = _header_index(headers, _HEADERS["watts_long"])
    watts_short_idx = _header_index_excluding(
        headers, _HEADERS["watts_short"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_long_idx,
        ) if i is not None},
    )
    watts_idx = watts_long_idx if watts_long_idx is not None else watts_short_idx

    lamp_idx = _header_index_excluding(
        headers, _HEADERS["lamp"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
        ) if i is not None},
    )
    lumens_idx = _header_index_excluding(
        headers, _HEADERS["lumens"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx, lamp_idx,
        ) if i is not None},
    )

    # VOLTAGE / VOLTS pinned first; bare V picked with longer
    # index excluded.
    voltage_long_idx = _header_index_excluding(
        headers, _HEADERS["voltage_long"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx,
        ) if i is not None},
    )
    voltage_short_idx = _header_index_excluding(
        headers, _HEADERS["voltage_short"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx, voltage_long_idx,
        ) if i is not None},
    )
    voltage_idx = voltage_long_idx if voltage_long_idx is not None else voltage_short_idx

    mounting_idx = _header_index_excluding(
        headers, _HEADERS["mounting"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx, voltage_idx,
        ) if i is not None},
    )

    # QUANTITY / QTY pinned first; bare Q picked with longer index
    # excluded.  Same shape as the WATTS / W case.
    qty_long_idx = _header_index_excluding(
        headers, _HEADERS["qty_long"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx, voltage_idx, mounting_idx,
        ) if i is not None},
    )
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx, voltage_idx, mounting_idx, qty_long_idx,
        ) if i is not None},
    )
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    notes_idx = _header_index_excluding(
        headers, _HEADERS["notes"],
        exclude={i for i in (
            tag_idx, desc_idx, mfr_idx, catalog_idx, watts_idx,
            lamp_idx, lumens_idx, voltage_idx, mounting_idx, qty_idx,
        ) if i is not None},
    )

    return {
        "tag":      tag_idx,
        "desc":     desc_idx,
        "mfr":      mfr_idx,
        "catalog":  catalog_idx,
        "watts":    watts_idx,
        "lamp":     lamp_idx,
        "lumens":   lumens_idx,
        "voltage":  voltage_idx,
        "mounting": mounting_idx,
        "qty":      qty_idx,
        "notes":    notes_idx,
    }


# Fixture-tag pattern.  Accepts a letter (or letter+digit, optionally
# hyphenated): ``A``, ``A1``, ``B-2``, ``C2``, ``FL-1``, ``EX-A``.
_FIXTURE_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,3}(?:[-_]?\d{1,3})?[A-Z]?\s*$",
    re.IGNORECASE,
)


def _records_from_table(headers: list[str], data_rows: list[list[str]],
                          page_index: int) -> list[LightingFixtureRecord]:
    """Convert one fixture table's rows to ``LightingFixtureRecord`` instances."""
    idx = _fixture_indices(headers)
    records: list[LightingFixtureRecord] = []
    for row in data_rows:
        if not row:
            continue
        tag = _cell(row, idx["tag"])
        if not tag:
            continue
        # Strip surrounding punctuation but keep meaningful tag chars.
        tag = tag.strip().strip(".,:")
        if not tag:
            continue
        # Filter out rows whose first column isn't a plausible
        # fixture tag (sub-headers and continuation rows that survive
        # grid extraction).
        if not _FIXTURE_TAG_RE.match(tag):
            # Allow simple multi-word "TYPE A1" patterns by stripping
            # the leading "TYPE " keyword if present.
            stripped = re.sub(r"^(?:TYPE|MARK|TAG)\s+", "", tag, flags=re.IGNORECASE)
            if _FIXTURE_TAG_RE.match(stripped):
                tag = stripped
            else:
                continue

        desc = _cell(row, idx["desc"]) or ""
        mfr = _cell(row, idx["mfr"])
        catalog = _cell(row, idx["catalog"])
        watts_raw = _cell(row, idx["watts"])
        lamp_raw = _cell(row, idx["lamp"])
        lumens_raw = _cell(row, idx["lumens"])
        voltage_raw = _cell(row, idx["voltage"])
        mounting_raw = _cell(row, idx["mounting"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        # Manufacturer / catalog # may live in the same cell joined
        # by ``/`` (``"Lithonia / 2BLT4-40L-LP840"``).  When that's
        # the case AND we don't have an explicit catalog column, split.
        if mfr and catalog is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, catalog = left, right

        wattage = _parse_wattage(watts_raw)
        lumens = _parse_lumens(lumens_raw)
        # Color temp may appear in the description / lamp / notes
        # field (``"2x4 LED RECESSED TROFFER 4000K"``).
        color_temp = (
            _parse_color_temp(lamp_raw)
            or _parse_color_temp(desc)
            or _parse_color_temp(notes_raw)
        )
        voltage = _parse_voltage_cell(voltage_raw)
        # Lamp technology and mounting may be inferable from the
        # description even when no dedicated column exists.
        lamp_type = _classify_lamp_type(lamp_raw, desc, notes_raw)
        mounting = _classify_mounting(mounting_raw, desc, notes_raw)
        dimmable = _detect_dimmable(desc, notes_raw, voltage_raw)
        emergency = _detect_emergency(desc, notes_raw)
        quantity = _parse_quantity(qty_raw)

        confidence = _fixture_confidence(
            tag=tag, has_description=bool(desc),
            has_manufacturer=bool(mfr), has_catalog=bool(catalog),
            has_wattage=wattage is not None, has_voltage=bool(voltage),
            has_mounting=bool(mounting),
        )

        records.append(LightingFixtureRecord(
            fixture_tag=tag,
            description=desc.strip(),
            manufacturer=(mfr.strip() if mfr else None),
            catalog_number=(catalog.strip() if catalog else None),
            wattage=wattage,
            lumens=lumens,
            color_temp_k=color_temp,
            voltage=voltage,
            lamp_type=lamp_type,
            mounting=mounting,
            dimmable=dimmable,
            emergency=emergency,
            quantity=quantity,
            notes=(notes_raw.strip() if notes_raw else None),
            confidence=confidence,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _fixture_confidence(*, tag: str, has_description: bool,
                          has_manufacturer: bool, has_catalog: bool,
                          has_wattage: bool, has_voltage: bool,
                          has_mounting: bool) -> float:
    """0.85 baseline; tick up to ~0.95 fully decorated, down to 0.65 partial.

    Tag alone (no description, no specs) lands at 0.65.  Every
    additional piece (description, manufacturer, catalog, wattage,
    voltage, mounting) ticks the row up so a fully-decorated fixture
    lands above the AUTO_APPROVE threshold (0.85).
    """
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_catalog,
        has_wattage, has_voltage, has_mounting,
    ]
    # Six possible decorations: cap the per-decoration bonus at
    # 0.05 each, max additive = 0.30 → ceiling 0.95.
    score += 0.05 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, fixtures: list[LightingFixtureRecord]) -> float:
    """Aggregate 0..1 confidence for the page-level result."""
    if not fixtures:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30  # at least one fixture extracted
    if any(f.wattage is not None for f in fixtures):
        score += 0.15
    if len(fixtures) >= 5:
        score += 0.15
    return min(score, 1.0)


def extract_lighting_schedule_from_page(page: "fitz.Page", page_index: int = 0,
                                          *, sheet_id: str | None = None
                                          ) -> LightingScheduleResult:
    """Extract every lighting-fixture schedule (if any) from a single page.

    Multi-table pages: every table whose header passes
    :func:`_looks_like_lighting_header` contributes its records to
    the aggregate result so a page with a fixture schedule + a
    controls/zones table (which won't pass the header heuristic)
    still produces the fixture rows cleanly.
    """
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _LIGHTING_SCHEDULE_KEYWORDS)

    all_records: list[LightingFixtureRecord] = []
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
        if not _looks_like_lighting_header(headers):
            continue
        data_rows = [
            [str(c).strip() if c is not None else "" for c in (r or [])]
            for r in extracted[1:]
            if r and any(c for c in r if c is not None and str(c).strip())
        ]
        records = _records_from_table(headers, data_rows, page_index)
        if not records:
            continue
        # Tag each record with the sheet ID + page for traceability.
        for r in records:
            r.source_sheet = sheet_id
            r.source_page = page_index
        all_records.extend(records)
        header_debug.append(" | ".join(headers))

    if not all_records and has_phrase:
        logger.debug(
            "lighting_schedule phrase fired on page %d but no fixtures parsed",
            page_index,
        )

    return LightingScheduleResult(
        pages=[page_index] if all_records else [],
        fixtures=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_lighting_schedule(pdf_path: Path, page_index: int,
                                *, sheet_id: str | None = None
                                ) -> LightingScheduleResult:
    """Run the lighting-fixture-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_lighting_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: LightingScheduleResult):
    """Return a :class:`core.schemas.LightingScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.LightingScheduleResult(
        pages=list(result.pages),
        fixtures=[
            S.LightingFixtureRecord(
                fixture_tag=f.fixture_tag,
                description=f.description,
                manufacturer=f.manufacturer,
                catalog_number=f.catalog_number,
                wattage=f.wattage,
                lumens=f.lumens,
                color_temp_k=f.color_temp_k,
                voltage=f.voltage,
                lamp_type=f.lamp_type,
                mounting=f.mounting,
                dimmable=f.dimmable,
                emergency=f.emergency,
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
