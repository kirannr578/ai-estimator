"""Phase T8.2 — end-to-end integration tests.

These tests stitch the four T8.2 surfaces together:

* PDF (text-only / scan-style) →
  :func:`core.pricing.subquote_parser.parse_subquote_pdf_with_llm`
  (with a stub LLM client) → :class:`SubquoteParseResult`.
* :class:`BatchOverrideRow` list →
  :func:`core.pricing.batch_override.match_cost_lines` →
  :class:`BatchOverridePlan` (REUSE — unchanged from T6.3).
* :class:`BatchOverridePlan` →
  :func:`core.pricing.batch_override.apply_batch_plan` →
  :class:`Estimate` with MANUAL_OVERRIDE lines (REUSE — unchanged
  from T6.3).
* Override-history entry construction with
  ``source_tag="[sub-quote-llm]"`` so the audit trail records the
  vision-LLM provenance distinctly from the deterministic T8.1
  ``[sub-quote]`` provenance.

Plus a concurrent-use scenario: the same session applying a T8.1
table parse override AND a T8.2 LLM-vision override; history should
show both tags in the correct entries.

NO real LLM calls — the stub client returns canned JSON dicts so
every assertion runs without network.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

reportlab = pytest.importorskip("reportlab")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Paragraph,
    SimpleDocTemplate,
    Table,
    TableStyle,
)

from core.estimator import MANUAL_OVERRIDE_NOTE_PREFIX  # noqa: E402
from core.pricing.batch_override import (  # noqa: E402
    apply_batch_plan,
    format_batch_operator_note,
    match_cost_lines,
)
from core.pricing.subquote_parser import (  # noqa: E402
    parse_subquote_pdf,
    parse_subquote_pdf_with_llm,
)
from core.schemas import (  # noqa: E402
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


# ---------------------------------------------------------------------------
# Stub LLM client
# ---------------------------------------------------------------------------


@dataclass
class _StubLLMResponse:
    parsed: Any
    text: str = ""
    provider: str = "stub"
    model: str = "stub-model"


class _StubLLMClient:
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
        self.calls.append({
            "image_path": image_path,
            "image_bytes_size": Path(image_path).stat().st_size
            if Path(image_path).exists()
            else None,
        })
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return _StubLLMResponse(parsed=nxt, text="")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _line(
    *,
    description: str,
    unit_cost: float = 100.0,
    quantity: float = 10.0,
    csi_section: str = "22 41 00",
) -> CostLine:
    return CostLine(
        csi_division=csi_section.split(" ", 1)[0],
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit="EA",
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.9,
        price_confidence=0.7,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        cost_source="cwicr:42",
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T8.2 integration",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _scanned_style_pdf(paragraphs: list[str]) -> bytes:
    """Build a text-only PDF — same render path as a scanned image
    would take in production (after OCR). The deterministic T8.1
    parser would raise SubquoteParseError on this, which is why T8.2
    is the right entry point."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = [Paragraph(p, styles["Normal"]) for p in paragraphs]
    doc.build(flow)
    return buf.getvalue()


def _tabular_pdf(rows: list[tuple[str, str, str]]) -> bytes:
    """Build a tabular PDF that the T8.1 parser would handle."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    data: list[list[str]] = [["Description", "Qty", "Unit Price"]]
    for desc, qty, unit_cost in rows:
        data.append([desc, qty, unit_cost])
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    doc.build([t])
    return buf.getvalue()


def _ok(line_items: list[dict[str, Any]], **meta: Any) -> dict[str, Any]:
    base_meta = {
        "vendor_name": None,
        "quote_number": None,
        "quote_date": None,
        "project_reference": None,
        "total_quoted": None,
    }
    base_meta.update(meta)
    return {
        "is_subquote_page": True,
        "metadata": base_meta,
        "line_items": line_items,
    }


# ---------------------------------------------------------------------------
# End-to-end happy path
# ---------------------------------------------------------------------------


class TestSubquoteLLMEndToEnd:
    def test_scanned_pdf_through_llm_creates_manual_override_lines(self) -> None:
        """Full T8.2 pipeline: scan-style PDF → LLM → rows → plan → applied Estimate."""
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
            _line(description="Water closet WC-1", unit_cost=600.0),
        ])

        pdf = _scanned_style_pdf([
            "Page rendered like a scanned image — the text layer is "
            "ignored by the production T8.2 path; the LLM sees the PNG.",
        ])
        client = _StubLLMClient([
            _ok(
                line_items=[
                    {"description": "Lavatory P-1", "quantity": 10, "unit_cost": 450.0},
                    {"description": "Water closet WC-1", "quantity": 8, "unit_cost": 525.0},
                ],
                vendor_name="ABC Plumbing",
                quote_number="QT-9001",
            ),
        ])

        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert len(result.rows) == 2

        plan = match_cost_lines(result.rows, list(estimate.line_items))
        assert len(plan.matched) == 2

        new_estimate, _summary = apply_batch_plan(estimate, plan)
        descriptions = {li.description: li for li in new_estimate.line_items}
        assert descriptions["Lavatory P-1"].unit_cost == 450.0
        assert descriptions["Water closet WC-1"].unit_cost == 525.0
        # T6.3 backend stamps every applied line with the
        # MANUAL_OVERRIDE tier, identically for T8.1 and T8.2 paths.
        for li in new_estimate.line_items:
            assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
            assert MANUAL_OVERRIDE_NOTE_PREFIX in (li.notes or "")

    def test_subquote_llm_source_tag_in_operator_history(self) -> None:
        """An LLM-extracted row's audit-trail note carries [sub-quote-llm]."""
        estimate = _estimate([_line(description="Lavatory P-1", unit_cost=500.0)])
        pdf = _scanned_style_pdf(["scan-style page"])
        client = _StubLLMClient([
            _ok([{"description": "Lavatory P-1", "quantity": 10, "unit_cost": 450.0}])
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        plan = match_cost_lines(result.rows, list(estimate.line_items))

        # Mirror the app.py code: build the override-history note with
        # the [sub-quote-llm] source tag.
        row = plan.matched[0].row
        note = format_batch_operator_note(row, source_tag="[sub-quote-llm]")
        assert note.startswith("[sub-quote-llm]")
        assert "[batch]" not in note
        # And the [sub-quote] tag must NOT appear (substring would not
        # be a real tag — confirm clean separation).
        assert "[sub-quote] " not in note  # trailing space rules out [sub-quote-llm]


# ---------------------------------------------------------------------------
# Source-tag differentiation across T8.1 vs T8.2 in the same session
# ---------------------------------------------------------------------------


class TestT81VsT82SourceTags:
    def test_t81_lines_tagged_subquote_t82_lines_tagged_subquote_llm(self) -> None:
        """Both ingestion paths run end-to-end in the same session;
        their override-history tags must remain distinguishable."""
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
            _line(description="Drywall 5/8 inch", unit_cost=2.0, csi_section="09 21 16"),
        ])

        # T8.1 — tabular path on the drywall line.
        t81_pdf = _tabular_pdf([("Drywall 5/8 inch", "1000", "1.85")])
        t81_result = parse_subquote_pdf(t81_pdf)
        t81_plan = match_cost_lines(t81_result.rows, list(estimate.line_items))
        t81_note = format_batch_operator_note(
            t81_plan.matched[0].row,
            source_tag="[sub-quote]",
        )

        # T8.2 — LLM-vision path on the plumbing line.
        t82_pdf = _scanned_style_pdf(["Lavatory invoice from ABC Plumbing"])
        t82_client = _StubLLMClient([
            _ok([{"description": "Lavatory P-1", "quantity": 10, "unit_cost": 450.0}])
        ])
        t82_result = parse_subquote_pdf_with_llm(t82_pdf, llm_client=t82_client)
        t82_plan = match_cost_lines(t82_result.rows, list(estimate.line_items))
        t82_note = format_batch_operator_note(
            t82_plan.matched[0].row,
            source_tag="[sub-quote-llm]",
        )

        assert t81_note.startswith("[sub-quote]")
        assert t82_note.startswith("[sub-quote-llm]")
        assert t81_note != t82_note
        # Each tag is unique to its path. The two strings ``[sub-quote]``
        # and ``[sub-quote-llm]`` are distinct (closing bracket differs)
        # so neither is a substring of the other.
        assert "[sub-quote-llm]" not in t81_note
        assert "[sub-quote]" not in t82_note
        # A loose audit-trail grep on ``sub-quote`` still matches both
        # — useful when the operator wants every PDF-sourced row
        # regardless of whether it came from the table parser or the
        # vision LLM.
        assert "sub-quote" in t81_note
        assert "sub-quote" in t82_note
        assert t81_note.split(" ", 1)[0] == "[sub-quote]"
        assert t82_note.split(" ", 1)[0] == "[sub-quote-llm]"

    def test_t81_and_t82_apply_in_same_session(self) -> None:
        """Apply a T8.1 then a T8.2 override in the same Estimate;
        both sets of overrides land cleanly on top of each other."""
        estimate = _estimate([
            _line(description="Drywall 5/8 inch", unit_cost=2.0, csi_section="09 21 16"),
            _line(description="Lavatory P-1", unit_cost=500.0),
        ])

        # T8.1 path first.
        t81_pdf = _tabular_pdf([("Drywall 5/8 inch", "1000", "1.85")])
        t81_result = parse_subquote_pdf(t81_pdf)
        t81_plan = match_cost_lines(t81_result.rows, list(estimate.line_items))
        estimate, _ = apply_batch_plan(estimate, t81_plan)

        # T8.2 path on the (now-modified) estimate.
        t82_pdf = _scanned_style_pdf(["scanned plumbing quote"])
        t82_client = _StubLLMClient([
            _ok([{"description": "Lavatory P-1", "quantity": 10, "unit_cost": 450.0}])
        ])
        t82_result = parse_subquote_pdf_with_llm(t82_pdf, llm_client=t82_client)
        t82_plan = match_cost_lines(t82_result.rows, list(estimate.line_items))
        estimate, _ = apply_batch_plan(estimate, t82_plan)

        descriptions = {li.description: li for li in estimate.line_items}
        assert descriptions["Drywall 5/8 inch"].unit_cost == 1.85
        assert descriptions["Lavatory P-1"].unit_cost == 450.0
        # Both lines carry MANUAL_OVERRIDE tier — the T6.3 backend is
        # path-agnostic.
        for desc in ("Drywall 5/8 inch", "Lavatory P-1"):
            assert (
                descriptions[desc].cost_source_tier
                == CostSourceTier.MANUAL_OVERRIDE
            )


# ---------------------------------------------------------------------------
# Backend signature integrity — T6.3 backend invoked unchanged from T8.2
# ---------------------------------------------------------------------------


class TestT82BackendIntegrity:
    def test_t63_backend_invoked_unchanged_from_t82(self) -> None:
        """The T8.2 path reaches the T6.3 backend across T6.3 → T8.2 → T6.4.c → T6.4.b.

        Mirrors the T8.1 integrity test — pinning the contract that the
        LLM-vision path emits the same ``BatchOverrideRow`` shape and
        invokes ``match_cost_lines`` / ``apply_batch_plan`` with their
        documented signatures.

        Phase T6.4.c added a keyword-only ``source_tag`` parameter to
        :func:`apply_batch_plan` (default :data:`SOURCE_TAG_BATCH`).
        Phase T6.4.b added a keyword-only ``enforce_uom_compatibility``
        parameter to :func:`match_cost_lines` (default ``True``).
        Both defaults preserve byte-identical behaviour for every
        pre-T6.4.b / pre-T6.4.c caller whose rows had no UoM info or
        whose UoMs were already compatible with the chosen lines.
        """
        import inspect
        from core.pricing.batch_override import SOURCE_TAG_BATCH

        match_sig = inspect.signature(match_cost_lines)
        # Original four params unchanged + trailing keyword-only
        # enforce_uom_compatibility (T6.4.b).
        assert list(match_sig.parameters.keys()) == [
            "rows",
            "cost_lines",
            "similarity_threshold",
            "ambiguity_margin",
            "enforce_uom_compatibility",
        ]
        uom_param = match_sig.parameters["enforce_uom_compatibility"]
        assert uom_param.kind == inspect.Parameter.KEYWORD_ONLY
        assert uom_param.default is True
        apply_sig = inspect.signature(apply_batch_plan)
        # Original five params unchanged + trailing keyword-only source_tag (T6.4.c).
        assert list(apply_sig.parameters.keys()) == [
            "estimate",
            "plan",
            "auto_apply_matched",
            "resolved_ambiguous",
            "skip_rows",
            "source_tag",
        ]
        # source_tag is KEYWORD_ONLY with the legacy [batch] default so
        # every pre-T6.4.c positional call site keeps working.
        st_param = apply_sig.parameters["source_tag"]
        assert st_param.kind == inspect.Parameter.KEYWORD_ONLY
        assert st_param.default == SOURCE_TAG_BATCH

        # And confirm the T8.2 entry point exists with the documented
        # signature.
        llm_sig = inspect.signature(parse_subquote_pdf_with_llm)
        params = list(llm_sig.parameters.keys())
        assert "pdf_bytes" in params
        assert "llm_client" in params
        assert "max_pages" in params
        assert "dpi" in params
