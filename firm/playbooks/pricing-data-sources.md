# Pricing-data sources — playbook

**Audience:** BPC estimating + tech.
**Status:** Tier 1 (free public APIs) shipped. Tier 2 (RSMeans / Gordian) deferred.
**Code:** `core/pricing/`, `scripts/refresh_pricing.py`.

---

## What this is

Blueprint Constructs has **no internal cost / sub / supplier database**. Until that's built (Tier 3 — see `firm/compliance/material-suppliers.md`), the estimating pipeline is 100% reliant on external public sources for unit costs and escalation signals.

This playbook documents:

1. The five free public data sources we pull from today.
2. How to refresh them.
3. How the escalation engine flows fresh PPI numbers into `config/cost_database.json`.
4. How to add a new source.
5. License + ToS for every source — non-negotiable, read this section before adding any new one.
6. Caveats — what these numbers are and aren't good for.

---

## Source registry

| Source | Adapter module | License | Auth | Update cadence | Provides | Status |
|---|---|---|---|---|---|---|
| BLS Producer Price Index | `core/pricing/sources/bls_ppi.py` | U.S. Public Domain — BLS | Free; optional key raises 25 → 500 req/day | Monthly | 15 commodity PPI indexes covering wood, plywood, gypsum, steel, copper wire, diesel, ready-mix, asphalt, paint, PVC, fab steel, plumbing fittings | **Shipped** |
| BLS Occupational Employment & Wage Statistics (OEWS) | `core/pricing/sources/bls_oews.py` | U.S. Public Domain — BLS | Free; optional key | Annual | 10 SOC construction trades × 6 TX metros — hourly mean wages | **Shipped** |
| FRED (Federal Reserve Economic Data) | `core/pricing/sources/fred.py` | FRED terms — attribution required | Free with email registration | Series-dependent (daily / weekly / monthly / annual) | 8 series: WTI crude (fuel proxy), construction inputs PPI, national construction earnings, industrial commodities PPI, TX CPI, construction loan rate, Case-Shiller home prices, sand & gravel PPI | **Shipped** |
| EIA petroleum prices | `core/pricing/sources/eia.py` | U.S. Public Domain — EIA | Free with email registration | Weekly | Retail diesel + retail regular gas, PADD3 (Gulf Coast / Texas) | **Shipped** |
| Davis-Bacon Wage Determinations | `core/pricing/sources/davis_bacon.py` | U.S. Public Domain — DOL WHD | None (public SAM.gov search) | On-demand per project | Active WD trade × hourly rate rows for any (state, county, project type) | **Shipped** |
| TX state-agency prevailing wage (per-project WD parser) | `core/pricing/sources/tx_prevailing_wage.py` | State of Texas public record | None (PDF arrives with solicitation) | Per-solicitation | Trade × hourly rate parsed from the per-project WD PDF attached to each TX state-agency solicitation | **Shipped** (per-project parser; see "Structural Note — Texas Prevailing Wage" below) |
| GSA Schedule price lists | `core/pricing/sources/gsa_schedule.py` | U.S. Public Domain — GSA | None | Quarterly | Construction materials catalogs (56V, 03FAC, 23V) | **Phase B — partial** (parser ships; auto-download TODO) |
| TX SmartBuy / ESBD historical awards | `core/pricing/sources/tx_smartbuy_awards.py` (`TXSmartBuyAwardsSource`) | State of Texas public record | None | Continuous (per-solicitation as they award) | Per-(solicitation, vendor) award amounts + NAICS + agency + period — REAL competitive intel for TX state contracts | **Shipped (Phase C)** — anchor-proximity regex parse over ESBD HTML; one snapshot per awarded vendor; 24h HTTP cache |
| Home Depot Pro retail catalog | `core/pricing/sources/hd_pro.py` (`HomeDepotProSource`) | Home Depot retailer-proprietary; public prices only | None | Daily (prices fluctuate hourly during promo seasons) | Per-SKU (Item ID, title, brand, price, UoM, MFR number) — retail floor for spot-checks | **Shipped (Phase C closure)** — schema.org-microdata regex parse; 10-SKU starter list; degrades to graceful empty on Akamai/CAPTCHA |
| Lowe's Pro retail catalog | `core/pricing/sources/lowes_pro.py` (`LowesProSource`) | Lowe's retailer-proprietary; public prices only | None | Daily (prices fluctuate hourly during promo seasons) | Per-SKU (Item Number, title, brand, price, UoM, model number) — retail floor for spot-checks | **Shipped (Phase C closure)** — mirror of `hd_pro`; same Akamai/CAPTCHA fragility posture |
| ENR Construction Cost Index | `core/pricing/sources/enr_cci.py` (`ENRCCISource`) | ENR — attribution required, no redistribution | None | Monthly | National 20-city composite cost index | **Shipped (Phase C)** — headline value only; full history requires ENR subscription |
| AGC PPI-based Construction Cost Index | `core/pricing/sources/agc_cci.py` (`AGCCCISource`) | AGC — attribution required, no redistribution | None | Monthly (underlying PPI) / Quarterly (Inflation Alert) | National PPI-based inflation roll-up | **Shipped (Phase C)** — landing-page headline only; Inflation Alert PDF parser is future work |
| Turner Building Cost Index | `core/pricing/sources/turner_cci.py` (`TurnerCCISource`) | Turner — attribution required, no redistribution | None | Quarterly | National TBCI composite | **Shipped (Phase C)** — latest quarter only; per-quarter article archive parser is future work |
| NAHB Cost of Constructing a Home | `core/pricing/sources/nahb_construction_cost.py` (`NAHBCostOfConstructingAHomeSource`) | NAHB — attribution required | None | Biennial (2019/2022/2024; 2026 expected) | NAHB residential single-family total construction cost (USD/home), hardcoded historical series since 1998 | **Shipped (Phase C)** — residential macro complement to ENR/AGC/Turner; live article parse + hardcoded historical fallback |

**Tier 2 (RSMeans / Gordian) — deferred.** Paid license per seat. Decision deferred until Tier 1 calibration data demonstrates a measurable gap that the free sources can't close. See `docs/ROADMAP_TAKEOFF_AUTOMATION.md` Section 5 for the build / buy gate.

---

## Refresh procedure

### Quick start

```powershell
# 1. (One-time) Copy .env.example to .env and fill in the three free keys.
copy .env.example .env

# 2. Refresh everything we can (sources missing a key skip with a warning).
.venv\Scripts\python.exe scripts\refresh_pricing.py

# 3. Refresh a subset.
.venv\Scripts\python.exe scripts\refresh_pricing.py --sources bls_ppi,fred

# 4. Pin a reporting period (BLS uses YYYY).
.venv\Scripts\python.exe scripts\refresh_pricing.py --period 2026-04

# 5. Pull Davis-Bacon WD for an active project.
.venv\Scripts\python.exe scripts\refresh_pricing.py `
    --sources davis_bacon `
    --davis-bacon-state TX `
    --davis-bacon-county "Tom Green" `
    --davis-bacon-project-type Building
```

### Where snapshots land

```
config/pricing_snapshots/
├── bls_ppi/<series_id>/
│   ├── 2026-03.json
│   ├── 2026-04.json
│   └── latest.json              # mirror of newest period
├── bls_oews/<series_id>/...
├── fred/<series_id>/...
├── eia/<series_id>/...
├── davis_bacon/<state>_<county>/<wd_number>.json
└── _http_cache/                 # gitignored, 24h TTL
```

`latest.json` is overwritten on each refresh with whichever snapshot has the most recent `fetched_at`. Period-specific files are append-only — they form the historical record we escalate against.

### Escalation into `cost_database.json`

```python
from pathlib import Path
from core.pricing.escalation import escalate_cost_database

escalate_cost_database(
    input_path=Path("config/cost_database.json"),
    output_path=Path("config/cost_database_escalated.json"),
    base_period="2026-01",
    target_period="2026-04",
)
```

What it does:

1. Reads every CSI entry from `cost_database.json`.
2. Picks the PPI series that best maps to that entry via, in order:
   - exact CSI-section override (e.g. `06 10 00` → `WPU0811` softwood lumber);
   - keyword match in the description (`drywall` → `WPU102201`);
   - CSI-division fallback (any `26 xx xx` → `WPU102301` copper wire);
   - generic `WPUSI012011` (Inputs to construction industries).
3. Computes `factor = ppi(target) / ppi(base)`.
4. Multiplies `unit_cost` by `factor` and writes a new file with three audit fields:
   - `escalated_from_period`
   - `escalation_factor`
   - `ppi_series_used`

`cost_database_escalated.json` is gitignored (regenerable artifact) so the diff doesn't churn on each refresh.

Idempotent: if `target_period == base_period`, factor = 1.0 and entries pass through unchanged save for the audit fields.

---

## API key registration (free, < 5 minutes each)

All three are **free with email registration**. None require payment, identity verification, or organization affiliation.

| Key | Where to register | Notes |
|---|---|---|
| `BLS_API_KEY` | https://data.bls.gov/registrationEngine/ | Raises BLS daily quota from 25 → 500. Required for the OEWS (60-series) pull. Without it, `bls_ppi` still works rate-limited. |
| `FRED_API_KEY` | https://fred.stlouisfed.org/docs/api/api_key.html | Required for the FRED source. No real rate limit. |
| `EIA_API_KEY` | https://www.eia.gov/opendata/register.php | Required for the EIA source. ~5000 req/hour soft cap. |

Place keys in `.env` at the repo root (gitignored). NEVER commit keys to the repo. NEVER paste keys into chat with an AI model. See workspace rule `01-secrets-and-data.mdc`.

---

## Adding a new source

1. **Confirm license + ToS first.** No new source ships until both are documented in the adapter module's docstring. See `firm/playbooks/pricing-data-sources.md#trust-and-license` below.
2. Subclass `PricingSource` (`core/pricing/sources/base.py`). Implement `fetch(series_ids, **filters)` and `default_series()`. Set `name`, `requires_env_vars`, `license_str`, `homepage_url`.
3. Use `self.http_get(url, params=...)` / `self.http_post_json(url, body)`. Both are TLS-verified, time-bounded, polite-UA, and disk-cached for 24h.
4. Return one `PricingSnapshot` per observation. Use `source=self.name`. Always populate `license`, `source_url`.
5. **Never** put an API key into `PricingSnapshot.raw`. The cache layer hashes the URL (which may contain the key) into the cache filename, but the snapshot itself is committed alongside everything else.
6. Add a `tests/test_pricing_sources_<name>.py` with `httpx.MockTransport` fakes. Run offline.
7. Wire the new source into `scripts/refresh_pricing.py`'s `ALL_SOURCES` dict.
8. Add a row to the registry table at the top of this file.

---

## Trust and license

**Every source we integrate must be public-domain or compatible-license**, and the license must be cited in each adapter's docstring AND in every snapshot's `license` field. We never:

- Scrape behind a login wall.
- Bypass robots.txt or rate limits.
- Re-publish a paywalled dataset.
- Train downstream models on a source whose license forbids derivative work.

| Source | License | Citation requirement |
|---|---|---|
| BLS PPI / OEWS | U.S. Public Domain — Bureau of Labor Statistics | https://www.bls.gov/bls/linksite.htm — attribution recommended, not required |
| FRED | FRED® terms — Federal Reserve Bank of St. Louis | https://fred.stlouisfed.org/legal/ — attribution required |
| EIA | U.S. Public Domain — Energy Information Administration | https://www.eia.gov/about/copyrights_reuse.php — attribution recommended |
| Davis-Bacon (SAM.gov) | U.S. Public Domain — DOL WHD | https://sam.gov/about/policies/terms-of-use — attribution recommended |
| TX TWC prevailing wage | State of Texas public record | https://www.twc.texas.gov/twc-website-privacy-and-security-policy — attribution recommended |
| GSA Schedule catalogs | U.S. Public Domain — GSA | https://www.gsaadvantage.gov/advantage/text/footer/disclaimer.do — attribution recommended |
| TX SmartBuy / ESBD | State of Texas public record | Comptroller website terms apply |
| HD Pro / Lowe's for Pros | **Retailer-proprietary; public prices only** | Each retailer's ToS prohibits automated scraping of the catalog at scale. Phase C closure ships the adapters with bounded per-call SKU lists and a 24h disk cache; **degrade-to-empty on Akamai/CAPTCHA is the documented posture, not a bug**. See "Home Depot Pro / Lowe's Pro retail catalog" section below for the full license / fragility / future-Phase-D-pivot writeup. Low-volume estimating spot-check use only — never bulk redistribution. |
| ENR CCI / AGC / Turner BCI / NAHB | Publisher-proprietary; attribution required, redistribution forbidden | Cite source URL in every snapshot |

---

## Caveats

- **CWICR (the existing 55k-row open cost-database matcher under `core/pricing/cwicr_matcher.py`) is composite — Labor + Material + Equipment in one number.** It is NOT directly comparable to a BLS PPI material-only index. Don't mix CWICR rows and PPI-escalated rows on the same line; pick one source per entry.
- **BLS PPI is for tracking inflation, NOT for setting absolute prices.** PPI series are dimensionless index numbers anchored to a base year (typically 1982 = 100, or 1990 = 100 depending on series). The escalation engine uses index *ratios* — `ppi(target) / ppi(base)` — to scale `cost_database.json` entries, never to set them in absolute dollars.
- **OEWS wages are the median hourly mean across the metro, NOT trade-union or Davis-Bacon prevailing rates.** For federal-funded work (Davis-Bacon Act, McNamara-O'Hara Service Contract Act), pull the WD via `core/pricing/sources/davis_bacon.py` instead. For state-funded TX work, parse the per-project WD PDF that arrives with the solicitation via `tx_prevailing_wage.py` — see the **Structural Note — Texas Prevailing Wage** below for why there is no centralized TWC per-county feed to point at.
- **EIA PADD3 retail fuel is a regional average for the entire Gulf Coast (TX, LA, MS, AL, AR, NM)**, not a Texas-only number. For a Houston / Dallas / Austin spot price, manual lookup on EIA's interactive map remains necessary.
- **Davis-Bacon WDs change mid-year via modifications.** A WD pulled in Q1 may be superseded by Q3. Always re-pull at bid time using `scripts/refresh_pricing.py --sources davis_bacon ...`.
- **Each free API has a daily quota.** The 24h HTTP cache prevents accidentally re-running the refresher 10 times in a day from exhausting them. Honor the cache; if you need to bypass, delete the specific entry under `config/pricing_snapshots/_http_cache/<source>/`.

---

## Structural Note — Texas Prevailing Wage

> **Why this section exists.** A previous roadmap entry assumed TWC publishes a centralized per-county prevailing-wage PDF directory that we could auto-crawl. **That premise was wrong.** The `par_pricing_twc` worker that tried to crawl such a directory errored with `[invalid_argument]` because the directory does not exist. Investigation surfaced the statutory framework below; this note is the durable record so the mistake is not repeated.

### The statutory framework

Under **Tex. Gov't Code Ch. 2258 ("Prevailing Wage Rates")**, prevailing wage on a Texas public-works contract is set by the **individual procuring public body** (the contracting state agency, university system, county jail authority, or political subdivision) — **not** by the Texas Workforce Commission centrally. Each agency must determine and publish the general prevailing rate of per diem wages in the locality for each craft or type of worker called for, **as part of each solicitation**, and incorporate that schedule into the contract.

Practical implications:

- **TWC does NOT publish a centralized per-county wage-determination repository.** There is nothing analogous to SAM.gov's federal Davis-Bacon WD library at the state level. TWC publishes occupational wage *statistics* (OEWS-style), which are statistical averages, **not** Ch. 2258 prevailing-wage determinations.
- A "Tom Green County prevailing wage as of 2026-Q2" PDF does not exist as a single document — only the WD schedules that individual TX state agencies attached to their active 2026-Q2 Tom Green County solicitations exist.
- Any roadmap entry that referenced a "TWC per-county wage PDF auto-downloader" was based on that faulty premise and is **deprecated**.

### Federal Davis-Bacon is different — it IS centralized

The federal Davis-Bacon Act (40 U.S.C. § 3142) routes through the U.S. Department of Labor Wage and Hour Division, which publishes active WDs in the **SAM.gov Wage Determination library**. That centralized repository is what `core/pricing/sources/davis_bacon.py` adapts. For federally-funded TX work (federal contracts, federal-aid highway projects, HUD-assisted projects, etc.), `davis_bacon.py` is the right entry point — not `tx_prevailing_wage.py`.

### The correct workflow for TX state-agency solicitations

1. **WD PDF arrives with the solicitation** as an attachment to the RFP / RFQ / CSP / RFCSP / IFB. It is the issuing agency's Ch. 2258 wage schedule for that specific procurement, locality, fiscal year, and trade scope.
2. **Operator drops the PDF** into the bid workspace under `bids/<slug>/wage-determination/`.
3. **Parse with `core/pricing/sources/tx_prevailing_wage.py`** (`fetch_from_pdf(pdf_path, county=..., year=...)` or `parse_wage_table_text(...)` for already-extracted text) to extract trade × hourly rate rows into `PricingSnapshot`s.
4. **Tag the snapshot** with the source solicitation number, county, fiscal year, and issuing agency (today via `series_id` + `region` + `period`; consider a structured `solicitation` field in a future schema bump).
5. The snapshot then participates in the **same escalation + CWICR matching workflow** as the centralized federal Davis-Bacon snapshots — it is just sourced per-project rather than pulled from a central library.

### Future enhancement — per-agency WD harvester (NOT in current scope)

A future enhancement would be a **per-agency** harvester that scrapes the active-solicitation pages of the major Texas procuring agencies and extracts the WD PDFs they attach. Candidate target agencies, in rough order of TX public-works volume:

- **TxDOT** (Texas Department of Transportation) — highway, bridge, traffic-control projects.
- **TFC** (Texas Facilities Commission) — state-office construction and renovation.
- **TBPC** (Texas Building & Procurement Commission, historical predecessor to TFC for some scopes).
- **TWDB** (Texas Water Development Board) — water/wastewater infrastructure.
- **University systems** — UT System, Texas A&M System, Texas Tech System, University of Houston System Office of Facilities Planning & Construction.
- **Large municipalities** — City of Houston, Dallas, San Antonio, Austin, Fort Worth, El Paso.
- **Large counties** — Harris, Dallas, Bexar, Travis, Tarrant (jail authorities, county-facility projects).
- **TDCJ** (Texas Department of Criminal Justice) — correctional facility construction.
- **HHSC** (Health and Human Services Commission) — state hospital and supported-living-center projects.

A skeleton placeholder for this work lives at `core/pricing/sources/tx_agency_wd.py` so the future shape is explicit and easy to find. **No HTTP fetching is implemented** — the placeholder documents the concept and raises `NotImplementedError` if invoked. This is documentation-as-code: the right time to build the harvester is when there is concrete demand from > 3 active TX state-agency bids per quarter, not before.

### Bottom line

- **`tx_prevailing_wage.py` works correctly for its real use case** — parsing the per-project WD PDF that arrives with each TX state-agency solicitation.
- **There is no centralized TWC source to point a Phase B-full auto-downloader at.** That branch of the roadmap is closed by statute, not by engineering scope.
- **Federal Davis-Bacon (`davis_bacon.py`) is the centralized one** for federally-funded work.
- The per-agency harvester is the only future-direction worth pursuing for additional TX coverage, and only when bid volume justifies it.

---

## Future work

| What | Why | When |
|---|---|---|
| ~~Phase B-full: TWC PDF auto-download~~ | **DEPRECATED** — based on faulty premise; no centralized TWC per-county WD source exists. See "Structural Note — Texas Prevailing Wage" above. | n/a (closed) |
| Per-agency TX WD harvester (TxDOT, TFC, TWDB, university systems, large municipalities) | Pull per-project WD PDFs from major TX procuring agencies' active-solicitation pages | Future — placeholder at `core/pricing/sources/tx_agency_wd.py`; pursue when > 3 active TX state-agency bids/quarter warrant it |
| Phase B-full: GSA Advantage CSV auto-download | Pulls catalog without manual step | Highest-value next step |
| ~~Phase C: TX SmartBuy / ESBD scraper~~ | **Shipped** — see "TX SmartBuy Historical Awards" section below | n/a (closed; shipped 2026-05-28) |
| ~~Phase C: HD Pro / Lowe's pro catalog~~ | **Shipped** — see "Home Depot Pro / Lowe's Pro retail catalog" section below | n/a (closed; shipped 2026-05-28; ships behind documented Akamai/CAPTCHA fragility) |
| Phase D: 3rd-party catalog aggregator | Replace direct retailer scraping with a license-clean aggregator (Datalink, Build.com, similar) so retail-floor pricing is reliable at refresh time without anti-bot fragility | After confirming bid-team demand for retail-floor signal AND securing a redistribution-licensed data feed |
| ~~Phase C: ENR / AGC / Turner PDF parsers~~ | **Shipped** — see Construction Cost Index section below | n/a (closed; CCI adapters shipped 2026-05-28) |
| Phase C-full: NAHB Cost of Constructing a Home annual PDF | Residential cost breakdown cross-check | Deferred — annual cadence + low marginal vs BLS PPI |
| Phase C-full: ENR / AGC / Turner historical archive parsers | Backfill full historical series (currently only latest headline) | After more bid-pricing demand confirms the marginal value vs BLS PPI |
| **Tier 2: RSMeans / Gordian** | Production-grade composite cost DB | Decision pending calibration data + commercial approval |
| **Tier 3: BPC internal cost DB** | Eliminates external dependency | Started when BPC has > 12 months of internal cost capture; see `firm/compliance/material-suppliers.md` |

---

## Construction Cost Index macro escalators (Phase C — shipped 2026-05-28)

The three CCI adapters (`enr_cci`, `agc_cci`, `turner_cci`) provide macro escalation signals **complementary to**, not replacing, the per-CSI BLS PPI integration:

- **BLS PPI** (Phase A) tracks per-commodity producer prices. Use for entry-by-entry escalation in `core/pricing/escalation.py` — the keyword + CSI-section + division fallback chain already in production.
- **ENR / AGC / Turner CCI** track a single macro index that aggregates labor + materials + market conditions. Use as a **cross-check** on a per-bid total escalation factor, or as a uniform multiplier when no per-CSI signal is available.

| Adapter | Series id | Cadence | Free-tier coverage | Period format | Snapshot path |
|---|---|---|---|---|---|
| `enr_cci` | `national-20city` | Monthly | Headline 20-city composite only; per-city + history are subscription-gated | `YYYY-MM` | `config/pricing_snapshots/enr_cci/national-20city/` |
| `agc_cci` | `national` | Monthly (underlying PPI) | Landing-page headline only; Inflation Alert PDFs are linked but not parsed | `YYYY-MM` | `config/pricing_snapshots/agc_cci/national/` |
| `turner_cci` | `national` | Quarterly | Latest quarter only; historical archive on the page is not yet parsed | `YYYY-QN` | `config/pricing_snapshots/turner_cci/national/` |

### How the CCIs differ from BLS PPI

| Dimension | BLS PPI | ENR / AGC / Turner CCI |
|---|---|---|
| Scope | Per-commodity (lumber, steel, gypsum, ...) | National macro composite |
| Granularity | 15 curated series, each mapped to specific CSI sections | One number per period, applies uniformly |
| Free-tier history | Full ≥ 10-year history per series | Latest headline value only (Phase C) |
| Use in escalation engine | Already integrated; per-entry factor | Not yet wired in to escalation engine (see "Optional escalation hook" below) |

### Access-posture audit (verified 2026-05-28)

- **ENR `/economics`** — landing page reachable; methodology + cost-report links public; full historical CSV requires a subscription. The headline 20-city CCI appears in the body text of the current cost-report article and is parsed by regex anchor against "20-City Average Construction Cost Index" / "Construction Cost Index" / "CCI". A year-range filter (1900–2100) skips date-like numbers so values such as 14021.34 are not confused with adjacent year strings.
- **AGC `/learn/construction-data`** — landing page reachable; lists Data Digest + Construction Industry Outlook + Producer Prices & Employment Costs tables. AGC's headline framing varies (sometimes a PPI index value, sometimes a YoY percent change). When the page only exposes a percent-change figure the adapter returns an empty list with a logged warning rather than persist a misleading snapshot. The Construction Inflation Alert PDF is publicly downloadable but not yet parsed — that is a follow-up slice.
- **Turner `/cost-index`** — landing page reachable; quarterly TBCI value appears in the current quarter's article body with a stable "NTH QUARTER YYYY" heading convention going back to 2006. Latest value is parsed by regex anchor against "Turner Building Cost Index" / "TBCI" / "Building Cost Index".
- **Bureau of Reclamation aggregator** (`https://www.usbr.gov/tsc/techreferences/mands/cci.html`) — the brief flagged this as a potential fallback that publishes ENR / AGC / Turner side-by-side. Live fetch timed out during validation; the URL is documented in `core/pricing/sources/enr_cci.py` as a future-resilience hook but is not currently consulted.

### Failure modes the adapters handle gracefully

- HTTP 4xx / 5xx from any publisher → adapter logs a warning and `fetch()` returns `[]`. The refresh runner is not crashed.
- Page layout changes that move the index value out of regex range → adapter logs "no index value found at <url> — page layout may have changed" and `fetch()` returns `[]`. Operators look up the latest value manually and document the gap.
- Cache hit within 24 hours → no second HTTP call. Cache is keyed by URL alone (no auth headers, no per-account state).
- Unknown `series_id` requested via `fetch(['regional-houston'])` → logged warning + skipped (only the curated series id per adapter is honored on the free tier).

### Optional escalation hook — SHIPPED (2026-05-28)

`core/pricing/escalation.py` now exposes `apply_macro_cci_multiplier(...)` that layers a single uniform `latest_cci / baseline_cci` ratio on top of the per-CSI BLS PPI escalation, with ENR → AGC → Turner fallback. See the **"Macro escalation chain — when to use what"** section below for the full contract and usage guidance. The per-CSI per-entry escalation is unchanged; the macro multiplier is an optional Step 2 that writes to a separate output file (`config/cost_database_escalated_with_cci.json`) so the per-CSI-only and per-CSI + macro outputs can be audited side-by-side.

### Source-of-truth references in the new code

- `core/pricing/sources/_cci_common.py` — shared HTML fetch + caching + index-value / period parsing.
- `core/pricing/sources/enr_cci.py` — ENR adapter.
- `core/pricing/sources/agc_cci.py` — AGC adapter.
- `core/pricing/sources/turner_cci.py` — Turner adapter.
- `tests/test_pricing_sources_{enr,agc,turner}_cci.py` — offline tests via `httpx.MockTransport`.

---

## NAHB Cost of Constructing a Home — residential macro complement (Phase C — shipped 2026-05-28)

The three commercial CCI adapters above (ENR / AGC / Turner) track non-residential / mixed escalation. **`nahb_construction_cost` complements them with a residential single-family cross-check** — the NAHB Cost of Constructing a Home special-study series, conducted biennially in recent cycles (2019 / 2022 / 2024; 2026 publication expected).

### How it differs from the three CCIs

| Dimension | ENR / AGC / Turner CCI | NAHB Cost of Constructing a Home |
|---|---|---|
| Unit | Dimensionless **index** | **Absolute USD** per typical home |
| Scope | Commercial / mixed / nonresidential | **Single-family residential** |
| Cadence | Monthly (ENR / AGC) or quarterly (Turner) | **Biennial** (recent cycles) |
| Period format | `YYYY-MM` / `YYYY-QN` | `YYYY` |
| Macro-escalator role | Wired into `apply_macro_cci_multiplier(...)` as ratios | NOT wired into the macro hook (different unit) |
| Cross-check role | Per-bid total-cost ratio vs commercial macro | Per-bid total-cost level vs residential single-family |

### When to use

- **Residential single-family bids** — use NAHB as the macro plausibility check on the total construction cost figure. If the BPC estimate for a typical-spec home lands wildly outside the NAHB latest year's national average (after adjustment for SF and finish level), revisit the estimate before bid submission.
- **Cross-checking commercial CCI escalation** — NAHB's biennial figure gives an independent national signal that is helpful when ENR/AGC/Turner are stale (e.g. AGC's headline is currently percent-change-only).

### Free-tier access posture (verified 2026-05-28)

- NAHB publishes each survey's article under `housing-economics-plus/special-studies/special-studies-pages/cost-of-constructing-a-home-in-YYYY` and a free PDF special study. URLs are year-specific; **the brief's pre-2024 URLs in earlier roadmap notes were 404 as of 2026-05-28**. The adapter pins to the 2024 article URL and bumps when 2026 publishes.
- The adapter **parses "Total Construction Cost $NNN,NNN" + the most recent 4-digit year** from the article body. If the live HTTP fetch fails (4xx / 5xx / unparseable HTML / layout change), it **falls back to a hardcoded historical table** covering every published survey since 1998 (1998 / 2002 / 2004 / 2007 / 2009 / 2011 / 2013 / 2015 / 2017 / 2019 / 2022 / 2024). The hardcoded table is provenance-tagged in the snapshot's `raw["provenance"]` field as `"hardcoded historical fallback"` vs `"live article parse"`, so operators can tell at a glance whether they got a fresh fetch.
- `fetch_history()` is implemented from the hardcoded table — the article URL convention is too inconsistent across years for a generic per-year scraper to be reliable.

### Snapshot shape

```
source:        nahb_construction_cost
series_id:     residential-single-family-national
label:         NAHB Cost of Constructing a Home (national, single-family)
unit:          USD                            # NOT "index"
value:         428215.0                       # total construction cost
region:        US
csi_division:  null                           # whole-house aggregate
naics:         236115                         # New Single-Family Housing
period:        "2024"                         # study year, biennial
license:       NAHB attribution required
source_url:    https://www.nahb.org/.../cost-of-constructing-a-home-in-2024
raw.provenance: "live article parse" | "hardcoded historical fallback"
```

### Source-of-truth references for the NAHB adapter

- `core/pricing/sources/nahb_construction_cost.py` — adapter + hardcoded historical table.
- `core/pricing/sources/construction_indexes.py` — backward-compat re-export shim (the Worker P stub used to live here; the real class is now in `nahb_construction_cost.py`).
- `tests/test_pricing_sources_nahb.py` — offline tests via `httpx.MockTransport`.

---

## Macro escalation chain — when to use what (Phase C — shipped 2026-05-28)

The escalation engine now supports a **two-step macro escalation chain**:

1. **Step 1 — per-CSI BLS PPI escalation.** `escalate_cost_database(...)` in `core/pricing/escalation.py`. Reads `config/cost_database.json`, picks a BLS PPI series per entry via the CSI-section / keyword / division fallback chain, applies `ppi(target) / ppi(base)` per entry. Writes `config/cost_database_escalated.json`.
2. **Step 2 (optional) — macro CCI multiplier.** `apply_macro_cci_multiplier(...)` in `core/pricing/escalation.py`. Reads the per-CSI escalated DB, applies a single uniform `latest_cci / baseline_cci` multiplier across every entry. Writes `config/cost_database_escalated_with_cci.json` (input file untouched). Source fallback chain: **`enr_cci` → `agc_cci` → `turner_cci`** (configurable; first source with on-disk snapshots wins).

The two outputs are kept side-by-side so the bid reviewer can compare per-CSI-only escalation (Step 1) against the per-CSI + macro CCI cross-check (Steps 1 → 2).

### When to use Step 2 (macro CCI multiplier)

| Situation | Apply macro CCI? | Why |
|---|---|---|
| Per-CSI BLS PPI coverage is dense and current (commodity bids) | **No** | Per-entry signal is already specific; layering a macro multiplier may double-count market conditions. |
| Bid spans a long baseline-to-target window (> 24 months) | **Yes** | BLS PPI captures commodity drift; CCI captures the cumulative labor + market drift that PPI misses. |
| Bid sensitive to total contract value (cost-plus, CMAR, etc.) | **Yes** | A second independent signal hardens the total-cost cross-check. |
| Mixed-use or unusual scope where per-CSI mapping is weak (lots of `99 99 99` generic-fallback hits) | **Yes** | Per-CSI factor is mostly the generic-construction-inputs PPI anyway; layering a CCI macro signal is a meaningful improvement. |
| Residential single-family bids | **Yes, with NAHB cross-check** | Step 2 with `enr_cci` is still appropriate; additionally compare the total escalated cost to the NAHB latest survey value (residential plausibility window). |

### Usage from Python

```python
from pathlib import Path
from core.pricing.escalation import (
    escalate_cost_database,
    apply_macro_cci_multiplier,
)

# Step 1 — per-CSI BLS PPI escalation
escalate_cost_database(
    input_path=Path("config/cost_database.json"),
    output_path=Path("config/cost_database_escalated.json"),
    base_period="2024-01",
    target_period="2026-04",
)

# Step 2 (optional) — macro CCI multiplier on top
apply_macro_cci_multiplier(
    escalated_db_path=Path("config/cost_database_escalated.json"),
    base_period="2024-01",                   # match the CCI period format:
                                              # ENR/AGC: YYYY-MM; Turner: YYYY-QN
    cci_source="enr_cci",                     # default; first source tried
    fallback_sources=("agc_cci", "turner_cci"),
    # out_path defaults to config/cost_database_escalated_with_cci.json
)
```

### Function semantics

- **Multiplier formula:** `multiplier = latest_cci_value / baseline_cci_value`. Applied uniformly to every cost-DB entry's `unit_cost`.
- **Baseline lookup:** exact-period match first; falls back to the most recent snapshot whose period is lexicographically ≤ `base_period`. Raises `EscalationMissingBaseline` if no usable baseline exists (i.e. all available snapshots are newer than `base_period` or all baseline candidates have non-positive values).
- **Latest lookup:** the snapshot with the lexicographically greatest period in the chosen source's history.
- **Source fallback:** tries `cci_source` first (default `enr_cci`); if that source has zero snapshots on disk (or in the injected `snapshots_by_source` for tests), falls through `fallback_sources` in order. Raises `PricingSourceUnavailable` (from `core.pricing.sources._cci_common`) if every source in the chain has zero snapshots.
- **Period format constraint:** the caller's `base_period` must match the chosen source's period cadence — `YYYY-MM` for ENR/AGC, `YYYY-QN` for Turner. Cross-format lookup ("2024-01" against a Turner-only history of "2024-Q1") will not match exactly and will fall through to the prior-period lookup; pick the format that matches the source you expect to win.
- **Audit fields added to every output entry:** `macro_cci_multiplier`, `macro_cci_source`, `macro_cci_baseline_period`, `macro_cci_latest_period`. The per-CSI escalation's audit fields (`escalation_factor`, `ppi_series_used`, `escalated_from_period`) survive untouched.
- **`_meta` annotations:** `macro_cci_applied_at`, `macro_cci_multiplier`, `macro_cci_source`, `macro_cci_baseline_value`, `macro_cci_latest_value` are appended to the output's `_meta` dict for traceability.
- **Idempotency:** running twice with the same inputs produces byte-identical outputs (no clock-dependent fields are written into per-entry rows). The function is safe to re-run.

### NAHB is intentionally NOT in the fallback chain

`apply_macro_cci_multiplier` operates on **ratios** of dimensionless index values. NAHB Cost of Constructing a Home publishes **absolute USD** per home, not an index. While a NAHB-based ratio is meaningful for a residential-only cross-check (see the NAHB section above), it is a different statistical object than the CCI ratios — mixing them in a single macro-multiplier chain would silently introduce a residential bias on a commercial-leaning DB. Use NAHB as a separate plausibility check on the total escalated cost instead.

### Source-of-truth references for the macro chain

- `core/pricing/escalation.py` — both `escalate_cost_database(...)` (Step 1) and `apply_macro_cci_multiplier(...)` (Step 2). `EscalationMissingBaseline` exception is defined here.
- `tests/test_pricing_escalation.py` — Step 1 tests.
- `tests/test_pricing_escalation_cci.py` — Step 2 tests (multiplier, fallback chain, idempotency, full-chain integration smoke).

---

## TX SmartBuy Historical Awards — competitive intel (Phase C — shipped 2026-05-28)

The macro CCI/PPI escalators above tell you **trend** (how much commercial construction inputs have inflated). The TX SmartBuy adapter tells you **level** — what actually got paid on a real, named TX state-agency contract.

### What this source provides

For each awarded solicitation posted on the Comptroller's Electronic State Business Daily (ESBD), one `PricingSnapshot` per (solicitation, awarded-vendor) pair carrying:

- **Vendor name** — the winning contractor (e.g. "Carr EFA Joint Venture").
- **Award amount** — lump-sum award value in USD.
- **NAICS code** — when the agency populates it on the detail page (TAMU System / university construction is typically 236220 Commercial & Institutional Building).
- **Agency** — issuing entity (e.g. Angelo State University, TAMU System, TxDOT).
- **Award date / period** — published as `YYYY-MM` (or `YYYY` if month not parseable).
- **Performance period** — start/end dates of the contract term, stored in `raw["performance_period"]`.
- **Source URL** — direct link to the public ESBD detail page for audit / re-verification.

### How it complements CCI/PPI

| Question the bid-team is asking | Where the answer comes from |
|---|---|
| "How much have construction inputs escalated since baseline?" | BLS PPI (per-CSI) + ENR/AGC/Turner CCI (macro) |
| "What did a *similar* TX state agency contract just pay for *similar* scope?" | **TX SmartBuy historical awards** |
| "Is BPC's intended price-point in line with the recent NAICS-236220 median for this agency?" | **TX SmartBuy** (filter `naics="236220"`, compute median of `value`) |
| "Did this incumbent vendor bid this contract type before, and at what level?" | **TX SmartBuy** (group by `raw["vendor"]`, look at history) |

Macro escalators alone tell you that costs went up ~5% YoY. Award history tells you that the actual winning bids on UT-System / TAMU-System Commercial & Institutional Building work in 2025 ran $4–12M for renovation scopes and $20–60M for ground-up — orders of magnitude more useful when calibrating a BPC bid.

### Access posture (verified 2026-05-28)

- Public, no auth required. The brief verified `https://www.txsmartbuy.gov/esbd/26-007RFCSP` was accessible without credentials earlier in this project.
- Polite User-Agent (inherited from `core/pricing/sources/base.py::build_client`).
- 24h disk cache via `core/pricing/sources/_cci_common.http_get_text`. Cache lives under `config/pricing_snapshots/_http_cache/tx_smartbuy_awards/` (gitignored).
- No bulk-download attempt. `fetch_recent_awards()` walks **one** listing page by default; the `limit` argument caps the per-call work (default 50 via `scripts/refresh_pricing.py`).
- No new third-party dependencies — `bs4` was explicitly NOT added. Parsing uses regex over a tag-stripped text view of the page, same family as the `_cci_common.find_index_value` anchor-proximity approach used by ENR/AGC/Turner.

### Snapshot shape

```
source:        tx_smartbuy_awards
series_id:     "<sol>"               # single-vendor
               "<sol>--<index>"      # multi-vendor (double-hyphen separator)
label:         "ESBD <sol> awarded to <vendor>"
unit:          "USD"                 # absolute dollars — NOT an index
value:         <awarded amount>      # lump-sum total
region:        "TX"
csi_division:  null                  # not derived (optional per brief)
naics:         "236220"              # when present on the page; else null
period:        "2025-12"             # YYYY-MM; "YYYY" fallback
license:       State of Texas public record — TX SmartBuy / ESBD
source_url:    https://www.txsmartbuy.gov/esbd/<sol>
raw:           {vendor, award_amount_usd, award_amount_raw, award_date_raw,
                agency, naics, performance_period, vendor_index,
                vendor_count, solicitation_number}
```

### Limitations

- **TX-only.** No federal, no other state. For federal-funded work cross-reference with `davis_bacon.py`.
- **Awards typically appear 30–90 days after the response date.** ESBD updates the detail page when the award notice is issued — there is a lag between bid-due date and the snapshot becoming available.
- **Some agencies redact award amounts** (especially negotiated contracts under Tex. Gov't Code 2156.121, the state equivalent of FAR Part 13.5 sole-source / competitive-negotiation cover). When the dollar figure is redacted or marked "Confidential", the adapter logs and skips that vendor rather than emitting a misleading snapshot.
- **Multi-vendor awards may not split amounts cleanly.** Some solicitations publish a single aggregate dollar figure across all awardees and leave the per-vendor split to the contract negotiation phase. In that case the adapter emits one snapshot per vendor with the aggregate amount duplicated — operators should manually review `raw["vendor_count"]` and split if a per-vendor figure is later disclosed.
- **HTML structure is not a stable API.** The Comptroller has changed the ESBD layout in the past. The parser uses multiple label spellings per field ("Awarded Vendor:" / "Vendor:" / "Awardee:"; "Award Amount:" / "Awarded Amount:" / "Contract Amount:") and falls back gracefully (returns `[]` for that page, refresh runner is never crashed). If a structural change moves the labels entirely, operators look up the award manually on ESBD and extend the anchor lists in `tx_smartbuy_awards.py::VENDOR_LABELS` / `AMOUNT_LABELS` / `AWARD_DATE_LABELS`.
- **NAICS field is not always populated.** When the agency omits it, the snapshot's `naics` is `null` — downstream filtering must tolerate that.
- **Single-page listing only.** `fetch_recent_awards()` walks the first listing page; multi-page pagination is a future enhancement (see "Future work" below).

### How to use the data in bid prep

1. **Calibrate against same-NAICS history.** Pull the last 25–50 awarded snapshots filtered by the bid's NAICS code:

   ```python
   from core.pricing.sources.tx_smartbuy_awards import TXSmartBuyAwardsSource
   from statistics import median

   with TXSmartBuyAwardsSource() as src:
       comparables = src.fetch_recent_awards(limit=50, naics="236220")
   amounts = sorted(s.value for s in comparables)
   print(f"n={len(amounts)} median=${median(amounts):,.0f} "
         f"p25=${amounts[len(amounts)//4]:,.0f} "
         f"p75=${amounts[3*len(amounts)//4]:,.0f}")
   ```

2. **Compare BPC's intended price-point.** A bid that lands wildly above the recent p75 or wildly below the p25 of the same-NAICS award distribution deserves a second look before submission — there is usually a scope-misread or a missed allowance behind that gap.

3. **Track incumbent behavior.** Filter by `raw["vendor"]` to see what a given incumbent has bid (and won) for the issuing agency in the last 12–24 months. Useful for go/no-go: if an incumbent has won three of the last three at this agency on similar scope, the GP-margin call for a new entrant becomes part of the bid strategy.

4. **Cross-check the macro escalation.** Multiply a baseline-period award through `apply_macro_cci_multiplier(...)` (Step 2 above) and compare against the latest award on similar scope. A large divergence flags either an agency-specific market move or a parser-stale macro snapshot — both worth verifying before bid lock.

### CLI

```powershell
# Refresh the most-recent 50 awarded solicitations (default).
.venv\Scripts\python.exe scripts\refresh_pricing.py --sources tx_smartbuy_awards

# Or via the Phase C shortcut (includes the CCI adapters + NAHB).
.venv\Scripts\python.exe scripts\refresh_pricing.py --phase c
```

### Source-of-truth references

- `core/pricing/sources/tx_smartbuy_awards.py` — adapter, HTML helpers, anchor lists.
- `core/pricing/sources/_cci_common.py::http_get_text` — shared 24h HTTP-text cache.
- `tests/test_pricing_sources_tx_smartbuy_awards.py` — offline tests via `httpx.MockTransport` (single-vendor, multi-vendor, missing-amount, cancelled, 4xx/5xx, NAICS filter, limit, dollar-format variants, period-format variants, round-trip serialization, listing-page parsing).

### Future work (parked)

- **Multi-page pagination.** Walk past the first listing page to backfill > 25 awards per refresh. Today `fetch_recent_awards(limit=50)` honors the limit at the parsing layer but only sees one page; raising the listing throughput is a follow-up slice.
- **CSI-section mapping from solicitation title.** Today `csi_division` is left null. A future enhancement could keyword-map common scopes (e.g. "Office Renovation" → CSI Division 09 finishes; "Roof Replacement" → CSI 07 thermal & moisture protection) so the awards become directly comparable to BPC's per-CSI cost database. Out of scope for the initial shipping slice because the mapping is judgment-heavy and easier reviewed manually at bid prep time.
- **Per-agency harvester integration.** The future TX agency WD harvester (`tx_agency_wd.py` placeholder) overlaps with the TX SmartBuy data shape; if both ship, deduplicate at the snapshot layer rather than the source layer.

---

## Home Depot Pro / Lowe's Pro retail catalog (Phase C closure — shipped 2026-05-28)

The macro CCI/PPI escalators tell you **trend** (commercial input inflation YoY). The TX SmartBuy adapter tells you **level** for TX state-agency awards. The HD Pro / Lowe's Pro catalog adapters fill in the third axis: **the user-actionable retail floor** — what a project manager or estimator can walk into a store and pay today for a specific SKU.

This is complementary to PPI (broad market index) and CWICR (open contractor cost DB) — neither of those tells you that a 5 gal bucket of joint compound is $19.99 at the Carrollton HD this week.

### What these adapters provide

For each SKU in the configured starter list, one `PricingSnapshot` per successful parse carrying:

- **Item ID / Item Number** — the retailer's product key (`series_id`).
- **Title** — product description (`label`).
- **Brand** — manufacturer / private label.
- **Price** — current public catalog price in USD (`value`).
- **Unit-of-measure** — verbatim from the catalog (`unit`); e.g. `"each"`, `"box of 100"`, `"case of 50"`, `"1 lb"`, `"gallon"`. Falls back to `"each"` when not parseable.
- **Model / MFR Number** — manufacturer part number (`raw["mpn"]`).
- **Zip code** — store-availability scope (`region` + `raw["zip_code"]`); defaults to `75001` (Carrollton, TX / Dallas-Fort Worth metro).
- **Source URL** — direct link to the public PDP for re-verification.

Snapshots are persisted under `config/pricing_snapshots/hd_pro/<sku>/<YYYY-MM-DD>.json` and `config/pricing_snapshots/lowes_pro/<sku>/<YYYY-MM-DD>.json`. Period is the **scrape date** (full ISO date, not just the month) because retail prices fluctuate hourly during promo seasons and a daily snapshot cadence is the right grain.

### URL patterns

| Retailer | URL pattern | Notes |
|---|---|---|
| Home Depot | `https://www.homedepot.com/p/<sku>` | Real PDP URLs include a marketing slug between `/p/` and the SKU; the bare-SKU form redirects to the canonical page. We use the bare form so we don't need to pre-know the slug. |
| Lowe's | `https://www.lowes.com/pd/<item-number>` | Same posture as HD; bare-Item-Number redirects to the canonical slug page. |

### SKU sourcing strategy

The starter SKU lists live in two places (intentionally — see "Where future SKU lists should be sourced" below for the migration plan):

1. **Module-level `DEFAULT_SKUS`** in each adapter (`core/pricing/sources/hd_pro.py`, `core/pricing/sources/lowes_pro.py`). These are the "everyone gets these by default" lists — 10 SKUs each covering door hardware, paint, drywall, framing lumber, plywood, fasteners, joint compound, gypsum board, roofing felt.
2. **CLI-level `HD_PRO_STARTER_SKUS` / `LOWES_PRO_STARTER_SKUS`** in `scripts/refresh_pricing.py` — same 10 SKUs, but with explicit CSI-section comments so the refresh-runner policy is greppable from the CLI side rather than buried inside the adapter module.

When the refresh runner is invoked the CLI list is what's used; the module-level list is the fallback for ad-hoc scripts that instantiate the adapter directly.

#### Where future SKU lists SHOULD be sourced (NOT YET IMPLEMENTED)

Three migration paths, in rough preference order:

1. **Per-bid CSV** under `bids/<slug>/catalog-skus.csv`. The estimator drops a printed Pro-counter quote into the bid workspace and the refresh runner reads the bid-specific list when running inside the bid context. Natural extension: a `--bid <slug>` flag on `scripts/refresh_pricing.py`.
2. **Per-firm config** under `firm/catalog/hd_pro_skus.csv` and `firm/catalog/lowes_pro_skus.csv` — a curated list of "always refresh these" SKUs that the firm tracks across all bids. Updated by the estimating lead at the start of each fiscal quarter.
3. **Per-CSI mapping** under `firm/catalog/csi_to_skus.json` — links each CSI section (e.g. `08 71 00` Door Hardware) to a list of exemplar SKUs, so a bid takeoff that touches a CSI section automatically pulls fresh prices for the exemplars. Depends on the per-CSI keyword catalog in `core/pricing/escalation.py` being externalized first.

Until those land, the CLI module-level list is the source of truth and is overridable per-call by `HomeDepotProSource(sku_list=[...])` / `LowesProSource(sku_list=[...])`.

### Structural fragility — the elephant in the room

**Both retailers serve product pages behind Akamai-fronted JavaScript shells with bot protection.** A polite `httpx` GET (no JavaScript engine, no cookie / fingerprint mimicry) will most often land on one of:

- A **"Pardon Our Interruption"** CAPTCHA / interstitial page (Distil Networks).
- An **HTTP 403** from Akamai's edge.
- A **200** with the JavaScript shell that, when rendered in a browser, populates from a private GraphQL endpoint we are NOT authorized to call programmatically.
- An **"Access Denied"** page citing an Akamai reference number.

**This is the biggest known limitation of these adapters and is not bypassed.** Honoring `00-global-security.mdc` and the retailer ToS, the adapter **degrades to graceful empty** on any of the above:

1. `fetch()` and `fetch_recent()` swallow per-SKU HTTP errors and anti-bot intercepts, log a warning, and return whatever they could parse (often `[]`). The refresh runner is never crashed.
2. `fetch_one()` raises `PricingSourceUnavailable` on a 4xx / 5xx so a one-off CLI lookup can detect failure.
3. When the response *is* a CAPTCHA / anti-bot page (200-OK HTML carrying one of the known interstitial markers), the adapter logs a warning and skips that SKU rather than emitting a misleading snapshot.

The CAPTCHA marker list lives at module scope (`CAPTCHA_MARKERS`) in each adapter and matches Akamai / Distil / Imperva / generic block pages: `pardon our interruption`, `/_incapsula_resource`, `as you were browsing`, `request unsuccessful. incapsula`, `access denied`, `bot detected`, `captcha verification`, `akamai-edgesuite`, `we want to make sure you're a real person`, `are you a robot`. When a structural change moves the markers, operators look up the latest one manually and extend the list.

### Recommended remediation paths (none implemented in this slice)

In preference order:

1. **Use HD's / Lowe's official supplier or B2B Pro account API.** Both retailers offer Pro-account programs (HD's Pro Xtra, LowesForPros.com) which include a commercial supplier portal in some configurations. Requires a signed Pro account agreement + a documented redistribution clause for estimating use.
2. **Use a 3rd-party catalog aggregator** (Datalink, Build.com, similar) with an explicit license to redistribute pricing for estimating use. This is the cleanest long-term answer and is captured in the "Future work" table above as the Phase D pivot.
3. **Curate a manual SKU CSV per bid.** A project manager walks the Pro counter for the bid scope, exports a printed quote, and the estimator imports it into the bid workspace under `bids/<slug>/catalog-skus.csv`. This is the lowest-tech fallback and is the most realistic posture for current bid volume.

### License + ToS — non-negotiable caveat

The Home Depot Customer Agreement and Lowe's Terms and Conditions of Use both prohibit automated scraping of the catalog at scale. This adapter is intended for **low-volume estimating spot-checks**, NOT for commercial redistribution of the catalog. Concretely:

- **No bulk download.** The SKU list is bounded at construction time (10 SKUs in the starter list). The refresh runner walks them sequentially, each behind a 24h disk cache (`config/pricing_snapshots/_http_cache/hd_pro/`, `.../lowes_pro/`).
- **No re-publish.** Each snapshot persists the canonical product URL so a downstream consumer must follow the link to view the price; the snapshot is an internal estimating record, not a syndicated catalog feed.
- **Polite User-Agent.** Inherited from `core/pricing/sources/base.py::build_client` — same identity as every other Phase A/B/C adapter.
- **No login wall bypass.** Pro-account-gated prices are not scraped; only the public catalog floor is.

If retail catalog use ever moves beyond per-bid spot-check (e.g. into syndicated bid-prep automation), **stop and renegotiate the license posture** before doing so. The Phase D 3rd-party-aggregator pivot is the clean answer; direct scraping at scale is not.

### Snapshot shape

```
source:        hd_pro | lowes_pro
series_id:     "<Item ID | Item Number>"
label:         "<Product title>"
unit:          "<UoM verbatim>"     # "each" / "box of 100" / "1 lb" / ...
value:         <price USD>
region:        "<zip_code>"         # store-availability scope
csi_division:  null
naics:         null
period:        "YYYY-MM-DD"         # scrape date (NOT month)
license:       <retailer>-proprietary; public catalog prices only — low-volume
               estimating use, not commercial redistribution
source_url:    https://www.homedepot.com/p/<sku>  | https://www.lowes.com/pd/<sku>
raw:           {sku_requested, sku_parsed, title, brand, mpn,
                price_raw, price_value_usd, unit_of_measure, zip_code,
                fetched_at}
```

### CLI

```powershell
# Refresh both retail catalogs (uses the starter SKU lists).
.venv\Scripts\python.exe scripts\refresh_pricing.py --sources hd_pro,lowes_pro

# Or via the Phase C shortcut (includes CCI + NAHB + TX SmartBuy + retail).
.venv\Scripts\python.exe scripts\refresh_pricing.py --phase c

# Single-SKU spot check from Python (raises PricingSourceUnavailable on failure).
.venv\Scripts\python.exe -c "from core.pricing.sources.hd_pro import HomeDepotProSource; \
print(HomeDepotProSource().fetch_one('100120362').value)"
```

In production usage today the live fetch will most often return the documented anti-bot intercept and the refresh-runner summary will read `[hd_pro] 0 snapshots returned` / `[lowes_pro] 0 snapshots returned`. **This is expected** — see "Structural fragility" above. The adapter ships its full interface, parsing logic, and tests; production utility unlocks when the Phase D 3rd-party aggregator pivot lands or a per-bid manual SKU CSV is supplied.

### Source-of-truth references

- `core/pricing/sources/hd_pro.py` — Home Depot Pro adapter, parsing helpers, anchor lists, default SKU list.
- `core/pricing/sources/lowes_pro.py` — Lowe's Pro adapter (mirror of `hd_pro`).
- `core/pricing/sources/_cci_common.py::http_get_text` — shared 24h HTTP-text cache.
- `tests/test_pricing_sources_hd_pro.py` — offline tests via `httpx.MockTransport` (47 tests).
- `tests/test_pricing_sources_lowes_pro.py` — offline tests via `httpx.MockTransport` (46 tests).
- `scripts/refresh_pricing.py` — `HD_PRO_STARTER_SKUS` / `LOWES_PRO_STARTER_SKUS` CLI-level constants + elif wiring in `_run_source`.

### Future-refactor note — `_catalog_common.py`

The HTML-parsing helpers in `hd_pro.py` and `lowes_pro.py` are near-identical clones because both retailers use the same `schema.org` `itemprop` microdata vocabulary on their PDPs. A future `core/pricing/sources/_catalog_common.py` could DRY out the meta / itemprop / price / UoM helpers behind a single `parse_product_page(html, *, adapter_name, source_url, ...)` entry point. **Intentionally NOT extracted in this slice** — both adapters ship as self-contained modules so the fragility surface, the per-retailer license / ToS docstring, and the adapter-specific anchor lists stay collocated. **Promote to shared helpers when a third catalog source is added** (most likely: Build.com or another aggregator).

### Phase C completion status

With these two adapters shipped, **Phase C is closed**. The pricing layer now covers:

- **Labor** — BLS OEWS (Phase A) + Davis-Bacon (Phase B) + TX per-project WD parser (Phase B).
- **Materials / PPI** — BLS PPI (Phase A) + FRED (Phase A) + EIA fuel (Phase A).
- **Construction cost indexes** — ENR + AGC + Turner + NAHB (Phase C).
- **Competitive intel** — TX SmartBuy historical awards (Phase C).
- **End-user retail catalog** — HD Pro + Lowe's Pro (Phase C closure).

No remaining Phase C stubs. The next move on the pricing roadmap is Phase D (3rd-party catalog aggregator pivot) or Tier 2 (RSMeans / Gordian commercial license decision) — both gated on demonstrated bid-team demand for the additional signal.

---

**End of playbook.**
