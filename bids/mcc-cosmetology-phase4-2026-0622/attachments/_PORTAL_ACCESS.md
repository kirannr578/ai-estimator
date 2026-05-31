# Portal access — MCC Cosmetology Phase 4 (HCS Box)

> **[USER ACTION REQUIRED]** — The plans, specs, and Owner's Proposal Form for this opportunity are gated behind the HCS Box link below. Cursor agents have **no Box credentials and no browser MCP for portal-gated downloads**, so the user must pull these files manually.

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

## Action items for the user

- [ ] Open the Box link in a browser
- [ ] If a Box account login is required, log in with the BPC corporate Box identity (or create one if BPC does not have one)
- [ ] Download all available files into the staging folder above
- [ ] Take a screenshot of the Box folder index showing every file's name + date + size, and save it as `_box-folder-index-{YYYY-MM-DD}.png` in `00-original-drop/`
- [ ] Notify the bid lead so the next slice can re-update [`../01-overview.md`](../01-overview.md), [`../06-scope-outline.md`](../06-scope-outline.md), and [`../07-risk-register.md`](../07-risk-register.md) with the now-known content

## If access fails

- If the Box link is restricted to authenticated users only, email HCS Estimating at the Waco address above (254-829-3200) and request access. Reference solicitation: "MCC CSC Module B Cosmetology Phase 4 Renovation, sub-quote due 2026-06-22 10:00 CT".
- If the Box folder is empty or missing the Owner's Proposal Form, email HCS Estimating to request the form be added to the share.

## Security note

This Box link is a **public share link** included in a publicly-distributed DFWMSDC mailing-list digest. The link is therefore not a credential and may be referenced freely in this repo. The *files* behind the link, however, are project-bid documents (plans + specs + Owner's Proposal Form) and should be treated as **Private-class** once downloaded — staging on OneDrive is appropriate; pasting their contents into chat with non-approved AI tooling is not.
