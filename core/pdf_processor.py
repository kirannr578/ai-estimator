"""Turn raw PDF bytes into a list of `Sheet` objects.

For each page we:
  * extract the embedded vector text (titles, notes, schedules)
  * render a high-DPI PNG that the vision LLM will consume
  * record dimensions, scanned-vs-vector heuristic and basic title-block guesses

We also detect "document-level" PDFs (bid packages, project manuals, blank bid
forms) up front - those are processed as a single unit by the bid-package
extractor rather than page-by-page with vision.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

from .schemas import Discipline, Sheet, SheetType


# Sheet-number regex covers most US conventions:
#   A-101, A101, A1.01, S-2.1, MP-301, FP1-01, etc.
SHEET_NUMBER_RE = re.compile(
    r"\b([A-Z]{1,3})[-]?(\d{1,3}(?:\.\d{1,2})?)\b"
)

DISCIPLINE_PREFIX = {
    "A":   Discipline.ARCHITECTURAL,
    "AD":  Discipline.ARCHITECTURAL,
    "AS":  Discipline.ARCHITECTURAL,
    "I":   Discipline.INTERIORS,
    "ID":  Discipline.INTERIORS,
    "S":   Discipline.STRUCTURAL,
    "SD":  Discipline.STRUCTURAL,
    "M":   Discipline.MECHANICAL,
    "MD":  Discipline.MECHANICAL,
    "MP":  Discipline.MECHANICAL,
    "E":   Discipline.ELECTRICAL,
    "ED":  Discipline.ELECTRICAL,
    "P":   Discipline.PLUMBING,
    "PD":  Discipline.PLUMBING,
    "FP":  Discipline.FIRE_PROTECTION,
    "F":   Discipline.FIRE_PROTECTION,
    "C":   Discipline.CIVIL,
    "CD":  Discipline.CIVIL,
    "L":   Discipline.LANDSCAPE,
    "LS":  Discipline.LANDSCAPE,
    "G":   Discipline.GENERAL,
    "T":   Discipline.GENERAL,
}


def _guess_sheet_number_and_discipline(text: str) -> tuple[str | None, Discipline]:
    """Heuristically pull a sheet number and discipline out of the page text.

    Title blocks tend to have the sheet number in the bottom-right; the regex
    is loose so this works whether the bid set follows AIA, NCS or office
    standards. We pick the *last* match because title blocks are usually at
    the end of the text-extraction order.
    """
    if not text:
        return None, Discipline.UNKNOWN

    candidates = SHEET_NUMBER_RE.findall(text)
    if not candidates:
        return None, Discipline.UNKNOWN

    # Prefer matches that look like real sheet numbers (have a hyphen or dot
    # in the original text). Fall back to the last bare candidate.
    best_prefix, best_num = candidates[-1]
    sheet_number = f"{best_prefix}-{best_num}" if "-" not in best_num else f"{best_prefix}{best_num}"

    discipline = DISCIPLINE_PREFIX.get(best_prefix.upper(), Discipline.UNKNOWN)
    return sheet_number, discipline


def _guess_title(text: str) -> str | None:
    """Pull a one-line title from common title-block phrases."""
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    keywords = (
        "FLOOR PLAN", "ROOF PLAN", "SITE PLAN", "FOUNDATION PLAN",
        "FRAMING PLAN", "REFLECTED CEILING", "ELEVATION", "SECTION",
        "SCHEDULE", "DETAIL", "ENLARGED PLAN", "DEMOLITION",
        "ELECTRICAL PLAN", "MECHANICAL PLAN", "PLUMBING PLAN",
        "RISER DIAGRAM", "SINGLE LINE",
    )
    for ln in lines:
        upper = ln.upper()
        if any(k in upper for k in keywords) and len(ln) < 80:
            return ln
    return None


@dataclass
class DocumentBundle:
    """A PDF that's been classified as a single document (e.g. a bid package).

    Carries the full text and a thumbnail (page 1) but no per-page sheets.
    """

    pdf_name: str
    pdf_path: str
    sheet_type: SheetType
    full_text: str
    page_count: int
    thumbnail_path: str
    title_hint: str | None = None


# --- Document-level classification ------------------------------------------

_BID_PACKAGE_HINTS = (
    "BID PACKAGE",
    "GENERAL INSTRUCTIONS TO BIDDERS",
    "SPECIFIC INSTRUCTIONS TO BIDDERS",
    "SPECIFIC INCLUSIONS",
    "SPECIFIC EXCLUSIONS",
)
_BID_FORM_HINTS = ("BLANK BID FORM", "BID FORM TEMPLATE")
# Bid-package filenames almost always start with "NN.NN_-_..."
_BID_PACKAGE_FILENAME_RE = re.compile(r"^\d{2}[.\-]\d{2}[\s_\-]")


_PROJECT_MANUAL_HINTS = (
    "GENERAL INSTRUCTIONS TO BIDDERS",
    "QUESTIONNAIRE",
    "PROJECT REQUIREMENTS",
    "EXHIBIT",
    "TABLE OF CONTENTS",
    "INVITATION TO BID",
)


def _classify_document(
    pdf_name: str,
    text: str,
    page_count: int,
    avg_chars_per_page: float,
) -> SheetType:
    """Heuristically decide whether a whole PDF should be treated as a single
    text document (bid package / form / manual) instead of split per-page for
    vision analysis.
    """
    upper = text.upper()
    name_upper = pdf_name.upper()

    if "BLANK BID FORM" in name_upper or any(h in upper for h in _BID_FORM_HINTS):
        return SheetType.BID_FORM

    # Bid package: filename pattern OR multiple structural hints
    bid_hits = sum(1 for h in _BID_PACKAGE_HINTS if h in upper)
    if bid_hits >= 2 or _BID_PACKAGE_FILENAME_RE.match(pdf_name):
        return SheetType.BID_PACKAGE

    # Project manual / boilerplate text: text-heavy, modest page count, hits
    # on at least one project-manual phrase.
    pm_hits = sum(1 for h in _PROJECT_MANUAL_HINTS if h in upper)
    if pm_hits >= 1 and page_count <= 30 and avg_chars_per_page > 600:
        return SheetType.PROJECT_MANUAL

    # Tiny brochure / flyer (1-3 pages, mostly text)
    if page_count <= 3 and avg_chars_per_page > 400:
        return SheetType.PROJECT_MANUAL

    return SheetType.UNKNOWN


def _read_full_text(doc: fitz.Document, max_pages: int = 60) -> str:
    """Concatenate text across pages with simple page markers."""
    chunks: list[str] = []
    for i, page in enumerate(doc):
        if i >= max_pages:
            chunks.append(f"\n[... {len(doc) - i} additional pages truncated ...]")
            break
        chunks.append(f"\n--- PAGE {i + 1} ---\n")
        chunks.append(page.get_text("text") or "")
    return "".join(chunks)


def process_pdfs(
    pdf_paths: Iterable[str | os.PathLike],
    cache_dir: str | os.PathLike,
    dpi: int = 200,
    document_level_types: tuple[SheetType, ...] = (
        SheetType.BID_PACKAGE,
        SheetType.BID_FORM,
        SheetType.PROJECT_MANUAL,
    ),
) -> tuple[list[Sheet], list[DocumentBundle]]:
    """Split every PDF into sheets and render them.

    Returns:
        ``(sheets, document_bundles)``.

        * ``sheets``           - drawing-style PDFs split into per-page sheets
                                 (each with a rendered PNG) for vision analysis.
        * ``document_bundles`` - text-heavy PDFs (bid packages etc.) treated as
                                 a single unit; carries full text + thumbnail.
    """
    cache_dir = Path(cache_dir)
    cache_dir.mkdir(parents=True, exist_ok=True)

    zoom = dpi / 72.0
    matrix = fitz.Matrix(zoom, zoom)
    thumb_matrix = fitz.Matrix(120 / 72.0, 120 / 72.0)  # cheap thumbnails

    sheets: list[Sheet] = []
    bundles: list[DocumentBundle] = []

    for pdf_path in pdf_paths:
        pdf_path = Path(pdf_path)
        if pdf_path.name.upper().startswith("DO_NOT_USE"):
            continue

        with fitz.open(pdf_path) as doc:
            page_count = len(doc)
            # --- Step 1: cheap doc-level classification using first 3 pages text ---
            first_text = "".join(
                (doc[i].get_text("text") or "") for i in range(min(3, page_count))
            )
            avg_chars = (len(first_text) / max(min(3, page_count), 1))
            doc_type = _classify_document(pdf_path.name, first_text, page_count, avg_chars)

            if doc_type in document_level_types:
                full_text = _read_full_text(doc)
                thumb_name = f"{pdf_path.stem}__thumb.png"
                thumb_path = cache_dir / thumb_name
                doc[0].get_pixmap(matrix=thumb_matrix, alpha=False).save(thumb_path)
                bundles.append(DocumentBundle(
                    pdf_name=pdf_path.name,
                    pdf_path=str(pdf_path),
                    sheet_type=doc_type,
                    full_text=full_text,
                    page_count=len(doc),
                    thumbnail_path=str(thumb_path),
                    title_hint=_guess_title(first_text),
                ))
                continue

            # --- Step 2: drawing PDFs - render each page as a Sheet ---
            for page_index, page in enumerate(doc):
                embedded_text = page.get_text("text") or ""
                is_scanned = len(embedded_text.strip()) < 20

                sheet_number, discipline = _guess_sheet_number_and_discipline(embedded_text)
                title = _guess_title(embedded_text)

                image_name = f"{pdf_path.stem}__p{page_index + 1:03d}.png"
                image_path = cache_dir / image_name
                pix = page.get_pixmap(matrix=matrix, alpha=False)
                pix.save(image_path)

                sheets.append(Sheet(
                    pdf_name=pdf_path.name,
                    page_index=page_index,
                    sheet_number=sheet_number,
                    title=title,
                    discipline=discipline,
                    sheet_type=SheetType.UNKNOWN,
                    width_pts=float(page.rect.width),
                    height_pts=float(page.rect.height),
                    image_path=str(image_path),
                    embedded_text=embedded_text,
                    is_scanned=is_scanned,
                ))

    return sheets, bundles
