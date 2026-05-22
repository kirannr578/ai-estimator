# 07 — Risk register

> Risks specific to this bid + this opportunity. Each row: risk → impact → likelihood → mitigation → owner → status.
>
> Scoring: Impact (1–5) × Likelihood (1–5) = Score. Anything ≥ 12 is a top-tier risk that needs an explicit mitigation tracked to closure.

---

## A. Top-tier risks (score ≥ 12)

### R-01 — CSP package not pulled in time

- **Impact:** 5 — Without the CSP package, we cannot price, cannot complete the HSP, cannot meet the submission deadline.
- **Likelihood:** 3 — The portal access via e-Builder is public per the Notice link, but vendor-portal hiccups (registration gates, expired links) are common.
- **Score:** 15
- **Mitigation:**
  - Today: hit the e-Builder Public Landing link from the Notice. If it returns or requires registration, register and log a screenshot.
  - Today: email Joelle Shidemantle requesting confirmation that the CSP package is downloadable and asking for direct file links if portal access is friction-y.
  - 2026-05-23 escalate to Patty Winkler (HUB Ops) if Joelle hasn't responded, since HUB Ops has separate visibility into the CSP package timing.
  - 2026-05-26 final escalation: TAMU System Office of Facilities Planning & Construction if both contacts are silent.
- **Owner:** `[USER TO FILL: bid-prep lead]`
- **Status:** Open

### R-02 — Missed pre-proposal meeting (2026-05-14) may be mandatory

- **Impact:** 5 — If the pre-proposal meeting was mandatory and the CSP package treats attendance as a condition of proposing, our bid is non-responsive on its face.
- **Likelihood:** 2 — Most TAMU System CSP pre-proposal meetings are "highly recommended" rather than mandatory; the Notice does not say "mandatory." But some are.
- **Score:** 10 (just under top-tier; treating as top-tier given the binary outcome)
- **Mitigation:**
  - Today: email Joelle and ask explicitly: "Was the 5/14 pre-proposal meeting mandatory for proposers? If not, can a firm that did not attend still submit a responsive proposal?"
  - Request the sign-in sheet, recording, and Q&A from the meeting so we don't miss any project intelligence shared at the meeting.
  - If mandatory: surface this immediately to the user; either withdraw from this bid OR confirm with Joelle whether late-arrivers are accommodated (rare, but possible if Joelle didn't get a quorum at the meeting).
- **Owner:** `[USER TO FILL]`
- **Status:** Open — confirmation pending

### R-03 — Hidden lab utilities scope (DI water, lab gas, fume hood, acid waste)

- **Impact:** 4 — Each of these is a 5-figure scope adder if present and not bid. Multiple of them stacked could push the bid 25%+ over our envelope.
- **Likelihood:** 4 — The Notice says "lab utility coordination" and "science classroom/lab" — there's likely *something* beyond a plain classroom. The question is how much.
- **Score:** 16
- **Mitigation:**
  - Site walk request to Joelle/Patterson — see Lab 303 first hand.
  - When CSP package arrives, read the MEP drawings and lab equipment schedule line-by-line before pricing.
  - Engage a lab-experienced MEP sub early in pricing (lab subs know what to look for that a general MEP sub would miss).
  - Carry a `Lab Utilities` allowance of $15K–$30K in the base price, plus a unit-price line for additional outlets / fixtures.
- **Owner:** `[USER TO FILL: estimator]`
- **Status:** Open — pending drawings

### R-04 — HSP good-faith-effort documentation gap

- **Impact:** 5 — HSP GFE failures are the #1 cause of TAMU System CSP non-responsiveness rejections.
- **Likelihood:** 3 — Common pitfall; well-mitigated by starting outreach early and documenting everything.
- **Score:** 15
- **Mitigation:** Per `05-hsp-plan.md`:
  - Start HUB sub outreach today (CMBL search + email-blast to 3+ HUB subs per major trade).
  - Maintain a dated GFE log (`local/hub-outreach-log.csv` — gitignored).
  - Publish a HUB-targeted ad in 2+ approved publications by 2026-05-28.
  - Internal HSP review on 2026-06-03 with a second-set-of-eyes reviewer who has done TAMU System HSPs before.
- **Owner:** `[USER TO FILL]`
- **Status:** Open

### R-05 — Bonding capacity / lead time

- **Impact:** 4 — If bonding agent can't issue a bid bond or P&P commitment by 2026-06-08, we miss the bid.
- **Likelihood:** 2 — Most bonding agents turn around a single-project bond commitment in 3–5 business days for a known client.
- **Score:** 8 (just below top-tier; including here because the lead-time risk grows if the price moves)
- **Mitigation:** Notify bonding agent today of the bid (~$250K envelope); reserve capacity. Pass updated final number 2026-06-04. Bond paperwork in hand by 2026-06-08.
- **Owner:** `[USER TO FILL: insurance/bonding broker]`
- **Status:** Open

---

## B. Mid-tier risks (score 6–11)

### R-06 — Thin drawing package from Patterson Architects

- **Impact:** 3 — More RFIs during construction → schedule risk, change-order disputes.
- **Likelihood:** 3 — Small A/E firms often produce thinner packages than national firms.
- **Score:** 9
- **Mitigation:** Carry an extra ~5% RFI churn in PM hours within general conditions; document assumptions explicitly in the Assumptions & Clarifications section of the proposal.

### R-07 — Occupied building / after-hours work premium

- **Impact:** 3 — After-hours labor is typically 1.25–1.5× day rate.
- **Likelihood:** 4 — Almost certain for a renovation in an active academic building.
- **Score:** 12 (top-tier-adjacent)
- **Mitigation:** Confirm with Joelle the working-hours envelope (typical TAMU campus: 7 AM – 5 PM weekdays for noisy work, with shutdown coordination required). Price the demo + any HVAC / sprinkler shutdown work at premium rates. Build the schedule around constrained working windows.

### R-08 — Existing-conditions surprises (hazmat, deteriorated substrate, hidden lab utilities)

- **Impact:** 4
- **Likelihood:** 2 (per-event, but cumulatively higher across categories)
- **Score:** 8
- **Mitigation:** Request TAMU EHS hazmat survey for Bldg 0435; carry a `Hazmat / Existing-Conditions` allowance in the proposal if a survey isn't available; explicit assumption in proposal narrative.

### R-09 — Brazos County prevailing wage labor cost not in our internal labor rates

- **Impact:** 3 — If our labor cost basis is sub-prevailing, we'll be on the wrong side of the labor-burden math.
- **Likelihood:** 2 — Most TX commercial GC labor rates are at or above prevailing wage, but worth confirming.
- **Score:** 6
- **Mitigation:** Pull the Brazos County prevailing wage from the CSP package when it arrives; cross-check against the labor rates baked into the cost DB. Adjust if needed.

### R-10 — TAMU SGC insurance limits higher than firm's currently-carried limits

- **Impact:** 3 — Increasing limits mid-bid is possible but takes 5–10 days; if Umbrella needs to move from $2M to $5M, that's a real meeting with the broker.
- **Likelihood:** 2
- **Score:** 6
- **Mitigation:** Confirm broker can ride to $5M Umbrella + $1M / $2M GL + $1M Auto + statutory WC immediately. Note the carrier-quoted premium add as a one-line bid adder if it materially shifts.

### R-11 — Schedule slip on the substantial-completion target

- **Impact:** 3 — TAMU SGCs commonly carry liquidated damages (ASU CSA template lists "$###.00 per calendar day" as a placeholder; typical TAMU SGC LDs run $500–$1,500/day for sub-$1M projects).
- **Likelihood:** 3 — Lab renovations slip on plenum / EHS coordination more often than not.
- **Score:** 9
- **Mitigation:** Conservative duration in the proposal (60–90 days minimum, depending on scope confirmation). Float on the critical path. Explicit assumption that EHS shutdown windows are available within 2 weeks of request.

### R-12 — Patterson Architects / SSC PM RFI response time slow

- **Impact:** 3
- **Likelihood:** 3
- **Score:** 9
- **Mitigation:** Establish a written RFI cadence at the kickoff meeting (target: 5 business day response); track in a project log; escalate to Joelle if responses slip past 7 days.

---

## C. Low-tier risks (score ≤ 5)

| ID | Risk | Score | Mitigation |
|---|---|---|---|
| R-13 | Email typo for Joelle (`Shidementle` vs `Shidemantle`) causes bounce | 2 | Try both addresses; call to confirm |
| R-14 | TAMU project-specific HUB goal exceeds 21.1% | 4 | Pull goal from CSP package; adjust HSP commitment up if needed |
| R-15 | Texas HB 1295 filing window slips past submission | 2 | File the 1295 certification by 2026-06-05 if applicable |
| R-16 | Proposal package not delivered on time due to last-minute courier issue | 4 | Hand-deliver 2026-06-09; arrive at SSC Service Solutions ≥30 min before 2:00 PM CT on 2026-06-10 |
| R-17 | Calibration v3 extraction missed the e-Builder portal URL → someone might rebuild the workspace from the JSON and not have it | 1 | The URL is now in `01-overview.md` and `03-missing-documents.md`; future runs of the LLM pipeline should add NOP-class extractor logic to surface the document-acquisition URL |

---

## D. Risk-related blockers beyond "missing CSP package"

The user asked to flag any blockers beyond the obvious missing-CSP-package. These are the bid-level (not document-level) blockers:

1. **R-02 (pre-proposal meeting mandatory?)** — could be a hard go/no-go gate. Resolve in the first email to Joelle.
2. **R-03 (hidden lab utilities)** — pricing this bid responsibly without a site walk is hard. Recommend the user push for a site walk before final pricing.
3. **R-05 (bonding capacity)** — should be confirmed with the bonding agent before the user sinks more hours into this bid.
4. **HSP outreach must start TODAY** to be defensible at submission — this is a process-blocker, not a document-blocker.
5. **Internal go/no-go.** The user should make a deliberate go/no-go decision after R-01 / R-02 / R-03 / R-05 are resolved (target: end of day 2026-05-23). If any of those four come back negative, walk away early rather than burning estimator hours on a bid that can't be won responsibly.
