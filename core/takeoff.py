"""Reconcile per-sheet extractions into a single deduplicated takeoff list.

The same room can show up on the floor plan AND the finish schedule. The same
door type can be counted on the door schedule AND inferred from the plan. We
need one canonical row per real-world item.

Strategy:
  * Rooms     -- merge by (number, name) keeping the row with the most data.
  * Doors     -- merge by mark.
  * Windows   -- merge by mark.
  * Structural-- merge by (kind, mark, size).
  * MEP       -- merge by (discipline, category, normalized description).
  * Specs     -- merge by csi_section.
  * Site      -- take max of each numeric field across sheets.
  * Raw takeoffs (the priced quantity rows) are then DERIVED from the
    reconciled domain entities so we never double-count, plus any extractor-
    supplied raw_takeoffs that don't overlap with an entity-derived row.
"""

from __future__ import annotations

import logging
import re
from collections import defaultdict
from dataclasses import dataclass

from rapidfuzz import fuzz

from .extraction.door_dedupe import dedupe_doors_against_synthesis
from .extraction.finish_dedupe import dedupe_finishes_against_synthesis
from .extraction.hvac_dedupe import dedupe_hvac_against_synthesis
from .extraction.lighting_dedupe import dedupe_lighting_against_synthesis
from .extraction.panel_dedupe import dedupe_panels_against_synthesis
from .extraction.plumbing_dedupe import dedupe_plumbing_against_synthesis
from .extraction.room_schedule import merge_room_schedules
from .extraction.takeoff_backfill import backfill_finish_quantities
from .extraction.takeoff_synthesis import (
    synthesize_door_takeoff_items,
    synthesize_finish_takeoff_items,
    synthesize_hvac_takeoff_items,
    synthesize_lighting_takeoff_items,
    synthesize_panel_takeoff_items,
    synthesize_plumbing_takeoff_items,
    synthesize_window_takeoff_items,
)
from .extraction.window_dedupe import dedupe_windows_against_synthesis
from .schemas import (
    Alternate,
    BidPackage,
    Discipline,
    DoorEntry,
    MEPItem,
    Room,
    ScopeItem,
    SheetExtraction,
    SiteInfo,
    SpecSection,
    StructuralElement,
    TakeoffItem,
    WindowEntry,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Container for the reconciled project
# ---------------------------------------------------------------------------


@dataclass
class ProjectInfo:
    name: str | None = None
    number: str | None = None
    location: str | None = None
    owner: str | None = None
    contractor: str | None = None
    bid_due: str | None = None
    sources: list[str] | None = None    # which PDFs each value came from


@dataclass
class ScopeMatrix:
    """Aggregated view of all bid packages, organized for an estimator."""

    packages: list[BidPackage]                       # one row per trade
    by_division: dict[str, list[BidPackage]]         # CSI div -> packages that hit it
    all_alternates: list[Alternate]                  # deduped alternates
    coverage_warnings: list[str]                     # divisions with no bid package, etc.


@dataclass
class ProjectModel:
    rooms: list[Room]
    doors: list[DoorEntry]
    windows: list[WindowEntry]
    structural: list[StructuralElement]
    mep: list[MEPItem]
    spec_sections: list[SpecSection]
    site: SiteInfo
    takeoffs: list[TakeoffItem]
    sheet_summaries: dict[str, str]
    warnings: list[str]
    bid_packages: list[BidPackage]
    project_info: ProjectInfo
    scope_matrix: ScopeMatrix
    aggregated_inclusions: list[ScopeItem]
    aggregated_exclusions: list[ScopeItem]

    @property
    def trade_packages(self) -> list[BidPackage]:
        """Subset of `bid_packages` that describe a priceable scope of work.

        `bid_packages` is the canonical single source of truth (it holds both
        trade packages and supporting documents); this property gives
        consumers a fast filter so the Bid Packages export / UI never
        accidentally pulls in wage determinations or sample agreements.
        """
        return [p for p in self.bid_packages if p.document_kind == "trade_package"]

    @property
    def supporting_documents(self) -> list[BidPackage]:
        """Subset of `bid_packages` that are reference/compliance docs.

        Wage determinations, sample CSA templates, tax-exemption certificates,
        HSP form templates, UGSC / supplementary general conditions, etc.
        These apply across all trades and were previously polluting the
        Bid Packages export with `trade_name='other'`. The `bid_packages`
        list intentionally KEEPS them in (single source of truth); this
        property is the consumer-facing filter.
        """
        return [p for p in self.bid_packages if p.document_kind == "supporting_document"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_NORMALIZE_RE = re.compile(r"[^a-z0-9]+")


def _norm(s: str | None) -> str:
    if not s:
        return ""
    return _NORMALIZE_RE.sub(" ", s.lower()).strip()


def _merge_room(a: Room, b: Room) -> Room:
    """Return a Room with the best-of-both fields."""
    def pick(x, y):
        return x if (x is not None and x != "") else y

    merged_sources = ", ".join(
        sorted({s for s in [a.source_sheet_id, b.source_sheet_id] if s})
    )
    return Room(
        name=a.name or b.name,
        number=pick(a.number, b.number),
        area_sqft=pick(a.area_sqft, b.area_sqft),
        perimeter_ft=pick(a.perimeter_ft, b.perimeter_ft),
        ceiling_height_ft=pick(a.ceiling_height_ft, b.ceiling_height_ft),
        floor_finish=pick(a.floor_finish, b.floor_finish),
        base_finish=pick(a.base_finish, b.base_finish),
        wall_finish=pick(a.wall_finish, b.wall_finish),
        ceiling_finish=pick(a.ceiling_finish, b.ceiling_finish),
        notes=pick(a.notes, b.notes),
        source_sheet_id=merged_sources or a.source_sheet_id,
    )


def _dedupe_rooms(rooms: list[Room]) -> list[Room]:
    """Merge rooms by (number, name). Falls back to fuzzy name match."""
    out: list[Room] = []
    for r in rooms:
        match_idx = None
        for i, existing in enumerate(out):
            if r.number and existing.number and r.number == existing.number:
                match_idx = i
                break
            if not r.number and not existing.number and fuzz.token_set_ratio(_norm(r.name), _norm(existing.name)) >= 92:
                match_idx = i
                break
        if match_idx is None:
            out.append(r)
        else:
            out[match_idx] = _merge_room(out[match_idx], r)
    return out


def _dedupe_by_key(items: list, key_fn) -> list:
    seen: dict = {}
    for it in items:
        k = key_fn(it)
        if k in seen:
            existing = seen[k]
            # Prefer the one with the most populated fields.
            if sum(1 for v in it.model_dump().values() if v) > sum(
                1 for v in existing.model_dump().values() if v
            ):
                seen[k] = it
        else:
            seen[k] = it
    return list(seen.values())


# ---------------------------------------------------------------------------
# Domain -> takeoff conversion
# ---------------------------------------------------------------------------


def _avg_room_height(rooms: list[Room], default: float = 9.0) -> float:
    heights = [r.ceiling_height_ft for r in rooms if r.ceiling_height_ft]
    return round(sum(heights) / len(heights), 2) if heights else default


def _gross_area(rooms: list[Room]) -> float:
    return round(sum(r.area_sqft or 0.0 for r in rooms), 2)


def _wall_area(rooms: list[Room]) -> float:
    """Approximate paintable wall area: perimeter * height per room."""
    h = _avg_room_height(rooms)
    return round(sum((r.perimeter_ft or 0.0) * (r.ceiling_height_ft or h) for r in rooms), 2)


def _all_sheets_for(items: list, attr: str = "source_sheet_id") -> list[str]:
    seen: list[str] = []
    for it in items:
        sid = getattr(it, attr, None)
        if not sid:
            continue
        # Source might already be comma-joined from a prior merge.
        for piece in str(sid).split(","):
            piece = piece.strip()
            if piece and piece not in seen:
                seen.append(piece)
    return seen


def _derive_takeoffs(
    rooms: list[Room],
    doors: list[DoorEntry],
    windows: list[WindowEntry],
    structural: list[StructuralElement],
    mep: list[MEPItem],
    site: SiteInfo,
) -> list[TakeoffItem]:
    derived: list[TakeoffItem] = []
    room_sheets = _all_sheets_for(rooms)

    gross = _gross_area(rooms)
    walls = _wall_area(rooms)

    if gross > 0:
        derived.append(TakeoffItem(
            csi_division="03", csi_section="03 30 00",
            description="Slab on grade (assumes 4\")",
            quantity=gross, unit="SF", confidence=0.6,
            source_sheet_ids=room_sheets,
            notes="Derived from sum of room areas",
        ))
        derived.append(TakeoffItem(
            csi_division="06", csi_section="06 10 00",
            description="Wood / metal framing - rough carpentry",
            quantity=gross, unit="SF", confidence=0.55,
            source_sheet_ids=room_sheets,
            notes="Allowance based on building footprint",
        ))

    # Floor finishes by material
    finish_buckets: dict[tuple[str, str | None, str], list[Room]] = defaultdict(list)
    for r in rooms:
        if not r.area_sqft or not r.floor_finish:
            continue
        f = r.floor_finish.lower()
        if "carpet" in f:
            key = ("09", "09 68 13", "Carpet flooring")
        elif "lvt" in f or "vinyl" in f or "lvp" in f:
            key = ("09", "09 65 19", "Vinyl plank flooring (LVT)")
        elif "tile" in f or "porcelain" in f or "ceramic" in f:
            key = ("09", "09 30 00", "Tile flooring")
        elif "hardwood" in f or "wood" in f:
            key = ("09", "09 64 29", "Wood flooring")
        elif "polished" in f or "concrete" in f or "sealed" in f:
            key = ("03", "03 35 00", "Polished / sealed concrete floor")
        else:
            key = ("09", None, f"Other flooring ({r.floor_finish})")
        finish_buckets[key].append(r)

    for (div, sec, desc), rs in finish_buckets.items():
        qty = round(sum(r.area_sqft or 0 for r in rs), 2)
        derived.append(TakeoffItem(
            csi_division=div, csi_section=sec, description=desc,
            quantity=qty, unit="SF", confidence=0.75,
            source_sheet_ids=_all_sheets_for(rs),
        ))

    # Painted walls
    if walls > 0:
        derived.append(TakeoffItem(
            csi_division="09", csi_section="09 91 23",
            description="Interior wall painting (two coats)",
            quantity=walls, unit="SF", confidence=0.6,
            source_sheet_ids=room_sheets,
            notes="Derived from sum of room perimeter * ceiling height",
        ))
        derived.append(TakeoffItem(
            csi_division="09", csi_section="09 29 00",
            description="Gypsum board, 5/8\" - one face",
            quantity=walls, unit="SF", confidence=0.55,
            source_sheet_ids=room_sheets,
            notes="Approx; assumes one face of partition equals interior wall area",
        ))

    # Base
    if rooms:
        base_lf = round(sum(r.perimeter_ft or 0 for r in rooms), 2)
        if base_lf > 0:
            derived.append(TakeoffItem(
                csi_division="09", csi_section="09 65 13",
                description="Resilient base, 4\"",
                quantity=base_lf, unit="LF", confidence=0.6,
                source_sheet_ids=room_sheets,
            ))

    # Doors
    if doors:
        wood = sum(1 for d in doors if (d.type or "").lower().find("wood") != -1 or (d.type or "").lower().find("sc") != -1)
        metal = sum(1 for d in doors if (d.type or "").lower().find("hm") != -1 or (d.type or "").lower().find("hollow metal") != -1)
        other = len(doors) - wood - metal

        sheets = _all_sheets_for(doors)
        if wood:
            derived.append(TakeoffItem(
                csi_division="08", csi_section="08 14 16",
                description="Solid-core wood doors",
                quantity=float(wood), unit="EA", confidence=0.85,
                source_sheet_ids=sheets,
            ))
        if metal:
            derived.append(TakeoffItem(
                csi_division="08", csi_section="08 11 13",
                description="Hollow metal doors",
                quantity=float(metal), unit="EA", confidence=0.85,
                source_sheet_ids=sheets,
            ))
        if other:
            derived.append(TakeoffItem(
                csi_division="08", csi_section="08 14 16",
                description="Doors (type unspecified)",
                quantity=float(other), unit="EA", confidence=0.6,
                source_sheet_ids=sheets,
            ))
        derived.append(TakeoffItem(
            csi_division="08", csi_section="08 71 00",
            description="Door hardware sets",
            quantity=float(len(doors)), unit="EA", confidence=0.85,
            source_sheet_ids=sheets,
        ))

    # Windows
    if windows:
        derived.append(TakeoffItem(
            csi_division="08", csi_section="08 50 00",
            description="Windows",
            quantity=float(len(windows)), unit="EA", confidence=0.85,
            source_sheet_ids=_all_sheets_for(windows),
        ))

    # Structural
    for s in structural:
        if s.quantity <= 0:
            continue
        material = (s.material or "").lower()
        kind = s.kind.lower()
        if material == "steel":
            section = "05 12 00"; div = "05"
        elif material == "concrete" and "footing" in kind:
            section = "03 31 00"; div = "03"
        elif material == "concrete" and ("slab" in kind or "deck" in kind):
            section = "03 30 00"; div = "03"
        elif material == "masonry":
            section = "04 22 00"; div = "04"
        elif material == "wood":
            section = "06 10 00"; div = "06"
        else:
            section = None; div = "05"
        derived.append(TakeoffItem(
            csi_division=div, csi_section=section,
            description=f"Structural {s.kind} ({s.size or 'unspec'})",
            quantity=s.quantity, unit=s.unit, confidence=0.8,
            source_sheet_ids=[s.source_sheet_id] if s.source_sheet_id else [],
            notes=s.notes,
        ))

    # MEP
    for m in mep:
        if m.quantity <= 0:
            continue
        d = m.description.lower()
        cat = m.category.lower()
        if m.discipline == Discipline.PLUMBING or "fixture" in cat or any(k in d for k in ("toilet", "water closet", "lavatory", "sink", "urinal")):
            section = "22 40 00"; div = "22"
        elif m.discipline == Discipline.MECHANICAL or "rtu" in d or "hvac" in d:
            section = "23 00 00"; div = "23"
        elif m.discipline == Discipline.ELECTRICAL and ("light" in d or cat == "lighting"):
            section = "26 51 00"; div = "26"
        elif m.discipline == Discipline.ELECTRICAL and ("panel" in d or cat == "panel"):
            section = "26 24 16"; div = "26"
        elif m.discipline == Discipline.ELECTRICAL:
            section = "26 05 00"; div = "26"
        elif m.discipline == Discipline.FIRE_PROTECTION:
            section = "21 13 00"; div = "21"
        else:
            section = None; div = "23"

        derived.append(TakeoffItem(
            csi_division=div, csi_section=section,
            description=m.description,
            quantity=m.quantity, unit=m.unit, confidence=0.8,
            source_sheet_ids=[m.source_sheet_id] if m.source_sheet_id else [],
            notes=m.notes,
        ))

    # Site
    if site:
        sid = [site.source_sheet_id] if site.source_sheet_id else []
        if site.paving_area_sqft:
            derived.append(TakeoffItem(
                csi_division="32", csi_section="32 12 16",
                description="Asphalt paving",
                quantity=site.paving_area_sqft, unit="SF", confidence=0.75,
                source_sheet_ids=sid,
            ))
        if site.sidewalk_lf:
            derived.append(TakeoffItem(
                csi_division="32", csi_section="32 13 13",
                description="Concrete sidewalk",
                quantity=site.sidewalk_lf, unit="LF", confidence=0.75,
                source_sheet_ids=sid,
            ))
        if site.landscaping_area_sqft:
            derived.append(TakeoffItem(
                csi_division="32", csi_section="32 90 00",
                description="Landscaping",
                quantity=site.landscaping_area_sqft, unit="SF", confidence=0.65,
                source_sheet_ids=sid,
            ))

    return derived


def _merge_finish_schedules(results: list):
    """Concatenate per-sheet finish schedules into one for the T5 back-fill.

    The back-fill only consumes the rooms' ``ceiling_height_ft`` for
    its wall-area fallback when the room schedule didn't carry the
    column, so the merge is a simple concat. Returns ``None`` when the
    input is empty so the back-fill can skip the fallback lookup
    entirely.
    """
    if not results:
        return None
    from .schemas import FinishScheduleResult
    rooms = []
    pages: list[int] = []
    confidence = 0.0
    for r in results:
        if r is None:
            continue
        rooms.extend(r.rooms or [])
        for pg in (r.pages or []):
            if pg not in pages:
                pages.append(pg)
        confidence = max(confidence, float(r.confidence or 0.0))
    return FinishScheduleResult(
        pages=pages, rooms=rooms, confidence=round(confidence, 4),
    )


def _merge_door_schedules(results: list):
    """Concatenate per-sheet door schedules into one for the T5.1 follow-up."""
    if not results:
        return None
    from .schemas import DoorScheduleResult
    doors = []
    pages: list[int] = []
    confidence = 0.0
    for r in results:
        if r is None:
            continue
        doors.extend(r.doors or [])
        for pg in (r.pages or []):
            if pg not in pages:
                pages.append(pg)
        confidence = max(confidence, float(r.confidence or 0.0))
    return DoorScheduleResult(
        pages=pages, doors=doors, confidence=round(confidence, 4),
    )


def _merge_window_schedules(results: list):
    """Concatenate per-sheet window schedules into one for the T5.1 follow-up."""
    if not results:
        return None
    from .schemas import WindowScheduleResult
    windows = []
    pages: list[int] = []
    confidence = 0.0
    for r in results:
        if r is None:
            continue
        windows.extend(r.windows or [])
        for pg in (r.pages or []):
            if pg not in pages:
                pages.append(pg)
        confidence = max(confidence, float(r.confidence or 0.0))
    return WindowScheduleResult(
        pages=pages, windows=windows, confidence=round(confidence, 4),
    )


def _merge_takeoffs(items: list[TakeoffItem]) -> list[TakeoffItem]:
    """Merge takeoffs that share (csi_section or division, normalized desc, unit)."""
    buckets: dict[tuple[str, str, str], TakeoffItem] = {}
    for t in items:
        key = (
            t.csi_section or t.csi_division,
            _norm(t.description),
            t.unit.upper(),
        )
        if key in buckets:
            existing = buckets[key]
            total_qty = existing.quantity + t.quantity
            # weighted-average confidence
            denom = (existing.quantity + t.quantity) or 1
            new_conf = (
                existing.confidence * existing.quantity + t.confidence * t.quantity
            ) / denom
            sheets = list(dict.fromkeys(existing.source_sheet_ids + t.source_sheet_ids))
            buckets[key] = existing.model_copy(update={
                "quantity": round(total_qty, 2),
                "confidence": round(new_conf, 2),
                "source_sheet_ids": sheets,
            })
        else:
            buckets[key] = t
    return list(buckets.values())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def _consolidate_project_info(packages: list[BidPackage]) -> ProjectInfo:
    """Pick the most-attested project info across all packages.

    Bid-package templates sometimes carry stale project info from a previous
    DISD project (we saw this with the drywall package referencing #173004
    while concrete referenced #9A8001). We pick the value that appears in
    the largest number of packages.
    """
    def _vote(field: str) -> tuple[str | None, list[str]]:
        counts: dict[str, list[str]] = {}
        for p in packages:
            v = getattr(p, field)
            if v:
                counts.setdefault(str(v), []).append(p.pdf_name)
        if not counts:
            return None, []
        winner = max(counts.items(), key=lambda kv: (len(kv[1]), kv[0]))
        return winner[0], winner[1]

    name, name_src = _vote("project_name")
    number, _ = _vote("project_number")
    location, _ = _vote("project_location")
    owner, _ = _vote("owner")
    # Prefer `gc` (post-v3) over the deprecated `contractor` field. They
    # mirror each other via BidPackage's model_validator, but voting on
    # `gc` first means new payloads win when both are set on different
    # packages.
    gc_or_contractor, _ = _vote("gc")
    if not gc_or_contractor:
        gc_or_contractor, _ = _vote("contractor")
    bid_due, _ = _vote("bid_due")

    return ProjectInfo(
        name=name,
        number=number,
        location=location,
        owner=owner,
        contractor=gc_or_contractor,
        bid_due=bid_due,
        sources=name_src,
    )


def _aggregate_scope_items(
    packages: list[BidPackage],
    attr: str,
    fuzz_threshold: int = 88,
) -> list[ScopeItem]:
    """Dedupe per-package inclusion/exclusion lines into project-level ScopeItems.

    Two lines are treated as duplicates when `rapidfuzz.fuzz.token_set_ratio`
    on their `_norm()`-ed text is >= `fuzz_threshold`. When that hits, the
    new package's `pdf_name` is appended to the existing item's
    `source_packages` list. The first-seen text wins to keep output stable.
    """
    aggregated: list[ScopeItem] = []
    aggregated_norms: list[str] = []   # parallel cache; avoids re-normalizing each compare

    for p in packages:
        items: list[str] = getattr(p, attr, []) or []
        for text in items:
            text_clean = (text or "").strip()
            if not text_clean:
                continue
            normed = _norm(text_clean)
            if not normed:
                continue

            match_idx: int | None = None
            for i, existing_norm in enumerate(aggregated_norms):
                if fuzz.token_set_ratio(normed, existing_norm) >= fuzz_threshold:
                    match_idx = i
                    break

            if match_idx is None:
                aggregated.append(ScopeItem(text=text_clean, source_packages=[p.pdf_name]))
                aggregated_norms.append(normed)
            else:
                existing = aggregated[match_idx]
                if p.pdf_name not in existing.source_packages:
                    existing.source_packages.append(p.pdf_name)

    return aggregated


def _build_scope_matrix(packages: list[BidPackage]) -> ScopeMatrix:
    by_div: dict[str, list[BidPackage]] = {}
    all_alts: list[Alternate] = []
    seen_alt_keys: set[str] = set()

    for p in packages:
        for div in p.csi_divisions:
            by_div.setdefault(div, []).append(p)
        for a in p.alternates:
            key = (a.number or "") + "::" + _norm(a.description)
            if key in seen_alt_keys:
                continue
            seen_alt_keys.add(key)
            all_alts.append(a)

    warnings: list[str] = []
    # Identify trades that share the same CSI division (potential scope overlap).
    for div, pkgs in by_div.items():
        if len(pkgs) > 1:
            names = ", ".join(p.trade_name or p.pdf_name for p in pkgs)
            warnings.append(f"Division {div} appears in {len(pkgs)} packages: {names}")

    return ScopeMatrix(
        packages=packages,
        by_division=by_div,
        all_alternates=all_alts,
        coverage_warnings=warnings,
    )


def reconcile(
    extractions: list[SheetExtraction],
    sheet_summaries: dict[str, str] | None = None,
) -> ProjectModel:
    """Reduce many `SheetExtraction`s into one project-wide model + takeoff list."""
    rooms: list[Room] = []
    doors: list[DoorEntry] = []
    windows: list[WindowEntry] = []
    structural: list[StructuralElement] = []
    mep: list[MEPItem] = []
    specs: list[SpecSection] = []
    site_info_acc: list[SiteInfo] = []
    raw_takeoffs: list[TakeoffItem] = []
    bid_packages: list[BidPackage] = []
    warnings: list[str] = []
    summaries: dict[str, str] = sheet_summaries or {}
    # Phase T2: per-sheet door-schedule pre-pass → typed TakeoffItem rows.
    # Collected here (not merged via _merge_takeoffs) so each DoorRecord
    # survives as its own line item; cross-source dedupe vs. LLM-derived
    # rows is Phase T3 work.
    synthesized_door_items: list[TakeoffItem] = []
    # Phase T2.5: per-sheet window-schedule pre-pass → typed TakeoffItem
    # rows. Mirror of the door collection above; survives _merge_takeoffs
    # for the same reason. T2.5 dedupe runs alongside T3 once everything
    # is merged.
    synthesized_window_items: list[TakeoffItem] = []
    # Phase T4: per-sheet finish-schedule pre-pass → typed TakeoffItem
    # rows. Each FinishRecord fans out into 3-7 items (one per finished
    # surface: floor / base / wall / ceiling). Survives _merge_takeoffs
    # for the same reason as doors + windows; T4 dedupe runs after.
    synthesized_finish_items: list[TakeoffItem] = []
    # Phase T2.6: per-sheet electrical-panel-schedule pre-pass → typed
    # TakeoffItem rows. Each PanelRecord fans out into 1 panel enclosure
    # + N branch-breaker groups + 2 feeder rows. Survives _merge_takeoffs
    # for the same reason as doors / windows / finishes; T2.6 dedupe runs
    # after the merge.
    synthesized_panel_items: list[TakeoffItem] = []
    # Phase T2.7: per-sheet lighting-fixture-schedule pre-pass → typed
    # TakeoffItem rows. Each LightingFixtureRecord fans out into 1 EA
    # fixture row + optionally 1 LS lamp/driver row (for non-LED-
    # integrated technologies). Same survives-through-merge pattern
    # as panels; T2.7 dedupe runs after the merge.
    synthesized_lighting_items: list[TakeoffItem] = []
    # Phase T2.8: per-sheet HVAC-equipment-schedule pre-pass → typed
    # TakeoffItem rows. Each HVACEquipmentRecord fans out into 1 EA
    # equipment row + 1 LS MEP rough-in row + optionally 1 EA
    # disconnect + flex row (motorized equipment with voltage feed).
    # Same survives-through-merge pattern as panels + lighting;
    # T2.8 dedupe runs after the merge.
    synthesized_hvac_items: list[TakeoffItem] = []
    # Phase T2.9: per-sheet plumbing-fixture-schedule pre-pass →
    # typed TakeoffItem rows. Each PlumbingFixtureRecord fans out
    # into 1 EA fixture row + 1 LS MEP rough-in row + optionally 1
    # LS trim / installation-hardware row (mfr+model gated). Same
    # survives-through-merge pattern as panels + lighting + HVAC;
    # T2.9 dedupe runs after the merge.  Closes the Division
    # 22+23+26 typed-schedule trifecta entirely.
    synthesized_plumbing_items: list[TakeoffItem] = []
    # Phase T5: per-sheet room-schedule pre-pass. Unlike doors / windows
    # / finishes there's no synthesis step — the room schedule supplies
    # GEOMETRY (area / perimeter / ceiling height) that the T5 back-fill
    # joins to the existing T4 finish rows by room_number to fill in
    # the quantity placeholders. Accumulated here, merged after the
    # extraction loop, and passed to ``backfill_finish_quantities`` at
    # the end of the reconcile pipeline.
    room_schedule_results: list = []
    # Phase T5 back-fill also wants the schema-side finish schedules
    # so the back-fill can fall back to the FinishRecord's
    # ceiling_height_ft when the room schedule didn't carry the column.
    finish_schedule_results: list = []
    door_schedule_results: list = []
    window_schedule_results: list = []

    for ex in extractions:
        rooms.extend(ex.rooms)
        doors.extend(ex.doors)
        windows.extend(ex.windows)
        structural.extend(ex.structural)
        mep.extend(ex.mep)
        specs.extend(ex.spec_sections)
        if ex.site:
            site_info_acc.append(ex.site)
        if ex.bid_package:
            bid_packages.append(ex.bid_package)
        raw_takeoffs.extend(ex.raw_takeoffs)
        warnings.extend(ex.warnings)
        if ex.summary:
            summaries.setdefault(ex.sheet_id, ex.summary)
        if ex.prepass is not None and ex.prepass.door_schedule is not None:
            synthesized_door_items.extend(
                synthesize_door_takeoff_items(
                    ex.prepass.door_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
        if ex.prepass is not None and ex.prepass.window_schedule is not None:
            synthesized_window_items.extend(
                synthesize_window_takeoff_items(
                    ex.prepass.window_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
        if ex.prepass is not None and ex.prepass.finish_schedule is not None:
            synthesized_finish_items.extend(
                synthesize_finish_takeoff_items(
                    ex.prepass.finish_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
            finish_schedule_results.append(ex.prepass.finish_schedule)
        if ex.prepass is not None and ex.prepass.room_schedule is not None:
            room_schedule_results.append(ex.prepass.room_schedule)
        if ex.prepass is not None and ex.prepass.door_schedule is not None:
            door_schedule_results.append(ex.prepass.door_schedule)
        if ex.prepass is not None and ex.prepass.window_schedule is not None:
            window_schedule_results.append(ex.prepass.window_schedule)
        if ex.prepass is not None and getattr(ex.prepass, "panel_schedule", None) is not None:
            synthesized_panel_items.extend(
                synthesize_panel_takeoff_items(
                    ex.prepass.panel_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
        if ex.prepass is not None and getattr(ex.prepass, "lighting_schedule", None) is not None:
            synthesized_lighting_items.extend(
                synthesize_lighting_takeoff_items(
                    ex.prepass.lighting_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
        if ex.prepass is not None and getattr(ex.prepass, "hvac_schedule", None) is not None:
            synthesized_hvac_items.extend(
                synthesize_hvac_takeoff_items(
                    ex.prepass.hvac_schedule,
                    sheet_id=ex.sheet_id,
                )
            )
        if ex.prepass is not None and getattr(ex.prepass, "plumbing_schedule", None) is not None:
            synthesized_plumbing_items.extend(
                synthesize_plumbing_takeoff_items(
                    ex.prepass.plumbing_schedule,
                    sheet_id=ex.sheet_id,
                )
            )

    # --- dedupe domain entities ---
    rooms = _dedupe_rooms(rooms)
    doors = _dedupe_by_key(doors, lambda d: d.mark)
    windows = _dedupe_by_key(windows, lambda w: w.mark)
    structural = _dedupe_by_key(
        structural, lambda s: (s.kind.lower(), (s.mark or "").lower(), (s.size or "").lower())
    )
    mep = _dedupe_by_key(
        mep, lambda m: (m.discipline, m.category.lower(), _norm(m.description))
    )
    specs = _dedupe_by_key(specs, lambda s: s.csi_section)

    # --- consolidate site ---
    if site_info_acc:
        site = SiteInfo(
            site_area_sqft=max((s.site_area_sqft or 0 for s in site_info_acc), default=0) or None,
            paving_area_sqft=max((s.paving_area_sqft or 0 for s in site_info_acc), default=0) or None,
            sidewalk_lf=max((s.sidewalk_lf or 0 for s in site_info_acc), default=0) or None,
            landscaping_area_sqft=max((s.landscaping_area_sqft or 0 for s in site_info_acc), default=0) or None,
            notes=" | ".join(s.notes for s in site_info_acc if s.notes) or None,
            source_sheet_id=", ".join(sorted({s.source_sheet_id for s in site_info_acc if s.source_sheet_id})),
        )
    else:
        site = SiteInfo()

    # --- build canonical takeoff list ---
    derived = _derive_takeoffs(rooms, doors, windows, structural, mep, site)
    all_takeoffs = _merge_takeoffs(derived + raw_takeoffs)
    # T2: append synthesised door-schedule rows AFTER _merge_takeoffs so each
    # DoorRecord survives as a distinct EA line. Each row is tagged with
    # ``source=door_schedule_prepass`` at the start of its notes for the
    # T3 dedupe pass below to find.
    all_takeoffs.extend(synthesized_door_items)
    # T2.5: append synthesised window-schedule rows. Same pattern as T2
    # doors; tagged ``source=window_schedule_prepass``.
    all_takeoffs.extend(synthesized_window_items)
    # T4: append synthesised finish-schedule rows. Each FinishRecord
    # already fanned out into 3-7 per-surface items inside
    # ``synthesize_finish_takeoff_items``; tagged
    # ``source=finish_schedule_prepass``.
    all_takeoffs.extend(synthesized_finish_items)
    # T2.6: append synthesised electrical-panel-schedule rows. Each
    # PanelRecord already fanned out into 1 enclosure + N breaker
    # groups + 2 feeder rows inside ``synthesize_panel_takeoff_items``;
    # every row is tagged ``source=panel_schedule_prepass`` for the
    # downstream dedupe pass.
    all_takeoffs.extend(synthesized_panel_items)
    # T2.7: append synthesised lighting-fixture-schedule rows. Each
    # LightingFixtureRecord already fanned out into 1 EA fixture row
    # + optional 1 LS lamp/driver row inside
    # ``synthesize_lighting_takeoff_items``; every row is tagged
    # ``source=lighting_schedule_prepass`` for the downstream
    # dedupe pass.
    all_takeoffs.extend(synthesized_lighting_items)
    # T2.8: append synthesised HVAC-equipment-schedule rows. Each
    # HVACEquipmentRecord already fanned out into 1 EA equipment +
    # 1 LS rough-in + optional 1 EA disconnect inside
    # ``synthesize_hvac_takeoff_items``; every row is tagged
    # ``source=hvac_schedule_prepass`` for the downstream dedupe
    # pass.
    all_takeoffs.extend(synthesized_hvac_items)
    # T2.9: append synthesised plumbing-fixture-schedule rows.  Each
    # PlumbingFixtureRecord already fanned out into 1 EA fixture +
    # 1 LS rough-in + optional 1 LS trim/hardware row inside
    # ``synthesize_plumbing_takeoff_items``; every row is tagged
    # ``source=plumbing_schedule_prepass`` for the downstream
    # dedupe pass.  Closes the Division 22+23+26 typed-schedule
    # trifecta entirely.
    all_takeoffs.extend(synthesized_plumbing_items)
    # T3: drop legacy LLM door aggregates ("Hollow metal doors", "Solid-core
    # wood doors", "Doors (type unspecified)") and same-mark LLM door rows
    # when a deterministic synthesised row already covers them. Pure on
    # `all_takeoffs`; no-op when no synthesised door exists on the project.
    all_takeoffs = dedupe_doors_against_synthesis(all_takeoffs)
    # T2.5 dedupe: same pattern as T3 for windows. Retires the legacy
    # bare "Windows" aggregate and per-material LLM rollups when ANY
    # synthesised window covers the project. No-op when no synthesised
    # window exists (safety rule, mirrors T3).
    all_takeoffs = dedupe_windows_against_synthesis(all_takeoffs)
    # T4 dedupe: same pattern for finishes. Retires per-material
    # finish aggregates ("Carpet flooring", "Interior wall painting
    # (two coats)", "Resilient base, 4"", ...) when ANY synthesised
    # finish row covers the project. No-op safety rule mirrors T3 /
    # T2.5; never touches door or window rows (CSI prefix discriminator).
    all_takeoffs = dedupe_finishes_against_synthesis(all_takeoffs)
    # T2.6 dedupe: retire legacy LLM electrical panel aggregates
    # ("Electrical Panel A, 200A", "Panelboard", "Branch Circuit
    # Breakers") and same-mark LLM panel rows when a deterministic
    # synthesised row already covers them. CSI prefixes ``26 24`` +
    # ``26 28`` keep this pass mutually exclusive with the door /
    # window / finish passes above (Division 08 / 09 / 03 don't
    # overlap). No-op when no synthesised panel exists on the project
    # (safety rule, mirrors T3 / T2.5 / T4).
    all_takeoffs = dedupe_panels_against_synthesis(all_takeoffs)
    # T2.7 dedupe: retire legacy LLM lighting aggregates ("LED
    # downlights", "2x4 troffer fixtures", "Wall sconces") and
    # same-tag LLM lighting rows when a deterministic synthesised
    # row already covers them. CSI prefixes ``26 51`` + ``26 55``
    # keep this pass mutually exclusive with the door / window /
    # finish / panel passes above (Division 08 / 09 / 03 / 26-24
    # / 26-28 don't overlap with 26-51 / 26-55). No-op when no
    # synthesised lighting fixture exists on the project (safety
    # rule, mirrors T3 / T2.5 / T4 / T2.6).
    all_takeoffs = dedupe_lighting_against_synthesis(all_takeoffs)
    # T2.8 dedupe: retire legacy LLM HVAC aggregates ("AHU-1
    # installation", "Mechanical Equipment", "Rooftop Units") and
    # same-tag LLM HVAC rows when a deterministic synthesised row
    # already covers them. CSI prefix ``23`` keeps this pass mutually
    # exclusive with the door / window / finish / panel / lighting
    # passes above (Divisions 08 / 09 / 03 / 26 don't overlap with
    # 23). Plumbing rows (``22 ...``) are also untouched. No-op
    # when no synthesised HVAC equipment exists on the project
    # (safety rule, mirrors T3 / T2.5 / T4 / T2.6 / T2.7).
    all_takeoffs = dedupe_hvac_against_synthesis(all_takeoffs)
    # T2.9 dedupe: retire legacy LLM plumbing aggregates ("Water
    # closets", "Lavatories", "Plumbing Fixtures", "Floor Drains")
    # and same-tag LLM plumbing rows when a deterministic
    # synthesised row already covers them.  CSI prefix ``22`` keeps
    # this pass mutually exclusive with all preceding dedupes
    # (Divisions 08 / 09 / 03 / 23 / 26 don't overlap with 22).
    # No-op when no synthesised plumbing fixture exists on the
    # project (safety rule, mirrors T3 / T2.5 / T4 / T2.6 / T2.7 /
    # T2.8).
    all_takeoffs = dedupe_plumbing_against_synthesis(all_takeoffs)
    # T5 back-fill: replace ``quantity=0.0`` on every finish-synthesis
    # row with the right SF (floor / ceiling = area; base = perimeter
    # in LF; wall = perimeter × height × share). Joins finish rows to
    # room schedules by ``room_number`` via notes-prefix parsing.
    # Door / window schedules are passed for the deferred T5.1
    # opening-deduction follow-up — currently logged-but-unused.
    # When no room schedule was extracted on any sheet the function
    # is a no-op and the finish rows stay at quantity=0.0.
    if room_schedule_results:
        merged_room_schedule = merge_room_schedules(room_schedule_results)
        merged_finish_schedule = _merge_finish_schedules(finish_schedule_results)
        merged_door_schedule = _merge_door_schedules(door_schedule_results)
        merged_window_schedule = _merge_window_schedules(window_schedule_results)
        all_takeoffs = backfill_finish_quantities(
            all_takeoffs,
            merged_room_schedule,
            finish_schedule=merged_finish_schedule,
            door_schedule=merged_door_schedule,
            window_schedule=merged_window_schedule,
        )

    project_info = _consolidate_project_info(bid_packages)
    scope_matrix = _build_scope_matrix(bid_packages)
    if scope_matrix.coverage_warnings:
        warnings.extend(scope_matrix.coverage_warnings)

    aggregated_inclusions = _aggregate_scope_items(bid_packages, "inclusions")
    aggregated_exclusions = _aggregate_scope_items(bid_packages, "exclusions")

    return ProjectModel(
        rooms=rooms,
        doors=doors,
        windows=windows,
        structural=structural,
        mep=mep,
        spec_sections=specs,
        site=site,
        takeoffs=all_takeoffs,
        sheet_summaries=summaries,
        warnings=warnings,
        bid_packages=bid_packages,
        project_info=project_info,
        scope_matrix=scope_matrix,
        aggregated_inclusions=aggregated_inclusions,
        aggregated_exclusions=aggregated_exclusions,
    )
