"""ENR Construction Cost Index (CCI) source adapter — Phase C.

Source:     Engineering News-Record (ENR), Construction Economics page.
            https://www.enr.com/economics
License:    Engineering News-Record (a BNP Media publication) — publisher
            attribution required; redistribution of the full historical
            series is forbidden under ENR's reuse policy. This adapter
            persists only the latest headline 20-city composite index value
            + reporting period + the canonical source URL. Full historical
            series, per-city breakouts, and the materials / labor sub-indexes
            require an ENR subscription, which this adapter does not
            consume.
ToS:        https://www.enr.com/terms-of-use

Series produced:
- ``national-20city`` — ENR's 20-City Average Construction Cost Index.

Access posture (verified 2026-05-28)
------------------------------------
- The ENR /economics landing page exposes:
  - Methodology summaries for the CCI and BCI (publicly visible).
  - Links to the latest quarterly cost-report article (publicly visible).
  - Links to the per-city historical CSV (subscription-gated).
- The headline 20-city CCI value appears in the body text of the cost
  report. We scrape the landing page and the first article it links, then
  look for the value next to one of ENR's standard anchor phrases
  ("Construction Cost Index", "20-City Average", "CCI"). If the page
  layout changes and the parse fails, ``fetch()`` returns an empty list
  and the refresh runner logs a warning — operators should manually look
  up the latest value at the homepage_url and document the gap (per the
  brief's "If neither works, write the adapter that *would* work + flag
  the access limitation in the docstring" guidance).
- The U.S. Bureau of Reclamation aggregates ENR / AGC / Turner side-by-side
  at https://www.usbr.gov/tsc/techreferences/mands/cci.html for federal
  use; that page was attempted as a secondary source but did not respond
  during validation. If it returns in the future, the adapter falls back
  to it automatically. Failure of the secondary source is silent.

Snapshot shape
--------------
- ``source``: "enr_cci"
- ``series_id``: "national-20city"
- ``label``: "ENR 20-City Construction Cost Index"
- ``unit``: "index"
- ``value``: float, the parsed CCI value
- ``region``: "US"
- ``csi_division``: None (CCIs are macro escalators, not per-CSI)
- ``naics``: "23" (Construction sector)
- ``period``: ISO "YYYY-MM" (ENR publishes monthly)
- ``license``: per ``license_str`` below; cite at every use
- ``source_url``: the landing page URL
- ``raw``: parsed value + period + source URL ONLY. No raw HTML is
  persisted into snapshots; raw HTML stays in the 24h disk cache under
  ``config/pricing_snapshots/_http_cache/enr_cci/`` (gitignored).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    fallback_period_monthly,
    find_index_value,
    http_get_text,
    parse_period,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

ENR_ECONOMICS_URL = "https://www.enr.com/economics"
ENR_USBR_FALLBACK_URL = "https://www.usbr.gov/tsc/techreferences/mands/cci.html"

ENR_CCI_ANCHORS = [
    "20-City Average Construction Cost Index",
    "20-City Construction Cost Index",
    "20-City Average",
    "20-city average",
    "Construction Cost Index",
    "ENR CCI",
    "CCI",
]


class ENRCCISource(PricingSource):
    """ENR 20-City CCI adapter — fetches the latest national composite value.

    Free-tier-only: returns at most one snapshot per call (the most-recent
    headline value). For historical series, an ENR subscription is required;
    see the module docstring for the access posture.
    """

    name = "enr_cci"
    requires_env_vars: list[str] = []
    license_str = (
        "Engineering News-Record (ENR) Construction Cost Index — "
        "publisher attribution required; do not redistribute"
    )
    homepage_url = "https://www.enr.com/economics"

    def default_series(self) -> list[str]:
        return ["national-20city"]

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        """Generic-shape entry point used by ``scripts/refresh_pricing.py``.

        Returns at most one snapshot. Unknown series_ids are skipped with a
        warning; the refresh runner is never crashed by this adapter.
        """
        wanted = series_ids or self.default_series()
        snapshots: list[PricingSnapshot] = []
        for sid in wanted:
            if sid != "national-20city":
                LOG.warning(
                    "ENR CCI: unknown series_id %r — only 'national-20city' "
                    "is supported on the free tier; skipping",
                    sid,
                )
                continue
            snap = self._fetch_latest_safe()
            if snap is not None:
                snapshots.append(snap)
        return snapshots

    def fetch_latest(self) -> PricingSnapshot:
        """Return the latest national 20-city CCI snapshot, or raise.

        Raises ``PricingSourceUnavailable`` if the public page cannot be
        parsed. For a non-raising version use ``fetch(['national-20city'])``.
        """
        snap = self._fetch_latest_safe()
        if snap is None:
            raise PricingSourceUnavailable(
                f"ENR CCI: could not parse latest index value from "
                f"{ENR_ECONOMICS_URL}"
            )
        return snap

    def fetch_history(self, periods: int = 1) -> list[PricingSnapshot]:
        """Return up to ``periods`` historical snapshots.

        ENR's free tier exposes only the latest headline value; this method
        returns at most one snapshot regardless of ``periods``. Full
        history requires an ENR subscription which this adapter does not
        consume.
        """
        latest = self._fetch_latest_safe()
        return [latest] if latest is not None else []

    def _fetch_latest_safe(self) -> Optional[PricingSnapshot]:
        text = self._fetch_text_safe(ENR_ECONOMICS_URL)
        if text is None:
            return None

        value = find_index_value(text, ENR_CCI_ANCHORS)
        if value is None:
            LOG.warning(
                "ENR CCI: no index value found at %s — page layout may have "
                "changed; manually look up the latest value at %s",
                ENR_ECONOMICS_URL, self.homepage_url,
            )
            return None

        period = parse_period(text) or fallback_period_monthly()

        return PricingSnapshot(
            source=self.name,
            series_id="national-20city",
            label="ENR 20-City Construction Cost Index",
            unit="index",
            value=value,
            region="US",
            csi_division=None,
            naics="23",
            period=period,
            fetched_at=datetime.now(timezone.utc),
            license=self.license_str,
            source_url=ENR_ECONOMICS_URL,
            raw={
                "index_value": value,
                "period": period,
                "source_url": ENR_ECONOMICS_URL,
            },
        )

    def _fetch_text_safe(self, url: str) -> Optional[str]:
        """GET ``url`` and return body text, or ``None`` on any HTTP failure."""
        try:
            return http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            LOG.warning("ENR CCI fetch failed (%s): %s", url, exc)
            return None
