# Source files manifest — B1710 Office Refurbishment

The full RFQ package is on OneDrive (canonical binary artifacts are NOT mirrored into git per the firm policy in `firm/firm-profile.json`). Reference paths below.

## Solicitation package

**ZIP (canonical archive):**
`C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710+Office+Refurbish.zip` (957,696 bytes; downloaded 2026-05-27 13:22 CDT)

**Contents (verified 2026-05-27):**

| # | File | Size | Description |
|---|---|---:|---|
| 01 | `Solicitation - FA667526Q0002.pdf` | 566,614 B | **The RFQ itself (SF 1449 + Schedule + Sections E/F/G/I/L/M)**, 25 pages, issued 29 Apr 2026 |
| 02 | `SOW for B1710 Office Refurbish.docx` | 59,068 B | Statement of Work — Attachment 01, dated 24 Apr 2026 |
| 03 | `B1710 Floorplan for Refresh Project.pdf` | 224,181 B | Attachment 02 — Floor plan with carpet/base/paint zones marked (24 Apr 2026) |
| 04 | `Construction WD Building TX20260270 02Jan2026.pdf` | 232,261 B | Attachment 03 — Davis-Bacon Wage Determination, Tarrant County Building Construction, modification dated 02 Jan 2026 |
| 05 | `AF3000 Material Submission Form.pdf` | 104,948 B | Attachment 04 — AF IMT 3000 form template for material submittals (post-award) |
| 06 | `Request For Information Form.pdf` | 52,721 B | Attachment 05 — RFI form template |

## How to access during prep

Open the zip directly (no need to extract):
```powershell
Add-Type -AssemblyName System.IO.Compression.FileSystem
$z = [System.IO.Compression.ZipFile]::OpenRead('C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710+Office+Refurbish.zip')
$z.Entries | Format-Table FullName, Length
```

Or extract once into a working folder:
```powershell
Expand-Archive 'C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710+Office+Refurbish.zip' -DestinationPath 'C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710-extracted' -Force
```

## Pre-extracted text dumps (for cross-referencing during scaffold authoring)

During scaffold creation on 2026-05-27, the 6 source files were text-extracted to a temp folder for quick reference: `.tmp_extract/txt/` (gitignored). To regenerate:

```powershell
.\.venv\Scripts\python.exe .tmp_extract\extract_text.py
```

The extracted text files are referenced inline in the scaffold (e.g. SOW §3.1.2 quoted in `02-scope-of-work.md`) so the user can verify any quote against the source PDF.

## Re-extraction confirmation — 2026-05-27 21:30 CDT

Re-extracted the zip into `%TEMP%\b1710_extract\` and re-parsed all 6 source files with `pymupdf` 1.27.2.3 (PDFs) and `xml.etree` on `word/document.xml` (DOCX). Results:

| File | Extraction | Note |
|---|---|---|
| `Solicitation - FA667526Q0002.pdf` | ✓ clean (68,773 chars / 25 pages) | All Section A–M plain-text extractable |
| `SOW for B1710 Office Refurbish.docx` | ✓ clean (10,550 chars) | DOCX → XML walk |
| `B1710 Floorplan for Refresh Project.pdf` | ⚠ partial (850 chars) | Vector floor-plan; room numbers + C/B/P labels extract, geometry does not |
| `Construction WD Building TX20260270 02Jan2026.pdf` | ✗ encoding-locked | Type3 font with custom CMap; OCR not available (no Tesseract on Windows). WD trade rates remain `[AWAITING SOURCE-DOC PULL]` in `10-prevailing-wages.md` |
| `AF3000 Material Submission Form.pdf` | ✓ clean (4,321 chars) | Form template; metadata (AF IMT 3000, 20030901, V1; OMB 9000-0062) folded into `02-scope-of-work.md` §7 |
| `Request For Information Form.pdf` | ✓ clean (1,528 chars) | Pre-routes "TO (Contracting Officer): 301 CONF/PK" — note added to `08-contacts.md` |

No new source-doc surprises. All previously-captured facts in the workspace markdown cross-check against the re-extracted text. The `[AWAITING …]` markers remaining in the workspace are all legitimately pending (per-trade DBA rates, price builds, firm-side documents) and not addressable from the source zip alone.

## Files NOT in the package

The following are typically present in larger federal construction RFQs but are **absent** from this 25-page SAP RFQ — flagged here so the user doesn't search for them:

- No bid bond form (SF 24) — bid bond is **not required** (the package contains FAR 52.228-13 *Alternative Payment Protections* requiring a payment bond OR ILC for 100% of contract price **within 10 days of award**, not pre-award)
- No SF 1442 — this RFQ uses **SF 1449** (Commercial Items form) because it's procured under FAR Part 12 Commercial Item Procedures
- No specs book / project manual — the SOW (Attachment 01) is the full technical specification
- No reps & certs questionnaire to complete on the offer — package relies on **SAM.gov-posted reps & certs** per DFARS 252.204-7998 Alternate A (Deviation 2026-O0043); offeror selects the SAM-posted box and submits
- No drawings beyond the single floor plan — single-page A-1 partial floor plan at Attachment 02 marking C/B/P (Carpet/Base/Paint) zones in 16 rooms + hallways
