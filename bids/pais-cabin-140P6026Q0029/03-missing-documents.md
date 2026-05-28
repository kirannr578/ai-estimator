# PAIS — Backcountry Cabin Roof Repairs — Missing Documents + RFI Candidates

> **Use:** Tracking what the RFP package is missing / ambiguous, and what BPC needs to raise as RFIs before the **6/7/2026 cutoff** (3 calendar days after the 6/4 site visit per Section L Part B). Per RFQ Section L, **only written RFIs by email to bridget_parizek@ios.doi.gov** will be considered, and NPS responses will be posted as a SAM amendment.
>
> **Form-on-cover disambiguation (per [federal-simplified-acquisition-best-value playbook](../../firm/playbooks/federal-simplified-acquisition-best-value.md) §4):** This RFQ is on **SF-18** (verified, RFQ pp 1–2). It is NOT on SF-1449 (which would have triggered the FAR Part 12 commercial-item integrated solicitation/contract/order format) and it is NOT on SF-1442 (which would have flipped this to a full FAR Part 14/15 construction RFP). The SF-18 form, combined with the cited FAR Part 13 + Part 12 acquisition method and the "groups of 3 lowest priced" evaluation language in Section M, is the canonical SAP best-value signature. If the CO posts an SF-30 amendment changing the form to SF-1449 (uncommon but the CO has discretion under FAR 13.500), re-verify the clause inventory shift from 52.213 → 52.212 family per the playbook §4. No ambiguity at this time — SF-18 is operative.

## 1. Document inventory — what we have

| RFP attachment | Filename / source | Reviewed | Notes |
|---|---|---|---|
| Solicitation cover (SF-18 RFQ) | `Sol_140P6026Q0029.pdf` (28 pp) | ☑ | RFQ on **SF-18**, not SF-1442. Issued 5/7/2026; original due 6/8/2026 12:00 CT |
| Amendment 0001 (SF-30) | `Sol_140P6026Q0029_Amd_0001.pdf` (2 pp) | ☑ | Site visit moved to 6/4/2026; due-date extended to **6/18/2026 12:00 CT**; project retitled to "PAIS - Backcountry Cabin Roof Repairs" |
| Section A — Solicitation/Contract Form | RFQ pp 1–2 (SF-18) + p 5 | ☑ | RFQ on SF-18; FAR Part 13 simplified acquisition; FFP |
| Section B — Schedule of Prices (CLINs) | RFQ p 5 | ☑ | 3 base CLINs (001/002/003) + 2 priced options (001/002); every CLIN priced is required |
| Section C — Specifications/Drawings | RFQ p 5 + Att 1 (SOW DOCX) + Att 2 (drawings PDF) | ☑ | SOW is in Attachment 1; ramp construction details in Attachment 2 |
| Section D — Packaging and Marking | RFQ p 6 | ☑ | "No clauses included" |
| Section E — Inspection and Acceptance | RFQ pp 6–7 | ☑ | 52.246-12 Inspection of Construction (Aug 1996); interim + final inspection process described |
| Section F — Period of Performance | RFQ p 7 | ☑ | 52.242-14 Suspension of Work; **POP unclearly stated — see ambiguity #1 below** |
| Section G — Contract Administration | RFQ pp 7–10 | ☑ | CS Bridget Parizek; CO designated at award per 1452.201-70; IPP for invoicing; DOI 1452.228-70 liability insurance limits |
| Section H — Special Contract Requirements | RFQ p 10 | ☑ | Green Procurement clause |
| Section I — Contract Clauses | RFQ pp 10–18 | ☑ | Long FAR + DIAR clause list including 52.222-6 Davis-Bacon, 52.225-9 Buy American, 52.228-13 Alt Payment Protections, 52.236-5/-21, 52.246-21 Warranty (Mar 1994), 52.249-10 Default |
| Section J — List of Attachments | RFQ p 18 | ☑ | 3 attachments: Att 1 Specs (9 pp), Att 2 Drawings (1 pp), Att 3 WD (6 pp) |
| Section K — Reps & Certs | RFQ pp 18–21 | ☑ | 52.252-1 / 52.252-5 + 52.203-18 + 52.209-11 + 52.209-13 |
| Section L — Instructions to Offerors | RFQ pp 21–26 | ☑ | Email submission only; 25 MB per-email cap; CHECKLIST FOR QUOTE SUBMITTAL on p 25–26 |
| Section M — Evaluation Factors | RFQ pp 27–28 | ☑ | **Best-value SAP** (NOT LPTA) — Price + Technical Capability + Prior Experience; evaluation in groups of 3 lowest-priced; 52.217-5 Evaluation of Options |
| Drawings | `B08_Solicitation_-_Att_2_-_Drawings.pdf` (1 pp) | ☑ | Ramp + landing construction details; references "Attachment 1 PAIS Cabin 1.25.23 - AS BUILTS" — **referenced but not included** in this zip — see ambiguity #2 |
| Spec book / Project Manual | `B08_Solicitation_-_Att_1_-_Specifications.docx` | ☑ | 9 pp equivalent; SOW format with §1–§9 |
| Wage Determination (Davis-Bacon) | `B08_Solicitation_-_Att_3_-_DOL_Wage_Determination.pdf` (6 pp, Jan/2026) | 🔴 | **Text extraction failed** — PDF uses encoded font with no ToUnicode mapping; pymupdf returns garbled bytes. **User must read the PDF directly and transcribe trade rates** for Kenedy County / TX-DOT 4 region |
| Past-performance template (if provided) | none | n/a | Section L lets BPC use any format with "brief description + POC contact" |
| As-built drawings reference | `Attachment 1 PAIS Cabin 1.25.23 - AS BUILTS` (referenced in Att 2) | 🔴 | **Referenced in Att 2 drawings but not present in this zip** — see ambiguity #2 |

## 2. Documents requested / pending

| Document | Why needed | How to obtain | Owner | Due |
|---|---|---|---|---|
| `Attachment 1 PAIS Cabin 1.25.23 - AS BUILTS` (existing cabin as-built drawings) | Option 001 ramp extension references the existing cabin's as-builts; need them to design integration to existing rim joists / pilings | RFI to Bridget Parizek + email request from Greg Smith at site visit | PM | Before pricing Option 001 |
| Wage Determination trade rates (transcribed from Att 3) | Required for DBA labor pricing | User to read Att 3 PDF directly + transcribe applicable rates | Estimator | Before pricing assembly |
| GFE aluminum ramp specs | Option 001 integration design | RFI #7; or sight-confirm at site visit | PM | Before pricing Option 001 |
| TDI CAT5 shutter approved-products list | CLIN 003 sub solicitation | RFI #6 | PM | Before sub solicitations |
| Site GPS coordinates / beach mile-marker | Crew briefing + EMS plan | RFI #3; or get from Greg Smith at site visit | PM | Before mobilization |
| Sea-turtle / wildlife seasonal restrictions | Schedule risk | RFI #4 | PM | Before pricing schedule |
| National-Register / LCS status of cabin | Determines whether NPS Preservation Brief 4 governs material selection | RFI #5 | PM | Before pricing CLIN 002 (roof) |
| Renewed COI (commercial GL) — ≤ 30 days old at submission | DOI 1452.228-70 | Pull from broker | PM | Pre-submission (not in proposal); pre-mobilization (post-award required) |
| Current SAM.gov registration status + Reps & Certs ≤ 12 months | 52.204-7 / 52.204-19 | User to verify on SAM.gov | PM | Pre-submission |
| Bond commitment letter (Payment Bond OR ILC option) | 52.228-13 — post-award only, but commitment letter strengthens past-performance volume | Bonding agent | PM | Optional pre-submission; required within 10 days of award |
| Past-perf reference contact verification (Lavon, Hindu Temple, Holiday Inn) | Section L Part C "Government may contact and confirm the information provided" | Pre-call references; confirm working email + phone | PM | Pre-submission |

## 3. Ambiguities / boilerplate-leakage flags

Federal RFPs frequently carry stale boilerplate from prior solicitations. Flag every inconsistency and either RFI or document the operative source in the proposal cover letter.

| # | Page / section | Ambiguity | Operative source (per SOW + CLINs) | Action |
|---|---|---|---|---|
| 1 | SOW Att 1 §9 + SF-18 page 2 | SOW §9 says "All on-site work must be completed before 01 JUNE 2025"; SF-18 page 2 says POP is "01/31/2026 to 06/01/2026"; Section B says "60 calendar days from Notice to Proceed". The 2025 date is clearly stale boilerplate from a prior solicitation; the 01/31/2026–06/01/2026 dates also appear retrofitted. | **60 calendar days from NTP**, per Section B and the Special Notice for Contractors | RFI #1 — get CO confirmation in writing |
| 2 | Att 2 drawing | References "ATTACHMENT 1 PAIS CABIN 1.25.23 - AS BUILTS" which is **not included** in this RFP package | Existing cabin as-builts dated 1/25/2023 (apparently held by Park staff) | RFI to request the as-builts; contractor cannot fully design Option 001 ramp integration without them |
| 3 | RFQ §G ("water/electricity furnished at no cost") vs. SOW Att 1 CLIN 003 ("absence of electrical power on-site") | Direct contradiction | SOW CLIN 003 governs (more recent, more specific) — assume **no electrical power on site** for tools | RFI #2 — confirm; affect on temp-utility GC pricing |
| 4 | Section L Part C.3.i subject line vs. Amd 0001 retitle | Section L subject line is "PAIS – Cabin Security and Improvements"; Amd 0001 retitled the project to "PAIS — Backcountry Cabin Roof Repairs" | Section L (subject line specified by Section L is operative) | RFI #10 — confirm subject line on submission email; document in cover letter as following Section L |
| 5 | SOW CLIN 003 specifies 10 windows | But site visit may reveal a different window count | Site visit will be authoritative; flag in RFI if count differs | Verify at 6/4 site visit; if discrepancy, RFI before close |
| 6 | RFQ §I clause list | 52.245-1 Government Property and 52.245-9 Use and Charges are listed (paragraph form) but only the GFE aluminum ramp (Option 001) is identified as Government property. Confirm scope. | GFE limited to aluminum ramp per SOW §6 | Accept as-is; confirm at site visit if any other government property is in play |
| 7 | RFQ Section M "Price Reasonableness" | Section M references "comparison to an independent Government estimate" but no IGE magnitude band is published in the RFQ | IGE exists per RFQ §"Award is subject to and based on the availability of funds. This project is currently funded based upon an independent cost estimate." but is not published | Accept silently; bid the true cost + reasonable markup; do not chase a magnitude that wasn't published |

## 4. RFI candidates (draft before 6/7/2026 cutoff)

| # | Topic | RFP reference | Question | Impact on price | Status |
|---|---|---|---|---|---|
| 1 | Stale POP dates | SOW §9 + SF-18 p 2 | Confirm operative POP is 60 cal-days from NTP | Schedule + GC | Draft |
| 2 | On-site utilities | RFQ §G vs SOW CLIN 003 | Confirm no electrical power on site for tools | Temp-utility cost (generator) | Draft |
| 3 | Site GPS / mile-marker | SOW §8 | Provide site GPS or beach mile-marker for crew briefing + EMS | Mobilization + GC | Draft |
| 4 | Wildlife buffers | SOW §4 | Sea-turtle nesting buffer status during 2026 construction window? | Schedule risk | Draft |
| 5 | National Register / LCS | SOW + NPS practice | Is cabin historic / LCS-listed? Preservation Brief 4 application? | CLIN 002 material premium | Draft |
| 6 | TDI shutter approved list | SOW CLIN 003 | TDI-listed manufacturer list or any compliant product? | Sub solicitation strategy | Draft |
| 7 | GFE aluminum ramp specs | SOW §6 + Option 001 | Make/model/dimensions/connection details of GFE aluminum ramp | Option 001 pricing risk | Draft |
| 8 | Sand-control flood loads | SOW Option 002 | Design base-flood elevation + lateral-load criteria for breakaway | Option 002 design | Draft |
| 9 | CO + COR designation | RFQ §G + 1452.201-70 | Confirm CS authority during bid window | Communication discipline | Draft |
| 10 | Email subject line | Section L Part C.3 vs Amd 0001 | Confirm submission subject line wording | Compliance / non-responsive risk | Draft |
| 11 | As-builts attachment | Att 2 cross-reference | Provide "Attachment 1 PAIS Cabin 1.25.23 - AS BUILTS" referenced in Att 2 | Option 001 design | Draft |

## 5. Draft RFI cover letter

```
Subject: RFI — 140P6026Q0029 — PAIS — Backcountry Cabin Roof Repairs

Dear Ms. Parizek:

In accordance with Section L of 140P6026Q0029, Blue Print Constructs (RK
Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs)
respectfully submits the following Request for Information regarding the
above-referenced solicitation. We request a response by the RFI cutoff
(6/7/2026, 3 calendar days following the 6/4/2026 site visit) to enable
accurate pricing.

11 RFI items follow:

  RFI #1: Stale period-of-performance dates
    Reference: SOW Attachment 1 §9; Solicitation SF-18 page 2; Section B
    Question: SOW §9 states "All on-site work must be completed before 01
              JUNE 2025" and SF-18 page 2 states POP is "01/31/2026 to
              06/01/2026", but Section B states 60 calendar days from
              Notice to Proceed. Please confirm that the operative POP is
              60 calendar days from NTP.
    Reason: Mobilization, crew lodging, weekend-work approval window,
            and weather/wildlife buffer planning all depend on the
            operative POP.

  RFI #2: On-site utilities contradiction
    Reference: RFQ Section G "AVAILABILITY OF UTILITIES SERVICES" vs.
              SOW Attachment 1 CLIN 003
    Question: Section G states water and electricity will be furnished at no
              cost from existing systems; SOW CLIN 003 states the cabin has
              "absence of electrical power on-site." Please confirm whether
              electrical power is available at the cabin or whether the
              contractor must furnish a generator for tools.
    Reason: Temp-utility General Conditions cost differential.

  [RFI #3 through RFI #11 — see numbered list above]

Thank you,

[USER TO FILL — signer name + title]
Blue Print Constructs (RK Residential Homes and Commercial Constructions, LLC
dba Blue Print Constructs)
UEI LM4YHVQ71QG7 • CAGE 9LET0
(469) 213-1838 • contactus@blueprintconstructs.com
```

## 6. Stand-in assumptions (if RFI not answered)

If an RFI is not answered before the 6/18/2026 12:00 CT due date, BPC will:

- Quote the most-conservative interpretation in the priced proposal
- Document the assumption in `08-pricing-strategy.md` (internal)
- **Not** include the assumption in the proposal narrative — exception language flips the bid to non-responsive ("Quotes offering alternative stipulations to the requirements of this solicitation will NOT be considered or accepted" — Section L General Information)
- File the unanswered RFI as a post-award clarification request via the post-award NTP+5 preconstruction conference (or DI-137 Release of Claims process)

| RFI | If unanswered, BPC will assume |
|---|---|
| #1 (POP) | 60 cal-days from NTP — price the schedule on this assumption |
| #2 (utilities) | **No on-site power** — price a generator into temp utilities (more conservative) |
| #3 (GPS) | Use Park Road 22 mile-marker estimate from site visit photos + Google Earth; allow 1.5-hr round-trip per crew-day |
| #4 (wildlife) | Build a 5-day weather/wildlife contingency into the 60-day POP |
| #5 (Preservation Brief 4) | Quote standard marine-grade like-kind shingles per CLIN 002 spec (not historic-grade); note in cover letter as compliance with stated SOW requirement |
| #6 (TDI list) | Sub-solicit ≥ 3 TDI-listed Bahama-shutter manufacturers and price the lowest-compliant |
| #7 (GFE ramp) | Standard 3-ft-wide aluminum ADA ramp with bolted-edge connection — adjust at site visit if specs differ |
| #8 (flood loads) | FEMA Tech Bulletin 9 default 20 psf failure load |
| #9 (CO/COR) | All RFIs to CS Bridget Parizek by email — only channel established |
| #10 (subject) | Use Section L exact subject line: "140P6026Q0029 – PAIS – Cabin Security and Improvements – email N of M" |
| #11 (as-builts) | Sight-survey at site visit + dimensional verification before Option 001 ramp design |
