# 08 — Contract-terms flags (UGSC + Sample CSA review)

> Sources:
> - Attachment C — 2010 TFC Uniform General Conditions as supplemented by TTUS, edited 09.07.2023 (`inbox/.../ESBD_516718_..._Attachment C - ...UGSC...pdf`)
> - Attachment B.2 — Sample Construction Services Agreement (`inbox/.../ESBD_516718_..._Attachment B.2 - Sample Construction Services Agreement.pdf`)
>
> The v3 extraction at `exports/calibration_v3/estimate.json` `bid_packages[7]` (CSA) and `bid_packages[10]` (UGSC) captured high-level summaries; the line-by-line clause analysis below requires reading the actual PDFs cover-to-cover before the proposal goes in. This document captures the **clauses worth highlighting** for negotiation leverage post-award and the **clauses that materially affect price** that must be priced into the bid.

---

## A. Top 3 contract-terms flags (the ones that matter most for pricing this bid)

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
