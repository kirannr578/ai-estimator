# Portal access — MCC Cosmetology Phase 4 (HCS Box)

> ✅ **DOWNLOADED 2026-05-30 20:08 CT** — User pulled the HCS Box folder contents as
> `Phase 4 CSC Module B Cosmetology.zip` (20.8 MB) into
> `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\`. The Cursor agent extracted
> the ZIP into `bids/mcc-cosmetology-phase4-2026-0622/attachments/` (3 PDFs: 414-page Project
> Manual + 37-sheet Drawing Set + 2-page Section 004213 CSP Proposal Form). See
> [`../source-files-manifest.md`](../source-files-manifest.md) for the full inventory.
>
> **Action posture below is now ADDENDUM MONITORING ONLY.** Re-pull the Box folder daily
> from 2026-06-15 through 2026-06-22 to capture any addenda HCS posts.

## HCS plans portal (Box)

| Field | Value |
|---|---|
| Portal | Box (HCS-hosted shared folder) |
| URL | `https://hcs-gc.box.com/s/bhy2pkudhlkcgcxfo7qxdb8vcjnhfwni` |
| Authentication | Box shared-link (no login required for shared links by default; a Box account may be required if HCS has restricted the share to authenticated users) |
| Password | None disclosed in digest |
| Listed contents (per digest) | Plans, Specs, Addenda |
| Implied contents (per digest text "ATTACHED BID FORM") | **Owner's Proposal Form** (XLSX or PDF) — BPC's pricing form |
| Source | DFWMSDC Construction Members digest, 2026-05-30 (verbatim: *"Plans: Download Plans, Specs and Addenda by clicking here: https://hcs-gc.box.com/s/bhy2pkudhlkcgcxfo7qxdb8vcjnhfwni"*) |
| Issuer contact | HCS Inc. Estimating Department, 365 Wayside Drive, Waco, TX 76705 — **254-829-3200** |

## What to download

When the user opens the Box link:

1. **Owner's Proposal Form** (XLSX or PDF) — this is the canonical bid form per the digest. **Highest priority.**
2. **Plans / Drawings** — architectural, MEP, finish schedule, demolition plan
3. **Specifications book / Project Manual** — particularly the cosmetology-relevant sections (Division 09 finishes, Division 11 equipment, Divisions 22/23/26 MEP)
4. **Any Addenda already posted** — date-stamp filenames; flag any addendum that materially changes scope or schedule

## Where to stage downloads

```
C:\Users\rnuduru1\OneDrive\Blueprint Constructs\HCS\05302026-mcc-cosmetology\00-original-drop\
```

Create the folder if it does not exist. Treat as read-only canonical source after the initial download.

## Action items for the user (DOWNLOADED — addendum-monitoring posture)

- [x] Open Box link, download ZIP, stage at OneDrive `Landmark/` (DONE 2026-05-30 20:08)
- [x] Extract ZIP into `attachments/` (DONE — committed via this enrichment)
- [x] Re-update [`../01-overview.md`](../01-overview.md) / [`../06-scope-outline.md`](../06-scope-outline.md) / [`../07-risk-register.md`](../07-risk-register.md) (DONE — committed via this enrichment)
- [ ] **Daily Box re-pull 2026-06-15 → 2026-06-22** to detect addenda. Re-extract into a fresh folder, diff against `attachments/`, and append any new files to [`../source-files-manifest.md`](../source-files-manifest.md) with date-of-addition

## If addendum re-pull access ever fails

- If the Box link returns 403 / requires a login, email HCS Estimating at the Waco address above (254-829-3200) and request access. Reference solicitation: "MCC CSC Module B Cosmetology Phase 4 Renovation, sub-quote due 2026-06-22 10:00 CT".

## Security note

This Box link is a **public share link** included in a publicly-distributed DFWMSDC mailing-list digest. The link is therefore not a credential and may be referenced freely in this repo. The *files* behind the link, however, are project-bid documents (plans + specs + Owner's Proposal Form) and should be treated as **Private-class** once downloaded — staging on OneDrive is appropriate; pasting their contents into chat with non-approved AI tooling is not.
