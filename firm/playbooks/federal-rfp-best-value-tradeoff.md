# Playbook — Federal RFP, Best-Value Tradeoff (FAR Part 15)

> **Exemplar bid:** *not yet exemplified by a shipped BPC bid.* Use this playbook the first time BPC pursues a federal RFP where Section M scores non-price factors against price rather than gating them Pass/Fail (LPTA).
>
> **Matching workspace template:** *to be created — clone `bids/_TEMPLATES/federal-sba-rfq-lpta/` and add a Volume II/III/IV technical-narrative scaffold.*

## 1. Procurement description

Federal civilian and DoD agencies use **best-value tradeoff source selection under FAR 15.101-1** when the government wants the discretion to pay more for a stronger technical proposal. This is the opposite end of the FAR 15.101 continuum from LPTA (covered in [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md)). Under tradeoff:

- The contracting officer **may** award to other than the lowest-priced offeror or other than the highest-rated technical offeror, so long as the tradeoff is documented in the Source Selection Decision Document (SSDD) per FAR 15.308.
- Non-price factors **carry weight against price** — Section M usually states whether they are "significantly more important than", "approximately equal to", or "significantly less important than" price.
- The proposal is structured as separate priced + technical volumes (often four: Price, Technical Approach, Past Performance, Management/Key Personnel) so the Source Selection Authority (SSA) can score them independently before tradeoff.

When you'll see it:

- Federal construction in the **$500K–$10M band** where the agency wants to differentiate on schedule confidence, key personnel, or technical approach
- USACE / NAVFAC / GSA / NIH / VA renovation, modernization, or design-build IDIQ task orders
- Repeat-customer agencies (NPS regions, USFWS regions) that have been burned by LPTA awards underperforming and want to weight past performance more heavily
- Multiple-award task-order competitions inside a single-award IDIQ (FAR 16.505) — the underlying IDIQ may be LPTA but task orders run tradeoff

When it's a different beast (use a different playbook):

- **LPTA** — Pass/Fail technical, lowest priced wins. Use [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md).
- **JOC task order** — pricing via Unit Price Book + coefficient; technical is minimal. Use [`federal-joc-task.md`](federal-joc-task.md).
- **Federal A/E commission** — FAR Part 36.6 Brooks Act qualifications-based selection; no price competition until the Brooks-selected firm is chosen. Different playbook entirely (not yet authored).
- **Pre-solicitation watchlist tracking** — before the RFP drops, opportunities are tracked via sources-sought + RFI responses. Use [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md).

## 2. Typical evaluation criteria

Section M factor weights vary widely. The table below shows the **modal** federal-construction tradeoff split BPC should pattern-match against:

| Factor | Typical weight | Sub-criteria | Evaluation method |
|---|---|---|---|
| **Technical Approach** | 30–45% | Project understanding; phasing + schedule logic; site logistics; QC/Safety integration; subcontracting plan | Narrative scored against an adjectival rating scale (Outstanding / Good / Acceptable / Marginal / Unacceptable) per Source Selection Plan (SSP) |
| **Past Performance** | 20–30% | Recency (typ ≤ 3 yrs), relevance (similar size + scope + complexity), quality (CPARS + PPQs from agency references) | Confidence rating (Substantial / Satisfactory / Limited / No / Unknown Confidence) per FAR 15.305(a)(2) |
| **Price** | 20–30% | Total evaluated price including all priced CLINs + option years + optional alternates | Price reasonableness + price realism per FAR 15.404-1 |
| **Management / Key Personnel** | 5–15% | PM, Super, Safety, QC résumés; org chart; commitment letters; substitution policy | Adjectival rating; sometimes oral presentations |
| **Small Business Participation** (or Subcontracting Plan) | 5–10% | Self-perform %, small-business subcontracting %, SDVOSB/WOSB/HUBZone goals if applicable | Narrative + numeric commitments |

**Key contrast with LPTA:** under tradeoff, every page of the technical volume is potentially worth score. The "shortest defensible Volume II Passes" discipline from LPTA is **wrong** here — under-investing in technical narrative gives the competitor with a stronger story a defensible tradeoff path even at a higher price.

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| SAM.gov registration active | Yes | Active per Day-1 sweep | ⚠️ Verify before each federal bid |
| UEI + CAGE | 12-char + DLA-issued | `LM4YHVQ71QG7` + `9LET0` | ✅ |
| NAICS 236220 small (≤ $45M 3-yr avg) | Yes | Self-attested small | ⚠️ Re-verify annually |
| Reps & Certs ≤ 12 months current per FAR 52.204-8(d) | Yes | Verify each bid | ⚠️ |
| CPARS in CPARS.gov for prior federal awards | Required to demonstrate past performance objectively | **`[USER TO FILL — BPC has not yet completed a federal performance period; first CPARS expected from Lavon RV Park-equivalent federal bid]`** | 🔴 — major posture gap on tradeoff bids where CPARS dominates Past Performance scoring |
| PPQs (Past Performance Questionnaires) prepared for past projects | Yes — 3 ready-to-send PPQ templates pre-filled with project facts | `[USER TO FILL — none on file; build PPQ for Lavon, Holiday Inn, Hindu Temple]` | 🔴 — needed for Day-2/3 capability build |
| Key-personnel résumés in federal format (1-page max, recent projects emphasized) | Yes | Partial — see [`firm/proposal-library/key-personnel/`](../proposal-library/key-personnel/) | ⚠️ |
| Technical narrative library (paste-ready by trade) | Yes | Partial — see [`firm/proposal-library/boilerplate/`](../proposal-library/boilerplate/) | ⚠️ — expand on each tradeoff bid |
| Subcontracting plan template (FAR 52.219-9 Schedule B if > $750K) | Yes | `[USER TO FILL — first subcontracting-plan threshold bid will trigger build]` | ⚠️ |
| Bond capacity sufficient for $500K–$10M range | Single-project capacity ≥ project value | $1M floor established; needs to climb | ⚠️ — coordinate with surety before committing to $1M+ tradeoff bid |
| Commercial GL $2M / $4M (typical tradeoff threshold above LPTA baseline) | $2M / $4M | $1M / $2M on current policy | ⚠️ — pull current COI; may need to bind additional Umbrella |

## 4. Required compliance docs (per bid)

See [`firm/compliance/README.md`](../compliance/README.md) for the registry. Per-bid checklist (additive to LPTA baseline in [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) §4):

- [ ] All LPTA-baseline docs (SAM entity, Reps & Certs, COIs, bondability letter, bid bond per FAR 52.228-1 / SF 24, Buy American cert, DBA acknowledgment, past performance summaries)
- [ ] **CPARS pull** for any past federal performance period (gov.cpars.gov) — attach printout to past-performance volume
- [ ] **PPQs sent** to all past-performance reference contacts named in the volume, **with sufficient lead time** (typically 21 days before due) so the reference can return the questionnaire to the CO
- [ ] **Key-personnel commitment letters** signed by each named individual confirming availability for the period of performance
- [ ] **Subcontracting plan (FAR 52.219-9 Schedule B)** if total contract value > $750K and prime is not small business on the bid NAICS — even small-business primes may need to submit a plan if the RFP explicitly requires it
- [ ] **Affirmative-Action Plan** (FAR 52.222-22 / -25) if firm > 50 employees + over EEO threshold
- [ ] **Oral presentation slides** if RFP §L requires an oral presentation — typically 30–60 minutes, 20–40 slides, key personnel must present in person or via Teams/Zoom

## 5. Standard solicitation forms

Same SF 1442 / SF 30 / SF 24 / SF 25 / SF 25A family as LPTA — see [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) §5. Additional on tradeoff bids:

| Form | When it's used | What it does |
|---|---|---|
| **PPQ (agency-specific)** | Most federal tradeoff RFPs include a PPQ template in §L attachments | Past-performance reference contact fills it out and emails back to the CO directly |
| **DD Form 2579** Small Business Coordination Record | DoD tradeoff bids only | Filed with subcontracting plan |
| **SF 1411** Contract Pricing Proposal Cover Sheet | Sometimes required for tradeoff > $700K to capture cost-or-pricing data | Cover sheet for the price volume |
| **Oral presentation script** | Custom per RFP | Not a "form" but treated like one — version-controlled, signed off by Principal in Charge before delivery |

## 6. Submission portals

- **SAM.gov** — primary discovery
- **PIEE / WAWF** — DoD tradeoff (USACE, NAVFAC, USAF) often uses the PIEE Solicitation Module
- **Agency e-portals** — GSA (`https://www.fbo.gov/` predecessor + `https://buy.gsa.gov/` for IDIQ), NIH (`https://obssr-decd.od.nih.gov/`), VA Vendor Portal, USDA Forest Service portal
- **PROCAS / VPP** — agency-specific vendor portals appearing more in 2024–2026 deals

## 7. Submission format conventions

| Convention | Tradeoff norm | Source |
|---|---|---|
| Volume split | Volume I — Price; Volume II — Technical Approach; Volume III — Past Performance; Volume IV — Mgmt/Key Personnel (sometimes folded into II) | FAR L.2.1.1 + RFP §L |
| File format | PDF; one PDF per volume | RFP §L |
| Page limits | Technical: typically 25–50 pages; Past Perf: typically 3 examples × 5 pages = 15 pages; Mgmt: typically 10 pages; Price: no limit | RFP §L |
| Font + spacing | 12 pt Times New Roman or 11 pt Arial, single-spaced, 1" margins (very common) | RFP §L |
| Tab/section dividers | Required between volumes; some RFPs require tabs within volumes (e.g. one tab per past-performance example) | RFP §L |
| Wet ink vs e-signature | E-signature generally OK post-2022 unless RFP says otherwise | FASA |
| Acceptance period (block 13d) | ≥ 120 calendar days common for tradeoff (longer than LPTA's 90) | RFP cover |
| Delivery cutoff time | Same as LPTA — local time of issuing office | RFP cover |
| Late submission | Rejected per FAR 52.215-1(c)(3) with narrow government-mishandling exception | FAR 52.215-1 |

**Submit 60+ minutes early.** Tradeoff packages are larger (often > 20 MB total); email attachments can fail silently.

## 8. Typical timeline

| Phase | Days from RFP release | Notes |
|---|---|---|
| RFP release on SAM.gov | T-0 | Often preceded by sources-sought + draft RFP — see [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md) |
| Industry day / pre-proposal conference (sometimes mandatory) | T+5 to T+10 | Slide deck + Q&A typically posted as amendment |
| Site visit window | T+5 to T+15 | Take measurements + photos + meet site POC |
| RFI cutoff | T+20 to T+30 | After cutoff, responses "may not be received" — file early |
| Proposal due | T+45 to T+90 (tradeoff is longer than LPTA's T+30–45) | |
| Initial evaluation | 4–8 weeks | Technical + Past Perf scoring per SSP |
| Discussions / clarifications (FAR 15.306) | Optional; if CO opens discussions, treat as mini-RFI cycle | All offerors in competitive range get equivalent discussion items |
| **Final Proposal Revision (FPR)** | Triggered if discussions opened | One revised proposal submission; typically 7–14 days to respond |
| SSDD signed | Per Source Selection Plan timeline | |
| Award notice | T+90 to T+180 from RFP release | Posted on SAM; unsuccessful offerors entitled to debriefing per FAR 15.506 |
| Debriefing window | ≤ 5 days after award notice request | Use as input to next bid |

## 9. Common pitfalls

1. **Treating tradeoff like LPTA.** The "shortest defensible Volume II Passes" discipline from LPTA *loses* tradeoff bids. Every page of the technical volume potentially earns score; under-investing in narrative quality gives the competitor a defensible tradeoff path.
2. **No CPARS history.** A firm with no federal performance period to point to scores **"Unknown Confidence"** at best on Past Performance — which under tradeoff means a lower-rated competitor with documented CPARS can win at a higher price. BPC must surface CPARS hygiene as a Day-3+ capability priority.
3. **PPQs sent late.** Many tradeoff CO templates require the PPQ to be returned by the reference *directly* to the CO. If the reference contact is on PTO or the email goes to spam, the past-performance volume is hollow. Send PPQs ≥ 21 days early and follow up.
4. **Key personnel "bait and switch."** Naming a marquee PM on the bid but staffing the actual project with a less-experienced PM is **the** classic federal tradeoff pitfall. FAR Part 7.105 + RFP §H clauses typically require CO consent for key-personnel substitution post-award; non-compliance is a contracting offense and a CPARS-killer.
5. **Oral presentation under-prep.** When orals are in §L, they are scored. Treat them like a board meeting — full deck, dry run, Principal in Charge presenting, named PM + Super + QC fielding questions. Trust falls hardest when the named PM can't answer a phasing question on the fly.
6. **Subcontracting plan thin.** Even a small-business prime may have to submit a Schedule B subcontracting plan; agencies score it. Default goals: small business 25%, SDB 5%, WOSB 5%, HUBZone 3%, SDVOSB 3%, VOSB 3% (FAR 19.708). Beat the defaults where defensible.
7. **Price realism low.** FAR 15.404-1(d)(3) lets the CO downgrade a technical rating if the price is "unrealistically low" — suggesting the offeror doesn't understand the scope. Bid the magnitude, not the floor.
8. **Discussions response sloppy.** When CO opens discussions, every offeror in the competitive range gets equivalent discussion items. Address each item explicitly in the FPR cover letter (item-by-item table). Skipping or rebutting an item is a non-responsive signal.
9. **Unbalanced bid** — front-loading early CLINs to maximize early-period cash flow. CO will flag and may award to second-lowest if the unbalance is material (FAR 15.404-1(g)).
10. **Source-selection-sensitive info leak.** Discussion items, draft scoring, FPR-cycle conversations are all CO-sensitive — do not discuss with subs in writing unless absolutely required. Treat the entire post-due-date period as if every email is FOIA-able.

## 10. Tradeoff pricing discipline

| Component | % of direct cost | Notes |
|---|---|---|
| Direct cost (subs + materials + self-perform labor) | 100% | More site-visit time than LPTA — tradeoff agencies often look for fewer hidden-condition surprises |
| General conditions / supervision | 10–16% | Tradeoff weights schedule confidence; staff the GC accordingly |
| Bonds (bid + P&P) | 1.5–2.5% | Per surety |
| Insurance | 3–6% | Higher Umbrella ($5M typical, vs LPTA's $1M / $2M baseline) |
| DBA labor-burden uplift | 0–4% | Same as LPTA |
| Contingency | 5–8% | Tradeoff allows more headroom than LPTA |
| Overhead | 9–14% | Above the LPTA floor |
| Profit | 6–10% | Tradeoff allows profit > LPTA's 7% ceiling when past-performance + technical can defend it |
| **Total markup over direct** | **~35–55%** | Direct-to-bid multiplier of ~1.35–1.55 |

**Bid the magnitude midpoint, not the floor.** A tradeoff competitor with a stronger technical volume can win at the magnitude midpoint even when a cheaper offeror scored Acceptable Technical. Bidding the floor signals "race to the bottom" and gives the SSA a tradeoff path away from BPC.

**Quote at full insurance + bond uplift.** Tradeoff often catches under-bonded competitors at price realism review — don't be the one.

## 11. Reusable language blocks

These will be added to [`firm/proposal-library/`](../proposal-library/README.md) as BPC pursues its first tradeoff bid:

| Block | Where it will live | When to use |
|---|---|---|
| Tradeoff exec-summary opening (Volume II cover) | `firm/proposal-library/exec-summary-archetypes/federal-tradeoff.md` *(TODO — author after first tradeoff bid)* | Front of Volume II (Technical) — sets the "why us at this price" tradeoff narrative |
| PPQ template (BPC reference contact instructions) | `firm/proposal-library/past-performance/ppq-template.md` *(TODO — Day-3 priority)* | Sent to past-perf reference contacts to fill out and email directly to the CO |
| Subcontracting plan (FAR 52.219-9 Schedule B) | `firm/proposal-library/boilerplate/subcontracting-plan-schedule-b.md` *(TODO)* | Volume IV — when contract value > $750K and SBP required |
| Oral presentation deck skeleton | `firm/proposal-library/presentation/oral-presentation-skeleton.md` *(TODO)* | When RFP §L requires orals |
| Key-personnel commitment letter | `firm/proposal-library/key-personnel/commitment-letter-template.md` *(TODO)* | Signed by each named individual |
| Discussions response cover-letter pattern | `firm/proposal-library/boilerplate/discussions-response-cover.md` *(TODO)* | Filed with FPR if CO opens discussions |

Until these are authored, paste the LPTA-equivalent block from [`firm/proposal-library/`](../proposal-library/README.md) and adapt.

## 12. Cross-references

- **LPTA playbook (sibling on the FAR Part 15 continuum):** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md)
- **Pre-solicitation watchlist (upstream of every federal tradeoff bid):** [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md)
- **Workspace template:** *to be created by cloning `bids/_TEMPLATES/federal-sba-rfq-lpta/` and adding a Volume II/III/IV technical-narrative scaffold*
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Capability statement (used heavily in tradeoff past-perf volumes):** [`firm/proposal-library/capability-statement/`](../proposal-library/capability-statement/) when shipped
- **Federal volumes library (under build):** [`firm/proposal-library/federal-volumes/`](../proposal-library/federal-volumes/)
- **PPQ library (Day-3 priority):** *not yet shipped*
