# Price references — $/SF and $/unit benchmarks

Benchmarks for federal interior renovation in the DFW Metroplex (Tarrant County). Used to sanity-check the takeoff rollup in `takeoff-template.json` and the bid envelope in `05-bid-schedule-mapping.md` § D.

> ⚠️ **Adjust to current local market.** RSMeans CCI for Fort Worth (74) is currently ~0.95–1.02 of national. Davis-Bacon TX20260270 trade rates apply (see `prevailing-wages.md`). Prices below are 2026 cost basis; if executing in 2027, escalate ~3–5%.

## A. Whole-project $/SF benchmarks (federal interior renovation)

| Project type | $/SF range (2026 cost) | Source / experience |
|---|---|---|
| Standard federal interior office renovation (paint, carpet, basic MEP, no specialty) | **$120 – $180/SF** | Industry typical for federal small-project renovations in DFW |
| **Secure-area** federal interior renovation (mantrap, secure doors, anti-access measures, security comm rough-in) — **CLIN 0001 benchmark** | **$180 – $280/SF** | 25–50% premium over standard federal interior renovation due to specialty doors+hardware, mantrap electronic-lock kit, double-layer GWB above ceiling, anti-access bars, EAP rotating light + signage, security comm conduit |
| Full SCIF construction (TEMPEST + ICD 705 + RF shielding) | **$450 – $800+/SF** | NOT applicable to this project — for reference only |
| AFFF-room conversion to standard interior space (PFAS-conscious demo, basic interior fit-out) — **CLIN 0002 benchmark** | **$130 – $220/SF** | Standard interior + 10–25% AFFF / environmental contingency. If PFAS-impacted-substrate residue is found, add 30–60% for TCEQ-permitted disposal |
| NDI / inspection-equipment-installation room (live equipment, RF shielding, vibration-isolation, dust containment) | **$300 – $550/SF** | NOT applicable — this CLIN is a space-conversion only, no live NDI equipment installation per SOW |

## B. CLIN-specific bid envelope (mid-target estimate)

Per `05-bid-schedule-mapping.md` § D:

| CLIN | Approx SF (verify) | $/SF mid | Mid-target estimate |
|---|---|---|---|
| **0001 — B1672 Command Post** (secure-area renovation) | ~2000 SF | $230/SF | **~$460K** |
| **0002 — B1675 NDI Room** (AFFF conversion) | ~600 SF | $175/SF | **~$105K** |
| **Combined** | ~2600 SF | — | **~$565K** |

Floor scenario (low SF + low $/SF, no major DSCs): ~$320K combined.
Ceiling scenario (high SF + high $/SF + AFFF + DSC + Sheet 2 surprises): ~$875K combined.

**Recommended bid envelope: $475K mid-target ± 20% based on site visit + sub quotes.** Bond capacity reservation: $500K (mid + small headroom).

## C. Trade-by-trade unit-cost benchmarks (DFW Metroplex, 2026, RSMeans + market)

| Item | Unit | RSMeans-class range | Market range (DFW + DBA) | Notes |
|---|---|---|---|---|
| Metal-stud partition (3-5/8" 25-ga, full-height to deck, framed at 16" OC) | LF | $9 – $14 | $12 – $18 | Apply 1.15× for full-height-to-deck |
| 5/8" GWB Type-X, taped/finished | SF (one side) | $3.00 – $4.50 | $3.50 – $5.50 | 2-layer adds ~75% |
| Painting — interior, walls (1 coat primer + 2 coats finish, cut + roll) | SF | $1.10 – $1.80 | $1.40 – $2.20 | SW1016 spec is mid-grade product |
| VCT (12" x 12") installed (AZrock) | SF | $4.50 – $6.50 | $5.50 – $7.50 | Including mastic + 4-side lay |
| Carpet tile installed (Shaw Contract Clear Tile spec) | SF | $5.50 – $8.50 | $7.00 – $10.50 | Specifically the Shaw Contract Style #59564 — call manufacturer for current price |
| Rubber cove base (4") | LF | $2.75 – $4.50 | $3.50 – $5.50 | |
| Drop-ceiling grid + tile mod (re-tile + adjust) | SF | $4.50 – $7.50 | $5.50 – $9.00 | Modify only — full replacement would be 2× |
| Solid-wood door + frame + std hinges (NO security upgrade) | EA | $850 – $1,500 | $1,100 – $2,000 | Baseline |
| Solid-wood door + steel-sheet exterior reinforcement + secure hardware (Stanley/Best Lock-Core compatible) | EA | n/a | **$2,500 – $4,500** | Specialty — sub quote |
| Mantrap electronic-lock kit (full system: 2 doors, console controls, fail-locked, anti-tailgate, manual override) | LS | n/a | **$15,000 – $35,000** | Sub quote — varies by manufacturer (HID, S2, LenelS2, Allegion) |
| Door alarm — emergency exit | EA | $300 – $600 | $450 – $850 | |
| Credential window — impact-rated mesh-reinforced 1-way + framed penetration + trim | EA | n/a | **$1,800 – $3,500** | Specialty — glazing sub |
| Casework — base cabinets (commercial laminate) | LF | $200 – $400 | $250 – $500 | Govt-approval cycle adds time |
| Casework — overhead cabinets (commercial laminate) | LF | $150 – $300 | $200 – $400 | |
| Counter (commercial laminate) | LF | $35 – $75 | $50 – $100 | Solid surface or quartz adds 2-3× |
| Sink + faucet (commercial stainless) | EA | $400 – $900 | $500 – $1,200 | Replace |
| 20A / 120V receptacle (rough-in + device + cover) | EA | $90 – $160 | $130 – $220 | DBA labor rate adjusts |
| GFCI receptacle | EA | $130 – $200 | $180 – $260 | |
| 2x4 LED drop-ceiling fixture | EA | $180 – $320 | $220 – $400 | |
| Occupancy sensor | EA | $100 – $200 | $130 – $260 | |
| Battery-backup emergency light + exit sign | EA | $150 – $260 | $200 – $340 | |
| Fire-alarm strobe | EA | $180 – $320 | $230 – $400 | Synchronization-tested adds time |
| Comm rough-in (¾" EMT to above ceiling, 1-gang box, pull string) | EA | $80 – $140 | $110 – $180 | Per point |
| HVAC supply diffuser (add) | EA | $250 – $450 | $350 – $600 | + duct spur |
| HVAC return grate (add) | EA | $150 – $300 | $200 – $400 | |
| HVAC duct mod (12" round galv flex) | LF | $25 – $45 | $35 – $65 | Per LF including hangers |
| HVAC override button + integration (BMS-platform-specific) | LS | n/a | **$1,200 – $4,500** | Highly platform-dependent |
| Anti-access bars on duct/return (custom fab) | EA | n/a | **$200 – $500** | Custom fab + install |
| HVAC test + balance + report (NEBB or AABC) | LS | n/a | **$2,500 – $6,500** | Sized for the small scope |
| Fire-suppression head (existing system mod) | EA | $250 – $500 | $350 – $700 | Including mod of existing branch |

## D. Markup envelope (federal small-project)

| Element | Range | Notes |
|---|---|---|
| Field overhead (super, layout, FOD, daily cleanup, fence) | 7–10% | Tight site = upper end |
| General Conditions (PM, safety, QC, submittals, badging coord) | 6–9% | DoD documentation load = upper end |
| Insurance | 2–3% | Of direct cost |
| Bonds | 1.5–2.5% | Of total bid value |
| Contingency CLIN 0001 | 3–5% | Secure-area unknowns |
| Contingency CLIN 0002 | 8–12% | Sheet 2 + AFFF unknowns (drop after RFI #5 + Sheet 2 review) |
| Home-office overhead | 4–6% | Standard small-firm rate |
| Profit | 6–9% | Comparative-evaluation allows mid-upper; LPTA would push to 3–5% |

**Total markup on direct cost** typically **30–45%** for federal small-project renovations of this complexity.

## E. Davis-Bacon impact

DBA wage rates (TX20260270) are typically 5–15% above non-DBA market rates for trades like electricians, plumbers, sheetmetal workers, carpenters in DFW. The unit costs above already reflect DBA-equivalent labor for federal work.

For specifically:
- Electricians: DBA wage + fringe ~$45/hr loaded → market is $35–$45/hr
- Carpenters: DBA wage + fringe ~$30/hr loaded → market is $25–$35/hr
- Sheetmetal workers: DBA wage + fringe ~$33/hr loaded → market is $28–$36/hr
- Painters: DBA wage + fringe ~$28/hr loaded → market is $22–$30/hr

See `prevailing-wages.md` for the WD distillation.

## F. Sources

- RSMeans Building Construction Cost Data 2026 (national, with DFW CCI of ~1.00)
- DFW Metroplex federal interior renovation experience (CO-cited construction cost ranges from past awards)
- Sub-quote pre-quotes for similar projects in 2024–2025 (firm-internal)
- Davis-Bacon WD TX20260270 (Tarrant County, Building Construction, 01/02/2026)
