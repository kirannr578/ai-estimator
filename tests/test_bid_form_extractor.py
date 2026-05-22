"""Tests for `core.extractors.extract_bid_form` (Bug B from calibration v2).

The BID_FORM branch of `extract_bundle` used to short-circuit to a no-op
stub, so the San Marcos Bid Schedule — the only PDF in the v2 input set
that carried real unit-price line items — never reached the LLM. These
tests confirm:

  * the dedicated `prompts/bid_form.txt` template is present and loadable
  * the BID_FORM branch in `extract_bundle` calls the LLM (no more silent
    skip), wires up a `BidPackage` with the returned `unit_prices`, and
    propagates basic project info
  * a near-empty PDF still skips (with a clear warning) instead of burning
    a useless LLM call

No real API calls — the LLM client is replaced by a hand-rolled stub.
"""

from __future__ import annotations

import logging
from types import SimpleNamespace

from core.extractors import extract_bundle
from core.pdf_processor import DocumentBundle
from core.schemas import SheetType
from prompts import load as load_prompt


def test_bid_form_prompt_template_is_loadable() -> None:
    """`prompts/bid_form.txt` must exist and look like an extractor prompt."""
    body = load_prompt("bid_form")
    assert "unit_prices" in body, "prompt must mention the unit_prices field"
    assert "JSON" in body.upper(), "prompt must instruct JSON output"
    # Same overall envelope as bid_package: project_name, summary, warnings.
    for key in ("project_name", "project_number", "summary", "warnings"):
        assert key in body, f"prompt missing field instruction: {key}"


class _LLMStub:
    """Minimal `LLMClient`-shaped stub.

    Captures the prompt it was given and returns a canned parsed-JSON
    response that mimics a real bid-schedule extraction.
    """

    def __init__(self, parsed: dict) -> None:
        self._parsed = parsed
        self.text_calls: list[tuple[str, str]] = []
        self.image_calls: list[dict] = []

    def analyze_text(self, system_prompt: str, user_prompt: str):
        self.text_calls.append((system_prompt, user_prompt))
        return SimpleNamespace(
            text="(stub)",
            parsed=self._parsed,
            provider="stub",
            model="stub",
        )

    def analyze_image(self, *args, **kwargs):  # pragma: no cover - unused
        self.image_calls.append({"args": args, "kwargs": kwargs})
        return SimpleNamespace(text="", parsed={}, provider="stub", model="stub")


def _make_bundle(text: str, name: str = "Bid_Schedule_San_Marcos.pdf") -> DocumentBundle:
    return DocumentBundle(
        pdf_name=name,
        pdf_path=f"/tmp/{name}",
        sheet_type=SheetType.BID_FORM,
        full_text=text,
        page_count=1,
        thumbnail_path=f"/tmp/{name}.png",
        title_hint=None,
    )


def test_extract_bundle_bid_form_invokes_llm_and_returns_unit_prices() -> None:
    """The BID_FORM dispatch now calls the LLM and returns a BidPackage
    populated with the extracted unit prices."""
    sample_text = (
        "BID SCHEDULE — San Marcos ARC, Rehabilitate Shop & 2-Stall Garage\n"
        "Solicitation: B08-Sample\n"
        "Item 1: Mobilization                LS  1   ____\n"
        "Item 2: Concrete slab on grade      SF  1200 ____\n"
        "Item 3: Standing-seam metal roof    SF  900  ____\n"
        + ("\n" * 5)
        + ("Fill in the unit prices in the blanks above. " * 20)
    )

    stub = _LLMStub(
        parsed={
            "trade_name": "Bid Schedule",
            "project_name": "San Marcos ARC – Rehabilitate Shop & 2-Stall Garage",
            "project_number": "B08-Sample",
            "project_location": "San Marcos, TX",
            "unit_prices": [
                {"description": "Mobilization", "unit": "LS", "amount": None},
                {"description": "Concrete slab on grade", "unit": "SF", "amount": None},
                {"description": "Standing-seam metal roof", "unit": "SF", "amount": None},
            ],
            "summary": "Three-line bid schedule for a small rehab project.",
        }
    )

    ex = extract_bundle(_make_bundle(sample_text), stub)

    # LLM was actually called — the calibration v2 regression was a silent skip.
    assert len(stub.text_calls) == 1
    system_prompt, user_prompt = stub.text_calls[0]
    assert "JSON" in system_prompt.upper()
    assert "FULL DOCUMENT TEXT" in user_prompt
    assert "Bid_Schedule_San_Marcos.pdf" in user_prompt

    # Result wires through to a populated BidPackage.
    bp = ex.bid_package
    assert bp is not None
    assert bp.pdf_name == "Bid_Schedule_San_Marcos.pdf"
    assert bp.project_name and "San Marcos" in bp.project_name
    assert bp.project_number == "B08-Sample"
    assert len(bp.unit_prices) == 3
    units = {u.unit for u in bp.unit_prices}
    assert {"LS", "SF"}.issubset(units)


def test_extract_bundle_bid_form_skips_on_near_empty_text(caplog) -> None:
    """A scanned blank form (no extractable text) should not waste an LLM
    call. We expect a WARNING log line and no `analyze_text` invocation."""
    caplog.set_level(logging.WARNING, logger="core.extractors")
    stub = _LLMStub(parsed={})
    ex = extract_bundle(_make_bundle(text=""), stub)

    assert stub.text_calls == []
    assert ex.bid_package is None
    assert ex.warnings, "skip path must surface a warning"
    assert any("bid_form skip" in str(w) for w in ex.warnings)
    assert any(
        "extract_bid_form" in rec.message for rec in caplog.records
    ), "missing WARNING log for empty bid form"
