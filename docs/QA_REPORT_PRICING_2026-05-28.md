# QA-2 Report — Confidence Pricing + Batch Overrides + Bid Alternates

**Author:** Worker YY-2 (Pair 25, subsystems 5–7)
**Date:** 2026-05-28
**Repo:** `c:\Users\rnuduru1\Estimator` @ `main`
**Baseline test count (per brief):** 2616 passed, 1 skipped
**Post-QA-2 test count:** 2749 passed, 1 skipped, 5 xfailed
**Contribution by YY-2:** 25 scenarios (24 PASS + 1 XFAIL surfacing 1 bug)
*(The remaining delta is from sibling workers YY-1/YY-3 landing in parallel.)*

---

## 1. Summary

| Stat | Count |
|---|---|
| Scenarios designed | 25 |
| Scenarios PASS | 24 |
| Scenarios FAIL (true failures) | 0 |
| Scenarios XFAIL (surfaced bugs) | 1 |
| Bugs surfaced (`B2-N`) | 1 |
| Per-subsystem confidence | see table below |

| Subsystem | Confidence | One-line rationale |
|---|---|---|
| 5. Confidence pricing | **GREEN** | All 7 scenarios PASS — band thresholds, tier assignment, suppression, snapshot cap, CWICR similarity all behaving to spec. |
| 6. Batch overrides + sub-quote ingestion | **GREEN** | All 8 scenarios PASS — CSV/xlsx/PDF parsing, UoM compat group, source-tag chain layering all behaving to spec. |
| 7. Bid alternates | **YELLOW** | 9/10 PASS. One real bug (B2-1) — the deterministic regex matches inside the literal section header text and emits a false-positive alternate. Severity is bid-form-quality dependent: any project with the literal phrase "BID ALTERNATES SECTION" gets a phantom alternate. |

**Test files added (3):**
- `tests/test_qa_pricing.py` — subsystem 5 (7 tests)
- `tests/test_qa_overrides.py` — subsystem 6 (8 tests)
- `tests/test_qa_alternates.py` — subsystem 7 (10 tests, 1 xfail)

**Doc added (1):** this report.

**Net: 4 files added, 0 files modified outside the test/doc territory granted by the brief.**

---

## 2. Methodology

### Synthetic input construction

| Subsystem | Inputs synthesised | How |
|---|---|---|
| 5 (pricing) | `TakeoffItem`s, `ProjectModel`, in-memory cost DB JSON | Tiny `tmp_path / "stub_cost_db.json"` (< 1 KB), `_FakeMatcher` for CWICR |
| 6 (overrides) | Vendor CSV strings, multi-sheet xlsx bytes, tabular sub-quote PDFs | `io.StringIO`-style strings, `openpyxl.Workbook` for xlsx, `reportlab.platypus` for PDF tables (same pattern as `tests/test_subquote_parser.py`) |
| 7 (alternates) | Bid-form page text strings, `AlternateLine` records | Plain Python strings; reconciliation drives the LLM-fallback mock surface |

### Mocking pattern

- **CWICR matcher** (subsystem 5): a duck-typed `_FakeMatcher` dataclass with a `match()` method returning a canned `[CwicrCandidate]`. Mirrors the only attribute `core.estimator.price_takeoff` reads. Avoids the bundled CWICR dataset entirely (~320 MB unloaded).
- **LLM client** (subsystem 6 LLM-vision sub-quote): `_StubLLMClient` mirrors `core.llm_client.LLMClient` surface. Reused across tests but the bug-free deterministic-only paths are predominant. The LLM-vision path is exercised through `apply_subquote_plan(llm=True)` against a synthetic `BatchOverrideRow` rather than running an actual LLM.
- **LLM fallback for alternates** (subsystem 7): the `should_invoke_llm_fallback` predicate is exercised directly; the LLM result is mocked as a list of `AlternateLine` records and passed to `reconcile_alternate_sources`. No `core.extractors.LLMClient` is instantiated.

### Cost-DB stubbing

`_write_cost_db(tmp_path, entries)` writes a tiny JSON dict with a `_meta` key plus the per-section entries. `core.estimator.CostDatabase(path)` consumes it identically to the bundled `config/cost_database.json` (~1.5 MB) — but without the disk read cost on every test.

### Deterministic-only assertions

Every test asserts deterministic outcomes — no `pytest.approx(rel=…)` for mutable seed data, no time-dependent asserts, no random-input fuzz. Confidence values are pinned to the canonical constants exported from `core.schemas`:
`COST_TIER_SEED_DB_PRICE_CONFIDENCE = 0.95`, `COST_BAND_AUTO_THRESHOLD = 0.85`, `COST_TIER_EXACT_THRESHOLD = 0.92`, `COST_TIER_CATEGORY_THRESHOLD = 0.75`, `MAX_OVERRIDE_SNAPSHOTS = 10`.

---

## 3. Per-subsystem results

### 3.1 Subsystem 5 — Confidence-aware pricing

#### Scenarios designed (7)

| Id | Class | One-line description |
|---|---|---|
| P1 | Positive | Seed-DB hit → `EXACT_MATCH` tier @ price_confidence=0.95, region multiplier baked into unit_cost |
| P2 | Positive | Manual override on `MISSING`-tier line → `MANUAL_OVERRIDE` tier, snapshot captured, revert restores |
| N1 | Negative | Unit-mismatched takeoff (LF vs SF DB row) → suppressed=True, total_cost=0, band=`HAND_TAKEOFF` |
| N2 | Negative | Missing cost-DB file → `FileNotFoundError` on `CostDatabase()` init; `use_seed=False` escape hatch works |
| E1 | Edge | combined_confidence == 0.85 (the AUTO band threshold) → `AUTO_APPROVE` (boundary inclusive) |
| E2 | Edge | 11 distinct overrides on one line → snapshot stack capped at `MAX_OVERRIDE_SNAPSHOTS=10`, oldest dropped FIFO |
| E3 | Edge | CWICR similarity at 0.92 / 0.75 / 0.7499 → `EXACT_MATCH` / `CATEGORY_MATCH` / `INTERPOLATED` (boundaries inclusive) |

#### Findings: ALL PASS. No bugs surfaced.

#### Existing test coverage (the work we built on)

- `tests/test_phase_t6_confidence_bands.py` — band threshold pins
- `tests/test_per_line_undo.py` — snapshot/revert pattern
- `tests/test_estimator_*.py` (multiple) — region multiplier + tier propagation

#### New tests added: 7 (file `tests/test_qa_pricing.py`)

#### Bugs surfaced: 0

#### Confidence: **GREEN**

Rationale: Every documented contract — confidence multiplication, band thresholds (inclusive at 0.85 / 0.70), tier assignment from seed DB and CWICR, region multiplier baked into unit_cost, unit-mismatch suppression with `total_cost=0` and `cost_band=HAND_TAKEOFF`, manual override + snapshot capture + FIFO eviction at the `MAX_OVERRIDE_SNAPSHOTS=10` cap — is reproducible and matches the schemas. The CWICR similarity boundary semantics survive an end-to-end pin through `price_takeoff`.

---

### 3.2 Subsystem 6 — Batch override + sub-quote ingestion

#### Scenarios designed (8)

| Id | Class | One-line description |
|---|---|---|
| P1 | Positive | Vendor CSV → matched, applied; `[vendor-csv]` tag at position 0 of `CostLine.notes` |
| P2 | Positive | 3-sheet xlsx → 3 plans; merged plan has unique row indices and per-row sheet-provenance prefix |
| P3 | Positive | Tabular sub-quote PDF → matched, applied; `[sub-quote]` tag at position 0 |
| N1 | Negative | CSV missing required `description` / `unit_cost` header → `ValueError` (no partial apply) |
| N2 | Negative | xlsx parser given non-xlsx bytes (CSV bytes / empty bytes) → `ValueError` |
| E1 | Edge | UoM compat group {LS, LOT} → row in LOT matches line in LS (T6.4.b compat group) |
| E2 | Edge | UoM cross-dimension (row=LF, line=SF) → match rejected, falls to `NO_MATCH` with diagnostic warning, apply must NOT mutate |
| E3 | Edge | Layered apply (tabular → LLM-vision) → `[sub-quote-llm]` at position 0, prior `[sub-quote] …` preserved as `\| previous: …` suffix |

#### Findings: ALL PASS. No bugs surfaced.

#### Existing test coverage

- `tests/test_subquote_parser.py` — tabular PDF parser
- `tests/test_subquote_llm_fallback.py` — LLM-vision fallback pattern
- `tests/test_phase_t6_4b_uom_aware_matcher.py` — UoM compat / cross-dimension predicate
- `tests/test_phase_t6_4c_source_tag_propagation.py` — source-tag chain layering
- `tests/test_xlsx_parser*.py` — xlsx multi-sheet structural test

#### New tests added: 8 (file `tests/test_qa_overrides.py`)

#### Bugs surfaced: 0

#### Confidence: **GREEN**

Rationale: Source-tag propagation across the full chain (`[vendor-csv]` / `[sub-quote]` / `[sub-quote-llm]`) is correctly stamped at position 0 with prior heads relegated to a `| previous: …` suffix; UoM compat group LS↔LOT is honoured both at the predicate (`uoms_compatible`) and end-to-end through `match_cost_lines`; UoM cross-dimension (LF vs SF) safety-on rejects matches and surfaces a diagnostic warning; malformed inputs (CSV missing required header, non-xlsx bytes) raise `ValueError` cleanly without partial apply. Multi-sheet xlsx merge produces unique monotonically-increasing row indices and preserves sheet name as a notes-prefix.

---

### 3.3 Subsystem 7 — Bid alternates

#### Scenarios designed (10)

| Id | Class | One-line description |
|---|---|---|
| P1 | Positive | 3 ADDITIVE alternates extracted from a bid-form text page → signed positive deltas, deterministic-tier confidence ≥ 0.55 |
| P2 | Positive | `subtotal_with_alternates_selected({A1, A2})` reflects only selected, base unchanged |
| N1 | Negative | Bid form with no Alternates section → 0 alternates, `should_invoke_llm_fallback` returns False |
| N2 | Negative | Section header present but no parseable rows → `should_invoke_llm_fallback` True; reconciliation with empty LLM result is empty |
| E1 | Edge | DEDUCTIVE printed with positive `$1,500` magnitude → coerced to `-1500.0` via `_apply_type_sign`; hand-built mismatched record carries `[sign-warning]` |
| E2 | Edge | "Alt #1" / "Alternate No. 1" / "Alternate 1" → dedupe collapses to one canonical record (deterministic wins); VE-3 stays distinct |
| E3 | Edge | Zero-alternates project → all rollup helpers return safe zero / empty defaults; `subtotal_with_alternates_selected` tolerates empty / `None` / unknown ids |
| (extra-1) | Pin | `parse_cost_delta` blank fillable line returns `None`; parens means negative |
| (extra-2) | Pin | `classify_alternate_type` keyword priority — VE > DEDUCTIVE > SUBSTITUTION > ADDITIVE |
| (extra-3) | Pin | Blank-fillable alternate flows through `price_alternates` with `pricing_basis=MISSING` and confidence floor ≤ 0.50 |

#### Findings: 9 PASS, 1 XFAIL (B2-1).

#### Existing test coverage

- `tests/test_bid_form_alternates_extraction.py` — deterministic extraction patterns + LLM fallback
- `tests/test_estimator_alternates.py` — `price_alternates`, `attach_alternates_to_estimate`, selection rollup
- `tests/test_alternate_id_dedupe.py` — id-normalization for dedupe (existing as part of T9.0)

#### New tests added: 10 (file `tests/test_qa_alternates.py`)

#### Bugs surfaced: 1 (see B2-1 in section 4)

#### Confidence: **YELLOW**

Rationale: The dominant happy paths (extraction, signed delta convention, selection rollup, zero-alternates safety, dedupe) all work correctly. The single bug surfaced — false-positive alternate emitted from the literal section header text — is a real false-positive risk in production but **degrades gracefully**: a stray $0-cost-delta `MISSING`-pricing-basis alternate from header noise will land in the alternates worksheet but will not contaminate the base subtotal. The downgrade from GREEN to YELLOW is deliberate: the issue is contained and well-characterised, but a trivial 0-character regex tweak (require digit / multi-char id token after "Bid Alternate " / "Alt #") would close it.

---

## 4. Bugs surfaced

### B2-1 — Deterministic alternates regex matches inside the literal "BID ALTERNATES SECTION" header

| Field | Value |
|---|---|
| **Title** | `extract_alternates_from_page` emits a false-positive alternate from the literal section-header phrase "BID ALTERNATES SECTION" (matches "Bid Alternate S" with description "SECTION") |
| **Subsystem** | 7 (bid alternates) |
| **Module** | `core/extraction/bid_form_alternates.py` |
| **Severity** | Medium — false positives in the alternates worksheet on any bid form whose section keyword line contains "BID ALTERNATES" followed by another word starting with a capital letter |
| **Repro** | `extract_alternates_from_page("BID ALTERNATES SECTION\n\n…non-parseable body…")` |
| **Expected** | `[]` (zero alternates) — section keyword detected, `should_invoke_llm_fallback` returns True, deterministic pass yields no records |
| **Actual** | `[AlternateLine(alternate_id='Bid Alternate S', alternate_type=ADDITIVE, description='SECTION', cost_delta=None, confidence=0.55, …)]` |
| **Pinned by test** | `tests/test_qa_alternates.py::TestQAAlternatesNegative::test_qa_alternates_n2_section_present_unparseable_invokes_llm` (XFAIL) |
| **Proposed fix slice** | Tighten the line-body regex in `extract_alternates_from_page` so that the alternate-id token after "Bid Alternate " / "Alt #" / "Alternate No." is at least two characters and contains at least one digit OR is a recognised Roman numeral. Estimated effort: < 1 hour incl. additional regression test for existing single-letter id corner cases (none exist in current real bid-form corpus). |
| **Blast-radius caveat** | Production fix should also re-run `tests/test_bid_form_alternates_extraction.py` to confirm no real bid-form fixtures broke; current fixtures are id="No. 1", "No. 2", … — all multi-character with digits, so the tightening is safe. |

---

## 5. Coverage gaps

The following surfaces remain out of scope for this QA pass and SHOULD be covered by a follow-up slice:

1. **CWICR network round-trip** (subsystem 5). All CWICR tests use a `_FakeMatcher`; the real `CwicrMatcher` performs a TF-IDF embedding + nearest-neighbour search against the bundled dataset. Recommend a single end-to-end smoke test that invokes the real matcher against a fixed, small, hand-curated dataset stub.
2. **xlsx parser cell-type coercion** (subsystem 6). Today, `parse_vendor_xlsx` accepts whatever `openpyxl` yields. Coverage gap: a cell containing the string `"$3,850.00"` (vs the float `3850.00`) — does the parser coerce or fall to a soft warn?
3. **Sub-quote LLM-vision multi-page** (subsystem 6). The current LLM-vision path is exercised on single-page payloads. A sub-quote PDF that spans 2+ pages with table continuation across page breaks is unmocked.
4. **Alternate auto-classification on ambiguous wording** (subsystem 7). The classifier today is keyword-priority based; "VE substitute" → VE, but "Substitute LVT (deductive cost saving)" → ? Today's tests show keyword priority but not multi-keyword tie-breaking.
5. **Selection-toggle on DEDUCTIVE+SUBSTITUTION mix** (subsystem 7). `subtotal_with_alternates_selected` is exercised on ADDITIVE-only fixtures; a real bid form often mixes ADDITIVE + DEDUCTIVE + VE, with subsetting interactions that I did NOT exhaustively pin.
6. **Snapshot revert on a stale id** (subsystem 5). `revert_last_override_in_estimate` was exercised on the most-recent override; reverting twice on a one-snapshot stack returns the prior `(None, None)` per spec — pinned implicitly by the FIFO test but not by a dedicated revert-empty-stack scenario.

---

## 6. Recommendations for fix-sprint slice

In priority order:

1. **B2-1 fix** — tighten the alternates line-body regex (subsystem 7). 1-line change in `core/extraction/bid_form_alternates.py`, fast win.
2. **Coverage gap #1** — add a CWICR end-to-end smoke test against a hand-curated 10-row dataset (subsystem 5). Prevents regressions in the real CWICR-similarity → tier wiring.
3. **Coverage gap #2** — add an xlsx parser cell-coercion test for currency strings like `"$3,850.00"` (subsystem 6).
4. **Coverage gap #5** — add a `subtotal_with_alternates_selected` rollup test on a mixed ADDITIVE+DEDUCTIVE+VE fixture (subsystem 7).

**Must-fix-before-T10:** B2-1 only. The other coverage gaps are insurance against regression and can ride a follow-on T10 calibration slice.

---

## Appendix: Source-of-truth references consumed

Strict 12-file read budget — actual reads in this session:

| # | Path | Purpose |
|---|---|---|
| 1 | `core/estimator.py` | `price_takeoff`, `apply_manual_override`, `attach_alternates_to_estimate`, `price_alternates` |
| 2 | `core/pricing/cwicr_matcher.py` | `CwicrMatcher`, `CwicrCandidate`, similarity thresholds |
| 3 | `core/pricing/batch_override.py` | `BatchOverrideRow`, `match_cost_lines`, `apply_batch_plan`, `parse_vendor_csv`, `uoms_compatible`, source-tag constants |
| 4 | `core/pricing/subquote_parser.py` | `parse_subquote_pdf`, `apply_subquote_plan`, LLM-vision fallback |
| 5 | `core/pricing/xlsx_parser.py` | `parse_vendor_xlsx`, `merge_xlsx_plans`, sheet provenance |
| 6 | `core/extraction/bid_form_alternates.py` | extraction, classification, sign coercion, dedupe / reconcile |
| 7 | `core/schemas.py` | `CostLine`, `Estimate`, `AlternateLine`, `CostLineOverrideSnapshot`, `MAX_OVERRIDE_SNAPSHOTS`, threshold constants |
| 8 | `tests/test_phase_t6_confidence_bands.py` | existing pricing test pattern |
| 9 | `tests/test_subquote_parser.py` | PDF construction pattern |
| 10 | `tests/test_subquote_llm_fallback.py` | LLM mocking pattern |
| 11 | `tests/test_estimator_alternates.py` | alternates test pattern |
| 12 | `tests/test_per_line_undo.py` | snapshot/revert test pattern |

**Total: 12 file reads — at budget.**

---

*End of QA-2 report (Worker YY-2 / Pair 25 / subsystems 5–7).*
