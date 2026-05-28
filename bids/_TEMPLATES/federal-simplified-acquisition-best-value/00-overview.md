# {{PROJECT_NAME}} — Overview

> **Source playbook:** [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../../firm/playbooks/federal-simplified-acquisition-best-value.md)
>
> **Template archetype:** Federal **Simplified Acquisition (FAR Part 13, often + Part 12 commercial-item), best-value comparative trade-off** across price + technical capability + prior experience. Quote on **SF-18** (or SF-1449 if commercial-item under FAR 13.500), NOT SF-1442. **NOT LPTA** — see playbook §1 decision matrix to confirm fit before pricing.

## Solicitation identity

| Field | Value |
|---|---|
| Solicitation # | `{{SOLICITATION_NUMBER}}` |
| Project name | `{{PROJECT_NAME}}` |
| Agency | `{{AGENCY}}` ({{AGENCY_SHORT}}) |
| Issuing office | `{{ISSUING_OFFICE}}`, `{{ISSUING_OFFICE_ADDRESS}}` |
| Solicitation form | **SF-18 RFQ** (or SF-1449 if commercial-item under FAR 13.500 — verify on RFQ cover page; NOT SF-1442) |
| Contract type | `{{CONTRACT_TYPE}}` (typ Firm-Fixed-Price per FAR 52.216-1) |
| Acquisition method | `Simplified Acquisition Procedures` (FAR Part 13, typically in conjunction with FAR Part 12) |
| Set-aside | `{{SET_ASIDE}}` (typ 100% Small Business per FAR 52.219-6) |
| Evaluation method | **Best Value — comparative trade-off across price + technical capability + prior experience** (per RFQ Section M or SAP-equivalent "Basis for Award"); often **evaluated in groups of 3 lowest priced quotes**; NOT LPTA |
| Primary NAICS | `{{NAICS_CODE}}` (typ 236220 Commercial + Institutional Building Construction) |
| Size standard | $`{{SIZE_STANDARD_USD}}M` (236220 current = $45.0M 3-yr avg revenue) |
| Magnitude | `{{MAGNITUDE_BAND}}` — `[USER TO FILL — SAP RFQs often DO NOT state a magnitude; if absent, use "magnitude unstated; sub-SAT cap = $250K per FAR 13.003 (civilian) or $7.5M per FAR 13.500 (commercial-item)"]` |
| Period of performance | `{{POP_DAYS}}` calendar days from NTP |
| Wage determination | `{{WD_NUMBER}}` effective `{{WD_DATE}}` (Davis-Bacon Act, per RFQ attachment) — applies regardless of SAT/SAP status if construction labor on site |

## Project location + site visit

| Field | Value |
|---|---|
| Site address | `{{SITE_ADDRESS}}` |
| Site city / state / ZIP | `{{SITE_CITY_STATE_ZIP}}` |
| County | `{{COUNTY}}` |
| Site visit date | `{{SITE_VISIT_DATE}}` |
| Site visit POC | `{{SITE_POC_NAME}}` — `{{SITE_POC_EMAIL}}` — `{{SITE_POC_PHONE}}` |
| Site visit RSVP method | `{{SITE_VISIT_RSVP_METHOD}}` |
| Special site-access notes | `[USER TO FILL — backcountry / boat / 4WD / helicopter / secured-facility access notes if applicable; per-diem zone if remote]` |

## Key dates

| Milestone | Date |
|---|---|
| RFQ release | `{{RFP_RELEASE_DATE}}` |
| Site visit | `{{SITE_VISIT_DATE}}` |
| RFI cutoff | `{{RFI_CUTOFF_DATE}}` |
| Quote due | `{{DUE_DATE}}` @ `{{DUE_TIME}}` `{{DUE_TIMEZONE}}` |
| Acceptance period | `{{ACCEPTANCE_PERIOD_DAYS}}` calendar days from quote receipt (typ 60 on SAP) |
| Anticipated award | `{{AWARD_TARGET_DATE}}` (SAP typically awards within 30–45 days of close) |
| NTP target | `{{NTP_TARGET_DATE}}` |
| Substantial completion target | NTP + `{{POP_DAYS}}` cal days |

## Scope summary (1–3 sentences)

`{{SCOPE_SUMMARY}}` — `[USER TO FILL — pull from RFQ Section C / SOW first paragraph. Brief but specific enough to anchor the technical-capability narrative.]`

## Contacts (agency-side)

| Role | Name | Email | Phone |
|---|---|---|---|
| Contracting Officer (CO) | `{{CO_NAME}}` | `{{CO_EMAIL}}` | `{{CO_PHONE}}` |
| Contract Specialist (CS) | `{{CS_NAME}}` | `{{CS_EMAIL}}` | `{{CS_PHONE}}` |
| Site / project POC | `{{SITE_POC_NAME}}` | `{{SITE_POC_EMAIL}}` | `{{SITE_POC_PHONE}}` |
| `[any additional POC named in the RFQ]` | | | |

## Submission

| Item | Value |
|---|---|
| Submission portal | `{{SUBMISSION_PORTAL}}` (often **email only** on SAP; SAM.gov / PIEE less common at this scale) |
| Submission email(s) | `{{SUBMISSION_EMAIL_1}}`; `{{SUBMISSION_EMAIL_2}}` (CC CO if a CC line is published) |
| File naming | Single combined PDF: `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - QUOTE PACKAGE.pdf` (split + number "email N of M" in subject if > 25 MB) |
| Email subject | Per RFQ Section L — typically `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - email N of M` (use exact format the RFQ states) |
| Email size limit | `{{EMAIL_SIZE_LIMIT_MB}}` MB total (25 MB common on agency tenants) |
| Send-by-buffer | Submit 30+ minutes before cutoff |

## Quote package contents (per RFQ Section L)

This is a SAP quote package — **not** a multi-volume proposal. Assemble as a single PDF in this order (refine against the RFQ's published checklist):

1. Section L checklist (if RFQ provides one) — completed as **first page** of package
2. **Signed SF-18** (or SF-1449 if commercial-item)
3. **Signed amendments** (SF-30 for each amendment posted before close)
4. Completed **Section K / 52.212-3** Reps & Certs as applicable (or SAM 52.204-8(d) incorporation page)
5. **Section B Price Schedule** — every CLIN priced; pricing rounded per Section L; total cited
6. **Technical Capability narrative** — proposed schedule + approach demonstrating thorough understanding of the SOW (typ 5–15 pp)
7. **Prior Experience** — 3–5 most-recent (typ ≤ 5 years) similar size+scope projects with owner / value / contact / dates / scope + relevance statement
8. **Key Personnel** — short-form (½-page per named role: PM, Super, QC; add PIC + Safety if RFQ asks)
9. **Buy American Certificate** (FAR 52.225-4) if RFQ triggers FAR 52.225-9 / -11
10. **Surety commitment letter** for post-award P&P (or FAR 52.228-13 Alternative Payment Protections) if RFQ requires
11. **"or-equal" product literature** if quoting a substitute for any specified product
12. **Contractor Core Data block** (company name, CAGE, UEI, POC, POC email/phone)

## Bid posture (BPC quick read)

| Question | Answer |
|---|---|
| BPC eligible (small + correct NAICS)? | ✅ — NAICS 236220 small ≤ $45M |
| SAM.gov current? | ⚠️ Verify expiration before pricing — see [`firm/compliance/README.md`](../../../firm/compliance/README.md) |
| Insurance current? | 🔴 / ⚠️ — pull current COIs; verify limits against the RFQ-cited agency clause (often LOWER than the LPTA $1M/$2M baseline — e.g. DOI 1452.228-70 is $100K/$500K/$500K) |
| Bondable at this magnitude? | ✅ — $1M single-project floor covers civilian SAP band ($50K–$250K) easily; commercial-item SAP at the $7.5M cap requires surety capacity confirmation |
| Bid bond required at submission? | `[USER TO FILL — verify Section I; SAP often DOES NOT require SF-24, using FAR 52.228-13 Alternative Payment Protections instead]` |
| Past-perf fit (3–5 references)? | ✅ — Lavon RV Park + Hindu Temple + Holiday Inn per [`firm/firm-profile.json → past_project_selection_rules`](../../../firm/firm-profile.json); pull 2 more if RFQ asks for 5 |
| Magnitude vs BPC's typical bid? | `[USER TO FILL — SAP magnitude often unstated; size against scope + last-3-job actuals]` |
| Geographic fit | `[USER TO FILL — drive time from Frisco / Little Elm to site + per-diem implications for the POP]` |
| Special hazards (lab, abatement, secure facility, remote / backcountry) | `[USER TO FILL — call out anything that demands a non-baseline sub or extra GC time]` |
| Go / No-go recommendation | `[USER TO FILL after pre-bid analysis]` |

## Cross-references

- Playbook: [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../../firm/playbooks/federal-simplified-acquisition-best-value.md)
- Sibling LPTA playbook (for comparison): [`firm/playbooks/federal-sba-rfq-lpta.md`](../../../firm/playbooks/federal-sba-rfq-lpta.md)
- Sibling full FAR 15 best-value playbook (for comparison): [`firm/playbooks/federal-rfp-best-value-tradeoff.md`](../../../firm/playbooks/federal-rfp-best-value-tradeoff.md)
- Compliance check: [`firm/compliance/README.md`](../../../firm/compliance/README.md)
- Scope template starter: pick one of [`firm/scope-templates/`](../../../firm/scope-templates/README.md) that matches the SOW
- Proposal-library: [`firm/proposal-library/`](../../../firm/proposal-library/README.md)
