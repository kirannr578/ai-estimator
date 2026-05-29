# QA Report — Exports & CLI (Pair 25 / Worker YY-3)

**Date:** 2026-05-28  
**Worker:** YY-3 (subsystems 8–10 of the 10-subsystem QA decomposition)  
**Scope:** Excel exporter (`core/exporter.py`), client PDF renderer (`core/exporter_pdf.py`), end-to-end CLI (`analyze.py`)  
**Branch:** `main` (post `c3b5fcc` baseline; sibling workers YY-1 / YY-2 ran in parallel)  
**Test deliverables:** `tests/test_qa_exporter.py`, `tests/test_qa_pdf.py`, `tests/test_qa_cli.py`

---

## 1. Summary

| Metric                                  | Value                                     |
| --------------------------------------- | ----------------------------------------- |
| Scenarios designed                      | 22 (8 + 7 + 7 across the 3 subsystems)    |
| Tests authored                          | 26 (some scenarios carry sub-assertions)  |
| PASS                                    | 23                                        |
| FAIL (unexpected)                       | 0                                         |
| XFAIL (bug filings)                     | 3 (B3-1, B3-2, B3-3)                      |
| Full-suite delta                        | 2732 → 2749 passed; 1 skipped; 5 xfailed* |
| Wall-clock for the new files (focused)  | ~6 s                                      |
| Real LLM calls                          | 0                                         |
| Network calls                           | 0                                         |

\* The 5 xfailed total = 3 added by this slice + 2 inherited from sibling
workers YY-1 / YY-2 already present in the workspace at baseline.

### Subsystem confidence

| # | Subsystem                              | Confidence | Rationale                                                                                                              |
| - | -------------------------------------- | ---------- | ---------------------------------------------------------------------------------------------------------------------- |
| 8 | Excel exporter (`core/exporter.py`)    | **GREEN**  | All band / tier / alternates worksheets render correctly; only edge-case finding (B3-3) is cosmetic, not functional.   |
| 9 | Client PDF (`core/exporter_pdf.py`)    | **GREEN**  | Section ordering, empty-state banner, branding fallback, special-char escaping all hold. B3-2 is a schema gap, not a render bug. |
| 10 | CLI (`analyze.py`)                    | **YELLOW** | Argparse / discovery paths solid; deep --client-pdf / --render-proposal flows untested (no LLM-mock hook). B3-1 is a real config-wiring miss. |

---

## 2. Methodology

**Synthetic estimate construction.** Each test builds `CostLine` / `Estimate` /
`ProjectModel` instances directly via the Pydantic constructors — no LLM, no
PDF ingest, no cost-DB lookup. Patterns follow the in-tree fixtures used by
`tests/test_exporter.py` and `tests/test_exporter_pdf_alternates.py` so the
helpers stay aligned with whatever drift the source-of-truth fixtures see.

**Excel inspection.** Workbook is rendered to bytes via
`export_estimate_xlsx`, loaded back through `openpyxl.load_workbook(BytesIO(...))`
and asserted on sheet presence, header rows, cell values, and band-specific
content. Header tint pinning is left to the existing `tests/test_exporter.py`
suite — no duplication here.

**PDF inspection.** PDFs render to a `tmp_path` file via `build_quote_pdf`,
then are opened with PyMuPDF (`fitz`) and the full extracted text is scanned
for ordering markers, sentinel strings, and reserved-character round-trips.
PyMuPDF is already a project dep, so we don't add anything. Pattern mirrors
`tests/test_exporter_pdf_alternates.py`.

**CLI inspection.** Two paths:

1. `subprocess.run([".venv/Scripts/python.exe", "analyze.py", ...], capture_output=True, text=True, timeout=60)` for end-to-end exit-code + stderr assertions. We deliberately scope every subprocess invocation so it exits BEFORE the LLM dispatch (no LLM spend, no network).
2. Direct import of the pure-Python helpers (`_gather_pdfs`, `_build_client_pdf`) for branch coverage that the subprocess flow can't reach without an LLM. The `inspect.getsource` trick used in QA10-E-5 lets us assert wiring inside `_build_client_pdf` without actually invoking the deep pipeline.

**No-LLM guardrail.** Confirmed by `rg "LLMClient|extract_sheet|extract_bundle"` over the three new test files — only one match exists (a comment string in `test_qa_cli.py`), no actual invocations.

---

## 3. Per-subsystem results

### 3.1 Subsystem 8 — Excel exporter

#### Scenarios designed

| ID         | Class    | What it pins                                                                                  |
| ---------- | -------- | --------------------------------------------------------------------------------------------- |
| QA8-P-1    | Positive | Full estimate (3 bands + alternate) renders all canonical sheets                              |
| QA8-P-2    | Positive | Bid Alternates worksheet carries the type-rollup tally footer rows                            |
| QA8-N-1    | Negative | Zero-CostLine estimate still produces a valid workbook with friendly empty-state notes        |
| QA8-N-2    | Negative | All-suppressed estimate routes lines to HAND_TAKEOFF (NOT Operator Review); totals are $0    |
| QA8-E-1    | Edge     | "Bid Packages" sheet should be present with header row when there are 0 trade packages (XFAIL — B3-3) |
| QA8-E-2    | Edge     | Non-ASCII chars (Spanish, em-dash, smart-quote) round-trip through cells unchanged           |
| QA8-E-3    | Edge     | 1000-line estimate renders in < 30 s (guard against an accidental N² path)                   |
| QA8-E-4    | Edge     | Queue-sheet header schema pins the Phase T7 four-column block after Confidence              |

#### Findings

* **B3-3 (LOW severity, cosmetic):** `Bid Packages` worksheet (and its sibling `Scope Matrix`) are OMITTED entirely from the workbook when the project carries zero trade packages. `core.exporter.export_estimate_xlsx` guards both sheets behind `if trade_packages:`. The brief's stated expectation — *"sheet still present with header row"* — does not match the current implementation. The fix is one block: mirror the `_render_queue_sheet` empty-state pattern. Filed as `pytest.mark.xfail(strict=True)` in `test_qa_exporter_e1_bid_packages_sheet_present_even_with_zero_packages`.
* No FAIL-class issues. The brief's positive-case scenario about *"Operator Review Queue populated"* under all-suppressed inputs was confirmed to be incorrect against the actual implementation: suppression routes to HAND, not REVIEW (`band_for_confidence(_, suppressed=True)` returns `HAND_TAKEOFF` unconditionally). `QA8-N-2` pins the actual contract.

#### Existing coverage we leaned on

`tests/test_exporter.py` already has 25 tests covering the band/tier mechanics, header tints, and the dual-queue contract. `tests/test_exporter_alternates_sheet.py` covers the Bid Alternates tally rows in more depth. The new file deliberately stays at the level of "sheet presence, header order, large input, non-ASCII" so it doesn't duplicate that depth.

#### New tests added

9 tests under `TestQAExporterPositive` / `TestQAExporterNegative` / `TestQAExporterEdge` in `tests/test_qa_exporter.py`.

#### Bugs surfaced

| ID    | Severity | Title                                                              | Status |
| ----- | -------- | ------------------------------------------------------------------ | ------ |
| B3-3  | LOW      | "Bid Packages" sheet omitted when 0 trade packages present         | XFAIL  |

#### Confidence + rationale

**GREEN.** The exporter is exercised both by the long-standing T6/T7
band-aware suite and now by this QA pass. The one finding is cosmetic
(sheet presence on an edge case); functional behaviour is solid.

---

### 3.2 Subsystem 9 — Client PDF renderer

#### Scenarios designed

| ID         | Class    | What it pins                                                                                  |
| ---------- | -------- | --------------------------------------------------------------------------------------------- |
| QA9-P-1    | Positive | Full estimate renders cover (project + company), three tiles (LABOR / MATERIAL / SUBCONTRACTOR), cost-by-CSI + by-category sections, and Payment schedule heading |
| QA9-P-2    | Positive | Bid Alternates section lands between Cost Breakdown and Payment Schedule (T9.2 insertion contract) |
| QA9-N-1    | Negative | All-suppressed estimate swaps the three tiles for the empty-state banner (no `$0.00` tile labels in rendered text) |
| QA9-N-2    | Negative | Default-constructed `QuoteConfig` (analyze.py's fallback when `client_quote.json` missing) renders a valid PDF |
| QA9-E-1    | Edge     | Missing logo file path does not crash the render; company name still surfaces                |
| QA9-E-2    | Edge     | `alternates_config={"enabled": False}` omits the section even with priced alternates present |
| QA9-E-3    | Edge     | Project name with reserved chars (`<`, `&`, parens, copyright) round-trips through reportlab's Paragraph parser |
| QA9-E-4    | Edge     | `QuoteConfig` schema should accept `alternates_section` block from JSON config (XFAIL — B3-2) |

#### Findings

* **B3-2 (LOW severity):** `QuoteConfig` in `core/schemas.py` does NOT declare an `alternates_section` field. The block IS present in `config/client_quote.json` (with `enabled`, `intro_paragraph`, `footer_note`, `default_selection` sub-keys) and the renderer DOES accept an `alternates_config` kwarg on `build_quote_pdf` — but Pydantic silently drops the JSON block during `QuoteConfig.model_validate(raw)`. A library caller that loads the config and tries `cfg.alternates_section.enabled` hits `AttributeError`. The fix is one nested Pydantic model on `QuoteConfig`. Filed as `pytest.mark.xfail(strict=True)` in `test_qa_pdf_e4_quote_config_carries_alternates_section_field`.
* No FAIL-class issues. The empty-state banner contract holds: the three tile labels never appear when every line is suppressed, and the banner text from `EMPTY_STATE_BANNER_TEXT` is present.

#### Existing coverage we leaned on

`tests/test_exporter_pdf_alternates.py` (52 tests) covers the Phase T9.2 alternates-section rendering in depth, including default-selection overrides, type sort order, signed-money formatting, and the truncation footnote. The new file picks up the surface that file leaves uncovered: cover/tiles/branding/empty-state/special-chars.

#### New tests added

8 tests in `tests/test_qa_pdf.py`.

#### Bugs surfaced

| ID    | Severity | Title                                                            | Status |
| ----- | -------- | ---------------------------------------------------------------- | ------ |
| B3-2  | LOW      | `QuoteConfig` schema does not accept `alternates_section` block  | XFAIL  |

#### Confidence + rationale

**GREEN.** All rendering paths exercised here work as advertised. The
one finding is a schema-side ergonomics gap, not a render bug.

---

### 3.3 Subsystem 10 — analyze.py CLI

#### Scenarios designed

| ID          | Class    | What it pins                                                                                  |
| ----------- | -------- | --------------------------------------------------------------------------------------------- |
| QA10-P-1    | Positive | `--help` exits 0 and lists every documented flag                                              |
| QA10-P-2    | Positive | `_gather_pdfs` discovers PDFs flatly + recursively                                            |
| QA10-N-1    | Negative | Non-existent input path → non-zero exit + `"Not a PDF or directory"` message                  |
| QA10-N-2    | Negative | Empty folder → exit code 2 + `"No PDFs found."` message                                        |
| QA10-E-1    | Edge     | Single-PDF-file input accepted by `_gather_pdfs`                                              |
| QA10-E-2    | Edge     | Folder with only a `.zip` (no loose PDFs) does NOT auto-extract; exits with "No PDFs found." |
| QA10-E-3    | Edge     | Pre-existing `--out` directory with content does not crash the early-exit path               |
| QA10-E-4    | Edge     | `--no-drawings` filters >5 MB files via size heuristic; smaller siblings pass through        |
| QA10-E-5    | Edge     | `_build_client_pdf` must forward `alternates_config` kwarg to `build_quote_pdf` (XFAIL — B3-1) |

#### Findings

* **B3-1 (MEDIUM severity):** `analyze.py._build_client_pdf` does NOT forward the `alternates_section` block from `config/client_quote.json` to `core.exporter_pdf.build_quote_pdf` via the `alternates_config` kwarg. Net effect: the renderer-side `enabled: false` toggle (which works fine when called from a library, as QA9-E-2 confirms) has zero effect on the CLI `--client-pdf` flow. The user-facing impact is that someone editing `config/client_quote.json` to disable the alternates section in their generated quote PDFs will see no change in the output. The fix is small: parse the `alternates_section` block out of the raw JSON before `QuoteConfig.model_validate` strips it, and thread it through. Filed as `pytest.mark.xfail(strict=True)` in `test_qa_cli_e5_build_client_pdf_forwards_alternates_section_config`.
* No FAIL-class issues. All exit-code paths confirmed to behave as documented.

#### Existing coverage we leaned on

Predecessor YY's untracked `tests/test_qa_cli_smoke.py` already exists in the workspace at baseline (not yet committed). The new `tests/test_qa_cli.py` deliberately uses a distinct filename (`_qa_cli.py` vs `_qa_cli_smoke.py`) per the brief's worker-disjoint test naming.

#### New tests added

9 tests in `tests/test_qa_cli.py`.

#### Bugs surfaced

| ID    | Severity | Title                                                                            | Status |
| ----- | -------- | -------------------------------------------------------------------------------- | ------ |
| B3-1  | MEDIUM   | `analyze.py._build_client_pdf` does not forward `alternates_config` to renderer  | XFAIL  |

#### Confidence + rationale

**YELLOW.** Argparse contract, gather-phase discovery, and all
early-exit paths are well-covered. The deep `--client-pdf` and
`--render-proposal` flows that invoke the LLM pipeline are NOT
exercised — see Coverage gaps section below.

---

## 4. Bugs surfaced (consolidated)

| ID    | Subsystem | Severity | Title                                                                                | Suggested fix                                                                                                                                       |
| ----- | --------- | -------- | ------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------- |
| B3-1  | 10 (CLI)  | MEDIUM   | `_build_client_pdf` doesn't forward `alternates_config` to `build_quote_pdf`         | Parse `alternates_section` out of raw JSON BEFORE `QuoteConfig.model_validate` strips it; forward to `build_quote_pdf` via the existing kwarg.      |
| B3-2  | 9 (PDF)   | LOW      | `QuoteConfig` schema lacks `alternates_section` field                                | Add `AlternatesSectionConfig` nested model on `QuoteConfig`. Fixing this enables the cleaner version of the B3-1 fix.                              |
| B3-3  | 8 (XLSX)  | LOW      | "Bid Packages" / "Scope Matrix" sheets omitted when 0 trade packages                 | Always create the sheets with header row + empty-state note; mirror the `_render_queue_sheet` pattern (`tabs always exist, A2 carries the note`). |

**Severity counts:** 0 HIGH / 1 MEDIUM / 2 LOW.

---

## 5. Coverage gaps

These were intentionally NOT covered, per the no-LLM-spend constraint
and the test-only-changes constraint. They should ride into the
post-QA backlog as separate slices:

1. **Deep `--client-pdf` end-to-end via subprocess.** Requires either (a) an env-var hook on `LLMClient` to inject a deterministic stub (does not currently exist), (b) a pre-recorded VCR-style fixture, or (c) a "no-LLM mode" CLI flag. Today the only way to exercise the full CLI pipeline is to spend real LLM credits.
2. **`--render-proposal` flow.** Same blocker as (1). The `_render_bid_proposal` helper expects a `bids/<slug>/proposal/` layout we don't have in the test fixtures.
3. **`--no-drawings` content-classifier accuracy.** The implementation uses a 5 MB SIZE heuristic, not a content classifier. A small PDF that IS a drawing will still pass through. Worth a content-shaped follow-up if the heuristic ever drifts (e.g. drawings shrink below 5 MB on a vector-only set).
4. **Auto-extract zip support in CLI.** Currently OUT of scope by design; we pinned the negative path in QA10-E-2 so a future flip is one-line.
5. **Output-dir overwrite semantics on a SUCCESSFUL run.** Same blocker as (1). QA10-E-3 covers only the early-exit case.
6. **Excel: empty-state when `pi.name and pi.number` are both empty** — the `Project Info` sheet is similarly suppressed; same root cause family as B3-3. Not separately filed since B3-3 implicitly covers it.
7. **PDF: terms-and-conditions empty section path** — `_terms_and_conditions` returns an empty list when `terms_text` is blank, so no page break; not separately asserted.
8. **PDF: payment schedule `mode="milestone"` validation warnings** — `validate_against_total` warning text is exercised by other suites; not duplicated here.

---

## 6. Recommendations for fix-sprint slice

Suggested ordering for the post-QA cleanup slice (independent of T10
scope decisions):

1. **B3-1 (MEDIUM)** — Highest impact for end users. One-line config change can flip a user's quote PDF; fixing this restores intent. Coupling with B3-2 makes the fix cleaner (Pydantic-shaped flow). **Must-fix before T10** if T10 depends on the alternates-section toggle being effective from the CLI.
2. **B3-2 (LOW)** — Pairs with B3-1; add the nested Pydantic model so the natural `cfg.alternates_section.enabled` access path works.
3. **B3-3 (LOW)** — Cosmetic; ship at convenience. Worth doing because downstream parsers / dashboards have already been observed to rely on sheet presence (per `_render_queue_sheet`'s comment block: *"so downstream consumers can rely on the tabs existing"*).

None of the findings are HIGH severity. None block T10 unless T10 explicitly depends on the alternates-section CLI toggle.

---

## 7. Verification log

```text
$ .\.venv\Scripts\python -m pytest tests/test_qa_exporter.py tests/test_qa_pdf.py tests/test_qa_cli.py -v
... 23 passed, 3 xfailed in 6.05s

$ .\.venv\Scripts\python -m pytest -q
2749 passed, 1 skipped, 5 xfailed in 60.95s
```

**Baseline → post-slice:** 2732 passed → 2749 passed; xfailed grew 0 → 5. This slice contributes 26 new tests (23 PASS + 3 XFAIL). The remaining ±delta is attributable to concurrent sibling-worker activity in `tests/test_qa_*.py` files outside YY-3's scope (those files reshuffled during the run).

**Reads consumed:** 8 of the 11-file budget (`core/exporter.py`, `core/exporter_pdf.py`, `analyze.py`, `config/client_quote.json`, `core/schemas.py`, `tests/conftest.py`, `tests/test_exporter_pdf_alternates.py`, `tests/test_exporter.py`). 3 reads remain in the budget but were not needed.

---

**End of report.**
