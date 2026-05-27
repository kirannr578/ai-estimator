"""Unit tests for core/pricing/snapshots.py."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from core.pricing.snapshots import (
    PricingSnapshot,
    list_series,
    list_sources,
    load_history,
    load_latest,
    write_snapshot,
    write_snapshots,
    write_text_record,
)


def _make_snapshot(*, period: str = "2026-04", value: float = 100.0,
                   source: str = "bls_ppi", series_id: str = "WPU0811") -> PricingSnapshot:
    return PricingSnapshot(
        source=source,
        series_id=series_id,
        label="Softwood lumber",
        unit="index",
        value=value,
        region=None,
        csi_division="06",
        period=period,
        fetched_at=datetime(2026, 5, 27, 18, 0, tzinfo=timezone.utc),
        license="U.S. Public Domain — BLS",
        source_url="https://data.bls.gov/timeseries/WPU0811",
        raw={"observation": {"year": 2026, "period": "M04", "value": "100.0"}},
    )


def test_roundtrip_serialize_and_load(tmp_path: Path) -> None:
    snap = _make_snapshot()
    write_snapshot(snap, root=tmp_path)

    loaded = load_latest("bls_ppi", "WPU0811", root=tmp_path)
    assert loaded is not None
    assert loaded.source == "bls_ppi"
    assert loaded.series_id == "WPU0811"
    assert loaded.value == pytest.approx(100.0)
    assert loaded.period == "2026-04"
    assert loaded.label == "Softwood lumber"
    assert loaded.raw == snap.raw


def test_latest_picks_newest_fetched_at(tmp_path: Path) -> None:
    older = _make_snapshot(period="2026-03", value=90.0)
    older = older.model_copy(update={"fetched_at": datetime(2026, 4, 1, tzinfo=timezone.utc)})
    newer = _make_snapshot(period="2026-04", value=110.0)
    newer = newer.model_copy(update={"fetched_at": datetime(2026, 5, 1, tzinfo=timezone.utc)})

    write_snapshots([older, newer], root=tmp_path)

    latest = load_latest("bls_ppi", "WPU0811", root=tmp_path)
    assert latest is not None
    assert latest.value == pytest.approx(110.0)
    assert latest.period == "2026-04"


def test_load_history_returns_sorted_excluding_latest_mirror(tmp_path: Path) -> None:
    a = _make_snapshot(period="2026-01", value=80.0).model_copy(
        update={"fetched_at": datetime(2026, 2, 1, tzinfo=timezone.utc)})
    b = _make_snapshot(period="2026-02", value=85.0).model_copy(
        update={"fetched_at": datetime(2026, 3, 1, tzinfo=timezone.utc)})
    c = _make_snapshot(period="2026-03", value=90.0).model_copy(
        update={"fetched_at": datetime(2026, 4, 1, tzinfo=timezone.utc)})
    write_snapshots([a, b, c], root=tmp_path)

    history = load_history("bls_ppi", "WPU0811", root=tmp_path)
    assert [s.period for s in history] == ["2026-01", "2026-02", "2026-03"]
    assert all(s.fetched_at is not None for s in history)


def test_load_latest_returns_none_when_missing(tmp_path: Path) -> None:
    assert load_latest("bls_ppi", "DOESNOTEXIST", root=tmp_path) is None
    assert load_history("bls_ppi", "DOESNOTEXIST", root=tmp_path) == []


def test_corrupt_snapshot_is_skipped(tmp_path: Path) -> None:
    snap = _make_snapshot()
    write_snapshot(snap, root=tmp_path)
    # plant a malformed file alongside
    series_dir = tmp_path / "bls_ppi" / "WPU0811"
    (series_dir / "2026-05.json").write_text("{not json", encoding="utf-8")

    history = load_history("bls_ppi", "WPU0811", root=tmp_path)
    assert len(history) == 1
    assert history[0].period == "2026-04"


def test_list_sources_and_series(tmp_path: Path) -> None:
    write_snapshot(_make_snapshot(), root=tmp_path)
    write_snapshot(_make_snapshot(series_id="WPU0812"), root=tmp_path)
    write_snapshot(_make_snapshot(source="fred", series_id="DCOILWTICO"), root=tmp_path)
    # underscored dir (_http_cache) is excluded
    (tmp_path / "_http_cache").mkdir()
    (tmp_path / "_http_cache" / "x.json").write_text("{}", encoding="utf-8")

    assert list_sources(root=tmp_path) == ["bls_ppi", "fred"]
    assert list_series("bls_ppi", root=tmp_path) == ["WPU0811", "WPU0812"]
    assert list_series("fred", root=tmp_path) == ["DCOILWTICO"]


def test_safe_path_sanitizes_traversal(tmp_path: Path) -> None:
    bad = PricingSnapshot(
        source="bls_ppi",
        series_id="../../../etc/passwd",
        label="bad",
        unit="index",
        value=1.0,
        period="2026-04",
        license="x",
        source_url="x",
    )
    written_path = write_snapshot(bad, root=tmp_path)
    # The security property: the written path stays underneath the requested
    # root — no traversal could escape the snapshots tree.
    written_path.resolve().relative_to(tmp_path.resolve())
    # The malicious series id components were sanitized.
    rel_parts = written_path.relative_to(tmp_path).parts
    assert ".." not in rel_parts
    assert "etc" not in rel_parts  # `/` chars in series_id got replaced
    assert any("etc_passwd" in p for p in rel_parts)


def test_write_text_record_creates_aux_file(tmp_path: Path) -> None:
    path = write_text_record(
        source="davis_bacon",
        series_id="TX_TomGreen",
        period="TX20260270",
        payload={"wd_number": "TX20260270", "pdf_url": "https://example.gov/wd.pdf"},
        root=tmp_path,
    )
    assert path.exists()
    contents = path.read_text(encoding="utf-8")
    assert "TX20260270" in contents
    assert "example.gov" in contents
