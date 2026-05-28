"""Phase T2.6 — retire LLM-extracted electrical-panel aggregates when synthesis exists.

The panel-schedule pre-pass (:mod:`core.extraction.panel_schedule`) +
T2.6 synthesis (:mod:`core.extraction.takeoff_synthesis`) emit four
``TakeoffItem`` families per ``PanelRecord``: panel enclosure
(26 24 16 / 26 24 13), branch breakers (26 28 16), feeder conductor
(26 05 19), feeder conduit (26 05 33). Meanwhile the legacy
``core.takeoff._derive_takeoffs`` keeps emitting per-panel aggregate
LLM rows under section ``26 24 16`` whenever an ``MEPItem`` mentioning
"panel" lands in the project model.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis`. It supplies
the panel-specific discriminators:

* CSI prefixes restricted to ``26 24`` (panelboards + switchboards)
  and ``26 28`` (circuit breakers) so the pass NEVER touches
  receptacles (``26 27 26``), lighting (``26 51 ...``), grounding
  (``26 05 26``), or other Division 26 rows.
* Legacy aggregate descriptions: ``Electrical Panel``, ``Panel A``,
  ``Panelboard``, ``Branch Circuit Breakers``, and the ``: N EA``
  trailing-count form. Description-match enabled (``match_family_by_
  description=True``) because LLM panel rows often land with an
  empty / generic section.
* Mark pattern: ``Panel <ID>`` matches the synthesised description
  shape and the typical LLM "Panel A — 200A" shape so per-mark dedupe
  catches both. Feeder conductor / conduit rows are NOT under the
  ``26 24`` / ``26 28`` prefix set — they're intentionally exempt
  from dedupe because the parametric 50 LF default needs the LLM
  estimate (when present) to land in the worklist, not be silently
  dropped.

See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_PANEL
from core.schemas import TakeoffItem

__all__ = ["dedupe_panels_against_synthesis"]


# Panel CSI section prefixes. ``26 24`` catches panelboards (26 24 16)
# and switchboards (26 24 13); ``26 28`` catches circuit breakers
# (26 28 16). Feeder wire (26 05 19) and feeder conduit (26 05 33)
# are intentionally excluded — see module docstring.
_PANEL_SECTION_PREFIXES: tuple[str, ...] = ("26 24", "26 28")

# Legacy per-panel aggregate descriptions. Covers the common LLM rollup
# shapes plus the bare ``Panel`` / ``Panelboard`` / ``Switchboard`` /
# ``Distribution Panel`` forms the legacy ``_derive_takeoffs`` MEP path
# emits when a panel mention lands in the project model. The optional
# tail ``(?:[\s,:\-].*?)?`` accepts:
#
#   - ``"Electrical Panel"``               (bare prefix)
#   - ``"Electrical Panel A"``             (space + ID)
#   - ``"Electrical Panel A, 200A"``       (space + ID + comma + amps)
#   - ``"Electrical Panel: PNL-A"``        (colon + explicit mark)
#   - ``"Panelboard 200A"``                (space + amps)
#   - ``"Branch Circuit Breakers: 12 EA"`` (colon + count)
#
# The tail is non-greedy and anchored at end-of-string with optional
# trailing whitespace so an exact-equals "Panelboard" still matches.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    r"electrical\s+panel(?:s|board|boards)?|"
    r"panelboard(?:s)?|"
    r"switchboard(?:s)?|"
    r"distribution\s+(?:panel|board)(?:s)?|"
    r"main\s+(?:distribution\s+)?(?:panel|board)(?:s|board)?|"
    r"branch(?:\s+circuit)?\s+breakers?|"
    r"circuit\s+breakers?|"
    r"panels?\s+\(.*?\)"
    r")\b(?:[\s,:\-].*?)?\s*$",
    re.IGNORECASE,
)

# Pull the panel ID out of the synthesised row's description, which
# the T2.6 synthesiser shapes as ``"Panel <ID> — <family> ..."`` for
# the enclosure row, ``"Panel <ID> — Branch breakers ..."`` for the
# breaker-group rows, and ``"Panel <ID> — Feeder ..."`` for the two
# feeder rows. The leading ``(`` on a hypothetical unmarked panel
# would fail the ``[A-Z0-9]`` start class so unmarked rows yield
# ``None`` (defensive — the extractor already filters these).
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^panel\s+([A-Z0-9][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_panels_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Trim LLM-extracted electrical-panel aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set. Pure
    function; original input ordering is preserved for every surviving
    row. When no synthesised panel exists anywhere on the project,
    the input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2/T2.5/T3/T4 + finish synthesis
            and the T2.6 panel-synthesis appends.

    Returns:
        The same list minus LLM panel rows that the deterministic
        synthesis renders redundant. Door / window / finish rows are
        NEVER touched (CSI prefix discriminator: ``26 24`` / ``26 28``
        is mutually exclusive with the ``08 ...`` / ``09 ...`` prefixes
        the upstream dedupes use). Feeder conductor / conduit synthesis
        rows are ALSO never touched (their sections fall outside the
        prefix set above).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_PANEL,
        section_prefixes=_PANEL_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="panel",
        match_family_by_description=True,
    )
