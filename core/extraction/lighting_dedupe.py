"""Phase T2.7 — retire LLM-extracted lighting aggregates when synthesis exists.

The lighting-fixture-schedule pre-pass
(:mod:`core.extraction.lighting_schedule`) + T2.7 synthesis
(:mod:`core.extraction.takeoff_synthesis`) emit 1-2 ``TakeoffItem``
families per ``LightingFixtureRecord``: the fixture itself
(``26 51 13`` interior or ``26 51 19`` wall-mounted) and optionally
a lamp/driver LS line (``26 55 53``) for non-LED-integrated
technologies.  Meanwhile the legacy ``core.takeoff._derive_takeoffs``
keeps emitting per-discipline aggregate LLM rows under section
``26 51 00`` whenever an ``MEPItem`` mentioning ``"light"`` /
``"lighting"`` / ``"fixture"`` / ``"luminaire"`` lands in the
project model.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis` (mirroring
:mod:`core.extraction.panel_dedupe`).  It supplies the lighting-
specific discriminators:

* CSI prefixes restricted to ``26 51`` (lighting fixtures —
  interior overhead + wall-mounted) and ``26 55`` (lamps) so the
  pass NEVER touches panels (``26 24 ...``), breakers
  (``26 28 ...``), feeders (``26 05 ...``), receptacles
  (``26 27 ...``), grounding (``26 05 26``), or other Division 26
  rows that belong to other extractors.
* Legacy aggregate descriptions: ``Lighting Fixtures``, ``Light
  Fixtures``, ``LED Lighting``, ``Luminaires``, ``Type A Fixture``,
  and the ``: N EA`` trailing-count form.  Description-match enabled
  (``match_family_by_description=True``) because LLM lighting rows
  often land with a generic ``"26"`` division and an empty
  ``csi_section``.
* Mark pattern: ``Fixture <TAG>`` (or ``Type <TAG>``) matches the
  synthesised description shape and the typical LLM ``"Type A —
  LED downlight"`` shape so per-mark dedupe catches both.

See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_LIGHTING
from core.schemas import TakeoffItem

__all__ = ["dedupe_lighting_against_synthesis"]


# Lighting CSI section prefixes.  ``26 51`` catches both interior
# overhead lighting (26 51 13) and wall-mounted lighting (26 51 19);
# ``26 55`` catches the lamp / driver replacement line (26 55 53).
# Exterior site lighting (``26 56 ...``) is intentionally excluded —
# the parametric synthesis routes WALL PACK and similar fixtures
# there as a side-channel and we want the LLM's per-pole / per-wall-
# pack rollup to land in the worklist for the estimator to compare.
_LIGHTING_SECTION_PREFIXES: tuple[str, ...] = ("26 51", "26 55")

# Legacy per-discipline lighting aggregate descriptions.  Covers the
# common LLM rollup shapes plus the bare ``Lighting Fixtures`` /
# ``Luminaires`` forms the legacy ``_derive_takeoffs`` MEP path emits
# when a lighting mention lands in the project model.  Pattern shape
# mirrors :mod:`panel_dedupe._LEGACY_AGGREGATE_RE` — anchored on
# common prefixes with an optional ``[ ,:\-]`` tail to accept the
# ``"Lighting Fixtures: 12 EA"`` / ``"LED downlights — 277V"`` /
# ``"Luminaires"`` shapes.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    r"lighting\s+fixtures?|"
    r"light\s+fixtures?|"
    r"luminaires?|"
    r"led\s+(?:lighting|fixtures?|downlights?|troffers?|panels?|sconces?|"
    r"strips?|wall\s+packs?|lights?)|"
    r"fluorescent\s+(?:lighting|fixtures?|lamps?|tubes?)|"
    r"hid\s+(?:lighting|fixtures?|lamps?)|"
    r"incandescent\s+(?:lighting|fixtures?|lamps?|bulbs?)|"
    r"interior\s+(?:lighting|light\s+fixtures?)|"
    r"wall[\s\-]mounted\s+(?:lighting|fixtures?|sconces?)|"
    r"recessed\s+(?:lighting|fixtures?|downlights?|troffers?)|"
    r"suspended\s+(?:lighting|fixtures?)|"
    r"pendant\s+(?:lighting|fixtures?)|"
    r"type\s+[A-Z][A-Z0-9\-]*\s+(?:fixture|light|luminaire|lighting)"
    r")\b(?:[\s,:\-].*?)?\s*$",
    re.IGNORECASE,
)

# Pull the fixture tag out of the synthesised row's description,
# which the T2.7 synthesiser shapes as ``"Fixture <TAG> — <body>"``
# for every row.  The mark capture matches the same tag shape the
# extractor accepts (single letter, letter+digit, optionally
# hyphenated).
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^fixture\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_lighting_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted lighting aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved for every surviving
    row.  When no synthesised lighting fixture exists anywhere on the
    project, the input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2/T2.5/T3/T4 + finish/panel
            syntheses, and the T2.7 lighting-synthesis appends.

    Returns:
        The same list minus LLM lighting rows that the deterministic
        synthesis renders redundant.  Door / window / finish / panel
        rows are NEVER touched (CSI prefix discriminator: ``26 51`` /
        ``26 55`` is mutually exclusive with the ``08 ...`` /
        ``09 ...`` / ``26 24`` / ``26 28`` / ``26 05`` prefixes the
        upstream dedupes use).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_LIGHTING,
        section_prefixes=_LIGHTING_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="lighting",
        match_family_by_description=True,
    )
