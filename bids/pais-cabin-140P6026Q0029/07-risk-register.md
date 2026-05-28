# PAIS — Backcountry Cabin Roof Repairs — Risk Register

> **Use:** Internal bid-decision tool + estimating-side contingency justification. **Not** in the proposal.
> Risks scored Impact × Likelihood (1–5 each); priority = product. PAIS-specific risks (backcountry, coastal, wildlife) noted alongside generic federal-SBA-RFQ risks.

## 1. Bid-side risks (decision-to-bid through 6/18/2026 submission)

| # | Risk | Impact | Likelihood | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| B1 | SAM.gov registration lapses or Reps & Certs > 12 months | 5 | `[USER TO FILL — confirmed active 2026-05-23 per firm-profile.json but expiration date unknown]` | TBD | Verify before pricing begins; refresh if needed (3–10 working days) | PM |
| B2 | Bond commitment letter not on file at submission | 2 | `[USER TO FILL]` | TBD | **Post-award only** per 52.228-13 — bond commitment letter is **not required** at submission for this RFQ. Optional pre-submission letter strengthens past-performance volume. | PM |
| B3 | Insurance COIs stale or below DOI 1452.228-70 limits ($100K/$500K/$500K) | 3 | 4 | 12 | Pull current COIs from agent on Day 1; verify renewed policy meets DOI minimums (BPC's expired $1M/$2M would over-meet) | PM |
| B4 | Wage Determination amended mid-bid by SF-30 | 3 | 2 | 6 | Subscribe to SAM amendment notifications; re-price labor if WD changes | Estimator |
| B5 | **Site-visit no-show due to 4WD logistics** (Frisco → CCI is 440 mi / 7 hr each way; 4WD required at site) | 5 | 3 | 15 | Confirm 4WD vehicle ≥ 7 days out; book overnight in Corpus Christi; if can't attend, bump contingency to 8–10% (above the typical 7–8% missed-site-visit floor) | PIC |
| B6 | RFI not answered by 6/7 cutoff | 3 | 3 | 9 | File 11 candidate RFIs (per `03-missing-documents.md`) by 6/5 — 2 days before cutoff; do not file Day-of-cutoff | PM |
| B7 | Past-perf reference contact unreachable | 4 | 4 | 16 | **All 3 picks have `[USER TO FILL]` for reference contacts in firm-profile.json** — pre-confirm Lavon (614 Forest Hill Dr Murphy POC), Hindu Temple of Southlake (NTHHS POC), Holiday Inn Hall Park (property POC) by working phone + email on Days 1–10 | PM |
| B8 | **Boilerplate-leakage in RFP** (POP date 2025; site address contradiction §G vs CLIN 003) | 4 | 5 | 20 | Already flagged as RFI #1 + #2; if unanswered, document operative interpretation in cover letter without taking exception | Estimator |
| B9 | TDI shutter sub does not commit by pricing-assembly deadline | 4 | 3 | 12 | Solicit ≥ 3 TDI-listed manufacturers; identify back-up before pricing locks; lead-time risk (4–6 wk fabrication) means sub commitment is a schedule item too | PM |
| B10 | Bid exceeds typical SAP cap ($250K per FAR 13.003) | 3 | 2 | 6 | Bid the true cost + reasonable markup; if total approaches $250K SAP cap, RFI to confirm acquisition method (could trigger conversion to full Part 15 RFP — would push competitors to a different pool) | PIC |
| B11 | Bid below realistic floor — "unreasonably low" determination | 5 | 1 | 5 | Verify bid covers per-diem + 4WD truck rental + lodging in CCI for the active construction days within 60-cal-day POP; do not chase volume by under-bidding the logistics premium | PIC |
| B12 | **PAIS-specific:** Subject-line mismatch (RFP retitled by Amd 0001 but Section L subject line is from the original RFP) | 2 | 3 | 6 | Use Section L exact subject line; document interpretation in transmittal email; RFI #10 if unresolved | PM |
| B13 | **PAIS-specific:** Wage Determination Att 3 PDF text-extraction failure | 4 | 5 | 20 | User reads Att 3 PDF directly in Acrobat or printed; transcribe Kenedy County / TX-DOT 4 region trade rates (prevailing wages effective Jan/2026) before pricing assembly | Estimator |
| B14 | **SAP archetype risk:** Under-investing in the Technical Capability narrative (treating it as the LPTA "no narrative" pattern would treat it). PAIS is best-value SAP — Section M scores narrative comparatively, not pass/fail. A one-page narrative loses to a competent 5–8 page narrative at the same price point. Per [federal-simplified-acquisition-best-value playbook](../../firm/playbooks/federal-simplified-acquisition-best-value.md) §7 (Pitfall #2), this is **the dominant SAP loser pattern**. | 5 | 3 | 15 | Allocate ≥ 8 estimator-hours to drafting the Technical Capability narrative in `09-proposal-draft.md` §7; cover all 5 sub-sections (Understanding, Site Logistics + Self-Performance, CLIN-by-CLIN Approach, Schedule, Compliance + Quality); paste-adapt boilerplate from `firm/proposal-library/boilerplate/` where applicable. Pre-submission, a non-author BPC reviewer reads narrative end-to-end and signs off that it demonstrates "thorough understanding" per Section L Part C. | PIC |
| B15 | **SAP archetype risk:** Missing or under-counting the 3–5 prior-experience references (Section L states "minimum of 3 and/or maximum of 5"). Submitting only 2 fails the count check on its face and per playbook §7 (Pitfall #6) is a hard eliminator from the lowest-3 evaluation pool — the CO has no comparative basis to evaluate prior experience. Currently all 3 picks (Lavon, Hindu Temple, Holiday Inn) have `[USER TO FILL]` reference contacts in `firm/firm-profile.json`. | 5 | 4 | 20 | Pre-confirm reference contacts (working email + phone) for all 3 firm-profile picks by Day 10; submit the **maximum 5** the RFQ allows (add 2 more from `firm/firm-profile.json → past_projects` — recommend any project with coastal/marine, federal-land, or roof-repair relevance). Cross-reference duplicates B7. | PM |
| B16 | **SAP archetype risk:** Wrong SF form on the quote (e.g. submitting SF-1442 because the LPTA template assumed it). Per playbook §7 (Pitfall #4) this is a common eliminator. **Mitigated** for PAIS — the workspace is now retrofitted to the SAP-best-value template which defaults to SF-18, and `05-bid-form-prep.md` explicitly verifies SF-18 against RFQ pp 1–2. Residual risk: a future SF-30 amendment switching the form to SF-1449 (CO discretion under FAR 13.500) — re-verify the form on every amendment. | 4 | 1 | 4 | Verify SF-18 on RFQ cover before submission; re-verify on every SF-30 amendment; if amendment switches to SF-1449, update `05-bid-form-prep.md` block-by-block fill from SF-18 to SF-1449 per playbook §4. | PM |

## 2. Execution-side risks (post-award; for pricing-strategy contingency justification)

| # | Risk | Impact | Likelihood | Score | Mitigation | Owner |
|---|---|---|---|---|---|---|
| E1 | Hidden conditions on demo — rotted sheathing under shingles (CLIN 002) or rot behind door frames (CLIN 001) | 4 | 4 | 16 | Pre-demo investigation at site visit; pre-demo RFI; contingency reserve in CLIN 001 + 002 self-perform labor for ~10% additional time | Super |
| E2 | **Long-lead CLIN 003 shutters** (TDI CAT5 fabrication 4–6 wk + 10 units custom) | 4 | 5 | 20 | Order at NTP+1 with 50% deposit; identify alternate TDI-listed manufacturer; build a delivery-window buffer into the schedule; if fabrication slips past NTP+50, accept LD risk (or request equitable schedule extension under 52.243-5 Changes) | PM |
| E3 | Davis-Bacon certified-payroll administrative cost on a 3-CLIN small project | 2 | 4 | 8 | Build PM hours into GC; payroll-clerk dedicated for project (one cycle/week, prime + sub) | PM |
| E4 | Buy American non-compliance (CLIN 003 shutter AL or SS fasteners from foreign mill) | 4 | 3 | 12 | Domestic-content rep on every PO; verify mill origin before delivery; if foreign material discovered post-PO, request 52.225-9 exception immediately (post-award exception requires CO determination) | PM |
| E5 | **Site-access lag** — Park Road 22 sand/tide closure or wildlife buffer activation | 4 | 3 | 12 | Pre-trip Greg Smith on tide/wildlife windows; alternate work-day plan if road closes; build 5–10 day weather/access buffer in 60-day POP | Super |
| E6 | NPS resource-protection rule violation (off-road vehicle, beach driving, resource removal) | 5 | 1 | 5 | Crew briefing at mobilization; sign-in/sign-out at HQ; no off-route vehicle travel; no beach driving outside designated routes | Super |
| E7 | Final inspection scheduling lag — Park rep availability in 60-day window | 3 | 3 | 9 | Pre-schedule final inspection at NTP+50 (10 days before SC target); back-up dates in CPM; concurrent interim inspections per 52.246-12 + RFQ §G to avoid surprises | Super |
| E8 | Adverse weather — coastal storms / hurricanes during 60-day POP | 4 | 3 | 12 | Buffer days in CPM; covered staging at HQ; weather-day clause per 52.249-10 default; **avoid hurricane season** — if 60-day window falls Aug–Oct, raise bidder option to start outside the season (cannot decline NTP, but can flag schedule) | Super |
| E9 | Sub default mid-project (CLIN 003 shutter manufacturer) | 5 | 1 | 5 | Pre-vetted back-up TDI-listed manufacturer; sub agreement w/ replacement clause; first-article delivery acceptance gate at fabricator | PM |
| E10 | Owner-directed change to scope (e.g. discover additional roof leak areas, expand sand-control to 4 sides) | 3 | 4 | 12 | Unit prices in proposal cover for ramp lumber + roof shingle SF + shutter unit; CO process documented; recover via change-order pricing per 52.243-5 | PM |
| E11 | **PAIS-specific:** Sea-turtle nesting buffer activation (Apr–Aug Kemp's ridley on PAIS) restricts vehicle/work hours | 3 | 3 | 9 | RFI #4 to clarify; if 60-day window crosses nesting season, plan night/dawn shifts or vehicle-route restrictions; flag schedule slip risk to PIC | Super |
| E12 | Closeout deliverable gap delays final pay (operation manual, as-builts, engineer-stamped shutter drawings) | 3 | 4 | 12 | Closeout package compiled from NTP forward, not at SC; engineer-stamped drawings ordered with shutter PO; as-built drawings updated weekly | PM |
| E13 | **PAIS-specific:** Cabin is on National Register / LCS — Preservation Brief 4 governs roof material / method (not just "marine-grade like-kind") | 3 | 2 | 6 | RFI #5; if confirmed historic, materials cost premium ~15–25% and approval cycle adds 2 weeks — flag PIC | PM |

## 3. Risk-driven pricing decisions

The contingency in `08-pricing-strategy.md` is justified by:

- Sum of E-risks scored ≥ 12: E1, E2, E4, E5, E8, E10, E12 = 7 high-priority risks → **5–7% contingency** justified (above the typical 3–5% LPTA floor)
- Concentration of risk in **CLIN 003 long-lead shutter (E2 score 20)**: → adds 1–2% to procurement-line GC for expedite-freight + dual-source contingency
- Concentration of risk in **logistics (B5 score 15, E5 score 12)**: → adds 2–3% to GC supervision + per-diem + 4WD vehicle line
- Concentration of risk in **wildlife / weather buffer (E8, E11)**: → adds 1% to schedule-buffer GC
- **SAP archetype risks (B14 + B15) do not flow into contingency dollars** — they are bid-quality / proposal-completeness risks. They are mitigated by allocating estimator-hours (not dollars) to narrative drafting and reference-contact pre-confirmation. Per the playbook §10, the SAP markup range (5–7% profit, 6–8% contingency, 8–11% OH) already prices in the estimator-hours premium vs. LPTA.

Recommended contingency band: **6–8%** (per [federal-simplified-acquisition-best-value playbook](../../firm/playbooks/federal-simplified-acquisition-best-value.md) §10 — between LPTA's 3–5% floor and FAR 15's 5–8% range; the SAP-specific tightening vs. FAR 15 reflects shorter schedule, the loosening vs. LPTA reflects narrative-buffer room).

## 4. Go / No-go drivers

The following risk thresholds drive a **No-Go**:

- **B1 active 🔴:** SAM lapsed = No-Go (cannot bid federal). Per `firm-profile.json`, user-confirmed active 2026-05-23 — verify expiration before 6/18 cutoff.
- **B7 unresolvable:** < 2 confirmed past-perf references with working POCs = high risk; reconsider bid.
- **B8 unresolvable:** boilerplate ambiguities so severe that BPC cannot price without exceptions = No-Go (best-value SAP rejects exceptions per Section L General Information).
- **B11 risk:** even at floor, true cost > $250K SAT cap and Govt's stated funding band is sub-SAT = No-Go.
- **B13 unresolvable:** if user cannot read Att 3 WD PDF, BPC cannot price DBA labor accurately = No-Go (or absorb as risk in self-perform contingency).

Recommended posture: **Conditional Go pending:**
1. Site visit attendance 6/4
2. WD trade-rate transcription (B13)
3. Renewed COI on hand (B3)
4. SAM expiration date verified (B1)
5. ≥ 1 past-perf reference contact pre-confirmed (B7 / B15)
6. ≥ 2 TDI shutter sub quotes returned (B9, E2)
7. Technical Capability narrative drafted to ≥ 5 pp by 6/14 (B14 — narrative-quality gate)

If 6 of the above 7 close by 6/14, recommend **Go**. If fewer, recommend **No-Go** and re-deploy estimating effort to other workspaces. The narrative-quality gate (item 7) is a SAP-archetype-specific addition — without it, the bid lands in the lowest-3 pool on price but loses on technical-capability comparison.
