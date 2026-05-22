"""Smoke test for the client-quote PDF builder (F12/F15).

Builds a PDF against a hand-crafted minimal `Estimate` + `ProjectModel` and
asserts that:
  * the file is non-empty (reportlab actually wrote bytes)
  * the byte stream starts with the PDF magic header `%PDF-`

This is intentionally a single, fast test — the full layout is exercised
visually by the user via the Streamlit "Client Quote" tab.
"""

from __future__ import annotations

from pathlib import Path

import pytest

reportlab = pytest.importorskip("reportlab")  # skip cleanly if not installed

from core.exporter_pdf import build_quote_pdf  # noqa: E402
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


def _minimal_project() -> ProjectModel:
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
        bid_packages=[],
        project_info=ProjectInfo(
            name="Sample Renovation",
            number="2026-001",
            location="Austin, TX",
        ),
        scope_matrix=ScopeMatrix(packages=[], by_division={}, all_alternates=[], coverage_warnings=[]),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _minimal_estimate() -> Estimate:
    return Estimate(
        project_name="Sample Renovation",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            CostLine(
                csi_division="03",
                csi_section="03 30 00",
                description="Slab on grade",
                quantity=1000.0,
                unit="SF",
                unit_cost=8.50,
                total_cost=8500.0,
                cost_category=CostCategory.MATERIAL,
            ),
            CostLine(
                csi_division="06",
                csi_section="06 10 00",
                description="Wood framing",
                quantity=1000.0,
                unit="SF",
                unit_cost=12.00,
                total_cost=12000.0,
                cost_category=CostCategory.LABOR,
            ),
            CostLine(
                csi_division="22",
                csi_section="22 40 00",
                description="Plumbing fixtures",
                quantity=8.0,
                unit="EA",
                unit_cost=950.0,
                total_cost=7600.0,
                cost_category=CostCategory.SUBCONTRACTOR,
            ),
        ],
    )


def _default_config() -> QuoteConfig:
    return QuoteConfig(
        quote_meta=QuoteMeta(scope_blurb="Test scope blurb.", payment_terms_text="Net 30."),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="Mobilization", percentage=30.0, notes="At NTP"),
                PaymentMilestone(label="Rough-in",     percentage=30.0, notes="At rough-in"),
                PaymentMilestone(label="Finish",       percentage=30.0, notes="Substantial completion"),
                PaymentMilestone(label="Retainage",    percentage=10.0, notes="After acceptance"),
            ],
        ),
    )


def test_build_quote_pdf_writes_non_empty_file(tmp_path: Path) -> None:
    out = tmp_path / "quote.pdf"
    result = build_quote_pdf(
        estimate=_minimal_estimate(),
        project=_minimal_project(),
        quote_config=_default_config(),
        out_path=out,
        csi_titles={"03": "Concrete", "06": "Wood, Plastics, and Composites", "22": "Plumbing"},
    )
    assert result == out
    assert out.is_file()
    size = out.stat().st_size
    assert size > 5000, f"PDF suspiciously small ({size} bytes)"
    head = out.read_bytes()[:5]
    assert head == b"%PDF-", f"output is not a valid PDF (header={head!r})"


def test_payment_schedule_percentage_validator() -> None:
    """Sum-to-100 invariant must fail on bad percentages."""
    with pytest.raises(ValueError, match="must sum to 100"):
        PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="A", percentage=40.0),
                PaymentMilestone(label="B", percentage=40.0),
            ],
        )


def test_payment_schedule_milestone_total_warning() -> None:
    sched = PaymentSchedule(
        mode="milestone",
        milestones=[
            PaymentMilestone(label="Deposit", amount=1000.0),
            PaymentMilestone(label="Final",   amount=1000.0),
        ],
    )
    warns = sched.validate_against_total(5000.0)
    assert warns, "Expected a warning when amounts don't cover contract total"
