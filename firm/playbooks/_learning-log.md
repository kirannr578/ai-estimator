# BPC playbooks — learning log

This file is **append-only**. Each entry is dated and sourced. Future agents and estimators add new entries to the **bottom** of this file; do not rewrite or condense existing entries. When the same date hosts entries from multiple sources, append in source order.

## Entry format

```
## YYYY-MM-DD — <source short name>

**Source:** <full source citation>
**Volume:** <count of opportunities triaged in this source>
**Breakdown:** <strong / no-go / watchlist / info / skip counts>

### Novel scope domains
- ...

### Playbook gaps
- ...

### Recurring patterns
- ...

### Followups
- ...
```

---

## 2026-05-30 — DFWMSDC Construction Members digest (email body, Public-class)

**Source:** DFWMSDC Construction Members mailing-list digest dated 2026-05-30, received as plain email body (not a folder of PDFs). Per data-classification policy, the digest content is Public-class (publicly distributed mailing list); contact info from the digest is scoped to per-bid workspaces only and is not surfaced into `firm/firm-profile.md` or any global file.

**Volume:** 13 opportunity slots in the digest, of which 3 (#7, #10, #11) were empty placeholders.

**Breakdown:** Across 10 actual opportunities:
- **Strong-fit scaffolds (2):** McLennan Community College CSC Cosmetology Phase 4 (`bids/mcc-cosmetology-phase4-2026-0622/`); 7-Eleven Celina ground-up (`bids/7eleven-celina-2026-0605/`)
- **No-go memos (3):** Plano Legacy Trail Pond Restoration; Kingsville Storm Water Improvements (CDBG-MIT); UT Dallas ECE Bootcamp Education RFP
- **Watchlist (2):** Adam's Trade & Services Powderly Bldg. 1; BCI Belisle Longhorn Steakhouse Little Elm
- **Informational (2):** City of Dallas Small Business Assistance Program (real-estate / capital-improvement grant); City of Irving Purchasing registration page
- **Skip (1):** FIFA World Cup Dallas vendor opportunities (event services + likely-expired Jan 9 deadline; not construction)

### Novel scope domains

- **Pond restoration via hydraulic dredging + dewatering** (City of Plano, Bid 2026-0422-B). NAICS 237990 / 562910. Outside BPC's NAICS lane; flagged as a "route-to-no-go" scope domain in the no-go memo. Trigger phrases: *dredging, dewatering, sediment removal, pond restoration, lake restoration, silt removal, wetland mitigation*.
- **Municipal storm-water utility construction (CDBG-MIT funded)** (City of Kingsville, Bid 26-04). NAICS 237110. Outside BPC's NAICS lane; flagged as "route-to-no-go" scope domain. Trigger phrases: *storm water improvements, water and sewer line, lift station, manhole rehabilitation, capital storm-drainage*. Note: CDBG-MIT (GLO Contract 22-085-...) is a real funding stream that **could** match BPC's lane on residential rehab / facility renovation projects in DFW counties — track GLO at `https://recovery.texas.gov/` for North-Texas-region scope-fit projects.
- **Non-credit education / workforce-development services** (UT Dallas RFP UTD20260301-AN). NAICS 611xxx / 541xxx. Different industry; flagged as "route-to-no-go" scope domain. Trigger phrases: *bootcamp, non-credit, workforce development, re-skilling, up-skilling, curriculum, instructional, training delivery*.
- **FIFA World Cup event-services vendor opportunities** (DFWMSDC #13). Event services (catering, fencing, dumpsters, IT, sanitation, security guards, canine detection, viewing platforms). Different industry from construction. Flagged as "route-to-skip" — these are NAICS 561xxx / 711xxx event-services opportunities that DFWMSDC distributes alongside construction opportunities because the host vendor program is centrally administered. Recognize the event-services framing and skip without further triage.

### Playbook gaps

- **No "private GC sub-bid" playbook exists.** Both pursue scaffolds in this batch (`mcc-cosmetology-phase4-2026-0622`, `7eleven-celina-2026-0605`) are subcontractor quotes to private commercial GCs (HCS Inc. and Ready Construction respectively). The current `firm/playbooks/README.md` procurement-type matrix lists "Private commercial / institutional negotiated" only as an "ad-hoc; not playbook-grade" row at the bottom. **Recommend** seeding `firm/playbooks/private-gc-sub-bid.md` the next time a GC sub-bid lands. The playbook would cover:
  - Identifying the GC's standard sub bid form layout (or absence thereof) and mapping BPC's quote structure to match
  - Sub-tier insurance / additional-insured wording (typical: GC + project owner named as AI; primary-and-non-contributory + waiver of subrogation)
  - MBE / HUB cert positioning on private projects (cert is a credential, not a scoring lever, but DFWMSDC channel implies the GC is seeking diversity sub coverage)
  - When to decline rolled-up multi-trade quotes vs. single-trade self-perform quotes (function of fuse length and BPC sub-network maturity)
  - Brand-specific specification handling (Royston, Mapes, Pac-Clad, Jimco, Porter SIPs in 7-Eleven brand standard; cosmetology-station MEP pattern in higher-ed cosmetology labs)
  - Geographic-stretch pricing convention (when project is outside BPC's DFW core radius — Waco, Lamar County, etc.)

### Recurring patterns

- **DFWMSDC blasts mix sub-bid invitations with public-agency primes.** This batch has 2 GC sub bids (HCS / Ready), 2 public-agency primes (Plano / Kingsville), 1 prime RFP from a higher-ed institution (UTD), 2 watchlist (Adam's Trade / BCI Belisle private GCs), 2 informational (Dallas SBA program, Irving Purchasing registration), and 1 event-services skip (FIFA). Triage must classify by *procurement type AND scope*, not by source channel.
- **Portal-locked plans are the dominant access pattern.** Of the 4 pursue-track opportunities (2 strong + 2 watchlist), all 4 require portal access (HCS Box, Autodesk BuildingConnected, BCI Belisle password-protected portal, Adam's Trade email-attached). Cursor agents have no creds and no browser MCP for these portals — every workspace gets an `attachments/_PORTAL_ACCESS.md` file with `[USER ACTION REQUIRED]` markers.
- **Geographic distribution is wider than DFW.** This batch reaches: Waco (McLennan County, ~95 mi south), Powderly (Lamar County, ~95 mi NE), Plano (Collin County, in-region), Kingsville (Kleberg County, ~360 mi south — way out), Celina (Collin County, in-region), Little Elm (Denton/Collin border, BPC's home town), Dallas / Irving (in-region informational), Richardson (Collin County, UTD location). The far-south outlier (Kingsville) suggests DFWMSDC forwards from beyond the DFW chamber when the program-funding source cuts a wider net — at intake, **screen the site location first** and route ≥ 200-mile-from-DFW opportunities directly to no-go.
- **MBE / HUB / SBE positioning matters at multiple tiers.** DFWMSDC blasts surface opportunities specifically because the GC or agency is seeking diversity sub coverage. BPC's DFW MSDC certs (MBE DL09279, SBE DL09279, TX HUB VID 1874292998900) are expired per `firm/firm-profile.json` (all expired 2024-08-31). **Recertification is a precondition** for BPC to credibly leverage the DFWMSDC channel. Surface as a firm-side action item independent of any single bid.
- **Bid forms come in three shapes:** (a) the GC's roll-up form ("Owner's Proposal Form" — McLennan / HCS), (b) an open-format email quote (Adam's Trade — Powderly), (c) portal-uploaded standard form (Ready Construction — BuildingConnected). Each shape changes BPC's quote-formatting workflow; flag the shape early in the bid-prep checklist.

### Followups

- [ ] **Recommend:** seed `firm/playbooks/private-gc-sub-bid.md` from the next GC sub-bid that lands (this batch alone is enough material to draft the playbook, but the user task-brief asked for triage + scaffold only, not playbook authoring)
- [ ] **Recommend:** seed `firm/scope-templates/cosmetology-classroom-reno.md` once the McLennan plans are in hand
- [ ] **Recommend:** seed `firm/scope-templates/c-store-fueling-pad-interior-finishes.md` once the Ready Construction plans are in hand
- [ ] **Firm-side action (Rocky):** recertify DFW MSDC MBE / SBE / HUB before any bid in the DFWMSDC channel can credibly leverage diversity positioning
- [ ] **Firm-side action (Rocky):** confirm renewed Commercial GL COI exists; the 2024-09-25 expiration on the on-file policy blocks every private GC sub-bid in this batch from getting to award
- [ ] **Firm-side action (Rocky):** subscribe BPC's vendor profile to (a) Plano IonWave (`https://planotx.ionwave.net`) and (b) UT Dallas Bonfire (`https://utdallas.bonfirehub.com`) for future BPC-lane construction opportunities at those agencies
- [ ] **Optional outreach:** introduce BPC's capability statement to Reginald Cleveland (UTD Small Business Office, `reginald.cleveland@utdallas.edu`) — separate from any RFP response — so BPC is on UTD's radar for future facility-construction set-asides

### Information-only entries (no workspace, no tracker row)

These two opportunities from the digest are **not bids** but are worth indexing for reference:

1. **City of Dallas Small Business Assistance Program** (DFWMSDC #8) — citywide grant program for small-business real-estate / capital-improvement projects ($150K minimum in Target Areas / $250K outside; ≥75% non-City funding required; project total < $2M; ≤20 employees). This is a **funding source** for BPC's *clients* (small-business owners renovating storefronts), not a bid for BPC. **Sales-channel signal:** if BPC works with DFW small-business owners renovating Dallas storefronts (residential remodel + commercial fit-out cumulative experience supports this), referencing this Dallas SBA program in BPC's marketing materials helps clients identify funding.
2. **City of Irving Purchasing registration page** (DFWMSDC #12) — vendor-registration landing page (`https://lp.constantcontactpages.com/ev/reg/rgjktfk`), 835 W. Irving Blvd., Irving, TX 75060. Not a bid; just a registration link. **Firm-side action:** subscribe BPC's vendor profile to City of Irving Purchasing for future Irving-area BPC-lane opportunities.

### Skip note

**FIFA World Cup Dallas — 20 bid opportunities** (DFWMSDC #13). Event-services scope (guards, catering, fencing, dumpsters, sanitation, IT, production, etc.) — outside BPC's construction lane. Match-day deadline of "Jan 9" with no year stated; given the digest receipt date of 2026-05-30 and the match dates given (Jun 14 / Jun 17 / Jun 22 / Jun 25 / Jun 27, 2026), the Jan 9 deadline is most consistent with **Jan 9, 2026** — already past by ~5 months at digest receipt. Even if Jan 9 referred to Jan 9, 2027 (post-tournament), the scope is still outside BPC's lane. No memo required; one-line note here for completeness.

### Empty digest slots

DFWMSDC digest slots #7, #10, and #11 were empty in the source email body. These are placeholder rows the digest format uses; no action required. Recurrence in future digests is normal.

---

## 2026-05-30 — OneDrive `Landmark/05272026` batch (Private-class folder)

**Source:** Folder dump at `C:\Users\rnuduru1\OneDrive\Blueprint Constructs\Landmark\05272026\` (12 files, ~14 MiB total). Files are ESBD-posted IFB/RFI packets + 1 SAM.gov federal RFP — Private-class. Deterministic ingest only (no LLM calls); first-page text extraction via `pypdf`. Full inventory + per-opportunity grouping at [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../../bids/_TRIAGE/2026-05-27-onedrive-batch.md).

**Volume:** 12 source files resolving to **5 distinct opportunities** (not 1 as the intake brief assumed).

**Breakdown:**
- **Path-B full scaffolds (3):** Allen Veterans Memorial 2026-4-49; HHSC Bldg 500 Mechanical Room Renovation HHS0017366; TPWD Old Tunnel State Park Stair Replacement 802-26-79308
- **Path-B-light scaffold + explicit go/no-go gate (1):** USACE Fort Hood Staging/Marshalling Area W9126G26RA015 ($5M-$10M federal RFP, magnitude 5-10× BPC's typical bid)
- **Path-C no-go memo (1):** TMD Camp Mabry Temporary Modular Office RFI TMD26-CFMO-RFI001 (RFI for modular-office rental, NIGP 971-08/971-40 — scope mismatch)

### Novel scope domains

- **City-park amenity / monument / hardscape** (Allen Veterans Memorial at Bethany Lakes Park, City of Allen). Concrete plaza, stone/brick seat walls, plaque pedestals, OFCI monument install, site lighting, flagpole, landscaping/irrigation tie-in, dedication signage. **Not represented in `firm/scope-templates/`** — recommend seeding `firm/scope-templates/parks-rec-hardscape-memorial.md` once the Allen plans are deeper-read.
- **State-park trail infrastructure** (TPWD Old Tunnel State Park lower-loop stairs). Pressure-treated lumber stair framing, helical-pile or concrete-pier foundations, ADA-vs-trail handrails, erosion control with TX-native vegetation per 34 TAC 20.38, wildlife-biology coordination (Old Tunnel SP is a bat-colony park). **Not represented in `firm/scope-templates/`** — recommend seeding `firm/scope-templates/park-trail-infrastructure.md` once the TPWD drawings are in hand.
- **Federal-installation staging/marshalling apron + operations building** (USACE Fort Hood W9126G26RA015). Roller-compacted concrete paving (Section 32 13 13.17), chain-link AT/OPSEC fencing (Section 32 31 13), FRCS cybersecurity at moderate-impact level (Section 25 05 11.01), BACnet DDC controls (Section 23 09 23.02), facility fall protection (Section 11 18 29), Special Project Procedures for Fort Hood (Section 01 35 10.00 44). Federal-installation-specific spec families.
- **HVAC mechanical-room renovation at a state hospital state-school facility** (HHSC Building 500, Mexia State Supported Living Center — Limestone County). Replace 6 AHUs ranging 7,500-12,500 CFM, 41 VAV terminals, MEP rework within an occupied mechanical room of a state-operated long-term-care facility for individuals with intellectual disabilities. Specialty consideration: **occupied facility serving a vulnerable population** — bonding capacity and past-performance requirements may include sensitivity to disruption of life-safety systems.
- **Bat-colony / wildlife-coordination construction window constraint** (TPWD Old Tunnel SP — Texas's largest urban-accessible bat colony, ~3M Mexican free-tailed bats roosting Mar-Oct). Likely construction window restricted to bat-absence months (Oct-Mar); cross-reference any future TPWD/USFWS scope at karst-cave or bat-roost sites.

### Playbook gaps

- **`texas-state-csp-hsp.md` does not cover Ch. 2155 IFBs.** The existing playbook is scoped to Tex. Gov't Code Ch. 2269 Competitive Sealed Proposals with mandatory HSPs. This batch surfaces **two state IFBs** (HHSC HHS0017366; TPWD 802-26-79308) issued under Ch. 2155.067 with materially different mechanics (lowest-responsible award; no HSP; VPTS pass/fail; negotiations prohibited; PCS 137 / TPWD Minor Construction templates). **Recommend** either adding a "Ch. 2155 IFB variant" section to `texas-state-csp-hsp.md` or splitting into a separate `texas-state-ifb.md` playbook.
- **`texas-municipal-csp.md` was listed as "not yet exemplified"** in `firm/playbooks/README.md`. Allen Veterans Memorial 2026-4-49 is the **first BPC exemplar**. Confirms the playbook's framing that municipal IFBs labeled "Invitation for Bid" frequently operate as best-value CSPs under Tex. Local Gov't Code Ch. 252; the published label is unreliable, the award language in the bid invitation governs.
- **`federal-rfp-best-value-tradeoff.md` (or whichever federal playbook covers FAR Part 15 negotiated source selection) needs a first exemplar.** USACE Fort Hood Staging W9126G26RA015 is BPC's first exposure to a Design-Bid-Build federal RFP at this scale ($5M-$10M, 100% TSB set-aside, 7 CLINs including options). The scaffold at `bids/usace-ft-hood-staging-W9126G26RA015/` should serve as the playbook exemplar once the go/no-go decision is made.
- **No "TPWD Minor Construction IFB" subsection exists anywhere.** TPWD's 48-page IFB template combines a distinct cover page (TX bidder-preference checkboxes spanning Title 34 TAC 20.38), §§1-25 main body, Attachment A General T&Cs for Minor Construction (Sept 2025), Attachments B Specs + Prevailing Wage / C Drawings / D Qualifications / E Bid Schedule. Distinctive features: VPTS pass/fail gate, State + TPWD as additional insured AND loss payee (dual designation is non-standard), 10% retainage tied to warranty + O&M documents, email-only submission with specific subject-line format, cover-page manual signature = pass/fail. Recommend adding a "TPWD Minor Construction" subsection wherever the state-IFB playbook content lands.

### Recurring patterns

- **OneDrive `Landmark/MMDDYYYY/` is a staging directory, not an opportunity name.** Earlier BPC bid workspaces already cite `Landmark/05072026/` for opportunities from a different batch. The 2026-05-27 intake brief framed `Landmark/05272026/` as a single "Landmark / Renovation of Park and Recreation Center Facilities (4024120)" opportunity; this is incorrect — no file references project number `4024120` or that phrase. Future intake conventions: **cite agency + solicitation number as the canonical opportunity ID; treat `MMDDYYYY` as a timestamp, not an opportunity identifier.**
- **RFI ≠ solicitation.** This batch includes 1 RFI (TMD Camp Mabry TMD26-CFMO-RFI001) mixed in with IFBs + 1 RFP. Naive triage allocates per-opportunity scaffold time to the RFI; correct triage detects "Request for Information" + "for information gathering and planning purposes" in the cover and routes to either a watchlist memo (if BPC has scope alignment) or a no-go memo (if BPC has scope misalignment). **Convention:** scan all batch files for `RFI` / `Sources Sought` / `Industry Day` in filenames before allocating scaffold time.
- **Disqualifying scope codes.** NIGP **971-08** (Pre-Fab Building Rental/Lease) and **971-40** (Mobile Office Rental/Lease) are disqualifying for BPC's NAICS 236220 GC lane — these are rental/lease product opportunities, not construction. **Add as automatic-no-go filters to BPC's ESBD watchlist.**
- **USACE Fort Worth District prefix W9126G.** The Fort Hood Staging RFP (W9126G26RA015) is BPC's first W9126G-prefix exposure. USACE-FWD also serves the Belton-area corps lakes, Fort Hood / Fort Cavazos installations, and DFW-area civil-works. **Convention:** add `W9126G` as a known USACE-FWD prefix in `federal-pre-solicitation-watchlist.md`; the Fort Hood installation name reverted from "Fort Cavazos" (2023) back to "Fort Hood" (late-2025) — future SAM saved-searches should match on *both* names.
- **Magnitude disparity within a single batch.** This batch ranges from a likely-sub-$500K TPWD minor-construction IFB to a $5M-$10M federal RFP — a 10-20× spread inside a single OneDrive drop. Triage convention: **classify by magnitude tier first**, then allocate scaffold depth proportionally (full scaffold for in-range bids; explicit go/no-go gate for out-of-range bids before any deep estimating investment).
- **Portal diversity.** This batch surfaces **four distinct portals** in 5 opportunities: IonWave (City of Allen), HHS IAMOnline Online Bid Room, TPWD email-only (`teresa.kay@tpwd.texas.gov`), and SAM.gov + Procurement Integrated Enterprise Environment (PIEE) for USACE. The Camp Mabry RFI is ESBD-only. **Convention:** each new portal earns a one-line entry in the bid workspace's `02-bid-prep-checklist.md` "Portal registration" gate; deduplicate registration effort across bids by tracking which portals BPC's vendor profile is already on.

### Followups

- [ ] **Recommend:** seed `firm/scope-templates/parks-rec-hardscape-memorial.md` from Allen Veterans Memorial drawings once they're deeper-read
- [ ] **Recommend:** seed `firm/scope-templates/park-trail-infrastructure.md` from TPWD Old Tunnel drawings once they're in hand
- [ ] **Recommend:** add "Ch. 2155 IFB variant" section to `texas-state-csp-hsp.md` (or split into separate `texas-state-ifb.md`) covering HHS PCS 137 + TPWD Minor Construction templates, IAMOnline registration flow, VPTS gate, dual-AI-loss-payee insurance pattern
- [ ] **Recommend:** mark `texas-municipal-csp.md` "BPC bids that exemplify it" column in `firm/playbooks/README.md` to cite Allen Veterans Memorial as the first exemplar
- [ ] **Recommend:** mark `federal-rfp-best-value-tradeoff.md` (or applicable federal playbook) "exemplar" column to cite Fort Hood Staging W9126G26RA015 (pending go/no-go outcome)
- [ ] **Firm-side action (Rocky):** decide go/no-go on Fort Hood Staging per [`bids/usace-ft-hood-staging-W9126G26RA015/go-no-go-decision.md`](../../bids/usace-ft-hood-staging-W9126G26RA015/go-no-go-decision.md) — bonding + past-performance + capacity gates
- [ ] **Firm-side action (Rocky):** confirm whether HHS Bldg 500 mandatory site visit on 2026-05-20 was attended; if missed, the HHS bid (HHS0017366) is non-responsive and the workspace should be re-routed to a no-go memo with "missed mandatory site visit" rationale
- [ ] **Firm-side action (Rocky):** the `opp_4024120_clarify` watchlist key referenced in the 2026-05-27 intake brief **does not exist in this repo** (no file under `bids/_WATCHLIST/`, no other source references `4024120`). Treat as a phantom reference; if Rocky has a real `4024120` lead, ask him to point at the source document or close the placeholder as stale
- [ ] **Recommend:** add `W9126G` to `federal-pre-solicitation-watchlist.md` as a known USACE-FWD prefix; index `Fort Hood`, `Fort Cavazos`, and Killeen-area installation keywords
- [ ] **Recommend:** tag NIGP **971-08** and **971-40** (and similar prefab/modular/leasing codes) as **disqualifying scope codes** in BPC's ESBD watchlist filters — automatic no-go

### `opp_4024120_clarify` resolution status

The 2026-05-27 OneDrive batch was triaged in [`bids/_TRIAGE/2026-05-27-onedrive-batch.md`](../../bids/_TRIAGE/2026-05-27-onedrive-batch.md) and found to contain **5 distinct opportunities, none of which reference project number `4024120` or "Renovation of Park and Recreation Center Facilities"**. The OneDrive folder name "Landmark" is a staging directory, not an opportunity name. The `opp_4024120_clarify` watchlist key has no associated file in `bids/_WATCHLIST/` and no other repo references it. **Status:** ❌ Not resolved — appears to be a stale or phantom reference. See `bids/_WATCHLIST/README.md` "Resolved / closed watchlist items" table.

---

## 2026-05-30 (continued) — McLennan Cosmetology + Camp Maxey ingest

- **Source:** HCS Box folder downloaded by user as `Phase 4 CSC Module B Cosmetology.zip` (20.8 MB, 3 PDFs / 19.9 MB / 453 pp) + standalone Adam's Trade & Services PDF *Camp Maxey Roof Replacement Project Information -2.pdf* (8 pp, 2 MB). Both staged in OneDrive `Landmark/` catch-all (Landmark is a staging dir, not an opportunity ID — confirms 2026-05-30 (Landmark batch) recurring pattern). Deterministic ingest only — `zipfile` + `pymupdf.fitz`; no LLM calls (OpenAI quota exhausted).
- **McLennan:** Enriched DFWMSDC scaffold from actual specs/drawings. **MCC** is the procuring entity (not HCS as the DFWMSDC framing implied) — running a **Texas Higher-Ed CSP** with weighted criteria (price 25%, office-near-college 5%, etc.); HCS is one of multiple competing GCs sourcing subs through DFWMSDC. **Davis-Bacon prevailing wages apply** (PM §1.17 + Section 007343 in ToC). Project no. **25062** (RBDR PLLC architect, EMA Engineering MEP). Procurement: 414-page PM + 37-sheet drawings + 2-page Section 004213 lump-sum CSP form. Spec ambiguity: PM §1.01 carries non-cosmetology "netting and artificial turf" template-carry-over text (RFI fodder).
- **Camp Maxey:** Converted prior watchlist [`powderly-bldg1-adams-trade-2026-0626.md`](../../bids/_WATCHLIST/powderly-bldg1-adams-trade-2026-0626.md) → pursue scaffold [`bids/tmd-camp-maxey-roof-2026-0626/`](../../bids/tmd-camp-maxey-roof-2026-0626/). Same prime (Adam's Trade & Services), same PM (Patrick Grabowski), same address (6351 US 271 N Powderly), same dates as the watchlist tracked — confirmed identical opportunity. Scope: TMD-owned **lower + upper TPO re-roof** on Bldg. 1 (60-mil TPO + 1/2" HD ISO + 24-ga drip edge / counterflashing / gutters / DS). **Davis-Bacon + Buy American Act both apply** (PDF §§1.5 + 5.2). Background checks by TMD Owner per §5.1.
- **Novel scope domains:** **Commercial flat-TPO re-roof** (Camp Maxey) — first BPC exposure. **Cosmetology classroom MEP** with chemical-resistant fluid-applied flooring (096700) + plam casework + quartz countertops + shampoo-bowl plumbing — first BPC exposure (closest existing template `office-tenant-refurb.md` does not capture cosmetology specifics).
- **Playbook gaps:** (a) `firm/scope-templates/commercial-tpo-reroof.md` does not exist — `roof-repair-historic.md` is **NOT a fit** (NPS / SHPO overlay does not apply to TMD National Guard training facilities); recommend seeding from Camp Maxey takeoff. (b) `firm/scope-templates/cosmetology-classroom-reno.md` does not exist — recommend seeding from McLennan takeoff. (c) "Private GC sub-bid" playbook gap from earlier today's DFWMSDC entry remains open and is reinforced by both opportunities.
- **Documentation patterns observed:** (a) **OneDrive `Landmark/` catch-all is now confirmed-as-pattern** — files arrive as catch-all regardless of opportunity owner; intake convention is to read each file's content (not folder name) to determine the owning opportunity. (b) **Watchlist→pursue conversion** is triggered by document arrival, not always by site-visit attendance — when a scope-clarifying document lands before the planned decision gate, convert immediately and retain the watchlist for lineage. (c) **Lump-sum CSP form vs. line-itemized GC sub-template** can both apply at different tiers in the same procurement (MCC's 004213 is single lump-sum; HCS's internal sub template asks for line-items + alternates) — surface this distinction at intake to avoid mis-framing the form structure.

---
