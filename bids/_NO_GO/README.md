# `_NO_GO/` directory

This directory contains **decision memos** documenting opportunities that BPC reviewed and chose not to pursue, with the rationale captured for future reference and process improvement.

## Why memos matter

Even for opportunities BPC doesn't pursue, the decision is worth recording. The memos serve four purposes:

1. **Process improvement** — Identifying common reasons (e.g., "we found out too late") to drive intake-cycle improvements
2. **Market intelligence** — Tracking what opportunities exist in BPC's served sectors
3. **Lessons learned** — If a similar opportunity surfaces later, the memo shows what to watch for
4. **Audit trail** — Demonstrating that BPC considered each opportunity intentionally, not by default-ignore

## File naming convention

Memos use the format:
```
YYYY-MM-DD-{short-project-slug}-{sol-number}.md
```

Where YYYY-MM-DD is the **decision date** (when the no-go was confirmed), not the bid deadline.

## Memo format (~1 page)

Each memo answers 5 questions:

1. **What it was** — 2-3 sentence summary of the opportunity
2. **Why no-go** — Primary reason for not pursuing (closed window, scope mismatch, scale mismatch, etc.) and any secondary blockers
3. **Did this fit BPC?** — yes / partial / no with reasoning. Distinguishes between scope-fit problems and process problems
4. **If similar opportunity arises, what to track differently** — Specific, actionable monitoring improvements (saved searches, weekly calendar checks, etc.)
5. **Source** — Citation to the source (email body, ESBD posting, etc.) that triggered the review

## Current memos

| File | Sol # | Closing date | Reason |
|---|---|---|---|
| `2026-05-22-mcfaddin-nwr-fence-140FC126Q0015.md` | 140FC126Q0015 | 2026-05-22 (closed before notification) | Window closed |
| `2026-05-19-garland-inwood-blvd-REQ00002146.md` | REQ00002146 | 2026-05-19 (closed before notification) | Window closed |
| `2026-05-30-plano-legacy-trail-pond-2026-0422-B.md` | 2026-0422-B | 2026-07-06 (open at decision time) | Scope mismatch — hydraulic dredging / pond restoration outside BPC NAICS lane |
| `2026-05-30-kingsville-storm-water-26-04.md` | 26-04 (CDBG-MIT GLO 22-085-009-D237) | 2026-06-11 (open at decision time) | Scope mismatch (heavy-civil storm-drainage utility) + out of region (Kingsville ~360 mi south of DFW) |
| `2026-05-30-utd-ece-bootcamp-UTD20260301-AN.md` | UTD20260301-AN | 2026-06-19 (open at decision time) | Industry mismatch — non-credit education / workforce-development services, not construction |
| `2026-05-30-tmd-camp-mabry-modular-rfi-TMD26-CFMO-RFI001.md` | TMD26-CFMO-RFI001 | RFI response 2026-07-14 (open at decision time) | Scope mismatch — RFI for prefab modular-office rental (NIGP 971-08 / 971-40), not BPC's NAICS 236220 construction lane |

## Revived opportunities (moved to active workspaces)

| Original memo | Sol # | Revival date | Active workspace |
|---|---|---|---|
| `2026-05-27-leroy-moore-gym-PV-0749-PV-0753.md` (deleted) | PV-0749 + PV-0753 | 2026-05-27 | [`bids/leroy-moore-gym-PV-0749-PV-0753/`](../leroy-moore-gym-PV-0749-PV-0753/) — Addendum 01 (2026-05-18) extended the deadline from 5/27 to 6/4; opportunity reopened and the no-go memo was rescinded. |

## Reading guide

- Each memo is self-contained; no required reading order
- If a memo concludes the opportunity is still pursue-able (e.g., revised deadline), it will explicitly flag that
- Memos are not pursued retroactively — if a memo's reason for no-go is invalidated, a new bid workspace is created (not edits to the memo)

## Related directories

- `bids/_WATCHLIST/` — Opportunities being actively monitored for solicitation release (not yet open for bid)
- `bids/*` — Active pursue workspaces

## Cadence

- New no-go memos are created when opportunities are surfaced and the decision is made not to pursue
- Memos are reviewed every quarter to identify pattern-level process improvements
- No memo is deleted unless the opportunity was processed twice in error
