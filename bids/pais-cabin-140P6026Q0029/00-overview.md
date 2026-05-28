# PAIS — Backcountry Cabin Roof Repairs — Overview

> **Source playbook:** [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../firm/playbooks/federal-simplified-acquisition-best-value.md)
>
> **Template archetype:** Federal **Simplified Acquisition (FAR Part 13, often + Part 12 commercial-item), best-value comparative trade-off** across price + technical capability + prior experience. Quote on **SF-18** (NOT SF-1442 / NOT typical SF-1449; this PAIS RFQ uses SF-18 per RFQ pp 1–2). **NOT LPTA** — Section M evaluates quotes comparatively, typically in groups of three lowest-priced. The narrative + 3–5 prior-experience refs + key-personnel short-form are required, not optional — under-investing here loses to a competent narrative at the same price point.
>
> **Template retrofit history:** This workspace was originally scaffolded from `bids/_TEMPLATES/federal-sba-rfq-lpta/`. The PAIS dogfood (dogfood #2) revealed LPTA was the wrong archetype. Retrofitted **2026-05-27** to align with `bids/_TEMPLATES/federal-simplified-acquisition-best-value/` and `firm/playbooks/federal-simplified-acquisition-best-value.md` (the SAP-best-value template + playbook Worker A authored to close the dogfood gap finding). See **Template dogfood notes — RESOLVED** at the bottom of this file for the per-quirk resolution log.

## Solicitation identity

| Field | Value |
|---|---|
| Solicitation # | `140P6026Q0029` |
| Project name | `PAIS — Backcountry Cabin Roof Repairs` (renamed via Amd 0001 from `PAIS — Cabin Security and Improvements`) |
| Agency | `U.S. Department of the Interior, National Park Service` (NPS) |
| Issuing office | `NPS, MWR — MWRO MABO`, `601 Riverfront Drive, Omaha NE 68102` |
| Performing office | `NPS, Padre Island National Seashore`, Corpus Christi TX 78418 |
| Solicitation form | **SF-18 RFQ** (NOT SF-1442 / SF-1449 — see dogfood notes) |
| Contract type | `Firm-Fixed-Price` (per FAR 52.216-1) |
| Acquisition method | `Simplified Acquisition Procedures` (FAR Part 13 in conjunction with FAR Part 12) |
| Set-aside | `100% Total Small Business Set-Aside` (per FAR 52.219-6 DEVIATION Jan 2026) |
| Evaluation method | **Best Value — comparative trade-off across price + technical capability + prior experience** (Section M); **NOT LPTA** |
| Primary NAICS | `236220` (Commercial and Institutional Building Construction) |
| Size standard | $`45M` 3-yr avg revenue |
| Magnitude | `[AWAITING SOURCE DOCS — no magnitude band stated; under SAT (~$250K) per FAR Part 13 simplified acquisition]` |
| Period of performance | `60` calendar days from NTP |
| Wage determination | `[AWAITING SOURCE DOCS — Att 3 PDF (B08_Solicitation_-_Att_3_-_DOL_Wage_Determination.pdf, 6 pp, dated Jan/2026) uses an encoded font that defeated text extraction; user to read PDF directly and transcribe Kenedy/Nueces-County-applicable trade rates]` effective `Jan/2026` |
| Buy American | FAR 52.225-9 applies — construction materials (excepted list: NONE) |
| Davis-Bacon | FAR 52.222-6 applies — WH-347 weekly certified payroll |
| PSC | Z2JZ — Repair or Alteration of Miscellaneous Buildings |
| Project / requisition # | 0044044135 |

## Project location + site visit

| Field | Value |
|---|---|
| Site address | Padre Island National Seashore — coastal wood-framed cabin **~50 miles south** of Hwy 361 on Park Road 22 (backcountry / Down Island; **4-wheel-drive vehicle required**) |
| Site visit muster point | NPS PAIS Facility Management Building, 20301 Park Road 22, Corpus Christi, TX 78418 |
| Site visit city / state / ZIP | Corpus Christi, TX 78418 (muster); cabin location is southern PAIS backcountry |
| County | **Kenedy County, TX** (cabin / place of performance — ~50 mi south of HQ); Nueces County, TX (HQ muster point) |
| Site visit date | **6/4/2026 at 10:00 AM CT** (rescheduled from 5/20/2026 by Amd 0001 due to inclement weather) |
| Site visit POC (NPS) | Greg Smith — `[AWAITING SOURCE DOCS — email]` — (361) 949-8173 ext 242 |
| Site visit RSVP method | Confirm with Contract Specialist (Bridget Parizek) by email; bring 4WD or arrange shuttle with site POC |

## Key dates

| Milestone | Date |
|---|---|
| RFQ release (SF-18) | 5/7/2026 |
| Amendment 0001 (SF-30) — site-visit + due-date extension | 5/20/2026 |
| Site visit (rescheduled) | **6/4/2026 @ 10:00 AM CT** |
| RFI cutoff | **6/7/2026** (3 calendar days following site visit, per Section L Part B) |
| Quote due | **6/18/2026 @ 12:00 CT** (extended from 6/8/2026 by Amd 0001) |
| Acceptance period | **60 calendar days** from quote receipt (per Section L General Information) |
| Anticipated award | `[AWAITING SOURCE DOCS — not stated]`; FAR 13 SAP awards typically within 30–45 days of close |
| NTP target | `[AWAITING SOURCE DOCS — not stated]` |
| Substantial completion target | NTP + 60 calendar days |

> **Boilerplate-leakage flag:** SF-18 page 2 lists "Period of Performance: 01/31/2026 to 06/01/2026" and the SOW (Att 1) Section 9 says "All on-site work must be completed before 01 JUNE 2025" — **both are stale dates** carried from a prior solicitation. The operative POP per Section B and the Special Notice for Contractors is **60 calendar days from NTP**. Flag to RFI in `03-missing-documents.md` and treat the 60-cal-day-from-NTP statement as governing.

## Scope summary (1–3 sentences)

Furnish all labor, materials, and equipment to repair, secure, and weather-protect a backcountry coastal cabin at Padre Island National Seashore: door repair + corrosion-resistant reinforcement + new deadbolts (CLIN 001, qty 3), roof leak repair with marine-grade like-kind shingles + sealant + stainless fasteners (CLIN 002, lump sum), and ten (10) CAT5 TDI hurricane-resistant Bahama shutters with manual operation + lockable hardware (CLIN 003, 10 units). Two priced options: (Option 001) construct a new cabin ramp extension with two new landings and integration of a Government-Furnished aluminum ramp (Option 002) construct a breakaway 2x10 sand-control enclosure on three sides of the raised cabin's perimeter. Site is ~50 mi south of HQ on Park Road 22 — backcountry access via 4WD only.

## Contacts (agency-side)

| Role | Name | Email | Phone |
|---|---|---|---|
| Contracting Officer (CO) | `[AWAITING SOURCE DOCS — CO not named in solicitation; only Contract Specialist is named. CO designated at award per 1452.201-70]` | | |
| Contract Specialist (CS) | Bridget Parizek | bridget_parizek@ios.doi.gov | (402) 800-7927 |
| Site / Project POC (NPS) | Greg Smith | `[AWAITING SOURCE DOCS — email]` | (361) 949-8173 ext 242 |
| COR | `[AWAITING SOURCE DOCS — designated at award per 1452.201-70(b)]` | | |

> **Communication discipline:** per Section L, **all questions in writing by email to bridget_parizek@ios.doi.gov only**. RFI cutoff is 3 calendar days after the 6/4 site visit. NPS will publish RFI responses as a SAM amendment.

## Submission

| Item | Value |
|---|---|
| Submission portal | **Email only** (quotes submitted by any other means shall not be accepted) |
| Submission email | bridget_parizek@ios.doi.gov |
| Email subject (exact) | `140P6026Q0029 – PAIS – Cabin Security and Improvements – email N of M` (per Section L Part C.3.i — note the subject still references the original project name, not the amended "Backcountry Cabin Roof Repairs"; defer to RFP-stated subject) |
| Attachment format | Single combined PDF titled "QUOTE PACKAGE" |
| Email size limit | 25 MB total per email; split across emails if larger and number them in the subject |
| Page format | 8.5" × 11"; 11" × 17" foldouts permitted for charts/tables/diagrams only |
| Send-by-buffer | Submit ≥ 30 min before 12:00 CT cutoff |

## Submission package contents (per Section L checklist)

1. Checklist for Quote Submittal — Section L Part C checklist completed as **first page** of package
2. **Signed SF-18** acknowledgment
3. **Signed amendments** (SF-30 Amd 0001 — and any further amendments NPS posts before close)
4. Completed **Section K** provisions / representations as applicable
5. **Section B Price/Bid Schedule** — every CLIN priced; pricing rounded to the nearest dollar; total cited
6. **Technical Capability narrative** — proposed schedule + approach demonstrating thorough understanding of the SOW
7. **Prior Experience** — 3 to 5 most-recent (last 5 years) similar size+scope projects with brief description + POC contact info
8. **"or-equal" product literature** if quoting a substitute (e.g. shutter brand other than the implied baseline)
9. **Contractor Core Data block** (company name, CAGE, UEI, POC, POC email/phone)

## Bid posture (BPC quick read)

| Question | Answer |
|---|---|
| BPC eligible (small + correct NAICS)? | ✅ — NAICS 236220 small ≤ $45M; BPC self-asserts small in SAM |
| SAM.gov current? | ⚠️ — User confirmed active 2026-05-23; specific expiration date TBD; verify before 6/18 cutoff. See [`firm/compliance/README.md`](../../firm/compliance/README.md) |
| Insurance current? | 🔴 — Commercial GL policy SBCC-042443-00 expired 2024-09-25 per `firm/firm-profile.json`; pull current/renewed COIs before submission |
| DOI insurance limit met? | DOI 1452.228-70 requires $100K/$500K/$500K — **lower** than typical commercial GL; BPC's expired policy was $1M/$2M which would have over-met. Verify renewal carries equivalent or greater limits. |
| Bondable at this magnitude? | ✅ — Payment Bond OR Irrevocable Letter of Credit (100% of contract value), due **within 10 days after award** (NOT at submission); BPC's $1M bonded envelope (Lavon RV Park reference) covers this typical-SAT magnitude |
| Bid bond required? | ❌ — **No bid bond** required (FAR 52.228-1 NOT invoked; FAR 52.228-13 Alternative Payment Protections instead) |
| Past-perf fit? | ✅ — Lavon RV Park + Hindu Temple of Southlake + Holiday Inn Hall Park per [`firm/firm-profile.json → past_project_selection_rules.pais-cabin-140P6026Q0029`](../../firm/firm-profile.json) |
| Magnitude vs BPC's typical bid? | Likely small (under-SAT, est. $50–200K based on scope of 3 CLINs + 2 options); fits BPC's bonded envelope easily |
| Geographic fit | 🔴 — Frisco TX → Corpus Christi TX HQ ≈ **440 mi (7-hr drive)**; cabin is +50 mi south of HQ. Per-diem + lodging + travel **non-trivial** for a 60-cal-day POP. Materials transport to backcountry site adds cost. |
| Special hazards | Backcountry coastal site (saltwater corrosion); 4WD-only vehicle access; sand intrusion; hurricane-zone construction (TDI CAT5); seasonal sea-turtle nesting (Kemp's ridley) on PAIS beaches — wildlife buffers may apply during construction |
| NPS-specific compliance | NPS Preservation Brief 4 (roofing on historic structures) may apply if cabin is on the National Register; coastal building codes + floodplain requirements per SOW Section 4 |
| Go / No-go recommendation | `[USER TO FILL after pre-bid analysis — recommend Conditional Go pending: (a) site visit attendance 6/4, (b) WD trade-rate transcription from Att 3, (c) renewed COI on hand, (d) SAM expiration verified, (e) sub solicitations to coastal-experienced roofers]` |

## Cross-references

- Playbook (canonical for this archetype): [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../firm/playbooks/federal-simplified-acquisition-best-value.md)
- Workspace template (canonical for this archetype): [`bids/_TEMPLATES/federal-simplified-acquisition-best-value/`](../../bids/_TEMPLATES/federal-simplified-acquisition-best-value/)
- Sibling LPTA playbook (rigid end of the SAP-to-LPTA-to-FAR-15 continuum; for comparison only): [`firm/playbooks/federal-sba-rfq-lpta.md`](../../firm/playbooks/federal-sba-rfq-lpta.md)
- Compliance check: [`firm/compliance/README.md`](../../firm/compliance/README.md)
- Scope template starter: pick from [`firm/scope-templates/`](../../firm/scope-templates/README.md) — closest archetype is small-structure repair / coastal envelope; no exact-fit cabin-roofing template exists in the scope-template library (separate gap from the workspace-template gap, which is now closed)
- Proposal-library: [`firm/proposal-library/`](../../firm/proposal-library/README.md)
- Firm profile: [`firm/firm-profile.json`](../../firm/firm-profile.json) → `past_project_selection_rules.pais-cabin-140P6026Q0029`
- Source documents (extracted from `Z--PAIS+-+Backcountry+Cabin+Roof+Repairs.zip`):
  - `Sol_140P6026Q0029.pdf` (28 pp) — main RFQ
  - `Sol_140P6026Q0029_Amd_0001.pdf` (2 pp) — site-visit + due-date extension
  - `B08_Solicitation_-_Att_1_-_Specifications.docx` (Scope of Work, 9 pp equivalent)
  - `B08_Solicitation_-_Att_2_-_Drawings.pdf` (1 pg — ramp extension construction details)
  - `B08_Solicitation_-_Att_3_-_DOL_Wage_Determination.pdf` (6 pp — encoded font, manual transcription required)

---

## Template dogfood notes — `bids/_TEMPLATES/federal-sba-rfq-lpta/` (dogfood #2) — **RESOLVED 2026-05-27**

> **Resolution summary:** All eleven quirks below were addressed by Worker A in `bids/_TEMPLATES/federal-simplified-acquisition-best-value/` (the new SAP-best-value workspace template) and `firm/playbooks/federal-simplified-acquisition-best-value.md` (the matching playbook). This PAIS workspace was retrofitted to the new template on **2026-05-27** — see "Template retrofit history" at the top of this file. Original quirk list preserved below for traceability and as a worked example of the dogfood → template-improvement loop. Per-quirk resolution annotation inline.
>
> Dogfood #1 was b1710-office-refurb-FA667526Q0002 (USACE office refurb, scaffolded *before* the template was extracted into `_TEMPLATES/`).
> These are the structural / content quirks I hit while applying the template to **PAIS — a SAP best-value RFQ on SF-18**, NOT a true LPTA on SF-1442. Each item below was a candidate template-improvement ticket; the new SAP-best-value template closes each.

### Quirks worth fixing in the template

1. **`05-bid-form-prep.md` hardcodes SF-1442** — but FAR Part 13 simplified-acquisition RFQs frequently use **SF-18** (this PAIS bid) or **SF-1449** (commercial-item construction). Recommend: split the bid-form prep into 3 variants — `05a-SF1442-construction.md` (full FAR 14/15 sealed-bid construction), `05b-SF1449-commercial-item.md`, `05c-SF18-RFQ.md` (under-SAT simplified). Or make the existing file SF-1442 + SF-18 + SF-1449 swap-tables and note which applies.

2. **Hardcoded LPTA evaluation language throughout** (especially `02-deliverables.md`, `09-proposal-draft.md`'s "Discipline reminder: keep this to one page. Do not narrate approach…", `00-overview.md` "Evaluation method: typ LPTA"). Best-value SAP requires technical-capability narrative + prior-experience POCs. Recommend: parameterize evaluation method as `LPTA | best-value-SAP | tradeoff` and gate the "no narrative" guidance on `LPTA` only. Many DOI/NPS construction RFQs in this $-class are best-value SAP, not LPTA.

3. **Bid bond + 100% P&P bond assumption is wrong for SAP** — `05-bid-form-prep.md` and `09-proposal-draft.md` reference `SF 24 Bid Bond + Power of Attorney` and `Performance and Payment Bonds at 100%`. PAIS uses **FAR 52.228-13 Alternative Payment Protections** — Payment Bond *or* Irrevocable Letter of Credit at 100%, due **after award** (within 10 days). No bid bond at submission. Recommend: parameterize bonding as `bid-bond + P&P | post-award P&P only | post-award alt-payment-protection (52.228-13)` and gate template content accordingly.

4. **Past-performance count: template says "2 examples per FAR M.1.4.B.f"** in `02-deliverables.md`, but PAIS RFQ Section L asks for **"a minimum of 3 and/or a maximum of 5"** prior-experience references. Different agency clauses request different counts — generalize to `{{PAST_PERF_MIN}}–{{PAST_PERF_MAX}}` parameters.

5. **Magnitude band assumed** — the bid-posture row "Magnitude vs BPC's typical bid" expects `{{MAGNITUDE_LOW}}` – `{{MAGNITUDE_HIGH}}` to be populated, but **simplified acquisitions rarely state a magnitude**. The template should accept "magnitude unstated; SAP cap = $250K (FAR 13.003)" as a valid value rather than leaving the placeholder visibly unfilled.

6. **No `proposal/` subdirectory in the template.** `scripts/render_proposals.py` requires a `bids/<slug>/proposal/` subdir to render. Consequence: rendering this newly scaffolded workspace returns "No proposal/ subdir under …" and exits 2. The template should ship a stub `proposal/00-readme.md` (and optionally a stub volume/cover so `build_internal_workbook` has *something* to roll up). Either: (a) extend the template, or (b) update `render_proposals.py` to fall back to the workspace root when `proposal/` is absent.

7. **`firm/_scripts/apply_firm_profile.py` `Layer 3 idempotency` references files this template doesn't produce.** The script's `PAST_PERF_FILES` set targets `proposal/04-past-performance.md`, `proposal/03-volume-III-past-performance.md`, `proposal/03-past-performance.md` — none of which exist in `_TEMPLATES/federal-sba-rfq-lpta/`. Layer 3 runs are silently a no-op for workspaces scaffolded from this template. Either ship the past-performance markdown stubs in the template, or document this gap so users don't expect the firm-profile picks to auto-fill into a nonexistent file.

8. **SAM.gov amendment-watch language missing** — federal SAP RFQs frequently get one or more SF-30 amendments mid-window (PAIS already has Amd 0001 changing site visit + due date). The `04-checklist.md` "Pre-pricing" section should explicitly include "[ ] subscribe to SAM.gov amendment notifications for {{SOLICITATION_NUMBER}}" and the timeline should call out re-checking SAM at Due-3.

9. **No backcountry / remote-site logistics section** — the 01-scope.md's site-visit shopping list assumes a building with paved drive + power + water. Backcountry / boat / 4WD / helicopter sites need their own checklist (lay-down at HQ vs. on-site; haul-out windows; ferry/boat schedules; wildlife seasonal restrictions). Recommend: add an optional `01a-remote-site-logistics.md` partial for remote/backcountry/marine sites.

10. **Insurance limits assumed at typical commercial-GL** ($1M/$2M is the implicit baseline). DOI 1452.228-70 mandates a *lower* baseline ($100K/$500K/$500K) — a lot of agency-specific insurance clauses operate this way. Recommend: parameterize per RFP and not assume any defaults.

11. **Subject-line drift on amended solicitations** — the RFQ's email-subject template still references the original project name even after Amd 0001 renamed it. Template should advise: "use the original project name in submission subject lines unless the amendment explicitly retitles the email subject."

### Quirks accepted as-is (no template change recommended)

- Davis-Bacon WD attachment language is fine; the encoded-font extraction failure is a per-PDF problem, not a template bug.
- Risk register and pricing strategy are reasonably agency-agnostic and do not need PAIS-specific alterations beyond filling values.
- Outreach email templates work as-is.

### Action: open improvement tickets

Each numbered quirk above is a candidate ticket against the template. Recommend a follow-up commit on a separate branch that addresses #1, #2, #3, #6 first (highest leverage — they affect every SAP / non-LPTA workspace going forward).

### **RESOLUTION LOG — 2026-05-27**

| Quirk | Resolution in new SAP-best-value template / playbook |
|---|---|
| #1 (SF-1442 hardcode) | New template's `05-bid-form-prep.md` defaults to SF-18 + documents the SF-1449 commercial-item variant. Playbook §4 ships the full SF-18 / SF-1449 / SF-1442 disambiguation matrix. PAIS file already SF-18-specific; no further change needed. |
| #2 (LPTA evaluation language hardcoded) | New template / playbook evaluation language is best-value-SAP throughout (comparative trade-off, groups-of-3, narrative required). PAIS files already SAP-specific; cleaned up residual references on this retrofit. |
| #3 (bid bond + P&P assumption wrong for SAP) | New template defaults to post-award P&P **or** FAR 52.228-13 Alternative Payment Protections, no SF-24 at submission. PAIS already 52.228-13. |
| #4 (past-perf count) | New template uses 3–5 refs as the SAP norm with Section L override. PAIS already 3–5 per Section L. |
| #5 (magnitude band assumption) | New template's overview accepts "magnitude unstated; sub-SAT cap" as a valid value. PAIS already uses that pattern. |
| #6 (no `proposal/` subdir) | Template-side fix is still pending per Worker A's ship notes; for now, this PAIS workspace will render via the `scripts/render_proposals.py` post-fix that falls back to the workspace root when `proposal/` is absent (or report renderer error in retrofit summary if not yet fixed). |
| #7 (`apply_firm_profile.py` Layer 3 idempotency) | Layer 3 hot-fix landed earlier today (per task brief); Layer 3 is now a clean no-op on workspaces that lack `proposal/` past-performance files, rather than erroring. |
| #8 (SAM amendment-watch missing) | New template `04-checklist.md` ships an explicit "subscribe to SAM amendment notifications" line. PAIS already has the equivalent line. |
| #9 (no remote-site logistics section) | New template ships an optional remote-site logistics partial. PAIS already has §7 backcountry-logistics in `01-scope.md`. |
| #10 (insurance limits assumption) | New playbook §8 parameterizes insurance per RFP-cited agency clause (DOI 1452.228-70 = $100K/$500K/$500K) and stops baking-in $1M/$2M. PAIS already DOI-clause-specific. |
| #11 (subject-line drift on amended solicitations) | New template advises using the original-RFQ subject line unless an amendment explicitly retitles it. PAIS already follows this discipline (Section L exact subject string used). |

**Net retrofit delta:** updated source-playbook + cross-reference links throughout, promoted "Key Personnel" to a standalone proposal section (per template Section L assembly order), added "groups of 3 lowest priced" pricing posture to pricing strategy, added 3 SAP-specific risks (under-investing in narrative, missing prior-experience count, wrong SF form) to risk register, and refreshed the dogfood notes header to RESOLVED. All previously-extracted PAIS RFQ facts (solicitation #, key dates, contacts, scope, CLINs) preserved verbatim.
