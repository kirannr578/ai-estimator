"""Phase T2.5 — retire LLM-extracted window aggregates when deterministic synthesis exists.

The window-schedule pre-pass (:mod:`core.extraction.window_schedule`) +
T2.5 synthesis (:mod:`core.extraction.takeoff_synthesis`) emit one
``TakeoffItem`` per window. Meanwhile the legacy
``core.takeoff._derive_takeoffs`` keeps emitting a single per-project
aggregate window line (``"Windows" — N EA``) plus any per-material
aggregates the LLM may have surfaced (``"Aluminum windows"``,
``"Vinyl windows"``, etc.). Both double-count whatever the schedule
already covers.

This module trims the duplicates after :func:`core.takeoff.reconcile`
finishes merging. The rules mirror the Phase T3 door dedupe but with
window-specific discriminators:

* **Synthesised** window rows (``notes`` starts with
  ``"source=window_schedule_prepass"``) are always preserved — they are
  the authoritative source for any window they cover.
* **Non-window** rows are always preserved. "Window" here means a CSI
  Division 08 row whose ``csi_section`` starts with one of the
  documented window sections (``08 41``, ``08 44``, ``08 5*``) OR whose
  description matches the legacy-aggregate / per-mark patterns. Door
  rows (``08 11`` / ``08 14`` / ``08 71`` / ``08 80``) and synthesised
  door rows are intentionally untouched by this pass.
* **LLM window** rows are dropped when *either*:
    1. A synthesised window whose mark matches the LLM row's description
       exists (per-window coverage), OR
    2. The row matches the legacy aggregate pattern (bare ``Windows`` /
       per-material rollup) AND at least one synthesised window exists
       on the project (the safety rule — we never drop aggregates
       without a replacement).

The function is pure: same input → same output, no side effects,
original ordering preserved for surviving rows.

Architectural choice (α). This module deliberately *mirrors*
``door_dedupe.py`` rather than generalising both into a parametrised
``dedupe_against_synthesis()``. The Phase T3 worker flagged
generalisation as the next big move and the T2.5 brief presents Option
α (mirror) and Option β (generalise) as alternatives; we picked α
because the door and window dedupe rules differ in three non-trivial
ways (window section is a regex over multiple prefixes, the legacy
aggregate set is shorter, and there's no equivalent of door's
``Doors (type unspecified)`` rollup). The generalisation is queued as a
Phase T3.5 follow-up — see :file:`docs/ROADMAP_TAKEOFF_AUTOMATION.md`.
"""

from __future__ import annotations

import re

from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_WINDOW
from core.schemas import TakeoffItem

__all__ = ["dedupe_windows_against_synthesis"]


# Stable handle the T2.5 synthesiser plants at the start of every row's
# ``notes`` field. Composing it from the imported tag (not hard-coding
# the literal) keeps the two sides in lock-step if the tag ever changes.
_SYNTHESIS_NOTES_PREFIX: str = f"source={SYNTHESIS_SOURCE_TAG_WINDOW}"

# Window CSI section prefixes. Restricted to the sub-tree of Division 08
# that windows + storefronts + curtain walls actually live in, so this
# pass NEVER touches door rows (which live at ``08 11`` / ``08 14`` /
# ``08 71`` / ``08 80``).
#
# * ``08 41`` — Entrances & Storefronts (Aluminum Storefronts)
# * ``08 44`` — Curtain Wall & Glazed Assemblies (Aluminum Curtain Walls)
# * ``08 5*`` — Windows (50 = generic, 51 = Metal, 52 = Wood, 53 = Plastic)
_WINDOW_SECTION_PREFIXES: tuple[str, ...] = (
    "08 41", "08 44", "08 50", "08 51", "08 52", "08 53",
)

# Legacy per-material aggregate descriptions. Covers the bare ``Windows``
# line that ``_derive_takeoffs`` actually emits today AND the
# per-material forms (``Aluminum windows``, ``Vinyl windows``,
# ``Wood windows``, ``Steel windows``, ``Storefront windows``) that an
# LLM extractor might surface. The optional ``: N EA`` tail mirrors the
# door-dedupe regex shape so explicit-count forms also match.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(aluminum|vinyl|wood|steel|metal[\-\s]?clad|storefront|curtain\s*wall|glass)?"
    r"\s*windows?(\s*:?\s*\d+\s+ea)?\s*$",
    re.IGNORECASE,
)

# Pull ``mark=...`` out of a synthesised row's notes
# (``"source=...; mark=...; type=...; ..."``).
_NOTES_MARK_RE: re.Pattern[str] = re.compile(r"(?:^|;\s*)mark=([^;]+)")

# Fall-back: pull the mark out of a synthesised row's description, which
# the T2.5 synthesiser shapes as ``"Window <MARK> — <label> ..."``. When
# the window was unmarked the synthesiser writes ``"Window (unmarked) — ..."``
# — the leading ``(`` deliberately fails the ``[A-Z0-9]`` start class so
# unmarked rows yield ``None``.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^window\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\-]|--)\s",
    re.IGNORECASE,
)


def _is_window_row(item: TakeoffItem) -> bool:
    """``True`` for CSI Division 08 window/storefront/curtain-wall rows.

    Recognised in two ways:
    1. ``csi_section`` starts with one of ``_WINDOW_SECTION_PREFIXES``,
       OR
    2. The description matches the legacy aggregate pattern OR contains
       a synth-shaped ``"Window <MARK>"`` head. (2) catches LLM rows
       that landed without an explicit section.
    """
    section = (item.csi_section or "").strip()
    if any(section.startswith(p) for p in _WINDOW_SECTION_PREFIXES):
        return True
    desc = (item.description or "").strip()
    if not desc:
        return False
    if _LEGACY_AGGREGATE_RE.match(desc):
        return True
    if _DESC_MARK_RE.match(desc):
        return True
    return False


def _is_synthesised(item: TakeoffItem) -> bool:
    """``True`` for Phase T2.5 synthesised window rows (notes-prefix probe)."""
    notes = item.notes or ""
    return notes.startswith(_SYNTHESIS_NOTES_PREFIX)


def _is_legacy_aggregate(item: TakeoffItem) -> bool:
    """``True`` for legacy per-material window rollups."""
    desc = (item.description or "").strip()
    if not desc:
        return False
    return bool(_LEGACY_AGGREGATE_RE.match(desc))


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

    Mirrors :func:`core.extraction.door_dedupe._mark_in_description`:
    alphanumeric boundary lookarounds prevent a mark of ``"01"`` from
    spuriously matching ``"101"``. Marks shorter than two characters are
    too promiscuous to dedupe on and are skipped.
    """
    if not mark or len(mark) < 2:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(mark)}(?![A-Za-z0-9])"
    return bool(re.search(pattern, desc, re.IGNORECASE))


def dedupe_windows_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted window aggregates when deterministic synthesis covers them.

    See module docstring for the full rule set. Pure function; original
    input ordering is preserved for every surviving row. When no
    synthesised window exists anywhere on the project, the input is
    returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2 door-synthesis append, the T3
            door dedupe, AND the T2.5 window-synthesis append.

    Returns:
        The same list minus LLM window rows that the deterministic
        synthesis renders redundant.
    """
    if not items:
        return []

    synthesised_marks: set[str] = set()
    has_synthesised_window = False
    for it in items:
        if _is_window_row(it) and _is_synthesised(it):
            has_synthesised_window = True
            mark = _extract_synthesised_mark(it)
            if mark:
                synthesised_marks.add(mark)

    if not has_synthesised_window:
        return list(items)

    out: list[TakeoffItem] = []
    for it in items:
        if not _is_window_row(it) or _is_synthesised(it):
            out.append(it)
            continue
        if _is_legacy_aggregate(it):
            continue
        desc = it.description or ""
        if any(_mark_in_description(m, desc) for m in synthesised_marks):
            continue
        out.append(it)
    return out
