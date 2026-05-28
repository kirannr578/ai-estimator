# {{PROJECT_NAME}} — Bid-Prep Checklist (SAP Best-Value)

> Track to closure for every federal SAP best-value bid. Marked items map to [`firm/compliance/README.md`](../../../firm/compliance/README.md).
> SAP cycle is **14–30 days from RFQ release to quote due** — much shorter than LPTA (T+30–45) or FAR 15 tradeoff (T+45–90). Compress the workflow accordingly.

## Pre-pricing (Day 1–3 after RFQ capture)

- [ ] **Confirm template archetype is correct** — verify SF-18 / SF-1449 on cover + FAR Part 13 (often + Part 12) + comparative trade-off Section M per `03-missing-documents.md` §0. If any answer is off-pattern, switch templates before sinking estimator hours
- [ ] SAM.gov registration verified active; Reps & Certs ≤ 12 months current; EFT + TIN refreshed
- [ ] **Subscribe to SAM.gov amendment notifications for `{{SOLICITATION_NUMBER}}`** — SAP RFQs frequently amend mid-window
- [ ] Verify firm meets SBA size standard for `{{NAICS_CODE}}` (≤ $`{{SIZE_STANDARD_USD}}M` 3-yr avg revenue)
- [ ] Read all RFQ attachments end-to-end; flag boilerplate-leakage in `03-missing-documents.md`
- [ ] Confirm `{{SITE_VISIT_DATE}}` and RSVP per Section L
- [ ] Confirm `{{RFI_CUTOFF_DATE}}` and start RFI drafting
- [ ] Pull Wage Determination `{{WD_NUMBER}}` `{{WD_DATE}}` and transcribe applicable trade rates (DBA applies regardless of SAT/SAP status)
- [ ] Verify whether bid bond required at submission (Section I — typical SAP uses **FAR 52.228-13 Alternative Payment Protections** instead of SF-24)
- [ ] Bondability commitment letter ordered from surety (post-award P&P or alt-payment per RFQ)
- [ ] Current GL COI pulled from agent (≤ 30 days old at submission); verify limits against RFQ-cited agency clause (often LOWER than $1M/$2M baseline)
- [ ] Current WC + Auto + Umbrella COIs pulled
- [ ] Prior-experience picks selected per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json) — need **3–5** references (verify count in Section L), not 2 (LPTA default)
- [ ] Owner-side reference contacts confirmed (working email + phone) for each prior-experience pick

## Site visit + RFI window (Day 3–10)

- [ ] Attend site visit `{{SITE_VISIT_DATE}}`; capture site-visit shopping list per `01-scope.md`
- [ ] Photo log filed; measurements verified against drawings
- [ ] Take-off finalized + reviewed against CLIN list in `05-bid-form-prep.md`
- [ ] RFIs filed by `{{RFI_CUTOFF_DATE}}` (often 3 cal days after site visit on SAP)
- [ ] Sub solicitations issued (≥ 3 quotes per major trade) — compressed timeline; sub quote-due dates need 5+ working days before BPC's quote-due date
- [ ] Sub vetting checklist (per [`firm/proposal-library/boilerplate/subcontractor-management.md`](../../../firm/proposal-library/boilerplate/subcontractor-management.md)) underway for each sub
- [ ] Re-check SAM.gov for amendments at Day-10 (or Due-3, whichever is earlier)

## Pricing assembly (Day 7–18)

- [ ] Direct cost rolled up (subs + materials + self-perform labor)
- [ ] General conditions priced (super, PM, temp protection, dumpster, etc.) — `{{POP_DAYS}}` cal day footprint
- [ ] Bond + insurance loaded as percentage (lower than LPTA if no bid bond at submission)
- [ ] DBA labor-burden uplift applied if firm labor < prevailing
- [ ] Contingency applied (**4–6% SAP**; bump higher if site-visit missed)
- [ ] Overhead applied (8–11%)
- [ ] Profit applied (**5–8% SAP** — looser than LPTA's 3–6%)
- [ ] Total cross-checked against `{{MAGNITUDE_BAND}}` (often unstated on SAP — sanity-check against last-3-job actuals + sub-SAT cap)
- [ ] **"Groups of 3" stress test:** at this price, is BPC likely in the lowest-3 priced quotes? If not, **re-tighten** before locking
- [ ] Self-perform > 15% of direct cost verified (FAR 52.236-1)
- [ ] Schedule of Prices completed — every CLIN priced (blank CLIN = non-responsive even on SAP)

## Quote package assembly (Day 14–25)

Single combined PDF — **not** multi-volume.

### Front matter
- [ ] Section L checklist (if RFQ provides one) — completed as first page
- [ ] **Signed SF-18** (or SF-1449) — blocks completed
- [ ] All amendments listed + signed SF-30 pages attached

### Reps & Certs
- [ ] SAM Reps & Certs incorporation page (FAR 52.204-8(d) or 52.212-3) attached
- [ ] Section K provisions completed as applicable
- [ ] Buy American Certificate (FAR 52.225-4) attached if RFQ triggers

### Price section
- [ ] Schedule of Prices attached — every CLIN priced
- [ ] Surety commitment letter for post-award P&P (or FAR 52.228-13 Alternative Payment Protections) attached if RFQ requires

### Technical capability narrative — REQUIRED (do not skip)
- [ ] Project understanding (1 pp)
- [ ] Proposed schedule (1 pp)
- [ ] Phasing + site logistics (1–2 pp)
- [ ] Trade-by-trade approach (3–8 pp)
- [ ] QC + safety summary (1 pp)
- [ ] Total length within Section L cap (typ 5–15 pp on SAP)

### Prior experience — REQUIRED (3–5 references)
- [ ] Reference 1 — short-form ½-page block (owner, value, contact, dates, scope, relevance)
- [ ] Reference 2 — short-form ½-page block
- [ ] Reference 3 — short-form ½-page block
- [ ] Reference 4 — if RFQ asks for 4 or 5
- [ ] Reference 5 — if RFQ asks for 5

### Key personnel — short-form (½-page per role)
- [ ] PM — ½-page resume
- [ ] Super — ½-page resume
- [ ] QC — ½-page resume
- [ ] Principal in Charge — ½-page resume (if RFQ asks)
- [ ] Safety officer — ½-page resume (if RFQ asks)

### Contractor core data
- [ ] Company name, UEI `LM4YHVQ71QG7`, CAGE `9LET0`, POC, email, phone

### Package finishing
- [ ] Combined into single PDF titled per Section L (typ `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - QUOTE PACKAGE.pdf`)
- [ ] PDF size ≤ email limit (typ 25 MB); split + number "email N of M" in subject if larger

## Submission (Day 20–30)

- [ ] Final QC review by a second BPC team member (PM or PIC)
- [ ] All `[USER TO FILL]` markers closed via [`firm/_scripts/scan_placeholders.py`](../../../firm/_scripts/scan_placeholders.py)
- [ ] Email transmittal drafted per Section L delivery instructions (exact subject line; correct addresses)
- [ ] Sent to `{{SUBMISSION_EMAIL_1}}` (and `{{SUBMISSION_EMAIL_2}}` if a second address is named; CC CO if a CC line is published)
- [ ] Submitted ≥ 30 minutes before `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}`
- [ ] Email transmittal saved + receipt timestamp captured
- [ ] SAM.gov / PIEE upload confirmed (if portal-based — uncommon on SAP)

## Post-submission (Day 25–award)

- [ ] Acceptance period tracked (`{{ACCEPTANCE_PERIOD_DAYS}}` cal days — typ 60 on SAP)
- [ ] Monitor SAM.gov for award notice or further amendments
- [ ] Respond to any CO clarification request within 1 business day
- [ ] If awarded → trigger post-award checklist (separate); P&P bonds or alt-payment protection due **within 10 days of award**
- [ ] If lost → request debrief per FAR 13.106-3(d) (SAP-equivalent debrief — less formal than FAR 15.506); document lessons learned
