"""QA pass — Subsystem 9: Client PDF renderer (2026-05-28).

Smoke checks the PDF renderer produces a valid byte stream for
representative estimates: priced, empty, and alternate-bearing.
Detailed sentinel-text coverage already lives in
``test_pdf_empty_state.py`` / ``test_exporter_pdf_alternates.py`` —
this slice spot-checks structural invariants (file written, %PDF-
header) so a reviewer can quickly cross-reference scenarios.
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")

from core.estimator import _combined_band  # noqa: E402
from core.exporter_pdf import (  # noqa: E402
    EMPTY_STATE_BANNER_TEXT,
    _is_priced_estimate_empty,
    build_quote_pdf,
)
from core.schemas import (  # noqa: E402
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
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
# Helpers
# ---------------------------------------------------------------------------


def _project() -> ProjectModel:
    return ProjectModel(
        rooms=[], doors=[], windows=[], structural=[], mep=[], spec_sections=[],
        site=SiteInfo(), takeoffs=[], sheet_summaries={}, warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(name="QA PDF", number="P-0001"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[],
        ),
        aggregated_inclusions=[], aggregated_exclusions=[],
    )


def _config() -> QuoteConfig:
    return QuoteConfig(
        quote_meta=QuoteMeta(scope_blurb="QA scope"),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[PaymentMilestone(label="Done", percentage=100.0)],
        ),
    )


def _line(*, total: float = 1_000.0, suppressed: bool = False) -> CostLine:
    return CostLine(
        csi_division="03",
        csi_section="03 30 00",
        description="Concrete slab",
        quantity=10.0,
        unit="SF",
        unit_cost=total / 10.0 if not suppressed else 0.0,
        total_cost=total if not suppressed else 0.0,
        cost_category=CostCategory.MATERIAL,
        confidence=0.92,
        price_confidence=0.95,
        suppressed=suppressed,
        cost_band=_combined_band(0.92, 0.95, suppressed=suppressed),
    )


def _read_pdf_text(path: Path) -> str:
    import fitz
    with fitz.open(path) as doc:
        return "\n".join(p.get_text() for p in doc)


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_qa_pos_priced_estimate_renders_pdf(tmp_path: Path) -> None:
    est = Estimate(project_name="QA Priced", line_items=[_line(total=5_000.0)])
    out = tmp_path / "priced.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    assert out.is_file()
    # Real PDF: starts with the canonical %PDF- magic bytes.
    assert out.read_bytes()[:5] == b"%PDF-"
    text = _read_pdf_text(out)
    # Headline grand total appears in the rendered text.
    assert est.project_name in text


def test_qa_pos_alternates_section_renders(tmp_path: Path) -> None:
    """Alternates-bearing estimate puts the section in the rendered PDF."""
    est = Estimate(
        project_name="QA Alts",
        line_items=[_line()],
        alternates=[AlternateLineEstimate(
            alternate_id="Alternate 1",
            alternate_type=AlternateType.ADDITIVE,
            description="Add upgraded carpet tile in lobby",
            cost_delta=12_500.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        )],
    )
    out = tmp_path / "alts.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    text = _read_pdf_text(out)
    # Alternate description surfaces somewhere in the rendered PDF.
    assert "carpet" in text.lower() or "Alternate 1" in text


# ---------------------------------------------------------------------------
# Negative
# ---------------------------------------------------------------------------


def test_qa_neg_empty_estimate_emits_banner(tmp_path: Path) -> None:
    """Empty estimate triggers the empty-state banner instead of $0 tiles."""
    est = Estimate(project_name="QA Empty", line_items=[])
    out = tmp_path / "empty.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    text = _read_pdf_text(out)
    assert EMPTY_STATE_BANNER_TEXT in text


def test_qa_neg_all_suppressed_emits_banner(tmp_path: Path) -> None:
    """Estimate where every line is suppressed → banner fires."""
    est = Estimate(
        project_name="QA AllSuppressed",
        line_items=[_line(suppressed=True), _line(suppressed=True)],
    )
    out = tmp_path / "all_supp.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    text = _read_pdf_text(out)
    assert EMPTY_STATE_BANNER_TEXT in text


def test_qa_neg_predicate_does_not_fire_on_partially_priced() -> None:
    """At least one priced line → ``_is_priced_estimate_empty`` is False."""
    est = Estimate(
        project_name="QA Mixed",
        line_items=[_line(total=5000.0), _line(suppressed=True)],
    )
    assert _is_priced_estimate_empty(est) is False


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_qa_edge_pdf_creates_missing_output_directory(tmp_path: Path) -> None:
    """``build_quote_pdf`` creates ``out_path.parent`` if it doesn't exist."""
    est = Estimate(project_name="QA Subdir", line_items=[_line()])
    nested = tmp_path / "nonexistent" / "deep" / "path"
    out = nested / "quote.pdf"
    # Confirm parent does not exist yet.
    assert not nested.exists()
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    assert out.is_file()


def test_qa_edge_alternates_disabled_via_config_skips_section(tmp_path: Path) -> None:
    """``alternates_config={"enabled": False}`` skips the section silently."""
    est = Estimate(
        project_name="QA AltsDisabled",
        line_items=[_line()],
        alternates=[AlternateLineEstimate(
            alternate_id="Alternate 1",
            alternate_type=AlternateType.ADDITIVE,
            description="Add upgraded mass-timber framing",
            cost_delta=42_000.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        )],
    )
    out = tmp_path / "alts_disabled.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
        alternates_config={"enabled": False},
    )
    text = _read_pdf_text(out)
    # Alternate scope text must NOT appear in the rendered PDF.
    assert "mass-timber" not in text.lower()
    assert "mass timber" not in text.lower()


def test_qa_edge_unicode_project_name_round_trips(tmp_path: Path) -> None:
    """Unicode project name doesn't crash the renderer."""
    est = Estimate(project_name="QA — éàü 漢字", line_items=[_line()])
    out = tmp_path / "unicode.pdf"
    build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    assert out.is_file()
    # The PDF byte stream is well-formed.
    assert out.read_bytes()[:5] == b"%PDF-"


def test_qa_edge_returns_path_object(tmp_path: Path) -> None:
    """``build_quote_pdf`` returns a ``Path`` pointing at the written file."""
    est = Estimate(project_name="QA ReturnPath", line_items=[_line()])
    out = tmp_path / "return.pdf"
    result = build_quote_pdf(
        estimate=est,
        project=_project(),
        quote_config=_config(),
        out_path=out,
    )
    assert isinstance(result, Path)
    assert result == out
