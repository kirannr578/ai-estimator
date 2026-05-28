"""Refresh pricing snapshots from configured external sources.

Usage:
    python scripts/refresh_pricing.py
    python scripts/refresh_pricing.py --sources bls_ppi,fred,eia,bls_oews
    python scripts/refresh_pricing.py --sources bls_ppi --period 2026-04
    python scripts/refresh_pricing.py --davis-bacon-state TX --davis-bacon-county "Tom Green"

Env vars (loaded from `.env` if present):
    BLS_API_KEY   — optional; raises BLS daily quota to 500 from 25.
    FRED_API_KEY  — required for FRED source. (free at fred.stlouisfed.org)
    EIA_API_KEY   — required for EIA source.  (free at eia.gov/opendata)

On missing API keys the affected sources are skipped with a warning; the
runner continues. Exit code is 0 if at least one source returned at least
one snapshot, 1 otherwise. HTTP and parsing errors per source are caught
locally and never crash the runner.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

# python-dotenv is in requirements.txt; load .env quietly if present.
try:
    from dotenv import load_dotenv
    load_dotenv(REPO_ROOT / ".env", override=False)
except Exception:  # noqa: BLE001
    pass

from core.pricing.snapshots import write_snapshots  # noqa: E402
from core.pricing.sources.agc_cci import AGCCCISource  # noqa: E402
from core.pricing.sources.bls_oews import BLSOEWSSource  # noqa: E402
from core.pricing.sources.bls_ppi import BLSPPISource  # noqa: E402
from core.pricing.sources.davis_bacon import DavisBaconSource  # noqa: E402
from core.pricing.sources.eia import EIAFuelSource  # noqa: E402
from core.pricing.sources.enr_cci import ENRCCISource  # noqa: E402
from core.pricing.sources.fred import FREDSource  # noqa: E402
from core.pricing.sources.hd_pro import HomeDepotProSource  # noqa: E402
from core.pricing.sources.lowes_pro import LowesProSource  # noqa: E402
from core.pricing.sources.nahb_construction_cost import (  # noqa: E402
    NAHBCostOfConstructingAHomeSource,
)
from core.pricing.sources.turner_cci import TurnerCCISource  # noqa: E402
from core.pricing.sources.tx_smartbuy_awards import (  # noqa: E402
    TXSmartBuyAwardsSource,
)

LOG = logging.getLogger("refresh_pricing")

ALL_SOURCES = {
    "bls_ppi": BLSPPISource,
    "bls_oews": BLSOEWSSource,
    "fred": FREDSource,
    "eia": EIAFuelSource,
    "davis_bacon": DavisBaconSource,
    # Phase C — Construction Cost Index macro escalators. Not in the
    # default --sources list because they scrape HTML and are more fragile
    # than the Phase A / B JSON APIs; opt in explicitly with
    # `--sources enr_cci,agc_cci,turner_cci,nahb_construction_cost` or
    # via `--phase c`.
    "enr_cci": ENRCCISource,
    "agc_cci": AGCCCISource,
    "turner_cci": TurnerCCISource,
    "nahb_construction_cost": NAHBCostOfConstructingAHomeSource,
    # Phase C — TX SmartBuy / ESBD historical-awards scraper.
    # Competitive intel (vendor + amount + NAICS + period per award),
    # complementing the macro CCI/PPI escalators above. Same fragility
    # posture as the CCI adapters (HTML scrape, not JSON API) — opt in
    # explicitly via `--sources tx_smartbuy_awards` or `--phase c`.
    "tx_smartbuy_awards": TXSmartBuyAwardsSource,
    # Phase C closure — Home Depot Pro + Lowe's Pro catalog scrapers.
    # Public retail catalog prices only. Both retailers serve product
    # pages behind Akamai bot protection — see the per-adapter module
    # docstring for the structural fragility, and the playbook section
    # "Home Depot Pro / Lowe's Pro retail catalog" for the license
    # caveat. Default starter SKU lists live in ``HD_PRO_STARTER_SKUS``
    # / ``LOWES_PRO_STARTER_SKUS`` below so the per-bid SKU policy is
    # greppable from the CLI side. Opt in explicitly via
    # ``--sources hd_pro,lowes_pro`` or ``--phase c``.
    "hd_pro": HomeDepotProSource,
    "lowes_pro": LowesProSource,
}

# Source bundles by phase, used by the `--phase` shortcut flag.
PHASE_SOURCES: dict[str, list[str]] = {
    "a": ["bls_ppi", "bls_oews", "fred", "eia"],
    "b": ["davis_bacon"],
    "c": [
        "enr_cci", "agc_cci", "turner_cci", "nahb_construction_cost",
        "tx_smartbuy_awards", "hd_pro", "lowes_pro",
    ],
}

# Default recent-awards batch size for the TX SmartBuy scraper when
# invoked via the refresh script (no explicit --series ids). Mirrors
# ``TXSmartBuyAwardsSource.DEFAULT_RECENT_LIMIT`` per the brief; kept
# here as a module constant so it is greppable from the CLI side.
TX_SMARTBUY_REFRESH_LIMIT = 50

# Starter SKU lists for the HD Pro / Lowe's Pro catalog scrapers.
# Curated 2026-05-28 from the most-frequently-quoted line items across
# recent BPC bids. These are deliberately broad — door hardware, paint,
# drywall screws, framing lumber, plywood, fasteners, joint compound,
# gypsum board, roofing felt — to give a Phase C closure a meaningful
# spot-check surface area without committing to per-bid SKU curation
# (which is the right long-term home for these lists).
#
# Where future SKU lists SHOULD be sourced from
# ---------------------------------------------
# - **Per-bid CSV** under ``bids/<slug>/catalog-skus.csv`` — the
#   estimator drops a printed Pro-counter quote into the bid workspace
#   and the refresh runner picks the bid-specific list when running
#   inside the bid context. NOT YET IMPLEMENTED — `--bid <slug>` flag
#   is the natural extension.
# - **Per-firm config** under ``firm/catalog/hd_pro_skus.csv`` and
#   ``firm/catalog/lowes_pro_skus.csv`` — a curated list of "always
#   refresh these" SKUs that the firm tracks across all bids. NOT YET
#   IMPLEMENTED.
# - **Per-CSI mapping** under ``firm/catalog/csi_to_skus.json`` — links
#   each CSI section (e.g. ``08 71 00`` Door Hardware) to a list of
#   exemplar SKUs, so a bid takeoff that touches a CSI section
#   automatically pulls fresh prices for the exemplars. NOT YET
#   IMPLEMENTED — depends on the per-CSI keyword catalog in
#   ``core/pricing/escalation.py`` being externalized.
#
# Until those are built, this module-level constant is the source of
# truth and is overridable by passing an explicit list via
# ``HomeDepotProSource(sku_list=[...])`` / ``LowesProSource(...)``.
HD_PRO_STARTER_SKUS: list[str] = [
    "100120362",   # 3/4 in. PVC pipe — plumbing rough-in (CSI 22 11)
    "100133104",   # 2x4x8 SPF framing lumber — rough carpentry (CSI 06 10)
    "202079922",   # drywall screws, 1 lb box — fasteners (CSI 06 09)
    "202519319",   # 1/2 in. sheathing plywood — sheathing (CSI 06 16)
    "203083697",   # interior latex paint, 1 gal — paints (CSI 09 91)
    "100195918",   # passage door knob — door hardware (CSI 08 71)
    "203070515",   # exterior door hinge — door hardware (CSI 08 71)
    "100129040",   # 5 gal joint compound — gypsum board finish (CSI 09 29)
    "200032100",   # 4x8 gypsum board — gypsum board (CSI 09 29)
    "100107516",   # 30 lb roofing felt — underlayment (CSI 07 31)
]

LOWES_PRO_STARTER_SKUS: list[str] = [
    "1099113",   # 3/4 in. PVC pipe — plumbing rough-in (CSI 22 11)
    "12533",     # 2x4x8 SPF framing lumber — rough carpentry (CSI 06 10)
    "73268",     # drywall screws, 1 lb box — fasteners (CSI 06 09)
    "12174",     # 1/2 in. sheathing plywood — sheathing (CSI 06 16)
    "1003356",   # interior latex paint, 1 gal — paints (CSI 09 91)
    "47546",     # passage door knob — door hardware (CSI 08 71)
    "303116",    # exterior door hinge — door hardware (CSI 08 71)
    "23005",     # 5 gal joint compound — gypsum board finish (CSI 09 29)
    "10243",     # 4x8 gypsum board — gypsum board (CSI 09 29)
    "12553",     # 30 lb roofing felt — underlayment (CSI 07 31)
]


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Refresh BPC pricing-data snapshots from free public sources.",
    )
    p.add_argument(
        "--sources",
        default="bls_ppi,fred,eia,bls_oews",
        help="Comma-separated list of sources to refresh. "
             f"Available: {','.join(sorted(ALL_SOURCES))}. "
             "Phase C CCI sources (enr_cci / agc_cci / turner_cci) are "
             "excluded from the default because they scrape HTML and are "
             "more fragile than the Phase A / B JSON APIs; opt in "
             "explicitly via --sources or --phase c.",
    )
    p.add_argument(
        "--phase",
        default=None,
        choices=sorted(PHASE_SOURCES.keys()),
        help="Shortcut for refreshing every source in a given phase "
             "bundle (a = BLS PPI/OEWS + FRED + EIA; b = Davis-Bacon; "
             "c = ENR/AGC/Turner CCI + NAHB cost-of-constructing-a-home "
             "+ TX SmartBuy historical-awards + HD Pro / Lowe's Pro "
             "catalogs). "
             "Overrides --sources when given.",
    )
    p.add_argument(
        "--period",
        default=None,
        help="Optional reporting period (e.g. 2026-04). "
             "If omitted, each source pulls its latest available.",
    )
    p.add_argument(
        "--davis-bacon-state", default=None,
        help="State abbreviation for a Davis-Bacon project lookup (e.g. 'TX').",
    )
    p.add_argument(
        "--davis-bacon-county", default=None,
        help="County name for a Davis-Bacon project lookup (e.g. 'Tom Green').",
    )
    p.add_argument(
        "--davis-bacon-project-type", default="Building",
        help="DOL construction type (Building / Heavy / Highway / Residential).",
    )
    p.add_argument(
        "--verbose", "-v", action="count", default=0,
        help="Increase logging verbosity.",
    )
    return p.parse_args(argv)


def _configure_logging(verbose: int) -> None:
    level = logging.WARNING
    if verbose == 1:
        level = logging.INFO
    elif verbose >= 2:
        level = logging.DEBUG
    logging.basicConfig(
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        level=level,
    )


def _run_source(
    name: str,
    *,
    period: Optional[str],
    davis_bacon_state: Optional[str],
    davis_bacon_county: Optional[str],
    davis_bacon_project_type: str,
) -> tuple[int, int, str]:
    """Run one source. Returns (snapshots_written, errors, status_msg)."""
    cls = ALL_SOURCES[name]
    # The HD Pro / Lowe's Pro catalog adapters take a starter SKU list
    # at construction time; everyone else takes no kwargs. Keeping the
    # construction site greppable here so the per-source policy is
    # discoverable from the CLI entry point rather than buried inside
    # the adapter module's DEFAULT_SKUS constant.
    if name == "hd_pro":
        src = cls(sku_list=HD_PRO_STARTER_SKUS)
    elif name == "lowes_pro":
        src = cls(sku_list=LOWES_PRO_STARTER_SKUS)
    else:
        src = cls()
    if not src.is_ready():
        missing = ",".join(src.missing_env())
        msg = f"[{name}] missing env: {missing} — skipped"
        LOG.warning(msg)
        src.close()
        return (0, 0, msg)

    try:
        if name == "davis_bacon":
            if not davis_bacon_state:
                msg = f"[{name}] needs --davis-bacon-state — skipped"
                LOG.warning(msg)
                return (0, 0, msg)
            snaps = src.fetch_for_project(
                state=davis_bacon_state,
                county=davis_bacon_county,
                project_type=davis_bacon_project_type,
            )
        elif name == "tx_smartbuy_awards":
            # ESBD is awards-driven, not series-driven: the listing-page
            # scan finds the most-recent N awarded solicitations and
            # emits one snapshot per (solicitation, vendor) pair.
            snaps = src.fetch([], limit=TX_SMARTBUY_REFRESH_LIMIT)
        elif name in ("hd_pro", "lowes_pro"):
            # Catalog scrapers iterate the configured starter SKU list.
            # Per-SKU HTTP errors and Akamai/CAPTCHA intercepts are
            # swallowed inside ``fetch()`` and surface as "0 snapshots
            # returned" + warnings in the per-SKU log lines, mirroring
            # the structural fragility documented in the playbook.
            snaps = src.fetch([])
        else:
            series = src.default_series()
            filters: dict[str, str] = {}
            if period and len(period) >= 4 and period[:4].isdigit():
                filters["startyear"] = period[:4]
                filters["endyear"] = period[:4]
            snaps = src.fetch(series, **filters)
    except Exception as exc:  # noqa: BLE001
        msg = f"[{name}] fetch error: {exc} — skipped"
        LOG.warning(msg)
        src.close()
        return (0, 1, msg)
    finally:
        # finally we close even on success
        pass

    src.close()

    if not snaps:
        msg = f"[{name}] 0 snapshots returned"
        LOG.warning(msg)
        return (0, 0, msg)

    try:
        write_snapshots(snaps)
    except Exception as exc:  # noqa: BLE001
        msg = f"[{name}] persistence error: {exc}"
        LOG.error(msg)
        return (0, 1, msg)

    msg = f"[{name}] {len(snaps)} snapshots fetched + persisted"
    LOG.info(msg)
    return (len(snaps), 0, msg)


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    _configure_logging(args.verbose)

    if args.phase:
        requested = list(PHASE_SOURCES[args.phase])
    else:
        requested = [s.strip() for s in args.sources.split(",") if s.strip()]
    unknown = [s for s in requested if s not in ALL_SOURCES]
    if unknown:
        print(f"ERROR: unknown sources: {unknown}", file=sys.stderr)
        print(f"Available: {sorted(ALL_SOURCES)}", file=sys.stderr)
        return 2

    summary: list[str] = []
    total_written = 0
    for name in requested:
        written, errors, msg = _run_source(
            name,
            period=args.period,
            davis_bacon_state=args.davis_bacon_state,
            davis_bacon_county=args.davis_bacon_county,
            davis_bacon_project_type=args.davis_bacon_project_type,
        )
        total_written += written
        summary.append(msg)

    print("\n=== Pricing-refresh summary ===")
    for line in summary:
        print(line)
    print(f"Total snapshots written: {total_written}")

    return 0 if total_written > 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
