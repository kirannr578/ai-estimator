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
| TX SmartBuy / ESBD award postings | `core/pricing/sources/tx_smartbuy_awards.py` | State of Texas public record | None | Continuous | Historical award amounts for sub-pricing reference | **Phase C — stub** |
| Home Depot Pro / Lowe's for Pros catalogs | `core/pricing/sources/hd_pro_catalog.py` | Retailer-proprietary (public prices only) | None for public pages | On-demand | ~50 high-volume building-material SKUs | **Phase C — stub** |
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
| HD Pro / Lowe's for Pros | **Retailer-proprietary; public prices only** | Each retailer's ToS forbids automated scraping of logged-in content — non-negotiable. Phase C implementation MUST honor robots.txt and rate limits. |
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
| Phase C: TX SmartBuy / ESBD scraper | Historical sub-pricing reference | After GSA Advantage |
| Phase C: HD Pro / Lowe's pro catalog | Spot-check single-SKU pricing | After GSA Advantage; **only if ToS posture clear** |
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

**End of playbook.**
