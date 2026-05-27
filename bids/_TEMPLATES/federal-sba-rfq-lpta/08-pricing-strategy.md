# {{PROJECT_NAME}} — Pricing Strategy

> **Use:** Internal pricing rationale + markup recipe + competitive-position read. **Not** in the proposal.
> Federal LPTA — lowest price among technically acceptable. Markup discipline matters more than narrative.

## 1. Magnitude anchor

| Metric | Value |
|---|---|
| Government estimate magnitude | $`{{MAGNITUDE_LOW}}` – $`{{MAGNITUDE_HIGH}}` |
| BPC target bid | $`{{TARGET_BID_LOW}}` – $`{{TARGET_BID_HIGH}}` (typ magnitude floor + 5–10%) |
| Floor for "unreasonably low" determination | ~$`{{FLOOR}}` (do not bid below) |
| Ceiling for competitive position | ~$`{{CEILING}}` (likely loses on price beyond this) |

## 2. Direct-cost rollup

| Bucket | Source | Cost |
|---|---|---|
| Sub bids (≥ 3 per trade) | `06-scope-outline.md` | $`{{SUB_COST}}` |
| Self-perform labor (DBA-rated) | Crew hours × DBA WD rates | $`{{SELF_LABOR}}` |
| Self-perform materials | `06-scope-outline.md` | $`{{SELF_MAT}}` |
| Equipment rental | per scope | $`{{EQUIP}}` |
| Per-diem + travel (if remote site) | crew × days × GSA rate | $`{{TRAVEL}}` |
| **Direct cost subtotal** | | **$`{{DIRECT_TOTAL}}`** |

## 3. Markup recipe

| Line | % of direct | $ |
|---|---|---|
| Direct cost (from above) | 100% | $`{{DIRECT_TOTAL}}` |
| General conditions (super + PM + temp protection + dumpster + temp utilities + AHJ coordination) | `{{GC_PCT}}%` (8–14%) | $`{{GC_$}}` |
| Bonds (bid + P&P @ ~`{{BOND_RATE}}%`) | 1.5–2.5% | $`{{BOND_$}}` |
| Insurance (GL + WC + Auto + Umbrella + Builder's Risk allocated) | 2–4% | $`{{INS_$}}` |
| DBA labor-burden uplift if firm labor < prevailing | 0–4% | $`{{DBA_$}}` |
| **Subtotal A — burdened direct** | | **$`{{SUBTOTAL_A}}`** |
| Contingency | 3–5% (LPTA; 7–8% if site visit missed) | $`{{CONT_$}}` |
| **Subtotal B — risk-adjusted** | | **$`{{SUBTOTAL_B}}`** |
| Overhead | 7–10% (floor of band on LPTA) | $`{{OH_$}}` |
| Profit | 3–6% (LPTA-thin) | $`{{PROFIT_$}}` |
| **Total bid** | | **$`{{TOTAL_BID}}`** |
| Direct-to-bid multiplier | | `{{MULTIPLIER}}` |

## 4. Competitive read

| Question | Answer |
|---|---|
| Target bid vs magnitude floor + 10% | `{{COMPARISON}}` |
| Target bid vs estimated competitor pricing | `[USER TO FILL — read of likely competitors and their typical bid posture]` |
| LPTA win probability at target | `[USER TO FILL]` |
| Acceptable walk-away (lowest bid we'd execute) | $`{{WALK_AWAY}}` |
| Acceptable upper bound (highest bid that's still likely competitive) | $`{{UPPER_BOUND}}` |

## 5. Pricing discipline reminders

- **Don't bid below magnitude floor.** FAR 15.404-1(d) "unreasonably low" determination is grounds for rejection.
- **Don't pad above 7% net profit on LPTA.** Every dollar over true cost gives the next offeror a window to underbid.
- **Don't unbalanced-bid** by front-loading early CLINs to improve cash flow. FAR 15.404-1(g)(2) flags this on review.
- **Every CLIN must be priced.** A blank CLIN is non-responsive even if grand total is correct.
- **Per-diem + travel adds non-trivially for remote sites.** GSA per-diem zones at <https://www.gsa.gov/travel/plan-book/per-diem-rates>.
- **DBA labor-burden differential is real.** If firm labor is < prevailing for a trade, the WD-rate uplift goes to the worker — not to overhead.
- **Bond + insurance are not 0%.** Surety will quote 1.0–2.5% combined; verify with surety, do not assume.

## 6. Comparison against prior BPC bids (calibration)

| Prior bid | Direct-to-bid multiplier | Win / Loss / Pending |
|---|---|---|
| `[USER TO FILL — prior federal LPTA bid 1]` | `[USER TO FILL]` | `[USER TO FILL]` |
| `[USER TO FILL — prior federal LPTA bid 2]` | `[USER TO FILL]` | `[USER TO FILL]` |

Target multiplier this bid: `{{MULTIPLIER}}` — `[USER TO FILL — justify against prior calibration]`

## 7. Schedule of Prices final review

Before locking the price:

- [ ] Cross-check each CLIN price against `06-scope-outline.md`
- [ ] Cross-check direct-cost subtotal against sub bids on file
- [ ] Cross-check self-perform > 15% of direct cost
- [ ] Verify total against magnitude band
- [ ] Verify no CLIN left blank
- [ ] Verify no exception language anywhere in the priced proposal (kiss-of-death on LPTA)
- [ ] Verify alternates only as RFP requests them
