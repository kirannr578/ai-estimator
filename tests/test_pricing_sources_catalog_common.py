"""Unit tests for ``core/pricing/sources/_catalog_common.py``.

The catalog-common module is the dict-returning low-level parser
shared by ``hd_pro`` and ``lowes_pro``. It carries the entire
HTML-parsing surface those adapters depend on (microdata extraction,
price parsing, UoM extraction, CAPTCHA detection, title extraction)
so the per-retailer modules can stay thin.

The HD- and Lowe's-specific test modules
(``test_pricing_sources_hd_pro.py`` and
``test_pricing_sources_lowes_pro.py``) cover the end-to-end
PricingSnapshot construction path. These tests cover the shared
parsing logic directly so a future retailer adapter (Build.com,
Ferguson, Grainger) inherits provable behavior on day 1 without
having to copy a 30-test fixture set.

All tests run offline against synthetic schema.org-microdata HTML
strings.
"""

from __future__ import annotations

import pytest

from core.pricing.sources._catalog_common import (
    DEFAULT_CAPTCHA_MARKERS,
    MAX_PLAUSIBLE_PRICE,
    MIN_PLAUSIBLE_PRICE,
    decode_html,
    extract_itemprop_text,
    extract_meta_itemprop,
    extract_title,
    looks_like_captcha,
    parse_price,
    parse_product_page,
    parse_unit_of_measure,
    strip_tags,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


HD_LIKE_PVC_HTML = """
<html>
<head>
<title>3/4 in. PVC Pipe - 10 ft - The Home Depot</title>
<meta itemprop="sku" content="100120362">
<meta itemprop="brand" content="Charlotte Pipe">
</head>
<body>
<h1 class="product-title">3/4 in. x 10 ft. PVC Schedule 40 Plain End Pipe</h1>
<span itemprop="brand">Charlotte Pipe</span>
<span itemprop="price">$3.45</span>
<span itemprop="mpn">PVC074</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

LOWES_LIKE_PVC_HTML = """
<html>
<head>
<title>3/4-in x 10-ft PVC Pipe | Lowe's</title>
<meta itemprop="sku" content="1099113">
</head>
<body>
<h1 class="product-title">3/4-in x 10-ft PVC Sch 40 Pipe</h1>
<span itemprop="brand">Charlotte Pipe</span>
<span itemprop="price">$3.78</span>
<span itemprop="mpn">PVC074-LOWES</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

CAPTCHA_HTML = """
<html><head><title>Pardon Our Interruption</title></head>
<body><h1>Pardon Our Interruption...</h1>
<p>As you were browsing, something about your browser made us think you
were a bot.</p></body></html>
"""

REVERSED_META_HTML = """
<html><head>
<meta content="REV-SKU-001" itemprop="sku">
<meta content="$9.99" itemprop="price">
</head><body><h1>Reversed Attribute Order</h1></body></html>
"""

NESTED_INNER_HTML = """
<html><body>
<span itemprop="price"><strong>$</strong>12.99</span>
<span itemprop="brand"><span class="logo">Acme</span></span>
</body></html>
"""

SPECIAL_CHAR_HTML = """
<html><head><title>3/4 &quot; PVC Coupling - The Home Depot</title>
<meta itemprop="sku" content="100120999"></head>
<body><h1>3/4 &quot; PVC Coupling Slip x Slip</h1>
<span itemprop="price">$0.89</span></body></html>
"""

NO_PRICE_HTML = """
<html><body><h1>No Price Here</h1>
<meta itemprop="sku" content="100099999">
<span itemprop="brand">Mystery</span></body></html>
"""

NO_SKU_NO_META_HTML = """
<html><body><h1>Bare-Bones Product</h1>
<span itemprop="price">$5.00</span></body></html>
"""

BODY_SCAN_PRICE_HTML = """
<html><body><h1>Body-Scan Fallback Product</h1>
<meta itemprop="sku" content="100099777">
<p>Was $99.99 — now on sale for only $79.95 today!</p>
</body></html>
"""

UOM_VARIANTS_HTML = {
    "structured_dt": (
        '<dl><dt>Unit of Measure</dt><dd>case of 50</dd></dl>'
    ),
    "structured_uom_class": (
        '<div class="uom">box of 100</div>'
    ),
    "structured_unit_of_measure_class": (
        '<div class="unit-of-measure">bundle of 12</div>'
    ),
    "structured_sales_unit_class": (
        '<span class="sales-unit">2 lbs</span>'
    ),
    "structured_sold_by": (
        '<span>Sold by</span><span>pack of 25</span>'
    ),
    "keyword_each": "<p>This product is sold each.</p>",
    "keyword_gallon": "<p>1 gallon container</p>",
    "keyword_box": "<p>Sold by the box</p>",
    "keyword_lbs": "<p>5 lbs per bag</p>",
    "no_uom_at_all": "<p>No measure info anywhere.</p>",
}

CAPTCHA_WITH_DATA_HTML = """
<html><head><title>Access Denied</title>
<meta itemprop="sku" content="100120362"></head>
<body><h1>Access Denied</h1>
<span itemprop="price">$3.45</span></body></html>
"""


# ---------------------------------------------------------------------------
# HTML entity / tag normalisation
# ---------------------------------------------------------------------------


def test_decode_html_handles_common_entities() -> None:
    assert decode_html("3/4 &quot; pipe") == '3/4 " pipe'
    assert decode_html("A &amp; B") == "A & B"
    assert decode_html("&lt;tag&gt;") == "<tag>"
    assert decode_html("&apos;quoted&apos;") == "'quoted'"
    assert decode_html("A&nbsp;B") == "A B"
    assert decode_html("") == ""
    assert decode_html(None) == ""  # type: ignore[arg-type]


def test_strip_tags_removes_inline_markup() -> None:
    """Each tag is replaced with a single space; the strip() at the
    outer boundary handles leading/trailing whitespace, but interior
    space runs are NOT collapsed (callers that need normalised
    whitespace re-run their own collapse).
    """
    assert strip_tags("<b>Hi</b>") == "Hi"
    assert strip_tags('<a href="#">Click</a>').strip() == "Click"
    # Each of "<em>" and "</em>" turn into 1 space → " there " sandwiched
    # by space-padded " Hello " on the left and " world " on the right.
    assert strip_tags("<p>Hello <em>there</em> world</p>") == (
        "Hello  there  world"
    )
    assert strip_tags("") == ""
    assert strip_tags("plain text") == "plain text"


def test_strip_tags_does_not_alter_text_with_no_tags() -> None:
    """Body content that already has no tags must be returned unchanged."""
    assert strip_tags("Just plain prose with no tags.") == (
        "Just plain prose with no tags."
    )


# ---------------------------------------------------------------------------
# Microdata extractors
# ---------------------------------------------------------------------------


def test_extract_meta_itemprop_forward_attribute_order() -> None:
    assert extract_meta_itemprop(HD_LIKE_PVC_HTML, "sku") == "100120362"
    assert extract_meta_itemprop(HD_LIKE_PVC_HTML, "brand") == "Charlotte Pipe"


def test_extract_meta_itemprop_reversed_attribute_order() -> None:
    """Some server-side renderers emit ``content=`` before ``itemprop=``."""
    assert extract_meta_itemprop(REVERSED_META_HTML, "sku") == "REV-SKU-001"
    assert extract_meta_itemprop(REVERSED_META_HTML, "price") == "$9.99"


def test_extract_meta_itemprop_missing_returns_none() -> None:
    assert extract_meta_itemprop(HD_LIKE_PVC_HTML, "doesnotexist") is None
    assert extract_meta_itemprop("", "sku") is None
    assert extract_meta_itemprop(None, "sku") is None  # type: ignore[arg-type]


def test_extract_itemprop_text_strips_nested_tags() -> None:
    assert extract_itemprop_text(NESTED_INNER_HTML, "price") == "$ 12.99"
    assert extract_itemprop_text(NESTED_INNER_HTML, "brand") == "Acme"


def test_extract_itemprop_text_missing_returns_none() -> None:
    assert extract_itemprop_text(HD_LIKE_PVC_HTML, "doesnotexist") is None
    assert extract_itemprop_text("", "price") is None


def test_extract_itemprop_text_special_chars_decoded() -> None:
    """HTML entities inside the itemprop content are decoded."""
    html = '<span itemprop="dim">3/4 &quot; coupling</span>'
    assert extract_itemprop_text(html, "dim") == '3/4 " coupling'


# ---------------------------------------------------------------------------
# Title extraction (with adapter-specific suffix stripping)
# ---------------------------------------------------------------------------


def test_extract_title_prefers_h1_over_title_tag() -> None:
    """When both ``<h1>`` and ``<title>`` are present, ``<h1>`` wins."""
    title = extract_title(
        HD_LIKE_PVC_HTML,
        title_suffixes=(" - The Home Depot",),
    )
    assert title == "3/4 in. x 10 ft. PVC Schedule 40 Plain End Pipe"


def test_extract_title_strips_known_suffix_from_title_tag() -> None:
    """``<title>`` content gets its storefront suffix stripped; ``<h1>``
    content does not (storefront branding only lives in ``<title>``)."""
    html = "<html><head><title>Foo Product - The Home Depot</title></head></html>"
    assert extract_title(
        html, title_suffixes=(" - The Home Depot",),
    ) == "Foo Product"


def test_extract_title_with_multiple_suffix_candidates() -> None:
    """Multiple suffix candidates are tried in order; the first match wins."""
    html = "<html><head><title>Bar Product | Lowe's for Pros</title></head></html>"
    assert extract_title(
        html,
        title_suffixes=(
            " | Lowe's",
            " | Lowe's for Pros",
        ),
    ) == "Bar Product"


def test_extract_title_returns_none_for_empty_html() -> None:
    assert extract_title("", title_suffixes=()) is None


def test_extract_title_no_suffix_match_returns_full_title() -> None:
    html = "<html><head><title>Unbranded Product</title></head></html>"
    assert extract_title(
        html, title_suffixes=(" - The Home Depot",),
    ) == "Unbranded Product"


# ---------------------------------------------------------------------------
# Price parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, expected",
    [
        ("$12.34", 12.34),
        ("12.34", 12.34),
        ("$1,234.56", 1234.56),
        ("$ 3.45", 3.45),
        ("$5,399.00", 5399.0),
        ("Now $89.99", 89.99),
        ("$0.89", 0.89),
    ],
)
def test_parse_price_accepts_common_token_shapes(
    text: str, expected: float,
) -> None:
    val = parse_price(text)
    assert val is not None
    assert val == pytest.approx(expected)


def test_parse_price_rejects_empty_and_non_numeric() -> None:
    assert parse_price("") is None
    assert parse_price(None) is None
    assert parse_price("no price here") is None
    assert parse_price("call for price") is None


def test_parse_price_rejects_implausible_values() -> None:
    """Values outside MIN_PLAUSIBLE_PRICE..MAX_PLAUSIBLE_PRICE → None."""
    assert parse_price("$0.00") is None
    assert parse_price("$200,000.00") is None
    assert parse_price(f"${MAX_PLAUSIBLE_PRICE * 2:.2f}") is None
    assert MIN_PLAUSIBLE_PRICE == 0.05
    assert MAX_PLAUSIBLE_PRICE == 100_000.0


# ---------------------------------------------------------------------------
# Unit-of-measure parsing
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "html, expected",
    [
        (UOM_VARIANTS_HTML["structured_dt"], "case of 50"),
        (UOM_VARIANTS_HTML["structured_uom_class"], "box of 100"),
        (UOM_VARIANTS_HTML["structured_unit_of_measure_class"], "bundle of 12"),
        (UOM_VARIANTS_HTML["structured_sales_unit_class"], "2 lbs"),
        (UOM_VARIANTS_HTML["structured_sold_by"], "pack of 25"),
        (UOM_VARIANTS_HTML["keyword_each"], "each"),
        (UOM_VARIANTS_HTML["keyword_gallon"], "gallon"),
        (UOM_VARIANTS_HTML["keyword_box"], "box"),
        (UOM_VARIANTS_HTML["keyword_lbs"], "5 lbs"),
        (UOM_VARIANTS_HTML["no_uom_at_all"], "each"),
        ("", "each"),
    ],
)
def test_parse_unit_of_measure_variants(html: str, expected: str) -> None:
    assert parse_unit_of_measure(html) == expected


def test_parse_unit_of_measure_multi_anchor_fallback_chain() -> None:
    """Order matters: when a structured selector matches, the keyword
    fallback is not consulted (verbatim wins). When NO structured
    selector matches, the keyword fallback fires."""
    structured_only = (
        '<div class="uom">verbatim-wins</div>'
        '<p>This is sold each.</p>'
    )
    assert parse_unit_of_measure(structured_only) == "verbatim-wins"

    keyword_only = "<p>Sold by the case</p>"
    assert parse_unit_of_measure(keyword_only) == "case"


# ---------------------------------------------------------------------------
# CAPTCHA / anti-bot detection
# ---------------------------------------------------------------------------


def test_looks_like_captcha_detects_pardon_our_interruption() -> None:
    assert looks_like_captcha(CAPTCHA_HTML) is True


def test_looks_like_captcha_detects_access_denied() -> None:
    assert looks_like_captcha(CAPTCHA_WITH_DATA_HTML) is True


def test_looks_like_captcha_negative_on_real_product_html() -> None:
    assert looks_like_captcha(HD_LIKE_PVC_HTML) is False
    assert looks_like_captcha(LOWES_LIKE_PVC_HTML) is False


def test_looks_like_captcha_negative_on_empty() -> None:
    assert looks_like_captcha("") is False
    assert looks_like_captcha(None) is False  # type: ignore[arg-type]


def test_looks_like_captcha_custom_marker_list() -> None:
    """A caller can pass a custom marker list to extend or override
    the default detector."""
    custom_markers = ["site-specific-block-phrase"]
    block_html = "<html><body>You hit our site-specific-block-phrase</body></html>"
    assert looks_like_captcha(block_html, custom_markers) is True
    assert looks_like_captcha(CAPTCHA_HTML, custom_markers) is False


def test_default_captcha_markers_lower_case_substring() -> None:
    """Default markers are all lowercase substrings; detection is
    case-insensitive via the html-lowering step."""
    for marker in DEFAULT_CAPTCHA_MARKERS:
        assert marker == marker.lower()


# ---------------------------------------------------------------------------
# Composed parser
# ---------------------------------------------------------------------------


def test_parse_product_page_returns_dict_on_hd_like_html() -> None:
    parsed = parse_product_page(
        HD_LIKE_PVC_HTML, sku="100120362",
        adapter_name="test_adapter",
        title_suffixes=(" - The Home Depot",),
    )
    assert parsed is not None
    assert parsed["sku"] == "100120362"
    assert "PVC Schedule 40" in parsed["title"]
    assert parsed["brand"] == "Charlotte Pipe"
    assert parsed["mpn"] == "PVC074"
    assert parsed["price"] == pytest.approx(3.45)
    assert parsed["price_raw"] == "$3.45"
    assert parsed["unit"] == "each"


def test_parse_product_page_returns_dict_on_lowes_like_html() -> None:
    parsed = parse_product_page(
        LOWES_LIKE_PVC_HTML, sku="1099113",
        adapter_name="test_adapter",
        title_suffixes=(" | Lowe's",),
    )
    assert parsed is not None
    assert parsed["sku"] == "1099113"
    assert "PVC Sch 40" in parsed["title"]
    assert parsed["brand"] == "Charlotte Pipe"
    assert parsed["mpn"] == "PVC074-LOWES"
    assert parsed["price"] == pytest.approx(3.78)
    assert parsed["unit"] == "each"


def test_parse_product_page_returns_none_for_empty_html() -> None:
    assert parse_product_page(
        "", sku="x", adapter_name="test_adapter",
    ) is None


def test_parse_product_page_returns_none_for_captcha() -> None:
    parsed = parse_product_page(
        CAPTCHA_HTML, sku="100120362", adapter_name="test_adapter",
    )
    assert parsed is None


def test_parse_product_page_captcha_wins_over_product_data() -> None:
    """When the page carries BOTH a CAPTCHA marker AND a price, the
    CAPTCHA check wins — better to skip than emit a misleading
    snapshot from a partially-rendered block page."""
    parsed = parse_product_page(
        CAPTCHA_WITH_DATA_HTML, sku="100120362",
        adapter_name="test_adapter",
    )
    assert parsed is None


def test_parse_product_page_returns_none_when_no_price() -> None:
    parsed = parse_product_page(
        NO_PRICE_HTML, sku="100099999", adapter_name="test_adapter",
    )
    assert parsed is None


def test_parse_product_page_falls_back_to_caller_sku() -> None:
    """When ``<meta itemprop="sku">`` is absent the caller-supplied SKU
    is used as the parsed value."""
    parsed = parse_product_page(
        NO_SKU_NO_META_HTML, sku="CALLER-SKU",
        adapter_name="test_adapter",
    )
    assert parsed is not None
    assert parsed["sku"] == "CALLER-SKU"


def test_parse_product_page_body_scan_finds_price_as_last_resort() -> None:
    """When neither ``itemprop`` nor ``meta`` carries the price, a body
    scan picks up the first ``$N.NN`` token."""
    parsed = parse_product_page(
        BODY_SCAN_PRICE_HTML, sku="100099777",
        adapter_name="test_adapter",
    )
    assert parsed is not None
    # The first $-prefixed token in the body is "$99.99" (the "was"
    # price); the body scan deliberately captures the FIRST token so
    # adapter authors can layer in promo-price detection later if
    # needed.
    assert parsed["price"] == pytest.approx(99.99)


def test_parse_product_page_decodes_special_chars_in_title() -> None:
    parsed = parse_product_page(
        SPECIAL_CHAR_HTML, sku="100120999",
        adapter_name="test_adapter",
        title_suffixes=(" - The Home Depot",),
    )
    assert parsed is not None
    assert '"' in parsed["title"]
    assert "3/4" in parsed["title"]


def test_parse_product_page_uses_adapter_specific_captcha_markers() -> None:
    """A custom CAPTCHA marker list shorts-circuits the parser even
    when the standard markers wouldn't fire."""
    custom_block_html = (
        "<html><body><h1>retailer-x-block</h1>"
        '<span itemprop="price">$5.00</span>'
        '<meta itemprop="sku" content="X"></body></html>'
    )
    parsed = parse_product_page(
        custom_block_html, sku="X",
        adapter_name="test_adapter",
        captcha_markers=["retailer-x-block"],
    )
    assert parsed is None


def test_parse_product_page_brand_optional_field() -> None:
    """Brand is optional — absent → None, present → preserved."""
    no_brand_html = """
    <html><head><meta itemprop="sku" content="NB-1"></head>
    <body><h1>Brandless Product</h1>
    <span itemprop="price">$10.00</span></body></html>
    """
    parsed = parse_product_page(
        no_brand_html, sku="NB-1", adapter_name="test_adapter",
    )
    assert parsed is not None
    assert parsed["brand"] is None


def test_parse_product_page_mpn_chained_fallbacks() -> None:
    """MPN tries ``itemprop="mpn"`` (span), then ``meta itemprop="mpn"``,
    then ``meta itemprop="model"`` — pin all three fallback paths."""
    meta_mpn_html = """
    <html><head><meta itemprop="sku" content="M1"><meta itemprop="mpn" content="META-MPN"></head>
    <body><h1>P</h1><span itemprop="price">$10.00</span></body></html>
    """
    parsed = parse_product_page(
        meta_mpn_html, sku="M1", adapter_name="test_adapter",
    )
    assert parsed is not None
    assert parsed["mpn"] == "META-MPN"

    meta_model_html = """
    <html><head><meta itemprop="sku" content="M2"><meta itemprop="model" content="META-MODEL"></head>
    <body><h1>P</h1><span itemprop="price">$10.00</span></body></html>
    """
    parsed = parse_product_page(
        meta_model_html, sku="M2", adapter_name="test_adapter",
    )
    assert parsed is not None
    assert parsed["mpn"] == "META-MODEL"


def test_parse_product_page_title_fallback_when_no_h1_no_title_tag() -> None:
    """When neither ``<h1>`` nor ``<title>`` is present, the parser
    falls back to ``"SKU <sku>"`` so the returned dict always has a
    usable label."""
    no_title_html = """
    <html><body><meta itemprop="sku" content="NT-1">
    <span itemprop="price">$10.00</span></body></html>
    """
    parsed = parse_product_page(
        no_title_html, sku="NT-1", adapter_name="test_adapter",
    )
    assert parsed is not None
    assert parsed["title"] == "SKU NT-1"
