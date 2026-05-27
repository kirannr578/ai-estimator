# Source-files manifest — TAMU Wehner Finance Rm 340E (Sol 2025-06871)

## What's on disk as of 2026-05-27 PM

### A. ESBD posting metadata (extracted text)

The ESBD posting for Sol SSC-2025-06871 was inventoried and text-extracted. The ESBD listing itself references **one downloadable attachment** that is NOT yet in BPC's possession:

| # | File name | Description | Where | Status |
|---:|---|---|---|---|
| 1 | `ESBD_513163_1778104136552_2025-06871_Notice of Project-CS_26.05.05.pdf` | Notice of Project (NOP) document — the "linking" PDF that points to the full CSP package | ESBD portal — `https://www.esbd.cpa.state.tx.us/bid_show.aspx?bidid=...` (need full URL from user / ESBD search by Sol ID SSC-2025-06871) | **NOT YET DOWNLOADED** |

### B. Email-body data (verbatim summary)

The user's email-body summary (2026-05-27) contains the following authoritative data points; treat these as primary source-of-truth alongside the ESBD:

- Solicitation 2025-06871 — HUB Subcontracting Plan REQUIRED
- Submission: SSC Service Solutions, Facilities Services EDCS, 1371 TAMU (Physical: 600 Agronomy Road, Suite 218), College Station, TX 77843
- Proposal due **Wed 2026-06-17, 2:00 PM CT**; public open at 2:30 PM
- Pre-proposal mtg was **2026-05-19** at SSC Facilities Services Conf Rm S118 — **already past as of 2026-05-27**
- SSC PM: **Matt Wiederstein, 979-446-2733, `Matthew.Wiederstein@sscserv.com`**
- A/E: **Kelsie Srnensky, SZS Architecture, 512-751-3132, `kelsie@szsarchitecture.com`**
- HUB contact: **Patty Winkler, `p-winkler@tamu.edu`, 979-845-4556** (same contact as TAMU Harrington 2025-06813)
- TAMU Procurement / ESBD contact: **Cherise Toler, (979) 845-5887, `ctoler@tamu.edu`**
- Scope: expand Rm 340E into Rms A, D, DA — remove sink + appliances + casework + cabinetry; new MARRS glass wall along corridor; finish coordination

### C. ESBD-extracted addendum + status

- Status (as of last extraction): **Addendum Posted** (5/6/2026 4:50 PM — "Corrected Due Date" per ESBD)
- Posting requirement: 14+ Days for Entire Solicitation Package (compliant)
- Class/Item Code: 90900 — Building Construction Services, New (Incl. Maintenance And Repair Services)

## What's NOT yet on disk (the gap)

| Document | Why needed | Where to obtain |
|---|---|---|
| **Notice of Project PDF** (ESBD attachment) | Contains the link to the full CSP package | ESBD posting for Sol SSC-2025-06871 |
| **Full CSP package** (drawings, specs, proposal form, HSP form, UGSC, sample contract, bid bond form) | Required for takeoff, pricing, narrative, form-fill | Linked from the NOP — likely hosted on Trimble Unity Construct / e-Builder |
| **Pre-proposal meeting sign-in sheet** | Documents the May 19 attendance; useful for understanding which competitors are in the pool | Request from Matt Wiederstein |
| **Pre-proposal Q&A / recording** | Captures clarifications and addenda issued at the meeting; critical for technical clarity | Request from Matt Wiederstein |
| **Site survey / facility-condition assessment** | If available from prior work; helps refine takeoff | Request from Matt Wiederstein OR Kelsie Srnensky |
| **TAMU HUB Goal for this project** | Drives the HSP threshold | Request from Patty Winkler |
| **Prevailing wage determination** (Brazos County) | Required by Tex. Gov't Code Ch. 2258 | Usually in the CSP package; if not, request from Matt Wiederstein |

## How to retrieve the CSP package (Thu 2026-05-28 morning)

1. Open the ESBD posting page for Solicitation ID **SSC-2025-06871** in a non-corporate-network browser (Zscaler may otherwise intercept large PDFs)
2. Locate the attachment named `ESBD_513163_1778104136552_2025-06871_Notice of Project-CS_26.05.05.pdf`
3. Download it — should be < 500 KB; it is the cover sheet that points to the full CSP package
4. Open the NOP PDF and find the embedded URL for the Trimble Unity Construct / e-Builder bid package landing page
5. Open that URL in the same browser (it should be a public landing page; if it requires login, contact Matt Wiederstein for credentials)
6. Download every file listed on the bid-package page; the standard TAMU System CSP package contains:
   - Drawings (architectural, structural, MEP)
   - Specifications (CSI-formatted project manual)
   - Proposal Form (Section 00 42 13 — CSI-division line-item pricing table)
   - Technical Proposal Form (Section 00 45 16)
   - Safety/Risk/QC Form (Section 00 45 17)
   - Subcontracting Plan / VetHUB Form (Section 00 45 17.1)
   - Master Vendor Agreement (Section 00 52 63) — sample
   - UGSC (Section 00 72 00) — Uniform General Conditions
   - SGC (Section 00 73 00) — Supplementary General Conditions
   - Prevailing Wage Determination (Brazos County)
7. Place all files into a `local/` subdirectory of this workspace (gitignored per `bids/*/local/` rule)
8. Update this manifest with the actual file names + sizes downloaded
9. Re-run text-extraction on the key PDFs (drawings + specs + UGSC + proposal form) for AI-assisted analysis

## Reference / sister solicitations to cross-check

- **TAMU Harrington 2025-06813** (`bids/tamu-harrington-2025-06813/`) — same SSC + TAMU CSP pattern; same Patty Winkler HUB contact; pre-proposal was 2026-05-14 (also missed). Use that workspace's CSP-form-fill-guide and HSP-form-fill-guide as templates.
- **Angelo State Carr EFA 26-007** (`bids/angelo-state-carr-efa-26-007/`) — TTU System UGSC pattern; insurance limits and contractual terms are template-compatible with TAMU.

## Network / portal caveat

The Trimble Unity Construct portal uses Adobe-style multi-redirect downloads (iframe → handshake → POST → file). On the corporate network (Zscaler), some larger PDFs are intercepted. If a download fails, retry from a non-corporate-network browser or use a mobile hotspot.
