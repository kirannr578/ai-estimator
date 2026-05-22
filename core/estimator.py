"""Apply unit costs to a `ProjectModel` to produce a priced `Estimate`.

Lookup order for each takeoff line:
  1. Exact CSI section match in `cost_database.json`.
  2. Keyword match within the same CSI division.
  3. Skip pricing (line is reported with $0 and a warning).
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from .schemas import CostCategory, CostLine, Estimate, TakeoffItem
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
) -> Estimate:
    db = cost_db or CostDatabase()
    line_items: list[CostLine] = []

    for t in project.takeoffs:
        entry, key = db.lookup(t)
        if entry is None:
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
            ))
            continue

        unit_cost = float(entry["unit_cost"]) * region_multiplier
        # Unit mismatches (e.g. takeoff is SF but DB entry is LF) get flagged,
        # not silently mispriced.
        unit_warning = ""
        if entry.get("unit", "").upper() != t.unit.upper():
            unit_warning = (
                f"Unit mismatch: takeoff is {t.unit}, cost-DB is {entry.get('unit')}. "
                f"Review before relying on this line."
            )

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
        total = round(unit_cost * ordered_qty, 2)
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
            notes=" | ".join(filter(None, [t.notes, unit_warning])) or None,
        ))

    # Sort: by division ascending, then by total_cost descending within division.
    line_items.sort(key=lambda li: (li.csi_division, -li.total_cost))

    return Estimate(
        project_name=project_name,
        region_multiplier=region_multiplier,
        contingency_pct=contingency_pct,
        overhead_pct=overhead_pct,
        profit_pct=profit_pct,
        line_items=line_items,
    )
