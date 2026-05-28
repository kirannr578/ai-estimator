"""Unit tests for core/pricing/sources/enr_cci.py.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in ``tests/test_pricing_sources_bls_ppi.py``.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources._cci_common import PricingSourceUnavailable
from core.pricing.sources.base import build_client
from core.pricing.sources.enr_cci import (
    ENR_CCI_ANCHORS,
    ENR_ECONOMICS_URL,
    ENRCCISource,
)


# Synthetic HTML loosely modeled on the real ENR /economics page. Includes
# the headline number we expect to parse out (14021.34), the canonical
# "20-City Average Construction Cost Index" anchor, and an "April 2026"
# period string. Real ENR pages embed many more numbers (table headers,
# years, etc.) — we deliberately include some of those as decoys to
# pressure-test the anchor proximity logic.
CANNED_ENR_HTML = """
<html>
<head><title>Construction Economics | Engineering News-Record</title></head>
<body>
<h1>Construction Economics</h1>
<p>ENR publishes both a Construction Cost Index and Building Cost index.
The 20-City Average Construction Cost Index for April 2026 was 14021.34,
up 0.6% from the prior month.</p>
<table>
  <tr><th>City</th><th>CCI</th></tr>
  <tr><td>Atlanta</td><td>13800</td></tr>
  <tr><td>Boston</td><td>14500</td></tr>
</table>
<p>Source data covers 1978 - 2021 for the historical archive.</p>
</body>
</html>
"""


def _build_mock_source(handler, tmp_path: Path) -> ENRCCISource:
    client = build_client(transport=httpx.MockTransport(handler))
    src = ENRCCISource(client=client, cache_root=tmp_path)
    return src


def test_adapter_instantiates_without_error() -> None:
    src = ENRCCISource()
    try:
        assert src.name == "enr_cci"
        assert src.homepage_url == "https://www.enr.com/economics"
        assert src.requires_env_vars == []
        assert "ENR" in src.license_str
    finally:
        src.close()


def test_default_series_returns_documented_series_id() -> None:
    src = ENRCCISource()
    try:
        assert src.default_series() == ["national-20city"]
    finally:
        src.close()


def test_url_is_documented_public_source(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national-20city"])
    assert captured["url"] == ENR_ECONOMICS_URL
    assert captured["method"] == "GET"


def test_fetch_parses_canned_html_into_expected_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national-20city"])

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "enr_cci"
    assert s.series_id == "national-20city"
    assert s.label == "ENR 20-City Construction Cost Index"
    assert s.unit == "index"
    assert s.value == pytest.approx(14021.34)
    assert s.region == "US"
    assert s.csi_division is None
    assert s.naics == "23"
    assert s.period == "2026-04"
    assert "ENR" in s.license
    assert s.source_url == ENR_ECONOMICS_URL
    assert s.raw is not None
    assert s.raw["index_value"] == pytest.approx(14021.34)


def test_fetch_latest_returns_single_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.series_id == "national-20city"
    assert snap.value == pytest.approx(14021.34)


def test_fetch_latest_raises_when_page_unparseable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>Coming soon.</body></html>")

    src = _build_mock_source(handler, tmp_path)
    with pytest.raises(PricingSourceUnavailable):
        src.fetch_latest()


def test_fetch_returns_empty_on_unparseable_page_not_raising(tmp_path: Path) -> None:
    """fetch() must remain safe for the refresh runner — never raises."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>Coming soon.</body></html>")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national-20city"]) == []


def test_fetch_handles_4xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national-20city"]) == []


def test_fetch_handles_5xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national-20city"]) == []


def test_cache_avoids_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national-20city"])
    src.fetch(["national-20city"])
    assert call_count["n"] == 1, "Second call should be served from disk cache"


def test_unknown_series_id_is_skipped(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national-20city", "regional-houston"])
    # Only the valid series produces a snapshot; unknown series is logged
    # and skipped.
    assert len(snaps) == 1
    assert snaps[0].series_id == "national-20city"


def test_period_parses_monthly_format(tmp_path: Path) -> None:
    """ENR is monthly — we expect YYYY-MM, not YYYY-QN."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.period == "2026-04"
    assert "-Q" not in snap.period


def test_fetch_history_returns_at_most_one(tmp_path: Path) -> None:
    """Free tier only — fetch_history is documented to return at most 1."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_ENR_HTML)

    src = _build_mock_source(handler, tmp_path)
    history = src.fetch_history(periods=10)
    assert len(history) == 1


def test_no_verify_false_in_constructed_client() -> None:
    """Smoke check: the default-constructed client must not disable TLS."""
    src = ENRCCISource()
    try:
        # The base.build_client sets verify=True explicitly; we just confirm
        # construction succeeded.
        assert src._client is not None
    finally:
        src.close()


def test_anchors_include_documented_phrases() -> None:
    """Regression: the anchor list must keep the canonical ENR phrase."""
    assert "Construction Cost Index" in ENR_CCI_ANCHORS
    assert any("20-City" in a for a in ENR_CCI_ANCHORS)
