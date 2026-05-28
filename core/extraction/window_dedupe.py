"""Phase T2.5 — retire LLM-extracted window aggregates when deterministic synthesis exists.

The window-schedule pre-pass (:mod:`core.extraction.window_schedule`) +
T2.5 synthesis (:mod:`core.extraction.takeoff_synthesis`) emit one
``TakeoffItem`` per window. Meanwhile the legacy
``core.takeoff._derive_takeoffs`` keeps emitting a single per-project
aggregate window line (``"Windows" — N EA``) plus any per-material
aggregates the LLM may have surfaced (``"Aluminum windows"``,
``"Vinyl windows"``, etc.). Both double-count whatever the schedule
already covers.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis`. It supplies
the window-specific discriminators (narrower CSI subsection prefixes
``08 41`` / ``08 44`` / ``08 5*`` so the pass NEVER touches doors at
``08 11`` / ``08 14`` / ``08 71`` / ``08 80``, the per-material
window-aggregate regex, the ``^Window <MARK> — `` description regex,
and the description-based family fallback for uncategorised LLM
rows). See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_WINDOW
from core.schemas import TakeoffItem

__all__ = ["dedupe_windows_against_synthesis"]


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

# Pull the mark out of a synthesised row's description, which the T2.5
# synthesiser shapes as ``"Window <MARK> — <label> ..."``. When the
# window was unmarked the synthesiser writes ``"Window (unmarked) — ..."``
# — the leading ``(`` deliberately fails the ``[A-Z0-9]`` start class so
# unmarked rows yield ``None``.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^window\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_windows_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted window aggregates when deterministic synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set. Pure
    function; original input ordering is preserved for every surviving
    row. When no synthesised window exists anywhere on the project, the
    input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2 door-synthesis append, the T3
            door dedupe, AND the T2.5 window-synthesis append.

    Returns:
        The same list minus LLM window rows that the deterministic
        synthesis renders redundant.
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_WINDOW,
        section_prefixes=_WINDOW_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="window",
        match_family_by_description=True,
    )
