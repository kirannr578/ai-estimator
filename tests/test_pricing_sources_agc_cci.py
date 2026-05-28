"""Unit tests for core/pricing/sources/agc_cci.py.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in ``tests/test_pricing_sources_bls_ppi.py``.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources._cci_common import PricingSourceUnavailable
from core.pricing.sources.agc_cci import (
    AGC_ANCHORS,
    AGC_CONSTRUCTION_DATA_URL,
    AGCCCISource,
)
from core.pricing.sources.base import build_client


# AGC's Construction Data landing page primarily exposes Data Digest +
# Construction Industry Outlook links + Producer Prices & Employment Costs
# tables. The headline figure tends to be the BLS PPI for inputs to
# nonresidential construction, framed in commentary text. Canned HTML below
# mirrors that shape — anchor phrase + index value + period.
CANNED_AGC_HTML = """
<html>
<head><title>Construction Data | Associated General Contractors of America</title></head>
<body>
<h1>Construction Data</h1>
<p>According to the AGC Construction Inflation Alert, the PPI for inputs to
new construction stood at 312.7 in April 2026, up 4.7% year-over-year.</p>
<h2>Producer Prices &amp; Employment Costs</h2>
<p>Tables showing changes in producer price indexes and employment cost
indexes for construction materials. Latest data through 2026-04 reflects
continued moderation in commodity inflation.</p>
</body>
</html>
"""


def _build_mock_source(handler, tmp_path: Path) -> AGCCCISource:
    client = build_client(transport=httpx.MockTransport(handler))
    src = AGCCCISource(client=client, cache_root=tmp_path)
    return src


def test_adapter_instantiates_without_error() -> None:
    src = AGCCCISource()
    try:
        assert src.name == "agc_cci"
        assert src.homepage_url == "https://www.agc.org/learn/construction-data"
        assert src.requires_env_vars == []
        assert "AGC" in src.license_str
    finally:
        src.close()


def test_default_series_returns_documented_series_id() -> None:
    src = AGCCCISource()
    try:
        assert src.default_series() == ["national"]
    finally:
        src.close()


def test_url_is_documented_public_source(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national"])
    assert captured["url"] == AGC_CONSTRUCTION_DATA_URL
    assert captured["method"] == "GET"


def test_fetch_parses_canned_html_into_expected_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national"])

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "agc_cci"
    assert s.series_id == "national"
    assert s.label == "AGC PPI-based Construction Cost Index"
    assert s.unit == "index"
    assert s.value == pytest.approx(312.7)
    assert s.region == "US"
    assert s.csi_division is None
    assert s.naics == "23"
    assert s.period == "2026-04"
    assert "AGC" in s.license
    assert s.source_url == AGC_CONSTRUCTION_DATA_URL
    assert s.raw is not None
    assert s.raw["index_value"] == pytest.approx(312.7)


def test_fetch_latest_returns_single_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.series_id == "national"
    assert snap.value == pytest.approx(312.7)


def test_fetch_latest_raises_when_page_unparseable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="<html><body>Maintenance window in progress.</body></html>",
        )

    src = _build_mock_source(handler, tmp_path)
    with pytest.raises(PricingSourceUnavailable):
        src.fetch_latest()


def test_fetch_returns_empty_on_unparseable_page_not_raising(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="<html><body>Maintenance window in progress.</body></html>",
        )

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_fetch_handles_4xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_fetch_handles_5xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(502, text="bad gateway")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_cache_avoids_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national"])
    src.fetch(["national"])
    assert call_count["n"] == 1


def test_unknown_series_id_is_skipped(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national", "regional"])
    assert len(snaps) == 1
    assert snaps[0].series_id == "national"


def test_period_parses_monthly_format(tmp_path: Path) -> None:
    """AGC PPI data is monthly — we expect YYYY-MM."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.period == "2026-04"


def test_fetch_history_returns_at_most_one(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_AGC_HTML)

    src = _build_mock_source(handler, tmp_path)
    assert len(src.fetch_history(periods=10)) == 1


def test_anchors_include_documented_phrases() -> None:
    """Regression: must include the canonical PPI / CCI anchors."""
    assert any("Producer Price" in a for a in AGC_ANCHORS)
    assert any(a == "CCI" for a in AGC_ANCHORS)
