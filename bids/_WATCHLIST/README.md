# `_WATCHLIST/` directory

This directory contains **monitoring memos** for opportunities BPC has identified as worth tracking but where the solicitation is **not yet open for bid**. Once a solicitation is released (or pre-bid event occurs), the watchlist entry transitions to either:
- A **pursue workspace** at `bids/{slug}/`, OR
- A **no-go memo** at `bids/_NO_GO/`

## Why a watchlist matters

Federal and state agencies frequently publish **pre-solicitation notices** (also called "synopsis," "intent to issue," or "industry day") **weeks or months ahead of the formal solicitation release**. BPC's bid pipeline benefits from:

1. **Early awareness** — Time to prepare firm-side documentation (HUB recertification, COI renewals, etc.) before the solicitation drops
2. **Sub-network buildup** — Time to identify and engage specialty subs (e.g., MARRS glazing) before competitors do
3. **Realistic capacity planning** — Knowing what's coming helps BPC decline new pursue opportunities that would over-extend the team
4. **Decision discipline** — Reduces last-minute "we just heard about it" no-gos

## File naming convention

Watchlist entries use the format:
```
{short-project-slug}-{sol-number}.md
```

(Decision date is in the memo body; file name doesn't need a date prefix since the entry is dated by file metadata + content.)

## Memo format

Each watchlist entry contains:

1. **Solicitation identity** — Sol number, agency, project title, NAICS, set-aside, magnitude
2. **Expected timeline** — Solicitation release date, expected award date, construction start
3. **Specialty considerations** — Any unusual scope (historic preservation, environmental, security-cleared, etc.)
4. **Required prep** — Firm-side action items to complete BEFORE solicitation drops
5. **Monitoring instructions** — Specific SAM.gov saved-search criteria + cadence
6. **Conversion criteria** — Triggers for either creating a pursue workspace or writing a no-go memo
7. **Notes** — Any relevant context or risk flags

## Current watchlist

| File | Sol # | Agency | Expected open | Type |
|---|---|---|---|---|
| `saan-san-juan-restrooms-140P1226Q0025.md` | 140P1226Q0025 | NPS Lakewood MABO | mid-May 2026 (possibly already posted) | Historic preservation; weak past-perf concern |
| `powderly-bldg1-adams-trade-2026-0626.md` | none (private GC) | Adam's Trade & Services, Inc. (Powderly TX) | Open — quote due 2026-06-26 | Private GC sub-bid; scope undisclosed in digest; site visit 2026-06-01 is the decision gate. **[USER ACTION REQUIRED]** attend site visit or email PM for scope summary. |
| `longhorn-little-elm-bcibelisle.md` | none (private GC) | BCI Belisle (Longhorn Steakhouse, Little Elm TX) | Open — sub-quote due not stated in digest | Private GC sub-bid (restaurant fit-out); plans gated behind password-protected portal. **[USER ACTION REQUIRED]** log in at `www.bcibelisle.com` (password `littleelm`) within 48 hr — best geographic match in 2026-05-30 digest (Little Elm is BPC's home town). |

## Resolved / closed watchlist items

| Original key | Resolution date | Resolution |
|---|---|---|
| `opp_4024120_clarify` (phantom — never had a file in this directory) | 2026-05-30 | **Not resolved.** The 2026-05-27 OneDrive batch (`Landmark/05272026/`) was triaged in [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../_TRIAGE/2026-05-27-onedrive-batch.md) and found to contain 5 distinct opportunities, **none** of which reference project number `4024120` or the literal phrase "Renovation of Park and Recreation Center Facilities". Grep across the entire repo for `4024120` returns only references created during this triage. The watchlist key appears to be a stale reference. Outcomes from the batch — 4 new active workspaces (Allen Veterans Memorial, HHSC Bldg 500 Mech, TPWD Old Tunnel Stairs, USACE Fort Hood Staging) + 1 no-go (TMD Camp Mabry modular RFI) — are tracked under `bids/<slug>/` and `bids/_NO_GO/` respectively. See [`firm/playbooks/_learning-log.md`](../../firm/playbooks/_learning-log.md) entry #8 for the open data-quality question to Rocky. |

## Cadence

- **During expected release window:** **DAILY** SAM.gov check for the specific Sol # AND a broader saved-search (e.g., agency + NAICS + set-aside)
- **Outside release window:** Weekly check
- **Quarterly:** Full watchlist review — close out items that aged out or never opened; add new items from emerging opportunity sources

## Conversion to pursue or no-go

When a watchlist item's solicitation drops:

1. **Within 24 hours:** Open the solicitation and do an initial triage:
   - Set-aside still aligns? Y/N
   - Scope still aligns? Y/N
   - Magnitude still in BPC's comfort zone? Y/N
   - Specialty/risk items manageable? Y/N

2. **If yes to all:** Create a pursue workspace at `bids/{slug}/` and copy the relevant Sol # into the file structure. Mirror the closest reference workspace.

3. **If no to any:** Write a no-go memo at `bids/_NO_GO/` explaining the disqualification (different from "missed window" — this is "doesn't fit").

4. **If unclear:** Maintain the watchlist entry with a "REVIEW PENDING" note and surface to Rocky for decision.

## Related directories

- `bids/_NO_GO/` — Decision memos for opportunities NOT pursued
- `bids/*` — Active pursue workspaces

## How to add a new watchlist entry

When a new pre-solicitation notice is identified:

1. Create `bids/_WATCHLIST/{slug}-{sol-number}.md` per the format above
2. Add the entry to the table in this README
3. Set up the SAM.gov saved-search per the entry's monitoring instructions
4. Calendar the daily/weekly check cadence in Rocky's task list
