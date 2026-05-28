"""Phase T3.5 — generic dedupe-by-source-tag scaffold for schedule-driven takeoffs.

This module is the parametrised skeleton extracted from
:mod:`core.extraction.door_dedupe` (Phase T3) and
:mod:`core.extraction.window_dedupe` (Phase T2.5). Both modules now reduce
to thin wrappers that supply the family-specific discriminators (CSI
prefix set, legacy-aggregate regex, mark regex, synthesis source tag).

Strategy. Given a list of ``TakeoffItem`` rows that have already passed
through :func:`core.takeoff.reconcile` (merge complete, synthesised rows
appended), drop the LLM-extracted rows that a deterministic-synthesis
row already covers — and only those rows.

Rules. For a given ``source_tag`` (e.g. ``"door_schedule_prepass"``):

* **Synthesised** family rows (``notes`` starts with
  ``f"source={source_tag}"``) are always preserved — they are the
  authoritative source for any item they cover.
* **Out-of-family** rows are always preserved (door dedupe never touches
  windows and vice-versa; see ``section_prefixes`` /
  ``match_family_by_description``).
* **LLM family** rows are dropped when *either*:
    1. A synthesised family row whose mark matches the LLM row's
       description exists (per-item coverage), OR
    2. The row matches one of the ``legacy_aggregate_patterns`` AND at
       least one synthesised family row exists on the project (the
       safety rule — we never drop aggregates without a replacement).

Pure function: same input → same output, no side effects, original
ordering preserved for every surviving row.

Asymmetries to be aware of when wiring a new family:

* Doors discriminate on ``csi_division`` (the entire MasterFormat
  Division 08); windows discriminate on ``csi_section`` (a narrower set
  of subsection prefixes inside Division 08). The ``section_field``
  parameter (defaults to ``"csi_section"``) picks which field the
  prefix-match is run against — pass ``"csi_division"`` for the
  division-wide pattern.
* Doors only consider a row in-family when its section/division
  matches. Windows additionally treat a row as in-family when its
  description matches one of the family's regexes (legacy aggregate
  OR mark pattern), even with an empty/uncategorised section. The
  ``match_family_by_description`` flag enables the description
  fallback (default off, matching door semantics).
* Doors carry a second legacy-aggregate regex
  (``"Doors (type unspecified)"``); windows do not. The
  ``legacy_aggregate_patterns`` parameter is a tuple so callers can
  pass however many regexes they need.
"""

from __future__ import annotations

import re
from typing import Literal

from core.schemas import TakeoffItem

__all__ = [
    "dedupe_against_synthesis",
    "extract_mark_from_synthesized",
]


# Pull ``mark=...`` out of a synthesised row's notes
# (``"source=...; mark=...; type=...; ..."``). Universal across families
# because :mod:`core.extraction.takeoff_synthesis` emits the same
# ``source=...; mark=...`` shape for doors and windows alike.
_NOTES_MARK_RE: re.Pattern[str] = re.compile(r"(?:^|;\s*)mark=([^;]+)")


def extract_mark_from_synthesized(
    item: TakeoffItem,
    *,
    source_tag: str,
    mark_pattern: re.Pattern[str] | None = None,
) -> str | None:
    """Pull the mark off a synthesised row. Notes win; description as fallback.

    Returns ``None`` unless ``item.notes`` starts with
    ``f"source={source_tag}"`` — the helper is intentionally a no-op
    on non-synth rows so callers can apply it indiscriminately.

    Args:
        item: A ``TakeoffItem`` candidate.
        source_tag: The synthesis tag identifying this family (e.g.
            ``"door_schedule_prepass"``). Acts as a guard.
        mark_pattern: Description-based fallback regex, capturing the
            mark in group 1 (e.g. ``r"^door\\s+([A-Z0-9...]+)\\s+—\\s"``).
            ``None`` disables the description fallback.

    Returns:
        The mark string if recoverable, else ``None``.
    """
    notes = item.notes or ""
    if not notes.startswith(f"source={source_tag}"):
        return None
    m = _NOTES_MARK_RE.search(notes)
    if m:
        mark = m.group(1).strip()
        if mark:
            return mark
    if mark_pattern is not None:
        desc = item.description or ""
        m = mark_pattern.match(desc)
        if m:
            return m.group(1).strip()
    return None


def _is_synthesised(item: TakeoffItem, source_tag: str) -> bool:
    notes = item.notes or ""
    return notes.startswith(f"source={source_tag}")


def _section_prefix_match(
    item: TakeoffItem,
    section_prefixes: tuple[str, ...],
    section_field: str,
) -> bool:
    field = (getattr(item, section_field, None) or "").strip()
    if not field:
        return False
    return any(field.startswith(p) for p in section_prefixes)


def _is_in_family(
    item: TakeoffItem,
    *,
    section_prefixes: tuple[str, ...],
    section_field: str,
    legacy_aggregate_patterns: tuple[re.Pattern[str], ...],
    mark_pattern: re.Pattern[str] | None,
    match_family_by_description: bool,
) -> bool:
    if _section_prefix_match(item, section_prefixes, section_field):
        return True
    if not match_family_by_description:
        return False
    desc = (item.description or "").strip()
    if not desc:
        return False
    if any(p.match(desc) for p in legacy_aggregate_patterns):
        return True
    if mark_pattern is not None and mark_pattern.match(desc):
        return True
    return False


def _matches_any_legacy_aggregate(
    item: TakeoffItem,
    legacy_aggregate_patterns: tuple[re.Pattern[str], ...],
) -> bool:
    desc = (item.description or "").strip()
    if not desc:
        return False
    return any(p.match(desc) for p in legacy_aggregate_patterns)


def _mark_in_description(mark: str, desc: str) -> bool:
    """Case-insensitive whole-token match of ``mark`` inside ``desc``.

    Alphanumeric boundary lookarounds prevent a mark of ``"10"`` from
    spuriously matching ``"1010"`` or ``"$10 each"`` in unrelated LLM
    noise. Marks shorter than two characters are too promiscuous to
    dedupe on and are skipped.
    """
    if not mark or len(mark) < 2:
        return False
    pattern = rf"(?<![A-Za-z0-9]){re.escape(mark)}(?![A-Za-z0-9])"
    return bool(re.search(pattern, desc, re.IGNORECASE))


def dedupe_against_synthesis(
    items: list[TakeoffItem],
    *,
    source_tag: str,
    section_prefixes: tuple[str, ...],
    legacy_aggregate_patterns: tuple[re.Pattern[str], ...],
    family_label: str,
    mark_pattern: re.Pattern[str] | None = None,
    section_field: Literal["csi_division", "csi_section"] = "csi_section",
    match_family_by_description: bool = False,
) -> list[TakeoffItem]:
    """Retire LLM-extracted aggregate rows when deterministic synthesis covers them.

    Generic scaffold used by both Phase T3 (doors) and Phase T2.5
    (windows). See module docstring for the full rule set.

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs`` and the relevant synthesis append.
        source_tag: The synthesis tag identifying this family (e.g.
            ``"door_schedule_prepass"``). Composed into
            ``f"source={source_tag}"`` for the notes-prefix probe.
        section_prefixes: CSI prefixes that define the family (e.g.
            ``("08",)`` for doors — the entire Division 08; or
            ``("08 41", "08 44", "08 50", "08 51", "08 52", "08 53")``
            for windows).
        legacy_aggregate_patterns: One or more anchored regexes that
            identify legacy per-material aggregate rows
            (e.g. ``"Hollow metal doors"``, ``"Aluminum windows: 12 EA"``).
        family_label: Informational label (``"door"`` /
            ``"window"`` / ...). Currently unused at runtime; reserved
            for future log messages and error attribution.
        mark_pattern: Description regex that captures the mark in
            group 1 (e.g. ``r"^door\\s+([A-Z0-9...]+)\\s+—\\s"``). When
            ``None``, per-mark dedupe is disabled — only legacy-aggregate
            dropping fires.
        section_field: Which TakeoffItem field the ``section_prefixes``
            are matched against. ``"csi_division"`` for doors (Division
            08 catches everything), ``"csi_section"`` for windows
            (narrower subsection prefixes). Defaults to ``"csi_section"``.
        match_family_by_description: When ``True``, additionally treat a
            row as in-family if its description matches one of the
            legacy aggregate patterns OR the mark pattern. Defaults to
            ``False``. Set to ``True`` for windows (legacy LLM rows
            often land with an empty / uncategorised section).

    Returns:
        The input list minus the LLM family rows that the deterministic
        synthesis renders redundant. Original ordering is preserved for
        every surviving row. When no synthesised family row exists
        anywhere on the project the input is returned unchanged (safety
        rule — we never drop aggregates without a replacement).
    """
    del family_label  # informational only; reserved for future logging
    if not items:
        return []

    synthesised_marks: set[str] = set()
    has_synthesised_family_row = False
    for it in items:
        if not _is_in_family(
            it,
            section_prefixes=section_prefixes,
            section_field=section_field,
            legacy_aggregate_patterns=legacy_aggregate_patterns,
            mark_pattern=mark_pattern,
            match_family_by_description=match_family_by_description,
        ):
            continue
        if not _is_synthesised(it, source_tag):
            continue
        has_synthesised_family_row = True
        mark = extract_mark_from_synthesized(
            it, source_tag=source_tag, mark_pattern=mark_pattern
        )
        if mark:
            synthesised_marks.add(mark)

    if not has_synthesised_family_row:
        return list(items)

    out: list[TakeoffItem] = []
    for it in items:
        in_family = _is_in_family(
            it,
            section_prefixes=section_prefixes,
            section_field=section_field,
            legacy_aggregate_patterns=legacy_aggregate_patterns,
            mark_pattern=mark_pattern,
            match_family_by_description=match_family_by_description,
        )
        if not in_family or _is_synthesised(it, source_tag):
            out.append(it)
            continue
        if _matches_any_legacy_aggregate(it, legacy_aggregate_patterns):
            continue
        if mark_pattern is not None and synthesised_marks:
            desc = it.description or ""
            if any(_mark_in_description(m, desc) for m in synthesised_marks):
                continue
        out.append(it)
    return out
