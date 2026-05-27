# {{PROJECT_NAME}} — Scope of Work

> **Source:** CSP package — drawings + Project Manual + Notice of Project §00 11 13.
> **Scope template to paste from:** pick one from [`firm/scope-templates/`](../../../firm/scope-templates/README.md) that matches the project archetype.

## 1. Project summary

`{{ONE_PARAGRAPH_PROJECT_DESCRIPTION}}` — pull from CSP package / Project Manual scope section.

## 2. Contractor vs Owner scope

| Item | Contractor (BPC) | Owner-supplied (OFCI / OFOI) | Notes |
|---|---|---|---|
| Demolition (selective) | ✅ | — | |
| Casework / millwork | `{{C/O}}` | `{{O/C}}` | |
| Lockers (if any) | `{{C/O}}` | `{{O/C}}` | Verify — Angelo State Carr EFA had a late OFCI → CFCI scope-flip on lockers |
| Lab equipment / fume hoods (if lab) | typically OFOI | ✅ | BPC coordinates connection |
| Window treatments | `{{C/O}}` | `{{O/C}}` | |
| Furniture (FF&E) | typically OFOI | ✅ | |
| Specialty signage / wayfinding | `{{C/O}}` | `{{O/C}}` | |
| Audiovisual / IT / data-network active equipment | typically OFCI | ✅ | BPC pulls pathway / cable |
| Structured cabling | `{{C/O}}` | `{{O/C}}` | Verify per CSP — often ambiguous |
| Owner's-rep / Cx agent fees | — | ✅ | |

## 3. Trade-by-trade scope

`[Paste from matching firm/scope-templates/ template, then refine against CSP package.]`

| Trade | CSI section | BPC self / sub | Quantity placeholder | Notes / assumptions |
|---|---|---|---|---|
| Mobilization + temp protection | 01 50 00 | Self | LS | Dust-tight barricades; temp HVAC if needed |
| Selective demolition | 02 41 19 | Sub | SF / LF | |
| Abatement (if triggered) | 02 82 13 | Sub (TDSHS-licensed) | SF | |
| Casework / millwork | 06 41 00 | Sub | LF base + LF wall + LF top | Verify epoxy / phenolic if lab |
| Doors / frames / hardware | 08 11 13 / 08 14 16 / 08 71 00 | Sub (material) + carpenter (install) | each | |
| Drywall + framing | 09 22 16 / 09 29 00 | Sub | LF + SF | Mold-resistant if wet adjacent |
| Acoustic ceilings | 09 51 23 | Sub | SF | |
| Resilient flooring | 09 65 19 (LVT) / 09 65 16 (sheet vinyl) | Sub | SF | Welded seams if lab / wet |
| Tile (if wet rooms) | 09 30 13 | Sub | SF wall + SF floor | Epoxy grout in wet rooms |
| Lockers (if any) | 10 51 13 | Sub | each | |
| Toilet partitions + accessories | 10 21 13 + 10 28 13 | Sub | each | |
| Paint | 09 91 23 | Sub | SF | Eggshell / semi-gloss per spec |
| Electrical | 26 27 26 / 26 51 19 | Sub | each | GFCI in wet; LED |
| HVAC | 23 series | Sub | tonnage / VAV | DDC integration if existing BMS |
| Plumbing | 22 41 00 / 22 13 19 | Sub | each | |
| Fire sprinkler mods | 21 13 13 | Sub (NICET) | each | |
| Low-voltage / Cat 6A | 27 11 00 | Sub | each drop / LF | |
| Specialty (lab gas, eyewash, DI, vacuum if lab) | 22 66 00 | Sub | each | |
| Punch + final clean | 01 77 00 / 01 78 00 | Self | LS | |
| Closeout (as-builts, O&M, warranty, training) | 01 78 23 / 39 / 01 79 00 | Self | LS | |

## 4. Assumptions (build into the proposal)

- TX prevailing wage per `{{TX_WAGE_FILE}}` for `{{COUNTY}}` County per Tex. Gov't Code Ch. 2258
- TX UGSC 2010 + `{{AGENCY_SHORT}}` SGC Article 5 insurance limits apply
- TX UGSC Article 6 — 5% bid bond, 100% P&P on award
- `{{AGENCY_SHORT}}` SGC supplement governs over base UGSC where they conflict
- Building remains: `{{OCCUPIED_OR_VACATED}}` during construction
- Owner-furnished items: per Section 2 above
- Site access via: `{{SITE_ACCESS_NOTES}}` (badging, escort hours, after-hours window)
- BPC scope ends at: `{{SCOPE_BOUNDARY}}`
- Substantial completion: `{{SC_DAYS}}` cal days; Final Completion: `{{FC_DAYS}}` cal days
- LD rate per `{{AGENCY_SHORT}}` SGC: $`{{LD_RATE}}` per calendar day

## 5. RFI candidates (raise before cutoff)

| # | Topic | CSP reference | Question | Why it matters |
|---|---|---|---|---|
| `{{NUM}}` | `{{TOPIC}}` | `{{REF}}` | `{{QUESTION}}` | `{{IMPACT}}` |
