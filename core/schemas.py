"""Pydantic data models that flow through the pipeline.

Every stage produces / consumes one of these. Keeping the schema strict makes
the LLM extraction reliable: we hand the JSON shape to the model and validate
the result on the way back.
"""

from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


# ---------------------------------------------------------------------------
# Enumerations
# ---------------------------------------------------------------------------


class CostCategory(str, Enum):
    """Cross-cutting cost-type axis (orthogonal to CSI division).

    Useful for labor/material splits, change-order pricing and cash-flow
    projections.
    """

    LABOR = "labor"
    MATERIAL = "material"
    EQUIPMENT = "equipment"
    SUBCONTRACTOR = "subcontractor"
    OTHER = "other"


class Discipline(str, Enum):
    ARCHITECTURAL = "A"
    STRUCTURAL = "S"
    MECHANICAL = "M"
    ELECTRICAL = "E"
    PLUMBING = "P"
    CIVIL = "C"
    LANDSCAPE = "L"
    FIRE_PROTECTION = "FP"
    GENERAL = "G"
    INTERIORS = "I"
    UNKNOWN = "?"


class SheetType(str, Enum):
    COVER = "cover"
    INDEX = "index"
    GENERAL_NOTES = "general_notes"
    SITE_PLAN = "site_plan"
    DEMOLITION = "demolition"
    FLOOR_PLAN = "floor_plan"
    REFLECTED_CEILING = "reflected_ceiling_plan"
    ROOF_PLAN = "roof_plan"
    ELEVATION = "elevation"
    SECTION = "section"
    DETAIL = "detail"
    ENLARGED_PLAN = "enlarged_plan"
    SCHEDULE = "schedule"          # door / window / finish / equipment tables
    SPECIFICATION = "specification"  # narrative spec section
    STRUCTURAL_PLAN = "structural_plan"
    FOUNDATION_PLAN = "foundation_plan"
    FRAMING_PLAN = "framing_plan"
    MECHANICAL_PLAN = "mechanical_plan"
    ELECTRICAL_PLAN = "electrical_plan"
    PLUMBING_PLAN = "plumbing_plan"
    SINGLE_LINE_DIAGRAM = "single_line_diagram"
    RISER_DIAGRAM = "riser_diagram"
    BID_PACKAGE = "bid_package"        # trade-specific scope/bid form (no drawings)
    BID_FORM = "bid_form"              # blank bid form template
    PROJECT_MANUAL = "project_manual"  # contract exhibits, schedule, narrative
    UNKNOWN = "unknown"


# ---------------------------------------------------------------------------
# Sheet-level
# ---------------------------------------------------------------------------


class Sheet(BaseModel):
    """One page of one PDF, with its rendered image and embedded text."""

    model_config = ConfigDict(use_enum_values=True)

    pdf_name: str
    page_index: int                  # 0-based within the source PDF
    sheet_number: Optional[str] = None   # e.g. "A-101"
    title: Optional[str] = None          # e.g. "First Floor Plan"
    discipline: Discipline = Discipline.UNKNOWN
    sheet_type: SheetType = SheetType.UNKNOWN
    scale: Optional[str] = None          # e.g. "1/4\" = 1'-0\""
    width_pts: float = 0.0
    height_pts: float = 0.0
    image_path: str = ""                 # rendered PNG location
    embedded_text: str = ""              # vector text from the PDF (may be empty for scans)
    is_scanned: bool = False             # heuristic: no embedded text -> scanned

    @property
    def sheet_id(self) -> str:
        """Stable human-friendly identifier."""
        if self.sheet_number:
            return self.sheet_number
        return f"{self.pdf_name}#p{self.page_index + 1}"


# ---------------------------------------------------------------------------
# Domain entities extracted from sheets
# ---------------------------------------------------------------------------


class Room(BaseModel):
    name: str
    number: Optional[str] = None
    area_sqft: Optional[float] = None
    perimeter_ft: Optional[float] = None
    ceiling_height_ft: Optional[float] = None
    floor_finish: Optional[str] = None
    base_finish: Optional[str] = None
    wall_finish: Optional[str] = None
    ceiling_finish: Optional[str] = None
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


class DoorEntry(BaseModel):
    mark: str                              # e.g. "101A"
    type: Optional[str] = None             # e.g. "SC HM"
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    rating: Optional[str] = None           # e.g. "20-min"
    hardware_set: Optional[str] = None
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


class WindowEntry(BaseModel):
    mark: str
    type: Optional[str] = None
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    glazing: Optional[str] = None
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


class StructuralElement(BaseModel):
    kind: str                              # footing, column, beam, slab, joist
    mark: Optional[str] = None
    material: Optional[str] = None         # concrete, steel, wood, masonry
    size: Optional[str] = None             # "W12x26", "8\" CMU", "2x10"
    quantity: float = 0.0
    unit: str = "EA"                       # EA, LF, SF, CY
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


class MEPItem(BaseModel):
    discipline: Discipline                 # M / E / P / FP
    category: str                          # "fixture", "equipment", "panel", "duct", "pipe"
    description: str
    quantity: float = 0.0
    unit: str = "EA"
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


class SpecSection(BaseModel):
    csi_section: str                       # e.g. "09 91 23"
    title: str                             # e.g. "Interior Painting"
    summary: Optional[str] = None
    requirements: list[str] = Field(default_factory=list)
    source_sheet_id: Optional[str] = None


class SiteInfo(BaseModel):
    site_area_sqft: Optional[float] = None
    paving_area_sqft: Optional[float] = None
    sidewalk_lf: Optional[float] = None
    landscaping_area_sqft: Optional[float] = None
    notes: Optional[str] = None
    source_sheet_id: Optional[str] = None


# ---------------------------------------------------------------------------
# Bid-package entities
# ---------------------------------------------------------------------------


class Alternate(BaseModel):
    """Project-wide add/deduct alternate referenced inside a bid package."""

    number: Optional[str] = None       # e.g. "Alt #1"
    description: str
    add_or_deduct: Optional[str] = None  # "Add", "Deduct", or None
    amount: Optional[float] = None     # known dollar amount, if any


class UnitPrice(BaseModel):
    """Unit-price line item solicited inside a bid package."""

    description: str
    unit: Optional[str] = None         # CY, EA, LF, TON, SQ, SACK, etc.
    amount: Optional[float] = None     # known $ if pre-filled


class ScopeItem(BaseModel):
    """A single inclusion or exclusion line aggregated across all bid packages.

    `source_packages` lists every bid-package pdf_name whose inclusions /
    exclusions list contained a fuzzy match for `text`. Used by the
    project-level "Scope Coverage" view to surface what is and is not in
    aggregate scope, with traceability back to the originating package.
    """

    text: str
    source_packages: list[str] = Field(default_factory=list)


class BidPackage(BaseModel):
    """One trade-specific bid package PDF.

    Bid packages have no measured quantities - they describe scope, exclusions,
    alternates and unit prices. They become the *budget shell* that real
    quantity takeoffs (from drawings) fill in later.
    """

    pdf_name: str
    package_number: Optional[str] = None      # e.g. "03.00"
    trade_name: Optional[str] = None          # e.g. "Turnkey Structural Concrete"
    project_name: Optional[str] = None        # e.g. "DISD John Lewis Social Justice Academy"
    project_number: Optional[str] = None      # e.g. "9A8001"
    project_location: Optional[str] = None    # e.g. "Dallas, TX"
    bid_due: Optional[str] = None             # date/time string
    contractor: Optional[str] = None          # e.g. "BECK 3I JOINT VENTURE"
    contact: Optional[str] = None             # contact name + email
    csi_divisions: list[str] = Field(default_factory=list)   # ["03", "31"]
    csi_sections: list[str] = Field(default_factory=list)    # ["03 30 00", "31 63 29"]
    inclusions: list[str] = Field(default_factory=list)
    exclusions: list[str] = Field(default_factory=list)
    alternates: list[Alternate] = Field(default_factory=list)
    unit_prices: list[UnitPrice] = Field(default_factory=list)
    second_tier_required: bool = False
    referenced_drawings: list[str] = Field(default_factory=list)   # e.g. ["A-111Ga"]
    referenced_specs: list[str] = Field(default_factory=list)      # e.g. ["098116"]
    summary: Optional[str] = None
    warnings: list[str] = Field(default_factory=list)


class SheetExtraction(BaseModel):
    """Everything extracted from a single sheet (or whole bid-package PDF)."""

    sheet_id: str
    summary: str = ""                      # one-paragraph human description
    rooms: list[Room] = Field(default_factory=list)
    doors: list[DoorEntry] = Field(default_factory=list)
    windows: list[WindowEntry] = Field(default_factory=list)
    structural: list[StructuralElement] = Field(default_factory=list)
    mep: list[MEPItem] = Field(default_factory=list)
    spec_sections: list[SpecSection] = Field(default_factory=list)
    site: Optional[SiteInfo] = None
    bid_package: Optional[BidPackage] = None   # set when the source was a bid-package PDF
    raw_takeoffs: list["TakeoffItem"] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Takeoff & estimate
# ---------------------------------------------------------------------------


class TakeoffItem(BaseModel):
    """A measured quantity not yet priced."""

    csi_division: str                      # "09" - two-digit MasterFormat division
    csi_section: Optional[str] = None      # "09 91 23" - full six-digit if known
    description: str
    quantity: float
    unit: str                              # SF, LF, CY, EA, TON, HR, LS
    confidence: float = 0.7                # 0..1, how sure the extractor was
    source_sheet_ids: list[str] = Field(default_factory=list)
    notes: Optional[str] = None


class CostLine(BaseModel):
    """Priced takeoff line.

    `quantity` is the *ordered* quantity (raw_quantity * waste_factor) which
    is what gets multiplied by `unit_cost` to land at `total_cost`. The
    un-padded measurement is preserved in `raw_quantity` for audit and so
    downstream consumers can re-derive waste without re-running the pipeline.
    """

    csi_division: str
    csi_section: Optional[str] = None
    description: str
    quantity: float
    unit: str
    unit_cost: float
    total_cost: float
    cost_category: CostCategory = CostCategory.OTHER
    raw_quantity: Optional[float] = None   # measured quantity before waste padding
    waste_factor: float = 1.0              # >= 1.0; quantity = raw_quantity * waste_factor
    confidence: float = 0.7
    source_sheet_ids: list[str] = Field(default_factory=list)
    cost_source: str = ""                  # which cost-db key was used
    notes: Optional[str] = None


class Estimate(BaseModel):
    project_name: str
    region_multiplier: float = 1.00
    contingency_pct: float = 10.0
    overhead_pct: float = 10.0
    profit_pct: float = 5.0

    line_items: list[CostLine] = Field(default_factory=list)

    @property
    def subtotal(self) -> float:
        return round(sum(li.total_cost for li in self.line_items), 2)

    @property
    def by_division(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for li in self.line_items:
            out[li.csi_division] = round(out.get(li.csi_division, 0.0) + li.total_cost, 2)
        return out

    @property
    def by_cost_category(self) -> dict[str, float]:
        """Roll up line totals by labor/material/equipment/sub/other."""
        out: dict[str, float] = {c.value: 0.0 for c in CostCategory}
        for li in self.line_items:
            key = li.cost_category.value if isinstance(li.cost_category, CostCategory) else str(li.cost_category)
            out[key] = round(out.get(key, 0.0) + li.total_cost, 2)
        return {k: v for k, v in out.items() if v > 0}

    @property
    def contingency(self) -> float:
        return round(self.subtotal * self.contingency_pct / 100.0, 2)

    @property
    def overhead(self) -> float:
        return round((self.subtotal + self.contingency) * self.overhead_pct / 100.0, 2)

    @property
    def profit(self) -> float:
        return round(
            (self.subtotal + self.contingency + self.overhead) * self.profit_pct / 100.0,
            2,
        )

    @property
    def grand_total(self) -> float:
        return round(self.subtotal + self.contingency + self.overhead + self.profit, 2)


# Resolve forward reference (TakeoffItem used inside SheetExtraction).
SheetExtraction.model_rebuild()
