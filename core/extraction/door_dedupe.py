"""Phase T3 — retire LLM-extracted door aggregates when deterministic synthesis exists.

Phase T2 (``core.extraction.takeoff_synthesis``) emits one ``TakeoffItem``
per door from the deterministic door-schedule pre-pass. The legacy
``core.takeoff._derive_takeoffs`` keeps emitting per-material aggregate
rollups ("Hollow metal doors", "Solid-core wood doors", "Doors (type
unspecified)") that double-count whatever the schedule already covered.

This module trims the duplicates after :func:`core.takeoff.reconcile`
finishes merging. The rules are intentionally conservative:

* **Synthesised** door rows (``notes`` starts with
  ``"source=door_schedule_prepass"``) are always preserved — they are the
  authoritative source for any door they cover.
* **Non-door** rows (CSI division != ``"08"``) are always preserved.
* **LLM door** rows are dropped when *either*:
    1. A synthesised door whose mark matches the LLM row's description
       exists (per-door coverage), OR
    2. The row matches the legacy per-material aggregate pattern AND at
       least one synthesised door exists on the project (the safety rule
       — we never drop aggregates without a replacement).

Conservative on ambiguous data: an LLM door whose description carries no
recognisable mark survives untouched unless it matches the aggregate
pattern. We would rather over-count than silently lose a door we cannot
confidently attribute to a deterministic row.

The function is pure: same input → same output, no side effects, original
ordering preserved for surviving rows.
"""

from __future__ import annotations

import re

from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG
from core.schemas import TakeoffItem

__all__ = ["dedupe_doors_against_synthesis"]


# CSI Division 08 is "Openings" — doors, frames, windows, and glazing. The
# synthesiser emits ``csi_division="08"`` on every row and the legacy
# aggregates also live there, so a single division check partitions the
# items cleanly.
_CSI_DOOR_DIVISION: str = "08"

# Stable handle the T2 synthesiser plants at the start of every row's
# ``notes`` field. Composing it from the imported tag (not hard-coding the
# literal) keeps the two sides in lock-step if the tag ever changes.
_SYNTHESIS_NOTES_PREFIX: str = f"source={SYNTHESIS_SOURCE_TAG}"

# Legacy per-material aggregate descriptions emitted by
# ``core.takeoff._derive_takeoffs``. Accepts the bare form ("Hollow metal
# doors") that the current ``_derive_takeoffs`` actually emits AND the
# explicit "<N> EA" suffix form documented in the Phase T3 brief
# ("Hollow metal doors: 12 EA").
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(hollow\s+metal|solid[\-\s]?core\s+wood|wood|steel|aluminum|glass)"
    r"\s+doors?(\s*:?\s*\d+\s+ea)?\s*$",
    re.IGNORECASE,
)

# The "Doors (type unspecified)" rollup ``_derive_takeoffs`` emits when
# the LLM extracted DoorEntry rows without a usable ``type`` field.
_LEGACY_TYPE_UNSPEC_RE: re.Pattern[str] = re.compile(
    r"^doors?\s*\(type\s+unspecified\)\s*$",
    re.IGNORECASE,
)

# Pull ``mark=...`` out of a synthesised row's notes
# (``"source=...; mark=...; type=...; ..."``).
_NOTES_MARK_RE: re.Pattern[str] = re.compile(r"(?:^|;\s*)mark=([^;]+)")

# Fall-back: pull the mark out of a synthesised row's description, which
# the T2 synthesiser shapes as ``"Door <MARK> — <label> ..."``. When the
# door was unmarked the synthesiser writes ``"Door (unmarked) — ..."`` —
# the leading ``(`` deliberately fails the ``[A-Z0-9]`` start class so
# unmarked rows yield ``None``.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^door\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\-]|--)\s",
    re.IGNORECASE,
)


def _is_door(item: TakeoffItem) -> bool:
    """``True`` for CSI Division 08 (Openings) rows."""
    return (item.csi_division or "").strip().startswith(_CSI_DOOR_DIVISION)


def _is_synthesised(item: TakeoffItem) -> bool:
    """``True`` for Phase T2 synthesised rows (notes-prefix probe)."""
    notes = item.notes or ""
    return notes.startswith(_SYNTHESIS_NOTES_PREFIX)


def _is_legacy_aggregate(item: TakeoffItem) -> bool:
    """``True`` for legacy per-material rollups emitted by ``_derive_takeoffs``."""
    desc = (item.description or "").strip()
    if not desc:
        return False
    return bool(
        _LEGACY_AGGREGATE_RE.match(desc) or _LEGACY_TYPE_UNSPEC_RE.match(desc)
    )


def _extract_synthesised_mark(item: TakeoffItem) -> str | None:
    """Pull the mark off a synthesised row. Notes win; description as fallback."""
    notes = item.notes or ""
    m = _NOTES_MARK_RE.search(notes)
    if m:
        mark = m.group(1).strip()
        if mark:
            return mark
    desc = item.description or ""
    m = _DESC_MARK_RE.match(desc)
    if m:
        return m.group(1).strip()
    return None


def _mark_in_description(mark: str, desc: str) -> bool:
    """Case-insensitive whole-token match of ``mark`` inside ``desc``.

    The Phase T3 brief specifies a case-insensitive substring match. We
    tighten that with alphanumeric boundary lookarounds so a mark of
    ``"10"`` does not spuriously match ``"1010"`` or ``"$10 each"`` in
    unrelated LLM noise. Marks shorter than two characters are too
    promiscuous to dedupe on and are skipped.
    """
    if not mark or len(mark) < 2:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(mark)}(?![A-Za-z0-9])"
    return bool(re.search(pattern, desc, re.IGNORECASE))


def dedupe_doors_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted door aggregates when deterministic synthesis covers them.

    See module docstring for the full rule set. Pure function; original
    input ordering is preserved for every surviving row.

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs`` and the T2 synthesis append.

    Returns:
        The same list minus LLM door rows that the deterministic
        synthesis renders redundant. When no synthesised door exists on
        the project the input is returned unchanged (safety rule).
    """
    if not items:
        return []

    synthesised_marks: set[str] = set()
    has_synthesised_door = False
    for it in items:
        if _is_door(it) and _is_synthesised(it):
            has_synthesised_door = True
            mark = _extract_synthesised_mark(it)
            if mark:
                synthesised_marks.add(mark)

    if not has_synthesised_door:
        return list(items)

    out: list[TakeoffItem] = []
    for it in items:
        if not _is_door(it) or _is_synthesised(it):
            out.append(it)
            continue
        if _is_legacy_aggregate(it):
            continue
        desc = it.description or ""
        if any(_mark_in_description(m, desc) for m in synthesised_marks):
            continue
        out.append(it)
    return out
