"""Phase T2.11 — retire LLM-extracted security aggregates when synthesis exists.

The security-schedule pre-pass
(:mod:`core.extraction.security_schedule`) + T2.11 synthesis
(:mod:`core.extraction.takeoff_synthesis.synthesize_security_takeoff_items`)
emit 1-3 ``TakeoffItem`` families per ``SecurityDeviceRecord``:
the device EA itself (CSI per type — CARD_READER → ``28 13
23.13``, CAMERA → ``28 23 23``, MOTION_SENSOR → ``28 16 13.13``,
DOOR_CONTACT → ``28 16 16.13``, KEYPAD → ``28 13 23.16``,
REQUEST_TO_EXIT → ``28 13 33.13``, MAGLOCK → ``28 13 43.13``,
OTHER → ``28 13 00``), a low-voltage cabling rough-in line at
``28 05 13``, and optionally a programming / commissioning
labor line at the same device CSI section.

This module is a thin wrapper over the Phase T3.5 generic
scaffold :func:`core.extraction.dedupe.dedupe_against_synthesis`.
It supplies the security-specific discriminators:

* CSI prefix restricted to ``28`` (Division 28 — Electronic
  Safety & Security).  Mutually exclusive with every prior
  dedupe family's prefixes (08 / 09 / 03 / 11 / 12 / 22 / 23 /
  26 / 27).
* Legacy aggregate descriptions: ``Security Equipment``,
  ``Access Control System``, ``Card Reader System``, ``CCTV
  System``, ``Video Surveillance System``, plus per-mark forms
  (``RDR-<n>`` / ``DR-<n>`` / ``MS-<n>`` / ``MOT-<n>`` /
  ``DC-<n>`` / ``KP-<n>`` / ``RTE-<n>`` / ``REX-<n>`` /
  ``ML-<n>`` / ``MAG-<n>``).  Description-match enabled
  (``match_family_by_description=True``).
* Mark pattern: ``Security device <TAG>`` matches the
  synthesised description shape.

**Conservative regex breadth — door hardware (Phase T1) guard.**

The dangerous shared prefix is ``DR-N``: BOTH security schedules
(door card readers) and door schedules (Phase T1, where ``DR``
is sometimes a generic door mark) can use it.  Mitigation:

* The CSI prefix discriminator (``28`` only) keeps door hardware
  rows (CSI ``08 ...``) outside the security dedupe scope.  A
  Phase T1 door row at ``08 71 00`` always survives unchanged.
* The bare ``dr-\\d+`` form is **INTENTIONALLY EXCLUDED** from
  the legacy regex (per the T2.11 brief).  Without an unambiguous
  ``security`` / ``access control`` / ``card reader`` phrase or
  the ``"Security device "`` description anchor, a Phase T1
  ``"DR-1"`` row at any CSI division would otherwise satisfy
  ``match_family_by_description=True`` via the legacy regex and
  be wrongly considered in-family.  Per-mark suppression for
  legitimate security ``DR-N`` rows still works because the
  synthesis writes ``"Security device DR-N — ..."`` and
  :func:`extract_mark_from_synthesized` populates the
  synthesised-marks set from notes, which the scaffold then uses
  for whole-token mark matching against any in-scope LLM row.

**Conservative regex breadth — AV-camera (CAM-) guard.**

* The bare ``cam-\\d+`` form is **INTENTIONALLY EXCLUDED** from
  the legacy-aggregate regex.  CAM- coverage relies on the
  description-mark fallback (``"Security device CAM-N — ..."``)
  so an AV ``CAM-1`` row described as ``"AV device CAM-1 — ..."``
  survives intact for the AV dedupe to claim.

**Conservative regex breadth — every other family guard.**

Every alternative requires EITHER an unambiguous security
phrase OR a per-mark tag form with an explicit digit suffix
from the security families.  Bare ``door\\s+contact`` /
``security\\s+`` / ``access\\s+control\\s+`` / ``cctv\\s+`` /
``surveillance\\s+`` phrases anchor the schedule-section
aggregates so a generic Division 8 ``"Door hardware set"`` row
never fires.
"""

from __future__ import annotations

import re

from core.extraction.dedupe import dedupe_against_synthesis
from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_SECURITY
from core.schemas import TakeoffItem

__all__ = ["dedupe_security_against_synthesis"]


# Security CSI section prefix.  ``28`` catches every Division 28
# Electronic Safety & Security subsection (``28 05`` cabling,
# ``28 13`` access control, ``28 16`` intrusion detection,
# ``28 23`` video surveillance).  Mutually exclusive with every
# prior dedupe family's prefix.
_SECURITY_SECTION_PREFIXES: tuple[str, ...] = ("28",)


# Legacy per-discipline security aggregate descriptions.  Every
# alternative requires EITHER an unambiguous security phrase OR a
# per-mark tag form with an explicit digit suffix.  Bare
# ``cam-\d+`` is INTENTIONALLY EXCLUDED — CAM- collides with AV
# cameras.  Per-mark CAM coverage relies on the description-mark
# fallback via the ``"Security device "`` anchor in
# :data:`_DESC_MARK_RE`.
_LEGACY_AGGREGATE_RE: re.Pattern[str] = re.compile(
    r"^(?:"
    # Schedule-section aggregates.  Each alternative anchors on
    # ``security`` / ``access control`` / ``surveillance`` /
    # ``cctv`` / ``card reader`` so generic Division 8 door
    # hardware rows don't fire.
    r"security\s+(?:equipment|devices?|system)"
        r"(?:\s+(?:installation|package))?|"
    r"access\s+control\s+(?:system|equipment|package|devices?)"
        r"(?:\s+(?:installation|package))?|"
    r"card\s+reader(?:s)?(?:\s+(?:system|equipment|package))?|"
    r"prox(?:imity)?\s+reader(?:s)?|"
    r"cctv\s+(?:system|equipment|package|cameras?)|"
    r"video\s+surveillance(?:\s+(?:system|equipment|package))?|"
    r"surveillance\s+camera(?:s)?(?:\s+(?:installation|package))?|"
    r"motion\s+(?:sensors?|detectors?)"
        r"(?:\s+(?:installation|package))?|"
    r"door\s+contact(?:s)?(?:\s+(?:installation|package))?|"
    r"keypad(?:s)?(?:\s+(?:installation|package))?|"
    r"request[-\s]?to[-\s]?exit(?:\s+(?:device|sensor|button))?|"
    r"electromagnetic\s+lock(?:s)?|"
    r"mag(?:netic)?\s+lock(?:s)?|"
    r"maglock(?:s)?(?:\s+(?:installation|package))?|"
    # Per-mark forms — every alternative requires an explicit
    # digit suffix.  Bare ``cam-\d+`` and bare ``dr-\d+`` are
    # **INTENTIONALLY EXCLUDED** — CAM- collides with AV cameras,
    # DR- collides with Phase T1 door marks.  Per-mark coverage
    # for these falls back to the ``"Security device "`` anchor
    # in :data:`_DESC_MARK_RE` plus the synthesised-marks set
    # populated from notes.
    r"rdr-\d+(?:[\s,:\-].*?)?|"
    r"cr-\d+(?:[\s,:\-].*?)?|"
    r"ms-\d+(?:[\s,:\-].*?)?|"
    r"mot-\d+(?:[\s,:\-].*?)?|"
    r"pir-\d+(?:[\s,:\-].*?)?|"
    r"dc-\d+(?:[\s,:\-].*?)?|"
    r"kp-\d+(?:[\s,:\-].*?)?|"
    r"rte-\d+(?:[\s,:\-].*?)?|"
    r"rex-\d+(?:[\s,:\-].*?)?|"
    r"ml-\d+(?:[\s,:\-].*?)?|"
    r"mag-\d+(?:[\s,:\-].*?)?"
    r")\s*$",
    re.IGNORECASE,
)


# Pull the device tag out of the synthesised row's description,
# which the T2.11 synthesiser shapes as
# ``"Security device <TAG> — <body>"``.  This handles the CAM-
# per-mark coverage via the explicit ``"Security device "``
# anchor — an AV ``CAM-1`` row described as ``"AV device CAM-1 —
# ..."`` does NOT match because the anchor differs.
_DESC_MARK_RE: re.Pattern[str] = re.compile(
    r"^security\s+device\s+([A-Z][A-Z0-9.\-]*)\s+"
    r"(?:[\u2014\u2013\-]|--)\s",
    re.IGNORECASE,
)


def dedupe_security_against_synthesis(
    items: list[TakeoffItem],
) -> list[TakeoffItem]:
    """Trim LLM-extracted security aggregates when synthesis covers them.

    See :mod:`core.extraction.dedupe` for the full rule set.  Pure
    function; original input ordering is preserved.  When no
    synthesised security device exists anywhere on the project,
    the input is returned unchanged (safety rule, mirrors every
    prior T2.x dedupe).

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list,
            after every T1-T2.10 synthesis pass, the T2.11 AV
            synthesis + dedupe, and the T2.11 security synthesis
            append.

    Returns:
        The same list minus LLM security rows that the
        deterministic synthesis renders redundant.  Door / window
        / finish / panel / lighting / HVAC / plumbing / kitchen /
        lab / AV rows are NEVER touched — CSI prefix
        discriminator ``28`` is mutually exclusive with every
        other family's prefix.  Bare ``CAM-N`` LLM rows are NEVER
        touched (the per-mark form excludes ``cam-\\d+``); they
        survive intact for the AV dedupe to claim if applicable.
        Phase T1 door hardware rows (CSI ``08 71 00``) survive
        intact — the dedupe scope is CSI ``28 ...`` only.
    """
    return dedupe_against_synthesis(
        items,
        source_tag=SYNTHESIS_SOURCE_TAG_SECURITY,
        section_prefixes=_SECURITY_SECTION_PREFIXES,
        section_field="csi_section",
        legacy_aggregate_patterns=(_LEGACY_AGGREGATE_RE,),
        mark_pattern=_DESC_MARK_RE,
        family_label="security",
        match_family_by_description=True,
    )
