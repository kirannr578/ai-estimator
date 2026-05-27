# SF 1449 fill guide — FA667526Q0002 B1710 Office Refurbishment

> **Form correction from initial task brief:** The original triage called this an "SF-1442" fill guide. The actual RFQ cover form is **STANDARD FORM 1449 (REV. 11/2021)** — Solicitation/Contract/Order for Commercial Products and Commercial Services — used because the procurement runs under FAR Part 12 (Commercial Items) + FAR Part 13 (SAP). The full unfilled form is at page 1 of `Solicitation - FA667526Q0002.pdf`.
>
> **Print page 1 from the source PDF**, fill the offeror-required blocks (12, 17, 23, 24, 30), sign, scan, and attach as `01_SF1449_FA667526Q0002_BluePrintConstructs.pdf` per the submission shape in `00-readme.md`.

---

## Block-by-block fill guide

The form headers Blocks 1–31. Per the form note at the top: *"OFFEROR TO COMPLETE BLOCKS 12, 17, 23, 24, AND 30."* These are the only blocks the offeror touches; everything else is government-pre-filled or completed by the CO post-award.

### Blocks already filled by the Government (do NOT modify)

| Block | Field | Pre-filled value |
|---:|---|---|
| 1 | Requisition Number | F5A3SG6104AW01 |
| 5 | Solicitation Number | **FA667526Q0002** |
| 7a | For Solicitation Information Call — Name | LYDIA CARLTON |
| 7b | Telephone | 817-782-5190 |
| 8 | Offer Due Date / Local Time | **29 May 2026, 05:00 PM** |
| 9 | Issued By — Code | FA6675 |
| 9 | Issued By — Office | FA6675 301 LRS LGC, 1637 Carswell Ave, NAS JRB TX 76127-6200; Lydia Carlton + Todd Benner |
| 10 | Set-aside | ☑ 100% Small Business — NAICS 236220 — Size Standard $45,000,000.00 |
| 11 | Delivery FOB | ☐ FOB Destination ☑ See Schedule |
| 13a/b | DPAS Rated Order | (left blank / N/A — no rating) |
| 14 | Method of Solicitation | ☑ **Request for Quote (RFQ)** |
| 15 | Deliver To — Code | F5A3SG; 301 MSG LRS, 1236 Supply Ave, NAS JRB TX 76127-1060; Steve Munnell |
| 16 | Administered By | (left blank — uses 9) |
| 19/20/21/22 | Item Number / Schedule / Qty / Unit | 0001 / Perform all work per SOW... / 1 / Lot |
| 25 | Accounting and Appropriation Data | See Section G — Contract Administration Data |
| 27a | Solicitation incorporates by reference | ☑ ARE attached (52.212-1, -4, -3, -5) |

### Blocks offeror MUST fill

#### Block 12 — Discount Terms

Value: **NET 30** (standard) — Blue Print Constructs offers no early-payment discount.

Format: write "NET 30" or check the prompt-payment box if available.

#### Block 17a — Contractor / Offerer Code (Name + Address)

```
RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs
16283 Willowick Ln
Frisco, TX 75033
```

Filled values from `firm/firm-profile.json`:
```
RK Residential Homes and Commercial Constructions, LLC
DBA: Blue Print Constructs
16283 Willowick Ln
Frisco, TX 75033
UEI: LM4YHVQ71QG7
CAGE: 9LET0
TELEPHONE NUMBER: (469) 213-1838
```

> **Address reconciliation note:** Two addresses are on file for the firm — Frisco, TX 75033 (per BPC info.docx, SOS-filing address) and Little Elm, TX 75068-1210 (per the Commercial GL policy). Same street, Frisco/Little Elm border. Use the **Frisco 75033 address** for the SF 1449 to match the SAM.gov-of-record entity address. See `firm/firm-profile.json → registered_address`.

#### Block 17b — Remittance Address

Check `☐ CHECK IF REMITTANCE IS DIFFERENT` only if payment is to be remitted to a different address than the offeror address in 17a. **For BPC: leave unchecked** (remittance = offeror address) unless the user surfaces a separate remittance address.

#### Block 23 — Unit Price

```
$[AWAITING PRICE BUILD — see ../proposal/01-price-proposal.md]
```

This is the per-unit price for the 1 Lot. Same value as Block 24.

#### Block 24 — Amount

```
$[AWAITING PRICE BUILD — see ../proposal/01-price-proposal.md]
```

This is the extended amount (unit price × quantity). Since quantity is 1 Lot, Block 23 = Block 24.

#### Block 30a — Signature of Offeror / Contractor

[Original ink signature — sign physically before scanning]

#### Block 30b — Name and Title of Signer

```
[USER TO FILL: signer name]
[USER TO FILL: signer title]
```

Filled values:
```
Ravikiran (Rocky) Nudurupati
Founder & Managing Director
```

#### Block 30c — Date Signed

```
[USER TO FILL: signature date — target 29 May 2026]
```

### Blocks the Government completes on award (do NOT pre-fill)

| Block | Field | Note |
|---:|---|---|
| 2 | Contract Number | Government assigns at award |
| 3 | Award / Effective Date | Government enters at award |
| 4 | Order Number | Government enters at award (if blanket purchase) |
| 6 | Solicitation Issue Date | Pre-filled (or left blank as in this case) |
| 17a — Facility Code | — | Government may enter |
| 18a/18b | Payment Will Be Made By + Submit Invoices To | Government fills at award; F87700 per Sec G |
| 26 | Total Award Amount | Government enters at award |
| 27b | Contract / Purchase Order Incorporates by Reference | Government checks at award |
| 28 | Contractor required to sign and return copies | Government completes at award |
| 29 | Award of Contract | Government completes at award |
| 31a/b/c | Signature of CO + Name + Date | CO signs at award |

---

## How to submit the SF 1449

1. **Print page 1** from `Solicitation - FA667526Q0002.pdf`.
2. **Fill blocks 12, 17, 23, 24, 30** by hand or in a fillable PDF editor (the SF 1449 is a fillable AcroForm — Adobe Acrobat or similar can fill the fields directly).
3. **Sign block 30a in ink** (or use a Adobe Sign / e-signature consistent with FAR 4.502 if Acrobat sign capability is configured).
4. **Scan / export to PDF** at 300 DPI.
5. **File-name:** `01_SF1449_FA667526Q0002_BluePrintConstructs.pdf`.
6. **Attach to the offer email** as Attachment 1 per `00-readme.md`.

---

## Common errors → CO non-responsiveness finding

| Error | How to avoid |
|---|---|
| Block 17 left blank or with mismatched address | Pull address from SAM.gov entity record; ensure city/zip matches |
| Block 30a missing signature | Sign physically in ink, then scan |
| Block 30b name/title not matching authorized signer in SAM | Rocky is the 100% owner-signer; SAM record confirms |
| Block 24 missing dollar sign / extended-amount formatting unclear | Use "$XX,XXX.00" format with cents |
| Unsigned offer (some firms forget to sign the scanned PDF) | After scanning, open PDF and visually confirm signature is on the page |
| Date signed (Block 30c) is after the offer due date | Sign before 29 May 17:00; if signing on 29 May, sign in the morning, not at 16:59 |
