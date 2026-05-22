# Bid prep — USFWS San Marcos Aquatic Resources Center, Rehabilitate Shop & 2 Stall Garage Building

**Solicitation:** 140FC126R0017
**Agency:** U.S. Fish & Wildlife Service, Division of Engineering (Construction A/E Team 1, Falls Church VA)
**Project:** Shop & 2-Stall Garage Building Rehabilitation — Asset #10006277
**Location:** San Marcos Aquatic Resources Center, 500 East McCarty Lane, San Marcos, TX 78666-1024 (Hays County)
**Status:** **DRAFT / READY FOR QUANTITIES + SITE VISIT** — full RFP, SOW, bid schedule, and Davis-Bacon WD in hand. Bid-schedule line items are mapped and structured; final pricing waits on (a) the May 27 or 28 site visit, and (b) sub quotes for the four items with no cost-DB hit.

---

## Headline numbers

| Item | Value | Source |
|---|---|---|
| Magnitude of construction (government estimate) | **$100,000 – $250,000** | RFP Section A + Sol_140FC126R0017 p.5 |
| Period of performance | **60 calendar days from NTP** (start within 10 days of NTP; mandatory completion) | FAR 52.211-10 in RFP Section A + Section F.1.0 |
| Proposal due | **Monday, June 22, 2026, 5:00 PM EDT** | SF1442 block 8 + RFP p.3 |
| RFI cutoff | **June 8, 2026, 5:00 PM EDT** | RFP p.3 + L.1.3 |
| Site visit (highly encouraged, not mandatory) | **May 27 or May 28, 2026, 8 AM – 4 PM CDT** | RFP p.3 + 52.236-27 |
| Set-aside | **100% Total Small Business Set-Aside** | SF1442 + Section A + 52.219-6 |
| NAICS / size standard | **236220 — Commercial & Institutional Building Construction**, **$45.0M** small-business size | 52.204-8(a) at RFP p.52 |
| Contract type | **Firm-Fixed Price**, single award | Section A + L.2.1.2 |
| Evaluation method | **Lowest Price Technically Acceptable (LPTA)** — Pass/Fail on technical+past-performance; tradeoffs explicitly NOT permitted | Section M.1.0–M.1.2 (RFP p.70) |
| Bid Guarantee (bid bond) | **20% of bid OR $1M, whichever is less** | 52.228-1 (RFP p.68) |
| Performance Bond + Payment Bond | **100% each** on award (contract > $150K threshold; magnitude says it likely is) | 52.228-15 (RFP p.47–48) |
| Self-perform | **At least 15% on-site with own organization** | 52.236-1 (RFP p.49) |
| Wage determination | **Davis-Bacon — Hays County, TX, Building Construction, WD TX20260254** (per attached SAM WD PDF filename) | Section H.15.0 + Section J Attachment 3 |
| Buy American — construction materials | Applies, with 20% domestic-preference price differential | 52.225-9 + 52.225-10 |
| Acceptance period | **Minimum 90 calendar days** from offer due date | RFP p.3 block 13d |

---

## What's complete in this workspace

- [x] `01-overview.md` — solicitation, location, dates, contacts, scope summary
- [x] `02-bid-prep-checklist.md` — SF 1442 + SAM.gov registration verification + reps & certs + bonding + insurance
- [x] `03-missing-documents.md` — drawings + spec narrative + any items not in the 4 attachments
- [x] `04-scope-of-work.md` — trade-by-trade from the SOW (8 items)
- [x] `05-bid-schedule-mapping.md` — the federal Bid Schedule items mapped to TakeoffItem rows + cost-DB matches
- [x] `06-evaluation-strategy.md` — **LPTA-specific** strategy (different shape from the TAMU / ASU RFCSP playbooks)
- [x] `07-risk-register.md` — bid-specific risks with mitigations
- [x] `08-far-clauses-flags.md` — FAR / DIAR clauses worth flagging on this small federal LPTA
- [x] `takeoff-template.json` — `Estimate`-shaped skeleton (per `core/schemas.py`) keyed to the 8 bid-schedule CLINs
- [x] `price-references.md` — $/SF and $/EA benchmarks for federal small-project shop/garage rehab
- [x] `contacts.md` — USFWS CO, CS, site-visit POC, COR/COTR, Field Inspector
- [x] `timeline.md` — backwards-planned from June 22 with site visit milestone on May 27 OR 28
- [x] `prevailing-wages.md` — Hays County DBA wage decision pointer + payroll mechanics

## What's blocked

- [ ] Final quantities — building footprint SF for roof + ceiling tile area beyond the 416 SF cited + total LF of gutter (SOW says ~110 LF; RFP says "Est. 110 LF"). Site visit on May 27/28 unlocks the last 20% of takeoff precision
- [ ] Sub quotes — OH door (item 1), gas-line cap (item 5), gutter (item 6), unit-heater removal/disposal (item 8) all need named-vendor pricing
- [ ] Bid bond — bonding agent needs a real total bid number before issuing the bid guarantee. Reserve capacity now against the upper-magnitude envelope
- [ ] **Davis-Bacon wage table extraction** — the attached SAM WD PDF (TX20260254) renders as garbled text in our extractor. Read it visually + transcribe rates into `prevailing-wages.md` (see ⚠️ flag at top of that file)
- [ ] **Internal SAM.gov status confirmation** — every line in `02-bid-prep-checklist.md` § A.1 is `[USER TO VERIFY]` until the firm logs into SAM.gov and confirms

---

## Tomorrow's top 5 actions — emphasize SAM.gov status + site visit RSVP

1. **🔴 Verify SAM.gov registration is active and current.** Log in to `https://sam.gov/`, confirm: (a) UEI is **Active**, (b) NAICS 236220 is in the registered list and SBSS-asserted as small at the $45M size standard, (c) Reps & Certs (52.204-8 / 52.212-3) are within the 12-month annual cycle, (d) CAGE code is active, (e) banking/EFT info is current, (f) TIN matches IRS records. **Without an active SAM registration, the bid is non-responsive on its face per FAR 52.204-7 / RFP L.1.0** — no matter how good the price.
2. **📅 RSVP the site visit by EOD May 26 (one business day buffer).** Email Katherine Bockrath (`Katherine_Bockrath@fws.gov`, 512-610-5597) requesting a slot on **May 27 OR May 28, 2026, between 8 AM and 4 PM CDT**. Confirm whether escort is required and what ID is needed (USFWS facility — civilian-controlled, not DoD — but still gate-locked at a national fish hatchery). Bring tape measure, camera, IR thermometer, moisture meter, ladder, notebook, and a roof-pitch finder for the 24-ga panel takeoff.
3. **🔧 Email the contracting officer to flag the Section B copy-paste error.** RFP pages 6–7 (Section B, Quote Schedule) describe items 0001–0008 for "Pelican Island NWR Replace Bunkhouse Roof, Indian River County, Vero Beach, Florida" — that is not this project. The actual CLINs (which match the SOW + Attachment 2 bid schedule for San Marcos) are correct, but the Project Description block above CLIN 0001 is wrong. Send a written RFI to `john_ferrall@fws.gov` (and copy `john_ferrall@ios.doi.gov` since L.1.2 uses a different email than p.3 of the RFP) before the June 8 cutoff so the CO can amend.
4. **📞 Notify bonding agent.** Reserve capacity against a **$250K bid envelope** (top of magnitude). Order: (a) bid guarantee — 20% of bid OR $1M, whichever is less, per 52.228-1, in firm-commitment form (bid bond, postal money order, certified check, cashier's check, irrevocable letter of credit, or eligible Treasury bonds); (b) Performance Bond commitment letter at 100%; (c) Payment Bond commitment letter at 100%. All on Treasury Circular 570 sureties or equivalent. Lead time 5 business days for known clients.
5. **💵 Solicit named-sub quotes for the 4 bid-schedule items with no cost-DB hit.** Item 1 (3 EA OH doors w/ chain hoist, 2" insulated panel, 20ga ext, white baked polyester, 3-yr door / 10-yr finish warranty per SOW 4.2.B) — quote from 2–3 OH-door subs; Item 5 (gas-line cap/remove) — plumbing/gas sub; Item 6 (~110 LF gutter system + downspouts) — gutter sub or self-perform; Item 8 (gas-fired unit heater removal/disposal) — typically same plumbing/HVAC sub as item 5. See `05-bid-schedule-mapping.md` for the full scope of each item.

---

## Hard rules respected in this workspace

- All work product lives under `bids/usfws-san-marcos-140FC126R0017/`. No edits to `core/`, `app.py`, `analyze.py`, `prompts/`, `tests/`, `requirements.txt`, repo-root `README.md`, or any other code path that F1 (CWICR cost-DB) or F3 (drawing pre-pass) might rebase over.
- Sibling bid-prep folders (`bids/tamu-harrington-2025-06813/`, `bids/angelo-state-carr-efa-26-007/`) were **not** touched.
- `analyze.py` was **not** run.
- `.env`, API keys, and any other workstation secrets were **not** read or referenced.
- `inbox/` source PDFs were read (via the `Read` tool) for content but not copied, edited, or committed; `inbox/` remains untracked per repo convention.
- v1 / v2 / v3 calibration outputs (under `exports/` if present) were **not** modified.
- Per the user task brief, all firm-internal data (UEI, CAGE, registered NAICS, insurance carrier limits, banking, etc.) carries a `[USER TO VERIFY]` or `[USER TO FILL]` placeholder — no fabricated firm data.

---

## File map

```
bids/usfws-san-marcos-140FC126R0017/
├─ README.md                          ← you are here
├─ 01-overview.md
├─ 02-bid-prep-checklist.md
├─ 03-missing-documents.md
├─ 04-scope-of-work.md
├─ 05-bid-schedule-mapping.md
├─ 06-evaluation-strategy.md
├─ 07-risk-register.md
├─ 08-far-clauses-flags.md
├─ takeoff-template.json
├─ price-references.md
├─ contacts.md
├─ timeline.md
└─ prevailing-wages.md
```

`local/` — if you create a sibling `bids/usfws-san-marcos-140FC126R0017/local/` folder for sub-quote PDFs, bonding paperwork, site-visit photos, or scratch sheets, it is gitignored via the workspace `.gitignore` rule `bids/*/local/`.
