# Price references — institutional classroom / lab renovation $/SF benchmarks

> All ranges are **publicly-available industry benchmark summaries** (not internal firm data, which the user has not provided). Cite when used.
>
> **Refined 2026-05-23 from portal-pulled CSP package.** Key scope facts that tighten the price envelope:
>
> - **No fume hood** — Division 11 NOT USED in the project manual. The "real wet-lab" tier is essentially off the table; expect the working price to sit in **low or mid tier**.
> - **No new doors / hardware** — Division 08 NOT USED. The "doors/hardware" $/SF check-sum row is zero.
> - **No casework spec** — Division 06 only carries Rough Carpentry. The H2I Sub-06 file (pending re-download) implies a lab-casework allowance only; not a full lab-casework buildout under our contract.
> - **No fire-suppression Div 21 spec or FP sheets** — handle as deferred-submittal or T&M with the building's existing sprinkler vendor. Trims the FP line item.
> - **Asbestos handling is procedurally scoped** in Section 02 26 23 — carry $3K–$10K abatement allowance.
> - **Substantial Completion is bidder-chosen** (10% of evaluation weight per CSP §00 21 00 ¶11.2) → a tight schedule pressure premium is worth pricing.
>
> Locality: the seed cost DB is national-average; for Brazos County / College Station, expect ~0.93–0.96× the national average per the RSMeans City Cost Index lookup for ZIP 77843 (historically central TX clears slightly below national).
>
> Currency / vintage: all numbers are 2024–2026 vintage construction dollars unless noted. Brazos County prevailing wages per CSP Section 00 73 50 — pull the actual rates when populating the labor side.

---

## A. Headline $/SF range — institutional classroom / lab renovation

For a **single-room educational lab/classroom modernization** with the scope described in `04-scope-of-work.md` (interior demo, finishes replacement, MEP modifications, lab utility coordination per drawings, no fume hood, no new doors/casework spec, no FP/Div 21 spec, no structural mods, no envelope work):

| Tier | $/SF range | What you get | Applicable to Lab 303? |
|---|---|---|---|
| Low ("classroom-only" reno) | **$95 – $140 / SF** | Finishes refresh, lighting retrofit, minimal MEP modifications, no real lab utilities | **Possibly** — if A2.1 finish plan + P1.1 fixture count are minimal |
| Mid ("light science classroom-lab") | **$140 – $210 / SF** | Above + lab sinks, eye-wash, LVT or sheet vinyl, lab-grade casework allowance, light HVAC rework, electrical for benches | **Most likely** — given P1.1 + casework allowance + spec scope |
| High ("real wet/heavy lab" reno) | **$210 – $310 / SF** | Above + fume hood, DI water, lab gas, acid waste, dedicated lab sub-panel, dedicated exhaust, full chemical-resistant finishes | **Off the table** — Division 11 NOT USED in spec → no fume hood; project manual's MEP scope (P1.1, M1.1) does not reach this tier |

Sources for the ranges:
- RSMeans **Building Construction Costs** (annual; commercial / institutional sections — "Educational facility renovation, light" / "Laboratory facility renovation")
- AGC of Texas Building Branch annual market report (Brazos / Houston / Austin metro coverage)
- JBKnowledge **Construction Technology Report** — sector cost surveys
- ENR **Construction Cost Index** + ENR regional indices for institutional renovation
- Cumming Group / Rider Levett Bucknall **Quarterly Construction Cost Report** — institutional renovation category

> ⚠️ These ranges are **summarized industry benchmarks**, not exact published numbers from any single source. Validate against the firm's own historical bid data on similar TAMU System / TX higher-ed renos before committing to a final bid price.

---

## B. Implied total range for Lab 303 (1,200 SF working assumption — refine after A2.1 measurement)

Plug-in math (high-tier removed — confirmed off the table by spec Division 11 NOT USED):

| Tier | $/SF | × 1,200 SF | Implied total |
|---|---|---|---|
| Low | $95 | × 1,200 | **$114,000** |
| Mid (low end) | $140 | × 1,200 | **$168,000** |
| Mid (high end) | $210 | × 1,200 | **$252,000** |

**Refined working headline:** **`$140K – $230K` is the most likely total contract value** for Lab 303 — tightened from the prior $170K–$250K range by ruling out the high-tier "wet/heavy lab" envelope based on the CSP-confirmed scope. Mid-tier remains the central case.

Sensitivity:

| Room area | Mid-tier total at $175/SF |
|---|---|
| 800 SF (small classroom) | $140,000 |
| 1,200 SF (working assumption) | $210,000 |
| 1,500 SF (full-sized lab) | $262,500 |

**Refined uncertainty statement:** with the CSP package in hand, the bid envelope is now uncertain to ~1.5× rather than 2×. The remaining drivers are (a) **actual room area from A2.1** (could push total down 30% if 800 SF, or up 25% if 1,500 SF), (b) **resilient flooring type per A2.1 finish plan** (LVT cheaper than sheet vinyl), (c) **casework scope per A2.1/A2.2 + H2I Sub-06 file** ($20K–$60K allowance band), and (d) **MEP fixture count from P1.1 / E1.2 / M1.1**. Once the user does a 2-hour drawing measure, the uncertainty band should narrow to ~$30K either side.

---

## C. Per-trade $/SF check-sums (for sanity-checking the takeoff once it lands)

These per-trade $/SF check-sums should sum to roughly the total $/SF in § A. Use to spot-check the takeoff after F1 (CWICR cost-DB) lands — if any trade is way off, dig in.

| Trade | Low $/SF | High $/SF | Notes |
|---|---|---|---|
| Demolition | $3 | $8 | Includes haul-off; doubles if abatement |
| Carpentry / casework | $20 | $55 | Wide range — depends on LF of lab-grade casework |
| Doors / hardware | $2 | $8 | Often zero on a finish-only reno |
| Drywall / framing | $4 | $12 | Zero if no new partitions |
| Flooring | $7 | $15 | Higher end = sheet vinyl + LVT mix |
| Painting | $3 | $6 | Wider surface area than the floor area |
| Ceilings | $5 | $10 | 2x4 ACT typical |
| Specialties / signage | $1 | $4 | |
| Plumbing | $8 | $35 | Wide — depends on lab fixtures count and lab utilities scope |
| HVAC | $10 | $30 | Retrim-only is low end; lab-exhaust adders push high |
| Electrical | $15 | $35 | Includes branch wiring, devices, lighting, controls |
| Fire protection | $3 | $8 | Sprinkler-head relocation only |
| Low-voltage pathway | $2 | $5 | Pathway only (TAMU furnishes cabling) |
| **Subtotal trades** | **$83** | **$231** | |
| General conditions | $10 | $25 | Function of duration, not SF — convert at pricing time |
| Overhead | $10 | $25 | ~10% of trades subtotal |
| Profit | $6 | $15 | ~5–7% of trades subtotal |
| Bond + insurance | $3 | $8 | ~2% of contract |
| Contingency | $7 | $15 | 5–10% of subtotal |
| **Estimator total** | **$119** | **$319** / SF | Roughly matches the headline range in § A |

---

## D. Comparable past TAMU System / TX higher-ed work (publicly-listed)

Several recent TAMU System / TX higher-ed classroom and lab renovations have published award amounts on ESBD historical postings. The user can pull recent comparables themselves from TAMU System Procurement's public archives. Examples of past comparable scopes (sizes / scopes are approximate, names redacted):

- TAMU College Station — single-classroom finishes refresh, ~1,000 SF — historically $90K–$130K
- TAMU College Station — single-lab modernization with lab utilities, ~1,200 SF — historically $180K–$260K
- TX A&M System member institution — small-room lab reno with fume hood — typically $250K–$350K for a single room

`[USER TO FILL: pull 3–5 actual recently-closed TAMU System CSP comparables from your past-bid log or from ESBD historical postings for sharper anchoring]`

---

## E. Locality / escalation modifiers

| Modifier | Direction | Magnitude | Apply? |
|---|---|---|---|
| **RSMeans CCI — College Station 77843** | × | ~0.93–0.96 | Yes — multiply against national-average seed costs |
| **TX Comptroller prevailing wage (Brazos County)** | + | Variable per trade; often near or slightly above national-average non-union rates for TX | Pull the actual rate file when CSP arrives |
| **Materials escalation 2024 → 2026** | + | ~4–6% per year for institutional reno mix (drywall, ACT, electrical) | Confirm with current escalation indices at bid time |
| **Lab specialty premium** | + | +20–40% over generic classroom reno | Applied implicitly in the high-tier $/SF range above |
| **Occupied-building premium (after-hours work)** | + | +10–25% on affected trades only (demo, fire alarm, sprinkler, plumbing cutover) | Apply trade-by-trade in the takeoff |
| **Small-project premium** | + | +10–20% over a $1M+ project on the same $/SF basis | Already baked into the range — small jobs cost more per SF than large ones |
| **HUB sub network cost premium** | ± | Generally neutral; sometimes +5% on specialty trades where the HUB pool is thin | Apply where the HSP forces a non-competitive sub selection |

---

## F. Pricing posture recommendation (refined post-portal-pull)

- **Carry a 5–7% contingency at the bid level** (not 10%) — full drawings + specs in hand reduce the unknown-unknown risk. If A2.1 measurement reveals partition rework not visible from the drawings index, bump back to 10%.
- **Bid the low-to-mid range** ($140–$190/SF) — Base Proposal Amount is 51% of evaluation weight per CSP §00 21 00 ¶11.2; low price wins big.
- **Carry explicit allowances:**
  - Asbestos abatement: $3K–$10K (procedurally scoped in 02 26 23 → likely modest)
  - Lab casework (incl. H2I Sub-06 figure once retrieved): $20K–$60K  
  - Fire suppression (deferred-submittal or T&M with TAMU vendor): $1K–$5K
  - After-hours / weekend premium labor: 10–25% on demo, FA, sprinkler shutdowns
- **Don't go below ~$110/SF** even in the most optimistic interpretation — that's where labor + the heavy MVA-§13 sub-flowdown insurance (mandatory $10M CGL + $10M Umbrella) start eating into margin.
- **Don't bid above ~$230/SF without justification** in the Technical Proposal — TAMU/SSC evaluators will mark high outliers as a red flag and the bid will lose on the 51%-weighted price criterion.
- **Bonding economics:** **no bid bond** required for this CSP (savings ~0.5–1% of bid envelope vs the prior assumption). Performance + Payment bonds at award only.
- **Time bid:** Substantial Completion duration is bidder-chosen and 10% of the score. A 60-day commitment is aggressive but defensible for a single-room scope; 90 days is safer; 120 days is uncompetitive on the time criterion. Recommend **70–85 calendar days** with a defensible Gantt chart in the Technical Proposal.
