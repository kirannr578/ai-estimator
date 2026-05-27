"""Unit tests for core/pricing/sources/bls_oews.py."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.bls_oews import (
    BLS_API_URL,
    BLSOEWSSource,
    _build_series_id,
    all_default_series,
    parse_series_id,
)


def _build_mock_source(handler) -> BLSOEWSSource:
    return BLSOEWSSource(client=build_client(transport=httpx.MockTransport(handler)))


def test_default_series_covers_10_socs_x_6_metros() -> None:
    series = all_default_series()
    assert len(series) == 60  # 6 metros x 10 trades
    # All should parse round-trip.
    for sid in series:
        parsed = parse_series_id(sid)
        assert parsed["soc_code"].count("-") == 1


def test_build_and_parse_series_id_roundtrip() -> None:
    sid = _build_series_id("0019124", "47-2031")
    assert sid == "OEUM0019124000000472031" "04"
    parsed = parse_series_id(sid)
    assert parsed["area_code"] == "0019124"
    assert parsed["occupation_code"] == "472031"
    assert parsed["soc_code"] == "47-2031"
    assert parsed["datatype"] == "04"


def test_fetch_parses_response(tmp_path: Path) -> None:
    series_id = _build_series_id("0019124", "47-2031")
    canned = {
        "status": "REQUEST_SUCCEEDED",
        "Results": {
            "series": [
                {
                    "seriesID": series_id,
                    "data": [
                        {"year": "2024", "period": "A01", "value": "32.41"},
                    ],
                }
            ]
        },
    }

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content.decode("utf-8"))
        return httpx.Response(200, json=canned)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    snaps = src.fetch([series_id])

    assert captured["url"] == BLS_API_URL
    assert captured["body"]["seriesid"] == [series_id]

    assert len(snaps) == 1
    snap = snaps[0]
    assert snap.unit == "USD/hr"
    assert snap.region == "0019124"
    assert snap.soc_code == "47-2031"
    assert snap.csi_division == "01"
    assert snap.value == pytest.approx(32.41)
    assert "Carpenters" in snap.label
    assert "Dallas" in snap.label


def test_batches_50_at_a_time(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, json={"status": "REQUEST_SUCCEEDED", "Results": {"series": []}})

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    # 60 series should go in 2 calls (50 + 10).
    src.fetch(all_default_series())
    assert call_count["n"] == 2


def test_failed_batch_does_not_break_others(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content.decode("utf-8"))
        # Fail the big batch, succeed on the smaller one.
        if len(body["seriesid"]) > 10:
            return httpx.Response(200, json={
                "status": "REQUEST_NOT_PROCESSED", "message": ["too many"]
            })
        canned = {
            "status": "REQUEST_SUCCEEDED",
            "Results": {"series": [{
                "seriesID": body["seriesid"][0],
                "data": [{"year": "2024", "period": "A01", "value": "30.00"}],
            }]},
        }
        return httpx.Response(200, json=canned)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    # 51 series triggers a 50-batch (fails) + a 1-batch (succeeds with 1 row).
    series = all_default_series()[:51]
    snaps = src.fetch(series)
    assert len(snaps) == 1
    assert snaps[0].value == pytest.approx(30.00)
