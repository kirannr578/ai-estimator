# Material suppliers — registry

**Audience:** BPC estimating + ops.
**Status:** Skeleton. **BPC has no internal supplier / pricing relationships established at this writing**; every section below is a placeholder pending operator action.
**Last updated:** 2026-05-27
**Maintainer:** [NOT YET ASSIGNED]

---

## Why this exists

BPC's estimating layer is currently 100% reliant on external public data sources (BLS PPI, FRED, EIA, OEWS, Davis-Bacon — see `firm/playbooks/pricing-data-sources.md`). The long-term plan is to back those public benchmarks with internal supplier accounts that give us:

1. **Pro pricing** (typically 5–25% below shelf retail on building materials).
2. **Bid-room quotes** for project-specific bulk orders.
3. **Net-30 / Net-60 payment terms** to align with project draw schedules.
4. **A negotiated discount history** auditable per project for transparent margin tracking.
5. **A return / take-back history** that informs honest VE (Value Engineering) suggestions on future bids.

Until accounts are open and a quarter of transactions are flowing through them, this file remains a **skeleton**. Estimators should NOT cite "supplier pricing" in bids until the registry below shows an actual confirmed-quote record.

---

## Pro accounts

### Home Depot Pro Xtra
**Status:** `[NOT YET ESTABLISHED]`

**Action items:**
- [ ] Register BPC EIN at https://www.homedepot.com/c/Pro_Xtra
- [ ] Apply for Pro Xtra net-30 (commercial credit application).
- [ ] Designate a primary buyer account (typically the PM on the active bid).
- [ ] Document the BPC store-of-record (typically the closest Pro Desk to the project site).

### Lowe's for Pros
**Status:** `[NOT YET ESTABLISHED]`

**Action items:**
- [ ] Register at https://www.lowesforpros.com/
- [ ] Apply for Lowe's Business Credit (LAR).
- [ ] Document primary buyer account.

### Ferguson (plumbing / mech)
**Status:** `[NOT YET ESTABLISHED]`

**Action items:**
- [ ] Open commercial account at the nearest Ferguson branch.
- [ ] Confirm whether the branch handles bid-room quotes (most do; some route to the regional bid desk).
- [ ] Get sales rep contact + email.

### White Cap (commercial construction supplies)
**Status:** `[NOT YET ESTABLISHED]`

**Action items:**
- [ ] Open commercial account at https://www.whitecap.com/
- [ ] Identify the regional rep for DFW / Austin / Houston (depends on first project site).
- [ ] Confirm fastener + anchor + concrete-accessory pricing tier.

### Sherwin-Williams (paint / coatings)
**Status:** `[NOT YET ESTABLISHED]`

**Action items:**
- [ ] Apply for Sherwin-Williams Commercial Account at https://www.sherwin-williams.com/painting-contractors
- [ ] Document store-of-record per market.
- [ ] Confirm whether project-specific quotes go through the store rep or a regional commercial desk.

### (Add as needed)
- Trex / TimberTech (decking)
- CertainTeed (insulation / gypsum)
- Behr / Benjamin Moore (paint alternates)
- Specialty roofing: GAF, CertainTeed, Tamko
- HVAC equipment: Carrier, Trane, Lennox dealer reps
- Local concrete supplier per market (CalPortland, Holcim, Texas Industries / Eagle Materials)
- Local lumber yard per market (84 Lumber, Foxworth-Galbraith)

---

## Negotiated discount tracking

Template for each established supplier — fill in after the first written discount confirmation:

| Supplier | Account # | Discount tier | Negotiated terms | Effective | Reviewed | Notes |
|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | |

**How to use:**
- Discount tier = the price modifier vs MSRP / shelf-retail (e.g. "Pro Xtra 7% off paint, 0% off lumber").
- Negotiated terms = payment terms, freight allowances, bulk-order thresholds.
- "Effective" + "Reviewed" form an audit trail — every discount tier must be re-confirmed at least annually.

---

## Material take-back / VE history

Template — fill in after the first project closes out:

| Project | Date | Material | Reason | Vendor handled? | $ recovered | $ lost | Lesson |
|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | |

**How to use:**
- "Reason" categories: over-ordered / wrong spec / damaged in transit / customer-driven change / contingency-budget release.
- "Vendor handled?" tracks whether the supplier accepted the return (yes / partial / no) — important for VE conversations with future clients.
- "Lesson" feeds back into the takeoff waste-factor table in `config/cost_database.json`.

---

## Project-specific quote log

Template — populate at bid time for each active opportunity:

| Bid | Date | Supplier | Material | Qty | Unit price | Total | Quote ref / email | Used in estimate? |
|---|---|---|---|---|---|---|---|---|
| _(none yet)_ | | | | | | | | |

**Reminder:** quotes from suppliers are confidential to BPC. Do not paste them into AI chat sessions, public docs, or shared drives outside BPC's controlled storage. See workspace rule `04-data-classification.mdc`.

---

## Cross-references

- **Pricing-data playbook:** `firm/playbooks/pricing-data-sources.md` — the external public sources we use today (BLS / FRED / EIA / OEWS / Davis-Bacon).
- **Cost database:** `config/cost_database.json` — the BPC seed cost DB; escalation flows in from PPI snapshots.
- **Escalation engine:** `core/pricing/escalation.py` — maps cost-DB entries to PPI series.

---

**End of registry.**
