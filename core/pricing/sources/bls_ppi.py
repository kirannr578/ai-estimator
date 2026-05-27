"""BLS Producer Price Index adapter.

API:        https://api.bls.gov/publicAPI/v2/timeseries/data/
Auth:       Optional. Without a key: 25 requests / day. With BLS_API_KEY:
            500 requests / day.
License:    U.S. Public Domain — Bureau of Labor Statistics.
            https://www.bls.gov/bls/linksite.htm
ToS:        https://www.bls.gov/developers/termsOfService.htm
            Polite use; no scraping; cite source. We comply by sending a
            descriptive User-Agent, caching responses for 24h, and limiting
            the curated series count to ~15.

Why these series: covers the dominant material inputs across the CSI
divisions in `config/cost_database.json` (wood, plywood, engineered wood,
gypsum, steel mill, structural-steel fabricated, copper wire, diesel,
ready-mix, asphalt, paint, plastics/PVC, plumbing fittings).

This adapter does NOT log or persist the API key value into snapshots or
disk cache; only the request hash is recorded.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"

# Per-series metadata: human label + CSI division hint + unit + license note.
# Units here describe what the index TRACKS, not what it RETURNS — BLS PPI
# values are dimensionless index numbers (typically base year = 100). The
# `unit` we record is intentionally "index" because absolute price levels are
# NOT what PPI publishes; downstream code uses index-to-index ratios to
# escalate the seed cost DB (see core/pricing/escalation.py).
_SERIES_CATALOG: dict[str, dict[str, str]] = {
    "WPU0811":     {"label": "Softwood lumber",                       "csi": "06", "unit": "index"},
    "WPU0812":     {"label": "Hardwood lumber",                       "csi": "06", "unit": "index"},
    "WPU0814":     {"label": "Plywood & veneer",                      "csi": "06", "unit": "index"},
    "WPU081305":   {"label": "Engineered wood (LVL / I-joists)",      "csi": "06", "unit": "index"},
    "WPU102201":   {"label": "Gypsum products (incl. drywall)",       "csi": "09", "unit": "index"},
    "WPU101":      {"label": "Iron & steel scrap",                    "csi": "05", "unit": "index"},
    "WPU1017":     {"label": "Steel mill products (structural)",      "csi": "05", "unit": "index"},
    "WPU102301":   {"label": "Copper wire & cable",                   "csi": "26", "unit": "index"},
    "WPU057303":   {"label": "Diesel fuel",                           "csi": "01", "unit": "index"},
    "WPU132":      {"label": "Ready-mix concrete",                    "csi": "03", "unit": "index"},
    "WPU1351":     {"label": "Roofing asphalt & asphalt products",    "csi": "07", "unit": "index"},
    "WPU065":      {"label": "Paints & coatings",                     "csi": "09", "unit": "index"},
    "WPU062":      {"label": "Plastics products (incl. PVC pipe)",    "csi": "22", "unit": "index"},
    "WPU101707":   {"label": "Fabricated structural steel",           "csi": "05", "unit": "index"},
    "WPU2025201":  {"label": "Plumbing fixtures & brass fittings",    "csi": "22", "unit": "index"},
}


class BLSPPISource(PricingSource):
    name = "bls_ppi"
    requires_env_vars: list[str] = []  # works (rate-limited) without a key
    license_str = "U.S. Public Domain — Bureau of Labor Statistics (BLS PPI)"
    homepage_url = "https://www.bls.gov/ppi/"

    def default_series(self) -> list[str]:
        return list(_SERIES_CATALOG.keys())

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        if not series_ids:
            return []

        body: dict[str, Any] = {"seriesid": list(series_ids)}
        # Optional date range filters; BLS accepts startyear / endyear (YYYY)
        if "startyear" in filters:
            body["startyear"] = str(filters["startyear"])
        if "endyear" in filters:
            body["endyear"] = str(filters["endyear"])

        api_key = self.env("BLS_API_KEY")
        if api_key:
            body["registrationkey"] = api_key
            body["catalog"] = True

        payload = self.http_post_json(BLS_API_URL, body)

        status = str(payload.get("status", "")).upper()
        if status and status != "REQUEST_SUCCEEDED":
            messages = payload.get("message", []) or []
            LOG.warning("BLS PPI request did not succeed (%s): %s", status, messages)
            return []

        snapshots: list[PricingSnapshot] = []
        results = payload.get("Results", {}) or {}
        for series in results.get("series", []) or []:
            sid = series.get("seriesID") or series.get("seriesId") or ""
            meta = _SERIES_CATALOG.get(sid, {"label": sid, "csi": None, "unit": "index"})
            for obs in series.get("data", []) or []:
                period = _bls_period(obs.get("year"), obs.get("period"))
                value_str = obs.get("value")
                if value_str in (None, "", "-"):
                    continue
                try:
                    value = float(value_str)
                except (TypeError, ValueError):
                    continue
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
                        source_url=f"https://data.bls.gov/timeseries/{sid}",
                        raw={"observation": obs, "seriesID": sid},
                    )
                )
        return snapshots


def _bls_period(year: Any, period: Any) -> str:
    """Convert BLS year+period into our canonical period string.

    BLS period codes:
      - M01..M12 — monthly
      - Q01..Q04 — quarterly
      - A01      — annual
    """
    y = str(year or "")
    p = str(period or "")
    if not y:
        return p or "unknown"
    if p.startswith("M") and len(p) == 3:
        return f"{y}-{p[1:]}"
    if p.startswith("Q") and len(p) == 3:
        return f"{y}-Q{p[2]}"
    if p == "A01":
        return y
    return f"{y}-{p}" if p else y
