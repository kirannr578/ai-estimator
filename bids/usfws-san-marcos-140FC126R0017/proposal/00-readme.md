# Proposal package — USFWS San Marcos ARC, Sol 140FC126R0017

> **Status: DRAFT — pending SAM.gov verification + site visit + sub quotes + signatures.** This folder contains the proposal-side scaffolding only: forms guides, narrative skeletons, templates, and submission mechanics. No firm-internal data, no priced numbers, and no signed forms live here yet.
>
> Read this first. Then the gate checklist in `../README.md` § PROPOSAL STATUS. Then the volume-by-volume guides below.

---

## 1. What this procurement actually is

- **FAR Part 15 negotiated RFP**, NOT a FAR Part 14 sealed-bid IFB. Despite the "bid bond" language (which is a FAR 52.228-1 *bid guarantee* and applies to both Part 14 and Part 15), this is a Request for Proposal evaluated under the **Lowest Price Technically Acceptable** source selection process.
- **Submission method is EMAIL** (RFP p.3 + L.1.2) — NOT a sealed envelope by courier. There is no public bid opening, no sealed-envelope ceremony. See `10-submission-checklist.md` for the email mechanics.
- The only physical/wet-ink piece that may need to follow electronically-submitted scans is the **original bid bond** with surety's raised seal — most COs accept a scanned PDF of an executed bid bond at the email submission and the original mailed to land within ~2 business days. Confirm with the CO if the firm uses a paper bid bond; if the surety can issue an **electronic bond** (e-bond via SurePath / Tinubu / equivalent), that resolves the paper-original question entirely.

## 2. What's in this folder

| File | Purpose | User action |
|---|---|---|
| `00-readme.md` | This file — package overview | Read first |
| `01-volume-I-price-proposal.md` | SF 1442 fill-in guide + Schedule of Prices structure mapped to the 8 CLINs; bid-bond calculation | Use as the price-volume table of contents |
| `02-volume-II-technical-acceptability.md` | MINIMAL Pass/Fail technical narrative per Section M.1.2 | Insert past-perf + bondability + SAM ref (per `06-evaluation-strategy.md` § F) |
| `03-volume-III-past-performance.md` | Template for 2 prior similar-scope projects per Section M.1.4 | `[USER TO FILL]` for each project |
| `04-SF-1442-fill-guide.md` | Section-by-section guide for SF 1442 (blocks 14–20C) | Use during proposal assembly |
| `05-reps-and-certs-pull-guide.md` | Step-by-step SAM.gov Reps & Certs pull per FAR 52.204-8 | Run on Monday 5/24 |
| `06-bondability-letter-template.md` | Surety letter template (T-Circular-570 surety, P&P commitment at 100%) | Send to surety with `outreach/04-email-bonding-agent.md` |
| `07-bid-bond-form-template.md` | Bid bond / SF 24 mechanics (20% of bid or $1M whichever less) | Order with bonding agent on 5/24 |
| `08-dba-compliance-acknowledgment.md` | DBA WD TX20260254 acknowledgment + WH-347 commitment | Sign with the proposal package |
| `09-site-visit-attendance-memo.md` | Pre-formatted memo template for the 5/27 OR 5/28 site visit | Fill out at the site visit |
| `10-submission-checklist.md` | HARD CHECKLIST: deadline, addresses, subject line, what-if-late | Execute on 6/22 |
| `11-rfi-cover-letter.md` | Cover letter for the consolidated RFI before 6/8 cutoff | Send via `outreach/01-email-tracy-gamble-rfi-consolidated.md` |

## 3. What's NOT in this folder (and shouldn't be committed here)

- Signed forms (sign at submission, file in firm's contracts repository)
- Firm-internal CAGE / UEI / banking / insurance certificate values
- Sub-quote PDFs (store in `../local/` which is gitignored per the workspace `.gitignore` rule `bids/*/local/`)
- Site-visit photos (same — `../local/`)
- The fully-priced Schedule of Prices with real dollar figures (priced just before submission; not committed)

## 4. What's in the envelope on submission day (6/22 by 5:00 PM EDT)

Per Section L.1.1, the proposal is one ZIP / two PDFs by email:

| Part | Contents |
|---|---|
| **Part I — Price Proposal** (single PDF, suggested name `140FC126R0017_Part_I_Price_Proposal.pdf`) | (a) Signed SF 1442 (blocks 14–20C); (b) Schedule of Prices (Section B / Attachment 2) with all 8 CLINs + grand total; (c) Any SF 30 amendments acknowledged on SF 1442 block 19; (d) Executed bid guarantee per FAR 52.228-1 (scanned bid bond / cashier's check / etc.); (e) Surety capacity / P&P commitment letter |
| **Part II — Technical Acceptability** (single PDF, suggested name `140FC126R0017_Part_II_Technical.pdf`) | (a) Past Performance Volume — 2 projects per L.2.1.3.(a); (b) Bondability letter per L.2.1.3.(b); (c) SAM Reps & Certs incorporation statement per L.2.1.4 + 52.204-8(d) + fresh SAM entity printout; (d) DBA compliance acknowledgment (`08-dba-compliance-acknowledgment.md`); (e) optional cover letter noting the Section B "Pelican Island" boilerplate carryover and treating CLINs 0001–0008 as binding |

**No technical-approach narrative. No QC plan. No Gantt chart. No safety plan.** None of these are required at proposal stage; adding them creates risk of an unintended exception. See `02-volume-II-technical-acceptability.md`.

## 5. What's missing — the 5 gates blocking submission

In order of severity. None of these can be papered over in this folder.

1. **SAM.gov verification** — the entity must be Active with NAICS 236220 small-asserted at $45M, current Reps & Certs (annual cycle), CAGE active, EFT current, TIN matching IRS. **Without this, the proposal is technically unacceptable per L.1.0 + FAR 52.204-7 regardless of price.** Due back EOD Mon 5/24 (see `outreach/08-internal-sam-gov-verification-checklist.md`).
2. **Site visit** — 5/27 OR 5/28, 8 AM – 4 PM CDT. Resolves takeoff for the largest dollar line (CLIN 0007 roof SF) and 3 smaller lines. RSVP per `outreach/03-email-katherine-bockrath-site-visit-rsvp.md`.
3. **Four sub quotes** — CLINs 0001, 0005, 0006, 0008 have no cost-DB hit. Solicit ≥ 2 vendors per CLIN by Wed 5/27; quotes back by Fri 6/5. See `outreach/05-` through `07-` and `../05-bid-schedule-mapping.md` § A.
4. **CO RFI responses** — 7 questions consolidated in `11-rfi-cover-letter.md`; send by Mon 6/1 to allow CO time to respond before the 6/8 cutoff.
5. **Bonding commitment + bid bond** — bid guarantee (20% of bid or $1M, whichever less) + P&P commitment letters (100% each). Order Mon 5/24; in hand by Wed 6/17 EOD. See `06-bondability-letter-template.md` + `07-bid-bond-form-template.md`.

## 6. Deadline math

| Event | Date / Time | Time-from-now |
|---|---|---|
| **SAM verification gate** | Mon 5/24 EOD | T+1 day |
| Sub-quote RFQs out | Mon 5/25 | T+2 |
| Site visit | Wed 5/27 OR Thu 5/28 | T+4 / T+5 |
| Sub quotes returned | Fri 6/5 | T+13 |
| **RFI cutoff** | Mon 6/8, 5:00 PM EDT | T+16 |
| Bid bond + P&P letters in hand | Wed 6/17 EOD | T+25 |
| Internal QC (2-person) | Fri 6/19 | T+27 |
| **Proposal submission** | Mon 6/22, ≤ 5:00 PM EDT (recommended 4:30 PM EDT) | T+30 |

After submission, the offer must remain valid ≥ 90 calendar days per RFP p.3 block 13d (through approximately 2026-09-20).

## 7. LPTA discipline reminder

This is **not** the TAMU CSP or ASU RFCSP. Every page of narrative added to this proposal is wasted hours **and** a risk of introducing an exception that flips technical-acceptability from Pass to Fail. The minimum-conforming proposal Passes; nothing beyond Pass moves the award.

If you find yourself writing a 5-page "approach narrative" or a multi-page "why us," **stop**. Re-read `../06-evaluation-strategy.md` § B "What doesn't matter (don't burn hours here)."

## 8. Pointer back to the prep workspace

- Solicitation overview + key dates + contacts: `../01-overview.md`
- Comprehensive proposal-side checklist (already exists): `../02-bid-prep-checklist.md` § A + § I
- CLIN mapping + pricing strategy + cost allocation: `../05-bid-schedule-mapping.md`
- LPTA strategy + Pass/Fail definition: `../06-evaluation-strategy.md`
- FAR clauses worth flagging: `../08-far-clauses-flags.md`
- DBA WD pointer + payroll mechanics: `../prevailing-wages.md`
- Risks: `../07-risk-register.md`
- Backwards-planned timeline: `../timeline.md`

All firm-internal data carries `[USER TO FILL]`. All federal procedural details I have not personally re-verified against the live RFP text carry `[VERIFY VS RFP SECTION X]`.
