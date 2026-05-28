"""Phase T2.10 — retire LLM-extracted kitchen aggregates when synthesis exists.

The kitchen-equipment-schedule pre-pass
(:mod:`core.extraction.kitchen_schedule`) + T2.10 synthesis
(:mod:`core.extraction.takeoff_synthesis.synthesize_kitchen_takeoff_items`)
emit 1-3 ``TakeoffItem`` families per ``KitchenEquipmentRecord``:
the equipment EA itself (CSI per type — RANGE/GRIDDLE/FRYER/OVEN →
``11 40 13.13``, REFRIGERATOR/FREEZER/WALK_IN/ICE_MACHINE →
``11 40 16.13``, DISHWASHER → ``11 40 19.13``, MIXER/PREP_TABLE/SINK
→ ``11 40 13``, HOOD/EXHAUST_FAN → ``11 40 13.16``, OTHER →
``11 40 00``), a parametric MEP rough-in line (``22 11 16`` water-
side / ``26 27 26`` electric-only / ``23 31 13`` hood ductwork —
dominant-utility rule), and optionally a trim / installation-
hardware line at the same equipment section when both mfr and
model are populated.

This module is a thin wrapper over the Phase T3.5 generic scaffold
:func:`core.extraction.dedupe.dedupe_against_synthesis` (mirroring
:mod:`core.extraction.plumbing_dedupe`).  It supplies the kitchen-
specific discriminators:

* CSI prefixes restricted to ``11 40`` (Division 11 foodservice
  family).  The kitchen rough-in CSIs (``22 11 16`` water,
  ``26 27 26`` electric, ``23 31 13`` ductwork) are **intentionally
  excluded** from the dedupe scope — they're owned by the plumbing
  / panel / HVAC dedupes upstream and dropping them here would
  break those families' invariants.  The synthesised rough-in row
  is preserved by the source-tag check; the dedupe just doesn't
  hunt for OTHER plumbing/panel/HVAC LLM rows under kitchen's
  authority.
* Legacy aggregate descriptions: ``Kitchen Equipment``, ``Food
  Service Equipment``, ``Foodservice Equipment``, ``Commercial
  Kitchen Equipment``, plus the ``K-<n>`` / ``RA-<n>`` / ``FE-<n>``
  / ``REF-<n>`` / ``WI-<n>`` / ``HOOD-<n>`` / ``DISH-<n>`` / ...
  per-mark shapes that the legacy LLM path emits.  Description-
  match enabled (``match_family_by_description=True``) because LLM
  kitchen rows often land with a generic ``"11"`` division and an
  empty ``csi_section``.
* Mark pattern: ``Kitchen equipment <TAG>`` matches the synthesised
  description shape and the typical LLM ``"K-1 range installation"``
  shape so per-mark dedupe catches both.

**Conservative regex breadth** — Worker DD's plumbing bug (where a
bare ``fixtures?`` alternation suppressed lighting rows) is the
cautionary example.  Every regex alternative MUST require either:

* The schedule section prefix (``kitchen equipment``, ``food
  service``, ``foodservice``, ``commercial kitchen``), OR
* A tag pattern with explicit digit suffix (``K-\\d+``, ``FE-\\d+``,
  ``RANGE-\\d+``, ``FRYER-\\d+``, ``REF-\\d+``, ``WI-\\d+``,
  ``IM-\\d+``, ``DW-\\d+``, ``HOOD-\\d+``, ``EF-\\d+``).

Specifically guarded against:

* **Plumbing collision** — a bare ``"sinks?"`` alternative would
  catch every plumbing fixture row mentioning "kitchen sink"
  vs. "lavatory".  The regex requires the schedule-prefix or
  the ``SK-`` tag form, so plumbing fixture rows survive
  intact.
* **HVAC collision** — kitchen hoods are cross-listed under
  ``23 38 13``, but the regex never matches a bare ``"hood"``
  — only ``HOOD-\\d+`` or ``"kitchen hood"`` / ``"exhaust hood"``.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_KITCHEN
from core.schemas import TakeoffItem

__all__ = ["dedupe_kitchen_against_synthesis"]


# Kitchen CSI section prefix.  ``11 40`` catches every Division
# 11 foodservice subsection (``11 40 00`` generic, ``11 40 13``
# cooking / ``11 40 13.13`` / ``11 40 13.16`` hood / ``11 40 16``
# refrigeration / ``11 40 19`` dishwashing).  The kitchen rough-in
# CSIs live under different divisions (22 / 26 / 23) and are
# intentionally outside the dedupe scope — those rows are owned
# by plumbing/panel/HVAC dedupes upstream.
_KITCHEN_SECTION_PREFIXES: tuple[str, ...] = ("11 40",)


# Legacy per-discipline kitchen aggregate descriptions.  Every
# alternative requires EITHER the foodservice/kitchen-equipment
# section prefix OR a per-mark form with an explicit digit suffix
# — never a bare common-word match that might catch a plumbing
# / HVAC / lighting row.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    # Schedule-section aggregates.  Each alternative anchors on a
    # phrase that is unambiguously foodservice / kitchen-equipment.
    r"kitchen\s+equipment(?:\s+(?:installation|package|allowance))?|"
    r"food\s*service\s+equipment(?:\s+(?:installation|package))?|"
    r"foodservice\s+equipment(?:\s+(?:installation|package))?|"
    r"commercial\s+kitchen\s+equipment|"
    r"commercial\s+kitchen\s+(?:hood|hoods|exhaust)|"
    r"kitchen\s+hood(?:s)?|"
    r"exhaust\s+hood(?:s)?|"
    r"walk[-\s]?in\s+(?:cooler|freezer|refrigerat(?:or|ion))s?(?:\s+(?:installation|unit|package))?|"
    r"refrigerated\s+(?:equipment|cases?)|"
    r"ice\s+machine(?:s)?(?:\s+(?:installation|unit|package))?|"
    # Per-mark forms — every alternative requires an explicit
    # digit suffix on the tag prefix so a stray ``"K"`` / ``"FE"``
    # token can't fire.  The optional descriptive tail accepts
    # the LLM's common ``"installation"`` / ``"unit"`` / ``"package"``
    # suffixes.
    r"k-\d+(?:[\s,:\-].*?)?|"
    r"fe-\d+(?:[\s,:\-].*?)?|"
    r"range-\d+(?:[\s,:\-].*?)?|"
    r"fryer-\d+(?:[\s,:\-].*?)?|"
    r"ra-\d+(?:[\s,:\-].*?)?|"
    r"fry-\d+(?:[\s,:\-].*?)?|"
    r"ov-\d+(?:[\s,:\-].*?)?|"
    r"ref-\d+(?:[\s,:\-].*?)?|"
    r"rf-\d+(?:[\s,:\-].*?)?|"
    r"fz-\d+(?:[\s,:\-].*?)?|"
    r"frz-\d+(?:[\s,:\-].*?)?|"
    r"wi-\d+(?:[\s,:\-].*?)?|"
    r"wic-\d+(?:[\s,:\-].*?)?|"
    r"wif-\d+(?:[\s,:\-].*?)?|"
    r"im-\d+(?:[\s,:\-].*?)?|"
    r"dw-\d+(?:[\s,:\-].*?)?|"
    r"dsh-\d+(?:[\s,:\-].*?)?|"
    r"hood-\d+(?:[\s,:\-].*?)?|"
    r"hd-\d+(?:[\s,:\-].*?)?|"
    r"eh-\d+(?:[\s,:\-].*?)?|"
    r"ef-\d+(?:[\s,:\-].*?)?|"
    r"mix-\d+(?:[\s,:\-].*?)?|"
    r"mx-\d+(?:[\s,:\-].*?)?|"
    r"prep-\d+(?:[\s,:\-].*?)?|"
    r"pt-\d+(?:[\s,:\-].*?)?"
    r")\s*$",
    re.IGNORECASE,
)


# Pull the equipment tag out of the synthesised row's description,
# which the T2.10 synthesiser shapes as
# ``"Kitchen equipment <TAG> — <body>"``.  The mark capture matches
# the tag shape the extractor accepts (letter prefix + digits /
# letters, optionally hyphenated).
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^kitchen\s+equipment\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_kitchen_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted kitchen aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved for every
    surviving row.  When no synthesised kitchen equipment exists
    anywhere on the project, the input is returned unchanged
    (safety rule, mirrors plumbing / HVAC dedupes).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list,
            after ``_merge_takeoffs``, every T2 / T2.5 / T3 / T4 /
            T2.6-T2.9 synthesis pass, and the T2.10 kitchen
            synthesis append.

    Returns:
        The same list minus LLM kitchen rows that the deterministic
        synthesis renders redundant.  Door / window / finish / panel
        / lighting / HVAC / plumbing rows are NEVER touched — CSI
        prefix discriminator ``11 40 ...`` is mutually exclusive
        with every upstream family's prefix.
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_KITCHEN,
        section_prefixes=_KITCHEN_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="kitchen",
        match_family_by_description=True,
    )
