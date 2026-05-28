# Playbook — Federal Simplified Acquisition, Best-Value Comparative Trade-Off (FAR Part 13 + 12)

> **Exemplar bid:** [`bids/pais-cabin-140P6026Q0029/`](../../bids/pais-cabin-140P6026Q0029/) — NPS, Padre Island National Seashore, Backcountry Cabin Roof Repairs (SF-18, 100% Small Business Set-Aside, simplified acquisition under SAT, best-value comparative trade-off across price + technical capability + prior experience, 60-day period of performance).
>
> **Matching workspace template:** [`bids/_TEMPLATES/federal-simplified-acquisition-best-value/`](../../bids/_TEMPLATES/federal-simplified-acquisition-best-value/)

## 1. Procurement description

Federal civilian and DoD agencies use **simplified acquisition procedures under FAR Part 13**, often layered with **commercial-item procedures under FAR Part 12**, for small construction and repair work below the simplified acquisition threshold (SAT). The dominant award flavor for renovation / repair work that is too narrative-thin for full FAR Part 15 source selection but too narrative-rich for pure LPTA is the **comparative trade-off** variant authorized by **FAR 13.106-2(b)(3)** — the contracting officer may use "any evaluation procedure that is consistent with customary commercial practice." This gives the CO discretion to weigh **price, technical capability, and prior experience** against each other without standing up a formal source-selection apparatus.

The signature characteristic is **lightweight evaluation machinery + meaningful narrative**:

- No formal Source Selection Plan (SSP), no Source Selection Authority (SSA), no Source Selection Decision Document (SSDD) of the kind FAR 15.308 requires
- No formal evaluation board — the CO and Contract Specialist evaluate directly, often with input from the technical / program office (the COR-to-be)
- A common shortcut: the CO ranks all quotes by price, then **evaluates technical capability + prior experience only on the lowest 3 (or sometimes the lowest 5)** to award the best value among that subset
- Quote (not proposal) language: offerors submit "quotes" against an RFQ, not "offers" against an RFP
- Submission is brief: 5–15 page technical narrative + price schedule + 3–5 prior-experience references + key-personnel snapshots — **not** the 4-volume FAR Part 15 structure

When you'll see it:

- DOI / NPS / USFWS / USDA Forest Service / BLM facility-repair RFQs in the **$50K–$250K** band
- DoD installation repair work below SAT under FAR 13.500 commercial-item simplified procedures (which can run higher — see §3 thresholds)
- GSA small-construction repair task orders
- Repeat-customer agencies that have been burned by pure LPTA on technically-fuzzy scopes (coastal envelope work, historic-structure repair, security retrofit) and want the discretion to pay slightly more for a stronger technical narrative

When it's a different beast (use a different playbook):

- **Pure LPTA — Pass/Fail technical, lowest priced wins.** Use [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md). The "no narrative" discipline is the inverse of what this playbook asks for.
- **Full FAR Part 15 best-value tradeoff.** Use [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md). 4 priced+narrative volumes, formal SSP / SSA / SSDD, oral presentations possible, FPR cycle.
- **Federal JOC task.** Use [`federal-joc-task.md`](federal-joc-task.md). UPB + coefficient, not Section M narrative.
- **Pre-solicitation watchlist (sources-sought / RFI / industry day).** Use [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md).

### Decision matrix — which federal playbook fits this RFP

| Signal in the RFP | LPTA | **SAP best-value (this playbook)** | FAR 15 best-value tradeoff |
|---|---|---|---|
| Form on cover | SF-1442 | **SF-18** (or SF-1449 if commercial-item) | SF-1442 |
| FAR Part cited | Part 14 / 15 | **Part 13 (often + Part 12)** | Part 15 |
| Section M language | "Lowest price among technically acceptable" / Pass/Fail factors | **"Best value" + factors evaluated comparatively, often "in groups of 3 lowest priced"** | "Trade-off" + factors weighted (e.g. "significantly more important than price") |
| Source-selection apparatus | None named (CO awards) | **None named — CO + CS evaluate; no SSP / SSA / SSDD** | Named: SSP referenced, SSA designated, SSDD will be issued |
| Volume structure | Volume I (Price) + Volume II (Technical/Past Perf) | **No formal volumes — single quote package** (technical narrative + price + experience refs + key personnel as sections) | Volume I (Price) + II (Technical) + III (Past Perf) + IV (Mgmt/Key Personnel) |
| Page-limit norms | 3–5 pp Volume II | **5–15 pp technical narrative + brief experience refs** | 25–50 pp Volume II + 15 pp Past Perf + 10 pp Mgmt |
| Past-performance count | 2 (per FAR M.1.4.B.f common pattern) | **3–5 prior-experience refs (Section L states the count)** | 3+ examples per Section L, with CPARS + PPQs |
| Bid bond required? | Yes (FAR 52.228-1, SF 24) | **Often no** — FAR 52.228-13 Alternative Payment Protections or no bond clause at submission | Yes |
| P&P bonds | At award if > $150K | At award if > $150K (or Alternative Payment Protections under 52.228-13) | At award if > $150K |
| RFQ vs RFP language | RFP | **RFQ** ("Request for Quotation" / "quoter" / "quote") | RFP |
| Typical RFP-to-award cycle | 45–90 days | **14–30 days** | 90–180 days |
| Typical contract value | sub-$500K | **$50K – $250K (civilian SAT); up to $7.5M micro-purchase / $4.5M commercial-item SAT for some scopes** | $500K – $10M |

## 2. Typical evaluation criteria

Section M (or, for SAP, the equivalent **"Basis for Award"** clause inside Section L) typically names three factors, evaluated comparatively rather than Pass/Fail:

| Factor | Typical posture | How it's evaluated |
|---|---|---|
| **Price** | Anchor of the comparison; often the gate that selects the subset evaluated on the other two factors | Total evaluated price across every CLIN + every priced option. CO ranks all quotes by price; **often evaluates technical capability + prior experience only on the lowest 3 (or 5) priced quotes**, then awards best value among that subset |
| **Technical capability** | Brief narrative demonstrating thorough understanding of the SOW + proposed schedule + approach. **REQUIRED** narrative — under-investing is a common loser pattern | Comparative adjectival assessment (typ "Excellent / Good / Acceptable / Marginal / Unacceptable") performed by CO + technical-office reviewer. Quotes rated "Unacceptable" on technical capability are eliminated regardless of price |
| **Prior experience** | 3–5 recent (typ ≤ 5 years) similar size-and-scope projects, each with owner / value / contact / scope / completion | Relevance + recency + quality. Subcontractor prior experience generally counts when the sub will execute that scope. No CPARS lookup is required at SAP scale — owner-side reference contacts are the primary verification source |

**Key contrast with pure LPTA:** the technical narrative is **not** Pass/Fail and **not** optional. A one-page "no exceptions" Volume II that wins on LPTA loses on SAP best-value because the CO has zero comparative basis to award to BPC over a competitor with the same price who wrote a substantive narrative.

**Key contrast with full FAR Part 15 tradeoff:** the narrative is much shorter (5–15 pp, not 25–50 pp) and the past-performance volume is references-and-facts (not CPARS + PPQs). Over-investing in volume structure, cover-letter formality, or oral-presentation prep is wasted on a SAP because the CO has no formal apparatus to consume it.

## 3. Dollar thresholds (FAR 2.101 + 13.003)

These thresholds (which the FAR updates periodically; cite the current FAR before relying on the number in a bid) drive whether an agency can use Part 13 simplified procedures at all and what flavor:

| Threshold | Current FAR value (2026) | What it gates |
|---|---|---|
| **Micro-purchase threshold (MPT)** | $10,000 (general); $2,000 (construction subject to Davis-Bacon); $2,500 (services subject to Service Contract Act) | Below MPT, agency may purchase without competition |
| **Simplified Acquisition Threshold (SAT)** | $250,000 (civilian + DoD general) | Below SAT, agency may use FAR Part 13 simplified procedures |
| **SAT for contingency / humanitarian / nuclear ops** | $800,000 domestic; $1.5M outside U.S. | Expanded SAT for specified contingency operations |
| **Commercial-item simplified procedures cap** | $7.5M (general); $15M (commercial services) | Under FAR 13.500, agency may use simplified procedures for commercial items up to this cap |
| **Test-program ceiling for certain commercial items** | $7.5M (acquisitions of commercial products); higher for commercial services | FAR 13.500 commercial-item simplified procedures cap — varies by category, verify per RFP |

**Why the thresholds matter for BPC posture:**

- A construction RFQ on SF-18 under SAT ($250K) means: no synopsis required pre-solicitation, lighter Section I clause set (52.213 series instead of 52.212 / 52.215), and the CO has wide discretion on evaluation method.
- A commercial-item construction RFQ between $250K and $7.5M may still ride FAR Part 13 simplified-acquisition rails under FAR 13.500 — but the clause inventory shifts to the 52.212-1 / -3 / -4 family. Read the RFQ cover page carefully to confirm which subpart applies.
- BPC's bonded envelope ($1M floor) covers the entire civilian SAT band and most of the commercial-item construction band easily.

## 4. Required forms — the SF-18 / SF-1449 / SF-1442 disambiguation

This is the most common federal-template foot-gun on a SAP bid. Pick the right form before drafting anything else.

| Form | When it's used | What it does |
|---|---|---|
| **SF-18** Request for Quotation | **Default for FAR Part 13 simplified-acquisition RFQs for commercial items or construction repair below SAT** — including the PAIS exemplar | 2-page RFQ-side form; the quoter completes price, acceptance period, and signature on page 2. No bid-bond block, no formal "Offer and Award" structure |
| **SF-1449** Solicitation/Contract/Order for Commercial Items | Commercial-item RFQs (FAR Part 12) when the CO **elects** to use 1449 instead of SF-18 for an integrated solicitation/contract/order document; common above SAT under FAR 13.500 | Combines solicitation + contract + order in one form. Used when the agency wants a single document the awardee signs that becomes the contract |
| **SF-1442** Solicitation, Offer and Award (Construction, Alteration, or Repair) | Default for **full** FAR Part 14 / Part 15 construction RFPs — **not** SAP | The form pure LPTA and full FAR 15 tradeoff bids use. If the RFQ cover says SF-1442, this is NOT a SAP — use [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) or [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md) instead |
| **SF-30** Amendment of Solicitation / Modification of Contract | Issued by the agency for any RFI response, due-date extension, or scope clarification | Acknowledge on the SF-18 (signature page) or SF-1449 (Block 19) and attach signed SF-30 pages in the quote package |
| **SF-24** Bid Bond | **Often NOT required on SAP** — FAR 52.228-1 must be invoked for SF-24 to apply, and SAP RFQs frequently use **FAR 52.228-13 Alternative Payment Protections** instead | Verify in Section I of the RFQ before ordering an SF-24 from the surety |
| **SF-25** Performance Bond / **SF-25A** Payment Bond | At award if contract > $150K (FAR 28.102-1) | 100% of contract value, on Treasury Circular 570 surety |

**Disambiguation rule of thumb:**

- Cover page says "Request for **Quotation**" + SF-18 + cites FAR Part 13 → this playbook
- Cover page says "Request for **Quotation**" + SF-1449 + cites FAR Part 12 + Part 13 → this playbook (commercial-item SAP variant)
- Cover page says "Request for **Proposal**" + SF-1442 + cites FAR Part 15 → NOT this playbook (use LPTA or full tradeoff)

### Section I clause inventory (typical SAP)

SAP RFQs ride a much **lighter** clause inventory than full FAR Part 15:

- **52.213 series** (Simplified Acquisition Procedures): 52.213-1 (Fast Payment), 52.213-2 (Invoices), 52.213-4 (Terms and Conditions — Simplified Acquisitions — Non-Commercial), as applicable
- **52.212 series** (Commercial Items, when FAR Part 12 layered on): 52.212-1 (Instructions to Offerors — Commercial), 52.212-3 (Offeror Reps & Certs — Commercial), 52.212-4 (Contract Terms — Commercial), 52.212-5 (Flowdowns)
- **52.219-6** Total Small Business Set-Aside — applies on a set-aside SAP just as on any other set-aside
- **52.222-6** Davis-Bacon (if construction labor on site, regardless of SAT/SAP status)
- **52.225-9** Buy American — Construction Materials (if construction materials involved)
- **52.228-13** Alternative Payment Protections (in lieu of standard bid bond + P&P)
- **52.232-39** Unenforceability of Unauthorized Obligations

**Not** typically in a SAP clause set: 52.215-1 (Instructions to Offerors — Competitive Acquisition), 52.215-22 (Limitations on Pass-Through Charges), most of the FAR Part 15 source-selection mechanics. If you see those, the RFQ is mis-labeled or the CO has elected full Part 15 procedures.

## 5. Submission format conventions

| Convention | SAP best-value norm | Contrast with LPTA / FAR 15 |
|---|---|---|
| Volume split | **None** — single quote package, sectioned (technical narrative, key personnel, prior experience, price summary) | LPTA: 2 volumes (Price + Tech). FAR 15: 4 volumes |
| File format | Single combined PDF ("QUOTE PACKAGE") or PDF + Excel price sheet | Same |
| File naming | Per Section L; common pattern: `{{SOLICITATION_NUMBER}} - {{PROJECT_NAME}} - QUOTE PACKAGE - email N of M.pdf` | LPTA / FAR 15 split by volume |
| Email subject | Per Section L; SAP RFQs often state an exact subject string to use | Same |
| Page limit on technical narrative | **5–15 pp** (Section L states the cap when there is one; many SAP RFQs leave it open) | LPTA: 3–5 pp. FAR 15: 25–50 pp |
| Prior-experience count | **3–5** (Section L states the count — see PAIS at "minimum 3, maximum 5") | LPTA: typ 2. FAR 15: typ 3+ |
| Key-personnel resume blocks | **Yes — short-form** (½ to 1 page per named role: PM, Super, QC) | LPTA: typ omitted. FAR 15: full 1-page resumes per named role, possibly with commitment letters |
| Wet-ink vs e-signature on SF-18 / SF-1449 | E-signature acceptable post-2022 unless RFQ explicitly forbids | Same |
| Acceptance period | **60 calendar days** common on SAP (PAIS = 60) | LPTA: 90 days common. FAR 15: 120 days common |
| Delivery cutoff time | Local time of issuing office; **email submission very common on SAP** (PAIS = email only) | LPTA / FAR 15: portal submission more common |
| Late submission | Rejected; no narrow exception window because FAR 52.215-1 is typically NOT in the clause set | Same outcome, different clause |
| Email size limit | **25 MB common** — split across emails if larger and number them "email N of M" in subject | Often the same limit on portal-based submissions |
| Send-by-buffer | Submit 30+ minutes early | Same |

**Send the quote 30+ minutes early.** SAP is email-heavy and email delivery to government tenants (Outlook 365 GCC, GCC High) has occasionally-multi-minute relay delays.

## 6. Typical timeline

SAP cycle times are dramatically shorter than full FAR Part 15:

| Phase | Days from RFQ release | Notes |
|---|---|---|
| RFQ release on SAM.gov | T-0 | Often posted with abbreviated synopsis (FAR 5.202(a)(13) exempts SAT-band acquisitions from full synopsis) |
| Site visit (recommended; often non-mandatory) | T+3 to T+7 | RSVP via Contract Specialist email |
| RFI cutoff | T+5 to T+10 (often 3 calendar days after site visit) | After cutoff, responses "may not be received" |
| Quote due | **T+14 to T+30** | The signature speed-up vs. LPTA (T+30–45) or FAR 15 (T+45–90) |
| CO evaluation | 1–3 weeks | Lighter machinery: rank by price, evaluate technical + experience on lowest 3 (or 5), award |
| Award notice | **T+30 to T+60** from RFQ release | Posted on SAM |
| NTP issuance | Within 5–10 days of award | RFQ Section F |
| Performance period | Per RFQ — typical 30–120 calendar days | Tighter than LPTA's 60–180 |

**The whole cycle compresses.** A SAP RFQ that drops on the 1st can be awarded by the 30th. Plan the bid-prep workflow accordingly — there is no slack for sub-bid solicitations to be issued late or for past-perf reference contacts to be tracked down on Day 25.

## 7. Common pitfalls

1. **Treating it like full FAR Part 15.** Over-investing in 4-volume structure, cover-letter formality, oral-presentation prep, or CPARS hygiene that no one is going to consume. SAP machinery is lighter — match the package to it. Wastes 20–40 estimator-hours per bid.
2. **Treating it like pure LPTA.** Under-investing in the technical narrative. A one-page "no exceptions" Volume II that wins on LPTA loses on SAP best-value because the CO has nothing comparative to score and will award to the next-lowest priced quoter who wrote 8 pages of competent narrative.
3. **Missing the "groups of 3" implication for pricing posture.** If the CO will only evaluate technical capability on the lowest 3 priced quotes, a 4th-place price is **eliminated regardless of narrative quality**. Price must clear the lowest-3 cutoff to even get read on the other factors. Bid posture is therefore "tightly competitive on price + strong on technical" — not "premium price + best narrative."
4. **Wrong SF form on the quote.** Using SF-1442 (construction RFP) when the RFQ asked for SF-18 (or vice versa) is a common eliminator. Read the RFQ cover page first; default to SF-18 for sub-SAT FAR Part 13 RFQs.
5. **Ordering an SF-24 bid bond that the RFQ doesn't require.** SAP RFQs often use FAR 52.228-13 Alternative Payment Protections instead of standard bid bond + P&P. Verify Section I before paying for a bid bond.
6. **Under-counting prior-experience refs.** Section L typically states "minimum 3 and/or maximum 5" — submitting only 2 fails the count check on its face. Submit at the maximum the RFQ allows.
7. **Stale boilerplate in the RFQ.** SAP RFQs are often built from agency templates that survived from a prior solicitation (PAIS had stale POP dates carried from a 2025 SOW). Walk every page, flag inconsistencies via RFI, document operative source in your quote's cover note.
8. **SAM.gov amendment-watch lapse.** SF-30 amendments are common mid-window — PAIS had Amd 0001 within 14 days of release moving the due date by 10 days and the site visit by 15 days. Subscribe to SAM.gov amendment notifications for the solicitation; re-check SAM at Due-3.
9. **Davis-Bacon WD assumption.** DBA applies to construction labor on site regardless of SAT/SAP status. If the RFQ attaches a WD, the rates on the WD effective on the day of quote opening govern the contract. Transcribe + re-price on amendment.
10. **Per-diem + travel under-counted on remote sites.** SAP RFQs are often for small remote facilities (national park backcountry, USFWS hatcheries, military training-range outbuildings). A 60-day POP for a 3-person crew at GSA per-diem rate adds non-trivial cost. Don't bid off "headquarters labor" assumptions.

## 8. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

Same federal-SBA thresholds apply as on LPTA — see [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) §3 for the full posture table (SAM active, UEI `LM4YHVQ71QG7`, CAGE `9LET0`, NAICS 236220 ≤ $45M small, Reps & Certs ≤ 12 months, FAR 52.204-21 Basic Safeguarding, insurance, bondability, past-perf picks per `firm-profile.json → past_project_selection_rules`). The differences specific to SAP best-value:

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| Technical-narrative library (paste-ready by trade / scope archetype) | Yes — short-form narrative blocks for envelope, roofing, finishes, MEP, site work | Partial — [`firm/proposal-library/boilerplate/`](../proposal-library/boilerplate/) covers safety + QC + schedule but not short-form trade narrative for SAP-class quotes | ⚠️ Day-3 priority: extract 1-page narrative blocks per trade from prior bids |
| Prior-experience reference block library (½-page per project) | Yes | Partial — [`firm/proposal-library/past-performance/`](../proposal-library/past-performance/) carries Lavon RV Park + Hindu Temple + Holiday Inn long-form. Need short-form ½-page block per project. | ⚠️ Day-3 priority |
| Key-personnel short-form (½-page resume per named role) | Yes | Partial — [`firm/proposal-library/key-personnel/`](../proposal-library/key-personnel/) carries full 1-page resumes. Need ½-page short-form for SAP packages. | ⚠️ Day-3 priority |
| Bonded envelope for SAT-band ($50K–$250K civilian; up to $7.5M commercial-item) | Single-project ≥ $250K (civilian SAP); ≥ $7.5M aspirational for commercial-item SAP at the cap | $1M floor established by Lavon RV Park performance bond | ✅ Civilian SAP; ⚠️ commercial-item SAP at the cap requires surety capacity confirmation |
| Insurance limits for SAP (typically lower than LPTA baseline — DOI 1452.228-70 = $100K/$500K/$500K) | Per RFQ-specified agency clause | $1M / $2M on current GL policy when active — over-meets DOI baseline | ⚠️ Verify current COI |

## 9. Required compliance docs (per bid)

See [`firm/compliance/README.md`](../compliance/README.md) for the registry. SAP per-bid checklist (subset of LPTA baseline; some items drop out):

- [ ] SAM.gov "Entity Information" PDF, pulled within 24 hours of submission
- [ ] SAM Reps & Certs printout (or 52.204-8(d) / 52.212-3 incorporation page if Reps are ≤ 12 months current)
- [ ] Current GL COI naming the issuing agency as Additional Insured + primary/non-contributory + waiver of subrogation (verify required limits against the RFQ-cited agency clause — often lower than $1M / $2M)
- [ ] Current WC + Auto + Umbrella COIs
- [ ] Surety bondability commitment letter (often required at submission for the post-award P&P / Alternative Payment Protection per FAR 52.228-13)
- [ ] **Brief technical-capability narrative** (5–15 pp typical — DO NOT skip)
- [ ] **3–5 prior-experience references** with owner / value / contact / dates / scope / completion + working-phone-and-email-verified POC for each
- [ ] **Key-personnel short-form** (½-page per named role: PM, Super, QC)
- [ ] Davis-Bacon WD acknowledgment (transcribed wage rates from WD attached to the RFQ) — if construction labor on site
- [ ] Buy American Certificate (FAR 52.225-4) signed — if construction materials
- [ ] Subject-line + email-format compliance per Section L

**Generally NOT required at SAP submission** (in contrast to LPTA / FAR 15):

- SF-24 Bid Bond (unless RFQ specifically invokes FAR 52.228-1)
- Affirmative-Action / OFCCP rep (52.222-22 / 52.222-25) — typically only if RFQ explicitly cites
- CPARS pull / PPQs — past-performance references suffice at SAP scale
- Subcontracting plan (FAR 52.219-9) — typically only triggered above $750K for non-small primes

## 10. SAP pricing discipline

| Component | % of direct cost | Notes |
|---|---|---|
| Direct cost (subs + materials + self-perform labor) | 100% | Site visit + ≥ 2 sub quotes per CLIN to tighten |
| General conditions / supervision | 8–14% | Counts toward 15% on-site self-perform |
| Bonds (post-award P&P or alt-payment protection) | 1.0–2.0% | Lower than LPTA because bid bond is often absent |
| Insurance | 2–4% | If carried as a percentage |
| DBA labor-burden uplift | 0–4% | Only if firm's labor rates are sub-prevailing |
| Contingency | 4–6% | Between LPTA's 3–5% floor and FAR 15's 5–8% — SAP tightens vs. FAR 15 because schedule is shorter but loosens vs. LPTA because technical narrative buys some buffer |
| Overhead | 8–11% | Slightly above LPTA floor because technical-narrative drafting is real estimator-hour cost |
| Profit | 5–8% | Above LPTA's 3–6% — best-value comparative trade-off gives the SSA a path to award at a slightly higher price when the technical narrative + prior experience are stronger |
| **Total markup over direct** | **~30–45%** | Direct-to-bid multiplier of ~1.30–1.45 (between LPTA's 1.25–1.40 and FAR 15's 1.35–1.55) |

### "Groups of 3" pricing posture

When Section M (or the SAP-equivalent "Basis for Award") states the CO will evaluate technical + experience **only on the lowest 3 (or 5) priced quotes**:

- **Price must clear the lowest-3 cutoff** to get the technical narrative read at all. A 4th-place quote is eliminated on price regardless of narrative quality.
- **Once inside the lowest-3 envelope, technical + experience pull weight.** A quote that is #2 on price but #1 on technical + experience can win over a quote that is #1 on price but #3 on technical + experience.
- **Bid posture: tightly competitive on price + strong on technical.** Bid the magnitude floor + 5–15%, **with** a substantive 5–15 page technical narrative + 3–5 prior-experience refs + short-form key personnel. Don't bid at the magnitude midpoint and rely on narrative quality — you won't make the lowest-3 cut.
- **The technical-capability buffer** (the gap between magnitude floor and BPC's competitive bid posture) is where the SAP pricing strategy lives. Slightly tighter than LPTA's "floor + 5–10%" because you need narrative-drafting room; slightly looser than FAR 15's "magnitude midpoint" because you still need to make the price cutoff.

### What still applies from LPTA discipline

- **Don't bid below magnitude floor.** "Unreasonably low" determinations under FAR 13.106-3 are rarer than under FAR 15.404-1(d) but still possible.
- **Don't pad profit unjustifiably.** Even on best-value comparative, the CO has price-realism discretion and an offer that is materially above the magnitude band invites a "high price did not reflect best value" award narrative for the competitor.
- **Don't unbalanced-bid.** Front-loading early CLINs raises the same CO concern under FAR 13 as under FAR 15.
- **Every CLIN priced.** A blank CLIN is non-responsive even when the grand total is correct.

## 11. Reusable language blocks

These are paste-ready short-form blocks tailored to SAP best-value quote packages. They live in [`firm/proposal-library/`](../proposal-library/README.md); the cross-references below show which file holds the canonical copy or, where not yet authored, what to extract from existing long-form blocks.

| Block | Where it lives | When to use |
|---|---|---|
| SAP best-value cover-note opening (½ page) | `firm/proposal-library/exec-summary-archetypes/federal-sap-best-value.md` *(TODO — author after first SAP bid ships)* | Front of the quote package; states no exceptions, names the technical / prior-experience sections, and signals best-value posture |
| Technical-approach narrative skeleton (5–15 pp) | `firm/proposal-library/boilerplate/technical-approach-sap-skeleton.md` *(TODO)* | Project understanding (1 pp) → proposed schedule (1 pp) → phasing + site logistics (1–2 pp) → trade-by-trade approach (3–8 pp) → QC + safety summary (1 pp) |
| Prior-experience reference block — short-form ½-page per project | [`firm/proposal-library/past-performance/`](../proposal-library/past-performance/) — extract short-form from existing long-form picks per [`firm/firm-profile.json → past_project_selection_rules`](../firm-profile.json) | Bundled 3–5 to a section; each block carries owner / value / contact / dates / scope / completion + 2-sentence relevance statement |
| Key-personnel short-form (½ page per role) | [`firm/proposal-library/key-personnel/`](../proposal-library/key-personnel/) — trim existing 1-page resumes to ½ page | One block each for PM, Super, QC; for some RFQs add Principal in Charge + Safety |
| SAM Reps & Certs incorporation (FAR 52.204-8(d) or 52.212-3) | [`firm/proposal-library/boilerplate/`](../proposal-library/boilerplate/) (see boilerplate index) | Final page of the price section |
| Buy American Certificate (FAR 52.225-4) | [`firm/proposal-library/boilerplate/`](../proposal-library/boilerplate/) (see boilerplate index) | After SAM Reps & Certs incorporation if RFQ triggers FAR 52.225-9 / -11 |
| Surety commitment letter (post-award P&P or 52.228-13 alt-payment) | [`firm/proposal-library/boilerplate/`](../proposal-library/boilerplate/) — letter request template to surety | Attach surety's commitment letter (BPC drafts the request; surety issues on letterhead) |

Until the SAP-specific blocks are authored, adapt the LPTA-equivalent blocks from [`firm/proposal-library/`](../proposal-library/README.md) — most carry across with light edits to remove "no narrative" language and add the technical-capability section.

## 12. Cross-references

- **LPTA sibling playbook (the rigid end of the SAP-to-LPTA-to-FAR-15 continuum):** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md)
- **Full FAR Part 15 best-value tradeoff sibling playbook (the narrative-heavy end):** [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md)
- **Pre-solicitation watchlist (upstream of every federal SAP bid):** [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md)
- **Workspace template:** [`bids/_TEMPLATES/federal-simplified-acquisition-best-value/`](../../bids/_TEMPLATES/federal-simplified-acquisition-best-value/)
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Exemplar shipped (dogfood) bid:** [`bids/pais-cabin-140P6026Q0029/`](../../bids/pais-cabin-140P6026Q0029/) — see the "Template dogfood notes" section at the bottom of `00-overview.md` for the quirks this template was authored to close
- **Scope templates for federal repair / renovation work:** [`firm/scope-templates/roof-repair-historic.md`](../scope-templates/roof-repair-historic.md), [`firm/scope-templates/restroom-renovation-historic.md`](../scope-templates/restroom-renovation-historic.md), [`firm/scope-templates/arc-rehab-steel-building.md`](../scope-templates/arc-rehab-steel-building.md)
