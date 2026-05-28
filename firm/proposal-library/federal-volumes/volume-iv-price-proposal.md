# Volume IV — Price Proposal

> **How to use this template** — Federal best-value tradeoff (FAR 15.101-1) Volume IV. Target page count **2–4 pages of narrative** + Schedule of Prices (CLIN/SLIN-formatted, no page limit unless Section L specifies). Tradeoff price proposals are scored on **price reasonableness** (FAR 15.404-1(b)) and **price realism** (FAR 15.404-1(d)) — the latter is the more dangerous gate, because an offer too low can be rejected as unrealistic. The narrative below documents BPC's basis of estimate so the SSEB can complete cost realism analysis without writing follow-up clarifications. **Volume IV must not contradict Volume I** (the priced scope must match the technical scope). Search-and-replace every `{{PLACEHOLDER}}`.

---

# Volume IV — Price Proposal
## {{PROJECT_NAME}} | Solicitation {{SOLICITATION_NUMBER}}
### Submitted by Blue Print Constructs (Blue Print Constructs, LLC dba) — UEI LM4YHVQ71QG7 • CAGE 9LET0

## 1. Pricing summary

### 1.1 Total evaluated price

| Element | Value |
|---|---|
| **Total Evaluated Price (sum of priced CLINs)** | **$`{{TOTAL_PRICE}}`** |
| Base CLIN total | $`{{BASE_CLIN_TOTAL}}` |
| Option CLIN total (if any) | $`{{OPTION_CLIN_TOTAL}}` |
| Alternate pricing total (if applicable) | $`{{ALTERNATE_TOTAL}}` |
| Bid bond (5% TX state / 20% federal up to $3M cap) | $`{{BID_BOND_AMOUNT}}` (separate; not included in priced total) |

### 1.2 CLIN / SLIN breakdown

| CLIN / SLIN | Description | Quantity | Unit | Unit price | Extended price |
|---|---|---|---|---|---|
| 0001 | `{{CLIN_0001_DESCRIPTION}}` | `{{CLIN_0001_QTY}}` | `{{CLIN_0001_UNIT}}` | $`{{CLIN_0001_UNIT_PRICE}}` | $`{{CLIN_0001_EXTENDED}}` |
| 0001AA | `{{SLIN_0001AA_DESCRIPTION}}` | `{{SLIN_0001AA_QTY}}` | `{{SLIN_0001AA_UNIT}}` | $`{{SLIN_0001AA_UNIT_PRICE}}` | $`{{SLIN_0001AA_EXTENDED}}` |
| 0002 | `{{CLIN_0002_DESCRIPTION}}` | `{{CLIN_0002_QTY}}` | `{{CLIN_0002_UNIT}}` | $`{{CLIN_0002_UNIT_PRICE}}` | $`{{CLIN_0002_EXTENDED}}` |
| 0003 | `{{CLIN_0003_DESCRIPTION}}` | `{{CLIN_0003_QTY}}` | `{{CLIN_0003_UNIT}}` | $`{{CLIN_0003_UNIT_PRICE}}` | $`{{CLIN_0003_EXTENDED}}` |
| 0004 | `{{CLIN_0004_DESCRIPTION}}` | `{{CLIN_0004_QTY}}` | `{{CLIN_0004_UNIT}}` | $`{{CLIN_0004_UNIT_PRICE}}` | $`{{CLIN_0004_EXTENDED}}` |
| 1001 (Option Year 1) | `{{CLIN_1001_DESCRIPTION}}` | `{{CLIN_1001_QTY}}` | `{{CLIN_1001_UNIT}}` | $`{{CLIN_1001_UNIT_PRICE}}` | $`{{CLIN_1001_EXTENDED}}` |
| `{{ADDITIONAL_CLINS}}` | | | | | |

> Schedule of Prices form (RFP Section B fill-in) is included as the first attachment to Volume IV. The CLIN structure above mirrors RFP Section B; do not renumber.

## 2. Basis of estimate

### 2.1 Methodology

BPC's price for `{{PROJECT_NAME}}` is built **bottom-up** from the takeoff at [`bids/{{SLUG}}/takeoff/`](../../../bids/{{SLUG}}/takeoff/) using:

- **Quantity takeoff** by CSI division from the issued drawings + specifications, cross-checked by two estimators independently (4-eyes rule on quantities).
- **Unit-rate productivities** from BPC's historical project records on Same-as / Similar-to scope, validated against `{{AGENCY}}`-region market data (RSMeans `{{RSMEANS_YEAR}}` city-cost-indexed to `{{COUNTY}}` County, TX; BLS PPI for materials, BLS OEWS for craft labor, EIA for energy; Davis-Bacon WD `{{WD_NUMBER}}` for federal projects).
- **Three sub quotes** per major scope item (per BPC standard) plus the lowest-of-three logic with quote integrity verified against BPC's vetted-sub-pool insurance / bonding / SAM-exclusion criteria.
- **Material quotes** from approved-vendor list (current quotes within `{{QUOTE_VALIDITY_DAYS}}` days of bid submission).

### 2.2 Cost buildup (high level)

| Element | $ value | % of total |
|---|---|---|
| Direct labor (BPC self-perform) | $`{{DIRECT_LABOR}}` | `{{DIRECT_LABOR_PCT}}%` |
| Direct material (BPC self-perform) | $`{{DIRECT_MATERIAL}}` | `{{DIRECT_MATERIAL_PCT}}%` |
| Direct equipment (BPC self-perform) | $`{{DIRECT_EQUIPMENT}}` | `{{DIRECT_EQUIPMENT_PCT}}%` |
| Subcontracted work (sum of sub quotes, vetted) | $`{{SUB_TOTAL}}` | `{{SUB_TOTAL_PCT}}%` |
| Subtotal direct cost | $`{{DIRECT_SUBTOTAL}}` | `{{DIRECT_SUBTOTAL_PCT}}%` |
| Project-specific General Requirements (GR) — temp protection, dumpster, project signage, OSHA program, QC plan, daily reports | $`{{GR_TOTAL}}` | `{{GR_PCT}}%` |
| **Subtotal direct + GR** | **$`{{DIRECT_PLUS_GR}}`** | |
| Indirect: Overhead (G&A allocated) | $`{{OH_AMOUNT}}` (`{{OH_PCT}}%` of direct + GR) | |
| Indirect: Profit | $`{{PROFIT_AMOUNT}}` (`{{PROFIT_PCT}}%` of direct + GR) | |
| Indirect: Performance + Payment Bond | $`{{BOND_AMOUNT}}` (`{{BOND_RATE}}%` of subtotal) | |
| Indirect: Builder's Risk + Project-specific Insurance | $`{{INSURANCE_AMOUNT}}` (`{{INSURANCE_RATE}}%` of subtotal) | |
| Indirect: Contingency (BPC management reserve) | $`{{CONTINGENCY_AMOUNT}}` (`{{CONTINGENCY_PCT}}%` of subtotal) | |
| **Total Evaluated Price** | **$`{{TOTAL_PRICE}}`** | |

### 2.3 Wage rates (federal projects)

Per FAR 52.222-6 (Construction Wage Rate Requirements) and the Davis-Bacon Act, BPC has priced all construction laborers + mechanics at the rates in **Wage Determination `{{WD_NUMBER}}`**, dated `{{WD_DATE}}`, applicable to `{{COUNTY}}` County, TX.

- WD attached as Volume IV Attachment B.
- BPC has flow-down to all subs at every tier (FAR 52.222-11).
- Certified payroll (WH-347) submitted weekly per FAR 52.222-8.
- Site-of-work classification list reviewed for missing classifications; conformance request will be filed pre-construction per FAR 52.222-30 if any classification needed for the work is not in the WD.

### 2.4 Wage rates (TX state-funded projects, if applicable)

> Federal Volume IV does not typically apply this section; included for cross-reference. For TX state-funded projects, BPC follows Tex. Gov't Code Ch. 2258 and the controlling county prevailing-wage table — see [`firm/playbooks/texas-state-csp-hsp.md`](../../playbooks/texas-state-csp-hsp.md).

## 3. Assumptions underlying the price

The price above assumes the following — invalidation of any triggers an RFI before contract award or a change-order request post-award per FAR 52.243-4:

- **Drawings + specifications + amendments** referenced are complete and constructable as issued.
- **Site access** available `{{ACCESS_HOURS}}` per `{{AGENCY}}` schedule; badge / escort process per `{{AGENCY}}` SOP `{{ACCESS_SOP}}`.
- **AHJ permits** issuable on the timeline assumed in the CPM.
- **Owner-Furnished items** per the OFOI list at SOW §`{{OFOI_REF}}` are delivered on the dates indicated.
- **Existing conditions** as documented; latent / differing-site conditions are FAR 52.236-2 events.
- **Hazardous materials** previously surveyed and abated by `{{AGENCY}}`; newly discovered hazmat is owner-removed.
- **Wage rates** per WD `{{WD_NUMBER}}` dated `{{WD_DATE}}`; modifications during performance trigger price-adjustment per FAR 52.222-30 if applicable.
- **Duration** of `{{SC_DAYS}}` calendar days for substantial completion; longer duration triggers extended GR per change-order mechanism.
- **Surety capacity** to issue Performance + Payment Bonds at 100% of contract value at award per FAR 52.228-15; commitment letter attached as Volume III Appendix III-D.
- **Insurance** at the limits required by Section H or as flowed down through the contract; limits are mirrored in BPC's COI (Volume IV Attachment C).
- **`{{PROJECT_SPECIFIC_ASSUMPTION_1}}`**.
- **`{{PROJECT_SPECIFIC_ASSUMPTION_2}}`**.

## 4. Unit-price schedule (if RFP requires unit prices)

For unit-price line items in RFP Section B, BPC provides:

| Item | Description | Unit | Estimated quantity | Unit price | Extended price (estimate × unit) |
|---|---|---|---|---|---|
| `{{UP_1_ITEM}}` | `{{UP_1_DESCRIPTION}}` | `{{UP_1_UNIT}}` | `{{UP_1_QTY}}` | $`{{UP_1_PRICE}}` | $`{{UP_1_EXTENDED}}` |
| `{{UP_2_ITEM}}` | `{{UP_2_DESCRIPTION}}` | `{{UP_2_UNIT}}` | `{{UP_2_QTY}}` | $`{{UP_2_PRICE}}` | $`{{UP_2_EXTENDED}}` |
| `{{UP_3_ITEM}}` | `{{UP_3_DESCRIPTION}}` | `{{UP_3_UNIT}}` | `{{UP_3_QTY}}` | $`{{UP_3_PRICE}}` | $`{{UP_3_EXTENDED}}` |

Unit prices are firm-fixed for the period of performance and apply to additive or deductive adjustments per FAR 52.243-4.

## 5. Alternate pricing (if RFP invites alternates)

> Federal RFPs sometimes invite alternates (e.g. "alternate bid for substituting `{{ALTERNATE_SCOPE}}`"). Only price an alternate if Section L explicitly requests one, **and** the alternate is consistent with the technical approach in Volume I. Do not introduce unrequested alternates — they are non-responsive.

| Alternate # | Description | $ delta from base | Net price with alternate |
|---|---|---|---|
| Alt 1 | `{{ALT_1_DESCRIPTION}}` | `{{ALT_1_DELTA}}` (Add / Deduct) | $`{{ALT_1_NET}}` |
| Alt 2 | `{{ALT_2_DESCRIPTION}}` | `{{ALT_2_DELTA}}` (Add / Deduct) | $`{{ALT_2_NET}}` |

## 6. Indirect-cost buildup detail

### 6.1 Overhead + G&A

BPC's overhead and G&A are pooled and allocated to direct cost at a rate of **`{{OH_PCT}}%`**. The pool includes:

- Home-office salaries (PIC + estimating + accounting + business development)
- Office rent, utilities, internet, software (estimating, scheduling, accounting)
- Vehicle + tool depreciation not project-billable
- Firm-level insurance (Commercial GL, Auto, Workers' Comp, Umbrella) — non-project-specific portion
- Firm-level certifications + license fees (SAM, NAICS-based, TX HUB recertification, DFW MSDC)
- Marketing + business development (proposal preparation, capability statements)

`[USER TO VERIFY OH_PCT — pull from current accounting; rate must be supportable under FAR 31.205 cost principles for federal pricing.]`

### 6.2 Profit

Profit is **`{{PROFIT_PCT}}%`** of direct + GR. Profit reflects BPC's risk-adjusted return for the scope, with consideration for:

- Contract type (FFP carries higher offeror risk than cost-reimbursable; profit reflects this)
- Cost risk (latent-conditions exposure, escalation exposure during PoP, complexity of interfaces)
- Schedule risk (LD exposure per RFP, criticality of completion date)
- Capital employed (working-capital tied up between pay-app and payment receipt)
- Past-performance leverage (BPC's ability to win without aggressive profit-cutting)

For federal weighted-guidelines analysis (FAR 15.404-4) where applicable, BPC's profit is derived from the four-factor structure (performance risk, contract-type risk, facilities capital employed, cost-control efficiency).

### 6.3 Bonding

Bonds priced at **`{{BOND_RATE}}%`** of subtotal (`{{BOND_DOLLAR_BAND}}` band per surety rate sheet):

- Performance + Payment Bond at 100% of contract value at award per FAR 52.228-15 (federal; required when contract > $150K) or RFP Section H equivalent.
- Surety: `{{SURETY_NAME}}` (Treasury Circular 570 listed; commitment letter at Volume III Appendix III-D).
- Bid Bond per SF 24 at `{{BID_BOND_PCT}}%` of bid (typically 20% federal up to $3M cap).

### 6.4 Insurance + project-specific allocations

- **Builder's Risk** at `{{BUILDERS_RISK_RATE}}%` of insurable value (if BPC-procured per RFP Section H).
- **Pollution Liability** at `{{POLLUTION_AMOUNT}}` if RFP requires (e.g. environmental remediation, abatement).
- **Project-specific endorsements** to add `{{AGENCY}}` as Additional Insured with primary-and-non-contributory wording and waiver of subrogation per RFP Section H.

## 7. Payment milestones

Per FAR 52.232-5 (Construction — Progress Payments) and the schedule above, BPC submits monthly pay applications. The pay-app cycle:

| Day of month | Activity |
|---|---|
| 25th of prior month | BPC PM compiles pay-app worksheet (Schedule of Values percentage complete, stored materials inventory, lien-waiver collection from subs) |
| 1st–3rd of month | Internal review by BPC PIC + estimating |
| 5th working day of month | Pay app submitted to `{{AGENCY}}` COR via `{{PROJECT_PORTAL}}` |
| 5th–10th of month | `{{AGENCY}}` COR + A/E review; field verification if requested |
| 14th of month (typical) | `{{AGENCY}}` certification |
| 14th–28th of month (per FAR 52.232-27 / Prompt Payment Act) | Government payment |

Conditional + unconditional lien waivers (BPC + subs) submitted with each pay app.

## 8. Cross-reference to other Volumes

| Volume | Cross-referenced item | Volume IV implication |
|---|---|---|
| Volume I §3 (Schedule) | `{{SC_DAYS}}` cal-day duration | GR budget sized to that duration |
| Volume I §6 (Sub management) | Sub list + percentages | Sub quotes incorporated in CLIN extensions |
| Volume II §2 (Key personnel) | Allocation per role | Burdened labor rate per role |
| Volume III §3 (Past performance) | Bond capacity demonstrated by Lavon RV Park | Bonding rate supportable |

If any Volume IV figure does not reconcile to its Volume I / II / III source, the inconsistency is a flag for the SSEB.

## 9. Evaluator's perspective (delete before submission — internal-use callout)

> **What scorers weight heavily on Volume IV (best-value tradeoff construction RFP):**
> 1. **Cost realism (FAR 15.404-1(d)).** The biggest evaluator concern. An offer materially below the IGE or below the cluster of competing offers is rejected as unrealistic — even if it is the lowest. The basis-of-estimate narrative + the cost buildup are the offeror's defense against this finding.
> 2. **Reasonableness (FAR 15.404-1(b)).** Above-market pricing without justification gets the offer rated as unreasonable. The unit-rate productivity sourcing + sub-quote evidence supports reasonableness.
> 3. **Internal consistency.** Volume IV's priced scope must match Volume I's technical scope; the schedule duration in Volume I must match the GR budget in Volume IV; the personnel allocation in Volume II must match the burdened labor in Volume IV.
> 4. **Wage-rate compliance.** Davis-Bacon WD applied correctly, classifications complete, conformance request flagged for any missing classification — these are FAR 52.222-6 / 52.222-11 / 52.222-30 compliance gates.
> 5. **Bonding evidence.** A current surety commitment letter on Treasury Circular 570 surety, dated within 30 days, on the surety's letterhead — supports FAR 9.104-1(a) financial responsibility.
> 6. **Profit defensibility.** A federal weighted-guidelines four-factor narrative (where applicable) supports the profit position; "industry standard" without quantification does not.
> 7. **Discipline on unrequested alternates / exceptions / qualifications.** Volume IV is **not** the place to introduce them. Unrequested alternates flip a responsive offer to non-responsive.
