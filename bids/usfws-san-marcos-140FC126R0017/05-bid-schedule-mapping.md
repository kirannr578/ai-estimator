# 05 — Bid-schedule mapping (the single most valuable deliverable)

> The federal Bid Schedule (Attachment 2) defines the **exact CLIN sequence + unit + quantity** the proposal must match. Per RFP M.1.9: "Any proposal that fails to cite a price for each item or fails to make an entry that indicates service will not be provided for an Item will be rejected as non-conforming to this solicitation." Per L.2.1.2.D: "Offeror's shall insert proposed unit and extended and totals in Section B for each Contract Line Item (CLIN). Any proposal that fails to cite a price for each item ... will be rejected as non-conforming."
>
> Bottom line: get the 8 lines right, in this exact order, with both unit price AND extended amount AND a grand total, or the bid is dead before it's read.

---

## A. CLIN-by-CLIN mapping table

For each line: bid-schedule row → SOW §reference → trade → cost-DB match → pricing source → suggested approach.

| CLIN | Bid Schedule (Attachment 2) text | Unit | Est QTY | SOW ref | Cost-DB match | Source for unit price |
|---:|---|:---:|:---:|---|---|---|
| **0001** | Remove and replace the three overhead sectional doors to include hardware, weather stripping and openers | EA | 3 | §1.1.A.1 + §4.1.A.1 + §4.2.B | ❌ **NO direct cost-DB hit** | **Sub quote** — 2" insulated panel OH door w/ manual chain hoist, 20-ga ext / 26-ga back, white baked polyester finish, weather strip, interior side lock. Carry **$3,500–$5,500/EA installed** until sub quote lands. |
| **0002** | Remove and replace existing light fixtures with LED light fixtures to meet OSHA requirements | JOB | 1 | §1.1.A.2 | ✅ `26 51 00` "Interior lighting fixture, average" @ **$285/EA** seed | Cost-DB hit at the EA level; the JOB rolls up to a fixture count × unit. Confirm count at site visit. For ~10–14 fixtures + disposal of legacy lamps + minor wiring tidy-up: **$3,500–$6,500 LS** |
| **0003** | Remove all suspended ceiling grids and tiles | JOB | 1 | §1.1.A.3 | ✅ `02 41 16` "Selective demolition (interior)" @ **$4.50/SF** seed | 416 SF × $4.50/SF = $1,872. Plus minor demo allowance for any T-bar grid attachments and EA stop count. Carry **$2,000–$3,500 LS** |
| **0004** | Remove and replace the existing three (3) exterior personnel doors with insulated hollow metal doors to include frames, hardware, weather stripping and thresh hold | JOB | 3 ⚠️ | §1.1.A.4 + §4.1.A.2 | ✅ `08 11 13` "Hollow metal door & frame" @ **$950/EA** seed + ✅ `08 71 00` "Door hardware set" @ **$425/EA** seed | Insulated HM premium over plain HM ≈ 20–40%, so $1,200–$1,400/EA for door+frame + $425/EA for hardware + ~$300/EA install labor + threshold + weather strip → **$2,000–$2,400/EA installed × 3 = $6,000–$7,200 LS** total. ⚠️ Note unit-quantity discrepancy (see RFI #4) — bid Qty 3 × unit price for safety unless CO clarifies. |
| **0005** | Terminate, cap and remove existing gas lines from the building | JOB | 1 | §1.1.A.5 | ❌ **NO cost-DB hit** | **Sub quote** — gas-licensed plumbing sub. Cap at meter outlet + at building penetration; remove all interior piping. Carry **$1,500–$3,500 LS** including utility coordination + permit + labor |
| **0006** | Remove and replace existing gutter system to include and replace down spouts | LF | 110 | §1.1.A.6 + §4.1.B.2 | ❌ **NO cost-DB hit** for residential/light-comm gutter | Carry **$12–$22/LF installed** for 6" K-style or ogee + downspouts. At 110 LF × $17/LF midpoint = **$1,870**. Bid by unit price + extension. Note: VARIATION IN ESTIMATED QUANTITY (52.211-18) caps adjustment at ±15% of estimated quantity. |
| **0007** | Remove and replace existing roof with new roofing sheets | JOB | 1 | §1.1.A.7 + §4.1.B.1 + §4.2.A | ⚠️ `07 41 13` "Standing seam metal roofing" @ **$14.50/SF** seed — close fit for 24-ga panels but verify | 24-ga corrugated / R-panel / U-panel pricing typically $9–$16/SF installed for tear-off + new panel + flashing + fasteners. At assumed 2,000 SF: **$18,000–$32,000 LS**. **THIS IS THE BIG-DOLLAR LINE — measure carefully at site visit.** |
| **0008** | Remove existing gas fired unit heaters | JOB | 1 | §1.1.A.8 | ❌ **NO cost-DB hit** | **Sub quote** (same sub as CLIN 0005 typically). Disconnect after gas cap, unbolt, remove, dispose. Per heater $400–$900 installed; for 1–3 heaters: **$500–$2,500 LS** |

**Subtotal of the 8 CLINs (midpoint of ranges, pre-burden):**

- CLIN 0001: $13,500 (3 × $4,500)
- CLIN 0002: $5,000
- CLIN 0003: $2,750
- CLIN 0004: $6,600 (3 × $2,200)
- CLIN 0005: $2,500
- CLIN 0006: $1,870
- CLIN 0007: $25,000 (2,000 SF × $12.50/SF midpoint)
- CLIN 0008: $1,500

**Raw direct-cost subtotal ≈ $58,720**

That's well below the $100K floor of the magnitude range, which means either: (a) our seed/ranges are light, (b) the government estimate carries thicker contingency than our raw direct cost, (c) the building footprint is larger than 2,000 SF, or (d) a combination. The site visit + sub quotes will move all of these.

**Working LPTA-thin bid envelope:** after **mobilization/demob ($4K) + GCs (2 mo × $8K = $16K — note: lighter than the cost-DB $12K/mo seed for a 60-day rural job) + bonds (2% = ~$2K) + insurance (3% = ~$3K) + DBA labor burden uplift (~5% on labor-heavy CLINs ~$3K) + 7% contingency + 10% OH + 6% profit**, total clears **~$110K–$130K** on the low end, **~$160K–$180K** on the high end. The "raw direct cost × ~2.0 markup" is typical for small federal renovation work where OH and bond drag are high.

## B. How many lines already have a cost-DB match

- **4 of 8** lines have a usable cost-DB match (0002, 0003, 0004, 0007 — though 0007's match is "close fit, verify the seam type")
- **4 of 8** lines need a sub quote or an allowance (0001, 0005, 0006, 0008)

That's a healthy ratio for a project where the bid schedule pre-defines the granularity — the cost DB doesn't need to be exhaustive; it needs to be right where it overlaps.

## C. Lines that need cost-DB additions (for F1 / CWICR pipeline)

If F1 (CWICR cost-DB extension) lands during this bid cycle, consider seeding these entries:

| Suggested CSI section | Description | Suggested seed unit + cost |
|---|---|---|
| `08 36 00` | Overhead coiling / sectional door, insulated, w/ manual chain hoist | EA, $4,500 (range $3,500–$5,500) |
| `22 11 24` | Gas piping abandonment / capping | LS, $2,500 (range $1,500–$3,500) — small federal sites |
| `07 71 23` | Gutter + downspout, K-style 6" w/ DS | LF, $17 (range $12–$22) |
| `23 54 00` | Suspended unit-heater removal (gas-fired, after disconnect) | EA, $650 (range $400–$900) |

These would each be tagged with a `cost_category: "subcontractor"` and `waste_factor: 1.00`. None blocks this bid — sub quotes will deliver the real numbers.

## D. CLIN ordering rule (don't reorder, don't add, don't subtract)

Per RFP M.1.9 + L.2.1.2.D: the proposal's Section B / Quote Schedule **must mirror the bid schedule exactly**. Specifically:

- 8 CLINs, numbered 0001–0008 (or 1–8 in Attachment 2 numbering — match whichever the CO accepts)
- Same description text (rewording is fine if the substance matches; the CO's clerks will pattern-match)
- Same unit of measure (EA / JOB / LF)
- Same estimated quantity
- Add a unit price column and an "AMOUNT" (extension) column
- Roll up to a **GRAND TOTAL**
- No additional alternates, no value-engineering deducts, no allowance line items (LPTA does not accept any of these)

## E. Pricing-form template (paste into Section B)

| ITEM NO. | Bid Item Description | Unit | Est QTY | Unit Price | AMOUNT |
|---:|---|:---:|:---:|---:|---:|
| 1 | Remove and replace the three overhead sectional doors to include hardware, weather stripping and openers | EA | 3 | $ ____.__ | $ ____.__ |
| 2 | Remove and replace existing light fixtures with LED light fixtures to meet OSHA requirements | JOB | 1 | $ ____.__ | $ ____.__ |
| 3 | Remove all suspended ceiling grids and tiles | JOB | 1 | $ ____.__ | $ ____.__ |
| 4 | Remove and replace the existing three (3) exterior personnel doors with insulated hollow metal doors to include frames, hardware, weather stripping and thresh hold | JOB | 3 | $ ____.__ | $ ____.__ |
| 5 | Terminate, cap and remove existing gas lines from the building | JOB | 1 | $ ____.__ | $ ____.__ |
| 6 | Remove and replace existing gutter system to include and replace down spouts | LF | 110 | $ ____.__ | $ ____.__ |
| 7 | Remove and replace existing roof with new roofing sheets | JOB | 1 | $ ____.__ | $ ____.__ |
| 8 | Remove existing gas fired unit heaters | JOB | 1 | $ ____.__ | $ ____.__ |
| | | | | **GRAND TOTAL** | **$ ____.__** |

Per L.2.1.2.1: "The line-item price shall include all necessary supervision, management, labor, transportation, equipment, materials, any other direct incidental costs, overhead and profit." Translation — **load each CLIN with its share of bonds, GCs, OH, and profit; do not present them as separate lines.**

## F. Cost-allocation strategy for non-CLIN costs

The LPTA bid is the sum of 8 priced CLINs. Bonds, GCs, OH, and profit cannot appear as standalone lines. Allocate them across the CLINs proportionally to direct cost. Suggested algorithm:

1. Compute raw direct cost per CLIN (sub or self-perform labor + material + minor incidentals)
2. Sum all raw direct costs → `RDC_total`
3. Compute total bid (RDC_total × (1 + GC% + bond% + insurance% + OH% + profit% + contingency%))
4. For each CLIN, allocated bid price = `RDC_clin / RDC_total × total_bid`
5. Round each allocated price to even dollars; force the grand total to match by adjusting the largest CLIN (typically 0007).

This keeps unit prices honest while passing the M.1.9 conformance check. Alternative: load heavier-percentage OH+P on the labor-rich CLINs (0003, 0008) and lighter on the material-rich CLINs (0001, 0004) — only do this if the firm's actual cost basis supports it.

## G. Variation in estimated quantity (52.211-18)

CLIN 0006 (gutter at 110 LF est.) is the only quantity-typed line that can vary; the others are JOB or EA-with-fixed-count.

- If actual gutter LF is between **93.5 LF (85%) and 126.5 LF (115%)**, no equitable adjustment; bid unit price applies.
- If actual LF is < 93.5 OR > 126.5, contractor or government may request an equitable adjustment for the variance above 115% or below 85% only.
- Site-visit measurement is the right time to true this number up. If actual is materially different from 110 LF, raise an RFI to update the estimate; don't bake the difference into the unit price.

## H. JSON mirror of this mapping

The `takeoff-template.json` file contains the same 8 CLINs in `core.schemas.Estimate` / `CostLine` shape, with quantity placeholders that can be filled after the site visit and then priced via `core.estimator.price_takeoff` or by hand. See that file for the structured / pipeline-consumable view.
