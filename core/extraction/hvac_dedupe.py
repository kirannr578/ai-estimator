"""Phase T2.8 — retire LLM-extracted HVAC aggregates when synthesis exists.

The HVAC equipment-schedule pre-pass
(:mod:`core.extraction.hvac_schedule`) + T2.8 synthesis
(:mod:`core.extraction.takeoff_synthesis`) emit 2-3 ``TakeoffItem``
families per ``HVACEquipmentRecord``: the equipment itself (CSI per
family — ``23 73 13`` AHU / ``23 74 13`` RTU / ``23 36 00`` VAV /
``23 22 23`` PUMP / ``23 52 00`` BOILER / ``23 64 23`` CHILLER /
``23 34 00`` FAN / ``23 00 00`` OTHER), a parametric MEP rough-in
line (``23 05 00``), and optionally a disconnect + flex line
(``26 28 16``) for motorized equipment with a voltage feed.
Meanwhile the legacy ``core.takeoff._derive_takeoffs`` keeps emitting
per-discipline aggregate LLM rows under section ``23 00 00`` whenever
an ``MEPItem`` mentioning ``"rtu"`` / ``"ahu"`` / ``"hvac"`` lands
in the project model.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis` (mirroring
:mod:`core.extraction.panel_dedupe` /
:mod:`core.extraction.lighting_dedupe`).  It supplies the HVAC-
specific discriminators:

* CSI prefixes restricted to ``23 XX`` — the Division 23 family
  spans every HVAC equipment section (``23 36`` VAV, ``23 52``
  boilers, ``23 64`` chillers, ``23 73`` AHU, ``23 74`` RTU,
  ``23 34`` fans, ``23 22`` pumps, plus ``23 05`` rough-in and
  ``23 00`` generic).  The disconnect (``26 28 16``) synthesised
  by T2.8 is INTENTIONALLY exempt — the disconnect is a real
  per-equipment line, and the LLM rarely emits a separate
  disconnect aggregate to dedupe against.
* Legacy aggregate descriptions: ``HVAC``, ``RTU``, ``AHU``,
  ``Mechanical Equipment``, ``Air Handling Unit``, ``Rooftop
  Unit``, ``Variable Air Volume Terminal``, ``Boiler``,
  ``Chiller``, ``Pump``, ``Fan``, and the ``: N EA`` trailing-count
  form. Description-match enabled (``match_family_by_description=
  True``) because LLM HVAC rows often land with a generic ``"23"``
  division and an empty ``csi_section``.
* Mark pattern: ``Equipment <TAG>`` matches the synthesised
  description shape and the typical LLM ``"AHU-1 installation"``
  shape so per-mark dedupe catches both.

See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_HVAC
from core.schemas import TakeoffItem

__all__ = ["dedupe_hvac_against_synthesis"]


# HVAC CSI section prefix.  ``23`` catches every Division 23 row
# (equipment + rough-in).  The disconnect (``26 28 16``) is
# intentionally outside the dedupe scope — see module docstring.
_HVAC_SECTION_PREFIXES: tuple[str, ...] = ("23",)

# Legacy per-discipline HVAC aggregate descriptions.  Covers the
# common LLM rollup shapes plus the bare ``HVAC`` / ``RTU`` / ``AHU``
# / ``Mechanical Equipment`` forms the legacy ``_derive_takeoffs``
# MEP path emits when an HVAC mention lands in the project model.
# Pattern shape mirrors :mod:`panel_dedupe._LEGACY_AGGREGATE_RE` /
# :mod:`lighting_dedupe._LEGACY_AGGREGATE_RE` — anchored on common
# prefixes with an optional ``[ ,:\-]`` tail to accept the
# ``"AHU-1 installation"`` / ``"Mechanical Equipment: 5 EA"`` /
# ``"Air handling units"`` shapes.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    r"hvac(?:\s+(?:equipment|system|unit|units))?|"
    r"mechanical\s+(?:equipment|units?|systems?)|"
    r"rtu(?:\s+\d+)?(?:\s+installation)?|"
    r"ahu(?:\s+\d+)?(?:\s+installation)?|"
    r"vav(?:\s+(?:box|boxes|terminal|terminals))?|"
    r"air\s+handling\s+units?|"
    r"air\s+handlers?|"
    r"rooftop\s+units?|"
    r"packaged\s+(?:rooftop\s+)?units?|"
    r"variable\s+air\s+volume(?:\s+(?:box|boxes|terminal|terminals))?|"
    r"boilers?|"
    r"chillers?|"
    r"(?:hot\s*water|chilled\s*water|condenser\s*water)?\s*pumps?|"
    r"(?:supply|exhaust|return|circulating)?\s*fans?|"
    r"unit\s+heaters?|"
    r"split\s+systems?|"
    r"vrf\s+(?:systems?|units?)|"
    r"ductwork|"
    r"hydronic\s+(?:piping|loop|system)"
    r")\b(?:[\s,:\-].*?)?\s*$",
    re.IGNORECASE,
)

# Pull the equipment tag out of the synthesised row's description,
# which the T2.8 synthesiser shapes as ``"Equipment <TAG> — <body>"``
# for every row.  The mark capture matches the same tag shape the
# extractor accepts (letter prefix + digits, optionally hyphenated).
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^equipment\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_hvac_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted HVAC aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved for every surviving
    row.  When no synthesised HVAC equipment exists anywhere on the
    project, the input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2/T2.5/T3/T4 + finish/panel/
            lighting syntheses, and the T2.8 HVAC-synthesis appends.

    Returns:
        The same list minus LLM HVAC rows that the deterministic
        synthesis renders redundant.  Door / window / finish / panel
        / lighting rows are NEVER touched (CSI prefix discriminator:
        ``23 ...`` is mutually exclusive with the ``08 ...`` /
        ``09 ...`` / ``26 24`` / ``26 28`` / ``26 51`` / ``26 55``
        prefixes the upstream dedupes use).  Plumbing rows
        (``22 ...``) are also untouched.
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_HVAC,
        section_prefixes=_HVAC_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="hvac",
        match_family_by_description=True,
    )
