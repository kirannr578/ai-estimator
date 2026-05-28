# 02 — Technical approach

> **Page target:** 2–4 pages when typeset.
> **Cross-references:** `../04-scope-of-work.md` (trade-by-trade), `../07-risk-register.md` (R-01..R-12), `05-schedule-narrative.md` (Gantt), `06-quality-control-plan.md` (3-phase QC), `07-safety-plan.md` (OSHA + EHS).

---

## A. Project understanding

The {{PROJECT_NAME}} is a **single-room renovation of an active educational laboratory space** at **{{SITE_ADDRESS}}, {{PROJECT_NAME}} site (Bldg #{{BUILDING_NUMBER}})** on {{AGENCY_SHORT}}'s {{AGENCY_SHORT}} campus. The project is designed by **{{AE_FIRM_NAME}}** (PA Project No. `[USER TO FILL: A/E project number]`, {{AE_FIRM_CITY_STATE}}) with MEP by **{{MEP_FIRM_NAME}}** ({{MEP_FIRM_CITY_STATE}}). Drawings are **Issued for Construction, dated {{DRAWING_DATE}}** — 10 sheets total (A0.1, A0.2 TAS, A0.3 TAS, A2.1 Floor Plans, A2.2 Ceiling Plan & Details, MEP1.0 MEP Specifications, M1.1 Mechanical Plan, E1.1 Electrical Demo, E1.2 Electrical Plans, P1.1 Plumbing Plans).

Our project understanding, post-portal-pull ({{PORTAL_PULL_DATE}}):

1. **Interior-only scope** — no structural modifications, no envelope work, no roof. Slab and overhead structure stay. Spec Divisions 03 (Concrete), 04 (Masonry), 05 (Metals), 31 (Earthwork), 32 (Exterior), 33 (Utilities) all explicitly **NOT USED**.
2. **Single room** — {{PROJECT_NAME}} only. Drawings cover only {{PROJECT_NAME}} in {{PROJECT_NAME}} site.
3. **Active-occupancy condition** — {{PROJECT_NAME}} site is an operating academic tower. Spec Section 01 41 00 "General Requirements for Renovation Work" (5 pp) governs renovation procedures; Section 01 50 00 (9 pp) governs temporary facilities. Adjacent rooms continue normal use during construction. Dust containment, vibration management, after-hours scheduling for noisy or odor-generating work, and {{ISSUING_OFFICE}}/{{AGENCY_SHORT}}-coordinated shutdown windows are required.
4. **No fume hood / no lab equipment in GC scope** — Spec Division 11 "Equipment" is **NOT USED**. The "lab" portion of the program is a teaching classroom-lab with lab sinks (per P1.1) but not a wet/heavy chemistry lab. This **rules out the high-tier price envelope** and substantially derisks the schedule (no 12–16 week fume hood lead time on the critical path).
5. **No new doors or hardware** — Spec Division 08 "Doors and Windows" is **NOT USED**. Existing classroom door, frame, and hardware remain.
6. **No casework spec in project manual; casework appears to be a deferred design or H2I sub-bid (Sub-06 file, posted 5/13 on the portal, currently blocked at our end by network policy — re-share requested via outreach 01).** Division 06 in the project manual is limited to 06 10 00 Rough Carpentry (5 pp). A casework allowance is carried in the price; refined upon H2I file retrieval.
7. **Asbestos handling is procedurally scoped** in Spec Section 02 26 23 (15 pp). We assume a clearance certificate is in place or that asbestos abatement, if encountered, proceeds per that procedure. A modest asbestos abatement allowance ($3K–$10K) is carried in the base bid.
8. **Owner-furnished items** — {{AGENCY_SHORT}} Technology Services furnishes and installs all low-voltage cabling, terminations, jacks, patch panels, and active gear. GC scope ends at the pathway (conduit, J-box, ring-and-string). AV equipment is OFOI per the typical {{AGENCY_SHORT}} pattern.

## B. Phased work plan (60–90 calendar days, single-shift baseline)

### Phase 0 — Pre-construction (NTP through Day 14)

- Notice to Proceed + contract execution (per {{ISSUING_OFFICE}} UGSC Section 00 72 00)
- Pre-construction meeting with {{ISSUING_OFFICE}} PM (`{{PM_NAME}}`, `{{PM_EMAIL}}`, `{{PM_PHONE}}`), A/E (Fred {{AE_FIRM_NAME}}, {{AE_FIRM_NAME}}), MEP (George, {{MEP_FIRM_NAME}}), {{AGENCY_SHORT}} EHS, {{AGENCY_SHORT}} Facilities, {{AGENCY_SHORT}} Technology Services
- {{AGENCY_SHORT}} EHS clearance review for Bldg {{BUILDING_NUMBER}} {{PROJECT_NAME}} per Spec Section 02 26 23 Asbestos Assessment procedure
- Submittal package per Spec Section 01 33 00 (3 pp) and 01 34 00 (9 pp Shop Drawings, Product Data and Samples): casework shop drawings (per H2I or alternate sub), lab fixture cut sheets, lighting cut sheets, low-voltage pathway routing, paint colors against {{AGENCY_SHORT}} finish standard, MEP shop drawings
- Long-lead order placement (see § E)
- Site logistics plan: dumpster placement ({{AGENCY_SHORT}}-approved location, coordinated with {{PM_NAME}}), loading-dock route, walk-off matting, dust-containment perimeter
- Site signage and life-safety walk

### Phase 1 — Demolition (Day 15–25)

- Establish negative-pressure dust containment at room perimeter; isolate corridor and adjacent-room HVAC returns
- EHS-coordinated 2-week-noticed shutdowns for: fire alarm devices in {{PROJECT_NAME}} (smoke detectors, strobes); sprinkler branch line serving {{PROJECT_NAME}}; any plumbing branches shared with adjacent labs
- Selective demolition: existing finishes (flooring + base, paint, ceiling tile), casework + countertops, fixtures slated for removal, lighting, MEP devices and rough-in
- After-hours scheduling for any noisy or odor-generating tasks (typically 5 PM – 11 PM weekdays, full-day Saturday/Sunday as agreed with {{PM_NAME}})
- Haul-off to {{AGENCY_SHORT}}-approved dumpster
- Phase 1 closeout walk with {{AGENCY_SHORT}} EHS, A/E, owner

### Phase 2 — Rough-in + MEP modifications (Day 20–45, overlap with Phase 1 end)

- Metal-stud framing for any new or furred partitions (if scope)
- Electrical rough-in: branch wiring for lab benches (dedicated 20A circuits, GFCI within 6' of any sink), classroom lighting controls (occupancy + daylight + dimming where applicable), low-voltage pathway (conduit, J-boxes, ring-and-string for {{AGENCY_SHORT}} Tech Services cable pull)
- Plumbing rough-in per P1.1: lab fixture supply + waste piping, eye-wash + safety shower rough-in (if shown on P1.1)
- HVAC modifications per M1.1 + MEP1.0: diffuser/grille relocation per new RCP (A2.2), VAV box retrim. **No fume hood scope** — Spec Division 11 NOT USED.
- Fire suppression: sprinkler head relocation per new ceiling layout. **No Div 21 spec or FP sheets in the package** — proceed via (a) deferred submittal proposed in this Technical Proposal, or (b) coordination with the existing {{AGENCY_SHORT}} building sprinkler vendor on T&M (NICET-certified) with EHS-coordinated shutdown windows.
- Inspections: in-wall electrical inspection, plumbing rough-in inspection, fire suppression hydrostatic test, framing inspection

### Phase 3 — Finishes (Day 40–70)

- Drywall hang + finish (level 4 typical for paint-grade) per Spec 09 22 00
- Acoustical ceiling grid + tile install per Spec 09 51 00 (full 2x4 lay-in replacement, per A2.2)
- Painting per Spec 09 91 00 (2-coat institutional latex, low-VOC)
- Resilient flooring install per Spec 09 65 00 (single spec — type per A2.1 finish plan)
- Resilient base
- Lab casework install (per A2.1/A2.2 details + {{CASEWORK_SUB_FILE_REF}} specifics once retrieved)
- Plumbing fixture set per P1.1 (lab sinks, faucets, eye-wash + safety shower if shown)
- Electrical trim per E1.2 (devices, plates, light fixtures, controls programming)
- Low-voltage pathway termination; {{AGENCY_SHORT}} Tech Services cable pull and termination
- **No new doors / hardware** — Division 08 NOT USED; existing door stays
- Specialties per Spec 10 14 00: room signage (ADA-compliant per A0.2/A0.3 TAS sheets)

### Phase 4 — Closeout (Day 65–90)

- Test, Adjust, Balance (TAB) report for HVAC per MEP1.0
- Fire alarm + sprinkler reconnect, full system test, EHS sign-off
- Punch list walk with A/E, {{ISSUING_OFFICE}} PM, {{AGENCY_SHORT}} Facilities per {{ISSUING_OFFICE}} UGSC Article 12
- Punch list completion per Spec Section 01 77 00 Closeout Procedures
- Final cleaning (lab-grade — no construction residue on bench tops)
- O&M manuals, attic stock, training per Spec Section 01 78 23 (Operation and Maintenance Data, 4 pp) + Section 01 78 20 (Facilities Management Data, 11 pp)
- As-built drawings
- {{AGENCY_SHORT}} EHS final clearance
- Substantial Completion + **30-day fixed Final Completion window** (per CSP §00 42 13); final payment + retainage release per {{ISSUING_OFFICE}} UGSC Article 10 + 12

## C. Lab-specific considerations (the pain-points worth pricing for)

This is the differentiator. Most GCs treat single-room labs like classroom finish work and then get burned on the lab utilities. We don't.

1. **Shared utility infrastructure with active adjacent labs.** {{PROJECT_NAME}} likely shares an exhaust stack, return-air plenum, lab-gas main, DI water riser, or acid waste branch with adjacent labs that remain in operation. Any cutover that affects an active adjacent lab requires PI-coordinated scheduling — often a single 4-hour window outside normal lab use. We will identify these shared systems in pre-construction and schedule cutovers explicitly.
2. **EHS shutdown windows.** Fire alarm, sprinkler, plenum work, and any plumbing branch tied to an active lab requires 2-week-noticed shutdown windows coordinated with {{AGENCY_SHORT}} EHS. We do not bid these as same-day-flex work; the schedule carries explicit shutdown-window placeholders.
3. **Hot-work permitting.** Soldering, brazing, welding, cutting in or around an active academic building requires {{AGENCY_SHORT}} EHS hot-work permits. We will incorporate the {{AGENCY_SHORT}} EHS hot-work procedure into our Phase 2 / Phase 3 plan.
4. **Legacy chemical contamination in existing dressing/lab spaces.** Older university lab rooms may have legacy chemical residue on bench tops, in sink traps, in fume hood interiors, or on the floor (mercury splashes, perchloric acid residue near old hoods). We will assume the room is **not** clear of legacy chemical residue and coordinate with {{AGENCY_SHORT}} EHS for any pre-demo wipe-down / clearance step. If {{AGENCY_SHORT}} EHS surveys the room and clears it, this allowance drops to zero.
5. **Ventilation isolation during demo.** Demo dust and odor cannot enter the adjacent-lab return-air plenum. We will install temporary plenum dampers or seal the existing return grilles in {{PROJECT_NAME}} throughout demo and rough-in. This is a typical missed scope item by inexperienced bidders.
6. **Lab equipment owner-furnished, contractor-installed (OFCI) vs owner-furnished, owner-installed (OFOI).** {{AGENCY_SHORT}} labs usually have a mix. Fume hoods and casework-mounted instruments are sometimes OFCI; balance tables and bench-top instruments are usually OFOI. Pre-construction submittal will explicitly enumerate this split per the lab equipment schedule `[PENDING e-BUILDER ACCESS: lab equipment schedule]`.
7. **{{AGENCY_SHORT}} Technology Services scope split.** GC scope ends at the low-voltage pathway. Cable, jacks, termination, patch panels, and active gear are {{AGENCY_SHORT}} Tech Services. We will coordinate Tech Services' cable pull window with our finishes phase to avoid ceiling re-opening after install.
8. **Lab fixture trim premium.** Lab fixtures (gooseneck spouts, lab-grade faucets, eye-wash bowls, integral fixture trim plates) cost roughly 50–80% more than commercial-grade fixtures. We have priced lab-grade fixture trim where the program calls for it; we have not assumed any "value engineer to commercial-grade" trim swap.

## D. Coordination with the academic calendar

The CSP package leaves Project Start and Substantial Completion as "TBD" — proposers select their own Substantial Completion duration in CSP Part 1 (Section 00 42 13), and this is scored at 10% of the evaluation per CSP §00 21 00 ¶11.2. Final Completion is fixed at 30 calendar days after Substantial Completion.

Our proposed duration: **{{SC_DAYS}} calendar days from NTP to Substantial Completion**, plus 30 calendar days to Final Completion ({{FC_DAYS}} calendar days total). See `05-schedule-narrative.md` for the trade-sequenced Gantt with EHS-shutdown windows and casework lead time built in.

Most likely academic-calendar windows:

- **Summer-to-fall window:** NTP early-to-mid June, Substantial Completion ~late-August (start of fall semester) — {{SC_DAYS}}-day commitment fits comfortably.
- **Fall-to-spring window:** NTP late October, Substantial Completion ~mid-January (start of spring semester) — {{SC_DAYS}}-day commitment fits with built-in holiday float.

## E. Long-lead items + procurement plan

| Item | Typical lead time | Order placement target | Risk if missed |
|---|---|---|---|
| Lab casework (per A2.1/A2.2 + {{CASEWORK_SUB_FILE_REF}} specifics) | 8–10 weeks fabricated; 10–12 weeks with custom configuration | Day 5 post-NTP | Schedule slip on Phase 3 finishes |
| Lab work tops (resin / chemical-resistant) | 8–10 weeks | Day 5 post-NTP | Same |
| Lab fixtures (faucets, gooseneck spouts, eye-wash + safety shower) | 6–8 weeks | Day 10 post-NTP | Manageable; carry stock alternates |
| LED lighting fixtures + controls per E1.2 | 4–6 weeks | Day 5 post-NTP | Manageable |
| Sprinkler heads (recessed, white-cover) — coordinated with existing {{AGENCY_SHORT}} sprinkler vendor | 2–4 weeks | Day 15 post-NTP | Minor |
| HVAC diffusers / grilles + VAV retrim per M1.1 | 4–6 weeks | Day 5 post-NTP | Manageable |

**No fume hood on critical path** — Division 11 NOT USED in spec → eliminates the historical biggest single-room lab schedule risk. The binding lead-time constraint is now casework (8–12 weeks), which sets the **earliest Substantial Completion at ~70 days** for a clean NTP-to-finishes sequence.

## F. Assumptions + clarifications

We submit this proposal subject to the following assumptions. If any prove false at the pre-construction meeting or during construction, the resulting scope adjustment will be handled per the change-order procedure in {{ISSUING_OFFICE}} UGSC Article 11 (Changes).

1. **Room area** measured from drawing A2.1 (`[USER TO FILL: actual SF after Bluebeam measure]`); price scaled accordingly.
2. **No structural modifications** — confirmed by spec (Divs 03–05 NOT USED).
3. **No envelope work** — confirmed by spec (Divs 31–33 NOT USED).
4. **Asbestos handling per Spec Section 02 26 23**, with a modest abatement allowance ($3K–$10K) in the base bid. If the room is fully cleared by {{AGENCY_SHORT}} EHS prior to NTP, the allowance returns to the owner via change order.
5. **Lab utility scope** per drawings (P1.1 plumbing, M1.1 mechanical, MEP1.0 specifications). **No fume hood** — Div 11 NOT USED. DI water / lab gas / acid waste / vacuum only if shown on P1.1 (carried per the takeoff).
6. **No new doors or hardware** — Division 08 NOT USED; existing door + frame + hardware remain.
7. **Casework scope** per A2.1/A2.2 details and the {{CASEWORK_SUB_FILE_REF}} file (currently pending re-share from {{PM_NAME}}); carried as a $20K–$60K allowance in the base bid pending {{CASEWORK_SUB_FILE_REF}} retrieval.
8. **Fire suppression** handled either as deferred-submittal (a) or via the existing {{AGENCY_SHORT}} building sprinkler vendor on T&M (b); modest allowance ($1K–$5K) in the base bid.
9. **Working-hours envelope** assumed to be 7 AM – 5 PM weekdays for routine work; after-hours (5 PM – 11 PM weekdays, Saturday and Sunday) for any noisy or odor-generating tasks. After-hours premium labor reflected in the base bid.
10. **EHS shutdown windows** assumed to be available within 2 weeks of request, in 4-hour blocks, with 2-week notice.
11. **{{AGENCY_SHORT}} Technology Services** furnishes and installs all low-voltage cabling, jacks, terminations, patch panels, and active gear. GC scope ends at the pathway.
12. **Substantial Completion** targeted at **{{SC_DAYS}} calendar days from NTP**; Final Completion + closeout at **{{FC_DAYS}} calendar days** (30-day fixed window per CSP §00 42 13).
13. **Owner-furnished items** assumed to include all lab instruments, balances, AV (projector, display, ceiling speakers, microphone arrays).
14. **{{AE_FIRM_NAME}} + {{MEP_FIRM_NAME}} RFI turnaround** assumed at 5 business days. Slower turnaround will be flagged.
15. **Proposal valid 90 calendar days** post-submittal per CSP §00 42 13.
16. **No bid bond required** (CSP §00 42 13 does not call for one). Performance + Payment bonds will be furnished at award per Spec Sections 00 61 13 + 00 61 14.
