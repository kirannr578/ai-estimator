"""NAHB Cost of Constructing a Home — Phase C STUB.

This module previously also stubbed the ENR / AGC / Turner cost-index
adapters. Those three are now shipped as dedicated modules:

- ``core/pricing/sources/enr_cci.py`` — ENR 20-City CCI
- ``core/pricing/sources/agc_cci.py`` — AGC PPI-based CCI
- ``core/pricing/sources/turner_cci.py`` — Turner Building Cost Index

Only NAHB remains as a stub here pending demand for its residential cost
breakdown.

Source:     NAHB "Cost of Constructing a Home" — annual report. Free PDF at
            https://www.nahb.org/news-and-economics/housing-economics/cost-of-constructing-a-home
License:    NAHB — publisher attribution required.

[Phase C — NOT YET IMPLEMENTED — annual NAHB report parser]
"""

from __future__ import annotations

import logging
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


class NAHBCostOfConstructingAHomeSource(PricingSource):
    name = "nahb_cost_of_home"
    requires_env_vars: list[str] = []
    license_str = "NAHB — publisher attribution required"
    homepage_url = (
        "https://www.nahb.org/news-and-economics/housing-economics/"
        "cost-of-constructing-a-home"
    )

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        LOG.info("NAHBCostOfConstructingAHomeSource is a stub. See module docstring.")
        return []
