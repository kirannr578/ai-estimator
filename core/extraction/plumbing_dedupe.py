"""Phase T2.9 — retire LLM-extracted plumbing aggregates when synthesis exists.

The plumbing-fixture-schedule pre-pass
(:mod:`core.extraction.plumbing_schedule`) + T2.9 synthesis
(:mod:`core.extraction.takeoff_synthesis`) emit 2-3 ``TakeoffItem``
families per ``PlumbingFixtureRecord``: the fixture itself (CSI per
type — WC → ``22 41 13``, LAV → ``22 41 16``, EWC → ``22 47 13``,
FD → ``22 13 19``, ...), a parametric MEP rough-in line (``22 11 16``
for water-supply-dominant fixtures or ``22 13 16`` for waste-dominant),
and optionally a trim / installation-hardware line at 0.70 (mfr+model
gate).  Meanwhile the legacy ``core.takeoff._derive_takeoffs`` keeps
emitting per-discipline aggregate LLM rows under section ``22 40 00``
whenever an ``MEPItem`` mentioning ``"toilet"`` / ``"water closet"`` /
``"lavatory"`` / ``"sink"`` / ``"urinal"`` lands in the project model.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis` (mirroring
:mod:`core.extraction.panel_dedupe` /
:mod:`core.extraction.lighting_dedupe` /
:mod:`core.extraction.hvac_dedupe`).  It supplies the plumbing-
specific discriminators:

* CSI prefixes restricted to ``22 XX`` — the Division 22 family
  spans every plumbing fixture section (``22 11`` rough-in,
  ``22 13`` waste piping + floor drains, ``22 33`` water heaters,
  ``22 41`` fixtures, ``22 47`` water coolers).  Division 23 HVAC
  + Division 26 electrical rows are INTENTIONALLY exempt — those
  are owned by the HVAC + panel + lighting dedupes upstream.
* Legacy aggregate descriptions: ``Plumbing Fixtures``,
  ``Toilets``, ``Water Closets``, ``Lavatories``, ``Urinals``,
  ``Showers``, ``Floor Drains``, ``Sinks``, ``Drinking
  Fountains``, ``Water Coolers``, ``Mop Sinks``, ``Hose Bibbs``,
  and the ``: N EA`` trailing-count form.  Description-match
  enabled (``match_family_by_description=True``) because LLM
  plumbing rows often land with a generic ``"22"`` division and
  an empty ``csi_section``.
* Mark pattern: ``Plumbing fixture <TAG>`` matches the synthesised
  description shape and the typical LLM ``"WC-1 toilet
  installation"`` shape so per-mark dedupe catches both.

See :mod:`core.extraction.dedupe` for the full rule set.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_PLUMBING
from core.schemas import TakeoffItem

__all__ = ["dedupe_plumbing_against_synthesis"]


# Plumbing CSI section prefix.  ``22`` catches every Division 22
# row (fixtures + rough-in + drains + water heaters).  HVAC
# (``23 ...``) and electrical (``26 ...``) rows are intentionally
# outside the dedupe scope — they're owned by hvac_dedupe and
# panel/lighting_dedupe respectively.
_PLUMBING_SECTION_PREFIXES: tuple[str, ...] = ("22",)


# Legacy per-discipline plumbing aggregate descriptions.  Covers the
# common LLM rollup shapes plus the bare ``Plumbing Fixtures`` /
# ``Toilets`` / ``Water Closets`` / ``Lavatories`` / ... forms the
# legacy ``_derive_takeoffs`` MEP path emits when a plumbing mention
# lands in the project model.  Pattern shape mirrors
# :mod:`hvac_dedupe._LEGACY_AGGREGATE_RE` — anchored on common
# prefixes with an optional ``[ ,:\-]`` tail to accept the
# ``"WC-1 installation"`` / ``"Plumbing Fixtures: 12 EA"`` /
# ``"Water closets"`` shapes.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    # Bare "Plumbing" / "Plumbing Fixtures" / "Plumbing System" /
    # "Plumbing Equipment" — the dominant generic-aggregate shape.
    r"plumbing(?:\s+(?:fixtures?|systems?|equipment))?|"
    # Plumbing-specific fixture-package aggregate forms. The bare
    # ``fixtures?`` shape is INTENTIONALLY excluded — it would
    # match lighting-synthesis "Fixture A1 — ..." descriptions
    # (Division 26 lighting) and other Division-08 / 11 / 12
    # "Fixture" rows that aren't plumbing.  Require the word
    # ``plumbing`` to disambiguate.
    r"plumbing\s+fixtures?(?:\s+(?:and\s+trim|package))?|"
    r"toilets?|"
    r"water\s+closets?|"
    r"wc(?:[\s\-]\d+)?(?:\s+(?:installation|fixture|toilet))?|"
    r"lavator(?:y|ies)|"
    r"lav(?:[\s\-][a-z0-9]+)?(?:\s+(?:installation|fixture|sink))?|"
    r"urinals?|"
    r"urn(?:[\s\-]\d+)?(?:\s+(?:installation|fixture))?|"
    r"showers?|"
    r"shower\s+(?:units?|assemblies|stalls?)|"
    r"sinks?(?:\s+(?:kitchen|laundry|utility))?|"
    r"kitchen\s+sinks?|"
    r"mop\s+sinks?|"
    r"service\s+sinks?|"
    r"drinking\s+fountains?|"
    r"water\s+coolers?|"
    r"electric\s+water\s+coolers?|"
    r"ewc(?:[\s\-]\d+)?(?:\s+(?:installation|fixture|cooler))?|"
    r"water\s+heaters?(?:\s+(?:electric|gas|tankless))?|"
    r"hose\s+bibbs?|"
    r"hose\s+hydrants?|"
    r"floor\s+drains?|"
    r"domestic\s+water\s+(?:piping|system|distribution)|"
    r"sanitary\s+(?:waste|drainage)|"
    r"waste\s+(?:and|&)\s+vent"
    r")\b(?:[\s,:\-].*?)?\s*$",
    re.IGNORECASE,
)

# Pull the fixture tag out of the synthesised row's description,
# which the T2.9 synthesiser shapes as
# ``"Plumbing fixture <TAG> — <body>"`` for every row.  The mark
# capture matches the same tag shape the extractor accepts (letter
# prefix + digits / letters, optionally hyphenated).
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^plumbing\s+fixture\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_plumbing_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted plumbing aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved for every surviving
    row.  When no synthesised plumbing fixture exists anywhere on the
    project, the input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list, after
            ``_merge_takeoffs``, the T2/T2.5/T3/T4 + finish/panel/
            lighting/HVAC syntheses, and the T2.9 plumbing-synthesis
            appends.

    Returns:
        The same list minus LLM plumbing rows that the deterministic
        synthesis renders redundant.  Door / window / finish / panel
        / lighting / HVAC rows are NEVER touched (CSI prefix
        discriminator: ``22 ...`` is mutually exclusive with the
        ``08 ...`` / ``09 ...`` / ``26 24`` / ``26 28`` / ``26 51``
        / ``26 55`` / ``23 ...`` prefixes the upstream dedupes use).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_PLUMBING,
        section_prefixes=_PLUMBING_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="plumbing",
        match_family_by_description=True,
    )
