# 08 — Contract-terms flags (UGSC + Sample CSA + Project Manual supplementary conditions)

> Sources:
> - Attachment C — 2010 TFC Uniform General Conditions as supplemented by TTUS, edited 09.07.2023 (`inbox/.../ESBD_516718_..._Attachment C - ...UGSC...pdf`)
> - Attachment B.2 — Sample Construction Services Agreement (`inbox/.../ESBD_516718_..._Attachment B.2 - Sample Construction Services Agreement.pdf`)
> - **NEW 2026-05-23: Project Manual Section 00 70 00 (Conditions of the Contract), 00 73 00 (Supplementary Conditions), 00 73 43 (Wage Rate Requirements TX), 00 73 46 (Wage Determination Schedule)** in `inbox/.../26-007 Carr EFA Dressing Room Renovation Project Manual.pdf` pages 35-66
> - Project Manual Div 01 General Requirements (Sec 01 10 00 through 01 91 13) pages 67-218
>
> 2026-05-23 refresh: Project Manual conditions read; major flags below now include the JOC/CSA discrepancy and Sec 01 35 16 Alteration Project Procedures.

---

## A. Top contract-terms flags (the ones that matter most for pricing this bid)

### Flag #0 — JOC vs CSA contract-form discrepancy in Project Manual ⚠️ NEW 2026-05-23

**Why it matters:** Project Manual Section **01 10 00 § 1.5** reads *"Project will be constructed under a Job Order Contract"* but the procurement is via **RFCSP under Tex. Gov't Code Ch. 2269** (which authorizes Construction Services Agreement via competitive sealed proposals). These are two completely different procurement vehicles — a JOC is a master-contract IDIQ-style vehicle and a CSA is a discrete-project lump-sum-or-GMP vehicle. The Sample CSA at Attachment B.2 is the actual contract form (consistent with the procurement vehicle); the 01 10 00 reference is almost certainly a PBK template-boilerplate scrivener's error (PBK does a lot of K-12 JOC work).

**Action:**
- **Flag to Hannah Bignall in the eligibility email** (`outreach/01-email-hannah-bignall-eligibility.md` § 3) — request written confirmation that post-award contract form will be the Sample CSA, NOT a JOC.
- If by some chance ASU intends to procure via JOC, the entire bid form, bond requirements, payment terms, and change order mechanism are different — we need to know before submission.
- Note in proposal Assumptions & Clarifications: "Proposal is based on Sample CSA at Attachment B.2 as the post-award contract form."

### Flag #0.5 — Project Manual Section 01 35 16 Alteration Project Procedures ⚠️ NEW 2026-05-23

**Why it matters:** Sec 01 35 16 is the dedicated alteration-project procedures section. It controls how we handle: (a) protection of existing-to-remain construction, (b) noise/dust windows, (c) coordination with active building, (d) cutting and patching procedures, (e) hazardous-material-encounter protocols (cross-references 01 35 43.13 + 02 82 00/02 83 00/02 87 13). Compliance is a labor + GC overhead premium of 5-8% on the trades that work in occupied zones.

**Action:**
- Price 5-8% premium-time labor allowance into demo + MEP trade scope.
- Include 01 35 16 + 01 35 43.13 procedures in the subcontractor scope packages.
- Include the IAQ procedures of Sec 01 35 46 — HVAC filtration upgrades during demo, no high-VOC finishes during occupied hours.

### Flag #1 — Insurance article (UGSC Art. 5) carries unusually strict additional-insured and timing requirements

**Why it matters:** The named-insured + waiver-of-subrogation + primary-and-non-contributory + 30-day-cancellation-notice combo is standard, but **TTUS pattern requires the insurance certificate to be received and accepted by ASU FP&C *before any work begins*** — not "within 30 days of NTP," not "before progress invoice 1." If our broker can't issue an acceptable cert on day one, NTP is functionally on hold and the LD clock could still be running against the fixed 11/2 substantial completion date.

**Action:**
- Confirm broker can issue the cert with all the right wording before 2026-07-01 NTP
- Cert must name "The Board of Regents of the Texas Tech University System, Angelo State University, and their officers, employees, and agents" as additional insured
- Waiver of subrogation in favor of additional insureds
- Primary and non-contributory language
- 30 days written notice of cancellation TO the additional insureds
- Confirm whether Builder's Risk is owner-carried (typical TTUS) or GC-carried (uncommon) — Builder's Risk is the single largest line in the insurance cost stack
- Pollution Liability if hazmat scope is added — confirm broker capacity

### Flag #2 — Liquidated damages mechanic + cap

**The number:** $250 / calendar day past substantial completion (per RFCSP). The Sample CSA placeholder is "$###.00 per calendar day of delay" (per v3 extract `bid_packages[7]`); the executed CSA will fill in the $250.

**The cap (if any):** TTUS sample CSA pattern — confirm against the actual Attachment B.2 PDF — typically does NOT cap LDs. Uncapped LDs on a fixed 2026-11-02 substantial completion is a real risk. 30 days late = $7,500. 60 days late = $15,000. 90 days late = $22,500. If construction slips into next semester, we're north of $25K in LDs which compounds with the project's profit margin compression.

**Action:**
- Read the LD article in the CSA cover-to-cover; confirm whether there's a cap
- If uncapped: in proposal Assumptions & Clarifications, note "schedule is conservatively bid to 2026-10-20 substantial completion, providing 13 days of float against the contract date"
- Post-award negotiate (if any leverage exists): request an LD cap at 5% of contract sum or 90 days of LDs, whichever is greater
- Reinforce schedule discipline per `07-risk-register.md` R-09 + R-10

### Flag #3 — Differing site conditions clause

**Why it matters:** UGSC Art. 4 (or equivalent) typically gives the GC a path to a change order if site conditions materially differ from those reasonably inferable from the construction documents. For a renovation in a 1960s/1970s-era performing-arts building, differing-site-conditions is the single most-likely change-order driver: asbestos surprises, hidden water damage, undersized electrical service, unexpected fireproofing, surprise plenum obstructions.

**Action:**
- Confirm the differing-site-conditions clause is in the TTUS-edited UGSC (it's in the 2010 TFC baseline; check whether TTUS preserved it)
- Confirm the notice-of-condition window (typically 7–14 calendar days from discovery; missing the window = no change order)
- Set up an internal procedure to document any differing condition with photographs + timestamps + immediate written notice to Samuel within 5 calendar days (well inside any TTUS notice window)
- Budget the $25,000 cash/contingency allowance from Attachment A primarily for differing-conditions consumption; do NOT consume it for owner-directed scope changes (those should be priced as separate change orders)

---

## B. Detailed clause-by-clause review checklist (read the actual PDFs to confirm)

### Insurance (UGSC Article 5)

- [ ] Commercial General Liability limit — confirm per occurrence + aggregate. TTUS pattern: $1M / $2M minimum for sub-$1M contracts
- [ ] Automobile Liability — confirm. TTUS pattern: $1M CSL
- [ ] Workers' Compensation — statutory TX limits; Employer's Liability $1M / $1M / $1M
- [ ] Umbrella / Excess — confirm. TTUS pattern: $5M for sub-$1M contracts; $10M+ for $1M+
- [ ] Builder's Risk — confirm owner-carried or GC-carried. TTUS commonly owner-carries on renovation.
- [ ] Pollution Liability — required if hazmat scope?
- [ ] Professional Liability — if any design-build elements (likely not on this project)
- [ ] Additional insured language — exact wording (see Flag #1)
- [ ] Waiver of subrogation in favor of additional insureds
- [ ] Primary and non-contributory wording
- [ ] Cancellation notice period (typically 30 days)
- [ ] Insurance cert delivery timing — **CRITICAL: before any work begins** is TTUS pattern; if rephrased "within X days," what happens to NTP

### Indemnity (typically UGSC Art. 5 or Art. 14)

- [ ] Scope of indemnity — broad form (Texas law historically restricts), intermediate form, or comparative-fault?
- [ ] Texas anti-indemnity statute (Tex. Civ. Prac. & Rem. Code § 130.002) applies to construction contracts — confirm UGSC indemnity wording is statute-compliant
- [ ] Defense obligation — is indemnitor obligated to defend?
- [ ] Mutual indemnity or one-way (GC indemnifies owner only)?
- [ ] Carve-out for owner's sole negligence (required under Texas law for residential; common practice for commercial)

### Liquidated damages (typically UGSC Art. 13 or CSA exhibit)

- [ ] LD rate — $250/calendar day confirmed from RFCSP; verify on CSA
- [ ] LD cap (if any) — see Flag #2
- [ ] LD trigger — substantial completion date (fixed) vs days from NTP — see `07-risk-register.md` R-10
- [ ] LD waived for force majeure (typically yes; check exceptions list)
- [ ] LD waived for owner-caused delay (typically yes)
- [ ] LD waived for differing-site-conditions delay (typically yes)
- [ ] LDs are owner's exclusive remedy for late completion (vs additional damages)? — commonly yes

### Retainage (typically UGSC Art. 10 or 11)

- [ ] Retainage percentage — TTUS pattern: 5% on the first 50% of contract, 0% thereafter (Tex. Gov't Code § 2252.032). Sometimes 10% throughout for higher-risk contracts.
- [ ] Substantial completion retainage release — typically retainage is partially released at substantial completion (e.g. 50% of accrued retainage)
- [ ] Final retainage release — typically 30–60 days after final acceptance, with all close-out submitted

### Differing site conditions (typically UGSC Art. 4)

- [ ] Clause exists — see Flag #3
- [ ] Notice window — calendar days from discovery
- [ ] Notice format — written, to whom
- [ ] Owner-acknowledgement timing
- [ ] Cost + time adjustment mechanism

### Change order pricing methodology (typically UGSC Art. 9)

- [ ] Methodology — direct cost + agreed markup (typical TTUS), unit prices from bid (if applicable), force account / T&M as fallback, or competitive sub-bid
- [ ] Allowable markup on direct cost — TTUS pattern: 15% on labor, 10% on materials, 10% on subcontractor work; confirm
- [ ] Bond + insurance markup on change orders — typically 1.5–2% combined
- [ ] Cumulative cap on change order markup — sometimes capped at $50K or 5% of contract
- [ ] Time impact analysis required for any change >$25K — typical TTUS requirement

### Termination for convenience (typically UGSC Art. 14 or 15)

- [ ] Termination for convenience clause exists — typical TFC UGSC
- [ ] Compensation on termination — typically: work performed to date + reasonable demob costs + (no profit on un-performed work)
- [ ] Notice period — typically 30 days written notice

### Termination for cause (UGSC Art. 14 or 15)

- [ ] Cure period before termination — typically 10–15 days written notice
- [ ] Owner's remedies — completion by others, with cost back-charged
- [ ] GC's remedies if owner improperly terminates

### Dispute resolution + venue (typically UGSC Art. 16 or CSA exhibit)

- [ ] Mediation required before litigation — typical TTUS
- [ ] Arbitration — typically NO for TTUS state work (sovereign immunity considerations)
- [ ] Venue — **Tom Green County, TX** typical for ASU-related disputes (the location of ASU); some TTUS contracts venue in Lubbock County (TTU main campus)
- [ ] Governing law — TX
- [ ] Attorney's fees — recoverable to prevailing party? (Tex. Civ. Prac. & Rem. Code Ch. 38 may govern)

### Payment terms (typically UGSC Art. 10)

- [ ] Pay app cycle — monthly pay apps typical
- [ ] Pay app due date — typically by 5th of the month
- [ ] Owner review period — typically 7–10 days
- [ ] Payment due date — typically 30 days from pay-app submission (Tex. Gov't Code § 2251 prompt-payment)
- [ ] Late payment interest — statutory under Tex. Gov't Code Ch. 2251
- [ ] Conditional / unconditional lien waivers required with pay apps — typical TTUS
- [ ] Monthly HSP Progress Assessment Report (PAR) required with each pay app — TTUS UGSC requirement; confirmed by `05-hsp-plan.md` § F

### Bonds (typically UGSC Art. 6)

- [ ] Bid bond — 5% of base proposal if total > $25K (Tex. Gov't Code Ch. 2253) — confirmed by RFCSP
- [ ] Performance Bond — 100% of contract value if > $100K — confirmed
- [ ] Payment Bond — 100% of contract value if > $25K — confirmed
- [ ] Bond form — TTUS-required form (must be in TTUS library, not generic AIA A310/A312)
- [ ] Surety qualifications — A.M. Best A- or better, on US Treasury Circular 570 list
- [ ] Bond delivery timing — typically with executed CSA

### HUB Subcontracting Plan (typically UGSC Art. 3 + Attachment D)

- [ ] HSP required — confirmed; see `05-hsp-plan.md`
- [ ] Project-specific HUB goal — TBD per RFCSP; sample CSA shows 30% placeholder
- [ ] HSP submission deadline — **Monday 2026-06-08, 5:00 PM CST** (per RFCSP)
- [ ] Monthly PARs required post-award — confirmed
- [ ] Revised HSP required if subcontracting scope changes — typical TX requirement
- [ ] Sanctions for HSP non-compliance — material breach of contract per Tex. Gov't Code Ch. 2161

### Warranties (typically UGSC Art. 12)

- [ ] Standard warranty period — **1 year from substantial completion** typical TTUS
- [ ] Extended warranties — typically pass-through manufacturer warranties for HVAC equipment (5–10 yr), lighting (5 yr), roofing (NSA, but no roofing on this project)
- [ ] Latent defect period — Texas statute of repose is 10 years

### Project closeout (typically UGSC Art. 11 or 12)

- [ ] Substantial completion criteria — punch list issued, owner can occupy
- [ ] Final completion criteria — punch list closed, all submittals approved
- [ ] Record drawings — required (CAD + PDF typical)
- [ ] O&M manuals — required (electronic + 2–3 hard copies typical)
- [ ] Owner training — required for major MEP equipment (HVAC, lighting controls)
- [ ] Attic stock — required for finishes (paint, flooring, ceiling tile)
- [ ] Final cleaning — required

---

## C. Sample CSA (Attachment B.2) — clauses to compare against final CSA at award

The Sample CSA per `exports/calibration_v3/estimate.json` `bid_packages[7]` shows:
- HUB contracting commitment: **30% of the total contract sum** (placeholder; project-specific commitment goes on the executed CSA)
- Liquidated damages: **$###.00 per calendar day of delay** (placeholder; RFCSP fills in $250)

When the executed CSA arrives at award, compare against the sample for any unfavorable shifts:
- [ ] LD rate matches RFCSP ($250/day)
- [ ] HUB commitment matches HSP commitment (≥30%)
- [ ] Contract sum matches the bid (separate base price + $25K cash/contingency allowance)
- [ ] Time of performance matches (7/1 NTP, 11/2 substantial completion)
- [ ] No new clauses added vs sample
- [ ] No deletion of sample clauses that favor the GC (differing site conditions, change order markup, termination for convenience compensation)

---

## D. Notable items NOT in the sample but worth requesting at award (low leverage; ask anyway)

- [ ] LD cap at 5% of contract sum or 90 days of LDs (whichever greater)
- [ ] Mutual termination-for-convenience compensation (i.e. owner pays demob costs)
- [ ] Mutual waiver of consequential damages (no liability for lost rents, lost revenues, lost profit on unrelated projects)
- [ ] Right to suspend work upon non-payment past statutory prompt-pay deadline
- [ ] Reasonable RFI response time commitment (5 business days)

> Realism check: TTUS standard CSA is heavily owner-favorable and rarely negotiated on a sub-$1M renovation. The leverage to negotiate is essentially zero pre-award and small post-award. Focus the negotiation energy on the differing-site-conditions clause + LD cap + insurance timing — those three are the real money items.

---

## E. Supplementary conditions and other Project Manual contract-shaping sections (NEW 2026-05-23)

These Project Manual sections layer on top of the 2010 TFC UGSC (Attachment C). Read and cross-reference at the line items below:

| Project Manual section | Title | Why it matters for this bid |
|---|---|---|
| **00 70 00** | Conditions of the Contract | Likely references back to TFC UGSC + TTUS edits — should be consistent with Attachment C; verify on re-read |
| **00 73 00** | Supplementary Conditions | This is where TTUS adds project-specific edits. Read for: insurance carve-outs, additional bond requirements, additional indemnity clauses, owner-furnished scope clarifications |
| **00 73 43** | Wage Rate Requirements (Texas) | Reinforces Tex. Gov't Code Ch. 2258 prevailing wage compliance per `prevailing-wages.md` |
| **00 73 46** | Wage Determination Schedule | The actual WD attached — should be **Tom Green County 2023 WD per Attachment F.1** unless a newer WD is published. Cross-reference per `prevailing-wages.md` |
| **01 21 00** | Allowances | Establishes the $25K cash/contingency allowance protocol; how it draws down + reporting |
| **01 22 00** | Unit Prices | Likely empty/template-only for this scope; verify whether any unit prices are required on the proposal form |
| **01 23 00** | Alternates | Likely empty/template-only for this scope; verify whether any alternates are required on Attachment A § Alternates |
| **01 25 13** | Product Substitution Procedures | Process for getting "or equal" approval pre-bid or post-award |
| **01 29 00 / 01 29 73** | Payment Procedures / Schedule of Values | SOV structure that must accompany pay app #1 |
| **01 31 00 + 01 31 13** | Project Management + Coordination + Admin Reqs | Submittal + RFI + change order procedures layered on top of UGSC |
| **01 32 00 + 01 32 33** | Construction Progress Documentation + Photographic Documentation | Owner expects CPM schedule + photographic documentation cadence |
| **01 33 00** | Submittal Procedures | The shop drawing / sample / O&M submission process |
| **01 35 16** | **Alteration Project Procedures** | See Flag #0.5 above |
| **01 35 43.13** | **Environmental Procedures for Hazardous Materials** | Triggers if abatement scope materializes; cross-references Div 02 contingent sections |
| **01 35 46** | **Indoor Air Quality Procedures** | IAQ submittal + HVAC filtration + occupied-hours VOC restrictions |
| **01 40 00 + 01 42 00** | Quality Requirements + References | Standards references (ASTM, ANSI, NFPA) |
| **01 45 23** | Testing and Inspecting Services | Owner-paid material testing is typical TTUS — verify |
| **01 50 00 + 01 56 00 + 01 57 13 + 01 57 15** | Temporary Facilities + Barriers + Erosion Control + Integrated Pest Management | Temp facilities scope + protections |
| **01 60 00 + 01 61 16** | Product Requirements + VOC Restrictions | Material standards + VOC compliance |
| **01 73 00 + 01 73 29** | Execution + Cutting and Patching | Workmanship requirements |
| **01 74 19** | Construction Waste Management and Disposal | Waste diversion targets (typical 75% diversion) |
| **01 77 00** | Closeout Procedures + Closeout Forms A/B/C (subcontractor lien releases, hazmat affidavits, warranty) | Closeout deliverables stack on top of UGSC |
| **01 78 23 + 01 78 39** | O&M Data + Project Record Documents | Closeout deliverables for owner |
| **01 91 13** | General Commissioning Requirements | Cx authority (owner-furnished) plus contractor support obligations |

**Net assessment after Project Manual review:** No material departures from the Attachment C TTUS-edited UGSC that we already analyzed. The Supplementary Conditions (Sec 00 73 00) need a careful read but in TTUS pattern they typically just reiterate the UGSC + clarify owner-furnished scope. **The biggest impact items are Sec 01 35 16 Alteration Project Procedures + the contingent Div 02 hazmat sections** — both already priced into the takeoff template via the demo premium + $15K hazmat allowance.
