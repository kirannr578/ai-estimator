"""Phase T4 — retire LLM-extracted finish aggregates when deterministic synthesis exists.

The finish-schedule pre-pass (:mod:`core.extraction.finish_schedule`) +
T4 synthesis (:mod:`core.extraction.takeoff_synthesis`) emit 3-7
``TakeoffItem`` rows per ``FinishRecord`` — one per finished surface
(floor / base / wall / ceiling). Meanwhile the legacy
``core.takeoff._derive_takeoffs`` keeps emitting per-material finish
aggregate lines (``"Carpet flooring" — N SF``, ``"VCT"``, ``"Tile
flooring"``, ``"Interior wall painting (two coats)"``, ``"Resilient
base, 4\""``). Both double-count whatever the schedule already covered.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis` — proving the
T3.5 leverage value with ~15 lines of family-specific configuration
vs. the ~95 LOC that doors/windows pre-T3.5 each carried.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_FINISH
from core.schemas import TakeoffItem

__all__ = ["dedupe_finishes_against_synthesis"]


# Finish CSI section prefixes. Mostly Division 09 (interior finishes) with
# two cross-division exceptions — ``06 64`` for FRP wall panels and
# ``03 35`` for polished concrete floors.
_FINISH_SECTION_PREFIXES: tuple[str, ...] = ("09 ", "06 64", "03 35")

# Legacy per-material finish aggregate descriptions emitted by
# ``core.takeoff._derive_takeoffs`` and typical LLM extractors. Matches
# the descriptions actually present in ``_derive_takeoffs`` plus a few
# common LLM rollup shapes. Requires a unit tail (``SF`` / ``LF`` /
# ``EA``) to avoid swallowing synthesis rows that share a leading
# token (``"Floor VCT-1 – Room 101 ..."`` starts with ``Floor`` but
# does NOT match the aggregate pattern below).
_LEGACY_FINISH_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:carpet|tile|paint|vct|vinyl|hardwood|wood\s+floor(?:ing)?|"
    r"polished\s+concrete|sealed\s+concrete|resilient\s+base|"
    r"acoustic\s+ceiling|wallcovering|wall\s+covering|frp|"
    r"gypsum\s+board|gyp\s+(?:bd|board)|interior\s+wall\s+painting|"
    r"other\s+flooring)\b[^\n]*$",
    re.IGNORECASE,
)
_LEGACY_FINISH_AGGREGATE_PATTERNS: tuple[re.Pattern[str], ...] = (
    _LEGACY_FINISH_AGGREGATE_RE,
)

# Pull the per-surface label out of a synthesised row's description,
# which the T4 synthesiser shapes as
# ``"<Surface> <CODE> – Room <#> <Name>"``. The ``mark`` captured here
# is composite (surface + code + room number) so it's effectively a
# coverage label rather than a real mark — the generic scaffold
# dedupes on description-mark match the same way regardless. The
# pattern accepts an en-dash, em-dash, or double-hyphen separator
# (mirrors the door + window patterns).
_FINISH_MARK_PATTERN: re.Pattern[str] = re.compile(
    r"^(?:Floor|Base|Wall(?:\s+[NSEW])?|Ceiling)\s+(?P<mark>[\w\-]+)\s+"
    r"(?:[\u2013\u2014\-]|--)\s+Room\s+(?P<room>\w+)\s",
    re.IGNORECASE,
)


def dedupe_finishes_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted finish aggregates when deterministic synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set. Pure
    function; original input ordering is preserved for every surviving
    row. When no synthesised finish exists anywhere on the project,
    the input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2/T2.5/T3/T2.5 door + window
            passes, AND the T4 finish-synthesis append.

    Returns:
        The same list minus LLM finish rows that the deterministic
        synthesis renders redundant. Door + window rows are NEVER
        touched (cross-pollination safety: ``08 ...`` sections fall
        outside ``_FINISH_SECTION_PREFIXES``).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_FINISH,
        section_prefixes=_FINISH_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=_LEGACY_FINISH_AGGREGATE_PATTERNS,
        mark_pattern=_FINISH_MARK_PATTERN,
        family_label="finish",
        match_family_by_description=True,
    )
