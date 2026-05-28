"""Phase T2.10 — retire LLM-extracted lab-casework aggregates when synthesis exists.

The lab-casework-schedule pre-pass
(:mod:`core.extraction.lab_casework_schedule`) + T2.10 synthesis
(:mod:`core.extraction.takeoff_synthesis.synthesize_lab_takeoff_items`)
emit 1-3 ``TakeoffItem`` families per ``LabCaseworkRecord``: the
primary item EA itself (BASE/WALL/TALL cabinets + LAB_BENCH →
``12 35 53.13``, FUME_HOOD → ``11 53 13``, SAFETY_CABINET →
``11 53 43``, EYEWASH_STATION → ``22 45 19`` cross-Division,
OTHER → ``12 35 53``), a parametric MEP rough-in line (``22 11 16``
piped / ``26 27 26`` electric-only), and optionally a trim line
when both mfr+model are populated AND the item is not a fume hood
(integrated trim) or eyewash (the station IS the trim).

This module is a thin wrapper over
:func:`core.extraction.dedupe.dedupe_against_synthesis`.  It
supplies the lab-specific discriminators:

* CSI prefixes restricted to ``11 53`` (Lab Equipment) + ``12 35``
  (Lab Casework).  The eyewash route to ``22 45 19`` is
  **intentionally excluded** from this dedupe — eyewashes are
  plumbing scope and may collide with the plumbing dedupe upstream
  (which owns Division 22).  The synthesised eyewash row is
  preserved by the source-tag check; the lab dedupe just doesn't
  hunt for OTHER LLM rows under plumbing's authority.
* Legacy aggregate descriptions: ``Lab Casework``, ``Laboratory
  Casework``, ``Laboratory Furniture``, ``Lab Furniture``,
  ``Fume Hood``, ``Fume Hoods``, ``Laboratory Fume Hoods``,
  ``Safety Cabinets``, ``Eyewash Station``, ``Laboratory
  Equipment``, plus per-mark forms ``BC-<n>`` / ``WC-<n>`` /
  ``TC-<n>`` / ``FH-<n>`` / ``LB-<n>`` / ``SC-<n>`` / ``EW-<n>``.
  Description-match enabled (``match_family_by_description=True``).
* Mark pattern: ``Lab casework <TAG>`` matches the synthesised
  description shape.

**Conservative regex breadth** — guarded against:

* **General Division 6 millwork** — the words ``millwork`` and
  ``casework`` are sometimes used loosely on architectural / Div 6
  schedules.  The regex requires the explicit ``lab`` /
  ``laboratory`` prefix on every casework-related alternative,
  so a Div 6 millwork row like ``"Custom millwork: 1500 SF"``
  doesn't fire the dedupe.  ``casework schedule`` and ``casework
  unit`` alone are NOT in the alternation.
* **WC- collision with plumbing** — ``WC-1`` is BOTH a wall-cabinet
  tag in lab schedules AND a water-closet tag in plumbing schedules.
  The per-mark form ``wc-\\d+`` would catch BOTH classes.  Worker
  DD's plumbing bug pattern.  Mitigation: the synthesised wall
  cabinet row is described as ``"Lab casework WC-1 — ..."`` (note
  the ``"Lab casework "`` prefix); a plumbing WC-1 row is
  described as ``"Plumbing fixture WC-1 — ..."`` and lives at
  ``22 41 13``.  The CSI prefix scope (``12 35`` + ``11 53``) plus
  the description-mark anchor on ``"Lab casework "`` keep the two
  dedupe scopes disjoint.  Still, to belt-and-brace this, the
  per-mark ``wc-\\d+`` form is INTENTIONALLY EXCLUDED from the
  legacy-aggregate regex below — we rely on the description-mark
  fallback ONLY for wall cabinets, not on a bare ``WC-N`` token.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_LAB
from core.schemas import TakeoffItem

__all__ = ["dedupe_lab_against_synthesis"]


# Lab CSI section prefixes.  ``12 35`` catches the Division 12
# casework family; ``11 53`` catches the Division 11 laboratory
# equipment family (fume hoods + safety cabinets).  The eyewash
# CSI ``22 45 19`` is intentionally OUTSIDE this scope — it
# crosses into plumbing territory and is owned by the plumbing
# dedupe upstream (which has its own ``22 ...`` prefix scope).
_LAB_SECTION_PREFIXES: tuple[str, ...] = ("12 35", "11 53")


# Legacy per-discipline lab-casework aggregate descriptions.
# Every alternative either requires the explicit ``lab`` /
# ``laboratory`` schedule-section prefix OR a per-mark tag form
# with an explicit digit suffix.  Bare ``casework`` / ``millwork``
# tokens are intentionally NOT in the alternation — those would
# misfire on Division 6 millwork rows.  Bare ``wc-\d+`` is also
# excluded (collides with plumbing water-closet tags); wall cabinet
# coverage relies on the description-mark fallback.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    # Schedule-section aggregates — every alternative anchors on
    # ``lab`` or ``laboratory`` so generic Div 6 millwork rows
    # don't fire.
    r"lab(?:oratory)?\s+casework(?:\s+(?:installation|package|allowance))?|"
    r"lab(?:oratory)?\s+furniture(?:\s+(?:installation|package))?|"
    r"lab(?:oratory)?\s+equipment(?:\s+(?:installation|package))?|"
    r"lab(?:oratory)?\s+benches?|"
    r"lab(?:oratory)?\s+(?:wall|base|tall)\s+cabinets?|"
    r"lab(?:oratory)?\s+fume\s+hoods?|"
    r"fume\s+hoods?(?:\s+(?:installation|package))?|"
    r"biosafety\s+cabinets?|"
    r"safety\s+cabinets?|"
    r"flammable\s+storage\s+cabinets?|"
    r"eyewash(?:\s+stations?)?|"
    r"eye\s+wash(?:\s+stations?)?|"
    r"emergency\s+shower(?:s)?|"
    r"drench\s+(?:shower|station)s?|"
    # Per-mark forms.  ``WC-\d+`` excluded — collides with plumbing
    # water-closet tags.  Wall-cabinet coverage relies on the
    # description-mark fallback via the ``"Lab casework WC-N"``
    # anchor in :data:`_DESC_MARK_RE`.
    r"bc-\d+(?:[\s,:\-].*?)?|"
    r"bcab-\d+(?:[\s,:\-].*?)?|"
    r"tc-\d+(?:[\s,:\-].*?)?|"
    r"tcab-\d+(?:[\s,:\-].*?)?|"
    r"wcab-\d+(?:[\s,:\-].*?)?|"
    r"fh-\d+(?:[\s,:\-].*?)?|"
    r"lb-\d+(?:[\s,:\-].*?)?|"
    r"sc-\d+(?:[\s,:\-].*?)?|"
    r"ew-\d+(?:[\s,:\-].*?)?"
    r")\s*$",
    re.IGNORECASE,
)


# Pull the casework tag out of the synthesised row's description,
# which the T2.10 synthesiser shapes as
# ``"Lab casework <TAG> — <body>"``.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^lab\s+casework\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_lab_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted lab aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved.  When no
    synthesised lab casework exists anywhere on the project, the
    input is returned unchanged (safety rule).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list,
            after every T1-T2.9 synthesis pass and the T2.10 lab
            synthesis append.

    Returns:
        The same list minus LLM lab rows that the deterministic
        synthesis renders redundant.  Door / window / finish /
        panel / lighting / HVAC / plumbing / kitchen rows are NEVER
        touched — CSI prefix discriminator ``12 35`` + ``11 53`` is
        mutually exclusive with every upstream family's prefix.
        Generic Div 6 millwork rows are NEVER touched (the
        legacy-aggregate regex requires explicit ``lab`` /
        ``laboratory`` qualification).
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_LAB,
        section_prefixes=_LAB_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="lab",
        match_family_by_description=True,
    )
