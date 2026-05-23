# Volume I — Price Proposal

> Source documents: RFP §B (pp.6–7) + §L.1.1 + §L.2.1.1.A + §L.2.1.2 (pp.63–66) + §M.1.9 (p.73) + Attachment 2 (Bid Schedule, 1 page). CLIN structure source of truth: **`../05-bid-schedule-mapping.md`**. Do not invent CLIN order, descriptions, units, or quantities in this volume; mirror Attachment 2 exactly.

This volume is the *only* thing the CO evaluates for price. Section M.1.9 + L.2.1.2.D: "Any proposal that fails to cite a price for each item ... will be rejected as non-conforming." Treat every CLIN cell as mandatory.

---

## A. Volume I assembly order (one PDF)

| # | Element | Source / template |
|---|---|---|
| 1 | **Cover sheet** (1 page) — solicitation #, project name, offeror name, UEI, CAGE, submission date, "Part I — Price Proposal" | `[USER TO FILL]` from SAM record |
| 2 | **Signed SF 1442** (1 page) — blocks 14–20C completed in ink (or accepted electronic signature equivalent) | See `04-SF-1442-fill-guide.md` |
| 3 | **SF 30 amendment acknowledgments** (one for each issued) | Check SAM.gov daily through 6/22; acknowledge each on SF 1442 block 19 + attach the signed SF 30 page |
| 4 | **Schedule of Prices** (1 page) — 8 CLINs + grand total, in the exact order and unit-of-measure of Attachment 2 | § B below |
| 5 | **Bid Guarantee** — scanned executed bid bond / cashier's check / certified check / postal money order / irrevocable letter of credit / Treasury bond cert (FAR 52.228-1) | See `07-bid-bond-form-template.md` |
| 6 | **Surety capacity / P&P bond commitment letter** — on T-Circular-570 surety letterhead | See `06-bondability-letter-template.md` |
| 7 | **Buy American Certificate (FAR 52.225-4)** — 1 signed page | Standard "no foreign construction material proposed" certificate; `[USER TO FILL]` if any non-domestic items |
| 8 | **Optional cover letter** (≤ 1 page) | Note the Section B "Pelican Island NWR" boilerplate carryover and that CLINs 0001–0008 are bid as published. Do NOT raise exceptions to the SOW in this letter — exceptions belong in pre-submission RFIs only |

Suggested PDF filename: `140FC126R0017_Part_I_Price_Proposal.pdf`. One single PDF (per `00-readme.md` § 4).

---

## B. Schedule of Prices — fill-in template

Paste this into Section B of the offer. Match Attachment 2 verbatim on description, unit, and estimated quantity. Add the **UNIT PRICE** and **AMOUNT** columns. Do NOT add new CLINs, alternates, allowances, or deducts (LPTA forbids per M.1.10).

| ITEM NO. | Bid Item Description (verbatim from Attachment 2) | Unit | Est QTY | Unit Price | AMOUNT |
|---:|---|:---:|:---:|---:|---:|
| 1 | Remove and replace the three overhead sectional doors to include hardware, weather stripping and openers | EA | 3 | $ ____.__ | $ ____.__ |
| 2 | Remove and replace existing light fixtures with LED light fixtures to meet OSHA requirements | JOB | 1 | $ ____.__ | $ ____.__ |
| 3 | Remove all suspended ceiling grids and tiles | JOB | 1 | $ ____.__ | $ ____.__ |
| 4 | Remove and replace the existing three (3) exterior personnel doors with insulated hollow metal doors to include frames, hardware, weather stripping and thresh hold | JOB | 3 ⚠️ | $ ____.__ | $ ____.__ |
| 5 | Terminate, cap and remove existing gas lines from the building | JOB | 1 | $ ____.__ | $ ____.__ |
| 6 | Remove and replace existing gutter system to include and replace down spouts | LF | 110 | $ ____.__ | $ ____.__ |
| 7 | Remove and replace existing roof with new roofing sheets | JOB | 1 | $ ____.__ | $ ____.__ |
| 8 | Remove existing gas fired unit heaters | JOB | 1 | $ ____.__ | $ ____.__ |
|   |   |   |   | **GRAND TOTAL** | **$ ____.__** |

⚠️ Item 4 unit/quantity discrepancy: Attachment 2 lists `Unit: JOB, Est QTY: 3`; RFP p.7 lists `Unit: JOB, Quantity: 1`. RFI #3 in `11-rfi-cover-letter.md` asks the CO to clarify. Until the CO answers, bid as Attachment 2 publishes (`Qty 3 × unit price`).

### Per L.2.1.2.1 — line-item loading rule

> "The line-item price shall include all necessary supervision, management, labor, transportation, equipment, materials, any other direct incidental costs, overhead and profit."

Operationally: **bonds, GCs, insurance, OH, and profit cannot appear as separate lines.** Allocate them across the 8 CLINs proportionally to direct cost. Mechanics + worked example: `../05-bid-schedule-mapping.md` § F.

---

## C. The 4 CLINs that need sub quotes BEFORE this volume is finalized

| CLIN | Scope | Sub-quote source | Outreach email |
|---:|---|---|---|
| **0001** | 3 EA insulated overhead doors w/ chain hoist | OH-door sub (Clopay / Wayne Dalton / CHI distributors) | `../outreach/05-email-sub-quote-overhead-doors.md` |
| **0005** | Gas-line cap + remove (1 JOB) | Texas Railroad Commission–licensed plumbing/gas sub | `../outreach/06-email-sub-quote-gas-line.md` |
| **0006** | 110 LF gutter system + downspouts | Gutter sub or sheet-metal sub | `../outreach/07-email-sub-quote-gutters.md` |
| **0008** | Gas-fired unit heater removal (1 JOB) | Same gas-licensed sub as 0005 typically | Folded into `../outreach/06-email-sub-quote-gas-line.md` |

Target: ≥ 2 quotes per CLIN by **Friday 2026-06-05**. The CLIN 0007 roof line (largest dollar) carries a partial cost-DB hit at `07 41 13` ($14.50/SF seed); pair the cost-DB number with at least one metal-roofing sub quote for sanity check.

---

## D. Bid Guarantee calculation (FAR 52.228-1)

**Penal amount = 20% of bid price OR $1,000,000, whichever is less.**

At the recommended LPTA-thin bid envelope of **$150K–$170K**, the bid bond is:

| Bid envelope | 20% of bid | Penal amount (vs $1M cap) |
|---:|---:|---:|
| $130,000 (LPTA-aggressive) | $26,000 | **$26,000** |
| $150,000 (LPTA-thin low) | $30,000 | **$30,000** |
| $160,000 (LPTA-thin mid — **recommended**) | $32,000 | **$32,000** |
| $170,000 (LPTA-thin high) | $34,000 | **$34,000** |
| $200,000 (cautious) | $40,000 | **$40,000** |

Order the bid bond on Monday 5/24 against a **$34,000 penal amount** (top of recommended envelope, with $2K headroom). If the final bid lands lower, the bid bond is still valid; if higher, you need to increase the bond before submission.

**Acceptable forms** per 52.228-1(c):

1. Bid bond on a Treasury Circular 570–listed surety (most common; standard form is **SF 24** — see `07-bid-bond-form-template.md`)
2. Postal money order
3. Certified check or cashier's check
4. Irrevocable letter of credit from a federally insured financial institution
5. United States bonds or notes
6. Individual surety per FAR 52.228-11 (rare; requires asset pledge; do not use unless the firm has an established individual-surety relationship)

For most small federal contractors with a surety relationship, **SF 24 bid bond** is the default.

---

## E. Per-CLIN price-build worksheet (internal use; do NOT submit)

See `../price-sheet-skeleton.json` for the JSON-shaped per-CLIN cost build. Final flow:

1. **Site visit (5/27 or 5/28)** → measured quantities (roof SF, gutter LF, fixture count, heater count, gas-pipe LF)
2. **Sub quotes (target 6/5)** → unit prices for CLINs 0001, 0005, 0006, 0008; sanity-check CLINs 0002, 0007
3. **Direct-cost subtotal** = Σ (CLIN quantity × unit cost) for the 8 priced CLINs
4. **Apply markup envelope** per `../06-evaluation-strategy.md` § C:
   - General conditions: 8–14%
   - Bonds: 1.5–2.5%
   - Insurance: 2–4%
   - DBA labor-burden uplift: 0–4%
   - Contingency: 3–5% (LPTA-thin)
   - Overhead: 7–10%
   - Profit: 3–6% (LPTA-thin)
   - **Total markup over direct: ~25–40%** (direct-to-bid multiplier ~1.25–1.40)
5. **Allocate markup back across the 8 CLINs proportionally to direct cost** (formula in `../05-bid-schedule-mapping.md` § F). Round each allocated price; force grand-total reconciliation by adjusting CLIN 0007 (the largest line) by ≤ $50.
6. **Sanity check** against the magnitude window: bid should be in $130K–$200K. **Below $100K = unreasonably low** (FAR 15.404-1(d) rejection risk). **Above $200K = competitively dead** on LPTA against an aggressive small-business pool.

---

## F. What NOT to put in Volume I

Adding any of these creates a non-conformance risk on a Pass/Fail evaluation:

- ❌ Contingency line item or allowance line item (LPTA forbids per M.1.10)
- ❌ Alternates or value-engineering deducts (not requested in Section B; M.1.10)
- ❌ Conditional pricing ("our price is $X assuming Y") — fails M.1.10
- ❌ Sliding-scale or escalation language — fails L.2.1.2.E
- ❌ Exceptions to the SOW, specs, or drawings inside the priced proposal — raise as RFI BEFORE submission per L.2.1.1.C
- ❌ A "narrative cover memo" that asserts assumptions the CO would read as deviations — keep the cover letter to procedural notes only (e.g., the Section B Pelican Island boilerplate carryover)
- ❌ References to past performance, past projects, qualifications, or differentiation — those belong in Volume II
- ❌ Pricing details on bonds, insurance, OH, profit as standalone columns — they must be loaded into the 8 CLIN prices per L.2.1.2.1

---

## G. Pre-submission QC checklist (Volume I specifically)

- [ ] SF 1442 blocks 14, 15, 17, 18, 19A–C (if any amendments), 20A, 20B (signed in ink or e-sig), 20C (date) all completed
- [ ] Section B / Attachment 2 has unit price + AMOUNT in every row, 8 rows, plus a GRAND TOTAL
- [ ] Grand Total = sum of the 8 AMOUNT cells (verify with calculator, not formula — typos in single-row totals are the #1 small-bid math error)
- [ ] Bid guarantee penal amount ≥ 20% of grand total (or $1M, whichever less) — verify on receipt of bond
- [ ] Buy American Certificate signed
- [ ] Cover letter (if used) raises NO exceptions
- [ ] All SF 30 amendments issued on SAM.gov for this solicitation are acknowledged on SF 1442 block 19 + attached
- [ ] PDF is bookmarked / table-of-contents'd for the CO's clerk to navigate
- [ ] Filename matches submission convention
