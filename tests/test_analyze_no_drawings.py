"""Regression tests for T10 Finding F-5 — ``--no-drawings`` semantic.

Calibration v4 (``exports/calibration_v4/CALIBRATION_REPORT.md`` §F-5)
documented that ``analyze.py --no-drawings`` was a 5 MB SIZE filter, not a
logical drawing-classifier filter. Two failure modes followed:

* Small drawings (<5 MB) still got vision-classified.
* Large non-drawing files (project manuals, spec PDFs, RFCSPs) were
  excluded even though they are NOT drawings.

The fix re-implements ``--no-drawings`` as a classifier filter that drops
files whose document-level type is the drawing (per-page) route, and adds
``--max-pdf-mb=<MB>`` to expose the legacy size heuristic for operators
who explicitly want it.

These tests synthesise PDFs on the fly — no real LLM, no binary fixtures.
"""

from __future__ import annotations

import logging
import subprocess
import sys
from pathlib import Path

import fitz
import pytest

from analyze import _filter_by_max_size_mb, _filter_out_drawing_pdfs


_DENSE_FILLER_LINE = (
    "Lorem ipsum dolor sit amet consectetur adipiscing elit sed do eiusmod "
    "tempor incididunt ut labore et dolore magna aliqua ut enim ad minim."
)


def _make_pdf(out_path: Path, *, pages: list[str], pad_to_bytes: int = 0) -> Path:
    """Build a small PDF and optionally pad it to ``pad_to_bytes`` total size.

    Each page body is split on newlines and rendered line-by-line at 10 pt;
    pages with single-very-long lines are auto-wrapped into 50 dense filler
    lines so the doc-level classifier's ``avg_chars_per_page > 600`` density
    threshold is reached (otherwise ``_classify_document`` falls through to
    ``UNKNOWN`` even on a body that clearly looks like a project manual).

    Padding is appended as an after-EOF comment so PyMuPDF still parses the
    file correctly while the on-disk size reaches the requested threshold —
    needed for the legacy size-filter tests.
    """
    doc = fitz.open()
    for body in pages:
        page = doc.new_page(width=612, height=792)
        lines = body.splitlines() or [body]
        # Pad sparse pages with deterministic filler so embedded-text density
        # passes the classifier threshold. 50 lines × ~120 chars ≈ 6 kB.
        filler_target = 50
        if len(lines) < filler_target:
            lines = list(lines) + [
                _DENSE_FILLER_LINE for _ in range(filler_target - len(lines))
            ]
        for i, line in enumerate(lines):
            page.insert_text((40, 60 + i * 13), line, fontsize=9)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    doc.save(out_path)
    doc.close()
    if pad_to_bytes:
        current = out_path.stat().st_size
        pad = pad_to_bytes - current
        if pad > 0:
            with open(out_path, "ab") as f:
                # ``%`` starts a PDF comment line — anything after EOF is
                # ignored by parsers but counted in file size.
                f.write(b"\n%" + b"P" * (pad - 2))
    return out_path


# ---------------------------------------------------------------------------
# _filter_out_drawing_pdfs (new classifier-based --no-drawings)
# ---------------------------------------------------------------------------


def test_filter_out_drawing_pdfs_keeps_classified_bundle(tmp_path: Path) -> None:
    """A bid-package PDF (small, non-drawing) is kept — the OLD size filter
    would have kept it too, but the NEW filter keeps it because the doc
    classifier identifies it as a BID_PACKAGE, not because it's small.
    """
    rfp = _make_pdf(
        tmp_path / "Sol_140P6026Q0029.pdf",
        pages=[
            "REQUEST FOR PROPOSALS\nSOLICITATION NUMBER 140P6026Q0029\n"
            "OFFEROR shall complete the attached BID SCHEDULE.\n"
            "STATEMENT OF WORK\nPERIOD OF PERFORMANCE 365 days.",
            "Section L\nSection M",
        ],
    )
    kept = _filter_out_drawing_pdfs([rfp])
    assert kept == [rfp]


def test_filter_out_drawing_pdfs_drops_drawing_set(tmp_path: Path) -> None:
    """A drawing PDF (filename triggers the drawing-veto) is dropped even
    when it is small — proving the filter is no longer size-based.
    """
    drawings = _make_pdf(
        tmp_path / "B08_Solicitation_-_Att_2_-_Drawings.pdf",
        pages=[
            "FLOOR PLAN\nSheet A-101\n1/4\" = 1'-0\"",
            "ELEVATION\nSheet A-201",
        ],
    )
    # Make sure the file is well under the legacy 5 MB threshold — that
    # is the whole point of the F-5 fix.
    assert drawings.stat().st_size < 5 * 1024 * 1024
    kept = _filter_out_drawing_pdfs([drawings])
    assert kept == []


def test_filter_out_drawing_pdfs_keeps_large_project_manual(
    tmp_path: Path,
) -> None:
    """A LARGE (> 5 MB) project manual is now kept under --no-drawings —
    this was the second F-5 failure mode where big spec PDFs got excluded
    by the size proxy despite not being drawings.
    """
    manual = _make_pdf(
        tmp_path / "26-007 Carr EFA Dressing Room Renovation Project Manual.pdf",
        pages=[
            "GENERAL INSTRUCTIONS TO BIDDERS\n"
            "TABLE OF CONTENTS\nINVITATION TO BID\n"
            "DAVIS-BACON WAGE DETERMINATION\nGENERAL CONDITIONS",
            "filler text " * 100,
            "filler text " * 100,
        ],
        pad_to_bytes=6 * 1024 * 1024,  # > 5 MB
    )
    assert manual.stat().st_size > 5 * 1024 * 1024
    kept = _filter_out_drawing_pdfs([manual])
    assert kept == [manual], (
        "F-5 regression: a >5 MB project manual must NOT be dropped by "
        "--no-drawings (only true drawing sets should be filtered)."
    )


def test_filter_out_drawing_pdfs_mixed_corpus_size_boundary(
    tmp_path: Path,
) -> None:
    """Mixed corpus where drawings + non-drawings overlap the 5 MB boundary.

    Pre-F-5 (size filter): small-drawing kept (bug), large-manual dropped
    (bug). Post-F-5 (classifier): small-drawing dropped (correct), large-
    manual kept (correct). This is the canonical F-5 fixture.
    """
    small_drawing = _make_pdf(
        tmp_path / "B08_Solicitation_-_Att_2_-_Drawings.pdf",
        pages=["FLOOR PLAN\nSheet A-101"],
    )
    large_manual = _make_pdf(
        tmp_path / "Project_Manual.pdf",
        pages=[
            "GENERAL INSTRUCTIONS TO BIDDERS\nINVITATION TO BID\n"
            "DAVIS-BACON\nGENERAL CONDITIONS"
        ],
        pad_to_bytes=6 * 1024 * 1024,
    )
    small_bidform = _make_pdf(
        tmp_path / "Bid_Schedule_San_Marcos.pdf",
        pages=["BID SCHEDULE\nITEM 1 ... ITEM 2 ..."],
    )
    large_drawing = _make_pdf(
        tmp_path / "Drawings_Big.pdf",
        pages=["FLOOR PLAN\nSheet A-101"],
        pad_to_bytes=6 * 1024 * 1024,
    )

    assert small_drawing.stat().st_size < 5 * 1024 * 1024
    assert large_manual.stat().st_size > 5 * 1024 * 1024
    assert small_bidform.stat().st_size < 5 * 1024 * 1024
    assert large_drawing.stat().st_size > 5 * 1024 * 1024

    kept = set(_filter_out_drawing_pdfs(
        [small_drawing, large_manual, small_bidform, large_drawing]
    ))
    assert kept == {large_manual, small_bidform}, (
        f"F-5 regression: classifier should drop drawings of any size and "
        f"keep non-drawings of any size. Got: {kept}"
    )


def test_filter_out_drawing_pdfs_empty_input(tmp_path: Path) -> None:
    """No inputs → no outputs, no crash."""
    assert _filter_out_drawing_pdfs([]) == []


def test_filter_out_drawing_pdfs_keeps_malformed_pdf(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """A malformed PDF that fails classification must NOT be silently
    dropped — keep it so the operator surfaces a real I/O / encryption
    issue inside ``process_pdfs`` instead of seeing a stale empty corpus.
    """
    bad = tmp_path / "corrupt.pdf"
    bad.write_bytes(b"%PDF-1.4\n% intentionally corrupted")

    caplog.set_level(logging.WARNING)
    log = logging.getLogger("analyze")
    kept = _filter_out_drawing_pdfs([bad], log)
    assert kept == [bad]


# ---------------------------------------------------------------------------
# v5a follow-up: real-world miss cases (Carr EFA + Harrington Lab303)
# ---------------------------------------------------------------------------
#
# Calibration v5a (CALIBRATION_REPORT.md §F-5 note) flagged
# `t10_followup_classifier_hint_depth`: the 311-page Carr EFA Project
# Manual and the Harrington_Lab303_Specifications PDF classified as
# UNKNOWN under `--no-drawings` because the body-text hint sampler only
# looked at the first 3 pages. The follow-up fix samples first 5 +
# middle 5 + last 5 pages AND adds a filename signal for /spec/ and
# /project[-_\s]*manual|book/.
#
# These tests stub both miss cases (small page count, no body hints) and
# verify the filename signal alone keeps them under the classifier-based
# `--no-drawings` filter. We deliberately do NOT synthesise the actual
# 311-page bundle here -- that fixture lives in
# tests/test_pdf_processor_classifier_depth.py (deeper-sampling proof);
# this file just pins the analyze.py-level wiring.


def test_filter_out_drawing_pdfs_keeps_carr_efa_project_manual(
    tmp_path: Path,
) -> None:
    """Real-world Carr EFA filename: ``26-007 Carr EFA Dressing Room
    Renovation Project Manual.pdf``. Pre-follow-up, this slipped through
    as UNKNOWN under ``--no-drawings`` because the body-hint sampler
    only saw the front 3 pages. The filename signal now catches it
    regardless of where the body hints sit.
    """
    pdf = _make_pdf(
        tmp_path / "26-007 Carr EFA Dressing Room Renovation Project Manual.pdf",
        # No PROJECT_MANUAL hint phrases in body -- the filename signal
        # is what must keep this PDF in the kept set.
        pages=["Generic intro page without classifier hint phrases."]
        * 5,
    )
    kept = _filter_out_drawing_pdfs([pdf])
    assert kept == [pdf], (
        "v5a follow-up: Carr EFA Project Manual must be KEPT by "
        "--no-drawings (filename signal classifies it as PROJECT_MANUAL)."
    )


def test_filter_out_drawing_pdfs_keeps_harrington_lab303_specifications(
    tmp_path: Path,
) -> None:
    """Real-world Harrington Lab303 filename:
    ``Harrington_Lab303_Specifications.pdf``. Filename signal catches it
    even with a stub body devoid of canonical hint phrases.
    """
    pdf = _make_pdf(
        tmp_path / "Harrington_Lab303_Specifications.pdf",
        pages=["Generic intro page without classifier hint phrases."]
        * 5,
    )
    kept = _filter_out_drawing_pdfs([pdf])
    assert kept == [pdf], (
        "v5a follow-up: Harrington Lab303 Specifications must be KEPT "
        "by --no-drawings (filename signal classifies it as PROJECT_MANUAL)."
    )


def test_filter_out_drawing_pdfs_still_drops_drawings_with_spec_in_name(
    tmp_path: Path,
) -> None:
    """A drawing PDF whose name happens to contain "specifications" --
    e.g. ``roof_specifications_drawing.pdf`` -- must STILL be dropped
    under ``--no-drawings``. The drawing-set veto runs ahead of the
    new project-manual filename signal so this case stays classified
    as UNKNOWN.
    """
    pdf = _make_pdf(
        tmp_path / "roof_specifications_drawing.pdf",
        pages=["FLOOR PLAN\nSheet A-101"],
    )
    kept = _filter_out_drawing_pdfs([pdf])
    assert kept == [], (
        "Drawing-set veto must beat the new project-manual filename "
        "signal: a drawing PDF with 'specifications' in its name must "
        "still be filtered out by --no-drawings."
    )


# ---------------------------------------------------------------------------
# _filter_by_max_size_mb (new --max-pdf-mb rescue flag)
# ---------------------------------------------------------------------------


def test_filter_by_max_size_mb_recovers_legacy_5mb_behaviour(tmp_path: Path) -> None:
    """The old ``--no-drawings`` (size > 5 MB → drop) behaviour is reachable
    via ``--max-pdf-mb=5`` — verifies the rescue flag.
    """
    small = _make_pdf(tmp_path / "small.pdf", pages=["BID SCHEDULE"])
    big = _make_pdf(
        tmp_path / "big.pdf",
        pages=["GENERAL INSTRUCTIONS TO BIDDERS"],
        pad_to_bytes=6 * 1024 * 1024,
    )
    assert small.stat().st_size < 5 * 1024 * 1024
    assert big.stat().st_size > 5 * 1024 * 1024

    kept = _filter_by_max_size_mb([small, big], max_mb=5.0)
    assert kept == [small]


def test_filter_by_max_size_mb_zero_disables(tmp_path: Path) -> None:
    """Threshold ≤ 0 disables the filter (pass-through)."""
    small = _make_pdf(tmp_path / "small.pdf", pages=["x"])
    big = _make_pdf(tmp_path / "big.pdf", pages=["x"], pad_to_bytes=6 * 1024 * 1024)
    assert _filter_by_max_size_mb([small, big], max_mb=0.0) == [small, big]


# ---------------------------------------------------------------------------
# CLI help text contract
# ---------------------------------------------------------------------------


def _run_cli(args: list[str]) -> subprocess.CompletedProcess:
    here = Path(__file__).resolve().parents[1]
    cmd = [sys.executable, str(here / "analyze.py")] + args
    return subprocess.run(cmd, capture_output=True, text=True, cwd=here, timeout=60)


def test_cli_help_text_documents_classifier_semantic() -> None:
    """``analyze.py --help`` describes the new ``--no-drawings`` meaning."""
    result = _run_cli(["--help"])
    assert result.returncode == 0, (
        f"--help should exit 0; stdout=\n{result.stdout}\nstderr=\n{result.stderr}"
    )
    raw = result.stdout + result.stderr
    # argparse hard-wraps help lines at terminal width, so we collapse
    # whitespace before substring-matching the phrase.
    flat = " ".join(raw.split())
    assert "doc-level classifier" in flat, (
        "Help text must clarify --no-drawings is a classifier filter; got:\n"
        + raw
    )
    assert "not file size" in flat, (
        "Help text must explicitly say the filter is not size-based; got:\n"
        + raw
    )
    assert "--max-pdf-mb" in flat, "Rescue flag --max-pdf-mb must appear in --help."
    assert "--no-dedupe" in flat, (
        "Dedupe-opt-out flag --no-dedupe must appear in --help."
    )


def test_cli_help_text_avoids_legacy_size_phrasing() -> None:
    """The OLD help string (\"Skip large PDFs (>5 MB)\") would be a
    regression — the operator would still expect the size filter. Pin it
    out.
    """
    result = _run_cli(["--help"])
    assert result.returncode == 0
    out = result.stdout + result.stderr
    bad_phrasing = "Skip large PDFs (>5 MB)"
    assert bad_phrasing not in out, (
        f"--no-drawings help still claims the legacy size semantic "
        f"({bad_phrasing!r}); F-5 fix incomplete."
    )
