"""ENR / AGC / Turner / NAHB Construction Cost Indexes — Phase C STUB.

Sources, all paywalled or quarterly-PDF for free tier:

- ENR Construction Cost Index (CCI) — Engineering News-Record. Free monthly
  national + 20-city values published as PDF / web table at
  https://www.enr.com/economics. Cited publicly; ENR's reuse policy
  requires attribution and forbids redistribution.

- AGC Construction Inflation Alert + producer-price summaries —
  https://www.agc.org/learn/construction-data. Free to download with
  attribution; AGC ToS https://www.agc.org/about-agc/agc-website-terms-use

- Turner Building Cost Index (TBI) — quarterly. Free PDF at
  https://www.turnerconstruction.com/cost-index. Turner's terms require
  attribution.

- NAHB "Cost of Constructing a Home" — annual report. Free PDF at
  https://www.nahb.org/news-and-economics/housing-economics/cost-of-constructing-a-home

License:    Each publisher's terms apply — DO NOT redistribute, DO cite
            source in every snapshot.
ToS:        See per-publisher links above.

[Phase C — NOT YET IMPLEMENTED — stubs for four indexes]

Why deferred:
- Each publisher uses a different PDF layout that changes quarterly.
- The signal is largely covered by BLS PPI (`bls_ppi`) + the FRED
  construction-loan-rate index (`fred`), so the marginal value is low for
  v1.

TODO (Phase C-full):
- Per-publisher PDF parser using `pymupdf` (already a project dep).
- Cache parsed indexes monthly (CCI / TBI) or annually (NAHB).
"""

from __future__ import annotations

import logging
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


class ENRConstructionCostIndexSource(PricingSource):
    name = "enr_cci"
    requires_env_vars: list[str] = []
    license_str = "ENR Construction Cost Index — publisher attribution required"
    homepage_url = "https://www.enr.com/economics"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        LOG.info("ENRConstructionCostIndexSource is a stub. See module docstring.")
        return []


class AGCInflationAlertSource(PricingSource):
    name = "agc_inflation_alert"
    requires_env_vars: list[str] = []
    license_str = "AGC of America — publisher attribution required"
    homepage_url = "https://www.agc.org/learn/construction-data"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        LOG.info("AGCInflationAlertSource is a stub. See module docstring.")
        return []


class TurnerBuildingCostIndexSource(PricingSource):
    name = "turner_bci"
    requires_env_vars: list[str] = []
    license_str = "Turner Construction — publisher attribution required"
    homepage_url = "https://www.turnerconstruction.com/cost-index"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        LOG.info("TurnerBuildingCostIndexSource is a stub. See module docstring.")
        return []


class NAHBCostOfConstructingAHomeSource(PricingSource):
    name = "nahb_cost_of_home"
    requires_env_vars: list[str] = []
    license_str = "NAHB — publisher attribution required"
    homepage_url = "https://www.nahb.org/news-and-economics/housing-economics/cost-of-constructing-a-home"

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        LOG.info("NAHBCostOfConstructingAHomeSource is a stub. See module docstring.")
        return []
