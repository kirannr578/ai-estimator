# `hsp/` — TX HUB Subcontracting Plan starter

This sub-library is the source of truth for **HUB Subcontracting Plan (HSP)** content used in Texas state-funded construction proposals. The HSP is the single most common cause of TAMU System / TTUS / UT / state-agency bid rejection — not because the rules are obscure, but because compliance is unforgiving and the agency's HUB office reviews HSPs against a checklist before the procurement officer ever scores the technical proposal.

> **Companion playbook:** [`firm/playbooks/texas-state-csp-hsp.md`](../../playbooks/texas-state-csp-hsp.md) — full HSP narrative including 34 TAC §20.284 goals, the GFE four-element rule, post-award PAR mechanics.
>
> **Companion bid template:** [`bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md`](../../../bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md) — per-bid HSP plan workbook (per-trade allocations, sub-by-sub roster).

## When the HSP is required

Per Tex. Gov't Code Ch. 2161 and 34 TAC §20.284, every Texas state agency contract over **$100,000** that has subcontracting opportunities must include an HSP, **unless** the procurement file documents probable subcontracting will not occur. In practice, every TAMU System / TTUS / UT / TX state-agency CSP for construction over $100K requires an HSP — the agency procurement office determines this at solicitation issuance and includes the HSP form in the RFP package.

## TX Comptroller forms referenced

| Form | Purpose | Source |
|---|---|---|
| **CPA Form 2177 (HUB Subcontracting Plan)** | The standard HSP form prescribed by the Texas Comptroller of Public Accounts. Most agencies require this form (or an agency-specific equivalent) | [Texas Comptroller HUB Forms](https://comptroller.texas.gov/purchasing/vendor/hub/forms.php) |
| **CPA Progress Assessment Report (PAR)** | Monthly post-award report — actual sub payments vs HSP commitment | [Texas Comptroller HUB Forms](https://comptroller.texas.gov/purchasing/vendor/hub/forms.php) |
| **Centralized Master Bidder List (CMBL) HUB Search** | Searchable directory of TX-Comptroller-certified HUB vendors by NIGP / NAICS / county | [TX CMBL HUB Search](https://comptroller.texas.gov/purchasing/vendor/hub/search.php) |
| **HUB certification application** | New HUB cert or recertification | [TX HUB Certification](https://comptroller.texas.gov/purchasing/vendor/hub/forms.php) |

> **Note** — agencies frequently issue their own HSP form layered on top of the CPA framework. **Always use the form the RFP attaches** — do not substitute a prior bid's HSP form. Agency-specific examples include TAMU System SSC HSP, ASU FP&C HSP, TTUS HSP.

## Files in this directory

| File | Purpose |
|---|---|
| [`README.md`](README.md) | This index |
| [`hsp-good-faith-effort.md`](hsp-good-faith-effort.md) | GFE narrative template — scope analysis, outreach methodology, advertisement, notification, response evaluation. The narrative the HSP form's "Method B" section requires. |
| [`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md) | Outreach log table — vendor name, CMBL # / VID, scope solicited, contact date / method, response. Required GFE evidence under 34 TAC §20.285. |
| [`hsp-progress-assessment-report-template.md`](hsp-progress-assessment-report-template.md) | Post-award PAR template — monthly / quarterly progress against HSP commitment. |
| [`hsp-supplemental-form.md`](hsp-supplemental-form.md) | Supplemental HSP form aligning with CPA Form 2177 fields — for cases where the agency's HSP form is missing fields the CPA model expects, or for BPC's internal pre-bid HSP draft. |

## How to use

1. Confirm at RFP issuance whether the agency requires HSP (per Section H / Section L) and which form (agency-specific or CPA Form 2177).
2. Read [`firm/playbooks/texas-state-csp-hsp.md`](../../playbooks/texas-state-csp-hsp.md) and [`bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md`](../../../bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md) to size BPC's commitment vs the applicable goal in 34 TAC §20.284.
3. Use the agency-provided HSP form. Cross-reference the GFE narrative ([`hsp-good-faith-effort.md`](hsp-good-faith-effort.md)) and the outreach log ([`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md)) as supplemental attachments.
4. Submit per the RFP's HSP submission deadline (sometimes a separate deadline from the proposal due date).
5. Post-award: file the PAR ([`hsp-progress-assessment-report-template.md`](hsp-progress-assessment-report-template.md)) on the cadence the contract specifies (typically monthly with each pay app or quarterly).

## TX HUB goals (34 TAC §20.284)

| Procurement category | Statewide annual HUB goal |
|---|---|
| Heavy construction, other than building contracts | 11.2% |
| All building construction, including general contractors and operative builders contracts | 21.1% |
| Special-trade construction contracts | 32.7% |
| Professional-services contracts | 23.7% |
| Other-services contracts | 26.0% |
| Commodities contracts | 21.1% |

> **Project-specific override** — agencies sometimes set a project-specific HUB goal that supersedes the statewide percentages, particularly on large building-construction projects with discrete trade-package opportunities. Always confirm via the RFP and via the agency HUB Operations office.

## BPC's TX HUB status (firm-side)

Per [`firm/compliance/README.md`](../../compliance/README.md), BPC's own TX HUB certification (VID 1874292998900) was **renewed 2026-05-30 per user confirmation** (prior cycle expired 2024-08-31 per source). The MBE / SBE certification with DFW MSDC (DL09279) was likewise renewed 2026-05-30 per user; DFW MSDC MBE recognition cascades into TX HUB recognition under the MOU. The new expiration date is pending user confirmation (`[USER TO CONFIRM: new expiration date]`) — capture it before any HSP that claims a specific cert expiration in Section 1.

## Placeholder convention

Same as the rest of the capability library:

- `{{UPPER_SNAKE}}` — project-specific facts pulled from the RFP or set during HSP prep
- `[USER TO FILL]` — firm-internal data not in `firm-profile.json`
- `[TEMPLATE]` — structural skeletons / illustrative examples
