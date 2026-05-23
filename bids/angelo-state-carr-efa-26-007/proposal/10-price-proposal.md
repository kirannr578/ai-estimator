# Price proposal — Carr EFA Dressing Room Renovation (2026-05-23 refresh)

> Documents the price-build for the bid: subtotal stack, contingency/OH/profit overlay, the separately-carried $25K cash/contingency allowance, the unit-price grid (formulas only — values come from final takeoff), and the line-item breakdown by CSI division.
>
> **Refresh basis (2026-05-23):** Project area verified at **3,115 SF** per drawing sheet AF100 (vs. earlier prep-doc assumption of ~2,500 SF — 25% larger). Contingency dropped from 8% to 7% reflecting drawing + PM in hand. Owner-furnished demarcation tightened: lockers are CONTRACTOR scope (PM Sec 10 51 13), Division 21 Fire Suppression IS owner-furnished (PM TOC marks Div 21 "NOT USED"). Working bid envelope refined from $425K–$560K mid $485K to **$465K–$575K mid $520K** per `../price-references.md` § A.

---

## A. Pricing framework (matches `../takeoff-template.json` `_meta`)

| Parameter | Value | Notes |
|---|---|---|
| Region multiplier | 1.0 | Tom Green County / San Angelo typically clears at 0.88–0.93 of national; using 1.0 as a conservative ceiling until RSMeans City Cost Index lookup confirms. Tom Green County prevailing wage is the labor floor per `../prevailing-wages.md` (confirmed operative WD per PM Sec 00 73 46). |
| Contingency | 7% | Reduced from 8% now that drawings + PM are in hand. Could drop to 6% post-site walk; bump to 10% if Section 00 31 00 hazmat survey (currently missing from PM) reveals issues. |
| Overhead | 10% | Standard TX state institutional rate |
| Profit | 6% | Mid-range for TX state institutional work; drop to 5% if pricing competitiveness is the differentiator vs. the 5 confirmed competitor firms (TPI Construction, Lee Lewis Construction, Crockett Facilities Services, San Angelo–based GCs), raise to 7% if a strong past-performance / HSP narrative gives margin headroom |
| Cash/contingency allowance | $25,000.00 | Per Attachment A — SEPARATE line; NOT rolled into base; NOT marked up |
| Bid bond cost | 1.0–1.5% of bid | Included in markup or carried separately per bonding-agent quote (`outreach/03-email-bonding-agent.md`) |
| P&P bond cost | 1.0–1.5% of bid | Included in markup |
| Insurance load | ~1.0% of bid | Standard TX broker quote per UGSC Art. 5 |
| **Project area** | **3,115 SF total** | Verified per AF100; back-of-house 1,047 SF (heavy reno @ $350–$420/SF) + circulation/entry 2,068 SF (light reno @ $50–$95/SF) per `../price-references.md` § A |

---

## B. Total proposal stack (the formulas)

```
Direct cost subtotal             = SUM(line items in C below)               [from takeoff]

Contingency                      = Direct cost × 7%                         [computed]

Subtotal with contingency        = Direct cost + Contingency                [sum]

Overhead                         = Subtotal with contingency × 10%          [computed]

Profit                           = Subtotal with contingency × 6%           [computed]

Bid subtotal                     = Subtotal with contingency + Overhead + Profit  [sum]

Bond + insurance load (~2.5%)    = Bid subtotal × 2.5%                      [computed]

────────────────────────────────────────────────────────────────────────────
BASE PROPOSAL PRICE              = Bid subtotal + Bond + insurance load     [→ Attachment A § 2a]
────────────────────────────────────────────────────────────────────────────

Cash/contingency allowance       = $25,000.00                               [→ Attachment A § 2b — fixed by owner]

────────────────────────────────────────────────────────────────────────────
TOTAL PROPOSAL                   = BASE PROPOSAL PRICE + $25,000            [→ Attachment A § 2c]
────────────────────────────────────────────────────────────────────────────
```

**Working envelope (refined 2026-05-23):** **$465K – $575K** per `../price-references.md` § A using verified 3,115 SF and split-zone $/SF. Midpoint **~$520K** is ~$35K above the implied $500K published budget — this reflects the 25%-larger-than-assumed area but is still well within typical TTUS contingency-aware budget ranges. **Base proposal alone should land in $440K–$550K (midpoint ~$495K)** with the $25K allowance brought separately to the $465K–$575K all-in.

**Bid-positioning advice** (per `../price-references.md` § B refresh): Submit at **mid-low to mid** (~$485K–$505K base) to be competitive against TPI / Lee Lewis / Crockett (who likely target $475K–$515K), but not below $470K base — anything below that signals scope misread on the 3,115 SF.

---

## C. Direct cost breakdown by CSI division (formulas, not values)

Each row pulls from `../takeoff-template.json` once quantities are filled. Formulas are SUM-of-line-items within each division. `[USER TO FILL after takeoff]` is the placeholder for each numeric value.

| Division | Title | Direct cost | % of subtotal | Source |
|---|---|---|---|---|
| 01 | General Requirements (PM + super + temp facilities + close-out) | `[USER TO FILL]` | 12–18% | `../takeoff-template.json` line items div 01 |
| 02 | Existing Conditions / Selective Demolition (finishes + MEP demo + hazmat allowance if any) | `[USER TO FILL]` | 6–10% | div 02 |
| 04 | Masonry (brick restoration — clean, repoint, seal) | `[USER TO FILL]` | 1–3% | div 04 |
| 06 | Wood / Plastics / Composites (carpentry + blocking + finish carpentry + theater millwork) | `[USER TO FILL]` | 8–14% | div 06 |
| 08 | Openings (doors, HM frames, Sargent hardware, CBORD prep) | `[USER TO FILL]` | 4–7% | div 08 |
| 09 | Finishes (framing, GWB, ACT, flooring, base, paint) | `[USER TO FILL]` | 14–22% | div 09 |
| 10 | Specialties (signage, toilet accessories, fire extinguishers) | `[USER TO FILL]` | 1–3% | div 10 |
| 21 | Fire Suppression | **$0** | 0% | OWNER-FURNISHED — PM TOC marks Div 21 "NOT USED" — DO NOT PRICE |
| 10 51 13 | Metal Lockers | `[USER TO FILL]` | 1–2% | CONTRACTOR scope per PM Sec 10 51 13 (corrected from earlier prep-doc assumption that this was owner-furnished) |
| 22 | Plumbing (fixtures + rough-in + showers if applicable) | `[USER TO FILL]` | 8–12% | div 22 |
| 23 | HVAC (full system replacement + exhaust + TAB + controls) | `[USER TO FILL]` | 14–22% | div 23 |
| 26 | Electrical (full replacement + theater-grade lighting + controls + sub-panel if needed) | `[USER TO FILL]` | 14–22% | div 26 |
| 27 | Communications (low-voltage pathway only — CABLE is owner-furnished) | `[USER TO FILL]` | 1–2% | div 27 |
| 28 | Electronic Safety / Security (FA device relocation — CBORD devices are owner-furnished) | `[USER TO FILL]` | 1–2% | div 28 |
| | **Direct cost subtotal** | **`[USER TO FILL: $XXX,XXX]`** | **~100%** | sum |
| | **Contingency (8%)** | **`[USER TO FILL]`** | | computed |
| | **Subtotal with contingency** | **`[USER TO FILL]`** | | sum |
| | **Overhead (10%)** | **`[USER TO FILL]`** | | computed |
| | **Profit (6%)** | **`[USER TO FILL]`** | | computed |
| | **Bid subtotal** | **`[USER TO FILL]`** | | sum |
| | **Bond + insurance (~2.5%)** | **`[USER TO FILL]`** | | computed |
| | **BASE PROPOSAL PRICE** | **`[USER TO FILL: → Attachment A § 2a]`** | | sum |
| | **Cash/contingency allowance (Attachment A)** | **$25,000.00** | | fixed |
| | **TOTAL PROPOSAL** | **`[USER TO FILL: → Attachment A § 2c]`** | | sum |

> ⚠️ Sales tax is **NOT** included in any line. ASU is sales-tax-exempt per Attachment E (TX Form 01-339). Subcontractors and material suppliers invoice without TX sales tax for items incorporated into the work.

---

## D. Unit prices (formulas — values come from final takeoff)

Per Attachment A's standard unit-price grid, the bid carries unit prices for owner-directed change items. These set the ceiling for change-order pricing during construction — bid at full retail (sub cost + full GC markup), NOT shaved.

> `[VERIFY ON PDF: confirm exactly which unit prices the Attachment A grid requests]`. The list below is the typical TTUS pattern; replace with the actual grid contents on the form once confirmed.

| # | Item | Unit | Add price | Deduct price |
|---|---|---|---|---|
| 1 | Additional/deduct dressing-room SF (full reno including finishes + MEP) | SF | `[USER TO FILL]` | `[USER TO FILL]` |
| 2 | Additional door + HM frame + Sargent cylindrical lockset + CBORD prep | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 3 | Additional 20A receptacle (dedicated circuit + device) | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 4 | Additional dimmable LED fixture (theater-grade) | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 5 | Additional ADA lavatory + plumbing rough-in | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 6 | Additional ADA water closet + plumbing rough-in | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 7 | Additional makeup-mirror surround with LED frame (millwork) | EA | `[USER TO FILL]` | `[USER TO FILL]` |
| 8 | Additional SF of acoustical ceiling tile (grid + tile) | SF | `[USER TO FILL]` | `[USER TO FILL]` |
| 9 | Additional SF of sheet vinyl flooring (heat-welded) | SF | `[USER TO FILL]` | `[USER TO FILL]` |
| 10 | Additional SF of paint (2 coats institutional) | SF | `[USER TO FILL]` | `[USER TO FILL]` |
| 11 | Hazmat abatement (VCT + mastic per SF if found) | SF | `[USER TO FILL]` | n/a (deduct n/a — abatement is presence-triggered) |

### Unit-price computation pattern

For each unit price, the formula is:

```
Add unit price = (sub bare cost × 1.10 sub OH/profit)
               × 1.08 contingency
               × 1.10 GC overhead
               × 1.06 GC profit
               × 1.025 bond + insurance
               = sub cost × ~1.357 effective markup
```

For deduct unit prices, deduct at the same sub bare cost without the markup stack — the markup is already in the base lump-sum.

---

## E. Allowance handling — the $25K cash/contingency

Per Attachment A and `../04-scope-of-work.md` § D-8:

- **Separate line on Attachment A.** Do NOT include in the base proposal price.
- **NOT marked up.** Bid this line at exactly $25,000.00.
- **Allowance consumption mechanism (post-award).** Allowance is drawn against during construction via Pending Change Order (PCO) procedure per UGSC Art. 9. Each draw requires Samuel Guevara's written authorization. Common consumption scenarios:
  - Differing site conditions (e.g. surprise asbestos requires abatement; surprise undersized electrical service requires sub-panel upgrade): allowance preferred to a change order because no contract-sum increase required
  - Owner-directed minor scope additions (e.g. add 1 outlet at a position the owner identifies post-NTP)
  - Late-stage A/E clarification that adds work below the change-threshold value
- **What allowance is NOT for.** Owner-directed major scope changes get a normal change order (Article 9), not the allowance. Allowance is for unforeseen scope, not directed scope.
- **Reconciliation at substantial completion.** Any unconsumed allowance is returned to ASU as a deduct via final change order. The firm does NOT retain unspent allowance.

---

## F. Markup discipline (per `../06-evaluation-strategy.md` § D)

- **Sub cost at face value** — no shaving sub quotes to make the headline number. If a sub bids $35K, $35K goes in the base.
- **General conditions priced from the 124-day window** at the firm's in-house rate, not at a "win the bid" reduced rate.
- **Bond + insurance load** — ~1.5% bond + ~1.0% insurance combined = ~2.5% on a sub-$1M TX state job.
- **Contingency 8%** — driven by the 4 risks listed in `../takeoff-template.json` `_meta.contingency_pct_note`. Bump to 12% if drawings prove thin OR site walk surfaces existing-conditions surprises.
- **Overhead 10%** standard.
- **Profit 6%** mid-range for TX state institutional.
- **Don't over-shave.** TTUS rejects bids >25% below median as "non-responsible." The $500K published budget is a strong signal of median; landing at $425K–$485K is competitive without flagging non-responsibility.

---

## G. Sensitivity analysis (what if scope is different)

Run these scenarios against the final takeoff (per `../price-references.md` § E):

| Scenario | SF | MEP scope | Base proposal | Total (with $25K) | Notes |
|---|---|---|---|---|---|
| A — Light reno | 2,000 | finishes + light MEP | ~$275K | ~$300K | Below $500K budget — owner has discretion for additional scope |
| **B — Mid reno (most likely)** | 2,500 | full MEP replacement | **~$460K** | **~$485K** | Matches published $500K budget |
| C — Heavy reno (upper bound) | 3,000 | full MEP + showers + theater-grade millwork | ~$655K | ~$680K | Exceeds $500K budget — surface to user immediately if drawings indicate Scenario C |

Once drawings land, run the takeoff against each scenario. If Scenario C is the drawn scope at $500K budget, surface to user + Samuel immediately for a budget conversation BEFORE the proposal goes in.

---

## H. Pricing QC checklist (2026-06-02 internal pricing review meeting)

- [ ] All `../takeoff-template.json` line items have quantities filled from drawings (or marked $0 if owner-furnished — verify against the demarcation table)
- [ ] All sub quotes received and reconciled against the takeoff — no orphaned scope items, no double-bid items
- [ ] Owner-furnished items (FP, AV cabling, FF&E, CBORD devices) confirmed at $0
- [ ] Hazmat allowance reconciled with ASU EHS survey result (or carry default $10K–$25K with assumption documented)
- [ ] After-hours premium labor (~25% of demo + MEP cutover hours) priced at the appropriate burden factor
- [ ] Long-lead items priced at the supplier's confirmed quote (theater millwork, Sargent hardware, HVAC equipment)
- [ ] Bond + insurance load matches the bonding-agent + broker quotes
- [ ] Contingency 8% applied to direct cost subtotal
- [ ] OH 10% applied to direct + contingency
- [ ] Profit 6% applied to direct + contingency
- [ ] Bond + insurance 2.5% applied to bid subtotal
- [ ] $25K allowance kept SEPARATE from base
- [ ] Sales tax NOT included in any line
- [ ] Unit prices computed at full retail (sub cost + full markup stack)
- [ ] Total proposal lands in $425K–$560K envelope (or surface deviation to user)
- [ ] Total proposal is NOT more than 25% below median ($500K reference)
- [ ] Cross-check against the 3 sensitivity scenarios — base price aligns with the matching scenario

---

## I. Cross-reference to other documents

| Question | Document |
|---|---|
| Detailed scope by trade with quantities | `../takeoff-template.json` |
| Skeleton for the post-drawings final takeoff | `../price-sheet-skeleton.json` |
| Quantity-driven scope rows (CSI Div by Div) | `../04-scope-of-work.md` § C |
| $/SF and scenario benchmarks | `../price-references.md` |
| Tom Green County prevailing wage + escalation factor | `../prevailing-wages.md` |
| Risk factors driving contingency | `../07-risk-register.md` |
| Owner-furnished items NOT priced | `../04-scope-of-work.md` § A |
