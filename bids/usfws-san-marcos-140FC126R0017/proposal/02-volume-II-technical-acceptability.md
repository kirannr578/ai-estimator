# Volume II — Technical Acceptability

> **The shortest defensible Volume II Passes.** Section M.1.4 + M.1.2: technical acceptability is Pass/Fail; tradeoffs between price and performance are *explicitly forbidden*. Every additional page of prose is a risk of introducing an unintended exception that flips Pass → Fail, with zero corresponding evaluation upside.
>
> Source documents: RFP §L.2.1.1.A + §L.2.1.3 + §L.2.1.4 (pp.64–66) + §M.1.2 + §M.1.4 + §M.1.6 + §M.1.7 (pp.70–72). Strategy + Pass criteria already enumerated in `../06-evaluation-strategy.md` § E + § F.

This volume is **3 pages, maximum**. Five if a bondability letter wraps to a second page or a SAM printout exceeds one page. Do not write a sixth.

---

## A. Volume II assembly order (one PDF)

| # | Element | Page count | Source / template |
|---|---|:---:|---|
| 1 | **Cover sheet** | 1 | Solicitation #, project name, offeror name, UEI, CAGE, "Part II — Technical Acceptability" |
| 2 | **Past Performance Volume** (per L.2.1.3.(a) + M.1.4.B.1) | ≤ 2 | `03-volume-III-past-performance.md` — 2 prior projects, table + 1-paragraph each |
| 3 | **Bondability Letter** (per L.2.1.3.(b) + M.1.4.B.2) | 1–2 | Insert surety's signed letter on T-Circular-570 surety letterhead (`06-bondability-letter-template.md`) |
| 4 | **SAM Reps & Certs reference** (per L.2.1.4 + 52.204-8(d)) | 1 | § B below + fresh SAM "Entity Information" printout |
| 5 | **DBA Compliance Acknowledgment** (operational courtesy; not strictly required at proposal stage) | 1 | `08-dba-compliance-acknowledgment.md` |

Total target: **3–5 pages**. If you find yourself past 5, audit each page for "does this move Pass/Fail?" and cut.

Suggested PDF filename: `140FC126R0017_Part_II_Technical.pdf`. One single PDF.

---

## B. SAM Reps & Certs incorporation page (L.2.1.4 + FAR 52.204-8(d))

Paste this on a single page. Sign and date.

> **Representations and Certifications**
>
> Offeror represents that the representations and certifications required under FAR 52.204-8 (Annual Representations and Certifications) are current, accurate, complete, and applicable to this solicitation, and have been entered electronically in the System for Award Management (SAM) at `https://www.sam.gov`.
>
> Offeror invokes incorporation by reference under FAR 4.1201 and FAR 52.204-8(d). **No changes** are made to those representations and certifications for purposes of this solicitation.
>
> **Offeror identification:**
>
> - Legal entity name: `[USER TO FILL]`
> - DBA / trade name (if any): `[USER TO FILL]`
> - Unique Entity ID (UEI): `[USER TO FILL: 12-character SAM UEI]`
> - CAGE code: `[USER TO FILL]`
> - SAM registration status: Active
> - SAM registration expiration date: `[USER TO FILL: as shown in SAM "Entity Information"]`
> - Reps & Certs last updated: `[USER TO FILL: must be within last 12 months]`
> - NAICS registered: 236220 — Commercial and Institutional Building Construction
> - Small business size status under NAICS 236220 ($45.0M size standard): **Small**
> - 100% Total Small Business Set-Aside per FAR 52.219-6: Offeror is a small business and is eligible to submit
>
> **By signing below, the undersigned, on behalf of the Offeror, certifies the above.**
>
> Signature: ________________________________________  Date: __________
>
> Name (typed): `[USER TO FILL]`
> Title: `[USER TO FILL]`

**Attach** a fresh SAM "Entity Information" printout dated within 24 hours of submission (pulled per `05-reps-and-certs-pull-guide.md`).

---

## C. What is required to Pass

Re-stated from `../06-evaluation-strategy.md` § E so the assembler can tick each one without context-switching.

Per L.2.1.1 – L.2.1.5 + M.1.4.B, here is the exact minimum to receive a "Pass" rating on technical acceptability:

| # | Element | Document | Status check |
|---:|---|---|---|
| 1 | Signed SF 1442 (blocks 14–20C) | `04-SF-1442-fill-guide.md` | Live with Volume I |
| 2 | All SF 30 amendments acknowledged | Check SAM daily through 6/22 | Live with Volume I |
| 3 | All 8 CLINs priced + grand total | `01-volume-I-price-proposal.md` § B | Live with Volume I |
| 4 | Past Performance — 2 examples, recent (last 3 yrs), similar size + scope + complexity | `03-volume-III-past-performance.md` | `[USER TO FILL]` |
| 5 | Bondability proof — surety commitment letter for $250K-magnitude P&P bonds | `06-bondability-letter-template.md` | Order with bonding agent |
| 6 | SAM Reps & Certs current per 52.204-8(d) | § B above | Verify Mon 5/24 |
| 7 | Bid Guarantee in proper form per 52.228-1 | `07-bid-bond-form-template.md` | Order Mon 5/24 |
| 8 | No exceptions to the SOW or specs in the priced proposal | This entire volume + Volume I cover letter | Audit before submission |

That's the entire Pass test. Nothing beyond moves the needle.

---

## D. Negative-narrative risks (things to actively NOT write)

Re-stated from `../06-evaluation-strategy.md` § G. Each of these can convert a Pass into a Fail on a literal reading:

1. **"We assume X"** where X is a deviation from the SOW — that's an exception. Raise as RFI before submission, or absorb in pricing without comment.
2. **"Our price is contingent on Y"** — fails M.1.10 (firm-fixed-price only; no contingencies).
3. **"As an alternate, we propose Z"** — fails M.1.10 (no alternates in the bid schedule).
4. **"We have not previously worked at a USFWS facility, but..."** — adds a Fail vector. State your relevant past performance affirmatively; let the CO judge similarity. Do not preemptively address dissimilarity.
5. **A QC plan, safety plan, schedule narrative, or Gantt chart** — not requested at proposal stage. Adds 0 Pass-points; can add Fail-points if the schedule narrative implies a deviation from the 60-day completion mandate.
6. **A "Why us" pitch or differentiating-qualifications page** — not requested; LPTA explicitly does not reward differentiation. Pure waste.
7. **Discussion of subcontractors by name** — only relevant if you're invoking subcontractor past performance per M.1.4.B.f. If so, include the sub's relevant project; if not, do not name subs.
8. **Pricing references in Volume II** — keep all dollar figures in Volume I. Volume II is non-priced.

---

## E. Optional content that's defensible (but skip unless it Passes a value test)

These are **NOT required** by Section L; include only if there's a specific reason:

- **Subcontractor past performance** (M.1.4.B.f): include only if the firm's own 2 references are thin on similar-scope work. If included, ≤ 1 paragraph per sub.
- **Adverse past-performance response** (M.1.7): include only if the firm has any unresolved CPARS adverse-performance flag. Address proactively — one sentence: what happened, what was done, current status. **Skip this section if there's nothing to address; raising "we have no adverse past performance" preemptively reads as defensive.**
- **Quality Control Plan reference** (RFP §E ambiguous on proposal-stage vs award-stage): the safer read is that QCP is delivered at preconstruction conference, not at proposal. If you choose to include a 1-page QCP outline at proposal stage anyway, keep it generic and non-binding — do NOT commit to specific procedures the firm wouldn't execute.

---

## F. The 1-paragraph rule for past-performance write-ups

For each past project, ONE paragraph of 3–4 sentences after the data table:

> "[Project name] for [owner], completed [month/year], contract value $[X]. Scope included [1-sentence list — emphasize overlap with the San Marcos SOW: overhead doors, metal roofing, light electrical, gutters, gas-line modifications, ceiling demo]. Performance was [in-budget / on-schedule] with [zero / one resolved] CPARS-tracked deficiencies. Project demonstrates the firm's capability to deliver a federal small-construction renovation of similar size, scope, and complexity to the San Marcos ARC requirement."

Template in `03-volume-III-past-performance.md`.

**Do not** write a 5-paragraph case study. Do not include photos. Do not include client testimonials. None of these move the Pass test.

---

## G. Cover-page template (paste at front of Volume II)

```
PROPOSAL FOR SOLICITATION 140FC126R0017
San Marcos Aquatic Resources Center
Rehabilitate Shop & 2 Stall Garage Building
USFWS, Construction A/E Team 1

PART II — TECHNICAL ACCEPTABILITY

Offeror:             [USER TO FILL: legal entity name]
UEI:                 [USER TO FILL]
CAGE:                [USER TO FILL]
NAICS:               236220 (Commercial & Institutional Building Construction)
Size status:         Small (under $45.0M 3-year average annual receipts)
Submission date:     June 22, 2026
Authorized by:       [USER TO FILL: name + title]
Email:               [USER TO FILL]
Phone:               [USER TO FILL]

Contents:
 - Past Performance Volume (2 projects per FAR L.2.1.3.(a))
 - Bondability Letter (per FAR L.2.1.3.(b))
 - SAM Representations & Certifications reference (per FAR L.2.1.4 + 52.204-8(d))
 - DBA Compliance Acknowledgment (WD TX20260254, Hays County, Building)
```

---

## H. Pre-submission QC checklist (Volume II specifically)

- [ ] Cover page complete
- [ ] Exactly 2 past-performance projects, each with owner / contact / $ value / completion date / scope summary
- [ ] Bondability letter on T-Circular-570 surety letterhead, signed
- [ ] SAM Reps & Certs invocation page signed + fresh SAM printout attached
- [ ] DBA acknowledgment signed
- [ ] Total page count ≤ 5
- [ ] Zero exceptions to the SOW or specs anywhere in this volume
- [ ] Zero pricing references anywhere in this volume
- [ ] PDF bookmarked
- [ ] Filename matches submission convention
