# `firm/` — canonical Blue Print Constructs profile

This directory holds the **single source of truth** for Blue Print Constructs' (BPC) firm-corporate profile. Bid workspaces under `bids/<slug>/` consume it; the BPC OneDrive folder is the upstream binary store.

## What's here

| File | Purpose |
|---|---|
| `firm-profile.json` | Canonical machine-readable record. Edit this first. |
| `firm-profile.md` | Human-readable companion. Derivative of the JSON. |
| `_scripts/extract_sources.py` | One-shot text dump from the BPC OneDrive folder (PDFs, DOCX, XLSX). Outputs land in `_scripts/_extracted/` — not committed. |
| `_scripts/scan_placeholders.py` | Counts `[USER TO FILL]`-style markers across `bids/`. Used to audit how much firm-profile coverage helped. |
| `_scripts/apply_firm_profile.py` | Idempotent replacement script that walks `bids/` and substitutes firm-profile values into every `.md` / `.json` file with placeholders. Re-runnable. |
| `_extracted/` (gitignored under `firm/private/`) | One-shot text dumps from the extraction script. **Should never be committed** — contains raw quoted text from source files, some of which is firm-internal. |
| `private/` (gitignored) | Drop-zone for unredacted source PDFs the user wants locally accessible without committing them. Convention: `firm/private/coi-current.pdf`, `firm/private/bond-letter-current.pdf`, etc. |

## How it's used

1. **Authoring a bid workspace.** When a new bid scaffold lands in `bids/<slug>/`, every `[USER TO FILL: firm legal name]`, `[USER TO FILL: firm address]`, `[USER TO FILL: UEI]`, `[USER TO FILL: bonding agent]`, etc. should be substituted from `firm-profile.json`.
2. **Per-bid substitution pass.** Run:

   ```powershell
   .\.venv\Scripts\python.exe firm\_scripts\apply_firm_profile.py
   ```

   This is **idempotent** — running it twice is safe. It only rewrites placeholders that match the firm-profile mapping. Items with no firm-profile data are rewritten to:

   ```
   [USER TO FILL — not found in BPC firm profile, needs current data]
   ```

   so a human reviewer sees both that we tried and that the firm doesn't have a current value on file. To re-audit, run:

   ```powershell
   .\.venv\Scripts\python.exe firm\_scripts\scan_placeholders.py
   ```

3. **Updating the profile.** Two paths:
   - **Re-extract from source.** Edit a source file in `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\BPC\`, then run `firm/_scripts/extract_sources.py` and re-read the dumps under `firm/_scripts/_extracted/`. The script is a one-shot text dumper, **not** a profile builder — you (or a future agent) will need to hand-update `firm-profile.json` from the dumps. The script writes to `_extracted/`; it does not overwrite `firm-profile.json`.
   - **Hand-edit `firm-profile.json` directly.** When values change between bids (renewed COI limits, current EMR, new bonding agent), just edit the JSON, then re-run `apply_firm_profile.py` against `bids/`. Re-render `firm-profile.md` to keep the human-readable companion in sync.

## Relationship to the OneDrive submission scaffold

OneDrive has its own pre-templated submission package at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\BPC-Submission-Package\` (11 sections, 29 markdown templates, tracking sheet `PLACEHOLDERS-TO-FILL.md`). That scaffold is where the firm produces **typeset bid output**.

This repo's `firm/` holds the **data**; the OneDrive scaffold holds the **presentation templates** that consume the data; the repo's `bids/<slug>/` holds the **per-bid scoping, scope-of-work, outreach, and price-proposal drafts** that connect the two for one specific solicitation.

**The repo does not mirror the OneDrive submission-package binaries** (PDFs, AI files, JPGs, etc.). Canonical artwork stays on OneDrive; the repo points to those files by path.

## PII policy (mirrors the workspace security rules)

The following classes of data are **deliberately excluded** from `firm-profile.json` and `firm-profile.md` even though they appear in BPC source files:

- Bank account / routing numbers
- Portal passwords (TX SOS, DFW MSDC, procurement portals)
- Personal cell phone numbers
- Customer / homeowner SSNs, DOBs, personal addresses
- Row data from `Records/Blue Print Constructs Payments, Contacts, To do List.xlsx` (worksheet/header inventory only)
- Row data from `BPC/Contacts.xlsx` (worksheet/header inventory only)
- Customer names from past-project folders where the customer is an individual homeowner (`1509 Astoria Dr/`, `2056 Zander Dr/`)
- Other corporate entities under the same principal not directly tied to Blue Print Constructs (Maxiple Group LLC, RK Creative Workz LLC, Buds n Petals LLC, etc.)

If a specific bid requires one of these items, paste the value directly into that bid's per-file content (e.g. `bids/<slug>/proposal/01-price-proposal.md`) — do **not** add it to `firm-profile.json`. The firm profile is what gets propagated everywhere; it should stay safe-to-share with future contributors and with bid evaluators if the JSON were ever accidentally shipped.

## Refresh checklist (recommended quarterly + on each cert renewal)

- [ ] Run `firm/_scripts/extract_sources.py` and skim the new dumps for changes vs `firm-profile.json`.
- [ ] Update any expired certs (HUB, MBE, SBE, GL policy, COI).
- [ ] Update annual revenue (every January).
- [ ] Update EMR / TRIR / LTIR (every January after the workers-comp annual posting).
- [ ] Add new past projects as they close out.
- [ ] Re-render `firm-profile.md` from `firm-profile.json`.
- [ ] Re-run `firm/_scripts/apply_firm_profile.py` against `bids/` and commit the diff.
- [ ] Skim `bids/_FIRM_PROFILE_INTEGRATION.md` for the per-workspace coverage report.
