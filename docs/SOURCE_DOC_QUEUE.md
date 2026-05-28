# Source-Document Gap Queue

Generated: **2026-05-28T02:51:37Z**  
Repo HEAD at audit start: **`395daea31a7757da8f35bb18e5c454cde8a61226`**  
Total markers: **1840** across **244** files  
Scope: every `[AWAITING SOURCE DOCS]`, `[USER TO FILL]`, `[TBD]`, `[NEEDS …]`, `[TEMPLATE]`, `[ACTION ITEM]`, `[TO BE DETERMINED]`, `[REQUIRES INPUT]`, `[NOT YET …]`, `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / SUBMISSION DATE), and bare `TBD` token across the working tree, minus `.venv/`, `node_modules/`, `__pycache__/`, `.git/`, `inbox/`, `exports/`, `config/pricing_snapshots/`, `firm/assets/`, `bids/*/proposal/exports/`, `firm/_scripts/_extracted/`, `firm/private/`, `bids/*/local/`, gitignored placeholder reports, this output file, and binary files.  

> **Coordination note** — the audit ran with 7 other workers in flight on disjoint paths writing new content with their own placeholders. Counts here include both committed state (at the HEAD SHA above) **and** uncommitted in-flight working-directory changes from parallel workers, since they share this workspace. Specifically, this audit captures the newly-scaffolded uncommitted workspaces `bids/chs-cafeteria-2026-0608-01/` and `bids/pais-cabin-140P6026Q0029/`, and the new `firm/proposal-library/federal-volumes/` and `firm/proposal-library/hsp/` directories. A follow-up audit pass is recommended once all parallel workers land — see *Refresh procedure* at the bottom.

## Summary by marker type

| Marker | Count | Most common single file |
|---|---:|---|
| `[USER TO FILL]` | 1528 | `bids/usfws-san-marcos-140FC126R0017/proposal/09-site-visit-attendance-memo.md` (109) |
| `TBD` (bare) | 139 | `bids/cmd-post-ndi-W50S7626QA001/04-scope-of-work.md` (18) |
| `[TBD]` | 107 | `bids/tamu-harrington-2025-06813/price-sheet-skeleton.json` (34) |
| `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.) | 41 | `bids/tamu-wehner-fin-340E-2025-06871/price-sheet-skeleton.json` (14) |
| `[AWAITING SOURCE DOCS]` | 10 | `bids/pais-cabin-140P6026Q0029/00-overview.md` (8) |
| `[TEMPLATE]` | 8 | `bids/_TEMPLATES/README.md` (1) |
| `[NOT YET …]` | 7 | `firm/compliance/material-suppliers.md` (6) |

Notes:

- `[USER TO FILL]` is by far the dominant placeholder convention (≈ 80 % of all markers). It is used **both** as a designed slot in `bids/_TEMPLATES/` and `firm/proposal-library/` skeletons **and** as a live gap in copies under `bids/<slug>/`. Template-intrinsic uses are called out separately at the bottom of this document and are **not bugs**.
- The repo's three core placeholder phrasings (used by the scaffolders) are `[USER TO FILL]`, `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / SUBMISSION DATE / SOURCE DOCS), and bracketed `[TBD]`. The other variants (`[NEEDS …]`, `[ACTION ITEM]`, `[TO BE DETERMINED]`, `[REQUIRES INPUT]`) appear only in single-digit counts in the new uncommitted `bids/chs-cafeteria-…` + `bids/pais-cabin-…` and `firm/proposal-library/federal-volumes/` files just landed.
- Bare `TBD` is more numerous than bracketed `[TBD]`. Many of the bare hits are legitimate values (e.g. *"sign-up TBD per agency"*, *"Sol expected mid-May 2026, exact date TBD"*) that aren't placeholders in the strict sense, but they still represent unresolved information.

## Summary by area

| Area | Markers | Files | Top 3 files |
|---|---:|---:|---|
| Bids — pursuable | 1393 | 167 | `bids/usfws-san-marcos-140FC126R0017/proposal/09-site-visit-attendance-memo.md` (109)<br>`bids/angelo-state-carr-efa-26-007/proposal/04-past-performance.md` (63)<br>`bids/tamu-harrington-2025-06813/proposal/04-past-performance.md` (55) |
| Firm — proposal library | 168 | 28 | `firm/proposal-library/federal-volumes/volume-ii-management-approach.md` (18)<br>`firm/proposal-library/key-personnel/project-executive.md` (14)<br>`firm/proposal-library/key-personnel/project-manager.md` (14) |
| Bids — templates | 105 | 26 | `bids/_TEMPLATES/texas-state-csp-hsp/05-bid-form-prep.md` (10)<br>`bids/_TEMPLATES/federal-sba-rfq-lpta/07-risk-register.md` (9)<br>`bids/_TEMPLATES/texas-state-csp-hsp/contacts.md` (8) |
| Firm — profile / scripts | 73 | 5 | `firm/_scripts/apply_firm_profile.py` (47)<br>`firm/firm-profile.json` (11)<br>`firm/firm-profile.md` (8) |
| Code (placeholder strings in source) | 49 | 9 | `tests/test_apply_firm_profile_idempotency.py` (19)<br>`tests/test_proposal_renderer.py` (17)<br>`core/proposal_renderer/common.py` (4) |
| Firm — compliance | 25 | 2 | `firm/compliance/README.md` (19)<br>`firm/compliance/material-suppliers.md` (6) |
| Bids — meta | 10 | 1 | `bids/_FIRM_PROFILE_INTEGRATION.md` (10) |
| Firm — playbooks | 9 | 3 | `firm/playbooks/texas-state-csp-hsp.md` (5)<br>`firm/playbooks/README.md` (3)<br>`firm/playbooks/federal-sba-rfq-lpta.md` (1) |
| Bids — no-go / watchlist | 5 | 1 | `bids/_WATCHLIST/saan-san-juan-restrooms-140P1226Q0025.md` (5) |
| Firm — scope templates | 2 | 1 | `firm/scope-templates/README.md` (2) |
| Docs | 1 | 1 | `docs/ROADMAP_TAKEOFF_AUTOMATION.md` (1) |

## Root-cause concentration — the 5 source documents that would unblock the most

Most `[USER TO FILL]` markers in `bids/*/proposal/` collapse to a small set of firm-profile gaps. Closing these 5 unblocks the majority of the per-bid noise via `firm/_scripts/apply_firm_profile.py`:

| # | Source doc / user action | Markers it unblocks | Cited by |
|---|---|---:|---|
| 1 | **Current ACORD 25 COI bundle** (GL renewed, WC, Auto, Umbrella, broker name + phone + email) | ~80 across firm + 5 bids | `firm/firm-profile.md` §7; every `outreach/*-email-insurance-broker.md`; every `proposal/07-safety-plan.md` or volume-II technical |
| 2 | **Renewed BPC bond letter + surety agent contact** (or just type the contents of the on-file image PDF) | ~40 across firm + 5 bids | `firm/firm-profile.md` §8; every `bid-bond-form-template.md`, `12-bid-bond-letter-template.md`, `06-bondability-letter-template.md` |
| 3 | **Key-personnel roster** (PM + Super + Safety + QA/QC + Project Executive — names, bios, OSHA 30, refs) | ~360 across firm proposal library + 5 bids `proposal/03-project-team.md` | `firm/proposal-library/key-personnel/*.md`; every `proposal/03-project-team.md`; `firm/compliance/README.md` §8 |
| 4 | **3-yr safety performance pack** (EMR ×4 yrs, OSHA 300/300A ×4 yrs, OSHA recordable rate, LWD rate, citation history, fatality count) | ~50 across firm + per-bid safety plans | `firm/compliance/README.md` §9; every `proposal/07-safety-plan.md`; every `proposal/06-quality-control-plan.md` |
| 5 | **Past-perf owner POC table** (3 owner-side contacts × name + title + current phone + email; Holiday Inn contract value + completion date; Lavon final contract value once substantial completion certified) | ~250 across firm proposal library + 5 bids `proposal/04-past-performance.md` | `firm/proposal-library/past-performance/*.md`; every `proposal/04-past-performance.md`; `firm/firm-profile.md` §11 |

## Action queue — top 20 highest-leverage unblocks

1. **TX HUB recertification (Texas Comptroller)**
    - File / section: `firm/compliance/README.md` §3 Texas state-government registrations / §12 Action priority queue
    - Marker: Expired 2024-08-31 per `firm/firm-profile.json → licenses_and_certifications[0]`
    - Unblock: BPC files HUB recertification via TX Comptroller HUB portal (VID 1874292998900); cascades into TAMU / ASU / TXDOT HSP scoring
    - Effort: MED (2–3 wks turnaround)
2. **MBE / SBE recertification (DFW MSDC)**
    - File / section: `firm/compliance/README.md` §2 SBA / small-business certifications
    - Marker: Cert DL09279 expired 2024-08-31
    - Unblock: BPC files DFW MSDC recertification; cascades into HUB recognition + MWBE participation claims
    - Effort: MED (3–4 wks)
3. **Current insurance COI bundle (GL + WC + Auto + Umbrella)**
    - File / section: `firm/firm-profile.md` §7 Insurance; per-bid `outreach/*-email-insurance-broker.md`
    - Marker: GL policy SBCC-042443-00 expired 2024-09-25; WC/Auto/Umbrella not on file
    - Unblock: User pulls current ACORD 25 COI from insurance agent (with AI + waiver-of-subrogation + primary/non-contributory endorsements; $5M umbrella for TAMU/TTUS)
    - Effort: LOW (1 phone call + 1 wk turnaround)
4. **Bond letter + surety agent capture**
    - File / section: `firm/firm-profile.md` §8 Bonding; `firm/compliance/README.md` §6 Bonding
    - Marker: Surety name + agent + capacity + bond rate `[NOT FOUND IN BPC]`
    - Unblock: User reads the image-only PDF `BPC/Bond Letter_RK Residential Homes ….pdf` on OneDrive and types surety + agent + single-project + aggregate capacity + bond rate into `firm/firm-profile.json → bonding`
    - Effort: LOW (15 min)
5. **Project Manager identity + bio + credentials**
    - File / section: `firm/proposal-library/key-personnel/project-manager.md` + every bid's `proposal/03-project-team.md`
    - Marker: 14× `[USER TO FILL]` per role file; PM cited by firm-profile as CRITICAL (fictitious PM = non-responsibility finding)
    - Unblock: User names BPC's PM, captures bio + OSHA 30 + PMP + 3 owner-side refs into `firm/firm-profile.json → key_personnel[]` and then `apply_firm_profile.py` propagates
    - Effort: MED (depends on whether PM is on-staff or being recruited)
6. **Superintendent + Site Safety Lead + QA/QC Lead identities**
    - File / section: `firm/proposal-library/key-personnel/{superintendent,safety-officer,qa-qc-lead}.md`
    - Marker: 13× `[USER TO FILL]` per role file; same skeleton across three roles
    - Unblock: User names each role (can be combined for sub-$500K bids); capture OSHA 30 + 1st-aid/CPR; same propagation path as PM
    - Effort: MED
7. **Project Executive role decision (combine w/ PIC?)**
    - File / section: `firm/proposal-library/key-personnel/project-executive.md`
    - Marker: 14× `[USER TO FILL]`; firm-profile suggests combining with Rocky (PIC)
    - Unblock: User decides whether to staff a separate Project Executive or combine with PIC; if combine, mark file `Not applicable` and link to PIC
    - Effort: LOW (1 decision)
8. **EMR / TRIR / OSHA 300/300A — 3-yr safety history**
    - File / section: `firm/compliance/README.md` §9 Safety performance; per-bid `proposal/07-safety-plan.md`
    - Marker: 10× `[USER TO FILL]` in compliance §9; EMR/TRIR also pulled in TAMU + ASU + USFWS safety plans
    - Unblock: User pulls WC carrier annual modification-rate notice + OSHA 300A posted summaries (Feb 1–Apr 30 each year) and types into firm-profile
    - Effort: LOW (call to WC carrier + scan)
9. **Past-perf owner reference contacts (3 projects × name + phone + email)**
    - File / section: `firm/proposal-library/past-performance/{hindu-temple-southlake,holiday-inn-hall-park,lavon-rv-park}.md` + per-bid `proposal/04-past-performance.md`
    - Marker: 9× `[USER TO FILL]` across the 3 past-project files (mostly owner POC); past-perf templates in 5 of 6 bids reference these
    - Unblock: User captures owner POC name + title + current phone + email for Lavon Leisure 78 RV Park LLC, North Texas Hindu Heritage Society, and Holiday Inn Hall Park franchisee
    - Effort: LOW (3 phone calls)
10. **Holiday Inn (Hall Park) contract value + completion date**
    - File / section: `firm/proposal-library/past-performance/holiday-inn-hall-park.md` + per-bid past-perf
    - Marker: Contract value + scope detail + completion date `[NOT FOUND IN BPC]`
    - Unblock: User reconstructs from BPC project records (folder not present on OneDrive root — may be archived offline)
    - Effort: MED (file-pull)
11. **SAM.gov registration expiration date**
    - File / section: `firm/firm-profile.json → sam_status_notes`; firm-profile.md §2
    - Marker: Expiration date `TBD`; reps & certs / EFT / TIN refresh currency NOT confirmed
    - Unblock: User logs into SAM.gov, reads Entity Management → Core Data → Registration Expiration Date; refreshes Reps & Certs (FAR 52.204-8) if > 12 months stale
    - Effort: LOW (15 min)
12. **USFWS site-visit memo (109 markers, single file)**
    - File / section: `bids/usfws-san-marcos-140FC126R0017/proposal/09-site-visit-attendance-memo.md`
    - Marker: 109× `[USER TO FILL]` — fully-templated capture form for the 2026-05-27/28 attendance
    - Unblock: User attends 8 AM – 4 PM site visit, fills the memo on-site (save to `local/` per gitignore), photographs everything before leaving
    - Effort: HIGH (1-day site visit, but a fixed deliverable)
13. **TAMU + ASU past-performance templates (50–63 markers per file)**
    - File / section: `bids/{angelo-state-carr-efa-26-007,tamu-harrington-2025-06813,usfws-san-marcos-140FC126R0017}/proposal/04-…-past-performance.md`
    - Marker: 50+× `[USER TO FILL]` per reference (owner / contact / value / dates / on-time? / variance / self-perf scope / HUB %)
    - Unblock: Mostly auto-fills once `firm-profile.json → past_projects[]` is updated with contract value, completion date, on-time?, and HUB participation actuals for Lavon + Hindu Temple + Holiday Inn. Then `apply_firm_profile.py` propagates via L3 rules.
    - Effort: MED (1 evening + apply_firm_profile re-run)
14. **B1710 / TAMU Wehner takeoff numbers (AWAITING TAKEOFF placeholders)**
    - File / section: `bids/tamu-wehner-fin-340E-2025-06871/price-sheet-skeleton.json` + `proposal/10-price-proposal.md` + `proposal/08-csp-proposal-form-fill-guide.md`; `bids/b1710-office-refurb-FA667526Q0002/proposal/01-price-proposal.md`
    - Marker: 41× `[AWAITING …]` (TAKEOFF / SUB QUOTE / FINAL / SUBMISSION DATE)
    - Unblock: Run takeoff against drawings (MARRS glazing wall for Wehner; B1710 SF-1449 line items); close sub quotes (electrical / plumbing / HVAC / glazing); fill final $.
    - Effort: HIGH (the actual estimating work)
15. **TAMU CSP Pricing Proposal Form (e-Builder gated)**
    - File / section: `bids/tamu-harrington-2025-06813/price-sheet-skeleton.json` + `04-scope-of-work.md`
    - Marker: 29× `[TBD]` flagged `[PENDING e-BUILDER ACCESS]`
    - Unblock: User requests e-Builder G2 access via Joelle Shidemantle (TAMU); pulls the actual TAMU Pricing Proposal Form into repo and re-shapes the skeleton.
    - Effort: MED (TAMU access turnaround)
16. **Hays / Brazos / Tom Green county prevailing-wage tables**
    - File / section: `firm/compliance/README.md` §10; per-bid `prevailing-wages.md`
    - Marker: 14× `[USER TO FILL]` in USFWS prevailing-wages; per-county TWC / federal WD pulls outstanding
    - Unblock: User pulls Davis-Bacon WD for USFWS San Marcos from beta.SAM.gov (Hays County, TX heavy/highway/building); TWC rate tables for TAMU (Brazos) + ASU (Tom Green)
    - Effort: LOW (each WD pull is ~15 min)
17. **Insurance broker / agent contact**
    - File / section: `firm/firm-profile.md` §7 Insurance broker; per-bid `outreach/*-email-insurance-broker.md`
    - Marker: Broker name + phone + email `[NOT FOUND IN BPC]`
    - Unblock: User captures broker (likely Appalachian Underwriters or downstream retail agent) into `firm/firm-profile.json → insurance.broker`
    - Effort: LOW
18. **AR / billing email**
    - File / section: `bids/_FIRM_PROFILE_INTEGRATION.md` §recurring TODOs; `firm-profile.md` §15
    - Marker: `[USER TO FILL]@blueprintconstructs.com`
    - Unblock: User chooses ar@ / billing@ / accounts@ alias and configures on Google Workspace; back into firm-profile JSON
    - Effort: LOW
19. **TX CMBL + TX state-vendor account confirmations**
    - File / section: `firm/compliance/README.md` §3
    - Marker: 5× 🔴 `Unknown` enrollments (CMBL, COMET, TAMU SSC, TTUS, UT System)
    - Unblock: User registers / confirms enrollment per agency portal before each TX state bid (TAMU = SSC Vendor Portal; ASU = TTUS FP&C)
    - Effort: MED (per-agency)
20. **Material-supplier accounts (Home Depot Pro / Lowe's Pro / Ferguson / White Cap / Sherwin-Williams)**
    - File / section: `firm/compliance/material-suppliers.md`
    - Marker: 6× `[NOT YET ESTABLISHED]` supplier statuses; full registry skeleton
    - Unblock: User opens each pro account (15–20 min each per supplier credit application). Not bid-blocking today but blocks the long-horizon internal cost DB (Tier 3 in `docs/ROADMAP_TAKEOFF_AUTOMATION.md`).
    - Effort: MED (cumulative)

## Full marker inventory (grouped)

Each line: file path — total markers (by-type breakdown). For markdown files, the section-heading drill-down is collapsed into the by-type tally so the doc stays skimmable. Pull individual line numbers from the live grep when triaging a specific file.

### Bids — pursuable

_1393 markers across 167 files; grouped by workspace below._

#### `bids/angelo-state-carr-efa-26-007/` — ASU Carr EFA-26-007 — Dorm renovation (Texas state CSP w/ HSP)

_Workspace total: **326** markers across 32 files._  
_Already through firm-profile substitution (L1+L2+L3); remaining `[USER TO FILL]` are bid-content: project team identities, EMR / TRIR, owner-side past-perf reference phone/email, ASU clarification answers, bid-bond + insurance broker numbers._

- `proposal/04-past-performance.md` — **63** (63× `[USER TO FILL]`)
- `proposal/03-project-team.md` — **50** (50× `[USER TO FILL]`)
- `proposal/10-price-proposal.md` — **34** (34× `[USER TO FILL]`)
- `proposal/09-attachment-D-hsp-form-guide.md` — **27** (27× `[USER TO FILL]`)
- `proposal/08-attachment-A-fill-guide.md` — **17** (17× `[USER TO FILL]`)
- `proposal/12-bid-bond-letter-template.md` — **13** (13× `[USER TO FILL]`)
- `proposal/07-safety-plan.md` — **12** (12× `[USER TO FILL]`)
- `contacts.md` — **11** (11× `[USER TO FILL]`)
- `outreach/04-email-insurance-broker.md` — **11** (11× `[USER TO FILL]`)
- `proposal/01-executive-summary.md` — **9** (9× `[USER TO FILL]`)
- `02-bid-prep-checklist.md` — **8** (7× `[USER TO FILL]`, 1× `TBD` (bare))
- `proposal/06-quality-control-plan.md` — **6** (6× `[USER TO FILL]`)
- `01-overview.md` — **5** (5× `TBD` (bare))
- `outreach/03-email-bonding-agent.md` — **5** (5× `[USER TO FILL]`)
- `outreach/05-email-hub-subs-template.md` — **5** (5× `[USER TO FILL]`)
- `outreach/07-call-script-samuel-guevara.md` — **5** (5× `[USER TO FILL]`)
- `proposal/00-readme.md` — **5** (5× `[USER TO FILL]`)
- `06-evaluation-strategy.md` — **4** (4× `[USER TO FILL]`)
- `proposal/11-submission-checklist.md` — **4** (4× `[USER TO FILL]`)
- `04-scope-of-work.md` — **3** (3× `[TBD]`)
- `05-hsp-plan.md` — **3** (2× `[USER TO FILL]`, 1× `TBD` (bare))
- `07-risk-register.md` — **3** (3× `[USER TO FILL]`)
- `README.md` — **3** (2× `[USER TO FILL]`, 1× `TBD` (bare))
- `outreach/01-email-hannah-bignall-eligibility.md` — **3** (3× `[USER TO FILL]`)
- `outreach/01-email-samuel-guevara-eligibility.md` — **3** (3× `[USER TO FILL]`)
- `outreach/02-email-samuel-guevara-owner-furnished.md` — **3** (3× `[USER TO FILL]`)
- `outreach/06-email-asu-procurement-clarifications.md` — **3** (3× `[USER TO FILL]`)
- `outreach/07-call-script-hannah-bignall.md` — **3** (3× `[USER TO FILL]`)
- `price-references.md` — **2** (2× `[USER TO FILL]`)
- `08-contract-terms-flags.md` — **1** (1× `TBD` (bare))
- `prevailing-wages.md` — **1** (1× `[USER TO FILL]`)
- `proposal/02-technical-approach.md` — **1** (1× `[USER TO FILL]`)

#### `bids/b1710-office-refurb-FA667526Q0002/` — AF Reserve B1710 — Office refurbishment (federal SBA RFQ, 48-hr sprint due Fri 2026-05-29 5 PM CDT)

_Workspace total: **44** markers across 12 files._  
_Scaffolded 2026-05-27 (48-hr sprint to 2026-05-29). Most markers unblocked by RFQ attachments (SF-1449, wage determination, drawings) once pulled from inbox/SAM.gov, + firm-profile refresh for COI / bond letter / EMR._

- `08-contacts.md` — **14** (10× `[USER TO FILL]`, 3× `[TBD]`, 1× `TBD` (bare))
- `proposal/03-past-performance.md` — **9** (9× `[USER TO FILL]`)
- `03-missing-documents.md` — **4** (4× `[USER TO FILL]`)
- `proposal/04-SF-1449-fill-guide.md` — **3** (3× `[USER TO FILL]`)
- `01-bid-prep-checklist.md` — **2** (1× `TBD` (bare), 1× `[USER TO FILL]`)
- `11-takeoff-template.json` — **2** (2× `TBD` (bare))
- `proposal/01-price-proposal.md` — **2** (2× `[USER TO FILL]`)
- `proposal/02-technical-acceptability.md` — **2** (2× `[USER TO FILL]`)
- `proposal/06-bondability-letter-template.md` — **2** (2× `[USER TO FILL]`)
- `proposal/10-submission-checklist.md` — **2** (2× `[USER TO FILL]`)
- `05-set-aside-eligibility.md` — **1** (1× `TBD` (bare))
- `06-timeline.md` — **1** (1× `[USER TO FILL]`)

#### `bids/chs-cafeteria-2026-0608-01/` — CHS Cafeteria — 2026-0608-01 (Texas state CSP w/ HSP; new workspace just landed)

_Workspace total: **57** markers across 14 files._  
_Just-landed workspace (uncommitted at audit time). Markers are largely template-copy `[USER TO FILL]` slots awaiting per-bid customization and the same firm-profile gaps (key personnel, EMR, past-perf POC) as the other active TX state CSP workspaces._

- `05-bid-form-prep.md` — **10** (10× `[USER TO FILL]`)
- `contacts.md` — **8** (8× `[USER TO FILL]`)
- `csp-scoring-matrix.md` — **8** (8× `[USER TO FILL]`)
- `outreach/email-template.md` — **7** (7× `[USER TO FILL]`)
- `01-overview.md` — **6** (6× `[USER TO FILL]`)
- `07-risk-register.md` — **5** (5× `[USER TO FILL]`)
- `09-proposal-draft.md` — **4** (4× `[USER TO FILL]`)
- `08-pricing-strategy.md` — **3** (3× `[USER TO FILL]`)
- `02-bid-prep-checklist.md` — **1** (1× `[USER TO FILL]`)
- `05-hsp-plan.md` — **1** (1× `[USER TO FILL]`)
- `06-evaluation-strategy.md` — **1** (1× `[USER TO FILL]`)
- `06-scope-outline.md` — **1** (1× `[USER TO FILL]`)
- `price-sheet-skeleton.json` — **1** (1× `[USER TO FILL]`)
- `takeoff-template.json` — **1** (1× `[USER TO FILL]`)

#### `bids/cmd-post-ndi-W50S7626QA001/` — TXANG Cmd Post + NDI — W50S7626QA001 (federal RFQ)

_Workspace total: **76** markers across 14 files._  
_Federal RFQ; most remaining markers are sub-quote stubs (secure doors / hardware, mechanical-HVAC), bond letter copy, and past-perf owner contacts._

- `04-scope-of-work.md` — **18** (18× `TBD` (bare))
- `proposal/03-past-performance.md` — **15** (15× `[USER TO FILL]`)
- `contacts.md` — **12** (12× `[USER TO FILL]`)
- `02-bid-prep-checklist.md` — **9** (9× `[USER TO FILL]`)
- `proposal/01-price-proposal.md` — **6** (6× `[USER TO FILL]`)
- `proposal/09-site-visit-attendance-memo.md` — **4** (4× `[USER TO FILL]`)
- `outreach/03-email-bonding-agent.md` — **3** (2× `[USER TO FILL]`, 1× `TBD` (bare))
- `proposal/04-SF-1442-fill-guide.md` — **3** (3× `[USER TO FILL]`)
- `00-window-check.md` — **1** (1× `TBD` (bare))
- `03-missing-documents.md` — **1** (1× `TBD` (bare))
- `README.md` — **1** (1× `[USER TO FILL]`)
- `outreach/04-email-sub-quote-secure-doors-hardware.md` — **1** (1× `[USER TO FILL]`)
- `outreach/06-email-sub-quote-mechanical-hvac.md` — **1** (1× `TBD` (bare))
- `proposal/07-bid-bond-form-template.md` — **1** (1× `[USER TO FILL]`)

#### `bids/pais-cabin-140P6026Q0029/` — PAIS Cabin — 140P6026Q0029 (federal SBA RFQ; new workspace just landed)

_Workspace total: **51** markers across 12 files._  
_Just-landed federal SBA workspace (uncommitted at audit time). Same firm-profile gaps as `usfws-san-marcos-…` and `b1710-office-refurb-…` plus the standard federal-LPTA template slots._

- `00-overview.md` — **10** (8× `[AWAITING SOURCE DOCS]`, 1× `TBD` (bare), 1× `[USER TO FILL]`)
- `07-risk-register.md` — **9** (9× `[USER TO FILL]`)
- `contacts.md` — **7** (7× `[USER TO FILL]`)
- `05-bid-form-prep.md` — **6** (6× `[USER TO FILL]`)
- `outreach/email-template.md` — **6** (6× `[USER TO FILL]`)
- `08-pricing-strategy.md` — **5** (5× `[USER TO FILL]`)
- `01-scope.md` — **2** (1× `[USER TO FILL]`, 1× `[AWAITING SOURCE DOCS]`)
- `09-proposal-draft.md` — **2** (2× `[USER TO FILL]`)
- `03-missing-documents.md` — **1** (1× `[USER TO FILL]`)
- `04-checklist.md` — **1** (1× `[USER TO FILL]`)
- `06-scope-outline.md` — **1** (1× `[USER TO FILL]`)
- `takeoff-template.json` — **1** (1× `[USER TO FILL]`)

#### `bids/tamu-harrington-2025-06813/` — TAMU Harrington EC Lab 303 — 2025-06813 (Texas state CSP w/ HSP)

_Workspace total: **404** markers across 34 files._  
_State CSP w/ HSP. Pricing skeletons gated on e-Builder access + closed sub quotes; team identities + EMR + owner reference contacts are firm-profile gaps._

- `proposal/04-past-performance.md` — **55** (55× `[USER TO FILL]`)
- `price-sheet-skeleton.json` — **51** (34× `[TBD]`, 17× `TBD` (bare))
- `proposal/03-project-team.md` — **44** (44× `[USER TO FILL]`)
- `proposal/08-csp-proposal-form-fill-guide.md` — **30** (30× `[USER TO FILL]`)
- `04-scope-of-work.md` — **29** (28× `[TBD]`, 1× `TBD` (bare))
- `proposal/09-hsp-form-fill-guide.md` — **28** (28× `[USER TO FILL]`)
- `takeoff-template.json` — **27** (26× `[TBD]`, 1× `TBD` (bare))
- `proposal/10-price-proposal.md` — **22** (22× `[USER TO FILL]`)
- `timeline.md` — **21** (20× `[USER TO FILL]`, 1× `TBD` (bare))
- `proposal/01-executive-summary.md` — **20** (19× `[USER TO FILL]`, 1× `TBD` (bare))
- `02-bid-prep-checklist.md` — **8** (8× `[USER TO FILL]`)
- `outreach/01-email-joelle-shidemantle-eligibility.md` — **7** (7× `[USER TO FILL]`)
- `outreach/03-email-fred-patterson-drawings.md` — **7** (7× `[USER TO FILL]`)
- `outreach/04-email-patty-winkler-hub.md` — **6** (6× `[USER TO FILL]`)
- `outreach/05-email-bonding-agent.md` — **6** (6× `[USER TO FILL]`)
- `07-risk-register.md` — **5** (5× `[USER TO FILL]`)
- `outreach/02-email-joelle-shidemantle-csp-access.md` — **4** (4× `[USER TO FILL]`)
- `outreach/06-email-insurance-broker.md` — **4** (4× `[USER TO FILL]`)
- `proposal/00-readme.md` — **4** (3× `[USER TO FILL]`, 1× `[TBD]`)
- `proposal/06-quality-control-plan.md` — **4** (3× `[USER TO FILL]`, 1× `[TBD]`)
- `README.md` — **3** (1× `TBD` (bare), 1× `[TBD]`, 1× `[USER TO FILL]`)
- `01-overview.md` — **2** (2× `TBD` (bare))
- `05-hsp-plan.md` — **2** (2× `[USER TO FILL]`)
- `contacts.md` — **2** (2× `[USER TO FILL]`)
- `outreach/07-call-script-joelle-shidemantle.md` — **2** (2× `[USER TO FILL]`)
- `proposal/02-technical-approach.md` — **2** (1× `TBD` (bare), 1× `[USER TO FILL]`)
- `proposal/11-submission-checklist.md` — **2** (2× `[USER TO FILL]`)
- `03-missing-documents.md` — **1** (1× `TBD` (bare))
- `06-evaluation-strategy.md` — **1** (1× `[USER TO FILL]`)
- `price-references.md` — **1** (1× `[USER TO FILL]`)
- `outreach/08-q-and-a-submission.md` — **1** (1× `TBD` (bare))
- `proposal/05-schedule-narrative.md` — **1** (1× `[USER TO FILL]`)
- `proposal/07-safety-plan.md` — **1** (1× `[USER TO FILL]`)
- `proposal/12-bid-bond-letter-template.md` — **1** (1× `[USER TO FILL]`)

#### `bids/tamu-wehner-fin-340E-2025-06871/` — TAMU Wehner Finance Rm 340E — 2025-06871 (Texas state CSP, due Wed 2026-06-17 2 PM CDT)

_Workspace total: **147** markers across 23 files._  
_Scaffolded 2026-05-27 (due 2026-06-17). Pricing fields await MARRS glazing + MEP + finishes sub quotes; team identities + EMR + bonding letter follow firm-profile gaps._

- `proposal/09-hsp-form-fill-guide.md` — **19** (11× `[USER TO FILL]`, 7× `TBD` (bare), 1× `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.))
- `contacts.md` — **17** (9× `[USER TO FILL]`, 8× `TBD` (bare))
- `proposal/03-project-team.md` — **16** (10× `[USER TO FILL]`, 6× `TBD` (bare))
- `proposal/08-csp-proposal-form-fill-guide.md` — **15** (12× `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.), 3× `[USER TO FILL]`)
- `price-sheet-skeleton.json` — **14** (14× `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.))
- `proposal/10-price-proposal.md` — **13** (13× `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.))
- `proposal/04-past-performance.md` — **10** (8× `[USER TO FILL]`, 2× `TBD` (bare))
- `price-references.md` — **7** (7× `TBD` (bare))
- `proposal/07-safety-plan.md` — **6** (6× `[USER TO FILL]`)
- `01-overview.md` — **5** (5× `TBD` (bare))
- `outreach/06-email-insurance-broker.md` — **4** (3× `[USER TO FILL]`, 1× `TBD` (bare))
- `06-evaluation-strategy.md` — **3** (2× `[USER TO FILL]`, 1× `TBD` (bare))
- `outreach/05-email-bonding-agent.md` — **3** (3× `[USER TO FILL]`)
- `proposal/00-readme.md` — **3** (3× `[USER TO FILL]`)
- `05-hsp-plan.md` — **2** (2× `TBD` (bare))
- `proposal/11-submission-checklist.md` — **2** (2× `[USER TO FILL]`)
- `proposal/12-bid-bond-letter-template.md` — **2** (2× `TBD` (bare))
- `02-bid-prep-checklist.md` — **1** (1× `[USER TO FILL]`)
- `03-missing-documents.md` — **1** (1× `[USER TO FILL]`)
- `07-risk-register.md` — **1** (1× `[USER TO FILL]`)
- `README.md` — **1** (1× `TBD` (bare))
- `outreach/08-q-and-a-submission.md` — **1** (1× `TBD` (bare))
- `proposal/01-executive-summary.md` — **1** (1× `[AWAITING …]` (TAKEOFF / FINAL / SUB QUOTE / etc.))

#### `bids/usfws-san-marcos-140FC126R0017/` — USFWS San Marcos ARC — 140FC126R0017 (federal SBA RFQ, site visit 2026-05-27/28)

_Workspace total: **288** markers across 26 files._  
_Federal SBA RFQ. The 109 markers in `09-site-visit-attendance-memo.md` are an on-purpose template to capture findings during the 2026-05-27/28 site visit; they all unblock the day the user attends + fills the memo. Past-perf + technical volumes await firm-profile refresh + Hays County prevailing-wage table._

- `proposal/09-site-visit-attendance-memo.md` — **109** (109× `[USER TO FILL]`)
- `proposal/03-volume-III-past-performance.md` — **34** (34× `[USER TO FILL]`)
- `prevailing-wages.md` — **14** (14× `[USER TO FILL]`)
- `proposal/04-SF-1442-fill-guide.md` — **13** (13× `[USER TO FILL]`)
- `contacts.md` — **10** (8× `[USER TO FILL]`, 2× `TBD` (bare))
- `outreach/03-email-katherine-bockrath-site-visit-rsvp.md` — **10** (10× `[USER TO FILL]`)
- `outreach/05-email-sub-quote-overhead-doors.md` — **10** (9× `[USER TO FILL]`, 1× `TBD` (bare))
- `outreach/06-email-sub-quote-gas-line.md` — **10** (8× `[USER TO FILL]`, 2× `TBD` (bare))
- `proposal/02-volume-II-technical-acceptability.md` — **10** (10× `[USER TO FILL]`)
- `04-scope-of-work.md` — **9** (9× `[TBD]`)
- `proposal/11-rfi-cover-letter.md` — **9** (9× `[USER TO FILL]`)
- `outreach/07-email-sub-quote-gutters.md` — **8** (8× `[USER TO FILL]`)
- `outreach/04-email-bonding-agent.md` — **7** (7× `[USER TO FILL]`)
- `proposal/05-reps-and-certs-pull-guide.md` — **6** (6× `[USER TO FILL]`)
- `07-risk-register.md` — **4** (4× `[USER TO FILL]`)
- `outreach/01-email-tracy-gamble-rfi-consolidated.md` — **4** (4× `[USER TO FILL]`)
- `proposal/08-dba-compliance-acknowledgment.md` — **4** (4× `[USER TO FILL]`)
- `02-bid-prep-checklist.md` — **3** (3× `[USER TO FILL]`)
- `outreach/08-internal-sam-gov-verification-checklist.md` — **3** (3× `[USER TO FILL]`)
- `03-missing-documents.md` — **2** (1× `TBD` (bare), 1× `[USER TO FILL]`)
- `proposal/00-readme.md` — **2** (2× `[USER TO FILL]`)
- `proposal/01-volume-I-price-proposal.md` — **2** (2× `[USER TO FILL]`)
- `proposal/10-submission-checklist.md` — **2** (2× `[USER TO FILL]`)
- `01-overview.md` — **1** (1× `TBD` (bare))
- `price-sheet-skeleton.json` — **1** (1× `[USER TO FILL]`)
- `README.md` — **1** (1× `[USER TO FILL]`)

### Bids — templates

_105 markers across 26 files._

> These are **template-intrinsic** placeholders (designed slots in `bids/_TEMPLATES/`). They are **not bugs**. Listed here for completeness and to confirm the templates are still skeleton-shaped. See *Template-intrinsic placeholders* section at the bottom for the convention.

- `bids/_TEMPLATES/texas-state-csp-hsp/05-bid-form-prep.md` — **10** (10× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/07-risk-register.md` — **9** (9× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/contacts.md` — **8** (8× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/csp-scoring-matrix.md` — **8** (8× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/contacts.md` — **7** (7× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/outreach/email-template.md` — **7** (7× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/05-bid-form-prep.md` — **6** (6× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/outreach/email-template.md` — **6** (6× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/01-overview.md` — **6** (6× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/00-overview.md` — **5** (5× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/08-pricing-strategy.md` — **5** (5× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/07-risk-register.md` — **5** (5× `[USER TO FILL]`)
- `bids/_TEMPLATES/README.md` — **4** (2× `[USER TO FILL]`, 1× `[TEMPLATE]`, 1× `TBD` (bare))
- `bids/_TEMPLATES/texas-state-csp-hsp/09-proposal-draft.md` — **4** (4× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/08-pricing-strategy.md` — **3** (3× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/09-proposal-draft.md` — **2** (2× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/03-missing-documents.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/04-checklist.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/06-scope-outline.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/federal-sba-rfq-lpta/takeoff-template.json` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/02-bid-prep-checklist.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/06-evaluation-strategy.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/06-scope-outline.md` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/price-sheet-skeleton.json` — **1** (1× `[USER TO FILL]`)
- `bids/_TEMPLATES/texas-state-csp-hsp/takeoff-template.json` — **1** (1× `[USER TO FILL]`)

### Bids — meta

_10 markers across 1 files._

- `bids/_FIRM_PROFILE_INTEGRATION.md` — **10** (6× `[USER TO FILL]`, 3× `TBD` (bare), 1× `[AWAITING SOURCE DOCS]`)

### Bids — no-go / watchlist

_5 markers across 1 files._

- `bids/_WATCHLIST/saan-san-juan-restrooms-140P1226Q0025.md` — **5** (5× `TBD` (bare))

### Firm — proposal library

_168 markers across 28 files._

- `firm/proposal-library/federal-volumes/volume-ii-management-approach.md` — **18** (17× `[USER TO FILL]`, 1× `TBD` (bare))
- `firm/proposal-library/key-personnel/project-executive.md` — **14** (14× `[USER TO FILL]`)
- `firm/proposal-library/key-personnel/project-manager.md` — **14** (14× `[USER TO FILL]`)
- `firm/proposal-library/key-personnel/safety-officer.md` — **13** (13× `[USER TO FILL]`)
- `firm/proposal-library/key-personnel/superintendent.md` — **13** (13× `[USER TO FILL]`)
- `firm/proposal-library/boilerplate/schedule-narrative-skeleton.md` — **11** (11× `[USER TO FILL]`)
- `firm/proposal-library/key-personnel/qa-qc-lead.md` — **11** (11× `[USER TO FILL]`)
- `firm/proposal-library/past-performance/holiday-inn-hall-park.md` — **7** (7× `[USER TO FILL]`)
- `firm/proposal-library/boilerplate/safety-plan-one-pager.md` — **6** (6× `[USER TO FILL]`)
- `firm/proposal-library/hsp/hsp-progress-assessment-report-template.md` — **6** (6× `[USER TO FILL]`)
- `firm/proposal-library/README.md` — **5** (4× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/proposal-library/boilerplate/communication-plan.md` — **5** (5× `[USER TO FILL]`)
- `firm/proposal-library/federal-volumes/README.md` — **5** (4× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/proposal-library/boilerplate/qa-qc-plan-one-pager.md` — **4** (4× `[USER TO FILL]`)
- `firm/proposal-library/past-performance/hindu-temple-southlake.md` — **4** (4× `[USER TO FILL]`)
- `firm/proposal-library/ppq/ppq-cover-letter-to-client.md` — **4** (4× `[USER TO FILL]`)
- `firm/proposal-library/exec-summary-archetypes/federal-sba-lpta.md` — **3** (3× `[USER TO FILL]`)
- `firm/proposal-library/federal-volumes/volume-i-technical-approach.md` — **3** (3× `[USER TO FILL]`)
- `firm/proposal-library/federal-volumes/volume-iii-past-performance.md` — **3** (3× `[USER TO FILL]`)
- `firm/proposal-library/key-personnel/principal-in-charge.md` — **3** (3× `[USER TO FILL]`)
- `firm/proposal-library/past-performance/lavon-rv-park.md` — **3** (3× `[USER TO FILL]`)
- `firm/proposal-library/ppq/README.md` — **3** (2× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/proposal-library/exec-summary-archetypes/texas-state-csp.md` — **2** (2× `[USER TO FILL]`)
- `firm/proposal-library/hsp/hsp-good-faith-effort.md` — **2** (2× `[USER TO FILL]`)
- `firm/proposal-library/hsp/hsp-supplemental-form.md` — **2** (2× `[USER TO FILL]`)
- `firm/proposal-library/hsp/README.md` — **2** (1× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/proposal-library/boilerplate/closeout-plan.md` — **1** (1× `[USER TO FILL]`)
- `firm/proposal-library/hsp/hsp-cmbl-vendor-outreach-log.md` — **1** (1× `[USER TO FILL]`)

### Firm — profile / scripts

_73 markers across 5 files._

- `firm/_scripts/apply_firm_profile.py` — **47** (46× `[USER TO FILL]`, 1× `TBD` (bare))
- `firm/firm-profile.json` — **11** (8× `[USER TO FILL]`, 3× `TBD` (bare))
- `firm/firm-profile.md` — **8** (7× `[USER TO FILL]`, 1× `TBD` (bare))
- `firm/README.md` — **6** (5× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/_scripts/scan_placeholders.py` — **1** (1× `TBD` (bare))

### Firm — compliance

_25 markers across 2 files._

- `firm/compliance/README.md` — **19** (18× `[USER TO FILL]`, 1× `TBD` (bare))
- `firm/compliance/material-suppliers.md` — **6** (6× `[NOT YET …]`)

### Firm — playbooks

_9 markers across 3 files._

- `firm/playbooks/texas-state-csp-hsp.md` — **5** (5× `TBD` (bare))
- `firm/playbooks/README.md` — **3** (2× `[USER TO FILL]`, 1× `[TEMPLATE]`)
- `firm/playbooks/federal-sba-rfq-lpta.md` — **1** (1× `TBD` (bare))

### Firm — scope templates

_2 markers across 1 files._

- `firm/scope-templates/README.md` — **2** (1× `[USER TO FILL]`, 1× `[TEMPLATE]`)

### Docs

_1 markers across 1 files._

- `docs/ROADMAP_TAKEOFF_AUTOMATION.md` — **1** (1× `[NOT YET …]`)

### Code (placeholder strings in source)

_49 markers across 9 files._

- `tests/test_apply_firm_profile_idempotency.py` — **19** (19× `[USER TO FILL]`)
- `tests/test_proposal_renderer.py` — **17** (16× `[USER TO FILL]`, 1× `TBD` (bare))
- `core/proposal_renderer/common.py` — **4** (3× `[USER TO FILL]`, 1× `[TBD]`)
- `core/proposal_renderer/pdf.py` — **2** (2× `[USER TO FILL]`)
- `core/proposal_renderer/pptx.py` — **2** (1× `[USER TO FILL]`, 1× `TBD` (bare))
- `scripts/render_proposals.py` — **2** (2× `[USER TO FILL]`)
- `app.py` — **1** (1× `[USER TO FILL]`)
- `core/proposal_renderer/internal_workbook.py` — **1** (1× `[USER TO FILL]`)
- `core/proposal_renderer/css/internal-workbook.css` — **1** (1× `[USER TO FILL]`)

## Template-intrinsic placeholders (not bugs — these are template slots)

The 105 markers in `bids/_TEMPLATES/` (26 files) and the 168 markers in `firm/proposal-library/` (28 files) are **designed skeleton slots**, not gaps in a live bid. They are listed in the inventory above for transparency but should not be on anyone's homework list. The convention is documented in `bids/_TEMPLATES/README.md` § *Placeholder convention*:

- `{{UPPER_SNAKE}}` — project-specific fact, search-and-replace per bid
- `[USER TO FILL: <short description>]` — firm-internal data not in `firm-profile.json`
- `[TEMPLATE]` — structural skeleton not yet refined by a shipped bid

These tokens are intentionally *not* substituted by `apply_firm_profile.py` when it runs against `bids/_TEMPLATES/` — they're meant to survive the substitution pass and become live markers only when the template is copied into a `bids/<slug>/` workspace.

Same applies to `firm/proposal-library/` — the `[USER TO FILL]` markers in `key-personnel/`, `boilerplate/`, `exec-summary-archetypes/`, `past-performance/` are template slots that get instantiated when proposals are written. They surface in the *Action queue* via the same root-cause (e.g. key-personnel skeletons → PM identity capture).

## Code placeholders (`core/`, `scripts/`, `tests/`, `app.py`)

_49 markers across 9 source files._ These are placeholder *constants and test fixtures* used by the proposal renderer (e.g. `core/proposal_renderer/common.py` carries the literal `[USER TO FILL]` token so the renderer can detect and gray-out unfilled cells) and by `firm/_scripts/apply_firm_profile.py` (regex patterns that recognize the placeholder shape). They are functional constants, not gaps — leave in place unless the renderer's redaction policy is being rewritten.

## Notes on markers without a clear unblock path

Most markers in this audit name their own unblock (e.g. `[USER TO FILL — Lavon Leisure 78 RV Park LLC owner POC]` is self-naming). The handful of bare `TBD` / `[TBD]` tokens that don't are:

- `firm/firm-profile.json → sam_status_notes` — *registration expiration date TBD*. Unblock: user logs into SAM.gov (see Action queue #11).
- `bids/_WATCHLIST/saan-san-juan-restrooms-140P1226Q0025.md` — 5× `TBD` are intentional placeholders awaiting solicitation drop (the user can't fill them; SAM.gov posts them). No action.
- `firm/playbooks/texas-state-csp-hsp.md` — 5× `TBD` are doc cross-references to per-bid takeoffs not yet existing. No action; resolves as bids land.
- `bids/cmd-post-ndi-W50S7626QA001/04-scope-of-work.md` — 18× `TBD` are tied to Sheet 2 visual review pending (drawings extracted partially). Unblock: visual review of `DDPM262101_Alter CP and NDI_Plans (20260512).pdf` page 2.
- `bids/tamu-harrington-2025-06813/{takeoff-template.json, price-sheet-skeleton.json, 04-scope-of-work.md}` — 80+× `[TBD]` flagged `[PENDING e-BUILDER ACCESS]`. Unblock: TAMU e-Builder G2 access (Action queue #15).

## Refresh procedure

This audit is a one-shot Markdown snapshot. To regenerate after parallel workers land or after the user closes any of the Action queue items above:

1. `git fetch origin && git pull --rebase --autostash origin main`
2. Re-run the same prompt as a worker task, or build `scripts/audit_source_doc_queue.py` (proposed Day-3 task) that walks the repo with the same skip rules and the same marker regex.
3. The audit's marker counts will drift downward as the Action queue closes (each `firm-profile.json` capture cascades through `apply_firm_profile.py` into the per-bid copies).

---

**Audit signature** — generated by a worker task against HEAD `395daea31a7757da8f35bb18e5c454cde8a61226` at 2026-05-28T02:51:37Z. 1,840 markers / 244 files / 7 distinct marker types observed (working-tree state, includes uncommitted in-flight worker files).
