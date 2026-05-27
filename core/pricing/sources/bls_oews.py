"""BLS Occupational Employment & Wage Statistics adapter.

API:        https://api.bls.gov/publicAPI/v2/timeseries/data/
Auth:       Optional. With BLS_API_KEY: 500 requests / day.
License:    U.S. Public Domain — Bureau of Labor Statistics (OEWS).
            https://www.bls.gov/oes/oes_emp.htm
ToS:        https://www.bls.gov/developers/termsOfService.htm

Series ID grammar for OEWS metropolitan-level hourly mean wages:

    OEU<area_type><area_code><industry_code><occupation_code><datatype>

Where:
  - area_type = "M" for MSA
  - area_code = 7-digit MSA code (we use Texas metros below)
  - industry_code = "000000" for cross-industry
  - occupation_code = 6-digit SOC, no hyphen (e.g. 472031)
  - datatype = "04" for hourly mean wage

Example: OEUM004191240000004720310 4  -> Austin MSA, Carpenters, hourly mean.

We curate 10 SOC codes that map to BPC's most-used trades across 6 Texas
metros. Output `unit` is "USD/hr", `region` is the MSA code, `soc_code`
is the SOC with the canonical hyphen for cross-referencing.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

BLS_API_URL = "https://api.bls.gov/publicAPI/v2/timeseries/data/"


# Six TX metros. Codes are the 7-digit OES area codes (which differ from the
# 5-digit MSA / CBSA codes used elsewhere — BLS pads with leading zeros).
_TX_METROS: dict[str, str] = {
    "0019124": "Dallas-Plano-Irving, TX MD",
    "0026420": "Houston-The Woodlands-Sugar Land, TX",
    "0012420": "Austin-Round Rock, TX",
    "0041700": "San Antonio-New Braunfels, TX",
    "0031180": "Lubbock, TX",
    "0017780": "College Station-Bryan, TX",
}

# Ten construction-trade SOC codes. Stored as canonical "XX-XXXX" strings;
# we strip the hyphen when composing OES series ids.
_TRADE_SOCS: dict[str, str] = {
    "47-2031": "Carpenters",
    "47-2061": "Construction Laborers",
    "47-2073": "Operating Engineers (construction equipment)",
    "47-2111": "Electricians",
    "47-2152": "Plumbers, Pipefitters, Steamfitters",
    "47-2211": "Sheet Metal Workers",
    "47-2141": "Painters, Construction & Maintenance",
    "47-2081": "Drywall & Ceiling Tile Installers",
    "47-2181": "Roofers",
    "47-1011": "First-Line Supervisors of Construction Trades",
}


def _build_series_id(metro_area_code: str, soc: str, datatype: str = "04") -> str:
    """Compose an OEWS hourly-mean series id for one (metro, trade) pair.

    `datatype` 04 = hourly mean wage. 13 = hourly median.
    """
    soc_no_dash = soc.replace("-", "")
    return f"OEUM{metro_area_code}000000{soc_no_dash}{datatype}"


def all_default_series() -> list[str]:
    """Return all (metro x trade) OEWS series ids for the curated lists."""
    return [
        _build_series_id(metro, soc)
        for metro in _TX_METROS
        for soc in _TRADE_SOCS
    ]


def parse_series_id(series_id: str) -> dict[str, str]:
    """Reverse the series id grammar back to its semantic parts.

    Layout: ``OEUM<7-digit area><6-digit industry><6-digit SOC><2-digit datatype>``
    Total length: 4 + 7 + 6 + 6 + 2 = 25 characters.
    """
    if not series_id.startswith("OEUM") or len(series_id) < 25:
        return {}
    area = series_id[4:11]
    industry = series_id[11:17]
    occ = series_id[17:23]
    datatype = series_id[23:25]
    soc = f"{occ[:2]}-{occ[2:]}" if len(occ) == 6 else occ
    return {
        "area_code": area,
        "industry_code": industry,
        "occupation_code": occ,
        "soc_code": soc,
        "datatype": datatype,
    }


class BLSOEWSSource(PricingSource):
    name = "bls_oews"
    requires_env_vars: list[str] = []  # works rate-limited without key
    license_str = "U.S. Public Domain — Bureau of Labor Statistics (OEWS)"
    homepage_url = "https://www.bls.gov/oes/"

    def default_series(self) -> list[str]:
        return all_default_series()

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        if not series_ids:
            return []

        # BLS POST limit is 50 series per request without a key, 50 with;
        # batch to be safe.
        batch_size = 50
        snapshots: list[PricingSnapshot] = []
        for i in range(0, len(series_ids), batch_size):
            batch = list(series_ids[i : i + batch_size])
            body: dict[str, Any] = {"seriesid": batch}
            if "startyear" in filters:
                body["startyear"] = str(filters["startyear"])
            if "endyear" in filters:
                body["endyear"] = str(filters["endyear"])
            api_key = self.env("BLS_API_KEY")
            if api_key:
                body["registrationkey"] = api_key

            payload = self.http_post_json(BLS_API_URL, body)
            status = str(payload.get("status", "")).upper()
            if status and status != "REQUEST_SUCCEEDED":
                LOG.warning(
                    "BLS OEWS batch failed (%s): %s",
                    status, payload.get("message", []),
                )
                continue

            for series in (payload.get("Results", {}) or {}).get("series", []) or []:
                sid = series.get("seriesID") or series.get("seriesId") or ""
                parsed = parse_series_id(sid)
                soc = parsed.get("soc_code", "")
                area = parsed.get("area_code", "")
                trade_label = _TRADE_SOCS.get(soc, soc)
                metro_label = _TX_METROS.get(area, area)
                for obs in series.get("data", []) or []:
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
                            label=f"{trade_label} — {metro_label}",
                            unit="USD/hr",
                            value=value,
                            region=area,
                            csi_division="01",
                            soc_code=soc,
                            period=str(obs.get("year") or "unknown"),
                            fetched_at=datetime.now(timezone.utc),
                            license=self.license_str,
                            source_url=f"https://data.bls.gov/oes/#/area/{area}",
                            raw={"observation": obs, "seriesID": sid},
                        )
                    )
        return snapshots
