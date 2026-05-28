"""Phase T5 — back-fill ``TakeoffItem.quantity`` for finish rows using room geometry.

The Phase T4 finish synthesis (:mod:`core.extraction.takeoff_synthesis`)
emits one ``TakeoffItem`` per finished surface per room, but every row
carries ``quantity=0.0`` because the finish schedule itself doesn't
publish the geometry (area, perimeter, ceiling height) needed to
compute square-footage. The Phase T5 room-schedule extractor
(:mod:`core.extraction.room_schedule`) DOES carry that geometry. This
module joins the two by ``room_number`` and replaces every finish
row's ``quantity=0.0`` with the right SF, derived per-surface:

* ``floor``           → ``area_sf``
* ``base``            → ``perimeter_lf`` (or ``4 * sqrt(area_sf)``
                         fallback with reduced confidence)
* ``wall_ALL``        → ``perimeter_lf × ceiling_height_ft`` (full
                         four-sided wall area; collapsed when the
                         schedule used a single WALL column)
* ``wall_<N|S|E|W>``  → ``perimeter_lf × ceiling_height_ft / 4``
                         (one wall = 1/4 of total)
* ``ceiling``         → ``area_sf``

For ``wall_*`` quantities, opening deductions (doors + windows) are
documented as a T5 stretch goal — the function accepts the door /
window schedules as parameters so a future revision can subtract per
door (~21 SF) and per window (parsed dimensions) without breaking the
signature. The current implementation leaves a note (``openings not
deducted``) and ships the gross wall area; the T5.1 follow-up will
land the deduction.

Pure function: input items are never mutated; output is a new list of
``TakeoffItem`` instances with refreshed ``quantity``, ``confidence``,
and ``notes``. Non-finish items pass through unchanged. Finish items
whose room# isn't in the schedule pass through with ``quantity=0.0``
preserved and a ``backfill_skipped`` note appended for the auditor.
"""

from __future__ import annotations

import logging
import math
import re
from typing import Any

from core.extraction.takeoff_synthesis import SYNTHESIS_SOURCE_TAG_FINISH
from core.schemas import (
    DoorScheduleResult,
    FinishScheduleResult,
    RoomRecord,
    RoomScheduleResult,
    TakeoffItem,
    WindowScheduleResult,
)

logger = logging.getLogger(__name__)

__all__ = [
    "BACKFILL_NOTE_OK",
    "BACKFILL_NOTE_SKIP_ROOM",
    "BACKFILL_NOTE_FALLBACK_PERIM",
    "BACKFILL_NOTE_NO_HEIGHT",
    "BACKFILL_NOTE_NO_OPENINGS",
    "backfill_finish_quantities",
]


# Notes appended after the original synthesis notes (joined with "; ").
BACKFILL_NOTE_OK: str = "backfill=ok"
BACKFILL_NOTE_SKIP_ROOM: str = "backfill skipped: room not in schedule"
BACKFILL_NOTE_FALLBACK_PERIM: str = "perimeter approximated from area (sqrt fallback)"
BACKFILL_NOTE_NO_HEIGHT: str = "ceiling height missing — wall back-fill skipped"
BACKFILL_NOTE_NO_OPENINGS: str = "openings not deducted (T5.1 stretch)"

# Confidence applied when the back-fill computes from real area + height
# (i.e. the operator can defend every term in the formula). Carries the
# 0.92 ceiling so the row stays in the same band as the synthesis output.
_BACKFILL_CONF_FULL: float = 0.92
# Confidence applied when the back-fill falls back to the square-room
# perimeter approximation. The 0.65 band signals "trustworthy enough to
# show but flag for human review" per the Phase T6 binning rubric.
_BACKFILL_CONF_FALLBACK: float = 0.65


# Notes are formatted as ``key=value; key=value; ...`` by
# :mod:`core.extraction.takeoff_synthesis`. ``room`` is the room number
# (``"101"``, ``"M101"``); ``surface`` is one of ``floor``, ``base``,
# ``wall_ALL``, ``wall_N``, ``wall_S``, ``wall_E``, ``wall_W``,
# ``ceiling``.
_NOTES_ROOM_RE: re.Pattern[str] = re.compile(r"(?:^|;\s*)room=([^;]+)")
_NOTES_SURFACE_RE: re.Pattern[str] = re.compile(r"(?:^|;\s*)surface=([^;]+)")


def _parse_room(item: TakeoffItem) -> str | None:
    notes = item.notes or ""
    m = _NOTES_ROOM_RE.search(notes)
    if not m:
        return None
    val = m.group(1).strip()
    return val or None


def _parse_surface(item: TakeoffItem) -> str | None:
    notes = item.notes or ""
    m = _NOTES_SURFACE_RE.search(notes)
    if not m:
        return None
    val = m.group(1).strip()
    return val or None


def _is_finish_synthesis(item: TakeoffItem) -> bool:
    return (item.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_FINISH}")


def _build_room_map(room_schedule: RoomScheduleResult | None) -> dict[str, RoomRecord]:
    """Build a ``room_number → RoomRecord`` lookup.

    On duplicate keys, the record with the most populated fields wins;
    ties keep the first-seen so output is deterministic.
    """
    if room_schedule is None or not room_schedule.rooms:
        return {}
    out: dict[str, RoomRecord] = {}
    for r in room_schedule.rooms:
        key = (r.room_number or "").strip()
        if not key:
            continue
        existing = out.get(key)
        if existing is None or _score(r) > _score(existing):
            out[key] = r
    return out


def _score(record: RoomRecord) -> int:
    """How many useful fields does this RoomRecord carry?"""
    return sum(
        1 for v in (
            record.room_name,
            record.area_sf,
            record.perimeter_lf,
            record.ceiling_height_ft,
            record.occupancy_type,
        ) if v is not None and v != ""
    )


def _build_finish_ceiling_map(
    finish_schedule: FinishScheduleResult | None,
) -> dict[str, float]:
    """``room_number → ceiling_height_ft`` from the finish schedule.

    Used as a fallback when the room schedule didn't carry the
    ceiling-height column (common in offices that publish two separate
    schedules — geometry on the architectural sheet, finishes-only on
    the schedule sheet).
    """
    if finish_schedule is None or not finish_schedule.rooms:
        return {}
    out: dict[str, float] = {}
    for r in finish_schedule.rooms:
        key = (r.room_number or "").strip()
        if not key or r.ceiling_height_ft is None:
            continue
        # First-seen wins on duplicates.
        out.setdefault(key, r.ceiling_height_ft)
    return out


def _resolve_ceiling_height(
    room: RoomRecord,
    finish_height_map: dict[str, float],
) -> float | None:
    """Pick the best ceiling height: room schedule first, then finish schedule."""
    if room.ceiling_height_ft is not None:
        return room.ceiling_height_ft
    key = (room.room_number or "").strip()
    return finish_height_map.get(key)


def _append_note(existing: str | None, *additions: str) -> str:
    """Join notes with ``"; "``; skip empties; preserve original ordering."""
    bits: list[str] = []
    if existing:
        bits.append(existing)
    for a in additions:
        if a:
            bits.append(a)
    return "; ".join(bits)


def _wall_unit_share(surface: str) -> float | None:
    """Return the fraction of the total wall area attributed to this surface.

    ``wall_ALL`` (single ``WALL`` column on the schedule, or four
    uniform compass codes that the synthesiser collapsed) covers the
    entire perimeter × height: share = 1.0. Each compass direction
    represents one of four walls: share = 0.25.

    Returns ``None`` if the surface is not a wall surface (caller
    treats as "not applicable").
    """
    if surface == "wall_ALL":
        return 1.0
    if surface in {"wall_N", "wall_S", "wall_E", "wall_W"}:
        return 0.25
    return None


def _fallback_perimeter(area_sf: float | None) -> float | None:
    """``4 * sqrt(area_sf)`` square-room perimeter approximation."""
    if area_sf is None or area_sf <= 0:
        return None
    return round(4.0 * math.sqrt(area_sf), 2)


def _backfilled_item(
    item: TakeoffItem,
    *,
    quantity: float,
    confidence: float,
    extra_notes: list[str],
) -> TakeoffItem:
    """Build a new TakeoffItem with refreshed quantity / confidence / notes.

    Quantity is clamped to non-negative (a future opening-deduction
    pass could in pathological cases over-subtract; ship the floor at
    zero rather than negative SF).
    """
    return item.model_copy(update={
        "quantity": round(max(quantity, 0.0), 2),
        "confidence": round(confidence, 4),
        "notes": _append_note(item.notes, *extra_notes),
    })


def backfill_finish_quantities(
    items: list[TakeoffItem],
    room_schedule: RoomScheduleResult | None,
    *,
    finish_schedule: FinishScheduleResult | None = None,
    door_schedule: DoorScheduleResult | None = None,
    window_schedule: WindowScheduleResult | None = None,
) -> list[TakeoffItem]:
    """Back-fill ``quantity`` on finish-synthesis rows using room geometry.

    Args:
        items: The full ``ProjectModel.takeoffs`` candidate list,
            after Phase T4 synthesis + dedupe. The list is **not**
            mutated; the return is a new list with refreshed rows.
        room_schedule: The Phase T5 room schedule (typically merged
            from multiple sheets via :func:`merge_room_schedules`).
            ``None`` / empty short-circuits to the input list — no
            back-fill possible without room data.
        finish_schedule: Optional fallback source for
            ``ceiling_height_ft`` when the room schedule didn't carry
            the column.
        door_schedule: Optional. Reserved for the T5.1 opening-
            deduction follow-up; currently unused but accepted to keep
            the public signature stable.
        window_schedule: Optional. Reserved for the T5.1 opening-
            deduction follow-up; currently unused.

    Returns:
        A new list where every finish-synthesis row's ``quantity`` and
        ``confidence`` have been updated per the surface-specific
        formula in the module docstring. Non-finish rows pass through
        unchanged. Finish rows whose room# is missing from the room
        schedule pass through with ``quantity=0.0`` preserved and a
        ``backfill_skipped`` note appended for the auditor.
    """
    # Door / window schedules are accepted today for signature stability
    # but only consumed once T5.1 lands. Reference them in a debug log
    # so the parameters are not silently ignored.
    if door_schedule is not None or window_schedule is not None:
        logger.debug(
            "backfill_finish_quantities: door/window schedules provided but "
            "opening deduction not yet implemented (T5.1 stretch goal)."
        )

    if not items:
        return []

    room_map = _build_room_map(room_schedule)
    finish_height_map = _build_finish_ceiling_map(finish_schedule)

    if not room_map:
        # Nothing to join against — return the input unchanged so the
        # synthesis rows stay visible (Phase T6 can still surface them
        # at quantity=0 for human review).
        return list(items)

    out: list[TakeoffItem] = []
    for item in items:
        if not _is_finish_synthesis(item):
            out.append(item)
            continue

        room_num = _parse_room(item)
        surface = _parse_surface(item)
        if not room_num or not surface:
            # Synthesised row without a parseable room or surface tag —
            # defensive; should never happen because the T4 synthesiser
            # always emits both. Pass through unchanged.
            out.append(item)
            continue

        room = room_map.get(room_num.strip())
        if room is None:
            out.append(_backfilled_item(
                item,
                quantity=item.quantity,
                confidence=item.confidence,
                extra_notes=[BACKFILL_NOTE_SKIP_ROOM],
            ))
            continue

        out.append(_compute_backfill(item, surface, room, finish_height_map))

    return out


def _compute_backfill(
    item: TakeoffItem,
    surface: str,
    room: RoomRecord,
    finish_height_map: dict[str, float],
) -> TakeoffItem:
    """Per-surface back-fill computation. Pure dispatch on ``surface``."""
    if surface == "floor" or surface == "ceiling":
        return _backfill_area_surface(item, surface, room)
    if surface == "base":
        return _backfill_base(item, room)
    if surface.startswith("wall"):
        return _backfill_wall(item, surface, room, finish_height_map)
    # Unknown surface — leave as-is with a debug note.
    return _backfilled_item(
        item,
        quantity=item.quantity,
        confidence=item.confidence,
        extra_notes=[f"backfill skipped: unknown surface {surface!r}"],
    )


def _backfill_area_surface(
    item: TakeoffItem,
    surface: str,
    room: RoomRecord,
) -> TakeoffItem:
    """Floor / ceiling share the same area = ``area_sf`` rule."""
    if room.area_sf is None or room.area_sf <= 0:
        return _backfilled_item(
            item,
            quantity=item.quantity,
            confidence=item.confidence,
            extra_notes=[f"backfill skipped: room {room.room_number} has no area"],
        )
    return _backfilled_item(
        item,
        quantity=room.area_sf,
        confidence=_BACKFILL_CONF_FULL,
        extra_notes=[BACKFILL_NOTE_OK],
    )


def _backfill_base(item: TakeoffItem, room: RoomRecord) -> TakeoffItem:
    """Base LF = ``perimeter_lf`` (with ``4 * sqrt(area_sf)`` fallback)."""
    if room.perimeter_lf is not None and room.perimeter_lf > 0:
        # Unit consistency: base finishes are LF, not SF. The synthesis
        # emitted unit=SF; update to LF when we back-fill from real
        # perimeter so the downstream pricing pass picks the right
        # cost-DB row.
        return item.model_copy(update={
            "quantity": round(room.perimeter_lf, 2),
            "unit": "LF",
            "confidence": round(_BACKFILL_CONF_FULL, 4),
            "notes": _append_note(item.notes, BACKFILL_NOTE_OK),
        })
    fallback = _fallback_perimeter(room.area_sf)
    if fallback is None:
        return _backfilled_item(
            item,
            quantity=item.quantity,
            confidence=item.confidence,
            extra_notes=[
                f"backfill skipped: room {room.room_number} has no perimeter or area",
            ],
        )
    return item.model_copy(update={
        "quantity": round(fallback, 2),
        "unit": "LF",
        "confidence": round(_BACKFILL_CONF_FALLBACK, 4),
        "notes": _append_note(item.notes, BACKFILL_NOTE_FALLBACK_PERIM),
    })


def _backfill_wall(
    item: TakeoffItem,
    surface: str,
    room: RoomRecord,
    finish_height_map: dict[str, float],
) -> TakeoffItem:
    """Wall SF = ``perimeter × height × share`` (share=1.0 ALL, 0.25 compass)."""
    share = _wall_unit_share(surface)
    if share is None:
        return _backfilled_item(
            item,
            quantity=item.quantity,
            confidence=item.confidence,
            extra_notes=[f"backfill skipped: unrecognised wall surface {surface!r}"],
        )

    height_ft = _resolve_ceiling_height(room, finish_height_map)
    if height_ft is None or height_ft <= 0:
        return _backfilled_item(
            item,
            quantity=item.quantity,
            confidence=item.confidence,
            extra_notes=[BACKFILL_NOTE_NO_HEIGHT],
        )

    perimeter_lf = room.perimeter_lf
    fallback_used = False
    if perimeter_lf is None or perimeter_lf <= 0:
        perimeter_lf = _fallback_perimeter(room.area_sf)
        fallback_used = True
    if perimeter_lf is None or perimeter_lf <= 0:
        return _backfilled_item(
            item,
            quantity=item.quantity,
            confidence=item.confidence,
            extra_notes=[
                f"backfill skipped: room {room.room_number} has no perimeter or area",
            ],
        )

    quantity = perimeter_lf * height_ft * share
    confidence = _BACKFILL_CONF_FALLBACK if fallback_used else _BACKFILL_CONF_FULL

    extras: list[str] = []
    if fallback_used:
        extras.append(BACKFILL_NOTE_FALLBACK_PERIM)
    extras.append(BACKFILL_NOTE_OK)
    # Opening deduction is the T5.1 stretch goal; flag the row so the
    # operator knows the wall SF is GROSS, not NET-of-openings.
    extras.append(BACKFILL_NOTE_NO_OPENINGS)
    return _backfilled_item(
        item,
        quantity=quantity,
        confidence=confidence,
        extra_notes=extras,
    )


def _unused(*_: Any) -> None:  # pragma: no cover
    """Anchor for the deferred door / window opening-deduction hook."""
