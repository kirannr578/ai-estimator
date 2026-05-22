# 03 — Missing documents

What is NOT in hand vs. what we need, with priority, source, and a stand-in if we can move forward without it for a day or two.

> The good news on this RFP: per Section J, the published attachments are **only** the SOW (17 pages), the RFP Bid Schedule (1 page), and the Davis-Bacon WD (7 pages) — and we have all three. So the universe of "missing" documents is much smaller than a state RFCSP. The missing items mostly fall into: (a) drawings, (b) confirmations from the CO via RFI, (c) machine-readable wage data.

---

## Priority 1 — blocks pricing or responsiveness

| # | Document / answer | What it is | Where to get it | Stand-in we can use |
|---|---|---|---|---|
| 1 | **Architectural drawings** (or plan + elevations + roof framing plan) | The SOW says "APPENDIX 3 ORIGINAL DRAWINGS" but no drawings are in the published PDF — Appendix 3 in the PDF is just a placeholder title page. Need building footprint, roof slope, panel layout, gas-line routing, ceiling-grid extent. | RFI to CO (Drew Ferrall) before June 8 OR confirm at site visit on May 27/28. | Site-visit measurements + SOW Appendix 2 photos. The SOW gives the key quantities (ceiling ~416 SF, gutter ~110 LF); roof SF is the missing big number. |
| 2 | **Confirm correct proposal-submission email address** | RFP p.3 says `john_ferrall@fws.gov`; RFP L.1.2 (p.63) says `john_ferrall@ios.doi.gov` | RFI to CO before June 8 | Send to BOTH addresses; copy CO Tracy Gamble. |
| 3 | **Clarify Section B copy-paste error** | RFP pp.6–7 Section B has Project Description for "Pelican Island NWR, Vero Beach FL" — wrong project. CLINs 0001–0008 below it are correct San Marcos items. | RFI to CO before June 8 | Treat the published CLINs as binding; document the discrepancy in the proposal cover letter for the record. |
| 4 | **Clarify Bid Schedule item 0004 quantity** | Attachment 2 lists item 0004 as "Unit JOB, Est QTY 3" (3 personnel doors); Section B p.7 lists same item as "Unit JOB, Quantity 1." SOW §1.1.A.4 says 3 doors. | RFI to CO before June 8 | Bid as quoted on Attachment 2 (Qty 3 × unit price extending to total) and confirm by RFI. If the CO answers "Qty 1 LS," re-state the bid as 1 LS for 3 doors at the same total. |
| 5 | **Davis-Bacon WD trade-rate table** | The WD PDF (TX20260254 — Hays County, Building Construction) renders as unreadable text in our extractor — bad PDF font glyphs. Need to read it visually + transcribe rates. | Open the PDF in a regular reader (Adobe / browser) and re-key the rates into `prevailing-wages.md`. | Use SAM.gov's wage-determination page (`https://sam.gov/wage-determinations/`) and look up TX20260254 — the same WD is published machine-readable there. |
| 6 | **Building footprint area in SF** | The single most important quantity. Drives Item 0007 (roof) directly, and influences item 0001 (door header dimensions) + item 0006 (gutter LF cross-check). | Site visit measurement | Inference from SOW context — "Shop & 2 Stall Garage Building" + 416 SF ceiling tile area suggests a building footprint in the **~1,500–2,500 SF** range. Carry the midpoint until measured. |

## Priority 2 — needed for compliance / risk reduction

| # | Document / answer | What it is | Where to get it | Stand-in |
|---|---|---|---|---|
| 7 | **Confirmation that the firm's SAM record is active + Reps & Certs current** | Go/no-go gate | `https://sam.gov/` — user logs in | None. Without this, no bid. |
| 8 | **Asbestos / lead survey results for the building** | Per H.12.0, contractor must immediately stop and notify CO if suspected hazardous materials are encountered. The building is a USFWS shop/garage — pre-1980 construction could harbor lead paint or transite (asbestos-cement) panels. | RFI to CO; or USFWS facility manager (Katherine Bockrath) at site visit | Carry a **$2K–$5K hazmat-encounter allowance** as a contingency in the markup, NOT as a CLIN (LPTA forbids contingency CLINs). Document the assumption in the cover letter. |
| 9 | **Roof slope + existing panel profile** | Needed so the new 24-ga panels "match existing profile" per SOW §4.2.A.1 | Site visit + roof-pitch finder | Photograph existing panels at site visit; verify profile matches a domestically-manufactured Buy-American-compliant SKU before submittal. |
| 10 | **Whether existing roof has underlayment that must be removed** | SOW §4.2.A.2 says "inspect underlayment metal joists" but is silent on a felt / synthetic underlayment layer. | RFI / site visit | Default assumption: existing underlayment stays; new ice-and-water shield only at eaves if local code requires (Hays County does not). Document. |
| 11 | **Existing electrical panel capacity for LED retrofit** | SOW §1.1.A.2 calls for LED replacement; if existing panel is at capacity, new circuit additions may be needed. | Site visit — photograph main + sub panel (SOW Appendix 2 already shows them). Read load on the panel directory. | LED retrofit typically reduces lighting load 40–60%; new circuit additions unlikely. Carry as-is. |
| 12 | **Gas line termination point — at meter, at wall penetration, or downstream of a valve?** | SOW §1.1.A.5 says "Terminate, cap and remove existing gas lines from the building." The cap location matters for the gas sub's scope. | RFI / site visit | Default: cap at the gas-meter outlet AND at the wall penetration into the building; remove all interior piping. Confirm with the gas-licensed sub. |
| 13 | **Whether SAM.gov has any amendments to the solicitation already** | RFI responses are issued as numbered amendments (SF 30) on SAM | `https://sam.gov/` → search "140FC126R0017" → Amendments tab. Check daily through June 22. | None — must check directly. |

## Priority 3 — nice to have / risk-reducers

| # | Document / answer | What it is | Where to get it | Stand-in |
|---|---|---|---|---|
| 14 | **List of prior similar awards by FWS Construction A/E Team 1** | Past clearing prices for sub-$250K USFWS rehab work | USAspending.gov + FPDS-NG search by funding agency (FWS) and NAICS 236220 | Use the $/SF benchmarks in `price-references.md`. |
| 15 | **CO's typical LPTA-bid spread** | Some USFWS COs publicly read awards; spread between low and second-low tells us how thin the LPTA pool will price | FBO archive (legacy) / SAM.gov award notices | Skip; not actionable in 31 days. |
| 16 | **Whether USFWS will accept electronic-signature on the SF 1442** | Some COs require wet ink. | RFI / clarification call | Default: electronic signature is acceptable on federal SF forms post-2022 unless the RFP says otherwise. This RFP doesn't say. |
| 17 | **Whether COR / COTR will be named before award** | If named pre-award, allows direct technical Q&A during pricing | RFI to CO | RFP G.1 says COR/COTR is TBD. Don't expect a name before award. |
| 18 | **Local utility (Atmos Energy or local LDC) requirements for gas-service termination** | Outside scope of the contract but the gas sub will need a permit / scheduling | Texas Railroad Commission + Atmos Energy site | Have the gas sub handle directly. |
| 19 | **Site security / access procedure** | What ID required at the gate, escort required? | Katherine Bockrath at site-visit RSVP | Default: state-issued ID + sign-in at the gate. Civilian USFWS site — no CAC required. |

---

## How to triage what's blocking what

- Items #1, #5, #6 are needed before takeoff can be finalized → all should be resolved at the May 27/28 site visit.
- Items #2, #3, #4, #7, #10, #12, #13 are needed before submission → all should be resolved by June 8 (RFI cutoff) or June 21 (last SAM-check).
- Items #8, #9, #11 are risk-reducers; their absence is acceptable if explicitly held inside the contingency markup and not raised as proposal exceptions.

---

## RFI cover-letter draft (paste into email to Drew Ferrall, copy Tracy Gamble, before 2026-06-08)

> **Subject:** RFI — 140FC126R0017 — San Marcos ARC Shop & 2 Stall Garage
>
> Drew Ferrall (with copy to Tracy Gamble),
>
> Per RFP §L.1.3, please confirm the following items at your earliest convenience:
>
> 1. **Proposal submission email.** RFP p.3 specifies `john_ferrall@fws.gov`; §L.1.2 (p.63) specifies `john_ferrall@ios.doi.gov`. Please confirm the operative address.
> 2. **Section B project description.** Pages 6–7 of the RFP describe a "Pelican Island NWR Replace Bunkhouse Roof" project in Vero Beach FL; CLINs 0001–0008 below the description are the correct San Marcos items. Please confirm the published CLINs are binding and that the prose block is a non-binding boilerplate carryover.
> 3. **CLIN 0004 quantity.** Bid Schedule (Attachment 2) lists Item #4 as Unit JOB, Est QTY 3; Section B p.7 lists the same item as Unit JOB, Quantity 1. SOW §1.1.A.4 says 3 doors. Please confirm whether the line should be bid Qty 3 × unit price or Qty 1 lump sum.
> 4. **Drawings.** SOW Appendix 3 references "ORIGINAL DRAWINGS" — none are attached. Please confirm whether any drawings or sheets will be issued via amendment, or whether the SOW + Appendix 2 photos are the complete design basis (in which case the site visit is the controlling source for dimensions).
> 5. **Existing roof scope.** Please confirm: (a) total building footprint area to receive new 24-ga panels (excluding the lean-to per SOW §1.1.A.7), (b) whether existing underlayment is to remain or be removed, (c) profile dimensions of existing panels so the replacement profile can be procured Buy-American-compliant.
> 6. **Gas-line cap location.** SOW §1.1.A.5 references termination/capping. Please confirm where the gas service is to be terminated (at the meter, at the building penetration, at an interior shut-off valve, or all of the above).
> 7. **Hazardous materials.** Has the facility been surveyed for asbestos (transite panels, pipe insulation) or lead paint? If a survey exists, please share. If not, please confirm the Differing Site Conditions / 52.236-2 procedure applies if material is encountered during demolition.
>
> Solicitation Passage references:
>
> - Item 1: RFP pp.3 and 63
> - Item 2: RFP pp.6–7
> - Item 3: Attachment 2 (Bid Schedule) row 4 + RFP p.7 line 0004
> - Item 4: SOW Appendix 3 + RFP H.7.0
> - Item 5: SOW §1.1.A.7 + §4.2.A
> - Item 6: SOW §1.1.A.5
> - Item 7: SOW §1.6.A + RFP H.12.0
>
> Offeror name, representative, email, and phone are provided below per L.1.3.a.
>
> `[USER TO FILL]`
