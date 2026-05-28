"""Deterministic security / access-control schedule extraction (Phase T2.11).

Security and access-control schedules live on S-series security
sheets (``S1.0`` / ``S-SEC``) or T-series telecom sheets and route
to MasterFormat **Division 28** (Electronic Safety & Security):

* ``28 13`` Access Control (card readers, keypads, REX, maglocks)
* ``28 16`` Intrusion Detection (motion sensors, door contacts)
* ``28 23`` Video Surveillance (cameras)

Each schedule typically carries:

1. **Device tag** — letter+digit identifier with a family prefix
   (``DR-1`` / ``RDR-1`` / ``CR-1`` card reader, ``CAM-1`` security-
   context camera, ``MS-1`` / ``MOT-1`` / ``PIR-1`` motion sensor,
   ``DC-1`` / ``DOOR-1`` door contact, ``KP-1`` keypad, ``RTE-1``
   request-to-exit, ``ML-1`` / ``MAG-1`` maglock).
2. **Type** — free text describing the device class.
3. **Manufacturer / model** — sometimes joined by ``/``, sometimes
   two distinct columns.
4. **Mounting** — ``WALL`` / ``CEILING`` / ``DOOR_FRAME``.
5. **Power** — ``PoE`` / ``12VDC`` / ``24VDC`` / ``Wiegand-power``.
6. **Connection** — ``Cat6`` / ``RS-485`` / ``Wiegand``.
7. **Optional QTY column** — drives a high-confidence synthesised
   count (``0.90``); when absent the synthesiser falls back to
   ``0.55`` → HAND_TAKEOFF.

Phase T2.11 is the **seventh** downstream consumer of the shared
``header_index_excluding`` helper (door / panel / lighting / HVAC /
plumbing / kitchen+lab / AV prior).  Header collisions resolved by
the two-pass picker:

* ``D`` / ``DOOR`` / ``DEVICE`` / ``DESCRIPTION``
* ``C`` / ``CAMERA`` / ``CARD`` / ``CONTACT`` / ``COM`` / ``CABLE``
  / ``CONNECTION``
* ``M`` / ``MOTION`` / ``MODEL`` / ``MOUNTING`` / ``MARK``
* ``R`` / ``READER``
* ``P`` / ``POWER``

**Cross-talk guards:**

* **CAM- AV-vs-Security collision** — both AV and security
  schedules use ``CAM-N`` tags.  Disambiguation is at the SCHEDULE
  level (this detector requires a security keyword phrase OR a
  security-shaped header that the AV detector cannot satisfy) AND
  at the DESCRIPTION level (a ``CAM-N`` row whose description
  carries ``CONFERENCE`` / ``LECTURE`` / ``WEBCAM`` is REJECTED to
  ``OTHER`` so the AV extractor can claim it).
* **Door hardware schedule** — Phase T1 owns architectural door
  hardware (Division 8).  This detector rejects pages whose
  header carries ``HARDWARE`` / ``HDW`` keywords without an
  accompanying ``SECURITY`` / ``ACCESS`` / ``CARD`` / ``READER``
  context.  The ``DOOR HARDWARE SCHEDULE`` keyword in the brief
  is intentionally guarded to require security context — see
  :func:`detect_security_schedule_page`.

Architectural pattern mirrors :mod:`core.extraction.av_schedule`.
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
class SecurityDeviceRecord:
    """One security / access-control device record."""

    tag: str
    item_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    mounting: str | None = None
    power: str | None = None
    connection: str | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class SecurityScheduleResult:
    """Aggregate security-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    devices: list[SecurityDeviceRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


_SECURITY_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "SECURITY SCHEDULE",
    "ACCESS CONTROL SCHEDULE",
    "SECURITY DEVICE SCHEDULE",
    "CCTV SCHEDULE",
    "VIDEO SURVEILLANCE SCHEDULE",
    "CARD READER SCHEDULE",
    "DOOR HARDWARE SCHEDULE",
)


# Required context tokens (any one) to ACCEPT a ``DOOR HARDWARE
# SCHEDULE`` phrase as security scope; without one of these the
# phrase is treated as a Phase T1 architectural door hardware
# schedule and rejected.
_SECURITY_CONTEXT_TOKENS: tuple[str, ...] = (
    "SECURITY", "ACCESS", "CARD", "READER", "ELECTRIFIED",
    "MAGLOCK", "ELECTRIC STRIKE", "REX", "REQUEST TO EXIT",
    "CCTV", "SURVEILLANCE", "WIEGAND",
)


_SECURITY_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "MARK", "DEVICE", "TYPE",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "MOUNTING", "MTG", "M",
    "POWER", "P",
    "CONNECTION", "C", "CABLE",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
    "READER", "R", "DOOR", "D", "CAMERA",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_security_header(headers: Iterable[str]) -> bool:
    """Three-signal header heuristic for security / access-control schedules.

    Requires:

    1. a tag column (``TAG`` / ``MARK`` / ``DEVICE``),
    2. at least one description / spec column,
    3. at least one security-specific spec column (``READER`` /
       ``CAMERA`` / ``MAGLOCK`` / ``WIEGAND`` / ``CARD`` / ``MOTION``
       / ``CONTACT`` / ``CONNECTION`` / ``POE`` / ``CCTV``).

    Disqualifies headers carrying foreign-schedule signals so a
    door / window / panel / lighting / HVAC / plumbing / kitchen /
    lab / AV schedule cannot be mis-claimed.

    **Door-hardware-schedule guard** — A pure architectural door
    hardware schedule (Phase T1 territory) typically has ``MARK``,
    ``HARDWARE`` (or ``HDW``), and ``SET`` columns and no security
    spec columns.  The ``HARDWARE`` disqualifier below catches
    those; ``HDW`` is also caught.
    """
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    disqualifiers = {
        # Door hardware schedule (Phase T1)
        "HARDWARE", "HDW", "GLAZING", "OPERATION", "FRAME",
        "RATING", "LATCH", "STRIKE", "CLOSER",
        # Panel
        "CIRCUIT", "CKT", "CIR", "BREAKER", "BKR", "AMPS", "AMP",
        # Lighting
        "LAMP", "LAMPS", "LUMENS", "LM", "BALLAST", "DRIVER",
        "WATTS", "WATTAGE",
        # HVAC
        "CFM", "MBH", "TONS", "BTU", "BTUH",
        "REFRIG", "REFRIGERANT",
        # Plumbing
        "GPF", "GPM", "FLOW", "VENT", "WASTE",
        # Kitchen
        "GAS", "DRAIN", "UTILITIES", "UTIL",
        # Lab
        "FUME", "VACUUM", "BENCHTOP", "EPOXY", "PHENOLIC",
        # AV — DO NOT claim AV schedules
        "HDMI", "RESOLUTION", "PROJECTOR", "DISPLAY", "SPEAKER",
        "MICROPHONE",
    }
    if words & disqualifiers:
        # However, ``HARDWARE`` is permissible IF security context
        # is also present on the header — e.g. a combined
        # ``ELECTRIFIED HARDWARE`` schedule.  Check that the
        # offending word is HARDWARE/HDW and at least one security
        # token is present elsewhere in the headers.
        if (words & disqualifiers) <= {"HARDWARE", "HDW"} and (
            words & {"SECURITY", "ACCESS", "CARD", "READER",
                     "WIEGAND", "MAGLOCK", "CCTV", "ELECTRIFIED"}
        ):
            pass  # fall through to the positive checks
        else:
            return False
    has_tag = bool(words & {"TAG", "MARK", "DEVICE"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL", "TYPE",
    })
    has_spec = bool(words & {
        "READER", "CAMERA", "MAGLOCK", "WIEGAND", "CARD", "MOTION",
        "CONTACT", "CONNECTION", "POE", "CCTV", "SURVEILLANCE",
        "ACCESS", "SECURITY",
    })
    return has_tag and has_desc and has_spec


def detect_security_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains a security schedule.

    **Door-hardware guard**: the ``DOOR HARDWARE SCHEDULE`` phrase
    is accepted ONLY when the page text also contains at least one
    security-context token (``SECURITY`` / ``ACCESS`` / ``CARD`` /
    ``READER`` / ``ELECTRIFIED`` / ...).  Without a context token,
    a ``DOOR HARDWARE SCHEDULE`` phrase belongs to Phase T1 and
    this detector returns False.
    """
    text = (page.get_text("text") or "").upper()
    has_phrase = False
    for kw in _SECURITY_SCHEDULE_KEYWORDS:
        if kw not in text:
            continue
        if kw == "DOOR HARDWARE SCHEDULE":
            # Only accept when security context is present.
            if any(tok in text for tok in _SECURITY_CONTEXT_TOKENS):
                has_phrase = True
                break
            # Otherwise this is a Phase T1 schedule, keep looking.
            continue
        has_phrase = True
        break
    try:
        tables = getattr(page.find_tables(), "tables", None) or []
    except Exception:  # pragma: no cover
        return has_phrase
    for table in tables:
        try:
            extracted = table.extract()
        except Exception:  # pragma: no cover
            continue
        if not extracted:
            continue
        headers = [str(h or "") for h in (extracted[0] or [])]
        if _looks_like_security_header(headers):
            return True
    if has_phrase:
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
            if words & {"WATTS", "LUMENS", "CFM", "MBH", "TONS",
                          "CIRCUIT", "BREAKER", "GPF", "GPM",
                          "FUME", "PROJECTOR", "HDMI"}:
                return False
        return True
    return False


# ---------------------------------------------------------------------------
# Item-type detection from tag prefix
# ---------------------------------------------------------------------------
#
# CAM- AV-vs-Security disambiguation: the security classifier
# accepts CAM- ONLY when the parent schedule is security-shaped
# (this module's detection has already run) AND the description
# does not include obvious AV / conferencing keywords.  When the
# description carries ``CONFERENCE`` / ``LECTURE`` / ``WEBCAM`` /
# ``HUDDLE``, the classifier rejects the row to ``OTHER`` so it
# stays out of the security CAMERA bucket; the AV extractor will
# pick it up on its own pass.

_ITEM_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("READER", "RDR", "DR", "CR"),       "CARD_READER"),
    (("CAMERA", "CAM"),                    "CAMERA"),
    (("MOTION", "MOT", "PIR", "MS"),       "MOTION_SENSOR"),
    (("DOOR", "DC"),                        "DOOR_CONTACT"),
    (("KEYPAD", "KP"),                      "KEYPAD"),
    (("RTE", "REX"),                        "REQUEST_TO_EXIT"),
    (("MAGLOCK", "MAG", "ML"),              "MAGLOCK"),
)


# Description keywords that REJECT a CAM- row from the security
# CAMERA bucket because they clearly belong to AV.
_SECURITY_CAM_AV_KEYWORDS: tuple[str, ...] = (
    "CONFERENCE", "LECTURE", "WEBCAM", "HUDDLE",
    "VIDEO CONFERENCING", "CAPTURE", "TELEPRESENCE",
)


def _classify_item_type(tag: str, description: str | None = None) -> str:
    """Classify security device from tag prefix or description fallback.

    Special handling for ``CAM-`` rows: when the description carries
    an AV / conferencing keyword, the row is REJECTED to ``OTHER``
    so the security synthesis doesn't claim an AV camera.
    """
    raw = (tag or "").strip().upper()
    desc_upper = (description or "").upper()
    if not raw:
        if description:
            return _classify_item_type(description)
        return "OTHER"

    head = re.split(r"[-_/\s]", raw, maxsplit=1)[0]

    # CAM- cross-domain guard.
    if head in {"CAM", "CAMERA"}:
        if any(kw in desc_upper for kw in _SECURITY_CAM_AV_KEYWORDS):
            return "OTHER"

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
        if any(kw in desc_upper for kw in _SECURITY_CAM_AV_KEYWORDS):
            return "OTHER"
        desc_hints = (
            ("CARD READER",        "CARD_READER"),
            ("PROX READER",        "CARD_READER"),
            ("PROXIMITY READER",   "CARD_READER"),
            ("PTZ CAMERA",         "CAMERA"),
            ("DOME CAMERA",        "CAMERA"),
            ("FIXED CAMERA",       "CAMERA"),
            ("SURVEILLANCE",       "CAMERA"),
            ("CCTV",               "CAMERA"),
            ("MOTION SENSOR",      "MOTION_SENSOR"),
            ("MOTION DETECTOR",    "MOTION_SENSOR"),
            ("PIR SENSOR",         "MOTION_SENSOR"),
            ("DOOR CONTACT",       "DOOR_CONTACT"),
            ("DOOR POSITION",      "DOOR_CONTACT"),
            ("KEYPAD",             "KEYPAD"),
            ("REQUEST TO EXIT",    "REQUEST_TO_EXIT"),
            ("REQUEST-TO-EXIT",    "REQUEST_TO_EXIT"),
            ("MAGNETIC LOCK",      "MAGLOCK"),
            ("MAGLOCK",            "MAGLOCK"),
            ("ELECTROMAGNETIC LOCK", "MAGLOCK"),
        )
        for kw, label in desc_hints:
            if kw in desc_upper:
                return label
    return "OTHER"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


def _parse_quantity(raw: str | None) -> int | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    m = re.match(r"^\s*(\d+)\s*(?:EA)?\s*$", text, re.IGNORECASE)
    if not m:
        return None
    return int(m.group(1))


_POWER_RE: re.Pattern[str] = re.compile(
    r"(?P<val>PoE\+?|120\s*V(?:AC)?|240\s*V(?:AC)?|"
    r"12\s*VDC|24\s*VDC|48\s*V|WIEGAND[-\s]?POWER)",
    re.IGNORECASE,
)


def _parse_power(raw: str | None) -> str | None:
    """Parse a power-format cell.  Returns the normalised token or None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _POWER_RE.search(upper)
    if m:
        token = m.group("val").upper()
        token = re.sub(r"\s+", "", token)
        return token
    return None


_CONNECTION_RE: re.Pattern[str] = re.compile(
    r"(?P<val>CAT\s*[56][AE]?|RS[-\s]?485|WIEGAND|"
    r"CAT\s*6|FIBER|COAX)",
    re.IGNORECASE,
)


def _parse_connection(raw: str | None) -> str | None:
    """Parse a connection-type cell."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _CONNECTION_RE.search(upper)
    if m:
        token = m.group("val").upper()
        token = re.sub(r"\s+", "", token)
        # Normalise CAT5/6.
        if token.startswith("CAT"):
            return token
        if token.startswith("RS"):
            return "RS-485"
        return token
    return None


def _parse_mounting(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    for token in ("WALL", "CEILING", "DOOR FRAME", "DOORFRAME",
                  "FRAME", "FLOOR", "PENDANT", "SURFACE", "RECESSED"):
        if token in upper:
            return token.replace(" ", "_")
    return upper


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":             ("TAG", "MARK", "DEVICE", "NO"),
    "type_col":        ("TYPE",),
    "desc_long":       ("DESCRIPTION", "DESC"),
    "desc_short":      ("D",),
    "mfr":             ("MANUFACTURER", "MFR", "MFG", "MAKE"),
    "model":           ("MODEL", "MODEL NO", "PART"),
    "mounting_long":   ("MOUNTING", "MTG"),
    "mounting_short":  ("M",),
    "power_long":      ("POWER",),
    "power_short":     ("P",),
    "connection_long": ("CONNECTION", "CABLE"),
    "connection_short": ("C",),
    "qty_long":        ("QUANTITY", "QTY"),
    "qty_short":       ("Q",),
    "notes":           ("NOTES", "REMARKS", "COMMENTS"),
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


def _security_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick security-device column indices using the two-pass picker.

    Seventh downstream consumer of :func:`_header_index_excluding`.
    Pins long-form columns first (``DESCRIPTION``, ``MOUNTING``,
    ``POWER``, ``CONNECTION``, ``QUANTITY``, ``NOTES``) so each
    multi-letter header claims its proper slot, then runs the
    short-form lookups (``D``, ``M``, ``P``, ``C``, ``Q``) with
    EVERY long-form index in the exclusion set.  This is the
    security-specific manifestation of the same pattern used by
    kitchen / lab / AV — the collisions are just the security
    letters.
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
    mounting_long_idx = _header_index_excluding(
        headers, _HEADERS["mounting_long"], exclude=set(long_exclude),
    )
    if mounting_long_idx is not None:
        long_exclude.add(mounting_long_idx)
    power_long_idx = _header_index_excluding(
        headers, _HEADERS["power_long"], exclude=set(long_exclude),
    )
    if power_long_idx is not None:
        long_exclude.add(power_long_idx)
    connection_long_idx = _header_index_excluding(
        headers, _HEADERS["connection_long"], exclude=set(long_exclude),
    )
    if connection_long_idx is not None:
        long_exclude.add(connection_long_idx)
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
    mounting_short_idx = _header_index_excluding(
        headers, _HEADERS["mounting_short"], exclude=set(long_exclude),
    )
    if mounting_short_idx is not None:
        long_exclude.add(mounting_short_idx)
    power_short_idx = _header_index_excluding(
        headers, _HEADERS["power_short"], exclude=set(long_exclude),
    )
    if power_short_idx is not None:
        long_exclude.add(power_short_idx)
    connection_short_idx = _header_index_excluding(
        headers, _HEADERS["connection_short"], exclude=set(long_exclude),
    )
    if connection_short_idx is not None:
        long_exclude.add(connection_short_idx)
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"], exclude=set(long_exclude),
    )
    if qty_short_idx is not None:
        long_exclude.add(qty_short_idx)

    desc_idx = desc_long_idx if desc_long_idx is not None else desc_short_idx
    mounting_idx = mounting_long_idx if mounting_long_idx is not None else mounting_short_idx
    power_idx = power_long_idx if power_long_idx is not None else power_short_idx
    connection_idx = connection_long_idx if connection_long_idx is not None else connection_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":        tag_idx,
        "type":       type_idx,
        "desc":       desc_idx,
        "mfr":        mfr_idx,
        "model":      model_idx,
        "mounting":   mounting_idx,
        "power":      power_idx,
        "connection": connection_idx,
        "qty":        qty_idx,
        "notes":      notes_idx,
    }


_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[SecurityDeviceRecord]:
    idx = _security_indices(headers)
    records: list[SecurityDeviceRecord] = []
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
            stripped = re.sub(r"^(?:TAG|MARK|DEVICE|NO)\s+", "", tag,
                                 flags=re.IGNORECASE)
            if _TAG_RE.match(stripped):
                tag = stripped
            else:
                continue

        type_cell = _cell(row, idx["type"])
        desc = _cell(row, idx["desc"]) or type_cell
        mfr = _cell(row, idx["mfr"])
        model = _cell(row, idx["model"])
        mounting_raw = _cell(row, idx["mounting"])
        power_raw = _cell(row, idx["power"])
        connection_raw = _cell(row, idx["connection"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

        mounting = _parse_mounting(mounting_raw)
        power = _parse_power(power_raw)
        connection = _parse_connection(connection_raw)
        quantity = _parse_quantity(qty_raw)

        item_type = _classify_item_type(tag, desc)
        confidence = _device_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_power=power is not None,
            has_connection=connection is not None,
        )

        records.append(SecurityDeviceRecord(
            tag=tag,
            item_type=item_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            mounting=mounting,
            power=power,
            connection=connection,
            quantity=quantity,
            notes=notes_raw,
            confidence=confidence,
            source_page=page_index,
        ))
    return records


# ---------------------------------------------------------------------------
# Confidence + entry points
# ---------------------------------------------------------------------------


def _device_confidence(*, tag: str, has_description: bool,
                          has_manufacturer: bool, has_model: bool,
                          has_power: bool, has_connection: bool) -> float:
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_model,
        has_power, has_connection,
    ]
    score += 0.06 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, records: list[SecurityDeviceRecord]) -> float:
    if not records:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30
    if any(r.power is not None or r.connection is not None for r in records):
        score += 0.15
    if len(records) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_security_schedule_from_page(
    page: "fitz.Page", page_index: int = 0,
    *, sheet_id: str | None = None,
) -> SecurityScheduleResult:
    """Extract every security schedule (if any) from a single page."""
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = False
    for kw in _SECURITY_SCHEDULE_KEYWORDS:
        if kw not in upper:
            continue
        if kw == "DOOR HARDWARE SCHEDULE":
            if any(tok in upper for tok in _SECURITY_CONTEXT_TOKENS):
                has_phrase = True
                break
            continue
        has_phrase = True
        break

    all_records: list[SecurityDeviceRecord] = []
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
        if not _looks_like_security_header(headers):
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

    return SecurityScheduleResult(
        pages=[page_index] if all_records else [],
        devices=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_security_schedule(pdf_path: Path, page_index: int,
                                *, sheet_id: str | None = None,
                                ) -> SecurityScheduleResult:
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_security_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: SecurityScheduleResult):
    """Return a :class:`core.schemas.SecurityScheduleResult` Pydantic model."""
    from core import schemas as S

    return S.SecurityScheduleResult(
        pages=list(result.pages),
        devices=[
            S.SecurityDeviceRecord(
                tag=r.tag,
                item_type=r.item_type,
                description=r.description,
                manufacturer=r.manufacturer,
                model_number=r.model_number,
                mounting=r.mounting,
                power=r.power,
                connection=r.connection,
                quantity=r.quantity,
                notes=r.notes,
                confidence=r.confidence,
                source_sheet=r.source_sheet,
                source_page=r.source_page,
            )
            for r in result.devices
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
