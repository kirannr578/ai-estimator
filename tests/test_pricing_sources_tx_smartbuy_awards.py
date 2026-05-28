"""Unit tests for ``core/pricing/sources/tx_smartbuy_awards.py``.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in
``tests/test_pricing_sources_turner_cci.py``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable

import httpx
import pytest

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import PricingSourceUnavailable
from core.pricing.sources.base import build_client
from core.pricing.sources.tx_smartbuy_awards import (
    ESBD_BASE_URL,
    TXSmartBuyAwardsSource,
    detail_url,
    html_to_text,
    listing_url,
    parse_award_detail_page,
    parse_award_period,
    parse_dollar_amount,
    parse_listing_for_solicitation_numbers,
)


# --- HTML fixtures ----------------------------------------------------

SINGLE_VENDOR_HTML = """
<html>
<head><title>ESBD 26-007RFCSP</title></head>
<body>
<h1>Solicitation 26-007RFCSP</h1>
<dl class="solicitation-meta">
  <dt>Solicitation ID:</dt><dd>26-007RFCSP</dd>
  <dt>Status:</dt><dd>Awarded</dd>
  <dt>Issuing Agency:</dt><dd>Angelo State University</dd>
  <dt>NAICS Code:</dt><dd>236220</dd>
  <dt>Performance Period:</dt><dd>01/15/2026 through 06/30/2027</dd>
</dl>

<h2>Solicitation Awards</h2>
<dl class="award-block">
  <dt>Awarded Vendor:</dt><dd>ABC Construction LLC</dd>
  <dt>Award Amount:</dt><dd>$1,234,567.89</dd>
  <dt>Award Date:</dt><dd>December 15, 2025</dd>
</dl>
</body>
</html>
"""

MULTI_VENDOR_HTML = """
<html>
<head><title>ESBD 25-100CSP</title></head>
<body>
<h1>Solicitation 25-100CSP — Office Renovation</h1>
<dl class="solicitation-meta">
  <dt>Solicitation ID:</dt><dd>25-100CSP</dd>
  <dt>Status:</dt><dd>Awarded</dd>
  <dt>Issuing Agency:</dt><dd>TAMU System</dd>
  <dt>NAICS Code:</dt><dd>236220</dd>
</dl>

<h2>Solicitation Awards</h2>
<div class="award-block">
  <p>Awarded Vendor: First Builders Group LLC</p>
  <p>Award Amount: $4,500,000.00</p>
  <p>Award Date: 11/30/2025</p>
</div>
<div class="award-block">
  <p>Awarded Vendor: Second Construction Co</p>
  <p>Award Amount: $3,200,000.00</p>
  <p>Award Date: 11/30/2025</p>
</div>
<div class="award-block">
  <p>Awarded Vendor: Third Contractor Inc</p>
  <p>Award Amount: $1,750,500.50</p>
  <p>Award Date: 11/30/2025</p>
</div>
</body>
</html>
"""

NO_AMOUNT_HTML = """
<html>
<body>
<h1>Solicitation 24-999X</h1>
<dl>
  <dt>Solicitation ID:</dt><dd>24-999X</dd>
  <dt>Status:</dt><dd>Awarded</dd>
  <dt>NAICS Code:</dt><dd>236220</dd>
</dl>
<h2>Solicitation Awards</h2>
<dl>
  <dt>Awarded Vendor:</dt><dd>Confidential Negotiated LLC</dd>
  <dt>Award Date:</dt><dd>October 1, 2025</dd>
</dl>
</body>
</html>
"""

CANCELLED_HTML = """
<html>
<body>
<h1>Solicitation 24-CXLD</h1>
<dl>
  <dt>Solicitation ID:</dt><dd>24-CXLD</dd>
  <dt>Status:</dt><dd>Posting Cancelled</dd>
  <dt>Awarded Vendor:</dt><dd>Nobody Inc</dd>
  <dt>Award Amount:</dt><dd>$1,000,000.00</dd>
  <dt>Award Date:</dt><dd>October 1, 2025</dd>
</dl>
</body>
</html>
"""

POSTED_HTML = """
<html>
<body>
<h1>Solicitation 26-POST</h1>
<dl>
  <dt>Solicitation ID:</dt><dd>26-POST</dd>
  <dt>Status:</dt><dd>Posted</dd>
</dl>
</body>
</html>
"""

LISTING_HTML = """
<html>
<body>
<h1>ESBD Solicitations — Awarded</h1>
<ul class="solicitation-list">
  <li><a href="/esbd/26-007RFCSP">CSP 26-007RFCSP — Construction</a>
      <span>NAICS: 236220</span> <span>Status: Awarded</span></li>
  <li><a href="/esbd/25-100CSP">CSP 25-100CSP — Office Renovation</a>
      <span>NAICS: 236220</span> <span>Status: Awarded</span></li>
  <li><a href="/esbd/25-050X">RFP 25-050X — IT Services</a>
      <span>NAICS: 541512</span> <span>Status: Awarded</span></li>
  <li><a href="/esbd/24-200B">IFB 24-200B — Roads</a>
      <span>NAICS: 237310</span> <span>Status: Awarded</span></li>
  <li><a href="https://www.txsmartbuy.gov/esbd/24-300C">RFCSP 24-300C —
      Bridges</a>
      <span>NAICS: 237310</span> <span>Status: Awarded</span></li>
  <li><a href="/esbd/help">Help</a></li>
  <li><a href="/esbd/about">About</a></li>
</ul>
</body>
</html>
"""

# An ESBD page that uses the "Vendor:" / "Amount:" loose labels rather
# than the explicit "Awarded Vendor:" / "Award Amount:" forms — to
# exercise the multi-label fallback.
LOOSE_LABEL_HTML = """
<html>
<body>
<h1>Solicitation 26-LOOSE</h1>
<p>Status: Awarded</p>
<p>Vendor: Loose Labels LLC</p>
<p>Amount: $500,000.00</p>
<p>Award Date: 2025-12-15</p>
</body>
</html>
"""


SHORTSCALE_HTML = """
<html>
<body>
<h1>Solicitation 26-MEGA</h1>
<dl>
  <dt>Solicitation ID:</dt><dd>26-MEGA</dd>
  <dt>Status:</dt><dd>Awarded</dd>
  <dt>Awarded Vendor:</dt><dd>Mega Build Co</dd>
  <dt>Award Amount:</dt><dd>$1.5B</dd>
  <dt>Award Date:</dt><dd>January 5, 2026</dd>
</dl>
</body>
</html>
"""


# --- Helpers ----------------------------------------------------------


def _route_handler(routes: dict[str, tuple[int, str]]) -> Callable:
    """Build an ``httpx.MockTransport`` handler from a path→(status, body) map.

    ``routes`` maps URL path (including any query string) to a tuple of
    (HTTP status, response body). The handler matches the path-plus-
    query of the incoming request and returns the configured response,
    or 404 if no route matches.
    """
    def handler(request: httpx.Request) -> httpx.Response:
        # Match on the full URL string to keep the routing rules
        # explicit (path AND query string).
        url = str(request.url)
        for pattern, (status, body) in routes.items():
            if url == pattern or url.endswith(pattern):
                return httpx.Response(status, text=body)
        return httpx.Response(404, text="not found")
    return handler


def _build_mock_source(handler, tmp_path: Path) -> TXSmartBuyAwardsSource:
    client = build_client(transport=httpx.MockTransport(handler))
    return TXSmartBuyAwardsSource(client=client, cache_root=tmp_path)


# --- Tests ------------------------------------------------------------


def test_adapter_instantiates_without_error() -> None:
    src = TXSmartBuyAwardsSource()
    try:
        assert src.name == "tx_smartbuy_awards"
        assert src.homepage_url == ESBD_BASE_URL
        assert src.requires_env_vars == []
        assert "Texas" in src.license_str
        assert src.default_series() == []
    finally:
        src.close()


def test_single_solicitation_parses_into_one_snapshot(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-007RFCSP"): (200, SINGLE_VENDOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-007RFCSP")
    finally:
        src.close()

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "tx_smartbuy_awards"
    assert s.series_id == "26-007RFCSP"
    assert s.label == "ESBD 26-007RFCSP awarded to ABC Construction LLC"
    assert s.unit == "USD"
    assert s.value == pytest.approx(1_234_567.89)
    assert s.region == "TX"
    assert s.csi_division is None
    assert s.naics == "236220"
    assert s.period == "2025-12"
    assert s.source_url == detail_url("26-007RFCSP")
    assert "Texas" in s.license
    assert s.raw is not None
    assert s.raw["vendor"] == "ABC Construction LLC"
    assert s.raw["award_amount_usd"] == pytest.approx(1_234_567.89)
    assert s.raw["solicitation_number"] == "26-007RFCSP"
    assert s.raw["agency"] == "Angelo State University"
    assert s.raw["vendor_count"] == 1


def test_multi_vendor_award_splits_into_n_snapshots(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("25-100CSP"): (200, MULTI_VENDOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("25-100CSP")
    finally:
        src.close()

    assert len(snaps) == 3
    series_ids = [s.series_id for s in snaps]
    assert series_ids == ["25-100CSP--1", "25-100CSP--2", "25-100CSP--3"]
    vendors = [s.raw["vendor"] for s in snaps]
    assert vendors == [
        "First Builders Group LLC",
        "Second Construction Co",
        "Third Contractor Inc",
    ]
    amounts = [s.value for s in snaps]
    assert amounts == [
        pytest.approx(4_500_000.0),
        pytest.approx(3_200_000.0),
        pytest.approx(1_750_500.5),
    ]
    for s in snaps:
        assert s.period == "2025-11"
        assert s.naics == "236220"
        assert s.raw["vendor_count"] == 3


def test_missing_amount_returns_empty_no_crash(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("24-999X"): (200, NO_AMOUNT_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("24-999X")
    finally:
        src.close()
    assert snaps == []


def test_4xx_response_raises_pricing_source_unavailable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_award("26-MISSING")
    finally:
        src.close()


def test_5xx_response_raises_pricing_source_unavailable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    src = _build_mock_source(handler, tmp_path)
    try:
        with pytest.raises(PricingSourceUnavailable):
            src.fetch_award("26-BROKEN")
    finally:
        src.close()


def test_cache_hit_no_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=SINGLE_VENDOR_HTML)

    src = _build_mock_source(handler, tmp_path)
    try:
        src.fetch_award("26-007RFCSP")
        src.fetch_award("26-007RFCSP")
    finally:
        src.close()
    assert call_count["n"] == 1


def test_naics_extracted_from_detail_page(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-007RFCSP"): (200, SINGLE_VENDOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-007RFCSP")
    finally:
        src.close()
    assert snaps[0].naics == "236220"


@pytest.mark.parametrize(
    "date_str, expected",
    [
        ("December 15, 2025", "2025-12"),
        ("Dec 15, 2025", "2025-12"),
        ("12/15/2025", "2025-12"),
        ("2025-12-15", "2025-12"),
        ("December 2025", "2025-12"),
        ("January 5, 2026", "2026-01"),
        ("1/5/2026", "2026-01"),
        ("2026-01-05", "2026-01"),
    ],
)
def test_period_parses_various_date_formats(date_str: str, expected: str) -> None:
    assert parse_award_period(date_str) == expected


def test_period_returns_none_when_no_date(tmp_path: Path) -> None:
    assert parse_award_period("no date here") is None
    assert parse_award_period("") is None


def test_fetch_recent_awards_naics_filter_in_url(tmp_path: Path) -> None:
    captured_urls: list[str] = []
    detail_routes = {
        detail_url("26-007RFCSP"): SINGLE_VENDOR_HTML,
        detail_url("25-100CSP"): MULTI_VENDOR_HTML,
        detail_url("25-050X"): SINGLE_VENDOR_HTML,
        detail_url("24-200B"): SINGLE_VENDOR_HTML,
        detail_url("24-300C"): SINGLE_VENDOR_HTML,
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        captured_urls.append(url)
        if url == listing_url(status="Awarded", naics="236220"):
            return httpx.Response(200, text=LISTING_HTML)
        for det_url, body in detail_routes.items():
            if url == det_url:
                return httpx.Response(200, text=body)
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_recent_awards(limit=5, naics="236220")
    finally:
        src.close()

    listing_called = [u for u in captured_urls if "esbd?" in u]
    assert listing_called, f"expected listing URL to be hit: {captured_urls}"
    assert "naics=236220" in listing_called[0]
    # Listing yields 5 detail pages → SINGLE_VENDOR yields 1 snap each,
    # MULTI_VENDOR yields 3 snaps for 25-100CSP.
    assert len(snaps) == 4 + 3


def test_fetch_recent_awards_limit_honored(tmp_path: Path) -> None:
    detail_routes = {
        detail_url(sol): SINGLE_VENDOR_HTML
        for sol in ("26-007RFCSP", "25-100CSP", "25-050X", "24-200B", "24-300C")
    }

    def handler(request: httpx.Request) -> httpx.Response:
        url = str(request.url)
        if url == listing_url(status="Awarded"):
            return httpx.Response(200, text=LISTING_HTML)
        for det_url, body in detail_routes.items():
            if url == det_url:
                return httpx.Response(200, text=body)
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_recent_awards(limit=2)
    finally:
        src.close()
    # Only the first 2 listing solicitations are fetched; each is
    # SINGLE_VENDOR_HTML which yields 1 snapshot.
    assert len(snaps) == 2


def test_listing_parser_de_duplicates_and_skips_nav(tmp_path: Path) -> None:
    sol_numbers = parse_listing_for_solicitation_numbers(LISTING_HTML)
    assert sol_numbers[:5] == [
        "26-007RFCSP", "25-100CSP", "25-050X", "24-200B", "24-300C",
    ]
    # Navigation paths (no digit, e.g. /esbd/help) must NOT appear.
    assert "help" not in sol_numbers
    assert "about" not in sol_numbers


def test_cancelled_solicitation_skipped(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("24-CXLD"): (200, CANCELLED_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("24-CXLD")
    finally:
        src.close()
    assert snaps == []


def test_posted_solicitation_skipped(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-POST"): (200, POSTED_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-POST")
    finally:
        src.close()
    assert snaps == []


@pytest.mark.parametrize(
    "amount_str, expected",
    [
        ("$1,234,567.89", 1_234_567.89),
        ("$ 1,234,567", 1_234_567.0),
        ("$1.23M", 1_230_000.0),
        ("$1.5B", 1_500_000_000.0),
        ("$500K", 500_000.0),
        ("Total: $999,999.99", 999_999.99),
        # bare comma-grouped number — at least 2 comma groups required
        # to avoid matching counts like "1,200".
        ("Total 12,345,678", 12_345_678.0),
    ],
)
def test_dollar_parsing_variants(amount_str: str, expected: float) -> None:
    val = parse_dollar_amount(amount_str)
    assert val is not None
    assert val == pytest.approx(expected)


def test_dollar_parsing_rejects_implausible() -> None:
    # $100 is below the plausibility floor — return None instead of
    # accepting a clearly-wrong value.
    assert parse_dollar_amount("$100") is None
    # Bare 1,200 is only one comma group — must NOT parse as $1,200.
    assert parse_dollar_amount("1,200") is None


def test_shortscale_amount_parses_into_snapshot(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-MEGA"): (200, SHORTSCALE_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-MEGA")
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(1_500_000_000.0)
    assert snaps[0].period == "2026-01"


def test_real_shape_esbd_fixture_parses(tmp_path: Path) -> None:
    """Parse a small static fixture modelled on the live page shape."""
    fixture_html = (
        "<html><body>"
        "<h1>Texas SmartBuy — ESBD Solicitation Detail</h1>"
        "<table class='detail'>"
        "<tr><th>Solicitation ID:</th><td>26-007RFCSP</td></tr>"
        "<tr><th>Status:</th><td>Awarded</td></tr>"
        "<tr><th>Issuing Agency:</th><td>Angelo State University</td></tr>"
        "<tr><th>NAICS Code:</th><td>236220</td></tr>"
        "</table>"
        "<h2>Notice of Award</h2>"
        "<p>Awarded Vendor: Carr EFA Joint Venture</p>"
        "<p>Award Amount: $12,500,000.00</p>"
        "<p>Award Date: March 3, 2026</p>"
        "<p>Performance Period: 03/15/2026 - 03/14/2028</p>"
        "</body></html>"
    )
    snaps = parse_award_detail_page(
        fixture_html,
        solicitation_number="26-007RFCSP",
        source_url=detail_url("26-007RFCSP"),
        license_str="State of Texas public record — TX SmartBuy / ESBD",
        adapter_name="tx_smartbuy_awards",
    )
    assert len(snaps) == 1
    s = snaps[0]
    assert s.raw["vendor"] == "Carr EFA Joint Venture"
    assert s.value == pytest.approx(12_500_000.0)
    assert s.period == "2026-03"
    assert s.naics == "236220"
    assert s.raw["agency"] == "Angelo State University"


def test_snapshot_serialization_round_trip(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-007RFCSP"): (200, SINGLE_VENDOR_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-007RFCSP")
    finally:
        src.close()
    assert len(snaps) == 1
    blob = snaps[0].to_json()
    round_tripped = PricingSnapshot.from_json(blob)
    assert round_tripped.value == pytest.approx(1_234_567.89)
    assert round_tripped.series_id == "26-007RFCSP"
    assert round_tripped.source == "tx_smartbuy_awards"
    assert round_tripped.unit == "USD"
    assert round_tripped.region == "TX"


def test_loose_label_fallback(tmp_path: Path) -> None:
    handler = _route_handler({
        detail_url("26-LOOSE"): (200, LOOSE_LABEL_HTML),
    })
    src = _build_mock_source(handler, tmp_path)
    try:
        snaps = src.fetch_award("26-LOOSE")
    finally:
        src.close()
    assert len(snaps) == 1
    assert snaps[0].raw["vendor"] == "Loose Labels LLC"
    assert snaps[0].value == pytest.approx(500_000.0)
    assert snaps[0].period == "2025-12"


def test_fetch_swallows_4xx_for_refresh_runner(tmp_path: Path) -> None:
    """``fetch()`` (the abstract entry) must NEVER raise."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    try:
        # Listing-page fetch fails — but fetch() must return [] silently.
        snaps = src.fetch([])
        assert snaps == []
        # Per-solicitation fetch also fails — same expectation.
        snaps2 = src.fetch(["26-MISSING"])
        assert snaps2 == []
    finally:
        src.close()


def test_html_to_text_strips_tags_and_decodes_entities() -> None:
    raw = (
        "<html><body><p>Award Amount: <b>$1,000,000</b>&nbsp;USD</p>"
        "<script>alert('xss')</script></body></html>"
    )
    out = html_to_text(raw)
    assert "<b>" not in out
    assert "&nbsp;" not in out
    assert "alert" not in out  # script body excluded
    assert "$1,000,000" in out


def test_listing_url_query_params() -> None:
    assert listing_url() == f"{ESBD_BASE_URL}?status=Awarded"
    assert listing_url(naics="236220") == (
        f"{ESBD_BASE_URL}?status=Awarded&naics=236220"
    )


def test_detail_url_quotes_solicitation_safely() -> None:
    assert detail_url("26-007RFCSP") == f"{ESBD_BASE_URL}/26-007RFCSP"
    # Solicitation IDs are alphanumeric+dashes; spaces should be quoted.
    assert detail_url("26 007") == f"{ESBD_BASE_URL}/26%20007"
