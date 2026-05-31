# Source files manifest — MCC Cosmetology Phase 4

> **Source:** DFWMSDC Construction Members digest, **2026-05-30**. The digest **text** is the only on-hand source at scaffold time. All bid documents are gated behind the HCS Box link — see [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md).

## On-hand at scaffold creation

| # | Source | Format | Description |
|--:|---|---|---|
| 1 | DFWMSDC Construction Members digest 2026-05-30 — Opportunity #1 (McLennan Community College / HCS) | Email body text | High-level project name, location, scope categories, due date, site-meeting date, Box plans URL, HCS Estimating phone + address. No solicitation #, no magnitude, no schedule, no specs. |

That's it. No PDFs, no XLSX, no drawings, no spec book.

## Documents referenced but NOT yet in hand

All documents below are gated behind the HCS Box link. **USER ACTION REQUIRED** to download — see [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md).

| Document | Status | Source |
|---|---|---|
| **Plans / Drawings** (architectural, MEP, finish schedule) | 🔴 Missing | HCS Box `https://hcs-gc.box.com/s/bhy2pkudhlkcgcxfo7qxdb8vcjnhfwni` |
| **Specifications book / Project Manual** | 🔴 Missing | Same Box link |
| **Owner's Proposal Form** (XLSX or PDF — BPC's bid form) | 🔴 Missing | Same Box link (digest verbatim: *"PLEASE SEE THE ATTACHED BID FORM"* — the form is in the Box, not in the digest) |
| Any addenda HCS posts during the bid window | 🔴 To monitor | Same Box link, daily check 2026-06-15 → 2026-06-22 |

## How to stage files once pulled

Per repo convention, large binary source files stay on OneDrive (not in git). Stage at:

```
C:\Users\rnuduru1\OneDrive\Blueprint Constructs\HCS\05302026-mcc-cosmetology\
```

Recommended subfolder layout (mirrors prior bid workspaces):

```
05302026-mcc-cosmetology\
├── 00-original-drop\      # raw downloads from Box (read-only)
├── 01-addenda\            # HCS-issued addenda; date-stamp filenames
├── 02-pricing-build\      # BPC's working pricing files (XLSX, takeoffs)
└── submitted\             # final pricing submission + email confirmation
```

After staging, re-update [`01-overview.md`](./01-overview.md), [`06-scope-outline.md`](./06-scope-outline.md), and [`07-risk-register.md`](./07-risk-register.md) with the now-known scope, magnitude, schedule, and form layout.

## Batch triage reference

This workspace is one fan-out of the DFWMSDC digest 2026-05-30 ingestion. See the per-opportunity table in the commit message for the full digest disposition. No batch-level triage memo is created for DFWMSDC digests because each digest reaches BPC as plain email body (not a folder of PDFs); the per-opportunity scaffolds are the canonical record.
