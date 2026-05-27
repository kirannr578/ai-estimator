"""GSA Schedule price-list importer (Phase B — partial).

Source:     GSA Advantage publishes Federal Supply Schedule price lists
            (CSV catalogs) at https://www.gsaadvantage.gov/ref_text/.
License:    U.S. Public Domain — General Services Administration.
            https://www.gsaadvantage.gov/advantage/text/footer/disclaimer.do
ToS:        Polite use; cite source.

Scope:      Only construction-relevant categories:
              - 56V    — Construction Materials
              - 03FAC  — Facilities Maintenance / Management
              - 23V    — Industrial Products & Services (overlaps with construction)

[Phase B — partial implementation]

What ships here:
- A working ``parse_catalog_csv`` that takes a CSV string and emits
  ``PricingSnapshot``s with `source="gsa_schedule"`. Driven by an already-
  downloaded catalog.
- ``fetch_from_csv_file(path, *, schedule_code)`` for local-file ingestion.

What's deferred:
- Auto-discovery + download of the latest catalog from gsaadvantage.gov.
  GSA Advantage's catalog index is published as a Schedule-specific FTP
  directory listing; pulling it requires HTTP + a polite back-off the Phase
  B-full work will add. Today the operator downloads the CSV manually and
  hands it to ``fetch_from_csv_file``.

TODO (Phase B-full):
- Pull the per-schedule catalog index (HTML).
- Resolve the newest CSV for each schedule code.
- Add inference for CSI division from the GSA SIN (Special Item Number).
"""

from __future__ import annotations

import csv
import io
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from core.pricing.snapshots import PricingSnapshot
from core.pricing.sources.base import PricingSource

LOG = logging.getLogger(__name__)


# Best-effort SIN-prefix → CSI division. Conservative; falls back to None.
_SIN_TO_CSI: dict[str, str] = {
    "332":  "05",  # metals
    "238":  "06",  # wood / siding
    "327":  "03",  # concrete / masonry
    "335":  "26",  # electrical equipment
    "326":  "07",  # plastics / rubber / roofing materials
    "238110": "03",
    "238120": "05",
    "238130": "06",
    "238140": "04",
    "238150": "08",
    "238160": "07",
    "238170": "08",
    "238210": "26",
    "238220": "23",
    "238290": "23",
    "238310": "09",
    "238320": "09",
    "238330": "09",
    "238340": "09",
    "238350": "06",
    "238910": "31",
}


def _infer_csi_division(sin: str) -> Optional[str]:
    sin = (sin or "").strip()
    if not sin:
        return None
    for prefix_len in (6, 3):
        prefix = sin[:prefix_len]
        if prefix in _SIN_TO_CSI:
            return _SIN_TO_CSI[prefix]
    return None


def _parse_unit_from_description(desc: str) -> str:
    """Coarse heuristic — extract a unit token from the description.
    Returns "USD/EA" by default.
    """
    if not desc:
        return "USD/EA"
    d = desc.upper()
    if re.search(r"\b(LF|LIN\.? FT|LINEAR FOOT)\b", d):
        return "USD/LF"
    if re.search(r"\b(SF|SQ\.? FT|SQUARE FOOT)\b", d):
        return "USD/SF"
    if re.search(r"\b(CY|CU\.? YD|CUBIC YARD)\b", d):
        return "USD/CY"
    if re.search(r"\b(GAL|GALLON)\b", d):
        return "USD/gallon"
    if re.search(r"\b(LB|POUND)\b", d):
        return "USD/lb"
    return "USD/EA"


def parse_catalog_csv(
    csv_text: str, *, schedule_code: str, period: Optional[str] = None,
    source_url: str = "",
) -> list[PricingSnapshot]:
    """Parse a GSA Advantage catalog CSV into snapshots.

    The CSV columns vary by schedule — we accept a permissive list of
    column-name aliases for SIN, item number, description, and price.
    """
    rows = list(csv.DictReader(io.StringIO(csv_text)))
    if not rows:
        return []

    sin_cols   = ["SIN", "Special Item Number", "SinNumber"]
    item_cols  = ["Manufacturer Part Number", "Mfr Part No", "Part Number",
                  "Item ID", "Vendor Part Number", "PartNumber"]
    desc_cols  = ["Description", "Product Description", "Item Description"]
    price_cols = ["Price", "GSA Price", "Net Price", "PRICE", "Unit Price"]

    def _first(row: dict, candidates: list[str]) -> str:
        for k in candidates:
            v = row.get(k)
            if v is None:
                continue
            v_str = str(v).strip()
            if v_str:
                return v_str
        return ""

    fetched_at = datetime.now(timezone.utc)
    period_str = period or fetched_at.strftime("%Y-%m-%d")

    snaps: list[PricingSnapshot] = []
    for row in rows:
        sin = _first(row, sin_cols)
        item = _first(row, item_cols)
        desc = _first(row, desc_cols)
        price_raw = _first(row, price_cols)
        if not price_raw:
            continue
        price_str = re.sub(r"[^0-9.\-]", "", price_raw)
        try:
            price = float(price_str)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        if not (item or desc):
            continue
        series_id = item or re.sub(r"\W+", "_", desc)[:60]
        unit = _parse_unit_from_description(desc)
        snaps.append(
            PricingSnapshot(
                source="gsa_schedule",
                series_id=f"{schedule_code}__{series_id}",
                label=(desc or item)[:200],
                unit=unit,
                value=price,
                region="US",
                csi_division=_infer_csi_division(sin),
                naics=None,
                period=period_str,
                fetched_at=fetched_at,
                license="U.S. Public Domain — General Services Administration",
                source_url=source_url
                    or f"https://www.gsaadvantage.gov/ref_text/{schedule_code}/",
                raw={"sin": sin, "item": item, "schedule_code": schedule_code},
            )
        )
    return snaps


def fetch_from_csv_file(
    path: Path, *, schedule_code: str, period: Optional[str] = None,
) -> list[PricingSnapshot]:
    p = Path(path)
    if not p.exists():
        LOG.warning("GSA catalog CSV not found: %s", p)
        return []
    return parse_catalog_csv(
        p.read_text(encoding="utf-8", errors="ignore"),
        schedule_code=schedule_code, period=period,
        source_url=f"file://{p}",
    )


class GSAScheduleSource(PricingSource):
    """Phase B partial — fetch is a no-op until auto-download lands."""

    name = "gsa_schedule"
    requires_env_vars: list[str] = []
    license_str = "U.S. Public Domain — General Services Administration"
    homepage_url = "https://www.gsaadvantage.gov/"

    SUPPORTED_SCHEDULES: tuple[str, ...] = ("56V", "03FAC", "23V")

    def default_series(self) -> list[str]:
        return []

    def fetch(self, series_ids: list[str], **filters: Any) -> list[PricingSnapshot]:
        # [Phase B — not yet implemented] — auto-download from
        # gsaadvantage.gov. Use `fetch_from_csv_file` for now.
        LOG.info(
            "GSAScheduleSource.fetch is a no-op until Phase B-full ships "
            "the GSA Advantage auto-downloader. Use fetch_from_csv_file(...) "
            "directly on a manually-downloaded CSV."
        )
        return []
