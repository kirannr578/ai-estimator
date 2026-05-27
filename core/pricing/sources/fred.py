"""FRED (Federal Reserve Economic Data) adapter.

API:        https://api.stlouisfed.org/fred/series/observations
Auth:       Requires FRED_API_KEY (free with email registration).
            https://fred.stlouisfed.org/docs/api/api_key.html
License:    Most series are U.S. federal public-domain or covered by FRED's
            terms permitting downstream non-commercial + commercial use with
            attribution. Each series page documents its specific provenance.
            https://fred.stlouisfed.org/legal/
ToS:        https://fred.stlouisfed.org/docs/api/terms_of_use.html
            We comply by: (a) attributing source in every snapshot
            (`license` field), (b) honoring the published rate limits via
            our 24h cache, (c) never republishing the data wholesale.

The API key value is read from the env var only at fetch time, sent as a
query string parameter (as the FRED API requires), and intentionally NOT
written into the snapshot's `raw` payload (the cache layer hashes the URL
including the key, but doesn't surface the key elsewhere).
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

FRED_OBS_URL = "https://api.stlouisfed.org/fred/series/observations"


_SERIES_CATALOG: dict[str, dict[str, str]] = {
    "PCU2122202122201": {
        "label": "Construction sand & gravel PPI",
        "unit": "index", "csi": "32",
    },
    "WPUSI012011": {
        "label": "Inputs to construction industries (PPI)",
        "unit": "index", "csi": "01",
    },
    "CES2000000003": {
        "label": "Construction — average hourly earnings, national",
        "unit": "USD/hr", "csi": "01",
    },
    "PPIIDC": {
        "label": "PPI — industrial commodities",
        "unit": "index", "csi": "01",
    },
    "DCOILWTICO": {
        "label": "Crude oil — WTI spot (fuel cost proxy)",
        "unit": "USD/barrel", "csi": "01",
    },
    "USACPALTT01CTGYM": {
        "label": "CPI — All items, total, Texas (growth, YoY)",
        "unit": "% YoY", "csi": "01",
    },
    "CONSTLOAN": {
        "label": "Commercial-bank construction loan rate index",
        "unit": "%", "csi": "01",
    },
    "CSUSHPINSA": {
        "label": "Case-Shiller national home price index (residential context)",
        "unit": "index", "csi": "01",
    },
}


class FREDSource(PricingSource):
    name = "fred"
    requires_env_vars: list[str] = ["FRED_API_KEY"]
    license_str = "FRED® data terms — Federal Reserve Bank of St. Louis"
    homepage_url = "https://fred.stlouisfed.org/"

    def default_series(self) -> list[str]:
        return list(_SERIES_CATALOG.keys())

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        if not series_ids:
            return []

        api_key = self.env("FRED_API_KEY")
        if not api_key:
            LOG.warning("FRED_API_KEY not set; skipping FRED fetch.")
            return []

        snapshots: list[PricingSnapshot] = []
        for sid in series_ids:
            meta = _SERIES_CATALOG.get(sid, {"label": sid, "unit": "index", "csi": None})
            params: dict[str, Any] = {
                "series_id": sid,
                "api_key": api_key,
                "file_type": "json",
                "sort_order": "desc",
                "limit": int(filters.get("limit", 12)),
            }
            if "observation_start" in filters:
                params["observation_start"] = filters["observation_start"]
            if "observation_end" in filters:
                params["observation_end"] = filters["observation_end"]

            try:
                payload = self.http_get(FRED_OBS_URL, params=params)
            except Exception as exc:  # noqa: BLE001 — adapter must not crash refresh
                LOG.warning("FRED fetch failed for %s: %s", sid, exc)
                continue

            for obs in payload.get("observations", []) or []:
                value_str = obs.get("value")
                if value_str in (None, "", ".", "NA"):
                    continue
                try:
                    value = float(value_str)
                except (TypeError, ValueError):
                    continue
                period = str(obs.get("date") or "unknown")
                # Scrub the cached payload before persisting — `obs` doesn't
                # contain the api_key, but be explicit about not leaking auth.
                raw = {"date": obs.get("date"), "value": obs.get("value"), "series_id": sid}
                snapshots.append(
                    PricingSnapshot(
                        source=self.name,
                        series_id=sid,
                        label=str(meta.get("label") or sid),
                        unit=str(meta.get("unit") or "index"),
                        value=value,
                        region=None,
                        csi_division=meta.get("csi"),
                        period=period,
                        fetched_at=datetime.now(timezone.utc),
                        license=self.license_str,
                        source_url=f"https://fred.stlouisfed.org/series/{sid}",
                        raw=raw,
                    )
                )
        return snapshots
