# Calibration v4 — operator pre-flight checklist

Standalone version of [`docs/CALIBRATION_V4_PLAN.md`](./CALIBRATION_V4_PLAN.md) §5.
Tick each box as you complete it. Hard-blockers are marked `**HARD**`.

## Environment

- [ ] LLM API key in `.env` (either `OPENAI_API_KEY` for `gpt-4o` OR `ANTHROPIC_API_KEY` for Claude)
- [ ] `pip install -r requirements.txt` runs clean
- [ ] `python -m pip check` reports no broken dependencies
- [ ] `.\.venv\Scripts\python -m pytest -q` is green — record the test count: `_____ passed, _____ skipped`
- [ ] Confirm Workers TT (Phase T6.4.a multi-sheet xlsx) and UU (Phase T6.4.c.2 manual-override tag) have both landed on `main`; verify with `git log --oneline | head -20`
- [ ] **HARD** — confirm the working tree is clean. `git status` reports no modified or untracked files outside `exports/calibration_v4/`

## Calibration bid set

- [ ] All 6 primary bundles' source PDFs are present in `inbox/opportunities/attachments/2026-05-21/` (or its named subdirectory). Slugs:
  - [ ] `angelo-state-carr-efa-26-007` (11 PDFs at folder root)
  - [ ] `chs-cafeteria-2026-0608-01` (2 PDFs at folder root)
  - [ ] `pais-cabin-140P6026Q0029` (2 PDFs at folder root)
  - [ ] `usfws-san-marcos-140FC126R0017` (1 PDF at folder root)
  - [ ] `tamu-harrington-2025-06813` (1 PDF at folder root)
  - [ ] `cmd-post-ndi-W50S7626QA001` (7 PDFs in `Command_Post_and_Nondestructive_Inspection_Room_Renovations/` subfolder)
- [ ] (Optional) Stretch bundles available — see plan §2.2 for `b1710-office-refurb-FA667526Q0002`, `tamu-wehner-fin-340E-2025-06871`, `leroy-moore-gym-PV-0749-PV-0753`

## Pricing setup

- [ ] Cost database refreshed (`python scripts/refresh_pricing.py`) OR skip noted in the run report
- [ ] Region multiplier per bundle confirmed (Davis-Bacon bundles default to `1.10`; commercial TX defaults to `1.00`)
- [ ] Overhead / profit / contingency defaults realistic (`--contingency 10 --overhead 10 --profit 5` baseline; federal raises overhead to 12 %)

## Output directory

- [ ] **HARD** — backup the prior v3 exports: `Copy-Item -Recurse exports\calibration_v3 exports\_archive_calibration_v3_b0dd955`
- [ ] Create `exports/calibration_v4/`
- [ ] Create `exports/calibration_v4/GROUND_TRUTH/<bid_slug>/` for each of the 6 primary slugs

## Ground truth collection (per bundle, before the run)

- [ ] Schedules — for each bundle with drawing PDFs, manually count rows per family (door / window / finish / room / panel / lighting / HVAC / plumbing / kitchen / lab / AV / security). Save `GROUND_TRUTH/<slug>/schedules.md`
- [ ] Alternates — for each bundle with a bid form / RFCSP, list every Alternate / Bid Alternate / VE / CLIN option. Save `GROUND_TRUTH/<slug>/alternates.md`
- [ ] Sub-quotes — for PAIS Cabin (recommended), construct a 5–8-row synthetic vendor quote PDF; save `GROUND_TRUTH/pais-cabin-140P6026Q0029/synthetic_subquote.pdf` and `synthetic_subquote.md`
- [ ] Pricing reference — note where pricing ground truth will come from (post-award contracts / RSMeans free trial / AGC published / FEMA-GSA-NAHB-USACE). Recorded in the run-prep notes

## Run

- [ ] Save the suggested `scripts/run_calibration_v4.ps1` skeleton from plan §D (the script itself is not committed; the operator pastes / saves it)
- [ ] **HARD** — for each primary bundle, run `analyze.py` per the per-bundle dispatch in the script. Capture stdout to `exports/calibration_v4/<bid_slug>/analyze_stdout.log`
- [ ] Verify per-bundle outputs exist: `estimate.xlsx`, `estimate.json`, `quote.pdf`, `run_log.txt`
- [ ] Open the Streamlit UI for the 2–3 bundles that surfaced alternates; tick alternates on the "Bid Alternates" tab; click "Download client quote PDF" — this exercises the T9.3 session-state → PDF round-trip. Save the resulting PDF as `exports/calibration_v4/<bid_slug>/quote_with_alternates.pdf`

## Sub-quote / vendor-CSV / manual-override exercises

- [ ] T8.1 tabular sub-quote — upload the synthetic vendor PDF from ground-truth into the Streamlit "Sub-quotes" path; confirm `[sub-quote]` reaches `CostLine.notes[0]` in the resulting Excel + PDF + JSON
- [ ] T8.2 LLM-vision sub-quote — force the deterministic parser to fail on a scanned page; confirm "Try LLM extraction" path produces rows; confirm `[sub-quote-llm]` reaches `CostLine.notes[0]`
- [ ] T6.3 vendor CSV — upload a 5-row vendor CSV; confirm `[vendor-csv]` reaches `CostLine.notes[0]`
- [ ] T6.1 manual override — apply a single-line override via the "Override unit cost" affordance; confirm `[manual-override]` reaches `CostLine.notes[0]`
- [ ] T6.3 default batch — apply a batch override without an explicit source tag; confirm `[batch]` reaches `CostLine.notes[0]`

## Verification (per the plan §3 measurement schema)

- [ ] Document-classifier accuracy ≥ 95 % across bundles
- [ ] Schedule recall ≥ 80 % per family per bundle (averaged)
- [ ] **HARD** — zero LF×SF cross-applications APPLIED (warnings OK)
- [ ] **HARD** — every applied override has the correct tag at `CostLine.notes[0]` across all 4 surfaces (Excel, JSON, PDF, Streamlit)
- [ ] **HARD** — `combined_confidence = qty_conf × price_conf` invariant holds on 100 % of lines
- [ ] **HARD** — re-run of one bundle produces byte-identical deterministic-stage `estimate.xlsx` + `estimate.json`
- [ ] Suppressed-line count + total $ contribution recorded; suppressed total contributes $0 to subtotal
- [ ] Confidence-band distribution recorded (AUTO_APPROVE / OPERATOR_REVIEW / HAND_TAKEOFF %)
- [ ] Cost-source-tier distribution recorded (EXACT_MATCH / CATEGORY_MATCH / INTERPOLATED / PARAMETRIC / MISSING %)
- [ ] LLM cost ≤ $1.00 total across the 6 primary bundles
- [ ] Wall-clock ≤ 15 min per bundle, ≤ 90 min total for the 6 primary
- [ ] Zero pipeline hard failures

## Reporting

- [ ] Compile `exports/calibration_v4/CALIBRATION_REPORT.md` per the plan §3 + §C audit notes (use v3 report as the template)
- [ ] Generate the companion `exports/calibration_v4/calibration_v4_metrics.json` (machine-readable; the §3 measurement table flattened per bundle)
- [ ] Diff against v3 — note regressions, note improvements
- [ ] Commit + push the report + metrics JSON. Suggested message: `docs: Phase T10 - calibration v4 report (6 bundles, full T6/T7/T8/T9 stack)`

## Post-run

- [ ] Decide on T6.4.d (per-line override undo) vs T6.4.e (markup knob) vs cost-DB expansion (`par_costdb_expand`) for the next slice — informed by which divisions ended up MISSING-tier-heaviest in the v4 metrics
- [ ] Open backlog issues for any soft-warning patterns that recurred across ≥ 2 bundles
- [ ] If any HARD check failed, file a regression issue with the specific bundle + the failing metric; do NOT mark v4 complete until the regression is closed
