# Bid prep — TAMU Wehner Finance Seminar Room 340E Expansion

**Solicitation:** SSC-2025-06871
**Agency:** SSC Services for Education (on behalf of Texas A&M University)
**Project:** Wehner Building (Mays Business School), Room 340E — Finance Seminar Room expansion into Rms A, D, DA
**Location:** College Station, TX 77843 (TAMU main campus)
**Status:** **DRAFT — AWAITING CSP PACKAGE FROM SSC** (only the ESBD Notice of Project is on disk as of 2026-05-27)

---

## Quick facts

| Item | Value | Source |
|---|---|---|
| Solicitation ID | SSC-2025-06871 (referred to as "2025-06871" in the email body) | ESBD posting 2026-05-06 |
| Project name | Wehner Finance Seminar Rm 340E | ESBD posting; user email-body |
| Issuing entity | SSC Services for Education (TAMU Part 02 / Mays Business School) | ESBD; user email-body |
| Procurement vehicle | **Competitive Sealed Proposal (CSP)** under TAMU System UGSC | TAMU System CSP pattern (matches Harrington 2025-06813) |
| NAICS (inferred) | 236220 — Commercial & Institutional Building Construction | Inferred from scope |
| Set-aside | Open competition; **HUB Subcontracting Plan REQUIRED** | User email-body |
| Class/Item Code | 90900 — Building Construction Services, New (Incl. Maintenance And Repair Services) | ESBD |
| Posting requirement | 14+ days for entire solicitation package | ESBD |
| Solicitation posting date | 2026-05-06 | ESBD |
| Solicitation status | Addendum Posted (5/6/2026 4:50 PM — Corrected Due Date) | ESBD |
| **Proposal Due** | **2026-06-17, 2:00 PM CT** | ESBD; user email-body (CORRECTED — original posting may have shown different date) |
| Public proposal opening | 2026-06-17, 2:30 PM CT | User email-body |
| **Pre-proposal meeting** | **2026-05-19, SSC Facilities Services Conf Rm S118** | User email-body — **ALREADY PAST** |
| Pre-proposal status | **MISSED** by Blue Print Constructs (lead arrived 2026-05-27) | User email-body |
| Period of performance | TBD — to be confirmed from CSP package | — |
| BPC pursue/no-go | **PURSUE — 21-day window** | User triage 2026-05-27 |

---

## Critical scope facts (from user email-body)

> Scope: expand Rm 340E into Rms A, D, DA — remove sink + appliances + casework + cabinetry; new **MARRS glass wall** along corridor; finish coordination.

This is a **finance-seminar / faculty-office expansion** at the Mays Business School. The structural intent appears to be combining four adjacent rooms (340E + A + D + DA) into a single larger seminar / faculty room. Trades involved:
- Selective demolition (sink + appliances + casework + cabinetry from existing kitchenette-like fitouts in adjacent rooms)
- Walls — partial demo of existing partitions between rooms; new partitions or finish-out as designed
- **MARRS architectural glazing** for the new corridor-side glass wall (specialty subcontractor required)
- Finishes — flooring, base, paint, ceiling, possibly new lighting
- MEP — likely demolition / relocation of existing plumbing (sink), electrical (appliance circuits), HVAC adjustments for new larger room volume; coordination with TAMU IT for new AV / data
- Coordination with TAMU EHS for any chemical / appliance hazards prior to demo
- Furniture coordination (likely TAMU-provided post-construction)

Drawings + specs not yet on disk. See `04-scope-of-work.md` for trade-by-trade extracted breakdown and `takeoff-template.json` for line-item skeleton (with `[AWAITING DRAWINGS]` quantity placeholders).

---

## Go / no-go gates (post-2026-05-19 missed-pre-proposal)

| # | Gate | Trigger | Deadline | If miss | Status as of 2026-05-27 PM |
|---|---|---|---|---|---|
| 1 | **Eligibility confirmed** post-missed 5/19 pre-proposal meeting | Matt Wiederstein (SSC PM) and/or Cherise Toler (TAMU Procurement) confirm in writing that a non-attending firm can still submit a responsive proposal | **EOD Thu 2026-05-28** | If pre-proposal meeting was mandatory and there is no late-arriver accommodation: **walk away** | 🟡 OUTREACH READY — `outreach/01-email-cherise-toler-eligibility.md` drafted; CC Matt Wiederstein for sub-contractor PM record. **Cherise Toler is the TAMU-side official procurement contact per ESBD; send to her first since she controls the responsiveness determination procedurally.** |
| 2 | **CSP package downloaded + scanned** | Full CSP package pulled (Notice of Project document + drawings + specs + HSP form + Proposal Form + UGSC + sample contract) | **EOD Fri 2026-05-29** (within 24 hrs of G1 close) | If still gated by 2026-06-02, escalate to TAMU System OFPC; if no path by 2026-06-04, walk away | 🟡 BLOCKED — ESBD posting references "Notice of Project (NOP) document for link to download all project documents" but the NOP itself was not in the email attachments. User likely needs to download the NOP PDF from ESBD and follow its link to the full CSP package (which is typically hosted on Trimble Unity Construct / e-Builder, same as Harrington). See `03-missing-documents.md` § 2. |
| 3 | **Internal go/no-go meeting** | PM + estimator + safety lead review scope, schedule, HSP feasibility (per BPC's known HUB cert expiration), and MARRS glazing sub availability | **EOD Mon 2026-06-01** | If no-go: archive workspace under `local/`, notify Matt Wiederstein + Cherise Toler as a no-bid courtesy | ⏳ PENDING G1 + G2 close |

**Net: 21 calendar days from today (Wed 2026-05-27) to bid submission (Wed 2026-06-17, 14:00 CT). After Gate 1/2 close, ~14 working days remain for takeoff, sub solicitation, HSP build, and proposal narrative.**

---

## What's complete in this workspace (scaffold pass 2026-05-27)

- [x] `README.md` — this file
- [x] `source-files-manifest.md` — what we have on disk (just the ESBD NOP listing) and what we still need
- [x] `01-overview.md` — solicitation summary (with email-body verbatim)
- [x] `02-bid-prep-checklist.md` — registration / insurance / bonding / HUB / pricing
- [x] `03-missing-documents.md` — list of inputs needed
- [x] `04-scope-of-work.md` — trade-by-trade scope draft with `[AWAITING DRAWINGS]` markers
- [x] `05-hsp-plan.md` — HSP strategy under BPC's expired-HUB-cert posture (sub-only, not self-perform)
- [x] `06-evaluation-strategy.md` — TAMU CSP scoring + positioning
- [x] `07-risk-register.md` — including the missed-pre-proposal-meeting risk
- [x] `contacts.md` — all POCs
- [x] `price-references.md` — $/SF benchmarks for office / seminar / classroom reno in TAMU System
- [x] `price-sheet-skeleton.json` — CSI-grouped pricing-form skeleton
- [x] `takeoff-template.json` — line-item takeoff skeleton
- [x] `timeline.md` — backwards-planned schedule from June 17 due date
- [x] `proposal/` — 13 markdown files mirroring TAMU Harrington (executive summary, technical approach, project team, past performance, schedule, QC, safety, CSP-form fill-guide, HSP-form fill-guide, price proposal, submission checklist, bid bond letter template)
- [x] `outreach/` — 8 outreach drafts (Cherise eligibility, Matt Wiederstein CSP access, Kelsie Srnensky drawings, Patty Winkler HUB, bonding agent, insurance broker, call script, Q&A submission)

## What's blocked

- [ ] **CSP package retrieval** — Notice of Project document not in BPC email attachments; user must pull from ESBD posting (look at the attachment named `ESBD_513163_1778104136552_2025-06871_Notice of Project-CS_26.05.05.pdf` listed in the ESBD HTML body), then follow the link inside to download the full CSP package from the Trimble Unity Construct e-Builder portal
- [ ] **Drawings + specs** — within the CSP package once retrieved
- [ ] **Real takeoff quantities** — drawings required
- [ ] **HUB cert renewal status** — Blue Print Constructs's HUB certificate expired 2024-08-31; user to confirm renewal status. Without renewal, **BPC cannot self-perform any HUB-scored portion** and must build HSP from HUB subs only.
- [ ] **MARRS glass wall installer** — specialty architectural glazing sub; BPC does not self-perform. User to identify and outreach a sub.
- [ ] **Sub quotes** — can't solicit broadly until G1 + G2 close

---

## Tomorrow's actions (top 5)

1. **Email Cherise Toler (TAMU Procurement)** Thu 2026-05-28 AM at `ctoler@tamu.edu`; cc Matt Wiederstein at `matthew.wiederstein@sscserv.com`. Confirm post-missed-meeting eligibility; request the pre-proposal meeting sign-in sheet, recording, Q&A, and addenda; ask about a site walk of Rm 340E in the week of 6/1. (See `outreach/01-email-cherise-toler-eligibility.md`.)
2. **Pull the CSP package from ESBD + Trimble Unity Construct** — open the ESBD posting (Solicitation ID SSC-2025-06871) in a regular browser; download the Notice of Project PDF; follow its embedded link to the full CSP package. (See `03-missing-documents.md` § 2 for step-by-step.)
3. **Confirm Blue Print Constructs HUB certificate status** — per `firm/firm-profile.json` the cert expired 2024-08-31. If renewed, claim self-perform HUB credit; if not, build the HSP from HUB subs only. (See `05-hsp-plan.md` § 2.)
4. **Identify and outreach a MARRS / architectural glazing sub** — specialty subcontractor for the corridor glass wall. (See `outreach/03-email-kelsie-szs-drawings.md` for A/E spec clarification on glass wall product specifics.)
5. **Notify bonding agent + insurance broker** of the upcoming submission. Use the same templates as TAMU Harrington but with Wehner-specific project value range ($75K–$200K — see `price-references.md`). (See `outreach/05-email-bonding-agent.md` and `outreach/06-email-insurance-broker.md`.)

---

## File map

```
bids/tamu-wehner-fin-340E-2025-06871/
├─ README.md
├─ 01-overview.md
├─ 02-bid-prep-checklist.md
├─ 03-missing-documents.md
├─ 04-scope-of-work.md
├─ 05-hsp-plan.md
├─ 06-evaluation-strategy.md
├─ 07-risk-register.md
├─ takeoff-template.json
├─ price-sheet-skeleton.json
├─ price-references.md
├─ contacts.md
├─ timeline.md
├─ source-files-manifest.md
├─ proposal/                          ← 13 markdown files
│  ├─ 00-readme.md
│  ├─ 01-executive-summary.md
│  ├─ 02-technical-approach.md
│  ├─ 03-project-team.md
│  ├─ 04-past-performance.md
│  ├─ 05-schedule-narrative.md
│  ├─ 06-quality-control-plan.md
│  ├─ 07-safety-plan.md
│  ├─ 08-csp-proposal-form-fill-guide.md
│  ├─ 09-hsp-form-fill-guide.md
│  ├─ 10-price-proposal.md
│  ├─ 11-submission-checklist.md
│  └─ 12-bid-bond-letter-template.md
└─ outreach/                          ← 8 outreach drafts
   ├─ 01-email-cherise-toler-eligibility.md   ← 🔴 PRIMARY — send Thu AM
   ├─ 02-email-matt-wiederstein-csp-access.md
   ├─ 03-email-kelsie-szs-drawings.md
   ├─ 04-email-patty-winkler-hub.md
   ├─ 05-email-bonding-agent.md
   ├─ 06-email-insurance-broker.md
   ├─ 07-call-script-matt-wiederstein.md
   └─ 08-q-and-a-submission.md
```
