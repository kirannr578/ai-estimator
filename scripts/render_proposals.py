"""CLI: render a single bid's proposal markdown into the four-tier
artifact set, or all active workspaces at once.

Examples (PowerShell):

    # All four tiers, single bid (default tier=all)
    python scripts/render_proposals.py --bid bids/tamu-harrington-2025-06813

    # All four active bids, all tiers
    python scripts/render_proposals.py --all

    # Just the pitch deck for one bid
    python scripts/render_proposals.py --bid bids/cmd-post-ndi-W50S7626QA001 --tier pitch

    # Show `[USER TO FILL ...]` markers in red on the client outputs
    # (default behavior is to neutralize them to a fillable underline).
    python scripts/render_proposals.py --all --show-placeholders

Output (per bid, in `bids/<slug>/proposal/exports/`):

    <slug>-client-executive-summary.pdf      # tier=client
    <slug>-full-proposal.pdf                  # tier=client
    <slug>-internal-workbook.pdf              # tier=internal
    <slug>-pitch-deck.pptx                    # tier=pitch

The `--tier` flag selects which artifact(s) to produce (`client` builds
both client PDFs; `internal` builds the workbook; `pitch` builds the
PPTX; `all` is the default and builds all four).

Note: this is a breaking change vs. the previous `--format` /
`--pptx-style` flags. Old callers should migrate to `--tier`. Errors
on a single bid are logged but do not abort the run when `--all` is
used; partial output is better than none.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.proposal_renderer import (  # noqa: E402  - after sys.path mutation
    build_client_pdfs,
    build_internal_workbook,
    build_pitch_deck,
    load_firm_profile,
)


def _bid_dirs() -> list[Path]:
    """Return every directory under `bids/` that has a `proposal/` subfolder."""
    bids_root = ROOT / "bids"
    if not bids_root.is_dir():
        return []
    return sorted(
        p for p in bids_root.iterdir()
        if p.is_dir() and (p / "proposal").is_dir()
    )


def _render_one(
    bid_dir: Path,
    *,
    tier: str,
    show_placeholders: bool,
    firm_profile: dict,
    log: logging.Logger,
) -> dict[str, str]:
    """Render the requested tier(s) for a single bid. Returns a status
    map keyed by artifact tag ("executive_summary" / "full_proposal" /
    "internal_workbook" / "pitch_deck")."""
    bid_slug = bid_dir.name
    out_dir = bid_dir / "proposal" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    statuses: dict[str, str] = {}

    do_client = tier in {"client", "all"}
    do_internal = tier in {"internal", "all"}
    do_pitch = tier in {"pitch", "all"}

    if do_client:
        try:
            artifacts = build_client_pdfs(
                bid_dir,
                out_dir,
                firm_profile,
                show_placeholders=show_placeholders,
            )
            for key, path in artifacts.items():
                statuses[key] = (
                    f"OK ({path.stat().st_size:,} bytes) -> "
                    f"{path.relative_to(ROOT)}"
                )
        except Exception as exc:
            log.error("Client PDFs failed for %s: %s", bid_slug, exc)
            statuses["executive_summary"] = f"FAILED: {exc}"
            statuses["full_proposal"] = f"FAILED: {exc}"

    if do_internal:
        out_path = out_dir / f"{bid_slug}-internal-workbook.pdf"
        try:
            build_internal_workbook(bid_dir, out_path, firm_profile)
            statuses["internal_workbook"] = (
                f"OK ({out_path.stat().st_size:,} bytes) -> "
                f"{out_path.relative_to(ROOT)}"
            )
        except Exception as exc:
            log.error("Internal workbook failed for %s: %s", bid_slug, exc)
            statuses["internal_workbook"] = f"FAILED: {exc}"

    if do_pitch:
        out_path = out_dir / f"{bid_slug}-pitch-deck.pptx"
        try:
            build_pitch_deck(
                bid_dir,
                out_path,
                firm_profile,
                show_placeholders=show_placeholders,
            )
            statuses["pitch_deck"] = (
                f"OK ({out_path.stat().st_size:,} bytes) -> "
                f"{out_path.relative_to(ROOT)}"
            )
        except Exception as exc:
            log.error("Pitch deck failed for %s: %s", bid_slug, exc)
            statuses["pitch_deck"] = f"FAILED: {exc}"

    return statuses


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Render a bid's proposal markdown into the four-tier "
        "artifact set."
    )
    grp = p.add_mutually_exclusive_group(required=True)
    grp.add_argument(
        "--bid",
        type=Path,
        help="Path to a bid workspace, e.g. bids/tamu-harrington-2025-06813",
    )
    grp.add_argument(
        "--all",
        action="store_true",
        help="Render every workspace under `bids/` that has a `proposal/` subdir.",
    )
    p.add_argument(
        "--tier",
        choices=["client", "internal", "pitch", "all"],
        default="all",
        help=(
            "Which tier(s) to produce. `client` builds the executive-summary "
            "+ full-proposal PDFs; `internal` builds the workbook PDF; "
            "`pitch` builds the PPTX; `all` (default) builds all four."
        ),
    )
    p.add_argument(
        "--show-placeholders",
        action="store_true",
        help=(
            "Render `[USER TO FILL ...]` markers in red on the client-facing "
            "outputs (executive summary, full proposal, pitch deck). Default "
            "is to neutralize them to a fillable underline. The internal "
            "workbook always shows markers in red regardless."
        ),
    )
    p.add_argument(
        "--quiet", action="store_true", help="Less console chatter."
    )
    args = p.parse_args(argv)

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("render_proposals")

    firm_profile = load_firm_profile()

    if args.all:
        bid_dirs = _bid_dirs()
        if not bid_dirs:
            log.error("No bids/<slug>/proposal/ workspaces found.")
            return 2
    else:
        bid_dir = args.bid.resolve()
        if not (bid_dir / "proposal").is_dir():
            log.error("No proposal/ subdir under %s", bid_dir)
            return 2
        bid_dirs = [bid_dir]

    log.info(
        "Rendering %d workspace(s); tier=%s, show-placeholders=%s",
        len(bid_dirs),
        args.tier,
        args.show_placeholders,
    )

    any_failed = False
    for bid_dir in bid_dirs:
        log.info("=== %s ===", bid_dir.name)
        statuses = _render_one(
            bid_dir,
            tier=args.tier,
            show_placeholders=args.show_placeholders,
            firm_profile=firm_profile,
            log=log,
        )
        for key, status in statuses.items():
            print(f"  [{key:>20}] {status}")
            if status.startswith("FAILED"):
                any_failed = True

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
