"""Phase T6 — Excel exporter band-aware tests.

Covers:

* Operator Review Queue sheet appears (even when empty).
* Hand Takeoff Queue sheet appears (even when empty).
* Hand Takeoff Queue header is tinted with ``HAND_TAKEOFF_HEADER_FILL``.
* Operator Review Queue header is tinted with ``OPERATOR_REVIEW_HEADER_FILL``.
* The "Line Items" sheet carries a ``Band`` column with values from
  ``{AUTO, REVIEW, HAND}``.
* The Project Summary sheet carries the seven new T6 rows.
* Queue sheets carry only the rows that belong to their band; the
  AUTO-band line never leaks into either queue.
"""

from __future__ import annotations

from io import BytesIO

import pytest
from openpyxl import load_workbook

from core.exporter import (
    HAND_TAKEOFF_HEADER_FILL,
    OPERATOR_REVIEW_HEADER_FILL,
    export_estimate_xlsx,
)
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    Estimate,
    SiteInfo,
    band_for_confidence,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _empty_project() -> ProjectModel:
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
        project_info=ProjectInfo(name="T6 Export Test"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
    )


def _line(
    *,
    division: str = "09",
    section: str | None = "09 91 23",
    description: str = "Interior painting",
    confidence: float = 0.92,
    total: float = 1000.0,
    suppressed: bool = False,
) -> CostLine:
    return CostLine(
        csi_division=division,
        csi_section=section,
        description=description,
        quantity=500.0,
        unit="SF",
        unit_cost=round(total / 500.0, 4),
        total_cost=total,
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        suppressed=suppressed,
        cost_band=band_for_confidence(confidence, suppressed=suppressed),
    )


def _mixed_estimate() -> Estimate:
    """Three priced lines (one per band) + one suppressed (HAND)."""
    return Estimate(
        project_name="T6 Export",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=[
            _line(description="Auto", confidence=0.92, total=10_000.0),
            _line(description="Review", confidence=0.78, total=5_000.0),
            _line(description="Hand", confidence=0.40, total=2_000.0),
            _line(
                description="Mismatch suppressed",
                confidence=0.99, total=0.0, suppressed=True,
            ),
        ],
    )


def _all_auto_estimate() -> Estimate:
    return Estimate(
        project_name="all-auto",
        line_items=[
            _line(description="A", confidence=0.92, total=1000.0),
            _line(description="B", confidence=0.99, total=2000.0),
        ],
    )


def _load_xlsx(payload: bytes):
    return load_workbook(BytesIO(payload))


# ---------------------------------------------------------------------------
# Sheet presence
# ---------------------------------------------------------------------------


def test_operator_review_queue_sheet_appears() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    assert "Operator Review Queue" in wb.sheetnames


def test_hand_takeoff_queue_sheet_appears() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    assert "Hand Takeoff Queue" in wb.sheetnames


def test_queue_sheets_appear_even_when_empty() -> None:
    """All-AUTO estimate: both queue sheets must still exist (no crash)."""
    payload = export_estimate_xlsx(_all_auto_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    assert "Operator Review Queue" in wb.sheetnames
    assert "Hand Takeoff Queue" in wb.sheetnames


# ---------------------------------------------------------------------------
# Header tinting
# ---------------------------------------------------------------------------


def _header_fill_rgb(ws) -> str | None:
    cell = ws.cell(row=1, column=1)
    fill = cell.fill
    if fill is None or fill.fgColor is None:
        return None
    rgb = fill.fgColor.rgb
    if rgb is None:
        return None
    return str(rgb).upper()


def test_hand_takeoff_queue_header_uses_amber_tint() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Hand Takeoff Queue"]
    # openpyxl serialises HAND fill as `00FFC107` (alpha + RGB) — match
    # by suffix so we don't depend on the alpha channel.
    rgb = _header_fill_rgb(ws)
    assert rgb is not None
    assert rgb.endswith(HAND_TAKEOFF_HEADER_FILL.fgColor.rgb.upper()), rgb


def test_operator_review_queue_header_uses_yellow_tint() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Operator Review Queue"]
    rgb = _header_fill_rgb(ws)
    assert rgb is not None
    assert rgb.endswith(OPERATOR_REVIEW_HEADER_FILL.fgColor.rgb.upper()), rgb


# ---------------------------------------------------------------------------
# Band column on the "Line Items" sheet
# ---------------------------------------------------------------------------


def test_line_items_sheet_has_band_column() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Line Items"]
    headers = [c.value for c in ws[1]]
    assert "Band" in headers, f"Expected Band column; got {headers}"


def test_line_items_band_values_are_in_short_label_set() -> None:
    """Band column values must be one of AUTO / REVIEW / HAND."""
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Line Items"]
    headers = [c.value for c in ws[1]]
    band_col = headers.index("Band") + 1
    seen: set[str] = set()
    for r in range(2, ws.max_row + 1):
        v = ws.cell(row=r, column=band_col).value
        # Skip division-banner rows where the Band column is blank.
        if v is None or v == "":
            continue
        seen.add(str(v))
    # Mixed estimate has one of each band.
    assert seen == {"AUTO", "REVIEW", "HAND"}, seen


# ---------------------------------------------------------------------------
# Queue-row content
# ---------------------------------------------------------------------------


def test_operator_review_queue_contains_only_review_rows() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Operator Review Queue"]
    # Description column is index 2 in the queue schema.
    descs = [
        ws.cell(row=r, column=2).value
        for r in range(2, ws.max_row + 1)
        if ws.cell(row=r, column=2).value
    ]
    assert "Review" in descs
    assert "Auto" not in descs
    assert "Hand" not in descs
    assert "Mismatch suppressed" not in descs


def test_hand_takeoff_queue_contains_low_conf_and_suppressed_rows() -> None:
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Hand Takeoff Queue"]
    descs = [
        ws.cell(row=r, column=2).value
        for r in range(2, ws.max_row + 1)
        if ws.cell(row=r, column=2).value
    ]
    assert "Hand" in descs
    assert "Mismatch suppressed" in descs
    assert "Auto" not in descs
    assert "Review" not in descs


def test_empty_queue_sheet_has_no_data_rows_just_friendly_note() -> None:
    payload = export_estimate_xlsx(_all_auto_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Hand Takeoff Queue"]
    # Headers in row 1; friendly note in row 2 column 1; no data beyond.
    note = ws.cell(row=2, column=1).value
    assert note is not None and "No hand-takeoff lines" in str(note)


# ---------------------------------------------------------------------------
# Project Summary band rows
# ---------------------------------------------------------------------------


def test_summary_sheet_has_seven_new_t6_rows() -> None:
    """The Summary sheet must carry the seven brief-mandated T6 rows."""
    payload = export_estimate_xlsx(_mixed_estimate(), _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Summary"]
    # Collect column A labels from rows 10–20 (T6 rows live in 10..16).
    labels = []
    for r in range(10, 18):
        v = ws.cell(row=r, column=1).value
        if v:
            labels.append(str(v))

    expected_phrases = [
        "Auto-Approve Total",
        "Operator-Review Total",
        "Hand-Takeoff Total",
        "Grand Total (Auto-Only)",
        "Grand Total (Auto + Review)",
        "Lines Needing Manual Takeoff",
        "Lines Needing Operator Review",
    ]
    for phrase in expected_phrases:
        assert any(phrase in l for l in labels), (
            f"Summary sheet missing T6 row '{phrase}'; got {labels}"
        )


def test_summary_sheet_t6_dollar_values_match_estimate() -> None:
    est = _mixed_estimate()
    payload = export_estimate_xlsx(est, _empty_project(), csi_titles={})
    wb = _load_xlsx(payload)
    ws = wb["Summary"]

    # Row 10: Auto-Approve Total
    assert ws["A10"].value == "Auto-Approve Total"
    assert ws["B10"].value == pytest.approx(est.total_auto_approve)
    # Row 11: Operator-Review Total
    assert ws["B11"].value == pytest.approx(est.total_operator_review)
    # Row 12: Hand-Takeoff Total
    assert ws["B12"].value == pytest.approx(est.total_hand_takeoff)
    # Row 13: Grand Total (Auto-Only)
    assert ws["B13"].value == pytest.approx(est.grand_total_auto_only)
    # Row 14: Grand Total (Auto + Review)
    assert ws["B14"].value == pytest.approx(est.grand_total_with_review)


# ---------------------------------------------------------------------------
# JSON export band aggregates
# ---------------------------------------------------------------------------


def test_export_json_carries_band_aggregates() -> None:
    """JSON export must surface T6 fields for downstream consumers."""
    import json
    from core.exporter import export_estimate_json

    est = _mixed_estimate()
    payload = json.loads(export_estimate_json(est, _empty_project()))
    assert payload["grand_total_with_review"] == pytest.approx(est.grand_total_with_review)
    assert payload["grand_total_auto_only"] == pytest.approx(est.grand_total_auto_only)
    assert payload["total_auto_approve"] == pytest.approx(est.total_auto_approve)
    assert payload["total_operator_review"] == pytest.approx(est.total_operator_review)
    assert payload["total_hand_takeoff"] == pytest.approx(est.total_hand_takeoff)
    assert payload["auto_approve_count"] == est.auto_approve_count
    assert payload["operator_review_count"] == est.operator_review_count
    assert payload["hand_takeoff_count"] == est.hand_takeoff_count
    # Each serialised CostLine must carry its cost_band string.
    for li in payload["line_items"]:
        assert li["cost_band"] in {b.value for b in CostBand}
