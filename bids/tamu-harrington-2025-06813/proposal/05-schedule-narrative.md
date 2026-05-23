# 05 — Schedule narrative + critical path

> **Page target:** 1 page narrative + 1 separate Gantt exhibit.
> **Baseline duration:** 70 calendar days substantial completion, 100 calendar days final completion + closeout. Subject to CSP-package adjustment.
> **Critical-path items:** lab-grade casework lead time (8–12 weeks); fume hood lead time (12–16 weeks, if in scope); EHS shutdown-window availability.

---

## A. Anchor dates (working assumption)

| Event | Assumed date |
|---|---|
| Proposal due to TAMU | 2026-06-10, 2:00 PM CT |
| Public proposal opening | 2026-06-10, 2:30 PM CT |
| TAMU evaluation period | 2026-06-10 to ~2026-06-30 (typical 2–3 weeks for sub-$500K CSP) |
| Best-and-final / clarifications | ~2026-06-30 to ~2026-07-10 |
| Award notification (estimated) | ~2026-07-15 |
| Notice to Proceed (estimated) | ~2026-07-25 to ~2026-08-01 |
| **Substantial completion target** | NTP + **70 calendar days** = ~2026-10-09 if NTP 2026-08-01 |
| Final completion + closeout | NTP + 100 calendar days = ~2026-11-08 |

`[PENDING e-BUILDER ACCESS: confirm if CSP package publishes a fixed substantial-completion date. The Notice gives a "Construction Period" range only; the CSP "Instructions to Proposers" typically pins a target. If the target is tied to an academic calendar window (e.g. "ready for spring 2027 semester" → late January 2027), our 70-day baseline has ample float; if the target is earlier than ~Oct 2026, we will need to compress via second-shift labor — reflected in unit-price line "shift premium."]`

---

## B. Phased schedule summary (backwards-planned from substantial completion)

> Calendar-day count from NTP. Adjust phase overlaps based on actual EHS shutdown-window availability and lab-utility cutover scheduling at preconstruction.

| Phase | Days | Calendar-day span (assumed NTP 2026-08-01) | Key milestones |
|---|---|---|---|
| 0 — Preconstruction | 1–14 | 2026-08-01 to 2026-08-15 | Submittals, long-lead orders, EHS coordination, hazmat survey review |
| 1 — Demolition | 15–25 | 2026-08-15 to 2026-08-26 | Containment up; EHS shutdowns; selective demo; haul-off |
| 2 — Rough-in (MEP + framing) | 20–45 | 2026-08-21 to 2026-09-15 | Branch wiring; plumbing rough-in; HVAC mods; sprinkler relocation; in-wall inspections |
| 3 — Finishes (drywall, ceiling, paint, flooring, casework) | 40–70 | 2026-09-10 to 2026-10-09 | GWB hang/finish; ACT install; paint; flooring; lab casework + tops; fixture set; electrical trim; low-voltage pathway termination + TAMU Tech Services cable pull |
| 4 — Closeout | 65–100 | 2026-10-05 to 2026-11-08 | TAB report; fire alarm + sprinkler retest; punch list; final cleaning; O&M + training; EHS final sign-off; substantial completion + acceptance |

**Substantial completion: Day 70 (~2026-10-09).**

(Detail per Phase: see `02-technical-approach.md` § B.)

---

## C. Critical path

The critical path runs through three sequential constraints:

1. **Lab-grade casework fabrication.** 8–12 weeks from approved shop drawings → delivered to site. Casework shop drawings must be submitted by Day 7 post-NTP, approved by Day 14, fabricated by Day 70, installed by Day 75. **This is the binding constraint for substantial completion** on most lab-room renos.

2. **Fume hood (if in scope).** 12–16 weeks from approved cut sheet → delivered to site. Order placement Day 1 post-NTP (assumes approved cut sheets), delivered by Day 90, installed by Day 95. `[PENDING e-BUILDER ACCESS: confirm whether fume hood is in scope]`. **If fume hood is in scope, this becomes the new critical path** and substantial completion moves to ~Day 100. We will flag this immediately on G2 close.

3. **EHS shutdown-window availability.** 2-week notice + 4-hour blocks for fire alarm, sprinkler, and shared-utility cutovers. EHS coordination starts at preconstruction; shutdown windows are scheduled by Day 14 for Phase 1 demo work.

Float: ~5 calendar days between Day 70 substantial completion and Day 100 final completion. This float absorbs punch-list completion + any minor closeout slips. If the fume-hood critical path is in play, this float shrinks; we will rebaseline at preconstruction.

---

## D. Long-lead items (procurement plan)

Cross-reference `02-technical-approach.md` § E. Summary:

| Long-lead item | Lead time | Order target (days post-NTP) |
|---|---|---|
| Lab-grade casework | 8–12 weeks | Day 5 |
| Phenolic / epoxy resin work tops | 8–10 weeks | Day 5 |
| Fume hood (if scope) | 12–16 weeks | Day 1 |
| Lab fixtures (faucets, gooseneck, eye-wash, safety shower) | 6–8 weeks | Day 10 |
| Specialty doors (if scope) | 8–12 weeks | Day 5 |
| Lab gas regulators + outlet trim (if scope) | 4–6 weeks | Day 10 |
| LED lighting + controls | 4–6 weeks | Day 5 |
| Recessed sprinkler heads | 2–4 weeks | Day 15 |

---

## E. Coordination dependencies (off the critical path but worth calling out)

| Dependency | Owner | Risk if late |
|---|---|---|
| TAMU EHS hazardous-materials clearance for Lab 303 | TAMU EHS | Phase 1 demo slip; ~5–10 calendar days |
| EHS shutdown approval for fire alarm + sprinkler | TAMU EHS | Phase 2 + Phase 4 slip; ~3–5 calendar days each event |
| Patterson Architects RFI turnaround (assumed 5 business days) | Patterson | Cumulative ~5–10 calendar days |
| TAMU Technology Services cable pull window | TAMU TS | Phase 3 finishes hold; ~3–7 calendar days |
| Patterson submittal review turnaround (assumed 10 business days) | Patterson | Phase 0 to Phase 2 hold |
| Lab equipment owner-furnished delivery (if OFCI) | TAMU | Phase 3 hold pending equipment receipt |

---

## F. Schedule risks (cross-reference `../07-risk-register.md`)

| Risk | Schedule impact | Mitigation in this schedule |
|---|---|---|
| R-03 — hidden lab utilities | +5–15 calendar days if fume hood or DI water added post-bid | Float in Phase 3; unit-price for shift premium if compression needed |
| R-06 — thin drawing package, RFI churn | +5–10 calendar days cumulative | 5-day RFI cadence assumption; PM staffing buffer in GCs |
| R-07 — after-hours work premium | Schedule impact neutral (work happens off-hours); cost impact only | Already priced |
| R-08 — existing-conditions surprises | +5–15 calendar days | Hazmat allowance + float in Phase 1 |
| R-11 — substantial-completion slip | LDs from `[PENDING e-BUILDER ACCESS: TAMU SGC LD rate]` | Conservative 70-day baseline; float in Phase 4 |
| R-12 — Patterson / SSC RFI slow | +5–10 calendar days | Establish 5-day cadence at kickoff; escalate to Joelle on slip |

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
