# Boilerplate — Closeout Plan

> **Use:** Closeout narrative in state CSP technical approach OR post-award submittal stub. Adapt the deliverable list per spec.

---

# Closeout Plan — {{PROJECT_NAME}}

## 1. Closeout philosophy

A successful project is one where the owner has **everything they need to operate the renovated space the day after final completion**: drawings reflecting what was built, manuals for every piece of equipment installed, warranties from every sub + vendor, training records for every operator, and a punch list that is empty — not deferred.

Blue Print Constructs starts closeout activities **at NTP, not at substantial completion**. Submittals approved during execution become the closeout binder. Daily QC reports become the QC turnover record. Sub agreements include closeout obligations as a condition of final payment.

## 2. Closeout milestones

| Milestone | Trigger | Owner |
|---|---|---|
| Substantial Completion request | Internal punch closed, building usable | BPC PM |
| Substantial Completion certification | Owner / A/E walk + acceptance | `{{AGENCY}}` + A/E |
| Owner punch list issued | At Substantial Completion walk | `{{AGENCY}}` + A/E |
| Owner punch list closed | Within `{{PUNCH_CLOSE_DAYS}}` cal days | BPC PM |
| Final Completion request | Owner punch closed, all closeout deliverables submitted | BPC PM |
| Final Completion certification | Final walk + acceptance | `{{AGENCY}}` + A/E |
| Final payment + retainage release | Final Completion + lien waivers + consent of surety | `{{AGENCY}}` Accounting |
| Warranty period begins | Substantial Completion date | — |
| 11-month warranty walk | At month 11 post-SC | BPC PM + `{{AGENCY}}` |
| Warranty closeout | At month 12 post-SC | BPC PM |

## 3. Closeout deliverables (compiled by BPC, turned over to owner)

| Deliverable | Format | Spec ref |
|---|---|---|
| As-built drawings (red-line + final electronic) | PDF + AutoCAD .dwg | per spec §01 78 39 typ |
| O&M manuals (per equipment item) | PDF binders | per spec §01 78 23 typ |
| Warranty letters (each sub + vendor) | PDF + signed originals | per spec §01 78 36 typ |
| Manufacturer training records (per system) | Signed training rosters + recording where requested | per spec §01 79 00 typ |
| Final test reports (air balance, electrical megger, hydrostatic, etc.) | PDF | per spec |
| Final special-inspection reports (third-party) | PDF | per spec §01 45 23 typ |
| Final inspection certificates from AHJ | PDF (occupancy / final electrical / final mechanical / final plumbing / final sprinkler / final fire alarm) | per spec + jurisdiction |
| Attic stock (extra paint, tile, ACT, flooring, hardware per spec) | Physical delivery + receipt | per spec |
| Keys (re-keyed cylinders, keying schedule) | Physical delivery + receipt | per spec §08 71 00 typ |
| Lien waivers — final unconditional (BPC + each sub tier) | PDF originals | per spec + contract |
| Consent of surety to final payment | PDF original | per surety + contract |
| Final pay application | per `{{AGENCY}}` form | per contract |
| Closeout-deliverables transmittal letter from BPC | PDF | BPC-generated |

## 4. Substantial Completion request — packet

Submitted to `{{AGENCY}}` + A/E 5 working days before requested walk-through date:

- Letter from BPC requesting Substantial Completion certification
- Statement that internal punch has been closed
- Updated CPM showing actual achievement of SC milestone
- Final QC log showing all NCRs closed
- AHJ inspection sign-offs for items required pre-occupancy (sprinkler, life-safety)
- Operating equipment in operating condition with O&M binders + warranty letters

## 5. Punch list discipline

- BPC internal walk first — generate internal punch, close before owner walk
- Owner walk → owner punch list issued in writing
- All punch items assigned to a sub (or BPC if self-perform) with due date
- Daily punch closure tracking; weekly punch status published
- Punch closed within `{{PUNCH_CLOSE_DAYS}}` cal days; back-charge any sub that does not close on time
- No final pay until punch is empty and signed off by owner

## 6. Training

For each system installed, BPC coordinates training for `{{AGENCY}}` Facilities staff:

- HVAC — controls, scheduling, alarm response, filter changes
- Electrical — panelboard layout, breaker assignments, lighting controls
- Plumbing — fixture access, valves, water-heater operation
- Specialty equipment — `[USER TO FILL — lab gas, eyewash, fume hood, lockers, etc. per project]`
- Doors / hardware — keying, access control, hardware adjustment

Training sessions are recorded (audio + video per `{{AGENCY}}` preference) and roster-signed. Training records become part of the closeout binder.

## 7. Warranty period

| Period | What's covered |
|---|---|
| **1-year general warranty (BPC + flow-down to subs)** | All workmanship + materials per AIA A201 §3.5 / federal contract / TX UGC Article 13 |
| **Extended warranties per spec** | Roofing, waterproofing, mechanical equipment, specialty equipment per mfr |
| **11-month warranty walk** | BPC + `{{AGENCY}}` walk-through to surface any items before 1-year general warranty expires |
| **Warranty closeout at 12 months** | Final warranty letter; sub warranty assignments to `{{AGENCY}}`; lessons-learned shared with `{{AGENCY}}` |

## 8. Sub closeout obligations (flowed down per BPC standard agreement)

Each sub agreement carries the following closeout obligations as a condition of final payment:

- Sub's portion of as-builts (red-line drawings reflecting their installed work)
- Sub's O&M manuals (manufacturer documentation)
- Sub's warranty letter (signed; flows to owner)
- Sub's training session for owner staff (if applicable to sub's scope)
- Sub's attic stock delivery (if specified)
- Sub's keys / access devices / passwords (if applicable)
- Sub's final lien waiver (unconditional)
- Sub's special-inspection reports for sub's scope (if applicable)
