"""Turner Building Cost Index (TBCI) source adapter — Phase C.

Source:     Turner Construction Company, quarterly Building Cost Index.
            https://www.turnerconstruction.com/cost-index
License:    Turner Construction — publisher attribution required;
            redistribution of the full TBCI history is not permitted under
            Turner's website terms. This adapter persists only the latest
            headline quarterly index value + reporting period + the
            canonical source URL.
ToS:        https://www.turnerconstruction.com/terms

Series produced:
- ``national`` — Turner's national Building Cost Index. Turner publishes
  one quarterly value tracking labor rates + productivity, material
  prices, and the competitive marketplace condition on a nationwide
  basis. No regional breakouts on the free tier.

Access posture (verified 2026-05-28)
------------------------------------
- The /cost-index page is publicly visible and lists every quarterly
  TBCI release going back to 2006. The latest value appears in the body
  of the current quarter's article. The page is well-structured: each
  quarter's heading follows the convention "NTH QUARTER YYYY" /
  "Turner Building Cost Index ... [value]" so a small regex over the
  rendered page text reliably finds the headline number.
- Turner provides the index value as a single dimensionless number
  (base 1967 = 100). No JSON / CSV download is offered for free; the
  page text is the canonical source.
- If the page layout changes and the parse fails, ``fetch()`` returns
  an empty list with a logged warning — operators should manually look
  up the latest TBCI value at the homepage_url and document the gap
  (per the brief's "If neither works, write the adapter that *would*
  work + flag the access limitation" guidance).

Snapshot shape
--------------
- ``source``: "turner_cci"
- ``series_id``: "national"
- ``label``: "Turner Building Cost Index"
- ``unit``: "index"
- ``value``: float, the parsed TBCI value
- ``region``: "US"
- ``csi_division``: None (macro escalator)
- ``naics``: "23" (Construction sector)
- ``period``: ISO "YYYY-QN" (Turner publishes quarterly)
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources._cci_common import (
    PricingSourceUnavailable,
    fallback_period_quarterly,
    find_index_value,
    http_get_text,
    parse_period,
)
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

TURNER_COST_INDEX_URL = "https://www.turnerconstruction.com/cost-index"

# Turner's terminology has been stable across the public page since the
# index's 2006-era reformat. We anchor on the published label first, then
# fall back to the shorter "TBCI" abbreviation if the long form is absent.
TURNER_ANCHORS = [
    "Turner Building Cost Index",
    "TBCI",
    "Building Cost Index",
]


class TurnerCCISource(PricingSource):
    """Turner Building Cost Index adapter — public quarterly page.

    Returns at most one snapshot per call (the latest published quarter).
    """

    name = "turner_cci"
    requires_env_vars: list[str] = []
    license_str = (
        "Turner Construction — Turner Building Cost Index — publisher "
        "attribution required; do not redistribute"
    )
    homepage_url = "https://www.turnerconstruction.com/cost-index"

    def default_series(self) -> list[str]:
        return ["national"]

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        wanted = series_ids or self.default_series()
        snapshots: list[PricingSnapshot] = []
        for sid in wanted:
            if sid != "national":
                LOG.warning(
                    "Turner CCI: unknown series_id %r — only 'national' is "
                    "supported on the free tier; skipping",
                    sid,
                )
                continue
            snap = self._fetch_latest_safe()
            if snap is not None:
                snapshots.append(snap)
        return snapshots

    def fetch_latest(self) -> PricingSnapshot:
        """Return the latest TBCI snapshot, or raise."""
        snap = self._fetch_latest_safe()
        if snap is None:
            raise PricingSourceUnavailable(
                f"Turner CCI: could not parse latest index value from "
                f"{TURNER_COST_INDEX_URL}"
            )
        return snap

    def fetch_history(self, periods: int = 1) -> list[PricingSnapshot]:
        """Return up to ``periods`` historical snapshots.

        Turner's free page lists every quarter back to 2006 but each
        historical value lives inside its own per-quarter article that
        would require a separate fetch + parse. This method currently
        returns at most one snapshot (the latest). Extending to full
        history is a future slice.
        """
        latest = self._fetch_latest_safe()
        return [latest] if latest is not None else []

    def _fetch_latest_safe(self) -> Optional[PricingSnapshot]:
        text = self._fetch_text_safe(TURNER_COST_INDEX_URL)
        if text is None:
            return None

        value = find_index_value(text, TURNER_ANCHORS)
        if value is None:
            LOG.warning(
                "Turner CCI: no index value found at %s — page layout may "
                "have changed; manually look up the latest TBCI value at %s",
                TURNER_COST_INDEX_URL, self.homepage_url,
            )
            return None

        period = parse_period(text, prefer_quarterly=True) or fallback_period_quarterly()

        return PricingSnapshot(
            source=self.name,
            series_id="national",
            label="Turner Building Cost Index",
            unit="index",
            value=value,
            region="US",
            csi_division=None,
            naics="23",
            period=period,
            fetched_at=datetime.now(timezone.utc),
            license=self.license_str,
            source_url=TURNER_COST_INDEX_URL,
            raw={
                "index_value": value,
                "period": period,
                "source_url": TURNER_COST_INDEX_URL,
            },
        )

    def _fetch_text_safe(self, url: str) -> Optional[str]:
        try:
            return http_get_text(
                self._client, self._cache_root, self.name, url,
            )
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Turner CCI fetch failed (%s): %s", url, exc)
            return None
