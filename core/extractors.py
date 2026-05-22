"""Discipline-specific extractors.

Each extractor takes a `Sheet` plus the shared `LLMClient` and returns a
`SheetExtraction`. The `extract_sheet` dispatcher routes the sheet to the
right extractor based on its classified `discipline` + `sheet_type`.
"""

from __future__ import annotations

import logging
from typing import Any

from prompts import load as load_prompt

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

    try:
        return BidPackage(
            pdf_name=pdf_name,
            package_number=str(data["package_number"]) if data.get("package_number") else None,
            trade_name=str(data["trade_name"]) if data.get("trade_name") else None,
            project_name=str(data["project_name"]) if data.get("project_name") else None,
            project_number=str(data["project_number"]) if data.get("project_number") else None,
            project_location=str(data["project_location"]) if data.get("project_location") else None,
            bid_due=str(data["bid_due"]) if data.get("bid_due") else None,
            contractor=str(data["contractor"]) if data.get("contractor") else None,
            contact=str(data["contact"]) if data.get("contact") else None,
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


def extract_sheet(sheet: Sheet, llm: LLMClient) -> SheetExtraction:
    """Run the right extractor for this sheet."""
    if sheet.sheet_type in {SheetType.COVER, SheetType.INDEX, SheetType.GENERAL_NOTES}:
        # Cover / index pages have no quantities; skip the LLM call.
        return SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=f"{sheet.sheet_type.value if isinstance(sheet.sheet_type, str) else sheet.sheet_type} sheet - no takeoff",
        )

    prompt_name = _select_prompt(sheet)
    user_prompt = load_prompt(prompt_name)

    extra = (
        f"Sheet number: {sheet.sheet_number or 'unknown'}\n"
        f"Sheet title:  {sheet.title or 'unknown'}\n"
        f"Discipline:   {sheet.discipline}\n"
        f"Sheet type:   {sheet.sheet_type}\n"
        f"Scale:        {sheet.scale or 'unknown'}\n"
        f"\nEmbedded text excerpt (may help with text-heavy sheets):\n"
        f"{sheet.embedded_text[:3000]}"
    )

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
        return SheetExtraction(
            sheet_id=sheet.sheet_id,
            summary=f"Extraction failed: {exc}",
            warnings=[f"extractor error: {exc}"],
        )

    return _build_extraction(sheet, data)


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
    """Run the bid-package prompt on the whole PDF text in a single call."""
    user_prompt = load_prompt("bid_package")
    body = _truncate_for_text_call(bundle.full_text)
    extra = f"Source PDF filename: {bundle.pdf_name}\nPage count: {bundle.page_count}\n\nFULL DOCUMENT TEXT:\n{body}"

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
    # it up uniformly. trade_name == "Project Manual" makes it skippable in
    # the scope matrix.
    bp = BidPackage(
        pdf_name=bundle.pdf_name,
        trade_name=str(data["document_kind"]) if data.get("document_kind") else "project manual",
        project_name=str(data["project_name"]) if data.get("project_name") else None,
        project_number=str(data["project_number"]) if data.get("project_number") else None,
        project_location=str(data["project_location"]) if data.get("project_location") else None,
        contractor=str(data["contractor"]) if data.get("contractor") else None,
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
