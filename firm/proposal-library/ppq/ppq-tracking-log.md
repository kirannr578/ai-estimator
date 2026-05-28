# PPQ — Internal Tracking Log

> **How to use this template** — Internal BPC tracking log for PPQ requests on a federal proposal. **Internal-only** — never submitted with the proposal, never shared with the federal CO, never shared with the past client. The point is to track that PPQs were requested, follow-ups happened on cadence, and (where the past client tells us) confirmation that the PPQ was returned to the agency. **Do not record PPQ content** in this log — content stays between the past client and the federal CO. Search-and-replace every `{{PLACEHOLDER}}`.

---

# PPQ Tracking Log — {{FEDERAL_SOLICITATION_NUMBER}}
## {{FEDERAL_PROJECT_NAME}} | {{FEDERAL_AGENCY}}
### Maintained by Blueprint Constructs (BPC) — internal use

## 1. RFP context

| Field | Value |
|---|---|
| Federal solicitation number | `{{FEDERAL_SOLICITATION_NUMBER}}` |
| Federal project name | `{{FEDERAL_PROJECT_NAME}}` |
| Federal agency | `{{FEDERAL_AGENCY}}` |
| Contracting Officer | `{{CO_NAME}}` (`{{CO_EMAIL}}`, `{{CO_PHONE}}`) |
| Proposal due date | `{{FEDERAL_PROPOSAL_DUE_DATE}}` |
| PPQ deadline (if separate) | `{{PPQ_RETURN_DEADLINE}}` |
| PPQ form used | `{{PPQ_FORM_NAME}}` (Agency-provided / BPC standard form `ppq-standard-federal-form.md`) |
| Section L PPQ requirement | `{{SECTION_L_REQUIREMENT}}` (number of PPQs, return method, deadline) |
| BPC PM owner | `{{BPC_PM_NAME}}` (`{{BPC_PM_EMAIL}}`) |

## 2. Per-project tracking

> One row per cited past project. Status updated on each touchpoint.

### Project 1 — `{{PROJECT_1_NAME}}`

| Field | Value |
|---|---|
| Past client name + title | `{{P1_PAST_CLIENT_NAME}}`, `{{P1_PAST_CLIENT_TITLE}}` |
| Past client organization | `{{P1_PAST_CLIENT_ORG}}` |
| Past client email | `{{P1_PAST_CLIENT_EMAIL}}` |
| Past client phone | `{{P1_PAST_CLIENT_PHONE}}` |
| Past client confirmed reachable? | `{{P1_REACHABLE}}` (Yes / Stale-needs-update / Voicemail-only) |
| **Day 0 — package sent** | `{{P1_DAY_0_DATE}}` — sent via `{{P1_DAY_0_METHOD}}` (email / printed packet by courier) |
| Email subject line used | `{{P1_DAY_0_SUBJECT}}` |
| **Day 7 — first follow-up** | `{{P1_DAY_7_STATUS}}` (Not yet / Sent on `{{P1_DAY_7_DATE}}` / N/A — already returned) |
| **Day 14 — escalation to PIC** | `{{P1_DAY_14_STATUS}}` (Not yet / Rocky called on `{{P1_DAY_14_DATE}}` / N/A — already returned) |
| **Day 21 — final follow-up** | `{{P1_DAY_21_STATUS}}` |
| **Past client confirmed PPQ returned to CO?** | `{{P1_RETURNED_YES_NO}}` (Yes / No / Unknown) |
| Date past client said they returned PPQ | `{{P1_RETURNED_DATE}}` (per past client's confirmation only — BPC does not see the form) |
| Notes | `{{P1_NOTES}}` |

### Project 2 — `{{PROJECT_2_NAME}}`

`[Repeat the table format from Project 1 for Project 2.]`

### Project 3 — `{{PROJECT_3_NAME}}`

`[Repeat the table format for Project 3.]`

### Project 4 — `{{PROJECT_4_NAME}}` (optional)

`[Repeat for Project 4 if RFP requires 4–5 PPQs.]`

### Project 5 — `{{PROJECT_5_NAME}}` (optional)

`[Repeat for Project 5 if RFP requires 5 PPQs.]`

## 3. Aggregate status

| Project | PPQ requested? | First follow-up? | Escalation? | Final follow-up? | Past client confirms returned to CO? |
|---|---|---|---|---|---|
| `{{PROJECT_1_NAME}}` | `{{P1_REQUESTED}}` | `{{P1_FOLLOWUP_1}}` | `{{P1_ESCALATION}}` | `{{P1_FINAL_FOLLOWUP}}` | `{{P1_RETURNED_YES_NO}}` |
| `{{PROJECT_2_NAME}}` | `{{P2_REQUESTED}}` | `{{P2_FOLLOWUP_1}}` | `{{P2_ESCALATION}}` | `{{P2_FINAL_FOLLOWUP}}` | `{{P2_RETURNED_YES_NO}}` |
| `{{PROJECT_3_NAME}}` | `{{P3_REQUESTED}}` | `{{P3_FOLLOWUP_1}}` | `{{P3_ESCALATION}}` | `{{P3_FINAL_FOLLOWUP}}` | `{{P3_RETURNED_YES_NO}}` |
| `{{PROJECT_4_NAME}}` | `{{P4_REQUESTED}}` | `{{P4_FOLLOWUP_1}}` | `{{P4_ESCALATION}}` | `{{P4_FINAL_FOLLOWUP}}` | `{{P4_RETURNED_YES_NO}}` |
| `{{PROJECT_5_NAME}}` | `{{P5_REQUESTED}}` | `{{P5_FOLLOWUP_1}}` | `{{P5_ESCALATION}}` | `{{P5_FINAL_FOLLOWUP}}` | `{{P5_RETURNED_YES_NO}}` |

## 4. Touchpoint cadence (template — set on calendar at Day 0)

| Day | Action | Owner | Status |
|---|---|---|---|
| 0 | PPQ package emailed to all cited past clients (cover letter + form + project fact-reminder card) | BPC PM | `{{D0_STATUS}}` |
| 0 | Tracking entry created in this log | BPC PM | `{{D0_LOG_STATUS}}` |
| 0 | Day 7, 14, 21 reminders set on BPC project calendar | BPC PM | `{{D0_CAL_STATUS}}` |
| 7 | First follow-up email to non-responding past clients | BPC PM | `{{D7_STATUS}}` |
| 14 | Phone-call escalation by BPC PIC (Rocky Nudurupati) to non-responding past clients | BPC PIC | `{{D14_STATUS}}` |
| 21 | Final follow-up + document non-response in this log | BPC PM | `{{D21_STATUS}}` |
| Proposal due – 2 days | Final aggregate-status check; flag any non-confirmed PPQs to BPC PIC for last-minute call | BPC PM | `{{FINAL_CHECK_STATUS}}` |
| Proposal due | Submit Volume III with PPQ-coordination tracking summary (this log's §3) cross-referenced | BPC PM | `{{SUBMIT_STATUS}}` |

## 5. Non-response handling

If a cited past client has not confirmed PPQ submission by Day 21, the BPC PM:

1. Documents the non-response in this log (last-known status, all touchpoints, reason if known).
2. Decides with the BPC PIC whether to:
   - **Substitute** the cited project with an alternate from `firm/firm-profile.json → past_projects[]` (if RFP allows substitution before submission)
   - **Submit without the PPQ** for that project, noting the unreturned PPQ in the Volume III §4 PPQ-coordination summary
   - **Request agency extension** if the RFP allows and the missing PPQ is materially important to the past-performance score

3. Documents the decision in §6 below.

## 6. Decisions log

| Date | Decision | Rationale | Authorized by |
|---|---|---|---|
| `{{DECISION_DATE_1}}` | `{{DECISION_1}}` | `{{RATIONALE_1}}` | `{{AUTH_1}}` |
| `{{DECISION_DATE_2}}` | `{{DECISION_2}}` | `{{RATIONALE_2}}` | `{{AUTH_2}}` |

## 7. Discipline notes

- **Never store PPQ content in this log.** Even if a past client volunteers a copy, do not paste it here, do not summarize ratings, do not narrate quotes from the past client. Store only the metadata (requested-date, follow-up dates, past client's confirmation that they submitted the form).
- **Never share this log externally.** Internal-only. Includes contact information that should not leak to a competitor or an unrelated party.
- **Past-client privacy.** Past-client emails / phones are firm-internal data; treat per `firm/_README` and the broader firm-profile PII discipline.
- **Retention.** Retain this log for the duration of the proposal evaluation cycle + 12 months for capture-management retrospective. Then archive or delete per BPC records-retention policy.
