# Missing documents — USACE Fort Hood Staging W9126G26RA015

The 1,835-page compiled RFP is the source. Scaffold-time extraction read pages **1-50** (the SF 1442, CLIN schedule, FAR provisions in Section 00 21 00, FAR 52.215-1 Instructions to Offerors, and part of the FAR matrix in Section 00 21 16). Most of the spec book (Divisions 01 through 33) is still pending.

## Key data points still not captured

| Item | Likely location in RFP | Status |
|---|---|---|
| **Offer due date** | SF 1442 Item 13c (page 6 region) | 🔴 Missing — must locate before any further investment |
| **Contracting Officer (CO) name + contact** | SF 1442 Item 9 ("For Information Call") + Section L Block 17 | 🔴 Missing |
| **Contract Specialist (KO) name + contact** | Section L (Section 00 21 16 or supplementary instructions) | 🔴 Missing |
| **Section M evaluation factors** | Section 00 22 16 (Design-Bid-Build Selection Procedures) | 🔴 Missing — critical for go/no-go past-performance Gate 2 |
| **Period of performance (calendar days from NTP)** | Section F / Section 01 00 00.00 44 Construction Schedule | 🔴 Missing |
| **Pre-proposal conference + site visit dates** | Section L (Section 00 21 16) | 🔴 Missing |
| **Question / RFI cutoff date** | Section L (Section 00 21 16) | 🔴 Missing |
| **Davis-Bacon WD number** | Section 00 73 00 Supplementary Conditions or separate WD attachment | 🔴 Missing |
| **AT/OPSEC personnel screening requirements** | Section 01 01 10.00 44 | 🔴 Missing — drives 4-8 week lead time |
| **DPAS rating (if any)** | Section L provision near FAR 52.214-34 | 🔴 Missing |
| **DD-Form-1391 magnitude** | Sometimes Appendix; or the "Target Price Range" stated in Method of Acquisition is the public-facing magnitude | ✅ Captured ($5M-$10M) |
| **Bid security amount** | FAR 52.228-1 says 20% of bid OR $1M whichever less | ✅ Captured |
| **P&P bond percentage** | FAR 52.228-15 says 100% / 100% | ✅ Captured |
| **Drawings package** | Separate from spec book; typically a `Drawings.pdf` or `Drawings.zip` on the SAM.gov posting | 🔴 Likely a separate file not in the OneDrive drop |

## How to pull missing items

### From the existing compiled PDF

Extend the page-extraction range in `tmp_smoke/extract_fthood.py`:

```python
# Read pages 100-300 (Section 00 21 16 + 00 22 16 + Section L+M region)
ranges = list(range(100, 300, 10))
```

Then re-run:

```powershell
.\.venv\Scripts\python.exe tmp_smoke\extract_fthood.py > tmp_smoke\fthood_pages_l_m.json
```

### From SAM.gov

The compiled PDF is one of multiple attachments on the SAM.gov posting. Drawings are almost certainly a separate attachment. To pull:

1. Open `https://sam.gov/opp/<sam-opportunity-id>/view` (search for `W9126G26RA015`)
2. Download the full attachment set into `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\ft-hood-w9126g26ra015\` (create subfolder)
3. Drawings (`.pdf` or `.dwg`) — required for takeoff
4. Any amendments / SF 30s posted since 2026-05-21
5. The Davis-Bacon WD attachment if posted separately

### From USACE Fort Worth District directly

If SAM.gov is incomplete:

- USACE-FWD contracting office: `swfco-cz@usace.army.mil` (general inquiries)
- USACE-FWD construction-procurement contact varies by project; the CO name from SF 1442 Item 9 is the canonical contact

## What we CAN'T do without these items

- **Cannot estimate** without drawings + complete Sections L + M
- **Cannot run the go/no-go decision** without the offer-due date (Gate 4 estimating-ROI depends on bid-window length)
- **Cannot brief surety** without final-contract magnitude band and POP
- **Cannot draft Volume III past-performance** without the Section M past-performance evaluation factors
