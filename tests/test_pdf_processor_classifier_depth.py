r"""Regression tests for T10 follow-up ``t10_followup_classifier_hint_depth``.

Calibration v5a (``exports/calibration_v5/CALIBRATION_REPORT.md`` §F-5
note) documented that the document classifier sampled only the first 3
pages of text when deciding PROJECT_MANUAL vs UNKNOWN. Two real-world
311-page documents -- Carr EFA Project Manual and Harrington Lab303
Specifications -- buried their TABLE OF CONTENTS / WAGE DETERMINATION /
GENERAL CONDITIONS hint phrases beyond page 3 and slipped through as
UNKNOWN under ``--no-drawings``.

The fix has two complementary parts that this module pins:

* **Deeper sampling.** :func:`_sample_page_indices` returns up to 15
  distinct indices spanning first 5 + middle 5 + last 5 pages, so
  hints buried in the spec body or the bid-form tail still surface
  on a 300-1000 page doc.
* **Filename signal.** :data:`_PROJECT_MANUAL_NAME_RES` matches
  ``/spec(ification)?s?/`` and ``/project[-_\s]*(manual|book)/`` on
  filename-separator boundaries, biasing the classifier toward
  PROJECT_MANUAL when the doc is text-dense and within the bundle
  page cap -- catches the two miss cases even when body hints are
  missing entirely.

The drawing-set veto still runs ahead of both signals so filenames like
``roof_specifications_drawing.pdf`` still classify as drawings.

All fixtures are synthesised on the fly with PyMuPDF -- no real LLM, no
binary fixtures.
"""

from __future__ import annotations

from pathlib import Path

import fitz
import pytest

from core.pdf_processor import (
    _BUNDLE_PAGE_CAP,
    _classify_document,
    _classify_pdf_kind,
    _gather_classifier_sample,
    _sample_page_indices,
)
from core.schemas import SheetType


# ---------------------------------------------------------------------------
# Fixture helpers
# ---------------------------------------------------------------------------


_DENSE_FILLER = (
    "Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim "
    "veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea "
    "commodo consequat. Duis aute irure dolor in reprehenderit in voluptate."
)


def _dense_page(prefix: str = "") -> str:
    """Build a page body with ~30 dense lines (~3-4 kB of text)."""
    body = "\n".join([_DENSE_FILLER] * 30)
    if prefix:
        body = prefix + "\n" + body
    return body


def _make_pdf(out_path: Path, page_bodies: list[str]) -> Path:
    """Build a PDF with one page per entry in ``page_bodies``.

    Each entry's newlines become per-line ``insert_text`` calls so the
    resulting PDF has real embedded text that ``fitz.Document.get_text()``
    can extract back out -- otherwise the classifier sees an empty body
    and falls through to UNKNOWN.
    """
    doc = fitz.open()
    for body in page_bodies:
        page = doc.new_page(width=612, height=792)
        lines = body.splitlines() or [body]
        for i, line in enumerate(lines):
            page.insert_text((40, 50 + i * 11), line, fontsize=8)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    doc.close()
    return out_path


# ===========================================================================
# Section 1 — page-index sampling math
# ===========================================================================


def test_sample_page_indices_short_pdf_preserves_legacy_short_circuit() -> None:
    """``page_count <= 3`` returns every page index -- identical to the
    pre-fix ``range(min(3, page_count))`` short-circuit so single-page
    bid forms and 2-3 page brochures behave exactly as before.
    """
    assert _sample_page_indices(0) == []
    assert _sample_page_indices(1) == [0]
    assert _sample_page_indices(2) == [0, 1]
    assert _sample_page_indices(3) == [0, 1, 2]


def test_sample_page_indices_311_page_doc_covers_front_body_tail() -> None:
    """A 311-page document (Carr EFA Project Manual) samples the front 5,
    last 5, and 5 evenly-spread body indices. The spread sample at
    ~35 % (page 108) lands inside the realistic spec-section zone
    (pages ~100-150) -- this is the canonical fixture for the follow-up.
    """
    idx = _sample_page_indices(311)
    assert len(idx) == 15, idx
    assert idx == sorted(set(idx))
    assert idx[:5] == [0, 1, 2, 3, 4]
    assert idx[-5:] == [306, 307, 308, 309, 310]
    # Middle 5: spread across the central 60 % of the doc.
    middle = sorted(set(idx) - {0, 1, 2, 3, 4, 306, 307, 308, 309, 310})
    assert len(middle) == 5
    # At least one middle sample lands at the first quartile (pages 60-120)
    # so a spec section starting on page ~30 is reliably sampled.
    assert any(60 <= i <= 120 for i in middle), middle
    # And at least one near the centroid and the third quartile.
    assert any(140 <= i <= 170 for i in middle), middle
    assert any(200 <= i <= 260 for i in middle), middle


def test_sample_page_indices_bounded_on_1000_page_doc() -> None:
    """Even a 1000-page doc never costs more than 15 page-text reads.
    This is the cost-control gate: classification is O(1) in document
    length and the per-call overhead stays well below the cost of a
    single LLM round-trip.
    """
    idx = _sample_page_indices(1000)
    assert len(idx) == 15
    assert idx[0] == 0
    assert idx[-1] == 999
    # Spread samples should hit the centroid region (~500).
    assert any(490 <= i <= 510 for i in idx)
    # And the first / third quartiles (~200 and ~800).
    assert any(150 <= i <= 250 for i in idx)
    assert any(750 <= i <= 850 for i in idx)


def test_sample_page_indices_small_doc_uses_centered_stripe() -> None:
    """4-10 page PDFs use the centered-stripe fallback (no point spreading
    on a doc this small). With dedupe vs first/last, the result is the
    full range.
    """
    assert _sample_page_indices(7) == [0, 1, 2, 3, 4, 5, 6]
    assert _sample_page_indices(10) == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_sample_page_indices_unique_and_sorted_for_all_sizes() -> None:
    """No duplicates and ascending order across the full size range."""
    for n in (4, 5, 6, 10, 15, 25, 100, 311, 500, 999):
        idx = _sample_page_indices(n)
        assert idx == sorted(set(idx)), n
        assert all(0 <= i < n for i in idx), n
        # Bound check: never more than 15 distinct indices.
        assert len(idx) <= 15, (n, len(idx))


# ===========================================================================
# Section 2 — deeper sampling fixes the Carr EFA 311-page case
# ===========================================================================


def test_311_page_manual_with_hints_buried_at_pages_100_to_150(tmp_path: Path) -> None:
    """End-to-end pin of the follow-up: a 311-page PDF whose only
    PROJECT_MANUAL hint phrases live on pages 100-150 (i.e. outside the
    legacy first-3-pages window) must now classify as PROJECT_MANUAL.

    The filename here is neutral -- ``26-007_dressing_room.pdf`` does
    NOT match the new filename signal -- so this test isolates the
    deeper-sampling fix from the filename-signal fix.
    """
    pages: list[str] = []
    # Pages 1-5: dense generic intro (no classifier hints)
    pages.extend([_dense_page("INTRODUCTION") for _ in range(5)])
    # Pages 6-99: dense filler (no hints)
    pages.extend([_dense_page() for _ in range(94)])
    # Pages 100-150: PROJECT_MANUAL hint zone (buried beyond first-3)
    pages.extend([
        _dense_page("TABLE OF CONTENTS\nGENERAL CONDITIONS\nWAGE DETERMINATION")
        for _ in range(51)
    ])
    # Pages 151-305: dense filler
    pages.extend([_dense_page() for _ in range(155)])
    # Pages 306-311: dense filler tail (mimics bid-form attachments)
    pages.extend([_dense_page() for _ in range(6)])
    assert len(pages) == 311

    pdf = _make_pdf(tmp_path / "26-007_dressing_room.pdf", pages)
    assert _classify_pdf_kind(pdf) == SheetType.PROJECT_MANUAL, (
        "Carr EFA scenario: deeper sampling must pick up the buried "
        "TABLE OF CONTENTS / GENERAL CONDITIONS hits on pages 100-150."
    )


def test_pre_fix_first_three_pages_would_have_missed_buried_hints() -> None:
    """Pin the pre-fix behaviour as a baseline: if the classifier were
    given ONLY the first 3 pages of a 311-page manual whose hints are
    buried in the middle, it would return UNKNOWN.

    This is an inline simulation of the pre-fix code path (without
    reverting the production change) so the test guarantees the buried-
    hint scenario is genuinely exercising the new sampling depth.
    """
    front_only = _dense_page("INTRODUCTION") * 1  # no hint phrases here
    avg = len(front_only) / 1
    # Filename also neutral so neither signal fires.
    result = _classify_document(
        "26-007_dressing_room.pdf",
        front_only,
        page_count=311,
        avg_chars_per_page=avg,
    )
    assert result == SheetType.UNKNOWN, (
        "Pre-fix baseline: 311-page doc with no hints in front-only sample "
        "and no project-manual filename must classify as UNKNOWN."
    )


def test_hints_only_in_tail_are_also_captured(tmp_path: Path) -> None:
    """Some real-world manuals put their bid-form / wage-determination
    hints at the very end (post-spec attachments). Our tail-5 sampling
    must catch them too.
    """
    pages = (
        [_dense_page() for _ in range(200)]
        + [_dense_page("WAGE DETERMINATION\nDAVIS-BACON") for _ in range(5)]
    )
    pdf = _make_pdf(tmp_path / "exhibit_only_tail_hints.pdf", pages)
    assert _classify_pdf_kind(pdf) == SheetType.PROJECT_MANUAL


# ===========================================================================
# Section 3 — filename-signal regex (positive + negative)
# ===========================================================================


@pytest.mark.parametrize(
    "name",
    [
        "Project Manual.pdf",
        "Project_Manual.pdf",
        "Project-Manual.pdf",
        "ProjectManual.pdf",
        "26-007 Carr EFA Dressing Room Renovation Project Manual.pdf",
        "Project_Book_Vol_1.pdf",
        "Project Book.pdf",
        "Specifications.pdf",
        "Specs.pdf",
        "Spec.pdf",
        "Harrington_Lab303_Specifications.pdf",
        "26-007_Specifications.pdf",
    ],
)
def test_filename_signal_positive_matches_route_to_project_manual(name: str) -> None:
    """Project-manual / specifications / project-book filename patterns
    route text-dense docs to PROJECT_MANUAL even with zero body-text
    hint phrases. The density gate (avg_chars > 600) still applies.
    """
    # Body is dense but contains none of the _PROJECT_MANUAL_HINTS phrases,
    # so only the filename signal can produce PROJECT_MANUAL here.
    text = ("Generic body without any classifier hint phrases. " * 30)
    avg = len(text) / 1
    result = _classify_document(name, text, page_count=50, avg_chars_per_page=avg)
    assert result == SheetType.PROJECT_MANUAL, (
        f"Filename {name!r} should bias toward PROJECT_MANUAL; got {result!r}"
    )


@pytest.mark.parametrize(
    "name",
    [
        # Drawing veto fires first — task brief explicitly calls out this case
        "roof_specifications_drawing.pdf",
        "roof_drawings_with_specifications.pdf",
        "Carr_EFA_Project_Manual_Drawings.pdf",
        "Specifications-Drawings.pdf",
        "Project Book Drawing Set.pdf",
    ],
)
def test_drawing_veto_wins_over_project_manual_filename_signal(name: str) -> None:
    """A filename that screams "drawings" still classifies as UNKNOWN
    even when "specifications" / "project manual" / "project book"
    co-appears -- the drawing veto runs first in the classifier flow.
    """
    text = "Body text. " * 30
    avg = len(text) / 1
    result = _classify_document(name, text, page_count=50, avg_chars_per_page=avg)
    assert result == SheetType.UNKNOWN, (
        f"Drawing veto must beat filename signal on {name!r}; got {result!r}"
    )


@pytest.mark.parametrize(
    "name",
    [
        # Substring collisions on word fragments must NOT trigger the signal
        "spectacles.pdf",
        "inspect_report.pdf",
        "specsheet.pdf",
        "introspection_notes.pdf",
        "respectful_owner_handbook.pdf",
    ],
)
def test_filename_signal_does_not_match_word_fragments(name: str) -> None:
    """The filename regex is anchored on filename separators (start of
    string, ``_``, ``-``, whitespace, ``.``) so "spec" inside "spectacles"
    or "inspect" does NOT fire the signal. Without the anchor, we'd
    false-positive on any word containing the letters s-p-e-c.
    """
    text = "Body text without any classifier hint phrases. " * 30
    avg = len(text) / 1
    result = _classify_document(name, text, page_count=50, avg_chars_per_page=avg)
    assert result == SheetType.UNKNOWN, (
        f"Substring collision {name!r} must NOT trigger PROJECT_MANUAL; got {result!r}"
    )


def test_filename_signal_requires_text_density_gate() -> None:
    """A drawing PDF named "Specifications.pdf" (low text density, since
    drawings are image-dominant) must NOT route to PROJECT_MANUAL. The
    ``avg_chars_per_page > 600`` gate protects against drawing PDFs
    sneaking through on a misleading filename alone.
    """
    sparse = "title-block text"
    avg = len(sparse) / 1  # ~16 chars/page
    result = _classify_document(
        "Specifications.pdf", sparse, page_count=24, avg_chars_per_page=avg
    )
    assert result == SheetType.UNKNOWN


def test_filename_signal_requires_page_count_within_cap() -> None:
    """A spec-named PDF beyond the bundle page cap must NOT bundle.
    Pins the off-by-one: ``page_count > 500`` falls through.
    """
    text = ("filler. " * 200)
    avg = len(text) / 1
    result = _classify_document(
        "Specifications.pdf",
        text,
        page_count=_BUNDLE_PAGE_CAP + 1,
        avg_chars_per_page=avg,
    )
    assert result == SheetType.UNKNOWN


def test_filename_signal_does_not_override_bid_package_filename() -> None:
    """A government-RFP filename like ``RFCSP_Specifications.pdf`` should
    still route to BID_PACKAGE -- the bid-package filename rule wins
    because it sits ahead of the project-manual body/filename rule in
    the classifier order.
    """
    text = "Generic body. " * 30
    avg = len(text) / 1
    result = _classify_document(
        "ESBD_516718_RFCSP_Specifications.pdf",
        text,
        page_count=50,
        avg_chars_per_page=avg,
    )
    assert result == SheetType.BID_PACKAGE


# ===========================================================================
# Section 4 — real-world miss cases (Carr EFA + Harrington Lab303) end-to-end
# ===========================================================================


def test_carr_efa_real_filename_classifies_as_project_manual(tmp_path: Path) -> None:
    """The real-world filename from the v5a calibration miss case --
    ``26-007 Carr EFA Dressing Room Renovation Project Manual.pdf`` --
    must classify as PROJECT_MANUAL via :func:`_classify_pdf_kind`
    (the entry point used by ``analyze.py --no-drawings``).

    Stub bundle (20 dense pages, no body hints) so the test is fast --
    the filename signal alone proves sufficient.
    """
    pdf = _make_pdf(
        tmp_path / "26-007 Carr EFA Dressing Room Renovation Project Manual.pdf",
        [_dense_page() for _ in range(20)],
    )
    assert _classify_pdf_kind(pdf) == SheetType.PROJECT_MANUAL


def test_harrington_lab303_specifications_classifies_as_project_manual(
    tmp_path: Path,
) -> None:
    """The other real-world v5a miss case: ``Harrington_Lab303_Specifications.pdf``
    must classify as PROJECT_MANUAL on the filename signal alone, even
    with a stub bundle that has no body hint phrases.
    """
    pdf = _make_pdf(
        tmp_path / "Harrington_Lab303_Specifications.pdf",
        [_dense_page() for _ in range(15)],
    )
    assert _classify_pdf_kind(pdf) == SheetType.PROJECT_MANUAL


# ===========================================================================
# Section 5 — sampling helper directly + regression pins on shorter paths
# ===========================================================================


def test_gather_classifier_sample_concatenates_indexed_pages(tmp_path: Path) -> None:
    """:func:`_gather_classifier_sample` should join text only from the
    indices :func:`_sample_page_indices` returns -- not every page.
    """
    pages = (
        [_dense_page("FRONT MARKER")]
        + [_dense_page() for _ in range(10)]
        + [_dense_page("MIDDLE MARKER")]
        + [_dense_page() for _ in range(10)]
        + [_dense_page("TAIL MARKER")]
    )
    pdf = _make_pdf(tmp_path / "markers.pdf", pages)
    with fitz.open(pdf) as doc:
        text, avg = _gather_classifier_sample(doc)
    assert "FRONT MARKER" in text
    assert "TAIL MARKER" in text
    assert avg > 600, "dense filler pages should easily clear the density gate"


def test_three_page_tiny_brochure_short_circuit_preserved(tmp_path: Path) -> None:
    """Tiny brochures (≤3 pages, dense text) still classify as
    PROJECT_MANUAL via the step-8 fallback -- pre-fix behaviour preserved.
    """
    pdf = _make_pdf(
        tmp_path / "tiny_brochure.pdf",
        [_dense_page() for _ in range(3)],
    )
    assert _classify_pdf_kind(pdf) == SheetType.PROJECT_MANUAL


def test_zero_page_document_handled_as_unknown() -> None:
    """Empty doc → no sample, no hits, no classification. Defensive."""
    assert _classify_document("anything.pdf", "", page_count=0, avg_chars_per_page=0.0) == SheetType.UNKNOWN


def test_existing_drawing_set_still_routes_to_sheets(tmp_path: Path) -> None:
    """A 50-page drawing PDF with no spec/manual filename keywords must
    still route to the sheet path (UNKNOWN at the document level).
    Guards against the deeper sampling accidentally lifting drawing-only
    PDFs into the bundle path on stray title-block text.
    """
    pages = [
        f"FLOOR PLAN A-{100 + i}\n1/4\" = 1'-0\"\nSheet {i + 1} of 50"
        for i in range(50)
    ]
    pdf = _make_pdf(tmp_path / "A_floor_plans.pdf", pages)
    assert _classify_pdf_kind(pdf) == SheetType.UNKNOWN
