# `firm/compliance/` — BPC compliance asset registry

This registry is the **single source of truth** for what compliance assets Blueprint Constructs holds, where each one lives, when it expires, and what to do about it. Every bid response under `bids/<slug>/` should reference this registry — not its own copy of the data — to keep firm-level facts consistent across all live bids.

> ⚠️ **Many of the items below are currently stale or missing per source files extracted in 2025.** The registry surfaces the gaps; closure is the user's action item. Do **not** submit any bid that depends on a `🔴` item until that row is refreshed.

## Status key

- ✅ Active, current, on file
- ⚠️ Active but verify currency / refresh before next bid
- 🔴 Expired, missing, or unknown — **bid-blocking** if the procurement requires it
- ⬜ Not applicable to BPC

## 1. Federal-government registrations

| Asset | Value | Where it lives | Expires / Renewal | Status | Action |
|---|---|---|---|---|---|
| **SAM.gov entity registration** | Active per user (2026-05-23) | SAM.gov (record key: UEI below) | Annual; specific expiration date TBD | ⚠️ | Pull SAM entity-info PDF before each federal bid; verify Reps & Certs, EFT, TIN refresh currency |
| **Unique Entity ID (UEI)** | `LM4YHVQ71QG7` | SAM.gov; `firm/firm-profile.json → uei` | Tied to SAM registration | ✅ | — |
| **CAGE Code** | `9LET0` | SAM.gov + DLA; `firm/firm-profile.json → cage_code` | Tied to SAM registration | ✅ | — |
| **Employer Identification Number (EIN)** | `87-4292998` | IRS; `firm/firm-profile.json → ein` | Permanent | ✅ | — |
| **Reps & Certs (FAR 52.204-8)** | Auto-populated from SAM | SAM.gov | Annual (rolling 12-month) | ⚠️ | Verify in SAM ≤ 12 months old before each federal bid |
| **EFT banking info in SAM** | On file | SAM.gov | Refresh on banking change | ⚠️ | Verify before each federal bid |
| **FASCSA reps (FAR 52.204-29)** | Boilerplate "does not / will not" | SAM.gov Reps | Same as Reps & Certs | ⚠️ | Confirm in SAM |
| **Section 889 reps (FAR 52.204-24/-25/-26)** | Boilerplate "does not / will not provide" | SAM.gov Reps | Same as Reps & Certs | ⚠️ | Confirm in SAM |
| **Buy American reps (FAR 52.225-2 / -20 / -25)** | Boilerplate yes | SAM.gov Reps | Same as Reps & Certs | ⚠️ | Confirm in SAM |
| **FAR 52.204-21 Basic Safeguarding posture** | Implemented at firm IT level | Firm IT | Continuous | ⚠️ | Document one-time validation; refresh annually |
| **Section 3 (HUD) Business Concern self-cert** | Per project | Per bid | Per bid | ⬜ | Only if HUD-funded |

## 2. SBA + small-business certifications

| Asset | Value | Where it lives | Expires / Renewal | Status | Action |
|---|---|---|---|---|---|
| **NAICS code — primary** | 236220 (Commercial + Institutional Building Construction) | SAM.gov + `firm/firm-profile.json → naics_codes` | — | ✅ | — |
| **NAICS codes — secondary** | 236115, 236116, 236118, 236210 (residential, single-family, multi-family, land subdivision) | SAM.gov + `firm/firm-profile.json` | — | ✅ | — |
| **SBA small-business self-cert on 236220** | Self-attested small (≤ $45M 3-yr avg revenue) | SAM.gov | Annual | ⚠️ | Verify 3-yr avg revenue ≤ $45M before each federal bid |
| **SBA size standard for 236220** | $45.0M (current per SBA 13 CFR 121) | SBA | — | ✅ | — |
| **HUBZone certification** | Not held per source | n/a | n/a | ⬜ | — |
| **8(a) Business Development certification** | Not held per source | n/a | n/a | ⬜ | — |
| **WOSB / EDWOSB** | Not held per source | n/a | n/a | ⬜ | — |
| **SDVOSB / VOSB** | Not held per source | n/a | n/a | ⬜ | — |
| **DBE (federal Disadvantaged Business Enterprise)** | Not held per source | n/a | n/a | ⬜ | — |
| **SBE (DFW MSDC)** | `DL09279` | `firm/firm-profile.json → licenses_and_certifications` | **Renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`** (prior cycle expired 2024-08-31 per source) | ✅ | Capture new expiration date once user supplies; refresh source cert PDF in `BPC/` |
| **MBE (DFW MSDC, NMSDC affiliate)** | `DL09279` | `firm/firm-profile.json` | **Renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`** (prior cycle expired 2024-08-31 per source) | ✅ | Capture new expiration date once user supplies; cascades into TX HUB recognition under DFW MSDC / TX Comptroller MOU |

## 3. Texas state-government registrations

| Asset | Value | Where it lives | Expires / Renewal | Status | Action |
|---|---|---|---|---|---|
| **TX HUB cert** | VID `1874292998900` | TX Comptroller; `firm/firm-profile.json → licenses_and_certifications` | **Renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`** (prior cycle expired 2024-08-31 per source) | ✅ | Capture new expiration date once user supplies; refresh source cert PDF in `BPC/`; reconfirm before any HSP that claims HUB self-perform credit |
| **TX SOS file number** | `0804376974` | TX Secretary of State; `firm/firm-profile.json → sos_file_number` | Permanent (annual public-information report due) | ⚠️ | Verify annual report filed |
| **TX Comptroller Taxpayer ID** | `32082600456` | TX Comptroller; `firm/firm-profile.json → tx_taxpayer_id` | Permanent | ✅ | — |
| **TX Comptroller franchise-tax good standing** | Assumed current; verify per bid | TX Comptroller — Taxable Entity Search | Annual (May 15 cycle) | ⚠️ | Verify via [Taxable Entity Search](https://mycpa.cpa.state.tx.us/coa/) before each TX state bid |
| **TX Comptroller WebFile ID** | `XT287610` | `firm/firm-profile.json → tx_webfile_id` | — | ✅ | — |
| **TX CMBL (Centralized Master Bidder List)** | Unknown | TX SmartBuy | Annual | 🔴 | Enroll / confirm enrollment |
| **TX state-vendor #** | Unknown | Per agency | Per agency | 🔴 | Confirm per agency |
| **TX COMET vendor account** | Unknown | TX Comptroller COMET | Per agency | 🔴 | Confirm per agency requiring it |
| **TAMU System SSC vendor account / Master Vendor Agreement** | Unknown | SSC Vendor Portal | Per MVA | 🔴 | Confirm before TAMU System bids |
| **TTUS member-institution vendor accounts (TTU / ASU / TTUHSC)** | Unknown | Per FP&C / Procurement | Per agency | 🔴 | Confirm per ASU / TTU / TTUHSC bid |
| **UT System member-institution vendor accounts** | Unknown | Per agency | Per agency | 🔴 | Confirm per UT bid |
| **HB 1295 Certificate of Interested Parties capability** | Standard procedure | TX Ethics Commission portal | Per contract ≥ $1M | ✅ | File per bid via TEC portal |
| **CIQ Form (Tex. Local Gov't Code Ch. 176)** | Standard form | Filled per bid | Per bid | ✅ | Fill per bid |

## 4. Trade + GC licenses

| Asset | Value | Where it lives | Expires / Renewal | Status | Action |
|---|---|---|---|---|---|
| **TX RCAT (Roofing Contractor)** | Not on file | — | — | 🔴 | Confirm if held; otherwise mark N/A on bids requiring |
| **EPA RRP (Lead-Safe)** | Not on file | — | 5-year cycle | 🔴 | Confirm if held; mandatory for pre-1978 residential / child-occupied work |
| **City of Frisco GC license** | Unknown — preferred-vendor status only mentioned | City of Frisco Building Inspections | Annual | 🔴 | Confirm + acquire if needed |
| **City of McKinney GC license** | Unknown — preferred vendor | City of McKinney | Annual | 🔴 | Confirm |
| **City of Plano GC license** | Unknown | City of Plano | Annual | 🔴 | Confirm |
| **City of Dallas GC license** | Unknown — preferred vendor | City of Dallas | Annual | 🔴 | Confirm |
| **City of Little Elm GC license** | Unknown | City of Little Elm | Annual | 🔴 | Confirm |
| **TX TDLR Electrical (if self-perform electrical)** | Not on file | — | — | ⬜ | Probably N/A — BPC subs electrical |
| **TX TSBPE Plumbing (if self-perform plumbing)** | Not on file | — | — | ⬜ | Probably N/A — BPC subs plumbing |

## 5. Insurance

| Asset | Carrier + policy | Limits | Expires | Status | Action |
|---|---|---|---|---|---|
| **Commercial General Liability** | American Builders Insurance Company RRG, policy `SBCC-042443-00` (via Appalachian Underwriters) | $1M occurrence / $2M aggregate / $2M products-completed-ops / $1M personal-and-advertising | 2024-09-25 per source | 🔴 | Pull current COI from agent; verify Additional Insured + waiver of subrogation + primary/non-contributory endorsements available; verify $5M umbrella if institutional bids require |
| **Workers' Compensation (TX statutory)** | Not on file | TX statutory | Unknown | 🔴 | Pull current COI |
| **Commercial Auto Liability** | Not on file | typically $1M CSL | Unknown | 🔴 | Pull current COI |
| **Umbrella / Excess Liability** | Not on file | typically $5M – $10M | Unknown | 🔴 | Pull current COI; verify $5M minimum for TAMU / TTUS bids |
| **Builder's Risk (per project)** | Per project | Per contract | Per project | ⬜ | Procured per project; verify carrier-pool relationship |
| **Pollution Liability (per project)** | Not on file | Per spec | — | ⬜ | Required by some specs (e.g. environmental remediation, abatement) — verify need per bid |
| **Professional Liability / E&O** | Not on file | — | — | ⬜ | Only needed for design-build delivery |

## 6. Bonding

| Asset | Value | Source | Action |
|---|---|---|---|
| **Surety company** | Unknown — image-only scan on file | `BPC/Bond Letter_RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs.pdf` | Surface surety name + agent contact from on-file letter |
| **Single-project bonding capacity** | ≥ $1,000,000 (established by Lavon RV Park $1M performance bond per AIA A101 Article 8) | `firm/firm-profile.json → bonding` | Confirm with agent; refresh bond letter dated within 6 months of any bid |
| **Aggregate bonding capacity** | Unknown | Surety | Confirm with agent |
| **Bid bond capability (5% TX state / 20% federal)** | Yes — order on demand 3–5 working days | Surety | — |
| **Performance + Payment bonds (100% TX state + federal > $150K)** | Yes — order on demand | Surety | — |
| **Bond rate** | Unknown | Surety | Capture for pricing-strategy templates |

## 7. Past-performance project library

| Asset | Value | Source | Action |
|---|---|---|---|
| **Lavon RV Park** (in execution; $1.05M; $1M performance bond) | `firm/proposal-library/past-performance/lavon-rv-park.md` | `firm/firm-profile.json → past_projects[0]` | Capture owner reference contact (`[USER TO FILL]`) |
| **Hindu Temple of Southlake** (in execution; institutional reno) | `firm/proposal-library/past-performance/hindu-temple-southlake.md` | `firm/firm-profile.json → past_projects[1]` | Capture contract value + owner reference contact |
| **Holiday Inn (Hall Park, Frisco)** (commercial reno) | `firm/proposal-library/past-performance/holiday-inn-hall-park.md` | `firm/firm-profile.json → past_projects[2]` | Capture contract value + completion date + owner reference contact |
| **250–500+ SFH portfolio (specialty trade sub)** | Per `firm/firm-profile.json` | `firm/firm-profile.json → past_projects` | Useful for TAMU / TTUS volume-of-work questions |
| **Past-project selection rules per bid type** | `firm/firm-profile.json → past_project_selection_rules` | — | Reference per bid |

## 8. Key personnel — bio paste-readiness

| Personnel | File | Status |
|---|---|---|
| **Principal in Charge (Rocky Nudurupati)** | `firm/proposal-library/key-personnel/principal-in-charge.md` | ✅ Paste-ready, factual |
| **Project Executive** | `firm/proposal-library/key-personnel/project-executive.md` | 🔴 Skeleton — `[USER TO FILL]`; identify or combine with PIC |
| **Project Manager** | `firm/proposal-library/key-personnel/project-manager.md` | 🔴 Skeleton — `[USER TO FILL]`; CRITICAL identification needed |
| **Superintendent** | `firm/proposal-library/key-personnel/superintendent.md` | 🔴 Skeleton — `[USER TO FILL]`; on-site daily role |
| **Site Safety Lead** | `firm/proposal-library/key-personnel/safety-officer.md` | 🔴 Skeleton — `[USER TO FILL]`; combined or dedicated |
| **QA/QC Lead** | `firm/proposal-library/key-personnel/qa-qc-lead.md` | 🔴 Skeleton — `[USER TO FILL]`; combined or dedicated |

## 9. Safety performance (firm)

| Metric | Value | Status | Action |
|---|---|---|---|
| EMR — current year | `[USER TO FILL]` | 🔴 | Pull from WC carrier modification rate notice |
| EMR — prior year | `[USER TO FILL]` | 🔴 | Same |
| EMR — 2 yrs ago | `[USER TO FILL]` | 🔴 | Same |
| EMR — 3 yrs ago | `[USER TO FILL]` | 🔴 | Same |
| OSHA 300/300A — current year | `[USER TO FILL]` | 🔴 | Pull annual posted summary |
| OSHA 300/300A — prior 3 years | `[USER TO FILL]` | 🔴 | Same |
| OSHA recordable incident rate (3-yr) | `[USER TO FILL]` | 🔴 | Compute from 300/300A |
| Lost-workday case rate (3-yr) | `[USER TO FILL]` | 🔴 | Same |
| OSHA citations — current + prior 3 years | `[USER TO FILL]` | 🔴 | Compile from inspection records |
| Fatalities — prior 3 years | `[USER TO FILL]` | 🔴 | Compile (likely zero) |

## 10. Prevailing-wage tables cache (by county / by federal WD)

Build this cache as bids cycle through counties + federal WDs. Each entry is a copy of the controlling rate table, dated, and scoped to a specific bid.

| County / WD | Source (state / federal) | Effective date | Bid using it | File location |
|---|---|---|---|---|
| Hays County, TX | `[USER TO FILL — TWC or USFWS RFP attachment]` | `[USER TO FILL]` | usfws-san-marcos-140FC126R0017 | `bids/usfws-san-marcos-140FC126R0017/wage-determination/` (per workspace) |
| Brazos County, TX | TAMU Harrington CSP attachment | `[USER TO FILL]` | tamu-harrington-2025-06813 | `bids/tamu-harrington-2025-06813/wage-table/` (per workspace) |
| Tom Green County, TX | ASU Attachment F.1 (2023) | 2023 | angelo-state-carr-efa-26-007 | `bids/angelo-state-carr-efa-26-007/` (per workspace) |
| `[next county as it comes in]` | | | | |

## 11. Subcontractor pool

A vetted sub list (per `firm/firm-profile.json → trade_capabilities → subcontract`) belongs here once curated:

- Sub name | trade | HUB cert # + expiration | TX cert # | insurance limits | OSHA EMR | 3 BPC project references | bond capacity | rates last quoted

Current state: not curated; build incrementally as each bid cycles. Target: 3 vetted subs per major trade by EOY 2026.

## 12. Action priority queue (open items, sorted)

These are the items that block bids today. The user (or the bid-prep agent) should triage these in order before / during the next bid cycle:

1. ~~**TX HUB recertification**~~ — ✅ **Closed 2026-05-30 per user confirmation.** Capture new expiration date once user supplies (`[USER TO CONFIRM: new expiration date]`).
2. ~~**MBE / SBE recertification with DFW MSDC**~~ — ✅ **Closed 2026-05-30 per user confirmation.** Same `[USER TO CONFIRM]` placeholder.
3. **Insurance refresh — pull current COIs from agent** (🔴 — blocks any bid that requires COI in submittal; separate from cert renewal above, Commercial GL `SBCC-042443-00` still shows expired 2024-09-25 per source)
4. **Identify + bio + cred each non-PIC key personnel role** (🔴 — blocks any bid requiring named project team)
5. **Confirm SAM.gov registration + Reps & Certs currency** (🔴 if expired — blocks all federal)
6. **Confirm TX Comptroller franchise-tax good standing** (🔴 if not good-standing — blocks all TX state)
7. **TX CMBL enrollment confirmation** (⚠️)
8. **Bond letter — pull current letter + capture surety + agent + capacity** (⚠️ — needed for federal P&P trigger > $150K and TX state CSP bid bond)
9. **Per-county prevailing-wage tables — build cache as bids land** (⚠️)
10. **Past-perf owner-side reference contacts on each of 3 projects** (⚠️ — blocks reference-checkable past-perf claims)
11. **Safety performance numbers (EMR + 300/300A + citation history)** (⚠️ — blocks any bid that scores safety)
