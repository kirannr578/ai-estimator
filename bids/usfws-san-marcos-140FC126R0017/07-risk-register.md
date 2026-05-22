# 07 — Risk register

> Bid- and project-specific risks. Each: risk → impact → likelihood → mitigation → owner → status.
>
> Scoring: Impact (1–5) × Likelihood (1–5) = Score. Anything ≥ 12 is top-tier.

---

## A. Top-tier risks (score ≥ 12)

### R-01 — SAM.gov registration stale or NAICS 236220 not asserted as small

- **Impact:** 5 — A non-current SAM registration or wrong NAICS-size assertion makes the bid technically unacceptable on its face per L.1.0 + FAR 52.204-7. No award is possible.
- **Likelihood:** 3 — Annual Reps & Certs cycle is easy to let slip; many small firms don't catch the lapse until they're submitting a bid.
- **Score:** 15
- **Mitigation:** First action tomorrow morning — log in to SAM.gov and verify: Active status, UEI active, CAGE active, NAICS 236220 listed + small-asserted at $45M size standard, Reps & Certs updated within the past 12 months, EFT banking + TIN current. If any item is stale, fix today (3–10 business days to propagate). Hard cutoff for SAM-fix start: **2026-06-12** (10 business days before submission).
- **Owner:** `[USER TO FILL: contracts admin]`
- **Status:** Open — verification pending

### R-02 — Takeoff materially wrong (roof SF, gutter LF, heater count)

- **Impact:** 5 — At LPTA-thin margin, a 20%+ takeoff error wipes out the entire profit envelope and can push the project net-negative.
- **Likelihood:** 4 — No drawings, only photos + SOW text estimates; without site-visit measurements, error bars on roof SF are wide (estimated 2,000 SF could easily be 1,500–2,800 SF).
- **Score:** 20 — **highest single risk**
- **Mitigation:** Attend the **May 27 or May 28 site visit** with the full shopping list in `04-scope-of-work.md` § D. Measure roof footprint, eave + ridge heights, slope, panel profile, gutter LF, gas-pipe LF, heater count + capacity, fixture count. Get sub quotes for items 0001, 0005, 0006, 0007, 0008 from at least 2 vendors each. If site visit cannot be attended for any reason, raise the takeoff risk premium in the contingency from 3–5% to 8–10%; if that drives the bid above the magnitude ceiling, walk away.
- **Owner:** `[USER TO FILL: estimator + PM]`
- **Status:** Open — pending site visit

### R-03 — Section B Project Description error not clarified by RFI cutoff

- **Impact:** 4 — RFP Section B (pp.6–7) describes a different project (Pelican Island NWR, Vero Beach FL). If the CO doesn't issue an amendment correcting the description, an offeror could argue ambiguity post-award and any bid is at risk of protest from a competitor.
- **Likelihood:** 3 — COs often don't formally amend boilerplate errors if no offeror flags them, but with the CLINs themselves being correct, the CO may rely on the SOW to control.
- **Score:** 12
- **Mitigation:** Submit RFI #2/#3 (in `03-missing-documents.md` § E) to CO Drew Ferrall + Tracy Gamble before 2026-06-08. Push for a written amendment. If no amendment is issued, document in the proposal cover letter that "Section B descriptive text references a Pelican Island NWR project; offeror's bid is based on the San Marcos ARC CLINs 0001–0008 as published in the bid schedule and the SOW dated 02/19/2026."
- **Owner:** `[USER TO FILL: PM]`
- **Status:** Open — pending RFI submission

### R-04 — Differing Site Conditions on the roof substrate

- **Impact:** 4 — SOW §4.2.A.2 explicitly anticipates joist damage from water. A compromised joist requires structural repair before new roof goes on; if not flagged immediately under 52.236-2, contractor eats the cost.
- **Likelihood:** 3 — Older USFWS shop buildings frequently have wet-roof history.
- **Score:** 12
- **Mitigation:** Photograph any visible underside damage at the site visit. If joist damage looks likely, file a pre-submission RFI to confirm whether structural repair is in or out of scope. If it's out of scope and we win the award, **strict adherence to 52.236-2 written-notice procedure** the moment substrate damage is observed during demo: stop work, notify CO in writing within the contract's notice window, request equitable adjustment, do not proceed until CO concurs.
- **Owner:** PM + superintendent
- **Status:** Open

---

## B. Mid-tier risks (score 6–11)

### R-05 — Davis-Bacon wage rates not yet machine-readable

- **Impact:** 3 — If labor-rate basis is wrong, labor cost is mis-priced (could be either too high or too low depending on which trade is mis-coded).
- **Likelihood:** 3 — The attached WD PDF is extracted as garbled text in our tooling.
- **Score:** 9
- **Mitigation:** Open the PDF in a normal PDF reader and re-key the rates into `prevailing-wages.md`. Cross-check against SAM.gov's machine-readable WD page for TX20260254. Verify rates with the gas-licensed sub and the metal-roofing sub when getting quotes — they typically build DBA into their own pricing.
- **Owner:** PM
- **Status:** Open

### R-06 — Hazmat encountered during demo (asbestos / lead / transite)

- **Impact:** 4 — Asbestos in old transite panels or ceiling tiles can stop work for 5–15 days and add $5K–$15K abatement cost.
- **Likelihood:** 2 — USFWS shop buildings can be pre-1980 vintage; but the SOW says nothing about hazmat survey, suggesting the FWS doesn't expect it.
- **Score:** 8
- **Mitigation:** Photograph any suspicious materials at site visit. Document an assumption in the cover letter ("offeror assumes no asbestos, lead, or other hazardous materials are present in the work area; if encountered, will follow RFP H.12.0 + 52.236-2 written-notice and equitable-adjustment procedures"). If site visit reveals likely transite, raise an RFI before submission.
- **Owner:** PM + safety lead
- **Status:** Open

### R-07 — Long-lead OH doors push the schedule

- **Impact:** 3 — Custom-insulated overhead doors with chain-hoist can have 4–6 week manufacturing lead time. The 60-day NTP-to-completion is tight if order placement slips.
- **Likelihood:** 3 — Common in 2025–2026 supply chain.
- **Score:** 9
- **Mitigation:** Pre-clear preferred OH-door manufacturer + model with site visit; order submittal package the day after award; expedite if needed. Build the procurement risk into the schedule but NOT into the bid price (LPTA forbids contingencies).
- **Owner:** PM
- **Status:** Open

### R-08 — Bonding agent late on bid bond

- **Impact:** 5 — No bid bond = non-conforming bid.
- **Likelihood:** 1 — Most bonding agents turn around in 3–5 days for known clients.
- **Score:** 5 (just below mid-tier; including given the binary outcome)
- **Mitigation:** Place the bid-bond order on 2026-05-23 (one business day after this workspace lands). Confirm receipt by 2026-06-15 at the latest (1 week buffer before June 22).
- **Owner:** `[USER TO FILL: insurance/bonding broker]`
- **Status:** Open

### R-09 — 15% self-perform minimum not met

- **Impact:** 3 — If the firm subs out > 85% of the construction cost, 52.236-1 is violated; CO can disapprove.
- **Likelihood:** 3 — Easy to slip on a small project with 4–5 specialty subs.
- **Score:** 9
- **Mitigation:** Self-perform: PM/super (counts), site logistics, ceiling demo (CLIN 0003), and possibly personnel-door install (CLIN 0004) or gutter install (CLIN 0006). Document weekly in certified payroll. Aim for ~18–20% self-performed direct labor + supervision to leave buffer.
- **Owner:** PM
- **Status:** Open

### R-10 — Buy American non-compliance on roof panels or door panels

- **Impact:** 4 — 20% price differential added if foreign material; full disallowance if no determination requested in advance.
- **Likelihood:** 2 — Most US-made 24-ga roof panels and 20-ga steel OH doors are domestically manufactured; check the SKU specifically.
- **Score:** 8
- **Mitigation:** Specify domestic suppliers in submittals. If anything has to be non-domestic, file a 52.225-9 determination request with the CO BEFORE submitting the offer (52.225-10(b)). Submit a 52.225-4 Buy American Certificate with the proposal.
- **Owner:** PM + procurement
- **Status:** Open

### R-11 — Bidding below "unreasonably low" floor

- **Impact:** 4 — CO can deem the offer non-responsible per FAR 15.404-1(d) and reject.
- **Likelihood:** 2 — Magnitude is $100K–$250K; we recommend bidding $150K–$170K, comfortably above the floor.
- **Score:** 8
- **Mitigation:** Anchor pricing in named sub quotes + measured quantities. Build the bid bottom-up, not top-down. If raw direct cost + reasonable markup lands below $110K, that's a signal to re-check the takeoff for missed scope rather than to celebrate.
- **Owner:** Estimator
- **Status:** Open

### R-12 — Section B copy-paste error (Pelican Island) creates a protest vector for a losing competitor

- **Impact:** 3 — Even if our bid is the lowest and we Pass, a competitor could file a GAO protest arguing the RFP was defective per 4 CFR 21.2 (timeliness of pre-award protest is 10 days before bid open).
- **Likelihood:** 1 — Pre-award protest is unlikely; post-award protest on this basis is weak (the CLINs are correct).
- **Score:** 3 — low but worth flagging
- **Mitigation:** R-03 covers the upstream RFI. If awarded and protested, the prose-block error is in the RFP itself, not in our bid — the protest is against the CO, not us.
- **Owner:** PM (post-award)

### R-13 — Submission email goes to wrong address

- **Impact:** 5 — A bid that arrives at the wrong CO mailbox is treated as never received; binary lose.
- **Likelihood:** 2 — RFP gives two addresses (p.3 vs p.63). Sending to both reduces the risk dramatically.
- **Score:** 10
- **Mitigation:** Send to both `john_ferrall@fws.gov` AND `john_ferrall@ios.doi.gov` AND copy `Tracy_Gamble@fws.gov`. Send 30+ minutes early (4:30 PM EDT, not 4:59) to leave room for email-system delays. Use both Read Receipts and Delivery Receipts if email client supports.
- **Owner:** Contracts admin
- **Status:** Open

### R-14 — 60-day NTP-to-completion overrun

- **Impact:** 3 — RFP doesn't publish liquidated damages, but 52.249-10 (Default — Fixed-Price Construction) gives the government the right to terminate for default if completion slips. Practically, COs negotiate; but a default termination is the worst-case ding to past-performance.
- **Likelihood:** 3 — Tight schedule, multiple subs, weather risk in Texas (summer heat at 105°F can suspend roof work; named storms can move into June–July).
- **Score:** 9
- **Mitigation:** Realistic schedule: 14 days for submittals + procurement, 7 days for OH door + roof-panel delivery (parallel), 30 days for installation + closeout. Build the gas-line cap (CLIN 0005) early so the unit-heater removal (CLIN 0008) and roof work (which may need pipe penetrations re-flashed) can proceed. Use 52.211-13 + H.4 for unusually severe weather suspensions.
- **Owner:** PM
- **Status:** Open

---

## C. Low-tier risks (score ≤ 5)

| ID | Risk | Score | Mitigation |
|---|---|---|---|
| R-15 | Field Inspector name typo (Martinez vs Marinez) causes confusion at preconstruction | 2 | Cosmetic; confirm at preconstruction meeting |
| R-16 | RFI cutoff (June 8) passes without CO clarifying the Section B error | 4 | R-03 mitigation; document in cover letter regardless |
| R-17 | Hays County permit required for any work (very unlikely on federal land) | 2 | Confirm with FWS that federal jurisdiction obviates county building permit; standard for federal sites |
| R-18 | Texas Railroad Commission gas-licensure issue for the gas sub | 3 | Vet sub credentials before sub-quote acceptance; verify Texas RRC license active |
| R-19 | Existing electrical panel cannot support LED retrofit without new circuits | 2 | Site visit confirms; LED reduces load, so adding capacity is rare |
| R-20 | Buy American 52.225-9 documentation gap on a fastener / minor component | 2 | COTS fastener exemption per 52.225-9(b); document in submittal |
| R-21 | DOI / IPP enrollment delay post-award stalls first invoice | 3 | Enrollment instructions arrive 3–5 days post-award per G.4; coordinate with controller immediately after award |
| R-22 | Surety pulls capacity after seeing the Section B Pelican Island prose error | 1 | Explain context to surety; the underlying scope/bond is on San Marcos |
| R-23 | Past-performance reference unresponsive when CO calls | 3 | Notify the 2–3 reference contacts in advance that USFWS may call between June 22 and award |

---

## D. Risk-related blockers beyond "missing document"

The user asked to flag any blockers beyond the obvious missing-document set. These are the bid-level blockers:

1. **SAM.gov status (R-01)** — go/no-go gate. Resolve in the first hour tomorrow morning.
2. **Site-visit quantity confirmation (R-02)** — go/no-go gate for LPTA-thin pricing. Without the site visit, the contingency carry has to be wide enough to kill the win probability.
3. **Bonding capacity (R-08)** — should be confirmed with the bonding agent before the user sinks more hours into this bid.
4. **Internal go/no-go decision date — recommended end of day 2026-05-28** (after site visit). If R-01, R-02, R-04, or R-08 come back negative at that point, walk away rather than burning estimator hours through June 22.
5. **Compliance overhead vs. profit envelope** — at this magnitude with full federal compliance load (SAM maintenance, certified payroll, IPP, Buy American substantiation, FASCSA, DBA postings, weekly photos & reports, daily inspector's log), the firm's overhead burden on a $200K project may be > 12%. If the firm's standard OH is > 12%, this bid leaves no profit envelope at LPTA-thin pricing. Go/no-go pivots on this.
