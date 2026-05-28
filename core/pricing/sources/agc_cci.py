"""AGC PPI-based Construction Cost Index (CCI) source adapter — Phase C.

Source:     Associated General Contractors of America (AGC),
            Construction Data + Construction Inflation Alert.
            https://www.agc.org/learn/construction-data
License:    AGC of America — publisher attribution required; redistribution
            of AGC's analytical commentary and the formatted Inflation Alert
            PDFs is not permitted under AGC's website terms. This adapter
            persists only the parsed headline index value (or the
            most-recent producer-price summary number) + reporting period +
            the canonical source URL.
ToS:        https://www.agc.org/about-agc/agc-website-terms-use

Series produced:
- ``national`` — AGC's national construction-inflation roll-up. AGC does
  not publish a single dimensionless "CCI" comparable to ENR's; their
  headline figure is a composite of BLS PPI series that AGC re-aggregates
  in the Construction Inflation Alert. We surface the headline figure
  printed on the public Construction Data landing page so downstream
  callers can use it as a macro escalator complementary to BLS PPI.

Access posture (verified 2026-05-28)
------------------------------------
- The AGC /learn/construction-data page is publicly visible and lists:
  - "Data Digest" — a weekly one-page summary (publicly downloadable PDF).
  - "Construction Industry Outlook" — quarterly outlook (publicly
    downloadable PDF).
  - "State Fact Sheets" — by-state employment + spending one-pagers.
  - "Producer Prices & Employment Costs" — landing for the BLS PPI tables
    AGC re-publishes with construction-specific commentary.
- The headline number AGC publishes is most commonly framed as a
  year-over-year producer-price percent change (e.g. "Producer prices for
  construction inputs rose 4.7% over the 12 months ending April 2026").
  The adapter scrapes the landing page and looks for an index value in
  proximity to one of AGC's standard anchor phrases.
- AGC's value-add over BLS PPI is the analytical commentary in the
  Construction Inflation Alert PDF, which we deliberately do NOT
  redistribute (license posture). For programmatic escalation, BLS PPI
  (Phase A, ``core/pricing/sources/bls_ppi.py``) is the more reliable
  primary source; this adapter complements it as a cross-check.

Caveat
------
If the AGC landing page does not yield a parseable index value (because
the headline is solely a percent-change figure that doesn't satisfy the
plausibility filter, or because the page structure changes), ``fetch()``
returns an empty list with a logged warning rather than crashing. This is
consistent with the brief's "write the adapter that would work + flag the
access limitation" guidance — the AGC public surface area is less
structured than ENR's or Turner's, so a graceful no-op on parse failure
is the right default.

Snapshot shape
--------------
- ``source``: "agc_cci"
- ``series_id``: "national"
- ``label``: "AGC PPI-based Construction Cost Index"
- ``unit``: "index"
- ``value``: float, the parsed headline value
- ``region``: "US"
- ``csi_division``: None (macro escalator)
- ``naics``: "23" (Construction sector)
- ``period``: ISO "YYYY-MM" (AGC's Data Digest is weekly; the underlying
  PPI series are monthly).
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

AGC_CONSTRUCTION_DATA_URL = "https://www.agc.org/learn/construction-data"

# Anchor phrases AGC uses to introduce the headline figure on the public
# Construction Data page and the Inflation Alert previews. Ordered most
# specific first; ``find_index_value`` returns the first plausible match.
AGC_ANCHORS = [
    "PPI for inputs to new construction",
    "PPI for construction inputs",
    "inputs to nonresidential construction",
    "Producer prices for construction inputs",
    "Producer Price Index",
    "Construction Inflation Alert",
    "construction inflation",
    "construction input price index",
    "CCI",
]


class AGCCCISource(PricingSource):
    """AGC PPI-based CCI adapter — public Construction Data landing page.

    Returns at most one snapshot per call. The headline figure AGC frames
    publicly is a producer-price index value with a percent-change overlay;
    this adapter persists the parsed index value when present.
    """

    name = "agc_cci"
    requires_env_vars: list[str] = []
    license_str = (
        "AGC of America Construction Inflation Alert — publisher attribution "
        "required; do not redistribute"
    )
    homepage_url = "https://www.agc.org/learn/construction-data"

    def default_series(self) -> list[str]:
        return ["national"]

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        wanted = series_ids or self.default_series()
        snapshots: list[PricingSnapshot] = []
        for sid in wanted:
            if sid != "national":
                LOG.warning(
                    "AGC CCI: unknown series_id %r — only 'national' is "
                    "supported on the free tier; skipping",
                    sid,
                )
                continue
            snap = self._fetch_latest_safe()
            if snap is not None:
                snapshots.append(snap)
        return snapshots

    def fetch_latest(self) -> PricingSnapshot:
        """Return the latest AGC PPI-based snapshot, or raise."""
        snap = self._fetch_latest_safe()
        if snap is None:
            raise PricingSourceUnavailable(
                f"AGC CCI: could not parse latest index value from "
                f"{AGC_CONSTRUCTION_DATA_URL}"
            )
        return snap

    def fetch_history(self, periods: int = 1) -> list[PricingSnapshot]:
        """Return up to ``periods`` historical snapshots.

        AGC's public landing page exposes the latest headline only;
        historical Inflation Alert PDFs are linked there but each PDF would
        require an additional fetch + parser per period. This method
        currently returns at most one snapshot. Extending to full history
        is a future slice once a stable AGC URL convention is confirmed.
        """
        latest = self._fetch_latest_safe()
        return [latest] if latest is not None else []

    def _fetch_latest_safe(self) -> Optional[PricingSnapshot]:
        text = self._fetch_text_safe(AGC_CONSTRUCTION_DATA_URL)
        if text is None:
            return None

        value = find_index_value(text, AGC_ANCHORS)
        if value is None:
            LOG.warning(
                "AGC CCI: no index value found at %s — page may currently "
                "show only percent-change figures; manually look up the "
                "latest PPI inputs index at %s",
                AGC_CONSTRUCTION_DATA_URL, self.homepage_url,
            )
            return None

        period = parse_period(text) or fallback_period_monthly()

        return PricingSnapshot(
            source=self.name,
            series_id="national",
            label="AGC PPI-based Construction Cost Index",
            unit="index",
            value=value,
            region="US",
            csi_division=None,
            naics="23",
            period=period,
            fetched_at=datetime.now(timezone.utc),
            license=self.license_str,
            source_url=AGC_CONSTRUCTION_DATA_URL,
            raw={
                "index_value": value,
                "period": period,
                "source_url": AGC_CONSTRUCTION_DATA_URL,
            },
        )

    def _fetch_text_safe(self, url: str) -> Optional[str]:
        try:
            return http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            LOG.warning("AGC CCI fetch failed (%s): %s", url, exc)
            return None
