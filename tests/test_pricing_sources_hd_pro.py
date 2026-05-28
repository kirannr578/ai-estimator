"""Unit tests for ``core/pricing/sources/hd_pro.py``.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in
``tests/test_pricing_sources_tx_smartbuy_awards.py``.

The Home Depot catalog adapter ships behind documented anti-bot
fragility (Akamai-fronted JS shell + CAPTCHA). These tests exercise:

- Successful parses against synthetic schema.org-microdata HTML.
- Graceful-empty behavior on 4xx / 5xx and on CAPTCHA / anti-bot
  interstitial pages.
- The brief's parsing edge cases (multi-pack UoM, missing fields,
  multiple price formats, special characters in the title).
- The ``fetch_one()`` raising contract for one-off CLI lookups.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable

import httpx
import pytest

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import PricingSourceUnavailable
from core.pricing.sources.base import build_client
from core.pricing.sources.hd_pro import (
    DEFAULT_SKUS,
    HD_BASE_URL,
    HD_PRO_HOMEPAGE,
    HomeDepotProSource,
    is_captcha_page,
    parse_price,
    parse_product_page,
    parse_unit_of_measure,
    product_url,
)


# --- HTML fixtures -----------------------------------------------------

PVC_PIPE_HTML = """
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
<dl>
  <dt>Unit of Measure</dt>
  <dd>each</dd>
</dl>
</body>
</html>
"""

DRYWALL_SCREWS_HTML = """
<html>
<head>
<title>Drywall Screws 1 lb - The Home Depot</title>
<meta itemprop="sku" content="202079922">
</head>
<body>
<h1>Drywall Screws, Coarse Thread - 1 lb</h1>
<span itemprop="brand">Grip-Rite</span>
<span itemprop="price">$8.97</span>
<span itemprop="mpn">DWS158C1</span>
<div class="unit-of-measure">box of 100</div>
</body>
</html>
"""

PAINT_HTML = """
<html>
<head>
<title>Interior Latex Paint, 1 gal - The Home Depot</title>
<meta itemprop="sku" content="203083697">
</head>
<body>
<h1>Behr Premium Plus Interior Eggshell Enamel - 1 Gallon</h1>
<span itemprop="brand">Behr</span>
<span itemprop="price">$32.99</span>
<span itemprop="mpn">PR12P</span>
<div class="uom">gallon</div>
</body>
</html>
"""

# Comma-formatted price (e.g. whole-house generator).
GENERATOR_HTML = """
<html>
<head>
<title>Whole-House Generator 22kW - The Home Depot</title>
<meta itemprop="sku" content="100330001">
</head>
<body>
<h1>Whole-House Generator, 22kW Air-Cooled</h1>
<span itemprop="brand">Generac</span>
<span itemprop="price">$5,399.00</span>
<span itemprop="mpn">7043</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

# Special characters in title — fraction + double-quote inch mark.
SPECIAL_CHAR_HTML = """
<html>
<head>
<title>3/4 &quot; PVC Coupling - The Home Depot</title>
<meta itemprop="sku" content="100120999">
</head>
<body>
<h1>3/4 &quot; PVC Coupling Slip x Slip</h1>
<span itemprop="price">$0.89</span>
<span itemprop="mpn">CPLG34</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

# Missing meta itemprop="sku" (we still parse via caller-supplied SKU).
NO_META_SKU_HTML = """
<html>
<head>
<title>Some Product - The Home Depot</title>
</head>
<body>
<h1>A Product Without Meta SKU</h1>
<span itemprop="price">$10.00</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

# Missing price entirely — should be skipped.
NO_PRICE_HTML = """
<html>
<head>
<title>Some Product - The Home Depot</title>
<meta itemprop="sku" content="100099999">
</head>
<body>
<h1>A Product Without A Price</h1>
<span itemprop="brand">Mystery Brand</span>
</body>
</html>
"""

# Missing UoM entirely — should fall back to "each".
NO_UOM_HTML = """
<html>
<head>
<title>UoM-less Product - The Home Depot</title>
<meta itemprop="sku" content="100099000">
</head>
<body>
<h1>A Product Without A Unit Of Measure</h1>
<span itemprop="price">$15.50</span>
<span itemprop="mpn">UNK01</span>
</body>
</html>
"""

# CAPTCHA / anti-bot page — must be detected and skipped.
CAPTCHA_HTML = """
<html>
<head><title>Pardon Our Interruption</title></head>
<body>
<h1>Pardon Our Interruption...</h1>
<p>As you were browsing, something about your browser made us think you
were a bot. There are a few reasons this might happen.</p>
<a href="/_Incapsula_Resource?CWUDNSAI=...">Continue</a>
</body>
</html>
"""

# CAPTCHA marker AND product-like data on the same page — CAPTCHA wins.
CAPTCHA_PLUS_DATA_HTML = """
<html>
<head>
<title>Pardon Our Interruption</title>
<meta itemprop="sku" content="100120362">
</head>
<body>
<h1>Pardon Our Interruption...</h1>
<span itemprop="price">$3.45</span>
</body>
</html>
"""

# Lumber 2x4x8 — bare-no-dollar-sign price token in body.
LUMBER_HTML = """
<html>
<head>
<title>2x4x8 SPF Stud - The Home Depot</title>
<meta itemprop="sku" content="100133104">
</head>
<body>
<h1>2 in. x 4 in. x 96 in. Premium Kiln-Dried Heat-Treated SPF Stud</h1>
<span itemprop="brand">Unbranded</span>
<meta itemprop="price" content="3.78">
<span itemprop="mpn">SPF208</span>
<div class="unit-of-measure">each</div>
</body>
</html>
"""

# "case of 50" multi-pack UoM.
CASE_OF_50_HTML = """
<html>
<head>
<title>Roofing Nails - The Home Depot</title>
<meta itemprop="sku" content="100107516">
</head>
<body>
<h1>Roofing Nails, Galvanized 1-1/4 in.</h1>
<span itemprop="price">$24.50</span>
<span itemprop="mpn">RN114-50</span>
<div class="unit-of-measure">case of 50</div>
</body>
</html>
"""

# "1 lb" verbatim UoM.
ONE_LB_HTML = """
<html>
<head>
<title>Finish Nails 1 lb - The Home Depot</title>
<meta itemprop="sku" content="100107520">
</head>
<body>
<h1>Finish Nails, 8d Bright</h1>
<span itemprop="price">$5.49</span>
<span itemprop="mpn">FN8B</span>
<dl><dt>Unit of Measure</dt><dd>1 lb</dd></dl>
</body>
</html>
"""


# --- Helpers -----------------------------------------------------------


def _route_handler(routes: dict[str, tuple[int, str]]) -> Callable:
    """Build an ``httpx.MockTransport`` handler from URL→(status, body)."""
    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        for pattern, (status, body) in routes.items():
            if url == pattern or url.endswith(pattern):
                return httpx.Response(status, text=body)
        return httpx.Response(404, text="not found")
    return handler


def _build_mock_source(
    handler, tmp_path: Path, sku_list=None, zip_code: str = "75001",
) -> HomeDepotProSource:
    client = build_client(transport=httpx.MockTransport(handler))
    return HomeDepotProSource(
        sku_list=sku_list,
        zip_code=zip_code,
        client=client,
        cache_root=tmp_path,
    )


# --- Tests -------------------------------------------------------------


def test_adapter_instantiates_without_error() -> None:
    src = HomeDepotProSource()
    try:
        assert src.name == "hd_pro"
        assert src.homepage_url == HD_PRO_HOMEPAGE
        assert src.requires_env_vars == []
        assert "Home Depot" in src.license_str
        assert "redistribution" in src.license_str
        # Default sku_list is the module-level DEFAULT_SKUS.
        assert src.sku_list == list(DEFAULT_SKUS)
        assert src.default_series() == list(DEFAULT_SKUS)
        assert src.zip_code == "75001"
    finally:
        src.close()


def test_explicit_sku_list_and_zip_propagate() -> None:
    src = HomeDepotProSource(
        sku_list=["aaa", "bbb"], zip_code="90210",
    )
    try:
        assert src.sku_list == ["aaa", "bbb"]
        assert src.zip_code == "90210"
        assert src.default_series() == ["aaa", "bbb"]
    finally:
        src.close()


def test_product_url_construction() -> None:
    assert product_url("100120362") == f"{HD_BASE_URL}/p/100120362"
    assert product_url("100120362", slug="my-product") == (
        f"{HD_BASE_URL}/p/my-product/100120362"
    )
    with pytest.raises(ValueError):
        product_url("")


def test_single_sku_parses_into_one_snapshot(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snaps = src.fetch([])
    finally:
        src.close()

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "hd_pro"
    assert s.series_id == "100120362"
    assert "PVC Schedule 40" in s.label
    assert s.unit == "each"
    assert s.value == pytest.approx(3.45)
    assert s.region == "75001"
    assert s.csi_division is None
    assert s.naics is None
    assert s.source_url == product_url("100120362")
    assert "Home Depot" in s.license
    assert s.raw is not None
    assert s.raw["sku_requested"] == "100120362"
    assert s.raw["sku_parsed"] == "100120362"
    assert s.raw["brand"] == "Charlotte Pipe"
    assert s.raw["mpn"] == "PVC074"
    assert s.raw["price_value_usd"] == pytest.approx(3.45)
    assert s.raw["unit_of_measure"] == "each"
    assert s.raw["zip_code"] == "75001"


def test_multiple_skus_in_fetch_returns_list(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
        product_url("202079922"): (200, DRYWALL_SCREWS_HTML),
        product_url("203083697"): (200, PAINT_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["100120362", "202079922", "203083697"],
    )
    try:
        snaps = src.fetch([])
    finally:
        src.close()

    assert len(snaps) == 3
    series = sorted(s.series_id for s in snaps)
    assert series == ["100120362", "202079922", "203083697"]
    by_sku = {s.series_id: s for s in snaps}
    assert by_sku["100120362"].value == pytest.approx(3.45)
    assert by_sku["202079922"].value == pytest.approx(8.97)
    assert by_sku["203083697"].value == pytest.approx(32.99)


def test_fetch_recent_iterates_configured_sku_list(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
        product_url("202079922"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path, sku_list=["100120362", "202079922"],
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()

    assert len(snaps) == 2
    assert {s.series_id for s in snaps} == {"100120362", "202079922"}


def test_empty_sku_list_returns_empty(tmp_path: Path) -> None:
    handler = _route_handler({})
    src = _build_mock_source(handler, tmp_path, sku_list=[])
    try:
        snaps = src.fetch([])
        assert snaps == []
        snaps2 = src.fetch_recent()
        assert snaps2 == []
    finally:
        src.close()


def test_http_404_graceful_empty_in_fetch_recent(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_http_503_graceful_empty_in_fetch_recent(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_fetch_one_404_raises(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_one("100120362")
    finally:
        src.close()


def test_fetch_one_503_raises(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_one("100120362")
    finally:
        src.close()


def test_fetch_one_empty_sku_raises(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_one("")
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_one("   ")
    finally:
        src.close()


def test_fetch_one_success_returns_single_snapshot(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snap = src.fetch_one("100120362")
    finally:
        src.close()

    assert isinstance(snap, PricingSnapshot)
    assert snap.series_id == "100120362"
    assert snap.value == pytest.approx(3.45)


def test_captcha_page_returns_empty_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, CAPTCHA_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    caplog.set_level(logging.WARNING, logger="core.pricing.sources.hd_pro")
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []
    # A warning must be emitted somewhere in the log capture for this
    # CAPTCHA event so operators are alerted.
    captcha_warnings = [
        rec for rec in caplog.records
        if "CAPTCHA" in rec.getMessage() or "captcha" in rec.getMessage().lower()
    ]
    assert captcha_warnings, (
        f"expected CAPTCHA warning in log; got {[r.getMessage() for r in caplog.records]}"
    )


def test_captcha_page_with_data_still_returns_empty(tmp_path: Path) -> None:
    """CAPTCHA marker wins even when product-like data is also present."""
    handler = _route_handler({
        product_url("100120362"): (200, CAPTCHA_PLUS_DATA_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_missing_meta_sku_falls_back_to_caller_sku(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100099001"): (200, NO_META_SKU_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100099001"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    # When meta itemprop sku is absent the caller-supplied id is used.
    assert snaps[0].series_id == "100099001"
    assert snaps[0].raw["sku_parsed"] == "100099001"


def test_missing_price_skipped(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100099999"): (200, NO_PRICE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100099999"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    # No price → snapshot skipped, list is empty.
    assert snaps == []


def test_missing_uom_falls_back_to_each(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100099000"): (200, NO_UOM_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100099000"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "each"


@pytest.mark.parametrize(
    "price_text, expected",
    [
        ("$12.34", 12.34),
        ("12.34", 12.34),
        ("$1,234.56", 1234.56),
        ("$1,234,567.89", 1_234_567.89),  # exceeds plausibility floor only
        ("$5,399.00", 5399.00),
        ("Now $89.99", 89.99),
        ("$ 3.45", 3.45),
    ],
)
def test_price_parsing_variants(price_text: str, expected: float) -> None:
    val = parse_price(price_text)
    if expected > 100_000.0:
        # Values above the plausibility ceiling must NOT parse.
        assert val is None
    else:
        assert val is not None
        assert val == pytest.approx(expected)


def test_price_parsing_rejects_no_token() -> None:
    assert parse_price("") is None
    assert parse_price(None) is None
    assert parse_price("no price here") is None


def test_price_parsing_rejects_implausible_values() -> None:
    # 0.0 — must reject as non-positive / below plausibility floor.
    assert parse_price("$0.00") is None
    # Above plausibility ceiling.
    assert parse_price("$200,000.00") is None


def test_thousands_separator_price(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100330001"): (200, GENERATOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100330001"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(5399.00)


def test_no_dollar_sign_meta_price(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100133104"): (200, LUMBER_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100133104"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(3.78)


def test_box_of_100_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("202079922"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["202079922"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "box of 100"


def test_case_of_50_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100107516"): (200, CASE_OF_50_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100107516"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "case of 50"


def test_one_lb_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100107520"): (200, ONE_LB_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100107520"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "1 lb"


def test_gallon_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("203083697"): (200, PAINT_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["203083697"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "gallon"


def test_special_characters_in_title_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120999"): (200, SPECIAL_CHAR_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120999"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    # The title's &quot; entity should be decoded to a literal ".
    assert '"' in snaps[0].label
    assert "3/4" in snaps[0].label


def test_zip_code_is_persisted_to_region(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["100120362"],
        zip_code="90210",
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].region == "90210"
    assert snaps[0].raw["zip_code"] == "90210"


def test_period_is_today_iso_date(tmp_path: Path) -> None:
    """When no period is passed, snapshot.period is today YYYY-MM-DD."""
    from datetime import datetime, timezone
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    today = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    assert snaps[0].period == today


def test_series_id_matches_meta_sku_when_present(tmp_path: Path) -> None:
    """When meta itemprop="sku" present, series_id matches it exactly."""
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snap = src.fetch_one("100120362")
    finally:
        src.close()
    assert snap.series_id == "100120362"
    assert snap.raw["sku_parsed"] == "100120362"


def test_raw_dict_contains_full_scraped_attrs(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("202079922"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["202079922"])
    try:
        snap = src.fetch_one("202079922")
    finally:
        src.close()
    raw = snap.raw
    assert raw is not None
    expected_keys = {
        "sku_requested", "sku_parsed", "title", "brand", "mpn",
        "price_raw", "price_value_usd", "unit_of_measure", "zip_code",
        "fetched_at",
    }
    assert expected_keys.issubset(raw.keys())
    assert raw["brand"] == "Grip-Rite"
    assert raw["mpn"] == "DWS158C1"
    assert raw["unit_of_measure"] == "box of 100"


def test_snapshot_serialization_round_trip(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        snap = src.fetch_one("100120362")
    finally:
        src.close()
    blob = snap.to_json()
    round_tripped = PricingSnapshot.from_json(blob)
    assert round_tripped.value == pytest.approx(3.45)
    assert round_tripped.series_id == "100120362"
    assert round_tripped.source == "hd_pro"
    assert round_tripped.unit == "each"


def test_cache_hit_no_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=PVC_PIPE_HTML)

    src = _build_mock_source(handler, tmp_path, sku_list=["100120362"])
    try:
        src.fetch_one("100120362")
        src.fetch_one("100120362")
    finally:
        src.close()
    assert call_count["n"] == 1


def test_is_captcha_page_detection() -> None:
    assert is_captcha_page(CAPTCHA_HTML) is True
    assert is_captcha_page(PVC_PIPE_HTML) is False
    assert is_captcha_page("") is False
    assert is_captcha_page(None) is False  # type: ignore[arg-type]
    # Embedded marker mid-HTML.
    assert is_captcha_page(
        "<html><body>Access Denied</body></html>"
    ) is True


def test_parse_unit_of_measure_helper_directly() -> None:
    assert parse_unit_of_measure(
        "<dl><dt>Unit of Measure</dt><dd>each</dd></dl>"
    ) == "each"
    assert parse_unit_of_measure(
        '<div class="unit-of-measure">box of 100</div>'
    ) == "box of 100"
    assert parse_unit_of_measure(
        '<div class="uom">case of 50</div>'
    ) == "case of 50"
    assert parse_unit_of_measure("") == "each"
    assert parse_unit_of_measure("<html>no uom anywhere</html>") == "each"


def test_parse_product_page_returns_none_for_empty() -> None:
    snap = parse_product_page(
        "",
        sku="100120362",
        source_url="https://example.com",
        zip_code="75001",
        license_str="test",
        adapter_name="hd_pro",
    )
    assert snap is None


def test_parse_product_page_returns_none_for_captcha() -> None:
    snap = parse_product_page(
        CAPTCHA_HTML,
        sku="100120362",
        source_url="https://example.com",
        zip_code="75001",
        license_str="test",
        adapter_name="hd_pro",
    )
    assert snap is None


def test_explicit_period_override(tmp_path: Path) -> None:
    """fetch_one() honors an explicit period argument."""
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snap = src.fetch_one("100120362", period="2026-01-15")
    finally:
        src.close()
    assert snap.period == "2026-01-15"


def test_default_skus_populated_with_starter_set() -> None:
    """The module-level DEFAULT_SKUS exposes a non-trivial starter set."""
    assert len(DEFAULT_SKUS) >= 5
    assert all(isinstance(s, str) for s in DEFAULT_SKUS)
    assert all(s.strip() for s in DEFAULT_SKUS)


def test_partial_failure_returns_partial_list(tmp_path: Path) -> None:
    """If 1 of 3 SKUs fails, return the 2 successes (graceful)."""
    handler = _route_handler({
        product_url("100120362"): (200, PVC_PIPE_HTML),
        product_url("203083697"): (200, PAINT_HTML),
        # Third SKU intentionally not routed → 404 → swallowed.
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["100120362", "203083697", "99999999"],
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 2
    assert {s.series_id for s in snaps} == {"100120362", "203083697"}
