# PAIS — Backcountry Cabin Roof Repairs — Bid Form Preparation (SF-18 + Section B)

> **Form on cover: SF-18** (verified, RFQ pp 1–2). This is the canonical SAP-best-value form for sub-SAT FAR Part 13 RFQs per the [federal-simplified-acquisition-best-value playbook](../../firm/playbooks/federal-simplified-acquisition-best-value.md) §4. NOT SF-1442 (would have flipped this to a full FAR Part 14/15 construction RFP) and NOT SF-1449 (would have triggered the integrated commercial-item solicitation/contract/order format — the CO may elect SF-1449 for commercial-item SAP under FAR 13.500, but did not here).
>
> **Variant note:** if a future SF-30 amendment changes the form to SF-1449 (rare; CO discretion), see the playbook §4 table for the clause-inventory shift from 52.213 → 52.212 family and update the Box-by-Box fill below from SF-18 (offeror fills Blocks 8 + 12–16) to SF-1449 (offeror fills Blocks 17a + 24 + 30a–c). No SF-1449 variant fill is provided in this file because SF-18 is operative.
>
> **No bid bond at submission.** FAR 52.228-1 is not invoked. FAR 52.228-13 Alternative Payment Protections governs — Payment Bond OR ILC due **within 10 days of award**. This is the SAP norm per the playbook §8.

## SF-18 — Request for Quotation (Construction)

### Boxes filled by Government (verify they match RFQ cover; any deviation = RFI before signing)

| Box | Field | Value (from RFQ) |
|---|---|---|
| 1 | Request number | 140P6026Q0029 |
| 2 | Date issued | 05/07/2026 |
| 3 | Requisition / purchase request number | 0044044135 |
| 4 | Cert. for Nat. Def. under BDSA Reg. 2 / DMS Reg. 1 — Rating | (none) |
| 5a | Issued by | NPS, MWR - MWRO MABO, 601 Riverfront Drive, Omaha NE 68102 |
| 5b | For Information Call | Bridget Parizek, (402) 800-7927 |
| 6 | Deliver by (date) | 06/01/2026 (note: this is per RFQ; treat as boilerplate-leakage — operative POP is 60 cal-days from NTP per Section B; RFI #1) |
| 7 | Delivery — FOB Destination ☑ Other ☐ | Per Section B (work performed at site, not delivered) |
| 8 | To (name + company + address) | RFQ leaves to be filled by recipient (offeror) |
| 9 | Destination — name of consignee + address | NPS, Padre Island NS — Corpus Christi, TX 78418 |
| 10 | Please furnish quotations to issuing office in Block 5a on or before close of business | **06/18/2026 1200 CT** (per Amd 0001) |

### Boxes filled by BPC (the offeror)

| Box | Field | BPC value |
|---|---|---|
| 8 | TO (Name / Company / Street / City / State / ZIP) | The "TO" block is for sending the RFQ to the offeror; on submission, the offeror's address goes in Block 13 |
| 12 | Discount for prompt payment — 10/20/30 calendar days % | `[USER TO FILL — typically 0% / 0% / 0% unless BPC offers a prompt-payment discount; not required]` |
| 13 | Name and address of quoter | Blue Print Constructs, RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs / 16283 Willowick Ln / Frisco / TX / 75033 / Collin County |
| 14 | Signature of person authorized to sign quotation | `[USER TO FILL — wet ink or e-signature]` |
| 15 | Date of quotation | `[USER TO FILL — submission date, e.g. 06/18/2026]` |
| 16a | Signer — name (type or print) | `[USER TO FILL — signer name; recommended: Ravikiran (Rocky) Nudurupati, Founder & Managing Director]` |
| 16b | Signer — telephone (area code + number) | (469) 213-1838 |
| 16c | Signer — title (type or print) | `[USER TO FILL — title, e.g. Founder & Managing Director]` |

> **Note:** SF-18 itself does not have a CAGE / UEI box. CAGE + UEI go into the **Contractor Core Data block** required by Section L Part C end-of-checklist (see below) and are required by Section L "GENERAL INFORMATION" — UEI + active SAM are mandatory for award.

### Section L — Contractor Core Data block (per RFQ p 27)

```
Offeror's Company Name:    Blue Print Constructs (RK Residential Homes and Commercial
                           Constructions, LLC dba Blue Print Constructs)
CAGE Code:                 9LET0
Unique Entity Identifier:  LM4YHVQ71QG7
Offeror's POC:             [USER TO FILL — recommended: Ravikiran (Rocky) Nudurupati]
POC Email:                 contactus@blueprintconstructs.com (firm-level)
                           rocky@blueprintconstructs.com (principal-level alternate)
POC Phone:                 (469) 213-1838 office
```

## SF-30 amendment acknowledgment (Amd 0001)

| Field | Value |
|---|---|
| 1 | Contract ID code | (per SF-30 Block 1 — leave as Government provided) |
| 9A | Amendment of solicitation number | 140P6026Q0029 |
| 9B | Dated | 05/07/2026 |
| Amendment number | 0001 |
| Effective date | 05/20/2026 |
| 15A | Name + title of signer (type or print) | `[USER TO FILL — same signer as SF-18]` |
| 15B | Contractor / Offeror signature | `[USER TO FILL]` |
| 15C | Date signed | `[USER TO FILL — recommended: same date as SF-18, 06/18/2026]` |

> Amd 0001 changes: site visit moved to 6/4/2026; due date extended to 6/18/2026 12:00 CT. Acknowledge by signing 15A/B/C and including in the QUOTE PACKAGE.
> **Re-check SAM.gov for any Amd 0002+ before final submission.**

## Section B — Schedule of Prices

| CLIN | Description (per RFQ Section B) | Quantity | Unit | Unit price | Extended | Notes |
|---|---|---|---|---|---|---|
| 001 | Repair Doors & Install Reinforcement | 3 | each | `${{UNIT_PRICE_001}}` | `${{EXTENDED_001}}` | Per CLIN 001 spec — SS hardware; reinforcement strips; deadbolt |
| 002 | Repair Roof Leak (Marine-grade shingles, sealant, labor) | 1 | LS | `${{LS_PRICE_002}}` | `${{LS_PRICE_002}}` | Per CLIN 002 spec — marine-grade like-kind shingles + sealant + SS fasteners + water test |
| 003 | Install CAT5 TDI Hurricane Bahama Shutters and Installation Labor for Shutters | 10 | each | `${{UNIT_PRICE_003}}` | `${{EXTENDED_003}}` | Per CLIN 003 spec — TDI-listed; SS or powder-coated AL; manual; lockable; engineer-stamped drawings |
| OPT 001 | Construct Cabin Ramp Extension | 1 | LS | `${{LS_PRICE_OPT_001}}` | `${{LS_PRICE_OPT_001}}` | Per Option 001 spec — 2 landings + 2 ramp runs; PT lumber per drawing; integrate GFE aluminum ramp |
| OPT 002 | Construct Breakaway Sand Control | 1 | LS | `${{LS_PRICE_OPT_002}}` | `${{LS_PRICE_OPT_002}}` | Per Option 002 spec — 2x10 PT lumber 2 boards high on 3 sides; breakaway design with flood openings |
| | **TOTAL** (sum of all base + option lines, per 52.217-5) | | | | `${{TOTAL_PRICE}}` | Per Section B and 52.217-5 — Govt evaluates all options added to base |

> **Pricing rules (per RFQ):**
> - "All pricing to be rounded to the nearest dollar" — Section L Part C.4
> - "Alternate pricing and alternate quotes will not be accepted" — Section L Part C.4
> - "Total price shall be cited and if listed on the Solicitation Form, it must be the same amount listed" — Section L Part C.4
> - **Option pricing evaluation:** per 52.217-5 the Govt adds total option pricing to base pricing for evaluation. Don't unbalance options high — they're scored.
> - Do not leave any line blank. Even if BPC declines to bid an option, **provide a price** (FAR Part 13 SAP doesn't require option award; you can price options high if BPC wants to discourage exercise — but check with PIC before doing that).

## SAM Reps & Certs incorporation (FAR 52.204-19)

This RFQ incorporates 52.204-19 Incorporation by Reference of Representations and Certifications (Dec 2014) at Section I. SAM Reps & Certs are auto-incorporated **as long as they are current ≤ 12 months** in the offeror's SAM record. No separate incorporation page required for this RFQ (52.204-8(d) is **not** invoked here — that clause is the SF-1442 / FAR Part 14-15 path).

If a Section K provision requires offeror-specific completion, complete the provision text + signature in the QUOTE PACKAGE.

## Buy American compliance (FAR 52.225-9 + 52.225-10)

Per Section I, FAR 52.225-9 applies. The "[Contracting Officer to list applicable excepted materials or indicate 'none']" line in the clause says **NONE** — meaning the contractor must use only domestic construction materials except for COTS items per the Buy American statute / Trade Agreements Act tests.

**Action for BPC:**

- ✅ All proposed roofing materials (CLIN 002 marine-grade shingles + SS fasteners) — verify domestic origin or COTS-item exemption
- ✅ All proposed shutter materials (CLIN 003 SS or powder-coated AL) — verify domestic origin or COTS-item exemption; some shutter manufacturers source AL from foreign mills
- ✅ All PT lumber + structural fasteners (Options 001 + 002) — domestic timber and SS hardware; verify

If a foreign material is unavoidable, BPC must request an exception per 52.225-9(c) **before contract performance** (typically pre-award is too late; raise via RFI if known). Don't bake foreign material into the price without notifying.

> **No separate Buy American Certificate** is required at offer for this RFQ — 52.225-4 is not in the §I clause list. The certification is implicit by acceptance of 52.225-9.

## What does NOT apply (vs. typical federal-SBA-LPTA template)

| Template item | Status |
|---|---|
| SF-1442 block fill | ❌ Not applicable — this RFQ is on SF-18. Use the SF-18 fill above instead. |
| SF-1449 block fill | ❌ Not applicable. |
| SF-24 Bid Bond | ❌ Not required (FAR 52.228-1 not invoked). |
| FAR 52.225-4 Buy American Certificate | ❌ Not at offer; clause not in §I list. |
| Performance + Payment Bonds at submission | ❌ Post-award only, per 52.228-13. |
| 52.204-8(d) SAM Reps & Certs incorporation page | ❌ Not invoked; 52.204-19 covers incorporation. |

## Section K — Reps & Certs offeror-specific completion

| Provision | Action |
|---|---|
| 52.203-18 Prohibition on Requiring Internal Confidentiality Agreements — Representation | BPC representation: **No internal confidentiality agreements that restrict employee whistleblower rights.** Sign + insert. |
| 52.209-11 Delinquent Tax Liability or Felony Conviction — Representation | Offeror represents: **Is NOT** a corporation with unpaid Federal tax liability; **Is NOT** a corporation convicted of a felony in past 24 months (sign per BPC's actual status). |
| 52.209-13 Violation of Arms Control Treaties — Certification | **Does not apply** — RFQ is below SAT and is for commercial-product/service-equivalent construction; per provision (a), this provision does not apply to acquisitions at or below the simplified acquisition threshold. **BPC may omit** unless RFQ requires; safer practice is to certify (b)(1) regardless. |

## Final pre-submission verification

- [ ] SF-18 signed (Blocks 13–16) ✅ wet ink or e-signature
- [ ] SF-30 Amd 0001 signed (Block 15) ✅
- [ ] Section L Checklist completed as page 1 ✅
- [ ] Every CLIN + every option priced (no blanks) ✅
- [ ] Pricing rounded to nearest dollar ✅
- [ ] Total cited at bottom of Section B ✅
- [ ] Technical Capability narrative attached ✅
- [ ] Prior Experience (3–5 references with verifiable POCs) attached ✅
- [ ] Contractor Core Data block completed ✅
- [ ] PDF combined to single file titled "QUOTE PACKAGE" ✅
- [ ] Email size ≤ 25 MB; split across 2 emails if larger ✅
- [ ] Subject line: `140P6026Q0029 – PAIS – Cabin Security and Improvements – email N of M` ✅
- [ ] Sent to `bridget_parizek@ios.doi.gov` ≥ 30 min before **06/18/2026 12:00 CT** ✅
