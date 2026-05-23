# source-files-manifest.md

> Source files retrieved from the TAMU Harrington Lab 303 e-Builder Public Landing.
> Not committed to git — these are large binary PDFs published by SSC Compass / Patterson Architects via the formal procurement channel. They live locally and serve as the source for the takeoff and proposal content under this folder.

## Portal pull

- **Date attempted:** 2026-05-23
- **Source URL:** `https://app.e-builder.net/public/publicLanding.aspx?QS=323d686fd1304ccbb2a0ee7d143af64b`
- **Result:** PUBLIC — 4 of 5 files retrieved programmatically; 1 of 5 intercepted by Zscaler Cloud Browser Isolation and saved as the interception HTML.
- **Local location:** `inbox/opportunities/attachments/2026-05-21/tamu-csp/`

## File inventory

| Local filename | Size | Source description |
|---|---|---|
| `Harrington_Lab303_Drawings.pdf` | 5.6 MB | Full architectural + MEP drawing set (A0.1–E1.2, plus MEP1.0) |
| `Harrington_Lab303_Specifications.pdf` | 5.4 MB | Full Project Manual including CSP §00 21 00, §00 42 13 Proposal Form, SSC UGSC, Spec Divisions 01, 02 26 23, 09 22 00, 09 51 00, 09 65 00, 09 91 00, 10 14 00 |
| `Pre-Bid_Attendance.pdf` | 162 KB | Sign-in sheet from the 2026-05-13 pre-proposal meeting |
| `Notice_of_Project_2026-05-08.pdf` | 264 KB | Original ESBD-published Notice of Project (mirrors the inbox copy) |
| `H2I_Casework_Sub-06_2026-05-13.FAILED.html` | 4.5 KB | **NOT retrieved** — Zscaler CBI interception page. The actual file is the H2I (Hospital to Innovate) Casework Sub-06 specification published as a supplement on 2026-05-13. |

## How to retrieve the failed file

The H2I Casework Sub-06 file is blocked by Zscaler Cloud Browser Isolation on the corporate network. Two recovery paths:

1. **Manual download from a non-corporate network** (home Wi-Fi, mobile hotspot) — same e-Builder public landing URL above, click "H2I Casework Sub-06" from the file listing, save to `inbox/opportunities/attachments/2026-05-21/tamu-csp/` overwriting the `.FAILED.html`.
2. **Direct request to Joelle Shidemantle** (`Joelle.Shidemantle@sscserv.com`, (979) 286-3497) — see the outreach email template at `outreach/01-email-joelle-shidemantle-eligibility.md` § Point 3.

## Why the PDFs are not in git

- `inbox/` is the workspace pattern for "raw source-of-truth procurement docs" — they live local-only by convention (see the git status at the start of this conversation, where ~30 other procurement PDFs in sibling `inbox/opportunities/attachments/2026-05-21/` paths are similarly untracked).
- The PDFs total ~11 MB and are formally distributed via the e-Builder portal — any team member can re-download them with the URL above.
- Bid-prep deliverables under `bids/tamu-harrington-2025-06813/` (Markdown + JSON + this manifest) are committed and reference the source files by name.

## Drawing index (from `Harrington_Lab303_Drawings.pdf`)

| Sheet | Title |
|---|---|
| A0.1 | Cover Sheet + Drawing Index |
| A0.2 | TAS / ADA Sheet 1 |
| A0.3 | TAS / ADA Sheet 2 |
| A1.1 | Demolition Plan — Lab 303 |
| A2.1 | New Floor Plan + Finish Schedule — Lab 303 |
| A2.2 | Reflected Ceiling Plan + Casework Elevations — Lab 303 |
| M1.1 | Mechanical Plan — Lab 303 |
| MEP1.0 | MEP Specifications + Schedules |
| P1.1 | Plumbing Plan — Lab 303 |
| E1.1 | Electrical Power + Special Systems Plan — Lab 303 |
| E1.2 | Lighting + Controls Plan — Lab 303 |

## Key spec sections (from `Harrington_Lab303_Specifications.pdf`)

| Section | Title |
|---|---|
| 00 11 16 | Invitation for Proposals |
| 00 21 00 | Instructions to Proposers (evaluation criteria: Price 60%, Construction Time 10%, Respondent Qualifications 30%) |
| 00 42 13 | Proposal Form (CSI-division line-item lump-sum + Substantial Completion days; no bid bond, no alternates, no unit prices) |
| 00 43 36 | VetHUB Subcontracting Plan |
| 00 61 13 | Performance Bond Form |
| 00 61 14 | Payment Bond Form |
| 00 72 00 | General Conditions (SSC UGSC reference) |
| 00 73 00 | Supplementary Conditions (references SSC/Compass Master Vendor Agreement) |
| 01 33 00 | Submittal Procedures |
| 01 34 00 | Shop Drawings, Product Data, and Samples |
| 01 77 00 | Closeout Procedures |
| 01 78 20 | Facilities Management Data |
| 01 78 23 | Operation and Maintenance Data |
| 02 26 23 | Asbestos Assessment (procedural; no abatement scope unless EHS finds material) |
| 09 22 00 | Non-Structural Metal Framing + GWB |
| 09 51 00 | Acoustical Ceilings |
| 09 65 00 | Resilient Flooring |
| 09 91 00 | Painting |
| 10 14 00 | Signage |

## Divisions explicitly NOT USED (per spec table of contents)

03 (concrete), 04 (masonry), 05 (metals), 07 (thermal/moisture protection), 08 (openings — existing door + frame + hardware remain), 11 (equipment — no fume hood, no lab equipment), 12 (furnishings), 13 (special construction), 14 (conveying), 31–33 (earthwork / utilities / exterior).

This pruning is the single most important takeoff input: it eliminates the biggest single source of bid-envelope width (fume-hood scope) and the second-biggest (new exterior door + hardware).
