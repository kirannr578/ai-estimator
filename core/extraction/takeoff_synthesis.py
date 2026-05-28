"""Phases T2 + T2.5 — synthesize :class:`TakeoffItem` rows from typed schedules.

Pure converter that turns the typed door / window records produced by the
deterministic schedule pre-passes (:mod:`core.extraction.door_schedule`
+ :mod:`core.extraction.window_schedule`) into priced-ready
:class:`core.schemas.TakeoffItem` rows. One ``DoorRecord`` or
``WindowRecord`` becomes one ``TakeoffItem``; the synthesised items are
deliberately **additive** to LLM-extracted takeoffs — cross-source
dedupe is Phase T3 / T2.5 dedupe.

Door CSI mapping (keyword heuristic, see ``_DOOR_CSI_MAPPING``):

* Hollow metal  (``HM`` / ``HOLLOW METAL``)              → ``08 11 13``
* Aluminum frame / storefront (``ALUM`` / ``STOREFRONT``) → ``08 11 16``
* Wood / solid-core (``WD`` / ``SCWD`` / ``WOOD``)        → ``08 14 13``
* Glass / glazed (``GLASS`` / ``GLAZED``)                  → ``08 80 00``
* Unknown / unmatched                                      → ``08 10 00``

Window CSI mapping (keyword heuristic, see ``_WINDOW_CSI_MAPPING``):

* Aluminum / Alum windows                                  → ``08 51 13``
* Storefront / curtain wall (size-tiered, see ``_classify_window``) →
  ``08 44 13`` (entry storefronts) or ``08 41 13`` (large curtain wall;
  any dimension > 96 in. on a storefront-tagged record)
* Vinyl windows                                            → ``08 53 13``
* Metal-clad wood (``METAL CLAD`` / ``CLAD``)              → ``08 52 19``
* Wood windows                                             → ``08 52 13``
* Steel windows                                            → ``08 51 23``
* Unknown / unmatched                                      → ``08 50 00``

Confidence rubric (same for doors and windows):

* mark **and** type present → ``0.92``
* only one of mark / type   → ``0.80``
* neither                   → ``0.60`` (caller may filter)

Every synthesised row carries ``source=door_schedule_prepass`` or
``source=window_schedule_prepass`` at the start of its ``notes`` field.
The schema does not yet expose a dedicated ``source`` column, so the
notes prefix is the stable handle the dedupe passes (T3 / T2.5) grep for.
"""

from __future__ import annotations

from typing import Final

from core.schemas import (
    AVDeviceRecord,
    AVScheduleResult,
    DoorRecord,
    DoorScheduleResult,
    FinishRecord,
    FinishScheduleResult,
    HVACEquipmentRecord,
    HVACScheduleResult,
    KitchenEquipmentRecord,
    KitchenScheduleResult,
    LabCaseworkRecord,
    LabScheduleResult,
    LightingFixtureRecord,
    LightingScheduleResult,
    PanelRecord,
    PanelScheduleResult,
    PlumbingFixtureRecord,
    PlumbingScheduleResult,
    SecurityDeviceRecord,
    SecurityScheduleResult,
    TakeoffItem,
    WindowRecord,
    WindowScheduleResult,
)

__all__ = [
    "SYNTHESIS_SOURCE_TAG",
    "SYNTHESIS_SOURCE_TAG_WINDOW",
    "SYNTHESIS_SOURCE_TAG_FINISH",
    "SYNTHESIS_SOURCE_TAG_PANEL",
    "SYNTHESIS_SOURCE_TAG_LIGHTING",
    "SYNTHESIS_SOURCE_TAG_HVAC",
    "SYNTHESIS_SOURCE_TAG_PLUMBING",
    "SYNTHESIS_SOURCE_TAG_KITCHEN",
    "SYNTHESIS_SOURCE_TAG_LAB",
    "SYNTHESIS_SOURCE_TAG_AV",
    "SYNTHESIS_SOURCE_TAG_SECURITY",
    "DERIVATION_HAIRCUT_MULTIPLIER",
    "DERIVATION_FLOOR_CONFIDENCE",
    "inherit_with_haircut",
    "synthesize_door_takeoff_items",
    "synthesize_window_takeoff_items",
    "synthesize_finish_takeoff_items",
    "synthesize_panel_takeoff_items",
    "synthesize_lighting_takeoff_items",
    "synthesize_hvac_takeoff_items",
    "synthesize_plumbing_takeoff_items",
    "synthesize_kitchen_takeoff_items",
    "synthesize_lab_takeoff_items",
    "synthesize_av_takeoff_items",
    "synthesize_security_takeoff_items",
]


SYNTHESIS_SOURCE_TAG: Final[str] = "door_schedule_prepass"
SYNTHESIS_SOURCE_TAG_WINDOW: Final[str] = "window_schedule_prepass"
SYNTHESIS_SOURCE_TAG_FINISH: Final[str] = "finish_schedule_prepass"
SYNTHESIS_SOURCE_TAG_PANEL: Final[str] = "panel_schedule_prepass"
SYNTHESIS_SOURCE_TAG_LIGHTING: Final[str] = "lighting_schedule_prepass"
SYNTHESIS_SOURCE_TAG_HVAC: Final[str] = "hvac_schedule_prepass"
SYNTHESIS_SOURCE_TAG_PLUMBING: Final[str] = "plumbing_schedule_prepass"
SYNTHESIS_SOURCE_TAG_KITCHEN: Final[str] = "kitchen_schedule_prepass"
SYNTHESIS_SOURCE_TAG_LAB: Final[str] = "lab_schedule_prepass"
SYNTHESIS_SOURCE_TAG_AV: Final[str] = "av_schedule_prepass"
SYNTHESIS_SOURCE_TAG_SECURITY: Final[str] = "security_schedule_prepass"


# ---------------------------------------------------------------------------
# Phase T6.1 — derivation-confidence inheritance
# ---------------------------------------------------------------------------
#
# Worker W's T6/T7 follow-up flagged that secondary / unit-converted items
# (panel branch breakers from the parent panel record, fixture lamp/driver
# from the parent fixture row, equipment disconnect+flex from the parent
# HVAC equipment row) used a hard-coded confidence (0.85, 0.85, 0.70
# respectively) regardless of how confident the underlying source record
# actually was. Concrete consequence: a 0.95-source row produced a 0.85
# derived item that landed in OPERATOR_REVIEW instead of AUTO_APPROVE,
# even though the derived count is uniquely determined by the source.
#
# Phase T6.1 fix: derived items inherit the parent / primary row's
# effective confidence with a small per-derivation-step haircut. The
# 0.95 multiplier represents "we lose ~5% confidence per derivation
# step" (matches the chain-decay convention adopted in T6.1's
# ``takeoff_backfill`` Issue 2 fix). The 0.45 floor pins derivations
# to the PARAMETRIC tier on T7 banding so a derivation can never sink
# below the parametric default that the same row would get if it had
# no source at all.
#
# Primary items (door enclosure, window enclosure, panel enclosure,
# fixture EA, equipment EA) keep their unmodified source confidence —
# the haircut only applies to SECONDARY / DERIVED rows. Parametric
# placeholders (panel feeder LF at 0.55, HVAC MEP rough-in LS at 0.45,
# plumbing rough-in LS at 0.45) keep their epistemological flat values
# because their uncertainty isn't about derivation depth — it's about
# the operator needing to walk the riser / plan to fill the real
# quantity in.

DERIVATION_HAIRCUT_MULTIPLIER: Final[float] = 0.95
DERIVATION_FLOOR_CONFIDENCE: Final[float] = 0.45


def inherit_with_haircut(
    source_confidence: float,
    *,
    multiplier: float = DERIVATION_HAIRCUT_MULTIPLIER,
    floor: float = DERIVATION_FLOOR_CONFIDENCE,
) -> float:
    """Return ``max(floor, source_confidence * multiplier)`` rounded to 4 dp.

    Phase T6.1 helper used by every secondary / unit-converted item
    in the synthesis pipeline so a high-confidence source row
    propagates its confidence to its derived items (minus the
    one-step haircut) instead of flattening to a hard-coded constant.

    See the module-level "Phase T6.1" docstring section for the
    rationale. ``source_confidence`` is clamped into ``[0, 1]`` so a
    malformed input can't push the result out of bounds.
    """
    sc = max(0.0, min(1.0, float(source_confidence)))
    return max(floor, round(sc * multiplier, 4))


# ---------------------------------------------------------------------------
# CSI mapping — doors
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
# CSI mapping — windows
# ---------------------------------------------------------------------------
#
# Ordered (specific → generic). The window haystack is
# ``type + frame + material + operation`` upper-cased. Metal-clad is
# checked before plain wood so a record tagged ``CLAD WOOD`` lands on
# ``08 52 19`` (Metal-Clad Wood Windows) rather than the bare wood
# section. Storefront / curtain wall lives in a separate size-aware
# helper (``_classify_window``) because the operator's choice between
# ``08 44 13`` (Glazed Aluminum Curtain Walls) and ``08 41 13``
# (Aluminum-Framed Entrances and Storefronts) depends on the unit size.

_CSI_WIN_ALUM:       Final[tuple[str, str, str]] = ("08", "08 51 13", "Aluminum Window")
_CSI_WIN_STEEL:      Final[tuple[str, str, str]] = ("08", "08 51 23", "Steel Window")
_CSI_WIN_WOOD:       Final[tuple[str, str, str]] = ("08", "08 52 13", "Wood Window")
_CSI_WIN_METAL_CLAD: Final[tuple[str, str, str]] = ("08", "08 52 19", "Metal-Clad Wood Window")
_CSI_WIN_VINYL:      Final[tuple[str, str, str]] = ("08", "08 53 13", "Vinyl Window")
_CSI_WIN_STOREFRONT: Final[tuple[str, str, str]] = ("08", "08 41 13", "Aluminum Storefront")
_CSI_WIN_CURTAIN:    Final[tuple[str, str, str]] = ("08", "08 44 13", "Aluminum Curtain Wall")
_CSI_WIN_GENERIC:    Final[tuple[str, str, str]] = ("08", "08 50 00", "Window")

# Threshold above which a STOREFRONT / CURTAIN keyword is upgraded from
# ``08 41 13`` (storefronts and entrances, typical residential / TI
# scale, < 8 ft tall and < 12 ft wide) to ``08 44 13`` (glazed curtain
# wall, larger unitized systems). Tuned to a single dimension > 96 in.
# (8 ft) — the threshold the operator's discretion settles on for the
# T2.5 brief. Documented inline so a future maintainer can lift it.
_WIN_CURTAIN_WALL_DIM_IN: Final[float] = 96.0

# Order matters: metal-clad before bare wood; vinyl / steel before alum
# only because ``ALUM`` is a substring of ``ALUMINUM`` (cheap match) and
# we want the keyword scan to short-circuit on the right family first.
_WIN_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # Metal-clad wood — ``CLAD WOOD`` / ``METAL CLAD`` / ``ALCLAD``.
    # Checked BEFORE bare wood and BEFORE aluminum to avoid a
    # ``CLAD WOOD`` record routing to either ``08 51 13`` or
    # ``08 52 13`` instead of the more-specific ``08 52 19``.
    (("METAL CLAD", "METAL-CLAD", "CLAD WOOD", "ALCLAD"), _CSI_WIN_METAL_CLAD),
    # Vinyl windows — explicit family, never a frame on another material.
    (("VINYL",), _CSI_WIN_VINYL),
    # Steel windows — historic / industrial style, distinct from aluminum.
    (("STEEL",), _CSI_WIN_STEEL),
    # Wood windows (bare wood, no clad).
    (("WOOD", "WD"), _CSI_WIN_WOOD),
    # Aluminum windows (last among specifics; size-aware storefront
    # classification is handled separately in ``_classify_window``).
    (("ALUMINUM", "ALUM"), _CSI_WIN_ALUM),
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


# ---------------------------------------------------------------------------
# Window helpers (Phase T2.5)
# ---------------------------------------------------------------------------


def _classify_window(window: WindowRecord) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one window.

    Storefront / curtain wall is size-tiered: ``08 44 13`` (Glazed
    Aluminum Curtain Walls) when ANY dimension on the record exceeds
    ``_WIN_CURTAIN_WALL_DIM_IN`` (96 in. / 8 ft); otherwise
    ``08 41 13`` (Aluminum-Framed Entrances and Storefronts). The
    operator's discretion called out in the T2.5 brief is encoded as
    this single threshold so a future maintainer can lift it.

    ``type`` wins when present; falls back to ``frame`` / ``material``
    / ``operation`` for schedules that left ``type`` blank.
    """
    parts = [window.type, window.frame, window.material, window.operation]
    hay = " ".join(p for p in parts if p).upper()
    if not hay:
        return _CSI_WIN_GENERIC
    # Storefront / curtain wall takes precedence over the plain
    # aluminum classification: an ``ALUM STOREFRONT`` record must land
    # on ``08 41 13`` or ``08 44 13``, never ``08 51 13``.
    if "STOREFRONT" in hay or "CURTAIN" in hay:
        widest = max(
            (d for d in (window.width_in, window.height_in) if d is not None),
            default=0.0,
        )
        if widest > _WIN_CURTAIN_WALL_DIM_IN or "CURTAIN" in hay:
            return _CSI_WIN_CURTAIN
        return _CSI_WIN_STOREFRONT
    for keywords, mapping in _WIN_CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_WIN_GENERIC


def _window_confidence(window: WindowRecord) -> float:
    has_mark = bool(window.mark and window.mark.strip())
    has_type = bool(window.type and window.type.strip())
    if has_mark and has_type:
        return 0.92
    if has_mark or has_type:
        return 0.80
    return 0.60


def _describe_window(window: WindowRecord, family: str) -> str:
    """Build a human-readable description for a window TakeoffItem.

    Examples::

        "Window W-01 — ALUM-S 3'-0\\" x 5'-0\\""
        "Window 102 — Wood Window"
        "Window (unmarked) — Aluminum Window"
    """
    mark = (window.mark or "").strip()
    label = (window.type or "").strip() or family
    head = f"Window {mark}" if mark else "Window (unmarked)"
    width = _format_inches(window.width_in)
    height = _format_inches(window.height_in)
    if width and height:
        return f"{head} — {label} {width} x {height}"
    return f"{head} — {label}"


def _window_notes_for(window: WindowRecord) -> str:
    """Stable, source-tagged notes string for window dedupe to grep.

    Format mirrors :func:`_notes_for` for doors: ``key=value`` pairs joined
    by ``"; "``. The first pair is always
    ``source=window_schedule_prepass`` so a prefix-match is cheap.
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_WINDOW}"]
    if window.mark:
        bits.append(f"mark={window.mark}")
    if window.type:
        bits.append(f"type={window.type}")
    width_s = _format_inches(window.width_in)
    height_s = _format_inches(window.height_in)
    if width_s and height_s:
        bits.append(f"size={width_s} x {height_s}")
    if window.width_in is not None:
        bits.append(f"width_in={window.width_in:g}")
    if window.height_in is not None:
        bits.append(f"height_in={window.height_in:g}")
    if window.sill_height_in is not None:
        bits.append(f"sill_height_in={window.sill_height_in:g}")
    if window.glazing:
        bits.append(f"glazing={window.glazing}")
    if window.operation:
        bits.append(f"operation={window.operation}")
    if window.frame:
        bits.append(f"frame={window.frame}")
    if window.material:
        bits.append(f"material={window.material}")
    if window.u_factor is not None:
        bits.append(f"u_factor={window.u_factor:g}")
    if window.shgc is not None:
        bits.append(f"shgc={window.shgc:g}")
    return "; ".join(bits)


def synthesize_window_takeoff_items(
    schedule: WindowScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``WindowRecord`` on ``schedule`` into a ``TakeoffItem``.

    Mirror of :func:`synthesize_door_takeoff_items` for the window-schedule
    pre-pass. Returns ``[]`` when ``schedule`` is ``None`` or has no
    windows. Each emitted item carries ``quantity=1.0``, ``unit="EA"``,
    a CSI section chosen by :func:`_classify_window`, and a confidence
    per the same rubric used for doors. Every row's ``notes`` field
    starts with ``source=window_schedule_prepass`` for the T2.5 dedupe
    pass to find.
    """
    if schedule is None or not schedule.windows:
        return []
    sheets: list[str] = [sheet_id] if sheet_id else []
    items: list[TakeoffItem] = []
    for window in schedule.windows:
        division, section, family = _classify_window(window)
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_window(window, family),
            quantity=1.0,
            unit="EA",
            confidence=_window_confidence(window),
            source_sheet_ids=list(sheets),
            notes=_window_notes_for(window),
        ))
    return items


# ---------------------------------------------------------------------------
# Finish helpers (Phase T4)
# ---------------------------------------------------------------------------
#
# Per-room expansion shape (THE structural difference vs. T2 + T2.5):
# each ``FinishRecord`` → multiple ``TakeoffItem`` rows, one per finished
# surface (floor / base / wall / ceiling). Wall finishes fan out to 1 row
# when uniform (or when the schedule uses a single ``WALL`` column),
# else N rows — one per unique compass-direction finish.
#
# CSI mapping by code prefix (keyword → CSI section). Floor / base /
# wall / ceiling families each have their own lookup table so a finish
# code like ``TILE-1`` routes correctly depending on which surface it
# was assigned to (floor tile is ``09 30 13``, wall tile is also
# ``09 30 13``, base tile lives in the same family — but the synth row
# is still per-surface so dedupe stays unambiguous).
#
# Quantity is **always 0.0 at this phase** — Phase T6 will compute SF
# from a room area cross-reference. T4 emits the line with a unit (SF
# for every finish surface), confidence, description, and notes so the
# takeoff sheet shows it and Phase T6 can fill the quantity.


# (csi_division, csi_section, family-label-for-description) for FLOOR finishes.
_CSI_FLOOR_VCT:        Final[tuple[str, str, str]] = ("09", "09 65 19", "Vinyl Composition Tile (VCT)")
_CSI_FLOOR_SHEET_VINYL: Final[tuple[str, str, str]] = ("09", "09 65 16", "Sheet Vinyl")
_CSI_FLOOR_CARPET:     Final[tuple[str, str, str]] = ("09", "09 68 13", "Carpet")
_CSI_FLOOR_TILE:       Final[tuple[str, str, str]] = ("09", "09 30 13", "Ceramic Tile")
_CSI_FLOOR_WOOD:       Final[tuple[str, str, str]] = ("09", "09 64 29", "Wood Flooring")
_CSI_FLOOR_POL_CONC:   Final[tuple[str, str, str]] = ("03", "03 35 43", "Polished Concrete")
_CSI_FLOOR_GENERIC:    Final[tuple[str, str, str]] = ("09", "09 60 00", "Flooring")

# Order matters: more-specific tokens BEFORE substrings. ``SHEET`` /
# ``SHT`` win over ``VINYL`` so ``SHEET VINYL`` lands on ``09 65 16``,
# not ``09 65 19`` (VCT). ``POL`` / ``SEAL`` / ``SC`` (sealed concrete)
# beat plain ``CONC`` for the polished/sealed routing.
_FLOOR_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # Polished / sealed concrete first — cross-division (03 35 43).
    # Both space- and dash-joined forms are accepted ("POL CONC" /
    # "POL-CONC" / "POLISHED CONCRETE"). ``POL`` alone is included for
    # the bare-token case; it's a distinctive enough finish code prefix
    # that no other floor family collides with it.
    (("POL CONC", "POL-CONC", "POLISHED", "SEAL CONC", "SEAL-CONC",
      "SEALED", "SC", "POL"), _CSI_FLOOR_POL_CONC),
    # Sheet vinyl before LVT / VCT
    (("SHEET VINYL", "SHT VINYL", "SHEET"), _CSI_FLOOR_SHEET_VINYL),
    # VCT / vinyl tile / LVT / LVP
    (("VCT", "VINYL", "LVT", "LVP"), _CSI_FLOOR_VCT),
    # Carpet
    (("CPT", "CARPET"), _CSI_FLOOR_CARPET),
    # Ceramic / porcelain tile
    (("TILE", "CT", "CER", "PORC"), _CSI_FLOOR_TILE),
    # Hardwood / wood floors
    (("HW", "WD", "WOOD"), _CSI_FLOOR_WOOD),
)

# (csi_division, csi_section, family-label) for BASE finishes.
_CSI_BASE_RUBBER:  Final[tuple[str, str, str]] = ("09", "09 65 13", "Resilient Base")
_CSI_BASE_TILE:    Final[tuple[str, str, str]] = ("09", "09 30 13", "Ceramic Base")
_CSI_BASE_WOOD:    Final[tuple[str, str, str]] = ("09", "09 64 33", "Wood Base")
_CSI_BASE_GENERIC: Final[tuple[str, str, str]] = ("09", "09 60 00", "Base")

_BASE_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # Resilient (rubber / vinyl) base
    (("RB", "RUBBER", "RES", "VB", "TB"), _CSI_BASE_RUBBER),
    # Ceramic base
    (("CB", "CER", "CT"), _CSI_BASE_TILE),
    # Wood base
    (("WB", "WOOD", "WD"), _CSI_BASE_WOOD),
)

# (csi_division, csi_section, family-label) for WALL finishes.
_CSI_WALL_PAINT:   Final[tuple[str, str, str]] = ("09", "09 91 23", "Interior Paint")
_CSI_WALL_VWC:     Final[tuple[str, str, str]] = ("09", "09 72 00", "Wall Covering")
_CSI_WALL_FRP:     Final[tuple[str, str, str]] = ("06", "06 64 00", "FRP Panels")
_CSI_WALL_TILE:    Final[tuple[str, str, str]] = ("09", "09 30 13", "Ceramic Wall Tile")
_CSI_WALL_GENERIC: Final[tuple[str, str, str]] = ("09", "09 70 00", "Wall Finish")

_WALL_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # FRP / fiber-reinforced plastic panels — cross-division (06 64 00)
    # checked before WC so ``FRP`` doesn't accidentally route as
    # ``Wall Covering``.
    (("FRP",), _CSI_WALL_FRP),
    # Wall covering / vinyl wall covering
    (("WC", "VWC", "WALLCOVERING", "WALL COVERING"), _CSI_WALL_VWC),
    # Ceramic / porcelain wall tile
    (("TILE", "CT", "CER", "PORC"), _CSI_WALL_TILE),
    # Paint (last, broad keyword)
    (("PT", "PAINT", "EP"), _CSI_WALL_PAINT),
)

# (csi_division, csi_section, family-label) for CEILING finishes.
_CSI_CEIL_ACT:      Final[tuple[str, str, str]] = ("09", "09 51 13", "Acoustic Ceiling Tile (ACT)")
_CSI_CEIL_GYP:      Final[tuple[str, str, str]] = ("09", "09 29 00", "Gypsum Board Ceiling")
_CSI_CEIL_WOOD:     Final[tuple[str, str, str]] = ("09", "09 64 29", "Wood Ceiling")
_CSI_CEIL_EXPOSED:  Final[tuple[str, str, str]] = ("09", "09 00 00", "Exposed Structure (marker)")
_CSI_CEIL_GENERIC:  Final[tuple[str, str, str]] = ("09", "09 50 00", "Ceiling Finish")

_CEIL_CSI_MAPPING: Final[tuple[tuple[tuple[str, ...], tuple[str, str, str]], ...]] = (
    # Acoustic ceiling tile
    (("ACT", "ACOUSTIC", "ACP", "ACOU"), _CSI_CEIL_ACT),
    # Exposed / open structure — marker only
    (("EXPOSED", "OPEN", "EXP"), _CSI_CEIL_EXPOSED),
    # Wood ceiling (rare; checked before GYP because ``WD CEIL`` would
    # otherwise be partially matched by neither family without an
    # explicit entry).
    (("WD CEIL", "WOOD"), _CSI_CEIL_WOOD),
    # Gypsum board / GWB / GYP BD
    (("GYP", "GWB", "GYP BD", "GB"), _CSI_CEIL_GYP),
)


def _normalise_code(code: str | None) -> str:
    return (code or "").upper().strip()


def _classify_floor(code: str | None) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for a floor code."""
    hay = _normalise_code(code)
    if not hay:
        return _CSI_FLOOR_GENERIC
    for keywords, mapping in _FLOOR_CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_FLOOR_GENERIC


def _classify_base(code: str | None) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for a base code."""
    hay = _normalise_code(code)
    if not hay:
        return _CSI_BASE_GENERIC
    for keywords, mapping in _BASE_CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_BASE_GENERIC


def _classify_wall(code: str | None) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for a wall code."""
    hay = _normalise_code(code)
    if not hay:
        return _CSI_WALL_GENERIC
    for keywords, mapping in _WALL_CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_WALL_GENERIC


def _classify_ceiling(code: str | None) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for a ceiling code."""
    hay = _normalise_code(code)
    if not hay:
        return _CSI_CEIL_GENERIC
    for keywords, mapping in _CEIL_CSI_MAPPING:
        for kw in keywords:
            if kw in hay:
                return mapping
    return _CSI_CEIL_GENERIC


def _finish_confidence(record: FinishRecord, code: str | None) -> float:
    """Confidence rubric: 0.92 with both room + code; 0.80 with one; 0.60 neither."""
    has_room = bool(
        (record.room_number and record.room_number.strip())
        or (record.room_name and record.room_name.strip())
    )
    has_code = bool(code and code.strip())
    if has_room and has_code:
        return 0.92
    if has_room or has_code:
        return 0.80
    return 0.60


def _room_label(record: FinishRecord) -> str:
    """Render a ``Room <#> <Name>`` label, omitting whichever piece is missing."""
    num = (record.room_number or "").strip()
    name = (record.room_name or "").strip()
    if num and name:
        return f"Room {num} {name}"
    if num:
        return f"Room {num}"
    if name:
        return f"Room {name}"
    return "Room (unmarked)"


def _describe_finish(surface: str, code: str | None, record: FinishRecord,
                       family: str) -> str:
    """Build a human-readable description for a finish TakeoffItem.

    Examples::

        "Floor VCT-1 – Room 101 Office"
        "Wall N PT-1 – Room 102 Lobby"
        "Ceiling ACT – Room (unmarked)"
    """
    label = (code or "").strip() or family
    return f"{surface} {label} – {_room_label(record)}"


def _finish_notes_for(surface_token: str, code: str | None,
                        record: FinishRecord) -> str:
    """Stable, source-tagged notes string for finish dedupe to grep.

    Format mirrors the door + window notes shape: ``key=value`` pairs
    joined by ``"; "``. The first pair is always
    ``source=finish_schedule_prepass`` so a prefix-match is cheap.
    Includes ``room=<num>``, ``surface=<floor|base|wall_N|wall_S|...|
    wall_ALL|ceiling>`` and ``code=<code>`` — the triple the finish
    dedupe pass uses to match per-room+surface synthesis.
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_FINISH}"]
    if record.room_number:
        bits.append(f"room={record.room_number}")
    if record.room_name:
        bits.append(f"room_name={record.room_name}")
    bits.append(f"surface={surface_token}")
    if code:
        bits.append(f"code={code}")
    if record.ceiling_height_ft is not None and surface_token.startswith("ceiling"):
        bits.append(f"ceiling_height_ft={record.ceiling_height_ft:g}")
    return "; ".join(bits)


def _emit(items: list[TakeoffItem], *,
           surface_label: str, surface_token: str, code: str | None,
           record: FinishRecord,
           classifier,
           sheets: list[str]) -> None:
    """Helper to build + append one finish TakeoffItem."""
    division, section, family = classifier(code)
    items.append(TakeoffItem(
        csi_division=division,
        csi_section=section,
        description=_describe_finish(surface_label, code, record, family),
        quantity=0.0,
        unit="SF",
        confidence=_finish_confidence(record, code),
        source_sheet_ids=list(sheets),
        notes=_finish_notes_for(surface_token, code, record),
    ))


def synthesize_finish_takeoff_items(
    schedule: FinishScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``FinishRecord`` on ``schedule`` into per-surface ``TakeoffItem``s.

    Unlike door / window synthesis (1:1), each finish record fans out
    into **multiple** items:

    * One **floor** item when ``floor_finish`` is set.
    * One **base** item when ``base_finish`` is set.
    * One **wall** item per unique compass-direction code when
      ``wall_finishes`` has multiple distinct values; one item when
      the codes are uniform (or the schedule used a single ``WALL``
      column → ``wall_finishes == {"ALL": code}``).
    * One **ceiling** item when ``ceiling_finish`` is set. The
      ``EXPOSED`` / ``OPEN`` ceiling routes to a marker section
      (``09 00 00``) so the row still surfaces — Phase T6 may suppress
      it from pricing without losing the audit trail.

    A record with no finishes at all emits zero items.

    Each emitted item carries ``quantity=0.0`` (Phase T6 will compute
    SF from a room area cross-reference), ``unit="SF"``, a CSI section
    chosen per-surface, and a confidence per the rubric in the module
    docstring. ``sheet_id`` (when provided) is stored on
    ``source_sheet_ids`` so downstream consumers can trace each row
    back to the originating sheet.
    """
    if schedule is None or not schedule.rooms:
        return []
    sheets: list[str] = [sheet_id] if sheet_id else []
    items: list[TakeoffItem] = []
    for record in schedule.rooms:
        if record.floor_finish:
            _emit(
                items,
                surface_label="Floor",
                surface_token="floor",
                code=record.floor_finish,
                record=record,
                classifier=_classify_floor,
                sheets=sheets,
            )
        if record.base_finish:
            _emit(
                items,
                surface_label="Base",
                surface_token="base",
                code=record.base_finish,
                record=record,
                classifier=_classify_base,
                sheets=sheets,
            )
        # Walls: collapse to one item when codes are uniform or schedule
        # used a single ``WALL`` column (key=``ALL``). Otherwise emit one
        # per unique compass direction.
        walls = record.wall_finishes or {}
        if walls:
            if "ALL" in walls or len(set(walls.values())) == 1:
                code = walls.get("ALL") or next(iter(walls.values()))
                _emit(
                    items,
                    surface_label="Wall",
                    surface_token="wall_ALL",
                    code=code,
                    record=record,
                    classifier=_classify_wall,
                    sheets=sheets,
                )
            else:
                # Stable compass order — N, S, E, W — so output is
                # deterministic regardless of dict insertion order.
                for direction in ("N", "S", "E", "W"):
                    if direction not in walls:
                        continue
                    code = walls[direction]
                    if not code:
                        continue
                    _emit(
                        items,
                        surface_label=f"Wall {direction}",
                        surface_token=f"wall_{direction}",
                        code=code,
                        record=record,
                        classifier=_classify_wall,
                        sheets=sheets,
                    )
        if record.ceiling_finish:
            _emit(
                items,
                surface_label="Ceiling",
                surface_token="ceiling",
                code=record.ceiling_finish,
                record=record,
                classifier=_classify_ceiling,
                sheets=sheets,
            )
    return items


# ---------------------------------------------------------------------------
# Panel helpers (Phase T2.6)
# ---------------------------------------------------------------------------
#
# Electrical panel schedules fan each ``PanelRecord`` out into four
# families of ``TakeoffItem``:
#
# 1. **1 EA panel enclosure** — CSI 26 24 16 (panelboards) up to and
#    including 400A bus, or 26 24 13 (switchboards) above 400A. The
#    400A threshold matches NEMA / NEC convention: NEMA-1 panelboards
#    are typically rated to 400A bus; > 400A loads ship as floor-
#    mounted switchboards (26 24 13) or distribution boards.
# 2. **N EA branch breakers** grouped by amp size — CSI 26 28 16
#    (circuit breakers, enclosed and motor-circuit protectors). One
#    item per distinct breaker rating (20A, 30A, 50A, ...) with the
#    quantity = circuit-count at that rating.
# 3. **50 LF feeder conductor** — CSI 26 05 19 (low-voltage wire and
#    cable). Parametric default; flagged for hand-takeoff via the
#    0.55 confidence (HAND_TAKEOFF band on the Phase T6 banding).
# 4. **50 LF feeder conduit** — CSI 26 05 33 (raceways).
#    Parametric default; same 0.55 confidence.
#
# Why 50 LF default: on a typical commercial TI / light-commercial
# project the feeder run from the upstream distribution panel to a
# branch panel averages 35-65 LF (electrical riser observations from
# the calibration set). 50 LF is the midpoint and produces a takeoff
# row that lands in OPERATOR_REVIEW band at 0.55 → forcing the
# estimator to verify against the riser diagram. A non-zero quantity
# is intentional — a zero-quantity row would suppress the line at
# pricing time and the estimator could miss the feeder entirely.


# 400A boundary between panelboard (26 24 16) and switchboard (26 24 13).
# NEMA classifies ≤ 400A bus as panelboard, > 400A as switchboard /
# distribution board. Exposed so a future maintainer / test can lift
# the threshold without spelunking the module.
_PANEL_BOARD_BUS_THRESHOLD_A: Final[int] = 400

# Parametric feeder length (LF). Documented inline at the top of the
# panel-helpers section above. Exposed for tests + future tuning.
_FEEDER_PARAMETRIC_LF: Final[float] = 50.0

# Confidence assigned to parametric feeder rows. 0.55 lands in
# ``CostBand.OPERATOR_REVIEW`` on the Phase T6 banding (0.55 < 0.65 → HAND);
# actually 0.55 < 0.65 → HAND_TAKEOFF, which is the desired routing
# so the estimator sees the row in the hand-takeoff queue and supplies
# a real LF.
_FEEDER_CONFIDENCE: Final[float] = 0.55

# CSI families used by panel synthesis. Tuples are (division, section,
# family-label-for-description), mirroring the shape used by the door
# / window / finish synthesisers.
_CSI_PANELBOARD:   Final[tuple[str, str, str]] = ("26", "26 24 16", "Panelboard")
_CSI_SWITCHBOARD:  Final[tuple[str, str, str]] = ("26", "26 24 13", "Switchboard")
_CSI_BREAKER:      Final[tuple[str, str, str]] = ("26", "26 28 16", "Branch Circuit Breaker")
_CSI_FEEDER_WIRE:  Final[tuple[str, str, str]] = ("26", "26 05 19", "Feeder Conductor")
_CSI_FEEDER_RACE:  Final[tuple[str, str, str]] = ("26", "26 05 33", "Feeder Raceway")


def _classify_panel_enclosure(panel: PanelRecord) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for a panel.

    Panelboard vs switchboard is decided by ``bus_amps`` when published,
    falling back to ``main_breaker_amps`` (MCB rating sets the panel
    class when bus_amps is absent), defaulting to panelboard otherwise.
    """
    rating = panel.bus_amps or panel.main_breaker_amps or 0
    if rating > _PANEL_BOARD_BUS_THRESHOLD_A:
        return _CSI_SWITCHBOARD
    return _CSI_PANELBOARD


def _panel_label(panel: PanelRecord) -> str:
    """Render a ``Panel <ID>`` label, fallback to ``Panel (unmarked)``."""
    pid = (panel.panel_id or "").strip()
    if not pid:
        return "Panel (unmarked)"
    return f"Panel {pid}"


def _describe_panel_enclosure(panel: PanelRecord, family: str) -> str:
    """Build a human-readable description for the panel-enclosure row.

    Examples::

        "Panel PNL-A — Panelboard 200A MCB, 120/208V 3-phase"
        "Panel MDP — Switchboard 800A MLO, 277/480V 3-phase"
        "Panel RP-1 — Panelboard"
    """
    parts: list[str] = [_panel_label(panel), "—", family]
    rating = panel.main_breaker_amps or panel.bus_amps
    designation = panel.mcb_or_mlo
    if rating and designation:
        parts.append(f"{rating}A {designation},")
    elif rating:
        parts.append(f"{rating}A,")
    elif designation:
        parts.append(f"{designation},")
    if panel.voltage:
        parts.append(panel.voltage)
    if panel.phase_count:
        parts.append(f"{panel.phase_count}-phase")
    rendered = " ".join(parts).rstrip(",")
    rendered = rendered.rstrip(",").rstrip()
    return rendered


def _describe_breaker_group(panel: PanelRecord, amps: int, count: int) -> str:
    """Build a description for a per-amp breaker group row."""
    return f"{_panel_label(panel)} — Branch breakers {amps}A ({count} ckt)"


def _describe_feeder_conductor(panel: PanelRecord) -> str:
    pid = panel.panel_id
    extra = ""
    if panel.feeder_conductor_size:
        extra = f" {panel.feeder_conductor_size}"
    return f"Panel {pid} — Feeder conductor{extra}"


def _describe_feeder_raceway(panel: PanelRecord) -> str:
    pid = panel.panel_id
    extra = ""
    if panel.feeder_conduit_size:
        extra = f" {panel.feeder_conduit_size}"
    return f"Panel {pid} — Feeder conduit{extra}"


def _panel_notes_for(panel: PanelRecord, *, role: str,
                       amps: int | None = None,
                       count: int | None = None) -> str:
    """Stable, source-tagged notes string for panel dedupe to grep.

    Format mirrors door + window + finish: ``key=value`` pairs joined
    by ``"; "``. The first pair is always
    ``source=panel_schedule_prepass`` so prefix-match is cheap. The
    ``role`` token disambiguates which of the four synthesis families
    the row belongs to (``enclosure`` / ``breakers`` / ``feeder_wire``
    / ``feeder_conduit``).
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_PANEL}"]
    if panel.panel_id:
        bits.append(f"mark={panel.panel_id}")
    bits.append(f"role={role}")
    if panel.voltage:
        bits.append(f"voltage={panel.voltage}")
    if panel.phase_count:
        bits.append(f"phase_count={panel.phase_count}")
    if panel.main_breaker_amps is not None:
        bits.append(f"main_breaker_amps={panel.main_breaker_amps}")
    if panel.bus_amps is not None:
        bits.append(f"bus_amps={panel.bus_amps}")
    if panel.mcb_or_mlo:
        bits.append(f"mcb_or_mlo={panel.mcb_or_mlo}")
    if amps is not None:
        bits.append(f"breaker_amps={amps}")
    if count is not None:
        bits.append(f"circuit_count={count}")
    if role == "feeder_wire" and panel.feeder_conductor_size:
        bits.append(f"feeder_conductor={panel.feeder_conductor_size}")
    if role == "feeder_conduit" and panel.feeder_conduit_size:
        bits.append(f"feeder_conduit={panel.feeder_conduit_size}")
    return "; ".join(bits)


def _branch_breaker_groups(panel: PanelRecord) -> list[tuple[int, int]]:
    """Group circuit entries by breaker amp size; return ``[(amps, count), ...]``.

    Stable order: ascending by amp size. Skips circuits without a
    breaker rating so the synthesiser doesn't fabricate a ``None``-A
    breaker group. Multi-pole breakers (phase ``A,B,C``) count as
    ONE breaker even though they consume 2 or 3 circuit numbers — the
    schedule typically lists one row per pole with the same amp rating,
    and the synthesiser counts the rows as-published rather than
    de-duplicating poles (the calibration data shows this matches the
    estimator's mental model better than collapsing).
    """
    counts: dict[int, int] = {}
    for c in panel.circuits:
        if c.breaker_amps is None:
            continue
        counts[c.breaker_amps] = counts.get(c.breaker_amps, 0) + 1
    return sorted(counts.items(), key=lambda kv: kv[0])


def synthesize_panel_takeoff_items(
    panels: list[PanelRecord] | PanelScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``PanelRecord`` into 1 + N + 2 ``TakeoffItem`` rows.

    Per-panel fan-out (the structural shape of T2.6 vs. T1 / T2.5 1:1):

    * One **panel enclosure** at 26 24 16 (or 26 24 13 if bus > 400A).
      Confidence = ``panel.confidence`` (typically 0.85+).
    * **N branch-breaker groups** at 26 28 16, one per distinct
      breaker amp size. Confidence = 0.85 (panel data is reliable).
      A panel with no circuits emits zero breaker rows.
    * One **feeder conductor** at 26 05 19, quantity = 50 LF (parametric
      default). Confidence = 0.55 → routes to HAND_TAKEOFF queue on
      Phase T6 banding so the estimator supplies a real LF.
    * One **feeder conduit** at 26 05 33, same 50 LF / 0.55 default.

    A panel with no usable ``panel_id`` is skipped entirely (defensive —
    the extractor already filters these). ``sheet_id`` (when provided)
    is stored on ``source_sheet_ids`` so downstream consumers can trace
    each row back to its sheet.
    """
    if panels is None:
        return []
    # Accept either the schema PanelScheduleResult OR a plain list per
    # the brief — the integration call site in core.takeoff uses the
    # PanelScheduleResult directly.
    if hasattr(panels, "panels"):
        panel_list: list[PanelRecord] = list(panels.panels)
    else:
        panel_list = list(panels)
    if not panel_list:
        return []

    items: list[TakeoffItem] = []
    for panel in panel_list:
        if not (panel.panel_id and panel.panel_id.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif panel.source_sheet:
            sheets.append(panel.source_sheet)

        # 1. Panel enclosure.
        division, section, family = _classify_panel_enclosure(panel)
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_panel_enclosure(panel, family),
            quantity=1.0,
            unit="EA",
            confidence=panel.confidence,
            source_sheet_ids=list(sheets),
            notes=_panel_notes_for(panel, role="enclosure"),
        ))

        # 2. Branch breakers grouped by amp size.
        for amps, count in _branch_breaker_groups(panel):
            items.append(TakeoffItem(
                csi_division=_CSI_BREAKER[0],
                csi_section=_CSI_BREAKER[1],
                description=_describe_breaker_group(panel, amps, count),
                quantity=float(count),
                unit="EA",
                # Phase T6.1 — branch breakers are SECONDARY items derived
                # from the parent panel record. Inherit the panel
                # confidence with the standard 5% per-derivation-step
                # haircut (floor 0.45). Pre-T6.1 this was a flat 0.85
                # regardless of the panel's confidence — see the
                # module-level "Phase T6.1" docstring for the rationale.
                confidence=inherit_with_haircut(panel.confidence),
                source_sheet_ids=list(sheets),
                notes=_panel_notes_for(
                    panel, role="breakers", amps=amps, count=count,
                ),
            ))

        # 3. Feeder conductor (parametric default).
        items.append(TakeoffItem(
            csi_division=_CSI_FEEDER_WIRE[0],
            csi_section=_CSI_FEEDER_WIRE[1],
            description=_describe_feeder_conductor(panel),
            quantity=_FEEDER_PARAMETRIC_LF,
            unit="LF",
            confidence=_FEEDER_CONFIDENCE,
            source_sheet_ids=list(sheets),
            notes=_panel_notes_for(panel, role="feeder_wire"),
        ))

        # 4. Feeder conduit (parametric default).
        items.append(TakeoffItem(
            csi_division=_CSI_FEEDER_RACE[0],
            csi_section=_CSI_FEEDER_RACE[1],
            description=_describe_feeder_raceway(panel),
            quantity=_FEEDER_PARAMETRIC_LF,
            unit="LF",
            confidence=_FEEDER_CONFIDENCE,
            source_sheet_ids=list(sheets),
            notes=_panel_notes_for(panel, role="feeder_conduit"),
        ))

    return items


# ---------------------------------------------------------------------------
# Lighting helpers (Phase T2.7)
# ---------------------------------------------------------------------------
#
# Lighting-fixture schedules fan each ``LightingFixtureRecord`` out
# into 1 or 2 families of ``TakeoffItem``:
#
# 1. **N EA fixture** — CSI 26 51 13 (Interior Lighting) for
#    recessed / surface / pendant / suspended mountings, OR 26 51 19
#    (Wall-Mounted Lighting) for wall-mounted fixtures. The CSI
#    boundary is the same one MasterFormat draws (interior-overhead
#    lighting vs wall-mounted sconces / cove / vanity); the
#    classification falls back to 26 51 13 when mounting is unknown.
# 2. **1 LS lamp/driver** — CSI 26 55 53 (lamps) for replaceable-
#    lamp fixtures (FLUORESCENT / HID). LED-integrated fixtures
#    have no separate lamp line; the driver is integral to the
#    fixture and is captured by the EA price. ``INCAN`` is treated
#    as replaceable too (a halogen / incandescent bulb is a
#    consumable).
#
# Quantity routing: the schedule rarely publishes a per-type count
# (the estimator walks the floor plan to count). When a QTY column
# IS present, the synthesised quantity uses it at high (0.90)
# confidence; when absent, the synthesiser emits ``quantity=1.0``
# at **0.55 confidence** so the row lands in the HAND_TAKEOFF queue
# (< 0.65 banding threshold) and the estimator can't miss it.
#
# Why the 0.55 vs 0.90 gap: 0.55 forces the row into HAND_TAKEOFF
# (the estimator MUST supply the real count); 0.90 is below
# AUTO_APPROVE (≥ 0.95 baseline) but well into OPERATOR_REVIEW so
# the row appears in the headline cost while remaining flagged. The
# 0.35 spread (vs the panel's 0.30 between 0.85 enclosure / 0.55
# feeder) is deliberately wider because lighting counts are MORE
# likely to be wrong than panel counts (panels are explicit on the
# schedule; fixtures aren't).


# CSI families used by lighting synthesis. Tuples are (division,
# section, family-label-for-description), mirroring the shape used
# by the door / window / finish / panel synthesisers.
_CSI_LIGHTING_INTERIOR: Final[tuple[str, str, str]] = (
    "26", "26 51 13", "Interior Lighting Fixture",
)
_CSI_LIGHTING_WALL:     Final[tuple[str, str, str]] = (
    "26", "26 51 19", "Wall-Mounted Lighting Fixture",
)
_CSI_LIGHTING_EXTERIOR: Final[tuple[str, str, str]] = (
    "26", "26 56 00", "Exterior Lighting Fixture",
)
_CSI_LIGHTING_LAMP:     Final[tuple[str, str, str]] = (
    "26", "26 55 53", "Replaceable Lamp / Ballast",
)

# Confidence assigned when the schedule DOES publish a QTY column.
# A QTY value is an explicit count, so we trust it on par with a
# clean door / window EA row.
_LIGHTING_QTY_CONFIDENCE: Final[float] = 0.90

# Confidence assigned when the schedule omits a QTY column and the
# synthesiser emits the default quantity=1.0. 0.55 lands the row in
# HAND_TAKEOFF (< 0.65 threshold) so the estimator walks the floor
# plan and supplies a real count.
_LIGHTING_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55

# Lamp-technology families whose fixture has a separately-priced
# replaceable lamp / driver. LED-integrated fixtures are NOT in
# this set — their driver is integral to the fixture and is captured
# by the EA price.
_REPLACEABLE_LAMP_TYPES: Final[frozenset[str]] = frozenset({
    "FLUORESCENT", "HID", "INCAN",
})


def _classify_lighting_fixture(
    fixture: LightingFixtureRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one fixture.

    Mounting wins when present: WALL → ``26 51 19``; RECESSED /
    SURFACE / PENDANT / SUSPENDED → ``26 51 13``. When mounting is
    unknown the description is scanned for an EXTERIOR / OUTDOOR /
    SITE / POLE / LANDSCAPE hint that routes to ``26 56 00``;
    otherwise the default is the interior section (the dominant
    case on commercial bid sets).
    """
    if fixture.mounting and fixture.mounting.upper() == "WALL":
        return _CSI_LIGHTING_WALL
    # Exterior detection from description / notes — cheap heuristic.
    blob = " ".join(t for t in (fixture.description, fixture.notes) if t).upper()
    if blob:
        for kw in ("EXTERIOR", "OUTDOOR", "SITE LIGHT", "POLE",
                   "LANDSCAPE", "WALL PACK"):
            if kw in blob:
                # WALL PACK is technically wall-mounted; route it as
                # exterior since the cost basis is closer to site
                # lighting than to interior sconces.
                return _CSI_LIGHTING_EXTERIOR
    return _CSI_LIGHTING_INTERIOR


def _fixture_label(fixture: LightingFixtureRecord) -> str:
    """Render a ``Fixture <TAG>`` label, fallback to ``Fixture (unmarked)``."""
    tag = (fixture.fixture_tag or "").strip()
    if not tag:
        return "Fixture (unmarked)"
    return f"Fixture {tag}"


def _describe_lighting_fixture(fixture: LightingFixtureRecord,
                                  family: str) -> str:
    """Build a human-readable description for the fixture row.

    Examples::

        "Fixture A1 — 2x4 LED RECESSED TROFFER 4000K (Lithonia 2BLT4-40L-LP840) 277V"
        "Fixture B — Wall sconce LED 15W (Cooper LF-15W-30K)"
        "Fixture C — Interior Lighting Fixture"
    """
    head = _fixture_label(fixture)
    parts: list[str] = []
    desc = (fixture.description or "").strip()
    if desc:
        parts.append(desc)
    else:
        parts.append(family)
    mfr_bits: list[str] = []
    if fixture.manufacturer:
        mfr_bits.append(fixture.manufacturer.strip())
    if fixture.catalog_number:
        mfr_bits.append(fixture.catalog_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if fixture.wattage is not None:
        parts.append(f"{fixture.wattage:g}W")
    if fixture.voltage:
        parts.append(fixture.voltage)
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_lighting_lamp(fixture: LightingFixtureRecord) -> str:
    """Build a description for the per-fixture lamp/driver LS row."""
    head = _fixture_label(fixture)
    lamp = (fixture.lamp_type or "lamp").lower()
    return f"{head} — {lamp} lamp/driver replacement allowance"


def _lighting_notes_for(fixture: LightingFixtureRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for lighting dedupe to grep.

    Format mirrors door + window + finish + panel: ``key=value``
    pairs joined by ``"; "``. The first pair is always
    ``source=lighting_schedule_prepass`` so a prefix-match is cheap.
    The ``role`` token disambiguates which family the row belongs to
    (``fixture`` / ``lamp``).
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_LIGHTING}"]
    if fixture.fixture_tag:
        bits.append(f"mark={fixture.fixture_tag}")
    bits.append(f"role={role}")
    if fixture.manufacturer:
        bits.append(f"manufacturer={fixture.manufacturer}")
    if fixture.catalog_number:
        bits.append(f"catalog={fixture.catalog_number}")
    if fixture.wattage is not None:
        bits.append(f"wattage={fixture.wattage:g}")
    if fixture.lumens is not None:
        bits.append(f"lumens={fixture.lumens}")
    if fixture.color_temp_k is not None:
        bits.append(f"color_temp_k={fixture.color_temp_k}")
    if fixture.voltage:
        bits.append(f"voltage={fixture.voltage}")
    if fixture.lamp_type:
        bits.append(f"lamp_type={fixture.lamp_type}")
    if fixture.mounting:
        bits.append(f"mounting={fixture.mounting}")
    if fixture.dimmable:
        bits.append("dimmable=true")
    if fixture.emergency:
        bits.append("emergency=true")
    if fixture.quantity is not None:
        bits.append(f"qty_from_schedule={fixture.quantity}")
    return "; ".join(bits)


def synthesize_lighting_takeoff_items(
    fixtures: list[LightingFixtureRecord] | LightingScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``LightingFixtureRecord`` into 1-2 ``TakeoffItem`` rows.

    Per-fixture fan-out (the structural shape of T2.7 vs. T2.6):

    * One **fixture** at ``26 51 13`` (interior) or ``26 51 19``
      (wall-mounted), unit ``EA``. Quantity = ``fixture.quantity``
      when the schedule published a QTY column (confidence ``0.90``);
      otherwise quantity ``1.0`` (confidence ``0.55`` → routes to
      HAND_TAKEOFF queue).
    * One **lamp / driver** at ``26 55 53``, unit ``LS``, ONLY for
      lamp technologies that have a replaceable lamp (FLUORESCENT /
      HID / INCAN). LED-integrated fixtures emit only the fixture
      row.  Confidence inherits from the fixture record.

    A fixture with no usable ``fixture_tag`` is skipped entirely
    (defensive — the extractor already filters these).  ``sheet_id``
    (when provided) is stored on ``source_sheet_ids`` so downstream
    consumers can trace each row back to its sheet.
    """
    if fixtures is None:
        return []
    # Accept either the schema LightingScheduleResult OR a plain list
    # — the integration call site in core.takeoff uses the schedule
    # directly the same way the panel synthesiser does.
    if hasattr(fixtures, "fixtures"):
        fixture_list: list[LightingFixtureRecord] = list(fixtures.fixtures)
    else:
        fixture_list = list(fixtures)
    if not fixture_list:
        return []

    items: list[TakeoffItem] = []
    for fixture in fixture_list:
        if not (fixture.fixture_tag and fixture.fixture_tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif fixture.source_sheet:
            sheets.append(fixture.source_sheet)

        # 1. Fixture row.
        division, section, family = _classify_lighting_fixture(fixture)
        if fixture.quantity is not None and fixture.quantity > 0:
            qty = float(fixture.quantity)
            fixture_confidence = _LIGHTING_QTY_CONFIDENCE
        else:
            qty = 1.0
            fixture_confidence = _LIGHTING_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_lighting_fixture(fixture, family),
            quantity=qty,
            unit="EA",
            confidence=fixture_confidence,
            source_sheet_ids=list(sheets),
            notes=_lighting_notes_for(fixture, role="fixture"),
        ))

        # 2. Lamp / driver — only for replaceable-lamp technologies.
        lamp_type = (fixture.lamp_type or "").upper()
        if lamp_type in _REPLACEABLE_LAMP_TYPES:
            items.append(TakeoffItem(
                csi_division=_CSI_LIGHTING_LAMP[0],
                csi_section=_CSI_LIGHTING_LAMP[1],
                description=_describe_lighting_lamp(fixture),
                quantity=1.0,
                unit="LS",
                # Phase T6.1 — lamp/driver is a SECONDARY item derived
                # from the fixture EA row (1 LS lamp pack per fixture
                # type). Inherit the EA row's effective confidence
                # (which already accounts for QTY-published vs hand-
                # takeoff) with the standard 5% per-derivation-step
                # haircut. Pre-T6.1 used ``fixture.confidence`` (the
                # record-level schema default) regardless of whether
                # the EA row was at 0.90 (QTY published) or 0.55
                # (HAND_TAKEOFF) — the haircut now propagates the
                # per-row routing decision into the lamp row.
                confidence=inherit_with_haircut(fixture_confidence),
                source_sheet_ids=list(sheets),
                notes=_lighting_notes_for(fixture, role="lamp"),
            ))

    return items


# ---------------------------------------------------------------------------
# HVAC helpers (Phase T2.8)
# ---------------------------------------------------------------------------
#
# Mechanical / HVAC equipment schedules fan each ``HVACEquipmentRecord``
# out into 2-3 families of ``TakeoffItem``:
#
# 1. **N EA equipment** — CSI per equipment family (AHU → 23 73 13,
#    RTU → 23 74 13, VAV → 23 36 00, PUMP → 23 22 23, BOILER → 23 52
#    00, CHILLER → 23 64 23, FAN → 23 34 00, OTHER → 23 00 00). Quantity
#    = ``record.quantity`` when the schedule published a QTY column
#    (confidence ``0.90``); otherwise quantity ``1.0`` (confidence
#    ``0.55`` → routes to HAND_TAKEOFF queue).
# 2. **1 LS MEP rough-in** — CSI 23 05 00 (Common Work Results for
#    HVAC). Parametric default; confidence ``0.45`` (PARAMETRIC tier
#    on T7 banding, HAND_TAKEOFF on T6 banding) because the actual
#    rough-in scope depends on a plan walk.
# 3. **1 EA disconnect + flex** — CSI 26 28 16 (Enclosed Switches and
#    Circuit Breakers, on the electrical side because the disconnect
#    + flex live in Division 26 even when serving Division 23
#    equipment). Confidence ``0.70``. ONLY for motorized equipment
#    with a voltage feed: AHU / RTU / PUMP / CHILLER / FAN. VAV
#    (duct-fed, no motor) and BOILER (integrated disconnect on the
#    equipment itself) skip the disconnect row.
#
# Quantity routing mirrors the lighting synthesis (T2.7): QTY-present
# lands at 0.90 confidence; absent lands at 0.55 → HAND_TAKEOFF so
# the estimator supplies a real count. The 0.55 vs 0.90 gap is the
# same width as lighting — equipment counts are explicit on the
# schedule when published, and absent when not.


# CSI families used by HVAC synthesis. Tuples are (division, section,
# family-label-for-description), mirroring the shape used by the door
# / window / finish / panel / lighting synthesisers.
_CSI_HVAC_AHU:     Final[tuple[str, str, str]] = (
    "23", "23 73 13", "Indoor Air-Handling Unit",
)
_CSI_HVAC_RTU:     Final[tuple[str, str, str]] = (
    "23", "23 74 13", "Packaged Rooftop Unit",
)
_CSI_HVAC_VAV:     Final[tuple[str, str, str]] = (
    "23", "23 36 00", "Variable Air Volume Terminal",
)
_CSI_HVAC_PUMP:    Final[tuple[str, str, str]] = (
    "23", "23 22 23", "Steam / Hot-Water Circulation Pump",
)
_CSI_HVAC_BOILER:  Final[tuple[str, str, str]] = (
    "23", "23 52 00", "Heating Boiler",
)
_CSI_HVAC_CHILLER: Final[tuple[str, str, str]] = (
    "23", "23 64 23", "Scroll Water Chiller",
)
_CSI_HVAC_FAN:     Final[tuple[str, str, str]] = (
    "23", "23 34 00", "HVAC Fan",
)
_CSI_HVAC_OTHER:   Final[tuple[str, str, str]] = (
    "23", "23 00 00", "HVAC Equipment",
)
_CSI_HVAC_ROUGHIN: Final[tuple[str, str, str]] = (
    "23", "23 05 00", "HVAC Rough-In (Common Work Results)",
)
_CSI_HVAC_DISCONNECT: Final[tuple[str, str, str]] = (
    "26", "26 28 16", "Equipment Disconnect + Flex Connection",
)

# Equipment-type → (CSI division, CSI section, family-label) lookup.
# OTHER catches anything the type detector falls through on, plus any
# future equipment family without a dedicated CSI section.
_HVAC_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "AHU":     _CSI_HVAC_AHU,
    "RTU":     _CSI_HVAC_RTU,
    "VAV":     _CSI_HVAC_VAV,
    "PUMP":    _CSI_HVAC_PUMP,
    "BOILER":  _CSI_HVAC_BOILER,
    "CHILLER": _CSI_HVAC_CHILLER,
    "FAN":     _CSI_HVAC_FAN,
    "OTHER":   _CSI_HVAC_OTHER,
}

# Equipment types that get a disconnect + flex row when motorized with
# voltage. VAV (typically duct-fed, no separate motor disconnect) and
# BOILER (integrated disconnect on the cabinet) are intentionally
# excluded — matches the T2.8 brief and BPC's calibration field notes.
_HVAC_DISCONNECT_TYPES: Final[frozenset[str]] = frozenset({
    "AHU", "RTU", "PUMP", "CHILLER", "FAN",
})

# Confidence assigned when the schedule DOES publish a QTY column.
# Mirrors ``_LIGHTING_QTY_CONFIDENCE`` from the T2.7 synthesis.
_HVAC_QTY_CONFIDENCE: Final[float] = 0.90

# Confidence assigned when the schedule omits a QTY column and the
# synthesiser emits the default quantity=1.0. Mirrors
# ``_LIGHTING_HAND_TAKEOFF_CONFIDENCE`` from T2.7.
_HVAC_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55

# Confidence assigned to the parametric MEP rough-in row. 0.45 lands
# in the PARAMETRIC tier on T7 banding (< 0.50) and HAND_TAKEOFF on
# T6 banding (< 0.65) so the row appears in the hand-takeoff queue
# AND is flagged as parametric on the tier rollups.
_HVAC_ROUGHIN_CONFIDENCE: Final[float] = 0.45

# Confidence assigned to the disconnect + flex EA row. 0.70 lands in
# OPERATOR_REVIEW on T6 banding — disconnect is reliably-counted
# (1 per motorized equipment) but the operator should eyeball the
# spec (NEMA rating, fusible vs non-fusible) before pricing.
_HVAC_DISCONNECT_CONFIDENCE: Final[float] = 0.70


def _classify_hvac_equipment(
    equipment: HVACEquipmentRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one record.

    Routes via ``equipment.equipment_type`` (set by the extractor's
    tag-prefix detector); unknown types land on the generic
    ``23 00 00`` HVAC section.
    """
    etype = (equipment.equipment_type or "OTHER").upper()
    return _HVAC_CSI_BY_TYPE.get(etype, _CSI_HVAC_OTHER)


def _hvac_label(equipment: HVACEquipmentRecord) -> str:
    """Render a ``Equipment <TAG>`` label, fallback to ``Equipment (unmarked)``."""
    tag = (equipment.equipment_tag or "").strip()
    if not tag:
        return "Equipment (unmarked)"
    return f"Equipment {tag}"


def _describe_hvac_equipment(equipment: HVACEquipmentRecord,
                               family: str) -> str:
    """Build a human-readable description for the equipment row.

    Examples::

        "Equipment AHU-1 — Indoor Air-Handling Unit 2000 CFM 5 HP 480V/3φ"
        "Equipment B-1 — Heating Boiler 500 MBH (Aerco Benchmark 5.0LN) GAS"
        "Equipment VAV-3-1 — Variable Air Volume Terminal 400 CFM"
    """
    head = _hvac_label(equipment)
    parts: list[str] = []
    desc = (equipment.description or "").strip()
    if desc:
        parts.append(desc)
    else:
        parts.append(family)
    mfr_bits: list[str] = []
    if equipment.manufacturer:
        mfr_bits.append(equipment.manufacturer.strip())
    if equipment.model_number:
        mfr_bits.append(equipment.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if equipment.capacity_value is not None and equipment.capacity_unit:
        parts.append(f"{equipment.capacity_value:g} {equipment.capacity_unit}")
    if equipment.motor_hp is not None:
        parts.append(f"{equipment.motor_hp:g} HP")
    if equipment.voltage:
        parts.append(equipment.voltage)
    if equipment.fuel_type:
        parts.append(equipment.fuel_type)
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_hvac_roughin(equipment: HVACEquipmentRecord) -> str:
    """Build a description for the per-equipment MEP rough-in LS row."""
    return f"{_hvac_label(equipment)} — MEP rough-in (duct / pipe / power feed)"


def _describe_hvac_disconnect(equipment: HVACEquipmentRecord) -> str:
    """Build a description for the per-equipment disconnect + flex EA row."""
    extra = ""
    if equipment.voltage:
        extra = f" ({equipment.voltage})"
    return f"{_hvac_label(equipment)} — Disconnect + flexible connection{extra}"


def _hvac_notes_for(equipment: HVACEquipmentRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for HVAC dedupe to grep.

    Format mirrors door + window + finish + panel + lighting:
    ``key=value`` pairs joined by ``"; "``. The first pair is always
    ``source=hvac_schedule_prepass`` so a prefix-match is cheap. The
    ``role`` token disambiguates which family the row belongs to
    (``equipment`` / ``roughin`` / ``disconnect``).
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_HVAC}"]
    if equipment.equipment_tag:
        bits.append(f"mark={equipment.equipment_tag}")
    bits.append(f"role={role}")
    if equipment.equipment_type:
        bits.append(f"equipment_type={equipment.equipment_type}")
    if equipment.manufacturer:
        bits.append(f"manufacturer={equipment.manufacturer}")
    if equipment.model_number:
        bits.append(f"model={equipment.model_number}")
    if equipment.capacity_value is not None:
        bits.append(f"capacity={equipment.capacity_value:g}")
    if equipment.capacity_unit:
        bits.append(f"capacity_unit={equipment.capacity_unit}")
    if equipment.motor_hp is not None:
        bits.append(f"motor_hp={equipment.motor_hp:g}")
    if equipment.voltage:
        bits.append(f"voltage={equipment.voltage}")
    if equipment.phase_count is not None:
        bits.append(f"phase_count={equipment.phase_count}")
    if equipment.refrigerant:
        bits.append(f"refrigerant={equipment.refrigerant}")
    if equipment.fuel_type:
        bits.append(f"fuel_type={equipment.fuel_type}")
    if equipment.quantity is not None:
        bits.append(f"qty_from_schedule={equipment.quantity}")
    return "; ".join(bits)


def synthesize_hvac_takeoff_items(
    equipment: list[HVACEquipmentRecord] | HVACScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``HVACEquipmentRecord`` into 2-3 ``TakeoffItem`` rows.

    Per-equipment fan-out (the structural shape of T2.8 vs. T2.7):

    * One **equipment** row at the per-family CSI section
      (``23 73 13`` AHU / ``23 74 13`` RTU / ``23 36 00`` VAV /
      ``23 22 23`` PUMP / ``23 52 00`` BOILER / ``23 64 23`` CHILLER
      / ``23 34 00`` FAN / ``23 00 00`` OTHER), unit ``EA``.
      Quantity = ``record.quantity`` when the schedule published a
      QTY column (confidence ``0.90``); otherwise quantity ``1.0``
      (confidence ``0.55`` → HAND_TAKEOFF queue).
    * One **MEP rough-in** row at ``23 05 00``, unit ``LS``, quantity
      ``1.0``, confidence ``0.45``. ALWAYS emitted for every record.
      The parametric scope (duct / pipe / power feed) depends on a
      plan walk that the synthesiser can't perform.
    * One **disconnect + flex** row at ``26 28 16``, unit ``EA``,
      quantity ``1.0``, confidence ``0.70``. ONLY emitted for
      motorized equipment with a voltage feed (AHU / RTU / PUMP /
      CHILLER / FAN). VAV (duct-fed) and BOILER (integrated
      disconnect) skip this row.

    A record with no usable ``equipment_tag`` is skipped entirely
    (defensive — the extractor already filters these). ``sheet_id``
    (when provided) is stored on ``source_sheet_ids`` so downstream
    consumers can trace each row back to its sheet.
    """
    if equipment is None:
        return []
    if hasattr(equipment, "equipment"):
        equipment_list: list[HVACEquipmentRecord] = list(equipment.equipment)
    else:
        equipment_list = list(equipment)
    if not equipment_list:
        return []

    items: list[TakeoffItem] = []
    for record in equipment_list:
        if not (record.equipment_tag and record.equipment_tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Equipment row.
        division, section, family = _classify_hvac_equipment(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            equipment_confidence = _HVAC_QTY_CONFIDENCE
        else:
            qty = 1.0
            equipment_confidence = _HVAC_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_hvac_equipment(record, family),
            quantity=qty,
            unit="EA",
            confidence=equipment_confidence,
            source_sheet_ids=list(sheets),
            notes=_hvac_notes_for(record, role="equipment"),
        ))

        # 2. MEP rough-in (parametric, ALWAYS emitted).
        items.append(TakeoffItem(
            csi_division=_CSI_HVAC_ROUGHIN[0],
            csi_section=_CSI_HVAC_ROUGHIN[1],
            description=_describe_hvac_roughin(record),
            quantity=1.0,
            unit="LS",
            confidence=_HVAC_ROUGHIN_CONFIDENCE,
            source_sheet_ids=list(sheets),
            notes=_hvac_notes_for(record, role="roughin"),
        ))

        # 3. Disconnect + flex — motorized equipment with voltage only.
        etype = (record.equipment_type or "OTHER").upper()
        has_motor_or_voltage = (
            record.motor_hp is not None or bool(record.voltage)
        )
        if has_motor_or_voltage and etype in _HVAC_DISCONNECT_TYPES:
            items.append(TakeoffItem(
                csi_division=_CSI_HVAC_DISCONNECT[0],
                csi_section=_CSI_HVAC_DISCONNECT[1],
                description=_describe_hvac_disconnect(record),
                quantity=1.0,
                unit="EA",
                # Phase T6.1 — disconnect+flex is a SECONDARY item
                # derived from the parent equipment row (1 EA per
                # motorised piece of equipment). Inherit the equipment
                # row's QTY-aware confidence with the standard 5%
                # per-derivation-step haircut. Pre-T6.1 this was a
                # flat 0.70 (``_HVAC_DISCONNECT_CONFIDENCE``)
                # regardless of whether the equipment row was at
                # 0.90 (QTY published) or 0.55 (HAND_TAKEOFF) — see
                # the module-level "Phase T6.1" docstring section.
                confidence=inherit_with_haircut(equipment_confidence),
                source_sheet_ids=list(sheets),
                notes=_hvac_notes_for(record, role="disconnect"),
            ))

    return items

# ---------------------------------------------------------------------------
# Phase T2.9 — Plumbing
# ---------------------------------------------------------------------------
#
# Plumbing fixture schedules fan each ``PlumbingFixtureRecord`` out
# into 2-3 families of ``TakeoffItem``:
#
# 1. **N EA fixture** — CSI per fixture family (WATER_CLOSET →
#    ``22 41 13``, LAVATORY → ``22 41 16``, URINAL → ``22 41 13``
#    (shares MasterFormat section with WCs), SHOWER → ``22 41 23``,
#    EWC / drinking fountain → ``22 47 13``, MOP_SINK / SINK →
#    ``22 41 19``, WATER_HEATER → ``22 33 00``, HOSE_BIBB →
#    ``22 11 23``, FLOOR_DRAIN → ``22 13 19``, OTHER → ``22 00 00``).
#    Quantity = ``record.quantity`` when the schedule published a
#    QTY column (confidence ``0.90``); otherwise quantity ``1.0``
#    (confidence ``0.55`` → routes to HAND_TAKEOFF queue).
# 2. **1 LS MEP rough-in** — CSI ``22 11 16`` (Domestic Water Piping)
#    for water-supply-dominant fixtures (LAV / SHOWER / EWC / SINK /
#    MOP_SINK / WATER_HEATER / HOSE_BIBB / OTHER), OR ``22 13 16``
#    (Sanitary Waste and Vent Piping) for waste-dominant fixtures
#    (WC / URINAL / FLOOR_DRAIN).  The split is documented inline so
#    a future maintainer can lift the mapping.  Confidence ``0.45``
#    (PARAMETRIC tier on T7 banding, HAND_TAKEOFF on T6 banding).
# 3. **1 LS trim / installation hardware** — same CSI section as the
#    fixture itself, confidence ``0.70``.  ONLY emitted when BOTH
#    ``manufacturer`` AND ``model_number`` are populated — the trim
#    package (faucets / stops / supplies / valves / drain assembly)
#    is mfr-specific and only meaningfully priceable once we know
#    which manufacturer-model combination was specified.
#
# Quantity routing mirrors the HVAC synthesis (T2.8): QTY-present
# lands at 0.90 confidence; absent lands at 0.55 → HAND_TAKEOFF so
# the estimator supplies a real count from the floor plan.
#
# Rough-in CSI rationale (BPC calibration):
# * Water-supply-dominant: the supply rough-in (hot / cold stops,
#   supplies, connection to building domestic water) is the
#   dominant scope on the unit.
# * Waste-dominant: WCs / urinals carry large-diameter (3" / 4")
#   waste laterals + carrier assemblies that dwarf the 1/2"
#   supply; FDs are waste-only by construction.
# * HOSE_BIBB / WATER_HEATER carry no waste line at all → 22 11 16
#   is the correct call.


# CSI families used by plumbing synthesis. Tuples are (division,
# section, family-label-for-description), mirroring the shape used
# by the door / window / finish / panel / lighting / HVAC synthesisers.
_CSI_PLUMB_WC:          Final[tuple[str, str, str]] = (
    "22", "22 41 13", "Water Closet",
)
_CSI_PLUMB_LAV:         Final[tuple[str, str, str]] = (
    "22", "22 41 16", "Lavatory",
)
_CSI_PLUMB_URINAL:      Final[tuple[str, str, str]] = (
    "22", "22 41 13", "Urinal",
)
_CSI_PLUMB_SHOWER:      Final[tuple[str, str, str]] = (
    "22", "22 41 23", "Shower",
)
_CSI_PLUMB_EWC:         Final[tuple[str, str, str]] = (
    "22", "22 47 13", "Electric Water Cooler / Drinking Fountain",
)
_CSI_PLUMB_MOP_SINK:    Final[tuple[str, str, str]] = (
    "22", "22 41 19", "Mop / Service Sink",
)
_CSI_PLUMB_SINK:        Final[tuple[str, str, str]] = (
    "22", "22 41 19", "Sink",
)
_CSI_PLUMB_WH:          Final[tuple[str, str, str]] = (
    "22", "22 33 00", "Domestic Water Heater",
)
_CSI_PLUMB_HOSE_BIBB:   Final[tuple[str, str, str]] = (
    "22", "22 11 23", "Hose Bibb / Hydrant",
)
_CSI_PLUMB_FLOOR_DRAIN: Final[tuple[str, str, str]] = (
    "22", "22 13 19", "Floor Drain",
)
_CSI_PLUMB_OTHER:       Final[tuple[str, str, str]] = (
    "22", "22 00 00", "Plumbing Fixture",
)
_CSI_PLUMB_ROUGHIN_SUPPLY: Final[tuple[str, str, str]] = (
    "22", "22 11 16", "Domestic Water Piping (rough-in)",
)
_CSI_PLUMB_ROUGHIN_WASTE:  Final[tuple[str, str, str]] = (
    "22", "22 13 16", "Sanitary Waste & Vent Piping (rough-in)",
)


# Fixture-type → (division, section, family-label) lookup.  OTHER
# catches anything the type detector falls through on, plus any
# future fixture family without a dedicated CSI section.
_PLUMB_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "WATER_CLOSET": _CSI_PLUMB_WC,
    "LAVATORY":     _CSI_PLUMB_LAV,
    "URINAL":       _CSI_PLUMB_URINAL,
    "SHOWER":       _CSI_PLUMB_SHOWER,
    "EWC":          _CSI_PLUMB_EWC,
    "MOP_SINK":     _CSI_PLUMB_MOP_SINK,
    "SINK":         _CSI_PLUMB_SINK,
    "WATER_HEATER": _CSI_PLUMB_WH,
    "HOSE_BIBB":    _CSI_PLUMB_HOSE_BIBB,
    "FLOOR_DRAIN":  _CSI_PLUMB_FLOOR_DRAIN,
    "OTHER":        _CSI_PLUMB_OTHER,
}


# Fixture types whose dominant rough-in is the WASTE line (large-
# diameter waste lateral + carrier on WCs / urinals; waste-only on
# floor drains).  Everything else routes to the SUPPLY rough-in.
_PLUMB_WASTE_DOMINANT_TYPES: Final[frozenset[str]] = frozenset({
    "WATER_CLOSET", "URINAL", "FLOOR_DRAIN",
})


# Confidence assigned when the schedule DOES publish a QTY column.
# Mirrors ``_HVAC_QTY_CONFIDENCE`` from the T2.8 synthesis.
_PLUMB_QTY_CONFIDENCE: Final[float] = 0.90

# Confidence assigned when the schedule omits a QTY column and the
# synthesiser emits the default quantity=1.0. Mirrors
# ``_HVAC_HAND_TAKEOFF_CONFIDENCE`` from T2.8.
_PLUMB_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55

# Confidence assigned to the parametric MEP rough-in row.  0.45 lands
# in the PARAMETRIC tier on T7 banding (< 0.50) and HAND_TAKEOFF on
# T6 banding (< 0.65) so the row appears in the hand-takeoff queue
# AND is flagged as parametric on the tier rollups.  Matches the
# HVAC rough-in confidence.
_PLUMB_ROUGHIN_CONFIDENCE: Final[float] = 0.45

# Confidence assigned to the trim / installation-hardware LS row.
# 0.70 lands in OPERATOR_REVIEW on T6 banding — trim is reliably-
# specified (mfr+model gates emission) but the operator should
# eyeball the trim package against the spec book before pricing.
_PLUMB_TRIM_CONFIDENCE: Final[float] = 0.70


def _classify_plumbing_fixture(
    fixture: PlumbingFixtureRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one record.

    Routes via ``fixture.fixture_type`` (set by the extractor's tag-
    prefix detector); unknown types land on the generic ``22 00 00``
    plumbing section.
    """
    ftype = (fixture.fixture_type or "OTHER").upper()
    return _PLUMB_CSI_BY_TYPE.get(ftype, _CSI_PLUMB_OTHER)


def _plumbing_label(fixture: PlumbingFixtureRecord) -> str:
    """Render a ``Plumbing fixture <TAG>`` label.

    The "Plumbing fixture" prefix (rather than just "Fixture") is
    deliberate — it disambiguates the description from lighting
    synthesis, which also produces "Fixture <TAG>" rows under CSI
    Division 26.  Belt-and-braces alongside the CSI-prefix scoping
    in :mod:`core.extraction.plumbing_dedupe`.
    """
    tag = (fixture.fixture_tag or "").strip()
    if not tag:
        return "Plumbing fixture (unmarked)"
    return f"Plumbing fixture {tag}"


def _describe_plumbing_fixture(fixture: PlumbingFixtureRecord,
                                  family: str) -> str:
    """Build a human-readable description for the fixture row.

    Examples::

        "Plumbing fixture WC-1 — Water Closet, Wall-hung, 1.28 GPF (American Standard 3461.001) WALL"
        "Plumbing fixture LAV-A — Lavatory (Kohler K-2210) 0.5 GPM COUNTER"
        "Plumbing fixture FD-1 — Floor Drain"
    """
    head = _plumbing_label(fixture)
    parts: list[str] = []
    desc = (fixture.description or "").strip()
    if desc:
        parts.append(desc)
    else:
        parts.append(family)
    mfr_bits: list[str] = []
    if fixture.manufacturer:
        mfr_bits.append(fixture.manufacturer.strip())
    if fixture.model_number:
        mfr_bits.append(fixture.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if fixture.flow_rate_value is not None and fixture.flow_rate_unit:
        parts.append(f"{fixture.flow_rate_value:g} {fixture.flow_rate_unit}")
    if fixture.mounting:
        parts.append(fixture.mounting.upper())
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_plumbing_roughin(fixture: PlumbingFixtureRecord,
                                  is_waste: bool) -> str:
    """Build a description for the per-fixture rough-in LS row."""
    label = "waste / vent rough-in" if is_waste else "water supply rough-in"
    return f"{_plumbing_label(fixture)} — {label}"


def _describe_plumbing_trim(fixture: PlumbingFixtureRecord) -> str:
    """Build a description for the per-fixture trim / hardware LS row."""
    return f"{_plumbing_label(fixture)} — trim / installation hardware"


def _plumbing_notes_for(fixture: PlumbingFixtureRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for plumbing dedupe to grep.

    Format mirrors door + window + finish + panel + lighting + HVAC:
    ``key=value`` pairs joined by ``"; "``.  The first pair is
    always ``source=plumbing_schedule_prepass`` so a prefix-match is
    cheap.  The ``role`` token disambiguates which family the row
    belongs to (``fixture`` / ``roughin`` / ``trim``).
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_PLUMBING}"]
    if fixture.fixture_tag:
        bits.append(f"mark={fixture.fixture_tag}")
    bits.append(f"role={role}")
    if fixture.fixture_type:
        bits.append(f"fixture_type={fixture.fixture_type}")
    if fixture.manufacturer:
        bits.append(f"manufacturer={fixture.manufacturer}")
    if fixture.model_number:
        bits.append(f"model={fixture.model_number}")
    if fixture.mounting:
        bits.append(f"mounting={fixture.mounting}")
    if fixture.flow_rate_value is not None:
        bits.append(f"flow_rate={fixture.flow_rate_value:g}")
    if fixture.flow_rate_unit:
        bits.append(f"flow_rate_unit={fixture.flow_rate_unit}")
    if fixture.cold_water_size:
        bits.append(f"cw={fixture.cold_water_size}")
    if fixture.hot_water_size:
        bits.append(f"hw={fixture.hot_water_size}")
    if fixture.waste_size:
        bits.append(f"waste={fixture.waste_size}")
    if fixture.vent_size:
        bits.append(f"vent={fixture.vent_size}")
    if fixture.ada_compliant:
        bits.append("ada=true")
    if fixture.sensor_operated:
        bits.append("sensor=true")
    if fixture.quantity is not None:
        bits.append(f"qty_from_schedule={fixture.quantity}")
    return "; ".join(bits)


def synthesize_plumbing_takeoff_items(
    fixtures: list[PlumbingFixtureRecord] | PlumbingScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``PlumbingFixtureRecord`` into 2-3 ``TakeoffItem`` rows.

    Per-fixture fan-out (the structural shape of T2.9 vs. T2.8):

    * One **fixture** row at the per-family CSI section (``22 41 13``
      WC / URINAL / ``22 41 16`` LAV / ``22 41 23`` SHOWER /
      ``22 47 13`` EWC / ``22 41 19`` MOP_SINK / SINK /
      ``22 33 00`` WATER_HEATER / ``22 11 23`` HOSE_BIBB /
      ``22 13 19`` FLOOR_DRAIN / ``22 00 00`` OTHER), unit ``EA``.
      Quantity = ``record.quantity`` when the schedule published a
      QTY column (confidence ``0.90``); otherwise quantity ``1.0``
      (confidence ``0.55`` → HAND_TAKEOFF queue).
    * One **MEP rough-in** row at ``22 11 16`` (water-supply-dominant
      fixtures) OR ``22 13 16`` (WC / URINAL / FLOOR_DRAIN — waste-
      dominant), unit ``LS``, quantity ``1.0``, confidence ``0.45``.
      ALWAYS emitted for every record (the actual rough-in scope
      depends on a plan walk that the synthesiser can't perform).
    * One **trim / installation hardware** row at the SAME fixture
      CSI section, unit ``LS``, quantity ``1.0``, confidence
      ``0.70``.  ONLY emitted when BOTH ``manufacturer`` AND
      ``model_number`` are populated — the trim package is mfr-
      specific and only meaningfully priceable once we know the
      manufacturer-model combination.

    A fixture with no usable ``fixture_tag`` is skipped entirely
    (defensive — the extractor already filters these).  ``sheet_id``
    (when provided) is stored on ``source_sheet_ids`` so downstream
    consumers can trace each row back to its sheet.
    """
    if fixtures is None:
        return []
    if hasattr(fixtures, "fixtures"):
        fixture_list: list[PlumbingFixtureRecord] = list(fixtures.fixtures)
    else:
        fixture_list = list(fixtures)
    if not fixture_list:
        return []

    items: list[TakeoffItem] = []
    for record in fixture_list:
        if not (record.fixture_tag and record.fixture_tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Fixture row.
        division, section, family = _classify_plumbing_fixture(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            fixture_confidence = _PLUMB_QTY_CONFIDENCE
        else:
            qty = 1.0
            fixture_confidence = _PLUMB_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_plumbing_fixture(record, family),
            quantity=qty,
            unit="EA",
            confidence=fixture_confidence,
            source_sheet_ids=list(sheets),
            notes=_plumbing_notes_for(record, role="fixture"),
        ))

        # 2. MEP rough-in (parametric, ALWAYS emitted).
        ftype = (record.fixture_type or "OTHER").upper()
        is_waste = ftype in _PLUMB_WASTE_DOMINANT_TYPES
        roughin_csi = (
            _CSI_PLUMB_ROUGHIN_WASTE if is_waste else _CSI_PLUMB_ROUGHIN_SUPPLY
        )
        items.append(TakeoffItem(
            csi_division=roughin_csi[0],
            csi_section=roughin_csi[1],
            description=_describe_plumbing_roughin(record, is_waste),
            quantity=1.0,
            unit="LS",
            confidence=_PLUMB_ROUGHIN_CONFIDENCE,
            source_sheet_ids=list(sheets),
            notes=_plumbing_notes_for(record, role="roughin"),
        ))

        # 3. Trim / installation hardware — only when mfr AND model
        # are both populated (the trim package is mfr-specific).
        if record.manufacturer and record.model_number:
            items.append(TakeoffItem(
                csi_division=division,
                csi_section=section,
                description=_describe_plumbing_trim(record),
                quantity=1.0,
                unit="LS",
                confidence=_PLUMB_TRIM_CONFIDENCE,
                source_sheet_ids=list(sheets),
                notes=_plumbing_notes_for(record, role="trim"),
            ))

    return items


# ====== Phase T2.10 — Specialty (Kitchen + Lab) ======
#
# Specialty schedules close the typed-extraction long-tail.  Kitchen
# equipment (Division 11 — Equipment) and lab casework / fume hoods
# (Division 12 — Furnishings, with cross-routes to Division 11 lab
# safety + Division 22 eyewash) are the two slices that ship in
# Phase T2.10.  AV (Division 27) + Security (Division 28) are
# DEFERRED to Phase T2.11 — their scaffold schemas already exist on
# :mod:`core.schemas`, but no extractor / synthesiser / dedupe is
# wired yet.
#
# Per-record fan-out shape (same architecture as plumbing T2.9):
#
# 1. **N × EA primary item** — CSI per item family (kitchen routes
#    Cooking / Refrigeration / Dishwashing / Hood / Generic to
#    distinct subsections under ``11 40``; lab routes BASE/WALL/TALL
#    cabinets + LAB_BENCH to ``12 35 53.13``, FUME_HOOD to
#    ``11 53 13``, SAFETY_CABINET to ``11 53 43``, and EYEWASH_STATION
#    to ``22 45 19`` — yes, eyewashes are plumbing scope even when
#    they live on a lab casework schedule).  Quantity = ``record.
#    quantity`` when the schedule published a QTY column (confidence
#    ``0.90``); otherwise quantity ``1.0`` (confidence ``0.55`` →
#    HAND_TAKEOFF queue).  Matches the plumbing T2.9 / HVAC T2.8 /
#    lighting T2.7 routing.
# 2. **1 × LS MEP rough-in** — emitted only when the record carries
#    at least one utility flag (gas / electric / water / drain for
#    kitchen; gas / vacuum / water / electric for lab).  The rough-in
#    CSI is picked by a "dominant utility" rule:
#      * Kitchen HOOD / EXHAUST_FAN → ``23 31 13`` (HVAC ductwork
#        dominates — the exhaust duct is the cost driver, even though
#        the hood enclosure itself is foodservice equipment in
#        Division 11).
#      * Kitchen with water / drain / gas piping → ``22 11 16``
#        (water-side rough-in; gas piping rolls into this bucket per
#        the T2.10 brief which collapses gas into water-side).
#      * Kitchen with electric only (no piping) → ``26 27 26``
#        (equipment wiring devices).
#      * Lab with water / drain (or gas / vacuum piping) → ``22 11
#        16`` — lab plumbing rough-in mirrors kitchen plumbing rough-in.
#      * Lab with electric only → ``26 27 26``.
#    Confidence inherits the parent record's confidence with the T6.1
#    haircut so a 0.85 parent yields a 0.808 rough-in (floored at
#    0.45 — well above PARAMETRIC but routable to OPERATOR_REVIEW on
#    a fully-decorated record).
# 3. **1 × LS trim / installation hardware** — emitted only when
#    BOTH ``manufacturer`` AND ``model_number`` are populated AND the
#    item is NOT a fume hood.  Trim package is mfr-specific; the
#    fume-hood exception is documented per the T2.10 brief: lab fume
#    hoods always ship from the factory with integrated trim (sash,
#    light, cup sinks, service fittings, baffles) and a separate trim
#    line would double-count.  Confidence ``inherit_with_haircut ×
#    0.70`` — applies the T6.1 derivation haircut AND a fixed 0.70
#    trim multiplier so a 0.85-parent yields ``0.85 × 0.95 × 0.70 =
#    0.5653`` → routes to HAND_TAKEOFF for the operator to verify
#    the trim spec against the manufacturer cut sheet.


# ---------------------------------------------------------------------------
# Kitchen — CSI families
# ---------------------------------------------------------------------------
#
# Kitchen mapping (per the T2.10 brief):
#   RANGE / GRIDDLE / FRYER / OVEN       → 11 40 13.13 (Food Cooking)
#   REFRIGERATOR / FREEZER / WALK_IN /
#     ICE_MACHINE                         → 11 40 16.13 (Food Refrigeration)
#   DISHWASHER                            → 11 40 19.13 (Food Dishwashing)
#   MIXER / PREP_TABLE / SINK             → 11 40 13     (generic Foodservice)
#   HOOD / EXHAUST_FAN                    → 11 40 13.16 (Food Service Hoods)
#                                           — cross-listed in 23 38 13
#                                           Commercial Kitchen Hoods, but
#                                           Division 11 wins per spec
#                                           convention (the foodservice
#                                           contractor furnishes the hood;
#                                           the mechanical sub installs
#                                           the duct).
#   OTHER                                 → 11 40 00     (generic Foodservice)

_CSI_KITCHEN_COOKING:  Final[tuple[str, str, str]] = (
    "11", "11 40 13.13", "Food Cooking Equipment",
)
_CSI_KITCHEN_REFRIG:   Final[tuple[str, str, str]] = (
    "11", "11 40 16.13", "Food Refrigeration Equipment",
)
_CSI_KITCHEN_DISH:     Final[tuple[str, str, str]] = (
    "11", "11 40 19.13", "Food Dishwashing Equipment",
)
_CSI_KITCHEN_GENERIC:  Final[tuple[str, str, str]] = (
    "11", "11 40 13", "Food Service Equipment",
)
_CSI_KITCHEN_HOOD:     Final[tuple[str, str, str]] = (
    "11", "11 40 13.16", "Food Service Hood",
)
_CSI_KITCHEN_OTHER:    Final[tuple[str, str, str]] = (
    "11", "11 40 00", "Foodservice Equipment",
)

# Kitchen rough-in CSI families.
_CSI_KITCHEN_ROUGHIN_WATER: Final[tuple[str, str, str]] = (
    "22", "22 11 16", "Kitchen Water / Gas Piping Rough-In",
)
_CSI_KITCHEN_ROUGHIN_ELEC:  Final[tuple[str, str, str]] = (
    "26", "26 27 26", "Kitchen Equipment Wiring Rough-In",
)
_CSI_KITCHEN_ROUGHIN_DUCT:  Final[tuple[str, str, str]] = (
    "23", "23 31 13", "Kitchen Hood Exhaust Ductwork Rough-In",
)

_KITCHEN_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "RANGE":        _CSI_KITCHEN_COOKING,
    "GRIDDLE":      _CSI_KITCHEN_COOKING,
    "FRYER":        _CSI_KITCHEN_COOKING,
    "OVEN":         _CSI_KITCHEN_COOKING,
    "REFRIGERATOR": _CSI_KITCHEN_REFRIG,
    "FREEZER":      _CSI_KITCHEN_REFRIG,
    "WALK_IN":      _CSI_KITCHEN_REFRIG,
    "ICE_MACHINE":  _CSI_KITCHEN_REFRIG,
    "DISHWASHER":   _CSI_KITCHEN_DISH,
    "MIXER":        _CSI_KITCHEN_GENERIC,
    "PREP_TABLE":   _CSI_KITCHEN_GENERIC,
    "SINK":         _CSI_KITCHEN_GENERIC,
    "HOOD":         _CSI_KITCHEN_HOOD,
    "EXHAUST_FAN":  _CSI_KITCHEN_HOOD,
    "OTHER":        _CSI_KITCHEN_OTHER,
}

# Kitchen item types that ALWAYS skip the trim row regardless of
# whether mfr+model are populated.  Currently empty for kitchen —
# the fume-hood exception is lab-only.  Held as an explicit constant
# so a future maintainer can add (e.g.) WALK_IN exclusions without
# touching the main loop.
_KITCHEN_TRIM_EXCLUDED: Final[frozenset[str]] = frozenset()

_KITCHEN_QTY_CONFIDENCE: Final[float] = 0.90
_KITCHEN_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55
# Fixed multiplier applied AFTER the T6.1 derivation haircut on the
# trim row.  The 0.70 ratio matches the plumbing trim confidence
# (Phase T2.9) so trim rows across both specialty + plumbing
# stacks share a consistent banding outcome.
_SPECIALTY_TRIM_MULTIPLIER: Final[float] = 0.70


def _classify_kitchen_item(
    record: KitchenEquipmentRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one kitchen item.

    Routes via ``record.item_type`` (set by the extractor's tag-prefix
    detector); unknown types land on the generic ``11 40 00``
    foodservice section.
    """
    itype = (record.item_type or "OTHER").upper()
    return _KITCHEN_CSI_BY_TYPE.get(itype, _CSI_KITCHEN_OTHER)


def _kitchen_roughin_csi(
    record: KitchenEquipmentRecord,
) -> tuple[str, str, str] | None:
    """Pick the dominant-utility rough-in CSI; ``None`` when no utility flags.

    Dominance rules (per the T2.10 brief):
      1. HOOD / EXHAUST_FAN → ductwork (``23 31 13``) — the duct is
         the cost driver regardless of any electrical accessory on
         the hood itself.
      2. Any piped utility (water / drain / gas) → water-side
         (``22 11 16``).  Gas piping collapses into this bucket per
         the brief's three-way split — keeps the rough-in row count
         per record to one (vs. fanning out a separate gas-piping
         row that would double-bill on combined gas+water equipment).
      3. Electric only (no piping) → equipment wiring (``26 27 26``).
      4. No utility flags at all → ``None`` (skip the rough-in row).
    """
    itype = (record.item_type or "OTHER").upper()
    if itype in {"HOOD", "EXHAUST_FAN"}:
        return _CSI_KITCHEN_ROUGHIN_DUCT
    if (record.utility_water is True or record.utility_drain is True
            or record.utility_gas is True):
        return _CSI_KITCHEN_ROUGHIN_WATER
    if record.utility_electric is True:
        return _CSI_KITCHEN_ROUGHIN_ELEC
    return None


def _kitchen_label(record: KitchenEquipmentRecord) -> str:
    tag = (record.tag or "").strip()
    if not tag:
        return "Kitchen equipment (unmarked)"
    return f"Kitchen equipment {tag}"


def _describe_kitchen_item(record: KitchenEquipmentRecord,
                              family: str) -> str:
    """Build a human-readable description for the primary kitchen item row.

    Examples::

        "Kitchen equipment RANGE-1 — Food Cooking Equipment 60\" 6-burner (Vulcan VHP660) 120K BTU GAS"
        "Kitchen equipment WI-1 — Food Refrigeration Equipment 8' x 10' walk-in cooler"
        "Kitchen equipment HOOD-1 — Food Service Hood 10' island canopy"
    """
    head = _kitchen_label(record)
    parts: list[str] = []
    desc = (record.description or "").strip()
    parts.append(desc if desc else family)
    mfr_bits: list[str] = []
    if record.manufacturer:
        mfr_bits.append(record.manufacturer.strip())
    if record.model_number:
        mfr_bits.append(record.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if record.btu_rating is not None:
        parts.append(f"{record.btu_rating} BTU")
    if record.voltage:
        parts.append(record.voltage)
    if record.utility_gas is True:
        parts.append("GAS")
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_kitchen_roughin(record: KitchenEquipmentRecord,
                                 family: str) -> str:
    """Build a description for the per-item rough-in LS row."""
    return f"{_kitchen_label(record)} — {family}"


def _describe_kitchen_trim(record: KitchenEquipmentRecord) -> str:
    """Build a description for the per-item trim / hardware LS row."""
    return f"{_kitchen_label(record)} — trim / installation hardware"


def _kitchen_notes_for(record: KitchenEquipmentRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for kitchen dedupe to grep.

    Format mirrors door + plumbing + HVAC: ``key=value`` pairs joined
    by ``"; "``.  First pair is always
    ``source=kitchen_schedule_prepass`` so a prefix-match is cheap.
    ``role`` disambiguates ``equipment`` / ``roughin`` / ``trim``.
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_KITCHEN}"]
    if record.tag:
        bits.append(f"mark={record.tag}")
    bits.append(f"role={role}")
    if record.item_type:
        bits.append(f"item_type={record.item_type}")
    if record.manufacturer:
        bits.append(f"manufacturer={record.manufacturer}")
    if record.model_number:
        bits.append(f"model={record.model_number}")
    if record.btu_rating is not None:
        bits.append(f"btu={record.btu_rating}")
    if record.voltage:
        bits.append(f"voltage={record.voltage}")
    if record.utility_gas is True:
        bits.append("utility_gas=true")
    if record.utility_electric is True:
        bits.append("utility_electric=true")
    if record.utility_water is True:
        bits.append("utility_water=true")
    if record.utility_drain is True:
        bits.append("utility_drain=true")
    if record.quantity is not None:
        bits.append(f"qty_from_schedule={record.quantity}")
    return "; ".join(bits)


def synthesize_kitchen_takeoff_items(
    equipment: list[KitchenEquipmentRecord] | KitchenScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``KitchenEquipmentRecord`` into 1-3 ``TakeoffItem`` rows.

    Per-record fan-out (mirrors the T2.9 plumbing shape):

    * One **equipment** row at the per-family CSI section under
      Division 11 (``11 40 13.13`` cooking / ``11 40 16.13``
      refrigeration / ``11 40 19.13`` dishwashing / ``11 40 13.16``
      hood / ``11 40 13`` generic foodservice / ``11 40 00`` other),
      unit ``EA``.  Quantity = ``record.quantity`` when the schedule
      published a QTY column (confidence ``0.90``); otherwise
      quantity ``1.0`` (confidence ``0.55`` → HAND_TAKEOFF queue).
    * One **MEP rough-in** row, unit ``LS``, ONLY when at least one
      utility flag is True.  Dominant-utility rule picks the CSI:
      hood/exhaust → ``23 31 13`` (ductwork); piped (water/drain/gas)
      → ``22 11 16`` (water-side); electric-only → ``26 27 26``.
      Confidence inherits the equipment row's confidence with the
      T6.1 haircut.
    * One **trim / installation hardware** row at the SAME equipment
      CSI section, unit ``LS``, ONLY when BOTH ``manufacturer`` AND
      ``model_number`` are populated.  Confidence ``inherit_with_
      haircut × 0.70`` so the trim row's banding tracks the parent's.

    A record with no usable ``tag`` is skipped entirely (defensive —
    the extractor already filters these).  ``sheet_id`` (when
    provided) is stored on ``source_sheet_ids`` so downstream
    consumers can trace each row back to its sheet.
    """
    if equipment is None:
        return []
    if hasattr(equipment, "equipment"):
        record_list: list[KitchenEquipmentRecord] = list(equipment.equipment)
    else:
        record_list = list(equipment)
    if not record_list:
        return []

    items: list[TakeoffItem] = []
    for record in record_list:
        if not (record.tag and record.tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Equipment row.
        division, section, family = _classify_kitchen_item(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            equipment_confidence = _KITCHEN_QTY_CONFIDENCE
        else:
            qty = 1.0
            equipment_confidence = _KITCHEN_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_kitchen_item(record, family),
            quantity=qty,
            unit="EA",
            confidence=equipment_confidence,
            source_sheet_ids=list(sheets),
            notes=_kitchen_notes_for(record, role="equipment"),
        ))

        # 2. MEP rough-in — only when at least one utility flag fires.
        roughin = _kitchen_roughin_csi(record)
        if roughin is not None:
            r_div, r_sec, r_fam = roughin
            items.append(TakeoffItem(
                csi_division=r_div,
                csi_section=r_sec,
                description=_describe_kitchen_roughin(record, r_fam),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(equipment_confidence),
                source_sheet_ids=list(sheets),
                notes=_kitchen_notes_for(record, role="roughin"),
            ))

        # 3. Trim / installation hardware — mfr+model gated; honour
        # the per-type exclusion set (currently empty for kitchen).
        itype = (record.item_type or "OTHER").upper()
        if (record.manufacturer and record.model_number
                and itype not in _KITCHEN_TRIM_EXCLUDED):
            items.append(TakeoffItem(
                csi_division=division,
                csi_section=section,
                description=_describe_kitchen_trim(record),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(
                    equipment_confidence,
                    multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                                  * _SPECIALTY_TRIM_MULTIPLIER,
                ),
                source_sheet_ids=list(sheets),
                notes=_kitchen_notes_for(record, role="trim"),
            ))

    return items


# ---------------------------------------------------------------------------
# Lab — CSI families
# ---------------------------------------------------------------------------
#
# Lab mapping (per the T2.10 brief):
#   BASE_CABINET / WALL_CABINET /
#     TALL_CABINET / LAB_BENCH         → 12 35 53.13 (Lab Bench Casework)
#   FUME_HOOD                          → 11 53 13    (Lab Fume Hoods)
#   SAFETY_CABINET                     → 11 53 43    (Lab Safety Equipment)
#   EYEWASH_STATION                    → 22 45 19    (Eyewash Equipment) —
#                                        cross-Division route!  Eyewashes
#                                        live on the lab casework schedule
#                                        but are a plumbing scope item.
#                                        Keeping them on Division 12 would
#                                        misroute the cost and break the
#                                        plumber's bid-package roll-up.
#   OTHER                              → 12 35 53    (generic Lab Casework)

_CSI_LAB_CASEWORK:    Final[tuple[str, str, str]] = (
    "12", "12 35 53.13", "Laboratory Bench Casework",
)
_CSI_LAB_GENERIC:     Final[tuple[str, str, str]] = (
    "12", "12 35 53", "Laboratory Casework",
)
_CSI_LAB_FUME_HOOD:   Final[tuple[str, str, str]] = (
    "11", "11 53 13", "Laboratory Fume Hood",
)
_CSI_LAB_SAFETY:      Final[tuple[str, str, str]] = (
    "11", "11 53 43", "Laboratory Safety Equipment",
)
_CSI_LAB_EYEWASH:     Final[tuple[str, str, str]] = (
    "22", "22 45 19", "Eyewash Equipment",
)

# Lab rough-in CSI families.
_CSI_LAB_ROUGHIN_WATER: Final[tuple[str, str, str]] = (
    "22", "22 11 16", "Lab Water / Gas / Vacuum Piping Rough-In",
)
_CSI_LAB_ROUGHIN_ELEC:  Final[tuple[str, str, str]] = (
    "26", "26 27 26", "Lab Equipment Wiring Rough-In",
)

_LAB_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "BASE_CABINET":     _CSI_LAB_CASEWORK,
    "WALL_CABINET":     _CSI_LAB_CASEWORK,
    "TALL_CABINET":     _CSI_LAB_CASEWORK,
    "LAB_BENCH":        _CSI_LAB_CASEWORK,
    "FUME_HOOD":        _CSI_LAB_FUME_HOOD,
    "SAFETY_CABINET":   _CSI_LAB_SAFETY,
    "EYEWASH_STATION":  _CSI_LAB_EYEWASH,
    "OTHER":            _CSI_LAB_GENERIC,
}

# Lab item types that ALWAYS skip the trim row.  FUME_HOOD is the
# documented exception per the T2.10 brief: factory-supplied fume
# hoods ship with integrated trim (sash + light + service fittings
# + cup sinks + baffles), and a separate trim line would double-
# count.  EYEWASH_STATION is also excluded because the eyewash trim
# is captured by the plumbing connection (the eyewash IS the trim,
# essentially — there's no separate finish carpentry layer).
_LAB_TRIM_EXCLUDED: Final[frozenset[str]] = frozenset({
    "FUME_HOOD", "EYEWASH_STATION",
})

_LAB_QTY_CONFIDENCE: Final[float] = 0.90
_LAB_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55


def _classify_lab_item(
    record: LabCaseworkRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one lab item.

    Routes via ``record.item_type`` (set by the extractor's tag-prefix
    detector); unknown types land on the generic ``12 35 53`` lab
    casework section.
    """
    itype = (record.item_type or "OTHER").upper()
    return _LAB_CSI_BY_TYPE.get(itype, _CSI_LAB_GENERIC)


def _lab_roughin_csi(
    record: LabCaseworkRecord,
) -> tuple[str, str, str] | None:
    """Pick the dominant-utility rough-in CSI; ``None`` when no utility flags.

    Dominance rules (per the T2.10 brief):
      1. Any piped utility (water / gas / vacuum) → water-side
         (``22 11 16``).  Gas + vacuum collapse into the same bucket
         as water+drain — they all need a piped service rough-in from
         the lab plumber.
      2. Electric only (no piping) → equipment wiring (``26 27 26``).
      3. No utility flags at all → ``None`` (skip the rough-in row).

    Note that ``EYEWASH_STATION`` always carries water — even when
    the extractor didn't fire the water flag on the schedule, the
    primary item CSI (``22 45 19``) already routes the cost to the
    plumber's scope, so a missing rough-in row is acceptable.
    """
    if (record.utility_water is True or record.utility_gas is True
            or record.utility_vacuum is True):
        return _CSI_LAB_ROUGHIN_WATER
    if record.utility_electric is True:
        return _CSI_LAB_ROUGHIN_ELEC
    return None


def _lab_label(record: LabCaseworkRecord) -> str:
    tag = (record.tag or "").strip()
    if not tag:
        return "Lab casework (unmarked)"
    return f"Lab casework {tag}"


def _describe_lab_item(record: LabCaseworkRecord, family: str) -> str:
    """Build a human-readable description for the primary lab item row.

    Examples::

        "Lab casework BC-1 — Laboratory Bench Casework 36\" x 22\" base cabinet EPOXY"
        "Lab casework FH-1 — Laboratory Fume Hood 6' bench-top (Labconco 1166000) GAS VACUUM"
        "Lab casework EW-1 — Eyewash Equipment wall-mount combination eyewash/drench"
    """
    head = _lab_label(record)
    parts: list[str] = []
    desc = (record.description or "").strip()
    parts.append(desc if desc else family)
    mfr_bits: list[str] = []
    if record.manufacturer:
        mfr_bits.append(record.manufacturer.strip())
    if record.model_number:
        mfr_bits.append(record.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if record.material:
        parts.append(record.material.upper())
    utility_bits: list[str] = []
    if record.utility_gas is True:
        utility_bits.append("GAS")
    if record.utility_vacuum is True:
        utility_bits.append("VACUUM")
    if record.utility_water is True:
        utility_bits.append("WATER")
    if utility_bits:
        parts.append(" ".join(utility_bits))
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_lab_roughin(record: LabCaseworkRecord, family: str) -> str:
    return f"{_lab_label(record)} — {family}"


def _describe_lab_trim(record: LabCaseworkRecord) -> str:
    return f"{_lab_label(record)} — trim / installation hardware"


def _lab_notes_for(record: LabCaseworkRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for lab dedupe to grep.

    First pair is always ``source=lab_schedule_prepass``; ``role``
    disambiguates ``casework`` / ``roughin`` / ``trim``.
    """
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_LAB}"]
    if record.tag:
        bits.append(f"mark={record.tag}")
    bits.append(f"role={role}")
    if record.item_type:
        bits.append(f"item_type={record.item_type}")
    if record.manufacturer:
        bits.append(f"manufacturer={record.manufacturer}")
    if record.model_number:
        bits.append(f"model={record.model_number}")
    if record.material:
        bits.append(f"material={record.material}")
    if record.utility_gas is True:
        bits.append("utility_gas=true")
    if record.utility_vacuum is True:
        bits.append("utility_vacuum=true")
    if record.utility_water is True:
        bits.append("utility_water=true")
    if record.utility_electric is True:
        bits.append("utility_electric=true")
    if record.quantity is not None:
        bits.append(f"qty_from_schedule={record.quantity}")
    return "; ".join(bits)


def synthesize_lab_takeoff_items(
    casework: list[LabCaseworkRecord] | LabScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``LabCaseworkRecord`` into 1-3 ``TakeoffItem`` rows.

    Per-record fan-out (mirrors the T2.10 kitchen shape):

    * One **primary** row at the per-family CSI section: BASE / WALL
      / TALL cabinets + LAB_BENCH route to ``12 35 53.13`` (Lab Bench
      Casework); FUME_HOOD → ``11 53 13`` (Lab Fume Hoods);
      SAFETY_CABINET → ``11 53 43`` (Lab Safety Equipment);
      EYEWASH_STATION → ``22 45 19`` (Eyewash, cross-Division to
      plumbing); OTHER → ``12 35 53`` (generic Lab Casework).  Unit
      ``EA``.  Quantity = ``record.quantity`` when the schedule
      published a QTY column (confidence ``0.90``); otherwise
      quantity ``1.0`` (confidence ``0.55`` → HAND_TAKEOFF queue).
    * One **MEP rough-in** row, unit ``LS``, ONLY when at least one
      utility flag is True.  Piped (water/gas/vacuum) → ``22 11 16``;
      electric-only → ``26 27 26``.  Confidence inherits the parent
      with the T6.1 haircut.
    * One **trim / installation hardware** row at the SAME primary
      CSI section, unit ``LS``, ONLY when BOTH ``manufacturer`` AND
      ``model_number`` are populated AND the item is NOT in
      :data:`_LAB_TRIM_EXCLUDED` (FUME_HOOD always ships with
      integrated trim; EYEWASH is itself the trim).  Confidence
      ``inherit_with_haircut × 0.70``.

    A record with no usable ``tag`` is skipped entirely.
    """
    if casework is None:
        return []
    if hasattr(casework, "casework"):
        record_list: list[LabCaseworkRecord] = list(casework.casework)
    else:
        record_list = list(casework)
    if not record_list:
        return []

    items: list[TakeoffItem] = []
    for record in record_list:
        if not (record.tag and record.tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Primary item row.
        division, section, family = _classify_lab_item(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            primary_confidence = _LAB_QTY_CONFIDENCE
        else:
            qty = 1.0
            primary_confidence = _LAB_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_lab_item(record, family),
            quantity=qty,
            unit="EA",
            confidence=primary_confidence,
            source_sheet_ids=list(sheets),
            notes=_lab_notes_for(record, role="casework"),
        ))

        # 2. MEP rough-in — only when at least one utility flag fires.
        roughin = _lab_roughin_csi(record)
        if roughin is not None:
            r_div, r_sec, r_fam = roughin
            items.append(TakeoffItem(
                csi_division=r_div,
                csi_section=r_sec,
                description=_describe_lab_roughin(record, r_fam),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(primary_confidence),
                source_sheet_ids=list(sheets),
                notes=_lab_notes_for(record, role="roughin"),
            ))

        # 3. Trim / installation hardware — mfr+model gated AND
        # item_type not in the per-family exclusion set.
        itype = (record.item_type or "OTHER").upper()
        if (record.manufacturer and record.model_number
                and itype not in _LAB_TRIM_EXCLUDED):
            items.append(TakeoffItem(
                csi_division=division,
                csi_section=section,
                description=_describe_lab_trim(record),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(
                    primary_confidence,
                    multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                                  * _SPECIALTY_TRIM_MULTIPLIER,
                ),
                source_sheet_ids=list(sheets),
                notes=_lab_notes_for(record, role="trim"),
            ))

    return items


# ====== Phase T2.11 — Specialty (AV + Security) ======
#
# Closes the T2.x typed-extraction family entirely.  AV equipment
# (Division 27 — Communications) and Security / access-control
# devices (Division 28 — Electronic Safety & Security) are the two
# specialty domains that ship in Phase T2.11.  Together with
# T2.10's kitchen + lab slices they close the long-tail of
# typed-schedule coverage.
#
# Per-record fan-out shape (mirrors the T2.10 kitchen+lab
# architecture):
#
# 1. **N × EA primary device** — CSI per item family.  AV routes
#    DISPLAY → 27 41 16.51, PROJECTOR → 27 41 16.31,
#    CAMERA (AV) → 27 41 16.49, MICROPHONE → 27 41 33.13,
#    SPEAKER → 27 41 33.16, RACK → 27 11 26, CONTROL_PROCESSOR
#    → 27 41 19.13, NETWORK_SWITCH → 27 21 33, OTHER → 27 41 16.
#    Security routes CARD_READER → 28 13 23.13, CAMERA →
#    28 23 23, MOTION_SENSOR → 28 16 13.13, DOOR_CONTACT →
#    28 16 16.13, KEYPAD → 28 13 23.16, REQUEST_TO_EXIT →
#    28 13 33.13, MAGLOCK → 28 13 43.13 (cross-list to 08 71 00
#    Door Hardware is OPTIONAL but we choose Div 28 since these
#    are on the security schedule and electrically driven),
#    OTHER → 28 13 00.  Quantity = ``record.quantity`` when the
#    schedule published a QTY column (confidence ``0.90``);
#    otherwise quantity ``1.0`` (confidence ``0.55`` →
#    HAND_TAKEOFF queue).
# 2. **1 × LS low-voltage cabling rough-in** — every powered AV
#    or security device needs structured low-voltage wiring
#    (Cat6 to switch, RS-485 to controller, PoE upstream).  AV
#    routes the cabling row to ``27 15 13.13`` (Communications
#    Copper Backbone Cabling); security routes to ``28 05 13``
#    (Conductors and Cables for Electronic Safety and Security).
#    Emitted for EVERY AV device (cabling is universal in AV)
#    and for security devices in {CARD_READER, CAMERA,
#    MOTION_SENSOR, KEYPAD, REQUEST_TO_EXIT, MAGLOCK}.  Confidence
#    inherits the parent's confidence with the T6.1 haircut.
# 3. **1 × LS installation / programming labor** — emitted only
#    for CONTROL_PROCESSOR, NETWORK_SWITCH, and any device whose
#    BOTH manufacturer + model are populated (these require
#    commissioning).  Confidence ``inherit_with_haircut × 0.70``
#    so the row tracks the parent's banding.
#
# **MAGLOCK CSI decision (Div 28 vs Div 8)**: Maglocks are an
# interesting cross-Division device — they are physically door
# hardware (Div 8, Section 08 71 00) but electrically a security
# / access-control component (Div 28, Section 28 13 43.13).  The
# brief recommends Div 28 since they live on the security
# schedule and the cost driver is the access-control sub, not the
# door hardware sub.  We follow that: MAGLOCK → 28 13 43.13.  A
# Div 8 cross-list would be visible to the door hardware dedupe
# (Phase T1) and could double-count if both extractors fire on
# the same row, so keeping the routing single-source-of-truth in
# Div 28 is also the safer dedupe posture.
#
# **NETWORK_SWITCH CSI decision (Div 27 vs Div 26)**: Network
# switches on an AV / T-series schedule are part of the
# communications / IT infrastructure (Div 27, Section 27 21 33
# Data Communications Network Equipment).  A panelboard or
# branch-circuit electrical schedule would route the switch to
# Div 26, but a switch listed on the AV schedule is being
# procured by the AV / IT integrator, not the electrical sub.
# We route to Div 27 to match the procurement reality and keep
# the AV bid package self-contained.


# ---------------------------------------------------------------------------
# AV — CSI families
# ---------------------------------------------------------------------------

_CSI_AV_DISPLAY:     Final[tuple[str, str, str]] = (
    "27", "27 41 16.51", "A-V Display Equipment",
)
_CSI_AV_PROJECTOR:   Final[tuple[str, str, str]] = (
    "27", "27 41 16.31", "A-V Projection Equipment",
)
_CSI_AV_CAMERA:      Final[tuple[str, str, str]] = (
    "27", "27 41 16.49", "A-V Capture Equipment",
)
_CSI_AV_MICROPHONE:  Final[tuple[str, str, str]] = (
    "27", "27 41 33.13", "Microphones",
)
_CSI_AV_SPEAKER:     Final[tuple[str, str, str]] = (
    "27", "27 41 33.16", "Loudspeakers",
)
_CSI_AV_RACK:        Final[tuple[str, str, str]] = (
    "27", "27 11 26", "Communications Racks",
)
_CSI_AV_CONTROL:     Final[tuple[str, str, str]] = (
    "27", "27 41 19.13", "A-V Control Equipment",
)
_CSI_AV_SWITCH:      Final[tuple[str, str, str]] = (
    "27", "27 21 33", "Data Communications Network Equipment",
)
_CSI_AV_OTHER:       Final[tuple[str, str, str]] = (
    "27", "27 41 16", "Integrated Audio-Video Systems",
)

# AV cabling rough-in CSI.
_CSI_AV_CABLING: Final[tuple[str, str, str]] = (
    "27", "27 15 13.13", "Communications Copper Backbone Cabling",
)

_AV_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "DISPLAY":           _CSI_AV_DISPLAY,
    "PROJECTOR":         _CSI_AV_PROJECTOR,
    "CAMERA":            _CSI_AV_CAMERA,
    "MICROPHONE":        _CSI_AV_MICROPHONE,
    "SPEAKER":           _CSI_AV_SPEAKER,
    "RACK":              _CSI_AV_RACK,
    "CONTROL_PROCESSOR": _CSI_AV_CONTROL,
    "NETWORK_SWITCH":    _CSI_AV_SWITCH,
    "OTHER":             _CSI_AV_OTHER,
}

# AV item types that ALWAYS get a programming / commissioning
# labor row regardless of mfr+model state.  These devices require
# integrator setup that flat-rate trim hardware doesn't cover.
_AV_PROGRAMMING_REQUIRED: Final[frozenset[str]] = frozenset({
    "CONTROL_PROCESSOR", "NETWORK_SWITCH",
})

_AV_QTY_CONFIDENCE: Final[float] = 0.90
_AV_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55
# Fixed multiplier applied AFTER the T6.1 derivation haircut on
# the programming/commissioning labor row.  Mirrors the kitchen+lab
# trim multiplier so banding is consistent.
_AV_PROGRAMMING_MULTIPLIER: Final[float] = 0.70
# Cabling rough-in inherits with the standard T6.1 haircut.  An
# additional 0.95 multiplier is applied on top so the cabling row
# never lands above the parent's effective confidence (it is
# strictly derived from the device's presence).
_AV_CABLING_MULTIPLIER: Final[float] = 0.95


def _classify_av_item(
    record: AVDeviceRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one AV item."""
    itype = (record.item_type or "OTHER").upper()
    return _AV_CSI_BY_TYPE.get(itype, _CSI_AV_OTHER)


def _av_label(record: AVDeviceRecord) -> str:
    tag = (record.tag or "").strip()
    if not tag:
        return "AV device (unmarked)"
    return f"AV device {tag}"


def _describe_av_item(record: AVDeviceRecord, family: str) -> str:
    """Build a human-readable description for the primary AV item row."""
    head = _av_label(record)
    parts: list[str] = []
    desc = (record.description or "").strip()
    parts.append(desc if desc else family)
    mfr_bits: list[str] = []
    if record.manufacturer:
        mfr_bits.append(record.manufacturer.strip())
    if record.model_number:
        mfr_bits.append(record.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if record.size_or_resolution:
        parts.append(record.size_or_resolution)
    if record.wattage is not None:
        parts.append(f"{record.wattage:g}W")
    if record.mounting:
        parts.append(record.mounting)
    if record.power:
        parts.append(record.power)
    if record.signal_type:
        parts.append(record.signal_type)
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_av_cabling(record: AVDeviceRecord, family: str) -> str:
    return f"{_av_label(record)} — {family}"


def _describe_av_programming(record: AVDeviceRecord) -> str:
    return f"{_av_label(record)} — programming / commissioning labor"


def _av_notes_for(record: AVDeviceRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for AV dedupe to grep."""
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_AV}"]
    if record.tag:
        bits.append(f"mark={record.tag}")
    bits.append(f"role={role}")
    if record.item_type:
        bits.append(f"item_type={record.item_type}")
    if record.manufacturer:
        bits.append(f"manufacturer={record.manufacturer}")
    if record.model_number:
        bits.append(f"model={record.model_number}")
    if record.size_or_resolution:
        bits.append(f"size_or_resolution={record.size_or_resolution}")
    if record.wattage is not None:
        bits.append(f"wattage={record.wattage}")
    if record.mounting:
        bits.append(f"mounting={record.mounting}")
    if record.power:
        bits.append(f"power={record.power}")
    if record.signal_type:
        bits.append(f"signal_type={record.signal_type}")
    if record.quantity is not None:
        bits.append(f"qty_from_schedule={record.quantity}")
    return "; ".join(bits)


def synthesize_av_takeoff_items(
    devices: list[AVDeviceRecord] | AVScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``AVDeviceRecord`` into 1-3 ``TakeoffItem`` rows.

    Per-record fan-out (mirrors the T2.10 kitchen / lab shape):

    * One **device** row at the per-family Division 27 CSI section
      (DISPLAY → 27 41 16.51, PROJECTOR → 27 41 16.31, CAMERA →
      27 41 16.49, MICROPHONE → 27 41 33.13, SPEAKER → 27 41
      33.16, RACK → 27 11 26, CONTROL_PROCESSOR → 27 41 19.13,
      NETWORK_SWITCH → 27 21 33, OTHER → 27 41 16), unit ``EA``.
      Quantity = ``record.quantity`` (confidence ``0.90``) when
      the schedule published a QTY column, else ``1.0`` (confidence
      ``0.55``).
    * One **low-voltage cabling rough-in** row at ``27 15 13.13``,
      unit ``LS``.  Emitted for every AV device (cabling is
      universal in AV).  Confidence inherits the device row's
      confidence with the T6.1 haircut.
    * One **programming / commissioning labor** row at the SAME
      device CSI section, unit ``LS``, emitted only for
      CONTROL_PROCESSOR / NETWORK_SWITCH OR any device with BOTH
      ``manufacturer`` AND ``model_number`` populated.  Confidence
      ``inherit_with_haircut × 0.70``.

    A record with no usable ``tag`` is skipped.  ``sheet_id``
    (when provided) is stored on ``source_sheet_ids`` so downstream
    consumers can trace each row back to its sheet.
    """
    if devices is None:
        return []
    if hasattr(devices, "devices"):
        record_list: list[AVDeviceRecord] = list(devices.devices)
    else:
        record_list = list(devices)
    if not record_list:
        return []

    items: list[TakeoffItem] = []
    for record in record_list:
        if not (record.tag and record.tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Device row.
        division, section, family = _classify_av_item(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            device_confidence = _AV_QTY_CONFIDENCE
        else:
            qty = 1.0
            device_confidence = _AV_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_av_item(record, family),
            quantity=qty,
            unit="EA",
            confidence=device_confidence,
            source_sheet_ids=list(sheets),
            notes=_av_notes_for(record, role="device"),
        ))

        # 2. Low-voltage cabling rough-in (universal for AV).
        c_div, c_sec, c_fam = _CSI_AV_CABLING
        items.append(TakeoffItem(
            csi_division=c_div,
            csi_section=c_sec,
            description=_describe_av_cabling(record, c_fam),
            quantity=1.0,
            unit="LS",
            confidence=inherit_with_haircut(
                device_confidence,
                multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                              * _AV_CABLING_MULTIPLIER,
            ),
            source_sheet_ids=list(sheets),
            notes=_av_notes_for(record, role="cabling"),
        ))

        # 3. Programming / commissioning labor row — gated.
        itype = (record.item_type or "OTHER").upper()
        needs_programming = (
            itype in _AV_PROGRAMMING_REQUIRED
            or (record.manufacturer and record.model_number)
        )
        if needs_programming:
            items.append(TakeoffItem(
                csi_division=division,
                csi_section=section,
                description=_describe_av_programming(record),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(
                    device_confidence,
                    multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                                  * _AV_PROGRAMMING_MULTIPLIER,
                ),
                source_sheet_ids=list(sheets),
                notes=_av_notes_for(record, role="programming"),
            ))

    return items


# ---------------------------------------------------------------------------
# Security — CSI families
# ---------------------------------------------------------------------------

_CSI_SEC_CARD_READER:  Final[tuple[str, str, str]] = (
    "28", "28 13 23.13", "Access Control Card Readers",
)
_CSI_SEC_CAMERA:       Final[tuple[str, str, str]] = (
    "28", "28 23 23", "Video Surveillance Cameras",
)
_CSI_SEC_MOTION:       Final[tuple[str, str, str]] = (
    "28", "28 16 13.13", "Passive Infrared Intrusion Detection",
)
_CSI_SEC_DOOR_CONTACT: Final[tuple[str, str, str]] = (
    "28", "28 16 16.13", "Door Position Switches",
)
_CSI_SEC_KEYPAD:       Final[tuple[str, str, str]] = (
    "28", "28 13 23.16", "Access Control Keypads",
)
_CSI_SEC_REX:          Final[tuple[str, str, str]] = (
    "28", "28 13 33.13", "Request-to-Exit Devices",
)
_CSI_SEC_MAGLOCK:      Final[tuple[str, str, str]] = (
    "28", "28 13 43.13", "Electromagnetic Locks",
)
_CSI_SEC_OTHER:        Final[tuple[str, str, str]] = (
    "28", "28 13 00", "Access Control",
)

# Security cabling rough-in CSI.
_CSI_SEC_CABLING: Final[tuple[str, str, str]] = (
    "28", "28 05 13",
    "Conductors and Cables for Electronic Safety and Security",
)

_SECURITY_CSI_BY_TYPE: Final[dict[str, tuple[str, str, str]]] = {
    "CARD_READER":     _CSI_SEC_CARD_READER,
    "CAMERA":          _CSI_SEC_CAMERA,
    "MOTION_SENSOR":   _CSI_SEC_MOTION,
    "DOOR_CONTACT":    _CSI_SEC_DOOR_CONTACT,
    "KEYPAD":          _CSI_SEC_KEYPAD,
    "REQUEST_TO_EXIT": _CSI_SEC_REX,
    "MAGLOCK":         _CSI_SEC_MAGLOCK,
    "OTHER":           _CSI_SEC_OTHER,
}

# Security item types that get a cabling rough-in row.  Per the
# T2.11 brief: CARD_READER, CAMERA, MOTION_SENSOR, KEYPAD,
# REQUEST_TO_EXIT, MAGLOCK.  DOOR_CONTACT is excluded — its wiring
# is part of the door frame and not a separate cabling pull.
_SECURITY_CABLING_TYPES: Final[frozenset[str]] = frozenset({
    "CARD_READER", "CAMERA", "MOTION_SENSOR",
    "KEYPAD", "REQUEST_TO_EXIT", "MAGLOCK",
})

# Security item types that ALWAYS get programming/commissioning
# labor.  Card readers and maglocks require panel-side enrollment
# and access-control programming.
_SECURITY_PROGRAMMING_REQUIRED: Final[frozenset[str]] = frozenset({
    "CARD_READER", "MAGLOCK",
})

_SECURITY_QTY_CONFIDENCE: Final[float] = 0.90
_SECURITY_HAND_TAKEOFF_CONFIDENCE: Final[float] = 0.55
_SECURITY_PROGRAMMING_MULTIPLIER: Final[float] = 0.70
_SECURITY_CABLING_MULTIPLIER: Final[float] = 0.95


def _classify_security_item(
    record: SecurityDeviceRecord,
) -> tuple[str, str, str]:
    """Return ``(csi_division, csi_section, family_label)`` for one security item."""
    itype = (record.item_type or "OTHER").upper()
    return _SECURITY_CSI_BY_TYPE.get(itype, _CSI_SEC_OTHER)


def _security_label(record: SecurityDeviceRecord) -> str:
    tag = (record.tag or "").strip()
    if not tag:
        return "Security device (unmarked)"
    return f"Security device {tag}"


def _describe_security_item(record: SecurityDeviceRecord,
                                family: str) -> str:
    """Build a human-readable description for the primary security row."""
    head = _security_label(record)
    parts: list[str] = []
    desc = (record.description or "").strip()
    parts.append(desc if desc else family)
    mfr_bits: list[str] = []
    if record.manufacturer:
        mfr_bits.append(record.manufacturer.strip())
    if record.model_number:
        mfr_bits.append(record.model_number.strip())
    if mfr_bits:
        parts.append(f"({' '.join(mfr_bits)})")
    if record.mounting:
        parts.append(record.mounting)
    if record.power:
        parts.append(record.power)
    if record.connection:
        parts.append(record.connection)
    return f"{head} — {' '.join(parts)}".rstrip()


def _describe_security_cabling(record: SecurityDeviceRecord,
                                   family: str) -> str:
    return f"{_security_label(record)} — {family}"


def _describe_security_programming(record: SecurityDeviceRecord) -> str:
    return f"{_security_label(record)} — programming / commissioning labor"


def _security_notes_for(record: SecurityDeviceRecord, *, role: str) -> str:
    """Stable, source-tagged notes string for security dedupe to grep."""
    bits: list[str] = [f"source={SYNTHESIS_SOURCE_TAG_SECURITY}"]
    if record.tag:
        bits.append(f"mark={record.tag}")
    bits.append(f"role={role}")
    if record.item_type:
        bits.append(f"item_type={record.item_type}")
    if record.manufacturer:
        bits.append(f"manufacturer={record.manufacturer}")
    if record.model_number:
        bits.append(f"model={record.model_number}")
    if record.mounting:
        bits.append(f"mounting={record.mounting}")
    if record.power:
        bits.append(f"power={record.power}")
    if record.connection:
        bits.append(f"connection={record.connection}")
    if record.quantity is not None:
        bits.append(f"qty_from_schedule={record.quantity}")
    return "; ".join(bits)


def synthesize_security_takeoff_items(
    devices: list[SecurityDeviceRecord] | SecurityScheduleResult | None,
    *,
    sheet_id: str | None = None,
) -> list[TakeoffItem]:
    """Convert each ``SecurityDeviceRecord`` into 1-3 ``TakeoffItem`` rows.

    Per-record fan-out (mirrors the T2.11 AV shape):

    * One **device** row at the per-family Division 28 CSI section
      (CARD_READER → 28 13 23.13, CAMERA → 28 23 23,
      MOTION_SENSOR → 28 16 13.13, DOOR_CONTACT → 28 16 16.13,
      KEYPAD → 28 13 23.16, REQUEST_TO_EXIT → 28 13 33.13,
      MAGLOCK → 28 13 43.13, OTHER → 28 13 00), unit ``EA``.
    * One **low-voltage cabling rough-in** row at ``28 05 13``,
      unit ``LS``.  Emitted for devices in
      :data:`_SECURITY_CABLING_TYPES` (DOOR_CONTACT excluded —
      its wiring lives inside the frame).  Confidence inherits
      the device row's confidence with the T6.1 haircut.
    * One **programming / commissioning labor** row at the SAME
      device CSI section, unit ``LS``, emitted only for
      CARD_READER / MAGLOCK OR any device with BOTH
      ``manufacturer`` AND ``model_number`` populated.  Confidence
      ``inherit_with_haircut × 0.70``.
    """
    if devices is None:
        return []
    if hasattr(devices, "devices"):
        record_list: list[SecurityDeviceRecord] = list(devices.devices)
    else:
        record_list = list(devices)
    if not record_list:
        return []

    items: list[TakeoffItem] = []
    for record in record_list:
        if not (record.tag and record.tag.strip()):
            continue
        sheets: list[str] = []
        if sheet_id:
            sheets.append(sheet_id)
        elif record.source_sheet:
            sheets.append(record.source_sheet)

        # 1. Device row.
        division, section, family = _classify_security_item(record)
        if record.quantity is not None and record.quantity > 0:
            qty = float(record.quantity)
            device_confidence = _SECURITY_QTY_CONFIDENCE
        else:
            qty = 1.0
            device_confidence = _SECURITY_HAND_TAKEOFF_CONFIDENCE
        items.append(TakeoffItem(
            csi_division=division,
            csi_section=section,
            description=_describe_security_item(record, family),
            quantity=qty,
            unit="EA",
            confidence=device_confidence,
            source_sheet_ids=list(sheets),
            notes=_security_notes_for(record, role="device"),
        ))

        # 2. Low-voltage cabling rough-in (gated by type).
        itype = (record.item_type or "OTHER").upper()
        if itype in _SECURITY_CABLING_TYPES:
            c_div, c_sec, c_fam = _CSI_SEC_CABLING
            items.append(TakeoffItem(
                csi_division=c_div,
                csi_section=c_sec,
                description=_describe_security_cabling(record, c_fam),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(
                    device_confidence,
                    multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                                  * _SECURITY_CABLING_MULTIPLIER,
                ),
                source_sheet_ids=list(sheets),
                notes=_security_notes_for(record, role="cabling"),
            ))

        # 3. Programming / commissioning labor row — gated.
        needs_programming = (
            itype in _SECURITY_PROGRAMMING_REQUIRED
            or (record.manufacturer and record.model_number)
        )
        if needs_programming:
            items.append(TakeoffItem(
                csi_division=division,
                csi_section=section,
                description=_describe_security_programming(record),
                quantity=1.0,
                unit="LS",
                confidence=inherit_with_haircut(
                    device_confidence,
                    multiplier=DERIVATION_HAIRCUT_MULTIPLIER
                                  * _SECURITY_PROGRAMMING_MULTIPLIER,
                ),
                source_sheet_ids=list(sheets),
                notes=_security_notes_for(record, role="programming"),
            ))

    return items
