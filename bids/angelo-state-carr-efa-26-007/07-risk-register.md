# 07 — Risk register

> Risks specific to this bid + this opportunity. Each row: risk → impact → likelihood → mitigation → owner → status.
>
> Scoring: Impact (1–5) × Likelihood (1–5) = Score. Anything ≥ 12 is a top-tier risk that needs an explicit mitigation tracked to closure.

---

## A. Top-tier risks (score ≥ 12)

### R-01 — Missed pre-response meeting (2026-05-20) may have been mandatory

- **Impact:** 5 — If the pre-response meeting was mandatory and the RFCSP treats attendance as a condition of proposing, our bid is non-responsive on its face.
- **Likelihood:** 2 — TTUS pre-response conferences are typically "highly recommended" rather than "required." But some are mandatory, particularly when the agency wants every bidder to have seen the site and asked the same questions.
- **Score:** 10 (treating as top-tier given the binary outcome)
- **Mitigation:**
  - **TODAY:** email Samuel Guevara: "Was the 5/20 pre-response conference mandatory for proposers? If not, can a firm that did not attend still submit a responsive proposal? Could you share the sign-in sheet, recording, and Q&A from the meeting?"
  - Follow up by phone within 24 hours if no email response
  - If mandatory: surface to user immediately. Options are (a) withdraw from this bid, (b) request waiver in writing from Samuel + Tracie Howell (rare but possible for a TTUS member institution if there wasn't a quorum at the original meeting), (c) hope for an addendum extending the deadline + adding a make-up meeting (also rare)
- **Owner:** `[USER TO FILL: bid-prep lead]`
- **Status:** Open — confirmation pending

### R-02 — Owner-furnished scope mis-priced (we double-bid or under-bid)

- **Impact:** 5 — The RFCSP lists technology, cabling, equipment install, furniture, AND fire suppression as owner-furnished. If we accidentally price any of these (e.g. include sprinkler-head relocation in our MEP sub's price), we're padded by 5–10% over competitors. If we accidentally exclude something we should have priced (e.g. CBORD rough-in pathway), we're under-bid and we eat the cost.
- **Likelihood:** 3 — Compounded by the fact that the owner-vs-contractor demarcation is in the RFCSP narrative only — the cleanest version of "where our scope ends and theirs starts" is in the drawings + spec book which we don't have yet.
- **Score:** 15
- **Mitigation:**
  - The contractor-vs-owner table in `04-scope-of-work.md` § A is the canonical demarcation; reconfirm in writing with Samuel before final sub-quotes go out
  - Brief every sub on the demarcation at quote time — "do NOT include sprinkler work, AV cabling, equipment install, furniture, or FF&E in your number"
  - When the drawings + specs arrive, do a dedicated read-through with the demarcation table open
  - In the proposal's Assumptions & Clarifications, restate the demarcation explicitly so any ambiguity is resolved at award rather than mid-construction
- **Owner:** `[USER TO FILL: estimator]`
- **Status:** Open — pending drawings + written confirmation from Samuel

### R-03 — Existing-conditions surprises (hazmat + 1960s/1970s-era MEP)

- **Impact:** 4 — Carr EFA is likely a 1960s–1970s building. Each of asbestos VCT/mastic/pipe insulation, galvanized water supply, cast-iron DWV with corroded transitions, undersized electrical service, and surprise plenum obstructions is a five-figure scope adder if present and not bid.
- **Likelihood:** 4 — TX higher-ed EFA buildings of that era almost always have at least one of these surprises.
- **Score:** 16
- **Mitigation:**
  - Push hard for a site walk via Samuel
  - Request ASU EHS hazmat survey for Carr EFA
  - When drawings arrive, look for existing-conditions notes + demo plans line-by-line
  - Carry an Existing-Conditions / Hazmat allowance of $10K–$25K in the base price (plus a unit-price line for additional abatement if RFCSP requests unit prices)
  - In the proposal's Assumptions & Clarifications, explicit assumption: "no hazmat abatement budgeted in base pending ASU EHS survey; abatement to be handled via the $25K cash/contingency allowance or change order"
- **Owner:** `[USER TO FILL: estimator]`
- **Status:** Open — pending site walk + EHS survey

### R-04 — HSP good-faith-effort documentation gap

- **Impact:** 5 — HSP GFE failures are the #1 cause of TX state RFCSP non-responsiveness rejections. Failure on HSP = automatic rejection of the proposal.
- **Likelihood:** 3 — Common pitfall; well-mitigated by starting outreach early and documenting everything.
- **Score:** 15
- **Mitigation:** Per `05-hsp-plan.md`:
  - Start HUB sub outreach today (CMBL search + email-blast to ≥3 HUB subs per major trade), with scope narrative if drawings aren't yet in hand
  - Maintain a dated GFE log (`local/hub-outreach-log.csv` — gitignored)
  - Publish a HUB-targeted ad in 2+ approved publications by 2026-05-27
  - Internal HSP review on 2026-06-03 with a second-set-of-eyes reviewer who has done TTUS HSPs before
  - HSP submission delivered Monday 2026-06-08 by 5 PM CST (separate sealed envelope from the proposal package)
- **Owner:** `[USER TO FILL]`
- **Status:** Open

### R-05 — HSP submitted after proposal deadline misses the Monday cutoff

- **Impact:** 5 — Proposal goes in Friday 6/5, HSP goes in Monday 6/8. If we accidentally treat them as a single package or if the HSP isn't ready by Friday's print run, we face a Monday-AM scramble.
- **Likelihood:** 2 — Mitigated by timeline awareness, but a real risk for a first-time TTUS bidder.
- **Score:** 10 (treating as top-tier given the binary outcome)
- **Mitigation:**
  - HSP target final-print: **COB Friday 2026-06-05** (same day as proposal submission)
  - Two-person QC pass on HSP separately from proposal QC
  - Delivery method confirmed with Samuel — confirm whether HSP goes to FP&C (same location as proposal) or to TTUS HUB Operations (different location)
  - Calendar block 2026-06-08 morning for HSP delivery + verification of receipt
- **Owner:** `[USER TO FILL]`
- **Status:** Open

---

## B. High-tier risks (score 9–11)

### R-06 — CBORD coordination friction

- **Impact:** 4 — If CBORD-specific door prep / pathway / power requirements aren't nailed down before we close subs, we get caught between the CBORD admin's requirements and what our hardware sub bid against.
- **Likelihood:** 3 — TTUS standardization on CBORD is well-known, but project-specific reader-side variants happen.
- **Score:** 12 (top-tier-adjacent)
- **Mitigation:**
  - In week 1 of construction (or earlier — try at site walk), schedule a coordination call with the CBORD system admin and our door-hardware sub + electrical sub
  - Carry a CBORD-coordination allowance of $1,500–$3,000 in GCs to absorb extra trips
  - Document the agreed pathway / power standards in writing and circulate to all affected subs

### R-07 — Bonding capacity / lead time

- **Impact:** 4 — If bonding agent can't issue a bid bond by 2026-06-05 OR P&P commitment by award, we miss the bid or the award.
- **Likelihood:** 2 — Most bonding agents turn around a single-project bond commitment in 3–5 business days for a known client. The ~$485K envelope is small.
- **Score:** 8 (just under top-tier; including here because the lead-time risk grows if the final price moves)
- **Mitigation:** Notify bonding agent today; reserve capacity against the ~$485K envelope. Confirm TTUS-required bid bond form is in their library. Pass updated final number 2026-06-03. Bid bond paperwork in hand and attached to proposal by 2026-06-05.

### R-08 — Active performing-arts building access friction

- **Impact:** 4 — If Carr EFA is hosting productions / rehearsals / classes during the 7/1–11/2 construction window, our access calendar narrows materially. Lost productive hours compound across a 124-day schedule.
- **Likelihood:** 4 — Carr EFA's fall semester (late August through December) is typically heavy with productions, recitals, finals.
- **Score:** 16 (top-tier — flag in mitigation paragraph)
- **Mitigation:**
  - **MOVED TO TOP-TIER MITIGATION:** Confirm with Samuel the production calendar for Carr EFA between 7/1 and 11/2
  - Bid the schedule assuming: no daytime noisy work during business hours during fall semester (8 AM – 5 PM weekdays); no work during scheduled productions (typically 7 PM – 11 PM); no work during dress rehearsals; coordinated access through ASU Facilities for after-hours
  - Carry after-hours premium labor (1.3–1.5× day rate) for at least 25% of the demo + MEP cutover work
  - Build float on the critical path; cushion the substantial completion target (avoid the LD trigger)

### R-09 — Schedule slip past 2026-11-02 → $250/day liquidated damages

- **Impact:** 4 — LD at $250/day for 30 days = $7,500. For 60 days = $15,000. Real dollars on a sub-$500K job.
- **Likelihood:** 3 — Renovations in active buildings slip on coordination more often than not.
- **Score:** 12 (top-tier)
- **Mitigation:**
  - Conservative duration in the proposal narrative (target substantial completion 2026-10-20 to bank 13 days of float against the 11/2 contract date)
  - Explicit assumption that EHS shutdown windows are available within 2 weeks of request
  - Internal weekly schedule review starting at NTP
  - Build a clear early-warning mechanism for any slip — request a 30-day notice extension via change order procedure if slip becomes likely (UGSC Art. 9)

### R-10 — Substantial-completion mechanism is fixed-date, not days-from-NTP

- **Impact:** 4 — If the LD clock starts against the fixed 2026-11-02 date regardless of any NTP slip, ASU can issue late NTP and we eat the schedule compression.
- **Likelihood:** 3 — TTUS sample CSA can carry either mechanism; user brief shows it as a fixed date which is consistent with the days-from-start interpretation (7/1 start + 124 days = 11/2).
- **Score:** 12
- **Mitigation:**
  - Read the RFCSP § Time of Performance + the CSA Art. (Time) clauses tomorrow to confirm whether the date is fixed or "X days from NTP"
  - If fixed: in the Assumptions & Clarifications, explicitly tie the substantial completion to receiving NTP by 2026-07-01 ± [USER TO FILL: acceptable variance]; negotiate at award if NTP slips
  - Include float per R-09

### R-11 — UGSC Art. 5 insurance limits exceed firm's currently-carried limits

- **Impact:** 3 — Increasing Umbrella from current to $5M+ is possible but takes 5–10 days; if Builder's Risk also needs to ride to GC-carried (rather than owner), that's a real meeting with the broker.
- **Likelihood:** 2
- **Score:** 6 (low-tier-adjacent; including here for visibility)
- **Mitigation:** Confirm broker can ride to all required limits in `02-bid-prep-checklist.md` § B immediately. Note the carrier-quoted premium add as a line in pricing if it materially shifts.

---

## C. Mid-tier risks (score 6–8)

### R-12 — Drawing set quality / completeness

- **Impact:** 3 — Thin drawings → more RFIs during construction → schedule + change-order risk
- **Likelihood:** 3 — TTUS member-institution renovation drawings vary widely by A/E firm
- **Score:** 9
- **Mitigation:** Carry RFI churn in PM hours within GCs; document assumptions explicitly in proposal Assumptions & Clarifications

### R-13 — Tom Green County prevailing wage rates have escalated since Attachment F.1 (dated July 2023)

- **Impact:** 3 — If our labor cost basis is sub-prevailing as escalated, we'll be on the wrong side of the labor-burden math by 6–10%
- **Likelihood:** 3 — 2.5 years of inflation since the WD was issued
- **Score:** 9
- **Mitigation:** Apply +6–10% labor escalation to the Attachment F.1 floor (see `prevailing-wages.md` § Escalation); request updated WD from TTUS if available; cross-check against Texas Workforce Commission's most-recent county survey data

### R-14 — TTUS HSP target exceeds 30% (sample CSA placeholder)

- **Impact:** 3 — Higher HUB target requires more aggressive sub-bid sourcing and reduces non-HUB bid leverage on price
- **Likelihood:** 2
- **Score:** 6
- **Mitigation:** Confirm project-specific HUB goal from RFCSP body when re-read; adjust per-trade allocation in `05-hsp-plan.md` § C if needed

### R-15 — Patterson-style small A/E firm = slow RFI response time

- **Impact:** 3 — Bottlenecks the construction schedule
- **Likelihood:** 3 — Unknown until A/E firm identity is confirmed
- **Score:** 9
- **Mitigation:** Establish a written RFI cadence at the kickoff meeting (target: 5 business day response); track in a project log; escalate to Samuel if responses slip past 7 days

### R-16 — Sargent lock supply chain lead time

- **Impact:** 3 — Sargent is named in the spec; if supply chain is constrained (post-2020 hardware supply has been volatile), delivery lead time can hit 8–14 weeks
- **Likelihood:** 2
- **Score:** 6
- **Mitigation:** Confirm Sargent lead time with distributor at sub-quote time; order long-lead hardware immediately on NTP receipt; carry an alternate Sargent-compatible cylinder series in the submittal

### R-17 — Theater-grade millwork (dressing-room makeup vanities with LED mirrors) lead time

- **Impact:** 3 — Theater-grade specialty millwork can have 10–14 week lead times
- **Likelihood:** 3
- **Score:** 9
- **Mitigation:** Order millwork submittal package within the first 14 days of NTP; identify alternative manufacturers in submittal package; carry expedite fee in GCs

---

## D. Low-tier risks (score ≤ 5)

| ID | Risk | Score | Mitigation |
|---|---|---|---|
| R-18 | Texas HB 1295 filing requirement if contract trips the $1M threshold (we're under, but borderline) | 3 | File the 1295 certification pre-emptively by 2026-06-03 to be safe |
| R-19 | Proposal not delivered on time due to last-minute courier issue | 4 | Hand-deliver 2026-06-04; arrive at ASU FP&C ≥30 min before 2:00 PM CST on 2026-06-05 |
| R-20 | HSP package delivered to wrong office (TTUS HUB Ops vs ASU FP&C) | 3 | Confirm delivery location in writing with Samuel by 2026-06-01 |
| R-21 | Calibration v3 phantom line items from `A1` (drawings extraction for an unrelated PDF) leak into the estimate | 1 | The 5 `06 10 00` line items in `exports/calibration_v3/estimate.json.line_items` are flagged `suppressed=True` and contribute $0; they are NOT carried into `takeoff-template.json` for this bid. Verified. |
| R-22 | Sample CSA HUB commitment (30%) is mis-extracted by v3 as the project-specific commitment | 2 | Confirmed in `01-overview.md` § 8 that the 30% is a sample CSA placeholder, not the project-specific commitment; HSP draft in `05-hsp-plan.md` § C targets ≥30% to align with TTUS pattern with margin |

---

## E. Bid-level (not document-level) blockers — for the user's go/no-go gate

The user asked to flag any blockers beyond the obvious missing-drawings. These are the bid-level blockers that should be resolved before the user sinks more estimator hours into this bid:

1. **R-01 (missed pre-response meeting was mandatory?)** — could be a hard go/no-go gate. Resolve in the first email + call to Samuel.
2. **R-02 (owner-furnished scope demarcation in writing)** — pricing this bid responsibly without a written owner-vs-GC scope demarcation is hard. Recommend the user request this in writing as part of the Samuel call.
3. **R-03 (hazmat survey + site walk)** — Carr EFA is old; without a site walk + hazmat survey, the existing-conditions allowance has to be generous which makes us less competitive.
4. **R-07 (bonding capacity)** — should be confirmed with bonding agent today.
5. **R-08 (production calendar)** — confirm with Samuel; if Carr EFA is heavily booked during the 7/1–11/2 window, the schedule becomes much tighter and the bid carries more after-hours premium.
6. **R-13 (prevailing wage escalation)** — confirm whether TTUS has a 2025/2026 prevailing wage update for Tom Green County before locking labor cost basis.
7. **HSP outreach must start TODAY** to be defensible at submission — this is a process-blocker, not a document-blocker.

**Internal go/no-go.** Make a deliberate go/no-go decision after R-01 / R-02 / R-03 / R-07 / R-08 are resolved (target: end of day 2026-05-25). If any come back negative, walk away early rather than burning estimator hours on a bid that can't be won responsibly.
