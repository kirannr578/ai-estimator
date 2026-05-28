# HSP — Good-Faith Effort Narrative

> **How to use this template** — Companion narrative to the agency-provided HSP form (typically CPA Form 2177 or an agency-specific equivalent). Required under 34 TAC §20.285 whenever BPC's HSP commitment does not meet the applicable goal in 34 TAC §20.284, **and recommended even when the commitment meets the goal** — the GFE narrative protects against post-submission challenges and against post-award shortfall. Pair with [`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md) (the outreach log is the underlying evidence; this narrative is the cover story). Search-and-replace every `{{PLACEHOLDER}}`.

---

# Good-Faith Effort Narrative — {{PROJECT_NAME}}
## {{SOLICITATION_TYPE}} {{SOLICITATION_NUMBER}} | {{AGENCY}}
### Submitted by Blue Print Constructs (Blue Print Constructs, LLC dba) — TX HUB VID `1874292998900` (status: confirm current renewal per `firm/compliance/README.md`)

## 1. Applicable HUB goal

| Field | Value |
|---|---|
| Applicable HUB goal source | 34 TAC §20.284 (statewide) `[OR]` project-specific override per RFP §`{{HUB_GOAL_RFP_REF}}` |
| Applicable category | `{{APPLICABLE_HUB_GOAL_LABEL}}` (heavy / building / special-trade / professional / other-services / commodities) |
| Statewide goal | `{{STATEWIDE_HUB_GOAL_PCT}}%` |
| Project-specific override (if any) | `{{HUB_GOAL_PCT}}%` |
| **BPC's HSP commitment on this project** | **`{{HUB_COMMIT_PCT}}%`** of subcontracted Work |
| Goal-met determination | `{{GOAL_MET_YES_NO}}` |

## 2. Scope analysis for subcontracting opportunities

Per 34 TAC §20.285(d)(1), BPC has divided the scope of `{{PROJECT_NAME}}` into reasonable sub-portions to facilitate HUB participation. The analysis below identifies each definable feature of the work and assigns it to **Self-perform** or **Subcontract** plan.

### 2.1 Per-CSI-division scope plan

| CSI Division | Scope description | Plan | % of contract | Subcontracting opportunity (HUB target) |
|---|---|---|---|---|
| 01 — General Requirements | Mob, super, GR, dumpster, temp protection, OSHA program, QC plan, daily reports | **Self** | `{{DIV_01_PCT}}%` | n/a (excluded from HUB denominator) |
| 02 — Existing Conditions | Selective demo, pre-demo investigation | **Sub** | `{{DIV_02_PCT}}%` | Demolition: 100% HUB target |
| 03 — Concrete | `{{DIV_03_DESCRIPTION}}` | `{{DIV_03_PLAN}}` | `{{DIV_03_PCT}}%` | `{{DIV_03_HUB_TARGET}}` |
| 04 — Masonry | `{{DIV_04_DESCRIPTION}}` | `{{DIV_04_PLAN}}` | `{{DIV_04_PCT}}%` | `{{DIV_04_HUB_TARGET}}` |
| 05 — Metals | `{{DIV_05_DESCRIPTION}}` | `{{DIV_05_PLAN}}` | `{{DIV_05_PCT}}%` | `{{DIV_05_HUB_TARGET}}` |
| 06 — Wood, Plastics, Composites | Casework + millwork; trim self-perform | **Sub (casework) + Self (trim)** | `{{DIV_06_PCT}}%` | Casework: 25% HUB target |
| 07 — Thermal & Moisture | Roofing, sealants | `{{DIV_07_PLAN}}` | `{{DIV_07_PCT}}%` | `{{DIV_07_HUB_TARGET}}` |
| 08 — Openings | Doors, frames, hardware, glazing | **Sub** | `{{DIV_08_PCT}}%` | per-sub HUB target |
| 09 — Finishes | Drywall, paint, flooring, ceilings, tile | **Mostly Self + selective Sub** | `{{DIV_09_PCT}}%` | Drywall sub: 50% HUB; ceilings sub: 50% HUB; flooring sub: 50% HUB; tile sub: 25% HUB |
| 10 — Specialties | Toilet partitions, signage, accessories | **Sub** | `{{DIV_10_PCT}}%` | varies per sub |
| 11 — Equipment | `{{DIV_11_DESCRIPTION}}` | `{{DIV_11_PLAN}}` | `{{DIV_11_PCT}}%` | `{{DIV_11_HUB_TARGET}}` |
| 21–23 — Fire / Plumbing / HVAC | Wet + dry MEP | **Sub** | `{{MEP_PCT}}%` | Plumbing: 50% HUB; HVAC: 25% HUB; Fire: 25% HUB |
| 26 — Electrical | Power, lighting, low-voltage | **Sub** | `{{DIV_26_PCT}}%` | 50% HUB target |
| 31–33 — Site / Utilities | `{{DIV_31_DESCRIPTION}}` | `{{DIV_31_PLAN}}` | `{{DIV_31_PCT}}%` | `{{DIV_31_HUB_TARGET}}` |
| **Self-perform total (excluded from HUB denominator)** | | | `{{SELF_PERFORM_PCT}}%` | n/a |
| **Subcontracted total (HUB denominator)** | | | `{{SUB_TOTAL_PCT}}%` | `{{HUB_COMMIT_PCT}}%` of this base |

### 2.2 Self-perform justification

BPC will self-perform `{{SELF_PERFORM_PCT}}%` of the contract value — `{{SELF_PERFORM_SCOPE_DESCRIPTION}}`. The HUB goal in 34 TAC §20.284 applies to the **subcontracted portion only**; self-perform $ is excluded from the HUB denominator.

Justification for self-performing this scope:

- `{{REASON_1}}` (e.g. "GC supervision must be by prime per agency-managed contract")
- `{{REASON_2}}` (e.g. "Selective demo is small-tonnage and within BPC's standard self-perform capability")
- `{{REASON_3}}` (e.g. "Punch list + closeout require the GC's documentation discipline and cannot reasonably be subcontracted")

## 3. HUB vendor outreach methodology

Per 34 TAC §20.285(d)(2)–(d)(3), BPC has identified and notified a representative sample of HUB-certified vendors for each subcontracting opportunity above. Outreach methodology:

### 3.1 Source — TX CMBL HUB Search

For each trade, BPC ran the **TX Comptroller CMBL HUB Search** at <https://comptroller.texas.gov/purchasing/vendor/hub/search.php> on `{{CMBL_SEARCH_DATE}}`, filtering by:

- **HUB-certified** status active
- **NIGP class / NAICS code** matching the trade (e.g. NAICS 238210 for electrical, NAICS 238220 for plumbing/HVAC)
- **County** = `{{COUNTY}}` County, plus adjacent counties; statewide for specialty trades with thin local pool

Search results saved as evidence at `{{CMBL_SEARCH_EVIDENCE_FILE}}` (per-trade CSV exports).

### 3.2 Minimum vendor outreach count

For each trade, BPC contacted **at least 3 HUB-certified vendors** (target ≥ 5) per the standard "good-faith effort" benchmark. Total HUB vendor contacts on this solicitation: **`{{TOTAL_HUB_OUTREACH_COUNT}}`**.

### 3.3 Solicitation packet sent to each HUB vendor

Each contacted HUB vendor received the following package via email at least **`{{NOTICE_DAYS_BEFORE_BID}}` working days** before bid submission (per 34 TAC §20.285 minimum notice):

- Project name + solicitation number + agency
- Scope summary specific to the trade
- Bid due date + time + timezone
- Plans / specs link or attached drawings
- Required certifications, insurance, bonding flow-down per the contract
- BPC point-of-contact (name, email, direct phone)
- Site-visit / pre-bid-meeting information if applicable

The standard solicitation email template is at `{{SOLICITATION_EMAIL_TEMPLATE_REF}}`.

## 4. Advertisement requirement

Per 34 TAC §20.285(d)(2), BPC has advertised the subcontracting opportunity in **at least three publications** that target Texas HUB vendors. Advertisement evidence:

| Publication | Type | Run date(s) | Evidence file |
|---|---|---|---|
| `{{AD_PUB_1}}` (e.g. agency HUB office bulletin) | `{{AD_TYPE_1}}` | `{{AD_DATE_1}}` | `{{AD_EVIDENCE_FILE_1}}` |
| `{{AD_PUB_2}}` (e.g. TX Comptroller HUB Operations newsletter) | `{{AD_TYPE_2}}` | `{{AD_DATE_2}}` | `{{AD_EVIDENCE_FILE_2}}` |
| `{{AD_PUB_3}}` (e.g. local minority chamber / regional MSDC bulletin) | `{{AD_TYPE_3}}` | `{{AD_DATE_3}}` | `{{AD_EVIDENCE_FILE_3}}` |

> **Note** — some agencies require the advertisement to run for a minimum number of days (typically 7+) before bid; confirm via Section L and the agency HSP form. The advertisement must include scope summary + BPC contact information + due date.

## 5. Notification + meeting documentation

Per 34 TAC §20.285(d)(3), BPC has documented:

### 5.1 Written notification

Each contacted HUB vendor received written notification (email + courier-receipt or read-receipt) of the subcontracting opportunity. Notification evidence stored in [`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md) (the per-vendor outreach log) plus the underlying email archive at `{{EMAIL_ARCHIVE_REF}}`.

### 5.2 HUB outreach events attended

| Event | Host | Date | Attendee from BPC | Evidence |
|---|---|---|---|---|
| `{{EVENT_1}}` | `{{HOST_1}}` (e.g. `{{AGENCY}}` HUB Operations) | `{{EVENT_DATE_1}}` | `{{ATTENDEE_1}}` | `{{EVENT_EVIDENCE_1}}` |
| `{{EVENT_2}}` (e.g. HUB Discretionary Contracting Forum) | `{{HOST_2}}` | `{{EVENT_DATE_2}}` | `{{ATTENDEE_2}}` | `{{EVENT_EVIDENCE_2}}` |

### 5.3 Pre-bid HUB sub-contractor meeting

BPC `{{HOSTED_OR_NOT}}` a pre-bid meeting specifically for HUB sub candidates on `{{PREBID_MEETING_DATE}}`. Meeting notice + attendance roster: `{{PREBID_MEETING_EVIDENCE}}`.

## 6. Response evaluation methodology

Per 34 TAC §20.285(d)(4), BPC has evaluated responses from HUB vendors using consistent criteria across HUB and non-HUB candidates:

### 6.1 Evaluation criteria (applied uniformly)

1. **Capability + capacity** — verifiable record on the same trade at similar magnitude; current bandwidth to deliver during the project's PoP.
2. **Compliance** — current TX HUB cert (HUB candidates only); insurance + bonding capacity meeting `{{AGENCY}}` requirements; trade license currency; OSHA training; W-9 on file; SAM exclusion check (federal projects).
3. **Past performance with BPC** — prior BPC project record where applicable, or 3 client references for new candidates.
4. **Competitive price** — quote in the bid-due window; pricing within `{{PRICE_BAND_PCT}}%` of low quote per scope.

### 6.2 Disposition of HUB responses

| HUB Vendor | Trade | Response received | Quote $ | Selected (Y/N) | If N, reason |
|---|---|---|---|---|---|
| `{{HUB_VENDOR_1}}` (VID `{{HUB_VID_1}}`) | `{{TRADE_1}}` | `{{RESPONSE_1}}` | $`{{QUOTE_1}}` | `{{SELECTED_1}}` | `{{REASON_1}}` |
| `{{HUB_VENDOR_2}}` (VID `{{HUB_VID_2}}`) | `{{TRADE_2}}` | `{{RESPONSE_2}}` | $`{{QUOTE_2}}` | `{{SELECTED_2}}` | `{{REASON_2}}` |
| `{{HUB_VENDOR_3}}` (VID `{{HUB_VID_3}}`) | `{{TRADE_3}}` | `{{RESPONSE_3}}` | $`{{QUOTE_3}}` | `{{SELECTED_3}}` | `{{REASON_3}}` |

> **Discipline reminder** — a HUB candidate cannot be rejected solely on price unless price exceeds the low non-HUB quote by more than the **`{{PRICE_BAND_PCT}}%`** band BPC applies uniformly. Rejecting only HUB candidates on price grounds while accepting non-HUB candidates outside the band is a GFE failure.

## 7. Contact with HUB Discretionary Contracting Forum / agency HUB Operations

Per 34 TAC §20.285(d)(5), BPC has contacted:

- **`{{AGENCY}}` HUB Operations / HUB Coordinator** — `{{AGENCY_HUB_CONTACT_NAME}}`, `{{AGENCY_HUB_CONTACT_EMAIL}}`, on `{{AGENCY_HUB_CONTACT_DATE}}`. Record: `{{AGENCY_HUB_CONTACT_EVIDENCE}}`.
- **TX Comptroller Statewide HUB Program Office** — request for vendor list / advice on `{{CPA_CONTACT_DATE}}`. Record: `{{CPA_CONTACT_EVIDENCE}}`.

## 8. Summary of GFE compliance against 34 TAC §20.285

| GFE element | Required by 34 TAC §20.285(d) | Evidence file |
|---|---|---|
| Scope divided into reasonable HUB-sized portions | (d)(1) | §2 above + per-trade table |
| Written notice to representative sample of HUB subs | (d)(2) | [`hsp-cmbl-vendor-outreach-log.md`](hsp-cmbl-vendor-outreach-log.md); email archive `{{EMAIL_ARCHIVE_REF}}` |
| Advertised in ≥ 3 HUB-targeted publications | (d)(2) | §4 above |
| Attended HUB outreach events the agency hosted | (d)(3) | §5.2 above |
| Contacted HUB Discretionary Contracting Forum / agency HUB Operations | (d)(5) | §7 above |
| Evaluated responses on capability + price using same criteria as non-HUB | (d)(4) | §6 above |

## 9. Sub-by-sub HSP roster (for the HSP form)

| Vendor | TX HUB VID | Trade / scope | $ value | % of subcontracted Work |
|---|---|---|---|---|
| `{{VENDOR_1}}` | `{{HUB_VID_1}}` | `{{TRADE_1}}` | $`{{VAL_1}}` | `{{PCT_1}}%` |
| `{{VENDOR_2}}` | `{{HUB_VID_2}}` | `{{TRADE_2}}` | $`{{VAL_2}}` | `{{PCT_2}}%` |
| `{{VENDOR_3}}` | `{{HUB_VID_3}}` | `{{TRADE_3}}` | $`{{VAL_3}}` | `{{PCT_3}}%` |
| `{{...}}` | | | | |
| **Total HSP HUB commitment** | | | $`{{HUB_TOTAL_$}}` | **`{{HUB_COMMIT_PCT}}%`** |

## 10. Signature

Submitted by:

```
[USER TO FILL — HSP signer name]
[USER TO FILL — HSP signer title]
Blue Print Constructs, LLC dba Blueprint Constructs
TX HUB VID 1874292998900 (verify current renewal)
Date: {{HSP_SIGN_DATE}}
```
