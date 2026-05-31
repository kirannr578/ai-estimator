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
