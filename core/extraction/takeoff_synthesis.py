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
    DoorRecord,
    DoorScheduleResult,
    FinishRecord,
    FinishScheduleResult,
    HVACEquipmentRecord,
    HVACScheduleResult,
    LightingFixtureRecord,
    LightingScheduleResult,
    PanelRecord,
    PanelScheduleResult,
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
    "synthesize_door_takeoff_items",
    "synthesize_window_takeoff_items",
    "synthesize_finish_takeoff_items",
    "synthesize_panel_takeoff_items",
    "synthesize_lighting_takeoff_items",
    "synthesize_hvac_takeoff_items",
]


SYNTHESIS_SOURCE_TAG: Final[str] = "door_schedule_prepass"
SYNTHESIS_SOURCE_TAG_WINDOW: Final[str] = "window_schedule_prepass"
SYNTHESIS_SOURCE_TAG_FINISH: Final[str] = "finish_schedule_prepass"
SYNTHESIS_SOURCE_TAG_PANEL: Final[str] = "panel_schedule_prepass"
SYNTHESIS_SOURCE_TAG_LIGHTING: Final[str] = "lighting_schedule_prepass"
SYNTHESIS_SOURCE_TAG_HVAC: Final[str] = "hvac_schedule_prepass"


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
                confidence=0.85,
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
                confidence=fixture.confidence,
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
                confidence=_HVAC_DISCONNECT_CONFIDENCE,
                source_sheet_ids=list(sheets),
                notes=_hvac_notes_for(record, role="disconnect"),
            ))

    return items
