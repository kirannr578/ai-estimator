"""Deterministic HVAC equipment schedule extraction (Phase T2.8).

Mechanical / HVAC equipment schedules live on M-series / H-series /
MH-series sheets (``M1.0`` / ``M2.0`` / ``H1.0`` / ``MH-1``) and are
the highest-dollar single Division 23 artefact in BPC's calibration
cost distribution.  Each schedule typically carries:

1. **Equipment tag** — letter+digit identifier with a family prefix
   (``AHU-1`` / ``RTU-A`` / ``VAV-3-1`` / ``P-1`` / ``B-1`` / ``CH-1`` /
   ``F-1`` / ``SF-1`` / ``EF-2``).
2. **Description** — free text describing the equipment.
3. **Manufacturer + model number** — sometimes one cell, sometimes two.
4. **Capacity** — unit varies per equipment family (``CFM`` for
   air-handlers / fans; ``TONS`` for chillers / AHUs / RTUs; ``MBH``
   or ``BTUH`` for boilers; ``GPM`` for pumps).  The unit is detected
   from the column header rather than the value.
5. **Motor HP** — often a dedicated column.
6. **Voltage / phase** — ``208V/3φ`` / ``480V/3φ`` / ``120V/1φ``;
   preserved as the original string so the spec round-trips intact.
7. **Refrigerant** — ``R-410A`` / ``R-454B`` for DX equipment.
8. **Fuel type** — ``GAS`` / ``ELECTRIC`` / ``HW`` (hot water).
9. **Notes** — service location, controls, options.
10. **Optional QTY column** — less common, but when present flows
    through to a high-confidence synthesised count.

The synthesiser downstream (:mod:`core.extraction.takeoff_synthesis`)
fans each ``HVACEquipmentRecord`` out into 2-3 ``TakeoffItem``
families: the equipment itself (CSI per family — AHU → ``23 73 13``,
RTU → ``23 74 13``, VAV → ``23 36 00``, ...), a parametric MEP
rough-in line (CSI ``23 05 00``, LS), and optionally a disconnect +
flex line (CSI ``26 28 16``, EA) for motorized equipment with a
voltage feed.  VAVs (typically duct-fed, no motor) and boilers
(integrated disconnects) skip the disconnect row.

Architectural pattern mirrors :mod:`core.extraction.lighting_schedule`
/ :mod:`core.extraction.panel_schedule`: pure functions of a ``Path``
+ page index (or a ``fitz.Page``), internal dataclasses with a
``to_schema()`` bridge to the Pydantic models on :mod:`core.schemas`,
and a confidence rubric.  Runs **independently** of door / window /
finish / room / panel / lighting precedence — mechanical schedules
live on M-series sheets that those upstream detectors never claim,
same posture as panels + lighting.

Substring-collision note: HVAC schedules have four classes of
single-letter / short-name collision the longest-header-first picker
must resolve:

* ``TONS`` (or ``T``) the capacity-unit column.  Bare ``T`` is a
  substring of every other ``T``-containing token, so the long form
  must be pinned first.
* ``HP`` (or ``H``) the motor-horsepower column.
* ``VOLTAGE`` / ``VOLTS`` (or ``V``) the voltage column.
* ``QUANTITY`` / ``QTY`` (or ``Q``) the count column.

Phase T2.8 is the FOURTH downstream consumer of the shared
``header_index_excluding`` helper promoted in Phase T3.6 (Worker CC,
commit ``cb979e6``); doors/panel/lighting are the prior three.
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
class HVACEquipmentRecord:
    """One HVAC equipment record pulled off a mechanical schedule.

    ``confidence`` defaults to ``0.85`` — equipment rows are well-
    structured and the parser is deterministic, so a clean extraction
    is high confidence by construction.  Partial extractions (tag
    without capacity, or capacity without HP / voltage) tick the
    confidence down slightly via :func:`_equipment_confidence`.
    """

    equipment_tag: str
    equipment_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    capacity_value: float | None = None
    capacity_unit: str | None = None
    motor_hp: float | None = None
    voltage: str | None = None
    phase_count: int | None = None
    weight_lbs: float | None = None
    dimensions: str | None = None
    refrigerant: str | None = None
    fuel_type: str | None = None
    location: str | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class HVACScheduleResult:
    """Aggregate HVAC-equipment-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    equipment: list[HVACEquipmentRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


# Page-level phrase signals.  Any of these in the page text triggers
# the extractor; the absence of all of them does not exclude the page
# because an equipment-table header is sufficient on its own.
_HVAC_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "AHU SCHEDULE",
    "RTU SCHEDULE",
    "VAV SCHEDULE",
    "PUMP SCHEDULE",
    "BOILER SCHEDULE",
    "CHILLER SCHEDULE",
    "FAN SCHEDULE",
    "MECHANICAL EQUIPMENT SCHEDULE",
    "MECHANICAL SCHEDULE",
    "HVAC SCHEDULE",
    "MECHANICAL EQUIPMENT",
)


# Tokens that identify an HVAC equipment-table header row.  Requires
# a TAG column AND at least one description-side column AND at least
# one capacity/spec column — the same three-signal pattern used by
# door / window / finish / panel / lighting detection.
_HVAC_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "MARK", "TYPE",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "CAPACITY", "TONS", "T",
    "CFM", "MBH", "BTUH", "BTU", "GPM",
    "HP", "H", "MOTOR",
    "VOLTAGE", "VOLTS", "V",
    "PHASE", "PH",
    "WEIGHT", "LBS",
    "REFRIG", "REFRIGERANT",
    "FUEL",
    "QUANTITY", "QTY", "Q",
    "NOTES", "REMARKS",
    "LOCATION", "LOC",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_hvac_header(headers: Iterable[str]) -> bool:
    """Heuristic: does this row look like an HVAC equipment header row?

    Requires three signals together to avoid false-positives on
    neighbouring door / window / finish / panel / lighting
    schedules:

    1. a tag column (``TAG`` / ``MARK`` / ``TYPE``),
    2. at least one description / spec column (``DESCRIPTION`` /
       ``DESC`` / ``MANUFACTURER`` / ``MFG`` / ``MFR`` / ``MODEL``),
    3. at least one mechanical-spec column (``CAPACITY`` / ``TONS`` /
       ``CFM`` / ``MBH`` / ``GPM`` / ``BTUH`` / ``HP`` / ``MOTOR`` /
       ``VOLTAGE`` / ``REFRIG`` / ``FUEL``).

    Door / window / finish / panel / lighting-specific signals
    (``HARDWARE`` / ``GLAZING`` / ``CEILING`` / ``CIRCUIT`` /
    ``BREAKER`` / ``LAMP`` / ``LUMENS`` / ``WATTS`` / ``WATTAGE`` /
    ``MOUNTING`` / ``COLOR`` / ``FINISH``) actively disqualify the
    header even when the other classes match — this is the
    belt-and-braces discriminator on top of the
    door/window/finish/panel/lighting precedence rules at the
    dispatcher level.
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
        "SHGC", "UFACTOR", "UVALUE", "SILL", "FRAME",
        "CIRCUIT", "CKT", "CIR", "BREAKER", "BKR",
        "CEILING", "CLG", "BASE", "FLOOR",
        "LAMP", "LAMPS", "LUMENS", "LM",
        "WATTS", "WATTAGE", "MOUNTING", "MTG", "MOUNT",
        "COLOR", "COLOUR", "PAINT",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "MARK", "TYPE"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL",
    })
    has_spec = bool(words & {
        "CAPACITY", "TONS", "CFM", "MBH", "BTUH", "BTU", "GPM",
        "HP", "MOTOR", "VOLTAGE", "VOLTS", "PHASE", "PH",
        "REFRIG", "REFRIGERANT", "FUEL", "WEIGHT", "LBS",
    })
    return has_tag and has_desc and has_spec


def detect_hvac_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains an HVAC equipment schedule.

    Two cheap signals: any of :data:`_HVAC_SCHEDULE_KEYWORDS` in the
    page text, OR an HVAC-shaped equipment-table header on any
    detected table.  Either suffices.
    """
    text = (page.get_text("text") or "").upper()
    for kw in _HVAC_SCHEDULE_KEYWORDS:
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
        if _looks_like_hvac_header(headers):
            return True
    return False


# ---------------------------------------------------------------------------
# Equipment-type detection from tag prefix
# ---------------------------------------------------------------------------


# Order matters: more-specific / longer prefixes BEFORE shorter ones.
# ``SF-`` (supply fan) and ``EF-`` (exhaust fan) are checked before bare
# ``F-`` so a tag ``SF-1`` doesn't accidentally route through ``F-``.
# ``CHL-`` / ``CHR-`` / ``CH-`` all map to CHILLER; ``BLR-`` / ``B-``
# both map to BOILER.
_EQUIPMENT_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("AHU",), "AHU"),
    (("RTU",), "RTU"),
    (("VAV", "VAV-BOX", "VAVBOX"), "VAV"),
    (("PUMP",), "PUMP"),
    (("BLR", "BOILER"), "BOILER"),
    (("CHL", "CHR", "CHILLER", "CH"), "CHILLER"),
    (("SF", "EF", "RF", "FAN", "EXHAUST FAN", "SUPPLY FAN", "RETURN FAN"), "FAN"),
    (("P",), "PUMP"),
    (("B",), "BOILER"),
    (("F",), "FAN"),
)


def _classify_equipment_type(tag: str, description: str | None = None) -> str:
    """Classify equipment family from a tag (``AHU-1``) or fallback to desc.

    Single-letter prefix forms (``P-1`` / ``B-1`` / ``F-1``) are
    checked last so multi-letter prefixes (``AHU`` / ``RTU`` / ``VAV``
    / ``CHL``) win when both could match.
    """
    raw = (tag or "").strip().upper()
    if not raw:
        if description:
            return _classify_equipment_type(description)
        return "OTHER"
    # Split tag on common separators to pick the leading family prefix.
    head = re.split(r"[-_/\s]", raw, maxsplit=1)[0]
    for keywords, label in _EQUIPMENT_TYPE_PREFIXES:
        for kw in keywords:
            if head == kw:
                return label
    # Fallback: any prefix substring match (so ``AHU01`` without a
    # separator still classifies).
    for keywords, label in _EQUIPMENT_TYPE_PREFIXES:
        for kw in keywords:
            if raw.startswith(kw) and (len(raw) == len(kw) or not raw[len(kw)].isalpha()):
                return label
    # Description-based fallback only when tag was uninformative.
    if description:
        desc_upper = description.upper()
        for keywords, label in _EQUIPMENT_TYPE_PREFIXES:
            for kw in keywords:
                if len(kw) >= 2 and kw in desc_upper:
                    return label
    return "OTHER"


# ---------------------------------------------------------------------------
# Cell-level parsing helpers
# ---------------------------------------------------------------------------


# Numeric capacity: ``20`` / ``20.0`` / ``20 TONS`` / ``20T`` / ``2000``
# / ``2,000 CFM`` / ``150 MBH``.  Strips the unit suffix when present.
_CAPACITY_RE: re.Pattern[str] = re.compile(
    r"^\s*([\d,]+(?:\.\d+)?)\s*"
    r"(?:T(?:ONS?)?|CFM|MBH|BTU(?:H)?|GPM|HP)?\s*$",
    re.IGNORECASE,
)


def _parse_capacity_value(raw: str | None) -> float | None:
    """Parse a capacity cell into a numeric value.

    Strips commas, trailing units, and surrounding whitespace.  Falls
    back to a leading-number scrape for cells like ``"20 TONS (240
    MBH)"`` where the explicit unit suffix is interrupted by other
    text.  Returns ``None`` for empty / non-numeric cells.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = _CAPACITY_RE.match(text)
    if m:
        digits = m.group(1).replace(",", "")
        try:
            return float(digits)
        except ValueError:
            return None
    leading = re.match(r"\s*([\d,]+(?:\.\d+)?)", text)
    if leading:
        digits = leading.group(1).replace(",", "")
        try:
            return float(digits)
        except ValueError:
            return None
    return None


# Capacity-unit detection from a header string — header wins over value.
# ``T`` alone (no other letters) is treated as TONS; longer aliases are
# checked first to avoid the substring trap.
_CAPACITY_UNIT_BY_HEADER: tuple[tuple[tuple[str, ...], str], ...] = (
    (("TONS", "TON"), "TONS"),
    (("CFM",), "CFM"),
    (("MBH",), "MBH"),
    (("BTUH", "BTU"), "BTUH"),
    (("GPM",), "GPM"),
)


def _capacity_unit_from_header(header: str | None) -> str | None:
    """Infer capacity unit from the column header text."""
    if not header:
        return None
    norm = _normalize_header(header)
    if not norm:
        return None
    for keywords, label in _CAPACITY_UNIT_BY_HEADER:
        for kw in keywords:
            if kw in norm.split() or kw in norm:
                return label
    # Bare single-letter ``T`` header → TONS (whole-word match to keep
    # ``WEIGHT`` / ``BTUH`` from triggering).
    if "T" in norm.split():
        return "TONS"
    return None


_HP_RE: re.Pattern[str] = re.compile(
    r"^\s*([\d.]+)\s*(?:HP|hp)?\s*$",
)


def _parse_hp(raw: str | None) -> float | None:
    """Parse a motor-HP cell (``"1/2"`` / ``"0.5"`` / ``"1.5 HP"``)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    # Fractional HP (``"1/2"``).
    frac = re.match(r"^\s*(\d+)\s*/\s*(\d+)\s*(?:HP|hp)?\s*$", text)
    if frac:
        num = float(frac.group(1))
        den = float(frac.group(2))
        if den == 0:
            return None
        return round(num / den, 4)
    m = _HP_RE.match(text)
    if m:
        try:
            value = float(m.group(1))
        except ValueError:
            return None
        return value if value >= 0 else None
    leading = re.match(r"\s*([\d.]+)", text)
    if leading:
        try:
            value = float(leading.group(1))
        except ValueError:
            return None
        return value if value >= 0 else None
    return None


def _parse_voltage_cell(raw: str | None) -> tuple[str | None, int | None]:
    """Parse a voltage cell.  Returns ``(voltage_string, phase_count)``.

    Preserves the original cell text as the canonical voltage string so
    ``"208V/3φ"`` round-trips intact.  Phase count is extracted as a
    side-channel: ``3φ`` / ``3 PHASE`` / ``3PH`` / ``/3`` → ``3``;
    ``1φ`` / ``1 PHASE`` / ``1PH`` / ``/1`` → ``1``; otherwise
    ``None``.
    """
    if raw is None:
        return None, None
    text = str(raw).strip()
    if not text:
        return None, None
    upper = text.upper()
    phase: int | None = None
    if re.search(r"3\s*(?:PHASE|PH|Φ|/\s*3)\b", upper) or "3PH" in upper or "/3" in upper:
        phase = 3
    elif re.search(r"1\s*(?:PHASE|PH|Φ|/\s*1)\b", upper) or "1PH" in upper or "/1" in upper:
        phase = 1
    return text, phase


def _parse_weight(raw: str | None) -> float | None:
    """Parse a weight cell (``"800 LBS"`` / ``"800"`` / ``"1,200 lb"``)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"^\s*([\d,]+(?:\.\d+)?)\s*(?:LBS?|lb)?\s*$", text)
    if m:
        try:
            return float(m.group(1).replace(",", ""))
        except ValueError:
            return None
    leading = re.match(r"\s*([\d,]+(?:\.\d+)?)", text)
    if leading:
        try:
            return float(leading.group(1).replace(",", ""))
        except ValueError:
            return None
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


# Refrigerant: ``R-410A`` / ``R-32`` / ``R-454B`` / ``R134A``.
_REFRIGERANT_RE: re.Pattern[str] = re.compile(
    r"\bR\s*-?\s*(\d{2,4}[A-Z]?)\b",
    re.IGNORECASE,
)


def _detect_refrigerant(*texts: str | None) -> str | None:
    """Pull a refrigerant designation from any concatenated text."""
    blob = " ".join(t for t in texts if t)
    if not blob:
        return None
    m = _REFRIGERANT_RE.search(blob)
    if not m:
        return None
    digits = m.group(1).upper()
    return f"R-{digits}"


# Fuel-type keywords.  Order matters: longer / more-specific phrases
# before the bare ``GAS`` token so ``"HOT WATER"`` lands as ``HW`` and
# doesn't fall through to ``ELECTRIC``.
_FUEL_TYPE_KEYWORDS: tuple[tuple[tuple[str, ...], str], ...] = (
    (("HOT WATER", "HW"), "HW"),
    (("NATURAL GAS", "GAS", "NG", "LPG", "PROPANE"), "GAS"),
    (("ELECTRIC", "ELEC"), "ELECTRIC"),
)


def _detect_fuel_type(*texts: str | None) -> str | None:
    """Heuristic-classify fuel type from notes / description text."""
    blob = " ".join(t for t in texts if t).upper()
    if not blob:
        return None
    for keywords, label in _FUEL_TYPE_KEYWORDS:
        for kw in keywords:
            if re.search(rf"\b{re.escape(kw)}\b", blob):
                return label
    return None


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


# Header candidate lists.  The order of the inner tuples does NOT
# express priority — the picking logic always pins the LONGEST /
# most-specific candidate first to avoid substring collisions
# (``TONS`` before ``T``, ``HP`` before ``H``, ``VOLTAGE`` /
# ``VOLTS`` before ``V``, ``QUANTITY`` / ``QTY`` before ``Q``).
_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":         ("TAG", "MARK", "TYPE"),
    "desc":        ("DESCRIPTION", "DESC"),
    "mfr":         ("MANUFACTURER", "MFR", "MFG", "MAKER"),
    "model":       ("MODEL", "MODEL NO", "PART"),
    "capacity":    ("CAPACITY", "CFM", "MBH", "BTUH", "BTU", "GPM"),
    "tons_long":   ("TONS",),
    "tons_short":  ("T",),
    "hp_long":     ("HP",),
    "hp_short":    ("H",),
    "voltage_long": ("VOLTAGE", "VOLTS"),
    "voltage_short": ("V",),
    "phase":       ("PHASE", "PH"),
    "weight":      ("WEIGHT", "LBS"),
    "refrigerant": ("REFRIGERANT", "REFRIG"),
    "fuel":        ("FUEL",),
    "location":    ("LOCATION", "LOC"),
    "qty_long":    ("QUANTITY", "QTY"),
    "qty_short":   ("Q",),
    "notes":       ("NOTES", "REMARKS", "COMMENTS"),
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


def _equipment_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick the HVAC equipment-table column indices for ONE schedule.

    Resolves four classes of single-letter / short-name collision by
    a TWO-PASS strategy: pin every LONG-FORM column first (so each
    multi-letter header claims its proper slot), then run the
    SHORT-FORM lookups with EVERY long-form index in the exclusion
    set.  This is structurally tighter than the lighting / panel
    one-pair-at-a-time approach because HVAC has more cross-column
    substring traps — bare ``T`` substring-matches ``VOLTAGE``,
    bare ``H`` substring-matches ``PHASE``, etc.

    The four short-vs-long collisions:

    1. ``TONS`` before bare ``T`` (``T`` is a substring of every
       ``T``-containing word so the long form must win, AND the
       short form must also exclude every other long-form column).
    2. ``HP`` before bare ``H`` (``H`` substring-collides with
       ``PHASE`` / ``WEIGHT`` if not excluded).
    3. ``VOLTAGE`` / ``VOLTS`` before bare ``V``.
    4. ``QUANTITY`` / ``QTY`` before bare ``Q``.

    This is the FOURTH downstream consumer of
    :func:`_header_index_excluding` from :mod:`header_utils` — door /
    panel / lighting are the prior three.
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
    model_idx = _header_index_excluding(
        headers, _HEADERS["model"],
        exclude={i for i in (tag_idx, desc_idx, mfr_idx) if i is not None},
    )

    capacity_idx = _header_index_excluding(
        headers, _HEADERS["capacity"],
        exclude={i for i in (tag_idx, desc_idx, mfr_idx, model_idx)
                  if i is not None},
    )

    # ---- Pin all LONG-FORM short-collision columns first ----
    # Each lookup excludes the indices already claimed by earlier
    # long-form picks so a single header can never be double-counted.
    long_exclude: set[int] = {
        i for i in (tag_idx, desc_idx, mfr_idx, model_idx, capacity_idx)
        if i is not None
    }
    tons_long_idx = _header_index_excluding(
        headers, _HEADERS["tons_long"], exclude=set(long_exclude),
    )
    if tons_long_idx is not None:
        long_exclude.add(tons_long_idx)
    hp_long_idx = _header_index_excluding(
        headers, _HEADERS["hp_long"], exclude=set(long_exclude),
    )
    if hp_long_idx is not None:
        long_exclude.add(hp_long_idx)
    voltage_long_idx = _header_index_excluding(
        headers, _HEADERS["voltage_long"], exclude=set(long_exclude),
    )
    if voltage_long_idx is not None:
        long_exclude.add(voltage_long_idx)
    phase_idx = _header_index_excluding(
        headers, _HEADERS["phase"], exclude=set(long_exclude),
    )
    if phase_idx is not None:
        long_exclude.add(phase_idx)
    weight_idx = _header_index_excluding(
        headers, _HEADERS["weight"], exclude=set(long_exclude),
    )
    if weight_idx is not None:
        long_exclude.add(weight_idx)
    refrig_idx = _header_index_excluding(
        headers, _HEADERS["refrigerant"], exclude=set(long_exclude),
    )
    if refrig_idx is not None:
        long_exclude.add(refrig_idx)
    fuel_idx = _header_index_excluding(
        headers, _HEADERS["fuel"], exclude=set(long_exclude),
    )
    if fuel_idx is not None:
        long_exclude.add(fuel_idx)
    location_idx = _header_index_excluding(
        headers, _HEADERS["location"], exclude=set(long_exclude),
    )
    if location_idx is not None:
        long_exclude.add(location_idx)
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

    # ---- Pin every SHORT-FORM column with ALL long-forms excluded ----
    # ``long_exclude`` now carries every multi-letter column index so
    # the bare ``T`` / ``H`` / ``V`` / ``Q`` matchers can't steal a
    # ``VOLTAGE`` / ``PHASE`` / ``WEIGHT`` column via substring match.
    tons_short_idx = _header_index_excluding(
        headers, _HEADERS["tons_short"], exclude=set(long_exclude),
    )
    if tons_short_idx is not None:
        long_exclude.add(tons_short_idx)
    hp_short_idx = _header_index_excluding(
        headers, _HEADERS["hp_short"], exclude=set(long_exclude),
    )
    if hp_short_idx is not None:
        long_exclude.add(hp_short_idx)
    voltage_short_idx = _header_index_excluding(
        headers, _HEADERS["voltage_short"], exclude=set(long_exclude),
    )
    if voltage_short_idx is not None:
        long_exclude.add(voltage_short_idx)
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"], exclude=set(long_exclude),
    )
    if qty_short_idx is not None:
        long_exclude.add(qty_short_idx)

    # Resolve final indices: long-form wins when both are present;
    # short-form supplies the value when no long-form column exists.
    tons_idx = tons_long_idx if tons_long_idx is not None else tons_short_idx
    hp_idx = hp_long_idx if hp_long_idx is not None else hp_short_idx
    voltage_idx = voltage_long_idx if voltage_long_idx is not None else voltage_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":         tag_idx,
        "desc":        desc_idx,
        "mfr":         mfr_idx,
        "model":       model_idx,
        "capacity":    capacity_idx,
        "tons":        tons_idx,
        "hp":          hp_idx,
        "voltage":     voltage_idx,
        "phase":       phase_idx,
        "weight":      weight_idx,
        "refrigerant": refrig_idx,
        "fuel":        fuel_idx,
        "location":    location_idx,
        "qty":         qty_idx,
        "notes":       notes_idx,
    }


# Equipment-tag pattern.  Accepts a letter prefix (1-6 chars) optionally
# followed by digits / dashes: ``AHU-1``, ``RTU-A``, ``VAV-3-1``,
# ``P-1``, ``B-1``, ``CH-1``, ``F-1``, ``SF-1``, ``EF-2``.
_EQUIPMENT_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[HVACEquipmentRecord]:
    """Convert one equipment table's rows to ``HVACEquipmentRecord`` instances."""
    idx = _equipment_indices(headers)
    # Determine the capacity unit at the table level — the header
    # wins.  Try the dedicated capacity column first, then fall back
    # to the TONS-specific column when present.
    capacity_header_idx = idx["capacity"] if idx["capacity"] is not None else idx["tons"]
    capacity_header = (
        headers[capacity_header_idx] if capacity_header_idx is not None else None
    )
    capacity_unit = _capacity_unit_from_header(capacity_header)
    # When the TONS column is what supplied the index, force unit=TONS
    # regardless of the header text (it's a TONS column by definition).
    if idx["tons"] is not None and capacity_unit is None:
        capacity_unit = "TONS"

    records: list[HVACEquipmentRecord] = []
    for row in data_rows:
        if not row:
            continue
        tag = _cell(row, idx["tag"])
        if not tag:
            continue
        tag = tag.strip().strip(".,:")
        if not tag:
            continue
        if not _EQUIPMENT_TAG_RE.match(tag):
            stripped = re.sub(r"^(?:TAG|MARK|TYPE)\s+", "", tag, flags=re.IGNORECASE)
            if _EQUIPMENT_TAG_RE.match(stripped):
                tag = stripped
            else:
                continue

        desc = _cell(row, idx["desc"])
        mfr = _cell(row, idx["mfr"])
        model = _cell(row, idx["model"])
        capacity_raw = _cell(row, idx["capacity"])
        tons_raw = _cell(row, idx["tons"])
        hp_raw = _cell(row, idx["hp"])
        voltage_raw = _cell(row, idx["voltage"])
        phase_raw = _cell(row, idx["phase"])
        weight_raw = _cell(row, idx["weight"])
        refrig_raw = _cell(row, idx["refrigerant"])
        fuel_raw = _cell(row, idx["fuel"])
        location_raw = _cell(row, idx["location"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        # Manufacturer / model number may live in the same cell joined
        # by ``/`` (``"Carrier / 50TC-A05"``).
        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

        # Pick the capacity value: TONS column wins (when present)
        # over the generic CAPACITY column; otherwise CAPACITY.
        capacity_value = _parse_capacity_value(tons_raw) or _parse_capacity_value(capacity_raw)
        motor_hp = _parse_hp(hp_raw)
        voltage, voltage_phase = _parse_voltage_cell(voltage_raw)
        # Dedicated PHASE column wins over the side-channel parse.
        phase_count: int | None = None
        if phase_raw:
            m = re.search(r"\b([13])\b", phase_raw)
            if m:
                phase_count = int(m.group(1))
        if phase_count is None:
            phase_count = voltage_phase
        weight_lbs = _parse_weight(weight_raw)
        refrigerant = (
            _detect_refrigerant(refrig_raw)
            or _detect_refrigerant(desc)
            or _detect_refrigerant(notes_raw)
        )
        fuel_type = (
            _detect_fuel_type(fuel_raw)
            or _detect_fuel_type(desc)
            or _detect_fuel_type(notes_raw)
        )
        quantity = _parse_quantity(qty_raw)
        equipment_type = _classify_equipment_type(tag, desc)

        confidence = _equipment_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_capacity=capacity_value is not None,
            has_hp=motor_hp is not None,
            has_voltage=bool(voltage),
        )

        records.append(HVACEquipmentRecord(
            equipment_tag=tag,
            equipment_type=equipment_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            capacity_value=capacity_value,
            capacity_unit=capacity_unit if capacity_value is not None else None,
            motor_hp=motor_hp,
            voltage=voltage,
            phase_count=phase_count,
            weight_lbs=weight_lbs,
            dimensions=None,
            refrigerant=refrigerant,
            fuel_type=fuel_type,
            location=location_raw,
            quantity=quantity,
            notes=notes_raw,
            confidence=confidence,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Confidence + public entry points
# ---------------------------------------------------------------------------


def _equipment_confidence(*, tag: str, has_description: bool,
                            has_manufacturer: bool, has_model: bool,
                            has_capacity: bool, has_hp: bool,
                            has_voltage: bool) -> float:
    """0.85 baseline; tick up to ~0.95 fully decorated, down to 0.65 partial.

    Tag alone (no description, no specs) lands at 0.65.  Every
    additional piece (description, manufacturer, model, capacity,
    motor HP, voltage) ticks the row up so a fully-decorated equipment
    row lands above the AUTO_APPROVE threshold (0.85).
    """
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_model,
        has_capacity, has_hp, has_voltage,
    ]
    score += 0.05 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, equipment: list[HVACEquipmentRecord]) -> float:
    """Aggregate 0..1 confidence for the page-level result."""
    if not equipment:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30  # at least one equipment extracted
    if any(e.capacity_value is not None for e in equipment):
        score += 0.15
    if len(equipment) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_hvac_schedule_from_page(page: "fitz.Page", page_index: int = 0,
                                      *, sheet_id: str | None = None
                                      ) -> HVACScheduleResult:
    """Extract every HVAC equipment schedule (if any) from a single page.

    Multi-table pages: every table whose header passes
    :func:`_looks_like_hvac_header` contributes its records to the
    aggregate result so a page with separate AHU / RTU / VAV tables
    produces records from all three.
    """
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _HVAC_SCHEDULE_KEYWORDS)

    all_records: list[HVACEquipmentRecord] = []
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
        if not _looks_like_hvac_header(headers):
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
            "hvac_schedule phrase fired on page %d but no equipment parsed",
            page_index,
        )

    return HVACScheduleResult(
        pages=[page_index] if all_records else [],
        equipment=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_hvac_schedule(pdf_path: Path, page_index: int,
                            *, sheet_id: str | None = None
                            ) -> HVACScheduleResult:
    """Run the HVAC-equipment-schedule pre-pass on a single page of a PDF."""
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_hvac_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: HVACScheduleResult):
    """Return a :class:`core.schemas.HVACScheduleResult` Pydantic model."""
    from core import schemas as S  # lazy — avoids a circular import

    return S.HVACScheduleResult(
        pages=list(result.pages),
        equipment=[
            S.HVACEquipmentRecord(
                equipment_tag=e.equipment_tag,
                equipment_type=e.equipment_type,
                description=e.description,
                manufacturer=e.manufacturer,
                model_number=e.model_number,
                capacity_value=e.capacity_value,
                capacity_unit=e.capacity_unit,
                motor_hp=e.motor_hp,
                voltage=e.voltage,
                phase_count=e.phase_count,
                weight_lbs=e.weight_lbs,
                dimensions=e.dimensions,
                refrigerant=e.refrigerant,
                fuel_type=e.fuel_type,
                location=e.location,
                quantity=e.quantity,
                notes=e.notes,
                confidence=e.confidence,
                source_sheet=e.source_sheet,
                source_page=e.source_page,
            )
            for e in result.equipment
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
