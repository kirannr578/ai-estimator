"""Phase T2.11 — retire LLM-extracted AV aggregates when synthesis exists.

The AV-equipment-schedule pre-pass
(:mod:`core.extraction.av_schedule`) + T2.11 synthesis
(:mod:`core.extraction.takeoff_synthesis.synthesize_av_takeoff_items`)
emit 1-3 ``TakeoffItem`` families per ``AVDeviceRecord``: the
device EA itself (CSI per type — DISPLAY → ``27 41 16.51``,
PROJECTOR → ``27 41 16.31``, CAMERA → ``27 41 16.49``,
MICROPHONE → ``27 41 33.13``, SPEAKER → ``27 41 33.16``, RACK →
``27 11 26``, CONTROL_PROCESSOR → ``27 41 19.13``, NETWORK_SWITCH
→ ``27 21 33``, OTHER → ``27 41 16``), a low-voltage cabling
rough-in line at ``27 15 13.13``, and optionally a programming /
commissioning labor line at the same device CSI section.

This module is a thin wrapper over the Phase T3.5 generic
scaffold :func:`core.extraction.dedupe.dedupe_against_synthesis`.
It supplies the AV-specific discriminators:

* CSI prefix restricted to ``27`` (Division 27 — Communications).
  Mutually exclusive with every prior dedupe family's prefixes
  (08 / 09 / 03 / 11 / 12 / 22 / 23 / 26).
* Legacy aggregate descriptions: ``AV Equipment``, ``Audio Visual
  Equipment``, ``A/V Equipment``, ``Video Conferencing System``,
  ``Display Package``, ``AV Rack``, plus per-mark forms
  (``DISP-<n>`` / ``PROJ-<n>`` / ``MIC-<n>`` / ``SPK-<n>`` /
  ``RACK-<n>`` / ``CTRL-<n>`` / ``SW-<n>``).  Description-match
  enabled (``match_family_by_description=True``).
* Mark pattern: ``AV device <TAG>`` matches the synthesised
  description shape so per-mark dedupe catches LLM rows like
  ``"DISP-1 65\" display installation"``.

**Conservative regex breadth — CAM- cross-domain guard.**

The dangerous shared prefix is ``CAM-N``: BOTH AV schedules
(conference cameras / lecture capture) and security schedules
(surveillance / CCTV) use it.  A naive ``cam-\\d+`` alternative
would catch ANY camera row from either domain and double-fire
with the security dedupe.  Mitigation:

* The bare ``cam-\\d+`` form is **INTENTIONALLY EXCLUDED** from
  the legacy-aggregate regex.  CAM- coverage relies on the
  description-mark fallback (``"AV device CAM-N — ..."``) so a
  Security ``CAM-1`` row described as ``"Security device CAM-1 —
  ..."`` survives intact.
* The CSI prefix discriminator (``27`` only) also keeps Security
  rows (CSI ``28 ...``) outside the AV dedupe scope.

**Conservative regex breadth — door / panel / lighting /
plumbing / kitchen / lab guards.**

Every alternative requires EITHER:

* The schedule section prefix (``av``, ``a/v``, ``audio[-\\s]?
  (visual|video)``, ``video conferencing``, ``display``), OR
* A tag pattern with explicit digit suffix from the AV families
  (``DISP-\\d+`` / ``DSP-\\d+`` / ``PROJ-\\d+`` / ``PJ-\\d+`` /
  ``MIC-\\d+`` / ``SPK-\\d+`` / ``SP-\\d+`` / ``RACK-\\d+`` /
  ``EQR-\\d+`` / ``CTRL-\\d+``, NOT bare ``SW-\\d+`` which would
  collide with electrical switchgear, NOT bare ``CAM-\\d+`` which
  would collide with security cameras).
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_AV
from core.schemas import TakeoffItem

__all__ = ["dedupe_av_against_synthesis"]


# AV CSI section prefix.  ``27`` catches every Division 27
# Communications subsection (``27 11`` racks, ``27 15`` cabling,
# ``27 21`` network equipment, ``27 41`` integrated AV systems).
# Mutually exclusive with every prior dedupe family's prefix.
_AV_SECTION_PREFIXES: tuple[str, ...] = ("27",)


# Legacy per-discipline AV aggregate descriptions.  Every
# alternative requires EITHER an unambiguous AV phrase OR a
# per-mark tag form with an explicit digit suffix from the AV
# families.  Bare ``cam-\d+`` and bare ``sw-\d+`` are
# INTENTIONALLY EXCLUDED — CAM- collides with security cameras,
# SW- collides with electrical switchgear.  Per-mark CAM coverage
# relies on the description-mark fallback via the ``"AV device "``
# anchor in :data:`_DESC_MARK_RE`.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    # Schedule-section aggregates.  Each alternative anchors on
    # an unambiguously AV phrase.
    r"av\s+equipment(?:\s+(?:installation|package|allowance))?|"
    r"a/?v\s+equipment(?:\s+(?:installation|package))?|"
    r"audio[-\s]?(?:visual|video)\s+equipment"
        r"(?:\s+(?:installation|package))?|"
    r"audio[-\s]?(?:visual|video)\s+system(?:s)?|"
    r"av/?it\s+(?:equipment|system|package)|"
    r"video\s+conferencing(?:\s+(?:system|equipment|package))?|"
    r"video\s+conference\s+(?:system|equipment|package)|"
    r"lecture\s+capture(?:\s+system)?|"
    r"display\s+(?:package|installation|equipment)|"
    r"projector(?:s)?(?:\s+(?:installation|package))?|"
    r"av\s+rack(?:s)?(?:\s+(?:installation|package))?|"
    r"equipment\s+rack(?:s)?\s+(?:av|a/v|audio)|"
    r"network\s+switch(?:es)?\s+(?:av|a/v|audio)|"
    # Per-mark forms — every alternative requires an explicit
    # digit suffix.  CAM- and bare SW- excluded (see module
    # docstring).
    r"disp-\d+(?:[\s,:\-].*?)?|"
    r"dsp-\d+(?:[\s,:\-].*?)?|"
    r"proj-\d+(?:[\s,:\-].*?)?|"
    r"pj-\d+(?:[\s,:\-].*?)?|"
    r"mic-\d+(?:[\s,:\-].*?)?|"
    r"spk-\d+(?:[\s,:\-].*?)?|"
    r"sp-\d+(?:[\s,:\-].*?)?|"
    r"rack-\d+(?:[\s,:\-].*?)?|"
    r"eqr-\d+(?:[\s,:\-].*?)?|"
    r"ctrl-\d+(?:[\s,:\-].*?)?"
    r")\s*$",
    re.IGNORECASE,
)


# Pull the device tag out of the synthesised row's description,
# which the T2.11 synthesiser shapes as
# ``"AV device <TAG> — <body>"``.  This handles the CAM- per-mark
# coverage via the explicit ``"AV device "`` anchor — a security
# ``CAM-1`` row described as ``"Security device CAM-1 — ..."``
# does NOT match because the anchor differs.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^av\s+device\s+([A-Z][A-Z0-9.\-]*)\s+(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_av_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted AV aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved.  When no
    synthesised AV device exists anywhere on the project, the
    input is returned unchanged (safety rule, mirrors every prior
    T2.x dedupe).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list,
            after every T1-T2.10 synthesis pass and the T2.11 AV
            synthesis append.

    Returns:
        The same list minus LLM AV rows that the deterministic
        synthesis renders redundant.  Door / window / finish /
        panel / lighting / HVAC / plumbing / kitchen / lab /
        Security rows are NEVER touched — CSI prefix
        discriminator ``27`` is mutually exclusive with every
        other family's prefix.  Bare ``CAM-N`` LLM rows are NEVER
        touched (the per-mark form excludes ``cam-\\d+``); they
        survive intact for the Security dedupe to claim if
        applicable.
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_AV,
        section_prefixes=_AV_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="av",
        match_family_by_description=True,
    )
