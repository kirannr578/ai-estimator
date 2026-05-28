# Playbook — Federal Job-Order Contract (JOC) Task Order

> **Exemplar bid:** *not yet exemplified by a shipped BPC bid.* BPC is not currently pre-qualified into any federal JOC pool — that's the first action item in this playbook.
>
> **Matching workspace template:** *to be created once BPC is pre-qualified into a JOC vehicle — until then, BPC cannot compete on JOC task orders.*

## 1. Procurement description

A **Job-Order Contract (JOC)** is a Federal IDIQ (Indefinite Delivery, Indefinite Quantity) vehicle pre-priced via a **Unit Price Book (UPB)** for facility renovation, repair, alteration, modernization, and minor new construction. JOCs were created in the 1980s by USACE; the model has since been adopted by GSA, NAVFAC, VA, NASA, DOD agencies, and many federal and state agencies.

The defining JOC mechanics:

- **The base contract is pre-bid** via a competitive procurement that establishes a multi-year IDIQ ceiling (often $20M–$500M, 5-year term with options), a Unit Price Book (typically RSMeans-derived or Gordian-derived), and a **coefficient** (multiplier) the prime applies to UPB unit prices to capture its overhead, profit, and area-cost adjustment
- **Individual projects ("task orders" or "delivery orders") are issued under the IDIQ** as the need arises, typically 30 days from scope-finalization to NTP
- **Pricing of a task order = sum of (UPB line item × quantity × coefficient)** — no separate competitive pricing per task; the coefficient was locked at IDIQ award
- **No per-task bid bond**; payment bond required at task-order level if task value > $35K (USACE) or > $150K (GSA)
- **Typical task sizes:** $25K – $2M per task; some JOCs allow up to $5M
- **Typical IDIQ term:** 1-year base + 4 option years (5 years total); some go longer

When you'll see it:

- USACE Districts (Fort Worth, Galveston, Tulsa, New Orleans, all others) issue JOC IDIQs every 2–5 years
- GSA Federal Acquisition Service has JOC IDIQs covering federal buildings nationwide
- VA Medical Centers — VA JOC programs for hospital renovation
- NAVFAC + DOD installations (Camp Mabry, Fort Hood, Lackland AFB, NAS JRB Fort Worth, etc.)
- NASA centers
- Federal Bureau of Prisons facilities
- USFWS regional offices for cyclical refuge maintenance

When it's a different beast (use a different playbook):

- **LPTA RFQ / RFP** — for one-off construction projects not covered by a JOC vehicle. Use [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md).
- **Best-value tradeoff RFP** — for one-off projects > $500K with tradeoff scoring. Use [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md).
- **The JOC IDIQ itself** (the upstream contract that establishes the UPB + coefficient + small-business pool) — this is a separate competition with its own complex playbook; this file covers the **task-order** phase only (downstream of pre-qualification into a JOC IDIQ pool).
- **State JOC** (TFC JOC, TAMU System JOC) — same mechanics but different procurement code + UPB source. This file is federal-only; a TX JOC variant should be authored separately if BPC ever pre-qualifies into one.

## 2. Pre-qualification — the gate before you can play

**BPC is not currently pre-qualified into any federal JOC IDIQ pool.** Without pre-qualification, BPC cannot bid task orders — task orders are competed (or directly assigned) only among the small-business contractors already on the IDIQ.

The pre-qualification gate: **win a JOC IDIQ.** The IDIQ competition uses the same FAR Part 15 tradeoff mechanics covered in [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md), with additional JOC-specific criteria:

| Factor | What the agency evaluates |
|---|---|
| **Coefficient bid** | The multiplier the firm applies to UPB unit prices. Lower coefficient = lower priced task orders; competitively bid at IDIQ award |
| **JOC technical experience** | Prior JOC IDIQ wins; demonstrated UPB-pricing capability; estimating staff trained on RSMeans / Gordian |
| **Subcontractor management plan** | JOC primes coordinate many small task orders simultaneously; the agency wants confidence the prime can run multiple subs concurrently |
| **Past performance on similar IDIQs** | CPARS on prior IDIQ task orders; firm-level past-performance on renovation work matching the JOC scope |
| **Small business participation** | Most JOC IDIQs are 100% small-business set-asides or have small-business subcontracting goals |
| **Bonding capacity** | Single-task limit + aggregate IDIQ ceiling exposure; surety must commit to the IDIQ-aggregate level (often $2M–$10M aggregate even for small-business JOCs) |
| **Geographic coverage** | Agencies prefer locally-headquartered firms for fast task-order response; some JOCs require an office within 50 miles of the issuing installation |

**Day-3+ action item:** research USACE Fort Worth + Galveston District JOC pre-qualification cycles + GSA JOC schedule entry. Pre-qualifying takes 6–18 months from RFP release to IDIQ award; BPC should start the pipeline now even if no immediate task-order revenue is expected.

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| Pre-qualified into ≥ 1 federal JOC IDIQ pool | Yes (gate to playing) | **No** | 🔴 — **#1 action item before any task-order pursuit** |
| RSMeans CostWorks subscription OR Gordian eGordian access | Yes (UPB pricing capability) | `[USER TO FILL — confirm if BPC has either subscription]` | 🔴 — required to even read a UPB; ~$3K-$8K/yr |
| Estimator trained on UPB pricing (RSMeans or Gordian) | Yes | `[USER TO FILL — Rocky / future estimator]` | 🔴 — 1-day Gordian course or RSMeans webinar |
| Coefficient pricing strategy / business case | Yes (Coefficient = 1.20 to 1.45 typical for small-business JOC primes) | `[USER TO FILL — model coefficient against BPC overhead + profit assumptions]` | 🔴 — Day-3+ |
| Bond capacity at IDIQ-aggregate level ($2M–$10M depending on JOC) | Single-project + aggregate | $1M floor; needs to climb for $5M+ aggregate JOC | ⚠️ — coordinate with surety |
| Office within 50 miles of intended installation (USACE Fort Worth District, NAS JRB Fort Worth, Fort Hood, etc.) | Yes for Fort Worth District (Frisco is ~35 miles from FW HQ) | ✅ for Fort Worth; ⚠️ for Galveston, Tulsa | ✅ Fort Worth |
| Section 889 + FAR 52.204-29 + Section 8(a) joint-venture (if relevant) reps | Current | Per LPTA baseline | ⚠️ |
| All LPTA-baseline compliance (SAM, Reps & Certs, COIs, Buy American, DBA readiness, etc.) | Current | See [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md) §3 | ⚠️ |

## 4. Unit Price Book (UPB) mechanics

| UPB source | Used by | Notes |
|---|---|---|
| **RSMeans** (Gordian's RSMeans Data Online / CostWorks) | Many federal JOCs (GSA, some USACE) | Industry-standard cost database; the JOC IDIQ specifies which RSMeans year + city-cost-index region applies |
| **Gordian eGordian / EZIQC** | Most modern JOC programs | Gordian's proprietary UPB + estimating platform; agency-licensed |
| **Custom agency UPB** | Some VA + DOD JOCs | Agency builds a UPB from internal historical pricing; harder to estimate against without prior task-order experience |

**UPB pricing workflow:**

1. **Receive task order scope** from the agency (typically a 1-page work-request + drawings if applicable)
2. **Decompose scope into UPB line items** (e.g. "remove existing 6-ft chain link fence" = UPB line `02-41-19-1234`, quantity 240 LF)
3. **Pull UPB unit prices** from the JOC's UPB version (e.g. RSMeans 2024)
4. **Apply the coefficient** (e.g. 1.32) to each unit price: `effective unit price = UPB unit price × coefficient × city-cost-index`
5. **Apply Non-PrePriced (NPP) coefficient** for any scope NOT in the UPB (custom items priced at cost + fixed NPP coefficient, typically 1.05–1.15)
6. **Apply Special Coefficients** as the JOC IDIQ allows:
   - **Overtime coefficient** for weekend / after-hours work (e.g. 1.30 for OT, 1.50 for double-time)
   - **Design coefficient** for design-build task orders (e.g. 1.06 for design effort included)
   - **NPP coefficient** for items not in UPB
7. **Total task-order price** = sum of (UPB line × qty × coefficient × city-cost-index) + (NPP items × NPP coefficient)
8. **Submit task-order proposal** — typically a 2–10 page document with the line-item rollup + assumptions + clarifications + schedule

**Pricing speed matters:** task-order proposals are often required within **5–15 calendar days** of scope release. Estimating speed is a competitive advantage.

## 5. Task-order workflow (post-pre-qual)

| Step | Owner | Days from scope release |
|---|---|---|
| Scope released by agency | CO | T-0 |
| Pre-task scoping meeting (PTSM) at site | Prime + agency + sub if known | T+2 to T+5 |
| Task-order proposal due | Prime | T+5 to T+15 |
| **Joint Task Order Review (JTOR)** — prime + agency walk every line | Prime + agency | T+7 to T+20 |
| Negotiated adjustments to UPB lines + quantities + assumptions | Prime + agency | T+10 to T+25 |
| Task order awarded | Agency | T+15 to T+30 |
| NTP | Within 10 days of award | T+25 to T+40 |
| Performance period | Per task scope | Typically 30–180 calendar days |
| Substantial completion + closeout | Prime | Per task |
| Final invoice + final-payment processing | Prime | Per task |

**Multiple task orders run concurrently** under a JOC IDIQ. A pre-qualified prime might have 3–10 active task orders at any time; coordination overhead is the dominant JOC management cost.

## 6. Submission portals

JOC task-order submissions don't go through SAM.gov (the IDIQ is on SAM, not individual task orders). Instead:

- **Agency-specific task-order portal** (USACE has its own; GSA has eGordian; NAVFAC has its own)
- **Email to assigned CO + Contract Specialist + Project Engineer**
- **In-person at JTOR meeting** for negotiated adjustments

## 7. Submission format conventions

| Convention | JOC task-order norm |
|---|---|
| Format | Typically Gordian eGordian export OR Excel rollup OR PDF proposal narrative |
| Content | Line-item rollup; coefficient applied; assumptions; clarifications; proposed schedule; key personnel for this task |
| Length | 2–10 pages typical; longer only for complex task orders |
| Wet ink vs e-signature | E-signature acceptable |
| Acceptance period | 30 cal days typical |
| Late submission | Generally rejected; some JOCs allow re-submittal but lose pricing-evaluation priority |

## 8. Common pitfalls

1. **Wrong UPB version.** JOC IDIQs lock the UPB version at award (e.g. RSMeans 2024). Using a newer / older RSMeans creates a non-conforming proposal that the agency must reject.
2. **Coefficient miscalculated on overhead.** The coefficient must cover prime's overhead + profit + bond + insurance. Underbidding the coefficient at IDIQ award means losing money on every task for 5 years. Conservative coefficient (1.30–1.40) on a small-business JOC is typical.
3. **Non-PrePriced (NPP) items mis-categorized.** If a UPB line exists for the work and the prime prices it as NPP (at higher coefficient), the agency rejects. If no UPB line exists and the prime forces a UPB line to fit, agency catches it at JTOR. Read the UPB carefully.
4. **PTSM no-show.** Pre-task scoping meetings are where 80% of task-order assumption-clarification happens. Missing PTSM forces wider assumptions at proposal time, which lose at JTOR negotiation.
5. **Scope creep absorbed.** Task orders are firm-fixed-price; if the scope grows after award, the prime eats the cost unless a Modification (SF 30 amendment) is processed. Document every assumption + clarification in the task-order proposal and never start work on a scope element that wasn't in the proposal.
6. **Concurrent task-order overcommitment.** Multiple active task orders under one IDIQ stress prime's PM bandwidth. JOC veterans cap themselves at ~5 concurrent active tasks per PM to avoid quality + schedule slippage.
7. **Subs not pre-qualified on the JOC.** Some JOCs require sub flow-down of pre-qualification — using an unqualified sub voids the task order. Confirm sub eligibility at PTSM.
8. **Coefficient unbalancing across task types.** A prime that bids a low base coefficient + a high NPP coefficient at IDIQ award will win the IDIQ but suffer if all tasks turn out to be UPB-coded (no NPP windfall). Model the coefficient mix against the expected task mix.
9. **Payment bond missed at task-order level.** Tasks > $35K (USACE) or > $150K (GSA) require a payment bond at the task-order level. Coordinate with surety pre-bid.
10. **CPARS scoring on JOC tasks is per-task** — strong individual task performance builds a CPARS portfolio that helps win the next IDIQ recompete. Treat each task as if it's the make-or-break for the next pre-qualification.

## 9. Coefficient bidding strategy (at IDIQ pre-qualification)

When BPC bids the upstream JOC IDIQ (i.e. competes for the right to play), the **coefficient bid is the dominant pricing factor**. Strategy:

| Coefficient component | Notes |
|---|---|
| Base coefficient | Direct cost recovery from the UPB. Modal range 1.10–1.40 for small-business JOCs; 1.05–1.25 for large JOCs with more competition. Includes overhead + profit + bond + insurance + city-cost-index adjustment. |
| NPP (non-prepriced) coefficient | 1.05–1.15 typical. Higher coefficient means more profit on custom items but less competitive on tasks with many NPP scopes. |
| OT/weekend coefficient | 1.30–1.50 for OT, 1.50–1.80 for double-time. Some JOCs lock at 1.30/1.50; others allow prime to bid. |
| Design coefficient | 1.05–1.10 if design-build tasks are anticipated. Some JOCs separate design tasks from construction tasks. |

**Coefficient bid optimization** (Day-3+ analysis when BPC pursues IDIQ pre-qual): model expected task mix (UPB vs NPP) and bid the coefficient mix that maximizes expected revenue against expected pricing competition.

## 10. Common JOC IDIQ pre-qual playbook (when BPC eventually competes for IDIQ entry)

| Item | BPC posture |
|---|---|
| Technical proposal (Volume II) | Demonstrate JOC-management experience (use Lavon RV Park + Hindu Temple as proxy IDIQ-management examples until real JOC CPARS exist); subcontractor management plan; estimating capability with RSMeans/Gordian |
| Past Performance (Volume III) | 3 examples; PPQs sent; CPARS where applicable |
| Key Personnel (Volume IV) | PM with JOC IDIQ experience (currently a gap — would need to hire or sub-contract a JOC-experienced PM for the IDIQ pursuit) |
| Coefficient (Volume I — Price) | Modeled per §9 above |
| Small-business participation | Per the IDIQ set-aside |
| Bonding | Surety capacity letter at IDIQ-aggregate level |

## 11. Reusable language blocks (Day-3+ build targets)

| Block | Where it will live | When to use |
|---|---|---|
| JOC IDIQ pre-qualification proposal volume skeleton | `firm/proposal-library/federal-volumes/joc-idiq-pre-qual.md` *(TODO — only if BPC pursues IDIQ pre-qual)* | IDIQ pre-qualification |
| JOC task-order proposal template | `firm/proposal-library/federal-volumes/joc-task-order-proposal.md` *(TODO — only after IDIQ pre-qual)* | Per task order |
| UPB pricing rollup spreadsheet | `core/pricing/joc_upb_rollup.xlsx` *(TODO — only after IDIQ pre-qual + UPB licensed)* | Per task order |
| Coefficient modeling spreadsheet | `core/pricing/joc_coefficient_model.xlsx` *(TODO — Day-3+ if BPC pursues IDIQ)* | Pre-IDIQ bid prep |

## 12. Cross-references

- **Federal LPTA + tradeoff playbooks (sibling federal procurement types):** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md), [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md)
- **Pre-solicitation watchlist (track upcoming JOC IDIQ recompetes):** [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md)
- **State CSP / municipal CSP (sibling procurement families — not JOC but useful context):** [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md), [`texas-municipal-csp.md`](texas-municipal-csp.md)
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **Workspace template:** *not yet created — will be authored after BPC's first IDIQ pre-qual is in progress*
- **USACE JOC pre-qualification information:** Each USACE District's contracting office posts JOC IDIQ RFPs on SAM.gov when recompetes are due; Fort Worth District is BPC's nearest
- **GSA JOC schedule information:** `https://www.gsa.gov/real-estate/real-estate-services/leasing-overview/job-order-contracting`
- **Day-3+ action item to file:** *Research current USACE Fort Worth + Galveston Districts' active JOC IDIQ pools; identify recompete cycles; identify next pre-qualification window for BPC entry.*

## 13. Status: BPC posture summary

BPC is currently **not pre-qualified into any federal JOC IDIQ pool.** This playbook serves three purposes today:

1. **Documenting JOC mechanics** so BPC's estimating + PM staff understand the procurement type when one surfaces
2. **Capturing the pre-qualification action item** as a Day-3+ research and pursuit
3. **Pre-positioning** so when a JOC IDIQ recompete is announced (typically 6–12 months ahead via pre-solicitation notice), BPC can engage immediately via the watchlist + sources-sought process

**[ACTION ITEM]** — research USACE JOC pre-qual + GSA JOC schedule entry pathways within the next 30 days; add findings to this playbook §2 + §3.
