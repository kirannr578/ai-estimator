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
| TX Workforce Commission prevailing wage | `core/pricing/sources/tx_prevailing_wage.py` | State of Texas public record — TWC | None (PDF download) | Annual per county | Per-county trade × hourly rate from TWC PDFs | **Phase B — partial** (parser ships; auto-download TODO) |
| GSA Schedule price lists | `core/pricing/sources/gsa_schedule.py` | U.S. Public Domain — GSA | None | Quarterly | Construction materials catalogs (56V, 03FAC, 23V) | **Phase B — partial** (parser ships; auto-download TODO) |
| TX SmartBuy / ESBD award postings | `core/pricing/sources/tx_smartbuy_awards.py` | State of Texas public record | None | Continuous | Historical award amounts for sub-pricing reference | **Phase C — stub** |
| Home Depot Pro / Lowe's for Pros catalogs | `core/pricing/sources/hd_pro_catalog.py` | Retailer-proprietary (public prices only) | None for public pages | On-demand | ~50 high-volume building-material SKUs | **Phase C — stub** |
| ENR Construction Cost Index | `core/pricing/sources/construction_indexes.py` (`ENRConstructionCostIndexSource`) | ENR — attribution required | None | Monthly | National + 20-city composite cost index | **Phase C — stub** |
| AGC Construction Inflation Alert | `core/pricing/sources/construction_indexes.py` (`AGCInflationAlertSource`) | AGC — attribution required | None | Quarterly | AGC inflation / producer-price summary | **Phase C — stub** |
| Turner Building Cost Index | `core/pricing/sources/construction_indexes.py` (`TurnerBuildingCostIndexSource`) | Turner — attribution required | None | Quarterly | TBI national index | **Phase C — stub** |
| NAHB Cost of Constructing a Home | `core/pricing/sources/construction_indexes.py` (`NAHBCostOfConstructingAHomeSource`) | NAHB — attribution required | None | Annual | NAHB residential cost breakdown report | **Phase C — stub** |

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
- **OEWS wages are the median hourly mean across the metro, NOT trade-union or Davis-Bacon prevailing rates.** For federal-funded work (Davis-Bacon Act, McNamara-O'Hara Service Contract Act), pull the WD via `core/pricing/sources/davis_bacon.py` instead. For state-funded TX work, use `tx_prevailing_wage` once Phase B-full ships.
- **EIA PADD3 retail fuel is a regional average for the entire Gulf Coast (TX, LA, MS, AL, AR, NM)**, not a Texas-only number. For a Houston / Dallas / Austin spot price, manual lookup on EIA's interactive map remains necessary.
- **Davis-Bacon WDs change mid-year via modifications.** A WD pulled in Q1 may be superseded by Q3. Always re-pull at bid time using `scripts/refresh_pricing.py --sources davis_bacon ...`.
- **Each free API has a daily quota.** The 24h HTTP cache prevents accidentally re-running the refresher 10 times in a day from exhausting them. Honor the cache; if you need to bypass, delete the specific entry under `config/pricing_snapshots/_http_cache/<source>/`.

---

## Future work

| What | Why | When |
|---|---|---|
| Phase B-full: TWC PDF auto-download | Avoids manual quarterly download | Highest-value next step |
| Phase B-full: GSA Advantage CSV auto-download | Pulls catalog without manual step | Same |
| Phase C: TX SmartBuy / ESBD scraper | Historical sub-pricing reference | After Phase B-full |
| Phase C: HD Pro / Lowe's pro catalog | Spot-check single-SKU pricing | After Phase B-full; **only if ToS posture clear** |
| Phase C: ENR / AGC / Turner / NAHB PDF parsers | Cross-check vs BLS PPI escalation | Lowest priority — overlaps with PPI |
| **Tier 2: RSMeans / Gordian** | Production-grade composite cost DB | Decision pending calibration data + commercial approval |
| **Tier 3: BPC internal cost DB** | Eliminates external dependency | Started when BPC has > 12 months of internal cost capture; see `firm/compliance/material-suppliers.md` |

---

**End of playbook.**
