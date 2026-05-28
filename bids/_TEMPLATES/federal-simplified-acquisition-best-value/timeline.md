# {{PROJECT_NAME}} — Timeline (SAP Compressed Cycle)

> Backwards-planned from the quote due date.
> **SAP RFQs run on a compressed cycle** — 14–30 days from RFQ release to quote due, vs. LPTA's 30–45 or FAR 15's 45–90. Plan accordingly.

## Key dates (anchor)

| Milestone | Date | Owner |
|---|---|---|
| RFQ capture | `{{RFP_CAPTURE_DATE}}` | PM |
| RFQ release on SAM.gov | `{{RFP_RELEASE_DATE}}` | — |
| Site visit | `{{SITE_VISIT_DATE}}` | PIC / Estimator |
| RFI cutoff | `{{RFI_CUTOFF_DATE}}` | PM |
| Quote due | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` | PM |
| Acceptance period through | `{{ACCEPTANCE_THROUGH_DATE}}` (DUE + `{{ACCEPTANCE_PERIOD_DAYS}}` cal days; typ 60 on SAP) | — |
| Anticipated award | `{{AWARD_TARGET_DATE}}` (SAP awards typically T+30 to T+60 from RFQ release) | — |
| NTP target | `{{NTP_TARGET_DATE}}` | — |
| Substantial completion target | NTP + `{{POP_DAYS}}` cal days | — |
| Final completion target | per RFQ | — |

## Bid-prep schedule (backwards-planned from due date — SAP compressed)

| Day | Date | Activity | Owner |
|---|---|---|---|
| Due − 20 | `{{DUE_MINUS_20}}` | Bid-decision review; compliance posture check; firm-profile applier run; workspace scaffolded from `bids/_TEMPLATES/federal-simplified-acquisition-best-value/`; RFQ attachments read; form-and-procurement disambiguation per `03-missing-documents.md` §0 | PIC + PM |
| Due − 18 | `{{DUE_MINUS_18}}` | Subscribe to SAM.gov amendment notifications; sub solicitations issued (≥ 3 per trade — compressed window); prior-experience reference contacts verified by phone/email (need 3–5) | PM |
| Due − 15 | `{{DUE_MINUS_15}}` | Site visit; takeoff started; RFI candidates drafted; bond + insurance refreshed | PIC + Estimator |
| Due − 12 | `{{DUE_MINUS_12}}` | RFIs filed before cutoff (typ 3 cal days after site visit) | PM |
| Due − 10 | `{{DUE_MINUS_10}}` | RFI responses + SF-30 amendments absorbed | Estimator |
| Due − 8 | `{{DUE_MINUS_8}}` | Sub quotes due (5 working days before submission); takeoff complete; pricing rollup started; **technical-capability narrative drafted in parallel** | Estimator + PM |
| Due − 6 | `{{DUE_MINUS_6}}` | Quote package sections assembled: cover note, SF-18, Reps & Certs, price section, technical narrative, key personnel, prior experience | PM |
| Due − 4 | `{{DUE_MINUS_4}}` | Pricing locked; Schedule of Prices finalized; surety commitment letter received; **"groups of 3" stress test** per `08-pricing-strategy.md` §4 | PIC + PM |
| Due − 3 | `{{DUE_MINUS_3}}` | Final amendment scan on SAM.gov; quote package combined into single PDF; transmittal email drafted with exact subject per Section L | PM |
| Due − 2 | `{{DUE_MINUS_2}}` | Final QC pass by second team member; placeholder scanner run | PM + reviewer |
| Due − 1 | `{{DUE_MINUS_1}}` | Final amendment check; submission package frozen | PM |
| Due | `{{DUE_DATE}}` | Submit ≥ 30 min before `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` via email (typ on SAP) | PM |

## Parallel work tracks

| Track | Owner | Cadence |
|---|---|---|
| Compliance refresh (SAM, COIs, bond letter, prior-experience references) | PM | Days 1–8 of bid prep |
| Sub procurement | PM | Days 1–12 of bid prep (compressed sub windows) |
| Takeoff + pricing | Estimator | Days 4–16 of bid prep |
| RFI tracking | PM | Days 4–10 of bid prep |
| **Technical-capability narrative drafting** | PM (with Estimator input on trade approach) | **Days 6–14 of bid prep — do not defer; it is the differentiator** |
| Quote package assembly | PM | Days 12–18 of bid prep |
| Final QC | PM + reviewer | Days 16–19 of bid prep |
