# Internal — SAM.gov verification checklist (to firm's SAM owner)

> **Send by:** Today (Saturday 2026-05-23) or Monday morning (2026-05-25) — whichever the firm's normal cadence supports. **Due back: EOD Monday 2026-05-24.**
>
> **Recipient:** The firm's SAM.gov Entity Administrator (typically the contracts admin, controller, or CFO). If unsure who owns SAM at the firm, this is the first question to answer.
>
> **Purpose:** Surface any stale or incorrect SAM.gov item BEFORE bid-prep effort is sunk into a bid the firm legally cannot submit. Per FAR 52.204-7 + RFP L.1.0, a non-current SAM record makes the bid technically unacceptable on its face. SAM fixes take 3–10 business days to propagate; the latest acceptable fix-start is 2026-06-12 (10 business days before submission), but earlier is much safer.
>
> **Single biggest gate blocking the bid.** See `../07-risk-register.md` R-01.

---

## Email composition

**To:** `[USER TO FILL: SAM Entity Administrator email]`

**CC:** `[USER TO FILL: bid PM]`, `[USER TO FILL: estimator]`

**Subject:** `URGENT — SAM.gov verification for USFWS Bid 140FC126R0017 — Due back EOD Mon 5/24`

**Attachment:** `../proposal/05-reps-and-certs-pull-guide.md` — the step-by-step pull guide (or excerpt of § A 12-step pull)

---

### Body

```
[SAM Admin First Name]:

We are bidding on a federal Firm-Fixed-Price construction job (USFWS San
Marcos ARC, Sol 140FC126R0017) due **Monday 2026-06-22**. Per FAR 52.204-7
and Solicitation §L.1.0, the firm must be SAM-registered active with
current Reps & Certs to be eligible for award. A stale or incorrect SAM
record makes the bid non-conforming on its face — regardless of how
competitive the price is.

We need a green-light check on SAM **by EOD Monday 2026-05-24**. SAM
updates take 3–10 business days to propagate; the latest acceptable date
to START a fix is 2026-06-12. Earlier is much safer.

Please run through the 12-step pull (detailed in
proposal/05-reps-and-certs-pull-guide.md) and report back on each of the
following:

  CRITICAL GREEN-LIGHT ITEMS (each must be ✅; any ❌ stops the bid)
  ---------------------------------------------------------------

   1. SAM Registration Status =  Active                                ☐
   2. Registration Expiration Date is after 2026-09-30                 ☐
   3. UEI is Active (12-character identifier)                          ☐
   4. CAGE Code is Active (5-character identifier)                     ☐
   5. NAICS 236220 (Commercial & Institutional Building Construction)
      is in the registered NAICS list                                  ☐
   6. Small Business size status under NAICS 236220 is Small
      (firm under $45.0M average annual receipts over trailing 3 yrs)  ☐
   7. Reps & Certs under FAR 52.204-8 were last updated within the
      past 12 months                                                   ☐
   8. EFT / Banking info in SAM is current and matches the firm's
      active operating account                                         ☐
   9. TIN matches IRS records (no IRS-side mismatch flags)             ☐

  REPS TO SPECIFICALLY VERIFY IN SAM (each must be answered correctly)
  -------------------------------------------------------------------

  10. 52.204-24 (Section 889 — Covered Telecom): "Does not use" +
      "Will not provide"                                               ☐
  11. 52.204-26 (Section 889 — second rep): same as -24                ☐
  12. 52.204-29 (FASCSA — Reasonable inquiry conducted; no covered
      articles/sources proposed)                                       ☐
  13. 52.209-2 (Inverted Domestic Corporation): "Is not" inverted      ☐
  14. 52.209-5 (Responsibility Matters): no undisclosed tax
      delinquencies, contract terminations, or convictions in the
      prior 3 years                                                    ☐
  15. 52.209-11 (Delinquent tax / felony conviction): "No"             ☐
  16. 52.219-1 (Small Business — small at $45.0M for NAICS 236220)     ☐
  17. 52.222-22 (Previous Contracts — federal > $10K in past 12 mo
      listed and OFCCP-compliant)                                      ☐
  18. 52.222-25 (Affirmative Action — will comply)                     ☐
  19. 52.225-2 (Buy American Certificate — Domestic)                   ☐
  20. 52.225-4 (Buy American + FTA — Domestic)                         ☐
  21. 52.225-20 (Sudan — Does not conduct restricted operations)       ☐
  22. 52.225-25 (Iran — Does not engage)                               ☐
  23. 52.232-33 (EFT via SAM — banking current per item 8 above)       ☐

  DELIVERABLES BACK TO THE BID TEAM
  ---------------------------------

   A. Each of items 1–23 marked ✅ or ❌ with one-line note for any ❌.

   B. Fresh "Entity Information" PDF pulled from SAM today, named
      SAM_Entity_Information_[Legal_Name]_2026-05-24.pdf.
      File to firm's bid-prep folder.

   C. The firm's UEI and CAGE in plain text so the bid team can insert
      into SF 1442 block 17.

   D. The Reps & Certs "last updated" date so the bid team can document
      it in the proposal's Reps & Certs invocation page.

   E. Any item that is ❌ or yellow: please call me directly to discuss
      whether a fix is feasible inside the 2026-06-22 submission window.

If anything is stale and needs immediate refresh, please start the
refresh today; refreshes propagate in 3–5 business days for Reps & Certs
without entity changes, longer if entity name / address / TIN need updates.

This is the SINGLE LARGEST RISK to the bid. Without a clean SAM check by
EOD Monday, we should consider walking away rather than burning hours on
a bid we cannot submit.

Thanks,

[USER TO FILL: bid PM name + title]
[OFFEROR LEGAL NAME]
[Phone] / [Email]
```

---

## Triage if items come back ❌

| Item ❌ | Severity | Fix path |
|---|---|---|
| Items 1, 3, 4 (registration / UEI / CAGE inactive) | **STOP — bid cannot be submitted** until fixed | Renew SAM registration; 7–15 business days |
| Item 2 (expiration before 2026-09-30) | Stop until renewed (registration must be active through 90-day acceptance period) | Renew now — 3–10 business days |
| Item 5 or 6 (NAICS not registered or size status not Small) | **STOP — bid cannot be submitted** | If NAICS 236220 not registered, add now (1–3 business days). If firm is no longer small at $45M, **withdraw — this is a 100% SB set-aside; firm is ineligible** |
| Item 7 (Reps & Certs stale > 12 months) | Refresh in SAM | 1–3 business days |
| Item 8 (EFT/banking outdated) | Update; doesn't block submission but blocks post-award payment | 5–10 business days |
| Item 9 (TIN mismatch with IRS) | Resolve with IRS first, then update SAM | 5–20 business days — **start this immediately if applicable** |
| Items 10–23 (any specific Rep wrong) | Correct the individual Rep in SAM | 1–3 business days |

---

## Latest acceptable fix-start dates

| Fix type | Latest start date for clearing by 6/22 |
|---|---|
| Reps & Certs refresh (no entity changes) | **2026-06-17** (Tuesday) |
| Add NAICS 236220 | **2026-06-15** (Sunday — effectively Mon 6/16) |
| Update entity name / address (with documentation) | **2026-06-08** (Monday) |
| TIN mismatch resolution | **2026-05-29** (Friday — uses most of this week's buffer) |
| Brand-new SAM registration | **2026-06-01** (Monday) |

After these dates, the corresponding fix likely cannot propagate in time. If a fix can't realistically clear, the responsible call is to **withdraw rather than submit a non-conforming proposal**.

---

## Tracking

| Verification step | Status | Notes |
|---|---|---|
| Email sent to SAM admin | ☐ | Date: |
| SAM admin acknowledged | ☐ | Date: |
| All 23 items verified | ☐ | Date: |
| SAM Entity Information PDF in firm's bid file | ☐ | Date: |
| UEI + CAGE transmitted to bid team | ☐ | Date: |
| Any ❌ items resolved | ☐ | Date / description: |
| Green light to continue bid-prep | ☐ | Date: |

---

## After clearance

Once all 23 items verify ✅, attach the SAM Entity Information PDF to
`../proposal/02-volume-II-technical-acceptability.md` § B as the supporting evidence for the Reps & Certs invocation per FAR 52.204-8(d). Pull a fresh copy on Sunday 6/21 or Monday 6/22 morning (within 24 hours of submission) to ensure currency.
