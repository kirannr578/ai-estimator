# HSP — Supplemental Form (CPA Form 2177-aligned)

> **How to use this template** — Generic supplemental HSP form aligning with the field structure of TX Comptroller CPA Form 2177. Use **only** when (a) the agency has not provided its own HSP form and CPA Form 2177 is the controlling form, or (b) the agency-provided HSP form is missing fields the CPA model expects, in which case attach this as a supplemental cover page. Always confirm at RFP issuance which HSP form the agency requires; do not substitute this form for an agency-mandated form. Search-and-replace every `{{PLACEHOLDER}}`.
>
> **Reference** — TX Comptroller HUB Subcontracting Plan (HSP) form, available at <https://comptroller.texas.gov/purchasing/vendor/hub/forms.php>. The structure below mirrors the CPA Form 2177 sections; field labels match the form on file as of `{{TEMPLATE_REF_DATE}}`. Re-verify against the most current published version before each submission.

---

# HUB Subcontracting Plan — Supplemental Form
## {{PROJECT_NAME}} | {{SOLICITATION_NUMBER}} | {{AGENCY}}

## Section 1 — Respondent (Prime) Information

| Field | Value |
|---|---|
| 1a. Respondent (company) name | Blue Print Constructs (Blue Print Constructs, LLC dba) |
| 1b. Legal entity name | RK Residential Homes and Commercial Constructions, LLC |
| 1c. State of formation | Texas |
| 1d. Date of formation | 2022-01-07 |
| 1e. Federal Employer Identification Number (FEIN / EIN) | 87-4292998 |
| 1f. TX Taxpayer ID | 32082600456 |
| 1g. TX SOS file number | 0804376974 |
| 1h. Address | 16283 Willowick Ln, Frisco, TX 75033 |
| 1i. Office phone | (469) 213-1838 |
| 1j. Primary email | contactus@blueprintconstructs.com |
| 1k. Website | https://www.blueprintconstructs.com |
| 1l. Texas HUB-certified? | `{{HUB_STATUS_YES_NO}}` (active — VID 1874292998900 renewed 2026-05-30 per user confirmation; prior cycle expired 2024-08-31. Capture new expiration `[USER TO CONFIRM: new expiration date]` before any HSP that asks for a specific cert expiration date) |
| 1m. Texas HUB VID (if certified) | `1874292998900` |
| 1n. UEI (federal) | LM4YHVQ71QG7 |
| 1o. CAGE (federal) | 9LET0 |

## Section 2 — Solicitation / Contract Information

| Field | Value |
|---|---|
| 2a. Agency | `{{AGENCY}}` |
| 2b. Solicitation / contract number | `{{SOLICITATION_NUMBER}}` |
| 2c. Solicitation type | `{{SOLICITATION_TYPE}}` (CSP / RFCSP / RFP / IFB / RFQ) |
| 2d. Project name | `{{PROJECT_NAME}}` |
| 2e. Project location | `{{PROJECT_LOCATION}}` |
| 2f. Estimated contract value | $`{{ESTIMATED_CONTRACT_VALUE}}` |
| 2g. Estimated period of performance | `{{POP_START}}` to `{{POP_END}}` |
| 2h. HSP submission deadline | `{{HSP_DUE_DATE}}` @ `{{HSP_DUE_TIME}}` `{{HSP_DUE_TIMEZONE}}` |

## Section 3 — Subcontracting Determination

| Field | Value |
|---|---|
| 3a. Will the respondent subcontract any portion of the contract? | Yes (if No, the HSP requirement does not apply; provide written justification) |
| 3b. Self-perform percentage | `{{SELF_PERFORM_PCT}}%` |
| 3c. Subcontracted percentage (denominator for HUB %) | `{{SUB_TOTAL_PCT}}%` |
| 3d. HUB commitment | `{{HUB_COMMIT_PCT}}%` of subcontracted work |
| 3e. Applicable HUB goal (34 TAC §20.284) | `{{APPLICABLE_HUB_GOAL_LABEL}}` — `{{STATEWIDE_HUB_GOAL_PCT}}%` (or project-specific override `{{HUB_GOAL_PCT}}%`) |
| 3f. Goal-met determination | `{{GOAL_MET_YES_NO}}` |

## Section 4 — Method Selection (CPA Form 2177 Method A / B / C)

The respondent is using:

- ☐ **Method A** — Subcontracting only with HUB vendors (≥ goal achieved with all-HUB subcontract pool)
- ☐ **Method B** — Subcontracting with a mix of HUB + non-HUB vendors (≥ goal achieved through partial HUB participation; requires GFE narrative if shortfall, recommended even if no shortfall)
- ☐ **Method C** — Subcontracting with non-HUB vendors only (requires comprehensive GFE narrative documenting why no HUB candidates were available or selected, per 34 TAC §20.285)

Selected method: **`{{METHOD_SELECTED}}`**

If Method B or C is selected, attach the GFE narrative ([`hsp-good-faith-effort.md`](hsp-good-faith-effort.md)) and the outreach log ([`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md)).

## Section 5 — Subcontracting Work Breakdown

> Per CPA Form 2177 Section: list each subcontracting opportunity, the percentage of total contract, planned dollar value, and whether a HUB will be used.

| # | Subcontracting opportunity (trade) | NIGP / NAICS | % of total contract | Planned $ value | HUB sub planned? | HUB sub name (if planned) | TX HUB VID (if planned) |
|---|---|---|---|---|---|---|---|
| 1 | `{{TRADE_1}}` | `{{NAICS_1}}` | `{{PCT_1}}%` | $`{{$_1}}` | `{{HUB_PLANNED_1}}` | `{{HUB_VENDOR_1}}` | `{{HUB_VID_1}}` |
| 2 | `{{TRADE_2}}` | `{{NAICS_2}}` | `{{PCT_2}}%` | $`{{$_2}}` | `{{HUB_PLANNED_2}}` | `{{HUB_VENDOR_2}}` | `{{HUB_VID_2}}` |
| 3 | `{{TRADE_3}}` | `{{NAICS_3}}` | `{{PCT_3}}%` | $`{{$_3}}` | `{{HUB_PLANNED_3}}` | `{{HUB_VENDOR_3}}` | `{{HUB_VID_3}}` |
| 4 | `{{TRADE_4}}` | `{{NAICS_4}}` | `{{PCT_4}}%` | $`{{$_4}}` | `{{HUB_PLANNED_4}}` | `{{HUB_VENDOR_4}}` | `{{HUB_VID_4}}` |
| 5 | `{{TRADE_5}}` | `{{NAICS_5}}` | `{{PCT_5}}%` | $`{{$_5}}` | `{{HUB_PLANNED_5}}` | `{{HUB_VENDOR_5}}` | `{{HUB_VID_5}}` |
| `{{...}}` | | | | | | | |
| **Total** | | | `{{TOTAL_SUB_PCT}}%` | $`{{TOTAL_SUB_$}}` | | | |

## Section 6 — HUB Sub-by-sub Roster (HSP Commitment)

> Vendors below are the HUB-certified subs BPC commits to use. By executing this HSP, BPC undertakes that any substitution requires written agency notification per 34 TAC §20.286.

| Vendor name | TX HUB VID (current) | Cert expiration | Trade / scope | Contract $ | % of subcontracted work |
|---|---|---|---|---|---|
| `{{HUB_VENDOR_1}}` | `{{HUB_VID_1}}` | `{{HUB_EXP_1}}` | `{{TRADE_1}}` | $`{{$_1}}` | `{{PCT_1}}%` |
| `{{HUB_VENDOR_2}}` | `{{HUB_VID_2}}` | `{{HUB_EXP_2}}` | `{{TRADE_2}}` | $`{{$_2}}` | `{{PCT_2}}%` |
| `{{HUB_VENDOR_3}}` | `{{HUB_VID_3}}` | `{{HUB_EXP_3}}` | `{{TRADE_3}}` | $`{{$_3}}` | `{{PCT_3}}%` |
| `{{...}}` | | | | | |
| **Total HUB commitment** | | | | $`{{HUB_TOTAL_$}}` | **`{{HUB_COMMIT_PCT}}%`** |

## Section 7 — Good-Faith Effort Documentation (required for Method B and C)

If Method B or C is selected, the GFE narrative must address each element of 34 TAC §20.285(d):

| GFE element | 34 TAC reference | Evidence file (in this submission package) |
|---|---|---|
| Scope divided into reasonable HUB-sized portions | §20.285(d)(1) | `hsp-good-faith-effort.md` §2 + `hsp-supplemental-form.md` §5 |
| Written notice to representative sample of HUB subs | §20.285(d)(2) | `hsp-cmbl-vendor-outreach-log.md` |
| Advertised in HUB-targeted publications | §20.285(d)(2) | `hsp-good-faith-effort.md` §4 |
| Attended HUB outreach events | §20.285(d)(3) | `hsp-good-faith-effort.md` §5.2 |
| Contacted HUB Discretionary Contracting Forum / agency HUB Operations | §20.285(d)(5) | `hsp-good-faith-effort.md` §7 |
| Evaluated HUB responses on capability + price using same criteria as non-HUB | §20.285(d)(4) | `hsp-good-faith-effort.md` §6 |

## Section 8 — Post-Award Commitments

By submitting this HSP, BPC commits to:

1. File a **Progress Assessment Report (PAR)** on the cadence the contract specifies (typically monthly with each pay app, on the agency-required form — template at [`hsp-progress-assessment-report-template.md`](hsp-progress-assessment-report-template.md)).
2. **Notify the agency HUB Operations office in writing** of any sub substitution before the substitution takes effect.
3. **Continue Good-Faith Effort** if actual HUB participation falls short of the HSP commitment, including (a) revised HSP submission with agency concurrence, or (b) documented continuing GFE per the PAR shortfall narrative section.
4. **Retain HSP records** (outreach log, GFE evidence, PAR submissions, sub agreements, lien waivers) for the duration of the contract + 3 years per 34 TAC §20.285(g).
5. **Make HSP records available** to agency HUB Operations and TX Comptroller HUB Program Office on request.

## Section 9 — Affirmation + Signature

The respondent affirms:

- The information in this HSP is true and correct to the best of the respondent's knowledge.
- The HUB-certified subs listed in Section 6 hold current TX HUB certificates as of the date of this HSP.
- The respondent will perform Good-Faith Effort throughout the period of performance.
- The respondent understands that material misrepresentation in this HSP may render the proposal non-responsive and may subject the respondent to sanctions under 34 TAC §20.288.

```
[USER TO FILL — HSP signer name]
[USER TO FILL — HSP signer title]
Blue Print Constructs, LLC dba Blueprint Constructs
TX HUB VID 1874292998900 (verify current renewal)
Signature: ______________________________     Date: {{HSP_SIGN_DATE}}
```
