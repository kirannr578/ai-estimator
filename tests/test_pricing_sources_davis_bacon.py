"""Unit tests for core/pricing/sources/davis_bacon.py."""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.davis_bacon import (
    DOL_TO_SOC,
    DavisBaconSource,
    map_classification_to_soc,
)


def _build_mock_source(handler) -> DavisBaconSource:
    return DavisBaconSource(client=build_client(transport=httpx.MockTransport(handler)))


CANNED_RESPONSE: dict = {
    "results": [
        {
            "wageDeterminationNumber": "TX20260270",
            "modificationDate": "2026-01-02",
            "pdfUrl": "https://sam.gov/wd/TX20260270.pdf",
            "classifications": [
                {"classification": "CARPENTER", "baseWageRate": 28.41},
                {"classification": "ELECTRICIAN", "baseWageRate": 35.10},
                {"classification": "LABORER (Common)", "baseWageRate": 19.27},
                {"classification": "DRYWALL HANGER", "baseWageRate": 24.66},
                {"classification": "TILE SETTER", "baseWageRate": 22.10},  # unmapped SOC
                {"classification": "PLUMBER", "baseWageRate": 33.21},
                {"classification": "UNCLOSED", "baseWageRate": ""},  # blank -> skipped
            ],
        },
    ],
}


def test_fetch_for_project_parses_classifications(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url).split("?")[0]
        captured["params"] = dict(request.url.params)
        return httpx.Response(200, json=CANNED_RESPONSE)

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    # Redirect snapshot writes via monkeypatching write_text_record? Simpler:
    # let it write to the real path under tmp_path by patching SNAPSHOTS_ROOT.
    import core.pricing.snapshots as snap_mod
    orig_root = snap_mod.SNAPSHOTS_ROOT
    snap_mod.SNAPSHOTS_ROOT = tmp_path
    try:
        snaps = src.fetch_for_project(
            state="TX", county="Tom Green", project_type="Building",
        )
    finally:
        snap_mod.SNAPSHOTS_ROOT = orig_root

    assert captured["params"]["state"] == "TX"
    assert captured["params"]["constructionType"] == "Building"
    assert captured["params"]["county"] == "Tom Green"

    # 6 valid rates (the blank "UNCLOSED" should be skipped)
    assert len(snaps) == 6

    by_soc = {s.soc_code: s for s in snaps if s.soc_code}
    assert by_soc["47-2031"].value == pytest.approx(28.41)
    assert by_soc["47-2111"].value == pytest.approx(35.10)
    assert by_soc["47-2061"].value == pytest.approx(19.27)
    assert by_soc["47-2081"].value == pytest.approx(24.66)
    assert by_soc["47-2152"].value == pytest.approx(33.21)

    # Tile setter survives but with soc_code=None.
    tile = next(s for s in snaps if "TILE" in s.label)
    assert tile.soc_code is None
    assert tile.unit == "USD/hr"
    assert tile.region == "TX-Tom Green"
    assert tile.csi_division == "01"
    assert "TX20260270" in tile.series_id

    # Aux WD pointer file landed on disk.
    aux = tmp_path / "davis_bacon" / "TX_Tom_Green" / "TX20260270.json"
    assert aux.exists()
    contents = aux.read_text(encoding="utf-8")
    assert "TX20260270" in contents
    assert "sam.gov" in contents


def test_state_required_returns_empty(tmp_path: Path) -> None:
    src = DavisBaconSource()
    src._cache_root = tmp_path
    src._client = build_client(transport=httpx.MockTransport(
        lambda r: httpx.Response(500)
    ))
    assert src.fetch_for_project(state=None, county=None) == []


def test_http_error_returns_empty_not_crash(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="upstream down")

    src = _build_mock_source(handler)
    src._cache_root = tmp_path
    assert src.fetch_for_project(state="TX", county="Tom Green") == []


def test_classification_mapping_unknown_returns_none() -> None:
    assert map_classification_to_soc("PILE DRIVER") is None
    assert map_classification_to_soc("") is None
    assert map_classification_to_soc("CARPENTER") == DOL_TO_SOC["CARPENTER"]
    # Partial-match: "JOURNEYMAN ELECTRICIAN" still matches ELECTRICIAN.
    assert map_classification_to_soc("JOURNEYMAN ELECTRICIAN") == "47-2111"
