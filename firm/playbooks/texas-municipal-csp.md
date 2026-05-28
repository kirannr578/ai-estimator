# Playbook — Texas City / County / ISD Competitive Sealed Proposal

> **Exemplar bids:** *not yet exemplified by a shipped BPC bid.* The Garland Inwood Blvd opportunity (`bids/_NO_GO/2026-05-19-garland-inwood-blvd-REQ00002146.md`) is the closest BPC near-miss; future Frisco / Plano / McKinney / Allen / Garland / Dallas city + ISD bids will fill in.
>
> **Matching workspace template:** *to be created — clone `bids/_TEMPLATES/texas-state-csp-hsp/` and trim out HSP (replace with city-specific MBE/WBE/DBE narrative where applicable), swap UGSC for city/county procurement code references.*

## 1. Procurement description

Texas city, county, and Independent School District (ISD) procurements use the **Competitive Sealed Proposal (CSP)** vehicle for construction work, similar to the state CSP in [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md) but with different controlling statutes and a different compliance fingerprint. Key differences:

- **Cities** procure under **Tex. Local Gov't Code Chapter 252** (cities + towns + special districts)
- **Counties** procure under **Tex. Local Gov't Code Chapter 262** (counties)
- **ISDs** procure under **Tex. Educ. Code Chapter 44** (school districts), which mirrors much of Chs. 252/262 but with TEA-specific overlays
- **CIQ (Conflict of Interest Questionnaire)** under **Tex. Local Gov't Code Chapter 176** is required for **every** vendor doing business with a local government entity — state agencies are exempt from Ch. 176; local govts are not
- **HB 1295 Certificate of Interested Parties** (Tex. Gov't Code §2252.908) is required for any contract ≥ $1M OR any contract requiring local-government governing-body approval — most ISD bond construction and most county courthouse / facility construction triggers it
- **Local-preference ordinances** vary by city: Dallas + Houston have established local-preference scoring up to 5%; Frisco, Plano, McKinney do not
- **Minority subcontracting goals** are stronger in Dallas + Houston (M/WBE programs with formal goals + GFE binders) than in suburban DFW cities (most have no formal program)
- **Pay-or-play / living-wage / prevailing-wage** rules are city-specific: Dallas has a prevailing wage ordinance for city-funded construction > $50K; Houston similar; most suburban cities defer to Tex. Gov't Code Ch. 2258 for prevailing wage on > $50K state-funded portions only
- **Cooperative procurement** — many ISDs + cities use **TASB BuyBoard**, **TIPS**, **Region purchasing co-ops** (Region 10 ESC, Region 11 ESC), or **OMNIA Partners** for non-CSP work, but new construction generally goes through the local CSP process

When you'll see it:

- City of Frisco / Plano / Allen / McKinney / Garland / Richardson / Carrollton / Lewisville (DFW suburbs) — small-to-medium city facility work, parks, fire stations, libraries; typical $250K – $5M
- City of Dallas / Houston / Fort Worth — major city facility + parks + transportation work; typical $1M – $50M+
- County (Collin, Denton, Dallas, Tarrant) — courthouse, jail, road & bridge facility work
- ISD (Frisco, Plano, Allen, McKinney, Lewisville, Richardson, Garland, Dallas) — bond-funded school + admin construction
- Major special districts (Trinity River Authority, NTMWD, North Texas Tollway Authority)

When it's a different beast (use a different playbook):

- **Texas State CSP / RFCSP with HSP** — State university (TAMU System, UT System, TTU System), TSC, TFC, TxDOT facility work. Use [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md). HSP is state-only; CIQ + HB 1295 are local-only at the form level.
- **Federal SBA RFQ / LPTA** — use [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md). Completely different statute frame.
- **TASB BuyBoard / TIPS / OMNIA cooperative purchase** — for off-the-shelf materials + equipment + services, not generally for new-construction CSPs. If the agency intends to award via cooperative, the bid is structured as a cooperative-pricing acceptance, not a CSP.

## 2. Typical evaluation criteria

CSP scoring under Tex. Local Gov't Code Ch. 252 / 262 / Educ. Code Ch. 44 must use **published evaluation factors**. Modal split for DFW-area local government construction CSPs:

| Factor | Typical weight | Sub-criteria | Notes |
|---|---|---|---|
| **Price** | 40–60% | Total proposal price including all priced items + alternates | Usually the largest single weight; rarely > 60% on negotiated CSPs |
| **Past Performance / References** | 15–25% | Similar size + scope projects within last 3–5 yrs; owner-side reference contacts | Local govt often calls all 3 references — pre-confirm them |
| **Project Management Plan / Schedule** | 10–15% | Phasing logic; CPM Gantt; key-milestone narrative | Some cities require a 30/60/90-day mobilization plan |
| **Qualifications of Key Personnel** | 5–15% | PM + Super résumés; commitment letters | Some ISDs (DISD, HISD) require named PM + Super in the proposal and lock them via the contract |
| **Local Preference** (Dallas, Houston, sometimes Fort Worth) | 5% | Up to 5% bid-evaluation credit for local firms | "Local" usually defined as headquartered within the city limits or county |
| **M/WBE / DBE Participation** (Dallas, Houston, DART, Fort Worth) | 5–15% | Numeric goal (e.g. Dallas M/WBE goal often 25–32% for construction) + GFE binder if shortfall | Suburban DFW cities (Frisco, Plano, etc.) typically have NO formal M/WBE goal |
| **Safety / Insurance / Bonding** | Pass/Fail or 5% | EMR + insurance limits + bondability | Most cities make this Pass/Fail; Dallas + Houston sometimes score it |

**Local govts publish their scoring rubric in the CSP §00 21 00 equivalent.** Read it before pricing — a Dallas CSP with 32% M/WBE goal scored at 15% weight is a fundamentally different bid than a Frisco CSP with no M/WBE goal at 0% weight.

## 3. BPC posture against this procurement type

Reference: [`firm/firm-profile.json`](../firm-profile.json), [`firm/firm-profile.md`](../firm-profile.md).

| Threshold | Required value | BPC value | Status |
|---|---|---|---|
| TX SOS franchise tax good standing | Yes | Per TX Taxable Entity Search | ⚠️ Verify before each bid |
| TX HUB cert (state-level certification — many cities accept as M/WBE equivalent) | Optional but useful in Dallas/Houston | TX HUB VID `1874292998900` (verify renewal) | ⚠️ |
| Local M/WBE certification with city procurement office (Dallas BDPS, Houston OBO) | Useful for Dallas + Houston bids | Not currently held | 🔴 — opportunity for Day-4+ posture build if BPC pursues Dallas market |
| North Central Texas Regional Certification Agency (NCTRCA) certification (covers DART, Fort Worth, NCTCOG entities) | Useful for DART + NCTCOG bids | Not currently held | 🔴 — opportunity if NCTCOG / DART bids surface |
| City-of-business-residence registration on each city's vendor portal | Required by most cities to receive notifications | Frisco vendor portal status `[USER TO FILL — verify]`; Plano `[USER TO FILL]`; Garland `[USER TO FILL]`; Dallas `[USER TO FILL]` | 🔴 — Day-3+ priority |
| CIQ (Tex. Local Gov't Code Ch. 176) — vendor signature on file or per-bid | Per-bid signed CIQ | `[USER TO FILL — sign per bid; verify BPC has not employed any local-government officer in past 12 months]` | ⚠️ |
| HB 1295 Certificate of Interested Parties (Tex. Gov't Code §2252.908) | Filed with TEC per-contract ≥ $1M | Per-bid filing; pre-file with placeholder contract # to accelerate | ⚠️ |
| Bond capacity for $500K – $5M city/ISD work | Single-project capacity ≥ project value | $1M floor; needs to climb for full DFW market access | ⚠️ — coordinate with surety |
| Commercial GL $1M / $2M (typical city minimum) | $1M / $2M | $1M / $2M on current policy | ✅ — confirm Umbrella $2M+ for ISD bond work |
| TX Comptroller WebFile active | Yes | Verify | ⚠️ |
| OSHA 10/30 rosters for site supervision | Yes | Per `firm/firm-profile.json → key_personnel` | ⚠️ — verify card currency annually |

## 4. Required compliance docs (per bid)

| Document | Source | Notes |
|---|---|---|
| Signed CIQ (Form CIQ — Tex. Local Gov't Code Ch. 176) | Standard form on each city's procurement page; also at TEC website | Required by every local-government bid; signature is per-vendor + per-procurement |
| Signed HB 1295 Certificate of Interested Parties (Form 1295) | Filed online at TEC: `https://www.ethics.state.tx.us/Forms/Form_1295.htm` | Required if contract value ≥ $1M; pre-file with placeholder contract # |
| Local-government Vendor Registration (per city portal) | Each city's procurement portal | Required to receive notifications + bid; one-time per city |
| CSP Proposal Form (city/county/ISD-specific) | CSP §00 42 13 equivalent | Varies by entity — never re-use a prior bid's form |
| Bid Bond (5% typical; sometimes 1–10% per local ordinance) | Surety on Texas-licensed list | Per Tex. Gov't Code Ch. 2253 + local ordinance |
| Surety P&P bond commitment letter | Same surety | For award |
| Insurance certificates per local SGC + Cost-of-Wrap if owner-controlled program | Insurance broker | City + county SGCs vary; Dallas + Houston often require higher limits than suburban cities |
| W-9 current calendar year | Form W-9 | Per agency |
| TX HUB cert (if claiming HUB status) | TX Comptroller | Per agency if HUB-preference applies |
| Local M/WBE cert (if claiming city-specific M/WBE) | Dallas BDPS / Houston OBO / NCTRCA / etc. | Per agency |
| Affidavit of non-collusion | Standard form | Per agency |
| Affidavit re Texas Resident Bidder (per Tex. Gov't Code §2252.001) | Standard form | TX-domiciled firms attest yes |
| Felony / debarment attestation | Standard form | Per agency |
| Child support obligation attestation (per Tex. Family Code §231.006) | Standard form | Per agency |
| Iran / Sudan / Israel / energy-company / firearms-industry boycott reps (per Tex. Gov't Code §§ 808, 2271, 809, 2274) | Standard reps | Per agency |
| Conflict-of-interest disclosure beyond CIQ (if applicable) | Per agency | Some cities + ISDs have additional disclosure forms (e.g. lobbyist disclosure) |
| OSHA 10 / 30 roster | Per firm | Per agency if SGC requires |

## 5. Standard solicitation forms

| Form | Source | When |
|---|---|---|
| **City / county / ISD-specific Proposal Form** | CSP package §00 42 13 equivalent | Always — never re-use prior bid |
| **CIQ Form** | Per CSP package or TEC website | Always |
| **HB 1295 Form 1295** | TEC online filing | Always if ≥ $1M or governing-body approval |
| **Bid bond form (city-specific)** | Surety | Always |
| **TX SOS Franchise Tax Good Standing letter** | TX Comptroller WebFile printout | Always |
| **Local M/WBE certification (if applicable)** | Dallas BDPS / Houston OBO / NCTRCA | Per agency |

## 6. Submission portals (DFW-area city-by-city)

| City / entity | Portal | Notes |
|---|---|---|
| Frisco | **Ionwave** at `https://frisco.bonfirehub.com/` or Ionwave-managed | Vendor registration required; e-bid submission |
| Plano | **Bonfire** at `https://plano.bonfirehub.com/` | Vendor registration required; e-bid |
| McKinney | **Bonfire** at `https://mckinneytexas.bonfirehub.com/` | Same |
| Allen | **Bonfire** | Same |
| Garland | **Ionwave** at `https://garland.ionwave.net/Login.aspx` | Vendor registration; e-bid; Garland Inwood Blvd was REQ00002146 |
| Richardson | **Bonfire** | Same |
| Carrollton | **OpenGov Procurement** at `https://procurement.opengov.com/` | Vendor registration |
| Lewisville | **OpenGov Procurement** | Same |
| Dallas | **BidNet / Dallas City Hall Procurement** at `https://www.bidnetdirect.com/dallas-texas/` | Multiple portals — verify per bid |
| Fort Worth | **PeopleSoft / BidSync** at `https://www.bidsync.com/` | Vendor registration |
| Houston | **City of Houston Strategic Procurement Division** at `https://purchasing.houstontx.gov/` | Vendor registration + M/WBE certification with Houston OBO |
| Collin County | **Ionwave** at `https://collincounty.ionwave.net/` | Vendor registration |
| Denton County | **eBid Systems** | Same |
| Dallas County | **PeopleSoft / Dallas County Purchasing** | Same |
| Tarrant County | **eBid Systems** | Same |
| Frisco ISD | **Bonfire** at `https://friscoisd.bonfirehub.com/` | ISD bond construction portal |
| Plano ISD | **Bonfire** | Same |
| Lewisville ISD | **eBid Systems / TASB BuyBoard for cooperative** | Same |
| Dallas ISD | **BidSync / DISD Procurement Services** | Major bond program |
| TASB BuyBoard (cooperative) | `https://www.buyboard.com/` | Cooperative purchasing — typically materials + services, not new construction CSPs |
| TIPS-USA (cooperative) | `https://www.tips-usa.com/` | Same |

## 7. Submission format conventions

| Convention | Norm | Notes |
|---|---|---|
| File format | PDF; e-bid submission via city portal | Some cities still accept sealed-envelope hand-delivery as backup |
| Number of copies (if physical) | 1 original + 1–3 copies typical | Per CSP |
| Page limits | Vary; most cities allow 50–100 pages total | Per CSP |
| Pricing form | City-specific Bid Schedule | Always required |
| Acceptance period | 90–120 cal days typical | Per CSP |
| Delivery cutoff | Local time of the city/county clerk | Always **before** the stated time — late = rejected |
| Email-only submission | Rare for CSPs ≥ $50K | Per CSP |

## 8. Typical timeline

| Phase | Days from notice | Notes |
|---|---|---|
| Notice of CSP posted on city portal + per Local Gov't Code Ch. 252 advertising rules | T-0 | Cities + counties: published in newspaper + on portal for ≥ 14 days per Ch. 252.041 |
| Pre-proposal meeting (often recommended, sometimes mandatory) | T+5 to T+14 | RSVP per CSP |
| Site visit | T+5 to T+14 | Often paired with pre-proposal |
| RFI / addenda cutoff | T+15 to T+25 | Typically 5–7 days before due |
| Last addendum | T+18 to T+26 | Per CSP |
| Proposal due | T+30 to T+45 (city ~4–6 wk; ISD ~6–8 wk; county ~6 wk) | |
| Public opening | Immediately after due | Per Local Gov't Code Ch. 252.041 |
| Evaluation | 2–4 weeks | Scoring committee scores against published rubric |
| BAFO / negotiations | Optional per Ch. 252.043 — CSP allows negotiation post-opening | Different from state CSP where BAFO is more constrained |
| Governing-body approval (if > local approval threshold) | T+60 to T+120 | Council/Court/Board agenda |
| Award notification | T+45 to T+120 | Per CSP |
| Contract execution | T+60 to T+150 | Per CSP |
| NTP | Within 10–30 days of execution | Per CSP |

## 9. Common pitfalls

1. **Missing CIQ.** Tex. Local Gov't Code Ch. 176 requires a signed CIQ from every vendor doing business with a local government. Missing CIQ = non-responsive bid. Pre-fill the standard form, sign per bid, attach.
2. **Missing HB 1295.** Required for contracts ≥ $1M. Filing online with TEC takes ~10 minutes but requires a contract identifying number — pre-file with the CSP solicitation number so the certified PDF is in hand at submission.
3. **Wrong cooperative procurement reference.** If the agency intends to award via TASB BuyBoard or TIPS cooperative, the bid must reference the cooperative agreement, not be structured as a standalone CSP. Confusing the two voids the bid.
4. **Local-preference forgone.** Dallas and Houston offer up to 5% local-preference scoring. A Frisco-based firm bidding Dallas should team with a Dallas-based sub to capture some local-preference value or accept the scoring gap.
5. **M/WBE goal underestimated.** Dallas + Houston bids with formal M/WBE goals require a GFE binder (similar to TX state HSP). Underestimating the binder workload kills the bid quality.
6. **Vendor registration missing.** Most cities require pre-registration on their portal to even download the CSP. Register on every DFW-area portal before any bid surfaces — one-time cost, eliminates last-minute scrambling.
7. **City-specific prevailing wage missed.** Dallas + Houston have city prevailing-wage ordinances for city-funded construction > $50K. Suburban DFW cities mostly defer to Tex. Gov't Code Ch. 2258 (state-funded prevailing wage). Read the CSP carefully — assuming "no prevailing wage" because the city is suburban can underprice labor.
8. **Pay-or-play / safety / E-Verify reps missed.** Dallas Pay-or-Play ordinance (for construction > $50K) + Houston similar. E-Verify required by state law for state-funded portions; some cities require for all bidders.
9. **Sub-list lock at proposal vs at award.** Some cities require a named sub list at proposal; others defer to post-award. Read CSP — if subs must be named, BPC commits to those subs and substitution requires city approval.
10. **Bond form non-conforming.** City-specific bond forms vary. Using a state CSP bond form for a city CSP is non-responsive. Pull the bond form from THIS CSP package.

## 10. CSP pricing discipline (local government)

| Component | % of direct | Notes |
|---|---|---|
| Direct cost (subs + materials + self-perform labor) | 100% | |
| General conditions / supervision | 10–14% | |
| Bonds (bid + P&P) | 1.5–2.5% | |
| Insurance | 3–5% | Higher Umbrella for ISD bond work ($5M+) |
| TX Ch. 2258 / city prevailing-wage uplift | 0–4% | Per applicable WD |
| Contingency | 5–7% | Local govt SGCs vary in hidden-condition allocation; 7% conservative |
| Overhead | 8–12% | |
| Profit | 5–8% | Local govt allows wider profit range than federal LPTA |
| **Total markup over direct** | **~35–50%** | Direct-to-bid multiplier of ~1.35–1.50 |

**Don't bid > 15% below median competitor on a city CSP.** Cities have more latitude than federal CO to award to non-lowest under tradeoff scoring, but they still flag suspiciously low bids on price realism.

**Carry allowances line-by-line, do NOT roll into lump-sum.** Same discipline as state CSP — owner controls the allowance and changes via change order.

## 11. Reusable language blocks (Day-3+ build targets)

These will be added to [`firm/proposal-library/`](../proposal-library/README.md) as BPC pursues its first city/county/ISD bid:

| Block | Where it will live | When to use |
|---|---|---|
| Texas municipal CSP exec-summary opening | `firm/proposal-library/exec-summary-archetypes/texas-municipal-csp.md` *(TODO)* | Front of proposal |
| CIQ pre-fill template | `firm/proposal-library/boilerplate/ciq-template.md` *(TODO)* | Attach to every local-govt bid |
| HB 1295 filing checklist | `firm/proposal-library/boilerplate/hb-1295-checklist.md` *(TODO)* | For every bid ≥ $1M |
| Local M/WBE GFE binder template (Dallas + Houston) | `firm/proposal-library/boilerplate/local-mwbe-gfe-binder.md` *(TODO if BPC pursues Dallas/Houston)* | Dallas + Houston bids with formal M/WBE goals |
| City-specific bond commitment letter templates | `firm/proposal-library/boilerplate/bond-commitment-city-template.md` *(TODO)* | Per city — most accept the same letter; some have city-specific forms |

## 12. Cross-references

- **State CSP playbook (sibling Texas procurement type):** [`texas-state-csp-hsp.md`](texas-state-csp-hsp.md)
- **Federal LPTA + tradeoff playbooks (sibling procurement families):** [`federal-sba-rfq-lpta.md`](federal-sba-rfq-lpta.md), [`federal-rfp-best-value-tradeoff.md`](federal-rfp-best-value-tradeoff.md)
- **Pre-solicitation watchlist (covers TX local pre-sol tracking too — extend SAM filters with city/ISD/county portals):** [`federal-pre-solicitation-watchlist.md`](federal-pre-solicitation-watchlist.md)
- **Workspace template:** *to be created — clone `bids/_TEMPLATES/texas-state-csp-hsp/`, swap HSP for local M/WBE language, swap UGSC for city SGC references*
- **Compliance registry:** [`firm/compliance/README.md`](../compliance/README.md)
- **NO-GO memo from the closest near-miss:** [`bids/_NO_GO/2026-05-19-garland-inwood-blvd-REQ00002146.md`](../../bids/_NO_GO/2026-05-19-garland-inwood-blvd-REQ00002146.md)
- **TEC Form 1295 filing portal:** `https://www.ethics.state.tx.us/Forms/Form_1295.htm`
- **TX Comptroller HUB Search (for any HUB-preference scoring):** `https://comptroller.texas.gov/purchasing/vendor/hub/search.php`
