# Cost database v2 — public-domain expansion

**File:** `config/cost_database.json`
**Schema:** unchanged from v1 (see `core/estimator.py::CostDatabase`)
**Entry count:** 45 → 128 (+83)
**Snapshot year:** 2024 (a handful of 2025 GSA / EPA values where current)
**Currency:** USD, national-average
**Status:** seed data only — escalate forward via `core/pricing/escalation.py`

---

## Why this exists

BPC has no internal historical pricing database. Until the firm closes
enough projects in a given trade to build its own median, the parametric
estimator needs a *defensible seed* of national-average unit prices to
fall back on after the CWICR matcher misses (CWICR similarity below
0.55, or row absent for the trade entirely).

v1 of `cost_database.json` shipped ~45 hand-seeded rows covering a
"generic light-commercial / residential build". The capability library
is now scaffolding scope templates for five additional trade families
that v1 didn't cover at all — every priced takeoff in those families was
landing on the `(no match)` placeholder line.

v2 adds ~80 rows sourced exclusively from **public-domain** references
so the firm carries zero licensing exposure on the seed values. Every
new row cites its source in the `notes` field.

## What changed

### Schema — unchanged

The JSON schema is the same as v1:

| Field           | Type     | Required | Notes                                                                                       |
|-----------------|----------|----------|---------------------------------------------------------------------------------------------|
| `description`   | str      | yes      | Human description; appears in priced exports.                                               |
| `unit`          | str      | yes      | One of `LF`, `SF`, `CY`, `CF`, `EA`, `TON`, `GAL`, `HR`, `MO`, `LS`, etc.                   |
| `unit_cost`     | number   | yes      | Per-unit price in USD. National average, pre-regional-multiplier.                           |
| `cost_category` | enum     | yes      | One of `labor`, `material`, `equipment`, `subcontractor`, `other` (see `core/schemas.py`).  |
| `waste_factor`  | float    | yes      | `>= 1.00`. Multiplies takeoff quantities at price time. Estimator clamps to `>= 1.00`.      |
| `keywords`      | list[str]| yes      | Keyword fallback when the takeoff csi_section doesn't exactly match a key.                  |
| `notes`         | str      | v2 only  | Source citation (e.g. `Source: FEMA P-784 2024 ...`). Free-form, human-readable.            |

**Note on `cost_category`:** the prompt that drove the expansion referenced
`"subcontract"` but the canonical schema enum is `subcontractor`. v2 uses
the schema-valid `subcontractor` value; turnkey-sub bundles (e.g. the
maple sport-floor panel system, the Type I exhaust hood w/ Ansul) are
tagged `subcontractor` and the turnkey nature is called out in the
`notes` field.

### Five new trade families

| Family                          | Lead CSI division(s)         | New rows |
|---------------------------------|------------------------------|----------|
| 1. Food-service / cafeteria     | 11 41, 11 45, 22 13, 23 38   | 19       |
| 2. Restroom renovation - historic | 02 41, 09 30, 22 41, 10 28 | 14       |
| 3. Roof repair - historic       | 07 25, 07 31, 07 41, 07 62   | 15       |
| 4. Security fence - perimeter   | 32 31, 28 13, 31 11, 31 22   | 18       |
| 5. Gymnasium multi-system       | 09 64, 09 65, 12 66, 23 74   | 17       |
| **Total new**                   |                              | **83**   |

Plus utility rows for CSI 01 35 91 (historic-preservation labor premium),
07 01 90 (NPS Preservation Brief 4 / 29 compliance review), 03 54 16
(self-leveling underlayment for sport flooring), and 06 10 13 (historic
roof carpenter hourly rate).

## Public-domain source references

Every v2 row cites at least one of these. Substitute current-year
publications as they're released.

| Token in `notes`                 | Source                                                                                          | URL                                                                                                |
|----------------------------------|-------------------------------------------------------------------------------------------------|----------------------------------------------------------------------------------------------------|
| `FEMA P-784` / `FEMA P-499`      | FEMA disaster-recovery unit-cost & coastal-construction manuals                                 | https://www.fema.gov/grants/policy-guidance/individual-assistance/cost-codes                       |
| `GSA Schedule 56`                | GSA Multiple Award Schedule — Buildings & Building Materials                                    | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 73`                | GSA MAS — Food Service / Hospitality / Cleaning Equipment & Supplies                            | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 78`                | GSA MAS — Sports, Promotional, Outdoor, Recreational, Trophies & Signs                          | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 84`                | GSA MAS — Law Enforcement, Security, Facilities Management, Fire, Rescue                        | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 58 I`              | GSA MAS — Audio-Visual Equipment                                                                | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 03FAC`             | GSA MAS — Facilities Maintenance & Management                                                   | https://www.gsaadvantage.gov                                                                       |
| `GSA Schedule 71 II`             | GSA MAS — Household & Industrial Furniture (incl. Hardware sub-line)                            | https://www.gsaadvantage.gov                                                                       |
| `NAHB 2024 Cost of Constructing a Home` | NAHB Cost of Constructing a Home, 2024 annual report                                     | https://www.nahb.org/research-and-economics/housing-economics/cost-of-constructing-a-home          |
| `AGC Q2-2024 ...`                | AGC quarterly construction cost-impact report (Q2 2024 + later quarters)                        | https://www.agc.org/learn/construction-data                                                        |
| `USACE EM 1110-2-1304`           | USACE Civil Works Cost Engineering — construction equipment ownership and operating cost manual | https://www.usace.army.mil/cost-engineering/                                                       |
| `USACE EM 1110-3-138`            | USACE EM 1110-3-138 — Pavement Design for Roads, Streets, and Open Storage                      | https://www.usace.army.mil/cost-engineering/                                                       |
| `HUD 2024 ADA-retrofit cost guide` | HUD Section 3 construction cost guide & ADA-retrofit unit-cost tables                         | https://www.huduser.gov/portal/datasets/cnstcost.html                                              |
| `Bureau of Reclamation 2024`     | USBR construction cost trends report                                                            | https://www.usbr.gov/tsc/techreferences/                                                           |
| `NPS Preservation Brief 4`       | National Park Service Preservation Brief 4 — *Roofing for Historic Buildings*                   | https://www.nps.gov/orgs/1739/upload/preservation-brief-04-roofing.pdf                             |
| `NPS Preservation Brief 9`       | NPS Preservation Brief 9 — *The Repair of Historic Wooden Windows*                              | https://www.nps.gov/orgs/1739/upload/preservation-brief-09-wooden-windows.pdf                      |
| `NPS Preservation Brief 24`      | NPS Preservation Brief 24 — *Heating, Ventilating, and Cooling Historic Buildings*              | https://www.nps.gov/orgs/1739/upload/preservation-brief-24-mechanical-systems.pdf                  |
| `NPS Preservation Brief 28`      | NPS Preservation Brief 28 — *Painting Historic Interiors*                                       | https://www.nps.gov/orgs/1739/upload/preservation-brief-28-painting-historic-interiors.pdf         |
| `NPS Preservation Brief 29`      | NPS Preservation Brief 29 — *The Repair, Replacement, and Maintenance of Historic Slate Roofs*  | https://www.nps.gov/orgs/1739/upload/preservation-brief-29-slate-roofs.pdf                         |
| `NPS Preservation Brief 40`      | NPS Preservation Brief 40 — *Preserving Historic Ceramic Tile Floors*                           | https://www.nps.gov/orgs/1739/upload/preservation-brief-40-ceramic-tile.pdf                        |
| `BLS OEWS 2024`                  | BLS Occupational Employment and Wage Statistics (May 2024)                                      | https://www.bls.gov/oes/                                                                           |
| `EPA WaterSense 2024`            | EPA WaterSense product list                                                                     | https://www.epa.gov/watersense                                                                     |
| `NFPA 96`                        | NFPA 96 — Standard for Ventilation Control and Fire Protection of Commercial Cooking Operations | https://www.nfpa.org/codes-and-standards/all-codes-and-standards                                   |

## How to use these seeds

These prices are **point-in-time** (mostly Q2/Q3 2024). Do **not** quote
them directly to a client without escalation. The estimator pipeline
already wires this up:

1. **Per-row keyword + section match.** `CostDatabase.lookup` (in
   `core/estimator.py`) consults the seed DB after CWICR misses.
2. **Region multiplier.** Applied at price time via the
   `region_multiplier` arg on `price_takeoff`.
3. **Time-basis escalation.** `core/pricing/escalation.py` reads the
   BLS PPI series (WPU)
   for the relevant trade (e.g., `WPU0811` for cedar, `WPU101` for
   metal) and brings the seed cost forward from the 2024 snapshot to
   the estimate's quote date.

The seed should be re-snapped to the latest published values once a
year. Track that as a recurring task in
`docs/ROADMAP_TAKEOFF_AUTOMATION.md`.

## What v2 does *not* include

- **Internal historical prices.** BPC's closed-job actuals belong in
  the CWICR feed (or a successor internal-data file), not here. Mixing
  the two would erase the audit trail this file is supposed to provide.
- **Regional adjustments.** Apply `region_multiplier` at estimate time.
- **Tax / bonding / GC overhead.** Captured by the `overhead_pct` and
  `profit_pct` controls on the `Estimate` object.
- **Specialty / proprietary equipment.** When a project calls for a
  named product (specific scoreboard model, branded modular sport
  floor), use a project-specific override file and leave the seed at
  the generic line price.

## Maintenance checklist

When editing this file:

- [ ] Add new rows in CSI-key sort order. `tests/test_cost_database_expansion.py::test_entries_sorted_by_csi` will fail otherwise.
- [ ] Keep `_meta.version` bumped when the entry-set shape changes (added family, schema field, etc.).
- [ ] Cite a public source in `notes` for every new row.
- [ ] Keep `waste_factor` in the `1.00 – 1.20` band; outside that, document the reason in `notes`.
- [ ] Use a recognised unit (`LF`, `SF`, `CY`, `CF`, `EA`, `TON`, `GAL`, `HR`, `MO`, `LS`).
- [ ] Prefer dimensional units (`LF`, `SF`, `CY`, `EA`) over `LS` where a dimensional measure is plausible.
- [ ] Run `pytest tests/test_cost_database_expansion.py` before pushing.
