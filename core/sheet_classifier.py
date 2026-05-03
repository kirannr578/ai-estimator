"""Decide each sheet's discipline and sheet type.

Two-stage strategy:
  1. *Cheap path*: title-block heuristics already done in `pdf_processor` give
     us a sheet number + discipline guess from the embedded text. If that's
     populated AND the title contains an obvious sheet-type keyword, we're
     done -- no LLM call needed.
  2. *Vision path*: otherwise call the LLM with the rendered image and the
     classifier prompt.

Either way the result is written back into the `Sheet` in place.
"""

from __future__ import annotations

import logging
from typing import Optional

from prompts import load as load_prompt

from .llm_client import LLMClient
from .schemas import Discipline, Sheet, SheetType

logger = logging.getLogger(__name__)


_TYPE_KEYWORDS: list[tuple[str, SheetType]] = [
    ("REFLECTED CEILING", SheetType.REFLECTED_CEILING),
    ("ROOF PLAN",         SheetType.ROOF_PLAN),
    ("SITE PLAN",         SheetType.SITE_PLAN),
    ("DEMOLITION",        SheetType.DEMOLITION),
    ("FOUNDATION PLAN",   SheetType.FOUNDATION_PLAN),
    ("FRAMING PLAN",      SheetType.FRAMING_PLAN),
    ("MECHANICAL PLAN",   SheetType.MECHANICAL_PLAN),
    ("ELECTRICAL PLAN",   SheetType.ELECTRICAL_PLAN),
    ("PLUMBING PLAN",     SheetType.PLUMBING_PLAN),
    ("STRUCTURAL PLAN",   SheetType.STRUCTURAL_PLAN),
    ("RISER",             SheetType.RISER_DIAGRAM),
    ("SINGLE LINE",       SheetType.SINGLE_LINE_DIAGRAM),
    ("ELEVATION",         SheetType.ELEVATION),
    ("SECTION",           SheetType.SECTION),
    ("ENLARGED",          SheetType.ENLARGED_PLAN),
    ("DETAIL",            SheetType.DETAIL),
    ("SCHEDULE",          SheetType.SCHEDULE),
    ("SPECIFICATION",     SheetType.SPECIFICATION),
    ("GENERAL NOTES",     SheetType.GENERAL_NOTES),
    ("INDEX",             SheetType.INDEX),
    ("COVER",             SheetType.COVER),
    ("FLOOR PLAN",        SheetType.FLOOR_PLAN),
]


def _heuristic_classify(sheet: Sheet) -> Optional[SheetType]:
    haystack = " ".join(filter(None, [sheet.title or "", sheet.embedded_text[:500] or ""])).upper()
    for keyword, stype in _TYPE_KEYWORDS:
        if keyword in haystack:
            return stype
    return None


def classify_sheet(sheet: Sheet, llm: LLMClient) -> Sheet:
    """Fill `discipline`, `sheet_type`, and improve title/sheet_number/scale."""
    # --- Stage 1: cheap heuristics ---
    if sheet.discipline != Discipline.UNKNOWN:
        guessed_type = _heuristic_classify(sheet)
        if guessed_type is not None:
            sheet.sheet_type = guessed_type
            return sheet

    # --- Stage 2: vision LLM ---
    system = "You return ONLY JSON. No prose, no markdown fences."
    user = load_prompt("classifier")

    try:
        resp = llm.analyze_image(
            image_path=sheet.image_path,
            system_prompt=system,
            user_prompt=user,
            extra_context=(
                f"Embedded text from this page (may be empty for scanned plans):\n"
                f"{sheet.embedded_text[:1500]}"
            ),
        )
        data = resp.parsed if isinstance(resp.parsed, dict) else {}
    except Exception as exc:
        logger.warning("Classifier LLM call failed for %s: %s", sheet.sheet_id, exc)
        return sheet

    # Discipline
    disc_raw = (data.get("discipline") or "").strip().upper()
    try:
        sheet.discipline = Discipline(disc_raw) if disc_raw else sheet.discipline
    except ValueError:
        pass

    # Sheet type
    stype_raw = (data.get("sheet_type") or "").strip().lower()
    try:
        sheet.sheet_type = SheetType(stype_raw) if stype_raw else sheet.sheet_type
    except ValueError:
        sheet.sheet_type = SheetType.UNKNOWN

    # Optional fields - only overwrite if we don't already have them.
    if not sheet.sheet_number and data.get("sheet_number"):
        sheet.sheet_number = str(data["sheet_number"])
    if not sheet.title and data.get("title"):
        sheet.title = str(data["title"])
    if data.get("scale"):
        sheet.scale = str(data["scale"])

    return sheet
