# {{PROJECT_NAME}} — Pricing Strategy (SAP Best-Value)

> **Use:** Internal pricing rationale + markup recipe + competitive-position read. **Not** in the quote.
> Federal SAP best-value — comparative trade-off across price + technical capability + prior experience. Often evaluated **in groups of 3 lowest priced quotes**. Pricing posture is **tightly competitive on price + strong on technical narrative**, not "premium price + best narrative."

## 1. Magnitude anchor

| Metric | Value |
|---|---|
| Government estimate magnitude | `{{MAGNITUDE_BAND}}` — **often unstated on SAP**; if absent, anchor against sub-SAT cap ($250K civilian per FAR 13.003 / $7.5M commercial-item per FAR 13.500) and last-3-job actuals |
| Sub-SAT cap (regulatory ceiling for this acquisition method) | $`{{SAP_CAP_USD}}` (typ $250K civilian; $7.5M commercial-item) |
| BPC target bid | $`{{TARGET_BID_LOW}}` – $`{{TARGET_BID_HIGH}}` (magnitude floor + 5–15% if magnitude stated; otherwise size against scope) |
| Estimated lowest-3 competitive envelope | $`{{LOWEST_3_LOW}}` – $`{{LOWEST_3_HIGH}}` — **must clear this cutoff to get technical + experience read** |
| Floor for "unreasonably low" determination (FAR 13.106-3) | ~$`{{FLOOR}}` (do not bid below) |

## 2. Direct-cost rollup

| Bucket | Source | Cost |
|---|---|---|
| Sub bids (≥ 3 per trade) | `06-scope-outline.md` | $`{{SUB_COST}}` |
| Self-perform labor (DBA-rated) | Crew hours × DBA WD rates | $`{{SELF_LABOR}}` |
| Self-perform materials | `06-scope-outline.md` | $`{{SELF_MAT}}` |
| Equipment rental | per scope | $`{{EQUIP}}` |
| Per-diem + travel (if remote site — SAP RFQs often for remote facilities) | crew × days × GSA rate | $`{{TRAVEL}}` |
| **Direct cost subtotal** | | **$`{{DIRECT_TOTAL}}`** |

## 3. Markup recipe (SAP-tuned)

| Line | % of direct | $ |
|---|---|---|
| Direct cost (from above) | 100% | $`{{DIRECT_TOTAL}}` |
| General conditions (super + PM + temp protection + dumpster + temp utilities + AHJ coordination + **estimator hours for technical-narrative drafting**) | `{{GC_PCT}}%` (8–14%) | $`{{GC_$}}` |
| Bonds (post-award P&P or FAR 52.228-13 alt-payment @ ~`{{BOND_RATE}}%`) | **1.0–2.0%** (lower than LPTA — no bid bond typical) | $`{{BOND_$}}` |
| Insurance (GL + WC + Auto + Umbrella + Builder's Risk allocated) | 2–4% | $`{{INS_$}}` |
| DBA labor-burden uplift if firm labor < prevailing | 0–4% | $`{{DBA_$}}` |
| **Subtotal A — burdened direct** | | **$`{{SUBTOTAL_A}}`** |
| Contingency | **4–6%** (SAP — between LPTA's 3–5% and FAR 15's 5–8%; bump higher if site visit missed) | $`{{CONT_$}}` |
| **Subtotal B — risk-adjusted** | | **$`{{SUBTOTAL_B}}`** |
| Overhead | **8–11%** (slightly above LPTA floor — technical-narrative drafting is real cost) | $`{{OH_$}}` |
| Profit | **5–8%** (above LPTA's 3–6% — best-value trade-off gives SSA a path to award slightly higher when narrative + experience are stronger) | $`{{PROFIT_$}}` |
| **Total bid** | | **$`{{TOTAL_BID}}`** |
| Direct-to-bid multiplier | | `{{MULTIPLIER}}` (target 1.30–1.45 on SAP, vs 1.25–1.40 on LPTA, vs 1.35–1.55 on FAR 15) |

## 4. "Groups of 3" pricing posture (the SAP-specific discipline)

When Section M (or the SAP-equivalent "Basis for Award") states the CO will evaluate technical + experience **only on the lowest 3 (or 5) priced quotes**, pricing strategy pivots on the cutoff:

| Question | Answer |
|---|---|
| Estimated number of quoters on this RFQ | `[USER TO FILL — based on SAM.gov interested-vendors list, prior similar awards on this NAICS / agency / region]` |
| Estimated lowest-3 envelope | $`{{LOWEST_3_LOW}}` – $`{{LOWEST_3_HIGH}}` — sourced from `[USER TO FILL — prior awards on similar scope + magnitude]` |
| BPC target bid position | ☐ #1 ☐ #2 ☐ #3 ☐ outside lowest-3 (= eliminated regardless of narrative) |
| Buffer over estimated #3 cutoff | $`{{BUFFER_$}}` — keep positive; if negative, re-tighten |
| Technical-capability buffer (% headroom above pure-LPTA pricing posture for narrative-drafting + experience-block effort) | `{{TECH_BUFFER_PCT}}%` (target 3–8% above pure LPTA floor) |

**Decision rule:** if the target bid is **outside the estimated lowest-3 envelope**, re-tighten before locking. A 4th-place price is eliminated on price regardless of how good the technical narrative is.

## 5. Competitive read

| Question | Answer |
|---|---|
| Target bid vs estimated lowest-3 cutoff | `{{COMPARISON}}` |
| Target bid vs estimated competitor pricing | `[USER TO FILL — read of likely competitors + their typical SAP bid posture]` |
| SAP best-value win probability at target (if inside lowest-3) | `[USER TO FILL — drives off technical narrative + experience strength relative to competitors at similar price]` |
| Acceptable walk-away (lowest bid we'd execute) | $`{{WALK_AWAY}}` |
| Acceptable upper bound (highest bid still inside lowest-3 envelope) | $`{{UPPER_BOUND}}` |

## 6. Pricing discipline reminders (SAP-specific)

- **Don't bid below the floor.** FAR 13.106-3 "unreasonably low" determinations are rarer than under FAR 15.404-1(d) but still possible.
- **Don't bid above the lowest-3 envelope.** Above the cutoff, technical narrative is never read — the bid is eliminated on price alone.
- **Don't skip the technical narrative.** A bid that clears the lowest-3 cutoff but submits no substantive narrative loses to a competitor at the same price who wrote 8 pp of competent narrative.
- **Don't pad profit above ~8%.** Comparative trade-off gives room above LPTA's 6% ceiling but not unlimited room — a quote materially above the magnitude band invites a "high price did not reflect best value" award narrative for the competitor.
- **Don't unbalanced-bid.** FAR 13.106-1 reasonableness review flags front-loading on SAP the same way FAR 15.404-1(g) does on FAR Part 15.
- **Every CLIN priced.** A blank CLIN is non-responsive even on SAP.
- **No bid bond typical on SAP.** Verify Section I before paying for an SF-24 — most SAP RFQs use FAR 52.228-13 Alternative Payment Protections instead.
- **Per-diem + travel adds non-trivially on remote SAP sites.** GSA per-diem zones at <https://www.gsa.gov/travel/plan-book/per-diem-rates>.
- **DBA applies regardless of SAP status** if construction labor is on site. Transcribe WD + re-price if amended.
- **Compressed cycle = compressed sub-quote windows.** Subs have 5 working days, not 10 — solicit on Day 1, not Day 7.

## 7. Comparison against prior BPC bids (calibration)

| Prior bid | Procurement type | Direct-to-bid multiplier | Win / Loss / Pending |
|---|---|---|---|
| `[USER TO FILL — prior federal SAP bid 1]` | SAP best-value | `[USER TO FILL]` | `[USER TO FILL]` |
| `[USER TO FILL — prior federal LPTA bid for comparison]` | LPTA | `[USER TO FILL]` | `[USER TO FILL]` |

Target multiplier this bid: `{{MULTIPLIER}}` — `[USER TO FILL — justify against prior calibration; expect 0.03–0.08 higher than LPTA equivalent]`

## 8. Schedule of Prices final review

Before locking the price:

- [ ] Cross-check each CLIN price against `06-scope-outline.md`
- [ ] Cross-check direct-cost subtotal against sub bids on file
- [ ] Cross-check self-perform > 15% of direct cost
- [ ] Verify total against magnitude band (or sub-SAT cap if magnitude unstated)
- [ ] **Verify total falls inside estimated lowest-3 envelope** (the SAP-specific check)
- [ ] Verify no CLIN left blank
- [ ] Verify priced options completed exactly per Section B
- [ ] Verify total reflects technical-capability buffer (3–8% above pure LPTA floor) — but no more
