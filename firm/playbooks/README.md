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
| [`federal-simplified-acquisition-best-value.md`](federal-simplified-acquisition-best-value.md) | Federal Simplified Acquisition (FAR Part 13, often + Part 12 commercial-item), best-value comparative trade-off across price + technical capability + prior experience — the gap between pure LPTA and full FAR Part 15 tradeoff; quote on SF-18 (or SF-1449), often evaluated "in groups of 3 lowest priced" | [`bids/pais-cabin-140P6026Q0029/`](../../bids/pais-cabin-140P6026Q0029/) (first dogfood) |
| [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md) | Federal RFP under FAR Part 15 tradeoff source-selection (technical + past-performance + price weighed) | *not yet exemplified — eligible for future federal RFPs at $250K+ where the agency values technical approach over price-only* |
| [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md) | Pre-solicitation workflow (sources-sought, RFI, industry day, capability statements) — what BPC does BEFORE an RFP drops | [`bids/_WATCHLIST/`](../../bids/_WATCHLIST/) entries (SAAN San Juan restrooms 140P1226Q0025; PAIS Backcountry Cabin 140P6026Q0029 anticipated) |
| [`federal-joc-task.md`](federal-joc-task.md) | Federal Job-Order Contract (JOC) task order via pre-priced UPB + coefficient bidding | *not yet exemplified — BPC not yet pre-qualified into any JOC pool; playbook drives Day-3+ research action* |
| [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md) | Texas state-funded Competitive Sealed Proposal (CSP / RFCSP) under Tex. Gov't Code Ch. 2269, with mandatory HUB Subcontracting Plan | [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/), [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/), [`bids/leroy-moore-gym-PV-0749-PV-0753/`](../../bids/leroy-moore-gym-PV-0749-PV-0753/) |
| [`texas-municipal-csp.md`](texas-municipal-csp.md) | Texas City / County / ISD Competitive Sealed Proposal under Tex. Local Gov't Code Ch. 252 / 262 / Educ. Code Ch. 44 — adds CIQ + HB 1295 + local-preference overlay | *not yet exemplified — eligible for Dallas / Frisco / Plano / McKinney / Allen / Garland / DFW-region ISD bond-program CSPs that match BPC scope* |

## Procurement-type matrix

The matrix is the cheat-sheet for matching an incoming opportunity to the right playbook. Read it left to right when you triage a new RFP.

| Procurement archetype | Playbook | Eligible BPC bids exemplifying it | Solicitation portals | Required compliance docs (must be current at bid) | Bid bond | P&P bonds | Typical NAICS / scope |
|---|---|---|---|---|---|---|---|
| **Federal SBA RFQ / RFP — LPTA** | [federal-sba-rfq-lpta](federal-sba-rfq-lpta.md) | USFWS San Marcos 140FC126R0017; future USFWS / USACE / NPS / TXANG (federal) small construction | SAM.gov (primary), PIEE (Wide-Area Workflow for DoD), agency email | SAM registration active, UEI + CAGE current, Reps & Certs ≤12 months old, FAR 52.219-1 small-size assertion on the bid NAICS, FAR 52.204-21 Basic Safeguarding posture, FASCSA rep (52.204-29), Section 889 reps (52.204-24/-25/-26), Buy American reps, DBA / certified-payroll readiness, Davis-Bacon WD freshness | 20% of bid OR $1M (whichever less) per FAR 52.228-1 | 100% Performance + 100% Payment if > $150K per FAR 28.102-1(a) / FAR 52.228-15 | NAICS 236220 small at $45M cap; renovation, rehab, site work, small ground-up |
| **Federal Simplified Acquisition — best-value comparative trade-off** (FAR Part 13 + 12) | [federal-simplified-acquisition-best-value](federal-simplified-acquisition-best-value.md) | PAIS Cabin 140P6026Q0029 (first dogfood); future DOI/NPS/USFWS/USDA-Forest-Service/BLM facility-repair RFQs $50K–$250K, DoD installation-repair work below SAT, GSA small-construction repair task orders | SAM.gov (primary), agency email (very common at SAP scale) | Same as LPTA, but: **technical-capability narrative (5–15 pp) REQUIRED**; 3–5 prior-experience references (per Section L); SF-18 (or SF-1449) NOT SF-1442; alt-payment protection per FAR 52.228-13 typical | Typically NONE at submission — FAR 52.228-13 Alternative Payment Protections common | 100% Performance + 100% Payment (or 52.228-13 alt-payment) due within 10 cal days of award | NAICS 236220 small; SAP cap $250K civilian / $7.5M commercial-item per FAR 13.003 / 13.500 |
| **Federal best-value RFP** (FAR Part 15 tradeoff) | [federal-rfp-best-value-tradeoff](federal-rfp-best-value-tradeoff.md) | *not yet exemplified — playbook now available* | Same as LPTA | Same as LPTA plus PPQ-readiness, oral-presentation capability, FPR workflow, Volume I/II/III/IV technical-narrative discipline | Same | Same | Same |
| **Federal pre-solicitation (sources-sought / RFI / industry day)** | [federal-pre-solicitation-watchlist](federal-pre-solicitation-watchlist.md) | [`bids/_WATCHLIST/`](../../bids/_WATCHLIST/) entries — SAAN San Juan, PAIS anticipated; NPS / USACE / USFWS / GSA cycles | SAM.gov (sources-sought + pre-solicitation notice tabs), agency forecast pages (NPS / USACE / GSA), industry-day registration portals | Capability statement (current), SAM active, OSHA EMR ≤ 1.0 documented, past-performance summary ready to attach | None | None | All federal scopes BPC is positioned for |
| **Federal job-order contract (JOC) task** | [federal-joc-task](federal-joc-task.md) | *not yet exemplified — BPC not pre-qualified in any JOC pool; playbook drives Day-3+ research action* | SAM.gov (IDIQ solicitation phase) + agency JOC pool portal (task-order phase) | IDIQ pre-qual: technical + past-performance + financial qualification; coefficient pricing strategy; UPB (RSMeans / Gordian) familiarity. Task-order phase: NTE coefficient + project-specific coefficient + bond letter ready | None at task | Per task (typically 100% P&P at task order if > $150K) | NAICS 236220 facility renovation, repair, light new construction |
| **Texas State CSP / RFCSP (Ch. 2269) with HSP** | [texas-state-csp-hsp](texas-state-csp-hsp.md) | TAMU Harrington 2025-06813; Angelo State Carr EFA 26-007; Leroy Moore Gym PV-0749/0753 (PVAMU); future TAMU / TTUS / UT System / UH System / TSU / TX K-12 | ESBD (Electronic State Business Daily, primary notice), Trimble Unity Construct / e-Builder (TAMU System CSP package portal), direct agency SSC / FP&C portals, agency email | TX HUB cert current (or HSP GFE binder), TX CMBL active, TX SOS franchise-tax good-standing, TX Comptroller WebFile, county prevailing-wage table for project county, OSHA 10/30 rosters for site supervision, CIQ + HB 1295 form-readiness | 5% of bid per Tex. Gov't Code Ch. 2253 | 100% Performance + 100% Payment (TX Statutory Bonds, SF 25 / 25A or TTUS / TAMU equivalents) | NAICS 236220 / 236118; interior reno, lab + classroom modernization, dressing-room reno, finish-out |
| **Texas City / County / ISD CSP** | [texas-municipal-csp](texas-municipal-csp.md) | *not yet exemplified — eligible for Dallas / Frisco / Plano / McKinney / Allen / Garland + DFW-region ISD bond-program CSPs* | City procurement portals (Ionwave, Bonfire, OpenGov, ProcureWare); ISD bond-program portals (TASB BuyBoard, regional ESC co-ops); county purchasing portals | CIQ (Tex. Local Gov't Code Ch. 176) ALWAYS; HB 1295 Form 1295 for ≥ $1M; TX Comptroller good-standing; county prevailing wage (Tex. Gov't Code Ch. 2258); local-preference ordinance compliance (Dallas, Houston); M/WBE goals (Dallas, Houston stronger than state HUB); cooperative-purchasing reference (BuyBoard / Choice Partners) when applicable | Varies (1–5% bid) | 100% P&P typically | NAICS 236220 / 238 trades; ISD bond-program facility renewal, city facility renovation |
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
