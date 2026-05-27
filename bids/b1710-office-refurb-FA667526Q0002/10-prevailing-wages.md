# Prevailing wages — Davis-Bacon Wage Determination TX20260270

> The applicable Davis-Bacon WD for this RFQ is **TX20260270** (Tarrant County, Building Construction, dated 02 Jan 2026, Modification 0). It is **Attachment 03** of the RFQ package. The PDF (232,261 B) is at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05072026\B1710+Office+Refurbish.zip\Construction WD Building TX20260270 02Jan2026.pdf`.
>
> ⚠️ **Same WD as the Cmd Post + NDI project** at NAS JRB Fort Worth — see `bids/cmd-post-ndi-W50S7626QA001/prevailing-wages.md` for the trade-by-trade rate table that has already been extracted and analyzed. The rates below cross-reference that document.

## A. WD identity

| Field | Value |
|---|---|
| WD Number | **TX20260270** |
| Modification Number | **0** |
| Publication Date | **02 Jan 2026** |
| Supersedes | TX20250270 |
| State | Texas |
| County | **Tarrant County** |
| Construction Type | **Building Construction** (excludes single-family homes and apartments up to 4 stories) |
| Source | Attachment 03 of FA667526Q0002 (referenced via FAR 52.222-6 in Section I) |

## B. Trades most relevant to B1710 scope

For this carpet + base + paint + drywall-patch scope, the trades that touch the project are:

| Trade | Estimated total loaded rate (2026) | Driver in scope |
|---|---|---|
| **Carpet / Resilient Floor Layer** | $26 – $34/hr | Carpet tile install (3,500 SF) + 6" rubber base (~1,200-1,500 LF) — dominant labor cost |
| **Painter** | $26 – $34/hr | Walls + drywall patch + Rm 1030 new wall (~12,000-15,000 SF wall area) |
| **Drywaller / Taper** | $30 – $38/hr | Rm 1030 doorway sheetrock-in + Rm 1008 patch (~50-60 SF GWB) |
| **Carpenter** | $32 – $40/hr | Metal-stud framing in Rm 1030 doorway (~7 LF) + access panel install in Rm 1008 |
| **Laborer (Group 1)** | $20 – $26/hr | Demo, debris hauling, daily cleanup, furniture relocation (~3-4 person-days) |

These ranges are the same as the Cmd Post + NDI project (same WD, same county). For the exact rates, **pull from Attachment 03 PDF directly** before finalizing the price proposal — the WD PDF in this package uses heavy form-layout encoding that doesn't extract cleanly to plain text. The Cmd Post workspace extracted only a partial trade list before encoding broke; this WD will need the same direct read.

> **`[AWAITING SOURCE-DOC PULL]`** — exact per-trade rates with explicit Base + Fringe + Total Loaded columns for Carpet Layer, Painter, Drywaller, Carpenter, Laborer. To unblock: open the PDF and transcribe the relevant trade rows. ETA: 30 minutes.

## C. Compliance mechanics during performance

Per FAR 52.222-6 + 52.222-8 + 52.222-10 (Section I clauses on this RFQ):

| # | Action | Frequency | Owner |
|---:|---|---|---|
| 1 | Post the WD at the jobsite (printed copy) | Once at NTP | Site superintendent |
| 2 | Submit weekly **WH-347 certified payroll** for prime + each sub | Weekly | PM (collect from subs Friday; submit to CO Monday) |
| 3 | WH-348 Statement of Compliance (signed by employer or authorized person) attached to each WH-347 | Weekly | PM |
| 4 | Maintain payroll records for 3 years post-completion | Continuous | Contracts admin |
| 5 | Post Notice to Employees (DOL Wage Theft poster) | Once at NTP | Site superintendent |
| 6 | If a trade classification not on the WD is needed, request a **Conformance** via the CO (form SF 1444) | As needed | PM |

## D. Apprenticeship + EEO flow-down

- FAR 52.222-9 limits apprentice ratio to that registered by USDOL or the State Apprenticeship Agency.
- Subcontractors must flow down DBA via FAR 52.222-11.
- Equal Opportunity flow-down per FAR 52.222-26 (verify on Section I; standard for federal construction).

## E. Common errors → CO holds payment

| Error | How to avoid |
|---|---|
| Wrong wage code (e.g., paying carpenter rate to a tile-setter) | Use the WD's exact trade titles; conform via SF 1444 if a unique classification needed |
| Missing fringe benefit accounting | Show fringe as either cash-paid or paid-into-bona-fide-plan; do not roll into base rate without disclosure |
| Apprentice pay above approved ratio | Track apprentice-to-journeyman ratio per trade per project |
| Late certified payroll | Submit weekly without fail; even 1-week delay can trigger CO funds withholding |
| Sub failure to submit certified payroll | Prime is responsible — collect from subs as condition of sub progress payment |

## F. Where to pull the full current WD

- **SAM.gov Wage Determinations**: `https://sam.gov/wage-determinations` — search for `TX20260270`. If a superseding WD has been issued since 02 Jan 2026, the SAM.gov-current version is the version that applies to any modification of this contract; but **the version embedded in this solicitation (Attachment 03) governs the award**.
- **DOL WHD**: `https://www.dol.gov/agencies/whd/` (Construction Wage Determinations search).

## G. Davis-Bacon impact on the bid number

For a target bid value of ~$50K-$70K all-in:

- Labor is typically 40-55% of direct cost on a finishes-heavy interior-renovation project (carpet + paint + drywall = labor-dominant).
- DBA-compliant rates are typically 5-15% above DFW-area market non-prevailing rates for these trades.
- This is already baked into the loaded unit costs in `09-price-references.md`.
- Certified payroll prep overhead: $50-100/wk (in-house) or $150-250/wk (service); 13 weeks × ~$200 = ~$2,600 included in general conditions line.
