# 01 — Project overview

> Sources, in order of weight: (1) `inbox/opportunities/attachments/2026-05-21/Sol_140FC126R0017.pdf` — the SF 1442 + Sections A–M, 73 pages; (2) `inbox/opportunities/attachments/2026-05-21/SOW_-_Final_-_San_Marcos_-_02192026_Word_r_1.pdf` — Statement of Work (17 pages, Asset #10006277); (3) `inbox/opportunities/attachments/2026-05-21/Bid_Schedule_San_Marcos_ARC__Rehabilitate_Shop___2_Stall_Garage_Build.pdf` — 1-page bid schedule with 8 CLINs; (4) `inbox/opportunities/attachments/2026-05-21/SAM_-_Davis-Bacon_Act_WD_TX20260254__Hays_County__Building.pdf` — Davis-Bacon WD (text-extraction broken; see `prevailing-wages.md`).

---

## 1. Solicitation identity

| Field | Value |
|---|---|
| Solicitation number | **140FC126R0017** |
| Project number | **FC1** (RFP p.2) |
| Requisition / purchase request | **0044039660** |
| Type of solicitation | NEGOTIATED (RFP) — Request For Proposal |
| Date issued | 2026-05-20 |
| Project name | **San Marcos Aquatic Resources Center (ARC) — Rehabilitate Shop & 2 Stall Garage Building** |
| Asset # | 10006277 (per SOW) |
| Issuing office | **FWS, Construction A/E Team 1**, 5275 Leesburg Pike, Falls Church VA 22041 (Code FC1) |
| Contracting Officer | **Tracy Gamble**, Tracy_Gamble@fws.gov, (404) 679-4055 — Section Chief, Construction/A&E, Acquisition and Property Operations, USFWS Atlanta, GA |
| Contract Specialist | **Drew Ferrall**, `john_ferrall@fws.gov` (note: RFP L.1.2 uses `john_ferrall@ios.doi.gov` — see `03-missing-documents.md` #2 for the inconsistency) |
| Set-aside | **100% Total Small Business Set-Aside** (FAR 52.219-6) |
| NAICS | **236220 — Commercial and Institutional Building Construction** (RFP 52.204-8(a)) |
| Small-business size standard | **$45.0 Million** (RFP 52.204-8(a)(2)) |
| Contract type | **Firm-Fixed Price Construction Purchase Order** (52.216-1; M.1.1) |
| Source-selection process | **Lowest Price Technically Acceptable (LPTA)** — Section M.1.0 |

## 2. Location

- **Project site:** San Marcos Aquatic Resources Center (a USFWS national fish hatchery), 500 East McCarty Lane, San Marcos, TX 78666-1024 — Hays County
- **Delivery Location Code:** 0011279575 (RFP p.4)
- **Site is civilian USFWS (Dept of the Interior), NOT DoD** — far easier access than a Sol_140P6026Q0029-class NPS / military site, but still a federal facility with gate sign-in. ID check required.

## 3. Key dates and clocks

| Event | Date / Time | Source | Status |
|---|---|---|---|
| Solicitation issued | 2026-05-20 | SF 1442 block 3 | Done |
| Site visit windows (highly encouraged, not mandatory) | **2026-05-27 or 2026-05-28, 8:00 AM – 4:00 PM CDT** | RFP p.3 + 52.236-27 in Section L | T-5/-6 days — RSVP by 5/26 |
| RFI cutoff | **2026-06-08, 5:00 PM EDT** | RFP p.3 + L.1.3 | T-17 days |
| Proposal due — email to `john_ferrall@fws.gov` | **2026-06-22, 5:00 PM EDT** | RFP p.3 + SF 1442 block 8 | T-31 days |
| Offer acceptance period | ≥ 90 calendar days from due date | RFP p.3 block 13d | Carry 90 days minimum |
| Performance period start | Within 10 calendar days after NTP | 52.211-10 + F.1.0 | After award |
| Substantial completion / final completion | **60 calendar days from NTP** (mandatory, not negotiable) | SF 1442 block 11 + F.1.0 + SOW 3.3 | After award |

## 4. Scope (verbatim from the RFP description block, p.3)

> "The U.S. Fish and Wildlife Service has a multi-discipline construction project for work that requires demolition and installation of garage doors, replacement of lighting, ceiling grids/tiles, personnel doors and gutters, terminate, cap and remove existing gas lines from the building and remove and replace existing roof with new 24-gauge roofing panels at the San Marcos ARC per the Statement of Work (SOW)."

Per the SOW (§1.1.A), the work breaks down to 8 discrete tasks, which map 1-to-1 to the 8 federal bid-schedule CLINs:

1. Replace **three overhead roll-up doors** w/ hardware, weather stripping, manual chain hoists
2. Replace existing **light fixtures with LED fixtures** to meet OSHA requirements
3. Remove all **suspended ceiling grids and tiles** (~416 SF per SOW §1.1.A.3)
4. Replace **three (3) exterior personnel doors** with insulated hollow metal doors incl. frames, hardware, weather strip, threshold
5. **Terminate, cap, and remove existing gas lines** from the building
6. Remove and replace existing **gutter system + downspouts** (~110 LF per RFP + SOW)
7. Remove and replace **existing roof with new 24-gauge metal roof panels**, matching existing profile — **excluding the lean-to / awning on the south side** (SOW §1.1.A.7)
8. Remove **existing gas-fired unit heaters**

Trade-by-trade breakout in `04-scope-of-work.md`; CLIN-by-CLIN cost mapping in `05-bid-schedule-mapping.md`; quantities & cost roll-up in `takeoff-template.json`.

## 5. Contacts (verbatim from RFP Sections G + L; full plan in `contacts.md`)

| Role | Name | Email | Phone |
|---|---|---|---|
| Contracting Officer (CO) | Tracy Gamble | Tracy_Gamble@fws.gov | (404) 679-4055 |
| Contract Specialist (CS) | Drew Ferrall | john_ferrall@fws.gov ⚠️ also referenced as `john_ferrall@ios.doi.gov` in L.1.2 — use both for RFI submissions until confirmed | not published |
| Site visit POC (Supervisory Biologist) | Katherine Bockrath | Katherine_Bockrath@fws.gov | (512) 610-5597 |
| Contracting Officer's Representative (COR/COTR) | TBD at award | — | — |
| Field Inspector | Juan Martinez (also spelled "Marinez" in RFP G.3 — same person, RFP typo) | — | — |
| Protest service-of-process | Tracy L. Gamble (Section Chief, Construction/A&E, USFWS Atlanta) | Tracy_Gamble@fws.gov | — |

## 6. Document acquisition

- The RFP, SOW, Bid Schedule, and Davis-Bacon WD are the **only published attachments** (Section J lists exactly these three plus the SF 1442). We have all four PDFs in `inbox/opportunities/attachments/2026-05-21/`.
- USFWS RFPs are posted on **SAM.gov** under the solicitation number. Any amendments will appear there. Check SAM.gov daily through June 8 (RFI cutoff) — if any RFIs are answered, they will be issued as a numbered amendment (SF 30), which must be acknowledged on SF 1442 block 19.
- **No drawings are attached.** The SOW relies on Appendix 2 photos + onsite measurement. This is normal for a sub-$250K shop-rehab project but means accurate pricing needs the site visit (see `03-missing-documents.md` #1).

## 7. What's in the RFP that matters for pricing

These items are tucked into the 73-page RFP and easily missed; they materially shape the bid:

1. **Work hours restricted to 7:00 AM – 4:30 PM CT, M–F**, no Federal holidays, no weekends without CO + Station Manager approval (H.1.0). No premium-time labor baked into the base price unless weather suspension drives a recovery push.
2. **Bid Guarantee required**: 20% of bid OR $1M, whichever is less (52.228-1). For a $200K bid, that's a $40K bid bond, not a percentage line item.
3. **Performance & Payment Bonds at 100% on award** (52.228-15). Threshold language ties to FAR 28.102-1(a) — currently $150K; magnitude says we're at or above it.
4. **15% on-site self-perform minimum** (52.236-1) — measured "with its own organization." Must be enforced through the schedule and crew-loading, not just the org chart.
5. **Buy American — Construction Materials** applies (52.225-9), with a **20% domestic-content price differential** if foreign material is proposed (per 52.225-10). 24-ga metal roof panels and steel doors/frames are both iron-and-steel construction material — verify domestic origin in submittals.
6. **DBA wage rates flow down to truck drivers only when hauling on-site or between site and a dedicated nearby facility** (H.16.0 + 29 CFR 5.2(j)). Don't accidentally over-burden the materials freight.
7. **Differing Site Conditions clause (52.236-2) applies** — important on a renovation where the substrate, structure underneath the roof panels, and existing gas-line layout aren't fully documented. Use the formal written-notice procedure to preserve equitable-adjustment rights.
8. **Submittal review window is 7 calendar days post-receipt by COTR** (H.6.0) — bake this into the schedule. Materials in scope for submittal: roll-up doors + chain hoists, LED fixtures, hollow metal personnel doors, metal roof panels (SOW §1.4.B).
9. **Invoicing must run through US Treasury's Invoice Processing Platform (IPP)** at `https://www.ipp.gov` (G.4). Enrollment instructions arrive from the Federal Reserve Bank of St. Louis within 3–5 business days of award. Plan cash flow against monthly progress payments and a 10% retainage hold if quality issues remain uncorrected (G "Payment Procedures" Step 4).
10. **Final invoice must state "FINAL" and include a Release of Claims (Form DI-137)** (G + 1452.204-70). One-line oversight that kicks the final payment back if missed.

## 8. Discrepancies and oddities in the published RFP (flag with the CO before bidding)

1. **Section B (RFP pp.6–7) carries a copy-paste error.** The Project Description block ("This requirement is for one (1) Firm Fixed Price Construction contract for the Pelican Island National Wildlife Refuge (NWR) Replace Bunkhouse Roof project in Indian River County, Vero Beach, Florida") is from a different solicitation. The CLINs 0001–0008 below it are the correct San Marcos items. Send an RFI to the CO before June 8 to confirm the CLINs as published are binding.
2. **Bid Schedule (Attachment 2) item 0004 lists "Unit: JOB, Est QTY: 3"** for 3 personnel doors. Section B p.7 lists item 0004 as "Unit: JOB, Quantity: 1". The intent (per SOW §1.1.A.4) is clearly 3 doors. RFI: confirm whether item 0004 is bid as Qty 3 × unit price OR Qty 1 × lump-sum for 3 doors.
3. **RFP p.3 says proposals go to `john_ferrall@fws.gov`**; **RFP L.1.2 (p.63) says they go to `john_ferrall@ios.doi.gov`.** Send to BOTH and copy the CO to be safe; raise this as an RFI as well.
4. **Field Inspector name spelled "Juan Martinez" in Section E and "Juan Marinez" in Section G.** Cosmetic, but worth confirming the FI's correct name on the post-award appointment letter.
5. **CALEA / "Pelican Island"-flavored boilerplate in Section B and elsewhere** suggests Section B was repurposed from a previous RFP. Re-read the entire SF 1442 + the CLIN headings and confirm what's actually being asked. The work + the CLINs match the SOW; only the Project Description prose is wrong.

## 9. Why this opportunity is a MAYBE and not a YES

From the triage canvas notes:

- **Small contract value vs. federal compliance overhead** is the central tension. A federal sub-$250K renovation drags in DBA, certified payroll (52.222-8), IPP invoicing, SAM registration maintenance through final payment, Buy American certification, the FASCSA supply-chain check, and a heaping list of FAR clauses by reference. The compliance burden is closer to that of a $1M project; the profit envelope is not.
- **LPTA means thin-margin** (see `06-evaluation-strategy.md`). At a sub-$250K size with federal overhead, the difference between winning and breaking even is often the difference between hitting the takeoff right the first time and not. Site visit + tight subcontractor coordination is more important here than on a value-based award.
- **What makes it a "go"**: bid-schedule is published — no need to invent your own structure; SOW is concise and well-bounded; site is civilian and accessible; period of performance is short (60 days) so the bid doesn't sit on bonded capacity for months; and a Small Business set-aside means the competitive pool is narrower than a full-and-open RFP.
- **The deciding question is internal**: does the firm currently have an active SAM.gov registration with NAICS 236220 asserted as small? If not, go/no-go pivots to "go" only after SAM is current — and SAM updates take 3–10 business days, which puts the go-decision on or before **2026-06-12** (10 business days ahead of June 22 submission) to leave margin.
