# HSP — Progress Assessment Report (PAR) Template

> **How to use this template** — Post-award report on actual HUB participation vs the HSP commitment. Required by 34 TAC §20.286 for all TX state-funded contracts with an executed HSP. Cadence is **monthly** (typical, with each pay app) for most agencies, **quarterly** for some — confirm in the contract. The CPA model PAR form is at the [Texas Comptroller HUB Forms page](https://comptroller.texas.gov/purchasing/vendor/hub/forms.php); some agencies issue an agency-specific PAR form layered on top of CPA. Always use the form the contract specifies; this template captures the underlying data BPC needs regardless of form. Search-and-replace every `{{PLACEHOLDER}}`.

---

# HSP Progress Assessment Report — {{PROJECT_NAME}}
## Contract {{CONTRACT_NUMBER}} | {{AGENCY}}
### Reporting period: {{REPORTING_PERIOD_START}} to {{REPORTING_PERIOD_END}}

## 1. Cover information

| Field | Value |
|---|---|
| Prime contractor | Blue Print Constructs (Blue Print Constructs, LLC dba) |
| Prime TX HUB VID | `1874292998900` (status: confirm current renewal per `firm/compliance/README.md`) |
| Contract number | `{{CONTRACT_NUMBER}}` |
| Agency contracting office | `{{AGENCY_CONTRACTING_OFFICE}}` |
| Agency HUB Operations contact | `{{AGENCY_HUB_CONTACT}}` |
| Reporting period | `{{REPORTING_PERIOD_START}}` to `{{REPORTING_PERIOD_END}}` |
| Report frequency per contract | `{{REPORT_FREQUENCY}}` (Monthly / Quarterly) |
| Report number (sequential) | `{{REPORT_SEQ_NUMBER}}` |
| Date submitted | `{{REPORT_SUBMISSION_DATE}}` |
| Submitted by | `[USER TO FILL — BPC PM or designee]` |

## 2. HSP commitment summary (from executed HSP)

| Field | Value |
|---|---|
| Original contract value | $`{{ORIGINAL_CONTRACT_VALUE}}` |
| Current contract value (with executed mods) | $`{{CURRENT_CONTRACT_VALUE}}` |
| Subcontracted work value (denominator for HUB %) | $`{{SUB_DENOMINATOR}}` |
| HUB commitment in HSP | `{{HUB_COMMIT_PCT}}%` of subcontracted work = $`{{HUB_COMMIT_$}}` |
| Applicable goal (34 TAC §20.284 or project-specific) | `{{APPLICABLE_GOAL_PCT}}%` |

## 3. HUB participation this period

### 3.1 HUB sub payments — this period

| Sub vendor | TX HUB VID | Trade | Sub contract $ (current) | Paid this period | Cumulative paid through end of period |
|---|---|---|---|---|---|
| `{{HUB_SUB_1}}` | `{{HUB_VID_1}}` | `{{TRADE_1}}` | $`{{SUB_CONTRACT_$_1}}` | $`{{PAID_THIS_PERIOD_1}}` | $`{{CUMULATIVE_PAID_1}}` |
| `{{HUB_SUB_2}}` | `{{HUB_VID_2}}` | `{{TRADE_2}}` | $`{{SUB_CONTRACT_$_2}}` | $`{{PAID_THIS_PERIOD_2}}` | $`{{CUMULATIVE_PAID_2}}` |
| `{{HUB_SUB_3}}` | `{{HUB_VID_3}}` | `{{TRADE_3}}` | $`{{SUB_CONTRACT_$_3}}` | $`{{PAID_THIS_PERIOD_3}}` | $`{{CUMULATIVE_PAID_3}}` |
| `{{...}}` | | | | | |
| **Total HUB** | | | $`{{TOTAL_HUB_SUB_$}}` | $`{{TOTAL_HUB_PAID_THIS_PERIOD}}` | **$`{{TOTAL_HUB_CUMULATIVE_PAID}}`** |

### 3.2 Non-HUB sub payments — this period (for comparison)

| Sub vendor | Trade | Sub contract $ (current) | Paid this period | Cumulative paid |
|---|---|---|---|---|
| `{{NONHUB_SUB_1}}` | `{{NONHUB_TRADE_1}}` | $`{{NONHUB_CONTRACT_$_1}}` | $`{{NONHUB_PAID_PERIOD_1}}` | $`{{NONHUB_CUMULATIVE_PAID_1}}` |
| `{{...}}` | | | | |
| **Total non-HUB** | | $`{{TOTAL_NONHUB_SUB_$}}` | $`{{TOTAL_NONHUB_PAID_THIS_PERIOD}}` | **$`{{TOTAL_NONHUB_CUMULATIVE_PAID}}`** |

### 3.3 Cumulative HUB participation rate

| Field | Value |
|---|---|
| Cumulative HUB sub payments | $`{{TOTAL_HUB_CUMULATIVE_PAID}}` |
| Cumulative total sub payments (HUB + non-HUB) | $`{{TOTAL_SUB_CUMULATIVE_PAID}}` |
| **Cumulative HUB participation rate** | **`{{CUMULATIVE_HUB_PCT}}%`** |
| HSP commitment | `{{HUB_COMMIT_PCT}}%` |
| **Variance vs commitment** | **`{{HUB_VARIANCE_PCT}}%`** (positive = above commitment, negative = shortfall) |

## 4. Sub substitutions / additions / removals this period

| Action | Sub | TX HUB VID | Trade | $ value | Reason | Agency notification date |
|---|---|---|---|---|---|---|
| `{{ACTION_1}}` (Add / Substitute / Remove) | `{{SUB_NAME_1}}` | `{{VID_1}}` | `{{TRADE_1}}` | $`{{$_1}}` | `{{REASON_1}}` | `{{NOTIFY_DATE_1}}` |
| `{{ACTION_2}}` | `{{SUB_NAME_2}}` | `{{VID_2}}` | `{{TRADE_2}}` | $`{{$_2}}` | `{{REASON_2}}` | `{{NOTIFY_DATE_2}}` |

> **Discipline reminder** — per 34 TAC §20.286 and most TX state contracts, BPC must notify the agency HUB Operations office in writing **before** any sub substitution that affects HSP commitment. Substitution of a HUB sub with a non-HUB sub triggers a revised HSP and re-running GFE for the substituted scope.

## 5. Shortfall narrative (if applicable)

> Complete this section only if the cumulative HUB participation rate is **below** the HSP commitment.

### 5.1 Cause of shortfall

`{{SHORTFALL_CAUSE}}` — for example: "Original HUB sub for electrical (`{{ORIG_HUB_SUB}}`, VID `{{ORIG_HUB_VID}}`) declared bankruptcy on `{{BANKRUPTCY_DATE}}`; replacement sub at the same scope is not HUB-certified."

### 5.2 Continuing GFE to close the gap

To close the variance, BPC has taken / will take the following steps:

- `{{GFE_STEP_1}}` (e.g. "Re-ran CMBL HUB Search for the affected trade on `{{NEW_SEARCH_DATE}}`")
- `{{GFE_STEP_2}}` (e.g. "Solicited 5 additional HUB vendors for trade-package re-bid")
- `{{GFE_STEP_3}}` (e.g. "Engaged with `{{AGENCY}}` HUB Operations to identify candidate replacement subs")

### 5.3 Revised HSP filed?

`{{REVISED_HSP_FILED_YES_NO}}` — if Yes, attach the revised HSP form; if No, BPC continues GFE on the existing HSP.

## 6. Per-trade variance

| Trade | HSP-committed $ | Cumulative paid to HUB on this trade | Variance | Status |
|---|---|---|---|---|
| Demolition | $`{{DEMO_COMMIT_$}}` | $`{{DEMO_PAID_$}}` | `{{DEMO_VARIANCE}}` | `{{DEMO_STATUS}}` |
| Drywall | $`{{DRYWALL_COMMIT_$}}` | $`{{DRYWALL_PAID_$}}` | `{{DRYWALL_VARIANCE}}` | `{{DRYWALL_STATUS}}` |
| Casework | $`{{CASEWORK_COMMIT_$}}` | $`{{CASEWORK_PAID_$}}` | `{{CASEWORK_VARIANCE}}` | `{{CASEWORK_STATUS}}` |
| Doors / frames / hardware | $`{{DOORS_COMMIT_$}}` | $`{{DOORS_PAID_$}}` | `{{DOORS_VARIANCE}}` | `{{DOORS_STATUS}}` |
| Flooring | $`{{FLOORING_COMMIT_$}}` | $`{{FLOORING_PAID_$}}` | `{{FLOORING_VARIANCE}}` | `{{FLOORING_STATUS}}` |
| Paint | $`{{PAINT_COMMIT_$}}` | $`{{PAINT_PAID_$}}` | `{{PAINT_VARIANCE}}` | `{{PAINT_STATUS}}` |
| Ceilings | $`{{CEILING_COMMIT_$}}` | $`{{CEILING_PAID_$}}` | `{{CEILING_VARIANCE}}` | `{{CEILING_STATUS}}` |
| Electrical | $`{{ELEC_COMMIT_$}}` | $`{{ELEC_PAID_$}}` | `{{ELEC_VARIANCE}}` | `{{ELEC_STATUS}}` |
| HVAC | $`{{HVAC_COMMIT_$}}` | $`{{HVAC_PAID_$}}` | `{{HVAC_VARIANCE}}` | `{{HVAC_STATUS}}` |
| Plumbing | $`{{PLUMB_COMMIT_$}}` | $`{{PLUMB_PAID_$}}` | `{{PLUMB_VARIANCE}}` | `{{PLUMB_STATUS}}` |
| Fire sprinkler | $`{{SPRINK_COMMIT_$}}` | $`{{SPRINK_PAID_$}}` | `{{SPRINK_VARIANCE}}` | `{{SPRINK_STATUS}}` |
| Specialty | $`{{SPEC_COMMIT_$}}` | $`{{SPEC_PAID_$}}` | `{{SPEC_VARIANCE}}` | `{{SPEC_STATUS}}` |
| **Totals** | $`{{HUB_TOTAL_COMMIT_$}}` | $`{{HUB_TOTAL_PAID_$}}` | `{{TOTAL_VARIANCE}}` | |

## 7. Supporting attachments

- **Attachment A** — Pay app for the reporting period (cross-references monthly invoice; HUB sub line-item visibility)
- **Attachment B** — Lien waivers (conditional + unconditional) collected from each HUB sub
- **Attachment C** — Sub-substitution notification memo (if §4 has any rows)
- **Attachment D** — Revised HSP (if §5.3 is Yes)
- **Attachment E** — Continuing GFE evidence (if §5.2 has steps)

## 8. Sign-off

```
Submitted by:  [USER TO FILL — BPC PM or designee]
Title:         [USER TO FILL]
Date:          {{REPORT_SUBMISSION_DATE}}
Email:         [USER TO FILL]
Phone:         [USER TO FILL]

Reviewed for accuracy by:
[USER TO FILL — BPC accounting / controller]

Concurred:
Ravikiran (Rocky) Nudurupati, Principal in Charge
Blue Print Constructs, LLC dba Blueprint Constructs
```

## 9. Distribution

- `{{AGENCY}}` HUB Operations — primary recipient
- `{{AGENCY}}` Project Manager / COR — copy
- BPC project file — internal copy
- TX Comptroller (if agency requires central reporting)
