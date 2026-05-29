"""Regression tests for ``prompts/architectural.txt`` content (T10 finding F-6).

These tests guard the prompt iteration that forbids the ``LS``-unit default
and requires dimensional units (EA / LF / SF / CY). They are deterministic,
fast, content-only assertions on the prompt file itself — they DO NOT
validate that the prompt produces better LLM output. The actual
AUTO_APPROVE-share lift requires the next T10 v5 calibration slice.

Context: calibration v4 (``exports/calibration_v4/CALIBRATION_REPORT.md``
finding F-6) reported AUTO_APPROVE band share at 2.8 % vs the 30 % target,
with 91.7 % of priced lines landing in HAND_TAKEOFF due to the cost-DB
unit-mismatch suppressor zeroing ``LS``-defaulted architectural takeoffs.
A prior attempt at the prompt fix shipped in commit ``7e75032`` but did
not stick at scale; this regression suite pins the second iteration so
the defaults cannot silently drift back.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

PROMPT_PATH = (
    Path(__file__).resolve().parent.parent / "prompts" / "architectural.txt"
)


@pytest.fixture(scope="module")
def prompt_text() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def test_prompt_file_exists() -> None:
    assert PROMPT_PATH.is_file(), f"missing prompt file: {PROMPT_PATH}"


# ---------------------------------------------------------------------------
# POS 1 — forbid-LS hard rule is present
# ---------------------------------------------------------------------------


def test_pos_forbid_ls_hard_rule_present(prompt_text: str) -> None:
    """The prompt must explicitly forbid LS as a default unit.

    Looks for the F-6 provenance reference, the word FORBIDDEN, and an
    imperative ``MUST NOT emit unit: "LS"`` instruction.
    """
    lower = prompt_text.lower()

    assert "forbidden" in lower, (
        "expected the word 'FORBIDDEN' in the LS-unit hard rule"
    )
    assert "f-6" in lower, (
        "expected the T10 F-6 finding reference for traceability"
    )
    assert re.search(r'must\s+not\s+emit\s+`?unit:\s*"?ls', lower), (
        "expected an explicit 'MUST NOT emit unit: \"LS\"' instruction"
    )


# ---------------------------------------------------------------------------
# POS 2 / POS 3 — dimensional-unit examples
# ---------------------------------------------------------------------------


DIMENSIONAL_UNITS = ("EA", "LF", "SF", "CY", "TON", "BF", "HR")


def _count_example_rows_by_unit(text: str) -> dict[str, int]:
    """Count occurrences of ``"unit": "<UNIT>"`` per dimensional unit."""
    counts: dict[str, int] = {}
    for unit in DIMENSIONAL_UNITS:
        pattern = re.compile(rf'"unit":\s*"{unit}"')
        counts[unit] = len(pattern.findall(text))
    return counts


def test_pos_at_least_four_dimensional_examples(prompt_text: str) -> None:
    """The prompt must include ≥ 4 inline JSON examples with dimensional units."""
    counts = _count_example_rows_by_unit(prompt_text)
    total = sum(counts.values())
    assert total >= 4, (
        f"expected at least 4 dimensional-unit examples; saw {total} "
        f"(per-unit breakdown: {counts})"
    )


def test_pos_examples_cover_multiple_unit_types(prompt_text: str) -> None:
    """Examples should cover at least three distinct dimensional units so
    the LLM has concrete patterns for several element categories.
    """
    counts = _count_example_rows_by_unit(prompt_text)
    distinct = sum(1 for n in counts.values() if n > 0)
    assert distinct >= 3, (
        f"expected examples covering ≥ 3 distinct dimensional units; "
        f"saw {distinct} (per-unit breakdown: {counts})"
    )


@pytest.mark.parametrize("unit", ["EA", "LF", "SF", "CY"])
def test_pos_preferred_unit_listed(prompt_text: str, unit: str) -> None:
    """The four core dimensional units called out in F-6 must each appear
    in the prompt body.
    """
    assert unit in prompt_text, (
        f"expected dimensional unit {unit!r} to be listed in the prompt"
    )


# ---------------------------------------------------------------------------
# POS 4 — unit_inference_failed fallback
# ---------------------------------------------------------------------------


def test_pos_unit_inference_failed_fallback(prompt_text: str) -> None:
    """The fallback when unit inference fails MUST be present and MUST NOT
    route to ``LS``. It should route to ``EA`` with ``quantity = 0`` and
    set the ``unit_inference_failed`` notes flag.
    """
    assert "unit_inference_failed" in prompt_text, (
        "expected the unit_inference_failed fallback marker in the prompt"
    )

    section_idx = prompt_text.find("unit_inference_failed")
    window = prompt_text[max(0, section_idx - 600) : section_idx + 600]

    assert re.search(r'"quantity":\s*0\b', window), (
        "fallback section must show quantity: 0 so downstream pricing skips it"
    )
    assert re.search(r'"unit":\s*"EA"', window), (
        "fallback section must direct the LLM to emit unit: \"EA\""
    )
    assert not re.search(r'"unit":\s*"LS"', window), (
        "fallback section must NOT contain a unit: \"LS\" example "
        "(the whole point is to avoid LS when inference fails)"
    )


# ---------------------------------------------------------------------------
# NEG 5 — regression guard: no default-to-LS instruction
# ---------------------------------------------------------------------------


_DEFAULT_TO_LS_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r'default(?:s|ing)?\s+to\s+[`"]*LS[`"]*', re.IGNORECASE),
    re.compile(r'use\s+[`"]*LS[`"]*\s+as\s+(?:the\s+)?default', re.IGNORECASE),
    re.compile(r'fall\s*back\s+to\s+[`"]*LS[`"]*\b', re.IGNORECASE),
)

_NEGATION_TOKENS: tuple[str, ...] = (
    "do not",
    "don't",
    "never",
    "must not",
    "forbidden",
    "no ",
    "not ",
)


def test_neg_no_default_to_ls_instruction(prompt_text: str) -> None:
    """Regression guard: the prompt must NOT contain any instruction that
    tells the LLM to default to / use / fall back to ``LS``.

    Negated instances ("Do NOT default to LS", "Never default to LS") are
    legitimate and allowed — they actively forbid the behaviour. Only
    bare / positive instances should fail this guard.
    """
    for pattern in _DEFAULT_TO_LS_PATTERNS:
        for match in pattern.finditer(prompt_text):
            window_start = max(0, match.start() - 60)
            preceding = prompt_text[window_start : match.start()].lower()
            if any(tok in preceding for tok in _NEGATION_TOKENS):
                continue
            raise AssertionError(
                "prompt contains an unforbidden default-to-LS instruction "
                f"at offset {match.start()}: "
                f"{prompt_text[window_start : match.end() + 40]!r}"
            )


# ---------------------------------------------------------------------------
# EDGE 6 — JSON-output schema block is pinned by snapshot
# ---------------------------------------------------------------------------


_SCHEMA_START_MARKER = "Return ONLY a JSON object with this exact shape:"
_SCHEMA_END_MARKER = '"warnings": [ "string" ]'

# Snapshot of the JSON schema block. Downstream coercion in
# core/extractors.py depends on this exact shape. If you INTENTIONALLY
# change the schema, update this snapshot AND audit downstream coercion.
_EXPECTED_SCHEMA_BLOCK = """\
Return ONLY a JSON object with this exact shape:

{
  "summary": "one short paragraph describing what this sheet shows",
  "rooms": [
    {
      "name": "string",
      "number": "string or null",
      "area_sqft": number or null,
      "perimeter_ft": number or null,
      "ceiling_height_ft": number or null,
      "floor_finish": "string or null",
      "base_finish": "string or null",
      "wall_finish": "string or null",
      "ceiling_finish": "string or null",
      "notes": "string or null"
    }
  ],
  "doors":   [ { "mark": "string", "type": "string or null", "width_in": number or null, "height_in": number or null, "rating": "string or null", "hardware_set": "string or null", "notes": "string or null" } ],
  "windows": [ { "mark": "string", "type": "string or null", "width_in": number or null, "height_in": number or null, "glazing": "string or null", "notes": "string or null" } ],
  "raw_takeoffs": [
    {
      "csi_division": "two-digit string, e.g. '09'",
      "csi_section":  "six-digit string with spaces, e.g. '09 91 23', or null",
      "description":  "string",
      "quantity":     number,
      "unit":         "EA | LF | SF | BF | CY | TON | HR | LS",
      "confidence":   number between 0 and 1,
      "notes":        "string or null"
    }
  ],
  "warnings": [ "string" ]
}"""


def _extract_schema_block(text: str) -> str:
    start = text.find(_SCHEMA_START_MARKER)
    assert start != -1, "schema-block start marker not found in prompt"
    end_search_from = text.find(_SCHEMA_END_MARKER, start)
    assert end_search_from != -1, "schema-block end marker not found in prompt"
    closing_brace = text.find("}", end_search_from)
    assert closing_brace != -1, "schema-block closing brace not found in prompt"
    return text[start : closing_brace + 1]


def test_edge_json_schema_block_pinned_by_snapshot(prompt_text: str) -> None:
    """The JSON-output schema block must match the pinned snapshot.

    Downstream coercion in ``core/extractors.py`` depends on this exact
    shape; any drift is a breaking change and must be intentional.
    """
    actual = _extract_schema_block(prompt_text)
    assert actual == _EXPECTED_SCHEMA_BLOCK, (
        "JSON schema block has changed from the pinned snapshot.\n"
        "Downstream coercion in core/extractors.py depends on this exact "
        "shape. If you INTENTIONALLY changed the schema, update "
        "_EXPECTED_SCHEMA_BLOCK in this test AND audit downstream coercion.\n"
        f"\n--- actual ---\n{actual!r}\n\n"
        f"--- expected ---\n{_EXPECTED_SCHEMA_BLOCK!r}"
    )


def test_edge_schema_unit_enum_unchanged(prompt_text: str) -> None:
    """Specifically pin the ``unit`` enum line. Downstream coercion
    validates incoming unit strings against this enum.
    """
    expected_enum_line = '"EA | LF | SF | BF | CY | TON | HR | LS"'
    assert expected_enum_line in prompt_text, (
        f"schema `unit` enum must remain {expected_enum_line}; downstream "
        "coercion in core/extractors.py depends on it"
    )
