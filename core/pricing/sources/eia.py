"""EIA fuel-price adapter — weekly retail diesel + regular gas, PADD3.

API:        https://api.eia.gov/v2/petroleum/pri/gnd/data/
Auth:       Requires EIA_API_KEY (free at https://www.eia.gov/opendata/register.php).
License:    U.S. Public Domain — Energy Information Administration.
            https://www.eia.gov/about/copyrights_reuse.php
ToS:        https://www.eia.gov/about/disclaimer.php

PADD3 = Petroleum Administration for Defense District 3 (Gulf Coast). This is
the relevant region for Texas-based bids because retail diesel in TX tracks
the PADD3 weekly retail observation closely.

This adapter outputs one snapshot per (product, period) point. `unit` is
"USD/gallon".
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

EIA_GND_URL = "https://api.eia.gov/v2/petroleum/pri/gnd/data/"

# EIA series IDs (from petroleum/pri/gnd):
#   EMD_EPD2D_PTE_R30_DPG = U.S. PADD3 No 2 Diesel Retail Price
#   EMM_EPMR_PTE_R30_DPG  = U.S. PADD3 Regular Gasoline Retail Price
_DEFAULT_SERIES = {
    "EMD_EPD2D_PTE_R30_DPG": {
        "label": "PADD3 — No. 2 ultra-low-sulfur diesel, retail",
        "product": "diesel",
    },
    "EMM_EPMR_PTE_R30_DPG": {
        "label": "PADD3 — regular gasoline, retail",
        "product": "regular_gas",
    },
}


class EIAFuelSource(PricingSource):
    name = "eia"
    requires_env_vars: list[str] = ["EIA_API_KEY"]
    license_str = "U.S. Public Domain — Energy Information Administration (EIA)"
    homepage_url = "https://www.eia.gov/petroleum/gasdiesel/"

    def default_series(self) -> list[str]:
        return list(_DEFAULT_SERIES.keys())

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        if not series_ids:
            return []

        api_key = self.env("EIA_API_KEY")
        if not api_key:
            LOG.warning("EIA_API_KEY not set; skipping EIA fetch.")
            return []

        snapshots: list[PricingSnapshot] = []
        for sid in series_ids:
            meta = _DEFAULT_SERIES.get(sid, {"label": sid, "product": "unknown"})
            params: dict[str, Any] = {
                "api_key": api_key,
                "frequency": "weekly",
                "data[0]": "value",
                "facets[series][]": sid,
                "sort[0][column]": "period",
                "sort[0][direction]": "desc",
                "offset": "0",
                "length": str(int(filters.get("length", 12))),
            }
            try:
                payload = self.http_get(EIA_GND_URL, params=params)
            except Exception as exc:  # noqa: BLE001
                LOG.warning("EIA fetch failed for %s: %s", sid, exc)
                continue

            response = payload.get("response", {}) or {}
            for obs in response.get("data", []) or []:
                value = obs.get("value")
                if value in (None, ""):
                    continue
                try:
                    value_f = float(value)
                except (TypeError, ValueError):
                    continue
                period = str(obs.get("period") or "unknown")
                raw = {
                    "period": obs.get("period"),
                    "value": obs.get("value"),
                    "series": obs.get("series"),
                    "duoarea": obs.get("duoarea"),
                    "product": obs.get("product"),
                    "process": obs.get("process"),
                }
                snapshots.append(
                    PricingSnapshot(
                        source=self.name,
                        series_id=sid,
                        label=str(meta.get("label") or sid),
                        unit="USD/gallon",
                        value=value_f,
                        region="PADD3",
                        csi_division="01",
                        period=period,
                        fetched_at=datetime.now(timezone.utc),
                        license=self.license_str,
                        source_url="https://www.eia.gov/petroleum/gasdiesel/",
                        raw=raw,
                    )
                )
        return snapshots
