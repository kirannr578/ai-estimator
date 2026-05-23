# Reps & Certs pull guide — SAM.gov per FAR 52.204-8

> Source: FAR 52.204-8 (Annual Representations and Certifications, OCT 2024 or current version) + RFP §K (pp.52–57) + §L.2.1.4 (p.66).
>
> **Why this matters:** The proposal invokes FAR 52.204-8(d) "incorporation by reference" of the offeror's SAM-resident reps and certs. If the SAM reps are stale (> 12 months old) OR if any of the specific reps below are missing or incorrectly answered in SAM, **the incorporation fails and the proposal is technically deficient.** This guide is the firm's last chance to catch a stale SAM record before submission.
>
> **Cycle:** Reps & certs in SAM are on an annual renewal cycle. The system prompts the entity-admin (typically the firm's contracts admin or controller) ~30 days before the annual deadline. If anyone in the firm has dismissed those prompts, this guide will surface that.

---

## A. The 12-step pull

Run this on **Monday 2026-05-24, before noon CT**. Total time: 20–35 minutes for a current SAM record; 30–90 minutes if anything is stale and needs in-line correction.

### Step 1 — Log in to SAM.gov as the Entity Administrator

- URL: `https://sam.gov/` → Sign In
- Credentials: the firm's **Entity Administrator** (NOT a regular SAM user). If unsure who that is, the EA shows on the Entity record under "Entity Administrators".
- If MFA is required and the EA isn't immediately available, escalate; only the EA can edit Reps & Certs.

### Step 2 — Navigate to Entity Management

- From the Workspace, click **Entity Management** → click the entity (matching the firm's legal name)

### Step 3 — Verify Core Data is Active

| Field to verify | Expected |
|---|---|
| Registration Status | **Active** |
| Registration Expiration Date | After **2026-09-30** (or sooner if you're inside the renewal window — see Step 4) |
| Legal Business Name | Matches the firm's legal name exactly |
| Unique Entity ID (UEI) | 12 characters; status = Active |
| CAGE Code | 5 characters; status = Active |
| Physical Address | Current |
| EFT / Banking Info | Current (controller / treasurer verifies) |
| TIN | Matches the firm's IRS TIN (controller verifies) |

If **any** of the above shows ❌, **stop and fix before continuing.** SAM updates take 3–10 business days to propagate. With submission on 6/22, the latest acceptable start date for a fix is **2026-06-12** (10 business days out). Any fix started after 6/12 may not propagate in time.

### Step 4 — Verify Reps & Certs are Within the Annual Cycle

- Reps & Certs in SAM expire 12 months after the last update.
- Find the "Last Updated" date on the Reps & Certs page.
- If the date is **older than ~11 months** (i.e., the renewal will fall due before 6/22), **refresh now**. Refresh takes 30–90 minutes for a small firm with no rep changes.
- If the date is within the last 11 months and no firm circumstances have changed (entity name, NAICS list, size status, etc.), no refresh is needed — just verify the rep answers below.

### Step 5 — Verify NAICS 236220 is Registered + Size = Small

- Navigate to **Goods and Services** → NAICS Codes
- Verify **236220 — Commercial and Institutional Building Construction** is in the registered NAICS list
- For NAICS 236220, verify the firm's small-business status is **Small** (under $45.0M average annual receipts over the trailing 3 years per SBA size standard)
- If the firm has grown above $45.0M and incorrectly still asserts Small, **do not submit this bid** — it is a 100% Small Business set-aside and a non-small firm is ineligible regardless of any other factor.

### Step 6 — Verify the FAR 52.204-8 Reps & Certs (Section K of the solicitation)

Each of the following is a SAM-resident rep that must be **current and accurate**. Each one is also listed in RFP §K. Walk through each one in SAM and verify the answer:

| FAR clause | Topic | Expected answer (typical small TX construction firm) |
|---|---|---|
| 52.203-2 | Certificate of Independent Price Determination | ✓ (default true) |
| 52.203-11 | Certification & Disclosure re: Payments to Influence Federal Transactions | "Has not / will not" (lobbying) |
| 52.203-18 | Prohibition on Contracting with Entities that Require Confidentiality Agreements | "Does not / will not require" |
| 52.204-3 | Taxpayer Identification | ✓ TIN provided |
| 52.204-5 | Women-Owned Business (other than Small Business concerns) | Per firm status |
| 52.204-17 | Ownership or Control of Offeror | Disclose if foreign-owned or has ≥ 50% control |
| 52.204-20 | Predecessor of Offeror | Disclose any predecessor under same TIN |
| 52.204-24 | Representation Regarding Certain Telecommunications and Video Surveillance Services or Equipment (Section 889) | "Does not use" + "Will not provide" |
| 52.204-26 | Covered Telecommunications Equipment or Services — Representation | Same as -24 |
| 52.204-29 | FASCSA Orders Representation and Disclosures | "Reasonable inquiry conducted; does not propose to use covered articles/sources" |
| 52.209-2 | Prohibition on Contracting with Inverted Domestic Corporations | "Is not" inverted |
| 52.209-5 | Certification Regarding Responsibility Matters | Disclose any tax delinquencies, contract terminations, or convictions in prior 3 years |
| 52.209-11 | Representation by Corporations Regarding Delinquent Tax Liability or a Felony Conviction | "No" (typical) |
| 52.214-14 | Place of Performance — Sealed Bidding | (May not apply — this is RFP, not IFB; verify) `[VERIFY VS RFP SECTION K]` |
| 52.215-6 | Place of Performance | Per Block 14 |
| 52.219-1 | Small Business Program Representations | **Small at $45M NAICS 236220 size standard** |
| 52.219-2 | Equal Low Bids | (RFP not IFB; may not apply) |
| 52.222-18 | Certification Regarding Knowledge of Child Labor | "No knowledge of any" |
| 52.222-22 | Previous Contracts and Compliance Reports | List federal contracts > $10K in prior 12 mo |
| 52.222-25 | Affirmative Action Compliance | "Will comply" |
| 52.222-38 | Compliance with Veterans' Employment Reporting Requirements | If firm > 50 employees + federal contracts > $150K, VETS-4212 filed |
| 52.222-48 | Exemption from Application of Service Contract Labor Standards | (Construction, not service — typically N/A) |
| 52.222-56 | Certification Regarding Trafficking in Persons Compliance Plan | Per firm policy (typically "No" — compliance plan needed if foreign-based) |
| 52.223-1 | Biobased Product Certification | Per firm policy |
| 52.223-4 | Recovered Materials Certification | "Will comply" |
| 52.223-9 | Estimate of Percentage of Recovered Material Content | Per material plan |
| 52.225-2 | Buy American Certificate | "Domestic" (default for small TX firm) |
| 52.225-4 | Buy American — Free Trade Agreements — Israeli Trade Act Certificate | "Domestic" |
| 52.225-20 | Prohibition on Conducting Restricted Business Operations in Sudan — Certification | "Does not conduct" |
| 52.225-25 | Prohibition on Contracting with Entities Engaging in Certain Activities or Transactions Relating to Iran | "Does not" |
| 52.226-2 | Historically Black College or University and Minority Institution Representation | If applicable |
| 52.227-6 | Royalty Information | "No royalties claimed" (typical) |
| 52.227-15 | Representation of Limited Rights Data | (Typically N/A for construction) |
| 52.232-33 | Payment by Electronic Funds Transfer — System for Award Management | EFT data current in SAM |
| 52.247-64 | Preference for Privately Owned U.S.-Flagged Commercial Vessels | (Typically N/A for construction) |

**For each:** open the rep in SAM, read the answer, confirm it's still accurate. If anything has changed (new federal contract, new owner, new banking, etc.), update before submission.

### Step 7 — Verify EFT / Banking Info (52.232-33)

- Controller / treasurer verifies: ABA routing, account number, account type
- This is the bank account the government will EFT to post-award; mismatch with IRS-registered TIN blocks payment via IPP

### Step 8 — Verify Points of Contact

- SAM has multiple POC types: Government Business POC, Electronic Business POC, Past Performance POC
- Ensure each is a real, currently-employed person at the firm with a working email and phone
- The Electronic Business POC must be reachable for award-administration questions

### Step 9 — Pull the SAM "Entity Information" PDF

- On the Entity record, click **Entity Information** → **Print** → save as PDF
- This is the document that goes into Volume II as evidence of current SAM registration
- File name suggestion: `SAM_Entity_Information_[Legal_Name]_[YYYY-MM-DD].pdf`
- Save to `../local/` (gitignored)
- Pull a fresh copy within **24 hours of submission** (i.e., on Sunday 6/21 or Monday 6/22 morning)

### Step 10 — Cross-check the SAM record against the Section B Section K reps in the RFP

- Read RFP §K (pp.52–57) end-to-end
- For each clause cited in §K, verify the SAM-resident rep matches the answer that's true for the firm
- If RFP §K asks for a rep that ISN'T in SAM (rare but possible — solicitation-specific reps), prepare to answer it inline in the proposal Volume II per L.2.1.4 / 52.204-8(d): "Offeror has completed the following representations in addition to those resident in SAM..." `[VERIFY VS RFP SECTION K]`

### Step 11 — Run a FASCSA SAM check

- SAM has a FASCSA "Excluded Source List" search — verify no proposed sub or supplier is on it
- For the prime: confirm the firm itself is not subject to a FASCSA order (would have been notified separately)

### Step 12 — Document the pull

Create a 1-page "SAM Reps & Certs Verification Memo" for the firm's internal contract file:

| Field | Value |
|---|---|
| Date of pull | `[USER TO FILL]` |
| Person who pulled | `[USER TO FILL]` |
| SAM registration status | Active |
| Registration expiration | `[USER TO FILL]` |
| Reps & Certs last updated | `[USER TO FILL]` |
| NAICS 236220 registered + small? | Yes |
| Any reps changed since last update? | Yes / No (if Yes, list which) |
| Any SAM amendments to refresh? | Yes / No (if Yes, scheduled completion date) |
| Issues flagged for resolution | `[USER TO FILL]` |
| Signature | `[USER TO FILL]` |

Save to `../local/SAM_Verification_Memo_[YYYY-MM-DD].pdf`.

---

## B. If the SAM record is stale or has problems

Per `../07-risk-register.md` R-01: **a stale SAM record makes the bid non-conforming on its face.** Per FAR 52.204-7 + RFP L.1.0, "to be eligible for contract award the offeror must be registered in SAM's database."

**Fix-cycle reality:**

| Issue | Typical fix time |
|---|---|
| Update Reps & Certs (no entity changes) | 1–3 business days to propagate |
| Update entity name / address (with documentation upload) | 5–10 business days |
| New SAM registration (first time) | 7–15 business days (UEI assigned, then CAGE assigned, then Reps & Certs entered) |
| CAGE code change | 5–10 business days |
| TIN match issue (IRS data mismatch) | 5–20 business days (involves IRS, not just SAM) |

**Latest acceptable start dates from 2026-06-22 submission:**

- Reps & Certs refresh: **2026-06-17** (3 business days out)
- Entity name/address update: **2026-06-08** (10 business days out)
- TIN match issue: **2026-05-29** (15 business days out — this includes today's grace period)

If a fix can't realistically complete in time, the responsible call is to **withdraw and not bid** rather than submit a non-conforming proposal.

---

## C. Output for Volume II

What goes into Volume II's "SAM Reps & Certs reference" section (`02-volume-II-technical-acceptability.md` § B):

1. The signed 1-page "Representations and Certifications" statement per `02-volume-II-technical-acceptability.md` § B
2. The fresh SAM Entity Information PDF (pulled within 24 hours of submission per Step 9)
3. Optionally: any solicitation-specific rep that isn't in SAM and was answered inline per Step 10

That's it. Do NOT include a re-typing of the entire FAR §K rep set — incorporation by reference per 52.204-8(d) is the whole point.

---

## D. Who owns this step

- **Primary:** Contracts admin / Entity Administrator on the SAM record
- **Backup:** Controller / treasurer (for banking + TIN verification specifically)
- **Reviewer:** PM-of-record on the bid (verifies the SAM screenshot before insertion into Volume II)

**Due back:** EOD **Monday 2026-05-24**. If the SAM verification is not green by EOD 5/24, halt all other bid-prep work until it's resolved — there's no point in chasing sub quotes or measurements if the firm can't legally submit the bid.
