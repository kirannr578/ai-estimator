# `firm/proposal-library/` — paste-ready proposal sections

This folder is the source of truth for proposal-section content. Each file is paste-ready markdown: open it, copy the section that matches the RFP requirement, paste into the proposal draft, search-and-replace the `{{...}}` placeholders, refine for the specific project.

## Index

### `past-performance/`

Per-project paste-ready writeups, in the format that the source RFP / RFCSP expects. Match the project to the RFP using [`firm/firm-profile.json → past_project_selection_rules`](../firm-profile.json) first — pick the three that fit the bid, not all of them.

| File | Project | Best fit for |
|---|---|---|
| [`past-performance/hindu-temple-southlake.md`](past-performance/hindu-temple-southlake.md) | Hindu Temple of Southlake (institutional renovation) | TAMU System CSP, ASU / TTUS CSP, City CSP, any public-sector institutional renovation |
| [`past-performance/holiday-inn-hall-park.md`](past-performance/holiday-inn-hall-park.md) | Holiday Inn (Hall Park, Frisco) — hospitality renovation | TAMU / TTUS / UT CSP, federal-LPTA commercial-equivalent, City CSP |
| [`past-performance/lavon-rv-park.md`](past-performance/lavon-rv-park.md) | Lavon RV Park — 30-lot ground-up new construction with $1M performance bond | Federal LPTA / construction RFQ (USFWS, USACE, NPS), TX-state ground-up site work, any RFP asking for bondability proof |

### `exec-summary-archetypes/`

Cover-letter / executive-summary archetypes by procurement type.

| File | Procurement type | Source bid mined |
|---|---|---|
| [`exec-summary-archetypes/federal-sba-lpta.md`](exec-summary-archetypes/federal-sba-lpta.md) | Federal SBA RFQ / RFP, LPTA | USFWS San Marcos 140FC126R0017 |
| [`exec-summary-archetypes/texas-state-csp.md`](exec-summary-archetypes/texas-state-csp.md) | Texas state CSP / RFCSP with HSP | TAMU Harrington 2025-06813, ASU Carr EFA 26-007 |

### `key-personnel/`

One file per BPC key-personnel role — paste-ready bio block. Trim to whichever roles the RFP requires.

| File | Role |
|---|---|
| [`key-personnel/principal-in-charge.md`](key-personnel/principal-in-charge.md) | Principal in Charge / Founder |
| [`key-personnel/project-executive.md`](key-personnel/project-executive.md) | Project Executive |
| [`key-personnel/project-manager.md`](key-personnel/project-manager.md) | Project Manager |
| [`key-personnel/superintendent.md`](key-personnel/superintendent.md) | Superintendent |
| [`key-personnel/safety-officer.md`](key-personnel/safety-officer.md) | Safety Officer / Site Safety Lead |
| [`key-personnel/qa-qc-lead.md`](key-personnel/qa-qc-lead.md) | QA/QC Lead |

### `boilerplate/`

Reusable management-plan one-pagers — for proposal narrative sections or as submittal stubs post-award.

| File | Use |
|---|---|
| [`boilerplate/safety-plan-one-pager.md`](boilerplate/safety-plan-one-pager.md) | Site-specific safety plan (proposal + post-award submittal under FAR 52.236-13) |
| [`boilerplate/qa-qc-plan-one-pager.md`](boilerplate/qa-qc-plan-one-pager.md) | 3-phase QC plan (proposal + post-award submittal) |
| [`boilerplate/communication-plan.md`](boilerplate/communication-plan.md) | PM communication cadence + escalation matrix |
| [`boilerplate/schedule-narrative-skeleton.md`](boilerplate/schedule-narrative-skeleton.md) | Narrative companion to CPM Gantt |
| [`boilerplate/subcontractor-management.md`](boilerplate/subcontractor-management.md) | Sub procurement + management + HSP narrative |
| [`boilerplate/closeout-plan.md`](boilerplate/closeout-plan.md) | Project closeout — punch, O&M, training, warranty |

## How to use

1. Read the matching playbook in [`firm/playbooks/`](../playbooks/README.md) and identify which proposal sections the RFP requires.
2. For each required section, copy the matching file from this folder into the proposal draft (typically `bids/<slug>/09-proposal-draft.md` or `bids/<slug>/proposal/<section>.md`).
3. Search-and-replace `{{...}}` placeholders against the project-specific RFP.
4. **Trim aggressively** — don't paste a section unless the RFP explicitly requests it. On LPTA, every paragraph not requested is an opportunity to introduce an unintended exception.
5. Cite past-performance projects per `firm-profile.json → past_project_selection_rules` — don't blanket-include all of them.

## Placeholder convention

Same as the rest of the capability library: `{{UPPER_SNAKE}}` for project-specific facts, `[USER TO FILL]` for firm-internal data not in `firm-profile.json`, `[TEMPLATE]` for structural skeletons.

## Firm-data flags to keep in mind

These come from [`firm-profile.json → key_personnel_notes`](../firm-profile.json) and [`missing_data_flags`](../firm-profile.json):

- **Only the Principal in Charge (Rocky Nudurupati) has a fully-documented bio.** All other key-personnel files are skeletons with `[USER TO FILL]` for name, credentials, project history. **Do not submit a proposal that names a fictitious person.**
- **Past-performance reference contacts are `[USER TO FILL]`** on Hindu Temple, Holiday Inn, and Lavon RV Park — confirm a live POC who will pick up the phone before submitting.
- **EMR and OSHA safety statistics are not on file.** Until provided, leave safety-plan numerics as `[USER TO FILL]`.
- **TX HUB cert renewed 2026-05-30 per user confirmation** (prior cycle expired 2024-08-31 per source). New expiration date pending user confirmation — capture before any HSP that claims a specific TX HUB expiration in Section 1.
- **Insurance COIs may be stale** (last documented GL policy expired 2024-09-25). Pull current COI from the agent before any submission that requires it.

---

## v2 — Federal Volumes + HSP + PPQ + Capability Statement

The v1 sections above (`past-performance/`, `exec-summary-archetypes/`, `key-personnel/`, `boilerplate/`) cover **section-level** content that gets pasted into proposal volumes. v2 adds **volume-level** scaffolding for federal best-value tradeoff RFPs, plus the supporting compliance / outreach / positioning artifacts those bids require.

### `federal-volumes/`

Standard 4-volume federal RFP response templates aligned with FAR 15.305 (source selection) and FAR 15.101-1 (best-value tradeoff). Use these for **federal best-value tradeoff** RFPs only — for federal LPTA, use [`exec-summary-archetypes/federal-sba-lpta.md`](exec-summary-archetypes/federal-sba-lpta.md) instead.

| File | Purpose |
|---|---|
| [`federal-volumes/README.md`](federal-volumes/README.md) | Sub-library index + the 4-volume model + when-to-use guidance |
| [`federal-volumes/volume-i-technical-approach.md`](federal-volumes/volume-i-technical-approach.md) | Volume I — Technical Approach (8–12 page narrative: project understanding, technical approach, WBS, schedule, QC, safety, sub-management, risks, assumptions) |
| [`federal-volumes/volume-ii-management-approach.md`](federal-volumes/volume-ii-management-approach.md) | Volume II — Management Approach (5–8 pages: corporate org, project-team org chart, key personnel, reporting, communications, change management, escalation, contingency) |
| [`federal-volumes/volume-iii-past-performance.md`](federal-volumes/volume-iii-past-performance.md) | Volume III — Past Performance (3–5 pages: corporate summary, project writeups, PPQ coordination, relevance matrix, CPARS / PPIRS, adverse-information disclosure) |
| [`federal-volumes/volume-iv-price-proposal.md`](federal-volumes/volume-iv-price-proposal.md) | Volume IV — Price Proposal (2–4 pages + Schedule of Prices: CLIN/SLIN breakdown, basis of estimate, indirect-cost buildup, payment milestones, cross-references) |

Companion playbook (capture / proposal-strategy guidance): [`firm/playbooks/federal-rfp-best-value-tradeoff.md`](../playbooks/federal-rfp-best-value-tradeoff.md).

### `hsp/`

TX HUB Subcontracting Plan starter — required on TX state-funded contracts > $100K with subcontracting opportunities (Tex. Gov't Code Ch. 2161 + 34 TAC §20.284). Aligned with TX Comptroller CPA Form 2177 conventions.

| File | Purpose |
|---|---|
| [`hsp/README.md`](hsp/README.md) | Sub-library index + 34 TAC §20.284 goals + CPA form references + BPC HUB-status flags |
| [`hsp/hsp-good-faith-effort.md`](hsp/hsp-good-faith-effort.md) | GFE narrative — scope analysis, CMBL outreach methodology, advertisement, notification, response evaluation (per 34 TAC §20.285) |
| [`hsp/hsp-cmbl-vendor-outreach-log.md`](hsp/hsp-cmbl-vendor-outreach-log.md) | Outreach log table — per-vendor evidence supporting the GFE narrative |
| [`hsp/hsp-progress-assessment-report-template.md`](hsp/hsp-progress-assessment-report-template.md) | Post-award PAR — monthly / quarterly progress against HSP commitment (per 34 TAC §20.286) |
| [`hsp/hsp-supplemental-form.md`](hsp/hsp-supplemental-form.md) | Supplemental HSP form aligning with CPA Form 2177 fields — fallback when agency provides no form |

Companion playbook: [`firm/playbooks/texas-state-csp-hsp.md`](../playbooks/texas-state-csp-hsp.md). Per-bid HSP plan: [`bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md`](../../bids/_TEMPLATES/texas-state-csp-hsp/05-hsp-plan.md).

### `ppq/`

Federal Past-Performance Questionnaire collection — for the Confidence Assessment under FAR 15.305(a)(2)(i) on federal best-value tradeoff RFPs.

| File | Purpose |
|---|---|
| [`ppq/README.md`](ppq/README.md) | Sub-library index + PPQ workflow (Day 0 / Day 7 / Day 14 / Day 21 cadence) |
| [`ppq/ppq-cover-letter-to-client.md`](ppq/ppq-cover-letter-to-client.md) | Letter from BPC to past client — requests PPQ completion + return directly to federal CO |
| [`ppq/ppq-standard-federal-form.md`](ppq/ppq-standard-federal-form.md) | Generic 12–15 question federal PPQ — fallback when agency does not provide a form |
| [`ppq/ppq-tracking-log.md`](ppq/ppq-tracking-log.md) | Internal BPC tracking log — metadata only (no PPQ content) |

### `capability-statement/`

BPC's federal 1-page capability statement — for sources-sought responses, pre-solicitation outreach, agency capability briefings, SBA Small-Business Specialist interactions.

| File | Purpose |
|---|---|
| [`capability-statement/README.md`](capability-statement/README.md) | Sub-library index + when-to-use guidance + cross-references to firm-profile + compliance |
| [`capability-statement/capability-statement-1pg.md`](capability-statement/capability-statement-1pg.md) | Paste-ready 1-page capability-statement content (corporate identity, NAICS, certs with expiry flags, core competencies, differentiators, 3 representative past-performance bullets, POC) |
| [`capability-statement/capability-statement-design-notes.md`](capability-statement/capability-statement-design-notes.md) | Design / layout guidance — brand colors (BPC Navy `#1B2A4E`, BPC Gold `#C9A87A`), typography (Inter / system sans), 0.5" margins, 10–11pt body, 14–16pt headings, asset references |

### Tradeoff vs LPTA cheat-sheet

| If the federal RFP is... | Use these v2 files | And these v1 files |
|---|---|---|
| **LPTA** (FAR 15.101-2) | `capability-statement/` (for sources-sought before solicitation) | `exec-summary-archetypes/federal-sba-lpta.md`; `past-performance/`; `key-personnel/` (only what RFP requests) |
| **Best-value tradeoff** (FAR 15.101-1) | `federal-volumes/` (all four); `ppq/` (for Volume III); `capability-statement/` (for sources-sought) | `past-performance/`; `key-personnel/`; `boilerplate/` (safety, QC, communications, schedule, sub-management, closeout — cross-referenced from Volumes I and II) |
| **TX state CSP / RFCSP** | `hsp/` (HSP form + GFE + outreach log + post-award PAR); `capability-statement/` (for agency outreach) | `exec-summary-archetypes/texas-state-csp.md`; `past-performance/`; `key-personnel/`; `boilerplate/` |
