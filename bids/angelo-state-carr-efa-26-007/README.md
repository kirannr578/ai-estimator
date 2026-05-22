# Bid prep — Angelo State University, Carr EFA Dressing Room Renovation

**Solicitation:** 26-007 (ESBD 516718)
**Agency / Sponsor:** Angelo State University (member of the Texas Tech University System)
**Project:** Carr Education and Fine Arts (EFA) Building — Dressing Room Renovation
**Location:** ASU Station #10924, San Angelo, TX 76909 (Tom Green County)
**Procurement vehicle:** Request for Competitive Sealed Proposal (RFCSP) — Tex. Gov't Code Ch. 2269
**Status:** **DRAFT / READY FOR QUANTITIES** — we have the full RFCSP package (RFCSP narrative + Attachments A–F.1). The only Priority-1 missing item is the construction drawing set + full project manual. The HSP is partially draftable today from the actual TX HSP form in Attachment D.

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
├─ README.md                          ← you are here
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
└─ prevailing-wages.md
```

`local/` — if you create a sibling `bids/angelo-state-carr-efa-26-007/local/` folder for sub-quote PDFs, bonding-agent paperwork, scratch spreadsheets, hub-outreach logs, or anything else that shouldn't be committed, the workspace `.gitignore` rule `bids/*/local/` keeps it out of git.
