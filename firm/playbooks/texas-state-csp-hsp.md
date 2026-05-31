# Playbook — Texas State CSP / RFCSP with HUB Subcontracting Plan

> **Exemplar bids (two — read both to see what's CSP-pattern vs project-specific):**
> - [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/) — TAMU System (Texas A&M, College Station), Harrington Lab 303 renovation, single-room educational lab, ~1,200 SF, CSP via SSC Services for Education
> - [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/) — TTU System (Angelo State, San Angelo), Carr Education and Fine Arts dressing-room renovation, 10 rooms / 3,115 SF, RFCSP via ASU Facilities Planning & Construction with HSP due 3 calendar days AFTER the proposal
>
> **Matching workspace template:** [`bids/_TEMPLATES/texas-state-csp-hsp/`](../../bids/_TEMPLATES/texas-state-csp-hsp/)

## 1. Procurement description

Texas state entities — public universities, K-12 ISDs, cities, counties, and state agencies — procure building construction primarily under **Tex. Gov't Code Ch. 2269 (Contracting and Delivery Procedures for Construction Projects)**, with the **Competitive Sealed Proposal (CSP)** delivery method as the dominant pattern for renovation and finish-out work. University systems use the CSP variant called **Request for Competitive Sealed Proposal (RFCSP)** under Tex. Educ. Code Ch. 51. The mechanics are the same.

Every state-funded CSP that subcontracts more than a de minimis amount triggers the **HUB Subcontracting Plan (HSP)** requirement per Tex. Gov't Code Ch. 2161 + 34 TAC §§ 20.281–20.298. A non-conforming HSP is the **#1 cause of TAMU System bid rejection** and applies across the entire state university system.

When you'll see it:

- TAMU System member institutions (TAMU College Station, TAMU Galveston, TAMU Corpus Christi, Prairie View A&M, West Texas A&M, TAMU Kingsville, TAMU International, etc.) — most run by SSC Services for Education on behalf of TAMU Facilities
- Texas Tech University System (Texas Tech, Angelo State, Texas Tech HSC) — usually direct via member-institution FP&C
- University of Texas System member institutions
- University of Houston System
- TSU (Texas Southern University)
- Texas K-12 ISDs with bond programs (Dallas ISD, Houston ISD, Fort Bend ISD, Cleburne ISD, etc.)
- Texas state agencies (TFC, TxDOT facilities)

When it's a different beast (use a different playbook):

- Federal-funded TX work — Davis-Bacon overrides Tex. Gov't Code Ch. 2258 prevailing wage; use the federal playbook
- Job-order contract pool at a TX university — JOC playbook (TBD)
- TX private commercial (developer / owner direct) — negotiated; not playbook-grade

## 2. Typical evaluation criteria

Per Tex. Gov't Code Ch. 2269 + standard TAMU System / TTUS CSP practice. **Exact weights are published in the CSP package** (Instructions to Proposers); the Notice of Project does not include them. Typical pattern:

| Factor | Typical weight range | What it measures |
|---|---|---|
| **Price** | 40–60% | Lump-sum proposal price + unit prices + alternates if requested |
| **Past performance / qualifications** | 15–25% | Similar institutional projects, references, key-personnel résumés |
| **Technical approach / project understanding** | 10–20% | Schedule, sequencing, coordination, QC, lab/specialty-specific considerations |
| **HUB / HSP compliance** | 10–15% | Quality of HSP submission + demonstrated GFE; sometimes pass/fail rather than scored |
| **Schedule (proposed substantial-completion duration)** | 5–10% | Often bidder-chosen with a fixed Final Completion window (e.g. TAMU Harrington: 70-day SC + 30-day fixed FC = 100 cal day) |
| **Safety record** | 0–5% | EMR (3-yr), OSHA recordables, safety plan |

**Anchor the price strategy on the published weights.** When the package is downloaded, replace the typical-pattern table in `06-evaluation-strategy.md` with the actual weights. Until then, plan against 50/20/15/10/5 (price / past-perf / technical / HSP / schedule).

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| TX HUB cert (firm-side) | Active if claiming HUB self-perform credit | VID `1874292998900` — **renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]`** (prior cycle expired 2024-08-31) | ✅ Active — capture new expiration before HSP submission |
| MBE cert (DFW MSDC) | Cascades into TX HUB recognition under DFW MSDC / TX Comptroller MOU | DL09279 — renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]` (prior cycle expired 2024-08-31) | ✅ Active — capture new expiration |
| SBE cert (DFW MSDC) | Useful for HSP self-perform sourcing | DL09279 — renewed 2026-05-30 per user; new expiration `[USER TO CONFIRM: new expiration date]` (prior cycle expired 2024-08-31) | ✅ Active — capture new expiration |
| TX Comptroller franchise tax good-standing | Auto-disqualification if not good-standing | TX Taxpayer ID `32082600456`; TX SOS file `0804376974`; TX WebFile `XT287610` | ⚠️ Verify good-standing before each bid via [Texas Taxable Entity Search](https://mycpa.cpa.state.tx.us/coa/) |
| TX CMBL (Centralized Master Bidder List) | Required to be listed for state-vendor visibility | Status TBD | ⚠️ Confirm |
| TX state-vendor # | Required for some agency portals | TBD | ⚠️ Confirm |
| TX COMET / agency-specific vendor portal accounts | Often required pre-RFP | TBD per agency | ⚠️ Confirm per RFP |
| County prevailing-wage rates for the project county | Required per Tex. Gov't Code Ch. 2258 | Not yet collected for any county | 🔴 Pull and shelf per county as each bid lands; track in [`firm/compliance/README.md`](../compliance/README.md) |
| TX statewide HUB goal (special-trade construction) | 21.1% per 34 TAC §20.284 | n/a — not a firm attribute | — |
| Bond capacity | Single-project ≥ contract value; aggregate ≥ project + current bonded backlog | Floor ≥ $1M from Lavon RV Park | ✅ Single-project; aggregate unknown |
| GL insurance (TAMU SGC Article 5 typical baseline: $1M / $2M) | $1M occurrence / $2M aggregate | $1M / $2M on expired policy | 🔴 Surface current COI |
| Umbrella / Excess (TAMU typical: $5M for institutional) | $5M (or per CSP package) | Not found in BPC files | 🔴 Confirm |
| WC + Auto + Builder's Risk | Per TAMU SGC | Not found in BPC files | 🔴 Confirm |
| OSHA 10/30 rosters for site supervision | Required by TAMU SGC | TBD per personnel | ⚠️ Confirm per project |
| Past performance — institutional/educational renovation, ≥ 3 similar projects | Yes (3+ ideally; some CSPs require 5) | Per [`firm-profile.json → past_project_selection_rules`](../firm-profile.json): TAMU/ASU picks are Hindu Temple of Southlake + Holiday Inn (Hall Park) + 250-500+ SFH portfolio | ⚠️ Cite-able; verify each owner-side reference contact before submission |
| TX Form CIQ (Tex. Local Gov't Code Ch. 176) | Yes (TX public-entity procurements) | Standard form; fill at bid time | ✅ Form on file convention |
| TX HB 1295 Certificate of Interested Parties | Required when contract value ≥ $1M OR contract requires legislative approval; otherwise often attached for prophylactic purposes | Form on file convention | ✅ |
| Texas resident-bidder attestation | Sometimes required | Per RFCSP | ✅ Boilerplate yes |
| Non-collusion affidavit | Standard | Per RFCSP | ✅ Boilerplate yes |

## 4. Required compliance docs checklist (for any TX-state-CSP-with-HSP bid)

Per-bid checklist (in addition to the firm-level table in §3):

- [ ] Completed CSP cover form / Proposal Form (TAMU System or TTUS or other agency-specific form; mirrors the typical Section 00 42 13 + Execution of Offer pattern)
- [ ] **HSP form** on the agency-specific template (TAMU System uses a different layout than TTUS uses) with all rows fully completed (vendor name, HUB cert #, scope, $ value)
- [ ] **HSP good-faith-effort (GFE) binder** — ≥3 HUB-certified subs solicited per scope item with dated outreach records (email, fax, certified mail); ≥2 ads in TX HUB publications; attendance at HUB outreach events where applicable
- [ ] Pricing proposal (lump-sum + unit prices + alternates per CSP form)
- [ ] Bid bond — 5% of total proposal price (or per CSP), original, payable to the agency's Board of Regents / governing body
- [ ] Surety commitment letter for Performance + Payment bonds (100% on award)
- [ ] Insurance certificates (ACORDs) compliant with the agency's SGC (TAMU System / TTUS / etc.) Article 5 limits, naming the agency as additional insured + waiver of subrogation + primary-and-non-contributory
- [ ] W-9, current calendar year, signed
- [ ] CIQ (Tex. Local Gov't Code Ch. 176) signed
- [ ] HB 1295 Certificate of Interested Parties filed with the Texas Ethics Commission (or attestation of non-applicability)
- [ ] Past performance / qualifications package (≥3 institutional projects; CSP may request up to 5)
- [ ] Project schedule / approach narrative
- [ ] Team org chart + key-personnel résumés
- [ ] Subcontractor list (if requested by CSP at proposal time; some CSPs defer to award)
- [ ] All addenda acknowledgments (numbered, signed)
- [ ] Sealed envelope with exterior labeling per CSP instructions (project number, name, due date/time, bidder name)

## 5. CSP scoring matrix template

The CSP scoring matrix is what the agency's evaluation committee fills in for each proposer. The exact rows + weights are in the CSP package; the structure is consistent.

| Factor | Weight | Score (0–100) | Weighted score | Notes |
|---|---|---|---|---|
| Price | `{{PRICE_WEIGHT}}%` | | | Lowest qualifying price typically gets 100; others scaled |
| Past performance | `{{PAST_PERF_WEIGHT}}%` | | | Quality + relevance of references; CO calls references |
| Technical approach | `{{TECHNICAL_WEIGHT}}%` | | | Narrative depth, project-specific considerations, sequencing |
| HSP compliance | `{{HSP_WEIGHT}}%` | | | Some CSPs make this pass/fail rather than scored |
| Schedule | `{{SCHEDULE_WEIGHT}}%` | | | Often bidder-chosen substantial-completion duration |
| Safety | `{{SAFETY_WEIGHT}}%` | | | EMR + OSHA history |
| **Total** | **100%** | | | |

**Pricing-vs-time trade-off discipline:** the shorter the proposed substantial-completion duration, the higher the schedule score — but the harder it is to deliver. Don't propose < 45 calendar days for a single-room reno without a defensible CPM schedule in the technical proposal.

## 6. HUB Subcontracting Plan (HSP) workflow

This is the **single most important section** of a TX-state-CSP bid. The HSP workflow lives on its own timeline that runs in parallel with the technical proposal. Start it the day the workspace lands.

### 6.1 The rules

- TX statewide HUB participation goals per 34 TAC §20.284:
  - **Heavy construction (other than building):** 11.2%
  - **Building construction** (GCs + operative builders): **32.7%** — typically quoted for whole-building work
  - **Special trade construction:** **21.1%** — typically applies to renovation work (Lab 303, Carr EFA dressing rooms)
  - Professional services: 23.7%; other services: 26.0%; commodities: 21.1%
- TAMU / TTUS / UT may set a **project-specific HUB goal** that overrides the statewide goal. Until confirmed, assume the **statewide special-trade goal (21.1%)** applies to renovation projects; **building (32.7%)** for whole-building work. The TTUS Sample CSA (Attachment B.2 in Angelo State) carries **30% HUB participation** as boilerplate — TTUS preference above the 21.1% statewide floor.
- The prime can **self-perform** any portion of the work as long as it's justified in the "Self-Performing Justification" section of the HSP. The HUB goal applies only to the **subcontracted** portion (denominator excludes self-perform $).
- A prime that does NOT meet the HUB goal can still be responsive if it documents **good-faith effort (GFE)** — see §6.4 below.
- Post-award: monthly **HUB Progress Assessment Reports (PARs)** must be filed with each pay application.

### 6.2 Per-trade HUB allocation table (template)

Based on a typical small GC self-performing ~25% of contract value, the HUB allocation by trade:

| Trade | % of contract | Plan | Target HUB share within trade | Notes |
|---|---|---|---|---|
| Demolition | 5–8% | Sub | **100%** | Many HUB-certified demo subs in TX |
| Drywall / metal-stud framing | 3–6% | Sub | 50% | HUB-certified drywall subs common |
| Doors / frames / hardware | 1–3% | Material-only OR sub | 0–100% | If material-only, check HUB-certified door distributors |
| Flooring (LVT, sheet vinyl, base) | 4–7% | Sub | 50% | HUB flooring subs in central TX |
| Painting | 2–4% | Sub | **100%** | HUB paint subs abundant |
| Acoustic ceilings | 2–3% | Sub | 50% | |
| Casework / lab-grade millwork | 7–12% | Sub | 25% | Specialty; HUB availability thinner |
| Electrical | 10–15% | Sub | 50% | Lab-experienced HUB subs thinner |
| HVAC | 6–10% | Sub | 25% | Lab-experienced HVAC subs mostly mid-size |
| Plumbing | 5–8% | Sub | 50% | |
| Fire suppression mods | 1–3% | Sub | 25% | NICET requirement narrows pool |
| Low-voltage pathway | 1–2% | Sub OR self | 50% | |
| Lab utility specialty | 2–4% | Sub | 0% with GFE if unavailable | |
| **GC + supervision (self)** | 8–12% | Self | n/a — excluded from HUB calc | |
| **OH + profit + bond** | 12–18% | n/a | n/a — excluded | |

**Roll-up target:** ≥ project-specific goal OR ≥ 21.1% (statewide special-trade goal) OR ≥ 32.7% (statewide building goal), whichever applies.

### 6.3 HUB sub sourcing — TX CMBL

Look up HUB-certified vendors at the **Texas CMBL HUB Search**: <https://comptroller.texas.gov/purchasing/vendor/hub/search.php>

- Filter by HUB-certified
- Filter by NIGP / NAICS code matching the trade
- Filter by geographic region (county of the site + adjacent counties + statewide for specialty work)

Process per trade:

1. Pull top 5–10 candidate HUB subs from CMBL
2. Email a standardized solicitation packet (project name + number, scope summary, due date back-timed from proposal, plans / specs link, required certs, GC contact)
3. Log every outreach (date, method, recipient, response or non-response)
4. If a HUB sub bids and is selected → include in HSP with vendor #
5. If a HUB sub bids and is NOT selected (price, schedule, qualification) → document the reason
6. If a HUB sub does NOT respond → counts as part of GFE evidence

Suggested log format (use a `local/hub-outreach-log.csv` outside git):

```
date,trade,sub_name,hub_cert_number,contact_email,method,outcome,bid_amount,notes
```

### 6.4 Good-faith-effort (GFE) documentation

When the HUB goal is not met, TX HSP rules require at least **two** of the following. To be safe, do all four:

1. **Divide the scope into reasonable HUB-sized portions** — the per-trade table is the seed
2. **Advertise the subcontracting opportunity** in ≥ 2 of: TX Comptroller's HUB News; trade publications serving HUBs (Texas Construction News, Greater Houston Black Chamber publication, Asian American Chamber of Commerce Texas, Hispanic Contractors Association of Texas, NAWIC TX chapter); firm's own subcontractor-bid portal with a HUB notice
3. **Send written notice to a representative sample of HUB subcontractors** for each subcontracting opportunity (the per-trade outreach in §6.3 satisfies this)
4. **Attend HUB outreach events** the agency hosts
5. **Contact a HUB Discretionary Contracting Forum** participant — for TAMU specifically, contact the TAMU HUB Operations office

### 6.5 Post-award HSP reporting

- **Monthly Progress Assessment Reports (PARs)** filed with each pay application
- Use the State of Texas Comptroller PAR form
- If actual HUB participation falls short of the HSP commitment, the prime must either revise the HSP (with agency concurrence) or document the reason and continue GFE

## 7. TX UGSC 2010 + SGC awareness

The **Uniform General Conditions for Texas Government Building Construction Contracts (2010 edition)** is published by the Texas Facilities Commission and adopted (with edits) by every state university system. The TAMU System and TTUS each maintain a "Supplementary General Conditions" overlay.

- **Sample full UGSC + SGC reference:** [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/) Attachment C ("2010 Uniform General Conditions and Supplementary General Conditions dated (TTUS edited 09.07.2023)")
- Article cross-walk (TAMU SGC may renumber but content is parallel):
  - Article 5 — Insurance (carrier ratings, limits, additional insured, waiver of subrogation)
  - Article 6 — Bonds (5% bid, 100% P&P on award; TX statutory bond forms)
  - Article 7 — Submittals and Quality Control
  - Article 8 — Construction Progress (CPM schedule, weekly updates)
  - Article 9 — Time of Performance + Liquidated Damages
  - Article 10 — Payment Procedures
  - Article 11 — Changes (change-order procedure)
  - Article 12 — Time of Substantial Completion + closeout
  - Article 13 — Warranty

**Action when a new TAMU / TTUS / UT bid lands:** read the SGC overlay first; it tells you what differs from the base UGSC. Save the SGC into the bid workspace.

## 8. Sample Construction Services Agreement (TTUS Attachment B.2 pattern)

The CSA is what the winning bidder signs at award. Key clauses to read **before bidding** (they may inform the price):

- HUB contracting commitment percentage (TTUS sample CSA carries 30%)
- Liquidated damages per calendar day (commonly $250–$1,000 for sub-$1M reno; ASU Carr EFA = $250/day)
- Payment terms (TAMU SGC: Net-30 after pay app approval; SSC Master Vendor Agreement: Net-75 — read carefully if SSC-managed)
- Sub flow-down insurance limits (Master Vendor Agreements often require $10M CGL aggregate + $10M umbrella from subs)
- Non-solicit / non-compete clauses (SSC MVA has 2-year non-solicit + 1-year non-compete with the client)
- Retainage (commonly 5–10%, released at substantial completion + 30 days)

**If any of these terms are deal-breakers, raise as RFI before submission.** Once you sign at award, you're bound.

## 9. Prevailing wage workflow (Tex. Gov't Code Ch. 2258)

State-funded construction in TX requires payment of the **county prevailing wage rate** for each trade, determined per Tex. Gov't Code Ch. 2258.

- The **county prevailing-wage rate table** is published either by the awarding state agency (TFC publishes for state agencies) or by the project's owner. For TAMU System work, the rate table is typically attached to the CSP package (e.g. ASU Attachment F.1 — Tom Green County Prevailing Wage 2023).
- Some counties publish their own; cross-check the project county's rates against the Texas Workforce Commission (TWC) at <https://www.twc.texas.gov/businesses/prevailing-wage-rates>.
- Build a county-rate cache under [`firm/compliance/README.md → prevailing-wage cache`](../compliance/README.md) as bids cycle through different counties.

## 10. Submission portals

- **ESBD (Electronic State Business Daily)** — `https://www.txsmartbuy.com/esbd` — primary notice portal. Every TX state RFP / RFCSP / IFB is posted here. Watch via TX SmartBuy filters.
- **Trimble Unity Construct / e-Builder** — `https://app.e-builder.net/public/publicLanding.aspx?QS=<id>` — TAMU System CSP package portal. The Notice of Project (NOP) on ESBD points to an e-Builder Public Landing Page for the full CSP package (drawings, specs, contract draft, HSP form, pricing form, bid bond form, addenda). Download everything.
- **Direct SSC portal** — for TAMU System SSC-managed bids, the SSC PM may share files via SharePoint / email
- **Agency procurement portals** — UT BuildIt, ASU Facilities Planning, TTU Procurement; vary by member institution

## 11. State-vendor # + COMET + CMBL prerequisites

| Prereq | What it is | When you need it |
|---|---|---|
| **TX SOS file number** | Texas Secretary of State entity filing number | BPC: `0804376974` |
| **TX Comptroller Taxpayer ID** | TX state taxpayer ID (different from federal EIN) | BPC: `32082600456` |
| **TX Comptroller WebFile** | TX Comptroller online tax-filing account | BPC: `XT287610` |
| **TX CMBL** | Centralized Master Bidder List enrollment (free; required for some agency portals) | Confirm enrollment status before each new agency |
| **TX state-vendor #** | Some agencies issue a vendor number on first registration | Confirm per agency |
| **TX COMET** | TX Comptroller's contracts platform — required for some agencies | Confirm per agency |

## 12. Typical timeline

| Phase | Days from Notice of Project | Notes |
|---|---|---|
| NOP issued on ESBD | T-0 | Notice points to e-Builder for the full CSP package |
| Pre-response meeting | T+5 to T+10 | Often non-mandatory but "highly recommended"; some are mandatory (verify) |
| Proposal due | T+25 to T+40 | TX state CSPs typically give 4–6 weeks |
| **HSP due** (separate deadline on some TTUS / ASU bids) | T+28 to T+43 | **Watch for this** — ASU Carr EFA had HSP due **3 calendar days AFTER** the proposal |
| Public opening | Immediately after proposal due | Sealed envelopes opened in-person + Teams livestream |
| Evaluation period | 2–4 weeks for sub-$500K CSP | |
| Best-and-final / clarifications | After evaluation | Some CSPs permit BAFO; TAMU / TTUS sometimes do |
| Award notification | T+50 to T+75 | Posted on ESBD |
| NTP issuance | Within 30 days of award typically | |
| Performance period | Per CSP / RFCSP — typical 60–180 calendar days for renovation | LD rate per CSA |

## 13. Common pitfalls

1. **HSP good-faith-effort binder is thin** — disqualification on HSP GFE is the #1 cause of TAMU System bid rejection. Start outreach the day the workspace lands.
2. **Missed pre-response / pre-proposal meeting** — if mandatory, bid is automatically non-responsive. Confirm in writing whether it was mandatory; if so, request sign-in sheet, recording, and Q&A from the agency PM.
3. **Wrong HSP form** — TAMU uses a different form than TTUS uses than UT uses. Pull the form from the CSP package, don't reuse from a prior bid at a different system.
4. **HSP separately due** — some TTUS bids put the HSP on a deadline 1–3 days AFTER the proposal. If you forget the HSP deadline, the proposal is automatically rejected.
5. **TX HUB cert lapsed** — annual recertification; an expired cert kills any HUB self-perform credit and any HSP commitment that lists the firm itself.
6. **TX Comptroller franchise tax not in good standing** — auto-disqualification. Check via Texas Taxable Entity Search before each bid.
7. **CIQ / HB 1295 missing or with mismatched legal name** — TAMU clerks reject mismatches.
8. **Sealed-envelope labeling wrong** — TX state procurement is famously process-oriented. Outside-of-envelope labeling must exactly match the CSP instructions (project number, name, due date/time, bidder name). Wrong label = rejected unopened.
9. **Subcontractor list required at proposal but submitted blank** — some CSPs require it at proposal; some defer to award. Read carefully.
10. **Unit prices padded** — TAMU clerks score unit-price reasonableness; padded unit prices can be a basis for non-responsibility finding even if base lump-sum is competitive.
11. **Insurance limits below SGC requirement** — some TAMU SGCs require $5M Umbrella; the firm's $1M / $2M GL alone won't meet the test.
12. **Conflict-of-interest with active TAMU / TTUS contract** — disclose on CIQ.
13. **Pre-response meeting Q&A not absorbed** — the Q&A often clarifies scope ambiguity. Get the published Q&A from the agency PM and re-read before pricing.

## 14. CSP pricing strategy

- **Lump-sum number** — the dominant scoring axis
- **Unit prices** — TX state CSPs often request unit prices on common owner-directed change items (sq. ft. of additional flooring, additional door, additional outlet). Bid these at **full retail** (sub cost + your full GC markup), not stripped — they set the change-order ceiling
- **Alternates** — bid only what the CSP lists; ignore the temptation to add unsolicited alternates (often disqualifies for non-responsiveness)
- **Allowances** — if CSP includes an owner-controlled cash/contingency allowance (ASU Attachment A had a $25,000 allowance), carry it line-by-line per CSP instructions — do NOT roll into lump-sum, do NOT mark it up
- **Markup discipline (state CSP):**
  - General conditions (PM, super, temp services) priced from the duration in scope-of-work
  - Bond + insurance loaded as a percentage of subtotal
  - **Contingency: 5–7%** for a single-room reno with reasonable drawings; bump to 10% if drawings are thin
  - **Overhead: 8–12%** typical
  - **Profit: 5–7%** typical for institutional state work
- **Don't over-shave.** TX state agencies reject bids that are > 25% below the median as "non-responsible" risk. Aim for tight, not lowest.

## 15. Reusable language blocks

| Block | Where it lives | When to use |
|---|---|---|
| TX state CSP exec-summary opening (cover letter) | [`firm/proposal-library/exec-summary-archetypes/texas-state-csp.md`](../proposal-library/exec-summary-archetypes/texas-state-csp.md) | Cover letter front of the bound proposal |
| Past-performance picks for institutional reno | [`firm/proposal-library/past-performance/`](../proposal-library/past-performance/) — per [`firm-profile.json → past_project_selection_rules`](../firm-profile.json), TAMU/ASU picks = Hindu Temple of Southlake + Holiday Inn (Hall Park) + 250-500+ SFH portfolio | Past Performance section |
| Key-personnel one-pagers (full set) | [`firm/proposal-library/key-personnel/`](../proposal-library/key-personnel/) | Project Team section |
| 3-phase QC plan (prep / initial / follow-up + completion) | [`firm/proposal-library/boilerplate/qa-qc-plan-one-pager.md`](../proposal-library/boilerplate/qa-qc-plan-one-pager.md) | Quality Control section |
| Site-specific safety plan template (OSHA + EHS) | [`firm/proposal-library/boilerplate/safety-plan-one-pager.md`](../proposal-library/boilerplate/safety-plan-one-pager.md) | Safety Plan section |
| Communication plan | [`firm/proposal-library/boilerplate/communication-plan.md`](../proposal-library/boilerplate/communication-plan.md) | Project-management approach |
| Schedule narrative skeleton (phased trade sequencing) | [`firm/proposal-library/boilerplate/schedule-narrative-skeleton.md`](../proposal-library/boilerplate/schedule-narrative-skeleton.md) | Schedule narrative + Gantt |
| Subcontractor management | [`firm/proposal-library/boilerplate/subcontractor-management.md`](../proposal-library/boilerplate/subcontractor-management.md) | Sub plan + HSP narrative |
| Closeout plan | [`firm/proposal-library/boilerplate/closeout-plan.md`](../proposal-library/boilerplate/closeout-plan.md) | Closeout / O&M / training narrative |

## 16. Cross-references

- **Workspace template:** [`bids/_TEMPLATES/texas-state-csp-hsp/`](../../bids/_TEMPLATES/texas-state-csp-hsp/)
- **Scope templates:** [`firm/scope-templates/office-tenant-refurb.md`](../scope-templates/office-tenant-refurb.md), [`firm/scope-templates/dressing-room-renovation.md`](../scope-templates/dressing-room-renovation.md)
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Exemplar shipped bids:** [`bids/tamu-harrington-2025-06813/`](../../bids/tamu-harrington-2025-06813/), [`bids/angelo-state-carr-efa-26-007/`](../../bids/angelo-state-carr-efa-26-007/)
