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

Phase T5.1 ships opening deduction: when a door schedule and / or
window schedule are passed, every opening with a populated
``room_number`` is attributed to that room, and each wall row's
quantity is reduced by ``(total_opening_sf × wall_share)`` — the
proportional share of openings carried by that one wall direction.
Openings without dimensions fall back to standard commercial defaults
(:data:`DOOR_DEFAULT_OPENING_SF` for doors, :data:`WINDOW_DEFAULT_OPENING_SF`
for windows). Openings whose ``room_number`` is missing or doesn't
appear in the room schedule are skipped (logged at debug; not deducted
from any wall). Deductions are capped at the raw wall SF so a wall
never goes negative — the cap firing is recorded in the audit notes.

Wall-direction assignment is intentionally proportional (1/N for an
N-compass-direction room, 1.0 for a single ``WALL`` column collapsed
to ``wall_ALL``). The future T5.2 enhancement, when door / window
schedules carry an explicit ``wall: "N"`` column, can replace the
proportional share with a per-direction lookup without breaking this
module's signature.

Pure function: input items are never mutated; output is a new list of
``TakeoffItem`` instances with refreshed ``quantity``, ``confidence``,
and ``notes``. Non-finish items pass through unchanged. Finish items
whose room# isn't in the schedule pass through with ``quantity=0.0``
preserved and a ``backfill_skipped`` note appended for the auditor.

Phase T6.1 — chain-derivation decay
-----------------------------------

Worker W's T6/T7 follow-up flagged that chained derivations (e.g.
paint second-coat from wall area, primer from wall area, base LF
approximated from area) reuse the parent's confidence verbatim
instead of degrading slightly per derivation step. The conservative
fix: apply a per-step degradation chain so a 3rd-degree derivation
(area → approximated perimeter → wall SF → second-coat allowance)
lands at a meaningfully-lower confidence than the primary measurement.

The degradation schedule is hand-calibrated to match the band
boundaries:

* 1st-degree derivation: ``confidence × 0.95``
* 2nd-degree derivation: ``confidence × 0.90``
* 3rd-degree derivation: ``confidence × 0.85``
* ≥ 4th-degree:           ``confidence × 0.85`` (clamped)
* Floor at 0.45 (PARAMETRIC tier on T7 banding).

Today's back-fill pipeline is a 1:1 transformer (one synthesis row
gets one back-filled row), so the only real chain present is the
sqrt-fallback path: ``area_sf → 4·sqrt(area)`` (1st step,
approximated perimeter) ``→ perimeter × height × share`` (2nd step,
wall SF). The existing ``_BACKFILL_CONF_FALLBACK = 0.65`` value pins
the 2-step sqrt-fallback case lower than the chain formula would
give (0.92 × 0.90 = 0.828) — an INTENTIONAL conservative override
to flag the geometric approximation for hand review independently
of the chain depth. The :func:`chain_decay` helper is exposed here
for future N-from-one derivations (paint topcoat / primer fan-out
from a primary wall row, joint-tape allowances, etc.) to call into
without re-deriving the multipliers.
"""

from __future__ import annotations

import logging
import math
import re

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
    "DOOR_DEFAULT_OPENING_SF",
    "WINDOW_DEFAULT_OPENING_SF",
    "CHAIN_DECAY_MULTIPLIERS",
    "CHAIN_DECAY_FLOOR",
    "chain_decay",
    "backfill_finish_quantities",
]


# Notes appended after the original synthesis notes (joined with "; ").
BACKFILL_NOTE_OK: str = "backfill=ok"
BACKFILL_NOTE_SKIP_ROOM: str = "backfill skipped: room not in schedule"
BACKFILL_NOTE_FALLBACK_PERIM: str = "perimeter approximated from area (sqrt fallback)"
BACKFILL_NOTE_NO_HEIGHT: str = "ceiling height missing — wall back-fill skipped"
# Surfaces a "we have no opening data at all" status — only emitted on
# wall rows when BOTH ``door_schedule`` and ``window_schedule`` were
# ``None``. When either is provided (even if no openings matched this
# room) the back-fill assumes the operator passed the available data
# and is comfortable with whatever the deduction landed at; the
# specific deduction count + total SF + per-wall amount go on the row
# as ``openings_deducted=…`` audit fields instead.
BACKFILL_NOTE_NO_OPENINGS: str = "openings not deducted (no door/window schedules provided)"


# Phase T5.1 — standard commercial opening defaults used when a door or
# window record carries a ``room_number`` but the schedule omitted both
# its width and height (or one of them). These match the calibration v3
# numbers the brief cited: ~21 SF for a 3'-0" × 7'-0" door is the
# American Institute of Architects' typical commercial interior door;
# ~12 SF for a 3'-0" × 4'-0" window is a sensible commercial default
# that splits the difference between a 2'-0" × 3'-0" residential window
# (6 SF) and a 4'-0" × 5'-0" punched window (20 SF). Both values are
# conservative — under-deduction is preferred to over-deduction because
# Phase T6 pricing can still review a slightly-gross wall row, but a
# negative wall row would crash the cost-DB lookup.
DOOR_DEFAULT_OPENING_SF: float = 21.0
WINDOW_DEFAULT_OPENING_SF: float = 12.0

# Confidence applied when the back-fill computes from real area + height
# (i.e. the operator can defend every term in the formula). Carries the
# 0.92 ceiling so the row stays in the same band as the synthesis output.
_BACKFILL_CONF_FULL: float = 0.92
# Confidence applied when the back-fill falls back to the square-room
# perimeter approximation. The 0.65 band signals "trustworthy enough to
# show but flag for human review" per the Phase T6 binning rubric.
_BACKFILL_CONF_FALLBACK: float = 0.65


# Phase T6.1 — chain-derivation decay schedule. See the module docstring
# section "Phase T6.1 — chain-derivation decay" for the rationale. Hand-
# calibrated multipliers per derivation depth so a 3-step chain lands
# meaningfully below a 1-step chain even when the source confidence is
# the same. ``CHAIN_DECAY_MULTIPLIERS[0]`` is the 0-step (= primary)
# identity multiplier; ``[1]`` is the 1st-step haircut; etc. Indices
# beyond the table cap at the deepest published step (currently 3).
CHAIN_DECAY_MULTIPLIERS: tuple[float, ...] = (1.00, 0.95, 0.90, 0.85)
CHAIN_DECAY_FLOOR: float = 0.45


def chain_decay(parent_confidence: float, depth: int) -> float:
    """Return ``max(CHAIN_DECAY_FLOOR, parent_confidence * mult[depth])``.

    Phase T6.1 helper for derivation chains where a single primary
    measurement (e.g. wall SF) spawns multiple derived items (paint
    primer + topcoat allowances, joint-tape, etc.). Each step in
    the chain takes one slot from :data:`CHAIN_DECAY_MULTIPLIERS`;
    indices beyond the table clamp at the last entry (treats deep
    chains as "at least as bad as 3rd-degree"). The 0.45 floor pins
    output to the PARAMETRIC tier so a deep chain can't sink below
    the fallback that the same item would land at without a source
    at all.

    ``depth=0`` is the identity (primary, no haircut). Values < 0
    are coerced to 0; non-integer floats are accepted but
    intentionally not interpolated — pick the integer step that
    matches the derivation graph.

    Today's back-fill pipeline is a 1:1 transformer with no real
    multi-step fan-out; this helper is exposed for future N-from-one
    derivations (paint topcoat / primer / joint-tape from a primary
    wall row) to call into without re-deriving the multipliers. The
    sqrt-fallback case in :func:`_backfill_wall` and
    :func:`_backfill_base` keeps its conservative
    ``_BACKFILL_CONF_FALLBACK = 0.65`` flat value because the 0.65
    is calibrated for the GEOMETRIC approximation uncertainty, not
    for chain depth — see the module docstring.
    """
    pc = max(0.0, min(1.0, float(parent_confidence)))
    step = max(0, int(depth))
    idx = min(step, len(CHAIN_DECAY_MULTIPLIERS) - 1)
    return max(CHAIN_DECAY_FLOOR, round(pc * CHAIN_DECAY_MULTIPLIERS[idx], 4))


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
        door_schedule: Phase T5.1 — door schedule with ``room_number``
            populated per :class:`~core.schemas.DoorRecord`. Each door
            whose ``room_number`` matches a room in ``room_schedule``
            contributes ``(width_in × height_in) / 144`` SF (or
            :data:`DOOR_DEFAULT_OPENING_SF` when dimensions are
            missing) to that room's wall-opening deduction.
        window_schedule: Phase T5.1 — window schedule. Same shape as
            ``door_schedule``; falls back to
            :data:`WINDOW_DEFAULT_OPENING_SF` when dimensions are
            missing.

    Returns:
        A new list where every finish-synthesis row's ``quantity`` and
        ``confidence`` have been updated per the surface-specific
        formula in the module docstring. Non-finish rows pass through
        unchanged. Finish rows whose room# is missing from the room
        schedule pass through with ``quantity=0.0`` preserved and a
        ``backfill_skipped`` note appended for the auditor.
    """
    if not items:
        return []

    room_map = _build_room_map(room_schedule)
    finish_height_map = _build_finish_ceiling_map(finish_schedule)

    if not room_map:
        # Nothing to join against — return the input unchanged so the
        # synthesis rows stay visible (Phase T6 can still surface them
        # at quantity=0 for human review).
        return list(items)

    # Phase T5.1 — compute per-room opening totals up front so every
    # wall row for a given room shares a consistent deduction baseline.
    # Doing this once at the top is also what makes the back-fill
    # idempotent: re-running with the same schedules produces the same
    # totals (the function recomputes from input every call rather than
    # consuming the previously-back-filled quantity).
    room_openings = _build_room_openings_map(
        door_schedule, window_schedule, room_map,
    )
    # When neither opening schedule was provided we surface that to the
    # auditor — wall SF is GROSS and the user should know openings
    # weren't deducted. When at least one was provided we trust the
    # operator passed what's available and treat empty matches as zero
    # deductions.
    opening_data_available = (
        door_schedule is not None or window_schedule is not None
    )

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

        out.append(_compute_backfill(
            item, surface, room, finish_height_map,
            room_openings=room_openings,
            opening_data_available=opening_data_available,
        ))

    return out


def _compute_backfill(
    item: TakeoffItem,
    surface: str,
    room: RoomRecord,
    finish_height_map: dict[str, float],
    *,
    room_openings: dict[str, tuple[int, float]],
    opening_data_available: bool,
) -> TakeoffItem:
    """Per-surface back-fill computation. Pure dispatch on ``surface``."""
    if surface == "floor" or surface == "ceiling":
        return _backfill_area_surface(item, surface, room)
    if surface == "base":
        return _backfill_base(item, room)
    if surface.startswith("wall"):
        return _backfill_wall(
            item, surface, room, finish_height_map,
            room_openings=room_openings,
            opening_data_available=opening_data_available,
        )
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
    *,
    room_openings: dict[str, tuple[int, float]],
    opening_data_available: bool,
) -> TakeoffItem:
    """Wall SF = ``perimeter × height × share`` minus a share-proportional
    deduction for doors / windows opening into the room (Phase T5.1).
    """
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

    raw_quantity = perimeter_lf * height_ft * share
    confidence = _BACKFILL_CONF_FALLBACK if fallback_used else _BACKFILL_CONF_FULL

    # Phase T5.1 — opening deduction. Per-room totals were assembled once
    # at the top of ``backfill_finish_quantities``; here we apply the
    # share-proportional slice to this one wall direction. Cap is at the
    # raw wall SF — a wall never goes negative even when openings somehow
    # over-fill it (rare; tends to be a sign of bad source data).
    room_key = (room.room_number or "").strip()
    open_count, open_total_sf = room_openings.get(room_key, (0, 0.0))
    raw_deduction = open_total_sf * share
    deduction = min(raw_deduction, raw_quantity)
    overflow = raw_deduction > raw_quantity
    net_quantity = max(raw_quantity - deduction, 0.0)

    extras: list[str] = []
    if fallback_used:
        extras.append(BACKFILL_NOTE_FALLBACK_PERIM)
    extras.append(BACKFILL_NOTE_OK)
    if open_count > 0:
        extras.append(f"openings_deducted={open_count}")
        extras.append(f"opening_sf={round(open_total_sf, 2)}")
        extras.append(f"{surface}_deduction={round(deduction, 2)}")
        if overflow:
            # Surface explicitly that the cap fired — the row's gross
            # geometry doesn't agree with the schedule, and the
            # operator should reconcile rather than trust either side.
            extras.append(
                f"openings_overflow: {surface} opening SF exceeded raw wall SF"
            )
    elif not opening_data_available:
        # Preserve the T5 "we don't know about openings" audit hint
        # only when neither door nor window schedule was supplied at
        # all. When schedules are supplied but no openings matched
        # this room, that's an intentional zero-deduction, not a
        # missing-data condition.
        extras.append(BACKFILL_NOTE_NO_OPENINGS)
    return _backfilled_item(
        item,
        quantity=net_quantity,
        confidence=confidence,
        extra_notes=extras,
    )


# ---------------------------------------------------------------------------
# Phase T5.1 — opening deduction helpers
# ---------------------------------------------------------------------------


def _opening_sf_from(
    width_in: float | None,
    height_in: float | None,
    default_sf: float,
) -> float:
    """Convert ``width_in × height_in`` → SF (÷ 144); fall back to ``default_sf``.

    The default fires when either dimension is missing or non-positive.
    Negative dimensions are treated as missing (defensive; the
    schedule extractors filter these out upstream but a future LLM
    pass could conceivably emit one).
    """
    if (
        width_in is not None and width_in > 0
        and height_in is not None and height_in > 0
    ):
        return (width_in * height_in) / 144.0
    return default_sf


def _build_room_openings_map(
    door_schedule: DoorScheduleResult | None,
    window_schedule: WindowScheduleResult | None,
    room_map: dict[str, RoomRecord],
) -> dict[str, tuple[int, float]]:
    """Aggregate per-room ``(opening_count, total_opening_sf)``.

    Openings are bucketed by their ``room_number`` after stripping
    whitespace. Three classes of opening are skipped (silently, with a
    debug log so the auditor can drill in if a number doesn't match
    expectations):

    * No ``room_number`` (orphan) — can't be attributed to any room.
    * ``room_number`` not in ``room_map`` — the room schedule didn't
      see this room; treating the opening as belonging to it would
      have no wall row to land on.

    Dimensions: when both ``width_in`` and ``height_in`` are present
    and positive, the opening SF is ``width × height / 144``. Either
    missing falls back to the standard-commercial defaults
    (:data:`DOOR_DEFAULT_OPENING_SF` / :data:`WINDOW_DEFAULT_OPENING_SF`)
    so a schedule that documents the door but elides the dimensions
    still subtracts something rather than silently overcounting wall
    paint.
    """
    out: dict[str, tuple[int, float]] = {}

    def _add(room_key: str, sf: float) -> None:
        prev_count, prev_sf = out.get(room_key, (0, 0.0))
        out[room_key] = (prev_count + 1, prev_sf + sf)

    orphan_doors = 0
    unknown_room_doors = 0
    if door_schedule is not None:
        for d in door_schedule.doors:
            key = (d.room_number or "").strip() if d.room_number else ""
            if not key:
                orphan_doors += 1
                continue
            if key not in room_map:
                unknown_room_doors += 1
                continue
            _add(key, _opening_sf_from(
                d.width_in, d.height_in, DOOR_DEFAULT_OPENING_SF,
            ))

    orphan_windows = 0
    unknown_room_windows = 0
    if window_schedule is not None:
        for w in window_schedule.windows:
            key = (w.room_number or "").strip() if w.room_number else ""
            if not key:
                orphan_windows += 1
                continue
            if key not in room_map:
                unknown_room_windows += 1
                continue
            _add(key, _opening_sf_from(
                w.width_in, w.height_in, WINDOW_DEFAULT_OPENING_SF,
            ))

    if orphan_doors or unknown_room_doors or orphan_windows or unknown_room_windows:
        logger.debug(
            "backfill_finish_quantities: openings could not be deducted — "
            "orphan_doors=%d, unknown_room_doors=%d, "
            "orphan_windows=%d, unknown_room_windows=%d",
            orphan_doors, unknown_room_doors,
            orphan_windows, unknown_room_windows,
        )

    return out
