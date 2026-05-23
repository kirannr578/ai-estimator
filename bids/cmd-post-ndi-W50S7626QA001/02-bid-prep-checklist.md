# Bid prep checklist — W50S7626QA001

A **gate-by-gate**, owner-assigned, day-by-day checklist. Every line is either ✅ done, ☐ pending, or ⚠️ blocked-on-external. The checklist is built **backwards from 04 JUN 2026** with explicit fix-by deadlines.

## A. SAM.gov registration — Gate 1 (must be ✅ before any other gate; non-current SAM = non-responsive offer)

Owner: Contracts admin / firm Entity Administrator. Deadline: **Mon 2026-05-25 EOD** to allow SAM.gov 3–10 business-day update cycle if anything is wrong.

| # | Item | Action | Status |
|---:|---|---|---|
| 1 | UEI active | Log in to `https://sam.gov/`; under Entity Information → confirm UEI status = **Active** and not expired | ☐ \[USER TO VERIFY\] |
| 2 | NAICS 236220 registered | Under "Goods and Services" → confirm 236220 (Commercial and Institutional Building Construction) is in the Registered NAICS list | ☐ \[USER TO VERIFY\] |
| 3 | NAICS 236220 small-business asserted at $45M size standard | Under "Size Metrics" → confirm small-business assertion at **$45.0M** for 236220 | ☐ \[USER TO VERIFY\] |
| 4 | Reps & Certs (FAR 52.204-8 / 52.212-3) current within 12-month annual cycle | Under "Representations and Certifications" → confirm last update date is < 12 months ago. If > 12 months, **update immediately** — typical processing 24–72 hours | ☐ \[USER TO VERIFY\] |
| 5 | CAGE code active | Under Entity Information → confirm CAGE is current and matches the legal entity | ☐ \[USER TO VERIFY\] |
| 6 | EFT / banking current | Under Financial Information → confirm routing + account on file matches current banking; a stale EFT entry will block payment under FAR 52.232-33 | ☐ \[USER TO VERIFY\] |
| 7 | TIN matches IRS records | Under Entity Information → confirm TIN/EIN displays "Matches" or equivalent | ☐ \[USER TO VERIFY\] |
| 8 | DFARS 252.204-7016 Covered Defense Telecommunications rep complete | Under Reps & Certs → confirm 252.204-7016 representation is on file (Section K of the solicitation requires this) | ☐ \[USER TO VERIFY\] |
| 9 | DFARS 252.204-7019 NIST SP 800-171 DoD Assessment Requirement | Per Section L 252.204-7019 (incorporated by reference) — confirm the firm has a current Basic Assessment in SPRS (Supplier Performance Risk System) at `https://www.sprs.csd.disa.mil/` for any covered defense info handling. **Even for a small renovation contract, DFARS 252.204-7019 + 252.204-7012 are clauses incorporated by reference** — confirm current SPRS NIST 800-171 score | ☐ \[USER TO VERIFY\] |
| 10 | DFARS 252.204-7024 Supplier Performance Risk System notice | Confirm SPRS access established (system notice, not a positive action — verify access is functional) | ☐ \[USER TO VERIFY\] |
| 11 | FAR 52.204-13 SAM Maintenance | No action — automatic if (1)–(10) are current | n/a |
| 12 | Active Exclusions / debarment screen | Under "Exclusions" search the entity name + UEI + key principals — confirm no active exclusions | ☐ \[USER TO VERIFY\] |

> ⚠️ **Latest acceptable fix-start for any SAM defect: Tue 2026-05-26.** SAM updates can take 3–10 business days; with closing 04 JUN, anything started after Tue may not clear in time.

## B. SF 1442 fill — Gate 2

Owner: Authorized signer (Officer / President / VP of the firm). Deadline: **Wed 2026-06-03 EOD** (so the file is ready to attach to the submission email Thu morning).

See `proposal/04-SF-1442-fill-guide.md` for the section-by-section guide. Block-by-block summary:

| Block | Field | Source / value |
|---:|---|---|
| 14 | Name and Address of Offeror (incl. ZIP) | \[USER TO FILL — registered legal name and SAM-registered address\] |
| 15 | Telephone Number | \[USER TO FILL\] |
| 16 | Remittance Address | \[USER TO FILL — only if different from Block 14\] |
| 17 | Acceptance period (cal days after offer due date) | **Insert the acceptance period from Block 13d (default 90 if Block 13d is blank).** If unsure, write **90** to be safe. |
| 18 | Furnishing P&P Bonds — YES/NO | **YES** (FAR 52.228-15 makes this required if award > $150K, which is virtually certain) |
| 19 | Acknowledgment of Amendments | **W50S7626QA0010001** dated \[the SF 30 effective date — VERIFY VS SF 30 BLOCK 16C — likely on/about 2026-05-12 since drawings (20260512) were added\] |
| 20a | Name and title of authorized signer | \[USER TO FILL\] |
| 20b | Signature | \[USER TO SIGN\] |
| 20c | Offer date | Date of submission |
| 22 | Total amount | Total of CLIN 0001 + CLIN 0002 (both CLINs offered together; partial-award is the Government's right per Section L (a)(1), but the offeror submits prices for both) |

## C. Schedule of Prices (CLIN-by-CLIN firm-fixed pricing)

Owner: Lead estimator. Deadline: **Wed 2026-06-03 EOD.**

Section L paragraph (a)(1) verbatim: *"The Contractor shall submit a firm-fixed-price proposal, clearly separated into the following Contract Line-Item Numbers (CLINs). Each CLIN shall include all labor, materials, equipment, and services necessary to complete the project as specified in the Statement of Work."*

| CLIN | Description | Pricing | Source |
|---|---|---|---|
| 0001 | B1672 Command Post Relocation (Quantity 1 Job, Firm Fixed Price) | $\[USER TO FILL — see `05-bid-schedule-mapping.md` and `takeoff-template.json`\] | Section B |
| 0002 | B1675 Nondestructive Inspection (NDI) Room (Quantity 1 Job, Firm Fixed Price) | $\[USER TO FILL\] | Section B |
| **Total** | | **$\[USER TO FILL\]** | |

> Each CLIN priced INDEPENDENTLY — Government may award one without the other.

## D. Required submittals with offer (Section L)

Owner: Lead estimator + PM. Deadline: **Wed 2026-06-03 EOD.**

| # | Submittal | Format | Source |
|---:|---|---|---|
| 1 | Completed SF 1442 (blocks 14, 15, 17, 18, 20a–c; blocks 16, 19 if applicable) | PDF (signed/scanned) | Section L (a)(1) |
| 2 | Firm-fixed price by CLIN | Embedded in SF 1442 + Schedule of Prices | Section L (a)(1) |
| 3 | **List of equipment, materials, and labor disciplines** ("RSMeans output list or similar product") | PDF — itemized list | Section L (a)(1) — Subfactor 1 evaluation per Section M (a)(iv)(a) |
| 4 | **Project schedule** showing realistic milestones for managing the activities, in logical sequence, fitting inside 90 calendar days | PDF — Gantt or task list | Section L (a)(1) — Subfactor 2 evaluation per Section M (a)(iv)(b) |
| 5 | Bid bond — SF 24 (scanned copy attached) | PDF | Section L (a)(2) NOTE + FAR 52.228-1 + Section L p.47 |
| 6 | Acknowledgment of Amendment 0001 | Either by completing SF 30 blocks 8 + 15 OR by acknowledging on SF 1442 Block 19 | SF 30 Block 11 + Section L paragraph (a) |
| 7 | Reps & Certs — by reference to active SAM.gov filing (per DFARS 252.204-7998 Alternate A paragraph (g)) | No separate document — assert via SF 1442 submission | Section K — DFARS 252.204-7998 Alternate A |

## E. Bonding — Gate 3

Owner: Bonding agent (firm's surety / broker). Deadline: **bid bond ready by Wed 2026-06-03 EOD.**

| # | Item | Detail | Owner | Status |
|---:|---|---|---|---|
| 1 | Notify bonding agent | Email surety with project number, bid envelope ($\[USER TO FILL\]), CLIN structure, and submission deadline 04 JUN 2026 | PM (today / Mon 5/25) | ☐ — see `outreach/03-email-bonding-agent.md` |
| 2 | Bid bond — SF 24, **20% of bid OR $3,000,000, whichever is less** | T-Circular-570 surety (Treasury-listed); firm commitment | Surety | ☐ |
| 3 | Performance Bond commitment letter — **100% of award** | T-Circular-570 surety; bondability letter (per `proposal/06-bondability-letter-template.md`) — required for inclusion in the proposal IF the firm is unknown to the CO and wants to demonstrate bondability up front; otherwise required at award | Surety | ☐ |
| 4 | Payment Bond commitment letter — **100% of award** | Same surety; same letter | Surety | ☐ |
| 5 | Aggregate single-project / single-customer capacity confirmed | Surety confirms in writing they can issue at the bid envelope | Surety | ☐ \[USER TO VERIFY\] |

> Bond mechanics for this contract — per FAR 52.228-15 and Section L:
> - Bid bond is **mandatory** with the offer (NOT optional) per Section L (a)(2) NOTE: *"NOTE: If a bid bond is required (SF1442, Page 1, Block 13B), scanned copies must be submitted with submission of the quote. The bid bond must be a SF 24."* **\[VERIFY VS SF 1442 BLOCK 13B — confirm "is required" is checked\]**.
> - At a $200K bid: bid bond = $40K penal amount.
> - At a $500K bid: bid bond = $100K penal amount.
> - Bid-bond cap is $3M; not a binding constraint at this magnitude.

## F. Insurance — Gate 4

Owner: Insurance broker. Deadline: **certificates evidencing minimums on file before award (NOT before bid)** — but secure broker confirmation of capacity now.

Per Section L paragraph (g):

| Insurance type | Minimum |
|---|---|
| Workers' Compensation | **$100,000** (except in monopolistic states) |
| Comprehensive General Liability | **$500,000 per occurrence** for Bodily Injury |
| Comprehensive Automobile Liability | **$200,000 per person + $500,000 per accident BI; $20,000 PD** |

> Standard ANG / federal minimums; firms with broader CGL/Auto already on file (typical $1M/$2M CGL) easily exceed the floor.

## G. Site visit — Gate 5

Owner: PM. Deadline: **request submitted Mon 2026-05-25 EOD.**

Per SOW §4.3: *"The Contractor is urged to conduct a site visit prior to submission of any offer to verify existing conditions, understand site constraints, and confirm work requirements. The 136th Civil Engineer Squadron (CES) will coordinate base access for required personnel."*

> ⚠️ **Site-access 14-business-day rule conflict.** Per SOW §7: *"The Contractor shall submit all base access requests to the Government point of contact no less than fourteen (14) business days prior to the required access date."* Counting backwards from 04 JUN 2026 (Wed) and accounting for Memorial Day (Mon 2026-05-26) and weekends: 14 business days backward = roughly **Tue 2026-05-13** — already in the past. **A standard site visit before bid close is not possible without an exception from MSgt Jones / MSgt Meeks (136 CES Operations).**

**Mitigation actions:**
1. Email both 136 CES Operations Managers (MSgt Jones + MSgt Meeks) AND the PE/PM (Maj Norton + Mr. Shamburger) with a polite exception request — see `outreach/02-email-136-aw-facility-poc.md`. Include: full names, dates of birth, last 4 SSN of attendees; vehicle make/model/license; firm CAGE; project number DDPM262101.
2. If exception denied: bid on field-verified-after-award basis with a 5–8% added contingency for unknowns; document in the offer that "Field verification per FAR 52.236-3 will occur post-award; any Differing Site Conditions per FAR 52.236-2 will be addressed by mod."
3. Use the existing-conditions photo PDFs as a partial substitute (`Alter CP and NDI_B1675 NDI Rm Photos REFERENCE ONLY.pdf` and `Altter CP and NDI_B1672 CP Rm Photos REFERENCE ONLY.pdf`) — these are explicitly labeled REFERENCE ONLY by the CO.
4. Use Google Earth / publicly available NAS-JRB Fort Worth imagery to confirm building 1672 + 1675 footprints and access routes.

## H. RFI — Gate 6

Owner: Lead estimator. Deadline: **Mon 2026-06-01 EOD** (3 business days before close gives the CO time to respond OR amend).

Per Section L paragraph (f) verbatim: *"Requests for Information (RFIs): Requests for Information must be submitted in writing through email to 136.AW.MSC@us.af.mil. RFIs will not be accepted after the date and time stated on the solicitation (SAM.gov) notice, unless a response is deemed to be in the best interests of the Government."*

> **\[VERIFY VS SAM.GOV NOTICE — RFI cutoff date.\]** The Section L language references "the date and time stated on the solicitation (SAM.gov) notice" — this is the RFI deadline shown on the SAM.gov posting itself, not on the SF 1442 cover. **Pull the SAM.gov posting** and confirm the RFI date.

Consolidated RFI questions (max 4–6) — see `proposal/11-rfi-cover-letter.md` for the draft. Topics:
1. Confirm closing date 04 JUN 2026 + the local time in Block 13.
2. Confirm site-visit accommodation given the 14-business-day-pre-access conflict with closing window.
3. Clarify B1675 NDI Room scope — is the renovation purely space-prep for future Government-installed NDI equipment, or are there shielding / EMI / lead-line / vibration-control requirements not on Sheet 2?
4. Confirm whether the existing fire-suppression system in B1672 / B1675 is wet-pipe, dry-pipe, or pre-action — for sub-quote sizing.
5. Confirm whether AFFF-room demolition involves any PFAS-impacted residue requiring TCEQ-permitted disposal beyond the SOW §9 (Disposal) standard universal-waste handling.
6. Confirm whether NAICS code is **236220** at $45M size standard (per cover-page block).

## I. Sub quotes — Gate 7

Owner: PM. Deadline: **Wed 2026-06-03 EOD.**

Sub categories with named outreach drafts under `outreach/`:

| Sub | Outreach draft | Why it's specialty / why we don't self-perform |
|---|---|---|
| Electrical (incl. emergency lighting, fire alarm, low-voltage rough-in) | `outreach/05-email-sub-quote-electrical.md` | UFC 3-501-01 compliance; secure-area conduit and comm-box rough-in; battery-backup egress; DOE/AHJ inspection coordination |
| Mechanical / HVAC (duct mod + diffuser + return + override + balancing) | `outreach/06-email-sub-quote-mechanical-hvac.md` | NAS-JRB-specific HVAC controls; balance-and-test-and-report deliverable |
| Doors + frames + secure hardware (Stanley/Best Lock-Core compatible, steel-sheet reinforced solid-wood doors) | `outreach/04-email-sub-quote-secure-doors-hardware.md` | Specialty hardware; security finish (anti-pin / anti-bolt); credential window / impact-rated mesh-reinforced 1-way window |
| Fire suppression (existing system modification to encompass new partitions) | (covered under electrical/mech sub or stand-alone — \[USER TO DECIDE\]) | NAS-JRB AHJ; system documentation update |

`outreach/07-internal-sam-gov-verification.md` is the internal SAM.gov readiness checklist; if the firm already verified SAM as part of a prior bid (e.g., USFWS San Marcos 140FC126R0017 within the last 12 months), much of that confirmation can be reused.

## J. Submission — Gate 8 (final gate)

Owner: PM + authorized signer. Deadline: **Thu 2026-06-04, time \[VERIFY BLOCK 13 LOCAL TIME — likely 1500 CDT, plan for 1200 CDT\].**

| # | Action | Owner |
|---:|---|---|
| 1 | Final SF 1442 + Schedule of Prices, signed | Authorized signer |
| 2 | Equipment / Materials / Labor list (RSMeans-style export) | Estimator |
| 3 | Project schedule (Gantt PDF, 90-day POP, both CLINs) | PM |
| 4 | Scanned bid bond SF 24 | Bonding agent → PM |
| 5 | Acknowledgment of Amendment 0001 (SF 1442 Block 19 OR SF 30 returned) | Authorized signer |
| 6 | One submission email to **`136.AW.MSC@us.af.mil`** with subject line: `Quote — W50S7626QA001 — Alter Command Post + NDI Room — \[Firm Name + UEI\]` | PM |
| 7 | Submission timestamp before Block 13 close time (build a 3-hour buffer; **send by 1200 CDT**) | PM |
| 8 | Save sent-email confirmation + delivery receipt for the file | PM |
| 9 | Receive bounce / non-delivery receipt? — escalate to bonding agent + PE phone (Maj Norton 817-852-3323) immediately | PM |

See `proposal/10-submission-checklist.md` for the full mechanics.

## K. Hard rules

- All firm-internal data is `[USER TO FILL]` until verified.
- All federal-procedural details that depend on the actual cover-page form-field state of the SF 1442 / SF 30 (closing time, NAICS field, Block 13B bid-bond required, Block 13d acceptance period, SF 30 effective date) are tagged `[VERIFY VS SOL ...]` and require a 5-minute visual check by opening the PDF in a renderer that handles AcroForms.
- No bid is submitted before all 8 gates are ✅.
- Any single ⚠️ blocked-on-external is escalated to the user the day-of, not stockpiled.
