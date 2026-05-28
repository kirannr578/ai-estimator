"""Streamlit UI for the Construction Plan Estimator.

Run with:

    streamlit run app.py

Workflow:
  1. Upload one or more PDFs (drag and drop in sidebar).
  2. Configure provider, region multiplier, OH&P, contingency.
  3. Click 'Analyze plan set' - the app:
     - splits each PDF into sheets and renders them,
     - classifies each sheet (discipline + type),
     - extracts structured takeoffs in parallel,
     - reconciles cross-sheet duplicates,
     - prices everything against the cost database.
  4. Review results across tabs (Estimate, Sheets, Rooms, Doors/Windows,
     Specs, Raw takeoffs, Warnings).
  5. Edit unit costs / quantities / OH&P live and re-price.
  6. Download Excel and JSON.
"""

from __future__ import annotations

import csv
import io
import json
import logging
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd
import streamlit as st
from dotenv import load_dotenv

from core.estimator import (
    MANUAL_OVERRIDE_NOTE_PREFIX,
    CostDatabase,
    apply_manual_override,
    price_takeoff,
)
from core.exporter import export_estimate_json, export_estimate_xlsx
from core.extractors import extract_bundle, extract_sheet
from core.llm_client import LLMClient
from core.pdf_processor import DocumentBundle, process_pdfs
from core.pricing.batch_override import (
    BatchMatchResult,
    BatchMatchStatus,
    BatchOverridePlan,
    apply_batch_plan,
    export_match_plan_csv,
    format_batch_operator_note,
    match_cost_lines,
    parse_vendor_csv,
)
from core.schemas import (
    ClientInfo,
    CompanyInfo,
    CostLine,
    CostSourceTier,
    Estimate,
    PaymentMilestone,
    PaymentSchedule,
    QuoteConfig,
    QuoteMeta,
    Sheet,
    SheetExtraction,
)


# Phase T7 — display labels for the catalog-completeness tiers, mirroring
# ``core.exporter._TIER_LABELS`` so the UI and Excel export agree exactly
# on user-visible strings.
_T7_TIER_LABELS: dict[CostSourceTier, str] = {
    CostSourceTier.EXACT_MATCH: "Exact Match",
    CostSourceTier.CATEGORY_MATCH: "Category Match",
    CostSourceTier.INTERPOLATED: "Interpolated",
    CostSourceTier.PARAMETRIC: "Parametric",
    CostSourceTier.MANUAL_OVERRIDE: "Manual Override",
    CostSourceTier.MISSING: "Missing",
}


def _t7_tier_label(li) -> str:
    """Resolve the display label for a CostLine's ``cost_source_tier``."""
    tier = getattr(li, "cost_source_tier", CostSourceTier.EXACT_MATCH)
    if isinstance(tier, CostSourceTier):
        return _T7_TIER_LABELS[tier]
    try:
        return _T7_TIER_LABELS[CostSourceTier(tier)]
    except Exception:
        return str(tier)


# ---------------------------------------------------------------------------
# Phase T6.2 — Operator override UI helpers (pure functions, easy to test)
# ---------------------------------------------------------------------------
#
# The helpers below back the "Operator price overrides" affordance in the
# Estimate tab. They are intentionally pure (no Streamlit calls, no
# session-state reads) so the test suite can exercise them without
# spinning up an ``AppTest`` harness — Streamlit's testing facility does
# not yet cleanly support form-submit round-trips against a heavy app
# like this one. The Streamlit form below is a thin wrapper that
# (1) collects the operator's input, (2) hands it to ``_apply_operator_override``,
# and (3) renders the result.

# Sort order for the line-selector dropdown. MANUAL_OVERRIDE first so an
# operator who already touched a row can find it immediately, then the
# remaining tiers in descending catalog-completeness quality (EXACT first,
# MISSING last). Any unknown tier falls through to the bottom.
_TIER_SORT_ORDER: dict[CostSourceTier, int] = {
    CostSourceTier.MANUAL_OVERRIDE: 0,
    CostSourceTier.EXACT_MATCH: 1,
    CostSourceTier.CATEGORY_MATCH: 2,
    CostSourceTier.INTERPOLATED: 3,
    CostSourceTier.PARAMETRIC: 4,
    CostSourceTier.MISSING: 5,
}


def _format_operator_note(
    vendor: str | None,
    quote_ref: str | None,
    free_text: str | None,
) -> str | None:
    """Combine vendor / quote-ref / free-text into one operator-note string.

    Format::

        [vendor: <vendor>] [quote-ref: <quote_ref>] <free_text>

    Empty / whitespace-only fields are skipped. If all three are empty
    the function returns ``None`` so the caller can pass it straight to
    ``apply_manual_override`` (which treats ``None`` as "no note" but
    still stamps the ``MANUAL_OVERRIDE`` sentinel).
    """
    parts: list[str] = []
    v = (vendor or "").strip()
    q = (quote_ref or "").strip()
    t = (free_text or "").strip()
    if v:
        parts.append(f"[vendor: {v}]")
    if q:
        parts.append(f"[quote-ref: {q}]")
    if t:
        parts.append(t)
    if not parts:
        return None
    return " ".join(parts)


def _select_line_label(idx: int, line: CostLine) -> str:
    """Human-readable label for the override line-selector dropdown.

    Format: ``#<idx> | <description, truncated> | $<unit_cost>/<unit> | <tier>``.

    The leading ``#<idx>`` is the stable line identifier the override
    pass uses (CostLine has no ``entity_id`` field per the T7 schema),
    so the operator can always disambiguate two visually-similar rows
    by their position.
    """
    desc = (line.description or "").strip() or "(no description)"
    if len(desc) > 60:
        desc = desc[:57] + "..."
    tier_label = _t7_tier_label(line)
    unit = (line.unit or "").strip() or "?"
    return f"#{idx} | {desc} | ${line.unit_cost:,.2f}/{unit} | {tier_label}"


def _sort_lines_by_tier(
    lines: list[CostLine],
) -> list[tuple[int, CostLine]]:
    """Stable-sort ``(index, line)`` pairs by tier preference.

    MANUAL_OVERRIDE first (so an operator who already touched a row
    finds it at the top), then EXACT → CATEGORY → INTERPOLATED →
    PARAMETRIC → MISSING. Stable-sorted on the original index so two
    rows in the same tier preserve their physical order in the
    estimate.
    """
    indexed = list(enumerate(lines))
    indexed.sort(
        key=lambda pair: (
            _TIER_SORT_ORDER.get(pair[1].cost_source_tier, 99),
            pair[0],
        )
    )
    return indexed


def _format_override_delta(
    old_estimate: Estimate,
    new_estimate: Estimate,
    line_idx: int,
) -> str:
    """Human-readable delta string for an override application.

    Surfaces three deltas the operator wants to see post-submit: the
    line's unit-cost change, the line's total-cost change, and the
    estimate-level subtotal change. Money formatted with thousands
    separators + 2dp; uses an arrow glyph (``→``) so the diff reads
    naturally.
    """
    old_line = old_estimate.line_items[line_idx]
    new_line = new_estimate.line_items[line_idx]
    return (
        f"Unit cost: ${old_line.unit_cost:,.2f} \u2192 ${new_line.unit_cost:,.2f}  |  "
        f"Line total: ${old_line.total_cost:,.2f} \u2192 ${new_line.total_cost:,.2f}  |  "
        f"Subtotal: ${old_estimate.subtotal:,.2f} \u2192 ${new_estimate.subtotal:,.2f}"
    )


def _apply_operator_override(
    estimate: Estimate,
    line_idx: int,
    new_unit_cost: float,
    vendor: str | None = None,
    quote_ref: str | None = None,
    free_text: str | None = None,
) -> tuple[Estimate, str | None]:
    """Format the operator-note + apply the override; returns ``(new_estimate, note)``.

    Pure wrapper around :func:`core.estimator.apply_manual_override`.
    Factored out of the Streamlit form so the round-trip can be tested
    without an ``AppTest`` harness. Re-raises ``ValueError`` from the
    underlying override pass unchanged so the UI layer can surface a
    clean ``st.error`` rather than a stack trace.
    """
    note = _format_operator_note(vendor, quote_ref, free_text)
    new_est = apply_manual_override(
        estimate,
        line_idx,
        new_unit_cost=new_unit_cost,
        operator_note=note,
    )
    return new_est, note


def _build_override_history_csv(history: list[dict[str, Any]]) -> str:
    """Serialise the override-history list to CSV for download.

    Empty history → header-only CSV (still a valid file, downloaded
    artifact tells the operator there are no overrides yet).
    """
    fieldnames = [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in history:
        writer.writerow(row)
    return buf.getvalue()


def _initialize_override_session_state(estimate: Estimate) -> None:
    """Populate the override-related session-state keys for a fresh estimate.

    Called once when a new estimate is built (analyze run) — captures
    a deep copy of the pre-override estimate for delta / reset, and
    seeds an empty history. Idempotent under repeat calls when an
    estimate already has snapshots: the brief specifies "populate once",
    but repeat calls (e.g. on an analysis re-run with the same run-id)
    overwrite the snapshot with the current estimate, which is the
    expected behaviour for a fresh analyze pass.
    """
    st.session_state["estimate_original"] = estimate.model_copy(deep=True)
    st.session_state["override_history"] = []


# ---------------------------------------------------------------------------
# Phase T6.3 — Batch operator override helpers
# ---------------------------------------------------------------------------
#
# Two pure helpers wrap the ``core.pricing.batch_override`` module for the
# Streamlit UI. The first summarises a match plan (counts + dollar adjustment
# estimate) for the preview pane. The second turns a list of applied
# ``BatchMatchResult`` into history rows compatible with the existing T6.2
# override-history download.


def _summarize_batch_plan(
    plan: BatchOverridePlan,
    estimate: Estimate | None = None,
) -> dict[str, Any]:
    """Aggregate a :class:`BatchOverridePlan` into UI-friendly counts + totals.

    Returns a dict with::

        total_rows            int   — sum of every bucket
        matched_count         int
        ambiguous_count       int
        no_match_count        int
        low_similarity_count  int
        similarity_threshold  float
        ambiguity_margin      float
        estimated_total_adjustment  float   — when ``estimate`` is supplied;
                                              0.0 otherwise. The dollar
                                              delta that auto-applying every
                                              MATCHED row would land, NOT
                                              including operator-resolved
                                              ambiguous rows.

    Pure / side-effect-free so the unit tests don't need a Streamlit
    harness. The Streamlit caller uses the same dict to render the
    summary metrics row in the preview pane.
    """
    out: dict[str, Any] = {
        "total_rows": plan.total_rows,
        "matched_count": len(plan.matched),
        "ambiguous_count": len(plan.ambiguous),
        "no_match_count": len(plan.no_match),
        "low_similarity_count": len(plan.low_similarity),
        "similarity_threshold": plan.similarity_threshold,
        "ambiguity_margin": plan.ambiguity_margin,
        "estimated_total_adjustment": 0.0,
    }
    if estimate is None:
        return out

    adj = 0.0
    for result in plan.matched:
        if result.best_match_index is None:
            continue
        if not 0 <= result.best_match_index < len(estimate.line_items):
            continue
        line = estimate.line_items[result.best_match_index]
        old_total = round(float(line.unit_cost) * float(line.quantity), 2)
        new_total = round(float(result.row.unit_cost) * float(line.quantity), 2)
        adj += new_total - old_total
    out["estimated_total_adjustment"] = round(adj, 2)
    return out


def _format_batch_csv_for_history(
    plan: BatchOverridePlan,
    applied_rows: list[BatchMatchResult],
) -> str:
    """Serialise applied batch rows into a CSV body with [batch]-tagged notes.

    Format mirrors :func:`_build_override_history_csv` (same eight
    column names) so a downstream auditor can concatenate the batch
    history block with the single-line history block without juggling
    schemas. The ``operator_note`` column always starts with
    ``[batch] ...`` via :func:`format_batch_operator_note`.

    ``applied_rows`` should be the subset of ``plan.matched`` (plus any
    operator-resolved ``plan.ambiguous`` rows) that were actually
    applied — not the full plan. Rows are emitted in ``row.row_index``
    order so the CSV reads the same direction as the source spreadsheet.
    """
    fieldnames = [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    buf = io.StringIO()
    writer = csv.DictWriter(buf, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    ordered = sorted(applied_rows, key=lambda r: r.row.row_index)
    for result in ordered:
        note = format_batch_operator_note(result.row)
        writer.writerow({
            "timestamp": "",
            "line_index": (
                result.best_match_index
                if result.best_match_index is not None
                else ""
            ),
            "description": result.row.description,
            "csi_division": "",
            "csi_section": "",
            "original_unit_cost": "",
            "new_unit_cost": round(float(result.row.unit_cost), 2),
            "operator_note": note,
        })
    return buf.getvalue()


from core.sheet_classifier import classify_sheet
from core.takeoff import ProjectModel, reconcile

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

ROOT = Path(__file__).parent
UPLOAD_DIR = ROOT / "uploads"
CACHE_DIR = ROOT / ".cache" / "renders"
EXPORT_DIR = ROOT / "exports"
CSI_TITLES_PATH = ROOT / "config" / "csi_divisions.json"
CLIENT_QUOTE_CFG_PATH = ROOT / "config" / "client_quote.json"

UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
CACHE_DIR.mkdir(parents=True, exist_ok=True)
EXPORT_DIR.mkdir(parents=True, exist_ok=True)


def _load_quote_config() -> QuoteConfig:
    """Read the client-quote config from disk, falling back to defaults."""
    if CLIENT_QUOTE_CFG_PATH.is_file():
        try:
            raw = json.loads(CLIENT_QUOTE_CFG_PATH.read_text(encoding="utf-8"))
            return QuoteConfig.model_validate(raw)
        except Exception as exc:
            logging.warning("client_quote.json failed to parse: %s", exc)
    return QuoteConfig()


def _save_quote_config(cfg: QuoteConfig) -> None:
    """Atomically replace the client-quote config on disk."""
    CLIENT_QUOTE_CFG_PATH.parent.mkdir(parents=True, exist_ok=True)
    tmp = CLIENT_QUOTE_CFG_PATH.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(cfg.model_dump(mode="json"), indent=2),
        encoding="utf-8",
    )
    os.replace(tmp, CLIENT_QUOTE_CFG_PATH)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@st.cache_data(show_spinner=False)
def _load_csi_titles() -> dict[str, str]:
    return json.loads(CSI_TITLES_PATH.read_text(encoding="utf-8"))


def _save_uploaded_pdfs(uploaded_files) -> list[Path]:
    paths: list[Path] = []
    for f in uploaded_files:
        target = UPLOAD_DIR / f.name
        target.write_bytes(f.getbuffer())
        paths.append(target)
    return paths


def _detect_provider() -> str | None:
    if os.getenv("ANTHROPIC_API_KEY"):
        return "anthropic"
    if os.getenv("OPENAI_API_KEY"):
        return "openai"
    return None


def _process_sheet(args: tuple[Sheet, str, str | None]) -> tuple[Sheet, SheetExtraction]:
    """Classifier + extractor for a single drawing sheet (thread-pool task)."""
    sheet, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    sheet = classify_sheet(sheet, llm)
    extraction = extract_sheet(sheet, llm)
    return sheet, extraction


def _process_bundle(args: tuple[DocumentBundle, str, str | None]) -> tuple[DocumentBundle, SheetExtraction]:
    """Document-level extractor for a whole text PDF (thread-pool task)."""
    bundle, provider, model = args
    llm = LLMClient(provider=provider, model=model)
    extraction = extract_bundle(bundle, llm)
    return bundle, extraction


def _run_pipeline(
    pdf_paths: list[Path],
    provider: str,
    model: str | None,
    region_mult: float,
    contingency_pct: float,
    overhead_pct: float,
    profit_pct: float,
    project_name: str,
    dpi: int,
    max_workers: int,
    progress_cb,
) -> tuple[list[Sheet], list[DocumentBundle], list[SheetExtraction], ProjectModel, Estimate]:
    progress_cb(0.02, "Splitting PDFs and rendering sheets...")
    sheets, bundles = process_pdfs(pdf_paths, cache_dir=CACHE_DIR, dpi=dpi)
    if not sheets and not bundles:
        raise RuntimeError("No usable pages found in the uploaded PDFs.")

    total_units = len(sheets) + len(bundles)
    progress_cb(
        0.08,
        f"Found {len(sheets)} drawing sheet(s) and {len(bundles)} text document(s). "
        f"Classifying and extracting...",
    )

    extractions: list[SheetExtraction] = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        sheet_futures = {
            pool.submit(_process_sheet, (s, provider, model)): ("sheet", s) for s in sheets
        }
        bundle_futures = {
            pool.submit(_process_bundle, (b, provider, model)): ("bundle", b) for b in bundles
        }
        all_futures = {**sheet_futures, **bundle_futures}

        new_sheets: list[Sheet] = list(sheets)

        for fut in as_completed(all_futures):
            kind, src = all_futures[fut]
            try:
                if kind == "sheet":
                    sheet, ex = fut.result()
                    # Replace original sheet object with the (possibly mutated) one.
                    for i, s in enumerate(new_sheets):
                        if s is src:
                            new_sheets[i] = sheet
                            break
                else:
                    _, ex = fut.result()
            except Exception as exc:
                logging.error("Unit %s failed: %s", getattr(src, "pdf_name", src), exc)
                sheet_id = getattr(src, "sheet_id", None) or getattr(src, "pdf_name", "unknown")
                ex = SheetExtraction(
                    sheet_id=sheet_id,
                    summary=f"Pipeline error: {exc}",
                    warnings=[f"pipeline error: {exc}"],
                )
            extractions.append(ex)
            completed += 1
            progress_cb(
                0.08 + 0.78 * completed / max(total_units, 1),
                f"Analyzed {completed}/{total_units} document units...",
            )

        sheets = new_sheets

    progress_cb(0.88, "Reconciling cross-document data...")
    project = reconcile(extractions)

    progress_cb(0.94, "Pricing takeoffs against cost database...")
    final_project_name = project.project_info.name or project_name
    estimate = price_takeoff(
        project,
        project_name=final_project_name,
        region_multiplier=region_mult,
        contingency_pct=contingency_pct,
        overhead_pct=overhead_pct,
        profit_pct=profit_pct,
        cost_db=CostDatabase(),
    )

    progress_cb(1.0, "Done.")
    return sheets, bundles, extractions, project, estimate


def _render_client_quote_tab(
    estimate: Estimate, project: ProjectModel, csi_titles: dict[str, str]
) -> None:
    """Edit `config/client_quote.json` and generate the proposal PDF (F12/F15)."""
    st.subheader("Client-ready quote (F12) + payment schedule (F15)")
    st.caption(
        "Edits below are saved to `config/client_quote.json`. The PDF reads "
        "from that file every time it's generated, so the CLI (`analyze.py "
        "--client-pdf`) and the UI stay in sync."
    )

    cfg = _load_quote_config()

    # ----- Branding sections -----
    with st.expander("Company info", expanded=False):
        cc1, cc2 = st.columns(2)
        company = CompanyInfo(
            name=cc1.text_input("Company name", cfg.company.name),
            license_number=cc2.text_input("License #", cfg.company.license_number),
            address_line_1=cc1.text_input("Address line 1", cfg.company.address_line_1),
            address_line_2=cc2.text_input("Address line 2", cfg.company.address_line_2),
            phone=cc1.text_input("Phone", cfg.company.phone),
            email=cc2.text_input("Email", cfg.company.email),
            website=cc1.text_input("Website", cfg.company.website),
            logo_path=cc2.text_input(
                "Logo path (optional)",
                cfg.company.logo_path,
                help="Absolute path or workspace-relative path to PNG/JPG. Leave blank to skip.",
            ),
        )

    with st.expander("Client info", expanded=False):
        kc1, kc2 = st.columns(2)
        client = ClientInfo(
            name=kc1.text_input("Client name", cfg.client.name),
            contact_name=kc2.text_input("Primary contact", cfg.client.contact_name),
            address_line_1=kc1.text_input("Client address line 1", cfg.client.address_line_1),
            address_line_2=kc2.text_input("Client address line 2", cfg.client.address_line_2),
            phone=kc1.text_input("Client phone", cfg.client.phone),
            email=kc2.text_input("Client email", cfg.client.email),
        )

    with st.expander("Quote meta", expanded=True):
        mc1, mc2 = st.columns([1, 1])
        quote_number = mc1.text_input(
            "Quote number", cfg.quote_meta.quote_number,
            help="Use 'AUTO' to derive from the project name + today's date at build time.",
        )
        valid_until_days = mc2.number_input(
            "Valid for (days)", value=int(cfg.quote_meta.valid_until_days),
            min_value=1, max_value=365, step=1,
        )
        scope_blurb = st.text_area(
            "Scope-of-work blurb (executive summary paragraph)",
            cfg.quote_meta.scope_blurb,
            height=100,
        )
        payment_terms_text = st.text_area(
            "Payment terms footer (rendered under the payment schedule)",
            cfg.quote_meta.payment_terms_text,
            height=70,
        )
        meta = QuoteMeta(
            quote_number=quote_number,
            valid_until_days=int(valid_until_days),
            scope_blurb=scope_blurb,
            payment_terms_text=payment_terms_text,
        )

    # ----- Payment schedule -----
    st.markdown("##### Payment schedule")
    st.caption(
        "Percentage mode auto-computes dollar amounts against the estimate's "
        "grand total. Milestone mode lets you set fixed dollar amounts."
    )
    sched_mode = st.radio(
        "Mode",
        options=["percentage", "milestone"],
        index=0 if cfg.payment_schedule.mode == "percentage" else 1,
        horizontal=True,
    )

    existing_rows = [
        {
            "label": m.label,
            "percentage": m.percentage if m.percentage is not None else 0.0,
            "amount": m.amount if m.amount is not None else 0.0,
            "notes": m.notes or "",
        }
        for m in cfg.payment_schedule.milestones
    ] or [{"label": "", "percentage": 0.0, "amount": 0.0, "notes": ""}]

    if sched_mode == "percentage":
        col_cfg = {
            "label":      st.column_config.TextColumn("Milestone", required=True),
            "percentage": st.column_config.NumberColumn("% of contract", min_value=0.0, max_value=100.0, step=0.5, format="%.1f"),
            "amount":     None,
            "notes":      st.column_config.TextColumn("Notes"),
        }
    else:
        col_cfg = {
            "label":      st.column_config.TextColumn("Milestone", required=True),
            "percentage": None,
            "amount":     st.column_config.NumberColumn("$ amount", min_value=0.0, step=100.0, format="$%.2f"),
            "notes":      st.column_config.TextColumn("Notes"),
        }
    edited = st.data_editor(
        pd.DataFrame(existing_rows),
        column_config=col_cfg,
        hide_index=True,
        use_container_width=True,
        num_rows="dynamic",
        key="payment_schedule_editor",
    )

    milestones: list[PaymentMilestone] = []
    for _, r in edited.iterrows():
        label = str(r.get("label", "") or "").strip()
        if not label:
            continue
        if sched_mode == "percentage":
            milestones.append(PaymentMilestone(
                label=label,
                percentage=float(r.get("percentage") or 0.0),
                amount=None,
                notes=str(r.get("notes", "") or ""),
            ))
        else:
            milestones.append(PaymentMilestone(
                label=label,
                percentage=None,
                amount=float(r.get("amount") or 0.0),
                notes=str(r.get("notes", "") or ""),
            ))

    # Build the candidate schedule WITHOUT raising — we want to show validation
    # errors inline instead of crashing the tab.
    schedule_valid = True
    schedule_err = ""
    try:
        schedule = PaymentSchedule(mode=sched_mode, milestones=milestones)
    except Exception as exc:
        schedule_valid = False
        schedule_err = str(exc)
        schedule = cfg.payment_schedule  # fall back so downstream code has something usable

    if not schedule_valid:
        st.warning(f"Payment schedule is invalid and will not be saved:\n\n{schedule_err}")
    elif sched_mode == "milestone":
        warns = schedule.validate_against_total(estimate.grand_total or 0.0)
        for w in warns:
            st.info(w)

    # ----- Terms -----
    with st.expander("Terms and conditions (optional)", expanded=False):
        terms_text = st.text_area(
            "Full T&Cs (blank to omit the page)",
            cfg.terms_text,
            height=240,
            help="Paragraph breaks are preserved (separate with a blank line).",
        )

    candidate_cfg = QuoteConfig(
        company=company,
        client=client,
        quote_meta=meta,
        payment_schedule=schedule,
        terms_text=terms_text,
    )

    # ----- Action buttons -----
    ac1, ac2 = st.columns(2)
    with ac1:
        if st.button(
            "Save configuration",
            type="secondary",
            use_container_width=True,
            disabled=not schedule_valid,
        ):
            try:
                _save_quote_config(candidate_cfg)
                st.success(f"Saved to {CLIENT_QUOTE_CFG_PATH.relative_to(ROOT)}.")
            except Exception as exc:
                st.error(f"Could not save: {exc}")

    with ac2:
        # Generate the PDF in-memory so the download works without writing
        # a (potentially client-identifying) file to disk by accident.
        pdf_bytes: bytes | None = None
        if schedule_valid:
            try:
                from core.exporter_pdf import build_quote_pdf  # local import for friendlier error
                tmp_pdf = EXPORT_DIR / "_quote_preview.pdf"
                build_quote_pdf(
                    estimate=estimate,
                    project=project,
                    quote_config=candidate_cfg,
                    out_path=tmp_pdf,
                    csi_titles=csi_titles,
                )
                pdf_bytes = tmp_pdf.read_bytes()
            except ImportError:
                st.error(
                    "`reportlab` is not installed. Run "
                    "`pip install 'reportlab>=4.0,<5.0'` in the venv."
                )
            except Exception as exc:
                st.error(f"PDF render failed: {exc}")

        st.download_button(
            "Generate & download PDF",
            data=pdf_bytes or b"",
            file_name=f"{estimate.project_name.replace(' ', '_')}_quote.pdf",
            mime="application/pdf",
            use_container_width=True,
            disabled=pdf_bytes is None,
        )


# ---------------------------------------------------------------------------
# UI
# ---------------------------------------------------------------------------


st.set_page_config(
    page_title="Construction Plan Estimator",
    page_icon="\U0001F3D7",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Construction Plan Estimator")
st.caption(
    "Upload a multi-PDF plan set; the app reads every sheet, builds a "
    "CSI-organized takeoff, and produces a priced estimate with full "
    "traceability back to the source drawings."
)

# --- Sidebar -----------------------------------------------------------------

with st.sidebar:
    st.header("Project")
    project_name = st.text_input("Project name", value="New Project")

    detected = _detect_provider()
    provider_choice = st.selectbox(
        "AI provider",
        options=[
            ("auto", "Auto-detect from .env"),
            ("anthropic", "Anthropic (Claude)"),
            ("openai", "OpenAI (GPT-4o)"),
        ],
        format_func=lambda x: x[1],
        index=0,
    )
    chosen_provider = detected if provider_choice[0] == "auto" else provider_choice[0]
    if chosen_provider:
        st.success(f"Using {chosen_provider}")
    else:
        st.error(
            "No API key found. Copy `.env.example` to `.env` and add either "
            "`ANTHROPIC_API_KEY` or `OPENAI_API_KEY`."
        )

    custom_model = st.text_input(
        "Model override (optional)",
        value="",
        placeholder="e.g. claude-sonnet-4-5 or gpt-4o",
    ).strip() or None

    st.divider()
    st.header("Estimating settings")
    region_mult = st.number_input(
        "Region cost multiplier", value=float(os.getenv("REGION_MULTIPLIER", "1.00")),
        min_value=0.5, max_value=2.5, step=0.01, format="%.2f",
    )
    contingency_pct = st.slider("Contingency %", 0.0, 25.0, 10.0, 0.5)
    overhead_pct = st.slider("Overhead %", 0.0, 25.0, 10.0, 0.5)
    profit_pct = st.slider("Profit %", 0.0, 20.0, 5.0, 0.5)

    st.divider()
    st.header("Performance")
    dpi = st.slider("Render DPI", 100, 300, int(os.getenv("RENDER_DPI", "200")), 25,
                    help="Higher = better OCR but more tokens. 200 is a good default.")
    max_workers = st.slider("Parallel sheets", 1, 8, int(os.getenv("MAX_CONCURRENCY", "4")))

    st.divider()
    st.subheader("Input")

    input_mode = st.radio(
        "Source",
        options=["Upload files", "Local folder"],
        horizontal=True,
        index=0,
        help="Use 'Local folder' to point at a directory with many PDFs (e.g. an entire GMP set) without dragging each file.",
    )

    uploaded_files = []
    folder_pdfs: list[Path] = []
    if input_mode == "Upload files":
        uploaded_files = st.file_uploader(
            "Upload plan-set PDF(s)",
            type=["pdf"],
            accept_multiple_files=True,
            help="Drag in any number of PDFs. Each page is treated as one sheet.",
        )
    else:
        folder_str = st.text_input(
            "Folder path",
            value="",
            placeholder=r"e.g. C:\Users\you\Project\GMP#003-Permit-Set",
        ).strip()
        recursive = st.checkbox("Recurse into subfolders", value=True)
        skip_large = st.checkbox(
            "Skip large PDFs (> 5 MB) - cheap text-only run",
            value=False,
            help="Useful for processing only the bid packages / specs without burning vision tokens on huge drawing sets.",
        )
        if folder_str:
            folder = Path(folder_str)
            if folder.exists() and folder.is_dir():
                pattern = "**/*.pdf" if recursive else "*.pdf"
                folder_pdfs = sorted(p for p in folder.glob(pattern) if p.is_file())
                if skip_large:
                    folder_pdfs = [p for p in folder_pdfs if p.stat().st_size <= 5 * 1024 * 1024]
                st.success(f"Found {len(folder_pdfs)} PDF(s).")
                with st.expander("Preview file list", expanded=False):
                    for p in folder_pdfs[:200]:
                        st.caption(f"\u2022 {p.relative_to(folder)}  ({p.stat().st_size / 1024:.0f} KB)")
                    if len(folder_pdfs) > 200:
                        st.caption(f"... and {len(folder_pdfs) - 200} more.")
            elif folder.exists():
                st.error("That path is a file, not a folder.")
            else:
                st.error("Folder not found.")

    run_disabled = not chosen_provider or (
        (input_mode == "Upload files" and not uploaded_files)
        or (input_mode == "Local folder" and not folder_pdfs)
    )
    run_clicked = st.button(
        "Analyze plan set",
        type="primary",
        use_container_width=True,
        disabled=run_disabled,
    )

# --- Main area --------------------------------------------------------------


def _render_proposal_panel() -> None:
    """Render-bid-proposal panel — picks a bid workspace, renders the four
    tier-appropriate artifacts (executive-summary PDF, full proposal PDF,
    internal workbook PDF, pitch-deck PPTX), and surfaces download
    buttons. Independent of the analyze flow above; safe to use without
    an active estimate in session state.
    """
    from core.proposal_renderer import (
        build_client_pdfs,
        build_internal_workbook,
        build_pitch_deck,
        load_firm_profile,
    )

    bids_root = ROOT / "bids"
    bid_dirs = sorted(
        p for p in bids_root.iterdir()
        if p.is_dir() and (p / "proposal").is_dir()
    ) if bids_root.is_dir() else []

    if not bid_dirs:
        st.info(
            "No `bids/<slug>/proposal/` workspaces found. Add a bid workspace "
            "before using the proposal renderer."
        )
        return

    bid_choice = st.selectbox(
        "Bid workspace",
        options=[p.name for p in bid_dirs],
        index=0,
        help="Each option corresponds to a `bids/<slug>/proposal/` directory.",
    )

    show_placeholders = st.checkbox(
        "Show `[USER TO FILL]` markers in red on client outputs",
        value=False,
        help=(
            "Default is to neutralize markers to a fillable underline on "
            "client-facing PDFs and the pitch deck. Toggle this on for "
            "your own internal review. The internal workbook always "
            "shows markers in red."
        ),
    )

    render_clicked = st.button(
        "Re-render proposal package",
        type="primary",
        help=(
            "Re-renders all four artifacts: client executive-summary PDF, "
            "full proposal PDF, internal workbook PDF, and pitch-deck PPTX."
        ),
    )

    state_key = f"proposal_render__{bid_choice}"
    if render_clicked:
        bid_dir = bids_root / bid_choice
        bid_slug = bid_dir.name
        out_dir = bid_dir / "proposal" / "exports"
        out_dir.mkdir(parents=True, exist_ok=True)
        try:
            firm_profile = load_firm_profile()
        except Exception as exc:
            st.error(f"Could not load firm/firm-profile.json: {exc}")
            return

        artifacts: dict[str, Path] = {}
        errors: list[str] = []

        try:
            client = build_client_pdfs(
                bid_dir, out_dir, firm_profile,
                show_placeholders=show_placeholders,
            )
            artifacts["executive_summary"] = client["executive_summary"]
            artifacts["full_proposal"] = client["full_proposal"]
        except Exception as exc:
            errors.append(f"Client PDF render failed: {exc}")

        try:
            internal_path = out_dir / f"{bid_slug}-internal-workbook.pdf"
            build_internal_workbook(bid_dir, internal_path, firm_profile)
            artifacts["internal_workbook"] = internal_path
        except Exception as exc:
            errors.append(f"Internal workbook render failed: {exc}")

        try:
            pitch_path = out_dir / f"{bid_slug}-pitch-deck.pptx"
            build_pitch_deck(
                bid_dir, pitch_path, firm_profile,
                show_placeholders=show_placeholders,
            )
            artifacts["pitch_deck"] = pitch_path
        except Exception as exc:
            errors.append(f"Pitch-deck render failed: {exc}")

        st.session_state[state_key] = {"artifacts": artifacts, "errors": errors}

    rendered = st.session_state.get(state_key)
    if not rendered:
        st.caption(
            "Click **Re-render proposal package** to (re-)generate the four "
            "tier-appropriate artifacts under "
            "`bids/<slug>/proposal/exports/`. If existing artifacts are on "
            "disk from a prior run, the download buttons below will surface "
            "them on next render."
        )
        # Try to surface previously rendered artifacts on disk so the user
        # doesn't have to re-render every reload.
        bid_dir = bids_root / bid_choice
        out_dir = bid_dir / "proposal" / "exports"
        bid_slug = bid_dir.name
        existing = {
            "executive_summary": out_dir / f"{bid_slug}-client-executive-summary.pdf",
            "full_proposal": out_dir / f"{bid_slug}-full-proposal.pdf",
            "internal_workbook": out_dir / f"{bid_slug}-internal-workbook.pdf",
            "pitch_deck": out_dir / f"{bid_slug}-pitch-deck.pptx",
        }
        existing = {k: v for k, v in existing.items() if v.exists()}
        if not existing:
            return
        rendered = {"artifacts": existing, "errors": []}

    for err in rendered["errors"]:
        st.error(err)

    artifacts = rendered["artifacts"]
    if not artifacts:
        return

    st.success(
        f"{len(artifacts)} artifact(s) ready under "
        f"`bids/{bid_choice}/proposal/exports/`."
    )

    pdf_mime = "application/pdf"
    pptx_mime = (
        "application/vnd.openxmlformats-officedocument.presentationml.presentation"
    )
    label_map = {
        "executive_summary": ("Executive summary (PDF)", pdf_mime),
        "full_proposal": ("Full proposal (PDF)", pdf_mime),
        "internal_workbook": ("Internal workbook (PDF)", pdf_mime),
        "pitch_deck": ("Pitch deck (PPTX)", pptx_mime),
    }
    # Stable display order: client deliverables first, then internal,
    # then pitch deck — matches the four-tier brief.
    order = ["executive_summary", "full_proposal", "internal_workbook", "pitch_deck"]
    ordered = [(k, artifacts[k]) for k in order if k in artifacts]
    cols = st.columns(len(ordered))
    for col, (key, path) in zip(cols, ordered):
        label, mime = label_map.get(key, (path.name, "application/octet-stream"))
        with col:
            st.download_button(
                label,
                data=path.read_bytes(),
                file_name=path.name,
                mime=mime,
                use_container_width=True,
            )
            st.caption(f"{path.stat().st_size:,} bytes")


with st.expander(
    "Bid Proposals — render client PDFs, internal workbook, and pitch deck",
    expanded=False,
):
    st.caption(
        "Independent of the plan-set analyzer above. Picks a bid workspace "
        "under `bids/`, reads its `proposal/*.md` files, and produces four "
        "tier-appropriate artifacts under `bids/<slug>/proposal/exports/`: "
        "client executive-summary PDF, full proposal PDF, internal workbook "
        "PDF, and pitch-deck PPTX."
    )
    _render_proposal_panel()


if run_clicked:
    if input_mode == "Upload files":
        pdf_paths = _save_uploaded_pdfs(uploaded_files)
    else:
        pdf_paths = folder_pdfs   # use the on-disk paths directly; no copy needed
    progress_bar = st.progress(0.0)
    status_text = st.empty()

    def update_progress(p: float, msg: str) -> None:
        progress_bar.progress(min(max(p, 0.0), 1.0))
        status_text.info(msg)

    started = time.time()
    try:
        sheets, bundles, extractions, project, estimate = _run_pipeline(
            pdf_paths=pdf_paths,
            provider=chosen_provider,
            model=custom_model,
            region_mult=region_mult,
            contingency_pct=contingency_pct,
            overhead_pct=overhead_pct,
            profit_pct=profit_pct,
            project_name=project_name,
            dpi=dpi,
            max_workers=max_workers,
            progress_cb=update_progress,
        )
    except Exception as exc:
        progress_bar.empty()
        status_text.empty()
        st.error(f"Pipeline failed: {exc}")
        st.stop()

    elapsed = time.time() - started
    status_text.success(
        f"Analyzed {len(sheets)} drawing sheet(s) and {len(bundles)} document(s) in {elapsed:.1f}s."
    )

    st.session_state["sheets"] = sheets
    st.session_state["bundles"] = bundles
    st.session_state["extractions"] = extractions
    st.session_state["project"] = project
    st.session_state["estimate"] = estimate
    # Phase T6.2 — seed the override snapshot + history for the operator-
    # override UI in the Estimate tab. Done here (immediately after the
    # estimate is committed to session state) so a fresh analyze run
    # always starts with an empty override history regardless of any
    # prior session activity.
    _initialize_override_session_state(estimate)

# --- Results -----------------------------------------------------------------

if "estimate" in st.session_state:
    csi_titles = _load_csi_titles()
    project: ProjectModel = st.session_state["project"]
    estimate: Estimate = st.session_state["estimate"]
    sheets: list[Sheet] = st.session_state["sheets"]
    bundles: list[DocumentBundle] = st.session_state.get("bundles", [])
    extractions: list[SheetExtraction] = st.session_state["extractions"]
    pi = project.project_info

    # --- Project header banner ---
    if pi and (pi.name or pi.number):
        bits = []
        if pi.name:        bits.append(f"**{pi.name}**")
        if pi.number:      bits.append(f"#{pi.number}")
        if pi.location:    bits.append(pi.location)
        if pi.contractor:  bits.append(f"GC: {pi.contractor}")
        if pi.bid_due:     bits.append(f"Bid due: {pi.bid_due}")
        st.info(" \u2022 ".join(bits))

    # --- KPI row ---
    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Drawing sheets", len(sheets))
    k2.metric("Bid packages", len(project.bid_packages))
    k3.metric("Line items", len(estimate.line_items))
    k4.metric("Subtotal", f"${estimate.subtotal:,.0f}")
    k5.metric("Grand total", f"${estimate.grand_total:,.0f}")

    tabs = st.tabs([
        "Project", "Bid Packages", "Scope Matrix", "Scope Coverage", "Alternates",
        "Estimate", "By Division", "Sheets", "Rooms",
        "Doors / Windows", "Structural / MEP", "Specs",
        "Raw takeoffs", "Warnings", "Client Quote",
    ])

    # --- Project tab ---
    with tabs[0]:
        c1, c2 = st.columns([1, 1])
        with c1:
            st.subheader("Project information")
            st.write(f"**Name:** {pi.name or '(not detected)'}")
            st.write(f"**Number:** {pi.number or '(not detected)'}")
            st.write(f"**Location:** {pi.location or '(not detected)'}")
            st.write(f"**Owner:** {pi.owner or '(not detected)'}")
            st.write(f"**General contractor:** {pi.contractor or '(not detected)'}")
            st.write(f"**Bid due:** {pi.bid_due or '(not detected)'}")
            if pi.sources:
                st.caption(f"Source PDFs: {', '.join(pi.sources)}")
        with c2:
            st.subheader("Document inventory")
            inventory = [
                {"Type": "Drawing sheet", "Count": len(sheets)},
                {"Type": "Bid package",   "Count": sum(1 for b in bundles if b.sheet_type.endswith("bid_package") or "bid_package" in str(b.sheet_type))},
                {"Type": "Project manual / flyer / questionnaire",
                 "Count": sum(1 for b in bundles if "project_manual" in str(b.sheet_type) or "bid_form" in str(b.sheet_type))},
            ]
            st.dataframe(pd.DataFrame(inventory), hide_index=True, use_container_width=True)

            st.subheader("Coverage by CSI division")
            sm_rows = []
            for div in sorted(project.scope_matrix.by_division):
                pkgs = project.scope_matrix.by_division[div]
                sm_rows.append({
                    "Div":      div,
                    "Title":    csi_titles.get(div, ""),
                    "# Packages": len(pkgs),
                    "Trades":   ", ".join(p.trade_name or p.pdf_name for p in pkgs),
                })
            if sm_rows:
                st.dataframe(pd.DataFrame(sm_rows), hide_index=True, use_container_width=True)
            else:
                st.caption("No bid-package coverage detected.")

    # --- Bid Packages tab ---
    # Split into two sub-sections: trade packages (the existing view, filtered
    # to `document_kind == 'trade_package'`) and supporting documents (wage
    # determinations, sample agreements, tax-exemption certificates, HSP
    # templates, UGSC, etc.). Pre-calibration-v3 these all landed in the same
    # table with `trade_name='other'`, polluting the export.
    with tabs[1]:
        trade_packages = [p for p in project.bid_packages if p.document_kind == "trade_package"]
        supporting_docs = [p for p in project.bid_packages if p.document_kind == "supporting_document"]

        st.subheader("Trade Packages")
        if not trade_packages:
            st.info("No trade packages detected. Upload Beck-style scope/bid PDFs to populate this view.")
        else:
            for p in sorted(trade_packages, key=lambda x: x.package_number or x.pdf_name):
                title_bits = filter(None, [
                    f"#{p.package_number}" if p.package_number else None,
                    p.trade_name,
                    f"({p.pdf_name})",
                ])
                with st.expander(" \u2022 ".join(title_bits), expanded=False):
                    cols = st.columns([1, 2])
                    with cols[0]:
                        st.write(f"**Project:** {p.project_name or '?'}  (#{p.project_number or '?'})")
                        # Owner / GC split — owner is the agency/institution
                        # paying (USFWS, ASU, TAMU); gc is the construction
                        # manager running the bid (Beck, JE Dunn). On
                        # government direct solicitations gc is typically None.
                        st.write(f"**Owner:** {p.owner or '—'}")
                        st.write(f"**General contractor:** {p.gc or '—'}")
                        st.write(f"**CSI divisions:** {', '.join(p.csi_divisions) or '?'}")
                        if p.csi_sections:
                            st.caption("Sections: " + ", ".join(p.csi_sections))
                        if p.referenced_drawings:
                            st.caption("Refd drawings: " + ", ".join(p.referenced_drawings))
                        if p.referenced_specs:
                            st.caption("Refd specs: " + ", ".join(p.referenced_specs))
                    with cols[1]:
                        if p.summary:
                            st.write(p.summary)
                    if p.inclusions:
                        st.markdown(f"**Inclusions ({len(p.inclusions)}):**")
                        for it in p.inclusions:
                            st.markdown(f"- {it}")
                    if p.exclusions:
                        st.markdown(f"**Exclusions ({len(p.exclusions)}):**")
                        for it in p.exclusions:
                            st.markdown(f"- {it}")
                    if p.alternates:
                        st.markdown(f"**Alternates ({len(p.alternates)}):**")
                        st.dataframe(
                            pd.DataFrame([a.model_dump() for a in p.alternates]),
                            hide_index=True, use_container_width=True,
                        )
                    if p.unit_prices:
                        st.markdown(f"**Unit prices ({len(p.unit_prices)}):**")
                        st.dataframe(
                            pd.DataFrame([u.model_dump() for u in p.unit_prices]),
                            hide_index=True, use_container_width=True,
                        )

        st.divider()
        st.subheader("Supporting Documents")
        if not supporting_docs:
            st.caption("No supporting documents extracted yet.")
        else:
            # Reuse the exporter's classifier so the UI matches the Excel
            # "Kind" column exactly.
            from core.exporter import _classify_supporting_doc
            sd_rows = []
            for p in sorted(supporting_docs, key=lambda x: x.pdf_name):
                sd_rows.append({
                    "Filename": p.pdf_name,
                    "Kind": _classify_supporting_doc(p),
                    "Owner": p.owner or "",
                    "Summary": (p.summary or "")[:300],
                })
            st.dataframe(
                pd.DataFrame(sd_rows),
                hide_index=True, use_container_width=True,
            )

    # --- Scope Matrix tab ---
    with tabs[2]:
        if not project.scope_matrix.by_division:
            st.info("No CSI division coverage to display yet.")
        else:
            rows = []
            for div in sorted(project.scope_matrix.by_division):
                for p in project.scope_matrix.by_division[div]:
                    rows.append({
                        "Div":     div,
                        "Title":   csi_titles.get(div, ""),
                        "Pkg #":   p.package_number or "",
                        "Trade":   p.trade_name or "",
                        "PDF":     p.pdf_name,
                        "Inclusions": len(p.inclusions),
                        "Exclusions": len(p.exclusions),
                        "Alternates": len(p.alternates),
                        "Unit prices": len(p.unit_prices),
                    })
            st.dataframe(pd.DataFrame(rows), hide_index=True, use_container_width=True)
            if project.scope_matrix.coverage_warnings:
                st.warning(
                    "Potential scope overlaps:\n\n- " +
                    "\n- ".join(project.scope_matrix.coverage_warnings)
                )

    # --- Scope Coverage tab ---
    with tabs[3]:
        agg_inc = project.aggregated_inclusions
        agg_exc = project.aggregated_exclusions
        if not agg_inc and not agg_exc:
            st.info("No aggregated inclusions or exclusions detected. Upload bid-package PDFs to populate this view.")
        else:
            st.caption(
                "Deduplicated across all bid packages using fuzzy text match. "
                "'# Packages' counts how many bid packages contributed an "
                "equivalent line; expand a row to see which ones."
            )

            c1, c2 = st.columns(2)
            with c1:
                st.subheader(f"Inclusions ({len(agg_inc)})")
                if agg_inc:
                    inc_rows = [{
                        "Inclusion": it.text,
                        "# Packages": len(it.source_packages),
                        "Source Packages": ", ".join(it.source_packages),
                    } for it in agg_inc]
                    st.dataframe(pd.DataFrame(inc_rows), hide_index=True, use_container_width=True)
                else:
                    st.info("No aggregated inclusions.")
            with c2:
                st.subheader(f"Exclusions ({len(agg_exc)})")
                if agg_exc:
                    exc_rows = [{
                        "Exclusion": it.text,
                        "# Packages": len(it.source_packages),
                        "Source Packages": ", ".join(it.source_packages),
                    } for it in agg_exc]
                    st.dataframe(pd.DataFrame(exc_rows), hide_index=True, use_container_width=True)
                else:
                    st.info("No aggregated exclusions.")

    # --- Alternates tab ---
    with tabs[4]:
        if not project.scope_matrix.all_alternates:
            st.info("No alternates detected.")
        else:
            st.dataframe(
                pd.DataFrame([a.model_dump() for a in project.scope_matrix.all_alternates]),
                hide_index=True, use_container_width=True,
            )

    # --- Estimate tab ---
    with tabs[5]:
        # Phase T6 — surface the manual-takeoff worklist at the top of
        # the tab BEFORE the cost breakdown, so an estimator's first
        # signal is "do you have hand-takeoff work to do?".
        if estimate.hand_takeoff_count > 0:
            st.warning(
                f"\u26A0 {estimate.hand_takeoff_count} line"
                f"{'s' if estimate.hand_takeoff_count != 1 else ''} need "
                f"manual takeoff — see Review Queues below.",
                icon="\u26A0\uFE0F",
            )

        st.subheader("Confidence band breakdown (Phase T6)")
        st.caption(
            "Auto-Approve (\u2265 0.85) rolls into the headline grand total. "
            "Operator-Review (0.65\u20130.85) also rolls in but needs a manual "
            "eyeball before submitting. Hand-Takeoff (< 0.65, or unit-mismatch "
            "suppressed) is excluded from the grand total and surfaced below "
            "as a worklist."
        )
        bc1, bc2, bc3 = st.columns(3)
        bc1.metric(
            "Auto-Approve",
            f"${estimate.total_auto_approve:,.0f}",
            f"{estimate.auto_approve_count} line"
            f"{'s' if estimate.auto_approve_count != 1 else ''}",
        )
        bc2.metric(
            "Operator-Review",
            f"${estimate.total_operator_review:,.0f}",
            f"{estimate.operator_review_count} line"
            f"{'s' if estimate.operator_review_count != 1 else ''}",
        )
        bc3.metric(
            "Hand-Takeoff",
            f"${estimate.total_hand_takeoff:,.0f}",
            f"{estimate.hand_takeoff_count} line"
            f"{'s' if estimate.hand_takeoff_count != 1 else ''} (not in total)",
            delta_color="off",
        )

        gtc1, gtc2 = st.columns(2)
        gtc1.metric(
            "Grand Total (Auto + Review)",
            f"${estimate.grand_total_with_review:,.0f}",
            help="Headline number — the 'if reviewer signs off' total.",
        )
        gtc2.metric(
            "Grand Total (Auto-Only)",
            f"${estimate.grand_total_auto_only:,.0f}",
            help="Conservative floor — markups computed against the AUTO-only subtotal.",
        )

        # Phase T7 — Cost Source Mix expander. Sits BELOW the T6 band
        # tiles so the reader's mental flow is "qty-side confidence
        # (band) → price-side confidence (tier)". Auto-collapsed by
        # default; opens on demand for the operator who wants to see
        # which CSI rows came from CWICR / seed-DB / no match.
        with st.expander(
            "Cost Source Mix (Phase T7)",
            expanded=False,
        ):
            st.caption(
                "Catalog-completeness breakdown of every line, regardless of "
                "band. **Exact Match** = direct CWICR hit at \u2265 0.92 sim or "
                "any seed-DB hit. **Category Match** = CWICR sim 0.75\u20130.92 "
                "(same CSI family, slightly off description). **Interpolated** "
                "= CWICR sim 0.50\u20130.75 (region-adjusted neighbour). "
                "**Parametric** = CWICR sim < 0.50 (rare). **Manual Override** "
                "= operator-set unit cost. **Missing** = no cost data found."
            )
            tier_counts = estimate.count_by_tier
            tier_totals = estimate.total_by_tier
            tier_rows = [
                {
                    "Tier": _T7_TIER_LABELS[tier],
                    "Lines": tier_counts.get(tier, 0),
                    "Total $": tier_totals.get(tier, 0.0),
                }
                for tier in CostSourceTier
            ]
            tier_df = pd.DataFrame(tier_rows)
            st.dataframe(
                tier_df, hide_index=True, use_container_width=True,
                column_config={
                    "Total $": st.column_config.NumberColumn(format="$%.2f"),
                },
            )

        with st.expander(
            "Review Queues "
            f"(Review: {estimate.operator_review_count}, "
            f"Hand: {estimate.hand_takeoff_count})",
            expanded=estimate.hand_takeoff_count > 0,
        ):
            # Phase T7 — tier-filter dropdown applied to BOTH queues.
            # Default "All" preserves the pre-T7 behaviour exactly.
            tier_filter_options = ["All"] + list(_T7_TIER_LABELS.values())
            queue_tier_filter = st.selectbox(
                "Filter queues by Cost Source Tier",
                options=tier_filter_options,
                index=0,
                key="t7_queue_tier_filter",
                help=(
                    "Narrow both queues to lines from a single catalog-"
                    "completeness tier. Useful for triaging the Missing / "
                    "Interpolated rows separately from the Category-Match ones."
                ),
            )

            def _matches_tier_filter(li) -> bool:
                if queue_tier_filter == "All":
                    return True
                return _t7_tier_label(li) == queue_tier_filter

            st.markdown("##### Operator Review Queue")
            st.caption(
                "Confidence 0.65\u20130.84 — included in totals but flagged "
                "for an eyeball before submitting."
            )
            review_lines = [
                li for li in estimate.operator_review_line_items
                if _matches_tier_filter(li)
            ]
            if not review_lines:
                if queue_tier_filter == "All":
                    st.caption("(empty — every priced row cleared the 0.85 auto-approve threshold.)")
                else:
                    st.caption(f"(no operator-review lines match tier '{queue_tier_filter}'.)")
            else:
                review_df = pd.DataFrame([
                    {
                        "CSI": li.csi_section or li.csi_division,
                        "Description": li.description,
                        "Qty": li.quantity,
                        "Unit": li.unit,
                        "Unit Cost": li.unit_cost,
                        "Total": li.total_cost,
                        "Conf": li.confidence,
                        "Tier": _t7_tier_label(li),
                        "Source": ", ".join(li.source_sheet_ids),
                        "Notes": li.notes or "",
                    }
                    for li in review_lines
                ])
                st.dataframe(
                    review_df, hide_index=True, use_container_width=True,
                    column_config={
                        "Unit Cost": st.column_config.NumberColumn(format="$%.2f"),
                        "Total":     st.column_config.NumberColumn(format="$%.2f"),
                        "Conf":      st.column_config.NumberColumn(format="%.2f"),
                        "Qty":       st.column_config.NumberColumn(format="%.2f"),
                    },
                )

            st.markdown("##### Hand Takeoff Queue")
            st.caption(
                "Confidence < 0.65 (or unit-mismatch suppressed) \u2014 excluded "
                "from the grand total. Each row needs an in-person takeoff."
            )
            hand_lines = [
                li for li in estimate.hand_takeoff_line_items
                if _matches_tier_filter(li)
            ]
            if not hand_lines:
                if queue_tier_filter == "All":
                    st.caption("(empty \u2014 no rows under 0.65 confidence and no unit-mismatch suppression.)")
                else:
                    st.caption(f"(no hand-takeoff lines match tier '{queue_tier_filter}'.)")
            else:
                hand_df = pd.DataFrame([
                    {
                        "CSI": li.csi_section or li.csi_division,
                        "Description": li.description,
                        "Qty": li.quantity,
                        "Unit": li.unit,
                        "Unit Cost": li.unit_cost,
                        "Total": li.total_cost,
                        "Conf": li.confidence,
                        "Tier": _t7_tier_label(li),
                        "Source": ", ".join(li.source_sheet_ids),
                        "Action": "Manual takeoff required",
                        "Notes": li.notes or "",
                    }
                    for li in hand_lines
                ])
                st.dataframe(
                    hand_df, hide_index=True, use_container_width=True,
                    column_config={
                        "Unit Cost": st.column_config.NumberColumn(format="$%.2f"),
                        "Total":     st.column_config.NumberColumn(format="$%.2f"),
                        "Conf":      st.column_config.NumberColumn(format="%.2f"),
                        "Qty":       st.column_config.NumberColumn(format="%.2f"),
                    },
                )

        st.divider()
        by_cat = estimate.by_cost_category
        if by_cat:
            st.subheader("Labor / material / sub split")
            cat_subtotal = estimate.subtotal or 0.0

            def _cat_tile(col, label: str, key: str) -> None:
                amount = by_cat.get(key, 0.0)
                pct = (amount / cat_subtotal * 100.0) if cat_subtotal else 0.0
                col.metric(label, f"${amount:,.0f}", f"{pct:.1f}% of subtotal")

            tile_cols = st.columns(5)
            _cat_tile(tile_cols[0], "Labor",          "labor")
            _cat_tile(tile_cols[1], "Material",       "material")
            _cat_tile(tile_cols[2], "Equipment",      "equipment")
            _cat_tile(tile_cols[3], "Subcontractor",  "subcontractor")
            _cat_tile(tile_cols[4], "Other",          "other")
            st.divider()

        # ----- Cost database breakdown (F1) -----
        st.subheader("Cost database")
        st.caption(
            "Where each line's unit cost came from. **cwicr** = matched against "
            "the 55k-row CWICR open dataset (CC-BY-4.0). **seed** = bundled "
            "47-entry seed `config/cost_database.json`. **no match** = neither "
            "layer found a unit cost; the line shows $0 and needs manual entry."
        )

        src_counts: dict[str, int] = {"cwicr": 0, "seed": 0, "no match": 0}
        cwicr_sims: list[float] = []
        for li in estimate.line_items:
            src = li.cost_source or ""
            if src.startswith("cwicr:"):
                src_counts["cwicr"] += 1
                cwicr_sims.append(float(li.confidence))
            elif src in ("", "(no match)"):
                src_counts["no match"] += 1
            else:
                src_counts["seed"] += 1

        sc1, sc2, sc3, sc4 = st.columns(4)
        sc1.metric("CWICR",     src_counts["cwicr"])
        sc2.metric("Seed DB",   src_counts["seed"])
        sc3.metric("No match",  src_counts["no match"])
        avg_sim = (sum(cwicr_sims) / len(cwicr_sims)) if cwicr_sims else 0.0
        sc4.metric("Avg CWICR sim", f"{avg_sim:.2f}" if cwicr_sims else "—")

        # Pie / bar chart of the breakdown.
        breakdown_df = pd.DataFrame(
            [{"source": k, "lines": v} for k, v in src_counts.items() if v > 0]
        )
        if not breakdown_df.empty:
            st.bar_chart(breakdown_df.set_index("source"))

        # Session-scoped toggle to disable CWICR + a re-price button.
        cwicr_off_now = st.session_state.get("cwicr_disabled_session", False)
        new_disabled = st.checkbox(
            "Disable CWICR for this session (use seed DB only)",
            value=cwicr_off_now,
            help=(
                "Toggle to re-price with the seed DB only — useful for "
                "before/after comparisons. Affects this Streamlit session "
                "only; does not write to `.env`."
            ),
            key="cwicr_disabled_session",
        )
        if st.button("Re-price with current CWICR setting", use_container_width=True):
            with st.spinner("Re-pricing…"):
                new_estimate = price_takeoff(
                    project,
                    project_name=estimate.project_name,
                    region_multiplier=estimate.region_multiplier,
                    contingency_pct=estimate.contingency_pct,
                    overhead_pct=estimate.overhead_pct,
                    profit_pct=estimate.profit_pct,
                    cost_db=CostDatabase(),
                    use_cwicr=not new_disabled,
                )
            st.session_state["estimate"] = new_estimate
            st.rerun()

        st.divider()
        st.subheader("Priced line items")
        priced = estimate.priced_line_items
        suppressed = estimate.suppressed_line_items
        df = pd.DataFrame([li.model_dump() for li in priced])
        if df.empty:
            st.info("No priced line items yet.")
        else:
            df["source_sheet_ids"] = df["source_sheet_ids"].apply(lambda xs: ", ".join(xs))

            def _src_family(s: str) -> str:
                if not s or s == "(no match)":
                    return "no match"
                if s.startswith("cwicr:"):
                    return "cwicr"
                return "seed"

            df["src_family"] = df["cost_source"].apply(_src_family)
            # CWICR similarity is the same as `confidence` for CWICR rows;
            # show it as a separate column for at-a-glance match quality.
            df["cwicr_sim"] = [
                float(li.confidence) if (li.cost_source or "").startswith("cwicr:") else None
                for li in priced
            ]
            edited = st.data_editor(
                df[
                    [
                        "csi_division", "csi_section", "cost_category", "description",
                        "raw_quantity", "waste_factor", "quantity", "unit",
                        "unit_cost", "total_cost",
                        "confidence", "src_family", "cwicr_sim",
                        "source_sheet_ids", "cost_source", "notes",
                    ]
                ].rename(columns={
                    "csi_division": "Div", "csi_section": "Section",
                    "cost_category": "Category",
                    "description": "Description",
                    "raw_quantity": "Raw Qty", "waste_factor": "Waste",
                    "quantity": "Qty",
                    "unit": "Unit", "unit_cost": "Unit Cost",
                    "total_cost": "Total", "confidence": "Conf",
                    "src_family": "Cost Source",
                    "cwicr_sim": "CWICR Sim",
                    "source_sheet_ids": "Source Sheets",
                    "cost_source": "Cost Key", "notes": "Notes",
                }),
                hide_index=True,
                use_container_width=True,
                num_rows="dynamic",
                column_config={
                    "Unit Cost":  st.column_config.NumberColumn(format="$%.2f"),
                    "Total":      st.column_config.NumberColumn(format="$%.2f"),
                    "Conf":       st.column_config.NumberColumn(format="%.2f"),
                    "Qty":        st.column_config.NumberColumn(format="%.2f"),
                    "Raw Qty":    st.column_config.NumberColumn(format="%.2f"),
                    "Waste":      st.column_config.NumberColumn(format="%.2f"),
                    "CWICR Sim":  st.column_config.NumberColumn(format="%.2f"),
                },
            )
            if st.button("Recalculate totals from edited table", use_container_width=True):
                edited["Total"] = (edited["Qty"].fillna(0) * edited["Unit Cost"].fillna(0)).round(2)
                # Update only the priced (non-suppressed) lines in place, in
                # the same order they were rendered.
                for i, li in enumerate(priced):
                    if i >= len(edited):
                        break
                    li.quantity = float(edited.iloc[i]["Qty"] or 0)
                    li.unit_cost = float(edited.iloc[i]["Unit Cost"] or 0)
                    li.total_cost = round(li.quantity * li.unit_cost, 2)
                st.session_state["estimate"] = estimate
                st.rerun()

        if suppressed:
            with st.expander(
                f"Unmatched / suppressed lines ({len(suppressed)}) — not in totals",
                expanded=False,
            ):
                st.caption(
                    "These takeoff lines were detected but couldn't be priced "
                    "safely (typically unit mismatch between the takeoff and the "
                    "cost-DB entry). They are listed here for visibility and are "
                    "excluded from every total / rollup."
                )
                sup_df = pd.DataFrame([li.model_dump() for li in suppressed])
                sup_df["source_sheet_ids"] = sup_df["source_sheet_ids"].apply(
                    lambda xs: ", ".join(xs)
                )
                st.dataframe(
                    sup_df[
                        [
                            "csi_division", "csi_section", "description",
                            "raw_quantity", "quantity", "unit", "cost_source", "notes",
                        ]
                    ].rename(columns={
                        "csi_division": "Div", "csi_section": "Section",
                        "description": "Description",
                        "raw_quantity": "Raw Qty", "quantity": "Qty",
                        "unit": "Unit", "cost_source": "Cost Key", "notes": "Notes",
                    }),
                    hide_index=True,
                    use_container_width=True,
                )

        # ------------------------------------------------------------------
        # Phase T6.2 — Operator price overrides
        # ------------------------------------------------------------------
        #
        # Wires ``apply_manual_override`` (T6.1) into the Streamlit
        # round-trip with vendor / quote-ref attribution and an
        # operator-note field. Sits after the suppressed expander so
        # the operator's mental flow is "look at table → spot a row
        # that needs a hand-priced number → apply override → see new
        # totals". Snapshot + history live in session-state, seeded
        # by ``_initialize_override_session_state`` at analyze time.

        # Defensive: if a session predates T6.2 (estimate already in
        # session_state from a pre-T6.2 run), seed the snapshot now so
        # the rest of the section works cleanly.
        if "estimate_original" not in st.session_state:
            st.session_state["estimate_original"] = estimate.model_copy(deep=True)
        if "override_history" not in st.session_state:
            st.session_state["override_history"] = []

        estimate_original: Estimate = st.session_state["estimate_original"]
        override_history: list[dict[str, Any]] = st.session_state["override_history"]

        # Top-of-section banner for context — only shown when overrides exist.
        manual_override_lines = [
            li for li in estimate.line_items
            if li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
        ]
        if manual_override_lines:
            adj_total = sum(
                li.total_cost - estimate_original.line_items[i].total_cost
                for i, li in enumerate(estimate.line_items)
                if li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
                and i < len(estimate_original.line_items)
            )
            adj_sign = "+" if adj_total >= 0 else "\u2212"
            st.info(
                f"\U0001F4DD {len(manual_override_lines)} manual override"
                f"{'s' if len(manual_override_lines) != 1 else ''} applied "
                f"\u2014 {adj_sign}${abs(adj_total):,.2f} total adjustment "
                f"vs. original."
            )

        with st.expander(
            "Operator price overrides (Phase T6.2)",
            expanded=False,
        ):
            st.caption(
                "Hand-price a single line by entering a vendor-quote unit "
                "cost. Overrides stamp ``cost_source_tier = MANUAL_OVERRIDE`` "
                "and ``price_confidence = 1.0`` on the line, force "
                "``suppressed = False`` (manual pricing IS the resolution "
                "to a unit-mismatch suppression), and recompute the band "
                "against the new combined confidence. A vendor / "
                "quote-ref / free-text note is stamped onto the line's "
                "``notes`` field with the ``operator override`` sentinel "
                "so downstream readers (Excel / PDF / CSV) can detect the "
                "override."
            )

            all_lines = list(estimate.line_items)
            if not all_lines:
                st.info("No line items to override.")
            else:
                indexed_sorted = _sort_lines_by_tier(all_lines)
                label_to_idx: dict[str, int] = {}
                labels: list[str] = []
                for orig_idx, li in indexed_sorted:
                    label = _select_line_label(orig_idx, li)
                    # Disambiguate the rare collision (same desc / unit /
                    # cost / tier on two indices) by appending the index.
                    if label in label_to_idx:
                        label = f"{label} (idx={orig_idx})"
                    label_to_idx[label] = orig_idx
                    labels.append(label)

                with st.form("operator_override_form", clear_on_submit=False):
                    selected_label = st.selectbox(
                        "Line to override",
                        options=labels,
                        index=0,
                        help=(
                            "Lines are sorted MANUAL_OVERRIDE first, then "
                            "EXACT \u2192 CATEGORY \u2192 INTERPOLATED \u2192 "
                            "PARAMETRIC \u2192 MISSING. The leading #N is "
                            "the stable line index used by the override "
                            "pass."
                        ),
                    )
                    selected_idx = label_to_idx.get(selected_label, 0)
                    selected_line = all_lines[selected_idx]

                    new_unit_cost = st.number_input(
                        "New unit cost",
                        min_value=0.0,
                        value=float(selected_line.unit_cost),
                        step=0.01,
                        format="%.2f",
                        help="Per-unit cost. Multiplied by the line's quantity to recompute total.",
                    )
                    vendor = st.text_input(
                        "Vendor (optional)",
                        value="",
                        placeholder="e.g., Ferguson Plumbing, Home Depot Pro",
                        help="Stamped onto the operator note as ``[vendor: ...]``.",
                    )
                    quote_ref = st.text_input(
                        "Quote / PO reference (optional)",
                        value="",
                        placeholder="e.g., Q-2026-0428, PO#12345",
                        help="Stamped onto the operator note as ``[quote-ref: ...]``.",
                    )
                    operator_free_text = st.text_area(
                        "Operator note (optional)",
                        value="",
                        placeholder="Free-form reason / context for the override",
                        height=80,
                    )
                    submitted = st.form_submit_button(
                        "Apply override",
                        use_container_width=True,
                    )

                if submitted:
                    pre_override = estimate
                    try:
                        new_estimate, formatted_note = _apply_operator_override(
                            estimate,
                            selected_idx,
                            new_unit_cost=float(new_unit_cost),
                            vendor=vendor,
                            quote_ref=quote_ref,
                            free_text=operator_free_text,
                        )
                    except ValueError as exc:
                        st.error(f"Override failed: {exc}")
                    else:
                        old_line = pre_override.line_items[selected_idx]
                        new_line = new_estimate.line_items[selected_idx]
                        # Append to history BEFORE rerun so the CSV
                        # download (rendered on the next pass) includes
                        # this entry.
                        override_history.append({
                            "timestamp": datetime.utcnow().isoformat(timespec="seconds"),
                            "line_index": selected_idx,
                            "description": old_line.description,
                            "csi_division": old_line.csi_division,
                            "csi_section": old_line.csi_section or "",
                            "original_unit_cost": round(float(old_line.unit_cost), 2),
                            "new_unit_cost": round(float(new_line.unit_cost), 2),
                            "operator_note": formatted_note or "",
                        })
                        st.session_state["override_history"] = override_history
                        st.session_state["estimate"] = new_estimate
                        st.success(
                            f"Override applied to line #{selected_idx} "
                            f"(``{_t7_tier_label(new_line)}``, band "
                            f"``{new_line.cost_band.value}``). "
                            f"New total: ${new_line.total_cost:,.2f}."
                        )
                        st.caption(
                            _format_override_delta(
                                pre_override, new_estimate, selected_idx
                            )
                        )
                        st.rerun()

            # ----- Override history (read-only) ---------------------------

            if override_history or manual_override_lines:
                st.markdown("##### Override history")
                history_rows = []
                for entry in override_history:
                    history_rows.append({
                        "Timestamp (UTC)": entry["timestamp"],
                        "Line #": entry["line_index"],
                        "Description": entry["description"],
                        "Orig $": entry["original_unit_cost"],
                        "New $": entry["new_unit_cost"],
                        "Note": entry["operator_note"],
                    })
                if history_rows:
                    hist_df = pd.DataFrame(history_rows)
                    st.dataframe(
                        hist_df,
                        hide_index=True,
                        use_container_width=True,
                        column_config={
                            "Orig $": st.column_config.NumberColumn(format="$%.2f"),
                            "New $": st.column_config.NumberColumn(format="$%.2f"),
                        },
                    )
                else:
                    st.caption(
                        "No overrides applied in this session yet. (Manual "
                        "Override-tier rows below are from a prior pass.)"
                    )

                # CSV export — every MANUAL_OVERRIDE-tier line in the current
                # estimate, with the original unit cost pulled from the snapshot
                # when the index aligns. Audit-trail artefact for the project file.
                csv_rows: list[dict[str, Any]] = []
                history_by_idx = {
                    e["line_index"]: e for e in reversed(override_history)
                }
                for idx, li in enumerate(estimate.line_items):
                    if li.cost_source_tier != CostSourceTier.MANUAL_OVERRIDE:
                        continue
                    orig_uc: float = 0.0
                    if idx < len(estimate_original.line_items):
                        orig_uc = round(
                            float(estimate_original.line_items[idx].unit_cost), 2
                        )
                    last_entry = history_by_idx.get(idx)
                    csv_rows.append({
                        "timestamp": last_entry["timestamp"] if last_entry else "",
                        "line_index": idx,
                        "description": li.description,
                        "csi_division": li.csi_division,
                        "csi_section": li.csi_section or "",
                        "original_unit_cost": orig_uc,
                        "new_unit_cost": round(float(li.unit_cost), 2),
                        "operator_note": li.notes or "",
                    })
                csv_text = _build_override_history_csv(csv_rows)
                st.download_button(
                    "Download override history CSV",
                    data=csv_text,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_overrides.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    disabled=not csv_rows,
                    help=(
                        "Exports every ``MANUAL_OVERRIDE``-tier line "
                        "with original \u2192 new unit cost + operator note. "
                        "Disabled when no overrides are present."
                    ),
                )

                # Reset strategy: SINGLE GLOBAL "Reset all overrides"
                # button (per the brief's "pick the simpler option"
                # guidance). Restores the pre-override snapshot
                # captured at analyze time. A per-line stack-based
                # reset would require tracking the prior estimate per
                # override application and would push session-state
                # complexity past the simplification line for this
                # slice.
                if st.button(
                    "Reset all overrides (restore original estimate)",
                    use_container_width=True,
                    help=(
                        "Restores the pre-override estimate snapshot "
                        "captured when this analyze run completed. "
                        "Clears the override history."
                    ),
                ):
                    st.session_state["estimate"] = estimate_original.model_copy(
                        deep=True
                    )
                    st.session_state["override_history"] = []
                    st.success("All overrides reverted; history cleared.")
                    st.rerun()

        # ------------------------------------------------------------------
        # Phase T6.3 — Batch operator overrides from vendor CSV
        # ------------------------------------------------------------------
        #
        # Wires ``core.pricing.batch_override`` into the Streamlit Estimate
        # tab as the bulk-CSV analogue of the T6.2 single-line affordance.
        # Two-stage flow (preview → apply) is mandatory: the operator must
        # see the match plan BEFORE any override is applied, because a
        # batch op touches many lines at once and a mismatch in the fuzzy
        # matcher could otherwise nuke the entire estimate silently.
        #
        # Session-state keys consumed (already seeded by T6.2):
        #   - ``estimate_original`` — pre-override snapshot (for the
        #     reset path; this section does not touch it).
        #   - ``override_history``  — appended to on each successful
        #     batch apply so the existing T6.2 history download stays
        #     authoritative.
        #
        # New (transient) session-state keys this section introduces:
        #   - ``batch_override_plan`` — the most recent
        #     :class:`BatchOverridePlan` for preview rendering.
        #   - ``batch_override_csv_lines`` — the parsed
        #     :class:`BatchOverrideRow` list (kept for plan re-derivation
        #     when the operator re-runs with different thresholds).
        #   - ``batch_override_resolved`` — dict mapping CSV row index
        #     to operator-chosen CostLine index for AMBIGUOUS rows.
        with st.expander(
            "Batch operator overrides from vendor CSV (Phase T6.3)",
            expanded=False,
        ):
            st.caption(
                "Upload a vendor pricing CSV (description + unit_cost "
                "columns required; optional vendor / quote_ref / notes / "
                "quantity). The matcher fuzzy-aligns each row to a "
                "CostLine by description and surfaces a preview before "
                "any override is committed. MATCHED rows auto-apply; "
                "AMBIGUOUS rows wait for operator resolution; "
                "LOW_SIMILARITY and NO_MATCH rows are flagged for "
                "manual review and never auto-applied."
            )

            uploaded_csv = st.file_uploader(
                "Vendor pricing CSV",
                type=["csv"],
                key="batch_override_csv_uploader",
                help=(
                    "Required columns (any of the case-insensitive "
                    "aliases): description / desc / item / "
                    "item_description / line_item AND unit_cost / price / "
                    "unit_price / cost / $/unit / rate. Optional: "
                    "vendor, quote_ref, notes, quantity."
                ),
            )

            with st.expander("Matching settings (advanced)", expanded=False):
                similarity_threshold = st.slider(
                    "Similarity threshold",
                    min_value=0.40,
                    max_value=0.95,
                    value=0.65,
                    step=0.01,
                    key="batch_override_threshold",
                    help=(
                        "Minimum description-similarity for a row to "
                        "be considered MATCHED or AMBIGUOUS. Below this "
                        "and above 0.40 lands in LOW_SIMILARITY (manual "
                        "review). Below 0.40 lands in NO_MATCH. Default "
                        "0.65 aligns with the Phase T6 OPERATOR_REVIEW "
                        "band boundary."
                    ),
                )
                ambiguity_margin = st.slider(
                    "Ambiguity margin",
                    min_value=0.05,
                    max_value=0.30,
                    value=0.10,
                    step=0.01,
                    key="batch_override_margin",
                    help=(
                        "Two CostLines whose similarities to the same "
                        "CSV row are within this margin are flagged "
                        "AMBIGUOUS and require operator resolution. "
                        "Default 0.10 distinguishes 'walls vs. ceiling' "
                        "(amb.) from 'Door 101A vs. 201A' (auto-resolved)."
                    ),
                )

            preview_clicked = st.button(
                "Preview match plan",
                use_container_width=True,
                disabled=uploaded_csv is None,
                key="batch_override_preview_btn",
                help=(
                    "Parse the CSV + build the match plan. Does NOT "
                    "apply any overrides. Required before the Apply "
                    "button activates."
                ),
            )

            if preview_clicked and uploaded_csv is not None:
                try:
                    raw_bytes = uploaded_csv.getvalue()
                    csv_text = raw_bytes.decode("utf-8-sig")
                except Exception as exc:
                    st.error(f"Could not decode CSV: {exc}")
                else:
                    try:
                        parsed_rows, parse_errors = parse_vendor_csv(csv_text)
                    except ValueError as exc:
                        st.error(f"CSV parse failed: {exc}")
                        parsed_rows, parse_errors = [], []
                    if parse_errors:
                        for err in parse_errors:
                            st.warning(err)
                    if parsed_rows:
                        plan = match_cost_lines(
                            parsed_rows,
                            list(estimate.line_items),
                            similarity_threshold=float(similarity_threshold),
                            ambiguity_margin=float(ambiguity_margin),
                        )
                        st.session_state["batch_override_plan"] = plan
                        st.session_state["batch_override_csv_lines"] = parsed_rows
                        st.session_state["batch_override_resolved"] = {}

            plan: BatchOverridePlan | None = st.session_state.get(
                "batch_override_plan"
            )
            if plan is not None:
                summary = _summarize_batch_plan(plan, estimate)
                m1, m2, m3, m4, m5 = st.columns(5)
                m1.metric("Total rows", summary["total_rows"])
                m2.metric("Matched", summary["matched_count"])
                m3.metric("Ambiguous", summary["ambiguous_count"])
                m4.metric("Low similarity", summary["low_similarity_count"])
                m5.metric("No match", summary["no_match_count"])
                adj = summary["estimated_total_adjustment"]
                adj_sign = "+" if adj >= 0 else "\u2212"
                st.caption(
                    f"Estimated subtotal adjustment if all MATCHED rows "
                    f"are applied: {adj_sign}${abs(adj):,.2f}."
                )

                if plan.matched:
                    st.markdown("##### Matched rows (auto-apply)")
                    matched_rows = []
                    for result in plan.matched:
                        if result.best_match_index is None:
                            continue
                        line = estimate.line_items[result.best_match_index]
                        matched_rows.append({
                            "CSV row": result.row.row_index,
                            "CSV description": result.row.description,
                            "Cost line #": result.best_match_index,
                            "Cost line description": line.description,
                            "Sim": round(result.best_match_similarity, 3),
                            "Old $/unit": round(float(line.unit_cost), 2),
                            "New $/unit": round(float(result.row.unit_cost), 2),
                        })
                    if matched_rows:
                        st.dataframe(
                            pd.DataFrame(matched_rows),
                            hide_index=True,
                            use_container_width=True,
                            column_config={
                                "Old $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                                "New $/unit": st.column_config.NumberColumn(
                                    format="$%.2f"
                                ),
                            },
                        )

                if plan.ambiguous:
                    st.markdown("##### Ambiguous rows (operator resolution required)")
                    resolved: dict[int, int] = st.session_state.get(
                        "batch_override_resolved", {}
                    )
                    for result in plan.ambiguous:
                        candidates: list[tuple[str, int | None]] = [
                            ("Skip this row", None),
                        ]
                        for idx, sim in result.candidate_lines:
                            if 0 <= idx < len(estimate.line_items):
                                desc = estimate.line_items[idx].description[:60]
                                candidates.append(
                                    (f"#{idx} | {desc} | sim={sim:.2f}", idx)
                                )
                        labels = [label for label, _ in candidates]
                        current_choice = resolved.get(result.row.row_index)
                        default_index = 0
                        for i, (_, idx) in enumerate(candidates):
                            if idx == current_choice:
                                default_index = i
                                break
                        chosen_label = st.selectbox(
                            f"Row {result.row.row_index}: "
                            f"{result.row.description[:80]}",
                            options=labels,
                            index=default_index,
                            key=f"batch_amb_resolve_{result.row.row_index}",
                        )
                        chosen_idx = dict(candidates)[chosen_label]
                        if chosen_idx is None:
                            resolved.pop(result.row.row_index, None)
                        else:
                            resolved[result.row.row_index] = chosen_idx
                    st.session_state["batch_override_resolved"] = resolved

                unmatched = list(plan.low_similarity) + list(plan.no_match)
                if unmatched:
                    st.markdown("##### Unmatched rows (read-only audit)")
                    unmatched_rows = []
                    for result in unmatched:
                        unmatched_rows.append({
                            "CSV row": result.row.row_index,
                            "CSV description": result.row.description,
                            "Best sim": round(result.best_match_similarity, 3),
                            "Status": result.status.value,
                            "Notes": result.row.notes or "",
                        })
                    st.dataframe(
                        pd.DataFrame(unmatched_rows),
                        hide_index=True,
                        use_container_width=True,
                    )

                plan_csv = export_match_plan_csv(plan, list(estimate.line_items))
                st.download_button(
                    "Download match plan CSV",
                    data=plan_csv,
                    file_name=(
                        f"{estimate.project_name.replace(' ', '_')}"
                        f"_batch_match_plan.csv"
                    ),
                    mime="text/csv",
                    use_container_width=True,
                    key="batch_override_plan_download",
                    help=(
                        "Audit-trail snapshot of the match plan: per-row "
                        "status, best + runner-up similarity, candidate "
                        "descriptions. Useful for offline review before "
                        "committing the batch."
                    ),
                )

                apply_clicked = st.button(
                    "Apply batch overrides",
                    use_container_width=True,
                    type="primary",
                    key="batch_override_apply_btn",
                    disabled=(
                        len(plan.matched) == 0
                        and not st.session_state.get(
                            "batch_override_resolved", {}
                        )
                    ),
                    help=(
                        "Applies every MATCHED row + every operator-"
                        "resolved AMBIGUOUS row. LOW_SIMILARITY and "
                        "NO_MATCH rows are always skipped. Updates the "
                        "estimate in place and appends to the override "
                        "history."
                    ),
                )

                if apply_clicked:
                    resolved_map: dict[int, int] = st.session_state.get(
                        "batch_override_resolved", {}
                    )
                    pre_apply = estimate
                    try:
                        new_estimate, apply_summary = apply_batch_plan(
                            estimate,
                            plan,
                            auto_apply_matched=True,
                            resolved_ambiguous=resolved_map,
                        )
                    except Exception as exc:
                        st.error(f"Batch apply failed: {exc}")
                    else:
                        applied_results: list[BatchMatchResult] = list(plan.matched)
                        for result in plan.ambiguous:
                            if result.row.row_index in resolved_map:
                                # Forge a synthesised result with the
                                # resolved index in best_match_index so
                                # the history row points at the line the
                                # override actually touched.
                                applied_results.append(BatchMatchResult(
                                    row=result.row,
                                    status=BatchMatchStatus.MATCHED,
                                    best_match_index=resolved_map[
                                        result.row.row_index
                                    ],
                                    best_match_similarity=(
                                        result.best_match_similarity
                                    ),
                                    runner_up_index=result.runner_up_index,
                                    runner_up_similarity=(
                                        result.runner_up_similarity
                                    ),
                                    candidate_lines=result.candidate_lines,
                                ))

                        now_ts = datetime.utcnow().isoformat(timespec="seconds")
                        for result in applied_results:
                            if result.best_match_index is None:
                                continue
                            if not 0 <= result.best_match_index < len(
                                pre_apply.line_items
                            ):
                                continue
                            old_line = pre_apply.line_items[
                                result.best_match_index
                            ]
                            new_line = new_estimate.line_items[
                                result.best_match_index
                            ]
                            note = format_batch_operator_note(result.row)
                            override_history.append({
                                "timestamp": now_ts,
                                "line_index": result.best_match_index,
                                "description": old_line.description,
                                "csi_division": old_line.csi_division,
                                "csi_section": old_line.csi_section or "",
                                "original_unit_cost": round(
                                    float(old_line.unit_cost), 2
                                ),
                                "new_unit_cost": round(
                                    float(new_line.unit_cost), 2
                                ),
                                "operator_note": note,
                            })

                        st.session_state["override_history"] = override_history
                        st.session_state["estimate"] = new_estimate
                        st.session_state.pop("batch_override_plan", None)
                        st.session_state.pop("batch_override_csv_lines", None)
                        st.session_state.pop("batch_override_resolved", None)

                        applied_count = sum(
                            1 for line in apply_summary
                            if line.startswith("Row") and "APPLIED" in line
                        )
                        st.success(
                            f"Batch override applied: {applied_count} line"
                            f"{'s' if applied_count != 1 else ''} updated. "
                            f"Subtotal: ${pre_apply.subtotal:,.2f} "
                            f"\u2192 ${new_estimate.subtotal:,.2f}."
                        )
                        with st.expander("Apply summary (full log)", expanded=False):
                            for line in apply_summary:
                                st.text(line)
                        st.rerun()

        st.divider()
        st.subheader("Project totals")
        c1, c2 = st.columns(2)
        c1.write(
            f"**Subtotal:** ${estimate.subtotal:,.2f}\n\n"
            f"**Contingency ({estimate.contingency_pct:.1f}%):** ${estimate.contingency:,.2f}\n\n"
            f"**Overhead ({estimate.overhead_pct:.1f}%):** ${estimate.overhead:,.2f}\n\n"
            f"**Profit ({estimate.profit_pct:.1f}%):** ${estimate.profit:,.2f}\n\n"
            f"### **GRAND TOTAL: ${estimate.grand_total:,.2f}**"
        )
        with c2:
            st.write("**Download**")
            xlsx_bytes = export_estimate_xlsx(estimate, project, csi_titles, extractions)
            st.download_button(
                "Download Excel (.xlsx)",
                data=xlsx_bytes,
                file_name=f"{estimate.project_name.replace(' ', '_')}_estimate.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                use_container_width=True,
            )
            json_str = export_estimate_json(estimate, project)
            st.download_button(
                "Download JSON",
                data=json_str,
                file_name=f"{estimate.project_name.replace(' ', '_')}_estimate.json",
                mime="application/json",
                use_container_width=True,
            )

    # --- By Division ---
    with tabs[6]:
        rows = []
        for div, total in sorted(estimate.by_division.items()):
            rows.append({
                "Div": div,
                "Title": csi_titles.get(div, ""),
                "Subtotal": total,
                "% of subtotal": (total / estimate.subtotal * 100) if estimate.subtotal else 0.0,
            })
        df_div = pd.DataFrame(rows)
        if df_div.empty:
            st.info("No priced lines.")
        else:
            st.dataframe(
                df_div,
                hide_index=True,
                use_container_width=True,
                column_config={
                    "Subtotal":     st.column_config.NumberColumn(format="$%.2f"),
                    "% of subtotal": st.column_config.ProgressColumn(
                        format="%.1f%%", min_value=0.0, max_value=100.0,
                    ),
                },
            )
            st.bar_chart(df_div.set_index("Div")["Subtotal"])

    # --- Sheets ---
    with tabs[7]:
        st.subheader("Sheet inventory")

        # F3 — drawing-prepass coverage tile. Only meaningful when there
        # are drawing sheets in the run; the bundle path is unaffected.
        sheet_extractions = [
            e for e in extractions
            if any(e.sheet_id == s.sheet_id for s in sheets)
        ]
        if sheet_extractions:
            skipped = sum(1 for e in sheet_extractions if e.lm_skipped)
            total = len(sheet_extractions)
            pct = (skipped / total * 100.0) if total else 0.0
            qt1, qt2, qt3 = st.columns(3)
            qt1.metric("Prepass-only (LLM skipped)", f"{skipped} / {total}", f"{pct:.0f}%")
            qt2.metric("LLM-augmented", str(total - skipped))
            qt3.caption(
                "\u26A1 = deterministic pre-pass cleared the confidence "
                "threshold; \U0001F916 = vision-LLM ran with pre-pass "
                "context. The pre-pass extracts title block, dimensions "
                "and schedule tables straight from the PDF's vector text."
            )

        for sheet in sheets:
            extraction = next(
                (e for e in extractions if e.sheet_id == sheet.sheet_id),
                None,
            )
            icon = "\u26A1" if (extraction and extraction.lm_skipped) else "\U0001F916"
            with st.expander(
                f"{icon} {sheet.sheet_id} - {sheet.title or '(no title)'} "
                f"[{sheet.discipline} / {sheet.sheet_type}]",
                expanded=False,
            ):
                cols = st.columns([2, 3])
                with cols[0]:
                    if sheet.image_path and Path(sheet.image_path).exists():
                        st.image(sheet.image_path, use_container_width=True)
                with cols[1]:
                    summary = extraction.summary if extraction else ""
                    st.write(f"**Source PDF:** {sheet.pdf_name} (page {sheet.page_index + 1})")
                    st.write(f"**Discipline:** {sheet.discipline}")
                    st.write(f"**Sheet type:** {sheet.sheet_type}")
                    st.write(f"**Scale:** {sheet.scale or 'unknown'}")
                    if extraction:
                        if extraction.lm_skipped:
                            st.success(
                                "\u26A1 LLM skipped — deterministic "
                                "pre-pass extracted this sheet."
                            )
                        elif extraction.prepass is not None:
                            st.caption(
                                "\U0001F916 LLM ran with pre-pass context "
                                f"(confidence {extraction.prepass.confidence:.2f})."
                            )
                    st.write("**Summary:**")
                    st.write(summary or "(no summary)")
                    if extraction and extraction.prepass is not None:
                        with st.popover("Prepass details"):
                            tb = extraction.prepass.title_block
                            st.write(f"**Title block:** {tb.model_dump()}")
                            st.write(f"**Confidence:** {extraction.prepass.confidence:.2f}")
                            st.write(f"**Dimensions:** {len(extraction.prepass.dimensions)}")
                            st.write(f"**Schedules:** {len(extraction.prepass.schedules)}")
                            if extraction.prepass.quality_issues:
                                st.warning("\n".join(
                                    f"- {q}" for q in extraction.prepass.quality_issues
                                ))

    # --- Rooms ---
    with tabs[8]:
        if not project.rooms:
            st.info("No rooms identified.")
        else:
            st.dataframe(
                pd.DataFrame([r.model_dump() for r in project.rooms]),
                hide_index=True,
                use_container_width=True,
            )

    # --- Doors / Windows ---
    with tabs[9]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Doors ({len(project.doors)})")
            if project.doors:
                st.dataframe(
                    pd.DataFrame([d.model_dump() for d in project.doors]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No doors identified.")
        with c2:
            st.subheader(f"Windows ({len(project.windows)})")
            if project.windows:
                st.dataframe(
                    pd.DataFrame([w.model_dump() for w in project.windows]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No windows identified.")

    # --- Structural / MEP ---
    with tabs[10]:
        c1, c2 = st.columns(2)
        with c1:
            st.subheader(f"Structural ({len(project.structural)})")
            if project.structural:
                st.dataframe(
                    pd.DataFrame([s.model_dump() for s in project.structural]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No structural items identified.")
        with c2:
            st.subheader(f"MEP ({len(project.mep)})")
            if project.mep:
                st.dataframe(
                    pd.DataFrame([m.model_dump() for m in project.mep]),
                    hide_index=True, use_container_width=True,
                )
            else:
                st.info("No MEP items identified.")

    # --- Specs ---
    with tabs[11]:
        if not project.spec_sections:
            st.info("No specification sections identified.")
        else:
            for spec in sorted(project.spec_sections, key=lambda s: s.csi_section):
                with st.expander(f"{spec.csi_section} - {spec.title}", expanded=False):
                    if spec.summary:
                        st.write(spec.summary)
                    if spec.requirements:
                        st.write("**Requirements:**")
                        for req in spec.requirements:
                            st.write(f"- {req}")
                    if spec.source_sheet_id:
                        st.caption(f"Source: {spec.source_sheet_id}")

    # --- Raw takeoffs ---
    with tabs[12]:
        if not project.takeoffs:
            st.info("No raw takeoffs.")
        else:
            df_t = pd.DataFrame([t.model_dump() for t in project.takeoffs])
            df_t["source_sheet_ids"] = df_t["source_sheet_ids"].apply(lambda xs: ", ".join(xs))
            st.dataframe(df_t, hide_index=True, use_container_width=True)

    # --- Warnings ---
    with tabs[13]:
        if not project.warnings:
            st.success("No warnings.")
        else:
            for w in project.warnings:
                st.warning(w)

    # --- Client Quote (F12 + F15) ---
    with tabs[14]:
        _render_client_quote_tab(estimate, project, csi_titles)

else:
    st.info(
        "Upload one or more plan-set PDFs in the sidebar and click "
        "**Analyze plan set** to begin."
    )
    with st.expander("How it works", expanded=True):
        st.markdown(
            """
            1. **Split + render.** Each PDF page becomes one sheet, rendered at the
               configured DPI for the vision model.
            2. **Classify.** A title-block heuristic (sheet number / keyword in
               embedded text) handles the easy cases; the vision LLM picks up the
               rest.
            3. **Extract.** Each sheet is routed to a discipline-specific
               extractor (architectural, structural, MEP, schedule, spec, site).
               Returns strict JSON matching our schema.
            4. **Reconcile.** Rooms, doors, windows, fixtures and specs are
               de-duplicated across sheets - the floor plan and the schedule
               agree on one row per item.
            5. **Price.** Each takeoff is matched against
               `config/cost_database.json` (exact CSI section first, then
               keyword fallback within the same division).
            6. **Review and edit.** Every line is editable in the table.
               Recalculate totals and download Excel / JSON when you're happy.
            """
        )
