# CHS Cafeteria Serving Line Renovation — Texas Prevailing-Wage Checklist

> **Statute:** Tex. Gov't Code Ch. 2258 — state-funded construction work requires payment of the county prevailing wage rate per trade.
> **County:** `Johnson` County, Texas

## 1. Wage-table source

| Item | Value |
|---|---|
| Wage table source | `SAM.gov Davis-Bacon, Johnson County, TX (Cleburne ISD adopted)` (per CSP Attachment / TFC / county / TX Workforce Commission) |
| Wage table filename | `Davis-Bacon Prevailing Wage Rates for Johnson County (SAM.gov; attached to RFCSP)` |
| Wage table effective date | `Per RFCSP Attachments tab (effective at issue date 2026-05-20)` |
| Wage table archived in workspace at | `bids/{{SLUG}}/wage-table/` |

## 2. Trade rates applied (per CSI / per CLIN)

| Trade | CSI division | Wage classification | Hourly rate per `Davis-Bacon Prevailing Wage Rates for Johnson County (SAM.gov; attached to RFCSP)` | Fringe per WD | Total rate | BPC firm rate | Uplift if firm < prevailing |
|---|---|---|---|---|---|---|---|
| `{{TRADE}}` | `{{CSI}}` | `{{CLASS}}` | $`{{HOURLY}}` | $`{{FRINGE}}` | $`{{TOTAL}}` | $`{{FIRM}}` | $`{{UPLIFT}}` |

## 3. Pricing impact

Sum of (`{{UPLIFT}}` × annual labor hours forecast for the project) = `{{TOTAL_UPLIFT_$}}` added to direct labor cost. Carry in `08-pricing-strategy.md`.

## 4. Compliance discipline (post-award)

- [ ] Weekly certified payroll for prime + every sub tier (TX Comptroller TX-specific certified-payroll form, NOT federal WH-347)
- [ ] Per-employee accurate rate + fringe payment, on-the-record (no off-the-books cash labor)
- [ ] On-site posting of prevailing wage rates per trade (per TWC rule)
- [ ] Apprentices documented per TX apprentice program if claimed
- [ ] Sub agreements flow down prevailing-wage obligation
- [ ] BPC retains payroll records for ≥ 3 years (per Ch. 2258)
- [ ] If `Cleburne ISD` has additional prevailing-wage clauses in SGC, comply with both
- [ ] Withholding for non-compliance = `$60/day per violation` per Ch. 2258 §2258.023

## 5. Federal-funded overlay

If any portion of this project is federally funded (rare on pure-state CSPs but possible on hybrid funding):

- [ ] Davis-Bacon Act (DBA) overrides Ch. 2258 for the federally-funded portion
- [ ] Federal WH-347 weekly for federally-funded scope
- [ ] DOL WD attached as separate wage table

## 6. Counties commonly covered

As BPC's bid pipeline cycles through TX counties, cache each county's prevailing-wage table in [`firm/compliance/README.md → §10 Prevailing-wage tables cache`](../../../firm/compliance/README.md).

Common counties to expect (refresh tables annually):

- Brazos County (TAMU College Station)
- Tom Green County (Angelo State, San Angelo)
- Lubbock County (Texas Tech)
- Bexar County (TAMU-San Antonio, UTSA, ACC)
- Travis County (UT Austin, City of Austin)
- Harris County (UH, TSU, Houston ISD)
- Dallas County (UTSW, UT Dallas, Dallas ISD)
- Tarrant County (TAMUFW, City of Fort Worth, Fort Worth ISD)
- Hays County (Texas State University)
- McLennan County (Baylor, Waco-area)
- Hidalgo County (UT Rio Grande Valley)
- Collin County (City of Frisco, City of McKinney, City of Plano)
- Denton County (UNT)
