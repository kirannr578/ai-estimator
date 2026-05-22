# 01 — Project overview

> Sources: the 7 Angelo State / TTUS attachments in `inbox/opportunities/attachments/2026-05-21/` (the v3 pipeline at `exports/calibration_v3/estimate.json` extracted summaries for every one of them — see `bid_packages` array indices 3, 4, 6, 7, 8, 10, 11), plus the project-facts block in the triage canvas.

---

## 1. Solicitation identity

| Field | Value | Source |
|---|---|---|
| Solicitation number | **26-007** (ESBD posting 516718) | RFCSP cover; ESBD URL pattern |
| Project name | **Carr EFA Dressing Room Renovation** | RFCSP cover + Attachment A |
| Issuing entity | **Angelo State University** (a member institution of the **Texas Tech University System / TTUS**) | RFCSP cover; Attachment C (TTUS-edited UGSC) |
| Procurement vehicle | **Request for Competitive Sealed Proposal (RFCSP)** under Tex. Gov't Code Ch. 2269 / Tex. Educ. Code Ch. 51 | RFCSP § Procurement Method |
| NAICS (inferred — not stated on the RFCSP) | 236220 — Commercial & Institutional Building Construction | Inference from scope; default for university interior renovation |
| Set-aside | Open competition; **HUB Subcontracting Plan required** (Tex. Gov't Code Ch. 2161) | RFCSP § HUB; Attachment D |
| Federal funding? | Not indicated. Treat as state-funded TTUS work. (No Davis-Bacon Act WD shipped with this packet — the `SAM_-_Davis-Bacon_Act_WD_TX20260254__Hays_County__Building.pdf` in the inbox is for a different opportunity in Hays County.) | RFCSP cover; cross-check against inbox |

## 2. Location

- **Project site:** Carr Education and Fine Arts Building, Angelo State University, San Angelo, TX (campus address ASU Station #10924, San Angelo, TX 76909)
- **County:** Tom Green County (relevant for prevailing-wage determination — see `prevailing-wages.md`)
- **Submission delivery:** TBD per RFCSP § Submission Instructions — almost certainly the ASU Procurement & Contracting office (verify mailing + physical addresses from the RFCSP body; the v3 extract did not pull the submission address)
- **Public-opening room:** TBD per RFCSP (TTUS pattern: public opening immediately after the proposal deadline; confirm)

## 3. Key dates

| Event | Date / Time | Status (today: 2026-05-22) |
|---|---|---|
| RFCSP issued | (per ESBD posting timestamp 2025-10-22 — preliminary) | Issued |
| **Pre-response meeting** | **2026-05-20, 2:00 PM CST** | 🔴 **MISSED.** Today is 2026-05-22. Confirm with Samuel Guevara whether attendance was mandatory; request sign-in sheet, recording, and Q&A. See `07-risk-register.md` R-01. |
| **Proposals due** | **2026-06-05, 2:00 PM CST** (Friday) | T-14 days. Hard deadline. |
| **HSP due** (separate deadline) | **2026-06-08, 5:00 PM CST** (Monday) — **3 calendar days AFTER the proposal** | T-17 days. Hard deadline. Failure to submit by then = automatic rejection. See `05-hsp-plan.md` § A. |
| Construction start | 2026-07-01 | NTP target |
| Substantial completion | 2026-11-02 | ~124 calendar days from start (≈ 4 months). Liquidated damages of $250/day past this date. |
| Project close-out (final completion + warranties + O&M + record drawings + final clean) | Typically 30–60 days after substantial completion | Confirm with CSA Art. 12 / 13 when CSA is in hand |

> ⚠️ The HSP being due AFTER the proposal is a TTUS-specific convention worth flagging internally: proposal package goes in on Friday June 5; HSP package goes in on Monday June 8. If we forget the Monday HSP, the Friday proposal is automatically rejected. Both deadlines are tracked separately in `timeline.md`.

## 4. Scope summary (per the RFCSP)

The RFCSP describes the project (per `exports/calibration_v3/estimate.json` `bid_packages[4].summary`) as:

> "The project involves the complete demolition and replacement of all interior finishes, mechanical systems, plumbing systems, electrical systems, along with all new IT infrastructure, and ADA code elements for the Carr EFA Dressing Room Renovation at Angelo State University."

Expanded per the user's task-brief project-facts block (verbatim from the RFCSP scope text):

**Contractor scope (what we price):**
- **Full interior demolition** — walls, flooring, ceilings, HVAC, lighting, infrastructure
- **New interior finishes** — flooring, ceiling, paint, brick, wall finishes, finish carpentry, millwork
- **Door hardware** — Sargent cylindrical locks + CBORD access control **rough-in** (cabling and reader install is owner — see § 5 below)
- **ADA compliance** — full compliance pass through reno scope (door clear width, hardware reach, accessible route, signage, mirror heights, accessible vanity if any)
- **Mechanical / HVAC** — new system, including rough-ins for owner-furnished tech equipment
- **Plumbing** — new system, with rough-ins
- **Electrical** — new system, with rough-ins for owner-furnished IT
- **General requirements** — CPM scheduling, submittals, change requests, inspections, material testing, dust containment, after-hours coordination (Carr EFA is an active performing-arts building)
- **Close-out** — punch list, record drawings, warranties, O&M manuals, final clean

**Owner-furnished (NOT in our scope — do not price; price coordination/protection only):**
- Technology systems (AV, IT, classroom tech)
- Network / data cabling and termination
- Equipment install (any equipment that goes IN the rooms post-construction)
- Furniture / FF&E
- Fire suppression system (the RFCSP narrative explicitly puts this on the owner side — unusual; confirm. Sprinkler-head relocation on the GC side typically follows ceiling rework, but the RFCSP excludes it.)

The full trade-by-trade decomposition with placeholders for quantities lives in `04-scope-of-work.md`. The contractor-vs-owner scope boundary is reiterated in § A of that document because it affects pricing — we price coordination and rough-ins for owner-furnished items, but not the items themselves.

## 5. Contacts (per the v3 extract; full plan in `contacts.md`)

| Role | Name | Email | Source |
|---|---|---|---|
| RFCSP point of contact | **Samuel Guevara**, ASU Facilities Planning & Construction | Samuel.Guevara@angelo.edu | RFCSP cover (v3: `bid_packages[4].contact`) |
| Director, ASU FP&C | **Tracie Howell** (Director of Facilities Planning and Construction) | Available via ASU FP&C directory — confirm via Samuel | Attachment A (v3: `bid_packages[3].contact`) |
| ASU HUB Coordinator | TBD — request from Samuel; TTUS system has a HUB Operations office at TTU main campus that typically supports member institutions | TBD | Attachment D + TTUS HSP form |
| ASU Procurement | TBD — the RFCSP body lists a procurement officer separate from the project manager | TBD | RFCSP § Submission Instructions |
| A/E firm | Not yet identified — request from Samuel | TBD | RFCSP cover (likely listed in § Project Team) |

Phone numbers are not in the v3 extract. Pull from the ASU directory at `https://www.angelo.edu/directory/` and confirm on first call.

## 6. Document acquisition status

- **In hand (7 attachments via `inbox/opportunities/attachments/2026-05-21/`):**
  - `ESBD_516718_1778880767322_26-007 Carr EFA Dressing Room Renocation RFCSP.pdf` — main RFCSP narrative
  - `ESBD_516718_1778880829538_26-007 Carr EFA Dressing Room Renocation Attachment A.pdf` — Proposal Form & Execution of Offer
  - `ESBD_516718_1778880857161_Attachment B.2 - Sample Construction Services Agreement.pdf` — TTUS sample CSA
  - `ESBD_516718_1778880869361_Attachment C - 2010 Uniform General Conditions and Supplementary General Conditions dated (TTUS edited 09.07.2023).pdf` — full UGSC
  - `ESBD_516718_1778880887164_Attachment D - HSP (Historically Underutilized Businesses (HUB) Subcontracting Plan) documents.pdf` — the actual HSP form to fill
  - `ESBD_516718_1778880901623_Attachment E - Tax Exemption Certificate.pdf` — TX sales tax exemption form
  - `ESBD_516718_1778880917414_Attachment F.1 - Tom Green County Prevailing Wage 2023 (TTUS).pdf` — wage determination
- **Missing (Priority 1 — blocks real takeoff):** architectural + MEP drawing set, full project manual / spec book, finish schedule, door schedule, equipment schedule. See `03-missing-documents.md` for the full list.

## 7. What's not in the RFCSP body but matters (will need to confirm)

These items are not in the v3 extract summaries; confirm by reading the full RFCSP body cover-to-cover (the PDF is in `inbox/`) when starting tomorrow:

1. **Evaluation factors + weights.** TTUS RFCSP pattern: published in the RFCSP § Evaluation Criteria. Confirm exact weights for `06-evaluation-strategy.md`.
2. **Pre-response meeting mandatory vs non-mandatory.** Worded as "Pre-Response Conference" on TTUS — usually "highly recommended" rather than "required." Confirm in writing with Samuel.
3. **Page-count limits on the technical proposal narrative.** TTUS sometimes caps narratives at 10–15 pages.
4. **Whether unit prices are requested.** Attachment A had an allowance line (`$25,000`) and a base-proposal line but the v3 extract did not surface unit-price line items beyond that allowance — re-confirm against the actual Attachment A PDF.
5. **Whether alternates are requested.** Same — re-confirm against Attachment A.
6. **Whether a subcontractor list is required at proposal time** or only at award.
7. **Substantial completion date being a fixed calendar date (2026-11-02)** vs "N days from NTP." The user brief lists it as a fixed date — confirm in writing because the LD clock starts running against this fixed date even if NTP slips.

## 8. Calibration v3 extraction — what was already pulled

The v3 pipeline (`exports/calibration_v3/estimate.json`) extracted summaries for all 7 Angelo State attachments. Pulling the relevant facts verbatim:

```
# bid_packages[4] — RFCSP main narrative
project_name     : Carr EFA Dressing Room Renovation
project_number   : 26-007
project_location : San Angelo, Texas
bid_due          : 2:00PM, Friday, June 05, 2026
contractor       : Angelo State University                          ← "contractor" here is the issuing OWNER (ASU); we are the GC bidding
contact          : Samuel Guevara, Samuel.Guevara@angelo.edu

# bid_packages[3] — Attachment A (Proposal Form)
project_location : ASU Station #10924, San Angelo, TX 76909
contact          : Tracie Howell, Director of Facilities Planning and Construction
unit_prices      : [{"description": "Include a cash/contingency allowance for unforeseen scope of work.", "unit": "ALLOWANCE", "amount": 25000.0}]
referenced_specs : ["01030"]                                       ← Div 01 General Requirements section reference

# bid_packages[10] — Attachment C (TTUS UGSC)
trade_name       : general instructions to bidders
project_name     : Texas Tech University System Construction Projects
key facts        : Document revision date: 09/07/2023
                 : Applies to all TTUS member institutions
                 : Incorporates TFC 2010 edition UGSC

# bid_packages[7] — Attachment B.2 (Sample CSA)
key facts        : HUB contracting commitment: 30% of the total contract sum
                 : Liquidated damages: $###.00 per calendar day of delay   ← placeholder; user brief confirms $250/day

# bid_packages[8] — Attachment F.1 (Tom Green County prevailing wage)
trade_name       : prevailing wage determination
construction type: Building
location         : Tom Green County
key dates        : July 2023

# bid_packages[11] — Attachment D (HSP)
trade_name       : HUB Subcontracting Plan
summary          : State of TX HSP form, required with bid response
```

Known v3 extraction quirks worth noting:
- `contractor: Angelo State University` is the **owner**, not a GC — same owner-vs-GC conflation called out in `exports/calibration_v3/CALIBRATION_REPORT.md` § "Net new issues v3 surfaced."
- The HSP commitment in the sample CSA is **30%** (boilerplate placeholder) whereas the statewide special-trade-construction HUB goal is **21.1%**. The 30% in the sample is a TTUS preference, not the regulatory floor. See `05-hsp-plan.md` § A for the resolution.
- The v3 extract did not pull the submission address, evaluation weights, page-count limits, or pre-response meeting mandatory-vs-not — backlog items for the NOP/RFCSP extractor.
- The "5 wood-framing items" in `estimate.json.line_items` came from `A1` (a stray drawing in the same inbox folder, NOT a Carr EFA drawing). They are flagged `suppressed=True` and contribute $0 to the subtotal. Ignore for this bid.
