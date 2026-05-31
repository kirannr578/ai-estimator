# {{PROJECT_NAME}} — Overview

> **Source playbook:** [`firm/playbooks/texas-state-csp-hsp.md`](../../../firm/playbooks/texas-state-csp-hsp.md)

## Solicitation identity

| Field | Value |
|---|---|
| Solicitation # | `{{SOLICITATION_NUMBER}}` |
| Project number (owner) | `{{PROJECT_NUMBER}}` |
| Project name | `{{PROJECT_NAME}}` |
| Agency | `{{AGENCY}}` ({{AGENCY_SHORT}}) |
| Issuing office | `{{ISSUING_OFFICE}}` |
| Procurement type | Competitive Sealed Proposal under Tex. Gov't Code Ch. 2269 / RFCSP under Tex. Educ. Code Ch. 51 |
| Delivery method | `{{DELIVERY_METHOD}}` (Lump-Sum Construction / CMAR / Design-Build) |
| Primary NAICS | 236220 (typ) |
| Period of performance | Substantial Completion `{{SC_DAYS}}` cal days + Final Completion `{{FC_DAYS}}` cal days from NTP |
| Estimated magnitude | $`{{MAGNITUDE_LOW}}` – $`{{MAGNITUDE_HIGH}}` `[USER TO FILL — often not published in NOP; estimate from scope]` |
| Prevailing wage source | `{{TX_WAGE_FILE}}` for `{{COUNTY}}` County per Tex. Gov't Code Ch. 2258 |
| HUB goal applied | `{{APPLICABLE_HUB_GOAL_LABEL}}` — `{{STATEWIDE_HUB_GOAL_PCT}}%` per 34 TAC §20.284, or project-specific override of `{{HUB_GOAL_PCT}}%` |

## Project location + pre-response meeting

| Field | Value |
|---|---|
| Site address | `{{SITE_ADDRESS}}` |
| Site city / state / ZIP | `{{SITE_CITY_STATE_ZIP}}` |
| County | `{{COUNTY}}` |
| Pre-response meeting | `{{PRE_RESPONSE_MEETING_DATE}}` at `{{PRE_RESPONSE_MEETING_LOCATION}}` |
| Pre-response meeting mandatory? | `{{MANDATORY_YES_NO}}` |
| Pre-response meeting RSVP | `{{RSVP_INSTRUCTIONS}}` |
| Site walk | `{{SITE_WALK_DATE}}` (often same as pre-response or paired) |

## Key dates

| Milestone | Date |
|---|---|
| NOP posted on ESBD | `{{NOP_DATE}}` |
| Pre-response meeting | `{{PRE_RESPONSE_MEETING_DATE}}` |
| Questions / RFI cutoff | `{{RFI_CUTOFF_DATE}}` |
| Last addendum | `{{LAST_ADDENDUM_DATE}}` |
| Proposal due | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` |
| **HSP due (if separate deadline — common on TTUS bids)** | `{{HSP_DUE_DATE}}` @ `{{HSP_DUE_TIME}}` |
| Public opening | immediately after proposal due |
| BAFO / clarifications window (if any) | `{{BAFO_WINDOW}}` |
| Anticipated award notification | `{{AWARD_TARGET_DATE}}` |
| NTP target | `{{NTP_TARGET_DATE}}` |
| Substantial completion target | NTP + `{{SC_DAYS}}` cal days |
| Final completion target | NTP + `{{FC_DAYS}}` cal days |

## Scope summary (1–3 sentences)

`{{SCOPE_SUMMARY}}` — `[USER TO FILL — pull from CSP package §00 11 13 (Notice of Project) or the project-manual scope section.]`

## Contacts (agency-side)

| Role | Name | Email | Phone |
|---|---|---|---|
| Agency project manager | `{{PM_NAME}}` | `{{PM_EMAIL}}` | `{{PM_PHONE}}` |
| Agency contracting / purchasing | `{{CO_NAME}}` | `{{CO_EMAIL}}` | `{{CO_PHONE}}` |
| A/E project manager | `{{AE_POC_NAME}}` (`{{AE_FIRM_NAME}}`) | `{{AE_POC_EMAIL}}` | `{{AE_POC_PHONE}}` |
| HUB / HSP coordinator | `{{HUB_POC_NAME}}` | `{{HUB_POC_EMAIL}}` | `{{HUB_POC_PHONE}}` |
| Facility owner / occupant POC | `{{FACILITY_POC_NAME}}` | `{{FACILITY_POC_EMAIL}}` | `{{FACILITY_POC_PHONE}}` |
| EHS coordinator | `{{EHS_POC_NAME}}` | `{{EHS_POC_EMAIL}}` | `{{EHS_POC_PHONE}}` |
| SSC PM (TAMU System only) | `{{SSC_PM_NAME}}` | `{{SSC_PM_EMAIL}}` | `{{SSC_PM_PHONE}}` |

## Submission

| Item | Value |
|---|---|
| Submission portal | `{{SUBMISSION_PORTAL}}` (e-Builder / SharePoint / direct / mail / hand-deliver) |
| Submission delivery address | `{{SUBMISSION_DELIVERY_ADDRESS}}` |
| Submission format | `{{SUBMISSION_FORMAT}}` (sealed envelope / electronic upload / both) |
| Sealed-envelope exterior labeling | per CSP instructions — `{{LABEL_REQUIREMENTS}}` |
| Number of copies | `{{NUM_COPIES}}` |
| File format (if electronic) | PDF |

## Bid posture (BPC quick read)

| Question | Answer |
|---|---|
| TX HUB cert current? | ✅ — renewed 2026-05-30 per user (prior cycle expired 2024-08-31); new expiration `[USER TO CONFIRM: new expiration date]`. See [`firm/compliance/README.md`](../../../firm/compliance/README.md) |
| TX franchise tax good-standing? | ⚠️ — verify via TX Taxable Entity Search |
| TX CMBL enrolled? | 🔴 — confirm |
| Insurance + Umbrella adequate for agency SGC? | 🔴 — pull current COIs + check Umbrella ≥ $5M for institutional |
| Bondable at this magnitude? | ✅ — $1M single-project floor established |
| Past-perf fit? | ✅ — Hindu Temple + Holiday Inn + 250+ SFH portfolio per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json) |
| HSP achievable at statewide goal? | `[USER TO FILL after sub outreach starts]` |
| Geographic fit | `[USER TO FILL — drive time from Frisco / Little Elm to site]` |
| Special hazards (lab, abatement, occupancy, secure facility) | `[USER TO FILL]` |
| Go / No-go recommendation | `[USER TO FILL after pre-bid analysis]` |

## Cross-references

- Playbook: [`firm/playbooks/texas-state-csp-hsp.md`](../../../firm/playbooks/texas-state-csp-hsp.md)
- Compliance check: [`firm/compliance/README.md`](../../../firm/compliance/README.md)
- Scope template starter: [`firm/scope-templates/office-tenant-refurb.md`](../../../firm/scope-templates/office-tenant-refurb.md) or [`firm/scope-templates/dressing-room-renovation.md`](../../../firm/scope-templates/dressing-room-renovation.md) per archetype
- Proposal-library: [`firm/proposal-library/`](../../../firm/proposal-library/README.md)
