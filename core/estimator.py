"""Apply unit costs to a `ProjectModel` to produce a priced `Estimate`.

Lookup order for each takeoff line (post-F1):

  1. **CWICR open dataset** — semantic + TF-IDF match against the 55k-row
     CWICR open cost dataset (CC-BY-4.0). Used when the resulting
     similarity is at or above `CWICR_MIN_SIMILARITY` (default 0.55) and
     CWICR is not disabled via `CWICR_DISABLED=true` or the `cost_db`
     CLI flag.
  2. Exact CSI section match in `config/cost_database.json` (seed DB).
  3. Keyword match within the same CSI division (seed DB).
  4. Skip pricing (line is reported with $0 and a `(no match)` source).

`CostLine.cost_source` records which lookup won: ``cwicr:<row_id>`` for a
CWICR match (traceable back to the source row), the CSI key for a seed-DB
match, or ``(no match)`` when both layers missed.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .pricing.cwicr_matcher import (
    CwicrCandidate,
    CwicrMatcher,
    get_default_matcher,
    is_cwicr_disabled,
    min_similarity_threshold,
)
from .schemas import (
    COST_TIER_SEED_DB_PRICE_CONFIDENCE,
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
    TakeoffItem,
    band_for_confidence,
    price_confidence_from_similarity,
)
from .takeoff import ProjectModel

logger = logging.getLogger(__name__)

DEFAULT_COST_DB = Path(__file__).resolve().parent.parent / "config" / "cost_database.json"


# ---------------------------------------------------------------------------
# Cost DB
# ---------------------------------------------------------------------------


class CostDatabase:
    def __init__(self, path: str | Path = DEFAULT_COST_DB):
        self.path = Path(path)
        with self.path.open(encoding="utf-8") as f:
            raw: dict[str, Any] = json.load(f)
        self.meta = raw.pop("_meta", {})
        # Keep only well-formed entries.
        self.entries: dict[str, dict[str, Any]] = {
            k: v for k, v in raw.items()
            if isinstance(v, dict) and "unit_cost" in v and "unit" in v
        }

    def lookup(self, item: TakeoffItem) -> tuple[dict[str, Any] | None, str]:
        """Return (entry, key_used) or (None, '') if no match."""
        # 1. Exact section
        if item.csi_section and item.csi_section in self.entries:
            return self.entries[item.csi_section], item.csi_section

        # 2. Keyword match within the same division
        desc = item.description.lower()
        best_key = None
        best_score = 0
        for key, entry in self.entries.items():
            if not key.startswith(item.csi_division):
                continue
            keywords = entry.get("keywords") or []
            score = sum(1 for kw in keywords if kw.lower() in desc)
            if score > best_score:
                best_score = score
                best_key = key

        if best_key:
            return self.entries[best_key], best_key

        # 3. Last resort - any keyword anywhere
        for key, entry in self.entries.items():
            for kw in entry.get("keywords") or []:
                if kw.lower() in desc:
                    return entry, key

        return None, ""


# ---------------------------------------------------------------------------
# CWICR ↔ seed-DB bridge
# ---------------------------------------------------------------------------


# Per-division fallback waste factor mirroring the seed DB heuristic. Used
# when CWICR wins the match (CWICR rows don't ship a waste factor). Kept
# in one place so it stays in sync with `config/cost_database.json` where
# possible.
_WASTE_BY_DIVISION: dict[str, float] = {
    "03": 1.07,  # concrete
    "04": 1.08,  # masonry
    "05": 1.03,  # steel
    "06": 1.10,  # wood / carpentry
    "07": 1.07,  # thermal / moisture
    "08": 1.02,  # openings
    "09": 1.10,  # finishes
    "31": 1.05,  # earthwork
    "32": 1.05,  # exterior
}


# Per-division default cost-category used when CWICR doesn't ship one. CWICR
# carries labour / material / equipment splits per row but no single tag —
# we infer "subcontractor" for trades that the seed DB also tags that way.
_CATEGORY_BY_DIVISION: dict[str, CostCategory] = {
    "01": CostCategory.OTHER,
    "02": CostCategory.SUBCONTRACTOR,
    "03": CostCategory.SUBCONTRACTOR,
    "04": CostCategory.SUBCONTRACTOR,
    "05": CostCategory.SUBCONTRACTOR,
    "06": CostCategory.LABOR,
    "07": CostCategory.SUBCONTRACTOR,
    "08": CostCategory.MATERIAL,
    "09": CostCategory.SUBCONTRACTOR,
    "10": CostCategory.MATERIAL,
    "11": CostCategory.EQUIPMENT,
    "21": CostCategory.SUBCONTRACTOR,
    "22": CostCategory.SUBCONTRACTOR,
    "23": CostCategory.SUBCONTRACTOR,
    "26": CostCategory.SUBCONTRACTOR,
    "31": CostCategory.SUBCONTRACTOR,
    "32": CostCategory.SUBCONTRACTOR,
    "33": CostCategory.SUBCONTRACTOR,
}


def _category_for_cwicr_candidate(item: TakeoffItem, candidate: CwicrCandidate) -> CostCategory:
    """Derive a CostCategory for a CWICR-priced line.

    Prefer the takeoff's CSI division → category map. Fall back to OTHER.
    """
    cat = _CATEGORY_BY_DIVISION.get(item.csi_division)
    if cat:
        return cat
    # Heuristic: if a row's labor cost dominates, it's labor; if equipment
    # dominates, equipment; else subcontractor as a safe default.
    parts = {
        CostCategory.LABOR:     candidate.labor_cost,
        CostCategory.MATERIAL:  candidate.material_cost,
        CostCategory.EQUIPMENT: candidate.equipment_cost,
    }
    biggest = max(parts.items(), key=lambda kv: kv[1])
    if biggest[1] > 0:
        return biggest[0]
    return CostCategory.SUBCONTRACTOR


def _waste_for_cwicr(item: TakeoffItem) -> float:
    """Per-CSI-division waste factor mirroring the seed DB convention."""
    return _WASTE_BY_DIVISION.get(item.csi_division, 1.0)


# ---------------------------------------------------------------------------
# Phase T7 — combined-confidence band assignment
# ---------------------------------------------------------------------------


def _combined_band(
    qty_confidence: float | None,
    price_confidence: float,
    *,
    suppressed: bool,
) -> CostBand:
    """Return the band for ``qty_confidence × price_confidence``.

    Mirrors the inline math of :pyattr:`CostLine.combined_confidence` so
    callers in ``price_takeoff`` can pick a band BEFORE constructing the
    CostLine (the band is set in the constructor and the
    ``combined_confidence`` property reads from already-set fields).

    ``suppressed=True`` short-circuits to ``HAND_TAKEOFF`` per the
    Phase T6 contract — preserves the calibration-v2 unit-mismatch
    guard regardless of how good the price-side confidence happens to
    be.

    ``qty_confidence is None`` is treated as the schema default 0.7,
    matching the no-confidence-from-LLM legacy path. Both inputs are
    clamped into ``[0, 1]`` before multiplying.
    """
    if suppressed:
        return CostBand.HAND_TAKEOFF
    qty = 0.7 if qty_confidence is None else float(qty_confidence)
    qty = max(0.0, min(1.0, qty))
    price = max(0.0, min(1.0, float(price_confidence)))
    combined = round(qty * price, 4)
    return band_for_confidence(combined, suppressed=False)


def _build_cwicr_line(
    item: TakeoffItem,
    candidate: CwicrCandidate,
    region_multiplier: float,
) -> CostLine:
    """Construct a `CostLine` from a CWICR candidate, honouring unit-mismatch
    suppression the same way the seed-DB path does.

    The estimator records `cost_source = "cwicr:<row_id>"` and stamps the
    candidate's similarity into `confidence` (clamped to [0, 1]).
    """
    unit_cost = float(candidate.unit_price) * region_multiplier
    cost_category = _category_for_cwicr_candidate(item, candidate)
    waste_factor = _waste_for_cwicr(item)

    raw_qty = item.quantity
    ordered_qty = round(raw_qty * waste_factor, 4)

    cost_source = f"cwicr:{candidate.source_row_id}"
    confidence = max(0.0, min(1.0, float(candidate.similarity)))

    # Phase T7 — bridge CWICR similarity into a (tier, price_confidence) pair.
    # The helper is the single source of truth for the boundary semantics.
    tier, price_conf = price_confidence_from_similarity(candidate.similarity)

    takeoff_unit = (item.unit or "").upper().strip()
    cand_unit = (candidate.unit or "").upper().strip()
    unit_mismatch = bool(takeoff_unit) and bool(cand_unit) and takeoff_unit != cand_unit

    if unit_mismatch:
        mismatch_note = (
            f"unit mismatch: takeoff={item.unit}, cwicr={candidate.unit}; "
            f"cost suppressed from total — the CWICR best match is metric / "
            f"differently-keyed. Add a conversion factor or override unit_cost "
            f"manually to include this line."
        )
        # Suppressed → tier=MISSING, price_confidence=0 (mirrors the
        # Phase T7 contract that suppressed lines effectively have no
        # usable cost data, even though CWICR did surface a candidate).
        return CostLine(
            csi_division=item.csi_division,
            csi_section=item.csi_section or "",
            description=item.description,
            quantity=ordered_qty,
            unit=item.unit,
            unit_cost=0.0,
            total_cost=0.0,
            cost_category=cost_category,
            raw_quantity=raw_qty,
            waste_factor=waste_factor,
            confidence=confidence,
            source_sheet_ids=item.source_sheet_ids,
            cost_source=cost_source,
            notes=" | ".join(filter(None, [item.notes, mismatch_note])) or None,
            suppressed=True,
            cost_band=_combined_band(confidence, 0.0, suppressed=True),
            price_confidence=0.0,
            cost_source_tier=CostSourceTier.MISSING,
        )

    total = round(unit_cost * ordered_qty, 2)
    return CostLine(
        csi_division=item.csi_division,
        csi_section=item.csi_section or "",
        description=item.description,
        quantity=ordered_qty,
        unit=item.unit,
        unit_cost=round(unit_cost, 2),
        total_cost=total,
        cost_category=cost_category,
        raw_quantity=raw_qty,
        waste_factor=waste_factor,
        confidence=confidence,
        source_sheet_ids=item.source_sheet_ids,
        cost_source=cost_source,
        notes=item.notes,
        cost_band=_combined_band(confidence, price_conf, suppressed=False),
        price_confidence=price_conf,
        cost_source_tier=tier,
    )


# ---------------------------------------------------------------------------
# Pricing
# ---------------------------------------------------------------------------


def price_takeoff(
    project: ProjectModel,
    project_name: str,
    region_multiplier: float = 1.0,
    contingency_pct: float = 10.0,
    overhead_pct: float = 10.0,
    profit_pct: float = 5.0,
    cost_db: CostDatabase | None = None,
    *,
    cwicr_matcher: CwicrMatcher | None = None,
    use_cwicr: bool | None = None,
    use_seed: bool = True,
) -> Estimate:
    """Apply unit costs to a project's takeoffs.

    Resolution order (when both layers are enabled):

      1. CWICR (if `use_cwicr`, `CWICR_DISABLED` is unset, and the best
         similarity ≥ `CWICR_MIN_SIMILARITY`).
      2. Seed cost DB (`config/cost_database.json`), exact CSI section
         then keyword match within the same division.
      3. `(no match)` placeholder line at $0.
    """
    if use_seed:
        db = cost_db or CostDatabase()
    else:
        db = None

    # ---- CWICR layer setup ----
    if use_cwicr is None:
        use_cwicr = not is_cwicr_disabled()
    matcher: CwicrMatcher | None = None
    if use_cwicr:
        try:
            matcher = cwicr_matcher or get_default_matcher()
        except Exception as exc:
            logger.warning(
                "CWICR matcher unavailable (%s); falling back to seed DB only.",
                exc,
            )
            matcher = None
    cwicr_threshold = min_similarity_threshold()

    line_items: list[CostLine] = []

    for t in project.takeoffs:
        # ---- 1. CWICR ----
        cwicr_cand: CwicrCandidate | None = None
        if matcher is not None:
            try:
                cands = matcher.match(
                    t.description,
                    unit_hint=t.unit,
                    csi_hint=t.csi_section or t.csi_division,
                    top_k=1,
                )
            except Exception as exc:
                logger.warning(
                    "CWICR match failed for %r (%s); falling back to seed DB.",
                    t.description[:60], exc,
                )
                cands = []
            if cands and cands[0].similarity >= cwicr_threshold:
                cwicr_cand = cands[0]

        if cwicr_cand is not None:
            line_items.append(_build_cwicr_line(t, cwicr_cand, region_multiplier))
            continue

        # ---- 2. Seed DB ----
        entry, key = (None, "")
        if db is not None:
            entry, key = db.lookup(t)
        if entry is None:
            # No-match line: total_cost is $0 regardless of band, so the
            # band assignment only affects which queue this line lands in
            # downstream (operator-review or hand-takeoff). A $0 line is
            # still useful as a "needs pricing" worklist marker.
            #
            # Phase T7 — no-match → tier=MISSING (no cost data was
            # available at all; mirrors the suppressed-line semantics).
            # ``price_confidence=0`` collapses ``combined_confidence`` to
            # 0, which lands the row in HAND_TAKEOFF via the band helper
            # — matching the brief's "informational, not in totals" rule.
            line_items.append(CostLine(
                csi_division=t.csi_division,
                csi_section=t.csi_section,
                description=t.description,
                quantity=t.quantity,
                unit=t.unit,
                unit_cost=0.0,
                total_cost=0.0,
                cost_category=CostCategory.OTHER,
                raw_quantity=t.quantity,
                waste_factor=1.0,
                confidence=t.confidence,
                source_sheet_ids=t.source_sheet_ids,
                cost_source="(no match)",
                notes=(t.notes + " | " if t.notes else "") + "Unit cost not found - add to cost_database.json",
                cost_band=_combined_band(t.confidence, 0.0, suppressed=False),
                price_confidence=0.0,
                cost_source_tier=CostSourceTier.MISSING,
            ))
            continue

        unit_cost = float(entry["unit_cost"]) * region_multiplier

        # Cost-category tag - default to OTHER if the DB entry is untagged or
        # carries a value we don't recognise.
        cat_raw = str(entry.get("cost_category", "")).lower().strip()
        try:
            cost_category = CostCategory(cat_raw) if cat_raw else CostCategory.OTHER
        except ValueError:
            cost_category = CostCategory.OTHER

        # Waste factor - clamp to >= 1.0 to keep ordered quantity from going
        # *below* the measured takeoff. A misconfigured 0.0 would silently
        # zero out a line, which is worse than ignoring the bad value.
        waste_factor = float(entry.get("waste_factor", 1.0) or 1.0)
        if waste_factor < 1.0:
            waste_factor = 1.0

        raw_qty = t.quantity
        ordered_qty = round(raw_qty * waste_factor, 4)

        # Unit mismatches (e.g. takeoff is LF but DB entry is TON) get
        # suppressed from the total — calibration v2 found two such lines
        # silently rolling a $34,608 phantom subcontractor line into the
        # headline subtotal because the multiplication was dimensionally
        # nonsensical (LF × TON unit price). Future enhancement: read a
        # documented conversion factor (e.g. `conversions: {LF: 0.012}`)
        # off the cost-DB entry and apply it; for now any mismatch without
        # an explicit override is suppressed.
        takeoff_unit = (t.unit or "").upper().strip()
        db_unit = str(entry.get("unit", "")).upper().strip()
        unit_mismatch = bool(takeoff_unit) and bool(db_unit) and takeoff_unit != db_unit

        if unit_mismatch:
            mismatch_note = (
                f"unit mismatch: takeoff={t.unit}, db={entry.get('unit')}; "
                f"cost suppressed from total — fix takeoff unit or add a "
                f"conversion factor to the cost DB"
            )
            # Phase T7 — suppressed seed-DB hit → tier=MISSING + price_conf=0,
            # exactly as the suppressed CWICR branch above.
            line_items.append(CostLine(
                csi_division=t.csi_division,
                csi_section=t.csi_section or key,
                description=t.description,
                quantity=ordered_qty,
                unit=t.unit,
                unit_cost=0.0,
                total_cost=0.0,
                cost_category=cost_category,
                raw_quantity=raw_qty,
                waste_factor=waste_factor,
                confidence=t.confidence,
                source_sheet_ids=t.source_sheet_ids,
                cost_source=key,
                notes=" | ".join(filter(None, [t.notes, mismatch_note])) or None,
                suppressed=True,
                cost_band=_combined_band(t.confidence, 0.0, suppressed=True),
                price_confidence=0.0,
                cost_source_tier=CostSourceTier.MISSING,
            ))
            continue

        total = round(unit_cost * ordered_qty, 2)
        # Phase T7 — seed-DB hit → tier=EXACT_MATCH with the fixed
        # ``COST_TIER_SEED_DB_PRICE_CONFIDENCE`` (0.95) discount. The
        # seed catalog is hand-curated against MasterFormat sections,
        # so any seed-DB hit is treated as exact; the 0.95 (vs 1.00)
        # acknowledges that the seed's coverage is narrower than CWICR.
        line_items.append(CostLine(
            csi_division=t.csi_division,
            csi_section=t.csi_section or key,
            description=t.description,
            quantity=ordered_qty,
            unit=t.unit,
            unit_cost=round(unit_cost, 2),
            total_cost=total,
            cost_category=cost_category,
            raw_quantity=raw_qty,
            waste_factor=waste_factor,
            confidence=t.confidence,
            source_sheet_ids=t.source_sheet_ids,
            cost_source=key,
            notes=t.notes,
            cost_band=_combined_band(
                t.confidence, COST_TIER_SEED_DB_PRICE_CONFIDENCE, suppressed=False
            ),
            price_confidence=COST_TIER_SEED_DB_PRICE_CONFIDENCE,
            cost_source_tier=CostSourceTier.EXACT_MATCH,
        ))

    # Sort: by division ascending, suppressed lines below priced lines within
    # each division, then by total_cost descending. Band order is implicitly
    # preserved within (division, suppressed) groups because higher-confidence
    # bands also tend to carry larger total_cost values; we don't sort on band
    # explicitly so the existing Excel "Line Items" reading order stays
    # familiar.
    line_items.sort(
        key=lambda li: (li.csi_division, 1 if li.suppressed else 0, -li.total_cost)
    )

    return Estimate(
        project_name=project_name,
        region_multiplier=region_multiplier,
        contingency_pct=contingency_pct,
        overhead_pct=overhead_pct,
        profit_pct=profit_pct,
        line_items=line_items,
    )
