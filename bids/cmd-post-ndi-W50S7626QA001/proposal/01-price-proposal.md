# Price Proposal — SF 1442 + Schedule of Prices

The SF 1442 is the cover form; the **Schedule of Prices** is the firm-fixed-price-per-CLIN table that goes on the SF 1442 (Block 22 area) and/or as a separately-attached page.

## A. SF 1442 mechanics

Section L paragraph (a)(1) specifies which blocks the offeror completes: **14, 15, 17, 18, 20a–20c**, and **16, 19 if necessary**. See `04-SF-1442-fill-guide.md` for the section-by-section guide.

The **price** lives in:
- SF 1442 Block 22 — total amount (sum of CLINs)
- Below Block 22 — the Schedule of Prices breaks the total into CLINs

## B. Schedule of Prices — format

The CO did not provide a formal Schedule of Prices template. Use the following format:

```
                  SCHEDULE OF PRICES
        Solicitation W50S7626QA001
   Alter Command Post and NDI Room
              Blue Print Constructs
              UEI: LM4YHVQ71QG7    CAGE: 9LET0
              Date: [date of submission]
─────────────────────────────────────────────────────────────────
CLIN    Description                                  Qty  Unit   Firm Fixed Price
─────────────────────────────────────────────────────────────────
0001    Building 1672 Command Post Relocation         1   Job    $   [USER TO FILL]
0002    Building 1675 Nondestructive Inspection       1   Job    $   [USER TO FILL]
        (NDI) Room
─────────────────────────────────────────────────────────────────
                                              TOTAL: $   [USER TO FILL]
─────────────────────────────────────────────────────────────────

Notes:
1. Each CLIN is priced independently; Government may award one without
   the other per Section L paragraph (a)(1).
2. Each CLIN price is firm-fixed and inclusive of all labor, materials,
   equipment, supervision, project management, safety, quality control,
   submittals, schedule management, badging coordination, mobilization,
   demobilization, daily site clear-out, FOD prevention, demolition
   debris disposal at appropriately-permitted facility, certified
   payroll administration per FAR 52.222-6 / -8 / -10 (Davis-Bacon),
   bonds (performance + payment per FAR 52.228-15), insurance per
   FAR 52.228-5 + Section L (g), and one-year warranty against defects
   per SOW §5.5.
3. Price acknowledges Davis-Bacon Wage Determination TX20260270 dated
   01/02/2026, Tarrant County, Building Construction.
4. Price acknowledges and incorporates Amendment W50S7626QA0010001.
5. Acceptance period: [USER TO FILL — minimum 90 cal days, see SF 1442 Block 17].
```

## C. CLIN 0001 build-up (internal — not delivered to Government)

See `takeoff-template.json` § line_items[0].subline_items for the line-by-line internal cost decomposition. Markup envelope per `05-bid-schedule-mapping.md` § C and `06-evaluation-strategy.md` § C.

```
CLIN 0001 — B1672 Command Post Relocation
─────────────────────────────────────────────
Direct cost (labor + materials + sub):                $[USER TO FILL]
+ Field overhead (8.5%):                              $[       ]
+ General Conditions (7.5%):                          $[       ]
+ Insurance (2.5%):                                   $[       ]
+ Bonds (2.0%):                                       $[       ]
+ Contingency 5%:                                     $[       ]
+ Home-office overhead (5.0%):                        $[       ]
+ Profit (7.5%):                                      $[       ]
─────────────────────────────────────────────
CLIN 0001 firm-fixed price:                           $[       ]
```

Mid-target indicative: ~$340K.

## D. CLIN 0002 build-up (internal — not delivered to Government)

```
CLIN 0002 — B1675 NDI Room
─────────────────────────────────────────────
Direct cost (labor + materials + sub):                $[USER TO FILL]
+ Field overhead (8.5%):                              $[       ]
+ General Conditions (7.5%):                          $[       ]
+ Insurance (2.5%):                                   $[       ]
+ Bonds (2.0%):                                       $[       ]
+ Contingency 10% (Sheet 2 + AFFF unknowns):          $[       ]
+ Home-office overhead (5.0%):                        $[       ]
+ Profit (7.5%):                                      $[       ]
─────────────────────────────────────────────
CLIN 0002 firm-fixed price:                           $[       ]
```

Mid-target indicative: ~$135K.

## E. Combined-CLIN sanity checks

| Check | Threshold | Action if exceeded |
|---|---|---|
| Combined total within $400K – $600K mid-band | ✅ aligned with bid envelope | no action |
| Combined total < $300K | Below floor — likely missing scope | Re-review takeoff |
| Combined total > $700K | Above ceiling — likely double-counting / over-conservative contingency | Re-review markup stack |
| CLIN 0001 / CLIN 0002 ratio between 2:1 and 4:1 | ✅ aligned with relative SF + complexity | no action |
| CLIN 0001 / CLIN 0002 ratio > 5:1 | CLIN 0002 is over-discounted | Re-review CLIN 0002 |
| CLIN 0001 / CLIN 0002 ratio < 1.5:1 | CLIN 0002 is over-loaded | Re-review CLIN 0002 contingency |
| Markup % on either CLIN > 60% | Likely double-counting | Re-review |
| Markup % on either CLIN < 25% | Skinny — confirms low margin / aggressive | OK if past-perf is the discriminator |

## F. CLIN-balance discipline

Per Section M (a)(v): *"costs are found to be unbalanced"* triggers Government negotiations.

**Don't load CLIN 0001 to subsidize CLIN 0002 (or vice versa).** Each CLIN should:
- Carry its own direct cost
- Carry an allocation share of field overhead, GCs, insurance, bonds, OH, profit proportional to its direct cost
- Carry CLIN-specific contingency (5% on 0001, 10% on 0002)

## G. Bid-bond penal amount

Bid bond = **20% of total bid OR $3,000,000, whichever is less** (FAR 52.228-1).

| Bid | Bid bond penal amount |
|---|---|
| $300,000 | $60,000 |
| $400,000 | $80,000 |
| $475,000 (mid) | $95,000 |
| $500,000 | $100,000 |
| $600,000 | $120,000 |
| $700,000 | $140,000 |

**$3M cap is not binding at this magnitude.** Tell the bonding agent to issue at the bid amount.

## H. Performance + Payment bonds (post-award)

Each = **100% of contract price** (FAR 52.228-15 if award > $150K — virtually certain).

| Bid | Perf bond | Payment bond |
|---|---|---|
| $300K | $300K | $300K |
| $475K | $475K | $475K |
| $700K | $700K | $700K |

Bondability letter (`06-bondability-letter-template.md`) reflects these.

## I. Subline-item rollup audit (do this on Wed 6/3 EOD)

| Audit | Method | Action if fail |
|---|---|---|
| Every subline in `takeoff-template.json` has a unit_cost > 0 | Open JSON, search for `"unit_cost": 0.0` | Either fill in or `"suppressed": true` with note |
| Every subline with `"needs_sub_quote": true` has an actual sub quote | Cross-reference with `outreach/04-`, `05-`, `06-` responses | Default to RSMeans + 10% if no quote arrived |
| Sum of subline totals matches the CLIN direct-cost line | Open JSON; arithmetic | Fix the math |
| Markup envelope applied per `05-bid-schedule-mapping.md` § C | Spreadsheet | Fix the math |
| Bid-bond penal amount calculated correctly (20% of final bid) | Calculator | Fix |

## J. Final pricing-lock checklist (Wed 6/3 EOD)

- ☐ All sub quotes incorporated
- ☐ Site-visit findings (or field-verify-after-award assumption) reflected
- ☐ Sheet 2 (NDI room) scope confirmed via visual review
- ☐ AFFF residue handling assumption confirmed (RFI \#5 response or assumption documented)
- ☐ Davis-Bacon labor rates applied (or sub quotes confirmed DBA-aware)
- ☐ Insurance carriers pre-confirmed at FAR 52.228-5 + Section L (g) minimums
- ☐ Bond capacity reserved at the bid envelope
- ☐ Schedule of Prices typed and printed for signature
- ☐ Bid total entered into SF 1442 Block 22
- ☐ Acceptance period entered into SF 1442 Block 17 (default 90 days)
- ☐ Authorized signer reviewed and approved
