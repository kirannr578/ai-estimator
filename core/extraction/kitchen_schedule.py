"""Deterministic kitchen equipment schedule extraction (Phase T2.10).

Kitchen equipment schedules live on K-series sheets (``K1.0`` /
``K-EQ`` / ``K2.0``) and route to MasterFormat Division 11
(Equipment), section ``11 40 13`` Food Service Equipment.  Each
schedule typically carries:

1. **Item tag** — letter+digit identifier with a family prefix
   (``K-1`` generic / ``RA-1`` range / ``FRY-1`` fryer / ``OV-1``
   oven / ``REF-1`` refrigerator / ``FZ-1`` freezer / ``WI-1``
   walk-in / ``IM-1`` ice machine / ``DW-1`` dishwasher / ``HD-1``
   hood / ``EF-1`` exhaust fan / ``SK-1`` sink).
2. **Description** — free text describing the unit.
3. **Manufacturer / model** — sometimes joined by ``/``, sometimes
   two distinct columns.
4. **Size** — width × depth × height in inches, or BTU rating.
5. **Utilities** — gas / electric / water / drain flags; voltage
   when electric.  Drives the rough-in synthesis line.
6. **Optional QTY column** — when present flows through to a high-
   confidence synthesised count (0.90); when absent the synthesiser
   falls back to 0.55 → HAND_TAKEOFF.

Phase T2.10 is the SIXTH downstream consumer of the shared
``header_index_excluding`` helper promoted in Phase T3.6 (door /
panel / lighting / HVAC / plumbing are the prior five).  Header
collisions resolved by the two-pass picker:

* ``H`` / ``HP`` / ``HOOD`` / ``HEIGHT`` — bare ``H`` substring-
  collides with each.  Pin ``HEIGHT`` and ``HP`` first.
* ``W`` / ``WIDTH`` / ``WATER`` / ``WATTAGE`` — bare ``W``
  collides with all three; long forms pin first.
* ``D`` / ``DEPTH`` / ``DRAIN`` — same pattern.
* ``B`` / ``BTU`` — long form first.

Architectural pattern mirrors :mod:`core.extraction.plumbing_schedule`.
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
class KitchenEquipmentRecord:
    """One kitchen equipment record pulled off a K-series schedule."""

    tag: str
    item_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    width_in: float | None = None
    depth_in: float | None = None
    height_in: float | None = None
    btu_rating: int | None = None
    utility_gas: bool | None = None
    utility_electric: bool | None = None
    utility_water: bool | None = None
    utility_drain: bool | None = None
    voltage: str | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class KitchenScheduleResult:
    """Aggregate kitchen-equipment-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    equipment: list[KitchenEquipmentRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


_KITCHEN_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "KITCHEN EQUIPMENT SCHEDULE",
    "FOOD SERVICE EQUIPMENT",
    "KITCHEN SCHEDULE",
    "FOOD SERVICE SCHEDULE",
    "FOODSERVICE EQUIPMENT",
)


_KITCHEN_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "ITEM", "MARK", "TYPE", "NO",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "SIZE", "DIMENSIONS", "DIM",
    "BTU", "BTUH",
    "GAS", "ELEC", "ELECTRIC", "WATER", "DRAIN",
    "VOLTAGE", "VOLTS", "V",
    "UTILITIES", "UTIL",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
    "WIDTH", "DEPTH", "HEIGHT",
    "W", "D", "H",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_kitchen_header(headers: Iterable[str]) -> bool:
    """Three-signal header heuristic for kitchen equipment schedules.

    Requires:

    1. a tag column (``TAG`` / ``ITEM`` / ``MARK`` / ``NO``),
    2. at least one description / spec column (``DESCRIPTION`` /
       ``DESC`` / ``MANUFACTURER`` / ``MFG`` / ``MFR`` / ``MODEL``),
    3. at least one kitchen-specific spec column (``BTU`` / ``BTUH``
       / ``GAS`` / ``DRAIN`` / ``UTILITIES`` / ``UTIL``).

    Disqualifies headers carrying door / window / panel / lighting /
    HVAC / plumbing / lab / AV / security signals so a foreign
    schedule cannot be mis-claimed.
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
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "FRAME",
        # Panel
        "CIRCUIT", "CKT", "CIR", "BREAKER", "BKR", "AMPS", "AMP",
        # Lighting
        "LAMP", "LAMPS", "LUMENS", "LM",
        "WATTS", "WATTAGE", "BALLAST", "DRIVER",
        # HVAC
        "CFM", "MBH", "TONS",
        "REFRIG", "REFRIGERANT", "MOTOR", "PHASE",
        # Plumbing
        "GPF", "GPM", "FLOW", "VENT", "WASTE",
        # Lab
        "FUME", "VACUUM", "BENCHTOP", "EPOXY", "PHENOLIC",
        # AV
        "HDMI", "RESOLUTION", "DISPLAY", "PROJECTOR", "SPEAKER",
        # Security
        "POE", "WIEGAND", "CARDREADER", "MAGLOCK",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "ITEM", "MARK", "NO"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL",
    })
    has_spec = bool(words & {
        "BTU", "BTUH", "GAS", "DRAIN", "UTILITIES", "UTIL",
    })
    return has_tag and has_desc and has_spec


def detect_kitchen_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains a kitchen equipment schedule."""
    text = (page.get_text("text") or "").upper()
    has_phrase = any(kw in text for kw in _KITCHEN_SCHEDULE_KEYWORDS)
    try:
        tables = getattr(page.find_tables(), "tables", None) or []
    except Exception:  # pragma: no cover - PyMuPDF internal
        return has_phrase
    for table in tables:
        try:
            extracted = table.extract()
        except Exception:  # pragma: no cover - PyMuPDF internal
            continue
        if not extracted:
            continue
        headers = [str(h or "") for h in (extracted[0] or [])]
        if _looks_like_kitchen_header(headers):
            return True
    if has_phrase:
        # Phrase fired with no kitchen-shaped header AND at least one
        # other shape detected → reject (phrase coincidence).
        for table in tables:
            try:
                extracted = table.extract()
            except Exception:  # pragma: no cover
                continue
            if not extracted:
                continue
            headers = [str(h or "") for h in (extracted[0] or [])]
            words: set[str] = set()
            for h in headers:
                if h:
                    words.update(re.findall(r"[A-Za-z]+", h.upper()))
            if words & {"WATTS", "LUMENS", "LAMP", "CFM", "MBH",
                          "TONS", "CIRCUIT", "BREAKER", "HARDWARE",
                          "GPF", "GPM"}:
                return False
        return True
    return False


# ---------------------------------------------------------------------------
# Item-type detection from tag prefix
# ---------------------------------------------------------------------------


# Order matters: longer / more-specific prefixes BEFORE shorter ones.
_ITEM_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("RANGE", "RA"),                   "RANGE"),
    (("GRIDDLE", "GRD", "GR"),          "GRIDDLE"),
    (("FRYER", "FRY", "FR"),            "FRYER"),
    (("OVEN", "OV"),                    "OVEN"),
    (("REFRIGERATOR", "REF", "RF"),     "REFRIGERATOR"),
    (("FREEZER", "FRZ", "FZ"),          "FREEZER"),
    (("WALKIN", "WI", "WIC", "WIF"),    "WALK_IN"),
    (("ICE", "IM"),                     "ICE_MACHINE"),
    (("DISHWASHER", "DSH", "DW"),       "DISHWASHER"),
    (("MIXER", "MIX", "MX"),            "MIXER"),
    (("PREP", "PT", "PR"),              "PREP_TABLE"),
    (("HOOD", "HD", "EH"),              "HOOD"),
    (("EXHAUST", "EF"),                 "EXHAUST_FAN"),
    (("SINK", "SK"),                    "SINK"),
)


def _classify_item_type(tag: str, description: str | None = None) -> str:
    """Classify kitchen item from tag (``RANGE-1``) or fallback to description."""
    raw = (tag or "").strip().upper()
    if not raw:
        if description:
            return _classify_item_type(description)
        return "OTHER"
    head = re.split(r"[-_/\s]", raw, maxsplit=1)[0]
    for keywords, label in _ITEM_TYPE_PREFIXES:
        for kw in keywords:
            if head == kw:
                return label
    for keywords, label in _ITEM_TYPE_PREFIXES:
        for kw in keywords:
            if raw.startswith(kw) and (
                len(raw) == len(kw) or not raw[len(kw)].isalpha()
            ):
                return label
    if description:
        desc_upper = description.upper()
        desc_hints = (
            ("RANGE",            "RANGE"),
            ("GRIDDLE",          "GRIDDLE"),
            ("FRYER",            "FRYER"),
            ("OVEN",             "OVEN"),
            ("REFRIGERATOR",     "REFRIGERATOR"),
            ("REFRIGERATED",     "REFRIGERATOR"),
            ("FREEZER",          "FREEZER"),
            ("WALK-IN",          "WALK_IN"),
            ("WALK IN",          "WALK_IN"),
            ("ICE MACHINE",      "ICE_MACHINE"),
            ("ICE MAKER",        "ICE_MACHINE"),
            ("DISHWASHER",       "DISHWASHER"),
            ("DISH MACHINE",     "DISHWASHER"),
            ("MIXER",            "MIXER"),
            ("PREP TABLE",       "PREP_TABLE"),
            ("WORK TABLE",       "PREP_TABLE"),
            ("EXHAUST FAN",      "EXHAUST_FAN"),
            ("EXHAUST HOOD",     "HOOD"),
            ("HOOD",             "HOOD"),
            ("SINK",             "SINK"),
        )
        for kw, label in desc_hints:
            if kw in desc_upper:
                return label
    return "OTHER"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


_BTU_RE: re.Pattern[str] = re.compile(
    r"(\d{2,3}(?:[,\s]\d{3})?|\d{4,7})\s*(?:K?\s*BTU|BTU/?H|BTUH|MBH)?",
    re.IGNORECASE,
)


def _parse_btu(raw: str | None) -> int | None:
    """Parse a BTU rating cell.  Accepts ``45000``, ``45,000``, ``45K BTU``."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"^\s*([\d,]+)\s*(K?)\s*(?:BTU(?:/?H)?|BTUH|MBH)?\s*$",
                    text, re.IGNORECASE)
    if not m:
        return None
    try:
        value = int(m.group(1).replace(",", ""))
    except ValueError:
        return None
    if m.group(2).upper() == "K":
        value *= 1000
    return value


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


def _parse_inches(raw: str | None) -> float | None:
    """Parse a single inch dimension; tolerates ``36"`` / ``36`` / ``36 IN``."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(?:\"|IN(?:CHES)?)?\s*$",
                    text, re.IGNORECASE)
    if not m:
        return None
    try:
        return float(m.group(1))
    except ValueError:
        return None


_SIZE_TRIPLE_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:\"|IN)?\s*[Xx×]\s*"
    r"(\d+(?:\.\d+)?)\s*(?:\"|IN)?\s*"
    r"(?:[Xx×]\s*(\d+(?:\.\d+)?)\s*(?:\"|IN)?\s*)?"
)


def _parse_size_triple(raw: str | None) -> tuple[float | None, float | None,
                                                       float | None]:
    """Parse a ``W × D × H`` size cell; returns (width, depth, height) inches."""
    if raw is None:
        return None, None, None
    text = str(raw).strip()
    if not text:
        return None, None, None
    m = _SIZE_TRIPLE_RE.search(text)
    if not m:
        return None, None, None
    try:
        w = float(m.group(1))
        d = float(m.group(2))
        h = float(m.group(3)) if m.group(3) else None
    except ValueError:
        return None, None, None
    return w, d, h


_VOLTAGE_RE: re.Pattern[str] = re.compile(
    r"(\d{2,3})(?:\s*/\s*\d{1,3})?\s*V?\s*(?:/\s*([13])\s*P?H?)?",
    re.IGNORECASE,
)


def _parse_voltage(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _VOLTAGE_RE.search(upper)
    if not m:
        return None
    return upper


# ---------------------------------------------------------------------------
# Utility detection
# ---------------------------------------------------------------------------


def _flag_from_cell(raw: str | None) -> bool | None:
    """Interpret a utility cell as a tri-state flag (True / False / unknown)."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE", "NO", "N", "0"}:
        return False
    if upper in {"X", "Y", "YES", "✓", "*", "1"}:
        return True
    if any(c.isdigit() for c in text):
        # Numeric utility cell (e.g. "1/2\"" supply size) implies the
        # utility is present.
        return True
    if upper in {"GAS", "ELEC", "ELECTRIC", "WATER", "DRAIN", "STEAM"}:
        return True
    return None


_UTILITY_KEYWORDS: dict[str, tuple[str, ...]] = {
    "gas":      ("GAS", "NATGAS", "NG", "LPG", "PROPANE"),
    "electric": ("ELEC", "ELECTRIC", "POWER", "VAC"),
    "water":    ("WATER", "CW", "HW", "H2O", "DOMESTIC"),
    "drain":    ("DRAIN", "WASTE", "FD"),
}


def _detect_utilities_from_text(*texts: str | None) -> dict[str, bool | None]:
    """Scan free-text fields for utility keyword markers."""
    blob = " ".join(t for t in texts if t)
    if not blob:
        return {k: None for k in _UTILITY_KEYWORDS}
    upper = blob.upper()
    out: dict[str, bool | None] = {}
    for key, kws in _UTILITY_KEYWORDS.items():
        hit = any(re.search(rf"\b{re.escape(kw)}\b", upper) for kw in kws)
        out[key] = True if hit else None
    return out


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":          ("TAG", "ITEM", "MARK", "NO"),
    "type_col":     ("TYPE",),
    "desc_long":    ("DESCRIPTION", "DESC"),
    "desc_short":   ("D",),
    "mfr":          ("MANUFACTURER", "MFR", "MFG", "MAKE"),
    "model":        ("MODEL", "MODEL NO", "PART"),
    "size":         ("SIZE", "DIMENSIONS", "DIM"),
    "width_long":   ("WIDTH",),
    "width_short":  ("W",),
    "depth_long":   ("DEPTH",),
    "height_long":  ("HEIGHT",),
    "height_short": ("H",),
    "btu_long":     ("BTU", "BTUH", "MBH"),
    "btu_short":    ("B",),
    "gas":          ("GAS",),
    "electric":     ("ELEC", "ELECTRIC", "POWER"),
    "water":        ("WATER",),
    "drain":        ("DRAIN",),
    "voltage_long": ("VOLTAGE", "VOLTS"),
    "voltage_short": ("V",),
    "wattage_long": ("WATTAGE", "WATTS"),
    "qty_long":     ("QUANTITY", "QTY"),
    "qty_short":    ("Q",),
    "notes":        ("NOTES", "REMARKS", "COMMENTS"),
}


def _header_index(headers: list[str], candidates: tuple[str, ...]) -> int | None:
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


def _kitchen_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick kitchen-equipment column indices using the two-pass picker.

    Sixth downstream consumer of :func:`_header_index_excluding`.
    Pins long-form columns first (``DESCRIPTION``, ``WIDTH``,
    ``DEPTH``, ``HEIGHT``, ``BTU``, ``WATTAGE``, ``VOLTAGE``,
    ``QUANTITY``, ``NOTES``) so each multi-letter header claims its
    proper slot, then runs the short-form lookups (``D``, ``W``,
    ``H``, ``B``, ``Q``, ``V``) with EVERY long-form index in the
    exclusion set.  This is the kitchen-specific manifestation of
    the same pattern used by HVAC + plumbing — the collisions are
    just the kitchen letters.
    """
    tag_idx = _header_index(headers, _HEADERS["tag"])
    type_idx = _header_index_excluding(
        headers, _HEADERS["type_col"],
        exclude={i for i in (tag_idx,) if i is not None},
    )

    # ---- Pin LONG-FORM columns ----
    desc_long_idx = _header_index_excluding(
        headers, _HEADERS["desc_long"],
        exclude={i for i in (tag_idx, type_idx) if i is not None},
    )
    long_exclude: set[int] = {
        i for i in (tag_idx, type_idx, desc_long_idx) if i is not None
    }
    mfr_idx = _header_index_excluding(
        headers, _HEADERS["mfr"], exclude=set(long_exclude),
    )
    if mfr_idx is not None:
        long_exclude.add(mfr_idx)
    model_idx = _header_index_excluding(
        headers, _HEADERS["model"], exclude=set(long_exclude),
    )
    if model_idx is not None:
        long_exclude.add(model_idx)
    size_idx = _header_index_excluding(
        headers, _HEADERS["size"], exclude=set(long_exclude),
    )
    if size_idx is not None:
        long_exclude.add(size_idx)
    width_long_idx = _header_index_excluding(
        headers, _HEADERS["width_long"], exclude=set(long_exclude),
    )
    if width_long_idx is not None:
        long_exclude.add(width_long_idx)
    depth_long_idx = _header_index_excluding(
        headers, _HEADERS["depth_long"], exclude=set(long_exclude),
    )
    if depth_long_idx is not None:
        long_exclude.add(depth_long_idx)
    height_long_idx = _header_index_excluding(
        headers, _HEADERS["height_long"], exclude=set(long_exclude),
    )
    if height_long_idx is not None:
        long_exclude.add(height_long_idx)
    btu_long_idx = _header_index_excluding(
        headers, _HEADERS["btu_long"], exclude=set(long_exclude),
    )
    if btu_long_idx is not None:
        long_exclude.add(btu_long_idx)
    wattage_long_idx = _header_index_excluding(
        headers, _HEADERS["wattage_long"], exclude=set(long_exclude),
    )
    if wattage_long_idx is not None:
        long_exclude.add(wattage_long_idx)
    voltage_long_idx = _header_index_excluding(
        headers, _HEADERS["voltage_long"], exclude=set(long_exclude),
    )
    if voltage_long_idx is not None:
        long_exclude.add(voltage_long_idx)
    gas_idx = _header_index_excluding(
        headers, _HEADERS["gas"], exclude=set(long_exclude),
    )
    if gas_idx is not None:
        long_exclude.add(gas_idx)
    electric_idx = _header_index_excluding(
        headers, _HEADERS["electric"], exclude=set(long_exclude),
    )
    if electric_idx is not None:
        long_exclude.add(electric_idx)
    water_idx = _header_index_excluding(
        headers, _HEADERS["water"], exclude=set(long_exclude),
    )
    if water_idx is not None:
        long_exclude.add(water_idx)
    drain_idx = _header_index_excluding(
        headers, _HEADERS["drain"], exclude=set(long_exclude),
    )
    if drain_idx is not None:
        long_exclude.add(drain_idx)
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

    # ---- SHORT-FORM lookups with every long form excluded ----
    desc_short_idx = _header_index_excluding(
        headers, _HEADERS["desc_short"], exclude=set(long_exclude),
    )
    if desc_short_idx is not None:
        long_exclude.add(desc_short_idx)
    width_short_idx = _header_index_excluding(
        headers, _HEADERS["width_short"], exclude=set(long_exclude),
    )
    if width_short_idx is not None:
        long_exclude.add(width_short_idx)
    height_short_idx = _header_index_excluding(
        headers, _HEADERS["height_short"], exclude=set(long_exclude),
    )
    if height_short_idx is not None:
        long_exclude.add(height_short_idx)
    btu_short_idx = _header_index_excluding(
        headers, _HEADERS["btu_short"], exclude=set(long_exclude),
    )
    if btu_short_idx is not None:
        long_exclude.add(btu_short_idx)
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

    desc_idx = desc_long_idx if desc_long_idx is not None else desc_short_idx
    width_idx = width_long_idx if width_long_idx is not None else width_short_idx
    height_idx = height_long_idx if height_long_idx is not None else height_short_idx
    btu_idx = btu_long_idx if btu_long_idx is not None else btu_short_idx
    voltage_idx = voltage_long_idx if voltage_long_idx is not None else voltage_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":      tag_idx,
        "type":     type_idx,
        "desc":     desc_idx,
        "mfr":      mfr_idx,
        "model":    model_idx,
        "size":     size_idx,
        "width":    width_idx,
        "depth":    depth_long_idx,
        "height":   height_idx,
        "btu":      btu_idx,
        "wattage":  wattage_long_idx,
        "voltage":  voltage_idx,
        "gas":      gas_idx,
        "electric": electric_idx,
        "water":    water_idx,
        "drain":    drain_idx,
        "qty":      qty_idx,
        "notes":    notes_idx,
    }


_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[KitchenEquipmentRecord]:
    idx = _kitchen_indices(headers)
    records: list[KitchenEquipmentRecord] = []
    for row in data_rows:
        if not row:
            continue
        tag = _cell(row, idx["tag"])
        if not tag and idx["type"] is not None:
            tag = _cell(row, idx["type"])
        if not tag:
            continue
        tag = tag.strip().strip(".,:")
        if not tag:
            continue
        if not _TAG_RE.match(tag):
            stripped = re.sub(r"^(?:TAG|ITEM|MARK|NO)\s+", "", tag,
                                 flags=re.IGNORECASE)
            if _TAG_RE.match(stripped):
                tag = stripped
            else:
                continue

        desc = _cell(row, idx["desc"])
        mfr = _cell(row, idx["mfr"])
        model = _cell(row, idx["model"])
        size_raw = _cell(row, idx["size"])
        width_raw = _cell(row, idx["width"])
        depth_raw = _cell(row, idx["depth"])
        height_raw = _cell(row, idx["height"])
        btu_raw = _cell(row, idx["btu"])
        voltage_raw = _cell(row, idx["voltage"])
        gas_raw = _cell(row, idx["gas"])
        electric_raw = _cell(row, idx["electric"])
        water_raw = _cell(row, idx["water"])
        drain_raw = _cell(row, idx["drain"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        # Manufacturer / model split on '/' when only one column.
        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

        # Size triple from a single SIZE column when WxDxH not split.
        width_in = _parse_inches(width_raw)
        depth_in = _parse_inches(depth_raw)
        height_in = _parse_inches(height_raw)
        if size_raw and (width_in is None or depth_in is None):
            w, d, h = _parse_size_triple(size_raw)
            if width_in is None:
                width_in = w
            if depth_in is None:
                depth_in = d
            if height_in is None:
                height_in = h

        btu_rating = _parse_btu(btu_raw)
        voltage = _parse_voltage(voltage_raw)
        quantity = _parse_quantity(qty_raw)

        utility_gas = _flag_from_cell(gas_raw)
        utility_electric = _flag_from_cell(electric_raw)
        utility_water = _flag_from_cell(water_raw)
        utility_drain = _flag_from_cell(drain_raw)

        # Fallback: scan description / notes for utility markers when
        # no per-utility column existed.
        text_flags = _detect_utilities_from_text(desc, notes_raw)
        if utility_gas is None and text_flags["gas"]:
            utility_gas = True
        if utility_electric is None and text_flags["electric"]:
            utility_electric = True
        if utility_electric is None and voltage is not None:
            utility_electric = True
        if utility_water is None and text_flags["water"]:
            utility_water = True
        if utility_drain is None and text_flags["drain"]:
            utility_drain = True
        if utility_gas is None and btu_rating is not None:
            # A BTU rating on a kitchen unit reliably implies a gas feed.
            utility_gas = True

        item_type = _classify_item_type(tag, desc)
        confidence = _equipment_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_dimensions=any(v is not None for v in (
                width_in, depth_in, height_in, btu_rating,
            )),
            has_utilities=any(v is True for v in (
                utility_gas, utility_electric, utility_water, utility_drain,
            )),
        )

        records.append(KitchenEquipmentRecord(
            tag=tag,
            item_type=item_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            width_in=width_in,
            depth_in=depth_in,
            height_in=height_in,
            btu_rating=btu_rating,
            utility_gas=utility_gas,
            utility_electric=utility_electric,
            utility_water=utility_water,
            utility_drain=utility_drain,
            voltage=voltage,
            quantity=quantity,
            notes=notes_raw,
            confidence=confidence,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Confidence + entry points
# ---------------------------------------------------------------------------


def _equipment_confidence(*, tag: str, has_description: bool,
                            has_manufacturer: bool, has_model: bool,
                            has_dimensions: bool, has_utilities: bool) -> float:
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_model,
        has_dimensions, has_utilities,
    ]
    score += 0.06 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool,
              records: list[KitchenEquipmentRecord]) -> float:
    if not records:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30
    if any(r.btu_rating is not None or r.voltage is not None for r in records):
        score += 0.15
    if len(records) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_kitchen_schedule_from_page(
    page: "fitz.Page", page_index: int = 0,
    *, sheet_id: str | None = None,
) -> KitchenScheduleResult:
    """Extract every kitchen equipment schedule (if any) from a single page."""
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _KITCHEN_SCHEDULE_KEYWORDS)

    all_records: list[KitchenEquipmentRecord] = []
    header_debug: list[str] = []

    try:
        tables = getattr(page.find_tables(), "tables", None) or []
    except Exception as exc:  # pragma: no cover
        logger.debug("find_tables failed on page %d: %s", page_index, exc)
        tables = []

    for table in tables:
        try:
            extracted = table.extract()
        except Exception as exc:  # pragma: no cover
            logger.debug("table.extract failed on page %d: %s", page_index, exc)
            continue
        if not extracted or len(extracted) < 2:
            continue
        headers = [str(h).strip() if h is not None else "" for h in (extracted[0] or [])]
        if not _looks_like_kitchen_header(headers):
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

    return KitchenScheduleResult(
        pages=[page_index] if all_records else [],
        equipment=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_kitchen_schedule(pdf_path: Path, page_index: int,
                                *, sheet_id: str | None = None,
                                ) -> KitchenScheduleResult:
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_kitchen_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: KitchenScheduleResult):
    """Return a :class:`core.schemas.KitchenScheduleResult` Pydantic model."""
    from core import schemas as S

    return S.KitchenScheduleResult(
        pages=list(result.pages),
        equipment=[
            S.KitchenEquipmentRecord(
                tag=r.tag,
                item_type=r.item_type,
                description=r.description,
                manufacturer=r.manufacturer,
                model_number=r.model_number,
                width_in=r.width_in,
                depth_in=r.depth_in,
                height_in=r.height_in,
                btu_rating=r.btu_rating,
                utility_gas=r.utility_gas,
                utility_electric=r.utility_electric,
                utility_water=r.utility_water,
                utility_drain=r.utility_drain,
                voltage=r.voltage,
                quantity=r.quantity,
                notes=r.notes,
                confidence=r.confidence,
                source_sheet=r.source_sheet,
                source_page=r.source_page,
            )
            for r in result.equipment
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
