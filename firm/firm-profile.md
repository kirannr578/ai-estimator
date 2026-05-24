# Blue Print Constructs — Firm Profile

> Human-readable companion to `firm-profile.json` (the canonical machine-readable source). Edit `firm-profile.json` first; treat this document as a derivative.
>
> **Extraction date:** 2026-05-23 from `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\` (read shallow first, deep-read only corporate-marketing + cert + scope files; row data from `Records/*.xlsx` intentionally never extracted per PII policy).
>
> **Gap marker convention:** `[NOT FOUND IN BPC — needs to be supplied]` means the extraction script found no source file that contains this data. The user must supply it before the next bid submission that asks for it. Items marked **EXPIRED PER SOURCE FILE** mean the source we found has a stale date — the renewed value may or may not exist; user to confirm.

---

## 1. Identity

| Field | Value | Source |
|---|---|---|
| Legal name | RK Residential Homes and Commercial Constructions, LLC | `BPC/BPC info.docx` |
| DBA | Blue Print Constructs | `BPC/BPC info.docx`; also seen as "Blueprint Constructs" (no space) and "BPC" |
| Other DBA on file | "That 1 Painter, North Texas" — appears on the older 2023 DFW MSDC welcome letter and SBE certificate; appears to be a prior DBA. User to clarify whether still active. | `BPC/RK Residential Homes and Commercial Constructions LLC.pdf` + `BPC/SBE RKRes 2023.pdf` |
| State of incorporation | Texas | `BPC/BPC info.docx` |
| Year founded | 2022 (TX Sec of State filing 0804376974) | `BPC/BPC info.docx`; corroborated by Beck Group pre-qual ("Date business started: 01/07/2022") |
| Entity type | Limited Liability Company (LLC) | `BPC/BPC info.docx` and GL policy declarations |

## 2. Federal / state IDs

| ID | Value | Source |
|---|---|---|
| EIN | 87-4292998 | `BPC/BPC info.docx` (raw 874292998) |
| TX Comptroller Taxpayer ID | 32082600456 | `BPC/BPC info.docx` |
| TX Web File # | XT287610 | `BPC/BPC info.docx` |
| TX SOS File # | 0804376974 | `BPC/BPC info.docx` |
| UEI (SAM.gov) | LM4YHVQ71QG7 | `BPC/BPC info.docx`; corroborated by `BPC/BPC Profile.pdf` |
| CAGE (DLA) | 9LET0 | `BPC/BPC info.docx`; corroborated by `BPC/Blueprint Constructs Capability Statement.pdf` |
| DUNS (legacy) | 053641222 | `BPC/BPC info.docx` (carried for historical / pre-UEI references) |
| SAM.gov current registration state | **Active** (user-confirmed 2026-05-23). Registration expiration date is still TBD — SAM registrations expire annually; user to verify the expiration date and supply it before any federal submission (USFWS San Marcos, USACE PAIS cabin, TXANG Cmd Post). Reps & Certs / EFT / TIN refresh currency are separate open items and not implied by this confirmation. | User confirmation 2026-05-23 |

## 3. Contact

| Field | Value | Source |
|---|---|---|
| Registered address | 16283 Willowick Ln, Frisco, TX 75033 | `BPC/BPC info.docx` |
| Mailing address on GL policy | 16283 Willowick Ln, Little Elm, TX 75068-1210 — same street; Frisco/Little Elm border. **User to reconcile current address-of-record.** | `BPC/RK Residential Homes and Commercial Constructions LLC DBA Blueprint Constructs-Commercial GL-SBCC-042443-00.pdf` |
| Office phone | (469) 213-1838 | `BPC/BPC info.docx`; `BPC/Blueprint Constructs Capability Statement.pdf` |
| Personal cell | [REDACTED — not for bid submissions per the firm's own PLACEHOLDERS-TO-FILL.md Section G policy] | `BPC/BPC info.docx` |
| Primary email | contactus@blueprintconstructs.com | `BPC/BPC info.docx` |
| Alternate email | info@blueprintconstructs.com | `BPC/BPC info.docx` |
| Principal email (Rocky) | rocky@blueprintconstructs.com | `BPC/Rocky Business Profile.docx` |
| Website | https://www.blueprintconstructs.com (inferred from email domain — **verify live URL before listing**) | inferred |

## 4. NAICS codes

`236115`, `236116`, `236118`, `236210`, `236220`, `238160`, `238170`, `238310`, `238320`, `238330`, `238340`, `238350`, `561790`

- **Primary for active renovation pipeline (TAMU, ASU, USFWS, TXANG):** `236220` — Commercial & Institutional Building Construction
- **Primary for residential remodel work:** `236118` — Residential Remodelers
- **Source files combined:** `BPC/BPC info.docx`, `BPC/BPC Profile.pdf`, `BPC/Blueprint Constructs Capability Statement.pdf`, `BPC/MBE.pdf`, `BPC/SBE.pdf`. The NAICS list differs slightly across sources; this union covers all five.

## 5. Business size + set-aside eligibility

| Designation | Status | Source / notes |
|---|---|---|
| Small business | **Yes** — SBA size-standard small per 13 CFR Part 121 | `BPC/SBE.pdf` (DFW MSDC SBE certificate DL09279) — **EXPIRED PER SOURCE FILE 2024-08-31**, recertify |
| MBE (minority-owned) | **Yes** — DFW MSDC certified | `BPC/MBE.pdf` (DL09279) — **EXPIRED PER SOURCE FILE 2024-08-31** |
| TX HUB | **Yes** — Texas Comptroller HUB program via DFW MSDC affiliate; VID 1874292998900 | `BPC/HUB.pdf` — **EXPIRED PER SOURCE FILE 2024-08-31** |
| SBA 8(a) | [NOT FOUND IN BPC] — no certificate on file | — |
| SDVOSB (service-disabled veteran-owned) | [NOT FOUND IN BPC] | — |
| WOSB (woman-owned) | [NOT FOUND IN BPC] | — |
| HUBZone | [NOT FOUND IN BPC] | — |

## 6. Licenses & certifications (detail)

### TX HUB Certificate
- **VID:** 1874292998900
- **Issued:** 2023-08-09 / **Expired per source file:** 2024-08-31
- **NAICS listed:** 236115, 236116, 236118, 236210, 236220
- **Source:** `BPC/HUB.pdf`

### MBE Certificate (DFW MSDC / NMSDC)
- **Number:** DL09279
- **Issued:** 2023-08-09 / **Expired per source file:** 2024-08-31 (annual recertification)
- **NAICS listed:** 236115, 236116, 236118, 236210, 236220
- **Source:** `BPC/MBE.pdf`; welcome letter at `BPC/RK Residential Homes and Commercial Constructions LLC.pdf`

### SBE Certificate (DFW MSDC)
- **Number:** DL09279
- **Expired per source file:** 2024-08-31
- **Commodities:** Flooring, drywall, sheetrock, painting, fence, power wash
- **Source:** `BPC/SBE.pdf`

### Other licenses (asked by bid forms)
- TX RCAT (roofing): [NOT FOUND IN BPC — if held, supply; if not, mark N/A]
- EPA RRP (Lead-Safe): [NOT FOUND IN BPC]
- Municipal GC license (Frisco, Dallas, Plano, McKinney, Little Elm): [NOT FOUND IN BPC] — Rocky's profile cites "preferred vendor" status with City of McKinney and City of Dallas; specific license numbers unconfirmed.

## 7. Insurance

### Commercial General Liability — current source file
- **Carrier:** American Builders Insurance Company RRG, Inc.
- **Underwriter:** Appalachian Underwriters, Inc.
- **Policy #:** SBCC-042443-00
- **Each occurrence limit:** $1,000,000
- **General aggregate limit:** $2,000,000
- **Products/Completed Ops aggregate:** $2,000,000
- **Personal & Advertising Injury:** $1,000,000
- **Damage to premises rented to you:** $100,000
- **Medical expense:** $5,000
- **Policy period:** 2023-09-25 → 2024-09-25 — **EXPIRED PER SOURCE FILE. Surface current renewed COI before any bid submittal.**
- **Business description on policy:** Painting – interior – building or structures (narrow — broaden via current renewal if BPC is positioning as a GC for institutional renos)
- **Source:** `BPC/RK Residential Homes and Commercial Constructions LLC DBA Blueprint Constructs-Commercial GL-SBCC-042443-00.pdf`

### Workers Comp, Auto, Umbrella, Professional, Pollution
[NOT FOUND IN BPC — needs to be supplied]

The COI PDF (`BPC/BPC COI.pdf`) is an image-only scan; the extraction script returned 16 characters of text (insufficient to parse limits or carriers). User must provide a current COI before any bid that requires ACORDs.

### Insurance broker / agent
[NOT FOUND IN BPC — needs to be supplied] — Each bid workspace has an `outreach/0X-email-insurance-broker.md` draft that assumes a broker contact exists.

## 8. Bonding

| Field | Value |
|---|---|
| Surety | [NOT FOUND IN BPC — needs to be supplied] |
| Single-project capacity | [NOT FOUND IN BPC] — floor of **≥ $1M** is empirically established by the Lavon RV Park contract, which references a $1M performance bond procurement |
| Aggregate capacity | [NOT FOUND IN BPC — needs to be supplied] |
| A.M. Best rating | [NOT FOUND IN BPC] |
| Agent name / agency / phone / email | [NOT FOUND IN BPC] |
| Letter date | [NOT FOUND IN BPC] |
| Source file (image scan) | `BPC/Bond Letter_RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs.pdf` — image-only PDF; extraction returned only 32 characters of text. **The bond letter exists on file** — the user has it and can read it; the extraction script just couldn't parse it. Recommend surfacing surety + capacity + agent contact manually into `firm-profile.json` for the next bid cycle. |

## 9. Trade capabilities

### Self-perform
Interior + exterior painting · Drywall & sheetrock (install, tape, bed, texture) · Tile setting · Flooring (laminate, vinyl, LVT, tile, hardwood refinish) · Trims, baseboards, crown molding, interior carpentry · Roofing (composition, flat, metal — repairs + replacement) · General remodeling · Project supervision, general conditions, QA/QC

### Managed via subs
Site work / excavation / grading · Concrete + masonry · Metal stud framing (commercial) · Electrical · Plumbing · HVAC / mechanical · Septic + sewer line install · Fire suppression / sprinkler · Acoustic ceilings + suspended grid · Lab casework + millwork · Cabinets + countertops · Doors / frames / hardware · FRP wall panel · Fencing · Retaining walls · Low-voltage / data cabling pathway

### Sectors served
Residential (high-end custom, multi-unit, housing developments) · Commercial (office, retail, hospitality) · Industrial (warehouse, manufacturing, distribution) · Institutional (schools, healthcare, religious assembly, community)

### Service radius
North Texas + central Texas; primary DFW metroplex (Denton, Collin, Dallas, Tarrant counties); has executed in Brazos County (College Station), Tarrant County (Southlake), Collin County (Frisco, McKinney, Farmersville).

**Sources:** `BPC/BPC info.docx`, `BPC/Blueprint Constructs Capability Statement.pdf`, `BPC/BPC Details.xlsx` (Vendors sheet), `BPC/Rocky Business Profile.docx`.

## 10. Key personnel

### Ravikiran (Rocky) Nudurupati — Founder & Managing Director (100% owner)
- **Credentials:** PMP, Certified Scrum Master (CSM), SAFe 5.0 Advanced Scrum Master, ITIL trained
- **Education:** M.C.A. (Andhra University); B.Com (Andhra University)
- **Years experience (overall):** 22
- **Years with firm:** 4 (founded 2022)
- **Construction-specific role:** Founder/operator since 2022. Led commercial renovation projects for hospitality (Holiday Inn, Hall Park). Preferred-vendor status with City of McKinney, City of Dallas, Red Elephant.
- **Prior career (2002–2022):** Sr. Program & Delivery Leader at Magellan Health, JCPenney, Bank of America, Wells Fargo, Xerox — managed teams of 25–150+ across North America/LATAM/APAC, multimillion-dollar budgets, IT + cloud + automation + infrastructure delivery.
- **Email:** rocky@blueprintconstructs.com
- **Sources:** `BPC/Rocky Business Profile.docx`; `BPC/BPC info.docx`; `Beck Group/Pre-Qual Beck Group.pdf` (per Beck SQS: 100% ownership, position held since 2022, age 45 at 2023 filing)

### Project Manager (PM of record)
[NOT FOUND IN BPC — needs to be supplied]

### Superintendent
[NOT FOUND IN BPC — needs to be supplied]

### Safety Officer / Safety Manager
[NOT FOUND IN BPC — needs to be supplied]

### Estimator / Pre-Con Lead
[NOT FOUND IN BPC — needs to be supplied]

### Quality Manager
[NOT FOUND IN BPC — needs to be supplied]

> The `Records/Blue Print Constructs Payments, Contacts, To do List.xlsx` workbook has a `Contact Details of Employees` sheet (headers: Name | Designation | Languages | Contact Number | Purpose | Status). Row data was intentionally not extracted per PII policy. The user can decide which employees are appropriate to surface into the firm profile.

## 11. Past projects (long-form summaries — selection rules in `firm-profile.json` → `past_project_selection_rules`)

### 11.1 Lavon RV Park — 30-lot RV park new construction
- **Owner:** Lavon Leisure 78 RV Park LLC (614 Forest Hill Dr, Murphy, TX 75094)
- **Site:** County Road 597, Farmersville, TX 75442
- **Contract value:** $1,050,000 (AIA A101-2020 fixed-price)
- **Schedule:** Started 2025-07-30; scheduled substantial completion 2026-04-30 (6–9 month duration). Final completion status: confirm before citing as "completed."
- **Scope:** Mobilization + excavation; rough grade; driveway + culvert; utility trenching (electrical, plumbing, septic); individual meters per lot; water lines; septic + sewer; final grading; storm drain + detention; rip-rap; 6-ft cedar fencing + metal gate each lot; 8x8 storage shed each lot; 30 trees + mulch + sod; park lights; dumpster/storage/laundromat sheds; 150-LF retaining wall; laundromat building; storm shelter.
- **Bond:** $1,000,000 performance bond per Article 8.
- **Role:** GC
- **Reference contact:** [USER TO FILL — Lavon Leisure 78 RV Park LLC owner contact]
- **Best fit for:** `bids/usfws-san-marcos-140FC126R0017/`, `bids/cmd-post-ndi-W50S7626QA001/`, future `bids/pais-cabin-140P6026Q0029/`
- **Source folder:** `Lavon RV Park/` (Lavon RV Park Scope and contract.docx + Lavon RV Park.docx)

### 11.2 Hindu Temple of Southlake — Place of Religious Worship renovation
- **Owner:** North Texas Hindu Heritage Society (nonprofit)
- **Site:** 595 South Kimball Avenue, Southlake, TX 76092
- **Owner-side project #:** 2024-024
- **Building area:** ≈ 10,700 SF, Occupancy Assembly A-3
- **Contract value:** [NOT FOUND IN SOURCE — material quote in hand: $6,481 phenolic toilet partitions, indicating active material procurement]
- **Schedule:** Drawings dated 2025-06-20 (PDF), updated 2025-09-12 (Arch + Structural). Project in execution per material quote 2025-10-30.
- **Scope:** Demolition + finishes + toilet partitions (phenolic) + partition framework on a 10,700 SF religious assembly building.
- **Role:** GC
- **Reference contact:** [USER TO FILL — North Texas Hindu Heritage Society project contact]
- **Best fit for:** `bids/tamu-harrington-2025-06813/`, `bids/angelo-state-carr-efa-26-007/`
- **Source folder:** `Hindu Temple of South Lake/` (Scope of work.xlsx + Hindu Partitions.pdf + Arch/Structural drawing PDFs)

### 11.3 Holiday Inn (Hall Park, Frisco) — hospitality renovation
- **Owner:** Holiday Inn franchisee at Hall Park, Frisco, TX
- **Site:** Hall Park, Frisco, TX
- **Contract value:** [NOT FOUND IN BPC]
- **Schedule / completion:** [NOT FOUND IN BPC]
- **Scope:** Commercial renovation for hospitality client per Rocky's professional profile.
- **Role:** GC
- **Reference contact:** [USER TO FILL — Holiday Inn Hall Park property POC]
- **Source:** Mention only in `BPC/Rocky Business Profile.docx` — no project-folder source under OneDrive root.
- **Best fit for:** `bids/tamu-harrington-2025-06813/`, `bids/angelo-state-carr-efa-26-007/`, `bids/cmd-post-ndi-W50S7626QA001/`

### 11.4 Volli (pickleball) — interior + exterior painting
- **Owner:** Volli
- **Role:** Painting sub / specialty trade
- **Source:** `BPC/BPC info.docx`; `BPC/BPC Profile.pdf`
- **Reference contact:** [USER TO FILL]

### 11.5 Commercial strip mall — drywall + tape, bed, texture
- **Owner:** [USER TO FILL — owner name not in source file]
- **Site:** DFW metroplex
- **Role:** Drywall sub / specialty trade
- **Source:** `BPC/BPC info.docx`

### 11.6 250–500+ single-family-home portfolio (cumulative)
- **Owners:** Multiple — primarily through GC partners That 1 Painter, Touchmark, Bridge View Build, Hill Design Build
- **Site:** DFW metroplex (cumulative)
- **Scope:** Interior + exterior painting, drywall, flooring, tile, trims, roofing repairs across 250+ to 500+ SFHs since 2022, primarily as specialty sub.
- **Role:** Specialty trade subcontractor
- **Reference contacts:** [USER TO FILL — at each of the four featured GC partners]

### 11.7 Private residential mitigation — 1509 Astoria Dr, Dallas County, TX
- **Owner:** Private homeowner — Dallas County, TX
- **Scope:** Residential mitigation / restoration. Specifics intentionally not extracted to avoid surfacing homeowner PII.
- **Reference contact:** [redacted — homeowner]
- **Source file omitted for privacy — contains PII** (`1509 Astoria Dr/POOJA_MOHAN_MITIGATION INVOICE.pdf`)

### 11.8 Private residential restoration + cabinetry — 2056 Zander Dr, Dallas County, TX
- **Owner:** Private homeowner — Dallas County, TX
- **Scope:** Residential restoration / pack-out + cabinetry + countertop replacement. Specifics intentionally not extracted to avoid surfacing homeowner PII.
- **Reference contact:** [redacted — homeowner]
- **Source files omitted for privacy — contain PII** (`2056 Zander Dr/*`)

### 11.9 Beck Group — pre-qualification (subcontractor, not a delivered project)
- **Owner-prospect:** The Beck Group (commercial GC, Dallas TX)
- **Status:** Pre-qual submitted 2023-03; pre-qual status not confirmed.
- **Source:** `Beck Group/Pre-Qual Beck Group.pdf`. **Do not cite as completed past performance** — pre-qual only.

## 12. Featured clients (for capability statement / cover letters)

That 1 Painter (North Texas) · Touchmark · Bridge View Build · Hill Design Build · Volli (pickleball) · Holiday Inn (Hall Park, Frisco) · North Texas Hindu Heritage Society · Lavon Leisure 78 RV Park LLC · City of McKinney (preferred vendor) · City of Dallas (preferred vendor) · Red Elephant (preferred vendor)

## 13. Submission assets (on OneDrive — referenced by path, not mirrored as binaries)

| Asset | Path |
|---|---|
| Capability Statement | `BPC/Blueprint Constructs Capability Statement.pdf` |
| Long-form profile | `BPC/BPC Profile.pdf` |
| Logo | `BPC/BPC Logo.pdf` (editable source `BPC/Editable source file.ai`) |
| Bond letter (image scan) | `BPC/Bond Letter_RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs.pdf` |
| COI (image scan) | `BPC/BPC COI.pdf` |
| Commercial GL policy (full) | `BPC/RK Residential Homes and Commercial Constructions LLC DBA Blueprint Constructs-Commercial GL-SBCC-042443-00.pdf` |
| W-9 | `BPC/Filled W9 Form - BPC.pdf` |
| DBA certificates | `BPC/BPC DBA 1.jpg`, `BPC/BPC DBA 2.jpg` |
| HUB certificate | `BPC/HUB.pdf` |
| MBE certificate | `BPC/MBE.pdf` |
| SBE certificate | `BPC/SBE.pdf` |
| TX HUB NIGP update guide | `BPC/Texas HUB_Vendor NIGP Updates & Certificate_2021-08-05.pdf` |
| MBE welcome letter | `BPC/RK Residential Homes and Commercial Constructions LLC.pdf` |
| Dallas County contractor app (blank template) | `Dallas County/Contractors Application for Certification..pdf` |
| Dallas County assumed-name cert (blank template) | `Dallas County/Assumed Name Certification.pdf` |
| Business card | `BPC/BPC Business card.pdf` |

## 14. Submission scaffold (pre-templated on OneDrive)

`C:\Users\rnuduru1\OneDrive\Blueprint Constructs\BPC-Submission-Package\` — 11-section pre-templated shell. Tracking sheet: `PLACEHOLDERS-TO-FILL.md`. See `firm-profile.json → submission_scaffold.templates_inventory` for the full 29-file template list. **Do not duplicate these into the repo;** they are bid-output templates that the firm has already designed and that the user manages on OneDrive.

The repo's `firm/firm-profile.json` is the source of company-level data; the OneDrive scaffold is where per-bid responses are typeset.

## 15. Annual financials, safety, banking — gaps

| Section | Status | Source |
|---|---|---|
| Annual revenue FY-1 / FY-2 / FY-3 | [NOT FOUND IN BPC — needs to be supplied] | n/a — per PLACEHOLDERS-TO-FILL.md Section A |
| Largest single contract completed | [NOT FOUND IN BPC — needs to be supplied] | n/a |
| Largest single contract underway | $1,050,000 — Lavon RV Park | `Lavon RV Park/Lavon RV Park.docx` |
| Cumulative contract value to date | [NOT FOUND IN BPC] | n/a |
| EMR (3-year history) | [NOT FOUND IN BPC] | n/a — required by every PQQ / TAMU CSP / federal safety questionnaire |
| TRIR / LTIR / OSHA recordables (3 yr) | [NOT FOUND IN BPC] | n/a |
| OSHA citation history (5 yr) | [NOT FOUND IN BPC] | n/a |
| Bank name + relationship manager | [NOT FOUND IN BPC] | n/a — bank account # in `BPC/BPC info.docx` intentionally NOT surfaced here per PII policy |
| Bank reference letter (last issued) | [NOT FOUND IN BPC] | n/a |
| AR / billing email | [USER TO FILL]@blueprintconstructs.com | per PLACEHOLDERS-TO-FILL.md Section G7 |

## 16. PII and confidentiality

The following data items were **deliberately not surfaced** into this profile even though they appeared in source files:

- Bank account / routing number (in `BPC/BPC info.docx`)
- TX SOS login password (in `BPC/BPC info.docx`)
- Other DFW MSDC portal password (in `BPC/RK Residential Homes and Commercial Constructions LLC.pdf` — DFW MSDC initial password)
- Procurement portal passwords (in `BPC/BPC Details.xlsx` Sheet1)
- Personal cell phone number
- Other corporate entities under the same principal (Maxiple Group LLC, RK Creative Workz LLC, Buds n Petals LLC — visible in BPC info but not part of this firm's bid profile)
- Customer/homeowner names from `1509 Astoria Dr/` and `2056 Zander Dr/` past-project folders (PII)
- Row data from `Records/Blue Print Constructs Payments, Contacts, To do List.xlsx` (only sheet names + headers were inventoried)
- Row data from `BPC/Contacts.xlsx` (only sheet names + headers were inventoried)
- Row data from `BPC/BPC Details.xlsx` past beyond the first ~10 rows used for context

If you (the firm principal) want any of these surfaced into a specific bid submission, paste the value directly into that bid's per-file content under `bids/<slug>/proposal/` — do NOT add them to this canonical firm profile. The firm profile is the public-facing record.

---

_Last extracted: 2026-05-23. Regenerate by running `firm/_scripts/extract_sources.py` after meaningfully updating any file under `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\BPC\`, or hand-edit `firm/firm-profile.json` directly and then rewrite this `.md` to match._
