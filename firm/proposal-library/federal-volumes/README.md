# `federal-volumes/` — federal RFP volume templates (FAR 15.305 best-value tradeoff)

This sub-library is the source of truth for **best-value tradeoff** federal RFP responses (FAR 15.101-1) — distinct from the LPTA archetype already covered in [`exec-summary-archetypes/federal-sba-lpta.md`](../exec-summary-archetypes/federal-sba-lpta.md). On a tradeoff source selection, the Government compares technical merit, management approach, past performance, and price against each other; non-price factors are typically equal to or more important than price. The proposal therefore has to **sell** — within strict page limits and a structure the SSEB can score against the Section M evaluation factors.

The standard 4-volume model below is FAR 15.305-derived. The exact volume names, page limits, and submission format will vary by RFP — always cross-check Section L (Instructions) and Section M (Evaluation Factors) before pasting.

> **Companion playbook:** [`firm/playbooks/federal-rfp-best-value-tradeoff.md`](../../playbooks/federal-rfp-best-value-tradeoff.md) (capture / proposal-strategy guidance — bid/no-bid, color-team reviews, theme statements, win-themes, ghost paragraphs, and graphics strategy).

## The 4-volume model

| Volume | Typical page limit | Scored against (Section M) | Template |
|---|---|---|---|
| **Volume I — Technical Approach** | 8–12 pages | Technical Approach factor (most heavily weighted on construction tradeoffs) | [`volume-i-technical-approach.md`](volume-i-technical-approach.md) |
| **Volume II — Management Approach** | 5–8 pages | Management / Key Personnel factor | [`volume-ii-management-approach.md`](volume-ii-management-approach.md) |
| **Volume III — Past Performance** | 3–5 pages + appendices | Past Performance factor (Confidence assessment per FAR 15.305(a)(2)) | [`volume-iii-past-performance.md`](volume-iii-past-performance.md) |
| **Volume IV — Price Proposal** | 2–4 pages + Schedule of Prices | Price factor (cost realism + reasonableness) | [`volume-iv-price-proposal.md`](volume-iv-price-proposal.md) |

Note: Section L sometimes calls these "Factor 1 / Factor 2 / ..." or "Tab A / Tab B / ..." or numbers volumes I–V (splitting Past Performance and Relevant Experience). When the RFP labels differently, **map BPC's volume content to the RFP's labels — do not change BPC's internal structure**. Renumber the cover page, leave the body alone.

## How to use

1. Read Section L and Section M of the RFP. Identify the page limits and the evaluation factors.
2. For each required volume, copy the matching file into `bids/<slug>/proposal/`, rename to match the RFP's volume label (e.g. `02-volume-II-management.md`), and search-and-replace `{{...}}` placeholders.
3. Cross-reference these supporting files (do **not** duplicate their content — link or paste in place):
   - Past performance: [`past-performance/`](../past-performance/) (3–5 picks per `firm-profile.json → past_project_selection_rules`)
   - Key personnel: [`key-personnel/`](../key-personnel/) (only Rocky's bio is fully sourced — see firm-profile flags)
   - Boilerplate (safety, QC, communications, schedule, sub-management, closeout): [`boilerplate/`](../boilerplate/)
   - Capability statement (sources-sought / pre-solicitation): [`../capability-statement/`](../capability-statement/)
   - Past-Performance Questionnaire collection: [`../ppq/`](../ppq/)
4. Trim aggressively to the Section L page limit. Every paragraph above the limit risks a non-responsive determination.
5. Run `firm/_scripts/scan_placeholders.py` against the bid workspace before submission — zero `{{...}}` and `[USER TO FILL]` hits is the gate.

## Placeholder convention

Same as the rest of the capability library:

- `{{UPPER_SNAKE}}` — project-specific facts pulled from the RFP or set during bid prep
- `[USER TO FILL]` — firm-internal data not yet captured in `firm-profile.json` (e.g. non-PIC personnel)
- `[TEMPLATE]` — structural skeletons / illustrative examples to overwrite

## Tradeoff vs LPTA — when to use which

| | LPTA | Best-value tradeoff |
|---|---|---|
| Section M emphasis | Lowest price meeting "acceptable" technical | Tradeoff between technical / management / past performance / price |
| Volume I role | Pass/Fail technical acceptability statement (1 page) | Sells the technical approach (8–12 pages) |
| Volume II role | Past performance + bond letter (1–2 pages) | Sells management approach + key personnel (5–8 pages) |
| Volume III role | n/a (folded into II) | Past performance with Confidence assessment (3–5 pages) |
| Volume IV role | Schedule of Prices + cover letter | Schedule of Prices + cost realism narrative |
| Companion file | [`exec-summary-archetypes/federal-sba-lpta.md`](../exec-summary-archetypes/federal-sba-lpta.md) | This sub-library |

If the RFP is LPTA, **do not paste these volume templates** — they will introduce narrative that flips Pass → Fail. Use the LPTA archetype instead.

## Firm-data flags that will block a federal tradeoff submission

These cascade in from [`firm/compliance/README.md`](../../compliance/README.md) and `firm-profile.json`:

- **Only the Principal in Charge has a fully sourced bio.** All other key-personnel files are `[USER TO FILL]` skeletons. Federal SSEBs verify named personnel; do not submit a Volume II that lists fictitious people.
- **EMR and OSHA 300 history are not on file.** Volume I (Safety section) and Volume II (Past Performance safety summary) cannot ship until provided.
- **TX HUB / MBE / SBE certifications renewed 2026-05-30 per user confirmation** (prior cycle expired 2024-08-31). New expiration date is pending user confirmation (`[USER TO CONFIRM: new expiration date]`). Federal evaluators don't typically score TX HUB, but the capability statement and small-business reps must reflect the current active status — capture the new expiration before claiming on any federal proposal that asks for a specific certification expiration.
- **Insurance COIs may be stale** (last documented GL policy expired 2024-09-25). Volume IV bonding/insurance buildup needs current limits before pricing.
- **Past-performance reference contacts are `[USER TO FILL]` on all three primary projects.** Volume III ships with live POCs only.
