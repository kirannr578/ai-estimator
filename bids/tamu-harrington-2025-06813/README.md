# Bid prep — TAMU Harrington Education Center, Lab 303 Renovation

**Solicitation:** 2025-06813
**Agency:** SSC Services for Education (on behalf of Texas A&M University, Part 02)
**Project:** Harrington Education Center, Bldg 0435 — Lab 303 (Science Education Classroom/Lab) renovation
**Location:** College Station, TX 77843
**Status:** **DRAFT — BLOCKED ON ELIGIBILITY CONFIRMATION** (CSP package was pulled from the e-Builder portal on 2026-05-23; the remaining blocker is written confirmation that a firm which missed the 5/14 pre-proposal meeting can still submit a responsive proposal)

---

## Portal access status

- **Attempted:** 2026-05-23
- **URL:** `https://app.e-builder.net/public/publicLanding.aspx?QS=323d686fd1304ccbb2a0ee7d143af64b`
- **Result:** **PUBLIC** (no registration required; ASP.NET WebForms + iframe-driven downloads via three-redirect chain through `FileDownload_mgr.aspx` → `FileDownload_act.aspx` → POST to `filedownload_filedownload_act.aspx`). 4 of 5 files downloaded cleanly; the 5th was intercepted by the corporate network's Zscaler Cloud Browser Isolation (returns a CBI handshake HTML, not the PDF).
- **Files now in `inbox/opportunities/attachments/2026-05-21/tamu-csp/`** (also enumerated in `source-files-manifest.md`):
  - `Harrington_Lab303_Drawings.pdf` — 5.6 MB, 10-sheet set dated 5/7/2026, "Issued for Construction"
  - `Harrington_Lab303_Specifications.pdf` — 5.3 MB, 308-page project manual
  - `Pre-Bid_Attendance.pdf` — 162 KB, 5/14 sign-in sheet (scanned image)
  - `Notice_of_Project_2026-05-08.pdf` — 264 KB, portal copy of the same Notice already in `ESBD_514190_...`
  - `H2I_Casework_Sub-06_2026-05-13.FAILED.html` — Zscaler CBI handshake page in place of the 8.1 MB PDF. **User must download this file from the portal in a regular browser** (no network restrictions), or ask Joelle to re-share by email (folded into outreach 01).
- **Estimated user time to retrieve the H2I file manually:** 5 minutes (open the public landing URL in a browser outside the corporate network, select the H2I row, click Download).

## PROPOSAL STATUS

> **`DRAFT — BLOCKED ON ELIGIBILITY CONFIRMATION + INTERNAL GO/NO-GO`**
>
> Proposal-draft scaffold lives in `proposal/`. Ready-to-send outreach lives in `outreach/`. The proposal cannot move out of DRAFT state until the three-row go/no-go gate below closes green.

### Go / no-go gate (sequential — each row blocks the next)

| # | Gate | Trigger | Deadline | If miss | Status |
|---|---|---|---|---|---|
| 1 | **Eligibility confirmed** post-missed 5/14 pre-proposal meeting | Joelle Shidemantle (SSC PM) confirms in writing that a non-attending firm can still submit a responsive proposal | **EOD Mon 2026-05-24** | If pre-proposal meeting was mandatory and there is no late-arriver accommodation: **walk away** | 🟡 Eligibility ask now has a **parallel TAMU-procurement-side path via Cherise Toler at (979) 845-5887 / `ctoler@tamu.edu`** if the SSC channel (Joelle) is slow. Cherise is the official TAMU-side solicitation officer per ESBD and can confirm procedurally whether the 5/14 meeting was mandatory. Cc her on outreach 01 from the outset. |
| 2 | **e-Builder CSP package downloaded + scanned** | Full CSP package pulled from e-Builder portal: drawings sheet count > 0, specs enumerated, pricing form + HSP/VetHUB form + sample agreement + UGSC identified | **EOD Tue 2026-05-26** (within 24 hrs of G1 close) | If portal still gated by Wed 5/27, escalate to TAMU System OFPC; if no path by Thu 5/28, **walk away** | ✅ **CLOSED GREEN on 2026-05-23.** 4 of 5 files pulled cleanly; H2I casework Sub-06 file pending (re-share request folded into outreach 01). Pricing form is SSC Section 00 42 13 (CSI-Division line-item table). HSP/VetHUB form is Section 00 45 17.1 → references TX State Subcontracting Plan (Rev. 5/26) — uses the **VetHUB (Veteran Heroes United in Business)** framework, NOT the older HUB Subcontracting Plan format. Sample agreement is the SSC / Compass **Master Vendor Agreement** (Section 00 52 63) between Compass Group USA and the sub — NOT a TAMU SGC variant. **No bid bond is required** by this CSP — only Performance Bond (00 61 13) and Payment Bond (00 61 14) at award. |
| 3 | **Internal go/no-go meeting** | PM + estimator + safety lead review now-known scope, schedule, and HSP feasibility; deliver decision | **EOD Tue 2026-05-26** | If no-go: archive folder under `local/`, notify Joelle as a no-bid courtesy | 🟡 Ready to convene once G1 closes. Scope from drawings is **modest** (Lab 303 only; 10-sheet drawing set; Divisions 06 limited to 06 10 00 Rough Carpentry only — i.e. no large carpentry scope in the specs; Divisions 03, 04, 05, 08, 11, 12, 13, 14 all "NOT USED"). Refer to refined `04-scope-of-work.md` for the trade list. |

**If gate 1 slips, the bid is not viable and we walk. Gates 2 and 3 are now within reach.**

### Single most important action Monday 8 AM

Send `outreach/01-email-joelle-shidemantle-eligibility.md` (single recipient — `Joelle.Shidemantle@sscserv.com`, spelling now CONFIRMED from the CSP package; cc Cherise Toler at `ctoler@tamu.edu` for the TAMU-procurement record). This single email is the gating action for the whole bid. See `proposal/00-readme.md` § 2 for the full BIG MISSING ITEMS list.

### Proposal-package contents (under `proposal/`)

`00-readme.md` · `01-executive-summary.md` · `02-technical-approach.md` · `03-project-team.md` · `04-past-performance.md` · `05-schedule-narrative.md` · `06-quality-control-plan.md` · `07-safety-plan.md` · `08-csp-proposal-form-fill-guide.md` · `09-hsp-form-fill-guide.md` · `10-price-proposal.md` · `11-submission-checklist.md` · `12-bid-bond-letter-template.md`

### Outreach-package contents (under `outreach/`)

`01-email-joelle-shidemantle-eligibility.md` (🔴 PRIMARY — send Mon 8 AM) · `02-email-joelle-shidemantle-csp-access.md` (follow-up) · `03-email-fred-patterson-drawings.md` · `04-email-patty-winkler-hub.md` · `05-email-bonding-agent.md` · `06-email-insurance-broker.md` · `07-call-script-joelle-shidemantle.md` (phone-backup) · `08-q-and-a-submission.md` (hold until G2)

### What's draftable now vs blocked

- **Draftable now** — narrative sections (Executive Summary template, Technical Approach skeleton + lab-specific considerations, Project Team template, Past Performance template, Schedule narrative with assumed substantial-completion, QC plan, Safety plan, Submission checklist); all 8 outreach emails; price-sheet skeleton (CSI-grouped). Now also draftable from the portal-pulled package: SSC Proposal Form (Section 00 42 13) CSI-division line items, SSC Technical Proposal form (Section 00 45 16) field-by-field, SSC Safety/Risk/QC form (Section 00 45 17), VetHUB-aware Subcontracting Plan (Section 00 45 17.1 → TX State Subcontracting Plan Rev. 5/26).
- **Blocked on G1 eligibility** — every estimator hour beyond what's already in the prep workspace + drawings/spec study. Until eligibility confirms, do not solicit subs.
- **Blocked on real takeoff quantities from drawings (G2 follow-on)** — quantities for partitions, finishes, sprinkler heads, lighting fixtures, receptacles, plumbing fixtures need to be hand-measured from A2.1 / A2.2 / M1.1 / E1.1+E1.2 / P1.1. PDF text extraction can't read drawing geometry; the user must measure with a takeoff tool (Bluebeam, On-Screen Takeoff, or even a manual rule-and-paper pass).
- **Blocked on H2I casework Sub-06 file** — Zscaler intercepted at download; user must retrieve manually from a non-corporate-network browser, or get re-share via outreach 01.
- **Blocked on lab-utility scope clarification (likely resolved by drawings)** — confirm wet-lab extent from P1.1 + the casework details on the H2I Sub-06 once retrieved.

---

## Headline numbers

| Item | Value | Source |
|---|---|---|
| Estimated budget range | $115K – $310K (single-room lab reno; see `price-references.md`) | Inferred — no published owner budget |
| Estimated total contract value (target) | ~$200K–$250K likely | Inferred from typical TAMU System single-room lab modernization |
| CSP RFP + HSP due | **2026-06-10, 2:00 PM CT** | Notice of Project |
| Public proposal opening | 2026-06-10, 2:30 PM CT — SSC Facilities Services Conf Rm 204 (+ Teams) | Notice of Project |
| Period of performance | TBD (project start TBD, finish TBD) | Notice of Project |
| Set-aside / HUB | HSP **required**; monthly HUB Progress Assessment Reports (PARs) tied to pay apps | Notice of Project |
| Contract type | Competitive Sealed Proposal (CSP) under TAMU System UGSC | Notice of Project + Texas Education Code Ch. 51 / Gov't Code 2269 |
| NAICS (inferred, not stated in Notice) | 236220 — Commercial & Institutional Building Construction | Inferred from work scope |

---

## What's complete in this workspace

- [x] `01-overview.md` — solicitation, location, dates, contacts, scope summary
- [x] `02-bid-prep-checklist.md` — every form / registration / insurance / bonding line we need
- [x] `03-missing-documents.md` — authoritative list of what we still need from SSC / Patterson / e-Builder
- [x] `04-scope-of-work.md` — trade-by-trade scope draft with "[TBD from drawings]" placeholders
- [x] `05-hsp-plan.md` — HUB Subcontracting Plan strategy + outreach playbook
- [x] `06-evaluation-strategy.md` — how TAMU CSPs score and what we should emphasize
- [x] `07-risk-register.md` — bid-specific risks with mitigations
- [x] `takeoff-template.json` — empty `Estimate`-shaped skeleton (per `core/schemas.py`) keyed to scope items
- [x] `price-references.md` — $/SF benchmarks for institutional classroom / lab reno
- [x] `contacts.md` — all POCs from the Notice + suggested outreach plan
- [x] `timeline.md` — backwards-planned schedule from June 10 due date

## What's blocked

- [ ] **Real takeoff quantities** — drawings are in hand, but quantities still need to be measured from the PDFs (Bluebeam / On-Screen Takeoff / manual rule-and-paper)
- [ ] **Final VetHUB / Subcontracting Plan completion** — form template is in hand (CSP Sec 00 45 17.1 → TX State Subcontracting Plan Rev. 5/26); needs to be populated against the live outreach log once subs respond
- [ ] **Insurance limit confirmation** — SSC UGSC Article 5 (in the 56-page UGSC section of the spec, Sec 00 72 00) carries the real numbers; need to read and codify in `02-bid-prep-checklist.md` § B. The Master Vendor Agreement (Sec 00 52 63) §13 sets limits for the sub-tier ($10M CGL aggregate, $2M WC, etc.) — useful as a sub-flowdown reference.
- [ ] **Performance + Payment bond commitment letters** — bonding agent needs a real total bid number, which needs takeoff. **No bid bond required by this CSP** (confirmed from Section 00 21 00 + 00 42 13).
- [x] ~~Pricing proposal form — comes with the CSP package; format varies by SSC PM~~ — pulled. CSI-division line-item table per Section 00 42 13. Contractor must list a dollar amount per CSI division actually in scope OR mark blank for divisions not in scope, OR bid will be disqualified for being incomplete.
- [ ] **Sub quotes** — can't solicit until G1 closes. Drawings + specs are ready to package and send.
- [ ] **Pre-proposal meeting record** — we **missed** the 5/14/2026 pre-proposal meeting. The Pre-Bid Attendance sheet is now in hand (scanned, image-only — counts but lacks Q&A). Still need Joelle to share any Q&A transcript or recording from the meeting.

---

## Tomorrow's actions (top 5, post-portal-pull)

1. **Email Joelle Shidemantle (SSC PM)** Monday 8 AM at `Joelle.Shidemantle@sscserv.com` (single address, spelling now CONFIRMED from the CSP package; cc `ctoler@tamu.edu` — Cherise Toler, TAMU Procurement) — confirm eligibility post-missed 5/14 meeting; request the pre-proposal Q&A / recording / addenda; request a re-share of the H2I casework Sub-06 file (network blocked our download); ask about a site walk of Lab 303 the week of 5/25.
2. **User manually retrieves the H2I casework Sub-06 file** from the public landing page in a non-corporate-network browser (5 min); saves to `inbox/opportunities/attachments/2026-05-21/tamu-csp/H2I_Casework_Sub-06_2026-05-13.pdf` (replacing the `.FAILED.html` stub). This contains the prospective casework sub's pricing — useful intel for setting our subcontract estimate.
3. **Email Brittany Crawley (TAMU HUB Operations per CSP §00 21 00 ¶3.3)** at `BrittanyFew@tamu.edu`, (979) 845-9010 — confirm whether the **VetHUB framework** (per the in-package TX State Subcontracting Plan Rev. 5/26) is the actual sub-plan we file, or whether TAMU is layering an additional HUB requirement on top; ask about VetHUB outreach events. Update `outreach/04-email-patty-winkler-hub.md` to retarget Brittany; keep Patty Winkler as a TAMU-HUB-Ops fallback second-touch.
4. **Notify bonding agent** of the upcoming submission — **no bid bond required**, only Performance + Payment bond commitment letters at award; estimated bid envelope $115K–$310K (single-room lab reno; refine after takeoff). Update `outreach/05-email-bonding-agent.md` accordingly.
5. **Start the takeoff** — open A2.1 (Floor Plans) and A2.2 (Ceiling Plan & Details) in Bluebeam (or equivalent); measure room area, partition LF, ceiling tile SF, flooring SF, base LF, paint SF. Then M1.1, E1.1, E1.2, P1.1 for counts (diffusers, fixtures, devices, sinks). Populate `takeoff-template.json`. **Hold sub solicitation until G1 closes.**

---

## Hard rules respected in this workspace

- All work product lives under `bids/tamu-harrington-2025-06813/` and `inbox/opportunities/attachments/2026-05-21/tamu-csp/` (the new download subfolder). No edits to `core/`, `app.py`, `analyze.py`, `prompts/`, `tests/`, `requirements.txt`, repo-root `README.md`, or any other code path that F1 (CWICR cost-DB) or F3 (drawing pre-pass) might rebase over.
- `analyze.py` was **not** run. The takeoff template is a hand-built skeleton intended to be filled in once the user does a real drawing-based takeoff in Bluebeam (or equivalent).
- `.env` and any API keys were **not** read, printed, or referenced. No credentials were submitted to the e-Builder portal — the public landing page is open and required no login on our end.
- Portal downloads land in `inbox/opportunities/attachments/2026-05-21/tamu-csp/` (large PDFs, not git-staged; see `source-files-manifest.md` for what's there). Pre-existing `inbox/` files were not touched.
- No fictional internal data — every place that needs the firm's own data (named insurance carrier, exact bonding capacity, specific past projects, named HUB / VetHUB subs) carries a `[USER TO FILL]` marker.

---

## File map

```
bids/tamu-harrington-2025-06813/
├─ README.md                          ← you are here
├─ 01-overview.md
├─ 02-bid-prep-checklist.md
├─ 03-missing-documents.md
├─ 04-scope-of-work.md
├─ 05-hsp-plan.md
├─ 06-evaluation-strategy.md
├─ 07-risk-register.md
├─ takeoff-template.json              ← line-item takeoff skeleton (per row of scope)
├─ price-sheet-skeleton.json          ← CSI-grouped pricing-form skeleton (per row of CSP pricing form)
├─ price-references.md
├─ contacts.md
├─ timeline.md
├─ proposal/                          ← proposal-draft package (13 markdown files)
│  ├─ 00-readme.md
│  ├─ 01-executive-summary.md
│  ├─ 02-technical-approach.md
│  ├─ 03-project-team.md
│  ├─ 04-past-performance.md
│  ├─ 05-schedule-narrative.md
│  ├─ 06-quality-control-plan.md
│  ├─ 07-safety-plan.md
│  ├─ 08-csp-proposal-form-fill-guide.md
│  ├─ 09-hsp-form-fill-guide.md
│  ├─ 10-price-proposal.md
│  ├─ 11-submission-checklist.md
│  └─ 12-bid-bond-letter-template.md
└─ outreach/                          ← ready-to-send outreach drafts (8 files)
   ├─ 01-email-joelle-shidemantle-eligibility.md   ← 🔴 PRIMARY — send Mon 8 AM
   ├─ 02-email-joelle-shidemantle-csp-access.md
   ├─ 03-email-fred-patterson-drawings.md
   ├─ 04-email-patty-winkler-hub.md
   ├─ 05-email-bonding-agent.md
   ├─ 06-email-insurance-broker.md
   ├─ 07-call-script-joelle-shidemantle.md
   └─ 08-q-and-a-submission.md
```

`local/` — if you create a sibling `bids/tamu-harrington-2025-06813/local/` folder for sub-quote PDFs, bonding-agent paperwork, scratch spreadsheets, or anything else that shouldn't be committed, it is gitignored via the workspace `.gitignore` rule `bids/*/local/`.
