"""Discipline-specific extractors.

Each extractor takes a `Sheet` plus the shared `LLMClient` and returns a
`SheetExtraction`. The `extract_sheet` dispatcher routes the sheet to the
right extractor based on its classified `discipline` + `sheet_type`.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from prompts import load as load_prompt

from .extraction.drawing_prepass import (
    CONFIDENCE_THRESHOLD,
    DrawingPrepassResult as _PrepassDC,
    prepass_drawing_page,
    to_schema as prepass_to_schema,
)
from .llm_client import LLMClient
from .pdf_processor import DocumentBundle
from .schemas import (
    Alternate,
    AlternateLine,
    AlternateType,
    BidPackage,
    Discipline,
    DoorEntry,
    MEPItem,
    Room,
    Sheet,
    SheetExtraction,
    SheetType,
    SiteInfo,
    SpecSection,
    StructuralElement,
    TakeoffItem,
    UnitPrice,
    WindowEntry,
)

logger = logging.getLogger(__name__)

SYSTEM = "You are a precise construction estimator. Return ONLY JSON. No prose, no markdown fences."


# ---------------------------------------------------------------------------
# T10 F-3 — LLM safety-refusal detection + constrained-context retry
# ---------------------------------------------------------------------------
#
# Background. During T10 calibration v4 the gpt-4o vision model refused
# to analyse 7 architectural sheets and 2 classifier prompts whose
# embedded photographs were tagged ``REFERENCE ONLY`` (typically US
# Army facility reference shots). The refusal text — variants of
# "I'm sorry, I can't assist with that" — surfaced inside the
# ``LLMClient`` JSON-repair loop and ultimately bubbled up as a
# ``ValueError("LLM did not return JSON. First 400 chars: …")``. The
# extractor treated this as a generic failure, returned zero takeoff
# rows, and the page was silently dropped — costing ~25-35 missed
# rows across the corpus.
#
# Fix. Detect the refusal text in any string the LLM (or its repair
# loop) surfaces, attempt **one** retry with a constrained
# business-context preamble that explicitly scopes the work to
# construction takeoff and tells the model to ignore photographs /
# REFERENCE ONLY annotations, and — if the retry also refuses — return
# an empty extraction with ``refused=True`` so downstream queue
# worksheets and exports surface the sheet for human review instead
# of silently swallowing it. Crucially we do **not** modify the
# ``LLMClient`` contract (per T10 spec) — refusal detection happens
# at the extractor boundary by inspecting the raised exception text.
_REFUSAL_PATTERNS: tuple[str, ...] = (
    "i'm sorry, i can't assist",
    "i'm sorry, i cannot assist",
    "i cannot help with",
    "i can't help with",
    "i am unable to",
    "i'm unable to",
)

_REFUSAL_RETRY_PREFIX: str = (
    "This is a construction-bid context. The drawing sheet shows a "
    "building floor plan, schedule, or detail. Extract only "
    "construction takeoff line items (counts, dimensions, materials). "
    "Ignore any photographs or REFERENCE ONLY annotations."
)


def _is_refusal(text: Any) -> bool:
    """T10 F-3 — Return True iff ``text`` looks like an LLM safety refusal.

    Accepts ``str`` (the common case — a response body or exception
    message), ``None``, or anything else (returns False for non-strings
    and for empty / whitespace-only strings). Matching is
    case-insensitive substring on a small allow-list of refusal
    phrases (``_REFUSAL_PATTERNS``). The patterns intentionally avoid
    bare ``"sorry"`` so neutral prose containing the word doesn't
    trip the detector.
    """
    if not isinstance(text, str):
        return False
    lower = text.strip().lower()
    if not lower:
        return False
    return any(pat in lower for pat in _REFUSAL_PATTERNS)


def _call_image_with_refusal_retry(
    llm: LLMClient,
    *,
    image_path: str,
    system_prompt: str,
    user_prompt: str,
    extra_context: str,
    sheet_id: str,
) -> tuple[Any, bool, list[str]]:
    """T10 F-3 — Call ``llm.analyze_image`` with refusal detection + retry.

    Returns a 3-tuple ``(parsed, refused, warnings)``:

    * ``parsed`` — the parsed JSON value on success, or ``None`` when
      both attempts refused or the call raised a non-refusal error.
    * ``refused`` — True iff the LLM refused twice in a row (initial
      attempt + constrained-context retry).
    * ``warnings`` — structured warning strings to attach to the
      ``SheetExtraction`` so they surface in exports and queue
      worksheets.

    Refusal is detected by inspecting the raised exception's message
    (the underlying ``LLMClient`` already includes the first 400
    chars of the offending response in its ``ValueError``). A
    non-refusal exception is re-raised by the caller via the
    ``warnings``/``parsed=None`` channel so the existing
    ``except Exception`` handler in :func:`extract_sheet` keeps the
    same shape it had before T10 F-3.
    """
    warnings: list[str] = []

    def _try(user: str, extra: str) -> tuple[Any, bool, Exception | None]:
        """Single attempt. Returns ``(parsed, refused, non_refusal_exc)``."""
        try:
            resp = llm.analyze_image(
                image_path=image_path,
                system_prompt=system_prompt,
                user_prompt=user,
                extra_context=extra,
            )
        except Exception as exc:  # noqa: BLE001 — narrow via _is_refusal
            if _is_refusal(str(exc)):
                return None, True, None
            return None, False, exc
        # Defensive: even if the client returned successfully, scan
        # the response text in case a future client version stops
        # raising on refusals.
        if _is_refusal(getattr(resp, "text", None)):
            return None, True, None
        return resp.parsed, False, None

    parsed, refused, exc = _try(user_prompt, extra_context)
    if exc is not None:
        # Non-refusal error: re-raise via warning + None so the
        # extract_sheet handler can keep its existing failure shape.
        raise exc
    if not refused:
        return parsed, False, warnings

    logger.warning(
        "LLM safety refusal on sheet %s; retrying with constrained-context prompt",
        sheet_id,
    )
    warnings.append(
        f"LLM safety refusal on initial attempt for {sheet_id}; "
        f"retrying with constrained-context prompt"
    )
    retry_user_prompt = f"{_REFUSAL_RETRY_PREFIX}\n\n{user_prompt}"
    parsed, refused, exc = _try(retry_user_prompt, extra_context)
    if exc is not None:
        raise exc
    if refused:
        logger.warning(
            "LLM refused twice on sheet %s; returning empty extraction with refused=True",
            sheet_id,
        )
        warnings.append(
            f"LLM safety refusal repeated twice for {sheet_id} "
            f"(initial + constrained-context retry); sheet flagged "
            f"refused=True for human review"
        )
        return None, True, warnings
    warnings.append(
        f"LLM safety refusal on {sheet_id} resolved after constrained-context retry"
    )
    return parsed, False, warnings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _safe_list(d: dict, key: str) -> list:
    val = d.get(key)
    return val if isinstance(val, list) else []


def _safe_dict(d: dict, key: str) -> dict | None:
    val = d.get(key)
    return val if isinstance(val, dict) else None


def _coerce_room(d: dict, sheet_id: str) -> Room | None:
    if not isinstance(d, dict) or not d.get("name"):
        return None
    try:
        return Room(
            name=str(d["name"]),
            number=d.get("number"),
            area_sqft=d.get("area_sqft"),
            perimeter_ft=d.get("perimeter_ft"),
            ceiling_height_ft=d.get("ceiling_height_ft"),
            floor_finish=d.get("floor_finish"),
            base_finish=d.get("base_finish"),
            wall_finish=d.get("wall_finish"),
            ceiling_finish=d.get("ceiling_finish"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception as exc:
        logger.debug("Skipping malformed room: %s (%s)", d, exc)
        return None


def _coerce_door(d: dict, sheet_id: str) -> DoorEntry | None:
    if not isinstance(d, dict) or not d.get("mark"):
        return None
    try:
        return DoorEntry(
            mark=str(d["mark"]),
            type=d.get("type"),
            width_in=d.get("width_in"),
            height_in=d.get("height_in"),
            rating=d.get("rating"),
            hardware_set=d.get("hardware_set"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _coerce_window(d: dict, sheet_id: str) -> WindowEntry | None:
    if not isinstance(d, dict) or not d.get("mark"):
        return None
    try:
        return WindowEntry(
            mark=str(d["mark"]),
            type=d.get("type"),
            width_in=d.get("width_in"),
            height_in=d.get("height_in"),
            glazing=d.get("glazing"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _coerce_structural(d: dict, sheet_id: str) -> StructuralElement | None:
    if not isinstance(d, dict) or not d.get("kind"):
        return None
    try:
        return StructuralElement(
            kind=str(d["kind"]),
            mark=d.get("mark"),
            material=d.get("material"),
            size=d.get("size"),
            quantity=float(d.get("quantity") or 0),
            unit=str(d.get("unit") or "EA"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _coerce_mep(d: dict, sheet_id: str) -> MEPItem | None:
    if not isinstance(d, dict) or not d.get("description"):
        return None
    try:
        disc_raw = (d.get("discipline") or "M").upper()
        try:
            disc = Discipline(disc_raw)
        except ValueError:
            disc = Discipline.MECHANICAL
        return MEPItem(
            discipline=disc,
            category=str(d.get("category") or "equipment"),
            description=str(d["description"]),
            quantity=float(d.get("quantity") or 0),
            unit=str(d.get("unit") or "EA"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _coerce_spec(d: dict, sheet_id: str) -> SpecSection | None:
    if not isinstance(d, dict) or not d.get("csi_section") or not d.get("title"):
        return None
    try:
        reqs = d.get("requirements") or []
        if not isinstance(reqs, list):
            reqs = []
        return SpecSection(
            csi_section=str(d["csi_section"]),
            title=str(d["title"]),
            summary=d.get("summary"),
            requirements=[str(r) for r in reqs],
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _coerce_takeoff(d: dict, sheet_id: str) -> TakeoffItem | None:
    if not isinstance(d, dict) or not d.get("description"):
        return None
    try:
        division = str(d.get("csi_division") or "").strip()
        if not division:
            section = str(d.get("csi_section") or "")
            division = section[:2] if section else "01"
        return TakeoffItem(
            csi_division=division.zfill(2)[:2],
            csi_section=d.get("csi_section"),
            description=str(d["description"]),
            quantity=float(d.get("quantity") or 0),
            unit=str(d.get("unit") or "EA"),
            confidence=float(d.get("confidence") if d.get("confidence") is not None else 0.6),
            source_sheet_ids=[sheet_id],
            notes=d.get("notes"),
        )
    except Exception as exc:
        logger.debug("Skipping malformed takeoff: %s (%s)", d, exc)
        return None


def _coerce_alternate(d: dict) -> Alternate | None:
    if not isinstance(d, dict) or not d.get("description"):
        return None
    try:
        amount = d.get("amount")
        return Alternate(
            number=str(d["number"]) if d.get("number") else None,
            description=str(d["description"]),
            add_or_deduct=str(d["add_or_deduct"]) if d.get("add_or_deduct") else None,
            amount=float(amount) if amount not in (None, "", "null") else None,
        )
    except Exception:
        return None


def _coerce_unit_price(d: dict) -> UnitPrice | None:
    if not isinstance(d, dict) or not d.get("description"):
        return None
    try:
        amount = d.get("amount")
        return UnitPrice(
            description=str(d["description"]),
            unit=str(d["unit"]) if d.get("unit") else None,
            amount=float(amount) if amount not in (None, "", "null") else None,
        )
    except Exception:
        return None


def _coerce_bid_package(data: dict, pdf_name: str) -> BidPackage | None:
    if not isinstance(data, dict):
        return None

    def _strs(key: str) -> list[str]:
        raw = data.get(key) or []
        if not isinstance(raw, list):
            return []
        return [str(x).strip() for x in raw if str(x).strip()]

    # Owner / GC / contractor — read the new fields and fall back to the
    # legacy `contractor` field when the LLM didn't emit `gc` (old prompts,
    # cached responses). The BidPackage model_validator then mirrors the
    # final pair to keep `contractor` populated for backward compatibility.
    owner = str(data["owner"]).strip() if data.get("owner") else None
    gc_val = str(data["gc"]).strip() if data.get("gc") else None
    legacy_contractor = str(data["contractor"]).strip() if data.get("contractor") else None
    if gc_val is None and legacy_contractor is not None:
        gc_val = legacy_contractor

    # document_kind — default to "trade_package" when missing. The validator
    # in the schema is a Literal so anything other than the two allowed
    # values will fail loudly; coerce unknown values back to the default.
    dk_raw = data.get("document_kind")
    if dk_raw in ("trade_package", "supporting_document"):
        document_kind = dk_raw
    else:
        document_kind = "trade_package"

    try:
        return BidPackage(
            pdf_name=pdf_name,
            package_number=str(data["package_number"]) if data.get("package_number") else None,
            trade_name=str(data["trade_name"]) if data.get("trade_name") else None,
            project_name=str(data["project_name"]) if data.get("project_name") else None,
            project_number=str(data["project_number"]) if data.get("project_number") else None,
            project_location=str(data["project_location"]) if data.get("project_location") else None,
            bid_due=str(data["bid_due"]) if data.get("bid_due") else None,
            owner=owner,
            gc=gc_val,
            contractor=legacy_contractor,
            contact=str(data["contact"]) if data.get("contact") else None,
            document_kind=document_kind,
            csi_divisions=_strs("csi_divisions"),
            csi_sections=_strs("csi_sections"),
            inclusions=_strs("inclusions"),
            exclusions=_strs("exclusions"),
            alternates=[a for a in (_coerce_alternate(x) for x in _safe_list(data, "alternates")) if a],
            unit_prices=[u for u in (_coerce_unit_price(x) for x in _safe_list(data, "unit_prices")) if u],
            second_tier_required=bool(data.get("second_tier_required")),
            referenced_drawings=_strs("referenced_drawings"),
            referenced_specs=_strs("referenced_specs"),
            summary=str(data["summary"]) if data.get("summary") else None,
            warnings=_strs("warnings"),
        )
    except Exception as exc:
        logger.warning("Failed to coerce bid package %s: %s", pdf_name, exc)
        return None


def _bid_package_has_content(bp: BidPackage) -> bool:
    """True when the coerced package carries at least one meaningful field."""
    if (
        bp.trade_name
        or bp.package_number
        or bp.project_name
        or bp.project_number
        or bp.project_location
        or bp.bid_due
        or bp.owner
        or bp.gc
        or bp.contractor
        or bp.contact
        or bp.summary
    ):
        return True
    if (
        bp.inclusions
        or bp.exclusions
        or bp.alternates
        or bp.unit_prices
        or bp.csi_divisions
        or bp.csi_sections
        or bp.referenced_drawings
        or bp.referenced_specs
    ):
        return True
    return False


# ---------------------------------------------------------------------------
# Supporting-document heuristic
# ---------------------------------------------------------------------------
#
# Cross-cutting reference documents (wage determinations, sample agreements,
# tax-exemption certificates, HSP form templates, UGSC / SGC, Instructions
# to Bidders boilerplate, AIA contract templates) routinely show up in the
# project inbox alongside the real trade bid packages. Pre-calibration v3
# they all landed in the Bid Packages table with `trade_name='other'`,
# polluting the export.
#
# `_supporting_doc_hint` is a cheap, deterministic filename + first-page
# heuristic the bundle dispatcher can call BEFORE the LLM to seed the
# extraction prompt with a strong classification hint. It's intentionally
# generous (better to ask the LLM "is this a supporting doc?" with a hint
# than to re-run on a misclassification).
#
# Keywords are case-insensitive substring matches over the filename and the
# first ~2000 chars of vector text. Extend this list as new document
# variants surface — the test suite covers the common cases.


_SUPPORTING_DOC_KEYWORDS: tuple[str, ...] = (
    # Wage determinations / prevailing-wage tables
    "wage determination",
    "wage decision",
    "wage rates",
    "prevailing wage",
    "davis-bacon",
    "davis bacon",
    "dba wd",
    "dbra",
    " wd ",
    "tx2026",
    "tx 2026",
    # Tax exemption / sales-tax cert
    "tax exemption",
    "tax-exempt",
    "tax exempt certificate",
    "sales tax",
    # Sample / template construction services agreements
    "sample agreement",
    "sample contract",
    "template agreement",
    "csa template",
    "sample construction services agreement",
    "construction services agreement",
    # HSP / HUB Subcontracting Plan templates
    "hub subcontracting plan",
    "subcontracting plan form",
    "hsp form",
    " hsp ",
    # Uniform / Supplementary General Conditions, ITB, AIA templates
    "ugsc",
    "uniform general conditions",
    "supplementary general conditions",
    "instructions to bidders",
    "instructions to offerors",
    "aia document",
)


def _supporting_doc_hint(filename: str, first_page_text: str) -> bool:
    """Return True when filename + first-page text look like a supporting document.

    Cheap deterministic check used BEFORE the LLM extraction to seed the
    prompt with a strong classification hint. False positives are tolerable
    (the LLM still gets to decide); false negatives just mean the document
    is treated as a normal trade package, which is the pre-v3 behavior.

    Args:
        filename: The PDF filename (basename or full path — both work).
        first_page_text: The vector text from page 1 (truncated to ~2000
            chars is enough for the keyword scan).
    """
    haystack = " ".join([
        (filename or "").lower(),
        (first_page_text or "")[:2000].lower(),
    ])
    for kw in _SUPPORTING_DOC_KEYWORDS:
        if kw in haystack:
            return True
    return False


def _coerce_site(d: dict | None, sheet_id: str) -> SiteInfo | None:
    if not isinstance(d, dict):
        return None
    try:
        return SiteInfo(
            site_area_sqft=d.get("site_area_sqft"),
            paving_area_sqft=d.get("paving_area_sqft"),
            sidewalk_lf=d.get("sidewalk_lf"),
            landscaping_area_sqft=d.get("landscaping_area_sqft"),
            notes=d.get("notes"),
            source_sheet_id=sheet_id,
        )
    except Exception:
        return None


def _build_extraction(sheet: Sheet, data: dict[str, Any]) -> SheetExtraction:
    sid = sheet.sheet_id
    return SheetExtraction(
        sheet_id=sid,
        summary=str(data.get("summary") or ""),
        rooms=[r for r in (_coerce_room(x, sid) for x in _safe_list(data, "rooms")) if r],
        doors=[d for d in (_coerce_door(x, sid) for x in _safe_list(data, "doors")) if d],
        windows=[w for w in (_coerce_window(x, sid) for x in _safe_list(data, "windows")) if w],
        structural=[s for s in (_coerce_structural(x, sid) for x in _safe_list(data, "structural")) if s],
        mep=[m for m in (_coerce_mep(x, sid) for x in _safe_list(data, "mep")) if m],
        spec_sections=[s for s in (_coerce_spec(x, sid) for x in _safe_list(data, "spec_sections")) if s],
        site=_coerce_site(_safe_dict(data, "site"), sid),
        raw_takeoffs=[t for t in (_coerce_takeoff(x, sid) for x in _safe_list(data, "raw_takeoffs")) if t],
        warnings=[str(w) for w in _safe_list(data, "warnings")],
    )


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def _select_prompt(sheet: Sheet) -> str:
    if sheet.sheet_type == SheetType.SCHEDULE:
        return "schedule"
    if sheet.sheet_type == SheetType.SPECIFICATION:
        return "specification"
    if sheet.sheet_type in {SheetType.SITE_PLAN}:
        return "site"

    if sheet.discipline in {Discipline.STRUCTURAL}:
        return "structural"
    if sheet.discipline in {Discipline.MECHANICAL, Discipline.ELECTRICAL,
                            Discipline.PLUMBING, Discipline.FIRE_PROTECTION}:
        return "mep"
    if sheet.discipline in {Discipline.CIVIL, Discipline.LANDSCAPE}:
        return "site"
    if sheet.discipline in {Discipline.ARCHITECTURAL, Discipline.INTERIORS}:
        return "architectural"

    if sheet.sheet_type in {
        SheetType.FLOOR_PLAN, SheetType.REFLECTED_CEILING, SheetType.ROOF_PLAN,
        SheetType.ELEVATION, SheetType.SECTION, SheetType.ENLARGED_PLAN,
    }:
        return "architectural"

    return "generic"


def _run_prepass(sheet: Sheet) -> _PrepassDC | None:
    """Run the deterministic pre-pass for a drawing sheet, if possible.

    Returns None when the source PDF can't be located on disk (e.g. tests
    that construct a `Sheet` without populating `pdf_path`).
    """
    if not sheet.pdf_path:
        return None
    pdf_path = Path(sheet.pdf_path)
    if not pdf_path.exists():
        logger.debug(
            "drawing-prepass: source PDF missing for %s (%s)",
            sheet.sheet_id, sheet.pdf_path,
        )
        return None
    try:
        return prepass_drawing_page(pdf_path, sheet.page_index)
    except Exception as exc:
        logger.warning(
            "drawing-prepass failed for %s page %d: %s",
            sheet.pdf_name, sheet.page_index + 1, exc,
        )
        return None


def _build_from_prepass(sheet: Sheet, prepass: _PrepassDC) -> SheetExtraction:
    """Build a `SheetExtraction` directly from a high-confidence prepass.

    Maps title-block fields into the summary, schedule rows into the
    appropriate door/window/room structures, and persists the full
    deterministic snapshot on the result for downstream debugging.
    """
    sid = sheet.sheet_id
    tb = prepass.title_block

    doors: list[DoorEntry] = []
    windows: list[WindowEntry] = []
    rooms: list[Room] = []

    for sched in prepass.schedules:
        if sched.kind == "door":
            for r in sched.rows:
                mark = _pick(r.columns, ("MARK", "DOOR", "NO", "NUMBER", "ID"))
                if not mark:
                    continue
                doors.append(DoorEntry(
                    mark=mark,
                    type=_pick(r.columns, ("TYPE",)),
                    hardware_set=_pick(r.columns, ("HARDWARE", "HARDWARE SET", "HW SET")),
                    rating=_pick(r.columns, ("RATING", "FIRE RATING")),
                    notes=_pick(r.columns, ("REMARKS", "NOTES")),
                    source_sheet_id=sid,
                ))
        elif sched.kind == "window":
            for r in sched.rows:
                mark = _pick(r.columns, ("MARK", "WINDOW", "NO", "NUMBER", "ID"))
                if not mark:
                    continue
                windows.append(WindowEntry(
                    mark=mark,
                    type=_pick(r.columns, ("TYPE",)),
                    glazing=_pick(r.columns, ("GLAZING", "GLASS")),
                    notes=_pick(r.columns, ("REMARKS", "NOTES")),
                    source_sheet_id=sid,
                ))
        elif sched.kind == "room":
            for r in sched.rows:
                name = _pick(r.columns, ("NAME", "ROOM", "ROOM NAME"))
                if not name:
                    continue
                rooms.append(Room(
                    name=name,
                    number=_pick(r.columns, ("NUMBER", "NO", "ROOM NO", "ROOM #")),
                    floor_finish=_pick(r.columns, ("FLOOR", "FLOOR FINISH")),
                    base_finish=_pick(r.columns, ("BASE",)),
                    wall_finish=_pick(r.columns, ("WALL", "WALLS")),
                    ceiling_finish=_pick(r.columns, ("CEILING",)),
                    source_sheet_id=sid,
                ))

    bits: list[str] = []
    if tb.discipline:
        bits.append(tb.discipline)
    if tb.sheet_number:
        bits.append(tb.sheet_number)
    if tb.sheet_title:
        bits.append(tb.sheet_title)
    elif sheet.title:
        bits.append(sheet.title)
    if tb.scale:
        bits.append(f"scale {tb.scale}")
    bits.append(
        f"{len(prepass.dimensions)} dimensions, {len(prepass.schedules)} "
        f"schedule table(s) extracted deterministically"
    )
    summary = " — ".join(b for b in bits if b)

    return SheetExtraction(
        sheet_id=sid,
        summary=summary,
        rooms=rooms,
        doors=doors,
        windows=windows,
        prepass=prepass_to_schema(prepass),
        lm_skipped=True,
        dimensions=list(_iter_dim_models(prepass.dimensions)),
    )


def _pick(cols: dict[str, str], candidates: tuple[str, ...]) -> str | None:
    """Look up a header by case-insensitive substring match."""
    if not cols:
        return None
    upper_cols = {k.upper(): v for k, v in cols.items() if k}
    for cand in candidates:
        cand_up = cand.upper()
        if cand_up in upper_cols and upper_cols[cand_up]:
            return upper_cols[cand_up]
        for key, val in upper_cols.items():
            if cand_up in key and val:
                return val
    return None


def _iter_dim_models(dims):
    from .extraction.drawing_prepass import iter_dimension_models
    return iter_dimension_models(dims)


def _format_prepass_context(prepass: _PrepassDC) -> str:
    """Render a compact 'deterministic context' block for the LLM prompt."""
    tb = prepass.title_block
    lines = ["DETERMINISTIC CONTEXT (pre-extracted from PDF vector text — trust these and focus on what's missing):"]
    fields = [
        ("Project name",   tb.project_name),
        ("Project number", tb.project_number),
        ("Sheet number",   tb.sheet_number),
        ("Sheet title",    tb.sheet_title),
        ("Discipline",     tb.discipline),
        ("Scale",          tb.scale),
        ("Date",           tb.date),
        ("Revision",       tb.revision),
    ]
    for label, val in fields:
        if val:
            lines.append(f"  {label}: {val}")
    if prepass.dimensions:
        lines.append(f"  Dimensions found: {len(prepass.dimensions)} (e.g. " +
                     ", ".join(d.raw_text for d in prepass.dimensions[:5]) + ")")
    if prepass.schedules:
        kinds = ", ".join(f"{s.kind}({len(s.rows)} rows)" for s in prepass.schedules)
        lines.append(f"  Schedule tables extracted: {kinds}")
    lines.append(f"  Pre-pass confidence: {prepass.confidence:.2f}")
    return "\n".join(lines)


def extract_sheet(sheet: Sheet, llm: LLMClient) -> SheetExtraction:
    """Run the right extractor for this sheet.

    F3 wires in a deterministic pre-pass that pulls the title block,
    dimensions, and schedule tables from the PDF's vector text. When the
    pre-pass clears `CONFIDENCE_THRESHOLD` we build a `SheetExtraction`
    directly from it and skip the vision-LLM call; otherwise the LLM
    runs as before but receives the pre-pass result as additional
    context.
    """
    if sheet.sheet_type in {SheetType.COVER, SheetType.INDEX, SheetType.GENERAL_NOTES}:
        # Cover / index pages have no quantities; skip the LLM call.
        return SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=f"{sheet.sheet_type.value if isinstance(sheet.sheet_type, str) else sheet.sheet_type} sheet - no takeoff",
        )

    prepass = _run_prepass(sheet)

    if prepass is not None and prepass.confidence >= CONFIDENCE_THRESHOLD:
        logger.info(
            "drawing-prepass hit page %d (confidence=%.2f, %s schedules, %s dimensions)",
            sheet.page_index + 1,
            prepass.confidence,
            len(prepass.schedules),
            len(prepass.dimensions),
        )
        return _build_from_prepass(sheet, prepass)

    # T10 F-3 (Layer 2). REFERENCE_PHOTO pages are dominated by a
    # large photograph + ``REFERENCE ONLY`` annotation; gpt-4o refuses
    # to analyse them. Skip the vision-LLM call entirely and return a
    # text-only extraction (the prepass already captured the title
    # block, any present schedules, and dimensions) so we don't burn
    # tokens on a guaranteed refusal.
    if prepass is not None and getattr(prepass, "is_reference_photo", False):
        logger.info(
            "REFERENCE_PHOTO page %d on sheet %s — skipping vision-LLM call",
            sheet.page_index + 1,
            sheet.sheet_id,
        )
        ex = SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=(
                f"REFERENCE_PHOTO sheet — vision-LLM analysis skipped "
                f"(page dominated by a REFERENCE ONLY photograph)."
            ),
            warnings=[
                f"REFERENCE_PHOTO: vision-LLM skipped on {sheet.sheet_id} "
                f"(prepass detected REFERENCE ONLY annotation + dominant image bbox)"
            ],
            lm_skipped=True,
        )
        ex.prepass = prepass_to_schema(prepass)
        ex.dimensions = list(_iter_dim_models(prepass.dimensions))
        return ex

    prompt_name = _select_prompt(sheet)
    user_prompt = load_prompt(prompt_name)

    extra_bits = [
        f"Sheet number: {sheet.sheet_number or 'unknown'}",
        f"Sheet title:  {sheet.title or 'unknown'}",
        f"Discipline:   {sheet.discipline}",
        f"Sheet type:   {sheet.sheet_type}",
        f"Scale:        {sheet.scale or 'unknown'}",
    ]
    if prepass is not None:
        extra_bits.append("")
        extra_bits.append(_format_prepass_context(prepass))
    extra_bits.append("")
    extra_bits.append("Embedded text excerpt (may help with text-heavy sheets):")
    extra_bits.append(sheet.embedded_text[:3000])
    extra = "\n".join(extra_bits)

    refusal_warnings: list[str] = []
    refused = False
    try:
        parsed, refused, refusal_warnings = _call_image_with_refusal_retry(
            llm,
            image_path=sheet.image_path,
            system_prompt=SYSTEM,
            user_prompt=user_prompt,
            extra_context=extra,
            sheet_id=sheet.sheet_id,
        )
        data = parsed if isinstance(parsed, dict) else {}
    except Exception as exc:
        logger.warning("Extractor failed for %s: %s", sheet.sheet_id, exc)
        ex = SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=f"Extraction failed: {exc}",
            warnings=[f"extractor error: {exc}"],
        )
        if prepass is not None:
            ex.prepass = prepass_to_schema(prepass)
        return ex

    if refused:
        ex = SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=(
                f"Vision-LLM refused on {sheet.sheet_id} after one retry; "
                f"sheet returned empty for human review."
            ),
            warnings=refusal_warnings,
            refused=True,
        )
        if prepass is not None:
            ex.prepass = prepass_to_schema(prepass)
            ex.dimensions = list(_iter_dim_models(prepass.dimensions))
        return ex

    extraction = _build_extraction(sheet, data)
    if refusal_warnings:
        extraction.warnings = list(extraction.warnings) + refusal_warnings
    if prepass is not None:
        extraction.prepass = prepass_to_schema(prepass)
        extraction.dimensions = list(_iter_dim_models(prepass.dimensions))
    return extraction


# ---------------------------------------------------------------------------
# Document-level (whole-PDF) extraction
# ---------------------------------------------------------------------------


def _truncate_for_text_call(text: str, char_budget: int = 60000) -> str:
    """Bid packages are small; project manuals can be longer. Keep under a
    reasonable token budget by truncating the middle.
    """
    if len(text) <= char_budget:
        return text
    keep = char_budget // 2
    head = text[:keep]
    tail = text[-keep:]
    omitted = len(text) - 2 * keep
    return f"{head}\n\n[... {omitted} chars truncated for length ...]\n\n{tail}"


def extract_bid_package(bundle: "DocumentBundle", llm: LLMClient) -> SheetExtraction:
    """Run the bid-package prompt on the whole PDF text in a single call.

    Calibration v3: cross-cutting reference docs (wage determinations,
    sample CSA templates, tax-exemption certificates, HSP forms, UGSC
    boilerplate) frequently arrive in the inbox alongside real trade
    packages. We run a cheap deterministic filename + first-page
    heuristic BEFORE the LLM call so the prompt can be seeded with a
    strong classification hint, and as a safety net we override
    `document_kind` when the heuristic strongly disagrees with the LLM.
    """
    user_prompt = load_prompt("bid_package")
    body = _truncate_for_text_call(bundle.full_text)

    supporting_hint = _supporting_doc_hint(bundle.pdf_name, bundle.full_text or "")
    hint_block = ""
    if supporting_hint:
        hint_block = (
            "\nCLASSIFICATION HINT (deterministic filename / first-page scan):\n"
            "This document strongly resembles a SUPPORTING DOCUMENT (wage\n"
            "determination, sample agreement, tax-exemption certificate,\n"
            "HSP template, UGSC, or similar) rather than a priced trade\n"
            "scope. Default to `document_kind: \"supporting_document\"`\n"
            "unless the body clearly describes a trade scope to price.\n"
        )

    extra = (
        f"Source PDF filename: {bundle.pdf_name}\n"
        f"Page count: {bundle.page_count}\n"
        f"{hint_block}"
        f"\nFULL DOCUMENT TEXT:\n{body}"
    )

    sheet_id = bundle.pdf_name
    try:
        resp = llm.analyze_text(system_prompt=SYSTEM, user_prompt=user_prompt + "\n\n" + extra)
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
    except Exception as exc:
        logger.warning("Bid-package extraction failed for %s: %s", bundle.pdf_name, exc)
        return SheetExtraction(
            sheet_id=sheet_id,
            summary=f"Bid-package extraction failed: {exc}",
            warnings=[f"bid_package extractor error: {exc}"],
        )

    # If the heuristic strongly says "supporting document" and the LLM
    # didn't already classify it as such, override. This cleans up the
    # pre-v3 behavior where Davis-Bacon wage tables landed with
    # `trade_name='other'` in the Bid Packages export.
    if supporting_hint and isinstance(data, dict):
        if data.get("document_kind") not in ("trade_package", "supporting_document"):
            data["document_kind"] = "supporting_document"
        elif data.get("document_kind") == "trade_package":
            # LLM disagreed with the heuristic. Trust the LLM only when the
            # body has enough scope-looking signals (inclusions, csi_sections,
            # unit_prices). Otherwise force supporting_document.
            scope_signals = (
                bool(_safe_list(data, "inclusions"))
                or bool(_safe_list(data, "csi_sections"))
                or bool(_safe_list(data, "unit_prices"))
            )
            if not scope_signals:
                data["document_kind"] = "supporting_document"

    bp = _coerce_bid_package(data, bundle.pdf_name)
    if bp is not None and not _bid_package_has_content(bp):
        bp = None
    summary = (bp.summary if bp and bp.summary else "") or str(data.get("summary") or "")

    # T10 v6 G-1 — drain the per-page deterministic + LLM-fallback path
    # into ``SheetExtraction.alternate_lines``. Single-shot LLM extraction
    # on the truncated whole-document body misses alternates pages that
    # land in the truncated middle (Carr EFA RFCSP p.42 is well past
    # the 60 KB head/tail window) and misses bare-``Option 001`` federal
    # SF18 layouts even when the page survives truncation; the per-page
    # path closes both gaps.
    alternate_lines = _extract_alternates_for_bundle(bundle, llm)

    return SheetExtraction(
        sheet_id=sheet_id,
        summary=summary,
        bid_package=bp,
        warnings=([str(w) for w in _safe_list(data, "warnings")] if isinstance(data, dict) else []),
        alternate_lines=alternate_lines,
    )


def extract_project_manual(bundle: "DocumentBundle", llm: LLMClient) -> SheetExtraction:
    """Brief summary + project-info pull for boilerplate text PDFs."""
    user_prompt = load_prompt("project_manual")
    body = _truncate_for_text_call(bundle.full_text, char_budget=40000)
    extra = f"Source PDF filename: {bundle.pdf_name}\nPage count: {bundle.page_count}\n\nFULL DOCUMENT TEXT:\n{body}"

    sheet_id = bundle.pdf_name
    try:
        resp = llm.analyze_text(system_prompt=SYSTEM, user_prompt=user_prompt + "\n\n" + extra)
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
    except Exception as exc:
        logger.warning("Project-manual extraction failed for %s: %s", bundle.pdf_name, exc)
        return SheetExtraction(
            sheet_id=sheet_id,
            summary=f"Manual summarization failed: {exc}",
            warnings=[f"project_manual extractor error: {exc}"],
        )

    summary_parts: list[str] = []
    if data.get("document_kind"):
        summary_parts.append(f"[{data['document_kind']}]")
    if data.get("summary"):
        summary_parts.append(str(data["summary"]))
    facts = data.get("key_facts") or []
    if isinstance(facts, list) and facts:
        summary_parts.append("Key facts: " + "; ".join(str(f) for f in facts[:6]))
    dates = data.get("key_dates") or []
    if isinstance(dates, list) and dates:
        summary_parts.append("Key dates: " + "; ".join(str(d) for d in dates[:4]))

    # Stash project info inside a synthetic BidPackage so reconcile can pick
    # it up uniformly. The project manual is a supporting reference doc, so
    # tag it as such — that keeps it out of the Trade Packages table.
    # `trade_name` is set to the LLM's `document_kind` label for backward
    # compatibility with the old `_consolidate_project_info` voting.
    owner = str(data["owner"]).strip() if data.get("owner") else None
    gc_val = str(data["gc"]).strip() if data.get("gc") else None
    legacy_contractor = str(data["contractor"]).strip() if data.get("contractor") else None
    if gc_val is None and legacy_contractor is not None:
        gc_val = legacy_contractor
    bp = BidPackage(
        pdf_name=bundle.pdf_name,
        trade_name=None,
        project_name=str(data["project_name"]) if data.get("project_name") else None,
        project_number=str(data["project_number"]) if data.get("project_number") else None,
        project_location=str(data["project_location"]) if data.get("project_location") else None,
        owner=owner,
        gc=gc_val,
        contractor=legacy_contractor,
        document_kind="supporting_document",
        summary=" ".join(summary_parts) if summary_parts else None,
    )

    return SheetExtraction(
        sheet_id=sheet_id,
        summary=" ".join(summary_parts) if summary_parts else "(no summary)",
        bid_package=bp,
        warnings=[str(w) for w in _safe_list(data, "warnings")] if isinstance(data, dict) else [],
    )


def extract_bid_form(bundle: "DocumentBundle", llm: LLMClient) -> SheetExtraction:
    """Run the bid-form prompt on a bid-schedule / price-schedule / HUB-plan PDF.

    Calibration v2 surfaced that the previous implementation short-circuited
    every BID_FORM PDF to a no-op stub. That swallowed the only document in
    the input set (the San Marcos Bid Schedule) that carried real unit-price
    line items. This extractor runs the same kind of one-shot text LLM call
    as `extract_bid_package`, but with a prompt focused on the schedule
    structure (unit prices, lump-sum lines, allowances) instead of the
    inclusion / exclusion narrative.

    Falls back to a clear WARNING-level skip stub when the document has
    essentially no text to send to the model (truly blank scanned form).
    """
    sheet_id = bundle.pdf_name

    body = (bundle.full_text or "").strip()
    if len(body) < 200:
        logger.warning(
            "extract_bid_form: %s has very little extractable text "
            "(%d chars); skipping LLM call.",
            bundle.pdf_name, len(body),
        )
        return SheetExtraction(
            sheet_id=sheet_id,
            summary="Bid form skipped: insufficient extractable text.",
            warnings=[
                f"bid_form skip: {bundle.pdf_name} had only {len(body)} chars of text "
                "(probably a scanned blank form)."
            ],
        )

    user_prompt = load_prompt("bid_form")
    body_trunc = _truncate_for_text_call(body)
    extra = (
        f"Source PDF filename: {bundle.pdf_name}\n"
        f"Page count: {bundle.page_count}\n\n"
        f"FULL DOCUMENT TEXT:\n{body_trunc}"
    )

    try:
        resp = llm.analyze_text(system_prompt=SYSTEM, user_prompt=user_prompt + "\n\n" + extra)
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
    except Exception as exc:
        logger.warning("Bid-form extraction failed for %s: %s", bundle.pdf_name, exc)
        return SheetExtraction(
            sheet_id=sheet_id,
            summary=f"Bid-form extraction failed: {exc}",
            warnings=[f"bid_form extractor error: {exc}"],
        )

    bp = _coerce_bid_package(data, bundle.pdf_name)
    if bp is not None and not bp.trade_name:
        # Default trade label so the Bid Packages sheet shows where it came from.
        bp = bp.model_copy(update={"trade_name": "Bid Form"})

    summary = (bp.summary if bp and bp.summary else "") or str(data.get("summary") or "")

    # T10 v6 G-1 — see the matching comment in :func:`extract_bid_package`.
    alternate_lines = _extract_alternates_for_bundle(bundle, llm)

    return SheetExtraction(
        sheet_id=sheet_id,
        summary=summary or f"Bid form extracted ({len(bp.unit_prices) if bp else 0} unit-price lines).",
        bid_package=bp,
        warnings=([str(w) for w in _safe_list(data, "warnings")] if isinstance(data, dict) else []),
        alternate_lines=alternate_lines,
    )


# ---------------------------------------------------------------------------
# Phase T9.0 — bid-alternates LLM-fallback extraction
# ---------------------------------------------------------------------------
#
# Companion to the deterministic regex parser in
# :mod:`core.extraction.bid_form_alternates`. Invoked only when the
# deterministic path returns zero alternates AND the page detector
# said the page contains alternates wording — see
# :func:`core.extraction.bid_form_alternates.should_invoke_llm_fallback`
# for the predicate.
#
# The prompt is the same `bid_form.txt` that backs :func:`extract_bid_form`
# (extended in T9.0 with explicit alternates-extraction guidance). We
# re-use the prompt rather than authoring a second one so the
# extracted alternates shape stays in lock-step with the bid-package
# extraction surface — operators see one consistent contract.


def _coerce_alternate_line(d: dict, *, bid_package_id: str | None, source_sheet: str | None) -> AlternateLine | None:
    """Build an :class:`AlternateLine` from a permissive dict.

    Tolerates either the new T9.0 keys (``alternate_id`` /
    ``alternate_type`` / ``cost_delta``) or the legacy keys the
    `bid_form.txt` prompt has emitted since calibration v1 (``number``
    / ``add_or_deduct`` / ``amount``). The latter is the common case
    today — the prompt extension is additive but the LLM occasionally
    emits the older shape because of cache.

    Returns ``None`` on a malformed dict so the caller can keep walking
    the list without per-row error handling.
    """
    from .extraction.bid_form_alternates import (
        classify_alternate_type,
        _apply_type_sign,
    )

    if not isinstance(d, dict):
        return None
    desc_raw = d.get("description") or d.get("scope_summary") or ""
    desc = str(desc_raw).strip()
    if not desc:
        return None

    raw_id = (
        str(d.get("alternate_id") or "").strip()
        or str(d.get("number") or "").strip()
    )
    if not raw_id:
        return None
    if not raw_id.lower().startswith(("alt", "ve", "bid alternate", "add alternate", "deduct alternate")):
        alt_id = f"Alternate {raw_id.lstrip('#').strip()}"
    else:
        alt_id = raw_id

    # alternate_type: prefer explicit string, else derive from add_or_deduct
    # label, else classify from the description body.
    type_raw = str(d.get("alternate_type") or "").strip().lower()
    atype: AlternateType
    if type_raw in {t.value for t in AlternateType}:
        atype = AlternateType(type_raw)
    else:
        label = str(d.get("add_or_deduct") or "").lower()
        if "deduct" in label:
            atype = AlternateType.DEDUCTIVE
        elif "add" in label or "additive" in label:
            atype = AlternateType.ADDITIVE
        elif "substitut" in label:
            atype = AlternateType.SUBSTITUTION
        elif "ve" in label or "value engineering" in label:
            atype = AlternateType.VE
        else:
            atype = classify_alternate_type(desc)

    raw_cost = d.get("cost_delta")
    if raw_cost is None:
        raw_cost = d.get("amount")
    try:
        cost_val: float | None = (
            float(raw_cost) if raw_cost not in (None, "", "null") else None
        )
    except (TypeError, ValueError):
        cost_val = None

    # The prompt emits magnitudes for DEDUCT alternates; apply the sign
    # convention here so the AlternateLine carries a signed delta.
    if cost_val is not None and "cost_delta" not in d:
        # Legacy key path — magnitude needs signing.
        cost_val = _apply_type_sign(cost_val, atype)

    confidence_raw = d.get("confidence")
    try:
        conf = (
            min(1.0, max(0.0, float(confidence_raw)))
            if confidence_raw is not None
            else 0.70
        )
    except (TypeError, ValueError):
        conf = 0.70

    return AlternateLine(
        alternate_id=alt_id,
        alternate_type=atype,
        description=desc,
        scope_summary=str(d.get("scope_summary") or desc[:160]).strip() or desc,
        cost_delta=cost_val,
        included_by_default=bool(d.get("included_by_default", False)),
        bid_package_id=bid_package_id,
        source_sheet=source_sheet,
        confidence=conf,
    )


def extract_alternates_via_llm(
    page_text: str,
    llm: LLMClient,
    *,
    bid_package_id: str | None = None,
    source_sheet: str | None = None,
) -> list[AlternateLine]:
    """LLM fallback for bid-alternates extraction (Phase T9.0).

    Invoked by callers when the deterministic regex parser in
    :func:`core.extraction.bid_form_alternates.extract_alternates_from_page`
    returns an empty list but
    :func:`core.extraction.bid_form_alternates.detect_alternates_section`
    indicates the page does carry alternates wording.

    Re-uses the `bid_form.txt` prompt (which T9.0 extended with
    explicit alternates-extraction guidance) — same JSON contract as
    the full bid-form path, but we read only the ``alternates`` field
    of the response. Confidence is clamped to a 0.70 ceiling because
    the LLM-fallback path runs only when the deterministic path
    couldn't parse the wording; the model is guessing on an
    intentionally unusual layout.

    Returns an empty list on LLM error rather than raising — the
    caller has the deterministic result available and can proceed
    without the fallback's contribution. Errors are logged.
    """
    if not page_text or len(page_text.strip()) < 30:
        return []
    try:
        user_prompt = load_prompt("bid_form")
    except Exception as exc:
        logger.warning("extract_alternates_via_llm: failed to load prompt (%s)", exc)
        return []
    extra = (
        f"Source page text (alternates section excerpt):\n{page_text}"
    )
    try:
        resp = llm.analyze_text(
            system_prompt=SYSTEM,
            user_prompt=user_prompt + "\n\n" + extra,
        )
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
    except Exception as exc:
        logger.warning("extract_alternates_via_llm: LLM call failed (%s)", exc)
        return []

    raw_alts = _safe_list(data, "alternates")
    out: list[AlternateLine] = []
    for d in raw_alts:
        line = _coerce_alternate_line(
            d if isinstance(d, dict) else {},
            bid_package_id=bid_package_id,
            source_sheet=source_sheet,
        )
        if line is not None:
            # Cap LLM-fallback confidence at 0.70 — this path runs only
            # when the deterministic parser missed, so the model is
            # working on an unusual layout where a reviewer should
            # confirm the result before it lands in any total.
            if line.confidence > 0.70:
                line = line.model_copy(update={"confidence": 0.70})
            out.append(line)
    return out


_BUNDLE_LLM_FALLBACK_CAP: int = 3
"""T10 v6 G-1 — cap on LLM-fallback invocations per bundle.

``extract_alternates_via_llm`` runs only on pages where the section
detector fired AND the deterministic regex returned zero alternates.
Even with that gate the marginal cost is bounded per-page; this cap
provides a hard ceiling per bundle so a pathological document with
many alternates-styled section headers cannot run away with cost.
Three covers every observed real-world case (the worst RFCSP in the
v5a corpus had 5 section-detector hits and 1 zero-deterministic hit).
"""


def _extract_alternates_for_bundle(
    bundle: "DocumentBundle", llm: LLMClient
) -> list[AlternateLine]:
    """T10 v6 G-1 — per-page deterministic + LLM-fallback alternates extraction.

    Walks every page of the bundle's source PDF via ``fitz``, runs the
    deterministic regex parser
    (:func:`core.extraction.bid_form_alternates.extract_alternates_from_page`)
    on each page, and gates the LLM fallback
    (:func:`extract_alternates_via_llm`) via
    :func:`core.extraction.bid_form_alternates.should_invoke_llm_fallback`
    capped at :data:`_BUNDLE_LLM_FALLBACK_CAP` invocations per bundle.

    Per-page deterministic + LLM-fallback results are merged via
    :func:`core.extraction.bid_form_alternates.reconcile_alternate_sources`,
    then the per-page lists are concatenated into a single bundle-level
    list. Returns ``[]`` on any I/O or parsing error — alternates are
    additive, never failure-critical.

    This is the wiring closure for G-1: the deterministic +
    LLM-fallback extractor module was implemented and unit-tested at
    HEAD ``9ad21a8`` but had **zero call sites** in
    :func:`extract_bundle` / :func:`extract_bid_package` /
    :func:`extract_bid_form`, so the calibration v5a output showed
    0 alternates across 25 bundles despite the unit tests being
    green. See ``exports/calibration_v5/G1_INVESTIGATION.md``.
    """
    from .extraction.bid_form_alternates import (
        extract_alternates_from_page,
        reconcile_alternate_sources,
        should_invoke_llm_fallback,
    )

    try:
        import fitz  # PyMuPDF
    except Exception as exc:  # pragma: no cover - fitz is a hard dep elsewhere
        logger.warning(
            "_extract_alternates_for_bundle(%s): fitz unavailable (%s); skipping.",
            bundle.pdf_name, exc,
        )
        return []

    try:
        doc = fitz.open(bundle.pdf_path)
    except Exception as exc:
        logger.warning(
            "_extract_alternates_for_bundle(%s): fitz.open failed (%s); skipping.",
            bundle.pdf_name, exc,
        )
        return []

    out: list[AlternateLine] = []
    llm_calls = 0
    try:
        for i, page in enumerate(doc):
            try:
                page_text = page.get_text("text") or ""
            except Exception:
                continue
            if not page_text.strip():
                continue

            det = extract_alternates_from_page(
                page_text,
                bid_package_id=bundle.pdf_name,
                source_sheet=f"{bundle.pdf_name} p.{i + 1}",
            )

            llm_extracted: list[AlternateLine] = []
            if (
                llm_calls < _BUNDLE_LLM_FALLBACK_CAP
                and should_invoke_llm_fallback(page_text, det)
            ):
                llm_calls += 1
                llm_extracted = extract_alternates_via_llm(
                    page_text,
                    llm,
                    bid_package_id=bundle.pdf_name,
                    source_sheet=f"{bundle.pdf_name} p.{i + 1}",
                )

            if not det and not llm_extracted:
                continue
            merged = reconcile_alternate_sources(det, llm_extracted)
            out.extend(merged)
    finally:
        try:
            doc.close()
        except Exception:
            pass

    return out


def extract_bundle(bundle: "DocumentBundle", llm: LLMClient) -> SheetExtraction:
    """Dispatch a `DocumentBundle` (whole-PDF text) to the right extractor."""
    if bundle.sheet_type == SheetType.BID_PACKAGE:
        return extract_bid_package(bundle, llm)
    if bundle.sheet_type == SheetType.PROJECT_MANUAL:
        return extract_project_manual(bundle, llm)
    if bundle.sheet_type == SheetType.BID_FORM:
        return extract_bid_form(bundle, llm)
    # Fallback: project-manual style summary
    return extract_project_manual(bundle, llm)
