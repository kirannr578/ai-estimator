"""QA pass — Subsystem 2: LLM client + extractors (2026-05-28).

Covers the LLM-pipeline boundary functions that the rest of the
pipeline talks to:

* :func:`core.llm_client._strip_json` / ``LLMClient._safe_json``
* :func:`core.llm_client._retry_with_backoff` budget exhaustion
* :func:`core.extractors._coerce_takeoff` / ``_coerce_alternate_line``
  / ``_coerce_bid_package`` defensive coercion
* :func:`core.extractors.extract_alternates_via_llm` short-circuits

Per the QA brief, **no live LLM calls** — every test mocks at the
``LLMClient`` boundary using a fake that records its inputs.
"""

from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from core.extractors import (
    _coerce_alternate_line,
    _coerce_bid_package,
    _coerce_takeoff,
    extract_alternates_via_llm,
)
from core.llm_client import (
    LLMClient,
    LLMResponse,
    _retry_with_backoff,
    _strip_json,
)
from core.schemas import AlternateType


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeLLM:
    """Minimal stand-in for :class:`core.llm_client.LLMClient`.

    Records every call into ``self.calls`` and returns ``self.responses``
    (a list popped FIFO; the last element is reused if exhausted, which
    lets tests assert "the LLM was called exactly N times").
    """

    def __init__(self, responses: list[LLMResponse | Exception]):
        self._responses = list(responses)
        self.calls: list[dict] = []

    def _next(self) -> LLMResponse:
        resp = self._responses.pop(0) if self._responses else self._responses[-1]
        if isinstance(resp, Exception):
            raise resp
        return resp

    def analyze_text(self, system_prompt: str, user_prompt: str) -> LLMResponse:
        self.calls.append({"kind": "text", "user_prompt": user_prompt})
        return self._next()


def _ok(parsed: dict | list, text: str | None = None) -> LLMResponse:
    return LLMResponse(
        text=text if text is not None else json.dumps(parsed),
        parsed=parsed,
        provider="fake",
        model="fake-model",
    )


# ---------------------------------------------------------------------------
# Positive
# ---------------------------------------------------------------------------


def test_qa_pos_strip_json_extracts_block_with_fence() -> None:
    """``_strip_json`` peels ```json ...``` fences."""
    raw = "Sure thing!\n```json\n{\"a\": 1}\n```"
    assert _strip_json(raw) == '{"a": 1}'


def test_qa_pos_safe_json_parses_well_formed() -> None:
    """``LLMClient._safe_json`` returns the parsed object on clean JSON."""
    assert LLMClient._safe_json('{"x": 42}') == {"x": 42}


def test_qa_pos_extract_alternates_via_llm_returns_priced_lines() -> None:
    """A clean LLM payload yields :class:`AlternateLine` objects."""
    payload = {
        "alternates": [
            {
                "alternate_id": "Alt 1",
                "alternate_type": "additive",
                "description": "Add epoxy floor coating to mechanical rooms",
                "scope_summary": "Epoxy floor coating, MEP rooms",
                "cost_delta": 1500.0,
                "confidence": 0.85,
            }
        ]
    }
    fake = _FakeLLM([_ok(payload)])
    out = extract_alternates_via_llm(
        "ALTERNATES SECTION\nAlternate #1: ...",
        fake,
        bid_package_id="bid.pdf",
        source_sheet="Bid Form p.3",
    )
    assert len(out) == 1
    line = out[0]
    assert line.alternate_id == "Alt 1"
    assert line.alternate_type == AlternateType.ADDITIVE
    assert line.cost_delta == 1500.0
    # T9.0 contract — LLM-fallback confidence capped at 0.70.
    assert line.confidence <= 0.70


# ---------------------------------------------------------------------------
# Negative
# ---------------------------------------------------------------------------


def test_qa_neg_safe_json_returns_none_on_garbage() -> None:
    """Truly malformed input returns ``None`` rather than raising."""
    assert LLMClient._safe_json("not json at all <<<") is None
    assert LLMClient._safe_json("") is None


def test_qa_neg_extract_alternates_short_circuits_on_empty_text() -> None:
    """An empty / nearly-empty page text → no LLM call, empty list."""
    fake = _FakeLLM([_ok({"alternates": []})])
    assert extract_alternates_via_llm("", fake) == []
    assert extract_alternates_via_llm("   ", fake) == []
    # The fake should not have been called for either invocation.
    assert fake.calls == []


def test_qa_neg_extract_alternates_swallows_llm_exception() -> None:
    """An LLM exception is caught and an empty list returned, not raised."""
    fake = _FakeLLM([RuntimeError("auth failed")])
    out = extract_alternates_via_llm(
        "ALTERNATES SECTION with enough text to pass the 30-char guard.",
        fake,
    )
    assert out == []
    # The call WAS made (and raised) — we count one attempt.
    assert len(fake.calls) == 1


def test_qa_neg_retry_loop_gives_up_after_budget_exhausted() -> None:
    """Repeated 429s → final exception bubbles after ``max_attempts``.

    Mirrors :mod:`tests.test_llm_retry` but pinned via a separate QA
    test for direct reference in the QA report.
    """
    class _Fake429(Exception):
        def __init__(self) -> None:
            super().__init__("rate limited")
            self.status_code = 429
            self.response = SimpleNamespace(headers={"Retry-After": "0.01"}, status_code=429)
            self.body = None

    sleeps: list[float] = []

    def fn():
        raise _Fake429()

    with pytest.raises(_Fake429):
        _retry_with_backoff(
            fn,
            provider="openai",
            description="qa-test",
            max_attempts=3,
            wall_clock_budget_s=60.0,
            sleep_fn=sleeps.append,
        )
    # 3 attempts → 2 sleeps between them.
    assert len(sleeps) == 2


# ---------------------------------------------------------------------------
# Edge
# ---------------------------------------------------------------------------


def test_qa_edge_coerce_takeoff_skips_missing_description() -> None:
    """A row with no ``description`` is dropped silently (returns None)."""
    assert _coerce_takeoff({"description": "", "quantity": 5}, "S-001") is None
    assert _coerce_takeoff({"quantity": 5}, "S-001") is None


def test_qa_edge_coerce_takeoff_defaults_division_from_section() -> None:
    """Missing ``csi_division`` is back-filled from the first 2 chars of ``csi_section``."""
    item = _coerce_takeoff(
        {"description": "x", "csi_section": "09 91 23", "quantity": 10, "unit": "SF"},
        "S-001",
    )
    assert item is not None
    assert item.csi_division == "09"


def test_qa_edge_coerce_takeoff_clamps_division_to_two_chars() -> None:
    """A 3-digit division is truncated to 2 chars (zfilled)."""
    item = _coerce_takeoff(
        {"description": "y", "csi_division": "099", "quantity": 1, "unit": "EA"},
        "S-002",
    )
    assert item is not None
    assert len(item.csi_division) == 2


def test_qa_edge_coerce_takeoff_default_confidence_when_missing() -> None:
    """``confidence`` absent → default 0.6 (the extractor's safety floor)."""
    item = _coerce_takeoff(
        {"description": "z", "csi_division": "08", "quantity": 1, "unit": "EA"},
        "S-003",
    )
    assert item is not None
    assert item.confidence == 0.6


def test_qa_edge_coerce_alternate_line_legacy_keys_supported() -> None:
    """Legacy ``number`` / ``add_or_deduct`` / ``amount`` keys still produce a line.

    The bid_form prompt has emitted both shapes through calibration.
    """
    legacy = {
        "number": "1",
        "description": "Add masonry restoration scope",
        "add_or_deduct": "Deduct",
        "amount": 1500.0,
    }
    line = _coerce_alternate_line(
        legacy, bid_package_id="x.pdf", source_sheet=None
    )
    assert line is not None
    assert line.alternate_type == AlternateType.DEDUCTIVE
    # Magnitude flipped to negative by ``_apply_type_sign``.
    assert line.cost_delta == -1500.0


def test_qa_edge_coerce_alternate_line_blank_amount_yields_none_delta() -> None:
    """``amount`` of '' or 'null' → ``cost_delta`` stays None (MISSING surface)."""
    line = _coerce_alternate_line(
        {"alternate_id": "Alt 1", "description": "x", "amount": ""},
        bid_package_id=None, source_sheet=None,
    )
    assert line is not None
    assert line.cost_delta is None


def test_qa_edge_coerce_bid_package_unknown_document_kind_defaults_to_trade() -> None:
    """An LLM that emits a bogus document_kind value gets coerced safely."""
    bp = _coerce_bid_package(
        {
            "package_number": "03.00",
            "trade_name": "Concrete",
            "document_kind": "weird-value-from-llm",
            "inclusions": ["foundations"],
        },
        pdf_name="x.pdf",
    )
    assert bp is not None
    assert bp.document_kind == "trade_package"


def test_qa_edge_coerce_bid_package_legacy_contractor_field_mirrors_to_gc() -> None:
    """Legacy LLM payload with only ``contractor`` populates ``gc`` via validator."""
    bp = _coerce_bid_package(
        {"contractor": "Beck Group", "trade_name": "Concrete"},
        pdf_name="x.pdf",
    )
    assert bp is not None
    assert bp.gc == "Beck Group"
    assert bp.contractor == "Beck Group"


# ---------------------------------------------------------------------------
# Pipeline-mock scenario (unittest.mock.patch demonstration)
# ---------------------------------------------------------------------------


def test_qa_pos_extract_bid_package_via_mocked_analyze_text() -> None:
    """End-to-end :func:`extract_bid_package` with a mocked LLM boundary.

    The brief calls for explicit ``unittest.mock`` patching of the
    LLM boundary methods (``analyze_image`` / ``analyze_text``) so we
    demonstrate the pattern with the bid-package extractor. We DON'T
    use ``patch.object`` because the extractor calls
    ``llm.analyze_text`` on whatever client is handed in — passing in
    a stand-in with the same shape is cleaner and equally explicit.
    """
    from core.extractors import extract_bid_package
    from core.pdf_processor import DocumentBundle
    from core.schemas import SheetType

    bundle = DocumentBundle(
        pdf_name="03.00_-_Concrete.pdf",
        pdf_path="03.00_-_Concrete.pdf",
        sheet_type=SheetType.BID_PACKAGE,
        full_text="BID PACKAGE\nSPECIFIC INCLUSIONS\nFoundations, slabs on grade",
        page_count=4,
        thumbnail_path="(unused)",
    )

    payload = {
        "package_number": "03.00",
        "trade_name": "Concrete",
        "project_name": "Test Project",
        "owner": "City of Example",
        "gc": "Beck Group",
        "document_kind": "trade_package",
        "inclusions": ["Foundations", "Slabs on grade"],
        "exclusions": ["Tilt-up panels"],
        "csi_divisions": ["03"],
        "summary": "Concrete trade package",
    }
    fake = _FakeLLM([_ok(payload)])

    out = extract_bid_package(bundle, fake)  # type: ignore[arg-type]

    assert out.sheet_id == "03.00_-_Concrete.pdf"
    assert out.bid_package is not None
    assert out.bid_package.trade_name == "Concrete"
    assert out.bid_package.gc == "Beck Group"
    assert out.bid_package.document_kind == "trade_package"
    assert out.bid_package.inclusions == ["Foundations", "Slabs on grade"]
    # The mock was called exactly once.
    assert len(fake.calls) == 1
    assert fake.calls[0]["kind"] == "text"


def test_qa_neg_extract_bid_package_swallows_llm_error() -> None:
    """An LLM error inside ``extract_bid_package`` becomes a warning-tagged extraction.

    Contract: ``extract_bid_package`` never raises; on LLM failure it
    returns a ``SheetExtraction`` with a non-empty warnings list. This
    keeps the outer dispatcher resilient when the network flakes mid-run.
    """
    from core.extractors import extract_bid_package
    from core.pdf_processor import DocumentBundle
    from core.schemas import SheetType

    bundle = DocumentBundle(
        pdf_name="bad.pdf",
        pdf_path="bad.pdf",
        sheet_type=SheetType.BID_PACKAGE,
        full_text="BID PACKAGE",
        page_count=2,
        thumbnail_path="(unused)",
    )
    fake = _FakeLLM([RuntimeError("network down")])

    out = extract_bid_package(bundle, fake)  # type: ignore[arg-type]
    assert out.bid_package is None
    assert any("bid_package extractor error" in w for w in out.warnings)


@pytest.mark.xfail(
    strict=False,
    reason=(
        "QA-1 finding #1-1: extract_bid_package emits a near-empty "
        "BidPackage placeholder when the LLM returns a non-dict "
        "payload (e.g. parsed=[] or parsed=None). Expected None (skip "
        "the row) to keep phantom rows out of downstream exports."
    ),
)
def test_qa_edge_extract_bid_package_with_unparseable_response() -> None:
    """An LLM that returns a non-dict payload should yield bid_package=None.

    Today's behavior: ``extract_bid_package`` falls back to ``data={}``
    when ``parsed`` is not a dict and passes the empty dict to
    ``_coerce_bid_package``, which happily builds a BidPackage with
    every field None / []. That row then lands in the project
    ``BidPackages`` table as a phantom entry with no usable
    information. The expected behavior is to skip the row entirely
    when no usable JSON was returned. Tracked as B1-1; no code fix
    in this QA slice.
    """
    from core.extractors import extract_bid_package
    from core.pdf_processor import DocumentBundle
    from core.schemas import SheetType

    bundle = DocumentBundle(
        pdf_name="weird.pdf",
        pdf_path="weird.pdf",
        sheet_type=SheetType.BID_PACKAGE,
        full_text="BID PACKAGE",
        page_count=1,
        thumbnail_path="(unused)",
    )
    fake = _FakeLLM([_ok([])])

    out = extract_bid_package(bundle, fake)  # type: ignore[arg-type]
    assert out.bid_package is None  # phantom-row guardrail


def test_qa_edge_extract_bid_package_unparseable_today_yields_placeholder() -> None:
    """Locks in today's behaviour for the non-dict-payload case (B1-1 mirror).

    Companion to the XFAIL above. This passes — it documents the
    actual current contract so a future fix that flips the behaviour
    can change BOTH tests together (XFAIL→PASS and PASS→FAIL),
    drawing reviewer attention to the change explicitly.
    """
    from core.extractors import extract_bid_package
    from core.pdf_processor import DocumentBundle
    from core.schemas import SheetType

    bundle = DocumentBundle(
        pdf_name="weird.pdf",
        pdf_path="weird.pdf",
        sheet_type=SheetType.BID_PACKAGE,
        full_text="BID PACKAGE",
        page_count=1,
        thumbnail_path="(unused)",
    )
    fake = _FakeLLM([_ok([])])

    out = extract_bid_package(bundle, fake)  # type: ignore[arg-type]
    # Today: phantom placeholder, all fields empty.
    assert out.bid_package is not None
    assert out.bid_package.trade_name is None
    assert out.bid_package.inclusions == []
    assert out.bid_package.document_kind == "trade_package"  # default
