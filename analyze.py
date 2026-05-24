"""Headless / CLI runner for the Construction Plan Estimator.

Use this when you have a folder full of PDFs and don't want to drag-and-drop
into the Streamlit UI, or when you want to script a batch run.

Examples (PowerShell):

    # Analyze every PDF under a folder, recursively
    python analyze.py "C:/path/to/GMP#003-Permit-Set" --recursive --out exports/run1

    # Just the bid packages folder, with a 5-PDF limit (cheap dry run)
    python analyze.py "C:/.../02-Bid-Packages-(Scope-Specific)" --limit 5 --out exports/dryrun

    # Force a specific provider / model
    python analyze.py "..." --provider openai --model gpt-4o --out exports/openai_run

The runner writes:
    <out>/estimate.xlsx   - full Excel workbook
    <out>/estimate.json   - everything as JSON
    <out>/run_log.txt     - per-document elapsed time + warnings
"""

from __future__ import annotations

import argparse
import logging
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

from dotenv import load_dotenv

from core.estimator import CostDatabase, price_takeoff
from core.exporter import export_estimate_json, export_estimate_xlsx, save_to_disk
from core.extractors import extract_bundle, extract_sheet
from core.llm_client import LLMClient
from core.pdf_processor import process_pdfs
from core.schemas import SheetExtraction
from core.sheet_classifier import classify_sheet
from core.takeoff import reconcile

load_dotenv()

import json  # noqa: E402

CONFIG_DIR = Path(__file__).resolve().parent / "config"


def _gather_pdfs(target: Path, recursive: bool, include_drawings: bool) -> list[Path]:
    if target.is_file() and target.suffix.lower() == ".pdf":
        return [target]
    if not target.is_dir():
        raise SystemExit(f"Not a PDF or directory: {target}")
    pattern = "**/*.pdf" if recursive else "*.pdf"
    pdfs = sorted(p for p in target.glob(pattern) if p.is_file())
    if not include_drawings:
        # Heuristic: very large PDFs (>5 MB) are usually drawing sets.
        pdfs = [p for p in pdfs if p.stat().st_size <= 5 * 1024 * 1024]
    return pdfs


def _process_sheet(args):
    sheet, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    sheet = classify_sheet(sheet, llm)
    return sheet, extract_sheet(sheet, llm)


def _process_bundle(args):
    bundle, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    return bundle, extract_bundle(bundle, llm)


_CLIENT_QUOTE_CONFIG = CONFIG_DIR / "client_quote.json"


def _build_client_pdf(
    estimate,
    project,
    csi_titles: dict,
    out_dir: Path,
    log: logging.Logger,
) -> str:
    """Best-effort client-quote PDF render. Returns a log-line summary.

    Never raises: a missing optional dep, missing config, or render error
    must not break the primary Excel/JSON deliverable.
    """
    try:
        from core.exporter_pdf import build_quote_pdf
        from core.schemas import QuoteConfig
    except ImportError as exc:
        msg = (
            f"client-pdf skipped: reportlab is not installed ({exc}). "
            f"Install it with: pip install 'reportlab>=4.0,<5.0'"
        )
        log.warning(msg)
        return msg

    if _CLIENT_QUOTE_CONFIG.is_file():
        try:
            raw = json.loads(_CLIENT_QUOTE_CONFIG.read_text(encoding="utf-8"))
            cfg = QuoteConfig.model_validate(raw)
        except Exception as exc:
            msg = (
                f"client-pdf: config/client_quote.json failed to parse ({exc}); "
                f"falling back to skeleton defaults."
            )
            log.warning(msg)
            cfg = QuoteConfig()
    else:
        msg = (
            f"client-pdf: {_CLIENT_QUOTE_CONFIG.name} not found; "
            f"using built-in skeleton defaults."
        )
        log.warning(msg)
        cfg = QuoteConfig()

    out_pdf = out_dir / "quote.pdf"
    try:
        build_quote_pdf(estimate, project, cfg, out_pdf, csi_titles=csi_titles)
    except Exception as exc:
        msg = f"client-pdf: render failed ({exc}); Excel/JSON output is unaffected."
        log.error(msg)
        return msg

    return f"client-pdf written: {out_pdf} ({out_pdf.stat().st_size:,} bytes)"


_REPO_ROOT = Path(__file__).resolve().parent


def _render_bid_proposal(bid_slug: str, log: logging.Logger) -> str:
    """Render the PDF + pitch-deck PPTX for `bids/<bid_slug>/proposal/`.

    Independent of the client-quote PDF flow. Failures are logged and
    returned as a single-line summary; they never break the primary
    analyze run.
    """
    bid_dir = _REPO_ROOT / "bids" / bid_slug
    if not (bid_dir / "proposal").is_dir():
        msg = f"render-proposal: no proposal/ subdir under bids/{bid_slug}; skipped."
        log.error(msg)
        return msg

    try:
        from core.proposal_renderer import (
            build_proposal_pdf,
            build_proposal_pptx,
            load_firm_profile,
        )
    except ImportError as exc:
        msg = (
            f"render-proposal skipped: dependency import failed ({exc}). "
            "Install: pip install markdown xhtml2pdf python-pptx pypdf."
        )
        log.warning(msg)
        return msg

    try:
        firm_profile = load_firm_profile()
    except Exception as exc:
        msg = f"render-proposal: failed to load firm/firm-profile.json: {exc}"
        log.error(msg)
        return msg

    out_dir = bid_dir / "proposal" / "exports"
    out_dir.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    pdf_out = out_dir / "proposal-full.pdf"
    try:
        build_proposal_pdf(bid_dir, pdf_out, firm_profile)
        parts.append(f"PDF {pdf_out} ({pdf_out.stat().st_size:,} bytes)")
    except Exception as exc:
        log.error("render-proposal: PDF render failed: %s", exc)
        parts.append(f"PDF FAILED: {exc}")

    pptx_out = out_dir / "proposal-pitch.pptx"
    try:
        build_proposal_pptx(bid_dir, pptx_out, firm_profile, style="pitch_deck")
        parts.append(f"PPTX {pptx_out} ({pptx_out.stat().st_size:,} bytes)")
    except Exception as exc:
        log.error("render-proposal: PPTX render failed: %s", exc)
        parts.append(f"PPTX FAILED: {exc}")

    return f"render-proposal[{bid_slug}]: " + "; ".join(parts)


def main() -> int:
    p = argparse.ArgumentParser(description="Run the Construction Plan Estimator on a folder of PDFs.")
    p.add_argument("path", type=Path, help="A PDF file or a folder containing PDFs.")
    p.add_argument("--recursive", action="store_true", help="Recurse into subfolders.")
    p.add_argument("--limit", type=int, default=0, help="Process at most N PDFs (0 = no limit).")
    p.add_argument("--out", type=Path, default=Path("exports/cli_run"), help="Output directory.")
    p.add_argument("--provider", choices=["anthropic", "openai"], default=None,
                   help="Force LLM provider (default: auto-detect from env).")
    p.add_argument("--model", default=None, help="Override the model name.")
    p.add_argument("--dpi", type=int, default=200, help="Render DPI for drawing pages (default 200).")
    p.add_argument("--workers", type=int, default=4, help="Parallel workers (default 4).")
    p.add_argument("--region", type=float, default=1.00, help="Region cost multiplier (default 1.00).")
    p.add_argument("--contingency", type=float, default=10.0, help="Contingency %% (default 10).")
    p.add_argument("--overhead",    type=float, default=10.0, help="Overhead %% (default 10).")
    p.add_argument("--profit",      type=float, default=5.0,  help="Profit %% (default 5).")
    p.add_argument("--project-name", default="CLI Run", help="Project name for the estimate header.")
    p.add_argument("--no-drawings", action="store_true",
                   help="Skip large PDFs (>5 MB) - cheap text-only run.")
    p.add_argument("--client-pdf", action="store_true",
                   help="Also render a client-ready quote.pdf using config/client_quote.json.")
    p.add_argument(
        "--render-proposal",
        metavar="BID_SLUG",
        default=None,
        help=(
            "After analyze finishes, render the proposal package at "
            "bids/<BID_SLUG>/proposal/ to a PDF + pitch-deck PPTX. Independent of "
            "--client-pdf (which renders the client-quote PDF for the analyze run)."
        ),
    )
    p.add_argument(
        "--cost-db",
        choices=["cwicr", "seed", "both"],
        default="both",
        help=(
            "Which cost source(s) to use. 'cwicr' = CWICR open dataset only "
            "(no seed fallback). 'seed' = the bundled 47-entry seed cost DB "
            "only. 'both' (default) = try CWICR first, fall back to seed. "
            "The env var CWICR_DISABLED=true overrides to seed-only."
        ),
    )
    p.add_argument("--quiet", action="store_true", help="Less console chatter.")
    args = p.parse_args()

    logging.basicConfig(
        level=logging.WARNING if args.quiet else logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    log = logging.getLogger("analyze")

    pdf_paths = _gather_pdfs(args.path, args.recursive, include_drawings=not args.no_drawings)
    if args.limit > 0:
        pdf_paths = pdf_paths[: args.limit]
    if not pdf_paths:
        log.error("No PDFs found.")
        return 2

    log.info("Found %d PDF(s) to analyze.", len(pdf_paths))

    args.out.mkdir(parents=True, exist_ok=True)
    cache_dir = args.out / "renders"

    t0 = time.time()
    sheets, bundles = process_pdfs(pdf_paths, cache_dir=cache_dir, dpi=args.dpi)
    log.info("Split into %d drawing sheets and %d text documents in %.1fs.",
             len(sheets), len(bundles), time.time() - t0)

    if not sheets and not bundles:
        log.error("Nothing to analyze after splitting (PDFs were empty or filtered out).")
        return 3

    extractions: list[SheetExtraction] = []
    log_lines: list[str] = []

    total_units = len(sheets) + len(bundles)
    completed = 0
    t1 = time.time()
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {}
        for s in sheets:
            futures[pool.submit(_process_sheet, (s, args.provider, args.model))] = ("sheet", s)
        for b in bundles:
            futures[pool.submit(_process_bundle, (b, args.provider, args.model))] = ("bundle", b)

        for fut in as_completed(futures):
            kind, src = futures[fut]
            sid = getattr(src, "sheet_id", None) or getattr(src, "pdf_name", "unknown")
            unit_t0 = time.time()
            try:
                if kind == "sheet":
                    sheet, ex = fut.result()
                else:
                    _, ex = fut.result()
            except Exception as exc:
                ex = SheetExtraction(sheet_id=sid, summary=f"Pipeline error: {exc}",
                                     warnings=[f"pipeline error: {exc}"])
            extractions.append(ex)
            completed += 1
            elapsed = time.time() - unit_t0
            line = f"[{completed:>3}/{total_units}] {kind:6s} {sid}  ({elapsed:5.1f}s)"
            if ex.warnings:
                line += f"  WARN: {ex.warnings[0]}"
            log_lines.append(line)
            if not args.quiet:
                print(line)

    log.info("All extractions done in %.1fs.", time.time() - t1)

    project = reconcile(extractions)
    final_name = project.project_info.name or args.project_name

    # --cost-db gates which lookup layers are active. CWICR_DISABLED env
    # overrides --cost-db=cwicr / both to seed-only, mirroring the spec.
    use_cwicr = args.cost_db in {"cwicr", "both"}
    use_seed = args.cost_db in {"seed", "both"}
    estimate = price_takeoff(
        project,
        project_name=final_name,
        region_multiplier=args.region,
        contingency_pct=args.contingency,
        overhead_pct=args.overhead,
        profit_pct=args.profit,
        cost_db=CostDatabase() if use_seed else None,
        use_cwicr=use_cwicr,
        use_seed=use_seed,
    )

    csi_titles = json.loads((CONFIG_DIR / "csi_divisions.json").read_text(encoding="utf-8"))

    xlsx_bytes = export_estimate_xlsx(estimate, project, csi_titles, extractions)
    save_to_disk(xlsx_bytes, args.out / "estimate.xlsx")
    json_str = export_estimate_json(estimate, project)
    save_to_disk(json_str, args.out / "estimate.json")

    if args.client_pdf:
        pdf_msg = _build_client_pdf(estimate, project, csi_titles, args.out, log)
        if pdf_msg:
            log_lines.append(pdf_msg)

    if args.render_proposal:
        proposal_msg = _render_bid_proposal(args.render_proposal, log)
        log_lines.append(proposal_msg)

    save_to_disk("\n".join(log_lines) + "\n", args.out / "run_log.txt")

    print("")
    print(f"Project:         {final_name}")
    if project.project_info.number:
        print(f"Project number:  {project.project_info.number}")
    if project.project_info.location:
        print(f"Location:        {project.project_info.location}")
    print(f"Drawing sheets:  {len(sheets)}")
    print(f"Bid packages:    {len(project.bid_packages)}")
    print(f"Line items:      {len(estimate.line_items)}")
    print(f"Subtotal:        ${estimate.subtotal:,.2f}")
    print(f"Grand total:     ${estimate.grand_total:,.2f}")
    print(f"Output written:  {args.out.resolve()}")
    if args.client_pdf:
        quote_pdf = args.out / "quote.pdf"
        if quote_pdf.is_file():
            print(f"Client quote:    {quote_pdf.resolve()}")
        else:
            print("Client quote:    (skipped — see run_log.txt)")
    if args.render_proposal:
        bid_dir = _REPO_ROOT / "bids" / args.render_proposal / "proposal" / "exports"
        if bid_dir.is_dir():
            print(f"Proposal pkg:    {bid_dir.resolve()}")
        else:
            print("Proposal pkg:    (skipped — see run_log.txt)")
    if project.warnings:
        print(f"Warnings:        {len(project.warnings)} (see Warnings sheet in Excel)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
