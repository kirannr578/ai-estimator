"""Davis-Bacon Wage Determinations adapter (SAM.gov / beta.SAM).

Source:     SAM.gov Wage Determinations OnLine (WDOL successor).
            Public search endpoint (no auth required for read):
              https://sam.gov/api/prod/wage-determinations/v1/search
            And per-WD detail:
              https://sam.gov/api/prod/wage-determinations/v1/<wd_number>
License:    U.S. Public Domain — U.S. Department of Labor, Wage and Hour
            Division. WDs themselves are federal public-domain documents.
ToS:        https://sam.gov/about/policies/terms-of-use

Use:
    src = DavisBaconSource()
    snaps = src.fetch_for_project(state="TX", county="Tom Green",
                                  project_type="Building")

Caveats:
- SAM.gov's API can rate-limit aggressive callers without warning. We honor
  the 24h base cache.
- Schemas have shifted in the past; if a response shape changes, the parser
  falls back to a permissive walker that pulls whatever trade rows it can
  recognize, rather than crashing the refresh.
- DOL trade classifications do not exactly map to SOC codes one-to-one;
  `DOL_TO_SOC` below is a best-effort crosswalk for the most common trades.
  Unmapped trades still produce a snapshot with `soc_code=None`.

This adapter writes one snapshot per (trade, county, WD) tuple, plus an
auxiliary record at config/pricing_snapshots/davis_bacon/<state>/<county>/<wd>.json
that captures the raw WD search hit + PDF URL for human retrieval.
"""

from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Optional

from core.pricing import snapshots as _snap_mod
from core.pricing.snapshots import PricingSnapshot, write_text_record
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)

SAM_WD_SEARCH_URL = "https://sam.gov/api/prod/wage-determinations/v1/search"


DOL_TO_SOC: dict[str, str] = {
    "CARPENTER": "47-2031",
    "LABORER": "47-2061",
    "OPERATING ENGINEER": "47-2073",
    "POWER EQUIPMENT OPERATOR": "47-2073",
    "ELECTRICIAN": "47-2111",
    "PLUMBER": "47-2152",
    "PIPEFITTER": "47-2152",
    "SHEET METAL WORKER": "47-2211",
    "PAINTER": "47-2141",
    "DRYWALL FINISHER": "47-2081",
    "DRYWALL HANGER": "47-2081",
    "ROOFER": "47-2181",
    "BRICKLAYER": "47-2021",
    "CEMENT MASON": "47-2051",
    "IRONWORKER": "47-2221",
    "TRUCK DRIVER": "53-3032",
}


def map_classification_to_soc(classification: str) -> Optional[str]:
    """Best-effort DOL-trade-string → SOC mapping. Returns None when unknown."""
    if not classification:
        return None
    upper = classification.upper()
    for key, soc in DOL_TO_SOC.items():
        if key in upper:
            return soc
    return None


class DavisBaconSource(PricingSource):
    name = "davis_bacon"
    requires_env_vars: list[str] = []
    license_str = "U.S. Public Domain — DOL Wage & Hour Division (Davis-Bacon)"
    homepage_url = "https://sam.gov/wage-determinations"

    def default_series(self) -> list[str]:
        # No "default" series for WDs — they're keyed by (state, county,
        # project_type, WD number). The refresh runner calls
        # `fetch_for_project` per active bid instead.
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        """Generic fetch — each ``series_id`` is a WD number; ``filters`` may
        carry ``state`` / ``county`` / ``project_type``."""
        snapshots: list[PricingSnapshot] = []
        state = filters.get("state")
        county = filters.get("county")
        project_type = filters.get("project_type", "Building")
        for wd in series_ids:
            snapshots.extend(
                self.fetch_for_project(
                    state=state, county=county, project_type=project_type,
                    wd_number=wd,
                )
            )
        return snapshots

    def fetch_for_project(
        self,
        *,
        state: Optional[str],
        county: Optional[str],
        project_type: str = "Building",
        wd_number: Optional[str] = None,
    ) -> list[PricingSnapshot]:
        if not state:
            LOG.warning("Davis-Bacon: state is required.")
            return []

        params: dict[str, Any] = {
            "state": state,
            "constructionType": project_type,
            "status": "Active",
        }
        if county:
            params["county"] = county
        if wd_number:
            params["wageDeterminationNumber"] = wd_number

        try:
            payload = self.http_get(SAM_WD_SEARCH_URL, params=params)
        except Exception as exc:  # noqa: BLE001
            LOG.warning("Davis-Bacon search failed: %s", exc)
            return []

        hits = (
            payload.get("results")
            or payload.get("_embedded", {}).get("wageDeterminations")
            or payload.get("data")
            or []
        )

        snapshots: list[PricingSnapshot] = []
        for wd in hits:
            wd_no = (
                wd.get("wageDeterminationNumber")
                or wd.get("number")
                or wd.get("id")
                or "UNKNOWN"
            )
            mod_date = (
                wd.get("modificationDate")
                or wd.get("effectiveDate")
                or wd.get("publicationDate")
                or "unknown"
            )
            pdf_url = wd.get("pdfUrl") or wd.get("documentUrl") or ""

            # Persist auxiliary WD pointer (PDF URL etc.) for human retrieval.
            # Look up SNAPSHOTS_ROOT via the module so tests that monkeypatch
            # it after import still route the write to the right place.
            county_safe = (county or "all").replace(" ", "_")
            write_text_record(
                source=self.name,
                series_id=f"{state}_{county_safe}",
                period=f"{wd_no}",
                payload={
                    "wd_number": wd_no,
                    "state": state,
                    "county": county,
                    "project_type": project_type,
                    "modification_date": mod_date,
                    "pdf_url": pdf_url,
                    "raw": wd,
                },
                root=_snap_mod.SNAPSHOTS_ROOT,
            )

            for cls in wd.get("classifications", []) or []:
                trade = cls.get("classification") or cls.get("name") or ""
                rate = cls.get("baseWageRate") or cls.get("rate") or cls.get("hourlyRate")
                if rate in (None, ""):
                    continue
                try:
                    rate_f = float(rate)
                except (TypeError, ValueError):
                    continue
                soc = map_classification_to_soc(trade)
                series_id = f"{wd_no}__{trade.replace(' ', '_')}"
                snapshots.append(
                    PricingSnapshot(
                        source=self.name,
                        series_id=series_id,
                        label=f"{trade} — {county or state} ({wd_no})",
                        unit="USD/hr",
                        value=rate_f,
                        region=f"{state}-{county}" if county else state,
                        csi_division="01",
                        soc_code=soc,
                        period=str(mod_date),
                        fetched_at=datetime.now(timezone.utc),
                        license=self.license_str,
                        source_url=pdf_url or f"https://sam.gov/wage-determinations/{wd_no}",
                        raw={
                            "wd_number": wd_no,
                            "classification": cls,
                        },
                    )
                )
        return snapshots
