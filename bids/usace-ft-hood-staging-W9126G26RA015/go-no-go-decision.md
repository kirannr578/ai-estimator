# Go / No-go decision — USACE Fort Hood Staging W9126G26RA015

> **Status:** **DECISION PENDING** as of 2026-05-30
> **Owner:** Rocky (final call)
> **Decision deadline:** Within 5 business days of locating the offer-due date on SF 1442 Item 13c — to preserve enough air time to either pursue or formally no-go without wasting estimator hours.

## Why this needs an explicit decision

This RFP is the **largest opportunity** in BPC's pipeline by an order of magnitude (target price $5M–$10M vs. recent bids under $1M). It triggers four BPC capacity gates simultaneously:

1. **Bonding capacity** — current surety floor of $1M single-project per `firm/firm-profile.json`. P&P 100/100 at $5M-$10M = $5M-$10M each. Bid bond at FAR 52.228-1 cap = $1M.
2. **Past-performance relevance** — federal Part-15 tradeoff source-selection weights past performance heavily. BPC has shipped construction priors up to ~$500K (Lavon RV Park, Hindu Temple of Southlake). The relevance + similarity gap to a $5M-$10M federal staging facility is material.
3. **Internal capacity** — design-bid-build construction of a staging facility + operations building + MEP + civil + options is a 12-18 month multi-crew project. BPC's current PM bench needs explicit confirmation it can run a project of this size in parallel with existing commitments.
4. **Estimating effort** — 1,835-page spec book with full Divisions 00-33 takeoff is 200-400 hours of estimator work before any narrative volumes. That investment is recoverable only if the bid wins.

A "soft pursue" without an explicit go/no-go invites the worst outcome: burning 100+ hours on a bid that will lose on past-performance scoring alone.

## Decision factors

### Pursue (Go) — arguments for

- **Playbook exemplar value.** First BPC opportunity exemplifying the `federal-rfp-best-value-tradeoff` playbook. Even a losing bid produces system learning: USACE Fort Worth District submission conventions, FAR Part 15 tradeoff scoring mechanics, federal volumes structure at scale.
- **TX state proximity.** Fort Hood is in BPC's TX home territory; site supervision is plausible (Killeen ≈ 2.5 hr from Frisco).
- **Set-aside fit.** 100% Total Small Business at NAICS 236220 with $45M size standard — BPC qualifies easily.
- **CLIN structure with options.** Base + 5 priced options (security fence + 4 tree replacements). BPC could price the base aggressively and let options pad margin.
- **Future positioning.** Even a non-winning bid puts BPC on USACE-FWD's offeror list and accumulates Section M scoring feedback that informs future bids.

### No-go — arguments against

- **Past-performance gap is the dominant risk.** Federal Part-15 tradeoff scoring on past performance is rarely overcome by aggressive pricing. Without a ≥$3M federal-construction prior in the past 5 years, BPC's offer is unlikely to score in the competitive range.
- **Bonding capacity** is not addressable in the bid window. Surety underwriting at $5M-$10M takes weeks of financial-statement review.
- **Internal capacity** can't be conjured. A 12-18 month staging-facility build at scale requires sustained PM + super attention BPC doesn't currently have idle.
- **Estimating opportunity cost.** 200-400 hours of estimator work could be invested in 5-10 smaller bids with much higher win probability (Allen Veterans Memorial, TPWD Old Tunnel, HHS Bldg 500 from this same batch, plus the existing active workspaces).
- **Specialty subs not pre-engaged.** Sections 11 18 29 (Facility Fall Protection), 23 09 23.02 (BACnet DDC HVAC), 25 05 11.01 (Cybersecurity for FRCS), 32 31 13 (Chain Link Fencing for AT) all require specialty subs BPC has not pre-qualified. Sub outreach during a Part-15 bid window competes against larger GCs with existing relationships.

## Recommendation framework

The decision **should NOT default to "pursue because we have the docs"**. Apply the gate test below:

### Gate 1 — Bonding (hard gate)

- [ ] Surety broker confirms BPC can post a $1M bid bond AND $5M-$10M P&P bonds within the bid window. If **NO**, **NO-GO**.

### Gate 2 — Past performance (hard gate)

- [ ] BPC has at least 2 (preferably 3) federal-construction priors at ≥$3M within the last 5 years OR a credible mentor-protégé / JV vehicle to bridge the gap. If **NO** to both, **NO-GO**.

### Gate 3 — Internal capacity (soft gate)

- [ ] BPC's PM bench has at least 1 PM + 1 super willing/able to commit to a 12-18 month assignment starting Q4 2026. If **NO**, **NO-GO** or pursue with explicit subcontracting-out plan.

### Gate 4 — Estimating ROI (soft gate)

- [ ] Estimator budget of 200-400 hours is acceptable given BPC's pipeline. If pipeline already has 3+ active workspaces consuming estimator hours, the marginal hour spent on a $5M-$10M bid with low win probability is not earning its cost. If **NO**, **NO-GO**.

## Decision template

When Rocky decides, capture the outcome below:

| Item | Decision |
|---|---|
| Date | `[YYYY-MM-DD]` |
| Decision | `[GO / NO-GO]` |
| Gate 1 — Bonding | `[PASS / FAIL]` |
| Gate 2 — Past performance | `[PASS / FAIL]` |
| Gate 3 — Internal capacity | `[PASS / FAIL]` |
| Gate 4 — Estimating ROI | `[PASS / FAIL]` |
| Rationale | `[1-3 sentence summary]` |
| If NO-GO: write memo to | `bids/_NO_GO/YYYY-MM-DD-usace-ft-hood-staging-W9126G26RA015.md` |
| If GO: scaffold remaining files | `02-bid-prep-checklist.md` fill, full Sections L+M, takeoff template, contacts (CO + KO + CS), past-performance binder, federal Volumes I-IV outlines |

## Default action if no decision is made

If 5 business days pass without an explicit Rocky decision, **default to NO-GO** and write the memo. Rationale: the bid window won't wait, and the default of "soft pursue" is a worse outcome than a clean no-go.
