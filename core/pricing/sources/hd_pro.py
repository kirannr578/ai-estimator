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
import re
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    http_get_text,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

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

# Conservative list — matches Akamai / Distil / Imperva / generic block
# pages without false-positiving on legitimate product copy. We
# normalize to lowercase before matching.
CAPTCHA_MARKERS: list[str] = [
    "pardon our interruption",
    "/_incapsula_resource",
    "as you were browsing, something about your browser",
    "request unsuccessful. incapsula",
    "access denied",
    "bot detected",
    "captcha verification",
    "akamai-edgesuite",
    "we want to make sure you're a real person",
    "are you a robot",
]


def is_captcha_page(html: str) -> bool:
    """True iff ``html`` looks like an anti-bot interstitial."""
    if not html:
        return False
    lower = html.lower()
    return any(marker in lower for marker in CAPTCHA_MARKERS)


# --- HTML parsing helpers ---------------------------------------------

_TAG_RE = re.compile(r"<[^>]+>")

_ENTITY_MAP = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&apos;": "'", "&#39;": "'", "&nbsp;": " ", "&#34;": '"',
}
_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|quot|apos|nbsp|#34|#39);")


def _decode_html(text: str) -> str:
    return _ENTITY_RE.sub(
        lambda m: _ENTITY_MAP.get(m.group(0), m.group(0)),
        text or "",
    )


def _strip_tags(html: str) -> str:
    if not html:
        return ""
    return _TAG_RE.sub(" ", html).strip()


_TITLE_RE = re.compile(r"<title[^>]*>([^<]*)</title>", re.IGNORECASE | re.DOTALL)
_H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)

_TITLE_SUFFIXES = (
    " - The Home Depot",
    " | The Home Depot",
    " | Pro Xtra",
)


def _extract_title(html: str) -> Optional[str]:
    """Pull the product title from ``<h1>`` (preferred) or ``<title>``."""
    if not html:
        return None
    m = _H1_RE.search(html)
    if m:
        text = _decode_html(_strip_tags(m.group(1))).strip()
        if text:
            return text
    m = _TITLE_RE.search(html)
    if m:
        text = _decode_html(m.group(1)).strip()
        for suffix in _TITLE_SUFFIXES:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                break
        if text:
            return text
    return None


def _meta_content(html: str, prop_name: str) -> Optional[str]:
    """Return the ``content`` of a ``<meta itemprop="prop_name">``.

    Tolerates both ``<meta itemprop="X" content="Y">`` and the reversed
    attribute order ``<meta content="Y" itemprop="X">``.
    """
    if not html:
        return None
    name = re.escape(prop_name)
    fwd = (
        rf'<meta\b[^>]*itemprop\s*=\s*["\']{name}["\']'
        rf'[^>]*content\s*=\s*["\']([^"\']*)["\']'
    )
    rev = (
        rf'<meta\b[^>]*content\s*=\s*["\']([^"\']*)["\']'
        rf'[^>]*itemprop\s*=\s*["\']{name}["\']'
    )
    m = re.search(fwd, html, re.IGNORECASE)
    if m:
        return _decode_html(m.group(1)).strip() or None
    m = re.search(rev, html, re.IGNORECASE)
    if m:
        return _decode_html(m.group(1)).strip() or None
    return None


def _itemprop_text(html: str, prop_name: str) -> Optional[str]:
    """Return the inner text of the first ``<* itemprop="prop_name">``.

    Matches ``span`` / ``div`` / ``p`` / ``a`` containers; ignores
    ``<meta>`` (use ``_meta_content`` for that). Inner HTML tags are
    stripped before returning.
    """
    if not html:
        return None
    name = re.escape(prop_name)
    pattern = (
        rf'<(?P<tag>span|div|p|a|h\d|strong|em)\b[^>]*'
        rf'itemprop\s*=\s*["\']{name}["\'][^>]*>'
        rf'(?P<inner>.*?)</(?P=tag)>'
    )
    m = re.search(pattern, html, re.IGNORECASE | re.DOTALL)
    if m:
        text = _decode_html(_strip_tags(m.group("inner"))).strip()
        return text or None
    return None


# Price tokens we accept:
#   $12.34       — explicit dollar sign, decimal
#   $1,234.56    — explicit dollar sign, thousands separator
#   12.34        — bare number with decimal (must look like a price)
#   $1234        — explicit dollar sign, integer (treated as whole-dollar)
_PRICE_RE = re.compile(
    r"\$?\s*((?:\d{1,3}(?:,\d{3})+|\d{1,9})(?:\.\d{1,2})?)"
)

# Plausibility window for a single retail catalog SKU. The cheapest
# catalog SKU is ~$0.10 (single screws, single bolts); the most
# expensive Pro-tier SKU we've seen is ~$50k (whole-house generators,
# major equipment). Outside this band we reject the parse rather than
# emit a wrong number.
MIN_PLAUSIBLE_PRICE = 0.05
MAX_PLAUSIBLE_PRICE = 100_000.0


def parse_price(text: Optional[str]) -> Optional[float]:
    """Parse a USD price out of ``text``.

    Returns ``None`` if no price-like token is found or the parsed
    value falls outside the plausibility window.
    """
    if not text:
        return None
    m = _PRICE_RE.search(text)
    if m is None:
        return None
    try:
        val = float(m.group(1).replace(",", ""))
    except ValueError:
        return None
    if not (MIN_PLAUSIBLE_PRICE <= val <= MAX_PLAUSIBLE_PRICE):
        return None
    return val


# UoM extraction — try structured selectors first, then keyword fallback.
_UOM_STRUCTURED_PATTERNS = [
    r'<dt[^>]*>\s*Unit\s+of\s+Measure\s*</dt>\s*<dd[^>]*>([^<]+)</dd>',
    r'<[^>]*class\s*=\s*["\'][^"\']*unit[\-_]of[\-_]measure[^"\']*["\']'
    r'[^>]*>([^<]+)</',
    r'<[^>]*class\s*=\s*["\'][^"\']*\buom\b[^"\']*["\'][^>]*>([^<]+)</',
    r'<[^>]*class\s*=\s*["\'][^"\']*sales-unit[^"\']*["\'][^>]*>([^<]+)</',
    r'<span[^>]*>\s*Sold\s+by\s*</span>\s*<span[^>]*>([^<]+)</span>',
]
_UOM_STRUCTURED_RE = [
    re.compile(p, re.IGNORECASE | re.DOTALL)
    for p in _UOM_STRUCTURED_PATTERNS
]

# Keyword fallback. Captures a bounded UoM-like phrase. Order matters:
# longer phrases ("box of 100") are tried before bare keywords ("box")
# so the verbose variant wins.
_UOM_KEYWORD_RE = re.compile(
    r"\b("
    r"box\s+of\s+\d+|"
    r"case\s+of\s+\d+|"
    r"pack\s+of\s+\d+|"
    r"bag\s+of\s+\d+|"
    r"bundle\s+of\s+\d+|"
    r"\d+\s*lbs?|"
    r"\d+\s*ft|"
    r"\d+\s*pc|"
    r"linear\s+ft|"
    r"square\s+ft|"
    r"sq\.?\s*ft\.?|"
    r"each|"
    r"box|case|pack|bag|bundle|"
    r"gallon|gal\.?|"
    r"piece|pieces|pc"
    r")\b",
    re.IGNORECASE,
)


def parse_unit_of_measure(html: str) -> str:
    """Extract the UoM verbatim from ``html``; fall back to ``"each"``.

    Tries structured selectors (``<dt>Unit of Measure</dt><dd>...</dd>``,
    ``<div class="unit-of-measure">``, etc.) before falling back to a
    keyword scan over the page body. Case is preserved as it appears in
    the source HTML.
    """
    if not html:
        return "each"
    for rx in _UOM_STRUCTURED_RE:
        m = rx.search(html)
        if m:
            value = _decode_html(m.group(1)).strip()
            if value:
                return value
    text = _strip_tags(html)
    m = _UOM_KEYWORD_RE.search(text)
    if m:
        return m.group(1).strip()
    return "each"


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

    Returns ``None`` (no crash) when:
      - ``html`` is empty.
      - ``html`` looks like a CAPTCHA / anti-bot interstitial.
      - No price-like token can be parsed.

    The function never raises on parse error — callers that want
    raising behavior must check the return value.
    """
    if not html:
        return None
    if is_captcha_page(html):
        LOG.warning(
            "%s: anti-bot/CAPTCHA page returned for sku %r at %s — "
            "skipping (this is the documented anti-bot fragility; see "
            "firm/playbooks/pricing-data-sources.md)",
            adapter_name, sku, source_url,
        )
        return None

    # Item ID — prefer the structured ``meta itemprop="sku"``, fall
    # back to ``productID``, fall back to the caller-supplied SKU.
    parsed_sku = (
        _meta_content(html, "sku")
        or _meta_content(html, "productID")
        or sku
    )

    # Price — try ``<span itemprop="price">`` first, then meta, then
    # a last-resort body scan for the first ``$N.NN`` token.
    price_str = (
        _itemprop_text(html, "price")
        or _meta_content(html, "price")
    )
    if not price_str:
        body_text = _strip_tags(html)
        m = re.search(
            r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
            body_text,
        )
        price_str = m.group(0) if m else None

    if not price_str:
        LOG.info(
            "%s: no price found for sku %r at %s — skipping",
            adapter_name, sku, source_url,
        )
        return None

    price = parse_price(price_str)
    if price is None:
        LOG.info(
            "%s: price text %r did not parse for sku %r — skipping",
            adapter_name, price_str, sku,
        )
        return None

    title = _extract_title(html) or f"SKU {parsed_sku}"
    brand = _itemprop_text(html, "brand") or _meta_content(html, "brand")
    mpn = (
        _itemprop_text(html, "mpn")
        or _meta_content(html, "mpn")
        or _meta_content(html, "model")
    )
    unit = parse_unit_of_measure(html)

    fetched_at = datetime.now(timezone.utc)
    period_str = period or fetched_at.strftime("%Y-%m-%d")

    return PricingSnapshot(
        source=adapter_name,
        series_id=parsed_sku,
        label=title,
        unit=unit,
        value=price,
        region=zip_code,
        csi_division=None,
        naics=None,
        period=period_str,
        fetched_at=fetched_at,
        license=license_str,
        source_url=source_url,
        raw={
            "sku_requested": sku,
            "sku_parsed": parsed_sku,
            "title": title,
            "brand": brand,
            "mpn": mpn,
            "price_raw": price_str,
            "price_value_usd": price,
            "unit_of_measure": unit,
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
