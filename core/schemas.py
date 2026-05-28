"""Pydantic data models that flow through the pipeline.

Every stage produces / consumes one of these. Keeping the schema strict makes
the LLM extraction reliable: we hand the JSON shape to the model and validate
the result on the way back.
"""

from __future__ import annotations

from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


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
    pdf_path: str = ""                   # absolute / workspace-relative source path (for the deterministic pre-pass)
    page_index: int = 0                  # 0-based within the source PDF
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
    """One trade-specific bid package PDF *or* one supporting reference document.

    For trade packages (the common case): no measured quantities - they describe
    scope, exclusions, alternates and unit prices. They become the *budget
    shell* that real quantity takeoffs (from drawings) fill in later.

    For supporting documents (wage determinations, sample CSAs, HSP templates,
    tax-exemption certs, UGSC, etc.): `document_kind == "supporting_document"`
    routes them to a separate export channel so they don't pollute the trade
    Bid Packages table with `trade_name='other'` rows.

    Owner vs GC split (calibration v3): on government solicitations,
    `BidPackage.contractor` historically captured the *owning agency*
    (USFWS, ASU, TAMU). The field name implied the GC, conflating two
    distinct entities. `owner` and `gc` make the split explicit; `contractor`
    is preserved for backward compatibility and is auto-populated from
    `gc` (or vice-versa) by the model_validator below.
    """

    pdf_name: str
    package_number: Optional[str] = None      # e.g. "03.00"
    trade_name: Optional[str] = None          # e.g. "Turnkey Structural Concrete"
    project_name: Optional[str] = None        # e.g. "DISD John Lewis Social Justice Academy"
    project_number: Optional[str] = None      # e.g. "9A8001"
    project_location: Optional[str] = None    # e.g. "Dallas, TX"
    bid_due: Optional[str] = None             # date/time string
    # Owner / GC split. On government direct solicitations (USFWS, ASU, TAMU)
    # `owner` holds the agency/institution name and `gc` is typically None.
    # On private GMP-style packages `owner` is the developer / end client and
    # `gc` is the construction manager (Beck, JE Dunn, SSC).
    owner: Optional[str] = None               # e.g. "U.S. Fish & Wildlife Service" or "Angelo State University"
    gc: Optional[str] = None                  # e.g. "Beck Group" (None for direct gov solicitations)
    # DEPRECATED: prefer `gc`. Kept for backward compatibility with the three
    # active bid-prep workspaces (Angelo State, TAMU Harrington, USFWS San
    # Marcos). The model_validator below mirrors `contractor` <-> `gc` so old
    # payloads (LLM emits only `contractor`) and new payloads (LLM emits only
    # `gc`) both round-trip cleanly.
    contractor: Optional[str] = None          # DEPRECATED — use `gc`
    contact: Optional[str] = None             # contact name + email
    # Document kind — separates priced trade scopes from cross-cutting
    # reference docs (wage determinations, sample agreements, etc.).
    # "trade_package": a scope-of-work package the bidder prices.
    # "supporting_document": a reference / compliance document that applies
    # across all trades (Davis-Bacon wage determination, sample construction
    # services agreement, tax-exemption certificate, HSP form template,
    # Uniform General Conditions, etc.).
    document_kind: Literal["trade_package", "supporting_document"] = "trade_package"
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

    @model_validator(mode="after")
    def _backfill_contractor_gc(self) -> "BidPackage":
        """Backward-compat: keep `contractor` and `gc` in lock-step.

        * Legacy payload (LLM emitted only `contractor`): copy to `gc`.
        * New payload (LLM emitted only `gc`): copy to `contractor` so old
          consumers that still read `contractor` see the right value.
        * Both set: leave as-is. Caller wins.
        Neither field is ever cleared by this validator.
        """
        if self.contractor and not self.gc:
            self.gc = self.contractor
        elif self.gc and not self.contractor:
            self.contractor = self.gc
        return self


# ---------------------------------------------------------------------------
# Deterministic drawing pre-pass (F3)
# ---------------------------------------------------------------------------
#
# These mirror the dataclasses in `core.extraction.drawing_prepass` so the
# result can be serialised onto `SheetExtraction` and round-tripped through
# the JSON/Excel exports. The pre-pass extracts what is unambiguously
# present in the PDF's vector text (title block, dimensions, schedule
# tables) so that high-confidence pages can skip the vision-LLM entirely.


class TitleBlockData(BaseModel):
    project_name: Optional[str] = None
    project_number: Optional[str] = None
    sheet_number: Optional[str] = None         # e.g. "A101"
    sheet_title: Optional[str] = None
    discipline: Optional[str] = None           # "Architectural", "Structural", ...
    scale: Optional[str] = None                # e.g. "1/4\" = 1'-0\""
    scale_factor: Optional[float] = None       # paper inches per real-world inch
    date: Optional[str] = None
    revision: Optional[str] = None
    drawn_by: Optional[str] = None
    checked_by: Optional[str] = None


class Dimension(BaseModel):
    raw_text: str
    inches: float                              # normalized to inches
    kind: str                                  # "feet-inches", "decimal-feet", "metric"


class ScheduleRow(BaseModel):
    columns: dict[str, str] = Field(default_factory=dict)


class Schedule(BaseModel):
    kind: str                                  # "door", "window", "room", "finish", "unknown"
    headers: list[str] = Field(default_factory=list)
    rows: list[ScheduleRow] = Field(default_factory=list)
    source_page: int = 0


class DoorRecord(BaseModel):
    """One door extracted from a door-schedule table (Phase T1).

    Door schedules are the most schema-stable tabular artefact in any
    drawing set, so this record carries door-specific fields directly
    rather than the loose ``columns: dict[str, str]`` of generic
    :class:`ScheduleRow`. Raw cell text is preserved alongside parsed
    inches so a downstream auditor can confirm a unit conversion.
    """

    mark: str                                  # "101A", "D-101", ...
    type: Optional[str] = None                 # "HM", "WD", "ALUM", ...
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    thickness_in: Optional[float] = None
    width_raw: Optional[str] = None
    height_raw: Optional[str] = None
    material: Optional[str] = None
    frame: Optional[str] = None
    hardware_set: Optional[str] = None
    fire_rating: Optional[str] = None
    remarks: Optional[str] = None
    source_page: int = 0


class DoorScheduleResult(BaseModel):
    """Aggregate door-schedule pre-pass result for a drawing page (Phase T1).

    Attached alongside (not replacing) the generic :class:`Schedule` rows
    on :class:`DrawingPrepassResult` so the existing prepass surface keeps
    working while downstream takeoff (Phase T2) consumes the richer typed
    records.
    """

    pages: list[int] = Field(default_factory=list)
    doors: list[DoorRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class WindowRecord(BaseModel):
    """One window extracted from a window-schedule table (Phase T2.5).

    Window schedules share the same shape as door schedules but carry
    different specialty columns (``GLAZING`` / ``OPERATION`` / ``SILL`` /
    ``U-FACTOR`` / ``SHGC``). The model preserves the raw cell text in
    ``raw_cells`` alongside parsed dimensions so a downstream auditor can
    confirm a unit conversion or surface a column the extractor didn't
    know about.
    """

    mark: str                                  # "W-01", "A", "101", ...
    type: Optional[str] = None                 # "ALUM-S", "VINYL-DH", ...
    width_in: Optional[float] = None
    height_in: Optional[float] = None
    sill_height_in: Optional[float] = None
    width_raw: Optional[str] = None
    height_raw: Optional[str] = None
    sill_height_raw: Optional[str] = None
    glazing: Optional[str] = None              # "INSUL", "TINTED LOW-E", ...
    operation: Optional[str] = None            # "FIXED", "CASEMENT", "DH", ...
    frame: Optional[str] = None                # "ALUM", "VINYL", "WOOD", ...
    material: Optional[str] = None
    u_factor: Optional[float] = None
    shgc: Optional[float] = None               # Solar Heat Gain Coefficient
    remarks: Optional[str] = None
    raw_cells: dict[str, str] = Field(default_factory=dict)
    source_page: int = 0


class WindowScheduleResult(BaseModel):
    """Aggregate window-schedule pre-pass result for a drawing page (Phase T2.5).

    Attached alongside (not replacing) the generic :class:`Schedule` rows
    on :class:`DrawingPrepassResult` so the existing prepass surface keeps
    working while downstream takeoff (Phase T2.5 synthesis) consumes the
    richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    windows: list[WindowRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class FinishRecord(BaseModel):
    """One room's finishes extracted from a finish-schedule table (Phase T4).

    A finish schedule typically has columns
    ``ROOM #, ROOM NAME, FLOOR, BASE, WALL N/S/E/W, CEILING,
    CEILING HEIGHT, REMARKS``. Unlike door / window records (1:1 with
    a TakeoffItem) every FinishRecord fans out into 3-7 TakeoffItems
    downstream — one per finished surface.

    ``wall_finishes`` is keyed by compass direction (``"N"`` / ``"S"`` /
    ``"E"`` / ``"W"``); when the schedule uses a single ``WALL`` column
    the dict is populated with one ``"ALL"`` key, which the synthesiser
    collapses into a single wall item rather than four.
    """

    room_number: str                           # "101", "M101", ...
    room_name: Optional[str] = None
    floor_finish: Optional[str] = None         # "VCT-1", "CPT-1", "POL CONC", ...
    base_finish: Optional[str] = None          # "RB-1", "CB-1", ...
    wall_finishes: dict[str, str] = Field(default_factory=dict)
    ceiling_finish: Optional[str] = None       # "ACT-1", "GYP", "EXPOSED", ...
    ceiling_height_ft: Optional[float] = None
    ceiling_height_raw: Optional[str] = None
    area_sf: Optional[float] = None            # cross-referenced from a room
                                                 # schedule by Phase T5; left
                                                 # optional in T4.
    remarks: Optional[str] = None
    raw_cells: dict[str, str] = Field(default_factory=dict)
    source_page: int = 0


class FinishScheduleResult(BaseModel):
    """Aggregate finish-schedule pre-pass result for a drawing page (Phase T4).

    Attached alongside (not replacing) the generic :class:`Schedule` rows
    on :class:`DrawingPrepassResult` so the existing prepass surface keeps
    working while downstream takeoff (Phase T4 synthesis) consumes the
    richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    rooms: list[FinishRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class RoomRecord(BaseModel):
    """One room's geometry extracted from a room-schedule table (Phase T5).

    Room schedules supply the **area** and **ceiling height** that the
    Phase T4 finish synthesis needed to compute real SF quantities.
    A single ``RoomRecord`` joined to its matching ``FinishRecord``
    (by ``room_number``) lets the back-fill pass replace the
    ``quantity=0.0`` placeholder on every floor/base/wall/ceiling
    finish TakeoffItem with the right square-footage.

    ``perimeter_lf`` is optional — many schedules don't publish it but
    when present it lets the back-fill bypass the ``4 * sqrt(area)``
    square-room fallback for base and wall computations.
    """

    room_number: str                           # "101", "M101", ...
    room_name: Optional[str] = None
    area_sf: Optional[float] = None            # square feet, floor area
    perimeter_lf: Optional[float] = None       # linear feet (when published)
    ceiling_height_ft: Optional[float] = None
    ceiling_height_raw: Optional[str] = None
    occupancy_type: Optional[str] = None       # "OFFICE", "STORAGE", ...
    notes: Optional[str] = None
    raw_cells: dict[str, str] = Field(default_factory=dict)
    source_page: int = 0


class RoomScheduleResult(BaseModel):
    """Aggregate room-schedule pre-pass result for a drawing page (Phase T5).

    Attached alongside (not replacing) the generic :class:`Schedule`
    rows on :class:`DrawingPrepassResult` so the existing prepass
    surface keeps working while downstream takeoff (Phase T5 back-fill)
    consumes the richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    rooms: list[RoomRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class DrawingPrepassResult(BaseModel):
    """Snapshot of everything the deterministic pre-pass could pull off
    a single drawing page without invoking the vision LLM."""

    title_block: TitleBlockData = Field(default_factory=TitleBlockData)
    dimensions: list[Dimension] = Field(default_factory=list)
    schedules: list[Schedule] = Field(default_factory=list)
    quality_issues: list[str] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    door_schedule: Optional[DoorScheduleResult] = None  # T1 typed door records
    window_schedule: Optional[WindowScheduleResult] = None  # T2.5 typed window records
    finish_schedule: Optional[FinishScheduleResult] = None  # T4 typed finish records
    room_schedule: Optional[RoomScheduleResult] = None  # T5 typed room geometry


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
    # F3 — deterministic drawing pre-pass. `prepass` is the structured
    # snapshot regardless of whether the LLM was eventually invoked;
    # `lm_skipped` is True when prepass confidence cleared the threshold
    # and the LLM call was skipped entirely.
    prepass: Optional[DrawingPrepassResult] = None
    lm_skipped: bool = False
    dimensions: list[Dimension] = Field(default_factory=list)


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

    `suppressed` lines stay in `line_items` for visibility but are excluded
    from `Estimate` totals / rollups. The estimator sets this when a takeoff
    can't be safely priced (e.g. a unit mismatch against the cost-DB entry
    with no documented conversion factor) — see calibration v2 finding #4
    where a LF×TON multiplication landed a $34,608 phantom line in the
    headline subtotal.
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
    suppressed: bool = False               # True -> excluded from Estimate totals


class Estimate(BaseModel):
    project_name: str
    region_multiplier: float = 1.00
    contingency_pct: float = 10.0
    overhead_pct: float = 10.0
    profit_pct: float = 5.0

    line_items: list[CostLine] = Field(default_factory=list)

    @property
    def priced_line_items(self) -> list[CostLine]:
        """`line_items` minus any flagged `suppressed=True`.

        Used by every total / rollup so the user still sees suppressed lines
        in exports but they never inflate the headline number.
        """
        return [li for li in self.line_items if not li.suppressed]

    @property
    def suppressed_line_items(self) -> list[CostLine]:
        return [li for li in self.line_items if li.suppressed]

    @property
    def subtotal(self) -> float:
        return round(sum(li.total_cost for li in self.priced_line_items), 2)

    @property
    def by_division(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for li in self.priced_line_items:
            out[li.csi_division] = round(out.get(li.csi_division, 0.0) + li.total_cost, 2)
        return out

    @property
    def by_cost_category(self) -> dict[str, float]:
        """Roll up line totals by labor/material/equipment/sub/other."""
        out: dict[str, float] = {c.value: 0.0 for c in CostCategory}
        for li in self.priced_line_items:
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


# ---------------------------------------------------------------------------
# Client-quote configuration (F12 / F15)
# ---------------------------------------------------------------------------


class CompanyInfo(BaseModel):
    """Company / contractor branding block printed on every quote."""

    name: str = ""
    address_line_1: str = ""
    address_line_2: str = ""
    phone: str = ""
    email: str = ""
    website: str = ""
    license_number: str = ""
    logo_path: str = ""              # absolute or workspace-relative path; "" = skip


class ClientInfo(BaseModel):
    """Recipient block printed on the cover page."""

    name: str = ""                   # company / org / individual
    contact_name: str = ""           # primary point of contact
    address_line_1: str = ""
    address_line_2: str = ""
    phone: str = ""
    email: str = ""


class QuoteMeta(BaseModel):
    """Per-quote metadata: numbering, validity window, narrative blurbs."""

    quote_number: str = "AUTO"       # "AUTO" means derive from project + date at build time
    valid_until_days: int = 30
    scope_blurb: str = ""
    payment_terms_text: str = ""


class PaymentMilestone(BaseModel):
    """One row of the payment schedule.

    Either `percentage` or `amount` is populated depending on the parent
    schedule's mode. The unused field is left None.
    """

    label: str
    percentage: Optional[float] = None     # 0..100; used when parent mode == "percentage"
    amount: Optional[float] = None         # dollars; used when parent mode == "milestone"
    notes: str = ""


class PaymentSchedule(BaseModel):
    """Payment schedule attached to a quote (F15).

    Two modes:
      * `percentage` - each milestone has a `percentage` of the contract; the
        dollar amounts are computed at PDF-build time against the estimate's
        grand total.
      * `milestone`  - each milestone has a fixed dollar `amount`. Use
        `validate_against_total()` at render time to confirm the milestones
        cover the full contract value.
    """

    mode: Literal["percentage", "milestone"] = "percentage"
    milestones: list[PaymentMilestone] = Field(default_factory=list)

    @model_validator(mode="after")
    def _check_consistency(self) -> "PaymentSchedule":
        if not self.milestones:
            return self
        if self.mode == "percentage":
            for m in self.milestones:
                if m.percentage is None:
                    raise ValueError(
                        f"Milestone '{m.label}' is missing a percentage in percentage mode."
                    )
                if m.percentage < 0 or m.percentage > 100:
                    raise ValueError(
                        f"Milestone '{m.label}' percentage {m.percentage} out of range 0..100."
                    )
            total_pct = sum(m.percentage or 0.0 for m in self.milestones)
            if abs(total_pct - 100.0) > 0.5:
                raise ValueError(
                    f"Payment percentages must sum to 100 (got {total_pct:.2f})."
                )
        else:  # milestone
            for m in self.milestones:
                if m.amount is None:
                    raise ValueError(
                        f"Milestone '{m.label}' is missing an amount in milestone mode."
                    )
                if m.amount < 0:
                    raise ValueError(
                        f"Milestone '{m.label}' amount {m.amount} must be non-negative."
                    )
        return self

    def validate_against_total(self, contract_total: float, tolerance: float = 1.0) -> list[str]:
        """Return a list of human-readable warnings (empty when valid).

        Only meaningful in `milestone` mode. We don't raise so the PDF still
        renders; the caller decides whether to log or surface to the user.
        """
        warnings: list[str] = []
        if self.mode != "milestone":
            return warnings
        total = sum(m.amount or 0.0 for m in self.milestones)
        if abs(total - contract_total) > tolerance:
            warnings.append(
                f"Milestone amounts sum to ${total:,.2f} but contract total is "
                f"${contract_total:,.2f} (delta ${total - contract_total:+,.2f})."
            )
        return warnings


class QuoteConfig(BaseModel):
    """Top-level container persisted to `config/client_quote.json`."""

    company: CompanyInfo = Field(default_factory=CompanyInfo)
    client: ClientInfo = Field(default_factory=ClientInfo)
    quote_meta: QuoteMeta = Field(default_factory=QuoteMeta)
    payment_schedule: PaymentSchedule = Field(default_factory=PaymentSchedule)
    terms_text: str = ""
