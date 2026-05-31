# Missing documents — TPWD Old Tunnel Stairs 802-26-79308

The OneDrive drop contains the **full 48-page bound IFB** with Attachments A, B, C, D, E. The scaffold has read pages 1–12 in detail. The remainder needs a deeper read before estimating can begin.

## Within the existing 48-page document — needs deeper read

| Attachment / Section | Pages (approx.) | What we need |
|---|---|---|
| **Attachment A — General Terms and Conditions for Minor Construction (Sept 2025)** | 10+ | Performance + Payment bond threshold (TPWD typically follows Tex. Gov't Code Ch. 2253 statutory thresholds — confirm); standard clauses on assignment, audit, termination, dispute resolution |
| **Attachment B — Specifications + Kendall County Prevailing Wage** | TBD | **Critical** — actual stair construction spec, materials, ADA / IBC reference standards, finishes, prevailing wage labor classifications |
| **Attachment C — Drawings** | TBD | **Critical** — sheet count, scale, plan + section views of the lower-loop stair, dimensions, foundation detail |
| **Attachment D — Contractor's Qualifications Form** | TBD | Form blanks to complete + supporting documents to attach |
| **Attachment E — Bid Schedule** | TBD | Bid-form line structure (lump sum vs. unit-price), allowance lines, alternates |

## Reasonable inferences pending deeper read

| Item | Inference (subject to confirmation) |
|---|---|
| Stair material | Wood (pressure-treated southern yellow pine or cedar) — typical TX state park trail stair |
| Stair construction | Stringer + tread + riser, possibly with cribbed retaining at higher rise sections; handrails per IBC §1014 |
| Tread depth / riser height | TX state park trails typically follow IBC §1011.5 with field allowances for terrain |
| ADA compliance | If the lower loop is designated accessible, ADA standards apply; otherwise IBC residential / state-park standards |
| Foundation | Concrete piers or helical piles for posts; surface-set timbers for stringers in lighter applications |
| Demo of existing stairs | Contractor responsible (§6.5 broad debris-removal language); confirm where waste goes |
| Performance + Payment bond | Likely 100% / 100% per Tex. Gov't Code §2253.021 if final contract > $50,000 (P&P) and > $25,000 (P only); confirm against Attachment A |

## How to read the remainder

```powershell
# Manually open in PDF viewer:
ii 'C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\ESBD_520362_1779834504715_IFB 802-26-79308_Stair Replacement at Old Tunnel State Park.pdf'

# Or regenerate text extraction (covers pages 1-12 by default; edit the script to expand):
.\.venv\Scripts\python.exe tmp_smoke\extract_more.py > tmp_smoke\landmark_05272026_more.json
```

## Other documents likely needed (not yet referenced or absent)

| Document | Why needed |
|---|---|
| TPWD vendor performance score (CPA VPTS) | Verify BPC's score ≥ C and no active Corrective Action Plan before submission (Attachment A §3.3.6 may disqualify) |
| BPC HUB certification | If current, claim preference under Title 34 TAC Rule 20.38 on cover page |
| BPC TX SOS franchise-tax good-standing | TX state procurement standard |
| Bond letter (current) | Bid bond if estimate > $25K |
| COI naming State of Texas + TPWD as additional insured + loss payee | §11.3 dual designation; coordinate with broker |
| Wildlife biology / bat-colony coordination memo | Site-specific risk; ask Izzy Mabry at site visit |
