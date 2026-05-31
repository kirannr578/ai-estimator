# Source files manifest — HHSC Bldg 500 Mech HHS0017366

The OneDrive folder `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\` is the canonical source. Binary artifacts are NOT mirrored into git. References below.

## Files in this drop relevant to G2 (HHSC Bldg 500 Mech)

| # | File | Size | MD5 (head 64KiB) | Pages | Description |
|--:|---|--:|---|--:|---|
| 3 | `ESBD_520042_1779477645212_HHS0017366_PCS_137_Building 500 Mechanical Room Renovation.pdf` | 437,241 B | `f1d30268a45d5f5f29cd843cf5c98ccb` | 41 | **Main IFB** — PCS 137 template v2.10 (Rev 2026-03-18). Sections 1–16 + Appendix A. |
| 4 | `ESBD_520042_1779477672947_Exhibit_B_PCS_111_HHS_UTCs_and_HHS_Affirmations_No_DUA.pdf` | 704,982 B | `810b472c507787d92af5767226e3f84b` | 35 | **Exhibit B** — HHS Contract Affirmations + Uniform Terms & Conditions (UTCs), v2.9, effective March 2026. "No DUA" = no Data Use Agreement needed for this solicitation. |
| 5 | `ESBD_520042_1779477694400_Exhibit_C Pricing_Sheet.xls.xlt` | 45,056 B | `faae4044b568c69ae39a8c4b9ea52d0b` | n/a | **Exhibit C** — Pricing sheet template (Excel 97-2003). **Double extension `.xls.xlt`** is a TX Comptroller artifact; rename to `.xlt` if Excel refuses to open. **Do not modify the template structure.** |
| 6 | `ESBD_520042_1779477713531_Exhibit_D_Bidder_Reference_Qualifications_Form_(01-21-26).pdf` | 106,365 B | `67cfd87a7d5658e0c2549e5c7c967d29` | 5 | **Exhibit D** — Bidder Reference + Contractor Qualifications Form. Requires minimum 3 verifiable references, last 5 years, similar size/scope. Plus company info (years in business, employee counts, geographic limits, industry certs, applicable staff licenses). |
| 7 | `ESBD_520042_1779477735493_Exhibit_E_Online_Bid_Room_Information_v.1.4_(07-22-25).pdf` | 104,855 B | `276ef9324d5c4a2bcd03557cd05bf28f` | 2 | **Exhibit E** — HHS Online Bid Room (IAMOnline) registration instructions. **Critical: multi-day registration process; start immediately.** Note: header labels it "Exhibit F" but it is Exhibit E per the IFB §1.4 component list. |
| 8 | `ESBD_520042_1779477761792_Exhibit_E-1-PCS_Map_Directions_(01-21-2026).pdf` | 4,048,179 B | `ac3d78eb3b1b6789f0da36580788f867` | 2 | **Exhibit E-1** — Map and directions to HHSC PCS (1100 W 49th St, Austin) for in-person bid drop. Coordinates 30.32115, -97.73325. Office hours 8 AM – 5 PM CT. |
| 9 | `ESBD_520042_1779477785436_Exhibit_F_Form_4109_Application_for_TIN_(01-21-2026).pdf` | 256,023 B | `35c905b8ace5d31f6c0a2e0b24fa6b5c` | 2 | **Exhibit F** — TX Comptroller Form 4109 (Application for Texas Identification Number), Feb 2022 revision. BPC already has a TIN — fill Section I option 3 with the existing TIN. |

## Files referenced in IFB §1.4 but NOT in this drop

| Document | Status |
|---|---|
| **Exhibit A — HHS Solicitation Affirmations** | 🔴 Missing — pull from ESBD posting 520042 |

See [`03-missing-documents.md`](./03-missing-documents.md) for the full gap list.

## ESBD posting reference

| Field | Value |
|---|---|
| ESBD posting ID | **520042** |
| ESBD URL | `https://www.txsmartbuy.gov/esbd` (search by posting ID or by HHS0017366) |
| Recommended browser | Google Chrome (per §5.h note in the IFB definitions) |

## Pre-extracted text dumps

Generated 2026-05-30 via `tmp_smoke/ingest_landmark_05272026.py` + `tmp_smoke/extract_more.py`. Output JSON in `tmp_smoke/` (gitignored). Regenerable.

```powershell
.\.venv\Scripts\python.exe tmp_smoke\ingest_landmark_05272026.py > tmp_smoke\landmark_05272026_inventory.json
.\.venv\Scripts\python.exe tmp_smoke\extract_more.py > tmp_smoke\landmark_05272026_more.json
```

The scaffold currently references content from **pages 1–12** of the main IFB. Pages 13–41 are pending — see [`03-missing-documents.md`](./03-missing-documents.md) § "Referenced beyond page 12".

## Batch triage reference

[`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (group **G2**).
