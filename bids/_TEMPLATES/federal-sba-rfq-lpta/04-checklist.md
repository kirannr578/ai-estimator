# {{PROJECT_NAME}} — Bid-Prep Checklist

> Pulled from [`bids/usfws-san-marcos-140FC126R0017/02-bid-prep-checklist.md`](../../usfws-san-marcos-140FC126R0017/02-bid-prep-checklist.md), generalized.
> Track to closure for every federal-SBA-LPTA bid. Marked items map to [`firm/compliance/README.md`](../../../firm/compliance/README.md).

## Pre-pricing (Day 1–5 after RFP capture)

- [ ] SAM.gov registration verified active; Reps & Certs ≤ 12 months current; EFT + TIN refreshed
- [ ] Verify firm meets SBA size standard for `{{NAICS_CODE}}` (≤ $`{{SIZE_STANDARD_USD}}M` 3-yr avg revenue)
- [ ] Read all RFP attachments end-to-end; flag boilerplate-leakage in `03-missing-documents.md`
- [ ] Confirm `{{SITE_VISIT_DATE}}` and RSVP per Section L
- [ ] Confirm `{{RFI_CUTOFF_DATE}}` and start RFI drafting
- [ ] Pull Wage Determination `{{WD_NUMBER}}` `{{WD_DATE}}` and transcribe applicable trade rates
- [ ] Bondability commitment letter ordered from surety (≤ $1M-class envelope confirmed)
- [ ] Bid bond (SF 24) ordered: 20% of estimated bid OR $1M cap
- [ ] P&P bond commitment letter ordered (if > $150K contract value)
- [ ] Current GL COI pulled from agent (≤ 30 days old at submission)
- [ ] Current WC + Auto + Umbrella COIs pulled
- [ ] Past-performance picks selected per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json) for this bid type
- [ ] Past-perf owner-side reference contacts confirmed (working email + phone)

## Site visit + RFI window (Day 5–20)

- [ ] Attend site visit `{{SITE_VISIT_DATE}}`; capture site-visit shopping list per `01-scope.md`
- [ ] Photo log filed; measurements verified against drawings
- [ ] Take-off finalized + reviewed against CLIN list in `05-bid-form-prep.md`
- [ ] RFIs filed by `{{RFI_CUTOFF_DATE}}`
- [ ] Sub solicitations issued (≥ 3 quotes per major trade)
- [ ] Sub vetting checklist (per [`firm/proposal-library/boilerplate/subcontractor-management.md`](../../../firm/proposal-library/boilerplate/subcontractor-management.md)) underway for each sub

## Pricing assembly (Day 15–25)

- [ ] Direct cost rolled up (subs + materials + self-perform labor)
- [ ] General conditions priced (super, PM, temp protection, dumpster, etc.) — `{{POP_DAYS}}` cal day footprint
- [ ] Bond + insurance loaded as percentage
- [ ] DBA labor-burden uplift applied if firm labor < prevailing
- [ ] Contingency applied (3–5% LPTA; 7–8% if site-visit missed)
- [ ] Overhead applied (7–10%)
- [ ] Profit applied (3–6% — LPTA-thin)
- [ ] Total cross-checked against `{{MAGNITUDE_LOW}}` – `{{MAGNITUDE_HIGH}}` magnitude band
- [ ] Self-perform > 15% of direct cost verified (FAR 52.236-1)
- [ ] Schedule of Prices completed — every CLIN priced

## Proposal assembly (Day 20–28)

### Volume I — Price

- [ ] Cover letter drafted per [`firm/proposal-library/exec-summary-archetypes/federal-sba-lpta.md`](../../../firm/proposal-library/exec-summary-archetypes/federal-sba-lpta.md)
- [ ] SF 1442 completed + signed (blocks 14–20C)
- [ ] All amendments listed in Block 19 + signed SF 30 pages attached
- [ ] Schedule of Prices attached
- [ ] SF 24 Bid Bond attached + POA
- [ ] SAM Reps & Certs incorporation page attached
- [ ] Buy American Certificate (FAR 52.225-4) attached if RFP triggers
- [ ] Volume I file named `{{SOLICITATION_NUMBER}}_Part_I_Price_Proposal.pdf`

### Volume II — Technical / Past Performance

- [ ] Affirmative technical-acceptability statement (1 page; no exceptions)
- [ ] Past-perf entry 1 (1 paragraph + facts table)
- [ ] Past-perf entry 2 (1 paragraph + facts table)
- [ ] Surety commitment letter attached
- [ ] Volume II file named `{{SOLICITATION_NUMBER}}_Part_II_Technical.pdf`

## Submission (Day 28–30)

- [ ] Final QC review by a second BPC team member (PM or PIC)
- [ ] All `[USER TO FILL]` markers closed via [`firm/_scripts/scan_placeholders.py`](../../../firm/_scripts/scan_placeholders.py)
- [ ] Email transmittal drafted per Section L delivery instructions
- [ ] Sent to `{{SUBMISSION_EMAIL_1}}` + `{{SUBMISSION_EMAIL_2}}` (CC CO)
- [ ] Submitted ≥ 30 minutes before `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}`
- [ ] Email transmittal saved + receipt timestamp captured
- [ ] SAM.gov / PIEE upload confirmed (if portal-based)

## Post-submission (Day 30–award)

- [ ] Acceptance period tracked (`{{ACCEPTANCE_PERIOD_DAYS}}` cal days)
- [ ] Monitor SAM.gov for award notice or further amendments
- [ ] Respond to any CO clarification request within 1 business day
- [ ] If awarded → trigger post-award checklist (separate)
- [ ] If lost → request debrief per FAR 15.506; document lessons learned
