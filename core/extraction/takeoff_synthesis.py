"""Phase T2 — synthesize :class:`TakeoffItem` rows from a :class:`DoorScheduleResult`.

Pure converter that turns the typed door records produced by the T1
deterministic door-schedule pre-pass (``core.extraction.door_schedule``)
into priced-ready :class:`core.schemas.TakeoffItem` rows. One ``DoorRecord``
becomes one ``TakeoffItem``; the synthesised items are deliberately
**additive** to LLM-extracted takeoffs — cross-source dedupe is Phase T3.

CSI mapping (keyword heuristic, see ``_CSI_MAPPING``):

* Hollow metal  (``HM`` / ``HOLLOW METAL``)              → ``08 11 13``
* Aluminum frame / storefront (``ALUM`` / ``STOREFRONT``) → ``08 11 16``
* Wood / solid-core (``WD`` / ``SCWD`` / ``WOOD``)        → ``08 14 13``
* Glass / glazed (``GLASS`` / ``GLAZED``)                  → ``08 80 00``
* Unknown / unmatched                                      → ``08 10 00``

Confidence rubric (per Phase T2 brief):

* mark **and** type present → ``0.92``
* only one of mark / type   → ``0.80``
* neither                   → ``0.60`` (caller may filter)

Every synthesised row carries ``source=door_schedule_prepass`` at the
start of its ``notes`` field. The schema does not yet expose a dedicated
``source`` column, so the notes prefix is the stable handle a future
T3 dedupe pass can grep for.
"""

from __future__ import annotations

from typing import Final

from core.schemas import DoorRecord, DoorScheduleResult, TakeoffItem

__all__ = ["SYNTHESIS_SOURCE_TAG", "synthesize_door_takeoff_items"]


SYNTHESIS_SOURCE_TAG: Final[str] = "door_schedule_prepass"


# ---------------------------------------------------------------------------
# CSI mapping
# ---------------------------------------------------------------------------
#
# Ordered (specific → generic). The matcher upper-cases the haystack
# (``type + material + frame``) once and tests each keyword as a
# substring. Storefront/aluminum is checked before wood so a frame label
# of ``ALUM`` on a record with ``type='WD'`` still classifies as wood
# (the ``type`` is checked first in the haystack order); see ``_classify``.

# (csi_division, csi_section, family-label-for-description)
_CSI_HM:    Final[tuple[str, str, str]] = ("08", "08 11 13", "Hollow Metal Door")
_CSI_ALUM:  Final[tuple[str, str, str]] = ("08", "08 11 16", "Aluminum Frame")
_CSI_WOOD:  Final[tuple[str, str, str]] = ("08", "08 14 13", "Wood Door")
_CSI_GLASS: Final[tuple[str, str, str]] = ("08", "08 80 00", "Glass Door")
_CSI_GENERIC: Final[tuple[str, str, str]] = ("08", "08 10 00", "Door")

_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # Hollow metal first — ``HM`` is unambiguous in a door schedule.
    (("HOLLOW METAL", "HM"), _CSI_HM),
    # Storefront / aluminum frames before wood so an aluminum frame on
    # a wood door still preferentially classifies via the type token.
    (("STOREFRONT", "ALUMINUM", "ALUM"), _CSI_ALUM),
    # Glass / glazed.
    (("GLASS", "GLAZED"), _CSI_GLASS),
    # Wood (last among specifics). Includes ``SC`` (solid-core) and
    # ``SCWD`` per the brief.
    (("SCWD", "WOOD", "WD", "SC"), _CSI_WOOD),
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _format_inches(in_val: float | None) -> str | None:
    """Render an inches value as a ``3'-0"`` feet-inches string.

    Returns ``None`` when ``in_val`` is ``None`` so callers can choose
    whether to omit the value. Negative values are passed through as-is
    (caller is expected to have validated upstream).
    """
    if in_val is None:
        return None
    feet = int(in_val // 12)
    rem = in_val - feet * 12
    if abs(rem - round(rem)) < 1e-3:
        rem_str = str(int(round(rem)))
    else:
        rem_str = f"{rem:g}"
    return f"{feet}'-{rem_str}\""


def _classify(door: DoorRecord) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one door.

    The type field wins when present; falls back to material / frame
    fields when the type cell was empty (e.g. a schedule that only
    records ``MATL=HOLLOW METAL``).
    """
    parts = [door.type, door.material, door.frame]
    hay = " ".join(p for p in parts if p).upper()
    if not hay:
        return _CSI_GENERIC
    for keywords, mapping in _CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_GENERIC


def _confidence(door: DoorRecord) -> float:
    has_mark = bool(door.mark and door.mark.strip())
    has_type = bool(door.type and door.type.strip())
    if has_mark and has_type:
        return 0.92
    if has_mark or has_type:
        return 0.80
    return 0.60


def _describe(door: DoorRecord, family: str) -> str:
    """Build a human-readable description.

    Examples::

        "Door 101A — HM 3'-0\\" x 7'-0\\""
        "Door 102 — Wood Door"
        "Door (unmarked) — Hollow Metal Door"
    """
    mark = (door.mark or "").strip()
    label = (door.type or "").strip() or family
    head = f"Door {mark}" if mark else "Door (unmarked)"
    width = _format_inches(door.width_in)
    height = _format_inches(door.height_in)
    if width and height:
        return f"{head} — {label} {width} x {height}"
    return f"{head} — {label}"


def _notes_for(door: DoorRecord) -> str:
    """Stable, source-tagged notes string a future T3 dedupe pass can grep.

    Format is ``key=value`` pairs joined by ``"; "``. The first pair is
    always ``source=door_schedule_prepass`` so the prefix-match is cheap.
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG}"]
    if door.mark:
        bits.append(f"mark={door.mark}")
    if door.type:
        bits.append(f"type={door.type}")
    width_s = _format_inches(door.width_in)
    height_s = _format_inches(door.height_in)
    if width_s and height_s:
        bits.append(f"size={width_s} x {height_s}")
    if door.width_in is not None:
        bits.append(f"width_in={door.width_in:g}")
    if door.height_in is not None:
        bits.append(f"height_in={door.height_in:g}")
    if door.thickness_in is not None:
        bits.append(f"thickness_in={door.thickness_in:g}")
    if door.material:
        bits.append(f"material={door.material}")
    if door.frame:
        bits.append(f"frame={door.frame}")
    if door.hardware_set:
        bits.append(f"hardware_set={door.hardware_set}")
    if door.fire_rating:
        bits.append(f"fire_rating={door.fire_rating}")
    return "; ".join(bits)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize_door_takeoff_items(
    schedule: DoorScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``DoorRecord`` on ``schedule`` into a ``TakeoffItem``.

    Returns ``[]`` when ``schedule`` is ``None`` or has no doors. Each
    emitted item carries ``quantity=1.0``, ``unit="EA"``, a CSI section
    chosen by the keyword heuristic, and a confidence per the rubric in
    the module docstring. ``sheet_id`` (when provided) is stored on
    ``source_sheet_ids`` so downstream consumers can trace each row
    back to the originating sheet.
    """
    if schedule is None or not schedule.doors:
        return []
    sheets: list[str] = [sheet_id] if sheet_id else []
    items: list[TakeoffItem] = []
    for door in schedule.doors:
        division, section, family = _classify(door)
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe(door, family),
            quantity=1.0,
            unit="EA",
            confidence=_confidence(door),
            source_sheet_ids=list(sheets),
            notes=_notes_for(door),
        ))
    return items
