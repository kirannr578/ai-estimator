"""Phase T8.2 — LLM-vision fallback core tests.

Covers ``parse_subquote_pdf_with_llm`` and its four pure helpers
(``_render_pdf_pages_to_png``, ``_call_vision_llm_for_page``,
``_parse_llm_json_response``, ``_merge_llm_pages_to_result``) plus the
internal validator ``_validate_and_build_row``.

Buckets:

* **Pure helpers** — JSON-response parsing tolerance, validator
  edge cases, metadata aggregation, page-to-PNG rendering. No LLM
  client involved.
* **Mocked LLM happy paths** — well-formed JSON with 1+ rows;
  multi-page mixing items + T&C; metadata aggregation across pages;
  ``max_pages`` cap honoured; DPI parameter applied.
* **Mocked LLM failure paths** — malformed JSON twice (raises
  ``SubquoteLLMError``); auth error (raises); 5xx (raises after
  client retry budget); negative unit_cost dropped with warning;
  empty description dropped with warning.
* **Render failure modes** — empty bytes / corrupted bytes /
  encrypted PDF / zero-page PDF all raise ``SubquoteLLMError``.

Test PDFs are generated on-the-fly with ``reportlab.platypus`` —
mirroring the T8.1 ``test_subquote_parser.py`` strategy. NO real
LLM calls; every test injects a stub ``LLMClient`` whose
``analyze_image`` method returns or raises whatever the test needs.
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
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

from core.pricing.batch_override import BatchOverrideRow  # noqa: E402
from core.pricing.subquote_parser import (  # noqa: E402
    SubquoteLLMError,
    SubquoteMetadata,
    SubquoteParseError,
    SubquoteParseResult,
    _build_metadata_from_llm_pages,
    _call_vision_llm_for_page,
    _coerce_optional_float,
    _load_subquote_vision_prompt,
    _merge_llm_pages_to_result,
    _parse_llm_json_response,
    _render_pdf_pages_to_png,
    _validate_and_build_row,
    parse_subquote_pdf_with_llm,
)


# ---------------------------------------------------------------------------
# Stub LLM client + LLM response shape
# ---------------------------------------------------------------------------


@dataclass
class _StubLLMResponse:
    """Mirrors ``core.llm_client.LLMResponse`` so the production code can
    consume our stub without modification.

    Only the two attributes the production code reads (``parsed`` and
    ``text``) are populated.
    """

    parsed: Any
    text: str = ""
    provider: str = "stub"
    model: str = "stub-model"


class _StubLLMClient:
    """Minimal LLM client that returns / raises whatever each test
    configures.

    ``analyze_image`` advances through ``responses`` one entry per call.
    Each entry is either a parsed-JSON dict (returned as
    :class:`_StubLLMResponse`), a tuple ``(text, parsed)`` (when a test
    needs the raw text differently from the parsed dict), or an
    ``Exception`` instance (raised). ``calls`` records every invocation
    so tests can assert on prompt routing.
    """

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
            "extra_context": extra_context,
        })
        if not self.responses:
            raise RuntimeError("Stub exhausted; test under-specified.")
        nxt = self.responses.pop(0)
        if isinstance(nxt, Exception):
            raise nxt
        if isinstance(nxt, tuple) and len(nxt) == 2:
            text, parsed = nxt
            return _StubLLMResponse(parsed=parsed, text=text)
        return _StubLLMResponse(parsed=nxt, text="")


# ---------------------------------------------------------------------------
# PDF builders (lifted from T8.1 patterns)
# ---------------------------------------------------------------------------


def _build_text_pdf(paragraphs: list[str], *, multi_page: bool = False) -> bytes:
    """Build a one-or-many-page text-only PDF.

    Used as the input to ``parse_subquote_pdf_with_llm`` because the
    T8.2 path doesn't care about table grids — it just needs to render
    pages to PNG. A text-only PDF triggers the same render path as a
    scanned PDF would in production.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow: list = []
    for i, text in enumerate(paragraphs):
        flow.append(Paragraph(text, styles["Normal"]))
        flow.append(Spacer(1, 6))
        if multi_page and i < len(paragraphs) - 1:
            flow.append(PageBreak())
    doc.build(flow)
    return buf.getvalue()


def _multipage_pdf(n_pages: int) -> bytes:
    return _build_text_pdf(
        [f"Page {i + 1} content." for i in range(n_pages)], multi_page=True
    )


# ---------------------------------------------------------------------------
# _parse_llm_json_response — pure helper
# ---------------------------------------------------------------------------


class TestParseLLMJSONResponse:
    def test_plain_json_object(self) -> None:
        out = _parse_llm_json_response('{"a": 1, "b": "two"}')
        assert out == {"a": 1, "b": "two"}

    def test_markdown_fenced_json(self) -> None:
        raw = '```json\n{"line_items": [], "metadata": null}\n```'
        out = _parse_llm_json_response(raw)
        assert out == {"line_items": [], "metadata": None}

    def test_chatty_prose_around_json(self) -> None:
        raw = (
            'Sure, here is your extraction:\n\n'
            '{"line_items": [{"description": "X", "unit_cost": 10}]}\n\n'
            'Let me know if you need anything else.'
        )
        out = _parse_llm_json_response(raw)
        assert out["line_items"][0]["description"] == "X"

    def test_empty_string_raises(self) -> None:
        with pytest.raises(SubquoteLLMError):
            _parse_llm_json_response("")

    def test_none_raises(self) -> None:
        with pytest.raises(SubquoteLLMError):
            _parse_llm_json_response(None)  # type: ignore[arg-type]

    def test_total_garbage_raises(self) -> None:
        with pytest.raises(SubquoteLLMError) as exc_info:
            _parse_llm_json_response("this is not json at all 12345")
        assert "malformed" in str(exc_info.value).lower()

    def test_array_instead_of_object_raises(self) -> None:
        # Spec requires an object; a top-level array fails validation.
        with pytest.raises(SubquoteLLMError):
            _parse_llm_json_response("[1, 2, 3]")


# ---------------------------------------------------------------------------
# _coerce_optional_float — pure helper
# ---------------------------------------------------------------------------


class TestCoerceOptionalFloat:
    def test_int(self) -> None:
        assert _coerce_optional_float(10) == 10.0

    def test_float(self) -> None:
        assert _coerce_optional_float(10.5) == 10.5

    def test_string_with_dollar(self) -> None:
        assert _coerce_optional_float("$1,250.00") == 1250.0

    def test_none(self) -> None:
        assert _coerce_optional_float(None) is None

    def test_garbage_string(self) -> None:
        assert _coerce_optional_float("not a number") is None


# ---------------------------------------------------------------------------
# _validate_and_build_row — row validation
# ---------------------------------------------------------------------------


class TestValidateAndBuildRow:
    def test_happy_path(self) -> None:
        row, warning = _validate_and_build_row(
            {"description": "Lavatory", "quantity": 10, "unit_cost": 450.0},
            page_num=1,
            row_index=2,
        )
        assert warning is None
        assert row is not None
        assert row.description == "Lavatory"
        assert row.unit_cost == 450.0
        assert row.quantity == 10.0

    def test_empty_description_skipped(self) -> None:
        row, warning = _validate_and_build_row(
            {"description": "", "unit_cost": 10.0},
            page_num=1,
            row_index=2,
        )
        assert row is None
        assert warning is not None
        assert "empty description" in warning.lower()

    def test_missing_description_skipped(self) -> None:
        row, warning = _validate_and_build_row(
            {"unit_cost": 10.0},
            page_num=1,
            row_index=2,
        )
        assert row is None
        assert warning is not None

    def test_negative_unit_cost_skipped(self) -> None:
        row, warning = _validate_and_build_row(
            {"description": "Item A", "unit_cost": -5.0},
            page_num=1,
            row_index=3,
        )
        assert row is None
        assert warning is not None
        assert "negative" in warning.lower()

    def test_unit_cost_derived_from_extended_qty(self) -> None:
        row, warning = _validate_and_build_row(
            {
                "description": "Concrete",
                "quantity": 500,
                "extended_price": 12500.0,
            },
            page_num=1,
            row_index=2,
        )
        assert warning is None
        assert row is not None
        assert row.unit_cost == 25.0

    def test_subtotal_row_silently_skipped(self) -> None:
        row, warning = _validate_and_build_row(
            {"description": "Subtotal", "unit_cost": 1000.0},
            page_num=1,
            row_index=4,
        )
        assert row is None
        # Silent skip — no warning emitted for an expected summary row.
        assert warning is None

    def test_string_unit_cost_coerced(self) -> None:
        row, _ = _validate_and_build_row(
            {"description": "X", "unit_cost": "$1,250.50"},
            page_num=1,
            row_index=2,
        )
        assert row is not None
        assert row.unit_cost == 1250.5

    def test_notes_truncated_to_100_chars(self) -> None:
        long_note = "X" * 250
        row, _ = _validate_and_build_row(
            {
                "description": "Item",
                "unit_cost": 1.0,
                "notes": long_note,
            },
            page_num=1,
            row_index=2,
        )
        assert row is not None
        assert row.notes is not None
        assert len(row.notes) <= 100

    def test_unit_field_appended_to_notes(self) -> None:
        row, _ = _validate_and_build_row(
            {"description": "Concrete", "unit_cost": 200.0, "unit": "CY"},
            page_num=1,
            row_index=2,
        )
        assert row is not None
        assert row.notes is not None
        assert "CY" in row.notes

    def test_not_a_dict_skipped(self) -> None:
        row, warning = _validate_and_build_row(
            "not a dict",  # type: ignore[arg-type]
            page_num=1,
            row_index=2,
        )
        assert row is None
        assert warning is not None


# ---------------------------------------------------------------------------
# _merge_llm_pages_to_result — pure aggregator
# ---------------------------------------------------------------------------


class TestMergeLLMPages:
    def test_single_page_with_items(self) -> None:
        per_page = [
            {
                "is_subquote_page": True,
                "metadata": {
                    "vendor_name": "ABC Co",
                    "quote_number": "QT-1",
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                "line_items": [
                    {"description": "Item A", "unit_cost": 10.0},
                    {"description": "Item B", "unit_cost": 20.0},
                ],
            }
        ]
        result = _merge_llm_pages_to_result(per_page, total_pages=1)
        assert isinstance(result, SubquoteParseResult)
        assert len(result.rows) == 2
        assert result.metadata.vendor_name == "ABC Co"
        assert result.metadata.quote_number == "QT-1"
        assert result.metadata.detected_pages == [1]
        assert result.metadata.confidence == 1.0

    def test_page_skipped_emits_warning(self) -> None:
        per_page = [
            {
                "is_subquote_page": False,
                "page_skipped_reason": "Terms-and-conditions only.",
                "metadata": None,
                "line_items": [],
            },
            {
                "is_subquote_page": True,
                "metadata": {
                    "vendor_name": "ABC Co",
                    "quote_number": None,
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                "line_items": [{"description": "X", "unit_cost": 1.0}],
            },
        ]
        result = _merge_llm_pages_to_result(per_page, total_pages=2)
        assert len(result.rows) == 1
        assert any("Terms" in w for w in result.warnings)
        # Only page 2 had items.
        assert result.metadata.detected_pages == [2]
        # 1 page with items / 2 pages processed.
        assert result.metadata.confidence == 0.5

    def test_metadata_first_non_null_wins(self) -> None:
        per_page = [
            {
                "is_subquote_page": True,
                "metadata": {
                    "vendor_name": "Page1Vendor",
                    "quote_number": "QT-1",
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                "line_items": [{"description": "A", "unit_cost": 1.0}],
            },
            {
                "is_subquote_page": True,
                "metadata": {
                    "vendor_name": "Page2Vendor",  # ignored — page1 won
                    "quote_number": None,
                    "quote_date": "2026-05-28",  # picked up — page1 was None
                    "project_reference": "Riverside",
                    "total_quoted": 12345.67,
                },
                "line_items": [{"description": "B", "unit_cost": 2.0}],
            },
        ]
        result = _merge_llm_pages_to_result(per_page, total_pages=2)
        assert result.metadata.vendor_name == "Page1Vendor"
        assert result.metadata.quote_number == "QT-1"
        assert result.metadata.quote_date == "2026-05-28"
        assert result.metadata.project_reference == "Riverside"
        assert result.metadata.total_quoted == 12345.67

    def test_invalid_rows_dropped_with_warnings(self) -> None:
        per_page = [
            {
                "is_subquote_page": True,
                "metadata": {
                    "vendor_name": None,
                    "quote_number": None,
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                "line_items": [
                    {"description": "Good", "unit_cost": 10.0},
                    {"description": "", "unit_cost": 10.0},  # empty desc
                    {"description": "Bad", "unit_cost": -1.0},  # negative
                    {"description": "Subtotal", "unit_cost": 100.0},  # silent
                ],
            }
        ]
        result = _merge_llm_pages_to_result(per_page, total_pages=1)
        assert len(result.rows) == 1
        assert result.rows[0].description == "Good"
        # Two warnings: empty description + negative unit_cost.
        # Subtotal skip is silent, no warning.
        warning_text = " ".join(result.warnings).lower()
        assert "empty description" in warning_text
        assert "negative" in warning_text

    def test_row_indices_monotonic_across_pages(self) -> None:
        per_page = [
            {
                "is_subquote_page": True,
                "metadata": None,
                "line_items": [
                    {"description": "A", "unit_cost": 1.0},
                    {"description": "B", "unit_cost": 2.0},
                ],
            },
            {
                "is_subquote_page": True,
                "metadata": None,
                "line_items": [
                    {"description": "C", "unit_cost": 3.0},
                ],
            },
        ]
        result = _merge_llm_pages_to_result(per_page, total_pages=2)
        indices = [r.row_index for r in result.rows]
        assert indices == sorted(indices)
        assert len(set(indices)) == len(indices)

    def test_empty_input(self) -> None:
        result = _merge_llm_pages_to_result([], total_pages=0)
        assert result.rows == []
        assert result.metadata.confidence == 0.0

    def test_non_dict_page_response_emits_warning(self) -> None:
        result = _merge_llm_pages_to_result(
            ["not a dict"], total_pages=1  # type: ignore[list-item]
        )
        assert result.rows == []
        assert any("not a JSON object" in w for w in result.warnings)


# ---------------------------------------------------------------------------
# _build_metadata_from_llm_pages
# ---------------------------------------------------------------------------


class TestBuildMetadataFromLLMPages:
    def test_zero_pages_processed_zero_confidence(self) -> None:
        md = _build_metadata_from_llm_pages(
            per_page_results=[],
            detected_pages=[],
            pages_with_items=0,
            pages_processed=0,
        )
        assert md.confidence == 0.0

    def test_partial_pages_with_items(self) -> None:
        md = _build_metadata_from_llm_pages(
            per_page_results=[],
            detected_pages=[1],
            pages_with_items=1,
            pages_processed=4,
        )
        assert md.confidence == 0.25
        assert md.detected_pages == [1]


# ---------------------------------------------------------------------------
# _render_pdf_pages_to_png
# ---------------------------------------------------------------------------


class TestRenderPDFPagesToPNG:
    def test_renders_to_png_bytes(self) -> None:
        pdf = _build_text_pdf(["Hello world."])
        pngs = _render_pdf_pages_to_png(pdf, max_pages=10, dpi=200)
        assert len(pngs) == 1
        assert pngs[0].startswith(b"\x89PNG")

    def test_max_pages_cap(self) -> None:
        pdf = _multipage_pdf(5)
        pngs = _render_pdf_pages_to_png(pdf, max_pages=2, dpi=72)
        assert len(pngs) == 2

    def test_dpi_changes_image_size(self) -> None:
        pdf = _build_text_pdf(["X"])
        small = _render_pdf_pages_to_png(pdf, max_pages=1, dpi=72)
        large = _render_pdf_pages_to_png(pdf, max_pages=1, dpi=200)
        # Higher DPI → larger PNG byte count (loose lower bound: 2x).
        assert len(large[0]) > len(small[0])

    def test_empty_bytes_raises(self) -> None:
        with pytest.raises(SubquoteLLMError) as exc_info:
            _render_pdf_pages_to_png(b"", max_pages=10, dpi=200)
        assert "empty" in str(exc_info.value).lower()

    def test_corrupted_bytes_raises(self) -> None:
        with pytest.raises(SubquoteLLMError):
            _render_pdf_pages_to_png(
                b"definitely not a pdf file", max_pages=10, dpi=200
            )

    def test_invalid_max_pages_raises(self) -> None:
        pdf = _build_text_pdf(["X"])
        with pytest.raises(SubquoteLLMError):
            _render_pdf_pages_to_png(pdf, max_pages=0, dpi=200)

    def test_invalid_dpi_raises(self) -> None:
        pdf = _build_text_pdf(["X"])
        with pytest.raises(SubquoteLLMError):
            _render_pdf_pages_to_png(pdf, max_pages=10, dpi=10)
        with pytest.raises(SubquoteLLMError):
            _render_pdf_pages_to_png(pdf, max_pages=10, dpi=10000)

    def test_encrypted_pdf_raises(self) -> None:
        from pypdf import PdfReader, PdfWriter

        plain = _build_text_pdf(["secret"])
        reader = PdfReader(io.BytesIO(plain))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(user_password="x", owner_password="x")
        buf = io.BytesIO()
        writer.write(buf)
        with pytest.raises(SubquoteLLMError) as exc_info:
            _render_pdf_pages_to_png(buf.getvalue(), max_pages=10, dpi=200)
        assert "encrypt" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# _call_vision_llm_for_page — wraps LLMClient.analyze_image
# ---------------------------------------------------------------------------


class TestCallVisionLLMForPage:
    def _png_bytes(self) -> bytes:
        pdf = _build_text_pdf(["X"])
        return _render_pdf_pages_to_png(pdf, max_pages=1, dpi=72)[0]

    def test_returns_parsed_dict(self) -> None:
        client = _StubLLMClient([
            {"is_subquote_page": True, "line_items": []},
        ])
        out = _call_vision_llm_for_page(
            self._png_bytes(),
            llm_client=client,
            user_prompt="prompt",
        )
        assert out["is_subquote_page"] is True
        assert client.calls
        # The wrapper writes the PNG to a tempfile that exists at call
        # time (Path.exists() check inside the stub captures it).
        assert client.calls[0]["image_bytes_size"] is not None

    def test_value_error_mapped_to_subquote_llm_error(self) -> None:
        client = _StubLLMClient([
            ValueError("LLM did not return JSON. First 400 chars: ..."),
        ])
        with pytest.raises(SubquoteLLMError):
            _call_vision_llm_for_page(
                self._png_bytes(),
                llm_client=client,
                user_prompt="prompt",
            )

    def test_other_exceptions_propagate(self) -> None:
        # Auth errors and 5xx propagate as-is so the parent function
        # can surface them under SubquoteLLMError with context.
        client = _StubLLMClient([RuntimeError("auth failure: 401")])
        with pytest.raises(RuntimeError):
            _call_vision_llm_for_page(
                self._png_bytes(),
                llm_client=client,
                user_prompt="prompt",
            )

    def test_empty_png_raises(self) -> None:
        with pytest.raises(SubquoteLLMError):
            _call_vision_llm_for_page(
                b"",
                llm_client=_StubLLMClient([{}]),
                user_prompt="prompt",
            )

    def test_none_client_raises(self) -> None:
        with pytest.raises(SubquoteLLMError):
            _call_vision_llm_for_page(
                self._png_bytes(),
                llm_client=None,  # type: ignore[arg-type]
                user_prompt="prompt",
            )

    def test_parsed_field_falls_back_to_text_when_not_dict(self) -> None:
        # Some models occasionally return a JSON list (against our
        # prompt). The wrapper falls back to parsing the raw text
        # field for an embedded object.
        embedded = (
            'Sure! {"is_subquote_page": true, "line_items": '
            '[{"description": "X", "unit_cost": 1.0}]}'
        )
        client = _StubLLMClient([(embedded, [1, 2, 3])])
        out = _call_vision_llm_for_page(
            self._png_bytes(),
            llm_client=client,
            user_prompt="prompt",
        )
        assert out["is_subquote_page"] is True


# ---------------------------------------------------------------------------
# parse_subquote_pdf_with_llm — public entry point (mocked end-to-end)
# ---------------------------------------------------------------------------


def _ok_response(
    *,
    line_items: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    is_subquote_page: bool = True,
) -> dict[str, Any]:
    """Build a syntactically-valid LLM response dict."""
    return {
        "is_subquote_page": is_subquote_page,
        "metadata": metadata
        or {
            "vendor_name": None,
            "quote_number": None,
            "quote_date": None,
            "project_reference": None,
            "total_quoted": None,
        },
        "line_items": line_items or [],
    }


class TestParseSubquotePDFWithLLM:
    def test_three_line_items_extracted(self) -> None:
        pdf = _build_text_pdf(["Scanned-style page."])
        client = _StubLLMClient([
            _ok_response(
                metadata={
                    "vendor_name": "ABC Co",
                    "quote_number": "QT-9",
                    "quote_date": "2026-05-28",
                    "project_reference": "Riverside",
                    "total_quoted": 12345.67,
                },
                line_items=[
                    {"description": "Lavatory", "quantity": 10, "unit_cost": 450.0, "unit": "EA"},
                    {"description": "Water closet", "quantity": 8, "unit_cost": 525.0},
                    {"description": "Urinal", "quantity": 4, "unit_cost": 600.0},
                ],
            ),
        ])

        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)

        assert isinstance(result, SubquoteParseResult)
        assert len(result.rows) == 3
        assert result.rows[0].description == "Lavatory"
        assert result.rows[0].unit_cost == 450.0
        assert result.metadata.vendor_name == "ABC Co"
        assert result.metadata.total_quoted == 12345.67
        # Rows can be matched + applied via the existing T6.3 backend.
        assert all(isinstance(r, BatchOverrideRow) for r in result.rows)

    def test_empty_line_items_no_rows_no_error(self) -> None:
        pdf = _build_text_pdf(["page with no priced items"])
        client = _StubLLMClient([_ok_response(line_items=[])])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert result.rows == []

    def test_malformed_json_repair_then_success(self) -> None:
        # The ``LLMClient`` itself does the malformed-JSON repair
        # internally (returning the second-attempt parsed JSON). Our
        # stub directly returns the repaired-JSON dict as the call
        # result — i.e. we simulate the repair having already
        # happened, since that retry lives inside the production
        # client. End-to-end the parser still succeeds.
        pdf = _build_text_pdf(["X"])
        client = _StubLLMClient([
            _ok_response(line_items=[
                {"description": "Y", "unit_cost": 1.0},
            ])
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert len(result.rows) == 1

    def test_malformed_json_twice_raises(self) -> None:
        # When the LLMClient's two-attempt JSON-repair loop fails,
        # it raises ValueError — the wrapper maps that to
        # SubquoteLLMError. Both attempts failing is simulated here
        # by the stub raising on the single call.
        pdf = _build_text_pdf(["X"])
        client = _StubLLMClient([
            ValueError("LLM did not return JSON. First 400 chars: 'lol no'"),
        ])
        with pytest.raises(SubquoteLLMError) as exc_info:
            parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert "every page" in str(exc_info.value).lower() or \
            "malformed" in str(exc_info.value).lower()

    def test_auth_error_raises(self) -> None:
        pdf = _build_text_pdf(["X"])

        class _AuthError(Exception):
            pass

        client = _StubLLMClient([_AuthError("invalid api key")])
        with pytest.raises(SubquoteLLMError) as exc_info:
            parse_subquote_pdf_with_llm(pdf, llm_client=client)
        # Wrapper preserves the exception type name in the message.
        assert "_AuthError" in str(exc_info.value) or \
            "auth" in str(exc_info.value).lower()

    def test_persistent_5xx_raises(self) -> None:
        # Simulates LLMClient's retry budget exhausting — the final
        # raised exception bubbles up.
        pdf = _build_text_pdf(["X"])

        class _RateLimit(Exception):
            pass

        client = _StubLLMClient([_RateLimit("429 budget exhausted")])
        with pytest.raises(SubquoteLLMError):
            parse_subquote_pdf_with_llm(pdf, llm_client=client)

    def test_negative_unit_cost_dropped(self) -> None:
        pdf = _build_text_pdf(["X"])
        client = _StubLLMClient([
            _ok_response(line_items=[
                {"description": "Bad", "unit_cost": -10.0},
                {"description": "Good", "unit_cost": 5.0},
            ])
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        descriptions = [r.description for r in result.rows]
        assert "Bad" not in descriptions
        assert "Good" in descriptions
        assert any("negative" in w.lower() for w in result.warnings)

    def test_empty_description_dropped(self) -> None:
        pdf = _build_text_pdf(["X"])
        client = _StubLLMClient([
            _ok_response(line_items=[
                {"description": "", "unit_cost": 10.0},
                {"description": "Good", "unit_cost": 5.0},
            ])
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        descriptions = [r.description for r in result.rows]
        assert "Good" in descriptions
        assert "" not in descriptions
        assert any("empty description" in w.lower() for w in result.warnings)

    def test_multipage_page2_is_terms_only(self) -> None:
        pdf = _multipage_pdf(2)
        client = _StubLLMClient([
            _ok_response(line_items=[{"description": "Item A", "unit_cost": 1.0}]),
            _ok_response(
                is_subquote_page=False,
                line_items=[],
                metadata={
                    "vendor_name": None,
                    "quote_number": None,
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
            ) | {"page_skipped_reason": "Terms-and-conditions only."},
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert len(result.rows) == 1
        assert any("Terms" in w for w in result.warnings)

    def test_max_pages_honoured(self) -> None:
        pdf = _multipage_pdf(5)
        # Stub only supplies 2 responses — enough for max_pages=2.
        client = _StubLLMClient([
            _ok_response(line_items=[{"description": "A", "unit_cost": 1.0}]),
            _ok_response(line_items=[{"description": "B", "unit_cost": 2.0}]),
        ])
        result = parse_subquote_pdf_with_llm(
            pdf, llm_client=client, max_pages=2
        )
        assert len(client.calls) == 2
        assert len(result.rows) == 2

    def test_dpi_parameter_changes_rendered_image(self) -> None:
        pdf = _build_text_pdf(["X"])
        client_72 = _StubLLMClient([_ok_response(line_items=[])])
        client_200 = _StubLLMClient([_ok_response(line_items=[])])
        parse_subquote_pdf_with_llm(pdf, llm_client=client_72, dpi=72)
        parse_subquote_pdf_with_llm(pdf, llm_client=client_200, dpi=200)
        size_72 = client_72.calls[0]["image_bytes_size"]
        size_200 = client_200.calls[0]["image_bytes_size"]
        assert size_72 is not None and size_200 is not None
        # Higher DPI → larger payload through to the LLM call.
        assert size_200 > size_72

    def test_metadata_aggregation_across_pages(self) -> None:
        pdf = _multipage_pdf(2)
        client = _StubLLMClient([
            _ok_response(
                metadata={
                    "vendor_name": "ABC Plumbing",
                    "quote_number": "QT-100",
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                line_items=[{"description": "X", "unit_cost": 1.0}],
            ),
            _ok_response(
                metadata={
                    "vendor_name": None,
                    "quote_number": None,
                    "quote_date": None,
                    "project_reference": None,
                    "total_quoted": None,
                },
                line_items=[],
            ),
        ])
        result = parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert result.metadata.vendor_name == "ABC Plumbing"
        assert result.metadata.quote_number == "QT-100"

    def test_subquote_llm_error_subclass_of_subquote_parse_error(self) -> None:
        pdf = b""
        # A SubquoteLLMError must also satisfy ``except SubquoteParseError``
        # so the UI can keep a single catch block when the path
        # doesn't matter.
        with pytest.raises(SubquoteParseError):
            parse_subquote_pdf_with_llm(pdf, llm_client=_StubLLMClient([]))

    def test_all_pages_failed_raises(self) -> None:
        pdf = _multipage_pdf(2)
        client = _StubLLMClient([
            ValueError("LLM did not return JSON"),
            ValueError("LLM did not return JSON"),
        ])
        with pytest.raises(SubquoteLLMError) as exc_info:
            parse_subquote_pdf_with_llm(pdf, llm_client=client)
        assert "every page" in str(exc_info.value).lower()


# ---------------------------------------------------------------------------
# Source-tag wiring (audit-trail provenance)
# ---------------------------------------------------------------------------


class TestSourceTagWiring:
    def test_subquote_llm_tag_supported_by_format_helper(self) -> None:
        """Confirm the [sub-quote-llm] tag survives format_batch_operator_note."""
        from core.pricing.batch_override import format_batch_operator_note

        row = BatchOverrideRow(
            row_index=2,
            description="Lavatory",
            unit_cost=450.0,
            vendor=None,
            quote_ref=None,
            notes=None,
        )
        note = format_batch_operator_note(row, source_tag="[sub-quote-llm]")
        assert note.startswith("[sub-quote-llm]")
        assert "[batch]" not in note
        assert "[sub-quote]" not in note.replace("[sub-quote-llm]", "X")
        assert "[csv-row: 2]" in note

    def test_subquote_and_subquote_llm_distinguishable(self) -> None:
        """[sub-quote] and [sub-quote-llm] produce distinct grep-able tags."""
        from core.pricing.batch_override import format_batch_operator_note

        row = BatchOverrideRow(
            row_index=2, description="X", unit_cost=1.0,
            vendor=None, quote_ref=None, notes=None,
        )
        t81 = format_batch_operator_note(row, source_tag="[sub-quote]")
        t82 = format_batch_operator_note(row, source_tag="[sub-quote-llm]")
        assert t81 != t82
        assert "[sub-quote]" in t81 and "[sub-quote-llm]" not in t81
        assert "[sub-quote-llm]" in t82


# ---------------------------------------------------------------------------
# Prompt-loading sanity
# ---------------------------------------------------------------------------


class TestVisionPromptFile:
    def test_prompt_loadable(self) -> None:
        prompt = _load_subquote_vision_prompt()
        assert isinstance(prompt, str)
        assert len(prompt) > 100
        # Must include the JSON schema cue.
        assert "line_items" in prompt
        assert "is_subquote_page" in prompt

    def test_prompt_cached(self) -> None:
        # Two calls return the exact same object (cached).
        a = _load_subquote_vision_prompt()
        b = _load_subquote_vision_prompt()
        assert a is b
