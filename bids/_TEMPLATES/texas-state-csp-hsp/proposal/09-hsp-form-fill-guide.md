# 09 — HSP (HUB Subcontracting Plan) form fill guide

> **STATUS as of {{PORTAL_PULL_DATE}}: ACTUAL FORM NOW IN HAND, AND IT'S A DIFFERENT FORM THAN ASSUMED.**
>
> The CSP package was pulled from the e-Builder portal on {{PORTAL_PULL_DATE}}. **Section 00 45 17.1** of the project manual (`{{CSP_PACKAGE_PDF_PATH}}` pp. 33–40) is **NOT** the older State of Texas HUB Subcontracting Plan form. It is the **TX State Subcontracting Plan (Rev. 5/26)** which uses the **VetHUB (Veteran Heroes United in Business)** framework — a Texas Comptroller-administered certification for veteran-owned businesses (Tex. Gov't Code Ch. 2161 Subchapter F; 34 TAC §20.285).
>
> **The whole strategy in `../05-hsp-plan.md` was built around the older HUB framework. It will need to be revised against the VetHUB framework.** Initial findings:
>
> - The form is **mandatory for every respondent**, even if the respondent intends to self-perform (in which case only pages 1–2 are completed + Section 3 affirmation).
> - GFE consists of **NIGP-code-based outreach to ≥2 VetHUBs per subcontracting opportunity**, with at least 7 business days for response. Notification template provided in the spec.
> - **HUB / VetHUB cert numbers are tracked by Texas Comptroller VID** (Vendor Identification Number), and certifications are looked up via the comptroller's CMBL (https://commbook.app.cpa.state.tx.us/) using the **VetHUB-only search** and `Active Bidder (A-Approved) VetHUB status` filter.
> - **Action: {{HUB_POC_NAME}}** (`{{HUB_POC_EMAIL}}`, {{HUB_POC_PHONE}}, per CSP §00 21 00 ¶3.3) is the {{AGENCY_SHORT}} HUB-Operations contact for this project — NOT {{HUB_POC_NAME}} as previously assumed from the Notice. Update `outreach/04-email-hub-contact.md` to retarget the corrected HUB POC.
> - **Action: revise `../05-hsp-plan.md`** — replace HUB outreach with VetHUB outreach; refresh CMBL search guidance.
>
> **Action TODAY (post-portal-pull):** start the VetHUB outreach immediately per `../05-hsp-plan.md` § D (with the revised VetHUB filtering). The form structure is in hand; the GFE outreach clock is now the binding constraint.

---

## A. What this form is

The HSP is the document by which the prime contractor commits to a HUB-participation goal on the project and documents the good-faith effort to achieve that goal. Under 34 TAC §20.281–.298:

- Texas state agencies (including {{AGENCY_SHORT}}) require an HSP when subcontracting opportunities exist
- The applicable HUB participation goal varies by procurement class — for renovation work, the **statewide 21.1% goal for "special trade construction"** applies unless {{AGENCY_SHORT}} has set a project-specific higher goal (`[USER TO FILL — confirm with {{HUB_POC_NAME}}]`)
- The HSP commits the prime to either (a) meeting the goal with named HUB subcontractors or (b) documenting a good-faith effort if the goal cannot be met
- The HSP must be submitted **with** the proposal (not after)
- Failure to submit or to document a defensible GFE renders the proposal non-responsive

`[PENDING e-BUILDER ACCESS or {{HUB_POC_NAME}} confirmation: download the actual {{AGENCY_SHORT}} HSP form and re-author this guide section-by-section against the actual fields.]`

---

## B. Cross-reference: existing HSP strategy

The full HSP strategy is in `../05-hsp-plan.md`. Key inputs that feed this form:

- Per-trade subcontracting plan with target HUB allocation (`../05-hsp-plan.md` § C)
- HUB sub outreach plan (CMBL search results, contact log) (`../05-hsp-plan.md` § D)
- GFE documentation (advertising, written notice, HUB-event attendance) (`../05-hsp-plan.md` § E)

This document is the **form-completion guide**, not a restatement of the strategy. Read `../05-hsp-plan.md` first.

---

## C. Anticipated form sections (standard TX HSP shape)

### C-1. Cover page (commitment summary)

| Field | Value to enter |
|---|---|
| Solicitation # | `{{SOLICITATION_NUMBER}}` |
| Project name | `{{PROJECT_NAME}}` |
| Agency | `{{AGENCY}}` (Part 02) |
| Issuing entity | `{{ISSUING_OFFICE}}` |
| Proposer (Prime) | `[FIRM LEGAL NAME]` |
| Prime's TX HUB status | `[USER TO FILL: HUB-certified Y/N; if Y, list cert #]` |
| Total proposal value | `$[USER TO FILL: matches 10-price-proposal.md]` |
| Total self-performed value | `$[USER TO FILL: from 03-project-team.md § H and self-performing justification]` |
| Total subcontracted value | `$[USER TO FILL: total proposal value − self-performed]` |
| HUB goal applicable | `21.1%` (statewide special-trade construction goal per 34 TAC §20.284, current as of 2024 amendment) — `[USER TO FILL: confirm vs project-specific goal from {{HUB_POC_NAME}}]` |
| HUB participation committed | `[USER TO FILL: $ amount and %]` |
| HUB goal met? (Y/N) | `[USER TO FILL]` — if N, full GFE documentation required in §§ C-4, C-5 |

### C-2. Self-performing justification

For each self-performed scope, fill in:

| Scope | Estimated value | Justification |
|---|---|---|
| `[USER TO FILL: e.g. "Project supervision and general conditions"]` | `$[USER TO FILL]` | `[USER TO FILL: "Required to maintain single-point project accountability per our standard project-execution model; not feasible to subcontract."]` |
| `[USER TO FILL: e.g. "Internal carpentry / demo crew" — if applicable]` | `$[USER TO FILL]` | `[USER TO FILL]` |

Self-performed dollars are removed from the denominator before computing the HUB target percentage.

### C-3. Per-trade HUB subcontracting plan

For **every** subcontracted trade, the form requires a named HUB sub OR a documented GFE record.

| Trade | Sub name | TX HUB cert # | HUB cert expiration | Scope description | Estimated $ value | % of total subcontracted |
|---|---|---|---|---|---|---|
| Demolition | `[USER TO FILL]` | `[USER TO FILL]` | `[USER TO FILL — must be current]` | `[USER TO FILL]` | `$[USER TO FILL]` | `[USER TO FILL]` |
| Framing / drywall | `[USER TO FILL]` | | | | | |
| Doors / frames / hardware (if scope) | `[USER TO FILL]` | | | | | |
| Flooring | `[USER TO FILL]` | | | | | |
| Painting | `[USER TO FILL]` | | | | | |
| Acoustical ceilings | `[USER TO FILL]` | | | | | |
| Lab casework | `[USER TO FILL]` | | | | | |
| Electrical (lab-exp) | `[USER TO FILL]` | | | | | |
| HVAC (lab-exp) | `[USER TO FILL]` | | | | | |
| Plumbing (lab-exp) | `[USER TO FILL]` | | | | | |
| Fire suppression | `[USER TO FILL]` | | | | | |
| Lab utility specialty (if scope) | `[USER TO FILL]` | | | | | |
| Low-voltage pathway | `[USER TO FILL]` | | | | | |

**Sum check:** sum of HUB-sub $ values ÷ total subcontracted value = HUB participation %.

### C-4. Good-faith effort documentation (mandatory if HUB goal not met)

For each trade where the HUB goal was not met or where no HUB sub was selected, attach:

1. **CMBL search records** — screenshot of search filtered by HUB-certified + NIGP/NAICS for that trade + {{COUNTY}} County area; dated.
2. **Written outreach log** — per `../05-hsp-plan.md` § D: date, sub name, contact method, response. Per-trade minimum of 3 documented HUB outreaches.
3. **Bid solicitation packet** — the exact packet sent to HUB subs for that trade (project name, scope, due date, contact).
4. **Sub responses** — any quotes received; reasons for non-selection (price, schedule, qualification).
5. **Non-response evidence** — for HUB subs that did not respond, the outreach log itself is the evidence.
6. **Advertisement in 2+ HUB publications** — copies of the ad; publication name; date of publication; circulation.
7. **HUB outreach event attendance** — sign-in sheet / event registration confirmation for any HUB-targeted event attended.

### C-5. Per-trade GFE narrative

For each trade where no HUB sub was selected, a 2–4 sentence narrative explaining why:

| Trade | Narrative |
|---|---|
| `[Trade]` | `[USER TO FILL — example: "We solicited 5 HUB-certified electrical subcontractors via CMBL search. 2 declined due to scheduling conflicts with existing commitments; 2 did not respond; 1 quoted at a 23% premium over the selected non-HUB sub due to lack of lab-experience pricing. Documented GFE per § C-4."]` |

### C-6. Subcontract administration plan

| Field | Value to enter |
|---|---|
| Monthly Progress Assessment Report (PAR) submitter | `[USER TO FILL — typically Project Manager]` |
| PAR recipient | `{{HUB_POC_NAME}}, {{AGENCY_SHORT}} HUB Operations, {{HUB_POC_EMAIL}}` (per Notice) |
| PAR cadence | Monthly with each pay application (per Notice) |
| HSP change-management procedure | Per 34 TAC §20.285; prime must request {{AGENCY_SHORT}} HUB Operations approval for any HSP modification post-award |

### C-7. Affirmation + signature

| Field | Value to enter |
|---|---|
| Affirmation language | (standard TX HSP affirmation; verify exact text against actual form `[PENDING — {{HUB_POC_NAME}}]`) |
| Authorized signatory | `[USER TO FILL — name + title]` |
| Date | `[USER TO FILL]` |
| Signature | wet ink, blue ink preferred |

---

## D. Pre-submission checklist (HSP-specific)

- [ ] CMBL search records (screenshot per trade, dated)
- [ ] Outreach log (≥3 HUB subs per trade, with dates and methods)
- [ ] Sub-bid solicitation packet (master copy + per-trade copies)
- [ ] HUB-publication advertisement copy (2 publications minimum) — `[USER TO FILL: which publications, dates of publication]`
- [ ] HUB-event attendance records (if any)
- [ ] HUB cert # verification — re-verify on CMBL search within 7 days of submission (expired certs get the HSP kicked back)
- [ ] Form-side math reconciles (HUB $ ÷ subcontracted $ = stated %)
- [ ] HSP signed in wet ink
- [ ] HSP bound with the proposal (typically as a separate, tabbed exhibit)
- [ ] HSP separately delivered to {{HUB_POC_NAME}} if {{AGENCY_SHORT}} requires both Proposal Form delivery and direct HSP delivery `[PENDING — confirm with {{HUB_POC_NAME}}]`
- [ ] Internal 2-person QC pass

---

## E. Common HSP rejection reasons

1. **Expired HUB certifications** for listed subs. Re-verify within 7 days of submission.
2. **HUB sub listed but no contract / scope detail.** Form requires named scope and estimated dollar value, not just "Sub XYZ, electrical."
3. **GFE narrative too thin.** "We tried but no HUB subs responded" is not GFE — must show the outreach log, the CMBL search, the publications.
4. **Math errors.** HUB $ doesn't sum to the stated %; subcontracted $ doesn't reconcile with total $ minus self-performed.
5. **Missing publications.** Both required publications listed in the form must be from the approved TX HUB publication list (see `../05-hsp-plan.md` § E for the list).
6. **Form on wrong template.** {{AGENCY_SHORT}} uses its own header; do not submit on a non-{{AGENCY_SHORT}} template once {{AGENCY_SHORT}}'s is in hand.

---

## F. Workflow when {{AGENCY_SHORT}} HSP form lands

1. Download the actual {{AGENCY_SHORT}} HSP form (from {{HUB_POC_NAME}} or the e-Builder portal).
2. Compare against the State of Texas standard HSP form and the Angelo State Attachment D HSP form. Note any {{AGENCY_SHORT}}-specific additions (commitment-letter format, narrative-length limits, attestation language).
3. Re-author this guide section-by-section against the actual {{AGENCY_SHORT}} form.
4. Populate per the data in `../05-hsp-plan.md` and the live outreach log (`local/hub-outreach-log.csv`).
5. Internal 2-person QC pass.
6. Sign, bind with proposal.
