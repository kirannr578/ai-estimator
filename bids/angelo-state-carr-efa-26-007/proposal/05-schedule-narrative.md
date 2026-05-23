# Schedule narrative — Carr EFA Dressing Room Renovation (2026-05-23 refresh)

> Companion document to the CPM Gantt exhibit (separate; submitted as a printed exhibit with the proposal). This narrative explains the critical path, long-lead items, EHS shutdown windows, owner-furnished handoffs, and float strategy that the Gantt represents in bar-chart form.
>
> **Refresh basis (2026-05-23):** Critical-path long-lead items revalidated against the 796-page Project Manual TOC and the 38-sheet drawing set. New long-leads surfaced from the PM (porcelain tile T1/T2/T3 + mosaic T4, metal lockers, phenolic toilet partitions). Construction window per Addendum #1 deck slide 6 confirms ~120-day target.

---

## 1. Anchors

| Anchor | Date | Source |
|---|---|---|
| Solicitation 26-007 issued | 2025-10-22 (preliminary, per ESBD posting timestamp) | ESBD posting 516718 |
| Proposal due | **2026-06-05, 2:00 PM CST** | RFCSP cover |
| HSP due | **2026-06-08, 5:00 PM CST** | RFCSP § HUB Subcontracting Plan |
| Expected award notice | 2026-06-15 to 2026-06-22 | TTUS pattern, sub-$1M contract |
| Contract execution + bonds delivered | by 2026-06-30 | UGSC Art. 6 + typical 10-day window post-award |
| **Notice to Proceed (NTP)** | **2026-07-01** | RFCSP § Time of Performance |
| **Substantial completion (contract date)** | **2026-11-02** | RFCSP § Time of Performance |
| **Substantial completion (internal target)** | **2026-10-20** | Internal — 13 days of float against contract date |
| Final completion + final pay app | ~2026-12-02 | Typical 30 days after substantial completion |
| Warranty period start | 2026-11-02 | UGSC Art. 12 — runs 1 year from substantial completion |

The 124-day construction window from 2026-07-01 NTP to 2026-11-02 substantial completion is the binding constraint. **Liquidated damages of $250 / calendar day** start accruing on 2026-11-02. Per `../07-risk-register.md` R-02, we have backwards-planned with conservative phase durations rather than aggressively compressing — schedule predictability scores higher with TTUS evaluators than the absolute shortest duration.

## 2. Phase-by-phase durations (matched to `02-technical-approach.md` § 3)

| Phase | Weeks | Dates | Duration | Critical-path activities | Float days |
|---|---|---|---|---|---|
| **Phase 1 — Mobilization, protection, coordination** | 1–2 | 7/1–7/14 | 14 cd | Site mob, dust containment, CBORD kickoff, EHS protocol established, ALL long-lead submittals out the door | 0 (no slack — Week 1 deliverables drive Phase 5) |
| **Phase 2 — Demolition** | 3–4 | 7/15–7/28 | 14 cd | Strip dressing rooms to demising walls + structure; MEP demo coordinated with subs; hazmat abatement if triggered | 2 (light Phase 2 contingency for hazmat finds) |
| **Phase 3 — MEP rough-in** | 5–8 | 7/29–8/25 | 28 cd | HVAC ductwork, plumbing supply/waste/vent rough, electrical branch wiring, CBORD door prep, low-voltage pathway, in-wall inspections | 3 (Phase 3 slack for RFI churn) |
| **Phase 4 — In-wall + above-ceiling close-out** | 9–11 | 8/26–9/15 | 21 cd | Framing, blocking, fire-stopping, GWB, ceiling grid set, brick restoration | 2 |
| **Phase 5 — Finishes** | 12–14 | 9/16–10/06 | 21 cd | Flooring, paint, finish carpentry, millwork install (theater-grade), ACT, door/frame/hardware install | 0 (no slack — millwork lead drives this phase) |
| **Phase 6 — MEP trim + fire alarm + specialties** | 15–16 | 10/07–10/20 | 14 cd | Light fixtures, diffusers, plumbing fixtures, devices, lighting controls programming, FA, signage, accessories | 3 |
| **Phase 7 — TAB + commissioning + punch + owner training + substantial completion** | 17–18 | 10/21–11/02 | 13 cd | TAB report, controls commissioning, owner training, punch walk, substantial completion **target 10/20**, then 13 days of float to 11/2 | 13 (the float bank) |
| **Phase 8 — Close-out** | 19–22 | 11/03–11/30 | 28 cd | Final punch closure, record drawings, O&M, attic stock, final clean, final pay app | n/a (after substantial completion) |

**Total Phases 1–7: 125 calendar days from 7/1 to 11/3** — one day over the contract date — but the internal target is 10/20, banking 13 days of float against 11/2. Phase 8 close-out is per the warranty / retainage schedule, not the substantial completion clock.

## 3. Critical path

The critical path runs through three serial dependencies:

```
Long-lead submittals (Week 1)
    │
    ▼
Theater-grade millwork manufacture + delivery (10–14 weeks → land by Week 12)
    │
    ▼
Phase 5 finishes (Weeks 12–14) — millwork install is the last gate before Phase 6 starts
    │
    ▼
Phase 6 MEP trim (Weeks 15–16) — lighting fixtures depend on millwork being in place (for makeup-mirror LED frames)
    │
    ▼
Phase 7 TAB + commissioning + punch (Weeks 17–18)
    │
    ▼
Substantial completion 10/20 internal target → 11/2 contract date with 13 days float
```

**Any slip in Phase 5 finishes by more than 13 calendar days triggers the LD clock.** This is why Phase 1 long-lead submittals are non-negotiable in Week 1.

## 4. Long-lead items (gating activities)

| Item | Lead time | Order by | Land by | Risk if slipped |
|---|---|---|---|---|
| **Theater-grade millwork** (makeup vanities + LED-lit 24"x72" mirror surrounds per Drawings Addendum 1, costume storage) — PM Sec 06 41 16 + 08 83 00 | 10–14 weeks | Week 1 (7/8) | Week 12 (9/22) | Phase 5 cannot start; LD-trigger risk |
| **Sargent door hardware** — PM Sec 08 71 00 (specified series) | 8–14 weeks | Week 1 (7/8) | Week 12 (9/22) | Phase 5 finish/hardware install delayed; substitute Sargent-compatible cylinder via submittal if needed |
| **Theater-grade dimmable LED light fixtures + replacement of corridor fixtures relocated to Makeup Room 108 per Drawings Addendum 2** — PM Sec 26 51 00 | 6–8 weeks | Week 1 (7/8) | Week 10 (9/8) | Phase 6 MEP trim delayed |
| **HM frames + doors** — PM Sec 08 11 13 + 08 14 16 | 8–10 weeks | Week 1 (7/8) | Week 11 (9/15) | Phase 5 door install delayed |
| **HVAC equipment** (specified AHU/VAV + dampers per LEAF Engineers MEP sheets M001–M501) — PM Sec 23 (full division) | 8–12 weeks | Week 1 (7/8) | Week 10 (9/8) | Phase 6 HVAC trim delayed; commissioning delayed |
| **Porcelain floor + wall tile (T1 + T2 + T3 + T4 mosaic added per Drawings Addendum 2)** — PM Sec 09 30 00 | 6–8 weeks | Week 2 (7/14) | Week 11 (9/15) | Phase 5 flooring delayed |
| **Metal lockers** (contractor scope per PM Sec 10 51 13, contrary to earlier prep assumption) | 8–10 weeks | Week 1 (7/8) | Week 12 (9/22) | Phase 5 specialty install delayed |
| **Phenolic-core toilet partitions** (ADA-compliant, restrooms 1R9 + 1R10) — PM Sec 10 21 13.19 | 6–8 weeks | Week 2 (7/14) | Week 11 (9/15) | Phase 6 specialties delayed |
| **Shower receptors + valves** (two ADA shower receptors confirmed per Drawings Addendum 2) — PM Sec 22 40 00 | 6–8 weeks | Week 2 (7/14) | Week 11 (9/15) | Phase 6 plumbing fixture set delayed |
| **CBORD electric strikes + readers** (owner-furnished, we accept delivery) | n/a (owner-supplied) | Owner orders | Per owner schedule | Phase 6 cannot finish door install until strikes on site |

**Submittal turnaround target:** 14 calendar days from sub to A/E approval. If A/E response slips past 14 days, we escalate via Samuel Guevara.

## 5. EHS shutdown windows (require 2 weeks lead time per UGSC Art. 8)

| Utility | Required for | Typical duration | Coordination |
|---|---|---|---|
| Fire alarm system | FA device relocation (Phase 6) | 4–6 hours | ASU EHS — coordinate test/quiet period |
| HVAC | New air handler / VAV cutover (Phase 6) | 8 hours | ASU EHS — coordinate cutover with Carr EFA building manager; ideally a weekend |
| Electrical (sub-panel cutover) | Phase 5 final + Phase 6 trim | 2–4 hours per circuit | ASU EHS — schedule outside business hours |
| Water (plumbing tie-in) | Phase 3 rough + Phase 6 fixture trim | 2–4 hours | ASU Facilities — usually low-impact since dressing rooms are off main distribution |
| Sprinkler (FP is owner-furnished but coordinate access) | Phases 2–4 | Per owner's FP contractor schedule | Owner's FP contractor — we provide access only |

All shutdowns are requested ≥2 weeks in advance via written notice to Samuel Guevara per the UGSC Article 8 procedure. Shutdowns are batched where possible to minimize disruption to the active building.

## 6. Owner-furnished handoff schedule (the "demarcation in time" complement to the demarcation in space)

| Owner-furnished scope | Required from owner | When (week) | What we deliver |
|---|---|---|---|
| Owner's FP contractor on-site coordination | Sprinkler-head relocation per new ceiling grid | Phase 4 (Week 10) | Open ceiling, clean access, electrical lockout |
| CBORD device + programming schedule | Devices on site for install | Phase 6 (Week 16) | Door prep complete, low-voltage pathway terminated at reader, 120V/PoE pathway ready |
| ASU IT data cabling pulls | Cable + termination + jacks | Phase 6 (Week 16, after Phase 5 finishes close out) | Pathway open + ring & string + faceplate ready |
| ASU AV equipment install | AV equipment on site | Phase 6 → Phase 7 transition | Power + pathway in place, mounting blocking installed |
| ASU FF&E delivery | Furniture, costume racks, lockers if applicable | Post-substantial-completion (Week 19+) | Spaces clean, punch closed, ready for FF&E install |

These handoffs are tracked in the project's submittal/RFI log alongside our own deliverables.

## 7. Float strategy

**Internal target substantial completion 2026-10-20** banks 13 calendar days of float against the contract date of 2026-11-02 and the $250/day LD trigger. The float is intended for:

1. **Hazmat surprises in Phase 2** if ASU EHS survey is unfavorable (consume 2–5 days of float).
2. **Differing site conditions** discovered during demo or MEP rough-in — undersized existing electrical service, cast-iron DWV requiring transition fittings, surprise plenum obstructions (consume 2–5 days of float per finding).
3. **A/E RFI response delay** beyond 14 days (consume 1–2 days per delayed response).
4. **Long-lead item slip** beyond stated manufacturer lead time (consume 5–10 days if a long-lead lands 1 week late).
5. **Active-building access window narrowing** if Carr EFA's production schedule absorbs more daytime hours than assumed (consume after-hours premium labor, not float days, where possible).

If the 13-day float is exhausted by mid-Phase 5 (around 10/01), we escalate to Samuel Guevara via the UGSC Article 9 change-order procedure for a no-cost time extension. We do NOT silently absorb schedule slip into the LD-trigger window.

## 8. Schedule risk callouts (cross-reference to `../07-risk-register.md`)

| Risk | Schedule impact | Mitigation reflected in this schedule |
|---|---|---|
| R-02 — owner-furnished scope mis-priced | None on schedule if scope is correct; major on schedule if a scope item slips between owner and us at the wrong moment | Demarcation table reviewed at kickoff (Week 1); coordination POCs named in `03-project-team.md` § 4 |
| R-03 — existing-conditions surprises (hazmat, undersized MEP) | Up to 5 days per finding | Phase 2 has 2 days of slack; float bank has 13 days |
| R-06 — CBORD coordination friction | Up to 3 days at Phase 6 door install | CBORD kickoff in Week 1 |
| R-08 — Carr EFA active-building access | Up to 1 day/week of lost productive time during fall semester | After-hours premium labor budgeted in pricing; production calendar confirmed by Week 1 |
| R-09 — schedule slip past 11/2 | LD clock; $250/day | Internal target 10/20 with 13 days float |
| R-10 — fixed-date vs days-from-NTP substantial completion | If NTP slips, the LD clock still starts on 11/2 | Assumptions & Clarifications in `02-technical-approach.md` § 7 ties substantial completion to receiving NTP by 7/1 |
| R-12 — drawing-set thinness → RFI churn | 1–2 days per RFI delay beyond 14 days | RFI cadence in submittal log; 14-day target with escalation procedure |
| R-16 — Sargent lock supply chain | Up to 4 weeks if Sargent has supply constraints | Order Week 1; substitute Sargent-compatible cylinder series via submittal if needed |
| R-17 — theater-grade millwork lead | Up to 4 weeks if specialty manufacturer slips | Order Week 1; identify alternative manufacturers in submittal package; carry expedite fee in GCs |

## 9. Schedule deliverables with the proposal

Submitted with the proposal as separate exhibits:

1. **CPM Gantt** showing 124-day window with the 7 construction phases + Phase 8 close-out, critical path highlighted, long-lead items shown as separate procurement bars
2. **Long-lead item schedule** with order dates + manufacturer lead times + landing dates + critical-path impact
3. **EHS shutdown window plan** with the 5 shutdown types + required notice + estimated duration

Submitted post-award as a contract submittal:

4. **Baseline CPM schedule** per UGSC Article 8 — fully resource-loaded, fully cost-loaded, updated monthly
