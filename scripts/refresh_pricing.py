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
from core.pricing.sources.bls_oews import BLSOEWSSource  # noqa: E402
from core.pricing.sources.bls_ppi import BLSPPISource  # noqa: E402
from core.pricing.sources.davis_bacon import DavisBaconSource  # noqa: E402
from core.pricing.sources.eia import EIAFuelSource  # noqa: E402
from core.pricing.sources.fred import FREDSource  # noqa: E402

LOG = logging.getLogger("refresh_pricing")

ALL_SOURCES = {
    "bls_ppi": BLSPPISource,
    "bls_oews": BLSOEWSSource,
    "fred": FREDSource,
    "eia": EIAFuelSource,
    "davis_bacon": DavisBaconSource,
}


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Refresh BPC pricing-data snapshots from free public sources.",
    )
    p.add_argument(
        "--sources",
        default="bls_ppi,fred,eia,bls_oews",
        help="Comma-separated list of sources to refresh. "
             f"Available: {','.join(sorted(ALL_SOURCES))}.",
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
