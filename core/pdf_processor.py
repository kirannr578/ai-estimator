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

import hashlib
import logging
import os
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import fitz  # PyMuPDF

from .schemas import Discipline, Sheet, SheetType


logger = logging.getLogger(__name__)


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
#
# This gate decides whether a PDF goes through the text/bundle path (one LLM
# call per doc) or the per-page sheet path (one LLM call per page). Misrouting
# a government solicitation into the sheet path inflates LLM cost ~35x AND
# silently skips bid-package extraction. The hint sets below cover both the
# original trade-specific bid packages (DISD-style "NN.NN_-_Trade.pdf") and
# government-RFP / SAM.gov / TX-ESBD solicitations that are the dominant
# real-world input.

_BID_PACKAGE_HINTS = (
    "BID PACKAGE",
    "GENERAL INSTRUCTIONS TO BIDDERS",
    "SPECIFIC INSTRUCTIONS TO BIDDERS",
    "SPECIFIC INCLUSIONS",
    "SPECIFIC EXCLUSIONS",
)

# Government / federal / state-procurement RFP language. Any single hit is a
# strong "this is a solicitation, not a drawing" signal; two hits lock it in
# even without filename evidence.
_GOV_RFP_HINTS = (
    "REQUEST FOR PROPOSALS",
    "REQUEST FOR PROPOSAL",
    "REQUEST FOR QUOTATIONS",
    "REQUEST FOR QUOTATION",
    "REQUEST FOR QUOTE",
    "REQUEST FOR COMPETITIVE SEALED PROPOSAL",
    "RFCSP",
    "SOLICITATION NUMBER",
    "SOLICITATION NO.",
    "SOLICITATION NO ",
    "OFFEROR",
    "OFFERORS",
    "CONTRACTING OFFICER",
    "SECTION L",
    "SECTION M",
    "STATEMENT OF WORK",
    "SCOPE OF WORK",
    "SAM.GOV",
    "BETA.SAM.GOV",
    "ELECTRONIC STATE BUSINESS DAILY",
    "ESBD",
    "SF 1442",
    "SF-1442",
    "STANDARD FORM 1442",
    "SF 33",
    "SF-33",
    "STANDARD FORM 33",
    "PERIOD OF PERFORMANCE",
    "MAGNITUDE OF CONSTRUCTION",
    "PROJECT MAGNITUDE",
    "NOTICE TO PROCEED",
)

_BID_FORM_HINTS = (
    "BLANK BID FORM",
    "BID FORM TEMPLATE",
    "BID SCHEDULE",
    "BID PROPOSAL FORM",
    "PRICE SCHEDULE",
    "PROPOSAL FORM",
    "HUB SUBCONTRACTING PLAN",
    "HSP GOOD FAITH EFFORT",
)

# Trade-specific bid-package filenames (legacy DISD/Beck convention).
_BID_PACKAGE_FILENAME_RE = re.compile(r"^\d{2}[.\-]\d{2}[\s_\-]")

# Government-solicitation filename signals. Any single match routes the doc
# straight to BID_PACKAGE — these prefixes/tokens are unambiguous in practice
# (SAM.gov uses "Sol_<number>", TX-ESBD prefixes attachments with "ESBD_",
# RFCSP and SOW appear in nothing but solicitations).
_GOV_BID_PACKAGE_FILENAME_RES = (
    re.compile(r"^Sol[_\-]", re.IGNORECASE),
    re.compile(r"^ESBD[_\-]\d+", re.IGNORECASE),
    re.compile(r"\bRFCSP\b", re.IGNORECASE),
    re.compile(r"\bRFP\b", re.IGNORECASE),
    re.compile(r"^SOW[_\-]", re.IGNORECASE),
    re.compile(r"_Solicitation_", re.IGNORECASE),
    re.compile(r"Notice[_\- ]of[_\- ]Project", re.IGNORECASE),
)

# Blank bid / pricing-schedule / HUB-plan filenames.
_BID_FORM_FILENAME_RES = (
    re.compile(r"Bid[_\- ]Schedule", re.IGNORECASE),
    re.compile(r"\bHSP\b", re.IGNORECASE),
    re.compile(r"Subcontracting[_\- ]Plan", re.IGNORECASE),
    re.compile(r"Attachment[_\- ]A\b", re.IGNORECASE),
)

_PROJECT_MANUAL_HINTS = (
    "GENERAL INSTRUCTIONS TO BIDDERS",
    "QUESTIONNAIRE",
    "PROJECT REQUIREMENTS",
    "EXHIBIT",
    "TABLE OF CONTENTS",
    "INVITATION TO BID",
    "WAGE DETERMINATION",
    "DAVIS-BACON",
    "DAVIS BACON",
    "PREVAILING WAGE",
    "GENERAL CONDITIONS",
    "SUPPLEMENTARY GENERAL CONDITIONS",
    "UNIFORM GENERAL CONDITIONS",
    "SAMPLE CONSTRUCTION SERVICES AGREEMENT",
    "TAX EXEMPTION",
    "TAX EXEMPT",
    "AMENDMENT TO SOLICITATION",
    "AMENDMENT NUMBER",
    "SOLICITATION AMENDMENT",
)

# Filenames that mark a doc as a supporting / boilerplate exhibit
# (amendments, wage determinations, general conditions, sample contracts).
# Checked BEFORE the bid-package filename signals so that e.g.
# "Sol_140P6026Q0029_Amd_0001.pdf" lands in PROJECT_MANUAL, not BID_PACKAGE.
_PROJECT_MANUAL_FILENAME_RES = (
    re.compile(r"Wage[_\- ]Determination", re.IGNORECASE),
    re.compile(r"\bDOL\b", re.IGNORECASE),
    re.compile(r"Davis[_\- ]Bacon", re.IGNORECASE),
    re.compile(r"Prevailing[_\- ]Wage", re.IGNORECASE),
    re.compile(r"General[_\- ]Conditions", re.IGNORECASE),
    re.compile(r"_Amd[_\- ]?\d+", re.IGNORECASE),
    re.compile(r"\bAmendment\b", re.IGNORECASE),
    re.compile(r"Tax[_\- ]Exemption", re.IGNORECASE),
    re.compile(r"Services[_\- ]Agreement", re.IGNORECASE),
)

# Hard veto: filenames that obviously indicate a drawing set should never be
# bundle-routed regardless of body text (some drawing-set cover pages contain
# the word "SOLICITATION" because the parent procurement is one). We anchor
# on filename separators (`_`, `-`, space, `.`, or end-of-string) rather than
# `\b` because Python's word-boundary treats `_` as a word character, so
# `\bDrawings\b` does NOT match `_Drawings.pdf` — the exact filename pattern
# we need to catch.
_DRAWING_FILENAME_RES = (
    re.compile(r"(?:^|[_\-\s.])Drawings?(?:[_\-\s.]|$)", re.IGNORECASE),
)

# Page-count cap on body-text PROJECT_MANUAL routing. Government solicitations
# routinely exceed 100 pages (Carr EFA RFCSP is 311 pages, the TTUS Uniform
# General Conditions exhibit is 109). The cap exists only to avoid bundling a
# 1000-page drawing set with a stray "Exhibit" phrase on page 1; 500 is well
# above any realistic single-document RFP and below any plausible drawing-set
# spine.
_BUNDLE_PAGE_CAP = 500


def _classify_document(
    pdf_name: str,
    text: str,
    page_count: int,
    avg_chars_per_page: float,
) -> SheetType:
    """Heuristically decide whether a whole PDF should be treated as a single
    text document (bid package / form / manual) instead of split per-page for
    vision analysis.

    Order matters and is filename-first so that the unambiguous signals in
    real-world solicitation filenames win over incidental body-text mentions
    (e.g. a parent RFP that says "complete the attached BID SCHEDULE" must
    not be misclassified as the bid form itself):

      1. drawing-set filename veto
      2. supporting-document filename (amendments, wage determinations, …)
      3. bid-form filename (Bid_Schedule, HSP, Attachment_A, …)
      4. bid-package filename (Sol_, ESBD_, RFCSP, SOW_, legacy NN.NN_-_, …)
      5. body-text bid-form hints
      6. body-text bid-package hints (legacy + government RFP)
      7. body-text project-manual hints
      8. tiny-brochure fallback
    """
    upper = text.upper()
    name_upper = pdf_name.upper()

    # 1. Drawing-set veto. A doc whose filename screams "drawings" must go
    #    through the per-page sheet path even if it has stray RFP text.
    if any(rx.search(pdf_name) for rx in _DRAWING_FILENAME_RES):
        return SheetType.UNKNOWN

    # 2. Supporting / boilerplate documents (amendments, wage determinations,
    #    general conditions, sample contracts, tax exemptions). Routed ahead
    #    of bid-package filename signals so that e.g.
    #    "Sol_140P6026Q0029_Amd_0001.pdf" lands in PROJECT_MANUAL rather
    #    than getting picked up by the leading `Sol_` prefix.
    if any(rx.search(pdf_name) for rx in _PROJECT_MANUAL_FILENAME_RES):
        return SheetType.PROJECT_MANUAL

    # 3. Bid-form filename signals (Bid_Schedule, HSP, Attachment_A, …).
    #    Checked before the bid-package filename signals so that an ESBD
    #    attachment like "ESBD_..._Attachment A.pdf" (a bid form on its own)
    #    isn't routed as the parent solicitation just because of the `ESBD_`
    #    prefix.
    if "BLANK BID FORM" in name_upper or any(rx.search(pdf_name) for rx in _BID_FORM_FILENAME_RES):
        return SheetType.BID_FORM

    # 4. Bid-package filename signals: legacy trade-specific pattern OR a
    #    government-solicitation prefix/token. These are unambiguous in
    #    practice, so a single filename match is enough.
    if (
        _BID_PACKAGE_FILENAME_RE.match(pdf_name)
        or any(rx.search(pdf_name) for rx in _GOV_BID_PACKAGE_FILENAME_RES)
    ):
        return SheetType.BID_PACKAGE

    # 5. Body-text bid-form hints (BLANK BID FORM, BID SCHEDULE, …).
    if any(h in upper for h in _BID_FORM_HINTS):
        return SheetType.BID_FORM

    # 6. Body-text bid-package hints — legacy structural phrases or
    #    two-or-more government-RFP phrases.
    bid_hits = sum(1 for h in _BID_PACKAGE_HINTS if h in upper)
    gov_hits = sum(1 for h in _GOV_RFP_HINTS if h in upper)
    if bid_hits >= 2 or gov_hits >= 2:
        return SheetType.BID_PACKAGE

    # 7. Project manual / boilerplate text: at least one project-manual phrase
    #    in body text, page count within the bundle cap, and meaningful text
    #    density (rules out drawing-only pages with a stray TOC hit).
    pm_hits = sum(1 for h in _PROJECT_MANUAL_HINTS if h in upper)
    if pm_hits >= 1 and page_count <= _BUNDLE_PAGE_CAP and avg_chars_per_page > 600:
        return SheetType.PROJECT_MANUAL

    # 8. Tiny brochure / flyer (1-3 pages, mostly text).
    if page_count <= 3 and avg_chars_per_page > 400:
        return SheetType.PROJECT_MANUAL

    return SheetType.UNKNOWN


# --- F-1: content-hash deduplication ---------------------------------------
#
# Calibration v4 (CALIBRATION_REPORT.md, Finding F-1) discovered that the
# corpus contained 16 PDFs that lived both at the root of an attachments
# folder AND under a `potentialsols/` sibling folder. With `--recursive` the
# ingestion path picked them up twice and inflated `bid_packages` ~1.6×. The
# `_pdf_content_hash` + dedupe filter inside `process_pdfs` collapses
# identical-content duplicates to a single canonical path. The canonical
# choice is "first seen wins after sorting by path length ascending", which
# preserves the root-level file over its `subdir/...` shadow.

_HASH_CHUNK_BYTES = 1 << 20  # 1 MiB; PDFs are small so a single chunk usually


def _pdf_content_hash(path: str | os.PathLike) -> str:
    """Return the SHA-256 hex digest of the file at ``path``.

    Treats the file as raw bytes — PDF metadata, embedded thumbnails, and
    any encryption envelope all participate in the identity. Two PDFs that
    encode the same source content but have different metadata (e.g.
    saved-by-different-versions of the same template) will hash differently
    and are NOT deduplicated; that conservative bias is intentional, since
    the consequence of a false-positive dedupe (silently dropping a real
    document) is much worse than a false-negative.
    """
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(_HASH_CHUNK_BYTES)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def _classify_pdf_kind(pdf_path: str | os.PathLike) -> SheetType:
    """Classify a PDF as a document-level :class:`SheetType` for filtering.

    Opens the PDF, reads the first 3 pages of text, and delegates to
    :func:`_classify_document`. The return is the same value
    :func:`process_pdfs` would compute internally — surfacing it here lets
    `analyze.py --no-drawings` filter out drawing-set PDFs (those that
    classify to :attr:`SheetType.UNKNOWN`) before the expensive
    vision-extraction stage.

    Raises whatever ``fitz.open`` raises on a malformed PDF; callers that
    need a non-throwing variant should wrap in try/except.
    """
    pdf_path = Path(pdf_path)
    with fitz.open(pdf_path) as doc:
        page_count = len(doc)
        first_text = "".join(
            (doc[i].get_text("text") or "") for i in range(min(3, page_count))
        )
        avg_chars = (len(first_text) / max(min(3, page_count), 1)) if page_count else 0.0
        return _classify_document(pdf_path.name, first_text, page_count, avg_chars)


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
    dedupe: bool = True,
) -> tuple[list[Sheet], list[DocumentBundle]]:
    """Split every PDF into sheets and render them.

    Args:
        pdf_paths: Iterable of paths to source PDFs. When ``dedupe`` is on
            (the default), the order does not matter — paths are re-sorted by
            length ascending so the shortest path wins on hash collision.
        cache_dir: Directory to write rendered page images / thumbnails to.
        dpi: Render DPI for drawing pages.
        document_level_types: Which :class:`SheetType` values route a PDF
            through the bundle (whole-document) path instead of the per-page
            sheet path.
        dedupe: When True (F-1 calibration finding), collapse PDFs with
            identical SHA-256 of file bytes to the single shortest-path
            occurrence and emit a warning naming both paths. When False, the
            duplicate-PDF inflation described in
            ``exports/calibration_v4/CALIBRATION_REPORT.md`` Finding F-1 is
            preserved — useful only when an operator genuinely wants to see
            shadowed duplicates.

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

    # --- F-1 dedupe pass: collapse identical-content PDFs by SHA-256 -------
    # We sort the paths by length ascending so that on a collision the
    # shorter (canonical) path wins. Hashing is read-only and never touches
    # PyMuPDF — encrypted / malformed PDFs hash fine and will surface their
    # error later inside ``fitz.open`` below, the same as before this filter.
    ordered = [Path(p) for p in pdf_paths]
    if dedupe and ordered:
        ordered.sort(key=lambda p: (len(str(p)), str(p)))
        seen: dict[str, Path] = {}
        deduped: list[Path] = []
        for path in ordered:
            try:
                digest = _pdf_content_hash(path)
            except OSError as exc:
                logger.warning(
                    "dedupe: could not hash %s (%s); keeping it in the input set.",
                    path,
                    exc,
                )
                deduped.append(path)
                continue
            existing = seen.get(digest)
            if existing is None:
                seen[digest] = path
                deduped.append(path)
            else:
                logger.warning(
                    "dedupe: dropping duplicate PDF (same SHA-256): kept=%s, dropped=%s",
                    existing,
                    path,
                )
        ordered = deduped

    for pdf_path in ordered:
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
                    pdf_path=str(pdf_path),
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
