# Bid Bond — FAR 52.228-1 (Standard Form 24)

> Source: FAR 52.228-1 (Bid Guarantee, SEP 1996) + RFP §L.2.1.5 (p.66) + GSA Standard Form 24 instructions.
>
> **What this is:** The Bid Guarantee accompanying Volume I per L.2.1.5. Per FAR 52.228-1(c), the penal amount is **20% of the bid price OR $1,000,000, whichever is less**.
>
> **Form:** Standard Form 24 (Bid Bond) is the customary instrument. Other acceptable forms per 52.228-1(c) are listed below.

---

## A. Penal amount calculation

| Bid envelope | 20% of bid | Penal amount (vs $1M cap) |
|---:|---:|---:|
| $130,000 (LPTA-aggressive) | $26,000 | **$26,000** |
| $150,000 (LPTA-thin low) | $30,000 | **$30,000** |
| $160,000 (LPTA-thin mid — **recommended target**) | $32,000 | **$32,000** |
| $170,000 (LPTA-thin high) | $34,000 | **$34,000** |
| $200,000 (cautious) | $40,000 | **$40,000** |

**Order recommendation:** order the bid bond at a penal amount of **$34,000** (top of recommended LPTA-thin envelope). If the locked bid lands lower, the bond is still valid. If higher, the bond must be re-issued at the new penal amount before submission — this takes 1–2 business days, so finalize the bid amount by **Friday 2026-06-19** to allow re-issue time if needed.

---

## B. Acceptable forms (FAR 52.228-1(c))

The CO will accept any of the following as the bid guarantee:

| Form | Description | Practicality for this bid |
|---|---|---|
| **Bid Bond (SF 24)** | Surety-issued bond on Treasury Circular 570 surety | **Default — recommended** |
| Postal money order | USPS money order | Impractical at $30K+ |
| Certified check | Bank-certified check | Ties up cash; possible if firm has cash to spare |
| Cashier's check | Bank-issued | Same as certified |
| Irrevocable Letter of Credit (ILOC) | From federally insured financial institution | Acceptable; takes bank 5–10 business days to issue |
| U.S. bonds / Treasury notes | Pledged Treasury securities | Esoteric; rarely used |
| Individual Surety per FAR 52.228-11 | Personal-asset-pledge by individual surety | Requires asset pledge + CO acceptance; do NOT use without an established individual-surety relationship |

For most small federal construction firms, **SF 24 Bid Bond is the default**. The remainder of this guide assumes SF 24.

---

## C. Standard Form 24 — fill-in fields (surety completes most; offeror verifies)

The surety's attorney-in-fact completes most fields. The offeror reviews for accuracy before submission. Fields to verify:

| Field | Verify |
|---|---|
| **Principal** (offeror) | Legal name, address, signature line for offeror |
| **Surety** | Name, address, NAIC code, state of incorporation, Treasury Circular 570 listing |
| **Penal Sum** | Numeric AND written ("Thirty-four thousand dollars and no/100 — $34,000.00") |
| **Solicitation / Bid date** | 140FC126R0017 / 2026-06-22 |
| **Contract description** | "San Marcos Aquatic Resources Center, Rehabilitate Shop & 2 Stall Garage Building" |
| **Date of bond** | Date of execution by surety (within 30 days of submission) |
| **Bond condition language** | Standard SF 24 language: "If the Principal's bid is accepted, the Principal will, within the period specified in the solicitation, execute the contract and give such bond(s) for the faithful performance of the contract as may be specified in the solicitation. Otherwise, the obligation of this bond shall be void." |
| **Principal signature** | Signed in ink by an authorized officer of the offeror (same person who signs SF 1442 block 20B is typical) |
| **Principal corporate seal** | If firm has one; many small LLCs do not — N/A is acceptable |
| **Surety signature** | Attorney-in-fact of surety, with Power of Attorney attached |
| **Surety corporate seal** | Raised seal of the surety company |

---

## D. Wet-ink original vs. scanned PDF

This is the one place in the proposal where the **wet-ink original may matter** — the surety's raised seal and original attorney-in-fact signature on SF 24 are traditionally a wet-ink, physical-document requirement.

**Three options to handle this in an electronic-submission environment:**

### Option 1 — Electronic bond (e-bond)

- Surety issues an electronic bond via a provider like SurePath, Tinubu, US Surety Services, or surety2000
- E-bond is a digitally signed PDF with verifiable cryptographic seal
- Federal government has accepted e-bonds since 2018 (DoD-class-deviation 2018-O0007 first; then GSA, then most civilian agencies)
- **Confirm with CO if e-bond is acceptable for this RFP** — if surety can issue e-bond, this resolves the paper-original question entirely
- `[VERIFY VS RFP SECTION L]` — RFP does not explicitly require wet-ink for the bid bond; absence of prohibition + government-wide e-bond acceptance suggests it's OK, but the CO is the authority

### Option 2 — Scanned PDF at submission + original mailed to follow

- Scan the wet-ink original SF 24 at ≥ 300 DPI and embed in Volume I
- Mail (or courier) the wet-ink original to the CO's address within 1–2 business days of email submission
- Most COs accept this practice; some require advance notice in the cover letter ("Original SF 24 bid bond mailed under separate cover, expected arrival 2026-06-25")
- Suggested mail-out method: **FedEx Express Saver** or **USPS Priority Mail with tracking**. Do NOT use any service that requires signature at the recipient (federal buildings often won't release a signature)

### Option 3 — Hand-deliver original to CO

- For local offerors, hand-deliver the wet-ink original to the CO's office on submission day or the next business day
- The CO's address is in Falls Church VA (5275 Leesburg Pike, Code FC1) — not practical from Texas
- **Skip this option** for a Texas-based offeror

**Recommended:** Option 1 (e-bond) if the surety supports it. Fallback to Option 2.

---

## E. The Power of Attorney

Every SF 24 issued by a corporate surety carries a Power of Attorney (POA) granting the attorney-in-fact authority to bind the surety. The POA must:

- Be on surety letterhead
- Be dated within a reasonable window (typically not expired)
- Specifically name the attorney-in-fact and the limit of their authority (must be ≥ the penal sum of the bid bond)
- Be attached to the bid bond when submitted

Verify POA is included before inserting SF 24 into Volume I. Missing POA = the surety's signature is unauthenticated = bid bond rejected = bid Fails.

---

## F. Treasury Circular 570 verification

Before accepting the bond from the surety, verify the surety is currently listed:

- Visit `https://fiscal.treasury.gov/surety-bonds/circular-570.html`
- Search the surety company name
- Verify:
  - Current listing (not removed from T-570)
  - Single-project underwriting limit ≥ penal sum of the bid bond ($34K is trivially small for any T-570 surety, but verify anyway)
  - State of admission includes the federal government's contracting venue (federal contracts: all 50 states + DC + territories)

---

## G. Pre-submission checklist for the bid bond piece

- [ ] Surety is on T-Circular-570 (verified day-of-submission)
- [ ] Penal sum is ≥ 20% of bid price (or $1M cap, whichever less)
- [ ] Penal sum is written numerically AND alphabetically
- [ ] Solicitation 140FC126R0017 referenced on the bond
- [ ] Principal name + address matches SF 1442 block 14
- [ ] Surety attorney-in-fact signature present
- [ ] Surety corporate seal present (or e-bond cryptographic equivalent)
- [ ] Power of Attorney attached
- [ ] Bond dated within 30 days of submission
- [ ] If paper bid bond: scanned at ≥ 300 DPI for Volume I + original mailed/couriered to CO with delivery within 2 business days of email submission
- [ ] If e-bond: cryptographic signature verifies, surety provider is on the agency's accepted-providers list, e-bond verification URL included in the bond PDF

---

## H. What happens to the bid bond after submission

- **If offeror is awarded the contract:** Bid bond is replaced by Performance Bond (SF 25) + Payment Bond (SF 25A) at 100% of contract price. Bid bond is then discharged.
- **If offeror withdraws after bid opening:** Bid bond may be forfeited (up to the penal sum) as liquidated damages for the government's cost of re-soliciting or accepting a higher offer.
- **If offeror is not selected:** Bid bond is discharged when the contract is awarded to another offeror (or solicitation is canceled). Surety releases the underwriting reserve.
- **Acceptance period:** Bid bond stays in force for the offer acceptance period (≥ 90 calendar days per RFP p.3 block 13d). Award typically happens well within that window.
