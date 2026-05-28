"""Home Depot Pro catalog scraper — Phase C (shipped 2026-05-28).

Source:     The Home Depot, public product detail pages.
            - https://www.homedepot.com/c/Pro                (Pro homepage)
            - https://www.homedepot.com/p/<slug>/<sku>       (PDP)
License:    The Home Depot retailer-proprietary. Public catalog prices
            only. The Home Depot's Terms of Use prohibit automated
            scraping at scale. This adapter is intended for **low-volume
            estimating spot-checks**, NOT for commercial redistribution
            of the catalog. Each snapshot persists the canonical product
            URL so a downstream consumer can re-verify the value
            interactively before committing it to a bid.
ToS:        https://www.homedepot.com/c/Customer_Agreement

What this adapter does
----------------------

Given a list of Home Depot Item IDs (SKUs), the adapter walks each
product page and emits one ``PricingSnapshot`` per successfully-parsed
SKU carrying:

- ``Item ID``               (snapshot ``series_id``)
- ``Title``                 (snapshot ``label``)
- ``Brand``                 (snapshot ``raw["brand"]``)
- ``Price``                 (snapshot ``value``, USD)
- ``Unit-of-measure``       (snapshot ``unit`` — verbatim where present,
                             e.g. ``"each"``, ``"box of 100"``,
                             ``"case of 50"``, ``"1 lb"``; falls back to
                             ``"each"``)
- ``MFR Number``            (snapshot ``raw["mpn"]``)
- ``zip_code``              (snapshot ``region`` + ``raw["zip_code"]``)

Snapshots use ``unit`` = the catalog UoM verbatim — distinct from the
TX SmartBuy ``unit="USD"`` (lump-sum awards), the BLS PPI
``unit="index"`` (dimensionless), and the OEWS ``unit="USD/hr"``.

Structural fragility — anti-bot / CAPTCHA / Akamai
--------------------------------------------------

**Home Depot serves its product pages behind an Akamai-fronted
JavaScript shell with bot protection.** A polite ``httpx`` GET (no
JavaScript engine, no cookie / fingerprint mimicry) will most often
land on one of:

- A "Pardon Our Interruption" CAPTCHA / interstitial page.
- An HTTP 403 from Akamai's edge.
- A 200 with the JavaScript shell that, when rendered in a browser,
  populates from a private GraphQL endpoint we are NOT authorized to
  call programmatically.

This is the **biggest known structural limitation** of the adapter and
is documented prominently in ``firm/playbooks/pricing-data-sources.md``.
The adapter degrades gracefully:

1. ``fetch()`` and ``fetch_recent()`` swallow per-SKU HTTP errors and
   anti-bot intercepts, log a warning, and return whatever they could
   parse (often ``[]``). The refresh runner is never crashed.
2. ``fetch_one()`` raises ``PricingSourceUnavailable`` on a 4xx / 5xx
   so a one-off CLI lookup can detect failure.
3. When the response *is* a CAPTCHA / anti-bot page (200-OK HTML
   carrying one of the known interstitial markers), the adapter logs a
   warning and skips that SKU rather than emitting a misleading
   snapshot.

When the live fetch is blocked at scale (the expected default), the
adapter ships its interface, parsing logic, and tests but produces
empty snapshot lists in production. Recommended remediation paths,
in preference order (none implemented in this slice):

(a) **Use HD's official supplier / B2B Pro account API** when one is
    available. Requires a Pro Xtra account + commercial contract.
(b) **Use a 3rd-party catalog aggregator** (Datalink, Build.com,
    similar) with an explicit license to redistribute pricing for
    estimating use.
(c) **Curate a manual SKU CSV per bid** — a project manager walks the
    Pro counter for the bid scope, exports a printed quote, and the
    estimator imports it into the bid workspace.

Free-tier access posture (verified 2026-05-28)
----------------------------------------------

- No auth.
- 24h disk cache via ``_cci_common.http_get_text``; cache lives under
  ``config/pricing_snapshots/_http_cache/hd_pro/`` (gitignored).
- Polite ``User-Agent`` (inherited from ``base.build_client``).
- No bulk-download attempt: the SKU list is bounded at construction
  time. The refresh runner uses a 10-SKU starter list (see
  ``scripts/refresh_pricing.py::HD_PRO_STARTER_SKUS``).
- No new third-party deps; ``bs4``/``lxml`` deliberately NOT added.
  Parsing is regex over the rendered HTML, same family as the
  ``tx_smartbuy_awards`` and ``_cci_common`` parsers.

Snapshot shape
--------------

- ``source``:        "hd_pro"
- ``series_id``:     "<Item ID>"          # parsed ``meta itemprop="sku"``,
                                            falling back to caller-supplied SKU
- ``label``:         "<Product title>"
- ``unit``:          "<UoM verbatim>"     # "each" / "box of 100" / "1 lb" / ...
- ``value``:         <price USD>
- ``region``:        "<zip_code>"         # store-availability scope
- ``csi_division``:  None
- ``naics``:         None
- ``period``:        "YYYY-MM-DD"         # scrape date — prices fluctuate
                                            hourly during promo seasons, so we
                                            persist by full date, not month
- ``license``:       per ``license_str`` below; cite at every use
- ``source_url``:    https://www.homedepot.com/p/<sku>
- ``raw``:           {sku_requested, sku_parsed, title, brand, mpn,
                      price_raw, price_value_usd, unit_of_measure,
                      zip_code, fetched_at}
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._catalog_common import (
    DEFAULT_CAPTCHA_MARKERS,
    MAX_PLAUSIBLE_PRICE,
    MIN_PLAUSIBLE_PRICE,
    looks_like_captcha,
    parse_price,
    parse_product_page as _common_parse_product_page,
    parse_unit_of_measure,
)
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    http_get_text,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

# Re-exports (kept at module top so the test surface remains stable
# with the public-name imports the existing test module relies on:
# ``parse_price`` and ``parse_unit_of_measure`` are imported via
# ``from core.pricing.sources.hd_pro import ...`` in
# ``tests/test_pricing_sources_hd_pro.py``).
__all__ = [
    "CAPTCHA_MARKERS",
    "DEFAULT_SKUS",
    "DEFAULT_ZIP_CODE",
    "HD_BASE_URL",
    "HD_PRO_HOMEPAGE",
    "HomeDepotProSource",
    "MAX_PLAUSIBLE_PRICE",
    "MIN_PLAUSIBLE_PRICE",
    "is_captcha_page",
    "parse_price",
    "parse_product_page",
    "parse_unit_of_measure",
    "product_url",
]

# --- URLs --------------------------------------------------------------

HD_BASE_URL = "https://www.homedepot.com"
HD_PRO_HOMEPAGE = "https://www.homedepot.com/c/Pro"

# Default zip code for store-availability scoping. Carrollton, TX
# (Dallas-Fort Worth metro) is the BPC operating zip; per-bid callers
# should override at construction time when working another market.
DEFAULT_ZIP_CODE = "75001"

# Default starter SKU list. Curated 2026-05-28 from common BPC scopes
# (door hardware, paint, drywall, framing lumber, plywood, fasteners).
# These are illustrative HD Item IDs — the live HD catalog is the
# source of truth, and these IDs may be retired or repriced at any
# time. The refresh runner overrides this list with its own
# ``HD_PRO_STARTER_SKUS`` constant so the policy lives at the call
# site (see ``scripts/refresh_pricing.py``).
DEFAULT_SKUS: list[str] = [
    "100120362",   # 3/4 in. PVC pipe (illustrative)
    "100133104",   # 2x4x8 SPF framing lumber
    "202079922",   # drywall screws, 1 lb box
    "202519319",   # 1/2 in. sheathing plywood
    "203083697",   # interior latex paint, 1 gal
    "100195918",   # passage door knob
    "203070515",   # exterior door hinge
    "100129040",   # 5 gal joint compound
    "200032100",   # 4x8 gypsum board
    "100107516",   # 30 lb roofing felt
]


def product_url(sku: str, slug: Optional[str] = None) -> str:
    """Canonical Home Depot product URL for ``sku``.

    Real-world HD product URLs include a marketing slug:
    ``/p/<slug>/<sku>``. For programmatic fetches the slug is optional;
    HD redirects bare-SKU URLs to the canonical slug page. We use the
    bare-SKU form so we don't need to pre-know the slug per SKU.
    """
    sku_clean = (sku or "").strip()
    if not sku_clean:
        raise ValueError("sku must be non-empty")
    if slug:
        return f"{HD_BASE_URL}/p/{slug}/{sku_clean}"
    return f"{HD_BASE_URL}/p/{sku_clean}"


# --- Anti-bot / CAPTCHA markers ---------------------------------------

# Per-adapter copy of the shared marker list. Currently identical to
# :data:`core.pricing.sources._catalog_common.DEFAULT_CAPTCHA_MARKERS`
# — both retailers run on Akamai's bot manager — but kept as a module-
# level constant so HD-specific markers can be added here without
# touching the shared list (or the Lowe's adapter).
CAPTCHA_MARKERS: list[str] = list(DEFAULT_CAPTCHA_MARKERS)


def is_captcha_page(html: str) -> bool:
    """True iff ``html`` looks like an HD anti-bot interstitial.

    Thin wrapper around :func:`_catalog_common.looks_like_captcha` that
    pins the HD-specific marker list.
    """
    return looks_like_captcha(html, CAPTCHA_MARKERS)


# --- Title suffixes (HD-specific storefront branding) -----------------

_TITLE_SUFFIXES = (
    " - The Home Depot",
    " | The Home Depot",
    " | Pro Xtra",
)


# --- Snapshot construction --------------------------------------------


def parse_product_page(
    html: str,
    sku: str,
    *,
    source_url: str,
    zip_code: str,
    license_str: str,
    adapter_name: str,
    period: Optional[str] = None,
) -> Optional[PricingSnapshot]:
    """Parse a Home Depot product page HTML into a ``PricingSnapshot``.

    Thin wrapper around
    :func:`core.pricing.sources._catalog_common.parse_product_page` that
    pins HD-specific title suffixes + CAPTCHA markers, then constructs
    the ``PricingSnapshot`` using adapter-specific fields the common
    parser doesn't (and shouldn't) know about — license string, source
    URL, region (zip code), and snapshot period.

    Returns ``None`` (no crash) when:
      - ``html`` is empty.
      - ``html`` looks like a CAPTCHA / anti-bot interstitial.
      - No price-like token can be parsed.

    The function never raises on parse error — callers that want
    raising behavior must check the return value.
    """
    parsed = _common_parse_product_page(
        html, sku,
        adapter_name=adapter_name,
        title_suffixes=_TITLE_SUFFIXES,
        captcha_markers=CAPTCHA_MARKERS,
    )
    if parsed is None:
        return None

    fetched_at = datetime.now(timezone.utc)
    period_str = period or fetched_at.strftime("%Y-%m-%d")

    return PricingSnapshot(
        source=adapter_name,
        series_id=parsed["sku"],
        label=parsed["title"],
        unit=parsed["unit"],
        value=parsed["price"],
        region=zip_code,
        csi_division=None,
        naics=None,
        period=period_str,
        fetched_at=fetched_at,
        license=license_str,
        source_url=source_url,
        raw={
            "sku_requested": sku,
            "sku_parsed": parsed["sku"],
            "title": parsed["title"],
            "brand": parsed["brand"],
            "mpn": parsed["mpn"],
            "price_raw": parsed["price_raw"],
            "price_value_usd": parsed["price"],
            "unit_of_measure": parsed["unit"],
            "zip_code": zip_code,
            "fetched_at": fetched_at.isoformat(),
        },
    )


# --- Adapter -----------------------------------------------------------


class HomeDepotProSource(PricingSource):
    """Home Depot Pro catalog scraper.

    See module docstring for the full contract, license, and the known
    anti-bot fragility. This adapter is a *spot-check* tool, not a bulk
    catalog mirror.
    """

    name = "hd_pro"
    requires_env_vars: list[str] = []
    license_str = (
        "Home Depot retailer-proprietary; public catalog prices only — "
        "low-volume estimating use, not commercial redistribution"
    )
    homepage_url = HD_PRO_HOMEPAGE

    def __init__(
        self,
        sku_list: Optional[list[str]] = None,
        zip_code: str = DEFAULT_ZIP_CODE,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.sku_list: list[str] = (
            list(sku_list) if sku_list is not None else list(DEFAULT_SKUS)
        )
        self.zip_code = str(zip_code or DEFAULT_ZIP_CODE)

    # --- public entry points ------------------------------------------

    def default_series(self) -> list[str]:
        """Return the configured SKU list as the default series."""
        return list(self.sku_list)

    def fetch(
        self, series_ids: list[str], **filters: Any
    ) -> list[PricingSnapshot]:
        """Generic-shape entry point used by ``scripts/refresh_pricing.py``.

        - If ``series_ids`` is non-empty each id is treated as an
          explicit Item ID and fetched.
        - If ``series_ids`` is empty (or None), the configured
          ``self.sku_list`` is used.

        Per-SKU HTTP errors and anti-bot intercepts are swallowed and
        logged; the refresh runner is never crashed by this adapter.
        """
        skus = list(series_ids) if series_ids else list(self.sku_list)
        if not skus:
            return []
        out: list[PricingSnapshot] = []
        for sku in skus:
            snap = self._fetch_one_safe(sku)
            if snap is not None:
                out.append(snap)
        return out

    def fetch_recent(
        self, since: Optional[datetime] = None
    ) -> list[PricingSnapshot]:
        """Convenience wrapper for the standard refresh flow.

        ``since`` is accepted for interface symmetry with the time-series
        adapters but ignored — the catalog is a snapshot of *current*
        pricing, not a historical series. Today's date is used as the
        snapshot ``period`` for every returned snapshot.
        """
        return self.fetch([])

    def fetch_one(
        self, sku: str, period: Optional[str] = None
    ) -> PricingSnapshot:
        """Fetch a single SKU; raise ``PricingSourceUnavailable`` on failure.

        Use this entry point when you want hard-failure semantics
        (e.g. a one-off CLI lookup). For the refresh flow use
        ``fetch()``/``fetch_recent()`` which swallow per-SKU errors.
        """
        sku_clean = (sku or "").strip()
        if not sku_clean:
            raise PricingSourceUnavailable("HD Pro: empty sku")
        url = product_url(sku_clean)
        try:
            html = http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            raise PricingSourceUnavailable(
                f"HD Pro: HTTP error fetching {url}: {exc}"
            ) from exc

        snap = parse_product_page(
            html,
            sku=sku_clean,
            source_url=url,
            zip_code=self.zip_code,
            license_str=self.license_str,
            adapter_name=self.name,
            period=period,
        )
        if snap is None:
            raise PricingSourceUnavailable(
                f"HD Pro: could not parse product page at {url} "
                f"(may be CAPTCHA / anti-bot, missing price, or layout "
                f"change)"
            )
        return snap

    # --- internal -----------------------------------------------------

    def _fetch_one_safe(
        self, sku: str, period: Optional[str] = None
    ) -> Optional[PricingSnapshot]:
        """Per-SKU fetch that never raises. Returns ``None`` on any error."""
        try:
            return self.fetch_one(sku, period=period)
        except PricingSourceUnavailable as exc:
            LOG.warning("HD Pro: skipping sku %r — %s", sku, exc)
            return None
        except Exception as exc:  # noqa: BLE001
            LOG.warning(
                "HD Pro: unexpected error fetching sku %r — %s", sku, exc,
            )
            return None
