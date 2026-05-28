# PAIS — Backcountry Cabin Roof Repairs — Pricing Strategy

> **Use:** Internal pricing rationale + markup recipe + competitive-position read. **Not** in the proposal.
> **Best-value SAP** (NOT LPTA). Markup discipline matters but Section M's stated weighting (price + technical capability + prior experience, evaluated in groups of 3 lowest-priced) means **lowest-price wins enter the evaluation pool first** — bid lean enough to be in the lowest-3 pool.

## 1. Magnitude anchor

| Metric | Value |
|---|---|
| Government estimate magnitude (IGE) | **Not published** in RFQ (per Section M "comparison to an independent Government estimate" — IGE exists per RFQ "Award is subject to and based on the availability of funds. This project is currently funded based upon an independent cost estimate.") |
| FAR Part 13 SAP cap | $250,000 (per FAR 13.003 simplified acquisition threshold for construction) |
| BPC magnitude estimate (rough order) | **$80–180K** based on scope: 3 doors + small-area roof repair + 10 hurricane shutters + small ramp ext + breakaway sand control; logistics premium for backcountry access |
| BPC target bid | `[USER TO FILL — recommend $100–160K depending on sub quotes; CLIN 003 shutters dominate the cost stack at est. $40–80K]` |
| Floor for "unreasonably low" determination (FAR 13.106-3 / FAR 15.404-1(d)) | ~`[USER TO FILL — recommend ~$80K; cost of self-perform labor + per-diem + 4WD truck + materials cannot honestly fall below this for a 60-cal-day backcountry job]` |
| Ceiling for competitive position | ~`[USER TO FILL — recommend ≤ $200K to remain in the lowest-3 evaluation pool; over $250K converts to non-SAP threshold]` |

## 2. Direct-cost rollup

| Bucket | Source | Cost |
|---|---|---|
| TDI CAT5 Bahama shutter sub (CLIN 003) — fabrication + install | Sub bid (target ≥ 3 quotes) | $`{{SUB_CLIN003}}` (est. $40–80K) |
| Roofing material (CLIN 002) — marine-grade shingles, sealant, SS fasteners | Material vendor | $`{{MAT_CLIN002}}` (est. $1–3K material; install self-perform) |
| Door hardware (CLIN 001) — SS hinges, locks, deadbolts, jamb reinforcement kits | Material vendor | $`{{MAT_CLIN001}}` (est. $1–3K material × 3 = $3–9K total; install self-perform) |
| PT lumber + hardware (Opt 001 ramp + Opt 002 sand control) | Material vendor | $`{{MAT_OPT}}` (est. $5–15K material; install self-perform) |
| Self-perform labor (DBA-rated, Kenedy/Nueces County) | Crew hours × DBA WD rates per Att 3 | $`{{SELF_LABOR}}` (est. 25–35 active work-days × 3-person crew × DBA carpenter / roofer / laborer rates from Att 3) |
| Equipment rental | 4WD pickup + small generator + power tools | $`{{EQUIP}}` (est. $2–5K — pickup ~$1.5K/wk × ~2 wk active mob; generator + tools $1–2K) |
| Per-diem + travel | Crew × cal-days × GSA Nueces County per-diem | $`{{TRAVEL}}` (est. 25–35 work days × 2-3 person crew × ~$200/day per-diem + lodging ~$110/night) |
| **Direct cost subtotal** | | **$`{{DIRECT_TOTAL}}`** |

> **Per-diem reference:** GSA per-diem rates at <https://www.gsa.gov/travel/plan-book/per-diem-rates>. Nueces County (Corpus Christi) typically standard CONUS lodging + M&IE rates.

## 3. Markup recipe

| Line | % of direct | $ |
|---|---|---|
| Direct cost (from above) | 100% | $`{{DIRECT_TOTAL}}` |
| General conditions (super + PM + temp protection + dumpster + temp utilities + AHJ coord + 4WD vehicle + per-diem + lodging + materials haul-out HQ-to-cabin) | **12–16%** (above the typical 8–14% — backcountry premium) | $`{{GC_$}}` |
| Bonds (post-award only — Payment Bond OR ILC; ILC may be cheaper if BPC has bank LOC capacity; bond rate ~0.8–1.5% if Payment Bond only) | **0.8–1.5%** (lower than 1.5–2.5% typical because no P&P at submission, just Payment Bond at award) | $`{{BOND_$}}` |
| Insurance (GL @ DOI 1452.228-70 limits + WC + Auto + Umbrella + Builder's Risk allocated) | **2–4%** | $`{{INS_$}}` |
| DBA labor-burden uplift (firm labor vs. WD prevailing for Kenedy County) | **0–4%** (depends on Att 3 transcription; coastal TX construction WDs typically run higher than firm avg) | $`{{DBA_$}}` |
| **Subtotal A — burdened direct** | | **$`{{SUBTOTAL_A}}`** |
| Contingency | **6–8%** (above 3–5% LPTA floor; backcountry + coastal weather + wildlife buffer + long-lead shutter risk per `07-risk-register.md`) | $`{{CONT_$}}` |
| **Subtotal B — risk-adjusted** | | **$`{{SUBTOTAL_B}}`** |
| Overhead | **8–10%** | $`{{OH_$}}` |
| Profit | **5–7%** (best-value SAP allows higher than LPTA-thin 3–6%) | $`{{PROFIT_$}}` |
| **Total bid** | | **$`{{TOTAL_BID}}`** |
| Direct-to-bid multiplier | | `{{MULTIPLIER}}` (est. 1.30–1.45 for this risk profile) |

## 4. Competitive read

| Question | Answer |
|---|---|
| Target bid vs IGE | IGE not published; bid against estimated true cost + reasonable markup |
| Target bid vs estimated competitor pricing | Local Corpus Christi GCs (e.g. NPS Region SAP-pool small-business contractors) typically bid this size at ~1.25–1.40× direct cost. BPC's 4WD/per-diem/lodging premium adds ~10% vs. local — must be lean elsewhere to compete |
| Best-value SAP win probability at target | `[USER TO FILL — depends on lowest-3 evaluation pool; if BPC's price lands in lowest-3 + technical narrative is solid + prior experience is verifiable, win probability 30–40% in a typical 5–10 offeror pool]` |
| Acceptable walk-away (lowest bid we'd execute) | $`[USER TO FILL — ~$80K; below this, cannot cover backcountry logistics]` |
| Acceptable upper bound (highest bid still competitive in evaluation pool) | $`[USER TO FILL — ~$180K; above this, unlikely to land in lowest-3 evaluation pool]` |

## 5. Pricing discipline reminders

- **Backcountry premium is real.** 4WD truck rental, lodging in CCI for the active work-week, per-diem for crew, materials haul-out — this stack is ~$15–25K of GC over a 25-35 work-day window. Don't shave it; build it in.
- **Don't bid below true cost.** FAR 13.106-3 SAP doesn't require a formal "unreasonably low" determination, but the CO can still reject a bid as not in the Government's interest. Verify total covers DBA labor + per-diem + 4WD truck + lodging.
- **Best-value SAP vs LPTA on profit.** LPTA "thin" profit (3–6%) doesn't apply directly here — best-value SAP allows up to 7% profit before the cost gets unreasonable. Target ~5–7%.
- **Don't unbalanced-bid options.** Section 52.217-5 says Govt evaluates options added to base. If BPC unbalances — e.g. base-CLIN-low / option-high to hedge against option non-exercise — the CO can reject for unbalanced pricing per Section M "Offerors are cautioned to distribute costs appropriately."
- **Every CLIN priced.** Including both options. A blank flips to non-responsive even if grand total is correct.
- **DBA labor-burden differential is real.** If firm labor < prevailing for trade rates in Kenedy / Nueces County, the WD-rate uplift goes to the worker — not to overhead. Verify by transcribing Att 3 rates and comparing to BPC's typical carpenter / roofer / laborer rates.
- **Shutter long-lead premium.** CLIN 003 (10 units engineer-stamped) is the schedule-critical-path. Sub may charge a 5–10% expedite premium for fabrication-and-delivery within the 60-day NTP window. Build in.
- **No bid bond cost.** Unlike full-Part-15 federal-LPTA, no SF-24 bid bond at submission means BPC saves the bid-bond fee (typically 0.5–1% of bid). Flag this advantage in the cover letter / cost-narrative if CO requests breakdown.

## 6. Comparison against prior BPC bids (calibration)

| Prior bid | Direct-to-bid multiplier | Win / Loss / Pending |
|---|---|---|
| usfws-san-marcos-140FC126R0017 (federal SBA RFQ Hatchery rehab) | `[USER TO FILL — pull from that workspace's pricing strategy]` | `[USER TO FILL]` |
| b1710-office-refurb-FA667526Q0002 (USACE office refurb) | `[USER TO FILL — pull from that workspace]` | `[USER TO FILL]` |
| Lavon RV Park (commercial new build, not federal — provides direct-cost calibration only) | ~1.10× (direct-pass-through with thin GC) | Pending — in execution |

Target multiplier this bid: **1.30–1.45** — `[USER TO FILL — justify against prior calibration; the backcountry / coastal / hurricane-shutter risk pushes higher than typical commercial, but lower than the 1.50+ that USACE secure-facility bids would carry]`

## 7. Schedule of Prices final review

Before locking the price:

- [ ] Cross-check each CLIN price against `06-scope-outline.md`
- [ ] Cross-check direct-cost subtotal against sub bids on file (≥ 3 TDI shutter quotes, lumber + hardware quote, roofing material quote)
- [ ] Cross-check self-perform > 15% of direct cost — target ≥ 30%
- [ ] Verify total stays under FAR Part 13 SAP cap ($250K)
- [ ] Verify no CLIN left blank (including BOTH options)
- [ ] Verify no exception language anywhere in the priced proposal (rejected per Section L General Information)
- [ ] Verify alternates only as RFP requests them (none requested here; "Alternate pricing and alternate quotes will not be accepted" — Section L Part C.4)
- [ ] Verify pricing rounded to nearest dollar (Section L Part C.4)
- [ ] Verify total cited at bottom of Section B + replicated in transmittal (Section L Part C.4 "Total price shall be cited and if listed on the Solicitation Form, it must be the same amount listed")
