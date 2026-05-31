# Source files manifest — USACE Fort Hood Staging W9126G26RA015

The OneDrive folder `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\` is the canonical source. Binary artifacts are NOT mirrored into git.

## Files in this drop relevant to G5 (USACE Fort Hood Staging)

| # | File | Size | MD5 (head 64KiB) | Pages | Description |
|--:|---|--:|---|--:|---|
| 12 | `W9126G26RA015_Compiled.pdf` | 12,648,619 B (~12.65 MiB) | `237330d6dfa14df2ed64ceffe24cd9bc` | **1,835** | Compiled RFP. Single PDF combining: cover sheet (May 2026), Project Table of Contents, SF 1442 form, Section 00 10 00 CLIN schedule, Section 00 21 00 Instructions (full FAR provisions text), Section 00 21 16 Section L matrix, and all spec sections under Divisions 00 through 33 + Appendix A Justification & Approval. **Likely missing: drawings package** (typically a separate file on the SAM.gov posting). |

## Document anatomy (transcribed from pages 1-50)

| Section | Pages (approx.) | Content |
|---|---|---|
| Cover sheet | 1 | "Design-Bid-Build Request for Proposal, STAGING/MARSHALLING AREA, Fort Hood, Texas, W9126G26RA015, MAY 2026, Total Small Business Set-Aside, Fort Worth District" |
| Project Table of Contents | 2-5 | Lists every spec section under Divisions 00-33 + Appendix A |
| SF 1442 (Solicitation, Offer, Award) | ~6+ | Standard federal SF 1442 form; Item 13c offer-due-date NOT YET LOCATED |
| Section 00 10 00 CLIN Schedule | ~11-12 | 7 CLINs: 0001-0002 base + 0003-0007 options |
| Section 00 21 00 Instructions | ~16+ | FAR provisions incorporated by full text (52.204-7 SAM Registration, etc.) |
| Section 00 21 16 Instructions, Conditions, Notices to Offerors | TBD | **Critical — Section L** |
| Section 00 22 00 Supplementary Instructions | TBD | |
| Section 00 22 16 Design-Bid-Build Selection Procedures | TBD | **Critical — Section M evaluation factors** |
| Section 00 45 00 Representations and Certifications | TBD | FAR matrix |
| Section 00 70-73 Conditions | TBD | General + Supplementary Conditions |
| Divisions 01-33 spec book | bulk of pages 50-1800 | Spec sections per Project TOC |
| Appendix A Justification & Approval | end | Documents the set-aside basis |

## ESBD / SAM.gov posting reference

| Field | Value |
|---|---|
| SAM.gov solicitation ID | W9126G26RA015 |
| USACE District | **Fort Worth District (W9126G prefix)** |
| Likely SAM.gov URL pattern | `https://sam.gov/opp/<sam-opportunity-id>/view` (search by W9126G26RA015) |
| SBA Case Number | 347768 |

## Pre-extracted text dumps

Generated 2026-05-30:

- `tmp_smoke/landmark_05272026_inventory.json` — first-page text from all 12 batch files
- `tmp_smoke/landmark_05272026_more.json` — pages 1-12 of HHS IFB, TPWD IFB; pages 1-6 of this Fort Hood RFP
- `tmp_smoke/fthood_pages.json` — extra pages from this Fort Hood RFP

All `tmp_smoke/` files are gitignored. To regenerate:

```powershell
.\.venv\Scripts\python.exe tmp_smoke\ingest_landmark_05272026.py > tmp_smoke\landmark_05272026_inventory.json
.\.venv\Scripts\python.exe tmp_smoke\extract_more.py > tmp_smoke\landmark_05272026_more.json
.\.venv\Scripts\python.exe tmp_smoke\extract_fthood.py > tmp_smoke\fthood_pages.json
```

The scaffold has only read **pages 1-50 of 1,835**. The vast majority of the spec book is pending — see [`03-missing-documents.md`](./03-missing-documents.md). Detailed extraction is gated on the go/no-go decision in [`go-no-go-decision.md`](./go-no-go-decision.md).

## Likely-missing companion documents

| Document | Where it should live |
|---|---|
| **Drawings package** (Architectural, Civil, Structural, MEP) | Separate PDF or ZIP on the SAM.gov posting |
| Amendments / SF 30s posted since 2026-05-21 | Separate files on the SAM.gov posting |
| Davis-Bacon WD attachment (if not embedded in 00 73 00) | Separate file on the SAM.gov posting |
| Q&A / clarifications addendum | Future; posted on SAM.gov as the bid window progresses |

## Batch triage reference

[`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (group **G5**).
