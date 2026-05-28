# {{PROJECT_NAME}} — Bid Form Preparation (SF-18 or SF-1449 + Schedule of Prices)

> **SAP variant — SF-18 default.** Federal SAP RFQs under FAR Part 13 most commonly use **SF-18 Request for Quotation** (not SF-1442). Under FAR 13.500 commercial-item simplified procedures, the CO may instead use **SF-1449** as an integrated solicitation/contract/order. SF-1442 is **wrong** for SAP — if the cover form is SF-1442, switch templates to `bids/_TEMPLATES/federal-sba-rfq-lpta/` or revisit playbook decision matrix.

## SF-18 — Request for Quotation (default SAP form)

SF-18 is a **2-page** RFQ-side form. The Government fills out page 1 (solicitation identity, items requested, schedule). The quoter completes page 2 (price, acceptance period, signature). Far fewer fields than SF-1442 / SF-1449 — no formal "Offer and Award" structure, no separate continuation pages.

### Page 1 — filled by Government (verify they match the RFQ)

| Field | Value (from RFQ) |
|---|---|
| 1 | Request number | `{{SOLICITATION_NUMBER}}` |
| 2 | Date issued | `{{RFP_RELEASE_DATE}}` |
| 3 | Requisition / purchase request | `{{PROJECT_NUMBER}}` |
| 4 | Cert. for nat. def. under BDSA Reg. 2 | per RFQ |
| 5a | Issued by | `{{ISSUING_OFFICE}}` |
| 5b | For information call | `{{CS_NAME}}` — `{{CS_PHONE}}` |
| 6 | Deliver by (date) | per RFQ Section F |
| 7 | Delivery | F.O.B. destination unless noted |
| 8 | To: (quoter) | (blank — for the quoter's address block in page 2) |
| 9 | Destination | `{{SITE_ADDRESS}}` |
| 10 | Please furnish quotations to the issuing office by | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` |
| 11 | Schedule (items, qty, unit, unit price, amount) | per RFQ Section B — mirror CLIN list exactly on the quoter's side |

### Page 2 — filled by BPC (the quoter)

| Field | BPC value |
|---|---|
| 12 | Discount for prompt payment | `[USER TO FILL — typically "Net 30" / no discount]` |
| 13 | Note (Government usage statement acknowledgment) | acknowledged |
| 14 | Name and address of quoter | Blue Print Constructs, LLC dba Blueprint Constructs / 16283 Willowick Ln, Frisco, TX 75033 |
| 15 | Signature of person authorized to sign | `[USER TO FILL — signer name + title; e-signature acceptable per FASA]` |
| 16 | Name and title of signer | `[USER TO FILL — name + title]` |
| 17 | Date signed | `{{SUBMISSION_DATE}}` |

**Note on continuation:** SF-18 does NOT have a continuation-page convention the way SF-1442 / SF-1449 do. If the price schedule does not fit on page 1, attach a **separate Schedule of Prices document** (not a numbered continuation block) referenced from Field 11.

**Note on acceptance period:** SF-18 does NOT have an explicit acceptance-period block. State the acceptance period (typ 60 cal days on SAP — per `{{ACCEPTANCE_PERIOD_DAYS}}`) in your **cover note** or as a header line on the Schedule of Prices.

## SF-1449 — Commercial-Item RFQ (alternate form, when FAR Part 12 + 13 layered)

When the CO elects SF-1449 for a commercial-item SAP under FAR 13.500, the form combines solicitation + contract + order. Quoter fills out:

| Block | Field | BPC value |
|---|---|---|
| 17a | Name and address of offeror | Blue Print Constructs, LLC dba Blueprint Constructs / 16283 Willowick Ln, Frisco, TX 75033 |
| 17b | UEI + CAGE | UEI: `LM4YHVQ71QG7` / CAGE: `9LET0` |
| 18a | Payment will be made by | per RFQ (the agency fills) |
| 19 | Schedule of supplies / services + unit + qty + unit price + amount | mirror CLIN list exactly |
| 23 | Amount | `${{TOTAL_PRICE}}` |
| 30a | Signature of offeror / contractor | `[USER TO FILL — signer name + title]` |
| 30b | Name and title of signer | `[USER TO FILL]` |
| 30c | Date signed | `{{SUBMISSION_DATE}}` |

The Government completes blocks 31a–31c (acceptance + award) at award.

## Bid bond (SF-24) — usually NOT required on SAP

**Verify Section I.** If FAR 52.228-1 is NOT in the clause set (typical SAP), **do not** order an SF-24 from the surety. SAP RFQs commonly use **FAR 52.228-13 Alternative Payment Protections** instead, with the post-award P&P (or alt-payment instrument) due within 10 days of award.

If FAR 52.228-1 IS in the clause set (atypical SAP), fall back to the SF-24 block-by-block from [`bids/_TEMPLATES/federal-sba-rfq-lpta/05-bid-form-prep.md`](../federal-sba-rfq-lpta/05-bid-form-prep.md).

## Schedule of Prices (CLIN-by-CLIN)

`[Mirror the CLIN list from RFQ Section B exactly. Every CLIN priced — leaving a CLIN blank is non-responsive even on SAP.]`

| CLIN | Description (per RFQ) | Qty | Unit | Unit price | Extended | Notes |
|---|---|---|---|---|---|---|
| 0001 | `{{CLIN_0001_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | |
| 0002 | `{{CLIN_0002_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | |
| 0003 | `{{CLIN_0003_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | |
| Option 0001 | `{{OPTION_0001_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | Priced option — per RFQ |
| Option 0002 | `{{OPTION_0002_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | Priced option — per RFQ |
| | **TOTAL EVALUATED PRICE (base + all priced options)** | | | | `${{TOTAL_PRICE}}` | |

## SAM Reps & Certs incorporation (FAR 52.204-8(d) or 52.212-3)

If BPC's SAM Reps & Certs are current (≤ 12 months from RFQ issuance), attach this 1-page incorporation statement. On a commercial-item SAP, the relevant clause is **FAR 52.212-3** (Offeror Representations and Certifications — Commercial Products and Commercial Services) and the incorporation is under 52.212-3(b).

```
SAM.GOV REPRESENTATIONS AND CERTIFICATIONS INCORPORATION

Per FAR 52.204-8(d) (and FAR 52.212-3(b) where applicable), Blueprint Constructs
(Blue Print Constructs, LLC dba) hereby incorporates by reference into this Quote
all current Representations and Certifications maintained in the System for Award
Management (SAM.gov) for the following entity:

  Entity:              Blue Print Constructs, LLC dba Blueprint Constructs
  UEI:                 LM4YHVQ71QG7
  CAGE:                9LET0
  NAICS for this bid:  {{NAICS_CODE}}
  Size assertion:      Small Business (per SAM record; SBA size standard for
                       NAICS {{NAICS_CODE}} is ${{SIZE_STANDARD_USD}}M 3-yr
                       average revenue)
  SAM record current as of: {{SAM_VERIFICATION_DATE}}

The Representations and Certifications in SAM are accurate, current, and
complete as of the date above. No exceptions to FAR Part 4 / FAR 52.204-8 /
FAR 52.212-3 representations apply to this Quote except as expressly listed
below:

  [USER TO FILL — list any specific exceptions, or write "None"]

Signed:  [USER TO FILL — signer name]    Title:  [USER TO FILL — title]
Date:    {{SUBMISSION_DATE}}
```

## Buy American Certificate (FAR 52.225-4)

If the RFQ includes FAR 52.225-9 (Buy American — Construction Materials) or 52.225-11, attach FAR 52.225-4 stating:

- Either: all construction materials are domestic per FAR 25.003 — OR —
- List specific foreign construction materials with country of origin + dollar value, AND request determination per FAR 52.225-9(b)(3) for unreasonable cost / non-availability if applicable

```
BUY AMERICAN CERTIFICATE — CONSTRUCTION MATERIALS (FAR 52.225-4)

The Quoter certifies, in accordance with FAR 52.225-4, that all construction
materials to be furnished in this contract are domestic construction materials
as defined in FAR 25.003 EXCEPT for the following:

  [Country] — [Material description] — [Dollar value]
   (none anticipated / list as applicable)

Signed:  [USER TO FILL — signer name]    Title:  [USER TO FILL — title]
Date:    {{SUBMISSION_DATE}}
```
