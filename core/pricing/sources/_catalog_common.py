"""Shared HTML-parsing helpers for retailer catalog adapters.

Pair-12 cleanup (2026-05-28). Extracted from
:mod:`core.pricing.sources.hd_pro` and
:mod:`core.pricing.sources.lowes_pro` because both retailers serve
their product detail pages with the **same** ``schema.org`` ``itemprop``
microdata vocabulary (``meta itemprop="sku"`` / ``meta itemprop="brand"`` /
``span itemprop="price"`` / etc.) AND the **same** Akamai-fronted
anti-bot interstitial markers.

Before this refactor the two adapters carried near-identical clones of:

- ``_decode_html`` / ``_strip_tags`` (HTML-entity normalisation)
- ``_meta_content`` / ``_itemprop_text`` (microdata extraction)
- ``_extract_title`` (title + suffix-strip)
- ``parse_price`` (USD price token with plausibility window)
- ``parse_unit_of_measure`` (UoM verbatim with keyword fallback)
- ``is_captcha_page`` (CAPTCHA / bot-interstitial detection)
- ``parse_product_page`` (the whole composition)

The duplication was flagged but intentionally left in place when only
two retailers existed. Pair-12 promotes the helpers to this module
behind a **dict-returning** low-level entry point so each adapter
keeps its own thin wrapper that constructs the per-retailer
``PricingSnapshot`` (with adapter-specific license text, source URL,
zip-code region, period, etc.) without touching the shared parsing
logic.

Each retailer adapter retains:

1. Its own license / ToS docstring at the top of the file (this is
   per-retailer legal text, not parsing code).
2. Its own ``CAPTCHA_MARKERS`` / ``_TITLE_SUFFIXES`` constants —
   currently identical across HD and Lowe's but they could diverge
   per retailer at any point.
3. Its own ``DEFAULT_SKUS`` / ``DEFAULT_ZIP_CODE`` starter constants.
4. Its own ``product_url()`` builder (URL shape is retailer-specific).
5. Its own ``parse_product_page()`` wrapper that constructs the
   ``PricingSnapshot`` from the dict this module returns.

Adding a third catalog adapter (Build.com, Ferguson, Grainger, etc.)
should be a thin per-retailer module that mirrors the HD/Lowe's
pattern — see ``hd_pro.py`` for the canonical example.
"""

from __future__ import annotations

import logging
import re
from typing import Optional

LOG = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# HTML entity / tag normalisation
# ---------------------------------------------------------------------------


_TAG_RE = re.compile(r"<[^>]+>")

_ENTITY_MAP = {
    "&amp;": "&", "&lt;": "<", "&gt;": ">", "&quot;": '"',
    "&apos;": "'", "&#39;": "'", "&nbsp;": " ", "&#34;": '"',
}
_ENTITY_RE = re.compile(r"&(?:amp|lt|gt|quot|apos|nbsp|#34|#39);")


def decode_html(text: str) -> str:
    """Decode the common HTML entities our retailer pages use.

    We deliberately don't ship a full ``html.unescape`` here because
    retailer product copy mixes encoded ASCII (e.g. ``&quot;`` in an
    inch-mark) with literal Unicode (e.g. ``½``) and accidental
    double-encoding (e.g. ``&amp;amp;``). The conservative entity
    map below covers everything we've seen in real HD / Lowe's HTML.
    """
    return _ENTITY_RE.sub(
        lambda m: _ENTITY_MAP.get(m.group(0), m.group(0)),
        text or "",
    )


def strip_tags(html: str) -> str:
    """Strip HTML tags and collapse whitespace edges."""
    if not html:
        return ""
    return _TAG_RE.sub(" ", html).strip()


# ---------------------------------------------------------------------------
# Microdata extractors (schema.org itemprop vocabulary)
# ---------------------------------------------------------------------------


def extract_meta_itemprop(html: str, prop_name: str) -> Optional[str]:
    """Return the ``content`` of a ``<meta itemprop="prop_name">`` tag.

    Tolerates both ``<meta itemprop="X" content="Y">`` and the reversed
    attribute order ``<meta content="Y" itemprop="X">`` that some
    server-side renderers emit.
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
        return decode_html(m.group(1)).strip() or None
    m = re.search(rev, html, re.IGNORECASE)
    if m:
        return decode_html(m.group(1)).strip() or None
    return None


def extract_itemprop_text(html: str, prop_name: str) -> Optional[str]:
    """Return the inner text of the first ``<* itemprop="prop_name">``.

    Matches the common inline containers
    (``span`` / ``div`` / ``p`` / ``a`` / ``h\\d`` / ``strong`` / ``em``)
    and ignores ``<meta>`` (use :func:`extract_meta_itemprop` for that).
    Inner HTML tags are stripped before returning.
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
        text = decode_html(strip_tags(m.group("inner"))).strip()
        return text or None
    return None


# ---------------------------------------------------------------------------
# Title extraction
# ---------------------------------------------------------------------------


_TITLE_RE = re.compile(r"<title[^>]*>([^<]*)</title>", re.IGNORECASE | re.DOTALL)
_H1_RE = re.compile(r"<h1\b[^>]*>(.*?)</h1>", re.IGNORECASE | re.DOTALL)


def extract_title(html: str, *, title_suffixes: tuple[str, ...] = ()) -> Optional[str]:
    """Pull the product title from ``<h1>`` (preferred) or ``<title>``.

    When a match comes from ``<title>``, any of ``title_suffixes`` that
    trails the decoded title text is stripped (e.g.
    ``" - The Home Depot"``, ``" | Lowe's"``). ``<h1>`` content is
    returned verbatim because retailers don't put the storefront
    name in the visible heading.
    """
    if not html:
        return None
    m = _H1_RE.search(html)
    if m:
        text = decode_html(strip_tags(m.group(1))).strip()
        if text:
            return text
    m = _TITLE_RE.search(html)
    if m:
        text = decode_html(m.group(1)).strip()
        for suffix in title_suffixes:
            if text.endswith(suffix):
                text = text[: -len(suffix)].strip()
                break
        if text:
            return text
    return None


# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------


_PRICE_RE = re.compile(
    r"\$?\s*((?:\d{1,3}(?:,\d{3})+|\d{1,9})(?:\.\d{1,2})?)"
)

MIN_PLAUSIBLE_PRICE = 0.05
MAX_PLAUSIBLE_PRICE = 100_000.0


def parse_price(text: Optional[str]) -> Optional[float]:
    """Parse a USD price out of ``text``.

    Accepts:

    - ``$12.34`` — explicit dollar sign, decimal
    - ``$1,234.56`` — explicit dollar sign, thousands separator
    - ``12.34`` — bare number with decimal
    - ``$1234`` — explicit dollar sign, integer

    Returns ``None`` (no raise) when:

    - No price-like token is found in ``text``.
    - The parsed value falls outside the plausibility window
      (``MIN_PLAUSIBLE_PRICE``..``MAX_PLAUSIBLE_PRICE``) — cheapest
      catalog SKU is ~$0.10, most expensive Pro-tier SKU we've seen
      is ~$50k. Out-of-band values are rejected rather than emitted
      as a wrong number.
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


# ---------------------------------------------------------------------------
# Unit-of-measure extraction
# ---------------------------------------------------------------------------


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

    Tries structured selectors first
    (``<dt>Unit of Measure</dt><dd>...</dd>``,
    ``<div class="unit-of-measure">``, ``<div class="uom">``,
    ``<div class="sales-unit">``, ``<span>Sold by</span><span>...</span>``)
    before falling back to a keyword scan over the page body.
    Case is preserved as it appears in the source HTML.

    Order in the structured selector list matters: HD's ``<dt>`` /
    ``<dd>`` pattern is the highest-fidelity signal so it ships
    first; the class-based selectors are a fall-back for layouts
    that omit the definition list.
    """
    if not html:
        return "each"
    for rx in _UOM_STRUCTURED_RE:
        m = rx.search(html)
        if m:
            value = decode_html(m.group(1)).strip()
            if value:
                return value
    text = strip_tags(html)
    m = _UOM_KEYWORD_RE.search(text)
    if m:
        return m.group(1).strip()
    return "each"


# ---------------------------------------------------------------------------
# CAPTCHA / anti-bot detection
# ---------------------------------------------------------------------------


# Default markers — matches Akamai / Distil / Imperva / generic block
# pages without false-positiving on legitimate product copy. We
# normalize to lowercase before matching. Per-adapter modules can
# extend this list with retailer-specific signals if a new bot
# manager surfaces.
DEFAULT_CAPTCHA_MARKERS: list[str] = [
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


def looks_like_captcha(html: str, markers: list[str] | None = None) -> bool:
    """True iff ``html`` looks like an anti-bot interstitial.

    Lowercase-substring match against ``markers`` (default:
    :data:`DEFAULT_CAPTCHA_MARKERS`). Returns ``False`` on empty
    input.
    """
    if not html:
        return False
    lower = html.lower()
    for marker in (markers if markers is not None else DEFAULT_CAPTCHA_MARKERS):
        if marker in lower:
            return True
    return False


# ---------------------------------------------------------------------------
# Composed parser — adapter-name-aware, dict-returning
# ---------------------------------------------------------------------------


def parse_product_page(
    html: str,
    sku: str,
    *,
    adapter_name: str,
    title_suffixes: tuple[str, ...] = (),
    captcha_markers: list[str] | None = None,
) -> Optional[dict]:
    """Parse a retailer product page into a normalised dict.

    Returns ``None`` (never raises) when:

    - ``html`` is empty.
    - ``html`` looks like a CAPTCHA / anti-bot interstitial.
    - No price-like token can be parsed (the page may be a CAPTCHA
      that's not on our marker list, or a layout the parser doesn't
      yet understand).

    On success returns a dict with these keys (never ``None`` keys —
    optional values are absent or explicitly ``None``)::

        {
            "sku": "<parsed sku, falling back to caller-supplied>",
            "title": "<title or 'SKU <sku>' fallback>",
            "brand": "<brand or None>",
            "mpn": "<mpn or None>",
            "price": <float USD>,
            "price_raw": "<original price token>",
            "unit": "<UoM verbatim or 'each' fallback>",
        }

    The per-retailer adapter wraps this dict + adapter-specific fields
    (license, source URL, region, period) into a
    :class:`core.pricing.snapshots.PricingSnapshot`. Keeping that
    construction at the adapter layer means this module never
    imports the snapshot model — it can be unit-tested in pure-Python
    without the Pydantic stack.

    ``adapter_name`` is used only for log messages so operators can
    correlate CAPTCHA warnings to the right retailer.
    """
    if not html:
        return None
    if looks_like_captcha(html, captcha_markers):
        LOG.warning(
            "%s: anti-bot/CAPTCHA page returned for sku %r — skipping "
            "(this is the documented anti-bot fragility; see "
            "firm/playbooks/pricing-data-sources.md)",
            adapter_name, sku,
        )
        return None

    # SKU — prefer the structured ``meta itemprop="sku"``, fall back
    # to ``productID``, fall back to the caller-supplied SKU.
    parsed_sku = (
        extract_meta_itemprop(html, "sku")
        or extract_meta_itemprop(html, "productID")
        or sku
    )

    # Price — try ``<span itemprop="price">`` first, then meta, then
    # a last-resort body scan for the first ``$N.NN`` token.
    price_str = (
        extract_itemprop_text(html, "price")
        or extract_meta_itemprop(html, "price")
    )
    if not price_str:
        body_text = strip_tags(html)
        m = re.search(
            r"\$\s?\d{1,3}(?:,\d{3})*(?:\.\d{2})?",
            body_text,
        )
        price_str = m.group(0) if m else None

    if not price_str:
        LOG.info(
            "%s: no price found for sku %r — skipping",
            adapter_name, sku,
        )
        return None

    price = parse_price(price_str)
    if price is None:
        LOG.info(
            "%s: price text %r did not parse for sku %r — skipping",
            adapter_name, price_str, sku,
        )
        return None

    title = extract_title(html, title_suffixes=title_suffixes) or f"SKU {parsed_sku}"
    brand = (
        extract_itemprop_text(html, "brand")
        or extract_meta_itemprop(html, "brand")
    )
    mpn = (
        extract_itemprop_text(html, "mpn")
        or extract_meta_itemprop(html, "mpn")
        or extract_meta_itemprop(html, "model")
    )
    unit = parse_unit_of_measure(html)

    return {
        "sku": parsed_sku,
        "title": title,
        "brand": brand,
        "mpn": mpn,
        "price": price,
        "price_raw": price_str,
        "unit": unit,
    }
