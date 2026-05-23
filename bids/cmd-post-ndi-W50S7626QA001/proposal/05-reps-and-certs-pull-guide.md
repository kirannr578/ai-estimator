# Reps & Certs — SAM.gov pull guide

Federal solicitations no longer require offerors to submit Representations and Certifications as standalone documents. Per **DFARS 252.204-7998 Alternate A (Deviation 2026-O0043)**, the offeror's submission of a quote with active SAM.gov reps & certs **incorporates them by reference**. The corollary: the SAM.gov reps & certs MUST be current and accurate, and the offeror represents (by submission) that they are.

## A. The mechanism (DFARS 252.204-7998 Alt A paragraph (g) verbatim)

> *"(g) The Offeror has completed the annual representations and certifications electronically via the SAM website at https://www.sam.gov After reviewing the SAM database information, the Offeror verifies by submission of the offer that the representations and certifications currently posted electronically that apply to this solicitation as indicated in FAR 52.204-7 and paragraph (f) of this provision have been entered or updated within the last 12 months, are current, accurate, complete, and applicable to this solicitation (including the business size standard applicable to the NAICS code referenced for this solicitation), as of the date of this offer, and are incorporated in this offer by reference (see FAR 4.203-1); except for the changes identified below..."*

**Translation**: Submitting the SF 1442 = certifying that SAM reps & certs are current, accurate, complete, and applicable to W50S7626QA001 as of the offer date.

## B. What to verify in SAM before submission

### B.1 Annual Reps & Certs (FAR 52.204-8 + 52.212-3)

Log in to `https://sam.gov/`, navigate to **Entity Profile → Representations and Certifications**. Verify:

| # | Item | Where in SAM |
|---:|---|---|
| 1 | Last updated date is **within 12 months** of the offer date | "Last Updated" field on Reps & Certs tab |
| 2 | All FAR 52.212-3 paragraphs are completed (no "incomplete" warnings) | Reps & Certs tab |
| 3 | NAICS-specific reps (52.204-8(c)(2)(iv)) for **236220** are completed | Reps & Certs tab |
| 4 | Small-business size assertion at $45.0M for NAICS 236220 | Size Metrics tab |
| 5 | DUNS legacy reference (if SAM still asks) | Entity Information |
| 6 | UEI active | Entity Information |
| 7 | CAGE active | Entity Information |
| 8 | Banking / EFT current | Financial Information |
| 9 | TIN matches IRS records | Entity Information |
| 10 | No active exclusions on entity name + UEI + key principals | Exclusions search |

### B.2 DFARS-specific reps & certs (Section K — DFARS provisions)

Verify the following are **on file** (active in SAM annual cycle):

| Provision | What it is | SAM section |
|---|---|---|
| **DFARS 252.204-7016** | Covered Defense Telecommunications Equipment or Services — Representation. Offeror represents whether they "do" or "do not" provide covered defense telecom equipment or services. | DFARS rep set |
| **DFARS 252.204-7017** | Prohibition on Acquisition of Covered Defense Telecom — Representation. Required only if 252.204-7016 says "does provide". | DFARS rep set |
| **DFARS 252.225-7050** | Disclosure of Ownership or Control by Government of a Country that is a State Sponsor of Terrorism. Applies to solicitations expected to result in contracts ≥ $150K. | DFARS rep set |
| **DFARS 252.203-7005** | Representation Relating to Compensation of Former DoD Officials. | DFARS rep set |
| **DFARS 252.225-7055** | Representation Regarding Business Operations with the Maduro Regime. | DFARS rep set |
| **DFARS 252.225-7059** | Prohibition on Certain Procurements from the Xinjiang Uyghur Autonomous Region — Representation. | DFARS rep set |

### B.3 NIST 800-171 Basic Assessment (DFARS 252.204-7019 + 252.204-7024)

Although the contract is for interior renovation (not Covered Defense Information handling per se), DFARS 252.204-7019 is **incorporated by reference in Section L**. Verify:

| # | Item | Where |
|---:|---|---|
| 1 | NIST SP 800-171 Basic Assessment posted to SPRS | `https://www.sprs.csd.disa.mil/` (login required) |
| 2 | Assessment date within last 3 years | Same |
| 3 | Score documented (max 110; partial-implementation is OK; positive scores preferred) | Same |

If no Basic Assessment is on file, **complete the self-assessment** per the NIST 800-171 control set, then post to SPRS. Standard process; CO can disqualify offers without an SPRS Basic Assessment on file.

### B.4 FAR 52.204-7 SAM Registration

Per FAR 52.204-7: *"An Offeror is required to be registered in SAM when submitting an offer or quotation, and shall continue to be registered until time of award, during performance, and through final payment of any contract, basic agreement, basic ordering agreement, or blanket purchasing agreement resulting from this solicitation."*

Active SAM registration is **gateway**. No SAM = no offer.

## C. Changes to specific reps (Block (g) of DFARS 252.204-7998 Alt A)

If any specific rep needs to change for this solicitation only (without updating SAM), DFARS 252.204-7998 Alt A paragraph (g) provides a fillable table:

```
FAR/DFARS provision No.    Title              Date    Change
____                       ____               ____    ____
```

**For W50S7626QA001, no rep is expected to change.** Leave the table blank in the offer (or simply not submit the form — SAM-by-reference is sufficient).

## D. Submission

**No separate document is needed in the proposal package.** The submission of the SF 1442 itself + active SAM registration = full reps & certs submission.

> ⚠️ **However, if the Government later asks "show me your active SAM reps & certs as of [offer date]"**, the firm should be able to produce a printout / PDF export of the SAM Reps & Certs page. **Best practice: print/export the SAM Reps & Certs page on the morning of submission and retain in the firm's bid file** as proof of currency.

## E. Common pitfalls

| Pitfall | Consequence | Mitigation |
|---|---|---|
| Reps & Certs > 12 months old | CO may reject offer as non-conforming | Update SAM Reps & Certs immediately if past 12-month cycle (24–72 hours) |
| NAICS 236220 not registered or not asserted as small at $45M | Set-aside ineligible | Add NAICS 236220 to registered list; assert small at $45M; allow 24–72 hours |
| 252.204-7016 not completed (or incorrect) | Offer rejected for covered-defense-telecom non-compliance | Verify the rep status; update if "does provide" + complete -7017 if applicable |
| SPRS Basic Assessment missing or stale | CO disqualifies for DFARS 252.204-7019 | Complete self-assessment per NIST 800-171; post to SPRS |
| Active exclusion on a key principal | Offeror is automatically excluded from award per FAR 9.405 | Check exclusions BEFORE submission; address proactively |
| TIN mismatch with IRS | Payment delays + SAM flags | Verify and reconcile in SAM |

## F. Day-of-submission verification

On the morning of Thu 2026-06-04, **before sending the email**, the Contracts Administrator runs a final SAM check:

- ☐ SAM Reps & Certs page shows "Updated within 12 months" — **export to PDF**
- ☐ Entity Profile page shows **Active** UEI + Active CAGE + EFT current + TIN matches — **export**
- ☐ Exclusions search returns 0 hits on entity name + UEI + key principals — **export**
- ☐ SPRS Basic Assessment current — **export**
- ☐ NAICS 236220 is registered + small at $45M — **export**

These exports go to the firm's bid-file (NOT in the submission package — they are evidence retained in case CO asks). If any item fails on the morning of submission, **STOP and remediate** before sending the offer.
