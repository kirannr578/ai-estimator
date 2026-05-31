# Triage — OneDrive `Landmark/05272026` batch (2026-05-27)

**Source folder (read-only, OneDrive):** `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\`
**Files modified on disk:** 2026-05-28 14:33 CT (sync timestamp)
**Triage performed:** 2026-05-30
**Triage performed by:** Cursor agent, deterministic ingest (no LLM calls — OpenAI quota exhausted)
**Batch shape:** 12 files spanning **5 distinct opportunities**

> **Important correction to intake assumption.** The intake brief framed this drop as a single "Landmark / Renovation of Park and Recreation Center Facilities (4024120)" opportunity. The actual folder contains **5 unrelated solicitations** from a 2026-05-27 ESBD + SAM.gov sweep. No file references the project number `4024120` or the literal phrase "Renovation of Park and Recreation Center Facilities". The closest matches to a *park/rec* theme are (a) the Allen Veterans Memorial Improvements at Bethany Lakes Park (city park, hardscape/memorial expansion) and (b) the TPWD stair replacement at Old Tunnel State Park (state park, minor construction). The `opp_4024120_clarify` watchlist key referenced in the intake does not exist in this repo; treat this triage memo as the clarification record itself.

## 1. Full inventory

Generated deterministically by `tmp_smoke/ingest_landmark_05272026.py` (pypdf 6.12.1 text extraction, MD5 head-hash for dedupe). The script is gitignored (`tmp_smoke/`); rerun any time against the OneDrive folder.

| # | File | Bytes | Modified | Doc-type guess | Confidence | Opportunity group |
|--:|---|--:|---|---|---|---|
| 1 | `2026-4-49 Legal Ad.pdf` | 107,135 | 2026-05-28 14:33 | Legal Ad / Notice to Bidders | High | **G1 — Allen Veterans Memorial** |
| 2 | `Bid Invitation.pdf` | 62,414 | 2026-05-28 14:33 | IFB Event Invitation (IonWave header) | High | **G1 — Allen Veterans Memorial** |
| 3 | `ESBD_520042_1779477645212_HHS0017366_PCS_137_Building 500 Mechanical Room Renovation.pdf` | 437,241 | 2026-05-28 14:33 | IFB (PCS 137 template, 41 pp) | High | **G2 — HHS Bldg 500 Mech** |
| 4 | `ESBD_520042_1779477672947_Exhibit_B_PCS_111_HHS_UTCs_and_HHS_Affirmations_No_DUA.pdf` | 704,982 | 2026-05-28 14:33 | Contract affirmations (Exhibit B) | High | **G2 — HHS Bldg 500 Mech** |
| 5 | `ESBD_520042_1779477694400_Exhibit_C Pricing_Sheet.xls.xlt` | 45,056 | 2026-05-28 14:33 | Pricing sheet (Excel template, double extension) | High | **G2 — HHS Bldg 500 Mech** |
| 6 | `ESBD_520042_1779477713531_Exhibit_D_Bidder_Reference_Qualifications_Form_(01-21-26).pdf` | 106,365 | 2026-05-28 14:33 | Bidder reference / qualifications form (Exhibit D) | High | **G2 — HHS Bldg 500 Mech** |
| 7 | `ESBD_520042_1779477735493_Exhibit_E_Online_Bid_Room_Information_v.1.4_(07-22-25).pdf` | 104,855 | 2026-05-28 14:33 | HHS Online Bid Room instructions (Exhibit E) | High | **G2 — HHS Bldg 500 Mech** |
| 8 | `ESBD_520042_1779477761792_Exhibit_E-1-PCS_Map_Directions_(01-21-2026).pdf` | 4,048,179 | 2026-05-28 14:33 | PCS site-visit map / directions (Exhibit E-1) | High | **G2 — HHS Bldg 500 Mech** |
| 9 | `ESBD_520042_1779477785436_Exhibit_F_Form_4109_Application_for_TIN_(01-21-2026).pdf` | 256,023 | 2026-05-28 14:33 | TX Comptroller Form 4109 (Exhibit F) | High | **G2 — HHS Bldg 500 Mech** |
| 10 | `ESBD_520356_1779824305593_Camp Mabry Temporary Modular Office RFI 5.26.26.pdf` | 273,877 | 2026-05-28 14:33 | RFI (TMD, pre-solicitation only) | High | **G3 — TMD Camp Mabry Modular RFI** |
| 11 | `ESBD_520362_1779834504715_IFB 802-26-79308_Stair Replacement at Old Tunnel State Park.pdf` | 2,280,601 | 2026-05-28 14:33 | IFB Minor Construction (48 pp) | High | **G4 — TPWD Old Tunnel Stairs** |
| 12 | `W9126G26RA015_Compiled.pdf` | 12,648,619 | 2026-05-28 14:33 | Federal RFP (Design-Bid-Build, ~1,835 pp) | High | **G5 — USACE Fort Hood Staging** |

**Total batch size:** 21,074,347 bytes (~20.1 MiB) across 12 files.
**File types:** 11× PDF, 1× XLT (Excel template, double extension `.xls.xlt`).
**No restricted-class content detected** on first-page inspection. All forms (Exhibit D bidder qualifications, Exhibit F Form 4109 TIN application) are blank templates for the *bidder* to complete; they do not contain PII from the agency side. Exhibit B (UTCs) and the procurement docs are all standard public-procurement boilerplate.

## 2. Opportunity grouping (5 groups)

### G1 — City of Allen Veterans Memorial Improvements (IFB 2026-4-49)

| Field | Value |
|---|---|
| Solicitation # | `2026-4-49` |
| Issuing agency | City of Allen, Texas — Purchasing Department |
| Procurement type | IFB (sealed bid) under **Tex. Local Gov't Code Ch. 252** (municipal) — best-value award language |
| Title | Veterans Memorial Improvements (expansion at Bethany Lakes Park) |
| Site | Bethany Lakes Park, Allen, TX 75013 (Collin County) |
| Portal | IonWave — `https://allentx.ionwave.net/` |
| Issue date | 2026-05-22 |
| Pre-bid meeting | 2026-06-02 11:00 CT (Microsoft Teams; registration required via IonWave) |
| Questions deadline | 2026-06-04 14:00 CT |
| Response deadline | **2026-06-11 14:00 CT** |
| Bid opening | 2026-06-11 14:00 CT (immediately after submission close) |
| Contact | Tim Massey, Purchasing — `tim.massey@allentx.gov` — 214-509-4643 |
| Source files | Files **#1** (Legal Ad) + **#2** (Bid Invitation w/ event metadata & attachment index). The IFB packet, bid form (xlsx), and Exhibit 1 insurance requirements are *referenced* by file #2 but were **not included** in the OneDrive drop — they must be re-pulled from IonWave (see Path-B scaffold `03-missing-documents.md`). |

### G2 — HHSC Building 500 Mechanical Room Renovation (IFB HHS0017366 / PCS 137)

| Field | Value |
|---|---|
| Solicitation # | `HHS0017366` (PCS template 137) |
| Issuing agency | Texas Health and Human Services Commission (HHSC) — Procurement and Contracting Services (PCS) |
| Procurement type | **IFB under Tex. Gov't Code §2155.067** (state-funded sealed-bid; *not* a Ch. 2269 CSP) |
| Title | Building 500 Mechanical Room Renovation |
| Site | 1401 S. Rangerville Rd, Harlingen, TX 78552 (Cameron County) |
| NIGP | 910-00 Building Maintenance, Installation and Repair Services |
| ESBD posted | 2026-05-22 |
| On-site visit | **May 28-29, 2026** ⚠️ already past as of triage |
| Questions deadline | 2026-06-01 10:30 CT |
| Addendum posted | 2026-06-03 |
| Response deadline | **2026-06-10 10:30 CT** |
| Sole point of contact | Byron Wright (CTCD, CTCM), HHSC PCS — `Byron.Wright@hhs.texas.gov` — 512-406-2512 |
| Onsite contact | Ruben Aguero, 956-364-8443 (office) / 956-320-4394 (state cell) |
| Binding offer period | 240 days |
| Source files | Files **#3** (main IFB), **#4** (Exhibit B UTCs), **#5** (Exhibit C pricing sheet — `.xls.xlt`), **#6** (Exhibit D), **#7** (Exhibit E), **#8** (Exhibit E-1 PCS map), **#9** (Exhibit F Form 4109). **Exhibit A — HHS Solicitation Affirmations** is referenced in §1.4 of the IFB but **not in the drop** — pull from ESBD. |
| Scope (from §7.1 of the IFB) | "Complete demolition, structural reinforcement, industrial generator removal, and installation of a new commercial overhead door." Includes (a) metal roof removal + structural beam inspection/replacement, (b) decommission + crane-rigged extraction of non-working industrial generator (hazardous fluids drain — coolant/oil/fuel), (c) commercial overhead door + track install with cycle testing, (d) interior prep + industrial-grade paint (~198 sf), (e) site restoration. |

### G3 — TMD Camp Mabry Temporary Modular Office (RFI TMD26-CFMO-RFI001)

| Field | Value |
|---|---|
| Solicitation # | `TMD26-CFMO-RFI001` |
| Issuing agency | Texas Military Department (TMD) — Contract Management Branch, CFMO |
| Procurement type | **RFI (Request for Information)** — pre-solicitation, NOT a contract opportunity |
| Title | Camp Mabry — Temporary Modular Office Building |
| Site | Camp Mabry, building 37, 2200 W. 35th Street, Austin, TX 78703 |
| NIGP | 971-08 Pre-Fabricated Bldg Rental/Lease; 971-40 Mobile Office Rental/Lease |
| Issue date | 2026-05-26 |
| Site visits | 2026-06-09 13:00 CT (1st) / 2026-06-10 10:00 CT (2nd) |
| Questions deadline | 2026-06-18 16:00 CT |
| Q&A posted | ~2026-06-30 |
| Response deadline | 2026-07-14 16:00 CT |
| POC | Tom Picazo, CTCD — `FY26RFIPORT@cfmo.mil.texas.gov` |
| Future window | Building renovations estimated March 2027 – March 2030; modular capacity ≤150 personnel |
| Source files | File **#10** |

### G4 — TPWD Old Tunnel State Park Stair Replacement (IFB 802-26-79308)

| Field | Value |
|---|---|
| Solicitation # | `802-26-79308` (TPWD project number) |
| Issuing agency | Texas Parks and Wildlife Department (TPWD), State Parks Division |
| Procurement type | **IFB — Minor Construction** under Tex. Gov't Code Ch. 2155 + Ch. 2269 (state-funded; sealed-bid; best-value award) |
| Title | Stair Replacement at Old Tunnel State Park (lower loop stairs) |
| Site | 10619 Old San Antonio Rd, Fredericksburg, TX 78624 (**Kendall County**) |
| Issue date | 2026-05-26 |
| Site visit | Non-mandatory; schedule with Elizabeth (Izzy) Mabry, Park Superintendent — `Elizabeth.mabry@tpwd.texas.gov` — 830-765-8101 |
| Questions deadline | 2026-06-02 17:00 CT |
| **Response deadline / bid opening** | **2026-06-09 14:00 CT** |
| POC | Teresa Kay (CTCD), Purchaser V — `teresa.kay@tpwd.texas.gov` — 903-504-1815 |
| Term of contract | 30 calendar days from NTP |
| Bid security | 5% if total > $25,000 (bond with valid POA, PDF with bid) |
| Insurance | Workers Comp (statutory), Employer's Liability $1M/$1M/$1M, CGL $1M occurrence / $2M aggregate / $2M products-completed, Auto $1M CSL; State of Texas / TPWD additional insured & loss payee |
| Liquidated damages | $500/week (small flat — much lower than fed-construction norm) |
| Retainage | 10% reserved by TPWD until acceptance |
| Source files | File **#11** (single 48-page PDF: IFB cover + Attachments A General T&Cs, B Specifications + Prevailing Wage, C Drawings, D Qualifications Form, E Bid Schedule — all bound in one document) |

### G5 — USACE Fort Hood Staging/Marshalling Area (W9126G26RA015)

| Field | Value |
|---|---|
| Solicitation # | `W9126G26RA015` |
| Issuing agency | U.S. Army Corps of Engineers, **Fort Worth District** (W9126G is the USACE-Fort-Worth solicitation prefix) |
| Procurement type | **Federal RFP, Design-Bid-Build, Best-Value Tradeoff** under **FAR Part 15** |
| Title | Staging / Marshalling Area, Fort Hood (formerly Fort Cavazos), Texas |
| NAICS | 236220 — Commercial and Institutional Building Construction ($45M size standard) |
| Set-aside | **100% Total Small Business** (FAR 19.104-1) |
| Target price range | **$5,000,000 – $10,000,000** ⚠️ above BPC's current comfort zone |
| SBA Case Number | 347768 |
| Bid bond | **Required** (FAR 52.228-1) |
| P&P bonds | **Required** post-award (FAR 52.228-5 + FAR 52.228-15) |
| Issue date | May 2026 (cover); SF 1442 generated 2026-05-21 13:56 CDT |
| Response deadline | **Not visible in pages 1–6 of the compiled package.** First-page-only extraction did not surface the offer-due date — must be read off SF 1442 Item 13c after a deeper page scan or pulled from the SAM.gov posting. Action queued in `bids/usace-ft-hood-staging-W9126G26RA015/03-missing-documents.md`. |
| Source files | File **#12** — 1,835-page compiled RFP package containing SF 1442, CLIN schedule, Section 00 21 16 Instructions, full Divisions 00–33 spec book, and Appendix A J&A. |
| Scope summary (from CLIN schedule) | Base = construct primary facility (operations building, container loading aprons, docks/ramps, non-organizational areas) inside the 5-ft line + work outside the 5-ft line. **5 priced options:** security fence + gate, plus 4 tree-replacement options. |

## 3. Per-opportunity triage decisions

| Group | Decision | Slug | Playbook | Downstream artifact |
|---|---|---|---|---|
| G1 — Allen Veterans Memorial | **Path B — pursue / scaffold** (also: **first exemplar** of the `texas-municipal-csp` playbook) | `allen-veterans-memorial-2026-4-49` | [`texas-municipal-csp.md`](../../firm/playbooks/texas-municipal-csp.md) | [`bids/allen-veterans-memorial-2026-4-49/`](../allen-veterans-memorial-2026-4-49/) |
| G2 — HHSC Bldg 500 Mech | **Path B — pursue / scaffold** (caveat: on-site visit window already past; non-mandatory but a competitive disadvantage) | `hhs-bldg500-mech-HHS0017366` | [`texas-state-csp-hsp.md`](../../firm/playbooks/texas-state-csp-hsp.md) — *applies to state-funded IFBs as well as RFCSPs; no HSP for HHSC IFB-template solicitations under 2155.067* | [`bids/hhs-bldg500-mech-HHS0017366/`](../hhs-bldg500-mech-HHS0017366/) |
| G3 — TMD Camp Mabry Modular RFI | **Path C — no-go** (scope mismatch: BPC is a GC, not a modular-office reseller/leaser; NIGP 971-08/971-40 is outside BPC's NAICS 236220 lane) — captured as monitoring memo *and* no-go | n/a | n/a | [`bids/_NO_GO/2026-05-30-tmd-camp-mabry-modular-rfi-TMD26-CFMO-RFI001.md`](../_NO_GO/2026-05-30-tmd-camp-mabry-modular-rfi-TMD26-CFMO-RFI001.md) |
| G4 — TPWD Old Tunnel Stairs | **Path B — pursue / scaffold** (good fit: small TX state IFB; ~30-day POP; scope matches BPC's self-perform light-civil/carpentry sweet spot if the stairs are wood; needs site visit fast) | `tpwd-old-tunnel-stairs-802-26-79308` | [`texas-state-csp-hsp.md`](../../firm/playbooks/texas-state-csp-hsp.md) — *applies; TPWD IFBs use the standard TX state procurement framework* | [`bids/tpwd-old-tunnel-stairs-802-26-79308/`](../tpwd-old-tunnel-stairs-802-26-79308/) |
| G5 — USACE Fort Hood Staging | **Path B-light — scaffold + flag for go/no-go review** (also: **first exemplar** of the `federal-rfp-best-value-tradeoff` playbook). $5–10M target is well above BPC's recent bid range (sub-$1M sweet spot); needs an explicit capacity + bonding-capacity check before any sub outreach starts. | `usace-ft-hood-staging-W9126G26RA015` | [`federal-rfp-best-value-tradeoff.md`](../../firm/playbooks/federal-rfp-best-value-tradeoff.md) | [`bids/usace-ft-hood-staging-W9126G26RA015/`](../usace-ft-hood-staging-W9126G26RA015/) |

## 4. Cross-batch learnings

Captured separately in [`firm/playbooks/_learning-log.md`](../../firm/playbooks/_learning-log.md). Headlines:

1. **HHSC PCS 137 = state IFB template, not CSP.** Texas-state procurement framework supports both Ch. 2269 CSPs (already exemplified in the playbook pack) and Ch. 2155 IFBs. The `texas-state-csp-hsp.md` playbook needs a sibling page (or a clear note) that covers the IFB variant — different evaluation method, no HSP under §2155.067-issued IFBs, different exhibit structure (Exhibits A–F under PCS 137).
2. **TX municipal CSP is real and active.** This batch surfaces the first concrete exemplar (Allen 2026-4-49) for the `texas-municipal-csp.md` playbook, which had been listed as "not yet exemplified" in the playbook README. The Allen IFB also uses IonWave (same portal family as CISD's CHS Cafeteria) — confirms IonWave is the dominant Tex. municipal/ISD CSP portal.
3. **TPWD Minor Construction IFB is a new agency-template archetype.** TPWD State Parks Division uses a specific 48-page bound IFB template with Attachments A–E (General T&Cs, Specs, Drawings, Qualifications, Bid Schedule). Worth seeding a TPWD-specific section into the state CSP playbook the next time a TPWD opp lands.
4. **USACE Fort Worth District prefix W9126G.** Fort Hood was renamed *back* from Fort Cavazos; the RFP uses both names ("Fort Hood (formerly Fort Cavazos)") in the spec book. Worth indexing W9126G as a known prefix in the federal pre-solicitation watchlist playbook so future BPC SAM saved-searches catch USACE-FWD postings.
5. **Park & rec scope vocabulary** — Old Tunnel State Park stairs (replacement of a *lower-loop stair*) is the first park-trail-infrastructure opportunity BPC has triaged; Allen Veterans Memorial at Bethany Lakes Park is the first park-amenity / hardscape / monument-expansion opportunity. Neither is "Renovation of Park and Recreation Center Facilities (4024120)" as framed in the intake, but both fall under a **parks & recreation scope domain** that no current `firm/scope-templates/` page covers. Seed a `parks-rec-amenity-improvements.md` scope template the next time a parks/rec opportunity needs a takeoff scaffold.
6. **Camp Mabry RFI** — modular-office-rental scope is **out of NAICS 236220**. RFI responses *can* be a low-cost market-intelligence play, but only if the responder has a credible offering in NIGP 971-08/971-40. BPC does not, so this is a clean no-go. Capture as a memo so the next "modular office at a TMD facility" RFI is recognized in <5 min.
7. **OneDrive `Landmark/` is a client/team folder, not an opportunity name.** Earlier workspaces (b1710, SAAN, McFaddin NWR) already cite OneDrive paths under `Blueprint Constructs/Landmark/05072026/`. The intake brief's "Landmark / Renovation of Park and Recreation Center Facilities (4024120)" was a misreading of the folder name — the folder is just where Rocky stages downloads dated by `MMDDYYYY`. Update intake conventions so future briefs cite the **agency + solicitation number**, not the staging folder name.
8. **No file referenced project number `4024120`** anywhere in the 12 PDFs. Treat the `opp_4024120_clarify` watchlist key (referenced in the intake brief) as not-resolved-here — there is no actual document in this batch that pertains to that project number. The user may want to verify whether `4024120` is real (perhaps it was a stale Rocky shorthand or a digit from a different ESBD posting).

## 5. Sanity checks performed

- ✅ `Test-Path` confirmed source folder exists and is reachable.
- ✅ `Get-ChildItem -Recurse` returned exactly 12 file entries (no subdirectories, no hidden files).
- ✅ MD5 head-hash (first 64 KiB) computed per file — all 12 are unique, no intra-batch dedupe candidates.
- ✅ Source folder treated as read-only throughout — no writes, deletes, or moves performed on OneDrive.
- ✅ No file copied into `inbox/` (which is gitignored). Per repo convention, large source PDFs stay in OneDrive and each `bids/<slug>/source-files-manifest.md` cites the OneDrive paths.
- ✅ First-page text scanned for restricted-class triggers (PII beyond contact info; payment data; regulated data). None detected. All forms (Exhibit D bidder-qualifications form, Exhibit F TIN application) are *blank* templates for the bidder to complete.
- ✅ No LLM calls invoked (`analyze.py` not run; pypdf used only for deterministic text extraction).
- ✅ No edits made under `core/`, `tests/`, `prompts/`, or any Python source — work confined to `bids/`, `firm/playbooks/`.

## 6. Future-slice handoff

The four pursue-scaffolds (G1, G2, G4, G5) are **template-grade** — they contain the extracted-from-source facts (dates, contacts, scope outlines, key risks) but every workspace still has `[USER TO FILL …]` markers for firm-side data and `[NEEDS DEEPER READ]` markers wherever first-page extraction wasn't enough. A future slice should:

1. For each pursue workspace, run `firm/_scripts/apply_firm_profile.py` to back-fill firm-internal values.
2. Run `firm/_scripts/scan_placeholders.py` to enumerate remaining `[USER TO FILL]` markers and triage them with Rocky.
3. For G5 (Fort Hood), do the **explicit go/no-go review first** before any sub outreach — the $5–10M magnitude is 5–10× recent BPC bids and the bonding capacity / capacity-to-self-manage check should gate further investment.
4. For G2 (HHSC Bldg 500), determine whether the missed 5/28–5/29 site visit is a competitive disqualifier or merely a disadvantage — questions deadline is 6/1 so we have very little air time.
5. For G3 (no-go), no further action — memo on file.
