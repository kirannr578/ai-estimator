"""Unit tests for ``core/pricing/sources/lowes_pro.py``.

Mirrors ``tests/test_pricing_sources_hd_pro.py`` because both adapters
parse the same schema.org-microdata vocabulary and degrade against the
same Akamai bot-protection posture. All HTTP is mocked via
``httpx.MockTransport`` so the tests run offline.
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
from core.pricing.sources.lowes_pro import (
    DEFAULT_SKUS,
    LOWES_BASE_URL,
    LOWES_PRO_HOMEPAGE,
    LowesProSource,
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
<title>3/4-in x 10-ft PVC Pipe | Lowe's</title>
<meta itemprop="sku" content="1099113">
<meta itemprop="brand" content="Charlotte Pipe">
</head>
<body>
<h1 class="product-title">3/4-in x 10-ft PVC Sch 40 Pipe</h1>
<span itemprop="brand">Charlotte Pipe</span>
<span itemprop="price">$3.78</span>
<span itemprop="mpn">PVC074-LOWES</span>
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
<title>Drywall Screws 1 lb | Lowe's</title>
<meta itemprop="sku" content="73268">
</head>
<body>
<h1>Drywall Screws, Coarse Thread - 1 lb</h1>
<span itemprop="brand">Grip-Rite</span>
<span itemprop="price">$9.28</span>
<span itemprop="mpn">DWS158C1-L</span>
<div class="unit-of-measure">box of 100</div>
</body>
</html>
"""

PAINT_HTML = """
<html>
<head>
<title>Interior Latex Paint, 1 gal | Lowe's</title>
<meta itemprop="sku" content="1003356">
</head>
<body>
<h1>Valspar Premium Interior Eggshell - 1 Gallon</h1>
<span itemprop="brand">Valspar</span>
<span itemprop="price">$34.99</span>
<span itemprop="mpn">VAL-PREM-EGG-G</span>
<div class="uom">gallon</div>
</body>
</html>
"""

GENERATOR_HTML = """
<html>
<head>
<title>Whole-House Generator 22kW | Lowe's</title>
<meta itemprop="sku" content="1330001">
</head>
<body>
<h1>Whole-House Generator, 22kW Air-Cooled</h1>
<span itemprop="brand">Generac</span>
<span itemprop="price">$5,499.00</span>
<span itemprop="mpn">7043-L</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

SPECIAL_CHAR_HTML = """
<html>
<head>
<title>3/4 &quot; PVC Coupling | Lowe's</title>
<meta itemprop="sku" content="1099199">
</head>
<body>
<h1>3/4 &quot; PVC Coupling Slip x Slip</h1>
<span itemprop="price">$0.92</span>
<span itemprop="mpn">CPLG34-L</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

NO_META_SKU_HTML = """
<html>
<head>
<title>Some Product | Lowe's</title>
</head>
<body>
<h1>A Product Without Meta SKU</h1>
<span itemprop="price">$10.50</span>
<dl><dt>Unit of Measure</dt><dd>each</dd></dl>
</body>
</html>
"""

NO_PRICE_HTML = """
<html>
<head>
<title>Some Product | Lowe's</title>
<meta itemprop="sku" content="9999999">
</head>
<body>
<h1>A Product Without A Price</h1>
<span itemprop="brand">Mystery Brand</span>
</body>
</html>
"""

NO_UOM_HTML = """
<html>
<head>
<title>UoM-less Product | Lowe's</title>
<meta itemprop="sku" content="9999000">
</head>
<body>
<h1>A Product Without A Unit Of Measure</h1>
<span itemprop="price">$15.99</span>
<span itemprop="mpn">UNK01-L</span>
</body>
</html>
"""

CAPTCHA_HTML = """
<html>
<head><title>Access Denied</title></head>
<body>
<h1>Access Denied</h1>
<p>You don't have permission to access "/" on this server.</p>
<p>Reference #18.akamai-edgesuite.foo.bar</p>
</body>
</html>
"""

CAPTCHA_PLUS_DATA_HTML = """
<html>
<head>
<title>Pardon Our Interruption</title>
<meta itemprop="sku" content="1099113">
</head>
<body>
<h1>Pardon Our Interruption...</h1>
<span itemprop="price">$3.78</span>
</body>
</html>
"""

LUMBER_HTML = """
<html>
<head>
<title>2x4x8 SPF Stud | Lowe's</title>
<meta itemprop="sku" content="12533">
</head>
<body>
<h1>2-in x 4-in x 8-ft Whitewood Stud</h1>
<span itemprop="brand">Top Choice</span>
<meta itemprop="price" content="3.92">
<span itemprop="mpn">SPF208-L</span>
<div class="unit-of-measure">each</div>
</body>
</html>
"""

CASE_OF_50_HTML = """
<html>
<head>
<title>Roofing Nails Case | Lowe's</title>
<meta itemprop="sku" content="12553">
</head>
<body>
<h1>Roofing Nails, Galvanized 1-1/4 in.</h1>
<span itemprop="price">$26.50</span>
<span itemprop="mpn">RN114-50-L</span>
<div class="unit-of-measure">case of 50</div>
</body>
</html>
"""

ONE_LB_HTML = """
<html>
<head>
<title>Finish Nails 1 lb | Lowe's</title>
<meta itemprop="sku" content="12557">
</head>
<body>
<h1>Finish Nails, 8d Bright</h1>
<span itemprop="price">$5.79</span>
<span itemprop="mpn">FN8B-L</span>
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
) -> LowesProSource:
    client = build_client(transport=httpx.MockTransport(handler))
    return LowesProSource(
        sku_list=sku_list,
        zip_code=zip_code,
        client=client,
        cache_root=tmp_path,
    )


# --- Tests -------------------------------------------------------------


def test_adapter_instantiates_without_error() -> None:
    src = LowesProSource()
    try:
        assert src.name == "lowes_pro"
        assert src.homepage_url == LOWES_PRO_HOMEPAGE
        assert src.requires_env_vars == []
        assert "Lowe" in src.license_str
        assert "redistribution" in src.license_str
        assert src.sku_list == list(DEFAULT_SKUS)
        assert src.default_series() == list(DEFAULT_SKUS)
        assert src.zip_code == "75001"
    finally:
        src.close()


def test_explicit_sku_list_and_zip_propagate() -> None:
    src = LowesProSource(
        sku_list=["aaa", "bbb"], zip_code="90210",
    )
    try:
        assert src.sku_list == ["aaa", "bbb"]
        assert src.zip_code == "90210"
        assert src.default_series() == ["aaa", "bbb"]
    finally:
        src.close()


def test_product_url_construction() -> None:
    assert product_url("1099113") == f"{LOWES_BASE_URL}/pd/1099113"
    assert product_url("1099113", slug="my-product") == (
        f"{LOWES_BASE_URL}/pd/my-product/1099113"
    )
    with pytest.raises(ValueError):
        product_url("")


def test_single_sku_parses_into_one_snapshot(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        snaps = src.fetch([])
    finally:
        src.close()

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "lowes_pro"
    assert s.series_id == "1099113"
    assert "PVC" in s.label
    assert s.unit == "each"
    assert s.value == pytest.approx(3.78)
    assert s.region == "75001"
    assert s.csi_division is None
    assert s.naics is None
    assert s.source_url == product_url("1099113")
    assert "Lowe" in s.license
    assert s.raw is not None
    assert s.raw["sku_requested"] == "1099113"
    assert s.raw["sku_parsed"] == "1099113"
    assert s.raw["brand"] == "Charlotte Pipe"
    assert s.raw["mpn"] == "PVC074-LOWES"
    assert s.raw["price_value_usd"] == pytest.approx(3.78)
    assert s.raw["unit_of_measure"] == "each"
    assert s.raw["zip_code"] == "75001"


def test_multiple_skus_in_fetch_returns_list(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
        product_url("73268"): (200, DRYWALL_SCREWS_HTML),
        product_url("1003356"): (200, PAINT_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["1099113", "73268", "1003356"],
    )
    try:
        snaps = src.fetch([])
    finally:
        src.close()

    assert len(snaps) == 3
    by_sku = {s.series_id: s for s in snaps}
    assert by_sku["1099113"].value == pytest.approx(3.78)
    assert by_sku["73268"].value == pytest.approx(9.28)
    assert by_sku["1003356"].value == pytest.approx(34.99)


def test_fetch_recent_iterates_configured_sku_list(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
        product_url("73268"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path, sku_list=["1099113", "73268"],
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 2
    assert {s.series_id for s in snaps} == {"1099113", "73268"}


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

    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_http_503_graceful_empty_in_fetch_recent(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
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
            src.fetch_one("1099113")
    finally:
        src.close()


def test_fetch_one_503_raises(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_one("1099113")
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
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snap = src.fetch_one("1099113")
    finally:
        src.close()

    assert isinstance(snap, PricingSnapshot)
    assert snap.series_id == "1099113"
    assert snap.value == pytest.approx(3.78)


def test_captcha_page_returns_empty_with_warning(
    tmp_path: Path, caplog: pytest.LogCaptureFixture,
) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, CAPTCHA_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    caplog.set_level(
        logging.WARNING, logger="core.pricing.sources.lowes_pro",
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []
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
        product_url("1099113"): (200, CAPTCHA_PLUS_DATA_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_missing_meta_sku_falls_back_to_caller_sku(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("9999001"): (200, NO_META_SKU_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["9999001"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].series_id == "9999001"
    assert snaps[0].raw["sku_parsed"] == "9999001"


def test_missing_price_skipped(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("9999999"): (200, NO_PRICE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["9999999"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert snaps == []


def test_missing_uom_falls_back_to_each(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("9999000"): (200, NO_UOM_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["9999000"])
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
        ("$5,499.00", 5499.00),
        ("Now $89.99", 89.99),
        ("$ 3.78", 3.78),
    ],
)
def test_price_parsing_variants(price_text: str, expected: float) -> None:
    val = parse_price(price_text)
    assert val is not None
    assert val == pytest.approx(expected)


def test_price_parsing_rejects_no_token() -> None:
    assert parse_price("") is None
    assert parse_price(None) is None
    assert parse_price("no price here") is None


def test_price_parsing_rejects_implausible_values() -> None:
    assert parse_price("$0.00") is None
    assert parse_price("$200,000.00") is None


def test_thousands_separator_price(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1330001"): (200, GENERATOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1330001"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(5499.00)


def test_no_dollar_sign_meta_price(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("12533"): (200, LUMBER_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["12533"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(3.92)


def test_box_of_100_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("73268"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["73268"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "box of 100"


def test_case_of_50_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("12553"): (200, CASE_OF_50_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["12553"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "case of 50"


def test_one_lb_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("12557"): (200, ONE_LB_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["12557"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "1 lb"


def test_gallon_uom_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1003356"): (200, PAINT_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1003356"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].unit == "gallon"


def test_special_characters_in_title_preserved(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099199"): (200, SPECIAL_CHAR_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099199"])
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 1
    assert '"' in snaps[0].label
    assert "3/4" in snaps[0].label


def test_zip_code_is_persisted_to_region(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["1099113"],
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
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
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
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        snap = src.fetch_one("1099113")
    finally:
        src.close()
    assert snap.series_id == "1099113"
    assert snap.raw["sku_parsed"] == "1099113"


def test_raw_dict_contains_full_scraped_attrs(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("73268"): (200, DRYWALL_SCREWS_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["73268"])
    try:
        snap = src.fetch_one("73268")
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
    assert raw["mpn"] == "DWS158C1-L"
    assert raw["unit_of_measure"] == "box of 100"


def test_snapshot_serialization_round_trip(tmp_path: Path) -> None:
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        snap = src.fetch_one("1099113")
    finally:
        src.close()
    blob = snap.to_json()
    round_tripped = PricingSnapshot.from_json(blob)
    assert round_tripped.value == pytest.approx(3.78)
    assert round_tripped.series_id == "1099113"
    assert round_tripped.source == "lowes_pro"
    assert round_tripped.unit == "each"


def test_cache_hit_no_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=PVC_PIPE_HTML)

    src = _build_mock_source(handler, tmp_path, sku_list=["1099113"])
    try:
        src.fetch_one("1099113")
        src.fetch_one("1099113")
    finally:
        src.close()
    assert call_count["n"] == 1


def test_is_captcha_page_detection() -> None:
    assert is_captcha_page(CAPTCHA_HTML) is True
    assert is_captcha_page(PVC_PIPE_HTML) is False
    assert is_captcha_page("") is False
    assert is_captcha_page(None) is False  # type: ignore[arg-type]
    assert is_captcha_page(
        "<html><body>Bot detected</body></html>"
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
        sku="1099113",
        source_url="https://example.com",
        zip_code="75001",
        license_str="test",
        adapter_name="lowes_pro",
    )
    assert snap is None


def test_parse_product_page_returns_none_for_captcha() -> None:
    snap = parse_product_page(
        CAPTCHA_HTML,
        sku="1099113",
        source_url="https://example.com",
        zip_code="75001",
        license_str="test",
        adapter_name="lowes_pro",
    )
    assert snap is None


def test_explicit_period_override(tmp_path: Path) -> None:
    """fetch_one() honors an explicit period argument."""
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snap = src.fetch_one("1099113", period="2026-01-15")
    finally:
        src.close()
    assert snap.period == "2026-01-15"


def test_default_skus_populated_with_starter_set() -> None:
    assert len(DEFAULT_SKUS) >= 5
    assert all(isinstance(s, str) for s in DEFAULT_SKUS)
    assert all(s.strip() for s in DEFAULT_SKUS)


def test_partial_failure_returns_partial_list(tmp_path: Path) -> None:
    """If 1 of 3 SKUs fails, return the 2 successes (graceful)."""
    handler = _route_handler({
        product_url("1099113"): (200, PVC_PIPE_HTML),
        product_url("1003356"): (200, PAINT_HTML),
    })
    src = _build_mock_source(
        handler, tmp_path,
        sku_list=["1099113", "1003356", "99999999"],
    )
    try:
        snaps = src.fetch_recent()
    finally:
        src.close()
    assert len(snaps) == 2
    assert {s.series_id for s in snaps} == {"1099113", "1003356"}
