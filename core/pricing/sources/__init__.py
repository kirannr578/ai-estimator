"""Adapters for free public pricing data sources.

Each module exports a `PricingSource` subclass. Public adapters today:

- ``bls_ppi``       — BLS Producer Price Index (15 curated series)
- ``bls_oews``      — BLS Occupational Employment + Wage Statistics
                      (10 SOC codes x 6 TX metros)
- ``fred``          — FRED economic data (8 curated series, incl. WTI proxy)
- ``eia``           — EIA weekly retail diesel + gasoline (PADD3 / Gulf Coast)
- ``davis_bacon``   — SAM.gov Wage Determinations lookup
- ``tx_prevailing_wage`` (Phase B, stub) — TWC per-county PDF parser
- ``gsa_schedule``  (Phase B, stub) — GSA Advantage construction schedules
- ``tx_smartbuy_awards`` (Phase C, stub) — TX SmartBuy / ESBD award postings
- ``hd_pro_catalog`` (Phase C, stub) — Pro-catalog scraper (public prices only)
- ``enr_cci``       (Phase C) — ENR 20-City Construction Cost Index
- ``agc_cci``       (Phase C) — AGC PPI-based Construction Cost Index
- ``turner_cci``    (Phase C) — Turner Building Cost Index
- ``nahb_construction_cost`` (Phase C) — NAHB Cost of Constructing a Home
                                          (residential macro complement)
- ``construction_indexes`` — historical bin / re-export shim for the NAHB
                              adapter (kept for backward compatibility
                              with pre-Phase-C-completion imports)

All adapters MUST:
- Use TLS verification (no ``verify=False``).
- Send a polite ``User-Agent`` per the brief.
- Respect upstream rate limits via the 24h file cache in ``base.py``.
- Honor the source's license + ToS (documented in each adapter's docstring).
- Be safe to import even if their required API key env var isn't set.
"""

from core.pricing.sources.base import PricingSource

__all__ = ["PricingSource"]
