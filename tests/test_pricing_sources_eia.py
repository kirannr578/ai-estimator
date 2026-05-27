"""Unit tests for core/pricing/sources/eia.py."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.eia import EIA_GND_URL, EIAFuelSource


def _build_mock_source(handler) -> EIAFuelSource:
    return EIAFuelSource(client=build_client(transport=httpx.MockTransport(handler)))


def test_skip_when_api_key_missing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("EIA_API_KEY", raising=False)
    called = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        called["n"] += 1
        return httpx.Response(500)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    assert src.fetch(["EMD_EPD2D_PTE_R30_DPG"]) == []
    assert called["n"] == 0


def test_request_shape_and_parsing(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.setenv("EIA_API_KEY", "eia-key")

    canned = {
        "response": {
            "data": [
                {"period": "2026-05-19", "value": 3.821,
                 "series": "EMD_EPD2D_PTE_R30_DPG",
                 "duoarea": "R30", "product": "EPD2D",
                 "process": "PTE"},
                {"period": "2026-05-12", "value": 3.799,
                 "series": "EMD_EPD2D_PTE_R30_DPG",
                 "duoarea": "R30", "product": "EPD2D",
                 "process": "PTE"},
            ]
        }
    }

    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url).split("?")[0]
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=canned)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    snaps = src.fetch(["EMD_EPD2D_PTE_R30_DPG"])

    assert captured["url"] == EIA_GND_URL
    assert captured["params"]["api_key"] == "eia-key"
    assert captured["params"]["frequency"] == "weekly"
    assert captured["params"]["facets[series][]"] == "EMD_EPD2D_PTE_R30_DPG"

    assert len(snaps) == 2
    snap = sorted(snaps, key=lambda s: s.period)[-1]
    assert snap.unit == "USD/gallon"
    assert snap.region == "PADD3"
    assert snap.value == pytest.approx(3.821)
    assert snap.csi_division == "01"
    assert "diesel" in snap.label.lower()


def test_default_series_includes_diesel_and_gasoline() -> None:
    src = EIAFuelSource()
    src.close()
    series = src.default_series()
    assert "EMD_EPD2D_PTE_R30_DPG" in series  # diesel
    assert "EMM_EPMR_PTE_R30_DPG" in series   # gas
