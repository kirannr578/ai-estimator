# Missing documents — HHSC Bldg 500 Mech HHS0017366

The OneDrive drop contains the **main IFB (41 pp)** and **Exhibits B, C, D, E, E-1, F**. Several items are referenced in the IFB but **not in the OneDrive drop**, or are present but unreadable beyond first-page extraction.

## Referenced in IFB §1.4 but NOT in the OneDrive drop

| Document | Status | Source |
|---|---|---|
| **Exhibit A — HHS Solicitation Affirmations** | 🔴 Missing | ESBD posting 520042 — `https://www.txsmartbuy.gov/esbd` |
| Solicitation Addendum Acknowledgement Form (Addendum 1 expected 2026-06-03) | 🔴 Pending posting | ESBD posting 520042 — pull on or after 2026-06-03 |

## Referenced beyond page 12 of the main IFB — needs deeper read

The scaffold-time extraction covered pages 1–12 of the 41-page IFB. The following sections are referenced in the TOC (page 2) but not yet transcribed in this workspace:

| IFB section | Pages (TOC) | Information we still need |
|---|---|---|
| §7 Scope of Work (full) | beyond 11 | Full SOW including any spec callouts beyond the 5 subsections currently captured |
| §8 Contract Terms | TBD | Period of performance, deliverables schedule, milestone payments |
| §10 Special Terms | TBD | Any contractor-furnished items, HHS-furnished items |
| §11 Solicitation Affirmations / UTCs cross-references | TBD | Which Exhibit A and B clauses control |
| §12.x Contractor Response to Deficiency, CAP, Performance | 24+ | Performance management framework |
| §13 Invoicing | 27 | Payment terms, retainage |
| §14 Insurance | 28+ | Coverage limits, additional-insured wording, umbrella requirements |
| §15 Screening of Responses | 31+ | Administrative screening + irregularity handling |
| §16 Evaluation | 32+ | **Critical** — confirms lowest-bid award (IFB) vs. best-value scoring (CSP-like) |
| Appendix A — Submission Instructions and Response Checklist | TBD | Final master checklist for what must be in the response |

## Exhibit C pricing sheet — double extension

| File | Issue | Resolution |
|---|---|---|
| `ESBD_520042_1779477694400_Exhibit_C Pricing_Sheet.xls.xlt` | The double extension `.xls.xlt` is a TX Comptroller template artifact (Excel 97–2003 template that ESBD's filesystem accidentally tagged as both `.xls` and `.xlt`). Modern Excel may refuse to open it. | Rename to `.xlt` (or `.xls`); Excel will open as a template; Save As `.xlsx` for editing. Do NOT modify the template structure — HHSC IFBs reject altered exhibits. |

## Site visit photos — gap

- HHSC scheduled on-site visit for 2026-05-28 + 2026-05-29 (past as of scaffold creation 2026-05-30).
- Per IFB §6.8.3, attendance is "strongly encouraged but not required" — non-attendance does not disqualify.
- However, the bid will be priced from imperfect information without site photos of (a) existing metal roof condition, (b) industrial generator footprint + access, (c) overhead-door opening dimensions + existing wall condition, (d) interior paint surface condition.
- **Action:** request photos from Ruben Aguero (956-364-8443 / 956-320-4394) — or schedule a make-up walk via the HUB Coordinator exception path (§6.2).

## Davis-Bacon / Tex. Gov't Code Ch. 2258 prevailing wage

| Document | Status |
|---|---|
| Cameron County prevailing wage schedule | `[NEEDS DEEPER READ — likely in IFB §7 or attached as an addendum]` |

## How to pull the missing Exhibit A

1. Open ESBD at `https://www.txsmartbuy.gov/esbd`.
2. Search for posting **520042** or solicitation **HHS0017366**.
3. Download `Exhibit_A` and any addenda into `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\`.
4. Re-run `tmp_smoke/ingest_landmark_05272026.py` to refresh inventory + text.
5. Update this file: mark Exhibit A complete.
