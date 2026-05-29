"""QA-2 subsystem 6 — batch override + sub-quote ingestion.

Worker YY-2 / Pair 25 / subsystem 6 of the QA decomposition. Covers:

* CSV parsing (vendor pricing) → :class:`BatchOverrideRow` + plan
* Multi-sheet xlsx parsing → per-sheet plans + flattened merge
* Tabular sub-quote PDF parsing (T8.1 deterministic path)
* T6.4.b UoM-aware matcher: compat-group + cross-dimension rejection
* T6.4.c source-tag propagation: ``[vendor-csv]`` / ``[sub-quote]`` /
  ``[sub-quote-llm]`` always at position 0 of ``CostLine.notes`` with
  prior provenance preserved as ``| previous: …`` suffix.
* Negative paths: malformed CSV (raises ``ValueError``), xlsx-shaped
  garbage bytes (raises ``ValueError``).

LLM mocking pattern (T8.2 LLM-vision sub-quote): the
:class:`_StubLLMClient` mirrors :class:`core.llm_client.LLMClient`'s
surface so production code consumes it transparently. NO real LLM
calls. NO network. Uses ``reportlab.platypus`` for PDF construction
(same approach as ``tests/test_subquote_parser.py`` and
``tests/test_subquote_llm_fallback.py``).
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

reportlab = pytest.importorskip("reportlab")

from openpyxl import Workbook  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.estimator import apply_manual_override  # noqa: E402
from core.pricing.batch_override import (  # noqa: E402
    SOURCE_TAG_BATCH,
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
    BatchMatchStatus,
    apply_batch_plan,
    match_cost_lines,
    parse_vendor_csv,
    uoms_compatible,
)
from core.pricing.subquote_parser import (  # noqa: E402
    apply_subquote_plan,
    parse_subquote_pdf,
)
from core.pricing.xlsx_parser import (  # noqa: E402
    merge_xlsx_plans,
    parse_vendor_xlsx,
)
from core.schemas import CostCategory, CostLine, Estimate  # noqa: E402


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _line(
    *,
    description: str,
    unit: str = "SF",
    unit_cost: float = 4.00,
    quantity: float = 100.0,
    csi_section: str = "09 91 23",
) -> CostLine:
    return CostLine(
        csi_division=csi_section.split()[0],
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit=unit,
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.92,
    )


def _estimate(*lines: CostLine) -> Estimate:
    return Estimate(project_name="QA-2 Overrides", line_items=list(lines))


# ---------------------------------------------------------------------------
# PDF builders (lifted from existing tests/test_subquote_parser.py pattern)
# ---------------------------------------------------------------------------


def _build_pdf_with_table(
    rows: list[list[str]], *, preamble: list[str] | None = None
) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow: list = []
    if preamble:
        for text in preamble:
            flow.append(Paragraph(text, styles["Normal"]))
        flow.append(Spacer(1, 12))
    t = Table(rows)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    flow.append(t)
    doc.build(flow)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Stub LLM client (mirrors tests/test_subquote_llm_fallback.py pattern)
# ---------------------------------------------------------------------------


@dataclass
class _StubLLMResponse:
    parsed: Any
    text: str = ""
    provider: str = "stub"
    model: str = "stub-model"


class _StubLLMClient:
    """Mock of :class:`core.llm_client.LLMClient` for sub-quote LLM tests."""

    def __init__(self, responses: list[Any]) -> None:
        self.responses = list(responses)
        self.calls: list[dict[str, Any]] = []

    def analyze_image(
        self,
        image_path: str,
        system_prompt: str,
        user_prompt: str,
        extra_context: str = "",
    ) -> _StubLLMResponse:
        self.calls.append({"image_path": image_path})
        if not self.responses:
            raise RuntimeError("Stub exhausted")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return _StubLLMResponse(parsed=nxt, text="")


# ---------------------------------------------------------------------------
# Multi-sheet xlsx builder
# ---------------------------------------------------------------------------


def _build_xlsx_bytes(sheets: dict[str, list[list[Any]]]) -> bytes:
    """Build an in-memory xlsx workbook from {sheet_name: rows}."""
    wb = Workbook()
    # Drop the default sheet — we build named sheets explicitly.
    wb.remove(wb.active)
    for name, rows in sheets.items():
        ws = wb.create_sheet(title=name)
        for row in rows:
            ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Positive scenarios
# ---------------------------------------------------------------------------


class TestQAOverridesPositive:
    """Three positive scenarios covering CSV / xlsx / sub-quote PDF paths."""

    def test_qa_overrides_p1_csv_apply_stamps_vendor_csv_tag(self) -> None:
        """POS-1: a clean vendor CSV parses, matches to an estimate line,
        and ``apply_batch_plan(source_tag=SOURCE_TAG_VENDOR_CSV)`` stamps
        ``[vendor-csv]`` at position 0 of the line's notes."""
        csv_text = (
            "description,unit_cost,vendor,quote_ref,quantity,unit\n"
            "Interior latex paint walls,3.85,SubX Painting,Q-1234,100,SF\n"
        )
        rows, errors = parse_vendor_csv(csv_text)
        assert len(rows) == 1
        assert errors == []
        assert rows[0].vendor == "SubX Painting"
        est = _estimate(_line(description="Interior latex paint, walls"))
        plan = match_cost_lines(rows, est.line_items)
        assert len(plan.matched) == 1
        new_est, summary = apply_batch_plan(
            est, plan, source_tag=SOURCE_TAG_VENDOR_CSV
        )
        line = new_est.line_items[0]
        assert line.notes is not None
        assert line.notes.startswith(SOURCE_TAG_VENDOR_CSV + " ")
        assert line.unit_cost == pytest.approx(3.85, abs=0.01)
        # The matched-row summary line surfaces what was applied.
        assert any("APPLIED to line #0" in s for s in summary)

    def test_qa_overrides_p2_multi_sheet_xlsx_merged_with_provenance(
        self,
    ) -> None:
        """POS-2: a 3-sheet xlsx parses to 3 plans; the merge flattens
        them into one plan with sheet-provenance prefixed to each row's
        ``notes`` field. Row indices renumber monotonically across sheets."""
        sheets = {
            "Mechanical": [
                ["Description", "Unit Cost", "Unit", "Vendor"],
                ["Air handler unit", 4500.00, "EA", "Vendor M"],
            ],
            "Electrical": [
                ["Description", "Unit Cost", "Unit", "Vendor"],
                ["Branch circuit wiring", 12.50, "LF", "Vendor E"],
                ["Disconnect 60A", 350.00, "EA", "Vendor E"],
            ],
            "Plumbing": [
                ["Description", "Unit Cost", "Unit", "Vendor"],
                ["Lavatory P-1", 525.00, "EA", "Vendor P"],
            ],
        }
        xlsx_bytes = _build_xlsx_bytes(sheets)
        plans = parse_vendor_xlsx(xlsx_bytes)
        assert list(plans.keys()) == ["Mechanical", "Electrical", "Plumbing"]
        assert plans["Mechanical"].total_rows == 1
        assert plans["Electrical"].total_rows == 2
        assert plans["Plumbing"].total_rows == 1

        merged = merge_xlsx_plans(plans)
        assert merged.total_rows == 4
        # Row indices must be unique post-merge so apply_batch_plan's
        # skip_rows / resolved_ambiguous dicts can key off them safely.
        indices = [r.row.row_index for r in merged.no_match]
        assert len(indices) == len(set(indices)) == 4
        assert indices == sorted(indices)
        # Each merged row's notes carries the sheet-provenance prefix.
        notes_by_desc = {
            r.row.description: r.row.notes for r in merged.no_match
        }
        assert notes_by_desc["Air handler unit"].startswith("Mechanical :: ")
        assert notes_by_desc["Branch circuit wiring"].startswith(
            "Electrical :: "
        )
        assert notes_by_desc["Lavatory P-1"].startswith("Plumbing :: ")

    def test_qa_overrides_p3_subquote_pdf_tabular_stamps_sub_quote_tag(
        self,
    ) -> None:
        """POS-3: a tabular sub-quote PDF parses through T8.1, matches
        against an estimate line, and ``apply_subquote_plan(llm=False)``
        stamps ``[sub-quote]`` at position 0."""
        pdf = _build_pdf_with_table(
            [
                ["Description", "Qty", "Unit", "Unit Price"],
                ["Interior latex paint", "100", "SF", "3.85"],
            ],
            preamble=["Vendor: SubX Painting", "Quote: Q-7777"],
        )
        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 1
        est = _estimate(_line(description="Interior latex paint, walls"))
        plan = match_cost_lines(result.rows, est.line_items)
        assert len(plan.matched) == 1
        new_est, _summary = apply_subquote_plan(est, plan, llm=False)
        line = new_est.line_items[0]
        assert line.notes is not None
        assert line.notes.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")
        assert line.unit_cost == pytest.approx(3.85, abs=0.01)


# ---------------------------------------------------------------------------
# Negative scenarios
# ---------------------------------------------------------------------------


class TestQAOverridesNegative:
    """Two negative scenarios — malformed inputs must NOT silently apply."""

    def test_qa_overrides_n1_csv_missing_required_header_raises(
        self,
    ) -> None:
        """NEG-1: a CSV missing the required ``description`` column must
        raise :class:`ValueError`. No silent partial-apply, no row
        emission."""
        # Missing 'description' header (alias 'desc' not present either).
        csv_text = "thing,unit_cost\nfoo,1.23\nbar,4.56\n"
        with pytest.raises(ValueError) as exc:
            parse_vendor_csv(csv_text)
        assert "description" in str(exc.value).lower()

        # Missing 'unit_cost' header — also fatal.
        csv_text2 = "description,vendor\npaint,SubX\n"
        with pytest.raises(ValueError) as exc2:
            parse_vendor_csv(csv_text2)
        assert "unit_cost" in str(exc2.value).lower()

    def test_qa_overrides_n2_xlsx_with_garbage_bytes_raises(self) -> None:
        """NEG-2: xlsx parser must reject non-xlsx payloads (e.g. someone
        renames a CSV to ``.xlsx`` and uploads it). ``ValueError`` is the
        contract; the underlying ``InvalidFileException`` is wrapped."""
        # Plain CSV bytes — looks like a vendor CSV but not a real xlsx.
        bogus_bytes = b"description,unit_cost\nfoo,1.23\n"
        with pytest.raises(ValueError):
            parse_vendor_xlsx(bogus_bytes)
        # Empty bytes → also raises with a distinct message.
        with pytest.raises(ValueError) as exc:
            parse_vendor_xlsx(b"")
        assert "empty" in str(exc.value).lower()


# ---------------------------------------------------------------------------
# Edge scenarios
# ---------------------------------------------------------------------------


class TestQAOverridesEdge:
    """Three edge scenarios — UoM compat group, UoM mismatch, tag layering."""

    def test_qa_overrides_e1_uom_compat_group_ls_lot_matched(self) -> None:
        """EDGE-1: T6.4.b compatibility group {LS, LOT} — a vendor row in
        ``LS`` matches a cost line in ``LOT`` and vice versa. Pinned at
        the ``uoms_compatible`` predicate AND end-to-end through the
        matcher (the row reaches the MATCHED bucket)."""
        # Predicate-level pin.
        assert uoms_compatible("LS", "LOT") is True
        assert uoms_compatible("LOT", "LS") is True
        assert uoms_compatible("lump sum", "lot") is True
        # End-to-end: a vendor CSV row in "LOT" matches a cost line in "LS".
        csv_text = (
            "description,unit_cost,unit\n"
            "Site mobilization lump sum,15000,LOT\n"
        )
        rows, errors = parse_vendor_csv(csv_text)
        assert errors == []
        est = _estimate(
            _line(
                description="Site mobilization lump sum",
                unit="LS",
                unit_cost=12000.0,
                quantity=1.0,
                csi_section="01 71 13",
            )
        )
        plan = match_cost_lines(
            rows, est.line_items, enforce_uom_compatibility=True
        )
        assert len(plan.matched) == 1
        assert plan.matched[0].uom_mismatch_warning is None

    def test_qa_overrides_e2_uom_cross_dimension_lf_vs_sf_rejected(
        self,
    ) -> None:
        """EDGE-2: T6.4.b safety-on path — a vendor row in ``LF`` cannot
        match a cost line in ``SF`` (the LF/SF cross-application bug is
        the entire reason this guard exists). Falls to NO_MATCH because
        the only cost line in the estimate fails the UoM filter."""
        assert uoms_compatible("LF", "SF") is False
        csv_text = (
            "description,unit_cost,unit\n"
            "Interior latex paint walls,3.85,LF\n"  # vendor row says LF
        )
        rows, errors = parse_vendor_csv(csv_text)
        assert errors == []
        # Only one cost line, in SF — the UoM filter must reject it as a
        # candidate. With zero compatible candidates, the row falls to
        # NO_MATCH (with a diagnostic warning).
        est = _estimate(
            _line(
                description="Interior latex paint, walls",
                unit="SF",
            )
        )
        plan = match_cost_lines(
            rows, est.line_items, enforce_uom_compatibility=True
        )
        assert len(plan.matched) == 0
        assert len(plan.no_match) == 1
        result = plan.no_match[0]
        # Warning carries the canonical "row=LF vs line=SF" diagnostic.
        assert result.uom_mismatch_warning is not None
        assert "LF" in result.uom_mismatch_warning
        assert "SF" in result.uom_mismatch_warning
        # Apply must NOT silently mutate the cost line.
        new_est, _summary = apply_batch_plan(est, plan)
        assert new_est.line_items[0].unit_cost == est.line_items[0].unit_cost

    def test_qa_overrides_e3_source_tag_layered_apply_preserves_chain(
        self,
    ) -> None:
        """EDGE-3: applying tabular sub-quote then LLM-vision sub-quote
        on the SAME line stamps ``[sub-quote-llm]`` at position 0 with
        the prior ``[sub-quote] …`` head preserved as a ``| previous: …``
        suffix. Pins T6.4.c source-tag chain semantics."""
        est = _estimate(_line(description="Interior latex paint"))
        # Layer 1: tabular sub-quote PDF apply.
        pdf = _build_pdf_with_table(
            [
                ["Description", "Qty", "Unit", "Unit Price"],
                ["Interior latex paint", "100", "SF", "3.50"],
            ],
        )
        tab_rows = parse_subquote_pdf(pdf).rows
        tab_plan = match_cost_lines(tab_rows, est.line_items)
        assert len(tab_plan.matched) == 1
        est_layer1, _ = apply_subquote_plan(est, tab_plan, llm=False)
        line1 = est_layer1.line_items[0]
        assert line1.notes is not None and line1.notes.startswith(
            SOURCE_TAG_SUBQUOTE_TABULAR + " "
        )
        # Layer 2: LLM-vision sub-quote re-apply with a different cost.
        # We synthesise the row directly (no need for a real PDF — the
        # test pins notes-rewrite semantics in apply, not parse).
        from core.pricing.batch_override import (
            BatchMatchResult,
            BatchOverridePlan,
            BatchOverrideRow,
        )

        llm_row = BatchOverrideRow(
            row_index=2,
            description="Interior latex paint",
            unit_cost=3.95,
            unit_of_measure="SF",
        )
        llm_plan = match_cost_lines([llm_row], est_layer1.line_items)
        assert len(llm_plan.matched) == 1
        est_layer2, _ = apply_subquote_plan(est_layer1, llm_plan, llm=True)
        line2 = est_layer2.line_items[0]
        # New head: [sub-quote-llm] at position 0.
        assert line2.notes is not None
        assert line2.notes.startswith(SOURCE_TAG_SUBQUOTE_LLM + " ")
        # Prior head preserved in the suffix.
        assert " | previous: " in line2.notes
        suffix = line2.notes.split(" | previous: ", 1)[1]
        assert suffix.startswith(SOURCE_TAG_SUBQUOTE_TABULAR + " ")
        # Numeric state reflects the latest layer.
        assert line2.unit_cost == pytest.approx(3.95, abs=0.01)
