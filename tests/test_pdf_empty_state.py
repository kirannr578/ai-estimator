"""Tests for the calibration-v3 PDF empty-state banner (Item 3).

When every `CostLine` in an `Estimate` is suppressed (or there are no
lines at all), the client-quote PDF used to render three $0.00 tiles in
the executive summary — Labor $0.00 / Material $0.00 / Subcontractor
$0.00. That looks broken, like the firm couldn't price anything. The
empty-state banner replaces those three tiles with a single explanatory
soft-warning block.

These tests confirm:
  * `_is_priced_estimate_empty` fires when (a) every line is suppressed,
    (b) the line list is empty entirely
  * `_is_priced_estimate_empty` does NOT fire on a normal partially-priced
    estimate
  * The rendered PDF contains the banner sentinel text when the empty
    state fires, and does NOT contain it on a normal estimate
  * The three $0.00 tiles do NOT appear when the banner fires (no
    "$0.00\\n$0.00\\n$0.00" pattern)

We avoid a hard dependency on `pdfplumber` and inspect the rendered byte
stream directly — reportlab embeds Paragraph text verbatim in the
content stream so a substring scan is reliable for sentinel checks.
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")

from core.exporter_pdf import (  # noqa: E402
    EMPTY_STATE_BANNER_TEXT,
    _is_priced_estimate_empty,
    build_quote_pdf,
)
from core.schemas import (  # noqa: E402
    CostCategory,
    CostLine,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    SiteInfo,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix  # noqa: E402


# ---------------------------------------------------------------------------
# Predicate behavior
# ---------------------------------------------------------------------------


def _make_line(suppressed: bool, total: float = 1000.0) -> CostLine:
    return CostLine(
        csi_division="03",
        csi_section="03 30 00",
        description="Test line",
        quantity=10.0,
        unit="SF",
        unit_cost=total / 10.0 if not suppressed else 0.0,
        total_cost=total if not suppressed else 0.0,
        cost_category=CostCategory.MATERIAL,
        suppressed=suppressed,
    )


def test_predicate_fires_when_every_line_suppressed() -> None:
    est = Estimate(
        project_name="all-suppressed",
        line_items=[_make_line(suppressed=True), _make_line(suppressed=True)],
    )
    assert _is_priced_estimate_empty(est)


def test_predicate_fires_when_no_lines_at_all() -> None:
    est = Estimate(project_name="empty", line_items=[])
    assert _is_priced_estimate_empty(est)


def test_predicate_does_not_fire_on_mixed_estimate() -> None:
    """At least one priced line => not empty (normal three-tile path runs)."""
    est = Estimate(
        project_name="mixed",
        line_items=[
            _make_line(suppressed=False, total=5000.0),
            _make_line(suppressed=True),
        ],
    )
    assert not _is_priced_estimate_empty(est)


def test_predicate_does_not_fire_on_fully_priced_estimate() -> None:
    est = Estimate(
        project_name="all-priced",
        line_items=[_make_line(suppressed=False, total=1000.0)],
    )
    assert not _is_priced_estimate_empty(est)


# ---------------------------------------------------------------------------
# PDF rendering — banner appears vs three tiles
# ---------------------------------------------------------------------------


def _minimal_project() -> ProjectModel:
    return ProjectModel(
        rooms=[], doors=[], windows=[], structural=[], mep=[], spec_sections=[],
        site=SiteInfo(), takeoffs=[], sheet_summaries={}, warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(name="X", number="0"),
        scope_matrix=ScopeMatrix(packages=[], by_division={}, all_alternates=[], coverage_warnings=[]),
        aggregated_inclusions=[], aggregated_exclusions=[],
    )


def _default_config() -> QuoteConfig:
    return QuoteConfig(
        quote_meta=QuoteMeta(scope_blurb="x"),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[PaymentMilestone(label="Done", percentage=100.0)],
        ),
    )


def _pdf_text(pdf_path: Path) -> str:
    """Return the extracted text of every page concatenated.

    Uses PyMuPDF (already a project dependency, no new install) so we can
    reliably check for sentinel strings even when the rendered text uses
    non-ASCII glyphs like em-dash. A pure byte-level scan of the PDF
    stream is unreliable because reportlab's Type 1 fonts encode
    non-ASCII codepoints under WinAnsiEncoding, not literal UTF-8.
    """
    import fitz  # PyMuPDF
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _pdf_text_contains(pdf_path: Path, needle: str) -> bool:
    return needle in _pdf_text(pdf_path)


def test_all_suppressed_estimate_renders_empty_state_banner(tmp_path: Path) -> None:
    """All lines suppressed => banner present, no three $0.00 tiles."""
    est = Estimate(
        project_name="All Suppressed",
        line_items=[
            _make_line(suppressed=True),
            _make_line(suppressed=True),
            _make_line(suppressed=True),
        ],
    )
    out = tmp_path / "all_suppressed.pdf"
    build_quote_pdf(
        estimate=est,
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
    )
    assert out.is_file()
    assert out.read_bytes()[:5] == b"%PDF-"

    assert _pdf_text_contains(out, EMPTY_STATE_BANNER_TEXT), \
        f"Empty-state banner text missing from PDF: {EMPTY_STATE_BANNER_TEXT!r}"

    # The three Labor/Material/Subcontractor tile labels must NOT be
    # rendered when the banner fires — they'd otherwise show "$0.00 / $0.00
    # / $0.00" which is the broken-looking output we're replacing.
    text = _pdf_text(out)
    tile_labels_present = sum(
        1 for label in ("LABOR", "MATERIAL", "SUBCONTRACTOR") if label in text
    )
    assert tile_labels_present == 0, (
        "Three-tile labels rendered alongside the empty-state banner — "
        "banner must replace, not coexist"
    )


def test_normal_mixed_estimate_renders_three_tiles_not_banner(tmp_path: Path) -> None:
    """Mixed priced + suppressed => three tiles present, no banner."""
    est = Estimate(
        project_name="Mixed",
        line_items=[
            _make_line(suppressed=False, total=5000.0),
            _make_line(suppressed=False, total=2500.0),
            _make_line(suppressed=True),
        ],
    )
    out = tmp_path / "mixed.pdf"
    build_quote_pdf(
        estimate=est,
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
    )
    assert out.is_file()
    assert out.read_bytes()[:5] == b"%PDF-"

    assert not _pdf_text_contains(out, EMPTY_STATE_BANNER_TEXT), \
        "Empty-state banner fired on a partially-priced estimate (should only fire when all lines are suppressed)"


def test_zero_lines_estimate_also_triggers_empty_state_banner(tmp_path: Path) -> None:
    """No CostLines at all => banner present (because total is $0 with no priced lines)."""
    est = Estimate(project_name="No Lines", line_items=[])
    out = tmp_path / "no_lines.pdf"
    build_quote_pdf(
        estimate=est,
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
    )
    assert out.is_file()
    assert _pdf_text_contains(out, EMPTY_STATE_BANNER_TEXT), \
        "Empty-state banner should fire when there are zero priced lines at all"
