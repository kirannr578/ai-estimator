# `bids/_TEMPLATES/` — workspace skeletons for new bid opportunities

When a new RFP lands, copy the matching workspace template into `bids/<new-slug>/` and refine. Each template mirrors the structure of a shipped BPC bid workspace, parameterized with `{{...}}` placeholders.

## Templates

| Template | Procurement type | Mirrors structure of |
|---|---|---|
| [`federal-sba-rfq-lpta/`](federal-sba-rfq-lpta/) | Federal SBA RFQ / RFP, LPTA | [`bids/usfws-san-marcos-140FC126R0017/`](../usfws-san-marcos-140FC126R0017/) |
| [`texas-state-csp-hsp/`](texas-state-csp-hsp/) | Texas State CSP / RFCSP with HUB Subcontracting Plan | [`bids/tamu-harrington-2025-06813/`](../tamu-harrington-2025-06813/) + [`bids/angelo-state-carr-efa-26-007/`](../angelo-state-carr-efa-26-007/) (common denominator) |

## How to instantiate a template

### Step 1 — Pick the matching template

Read the matching playbook in [`firm/playbooks/`](../../firm/playbooks/README.md) to confirm the procurement archetype matches.

### Step 2 — Copy + rename

PowerShell (Windows):

```powershell
$src = "bids\_TEMPLATES\federal-sba-rfq-lpta"      # or "texas-state-csp-hsp"
$slug = "<new-slug>"                                # e.g. "usace-fort-bliss-12345"
Copy-Item -Path $src -Destination "bids\$slug" -Recurse
```

Slug convention: `<agency-short>-<short-project-name>-<solicitation-number>` in kebab-case, e.g. `usfws-san-marcos-140FC126R0017` or `tamu-harrington-2025-06813`.

### Step 3 — Global search-and-replace

The template uses `{{UPPER_SNAKE}}` for project-specific facts. Walk the new workspace and search-and-replace each `{{...}}` token against the RFP.

Master placeholder vocabulary: [`firm/playbooks/README.md → Master placeholder vocabulary`](../../firm/playbooks/README.md).

### Step 4 — Run the firm-profile applier

```powershell
.\.venv\Scripts\python.exe firm\_scripts\apply_firm_profile.py
```

Idempotent. Substitutes firm-profile JSON values (firm legal name, UEI, CAGE, NAICS, addresses, etc.) into every `.md` / `.json` file in `bids/<new-slug>/`. Re-run after editing `firm-profile.json`.

### Step 5 — Triage remaining placeholders

```powershell
.\.venv\Scripts\python.exe firm\_scripts\scan_placeholders.py
```

Generates a report of remaining `[USER TO FILL]` markers. These are firm-internal data points (person names, current EMR, current COIs) that need human input before submission.

### Step 6 — Pull scope + proposal-library content

- Pull scope template(s) from [`firm/scope-templates/`](../../firm/scope-templates/README.md) into the new workspace's `04-scope-of-work.md` / `06-scope-outline.md`.
- Pull matching proposal-library content from [`firm/proposal-library/`](../../firm/proposal-library/README.md) into the new workspace's `09-proposal-draft.md` (federal) or `proposal/` sub-folder (state CSP).

### Step 7 — Confirm compliance posture

Read [`firm/compliance/README.md`](../../firm/compliance/README.md) — if any 🔴 item blocks this bid, **stop and fix it** before any estimator hours are sunk. Most fixes have 3–10 business-day turnaround; a stale cert disqualifies the bid on its face.

## Placeholder convention

Same as the rest of the capability library:

- `{{UPPER_SNAKE}}` — project-specific fact, search-and-replace per bid
- `[USER TO FILL: <short description>]` — firm-internal data not in `firm-profile.json`
- `[TEMPLATE]` — structural skeleton not yet refined by a shipped bid

For factual fields populated from `firm/firm-profile.json` (firm legal name, UEI, CAGE, NAICS, etc.), the template carries the literal value — these are NOT placeholders. `firm/_scripts/apply_firm_profile.py` keeps them in sync if the profile is updated.

## File layout

Each template folder contains the same files (filenames mirror the shipped bid structure):

```
<template>/
  README.md                       ← per-template usage notes (TBD as templates mature)
  00-overview.md                  (or 01-overview.md for state CSP)
  01-scope.md                     (or 04-scope-of-work.md for state CSP)
  02-deliverables.md
  03-missing-documents.md
  04-checklist.md                 (or 02-bid-prep-checklist.md for state CSP)
  05-bid-form-prep.md             (federal: SF 1442/1449 fields)
  06-scope-outline.md
  07-risk-register.md
  08-pricing-strategy.md
  09-proposal-draft.md
  contacts.md
  timeline.md
  takeoff-template.json
  price-sheet-skeleton.json
  outreach/
    email-template.md
```

The TX-state-CSP-HSP template additionally includes:

```
  05-hsp-plan.md                  ← HUB Subcontracting Plan
  hsp-gfe-checklist.md
  csp-scoring-matrix.md
  tx-prevailing-wage-checklist.md
```

The federal-SBA-LPTA template additionally includes:

```
  08-far-clauses-flags.md         ← FAR-clause review per RFP
```

## Conventions

- **Files numbered 00–09 vs 01–09:** federal templates start at `00-overview.md` (mirrors USFWS); state templates start at `01-overview.md` (mirrors TAMU + ASU). Both work; respect whichever the template uses to keep diff-readability against the source bid.
- **Markdown only at the top level of each `bids/<slug>/`** — keep PDFs, drawings, and other binaries in `bids/<slug>/source-pdfs/` (gitignored if large, per repo convention).
- **`outreach/`** holds email drafts to the agency (pre-bid Q&A, site-visit RSVP, RFI submissions). One file per outbound thread; subject in the filename.
- **`proposal/`** (state CSP) holds per-section proposal drafts. Each section gets its own file: `01-executive-summary.md`, `02-technical-approach.md`, etc.
