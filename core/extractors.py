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

    try:
        resp = llm.analyze_image(
            image_path=sheet.image_path,
            system_prompt=SYSTEM,
            user_prompt=user_prompt,
            extra_context=extra,
        )
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
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

    extraction = _build_extraction(sheet, data)
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
    summary = (bp.summary if bp and bp.summary else "") or str(data.get("summary") or "")
    return SheetExtraction(
        sheet_id=sheet_id,
        summary=summary,
        bid_package=bp,
        warnings=([str(w) for w in _safe_list(data, "warnings")] if isinstance(data, dict) else []),
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
    return SheetExtraction(
        sheet_id=sheet_id,
        summary=summary or f"Bid form extracted ({len(bp.unit_prices) if bp else 0} unit-price lines).",
        bid_package=bp,
        warnings=([str(w) for w in _safe_list(data, "warnings")] if isinstance(data, dict) else []),
    )


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
