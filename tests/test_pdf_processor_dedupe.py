"""Regression tests for T10 Finding F-1 — content-hash dedupe at ingestion.

Calibration v4 (``exports/calibration_v4/CALIBRATION_REPORT.md`` §F-1)
discovered that the corpus contained 16 PDFs that lived both at the root of
an attachments folder AND under a ``potentialsols/`` sibling. With
``--recursive``, the bundler picked them up twice and inflated
``bid_packages`` ~1.6×. This module pins the fix:

* ``_pdf_content_hash`` returns the SHA-256 of file bytes.
* ``process_pdfs(..., dedupe=True)`` (the default) collapses
  identical-content PDFs to a single canonical occurrence chosen by
  shortest path.
* ``process_pdfs(..., dedupe=False)`` preserves duplicates for back-compat.

No live LLM, no binary fixtures — every PDF is synthesised on the fly with
PyMuPDF.
"""

from __future__ import annotations

import logging
from pathlib import Path

import fitz
import pytest

from core.pdf_processor import _pdf_content_hash, process_pdfs


def _make_pdf(out_path: Path, *, pages: list[str]) -> Path:
    """Build a deterministic-content PDF.

    The same ``pages`` list produces a byte-identical PDF in two calls (modulo
    PyMuPDF metadata noise — see ``_make_pdf_pair`` for the safer way to
    produce two byte-identical files).
    """
    doc = fitz.open()
    for body in pages:
        page = doc.new_page(width=612, height=792)
        for i, line in enumerate(body.splitlines() or [body]):
            page.insert_text((40, 60 + i * 14), line, fontsize=10)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    doc.close()
    return out_path


def _make_pdf_pair(root: Path, *, pages: list[str], name: str) -> tuple[Path, Path]:
    """Produce two PDFs with literally identical bytes at two paths.

    Builds one PDF, then ``write_bytes()`` copies the raw bytes to a second
    location so SHA-256 matches even if PyMuPDF embeds a timestamp / random
    object id in the source PDF.
    """
    canonical = _make_pdf(root / name, pages=pages)
    shadow_dir = root / "potentialsols"
    shadow_dir.mkdir(parents=True, exist_ok=True)
    shadow = shadow_dir / name
    shadow.write_bytes(canonical.read_bytes())
    return canonical, shadow


# ---------------------------------------------------------------------------
# _pdf_content_hash
# ---------------------------------------------------------------------------


def test_pdf_content_hash_is_stable_and_distinguishes_content(tmp_path: Path) -> None:
    """Same bytes → same digest; different bytes → different digest."""
    a, b = _make_pdf_pair(tmp_path, pages=["FLOOR PLAN\nA-101"], name="same.pdf")
    other = _make_pdf(tmp_path / "other.pdf", pages=["ELEVATION\nA-201"])

    assert _pdf_content_hash(a) == _pdf_content_hash(b)
    assert _pdf_content_hash(a) != _pdf_content_hash(other)
    # SHA-256 hex is 64 chars.
    assert len(_pdf_content_hash(a)) == 64


# ---------------------------------------------------------------------------
# Core dedupe behaviour inside process_pdfs
# ---------------------------------------------------------------------------


def test_dedupe_keeps_shorter_path_on_collision(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """Two identical-content PDFs at different paths → keep the shorter path,
    and emit a structured warning naming both sides of the collision.

    This is the canonical Finding F-1 scenario: the same file lives at
    ``<root>/RFP.pdf`` and ``<root>/potentialsols/RFP.pdf``; we want
    ``RFP.pdf`` (shorter) to be the canonical and ``potentialsols/RFP.pdf``
    to be dropped with a warning.
    """
    root_pdf, shadow_pdf = _make_pdf_pair(
        tmp_path, pages=["BID PACKAGE\nGENERAL INSTRUCTIONS TO BIDDERS"], name="RFP.pdf"
    )

    caplog.set_level(logging.WARNING, logger="core.pdf_processor")
    # Pass the shadow FIRST to prove the sort step (not input order)
    # picks the canonical.
    sheets, bundles = process_pdfs(
        [shadow_pdf, root_pdf], cache_dir=tmp_path / "cache"
    )

    # Exactly one bundle (BID_PACKAGE body text routes it through the bundle
    # path), and the canonical one is the shorter / root-level file.
    assert len(bundles) == 1
    assert Path(bundles[0].pdf_path) == root_pdf
    assert sheets == []

    # A structured warning naming both paths was emitted.
    dedupe_msgs = [r.message for r in caplog.records if "dedupe:" in r.message]
    assert dedupe_msgs, f"expected a dedupe warning; saw {caplog.records!r}"
    msg = dedupe_msgs[0]
    assert str(root_pdf) in msg
    assert str(shadow_pdf) in msg
    assert "dropped" in msg.lower() or "duplicate" in msg.lower()


def test_dedupe_distinct_content_same_name_both_retained(tmp_path: Path) -> None:
    """Two PDFs with the same filename but different content → both kept.

    Same SHA-256 is the ONLY dedupe trigger; filename collisions across
    folders without content collision must not collapse.
    """
    a_dir = tmp_path / "rfp_a"
    b_dir = tmp_path / "rfp_b"
    a = _make_pdf(a_dir / "RFP.pdf", pages=["BID PACKAGE A\nGENERAL INSTRUCTIONS TO BIDDERS"])
    b = _make_pdf(b_dir / "RFP.pdf", pages=["BID PACKAGE B\nGENERAL INSTRUCTIONS TO BIDDERS"])
    assert _pdf_content_hash(a) != _pdf_content_hash(b)

    sheets, bundles = process_pdfs([a, b], cache_dir=tmp_path / "cache")

    assert sheets == []
    assert len(bundles) == 2
    kept_paths = {Path(b_.pdf_path) for b_ in bundles}
    assert kept_paths == {a, b}


def test_dedupe_empty_input_returns_empty(tmp_path: Path) -> None:
    """No PDFs in, no crash, no output."""
    sheets, bundles = process_pdfs([], cache_dir=tmp_path / "cache")
    assert sheets == []
    assert bundles == []


def test_no_dedupe_flag_bypasses_filter(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """``dedupe=False`` preserves duplicates (back-compat / debug surface)."""
    a, b = _make_pdf_pair(
        tmp_path,
        pages=["BID PACKAGE\nGENERAL INSTRUCTIONS TO BIDDERS"],
        name="RFP.pdf",
    )

    caplog.set_level(logging.WARNING, logger="core.pdf_processor")
    sheets, bundles = process_pdfs(
        [a, b], cache_dir=tmp_path / "cache", dedupe=False
    )

    # BOTH files processed → 2 bundles.
    assert sheets == []
    assert len(bundles) == 2
    # No dedupe warning emitted.
    assert not [r for r in caplog.records if "dedupe:" in r.message]


def test_dedupe_default_is_on(tmp_path: Path) -> None:
    """The dedupe behaviour is the default — callers don't have to opt in.

    This is a contract pin: shipping ``dedupe=False`` by default would
    silently re-introduce the F-1 corpus inflation.
    """
    a, b = _make_pdf_pair(
        tmp_path,
        pages=["BID PACKAGE\nGENERAL INSTRUCTIONS TO BIDDERS"],
        name="RFP.pdf",
    )
    # No explicit dedupe arg.
    sheets, bundles = process_pdfs([a, b], cache_dir=tmp_path / "cache")
    assert len(bundles) == 1


def test_dedupe_three_way_collision_keeps_shortest(tmp_path: Path) -> None:
    """Three byte-identical PDFs at differently-long paths → only the
    shortest path survives, two warnings are emitted."""
    pages = ["BID PACKAGE\nGENERAL INSTRUCTIONS TO BIDDERS"]
    short = _make_pdf(tmp_path / "RFP.pdf", pages=pages)
    medium_dir = tmp_path / "potentialsols"
    medium_dir.mkdir()
    medium = medium_dir / "RFP.pdf"
    medium.write_bytes(short.read_bytes())
    deepest_dir = tmp_path / "archive" / "old" / "subfolder"
    deepest_dir.mkdir(parents=True)
    deepest = deepest_dir / "RFP.pdf"
    deepest.write_bytes(short.read_bytes())

    sheets, bundles = process_pdfs(
        [deepest, medium, short], cache_dir=tmp_path / "cache"
    )

    assert len(bundles) == 1
    assert Path(bundles[0].pdf_path) == short
    assert sheets == []


def test_dedupe_collapses_drawing_set_pair(tmp_path: Path) -> None:
    """The dedupe filter applies BEFORE the sheet/bundle routing, so two
    identical drawing PDFs collapse to one ⇒ one set of rendered sheets,
    not two. This is the inverse of the bundle scenario above and confirms
    the filter is independent of document classification.
    """
    pages = ["FLOOR PLAN\nA-101\n1/4\" = 1'-0\""]
    a = _make_pdf(tmp_path / "Drawings.pdf", pages=pages)
    shadow = tmp_path / "potentialsols" / "Drawings.pdf"
    shadow.parent.mkdir()
    shadow.write_bytes(a.read_bytes())

    sheets, bundles = process_pdfs([a, shadow], cache_dir=tmp_path / "cache")

    assert bundles == []
    assert {s.pdf_path for s in sheets} == {str(a)}
