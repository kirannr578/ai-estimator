# CHS Cafeteria Serving Line Renovation — Pricing Strategy

> **Use:** Internal pricing rationale + markup recipe + competitive-position read. **Not** in the proposal.
> TX state CSP — weighted scoring with price typically 40–60%. Tight markup matters but not the only axis.

## 1. Magnitude anchor

| Metric | Value |
|---|---|
| Estimated magnitude (often not published in NOP) | $`265,000` – $`325,000` `[USER TO FILL — estimate from scope]` |
| BPC target bid | $`{{TARGET_BID_LOW}}` – $`{{TARGET_BID_HIGH}}` |
| Floor for "non-responsibility" risk | ~25% below median competitor bid |
| Ceiling for competitive position | typically near magnitude high |

## 2. Direct-cost rollup

| Bucket | Source | Cost |
|---|---|---|
| Sub bids (≥ 3 per trade) | `04-scope-of-work.md` | $`{{SUB_COST}}` |
| Self-perform labor (TX prevailing-wage rated) | Crew hours × TX wage rates | $`{{SELF_LABOR}}` |
| Self-perform materials | per scope | $`{{SELF_MAT}}` |
| Equipment rental | per scope | $`{{EQUIP}}` |
| Per-diem + travel (if remote site) | crew × days × per diem | $`{{TRAVEL}}` |
| **Direct cost subtotal** | | **$`{{DIRECT_TOTAL}}`** |

## 3. Markup recipe (TX state institutional renovation)

| Line | % of direct | $ |
|---|---|---|
| Direct cost (from above) | 100% | $`{{DIRECT_TOTAL}}` |
| General conditions (super + PM + temp protection + dumpster + temp utilities) | `{{GC_PCT}}%` (10–14% for institutional) | $`{{GC_$}}` |
| Bonds (bid + P&P @ ~`{{BOND_RATE}}%`) | 1.5–2.5% | $`{{BOND_$}}` |
| Insurance (GL + WC + Auto + Umbrella + Builder's Risk allocated) | 3–5% (institutional Umbrella requirement higher) | $`{{INS_$}}` |
| TX prevailing-wage uplift if firm < prevailing | 0–4% | $`{{TX_WAGE_$}}` |
| **Subtotal A — burdened direct** | | **$`{{SUBTOTAL_A}}`** |
| Contingency | 5–7% (institutional baseline; 10% if drawings thin) | $`{{CONT_$}}` |
| **Subtotal B — risk-adjusted** | | **$`{{SUBTOTAL_B}}`** |
| Overhead | 8–12% | $`{{OH_$}}` |
| Profit | 5–7% | $`{{PROFIT_$}}` |
| **Total lump-sum bid** | | **$`{{TOTAL_BID}}`** |
| Direct-to-bid multiplier | | `{{MULTIPLIER}}` |

## 4. Unit prices (full retail)

TX state CSPs often request unit prices on common owner-directed change items. Bid at full retail (sub cost + full GC markup) — these become the change-order ceiling:

| Unit price item | Unit | BPC price |
|---|---|---|
| Additional `{{ITEM}}` | `{{UNIT}}` | $`{{PRICE}}` |
| Additional `{{ITEM}}` | `{{UNIT}}` | $`{{PRICE}}` |

## 5. Alternates (only as CSP requests)

| Alternate # | Description | Add / Deduct | $ |
|---|---|---|---|
| ALT-001 | `{{DESCRIPTION}}` | ADD | $`{{PRICE}}` |
| ALT-002 | `{{DESCRIPTION}}` | DEDUCT | $`{{PRICE}}` |

**Do not add unsolicited alternates** — TX state CSPs often disqualify for non-responsiveness if proposer adds alternates not in the CSP.

## 6. Allowances (owner-controlled)

If the CSP includes an owner-controlled allowance, carry line-by-line per CSP instructions — do NOT roll into lump-sum, do NOT mark up:

| Allowance | $ | Notes |
|---|---|---|
| `{{ALLOWANCE_DESCRIPTION}}` | $`{{ALLOWANCE_AMOUNT}}` | per CSP §00 21 00 typ |

## 7. Competitive read

| Question | Answer |
|---|---|
| Target bid vs estimated magnitude | `{{COMPARISON}}` |
| Target bid vs estimated competitor pricing | `[USER TO FILL]` |
| Win probability at target (across all scored factors) | `[USER TO FILL]` |
| Acceptable walk-away (lowest bid we'd execute) | $`{{WALK_AWAY}}` |
| Acceptable upper bound (highest bid that's still likely competitive) | $`{{UPPER_BOUND}}` |

## 8. Pricing discipline reminders

- **Don't bid > 25% below median.** TX state agencies often flag "non-responsibility" risk on extreme low bids.
- **Don't over-shave.** TX state evaluators weight past-performance + team + HSP. Pricing alone doesn't win.
- **Set unit prices high** — change-order ceiling.
- **No unsolicited alternates.**
- **Carry allowances line-by-line.** Don't roll into lump-sum.
- **Bond + insurance loaded as %.** Verify with surety + agent before locking.
- **TX prevailing-wage uplift is real.** Verify firm + sub labor rates against `Davis-Bacon Prevailing Wage Rates for Johnson County (SAM.gov; attached to RFCSP)` for `Johnson`.

## 9. Schedule of Prices final review

Before locking the price:

- [ ] Cross-check lump-sum against `04-scope-of-work.md` rollup
- [ ] Cross-check direct-cost subtotal against sub bids on file
- [ ] Verify unit prices set at full retail
- [ ] Verify alternates only as CSP requests
- [ ] Verify allowances carried line-by-line
- [ ] Verify HSP commitment $ matches `05-hsp-plan.md`
- [ ] Verify total against magnitude band
