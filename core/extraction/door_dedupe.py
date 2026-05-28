"""Phase T3 — retire LLM-extracted door aggregates when deterministic synthesis exists.

Phase T2 (``core.extraction.takeoff_synthesis``) emits one ``TakeoffItem``
per door from the deterministic door-schedule pre-pass. The legacy
``core.takeoff._derive_takeoffs`` keeps emitting per-material aggregate
rollups ("Hollow metal doors", "Solid-core wood doors", "Doors (type
unspecified)") that double-count whatever the schedule already covered.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis`. It supplies
the door-specific discriminators (Division 08 catches everything, two
legacy-aggregate regexes for per-material rollups plus the "(type
unspecified)" rollup, and the ``^Door <MARK> — `` description regex).
See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG
from core.schemas import TakeoffItem

__all__ = ["dedupe_doors_against_synthesis"]


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

# Pull the mark out of a synthesised row's description, which the T2
# synthesiser shapes as ``"Door <MARK> — <label> ..."``. When the door
# was unmarked the synthesiser writes ``"Door (unmarked) — ..."`` — the
# leading ``(`` deliberately fails the ``[A-Z0-9]`` start class so
# unmarked rows yield ``None``.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^door\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_doors_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted door aggregates when deterministic synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set. Pure
    function; original input ordering is preserved for every surviving
    row.

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs`` and the T2 synthesis append.

    Returns:
        The same list minus LLM door rows that the deterministic
        synthesis renders redundant. When no synthesised door exists on
        the project the input is returned unchanged (safety rule).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG,
        section_prefixes=("08",),
        section_field="csi_division",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE, _LEGACY_TYPE_UNSPEC_RE),
        mark_pattern=_DESC_MARK_RE,
        family_label="door",
        match_family_by_description=False,
    )
