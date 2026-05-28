# Proposal package — Leroy Moore Gymnasium Racquetball Courts 1, 2 & 8 Renovations (Sol PV-0749 & PV-0753)

This directory contains the **Competitive Sealed Proposal (CSP)** narrative + forms for submission to Prairie View A&M University (TAMU System) via SSC Services for Education.

**Due: 2026-06-04 @ 2:00 PM CT. Target submit: 2026-06-03 EOD (1-day buffer).**

> ⚠️ **Skeleton scaffold.** This `proposal/` subdirectory was generated
> from the TAMU Wehner template on workspace creation because the
> `bids/_TEMPLATES/texas-state-csp-hsp/` template does NOT ship one.
> Every section below is a `[USER TO FILL]` skeleton — verify against
> the actual CSP package (Project Manual §00 21 00) before submission.

---

## 1. Submission shape

Per the Notice of Project: **sealed envelope, mail or hand-deliver** to:

> SSC Service Solutions
> Construction and Planning
> ATTN: Joe Ellis
> 580 Anne Preston St
> Prairie View, TX 77446

The exterior of the envelope must include an email address for the Teams meeting invitation per the NOP supplemental info.

## 2. BIG MISSING ITEMS (before this proposal can ship)

1. **CSP package retrieved** — pull from the e-Builder public landing link in `00-overview.md` / `01-overview.md`
2. **Drawings + project manual + addenda in hand** — for takeoff
3. **Sub quotes received** — minimum 3 per trade for HUB GFE
4. **HUB sub commitments documented** — for HSP form
5. **Current COI from insurance broker**
6. **Bonding agent commitment letter**
7. **Past-perf reference contacts surfaced** — 3 references
8. **EMR / TRIR / LTIR figures from WC carrier** — for Safety scoring

## 3. Proposal sections (mapped to TAMU System CSP scoring)

Scoring weights are estimates pending Addendum 02 (CSP Evaluation Scoring Guidelines) close read.

| Section | File | Estimated weight | Status |
|---|---|---:|---|
| Executive Summary | `01-executive-summary.md` | (cover; no direct score) | 🟡 Skeleton |
| Technical Approach | `02-technical-approach.md` | 10-15% | 🟡 Skeleton |
| Project Team | `03-project-team.md` | 5-10% | 🟡 Skeleton |
| Past Performance | `04-past-performance.md` | 15-25% | 🟡 Skeleton — `[USER TO FILL]` reference contacts |
| Schedule Narrative | `05-schedule-narrative.md` | (part of Technical Approach) | 🟡 Skeleton |
| Quality Control Plan | `06-quality-control-plan.md` | (part of Technical Approach) | 🟡 Skeleton |
| Safety Plan | `07-safety-plan.md` | ~5% | 🟡 Skeleton — EMR/TRIR `[USER TO FILL]` |
| CSP Proposal Form fill | `08-csp-proposal-form-fill-guide.md` | (form, not narrative) | 🟡 Awaiting form retrieval |
| HSP Form fill | `09-hsp-form-fill-guide.md` | 5-10% | 🟡 Awaiting sub commitments |
| Price Proposal | `10-price-proposal.md` | 40-60% (largest weight) | 🟡 Awaiting takeoff + sub quotes |
| Submission Checklist | `11-submission-checklist.md` | — | 🟡 Skeleton |
| Bid Bond Letter Template | `12-bid-bond-letter-template.md` | — | 🟡 Awaiting bonding-agent commitment letter |

## 4. Cross-reference to firm-profile

This proposal uses values from `firm/firm-profile.json` as the canonical source for firm name, UEI, CAGE, NAICS, key personnel, past projects, and insurance/bonding. Run `python firm/_scripts/apply_firm_profile.py bids/leroy-moore-gym-PV-0749-PV-0753/` after editing to refresh placeholders.

## 5. Cross-reference to sibling workspaces

This workspace's CSP scaffolding (`01-overview.md` … `09-proposal-draft.md` at the workspace root) was generated from `bids/_TEMPLATES/texas-state-csp-hsp/`. The `proposal/` subfolder structure mirrors `bids/tamu-wehner-fin-340E-2025-06871/proposal/` and `bids/tamu-harrington-2025-06813/proposal/`.
