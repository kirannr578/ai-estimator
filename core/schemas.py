"""Pydantic data models that flow through the pipeline.

Every stage produces / consumes one of these. Keeping the schema strict makes
the LLM extraction reliable: we hand the JSON shape to the model and validate
the result on the way back.
"""

from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


# Phase T6.4.d — per-line undo cap. Each :class:`CostLine` keeps at most
# this many :class:`CostLineOverrideSnapshot` entries on its
# ``override_snapshots`` stack; older entries are dropped FIFO when the
# cap is exceeded so a pathological re-apply loop (200-row vendor batch
# accidentally re-applied 50 times) cannot grow the line's memory
# footprint without bound. Calibration intent: typical override-chain
# depth on a real bid is 1-3 (priced-from-cost-DB → vendor batch →
# manual override on top). 10 leaves comfortable headroom while still
# bounding the worst case.
MAX_OVERRIDE_SNAPSHOTS: int = 10


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


class CostBand(str, Enum):
    """Confidence band assigned to a priced ``CostLine`` (Phase T6).

    The band drives downstream routing in exports and the Streamlit UI:

    * ``AUTO_APPROVE`` — confidence ≥ 0.85; rolls into the headline cost
      and is the default for the conservative grand-total (``grand_total_auto_only``).
    * ``OPERATOR_REVIEW`` — 0.65 ≤ confidence < 0.85; rolls into the
      headline cost ("if reviewer signs off" total) but is flagged in
      exports + UI so the estimator eyeballs the row before submitting.
    * ``HAND_TAKEOFF`` — confidence < 0.65 OR the line was
      ``suppressed=True`` by the unit-mismatch path; excluded from every
      grand-total and surfaced as a "needs manual takeoff" worklist.

    Thresholds are deliberately the same constants used by the prepass
    confidence rubric (``drawing_prepass._score``) and the back-fill
    confidence rubric (``takeoff_backfill._BACKFILL_CONF_FALLBACK``) so a
    perimeter-fallback row ends up in OPERATOR_REVIEW by construction.

    Phase T7: the threshold input is now ``combined_confidence``
    (= ``qty_confidence × price_confidence``), so a low-quality cost
    lookup can demote an otherwise-high-confidence quantity into a
    lower band even when the takeoff itself was crisp. Backward-compat
    is preserved by ``CostLine.price_confidence`` defaulting to ``1.0``,
    which collapses ``combined`` back to ``qty_confidence`` for every
    pre-T7 fixture / test that didn't set it explicitly.
    """

    AUTO_APPROVE = "auto_approve"
    OPERATOR_REVIEW = "operator_review"
    HAND_TAKEOFF = "hand_takeoff"


class CostSourceTier(str, Enum):
    """Catalog-completeness tier assigned to a priced ``CostLine`` (Phase T7).

    Independent of the qty-confidence axis (which lives in
    :class:`CostBand`) and the unit-mismatch axis (which lives in
    ``CostLine.suppressed``). Together they form a 3-way classification
    of "how good is this priced row?":

    * **EXACT_MATCH** — the cost lookup landed a direct CWICR hit with
      similarity ≥ 0.92, OR the takeoff hit the bundled seed
      ``cost_database.json`` (which is hand-curated against MasterFormat
      sections, so any seed-DB hit is treated as exact).
    * **CATEGORY_MATCH** — CWICR similarity in [0.75, 0.92); same CSI
      section family but the specific item description doesn't perfectly
      align (e.g. takeoff says "interior latex paint", catalog says
      "primer + 2 coats latex"). Price is usable but the reviewer should
      eyeball the line.
    * **INTERPOLATED** — CWICR similarity in [0.50, 0.75) (well above
      the 0.55 minimum-similarity threshold but below category-match
      quality). Treated as a region-adjusted neighbour: the price is a
      rough proxy, not a direct quote.
    * **PARAMETRIC** — fell back to the parametric path: CWICR similarity
      below 0.50 (rare given ``CWICR_MIN_SIMILARITY`` defaults to 0.55)
      or a future ``$/SF default for the trade``-style fallback. Lowest
      price-confidence.
    * **MANUAL_OVERRIDE** — the operator hand-set the unit cost via the
      Streamlit "Recalculate totals" affordance (or via a downstream
      override mechanism). ``price_confidence`` is forced to 1.0 by
      convention — the operator vouches for the number.
    * **MISSING** — no cost data was available at all (no CWICR hit,
      no seed-DB hit). ``total_cost == 0``; mirrors the ``suppressed=True``
      semantics for "informational, not in totals". Unit-mismatch
      suppressed lines also resolve to MISSING because the cost
      effectively wasn't usable.

    The brief's similarity-to-tier mapping (Phase T7 spec):

    +-----------------+-----------------+----------------------+
    | similarity      | tier            | price_confidence     |
    +=================+=================+======================+
    | ≥ 0.92          | EXACT_MATCH     | similarity (0.92–1.0)|
    +-----------------+-----------------+----------------------+
    | [0.75, 0.92)    | CATEGORY_MATCH  | similarity × 0.85    |
    +-----------------+-----------------+----------------------+
    | [0.50, 0.75)    | INTERPOLATED    | 0.65                 |
    +-----------------+-----------------+----------------------+
    | < 0.50          | PARAMETRIC      | 0.45                 |
    +-----------------+-----------------+----------------------+

    ``EXACT_MATCH`` from the seed DB carries a fixed
    ``price_confidence = 0.95`` — slightly discounted from 1.0 because
    the seed catalog isn't comprehensive, even though every entry is
    hand-curated.
    """

    EXACT_MATCH = "exact_match"
    CATEGORY_MATCH = "category_match"
    INTERPOLATED = "interpolated"
    PARAMETRIC = "parametric"
    MANUAL_OVERRIDE = "manual_override"
    MISSING = "missing"


# Phase T6 band thresholds. Exposed at module-level so tests + downstream
# callers (e.g. ``app.py``) can reference the exact boundaries rather than
# hard-coding them in two places.
COST_BAND_AUTO_THRESHOLD: float = 0.85
COST_BAND_REVIEW_THRESHOLD: float = 0.65

# Phase T7 catalog-completeness thresholds. The CWICR similarity input is
# bucketed into the four cost-source tiers below; the tier in turn drives
# the ``price_confidence`` value that multiplies into ``combined_confidence``
# for band assignment. Exposed as module-level constants so tests + the
# CWICR ↔ tier bridge in ``core.estimator`` reference the same numbers.
COST_TIER_EXACT_THRESHOLD: float = 0.92          # ≥ → EXACT_MATCH
COST_TIER_CATEGORY_THRESHOLD: float = 0.75       # ≥ → CATEGORY_MATCH (and < EXACT)
COST_TIER_INTERPOLATED_THRESHOLD: float = 0.50   # ≥ → INTERPOLATED (and < CATEGORY)

# Per-tier ``price_confidence`` constants for the non-EXACT branches.
# EXACT_MATCH maps to the *similarity* itself (so 0.95 sim → 0.95 price_conf).
# Seed-DB hits (always EXACT_MATCH per the contract) get this fixed discount
# instead — a tiny haircut from 1.0 because the seed catalog isn't
# comprehensive even though every entry is hand-curated.
COST_TIER_SEED_DB_PRICE_CONFIDENCE: float = 0.95
COST_TIER_CATEGORY_MULTIPLIER: float = 0.85      # similarity × this → price_conf
COST_TIER_INTERPOLATED_PRICE_CONFIDENCE: float = 0.65
COST_TIER_PARAMETRIC_PRICE_CONFIDENCE: float = 0.45


def price_confidence_from_similarity(
    similarity: float,
) -> tuple["CostSourceTier", float]:
    """Map a CWICR similarity in [0, 1] to (tier, price_confidence).

    Boundaries are inclusive on the upper-tier side, mirroring the
    ``band_for_confidence`` convention:

    * 0.92         → ``EXACT_MATCH``     (price_conf = similarity)
    * 0.75 .. 0.92 → ``CATEGORY_MATCH``  (price_conf = similarity × 0.85)
    * 0.50 .. 0.75 → ``INTERPOLATED``    (price_conf = 0.65)
    * < 0.50       → ``PARAMETRIC``      (price_conf = 0.45)

    The CWICR matcher's minimum-similarity threshold (default 0.55) means
    the PARAMETRIC branch is rarely exercised in practice — a CWICR
    candidate below 0.55 is rejected upstream and the caller falls
    through to the seed DB instead. The branch is kept here so the
    function's contract is total over [0, 1] for tests + future callers
    that lower the threshold.
    """
    sim = max(0.0, min(1.0, float(similarity)))
    if sim >= COST_TIER_EXACT_THRESHOLD:
        return CostSourceTier.EXACT_MATCH, sim
    if sim >= COST_TIER_CATEGORY_THRESHOLD:
        return CostSourceTier.CATEGORY_MATCH, round(
            sim * COST_TIER_CATEGORY_MULTIPLIER, 4
        )
    if sim >= COST_TIER_INTERPOLATED_THRESHOLD:
        return CostSourceTier.INTERPOLATED, COST_TIER_INTERPOLATED_PRICE_CONFIDENCE
    return CostSourceTier.PARAMETRIC, COST_TIER_PARAMETRIC_PRICE_CONFIDENCE


def band_for_confidence(
    confidence: float | None,
    *,
    suppressed: bool = False,
) -> CostBand:
    """Map a CostLine's ``confidence`` (+ suppression flag) to a band.

    The single source of truth for the threshold semantics — used by
    ``price_takeoff`` when constructing CostLines and by the exporter /
    Streamlit code when re-banding hand-edited rows.

    Rules (in priority order):

    1. ``suppressed=True`` always wins → ``HAND_TAKEOFF``. A unit-mismatch
       line carries ``total_cost=0`` already (see
       ``core.estimator._build_cwicr_line`` / the seed-DB suppression
       branch) so it cannot inflate any total, but routing it to
       ``HAND_TAKEOFF`` keeps the worklist honest about manual eyes
       needed.
    2. ``confidence is None`` → ``OPERATOR_REVIEW`` (conservative default
       for the legacy LLM-extracted, pre-T1 codepath where the source
       ``TakeoffItem`` carried no confidence at all).
    3. ``confidence >= 0.85`` → ``AUTO_APPROVE``.
    4. ``confidence >= 0.65`` → ``OPERATOR_REVIEW``.
    5. otherwise                → ``HAND_TAKEOFF``.
    """
    if suppressed:
        return CostBand.HAND_TAKEOFF
    if confidence is None:
        return CostBand.OPERATOR_REVIEW
    if confidence >= COST_BAND_AUTO_THRESHOLD:
        return CostBand.AUTO_APPROVE
    if confidence >= COST_BAND_REVIEW_THRESHOLD:
        return CostBand.OPERATOR_REVIEW
    return CostBand.HAND_TAKEOFF


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


# ---------------------------------------------------------------------------
# Phase T9.0 — bid alternates / value-engineering pricing
# ---------------------------------------------------------------------------
#
# The pre-T9.0 `Alternate` (above) is the *informational* form that the
# bid-package extractor has emitted since calibration v1 — it carries the
# narrative description plus an optional dollar amount with no signed-cost
# semantics. T9.0 introduces a parallel, *priceable* shape with explicit
# type-tagging, a signed `cost_delta`, and traceability fields the
# estimator can consume to fold the alternate into a parallel
# `Estimate.alternates` rollup. The legacy `Alternate` is unchanged so
# every pre-T9.0 export, fixture, and Excel "Scope Matrix" row keeps
# rendering exactly as before.


class AlternateType(str, Enum):
    """Classification of a bid alternate line.

    Mirrors the four forms real federal / state bid forms enumerate:

    * **ADDITIVE** — extra scope priced separately ("Alternate #1: ADD
      epoxy floor coating to mechanical rooms, +$X"). `cost_delta`
      should be non-negative.
    * **DEDUCTIVE** — scope reduction priced as savings ("Alternate #2:
      DEDUCT skylight system, -$X"). `cost_delta` should be non-positive
      (the savings appear as a negative dollar amount, so the math
      ``subtotal_with_alternates_selected = subtotal_base_only + sum(deltas)``
      naturally subtracts).
    * **SUBSTITUTION** — material / system swap with a net delta after
      netting the cost of the removed scope ("Alternate #3: SUBSTITUTE
      LVT flooring for VCT, net ±$X"). `cost_delta` is the NET signed
      delta; it can be either positive (substitution costs more) or
      negative (substitution saves money).
    * **VE** — Value Engineering suggestion, typically a post-award
      negotiation surface but occasionally solicited at bid time. VE
      items behave numerically like DEDUCTIVE (savings → negative
      delta) but are tagged separately so the downstream UI / PDF
      can group them under a "Value Engineering" header rather than
      lumping them with the architect-authored deductive alternates.

    The numeric math (`subtotal_with_alternates_selected`,
    `total_with_alternates_selected`) treats VE identically to
    DEDUCTIVE — both contribute a (typically negative) `cost_delta`
    to the rollup. Type is preserved for downstream grouping only.
    """

    ADDITIVE = "additive"
    DEDUCTIVE = "deductive"
    SUBSTITUTION = "substitution"
    VE = "value_engineering"


class AlternatePricingBasis(str, Enum):
    """How a priced :class:`AlternateLineEstimate` got its dollar value.

    Distinct from :class:`CostSourceTier` (which lives on every priced
    line item and tracks CWICR / seed-DB completeness) — alternates have
    a much narrower set of provenance signals because the bid form
    itself is the canonical source of the printed dollar amount.

    * **EXTRACTED_FROM_BID_FORM** — the `AlternateLine.cost_delta` came
      out of a printed dollar value on the bid form (rare: most bid
      forms print blank fillable lines and ask the bidder to fill in
      the price).
    * **OPERATOR_ENTERED** — the operator hand-entered `cost_delta`
      via the (deferred T9.1) Streamlit toggle UI or via a vendor /
      subcontractor quote outside the bid-form extraction path.
      Numerically indistinguishable from EXTRACTED_FROM_BID_FORM, but
      the audit trail differs.
    * **SYNTHESIZED_FROM_TAKEOFF** — `cost_delta` was computed by
      summing the priced takeoff items referenced in
      `AlternateLine.related_takeoff_items`. Used when the bid form
      enumerates the alternate description but no price (and the
      project model carries enough takeoff detail to estimate the
      delta locally).
    * **MISSING** — neither `cost_delta` nor `related_takeoff_items`
      were populated. Surfaced in the operator-review queue so the
      estimator can supply a number before submitting the bid.
    """

    EXTRACTED_FROM_BID_FORM = "extracted_from_bid_form"
    OPERATOR_ENTERED = "operator_entered"
    SYNTHESIZED_FROM_TAKEOFF = "synthesized_from_takeoff"
    MISSING = "missing"


class AlternateLine(BaseModel):
    """One bid-alternate line item (Phase T9.0).

    Source-of-truth fields are populated by the deterministic
    bid-form alternates extractor in
    :mod:`core.extraction.bid_form_alternates` (and its LLM-fallback
    sibling); the estimator (:func:`core.estimator.price_alternates`)
    reads them to produce :class:`AlternateLineEstimate` rows that
    fold into the parallel :pyattr:`Estimate.alternates` rollup.

    The base estimate (``Estimate.subtotal``, ``Estimate.grand_total``)
    is **NOT** modified by an alternate's presence — alternates are
    priced separately and surfaced via
    :meth:`Estimate.subtotal_with_alternates_selected` so the headline
    base bid stays as-is (matching real federal / state bid practice:
    you bid the base, alternates are at owner option). The single
    exception is when ``included_by_default=True``; see the field
    documentation below.

    Numeric sign convention for ``cost_delta``:

    * ADDITIVE → ``cost_delta >= 0`` (adds to base)
    * DEDUCTIVE → ``cost_delta <= 0`` (subtracts from base; savings)
    * SUBSTITUTION → signed net delta (either direction)
    * VE → typically ``cost_delta <= 0`` (savings)

    A validator (``_validate_sign_consistency``) emits a Pydantic
    warning when type and sign disagree but does NOT raise — real
    bid forms sometimes print a positive absolute value with a
    separate ADD/DEDUCT label, and the operator or extractor is
    free to keep that convention. Downstream callers
    (``price_alternates``) trust the sign of ``cost_delta`` as-is.
    """

    alternate_id: str = Field(
        ...,
        description=(
            "Human-readable identifier from the bid form. Examples: "
            "'Alternate #1', 'Alt 1', 'Add Alternate A', 'VE-3', "
            "'Bid Alternate B'. Used as the stable key for selection / "
            "deselection and as the cross-bid-package dedupe key."
        ),
    )
    alternate_type: AlternateType = AlternateType.ADDITIVE
    description: str = Field(
        ...,
        description="Free-text description copied verbatim from the bid form.",
    )
    scope_summary: Optional[str] = Field(
        default=None,
        description=(
            "1-2 sentence summary (LLM-distilled or copied verbatim). "
            "Used in the Excel + PDF + UI surface so the reader sees a "
            "compact narrative even when ``description`` is long."
        ),
    )
    cost_delta: Optional[float] = Field(
        default=None,
        description=(
            "Signed dollar amount. Positive = adds cost (ADDITIVE), "
            "negative = saves cost (DEDUCTIVE / VE). For SUBSTITUTION "
            "this is the NET delta after netting the cost of removed "
            "scope. ``None`` means the bid form left the field blank — "
            "the estimator may synthesize a value from "
            "``related_takeoff_items`` or surface the line as MISSING."
        ),
    )
    included_by_default: bool = Field(
        default=False,
        description=(
            "Whether this alternate is pre-priced into the base estimate. "
            "Default ``False`` — alternates surface separately and "
            "operators opt them in via the (deferred T9.1) UI. ``True`` "
            "indicates the alternate's dollar delta is ALREADY in "
            "``Estimate.subtotal`` and the operator can opt OUT. Rare; "
            "some federal RFPs use this for a base-bid-includes-Option-A "
            "convention."
        ),
    )
    related_takeoff_items: list[str] = Field(
        default_factory=list,
        description=(
            "Optional list of takeoff entity ids (csi_section / mark / "
            "description hash) the alternate affects. When populated and "
            "``cost_delta`` is ``None``, the estimator sums the priced "
            "rows for these items to synthesize a ``cost_delta`` and "
            "tags the resulting AlternateLineEstimate with "
            ":attr:`AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF`."
        ),
    )
    related_csi: list[str] = Field(
        default_factory=list,
        description=(
            "Optional list of CSI codes the alternate touches "
            "(e.g. '09 65 19' for LVT flooring on a flooring "
            "substitution). Surfaced in the Excel + PDF for "
            "traceability; never used in the numeric math."
        ),
    )
    bid_package_id: Optional[str] = Field(
        default=None,
        description=(
            "Which :class:`BidPackage` this alternate belongs to "
            "(``pdf_name`` or ``package_number``). Used by the "
            "cross-bid-package aggregator to deduplicate alternates "
            "that appear in multiple bid forms. ``None`` means the "
            "alternate is not attributed to any specific package and "
            "is grouped under 'general' in the aggregator."
        ),
    )
    source_sheet: Optional[str] = Field(
        default=None,
        description=(
            "Page reference for traceability (e.g. 'Bid Form p.3'). "
            "Surfaced in the Excel + PDF for the audit trail; never "
            "used in the numeric math."
        ),
    )
    confidence: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description=(
            "Extraction confidence in [0.0, 1.0]. The deterministic "
            "regex parser emits ~0.85-0.90 for a clean parse with "
            "both type and delta extracted; the LLM-fallback path "
            "emits ~0.70 (lower because the model occasionally "
            "guesses on ambiguous wording). Used by the Excel + "
            "PDF to highlight low-confidence alternate rows."
        ),
    )
    operator_notes: Optional[str] = Field(
        default=None,
        description="Free-form operator commentary. Never read by the math.",
    )

    @model_validator(mode="after")
    def _validate_sign_consistency(self) -> "AlternateLine":
        """Soft sign-vs-type check — sets ``operator_notes`` warning.

        Does NOT raise. Real bid forms occasionally print a positive
        absolute value alongside a separate ADD/DEDUCT label and the
        downstream pipeline needs to tolerate both conventions. When
        the sign disagrees with the type, we leave the values
        as-given and prepend a ``[sign-warning]`` note so a downstream
        reviewer can spot the inconsistency.
        """
        if self.cost_delta is None:
            return self
        if self.alternate_type == AlternateType.ADDITIVE and self.cost_delta < 0:
            note = (
                "[sign-warning] ADDITIVE alternate with negative cost_delta; "
                "verify sign — the bid form may have printed the savings "
                "label separately."
            )
            self.operator_notes = (
                f"{self.operator_notes} | {note}" if self.operator_notes else note
            )
        elif self.alternate_type == AlternateType.DEDUCTIVE and self.cost_delta > 0:
            note = (
                "[sign-warning] DEDUCTIVE alternate with positive cost_delta; "
                "verify sign — the bid form may have printed the magnitude "
                "with the DEDUCT label separately."
            )
            self.operator_notes = (
                f"{self.operator_notes} | {note}" if self.operator_notes else note
            )
        return self


class AlternateLineEstimate(BaseModel):
    """Priced view of one :class:`AlternateLine` (Phase T9.0).

    Built by :func:`core.estimator.price_alternates` and attached to
    :pyattr:`Estimate.alternates`. Carries the resolved dollar delta
    plus a :class:`AlternatePricingBasis` tag so the Excel + PDF + UI
    can show *how* the number was derived (printed on the bid form,
    operator-entered, synthesized from takeoff, or missing entirely).
    """

    alternate_id: str
    alternate_type: AlternateType
    description: str
    cost_delta: Optional[float] = Field(
        default=None,
        description=(
            "Resolved signed dollar amount, mirroring the contract of "
            ":pyattr:`AlternateLine.cost_delta`. ``None`` only when the "
            "pricing basis is :attr:`AlternatePricingBasis.MISSING`."
        ),
    )
    pricing_basis: AlternatePricingBasis = AlternatePricingBasis.MISSING
    confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    included_in_base: bool = Field(
        default=False,
        description=(
            "Current toggle state — whether this alternate is rolled "
            "into the base bid right now. Mirrors "
            ":pyattr:`AlternateLine.included_by_default` at estimate-"
            "build time; the (deferred T9.1) UI lets an operator flip "
            "this at runtime via "
            ":meth:`Estimate.subtotal_with_alternates_selected`."
        ),
    )
    bid_package_id: Optional[str] = None
    source_sheet: Optional[str] = None
    related_csi: list[str] = Field(default_factory=list)
    operator_notes: Optional[str] = None


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
    # Phase T5.1: room this door opens INTO. Populated when the door
    # schedule carries a ``ROOM`` / ``RM`` / ``LOCATION`` column. Used
    # by ``backfill_finish_quantities`` to attribute opening SF to the
    # right room's wall area; left ``None`` when the schedule omitted
    # the column (the back-fill then annotates with ``openings_partial``
    # rather than deducting).
    room_number: Optional[str] = None
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
    # Phase T5.1: room this window opens INTO. Populated when the window
    # schedule carries a ``ROOM`` / ``RM`` / ``LOCATION`` column (less
    # common than on door schedules). Used by ``backfill_finish_quantities``
    # to attribute opening SF to the room's wall area.
    room_number: Optional[str] = None
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


class CircuitEntry(BaseModel):
    """One row in an electrical panel schedule's circuit table (Phase T2.6).

    A 3-pole breaker carries the same load across phases ``A,B,C``;
    ``phase`` is the literal text of the schedule's PHASE column so the
    multi-pole case round-trips without lossy parsing. ``circuit_number``
    is also stored as-published (``"1"``, ``"1,3,5"``, ``"21"``) for the
    same reason.
    """

    circuit_number: str                        # "1", "1,3,5", "21", ...
    breaker_amps: Optional[int] = None         # 20, 30, 50, ...
    load_description: str
    load_watts: Optional[float] = None
    phase: Optional[str] = None                # "A", "B", "C", "A,B,C", ...


class PanelRecord(BaseModel):
    """One electrical panel pulled off a panel schedule (Phase T2.6).

    Electrical panel schedules are the highest-dollar single drawing
    artefact in BPC's calibration set — each panel synthesises into
    four families of TakeoffItem (panel enclosure, branch breakers,
    feeder conductor, feeder conduit). Phase T2.6 is the EA-unit
    dispatcher analogue of T1/T2.5 (doors, windows) extended into
    Division 26 (electrical).
    """

    panel_id: str                              # "PNL-A", "MDP", "RP-1", ...
    voltage: Optional[str] = None              # "120/208V", "277/480V", ...
    phase_count: Optional[int] = None          # 1 or 3
    main_breaker_amps: Optional[int] = None
    bus_amps: Optional[int] = None
    mcb_or_mlo: Optional[str] = None           # "MCB" | "MLO"
    feeder_conductor_size: Optional[str] = None  # "3/0 AWG Cu", ...
    feeder_conduit_size: Optional[str] = None    # "2 inch", ...
    location: Optional[str] = None             # room or area description
    circuits: list[CircuitEntry] = Field(default_factory=list)
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class PanelScheduleResult(BaseModel):
    """Aggregate panel-schedule pre-pass result for a drawing page (Phase T2.6).

    Attached alongside (not replacing) the generic :class:`Schedule`
    rows on :class:`DrawingPrepassResult` so the existing prepass
    surface keeps working while downstream takeoff (Phase T2.6
    synthesis) consumes the richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    panels: list[PanelRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class LightingFixtureRecord(BaseModel):
    """One lighting fixture pulled off a lighting-fixture schedule (Phase T2.7).

    Lighting-fixture schedules live on electrical sheets (E1.0 / E2.0 /
    EL.0) and are the second-highest single Division 26 artefact after
    panel hardware. Each fixture type fans out into 1 EA TakeoffItem
    (the fixture itself) plus optionally 1 LS lamp/driver line for
    non-LED-integrated technologies (fluorescent / HID). Phase T2.7 is
    the EA-unit dispatcher analogue of T2.6 (panels), simpler because
    there is no parametric feeder fan-out — just per-fixture-type rows.

    Schedule rarely publishes a per-type quantity (the count comes
    from a floor-plan walk by the estimator). When the schedule DOES
    include a ``QTY`` column the value flows through ``quantity`` and
    the synthesiser bumps confidence; when absent, the synthesiser
    emits a single EA with low confidence so the row lands in the
    HAND_TAKEOFF queue for the estimator to back-fill.
    """

    fixture_tag: str                           # "A1", "B", "C2", "F1"
    description: str
    manufacturer: Optional[str] = None
    catalog_number: Optional[str] = None
    wattage: Optional[float] = None            # watts (per fixture)
    lumens: Optional[int] = None
    color_temp_k: Optional[int] = None         # 3000, 4000, 5000
    voltage: Optional[str] = None              # "120V", "277V", "120/277V"
    lamp_type: Optional[str] = None            # "LED", "FLUORESCENT", "HID", "INCAN"
    mounting: Optional[str] = None             # "RECESSED", "SURFACE", "PENDANT", ...
    dimmable: Optional[bool] = None
    emergency: Optional[bool] = None
    quantity: Optional[int] = None             # from QTY column when present
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class LightingScheduleResult(BaseModel):
    """Aggregate lighting-fixture-schedule pre-pass result for one page (Phase T2.7).

    Attached alongside (not replacing) the generic :class:`Schedule`
    rows on :class:`DrawingPrepassResult` so the existing prepass
    surface keeps working while downstream takeoff (Phase T2.7
    synthesis) consumes the richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    fixtures: list[LightingFixtureRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class HVACEquipmentRecord(BaseModel):
    """One HVAC equipment record pulled off a mechanical schedule (Phase T2.8).

    Mechanical / HVAC equipment schedules live on M-series / H-series /
    MH-series sheets and are the highest-dollar single Division 23
    artefact (and the third-highest single MEP artefact after panels and
    lighting in BPC's calibration cost distribution). Each equipment
    record fans out into 2-3 ``TakeoffItem`` families: the equipment
    itself (CSI per type — AHU → ``23 73 13``, RTU → ``23 74 13``, etc.),
    a parametric MEP rough-in line (CSI ``23 05 00``, LS), and optionally
    a disconnect + flex line (CSI ``26 28 16``, EA) for motorized
    equipment with a voltage feed. Phase T2.8 is the SIXTH dispatcher
    on the door/window/finish/panel/lighting scaffold.

    Equipment type is detected from the tag prefix (``AHU-``, ``RTU-``,
    ``VAV-``, ``P-`` / ``PUMP``, ``B-`` / ``BLR``, ``CH-`` / ``CHR`` /
    ``CHL``, ``F-`` / ``FAN`` / ``SF-`` / ``EF-``). The capacity unit
    is type-dependent (CFM for air-handlers, tons for chillers, MBH or
    BTUH for boilers, GPM for pumps) and is detected from the column
    header rather than from the value.
    """

    equipment_tag: str                         # "AHU-1", "RTU-A", "VAV-3-1", ...
    equipment_type: str                        # "AHU" | "RTU" | "VAV" | "PUMP" |
                                                # "BOILER" | "CHILLER" | "FAN" | "OTHER"
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    capacity_value: Optional[float] = None
    capacity_unit: Optional[str] = None        # "TONS" | "CFM" | "MBH" | "GPM" |
                                                # "BTUH" | None
    motor_hp: Optional[float] = None
    voltage: Optional[str] = None              # "208V/3φ", "208/3", "120V/1φ", ...
    phase_count: Optional[int] = None          # 1 or 3
    weight_lbs: Optional[float] = None
    dimensions: Optional[str] = None
    refrigerant: Optional[str] = None          # "R-410A", "R-454B", None
    fuel_type: Optional[str] = None            # "GAS" | "ELECTRIC" | "HW" | None
    location: Optional[str] = None
    quantity: Optional[int] = None             # from QTY column when present
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class HVACScheduleResult(BaseModel):
    """Aggregate HVAC equipment schedule pre-pass result for one page (Phase T2.8).

    Attached alongside (not replacing) the generic :class:`Schedule`
    rows on :class:`DrawingPrepassResult` so the existing prepass
    surface keeps working while downstream takeoff (Phase T2.8
    synthesis) consumes the richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    equipment: list[HVACEquipmentRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


class PlumbingFixtureRecord(BaseModel):
    """One plumbing fixture record pulled off a P-series fixture schedule (Phase T2.9).

    Plumbing fixture schedules live on P-series sheets (P1.0 / P2.0 /
    PL-1) and round out the Division 22+23+26 trifecta alongside the
    panels (T2.6), lighting (T2.7), and HVAC (T2.8) typed extractors.
    Each fixture record fans out into 2-3 :class:`TakeoffItem`
    families: the fixture itself (CSI per type — WC → ``22 41 13``,
    LAV → ``22 41 16``, EWC → ``22 47 13``, FD → ``22 13 19``, ...),
    a parametric MEP rough-in line (CSI ``22 11 16`` for water-
    supply-dominant fixtures or ``22 13 16`` for waste-dominant), and
    optionally a trim / installation-hardware line when manufacturer
    AND model_number are both populated.

    Fixture type is detected from the tag prefix (``WC-``, ``LAV-``,
    ``URN-`` / ``UR-``, ``SH-`` / ``SHU-``, ``EWC-`` / ``DF-``,
    ``MS-``, ``SK-``, ``WH-``, ``HD-`` / ``HB-``, ``FD-``). Flow rate
    captures the eco / efficiency spec (``1.28 GPF`` for flush
    fixtures, ``0.5 GPM`` for lavatory aerators, ``1.5 GPM`` for
    showerheads). Connection sizes round-trip as their original
    strings (``"1/2\""`` / ``"3/4\""`` / ``"1-1/2\""`` / ``"2\""``)
    so the spec passes through unchanged.

    Phase T2.9 is the FIFTH downstream consumer of the shared
    ``header_index_excluding`` helper (door / panel / lighting /
    HVAC are the prior four).
    """

    fixture_tag: str                           # "WC-1", "LAV-A", "URN-1", ...
    fixture_type: str                          # "WATER_CLOSET" | "LAVATORY" |
                                                # "URINAL" | "SHOWER" | "EWC" |
                                                # "MOP_SINK" | "SINK" |
                                                # "WATER_HEATER" | "HOSE_BIBB" |
                                                # "FLOOR_DRAIN" | "OTHER"
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    mounting: Optional[str] = None             # "FLOOR" | "WALL" | "COUNTER" |
                                                # "DECK" | "FREESTANDING"
    flow_rate_value: Optional[float] = None    # 1.28, 0.5, 1.5
    flow_rate_unit: Optional[str] = None       # "GPF" | "GPM" | None
    cold_water_size: Optional[str] = None      # "1/2\"", "3/4\""
    hot_water_size: Optional[str] = None
    waste_size: Optional[str] = None           # "1-1/2\"", "2\"", "4\""
    vent_size: Optional[str] = None
    ada_compliant: Optional[bool] = None
    sensor_operated: Optional[bool] = None
    quantity: Optional[int] = None             # from QTY column when present
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class PlumbingScheduleResult(BaseModel):
    """Aggregate plumbing-fixture-schedule pre-pass result for one page (Phase T2.9).

    Attached alongside (not replacing) the generic :class:`Schedule`
    rows on :class:`DrawingPrepassResult` so the existing prepass
    surface keeps working while downstream takeoff (Phase T2.9
    synthesis) consumes the richer typed records.
    """

    pages: list[int] = Field(default_factory=list)
    fixtures: list[PlumbingFixtureRecord] = Field(default_factory=list)
    confidence: float = 0.0                    # 0..1
    raw_table_text: str = ""                   # joined-headers debug string


# ---------------------------------------------------------------------------
# Phase T2.10 — Specialty equipment schedules
# (Kitchen / Lab Casework / AV / Security)
# ---------------------------------------------------------------------------
#
# Closes the typed-extraction long-tail.  Sixth class of consumer of the
# shared ``header_index_excluding`` helper from
# :mod:`core.extraction.header_utils` (door / panel / lighting / HVAC /
# plumbing are the prior five).  Each domain is structurally simpler
# than HVAC (fewer columns, no fuel/voltage matrix) so all four ship in
# a single phase.


class KitchenEquipmentRecord(BaseModel):
    """One kitchen equipment record pulled off a K-series schedule (Phase T2.10).

    Kitchen equipment schedules live on K-series sheets (K1.0 / K-EQ)
    and route to MasterFormat Division 11 (Equipment), section
    ``11 40 13`` Food Service Equipment.  Item types are detected
    from tag prefix or description: RANGE / GRIDDLE / FRYER / OVEN
    / REFRIGERATOR / FREEZER / WALK_IN / ICE_MACHINE / DISHWASHER /
    MIXER / PREP_TABLE / HOOD / EXHAUST_FAN / SINK / OTHER.

    High-dollar: $3K-$80K per unit; some single line items (walk-in
    cooler) can dominate a small RFP.  Utility flags drive the
    rough-in synthesis (gas + water + drain + electric → MEP
    rough-in LS row).
    """

    tag: str                                   # "K-1", "FE-1", "RANGE-1", ...
    item_type: str                             # "RANGE" | "FRYER" | "REFRIGERATOR" | ...
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    width_in: Optional[float] = None
    depth_in: Optional[float] = None
    height_in: Optional[float] = None
    btu_rating: Optional[int] = None           # gas equipment BTU/hr
    utility_gas: Optional[bool] = None
    utility_electric: Optional[bool] = None
    utility_water: Optional[bool] = None
    utility_drain: Optional[bool] = None
    voltage: Optional[str] = None              # "120V", "208V", "480V/3PH"
    quantity: Optional[int] = None             # from QTY column when present
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class KitchenScheduleResult(BaseModel):
    """Aggregate kitchen-equipment-schedule pre-pass result for one page."""

    pages: list[int] = Field(default_factory=list)
    equipment: list[KitchenEquipmentRecord] = Field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


class LabCaseworkRecord(BaseModel):
    """One lab casework / fume hood record pulled off a lab schedule (Phase T2.10).

    Lab casework schedules live on lab plans / I-series interior
    sheets and route to MasterFormat Division 12 (Furnishings),
    section ``12 35 53`` Laboratory Casework, with cross-division
    routing of fume hoods + safety equipment to ``11 53 13`` /
    ``11 53 19`` Laboratory Equipment.  Item types: BASE_CABINET
    / WALL_CABINET / TALL_CABINET / FUME_HOOD / LAB_BENCH /
    SAFETY_CABINET / EYEWASH_STATION / OTHER.

    Fume hoods are the dominant cost line ($15K-$50K per hood);
    everything else is mid-dollar casework.
    """

    tag: str                                   # "BC-1", "WC-1", "FH-1", "LB-1", ...
    item_type: str                             # "BASE_CABINET" | "FUME_HOOD" | ...
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    width_in: Optional[float] = None
    depth_in: Optional[float] = None
    height_in: Optional[float] = None
    material: Optional[str] = None             # "EPOXY" | "STAINLESS" | "PHENOLIC"
    drawer_door_config: Optional[str] = None
    utility_gas: Optional[bool] = None
    utility_vacuum: Optional[bool] = None
    utility_water: Optional[bool] = None
    utility_electric: Optional[bool] = None
    quantity: Optional[int] = None
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class LabScheduleResult(BaseModel):
    """Aggregate lab-casework-schedule pre-pass result for one page."""

    pages: list[int] = Field(default_factory=list)
    casework: list[LabCaseworkRecord] = Field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


class AVDeviceRecord(BaseModel):
    """One AV / IT device record pulled off a T-series schedule (Phase T2.10).

    AV/IT equipment schedules live on T-series / A/V drawings and
    route to MasterFormat Division 27 (Communications), section
    ``27 41 16`` Integrated Audio-Video Systems.  Item types:
    DISPLAY / PROJECTOR / CAMERA / MICROPHONE / SPEAKER / RACK /
    CONTROL_PROCESSOR / NETWORK_SWITCH / OTHER.
    """

    tag: str                                   # "DISP-1", "PROJ-1", "CAM-1", "RACK-1"
    item_type: str                             # "DISPLAY" | "PROJECTOR" | "CAMERA" | ...
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    size_or_resolution: Optional[str] = None   # "75\"", "4K", "1080p"
    wattage: Optional[float] = None
    mounting: Optional[str] = None             # "WALL" | "CEILING" | "RACK" | "FLOOR"
    power: Optional[str] = None                # "120V" | "PoE" | "12VDC"
    signal_type: Optional[str] = None          # "HDMI" | "SDI" | "IP" | "USB"
    quantity: Optional[int] = None
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class AVScheduleResult(BaseModel):
    """Aggregate AV-equipment-schedule pre-pass result for one page."""

    pages: list[int] = Field(default_factory=list)
    devices: list[AVDeviceRecord] = Field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


class SecurityDeviceRecord(BaseModel):
    """One security / access-control device record pulled off an S- or T-series schedule (Phase T2.10).

    Security / access-control schedules live on S-series security
    sheets or T-series telecom sheets and route to MasterFormat
    Division 28 (Electronic Safety & Security), sections ``28 13``
    Access Control and ``28 23`` Video Surveillance.  Item types:
    CARD_READER / CAMERA / MOTION_SENSOR / DOOR_CONTACT / KEYPAD
    / REQUEST_TO_EXIT / MAGLOCK / OTHER.
    """

    tag: str                                   # "DR-1", "CAM-1", "MS-1", "DC-1", ...
    item_type: str                             # "CARD_READER" | "CAMERA" | ...
    description: Optional[str] = None
    manufacturer: Optional[str] = None
    model_number: Optional[str] = None
    mounting: Optional[str] = None             # "WALL" | "CEILING" | "DOOR_FRAME"
    power: Optional[str] = None                # "PoE" | "12VDC" | "24VDC"
    connection: Optional[str] = None           # "Cat6" | "RS-485" | "Wiegand"
    quantity: Optional[int] = None
    notes: Optional[str] = None
    confidence: float = 0.85
    source_sheet: Optional[str] = None
    source_page: int = 0


class SecurityScheduleResult(BaseModel):
    """Aggregate security/access-control-schedule pre-pass result for one page."""

    pages: list[int] = Field(default_factory=list)
    devices: list[SecurityDeviceRecord] = Field(default_factory=list)
    confidence: float = 0.0
    raw_table_text: str = ""


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
    panel_schedule: Optional[PanelScheduleResult] = None  # T2.6 typed electrical panels
    lighting_schedule: Optional[LightingScheduleResult] = None  # T2.7 typed lighting fixtures
    hvac_schedule: Optional[HVACScheduleResult] = None  # T2.8 typed HVAC equipment
    plumbing_schedule: Optional[PlumbingScheduleResult] = None  # T2.9 typed plumbing fixtures
    kitchen_schedule: Optional[KitchenScheduleResult] = None  # T2.10 Div 11 kitchen equipment
    lab_schedule: Optional[LabScheduleResult] = None  # T2.10 Div 12 lab casework
    av_schedule: Optional[AVScheduleResult] = None  # T2.10 Div 27 AV/IT devices
    security_schedule: Optional[SecurityScheduleResult] = None  # T2.10 Div 28 security/access
    # T10 F-3 — page is dominated by a "REFERENCE ONLY" photograph (e.g. a
    # US Army facility reference shot embedded on an architectural sheet).
    # Vision-LLM analysis is skipped entirely for such pages; the
    # deterministic prepass still records the page's title block /
    # dimensions / schedules when they are present. Default False keeps
    # every pre-T10 prepass result backwards-compatible.
    is_reference_photo: bool = False


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
    # T10 F-3 — set True when the vision LLM refused to analyse this sheet
    # twice (initial attempt + constrained-context retry both surfaced a
    # safety refusal like "I'm sorry, I can't assist with that"). The
    # extraction itself is empty; the flag lets downstream queue worksheets
    # and exports surface the sheet to a human reviewer rather than
    # silently dropping zero takeoff rows. Default False keeps every
    # pre-T10 fixture / persisted JSON backwards-compatible.
    refused: bool = False


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


class CostLineOverrideSnapshot(BaseModel):
    """Phase T6.4.d — pre-override snapshot of a :class:`CostLine`.

    Captured by :func:`core.estimator._capture_line_snapshot` BEFORE
    every override path mutates a line, then pushed onto the line's
    :pyattr:`CostLine.override_snapshots` stack. A per-line revert
    (:func:`core.estimator.revert_last_override`) pops the top
    snapshot and restores the recorded fields back onto the line
    exactly, so an operator who clicked "Apply" on a 200-row vendor
    batch can roll back line 47 without re-running the whole pipeline.

    Why not parse the ``| previous: ...`` suffix that T6.4.c /
    T6.4.c.2 already write into ``CostLine.notes``? The notes string
    is **human-readable** — it carries ``[unit_cost: $3.00]`` text
    describing what each override DID, but does not preserve the
    actual numeric values that existed BEFORE each override. So a
    notes-only undo cannot recompute ``total_cost`` /
    ``price_confidence`` / ``cost_band`` from scratch — restoration
    would be lossy. A parallel snapshot store sidesteps the
    lossiness entirely. The brief acknowledged this and recommended
    Option A (snapshot store) over Option C (notes parse); this
    model is the realisation.

    Bounded: at most :data:`MAX_OVERRIDE_SNAPSHOTS` (10) entries
    per line; older entries drop FIFO. Default empty list on
    :pyattr:`CostLine.override_snapshots` keeps every pre-T6.4.d
    estimate (loaded from JSON, hand-built fixture, etc.)
    backwards-compatible — those lines simply can't undo because
    they predate this feature.
    """

    unit_cost: float = 0.0
    qty: float = 0.0
    total_cost: float = 0.0
    notes: str = ""
    cost_source_tier: CostSourceTier = CostSourceTier.EXACT_MATCH
    price_confidence: float = 1.0
    combined_confidence: float = 1.0
    cost_band: CostBand = CostBand.AUTO_APPROVE
    suppressed: bool = False
    applied_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description=(
            "UTC timestamp when this snapshot was captured (i.e. just "
            "before the override mutated the line). Surfaced in the "
            "Streamlit revert toast so the operator sees 'reverted to "
            "state from 14:32 UTC'."
        ),
    )
    source_tag: str = Field(
        default="",
        description=(
            "Canonical source tag at position 0 of ``CostLine.notes`` "
            "BEFORE this override layered on top — i.e. the provenance "
            "tag of the layer we are about to bury. Examples: "
            "``\"\"`` (no tag; line was at priced-from-cost-DB defaults), "
            "``\"[batch]\"``, ``\"[sub-quote]\"``, ``\"[manual-override]\"``. "
            "Used by the Streamlit revert UI to label the snapshot ('revert "
            "to vendor-CSV state from 14:32') without re-parsing the notes."
        ),
    )


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
    # Phase T6 — confidence band assigned by ``price_takeoff``. Defaults
    # to ``AUTO_APPROVE`` for backward compatibility with hand-constructed
    # ``CostLine`` instances in tests + persisted fixtures that pre-date
    # T6. Real CostLines emitted by the pricing pipeline always carry an
    # explicit band derived via ``band_for_confidence``.
    cost_band: CostBand = CostBand.AUTO_APPROVE
    # Phase T7 — catalog-completeness scoring. ``confidence`` (above) is
    # the qty-side confidence (how good was the takeoff?); these two fields
    # are the price-side confidence (how good was the cost lookup?).
    # ``price_confidence`` defaults to ``1.0`` and ``cost_source_tier``
    # defaults to ``EXACT_MATCH`` so every pre-T7 fixture, hand-constructed
    # CostLine, and persisted JSON round-trip has identical
    # ``combined_confidence`` semantics as before T7 — the band assignment
    # is unchanged for any code path that doesn't explicitly set these.
    price_confidence: float = 1.0
    cost_source_tier: CostSourceTier = CostSourceTier.EXACT_MATCH
    # Phase T6.4.d — per-line undo stack. Each entry is a
    # :class:`CostLineOverrideSnapshot` captured by
    # :func:`core.estimator._capture_line_snapshot` BEFORE one of the
    # override paths (T6.1 manual, T6.3 batch CSV, T8.1 / T8.2
    # sub-quote PDF) mutated this line. The Streamlit "↶ revert" affordance
    # in the Estimate tab pops the stack-top snapshot via
    # :func:`core.estimator.revert_last_override` to roll back the line
    # without re-running the pricing pipeline. Bounded at
    # :data:`MAX_OVERRIDE_SNAPSHOTS` (10) entries — older snapshots
    # drop FIFO so a pathological re-apply loop can't grow the line's
    # footprint without bound. Default empty list keeps every pre-T6.4.d
    # estimate backwards-compatible (those lines simply have nothing to
    # revert).
    override_snapshots: list[CostLineOverrideSnapshot] = Field(default_factory=list)

    @property
    def combined_confidence(self) -> float:
        """Phase T7 ``qty_confidence × price_confidence``.

        This is the value the band thresholds (0.85 / 0.65) apply to
        post-T7. Both factors are clamped into [0, 1] before
        multiplying so a malformed input can't push combined out of
        bounds. ``confidence is None`` (the legacy LLM-no-confidence
        path) is treated as the schema default of 0.7 — same as
        ``band_for_confidence(None)`` which routes to OPERATOR_REVIEW.
        """
        qty = 0.7 if self.confidence is None else float(self.confidence)
        qty = max(0.0, min(1.0, qty))
        price = max(0.0, min(1.0, float(self.price_confidence)))
        return round(qty * price, 4)


class Estimate(BaseModel):
    project_name: str
    region_multiplier: float = 1.00
    contingency_pct: float = 10.0
    overhead_pct: float = 10.0
    profit_pct: float = 5.0

    line_items: list[CostLine] = Field(default_factory=list)

    # ------------------------------------------------------------------
    # Phase T9.0 — bid alternates / VE
    # ------------------------------------------------------------------
    #
    # Alternates do NOT roll into ``subtotal`` / ``grand_total`` by
    # default — the base estimate's headline number reflects the base
    # bid only, mirroring real federal / state bid practice ("you bid
    # the base; alternates are at owner option"). Two helper methods
    # (`subtotal_with_alternates_selected`,
    # `total_with_alternates_selected`) compute the rolled-up totals
    # when an operator opts an alternate in via the (deferred T9.1)
    # UI. The set of alternates that ARE rolled in by default lives
    # in ``alternates_selected_default`` — non-empty only when an
    # :class:`AlternateLine` was marked ``included_by_default=True``,
    # which is rare.
    alternates: list[AlternateLineEstimate] = Field(default_factory=list)
    alternates_selected_default: set[str] = Field(
        default_factory=set,
        description=(
            "Set of ``alternate_id`` values that are rolled into the "
            "base estimate by construction (the corresponding "
            ":class:`AlternateLine` had ``included_by_default=True``). "
            "Most projects leave this empty."
        ),
    )

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

    # -- Phase T6 band-aware helpers -----------------------------------
    #
    # ``priced_line_items`` already strips suppressed lines, so band
    # roll-ups below operate on it (suppressed lines always live in the
    # HAND_TAKEOFF band and carry ``total_cost == 0`` already, so they
    # contribute nothing to dollar aggregates regardless — this is the
    # double-counting guard the brief asks for).

    @property
    def auto_approve_line_items(self) -> list[CostLine]:
        return [li for li in self.priced_line_items if li.cost_band == CostBand.AUTO_APPROVE]

    @property
    def operator_review_line_items(self) -> list[CostLine]:
        return [li for li in self.priced_line_items if li.cost_band == CostBand.OPERATOR_REVIEW]

    @property
    def hand_takeoff_line_items(self) -> list[CostLine]:
        """All HAND_TAKEOFF lines, regardless of suppression.

        Suppressed lines are forced to HAND_TAKEOFF by ``price_takeoff``
        but live in ``suppressed_line_items`` (not ``priced_line_items``).
        The Streamlit "Hand Takeoff Queue" and the Excel queue sheet want
        BOTH paths, because the estimator's mental model of "needs manual
        eyes" includes unit-mismatch lines.
        """
        return [li for li in self.line_items if li.cost_band == CostBand.HAND_TAKEOFF]

    @property
    def headline_line_items(self) -> list[CostLine]:
        """Lines whose ``total_cost`` rolls into the headline ``grand_total``.

        Phase T6 contract: AUTO_APPROVE + OPERATOR_REVIEW lines only.
        HAND_TAKEOFF lines (low-confidence raw takeoffs or unit-mismatch
        suppressed lines) are excluded so the headline number reflects
        only what a reviewer would actually sign off on. The hand-takeoff
        totals stay available via ``total_hand_takeoff`` for the
        worklist UI and Excel queue sheet.
        """
        return [
            li for li in self.priced_line_items
            if li.cost_band in (CostBand.AUTO_APPROVE, CostBand.OPERATOR_REVIEW)
        ]

    # -- Phase T6 band-aware dollar aggregates --------------------------

    @property
    def total_auto_approve(self) -> float:
        """Sum of ``total_cost`` for AUTO_APPROVE-banded lines."""
        return round(sum(li.total_cost for li in self.auto_approve_line_items), 2)

    @property
    def total_operator_review(self) -> float:
        """Sum of ``total_cost`` for OPERATOR_REVIEW-banded lines."""
        return round(sum(li.total_cost for li in self.operator_review_line_items), 2)

    @property
    def total_hand_takeoff(self) -> float:
        """Sum of ``total_cost`` for HAND_TAKEOFF-banded lines.

        **Informational only — NOT in any grand total.** Suppressed lines
        (which are forced to HAND_TAKEOFF by ``price_takeoff``) carry
        ``total_cost == 0`` already, so this sum captures only the
        low-confidence (< 0.65) lines that DID get priced but were
        bumped out of the headline by the band assignment.
        """
        return round(sum(li.total_cost for li in self.hand_takeoff_line_items), 2)

    @property
    def hand_takeoff_count(self) -> int:
        return len(self.hand_takeoff_line_items)

    @property
    def operator_review_count(self) -> int:
        return len(self.operator_review_line_items)

    @property
    def auto_approve_count(self) -> int:
        return len(self.auto_approve_line_items)

    @property
    def subtotal(self) -> float:
        """Subtotal of the headline ``grand_total`` (AUTO + REVIEW).

        Phase T6 changed the semantics: HAND_TAKEOFF lines are now
        excluded in addition to the long-standing exclusion of
        ``suppressed=True`` lines (which now also resolve to
        HAND_TAKEOFF by construction). Tests that built lines with the
        default ``CostLine.confidence == 0.7`` (→ OPERATOR_REVIEW) are
        unaffected.
        """
        return round(sum(li.total_cost for li in self.headline_line_items), 2)

    @property
    def subtotal_auto_only(self) -> float:
        """AUTO-only subtotal — the conservative confidence-floor basis."""
        return self.total_auto_approve

    @property
    def by_division(self) -> dict[str, float]:
        out: dict[str, float] = {}
        for li in self.headline_line_items:
            out[li.csi_division] = round(out.get(li.csi_division, 0.0) + li.total_cost, 2)
        return out

    @property
    def by_cost_category(self) -> dict[str, float]:
        """Roll up line totals by labor/material/equipment/sub/other."""
        out: dict[str, float] = {c.value: 0.0 for c in CostCategory}
        for li in self.headline_line_items:
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
        """Headline contract value (AUTO + REVIEW + markups).

        Phase T6: alias for :pyattr:`grand_total_with_review`. Tests that
        check ``grand_total`` against the existing
        ``subtotal * (1 + cont%) * (1 + oh%) * (1 + profit%)`` formula
        keep passing because ``subtotal`` itself moved to "headline-only"
        in lock-step.
        """
        return round(self.subtotal + self.contingency + self.overhead + self.profit, 2)

    @property
    def grand_total_with_review(self) -> float:
        """Explicit name for the headline grand total (= ``grand_total``).

        Surfaced as a separate property so the Excel + PDF + UI layers can
        clearly label the "if reviewer signs off" number alongside the
        more-conservative ``grand_total_auto_only``.
        """
        return self.grand_total

    @property
    def grand_total_auto_only(self) -> float:
        """Conservative grand total: AUTO_APPROVE lines + markups, only.

        The "confidence floor" — every dollar in this number came out of
        a high-confidence (≥ 0.85) line. Markups (contingency / overhead
        / profit) are recomputed against the AUTO-only subtotal so the
        compounding stays internally consistent.
        """
        base = self.subtotal_auto_only
        cont = round(base * self.contingency_pct / 100.0, 2)
        oh = round((base + cont) * self.overhead_pct / 100.0, 2)
        prof = round((base + cont + oh) * self.profit_pct / 100.0, 2)
        return round(base + cont + oh + prof, 2)

    # -- Phase T7 catalog-completeness aggregates -----------------------
    #
    # Tier roll-ups walk *every* line in ``line_items`` (including
    # ``MISSING`` / suppressed) so the breakdown reconciles back to the
    # full extracted takeoff, not just the priced subset. ``total_by_tier``
    # uses ``total_cost`` directly: MISSING lines contribute $0 already
    # (suppression / no-match path zeros the cost), so they show up with
    # a non-zero count but $0 total — which is exactly the
    # "informational, not in subtotal" signal the brief calls for.

    @property
    def total_by_tier(self) -> dict[CostSourceTier, float]:
        """Sum of ``total_cost`` per :class:`CostSourceTier`.

        Includes all line items regardless of suppression / band so the
        rollup reconciles to the source takeoff count. ``MISSING``
        lines have ``total_cost == 0`` already, so the dollar number
        for that tier is informational ($0 unless an operator hand-
        priced a MISSING line and then forgot to update the tier).
        """
        out: dict[CostSourceTier, float] = {t: 0.0 for t in CostSourceTier}
        for li in self.line_items:
            tier = li.cost_source_tier
            if not isinstance(tier, CostSourceTier):
                try:
                    tier = CostSourceTier(tier)
                except ValueError:
                    tier = CostSourceTier.MISSING
            out[tier] = round(out[tier] + li.total_cost, 2)
        return out

    @property
    def count_by_tier(self) -> dict[CostSourceTier, int]:
        """Count of line items per :class:`CostSourceTier`.

        Sums to ``len(line_items)`` exactly — every line lands in
        exactly one tier bucket.
        """
        out: dict[CostSourceTier, int] = {t: 0 for t in CostSourceTier}
        for li in self.line_items:
            tier = li.cost_source_tier
            if not isinstance(tier, CostSourceTier):
                try:
                    tier = CostSourceTier(tier)
                except ValueError:
                    tier = CostSourceTier.MISSING
            out[tier] += 1
        return out

    # ------------------------------------------------------------------
    # Phase T9.0 — bid alternates helpers
    # ------------------------------------------------------------------
    #
    # All four helpers below operate on the priced
    # :pyattr:`alternates` list (built by
    # :func:`core.estimator.price_alternates`) and never mutate the
    # base estimate. They are read-only views — the math composes:
    #
    #   subtotal_with_alternates_selected(ids)
    #     = subtotal_base_only + sum(cost_delta for alt in selected)
    #
    #   total_with_alternates_selected(ids)
    #     = subtotal_with_alternates_selected(ids)
    #       + contingency on adjusted subtotal
    #       + overhead on (subtotal + contingency)
    #       + profit on (subtotal + contingency + overhead)
    #
    # so the markups apply to the adjusted subtotal — same composition
    # the base ``grand_total`` uses against ``subtotal``.

    @property
    def subtotal_base_only(self) -> float:
        """Alias for ``subtotal`` — the base bid before any alternates.

        Phase T9.0 contract: the base estimate is unchanged by the
        presence of alternates; this property exists so downstream
        callers can be explicit about which subtotal they're reading.
        Equivalent to :pyattr:`subtotal`.
        """
        return self.subtotal

    @property
    def alternates_total_additive(self) -> float:
        """Sum of every ADDITIVE alternate's resolved ``cost_delta``.

        Returns 0.0 when no ADDITIVE alternates carry a numeric
        ``cost_delta`` (or none are priced at all). Used by the Excel
        "Project Summary" alternates block and the
        "Bid Alternates" worksheet footer rows.
        """
        return round(
            sum(
                (a.cost_delta or 0.0)
                for a in self.alternates
                if a.alternate_type == AlternateType.ADDITIVE and a.cost_delta is not None
            ),
            2,
        )

    @property
    def alternates_total_deductive(self) -> float:
        """Sum of every DEDUCTIVE + VE alternate's ``cost_delta``.

        DEDUCTIVE and VE alternates both carry negative deltas (savings)
        and behave identically in the math; the type tag preserves
        downstream grouping. The returned number is negative when
        savings exist.
        """
        return round(
            sum(
                (a.cost_delta or 0.0)
                for a in self.alternates
                if a.alternate_type in (AlternateType.DEDUCTIVE, AlternateType.VE)
                and a.cost_delta is not None
            ),
            2,
        )

    @property
    def alternates_total_substitution(self) -> float:
        """Sum of every SUBSTITUTION alternate's ``cost_delta`` (signed)."""
        return round(
            sum(
                (a.cost_delta or 0.0)
                for a in self.alternates
                if a.alternate_type == AlternateType.SUBSTITUTION and a.cost_delta is not None
            ),
            2,
        )

    @property
    def alternates_count_missing(self) -> int:
        """Number of priced alternates with no resolvable ``cost_delta``."""
        return sum(
            1 for a in self.alternates
            if a.pricing_basis == AlternatePricingBasis.MISSING
        )

    def alternates_delta_for_selection(self, selected_ids: set[str] | None) -> float:
        """Sum of ``cost_delta`` over alternates in ``selected_ids``.

        ``None`` is treated as the empty set (no alternates selected).
        Alternates with ``cost_delta is None`` contribute 0.0 to the
        sum — they're surfaced separately via
        :pyattr:`alternates_count_missing`.
        """
        ids = selected_ids or set()
        return round(
            sum(
                (a.cost_delta or 0.0)
                for a in self.alternates
                if a.alternate_id in ids and a.cost_delta is not None
            ),
            2,
        )

    def subtotal_with_alternates_selected(
        self, selected_ids: set[str] | None
    ) -> float:
        """Base subtotal + the signed deltas of every alternate in ``selected_ids``.

        Pre-markup. The base subtotal itself is unaffected — alternates
        are an additive layer on top so an operator can compare
        scenarios without re-running the estimator.
        """
        return round(
            self.subtotal_base_only + self.alternates_delta_for_selection(selected_ids),
            2,
        )

    def total_with_alternates_selected(
        self, selected_ids: set[str] | None
    ) -> float:
        """Grand total recomputed against the alternate-adjusted subtotal.

        Applies the same contingency / overhead / profit composition
        that :pyattr:`grand_total` applies against the base subtotal.
        Region multiplier is already baked into each ``cost_delta`` by
        :func:`core.estimator.price_alternates` (mirrors the seed-DB /
        CWICR pricing path that bakes region multiplier into
        ``unit_cost``), so no extra region scaling is applied here.
        """
        base = self.subtotal_with_alternates_selected(selected_ids)
        cont = round(base * self.contingency_pct / 100.0, 2)
        oh = round((base + cont) * self.overhead_pct / 100.0, 2)
        prof = round((base + cont + oh) * self.profit_pct / 100.0, 2)
        return round(base + cont + oh + prof, 2)


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


class AlternatesSectionConfig(BaseModel):
    """Bid-alternates section toggles in ``config/client_quote.json`` (Phase T9)."""

    enabled: bool = True
    intro_paragraph: Optional[str] = None
    footer_note: Optional[str] = None
    default_selection: Optional[list[str]] = None


class QuoteConfig(BaseModel):
    """Top-level container persisted to `config/client_quote.json`."""

    company: CompanyInfo = Field(default_factory=CompanyInfo)
    client: ClientInfo = Field(default_factory=ClientInfo)
    quote_meta: QuoteMeta = Field(default_factory=QuoteMeta)
    payment_schedule: PaymentSchedule = Field(default_factory=PaymentSchedule)
    terms_text: str = ""
    alternates_section: AlternatesSectionConfig = Field(
        default_factory=AlternatesSectionConfig
    )
