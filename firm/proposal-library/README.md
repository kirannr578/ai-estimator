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
- **TX HUB cert was expired per source.** If the HSP cites BPC as a HUB self-perform contributor, confirm current renewal first.
- **Insurance COIs may be stale** (last documented GL policy expired 2024-09-25). Pull current COI from the agent before any submission that requires it.
