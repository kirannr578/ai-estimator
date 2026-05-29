"""Regression -- T10 calibration v4 finding F-2.

The client PDF builder (:func:`core.exporter_pdf.build_quote_pdf`) crashed
with reportlab's "Flowable too large on page ... in frame ..." error when
an estimate carried a :class:`core.schemas.BidPackage` with a
multi-thousand-character inclusion line. The offending bundle in the v4
calibration corpus was ``DDPM262101-Alter CP and NDI-SOW``, whose
aggregated scope-coverage cell rendered as a single ~1641-pt Paragraph
that overflowed a one-page Table cell.

Excel and JSON outputs were unaffected -- only the PDF render path. The
fix wraps user-supplied Paragraph cells in
:class:`reportlab.platypus.KeepInFrame` (mode ``'shrink'``) so a single
oversized cell shrinks to fit one page instead of aborting the build.

Coverage:

* positive -- single ~8000-char inclusion (the bug repro)
* edge -- 20 separate ~500-char inclusion paragraphs
* edge -- standard estimate still renders
* edge -- empty inclusion list still renders
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")
fitz = pytest.importorskip("fitz")  # PyMuPDF; already a project dep

from core.exporter_pdf import build_quote_pdf  # noqa: E402
from core.schemas import (  # noqa: E402
    BidPackage,
    CostCategory,
    CostLine,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    ScopeItem,
    SiteInfo,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix  # noqa: E402


def _project(
    *,
    bid_packages=None,
    aggregated_inclusions=None,
    aggregated_exclusions=None,
):
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=[],
        sheet_summaries={},
        warnings=[],
        bid_packages=bid_packages or [],
        project_info=ProjectInfo(
            name="F-2 Regression",
            number="2026-F2",
            location="Austin, TX",
        ),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=aggregated_inclusions or [],
        aggregated_exclusions=aggregated_exclusions or [],
    )


def _line(total=10_000.0):
    return CostLine(
        csi_division="09",
        csi_section="09 91 23",
        description="Painting",
        quantity=100.0,
        unit="SF",
        unit_cost=total / 100.0,
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


def _estimate():
    return Estimate(
        project_name="F-2 Regression",
        region_multiplier=1.0,
        line_items=[_line()],
    )


def _config():
    return QuoteConfig(
        quote_meta=QuoteMeta(
            scope_blurb="Test scope blurb.", payment_terms_text="Net 30."
        ),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="Mobilization", percentage=30.0),
                PaymentMilestone(label="Rough-in", percentage=40.0),
                PaymentMilestone(label="Finish", percentage=30.0),
            ],
        ),
    )


def _build(project, out_path):
    return build_quote_pdf(
        estimate=_estimate(),
        project=project,
        quote_config=_config(),
        out_path=out_path,
        csi_titles={"09": "Finishes"},
    )


def _read_pdf_text(pdf_path):
    with fitz.open(pdf_path) as doc:
        return "\n".join(page.get_text() for page in doc)


def _read_pdf_text_flat(pdf_path):
    return " ".join(_read_pdf_text(pdf_path).split())


_LONG_INCLUSION = (
    "Contractor shall furnish all labor, materials, equipment, supervision, "
    "permits, taxes, freight, hoisting, and incidentals required to fully "
    "execute the Alter CP and NDI Scope of Work as described in the bid "
    "documents and as further detailed in the following inclusion list. "
    "\u2022 Demolition of existing CP and NDI assemblies, including selective "
    "removal of partitions, ceilings, floor finishes, and associated "
    "mechanical, electrical, and plumbing rough-ins where indicated on the "
    "demolition drawings. "
    "\u2022 Salvage and protect-in-place any equipment, fixtures, or finishes "
    "designated for reuse; coordinate temporary storage and reinstallation "
    "with the General Contractor. "
    "\u2022 Furnish and install new CP and NDI assemblies per the architectural, "
    "structural, mechanical, electrical, plumbing, and fire-protection "
    "drawings, including all framing, sheathing, gypsum board, insulation, "
    "acoustical treatments, finishes, and accessories. "
    "\u2022 All cutting, patching, fireproofing, firestopping, and "
    "smoke-sealing of penetrations through fire-rated assemblies in "
    "accordance with UL listings and the project Code Summary. "
    "\u2022 Coordination with all other trades for blocking, backing, "
    "blocking-in-wall for equipment, hangers, supports, and anchor points; "
    "provide submittals and coordination drawings as required by the "
    "specifications and the GC's BIM execution plan. "
    "\u2022 Mock-ups and field samples as required by the specifications, "
    "including any third-party testing, certifications, and observation "
    "reports. "
    "\u2022 Punch-list completion within fourteen (14) calendar days of "
    "issuance; one-year warranty walk-through scheduled at substantial "
    "completion plus eleven months. "
) * 6


class TestLongInclusionRendersWithoutCrash:
    """The F-2 bug repro -- must not raise reportlab LayoutError."""

    def test_single_very_long_inclusion_renders(self, tmp_path: Path) -> None:
        """~8000-char inclusion text must produce a valid PDF, not crash."""
        bp = BidPackage(
            pdf_name="DDPM262101-Alter CP and NDI-SOW.pdf",
            package_number="01.00",
            trade_name="Alter CP and NDI",
            inclusions=[_LONG_INCLUSION],
        )
        project = _project(
            bid_packages=[bp],
            aggregated_inclusions=[
                ScopeItem(text=_LONG_INCLUSION, source_packages=[bp.pdf_name])
            ],
        )

        out = tmp_path / "long_inclusion.pdf"
        result = _build(project, out)

        assert result.is_file(), "PDF was not written"
        size = out.stat().st_size
        assert size > 1024, f"PDF unexpectedly small ({size} bytes)"
        head = out.read_bytes()[:5]
        assert head == b"%PDF-", "PDF header missing"

        text = _read_pdf_text(out)
        assert "Scope coverage" in text
        assert "Contractor shall furnish all labor" in text


class TestMultipleLongParagraphsRender:
    """20 separate ~500-char paragraphs -- each fits, but in aggregate they
    drive a tall cell. Must still render cleanly."""

    def test_twenty_500_char_inclusions_render(self, tmp_path: Path) -> None:
        sentence = (
            "Furnish and install miscellaneous accessories and incidentals "
            "required to complete the scope of work, including all "
            "coordination with adjacent trades, third-party testing, "
            "and one-year warranty coverage on installed assemblies. "
        )
        long_para = (sentence * 2)[:500]
        inclusions_text = [f"{long_para} (item #{i + 1})" for i in range(20)]
        bp = BidPackage(
            pdf_name="multi-paragraph-sow.pdf",
            inclusions=inclusions_text,
        )
        project = _project(
            bid_packages=[bp],
            aggregated_inclusions=[
                ScopeItem(text=t, source_packages=[bp.pdf_name])
                for t in inclusions_text
            ],
        )

        out = tmp_path / "multi_para.pdf"
        result = _build(project, out)

        assert result.is_file()
        assert out.stat().st_size > 1024
        text = _read_pdf_text(out)
        assert "Scope coverage" in text
        flat = _read_pdf_text_flat(out)
        assert "item #20" in flat


def test_standard_estimate_without_long_text_still_renders(
    tmp_path: Path,
) -> None:
    """The defensive KeepInFrame wrapping must not regress short text."""
    project = _project(
        aggregated_inclusions=[
            ScopeItem(text="Furnish and install all painting.", source_packages=["a"]),
            ScopeItem(text="All necessary access and protection.", source_packages=["a"]),
        ],
        aggregated_exclusions=[
            ScopeItem(text="Hazardous material abatement.", source_packages=["a"]),
        ],
    )
    out = tmp_path / "standard.pdf"
    result = _build(project, out)

    assert result.is_file()
    assert out.stat().st_size > 1024
    text = _read_pdf_text(out)
    assert "Furnish and install all painting." in text
    assert "Hazardous material abatement." in text


def test_empty_inclusion_list_does_not_crash(tmp_path: Path) -> None:
    """No aggregated inclusions/exclusions still renders the section."""
    project = _project(aggregated_inclusions=[], aggregated_exclusions=[])
    out = tmp_path / "empty.pdf"
    result = _build(project, out)

    assert result.is_file()
    assert out.stat().st_size > 1024
    head = out.read_bytes()[:5]
    assert head == b"%PDF-"
    text = _read_pdf_text(out)
    assert "Scope coverage" in text
