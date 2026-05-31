# Source files manifest — MCC Cosmetology Phase 4

> **Source:** HCS Box folder (`https://hcs-gc.box.com/s/bhy2pkudhlkcgcxfo7qxdb8vcjnhfwni`)
> downloaded by user on **2026-05-30 20:08 CT** as `Phase 4 CSC Module B Cosmetology.zip`
> (20.8 MB) and staged at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\`.
> The ZIP contained a single wrapper folder `Phase 4 CSC Module B Cosmetology/` with three
> PDFs in three subdirectories (Specifications, Plans, Solicitation Documents). The wrapper
> was flattened during extraction so files land directly under `attachments/<subdir>/`.
> Extraction is fully deterministic (`zipfile.ZipFile` + `pymupdf.fitz.open`); no LLM calls.

## Attachment inventory (extracted 2026-05-30)

| # | Path under `attachments/` | Size | Pages | Type | Source title block |
|--:|---|---:|---:|---|---|
| 1 | `Specifications/25062 MCC CSC Module B Cosmetology Phase 4 Renovations PM.pdf` | 5.4 MB | **414** | Project Manual | RBDR PLLC, Project No. **25062**, May 2026 |
| 2 | `Plans/25062 MCC CSC MODULE B PHASE 4 RENOVATIONS DWG.pdf` | 13.4 MB | **37** | Drawings | RBDR PLLC + EMA Engineering, Project No. 25062 |
| 3 | `Solicitation Documents/Proposal Form.pdf` | 1.1 MB | 2 | CSP Proposal Form (Section 004213, vector-only — no extractable text) | RBDR PLLC, Project No. 25062 |

**Total:** 3 PDFs, ~19.9 MB, 453 pages.

## Extracted facts (deterministic — sourced directly from page text or rendered form)

### Project identity (verbatim)

| Field | Value | Source |
|---|---|---|
| Project name | **MCC CSC Module B Cosmetology Phase 4 Renovation** | Spec book p.1 + DWG p.1 cover sheet |
| Architect's project number | **25062** | Spec book p.1 + DWG p.1 |
| Owner | **McLennan Community College** (1400 College Dr, Waco, TX 76708) | Proposal Form p.1 (TO field), Spec §002116 |
| Architect | **RBDR PLLC** — 913 Franklin Avenue, Suite 100, Waco, TX 76701, P (254) 776-8380 | DWG p.1 cover sheet |
| Architect of record | Bernadette Conrad Hookham, AIA, TX Reg. No. **16887**, certification dated 05/27/2026 | Spec book p.2 |
| MEP consultant | **EMA Engineering & Consultant, Inc.** — 328 S. Broadway Ave., Tyler, TX 75702, P (903) 581-2677 | DWG p.1 cover sheet |
| Spec book date | May 2026 (cert 05/27/2026) | Spec book p.1 |
| Submission attn (direct-to-MCC) | Vice President, Finance and Administration, MCC | Proposal Form p.1 |

### Procurement type (correction to scaffold-time hypothesis)

The DFWMSDC scaffold framed this as a private-GC sub-bid only. Reading the project manual
directly clarifies that **MCC is the procuring entity** running a Texas **Competitive Sealed
Proposal (CSP)** under the MCC Purchasing & Auxiliary Services office. Section 002116
(*Information for Proposers*) specifies:

- Sealed proposals received at MCC Purchasing & Auxiliary Services, 4th Floor Office 404, **until 2:00 P.M. Thursday June 23, 2026**
- Proposal Bond 5%, Performance + Payment Bonds 100% Contract Sum
- Proposal valid 30 days (per Section 004213 form text; the spec §1.11 narrative says 45 days — Form 004213 controls)
- Selection criteria (weighted): price 25%, time of completion 10%, supervision 10%, financial capacity 8%, office location near college 5%, environmentally-friendly construction 10%, reputation 10%, quality 10%, vendor needs 2%, past relationship 10% (=100%)
- Sales tax exempt (TX Ruling No. 9 amended)
- Federal labor compliance: Contract Work Hours and Safety Standards Act (40 USC 327-330), EEO, EPCA, EOAA — implies **federal funding component**, in turn implies **Davis-Bacon Act** prevailing wages apply (Section **007343 PREVAILING WAGE RATES** in the project manual ToC)
- HUB acknowledgment required at prime tier (Form 004213 dedicates a paragraph to MCC's HUB policy)

**HCS Inc. is one of multiple GCs bidding into MCC's CSP.** HCS sources sub pricing through
DFWMSDC and uses its own template referencing "the Owners Proposal Form" layout for HCS's
internal roll-up. BPC's tier remains **subcontractor quote to HCS**, with the relevant due
date being **HCS's 6/22 10AM cutoff** (24 hr ahead of HCS's own 6/23 2PM submission to MCC).

### Spec divisions present (CSI MasterFormat — from spec book Table of Contents)

- **Div 00 — Procurement & Contracting:** 002116 Info for Proposers, 004213 CSP Form, 004336 List of Subs, 004516 Proposer Information, 005213 Agreement, 006113 P-Bond, 006114 Pmt-Bond, 007200 Gen Conditions, **007343 Prevailing Wage Rates**, 008000 Submittals
- **Div 01 — General Requirements:** Summary, Price/Pmt Procedures, **012100 Allowances**, **012300 Alternates**, Substitutions, Admin, Schedule, Quality, Regulatory, Definitions, Temp Facilities/Utilities, Products, Execution/Closeout, Waste Mgmt, Closeout Submittals, Demonstration & Training, **019100 Building Systems Commissioning**
- **Div 02:** 024100 Demolition (single section)
- **Div 03:** 033053 Misc Cast-In-Place Concrete (likely floor-slab patching)
- **Div 06:** 061053 Misc Rough Carpentry, **064101 Architectural Plastic-Laminate Casework**
- **Div 07:** 072100 Thermal Insulation, 078400 Firestopping, 079200 Joint Sealants
- **Div 08:** 081217 Prefinished Steel Frames, 081416 Flush Wood Doors, 087100 Door Hardware (+ 087100.01 schedule), 088813 Fire-Rated Glazing
- **Div 09:** 090561 Floor Prep, 092116 GWB, 092216 Non-Structural Metal Framing, 095100 Acoustical Ceilings, 096500 Resilient Flooring, 096519 Resilient Tile Flooring, **096700 Fluid-Applied Flooring** (chemical-resistant — cosmetology-lab signature spec), 099123 Interior Painting
- **Div 10:** 101100 Visual Display Units, 101423 Panel Signage, 102600 Wall and Door Protection
- **Div 12:** **123661.19 Quartz Agglomerate Countertops**, 124813 Entrance Floor Mats and Frames
- **Div 22 — Plumbing:** 220000 Basic Plumbing, 220090 Submittals, 220534 Isolation Devices, 220554 Identification, 220720 Piping Insulation, 221117 Domestic Water Copper, 221317 Waste/Drain/Vent, 223334 Access Doors, **224001 Plumbing Fixtures and Fixture Carriers** (shampoo bowls included)
- **Div 23 — HVAC:** 230000 Basic Mechanical, 230090 Submittals, **230532 Roof Curbs**, 230553 ID, 230593 Test/Adjust/Balance, 230713 Duct/Grille Insulation, 233333 Access Doors, 233416 HVAC Fans, 233713 Diffusers/Registers/Grilles
- **Div 26 — Electrical:** 260000, 260505 Selective Demo, 260519 LV Conductors, 260526 Grounding, 260533 Raceways/Boxes, 260553 ID, 260923 Lighting Controls, 262000 LV Distribution, 262726 Wiring Devices, 265000 Lighting

**Not in spec book:** Div 04 Masonry, Div 05 Steel, Div 11 Equipment (cosmetology stations are likely OFCI), Div 13 Special Construction, Div 14 Conveying, Div 21 Fire Suppression, Div 27 Communications, Div 28 Electronic Safety, Div 31-33 Sitework/Landscape/Utilities. → Confirms **interior renovation** with no exterior, structural, sitework, fire-sprinkler, or low-voltage-systems scope.

### Drawing index (from DWG cover sheet, all 37 sheets)

| Discipline | Sheets | Notes |
|---|---|---|
| Architectural | A0.1, A2.1, A2.2, A6.1, A6.2, A6.3, A7.1, A7.2, A7.3, A7.4, A8.1, LS2.1, LS5.1 | A6.3 + A7.3 are **Alternate 1** RCP / Finish Plan; LS2.1 Life Safety / Code Review; LS5.1 Wall Partition Types; A8.1 Door Schedule + Hardware Schedule |
| Mechanical | MD2.1, MD2.1A, MH2.2, MH2.2A, MH7.0 | "A" suffix = Alternate 1 |
| Plumbing | PD2.1, PL2.2, PL7.1 | Demo + new + details |
| Electrical Power | ED2.1, ED2.1A, EP2.2, EP7.1, EP7.2, EP8.1, EP9.1 | EP8.1 panels, EP9.1 riser |
| Electrical Lighting | EL2.1, EL2.1A, EL7.1, EL7.2, EL8.1, EL8.2 | EL2.1A Alt 1 ceiling lighting; EL7.2 distributed lighting control chart; EL8.2 IECC C405.2 interior lighting compliance |
| Technology | ET2.2, ET7.1 | Tech symbols + responsibility matrix; spec book has no Div 27, so Div 26 / OFCI handles raceway+device cuts |

**Alternate 1** (visible from drawing index): finish + lighting + mechanical scope variant, scattered across A6.3, A7.3, MD2.1A, MH2.2A, ED2.1A, EL2.1A. Pricing route per Section **012300 ALTERNATES** in the project manual (not on the standalone Section 004213 Proposal Form, which is single-lump-sum).

### Proposal Form (Section 004213, standalone 2-page extract)

Structure (read from rendered page image — vector PDF has no extractable text):

- TO: McLennan Community College, Attn: Vice President, Finance and Administration
- Name of Proposer: ____________________
- **Base Proposal:** single lump sum dollar amount (no line-item breakdown on the form itself)
- Completion Time: ____ calendar days from NTP receipt
- Addenda numbers acknowledged: ____ through ____
- Guaranty Bonds: 100% Contract amount P&P Bonds; premiums included
- Documents acknowledgment + HUB acknowledgment paragraph
- 30-day proposal validity
- Signature block (Proposer name, address, FEIN, signature, title, "Seal if Incorporated")

**Implication:** the 5-line-item structure HCS asks subs to use is **HCS's internal template**, not the MCC form. HCS does not pass sub line items through to MCC — it rolls them up to a single Base Proposal $ figure on Section 004213.

### Notable spec ambiguity (potential RFI fodder)

Section 002116 §1.01 reads: *"The Project consists of demolition of the existing netting and
flooring and construction of new netting and artificial turf."* — this language was carried
over from a prior RBDR template (likely a gym renovation) and **does not match the actual
Cosmetology Phase 4 scope** described elsewhere in the same project manual. All other places
in the project manual, the title-block, and the drawings consistently identify the project
as the cosmetology renovation. Treat as a non-substantive drafting carry-over; flag to HCS
for clarification before submission so HCS can RFI RBDR if HCS judges it material.

## Documents NOT in the drop

- No standalone **Section 004336 LIST OF SUBCONTRACTORS** form (it's embedded in the spec book by section number; pull the form pages from the spec book and complete)
- No standalone **Section 004516 PROPOSER INFORMATION** form (same — embedded in spec book)
- No standalone **Section 005213 AGREEMENT FORM** (template only — completed at award)
- No addenda issued at extraction time (no `_Addendum_` filename pattern in the ZIP)

## Addendum monitoring

The HCS Box folder is the canonical addendum channel. **Re-pull the Box link daily 2026-06-15
through 2026-06-22** and append any new files to the table above with date-of-addition.
Adopt naming `Addendum-{NN}-{YYYY-MM-DD}.pdf` when staging.

## Where copies live

- Repo (committed, this directory): `bids/mcc-cosmetology-phase4-2026-0622/attachments/`
- OneDrive (read-only canonical originals): `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\Phase 4 CSC Module B Cosmetology.zip`
