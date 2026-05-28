"""Phase T8.2 — ``app.py`` LLM-vision UI helper tests.

Two helpers added to ``app.py`` by Phase T8.2:

* :func:`app._render_subquote_llm_cost_estimate` — builds the
  cost-disclosure caption shown above the "Try LLM extraction" button.
  This is the only LLM-spending button in the override flow, so the
  text must be reproducible and contain the per-page + total bounds.
* :func:`app._render_subquote_llm_source_banner` — builds the
  one-line banner identifying an LLM-extracted result so an operator
  reviewing the preview-table can tell it came from the vision model.

Plus end-to-end tests of the public T8.2 surface (``parse_subquote_pdf_with_llm``)
through a mock LLM client to confirm the helper-to-parser wiring.

Streamlit-free — both helpers return strings, both can be exercised
without an ``AppTest`` harness.
"""

from __future__ import annotations

import io
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pytest

reportlab = pytest.importorskip("reportlab")

from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    Paragraph,
    SimpleDocTemplate,
)

from app import (  # noqa: E402
    _render_subquote_llm_cost_estimate,
    _render_subquote_llm_source_banner,
)
from core.pricing.subquote_parser import (  # noqa: E402
    SubquoteMetadata,
    parse_subquote_pdf_with_llm,
)


# ---------------------------------------------------------------------------
# Stub LLM client — same shape as the fallback test file
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
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
        })
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        return _StubLLMResponse(parsed=nxt, text="")


def _build_text_pdf(paragraphs: list[str]) -> bytes:
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = [Paragraph(p, styles["Normal"]) for p in paragraphs]
    doc.build(flow)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# _render_subquote_llm_cost_estimate
# ---------------------------------------------------------------------------


class TestRenderSubquoteLLMCostEstimate:
    def test_default_text_contains_required_facts(self) -> None:
        text = _render_subquote_llm_cost_estimate()
        # Mention "cost", per-page, and an explicit cap.
        assert "cost" in text.lower()
        assert "per page" in text.lower()
        assert "10 pages" in text
        # Default low + high bounds appear ($0.02 - $0.10).
        assert "$0.02" in text
        assert "$0.10" in text

    def test_default_total_bounds(self) -> None:
        # Worst-case total = $0.02 * 10 .. $0.10 * 10 = $0.20 .. $1.00.
        text = _render_subquote_llm_cost_estimate()
        assert "$0.20" in text
        assert "$1.00" in text

    def test_custom_max_pages_changes_totals(self) -> None:
        text = _render_subquote_llm_cost_estimate(max_pages=5)
        assert "5 pages" in text
        assert "$0.10" in text  # 0.02 * 5
        assert "$0.50" in text  # 0.10 * 5

    def test_custom_per_page_bounds(self) -> None:
        text = _render_subquote_llm_cost_estimate(
            per_page_low_usd=0.05,
            per_page_high_usd=0.20,
        )
        assert "$0.05" in text
        assert "$0.20" in text

    def test_returns_string(self) -> None:
        assert isinstance(_render_subquote_llm_cost_estimate(), str)


# ---------------------------------------------------------------------------
# _render_subquote_llm_source_banner
# ---------------------------------------------------------------------------


class TestRenderSubquoteLLMSourceBanner:
    def test_banner_identifies_llm_path(self) -> None:
        text = _render_subquote_llm_source_banner()
        assert "LLM" in text
        # Mentions the audit-trail tag so an operator knows what to
        # grep for in the override-history CSV download.
        assert "[sub-quote-llm]" in text

    def test_banner_accepts_metadata_argument(self) -> None:
        # The metadata parameter is wired but not yet rendered in the
        # banner — this test pins the call-site contract so future
        # calibration that does surface fields here can't accidentally
        # change the function shape.
        md = SubquoteMetadata(vendor_name="ABC Co", confidence=0.5)
        text = _render_subquote_llm_source_banner(md)
        assert isinstance(text, str)
        assert "LLM" in text


# ---------------------------------------------------------------------------
# Helper importability
# ---------------------------------------------------------------------------


def test_helpers_importable_from_app() -> None:
    """Both helpers must be exposed at module scope on app.py."""
    import app

    assert callable(app._render_subquote_llm_cost_estimate)
    assert callable(app._render_subquote_llm_source_banner)


def test_t82_imports_routed_through_app() -> None:
    """``parse_subquote_pdf_with_llm`` + ``SubquoteLLMError`` must be in app's namespace."""
    import app

    assert callable(app.parse_subquote_pdf_with_llm)
    assert app.SubquoteLLMError is not None


# ---------------------------------------------------------------------------
# Mock LLM client end-to-end through the UI parser entry point
# ---------------------------------------------------------------------------


class TestMockLLMIntegrationThroughUI:
    """Confirm the helper UI text aligns with the parser behaviour.

    These tests don't drive Streamlit — they exercise the same call
    chain ``app.py`` would make when an operator clicks the "Try LLM
    extraction" button: ``parse_subquote_pdf_with_llm`` with a
    pre-rendered PDF and an injected stub client. The cost-estimate
    and source-banner helpers are then rendered against the result so
    we pin the helper-output contract end-to-end.
    """

    def _ok_response(self) -> dict[str, Any]:
        return {
            "is_subquote_page": True,
            "metadata": {
                "vendor_name": "ABC Plumbing",
                "quote_number": "QT-1",
                "quote_date": "2026-05-28",
                "project_reference": None,
                "total_quoted": 1234.56,
            },
            "line_items": [
                {"description": "Lavatory P-1", "quantity": 10, "unit_cost": 450.0},
            ],
        }

    def test_end_to_end_parser_to_helpers(self) -> None:
        pdf = _build_text_pdf(["This is a scanned-style page."])
        client = _StubLLMClient([self._ok_response()])

        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)

        # Banner renders without error against the parser's metadata.
        banner = _render_subquote_llm_source_banner(result.metadata)
        assert "LLM" in banner

        # Cost estimate is independent of the parse result and
        # reproducible — operator should see identical text on every
        # render of the button.
        cost = _render_subquote_llm_cost_estimate()
        cost_again = _render_subquote_llm_cost_estimate()
        assert cost == cost_again

    def test_helper_text_does_not_change_per_session(self) -> None:
        """Cost-estimate text is deterministic — no session state, no env reads."""
        a = _render_subquote_llm_cost_estimate()
        b = _render_subquote_llm_cost_estimate()
        c = _render_subquote_llm_cost_estimate()
        assert a == b == c
