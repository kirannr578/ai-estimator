# Internal — SAM.gov verification checklist

**Owner:** Contracts admin / Entity Administrator.
**Deadline:** Monday 2026-05-25 EOD (so any defect can be fixed before SAM's 3–10 BD update cycle eats the bid window).

This checklist is the cross-reference for the firm's SAM.gov readiness. **If the firm has already verified SAM.gov in the past 7 days for another federal bid (e.g., the USFWS San Marcos 140FC126R0017 bid), most of this can be reused** — just re-confirm the items still apply to NAICS 236220 + the size standard.

## A. Pre-conditions

- [ ] Entity Administrator has login credentials to `https://sam.gov/`
- [ ] Authorization to make changes (or escalation path to firm Officer for change approval)
- [ ] Browser with PDF-export capability (for evidence collection)

## B. Verification items (12)

| # | Item | Expected value | How to verify | Status |
|---:|---|---|---|---|
| 1 | UEI is **Active** | Active (not expired or revoked) | SAM.gov → Entity Profile → Entity Information → "UEI Status" | ☐ |
| 2 | Active Registration in SAM | "Active" with expiration > 30 days from today | Same page → "Registration Status" | ☐ |
| 3 | NAICS 236220 is in the registered NAICS list | 236220 listed | SAM.gov → Goods and Services tab → NAICS Codes | ☐ |
| 4 | NAICS 236220 small-business assertion at $45.0M | "Small" at $45M | SAM.gov → Size Metrics tab → NAICS 236220 row | ☐ |
| 5 | Reps & Certs (FAR 52.204-8 / 52.212-3 / DFARS 252.204-7998 Alt A) updated within 12 months | "Last Updated" within 12 months | SAM.gov → Representations and Certifications tab | ☐ |
| 6 | DFARS 252.204-7016 Covered Defense Telecom — Representation completed | Either "does" or "does not" provide; if "does", -7017 also completed | Same tab | ☐ |
| 7 | DFARS 252.225-7050 (Country sponsor of terrorism) Representation completed | Standard rep | Same tab | ☐ |
| 8 | DFARS 252.225-7055 (Maduro Regime) Representation completed | Standard rep | Same tab | ☐ |
| 9 | DFARS 252.225-7059 (Xinjiang) Representation completed | Standard rep | Same tab | ☐ |
| 10 | CAGE code Active | Active | SAM.gov → Entity Profile → Entity Information | ☐ |
| 11 | EFT / Banking current | Routing + account match firm's current banking | SAM.gov → Financial Information | ☐ |
| 12 | TIN matches IRS | "Matches" or equivalent confirmation | SAM.gov → Entity Profile → Entity Information | ☐ |

## C. SPRS NIST 800-171 Basic Assessment (DFARS 252.204-7019)

- [ ] SPRS access established at `https://www.sprs.csd.disa.mil/`
- [ ] NIST SP 800-171 Basic Assessment posted within last 3 years
- [ ] Score documented (max 110; partial-implementation OK; positive scores preferred)

> ⚠️ If no Basic Assessment posted: complete the self-assessment per the NIST 800-171 control set and post to SPRS. CO can disqualify offers without SPRS Basic Assessment.

## D. Exclusions screen

Run an Exclusions search at `https://sam.gov/exclusions` against:
- [ ] Firm legal name
- [ ] Firm UEI
- [ ] Firm CAGE
- [ ] Each key principal (President, VP, Officer, Director — anyone with > 25% ownership or signing authority on federal bids)

Expected result: 0 active exclusions.

If any active exclusion is found: **STOP — escalate immediately.** An active exclusion on the firm or any key principal disqualifies the offer per FAR 9.405. Resolve before submission.

## E. Cross-reference with USFWS sibling bid

If the firm's contracts admin completed the SAM.gov verification for the USFWS San Marcos 140FC126R0017 bid within the last 7 days:

- [ ] Items 1, 2, 3, 4, 5, 6, 10, 11, 12 likely re-usable as confirmed
- [ ] Items 7, 8, 9 (DFARS reps) are the same — confirm if they were checked
- [ ] SPRS Basic Assessment likely re-usable
- [ ] Re-run Exclusions search (it's quick)
- [ ] **Re-confirm Item 4 — NAICS 236220 small-business assertion at $45.0M** — same NAICS as USFWS (which is also 236220), so already confirmed

If the USFWS verification was clean, **the SAM gate for W50S7626QA001 is essentially closed** — just re-run Exclusions search + verify still-active.

## F. Defect remediation

If any item fails:

| Item | Remediation | Cycle time |
|---|---|---|
| 1 (UEI) | Request UEI from `https://sam.gov/` if missing or expired | 1–3 BD |
| 3, 4 (NAICS) | Add NAICS 236220 to registered list + assert small at $45M | 1–3 BD |
| 5 (Reps & Certs) | Update via SAM.gov; standard 24–72 hour propagation | 1–3 BD |
| 6, 7, 8, 9 (DFARS reps) | Update via SAM.gov | 1–3 BD |
| 10 (CAGE) | Coordinate with DLA CAGE office at `https://cage.dla.mil/` | 3–10 BD |
| 11 (EFT) | Update via SAM.gov | 1–3 BD |
| 12 (TIN match) | Coordinate with SAM.gov + IRS reconciliation | 3–10 BD |
| Active Exclusions | Resolve via SAM.gov + DOJ if disputed | varies (potentially weeks) |

> ⚠️ **Latest acceptable fix-start: Tuesday 2026-05-26.** SAM updates have a 3–10 BD lead time. Anything started after Tuesday risks not clearing in time.

## G. Evidence collection

Before submission day (Thu 2026-06-04), export to PDF:
- [ ] SAM.gov Entity Profile page → save as `W50S7626QA001_SAM_EntityProfile_[Firm].pdf`
- [ ] SAM.gov Reps & Certs page → `W50S7626QA001_SAM_RepsCerts_[Firm].pdf`
- [ ] SAM.gov Exclusions search results → `W50S7626QA001_SAM_Exclusions_[Firm].pdf`
- [ ] SAM.gov Size Metrics page → `W50S7626QA001_SAM_SizeMetrics_[Firm].pdf`
- [ ] SPRS Basic Assessment screen → `W50S7626QA001_SPRS_BasicAssessment_[Firm].pdf`

These are NOT submitted to the Government but retained in the firm's bid file as evidence-of-currency in case the CO asks at evaluation.

## H. Day-of-submission re-verification

On the morning of Thu 2026-06-04, **before sending the email**, the Contracts Administrator:

1. Logs in to SAM.gov + confirms all 12 items still active
2. Re-runs Exclusions search
3. Re-exports the evidence-collection PDFs
4. Files them with the bid file
5. Notifies PM that SAM is current

If any item fails on the morning of submission, **STOP and remediate** before sending the offer. Do not send a non-conforming offer.

## I. Common pitfalls

| Pitfall | Why | Mitigation |
|---|---|---|
| Reps & Certs rolled past 12-month renewal date a week before bid | SAM "annual" is a calendar-year cycle — easy to miss | Set firm-internal calendar reminder 30 days before annual rollover |
| EFT updated but not propagated to SAM | Bank changes don't auto-propagate | Confirm SAM EFT after any banking change |
| TIN mismatch from IRS | IRS database lag or firm-side entity-name change | Reconcile early; can take 7–10 BD |
| UEI expired (e.g., 5-year cycle) | Common at firms that don't bid frequently | Renew at SAM.gov |
| NAICS 236220 not registered (firm registered under different NAICS) | Often firms register the most-common NAICS but miss specific ones | Add 236220 + any related (e.g., 237310, 238210, 238220, etc. for trade-specific work) |
| CAGE expired | DLA cycle | Renew at `https://cage.dla.mil/` |
| Active exclusion on a sub-10% owner that CO discovers via principal screen | FAR 9.405 captures key principals | Pre-screen all named principals on bid forms before submission |
