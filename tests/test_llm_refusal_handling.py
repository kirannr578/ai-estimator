"""T10 finding F-3 — LLM safety-refusal detection + REFERENCE_PHOTO skip.

Calibration v4 surfaced gpt-4o vision refusing to analyse architectural
drawing sheets that carry a "REFERENCE ONLY" photograph of a US Army
facility. Pre-T10 the refusal was swallowed as a generic JSON-parse error
and produced 0 takeoff rows silently, costing ~25-35 missed rows across
the v4 corpus.

This test file pins both halves of the mitigation:

* **Layer 1** — :func:`core.extractors._is_refusal` matches refusal text
  and :func:`core.extractors.extract_sheet` retries once with a
  constrained business-context prompt before marking the extraction
  ``refused=True``.
* **Layer 2** — :func:`core.extraction.drawing_prepass._detect_reference_photo`
  classifies pages combining ``REFERENCE ONLY`` text with a dominant
  embedded image, and :func:`core.extractors.extract_sheet` skips the
  vision-LLM entirely for those pages.

Mocks follow the ``_FakeLLM`` pattern from ``tests/test_qa_llm_extractors.py``;
synthetic PDFs follow the in-memory ``fitz`` construction pattern from
``tests/test_qa_ingest.py`` / ``tests/test_extractor_prepass_integration.py``.
No live LLM calls.
"""

from __future__ import annotations

import json
from pathlib import Path

import fitz

from core.extraction.drawing_prepass import (
    REFERENCE_PHOTO_IMAGE_AREA_RATIO,
    prepass_drawing_page,
)
from core.extractors import _is_refusal, extract_sheet
from core.llm_client import LLMResponse
from core.schemas import Discipline, Sheet, SheetType


# ---------------------------------------------------------------------------
# Fakes
# ---------------------------------------------------------------------------


class _FakeLLM:
    """Records ``analyze_image`` / ``analyze_text`` calls and yields scripted responses.

    Mirrors the helper in ``tests/test_qa_llm_extractors.py`` but adds
    ``analyze_image`` because :func:`extract_sheet` runs the vision path.
    Each scripted entry is either an :class:`LLMResponse` (returned as-is)
    or an :class:`Exception` (raised). When the script is exhausted, the
    last element is reused — so a test can say "every call after the
    second one returns valid JSON".
    """

    def __init__(self, responses: list[LLMResponse | Exception]):
        self._responses = list(responses)
        self.image_calls: list[dict] = []
        self.text_calls: list[dict] = []

    def _next(self) -> LLMResponse:
        if not self._responses:
            raise RuntimeError("_FakeLLM script exhausted")
        if len(self._responses) == 1:
            resp = self._responses[0]
        else:
            resp = self._responses.pop(0)
        if isinstance(resp, Exception):
            raise resp
        return resp

    def analyze_image(self, *, image_path: str, system_prompt: str,
                       user_prompt: str, extra_context: str = "") -> LLMResponse:
        self.image_calls.append({
            "image_path": image_path,
            "system_prompt": system_prompt,
            "user_prompt": user_prompt,
            "extra_context": extra_context,
        })
        return self._next()

    def analyze_text(self, *, system_prompt: str, user_prompt: str) -> LLMResponse:  # pragma: no cover
        self.text_calls.append({"system_prompt": system_prompt, "user_prompt": user_prompt})
        return self._next()


def _ok(parsed: dict) -> LLMResponse:
    return LLMResponse(
        text=json.dumps(parsed),
        parsed=parsed,
        provider="fake",
        model="fake-model",
    )


def _refusal_value_error() -> ValueError:
    """Mimics what :class:`core.llm_client.LLMClient` raises on a refusal.

    The client wraps a non-JSON response (which is what gpt-4o returns
    when refusing) in a ``ValueError`` whose message embeds the first
    400 chars of the response text. Refusal-detection scans the
    exception message — same surface the extractor sees in production.
    """
    return ValueError(
        "LLM did not return JSON. First 400 chars:\n"
        "I'm sorry, I can't assist with that."
    )


# ---------------------------------------------------------------------------
# Synthetic PDF builders
# ---------------------------------------------------------------------------


def _build_page_pdf(
    tmp_path: Path,
    *,
    text_lines: list[str],
    image_rect: tuple[float, float, float, float] | None,
    name: str,
    page_width: float = 792.0,
    page_height: float = 612.0,
) -> Path:
    """Build a 1-page PDF with text lines + an optional embedded image.

    The image (when requested) is a solid-gray RGB :class:`fitz.Pixmap`
    placed at ``image_rect``. Using a real :class:`Pixmap` means
    PyMuPDF's :meth:`Page.get_image_info` finds it with the right bbox —
    drawing a rectangle with ``draw_rect`` would NOT, because the
    REFERENCE_PHOTO classifier only counts embedded images, not vector
    shapes.
    """
    doc = fitz.open()
    page = doc.new_page(width=page_width, height=page_height)
    for i, line in enumerate(text_lines):
        page.insert_text((40.0, 60.0 + i * 16), line, fontsize=11)
    if image_rect is not None:
        pix = fitz.Pixmap(fitz.csRGB, fitz.IRect(0, 0, 200, 200))
        pix.clear_with(180)
        page.insert_image(fitz.Rect(*image_rect), pixmap=pix)
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


def _make_sheet(pdf: Path, *, sheet_id: str = "A-101") -> Sheet:
    """Build a :class:`Sheet` pointing at the given synthetic PDF.

    Mirrors the construction in
    ``tests/test_extractor_prepass_integration.py`` so the prepass
    actually runs against the on-disk PDF.
    """
    return Sheet(
        pdf_name=pdf.name,
        pdf_path=str(pdf),
        page_index=0,
        sheet_number=sheet_id,
        title="Test Sheet",
        discipline=Discipline.ARCHITECTURAL,
        sheet_type=SheetType.FLOOR_PLAN,
        image_path=str(pdf),  # never actually opened on the skip path
        embedded_text="(test fixture)",
    )


# ---------------------------------------------------------------------------
# 1-4. Text-level refusal detector
# ---------------------------------------------------------------------------


def test_pos_is_refusal_detects_verbatim_gpt4o_phrasing() -> None:
    """Scenario 1 — the exact gpt-4o phrasing seen in T10 v4 calibration."""
    assert _is_refusal("I'm sorry, I can't assist with that.") is True


def test_pos_is_refusal_detects_phrase_variants() -> None:
    """Scenario 2 — alternate refusal phrasings the model emits."""
    assert _is_refusal("I cannot help with that request") is True
    assert _is_refusal("I am unable to process this image") is True
    # Trailing punctuation / extra whitespace shouldn't matter.
    assert _is_refusal("  I'm sorry, I cannot assist.   ") is True
    assert _is_refusal("I can't help with this content.") is True


def test_neg_is_refusal_ignores_normal_extraction_output() -> None:
    """Scenario 3 — normal extraction output / unrelated 'sorry' usage."""
    json_like = '{"summary": "Door schedule with 12 rows", "raw_takeoffs": []}'
    assert _is_refusal(json_like) is False

    plain_sorry = (
        "I'm sorry the prior response was truncated; here is the rest of "
        "the door schedule extraction."
    )
    # Bare "I'm sorry" is NOT a refusal — model uses it in non-refusal
    # apologies all the time. Only the full "can't assist" / "cannot help
    # with" / "unable to" phrasing counts.
    assert _is_refusal(plain_sorry) is False

    # A bare "as an AI" mention also doesn't count — the spec excludes
    # this weak signal from the refusal pattern list.
    assert _is_refusal("As an AI assistant, here is the extraction:") is False


def test_neg_is_refusal_handles_empty_and_none_input() -> None:
    """Scenario 4 — empty / whitespace / None input must return False."""
    assert _is_refusal("") is False
    assert _is_refusal(None) is False
    assert _is_refusal("   ") is False
    assert _is_refusal("\n\t  \r\n") is False


# ---------------------------------------------------------------------------
# 5-6. Extractor refusal-retry semantics
# ---------------------------------------------------------------------------


def test_pos_extractor_retries_once_after_refusal_then_succeeds(tmp_path: Path) -> None:
    """Scenario 5 — refusal first, valid JSON second → extraction succeeds + warning."""
    pdf = _build_page_pdf(
        tmp_path,
        text_lines=["Just some prose."],
        image_rect=None,
        name="retry_succeeds.pdf",
    )
    sheet = _make_sheet(pdf, sheet_id="A-201")

    valid_payload = {
        "summary": "Architectural floor plan with 3 takeoff rows.",
        "raw_takeoffs": [
            {
                "csi_division": "09",
                "csi_section": "09 91 23",
                "description": "Interior paint, walls",
                "quantity": 500.0,
                "unit": "SF",
                "confidence": 0.8,
            },
        ],
    }
    fake = _FakeLLM([_refusal_value_error(), _ok(valid_payload)])

    extraction = extract_sheet(sheet, fake)  # type: ignore[arg-type]

    # The LLM was called exactly twice — initial attempt + constrained retry.
    assert len(fake.image_calls) == 2, (
        f"expected 2 image calls (initial + constrained retry), got "
        f"{len(fake.image_calls)}"
    )
    # The second call's user prompt carries the constrained-context preamble.
    retry_prompt = fake.image_calls[1]["user_prompt"]
    assert "construction-bid context" in retry_prompt
    assert "REFERENCE ONLY annotations" in retry_prompt

    # The extraction is populated from the second response and is NOT
    # marked refused (because the retry succeeded).
    assert extraction.refused is False
    assert "3 takeoff rows" in (extraction.summary or "")
    assert len(extraction.raw_takeoffs) == 1
    assert extraction.raw_takeoffs[0].description == "Interior paint, walls"
    # A structured warning surfaces the refusal-then-retry path.
    assert any("safety refusal" in w for w in extraction.warnings)


def test_pos_extractor_double_refusal_returns_empty_with_refused_flag(tmp_path: Path) -> None:
    """Scenario 6 — refusal twice → empty extraction with refused=True + warnings; no crash."""
    pdf = _build_page_pdf(
        tmp_path,
        text_lines=["Just some prose."],
        image_rect=None,
        name="double_refusal.pdf",
    )
    sheet = _make_sheet(pdf, sheet_id="A-202")

    fake = _FakeLLM([_refusal_value_error(), _refusal_value_error()])

    # Must not raise.
    extraction = extract_sheet(sheet, fake)  # type: ignore[arg-type]

    assert len(fake.image_calls) == 2
    assert extraction.refused is True, (
        "double refusal must surface refused=True on the SheetExtraction"
    )
    assert extraction.raw_takeoffs == []
    assert extraction.rooms == []
    assert extraction.doors == []
    # Warnings carry both the initial-refusal note and the persistence note.
    joined = " | ".join(extraction.warnings).lower()
    assert "safety refusal" in joined
    assert "refused=true" in joined


# ---------------------------------------------------------------------------
# 7-9. REFERENCE_PHOTO detector
# ---------------------------------------------------------------------------


def test_pos_drawing_prepass_classifies_reference_only_photo_page(tmp_path: Path) -> None:
    """Scenario 7 — REFERENCE ONLY text + dominant image ⇒ REFERENCE_PHOTO + LLM skip."""
    # Large image covers ~85% of the page area (well above the 60% gate).
    pdf = _build_page_pdf(
        tmp_path,
        text_lines=[
            "SHEET NO: A-501",
            "REFERENCE ONLY — US Army Carr EFA facility (existing condition)",
        ],
        image_rect=(20.0, 20.0, 770.0, 590.0),
        name="reference_only.pdf",
    )

    # Detector hits.
    result = prepass_drawing_page(pdf, 0)
    assert result.is_reference_photo is True
    assert any(
        "REFERENCE_PHOTO" in qi for qi in result.quality_issues
    ), f"quality_issues should annotate the classification: {result.quality_issues!r}"

    # And `extract_sheet` must skip the vision LLM entirely for the page.
    sheet = _make_sheet(pdf, sheet_id="A-501")
    fake = _FakeLLM([_ok({"summary": "should never be returned"})])
    extraction = extract_sheet(sheet, fake)  # type: ignore[arg-type]

    assert fake.image_calls == [], (
        "vision-LLM must not be invoked on a REFERENCE_PHOTO page"
    )
    assert extraction.lm_skipped is True
    assert extraction.raw_takeoffs == []
    assert any(
        "reference_photo" in w.lower() for w in extraction.warnings
    ), f"missing reference_photo warning: {extraction.warnings!r}"


def test_neg_drawing_prepass_does_not_classify_reference_grid_callout(tmp_path: Path) -> None:
    """Scenario 8 — page mentions "reference" in a non-photo context only."""
    pdf = _build_page_pdf(
        tmp_path,
        text_lines=[
            "SHEET NO: A-101",
            "SHEET TITLE: First Floor Plan",
            "REFERENCE GRID: see structural sheets S-1.0 through S-1.2",
            "REFERENCE ELEVATION: 100'-0\" = first floor",
        ],
        # Dominant image, but no REFERENCE ONLY phrase — must not classify.
        image_rect=(20.0, 20.0, 770.0, 590.0),
        name="reference_grid.pdf",
    )
    result = prepass_drawing_page(pdf, 0)
    assert result.is_reference_photo is False
    assert not any("REFERENCE_PHOTO" in qi for qi in result.quality_issues)


def test_edge_drawing_prepass_small_image_with_reference_only_not_classified(tmp_path: Path) -> None:
    """Scenario 9 — REFERENCE ONLY caption with a small image bbox is a callout, not a photo page."""
    # Compute a deliberately-small bbox: a 60x40 pt rect on an 792x612
    # page is ~0.5% of the page area, far below the 20% callout band the
    # spec calls out and well below the 60% dominance gate.
    small_rect = (40.0, 200.0, 100.0, 240.0)
    pdf = _build_page_pdf(
        tmp_path,
        text_lines=[
            "SHEET NO: A-101",
            "DETAIL 1/A-501  REFERENCE ONLY — see installation manual",
            "Continue with construction-standard finishes per spec.",
        ],
        image_rect=small_rect,
        name="small_callout.pdf",
    )

    # Sanity-check the image-area ratio against the threshold before asserting.
    page_area = 792.0 * 612.0
    img_area = (small_rect[2] - small_rect[0]) * (small_rect[3] - small_rect[1])
    assert (img_area / page_area) < REFERENCE_PHOTO_IMAGE_AREA_RATIO

    result = prepass_drawing_page(pdf, 0)
    assert result.is_reference_photo is False
    assert not any("REFERENCE_PHOTO" in qi for qi in result.quality_issues)
