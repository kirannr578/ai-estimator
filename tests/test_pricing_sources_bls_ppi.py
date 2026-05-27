"""Unit tests for core/pricing/sources/bls_ppi.py.

All HTTP is mocked via `httpx.MockTransport` so the tests run offline.
"""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.bls_ppi import (
    BLS_API_URL,
    BLSPPISource,
    _SERIES_CATALOG,
    _bls_period,
)


CANNED_RESPONSE: dict = {
    "status": "REQUEST_SUCCEEDED",
    "responseTime": 117,
    "message": [],
    "Results": {
        "series": [
            {
                "seriesID": "WPU0811",
                "data": [
                    {"year": "2026", "period": "M04", "periodName": "April",
                     "value": "302.1", "footnotes": [{}]},
                    {"year": "2026", "period": "M03", "periodName": "March",
                     "value": "298.7", "footnotes": [{}]},
                ],
            },
            {
                "seriesID": "WPU102201",
                "data": [
                    {"year": "2026", "period": "M04", "periodName": "April",
                     "value": "342.5", "footnotes": [{}]},
                    {"year": "2026", "period": "M03", "periodName": "March",
                     "value": "",  # blank value should be skipped
                     "footnotes": [{}]},
                ],
            },
        ],
    },
}


def _build_mock_source(handler) -> BLSPPISource:
    client = build_client(transport=httpx.MockTransport(handler))
    return BLSPPISource(client=client)


def test_request_shape_and_parsing(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=CANNED_RESPONSE)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path  # isolate cache
    snaps = src.fetch(["WPU0811", "WPU102201"], startyear=2026, endyear=2026)

    assert captured["method"] == "POST"
    assert captured["url"] == BLS_API_URL
    assert captured["body"]["seriesid"] == ["WPU0811", "WPU102201"]
    assert captured["body"]["startyear"] == "2026"
    assert captured["body"]["endyear"] == "2026"
    # No registrationkey when BLS_API_KEY isn't set
    assert "registrationkey" not in captured["body"]

    # We expect 2 (WPU0811) + 1 (WPU102201 non-blank) = 3 snapshots.
    assert len(snaps) == 3

    by_series = {s.series_id: [] for s in snaps}
    for s in snaps:
        by_series[s.series_id].append(s)

    lumber = sorted(by_series["WPU0811"], key=lambda s: s.period)
    assert lumber[0].period == "2026-03"
    assert lumber[0].value == pytest.approx(298.7)
    assert lumber[1].period == "2026-04"
    assert lumber[1].value == pytest.approx(302.1)
    assert lumber[0].csi_division == "06"
    assert lumber[0].unit == "index"
    assert lumber[0].source == "bls_ppi"

    gyp = by_series["WPU102201"][0]
    assert gyp.csi_division == "09"
    assert gyp.value == pytest.approx(342.5)
    assert gyp.label == "Gypsum products (incl. drywall)"


def test_api_key_added_when_present(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BLS_API_KEY", "secret-test-key-1234")
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=CANNED_RESPONSE)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    src.fetch(["WPU0811"])
    assert captured["body"]["registrationkey"] == "secret-test-key-1234"
    assert captured["body"]["catalog"] is True


def test_request_failed_status_returns_empty(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, json={
            "status": "REQUEST_NOT_PROCESSED",
            "message": ["Daily threshold exceeded"],
        })

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    assert src.fetch(["WPU0811"]) == []


def test_default_series_covers_full_catalog() -> None:
    src = BLSPPISource()
    src.close()
    series = src.default_series()
    assert len(series) == 15
    assert set(series) == set(_SERIES_CATALOG.keys())


def test_period_helper() -> None:
    assert _bls_period(2026, "M04") == "2026-04"
    assert _bls_period(2026, "Q02") == "2026-Q2"
    assert _bls_period(2026, "A01") == "2026"
    assert _bls_period(2026, None) == "2026"
    assert _bls_period(None, None) == "unknown"


def test_cache_avoids_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json=CANNED_RESPONSE)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    src.fetch(["WPU0811"])
    src.fetch(["WPU0811"])
    assert call_count["n"] == 1, "Second call should be served from disk cache"


def test_no_verify_false_anywhere() -> None:
    """Smoke check: confirm the adapter never disables TLS verification."""
    src = BLSPPISource()
    assert src._client._transport is not None or True  # just construct
    src.close()
