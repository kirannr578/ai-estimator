# Reps & Certs pull guide — FA667526Q0002 B1710 Office Refurbishment

This RFQ relies on **SAM.gov-posted representations and certifications** per:

- FAR 52.204-7 — System for Award Management Registration (Deviation 2026-O0038) — Section I
- FAR 52.204-13 — System for Award Management Maintenance (Deviation 2026-O0038) — Section I
- FAR 52.204-19 — Incorporation by Reference of Representations and Certifications — Section I
- DFARS 252.204-7998 — Alternate A, Annual Reps and Certs (Deviation 2026-O0043) — Section K (Reps & Certs)

The offeror does **not need to complete a paper reps-and-certs questionnaire**. Instead, the offeror confirms in the offer that its SAM-posted reps and certs are current, accurate, and incorporated into the offer by reference.

---

## What to do (Wed 2026-05-27 PM)

### Step 1 — Log into SAM.gov

- URL: `https://sam.gov/`
- Login with Rocky's SAM.gov user account (Rocky as the firm's E-Business POC per BPC's SAM registration)
- Navigate to **Entity Management** → **Active Registrations** → select Blue Print Constructs

### Step 2 — Verify the following before submission

| Check | Required value | Action if failed |
|---|---|---|
| Registration status | **Active** (green) | If Inactive: contact SAM.gov Federal Service Desk at 866-606-8220; cannot submit offer until Active |
| Registration expiration date | **On or after 2026-05-29** | If sooner: renew now; takes 24-48 hours typically |
| Reps & Certs last refresh date | **Within 12 months** of 2026-05-29 (so refresh date ≥ 2025-05-29) | If older: refresh in SAM; **takes 3-10 business days to propagate** — this is the longest-lead item and can block submission |
| NAICS 236220 in entity NAICS list | Yes | If missing: add 236220 to SAM (24-48 hour propagation) |
| Size representation at 236220 | **Small under $45M** | Confirm SAM's auto-calculation matches; if wrong, fix in SAM Reps & Certs |
| EFT (banking) info | Current | If outdated: refresh; takes 24-48 hours |
| TIN matches IRS records | **Matched** | If mismatch: contact IRS and SAM Help Desk; this is a separate process |
| Excluded Parties (debarment / suspension) | **Not excluded** | If excluded: this is a much bigger problem than a missed bid |
| FAR 52.212-3 Reps & Certs (commercial items) | Current and complete | Auto-handled when SAM Reps & Certs are current |

### Step 3 — Print / export the SAM entity-status page

- From the SAM entity page, click **View** → **Print** → **Save as PDF**
- Save as: `05_RepsAndCerts_SAM-screenshot.pdf` for inclusion in the offer email packet (Attachment 5)
- The PDF should show:
  - Firm legal name: RK Residential Homes and Commercial Constructions, LLC
  - DBA: Blue Print Constructs
  - UEI: LM4YHVQ71QG7
  - CAGE: 9LET0
  - Registration status: Active (green badge)
  - Registration expiration date
  - Date this status was last verified

### Step 4 — Affirmative statement in the offer cover letter

In the offer cover email body (drafted in `11-rfi-cover-letter.md`), include this statement:

> *Per DFARS 252.204-7998 Alternate A, Deviation 2026-O0043 (Feb 2026), the offeror has completed the annual representations and certifications electronically via the SAM.gov website at https://sam.gov. The offeror verifies by submission of this offer that the representations and certifications currently posted electronically that apply to this solicitation are current, accurate, complete, and applicable to this solicitation (including the business size standard applicable to NAICS code 236220), as of the date of this offer, and are incorporated in this offer by reference. The offeror represents that it is a Small Business concern under NAICS 236220 ($45,000,000 size standard).*

---

## Firm-profile-derived data for reps & certs cross-reference

The following firm-side data is consistent with the SAM reps and certs and is referenced (not re-asserted) in this offer:

| SAM-posted rep | Value (per `firm/firm-profile.json`) |
|---|---|
| Firm legal name | RK Residential Homes and Commercial Constructions, LLC |
| DBA | Blue Print Constructs |
| Address (registered) | 16283 Willowick Ln, Frisco, TX 75033 |
| UEI | LM4YHVQ71QG7 |
| CAGE | 9LET0 |
| EIN | 87-4292998 |
| TX Taxpayer ID | 32082600456 |
| Phone | (469) 213-1838 |
| Email | contactus@blueprintconstructs.com |
| Website | https://www.blueprintconstructs.com |
| State of incorporation | Texas |
| Year founded | 2022 |
| NAICS list | 236115, 236116, 236118, 236210, **236220**, 238160, 238170, 238310, 238320, 238330, 238340, 238350, 561790 |
| Primary NAICS for this bid | **236220** ($45M size standard) |
| Business size | Small |

---

## Reps & Certs that explicitly apply per Section K of THIS RFQ

Per Section K of `Solicitation - FA667526Q0002.pdf` (Representations, Certifications, & Other Statements — pages 21-23):

- **52.240-90** — Security Prohibitions and Exclusions Representations and Certifications (Deviation 2026-O0038)
- **252.203-7005** — Representation Relating to Compensation of Former DoD Officials — (handled in SAM)
- **252.204-7008** — Compliance with Safeguarding Covered Defense Information Controls — (handled in SAM)
- **252.225-7055** — Representation Regarding Business Operations with the Maduro Regime — (handled in SAM)
- **252.225-7059** — Prohibition on Certain Procurements from the Xinjiang Uyghur Autonomous Region-Representation — (handled in SAM)
- **52.209-2** — Prohibition on Contracting With Inverted Domestic Corporations-Representation — (handled in SAM)
- **252.204-7017** — Prohibition on the Acquisition of Covered Defense Telecommunications Equipment or Services-Representation — (handled in SAM; offeror represents that it does NOT provide covered defense telecommunications equipment)
- **252.204-7998 Alt A** — Annual Reps and Certs (Deviation 2026-O0043) — **the umbrella clause that says SAM-posted reps suffice**

If any specific rep is required to be made on the offer paper (e.g., a foreign-ownership question that doesn't have a SAM-posted answer), the offer cover should include a section header *Additional Representations* with each rep restated and answered.

> Spot-check from the Section K reading: none of the Section K reps require paper completion when the offeror has SAM-current reps. **All Section K reps are satisfied by reference**.

---

## Failure modes (the 4 ways this section can hose the offer)

1. **SAM goes Inactive between submission and award.** Mitigation: Rocky monitors SAM weekly during the award window; renews proactively if expiration is within 60 days.
2. **Reps & Certs lapsed > 12 months ago.** Mitigation: refresh TODAY; 3-10 BD propagation. If propagation hasn't completed by 29 May 17:00, offer is technically non-responsive on FAR 52.204-7 / 52.204-19 — flag to CO with an explanatory note that the refresh was initiated and is in-flight.
3. **NAICS 236220 not in SAM list.** Mitigation: add NAICS in SAM (24-48 hr); confirm presence Thu PM.
4. **Excluded Parties List shows BPC.** Mitigation: this should not be the case (no known exclusions per firm profile). If it appears unexpectedly, this is a separate process problem that requires resolution before any federal bid.
