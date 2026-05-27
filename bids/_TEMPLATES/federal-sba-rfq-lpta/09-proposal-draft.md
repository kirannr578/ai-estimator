# {{PROJECT_NAME}} — Proposal Draft (Volume I + Volume II Assembly)

> **Federal LPTA proposal discipline:** the proposal is **two PDFs**, not a narrative pitch.
> - **Volume I — Price** is for the CO to score against other offerors' prices.
> - **Volume II — Technical / Past Performance** is for the CO to Pass/Fail the technical-acceptability gate.

## Volume I — Price Proposal

> File name: `{{SOLICITATION_NUMBER}}_Part_I_Price_Proposal.pdf`
> Assembly order: cover letter → SF 1442 → amendment acknowledgments → Schedule of Prices → SF 24 Bid Bond → SAM Reps & Certs incorporation → Buy American Certificate

### Volume I cover letter

`[Paste from firm/proposal-library/exec-summary-archetypes/federal-sba-lpta.md and search-and-replace placeholders. Single page, no exceptions.]`

### SF 1442 — Solicitation, Offer and Award

See `05-bid-form-prep.md` for the block-by-block field map. Print, sign (wet ink or e-signature), insert.

### Amendment acknowledgments

Each SF 30 amendment numbered + signed; attach. List numbers on SF 1442 Block 19.

| # | SF 30 amendment | Date | Acknowledged |
|---|---|---|---|
| 1 | `{{AMD_1_NUMBER}}` | `{{AMD_1_DATE}}` | ☐ |
| 2 | `{{AMD_2_NUMBER}}` | `{{AMD_2_DATE}}` | ☐ |

### Schedule of Prices

See `05-bid-form-prep.md`. Every CLIN priced. Insert.

### SF 24 Bid Bond + Power of Attorney

See `05-bid-form-prep.md`. 20% of bid or $1M cap. Insert.

### SAM Reps & Certs incorporation

See `05-bid-form-prep.md` for the 1-page incorporation statement. Insert.

### Buy American Certificate

See `05-bid-form-prep.md`. Required if RFP triggers FAR 52.225-9 / -11. Insert.

---

## Volume II — Technical Acceptability + Past Performance

> File name: `{{SOLICITATION_NUMBER}}_Part_II_Technical.pdf`
> Assembly order: cover sheet → affirmative statement of technical acceptability → past performance × 2 → surety commitment letter

### Volume II cover sheet

```
{{SOLICITATION_NUMBER}}
{{PROJECT_NAME}}

VOLUME II — TECHNICAL ACCEPTABILITY + PAST PERFORMANCE

Submitted by:  Blue Print Constructs, LLC dba Blueprint Constructs
               UEI LM4YHVQ71QG7  •  CAGE 9LET0
               16283 Willowick Ln, Frisco, TX 75033
               (469) 213-1838  •  contactus@blueprintconstructs.com

Date:          {{SUBMISSION_DATE}}
```

### Affirmative statement of technical acceptability

> **Discipline reminder:** keep this to one page. Do not narrate approach, schedule, safety, QC. Those belong in post-award submittals. **Every narrative paragraph here is an opportunity to inadvertently introduce an exception that flips Pass → Fail.**

```
STATEMENT OF TECHNICAL ACCEPTABILITY

Blue Print Constructs, LLC dba Blueprint Constructs offers to perform 100% of
the Statement of Work in {{SOLICITATION_NUMBER}}, {{PROJECT_NAME}}, in
accordance with all terms, conditions, drawings, specifications, and amendments
referenced in the solicitation, without exception.

Blueprint Constructs:
  • Is a Small Business under NAICS {{NAICS_CODE}} (size standard
    ${{SIZE_STANDARD_USD}}M 3-year average revenue) per its active SAM.gov
    record (UEI LM4YHVQ71QG7, CAGE 9LET0).
  • Will self-perform a minimum of 15% of the work on site, in compliance
    with FAR 52.236-1.
  • Will comply with the Davis-Bacon Act and Wage Determination
    {{WD_NUMBER}} dated {{WD_DATE}} for all construction laborers and
    mechanics.
  • Will comply with the Buy American Act and FAR 52.225-9 for all iron,
    steel, and construction materials.
  • Will procure Performance and Payment Bonds at 100% of contract value
    on award, per FAR 52.228-15.
  • Will comply with all FAR Part 52 clauses listed in Section I of the
    solicitation.
  • Takes no exception to any term, condition, drawing, specification, or
    amendment in this solicitation.

Signed:  [USER TO FILL — signer name + title]
Date:    {{SUBMISSION_DATE}}
```

### Past performance — Project 1

Pick from `firm/firm-profile.json → past_project_selection_rules.{{BID_KEY}}` (typ {{PAST_PERF_PICK_1}}). Paste from `firm/proposal-library/past-performance/{{PAST_PERF_PICK_1}}.md` and refine.

| Field | Value |
|---|---|
| Project name | `{{PROJECT_1_NAME}}` |
| Owner | `{{PROJECT_1_OWNER}}` |
| Contract value | `${{PROJECT_1_VALUE}}` |
| Period of performance | `{{PROJECT_1_POP}}` |
| BPC role | `{{PROJECT_1_ROLE}}` |
| Owner-side reference | `{{PROJECT_1_REF_NAME}}` — `{{PROJECT_1_REF_EMAIL}}` — `{{PROJECT_1_REF_PHONE}}` |
| Scope summary | `{{PROJECT_1_SCOPE}}` |
| Relevance to this bid | `{{PROJECT_1_RELEVANCE}}` |

### Past performance — Project 2

Same fields, second pick.

### Surety bondability commitment letter

`[USER TO FILL — attach commitment letter from BPC's bonding surety, on letterhead, signed, dated within 30 days of submission, naming the project + agency + contract value envelope. Commitment letter must state surety is on Treasury Circular 570 list and is willing to issue Performance + Payment Bonds at 100% of contract value at award.]`

---

## Post-submission tracker

| Activity | Status | Date |
|---|---|---|
| Volume I + Volume II final QC | ☐ | |
| `firm/_scripts/scan_placeholders.py` returns 0 hits in `bids/{{SLUG}}/` | ☐ | |
| Email transmittal drafted | ☐ | |
| Submitted via `{{SUBMISSION_PORTAL}}` to `{{SUBMISSION_EMAIL_1}}` + `{{SUBMISSION_EMAIL_2}}` | ☐ | |
| Submission timestamp recorded | ☐ | |
| Receipt confirmation from CO | ☐ | |
