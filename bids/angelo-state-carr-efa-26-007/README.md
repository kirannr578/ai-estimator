# Bid prep — Angelo State University, Carr EFA Dressing Room Renovation

**Solicitation:** 26-007 (ESBD 516718)
**Agency / Sponsor:** Angelo State University (member of the Texas Tech University System)
**Project:** Carr Education and Fine Arts (EFA) Building — Dressing Room Renovation
**Location:** ASU Station #10924, San Angelo, TX 76909 (Tom Green County)
**Procurement vehicle:** Request for Competitive Sealed Proposal (RFCSP) — Tex. Gov't Code Ch. 2269
**Status:** **DRAFT / READY FOR QUANTITIES** — we have the full RFCSP package (RFCSP narrative + Attachments A–F.1). The only Priority-1 missing item is the construction drawing set + full project manual. The HSP is partially draftable today from the actual TX HSP form in Attachment D.

---

## PROPOSAL STATUS

**`DRAFT — pending drawings + sub quotes + signatures`**

A complete review-ready proposal package has been drafted in `proposal/` (13 files) with companion outreach drafts in `outreach/` (7 files) and a CSI-grouped pricing scaffold at `price-sheet-skeleton.json`. Everything that does NOT depend on drawings, sub quotes, or firm-internal data is drafted to a defensible state. Every place that needs firm-internal data carries a `[USER TO FILL]` marker.

### Remaining gates to lock before submission

| # | Gate | Owner | Target close date | Status |
|---|---|---|---|---|
| 1 | **Drawings + full project manual** received from ASU FP&C; takeoff quantities filled in `takeoff-template.json` and `price-sheet-skeleton.json`; sub quotes solicited and received | Bid-prep lead + Estimator | 2026-05-27 drawings; 2026-05-29 sub quotes | 🔴 Blocked on drawings |
| 2 | **HUB outreach window closes 5 business days before HSP due** (2026-06-01 for a 2026-06-08 HSP) — ≥3 HUB subs solicited per trade, ad placement in ≥2 publications, GFE binder in flight | HUB compliance lead | **2026-06-01** | 🟡 Outreach drafts ready in `outreach/05-email-hub-subs-template.md`; send today |
| 3 | **Owner-furnished demarcation confirmed in writing** by Samuel Guevara (R-02) — so sub-quotes go out with clean scope | Bid-prep lead | 2026-05-25 | 🟡 Email drafted in `outreach/02-email-samuel-guevara-owner-furnished.md`; send today |

Also tracking from `07-risk-register.md` § E (the bid-level go/no-go gate):

- R-01 — pre-response meeting eligibility (CRITICAL; could be a no-go gate)
- R-07 — bonding capacity (resolve via bonding agent today via `outreach/03-email-bonding-agent.md`)
- R-08 — Carr EFA production calendar (resolve via Samuel)
- R-11 — UGSC Art. 5 insurance limits within carrier capacity (resolve via `outreach/04-email-insurance-broker.md`)

### Top 5 [USER TO FILL] items needed by Monday morning

1. **Signing officer + bid-prep lead identity.** Name, title, phone, email for the officer who will sign Attachment A in blue ink and the bid-prep lead who fronts all outreach. Drives signature blocks across `proposal/01-executive-summary.md`, all 7 outreach drafts, and the Attachment A fill guide.
2. **Bonding agent + insurance broker contact info.** Email + phone + firm names. Unblocks `outreach/03-email-bonding-agent.md` and `outreach/04-email-insurance-broker.md` — both should go out today. R-07 + R-11 close on the responses.
3. **3–5 past-performance project references with current owner contacts.** Drives `proposal/04-past-performance.md`. Prioritize TTUS or other TX higher-ed renovation, performing-arts/theater work, occupied-building MEP-replacement renovations. Owner contacts must be verified current (within 7 days of submission).
4. **PM + Superintendent + Safety lead identification** for the 2026-07-01 → 2026-11-02 construction window, with résumés and OSHA 30 / OSHA 10 current training dates. Drives `proposal/03-project-team.md` and `proposal/07-safety-plan.md`. Also: most-recent 3-year EMR letter from broker.
5. **Firm's TX HUB certification status** (Yes + cert # OR No) — affects HSP Section 1 Block B and the cover letter's "why us" paragraph. Plus the firm's exact legal name as it appears on the TX Comptroller's Taxable Entity Search and W-9 (used to validate consistency across Attachment A, bid bond, ACORDs, CIQ, HB 1295, and the HSP form).

---

## Headline numbers

| Item | Value | Source |
|---|---|---|
| Published owner budget | ~$500,000 | RFCSP § Budget (triage canvas card #5) |
| Estimated total contract value | **$425K – $560K** likely envelope; mid-point $485K | Inferred from $/SF range in `price-references.md` against an assumed 2,000–3,000 SF dressing-room footprint |
| Owner-required cash/contingency allowance | **$25,000** carried as a separate line on Attachment A | `exports/calibration_v3/estimate.json` `bid_packages[3].unit_prices[0]` |
| Headline $/SF range we landed on | **$165 – $260 / SF** for dressing-room reno with full MEP demo & replace in a TX university performing-arts building | `price-references.md` |
| Pre-response meeting | **2026-05-20, 2:00 PM CST — MISSED (today is 2026-05-22)** | RFCSP § Pre-Response Conference |
| Proposals due | **2026-06-05, 2:00 PM CST** (T-14 days) | RFCSP cover |
| HSP due (separate deadline) | **2026-06-08, 5:00 PM CST** (T-17 days; 3 calendar days AFTER the proposal) | RFCSP § HUB Subcontracting Plan |
| Construction start | 2026-07-01 | RFCSP § Time of Performance |
| Substantial completion | 2026-11-02 (~124 calendar days, ≈ 4 months) | RFCSP § Time of Performance |
| Liquidated damages | **$250 / calendar day** past substantial completion | RFCSP / UGSC LD article |
| Bid bond | **5%** of base proposal if total > $25K | UGSC Art. 6 / Tex. Gov't Code Ch. 2253 |
| Payment Bond | **100%** of contract value if > $25K | UGSC Art. 6 |
| Performance Bond | **100%** of contract value if > $100K | UGSC Art. 6 |
| HUB Subcontracting Plan | **Required — failure = automatic rejection.** ASU sample CSA carries a 30% HUB commitment placeholder; statewide TX goal for special-trade construction is 21.1%. | Attachment D + Attachment B.2 |
| NAICS (inferred — not stated on the RFCSP) | 236220 — Commercial & Institutional Building Construction | Inferred from scope |
| Owner-furnished (NOT in our scope) | Technology systems, network/data cabling, equipment install, FF&E / furniture, fire-suppression system | RFCSP § Scope |

---

## Top 5 actions for tomorrow

1. **Call Samuel Guevara (ASU Facilities Planning & Construction) today / first thing tomorrow.** The May 20 pre-response meeting is past; we need to (a) confirm it was non-mandatory so we remain eligible to propose, (b) request the sign-in sheet, attendee Q&A, and any meeting minutes, and (c) confirm whether site access can be arranged before the June 5 due date. Suggested phone + email draft in `contacts.md`.
2. **Download the drawing set + full project manual / specifications** from the ESBD / ASU procurement portal. The 7 attachments we have are the RFP package; the architectural and MEP drawings + the full spec book are the #1 missing item per `03-missing-documents.md`. Without drawings we cannot run a real takeoff against `takeoff-template.json`.
3. **Start HSP outreach to ≥3 HUB subs per major trade today** — demo, drywall/framing, flooring, painting, electrical, HVAC, plumbing, finish carpentry/millwork, ceilings. The HSP is due 2026-06-08 (3 days AFTER proposal) and good-faith-effort (GFE) documentation must be dated and back-walkable. See `05-hsp-plan.md` § D for the per-trade CMBL search recipe + outreach packet template.
4. **Notify bonding agent** of the bid (~$485K envelope; bid bond 5%, P&P bonds 100% on award). Reserve capacity by 2026-05-27 and confirm turnaround time on a TTUS-format bid bond. Note ASU is a TTUS member institution; bid bond must be payable to "The Board of Regents of the Texas Tech University System." See `02-bid-prep-checklist.md` § A.
5. **Confirm insurance carrier can ride to UGSC Art. 5 limits** — GL $1M / $2M, Auto $1M, WC statutory + Employer's $1M, Builder's Risk (likely owner-provided; confirm), Umbrella $5M typical. ASU/TTUS must appear as additional insured with waiver of subrogation; named-insured ACORD must be issued **before any work begins**. See `08-contract-terms-flags.md` § Insurance.

---

## What's in this workspace

- [x] `README.md` — you are here
- [x] `01-overview.md` — solicitation identity, dates, contacts, scope summary
- [x] `02-bid-prep-checklist.md` — forms / registrations / insurance / bonding / sub coverage with status
- [x] `03-missing-documents.md` — what we still need, priority-tiered, with stand-ins
- [x] `04-scope-of-work.md` — trade-by-trade scope per the RFCSP, with an explicit contractor-vs-owner scope boundary
- [x] `05-hsp-plan.md` — actual HSP draft against the TX HSP form in Attachment D + per-trade HUB allocation + outreach playbook
- [x] `06-evaluation-strategy.md` — CSP evaluation factors + what to emphasize
- [x] `07-risk-register.md` — bid-specific risks + mitigations (top-tier: missed pre-response meeting, HSP GFE, owner-furnished scope confusion, hidden existing conditions)
- [x] `08-contract-terms-flags.md` — notable UGSC + Sample CSA clauses to negotiate or accept (insurance, indemnity, LDs, retainage, differing site conditions, change-order pricing, termination for convenience, dispute resolution venue)
- [x] `takeoff-template.json` — structured skeleton per `core/schemas.py` `Estimate` / `CostLine`, all line items pre-populated with `quantity: null`, `unit: "<TBD per drawings>"`, grouped by CSI division
- [x] `price-references.md` — $/SF benchmarks + comparable past-project examples for university dressing-room and theater-support renovations
- [x] `contacts.md` — Samuel Guevara + Tracie Howell + ASU procurement + TTUS HUB POC + suggested outreach drafts
- [x] `timeline.md` — backwards-planned schedule from the 2026-06-05 proposal deadline AND the 2026-06-08 HSP deadline
- [x] `prevailing-wages.md` — Tom Green County trade-by-trade wage table distilled from Attachment F.1

## What's blocked

- [ ] **Real takeoff quantities** — need the architectural + MEP drawings + finish schedule + door schedule from the ASU procurement portal
- [ ] **Final HSP form completion** — line-item vendor names + HUB cert numbers + dollar values; can only be filled in after sub-quotes arrive
- [ ] **Sub quotes** — can't solicit substantively until drawings ship; in the meantime, place "scope ahead, drawings to follow" GFE outreach (see `05-hsp-plan.md`)
- [ ] **Pre-response meeting record** — we missed 2026-05-20; awaiting Samuel Guevara's reply with sign-in sheet / Q&A
- [ ] **Site walk of Carr EFA dressing rooms** — request via Samuel; existing-conditions risk is non-trivial on a 1960s-era performing-arts building
- [ ] **Owner-furnished item demarcation diagram** — RFCSP narrative lists tech, cabling, equipment install, furniture, and fire suppression as owner-furnished, but the cleanest version of "where our scope ends and theirs starts" is in the drawings/specs we don't have yet

---

## Hard rules respected in this workspace

- All work product lives under `bids/angelo-state-carr-efa-26-007/`. No edits to `core/`, `app.py`, `analyze.py`, `prompts/`, `tests/`, `requirements.txt`, repo-root `README.md`, or any other path that F1/F3 might rebase over.
- Sibling bid-prep folders (`bids/tamu-harrington-2025-06813/`, `bids/usfws-san-marcos-140FC126R0017/` if/when created) were not touched.
- `analyze.py` was **not** run. We reused `exports/calibration_v3/estimate.json` (the v3 pipeline already extracted all 7 Angelo State attachments into `bid_packages[3]`, `bid_packages[4]`, `bid_packages[6]`, `bid_packages[7]`, `bid_packages[8]`, `bid_packages[10]`, `bid_packages[11]`). `exports/calibration_v3/{estimate.xlsx, quote.pdf, CALIBRATION_REPORT.md, run_log.txt, analyze_stdout.log}` were not modified.
- `.env` and any API keys were **not** read, printed, or referenced.
- `inbox/` source PDFs were read (via the `Read` tool) but not copied or committed; the `inbox/` tree remains untracked per repo convention.
- No fictional firm-internal data — every place that needs the firm's own data (specific insurance carrier, bonding capacity, named past projects, named HUB subs already in our rolodex) carries a `[USER TO FILL]` marker.

---

## File map

```
bids/angelo-state-carr-efa-26-007/
├─ README.md                          ← you are here (includes PROPOSAL STATUS)
├─ 01-overview.md
├─ 02-bid-prep-checklist.md
├─ 03-missing-documents.md
├─ 04-scope-of-work.md
├─ 05-hsp-plan.md
├─ 06-evaluation-strategy.md
├─ 07-risk-register.md
├─ 08-contract-terms-flags.md
├─ takeoff-template.json
├─ price-references.md
├─ contacts.md
├─ timeline.md
├─ prevailing-wages.md
├─ price-sheet-skeleton.json          ← CSI-grouped pricing scaffold (post-takeoff fill-in)
├─ proposal/                          ← 13-file review-ready proposal-draft package
│  ├─ 00-readme.md                       Submission overview + signing/sealing/delivery
│  ├─ 01-executive-summary.md            Cover letter / 1-page exec summary
│  ├─ 02-technical-approach.md           3–5 page phased work plan + owner-furnished demarcation
│  ├─ 03-project-team.md                 Org chart + key personnel template
│  ├─ 04-past-performance.md             Template for 3–5 similar projects
│  ├─ 05-schedule-narrative.md           Backwards-planned from 11/2; 13-day LD float strategy
│  ├─ 06-quality-control-plan.md         3-phase QC + submittal log + close-out
│  ├─ 07-safety-plan.md                  OSHA 1926 + 8 site-specific hazards
│  ├─ 08-attachment-A-fill-guide.md      Section-by-section fill guide
│  ├─ 09-attachment-D-hsp-form-guide.md  HSP form fill guide
│  ├─ 10-price-proposal.md               Base bid stack + unit prices (formulas)
│  ├─ 11-submission-checklist.md         Hard checklist + 2-person QC pass
│  └─ 12-bid-bond-letter-template.md     Letter template to bonding agent
├─ outreach/                          ← 7 ready-to-send email drafts
│  ├─ 01-email-samuel-guevara-eligibility.md       Confirm eligibility post pre-response miss
│  ├─ 02-email-samuel-guevara-owner-furnished.md   Written demarcation request
│  ├─ 03-email-bonding-agent.md                    Reserve $485K envelope; TTUS bond form
│  ├─ 04-email-insurance-broker.md                 UGSC Art. 5 cert by 7/1 NTP
│  ├─ 05-email-hub-subs-template.md                Per-trade HUB sub outreach (customize per send)
│  ├─ 06-email-asu-procurement-clarifications.md   28-question Q&A list
│  └─ 07-call-script-samuel-guevara.md             Phone backup script for Email #01
```

`local/` — if you create a sibling `bids/angelo-state-carr-efa-26-007/local/` folder for sub-quote PDFs, bonding-agent paperwork, scratch spreadsheets, hub-outreach logs, or anything else that shouldn't be committed, the workspace `.gitignore` rule `bids/*/local/` keeps it out of git.
