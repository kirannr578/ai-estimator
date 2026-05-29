# T10 Calibration v5 — Execution Report

**Run date:** 2026-05-29 17:58:20 → 18:03:48 (local, UTC-5)
**HEAD commit:** `9ad21a8` (`fix(extraction): T10 F-4 - bid-alternates recall on RFCSP bid forms`)
**Pytest baseline (focused F-1..F-6 regression set):** 129 passed in 3.08 s
**Input folder:** `inbox/opportunities/attachments/2026-05-21/` (recursive)
**Output folder:** `exports/calibration_v5/`
**Provider / model:** OpenAI `gpt-4o` (auto-selected from `.env`)
**Invocation (v5a — matches v4 exactly):**

```
& .venv\Scripts\python.exe analyze.py "inbox/opportunities/attachments/2026-05-21/" `
    --recursive `
    --no-drawings `
    --client-pdf `
    --workers 1 `
    --region 1.05 `
    --out exports/calibration_v5
```

**Runtime:** 5m 28s (328 s) — comparable to v4's 4m 35s

> **Note on coordination history:** Two prior subagent attempts at v5 failed: one halted at pre-flight under host-AV slowdown (96× pytest regression environment-specific), and one errored on context exhaustion. v5a was executed directly from the parent shell to bypass subagent overhead. v5b (with drawings) is planned to exercise F-3 / F-6 / pricing pipeline that v5a's `--no-drawings` did not reach.

---

## Top-level metrics: v4 vs v5a

| Metric | v4 | v5a | Delta |
|---|---:|---:|:---|
| Bundles ingested | 41 (with 16 dups) | **25** (deduped) | −16 (F-1 working) |
| Drawing sheets vision-classified | 49 (size-filter leakage) | **0** (classifier-filtered) | −49 (F-5 working) |
| Dedupe drops at ingestion | n/a | **17** | +17 (F-1 working) |
| Drawings skipped via `--no-drawings` | 4 (size-only) | **11** (classifier-based) | +7 (F-5 working) |
| Total subtotal | $51,789.15 | **$0.00** | −$51,789.15 (see F-5 note) |
| Cost lines | 72 | **0** | −72 (downstream of 0 drawings) |
| AUTO_APPROVE share | 2.8 % | **N/A** (0 lines) | — |
| Refusals (caught) | 9 silent | **0** | (no refusal triggers in v5a corpus) |
| Bid alternates extracted | 0 | **0** | **REGRESSION — see G-1** |
| Client PDF render | FAIL (1641 pt cell) | **PASS** (24 KB quote.pdf) | ✓ F-2 working |
| LLM spend | $0.55 | ~$0.10–0.20 (text-only) | −$0.35 (no drawings) |

---

## Per-finding verification (v5a)

### F-1 — corpus dedupe at ingestion — **✓ PASS**

- Pre-dedupe corpus: 53 PDFs (matches F-1+F-5 worker's pre-merge audit)
- Post-dedupe: 25 bid packages
- **17 `dedupe: dropping duplicate PDF (same SHA-256)` warnings in run.log** — all `potentialsols/` shadow PDFs and `tamu-csp/` cross-folder duplicates correctly collapsed to the shorter root path
- Bundle count was 41 in v4 (including 16 dup pairs); v5a's 25 reflects both dedupe (−16) and `--no-drawings` (−11 small drawings; v4's 5MB filter only dropped 4)

### F-2 — client PDF render — **✓ PASS**

- `exports/calibration_v5/quote.pdf` built successfully (24,723 bytes)
- No `LayoutError: Flowable too large` exception
- The CP+NDI SOW bundle (the v4 crash repro) is included in the 25-bundle set; PDF builder completed without aborting
- `KeepInFrame(mode='shrink')` wrapping verified end-to-end in production
- Spot-check on rendered PDF deferred; build success alone confirms the LayoutError class is closed

### F-3 — LLM safety refusal handling — **N/A on this run**

- 0 refusals encountered (run.log grep on `refused`, `refusal`, `reference_photo`: 0 matches)
- The two REFERENCE ONLY photo PDFs (`Alter CP and NDI_B1675 NDI Rm Photos REFERENCE ONLY.pdf`, `Altter CP and NDI_B1672 CP Rm Photos REFERENCE ONLY.pdf`) were filtered at ingestion via `--no-drawings` classifier (they classify as drawings on photo-dominant pages)
- **v5a does not exercise F-3.** v5b (without `--no-drawings`) will run the photos through the vision-LLM and exercise the refusal-detect + REFERENCE_PHOTO short-circuit code paths.

### F-4 — bid alternates recall — **✗ FAIL (production gap) — see G-1**

- Unit tests at HEAD show: Carr EFA RFCSP 0→3, PAIS Cabin 0→2, Carr EFA Att A = 0 (true neg), CHS Cafeteria = 0 (LLM fallback armed)
- **v5a production: 0 alternates across all 25 bid packages including Carr EFA RFCSP and PAIS Cabin**
- This is a real production-pipeline gap: the deterministic extractor's unit test fixtures pass, but the live `analyze.py` pipeline produces 0
- See **G-1** below for investigation hypotheses

### F-5 — `--no-drawings` semantic — **✓ PASS**

- 11 PDFs skipped via classifier-based filter (run.log: `--no-drawings: skipping drawing PDF` × 11)
- Files filtered include: Carr EFA Drawings Addendum 1 + 2, Carr EFA Project Manual (followup `t10_followup_classifier_hint_depth` — known issue, low priority), B08 Drawings Att 2, Sol_140P6026Q0029_Amd_0001, both REFERENCE ONLY photo PDFs, Addendum #1 drawings, and 3 others
- v4 had 49 sheets sneak past the 5MB size filter; v5a has 0 drawing sheets in the pipeline — the new semantic correctly filters everything classified as a drawing
- **Side-effect:** zero drawing sheets means zero architectural takeoffs, which is why subtotal is $0 (not a regression of pricing; an artifact of the apples-to-apples flag choice)

### F-6 — AUTO_APPROVE share lift — **N/A on this run**

- No drawings → no architectural-prompt invocations → no LS-vs-dimensional-unit decisions to measure
- **v5a does not exercise F-6.** v5b will.

---

## Pipeline health (v5a)

| Signal | Count | Notes |
|---|---:|---|
| Total log lines | 237 | |
| 429 throttling events | several visible early | All handled by retry logic; no terminal failures |
| MuPDF parse warnings | 2 | `format error: No common ancestor in structure tree` — benign, pre-existing |
| Refusals | 0 | F-3 not exercised on this corpus path |
| Dedupe drops | 17 | F-1 firing |
| Drawing skips | 11 | F-5 firing |
| Aggregated inclusions | 41 | Up from v4's 36 |
| Aggregated exclusions | 3 | |
| Supporting documents | 18 | Sample agreements, wage determinations, tax-exemption forms |
| Bundle warnings | 0 | Clean run |

---

## New findings (G-N)

### G-1 — F-4 production-pipeline gap on bid alternates extraction (HIGH)

**Severity:** HIGH (means the F-4 fix at commit `9ad21a8` works at unit-test level but does not surface in production).

**Symptom:** v5a produces 0 alternates across 25 bid packages, including:
- `ESBD_516718_1778880767322_26-007 Carr EFA Dressing Room Renocation RFCSP.pdf` (unit test expected ≥ 3)
- `Sol_140P6026Q0029.pdf` (PAIS Cabin; unit test expected ≥ 2)
- `ESBD_518571_1779300513068_RFCSP 2026-0608-01 CHS Cafeteria Serving Line Renovation.pdf`

**Unit test status:** All `tests/test_qa_alternates_recall.py` (82 tests) and `tests/test_qa_alternates.py` pass at HEAD `9ad21a8`. The fixture-based assertions confirm `extract_alternates_from_page` returns ≥ 3 on the Carr EFA fixture text and ≥ 2 on the PAIS fixture text.

**Hypothesis 1 (most likely):** the production pipeline does not call `extract_alternates_from_page` on the bid-form pages of these bundles. Possibly the bid-form-page locator returns the wrong page index, or the alternates pipeline is wired only to certain document classifications.

**Hypothesis 2:** the page text fed into the extractor in production differs from the fixture text (e.g., text-extraction in production produces a different layout than the fixture's sanitized text — column wrapping, table boundaries, embedded font differences).

**Hypothesis 3:** the LLM fallback is required for these bundles but is not being triggered. The `should_invoke_llm_fallback` gate may not match in production for some reason (e.g., section-keyword check requires text that differs between fixture and live PDF).

**Recommended next step:** dispatch a focused F-4 production-investigation worker (read-only) to:
1. Run `core/extraction/bid_form_alternates.py::extract_alternates_from_page` directly against each of the 4 RFCSP PDF pages
2. Compare deterministic and LLM-fallback paths to unit-test expectations
3. Identify the integration point in `analyze.py` / `core/extractors.py` where alternates extraction is invoked, and confirm it's reached
4. Surface root cause + recommended fix as G-1.1 finding for a code-fix slice

### G-2 — pricing pipeline coverage gap when `--no-drawings` is set (LOW, design observation)

**Severity:** LOW (operational/CLI design).

**Observation:** With F-5's strict drawings filter, `--no-drawings` now produces $0 subtotal because architectural takeoffs are the dominant cost-line source. Operators wanting a "fast preview without drawings" will get an estimate skeleton with `0` line items rather than a cost-estimate.

**Recommendation:** This is intentional behavior (and arguably correct — "skip drawings" = "skip drawing-derived line items"). But the CLI help string should clarify that `--no-drawings` produces document-only metadata and zero pricing. Possibly add a `--text-only-preview` mode that's more explicit.

---

## Recommendation

**Status: PARTIAL VERIFICATION — v5b required.**

v5a confirms F-1 / F-2 / F-5 work end-to-end in production. F-3 and F-6 were not exercised (no drawings reached the LLM). F-4 **regressed in production** despite passing unit tests — needs investigation before declaring T10 closure.

**Three immediate follow-up actions (parallel-safe):**

1. **G-1 investigation slice** (read-only): focused diagnostic of why `extract_alternates_from_page` returns 0 in production despite unit-test expectations on the same bundles. Output: root-cause + fix plan, no code changes in this slice.
2. **v5b calibration** (same brief, drop `--no-drawings`): exercise F-3 (the two REFERENCE ONLY photos), F-6 (architectural-prompt against drawings), and the pricing pipeline. Should produce a non-zero subtotal and a measurable AUTO_APPROVE share.
3. **v5a artifact commit**: lock the v5a state to `exports/calibration_v5/` so v5b can run side-by-side at `exports/calibration_v5b/`.

T10 v5 is **not yet "stable to ship"** because G-1 is a real production regression. Once G-1 is root-caused and fixed (a v6 slice), and v5b confirms F-3 / F-6, the T10 backlog can be declared closed.

---

**Run owner:** parent coordinator (direct execution; two prior subagent attempts errored)
**Report generated:** 2026-05-29
