"""Unit tests for core/pricing/sources/nahb_construction_cost.py.

All HTTP is mocked via ``httpx.MockTransport`` so the tests run offline,
mirroring the established pattern in ``tests/test_pricing_sources_*.py``.
"""

from __future__ import annotations

from pathlib import Path

import httpx
import pytest

from core.pricing.sources.base import build_client
from core.pricing.sources.construction_indexes import (
    NAHBCostOfConstructingAHomeSource as RexportedNAHBSource,
)
from core.pricing.sources.nahb_construction_cost import (
    NAHB_ANCHORS,
    NAHB_HISTORICAL_TOTAL_COST,
    NAHB_HOMEPAGE_URL,
    NAHB_LATEST_ARTICLE_URL,
    NAHBCostOfConstructingAHomeSource,
    _find_headline_dollar_value,
    _find_study_year,
)


# Canned HTML approximating the structure of the live NAHB
# Cost-of-Constructing 2024 article body — lead paragraph + Table 1 row B
# + Table 3 historical column headers. The dollar amounts, year tokens,
# and anchor phrasing all mirror the live page verified 2026-05-28.
CANNED_NAHB_HTML = """
<html>
<head><title>Cost of Constructing a Home-2024 | NAHB</title></head>
<body>
<h1>Cost of Constructing a Home — 2024</h1>
<p>Over the years, NAHB has periodically conducted construction cost
surveys to collect information from builders on the various components
that go into the sales price of a typical newly-built single-family
home. NAHB's most recent Construction Cost survey (conducted in the
Fall of 2024) shows that, on average, 64.4% of the sales price is due
to construction costs and 13.7% to finished lot costs.</p>

<h2>Table 1. Sale Price Breakdown</h2>
<table>
<tr><td>A. Finished Lot Cost (including financing cost)</td><td>$91,057</td><td>13.7%</td></tr>
<tr><td>B. Total Construction Cost</td><td>$428,215</td><td>64.4%</td></tr>
<tr><td>C. Financing Cost</td><td>$10,220</td><td>1.5%</td></tr>
<tr><td>G. Profit</td><td>$72,971</td><td>11.0%</td></tr>
<tr><td>Total Sales Price</td><td>$665,298</td><td>100.0%</td></tr>
</table>

<p>The average construction cost of a typical single-family home in
the 2024 survey is $428,215 (Table 3), or about $162 per square foot —
the highest in the history of this series.</p>

<h2>Table 3. Single-Family Construction Cost Breakdown History</h2>
<table>
<tr><th>Year</th><th>1998</th><th>2011</th><th>2022</th><th>2024</th></tr>
<tr><td>TOTAL</td><td>$124,276</td><td>$184,125</td><td>$392,241</td><td>$428,215</td></tr>
</table>
</body>
</html>
"""


def _build_mock_source(handler, tmp_path: Path) -> NAHBCostOfConstructingAHomeSource:
    client = build_client(transport=httpx.MockTransport(handler))
    src = NAHBCostOfConstructingAHomeSource(client=client, cache_root=tmp_path)
    return src


# --- 1. Adapter instantiates without error ------------------------------

def test_adapter_instantiates_without_error() -> None:
    src = NAHBCostOfConstructingAHomeSource()
    try:
        assert src.name == "nahb_construction_cost"
        assert src.homepage_url.startswith("https://www.nahb.org/")
        assert src.requires_env_vars == []
        assert "NAHB" in src.license_str
    finally:
        src.close()


def test_backward_compat_reexport_from_construction_indexes() -> None:
    """The Worker P stub previously lived in construction_indexes.py; the
    re-export shim must point at the new real class."""
    assert RexportedNAHBSource is NAHBCostOfConstructingAHomeSource


# --- 2. URL is the documented NAHB public landing -----------------------

def test_url_is_documented_public_landing(tmp_path: Path) -> None:
    captured: dict = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["method"] = request.method
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["residential-single-family-national"])
    assert captured["url"] == NAHB_LATEST_ARTICLE_URL
    assert captured["method"] == "GET"
    assert "nahb.org" in NAHB_LATEST_ARTICLE_URL
    assert "cost-of-constructing-a-home" in NAHB_LATEST_ARTICLE_URL


def test_default_series_returns_documented_series_id() -> None:
    src = NAHBCostOfConstructingAHomeSource()
    try:
        assert src.default_series() == ["residential-single-family-national"]
    finally:
        src.close()


# --- 3. Mock HTML response → parsed snapshot has expected fields --------

def test_fetch_parses_canned_html_into_expected_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["residential-single-family-national"])

    assert len(snaps) == 1
    s = snaps[0]
    assert s.source == "nahb_construction_cost"
    assert s.series_id == "residential-single-family-national"
    assert "NAHB" in s.label
    assert "single-family" in s.label
    assert s.unit == "USD"  # NOT "index"
    assert s.value == pytest.approx(428_215.0)
    assert s.region == "US"
    assert s.csi_division is None
    assert s.naics == "236115"
    assert s.period == "2024"
    assert "NAHB" in s.license
    assert s.source_url == NAHB_LATEST_ARTICLE_URL
    assert s.raw is not None
    assert s.raw["total_construction_cost_usd"] == pytest.approx(428_215.0)
    assert s.raw["provenance"] == "live article parse"


def test_fetch_latest_returns_single_snapshot(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.series_id == "residential-single-family-national"
    assert snap.value == pytest.approx(428_215.0)
    assert snap.period == "2024"


# --- 4. 4xx response → graceful failure (hardcoded-fallback shipped) ----

def test_fetch_handles_4xx_with_hardcoded_fallback(tmp_path: Path) -> None:
    """On 4xx, the adapter falls back to the most-recent hardcoded
    historical value rather than returning empty. This is the brief's
    'write the adapter that would work + flag the limitation' posture —
    a snapshot still ships so downstream estimators always have a value,
    and the snapshot's raw['provenance'] tags it as a fallback."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(404, text="not found")

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["residential-single-family-national"])
    assert len(snaps) == 1
    s = snaps[0]
    # Latest hardcoded year is 2024 with $428,215.
    assert s.period == "2024"
    assert s.value == pytest.approx(428_215.0)
    assert s.source_url == NAHB_HOMEPAGE_URL
    assert s.raw is not None
    assert s.raw["provenance"] == "hardcoded historical fallback"


def test_fetch_handles_5xx_with_hardcoded_fallback(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, text="service unavailable")

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["residential-single-family-national"])
    assert len(snaps) == 1
    assert snaps[0].raw["provenance"] == "hardcoded historical fallback"


def test_fetch_handles_unparseable_html_with_hardcoded_fallback(
    tmp_path: Path,
) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200, text="<html><body>Maintenance window in progress.</body></html>",
        )

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(["residential-single-family-national"])
    assert len(snaps) == 1
    assert snaps[0].raw["provenance"] == "hardcoded historical fallback"
    assert snaps[0].period == "2024"  # most recent hardcoded entry


# --- 5. Cache hit → no second HTTP call within 24h ----------------------

def test_cache_avoids_second_http_call(tmp_path: Path) -> None:
    call_count = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        call_count["n"] += 1
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    src.fetch(["residential-single-family-national"])
    src.fetch(["residential-single-family-national"])
    assert call_count["n"] == 1


# --- 6. Period parsing — biennial year format ---------------------------

def test_period_is_4digit_year_not_yyyy_mm(tmp_path: Path) -> None:
    """NAHB is biennial; the period is just the survey year (YYYY), not
    YYYY-MM or YYYY-QN like the other CCI adapters."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.period == "2024"
    assert len(snap.period) == 4
    assert snap.period.isdigit()


def test_find_study_year_picks_most_recent_mention() -> None:
    """The article body mentions multiple study years (1998, 2011, 2022,
    2024). The helper should pick the most recent."""
    assert _find_study_year("the 2024 survey is $428,215") == "2024"
    assert _find_study_year("history: 1998, 2011, 2022, 2024") == "2024"
    assert _find_study_year("") is None
    assert _find_study_year("no year here, just text") is None


# --- 7. Historical hardcoded values present + period-tagged correctly ---

def test_hardcoded_historical_values_present() -> None:
    """The historical table must include the key inflection-point years
    used in the BPC playbook + ROADMAP discussions: 1998 baseline, 2017
    pre-COVID, 2022 post-COVID, 2024 most recent."""
    for year in ("1998", "2017", "2019", "2022", "2024"):
        assert year in NAHB_HISTORICAL_TOTAL_COST
    assert NAHB_HISTORICAL_TOTAL_COST["1998"] == pytest.approx(124_276.0)
    assert NAHB_HISTORICAL_TOTAL_COST["2024"] == pytest.approx(428_215.0)


def test_fetch_history_returns_period_tagged_snapshots(tmp_path: Path) -> None:
    """fetch_history returns one snapshot per published survey year, each
    tagged with the correct YYYY period."""
    src = NAHBCostOfConstructingAHomeSource()
    try:
        snaps = src.fetch_history()
        assert len(snaps) >= 10  # 1998..2024 inclusive
        periods = [s.period for s in snaps]
        assert periods == sorted(periods)  # ascending order
        for s in snaps:
            assert s.period in NAHB_HISTORICAL_TOTAL_COST
            assert s.value == pytest.approx(
                NAHB_HISTORICAL_TOTAL_COST[s.period]
            )
            assert s.unit == "USD"
            assert s.naics == "236115"
    finally:
        src.close()


def test_fetch_history_periods_arg_limits_count() -> None:
    src = NAHBCostOfConstructingAHomeSource()
    try:
        snaps = src.fetch_history(periods=3)
        assert len(snaps) == 3
        # Must be the three most recent.
        assert snaps[-1].period == "2024"
    finally:
        src.close()


# --- 8. Headline figure plausibility check ($100k - $1M) ----------------

def test_headline_figure_within_plausibility_range(tmp_path: Path) -> None:
    """A single-family home total construction cost should land between
    $100k (floor since at least the early 1990s) and $1M (well above
    even high-end markets in the published series). Validates against
    the brief's $100k-$1M plausibility check."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert 100_000.0 < snap.value < 1_000_000.0


def test_hardcoded_values_all_within_plausibility_range() -> None:
    for year, value in NAHB_HISTORICAL_TOTAL_COST.items():
        assert 100_000.0 < value < 1_000_000.0, (
            f"{year}: {value} is outside $100k-$1M plausibility window"
        )


# --- 9. unit is "USD" not "index" ---------------------------------------

def test_unit_is_dollar_not_index(tmp_path: Path) -> None:
    """NAHB's headline is an absolute dollar value per home — explicitly
    NOT a dimensionless index. This is the structural difference vs the
    three CCI adapters and the reason this adapter is not wired into
    core/pricing/escalation.py's macro CCI hook."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.unit == "USD"
    assert snap.unit != "index"


# --- 10. naics is "236115" ---------------------------------------------

def test_naics_is_residential_construction(tmp_path: Path) -> None:
    """NAICS 236115 = New Single-Family Housing Construction (except
    for-sale builders). Confirms the adapter tags snapshots with the
    correct industry code."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.naics == "236115"


# --- Misc invariants the brief calls out --------------------------------

def test_unknown_series_id_is_skipped(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snaps = src.fetch(
        ["residential-single-family-national", "multifamily-national"]
    )
    assert len(snaps) == 1
    assert snaps[0].series_id == "residential-single-family-national"


def test_anchors_include_documented_phrases() -> None:
    """Regression: 'Total Construction Cost' must be the primary anchor."""
    assert NAHB_ANCHORS[0] == "Total Construction Cost"
    assert any("average construction cost" in a.lower() for a in NAHB_ANCHORS)


def test_find_headline_dollar_value_picks_first_plausible_match() -> None:
    """The lead paragraph contains $91,057 (lot cost, below the $50k
    plausibility floor wouldn't apply — but it's $91k, which is well
    below the $124k historical floor). The first plausible Total
    Construction Cost match is $428,215; that's what should win."""
    text = (
        "A. Finished Lot Cost $91,057 13.7% "
        "B. Total Construction Cost $428,215 64.4% "
    )
    assert _find_headline_dollar_value(text, ["Total Construction Cost"]) == pytest.approx(
        428_215.0
    )


def test_find_headline_dollar_value_returns_none_when_no_anchor() -> None:
    text = "<html><body>Nothing relevant here.</body></html>"
    assert _find_headline_dollar_value(text, NAHB_ANCHORS) is None


def test_csi_division_is_none(tmp_path: Path) -> None:
    """NAHB is a whole-house aggregate — explicitly NOT a per-CSI cost."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=CANNED_NAHB_HTML)

    src = _build_mock_source(handler, tmp_path)
    snap = src.fetch_latest()
    assert snap.csi_division is None
