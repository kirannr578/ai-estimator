"""Tests for the Phase T3.5 generic dedupe-by-source-tag scaffold.

These tests exercise :func:`core.extraction.dedupe.dedupe_against_synthesis`
and :func:`core.extraction.dedupe.extract_mark_from_synthesized` in
isolation, using a synthetic "fixture_schedule_prepass" family so the
tests cannot be confused with the door- or window-specific contracts
already pinned by :mod:`tests.test_door_dedupe` and
:mod:`tests.test_window_dedupe`.

The two real callers (doors and windows) provide the byte-identical
behavioural contract — those test files are intentionally untouched
during the T3.5 refactor. This file pins the *generic* surface.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import (
    dedupe_against_synthesis,
    extract_mark_from_synthesized,
)
from core.schemas import TakeoffItem


# ---------------------------------------------------------------------------
# Fixture family — synthetic "fixture schedule prepass" used by these tests
# ---------------------------------------------------------------------------

# A made-up source tag so these tests never accidentally interact with
# the real door / window dedupe flows.
_FIXTURE_TAG = "fixture_schedule_prepass"

# Plumbing fixtures live in CSI Division 22, sections 22 40 xx (Plumbing
# Fixtures) and 22 42 xx (Commercial Plumbing Fixtures) — picked just to
# avoid any overlap with the doors/windows surface.
_FIXTURE_SECTION_PREFIXES: tuple[str, ...] = ("22 40", "22 42")

# Legacy aggregate regex shaped after the door/window pattern: optional
# material prefix + "fixtures" suffix + optional ": N EA" count tail.
_FIXTURE_AGG_RE: re.Pattern[str] = re.compile(
    r"^(plumbing|water\s*closet|wc|lavatory|sink|urinal)?"
    r"\s*fixtures?(\s*:?\s*\d+\s+ea)?\s*$",
    re.IGNORECASE,
)

# Mark regex shaped after the door/window pattern:
# ``Fixture <MARK> — <label> ...``.
_FIXTURE_MARK_RE: re.Pattern[str] = re.compile(
    r"^fixture\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\-]|--)\s",
    re.IGNORECASE,
)


def _synth(mark: str, section: str = "22 40 13") -> TakeoffItem:
    return TakeoffItem(
        csi_division="22",
        csi_section=section,
        description=f"Fixture {mark} \u2014 WC vitreous china",
        quantity=1.0,
        unit="EA",
        confidence=0.92,
        notes=f"source={_FIXTURE_TAG}; mark={mark}; type=WC",
    )


def _llm_mark(mark: str, section: str = "22 40 13") -> TakeoffItem:
    return TakeoffItem(
        csi_division="22",
        csi_section=section,
        description=f"Fixture {mark} (LLM-extracted, water closet)",
        quantity=1.0,
        unit="EA",
        confidence=0.75,
    )


def _llm_agg(desc: str, section: str = "22 40 13", qty: float = 8.0) -> TakeoffItem:
    return TakeoffItem(
        csi_division="22",
        csi_section=section,
        description=desc,
        quantity=qty,
        unit="EA",
        confidence=0.85,
    )


def _out_of_family(
    division: str = "09",
    section: str = "09 91 23",
    desc: str = "Interior wall painting (two coats)",
) -> TakeoffItem:
    return TakeoffItem(
        csi_division=division,
        csi_section=section,
        description=desc,
        quantity=500.0,
        unit="SF",
        confidence=0.65,
    )


def _dedupe_fixtures(
    items: list[TakeoffItem],
    *,
    mark_pattern: re.Pattern[str] | None = _FIXTURE_MARK_RE,
    legacy_aggregate_patterns: tuple[re.Pattern[str], ...] = (_FIXTURE_AGG_RE,),
) -> list[TakeoffItem]:
    """Common test driver around the generic scaffold."""
    return dedupe_against_synthesis(
        items,
        source_tag=_FIXTURE_TAG,
        section_prefixes=_FIXTURE_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=legacy_aggregate_patterns,
        mark_pattern=mark_pattern,
        family_label="fixture",
        match_family_by_description=False,
    )


# ---------------------------------------------------------------------------
# 1. Empty input -> empty output
# ---------------------------------------------------------------------------


def test_empty_input_returns_empty() -> None:
    assert _dedupe_fixtures([]) == []


# ---------------------------------------------------------------------------
# 2. Safety rule: no synth rows -> input unchanged (identity preserved)
# ---------------------------------------------------------------------------


def test_no_synthesised_returns_input_unchanged() -> None:
    items = [
        _llm_agg("Plumbing fixtures", qty=12),
        _llm_mark("WC-101"),
        _out_of_family(),
    ]
    out = _dedupe_fixtures(items)
    assert out == items
    assert all(a is b for a, b in zip(out, items))


# ---------------------------------------------------------------------------
# 3. Legacy aggregate retired when at least one synth row exists
# ---------------------------------------------------------------------------


def test_legacy_aggregate_dropped_when_any_synth_exists() -> None:
    items = [
        _synth("WC-101"),
        _llm_agg("Plumbing fixtures"),
        _llm_agg("Lavatory fixtures"),
        _llm_agg("Fixtures: 8 EA"),
    ]
    out = _dedupe_fixtures(items)
    assert len(out) == 1
    assert out[0].description.startswith("Fixture WC-101")


# ---------------------------------------------------------------------------
# 4. Same-mark LLM row dropped when matched by a synth row
# ---------------------------------------------------------------------------


def test_synth_with_matching_mark_drops_llm_row() -> None:
    items = [
        _synth("WC-101"),
        _llm_mark("WC-101"),
    ]
    out = _dedupe_fixtures(items)
    assert len(out) == 1
    assert (out[0].notes or "").startswith(f"source={_FIXTURE_TAG}")


# ---------------------------------------------------------------------------
# 5. Synth + non-matching items -> all preserved, original order intact
# ---------------------------------------------------------------------------


def test_synth_and_non_matching_items_preserved_in_order() -> None:
    items = [
        _out_of_family(),
        _synth("WC-101"),
        _llm_mark("ZZ-999"),
        _out_of_family("23", "23 00 00", "Rooftop unit"),
    ]
    out = _dedupe_fixtures(items)
    assert [it.description for it in out] == [it.description for it in items]


# ---------------------------------------------------------------------------
# 6. Out-of-family rows are untouched regardless of dedupe state
# ---------------------------------------------------------------------------


def test_out_of_family_rows_untouched_with_and_without_synth() -> None:
    # First: with a synth row driving an active dedupe pass.
    items_with_synth = [
        _synth("WC-101"),
        _llm_agg("Plumbing fixtures"),         # dropped (aggregate)
        _llm_mark("WC-101"),                   # dropped (mark match)
        _out_of_family("09", "09 91 23", "Painting"),
        _out_of_family("06", "06 10 00", "Rough carpentry"),
        # Coincidental "fixtures"-suffix row in a different division —
        # NOT in family (section_prefixes only match Division 22 codes)
        # and ``match_family_by_description=False`` here, so it survives.
        TakeoffItem(
            csi_division="26",
            csi_section="26 51 00",
            description="Light fixtures",
            quantity=10.0,
            unit="EA",
            confidence=0.7,
        ),
    ]
    out = _dedupe_fixtures(items_with_synth)
    divisions = sorted(it.csi_division for it in out)
    assert divisions == ["06", "09", "22", "26"]

    # Second: with no synth row -> input unchanged.
    items_without_synth = [
        _llm_agg("Plumbing fixtures"),
        _out_of_family(),
    ]
    out2 = _dedupe_fixtures(items_without_synth)
    assert out2 == items_without_synth


# ---------------------------------------------------------------------------
# 7. Arbitrary source_tag — the scaffold is tag-agnostic
# ---------------------------------------------------------------------------


def test_custom_source_tag_works_with_arbitrary_values() -> None:
    """The generic must not hard-code door/window tags anywhere."""
    custom_tag = "some_other_prepass_v7"

    def _custom_synth(mark: str) -> TakeoffItem:
        return TakeoffItem(
            csi_division="22", csi_section="22 40 13",
            description=f"Fixture {mark} \u2014 widget",
            quantity=1.0, unit="EA", confidence=0.92,
            notes=f"source={custom_tag}; mark={mark}; type=W",
        )

    items = [
        _custom_synth("X-1"),
        _llm_mark("X-1"),                       # drop (mark match)
        _llm_agg("Plumbing fixtures"),          # drop (aggregate)
        _llm_mark("Y-2"),                       # keep
    ]
    out = dedupe_against_synthesis(
        items,
        source_tag=custom_tag,
        section_prefixes=_FIXTURE_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_FIXTURE_AGG_RE,),
        mark_pattern=_FIXTURE_MARK_RE,
        family_label="fixture",
    )
    assert len(out) == 2
    descs = [it.description for it in out]
    assert any("Fixture X-1" in d for d in descs)
    assert any("Y-2" in d for d in descs)

    # Using the wrong tag against the same items -> no synth detected -> no drops.
    out_wrong = dedupe_against_synthesis(
        items,
        source_tag="completely_unrelated_tag",
        section_prefixes=_FIXTURE_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_FIXTURE_AGG_RE,),
        mark_pattern=_FIXTURE_MARK_RE,
        family_label="fixture",
    )
    assert out_wrong == items


# ---------------------------------------------------------------------------
# 8. mark_pattern=None disables per-mark dedupe; only aggregates are dropped
# ---------------------------------------------------------------------------


def test_mark_pattern_none_disables_per_mark_dedupe() -> None:
    items = [
        _synth("WC-101"),
        _llm_mark("WC-101"),                    # would normally drop on mark
        _llm_agg("Plumbing fixtures"),          # still dropped — aggregate
    ]
    out = _dedupe_fixtures(items, mark_pattern=None)
    descs = [it.description for it in out]
    # Mark-based dedupe disabled -> the LLM row survives despite same mark.
    assert any("Fixture WC-101 (LLM-extracted" in d for d in descs)
    # Legacy aggregate path still fires.
    assert "Plumbing fixtures" not in descs
    # Synth row preserved.
    assert any(
        (it.notes or "").startswith(f"source={_FIXTURE_TAG}") for it in out
    )


# ---------------------------------------------------------------------------
# 9. Both retire paths can fire on a single row without double-counting
# ---------------------------------------------------------------------------


def test_legacy_aggregate_and_mark_both_match_row_dropped_once() -> None:
    """A row that matches *both* the aggregate regex AND a synthesised mark.

    The aggregate path fires first; the mark path is never reached. The
    row should be dropped exactly once (verified by the surviving count).
    """
    items = [
        _synth("WC"),                           # mark "WC"
        # Description matches the aggregate regex (^...fixtures$) AND
        # the synthesised mark "WC" appears as a whole token inside it.
        TakeoffItem(
            csi_division="22", csi_section="22 40 13",
            description="WC fixtures",
            quantity=6.0, unit="EA", confidence=0.85,
        ),
    ]
    out = _dedupe_fixtures(items)
    assert len(out) == 1
    assert (out[0].notes or "").startswith(f"source={_FIXTURE_TAG}")


# ---------------------------------------------------------------------------
# 10. Multiple aggregate patterns — every supplied pattern is honoured
# ---------------------------------------------------------------------------


def test_multiple_legacy_aggregate_patterns_all_honoured() -> None:
    """The tuple shape lets families register more than one regex.

    Doors use this in production for the "(type unspecified)" rollup; we
    mirror the shape here with a fixture-side synthetic second regex.
    """
    extra_re = re.compile(
        r"^fixtures?\s*\(type\s+unspecified\)\s*$",
        re.IGNORECASE,
    )
    items = [
        _synth("WC-101"),
        _llm_agg("Plumbing fixtures"),                  # matches first regex
        _llm_agg("Fixtures (type unspecified)"),        # matches second regex
        _llm_mark("Y-2"),                                # survives — mark mismatch
    ]
    out = _dedupe_fixtures(
        items,
        legacy_aggregate_patterns=(_FIXTURE_AGG_RE, extra_re),
    )
    descs = [it.description for it in out]
    assert "Plumbing fixtures" not in descs
    assert "Fixtures (type unspecified)" not in descs
    assert any("Y-2" in d for d in descs)


# ---------------------------------------------------------------------------
# 11. extract_mark_from_synthesized — helper unit tests
# ---------------------------------------------------------------------------


def test_extract_mark_from_notes_wins_over_description() -> None:
    """Notes ``mark=...`` takes precedence over the description regex."""
    item = TakeoffItem(
        csi_division="22", csi_section="22 40 13",
        description="Fixture FROM-DESC \u2014 WC",
        quantity=1.0, unit="EA", confidence=0.9,
        notes=f"source={_FIXTURE_TAG}; mark=FROM-NOTES; type=WC",
    )
    assert extract_mark_from_synthesized(
        item, source_tag=_FIXTURE_TAG, mark_pattern=_FIXTURE_MARK_RE
    ) == "FROM-NOTES"


def test_extract_mark_description_fallback_when_notes_lack_mark_segment() -> None:
    item = TakeoffItem(
        csi_division="22", csi_section="22 40 13",
        description="Fixture FROM-DESC \u2014 WC",
        quantity=1.0, unit="EA", confidence=0.9,
        notes=f"source={_FIXTURE_TAG}; type=WC",
    )
    assert extract_mark_from_synthesized(
        item, source_tag=_FIXTURE_TAG, mark_pattern=_FIXTURE_MARK_RE
    ) == "FROM-DESC"


def test_extract_mark_returns_none_when_source_tag_does_not_match() -> None:
    """Helper is a no-op for non-synth rows (notes-prefix guard)."""
    item = TakeoffItem(
        csi_division="22", csi_section="22 40 13",
        description="Fixture WC-101 \u2014 WC",
        quantity=1.0, unit="EA", confidence=0.9,
        notes="source=some_other_tag; mark=WC-101",
    )
    assert extract_mark_from_synthesized(
        item, source_tag=_FIXTURE_TAG, mark_pattern=_FIXTURE_MARK_RE
    ) is None


def test_extract_mark_returns_none_when_no_notes_and_no_mark_pattern() -> None:
    item = TakeoffItem(
        csi_division="22", csi_section="22 40 13",
        description="Fixture WC-101 \u2014 WC",
        quantity=1.0, unit="EA", confidence=0.9,
        notes=None,
    )
    assert extract_mark_from_synthesized(
        item, source_tag=_FIXTURE_TAG, mark_pattern=_FIXTURE_MARK_RE
    ) is None
