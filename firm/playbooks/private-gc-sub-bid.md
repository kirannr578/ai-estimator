# Playbook — Private General Contractor, Sub-Bid Pursuit

> **Exemplar bid (live, watchlist):** [`bids/_WATCHLIST/longhorn-little-elm-bcibelisle.md`](../../bids/_WATCHLIST/longhorn-little-elm-bcibelisle.md) — Longhorn Steakhouse Little Elm fit-out, sourced through a private national GC (anonymized handle **GC-Belisle** in narrative; folder retains the literal name). Two near-term exemplars from the same DFWMSDC batch reinforce the lane: McLennan Phase 4 CSC Cosmetology (GC = HCS Inc.) and 7-Eleven Celina ground-up (GC = Ready Construction).
>
> **Matching workspace template:** *to be created — clone `bids/_TEMPLATES/texas-state-csp-hsp/`, **strip out** HSP / CIQ / HB 1295 / TX state procurement-code references, **strip out** SF 1442 / FAR clauses, **swap in** GC-portal mechanics + GC's prime-contract flow-down review + sub-tier insurance addenda. Keep the takeoff + estimate stack; the dollars-and-cents work doesn't change with the procurement vehicle.*

## When to use this playbook

Use this playbook when BPC is bidding as a **subcontractor to a private general contractor** — i.e., the contracting party above BPC is a privately-owned commercial GC (regional builder, restaurant-rollout specialist, ground-up retail GC, hotel-brand GC, private-developer GC), and the project owner is **also private** or is a private-equity / institutional party with no public-procurement statute attached. This is the procurement archetype where **the GC's prime contract is the binding document**, not a FAR clause or a Texas Government Code chapter. It is materially different from BPC bidding as a prime to a public owner — different rules, different docs, different risks, different escape valves when things go sideways.

If the underlying project is **public-funded** (federal, state, or local money flowing through the private GC as prime), most of this playbook still applies at the sub tier, but you must also pull the public-money overlay: Davis-Bacon, MBE/SBE participation goals, Buy American, certified payroll, etc. Confirm the funding source in Step 2 of the 5-step pursue checklist below — that confirmation drives whether this playbook fully owns the pursuit or whether a public-procurement playbook also applies in parallel.

## Why we needed this playbook — three triggers in `_learning-log.md`

The same gap surfaced three times during the 2026-05-30 ingest week. Quoted verbatim from [`_learning-log.md`](_learning-log.md):

1. **2026-05-30 — DFWMSDC Construction Members digest** (first identification):
   > "No 'private GC sub-bid' playbook exists. Both pursue scaffolds in this batch (`mcc-cosmetology-phase4-2026-0622`, `7eleven-celina-2026-0605`) are subcontractor quotes to private commercial GCs (HCS Inc. and Ready Construction respectively). The current `firm/playbooks/README.md` procurement-type matrix lists 'Private commercial / institutional negotiated' only as an 'ad-hoc; not playbook-grade' row at the bottom. **Recommend** seeding `firm/playbooks/private-gc-sub-bid.md` the next time a GC sub-bid lands."

2. **2026-05-30 — DFWMSDC followup item** (same entry, restated as a tracked recommendation):
   > "[ ] **Recommend:** seed `firm/playbooks/private-gc-sub-bid.md` from the next GC sub-bid that lands (this batch alone is enough material to draft the playbook, but the user task-brief asked for triage + scaffold only, not playbook authoring)."

3. **2026-05-30 (continued) — McLennan Cosmetology + Camp Maxey ingest** (third reinforcement, after McLennan Phase 4 + Camp Maxey Roof both landed as private-GC sub-quotes):
   > "Playbook gaps: (a) `firm/scope-templates/commercial-tpo-reroof.md` does not exist… (b) `firm/scope-templates/cosmetology-classroom-reno.md` does not exist… **(c) 'Private GC sub-bid' playbook gap from earlier today's DFWMSDC entry remains open and is reinforced by both opportunities.**"

A live BCI Belisle / Longhorn Little Elm watchlist entry was created the same day under the same digest, making the gap impossible to defer any further. This playbook is the response.

## 1. Procurement description

Private General Contractors solicit subcontractor quotes through one of three channels, and the channel matters because it dictates the entire submission mechanic:

- **GC portal (most common in 2024–2026):** the GC posts plans + specs + a sub bid form + an invitation list on a SaaS bid-management platform. Subs log in, download, price, upload. The GC's portal of choice is itself an indicator of GC size and process maturity (see §6 below).
- **Email invitation with attached plans:** smaller regional GCs, especially first-time-to-BPC GCs from diversity-channel blasts (DFWMSDC, etc.), email a ZIP of plans + an Excel or PDF bid form. Subs return the form by reply email.
- **Open prequal / vendor-list channel:** the GC pre-qualifies a subcontractor pool ahead of any specific project (Procore Network, BuildingConnected ProjectNet, etc.). Once BPC is in the pool, invitations arrive automatically. This is a longer-lead lane and not the focus of this playbook, though prequalification effort is non-zero — flag for Day-3+ posture build.

When you'll see it:

- **Restaurant rollouts** — Darden brands (Longhorn, Olive Garden, LongHorn, Cheddar's), Brinker brands (Chili's, Maggiano's), Inspire Brands (Buffalo Wild Wings, Sonic, Arby's), Yum! Brands (Taco Bell, KFC, Pizza Hut), and the C-store family (7-Eleven, QuikTrip, Buc-ee's where they hire a private GC). National-brand rollouts route through a national GC who shops trades locally.
- **Hotel / hospitality fit-outs** — Marriott / Hilton / IHG flag fit-outs with a brand-standard GC (Hall Park is an existing BPC reference here).
- **Private K-12 + private higher-ed renovation** — DFW private schools (Greenhill, ESD, Hockaday, St. Mark's) and private colleges use a GC-led delivery model that looks like ISD bond work but skips Tex. Educ. Code Ch. 44 entirely.
- **Faith-based / institutional new construction** — temples, mosques, churches, and faith-affiliated facilities (the Hindu Temple of Southlake reference under "Private commercial / institutional negotiated" in `README.md` falls here).
- **Subbing under a CM/GC on a public-funded project** — McLennan Phase 4 CSC Cosmetology is exactly this pattern: MCC is the public owner running a Ch. 2269 CSP, HCS Inc. is one of multiple competing private GCs sourcing subs through DFWMSDC. At BPC's sub tier, the contract is between BPC and HCS — private — even though Davis-Bacon flows down because MCC's funding is public.

When it's a different beast (use a different playbook):

- **BPC as prime to a public owner** — use the matching public playbook ([federal LPTA](federal-sba-rfq-lpta.md), [federal tradeoff](federal-rfp-best-value-tradeoff.md), [TX state CSP](texas-state-csp-hsp.md), [TX municipal CSP](texas-municipal-csp.md)).
- **BPC as prime to a private owner, direct negotiated** — the "Private commercial / institutional negotiated" ad-hoc row in [`README.md`](README.md). No competitive procurement, no portal, no bid form. AIA A101/A201 (or owner's preferred form) governs end-to-end. Not playbook-grade because every owner relationship is bespoke; refer to the existing references (Hindu Temple of Southlake; Holiday Inn / Hall Park; Lavon RV Park).
- **BPC as sub to a public-prime GC on a federal job** — a hybrid case. The prime is private, but its prime contract is federal (FAR, Davis-Bacon, certified payroll, Section 3, EEO). At BPC's sub tier you face **flow-down clauses** from the GC's prime contract that go well beyond what this playbook covers. Treat as this playbook PLUS the matching federal playbook in parallel; the GC's subcontract form will list which FAR clauses flow down (typically the §52.244-6 commercial-item subcontracts flow-down, the DBA prevailing-wage / certified-payroll requirements, EEO clauses, and small-business participation).

## 2. Key differences vs. BPC-as-prime-to-public-owner pursuits

| Dimension | Public-prime pursuit | Private-GC sub-bid pursuit (this playbook) |
|---|---|---|
| **Controlling document** | FAR (federal); Tex. Gov't Code Ch. 2269 / Loc. Gov't Code Ch. 252/262 / Educ. Code Ch. 44 (state/local). Statute is **prescriptive**. | **The GC's prime contract** and the GC's subcontract form. Statute is **default rule only** — most defaults are over-ridden by contract. Read the subcontract before any quote sticks. |
| **Bid opening** | Public opening at the stated time + place; bid tabs are public record. | **No public opening.** The GC takes quotes privately and selects on its own criteria (price, schedule fit, prior relationship, GFE coverage of the GC's MBE goal, payment-terms acceptance). BPC may never see the other subs' numbers. |
| **FOIA / open records** | Bids become public record on opening (federal FOIA; Tex. Pub. Info. Act). Past-bid pricing visible. | **No public-records access.** Past pricing is a closely-held GC asset. Reliance on GC relationship + the sub's own historical-bid log is the only source of "what the market is paying". |
| **Federal/state procurement integrity** | Source-selection-sensitive info rules apply (FAR 3.104; CO-only channel). | No equivalent. The GC may negotiate, share competitor scopes, ask for value-engineering, and re-shop the trade openly. **Standard practice in restaurant + retail rollouts.** Bid the magnitude with that in mind. |
| **MBE / SBE / HUB scoring** | Goal-based scoring with formal GFE binder (state HUB; Dallas/Houston M/WBE). Certificate is a scoring lever. | Certificate is a **door-opener** (DFWMSDC channel; GC's diversity-spend goal) but **not a scoring lever** at the GC level. The GC may report sub-tier diversity to its owner — confirms BPC's certification provides MBE participation credit on the GC's spend report, but does not bump BPC's price evaluation. |
| **Pricing posture** | Carry DBA / TWC prevailing-wage + certified-payroll uplift, bond cost, federal/state insurance limits, full overhead allocation. Bid the magnitude midpoint. | Open-shop labor at **BLS OEWS rate** + standard markup is the default — UNLESS the project is public-funded pass-through (confirm in Step 2). No bond at the sub tier under typical thresholds. Bid the local trade-market rate, then add the GC-portal-specific overhead. |
| **Schedule control** | The agency publishes the schedule and the float. BPC's CPM negotiates from a public baseline. | **The GC controls the schedule and the float.** BPC's pricing reflects the GC's stated milestones; if the GC compresses or delays, BPC's recovery comes through change orders under the **subcontract**, not through agency-side equitable adjustment processes. Schedule risk is asymmetric — the GC owns the calendar. |
| **Dispute resolution venue** | Federal: COFC / boards of contract appeals; state: Texas District Court (TX prompt-payment statute carve-outs). | **The GC sets the venue.** Standard private-GC subcontract forms (AGC 650, ConsensusDocs 750, GC's own form) typically pick the GC's home county for venue + arbitration under AAA Construction Industry Rules. **Read it.** A Texas sub on a Texas project may end up bound to arbitrate in the GC's home state. |
| **Payment terms** | Federal: Prompt Payment Act (5 USC 3902) — agency pays prime in ~30 days; prime pays sub in 7 days after agency payment (FAR 52.232-27). State: Tex. Gov't Code Ch. 2251 — agency pays in 30 days; prime pays sub in 10 days after that. | **Pay-when-paid** and **pay-if-paid** clauses are standard (see §8). Net 30 to net 60+ from GC's receipt of owner payment is typical. Sub cash flow is exposed. |
| **Bid bond requirement** | Federal: yes if > $150K (FAR 28.101-2 / 52.228-1 / SF 24, 20% or $3M cap). State: yes per Tex. Gov't Code Ch. 2253 (5% typical). | **Generally no bid bond at the sub tier.** Some GCs request a sub bid bond on larger trades or on first-time sub relationships; rare under $1M sub-contract value. |
| **P&P bond requirement** | Federal: 100%/100% if > $150K (Miller Act + FAR 52.228-15). State: 100%/100% per Tex. Gov't Code Ch. 2253 (Little Miller Act). | **Usually waived at the sub tier under $1M** subcontract value; GC may request a sub P&P on larger trades (drywall on a $10M project; MEP package; structural steel). Confirm in the invitation; never assume. |
| **Insurance posture** | Federal/state SGC limits (typically $1M GL / $2M aggregate; auto $1M; WC statutory; Umbrella $2M+ on larger). | **GC dictates limits and endorsements.** Typical: GC + project owner named as additional insured (often using ISO **CG 20 10** ongoing-ops + **CG 20 37** completed-ops, NOT the older blanket-AI endorsements); **primary-and-non-contributory** wording; **waiver of subrogation** in favor of GC + owner; Umbrella $2M – $5M; pollution + professional only on trades that handle them. See §9. |
| **Cert of insurance flow** | Submitted with bid; renewed annually to agency. | Submitted **per project** with the subcontract execution; AI endorsements are project-specific and must be requested from BPC's broker for each sub-job. Lag time on broker turnaround can hold up sub-contract execution. |
| **FOIA-able correspondence** | All emails to/from CO are potentially FOIA-able post-due. | All emails between BPC and the GC are **private** — but discoverable in arbitration / litigation if the relationship breaks down. Write every email as if it will be read at deposition (this is good practice on public bids too, but the trigger is different). |

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| Commercial GL current (no expired policy on file) | $1M / $2M minimum; many GCs require $2M / $4M; restaurant chains often $5M umbrella | `[USER TO FILL — pull current COI; on-file policy expired 2024-09-25 per learning log followup]` | 🔴 — blocks every private GC sub-bid from reaching award until renewed |
| Auto liability | $1M combined single limit typical; $2M for hauling | Verify on COI | ⚠️ |
| WC statutory + Employers Liability ≥ $500K/$500K/$500K | TX statutory | Verify on COI | ⚠️ |
| Umbrella | $2M – $5M depending on GC's prime contract flow-down | `[USER TO FILL — confirm current umbrella limit + carrier]` | ⚠️ |
| Additional-insured capability — **CG 20 10** (ongoing) + **CG 20 37** (completed) endorsements on demand | Standard ISO forms; broker should turn around in 24–48 hr | Verify with broker | ⚠️ — confirm broker can issue both endorsements; older blanket-AI endorsement is **not equivalent** under most modern GC subcontracts |
| Primary-and-non-contributory wording available | Standard endorsement (ISO CG 20 01 or carrier equivalent) | Verify | ⚠️ |
| Waiver-of-subrogation endorsement available | Standard | Verify | ⚠️ |
| Bondability letter from surety (in case GC requests sub P&P) | One-line letter naming BPC's single-project + aggregate capacity | $1M floor established; coordinate with surety | ⚠️ |
| TX HUB / MBE / SBE certs (door-openers, not scoring levers at this tier) | At least one current to leverage DFWMSDC + similar diversity channels | All three expired 2024-08-31 per `firm-profile.json` | 🔴 — recertify before next DFWMSDC-sourced pursuit ships |
| OSHA 10 / 30 cards current for site supervision | Yes | Per `firm/firm-profile.json → key_personnel` | ⚠️ |
| Vendor registrations on GC portals BPC will see most often | Yes (see §6) | `[USER TO FILL — BPC's portal presence: BuildingConnected? Procore? BuildBid? iSqFt? PlanGrid?]` | ⚠️ |
| W-9 current calendar year + EIN | Standard | On file | ✅ |
| Capability statement / one-page sub profile for GC's prequal binder | One-pager, brand-clean | `[USER TO FILL — pull from `firm/proposal-library/capability-statement/` when shipped; until then, build per-pursuit]` | ⚠️ |
| References (3 past projects of similar size + scope; owner-side AND GC-side contacts) | 3 minimum, ≤ 5 yrs old | Per `firm/firm-profile.json → past_project_selection_rules` | ✅ — confirm contacts current |

## 4. Required compliance docs (per bid)

Far shorter than a federal or state-prime checklist, but the items are non-negotiable and the timing is tight:

- [ ] **Signed sub bid form** in the GC's required format (varies — see §5)
- [ ] **Scope letter** clearly listing **inclusions + exclusions + clarifications + assumptions** (line-by-line; never let the GC infer scope from an email price)
- [ ] **Current COI** with **GC and project owner named as additional insured**, **primary-and-non-contributory**, **waiver of subrogation** in favor of GC + owner (broker hand-off; allow 24–48 hr)
- [ ] **W-9** current calendar year
- [ ] **TX HUB / MBE / SBE cert** if diversity participation is on the GC's checklist (DFWMSDC channels)
- [ ] **OSHA 10 / 30 roster** if the GC's site-safety plan requires it
- [ ] **Capability statement** (one-pager) if the GC requests a sub prequal package
- [ ] **Bondability letter** from surety (only if GC requests sub P&P; rare under $1M)
- [ ] **References list** (3 past projects, GC-side + owner-side contacts) if the GC requests with the bid
- [ ] **Schedule narrative** (if the GC's portal asks; many do not at bid stage)
- [ ] **Acknowledgment of GC's subcontract form** (only AFTER the GC issues an intent-to-award; reviewing the subcontract pre-bid is asymmetric and most GCs won't share until award is imminent — but **always ask**)

## 5. Standard sub bid forms (varies by GC tier)

The bid-form shape was logged as a recurring pattern in `_learning-log.md` (2026-05-30 DFWMSDC entry, Recurring Patterns §5). Three shapes:

| Shape | Typical GC tier | Example | BPC quote workflow |
|---|---|---|---|
| **GC's roll-up form** ("Owner's Proposal Form" — single lump-sum trade total + alternates + unit prices) | Mid-size regional GC; CM-at-risk delivery on public-funded projects | HCS Inc. on McLennan Phase 4 CSC | Map BPC's takeoff to the GC's line items; do NOT carry hidden allowances in the lump-sum — break out as listed allowances if the form permits |
| **Open-format email quote** (free-form scope letter + price + schedule + clarifications) | Small regional GC; private commercial; first-time-to-BPC GC | Adam's Trade & Services on Camp Maxey Roof; faith-based / institutional one-offs | Use BPC's standard quote-letter template; lead with **inclusions + exclusions + clarifications + assumptions**, then price, then schedule, then qualifications |
| **Portal-uploaded standard form** (GC-portal-managed bid sheet, often pre-coded to GC's cost code structure) | National GC; portal-mature; restaurant + hotel + retail rollouts | Ready Construction on 7-Eleven Celina (BuildingConnected); GC-Belisle on Longhorn Little Elm | Fill the portal form line-by-line; attach BPC's own scope letter as a PDF appendix (do not rely on free-text fields in the portal to carry exclusions — the portal may truncate or filter) |

**Mismatch tax:** if BPC's quote structure doesn't match the GC's expected shape, the GC's estimator has to manually re-map BPC's numbers — slower, error-prone, and a quality signal against BPC. Match the shape.

## 6. Common GC portals BPC encounters

| Portal | URL / login | GC tier and typical use | BPC posture |
|---|---|---|---|
| **Autodesk BuildingConnected** (formerly BuildingConnected ProjectNet) | `https://app.buildingconnected.com/` | National + super-regional GCs. Strong restaurant + retail + hotel rollout footprint. Owner of the largest sub-prequal network in North America. | **Register BPC's vendor profile** — one-time, free for subs. Subs receive invitations automatically once added to a GC's bid list. |
| **BuildBid / Building Bid** | `https://www.buildingbid.com/` | Mid-size regional GCs; growing footprint in TX restaurant + retail rollouts. | Register vendor profile; less common than BuildingConnected. |
| **Procore Bid Board** | `https://app.procore.com/` (GC's project URL) | Large national GCs that have standardized on Procore for project management end-to-end. Sub invitations arrive as Procore project invitations. | BPC creates a Procore account per GC; profile data is GC-scoped, not portable. |
| **PlanGrid (now Autodesk Construction Cloud / Build)** | `https://construction.autodesk.com/` | Older platform; some GCs still issue plans via PlanGrid links even when bid-management is on a different portal. | View-only access for plans; bid submission usually elsewhere. |
| **iSqFt** (ConstructConnect) | `https://www.isqft.com/` | Mid-size regional GCs; common in the South-Central US. ConstructConnect's sub-pre-qual + bid-invitation tool. | Register vendor profile; receive invitations by trade + region. |
| **DemandStar** | `https://network.demandstar.com/` | Mixed public + private; more often a public-procurement portal but some private GCs use it for invitation routing. | Register if a target GC issues here; otherwise skip. |
| **HCS Box** | GC-issued Box folder link (file-share, not a true bid-mgmt portal) | Smaller regional GC or CM-at-risk delivering a public-funded job (e.g., HCS Inc. on McLennan) | Download per invitation; treat as email-channel for bid response. |
| **GC's own password-protected portal** | GC's website, sub portal section (e.g., GC-Belisle on Longhorn Little Elm — `www.bcibelisle.com → Subcontractors → Projects Bidding`, password supplied in DFWMSDC blast) | Small + mid-size GCs running their own bid-management page; common in restaurant rollouts where the GC has a national pipeline | Use the password from the invitation; download all materials; **back up to OneDrive** because GC-owned portals can revoke access without notice |
| **Email-attached ZIP / direct download link** | None — direct file transfer | Small regional GCs; first-time-to-BPC relationships; faith-based / institutional one-offs | Save ZIP + PDFs to OneDrive `bids/<slug>/00-original-drop/`; treat as the canonical drop |

**Convention:** every GC portal BPC's vendor profile is NOT already registered on adds a one-time setup task to the bid's `02-bid-prep-checklist.md` "Portal registration" gate. Deduplicate across bids — register once, reuse forever.

## 7. The 5-step pursue checklist for private-GC sub bids

This is the minimum sequence between "invitation lands" and "quote submitted". Skipping any step is a known failure mode (see §10).

### Step 1 — Get and read the GC's invitation + bid form

- Pull the invitation email or portal notification verbatim. Note the GC's named **estimator contact**, **due date + time + timezone**, **submission channel** (portal vs. email vs. attached form), and the **bid form shape** (see §5).
- Log into the portal (BuildingConnected / BuildBid / Procore / PlanGrid / iSqFt / GC's own portal). Download **everything** — plans, specs, addenda, the GC's bid form, the GC's sub prequal questionnaire (if any), the GC's reference subcontract form (if available pre-bid).
- Stage at `bids/<slug>/00-original-drop/` (or for OneDrive-routed drops, mirror at `C:\Users\...\OneDrive\Blueprint Constructs\<GC>\<slug>\00-original-drop\`).
- If the portal requires an account BPC doesn't have, file an `attachments/_PORTAL_ACCESS.md` `[USER ACTION REQUIRED]` ticket immediately — Cursor agents have no GC-portal credentials and no browser MCP. Time wasted waiting for portal access is the most common bid-window killer.

### Step 2 — Confirm the project's underlying funding source

The single most important question on a private-GC sub bid: **whose money is paying for this project?**

| Funding source | Davis-Bacon? | Buy American? | Certified payroll? | MBE/SBE goals? | This playbook fully owns? |
|---|---|---|---|---|---|
| **Pure private** (owner is private commercial; no public grant; no federal tax-credit pass-through) | No | No | No | Only if GC's owner has internal goals (e.g., Dallas brand owner with corporate-DEI goals — rare) | ✅ Yes |
| **Federal pass-through to a private prime** (e.g., USDA Rural Development grant funding a private project; FEMA Stafford Act funding flowing through a private GC) | Yes (DBRA flow-down) | Sometimes (BABA / Buy American Act sometimes; ARRA / IIJA-era projects more often) | Yes (WH-347 weekly) | Yes if the funding source has explicit goals (HUD Section 3; DOT DBE) | ⚠️ Read this playbook + the matching federal playbook in parallel |
| **State pass-through** (e.g., TX GLO CDBG-MIT grant to a private owner; TX TDHCA tax-credit project) | Yes if > $50K state-funded portion (Tex. Gov't Code Ch. 2258) | No federal Buy American; sometimes state preference (Tex. Gov't Code §2155.4441 if state-agency-financed) | Yes (TWC payroll forms) | Yes if the funding source has explicit goals (TX HUB sometimes; TX HTC compliance period MBE goals sometimes) | ⚠️ Read this playbook + the matching TX state CSP playbook in parallel |
| **Local pass-through** (city / county / ISD pays a private GC to deliver a project on public land — uncommon, but happens in P3 + facility-lease deals) | Per local ordinance + state portion (Ch. 2258) | No federal; varies by city | Varies | Per city M/WBE program (Dallas; Houston) | ⚠️ Read this playbook + the matching TX municipal CSP playbook in parallel |
| **CM-at-risk on a public-prime project** (public owner; CSP-awarded private CM/GC; BPC sub-quoting to the CM) | Yes — all flow-down clauses apply | Per the agency's prime contract | Yes | Per the agency's HUB/HSP/M/WBE program (HSP credit at the sub tier where applicable) | ⚠️ Read this playbook + the matching public playbook in parallel; the public playbook drives flow-down |

**How to confirm:** the GC's invitation may state it directly ("Davis-Bacon applies", "TWC prevailing wage applies", "this is a private commercial project"). When it does not, the **specifications front-end** is the next-best source — look for Section 007343 (Davis-Bacon / prevailing wage) in the Table of Contents; if it exists, public money is flowing somewhere upstream. RFI the GC if the front-end is ambiguous; better to ask than to under-price labor by 15–30%.

### Step 3 — Get scope-of-work clarity from the GC (RFI early)

Sub-bid scope ambiguity is the largest single source of post-award disputes. Sources of ambiguity:

- **GC's scope-of-work narrative is shorter than the spec sections it references.** Restaurant + retail brand standards routinely incorporate brand-spec manuals (Royston, Mapes, Pac-Clad, Jimco, Porter SIPs in the 7-Eleven brand standard noted in `_learning-log.md`) that the GC has not attached to the bid package. RFI the GC for the brand-spec manual; do not assume the standard cut.
- **Drawing-spec conflict.** The plans show one thing; the specs say another. Standard precedence under most subcontracts is "specs over plans" but the GC's prime contract may invert. RFI in writing.
- **Template-carryover boilerplate.** Spec front-ends are copy-paste between projects; the McLennan Cosmetology PM had "netting and artificial turf" language that obviously didn't belong (logged 2026-05-30 (continued)). Quote what's drawn and specced for the **actual** project; flag carryover language as an RFI item; never assume scope from copy-paste.
- **Allowance items not called out.** When the GC carries an allowance and BPC's trade is supposed to deliver a base + allowance line, the GC's bid form usually has a line for it. If it doesn't, ask — quoting "lump-sum, includes all" exposes BPC to take the allowance shortfall.

RFI etiquette on a private GC: **email the named estimator directly, cc the project manager if one is named, use the portal's RFI channel if one exists.** Most private GCs welcome pre-bid RFIs because their estimator wants the trade priced cleanly. Wait until the RFI is answered (or the cutoff passes) before pricing. If the RFI cutoff is too tight, price a defensible interpretation and document the interpretation in the scope letter; flag the carry as an assumption.

### Step 4 — Pricing posture

| Component | % of direct cost (pure-private) | % of direct cost (public-pass-through) | Notes |
|---|---|---|---|
| Direct cost (subs + materials + self-perform labor) | 100% | 100% | |
| Labor base | **BLS OEWS rate** for the trade + county | DBRA WD rate **or** TWC Ch. 2258 county prevailing-wage rate (whichever applies + carry certified-payroll admin time at 2–4% of labor) | Pure-private bids price at OEWS; public-pass-through bids carry the prevailing-wage uplift |
| General conditions / supervision allocation | 5–10% (sub-tier supervision; smaller than prime GC's GC&D) | 5–10% | Sub-tier supervision is light; allocate per actual trade-foreman time |
| Insurance uplift | 2–4% | 3–5% (additional AI endorsements; broker time on per-project COIs) | Higher when GC requires CG 20 10 + CG 20 37 + waiver + P&NC; restaurant-chain projects often demand $5M umbrella |
| Sub bond (if requested) | 0–2% | 0–2% | Rare under $1M; budget if GC's invitation flags it |
| Contingency | 3–6% | 5–8% | Higher on public-pass-through to absorb DBRA enforcement risk |
| Overhead | 8–12% | 8–12% | |
| Profit | 5–10% | 5–8% | Public-pass-through allows less profit headroom because the prime is also squeezed |
| **Total markup over direct** | **~30–45%** (direct-to-bid multiplier of ~1.30–1.45) | **~35–50%** | |

**Don't carry DBRA / TWC overhead on a pure-private project — it prices BPC out of the market on that trade.** Conversely, **don't omit the DBRA / TWC uplift on a public-pass-through project** — it exposes BPC to certified-payroll noncompliance and back-wage liability under the Davis-Bacon Related Acts.

**Quote at full insurance / endorsement uplift.** Private GCs catch under-endorsed competitors at the COI-review stage (which happens AFTER price selection); a sub that can't produce CG 20 10 + CG 20 37 on demand loses the award and the GC re-shops the trade.

### Step 5 — Submit on the GC's portal or by the GC's preferred email — never the owner's portal

This is where private-GC sub bids most commonly fail to be received. Three rules:

1. **Submit to the GC's channel.** If the project is a CM-at-risk job where MCC (or any public owner) is the underlying entity, **do not** route BPC's sub quote to MCC's procurement office — they will not look at it, and they cannot route it to the GC. The GC's named estimator is the channel.
2. **Submit on the right portal.** If the GC invited via BuildingConnected, submit on BuildingConnected; if the GC invited via the GC's own password-protected portal, submit there. Do not switch channels mid-pursuit.
3. **Submit 60+ minutes early.** Portal uploads can fail silently — the file appears to upload but the portal queue doesn't accept it; the GC's estimator never sees the quote. Confirm submission with a screenshot + a follow-up email to the GC's estimator: "Quote submitted at HH:MM via [portal] for [project]. Please confirm receipt."

## 8. Pay-when-paid / pay-if-paid clause checklist

This is the single most consequential subcontract clause for sub cash flow. Texas distinguishes between the two:

- **Pay-when-paid** clauses are **timing modifiers**. They state that the GC will pay the sub *when* the GC is paid by the owner, but the GC remains obligated to pay within a reasonable time even if the owner doesn't pay. Texas courts treat pay-when-paid as enforceable for timing but **not** as a permanent shield against the GC's payment duty.
- **Pay-if-paid** clauses **attempt to be conditions precedent** — the GC pays the sub *only if* the GC is paid, with non-payment by the owner discharging the GC's obligation entirely. Texas courts will enforce a pay-if-paid clause **only when the language is unambiguous and explicit** in conditioning payment on owner payment; ambiguous language is read as pay-when-paid (i.e., timing only).

**Texas prompt-payment context:** Tex. Bus. & Com. Code Ch. 56 (Prompt Payment to Subcontractors and Suppliers) sets the timing default for **private** construction: the GC must pay the sub within **7 days** after the GC receives payment from the owner (subject to limited statutory exceptions for disputed items). [USER TO FILL — verify with counsel that the §56 citation is current; the chapter was restructured in the 2019 legislative session, and the pay-when-paid case law is still developing under the restructured chapter.]

Statutory backstop in addition to Ch. 56:

- **Texas Trust Fund Act (Tex. Prop. Code Ch. 162):** construction payments received by the GC for work performed by the sub are **trust funds** held for the sub's benefit. A GC that diverts trust funds (uses the sub's earned payment to cover the GC's other operating expenses) faces personal liability against the responsible officers. This is the sub's strongest leverage when a GC slow-pays — the GC's CFO is personally exposed.
- **Mechanic's lien rights (Tex. Prop. Code Ch. 53):** subs have lien rights against the project property. Filing deadlines are tight (varies by sub tier; first-tier subs and original contractors have different windows). [USER TO FILL — verify lien-filing windows with counsel; Ch. 53 was restructured in 2021 and the windows changed.]

**Per-bid clause-review checklist** (run this against every GC subcontract before signing):

- [ ] **Is the pay clause pay-when-paid or pay-if-paid?** Quote the clause verbatim.
- [ ] **If pay-if-paid:** is the language unambiguous and explicit ("condition precedent", "shall be a condition precedent", "the sole source of payment shall be funds received from the owner")? If yes, raise it for legal review — accepting an unambiguous pay-if-paid clause shifts owner-credit risk to BPC.
- [ ] **What's the stated payment window?** Default to Ch. 56's 7-day-after-GC-payment timing unless the contract is explicit (most GCs draft to "X days after approval of pay application" which can stretch the window).
- [ ] **What's the retainage?** Standard is 5–10% of each progress payment held until substantial completion; some GCs hold 10% through final completion + warranty.
- [ ] **What triggers final-payment release?** Substantial completion? Final completion? Owner's acceptance? Punchlist closeout? Owner's payment to GC of the final draw?
- [ ] **Are there pay-application-timing requirements?** (Submit by the 25th; processed by the 10th; etc.) Missing the submission window can push payment a full cycle.
- [ ] **What's the dispute / set-off language?** GCs typically reserve broad set-off rights against the sub's payment for back-charges, defective work, schedule damages. Confirm the set-off rights are not unlimited.
- [ ] **What's the venue + dispute-resolution clause?** Often AAA Construction Industry Rules + GC's home county. Note for BPC's risk register.

**Verify with counsel** before signing any subcontract that has a pay-if-paid clause; the language difference between pay-when-paid and pay-if-paid is a material allocation of credit risk and BPC should price the credit risk if it is being asked to absorb it.

## 9. Insurance & bonds checklist (sub tier on a private GC)

Pull this against the GC's invitation requirements and BPC's current COI **before** the bid sticks. Broker turnaround on AI endorsements is 24–48 hr; allow time.

### Coverage limits (typical GC minimums)

| Line | Typical GC minimum | Restaurant-chain / national-brand minimum | BPC posture |
|---|---|---|---|
| Commercial GL (per occurrence / aggregate) | $1M / $2M | $1M / $2M + Umbrella $5M | `[USER TO FILL — current policy; renewal status]` |
| Commercial GL (products-completed operations) | $2M | $2M – $5M | Verify on COI |
| Auto liability (combined single limit) | $1M | $1M – $2M | Verify |
| Workers' Comp + Employers' Liability | TX statutory + $500K/$500K/$500K | Same | Verify |
| Umbrella / Excess | $2M | $5M ($10M on some hotel-brand jobs) | `[USER TO FILL]` |
| Pollution liability | Trade-dependent (painters; flooring; roofing; demolition) | Same | Only if BPC's trade triggers |
| Professional liability | Trade-dependent (design-assist; design-build) | Same | Only if BPC's trade triggers |
| Builder's Risk | **The GC or owner carries Builder's Risk, not the sub.** Confirm in the subcontract that BPC is named as an additional insured on the BR policy with waiver of subrogation. | Same | Verify in subcontract |

### Required endorsements

- [ ] **Additional Insured — Ongoing Operations** (ISO **CG 20 10 04 13** or equivalent) naming the **GC AND the project owner** (and the owner's lender / architect / CM if the GC's contract requires)
- [ ] **Additional Insured — Completed Operations** (ISO **CG 20 37 04 13** or equivalent) same named additional insureds — completed-ops AI is **separately required** under most modern GC subcontracts; the older blanket CG 20 33 or CG 20 38 endorsements are not equivalent on completed-ops
- [ ] **Primary and Non-Contributory** (ISO **CG 20 01 04 13** or equivalent) — BPC's policy responds first; GC's / owner's policies are excess
- [ ] **Waiver of Subrogation** in favor of the GC + owner (per the subcontract's named parties)
- [ ] **Per-Project Aggregate** endorsement if BPC's GL aggregate is shared across multiple projects
- [ ] **Notice of Cancellation** — 30-day notice to GC + owner of cancellation or non-renewal

### Bonds

- [ ] **Bid bond at the sub tier** — typically **not required** below $1M sub-contract value; some restaurant + retail GCs request a sub bid bond on first-time relationships even at lower values. Confirm in invitation.
- [ ] **Performance bond at the sub tier** — typically **not required** below $1M; mid-size GCs often require sub P&P on MEP packages and structural-steel packages above $500K regardless of trade.
- [ ] **Payment bond at the sub tier** — paired with performance bond when required; same threshold.
- [ ] **Bondability letter from BPC's surety** — one-line letter naming BPC's single-project + aggregate capacity; useful as a sub prequal artifact even when no actual bond is requested.

### COI deliverable timeline

- Bid stage: a **sample COI** showing BPC's current limits is enough; AI endorsements not yet issued
- Subcontract-execution stage (post-intent-to-award): **project-specific COI** with the GC + owner named as AI + waiver + P&NC, plus the GL + WC + auto certificate, delivered to the GC before subcontract execution. Allow 24–48 hr from BPC's request to broker turnaround.
- Renewal during the project: BPC's broker auto-renews; BPC issues an updated COI to the GC within 10 business days of renewal.

## 10. Risk register — top 5 risks specific to subbing on a private GC

| # | Risk | Impact | Probability | Mitigation |
|---|---|---|:---:|---|
| 1 | **Pay-if-paid clause that BPC signed without review shifts owner-credit risk to BPC.** Owner stops paying GC → GC stops paying BPC → BPC's earned work is unpaid for the duration of the dispute. | HIGH ($) | MEDIUM | Run §8 clause-review checklist before subcontract execution; price credit risk if pay-if-paid is unambiguous; preserve Trust Fund Act + lien rights as leverage. |
| 2 | **Scope ambiguity at bid stage → post-award change-order dispute.** GC's invitation under-spec'd the brand-standard package; BPC priced base-spec; GC expects brand-spec at no change. | HIGH ($ + relationship) | HIGH | RFI early (Step 3); document inclusions + exclusions + clarifications + assumptions in the scope letter; never quote "lump-sum, includes all"; carry brand-spec callouts explicitly. |
| 3 | **Schedule compression with no schedule float relief.** GC overpromised the owner on the master schedule; trades are squeezed; BPC's productivity loss is absorbed under "subcontractor responsibility for schedule" language. | HIGH ($) | MEDIUM | Negotiate the schedule clause at subcontract execution; preserve change-order rights for owner-caused or GC-caused delays; document daily delays in writing (email log). |
| 4 | **AI endorsement mismatch at COI-review stage costs BPC the award.** GC requires CG 20 10 + CG 20 37 + P&NC + waiver; BPC's broker can produce ongoing-ops AI but not completed-ops on the older blanket endorsement. GC re-shops the trade. | HIGH (lost award) | MEDIUM | Verify broker capability **before** quoting; standardize on modern ISO endorsements; pre-issue a sample COI to use with the bid. |
| 5 | **First-time-to-BPC GC walks away from the relationship after the first slow-pay dispute.** BPC is new to the GC's prequal list; BPC files a lien or invokes the Trust Fund Act; GC blacklists BPC from future work. | MEDIUM (channel) | LOW–MEDIUM | Escalate slow-pay disputes carefully — phone before email, email before letter, letter before lien; document the GC's payment history; differentiate "GC has cash flow problem" (lien) from "owner has cash flow problem" (Trust Fund Act + lien); never let a $5K back-charge dispute escalate to a $50K lien filing without a financial-judgment business case. |

## 11. Reusable language blocks (Day-3+ build targets)

These will be added to [`firm/proposal-library/`](../proposal-library/README.md) as BPC ships its first private-GC sub bids:

| Block | Where it will live | When to use |
|---|---|---|
| Sub scope letter — inclusions + exclusions + clarifications + assumptions template | `firm/proposal-library/sub-bid/scope-letter-template.md` *(TODO — Day-3 priority, highest reuse value)* | Attach to every private-GC sub bid |
| Sub bid cover-email template | `firm/proposal-library/sub-bid/cover-email.md` *(TODO)* | Body of the submission email to the GC's estimator |
| Sub COI-request template to broker | `firm/proposal-library/sub-bid/coi-request-to-broker.md` *(TODO)* | Hand-off to BPC's insurance broker with the GC's required endorsement list pre-filled |
| Subcontract clause-review checklist (pay-when-paid / pay-if-paid / venue / set-off / retainage / schedule) | `firm/proposal-library/sub-bid/subcontract-clause-checklist.md` *(TODO)* | Run before signing every GC subcontract |
| Diversity-cert door-opener language (DFWMSDC channel) | `firm/proposal-library/sub-bid/diversity-channel-positioning.md` *(TODO — pairs with the firm-side action to recertify MBE / SBE / HUB)* | Cover-email + scope letter when the invitation came via DFWMSDC or similar diversity-channel blast |
| Restaurant + retail brand-standard scope clarification language | `firm/proposal-library/sub-bid/brand-standard-clarifications.md` *(TODO — populates from Longhorn + 7-Eleven + future rollouts)* | Restaurant + retail fit-out scopes where the GC's invitation references a brand-spec manual |

Until these are authored, paste the closest equivalent block from [`firm/proposal-library/`](../proposal-library/README.md) and adapt.

## 12. Live applications of this playbook

| Bid workspace | GC | Status | Why this playbook applies |
|---|---|---|---|
| [`bids/_WATCHLIST/longhorn-little-elm-bcibelisle.md`](../../bids/_WATCHLIST/longhorn-little-elm-bcibelisle.md) | GC-Belisle (national restaurant-rollout GC, anonymized handle per task brief; folder retains literal name) | **Watchlist — portal access pending; convert to pursue within 48 hr if scope confirms** | Pure-private restaurant fit-out; GC-portal-managed (GC's own password-protected portal); BPC's home-town geographic match (Little Elm); first BCI-Belisle-to-BPC relationship |
| [`bids/mcc-cosmetology-phase4-2026-0622/`](../../bids/mcc-cosmetology-phase4-2026-0622/) | HCS Inc. | Pursue scaffold | Public-pass-through (MCC is the public owner running a Ch. 2269 CSP; HCS is the private CM/GC); Davis-Bacon flows down; sub-quote via DFWMSDC channel; bid form is HCS's roll-up "Owner's Proposal Form" |
| [`bids/7eleven-celina-2026-0605/`](../../bids/7eleven-celina-2026-0605/) | Ready Construction | Pursue scaffold | Pure-private C-store ground-up; portal-uploaded standard form on BuildingConnected; brand-standard spec manual (Royston, Mapes, Pac-Clad, Jimco, Porter SIPs) requires RFI to source |
| [`bids/tmd-camp-maxey-roof-2026-0626/`](../../bids/tmd-camp-maxey-roof-2026-0626/) | Adam's Trade & Services | Pursue scaffold | Public-pass-through (TMD is the public owner; Adam's Trade is the private prime/GC); Davis-Bacon + Buy American Act both flow down; open-format email quote channel |

## 13. Cross-references

- **Public-prime playbooks (sibling families on the opposite side of the prime/sub divide):** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md), [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md), [`federal-simplified-acquisition-best-value.md`](federal-simplified-acquisition-best-value.md), [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md), [`texas-municipal-csp.md`](texas-municipal-csp.md)
- **Pricing-data sources (sub-tier pricing builds against the same data stack as prime-tier):** [`pricing-data-sources.md`](pricing-data-sources.md)
- **Workspace template:** *to be created — clone `bids/_TEMPLATES/texas-state-csp-hsp/`, strip public-procurement-code references, swap in GC-portal mechanics and sub-tier insurance addenda*
- **Compliance registry (the Day-1 sweep for every sub bid):** [`firm/compliance/README.md`](../compliance/README.md)
- **Capability statement (sub prequal artifact):** [`firm/proposal-library/capability-statement/`](../proposal-library/capability-statement/) when shipped
- **Learning log (running list of triggers that motivated this playbook + future reinforcements):** [`_learning-log.md`](_learning-log.md)

---

**Update this playbook the next time we hit a sub-on-private-GC pursuit.** Every new GC + every new portal + every new subcontract clause variation is a chance to tighten this playbook. The §10 risk register and the §8 pay-clause checklist in particular will mature as BPC ships more sub-bids; replace `[USER TO FILL — verify with counsel]` placeholders with concrete legal-review outputs as they become available.
