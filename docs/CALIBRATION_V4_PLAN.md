# Phase T10 — Calibration v4 pre-flight plan

**Document type:** docs-only deliverable. Pre-flight plan + measurement matrix + ground-truth strategy for the first end-to-end calibration run with the full T6.x / T7 / T8.x / T9.x stack active. Authored by Worker VV; executed (separately) by an operator user action once the T6.4 polish bundle closes.

**Companion file:** [`docs/CALIBRATION_V4_CHECKLIST.md`](./CALIBRATION_V4_CHECKLIST.md) is the standalone operator checklist extracted from §5 below.

**Baseline reference docs:**

- [`exports/calibration_v3/CALIBRATION_REPORT.md`](../exports/calibration_v3/CALIBRATION_REPORT.md) — the most recent SHIPPED run (commit `f92f2dc`-era; 17 PDFs / 16 bundles / 4m35s / ~$0.55)
- [`exports/calibration_v2/CALIBRATION_REPORT.md`](../exports/calibration_v2/CALIBRATION_REPORT.md) — the Q1–Q7 framework v4 is a strict superset of

**Repo head at authoring:** post-`b0dd955` (T6.4.b unit-aware matching). Two follow-up commits from Worker TT (Phase T6.4.a multi-sheet xlsx) and Worker UU (Phase T6.4.c.2 manual-override tag) are in flight; v4 should run only AFTER both land.

---

## 1. Executive summary

Calibration v4 is the first end-to-end run with the **full T6 / T7 / T8 / T9 stack** active end-to-end. v3 surfaced and closed three deterministic-stage bugs (LLM 429 retry, BID_FORM short-circuit, unit-mismatch suppression) on a 17-PDF mixed-opportunity folder; v4 will exercise the **operator-facing override + sub-quote + alternates surfaces** that have shipped on top of that baseline (T6.1 / T6.2 / T6.3 / T6.4.a-c, T7, T8.1 / T8.2, T9.0 / T9.1 / T9.2 / T9.3) plus the 9 typed schedule extractors from the T2.x family.

We expect to learn: (a) whether bid-form alternates extract deterministically on real bid forms or fall back to the LLM path; (b) whether T6.4.b's UoM safety net catches any real LF×SF cross-application risks in calibration bundles; (c) whether source-tag provenance (`[batch]` / `[vendor-csv]` / `[sub-quote]` / `[sub-quote-llm]` / `[manual-override]`) propagates byte-correctly to `CostLine.notes` position 0 across every downstream surface (Excel, JSON, client PDF); (d) how much of the cost-DB's 128 entries cover the schedules our extractors emit. **LLM budget: ≤ $1.00 total** (v3 was $0.55 on 16 bundles; v4 adds T9 alternates fallback). **Time budget: ≤ 15 min per bundle** (v3 was 4m35s on the whole folder). **Go/no-go:** §7 below.

## 2. Calibration bid set

### 2.1 Source-of-truth audit

The canonical calibration input set lives at **`inbox/opportunities/attachments/2026-05-21/`** — the same folder v1 / v2 / v3 consumed. Audit (one Get-ChildItem):

- **27 PDFs at the folder root** covering ~6 distinct opportunities + boilerplate attachments + wage determinations
- **1 `.docx`** (`B08_Solicitation_-_Att_1_-_Specifications.docx`) silently ignored by `analyze.py`
- **4 subdirectories**: `Command_Post_and_Nondestructive_Inspection_Room_Renovations/` (7 files), `potentialsolicitationsforrkresidentialhomesandcommerc/` (0 files), `potentialsols/` (18 files), `tamu-csp/` (5 files) — these supply the **B1710** / **TAMU-Wehner** / **Cmd-Post-NDI** workspaces that have their own `bids/<slug>/` shells but were never wired into the v1–v3 inbox-flat runs

The `bids/` directory carries **9 active workspaces** (plus `_NO_GO`, `_TEMPLATES`, `_WATCHLIST` shells). Workspaces map to opportunities in the attachments folder as follows:

| Bid slug | Opportunity | Source PDFs (in `inbox/opportunities/attachments/2026-05-21/`) | In v3 set? |
|---|---|---|---|
| `angelo-state-carr-efa-26-007` | Carr EFA Dressing Room Renovation #26-007 — Angelo State / TX | 11 PDFs (RFCSP + Project Manual + Drawings Addendum 1/2/3.27.26 compressed + Attachments A/B.2/C/D/E/F.1 + Addendum #1) | ✓ |
| `chs-cafeteria-2026-0608-01` | CHS Cafeteria Serving Line Renovation — TX | 2 PDFs (`CHS Serving Line Renovation.pdf` + `ESBD_518571_..._RFCSP 2026-0608-01...pdf`) | ✓ |
| `pais-cabin-140P6026Q0029` | PAIS Cabin Roof / Sol_140P6026Q0029 (NPS) | 2 PDFs (`Sol_140P6026Q0029.pdf` + `Sol_140P6026Q0029_Amd_0001.pdf`) | ✓ |
| `usfws-san-marcos-140FC126R0017` | USFWS San Marcos Aquatic Resources Centre / 140FC126R0017 | 1 PDF (`Sol_140FC126R0017.pdf`) | ✓ |
| `tamu-harrington-2025-06813` | Harrington Lab 303 Notice of Project / ESBD_514190 | 1 PDF (`ESBD_514190_..._2025-06813_Notice of Project-CS_26.05.08.pdf`) | ✓ |
| `cmd-post-ndi-W50S7626QA001` | Command Post + NDI Room Renovations | 7 PDFs (subfolder `Command_Post_and_Nondestructive_Inspection_Room_Renovations/`) | ✗ (subfolder skipped by flat-recursive v3 path; needs explicit pointing) |
| `b1710-office-refurb-FA667526Q0002` | B1710 Office Refurb — USAF | (in `potentialsols/`, requires per-bundle pull) | ✗ |
| `tamu-wehner-fin-340E-2025-06871` | TAMU Wehner Finance 340E Renovation | (in `tamu-csp/`) | ✗ |
| `leroy-moore-gym-PV-0749-PV-0753` | Leroy Moore Gym / PV-0749 + PV-0753 | (not in 2026-05-21 attachments folder; operator must locate) | ✗ |

Additional v3-set items NOT in any active bid workspace:

- **`Bid_Schedule_San_Marcos_*.pdf`** — the 8-line unit-price bid schedule v3 used to verify the BID_FORM repair. Conceptually paired with `usfws-san-marcos-140FC126R0017` (San Marcos in the file name) but actually came in via the v3 mixed-folder run.
- **`SOW_-_Final_-_San_Marcos_*.pdf`** — 8 inclusions; the SOW the v2 voter quoted.
- **`SAM_-_Davis-Bacon_Act_WD_TX20260254__Hays_County__Building.pdf`** + **`B08_Solicitation_-_Att_3_-_DOL_Wage_Determination.pdf`** — Davis-Bacon wage determinations, no bid signal.
- **`B08_Solicitation_-_Att_2_-_Drawings.pdf`** — 1-page floor plan; v3's only drawing-sheet path through the deterministic classifier.

### 2.2 Recommended v4 bundle set: **6 bids (primary) + 3 stretch goals**

| # | Bid slug | Why this run | Expected extractors fire |
|---|---|---|---|
| 1 | `angelo-state-carr-efa-26-007` | Largest single-opportunity bundle (11 PDFs / 311 p RFCSP). Anchor for project-info voter coherency, T8.1 sub-quote ingestion (if vendor PDFs ship later), T9.0 alternates extraction (RFCSPs typically carry CLIN-option alternates). | Schedule families: doors (likely), finishes (likely), rooms; LLM-stage retry budget; project-info voter; full alternates extraction path |
| 2 | `chs-cafeteria-2026-0608-01` | v2 / v3's strongest extraction (7 inclusions + 3 exclusions). Sanity check for scope-coverage aggregation regressions. | Schedule families: kitchen (T2.10), finishes, alternates (likely); scope-matrix |
| 3 | `pais-cabin-140P6026Q0029` | NPS PAIS-format solicitation with CLIN options — best deterministic candidate for T9.0 alternates extraction. Known external vendor quote possible (roofing) → T8.1 sub-quote candidate. | Alternates (deterministic priority); T8.1 if vendor quote attached |
| 4 | `usfws-san-marcos-140FC126R0017` | USFWS solicitation — second-largest LLM-stage exercise after Carr EFA. Pair with the **San Marcos Bid Schedule** (Sched: 8 unit prices) for end-to-end unit_prices extraction. | LLM retry; BID_FORM extraction; possible alternates |
| 5 | `tamu-harrington-2025-06813` | 1-page Notice of Project. Boundary case — minimal text, no schedules. Validates that the LLM-stage 200-char skip threshold still fires correctly post-T8/T9. | Voter only; no schedules; no alternates |
| 6 | `cmd-post-ndi-W50S7626QA001` | 7-PDF subfolder bundle (was NOT in v3's flat-recursive sweep). Adds a new opportunity to the calibration superset without re-shuffling v3 coverage. | TBD on first run; expected: doors, finishes, possibly HVAC |

**Stretch (run only if budget + wall-clock allow):**

| # | Bid slug | Why this is stretch, not primary |
|---|---|---|
| 7 | `b1710-office-refurb-FA667526Q0002` | Carpentry-heavy USAF refurb. Best T8.1 candidate (carpentry vendor quotes known to circulate for this opportunity). Stretch because no v3 baseline exists. |
| 8 | `tamu-wehner-fin-340E-2025-06871` | TAMU Finance renovation; AV / security / lab fixtures expected (T2.10 / T2.11 exercise). Stretch because the source PDFs need re-curating from `tamu-csp/`. |
| 9 | `leroy-moore-gym-PV-0749-PV-0753` | Gymnasium scope — exercise the T2.x trifecta (panel + lighting + HVAC). Stretch because attachments are not in the 2026-05-21 folder. |

### 2.3 T9 alternates calibration candidates (bid-form alternates)

Best candidates for exercising the T9.0 deterministic + LLM-fallback alternates path:

- **Carr EFA Attachment A** (`ESBD_516718_..._Attachment A.pdf`, 4 p) — RFCSP proposal form; v3 already extracted 1 allowance line. Likely to carry 2–4 Alternate / VE bullets.
- **PAIS Cabin `Sol_140P6026Q0029.pdf`** — NPS solicitations use CLIN-option layouts that the T9.0 deterministic extractor's bid-form patterns should recognise as alternates. Highest-value test of the deterministic path.
- **CHS Cafeteria RFCSP** — RFCSP layouts vary by district; if explicit "Bid Alternate 1 — Add stainless backsplash" sections appear in the PDF, this is the cleanest deterministic-extraction case.
- **San Marcos Bid Schedule** (1 p) — pure unit-price table; the T9.0 extractor should correctly distinguish this as a base-bid schedule (NOT alternates) and emit zero alternate rows. Negative-case test.

If the deterministic extractor returns < 2 alternates per RFCSP-containing bundle (expected: ≥ 1 per Carr EFA / PAIS / CHS), the LLM fallback is the path to verify. The LLM-fallback path can spike LLM cost; budget §6 accounts for this.

### 2.4 T8 sub-quote calibration candidates

Real vendor sub-quotes are not bundled into the public solicitation PDFs. For T8.1 / T8.2 calibration, the operator needs to either:

1. **Locate known external vendor quotes** for the calibration opportunities. The PAIS Cabin roofing scope has historically attracted Carlisle / Firestone roofing quotes; B1710 carpentry has Henrybuilt-style quotes. Operator-collected PDFs go into `data/calibration_v4/sub_quotes/<bid_slug>/` (folder to create at run time; not committed).
2. **Synthesise a representative vendor quote** from the SOW line items (e.g. for the San Marcos SOW's 8 inclusions, produce an 8-row vendor PDF with realistic per-LF / per-EA / per-JOB pricing) and run it through the T8.1 tabular path. This is the cheapest deterministic-path verification.
3. **For T8.2 LLM-vision fallback verification:** scan one synthesised quote, force `parse_subquote_pdf` to raise `SubquoteParseError` (rename the page so the deterministic parser misses it), and verify the "Try LLM extraction" affordance recovers the row list and applies with `[sub-quote-llm]` tag at position 0.

T8 calibration is **partly a synthetic exercise** — that is acceptable, because the dollar-touching backend (`apply_batch_plan`) is the same one T6.3 calibrated against real CSV ingestion. T8.1 / T8.2 add a parser frontend only.

---

## 3. What to measure

Each metric below has a name, source-of-truth file (or computation), and a one-line acceptance criterion. The full table is the schema for the per-run `calibration_v4_metrics.json` companion (see §8).

### 3.1 Pipeline routing & extraction

| Metric | Source | Acceptance |
|---|---|---|
| Document-classifier accuracy (per-PDF) | `analyze_stdout.log` "Split into N drawing sheets and M text documents" line + per-PDF routing | ≥ 95 % of calibration PDFs route to the correct bucket (drawing vs bundle vs BID_FORM) |
| Schedule-extraction recall (per family) | Pre-pass output in stdout log + ground-truth count per §4 | ≥ 80 % of ground-truth records per family per bundle |
| Schedule-extraction precision (per family) | Same — false-positive count vs total emitted | ≤ 10 % false-positive rate per family |
| `TakeoffItem` total count | `estimate.json` `project.takeoffs[]` length | Documented per bundle; v4 establishes baseline |
| CSI distribution | `estimate.json` `by_division` keys | ≥ 6 divisions present in any bundle with full schedules (08, 09, 22, 23, 26 + at least one specialty) |
| Dedupe effectiveness | Pre-pass synthesised count vs post-dedupe count in run_log warnings | Dedupe rate ≥ 30 % on bundles with combined typed + LLM-derived takeoffs |
| Room-area cross-reference + opening-deduction firing | T5.1 wall-SF lines: `quantity` < gross room area | Operator visually verifies ≥ 1 wall-SF line per finish-bundle is net-of-openings |

### 3.2 Confidence + pricing tier distribution (T6 / T7)

| Metric | Source | Acceptance |
|---|---|---|
| Confidence-band distribution | `estimate.json` `line_items[].cost_band` aggregated | AUTO_APPROVE share ≥ 30 % across the run (target: rises vs v3's $0 priced state) |
| Cost-source-tier distribution | `line_items[].cost_source_tier` aggregated | MISSING share ≤ 50 % (see §8 open question on cost DB expansion) |
| Price-confidence calibration | `line_items[].price_confidence` vs CWICR similarity bucket | Spot-check 10 random lines: predicted band matches actual `cost_band` |
| Combined-confidence accuracy | `combined_confidence = qty_confidence × price_confidence` math vs `cost_band` | 100 % — invariant check, any drift is a regression |
| CWICR match share | `line_items[].cost_source` count starting with `cwicr:` ÷ total | ≥ 25 % CWICR-priced lines in any bundle with > 10 lines |
| Min-similarity floor (0.55 default) | Run log for "below similarity threshold" warnings | Documented; no acceptance threshold yet |

### 3.3 UoM safety + suppression (T6.4.b + suppressed-line guard)

| Metric | Source | Acceptance |
|---|---|---|
| Unit-mismatched lines suppressed | `line_items[].suppressed=true` count | All suppressed lines have a `unit mismatch:` note prefix |
| Suppressed total $ contribution | `Estimate.subtotal` minus sum of suppressed `total_cost` | $0 — by construction, suppression excludes from totals |
| Near-miss UoM cross-applications | Match-plan CSV preview `uom_mismatch_warning` column where present | Documented per bundle; **0 LF×SF cross-applications applied** (T6.4.b safety floor) |
| `apply_batch_plan` UoM filter coverage | Sub-quote / vendor-CSV apply-result `rejected_rows[].reason` containing `unit mismatch:` | Documented; no acceptance threshold (depends on the vendor input) |

### 3.4 Aggregation + regional adjustment

| Metric | Source | Acceptance |
|---|---|---|
| `Estimate.subtotal` accuracy | Sum of priced (non-suppressed) `total_cost` | Matches Excel "Project Summary" Subtotal cell to the penny |
| Regional multiplier application | Spot-check 5 lines: priced `unit_cost` ÷ source DB `unit_cost` | Equals `--region` value (default 1.00; TX run-script sets per §5) |
| Overhead / profit / contingency | Excel "Project Summary" tier cells vs CLI flags | Equal to `--overhead` / `--profit` / `--contingency` |
| `grand_total` round-trip | Excel grand-total = `subtotal × (1 + contingency%) × (1 + overhead%) × (1 + profit%)` (rounded) | Matches to within $1.00 (rounding tolerance) |

### 3.5 T9 alternates (extraction → pricing → render)

| Metric | Source | Acceptance |
|---|---|---|
| Alternates extracted per bundle | `project.alternates[]` length (deterministic + LLM-fallback) | Documented per bundle; ≥ 1 per RFCSP-containing bundle expected |
| Deterministic vs LLM fallback share | `analyze_stdout.log` "bid-form-alternates: deterministic match" lines vs "LLM fallback" | Documented; deterministic share ≥ 50 % expected |
| Signed cost-delta correctness | `project.alternates[].cost_delta` sign vs `alternate_type` | DEDUCTIVE / VE → negative; ADD / SUBSTITUTION → positive or net-positive |
| `included_by_default` correctness | Spot-check vs bid-form text | All extracted alternates carry the explicit base-bid inclusion flag from the source PDF |
| Sign-validation soft warnings | `extraction.warnings` containing `alternate sign mismatch` | Documented; non-zero is informational, not a regression |
| Selection → tally | Excel "Bid Alternates" "Selected total" cell vs `Estimate.subtotal_with_alternates_selected()` | Matches to the penny |
| Streamlit selection → PDF round-trip | T9.3 path: `st.session_state["alternates_selected_ids"]` → `build_quote_pdf(alternates_config={"default_selection": [...]})` | Selected alternates appear on the PDF's "Bid Alternates" section with matching base-vs-selected tally |
| Client PDF section render | `quote.pdf` "Bid Alternates" page bytes-present | Section renders without `reportlab` warning |

### 3.6 T8 sub-quote ingestion

| Metric | Source | Acceptance |
|---|---|---|
| Tabular parse rows per quote | T8.1 parse result `BatchOverrideRow[]` length | Matches operator-counted source table rows ≥ 90 % |
| LLM-vision fallback rows per quote | T8.2 parse result via "Try LLM extraction" affordance | Equal to deterministic count on a controlled test |
| `[sub-quote]` tag at `CostLine.notes[0]` | T6.4.c regression — Excel "Line Items" Notes column starts with `[sub-quote]` | 100 % of T8.1-applied lines |
| `[sub-quote-llm]` tag at `CostLine.notes[0]` | T6.4.c regression — same column, `[sub-quote-llm]` prefix | 100 % of T8.2-applied lines |
| Per-row apply correctness | `apply_batch_plan` result.applied count vs T8 plan.matched | Equal — matched rows apply; ambiguous rows surface in UI for operator resolution |
| UoM mismatch suppression on sub-quote apply | T8 plan rows where `result.uom_mismatch_warning is not None` | All such rows land in `no_match` with the explicit warning string |

### 3.7 T6.4 source-tag provenance (the cross-cutting audit)

For every override-applied `CostLine`, position 0 of `notes` must carry the canonical tag for its ingestion path:

| Ingestion path | Expected tag | Reaches `CostLine.notes[0]`? |
|---|---|---|
| T6.3 vendor CSV | `[vendor-csv]` | T6.4.c.1 SHIPPED — yes |
| T8.1 tabular sub-quote | `[sub-quote]` | T6.4.c SHIPPED — yes |
| T8.2 LLM-vision sub-quote | `[sub-quote-llm]` | T6.4.c SHIPPED — yes |
| T6.1 single-line manual override | `[manual-override]` | T6.4.c.2 (Worker UU, in flight) — yes once UU lands |
| T6.3 default batch (no source override) | `[batch]` | T6.4.c SHIPPED — yes |

**Cross-cut acceptance:** every applied override has the correct tag at `notes[0]` across **all four downstream surfaces**: `estimate.xlsx` "Line Items" → Notes column, `estimate.json` → `line_items[i].notes`, `quote.pdf` → cost-breakdown notes column, Streamlit Estimate tab → notes column.

### 3.8 End-to-end determinism

| Metric | Source | Acceptance |
|---|---|---|
| Re-run byte equality | Run analyze.py twice on the same bundle with the same flags; compare `estimate.xlsx` / `estimate.json` | **Byte-identical** for the deterministic stage (LLM stage WILL differ); document this and freeze the LLM stage outputs as a separate fixture |
| `estimate.json` re-export idempotency | Round-trip JSON → load → re-export → diff | Byte-identical |

### 3.9 Cost + time + errors

| Metric | Source | Acceptance |
|---|---|---|
| LLM tokens spent (input + output) | `analyze_stdout.log` token-accounting lines per LLM call | Documented per-bundle + total |
| LLM dollar estimate (by provider/model) | Token count × per-million-token rate (default `gpt-4o`: $2.50/M input, $10/M output) | ≤ $1.00 total run (v3 baseline $0.55; v4 budget +90 % for T9 alternates fallback) |
| Per-bundle breakdown | Per-PDF cost line in `run_log.txt` | Documented |
| Time: deterministic stage / LLM stage / synthesis / pricing / export | Wall-clock timestamps in `analyze_stdout.log` | Deterministic stage < 30 s/bundle; LLM stage < 4 min/bundle; ≤ 15 min/bundle total |
| Retries logged | `analyze_stdout.log` 429 retry lines (T6-era LLM-client retry loop) | All retries succeeded (none hit the 12-attempt / 5-min budget) |
| Pipeline failures | stderr stack traces; missing artefacts | 0 expected |
| Soft warnings | `Estimate.warnings[]` + `BidPackage.warnings[]` | Documented; non-zero is informational |

---

## 4. Ground-truth strategy

Ground truth is **operator-collected, per-bundle, manual** — not sampled, not external-source-only. The operator works each calibration bundle through the steps below before re-running v4, and stores per-bundle ground-truth files at `exports/calibration_v4/GROUND_TRUTH/<bid_slug>/` (a new subdirectory created at run time; not part of this docs-only deliverable).

### 4.1 Schedule families (doors, windows, finishes, rooms, panels, lighting, HVAC, plumbing, kitchen, lab, AV, security)

For each bundle containing real drawing sets:

1. Open each drawing PDF in Adobe / Foxit. Navigate to the schedule pages (Door Schedule, Window Schedule, Finish Schedule, Room Schedule, Panel Schedule, Lighting Schedule, HVAC Schedule, Plumbing Schedule, Kitchen Equipment, Lab Casework, AV Devices, Security Devices).
2. For each schedule found, manually count rows. Record:
   - `family`: `door` / `window` / `finish` / `room` / `panel` / `lighting` / `hvac` / `plumbing` / `kitchen` / `lab` / `av` / `security`
   - `ground_truth_count`: the row count (excluding the header)
   - `notes`: any blank rows, "as-shown" placeholders, or multi-row records that should fan out
3. Save as `exports/calibration_v4/GROUND_TRUTH/<bid_slug>/schedules.md` with one section per family.

This is ~10–20 minutes of operator time per bundle. The pre-flight run (§5) will print the extracted count per family to the run log; comparison against the ground-truth file produces recall + precision rows for §3.1.

### 4.2 Alternates

For each bundle containing a bid form / RFCSP / RFP:

1. Open the bid form PDF and search for any of: `Alternate`, `Bid Alternate`, `Alternates`, `VE`, `Value Engineering`, `Deduct`, `Deductive`, `Substitution`, `CLIN Option`, `Option Period`, `Add Alternate`.
2. List every match. For each, record:
   - `alternate_id`: bid-form-printed ID (e.g. `Alt-1`, `BA-3`, `CLIN-0001-A`)
   - `description`: the printed scope text
   - `alternate_type`: ADD / DEDUCTIVE / SUBSTITUTION / VE (per the bid form's terminology)
   - `cost_delta`: the printed dollar figure if present; null otherwise
   - `included_by_default`: true if the bid form base-bid explicitly includes this scope
3. Save as `exports/calibration_v4/GROUND_TRUTH/<bid_slug>/alternates.md`.

### 4.3 Sub-quotes (T8.1 / T8.2 calibration)

Sub-quote ground truth is **synthetic for v4**:

1. For one bundle (recommendation: PAIS Cabin), construct a 5–8-row synthetic vendor quote PDF using a real-looking layout (vendor letterhead, table with `Description / Qty / Unit / Unit Cost / Total` columns, total at bottom). Save as `exports/calibration_v4/GROUND_TRUTH/pais-cabin-140P6026Q0029/synthetic_subquote.pdf`. Record the exact row contents in a sibling `synthetic_subquote.md` so the operator has a ground-truth row list to compare against the T8.1 parsed output.
2. Optionally: scan one printed page (or PDF-flatten the page so the deterministic table parser misses) to force the T8.2 LLM-vision fallback. Same row contents; verify the LLM-extracted rows match.

### 4.4 Pricing ground truth

Pricing ground truth is HARD — the open dataset CWICR is the same one the matcher reads, so it can't validate itself. Use the following ladder, in order of preference:

1. **Post-award contract values** if any prior bid on a similar opportunity has been awarded — the unit prices in the public contract are the closest thing to truth.
2. **RSMeans free-trial pricing** (the cost-DB seed cites RSMeans as the reference) — for ≤ 10 spot-check lines per bundle.
3. **AGC published unit prices** (state-level publications) — useful for region-specific calibration of the `--region` flag.
4. **Industry average ranges** (FEMA / GSA / NAHB / USACE) — already used to seed the v2 cost DB expansion; consult [`docs/COST_DATABASE_v2.md`](./COST_DATABASE_v2.md) for the source URL table.

**Hard rule:** if pricing ground truth disagrees with the run by > 50 % on > 25 % of priced lines, the cost-DB coverage is insufficient and the run should NOT be the basis for a client quote — the calibration metric set is still valid for documenting the gap, but the operator must annotate the report accordingly.

### 4.5 Acceptable bundling for ground-truth collection

The pre-flight strategy is **fully-manual per bundle**, not sampled. Rationale: the calibration bid set is intentionally small (6 primary + 3 stretch = 9 bundles maximum); sampling within that already-small set would erode the precision/recall signal too far to be useful. The estimated total operator labour for ground-truth collection across the 6 primary bundles is **3–5 hours one-time**, which is an acceptable one-time cost to harden the v4 metric base.

---

## 5. Pre-flight checklist

This list is duplicated verbatim in [`docs/CALIBRATION_V4_CHECKLIST.md`](./CALIBRATION_V4_CHECKLIST.md) for in-line ticking.

- [ ] LLM API key in `.env` — provider + model (`OPENAI_API_KEY` for `gpt-4o`, OR `ANTHROPIC_API_KEY` for Claude). Verify via `python -c "import os; print(bool(os.environ.get('OPENAI_API_KEY')))"`.
- [ ] `pip install -r requirements.txt` runs clean. Lockfile-style verification: `python -m pip check`.
- [ ] `.\.venv\Scripts\python -m pytest -q` is green. Baseline at v4 author time: **2479 passed, 1 skipped** (post-`b0dd955`). Workers TT (T6.4.a) and UU (T6.4.c.2) will land before/after this doc; record the new count here before running.
- [ ] Calibration bid set complete. For each of the 6 primary slugs in §2.2: confirm the relevant source PDFs are in `inbox/opportunities/attachments/2026-05-21/` (or the corresponding subdirectory) and accessible.
- [ ] Cost database refreshed. Run `python scripts/refresh_pricing.py` if escalation-bringing-forward is in scope; otherwise note "skipped — using 2024-snapshot pricing".
- [ ] Confirm region multiplier setting. TX is the calibration region. Default `--region 1.00`. If using county-specific RSMeans factors, set per-county per `bids/<slug>/01-overview.md`'s region line.
- [ ] Confirm overhead / profit / contingency defaults are realistic. v3 used `--contingency 10 --overhead 10 --profit 5`. For TX commercial, this is the conservative range; for federal / Davis-Bacon, raise overhead to 12 %.
- [ ] Backup the prior calibration v3 exports. `Copy-Item -Recurse exports\calibration_v3 exports\_archive_calibration_v3_b0dd955` — preserves the v3 baseline for diffing.
- [ ] Create `exports/calibration_v4/` and `exports/calibration_v4/GROUND_TRUTH/<slug>/` per the §4 strategy.
- [ ] **Collect ground truth** per §4 before running. Hard requirement for any bundle whose recall + precision will be reported in the v4 report.
- [ ] For each bundle: invoke `analyze.py` per the §D run-script template below, capturing logs to `exports/calibration_v4/<bid_slug>/analyze_stdout.log`.
- [ ] Render client PDFs for the 2–3 bundles that surface alternates. Use the Streamlit UI's "Download client quote PDF" button so the T9.3 session-state selection round-trip is exercised end-to-end.
- [ ] Compile `exports/calibration_v4/CALIBRATION_REPORT.md` from per-bundle outputs. Use the v3 report as the template for the per-bundle delta + headline table.
- [ ] Generate the companion `exports/calibration_v4/calibration_v4_metrics.json` (machine-readable) by aggregating the per-bundle JSON exports + the §3 measurement schema. This is what future T11 / T12 regression CI gates will diff against.
- [ ] Diff against v3. Note any regressions in extracted-count or band distribution. Note any improvements (alternates extracted, sub-quote tags propagating, etc.).
- [ ] Commit the report + metrics JSON. Suggested message: `docs: Phase T10 - calibration v4 report (6 bundles, full T6/T7/T8/T9 stack)`.

---

## 6. Expected outcomes & gotchas

**T9 alternates: first in-the-wild run.** Anticipate calibration issues with:

- **Sign conventions.** The T9.0 backend signs DEDUCTIVE / VE alternates as negative. If a bid form prints a deductive value as a positive number with the word "DEDUCT" in the description, the extractor's sign-flip heuristic must catch it. Expect 0–2 sign-flip soft warnings per bundle.
- **Bid-form layout variations.** RFCSPs vary by issuing agency. NPS PAIS uses `CLIN-0001-A` style; Texas school districts use `Bid Alternate 1`; federal civil works uses `Optional Bid Item 1`. The deterministic extractor's pattern library covers ≥ 3 of these layouts; the LLM fallback should catch the rest.
- **`included_by_default` ambiguity.** Some bid forms list alternates as "items not in base bid" without making the base-bid inclusion state explicit. The extractor's default is `false`; if the bid form text says "base bid INCLUDES Alt-1", the LLM-fallback should flip this to `true`.

**T6.4.b UoM safety: should be invisible.** On good bundles (clean schedules with consistent UoMs), expect zero `uom_mismatch_warning` entries. On bundles with mixed-UoM hand-shaped takeoffs, expect 0–3 warnings per 100 lines. **Any LF×SF cross-application that *applies* (not just warns) is a regression** — the T6.4.b safety net should block these at the `match_cost_lines` filter step.

**T6.4 source tags: position 0 invariant.** Most calibration lines are auto-priced by `price_takeoff` (no override applied), so the tag check matters only for sub-quote / vendor-CSV / manual-override paths. Expect:

- 0 tags on most lines (no override)
- 100 % of T8.1-applied lines: `[sub-quote]` at position 0
- 100 % of T8.2-applied lines: `[sub-quote-llm]` at position 0
- 100 % of T6.3-applied vendor-CSV lines: `[vendor-csv]` at position 0
- 100 % of T6.1-applied manual-override lines: `[manual-override]` at position 0 (post-UU)
- 100 % of T6.3 default batch-applied lines: `[batch]` at position 0

**Cost gotcha:** prior runs cost ~$0.35 (v2) – $0.55 (v3). v4 is targeted at ≤ $1.00 total, but T9 alternates LLM fallback can spike for bundles where the deterministic bid-form pattern library misses. **Set per-bundle hard caps** in the run script (`--workers 1` + 15-minute timeout per bundle) so a runaway LLM-fallback loop doesn't blow the budget.

**Carr EFA RFCSP 311-page wall-clock.** v3's longest extraction was the Carr EFA RFCSP at 60.14 s longest single 429 backoff. Expect 4–6 minutes total on this one bundle in v4. If the T6.4.b match step takes > 30 s on this bundle, that's a regression worth investigating.

---

## 7. Go / no-go criteria

The run is **GO** if all of the following hold:

1. **≥ 95 %** of calibration bundles classify correctly (drawing vs bundle vs BID_FORM at the deterministic layer).
2. **≥ 80 %** of schedule extractions hit ground-truth count (per family, per bundle, averaged).
3. **0 LF×SF cross-applications applied** end-to-end (T6.4.b safety check). Warnings are OK; applications are not.
4. **All source tags propagate end-to-end** to `CostLine.notes[0]` across Excel + JSON + PDF + Streamlit, for every applied override.
5. **LLM cost ≤ $1.00 total** across all 6 primary bundles (≤ $1.50 with the 3 stretch bundles).
6. **Wall-clock ≤ 15 min per bundle**, ≤ 90 min total for the 6 primary bundles.
7. **Zero pipeline hard failures.** Soft warnings (sign-flip, low-similarity, BID_FORM-skipped-empty) are acceptable and expected.
8. **`combined_confidence` invariant** holds on 100 % of lines (`qty_conf × price_conf` rounded to 4 dp equals the recorded value; band assignment matches the spec).
9. **Re-run determinism**: byte-equal `estimate.xlsx` + `estimate.json` from the **deterministic stage** on a re-run with the same inputs. LLM-stage outputs WILL differ; the deterministic-stage invariant is the hard one.

The run is **NO-GO and must be re-attempted** if any of (3), (4), (8), or (9) fail. The run is **YELLOW (proceed but document the gap)** if (1), (2), (5), (6), (7) fall in the ranges:

- 90–95 % classifier accuracy
- 70–80 % schedule recall
- $1.00 – $1.50 LLM cost
- 15–20 min per bundle
- 1–5 soft warnings per bundle

---

## 8. Open questions / follow-ups for the operator

1. **Cost-DB coverage.** v3 reported a near-complete MISSING-tier landscape (the only 4 lines that priced were unit-mismatched). v4 will exercise T2.x typed schedules that should hit broader coverage, but the 128-entry seed `config/cost_database.json` is still narrow. **Open question:** should v4 wait on the `par_costdb_expand` work (open in the backlog) before running? **Recommendation:** run v4 now to surface the gap quantitatively (per-division MISSING-tier %), then prioritise the expansion based on which divisions are MISSING-most.
2. **Photo curation.** Past-project photos for the client PDF are still pending PII-clean review. The `--client-pdf` output renders without photos by default; v4 should NOT block on photo curation but should note the gap in the run report.
3. **WeasyPrint / GTK.** The proposal-render path (`--render-proposal`) requires GTK on Windows for some PDF flows. v4 does NOT need `--render-proposal` for the core calibration; document that proposal rendering remains pending.
4. **Calibration metric file format — BOTH.** This was a design choice for v4. The Markdown report (`CALIBRATION_REPORT.md`) is the human-readable narrative; the JSON companion (`calibration_v4_metrics.json`) is the machine-readable diff target. The JSON schema is the §3 measurement table flattened to one key per row plus per-bundle nesting. **Action for operator:** when authoring the v4 report, emit both files atomically so future runs can `git diff` the JSON and pull-quote the Markdown.
5. **TT + UU rebase ordering.** Worker TT (T6.4.a multi-sheet xlsx) and Worker UU (T6.4.c.2 manual-override tag) are landing concurrently with this docs-only PR. v4 should run AFTER both land. Verify with `git log --oneline | head` that both phases appear before kicking the run.
6. **Region multiplier for federal / Davis-Bacon bundles.** The Carr EFA + USFWS + B1710 + Cmd-Post-NDI bundles are Davis-Bacon wage scope. For these, `--region 1.10` (Davis-Bacon labour uplift) is the more honest setting than `1.00`. **Open question:** should the run script switch `--region` per bundle? **Recommendation:** yes — see the run-script template below for the per-bundle dispatch.

---

## §D. Suggested `scripts/run_calibration_v4.ps1` (PowerShell skeleton)

**DO NOT** create this file as part of the docs-only deliverable — PowerShell scripts that drive analyze.py should land via an operator-reviewed PR. The block below is the suggested content for the operator to save once they're ready.

```powershell
# scripts/run_calibration_v4.ps1
# Phase T10 — Calibration v4 driver. Iterates over the primary bid set,
# runs analyze.py once per bundle, captures logs.
#
# Usage (from repo root):
#   .\scripts\run_calibration_v4.ps1            # primary bundles only
#   .\scripts\run_calibration_v4.ps1 -Stretch   # add stretch bundles
#
# Prerequisites — work through docs/CALIBRATION_V4_CHECKLIST.md FIRST.

[CmdletBinding()]
param(
    [switch]$Stretch,
    [string]$OutRoot = "exports/calibration_v4"
)

$ErrorActionPreference = "Stop"

# Per-bundle dispatch: (slug, source-path, region, extra-flags).
# Source paths are relative to repo root.
$primary = @(
    @{ slug = "angelo-state-carr-efa-26-007";     src = "inbox/opportunities/attachments/2026-05-21";           region = 1.10; flags = @("--no-drawings") },
    @{ slug = "chs-cafeteria-2026-0608-01";       src = "inbox/opportunities/attachments/2026-05-21";           region = 1.00; flags = @("--no-drawings") },
    @{ slug = "pais-cabin-140P6026Q0029";         src = "inbox/opportunities/attachments/2026-05-21";           region = 1.05; flags = @("--no-drawings") },
    @{ slug = "usfws-san-marcos-140FC126R0017";   src = "inbox/opportunities/attachments/2026-05-21";           region = 1.10; flags = @("--no-drawings") },
    @{ slug = "tamu-harrington-2025-06813";       src = "inbox/opportunities/attachments/2026-05-21";           region = 1.00; flags = @("--no-drawings") },
    @{ slug = "cmd-post-ndi-W50S7626QA001";       src = "inbox/opportunities/attachments/2026-05-21/Command_Post_and_Nondestructive_Inspection_Room_Renovations"; region = 1.10; flags = @() }
)

$stretch = @(
    @{ slug = "b1710-office-refurb-FA667526Q0002"; src = "inbox/opportunities/attachments/2026-05-21/potentialsols"; region = 1.10; flags = @() },
    @{ slug = "tamu-wehner-fin-340E-2025-06871";   src = "inbox/opportunities/attachments/2026-05-21/tamu-csp";      region = 1.00; flags = @() },
    @{ slug = "leroy-moore-gym-PV-0749-PV-0753";   src = "inbox/opportunities/attachments/2026-05-21";               region = 1.00; flags = @("--no-drawings") }
)

$bundles = $primary
if ($Stretch) { $bundles += $stretch }

New-Item -ItemType Directory -Force -Path $OutRoot | Out-Null

$totalStart = Get-Date
foreach ($b in $bundles) {
    $outDir = Join-Path $OutRoot $b.slug
    $logFile = Join-Path $outDir "analyze_stdout.log"
    New-Item -ItemType Directory -Force -Path $outDir | Out-Null

    Write-Host "==== $($b.slug) ====" -ForegroundColor Cyan
    Write-Host "Source: $($b.src)"
    Write-Host "Region: $($b.region)"
    Write-Host "Flags : $($b.flags -join ' ')"

    $bundleStart = Get-Date

    # Per-bundle hard-cap defence: --workers 1 keeps LLM cost bounded,
    # --client-pdf exercises the T9.2 + T9.3 PDF render path.
    & .venv\Scripts\python.exe analyze.py $b.src `
        --recursive `
        --out $outDir `
        --region $b.region `
        --workers 1 `
        --client-pdf `
        --project-name $b.slug `
        @($b.flags) `
        2>&1 | Tee-Object -FilePath $logFile

    $bundleEnd = Get-Date
    $bundleElapsed = ($bundleEnd - $bundleStart).TotalSeconds
    Write-Host ("`n[done] {0}  {1:N1}s" -f $b.slug, $bundleElapsed) -ForegroundColor Green
    Write-Host ""
}

$totalElapsed = ((Get-Date) - $totalStart).TotalSeconds
Write-Host ("`n==== ALL DONE  {0:N1}s ====" -f $totalElapsed) -ForegroundColor Cyan
Write-Host "Next: compile $OutRoot\CALIBRATION_REPORT.md per docs/CALIBRATION_V4_PLAN.md §5."
```

The script intentionally uses `--workers 1` (single-threaded) to keep LLM costs predictable and to avoid the v2-era TPM-ceiling collisions across parallel bundle extractions. v3 already proved the LLM-client retry loop respects `Retry-After` headers, but serial execution is the safest run profile for the calibration deliverable.

---

## Audit notes — what v3 measured that v4 should carry forward, with format updates

The v3 report is a **before / after delta** vs v2, structured around the three bug fixes that landed between the runs. v4 should be:

- **Strict superset** of v3's headline metrics (extraction success per bundle, LLM-stage 429 / retry log, project-info voter coherency, unit-mismatch suppression count, headline-subtotal phantom-line audit, wall-clock + cost). All of these carry forward unchanged.
- **Format upgrade**: v3 was bundle-flat (one estimate.json for the 17-PDF folder). v4 is **per-bundle**: one estimate.json + one analyze_stdout.log + one quote.pdf per slug, plus one top-level `CALIBRATION_REPORT.md` aggregating across the 6 primary bundles.
- **Added metric families** (not in v2 / v3 because the corresponding code hadn't shipped):
  - T6 confidence-band distribution
  - T7 cost-source-tier distribution
  - T6.4.b UoM safety + near-miss tracking
  - T6.4.c source-tag provenance audit
  - T8.1 / T8.2 sub-quote ingestion (synthetic in v4)
  - T9.0 / T9.1 / T9.2 / T9.3 alternates end-to-end
  - T2.x typed-schedule recall + precision per family

**Deprecated v3 metrics (do NOT carry forward):**

- The "Bug A retry-after-aware 429 handling" delta table — v4 starts from a baseline where the retry loop is the default and need not be re-measured. Carry forward only the **outcome** ("0 hard-failed on 429") as a hygiene check.
- The "Bug B BID_FORM branch now calls the LLM" delta table — same; carry forward only the outcome ("unit_prices extracted on real BID_FORM bundles").
- The "Bug C unit-mismatch cost suppression" delta table — measure once, document the suppressed-line count and the headline-phantom-line $ value (should be $0), and move on.

**No format updates needed.** v3's structure (TL;DR table → per-bug section → time/cost/errors → backlog → artifacts) is a good template; v4 just folds the new metric families in as additional sections after the bug-aftermath blocks.
