# Source files manifest — Camp Maxey Bldg. 1 Roof Replacement

> **Source:** Single PDF *Camp Maxey Roof Replacement Project Information -2.pdf* received by
> the user from Adam's Trade & Services, Inc. and staged at
> `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\` on 2026-05-30 19:49 CT. The
> "Landmark" OneDrive folder is BPC's catch-all staging directory for incoming bid documents
> that the user has not yet fanned out into the per-bid OneDrive structure — the Landmark
> folder name is **not** an opportunity identifier (this opportunity is owned by TMD, with
> ATS as prime). PDF metadata: title "Camp Maxey Roof Replacement Project Information",
> creationDate `D:20260526184044-05'00'` (Adam's Trade authored 2026-05-26 18:40 CT),
> producer "Skia/PDF m150 Google Docs Renderer" (=Google Docs export). Extraction is fully
> deterministic (`pymupdf.fitz.open`); no LLM calls.

## Attachment inventory (extracted 2026-05-30)

| # | Path under `attachments/` | Size | Pages | Type |
|--:|---|---:|---:|---|
| 1 | `Camp Maxey Roof Replacement Project Information -2.pdf` | 2.0 MB | 8 | Adam's Trade Project Information document |

**Total:** 1 PDF, ~2 MB, 8 pages.

## Page-by-page contents (extracted text — verbatim, deterministic)

| Page | Length (chars) | Content |
|---:|---:|---|
| 1 | 767 | Cover sheet — Project Owner (TMD), Prime (Adam's Trade & Services, Inc.), submission email (`patrickgrabowski.ats@gmail.com`), questions cutoff (Tue 6/9), quote due (Fri 6/26), project location (6351 US 271 N Powderly TX 75473 Bldg. 1), site visit (Mon 6/1 8:00 AM CT or 1:00 PM CT), sales-tax-exempt note |
| 2 | 733 | **Pricing Schedule** — 5 line items: General Conditions & Mobilization, Demolition & Removal (all Roof Areas), Lower Roof Replacement, Upper Roof Replacement, Cleanup. Total Base Bid (Not to Exceed) |
| 3 | 2,167 | §1 Scope of Work (1.1 Goal, 1.2-1.4 materials/equipment/labor inclusion language), §1.5 Buy American Act citation (41 U.S.C. 10), §1.6 **Lower Roof Section** scope (1.6.1-1.6.9 detailed steps) |
| 4 | 2,538 | §1.7 **Upper Roof Section** scope (1.7.7-1.7.9 perimeter plywood + drip edge + counterflashing), §2 Additional Subcontractor Responsibilities (2.1-2.5), §3 Attachments (A. Photos, Camp Maxey Roof Replacement.pdf — *referenced but missing from drop*), §4 Milestones and Deliverables (submittals), §5 Project Specifications and Requirements (5.1 background checks, 5.2 Davis-Bacon Act / TX Ch. 2258 wage scale, 5.3 working hours, 5.4 daily cleanup, 5.5 garbage haul, 5.6-5.7 laws/regulations) |
| 5 | 2,347 | §5.7 Owner site rules (no alcohol / illegal substances, no smoking within building footprint or within 100 ft of doorway, no firearms/weapons, site-access management, competent workmen, safety-and-welfare responsibility, barricades/guard rails), §6 Workmanship Warranty (1 yr), §7 Manufacturer Warranty (per manufacturer), §8 Project Term (1 yr completion), §9 Project Laws and Codes (Local/State/Federal + OSHA), §10 Prior to Starting Project (10.1 personnel roster, 10.2 pre-construction meeting, 10.3 milestone approvals, 10.4 sub documents) |
| 6 | 2,039 | §10.4 (cont.) — W-9, COI (Liability + WC), Insurance per §12; §11 During Project (11.1 inspections, 11.2 substantial-completion walkthrough w/ ATS + Owner, 11.3 OSHA-compliant dress code); §12 Insurance Requirements (Certificate Holder = ATS, GL $1M occurrence/$2M aggregate, Auto $1M, WC statutory, ATS as additional insured, 30-day cancellation notice "to the State"); closing — Patrick Grabowski as POC |
| 7 | 9 | "PHOTOS:" heading only — **content missing** (likely intended placeholder for the Photos attachment referenced in §3.A) |
| 8 | 0 | Empty page (likely terminator) |

## Documents referenced but NOT in the drop

| Document | Status | Source reference |
|---|---|---|
| **Photos, Camp Maxey Roof Replacement.pdf** | 🔴 Missing | PDF §3.A (Attachment A) — placeholder heading on PDF p.7 with no image content |
| **Wind uplift calculations** | 🔴 Missing | PDF §§1.6.3 + 1.7.3 reference uplift calcs as the basis for fastener pattern + adhesive coverage |
| **TMD background-check form / process documentation** | 🔴 Not yet supplied | PDF §5.1 — TMD conducts background check; process not described in the drop |
| **TPO membrane manufacturer + system warranty spec** | 🔴 Missing | PDF §§1.6.4 + 1.7.4 — only generic "60 Mil TPO membrane" |
| **HD ISO board manufacturer + R-value** | 🔴 Missing | PDF §§1.6.3 + 1.7.3 — only "1/2" High Density ISO" |

**All five missing items must be requested from Patrick Grabowski before BPC's pricing build (Gate 5).** See [`02-bid-prep-checklist.md`](./02-bid-prep-checklist.md) Gate 4 for the email content to send.

## Where copies live

- Repo (committed, this directory): `bids/tmd-camp-maxey-roof-2026-0626/attachments/`
- OneDrive (read-only canonical original): `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\Camp Maxey Roof Replacement Project Information -2.pdf`

## PDF text-extraction note

Extraction was straightforward — the PDF carries embedded text (not a scanned image), with one
quirk: the PDF includes Unicode BOM characters (zero-width no-break space `U+FEFF`) that render
as `'\u200b'` artifacts in some Windows console encodings. Text was redirected to UTF-8 file
output to avoid `cp1252` encoding errors. The extracted text matches the rendered visual content
exactly; no OCR was needed.

## Lineage

This workspace **converts** the prior watchlist entry
[`bids/_WATCHLIST/powderly-bldg1-adams-trade-2026-0626.md`](../_WATCHLIST/powderly-bldg1-adams-trade-2026-0626.md),
which was created from the DFWMSDC Construction Members digest 2026-05-30 (Opportunity #2 —
"Powderly Bldg. 1, Adam's Trade & Services") with no scope. The Camp Maxey project-information
PDF (received separately by user 2026-05-30 19:49 CT) provides the previously-missing scope.
The watchlist file is retained with a CONVERTED banner pointing here; the watchlist `README.md`
table moves the Powderly row to "Resolved / closed".
