# {{PROJECT_NAME}} — Overview

> **Source playbook:** [`firm/playbooks/federal-sba-rfq-lpta.md`](../../../firm/playbooks/federal-sba-rfq-lpta.md)

## Solicitation identity

| Field | Value |
|---|---|
| Solicitation # | `{{SOLICITATION_NUMBER}}` |
| Project name | `{{PROJECT_NAME}}` |
| Agency | `{{AGENCY}}` ({{AGENCY_SHORT}}) |
| Issuing office | `{{ISSUING_OFFICE}}`, `{{ISSUING_OFFICE_ADDRESS}}` |
| Contract type | `{{CONTRACT_TYPE}}` (typ Firm-Fixed-Price per FAR 52.216-1) |
| Set-aside | `{{SET_ASIDE}}` (typ 100% Small Business per FAR 52.219-6) |
| Evaluation method | `{{EVALUATION_METHOD}}` (typ LPTA — Lowest Price Technically Acceptable per FAR 15.101-2) |
| Primary NAICS | `{{NAICS_CODE}}` (typ 236220 Commercial + Institutional Building Construction) |
| Size standard | $`{{SIZE_STANDARD_USD}}M` (236220 current = $45.0M 3-yr avg revenue) |
| Magnitude | $`{{MAGNITUDE_LOW}}` – $`{{MAGNITUDE_HIGH}}` |
| Period of performance | `{{POP_DAYS}}` calendar days from NTP |
| Wage determination | `{{WD_NUMBER}}` effective `{{WD_DATE}}` (Davis-Bacon Act, per RFP attachment) |

## Project location + site visit

| Field | Value |
|---|---|
| Site address | `{{SITE_ADDRESS}}` |
| Site city / state / ZIP | `{{SITE_CITY_STATE_ZIP}}` |
| County | `{{COUNTY}}` |
| Site visit date | `{{SITE_VISIT_DATE}}` |
| Site visit POC | `{{SITE_POC_NAME}}` — `{{SITE_POC_EMAIL}}` — `{{SITE_POC_PHONE}}` |
| Site visit RSVP method | `{{SITE_VISIT_RSVP_METHOD}}` |

## Key dates

| Milestone | Date |
|---|---|
| RFP release | `{{RFP_RELEASE_DATE}}` |
| Site visit | `{{SITE_VISIT_DATE}}` |
| RFI cutoff | `{{RFI_CUTOFF_DATE}}` |
| Proposal due | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` |
| Acceptance period | `{{ACCEPTANCE_PERIOD_DAYS}}` calendar days from proposal opening |
| Anticipated award | `{{AWARD_TARGET_DATE}}` |
| NTP target | `{{NTP_TARGET_DATE}}` |
| Substantial completion target | NTP + `{{POP_DAYS}}` cal days |

## Scope summary (1–3 sentences)

`{{SCOPE_SUMMARY}}` — `[USER TO FILL — pull from RFP Section C / SOW first paragraph; e.g. "Renovate and rehabilitate the existing single-story 1,500 SF shop building and adjacent 2-stall garage at the San Marcos National Fish Hatchery & Technology Center, including envelope repair, OH-door + man-door replacement, MEP re-fit, and interior finish work."]`

## Contacts (agency-side)

| Role | Name | Email | Phone |
|---|---|---|---|
| Contracting Officer (CO) | `{{CO_NAME}}` | `{{CO_EMAIL}}` | `{{CO_PHONE}}` |
| Contract Specialist (CS) | `{{CS_NAME}}` | `{{CS_EMAIL}}` | `{{CS_PHONE}}` |
| Site / project POC | `{{SITE_POC_NAME}}` | `{{SITE_POC_EMAIL}}` | `{{SITE_POC_PHONE}}` |
| `[any additional POC named in the RFP]` | | | |

## Submission

| Item | Value |
|---|---|
| Submission portal | `{{SUBMISSION_PORTAL}}` (SAM.gov, PIEE, or direct email) |
| Submission email(s) | `{{SUBMISSION_EMAIL_1}}`; `{{SUBMISSION_EMAIL_2}}` (CC CO) |
| File naming | `{{SOLICITATION_NUMBER}}_Part_I_Price_Proposal.pdf`, `{{SOLICITATION_NUMBER}}_Part_II_Technical.pdf` |
| Email subject | `Proposal Submission-{{SOLICITATION_NUMBER}}` (exact) |
| Send-by-buffer | Submit 30+ minutes before cutoff |

## Bid posture (BPC quick read)

| Question | Answer |
|---|---|
| BPC eligible (small + correct NAICS)? | ✅ — NAICS 236220 small ≤ $45M |
| SAM.gov current? | ⚠️ Verify expiration before pricing — see [`firm/compliance/README.md`](../../../firm/compliance/README.md) |
| Insurance current? | 🔴 / ⚠️ — pull current COIs |
| Bondable at this magnitude? | ✅ — $1M single-project floor established |
| Past-perf fit? | ✅ — Lavon RV Park + Hindu Temple + Holiday Inn per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json) |
| Magnitude vs BPC's typical bid? | `[USER TO FILL — match against firm's current bonded backlog + estimating capacity]` |
| Geographic fit | `[USER TO FILL — drive time from Frisco / Little Elm to site + per-diem implications]` |
| Special hazards (lab, abatement, secure facility, remote) | `[USER TO FILL — call out anything that demands a non-baseline sub or extra GC time]` |
| Go / No-go recommendation | `[USER TO FILL after pre-bid analysis]` |

## Cross-references

- Playbook: [`firm/playbooks/federal-sba-rfq-lpta.md`](../../../firm/playbooks/federal-sba-rfq-lpta.md)
- Compliance check: [`firm/compliance/README.md`](../../../firm/compliance/README.md)
- Scope template starter: pick one of [`firm/scope-templates/`](../../../firm/scope-templates/README.md) that matches the SOW
- Proposal-library: [`firm/proposal-library/`](../../../firm/proposal-library/README.md)
