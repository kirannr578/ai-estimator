# Template — `federal-simplified-acquisition-best-value/`

Workspace skeleton for federal **Simplified Acquisition (FAR Part 13, often + Part 12 commercial-item)** RFQs evaluated as **best-value comparative trade-off** across price + technical capability + prior experience.

> **Playbook:** [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../../firm/playbooks/federal-simplified-acquisition-best-value.md)
> **First dogfood bid:** [`bids/pais-cabin-140P6026Q0029/`](../../pais-cabin-140P6026Q0029/) (NPS, Padre Island National Seashore, Backcountry Cabin Roof Repairs)

## When to use this template (vs. the other two federal templates)

The three federal templates sit on a continuum from **most rigid (LPTA)** to **most narrative-heavy (FAR Part 15 best-value tradeoff)**. This template fills the gap in the middle.

| Signal in the RFP/RFQ | `federal-sba-rfq-lpta/` | **`federal-simplified-acquisition-best-value/`** (this template) | `federal-rfp-best-value-tradeoff/` *(to be created)* |
|---|---|---|---|
| Form on cover | SF-1442 | **SF-18** (or SF-1449 for commercial-item under FAR 13.500) | SF-1442 |
| FAR Part cited | Part 14 / 15 | **Part 13 (often + Part 12)** | Part 15 |
| Section M language | "Lowest price among technically acceptable" / Pass/Fail factors | **"Best value" + factors evaluated comparatively, often "in groups of 3 lowest priced"** | "Trade-off" + factors weighted (e.g. "significantly more important than price") |
| Source-selection apparatus | None named (CO awards) | **None named — CO + CS evaluate; no SSP / SSA / SSDD** | Named: SSP, SSA designated, SSDD will be issued |
| Volume structure | Volume I (Price) + Volume II (Technical/Past Perf) | **No formal volumes — single combined PDF "QUOTE PACKAGE"** with 4 sections | Volume I (Price) + II (Technical) + III (Past Perf) + IV (Mgmt/Key Personnel) |
| Page-limit norms | 3–5 pp Volume II | **5–15 pp technical narrative + ½-page-per-ref experience blocks + ½-page-per-role key personnel** | 25–50 pp Volume II + 15 pp Past Perf + 10 pp Mgmt |
| Past-performance count | 2 (per FAR M.1.4.B.f common pattern) | **3–5 prior-experience refs** (Section L states the count) | 3+ examples per Section L, with CPARS + PPQs |
| Bid bond at submission? | Yes (FAR 52.228-1, SF 24) | **Typically no** — FAR 52.228-13 Alternative Payment Protections or no bond clause | Yes |
| RFQ-to-award cycle | 45–90 days | **14–30 days from RFQ release to quote due** | 90–180 days |
| Typical contract value | sub-$500K | **$50K – $250K (civilian SAT); up to $7.5M commercial-item SAT** | $500K – $10M |
| Technical narrative discipline | "Shortest defensible Volume II Passes" — minimize | **REQUIRED 5–15 pp** — under-investing loses bids | Maximize within page limit — narrative is the differentiator |
| Profit posture | 3–6% (LPTA-thin) | **5–8%** (best-value comparative gives some room) | 6–10% |
| Direct-to-bid multiplier | 1.25–1.40 | **1.30–1.45** | 1.35–1.55 |

### Decision rules (use this template when…)

- The cover page says "Request for **Quotation**" + SF-18 + cites FAR Part 13 → **this template**
- The cover page says "Request for **Quotation**" + SF-1449 + cites FAR Part 12 + Part 13 → **this template** (commercial-item SAP variant)
- The cover page says "Request for **Proposal**" + SF-1442 + cites FAR Part 15 → **NOT this template** — use [`../federal-sba-rfq-lpta/`](../federal-sba-rfq-lpta/) (if LPTA) or the FAR 15 best-value template once created
- Section M (or SAP-equivalent "Basis for Award") says "comparative trade-off" or "groups of 3 lowest priced" → **this template**
- Section M says "lowest price among technically acceptable" → **NOT this template** — use [`../federal-sba-rfq-lpta/`](../federal-sba-rfq-lpta/)
- Section M says "trade-off" with explicit factor weighting like "significantly more important than price" → **NOT this template** — use the full FAR 15 best-value template (when created)

If unsure, walk through the decision matrix in [`firm/playbooks/federal-simplified-acquisition-best-value.md`](../../../firm/playbooks/federal-simplified-acquisition-best-value.md) §1 before sinking estimator hours.

## How to instantiate

```powershell
$src = "bids\_TEMPLATES\federal-simplified-acquisition-best-value"
$slug = "<new-slug>"   # e.g. "nps-pais-cabin-140P6026Q0029"
Copy-Item -Path $src -Destination "bids\$slug" -Recurse
```

Then follow the standard steps in [`bids/_TEMPLATES/README.md`](../README.md) (global search-and-replace, `apply_firm_profile.py`, `scan_placeholders.py`, scope-template + proposal-library content, compliance posture confirmation).

## File layout

```
federal-simplified-acquisition-best-value/
  TEMPLATE_README.md              ← this file (decision matrix + usage)
  00-overview.md                  ← solicitation identity + contacts + submission + bid posture
  01-scope.md                     ← SOW-side scope-of-work (feeds technical narrative)
  02-deliverables.md              ← single quote package deliverables (NOT multi-volume)
  03-missing-documents.md         ← document inventory + RFI candidates + form-and-procurement disambiguation (§0)
  04-checklist.md                 ← SAP-specific bid-prep checklist (compressed 20-day cycle)
  05-bid-form-prep.md             ← SF-18 (default) + SF-1449 (commercial-item) field maps; bid-bond verification
  06-scope-outline.md             ← Internal SOW→CLIN→Sub mapping; feeds technical narrative
  07-risk-register.md             ← Bid + execution risk register; SAP-specific risks B12-B15
  08-far-clauses-flags.md         ← FAR clause map; 52.213 + 52.212 series; clauses NOT typical on SAP
  08-pricing-strategy.md          ← Markup recipe + "groups of 3" pricing posture
  09-proposal-draft.md            ← Single quote package draft: 4 sections (technical narrative, key personnel, prior experience, price summary)
  contacts.md                     ← Agency + BPC + sub contacts
  timeline.md                     ← Compressed SAP-cycle bid-prep timeline (Due-20 to Due)
  takeoff-template.json           ← Takeoff JSON schema (SAP-tuned markup defaults)
  price-sheet-skeleton.json       ← Price-sheet JSON schema (priced options + alt-payment compliance attestations)
  outreach/
    email-template.md             ← Site-visit RSVP / RFI / quote submission / sub solicitation drafts
```

## Key differences from `federal-sba-rfq-lpta/` (sibling template)

When this template was extracted from `federal-sba-rfq-lpta/` (the PAIS dogfood) the following template-archetype changes were made:

1. **Source playbook cross-references** changed from `federal-sba-rfq-lpta.md` to `federal-simplified-acquisition-best-value.md` throughout
2. **SF-1442 → SF-18** (or SF-1449) on the bid form (05-bid-form-prep.md); SF-1442 noted as wrong for SAP
3. **"LPTA" → "comparative trade-off"** in evaluation method placeholders; "groups of 3 lowest priced" call-outs added
4. **Technical narrative REQUIRED** (09-proposal-draft.md restructured to 4 sections — technical narrative, key personnel, prior experience, price summary — NOT the 2-volume LPTA structure)
5. **3–5 prior-experience refs** (vs. LPTA's typical 2) with the count parameterized per RFQ Section L
6. **Bid bond often absent at submission** — 05-bid-form-prep.md and 08-far-clauses-flags.md call out FAR 52.228-13 Alternative Payment Protections as the typical SAP alternative
7. **Magnitude often unstated** — 00-overview.md accepts "magnitude unstated; sub-SAT cap = $250K civilian / $7.5M commercial-item" as a valid value
8. **Form-and-procurement disambiguation** added as §0 of 03-missing-documents.md to catch wrong-template scaffolding before estimator hours are sunk
9. **SAM amendment-watch** explicitly called out (04-checklist.md Day 1, timeline.md, 07-risk-register.md) — SAP RFQs frequently amend mid-window
10. **Compressed bid-prep timeline** (timeline.md Due−20 to Due, vs. LPTA's Due−30 to Due) reflecting the 14–30 day SAP cycle
11. **Pricing-strategy markup band** shifted (08-pricing-strategy.md) — lower bond (no SF-24), higher overhead + profit + contingency to fund technical-narrative drafting and reflect comparative-tradeoff upside
12. **SAP-specific risks** B12–B15 added (07-risk-register.md): under-investing in narrative, missing prior-experience count, price outside "lowest 3" cutoff, wrong SF form
13. **FAR clause inventory** (08-far-clauses-flags.md) reframed around 52.213 series (SAP) + 52.212 series (commercial-item); 52.215 family called out as NOT typical
14. **Outreach email subject + body** (outreach/email-template.md) updated for SAP quote-submission format (single PDF "QUOTE PACKAGE", subject-line format from RFQ Section L)

## Template-improvement backlog

Tracked in [`bids/pais-cabin-140P6026Q0029/00-overview.md`](../../pais-cabin-140P6026Q0029/00-overview.md) "Template dogfood notes" — items 1–11 of that backlog informed this template. Open against future SAP bids:

- Short-form (½-page) prior-experience reference blocks in `firm/proposal-library/past-performance/` (currently long-form only)
- Short-form (½-page) key-personnel resumes in `firm/proposal-library/key-personnel/` (currently 1-page only)
- SAP best-value exec-summary archetype in `firm/proposal-library/exec-summary-archetypes/federal-sap-best-value.md`
- Technical-approach narrative skeleton in `firm/proposal-library/boilerplate/technical-approach-sap-skeleton.md`
- Optional `01a-remote-site-logistics.md` partial for backcountry / boat / 4WD / helicopter / marine sites (PAIS dogfood note #9)
- Insurance-limit parameterization per agency-specific clause (PAIS dogfood note #10 — DOI 1452.228-70 is lower than baseline)
