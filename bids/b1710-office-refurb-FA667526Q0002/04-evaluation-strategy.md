# Evaluation strategy — B1710 Office Refurbishment

## 1. RFQ shape

| Dimension | Value |
|---|---|
| Method | RFQ (Request for Quote), SF 1449 |
| Regulatory basis | FAR Part 12 (Commercial Items) + FAR Part 13 (SAP), Class Deviation 2026-O0038 |
| Pricing | Firm Fixed Price, single Lot |
| Evaluation regime | **Comparative evaluation per FAR 12.203(c)(2)** (inferred from absence of any Section M scoring matrix; FAR 52.212-2 is **not cited** in the package; Section M contains only FAR 52.225-10 *Notice of Buy American Requirement*) |
| Set-aside | 100% Small Business, NAICS 236220 |
| Award | Single award (one Lot) |

## 2. What's actually written in Section M

Verbatim from the source PDF, page 25:

> Section M — Evaluation Factors for Award
> 52.225-10 — Notice of Buy American Requirement—Construction Materials. (May 2014)

**That's the entire Section M.** No `52.212-2` (Evaluation - Commercial Items). No scoring matrix. No published weights. No LPTA / best-value declaration.

## 3. What this almost certainly means

Three plausible readings, ranked by likelihood:

### Reading #1 (most likely): comparative evaluation per FAR 12.203(c)(2)

FAR 12.203(c)(2) was added by the Federal Acquisition Streamlining language and authorizes COs running commercial-item RFQs under simplified acquisition procedures to **"conduct a comparative evaluation of the quotes received"** without publishing objective standards. The CO can weigh past performance, technical understanding, schedule realism, and price however the CO finds reasonable, and award to the offer that represents the "best value" — which can be the lowest price OR a higher-price offer with stronger past performance.

This is the **same regime as the sister `bids/cmd-post-ndi-W50S7626QA001/` workspace** (Section M Tailored Deviation 2026-O0038 there spells it out explicitly; here, the CO has simplified by just citing the Buy American notice and relying on FAR 12.203(c)(2) by reference through the 52.212-1 Deviation).

### Reading #2: de facto LPTA (lowest-price technically acceptable)

Under FAR 13.106 SAP, when the CO publishes no evaluation criteria, the default is LPTA: award to the lowest-priced offeror who is technically acceptable + responsible. This is the most common reality for sub-$100K SAP construction work.

If this is the regime, then **price is the dominant factor**, and our strategy is to be the lowest responsive offeror. "Responsive" here means:
- Signed SF 1449 with all required blocks filled
- SAM.gov active + reps & certs current
- Price for the entire Lot, FFP
- Acknowledgement of any amendments (none yet)
- Compliance with Buy American (52.225-9 + 52.225-10)

### Reading #3: tailored deviation (Section M is incomplete)

The CO may have intended to cite a tailored 52.212-2 deviation but omitted it. This is unlikely (the RFQ is otherwise meticulously formed with 50+ explicit clause cites), but worth noting. If the CO is using Tailored Deviation 2026-O0038 the way the 136 AW used it on the Cmd Post RFQ, the evaluation regime would be:

1. Responsibility check (FAR 9.104 — debarment/suspension/exclusion)
2. Comparative evaluation (FAR 12.203(c)(2))
3. Past performance (CPARS / SPRS / personal knowledge)
4. Technical review:
   - Materials / equipment / labor list ("RSMeans-style output")
   - Realistic 90-day schedule
5. Best-value award (CO has discretion to accept other than lowest-price)

**Working assumption:** Reading #1 + Reading #3 hybrid. We prepare a complete offer package — signed SF 1449, equipment/material/labor list, 90-day schedule, past-perf 3-pack, SAM screenshot, COI, payment-bond letter — and a competitive price.

## 4. Our winning posture

Given the comparative-evaluation likely regime, we aim to be **clearly in the top quartile on at least 2 of {price, past performance, technical clarity}**, and at minimum competitive on the third.

### 4.1 Price competitiveness

- Use rule-of-thumb Davis-Bacon-uplifted pricing from `09-price-references.md` + CWICR matcher hits.
- 5% quantity contingency baked in (no site walk).
- Target: ~$50K-$70K all-in lump-sum (preliminary; will firm up after Gate 4 in `01-bid-prep-checklist.md`).
- Do NOT undercut — federal evaluators view a too-low price as a flag for an irresponsible bid or a misunderstanding of scope.

### 4.2 Past performance — 3-pack

Per `firm/firm-profile.json → past_project_selection_rules`:

1. **Hindu Temple of Southlake** — Institutional interior finishes (10,700 SF Assembly A-3 renovation; toilet partitions, demolition, finishes, partition framework). Proves BPC's institutional-construction depth.
2. **Holiday Inn Hall Park (Frisco)** — Commercial hospitality renovation. Proves BPC's commercial-finish depth and ability to work in an occupied facility (parallels the B1710 occupied-office context per SOW §3.1.2 "minimize interruption of the normal duty day").
3. **Lavon RV Park** — $1.05M new-construction RV park. Proves BPC's federal-style coordination capability — site work, MEP, utilities, fencing, retaining walls, performance-bond procurement at $1M. Most-relevant for federal CPARS-equivalence storytelling.

See `proposal/03-past-performance.md` for the full write-up. Bid-specific narrative emphasizes:
- BPC self-performs interior finishes (carpet, base, paint, drywall) — the entire B1710 scope is sweet-spot self-perform work.
- Occupied-building coordination (Hindu Temple is fully comparable to the AFRC office-occupied context).
- DBE / institutional-customer compliance track record.

### 4.3 Technical clarity

For comparative evaluation, "technical review" hinges on whether the offer demonstrates the offeror understands the work. Three deliverables make this concrete:

1. **Equipment / material / labor list** — itemized for every CSI division touched (Div 02 demolition, Div 06 wood/casework/blocking if any, Div 09 finishes covering 09 6500 resilient flooring + 09 6800 carpet tile + 09 9000 painting + 09 2900 GWB patches, Div 10 specialties for access panel). Format per `proposal/02-technical-acceptability.md`.
2. **90-day calendar schedule** with major milestones (mobilization, demo/relocate, dry trades, wet trades, flooring, punch-list, substantial completion). Gantt-style table in `proposal/02-technical-acceptability.md`.
3. **QC + Safety plan** — 1 page each. Reference OSHA 29 CFR 1926 + DAFMAN 91-203 (already cited in SOW §PART I).

## 5. Pitfalls to avoid

- **Don't include unsolicited material.** Some COs flag offers that include marketing fluff (capability statements, brochures) as non-responsive on a strict reading. Capability statement + pitch deck are appendix-only if at all.
- **Don't quote a non-equal carpet without flagging it as alternate.** SOW §B says "Shaw or other accepted contractor submission" — if quoting a Mohawk or Interface as the primary, lead with the equivalency argument; otherwise quote Shaw at spec.
- **Don't omit the dye-lot disclaimer.** Dye-lot H6958 from a 2-year-old spec may no longer be in production. Add a footnote to the price proposal: "Carpet tile quoted at Shaw Constellat EW24 Style 59326, Color 26110 Moonlight Grade A. Current dye-lot availability subject to confirmation with Shaw at submittal time per AF IMT 3000 process."
- **Don't promise a site visit that didn't happen.** The 90-day schedule should explicitly start with "Field verification of all measurements within 5 cal days of NTP" — sets expectations clearly that the SF figures are SOW-stated, not contractor-verified.
- **Don't forget the Buy American certification.** FAR 52.225-9 applies. Shaw carpet is US-made (Dalton, GA); SW paint is US-made; rubber base is US-made (Roppe, Johnsonite, etc.). All construction materials in scope are domestic; no Buy American waiver needed. State this affirmatively in the technical proposal.

## 6. Decision points for Rocky (today)

- [ ] Approve target price range $50K-$70K? (Build-up in `09-price-references.md` justifies this band.)
- [ ] Approve past-perf 3-pack as listed above? (Same as the sister `cmd-post-ndi` workspace's picks; consistent.)
- [ ] Approve Rocky as Project Manager / Superintendent of record (subject to subcontracted painter / installer crew under direct supervision)?
- [ ] Approve subcontractor strategy? Options:
   - **Self-perform 100%** — BPC's existing crew handles demo, drywall, paint, flooring. Simplest narrative.
   - **Self-perform + flooring sub** — bid a Shaw-certified installer (e.g. one of BPC's That 1 Painter-network installers) for the 3,500 SF carpet tile + base. Reduces schedule risk on the dominant scope item.
   - **Hybrid** — Rocky decides on a per-trade basis after takeoff (Thu PM).
