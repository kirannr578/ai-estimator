"""CLI: render a single bid's proposal markdown to PDF and/or PPTX, or all
of them at once.

Examples (PowerShell):

    # One bid, both formats (default)
    python scripts/render_proposals.py --bid bids/tamu-harrington-2025-06813

    # All four active bids, both formats
    python scripts/render_proposals.py --all

    # PDF only, single bid
    python scripts/render_proposals.py --bid bids/cmd-post-ndi-W50S7626QA001 --format pdf

    # Full-walkthrough PPTX (one slide per H1) instead of pitch deck
    python scripts/render_proposals.py --bid bids/usfws-san-marcos-140FC126R0017 --pptx-style full

Output:

    bids/<slug>/proposal/exports/proposal-full.pdf
    bids/<slug>/proposal/exports/proposal-pitch.pptx        # style=pitch_deck
    bids/<slug>/proposal/exports/proposal-full.pptx         # style=full

Errors on a single bid are logged but do not abort the run when `--all` is
used; partial output is better than none.
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Make the project root importable when running `python scripts/...`.
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from core.proposal_renderer import (  # noqa: E402  - after sys.path mutation
    build_proposal_pdf,
    build_proposal_pptx,
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
    fmt: str,
    pptx_style: str,
    firm_profile: dict,
    log: logging.Logger,
) -> dict[str, str]:
    """Render PDF / PPTX for a single bid. Returns map of artifact name → status."""
    out_dir = bid_dir / "proposal" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)
    artifacts: dict[str, str] = {}

    do_pdf = fmt in {"pdf", "both"}
    do_pptx = fmt in {"pptx", "both"}

    if do_pdf:
        pdf_out = out_dir / "proposal-full.pdf"
        try:
            build_proposal_pdf(bid_dir, pdf_out, firm_profile)
            artifacts["pdf"] = (
                f"OK ({pdf_out.stat().st_size:,} bytes) -> {pdf_out.relative_to(ROOT)}"
            )
        except Exception as exc:
            log.error("PDF render failed for %s: %s", bid_dir.name, exc)
            artifacts["pdf"] = f"FAILED: {exc}"

    if do_pptx:
        pptx_name = (
            "proposal-pitch.pptx" if pptx_style == "pitch_deck" else "proposal-full.pptx"
        )
        pptx_out = out_dir / pptx_name
        try:
            build_proposal_pptx(
                bid_dir, pptx_out, firm_profile, style=pptx_style,
            )
            artifacts["pptx"] = (
                f"OK ({pptx_out.stat().st_size:,} bytes) -> "
                f"{pptx_out.relative_to(ROOT)}"
            )
        except Exception as exc:
            log.error("PPTX render failed for %s: %s", bid_dir.name, exc)
            artifacts["pptx"] = f"FAILED: {exc}"

    return artifacts


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(
        description="Render a bid's proposal markdown to PDF + PPTX deliverables."
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
        "--format",
        choices=["pdf", "pptx", "both"],
        default="both",
        help="Which artifact(s) to produce (default: both).",
    )
    p.add_argument(
        "--pptx-style",
        choices=["pitch_deck", "full"],
        default="pitch_deck",
        help="`pitch_deck` (default, 10-15 distilled slides) or `full` (one slide per H1).",
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

    log.info("Rendering %d workspace(s); format=%s, pptx-style=%s",
             len(bid_dirs), args.format, args.pptx_style)

    any_failed = False
    for bid_dir in bid_dirs:
        log.info("=== %s ===", bid_dir.name)
        artifacts = _render_one(
            bid_dir,
            fmt=args.format,
            pptx_style=args.pptx_style,
            firm_profile=firm_profile,
            log=log,
        )
        for kind, status in artifacts.items():
            print(f"  [{kind:4}] {status}")
            if status.startswith("FAILED"):
                any_failed = True

    return 1 if any_failed else 0


if __name__ == "__main__":
    sys.exit(main())
