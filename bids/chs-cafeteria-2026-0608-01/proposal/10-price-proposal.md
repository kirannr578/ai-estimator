# 10 — Price proposal

> **STATUS: FORMULAS REFINED {{PORTAL_PULL_DATE}} against the actual downloaded CSP package** (drawings A0.1–E1.2 + Project Manual). Quantities still `[USER TO FILL]` after Bluebeam takeoff against A2.1 / P1.1 / M1.1 / E1.2.
> Cross-references: `../price-references.md` for refined $/SF benchmarks, `../takeoff-template.json` for the line-item skeleton (now scope-pruned per spec), `../price-sheet-skeleton.json` for the CSI-grouped pricing-form skeleton.
>
> **Pricing form structure:** Single CSI-division line-item sheet inside `{{CSP_PACKAGE_PDF_FILENAME}}` (Section 00 42 13 Proposal Form). Bidder fills:
>  - One $ figure per CSI division (Divs 01, 02, 06, 09, 22, 23, 26, 27, 28; Divs 03–05, 07, 08, 11, 13, 14, 31–33 NOT USED)
>  - One $ figure for total lump-sum
>  - Substantial Completion calendar days (proposer-chosen)
>  - Acknowledgment of any addenda
>  - Respondent info + VetHUB plan + bonding-agent commitment (separate enclosure)
>
> **No bid bond required** (CSP §00 42 13 does not call for one). **No alternates** (CSP §00 42 13 has no alternate lines). **No unit-price form** (CSP §00 42 13 has no unit-price grid).

---

## A. Methodology

We construct the base bid as:

```
Base Bid = (Direct trades + Self-performed labor) × Region multiplier
        + General Conditions (duration × monthly rate)
        + Bond + Insurance (% of subtotal)
        + Contingency (% of subtotal)
        + Overhead (% of subtotal)
        + Profit (% of subtotal)
```

Where:

- **Direct trades** sum the priced line items in `../takeoff-template.json` (each = quantity × unit cost × waste factor; line items pruned to match Divs that ARE USED per spec)
- **Region multiplier** = ~0.93–0.96 for {{SITE_CITY}} ({{COUNTY}} County) per current RSMeans CCI. Carry **1.0** until the final estimator pass.
- **General conditions** = project duration ({{SC_DAYS}} days commitment) × monthly GC rate (PM + super + temp services + project setup)
- **Bond + insurance** = ~1.5–2.0% of subtotal (no bid bond required; P&P bonds at 0.6–1.2% of contract value; insurance per {{INSURANCE_PROGRAM_REF}} limits)
- **Contingency** = 7% for a single-room reno with the now-confirmed drawing+spec set; **drop from 10% to 7%** as G2 is CLOSED GREEN per `../README.md`
- **Overhead** = 10% typical
- **Profit** = 6% typical for institutional state work; consider 5% to optimize the 60%-weighted Price criterion if pursuing aggressively

---

## B. Implied bid envelope (refined per `../price-references.md` § B post-portal-pull)

The high-tier "wet lab with fume hood" is **eliminated** per Spec Division 11 NOT USED. The realistic tiers are now:

| Scenario | Lab program | $/SF | × 1,200 SF (assumed) | Implied total |
|---|---|---|---|---|
| Low | Finishes-only refresh — but spec includes MEP rough-in so NOT this | $95 | × 1,200 | ~$114K (floor only) |
| Mid (low) | Light classroom-lab (light MEP + casework, no fume hood) | $140 | × 1,200 | **~$168K** |
| Mid (high) | Standard classroom-lab (MEP rough-in + casework + safety shower / eye-wash) | $210 | × 1,200 | **~$252K** |

**Working bid envelope (refined):** **`$170K–$240K`** assuming a mid-tier classroom-lab program without fume hood and without DI water. The envelope tightens further once (a) room SF is measured from A2.1 and (b) {{CASEWORK_SUB_FILE_REF}} casework specifics are retrieved.

**Net effect of portal pull:** **the high outlier ($310/SF ≈ $372K) is OFF THE TABLE**. The bid-envelope width tightens from ~$258K to ~$70K. Pricing posture moves squarely into the **$180K–$220K sweet spot**.

---

## C. Base bid summary table (pricing form skeleton, matched to CSP §00 42 13)

> This matches the actual CSP §00 42 13 Proposal Form structure: one $ per CSI division (Divs that ARE USED only) + lump-sum + Substantial Completion days. **Divisions that are NOT USED per spec are explicitly marked $0 / N/A.**

### C-1. By CSI division (per CSP §00 42 13 form structure)

| CSI Div | Description | $ amount |
|---|---|---|
| 01 | General Requirements (PM, super, temp services, dumpster, project closeout) | `$[USER TO FILL]` |
| 02 | Existing Conditions / Selective Demolition + asbestos handling per Spec 02 26 23 (modest $3K–$10K allowance) | `$[USER TO FILL]` |
| ~~03–05~~ | **NOT USED** (no concrete, masonry, metals per spec) | N/A |
| 06 | Lab Casework per A2.1/A2.2 + {{CASEWORK_SUB_FILE_REF}} (carry $20K–$60K allowance pending {{CASEWORK_SUB_FILE_REF}} retrieval) | `$[USER TO FILL]` |
| ~~07~~ | **NOT USED** (no thermal/moisture protection per spec) | N/A |
| ~~08~~ | **NOT USED — existing door + frame + hardware stay** | N/A |
| 09 | Finishes — framing, GWB (09 22 00), ACT (09 51 00), resilient flooring (09 65 00), paint (09 91 00) per A2.1/A2.2 | `$[USER TO FILL]` |
| 10 | Specialties per Spec 10 14 00 (ADA signage per A0.2/A0.3) | `$[USER TO FILL]` |
| ~~11~~ | **NOT USED — no fume hood, no lab equipment** | N/A |
| ~~12, 13, 14~~ | **NOT USED** | N/A |
| 21 | Fire Suppression (sprinkler-head relocation; no spec — deferred submittal allowance $1K–$5K) | `$[USER TO FILL]` |
| 22 | Plumbing per P1.1 (lab fixtures, eye-wash + safety shower if shown) | `$[USER TO FILL]` |
| 23 | HVAC per M1.1 + MEP1.0 (diffuser relocation, VAV retrim, TAB report) | `$[USER TO FILL]` |
| 26 | Electrical per E1.1 + E1.2 (lighting + controls retrofit, branch wiring + devices) | `$[USER TO FILL]` |
| 27 | Communications / low-voltage pathway ({{AGENCY_SHORT}} TS pulls cable) | `$[USER TO FILL]` |
| 28 | Electronic Safety / Fire Alarm (device relocation) | `$[USER TO FILL]` |
| ~~31–33~~ | **NOT USED** (no earthwork, utilities, exterior) | N/A |
| **Subtotal direct trades** | | `$[USER TO FILL]` |
| × Region multiplier (~0.93–0.96 {{SITE_CITY}}) | | `$[USER TO FILL]` |
| **Subtotal trades (region-adjusted)** | | `$[USER TO FILL]` |
| General Conditions (70 days × monthly rate) | | `$[USER TO FILL]` |
| Bond + Insurance (~1.5–2.0% of subtotal; no bid bond) | | `$[USER TO FILL]` |
| **Subtotal pre-OH/P/C** | | `$[USER TO FILL]` |
| Contingency (7%) | | `$[USER TO FILL]` |
| Overhead (10%) | | `$[USER TO FILL]` |
| Profit (6%, or 5% if aggressive on the 60%-weighted Price criterion) | | `$[USER TO FILL]` |
| **BASE LUMP-SUM PROPOSAL PRICE** | | **`$[USER TO FILL]`** |
| **Substantial Completion (calendar days from NTP, proposer-chosen, 10% weight)** | | **70 cal days** |
| Final Completion (fixed at Subs.Comp. + 30 cal days per CSP §00 42 13) | | 100 cal days |

### C-2. Owner contingency allowance

**Not specified in CSP §00 42 13** (confirmed against the downloaded form). No owner-controlled contingency line to carry.

### C-3. Alternates

**Not specified in CSP §00 42 13** (confirmed against the downloaded form). Do NOT submit any unsolicited alternates — risks non-responsiveness.

### C-4. Unit prices

**Not specified in CSP §00 42 13** (confirmed against the downloaded form). No unit-price grid. Any pricing for change-order work is governed by {{ISSUING_OFFICE}} UGSC Article 11 (Changes).

---

## D. Pricing posture (refined per `../price-references.md` § F post-portal-pull)

- **Contingency:** 7% baseline (G2 CLOSED GREEN so we no longer need the 10% drawing-uncertainty bump).
- **Bid posture:** middle of the mid-tier range (~$175–$200/SF effective rate). Aggressive: lower end ($150–$175/SF) for an experience-light {{AGENCY_SHORT}} portfolio.
- **Floor:** do not go below ~$140/SF — below this, the 10%-weighted Construction Time + bond + insurance start eating margin given the Net-75 payment terms in the {{ISSUING_OFFICE}} MVA.
- **Ceiling:** do not go above ~$240/SF — {{AGENCY_SHORT}} evaluators reading {{AE_FIRM_NAME}} + {{MEP_FIRM_NAME}} scope confirm will mark higher pricing as unjustified.

---

## E. Bid bond

**NOT REQUIRED.** Per CSP §00 42 13 (confirmed against the downloaded form), no bid bond is required for this CSP. Skip the bid-bond enclosure entirely.

`../12-bid-bond-letter-template.md` is now **not needed for submittal** — keep on file as a generic template for future use.

---

## F. Performance + payment bond commitment

- **100% of contract value, each**, on award per Spec Section 00 61 13 (Performance Bond) and 00 61 14 (Payment Bond)
- {{AGENCY_SHORT}} System bond forms are referenced in the Project Manual — use the forms attached to the spec sections, not generic AIA forms
- Bonding-agent commitment letter included with proposal — letterhead, signed by underwriter
- Bond premium typically 0.6–1.2% of contract value; included in the Bond + Insurance line in § C-1
- Insurance limits flow from the {{INSURANCE_PROGRAM_REF}} (referenced in Spec Section 00 73 00 Supplementary Conditions); confirm GL + Auto + W/C + Umbrella against current carrier before bid submittal

---

## G. Pricing-form workflow (post-portal-pull state)

1. ✅ CSP §00 42 13 Proposal Form is in hand (within `{{CSP_PACKAGE_PDF_FILENAME}}`).
2. ✅ Format compared — single CSI-division line-item sheet + lump-sum + Substantial Completion days. No alternates, no unit prices, no owner allowance.
3. ✅ This guide is now matched to the actual form (§ C-1 above).
4. **NEXT:** populate from the takeoff (`../takeoff-template.json`) against the actual drawings (A2.1 / P1.1 / M1.1 / E1.2).
5. Run the math twice. Sum check against `../price-references.md` § C per-trade benchmarks.
6. 2-person QC pass.
7. Sign and seal per `08-csp-proposal-form-fill-guide.md` § D.

---

## H. Pricing risks (cross-reference `../07-risk-register.md`)

| Risk | Pricing impact | Mitigation |
|---|---|---|
| R-03 (hidden lab utilities) | Now bounded — fume hood OFF, DI/lab gas only if shown on P1.1; +5–10% on MEP scopes max | Carry $5K–$10K lab-utility allowance; confirm P1.1 scope at takeoff |
| R-06 (thin drawings) | RESOLVED — full drawing set + spec in hand; contingency stays at 7% | No bump needed |
| R-07 (occupied building / after-hours) | +10–25% on affected trades (demo, fire alarm, sprinkler, plumbing cutover) | Already priced |
| R-08 (existing-conditions surprises — asbestos) | $3K–$10K allowance per Spec 02 26 23 procedural handling | Allowance line in § C-1 Div 02 |
| R-09 ({{COUNTY}} County prevailing wage) | +1–5% on direct labor | Pull {{AGENCY_SHORT}} SGC prevailing wage; cross-check against firm labor rates |
| R-10 (insurance limits per {{INSURANCE_PROGRAM_REF}}) | +$2K–$8K one-time premium for Umbrella increase | One-line bid adder if material; confirm at G3 |
| R-NEW (Net-75 payment terms per {{ISSUING_OFFICE}} MVA) | Working capital float on a 70-day job → ~2% effective margin impact | Bake into the 6% profit assumption or move to 5%+ if pursuing aggressively |
| R-NEW ({{CASEWORK_SUB_FILE_REF}} not yet retrieved) | Casework allowance $20K–$60K wide range until file in hand | Retrieve via {{PM_NAME}} outreach (`../outreach/01-...md`); tighten range to ~$15K wide at G3 |

---

## I. Honest dependency note for the reviewer

The numbers in this document are **placeholders for the SF-driven line items** until:

1. ✅ CSP package landed (G2 CLOSED GREEN per `../README.md`) → drawings + spec in hand
2. ⏳ Bluebeam takeoff against A2.1 / P1.1 / M1.1 / E1.2 → fills `../takeoff-template.json` with real quantities
3. ⏳ {{CASEWORK_SUB_FILE_REF}} retrieval (Zscaler-blocked; user to fetch manually or {{PM_NAME}} re-share) → tightens casework allowance
4. ⏳ Sub quotes from 2-3 trades (demo, casework, MEP combined) → fix sub-line unit costs
5. ⏳ {{INSURANCE_PROGRAM_REF}} insurance + Net-75 payment terms confirmed against carrier → fix bond + insurance + working-capital load

Items 2 and 4 are the main remaining estimator work; items 3 and 5 are 30-minute calls. The earliest a defensible final price exists is the morning of Mon {{BID_LOCK_DATE}} per `../timeline.md`.
