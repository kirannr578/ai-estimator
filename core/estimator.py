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
import re
from datetime import datetime, timezone
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
    MAX_OVERRIDE_SNAPSHOTS,
    AlternateLine,
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    CostBand,
    CostCategory,
    CostLine,
    CostLineOverrideSnapshot,
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


# Phase T6.1 — fallback qty-confidence used when ``_combined_band`` is
# called with ``qty_confidence is None`` (the legacy LLM-emitted-no-
# confidence path). Bumped from the pre-T6.1 value of 0.70 to 0.80 to
# align with the AUTO_APPROVE / OPERATOR_REVIEW band boundary the BB
# calibration math depends on (see T6.1 calibration notes in
# ``docs/ROADMAP_TAKEOFF_AUTOMATION.md``). The schema-level
# ``TakeoffItem.confidence`` and ``CostLine.confidence`` defaults
# (still 0.70) are preserved per the T6.1 no-touch-schemas constraint;
# this constant fires only when the runtime sees an explicit None,
# i.e. defensive for hand-constructed payloads that omit the field.
LLM_DEFAULT_QTY_CONFIDENCE: float = 0.80


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

    ``qty_confidence is None`` is treated as
    :data:`LLM_DEFAULT_QTY_CONFIDENCE` (0.80 post-T6.1, was 0.70
    pre-T6.1) — the LLM-no-confidence legacy path. Both inputs are
    clamped into ``[0, 1]`` before multiplying.
    """
    if suppressed:
        return CostBand.HAND_TAKEOFF
    qty = LLM_DEFAULT_QTY_CONFIDENCE if qty_confidence is None else float(qty_confidence)
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


# ---------------------------------------------------------------------------
# Phase T9.0 — bid alternates / VE pricing
# ---------------------------------------------------------------------------
#
# Companion to ``price_takeoff`` above. Where ``price_takeoff`` builds
# the headline :class:`Estimate` from a project's measured takeoffs,
# ``price_alternates`` walks the project's :class:`AlternateLine`
# records (populated by the bid-form alternates extractor in
# :mod:`core.extraction.bid_form_alternates`) and resolves each into a
# priced :class:`AlternateLineEstimate` row.
#
# The alternates list is a PARALLEL rollup — it does NOT modify the
# base estimate's ``subtotal`` / ``grand_total``. The two helpers on
# :class:`Estimate` (``subtotal_with_alternates_selected`` /
# ``total_with_alternates_selected``) let an operator compose the
# base bid with any subset of alternates at runtime without
# re-running the pipeline.
#
# Resolution order per :class:`AlternateLine`:
#
#   1. ``cost_delta`` populated  → pricing_basis = EXTRACTED_FROM_BID_FORM
#      (the printed value came off the bid form). Confidence pulls from
#      the AlternateLine's own ``confidence`` (set by the extractor).
#   2. ``related_takeoff_items`` populated → pricing_basis =
#      SYNTHESIZED_FROM_TAKEOFF. Cost is the signed sum of priced
#      ``CostLine.total_cost`` for every line whose ``description``
#      (case-insensitive substring match) or ``csi_section`` appears
#      in the AlternateLine's takeoff-item id list. DEDUCTIVE / VE
#      alternates flip the synthesized sum to negative.
#   3. Neither → pricing_basis = MISSING, ``cost_delta=None``. Surfaced
#      in the operator-review queue (Excel "Bid Alternates" sheet +
#      Project Summary block + the deferred T9.1 Streamlit tab).


def _synthesize_alternate_cost_delta(
    alt: AlternateLine,
    line_items: list[CostLine],
) -> float | None:
    """Sum priced CostLines that match ``alt.related_takeoff_items``.

    Match rule: a CostLine matches when ANY of the strings in
    ``related_takeoff_items`` appears (case-insensitive substring) in
    the CostLine's ``description`` OR equals the CostLine's
    ``csi_section`` (case-insensitive). Conservative — designed to
    capture the common "alternate references the CSI section the
    affected scope rolls up to" pattern without false-matching on
    short tokens.

    DEDUCTIVE and VE alternates flip the magnitude to negative.
    SUBSTITUTION alternates pass through as-is (signed sum); the
    caller has already accounted for the "net of removed scope" by
    listing both the new and removed line items in
    ``related_takeoff_items`` if appropriate.

    Returns ``None`` when ``related_takeoff_items`` is empty OR no
    line items match — caller treats this as MISSING.
    """
    if not alt.related_takeoff_items:
        return None
    needles = [s.lower().strip() for s in alt.related_takeoff_items if s and s.strip()]
    if not needles:
        return None
    total = 0.0
    matched = 0
    for li in line_items:
        if li.suppressed:
            continue
        desc = (li.description or "").lower()
        section = (li.csi_section or "").lower()
        for n in needles:
            if not n:
                continue
            if n == section or n in desc:
                total += float(li.total_cost or 0.0)
                matched += 1
                break
    if matched == 0:
        return None
    if alt.alternate_type in (AlternateType.DEDUCTIVE, AlternateType.VE):
        return -abs(round(total, 2))
    return round(total, 2)


def price_alternates(
    project: ProjectModel,
    line_items: list[CostLine] | None = None,
    *,
    region_multiplier: float = 1.0,
) -> list[AlternateLineEstimate]:
    """Resolve every :class:`AlternateLine` on ``project`` into a priced row.

    ``line_items`` is the priced base estimate's ``line_items`` list
    (used for the SYNTHESIZED_FROM_TAKEOFF path). When ``None``, the
    synthesis path is skipped — alternates with neither a
    ``cost_delta`` nor priced related_takeoff_items collapse to
    MISSING.

    ``region_multiplier`` scales the extracted cost_delta (mirrors the
    seed-DB / CWICR pricing path). Set to the same value the
    estimator passed to ``price_takeoff`` so the alternates roll-up
    composes cleanly with the base subtotal.

    Returns a list with the same ordering as ``project.alternates``.
    """
    project_alts: list[AlternateLine] = list(getattr(project, "alternates", None) or [])
    base_lines: list[CostLine] = list(line_items or [])
    out: list[AlternateLineEstimate] = []

    for alt in project_alts:
        included = bool(alt.included_by_default)
        confidence = alt.confidence

        # Path 1: cost_delta populated on the AlternateLine → use as-is.
        if alt.cost_delta is not None:
            delta = round(float(alt.cost_delta) * region_multiplier, 2)
            out.append(
                AlternateLineEstimate(
                    alternate_id=alt.alternate_id,
                    alternate_type=alt.alternate_type,
                    description=alt.description,
                    cost_delta=delta,
                    pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
                    confidence=confidence,
                    included_in_base=included,
                    bid_package_id=alt.bid_package_id,
                    source_sheet=alt.source_sheet,
                    related_csi=list(alt.related_csi or []),
                    operator_notes=alt.operator_notes,
                )
            )
            continue

        # Path 2: related_takeoff_items populated → synthesize from base.
        synthesized = _synthesize_alternate_cost_delta(alt, base_lines)
        if synthesized is not None:
            delta = round(synthesized * region_multiplier, 2)
            # Synthesis confidence: the extractor's qty-side confidence
            # × a 0.85 "synthesis isn't a printed number" haircut.
            syn_conf = round(max(0.0, min(1.0, confidence)) * 0.85, 4)
            out.append(
                AlternateLineEstimate(
                    alternate_id=alt.alternate_id,
                    alternate_type=alt.alternate_type,
                    description=alt.description,
                    cost_delta=delta,
                    pricing_basis=AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF,
                    confidence=syn_conf,
                    included_in_base=included,
                    bid_package_id=alt.bid_package_id,
                    source_sheet=alt.source_sheet,
                    related_csi=list(alt.related_csi or []),
                    operator_notes=alt.operator_notes,
                )
            )
            continue

        # Path 3: neither — MISSING. Surfaced in the operator-review
        # queue. ``cost_delta=None`` and a low confidence floor so the
        # downstream UI / PDF can highlight the row visually.
        out.append(
            AlternateLineEstimate(
                alternate_id=alt.alternate_id,
                alternate_type=alt.alternate_type,
                description=alt.description,
                cost_delta=None,
                pricing_basis=AlternatePricingBasis.MISSING,
                confidence=min(confidence, 0.50),
                included_in_base=included,
                bid_package_id=alt.bid_package_id,
                source_sheet=alt.source_sheet,
                related_csi=list(alt.related_csi or []),
                operator_notes=alt.operator_notes,
            )
        )

    return out


def attach_alternates_to_estimate(
    estimate: Estimate,
    project: ProjectModel,
    *,
    region_multiplier: float | None = None,
) -> Estimate:
    """Return a new :class:`Estimate` with priced alternates attached.

    Companion to :func:`price_alternates` for the common one-shot
    caller pattern: build the base estimate via :func:`price_takeoff`,
    then attach alternates via this helper. The returned estimate is
    a fresh object (Pydantic ``model_copy``); the input is not
    mutated.

    ``region_multiplier`` defaults to the estimate's own
    ``region_multiplier`` — matches the convention the seed-DB /
    CWICR pricing uses when baking the regional adjustment into each
    ``unit_cost``.
    """
    rm = (
        float(region_multiplier)
        if region_multiplier is not None
        else float(estimate.region_multiplier)
    )
    priced = price_alternates(project, estimate.line_items, region_multiplier=rm)
    selected_default: set[str] = {
        p.alternate_id for p in priced if p.included_in_base
    }
    return estimate.model_copy(
        update={
            "alternates": priced,
            "alternates_selected_default": selected_default,
        }
    )


# ---------------------------------------------------------------------------
# Phase T6.1 — manual override
# ---------------------------------------------------------------------------


# Note prefix the override pass writes onto every overridden CostLine. The
# prefix is stable so a downstream reader (Excel / PDF / Streamlit) can
# detect overrides by inspecting ``notes`` even when the operator forgot
# to label them. Kept short to avoid bloating exports.
MANUAL_OVERRIDE_NOTE_PREFIX: str = "operator override"


# Phase T6.4.c.2 — canonical manual-override source tag.
#
# This constant MIRRORS
# :data:`core.pricing.batch_override.SOURCE_TAG_MANUAL_OVERRIDE` (the
# project-wide canonical source-of-truth). The mirror exists ONLY
# because :mod:`core.pricing.batch_override` already imports
# :func:`apply_manual_override` from this module at top level (the
# batch-apply loop drives one manual override per matched row), so a
# top-level ``from .pricing.batch_override import SOURCE_TAG_MANUAL_OVERRIDE``
# here would cause a circular import. The two constants are pinned to
# the SAME string literal by
# :func:`tests.test_manual_override_tag.test_local_tag_constant_matches_canonical`
# so a future rename in :mod:`core.pricing.batch_override` lights up
# immediately.
SOURCE_TAG_MANUAL_OVERRIDE: str = "[manual-override]"


def format_manual_override_note(
    *,
    unit_cost: float | None = None,
    qty: float | None = None,
    reason: str = "",
    source_tag: str = SOURCE_TAG_MANUAL_OVERRIDE,
    prior_notes: str | None = None,
) -> str:
    """Phase T6.4.c.2 — format a manual-override operator note with the
    canonical source tag at **position 0** of the returned string.

    Closes the last loose end from the T6.4.c source-tag propagation
    contract: every override path (batch CSV, sub-quote tabular,
    sub-quote LLM-vision, AND the T6.1 single-line manual primitive)
    now lands its provenance tag at the start of ``CostLine.notes``
    so a downstream auditor sees the attribution at a glance even
    when an Excel / PDF column is narrow.

    Format::

        <source_tag> operator override: [unit_cost: $X.XX] [qty: Y] <reason>[ | previous: <prior_notes>]

    The shape mirrors the head produced by
    :func:`core.pricing.batch_override._rewrite_notes_with_tag_first`
    (a deliberate symmetry — see *Design choice* below). Empty fields
    are skipped without leaving double-space gaps. A bare call with
    no args + no prior + default tag yields the minimal
    ``"[manual-override] operator override"`` sentinel.

    Args:
        unit_cost: New per-unit cost. Renders as
            ``"[unit_cost: $X.XX]"`` (always 2-decimal) when set.
            ``None`` omits the field entirely.
        qty: New quantity. Renders as ``"[qty: Y]"`` (``:g`` formatted
            so ``100.0`` → ``"100"``, ``12.5`` → ``"12.5"``) when set.
            ``None`` omits the field. :func:`apply_manual_override`
            does not currently change quantity so it always passes
            ``None`` here; the parameter exists for forward-compat
            with a future qty-tweak primitive and for direct callers.
        reason: Free-text operator note. Stripped; empty values are
            skipped. No orphan colon when empty.
        source_tag: Canonical source tag. Defaults to
            :data:`SOURCE_TAG_MANUAL_OVERRIDE` (``"[manual-override]"``);
            parametrised so a future calibration tier
            (``"[manual-override-llm]"`` etc.) can slot in without a
            code change.
        prior_notes: The line's ``notes`` field BEFORE the override.
            ``None`` / empty → no ``"| previous: ..."`` suffix. When
            ``prior_notes`` already starts with the same head string,
            the function short-circuits and returns ``prior_notes``
            unchanged (idempotency).

    Returns:
        A new notes string with ``source_tag`` at position 0,
        ``operator override`` sentinel immediately after, the
        bracketed-fields portion, the reason text, and the
        ``" | previous: ..."`` suffix (when applicable).

    Design choice — own formatter vs reusing
    ``_rewrite_notes_with_tag_first``: the batch helper is private
    (leading underscore) and its contract requires a ``note_payload``
    string already shaped by :func:`format_batch_operator_note` (the
    ``[vendor: …] [quote-ref: …] [csv-row: N] …`` layout, irrelevant
    to a single-line manual override). Reaching across module
    privacy to reuse it would couple ``apply_manual_override`` to
    the batch pipeline's internal layout. The symmetry that matters
    — tag at position 0, ``operator override`` sentinel,
    ``| previous: …`` suffix, idempotency on identical head — is
    replicated here inline. The two functions can drift
    independently if the manual primitive ever needs a field (e.g.
    ``[approver: …]``) the batch path doesn't.

    Re-apply semantics: **most-recent-wins** with chain-preserving
    suffix. When called twice with the SAME args, the second call
    returns the first's output unchanged (idempotent — the head
    string equality check short-circuits). When called twice with
    DIFFERENT args, the new head sits at position 0 and the prior
    string is preserved in the ``" | previous: …"`` suffix; the
    operator can read the full chain of overrides by walking the
    suffix. This matches the T6.4.c batch contract verbatim.
    """
    parts: list[str] = []
    if unit_cost is not None:
        parts.append(f"[unit_cost: ${float(unit_cost):.2f}]")
    if qty is not None:
        parts.append(f"[qty: {float(qty):g}]")
    reason_clean = reason.strip() if reason else ""
    if reason_clean:
        parts.append(reason_clean)

    if parts:
        head = f"{source_tag} {MANUAL_OVERRIDE_NOTE_PREFIX}: " + " ".join(parts)
    else:
        head = f"{source_tag} {MANUAL_OVERRIDE_NOTE_PREFIX}"

    prior = (prior_notes or "").strip()
    if not prior:
        return head

    if prior == head or prior.startswith(head + " | previous: "):
        return prior

    return f"{head} | previous: {prior}"


def _resolve_override_index(
    estimate: Estimate,
    line_id: int | str,
) -> int:
    """Return the 0-based index of the line targeted by ``line_id``.

    Matching order:

    1. ``int`` -> use directly as an index (negative indexing OK).
    2. ``str`` that equals an existing ``CostLine.cost_source`` (must
       be unique across the estimate; ambiguous matches raise).
    3. ``str`` that equals an existing ``CostLine.description`` (same
       uniqueness rule).

    Raises :class:`ValueError` for a missing, ambiguous, or out-of-range
    target. Pydantic-validated input means the calling Streamlit /
    test code can rely on ``ValueError`` to surface a clean operator-
    facing message rather than a silent mis-update.
    """
    items = estimate.line_items
    if not items:
        raise ValueError(
            "apply_manual_override: estimate has no line items to override."
        )

    if isinstance(line_id, int):
        idx = line_id
        if idx < 0:
            idx += len(items)
        if not 0 <= idx < len(items):
            raise ValueError(
                f"apply_manual_override: index {line_id} out of range "
                f"for {len(items)} line items"
            )
        return idx

    if not isinstance(line_id, str) or not line_id.strip():
        raise ValueError(
            f"apply_manual_override: line_id must be int or non-empty str, "
            f"got {type(line_id).__name__}"
        )

    needle = line_id.strip()
    for attr in ("cost_source", "description"):
        matches = [
            i for i, li in enumerate(items) if str(getattr(li, attr) or "") == needle
        ]
        if len(matches) == 1:
            return matches[0]
        if len(matches) > 1:
            raise ValueError(
                f"apply_manual_override: line_id {line_id!r} matched "
                f"{len(matches)} lines on {attr}; pass an integer index "
                f"to disambiguate"
            )
    raise ValueError(
        f"apply_manual_override: no line item matched line_id {line_id!r}"
    )


def apply_manual_override(
    estimate: Estimate,
    line_id: int | str,
    new_unit_cost: float,
    operator_note: str | None = None,
) -> Estimate:
    """Apply an operator-vouched unit-cost override to one CostLine.

    Returns a NEW :class:`Estimate` with one line item replaced; the
    input ``estimate`` is not mutated. The returned estimate has every
    aggregate recomputed automatically because all aggregates
    (``subtotal``, ``total_by_tier``, ``grand_total``, ...) are derived
    properties.

    The targeted line is identified by ``line_id`` (see
    :func:`_resolve_override_index` for the matching rules), the
    ``unit_cost`` is replaced with ``new_unit_cost`` (clamped to
    non-negative), ``total_cost`` is recomputed as
    ``unit_cost × quantity`` (rounded to 2 dp), the
    ``cost_source_tier`` is stamped to
    :attr:`CostSourceTier.MANUAL_OVERRIDE` and
    ``price_confidence`` is forced to 1.0 (the operator vouches for
    the number). The new ``cost_band`` is recomputed against the new
    ``combined_confidence`` (qty × 1.0 — and the suppressed flag is
    cleared because hand-pricing IS the unit-mismatch resolution).
    ``operator_note`` (when supplied) is appended to the line's
    ``notes`` field with the :data:`MANUAL_OVERRIDE_NOTE_PREFIX`
    sentinel so a downstream reader can detect the override.

    Idempotency: re-applying the same override (same ``line_id`` /
    ``new_unit_cost``) produces a CostLine with the same fields — the
    ``operator_note`` is appended once per call when supplied, so
    callers should pass ``operator_note=None`` on retries that
    shouldn't grow the notes blob.

    Args:
        estimate: The :class:`Estimate` to update. NOT mutated.
        line_id: ``int`` index OR ``str`` cost_source / description.
        new_unit_cost: New per-unit cost. Must be ≥ 0; values < 0
            raise :class:`ValueError`.
        operator_note: Optional free-text note appended to the line's
            ``notes`` field.

    Returns:
        A new :class:`Estimate` with one CostLine replaced and all
        aggregates implicitly recomputed.

    Raises:
        ValueError: if ``new_unit_cost`` is negative, or
            ``line_id`` doesn't resolve to a unique line item.
    """
    if new_unit_cost is None or float(new_unit_cost) < 0:
        raise ValueError(
            f"apply_manual_override: new_unit_cost must be ≥ 0, "
            f"got {new_unit_cost!r}"
        )

    idx = _resolve_override_index(estimate, line_id)
    line = estimate.line_items[idx]

    new_uc = round(float(new_unit_cost), 2)
    new_total = round(new_uc * line.quantity, 2)

    # Phase T6.4.c.2 — always stamp ``[manual-override]`` at position 0
    # of ``CostLine.notes`` (mirrors the T6.4.c batch / sub-quote tag
    # propagation). The formatter handles idempotency: re-applying the
    # same override leaves notes unchanged; a re-apply with new args
    # puts the new head first and preserves prior notes in the
    # ``| previous: ...`` suffix.
    new_notes = format_manual_override_note(
        unit_cost=new_uc,
        reason=(operator_note or "").strip(),
        prior_notes=line.notes,
    )

    # Recompute the band against the NEW combined_confidence. Manual
    # override clears the suppression flag — hand-pricing IS the
    # resolution to a unit-mismatch suppression, so the line should
    # roll back into the headline once it's priced.
    new_band = _combined_band(
        line.confidence, 1.0, suppressed=False
    )

    # Phase T6.4.d — capture the pre-override snapshot BEFORE mutating
    # the line so an operator can roll back this single override later
    # via :func:`revert_last_override`. Append to the existing stack
    # (preserves any prior batch / sub-quote / manual snapshots so a
    # multi-layer chain can be unwound one layer at a time) and enforce
    # the FIFO cap so a pathological re-apply loop cannot grow the
    # line's footprint without bound. This applies to EVERY override
    # path because batch / sub-quote apply both flow through this same
    # primitive (see :func:`core.pricing.batch_override.apply_batch_plan`
    # and :func:`core.pricing.subquote_parser.apply_subquote_plan`).
    snapshot = _capture_line_snapshot(line)
    new_snapshots = list(line.override_snapshots) + [snapshot]
    if len(new_snapshots) > MAX_OVERRIDE_SNAPSHOTS:
        new_snapshots = new_snapshots[-MAX_OVERRIDE_SNAPSHOTS:]

    new_line = line.model_copy(update={
        "unit_cost": new_uc,
        "total_cost": new_total,
        "price_confidence": 1.0,
        "cost_source_tier": CostSourceTier.MANUAL_OVERRIDE,
        "cost_band": new_band,
        "suppressed": False,
        "notes": new_notes,
        "override_snapshots": new_snapshots,
    })

    new_lines = list(estimate.line_items)
    new_lines[idx] = new_line

    return estimate.model_copy(update={"line_items": new_lines})


# ---------------------------------------------------------------------------
# Phase T6.4.d — per-line undo via snapshot store
# ---------------------------------------------------------------------------
#
# Every override path (T6.1 manual primitive, T6.3 batch CSV, T8.1 / T8.2
# sub-quote PDF) flows through :func:`apply_manual_override` — so wiring
# the snapshot capture into that single function gives us pre-override
# snapshot capture for FREE on every batch / sub-quote / manual apply.
#
# Design choice: snapshot store (Option A) over notes-suffix parsing
# (Option C). The ``| previous: ...`` suffix that T6.4.c / T6.4.c.2
# already write into ``CostLine.notes`` carries the prior tag /
# bracketed-fields description but does NOT preserve actual numeric
# values (``unit_cost``, ``qty``, ``total_cost``, ``price_confidence``,
# ``combined_confidence``, ``cost_band``). So a notes-only undo cannot
# rebuild the pre-override numeric state without re-running the pricing
# pipeline. The snapshot store sidesteps the lossiness entirely: each
# entry carries every field needed to restore the line byte-identically.
#
# UU's "elegant path" suggestion (parse the notes suffix) was an
# over-optimistic read — the brief acknowledged this and recommended
# Option A. The implementation below realises Option A. Notes-suffix
# parsing is still useful for human-facing audit (Excel / PDF / UI), but
# the canonical undo target is always the snapshot.


# Regex matching the canonical T6.4.c source-tag pattern at the head of
# a ``CostLine.notes`` string. Mirrors
# :data:`core.pricing.batch_override.SOURCE_TAG_PATTERN` but kept local
# to avoid a circular import (``core.pricing.batch_override`` already
# imports :func:`apply_manual_override` from this module). Pinned to the
# same shape by tests in ``tests/test_per_line_undo.py``.
_SOURCE_TAG_HEAD_RE = re.compile(r"^(\[[a-z][a-z\-]*\])\s")


def _extract_leading_source_tag(notes: str | None) -> str:
    """Return the canonical source tag at position 0 of ``notes``, or ``""``.

    Helper for :func:`_capture_line_snapshot`. The snapshot's
    ``source_tag`` field labels the layer we're about to bury so the
    Streamlit revert UI can show "revert to vendor-CSV state from
    14:32" without re-parsing the chain.

    A line at priced-from-cost-DB defaults (no override yet) has no
    leading tag — those snapshots carry ``source_tag=""`` which the UI
    renders as "(priced default)".
    """
    if not notes:
        return ""
    m = _SOURCE_TAG_HEAD_RE.match(notes)
    return m.group(1) if m else ""


def _capture_line_snapshot(
    line: CostLine,
    *,
    applied_at: datetime | None = None,
) -> CostLineOverrideSnapshot:
    """Snapshot the current state of ``line`` for per-line undo.

    Captured BEFORE every override path (T6.1 manual / T6.3 batch /
    T8.1 / T8.2 sub-quote) mutates the line. The snapshot describes
    the state to roll back TO — i.e. the state the line was in at
    the moment this function ran.

    Args:
        line: The :class:`CostLine` whose pre-override state to
            capture. Not mutated.
        applied_at: UTC timestamp to stamp on the snapshot. Defaults
            to ``datetime.now(timezone.utc)`` — caller injects a
            fixed value in tests for deterministic comparisons.

    Returns:
        A new :class:`CostLineOverrideSnapshot` carrying every field
        needed for :func:`revert_last_override` to restore the line
        byte-identically.
    """
    return CostLineOverrideSnapshot(
        unit_cost=float(line.unit_cost),
        qty=float(line.quantity),
        total_cost=float(line.total_cost),
        notes=line.notes or "",
        cost_source_tier=line.cost_source_tier,
        price_confidence=float(line.price_confidence),
        combined_confidence=float(line.combined_confidence),
        cost_band=line.cost_band,
        suppressed=bool(line.suppressed),
        applied_at=applied_at or datetime.now(timezone.utc),
        source_tag=_extract_leading_source_tag(line.notes),
    )


def revert_last_override(line: CostLine) -> CostLineOverrideSnapshot | None:
    """Pop the stack-top override snapshot and restore ``line`` to it.

    Phase T6.4.d — per-line undo. The ``↶ revert`` affordance in the
    Streamlit Estimate tab calls this once per click; a bulk
    "revert all batch applies" iterates every line with a non-empty
    snapshot stack and calls this once per line. Mutates ``line``
    in place (Pydantic ``BaseModel`` is mutable by default and
    :class:`CostLine` does not opt into ``frozen``).

    Restoration order: pop the stack-top snapshot, then assign each
    snapshotted field back onto the line. Numeric fields are coerced
    via ``float(...)`` to match the line's original schema types
    (``CostLine.unit_cost`` / ``quantity`` / ``total_cost`` are
    ``float`` per :class:`CostLine`, even though the snapshot carries
    them as ``float`` too — the explicit coercion guards a future
    schema migration). Enum fields (``cost_source_tier`` /
    ``cost_band``) round-trip as enum instances.

    Notes are restored to the snapshot's ``notes`` string verbatim —
    that is the state we are rolling back to, including whatever
    head tag (or absence of one) was at position 0 at the time the
    snapshot was captured. The ``[manual-override]`` (or
    ``[batch]`` / ``[sub-quote]`` / ``[sub-quote-llm]``) head that
    THIS override layered on top is gone after revert.

    The returned snapshot carries the popped values so a downstream
    "undo of undo" / "show snapshot details" affordance can replay
    the operation later if the operator changes their mind.

    Args:
        line: The :class:`CostLine` to roll back. Mutated in place.

    Returns:
        The popped :class:`CostLineOverrideSnapshot`, or ``None`` when
        the line had no snapshots (line is at its priced-from-cost-DB
        defaults, OR the line predates Phase T6.4.d and was loaded
        from a saved JSON estimate without an ``override_snapshots``
        field).
    """
    snapshots = list(line.override_snapshots or [])
    if not snapshots:
        return None

    snapshot = snapshots.pop()

    # Restore each snapshotted field. The order here doesn't matter
    # mechanically (Pydantic doesn't run cross-field validators on
    # bare assignment) but tracks the field declaration order in
    # :class:`CostLineOverrideSnapshot` for readability.
    line.unit_cost = float(snapshot.unit_cost)
    line.quantity = float(snapshot.qty)
    line.total_cost = float(snapshot.total_cost)
    # The snapshot's ``notes`` is always a string (default ""); the
    # CostLine schema's ``notes`` field is ``Optional[str]``. Restore
    # ``None`` when the snapshot recorded an empty string so a line at
    # priced-from-cost-DB defaults (no notes) round-trips byte-identically
    # — Excel / PDF / UI readers treat empty-string and None differently.
    line.notes = None if snapshot.notes == "" else snapshot.notes
    line.cost_source_tier = snapshot.cost_source_tier
    line.price_confidence = float(snapshot.price_confidence)
    line.cost_band = snapshot.cost_band
    line.suppressed = bool(snapshot.suppressed)
    # combined_confidence is a derived @property — no need to assign;
    # the property recomputes from confidence × price_confidence.
    line.override_snapshots = snapshots

    return snapshot


def revert_last_override_in_estimate(
    estimate: Estimate,
    line_id: int | str,
) -> tuple[Estimate, CostLineOverrideSnapshot | None]:
    """Estimate-level wrapper around :func:`revert_last_override`.

    Mirrors the immutability convention of :func:`apply_manual_override`
    (returns a new :class:`Estimate`; does not mutate the input). Useful
    for callers that want to thread the revert through a session-state
    re-assignment without worrying about shared object identity.

    Args:
        estimate: The :class:`Estimate` to roll back. NOT mutated.
        line_id: ``int`` index OR ``str`` cost_source / description
            (same matching rules as :func:`apply_manual_override`).

    Returns:
        ``(new_estimate, popped_snapshot)``. ``popped_snapshot`` is
        ``None`` when the targeted line had no snapshots; ``new_estimate``
        in that case is identical to the input.
    """
    idx = _resolve_override_index(estimate, line_id)
    # Deep-copy the targeted line so we don't mutate the input estimate's
    # CostLine object; revert_last_override mutates in place.
    target = estimate.line_items[idx].model_copy(deep=True)
    snapshot = revert_last_override(target)
    if snapshot is None:
        return estimate, None
    new_lines = list(estimate.line_items)
    new_lines[idx] = target
    return estimate.model_copy(update={"line_items": new_lines}), snapshot
