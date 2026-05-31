# Risk register — USACE Fort Hood Staging W9126G26RA015

> Initial register at scaffold time (2026-05-30). **Risks 1-5 are gating risks** that drive the go/no-go decision in [`go-no-go-decision.md`](./go-no-go-decision.md). Do not progress to detailed estimating until gating risks are resolved.

## Gating risks (drive go/no-go)

| # | Risk | Likelihood | Impact | Score | Mitigation / decision-gate behavior |
|--:|---|:--:|:--:|:--:|---|
| 1 | **Past-performance relevance gap** — federal Part-15 tradeoff source-selection weights past performance heavily; BPC has no construction prior at $5M-$10M federal scale | H | H | 🔴 | Inventory BPC priors; if no ≥$3M federal prior in last 5 years, default to NO-GO unless mentor-protégé / JV is in place |
| 2 | **Bonding capacity gap** — bid bond up to $1M (FAR 52.228-1 cap) + 100% P&P bonds at $5M-$10M = $5M-$10M each post-award | H | H | 🔴 | Surety broker confirmation required as Gate 1 of go/no-go |
| 3 | **Internal capacity gap** — 12-18 month POP, design-bid-build with operations bldg + full MEP + civil + options requires sustained PM + super; BPC's bench may be over-committed | M | H | 🔴 | Rocky's explicit capacity review as Gate 3 of go/no-go |
| 4 | **Estimating opportunity cost** — 200-400 hours of estimator effort for a low-probability bid trades against 5-10 smaller, higher-probability bids | M | M | 🟠 | Hard limit on hours invested pre-decision (≤ 20 hr); decision must come before deeper investment |
| 5 | **Specialty sub network not pre-engaged** (FRCS cybersecurity Section 25 05 11.01 / .02; facility fall protection Section 11 18 29; AT/OPSEC chain-link Section 32 31 13; BACnet DDC Section 23 09 23.02) | M | M | 🟠 | Outreach during bid window competes against larger GCs with existing relationships; cap effort if go/no-go favors no-go |

## Post-go risks (only relevant if GO)

| # | Risk | Likelihood | Impact | Score | Mitigation |
|--:|---|:--:|:--:|:--:|---|
| 6 | **AT/OPSEC personnel screening** (Section 01 01 10.00 44) — NACI/NACLC for site personnel takes 4-8 weeks | H | M | 🟠 | Start screening immediately upon GO decision |
| 7 | **Drawings package separate from spec book** — not in OneDrive drop; pull from SAM.gov | H | H | 🔴 | Cannot estimate without drawings; pull within 24 hr of GO decision |
| 8 | **Davis-Bacon WD for Bell + Coryell counties** — likely Heavy Construction or Building Construction WD | M | M | 🟡 | Pull from SAM.gov; integrate into labor build-up; verify trade classes |
| 9 | **FRCS cybersecurity (Section 25 05 11.01)** — moderate-impact controls; specialty sub market is thin and pricey | M | H | 🟠 | Outreach to FRCS specialists (e.g., Honeywell, Schneider, Johnson Controls cleared SBA-eligible partners) |
| 10 | **Roller-compacted concrete paving (Section 32 13 13.17)** for high-load staging aprons — specialty sub network limited in TX | M | M | 🟡 | Outreach to TXDOT-prequalified RCC paving subs |
| 11 | **Section 889 compliance** — confirm BPC's subs don't use covered telecom (Huawei, ZTE, Hytera, Hikvision, Dahua) | M | M | 🟡 | Sub questionnaire at outreach; reps & certs flow-down |
| 12 | **DPAS rating** (if any) — requires acceptance of rated-order priority obligations | L | M | 🟡 | Read Section L provision near FAR 52.214-34; confirm acceptance in offer |
| 13 | **SAM.gov registration lapse** | L | H | 🟡 | Confirm SAM active through anticipated NTP + 12 mo |
| 14 | **Volume IV pricing format** — federal RFPs have strict pricing-format requirements (sealed envelope or separate file) | L | M | 🟡 | Read Section L Volume IV requirements before final submission |
| 15 | **Amendments** issued by USACE-FWD between issue date and offer due | M | M | 🟡 | Monitor SAM.gov daily; acknowledge each SF 30 in Block 19 of SF 1442 |
| 16 | **Bid security forfeiture** if signed contract not returned within stated timeframe post-award | L | H | 🟡 | Standard; treat as compliance item |
| 17 | **Soliciting subs against large GCs** at $5M-$10M magnitude — BPC's relative market position is junior | M | M | 🟡 | Lead with BPC's HUB / small-business set-aside fit; price aggressively where BPC self-performs |

## Risks **not** present (per current understanding)

- ❌ HSP / TX HUB Subcontracting Plan exposure — federal solicitation, not TX state
- ❌ Local-preference tie-breaker — federal solicitation, no state/local overlay
- ❌ Restricted-class data from the solicitation itself — solicitation is Private at most (publicly posted on SAM.gov)
- ❌ ESBD-specific compliance — federal solicitation, not posted on ESBD

## Open questions for the go/no-go decision

See [`go-no-go-decision.md`](./go-no-go-decision.md) for the structured decision template. Key questions:

1. What is BPC's surety's max single-project P&P limit today? (Gate 1)
2. Does BPC have a ≥$3M federal-construction prior in the last 5 years? (Gate 2)
3. Can BPC commit 1 PM + 1 super to a 12-18 month assignment starting Q4 2026? (Gate 3)
4. Is a 200-400-hour estimating investment justified given the current pipeline? (Gate 4)
