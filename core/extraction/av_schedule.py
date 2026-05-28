"""Deterministic AV / IT equipment schedule extraction (Phase T2.11).

AV / IT equipment schedules live on T-series sheets (``T1.0`` / ``T-AV``
/ ``T2.0``) or A/V drawings and route to MasterFormat **Division 27**
(Communications).  Each schedule typically carries:

1. **Device tag** — letter+digit identifier with a family prefix
   (``DISP-1`` / ``DSP-1`` display, ``PROJ-1`` / ``PJ-1`` projector,
   ``CAM-1`` AV-context camera, ``MIC-1`` / ``M-1`` microphone,
   ``SPK-1`` / ``SP-1`` speaker, ``RACK-1`` / ``EQR-1`` rack,
   ``CTRL-1`` control processor, ``SW-1`` network switch).
2. **Type** — free text describing the device class.
3. **Manufacturer / model** — sometimes joined by ``/``, sometimes two
   distinct columns.
4. **Size / resolution / wattage** — display diagonal in inches,
   projector resolution (``4K`` / ``1080p``), speaker wattage.
5. **Mounting** — ``WALL`` / ``CEILING`` / ``RACK`` / ``FLOOR``.
6. **Power** — ``120V`` / ``PoE`` / ``PoE+`` / ``12VDC`` / ``USB-C``.
7. **Signal type** — ``HDMI`` / ``SDI`` / ``IP`` / ``USB``.
8. **Optional QTY column** — drives a high-confidence synthesised
   count (``0.90``); when absent the synthesiser falls back to
   ``0.55`` → HAND_TAKEOFF.

Phase T2.11 is the **seventh** downstream consumer of the shared
``header_index_excluding`` helper (door / panel / lighting / HVAC /
plumbing / kitchen+lab prior).  Header collisions resolved by the
two-pass picker:

* ``D`` / ``DISPLAY`` / ``DESCRIPTION`` / ``DEVICE`` — bare ``D``
  substring-collides with each.  Pin all long forms first.
* ``M`` / ``MIC`` / ``MODEL`` / ``MOUNTING`` / ``MARK`` — same
  pattern.
* ``P`` / ``POWER`` / ``PROJECTOR`` — same pattern.
* ``S`` / ``SIZE`` / ``SIGNAL`` / ``SPEAKER`` — same pattern.
* ``W`` / ``WATTAGE`` — same pattern.
* ``Q`` / ``QTY`` / ``QUANTITY`` — same pattern.

**CAM- cross-domain collision** with the security schedule is
resolved at the SCHEDULE level (this module's detection requires
an AV / video-conferencing keyword phrase OR an AV-shaped header)
and at the DESCRIPTION level (a ``CAM-N`` row whose description
mentions ``CONFERENCE`` / ``LECTURE`` / ``WEBCAM`` / ``HUDDLE``
classifies as AV CAMERA; a ``CAM-N`` row whose description
mentions ``SURVEILLANCE`` / ``CCTV`` / ``PTZ`` is REJECTED by the
classifier and falls through to ``OTHER`` so the security
extractor can claim it on its own pass).

Architectural pattern mirrors :mod:`core.extraction.kitchen_schedule`.
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
class AVDeviceRecord:
    """One AV / IT device record pulled off a T-series schedule."""

    tag: str
    item_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    size_or_resolution: str | None = None
    wattage: float | None = None
    mounting: str | None = None
    power: str | None = None
    signal_type: str | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class AVScheduleResult:
    """Aggregate AV-equipment-schedule pre-pass result for one page."""

    pages: list[int] = field(default_factory=list)
    devices: list[AVDeviceRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


_AV_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "AV SCHEDULE",
    "A/V SCHEDULE",
    "AUDIO VISUAL SCHEDULE",
    "AUDIO-VIDEO SCHEDULE",
    "AUDIO-VISUAL SCHEDULE",
    "AV EQUIPMENT SCHEDULE",
    "AV DEVICE SCHEDULE",
    "VIDEO CONFERENCING SCHEDULE",
    "AV/IT SCHEDULE",
    "DISPLAY SCHEDULE",
)


_AV_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "MARK", "DEVICE", "TYPE",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "SIZE", "RESOLUTION", "POWER", "P",
    "WATTAGE", "W",
    "MOUNTING", "MTG", "M",
    "SIGNAL", "S",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
    "DISPLAY", "D",
    "PROJECTOR",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_av_header(headers: Iterable[str]) -> bool:
    """Three-signal header heuristic for AV equipment schedules.

    Requires:

    1. a tag column (``TAG`` / ``MARK`` / ``DEVICE``),
    2. at least one description / spec column (``DESCRIPTION`` /
       ``DESC`` / ``MANUFACTURER`` / ``MFG`` / ``MFR`` / ``MODEL`` /
       ``TYPE``),
    3. at least one AV-specific spec column (``DISPLAY`` /
       ``PROJECTOR`` / ``RESOLUTION`` / ``SIGNAL`` / ``MOUNTING`` /
       ``HDMI``).

    Disqualifies headers carrying door / window / panel / lighting /
    HVAC / plumbing / kitchen / lab / security signals so a foreign
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
        "LAMP", "LAMPS", "LUMENS", "LM", "BALLAST", "DRIVER",
        # HVAC
        "CFM", "MBH", "TONS", "BTU", "BTUH",
        "REFRIG", "REFRIGERANT",
        # Plumbing
        "GPF", "GPM", "FLOW", "VENT", "WASTE",
        # Kitchen
        "GAS", "DRAIN", "UTILITIES", "UTIL",
        # Lab
        "FUME", "VACUUM", "BENCHTOP", "EPOXY", "PHENOLIC",
        # Security — DO NOT claim security schedules.  ``CONNECTION``
        # and ``CONTACT`` are unambiguously security-side header
        # tokens (cable / RS-485 / Wiegand columns or door-contact
        # rows).  ``READER`` and ``CARD`` ditto.
        "WIEGAND", "CARDREADER", "MAGLOCK", "SURVEILLANCE", "CCTV",
        "ACCESS", "CONNECTION", "CONTACT", "READER", "CARD",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "MARK", "DEVICE"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL", "TYPE",
    })
    # ``MOUNTING`` and ``POWER`` are shared with the security schedule
    # — they DO NOT alone qualify a header as AV.  An AV header must
    # carry at least one distinctively-AV token (DISPLAY / PROJECTOR
    # / RESOLUTION / SIGNAL / HDMI / SDI / SPEAKER / MICROPHONE).
    has_spec = bool(words & {
        "DISPLAY", "PROJECTOR", "RESOLUTION", "SIGNAL",
        "HDMI", "SDI", "PROJ", "SPEAKER", "MICROPHONE", "WATTAGE",
        # SIZE is AV-specific in this set — security schedules
        # don't carry a SIZE column.
        "SIZE",
    })
    return has_tag and has_desc and has_spec


def detect_av_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains an AV equipment schedule."""
    text = (page.get_text("text") or "").upper()
    has_phrase = any(kw in text for kw in _AV_SCHEDULE_KEYWORDS)
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
        if _looks_like_av_header(headers):
            return True
    if has_phrase:
        # Phrase fired with no AV-shaped header AND at least one
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
                          "GPF", "GPM", "FUME", "WIEGAND", "CCTV",
                          "MAGLOCK"}:
                return False
        return True
    return False


# ---------------------------------------------------------------------------
# Item-type detection from tag prefix
# ---------------------------------------------------------------------------
#
# AV CAM- vs Security CAM- disambiguation: the AV classifier accepts
# CAM- ONLY when the parent schedule is AV-shaped (this module's
# detection has already run) AND the description does not include
# obvious security keywords.  When the description carries
# ``SURVEILLANCE`` / ``CCTV`` / ``PTZ`` / ``DOME``, the classifier
# rejects the row to ``OTHER`` so it stays out of the AV CAMERA
# bucket; the security extractor will pick it up on its own pass
# if the page also matches a security schedule.

# Order matters: longer / more-specific prefixes BEFORE shorter ones.
_ITEM_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("DISPLAY", "DISP", "DSP", "MON"),     "DISPLAY"),
    (("PROJECTOR", "PROJ", "PJ"),            "PROJECTOR"),
    (("CAMERA", "CAM"),                       "CAMERA"),
    (("MICROPHONE", "MIC"),                   "MICROPHONE"),
    (("SPEAKER", "SPK", "SP"),                "SPEAKER"),
    (("RACK", "EQR"),                         "RACK"),
    (("CONTROL", "CTRL"),                     "CONTROL_PROCESSOR"),
    (("SWITCH", "SW"),                        "NETWORK_SWITCH"),
)


# Description keywords that REJECT a CAM- row from the AV CAMERA
# bucket because they clearly belong to surveillance / security.
_AV_CAM_SECURITY_KEYWORDS: tuple[str, ...] = (
    "SURVEILLANCE", "CCTV", "PTZ", "DOME", "FIXED DOME",
    "SECURITY CAMERA", "IP CAMERA SECURITY",
)

# Description keywords that POSITIVELY confirm a CAM- row as AV.
_AV_CAM_AV_KEYWORDS: tuple[str, ...] = (
    "CONFERENCE", "LECTURE", "WEBCAM", "HUDDLE",
    "VIDEO CONFERENCING", "CAPTURE", "TELEPRESENCE",
)


def _classify_item_type(tag: str, description: str | None = None) -> str:
    """Classify AV device from tag (``DISP-1``) or fallback to description.

    Special handling for ``CAM-`` rows: when the description carries
    a surveillance keyword, the row is REJECTED to ``OTHER`` so it
    falls outside the AV CAMERA bucket (the security extractor owns
    that row).
    """
    raw = (tag or "").strip().upper()
    desc_upper = (description or "").upper()
    if not raw:
        if description:
            return _classify_item_type(description)
        return "OTHER"

    head = re.split(r"[-_/\s]", raw, maxsplit=1)[0]

    # CAM- cross-domain guard: if the description carries an
    # unambiguous security keyword, reject the row to OTHER so
    # the AV synthesis doesn't classify a surveillance camera as
    # an AV conference cam.
    if head in {"CAM", "CAMERA"}:
        if any(kw in desc_upper for kw in _AV_CAM_SECURITY_KEYWORDS):
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
        # Security-keyword rejection still applies to bare description
        # classification (e.g. tag was empty/odd, description says
        # "PTZ surveillance camera").
        if any(kw in desc_upper for kw in _AV_CAM_SECURITY_KEYWORDS):
            return "OTHER"
        desc_hints = (
            ("DISPLAY",          "DISPLAY"),
            ("MONITOR",          "DISPLAY"),
            ("LCD",              "DISPLAY"),
            ("OLED",             "DISPLAY"),
            ("PROJECTOR",        "PROJECTOR"),
            ("CONFERENCE CAM",   "CAMERA"),
            ("WEBCAM",           "CAMERA"),
            ("LECTURE CAPTURE",  "CAMERA"),
            ("MICROPHONE",       "MICROPHONE"),
            ("CEILING MIC",      "MICROPHONE"),
            ("SPEAKER",          "SPEAKER"),
            ("LOUDSPEAKER",      "SPEAKER"),
            ("AV RACK",          "RACK"),
            ("EQUIPMENT RACK",   "RACK"),
            ("CONTROL PROCESSOR", "CONTROL_PROCESSOR"),
            ("DSP",              "CONTROL_PROCESSOR"),
            ("NETWORK SWITCH",   "NETWORK_SWITCH"),
            ("POE SWITCH",       "NETWORK_SWITCH"),
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


_RESOLUTION_RE: re.Pattern[str] = re.compile(
    r"(?P<val>4K|UHD|8K|1080P|720P|2160P|1440P|"
    r"\d+\s*(?:[\"x×]|INCH|IN\b))",
    re.IGNORECASE,
)


def _parse_resolution(raw: str | None) -> str | None:
    """Parse a resolution / size cell.  Stores the raw normalised string.

    Accepts ``4K`` / ``UHD`` / ``1080p`` / ``75"`` / ``85 inch`` /
    ``2160P``.  Returns the matched substring in upper-case, or
    ``None`` when nothing recognisable is in the cell.
    """
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _RESOLUTION_RE.search(upper)
    if m:
        # Normalise internal whitespace so ``"85 INCH"`` → ``"85INCH"``.
        return re.sub(r"\s+", "", m.group("val").upper())
    # Plain inches like '75' on its own.
    m2 = re.match(r"^\s*(\d{2,3})\s*$", text)
    if m2:
        return f'{m2.group(1)}"'
    return None


_WATTAGE_RE: re.Pattern[str] = re.compile(
    r"(\d+(?:\.\d+)?)\s*W\b", re.IGNORECASE,
)


def _parse_wattage(raw: str | None) -> float | None:
    """Parse a wattage cell.  Accepts ``40W`` / ``40`` / ``40.5 W``."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _WATTAGE_RE.search(upper)
    if m:
        try:
            return float(m.group(1))
        except ValueError:
            return None
    m2 = re.match(r"^\s*(\d+(?:\.\d+)?)\s*$", text)
    if m2:
        try:
            return float(m2.group(1))
        except ValueError:
            return None
    return None


_POWER_RE: re.Pattern[str] = re.compile(
    r"(?P<val>PoE\+?|120\s*V(?:AC)?|240\s*V(?:AC)?|"
    r"12\s*VDC|24\s*VDC|48\s*V|USB-?C)",
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
        # Normalise spacings.
        token = re.sub(r"\s+", "", token)
        return token
    return None


_SIGNAL_RE: re.Pattern[str] = re.compile(
    r"\b(HDMI|SDI|DISPLAYPORT|DP|USB(?:-?C)?|IP|HDBASE-?T|CAT6|VGA)\b",
    re.IGNORECASE,
)


def _parse_signal(raw: str | None) -> str | None:
    """Parse a signal-type cell.  Returns the normalised token or None."""
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    m = _SIGNAL_RE.search(upper)
    if m:
        return m.group(1).upper().replace("-", "")
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
    for token in ("WALL", "CEILING", "RACK", "FLOOR", "PENDANT",
                  "TABLE", "RECESSED", "SURFACE"):
        if token in upper:
            return token
    return upper


# ---------------------------------------------------------------------------
# Column picking + record assembly
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":           ("TAG", "MARK", "DEVICE", "NO"),
    "type_col":      ("TYPE",),
    "desc_long":     ("DESCRIPTION", "DESC"),
    "desc_short":    ("D",),
    "mfr":           ("MANUFACTURER", "MFR", "MFG", "MAKE"),
    "model":         ("MODEL", "MODEL NO", "PART"),
    "size":          ("SIZE", "RESOLUTION", "DIAGONAL"),
    "wattage_long":  ("WATTAGE", "WATTS"),
    "wattage_short": ("W",),
    "mounting_long": ("MOUNTING", "MTG"),
    "mounting_short": ("M",),
    "power_long":    ("POWER",),
    "power_short":   ("P",),
    "signal_long":   ("SIGNAL", "SIGNALTYPE"),
    "signal_short":  ("S",),
    "qty_long":      ("QUANTITY", "QTY"),
    "qty_short":     ("Q",),
    "notes":         ("NOTES", "REMARKS", "COMMENTS"),
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


def _av_indices(headers: list[str]) -> dict[str, int | None]:
    """Pick AV-device column indices using the two-pass picker.

    Seventh downstream consumer of :func:`_header_index_excluding`.
    Pins long-form columns first (``DESCRIPTION``, ``WATTAGE``,
    ``MOUNTING``, ``POWER``, ``SIGNAL``, ``QUANTITY``, ``NOTES``)
    so each multi-letter header claims its proper slot, then runs
    the short-form lookups (``D``, ``W``, ``M``, ``P``, ``S``,
    ``Q``) with EVERY long-form index in the exclusion set.  This
    is the AV-specific manifestation of the same pattern used by
    kitchen + lab — the collisions are just the AV letters.
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
    wattage_long_idx = _header_index_excluding(
        headers, _HEADERS["wattage_long"], exclude=set(long_exclude),
    )
    if wattage_long_idx is not None:
        long_exclude.add(wattage_long_idx)
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
    signal_long_idx = _header_index_excluding(
        headers, _HEADERS["signal_long"], exclude=set(long_exclude),
    )
    if signal_long_idx is not None:
        long_exclude.add(signal_long_idx)
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
    wattage_short_idx = _header_index_excluding(
        headers, _HEADERS["wattage_short"], exclude=set(long_exclude),
    )
    if wattage_short_idx is not None:
        long_exclude.add(wattage_short_idx)
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
    signal_short_idx = _header_index_excluding(
        headers, _HEADERS["signal_short"], exclude=set(long_exclude),
    )
    if signal_short_idx is not None:
        long_exclude.add(signal_short_idx)
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"], exclude=set(long_exclude),
    )
    if qty_short_idx is not None:
        long_exclude.add(qty_short_idx)

    desc_idx = desc_long_idx if desc_long_idx is not None else desc_short_idx
    wattage_idx = wattage_long_idx if wattage_long_idx is not None else wattage_short_idx
    mounting_idx = mounting_long_idx if mounting_long_idx is not None else mounting_short_idx
    power_idx = power_long_idx if power_long_idx is not None else power_short_idx
    signal_idx = signal_long_idx if signal_long_idx is not None else signal_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":      tag_idx,
        "type":     type_idx,
        "desc":     desc_idx,
        "mfr":      mfr_idx,
        "model":    model_idx,
        "size":     size_idx,
        "wattage":  wattage_idx,
        "mounting": mounting_idx,
        "power":    power_idx,
        "signal":   signal_idx,
        "qty":      qty_idx,
        "notes":    notes_idx,
    }


_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[AVDeviceRecord]:
    idx = _av_indices(headers)
    records: list[AVDeviceRecord] = []
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
        size_raw = _cell(row, idx["size"])
        wattage_raw = _cell(row, idx["wattage"])
        mounting_raw = _cell(row, idx["mounting"])
        power_raw = _cell(row, idx["power"])
        signal_raw = _cell(row, idx["signal"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        # Manufacturer / model split on '/' when only one column.
        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

        size_or_resolution = _parse_resolution(size_raw)
        wattage = _parse_wattage(wattage_raw)
        mounting = _parse_mounting(mounting_raw)
        power = _parse_power(power_raw)
        signal_type = _parse_signal(signal_raw)
        quantity = _parse_quantity(qty_raw)

        item_type = _classify_item_type(tag, desc)
        confidence = _device_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_spec=any(v is not None for v in (
                size_or_resolution, wattage, signal_type,
            )),
            has_mounting_or_power=any(v is not None for v in (
                mounting, power,
            )),
        )

        records.append(AVDeviceRecord(
            tag=tag,
            item_type=item_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            size_or_resolution=size_or_resolution,
            wattage=wattage,
            mounting=mounting,
            power=power,
            signal_type=signal_type,
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
                          has_spec: bool, has_mounting_or_power: bool) -> float:
    if not tag:
        return 0.5
    score = 0.65
    decorations = [
        has_description, has_manufacturer, has_model,
        has_spec, has_mounting_or_power,
    ]
    score += 0.06 * sum(1 for d in decorations if d)
    score = min(score, 0.95)
    score = max(score, 0.5)
    return round(score, 4)


def _score(has_phrase: bool, records: list[AVDeviceRecord]) -> float:
    if not records:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30
    if any(r.size_or_resolution is not None or r.signal_type is not None
           for r in records):
        score += 0.15
    if len(records) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_av_schedule_from_page(
    page: "fitz.Page", page_index: int = 0,
    *, sheet_id: str | None = None,
) -> AVScheduleResult:
    """Extract every AV equipment schedule (if any) from a single page."""
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _AV_SCHEDULE_KEYWORDS)

    all_records: list[AVDeviceRecord] = []
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
        if not _looks_like_av_header(headers):
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

    return AVScheduleResult(
        pages=[page_index] if all_records else [],
        devices=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_av_schedule(pdf_path: Path, page_index: int,
                          *, sheet_id: str | None = None,
                          ) -> AVScheduleResult:
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_av_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


# ---------------------------------------------------------------------------
# Pydantic-model bridge
# ---------------------------------------------------------------------------


def to_schema(result: AVScheduleResult):
    """Return a :class:`core.schemas.AVScheduleResult` Pydantic model."""
    from core import schemas as S

    return S.AVScheduleResult(
        pages=list(result.pages),
        devices=[
            S.AVDeviceRecord(
                tag=r.tag,
                item_type=r.item_type,
                description=r.description,
                manufacturer=r.manufacturer,
                model_number=r.model_number,
                size_or_resolution=r.size_or_resolution,
                wattage=r.wattage,
                mounting=r.mounting,
                power=r.power,
                signal_type=r.signal_type,
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
