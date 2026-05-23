# Source files manifest — Angelo State Carr EFA 26-007

> Authoritative inventory of every source document referenced by this bid-prep + proposal-draft workspace. The PDFs themselves are NOT committed to git (the `inbox/` tree is gitignored). This manifest is the single place to look up "what document, what version, where on disk, what date?"
>
> Last refresh: **2026-05-23** (added 5 new ESBD attachments — drawings + project manual + Addendum #1)

---

## A. Files held locally in `inbox/opportunities/attachments/2026-05-21/`

All paths are relative to the repo root. All sizes are approximate (rounded to nearest 100 KB).

### Original RFCSP package (received 2026-05-21)

| # | Filename | Size | Source URL | Source date | Notes |
|---|---|---|---|---|---|
| 1 | `ESBD_516718_1778880767322_26-007 Carr EFA Dressing Room Renocation RFCSP.pdf` | ~0.4 MB | TX SmartBuy ESBD posting 516718 | 2025-10-22 (ESBD posting) | The RFCSP narrative — Sections A–L; signed cover page; submission instructions |
| 2 | `ESBD_516718_1778880829538_26-007 Carr EFA Dressing Room Renocation Attachment A.pdf` | ~0.2 MB | ESBD 516718 | 2025-10-22 | Attachment A — Bid form / proposal pricing form (where the bid number lives) |
| 3 | `ESBD_516718_1778880857161_Attachment B.2 - Sample Construction Services Agreement.pdf` | ~0.3 MB | ESBD 516718 | 2025-10-22 | Sample CSA — controlling contract form on award |
| 4 | `ESBD_516718_1778880869361_Attachment C - 2010 Uniform General Conditions and Supplementary General Conditions dated (TTUS edited 09.07.2023).pdf` | ~1.2 MB | ESBD 516718 | TTUS edit dated 2023-09-07 | UGSC + TTUS supplemental |
| 5 | `ESBD_516718_1778880887164_Attachment D - HSP (Historically Underutilized Businesses (HUB) Subcontracting Plan) documents.pdf` | ~0.6 MB | ESBD 516718 | 2025-10-22 | TX HSP form + GFE guidance + Method A/B instructions |
| 6 | `ESBD_516718_1778880901623_Attachment E - Tax Exemption Certificate.pdf` | ~0.1 MB | ESBD 516718 | 2025-10-22 | TX state tax-exempt cert for institutional construction |
| 7 | `ESBD_516718_1778880917414_Attachment F.1 - Tom Green County Prevailing Wage 2023 (TTUS).pdf` | ~0.4 MB | ESBD 516718 | 2023-07 (WD issue date) | TTUS-adopted Tom Green County prevailing wage determination (Building) |

### NEW: 5 attachments downloaded 2026-05-23 (this refresh)

| # | Filename | Size | Source URL | Source date | Notes |
|---|---|---|---|---|---|
| 8 | `26-007 Carr EFA Dressing Room Renovation Drawings Addendum 2.pdf` | ~2.1 MB | `https://www.txsmartbuy.gov/` ESBD attachment (no ESBD numeric prefix in upstream filename) | 2026-05-07 | Drawings Addendum 2 — adds 2 ADA shower receptors (sheet P201), mosaic tile T4 spec (sheet AF100), corridor 8" cans + emergency lighting (sheet E301), salvage of corridor 2x4 light fixtures to Makeup Room 108 (sheet AE100) |
| 9 | `26-007 Carr EFA Dressing Room Renovation Project Manual.pdf` | ~12.3 MB | `https://www.txsmartbuy.gov/` ESBD attachment | 2026-03-27 (Issue for Construction) | **796 pages.** Full specifications. 144 unique CSI sections spanning Div 00–28. PBK Architects Project No. 250402. Div 21 marked "NOT USED" (FP is owner-furnished). Section 00 31 00 (Available Project Information) NOT included — top open clarification. References "Job Order Contract" in places (PBK boilerplate) — clarification request open re. JOC vs. RFCSP's Construction Services Agreement |
| 10 | `ESBD_516718_1778880917415_26-007 Carr EFA Dressing Room Renovation Drawings Addendum 1.pdf` | ~3.9 MB | ESBD 516718 | 2026-04-15 | Drawings Addendum 1 — sizes the dressing-room vanity mirrors (24"x72"), clarifies HM frame finishes, confirms ADA grab-bar layouts in RR 1R9 + 1R10 |
| 11 | `ESBD_516718_1778880917416_26-007 Carr EFA Dressing Room Renovation Drawings 3.27.26 compressed.pdf` | ~9.8 MB | ESBD 516718 | 2026-03-27 | **38-sheet base drawing set.** PBK Architects + LEAF Engineers (MEP) + Lundy & Franke Engineering (structural). G-series (2), A-series (~17 incl. AF100 finish schedule), M-series (~7), E-series (~7), P-series (~3), FA-series (~2). No civil / no landscape / no structural sheets (interior-only). |
| 12 | `ESBD_516718_1779308778671_26-007 Carr EFA Dressing Room Addendum #1.pdf` | ~1.3 MB | ESBD 516718 | 2026-05-20 (meeting date) | Pre-Response Meeting deck + sign-in sheet. **Cover memo confirms meeting was NON-MANDATORY** (resolves R-01). Sign-in sheet lists 5 competitor firms (see `contacts.md` § C). Slide 17 confirms evaluation criteria: Cost 45 / Firm + Team 25 / Schedule 20 / Compliance 10 = 100. |

### Render artifact from analysis (2026-05-23)

| # | Filename | Size | Notes |
|---|---|---|---|
| 13 | `signin_p21.png` | ~0.3 MB | PNG render of Addendum #1 page 21 (sign-in sheet) — used for manual competitor extraction since OCR (Tesseract) is not installed locally. Safe to delete after competitor list is locked. |

---

## B. Storage location

All files above live in the local workspace at:

```
C:\Users\rnuduru1\Estimator\inbox\opportunities\attachments\2026-05-21\
```

The `inbox/` tree is gitignored (see repo `.gitignore`) and is NOT pushed to GitHub. To rehydrate this workspace on a new machine, re-download from the ESBD posting:

- **ESBD posting:** [TX SmartBuy ESBD 26-007RFCSP](https://www.txsmartbuy.gov/esbd/26-007RFCSP)
- **Solicitation #:** 26-007 (ESBD 516718)

---

## C. Verification commands (re-run after any rehydrate)

```powershell
# Confirm all 12 source PDFs + 1 sign-in PNG are present and non-empty
$dir = "inbox\opportunities\attachments\2026-05-21"
Get-ChildItem $dir -Filter "*.pdf" | Format-Table Name, Length -AutoSize
Get-ChildItem $dir -Filter "*.png" | Format-Table Name, Length -AutoSize
```

```powershell
# PyMuPDF page-count sanity check (re-run if drawings or PM change)
python -c "import fitz; print('Drawings:', fitz.open(r'inbox/opportunities/attachments/2026-05-21/ESBD_516718_1778880917416_26-007 Carr EFA Dressing Room Renovation Drawings 3.27.26 compressed.pdf').page_count, 'pages')"
python -c "import fitz; print('PM:', fitz.open(r'inbox/opportunities/attachments/2026-05-21/26-007 Carr EFA Dressing Room Renovation Project Manual.pdf').page_count, 'pages')"
```

---

## D. Provenance and chain of custody

| Action | Date | Actor | Method | Evidence |
|---|---|---|---|---|
| Original RFCSP package received | 2026-05-21 | Bid-prep lead | ESBD email notification | Files 1–7 in § A above |
| 5 new attachments downloaded | 2026-05-23 | Bid-prep automation (Cursor agent) | `Invoke-WebRequest` against ESBD attachment endpoints (URLs scraped from `data-href` attributes on the rendered ESBD posting) | Files 8–12 in § A above |
| Project Manual TOC + scope analyzed | 2026-05-23 | Bid-prep automation | PyMuPDF (`fitz`) extract of all 796 pages; regex on `^SECTION ##  ##  ##  TITLE` pattern → 144 unique CSI sections | Findings flow into `04-scope-of-work.md`, `08-contract-terms-flags.md`, `takeoff-template.json` |
| Drawings finish schedule extracted | 2026-05-23 | Bid-prep automation | PyMuPDF render of AF100; manual text extraction of room schedule (10 rooms / 3,115 SF total) | Findings flow into `04-scope-of-work.md` § "Project scope at a glance", `takeoff-template.json` `_meta.project_area_sf` |
| Sign-in sheet inspected for competitors | 2026-05-23 | Bid-prep lead (manual, image-based — Tesseract not installed) | PyMuPDF render of Addendum #1 p.21 to `signin_p21.png` → manual read | Competitor list in `contacts.md` § C and README "Known competitors" table |

---

## E. What's NOT in this manifest (yet)

- **Site walk photos / video** — pending site walk arranged with Hannah Bignall (top-priority open item)
- **Hazmat survey** — Project Manual Section 00 31 00 (Available Project Information) was not included in the issued PM; pending request to Hannah Bignall
- **Sub quotes** — none received yet; outreach drafts ready in `outreach/05-email-hub-subs-template.md`
- **Bonding agent capacity letter** — pending response from `outreach/03-email-bonding-agent.md`
- **Insurance broker UGSC Art. 5 confirmation** — pending response from `outreach/04-email-insurance-broker.md`
- **A/E firm direct contact** — PBK Architects identified from title blocks; direct contact info not yet captured (try via Hannah)
- **Any Q&A or amendments issued after 2026-05-20** — none observed on ESBD as of 2026-05-23; re-check ESBD daily until 2026-06-05

When any of these arrive, add a new row to § A above and update the relevant prep-doc.
