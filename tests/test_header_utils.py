"""Tests for the Phase T3.6 shared ``header_utils`` module.

The ``header_index_excluding`` helper was promoted out of
:mod:`core.extraction.door_schedule` once it became load-bearing
across door / panel / lighting extractors and the T2.8 HVAC slice
made it the FOURTH consumer.  These tests pin the helper's contract
directly so a future refactor can't silently regress the
short-vs-long header collision behaviour all four extractors rely on.

The legacy ``_header_index_excluding`` alias on ``door_schedule``
is also tested so frozen downstream modules (``finish_schedule``,
``room_schedule``, ``window_schedule``) keep working.
"""

from __future__ import annotations

from core.extraction.header_utils import (
    header_index_excluding,
    normalize_header,
)


# ---------------------------------------------------------------------------
# Standard inclusion paths
# ---------------------------------------------------------------------------


def test_returns_first_word_match_with_no_exclusions() -> None:
    """Vanilla case: ``"ROOM"`` in ``["ROOM", "DOOR"]`` → 0."""
    assert header_index_excluding(
        ["ROOM", "DOOR"], ("ROOM",), exclude=set()
    ) == 0


def test_returns_first_substring_match_when_word_match_misses() -> None:
    """Substring fallback fires when no word-level hit exists."""
    assert header_index_excluding(
        ["ROOM NUMBER", "TYPE"], ("NUMBER",), exclude=set()
    ) == 0


def test_returns_none_when_no_header_matches() -> None:
    """No candidate present anywhere → None (caller handles missing column)."""
    assert header_index_excluding(
        ["TAG", "DESCRIPTION"], ("HARDWARE",), exclude=set()
    ) is None


def test_returns_none_for_empty_headers() -> None:
    """Empty header list short-circuits to None."""
    assert header_index_excluding([], ("MARK",), exclude=set()) is None


# ---------------------------------------------------------------------------
# Substring collision — the headline use case
# ---------------------------------------------------------------------------


def test_room_number_excluded_does_not_steal_number_candidate() -> None:
    """``ROOM NUMBER`` excluded → ``NUMBER`` candidate finds no other column."""
    headers = ["ROOM NUMBER", "TYPE"]
    # When ROOM NUMBER (index 0) is excluded, the substring-tolerant
    # NUMBER lookup finds nothing else.
    assert header_index_excluding(
        headers, ("MARK", "NUMBER"), exclude={0}
    ) is None


def test_room_number_excluded_finds_separate_mark_column() -> None:
    """When MARK lives in a different column, exclusion of ROOM NUMBER pins it."""
    headers = ["ROOM NUMBER", "MARK", "TYPE"]
    assert header_index_excluding(
        headers, ("MARK", "NUMBER"), exclude={0}
    ) == 1


def test_wattage_excluded_finds_short_w_column() -> None:
    """T2.7 lighting reuse: ``WATTAGE`` pinned → bare ``W`` resolves elsewhere."""
    headers = ["TAG", "WATTAGE", "W"]
    assert header_index_excluding(
        headers, ("W",), exclude={1}
    ) == 2


def test_amps_excluded_finds_phase_letter_column() -> None:
    """T2.6 panel reuse: ``AMPS`` pinned → bare ``A`` resolves elsewhere.

    Models the real T2.6 wire-in: the panel-schedule header picker
    pins ``AMPS`` (index 1) first via the long candidate set, then
    re-runs the bare letter PHASE candidate with that index excluded.
    A bare-letter PHASE column at the right edge of the table must
    still resolve to its own column rather than slipping back onto
    ``AMPS`` via the substring matcher.
    """
    headers = ["NUMBER", "AMPS", "A"]
    assert header_index_excluding(
        headers, ("A",), exclude={1}
    ) == 2


# ---------------------------------------------------------------------------
# Multi-exclusion + ordering
# ---------------------------------------------------------------------------


def test_multiple_exclusions_skip_all_named_columns() -> None:
    """Pass the helper several already-claimed indices in one call."""
    headers = ["TAG", "DESCRIPTION", "WATTS", "VOLTAGE", "MOUNTING"]
    # Pre-claim TAG (0), DESCRIPTION (1), WATTS (2). Looking for VOLTAGE
    # finds the only remaining match at index 3.
    assert header_index_excluding(
        headers, ("VOLTAGE",), exclude={0, 1, 2}
    ) == 3


def test_returns_first_match_when_multiple_exist() -> None:
    """Iteration is left-to-right; first non-excluded hit wins."""
    headers = ["A", "A", "B"]
    assert header_index_excluding(headers, ("A",), exclude=set()) == 0
    assert header_index_excluding(headers, ("A",), exclude={0}) == 1
    assert header_index_excluding(headers, ("A",), exclude={0, 1}) is None


# ---------------------------------------------------------------------------
# Whitespace + case + edge cases
# ---------------------------------------------------------------------------


def test_case_insensitive_match() -> None:
    """Headers are upper-cased internally — lower-case input still matches."""
    assert header_index_excluding(
        ["mark", "type"], ("MARK",), exclude=set()
    ) == 0


def test_whitespace_tolerated_in_header() -> None:
    """``"  MARK  "`` matches ``"MARK"`` after normalisation."""
    assert header_index_excluding(
        ["  MARK  ", "TYPE"], ("MARK",), exclude=set()
    ) == 0


def test_punctuation_stripped_during_normalisation() -> None:
    """``"ROOM #"`` normalises to ``"ROOM"`` — the ``#`` is dropped."""
    assert header_index_excluding(
        ["ROOM #", "TYPE"], ("ROOM",), exclude=set()
    ) == 0


def test_same_string_candidate_and_excluded_returns_none() -> None:
    """When the only matching column is itself excluded → None."""
    headers = ["MARK"]
    assert header_index_excluding(
        headers, ("MARK",), exclude={0}
    ) is None


def test_handles_none_in_header_row_gracefully() -> None:
    """``None`` cells (PyMuPDF returns these for unparsed cells) → skipped."""
    # PyMuPDF table.extract() can yield ``None`` for empty cells; the
    # helper normalises ``""`` for those and they don't match anything.
    assert header_index_excluding(
        ["", "MARK", ""], ("MARK",), exclude=set()
    ) == 1


# ---------------------------------------------------------------------------
# normalize_header — exposed companion helper
# ---------------------------------------------------------------------------


def test_normalize_header_drops_punctuation_and_uppercases() -> None:
    assert normalize_header("room #") == "ROOM"
    assert normalize_header("room number.") == "ROOM NUMBER"
    assert normalize_header("") == ""
    assert normalize_header(None) == ""  # type: ignore[arg-type]


# ---------------------------------------------------------------------------
# Backward-compat alias on door_schedule (used by frozen consumers)
# ---------------------------------------------------------------------------


def test_door_schedule_legacy_alias_still_imports() -> None:
    """``finish_schedule`` / ``room_schedule`` / ``window_schedule`` still
    do ``from .door_schedule import _header_index_excluding``; this
    alias must continue to resolve to the shared helper.
    """
    from core.extraction.door_schedule import _header_index_excluding
    from core.extraction.header_utils import header_index_excluding as canonical

    assert _header_index_excluding is canonical


def test_door_schedule_legacy_alias_runtime_behaviour() -> None:
    """The aliased name must produce identical answers as the canonical one."""
    from core.extraction.door_schedule import _header_index_excluding

    headers = ["ROOM NUMBER", "MARK"]
    assert _header_index_excluding(
        headers, ("MARK", "NUMBER"), exclude={0}
    ) == 1
