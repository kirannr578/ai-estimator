# Playbook — Federal SBA RFQ / RFP, LPTA

> **Exemplar bid:** [`bids/usfws-san-marcos-140FC126R0017/`](../../bids/usfws-san-marcos-140FC126R0017/) — USFWS, Construction A/E Team 1, San Marcos ARC Shop & 2 Stall Garage Building, 100% Total Small Business Set-Aside, LPTA, magnitude $100K–$250K, 60-day period of performance.
>
> **Matching workspace template:** [`bids/_TEMPLATES/federal-sba-rfq-lpta/`](../../bids/_TEMPLATES/federal-sba-rfq-lpta/)

## 1. Procurement description

Federal civilian and DoD construction agencies use **set-aside Request for Quotes / Proposals (RFQs / RFPs) under the FAR Small Business Programs (FAR Part 19)** to drive small-business participation in construction work that's typically under $7M. The dominant award flavor in the sub-$500K band is **Lowest-Price-Technically-Acceptable (LPTA)** per FAR 15.101-2 — the contract goes to the lowest-priced offeror that clears a Pass/Fail technical-acceptability gate. Tradeoffs between price and performance are **explicitly forbidden** on LPTA.

When you'll see it:

- USFWS / USACE / NPS / GSA / DoD small construction (rehab, replace, repair tasks) at sub-$500K bid envelopes
- 100% Small Business set-aside (FAR 52.219-6), sometimes layered with WOSB / SDVOSB / 8(a) / HUBZone narrowing
- Firm-Fixed-Price (FAR 52.216-1) construction contract
- Period of performance typically 30–180 calendar days from NTP

When it's a different beast (use a different playbook):

- Federal "best-value" / "tradeoff" RFP — same FAR Part 15 backbone but the technical narrative is scored, not Pass/Fail
- Federal IDIQ / JOC — pricing is by Unit Price Book, not bid-schedule CLINs
- Federal A/E commission (FAR Part 36.6) — Brooks Act qualifications-based selection, not price-based

## 2. Typical evaluation criteria

| Factor | Weight | How it's evaluated |
|---|---|---|
| **Price** | Sole award discriminator | Total evaluated price; CO ranks all Technically Acceptable offers and awards to the lowest |
| **Past performance** | Pass / Fail | Minimum 2 examples of recent (last 3 yrs) general construction projects similar in size, scope, and complexity to the SOW. **Subcontractor past performance counts equally per FAR M.1.4.B.f** — borrow the OH-door sub or the metal-roof sub's past performance if needed |
| **Bondability** | Pass / Fail | Surety commitment letter for P&P bonds at this contract magnitude |
| **SAM Reps & Certs** | Pass / Fail | Current (≤ 12 months) per FAR 52.204-8(d) |
| **Bid Guarantee** | Pass / Fail | Proper form per FAR 52.228-1 |
| **CLIN pricing completeness** | Pass / Fail | Every CLIN priced (unit + extended + grand total) per FAR L.2.1.2.D + M.1.9 |
| **No exceptions to the SOW** | Pass / Fail | Exceptions in priced proposal = automatic Fail; raise as pre-submission RFI instead |

**The shortest defensible Volume II Passes.** Anything past 3–5 pages of narrative either (a) adds zero scoring upside or (b) introduces an unintended exception that flips Pass → Fail. Don't write a QC plan, safety plan, schedule narrative, or "Why us" pitch unless explicitly requested in Section L.

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| SAM.gov registration active | Yes | Active (user-confirmed 2026-05-23) | ⚠️ Expiration date TBD — verify before each federal bid |
| Unique Entity ID (UEI) | 12-char alphanumeric, on SAM record | `LM4YHVQ71QG7` | ✅ |
| CAGE Code | DLA-issued | `9LET0` | ✅ |
| NAICS 236220 in registered NAICS list | Yes | Yes (primary for renovation pipeline) | ✅ |
| Small-business assertion on NAICS 236220 | Yes (≤ $45M 3-yr avg revenue) | Self-attested small | ⚠️ Confirm annual revenue ≤ $45M before each bid; SBE cert (DFW MSDC DL09279) expired 2024-08-31 per source |
| Reps & Certs current per FAR 52.204-8 | Yes (≤ 12 months) | Unknown — needs SAM check | ⚠️ Verify before each bid |
| EFT banking info current in SAM | Yes | Unknown | ⚠️ Verify |
| TIN matches IRS | Yes | EIN 87-4292998 | ⚠️ Verify in SAM |
| FASCSA reps (52.204-29) | Yes | Unknown | ⚠️ Verify |
| Section 889 reps (52.204-24/-25/-26) | Yes (does not use / will not provide) | Boilerplate yes | ⚠️ Verify in SAM |
| Buy American reps (52.225-2/-20/-25) | Yes | Boilerplate yes | ⚠️ Verify in SAM |
| FAR 52.204-21 Basic Safeguarding (17 NIST SP 800-171 subset controls) | Implemented at firm IT level | Likely; minimal validation done | ⚠️ One-time verification |
| Bond capacity for sub-$500K federal jobs | Single-project capacity ≥ $250K, aggregate ≥ project plus current bonded backlog | Floor ≥ $1M established by Lavon RV Park performance bond | ✅ Single-project; aggregate unknown — confirm with bonding agent |
| Commercial GL insurance (federal small-construction baseline: $1M / $2M) | $1M occurrence / $2M aggregate | $1M / $2M on policy SBCC-042443-00 — **expired 2024-09-25 per source; user to verify renewal** | 🔴 Surface current COI |
| Auto + WC + Umbrella + Builder's Risk | Per federal baseline | WC / Auto / Umbrella / BR: not found in BPC extracted files | 🔴 Surface current COIs |
| Past performance — ≥ 2 federal or commercial-equivalent comparable projects | Yes | Lavon RV Park ($1.05M, 30-lot park new-build, $1M perf bond, in execution); Hindu Temple of Southlake (~10,700 SF reno, in execution); Holiday Inn Hall Park (commercial reno, no recorded $); 250-500+ SFH portfolio (specialty trade sub). Per [`firm-profile.json → past_project_selection_rules`](../firm-profile.json) USFWS-class picks are Lavon + Hindu Temple + Holiday Inn. | ⚠️ Sufficient quantity; verify owner-side reference contacts are still in role before each submission |

## 4. Required compliance docs checklist (for any federal-SBA-LPTA bid)

See [`firm/compliance/README.md`](../compliance/README.md) for the registry. Per-bid checklist:

- [ ] SAM "Entity Information" PDF, pulled within 24 hours of submission
- [ ] SAM Reps & Certs printout (or 52.204-8(d) incorporation-by-reference page if Reps are ≤ 12 months current)
- [ ] Current GL COI naming the issuing agency as Additional Insured + primary/non-contributory + waiver of subrogation
- [ ] Current WC + Auto + Umbrella + Builder's Risk COIs
- [ ] Surety bondability commitment letter on a Treasury Circular 570 surety, signed
- [ ] Bid bond (SF 24 or surety equivalent) at 20% of bid OR $1M cap
- [ ] Buy American Certificate (FAR 52.225-4) signed
- [ ] Past-performance package — 2 examples, each ≤ 1 paragraph narrative + table of facts (owner, $ value, contact, completion date, scope summary)
- [ ] DBA / Davis-Bacon WD acknowledgment (transcribed wage rates from the WD attached to the RFP)
- [ ] Affirmative-Action / OFCCP rep (52.222-22 / 52.222-25) if firm > 50 employees and over EEO threshold

## 5. Standard solicitation forms (the SF 1449 / SF 1442 family)

| Form | When it's used | What it does |
|---|---|---|
| **SF 1442** Solicitation, Offer and Award (Construction, Alteration, or Repair) | Default for construction RFPs | Blocks 14–20C on the bid side: offeror name + UEI/CAGE + ZIP, phone, signature, acceptance period |
| **SF 1449** Solicitation/Contract/Order for Commercial Items | Commercial-item RFQs (FAR Part 12) — rare for construction | Same fields, different layout |
| **SF 30** Amendment of Solicitation / Modification of Contract | Issued by the agency for any RFI response or scope clarification | Acknowledge on SF 1442 block 19, attach signed SF 30 page in submission |
| **SF 24** Bid Bond | Default bid-guarantee form | Surety on Treasury Circular 570 list |
| **SF 25** Performance Bond | At award if contract > $150K | 100% of contract value |
| **SF 25A** Payment Bond | At award if contract > $150K | 100% of contract value |
| **SF 254 / SF 330** A/E Qualifications | A/E commissions only — not used for construction bids | — |
| **OF 312** Declaration for Federal Employment | Not used at bid stage | — |
| **DI-137** Release of Claims | Submitted with final invoice (DOI / USFWS-style) | One-line oversight kicks final payment back |

## 6. Submission portals

- **SAM.gov** (`https://sam.gov/`) — primary discovery portal. All amendments are posted here. **Check daily through the due date.**
- **PIEE / Wide Area Workflow** (`https://piee.eb.mil/`) — DoD submission portal for DLA / USACE / USAF / USN small construction
- **Agency email** — common for sub-$500K civilian work (USFWS, NPS, FWS); the RFP names a Contract Specialist mailbox at the issuing office. Send to the published address(es) + CC the CO. If two addresses appear in the same RFP (e.g. `john_ferrall@fws.gov` and `john_ferrall@ios.doi.gov` on the USFWS San Marcos), send to **both** and CC the CO; raise it as an RFI.
- **Beta SAM legacy archive** — for cross-referencing prior awards / clearing prices in the same agency / NAICS

## 7. Submission format conventions

| Convention | Federal-SBA-LPTA norm | Source |
|---|---|---|
| Volume split | Volume I — Price; Volume II — Technical/Past Performance | FAR L.2.1.1.A |
| File format | PDF; one PDF per volume | RFP §L |
| File naming | `<SolNumber>_Part_I_Price_Proposal.pdf`, `<SolNumber>_Part_II_Technical.pdf` | Convention; check RFP §L |
| Email subject | `Proposal Submission-<SolNumber>` exactly | RFP cover |
| Page limit | None on price proposal; 3–5 pages target for Volume II | Pass/Fail discipline |
| Wet ink vs e-signature on SF 1442 | E-signature acceptable post-2022 unless RFP explicitly forbids | Federal Acquisition Streamlining Act |
| Acceptance period (block 13d) | ≥ 90 calendar days | RFP cover; default to minimum if blank |
| Delivery cutoff time | Local time of the issuing office (often EDT/EST since DC); 5:00 PM is the common hard cutoff | RFP cover |
| Late submission policy | Rejected; FAR 52.215-1(c)(3) allows narrow exceptions for government mishandling | FAR 52.215-1 |

**Send the proposal 30+ minutes early** to leave room for email-system delays.

## 8. Typical timeline

| Phase | Days from RFP release | Notes |
|---|---|---|
| RFP release on SAM.gov | T-0 | |
| Site visit window (often non-mandatory but recommended) | T+5 to T+10 | RSVP required; ask measurement questions in person |
| RFI cutoff | T+15 to T+20 | After cutoff, responses "may not be received" — file early |
| Proposal due | T+30 to T+45 (sub-$500K small-construction LPTA) | |
| CO evaluation | 2–4 weeks | Pass/Fail past perf + bondability + price reasonableness |
| Award notice | T+45 to T+90 from RFP release | Posted on SAM |
| NTP issuance | Within 10 days of award | RFP F.1.0 |
| Performance period | Per RFP — typical 60–180 calendar days | Liquidated damages rarely published on sub-$500K but FAR 52.249-10 default-termination right is always present |

## 9. Common pitfalls

1. **SAM-registration lapse.** Annual cycle for Reps & Certs is easy to miss. A lapsed SAM kills the bid on its face per FAR 52.204-7 + RFP L.1.0. Fix takes 3–10 business days — too late for an in-flight bid.
2. **Wrong NAICS size assertion.** If the firm has self-certified small on NAICS 236220 in SAM but actual 3-yr avg revenue exceeds the $45M cap, the bid is non-responsive and exposes the firm to FAR 52.219-1(c)(5) "misrepresentation" liability.
3. **Davis-Bacon WD freshness.** The WD effective on the day of bid opening governs the contract. If the agency issues a new WD via amendment, acknowledge it on SF 1442 block 19 and re-price labor accordingly.
4. **Certified-payroll administrative lag.** Weekly WH-347 for prime + every sub tier. For a 60-day project that's 8–9 weeks of payroll administration; build PM-hours into general conditions.
5. **Bonding lag.** Bid bond, P&P commitment letter, and surety capacity letter all take 3–5 business days. Order **all three** at the same time, on the same day, against an envelope that's $2K above your highest-realistic bid.
6. **Buy American non-compliance** on iron-and-steel construction material (24-ga roof panels, OH-door panels, hollow-metal doors, sheet-metal gutters). 20% domestic-content price differential per FAR 52.225-10. If forced non-domestic, file FAR 52.225-9(b)(3) determination request **before** submission.
7. **Site-visit no-show.** On LPTA-thin pricing, the site visit is where you buy down takeoff risk. Missing it forces a wider contingency that pushes the bid out of the competitive band.
8. **Section B copy-paste errors in the RFP itself.** USFWS / DoI / DoD RFPs often have boilerplate that survived from a prior solicitation (the USFWS San Marcos RFP carried a "Pelican Island NWR" prose block in Section B). Read every page; flag discrepancies in an RFI; document the operative scope (the CLINs + SOW are typically authoritative) in the proposal cover letter.
9. **15% on-site self-perform requirement** (FAR 52.236-1). Design the crew loading so > 15% of direct cost is delivered with firm employees on site, documented in certified payroll.
10. **Unbalanced bid / unreasonably low** (FAR 15.404-1(d) + (g)(2)). Bidding below the magnitude floor or front-loading early CLINs can get the bid rejected as non-responsible.

## 10. LPTA pricing discipline

| Component | % of direct cost | Notes |
|---|---|---|
| Direct cost (subs + materials + self-perform labor) | 100% | Site visit + ≥ 2 sub quotes per CLIN to tighten |
| General conditions / supervision | 8–14% | Counts toward 15% on-site self-perform |
| Bonds (bid + P&P) | 1.5–2.5% | Per surety quote |
| Insurance | 2–4% | If carried as a percentage |
| DBA labor-burden uplift | 0–4% | Only if firm's labor rates are sub-prevailing |
| Contingency | 3–5% | LPTA-thin; bump to 7–8% if site visit missed |
| Overhead | 7–10% | Floor of the range on a competitive LPTA |
| Profit | 3–6% | LPTA-thin; up to 8% only if defensible past-performance moat exists |
| **Total markup over direct** | **~25–40%** | Direct-to-bid multiplier of ~1.25–1.40 |

**Don't bid below the magnitude floor** (FAR 15.404-1(d) "unreasonably low") — bid at the floor + 5–10% at most.

**Don't pad above 7% net profit** unless you have a specific reason — every dollar over true cost gives the next offeror a window to underbid you.

## 11. Reusable language blocks

These are paste-ready blocks pulled from the USFWS San Marcos proposal package. They live in [`firm/proposal-library/`](../proposal-library/README.md); the cross-references below show which file holds the canonical copy.

| Block | Where it lives | When to use |
|---|---|---|
| Federal-SBA-LPTA exec-summary opening (Volume I cover letter) | [`firm/proposal-library/exec-summary-archetypes/federal-sba-lpta.md`](../proposal-library/exec-summary-archetypes/federal-sba-lpta.md) | Front of Volume I; cover-letter only — no exceptions, no narrative |
| SAM Reps & Certs incorporation page (52.204-8(d)) | [`firm/proposal-library/boilerplate/sam-reps-and-certs-incorporation.md`](../proposal-library/boilerplate/safety-plan-one-pager.md) (see boilerplate index) | Volume II — final page |
| Past-performance 1-paragraph template | [`firm/proposal-library/past-performance/`](../proposal-library/past-performance/) — pick 2 of {Lavon RV Park, Holiday Inn Hall Park, Hindu Temple of Southlake} per [`firm-profile.json → past_project_selection_rules`](../firm-profile.json) | Volume II — Past Performance sub-volume |
| Key-personnel one-pager (Principal in Charge, PM, Super, Safety, QA/QC) | [`firm/proposal-library/key-personnel/`](../proposal-library/key-personnel/) | Volume II only if RFP explicitly asks for key personnel (uncommon on LPTA); trim if not |
| Safety-plan one-pager | [`firm/proposal-library/boilerplate/safety-plan-one-pager.md`](../proposal-library/boilerplate/safety-plan-one-pager.md) | Submittal stage post-award (per FAR 52.236-13); NOT in proposal |
| Schedule-narrative skeleton | [`firm/proposal-library/boilerplate/schedule-narrative-skeleton.md`](../proposal-library/boilerplate/schedule-narrative-skeleton.md) | Submittal stage post-award per the NTP+14 schedule; NOT in proposal |

## 12. Cross-references

- **Workspace template:** [`bids/_TEMPLATES/federal-sba-rfq-lpta/`](../../bids/_TEMPLATES/federal-sba-rfq-lpta/)
- **Scope templates for federal renovation work:** [`firm/scope-templates/arc-rehab-steel-building.md`](../scope-templates/arc-rehab-steel-building.md), [`firm/scope-templates/office-tenant-refurb.md`](../scope-templates/office-tenant-refurb.md) where the federal scope overlaps the office-finish-out pattern
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Exemplar shipped bid:** [`bids/usfws-san-marcos-140FC126R0017/`](../../bids/usfws-san-marcos-140FC126R0017/)
