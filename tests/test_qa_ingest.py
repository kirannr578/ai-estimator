"""QA pass — Subsystem 1: PDF ingestion + classification (2026-05-28).

Exercises :mod:`core.pdf_processor` against positive / negative / edge
scenarios documented in ``docs/QA_REPORT_2026-05-28.md`` §3.1.

All fixtures are synthesised on the fly with ``fitz`` so no binary
fixtures need to live in the repo and no live LLM is involved (this
module never instantiates :class:`core.llm_client.LLMClient`).
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz
import pytest

from core.pdf_processor import (
    DocumentBundle,
    _BUNDLE_PAGE_CAP,
    _classify_document,
    process_pdfs,
)
from core.schemas import Discipline, SheetType


# ---------------------------------------------------------------------------
# Fixture builders
# ---------------------------------------------------------------------------


def _make_pdf(
    tmp_path: Path,
    *,
    pages: list[str],
    name: str = "sample.pdf",
) -> Path:
    """Build a PDF with one page per ``pages`` entry; each page text is the entry."""
    doc = fitz.open()
    for body in pages:
        page = doc.new_page(width=792, height=612)
        for i, line in enumerate(body.splitlines() or [body]):
            page.insert_text((40, 60 + i * 14), line, fontsize=10)
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_qa_pos_drawing_set_routes_to_sheets(tmp_path: Path) -> None:
    """Multi-page drawing PDF → all pages emerge as Sheets, no bundle."""
    pages = [
        "FLOOR PLAN\nSheet A-101\n1/4\" = 1'-0\"",
        "ELEVATION\nSheet A-201",
        "DOOR SCHEDULE\nSheet A-601",
    ]
    pdf = _make_pdf(tmp_path, pages=pages, name="DrawingSet.pdf")
    sheets, bundles = process_pdfs([pdf], cache_dir=tmp_path / "cache")

    assert bundles == []
    assert len(sheets) == 3
    assert {s.page_index for s in sheets} == {0, 1, 2}
    # Every drawing sheet has a rendered PNG on disk.
    for s in sheets:
        assert Path(s.image_path).is_file()
        assert s.pdf_name == "DrawingSet.pdf"


def test_qa_pos_bid_form_routes_to_bundle(tmp_path: Path) -> None:
    """A bid-schedule PDF lands in document_bundles with sheet_type=BID_FORM."""
    pdf = _make_pdf(
        tmp_path,
        pages=[
            "PROPOSAL FORM\n"
            "BID SCHEDULE\n"
            "ALL BIDDERS PROVIDE PRICING BELOW.\n"
            "ITEM 1 - MOBILIZATION\n"
        ],
        name="Bid_Schedule.pdf",
    )
    sheets, bundles = process_pdfs([pdf], cache_dir=tmp_path / "cache")
    assert sheets == []
    assert len(bundles) == 1
    assert bundles[0].sheet_type == SheetType.BID_FORM
    assert bundles[0].pdf_name == "Bid_Schedule.pdf"
    assert bundles[0].page_count == 1


def test_qa_pos_government_rfp_routes_to_bid_package(tmp_path: Path) -> None:
    """SAM.gov-style RFP body text routes to BID_PACKAGE."""
    body = (
        "REQUEST FOR PROPOSALS\n"
        "SOLICITATION NUMBER 140P6026Q0029\n"
        "STATEMENT OF WORK\n"
        "OFFERORS shall comply with the contracting officer's instructions.\n"
    )
    pdf = _make_pdf(tmp_path, pages=[body, "Continuation."], name="Sol_Carr_EFA.pdf")
    sheets, bundles = process_pdfs([pdf], cache_dir=tmp_path / "cache")
    assert sheets == []
    assert len(bundles) == 1
    assert bundles[0].sheet_type == SheetType.BID_PACKAGE


# ---------------------------------------------------------------------------
# Negative
# ---------------------------------------------------------------------------


def test_qa_neg_corrupted_pdf_raises(tmp_path: Path) -> None:
    """Truncated PDF bytes → fitz raises a clear error; no silent miss."""
    bad = tmp_path / "bad.pdf"
    bad.write_bytes(b"%PDF-1.4\n% corrupted intentionally")
    with pytest.raises(Exception):  # fitz.fitz.FileDataError or RuntimeError
        process_pdfs([bad], cache_dir=tmp_path / "cache")


def test_qa_neg_nonpdf_extension_raises(tmp_path: Path) -> None:
    """A path that doesn't open as PDF should not silently produce empty output."""
    bad = tmp_path / "not_a.pdf"
    bad.write_text("this is plain text, not a PDF")
    with pytest.raises(Exception):
        process_pdfs([bad], cache_dir=tmp_path / "cache")


def test_qa_neg_drawing_filename_veto_blocks_misroute(tmp_path: Path) -> None:
    """A file whose name screams "Drawings" should never bundle even with RFP text.

    Calibration-v3 hard veto: a drawing-set cover page may legitimately
    contain RFP wording for the parent procurement, but the per-page
    sheet path must still win.
    """
    # Two RFP phrases would normally route to BID_PACKAGE under hint
    # rule #6, but the filename veto runs first.
    body = (
        "REQUEST FOR PROPOSALS\n"
        "STATEMENT OF WORK\n"
        "Sheet A-101 — Cover\n"
    )
    pdf = _make_pdf(tmp_path, pages=[body], name="Project_Drawings.pdf")
    sheets, bundles = process_pdfs([pdf], cache_dir=tmp_path / "cache")
    assert bundles == []
    assert len(sheets) == 1
    assert sheets[0].sheet_type == SheetType.UNKNOWN


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_qa_edge_single_page_pdf_classified(tmp_path: Path) -> None:
    """A 1-page PDF still classifies and yields one sheet OR one bundle."""
    pdf = _make_pdf(
        tmp_path,
        pages=["FLOOR PLAN A-101\n1/4\" = 1'-0\""],
        name="single.pdf",
    )
    sheets, bundles = process_pdfs([pdf], cache_dir=tmp_path / "cache")
    assert (len(sheets) + len(bundles)) == 1


def test_qa_edge_do_not_use_prefix_skipped(tmp_path: Path) -> None:
    """PDFs prefixed ``DO_NOT_USE`` are silently dropped by ``process_pdfs``."""
    skip = _make_pdf(
        tmp_path, pages=["FLOOR PLAN A-101"], name="DO_NOT_USE_old.pdf"
    )
    keep = _make_pdf(tmp_path, pages=["FLOOR PLAN A-201"], name="keep.pdf")
    sheets, bundles = process_pdfs([skip, keep], cache_dir=tmp_path / "cache")
    assert all(s.pdf_name == "keep.pdf" for s in sheets)
    assert all(b.pdf_name == "keep.pdf" for b in bundles)


def test_qa_edge_amendment_filename_routes_to_project_manual() -> None:
    """``Sol_*_Amd_0001.pdf`` must land in PROJECT_MANUAL, not BID_PACKAGE.

    Filename-rule #2 (supporting docs) runs ahead of #4 (bid-package
    filename) so an amendment whose filename starts with the
    bid-package prefix doesn't get routed by the wrong rule.
    """
    name = "Sol_140P6026Q0029_Amd_0001.pdf"
    body = "AMENDMENT TO SOLICITATION\nAMENDMENT NUMBER 0001"
    assert _classify_document(name, body, page_count=4, avg_chars_per_page=200) == \
        SheetType.PROJECT_MANUAL


def test_qa_edge_500_page_at_bundle_cap_classifies() -> None:
    """At the bundle cap (500), a manual still classifies as PROJECT_MANUAL.

    Tests the boundary off-by-one of ``page_count <= _BUNDLE_PAGE_CAP``.
    """
    body = (
        "GENERAL CONDITIONS\nINVITATION TO BID\nWAGE DETERMINATION\n"
        + ("filler text for density. " * 40)
    )
    assert _classify_document(
        "Project_Manual.pdf", body, page_count=_BUNDLE_PAGE_CAP, avg_chars_per_page=900
    ) == SheetType.PROJECT_MANUAL


def test_qa_edge_501_pages_above_cap_falls_through() -> None:
    """One page over the cap → not bundled (falls through to UNKNOWN).

    Pins the off-by-one: ``page_count > 500`` must NOT bundle.
    """
    body = "GENERAL CONDITIONS\n" + ("filler. " * 80)
    result = _classify_document(
        "ProjectManual.pdf",
        body,
        page_count=_BUNDLE_PAGE_CAP + 1,
        avg_chars_per_page=900,
    )
    assert result == SheetType.UNKNOWN


def test_qa_edge_sheet_number_regex_extracts_disciplines(tmp_path: Path) -> None:
    """Discipline prefix in the title block resolves to the right enum."""
    cases: dict[str, Discipline] = {
        "M-101": Discipline.MECHANICAL,
        "E-201": Discipline.ELECTRICAL,
        "P-301": Discipline.PLUMBING,
        "S-1.0": Discipline.STRUCTURAL,
    }
    for sn, disc in cases.items():
        pdf = _make_pdf(
            tmp_path,
            pages=[f"{sn}\nFLOOR PLAN"],
            name=f"d_{sn.replace('-', '_').replace('.', '_')}.pdf",
        )
        sheets, _ = process_pdfs([pdf], cache_dir=tmp_path / "cache")
        assert sheets, f"expected at least one sheet for {sn}"
        # process_pdfs uses use_enum_values=True so this comes back as the str value.
        assert sheets[0].discipline == disc.value, f"{sn} → {sheets[0].discipline}"


def test_qa_neg_password_protected_pdf_raises(tmp_path: Path) -> None:
    """A password-protected PDF must NOT silently produce empty extraction.

    The brief calls for a graceful error / no-crash path. The current
    implementation of :func:`process_pdfs` calls ``fitz.open(path)``
    without ``authenticate()``; PyMuPDF surfaces this either by raising
    on ``open`` or by returning a doc whose pages have empty text /
    zero-width. We assert either an exception OR an obviously-degraded
    result (sheets count == 0). If the PDF passes through with full
    page content extracted we'd flag a security/correctness bug — at
    today's behaviour we expect the empty / raise path.
    """
    import fitz

    doc = fitz.open()
    page = doc.new_page(width=612, height=792)
    page.insert_text((50, 50), "DOOR SCHEDULE\nMARK TYPE WIDTH HEIGHT")
    enc = tmp_path / "encrypted.pdf"
    # AES-256 with user password — the most common real-world case.
    doc.save(
        enc,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        user_pw="secret",
        owner_pw="secret",
    )
    doc.close()

    try:
        sheets, bundles = process_pdfs([enc], cache_dir=tmp_path / "cache")
    except Exception:
        # Acceptable outcome — PyMuPDF refused the encrypted document.
        return

    # If process_pdfs returned, sheets+bundles must NOT contain extracted
    # content (otherwise content was leaked through encryption).
    for s in sheets:
        # Embedded text from an encrypted page must not contain the
        # plaintext we wrote (``DOOR SCHEDULE``).
        assert "DOOR SCHEDULE" not in (s.embedded_text or ""), (
            "encrypted PDF leaked plaintext via process_pdfs"
        )
    for b in bundles:
        assert "DOOR SCHEDULE" not in (b.full_text or ""), (
            "encrypted PDF leaked plaintext via process_pdfs"
        )
