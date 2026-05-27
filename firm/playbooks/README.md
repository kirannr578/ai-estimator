# `firm/playbooks/` — BPC procurement-type playbooks

This folder is the **first stop** when a new RFP / RFCSP / IFB lands in `inbox/opportunities/`. Each playbook captures everything Blueprint Constructs has learned about a specific procurement archetype — what the agency expects, what BPC needs in hand to bid, what kills bids on this kind of work, and what reusable language goes into the proposal.

A new bid workspace under `bids/<slug>/` is built by:

1. Reading the matching playbook here.
2. Copying the matching workspace skeleton from [`bids/_TEMPLATES/`](../../bids/_TEMPLATES/README.md).
3. Pulling matching scope templates from [`firm/scope-templates/`](../scope-templates/README.md).
4. Reusing paste-ready language from [`firm/proposal-library/`](../proposal-library/README.md).
5. Confirming current BPC compliance posture against [`firm/compliance/`](../compliance/README.md).
6. Running `firm/_scripts/apply_firm_profile.py` to substitute firm-profile values into the new workspace.

## Playbook index

| Playbook | Procurement type | BPC bids that exemplify it |
|---|---|---|
| [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) | Federal Small-Business set-aside Request for Quote (or RFP), Lowest-Price-Technically-Acceptable | [`bids/usfws-san-marcos-140FC126R0017/`](../../bids/usfws-san-marcos-140FC126R0017/) |
| [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md) | Texas state-funded Competitive Sealed Proposal (CSP / RFCSP) under Tex. Gov't Code Ch. 2269, with mandatory HUB Subcontracting Plan | [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/), [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/) |

## Procurement-type matrix

The matrix is the cheat-sheet for matching an incoming opportunity to the right playbook. Read it left to right when you triage a new RFP.

| Procurement archetype | Playbook | Eligible BPC bids exemplifying it | Solicitation portals | Required compliance docs (must be current at bid) | Bid bond | P&P bonds | Typical NAICS / scope |
|---|---|---|---|---|---|---|---|
| **Federal SBA RFQ / RFP — LPTA** | [federal-sba-rfq-lpta](federal-sba-rfq-lpta.md) | USFWS San Marcos 140FC126R0017; future USFWS / USACE / NPS / TXANG (federal) small construction | SAM.gov (primary), PIEE (Wide-Area Workflow for DoD), agency email | SAM registration active, UEI + CAGE current, Reps & Certs ≤12 months old, FAR 52.219-1 small-size assertion on the bid NAICS, FAR 52.204-21 Basic Safeguarding posture, FASCSA rep (52.204-29), Section 889 reps (52.204-24/-25/-26), Buy American reps, DBA / certified-payroll readiness, Davis-Bacon WD freshness | 20% of bid OR $1M (whichever less) per FAR 52.228-1 | 100% Performance + 100% Payment if > $150K per FAR 28.102-1(a) / FAR 52.228-15 | NAICS 236220 small at $45M cap; renovation, rehab, site work, small ground-up |
| **Federal best-value RFP** (FAR Part 15 tradeoff) | *not yet exemplified — TODO playbook* | — | Same as LPTA | Same as LPTA plus past-performance CPARS hygiene + technical-narrative submittal capability | Same | Same | Same |
| **Texas State CSP / RFCSP (Ch. 2269) with HSP** | [texas-state-csp-hsp](texas-state-csp-hsp.md) | TAMU Harrington 2025-06813; Angelo State Carr EFA 26-007; future TAMU / TTUS / UT System / UH System / TSU / TX K-12 | ESBD (Electronic State Business Daily, primary notice), Trimble Unity Construct / e-Builder (TAMU System CSP package portal), direct agency SSC / FP&C portals, agency email | TX HUB cert current (or HSP GFE binder), TX CMBL active, TX SOS franchise-tax good-standing, TX Comptroller WebFile, county prevailing-wage table for project county, OSHA 10/30 rosters for site supervision, CIQ + HB 1295 form-readiness | 5% of bid per Tex. Gov't Code Ch. 2253 | 100% Performance + 100% Payment (TX Statutory Bonds, SF 25 / 25A or TTUS / TAMU equivalents) | NAICS 236220 / 236118; interior reno, lab + classroom modernization, dressing-room reno, finish-out |
| **Texas city / county / ISD CSP** | *partially covered by* `texas-state-csp-hsp` | — | Agency portals (city procurement, ISD bond-program portals, county purchasing) | Local-government CIQ (Tex. Local Gov't Code Ch. 176), HB 1295 ($1M+ threshold), TX Comptroller good-standing, county-specific prevailing wage if Tex. Gov't Code Ch. 2258 triggers | Varies (1–5% bid) | 100% P&P typically | NAICS 236220 / 238 trades depending on scope |
| **Federal job-order contract (JOC) task** | *not yet exemplified — TODO playbook* | — | SAM.gov + agency JOC pool portal | Pre-qual into the JOC pool, UPB pricing capability | None at task | Per task | Renovation, IDIQ work |
| **Private commercial / institutional negotiated** | *not playbook-grade; ad-hoc* | Hindu Temple of Southlake; Holiday Inn (Hall Park); Lavon RV Park | Owner-direct, GC partner | COI, W-9, bond letter (if requested) | Owner-discretion | Owner-discretion | Varies |

## Placeholder convention used throughout this capability library

Every reusable artifact (playbooks, workspace templates, scope templates, proposal-library entries) uses the **same** placeholder convention so that a future agent or estimator can search-and-replace them consistently.

- **`{{UPPER_SNAKE}}`** — project-specific fact that must be filled per opportunity (e.g. `{{SOLICITATION_NUMBER}}`, `{{DUE_DATE}}`, `{{SITE_ADDRESS}}`, `{{AGENCY}}`, `{{COUNTY}}`).
- **`[USER TO FILL: <short description>]`** — firm-internal data point that no agent can supply (a person's name, a private contact at a sub, a current EMR number not in `firm-profile.json`).
- **`[TEMPLATE]`** — section is a structural skeleton because no shipped BPC bid has exemplified that section yet. Treat as a stub; refine after the next bid that exercises it.
- **`{{...}}` tokens are case-sensitive and use UPPER_SNAKE.** Do not mix `{{site_address}}` and `{{SITE_ADDRESS}}` in the same file — pick the upper form.
- **No placeholder for facts that already live in `firm/firm-profile.json`** — those are filled with the literal value (firm legal name, UEI, CAGE, NAICS codes, office phone, etc.). Re-running `firm/_scripts/apply_firm_profile.py` keeps them in sync if the profile is updated.

### Master placeholder vocabulary

The placeholders below are the union of those used across all workspace templates. New playbooks / templates should reuse names from this list before inventing new ones.

| Placeholder | Meaning | Source when filling |
|---|---|---|
| `{{SOLICITATION_NUMBER}}` | Agency's solicitation / RFP / RFCSP / IFB number | RFP cover or ESBD posting |
| `{{PROJECT_NUMBER}}` | Owner-side project number, if separate from solicitation # | RFP / SOW |
| `{{PROJECT_NAME}}` | Short project name as the agency writes it | RFP cover |
| `{{AGENCY}}` | Issuing agency / owner full name | RFP cover |
| `{{AGENCY_SHORT}}` | Common acronym (USFWS, TAMU, ASU, USACE, TXANG, NPS) | Inference |
| `{{ISSUING_OFFICE}}` | Issuing office address (federal) or agency-procurement office (state) | RFP / SF 1442 |
| `{{NAICS_CODE}}` | Primary NAICS for the bid (typically 236220) | RFP §K / 52.204-8 |
| `{{SIZE_STANDARD_USD}}` | SBA size standard for that NAICS | SBA size-standards table; current 236220 = $45.0M |
| `{{CONTRACT_TYPE}}` | Firm-Fixed Price / Cost-Plus / IDIQ / etc. | RFP §B |
| `{{EVALUATION_METHOD}}` | LPTA / Tradeoff / Best Value / Competitive-Sealed-Proposal-with-scoring | RFP §M / CSP §00 21 00 |
| `{{DUE_DATE}}` | Proposal due date | RFP cover / NOP |
| `{{DUE_TIME}}` | Proposal due time (local) | Same |
| `{{DUE_TIMEZONE}}` | EDT / CDT / CT — the timezone the agency writes | Same |
| `{{SITE_VISIT_DATE}}` | Pre-bid site visit date(s) | RFP / NOP |
| `{{RFI_CUTOFF_DATE}}` | RFI cutoff | RFP §L |
| `{{POP_DAYS}}` | Period of performance (calendar days from NTP) | RFP §F / SOW |
| `{{SITE_ADDRESS}}` | Full physical site address with county | RFP / SOW |
| `{{SITE_CITY_STATE_ZIP}}` | City, state, ZIP only | Same |
| `{{COUNTY}}` | County containing the site (drives prevailing-wage lookup) | Same |
| `{{CO_NAME}}` / `{{CO_EMAIL}}` / `{{CO_PHONE}}` | Contracting Officer | RFP §G |
| `{{CS_NAME}}` / `{{CS_EMAIL}}` / `{{CS_PHONE}}` | Contract Specialist | RFP §L |
| `{{SITE_POC_NAME}}` / `{{SITE_POC_EMAIL}}` / `{{SITE_POC_PHONE}}` | Site-visit POC | RFP / SOW |
| `{{AE_FIRM_NAME}}` / `{{AE_POC_EMAIL}}` | A/E firm for the project (state CSPs) | NOP / CSP cover |
| `{{SSC_PM_NAME}}` / `{{SSC_PM_EMAIL}}` | TAMU System SSC project manager | NOP |
| `{{HUB_POC_NAME}}` / `{{HUB_POC_EMAIL}}` | Agency HUB coordinator (state) | NOP / RFCSP |
| `{{WD_NUMBER}}` | Davis-Bacon WD number (federal) | RFP attachment |
| `{{WD_DATE}}` | Davis-Bacon WD effective date | Same |
| `{{TX_WAGE_FILE}}` | Texas county prevailing wage filename | Attachment F.x in state CSPs |
| `{{MAGNITUDE_LOW}}` / `{{MAGNITUDE_HIGH}}` | Government estimate magnitude range (federal) | RFP cover |
| `{{HUB_GOAL_PCT}}` | Project-specific HUB goal (if agency overrides the statewide goal) | RFCSP HUB section |
| `{{LD_RATE}}` | Liquidated damages per calendar day | RFP / CSA |
| `{{NTP_TARGET_DATE}}` | Expected NTP date | RFP / NOP |
| `{{SUBSTANTIAL_COMPLETION_DATE}}` | Substantial-completion target date | RFP / CSP §00 42 13 |
| `{{ACCEPTANCE_PERIOD_DAYS}}` | Days the offer must remain valid | RFP block 13d |
| `{{ADDENDA_LIST}}` | Numbered list of acknowledged addenda / SF 30s | SAM / portal |

When a new placeholder is genuinely needed, add it to this list in the same PR that introduces it.

## How to use a playbook

1. **Read the playbook end-to-end** before opening the matching workspace template. The playbook describes which compliance docs you must have in hand before any estimator hours are sunk.
2. **Copy the matching workspace template** from `bids/_TEMPLATES/<type>/` into `bids/<new-slug>/` and global-search-and-replace the `{{...}}` placeholders against the RFP.
3. **Pull scope templates** from `firm/scope-templates/` for whichever trades match the SOW; merge them into `04-scope-of-work.md` (federal template) or `04-scope-of-work.md` + `06-scope-outline.md` (state template).
4. **Pull proposal-library content** from `firm/proposal-library/`:
   - One archetype from `exec-summary-archetypes/`
   - The matching past-performance picks per `firm/firm-profile.json → past_project_selection_rules`
   - All six key-personnel files (paste into the project team section, then trim to the roles the RFP requires)
   - Whichever boilerplate sections the RFP asks for (safety, QA/QC, communication, schedule narrative, sub management, closeout)
5. **Confirm BPC compliance posture** against `firm/compliance/README.md`. If any required item is missing or expired, **stop and fix it** before any sub-quote goes out — most fixes have 3–10 business day turnaround and a stale cert can disqualify the bid on its face.
6. **Run `firm/_scripts/apply_firm_profile.py`** to substitute `firm-profile.json` values into the new workspace. Then run `firm/_scripts/scan_placeholders.py` to see what `[USER TO FILL]` markers remain and triage the firm-internal data-gathering before bid prep continues.
