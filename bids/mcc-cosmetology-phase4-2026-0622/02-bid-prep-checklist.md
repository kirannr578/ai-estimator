# Bid-prep checklist — MCC Cosmetology Phase 4 (HCS sub-bid)

> No matching "private GC sub-bid" playbook in [`firm/playbooks/README.md`](../../firm/playbooks/README.md). At MCC's tier the *Texas Higher-Ed CSP* pattern is the right playbook root — see [`firm/playbooks/texas-state-csp-hsp.md`](../../firm/playbooks/texas-state-csp-hsp.md) — but at BPC's tier (sub-to-HCS) only HCS's internal flow controls. When the [PLAYBOOK GAP] for private-GC sub-bid is closed, restructure this file against the new playbook.
>
> Sub-quote due to HCS: **2026-06-22 10:00 CT** — 23 calendar days from triage (2026-05-30).

## Gate 0 — Decision gate (post-enrichment, scope is now in hand)

- [x] Pull plans + specs + Proposal Form from HCS Box (DONE 2026-05-30 20:08 — see [`attachments/_PORTAL_ACCESS.md`](./attachments/_PORTAL_ACCESS.md))
- [x] Update [`01-overview.md`](./01-overview.md), [`06-scope-outline.md`](./06-scope-outline.md), [`07-risk-register.md`](./07-risk-register.md), [`source-files-manifest.md`](./source-files-manifest.md) with the actual content (DONE this commit)
- [ ] **Email HCS Estimating** (254-829-3200 / 365 Wayside Drive, Waco TX 76705) to:
  - Confirm specific HCS sub-pricing template (HCS's internal template, not Form 004213 which is HCS-to-MCC only)
  - Confirm scope of Alternate 1 (visible from drawings as MD2.1A / MH2.2A / ED2.1A / EL2.1A / A6.3 / A7.3 / A7.4 — pricing route via Section 012300 Alternates)
  - Confirm whether HCS counts BPC's pending HUB recertification as material to HCS's MCC HUB acknowledgment (Form 004213)
  - Request HCS's identification of which trade scopes it most wants quoted by MBE/HUB subs
- [ ] Decide BPC's quote scope: Option A (single self-perform trade), B (multi-trade self-perform package), or C (rolled-up sub-GC package). **Recommend Option B** — see [`06-scope-outline.md`](./06-scope-outline.md).
- [ ] Decide attendance at MCC Pre-Proposal Conference (6/1 10AM) — *encouraged not mandatory* per PM §002116 §1.05; cost-benefit on the Waco round-trip

## Gate 1 — Source-document completeness ✅

- [x] **Project Manual** (414 pages) — `attachments/Specifications/25062 MCC CSC Module B Cosmetology Phase 4 Renovations PM.pdf`
- [x] **Drawings** (37 sheets) — `attachments/Plans/25062 MCC CSC MODULE B PHASE 4 RENOVATIONS DWG.pdf`
- [x] **Section 004213 CSP Proposal Form** standalone (2 pages, vector-only) — `attachments/Solicitation Documents/Proposal Form.pdf`
- [ ] **Davis-Bacon wage determination** for McLennan County, TX (building construction) — pull from `https://sam.gov/wage-determinations` per PM §002116 §1.17 reference to `https://beta.sam.gov`
- [ ] Daily Box re-pull 6/15 → 6/22 for any addenda HCS posts (deterministic — re-download the ZIP, diff against committed `attachments/`)
- [ ] HCS's internal sub-pricing template (separate document; arrives by request from HCS Estimating)

## Gate 2 — MCC Pre-Proposal Conference (2026-06-01 10:00 CT, if attending)

> **Location:** MCC Physical Plant Plan Room, 1400 College Drive, Waco TX 76708 (per PM §002116 §1.05 verbatim).

- [ ] Decide attendance: encouraged not mandatory; same-day round trip from Frisco is ~3 hr drive total
- [ ] Pre-read: at minimum sheets A0.1 (codes/symbols) + A2.1 (1st floor plan) + A2.2 (RCP) + A7.1 (finish plan) + LS2.1 (life safety) + Form 004213 + spec §002116 + PM ToC before going
- [ ] Bring: tape measure, photo capability, business cards, BPC capability statement, printed copy of Form 004213 + ToC for Q&A reference
- [ ] Capture site notes: existing classroom conditions, after-hours/summer access policy, demolition staging area, dumpster location, parking, hazmat-survey indicators (legacy floor tile, paint condition), MEP rough-in conditions visible behind ceiling tiles
- [ ] Identify other proposers in attendance (BPC's competing sub-quote landscape) and other GC primes besides HCS who may also want BPC's quote

## Gate 3 — Compliance readiness (firm-side, blocker for any DFWMSDC-channel sub-bid)

- [ ] **TX Comptroller good-standing** — verify no franchise-tax delinquency (firm-side)
- [ ] **Insurance / COI** — renewed COI naming **HCS Inc.** as additional insured (CGL $1M/$2M, WC statutory, Auto $1M CSL minimum). The on-file CGL SBCC-042443-00 expired 2024-09-25 per `firm/firm-profile.json`; broker hand-off in flight
- [x] **DFW MSDC MBE / SBE recertification** — DL09279 ✅ renewed 2026-05-30 per user confirmation (prior cycle expired 2024-08-31); new expiration `[USER TO CONFIRM: new expiration date]`
- [x] **TX HUB recertification** — VID 1874292998900 ✅ renewed 2026-05-30 per user confirmation (prior cycle expired 2024-08-31); new expiration `[USER TO CONFIRM: new expiration date]`
- [ ] **Davis-Bacon labor compliance prep** — confirm BPC payroll software supports WH-347 weekly certified payroll (or arrange manual filing); confirm sub-tier flow-down in BPC's standard sub-PO template
- [ ] **W-9 + DBA registration** — current copies on file with HCS

## Gate 4 — Scope clarification + sub outreach

- [ ] **RFI window:** Per PM §002116 §1.12 inquiries to the architect (RBDR) must allow ≥7 days for reply and "no inquiries will be received within 48 hours of receipt of proposals" — i.e., **last-call RFI is ~2026-06-21 14:00 CT**. Route BPC's RFIs through HCS Estimating (HCS bundles questions to RBDR per CSP convention).
- [ ] If BPC quotes Option B (drywall + paint + flooring): no managed-via-subs needed beyond firestopping (Section 078400) and rough-carp prep (Section 061053)
- [ ] If BPC quotes Option C (rolled-up multi-trade): identify subs for casework (064101 plam, not Royston), glazing (088813 fire-rated), HVAC (Div 23 — Tyler-area subs maybe; EMA is the engineer of record), plumbing (Div 22 — shampoo bowls per 224001), electrical (Div 26 — high station-circuit density)
- [ ] Sub outreach 3+ quotes per critical trade — target deadline 5 business days before HCS due (i.e., ~2026-06-15) for clean review

## Gate 5 — Pricing build

- [ ] Pull McLennan-County **Davis-Bacon wage determination** (sam.gov, building-construction schedule) before any labor pricing — cosmetology renovation is "building construction" not "residential"
- [ ] Self-perform pricing (drywall 092116, paint 099123, resilient flooring 096500/096519, fluid-applied flooring 096700, possibly door hardware install 087100) priced at DBA wage rates for each trade classification (drywall finisher / painter / floor layer / etc.)
- [ ] **Mobilization premium** — Waco is ~95 mi from BPC HQ; price travel + per diem honestly. Call out a separate mob/demob line in BPC's HCS-internal template; HCS will roll it into MCC's lump-sum
- [ ] Sub-managed pricing at sub low + BPC OH&P markup
- [ ] **Alternate 1** pricing per Section 012300 in PM (drawings: MD2.1A, MH2.2A, ED2.1A, EL2.1A, A6.3, A7.3, A7.4) — likely a finishes/lighting upgrade variant; do not skip
- [ ] Allowances per Section 012100 — read in PM; MCC may have specified contingency allowances that BPC's quote should accommodate
- [ ] **Cosmetology-specific cost drivers** to confirm in spec book: shampoo bowl count (224001), station electrical circuit density (262000 / 262726), HVAC exhaust if cosmetology-specific, fluid-applied floor SF + chemical resistance grade
- [ ] Asbestos / lead-paint survey inclusion or exclusion — surface explicitly. Phase-4 of an older campus building may have legacy materials behind partitions; BPC must either include hazmat survey scope or exclude it explicitly so HCS can carry the risk
- [ ] Internal pricing review with Rocky before submission

## Gate 6 — Sub-quote package to HCS

- [ ] Fill HCS's internal sub-pricing template (line-itemized) covering BPC's full quoted scope
- [ ] Detailed-pricing supplement: BPC's standard takeoff workbook, formatted to map cleanly to HCS's template rows
- [ ] Note: the MCC Form 004213 is a single-lump-sum form — BPC does NOT fill 004213 (HCS does, after rolling up subs)
- [ ] Math double-check
- [ ] Sign / initial wherever HCS's template requires

## Gate 7 — Submission to HCS (2026-06-22 by 10:00 CT)

- [ ] Confirm submission channel with HCS (likely email to HCS Estimating; phone 254-829-3200 to confirm address before sending)
- [ ] Send pricing **at least 4 hours before the 10:00 CT deadline** — email-attachment slip is the largest risk
- [ ] Save email confirmation + read-receipt
- [ ] Internal copy filed at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\HCS\05302026-mcc-cosmetology\submitted\`

## Watch items

- HCS may post addenda directly into the Box folder; **check daily 2026-06-15 → 2026-06-22**. Re-pull the entire ZIP, diff `attachments/` against the committed copy.
- Spec §1.01 carries non-cosmetology language ("netting and artificial turf") — flag to HCS for RFI to RBDR as the first cleanup item before pricing build
- Cosmetology classrooms are highly trade-specific (shampoo bowl plumbing per 224001, station electrical per 262xxx, fluid-applied chemical-resistant flooring per 096700) — these are spec'd in the project manual; pull the actual product manufacturers + alternates from each section before any sub outreach
- The 95-mi geographic stretch + 5% MCC scoring weight on "office location close to college" make BPC's quote materially more expensive than a Waco-domiciled GC's quote unless BPC's HUB story compensates. HUB cert is now active (renewed 2026-05-30 per user); capture the new expiration date so HCS's MCC roll-up cites a specific date
