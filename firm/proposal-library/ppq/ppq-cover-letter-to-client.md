# PPQ — Cover Letter to Past Client

> **How to use this template** — Cover letter from BPC to a cited owner reference, requesting completion of a Past-Performance Questionnaire (PPQ) for a federal proposal. One letter per cited project. Personalize the project name, dates, and BPC POC per project. **Send the cover letter + the PPQ form (agency-provided or [`ppq-standard-federal-form.md`](ppq-standard-federal-form.md) as fallback) + a project fact-reminder card** as a single email or printed packet within 48 hours of RFP issuance. Search-and-replace every `{{PLACEHOLDER}}`. Do **not** ask the past client to send the completed PPQ back to BPC — they must send it **directly to the federal Contracting Officer**.

---

```
Blueprint Constructs (Blue Print Constructs, LLC dba)
16283 Willowick Ln
Frisco, TX 75033
(469) 213-1838 office
contactus@blueprintconstructs.com
UEI LM4YHVQ71QG7  •  CAGE 9LET0


{{LETTER_DATE}}


{{PAST_CLIENT_NAME}}, {{PAST_CLIENT_TITLE}}
{{PAST_CLIENT_ORGANIZATION}}
{{PAST_CLIENT_ADDRESS}}


Re:  Past-Performance Questionnaire — {{PAST_PROJECT_NAME}}
     Federal solicitation {{FEDERAL_SOLICITATION_NUMBER}} — {{FEDERAL_PROJECT_NAME}}
     Issued by {{FEDERAL_AGENCY}}, due {{FEDERAL_PROPOSAL_DUE_DATE}}


Dear {{PAST_CLIENT_NAME}}:

Blueprint Constructs is preparing a proposal for {{FEDERAL_AGENCY}} on
{{FEDERAL_SOLICITATION_NUMBER}}, {{FEDERAL_PROJECT_NAME}}. As part of the
past-performance evaluation under FAR 15.305(a)(2), the Government requests
that prior clients of the offeror complete a brief Past-Performance
Questionnaire (PPQ) describing the offeror's performance on a recent
relevant project.

We are citing the {{PAST_PROJECT_NAME}} project, on which Blueprint Constructs
served as {{BPC_ROLE}} from {{PAST_PROJECT_START}} to
{{PAST_PROJECT_END_OR_STATUS}}. We would be grateful if you would complete
the enclosed PPQ and return it directly to the {{FEDERAL_AGENCY}}
Contracting Officer at the address below.


  Return the completed PPQ to:

      {{CO_NAME}}, Contracting Officer
      {{FEDERAL_AGENCY}} — {{ISSUING_OFFICE}}
      Email: {{CO_EMAIL}}
      Phone: {{CO_PHONE}}

  Please include "{{FEDERAL_SOLICITATION_NUMBER}} — Past-Performance
  Questionnaire — Blueprint Constructs" in the email subject line.


  Requested return window:

      Three (3) business days from receipt, or no later than
      {{PPQ_RETURN_DEADLINE}}, whichever is earlier.


To assist your recall of the project, the enclosed Project Fact Reminder
card summarizes the contract scope, value, period of performance, and key
personnel. If you would like to verify any project details before completing
the PPQ, please reach out to me directly — I am happy to provide the
underlying project records, drawings, schedule, or pay-app history.

Per the Federal Acquisition Regulation, the completed PPQ travels directly
from you to the Contracting Officer; Blueprint Constructs does not see the
content of the questionnaire. Your candid assessment is what the
Government's source-selection team relies on, and we are grateful for the
time you take to provide it.


Blueprint Constructs point of contact for this proposal:

      {{BPC_POC_NAME}}
      {{BPC_POC_TITLE}}
      Email:  {{BPC_POC_EMAIL}}
      Phone:  {{BPC_POC_PHONE}}


Thank you for your support of this past-performance review.

Respectfully,



[USER TO FILL — BPC signer name]
[USER TO FILL — BPC signer title]
Blueprint Constructs (Blue Print Constructs, LLC dba)


Enclosures:
  1. Past-Performance Questionnaire (PPQ form — {{PPQ_FORM_NAME}})
  2. Project Fact Reminder card — {{PAST_PROJECT_NAME}}
  3. Self-addressed return-envelope to {{FEDERAL_AGENCY}} Contracting Officer
     (printed copy only; for electronic return use the email address above)


cc: Ravikiran (Rocky) Nudurupati, Principal in Charge, Blueprint Constructs
    rocky@blueprintconstructs.com
```

---

## Project Fact Reminder card (enclosed with cover letter)

> **Print on a single page; attach behind the PPQ form. The point is to refresh the past client's memory of the project so they can complete the PPQ confidently and accurately. Do not coach the response — list facts only.**

```
Blueprint Constructs — Project Fact Reminder
============================================

Project name:           {{PAST_PROJECT_NAME}}
Project number:         {{PAST_PROJECT_NUMBER}}
Owner / Customer:       {{PAST_CLIENT_ORGANIZATION}}
Site address:           {{PAST_PROJECT_SITE_ADDRESS}}

BPC's role:             {{BPC_ROLE}}
Contract type:          {{PAST_PROJECT_CONTRACT_TYPE}}
Contract value (orig):  ${{PAST_PROJECT_VALUE_ORIGINAL}}
Contract value (final): ${{PAST_PROJECT_VALUE_FINAL}}
Period of performance:  {{PAST_PROJECT_START}} → {{PAST_PROJECT_END_OR_STATUS}}
Bonding:                {{PAST_PROJECT_BOND}}

Scope summary:
  {{PAST_PROJECT_SCOPE_SUMMARY_BRIEF}}

Key personnel from BPC on this project:
  - Principal in Charge: Ravikiran (Rocky) Nudurupati
  - Project Manager:     [USER TO FILL — PM name on this past project]
  - Superintendent:      [USER TO FILL — Super name on this past project]

Outcome highlights (factual; for memory refresh only):
  - Schedule: {{PAST_PROJECT_SCHEDULE_OUTCOME}}
  - Budget:   {{PAST_PROJECT_BUDGET_OUTCOME}}
  - Quality:  {{PAST_PROJECT_QUALITY_OUTCOME}}
  - Safety:   {{PAST_PROJECT_SAFETY_OUTCOME}}

If you need additional information to complete the PPQ:
  Contact {{BPC_POC_NAME}} at {{BPC_POC_EMAIL}} / {{BPC_POC_PHONE}}.
```

---

## Internal cover-letter checklist (do not include with the mailing)

Before sending the cover letter to a past client, the BPC PM verifies:

- [ ] Past client name, title, organization, and address are **current** (not stale per a prior project)
- [ ] Past client email and phone are confirmed reachable (test email; voice on phone)
- [ ] Past client is a person who has direct, recent knowledge of BPC's performance — not a generic procurement office
- [ ] PPQ form is the **agency-provided form** if RFP attached one; otherwise [`ppq-standard-federal-form.md`](ppq-standard-federal-form.md)
- [ ] Project Fact Reminder card facts are sourced from `firm/firm-profile.json → past_projects[]` and the BPC project file (no marketing language; facts only)
- [ ] CO email, CO phone, and `{{PPQ_RETURN_DEADLINE}}` are correctly extracted from RFP Section L
- [ ] BPC POC for this proposal is correct (typically the BPC PM running the capture)
- [ ] Letter is signed (wet ink or e-signature) by Rocky Nudurupati or designee
- [ ] Tracking entry created in [`ppq-tracking-log.md`](ppq-tracking-log.md)
- [ ] Day 7 / Day 14 / Day 21 follow-up reminders set on BPC's project calendar
