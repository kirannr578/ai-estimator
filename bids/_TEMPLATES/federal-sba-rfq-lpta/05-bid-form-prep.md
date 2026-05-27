# {{PROJECT_NAME}} — Bid Form Preparation (SF 1442 + Schedule of Prices)

## SF 1442 — Solicitation, Offer and Award (Construction, Alteration, or Repair)

### Boxes filled by Government (verify they match RFP cover)

| Box | Field | Value (from RFP) |
|---|---|---|
| 1 | Solicitation number | `{{SOLICITATION_NUMBER}}` |
| 2 | Type of solicitation | `{{SOLICITATION_TYPE}}` (IFB / RFQ / RFP) |
| 3 | Date issued | `{{RFP_RELEASE_DATE}}` |
| 4 | Contract number | (blank at offer) |
| 5 | Requisition / purchase request | (blank at offer) |
| 6 | Project number | `{{PROJECT_NUMBER}}` |
| 7 | Issued by | `{{ISSUING_OFFICE}}` |
| 8 | Address offer to | `{{SUBMISSION_OFFICE_ADDRESS}}` |
| 9–12 | Solicitation details (sealed offers, due date, etc.) | per RFP |
| 13a | Sealed offers due by | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` |

### Boxes filled by BPC (the bidder)

| Box | Field | BPC value |
|---|---|---|
| 13b | Number of copies | per RFP |
| 13c | Type of envelope | per RFP |
| 13d | Acceptance period | **`{{ACCEPTANCE_PERIOD_DAYS}}` calendar days** from opening (minimum acceptable per RFP, often 90 days) |
| 14 | Name + address of offeror | Blue Print Constructs, LLC dba Blueprint Constructs / 16283 Willowick Ln, Frisco, TX 75033 |
| 15 | Telephone | (469) 213-1838 |
| 16 | Remittance address | Same as block 14 (unless different EFT) |
| 17 | Code | UEI: `LM4YHVQ71QG7` / CAGE: `9LET0` |
| 18 | Offer (lump-sum) | `${{TOTAL_PRICE}}` |
| 19 | Acknowledgment of amendments | `{{ADDENDA_LIST}}` (number + date of each SF 30) |
| 20A | Name + title of person authorized to sign | `[USER TO FILL — signer name + title]` |
| 20B | Signature | (wet ink or e-signature; e-signature acceptable per FASA) |
| 20C | Date signed | `{{SUBMISSION_DATE}}` |

### Boxes filled by Government on award (leave blank at offer)

Blocks 21–28 — accepted amount, accounting/appropriation data, award number, CO signature, etc.

## SF 24 — Bid Bond

| Field | Value |
|---|---|
| Principal | Blue Print Constructs, LLC dba Blueprint Constructs / 16283 Willowick Ln, Frisco, TX 75033 |
| Surety | `[USER TO FILL — Treasury Circular 570-listed surety name + address]` |
| Penal sum | **20% of total bid amount OR $1,000,000 (whichever is less)** — per FAR 52.228-1 |
| Solicitation number | `{{SOLICITATION_NUMBER}}` |
| Date of solicitation | `{{RFP_RELEASE_DATE}}` |
| Date of bond | within 30 days of bid opening |
| Principal signature | `[USER TO FILL — same signer as SF 1442 Block 20A]` |
| Surety signature + Power of Attorney attached | yes |

## Schedule of Prices (CLIN-by-CLIN)

`[Mirror the CLIN list from RFP Section B exactly. Every CLIN priced — leaving a CLIN blank flips bid to non-responsive.]`

| CLIN | Description (per RFP) | Qty | Unit | Unit price | Extended | Notes |
|---|---|---|---|---|---|---|
| 0001 | `{{CLIN_0001_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | |
| 0002 | `{{CLIN_0002_DESCRIPTION}}` | `{{QTY}}` | `{{UNIT}}` | `${{UNIT_PRICE}}` | `${{EXTENDED}}` | |
| `{{...}}` | | | | | | |
| | **TOTAL EVALUATED PRICE** | | | | `${{TOTAL_PRICE}}` | |

## SAM Reps & Certs incorporation (FAR 52.204-8(d))

If BPC's SAM Reps & Certs are current (≤ 12 months from RFP issuance), attach this 1-page incorporation statement:

```
SAM.GOV REPRESENTATIONS AND CERTIFICATIONS INCORPORATION

Per FAR 52.204-8(d), Blueprint Constructs (Blue Print Constructs, LLC dba)
hereby incorporates by reference into this Offer all current Representations
and Certifications maintained in the System for Award Management (SAM.gov) for
the following entity:

  Entity:              Blue Print Constructs, LLC dba Blueprint Constructs
  UEI:                 LM4YHVQ71QG7
  CAGE:                9LET0
  NAICS for this bid:  {{NAICS_CODE}}
  Size assertion:      Small Business (per SAM record; SBA size standard for
                       NAICS {{NAICS_CODE}} is ${{SIZE_STANDARD_USD}}M 3-yr
                       average revenue)
  SAM record current as of: {{SAM_VERIFICATION_DATE}}

The Representations and Certifications in SAM are accurate, current, and
complete as of the date above. No exceptions to FAR Part 4 / FAR 52.204-8
representations apply to this Offer except as expressly listed below:

  [USER TO FILL — list any specific exceptions, or write "None"]

Signed:  [USER TO FILL — signer name]    Title:  [USER TO FILL — title]
Date:    {{SUBMISSION_DATE}}
```

## Buy American Certificate (FAR 52.225-4)

If the RFP includes FAR 52.225-9 (Buy American — Construction Materials) or 52.225-11, attach FAR 52.225-4 stating:

- Either: all construction materials are domestic per FAR 25.003 — OR —
- List specific foreign construction materials with country of origin + dollar value, AND request determination per FAR 52.225-9(b)(3) for unreasonable cost / non-availability if applicable

```
BUY AMERICAN CERTIFICATE — CONSTRUCTION MATERIALS (FAR 52.225-4)

The Offeror certifies, in accordance with FAR 52.225-4, that all construction
materials to be furnished in this contract are domestic construction materials
as defined in FAR 25.003 EXCEPT for the following:

  [Country] — [Material description] — [Dollar value]
   (none anticipated / list as applicable)

Signed:  [USER TO FILL — signer name]    Title:  [USER TO FILL — title]
Date:    {{SUBMISSION_DATE}}
```
