# Source files manifest — Allen Veterans Memorial 2026-4-49

The OneDrive folder `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\` is the canonical source. Binary artifacts are NOT mirrored into git (per repo convention; `inbox/` is gitignored). Reference paths below.

## Files in this drop relevant to G1 (Allen Veterans Memorial)

| # | File | Size | MD5 (head 64KiB) | Description |
|--:|---|--:|---|---|
| 1 | `2026-4-49 Legal Ad.pdf` | 107,135 B | `2fa128a1a4a11e1b66b695505f88460a` | Legal Ad / Notice to Bidders — 1 page. Published in *Allen American* 2026-05-22 + 2026-05-29. Provides high-level project name, deadline, portal URL, purchasing POC. |
| 2 | `Bid Invitation.pdf` | 62,414 B | `58d5b7adf55d16f594cefbef0fb28ea0` | IonWave Event Invitation — 11 pages. Provides issue date, response deadline, pre-bid Teams URL, bid-opening Teams URL, attachment index. **The attachment index lists three additional documents (IFB Packet, Bid Form XLSX, Exhibit 1) that are NOT in this drop.** |

## Files referenced but NOT in this drop

See [`03-missing-documents.md`](./03-missing-documents.md). Three documents must be pulled from IonWave before estimating can begin:

- IFB Packet — Veterans Memorial Improvements.pdf
- Bid Form.xlsx
- Exhibit 1 — Contractor Insurance Requirements & Agreement.pdf

## Pre-extracted text (for cross-referencing during scaffold authoring)

During scaffold creation on 2026-05-30, all PDFs in the 2026-05-27 batch were text-extracted via `tmp_smoke/ingest_landmark_05272026.py` (pypdf 6.12.1). The script's output (`tmp_smoke/landmark_05272026_inventory.json`) is gitignored but regenerable.

```powershell
.\.venv\Scripts\python.exe tmp_smoke\ingest_landmark_05272026.py > tmp_smoke\landmark_05272026_inventory.json
```

Page-1 + page-2 text for files #1 and #2 is captured inline in [`01-overview.md`](./01-overview.md), [`06-scope-outline.md`](./06-scope-outline.md), and elsewhere in this workspace where direct quotation supports a scaffold claim.

## Batch triage reference

This workspace is one of five fan-outs from the `05272026` batch — see [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) (group **G1**) for the full inventory + per-opportunity decisions.
