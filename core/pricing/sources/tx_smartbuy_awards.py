"""TX SmartBuy / ESBD award postings scraper — Phase C STUB.

Source:     Texas SmartBuy + Electronic State Business Daily.
            - https://comptroller.texas.gov/purchasing/contracts/
            - https://www.txsmartbuy.com/esbd
License:    State of Texas public records.
ToS:        https://comptroller.texas.gov/about/policies/website-policy.php
            Polite use; do not scrape behind login walls; cite source.

[Phase C — NOT YET IMPLEMENTED — stub only]

Why deferred: Historical award postings are useful for sub-pricing
reference, but the data is captured as a paginated HTML index plus per-
award detail pages with inconsistent column layouts across agencies. A
robust parser needs:

  1. Polite rate-limited HTTP (BeautifulSoup4 + httpx + a per-domain
     RateLimiter from `tenacity` — `bs4` is NOT a current project dep).
  2. Per-agency column-mapping table.
  3. Award-line-item normalization to CSI sections / NAICS.

TODO:
- Add bs4 to requirements when this work is greenlit (pin exact version).
- Confirm ToS for automated browsing.
- Negotiate a sane scrape cadence (daily? weekly?) with the user.
"""

from __future__ import annotations

import logging
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


class TXSmartBuyAwardsSource(PricingSource):
    name = "tx_smartbuy_awards"
    requires_env_vars: list[str] = []
    license_str = "State of Texas public record — TX SmartBuy / ESBD"
    homepage_url = "https://comptroller.texas.gov/purchasing/contracts/"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        # [Phase C — NOT YET IMPLEMENTED]
        LOG.info(
            "TXSmartBuyAwardsSource.fetch is a stub. See module docstring."
        )
        return []
