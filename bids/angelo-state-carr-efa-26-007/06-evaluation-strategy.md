# 06 — Evaluation strategy

> The RFCSP body publishes the actual evaluation factors + weights for the Carr EFA project. The v3 extract (`exports/calibration_v3/estimate.json` `bid_packages[4]`) summary did not surface them — we must read the RFCSP § Evaluation Criteria cover-to-cover tomorrow to lock the weights. Until then, this document is a strategy framework based on the standard TTUS member-institution RFCSP scoring pattern.

---

## A. What TTUS RFCSPs typically evaluate

Per Tex. Gov't Code Ch. 2269 (Texas's procurement statute for government building construction) and standard TTUS practice, RFCSP evaluation factors typically include:

| Factor | Typical weight range | What it measures | Where to source for our response |
|---|---|---|---|
| **Price** | 35–55% | Base proposal price (with the $25K cash/contingency allowance carried as a separate line) | `takeoff-template.json` once filled |
| **Past performance / qualifications** | 15–25% | Similar institutional / educational / performing-arts projects; references; key-personnel résumés | `[USER TO FILL]` |
| **Project understanding / technical approach** | 10–20% | Narrative covering schedule, sequencing, coordination, quality control, dressing-room-specific considerations, owner-furnished-scope coordination, CBORD coordination, ADA compliance approach | This document § E + `04-scope-of-work.md` |
| **Schedule** | 5–15% | Proposed completion (124-day window from 2026-07-01 NTP); ability to meet the 2026-11-02 substantial completion | `timeline.md` |
| **HUB / HSP compliance** | 5–15% **OR pass/fail** | Quality of the HSP submission and demonstrated GFE; sometimes scored separately (pass/fail responsiveness check) | `05-hsp-plan.md` |
| **Safety record / EMR** | 0–10% | EMR, OSHA-incident record, project-specific safety plan | `[USER TO FILL]` |

> **Action:** As soon as the RFCSP body is re-read tomorrow, replace the table above with the actual weights ASU/TTUS publishes. The strategy below assumes a typical 45/20/15/10/10 split (price / past-perf / technical / schedule / HUB) for a sub-$1M TTUS RFCSP until proven otherwise.

---

## B. Where we win

| Lever | Why it scores | What we need to do |
|---|---|---|
| **Right-sized GC for a $400K–$600K reno** | TTUS member institutions have experienced large GCs treating small renos as nuisance work — late, distracted, overhead-padded. A focused mid-size GC with educational / performing-arts experience scores well on technical approach and past performance. | Lead narrative with: "single-building interior renovations at TX higher-ed under $1M are our sweet-spot scope; here are 3 we've delivered on time and on budget." |
| **Performing-arts and theater-support experience** | The Carr EFA dressing-room scope has performer-specific UX (makeup-mirror lighting, costume storage, theater-friendly acoustics, hair/makeup chemical exhaust) that a general institutional GC may miss. | `[USER TO FILL: surface ≥1 performing-arts / theater / locker / dressing-room reno]`. If the firm has any prior TTUS or other TX higher-ed performing-arts work, lead with it. |
| **CBORD + AV/IT coordination depth** | The owner-furnished scope on this project is unusually broad. ASU's PM is going to be reading proposals for someone who has done CBORD-rough-in + owner-vendor coordination cleanly before. | Dedicate a section of the technical narrative to "Owner-Furnished Coordination" with a written demarcation table (lifted from `04-scope-of-work.md` § A) and a named coordination POC on our team. |
| **TTUS member-institution past performance** | Past-perf is the second-largest scoring factor and the easiest to differentiate on. | `[USER TO FILL: surface ≥3 similar projects — TTUS / UT System / TAMU System / other TX higher-ed]`. If the firm has any prior ASU work, lead with it (owner's experience with the firm is the single strongest signal). |
| **HSP plan strength + GFE binder** | HSP is typically scored or pass/fail; either way, a robust GFE binder reduces disqualification risk to near zero. The sample CSA carries a 30% HUB commitment placeholder — a HSP committing to ≥30% with documented GFE positions us well above the floor. | Per `05-hsp-plan.md`: start HUB outreach today; document every contact; aim HSP commitment at 30% of subcontracted dollars (above the 21.1% statewide floor). |
| **Schedule realism around the active-building constraint** | ASU values predictable completion over the absolute shortest duration. A bid that says "we'll hit 11/2/2026 substantial completion with these access-window risks accounted for" scores better than "60 days, no contingency." | Build the proposed schedule from the trade-sequencing in `04-scope-of-work.md`; bake in after-hours premium time + EHS shutdown windows + Carr EFA production-calendar coordination. |
| **Clean, error-free proposal package** | TTUS clerks reject technically responsive proposals on form mismatches, missing signatures, blank fields, mismatched legal names across CIQ / 1295 / W-9. | Use the checklist in `02-bid-prep-checklist.md` § F and run a 2-person QC pass before sealing the package. Double the QC on the HSP package (it's a separate sealed submission on a separate deadline). |

## C. Where we DON'T win (don't waste narrative on these)

| Lever | Why it doesn't move the needle |
|---|---|
| Federal certifications (SAM.gov, SBA 8(a), HUBZone, etc.) | This is TTUS state work — federal small-business status doesn't help in TTUS scoring. TX HUB status (firm's own, if applicable) is what matters. |
| Big-project past performance ($5M+, ground-up institutional) | TTUS wants to see the bidder has done **work like this** — interior renovation under $1M with strong MEP and coordination complexity. A $20M ground-up academic building reference signals "this contractor will treat us as a nuisance." |
| Long marketing biography of the firm | TTUS evaluators are FP&C construction PMs and HUB Operations reviewers — they read for technical substance, not branding. Keep the narrative tight. |
| Generic safety plan boilerplate | If safety is scored, it's scored on actual EMR + OSHA-incident history, not on the length of the safety plan. Submit a brief, project-specific safety plan that names dressing-room / active-building hazards (after-hours egress, plenum work, electrical lockout/tagout, dust containment for performer health, fire-alarm shutdown coordination). |
| Proposing a value-engineering deduct without owner request | TTUS RFCSPs accept alternates only when published in the RFCSP. Unsolicited VE proposals often get the bid disqualified for non-responsiveness. Park any VE ideas in a separate "Post-award discussion" cover letter, not the priced proposal. |
| Lowballing the price by >25% below median | TTUS / TX state procurement consistently treats >25% below-median bids as "non-responsible" and disqualifies. Aim for tight, not lowest. |

## D. Pricing strategy

- **Base lump-sum number.** Dominant scoring axis. Carry every assumption in `04-scope-of-work.md` § B explicitly; everything not in the drawings + specs should be either priced with a clear assumption or excluded with a clear assumption.
- **Cash/contingency allowance ($25,000).** Per Attachment A, this is a separate line item — do NOT roll it into the lump-sum, do NOT mark it up.
- **Unit prices.** TTUS RFCSPs sometimes request unit prices for common owner-directed change items (sq. ft. of additional flooring, additional door, additional outlet, additional fixture). When the RFCSP body is re-read, populate carefully — unit prices set the ceiling for change orders. Bid them at full retail (sub cost + your full GC markup), not stripped-down.
- **Alternates.** Bid only those the RFCSP / Attachment A list (the v3 extract shows none beyond the allowance — confirm against the actual PDF).
- **Markup discipline.**
  - Sub cost at face value (no shaving sub quotes to make the headline number)
  - General conditions priced from the 124-day construction window at the in-house rate
  - Bond + insurance loaded as a percentage of subtotal — typically 1.5% bond + 1.0% insurance combined for a sub-$1M TX state job
  - Contingency: **8% for a renovation with reasonable drawings; 12% if drawings are thin** (or if site walk doesn't happen). Default to 8% in `takeoff-template.json`.
  - Overhead: 10% typical
  - Profit: 5–7% typical for TX state institutional work
- **Don't over-shave to win.** TTUS rejects bids that are >25% below the median as "non-responsible" risk. The $500K published budget is a strong signal of the median; landing at $425K–$485K is competitive without flagging non-responsibility.
- **Show the $25K allowance in the price summary** as a separate line so the evaluator can see we read the form correctly.

## E. The narrative arc of the technical proposal

A TTUS RFCSP technical narrative is typically 10–15 pages. Suggested structure:

1. **Cover letter** — 1 page; references the solicitation, addenda received, key team, summary of price including the separately-priced $25K allowance
2. **Project understanding** — 1 page; restate the scope in our words; flag the assumptions in `04-scope-of-work.md`; explicitly identify the owner-furnished items list (the unusually broad demarcation is itself a qualification differentiator)
3. **Approach & sequencing** — 2–3 pages; tied to the schedule; calls out the coordination pain-points (active performing-arts building, CBORD rough-in, owner-furnished tech/cabling/equipment install, fire-suppression interface, ADA alterations standard)
4. **Owner-furnished scope coordination** — 1 page; dedicated section reciting the demarcation table from `04-scope-of-work.md` § A and naming a coordination POC on our team
5. **Team & key personnel** — 2 pages; bio + experience + recent similar project for the PM, super, and safety lead
6. **Past performance / references** — 1–2 pages; 3–5 similar projects with owner contact + scope + value + completion date; performing-arts or theater-support work surfaced if available
7. **HSP** — separate document (delivered Monday 6/8), but referenced in the narrative ("Our HSP, delivered per the RFCSP separate-submission schedule, commits to 30% HUB participation of subcontracted dollars, exceeding the statewide special-trade-construction floor and aligning with the TTUS sample CSA pattern.")
8. **Schedule** — separate exhibit (CPM Gantt or bar chart); referenced in the narrative; explicitly accounts for production-calendar constraints and EHS shutdown windows
9. **Assumptions & clarifications** — 1 page; explicit list of anything not in the drawings + specs that we've assumed (e.g. "we have assumed ~2,500 SF of dressing-room footprint based on the RFCSP scope description; final price subject to drawing-set verification" + "we have assumed no hazmat abatement pending ASU EHS survey")
10. **Safety plan + EMR letter** — separate exhibit
11. **Quality control plan** — short, project-specific; mention TAB report, punch-list close-out, owner training, record drawings, O&M manuals

## F. Open questions for the RFCSP body re-read

When the RFCSP body is re-read tomorrow, confirm:

- [ ] Published evaluation weights
- [ ] Whether the 2026-05-20 pre-response meeting was mandatory (if yes, our missed-meeting risk goes from "high" to "showstopper" — see `07-risk-register.md` R-01)
- [ ] Page-count limits on the narrative (TTUS sometimes caps at 10–15 pages)
- [ ] Whether sub list is required at proposal time or only at award
- [ ] Whether alternates beyond the $25K allowance are requested
- [ ] Whether unit prices are requested (and which units)
- [ ] Project-specific HUB goal (does it exceed the 30% sample CSA pattern?)
- [ ] Substantial-completion mechanism: is 2026-11-02 a fixed calendar date regardless of NTP slip, or "124 days from NTP"?
- [ ] Submission delivery address (the v3 extract did not pull it)
- [ ] HSP submission delivery address (may differ from proposal submission)
- [ ] Whether bonding paperwork (commitment letters) is required at proposal or only at award
