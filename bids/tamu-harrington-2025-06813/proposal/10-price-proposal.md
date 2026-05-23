# 10 — Price proposal

> **STATUS: FORMULAS ONLY — actual values pending takeoff against the e-Builder drawing set.**
> Cross-references: `../price-references.md` for $/SF benchmarks, `../takeoff-template.json` for the line-item skeleton, `../price-sheet-skeleton.json` for the CSI-grouped pricing-form skeleton.

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

- **Direct trades** sum the priced line items in `../takeoff-template.json` (each = quantity × unit cost × waste factor)
- **Region multiplier** = ~0.93–0.96 for College Station (Brazos County) per current RSMeans CCI. Carry **1.0** until the final estimator pass.
- **General conditions** = project duration × monthly GC rate (PM + super + temp services + project setup)
- **Bond + insurance** = ~2.0–2.5% of subtotal (5% bid bond cost is one-time; P&P bonds are typically 0.6–1.2% of contract value)
- **Contingency** = 7% for a single-room reno with reasonable drawings; 10% if drawings prove thin
- **Overhead** = 10% typical
- **Profit** = 6% typical for institutional state work

---

## B. Implied bid envelope (from `../price-references.md` § B)

| Scenario | Lab program | $/SF | × 1,200 SF (assumed) | Implied total |
|---|---|---|---|---|
| Low | Finishes-only classroom refresh | $95 | × 1,200 | **~$114K** |
| Mid (low) | Light science classroom-lab | $140 | × 1,200 | **~$168K** |
| Mid (high) | Standard science classroom-lab | $210 | × 1,200 | **~$252K** |
| High | Wet lab with fume hood / DI water / lab gas / acid waste | $310 | × 1,200 | **~$372K** |

**Working bid envelope:** **`$170K–$250K`** assuming a mid-tier light-science-classroom-lab program. The envelope drops to a ~$50K-wide band once we know (a) room SF from drawings and (b) lab-utility scope from MEP set.

**Honest dependence on lab-utility scope clarification:** the lab-program tier alone changes the bid by 2.5×. A bid filed without lab-utility-scope confirmation is either (a) priced low and at high CO-risk, or (b) priced high and uncompetitive. We need the MEP set or a Fred Patterson scope-clarification call before final pricing.

---

## C. Base bid summary table (pricing form skeleton)

> This is what we will populate into the actual TAMU CSP Pricing Proposal Form once the form is downloaded (`08-csp-proposal-form-fill-guide.md` § B-3). Values are placeholders.

### C-1. By CSI division

| CSI Div | Description | $ amount |
|---|---|---|
| 01 | General Requirements (PM, super, temp services, dumpster, project closeout) | `$[USER TO FILL]` |
| 02 | Existing Conditions / Selective Demolition | `$[USER TO FILL]` |
| 02 | Hazmat allowance (pending TAMU EHS clearance) | `$[USER TO FILL or "$0 pending EHS clearance"]` |
| 06 | Carpentry / Lab Casework | `$[USER TO FILL]` |
| 08 | Openings (doors, frames, hardware — if scope) | `$[USER TO FILL]` |
| 09 | Finishes (framing, GWB, ACT, flooring, base, paint) | `$[USER TO FILL]` |
| 10 | Specialties (signage, tackable panels, marker board, fire extinguishers) | `$[USER TO FILL]` |
| 11 | Lab Equipment (coordination only; owner-furnished) | `$0` (coordination time in GCs) |
| 21 | Fire Suppression (sprinkler-head relocation) | `$[USER TO FILL]` |
| 22 | Plumbing (lab fixtures, eye-wash + safety shower; lab gas + DI water if scope) | `$[USER TO FILL]` |
| 23 | HVAC (diffuser relocation, VAV retrim, TAB report; lab exhaust if scope) | `$[USER TO FILL]` |
| 26 | Electrical (lighting + controls retrofit, branch wiring + devices; lab sub-panel if scope) | `$[USER TO FILL]` |
| 27 | Communications / low-voltage pathway | `$[USER TO FILL]` |
| 28 | Electronic Safety / Fire Alarm (device relocation) | `$[USER TO FILL]` |
| **Subtotal direct trades** | | `$[USER TO FILL]` |
| × Region multiplier (~0.93–0.96 College Station) | | `$[USER TO FILL]` |
| **Subtotal trades (region-adjusted)** | | `$[USER TO FILL]` |
| General Conditions (duration × monthly rate) | | `$[USER TO FILL]` |
| Bond + Insurance (~2.0–2.5% of subtotal) | | `$[USER TO FILL]` |
| **Subtotal pre-OH/P/C** | | `$[USER TO FILL]` |
| Contingency (7%) | | `$[USER TO FILL]` |
| Overhead (10%) | | `$[USER TO FILL]` |
| Profit (6%) | | `$[USER TO FILL]` |
| **BASE LUMP-SUM PROPOSAL PRICE** | | **`$[USER TO FILL]`** |

### C-2. Owner contingency allowance (if specified by CSP)

`$[PENDING e-BUILDER ACCESS]` — if the CSP Pricing Form requires a carried owner-controlled contingency allowance (the Angelo State packet had a $25,000 allowance line per Attachment A), carry it line-by-line per the CSP instructions. **Do NOT roll into the lump-sum. Do NOT mark up.**

### C-3. Alternates

| # | Alternate description | Add / Deduct | $ amount |
|---|---|---|---|
| 1 | `[PENDING e-BUILDER ACCESS: alternates list comes from CSP package]` | | `$[USER TO FILL]` |

Bid only alternates published in the CSP package. Unsolicited alternates often get the bid disqualified for non-responsiveness.

### C-4. Unit prices

Per `08-csp-proposal-form-fill-guide.md` § B-4. Bid at full retail (sub cost + full GC markup).

---

## D. Pricing posture (from `../price-references.md` § F)

- **Contingency:** 7% baseline; bump to 10% if drawings prove thin.
- **Bid posture:** middle of the mid-tier range (~$175–$200/SF effective rate) unless firm is hungry for TAMU work, in which case low end of mid-tier (~$140–$170/SF).
- **Floor:** do not go below ~$110/SF effective rate even in the most optimistic interpretation; below this, labor + bond start eating margin.
- **Ceiling:** do not go above ~$280/SF without explicit justification in the proposal narrative — TAMU evaluators mark high outliers as red flags.

---

## E. Bid bond

- **5% of total proposal price** (per TAMU System / Tex. Gov't Code Ch. 2253 pattern)
- On TAMU System form `[PENDING e-BUILDER ACCESS: confirm bond form]`
- Payable to the **Board of Regents of The Texas A&M University System**
- Original, attached to the proposal — see `12-bid-bond-letter-template.md`
- Bonding agent: `[USER TO FILL — name + AM Best rating]`

Sample math:
- If base bid = $200,000 → bid bond = $10,000
- If base bid = $250,000 → bid bond = $12,500

---

## F. Performance + payment bond commitment

- **100% of contract value, each**, on award
- TAMU System bond forms `[PENDING e-BUILDER ACCESS]`
- Bonding-agent commitment letter included with proposal — letterhead, signed by underwriter
- Bond premium typically 0.6–1.2% of contract value; included in the Bond + Insurance line in § C-1

---

## G. Pricing-form workflow (when CSP package lands)

1. Download the actual TAMU CSP Pricing Proposal Form from the e-Builder portal.
2. Compare format to the skeleton in `../price-sheet-skeleton.json` and § C-1 above.
3. Re-author this guide to match the actual form structure.
4. Populate from the actual takeoff against the actual drawings.
5. Run the math twice. Sum check against `../price-references.md` § C per-trade benchmarks.
6. 2-person QC pass.
7. Sign and seal per `08-csp-proposal-form-fill-guide.md` § D.

---

## H. Pricing risks (cross-reference `../07-risk-register.md`)

| Risk | Pricing impact | Mitigation |
|---|---|---|
| R-03 (hidden lab utilities) | +20–40% on MEP scopes if fume hood + DI water + lab gas + acid waste all confirmed | Carry lab-utility allowance $15K–$30K in base; price detailed scope as change order if confirmed |
| R-06 (thin drawings) | +5% on contingency | Move contingency to 10% if drawing package is thin |
| R-07 (occupied building / after-hours) | +10–25% on affected trades (demo, fire alarm, sprinkler, plumbing cutover) | Already priced; surface in unit-price shift-premium line |
| R-08 (existing-conditions surprises) | $0–$8K if hazmat; $0–$15K if substrate or hidden utilities | Allowance line in § C-1 |
| R-09 (Brazos County prevailing wage above firm rates) | +1–5% on direct labor | Pull rates from CSP; cross-check against our labor rates |
| R-10 (TAMU SGC insurance limits above firm's current carrier) | +$2K–$8K one-time premium for Umbrella increase | One-line bid adder if material |

---

## I. Honest dependency note for the reviewer

The numbers in this document are **all placeholders** until:

1. The CSP package lands (G2) → enables takeoff against actual drawings → fills `../takeoff-template.json`
2. The lab-utility scope is clarified → fixes the bid-envelope tier
3. The TAMU SGC insurance limits are confirmed → fixes the bond + insurance load
4. Sub quotes come in → fix the sub-line unit costs

Until those four are resolved, this file is **scaffolding for the final price**, not a final price. The earliest a defensible final price exists is the morning of Mon 2026-06-01 per `../timeline.md`.
