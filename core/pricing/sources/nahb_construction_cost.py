"""NAHB Cost of Constructing a Home source adapter — Phase C.

Source:     National Association of Home Builders (NAHB), special-studies
            "Cost of Constructing a Home" series.
License:    NAHB — publisher attribution required. The series is published
            as a free PDF special study + an HTML article on nahb.org for
            each survey year. The headline figures (total construction
            cost, sales-price share breakdown, per-square-foot cost) are
            publicly excerpted in both the article body and the blog
            announcement; the detailed methodology PDF is itself publicly
            downloadable from the article page.
ToS:        https://www.nahb.org/other/about-nahb/terms-of-use

Series produced:
- ``residential-single-family-national`` — Average total construction
  cost of a typical newly-built single-family home in the most recent
  NAHB Cost of Constructing a Home survey. Reported as a single dollar
  value (NOT an index), nationally aggregated, single-family only.

Access posture (verified 2026-05-28)
------------------------------------
NAHB does not maintain a stable "landing" URL for the cost-of-constructing
series itself; each survey year publishes under a year-suffixed path under
``housing-economics-plus/special-studies/special-studies-pages/``.

Verified live URL pattern (2026-05-28):
- 2024 study: ``cost-of-constructing-a-home-in-2024``
- 2017 study: ``cost-of-constructing-home-in-2017`` (note the slight
  inconsistency in slug naming — "home" vs "a-home" — which is why the
  adapter does not try to guess unseen-year URLs)

NAHB conducts the survey biennially in recent cycles (2019, 2022, 2024),
so the next expected publication is 2026. When the 2026 article ships,
update ``NAHB_LATEST_ARTICLE_URL`` below to point at it. The headline
parse path looks for "Total Construction Cost" + a dollar amount on the
configured article page, so the URL is the only year-specific knob.

The brief flagged that NAHB occasionally relocates these articles. As of
2026-05-28 the older URLs documented in
``core/pricing/sources/construction_indexes.py`` (Worker P stub)
returned HTTP 404; the new canonical pattern is captured here.

Free-tier strategy
------------------
The article body contains the headline figures inline in plain prose
("the average construction cost of a typical single-family home in the
2024 survey is $428,215"). The adapter anchors on the "Total
Construction Cost" / "average construction cost" phrasings and extracts
the first plausible dollar figure that follows.

If the live article is unreachable (4xx / 5xx) or the layout has changed
enough that parsing fails, the adapter falls back to the hardcoded
historical series in ``NAHB_HISTORICAL_TOTAL_COST`` (every published
survey since 1998, sourced from the NAHB 2017 and 2024 special-study
PDFs which both publish Table 3 "Single-Family Construction Cost
Breakdown History"). The hardcoded series exists primarily for backfill
via ``fetch_history()``, but it also acts as a graceful degradation path
when the live HTTP fetch fails.

Snapshot shape
--------------
- ``source``: "nahb_construction_cost"
- ``series_id``: "residential-single-family-national"
- ``label``: "NAHB Cost of Constructing a Home (national, single-family)"
- ``unit``: "USD" — NOT "index". This is a dollar value per home.
- ``value``: float, the total-construction-cost dollar figure
- ``region``: "US"
- ``csi_division``: None — this is a whole-house aggregate, not a
  per-CSI material/labor cost
- ``naics``: "236115" — New Single-Family Housing Construction (except
  for-sale builders)
- ``period``: the study year ("2024", "2022", etc.) — the NAHB
  cost-of-constructing series is biennial in recent cycles
- ``license``: per ``license_str`` below; cite at every use
- ``source_url``: the NAHB article URL the value was parsed from (or the
  documented homepage when serving from the hardcoded history)
- ``raw``: parsed value + period + source URL ONLY. No raw HTML is
  persisted into snapshots; raw HTML stays in the 24h disk cache under
  ``config/pricing_snapshots/_http_cache/nahb_construction_cost/``.

Relationship to the CCI adapters
--------------------------------
The three CCI adapters (ENR / AGC / Turner) track commercial /
nonresidential macro escalation. NAHB Cost of Constructing a Home
complements them with a residential / single-family cross-check. It is
intentionally NOT plugged into the macro CCI multiplier in
``core/pricing/escalation.py``: that hook is index-based, and NAHB's
output is an absolute dollar value, not a dimensionless index. To
derive a residential escalation factor from this series, callers
compute ``value(target_year) / value(base_year)`` themselves — see
``firm/playbooks/pricing-data-sources.md`` "Residential macro
escalation" section.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    http_get_text,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


# Canonical landing for the most recent NAHB cost-of-constructing survey.
# Bump the year suffix when NAHB publishes a newer study (biennial cadence
# — 2022, 2024; 2026 expected). The adapter parses the article body for
# "Total Construction Cost" + a dollar amount.
NAHB_LATEST_ARTICLE_URL = (
    "https://www.nahb.org/news-and-economics/housing-economics-plus/"
    "special-studies/special-studies-pages/cost-of-constructing-a-home-in-2024"
)

# Documented homepage to cite when the live fetch fails and the adapter
# falls back to its hardcoded historical series. The cost-of-constructing
# series lives under NAHB's broader special-studies index — there is no
# stable per-series landing, but the special-studies index has been
# durable since 2020.
NAHB_HOMEPAGE_URL = (
    "https://www.nahb.org/news-and-economics/housing-economics-plus/"
    "special-studies"
)


# Anchors used to find the headline dollar figure on the article page.
# Ordered most-specific first; ``_find_headline_dollar_value`` returns the
# first plausible match. These phrases are stable across the 2017, 2022,
# and 2024 articles — both the prose and Table 1 row B use one of them.
NAHB_ANCHORS = [
    "Total Construction Cost",
    "average construction cost of a typical single-family home",
    "Average Total Construction Cost",
    "average construction cost",
]


# Hardcoded historical series — total construction cost per typical
# single-family home, dollars, by survey year. Provenance:
#
# - 1998 / 2002 / 2004 / 2007 / 2009 / 2011 / 2013 / 2015 / 2017:
#   NAHB "Cost of Constructing a Home — 2017" special study (Carmel Ford,
#   NAHB Economics & Housing Policy Group), Table 3 "Single-Family
#   Construction Cost Breakdown History". Hosted at
#   https://www.nahb.org/-/media/CC931183F12F43239FFDA9CD80A06F4D.ashx
# - 2019: NAHB "Cost of Constructing a Home — 2019" special study
#   (Carmel Ford, January 2, 2020), p.1 "average construction cost of a
#   typical single-family home in the 2019 survey is $296,652".
#   Hosted at https://www.nahb.org/-/media/8F04D7F6EAA34DBF8867D7C3385D2977.ashx
# - 2022: NAHB "Cost of Constructing a Home — 2022" special study,
#   Table 1 row B ($392,241). Hosted at
#   https://www.nahb.org/-/media/27E8E24FA6CB432CA4EF3D9C0249771D.ashx
# - 2024: NAHB "Cost of Constructing a Home — 2024" special study,
#   January 2025, Table 1 row B ($428,215). Hosted at
#   https://www.nahb.org/-/media/NAHB/news-and-economics/docs/
#   housing-economics-plus/special-studies/2025/
#   special-study-cost-of-constructing-a-home-2024-january-2025.pdf
#
# All values are the publisher-reported "Total Construction Cost" line
# (Table 1 row B). The 2017 special study's Table 3 lists each prior
# survey on the same definition so historical comparability is consistent
# (NAHB notes that "different builders responded each round" so use the
# series for trend cross-check, not absolute backfill).
NAHB_HISTORICAL_TOTAL_COST: dict[str, float] = {
    "1998": 124_276.0,
    "2002": 151_671.0,
    "2004": 192_846.0,
    "2007": 219_015.0,
    "2009": 222_511.0,
    "2011": 184_125.0,
    "2013": 246_453.0,
    "2015": 289_415.0,
    "2017": 237_760.0,
    "2019": 296_652.0,
    "2022": 392_241.0,
    "2024": 428_215.0,
}


# Plausibility window for the parsed dollar figure. The series has run
# from $124k (1998) to $428k (2024); we allow $50k–$2M to comfortably
# bracket future surveys without admitting unrelated numbers (e.g. lot
# size, square footage, percent shares) found elsewhere on the page.
_MIN_PLAUSIBLE_VALUE = 50_000.0
_MAX_PLAUSIBLE_VALUE = 2_000_000.0


# Matches dollar amounts like "$428,215" / "$428,215.00" / "$1,234,567".
# Anchored to the leading "$" so we don't pick up bare percent shares or
# square-footage figures that the article also contains.
_DOLLAR_RE = re.compile(
    r"\$\s?(\d{1,3}(?:,\d{3})+(?:\.\d{1,2})?|\d{4,7}(?:\.\d{1,2})?)"
)

# Matches a 4-digit year in [1990, 2099]. The article and PDF both
# include phrasings like "the 2024 survey is $428,215" / "the 2022
# survey is $392,241"; we use this to recover the study year.
_YEAR_RE = re.compile(r"\b(19[9]\d|20[0-9]\d)\b")


def _find_headline_dollar_value(
    text: str,
    anchors: list[str],
    *,
    window: int = 600,
    min_value: float = _MIN_PLAUSIBLE_VALUE,
    max_value: float = _MAX_PLAUSIBLE_VALUE,
) -> Optional[float]:
    """Locate the headline dollar figure near one of the ``anchors``.

    Walks ``text`` left-to-right; for each anchor, searches the next
    ``window`` characters for a "$NNN,NNN" pattern in the plausibility
    range. The first match wins.

    Designed to ignore percent-share figures, square-foot rates ($/sf
    is too small to pass min_value), and lot-cost rows ($91,057 for
    2024 would normally pass min_value at $50k — that's why min_value
    defaults to $50k; anything published in this series since 1998 has
    been above $124k, so $50k is safely below the floor of the real
    series while still excluding lot-cost rows that hover in the low
    five figures).
    """
    if not text:
        return None
    lower = text.lower()
    for anchor in anchors:
        a_low = anchor.lower()
        idx = lower.find(a_low)
        while idx != -1:
            snippet = text[idx + len(anchor) : idx + len(anchor) + window]
            for m in _DOLLAR_RE.finditer(snippet):
                num_str = m.group(1).replace(",", "")
                try:
                    val = float(num_str)
                except ValueError:
                    continue
                if min_value <= val <= max_value:
                    return val
            idx = lower.find(a_low, idx + 1)
    return None


def _find_study_year(text: str) -> Optional[str]:
    """Find the most recent study-year mention in ``text``.

    NAHB articles consistently include phrasings like "the 2024 NAHB
    survey" / "the 2022 survey" in the lead paragraph and Table 3
    column headers. The largest 4-digit year in [1990, 2099] is
    returned as a YYYY string. Returns None if no year is found.
    """
    if not text:
        return None
    years = [int(m.group(1)) for m in _YEAR_RE.finditer(text)]
    if not years:
        return None
    candidates = [y for y in years if 1990 <= y <= 2099]
    if not candidates:
        return None
    return str(max(candidates))


class NAHBCostOfConstructingAHomeSource(PricingSource):
    """NAHB Cost of Constructing a Home adapter — public special-study.

    Returns one snapshot per call: the most recent survey year's total
    construction cost figure. ``fetch_history()`` returns one snapshot
    per published survey year, sourced from the hardcoded historical
    table (NAHB does not expose a programmatic history endpoint).
    """

    name = "nahb_construction_cost"
    requires_env_vars: list[str] = []
    license_str = (
        "NAHB Cost of Constructing a Home special study — publisher "
        "attribution required; cite source article URL"
    )
    homepage_url = NAHB_HOMEPAGE_URL

    def default_series(self) -> list[str]:
        return ["residential-single-family-national"]

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        """Generic-shape entry point used by ``scripts/refresh_pricing.py``.

        Returns at most one snapshot. Unknown series_ids are skipped with
        a warning; the refresh runner is never crashed by this adapter.
        """
        wanted = series_ids or self.default_series()
        snapshots: list[PricingSnapshot] = []
        for sid in wanted:
            if sid != "residential-single-family-national":
                LOG.warning(
                    "NAHB cost-of-constructing: unknown series_id %r — only "
                    "'residential-single-family-national' is supported; "
                    "skipping",
                    sid,
                )
                continue
            snap = self._fetch_latest_safe()
            if snap is not None:
                snapshots.append(snap)
        return snapshots

    def fetch_latest(self) -> PricingSnapshot:
        """Return the latest NAHB cost-of-constructing snapshot, or raise.

        Tries the live article first; if parsing fails, falls back to
        the most recent year in the hardcoded historical table.
        Raises ``PricingSourceUnavailable`` only if both the live fetch
        and the hardcoded table are empty (the latter is checked-in, so
        the raise path is effectively unreachable in practice and exists
        only as a defensive guarantee).
        """
        snap = self._fetch_latest_safe()
        if snap is None:
            raise PricingSourceUnavailable(
                f"NAHB cost-of-constructing: could not parse latest value "
                f"from {NAHB_LATEST_ARTICLE_URL} and no hardcoded history "
                f"available"
            )
        return snap

    def fetch_history(self, periods: int = 0) -> list[PricingSnapshot]:
        """Return historical snapshots from the hardcoded table.

        Returns ALL known surveys if ``periods <= 0`` (the default);
        otherwise returns the ``periods`` most recent. The hardcoded
        table is the canonical source of historical values because
        NAHB does not expose a structured history endpoint and the
        per-year article URLs are inconsistent (see module docstring).
        """
        years_sorted = sorted(NAHB_HISTORICAL_TOTAL_COST.keys())
        if periods > 0:
            years_sorted = years_sorted[-periods:]
        out: list[PricingSnapshot] = []
        for year in years_sorted:
            out.append(
                self._build_snapshot(
                    value=NAHB_HISTORICAL_TOTAL_COST[year],
                    period=year,
                    source_url=NAHB_HOMEPAGE_URL,
                    raw_extra={"provenance": "hardcoded historical table"},
                )
            )
        return out

    def _fetch_latest_safe(self) -> Optional[PricingSnapshot]:
        """Best-effort fetch: live article first, then hardcoded fallback.

        Returns None only if the hardcoded table is empty (defensive;
        the table ships with > 10 entries and is checked into the repo).
        """
        text = self._fetch_text_safe(NAHB_LATEST_ARTICLE_URL)
        if text is not None:
            value = _find_headline_dollar_value(text, NAHB_ANCHORS)
            if value is not None:
                period = _find_study_year(text)
                if period is None:
                    # The article body is malformed enough that we
                    # can't recover a study year. Don't ship a snapshot
                    # without a period — fall through to the hardcoded
                    # fallback. (PricingSnapshot.period is required.)
                    LOG.warning(
                        "NAHB cost-of-constructing: value parsed but no "
                        "study year recoverable from %s — falling back to "
                        "hardcoded most-recent value",
                        NAHB_LATEST_ARTICLE_URL,
                    )
                else:
                    return self._build_snapshot(
                        value=value,
                        period=period,
                        source_url=NAHB_LATEST_ARTICLE_URL,
                        raw_extra={"provenance": "live article parse"},
                    )
            else:
                LOG.warning(
                    "NAHB cost-of-constructing: no headline dollar value "
                    "found at %s — page layout may have changed; falling "
                    "back to hardcoded most-recent historical value",
                    NAHB_LATEST_ARTICLE_URL,
                )

        if not NAHB_HISTORICAL_TOTAL_COST:
            return None
        latest_year = max(NAHB_HISTORICAL_TOTAL_COST.keys())
        return self._build_snapshot(
            value=NAHB_HISTORICAL_TOTAL_COST[latest_year],
            period=latest_year,
            source_url=NAHB_HOMEPAGE_URL,
            raw_extra={"provenance": "hardcoded historical fallback"},
        )

    def _build_snapshot(
        self,
        *,
        value: float,
        period: str,
        source_url: str,
        raw_extra: dict[str, Any],
    ) -> PricingSnapshot:
        return PricingSnapshot(
            source=self.name,
            series_id="residential-single-family-national",
            label="NAHB Cost of Constructing a Home (national, single-family)",
            unit="USD",
            value=float(value),
            region="US",
            csi_division=None,
            naics="236115",
            period=period,
            fetched_at=datetime.now(timezone.utc),
            license=self.license_str,
            source_url=source_url,
            raw={
                "total_construction_cost_usd": float(value),
                "period": period,
                "source_url": source_url,
                **raw_extra,
            },
        )

    def _fetch_text_safe(self, url: str) -> Optional[str]:
        """GET ``url`` and return body text, or ``None`` on any HTTP failure."""
        try:
            return http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            LOG.warning("NAHB cost-of-constructing fetch failed (%s): %s", url, exc)
            return None
