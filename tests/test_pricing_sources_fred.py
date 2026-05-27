"""Unit tests for core/pricing/sources/fred.py."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.fred import FRED_OBS_URL, FREDSource


def _build_mock_source(handler) -> FREDSource:
    return FREDSource(client=build_client(transport=httpx.MockTransport(handler)))


def test_skip_when_api_key_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("FRED_API_KEY", raising=False)
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(500)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    assert src.fetch(["DCOILWTICO"]) == []
    assert called["n"] == 0


def test_request_shape_and_parsing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("FRED_API_KEY", "fake-key-9999")

    canned = {
        "realtime_start": "2026-05-27",
        "observations": [
            {"date": "2026-04-01", "value": "85.42"},
            {"date": "2026-03-01", "value": "82.10"},
            {"date": "2026-02-01", "value": "."},  # FRED "missing" sentinel
            {"date": "2026-01-01", "value": ""},   # blank
        ],
    }

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url).split("?")[0]
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=canned)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    snaps = src.fetch(["DCOILWTICO"])

    assert captured["url"] == FRED_OBS_URL
    assert captured["params"]["series_id"] == "DCOILWTICO"
    assert captured["params"]["api_key"] == "fake-key-9999"
    assert captured["params"]["file_type"] == "json"

    # 4 observations, 2 valid.
    assert len(snaps) == 2
    snaps_sorted = sorted(snaps, key=lambda s: s.period)
    assert snaps_sorted[0].period == "2026-03-01"
    assert snaps_sorted[0].value == pytest.approx(82.10)
    assert snaps_sorted[1].period == "2026-04-01"
    assert snaps_sorted[1].value == pytest.approx(85.42)
    assert snaps_sorted[0].unit == "USD/barrel"
    assert snaps_sorted[0].csi_division == "01"

    # Critically: the api_key must NOT be inside the raw payload we persist.
    assert "api_key" not in (snaps_sorted[0].raw or {})


def test_default_series_count() -> None:
    src = FREDSource()
    src.close()
    assert len(src.default_series()) == 8


def test_http_error_for_one_series_does_not_break_others(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    monkeypatch.setenv("FRED_API_KEY", "k")

    def handler(request: httpx.Request) -> httpx.Response:
        if "DCOILWTICO" in str(request.url):
            return httpx.Response(500, text="boom")
        return httpx.Response(200, json={"observations": [
            {"date": "2026-04-01", "value": "303.0"}
        ]})

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    snaps = src.fetch(["DCOILWTICO", "WPUSI012011"])
    assert len(snaps) == 1
    assert snaps[0].series_id == "WPUSI012011"
