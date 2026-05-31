# `_TRIAGE/` directory

This directory holds **batch-level triage memos** for OneDrive drops that contain multiple solicitations from a single date. The triage memo is the bridge between a raw folder of PDFs and one-or-more downstream artifacts:

- A pursue workspace at `bids/<slug>/`
- A watchlist memo at `bids/_WATCHLIST/`
- A no-go memo at `bids/_NO_GO/`

## When to create a triage memo

Create one whenever the source folder contains **more than one** distinct solicitation (different agencies, different solicitation numbers, or one solicitation plus its unrelated companions). A single-solicitation drop goes straight to `bids/<slug>/source-files-manifest.md`; multi-solicitation drops need a fan-out document so the inventory + per-opportunity decisions stay together.

## File-naming convention

```
YYYY-MM-DD-<source-shortname>.md
```

Where `YYYY-MM-DD` is the drop date (date the user saved the folder, not the date the agency posted the docs) and `<source-shortname>` describes where the batch came from.

## Memo contents (template)

1. **Source** — OneDrive path (canonical, read-only), batch date, ingestion date
2. **Inventory** — every file, size, type guess, confidence
3. **Opportunity grouping** — which files belong to which solicitation
4. **Per-opportunity triage** — for each opportunity: Path A / B / C decision, slug chosen, playbook chosen, downstream artifact created
5. **Cross-batch learnings** — anything novel about the batch as a whole worth capturing in `firm/playbooks/_learning-log.md`

## Current triage memos

| File | Source | Date | Opportunities |
|---|---|---|---|
| [`2026-05-27-onedrive-batch.md`](2026-05-27-onedrive-batch.md) | `OneDrive/Blueprint Constructs/Landmark/05272026/` | 2026-05-27 | 5 (Allen Veterans Memorial; HHS Bldg 500 Mech; TMD Camp Mabry Modular RFI; TPWD Old Tunnel Stairs; USACE Fort Hood Staging) |
