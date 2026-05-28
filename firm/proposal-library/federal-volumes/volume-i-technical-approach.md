# Volume I — Technical Approach

> **How to use this template** — Federal best-value tradeoff (FAR 15.101-1) Volume I. Target page count **8–12 pages** unless Section L specifies otherwise. Read Section M first; weight each subsection in proportion to that factor's weight in the evaluation criteria. This is the volume that wins or loses a tradeoff source selection — it must be specific to the project (no boilerplate that could equally describe any other RFP) and demonstrably tied to the SOW. Search-and-replace every `{{PLACEHOLDER}}`. Trim sections the RFP does not explicitly request.

---

# Volume I — Technical Approach
## {{PROJECT_NAME}} | Solicitation {{SOLICITATION_NUMBER}}
### Submitted by Blue Print Constructs (Blue Print Constructs, LLC dba) — UEI LM4YHVQ71QG7 • CAGE 9LET0

## 1. Project Understanding

### 1.1 Mission context

`{{AGENCY}}` requires `{{ONE_SENTENCE_MISSION_NEED}}`. The work at `{{SITE_NAME}}` directly supports `{{AGENCY_MISSION_LINK}}` — for example, `{{MISSION_EXAMPLE}}`. Successful delivery means `{{AGENCY}}` `{{MISSION_OUTCOME}}` on `{{REQUIRED_DATE}}`.

### 1.2 Scope summary (BPC's reading of the SOW)

In the words of the Statement of Work (SOW Section `{{SOW_SECTION_REF}}`), the Contractor shall:

> `{{KEY_SOW_QUOTE_1}}`
> `{{KEY_SOW_QUOTE_2}}`

Blue Print Constructs reads the scope as follows:

| SOW reference | Scope item | BPC's understanding | Critical interface |
|---|---|---|---|
| §`{{SOW_SECTION_1}}` | `{{SCOPE_ITEM_1}}` | `{{BPC_INTERPRETATION_1}}` | `{{INTERFACE_1}}` |
| §`{{SOW_SECTION_2}}` | `{{SCOPE_ITEM_2}}` | `{{BPC_INTERPRETATION_2}}` | `{{INTERFACE_2}}` |
| §`{{SOW_SECTION_3}}` | `{{SCOPE_ITEM_3}}` | `{{BPC_INTERPRETATION_3}}` | `{{INTERFACE_3}}` |

### 1.3 Site-specific drivers

The conditions at `{{SITE_ADDRESS}}` that drive the technical approach:

- **`{{DRIVER_1_TITLE}}`.** `{{DRIVER_1_NARRATIVE}}` — for example, an active-occupancy condition where `{{AGENCY}}` operations continue throughout construction requires dust-tight barricades, HEPA negative-air, and after-hours hot-work windows.
- **`{{DRIVER_2_TITLE}}`.** `{{DRIVER_2_NARRATIVE}}` — for example, a federal facility's badge-and-escort requirement adds 30–60 minutes per craft per day to the labor envelope.
- **`{{DRIVER_3_TITLE}}`.** `{{DRIVER_3_NARRATIVE}}` — for example, AHJ inspection scheduling lag in `{{COUNTY}}` County is typically 5–10 working days and is reflected in the CPM.

## 2. Technical Approach

### 2.1 Approach summary (theme statement)

Blue Print Constructs proposes to deliver `{{PROJECT_NAME}}` by `{{ONE_SENTENCE_APPROACH}}`. This approach reduces `{{KEY_RISK_AVOIDED}}` and ensures `{{KEY_BENEFIT_DELIVERED}}`, with substantial completion in `{{SC_DAYS}}` calendar days and final completion in `{{FC_DAYS}}` calendar days from Notice to Proceed.

### 2.2 Self-perform vs subcontracted work

Per FAR 52.236-1, BPC will self-perform a minimum of 15% of the construction Work. On `{{PROJECT_NAME}}`, BPC plans to self-perform `{{SELF_PERFORM_PCT}}%` of the contract value:

- **Self-perform** (BPC craft on site daily): `{{SELF_PERFORM_SCOPE_LIST}}` — typically GC supervision, selective demolition, drywall and finishes, paint, trim and casework install, light flooring, project closeout.
- **Subcontract** (vetted sub pool, see Volume II §3 and [`firm/proposal-library/boilerplate/subcontractor-management.md`](../boilerplate/subcontractor-management.md)): `{{SUB_SCOPE_LIST}}` — typically MEP, fire suppression, specialty equipment, site/civil if applicable.

### 2.3 Scope of work breakdown (CSI-aligned WBS)

| Division | Scope | Plan | Approx. % | Critical-path? |
|---|---|---|---|---|
| 01 — General Requirements | Mob, super, GR, dumpster, temp protection, OSHA program, QC plan, closeout deliverables | Self | `{{DIV_01_PCT}}%` | Throughout |
| 02 — Existing Conditions | Selective demo, pre-demo investigation, asbestos / lead clearance | Self + sub | `{{DIV_02_PCT}}%` | Yes (early) |
| 03 — Concrete | `{{DIV_03_DESCRIPTION}}` | `{{DIV_03_PLAN}}` | `{{DIV_03_PCT}}%` | `{{DIV_03_CP}}` |
| 04 — Masonry | `{{DIV_04_DESCRIPTION}}` | `{{DIV_04_PLAN}}` | `{{DIV_04_PCT}}%` | `{{DIV_04_CP}}` |
| 05 — Metals | `{{DIV_05_DESCRIPTION}}` | `{{DIV_05_PLAN}}` | `{{DIV_05_PCT}}%` | `{{DIV_05_CP}}` |
| 06 — Wood, Plastics, Composites | Casework, trim | `{{DIV_06_PLAN}}` | `{{DIV_06_PCT}}%` | `{{DIV_06_CP}}` |
| 07 — Thermal & Moisture | Roofing, sealants | `{{DIV_07_PLAN}}` | `{{DIV_07_PCT}}%` | `{{DIV_07_CP}}` |
| 08 — Openings | Doors, frames, hardware, glazing | `{{DIV_08_PLAN}}` | `{{DIV_08_PCT}}%` | `{{DIV_08_CP}}` |
| 09 — Finishes | Drywall, paint, flooring, ceilings, tile | Mostly self | `{{DIV_09_PCT}}%` | Yes (mid) |
| 10 — Specialties | Toilet partitions, signage, accessories | Sub | `{{DIV_10_PCT}}%` | `{{DIV_10_CP}}` |
| 11 — Equipment | `{{DIV_11_DESCRIPTION}}` (lab, kitchen, etc.) | `{{DIV_11_PLAN}}` | `{{DIV_11_PCT}}%` | `{{DIV_11_CP}}` |
| 21–23 — Fire / Plumbing / HVAC | Wet + dry MEP | Sub | `{{MEP_PCT}}%` | Yes (rough + trim) |
| 26 — Electrical | Power, lighting, low-voltage pathway | Sub | `{{DIV_26_PCT}}%` | Yes (rough + trim) |
| 31–33 — Site / Utilities | `{{DIV_31_DESCRIPTION}}` | `{{DIV_31_PLAN}}` | `{{DIV_31_PCT}}%` | `{{DIV_31_CP}}` |

### 2.4 Means and methods (per critical scope item)

For each major scope item, BPC has a documented means-and-methods plan that the SSEB can audit:

- **`{{CRITICAL_SCOPE_1}}`.** `{{MEANS_AND_METHODS_1}}` — equipment, crew, productivity rate, sequence, inspection / hold points.
- **`{{CRITICAL_SCOPE_2}}`.** `{{MEANS_AND_METHODS_2}}`.
- **`{{CRITICAL_SCOPE_3}}`.** `{{MEANS_AND_METHODS_3}}`.

## 3. Schedule

### 3.1 Schedule summary

| Milestone | Calendar days from NTP | Target date |
|---|---|---|
| Notice to Proceed (NTP) | 0 | `{{NTP_TARGET_DATE}}` |
| Submittals + procurement complete | `{{SUBMITTAL_COMPLETE_DAYS}}` | `{{SUBMITTAL_COMPLETE_DATE}}` |
| Mobilization complete | `{{MOB_DAYS}}` | `{{MOB_DATE}}` |
| Demolition complete | `{{DEMO_DAYS}}` | `{{DEMO_DATE}}` |
| Rough MEP complete + in-wall inspection | `{{ROUGH_MEP_DAYS}}` | `{{ROUGH_MEP_DATE}}` |
| Walls + ceilings complete | `{{WALLS_DAYS}}` | `{{WALLS_DATE}}` |
| Finishes complete | `{{FINISHES_DAYS}}` | `{{FINISHES_DATE}}` |
| MEP trim + commissioning | `{{TRIM_DAYS}}` | `{{TRIM_DATE}}` |
| **Substantial Completion** | **`{{SC_DAYS}}`** | **`{{SC_DATE}}`** |
| **Final Completion** | **`{{FC_DAYS}}`** | **`{{FC_DATE}}`** |

### 3.2 CPM Gantt chart

`[INSERT GANTT — BPC will deliver a CPM schedule (MS Project XER export or Primavera P6, per Section L) within NTP+14 days. The proposal-stage Gantt below is illustrative and shows the critical path; the post-award CPM will be cost-loaded and resource-loaded per FAR 52.236-15.]`

```
{{PROJECT_NAME}} — Proposal Schedule (illustrative)
                                    NTP    +30    +60    +90   +120   +150   +180   +210   +240
Submittals + procurement              [=========]
Mobilization + protection                 [===]
Selective demolition                            [=====]
Rough MEP + in-wall                                  [========]
Walls + ceilings + casework                                [==========]
Finishes (flooring / paint / tile)                                [=========]
MEP trim + commissioning                                                [======]
Substantial Completion                                                          ▲
Owner punch + closeout                                                          [====]
Final Completion                                                                       ▲
```

### 3.3 Schedule narrative

Detailed phase-by-phase narrative is provided as a companion to the CPM. See [`firm/proposal-library/boilerplate/schedule-narrative-skeleton.md`](../boilerplate/schedule-narrative-skeleton.md) for the long-form narrative; below is the proposal-tier summary.

The schedule is built bottom-up from approved unit-rate productivities and verified sub commitments. Float is distributed to non-critical paths; the critical path passes through `{{CRITICAL_PATH_SUMMARY}}`. Long-lead items (`{{LONG_LEAD_LIST}}`) are ordered at NTP+1 and tracked weekly until on site.

## 4. Quality Control

### 4.1 Plan reference

BPC's three-phase QC plan (Preparatory → Initial → Follow-up) per USACE EM 385-1-1 / FAR 52.246-12 is at [`firm/proposal-library/boilerplate/qa-qc-plan-one-pager.md`](../boilerplate/qa-qc-plan-one-pager.md). The proposal-stage summary:

- **QC Lead (CQM-C certified):** `[USER TO FILL — QC Lead name]`, reporting to the Project Manager and independent of production.
- **Preparatory Phase Inspection** before each definable feature of work — verify submittals approved, materials on site, crew briefed, AHA approved.
- **Initial Phase Inspection** at first installation of each definable feature — verify workmanship establishes the standard for the rest of the run.
- **Follow-up Inspections** continuous through the duration of each feature — verify ongoing compliance, capture deficiencies, drive corrective action.
- **NCR / Corrective-action discipline** — every nonconforming work item logged on a Nonconformance Report; root cause + corrective action + verification by `{{AGENCY}}`'s Quality Assurance representative.

### 4.2 Submittals + RFIs

- Submittal log issued at NTP+1; tracked weekly; submittals transmitted in `{{AGENCY}}` portal (`{{PROJECT_PORTAL}}`).
- BPC submittal review window: 5 working days from sub receipt to A/E transmittal.
- A/E review window per spec; BPC tracks days-with-A/E and escalates at 10 working days.
- RFI log issued at NTP+1; BPC issues RFIs within 5 working days of identification.

## 5. Safety

BPC's site-specific safety plan per OSHA 29 CFR 1926 / FAR 52.236-13 is at [`firm/proposal-library/boilerplate/safety-plan-one-pager.md`](../boilerplate/safety-plan-one-pager.md). Proposal-stage summary:

- **Site Safety Lead (OSHA 30, CHST if held):** `[USER TO FILL — SSL name]`, on site every day work is performed.
- **Daily** tailgate / pre-task brief at 7:00 AM; site walk at 3:30 PM; both documented in the Daily Construction Report.
- **Per-task** Activity Hazard Analysis (AHA) for every definable feature; AHAs submitted to `{{AGENCY}}` EHS in advance.
- **Hot Work, LOTO, Confined Space, Fall Protection** programs all written, all current, all on site.
- **Coordination with `{{AGENCY}}` EHS** — pre-construction meeting within 5 days of NTP; project-specific orientation for every worker before first day; incidents reported within 1 hour.
- **Firm safety performance** (EMR, OSHA recordable rate, lost-workday case rate, citations): `[USER TO FILL — pull from WC carrier modification rate notice + OSHA 300A; documented in firm-profile.json safety_performance section once captured]`.

## 6. Subcontractor management

Full sub-management approach at [`firm/proposal-library/boilerplate/subcontractor-management.md`](../boilerplate/subcontractor-management.md). Proposal-stage summary:

- **Vetted, repeat-business sub pool.** Subs selected on capability + capacity, BPC past-performance record, compliance (insurance, bonding, license, OSHA training, SAM exclusion check for federal), and competitive price (3 quotes minimum per scope unless single-source justified in writing).
- **Standard flow-down terms** — `{{AGENCY}}` insurance + bonding, safety, QC, Buy American (federal), Davis-Bacon + certified payroll (federal), pay-when-paid, lien waivers, look-ahead participation.
- **Weekly sub-foreman coordination** the day before OAC meeting.
- **Probation / replacement protocol** — written notice + 5-working-day cure period; BPC right to terminate and bring in identified back-up sub if cure fails.
- **Federal-specific:** SAM.gov exclusion check on every sub before contract execution; Davis-Bacon certified payroll (WH-347) collected weekly from each sub tier.

## 7. Risks and mitigations

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Long-lead item delayed | Medium | High | Order at NTP+1; expedite-freight contingency; alternates pre-bid |
| Submittal rejection round-trip | Medium | Medium | BPC submittal review before transmittal; pre-coordinate spec interpretation with A/E |
| Hidden conditions on demo | Medium | High | Investigative pre-demo walk with A/E + owner; immediate RFI on discovery |
| Concurrent owner / occupant disruption | High | Medium | Daily owner walk; weekly OAC; after-hours / weekend window if scope-critical |
| Adverse weather (outdoor scope) | Low–Medium | Low–High | Buffer days in CPM; covered staging |
| AHJ inspection scheduling lag | Medium | Medium | Schedule 5+ working days in advance; back-up dates in CPM |
| Sub crew sickness / absenteeism | Low | Low | Sub commitment with crew-replacement clause; back-up sub identified for each critical trade |
| Change-of-conditions discovery | Medium | High | FAR 52.236-2 differing site conditions notice within statutory window; documented field observations |
| Wage Determination revision mid-project | Low | Medium | Track WD modifications via SAM.gov; flow-down to subs; price-adjustment mechanism per FAR 52.222-30 if triggered |
| `{{PROJECT_SPECIFIC_RISK_1}}` | `{{LIKELIHOOD_1}}` | `{{IMPACT_1}}` | `{{MITIGATION_1}}` |
| `{{PROJECT_SPECIFIC_RISK_2}}` | `{{LIKELIHOOD_2}}` | `{{IMPACT_2}}` | `{{MITIGATION_2}}` |

## 8. Assumptions and exclusions

### 8.1 Assumptions

This Volume I, the priced offer in Volume IV, and the schedule above are based on the following assumptions. If any are invalidated, BPC will issue an RFI before contract award (or a change-order request post-award per FAR 52.243-4):

- Drawings + specifications + amendments referenced are complete and constructable as issued.
- Site access available `{{ACCESS_HOURS}}` per `{{AGENCY}}` schedule; badge / escort process per `{{AGENCY}}` SOP `{{ACCESS_SOP}}`.
- AHJ permits issuable on the timeline assumed in the CPM.
- `{{AGENCY}}` Owner-Furnished items per the OFOI list at SOW §`{{OFOI_REF}}` are delivered on the dates indicated.
- Existing `{{EXISTING_CONDITION_ASSUMPTION}}` is as documented in the RFP attachments; latent conditions discovered are differing site conditions per FAR 52.236-2.
- Hazardous materials previously surveyed and abated by `{{AGENCY}}` per the survey at `{{HAZMAT_SURVEY_REF}}`; any newly discovered hazmat is owner-removed.
- `{{PROJECT_SPECIFIC_ASSUMPTION_1}}`.
- `{{PROJECT_SPECIFIC_ASSUMPTION_2}}`.

### 8.2 Exclusions (only if RFP allows)

> **Discipline reminder:** federal RFPs typically do **not** permit exceptions or exclusions; including them flips a Pass → Fail or makes the offer non-responsive. Only list exclusions if Section L explicitly invites them, **and** raise the underlying issue as an RFI before the cutoff.

- `{{EXCLUSION_1}}` — `[only if RFP permits]`
- `{{EXCLUSION_2}}` — `[only if RFP permits]`

## 9. Evaluator's perspective (delete before submission — internal-use callout)

> **What scorers weight heavily on Volume I (best-value tradeoff construction RFP):**
> 1. **Specificity to the project.** Boilerplate that could describe any RFP scores low. Means-and-methods, site-specific drivers, and risk register tied to the actual SOW score high.
> 2. **Demonstrated understanding of the SOW.** SSEB looks for evidence the offeror read the spec — quoted SOW language, accurate WBS, precise interface descriptions.
> 3. **Self-perform plan + sub plan** — FAR 52.236-1 compliance plus a credible sub-management approach. Tradeoff evaluators reward firms that can prove they will not body-shop the scope to the lowest sub.
> 4. **Schedule realism.** Float distribution, long-lead-item discipline, AHJ inspection lag accounted for. Aggressive schedules without contingency draw skepticism.
> 5. **Risk register.** Site-specific risks beat generic risks; mitigations tied to FAR / contract clauses (FAR 52.236-2, 52.236-15, 52.243-4) score higher than soft-language commitments.
> 6. **Safety.** Documented EMR + OSHA 300A history, named SSL with credentials, AHA discipline. SSEB is allergic to safety-by-marketing-copy.
> 7. **Cross-references.** Volume I that links cleanly to Volumes II / III / IV (consistent personnel, consistent schedule, consistent price assumptions) demonstrates integrated proposal management.
