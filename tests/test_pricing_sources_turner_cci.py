"""Unit tests for core/pricing/sources/turner_cci.py.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in ``tests/test_pricing_sources_bls_ppi.py``.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources._cci_common import PricingSourceUnavailable
from core.pricing.sources.base import build_client
from core.pricing.sources.turner_cci import (
    TURNER_ANCHORS,
    TURNER_COST_INDEX_URL,
    TurnerCCISource,
)


# Turner publishes a quarterly TBCI in a single per-quarter article body.
# Canned HTML below mirrors the shape verified on
# https://www.turnerconstruction.com/cost-index — heading per quarter +
# headline number + textual commentary.
CANNED_TURNER_HTML = """
<html>
<head><title>Cost Index | Turner Construction Company</title></head>
<body>
<h1>Cost Index</h1>
<p>The TBCI is determined by labor rates and productivity, material prices,
and the competitive condition of the marketplace.</p>
<h2>1ST QUARTER 2026</h2>
<p>The Turner Building Cost Index increased to 1532 in the first quarter
of 2026, representing a 1.2% increase from the fourth quarter of 2025.</p>
<h2>4TH QUARTER 2025</h2>
<p>The Turner Building Cost Index increased to 1514 in the fourth quarter
of 2025.</p>
<h2>3RD QUARTER 2025</h2>
<p>Earlier quarterly values are listed back to 2006 in the archive.</p>
</body>
</html>
"""


def _build_mock_source(handler, tmp_path: Path) -> TurnerCCISource:
    client = build_client(transport=httpx.MockTransport(handler))
    src = TurnerCCISource(client=client, cache_root=tmp_path)
    return src


def test_adapter_instantiates_without_error() -> None:
    src = TurnerCCISource()
    try:
        assert src.name == "turner_cci"
        assert src.homepage_url == "https://www.turnerconstruction.com/cost-index"
        assert src.requires_env_vars == []
        assert "Turner" in src.license_str
    finally:
        src.close()


def test_default_series_returns_documented_series_id() -> None:
    src = TurnerCCISource()
    try:
        assert src.default_series() == ["national"]
    finally:
        src.close()


def test_url_is_documented_public_source(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national"])
    assert captured["url"] == TURNER_COST_INDEX_URL
    assert captured["method"] == "GET"


def test_fetch_parses_canned_html_into_expected_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national"])

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "turner_cci"
    assert s.series_id == "national"
    assert s.label == "Turner Building Cost Index"
    assert s.unit == "index"
    # The first TBCI value encountered after the anchor wins — 1532 (Q1 2026).
    assert s.value == pytest.approx(1532.0)
    assert s.region == "US"
    assert s.csi_division is None
    assert s.naics == "23"
    # Turner is quarterly; ``prefer_quarterly=True`` in the adapter must
    # produce a YYYY-QN period, not YYYY-MM.
    assert s.period == "2026-Q1"
    assert "Turner" in s.license
    assert s.source_url == TURNER_COST_INDEX_URL
    assert s.raw is not None
    assert s.raw["index_value"] == pytest.approx(1532.0)


def test_fetch_latest_returns_single_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.series_id == "national"
    assert snap.value == pytest.approx(1532.0)


def test_fetch_latest_raises_when_page_unparseable(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>No data yet.</body></html>")

    src = _build_mock_source(handler, tmp_path)
    with pytest.raises(PricingSourceUnavailable):
        src.fetch_latest()


def test_fetch_returns_empty_on_unparseable_page_not_raising(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="<html><body>No data yet.</body></html>")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_fetch_handles_4xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_fetch_handles_5xx_gracefully(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="internal error")

    src = _build_mock_source(handler, tmp_path)
    assert src.fetch(["national"]) == []


def test_cache_avoids_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["national"])
    src.fetch(["national"])
    assert call_count["n"] == 1


def test_unknown_series_id_is_skipped(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["national", "european"])
    assert len(snaps) == 1
    assert snaps[0].series_id == "national"


def test_period_parses_quarterly_format(tmp_path: Path) -> None:
    """Turner is quarterly — period must be YYYY-QN."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.period.startswith("2026-Q")
    assert "-" in snap.period


def test_fetch_history_returns_at_most_one(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_TURNER_HTML)

    src = _build_mock_source(handler, tmp_path)
    assert len(src.fetch_history(periods=10)) == 1


def test_anchors_include_documented_phrases() -> None:
    """Regression: TBCI long form must be present and tried first."""
    assert TURNER_ANCHORS[0] == "Turner Building Cost Index"
    assert "TBCI" in TURNER_ANCHORS


def test_alternate_period_phrasing(tmp_path: Path) -> None:
    """Verify that 'First Quarter 2026' phrasing also parses."""
    html = (
        "<html><body>"
        "<p>The Turner Building Cost Index reached 1488 in the First "
        "Quarter, 2026.</p>"
        "</body></html>"
    )

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=html)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.value == pytest.approx(1488.0)
    assert snap.period == "2026-Q1"
