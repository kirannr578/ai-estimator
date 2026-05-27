# Price references — B1710 Office Refurbishment

This is the rule-of-thumb pricing reference for the 4 main line items in the SOW. Used as a sanity check against the actual price build in `proposal/01-price-proposal.md` and the CWICR matcher hits stored in `11-takeoff-template.json`.

> ⚠️ **All ranges below are DFW-area Davis-Bacon-uplifted 2026 estimates.** For the actual price proposal, run the CWICR matcher and `config/cost_database.json` lookups against the trade descriptions, and apply the +5% quantity contingency (no site walk per `07-risk-register.md` R2). Final lump-sum should be the build-up here cross-checked against the matcher hits, not either alone.

## 1. Carpet tile install — 24"×24" 100% nylon (Shaw Constellat EW24 or equal)

| Cost component | Range ($/SF installed) | Driver |
|---|---|---|
| Shaw Constellat EW24 tile (material, Style 59326) | $4.50 – $6.50 / SF | Spec-quality commercial Nylon Type 6,6; dye-lot match available |
| Adhesive (release / pressure-sensitive) | $0.30 – $0.60 / SF | Shaw spec'd release adhesive for tile applications |
| Floor leveler (where required) | $1.50 – $3.50 / SF over leveled area (~10-15% of total) | SOW intro: "level flooring before new carpet squares are placed" |
| Installation labor (Davis-Bacon TX20260270 Floor Layer) | $2.50 – $4.00 / SF | Includes layout, cut, install, seal |
| **Total installed range** | **$7.80 – $14.60 / SF** | High end accounts for spec-grade carpet + leveler + DBA labor |

For 3,500 SF: **$27,300 – $51,100** (range)
Mid-point estimate: **$36,000 – $42,000**

If using or-equal substitute (Mohawk SmartStrand, Interface 24×24): subtract $1-2/SF from material = ~$3,500-7,000 cost reduction. Document substitution explicitly per `04-evaluation-strategy.md` §5.

### CWICR / cost_database.json cross-check

> **`[AWAITING CWICR MATCHER RUN]`** — to unblock: run the existing matcher against descriptions:
> 1. `Carpet tile, 100% nylon, 24x24, commercial Grade A, installed`
> 2. `Carpet tile, glue-down adhesive method, light commercial`
> 3. `Self-leveling floor underlayment, cementitious, 1/8 inch`
> Compare against the ranges above; adjust mid-point if matcher confidence > 0.7.

## 2. Rubber cove base — 6", gray

| Cost component | Range ($/LF installed) | Driver |
|---|---|---|
| 6" rubber base (Roppe / Johnsonite / Burke Mercer) | $1.00 – $1.80 / LF | Gray, commercial grade; samples for owner selection per SOW |
| Adhesive (cove-base cement) | $0.10 – $0.20 / LF | Standard practice |
| Installation labor (Floor Layer, DBA) | $1.80 – $3.20 / LF | Includes cope/miter at corners, scribe to walls |
| **Total installed range** | **$2.90 – $5.20 / LF** | |

For 1,300 LF (estimate; field-verify): **$3,770 – $6,760** (range)
Mid-point: **~$5,000**

## 3. Paint — walls (primer + 2 coats interior latex eggshell, SW 7029 Agreeable Gray)

| Cost component | Range ($/SF wall area) | Driver |
|---|---|---|
| Primer (SW PrepRite ProBlock or similar) — 1 coat where bare/repair | $0.20 – $0.40 / SF | Selective application |
| Finish paint — 2 coats SW ProMar 200 eggshell, color SW 7029 | $0.55 – $0.90 / SF | Commercial spec; ~250 SF/gal coverage at 2 coats |
| Surface prep (patch, sand, caulk, masking) | $0.30 – $0.60 / SF | Per SOW §C "Patch/Fill Holes/Prepare surface" |
| Labor (Painter, DBA) | $1.20 – $2.20 / SF | Includes cut-in + roll, 2 coats, drying-time scheduling |
| **Total range** | **$2.25 – $4.10 / SF** | |

For ~13,500 SF wall area (estimate based on 3.5 SF-wall per 1 SF-floor for typical 9-ft office + hallway): **$30,400 – $55,400** (range)
Mid-point: **~$42,000**

> ⚠️ **Paint SF is the most volatile number in this estimate.** The SOW says "paint all identified surfaces" without specifying a take-off basis. Three possibilities:
> 1. **Walls only, in C/B/P rooms + hallway** — ~13,500 SF (the estimate above)
> 2. **Walls + ceilings, in C/B/P rooms + hallway** — ~16,500 SF (add ceiling SF roughly equal to floor SF)
> 3. **Walls only, in C/B/P rooms but NOT hallway** — ~9,500 SF
>
> The plan annotation "paint all hallway" suggests scenario 1. The wider interpretation (scenario 2) is more conservative. **Recommended: quote scenario 1 in the lump-sum number; mention scenario 2 as a price-add in the cover letter if the CO clarifies "paint all surfaces" to mean walls + ceilings.**

## 4. Drywall — Rm 1030 doorway in-fill + Rm 1008 patch + access panel

| Cost component | Range ($) | Driver |
|---|---|---|
| Rm 1030 metal-stud framing (7 LF stud, 3-5/8" or 6") | $80 – $140 | Material + labor |
| Rm 1030 GWB (42 SF, both sides 5/8" Type X) | $140 – $220 | Material + labor |
| Rm 1030 tape/bed/texture/prime/paint | $180 – $280 | Standard repair to match adjacent finish |
| Rm 1008 wall patch (16 SF GWB) | $120 – $180 | Patch + tape/bed/texture/prime/paint |
| Access panel — 12"×12" Karp DSB-214M valve-rated | $80 – $150 | Material |
| Access panel install labor (Carpenter, DBA) | $60 – $120 | Layout, cut, install |
| **Total range** | **$660 – $1,090** | Round to ~$900 mid-point |

## 5. General conditions + overhead + profit

| Line item | Range ($) | Driver |
|---|---|---|
| Mobilization / demobilization (truck, base-access coordination, sub coordination) | $1,200 – $2,400 | 2 mobilizations × ~$1K each; DBA-flag base-access vetting |
| Project management + supervision (Rocky on-site / available) | $2,500 – $5,000 | Owner-PM rate × ~6-10 day on-site over 90 cal day PoP |
| Dumpster / debris disposal (~10 CY roll-off) | $450 – $900 | Tarrant Co tipping fee + haul; double if 2 hauls |
| Furniture relocate / restore (16 rooms, 2-person crew × 3-4 days) | $1,400 – $2,800 | DBA Laborer rate |
| Site cleanup / daily cleanup labor | $600 – $1,200 | Built into general conditions |
| Certified payroll prep + WH-347 admin (~13 weeks × $50-200/wk) | $650 – $2,600 | DBA compliance overhead |
| **Subtotal GCs** | **$6,800 – $14,900** | |
| Overhead (% of direct cost) | 8 – 12% | Small firm baseline |
| Profit (% of direct cost) | 8 – 12% | Standard fixed-fee bid markup |

## 6. Build-up summary — full lump-sum range

| Line item | Low | Mid | High |
|---|---:|---:|---:|
| Carpet tile install (3,500 SF) | $27,300 | $36,000 | $51,100 |
| Floor leveler (~10% of area) | $500 | $1,000 | $1,500 |
| Rubber base 6" gray (~1,300 LF) | $3,800 | $5,000 | $6,800 |
| Paint walls (~13,500 SF) | $30,400 | $42,000 | $55,400 |
| Drywall + access panel | $660 | $900 | $1,100 |
| **Direct subtotal** | **$62,660** | **$84,900** | **$115,900** |
| General conditions | $6,800 | $10,000 | $14,900 |
| **Subtotal pre-OH/P** | **$69,460** | **$94,900** | **$130,800** |
| Overhead (10%) | $6,946 | $9,490 | $13,080 |
| Profit (10%) | $6,946 | $9,490 | $13,080 |
| **Lump-sum range** | **$83,400** | **$113,900** | **$157,000** |
| 5% quantity contingency | $4,170 | $5,695 | $7,850 |
| **Final lump-sum with contingency** | **~$87,500** | **~$119,600** | **~$164,900** |

> ⚠️ **The mid-point estimate above (~$120K) is HIGHER than the "$25K-$100K typical band" assumption in `00-overview.md` and `01-bid-prep-checklist.md`.** This is driven primarily by the paint SF assumption (13,500 SF wall area). If paint scope is narrower (scenario 3 above, ~9,500 SF), the mid-point drops to ~$95K.
>
> **The realistic bid range is $80K–$135K all-in** depending on:
> - Paint scope interpretation (walls only / walls + ceilings / partial)
> - Whether floor leveler is needed in 10% of the area (worst case) vs <5% (best case)
> - Whether furniture relocation is a 2-day or 5-day effort
> - Subcontracted flooring quote (could shave $5-10K if sub is competitive)
>
> **Recommended target: $90,000 – $105,000** for the initial price build. Refine after Gate 2 takeoff and Gate 4 sub-quote intake.

## 7. Competitor band (informational)

Plausible competing offerors on this RFQ:
- Other DFW-area small-business GCs in the $5M-$30M revenue range with prior AFRC / DoD experience
- TX HUB-certified firms running the AFRC route
- Specialty flooring contractors operating under a small-business GC umbrella

Typical AFRC SAP construction at NAS JRB Fort Worth in the $50K-$100K band attracts 3-7 offerors. The winning bid in a comparative-evaluation regime is typically NOT the lowest; it is the lowest among offerors with credible past performance.

## 8. CWICR matcher pull (when to run)

Run before Fri 11:00 (Gate 4.6). Commands (PowerShell):

```powershell
# From the repo root with .venv activated
$matches = .\.venv\Scripts\python.exe -c "
from core.cwicr import match_descriptions
print(match_descriptions([
    'Carpet tile, 24x24, 100% nylon, commercial grade A, installed glue-down',
    'Rubber cove base, 6 inch, gray, commercial, installed',
    'Interior latex paint, eggshell, 2 coats over primer, on prepared drywall',
    'Drywall, 5/8 inch Type X, GWB, taped and finished, in-wall infill at door opening',
    'Self-leveling underlayment, cementitious, 1/8 inch over slab',
])"
$matches | Format-Table
```

(The exact API is documented in `core/cwicr/` and `config/cost_database.json` — see that module for the function signature. If `match_descriptions` is not the right name, use the `core/cwicr/__init__.py` exports.)
