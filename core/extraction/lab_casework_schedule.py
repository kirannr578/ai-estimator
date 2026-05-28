"""Deterministic lab casework / fume hood schedule extraction (Phase T2.10).

Lab casework schedules live on lab plans / I-series interior sheets
and route to MasterFormat Division 12 (Furnishings), section
``12 35 53`` Laboratory Casework.  Fume hoods + safety equipment
cross-route to Division 11 sections ``11 53 13`` (Fume Hoods) and
``11 53 19`` (Safety Equipment) per MasterFormat.  Each schedule
typically carries:

1. **Casework tag** — letter+digit identifier with a family prefix
   (``BC-1`` base cabinet / ``WC-1`` wall cabinet / ``TC-1`` tall
   cabinet / ``FH-1`` fume hood / ``LB-1`` lab bench / ``SC-1``
   safety cabinet / ``EW-1`` eyewash station).
2. **Type** — column or column derivative.
3. **Width × Depth × Height** — inches.
4. **Material** — ``EPOXY`` / ``STAINLESS`` / ``PHENOLIC`` /
   ``LAMINATE`` / ``WOOD``.
5. **Drawer / door config** — free text.
6. **Utilities** — gas / vacuum / water / electrical flags.
7. **Optional QTY column** — drives high-confidence synthesis.

Phase T2.10 is the SIXTH downstream consumer of
``header_index_excluding`` (door / panel / lighting / HVAC /
plumbing prior).  Header collisions resolved by the two-pass
picker:

* ``H`` / ``HEIGHT`` — bare ``H`` collides with ``HEIGHT``.
* ``W`` / ``WIDTH`` — same pattern.
* ``D`` / ``DEPTH`` — same pattern.
* ``T`` / ``TYPE`` — bare ``T`` collides with ``TYPE``.
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
class LabCaseworkRecord:
    tag: str
    item_type: str
    description: str | None = None
    manufacturer: str | None = None
    model_number: str | None = None
    width_in: float | None = None
    depth_in: float | None = None
    height_in: float | None = None
    material: str | None = None
    drawer_door_config: str | None = None
    utility_gas: bool | None = None
    utility_vacuum: bool | None = None
    utility_water: bool | None = None
    utility_electric: bool | None = None
    quantity: int | None = None
    notes: str | None = None
    confidence: float = 0.85
    source_sheet: str | None = None
    source_page: int = 0


@dataclass
class LabScheduleResult:
    pages: list[int] = field(default_factory=list)
    casework: list[LabCaseworkRecord] = field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


# ---------------------------------------------------------------------------
# Detection
# ---------------------------------------------------------------------------


_LAB_SCHEDULE_KEYWORDS: tuple[str, ...] = (
    "LABORATORY CASEWORK SCHEDULE",
    "LAB CASEWORK SCHEDULE",
    "LABORATORY CASEWORK",
    "LAB CASEWORK",
    "FUME HOOD SCHEDULE",
    "LABORATORY FURNITURE",
    "LAB FURNITURE",
    "CASEWORK SCHEDULE",
)


_LAB_HEADER_KEYWORDS: frozenset[str] = frozenset({
    "TAG", "ITEM", "MARK", "TYPE", "NO",
    "DESCRIPTION", "DESC",
    "MANUFACTURER", "MFG", "MFR",
    "MODEL",
    "WIDTH", "DEPTH", "HEIGHT",
    "W", "D", "H", "T",
    "MATERIAL", "MATL",
    "FUME", "VACUUM", "GAS", "WATER", "ELEC", "ELECTRIC",
    "DRAWER", "DOORS", "DRWR", "DOOR",
    "QTY", "Q", "QUANTITY",
    "NOTES", "REMARKS",
})


def _normalize_header(s: str) -> str:
    return re.sub(r"[^A-Z]+", " ", (s or "").upper()).strip()


def _looks_like_lab_header(headers: Iterable[str]) -> bool:
    """Three-signal header heuristic for lab casework / fume hood schedules."""
    words: set[str] = set()
    for h in headers:
        if not h:
            continue
        words.update(re.findall(r"[A-Za-z]+", h.upper()))
    if not words:
        return False
    disqualifiers = {
        "HARDWARE", "GLAZING", "OPERATION", "FRAME",
        "CIRCUIT", "CKT", "BREAKER", "BKR", "AMPS",
        "LAMP", "LAMPS", "LUMENS", "BALLAST",
        "CFM", "MBH", "BTU", "BTUH", "TONS",
        "REFRIG", "REFRIGERANT",
        "GPF", "GPM", "FLOW", "VENT", "WASTE",
        "HDMI", "RESOLUTION", "PROJECTOR", "SPEAKER",
        "POE", "WIEGAND", "CARDREADER", "MAGLOCK",
    }
    if words & disqualifiers:
        return False
    has_tag = bool(words & {"TAG", "ITEM", "MARK", "NO"})
    has_desc = bool(words & {
        "DESCRIPTION", "DESC", "MANUFACTURER", "MFG", "MFR", "MODEL", "TYPE",
    })
    has_spec = bool(words & {
        "FUME", "VACUUM", "MATERIAL", "MATL", "DRAWER", "DOORS", "DRWR",
        "WIDTH", "DEPTH", "HEIGHT", "CASEWORK",
    })
    return has_tag and has_desc and has_spec


def detect_lab_schedule_page(page: "fitz.Page") -> bool:
    """True when the page very likely contains a lab casework schedule."""
    text = (page.get_text("text") or "").upper()
    has_phrase = any(kw in text for kw in _LAB_SCHEDULE_KEYWORDS)
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
        if _looks_like_lab_header(headers):
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
                          "CIRCUIT", "BREAKER", "GPF", "GPM"}:
                return False
        return True
    return False


# ---------------------------------------------------------------------------
# Item-type detection from tag prefix
# ---------------------------------------------------------------------------


_ITEM_TYPE_PREFIXES: tuple[tuple[tuple[str, ...], str], ...] = (
    (("BC", "BCAB"),               "BASE_CABINET"),
    (("WC", "WCAB"),               "WALL_CABINET"),
    (("TC", "TCAB"),               "TALL_CABINET"),
    (("FH", "FUME"),               "FUME_HOOD"),
    (("LB", "BENCH"),              "LAB_BENCH"),
    (("SC", "SAFETY"),             "SAFETY_CABINET"),
    (("EW", "EYEWASH"),            "EYEWASH_STATION"),
)


def _classify_item_type(tag: str, description: str | None = None) -> str:
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
            ("FUME HOOD",        "FUME_HOOD"),
            ("FUMEHOOD",         "FUME_HOOD"),
            ("BIOSAFETY",        "FUME_HOOD"),
            ("BASE CABINET",     "BASE_CABINET"),
            ("WALL CABINET",     "WALL_CABINET"),
            ("TALL CABINET",     "TALL_CABINET"),
            ("LAB BENCH",        "LAB_BENCH"),
            ("LABORATORY BENCH", "LAB_BENCH"),
            ("SAFETY CABINET",   "SAFETY_CABINET"),
            ("EYEWASH",          "EYEWASH_STATION"),
            ("EYE WASH",         "EYEWASH_STATION"),
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


def _parse_inches(raw: str | None) -> float | None:
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


def _flag_from_cell(raw: str | None) -> bool | None:
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
    if upper in {"GAS", "VAC", "VACUUM", "WATER", "ELEC", "ELECTRIC",
                  "DI", "DRAIN", "AIR"}:
        return True
    if any(c.isdigit() for c in text):
        return True
    return None


def _normalize_material(raw: str | None) -> str | None:
    if raw is None:
        return None
    text = str(raw).strip()
    if not text:
        return None
    upper = text.upper()
    if upper in {"-", "--", "N/A", "NA", "NONE"}:
        return None
    return upper


# ---------------------------------------------------------------------------
# Column picking
# ---------------------------------------------------------------------------


_HEADERS: dict[str, tuple[str, ...]] = {
    "tag":          ("TAG", "ITEM", "MARK", "NO"),
    "type_long":    ("TYPE",),
    "type_short":   ("T",),
    "desc_long":    ("DESCRIPTION", "DESC"),
    "mfr":          ("MANUFACTURER", "MFR", "MFG", "MAKE"),
    "model":        ("MODEL", "MODEL NO", "PART"),
    "width_long":   ("WIDTH",),
    "width_short":  ("W",),
    "depth_long":   ("DEPTH",),
    "depth_short":  ("D",),
    "height_long":  ("HEIGHT",),
    "height_short": ("H",),
    "size":         ("SIZE", "DIMENSIONS", "DIM"),
    "material":     ("MATERIAL", "MATL", "MAT", "TOP"),
    "drawer_door":  ("DRAWER", "DRAWERS", "DOORS", "DRWR", "CONFIG"),
    "gas":          ("GAS",),
    "vacuum":       ("VACUUM", "VAC"),
    "water":        ("WATER",),
    "electric":     ("ELEC", "ELECTRIC", "POWER"),
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


def _lab_indices(headers: list[str]) -> dict[str, int | None]:
    """Two-pass picker: pin long-form first, then short-form excluding all longs.

    Sixth downstream consumer of ``header_index_excluding``.
    Lab-specific collisions: ``T``/``TYPE``, ``W``/``WIDTH``,
    ``D``/``DEPTH``, ``H``/``HEIGHT``, ``Q``/``QTY``.
    """
    tag_idx = _header_index(headers, _HEADERS["tag"])
    type_long_idx = _header_index_excluding(
        headers, _HEADERS["type_long"],
        exclude={i for i in (tag_idx,) if i is not None},
    )
    desc_long_idx = _header_index_excluding(
        headers, _HEADERS["desc_long"],
        exclude={i for i in (tag_idx, type_long_idx) if i is not None},
    )
    long_exclude: set[int] = {
        i for i in (tag_idx, type_long_idx, desc_long_idx) if i is not None
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
    size_idx = _header_index_excluding(
        headers, _HEADERS["size"], exclude=set(long_exclude),
    )
    if size_idx is not None:
        long_exclude.add(size_idx)
    material_idx = _header_index_excluding(
        headers, _HEADERS["material"], exclude=set(long_exclude),
    )
    if material_idx is not None:
        long_exclude.add(material_idx)
    drawer_idx = _header_index_excluding(
        headers, _HEADERS["drawer_door"], exclude=set(long_exclude),
    )
    if drawer_idx is not None:
        long_exclude.add(drawer_idx)
    gas_idx = _header_index_excluding(
        headers, _HEADERS["gas"], exclude=set(long_exclude),
    )
    if gas_idx is not None:
        long_exclude.add(gas_idx)
    vacuum_idx = _header_index_excluding(
        headers, _HEADERS["vacuum"], exclude=set(long_exclude),
    )
    if vacuum_idx is not None:
        long_exclude.add(vacuum_idx)
    water_idx = _header_index_excluding(
        headers, _HEADERS["water"], exclude=set(long_exclude),
    )
    if water_idx is not None:
        long_exclude.add(water_idx)
    electric_idx = _header_index_excluding(
        headers, _HEADERS["electric"], exclude=set(long_exclude),
    )
    if electric_idx is not None:
        long_exclude.add(electric_idx)
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

    # ---- SHORT-FORM with all longs excluded ----
    type_short_idx = _header_index_excluding(
        headers, _HEADERS["type_short"], exclude=set(long_exclude),
    )
    if type_short_idx is not None:
        long_exclude.add(type_short_idx)
    width_short_idx = _header_index_excluding(
        headers, _HEADERS["width_short"], exclude=set(long_exclude),
    )
    if width_short_idx is not None:
        long_exclude.add(width_short_idx)
    depth_short_idx = _header_index_excluding(
        headers, _HEADERS["depth_short"], exclude=set(long_exclude),
    )
    if depth_short_idx is not None:
        long_exclude.add(depth_short_idx)
    height_short_idx = _header_index_excluding(
        headers, _HEADERS["height_short"], exclude=set(long_exclude),
    )
    if height_short_idx is not None:
        long_exclude.add(height_short_idx)
    qty_short_idx = _header_index_excluding(
        headers, _HEADERS["qty_short"], exclude=set(long_exclude),
    )
    if qty_short_idx is not None:
        long_exclude.add(qty_short_idx)

    type_idx = type_long_idx if type_long_idx is not None else type_short_idx
    width_idx = width_long_idx if width_long_idx is not None else width_short_idx
    depth_idx = depth_long_idx if depth_long_idx is not None else depth_short_idx
    height_idx = height_long_idx if height_long_idx is not None else height_short_idx
    qty_idx = qty_long_idx if qty_long_idx is not None else qty_short_idx

    return {
        "tag":      tag_idx,
        "type":     type_idx,
        "desc":     desc_long_idx,
        "mfr":      mfr_idx,
        "model":    model_idx,
        "width":    width_idx,
        "depth":    depth_idx,
        "height":   height_idx,
        "size":     size_idx,
        "material": material_idx,
        "drawer":   drawer_idx,
        "gas":      gas_idx,
        "vacuum":   vacuum_idx,
        "water":    water_idx,
        "electric": electric_idx,
        "qty":      qty_idx,
        "notes":    notes_idx,
    }


_TAG_RE: re.Pattern[str] = re.compile(
    r"^\s*[A-Z]{1,6}(?:[-_/]?[A-Z0-9]+)*\s*$",
    re.IGNORECASE,
)


def _records_from_table(
    headers: list[str], data_rows: list[list[str]], page_index: int,
) -> list[LabCaseworkRecord]:
    idx = _lab_indices(headers)
    records: list[LabCaseworkRecord] = []
    for row in data_rows:
        if not row:
            continue
        tag = _cell(row, idx["tag"])
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

        type_cell = _cell(row, idx["type"])
        desc = _cell(row, idx["desc"]) or type_cell
        mfr = _cell(row, idx["mfr"])
        model = _cell(row, idx["model"])
        size_raw = _cell(row, idx["size"])
        width_raw = _cell(row, idx["width"])
        depth_raw = _cell(row, idx["depth"])
        height_raw = _cell(row, idx["height"])
        material_raw = _cell(row, idx["material"])
        drawer_raw = _cell(row, idx["drawer"])
        gas_raw = _cell(row, idx["gas"])
        vacuum_raw = _cell(row, idx["vacuum"])
        water_raw = _cell(row, idx["water"])
        electric_raw = _cell(row, idx["electric"])
        qty_raw = _cell(row, idx["qty"])
        notes_raw = _cell(row, idx["notes"])

        if mfr and model is None and "/" in mfr:
            left, right = (s.strip() for s in mfr.split("/", 1))
            if left and right:
                mfr, model = left, right

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

        material = _normalize_material(material_raw)
        utility_gas = _flag_from_cell(gas_raw)
        utility_vacuum = _flag_from_cell(vacuum_raw)
        utility_water = _flag_from_cell(water_raw)
        utility_electric = _flag_from_cell(electric_raw)
        quantity = _parse_quantity(qty_raw)

        item_type = _classify_item_type(tag, type_cell or desc)
        confidence = _casework_confidence(
            tag=tag,
            has_description=bool(desc),
            has_manufacturer=bool(mfr),
            has_model=bool(model),
            has_dimensions=any(v is not None for v in (
                width_in, depth_in, height_in,
            )),
            has_utilities=any(v is True for v in (
                utility_gas, utility_vacuum, utility_water, utility_electric,
            )),
        )

        records.append(LabCaseworkRecord(
            tag=tag,
            item_type=item_type,
            description=(desc.strip() if desc else None),
            manufacturer=(mfr.strip() if mfr else None),
            model_number=(model.strip() if model else None),
            width_in=width_in,
            depth_in=depth_in,
            height_in=height_in,
            material=material,
            drawer_door_config=(drawer_raw.strip() if drawer_raw else None),
            utility_gas=utility_gas,
            utility_vacuum=utility_vacuum,
            utility_water=utility_water,
            utility_electric=utility_electric,
            quantity=quantity,
            notes=notes_raw,
            confidence=confidence,
            source_page=page_index,
        ))
    return records


def _casework_confidence(*, tag: str, has_description: bool,
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


def _score(has_phrase: bool, records: list[LabCaseworkRecord]) -> float:
    if not records:
        return 0.0
    score = 0.0
    if has_phrase:
        score += 0.40
    score += 0.30
    if any(r.material is not None for r in records):
        score += 0.15
    if len(records) >= 3:
        score += 0.15
    return min(score, 1.0)


def extract_lab_schedule_from_page(
    page: "fitz.Page", page_index: int = 0,
    *, sheet_id: str | None = None,
) -> LabScheduleResult:
    text = page.get_text("text") or ""
    upper = text.upper()
    has_phrase = any(kw in upper for kw in _LAB_SCHEDULE_KEYWORDS)

    all_records: list[LabCaseworkRecord] = []
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
        if not _looks_like_lab_header(headers):
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

    return LabScheduleResult(
        pages=[page_index] if all_records else [],
        casework=all_records,
        confidence=round(_score(has_phrase, all_records), 4),
        raw_table_text="\n".join(header_debug),
    )


def extract_lab_schedule(pdf_path: Path, page_index: int,
                            *, sheet_id: str | None = None,
                            ) -> LabScheduleResult:
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        if page_index < 0 or page_index >= len(doc):
            raise IndexError(
                f"page_index {page_index} out of range for {pdf_path.name} "
                f"({len(doc)} pages)"
            )
        return extract_lab_schedule_from_page(
            doc[page_index], page_index, sheet_id=sheet_id,
        )


def to_schema(result: LabScheduleResult):
    """Return a :class:`core.schemas.LabScheduleResult` Pydantic model."""
    from core import schemas as S

    return S.LabScheduleResult(
        pages=list(result.pages),
        casework=[
            S.LabCaseworkRecord(
                tag=r.tag,
                item_type=r.item_type,
                description=r.description,
                manufacturer=r.manufacturer,
                model_number=r.model_number,
                width_in=r.width_in,
                depth_in=r.depth_in,
                height_in=r.height_in,
                material=r.material,
                drawer_door_config=r.drawer_door_config,
                utility_gas=r.utility_gas,
                utility_vacuum=r.utility_vacuum,
                utility_water=r.utility_water,
                utility_electric=r.utility_electric,
                quantity=r.quantity,
                notes=r.notes,
                confidence=r.confidence,
                source_sheet=r.source_sheet,
                source_page=r.source_page,
            )
            for r in result.casework
        ],
        confidence=result.confidence,
        raw_table_text=result.raw_table_text,
    )
