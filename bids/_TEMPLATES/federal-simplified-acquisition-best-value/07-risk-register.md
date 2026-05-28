# {{PROJECT_NAME}} — Risk Register

> **Use:** Internal bid-decision tool + estimating-side contingency justification. **Not** in the proposal.
> Risks are scored Impact × Likelihood (each 1–5); priority score = product.

## 1. Bid-side risks (decision-to-bid through submission)

| # | Risk | Impact | Likelihood | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| B1 | SAM.gov registration lapses or Reps & Certs > 12 months | 5 | `[USER TO FILL — 1 if confirmed current, 5 if stale]` | | Verify before pricing begins; refresh if needed (3–10 working days) | PM |
| B2 | Bond commitment letter not on file at submission | 5 | `[USER TO FILL]` | | Order with surety on Day 1 of bid prep (3–5 working days) | PM |
| B3 | Insurance COIs stale or below required limits | 4 | `[USER TO FILL]` | | Pull current COIs from agent on Day 1 (same-day) | PM |
| B4 | Wage Determination amended mid-bid by agency SF 30 | 3 | 2 | 6 | Watch SAM for amendments through cutoff; re-price labor if WD changes | Estimator |
| B5 | Site-visit no-show — takeoff risk widens | 4 | `[USER TO FILL]` | | Attend site visit; if missed, bump contingency to 7–8% | PIC |
| B6 | RFI not answered by cutoff | 3 | 3 | 9 | File RFIs early (within Days 5–10); not Days 25–28 | PM |
| B7 | Prior-experience reference contact unreachable (need 3–5 on SAP) | 4 | 3 | 12 | Pre-confirm 3–5 references by working phone + email on Days 3–7 (compressed SAP timeline) | PM |
| B8 | Boilerplate-leakage in RFQ — pricing assumption wrong (stale POP, wrong project name) | 4 | 4 | 16 | Walk every page of RFQ attachments; flag inconsistencies as RFI | Estimator |
| B9 | Sub does not commit by pricing-assembly deadline | 4 | 3 | 12 | Solicit ≥ 3 subs per trade; identify back-up before pricing locks. Compressed SAP timeline forces shorter sub-quote windows (5 working days vs LPTA's 10) | PM |
| B10 | Bid exceeds magnitude / sub-SAT cap — non-competitive | 5 | `[USER TO FILL]` | | Bid at magnitude floor + 5–15%; verify against last-3-job actuals; sub-SAT cap = $250K civilian / $7.5M commercial-item per FAR 13.003 / 13.500 | PIC |
| B11 | Bid below magnitude low — "unreasonably low" determination under FAR 13.106-3 | 5 | 2 | 10 | Do not bid below magnitude floor; document reasonableness | PIC |
| **B12** | **Under-investing in technical-capability narrative — "Unacceptable" rating eliminates quote** | **5** | **3** | **15** | **Write 5–15 pp narrative covering project understanding + schedule + phasing + trade approach + QC/safety summary; do NOT treat as LPTA "no narrative" gate** | **PM** |
| **B13** | **Missing prior-experience reference count — submit fewer than RFQ's "minimum 3" / "min 3 max 5"** | **5** | **2** | **10** | **Submit at the RFQ's stated maximum; verify count in Section L on Day 1; pull additional refs from `firm-profile.json` past-project rules if needed** | **PM** |
| **B14** | **Price outside "lowest 3" cutoff — technical + experience never read** | **5** | **3** | **15** | **Stress-test bid against likely competitor pricing on Day 18; if outside lowest-3 envelope, re-tighten GC + contingency + profit before locking** | **PIC** |
| **B15** | **Wrong SF form on quote (using SF-1442 when RFQ asks for SF-18, or vice versa)** | **5** | **2** | **10** | **Verify form on RFQ cover page on Day 1; default to SF-18 for sub-SAT FAR Part 13 RFQs** | **PM** |

## 2. Execution-side risks (post-award; for pricing-strategy contingency justification)

| # | Risk | Impact | Likelihood | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| E1 | Hidden conditions on demo (concealed structural / MEP / hazmat) | 4 | 3 | 12 | Investigative pre-demo walk with A/E + owner; pre-demo RFI; contingency reserve | Super |
| E2 | Long-lead item delayed (OH door, HM frame, lab equipment) | 3 | 3 | 9 | Order at NTP+1; expedite-freight contingency; identify alternate suppliers | PM |
| E3 | Davis-Bacon certified-payroll administrative cost overrun | 2 | 4 | 8 | Build PM hours into GC; payroll-clerk dedicated for project | PM |
| E4 | Buy American non-compliance discovered post-PO | 4 | 2 | 8 | Domestic-content rep on every PO; verify before delivery | PM |
| E5 | Site-access lag (base background checks, escort hours) | 3 | 3 | 9 | Submit worker BCG packets at NTP; crew sizing with extras | Super |
| E6 | Owner-occupant disruption complaint | 2 | 4 | 8 | After-hours / weekend windows; daily owner walk; communication plan | PM |
| E7 | AHJ inspection scheduling lag | 3 | 3 | 9 | Schedule inspections 5+ working days in advance; back-up dates in CPM | Super |
| E8 | Adverse weather (outdoor scope) | 3 | 3 | 9 | Buffer days in CPM; covered staging; weather-day clause | Super |
| E9 | Sub default mid-project | 5 | 1 | 5 | Pre-vetted back-up sub identified per critical trade; sub agreement w/ replacement clause | PM |
| E10 | Change in scope by owner via change order | 3 | 4 | 12 | Unit prices set high on RFP; CO process documented; recover via change-order pricing | PM |
| E11 | LD assessment at substantial completion miss | 4 | 2 | 8 | Critical-path discipline; schedule recovery plan if slippage > 5 working days | PM |
| E12 | Closeout deliverable gap delays final pay | 3 | 4 | 12 | Closeout package compiled from NTP forward; not at SC | PM |

## 3. Risk-driven pricing decisions

The contingency in `08-pricing-strategy.md` is justified by:

- Sum of E-risks scored ≥ 10: `[USER TO FILL — total contingency $ implied]`
- Concentration of risk in long-lead procurement: → adds `[USER TO FILL]`% to procurement-line GC
- Concentration of risk in owner-side disruption: → adds `[USER TO FILL]`% to GC supervision

## 4. Go / No-go drivers

The following risk thresholds drive a **No-Go**:

- B1 active 🔴: SAM lapsed = No-Go (cannot bid federal)
- B2 unresolvable: surety will not commit (post-award P&P or alt-payment per FAR 52.228-13) = No-Go
- B7 unresolvable: < 3 confirmed prior-experience references (when RFQ asks for 3–5) = No-Go on its face; quote fails the count check
- B10 unresolvable: even at magnitude floor BPC's true cost runs above sub-SAT cap = No-Go (bidding at a loss)
- B11 risk: BPC must underbid magnitude low to be competitive = No-Go
- B12 unresolvable: estimator capacity does not exist to write 5–15 pp technical narrative inside the compressed SAP timeline = No-Go (a quote without substantive technical narrative loses on SAP)
- B14 risk: BPC's true cost puts the bid materially above estimated lowest-3 envelope = Conditional No-Go; re-scope or pass

Recommended posture: `[USER TO FILL after pre-bid analysis — Go / No-Go / Conditional Go pending risk closure]`
