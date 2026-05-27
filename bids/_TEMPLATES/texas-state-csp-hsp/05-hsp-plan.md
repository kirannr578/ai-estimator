# {{PROJECT_NAME}} — HUB Subcontracting Plan (HSP)

> **Source playbook:** [`firm/playbooks/texas-state-csp-hsp.md → §6`](../../../firm/playbooks/texas-state-csp-hsp.md).
> **Source bid mined:** [`bids/tamu-harrington-2025-06813/05-hsp-plan.md`](../../tamu-harrington-2025-06813/05-hsp-plan.md).
>
> The HSP is the **#1 cause of TAMU System bid rejection** when done poorly. Start the day the workspace lands; run in parallel with technical proposal.

## 1. Goal applied

| Field | Value |
|---|---|
| Applicable HUB goal source | 34 TAC §20.284 (statewide) OR project-specific override |
| Applicable category | `{{APPLICABLE_HUB_GOAL_LABEL}}` (heavy / building / special-trade / professional / other) |
| Statewide goal | `{{STATEWIDE_HUB_GOAL_PCT}}%` |
| Project-specific override | `{{HUB_GOAL_PCT}}%` `[USER TO FILL — confirm via RFI if not explicit]` |
| **HUB commitment in BPC's HSP** | **`{{HUB_COMMIT_PCT}}%`** (≥ applicable goal) |

## 2. Self-perform justification

BPC will self-perform `{{SELF_PERFORM_PCT}}%` of the work — `{{SELF_PERFORM_SCOPE_DESCRIPTION}}` (typically GC + supervision + selective demo + punch + closeout). The HUB goal applies to the **subcontracted** portion only; self-perform $ is excluded from the HUB denominator.

Justification for self-performing this scope:

- `{{REASON_1}}` (e.g. "GC supervision must be by prime per agency-managed contract")
- `{{REASON_2}}` (e.g. "Selective demo is small-tonnage and BPC's standard self-perform discipline")
- `{{REASON_3}}` (e.g. "Punch + closeout require GC's documentation discipline")

## 3. Per-trade HSP allocation

| Trade | % of contract | Plan | Target HUB share within trade | $ committed to HUB |
|---|---|---|---|---|
| Demolition | `{{DEMO_PCT}}%` | Sub | 100% | $`{{DEMO_HUB_$}}` |
| Drywall + framing | `{{DRYWALL_PCT}}%` | Sub | 50% | $`{{DRYWALL_HUB_$}}` |
| Casework / millwork | `{{CASEWORK_PCT}}%` | Sub | 25% | $`{{CASEWORK_HUB_$}}` |
| Doors / frames / hardware | `{{DOORS_PCT}}%` | Sub | per-sub | $`{{DOORS_HUB_$}}` |
| Flooring | `{{FLOORING_PCT}}%` | Sub | 50% | $`{{FLOORING_HUB_$}}` |
| Paint | `{{PAINT_PCT}}%` | Sub | 100% | $`{{PAINT_HUB_$}}` |
| Acoustic ceilings | `{{CEILING_PCT}}%` | Sub | 50% | $`{{CEILING_HUB_$}}` |
| Electrical | `{{ELEC_PCT}}%` | Sub | 50% | $`{{ELEC_HUB_$}}` |
| HVAC | `{{HVAC_PCT}}%` | Sub | 25% | $`{{HVAC_HUB_$}}` |
| Plumbing | `{{PLUMB_PCT}}%` | Sub | 50% | $`{{PLUMB_HUB_$}}` |
| Fire sprinkler | `{{SPRINK_PCT}}%` | Sub | 25% | $`{{SPRINK_HUB_$}}` |
| Lockers / specialty (per project) | `{{SPEC_PCT}}%` | Sub | varies | $`{{SPEC_HUB_$}}` |
| Tile + waterproofing (if wet rooms) | `{{TILE_PCT}}%` | Sub | 25% | $`{{TILE_HUB_$}}` |
| Self-perform (GC + super + demo + punch + closeout) | `{{SELF_PCT}}%` | Self | n/a (excluded) | n/a |
| OH + profit + bond + insurance | `{{OH_PCT}}%` | n/a | n/a (excluded) | n/a |
| **Total HSP commitment** | | | | **$`{{HUB_TOTAL_$}}` (`{{HUB_COMMIT_PCT}}%` of subcontracted Work)** |

## 4. HUB sub sourcing — TX CMBL Search

Process per trade (target: ≥ 5 HUB candidates contacted):

1. **TX CMBL HUB Search** at <https://comptroller.texas.gov/purchasing/vendor/hub/search.php>
2. Filter by HUB-certified + NIGP/NAICS for trade + `{{COUNTY}}` + adjacent counties + statewide for specialty
3. Solicitation packet sent (project name + number, scope summary, due date, plans link, required certs, GC contact)
4. Log entry in outreach log (`local/hub-outreach-log.csv` — outside git):
   ```
   date,trade,sub_name,hub_cert_number,contact_email,method,outcome,bid_amount,notes
   ```

## 5. Good-Faith Effort (GFE) documentation

Required per 34 TAC §20.285 if HSP commitment does not meet the goal — even at commitment ≥ goal, complete all four for robustness:

| GFE element | Status | Evidence file |
|---|---|---|
| Scope divided into reasonable HUB-sized portions | ☐ | per-trade table above |
| Advertised in ≥ 2 HUB publications | ☐ | `{{AD_FILE_1}}`, `{{AD_FILE_2}}` |
| Written notice to representative sample of HUB subs | ☐ | outreach log + sample solicitation email |
| Attended HUB outreach events the agency hosts | ☐ | `{{EVENT_RECORD}}` |
| Contacted HUB Discretionary Contracting Forum / `{{AGENCY_SHORT}}` HUB Operations | ☐ | `{{CONTACT_RECORD}}` |

## 6. Sub-by-sub HSP roster (for the HSP form)

| Vendor name | TX HUB cert # | Trade / scope | $ value | % of subcontracted Work |
|---|---|---|---|---|
| `{{VENDOR_1}}` | `{{HUB_VID_1}}` | `{{TRADE_1}}` | $`{{VAL_1}}` | `{{PCT_1}}%` |
| `{{VENDOR_2}}` | `{{HUB_VID_2}}` | `{{TRADE_2}}` | $`{{VAL_2}}` | `{{PCT_2}}%` |
| `{{...}}` | | | | |

## 7. Post-award HSP commitments

If awarded, BPC will:

- File **Monthly Progress Assessment Reports (PARs)** with each pay app, on the State of Texas Comptroller PAR form
- Notify the `{{AGENCY_SHORT}}` HUB Office in writing of any sub substitution
- If actual HUB participation falls short of the HSP commitment, file a revised HSP (with `{{AGENCY_SHORT}}` concurrence) or document the reason and continue GFE

## 8. HSP submission

| Field | Value |
|---|---|
| HSP submission method | `{{HSP_SUBMISSION_METHOD}}` (with proposal / separate deadline) |
| HSP submission deadline | `{{HSP_DUE_DATE}}` @ `{{HSP_DUE_TIME}}` `{{HSP_DUE_TIMEZONE}}` |
| HSP form template used | `{{HSP_FORM_NAME}}` (per CSP — DO NOT use a prior bid's form) |
| HSP signer | `{{HSP_SIGNER_NAME}}`, `{{HSP_SIGNER_TITLE}}` |
| HSP signing date | `{{HSP_SIGN_DATE}}` |
