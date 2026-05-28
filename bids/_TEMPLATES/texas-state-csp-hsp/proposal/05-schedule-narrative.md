# 05 — Schedule narrative + critical path

> **Page target:** 1 page narrative + 1 separate Gantt exhibit.
> **Baseline duration:** {{SC_DAYS}} calendar days Substantial Completion + 30 calendar days fixed window to Final Completion (per CSP §00 42 13) = **{{FC_DAYS}} calendar days total**. Bidder-chosen, scored at **10% of evaluation** per CSP §00 21 00 ¶11.2.
> **Critical-path items:** lab casework lead time (8–12 weeks). **NO fume hood** — Division 11 NOT USED in spec, so the 12–16-week fume-hood lead-time risk is OFF THE TABLE. EHS shutdown-window availability is a secondary constraint.

---

## A. Anchor dates (working assumption)

| Event | Assumed date |
|---|---|
| Proposal due to {{AGENCY_SHORT}} | {{DUE_DATE}}, {{DUE_TIME}} {{DUE_TIMEZONE}} |
| Public proposal opening | {{DUE_DATE}}, {{OPENING_TIME}} {{DUE_TIMEZONE}} |
| {{AGENCY_SHORT}} evaluation period | {{DUE_DATE}} to ~{{EVAL_PERIOD_END_DATE}} (typical 2–3 weeks for sub-$500K CSP) |
| Best-and-final / clarifications | ~{{EVAL_PERIOD_END_DATE}} to ~{{BAFO_WINDOW_END_DATE}} |
| Award notification (estimated) | ~{{AWARD_TARGET_DATE}} |
| Notice to Proceed (estimated) | ~{{NTP_WINDOW_START}} to ~{{NTP_WINDOW_END}} |
| **Substantial completion target** | NTP + **{{SC_DAYS}} calendar days** = ~{{SC_TARGET_DATE}} if NTP {{NTP_TARGET_DATE}} |
| Final completion + closeout | NTP + {{FC_DAYS}} calendar days = ~{{FC_TARGET_DATE}} |

**CSP confirmed (post-portal-pull {{PORTAL_PULL_DATE}}):** there is NO fixed Substantial Completion date in the CSP package. The proposer **chooses** the duration in CSP §00 42 13 (Substantial Completion calendar days from NTP). Final Completion is **fixed at 30 calendar days after Substantial Completion**. This is the **10%-weighted "Construction Time"** criterion. Shorter is better (more points) but only if defensible by a real Gantt; padded short durations get penalized in evaluation if {{AE_FIRM_NAME}} + {{MEP_FIRM_NAME}} flag the proposal as not credible.

---

## B. Phased schedule summary (backwards-planned from substantial completion)

> Calendar-day count from NTP. Adjust phase overlaps based on actual EHS shutdown-window availability and lab-utility cutover scheduling at preconstruction.

| Phase | Days | Calendar-day span (assumed NTP {{NTP_TARGET_DATE}}) | Key milestones |
|---|---|---|---|
| 0 — Preconstruction | 1–14 | {{NTP_TARGET_DATE}} to {{PHASE_1_START_DATE}} | Submittals, long-lead orders, EHS coordination, hazmat survey review |
| 1 — Demolition | 15–25 | {{PHASE_1_START_DATE}} to {{PHASE_1_END_DATE}} | Containment up; EHS shutdowns; selective demo; haul-off |
| 2 — Rough-in (MEP + framing) | 20–45 | {{PHASE_2_START_DATE}} to {{PHASE_2_END_DATE}} | Branch wiring; plumbing rough-in; HVAC mods; sprinkler relocation; in-wall inspections |
| 3 — Finishes (drywall, ceiling, paint, flooring, casework) | 40–70 | {{PHASE_3_START_DATE}} to {{SC_TARGET_DATE}} | GWB hang/finish; ACT install; paint; flooring; lab casework + tops; fixture set; electrical trim; low-voltage pathway termination + {{AGENCY_SHORT}} Tech Services cable pull |
| 4 — Closeout | 65–100 | {{PHASE_4_START_DATE}} to {{FC_TARGET_DATE}} | TAB report; fire alarm + sprinkler retest; punch list; final cleaning; O&M + training; EHS final sign-off; substantial completion + acceptance |

**Substantial completion: Day 70 (~{{SC_TARGET_DATE}}).**

(Detail per Phase: see `02-technical-approach.md` § B.)

---

## C. Critical path

The critical path runs through two sequential constraints (fume-hood eliminated by spec):

1. **Lab casework fabrication.** 8–12 weeks from approved shop drawings → delivered to site. Casework shop drawings must be submitted by Day 7 post-NTP, approved by Day 14, fabricated by Day 70, installed by Day 75. **This is the binding constraint** for our {{SC_DAYS}}-day Substantial Completion commitment. {{CASEWORK_SUB_FILE_REF}} specifics (pending re-share from {{PM_NAME}}) confirm whether (a) a single specified casework manufacturer is committed (binding to their lead time) or (b) competitive subs are allowed (~2 weeks of additional shopping float).

2. **EHS shutdown-window availability.** 2-week notice + 4-hour blocks for fire alarm, sprinkler, and shared-utility cutovers. EHS coordination starts at preconstruction; shutdown windows are scheduled by Day 14 for Phase 1 demo work. Asbestos handling per Spec 02 26 23 is procedural (no abatement scope unless EHS finds material in the room) — modest float is built in for hazmat-survey review.

Float: 30 calendar days between Day 70 Substantial Completion and Day 100 Final Completion — this is the CSP-fixed window per §00 42 13 and is used for punch list, TAB, EHS final clearance, O&M closeout, and minor finishes touch-up.

---

## D. Long-lead items (procurement plan)

Cross-reference `02-technical-approach.md` § E. Summary:

| Long-lead item | Lead time | Order target (days post-NTP) |
|---|---|---|
| Lab casework (per A2.1/A2.2 + {{CASEWORK_SUB_FILE_REF}}) | 8–12 weeks | Day 5 |
| Lab work tops (chem-resistant) | 8–10 weeks | Day 5 |
| ~~Fume hood~~ | — | **NOT IN SCOPE — Div 11 NOT USED** |
| Lab fixtures (faucets, gooseneck, eye-wash, safety shower) | 6–8 weeks | Day 10 |
| ~~Specialty doors~~ | — | **NOT IN SCOPE — Div 08 NOT USED** |
| LED lighting + controls per E1.2 | 4–6 weeks | Day 5 |
| HVAC diffusers / grilles + VAV retrim per M1.1 | 4–6 weeks | Day 5 |
| Recessed sprinkler heads (coord. with existing {{AGENCY_SHORT}} sprinkler vendor) | 2–4 weeks | Day 15 |

---

## E. Coordination dependencies (off the critical path but worth calling out)

| Dependency | Owner | Risk if late |
|---|---|---|
| {{AGENCY_SHORT}} EHS hazardous-materials clearance for {{PROJECT_NAME}} (per Spec 02 26 23) | {{AGENCY_SHORT}} EHS | Phase 1 demo slip; ~5–10 calendar days |
| EHS shutdown approval for fire alarm + sprinkler | {{AGENCY_SHORT}} EHS | Phase 2 + Phase 4 slip; ~3–5 calendar days each event |
| {{AE_FIRM_NAME}} RFI turnaround (assumed 5 business days) | {{AE_FIRM_NAME}} | Cumulative ~5–10 calendar days |
| {{MEP_FIRM_NAME}} ({{MEP_POC_NAME}}) RFI turnaround (assumed 5 business days) | {{MEP_FIRM_NAME}} | Cumulative ~5–10 calendar days |
| {{AGENCY_SHORT}} Technology Services cable pull window | {{AGENCY_SHORT}} TS | Phase 3 finishes hold; ~3–7 calendar days |
| {{AE_FIRM_NAME}} + {{MEP_FIRM_NAME}} submittal review (assumed 10 business days) | A/E | Phase 0 to Phase 2 hold |
| Lab equipment owner-furnished delivery (if OFCI) | {{AGENCY_SHORT}} | Phase 3 hold pending equipment receipt |
| {{CASEWORK_SUB_FILE_REF}} file (currently re-share pending from {{PM_NAME}}) | {{ISSUING_OFFICE}} PM | Day 5 casework order target slips |

---

## F. Schedule risks (cross-reference `../07-risk-register.md`)

| Risk | Schedule impact | Mitigation in this schedule |
|---|---|---|
| R-03 — hidden lab utilities | +5–15 calendar days if DI water / lab gas added post-bid (fume hood not in scope) | Float in Phase 3 |
| R-06 — thin drawing package, RFI churn | +5–10 calendar days cumulative | 5-day RFI cadence; PM staffing buffer; {{MEP_FIRM_NAME}} + {{AE_FIRM_NAME}} both available |
| R-07 — after-hours work premium | Schedule impact neutral (work happens off-hours); cost impact only | Already priced |
| R-08 — existing-conditions surprises (asbestos finding) | +5–15 calendar days | Asbestos handling per Spec 02 26 23; modest allowance + float in Phase 1 |
| R-11 — Substantial Completion slip | Per {{ISSUING_OFFICE}} UGSC Article 9 (Time of Performance) liquidated damages | Defensible {{SC_DAYS}}-day baseline; 30-day fixed Final Completion window absorbs minor slips |
| R-12 — A/E RFI slow | +5–10 calendar days | Establish 5-day cadence at kickoff; escalate to {{PM_NAME}} + Cherise Toler on slip |
| R-NEW — {{CASEWORK_SUB_FILE_REF}} missing | +2 weeks on casework order if not re-shared in next 7 days | Outreach to {{PM_NAME}} (see `../outreach/01-...md`) requesting Zscaler-blocked file |

---

## G. Schedule exhibit

A separate Gantt chart exhibit (`exhibit-G-1-gantt.pdf` or similar; tool-agnostic — MS Project, Smartsheet, or hand-drawn) must accompany this narrative. The Gantt shows:

- Calendar-day axis from Day 1 (NTP) to Day 100 (final completion)
- One swimlane per trade
- Critical path highlighted (casework + fume-hood-if-scope)
- Phase boundaries at Day 14, Day 25, Day 45, Day 70, Day 100
- Long-lead procurement bars (typically off-site, shown as separate row)
- EHS shutdown windows shown as red event markers
- Owner-decision points (submittal approval, RFI responses, lab equipment delivery if OFCI) shown as diamond markers
- Substantial completion and final completion shown as flag markers

`[USER TO FILL: produce the Gantt in MS Project or Smartsheet, export to PDF, attach as Exhibit G-1.]`
