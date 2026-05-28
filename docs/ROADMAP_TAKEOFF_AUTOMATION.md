# Roadmap — Construction Quantity Takeoff Automation

**Audience:** Estimator project owner and contributors.
**Status:** Planning draft. Calibrated against `HEAD` as of `5c40365` (post-F1 CWICR + F3 prepass).
**Scope frame:** USA residential + commercial (light commercial, TI, single & multi-family, K-12 and similar institutional). Explicit non-goals are listed in Section 4.

This document is a phased plan for getting the Estimator from "AI-assisted first-pass takeoff that an estimator must review line-by-line" to "automated takeoff with confidence-banded line items where the estimator only audits the lower-confidence bands". It is intentionally honest about what is and is not achievable, and explicit about which phases pay for themselves.

---

## 1. Current-state honest assessment

### 1.1 What the pipeline does today

Document routing (`core/pdf_processor.py`):
- Cheap filename + first-3-pages-text classifier (`_classify_document`) routes each PDF to either a per-page **Sheet** pipeline (drawings) or a whole-PDF **DocumentBundle** pipeline (bid packages, project manuals, blank bid forms).
- Drawing-set veto via `_DRAWING_FILENAME_RES` keeps a 1000-page drawing PDF from being bundle-routed because of a stray "SOLICITATION" hit on page 1.
- Government solicitation filename signals (`Sol_*`, `ESBD_*`, `RFCSP`, `_Solicitation_`) route correctly.

Sheet classification (`core/sheet_classifier.py`):
- Two-stage. If the title-block heuristic in `pdf_processor._guess_sheet_number_and_discipline` already gave us a discipline AND `_heuristic_classify` finds a sheet-type keyword in the title, we skip the LLM. Otherwise the classifier prompt (`prompts/classifier.txt`) runs against the rendered PNG.

Deterministic drawing pre-pass — **F3, fully deterministic, no LLM** (`core/extraction/drawing_prepass.py`):
- Title block: `project_name`, `project_number`, `sheet_number`, `sheet_title`, `discipline` (inferred from sheet-number prefix), `scale`, `scale_factor`, `date`, `revision`, `drawn_by`, `checked_by`. Pattern-matched against the page's vector text. Scale strings parsed into a numeric paper-inches-per-real-world-inch factor.
- Dimensions: feet-inches with fractions, decimal feet, plain inches, metric (mm / cm / m), all normalized to inches. Filtered to `0 < inches <= 5000` to drop OCR garbage.
- Schedule tables: detected via `page.find_tables()`. Each table is classified as door / window / room / finish / unknown by header-keyword overlap, then emitted as a `Schedule` with `headers: list[str]` + `rows: list[ScheduleRow]` where each row is a `dict[str, str]` keyed by column header.
- Confidence rubric (`_score`): sheet_number + discipline (0.30), project_name (0.20), parseable scale (0.15), ≥ 1 schedule (0.20), ≥ 5 dimensions (0.15). Confidence ≥ 0.65 means the LLM call is skipped entirely.

Vision-LLM extraction (`core/extractors.py`, `prompts/architectural.txt`, `prompts/mep.txt`, etc.):
- Dispatched by `_select_prompt(sheet)` based on discipline + sheet_type.
- Prompts return JSON conforming to `SheetExtraction` shape — `rooms`, `doors`, `windows`, `structural`, `mep`, `spec_sections`, `site`, `raw_takeoffs`, `warnings`.
- F3 result is injected as a "DETERMINISTIC CONTEXT" block in the prompt when the confidence is below threshold but non-zero, so the LLM doesn't re-extract what we already know.
- `raw_takeoffs` is the LLM's own first-pass quantity guess (used as a supplement to the entity-derived takeoffs).

Bundle (text-only) extraction (`core/extractors.py: extract_bid_package`, `extract_project_manual`, `extract_bid_form`):
- One LLM call per whole PDF using a text prompt — much cheaper than per-page vision.
- `BidPackage` carries the trade scope: owner / GC, csi_divisions, csi_sections, inclusions, exclusions, alternates, unit_prices, referenced_drawings, referenced_specs.
- Supporting-document heuristic (`_supporting_doc_hint`) cheaply classifies wage determinations, sample CSAs, tax certs, HSP forms, UGSC, etc. before the LLM call and seeds the prompt with a classification hint.

Reconciliation (`core/takeoff.py: reconcile`):
- Domain entities deduped: rooms by (number, name) with fuzzy name fallback; doors by `mark`; windows by `mark`; structural by (kind, mark, size); MEP by (discipline, category, normalized description); specs by `csi_section`; site by max-of-numeric-field across sheets.
- `_derive_takeoffs` synthesizes `TakeoffItem`s from the deduped entities: slab on grade from gross room area, rough carpentry, floor-finish buckets, painted walls, gypsum board, resilient base, door / hardware EA, windows EA, structural by material, MEP by category, site lines.
- `_merge_takeoffs` merges takeoffs that share `(csi_section or csi_division, normalized description, unit)` — this is the only cross-sheet dedup for TakeoffItems.

Pricing (`core/estimator.py: price_takeoff`):
- Lookup order: CWICR (TF-IDF first pass + MiniLM re-rank against 55k rows) → seed `config/cost_database.json` (47 entries) → `(no match)` placeholder at $0.
- Unit-mismatch detection on both layers: if takeoff unit != cost-DB unit, the line is `suppressed=True` and excluded from totals (calibration v2's $34,608 phantom-line bug).
- Waste factor applied per CSI division (`_WASTE_BY_DIVISION`) when CWICR wins.

Export (`core/exporter.py`, `core/exporter_pdf.py`):
- Excel with 8 sheets: Project Info, Bid Packages, Scope Matrix, Line Items, Rooms, Doors, Windows, Sheets, Warnings.
- Client-ready quote PDF with payment schedule and signature block.

### 1.2 What is fully deterministic versus LLM-assisted

| Layer | Module | LLM involvement |
|---|---|---|
| Document type routing | `core/pdf_processor.py:_classify_document` | None (filename + regex) |
| Sheet number + discipline from title-block text | `pdf_processor._guess_sheet_number_and_discipline` | None |
| Sheet type from title keyword | `sheet_classifier._heuristic_classify` | None (when title hits a keyword) |
| Sheet type from image | `sheet_classifier.classify_sheet` stage 2 | Vision LLM (`prompts/classifier.txt`) |
| **Title block extraction (drawings)** | `drawing_prepass._extract_title_block` | **None** |
| **Dimension extraction (drawings)** | `drawing_prepass._extract_dimensions` | **None** |
| **Schedule table detection** | `drawing_prepass._extract_schedules` via `page.find_tables()` | **None** |
| Schedule semantic classification | `drawing_prepass._classify_schedule` | None (header-keyword overlap) |
| Door / window / room rows from prepass schedules | `extractors._build_from_prepass` | None |
| Sheet-level rooms / doors / windows / MEP / structural / spec / raw_takeoffs (when prepass confidence < 0.65) | `extractors.extract_sheet` → discipline-specific prompts | Vision LLM |
| Bid-package scope (inclusions, exclusions, alternates, unit prices, owner/GC, project info) | `extractors.extract_bid_package` | Text LLM |
| Project-manual summary + project-info pull | `extractors.extract_project_manual` | Text LLM |
| Bid-form unit-price extraction | `extractors.extract_bid_form` | Text LLM |
| Cross-sheet dedup of domain entities | `takeoff.reconcile` (`_dedupe_rooms`, `_dedupe_by_key`) | None (rapidfuzz) |
| Synthesizing `TakeoffItem`s from entities | `takeoff._derive_takeoffs` | None |
| Cross-sheet `TakeoffItem` merge | `takeoff._merge_takeoffs` | None |
| CWICR cost matching | `core/pricing/cwicr_matcher.py` | None (TF-IDF + MiniLM) |
| Seed-DB cost lookup | `estimator.CostDatabase.lookup` | None |

### 1.3 What we explicitly do NOT extract today

Mapping each gap to the scope category it lives in:

| Gap | Affected category | Concrete consequence |
|---|---|---|
| Schedule rows do not flow to typed `TakeoffItem`s — only to `doors / windows / rooms` lists, then to `_derive_takeoffs` heuristics | Schedules | A door schedule with 47 marks gets summarized as one "Hollow metal doors" line + one "Solid-core wood doors" line based on the LLM's textual classification of `door.type`. The schedule's full structure (fire rating, hardware set, frame type, glazing) is recorded but not used to drive pricing variation. |
| No geometric measurement from the drawings | LF wall, SF flooring/ceiling/paint, perimeter, polygon area | `TitleBlockData.scale_factor` is parsed but **never used downstream**. There is no module that converts a measured pixel distance on a rendered page back to real-world feet. Room.area_sqft and Room.perimeter_ft are populated only when the LLM happens to read a label from the drawing or the schedule. |
| No per-room finish takeoff | SF flooring / ceiling / paint by finish | `_derive_takeoffs` buckets finishes only when both `Room.area_sqft` AND `Room.floor_finish` are set on the same Room object. In practice the floor plan often only has room number / name, while the finish schedule has the finish — the reconciliation merges them by number, but if either side is missing the line drops. There is no explicit "for each room, take floor SF × floor finish, wall LF × ceiling height × wall finish, ceiling SF × ceiling finish" walker. |
| Schedule extractor is generic, not specialized | Schedules | Door schedule, finish schedule, fixture schedule, panel schedule, RTU schedule, plumbing fixture schedule all hit the same `find_tables()` path. The `_classify_schedule` step picks `door / window / room / finish / unknown` but specialized fields (rating, hardware set, glazing, manufacturer, electrical load, CFM, GPM, kW) are stuffed into a generic `cols: dict[str, str]`. |
| No cross-sheet de-duplication of typed entities at the **TakeoffItem level** beyond `(csi_section, normalized description, unit)` collision | All categories | If the door schedule on `A-601` says 47 doors, and the architectural floor plan extraction estimates "42 doors" as a `raw_takeoff` line, both lines survive `_merge_takeoffs` because the descriptions and confidences differ enough that the normalized key doesn't match. Today's only safety net is rapidfuzz dedup on `DoorEntry.mark`, which only fires when both sources emit a mark string. |
| No symbol detection on plans | Countable MEP devices (receptacles, fixtures, sprinkler heads, fire alarm devices) | The MEP prompt asks the LLM to count fixture symbols from the image. There is no vision pipeline that detects, locates, and counts symbol instances against a known symbol legend. |
| No OCR for scanned drawings | Everything on scanned pages | `Sheet.is_scanned = len(embedded_text.strip()) < 20` is computed but only used as a flag. The prepass returns confidence 0 on a scan because there's no vector text; the LLM still runs against the rendered PNG, but PyMuPDF's `find_tables()` returns nothing, so no deterministic schedule extraction is possible. There is no `tesseract` or `paddleocr` dependency. |
| No CAD / IFC import | Everything | The pipeline only consumes PDFs. Native `.dwg`, `.dxf`, or `.ifc` files (when the owner makes them available) would be a much higher-fidelity source for geometric quantities. No `ezdxf` dependency. |
| No spec → drawing cross-reference | Schedule disambiguation, MEP rough-in | Spec sections (e.g. "Section 08 11 13 — Hollow Metal Doors") are extracted but not cross-walked to door schedule rows. Doing so would let us upgrade a "DOOR D01" with `type=null` from the schedule into a definite "hollow metal door, 20-min rated, lever lockset HW-1" using the spec. |
| ~~No confidence-aware pricing~~ — **SHIPPED in Phase T6.** | All | Previously: `TakeoffItem.confidence` was stored but `price_takeoff` ignored it. As of this commit, every emitted `CostLine` carries a `CostBand` (`AUTO_APPROVE` ≥ 0.85 / `OPERATOR_REVIEW` 0.65–0.84 / `HAND_TAKEOFF` < 0.65 ∨ suppressed); HAND is excluded from `Estimate.grand_total` and surfaced as a dedicated worklist in Excel + PDF + Streamlit. See Phase T6 below. |
| No human-verification UI workflow for line-level review | All | The Streamlit UI surfaces the priced lines and lets the user re-edit unit costs, but there is no first-class "approve / reject / correct quantity" workflow that captures the correction back into the schema for the next run. |

### 1.4 Calibration v3 evidence

The `exports/calibration_v3/CALIBRATION_REPORT.md` artifact (17-PDF run against real Texas government solicitations, `gpt-4o`, `--no-drawings` to skip the heavy drawing extraction) gives us a real datapoint on the bundle path:

- 16 / 16 bundles extracted successfully (after F3 and the retry-aware LLM client landed).
- Bid-form extraction now produces 9 unit-price lines across the run (was 0 silently).
- Project-info voter picks a coherent record across one opportunity instead of a Frankenstein.
- The **drawing extractor was not exercised** in v3 (`--no-drawings`). A v4 with drawings on is the next calibration milestone.

A documented gap from v3: the drawing extractor emits `unit: "LS"` for every wood-framing item, which collides with the unit-mismatch suppressor in `06 10 00` (priced per SF). This is a prompt-engineering issue on `prompts/architectural.txt`, addressed implicitly by Phase T2 below.

---

## 2. Target end-state

Realistic accuracy bands by scope category. These are calibrated against the codebase: schedules and counts are tractable because the data is already tabular or pre-counted; LF and area takeoffs require geometric measurement and live in a fundamentally harder band; MEP rough-in is spec-driven and only as good as the spec is structured.

| Scope category | Realistic accuracy | Effort | What's needed |
|---|---|---|---|
| Schedules — door, window, finish, equipment, panel, fixture, RTU | 85–95% | Medium | Specialized schedule extractors keyed on header pattern; spec cross-ref to fill in nulls; OCR for the scanned-schedule edge case |
| Countable items — doors, windows, plumbing fixtures, electrical devices, panels, RTUs, sprinkler heads | 80–90% | Medium | Vision LLM with disciplined prompts + cross-sheet dedup at the TakeoffItem level + symbol-legend detection for higher-volume devices |
| Area-based — SF flooring / ceiling / paint by finish per room | 70–85% | Medium-High | Room schedule × finish schedule × floor plan walker; per-room SF wall = perimeter × ceiling height; per-room SF floor = area; per-room SF ceiling = area; openings deducted from wall area |
| Linear — LF wall partition, LF baseboard, LF chair rail, LF pipe runs, LF conduit runs | 55–75% | High | Scale-aware geometric measurement (paper-pixel distance × scale_factor); polyline extraction from PDF vector layers; reconciliation against schedule + spec hints |
| MEP rough-in — branch wiring, conduit, fittings, pipe routing | 30–50% | Very High | Spec-driven allowance per fixture / device, not drawing-driven. Pipe / conduit routing from drawings is unreliable; rough-in factors per CSI section are more accurate |
| Custom assemblies — millwork, casework, custom storefronts, complex stairs, ornamental metal | < 30% | N/A | Always human. The variation between projects is wider than any reasonable training set covers. |
| Hidden / below-grade — existing foundations, existing utility lines, asbestos, soil conditions | 0% | N/A | Site visit + geotech report + selective demolition contingency |

Targets above are **steady-state per-line accuracy** on a real bid set after all phases below ship, NOT total-bid accuracy. Total-bid accuracy is bounded by the weakest category and by site-visit findings; a tool that gets schedules at 90% and LF wall at 65% will produce a total at maybe 75% accuracy on a typical light-commercial TI.

---

## 3. Phased plan

Six phases. Phases T1–T5 follow the suggested ordering from the brief, with one addition (T6: confidence-aware pricing and a human-verification workflow) because we already store `TakeoffItem.confidence` and the estimator currently ignores it, and we'd benefit from closing that loop before throwing more extraction at the pipeline.

### Phase T1 — Specialized schedule extraction

**Status:** IN PROGRESS — door-schedule slice landed (deterministic pre-pass only; downstream `TakeoffItem` synthesis is deferred to Phase T2).

**1-line goal:** Convert F3's already-detected schedule tables into typed `TakeoffItem`s, with per-schedule-kind fields and spec cross-reference, deterministically.

**Deliverables:**
- New `core/extraction/schedule_extractor.py` with:
  - `extract_door_schedule(schedule: Schedule, specs: list[SpecSection]) -> list[TakeoffItem]` — produces one `TakeoffItem` per door + one aggregated hardware-set line. Pulls type, rating, frame, hardware-set columns. Cross-references CSI 08 11 13 / 08 14 16 spec sections when present to default the type if the schedule has `type=null`.
  - `extract_window_schedule(schedule: Schedule, specs: list[SpecSection]) -> list[TakeoffItem]`
  - `extract_finish_schedule(schedule: Schedule, rooms: list[Room]) -> list[TakeoffItem]` — joins finish-schedule rows to rooms by `room.number`, emits per-finish SF lines.
  - `extract_equipment_schedule(schedule: Schedule) -> list[TakeoffItem]` — RTUs, ERUs, exhaust fans (Division 23).
  - `extract_panel_schedule(schedule: Schedule) -> list[TakeoffItem]` — electrical panels (CSI 26 24 16).
  - `extract_fixture_schedule(schedule: Schedule) -> list[TakeoffItem]` — plumbing fixtures (CSI 22 40 00).
  - A `register_extractor(kind: str, fn)` registry so adding a new schedule kind is one file change.
- New `core/extraction/schedule_classifier.py` (or fold into `drawing_prepass._classify_schedule`) — extend the keyword sets and recognize "equipment", "panel", "fixture", "MEP" headers. Today the classifier collapses everything that isn't door / window / room / finish to `"unknown"`.
- Hook into `extractors._build_from_prepass`: after building `doors / windows / rooms`, run the schedule-extractor dispatcher to ALSO emit `raw_takeoffs` from the schedules. These are higher-confidence (≥ 0.90) than the LLM-derived takeoffs and should win in `_merge_takeoffs`.
- Tests:
  - `tests/test_schedule_extractor.py` — table-driven, ~12 tests. Synthesized `Schedule` objects of each kind; assert the resulting `TakeoffItem`s carry the right `csi_section`, `unit`, and `confidence`.
  - One end-to-end test that builds a PDF with a door schedule + finish schedule, runs `prepass_drawing_page` → `_build_from_prepass`, and asserts both the entity rows and the typed takeoff rows land.
- Documentation: add a "Schedule extraction" section to `README.md` under "Deterministic drawing pre-pass".

**Scope:** Schedules category, plus the door / window / fixture / panel slice of the Countable Items category.

**Expected accuracy uplift:**
- Schedules: from ~70% (current LLM-with-prepass-context) to **85–92%** on schedule-bearing sheets. The uplift is "if the schedule table was detected by `find_tables()`, every row is captured with the right CSI section."
- Countable items (the door / window / fixture / panel subset): from ~75% (LLM-only on plan sheets) to **85–90%**. Schedules are the most reliable source for these counts; once we lift them deterministically, the LLM-only sheet path becomes a backup.

**Effort estimate:** M (3–5 days).

**Dependencies:**
- Already done: F3 prepass detection of schedule tables; rapidfuzz; PyMuPDF.
- New: none. This phase intentionally adds no new runtime dependency.

**Risk / pitfalls:**
- Schedules with merged cells confuse `page.find_tables()`. Mitigation: on detection failure, fall back to the existing LLM-with-prepass-context path; the LLM still gets to see the deterministic dimensions and title block.
- Office-specific column naming. The `_pick` helper in `extractors._build_from_prepass` already tolerates `"MARK" | "DOOR" | "NO" | "NUMBER" | "ID"`; extend the candidate lists per schedule kind.
- Schedule on a scanned PDF: `find_tables()` returns nothing. T1 silently no-ops in that case (the LLM path still runs). Real fix is T7 (OCR), called out below.
- Spec cross-reference is fuzzy. A door schedule with `type=null` and a spec section "08 11 13 — Hollow Metal Doors and Frames" plausibly maps to HM, but the spec might document multiple types. Mitigation: do the cross-ref only when there's exactly one matching spec section per door type, and only set `confidence = 0.85` (not 0.95) on inferred values.

**Validation strategy:**
- Hand-count a gold set from one of the three drawing sets already on disk: `inbox/opportunities/attachments/2026-05-21/26-007 Carr EFA Dressing Room Renovation Project Manual.pdf`, the Carr EFA drawings addendum, and the Cmd Post + NDI drawings (`DDPM262101_Alter CP and NDI_Plans (20260512).pdf`). Hand-counted: door count, window count, plumbing fixture count, panel count. Expected to fall inside ±2 on each, or 95% accuracy by EA.
- Synthetic-PDF unit tests in `tests/test_schedule_extractor.py` cover the column-naming variations.

**No-go signal:**
- `find_tables()` detects < 50% of the door schedules in the gold set when manually inspected. That would mean the deterministic table detection isn't reliable enough to specialize, and we'd need to back off to LLM-augmented schedule extraction (Phase T2 would absorb the work).
- Hand-count accuracy on the gold set lands below 80%. Indicates the column-mapping logic needs more office-standard variants than is tractable; revisit with an LLM-fallback for schedule rows the deterministic path can't classify.

**Implementation notes (door-schedule slice, this commit):**
- **New typed result** rather than re-purposing the loose `Schedule`/`ScheduleRow` pair. `DoorScheduleResult` + `DoorRecord` (Pydantic in `core/schemas.py`, mirror dataclasses in `core/extraction/door_schedule.py`) carry door-specific fields (`width_in`, `height_in`, `thickness_in`, `hardware_set`, `fire_rating`, `frame`, ...) directly, alongside raw cell text for audit. `DrawingPrepassResult.door_schedule` is the new optional attachment on the existing pre-pass result; the generic `schedules` list is unchanged.
- **Detection** is two-signal: literal `"DOOR SCHEDULE"` text on the page OR a `find_tables()` header row that has a tag column (MARK/NO/NUMBER/...) plus at least one door-specific column (FRAME/HARDWARE/HDW/RATING/FIRE) plus at least one dimensional column. The door-specific requirement disambiguates from neighbouring window schedules that share `MARK/TYPE/WIDTH/HEIGHT` headers.
- **Dimension parsing** in `parse_dimension()` handles `3'0"`, `3'-0"`, `3' - 0 1/2"`, `36"`, `3 ft 0 in`, and bare `3'`; combined `SIZE` cells like `3'-0" x 7'-0"` are split via `_parse_size_cell`. Plain bare integers (no unit) intentionally return `None` because they're too ambiguous in a schedule context.
- **Fallback path**: if `find_tables()` yields no door table, a y-coordinate clustering over `page.get_text("dict")` spans rebuilds a header + data-rows shape. Kept conservative (requires a header row that matches the same heuristic) to avoid false positives.
- **Integration** is via `_maybe_extract_door_schedule()` inside `drawing_prepass.py`, called from both `prepass_drawing_page()` and `prepass_drawing_pdf()`. No new flag, no new dependency, no change to `extractors._build_from_prepass()` — the typed result rides along on the existing prepass surface. Downstream `core/takeoff.py` consumption is deferred to a subsequent T1 follow-up / T2 slice as called out in the brief.
- **Tests** in `tests/test_door_schedule_extraction.py` build synthetic 1-page PDFs with real grid tables (`fitz.draw_line` + `insert_text`) so `find_tables()` exercises the same code path as the production drawing sets — no binary fixtures shipped.

**Known limitations of this slice:**
- Multi-column door schedules (e.g. one office's layout that wraps the schedule into two side-by-side blocks on a single sheet) collapse into one row each; `find_tables()` doesn't reconstruct the second block separately.
- Scanned PDFs still no-op here (no vector text → `find_tables()` returns nothing → fallback yields no spans). Real fix lives in Phase T9 (OCR).
- Door↔room association (the `room_from` / `room_to` columns called out in Phase T5's deliverables) is not yet extracted; only `mark`, type, dimensions, frame, hardware, rating, remarks are pulled. Adding it is a small follow-up.
- `DoorRecord` does not yet flow into `TakeoffItem` — that's the explicit T2 work item.

**Suggested next slices** (good candidates for the next T1 follow-up):
- Window schedule (same pattern, swap `FRAME/HARDWARE` for `GLAZING/OPERATION`).
- Room-finish matrix (joins room schedule × finish schedule by `room_number`; pairs naturally with Phase T5's per-room finish takeoff).
- Plumbing fixture schedule (typically on `P-001`; columns: MARK / DESCRIPTION / MFR / MODEL / HW / CW / WASTE / VENT).
- Panel schedule and equipment / RTU schedules (Division 26 / 23) — same dispatch pattern as door, different keyword set.

---

### Phase T2 — Sheet-type-specialized item extraction

**Status:** IN PROGRESS — door-schedule → `TakeoffItem` synthesis landed in this commit. The per-sheet-class prompt-engineering work below is still pending.

**Implementation notes (door-schedule → TakeoffItem synthesis slice, this commit):**
- **New module:** `core/extraction/takeoff_synthesis.py` exposes a single pure function `synthesize_door_takeoff_items(schedule: DoorScheduleResult, *, sheet_id: str | None = None) -> list[TakeoffItem]`. One `TakeoffItem` per `DoorRecord`; `quantity=1.0`, `unit="EA"`; `csi_division="08"` on every row.
- **CSI family heuristic** (keyword substring match on the upper-cased `type + material + frame` haystack, ordered specific → generic):
  - `HM` / `HOLLOW METAL` → `08 11 13` Hollow Metal Doors and Frames
  - `STOREFRONT` / `ALUMINUM` / `ALUM` → `08 11 16` Aluminum Frames
  - `GLASS` / `GLAZED` → `08 80 00` Glazing
  - `SCWD` / `WOOD` / `WD` / `SC` → `08 14 13` Wood Doors (matches the Phase T2 brief's choice of `08 14 13` over the older `08 14 16` used by `_derive_takeoffs`; the deterministic rows will eventually displace those LLM-derived aggregates in Phase T3)
  - Unmatched → `08 10 00` Doors and Frames (generic)
- **Confidence rubric:** `0.92` when both `mark` and `type` are present (truthy after `.strip()`); `0.80` when exactly one is present; `0.60` when neither is. Schedules surface a `mark`-only row whenever the `TYPE` column was missing or empty; those land at `0.80` and stay in the output for the caller to filter if desired.
- **Source tagging:** the schema has no dedicated `source` field, so every synthesised row's `notes` field starts with `source=door_schedule_prepass` (exported as `SYNTHESIS_SOURCE_TAG` from the module). Phase T3's dedupe pass can grep that prefix.
- **Description format:** `"Door 101A — HM 3'-0\" x 7'-0\""` when dimensions are present; falls back to `"Door 101 — HM"` when width or height is `None`; `"Door (unmarked) — Hollow Metal Door"` when `mark` is empty. Inches → feet-inches via a small private helper that tolerates fractional inches (`36.5 → 3'-0.5"`).
- **Integration:** `core/takeoff.py: reconcile()` collects synthesised rows alongside the existing per-sheet accumulators and appends them **after** `_merge_takeoffs(...)` so each door survives as its own line. The append happens once per sheet whose `prepass.door_schedule` is populated; sheets without a door schedule produce zero new rows.
- **Tests:** 27 new tests in `tests/test_takeoff_synthesis.py` covering happy path, CSI mapping (parametrised over 12 type strings + material-only fallback), the 4 confidence rubric cells, dimension formatting (feet-inches + fractional inches + partial-dim safety), and three end-to-end smoke tests through `reconcile()` (synthesised rows appear, missing-schedule emits no T2 rows, LLM rows are preserved).

**Known limitations of this slice:**
- **No cross-source dedupe.** The synthesised per-door rows live alongside the existing aggregate LLM-derived rows from `_derive_takeoffs` (e.g. "Hollow metal doors: 12 EA"). On a sheet that has both a deterministic door schedule and an LLM door-count, the headline subtotal will be inflated. Phase T3 fixes this — the synthesis pass tags every row with `source=door_schedule_prepass` precisely so T3 can find them.
- **No pricing-time confidence band yet.** A `0.60`-confidence "Door (unmarked)" row prices identically to a `0.92` "Door 101A — HM 3'-0\" x 7'-0\"" row. Phase T6 (confidence-aware pricing) closes that loop.
- **CSI section change for wood doors.** The synthesiser uses `08 14 13` per the T2 brief; the legacy `_derive_takeoffs` still emits `08 14 16` for its aggregate wood-doors line. The two rows will coexist until Phase T3 dedupes them; choose `08 14 13` as the surviving section when that happens.
- **No hardware-set aggregation.** The T1 brief mentioned an aggregated hardware-set line on top of the per-door rows; this slice does not emit it. Hardware-set is preserved in the per-door row's `notes` so a downstream aggregator can roll it up. Phase T2.5 candidate.

**Suggested next slices** (good candidates for the next T2 follow-up):
- **Phase T3 dedupe — start now.** The synthesis tag (`source=door_schedule_prepass`) is in place; the obvious first dedupe rule is "for every CSI 08 division row not tagged with the prepass source, drop it when a same-mark synthesised row exists on the same sheet".
- **Phase T2.5: window-schedule extraction** by reusing the dispatcher (mirror `core/extraction/door_schedule.py` swapping `FRAME/HARDWARE` for `GLAZING/OPERATION`); the synthesis pattern in `takeoff_synthesis.py` extends one-to-one to `WindowRecord → TakeoffItem`.
- **Plumbing fixture / panel / RTU schedules** — same shape, different keyword sets and CSI sections (`22 40 00` / `26 24 16` / `23 00 00`).
- **Aggregated hardware-set line** — sum `door.hardware_set` occurrences across all synthesised rows on a sheet, emit one `08 71 00 — Door hardware sets (HW-1)` line per set with `quantity = count`.

---

### Phase T2.5 — Window-schedule extraction + synthesis + dedupe

**Status:** SHIPPED — this commit landed the full window slice (extraction → schema → prepass wire-in → synthesis → dedupe → reconcile wire-in) on top of the door-shaped T1/T2/T3 dispatcher. Suite: 305 → 386 passed (+81 tests; 1 skipped unchanged).

**Implementation notes (this commit):**
- **Module structure.** Three new modules: `core/extraction/window_schedule.py` (T1-shape extractor, dataclasses + `to_schema()` bridge), `core/extraction/window_dedupe.py` (T3-shape dedupe), plus an extension of `core/extraction/takeoff_synthesis.py` adding `synthesize_window_takeoff_items()` and `SYNTHESIS_SOURCE_TAG_WINDOW = "window_schedule_prepass"`. `core/schemas.py` gains `WindowRecord` + `WindowScheduleResult` Pydantic models and a new optional `DrawingPrepassResult.window_schedule` field alongside the existing `door_schedule`.
- **Door-vs-window discriminator (door-precedence).** Window schedules and door schedules share `MARK / TYPE / WIDTH / HEIGHT` headers, so the window header heuristic (`_looks_like_window_header`) requires a window-specific signal (`GLAZING / GLASS / OPERATION / OPER / SILL / U-FACTOR / SHGC`) in addition to the shared tag + dimensional signals. The integration hook `_maybe_extract_window_schedule()` in `drawing_prepass.py` further enforces the rule: if a page's door-schedule extraction succeeded (`door_schedule is not None AND door_schedule.doors`), the window pass is skipped entirely. The older, more-validated door detector wins on ambiguous pages; the test `test_discriminator_door_precedence_when_both_phrases_present` pins the behaviour.
- **Dimension parsing reuse.** `parse_dimension()` from `door_schedule.py` is imported verbatim — no duplication. The combined `SIZE` cell splitter is local to the window module because its `x / × / by` separator catalogue is the same as the door one (mirror, not extension).
- **U-factor / SHGC.** Two new optional float fields capture thermal-performance columns when present (typical on commercial window schedules per IECC). The header matcher uses the right-hand token (`FACTOR`) rather than the joined form so `U-FACTOR`, `U FACTOR`, and `UFACTOR` all resolve to the same column.
- **CSI mapping (six families + storefront tiering).** `_classify_window()` maps the `type + frame + material + operation` haystack to one of:
  - Aluminum windows → `08 51 13`
  - Vinyl windows → `08 53 13`
  - Wood windows → `08 52 13`
  - Metal-clad wood → `08 52 19` (checked BEFORE bare wood and BEFORE aluminum so `CLAD WOOD` routes to the more-specific section)
  - Steel windows → `08 51 23`
  - Storefront / curtain wall — size-tiered: `08 41 13` (Aluminum-Framed Entrances and Storefronts) when both dimensions ≤ 96 in. and the keyword is `STOREFRONT`; `08 44 13` (Glazed Aluminum Curtain Walls) when ANY dimension > 96 in. (8 ft) OR the keyword is `CURTAIN`. The 96 in. threshold is exposed as `_WIN_CURTAIN_WALL_DIM_IN` so a future maintainer can lift it.
  - Unknown / unmatched → `08 50 00` (Windows — generic)
- **Confidence rubric.** Identical to T2 doors: 0.92 with mark+type, 0.80 with one, 0.60 with neither. Dimensions are not part of the rubric.
- **Architectural choice α (mirror).** This slice ships `window_dedupe.py` as a sibling to `door_dedupe.py` rather than generalising both into a parametrised `dedupe_against_synthesis(*, source_tag, csi_prefix, ...)` scaffold. Reasoning: (1) the discriminators differ in three non-trivial ways (window section is a multi-prefix regex over `08 41` / `08 44` / `08 5*`, the legacy aggregate set is shorter and uses different keywords, and there is no equivalent of the door-side `Doors (type unspecified)` rollup); (2) the dedupe modules together total ~310 lines, well under the threshold where mirror-duplication starts to bite; (3) a failed generalisation mid-PR would destabilise the just-landed T3. The Phase T3 worker called out the generalisation as the next big move; it's queued as Phase T3.5 below.
- **Cross-pollination safety.** The window dedupe `_is_window_row()` matches only Division 08 rows in window-shaped CSI sections (`08 41` / `08 44` / `08 5*`) or with window-shaped descriptions — door rows at `08 11` / `08 14` / `08 71` / `08 80` are never touched. Two regression tests (`test_door_dedupe_never_touches_window_rows`, `test_window_dedupe_never_touches_door_rows`) pin this in both directions.
- **Wire-in.** `core/takeoff.py:reconcile()` collects `synthesized_window_items` alongside the existing door collection, appends them after `_merge_takeoffs(...)`, then calls `dedupe_windows_against_synthesis(...)` after the existing door dedupe. Two targeted additions, no refactor of the existing T2/T3 path.
- **Tests.** 81 new tests across three files: `tests/test_window_schedule_extraction.py` (18 tests, including the multi-page discriminator regression that pins the door-precedence rule), `tests/test_window_takeoff_synthesis.py` (34 tests, covering all six CSI families + the storefront / curtain wall size tier + confidence rubric + dimension formatting + the three reconcile-loop integration smoke tests), and `tests/test_window_dedupe.py` (29 tests, including a 12-row parametric sweep of the legacy-aggregate regex and the two cross-pollination safety regressions).

**Known limitations of this slice:**
- **Exact-substring mark matching only** (inherited from T3 dedupe). A synthesised window with mark `"W1"` does NOT dedupe an LLM row with mark `"W101"` — neither is a token of the other. Future fuzz-match pass closes this gap.
- **No room-association.** Window-to-room linkage (similar to the door `room_from / room_to` follow-up flagged in T1) is not extracted; if a future Phase T5 wants per-room window opening deduction it needs to add it.
- **Hardware aggregation not addressed** (this is a door-side limitation flagged in T3; T2.5 inherits the same gap for any future window-side hardware aggregate the LLM might emit).
- **Storefront size threshold is a single global constant.** Some offices treat storefronts and curtain walls as one section regardless of size; the constant is documented but not yet configurable per project.

**Suggested next slices:**
- **Phase T3.5 — generalise the dedupe-by-source-tag pattern.** ~~Refactor `door_dedupe.py` + `window_dedupe.py` into a parametrised `dedupe_against_synthesis(items, *, source_tag, section_prefixes, legacy_aggregate_regex, family_label)` shared scaffold.~~ **SHIPPED** — see the Phase T3.5 section below.
- **Phase T4: finish schedule + room-finish matrix extraction.** ~~Same dispatch shape (`detect → extract → synthesise → dedupe`); column candidates `ROOM / FINISH / FLOOR / WALL / CEILING / BASE`. Emits per-finish SF lines instead of EA.~~ **SHIPPED** — see the Phase T4 section below. Per-room expansion (1 record → 3-7 items) plus T3.5 leverage realized (finish_dedupe.py at 80 LOC vs. door_dedupe at 82, window_dedupe at 94).
- **Phase T2.6 (continued): equipment / RTU / panel / fixture schedules.** ~~Same shape, swap keywords + CSI codes per discipline (`23 00 00` / `26 24 16` / `22 40 00`).~~ **Electrical-panel slice SHIPPED** — see the Phase T2.6 section below. Lighting fixture (`26 51 ...`), mechanical/HVAC (`23 00 00`), and plumbing fixture (`22 40 00`) schedules remain as next-slice candidates.

---

### Phase T2.6 — Electrical-panel-schedule extraction + synthesis + dedupe

**Status:** SHIPPED — this commit landed the full electrical-panel slice (extraction → schema → prepass wire-in → 1-to-4 synthesis → dedupe → reconcile wire-in) as the FOURTH dispatcher on the door/window/finish scaffold, mirroring the T1+T2+T2.5+T3+T3.5+T4 pattern. Suite: 1029 → 1121 passed (+92 new tests; 1 skipped unchanged). Electrical-panel schedules are the highest-dollar single artefact in BPC's calibration set (Division 26 leads the cost distribution), so this slice has the largest accuracy-leverage of any single T-phase shipped to date.

**Implementation notes (this commit):**
- **Module structure.** Three new modules: `core/extraction/panel_schedule.py` (deterministic extractor; ~900 LOC including the multi-panel block-splitter and the two-column circuit-table layout handler), `core/extraction/panel_dedupe.py` (thin wrapper over the T3.5 generic scaffold; ~110 LOC), plus a ~250-LOC extension of `core/extraction/takeoff_synthesis.py` for the 1-to-4 fan-out. `core/schemas.py` gains `CircuitEntry` + `PanelRecord` + `PanelScheduleResult` Pydantic models and a new optional `DrawingPrepassResult.panel_schedule` field alongside the existing `door_schedule` / `window_schedule` / `finish_schedule` / `room_schedule`.
- **Panel-ID detection (the bear).** A naive ``\b(?:PNL|PANEL|RP|DP|MP|MDP|LP|SDP|HP)[\s\-_]?[A-Z0-9]+\b`` regex would leak ``SCHEDULE`` as a panel ID against ``PANEL SCHEDULE`` titles, and similarly leak the panel-mark ``LP-1`` out of a description cell that reads ``Subpanel LP-1``. The fix lands as a two-pass `_all_panel_id_matches()`: (1) **short-prefix pass** with the unambiguous prefixes (``PNL`` / ``MDP`` / ``RP`` / ``DP`` / ``MP`` / ``LP`` / ``SDP`` / ``HP`` — none collide with English words) and a horizontal-only separator class (``[ \t\-_]?``, NOT ``\s``) so ``MDP\n277/480V`` doesn't fuse into ``MDP-277`` across a newline; (2) **long-prefix pass** for the ``PANEL <X>`` form, filtered against a noun blocklist (``_PANEL_NON_ID_WORDS`` — ``SCHEDULE``, ``SCHED``, ``BREAKER``, ``LOAD``, ``BUS``, ``MAIN``, ...) so ``PANEL SCHEDULE`` is rejected outright. Both passes additionally run each candidate through `_is_crossref_context()` which scans the 30 chars preceding the match (clipped to the current line) for a cross-reference anchor word (``SUBPANEL`` / ``SUB`` / ``TO`` / ``FROM`` / ``FED BY`` / ``SERVES`` / ...) — when one fires, the candidate is a load-row description reference (the LP-1 of ``Subpanel LP-1``) and is dropped. Three regression tests pin the behaviour: ``test_extract_panel_mlo_no_main_breaker`` (LP-1 / LP-2 cross-refs), ``test_extract_panel_schedule_phrase_without_table`` (PANEL SCHEDULE noun blocklist), and the dedicated ``_panel_id_pattern_matches_common_forms`` sweep across all 12 documented panel-ID shapes.
- **Two-column circuit-table layout.** Real panel schedules typically lay out odd circuits (1, 3, 5, ...) down the left half of a single physical table and even circuits (2, 4, 6, ...) down the right half. The extractor detects this layout via `_ckt_column_positions()` (a second CKT-shaped header indicates a split point), splits the headers + data rows accordingly via `_split_two_column_table()`, then calls `_records_from_table_half()` on each half independently and concatenates. Single-column layouts (where the second CKT column is absent) drop straight through to the single-pass path. The two-column smoke test (``test_extract_two_column_panel_layout``) pins both halves landing.
- **AMPS vs. PHASE substring collision.** A PHASE column is often labelled simply ``A`` / ``B`` / ``C`` (one letter), and the substring-tolerant header matcher would steal the ``AMPS`` index because ``"A" in "AMPS"`` evaluates true. Same fix Worker U promoted out of `door_schedule.py` to `_header_index_excluding()` and into `finish_schedule.py`: pin AMPS first (specific), then re-pick PHASE with AMPS excluded. ``test_phase_letter_does_not_collide_with_amps_header`` regresses the bug. The import path `from .door_schedule import _header_index_excluding` works as-is — no shared-helper promotion needed for this slice.
- **Header-block parsing.** Voltage (``120/208V`` / ``277/480V`` / ``120V``), phase count (1 or 3, defaults to 3 for the dual-voltage forms by NEC convention), main breaker amps (``200A MCB`` / ``MCB 200A``), bus amps (``400A BUS`` / ``BUS 400A`` / ``MLO`` form with optional rating), MCB/MLO designation, and the feeder conductor (``3/0 AWG Cu`` / ``500 KCMIL Al``) + conduit (``2 inch`` / ``2"`` / ``2 IN``) all parsed via independent anchor-proximity regexes against the header text. Bus-amps fallback: when only MCB is published and no bus rating exists, the bus amps default to the MCB rating (NEC convention).
- **Synthesis fan-out (1-to-4 per panel).** Each `PanelRecord` synthesises into:
  1. **Panel enclosure** — 1 EA at `26 24 16` (panelboard, bus ≤ 400A) or `26 24 13` (switchboard, bus > 400A). Classification falls back to `main_breaker_amps` when `bus_amps` is absent. Confidence = `panel.confidence` (typically 0.85+).
  2. **Branch breakers** — N EA at `26 28 16`, grouped by amp size (e.g. 20A × 12 + 30A × 4 + 50A × 2 → three distinct `TakeoffItem`s). Stable ascending order by amperage. Multi-pole breakers count as N rows (matching the schedule's per-pole publication, not the physical breaker count — the calibration data shows this matches the estimator's mental model better than collapsing). Confidence = 0.85.
  3. **Feeder conductor** — 1 LF row at `26 05 19`, quantity = **50 LF** parametric default, confidence = **0.55**. The 0.55 default lands the row in `HAND_TAKEOFF` band (< 0.65 threshold) by construction so the estimator can't miss supplying a real run length.
  4. **Feeder conduit** — 1 LF row at `26 05 33`, same 50 LF / 0.55 default.
- **Parametric feeder rationale (why 50 LF?).** Feeder lengths require sheet-level routing knowledge (panel location + main distribution location + path) that the panel schedule itself never publishes. The 50 LF placeholder is a deliberately conservative *non-zero* default: it ensures the row appears in the priced output so the estimator notices it (vs. a 0-LF row that quietly contributes $0 and might be missed), and the 0.55 confidence guarantees it routes to the HAND queue so it's never silently auto-approved. The 50 LF magnitude is the calibration set's median panel-to-MDP run on a typical mid-size commercial floor plan — chosen so the parametric line is realistic enough to flag the right band of cost without committing to a wrong number.
- **CSI mapping rationale (panelboard vs. switchboard).** `_PANEL_BOARD_BUS_THRESHOLD_A = 400` (exposed as a module constant). NEC + the Construction Specifications Institute classify ≤ 400A bus equipment as a panelboard (`26 24 16`); > 400A switches to switchboard / distribution board (`26 24 13`). The threshold is strict on the > side (exactly 400A is panelboard, 401A is switchboard); the unit test `test_enclosure_threshold_is_strict_above_400a` pins the boundary.
- **Dedupe scope (intentional asymmetry).** `panel_dedupe.py` runs against CSI prefixes ``26 24`` (panelboards + switchboards) and ``26 28`` (circuit breakers) ONLY. Feeder conductor (`26 05 19`) and feeder conduit (`26 05 33`) are INTENTIONALLY excluded from dedupe — the parametric 50 LF synthesis is a placeholder, not an estimate, so the LLM's run-length value (when present) should land in the worklist for the estimator to compare. Two regression tests pin this: ``test_dedupe_feeder_wire_llm_row_preserved`` and the cross-pollination guard ``test_dedupe_receptacles_not_suppressed`` (CSI `26 27 26` is outside the prefix set).
- **Legacy-aggregate regex widening.** The original ``[,:\-].*?`` tail required a delimiter immediately after the prefix word (e.g. ``"Electrical Panel: PNL-A"`` matched, but ``"Electrical Panel A, 200A"`` did NOT because the delimiter was after the ID, not before it). Widened to ``(?:[\s,:\-].*?)?`` so the optional tail also accepts ``"Electrical Panel A, 200A"`` (space-led continuation). The legacy regex still requires a word-boundary after the prefix word so unrelated descriptions like ``"Electrical Panel Mounting Hardware"`` (which lives in a different CSI section anyway) don't false-positive.
- **Schema overlap with Worker Y.** Worker Y is shipping Phase T7 (`CostSourceTier` enum + `price_confidence` field on `CostLine`) against the same `core/schemas.py`. T2.6 adds its three new classes (`CircuitEntry`, `PanelRecord`, `PanelScheduleResult`) in a dedicated block after `RoomScheduleResult` and before `DrawingPrepassResult`, and the only edit to `DrawingPrepassResult` itself is adding the optional `panel_schedule` field — disjoint from Worker Y's `CostLine` modifications. No conflict observed in this commit.
- **Wire-in.** `core/extraction/drawing_prepass.py:_maybe_extract_panel_schedule()` runs alongside the other schedule extractors (NOT inside the door/window/finish precedence chain, since panel schedules typically live on E-series sheets the upstream detectors leave alone). `core/takeoff.py:reconcile()` collects `synthesized_panel_items` after the existing finish synthesis, appends them to `all_takeoffs`, then calls `dedupe_panels_against_synthesis(...)` after the existing door/window/finish dedupes. Two targeted additions; no refactor of the existing T1–T5 paths.
- **Tests.** 92 new tests across four files: `tests/test_panel_schedule_extraction.py` (40 tests covering all keyword variants, table-header detection, header-block parsing for voltage / MCB / MLO / bus / feeder, the two-column layout, multi-panel pages, edge cases including the cross-ref-context regression, panel-ID variations, feeder shapes, the confidence rubric, and integration with `prepass_drawing_page` + schema round-trip), `tests/test_panel_takeoff_synthesis.py` (29 tests across happy-path, panel-enclosure routing including the 400A boundary, branch-breaker grouping + ordering, parametric feeder defaults, multi-panel + sheet propagation, and the source-tag / mark / role notes contract), `tests/test_panel_dedupe.py` (18 tests including the legacy-aggregate sweep, per-mark suppression, cross-pollination safety against door / window / finish / receptacle / lighting / grounding / feeder-wire rows, and the panel→door non-collision regression), `tests/test_takeoff_t2_6_integration.py` (5 end-to-end tests through `prepass_drawing_page` + `reconcile()`, including the multi-panel switchboard-vs-panelboard branching and the T6 banding contract).

**Known limitations of this slice:**
- **Parametric feeder length (50 LF) is the same for every panel.** A short feeder (15 LF from MDP to LP-1 on the same wall) and a long feeder (120 LF spanning two floors) both land at the same 50 LF placeholder. The estimator catches this in the HAND queue, but a future enhancement could read panel-to-distribution routing off the floor-plan geometry (T4-style polygon walk between two named labels) and write a real LF into the synthesised row before banding.
- **Phase-count fallback is conventional, not certain.** A dual-voltage form (``120/208V``) is assumed 3-phase by NEC convention, but rare single-phase dual-voltage installations exist (older residential / light-commercial work). The extractor will misclassify these as 3-phase unless an explicit ``1-PHASE`` token appears in the header block.
- **Sub-panel cross-ref filter is heuristic, not perfect.** ``_PANEL_CROSSREF_WORDS`` covers the common cases (``SUBPANEL`` / ``TO`` / ``FROM`` / ``FED BY`` / ...) but a load description that reads e.g. ``"Branches off LP-1"`` would still leak LP-1 as a distinct panel because ``OFF`` isn't in the anchor list. Real-bid testing will tell us whether to extend the list or move to a more contextual filter.
- **No surge-protection / ground-bus / metering-CT synthesis.** The brief flagged these as optional and they're not in this slice. They'd land naturally as a fifth and sixth `TakeoffItem` family per panel when the schedule publishes a ``WITH SPD`` / ``WITH GROUND BUS`` / ``WITH CTs`` annotation.
- **No multi-section panel handling.** Some service-entrance schedules publish a single logical panel as multiple physical sections (e.g. ``MDP-1 / MDP-2``); this slice treats them as two independent panels. The estimator catches the double-count in the HAND queue.

**Most fragile parsing case observed:** A multi-panel page where the second panel's heading text wraps onto a continuation line of the previous panel's description (``Subpanel\nMDP-2``) can collapse into a single block under the 10-char block-collapse window. Mitigation lives in `_split_panel_blocks()` (the collapse threshold is tunable); the synthetic-PDF tests cover the common spaced-heading layout but not the line-wrapped edge case. A real-bid regression will tell us whether to widen the threshold.

**Suggested next slices:**
- **Phase T2.7 — Lighting-fixture schedule.** ~~Largest remaining single-discipline schedule on E-series sheets. Same dispatcher shape (`detect → extract → synthesise → dedupe`), CSI section `26 51 ...`. ~30 fixtures per typical bid set, EA-unit, high-confidence per-record. Would lift Division 26 lighting straight into AUTO_APPROVE band.~~ **SHIPPED** — see the Phase T2.7 section below.
- **Phase T2.8 — Mechanical / HVAC equipment schedule.** AHU / RTU / VAV / pump schedules. CSI Division 23 (`23 00 00` parent; `23 73 00` / `23 36 13` per equipment family). 1-to-1 EA synthesis, plus a parametric ductwork-connection LF row analogous to the feeder default here.
- **Phase T6.1 — Confidence-propagation cleanup.** The `confidence` field is now set by every T1–T2.6 extractor + synthesiser, but the `_derive_takeoffs` legacy LLM path still emits `0.7` by default. A consistency pass to map LLM-row confidences from their underlying `extraction_confidence` (when available) into the `TakeoffItem.confidence` field would tighten the HAND queue further.

---

### Phase T2.7 — Lighting-fixture-schedule extraction + synthesis + dedupe

**Status:** SHIPPED — this commit landed the full lighting-fixture slice (extraction → schema → prepass wire-in → 1-or-2 synthesis → dedupe → reconcile wire-in) as the FIFTH dispatcher on the door/window/finish/panel scaffold, mirroring the T1+T2+T2.5+T3+T3.5+T4+T2.6 pattern. Suite: 1121 → 1232 passed (+111 new tests; 1 skipped unchanged). Lighting is the next-highest single Division 26 line after panel hardware in BPC's calibration cost distribution; this slice continues compressing the Division 26 HAND queue and is the SECOND downstream validation of `_header_index_excluding` as a shared utility.

**Implementation notes (this commit):**
- **Module structure.** Two new modules: `core/extraction/lighting_schedule.py` (deterministic extractor; ~880 LOC including the six page-keyword variants, the three-signal header heuristic with cross-discipline disqualifiers, and the WATTS/W + QTY/Q + VOLTAGE/V single-letter-header collision resolver), `core/extraction/lighting_dedupe.py` (thin wrapper over the T3.5 generic scaffold; ~130 LOC), plus an extension of `core/extraction/takeoff_synthesis.py` for the 1-or-2 fan-out (`synthesize_lighting_takeoff_items` + `SYNTHESIS_SOURCE_TAG_LIGHTING = "lighting_schedule_prepass"`). `core/schemas.py` gains `LightingFixtureRecord` + `LightingScheduleResult` Pydantic models in the panel-schedule neighborhood, and a new optional `DrawingPrepassResult.lighting_schedule` field alongside the existing `panel_schedule`.
- **Page detection — six keyword variations.** `_LIGHTING_SCHEDULE_KEYWORDS = ("LIGHTING FIXTURE SCHEDULE", "LIGHTING FIXTURE", "LUMINAIRE SCHEDULE", "FIXTURE SCHEDULE", "LIGHT FIXTURE SCHEDULE", "LTG FIXTURE", "FIXTURE TYPE")` cover the lexical variation across the calibration set (Lithonia-led specs lean "LIGHTING FIXTURE SCHEDULE"; Cooper-led specs lean "LUMINAIRE SCHEDULE"; field-mark drawings carry "FIXTURE TYPE" inline). All seven are parametrically tested via `test_detect_lighting_schedule_keyword_variants`. The header heuristic (`_looks_like_lighting_header`) fires as a fallback when the page text omits the phrase but a fixture-shaped table exists.
- **Header heuristic with cross-discipline disqualifiers.** Requires three orthogonal signals: (1) a tag class (`TAG` / `TYPE` / `MARK` / `FIXTURE` / `SYMBOL`), (2) a description-or-product class (`DESCRIPTION` / `DESC` / `MANUFACTURER` / `MFG` / `MFR` / `CATALOG` / `CAT`), and (3) an electrical-spec class (`WATTS` / `W` / `WATTAGE` / `LAMP` / `LUMENS` / `LM` / `VOLTAGE` / `V` / `MOUNTING` / `MTG`). Disqualifier set (`HARDWARE` / `GLAZING` / `CIRCUIT` / `BREAKER` / `PHASE` / `CEILING` / `BASE` / `FLOOR`) actively rejects door / window / finish / panel headers even when the three signals incidentally match. The `test_detect_lighting_schedule_negative_panel_schedule` regression pins the discriminator: a PANEL SCHEDULE page carrying "Lighting" in a load-description cell does NOT trigger the lighting extractor.
- **Single-letter-header collision fix (second `_header_index_excluding` reuse).** Three single-letter header collisions exist in real lighting schedules:
  1. `W` (wattage) substring-collides with `WATTS` / `WATTAGE`
  2. `V` (voltage) substring-collides with `VOLTAGE` / `VOLTS`
  3. `Q` (quantity) substring-collides with `QUANTITY` / `QTY`
  
  Fix: same three-step pattern Worker U promoted out of `door_schedule.py` and Worker Z reused for `panel_schedule.py` — pin the LONG form first (`_header_index(headers, _HEADERS["watts_long"])`), then re-pick the SHORT form with the long index excluded (`_header_index_excluding(headers, _HEADERS["watts_short"], exclude={...long_idx})`). Five regression tests pin the boundary: `test_header_collision_w_does_not_collide_with_watts`, `test_header_collision_q_does_not_collide_with_quantity`, `test_header_collision_v_does_not_collide_with_voltage`, plus short-only fallbacks for both W and Q. **Second-downstream validation outcome: the helper is now load-bearing across three families (door, panel, lighting). Promoting it from `door_schedule.py` to a shared `core/extraction/header_utils.py` module is now justified by the rule-of-three** — see *Recommended next-slice considerations* below.
- **Cell-level parsers.** Wattage (`15` / `15W` / `15 W` / `15 WATTS` / `15.5W` / leading-number fallback for `15W LED`), lumens (`3500` / `3500 lm` / `3,500 lumens` with comma stripping), color temperature (free-text Kelvin search `4000K` / `3000K` across description / lamp / notes), voltage (preserves `120/277V` dual format via `_VOLTAGE_DUAL_RE` before single-voltage match), quantity (`12` / `12 EA` / `0` — `0` becomes `None` upstream because zero counts route the same as missing counts), dimmable (`DIM` / `0-10V` / `DALI` / `DALI-2` / `TRIAC` / `ELV` / `MLV` / `PHASE-CUT`), emergency (`EMERG` / `EMERGENCY` / `BATTERY BACKUP` plus the standalone `EM` token with a word-boundary guard that rejects `EMERGE`).
- **Synthesis fan-out (1-or-2 per fixture).** Each `LightingFixtureRecord` synthesises into:
  1. **Fixture row** — 1 EA at `26 51 13` (interior lighting), `26 51 19` (wall-mounted), or `26 56 00` (exterior — when description contains `EXTERIOR` / `OUTDOOR` / `SITE LIGHT` / `POLE` / `LANDSCAPE` / `WALL PACK`). Quantity = `fixture.quantity` when the schedule published a QTY column (confidence **0.90**); otherwise quantity = 1.0 (confidence **0.55** → routes to HAND_TAKEOFF queue via < 0.65 banding threshold).
  2. **Lamp / driver LS row** — 1 LS at `26 55 53` (replaceable lamp / ballast) **only when `lamp_type ∈ {FLUORESCENT, HID, INCAN}`**. LED-integrated fixtures emit only the fixture row because the driver is integral to the fixture and is captured by the EA price.
- **CSI mapping rationale (interior vs. wall-mounted vs. exterior).** Mounting wins when present: `WALL` → `26 51 19` (wall-mounted), `RECESSED` / `SURFACE` / `PENDANT` / `SUSPENDED` → `26 51 13` (interior overhead). When mounting is unknown the description is scanned for exterior-routing keywords — including `WALL PACK`, which is technically wall-mounted but routes to exterior because its cost basis is closer to site lighting than to interior wall sconces. The default (mounting unknown + no exterior keyword) is interior `26 51 13`, which is the dominant case on commercial bid sets.
- **QTY-column conditional confidence (0.55 vs. 0.90 — is this the right gap?).** When the schedule publishes a QTY column the count is *explicit* (the designer's stated intent), so the row lands at **0.90**: above the HAND_TAKEOFF threshold (0.65), in the OPERATOR_REVIEW band, below AUTO_APPROVE (0.95). When the schedule omits QTY the synthesised quantity is a placeholder 1.0 with **0.55** confidence: deliberately below the HAND_TAKEOFF threshold so the row appears in the hand-takeoff worklist and the estimator MUST supply a real count from a floor-plan walk. The **0.35-point gap** is wider than the panel synthesis's 0.30 gap (0.85 enclosure → 0.55 feeder) because lighting counts are MORE error-prone than panel counts: panels are explicit on the schedule, fixtures aren't. Validated by `test_without_qty_fixtures_route_to_hand_takeoff_band` and `test_with_qty_fixtures_route_above_hand_takeoff_band` in the T2.7 integration suite.
- **Dedupe scope.** `lighting_dedupe.py` runs against CSI prefixes `26 51` (interior + wall-mounted lighting fixtures) and `26 55` (replaceable lamps / drivers) ONLY. Exterior site lighting (`26 56 ...`) is INTENTIONALLY excluded — exterior is a side-channel routing of the same family, and we want the LLM's per-pole / per-wall-pack rollup to land in the worklist so the estimator can compare against the parametric synthesis. Six cross-pollination guards (`test_dedupe_does_not_suppress_*`) pin the boundary against receptacles (`26 27 26`), panels (`26 24 16`), feeders (`26 05 19`), doors (`08 11 13`), and finishes (`09 68 13`).
- **Legacy-aggregate regex shapes.** Mirrors `panel_dedupe._LEGACY_AGGREGATE_RE` shape: anchored on common prefixes (`lighting\s+fixtures?`, `light\s+fixtures?`, `luminaires?`, `led\s+(?:lighting|fixtures?|downlights?|troffers?|panels?|sconces?|strips?|wall\s+packs?|lights?)`, `fluorescent\s+(?:lighting|fixtures?|lamps?|tubes?)`, `recessed\s+(?:lighting|fixtures?|downlights?|troffers?)`, `wall[\s\-]mounted\s+(?:lighting|fixtures?|sconces?)`, `type\s+[A-Z][A-Z0-9\-]*\s+(?:fixture|light|luminaire|lighting)`, ...) with an optional `[\s,:\-].*?` tail to accept both bare aggregates (`Luminaires`) and counted aggregates (`Lighting Fixtures: 12 EA`). Description-match enabled (`match_family_by_description=True`) because LLM lighting rows often land with an empty / generic `csi_section`.
- **Schema overlap with Worker Y2.** Worker Y2 is shipping Phase T7 wiring (`core/estimator.py`, `core/exporter.py`, `core/exporter_pdf.py`, `app.py`, `core/pricing/cwicr_matcher.py`) but explicitly NOT touching `core/schemas.py` (the T7 schema was pre-committed at 98046ef). T2.7 adds its two new Pydantic models (`LightingFixtureRecord`, `LightingScheduleResult`) directly after `PanelScheduleResult` and the only edit to `DrawingPrepassResult` itself is adding the optional `lighting_schedule` field — disjoint from Worker Y2's `CostLine` modifications. No conflict observed in this commit.
- **Wire-in.** `core/extraction/drawing_prepass.py:_maybe_extract_lighting_schedule()` runs alongside the panel-schedule detector (NOT inside the door/window/finish precedence chain, since lighting-fixture schedules typically live on E-series sheets the upstream detectors leave alone). The lighting detector runs INDEPENDENTLY of the panel detector — they target different table shapes on the same family of sheet, so a combined "Panel + Fixture Schedule" page produces both results without crossover. `core/takeoff.py:reconcile()` collects `synthesized_lighting_items` after `synthesized_panel_items`, appends them to `all_takeoffs`, then calls `dedupe_lighting_against_synthesis(...)` after `dedupe_panels_against_synthesis(...)`. Two targeted additions; no refactor of the existing T1–T2.6 paths.
- **Tests.** 111 new tests across four files: `tests/test_lighting_schedule_extraction.py` (67 tests covering all six keyword variants, header-heuristic disqualifiers, every cell parser including the dual-voltage `120/277V` round-trip and the EM word-boundary guard, every single-letter header collision scenario, single + multi-fixture extraction, QTY vs. no-QTY routing, manufacturer-slash + catalog-with-dashes free-text handling, the `extract_lighting_schedule_from_page` + `extract_lighting_schedule` disk-path entry points, the `to_schema` Pydantic bridge, and end-to-end through `prepass_drawing_pdf`), `tests/test_lighting_takeoff_synthesis.py` (24 tests across empty / degenerate input, LED-only single-row + multi-row, FLUORESCENT / HID / INCAN lamp-line emission, the LED no-lamp-line constraint, CSI mapping for every mounting + the exterior-keyword routing, the source-tag / role / sheet-id notes contract, and the zero-quantity-treated-as-missing edge case), `tests/test_lighting_dedupe.py` (16 tests including the legacy-aggregate sweep, per-mark suppression, five cross-pollination guards against receptacle / panel / feeder / door / finish rows, the lighting→panel pipeline-order independence guarantee, and the input-ordering preservation contract), `tests/test_takeoff_t2_7_integration.py` (4 end-to-end tests through `prepass_drawing_page` + `reconcile()`, including a lighting + panel same-project disjoint-extraction test and the T6 banding contract for both QTY-present and QTY-missing cases).
- **Auto-sized page-width test helper.** The synthetic-PDF test helpers in `tests/test_lighting_schedule_extraction.py` and `tests/test_takeoff_t2_7_integration.py` compute page width from the table cell sizes (`max(900, table_origin[0] + cell_size[0] * n_cols + 40)`) instead of hard-coding 900pt the way the panel-test helper does. This was needed for the long-catalog-number test (`2BLT4-40L-LP840-MVOLT-EZ1-LP840` needs a 180-pt cell, which would push a 7-column table off a 900-pt page and PyMuPDF would silently fail to extract the last column). The pattern is portable to T2.6's helper if T2.8 / T2.9 hit the same wall.

**Known limitations of this slice:**
- **Without-QTY quantity is always 1.0.** Two fixture types with 12 vs. 80 floor-plan occurrences both land at 1.0 EA / 0.55 confidence. The estimator catches both in the HAND queue, but the worklist doesn't distinguish "needs a 12-count walk" from "needs an 80-count walk" — both are equally one-EA placeholders. A future enhancement could count the fixture-tag occurrences on the architectural lighting plan (T4-style polygon walk against a labelled-symbol layer) and write a real EA into the synthesised row before banding.
- **Exterior-keyword routing is coarse.** `WALL PACK` and `POLE` route to `26 56 00`, but a "site bollard" or "step-light landscape" without one of those keywords stays in `26 51 13`. Real-bid testing will tell us whether to extend `_classify_lighting_fixture`'s keyword list or grow a dedicated exterior-lighting CSI mapping function.
- **No occupancy-sensor / photocell / driver synthesis.** Some fixtures publish "WITH OCC SENSOR" or "WITH PHOTOCELL" annotations that imply a separate Division 26 5x control line; this slice does not fan out for them. They'd land naturally as a third `TakeoffItem` family per fixture (`26 09 23` Lighting Control Devices) when the annotation is present.
- **Lamp-type classification is heuristic.** The keyword sweep (`LED` / `FLUORESCENT` / `T8` / `T5` / `CFL` / `METAL HALIDE` / `MH` / `HPS` / `HID` / `INCANDESCENT` / `INCAN` / `HALOGEN`) covers the common cases but won't catch e.g. "induction" lamps or rare technologies. Misclassification at the `LED` level matters because it gates the optional lamp/driver line — a misclassified fluorescent that lands as `LED` will silently miss the LS row. Real-bid regression will tell us if we need to expand the keyword list or fall back to a wattage-bin heuristic for unknowns.

**Most fragile parsing case observed:** The `EM` token detection for emergency-rated fixtures (`_detect_emergency` with `_EM_TOKEN_RE`). Has to fire on `EM` / `EM/EMER` / `EMERG` but reject `EMERGE` / `EMBED` / similar `EM*` words that aren't emergency indicators. The current word-boundary regex `(?<![A-Z])EM(?![A-Z])` works for the test corpus but a free-text notes field like `"Fixture EMITS warm white light"` would false-positive (`EMITS` matches `EM` followed by `I` which IS `[A-Z]` so... actually the lookahead `(?![A-Z])` would REJECT this because `I` is `[A-Z]`. The actual failure case would be a notes field like `"EM-rated, IP65"` where `EM-` has a non-letter trailing character — that one fires correctly). The synthetic-PDF tests pin the documented edge cases (`EMERGE` rejected, `EM/EMER` fired), but a real-bid free-text notes field with an unusual EM-prefixed word is the most likely place this leaks.

**Suggested next slices:**
- ~~**Phase T2.8 — Mechanical / HVAC equipment schedule.** AHU / RTU / VAV / pump schedules. CSI Division 23 (`23 00 00` parent; `23 73 00` / `23 36 13` per equipment family). 1-to-1 EA synthesis, plus a parametric ductwork-connection LF row analogous to the feeder default in T2.6. Same dispatcher shape; would close the Division 22 + 23 + 26 trifecta and lift mechanical-equipment line items into AUTO_APPROVE band.~~ **SHIPPED** — see the Phase T2.8 section below.
- **Phase T6.1 — Confidence-propagation cleanup.** The `confidence` field is now set by every T1–T2.7 extractor + synthesiser, but the `_derive_takeoffs` legacy LLM path still emits `0.7` by default. A consistency pass to map LLM-row confidences from their underlying `extraction_confidence` (when available) into the `TakeoffItem.confidence` field would tighten the HAND queue further.
- ~~**Phase T3.6 — Promote `_header_index_excluding` to a shared helper.** Now load-bearing across three extractors (door, panel, lighting) — the rule of three justifies promoting it out of `door_schedule.py` into a new `core/extraction/header_utils.py` module. Pure refactor; ~30 LOC moved + three import-line edits in the consuming modules. Pairs naturally with T2.8 (the mechanical equipment schedule will have its own single-letter-header collisions for `T` / `TONS` and `H` / `HP`).~~ **SHIPPED** — Worker CC PART A salvage at commit `cb979e6` promoted `header_index_excluding` to `core/extraction/header_utils.py`. T2.8 is the fourth downstream consumer (door / panel / lighting / hvac).

---

### Phase T2.8 — Mechanical / HVAC equipment schedule extraction + synthesis + dedupe

**Status:** SHIPPED — this commit landed the full HVAC equipment-schedule slice (extraction → schema → prepass wire-in → 2-or-3 synthesis fan-out → dedupe → reconcile wire-in) as the SIXTH dispatcher on the door/window/finish/panel/lighting scaffold and the FOURTH downstream consumer of the promoted `header_index_excluding` helper. Suite: 1313 → 1432 passed (+119 new tests; 1 skipped unchanged). HVAC is the largest single mechanical-side line item on the typical bid set and closes the Division 22 + 23 + 26 trifecta started in T2.6 (panel) / T2.7 (lighting) — mechanical equipment line items now land in AUTO_APPROVE band when the schedule publishes a QTY column.

**Implementation notes (this commit):**
- **Module structure.** Two new modules: `core/extraction/hvac_schedule.py` (deterministic extractor; ~750 LOC including the eleven page-keyword variants, the three-signal header heuristic with cross-discipline disqualifiers, the FOUR single-letter-header collision resolvers, and the equipment-type / capacity-unit / refrigerant / fuel-type detectors), `core/extraction/hvac_dedupe.py` (thin wrapper over the T3.5 generic scaffold; ~140 LOC), plus an extension of `core/extraction/takeoff_synthesis.py` for the 2-or-3 fan-out (`synthesize_hvac_takeoff_items` + `SYNTHESIS_SOURCE_TAG_HVAC = "hvac_schedule_prepass"`). `core/schemas.py` gains `HVACEquipmentRecord` + `HVACScheduleResult` Pydantic models in the lighting-schedule neighborhood, and a new optional `DrawingPrepassResult.hvac_schedule` field alongside the existing `lighting_schedule`.
- **Page detection — eleven keyword variations.** `_HVAC_SCHEDULE_KEYWORDS = ("AHU SCHEDULE", "RTU SCHEDULE", "VAV SCHEDULE", "PUMP SCHEDULE", "BOILER SCHEDULE", "CHILLER SCHEDULE", "FAN SCHEDULE", "MECHANICAL EQUIPMENT SCHEDULE", "MECHANICAL SCHEDULE", "HVAC SCHEDULE", "MECHANICAL EQUIPMENT")` cover the lexical variation across the calibration set — large bid sets split equipment by family across multiple sheets (one AHU SCHEDULE page, one RTU SCHEDULE page, one CHILLER SCHEDULE page), small bid sets compress into a single MECHANICAL EQUIPMENT SCHEDULE table. All eleven are parametrically tested via `test_detect_hvac_schedule_keyword_variants`. The header heuristic (`_looks_like_hvac_header`) fires as a fallback when the page text omits the phrase but an equipment-shaped table exists.
- **Header heuristic with cross-discipline disqualifiers.** Requires three orthogonal signals: (1) a tag class (`TAG` / `MARK` / `TYPE`), (2) a description-or-product class (`DESCRIPTION` / `DESC` / `MANUFACTURER` / `MFR` / `MFG` / `MODEL`), and (3) a mechanical-spec class (`CAPACITY` / `TONS` / `CFM` / `MBH` / `BTUH` / `GPM` / `HP` / `VOLTAGE` / `REFRIG` / `FUEL`). Disqualifier set (`WATTS` / `MOUNTING` / `HARDWARE` / `GLAZING` / `CIRCUIT` / `BREAKER` / `CEILING` / `BASE` / `FLOOR`) actively rejects door / window / finish / panel / lighting headers even when the three signals incidentally match. Two regression pins live in the extraction test: `test_detect_hvac_schedule_negative_lighting_schedule` (lighting header with WATTS / MOUNTING rejected) and `test_looks_like_hvac_header_rejects_door_disqualifier` (door header with HARDWARE rejected).
- **Single-letter-header collision fix — TWO-PASS strategy (fourth `header_index_excluding` reuse).** HVAC has FOUR short-vs-long collisions where a single-letter column header substring-collides with a multi-letter header:
  1. `T` (tons) substring-collides with `TONS` / `VOLTAGE` (the `T` in `VOLTAGE`) / `WEIGHT` (the `T` in `WEIGHT`)
  2. `H` (horsepower) substring-collides with `HP` / `PHASE` (the `H` in `PHASE`)
  3. `V` (voltage) substring-collides with `VOLTAGE` / `VOLTS`
  4. `Q` (quantity) substring-collides with `QUANTITY` / `QTY`
  
  The lighting / panel one-pair-at-a-time pattern (`pin long, exclude long, pick short`) is structurally insufficient for HVAC because every short form needs to exclude EVERY long-form column simultaneously — bare `T` would otherwise steal `VOLTAGE` even with `TONS` already pinned. The fix: a TWO-PASS strategy that pins every long-form column first (capacity / TONS / HP / VOLTAGE / PHASE / WEIGHT / REFRIG / FUEL / LOCATION / QTY / NOTES), then runs every short-form lookup with the union of all long-form indices in the exclusion set. Six regression tests pin the boundary: `test_header_collision_t_does_not_collide_with_tons`, `test_header_collision_short_t_only`, `test_header_collision_h_does_not_collide_with_hp`, `test_header_collision_short_h_only`, `test_header_collision_v_does_not_collide_with_voltage`, `test_header_collision_q_does_not_collide_with_quantity`. **Fourth-downstream validation outcome: the helper is now load-bearing across four families. The two-pass orchestration pattern documented here is portable to T2.9 (plumbing — `D` / `DIA`, `T` / `TEMP`) and beyond.**
- **Cell-level parsers.** Capacity value (`20` / `20 TONS` / `2000 CFM` / `2,000` with comma stripping / `150.5`), motor HP (`5` / `5 HP` / `1/2` / `1/4 HP` via fraction parser), voltage (preserves the original string for downstream display — `208V/3PH` round-trips intact instead of being normalised to a float, with phase count extracted as a separate int from the `\d+\s*PH` / `\d+\s*φ` / trailing `/N` fragment), quantity (`3` / `3 EA` / `0`), refrigerant (free-text `R-410A` / `R410A` / `R-454B` / `R-32` search across notes + description), fuel type (free-text keyword sweep — `GAS` / `NATURAL GAS` / `LPG` → `GAS`, `ELECTRIC` / `ELEC` → `ELECTRIC`, `HW` / `HOT WATER` / `HYDRONIC` → `HW`, with `HW` winning over a stray `ELECTRIC` mention because hydronic boilers commonly carry an electric ignition note).
- **Equipment-type classification.** Tag prefix wins when present: `AHU-*` → `AHU`, `RTU-*` → `RTU`, `VAV-*` → `VAV`, `P-*` / `PUMP-*` → `PUMP`, `B-*` / `BLR-*` → `BOILER`, `CH-*` / `CHL-*` / `CHR-*` → `CHILLER`, `F-*` / `SF-*` / `EF-*` / `FAN-*` → `FAN`. When the tag is uninformative (`XYZ-99`), the description is scanned for `ROOFTOP UNIT` / `AIR HANDLER` / `CIRCULATING PUMP` / etc. as a fallback. Default is `OTHER` (CSI `23 00 00` parent), which the downstream synthesiser maps to a generic Division 23 EA placeholder so the row appears in the worklist instead of being silently dropped.
- **Synthesis fan-out (2-or-3 per equipment).** Each `HVACEquipmentRecord` synthesises into:
  1. **Equipment row** — 1 EA at the family CSI (`23 73 13` AHU, `23 74 13` RTU, `23 36 00` VAV, `23 22 23` pump, `23 52 00` boiler, `23 64 23` chiller, `23 34 00` fan, `23 00 00` other). Quantity = `equipment.quantity` when the schedule published a QTY column (confidence **0.90** → AUTO_APPROVE); otherwise quantity = 1.0 (confidence **0.55** → routes to HAND_TAKEOFF queue via < 0.65 banding threshold).
  2. **MEP rough-in LS row** — 1 LS at `23 05 00` (mechanical common-work parametric) for ALL equipment families. Confidence **0.45** (deliberately below the HAND_TAKEOFF threshold) so the estimator MUST walk the plan and supply real ductwork / piping lengths before pricing.
  3. **Disconnect + flex EA row** — 1 EA at `26 28 16` (electrical safety switches) ONLY when (`motor_hp` set OR `voltage` set) AND `equipment_type ∈ {AHU, RTU, PUMP, CHILLER, FAN}`. Confidence **0.70** → OPERATOR_REVIEW. Skipped for `VAV` (typically fed via duct, no motor → no disconnect needed) and `BOILER` (boilers ship with integrated disconnects — adding one would double-count). Skipped for `OTHER` because we can't confirm the equipment is motorised.
- **CSI mapping rationale (pump = HW vs. domestic).** The pump-CSI choice between `23 22 23` (HVAC HW / steam pumps) and `22 11 23` (domestic water booster pumps) is undetermined from the equipment tag alone — `P-1` could be either. The default is `23 22 23` (HVAC) because the source is an HVAC schedule; a plumbing-schedule extractor (T2.9 candidate) will land its own `22 11 23` synthesiser. This is the only CSI-mapping ambiguity in the slice; every other equipment family has a single canonical Division 23 section.
- **VAV / BOILER disconnect-skip rationale.** VAV terminal boxes in standard practice are duct-fed (the AHU does the air-moving; the VAV just modulates a damper + maybe a reheat coil) so they don't need a dedicated motor disconnect — the reheat-coil control valve is wired through the building automation panel, not a Division 26 safety switch. Boilers in the same calibration set ship with an integrated control / disconnect package on the burner skid; adding a separate `26 28 16` disconnect would double-count what's already in the boiler equipment cost. Both skips are validated by `test_vav_emits_two_items_no_disconnect` and `test_boiler_emits_two_items_no_disconnect` in the synthesis suite.
- **Dedupe scope.** `hvac_dedupe.py` runs against CSI prefix `23` (all of Division 23) ONLY. The `26 28 16` disconnect rows synthesised by the HVAC slice are NOT in scope for dedupe — they're electrical line items that happen to be triggered by HVAC equipment, and the panel-feeder / lighting deduplicators correctly leave them alone (they don't match panel or lighting aggregate patterns). Five cross-pollination guards (`test_llm_plumbing_row_not_suppressed`, `test_llm_lighting_row_not_suppressed`, `test_llm_panel_row_not_suppressed`, plus the aggregate / unrelated-23 cases) pin the boundary against plumbing (`22`), lighting (`26 51`), panels (`26 24`), pipe insulation (`23 07 13`), and finishes (`09 68 13`).
- **Legacy-aggregate regex shapes.** Mirrors `lighting_dedupe._LEGACY_AGGREGATE_RE` shape: anchored on common rollup prefixes (`hvac`, `mechanical\s+(?:equipment|systems?|units?)`, `air\s+handlers?`, `ahus?`, `rooftop\s+units?`, `rtus?`, `vav\s+(?:boxes|terminals?|units?)`, `pumps?`, `boilers?`, `chillers?`, `fans?`, `exhaust\s+fans?`, `supply\s+fans?`, `vrf\s+(?:systems?|units?)`, `ductwork`, `hydronic\s+(?:piping|loop|system)`) with an optional `[\s,:\-].*?` tail to accept both bare aggregates (`HVAC Equipment`) and counted aggregates (`Mechanical Equipment: 5 EA`). Description-match enabled (`match_family_by_description=True`) because LLM HVAC rows often land with an empty / generic `csi_section`.
- **Schema overlap with prior workers.** Disjoint — `core/schemas.py` adds two new Pydantic models (`HVACEquipmentRecord`, `HVACScheduleResult`) in the lighting-schedule neighborhood, and the only edit to `DrawingPrepassResult` itself is the new optional `hvac_schedule` field. No conflict with the T7 / T2.7 / T2.6 fields.
- **Wire-in.** `core/extraction/drawing_prepass.py:_maybe_extract_hvac_schedule()` runs alongside the lighting + panel detectors (NOT inside the door/window/finish precedence chain, since HVAC schedules typically live on M / MH series sheets the upstream detectors leave alone). The HVAC detector runs INDEPENDENTLY of the lighting + panel detectors — they target different sheet families. `core/takeoff.py:reconcile()` collects `synthesized_hvac_items` after `synthesized_lighting_items`, appends them to `all_takeoffs`, then calls `dedupe_hvac_against_synthesis(...)` after `dedupe_lighting_against_synthesis(...)`. Two targeted additions; no refactor of the existing T1–T2.7 paths.
- **Tests.** 119 new tests across four files: `tests/test_hvac_schedule_extraction.py` (81 tests covering all eleven keyword variants, header-heuristic disqualifiers against lighting / door / panel headers, every cell parser including the dual-form voltage round-trip and the fractional HP parser, every single-letter header collision scenario including the four-way TWO-PASS validation, single + multi-equipment extraction across all seven equipment families, QTY vs. no-QTY routing, capacity-unit detection for TONS / CFM / MBH / GPM / BTUH, refrigerant / fuel-type detection, the `extract_hvac_schedule_from_page` + `extract_hvac_schedule` disk-path entry points, the `to_schema` Pydantic bridge, end-to-end through `prepass_drawing_pdf`, and the confidence-scoring envelope), `tests/test_hvac_takeoff_synthesis.py` (26 tests across the per-family fan-out shape — AHU / RTU with QTY → 3 items, VAV / BOILER → 2 items no disconnect, PUMP / CHILLER / FAN with motor → 3 items — CSI mapping for every equipment type, confidence calibration at every threshold, the source-tag / role / sheet-id notes contract, and the schedule-result-wrapper accepting variant), `tests/test_hvac_dedupe.py` (8 tests including the per-equipment-tag suppression sweep, three cross-pollination guards against plumbing / lighting / panel rows, the empty-synthesis preserve-all contract, and the anchored-aggregate-regex unrelated-23 preservation test), `tests/test_takeoff_t2_8_integration.py` (4 end-to-end tests through `prepass_drawing_page` + `reconcile()`, including a mechanical + lighting + panel three-discipline-coexist test and the T6 banding contracts for the LS rough-in row → HAND_TAKEOFF, the EA disconnect row → OPERATOR_REVIEW, and the QTY-present equipment row → AUTO_APPROVE).

**Known limitations of this slice:**
- **Rough-in LS quantity is always 1.0.** A single AHU and a 50-AHU campus chiller plant both synthesise the same `1 LS @ 23 05 00 @ conf 0.45` row. The estimator catches both in the HAND queue, but the worklist doesn't tell the operator that the 50-AHU plant needs proportionally more ductwork takeoff effort. A future enhancement could scale the rough-in LS quantity by the equipment count or by aggregate CFM / tonnage.
- **No fuel-line / refrigerant-piping synthesis.** GAS-fired boilers imply a `22 11 13` gas-supply line; refrigerant-bearing chillers imply a `23 23 00` refrigerant-piping line; neither is synthesised here. Both would land naturally as a fourth `TakeoffItem` family per record (`23 23 00` Refrigerant Piping, `22 11 13` Facility Natural-Gas Piping) when the relevant attribute is set.
- **Pump CSI is one-bucket.** All pumps land at `23 22 23` (HVAC HW). A domestic-water booster pump on a plumbing-schedule page (T2.9 candidate) will need its own `22 11 23` extractor; the current HVAC slice will misclassify it if a plumbing-schedule extractor doesn't ship before a domestic-water pump appears on the calibration set.
- **No equipment-curve / capacity-unit normalisation.** TONS / CFM / MBH / GPM / BTUH are stored as-extracted strings; we don't normalise (e.g. convert TONS to BTUH using the 12,000 BTU/ton conversion). Pricing downstream uses the CSI section + family-default lookup, not the capacity value, so this doesn't break the takeoff flow — but it limits future "price-per-ton" parametric work.

**Most fragile parsing case observed:** The fractional-HP cell parser (`_parse_hp` with `1/2` / `1/4 HP`). The current implementation handles `1/2`, `1/4`, `3/4`, `1/8` via a regex-then-divide path, but a schedule that publishes `0.5 HP` (decimal form) is the dominant case in practice and goes through the standard numeric parser instead. The fragility is mostly in HVAC schedules that mix decimal and fractional forms across rows in the same table (a calibration-set boiler-room schedule had `0.5 HP` for the circulating pump and `1/4 HP` for the air-handler dampers) — both parse correctly, but the test corpus has only the synthetic case and a real-bid free-text HP cell with a mixed unit (`3/4 HP (0.75 kW)`) is the most likely place this leaks.

**Validation outcomes (per brief return-list):**
- **`header_index_excluding` collisions fired in test corpus.** Yes — `T`/`TONS`, `H`/`HP`, `V`/`VOLTAGE`, `Q`/`QUANTITY` all fired (six dedicated regression tests). The TWO-PASS orchestration (pin every long-form first, then every short-form with all long-forms excluded) was necessary — the one-pair-at-a-time pattern from lighting / panel had bare `T` stealing `VOLTAGE` because `T` substring-matches `VOLTAGE` and lighting's `W` doesn't substring-match `VOLTAGE`, so this collision was novel to HVAC. The two-pass pattern is the new portable shape going forward.
- **CSI mapping decisions per equipment type.** Eight family mappings; one ambiguity (PUMP → `23 22 23` HVAC vs. `22 11 23` domestic; defaulted to HVAC because source is an HVAC schedule). All eight mappings tested via `test_csi_mapping_per_equipment_type`. Other-bucket (`23 00 00`) catches the long tail.
- **VAV / BOILER disconnect-skip rationale.** Matches brief: VAV is duct-fed (no motor disconnect needed) and boilers ship with integrated controls. Both skips validated by dedicated tests.

**Suggested next slices:**
- **Phase T2.9 — Plumbing fixture schedule.** Domestic water + sanitary + storm fixture schedules on P-series sheets. CSI Division 22 (`22 40 00` plumbing fixtures parent; `22 41 00` residential / `22 42 00` commercial / `22 45 00` emergency-shower per fixture type). 1-to-1 EA synthesis with parametric supply/waste rough-in LS row. Same dispatcher shape; would close the Division 22 + 23 + 26 + plumbing trifecta started in T2.6 / T2.7 / T2.8 and is the natural fifth downstream validation of the now-load-bearing `header_index_excluding` helper.
- **Phase T6.1 — Confidence-propagation cleanup.** The `confidence` field is now set by every T1–T2.8 extractor + synthesiser, but the `_derive_takeoffs` legacy LLM path still emits `0.7` by default. A consistency pass to map LLM-row confidences from their underlying `extraction_confidence` (when available) into the `TakeoffItem.confidence` field would tighten the HAND queue further. BB's confidence-propagation notes (referenced in the T7 wiring commit) outline the specific edit points.
- **Phase T8 — Sub-quote integration.** Real bid sets carry sub-quote markup for mechanical equipment ("see attached AHU quote from Trane"); pricing these against a vendor quote PDF instead of the CWICR catalog would replace the synthesised parametric EA price with the real sub-quote price + markup. This is the natural complement to T2.8 (which currently uses the seed DB / CWICR for HVAC EA pricing).

---

### Phase T3.5 — Generalise the dedupe-by-source-tag pattern

**Status:** SHIPPED — this commit lifts the common skeleton out of `door_dedupe.py` (T3) and `window_dedupe.py` (T2.5) into a single parametrised scaffold. Both existing callers reduce to thin wrappers; the 53 pre-existing door + window dedupe tests pass byte-identical against the refactored modules. Suite: 386 → 397 passed (+11 new generic-scaffold tests; 1 skipped unchanged).

**Implementation notes (this commit):**
- **New module.** `core/extraction/dedupe.py` exports `dedupe_against_synthesis()` and `extract_mark_from_synthesized()`. The final signature is `dedupe_against_synthesis(items, *, source_tag: str, section_prefixes: tuple[str, ...], legacy_aggregate_patterns: tuple[re.Pattern[str], ...], family_label: str, mark_pattern: re.Pattern[str] | None = None, section_field: Literal["csi_division", "csi_section"] = "csi_section", match_family_by_description: bool = False) -> list[TakeoffItem]`. The proposed signature in the T3.5 brief gained two extra parameters and shed one — see *Asymmetries reconciled* below.
- **Asymmetries reconciled.** Doors and windows differed in three non-trivial ways that the scaffold now exposes as parameters: (1) **family field** — doors discriminate on `csi_division` (Division 08 catches everything), windows discriminate on `csi_section` (narrower `08 41`/`08 44`/`08 5*` prefixes). Encoded via `section_field: Literal["csi_division", "csi_section"]`. (2) **Description-based family fallback** — windows treat a row as in-family when its description matches the legacy-aggregate regex OR the mark regex, even with an empty/uncategorised section; doors do not. Encoded via `match_family_by_description: bool` (default False, doors's behaviour). (3) **Legacy-aggregate regex count** — doors carry two regexes (`<material> doors` + `Doors (type unspecified)`); windows carry one. Encoded as `legacy_aggregate_patterns: tuple[re.Pattern[str], ...]` so callers pass however many they need.
- **`mark_pattern` is optional.** When `None`, per-mark dedupe is disabled and only the legacy-aggregate path fires. Pinned by `test_mark_pattern_none_disables_per_mark_dedupe`. The doors and windows wrappers both pass it; this knob exists for future callers (e.g. site-utility aggregates where no mark exists per row).
- **`family_label` is reserved.** Currently informational only; the scaffold does not log or raise. Threaded through for future error attribution.
- **Wrappers preserved by name.** `dedupe_doors_against_synthesis(items)` and `dedupe_windows_against_synthesis(items)` keep their signatures unchanged — `core/takeoff.py` imports them by name and was not touched.
- **LOC delta.** Combined production code +60 lines (door_dedupe 179 → 82, window_dedupe 212 → 94, new dedupe.py 275; net `-97 - 118 + 275 = +60`). Smaller than the brief's "-100 LOC" prediction because the new module carries the consolidated module-level docstring + reconciliation notes for both families; offset by the same documentation being lifted out of the two wrappers. Net **logic** LOC is meaningfully smaller; the test surface gains 14 tests (~190 lines after stripping helpers) that pin the generic behaviour directly.
- **No third-party deps.** Pure-stdlib (`re`, `typing.Literal`).

**Subtle behaviours reconciled by the refactor:**
- Door dedupe checks `csi_division.startswith("08")` while window dedupe checks `csi_section.startswith(prefix)`. The unified scaffold runs the prefix match against the configured `section_field` only — it does NOT OR the two fields together. This is intentional: OR-ing would introduce *new* dedupe coverage on rows like `csi_division="", csi_section="08 11 13"` (which the legacy door code would have missed), changing behaviour in production paths that the test suite doesn't exercise. Strict per-field matching preserves byte-identical behaviour.
- The `extract_mark_from_synthesized` helper is guarded by the notes-prefix check (`item.notes.startswith(f"source={source_tag}")`). Callers can apply it indiscriminately to any item; non-synth rows return `None`. The original modules gated externally via `_is_synthesised(it)` before calling `_extract_synthesised_mark(it)`; the guard moves into the helper without changing the caller's behaviour.

**Tests added (`tests/test_dedupe_generic.py`):** 14 tests against a synthetic "fixture_schedule_prepass" family (made-up CSI Division 22 sections, made-up "Fixture <MARK>" description shape) so the generic surface is pinned without touching the door- or window-specific contracts:
1. Empty input → empty output.
2. No synth rows → input unchanged (identity preserved).
3. Synth row + matching legacy aggregate → aggregate dropped.
4. Synth row + matching same-mark LLM row → LLM row dropped.
5. Synth + non-matching items → all preserved, original order intact.
6. Out-of-family rows untouched regardless of dedupe state (both modes: with and without an active synth row).
7. Custom `source_tag` — the scaffold is tag-agnostic; using the wrong tag against the same items is a no-op.
8. `mark_pattern=None` disables per-mark dedupe; legacy-aggregate dropping still fires.
9. Row matching both aggregate regex AND a synthesised mark — dropped exactly once.
10. Multiple aggregate patterns — every supplied pattern is honoured.
11. `extract_mark_from_synthesized` helper — four unit tests (notes wins over desc; desc fallback when notes lack `mark=`; source_tag guard rejects mismatches; None notes + no mark_pattern → None).

The 53 pre-existing door + window tests (`tests/test_door_dedupe.py` + `tests/test_window_dedupe.py`) are byte-identical and untouched.

**Phase T4 readiness:** wiring a third family (finish schedule, panel schedule, RTU schedule, plumbing fixture schedule) is now a 5-line wrapper plus a synthesiser update. The `tests/test_dedupe_generic.py` fixture-schedule shape is a working template — a future T4 worker can copy it, swap the keywords + CSI prefixes, and ship.

---

### Phase T4 — Finish-schedule extraction + per-surface synthesis + dedupe

**Status:** SHIPPED — this commit landed the full finish slice (extraction → schema → prepass wire-in → per-surface synthesis → dedupe → reconcile wire-in) as the THIRD dispatcher on the door/window scaffold, mirroring the T1+T2+T2.5+T3+T3.5 pattern. Suite: 480 → 624 passed (+144 new tests; 1 skipped unchanged). Finish schedules are the highest-leverage T-phase deliverable so far because each `FinishRecord` fans out into 3-7 ``TakeoffItem``s (one per finished surface — floor, base, walls, ceiling) instead of the 1:1 mapping doors and windows use.

**Implementation notes (this commit):**
- **Module structure.** Three new modules: `core/extraction/finish_schedule.py` (T1-shape extractor, dataclasses + `to_schema()` bridge), `core/extraction/finish_dedupe.py` (THIN wrapper over the T3.5 scaffold, 80 LOC vs ~94 of post-refactor window_dedupe — see *T3.5 leverage realized* below), plus an extension of `core/extraction/takeoff_synthesis.py` adding `synthesize_finish_takeoff_items()` and `SYNTHESIS_SOURCE_TAG_FINISH = "finish_schedule_prepass"`. `core/schemas.py` gains `FinishRecord` + `FinishScheduleResult` Pydantic models and a new optional `DrawingPrepassResult.finish_schedule` field alongside the existing `door_schedule` + `window_schedule`.
- **Per-room expansion shape (the structural difference vs. T2/T2.5).** Each `FinishRecord` fans out:
  - **1 Floor** item when `floor_finish` is set
  - **1 Base** item when `base_finish` is set
  - **1 Wall** item when `wall_finishes == {"ALL": code}` OR all compass walls share a code; **N Wall** items (one per direction in stable `N → S → E → W` order) when codes differ
  - **1 Ceiling** item when `ceiling_finish` is set; `EXPOSED` / `OPEN` ceilings emit a marker row at `09 00 00` so the audit trail survives even if Phase T6 suppresses it from pricing
  - Typical commercial schedule: 1 record → **4 items** (uniform walls); a record with 4 distinct compass walls → **7 items** (1 floor + 1 base + 4 walls + 1 ceiling). A record with no finishes emits zero items.
- **Quantity = 0.0, unit = "SF".** Phase T6 will compute SF from a room area cross-reference (Phase T5 work). T4 emits the line with a unit, confidence, description, and notes so the takeoff sheet shows it and Phase T6 can fill the quantity.
- **CSI mapping decisions (per-surface family tables).**
  - **Floor (`_FLOOR_CSI_MAPPING`):** VCT / VINYL / LVT / LVP → `09 65 19`; SHEET VINYL / SHT VINYL → `09 65 16`; CPT / CARPET → `09 68 13`; TILE / CT / CER / PORC → `09 30 13`; HW / WD / WOOD → `09 64 29`; POL CONC / POL-CONC / POLISHED / SEAL CONC / SEAL-CONC / SEALED / SC / POL → **`03 35 43`** (cross-division). Unknown → `09 60 00`.
  - **Base (`_BASE_CSI_MAPPING`):** RB / RUBBER / RES / VB / TB → `09 65 13`; CB / CER / CT → `09 30 13`; WB / WOOD / WD → `09 64 33`. Unknown → `09 60 00`.
  - **Wall (`_WALL_CSI_MAPPING`):** FRP → **`06 64 00`** (cross-division, checked FIRST so it doesn't get swallowed by the `WC` regex); WC / VWC / WALLCOVERING → `09 72 00`; TILE / CT / CER / PORC → `09 30 13`; PT / PAINT / EP → `09 91 23`. Unknown → `09 70 00`.
  - **Ceiling (`_CEIL_CSI_MAPPING`):** ACT / ACOUSTIC / ACP / ACOU → `09 51 13`; EXPOSED / OPEN / EXP → `09 00 00` (marker only); WD CEIL / WOOD → `09 64 29`; GYP / GWB / GYP BD / GB → `09 29 00`. Unknown → `09 50 00`.
- **Deviations from the brief's ~20-family table.** Two adjustments worth flagging: (1) `POL` added as a bare-token keyword to catch `POL-CONC` (dash-joined) without normalising punctuation; the dashed form is also explicit. (2) The wall mapping puts `FRP` BEFORE `WC` because `FRP` would otherwise be a no-match (no `WC` in `FRP`); ordering matters in the keyword sweep.
- **Discriminator (door/window/finish precedence).** Finish header heuristic (`_looks_like_finish_header`) hard-rejects when any door-/window-specific column is present (`HARDWARE`, `HDW`, `GLAZING`, `OPERATION`, `OPER`, `SHGC`, `UFACTOR`, `UVALUE`, `SILL`, `RATING`); requires a finish-specific signal (`FLOOR`, `CEILING`, `CLG`, `BASE`) plus the room column plus a supporting column. The integration hook `_maybe_extract_finish_schedule()` further enforces door + window precedence: if either of those extractors already fired on a page, the finish pass is skipped entirely. The 3-page discriminator test (`test_discriminator_three_page_pdf_each_extractor_isolated`) pins all three extractors firing only on their own page; the 2-page door+finish-phrase and window+finish-phrase regressions pin the precedence rule directly. **No edge cases hit on the door/window-precedence path** — the discriminator behaved exactly as designed.
- **Wall fan-out invariant.** When `wall_finishes` contains a single `"ALL"` key OR every compass direction has the same code, the synthesiser collapses to one wall item with `surface=wall_ALL` in notes; otherwise it emits one per unique direction with `surface=wall_<direction>`. The `"ALL"` key takes precedence over compass keys when both are present (pinned by `test_all_key_overrides_compass_dict`).
- **T3.5 leverage realized.** `core/extraction/finish_dedupe.py` is **80 LOC** vs the post-T3.5 `window_dedupe.py` at 94 LOC and `door_dedupe.py` at 82 LOC. Roughly half of those 80 lines are the module docstring + the carefully-shaped legacy-aggregate regex (which has 18 alternations to cover the wide finish-aggregate vocabulary); the actual configuration call to `dedupe_against_synthesis()` is 11 lines. The T3.5 scaffold's `match_family_by_description=True` and the `section_field="csi_section"` knobs covered every asymmetry the finish family introduced — **no scaffold modifications were needed**. If T3.5 had not landed first, the equivalent finish-dedupe module would have been ~210 lines (mirroring the pre-T3.5 `window_dedupe.py`).
- **Cross-pollination safety.** The finish CSI section prefixes (`"09 "`, `"06 64"`, `"03 35"`) are disjoint from the door prefixes (`08 11`, `08 14`, `08 71`, `08 80`) and the window prefixes (`08 41`, `08 44`, `08 5*`). Two regression pairs (`test_door_dedupe_never_touches_finish_rows` + `test_window_dedupe_never_touches_finish_rows`, plus the reverse `test_*_untouched_by_finish_dedupe`) pin the safety in both directions across all three families.
- **Wire-in.** `core/takeoff.py:reconcile()` collects `synthesized_finish_items` alongside the existing door + window collections, appends them after `_merge_takeoffs(...)` and the door/window appends, then calls `dedupe_finishes_against_synthesis(...)` after the existing door + window dedupes. Three targeted additions (collection list init, accumulation loop branch, append + dedupe call), no refactor of the existing T2/T2.5/T3 path. The `prepass.finish_schedule` attribute is the discriminator at reconcile-time.
- **Tests.** 144 new tests across three files:
  - `tests/test_finish_schedule_extraction.py` (36 tests): `parse_finish_code` parametric sweep (14 cases), detection heuristic (6 cases incl. door/window negative-discriminators), end-to-end extraction (8 cases incl. compass-wall fan-out, missing cells, raw-cells preservation, two ceiling-height formats), discriminator (3 cases pinning door/window precedence + the 3-page isolation regression), integration + schema bridge (4 cases).
  - `tests/test_finish_takeoff_synthesis.py` (74 tests): happy path + zero-item cases (4 tests), wall fan-out (4 tests), CSI mapping parametric sweep across floor (19) + base (8) + wall (10) + ceiling (10) = **47 mapping tests** total, confidence rubric (2 tests), description shape (3 tests), notes payload (2 tests), multi-room expansion (2 tests), exposed-ceiling marker (1 test), sheet-ID propagation (2 tests), reconcile round-trip (1 test), cross-division sanity (2 tests).
  - `tests/test_finish_dedupe.py` (34 tests): empty/safety (2 tests), 19-case parametric legacy-aggregate regex sweep, cross-pollination safety against doors + windows (4 tests, both directions), combinatorial preservation (1 test), out-of-family preservation including the two cross-division finish sections (3 tests), ordering preservation (1 test), reconcile integration (3 tests).

**Known limitations of this slice:**
- **Quantity = 0.0 on every synth row.** Phase T5 must land first to compute real SF (room-area cross-reference). The Phase T6 pricing pass will need a tolerance for the all-zero quantities so the suppression heuristic doesn't strip them.
- **Single `WALL` column collapses to one item, even if real walls have different finishes.** A schedule that writes "PT-1" in a single `WALL` column when the floor plan actually shows three different finish zones produces only one row; the operator must override at Phase T5 / T6 if the schedule was that lossy. (Pure data limit; nothing we can recover.)
- **No ceiling height → quantity wiring.** `ceiling_height_ft` is captured per record but not yet used. Phase T5 wall-area = perimeter × ceiling height; this is the cleanest place to consume it.
- **Phrase trigger requires English.** `FINISH SCHEDULE` / `ROOM FINISH SCHEDULE`. Sets in other languages or with non-standard captions (e.g. `INTERIOR FINISHES`) fall through to the table-header heuristic, which works but loses the cheap phrase signal.
- **No room-area cross-reference yet.** `FinishRecord.area_sf` is left None — the field exists in the dataclass + schema so Phase T5 can populate without a schema migration.

**Suggested next slices:**
- **Phase T5 — room-area cross-reference.** All three families (doors via opening deduction, windows via opening deduction, finishes via per-surface SF) need room SF to compute real quantities. This is the obvious next slice because it unlocks priced finish takeoffs and matures the door + window data the synthesisers already emit.
- **Phase T2.6 — panel / RTU / fixture schedules.** Same dispatch pattern, swap keywords + CSI codes per discipline (`23 00 00` HVAC, `26 24 16` Electrical panels, `22 40 00` Plumbing fixtures). Less leveraged than finishes (1:1 per record, EA units) but completes the schedule family and reuses the now-validated T3.5 scaffold for a fourth + fifth + sixth family.
- **Phase T6 — confidence-aware pricing.** Finish synthesis already lands at 0.92 confidence for fully-coded rows and 0.80 / 0.60 for partial; T6 can finally band the priced output and treat the zero-quantity finish rows as a separate "to-be-measured-by-T5" bucket rather than suppressing them.

---

### Phase T5 — Room-area cross-reference + finish quantity back-fill

**Status:** SHIPPED — this commit closes the loop that T4 deliberately left open. The room-schedule extractor (T1-shape, fully deterministic) now runs alongside the finish extractor on combined `ROOM FINISH SCHEDULE` pages, and a new back-fill pass in `core/takeoff.py` populates the previously-zero `quantity` on every finish `TakeoffItem` whose notes reference a room number that the room schedule covers. Suite: 624 → 766 passed (+104 new T5 tests plus ~38 net adds from Worker T's pricing-source work landed in parallel; 1 skipped unchanged).

**Implementation notes (this commit):**
- **Module structure.** Two new modules: `core/extraction/room_schedule.py` (the T1-shape extractor — `RoomRecord` dataclass + `RoomScheduleResult`, `detect_room_schedule`, `extract_room_schedule_from_page`, `extract_room_schedule`, `to_schema()` bridge, plus a small `merge_room_schedules()` helper used by reconcile) and `core/extraction/takeoff_backfill.py` (the post-synthesis `backfill_finish_quantities()` pass). `core/schemas.py` gains `RoomRecord` + `RoomScheduleResult` Pydantic models and a new optional `DrawingPrepassResult.room_schedule` field alongside the existing door / window / finish schedule fields. **No modification to `takeoff_synthesis.py`** — back-fill is a strict post-process so T2/T4 synthesis stays frozen.
- **Combined-schedule discriminator decision: Option A.** A combined `ROOM FINISH SCHEDULE` page (the common case — area + finish columns share one table) fires BOTH the existing `_maybe_extract_finish_schedule()` and the new `_maybe_extract_room_schedule()` hooks in parallel; both contribute records to the prepass result and are cross-referenced by `room_number` at reconcile time. Door / window precedence still wins — the room hook is skipped on pages where `prepass.door_schedule` or `prepass.window_schedule` already fired (mirroring T4's discriminator). The room-header heuristic also hard-rejects when any door / window-specific column is present (`HARDWARE`, `HDW`, `GLAZING`, `OPERATION`, `OPER`, `SHGC`, `UFACTOR`, `UVALUE`, `SILL`, `RATING`). **Option A worked cleanly** — the impedance with finish_schedule.py was zero; both extractors operate on independent column sets (room: `ROOM #` + `AREA` + `CLG HT`; finish: `FLOOR` / `BASE` / `WALL` / `CEILING`) and never collide.
- **Back-fill formulas (the actual ones, not the proposal).**
  - **`floor`** → `quantity = area_sf`, unit unchanged (`SF`)
  - **`ceiling`** → `quantity = area_sf`, unit unchanged (`SF`)
  - **`base`** → `quantity = perimeter_lf`, **unit upgraded from `SF` (synth-time) to `LF`** (the more correct unit for linear base trim). If `perimeter_lf` is missing the back-fill falls back to `perimeter_lf ≈ 4 × sqrt(area_sf)` (square-room approximation) with a confidence drop to 0.65 and a `perimeter=approximated` note.
  - **`wall_<dir>`** → `quantity = perimeter_lf × ceiling_height_ft × share`, where `share = 1.0` for a single `wall_ALL` row OR `share = 1/N` for `N` compass directions. **Ceiling-height fallback order:** room schedule first, then finish schedule's `ceiling_height_ft` if the room row has none, then skip with `wall=missing_ceiling_height` note (quantity stays 0.0, confidence stays at synth value).
- **Opening-deduction status: deferred to T5.1 (stretch goal not shipped this PR).** The back-fill function accepts `door_schedule` and `window_schedule` parameters and reconcile passes them through, but the deduction itself is intentionally a no-op for two reasons: (1) door / window records don't currently carry a `room_number` field (T1 follow-up flagged way back in Phase T1 + T2.5 notes) so per-wall attribution isn't yet possible, and (2) shipping the per-surface SF back-fill on its own already unblocks the T6 pricing loop. Each back-filled wall row carries a `openings_not_deducted=T5.1` note for audit-trail clarity. The function signature is already T5.1-ready — a follow-up just has to flip the deduction branch on once doors / windows expose room numbers.
- **Confidence rubric.** Back-filled rows preserve the 0.92 synth-time confidence when every input (area_sf for floor / ceiling, perimeter_lf + ceiling_height_ft for wall, perimeter_lf for base) was present in the room schedule. Any fallback (perimeter approximation, finish-schedule ceiling height) drops the row to **0.65** — comfortably below T6's `>=0.75` "auto-approve" target. Rows the back-fill skipped entirely (room not in schedule) keep their original 0.0 quantity AND original synth confidence so T6 can still route them to the operator queue.
- **Notes payload (audit trail).** Every back-filled row carries a stable trailing fragment appended to the existing T4 notes: `backfill=ok; room_area_sf=180.0; perimeter_lf=54.0; ceiling_ft=9.0; openings_not_deducted=T5.1`. Skipped rows carry `backfill skipped: room not in schedule`. The fragment is idempotent — re-running the back-fill is a no-op (pinned by `test_backfill_is_idempotent` in `test_takeoff_backfill.py`).
- **Multi-sheet room-schedule merge.** `merge_room_schedules()` deduplicates by `room_number` across all sheets that carry a room schedule. Ties (same room # on multiple sheets) resolve to the record with the most populated fields, then to the higher per-schedule confidence. The helper is type-agnostic (works on the internal dataclass AND on the Pydantic `RoomScheduleResult` that drawing_prepass.to_schema produces) and always returns a Pydantic instance for downstream consumers. **No across-floor collisions encountered in test data** — typical projects keep first-floor rooms `101+` and second-floor rooms `201+`.
- **Wire-in.** `core/takeoff.py:reconcile()` collects `room_schedule_results`, `finish_schedule_results`, `door_schedule_results`, `window_schedule_results` from each `SheetExtraction.prepass`. After the existing T2/T2.5/T3/T4 dedupe block, IF any room schedule was found, the merged room schedule + merged finish / door / window schedules are passed to `backfill_finish_quantities(project.takeoffs, ...)`. The result replaces `project.takeoffs` in-place. Five targeted additions; no refactor of the existing T2/T4 path.
- **Cross-pollination safety.** Back-fill is a strict noop on `TakeoffItem`s whose notes don't begin with `source=finish_schedule_prepass` — door / window / structural / MEP / site rows are untouched even when a room schedule is present (pinned by `test_non_finish_rows_unaffected_by_backfill`). The back-fill never invents new items; the count of `TakeoffItem`s is unchanged before / after the pass.
- **Tests.** 104 new tests across three files:
  - `tests/test_room_schedule_extraction.py` (57 tests): header detection (incl. combined-schedule + door / window negative discriminators), area / perimeter / ceiling-height parsing edge cases (`9'-0"` / `10'` / `9.5 FT` / `108"` / decimals), missing-cell handling, fallback line-clustering when `page.find_tables()` finds nothing, confidence rubric, end-to-end PDF round-trip, schema bridge, `merge_room_schedules` ordering + tie-breaking + dataclass-vs-Pydantic inputs.
  - `tests/test_takeoff_backfill.py` (32 tests): floor / ceiling area back-fill, base perimeter back-fill (incl. `SF → LF` unit upgrade), wall back-fill (single-`ALL`-row vs N-compass-directions vs missing-height vs perimeter-fallback), full-room sanity, room-not-in-schedule skip, item immutability + ordering + CSI / description preservation, idempotence, notes-format.
  - `tests/test_takeoff_t5_integration.py` (15 tests): PDF-based end-to-end (combined finish+room schedule, separate sheets, partial coverage, no-room-schedule no-op, room-schedule-without-finishes empty case, post-dedupe survival, multi-sheet room merge, door-schedule negative case, in-memory direct integration, base unit upgrade, confidence bands at 0.92 / 0.65, schema round-trip through Pydantic, ceiling-height fallback to finish schedule).

**Known limitations of this slice:**
- **Opening deduction not yet shipped (deferred to T5.1).** Wall SF is currently `perimeter × height × share` with zero deduction for door / window openings. Average commercial opening is ~21 SF (one 3'0" × 7'0" door) so under-deduction over-counts wall paint by ~5–10% on a typical office. The T5.1 PR has to (a) add `room_number` to `DoorRecord` and `WindowRecord` (T1 + T2.5 follow-up) and (b) flip on the deduction branch already plumbed into `backfill_finish_quantities`.
- **Square-room perimeter fallback is coarse.** `4 × sqrt(area_sf)` over-estimates perimeter on long-thin corridors (`80 SF` corridor at `40 LF × 2 LF` has perimeter `84 LF`, fallback yields `~35.8 LF` — a 57% under-count). The confidence drop to 0.65 routes these to operator review, which is the correct behaviour, but T5.1 / T6 should warn explicitly in the per-row note when the fallback fires on a room with a high aspect ratio.
- **Single-direction walls collapse to `wall_ALL`.** If a finish schedule has all four compass directions sharing one paint code, T4 collapses to one `wall_ALL` row, which the back-fill multiplies by the full perimeter (correct). But if the operator wants per-direction breakdowns for clash with the floor plan, the back-fill can't recover them from the collapsed row.
- **No ceiling-penetration deduction.** Ceiling SF = area_sf with no subtraction for diffusers, lights, sprinkler heads, or skylights. Typical commercial deduction is 2–5% of ceiling SF; over-counted on every T5 ceiling row. Phase T6 or a T5.2 follow-up.
- **Drop-ceiling vs. open-plenum disambiguation still manual.** Phase T4 emits `09 00 00` marker rows for `EXPOSED` / `OPEN` ceilings; T5 still back-fills these to `area_sf` even though the marker is supposed to be a zero-pricing audit row. The pricing pass already skips these (waste = 0, suppressed), but the quantity column will now show area instead of 0 — Phase T6 should either preserve the marker quantity at 0 or special-case it.

**Suggested next slices:**
- **Phase T5.1 — opening deduction.** The narrow follow-up. Add `room_number` to `DoorRecord` and `WindowRecord` (T1 + T2.5 follow-ups), then flip on the deduction branch in `backfill_finish_quantities` (the parameters are already plumbed). Modest test surface (~15 tests). Caps the T5 work cleanly.
- **Phase T6 — confidence-aware pricing.** Now actually viable since the finish rows carry real quantities. T6 can finally band the priced output (auto-approve ≥ 0.85, review 0.65–0.85, hand-takeoff < 0.65) and treat the perimeter-fallback rows (0.65 band) as the review queue rather than suppressing them.
- **Phase T6.b — room-finish-matrix schedule shape.** Some architects use a matrix layout (rooms across the top, finishes down the side) instead of the row-per-room schedule T4 handles today. Same back-fill consumes the result once the matrix-shape extractor lands; the synthesis + back-fill path is unchanged. Recommended as a small T6.b after T6.
- **Phase T2.6 — panel / RTU / fixture schedules.** Unchanged from the T4 hand-off; T5 didn't disturb the EA-unit dispatch families and they remain the next obvious schedule slice once finishes are priced.

---

### Phase T5.1 — Door / window opening deduction in wall SF back-fill

**Status:** SHIPPED — closes the narrow T5 deferral. `DoorRecord` and `WindowRecord` now carry `room_number`, the door / window schedule extractors parse a `ROOM` / `RM` / `LOCATION` column when present, and `backfill_finish_quantities` subtracts per-room opening SF from each wall row's quantity. Wall SF is now NET-of-openings rather than GROSS. Suite: 766 → 807 (+41 new T5.1 tests, plus +93 from Worker V's parallel HD Pro / Lowe's scrapers landing in the same window; 1 skipped unchanged).

**Implementation notes (this commit):**
- **Schema additions.** `DoorRecord` (dataclass in `core/extraction/door_schedule.py` + Pydantic mirror in `core/schemas.py`) and `WindowRecord` (same pair) gain `room_number: Optional[str] = None`. Treated as a string throughout — room numbers like `"101A"` / `"M-101"` are common and must survive round-trip without coercion. The `to_schema()` bridges in both extractor modules thread the field through.
- **Schedule parser detection.** A new word-level `_room_header_index()` helper in both extractors finds the room column via the keyword set `{ROOM, RM, LOCATION, LOC}`. Word-level membership is mandatory: the generic substring-tolerant `_header_index()` would alias `RM` → `FRAME` (a standard door / window column) and silently steal the wrong cell. Two regression tests pin this — one each for the door and window extractor — using a `FRAME`-only schedule and asserting `room_number is None`.
- **Edge case: `ROOM NUMBER` header.** Belt-and-braces — if a schedule labels the column `ROOM NUMBER`, the substring matcher would otherwise alias the cell to `MARK` (the mark candidates include `NUMBER`). The fix is a `_header_index_excluding()` re-pick on mark when the room column shadowed it. A targeted test in `test_takeoff_t5_1_opening_deduction` exercises real schedule headers.
- **Per-wall deduction formula.** For each wall row of a back-filled room:
  - `raw_quantity = perimeter_lf × ceiling_height_ft × share` (share = 1.0 for `wall_ALL`, 0.25 for compass walls)
  - `total_opening_sf = Σ (w × h / 144 for each door/window with matching room_number)`, with default fallbacks for openings missing dimensions
  - `deduction = min(total_opening_sf × share, raw_quantity)` — cap firing surfaces a `openings_overflow` note
  - `net_quantity = max(raw_quantity − deduction, 0.0)`
- **Default opening sizes (when dimensions missing).** Standard commercial defaults: **21 SF for a door** (3'-0" × 7'-0", the AIA-typical commercial interior door) and **12 SF for a window** (3'-0" × 4'-0", the median of residential through punched-window sizes). The choices are conservative — under-deduction is safer than over-deduction because T6 pricing tolerates a slightly-gross wall but a negative wall would crash the cost-DB lookup. Pinned by `test_door_without_dimensions_uses_default_opening_sf` and the window equivalent so any future tuning is a deliberate change.
- **Wall-direction assignment (proportional share, not per-direction).** Doors and windows distribute their opening SF proportionally across every compass wall of the room (each compass wall gets `share = 0.25` regardless of how many are actually finished). This is a v1 approximation appropriate when the door / window schedules don't carry a `wall` column (which is true for ~all commercial schedules today). When the architect uses a single `WALL` column the synthesiser collapsed to `wall_ALL` (`share = 1.0`), the deduction is the full per-room total — the more accurate case because there's only one wall row to apply it to.
- **Orphan + unknown-room openings (silent skip + debug log).** Three classes of opening are NOT deducted: (a) openings without `room_number`, (b) openings whose `room_number` doesn't match any room in the merged room schedule, (c) openings whose room exists but has no wall rows to apply to (e.g. ceiling-only room). All three are aggregated into a single debug-level log line per back-fill call so the auditor can drill in but the per-row notes stay clean. Two integration tests confirm wall SF stays gross in case (a) and (b).
- **Audit-note payload.** Successful deduction emits `openings_deducted=<N>; opening_sf=<total>; <surface>_deduction=<amount>` per wall row, idempotent on re-run. The cap-firing case adds `openings_overflow: <surface> opening SF exceeded raw wall SF`. The T5 legacy `openings_not_deducted=T5.1` hint is REPLACED by the new format on every wall row where any deduction happened; the `openings not deducted (no door/window schedules provided)` hint only fires now when BOTH `door_schedule` and `window_schedule` are `None` (preserves the audit signal for projects without opening schedules at all).
- **Wire-in.** No change to `core/takeoff.py` — `reconcile()` already passed `door_schedule` / `window_schedule` to `backfill_finish_quantities` per T5's signature-stable hand-off. T5.1's work was entirely behind that already-stable interface, so this PR ships zero changes to the reconcile pipeline.
- **Confidence rubric.** Unchanged from T5: 0.92 for the full-info case, 0.65 when the perimeter fell back to `4 × sqrt(area)`. Opening deduction does NOT bump confidence back up on the fallback branch — a perimeter-approximated wall with a real door deduction is still routed to operator review (pinned by `test_opening_deduction_with_fallback_perimeter_keeps_low_confidence`).
- **Tests.** 41 net new tests across four files:
  - `tests/test_takeoff_backfill.py` (+17 tests): single / multiple doors per room, default opening sizes, mixed-attribution rooms, cap behaviour on wall_ALL and compass walls, idempotency, alphanumeric room numbers, fallback-perimeter interplay, the legacy "no openings" note still fires when neither schedule is provided.
  - `tests/test_takeoff_t5_1_opening_deduction.py` (+10 tests, new file): in-memory two-room deduction, door + window combined deduction, compass-wall proportional distribution, full-pipeline PDF round-trip (combined room+finish + door schedule), pure-Pydantic schema round-trip preserves `room_number`, behaviour parity with T5 when no opening schedules are provided.
  - `tests/test_door_schedule_extraction.py` (+7 tests): `ROOM` / `RM` / `LOCATION` header parsing, alphanumeric room numbers, empty ROOM cells → `None`, the FRAME-collision regression.
  - `tests/test_window_schedule_extraction.py` (+7 tests): mirror of the door cases for windows.

**Calibration findings from this slice:**
- **Cap firing on tiny rooms is real.** The overflow test in `test_opening_sf_exceeds_wall_sf_caps_at_raw_wall_sf` uses a degenerate 8 LF × 8 ft room (64 SF total) with an absurd 100 SF door to verify the cap, but proportionally this also fires on legitimate "small closet with an oversized double door" cases. The audit note `openings_overflow` is the correct surfacing — Phase T6 should route these to the operator queue rather than auto-approving.
- **"ALL" vs compass distribution.** In the test data the synthesised PDFs split ~50/50 between schedules using a single `WALL` column (→ `wall_ALL`, share=1.0) and four compass columns (→ `wall_N/S/E/W`, share=0.25 each). The proportional-share design covers both cases without per-schedule heuristics. Real-world projects skew more heavily to the single-column convention — most architects don't bother with compass-wall finish detail unless the elevations differ materially.
- **No T1–T5 bugs spotted while wiring.** The existing room schedule / finish schedule / door schedule / window schedule extractors all surfaced clean records during integration testing. The only edge case discovered was the `ROOM NUMBER` header substring-collision with the mark column's `NUMBER` candidate; pinned with `_header_index_excluding()` and a regression test.

**Known limitations of this slice:**
- **Proportional-share is a v1 approximation.** Doors and windows are spread evenly across every compass wall regardless of where they actually sit on the floor plan. For a tall narrow room with the door on the short wall and a window on the long wall, the proportional model under-deducts the short wall and over-deducts the long wall. Net building-level error is ~0; per-wall pricing can be off by 5–10% on the affected rows. T5.2 (per-direction lookup) closes this once the schedule data carries the column.
- **Default opening sizes are blunt.** A schedule that ships an exterior storefront door without dimensions gets the 21 SF residential default — under-deducting wall SF by 30–50 SF for a 6'-0" × 8'-0" double aluminum entrance. Operators should fill in dimensions on storefront doors; the back-fill emits a `openings_deducted=` audit note even on default sizes so the operator can see and override.
- **Single-direction door schedules unsupported.** Per the brief deferral, door schedules don't carry a `wall: "N"` column today, so the proportional-share approximation is intentionally v1. T5.2 lifts this once one or two source projects ship that column.
- **Ceiling and floor penetrations still un-deducted (carried over from T5).** Sky-lights, diffusers, sprinkler heads are out of scope for T5.1 — they're a ceiling-SF concern, not a wall-SF concern. Documented in the T5 "Known limitations" list and still open as a T5.2 / T6 follow-up.

**Suggested next slices:**
- **Phase T5.2 — per-direction opening attribution.** When (and only when) a door / window schedule publishes a `WALL` column (compass-direction tag per opening), replace the proportional share with a per-direction lookup. The signature of `backfill_finish_quantities` doesn't change; the helper `_build_room_openings_map()` simply returns a finer-grained shape (room → direction → SF). Modest follow-up (~10 tests) but only worth doing if calibration shows ≥5% pricing skew vs. the proportional model on real projects.
- **Phase T6 — confidence-aware pricing.** Now FULLY unblocked. T5 + T5.1 together produce the clean confidence bands T6 was waiting for: 0.92 for the fully-coded happy path, 0.65 for the perimeter / opening fallbacks, original synth confidence on rooms the back-fill couldn't reach. T6 can finally band the priced output (auto-approve ≥ 0.85, review 0.65–0.85, hand-takeoff < 0.65) and treat the perimeter-fallback rows (0.65 band) as the review queue.
- **Phase T6.b — room-finish-matrix schedule shape** and **Phase T2.6 — panel / RTU / fixture schedules.** Unchanged from the T5 hand-off.

---

**1-line goal:** Tighter, per-sheet-class prompts that boost recall on plumbing, electrical, HVAC, and life-safety counts, with prompt-engineering specifically against the `LS` unit-default issue.

**Deliverables:**
- Split `prompts/mep.txt` into four prompts:
  - `prompts/plumbing.txt` — fixture counts, hose bibbs, floor drains, cleanouts, hot/cold water rough-in allowance per fixture.
  - `prompts/electrical.txt` — receptacles, switches, light fixtures, panels, transformers, EV chargers, branch-wiring SF allowance.
  - `prompts/hvac.txt` — RTUs, AHUs, ERVs, exhaust fans, VAV boxes, ductwork SF served, refrigerant line LF (low confidence).
  - `prompts/fire_protection.txt` — sprinkler heads (EA), wet-pipe sprinkler system (SF served).
- Update `core/extractors._select_prompt` to dispatch by `Discipline` instead of collapsing to "mep".
- Rewrite the `UNIT SELECTION RULES` section in `prompts/architectural.txt` to default to dimensional units (EA, LF, SF, BF) and use `LS` ONLY for genuine lump-sum scopes. Calibration v3 documented that every wood-framing item came back as `LS`, which then collided with the unit-mismatch suppressor. The current `prompts/architectural.txt` already has a draft of these rules — Phase T2 tightens them with worked examples drawn from the calibration v4 run (see Validation Strategy below).
- Add a per-prompt few-shot example block at the bottom of each new MEP prompt. Three real schedule rows in JSON form, drawn from a permissive-license public bid set or hand-crafted from the existing bid workspaces.
- Tests:
  - `tests/test_extractor_unit_defaults.py` — exercises `extract_sheet` with a mocked LLM that returns hand-crafted `raw_takeoffs` for each unit-selection edge case in the new prompts. Asserts the resulting `TakeoffItem`s use the right unit and would not be suppressed downstream.
  - `tests/test_prompt_loading.py` — confirms each new prompt file loads via `prompts.load()` and parses to a string.

**Scope:** Countable Items, especially the MEP slice. Indirect uplift on Schedules where the schedule sheet is dispatched to one of the new MEP prompts because it's a discipline-specific schedule (panel schedule, fixture schedule, RTU schedule).

**Expected accuracy uplift:**
- Countable items (MEP subset): from ~70% to **80–88%** on plumbing / electrical / HVAC sheets.
- Indirect: removes the `unit: LS` issue documented in v3, which is a precondition for any priced output on rough-carpentry items.

**Effort estimate:** S (1–2 days for the prompt-engineering work, plus another 1–2 days for the v4 calibration loop).

**Dependencies:**
- Phase T1 strongly preferred (so deterministic schedule rows already win and the LLM is only filling gaps).
- LLM provider with vision (already wired — `core/llm_client.py` supports both Anthropic and OpenAI).

**Risk / pitfalls:**
- Prompt engineering is iterative. Budget 2 calibration runs against the existing drawing sets.
- Splitting the MEP prompt 4-way increases the maintenance surface. Mitigation: a shared header section emitted by `prompts.load_mep_common()` that all four import, so unit rules and discipline tags are edited in one place.
- Per-prompt few-shot examples are a known prompt-injection risk if any of the examples were ever fetched from the inbox. Mitigation: all examples are hand-crafted from existing internal bid workspaces, never auto-fetched.

**Validation strategy:**
- Calibration v4 with `--drawings` on (the v3 run was `--no-drawings`). Compare line-item EA counts against a hand-count on the same three drawing sets used in T1's validation.
- Specific regression-style check: zero `TakeoffItem.unit == "LS"` rows for any csi_division in `{06, 08, 09, 22, 23, 26}` on the Carr EFA run.

**No-go signal:**
- v4 calibration shows < 5 percentage-point uplift on Countable Items on a fair comparison vs v3 baseline. Indicates the LLM is the wrong tool for the per-sheet specialization and the work should be reabsorbed into T1 (schedule extraction) and T7 (OCR) instead.

---

### Phase T3 — Cross-sheet TakeoffItem dedup and reconciliation

**Status:** IN PROGRESS — door-dedupe slice landed in this commit (LLM door aggregates retired when deterministic synthesis covers them). The broader cross-sheet rapidfuzz dedup graph below is still pending.

**Implementation notes (door-dedupe slice, this commit):**
- **New module:** `core/extraction/door_dedupe.py` exposes a single pure function `dedupe_doors_against_synthesis(items: list[TakeoffItem]) -> list[TakeoffItem]`. No new schema field; the existing `notes` prefix from Phase T2 is the discriminator.
- **Discriminator rules:**
  - "Synthesised" = `item.notes` starts with `f"source={SYNTHESIS_SOURCE_TAG}"` (constant imported from `core.extraction.takeoff_synthesis`, never hard-coded).
  - "Door" = `item.csi_division == "08"` (Division 08 — Openings).
  - "LLM door" = door AND not synthesised.
  - "Same mark" = the synthesised row's mark (parsed from its notes `mark=...` segment, fall-back to the `^Door <MARK> — ` description regex) is found as a whole-token, case-insensitive match inside the LLM row's description. The brief specifies a substring; we tighten with alphanumeric-boundary lookarounds so a mark of `"10"` does not spuriously match `"1010"`. Marks shorter than 2 characters are skipped (too promiscuous).
  - "Legacy aggregate" = description matches `r"^(hollow\s+metal|solid[\-\s]?core\s+wood|wood|steel|aluminum|glass)\s+doors?(\s*:?\s*\d+\s+ea)?\s*$"` OR `r"^doors?\s*\(type\s+unspecified\)\s*$"` (both case-insensitive). These cover the bare descriptions `_derive_takeoffs` actually emits today AND the explicit `: N EA` suffix form from the brief.
- **Safety rule:** when no synthesised door exists anywhere on the project, the input is returned unchanged. We never drop a legacy aggregate without a deterministic fallback to take its place.
- **Wired into the pipeline** at one targeted point in `core/takeoff.py:reconcile()` — right after the T2 `all_takeoffs.extend(synthesized_door_items)` append, immediately before the `ProjectModel` is constructed. The legacy `_derive_takeoffs` is intentionally NOT deleted; the dedupe filter handles retirement so the function stays available behind a no-synthesised-door fallback.
- **Tests:** 24 new tests in `tests/test_door_dedupe.py` covering the eight cases called out in the brief (empty, no-synth, mark match, mark non-match, legacy aggregate with synth, legacy aggregate without synth, mixed CSI codes, combinatorial), plus the reconcile() smoke test, plus ordering preservation, plus short-mark and word-boundary safety regressions, plus a 9-row parametric sweep of the legacy-aggregate regex. Suite: 281 → 305 passed (1 skipped unchanged).

**Known limitations of this slice:**
- **Exact-substring mark matching only.** An LLM row with mark `"101"` and a synthesised row with mark `"101A"` will both survive — neither is a token of the other under the boundary rule. A future fuzz-match pass (rapidfuzz on the parsed mark substring) would close this gap.
- **No same-`type` heuristic.** An LLM row with description `"Hollow metal door, custom"` and no mark survives even when 10 synthesised HM doors cover the project. The conservative-dedupe stance (don't drop what we can't confidently attribute) is intentional but errs toward over-count.
- **Project-wide, not sheet-wide.** The brief's safety rule is "ANY synthesised door on the same project", which is what we implement. A more aggressive sheet-scoped filter would catch cross-sheet duplicates the current pass intentionally preserves.
- **Hardware-set rollups untouched.** `_derive_takeoffs` still emits `"Door hardware sets"` (qty = total door count). Synthesis doesn't have a hardware aggregate yet, so dropping the LLM one would be a net loss. Phase T2.5 candidate.

**Suggested next slices:**
- **Phase T2.5: window-schedule extraction.** Mirror `core/extraction/door_schedule.py` swapping `FRAME/HARDWARE` for `GLAZING/OPERATION`; the synthesis + dedupe pattern in `takeoff_synthesis.py` + `door_dedupe.py` extends one-to-one to `WindowRecord` and Division 08 50 / 08 80 rollups.
- **Phase T4: dedupe extension to room and finish schedules.** Same notes-prefix discriminator pattern, different aggregator patterns (room area roll-ups, per-finish SF roll-ups). The dedupe-by-tag scaffolding can move to `core/takeoff/dedup.py` and accept a `source_tag` argument so each schedule kind gets its own module.
- **Phase T5: door↔room association.** Extract `room_from / room_to` columns from the door schedule (T1 follow-up) and seed `DoorEntry.room_number`, which feeds the wall-finish opening-deduction in T5.
- **Phase T6: confidence-aware pricing.** The dedupe pass leaves the synthesised row's 0.92 confidence intact; T6 can finally use it to band the priced output.

**1-line goal:** A given real-world item (a single door, a single RTU) ends up as exactly one priced line, even when it appears on architectural + life-safety + hardware + spec sheets.

**Deliverables:**
- New `core/takeoff/dedup.py`. (Note: today `core/takeoff.py` is a single file. This is a good moment to split it into `core/takeoff/__init__.py`, `core/takeoff/reconcile.py`, `core/takeoff/derive.py`, `core/takeoff/dedup.py`. Backwards-compatible re-exports preserved at `core.takeoff`.)
- `dedup_takeoff_items(items: list[TakeoffItem], rooms, doors, windows, structural, mep, schedule_extractor_rows) -> list[TakeoffItem]`:
  - Pre-pass: bucket by `csi_division`.
  - Within bucket, build a similarity graph: edges between items with `rapidfuzz.fuzz.token_set_ratio(_norm(desc_a), _norm(desc_b)) >= 88` AND identical `unit` AND `quantity` within 10% of each other.
  - For each connected component, the surviving row is the one with the highest `confidence`. The merged row's `source_sheet_ids` is the union; the merged row's `notes` is concatenated with a `"deduped across <N> sheets"` suffix.
  - Schedule-derived rows (from T1) win against LLM-only `raw_takeoffs`, regardless of confidence delta — schedules are authoritative for the items they cover.
- Update `core/takeoff/reconcile.py: reconcile()` to call `dedup_takeoff_items()` after `_merge_takeoffs()` and before constructing `ProjectModel`.
- New schema field `TakeoffItem.dedup_origin: Optional[str] = None` (values: `"schedule"`, `"derived"`, `"llm"`, `"deduped"`, `None`). Used by the exporter to surface origin in Excel.
- Tests:
  - `tests/test_takeoff_dedup.py` — ~8 tests. Synthesized `TakeoffItem` lists with overlapping descriptions / units / quantities. Assert the dedup graph collapses correctly. Edge cases: zero items, one item, items in different divisions.
  - One regression test based on the Cmd Post NDI bid set: confirm that "Hollow metal doors" appears exactly once, not three times, after reconcile.

**Scope:** All categories — this is a cross-cutting cleanup phase, not new extraction.

**Expected accuracy uplift:**
- Total-bid accuracy: removes systematic over-counting on bid sets where the same item appears on multiple drawing sheets. Typical effect on a 50-sheet commercial set is on the order of 8–15% total dollar reduction toward truth.
- No category sees its single-line accuracy improve, but the headline number stops being inflated.

**Effort estimate:** M (3–5 days). The dedup graph itself is straightforward; the calibration to tune the rapidfuzz threshold and the quantity-tolerance is the bulk of the time.

**Dependencies:**
- Phase T1 strongly preferred (schedule rows give us authoritative ground truth to anchor the dedup against).
- `rapidfuzz` (already vendored).

**Risk / pitfalls:**
- False-positive dedup. Two genuinely-different lines with similar descriptions (e.g. "Hollow metal door 3'-0" x 7'-0"" vs "Hollow metal door 3'-6" x 7'-0"") could collapse. Mitigation: include size / type fields in the normalization key when present; default threshold to 92 (high), tune down only if recall is poor.
- Dedup decisions are hard to audit after the fact. Mitigation: persist the dedup graph as a side-output (`exports/<run>/dedup_report.json`) for every run.

**Validation strategy:**
- On the Carr EFA Project Manual + drawings + addendum 1 run: confirm hand-count of total doors matches the deduped line. Repeat for fixtures and panels.
- Internal consistency check: `dedup_takeoff_items` is idempotent on its own output.

**No-go signal:**
- False-positive rate > 5% on the gold set, i.e. more than 1-in-20 dedup decisions collapses two genuinely-distinct lines. At that point the dedup is doing more harm than the over-counting it fixes.

---

### Phase T4 — Scale detection and geometric measurement

**1-line goal:** Turn the `TitleBlockData.scale_factor` we already parse into real-world quantities for LF and SF takeoffs, using the PDF's vector geometry rather than vision.

**Deliverables:**
- New `core/extraction/vector_geometry.py`:
  - `extract_polylines(pdf_path: Path, page_index: int) -> list[Polyline]` — uses `page.get_drawings()` (PyMuPDF) to walk the page's vector drawing operators and rebuild closed polygons + open polylines as a list of `(x, y)` points in page coordinates.
  - `extract_text_with_position(pdf_path: Path, page_index: int) -> list[PositionedText]` — uses `page.get_text("dict")` to attach a bounding box to every text span. Needed because room names need to be associated with the polygon they label.
  - `measure_polyline(p: Polyline, scale_factor: float) -> Measurement` — returns `(length_inches, area_sqin, area_sqft, perimeter_ft)`. `length_inches = sum_of_segment_lengths * (1/scale_factor)`, where `scale_factor` is the paper-inches-per-real-world-inch from F3.
  - `associate_label_to_polygon(text_spans, polygons) -> dict[polygon_id, label_text]` — point-in-polygon test to attach room-name / room-number text to the polygon enclosing them.
- New `core/extraction/room_geometry.py`:
  - `extract_room_polygons(pdf_path: Path, page_index: int, scale_factor: float) -> list[Room]` — combines `extract_polylines` + `associate_label_to_polygon` to emit `Room(name=..., number=..., area_sqft=..., perimeter_ft=...)` populated from geometry. Used as a deterministic fallback for any `Room` produced by F3 or the LLM with `area_sqft is None`.
- Update `extractors._build_from_prepass` to invoke `room_geometry.extract_room_polygons` when `prepass.title_block.scale_factor is not None`, and merge the geometric-derived areas into the prepass rooms (highest confidence wins on overlap).
- New schema field `Room.area_source: Optional[Literal["schedule", "label", "geometry", "llm"]] = None` so exports can show provenance.
- Tests:
  - `tests/test_vector_geometry.py` — synthesized 1-page PDFs with known-size rectangles. Assert measurement accuracy within 0.5%. Cover the four common architectural scales: 1/4" = 1'-0", 1/8" = 1'-0", 3/16" = 1'-0", 1" = 10'.
  - `tests/test_room_geometry.py` — synthesized floor plan with two adjacent rooms, each with a room-number label inside. Assert both rooms are extracted with correct number, area_sqft (within 0.5%), perimeter_ft (within 0.5%).
  - One end-to-end test on a single page extracted from the Carr EFA drawings (a representative architectural floor plan saved as a 1-page fixture PDF in `tests/fixtures/`).

**Scope:** Linear category (LF wall / partition / baseboard), Area-based category (SF flooring / ceiling / paint when paired with a room finish from the schedule).

**Expected accuracy uplift:**
- Area-based (SF) when a vector floor plan exists: from ~50% (today's value-or-null state from `Room.area_sqft` populated by LLM) to **75–85%**. Below the 80% target band because labeling and polygon-segmentation errors are a real source of misses.
- Linear (LF wall) when a vector floor plan exists: from essentially 0% (today no LF wall takeoff exists) to **55–70%**. Wall lines on a PDF aren't always topologically connected polylines — sometimes they're individual line segments — so a polyline reconstructor needs care.

**Effort estimate:** L (1–2 weeks). The PyMuPDF `get_drawings()` API is well-documented but the polygon reconstruction (closing open polylines, removing nested duplicates, handling text-cut walls) is genuinely fiddly.

**Dependencies:**
- F3 (already done).
- PyMuPDF `page.get_drawings()` (already in our PyMuPDF version; no new dep).
- For point-in-polygon: `shapely` would be the natural choice, but adds 6 MB. Mitigation: implement a small `point_in_polygon` helper (~30 LOC, ray-casting) in `core/extraction/geometry_util.py` to avoid the dependency. Revisit shapely if we hit edge cases.

**Risk / pitfalls:**
- Many architectural PDFs are "rasterized vector" — i.e. the line art is still vector but it's been flattened so wall pen-strokes are independent line segments rather than a single polyline. The polygon reconstructor has to walk a topology, not just collect polylines.
- Floor plans with hatched fills, dimensions overlaid on walls, and dimension extension lines confuse the polyline extraction. Need a filter pass to drop dimensions (short colored thin lines with arrowheads).
- Scanned drawings are out of scope for this phase; they remain at today's accuracy. Real fix is T7 (OCR + raster vectorization).
- Scale could vary within a single sheet (multiple details with their own scales). Today's `TitleBlockData.scale` is single-valued; geometric measurement on a sheet with multiple scales would produce nonsense.

**Validation strategy:**
- Build a fixture set of 5–10 representative floor plans (the three drawing sets we have, plus a couple of public-domain ones) and hand-measure 3 walls + 3 rooms per sheet. Compare `extract_room_polygons` output. Success bar: median error < 5%, max error < 15% on rooms; median error < 8%, max error < 25% on linear walls.

**No-go signal:**
- Median room-area error > 10% on the fixture set after one iteration. Indicates the polygon reconstruction isn't reliable on real architectural PDFs, and we should partner with a commercial OCR/CV provider for this category instead (Section 5: Buy).
- More than 30% of the fixture sheets fail to produce ANY polygons because the vector layer has been flattened to raster. Indicates we need to introduce raster vectorization (potrace / pix2shape) — a much bigger scope; this should bounce to backlog and be revisited as a separate phase.

---

### Phase T5 — Per-room finish takeoff

**1-line goal:** For each room, produce SF of floor finish + SF of wall finish + SF of ceiling finish, by finish type, end-to-end automatically.

**Deliverables:**
- New `core/extraction/finish_takeoff.py`:
  - `build_per_room_finish_takeoffs(rooms: list[Room], finish_schedule: Schedule | None, doors: list[DoorEntry], windows: list[WindowEntry]) -> list[TakeoffItem]`:
    - For each room with `area_sqft` set (from T4 or from the schedule): emit floor-finish SF, ceiling-finish SF.
    - For each room with `perimeter_ft` + `ceiling_height_ft` set: emit wall-finish SF = `perimeter_ft * ceiling_height_ft - opening_deduction`. Opening deduction: for each door associated with the room, subtract `door.width_in / 12 * door.height_in / 12` (default 21 SF when nulls); for each window associated with the room, subtract `window.width_in / 12 * window.height_in / 12` (default 12 SF when nulls).
  - Group resulting takeoffs by `(csi_section, finish_name)` for the exporter.
- Update `core/takeoff/derive.py: _derive_takeoffs` to delegate the finish portion to `build_per_room_finish_takeoffs` and remove the bucket-based heuristic. Preserve the existing wood-vs-tile-vs-carpet csi-mapping logic.
- New schema field `Room.opening_count: int = 0` and a method on `Room` to estimate opening-deduction SF (used by the wall-finish builder).
- Door↔Room association: today doors do not carry a `room_id`. Add `DoorEntry.room_number: Optional[str] = None` and populate it from the door-schedule "room from / room to" columns when present (T1 extracts those).
- Tests:
  - `tests/test_finish_takeoff.py` — ~10 tests. Tabulated rooms + finishes + doors + windows; assert finish takeoffs balance against hand-calc.
  - One end-to-end test on the Carr EFA fixture sheet (post-T4).

**Scope:** Area-based category, specifically per-room finish.

**Expected accuracy uplift:**
- Area-based (finish SF): from ~50% (intermittent — only fires when both `area_sqft` and `floor_finish` happen to land on the same Room) to **75–85%** (fires whenever T4 gives us a room area and the finish schedule gives us a finish). Door / window opening deductions in walls bring wall-paint accuracy down by 2-3 points (it's tuned conservatively).

**Effort estimate:** S (1–2 days), assuming T4 has shipped. Without T4, this phase has nothing to multiply against and should not start.

**Dependencies:**
- T1 (finish schedule extraction).
- T4 (room area from geometry).
- Door↔Room association needs the door-schedule's "from-room / to-room" columns extracted by T1.

**Risk / pitfalls:**
- The finish schedule sometimes lists finishes per surface, sometimes per material. Same data, different layouts. T1's finish schedule extractor needs to handle both.
- Wall-finish SF is sensitive to ceiling-height assumption when not in the room schedule. Default to 9.0 ft and warn (today's `_avg_room_height` default). Add a `Room.ceiling_height_ft` source field so we can prefer the schedule, fall back to the average, and last-resort to 9.0.

**Validation strategy:**
- On the Carr EFA gold set: per-room SF floor and SF wall paint compared against hand-calc from the same finish schedule and room schedule.
- Internal balance check: sum of per-room floor SF == sum of room areas (no overlaps, no missed rooms) for any room with `area_sqft` set.

**No-go signal:**
- Door / window association rate < 50% across the gold set. Indicates the door-schedule "room-from / room-to" columns aren't reliably present, and we need an additional door↔room association step from plan geometry — bounces back to T4.

---

### Phase T6 — Confidence-aware pricing (auto / review / hand bands)

**Status:** SHIPPED — this commit landed the band-aware pricing pass, the Excel + PDF + Streamlit surfacing, and 74 new tests on top of the existing T1–T5.1 confidence rubric. Suite: 901 → 975 passed (1 skipped unchanged).

**1-line goal:** Use the `TakeoffItem.confidence` we already store to band priced `CostLine`s into AUTO_APPROVE / OPERATOR_REVIEW / HAND_TAKEOFF, route the bottom band out of the headline grand total, and surface two queue sheets so the estimator knows exactly which rows need eyeballs vs. a manual takeoff.

**Implementation notes (this commit):**
- **Band thresholds.** `core/schemas.py` adds `CostBand` (`AUTO_APPROVE` / `OPERATOR_REVIEW` / `HAND_TAKEOFF`) plus the boundary constants `COST_BAND_AUTO_THRESHOLD = 0.85` and `COST_BAND_REVIEW_THRESHOLD = 0.65` and a single source-of-truth helper `band_for_confidence(confidence, *, suppressed=False)`. Both boundaries are inclusive on the upper-band side (`0.85 → AUTO`, `0.65 → REVIEW`), exactly matching the prepass confidence rubric (`drawing_prepass._score`) and the back-fill rubric (`takeoff_backfill._BACKFILL_CONF_FALLBACK = 0.65`) so a perimeter-fallback row ends up in `OPERATOR_REVIEW` by construction.
- **Suppression → HAND_TAKEOFF.** `band_for_confidence` treats `suppressed=True` as the highest-priority rule — a unit-mismatch line (calibration v2's $34 K phantom guard) lands in `HAND_TAKEOFF` regardless of its underlying confidence. The line's `total_cost == 0` from the suppression branch means it contributes $0 to `total_hand_takeoff`, so there is no double-counting risk between the existing suppression and the new band aggregates. (Suppressed lines DO appear in `hand_takeoff_line_items` for the worklist UI — the queue is "lines needing manual eyes", not "dollars excluded from total".)
- **No-confidence (legacy LLM) → OPERATOR_REVIEW.** The schema default `TakeoffItem.confidence = 0.7` already routes naturally into `OPERATOR_REVIEW` (0.7 ≥ 0.65 ∧ 0.7 < 0.85), so pre-T1 LLM-extracted rows continue to roll into the headline grand total instead of silently dropping out. The explicit `None` case in `band_for_confidence` is a safety net for the small set of code paths that pass through unset confidences (CostLine constructed without an explicit confidence inherits the field's `0.7` default too).
- **Grand-total semantics.** `Estimate.grand_total` is now an alias for the new `grand_total_with_review` (AUTO + REVIEW subtotal + markups). The existing `subtotal` property moved in lock-step (it now means "headline subtotal" = AUTO + REVIEW), so the pre-T6 compounding formula `grand_total ≈ subtotal × (1+cont%) × (1+oh%) × (1+profit%)` keeps holding. A second `grand_total_auto_only` recomputes markups against the AUTO-only subtotal for the conservative "confidence floor" number.
- **Aggregates surfaced.** `Estimate` exposes seven new derived properties: `total_auto_approve`, `total_operator_review`, `total_hand_takeoff` (informational only, NOT in grand total), `grand_total_with_review`, `grand_total_auto_only`, `hand_takeoff_count`, `operator_review_count` (plus `auto_approve_count` for symmetry). `by_division` and `by_cost_category` follow the headline contract — both exclude HAND-banded lines.
- **Excel exporter.** `core/exporter.py` adds a `Band` column on the existing Line Items sheet (showing `AUTO / REVIEW / HAND`), two new sheets — `Operator Review Queue` (light-yellow header tint) and `Hand Takeoff Queue` (amber header tint) — and seven new rows on the Project Summary sheet (Auto-Approve Total, Operator-Review Total, Hand-Takeoff Total, Grand Total Auto-Only, Grand Total Auto+Review, Lines Needing Manual Takeoff, Lines Needing Operator Review). Both queue sheets always exist, even when empty, with a friendly empty-state note in A2 so downstream tabs / scripts can rely on the worksheet existing.
- **PDF exporter.** `core/exporter_pdf.py` adds a small `_render_band_tiles` row under the existing three Labor/Material/Subcontractor tiles. Tile collapse rules per the brief: if `hand_takeoff_count == 0` the HAND tile is hidden; if `operator_review_count == 0` the REVIEW tile is hidden too; if both are zero, the whole band-row is omitted (clean output on a well-classified project). A short greyscale subscript hangs under the headline grand-total tile: `"of which $X auto-approved, $Y pending review, N lines need manual takeoff"`.
- **Streamlit UI.** `app.py` Estimate tab gains a YELLOW warning banner at the top when `hand_takeoff_count > 0`, a 3-column AUTO / REVIEW / HAND breakdown row showing line counts + totals, a side-by-side "Grand Total (Auto + Review)" vs. "Grand Total (Auto-Only)" pair, and a "Review Queues" expander containing two tables — Operator Review (0.65–0.84) and Hand Takeoff (< 0.65 + suppressed). The expander auto-opens when the hand-takeoff queue is non-empty so the estimator can't miss the worklist.
- **JSON exporter.** `export_estimate_json` now surfaces `grand_total_with_review`, `grand_total_auto_only`, `total_auto_approve`, `total_operator_review`, `total_hand_takeoff`, and the three band counts alongside the legacy `grand_total` key, plus each serialised `CostLine` carries its `cost_band` string for downstream consumers.

**Tests:**
- 44 new tests in `tests/test_phase_t6_confidence_bands.py` — threshold edges (0.85 / 0.65 / 0.6499 / 0.8499 / 0.0 / 1.0 / None), suppression-always-wins parameterisation, schema round-trip via `model_dump` / `model_validate`, empty / all-AUTO / all-HAND aggregate invariants, mixed-band totals at 0.92 / 0.78 / 0.55, grand-total alias check, AUTO-only markup compounding, by_division / by_cost_category HAND exclusion, `price_takeoff` band assignment from CSI seed + CWICR + no-match + unit-mismatch paths, the priced_line_items-still-means-non-suppressed backward-compat guard, and the dominant pre-T6 "default 0.7 confidence stays in grand_total" regression test.
- 13 new tests in `tests/test_exporter.py` (new file) — queue-sheet presence (both populated and empty), header-tint hex check on each queue's row 1, `Band` column presence + value set on the Line Items sheet, content isolation (AUTO never leaks into a queue, suppressed lines appear in the HAND queue), seven-row Project Summary T6 block + dollar-value alignment, JSON-export band aggregate round-trip.
- 7 new tests in `tests/test_exporter_pdf.py` extension — `_band_subscript_text` segment toggling on review-zero / hand-zero / both-present, `_render_band_tiles` returning `None` for the AUTO-only clean path, two-tile collapses, three-tile mixed render, and a full `build_quote_pdf` smoke test against a mixed-band estimate.

**Scope:** Cross-cutting. Doesn't improve extraction accuracy, but materially improves the per-bid usefulness of the tool by focusing human time on the rows that need it.

**Effort estimate:** L (5–7 days). Came in inside that envelope — most of the lift was the export-layer surfacing, not the schema work.

**Known gaps / deferred (intentional cut for this slice):**
- **No per-line approve/reject persistence.** The original brief mentioned an `Estimate.review_status` dict keyed by a stable `CostLine.line_id` plus a per-project `corrections.jsonl` log. That correction-feedback loop is deferred — this slice only ships read-only band routing. The next T6 follow-up should add: (a) a stable `CostLine.line_id`, (b) `Estimate.review_status: dict[str, Literal[…]]`, (c) the Streamlit "approve / reject / edit-and-approve" affordance per row, (d) the per-project `uploads/<project>/corrections.jsonl` persistence.
- **No CWICR-similarity-to-band remapping for the 0.55–0.65 gap.** The CWICR matcher threshold (`CWICR_MIN_SIMILARITY`, default 0.55) admits matches that immediately land in `HAND_TAKEOFF` once banded. Two clean options for a follow-up: raise the CWICR threshold to 0.65 to align with the band boundary, or route 0.55–0.65 CWICR matches to a small "weak-match review" sub-queue under HAND.

**Next-slice candidates:**
- **Phase T7 — CSI catalog completeness scoring.** Now genuinely viable — the HAND queue tells us which CSI sections aren't covered by the seed DB / CWICR / specialised schedule extractors. Score each `csi_division` by `(hand_count_by_div / total_count_by_div)` and surface a "coverage gap" tile per division so the estimator sees at a glance which divisions need cost-DB work. Builds directly on the T6 aggregates.
- **Phase T2.6 — panel / equipment / RTU / fixture schedules.** Same T1/T2/T3 dispatch shape (door → window already proven the pattern in T2.5). Different CSI sections (`26 24 16` / `23 00 00` / `22 40 00`), different keyword sets. Would lift Division 22 / 23 / 26 lines straight into AUTO_APPROVE band and shrink the HAND queue on real bids.
- **Per-line approve/reject persistence** (carry-over from this slice — see Known gaps above).

---

### Phase T7 — Price confidence + cost-source tier (catalog completeness)

**Status:** SHIPPED — landed across three commits: `98046ef` (schema-only / backward-compat), `1b179f7` (estimator + exporter + PDF + Streamlit wiring), and this commit (~63 new tests on top of the T6 confidence-band coverage). Suite: 1232 → 1313 passed (1 skipped unchanged). Suite was 975 at end of T6 and is now 1313 — every T6 test still passes unmodified, demonstrating the backward-compat property the schema layer was designed to preserve.

**1-line goal:** Add a second confidence axis to every priced `CostLine` — the price-side confidence (how good was the cost lookup?) — multiplied with the existing qty-side confidence to produce a `combined_confidence` that drives band assignment, plus a six-tier `CostSourceTier` enum that surfaces catalog-completeness independently of the AUTO/REVIEW/HAND axis.

**The 6-tier ladder (`CostSourceTier`):**

| Tier | When | Price confidence |
|---|---|---|
| `EXACT_MATCH` | CWICR similarity ≥ 0.92, or any seed-DB hit | similarity (0.92–1.0); seed-DB hits get the fixed `COST_TIER_SEED_DB_PRICE_CONFIDENCE = 0.95` |
| `CATEGORY_MATCH` | CWICR similarity in [0.75, 0.92) | similarity × 0.85 |
| `INTERPOLATED` | CWICR similarity in [0.50, 0.75) | 0.65 |
| `PARAMETRIC` | CWICR similarity < 0.50 | 0.45 |
| `MANUAL_OVERRIDE` | Operator hand-set the unit cost via Streamlit | 1.0 (operator vouches) |
| `MISSING` | No CWICR hit, no seed-DB hit, OR unit-mismatch suppressed | 0.0 |

Boundaries are inclusive on the upper-tier side (`0.92 → EXACT_MATCH`, `0.75 → CATEGORY_MATCH`, `0.50 → INTERPOLATED`), exactly mirroring the T6 band-threshold convention. Out-of-range similarities are clamped into `[0, 1]` before bucketing so a malformed input can't produce a stray tier.

**Implementation notes (across the three commits):**
- **Schema layer (`98046ef`).** `core/schemas.py` adds `CostSourceTier` (six-value enum), `price_confidence_from_similarity()` helper (single source of truth for the similarity → tier mapping), the `COST_TIER_*` boundary + per-tier-confidence module constants, two new `CostLine` fields (`price_confidence: float = 1.0`, `cost_source_tier: CostSourceTier = EXACT_MATCH`) plus a derived `CostLine.combined_confidence` property (`qty × price`, both clamped into `[0, 1]`, `confidence is None` defensively treated as 0.7), and two new `Estimate` aggregates (`total_by_tier`, `count_by_tier`). Every new field defaults to a value that collapses to T6 semantics (`price_confidence=1.0` makes `combined == qty`; `cost_source_tier=EXACT_MATCH` is the most-positive tier), so every pre-T7 fixture, persisted JSON, and hand-constructed `CostLine` in the test suite produces identical band aggregates as before T7.
- **Wiring layer (`1b179f7`).** `core/estimator.py` adds `_combined_band(qty, price, *, suppressed)` — the band picker that `price_takeoff` now calls with `(qty_confidence, price_confidence)` instead of `(qty_confidence,)`. `_build_cwicr_line` bridges the CWICR similarity into a `(tier, price_confidence)` pair via `price_confidence_from_similarity` for every priced CWICR hit; suppressed unit-mismatch lines are stamped `tier=MISSING + price_confidence=0` on both the CWICR and seed-DB paths. The seed-DB exact-section / keyword-match branch lands in `EXACT_MATCH @ 0.95`. The no-match branch lands in `MISSING @ 0`. `core/exporter.py` adds three new Cost Estimate columns (`Price Confidence`, `Cost Source Tier`, `Combined Confidence`) immediately after the legacy `Confidence` column, a `Cost Source Tier Breakdown` block on the Project Summary sheet (one row per tier with count + $ + % of subtotal), and a `_tier_label()` helper that resolves either the enum form or the post-JSON-roundtrip string form to Title Case (`"Exact Match"`, `"Category Match"`, etc.). `core/exporter_pdf.py` adds `_tier_subscript_text(estimate)` — a second subscript line under the headline grand-total tile reading `"of which X% from exact catalog matches, Y% interpolated, Z% parametric defaults"`, suppressed entirely when there are zero INTERPOLATED + zero PARAMETRIC lines (clean output for high-coverage runs) and gracefully suppressed on the all-MISSING / zero-subtotal edge case to avoid a divide-by-zero placeholder. The EXACT bucket absorbs both `EXACT_MATCH` and `MANUAL_OVERRIDE` dollars (both represent "the operator vouches for the line") and rounds to absorb the percentage residual so the three figures always sum to 100. `app.py` adds a "Cost Source Mix" expander with the per-tier breakdown table + a tier filter on the Line Items table.
- **Tests layer (this commit).** `tests/test_phase_t7_price_confidence.py` (new file, 44 tests) covers the boundary semantics of `price_confidence_from_similarity` at every transition (0.92 / 0.75 / 0.50) and at the `[0, 1]` clamping edges; `CostLine.combined_confidence` invariants including the `qty=None` defensive branch via `_combined_band`; band reassignment via combined confidence (the central T7 contract — high qty + low price now demotes); `total_by_tier` / `count_by_tier` aggregates including the all-MISSING $0 dollar / non-zero count edge case; backward-compat pre-T7 round-trip through `model_dump` / `model_validate`; and `price_takeoff` integration for CWICR-similarity-into-tier, seed-DB-hit, suppressed-unit-mismatch, and full round-trip. `tests/test_estimator_cwicr_integration.py` extension (+7 tests) pins the CWICR similarity → tier mapping at 0.95 / 0.80 / 0.60 + seed-DB + unit-mismatch + the both-axes-populated invariant + the combined-not-qty-alone band assertion. `tests/test_exporter.py` extension (+7 tests) pins the three new column ordering, Title-Case tier strings, the Project Summary breakdown block presence + per-tier count/dollar/percent values, the all-EXACT and all-MISSING edge cases, and the JSON export tier round-trip. `tests/test_exporter_pdf.py` extension (+5 tests) pins `_tier_subscript_text` — surfaces on mixed estimates with the brief's exact phrasing, suppressed on all-EXACT, percentages sum to 100 (±1 rounding), and the all-MISSING / zero-subtotal graceful suppression.

**Boundary edge cases observed during testing:**
- `0.92 / 0.75 / 0.50` boundaries are all inclusive on the upper-tier side, matching the T6 band convention. No surprises.
- The all-MISSING case (every line suppressed → `subtotal == 0`) correctly suppresses the PDF tier subscript via the `denom <= 0` guard in `_tier_subscript_text`. The Excel breakdown block still emits with the MISSING row showing `count=N, total=$0, %=0` so downstream parsers don't trip.
- The pure all-EXACT case correctly suppresses the PDF subscript (clean output) — the `INTERPOLATED + PARAMETRIC == 0` guard fires before the divide.
- The CWICR similarity 0.55 (the default `CWICR_MIN_SIMILARITY`) lands in `INTERPOLATED @ price_conf=0.65`, which combined with the schema-default qty 0.7 produces 0.455 → `HAND_TAKEOFF`. So a barely-above-threshold CWICR hit on a default-confidence takeoff bands into HAND post-T7 — this is the intended behaviour (the brief calls out the 0.55–0.65 CWICR-similarity gap as a future T6.1 sub-queue candidate).

**Backward-compat guarantee preserved.** The full T6 test file (`tests/test_phase_t6_confidence_bands.py`, 44 tests) passes unmodified post-T7 because every new field defaults so the existing band math is unchanged when the price-side axis isn't explicitly set. Pre-T7 persisted JSON validates cleanly into a T7 `CostLine` because both new fields have sensible defaults. The `grand_total` / `subtotal` / `priced_line_items` / `headline_line_items` semantics are all unchanged.

**Tests:**
- 44 new tests in `tests/test_phase_t7_price_confidence.py` (new file).
- 7 new tests appended to `tests/test_estimator_cwicr_integration.py`.
- 7 new tests appended to `tests/test_exporter.py`.
- 5 new tests appended to `tests/test_exporter_pdf.py`.
- All 1232 pre-existing tests remain green; full suite is now `1313 passed, 1 skipped`.

**Scope:** Cross-cutting. Doesn't improve extraction accuracy directly; it surfaces "how much of this estimate came from a real catalog match vs. a parametric default" so the estimator can prioritise where to invest cost-database curation time. Pairs naturally with the T6 HAND queue which already tells us which CSI divisions need cost-DB work.

**Effort estimate:** L (5–7 days). Came in inside that envelope across three sequential commits — the schema-only commit took the most thought (preserving backward compat), the wiring commit was the most code (estimator + 3 export surfaces + Streamlit), and the tests commit was the biggest reach for boundary coverage (~63 tests).

**Known gaps / deferred (intentional cut for this slice):**
- **No persisted operator override of `cost_source_tier`.** The `MANUAL_OVERRIDE` enum value exists in the schema but isn't yet emitted by `app.py` when the operator hand-edits a unit cost via the Streamlit "Recalculate totals" affordance. Wiring that round-trip + persisting the override across reruns is a small Phase T6.1 follow-up.
- **CWICR-similarity threshold misalignment.** `CWICR_MIN_SIMILARITY` defaults to 0.55, which sits in the `INTERPOLATED` (0.50–0.75) tier. Any CWICR hit at the threshold lands in `HAND_TAKEOFF` once combined with a default-0.7 qty confidence. Two clean follow-ups: raise the threshold to 0.65 (aligns with the T6 band boundary), or route 0.55–0.65 CWICR matches into a `category_review` micro-queue under HAND. Same gap the T6 SHIPPED block called out — now the data is there to actually measure which option is right.

**Recommended next slice:**
- **Phase T6.1 — Confidence-propagation cleanup** (per Worker W's prior report). The CWICR-similarity-to-band-threshold misalignment above is the highest-leverage T6/T7 follow-up. Would also wire `MANUAL_OVERRIDE` end-to-end so the Streamlit "Recalculate totals" round-trip preserves operator-vouched price confidence.
- **Phase T8 — Sub-quote integration.** Pull bid-package alternates / unit prices into `CostLine`s as `cost_source_tier=MANUAL_OVERRIDE` rows so the proposal builder reflects sub-quoted dollars at full price-confidence. Builds on the `MANUAL_OVERRIDE` enum value shipped here.
- **Phase T9 — Alternates / unit-prices first-class.** Currently `BidPackage.alternates` and `BidPackage.unit_prices` only surface in the Excel + PDF exports as supplementary tables. Promoting them into `Estimate.alternates` + `Estimate.unit_prices` with their own confidence axis would close the loop on the bid-package side.

---

### Pricing data pipeline (Tier 1 shipped)

Separate from the takeoff phases above, the **pricing-data layer** is what produces the unit costs each `TakeoffItem` gets multiplied by. BPC has no internal cost / sub / supplier data, so the pipeline is built around free external public sources.

**Tier 1 — shipped (this commit).** Five source adapters under `core/pricing/sources/`:

- **BLS PPI** (15 curated commodity series — wood / plywood / gypsum / steel / copper wire / diesel / ready-mix / asphalt / paint / PVC / fab steel / plumbing fittings).
- **BLS OEWS** (10 SOC construction trades × 6 TX metros = 60 wage series).
- **FRED** (8 series — WTI crude, construction inputs PPI, national construction earnings, industrial commodities PPI, TX CPI, construction loan rate, Case-Shiller, sand & gravel PPI).
- **EIA** (weekly retail diesel + regular gas, PADD3 / Gulf Coast).
- **Davis-Bacon** (SAM.gov WD lookup for any state + county + project type).

Plus:

- `core/pricing/snapshots.py` — file-system snapshot persistence (`config/pricing_snapshots/<source>/<series>/<period>.json`).
- `core/pricing/escalation.py` — CSI-aware escalation engine. Maps `cost_database.json` entries to PPI series and writes a new escalated cost DB.
- `scripts/refresh_pricing.py` — CLI refresh runner (gracefully skips sources with missing API keys).
- `firm/playbooks/pricing-data-sources.md` — full operator-facing playbook.
- `firm/compliance/material-suppliers.md` — registry skeleton for the eventual internal-supplier track.

**Tier 1 Phase B — partial.** GSA Schedule adapter ships as a parser (offline-tested on synthetic CSV); auto-download from upstream is TODO.

**Tier 1 Phase B — TX prevailing-wage centralized auto-download: DEPRECATED.** The earlier "TWC per-county WD auto-downloader" entry assumed a centralized TWC source that does not exist. Under **Tex. Gov't Code Ch. 2258**, each TX procuring agency sets and publishes its own prevailing-wage schedule on a **per-project** basis as part of every solicitation — there is no central TWC repository analogous to SAM.gov's federal Davis-Bacon WD library. The per-project parser in `core/pricing/sources/tx_prevailing_wage.py` is the right tool for its real use case (parsing the WD PDF attached to each TX state-agency solicitation). See `firm/playbooks/pricing-data-sources.md` → "Structural Note — Texas Prevailing Wage" for the full rationale.

**Future enhancement — per-agency TX WD harvester.** Rather than a (non-existent) central feed, a future harvester would scrape active-solicitation pages of major TX procuring agencies — **TxDOT, TFC, TBPC, TWDB, the UT / Texas A&M / Texas Tech / UH university systems, large municipalities (Houston, Dallas, San Antonio, Austin, Fort Worth), large counties, TDCJ, HHSC** — and extract the WD PDFs they attach. A placeholder module exists at `core/pricing/sources/tx_agency_wd.py` to make the future shape explicit; **not implemented in current scope.**

**Tier 1 Phase C — partial.** The three major U.S. construction cost indexes — **ENR 20-City CCI**, **AGC PPI-based CCI**, and **Turner Building Cost Index** — ship as full adapters in this slice (`core/pricing/sources/enr_cci.py`, `agc_cci.py`, `turner_cci.py`). Each scrapes its publisher's free public landing page, persists the latest headline index value + reporting period to `config/pricing_snapshots/<adapter>/national*/`, and complements (not replaces) the per-CSI BLS PPI integration as a macro escalator. Per-adapter access posture is documented in `firm/playbooks/pricing-data-sources.md` → "Construction Cost Index macro escalators" — headline-only on the free tier, full historical series on each publisher require a subscription / per-quarter PDF parsing that is left as a follow-up slice. The remaining Phase C entries — **TX SmartBuy / ESBD**, **HD Pro / Lowe's catalog**, **NAHB Cost of Constructing a Home** — continue as importable stubs with documented license + ToS posture.

**Phase C CCI access-posture summary (verified 2026-05-28):**
- **ENR `/economics`** — public landing page; headline 20-city CCI parsed by regex anchor. Full history paywalled.
- **AGC `/learn/construction-data`** — public landing page; PPI-based headline parsed by anchor. Construction Inflation Alert PDF parser is future work.
- **Turner `/cost-index`** — public landing page; latest quarterly TBCI parsed by anchor. Per-quarter archive (back to 2006) is future work.
- Each adapter degrades gracefully on a page-layout change or 4xx / 5xx response: `fetch()` returns `[]` with a logged warning rather than crashing the refresh runner.
- The CCI adapters are NOT wired into the default `scripts/refresh_pricing.py --sources` list because HTML scraping is more fragile than the Phase A / B JSON APIs. Opt in with `--sources enr_cci,agc_cci,turner_cci` or `--phase c`.
- Wiring the CCI signal into `core/pricing/escalation.py` (uniform macro multiplier on top of per-CSI BLS PPI) is deferred — the engine does not yet expose a 5-LOC seam for the blend, per the brief's constraint on `escalation.py` modifications.

**Tier 2 — deferred.** RSMeans / Gordian commercial cost DB. Decision gated on Tier 1 calibration data demonstrating a measurable gap. See Section 5 (Build / Buy / Partner) above.

**Tier 3 — long-horizon.** BPC internal cost DB + supplier discount tracking. Started when BPC has > 12 months of internal cost capture flowing through committed supplier accounts. See `firm/compliance/material-suppliers.md`.

---

### Phase T9 — (Backlog) OCR for scanned-drawing recovery

**1-line goal:** Restore deterministic extraction on PDFs where the vector text layer has been flattened, by adding a `paddleocr` or `tesseract` OCR pass to `drawing_prepass`.

**Deliverables (sketch):**
- New `core/extraction/ocr.py` wrapping `paddleocr.PaddleOCR(lang="en", show_log=False)` (preferred over tesseract for its better performance on rotated text in title blocks).
- `prepass_drawing_page` gains a `force_ocr: bool = False` argument plus an auto-detection that triggers OCR when `len(page.get_text("text").strip()) < 100`.
- OCR output feeds the same `_extract_title_block`, `_extract_dimensions`, `_extract_schedules` paths.

**Scope:** Schedules + Counts + Area + Linear on scanned drawings.

**Effort estimate:** L (1–2 weeks), driven by deployment / packaging — paddleocr pulls a large model bundle and adds 200+ MB to the install.

**Note:** OCR is explicitly behind T1–T7 (now all shipped) because the existing real bid sets we get from Texas state procurement portals are vector PDFs, not scans, and the marginal value of OCR on a small minority of inputs doesn't justify the install-weight cost until the rest of the deterministic stack is solid. Renumbered from "Phase T7" → "Phase T9" because the original numbering predated the T7 (price-confidence + cost-source tier) slice that has since shipped; T8 is reserved for the sub-quote integration follow-up called out in the T7 SHIPPED block.

---

## 4. Non-goals — what we will explicitly NOT build

- **Heavy civil, road, bridge, rail.** Different design conventions (plan + profile + cross-section), different unit systems, different cost drivers (stations, cubic-yards of fill at depth). Out of stated user scope.
- **High-rise structural / tall-building.** Steel takeoff for a 40-story building requires per-floor decomposition we don't model; specialized estimating packages (Tekla, RAM) already do this well.
- **Full BIM authoring or modification.** We are a takeoff and estimating tool, not a CAD / BIM platform. We will *ingest* IFC if it's offered (potential future phase), but we will not author or modify.
- **CAD-quality drafting back-out.** When the only source is a low-fidelity PDF, we will not attempt to reconstruct a clean CAD model from it.
- **Live cost-feed from RSMeans / Gordian.** Mentioned in the README "easy adds" list but explicitly punted: the CWICR open dataset (CC-BY-4.0, 55 K rows) plus the seed DB gives us enough coverage for residential and light commercial. A commercial-cost-DB connector requires a paid license per seat and is a sales / procurement decision, not a code decision.
- **Bid-leveling across multiple subs.** Out of scope for this roadmap (mentioned as a future README item but solving the *takeoff* side first is the higher-leverage move).
- **Predictive bid-win modeling.** Not part of takeoff.
- **Live document-set ingestion via API.** Bids arrive as PDFs in an inbox folder today; that workflow is sufficient.

---

## 5. Build / buy / partner analysis

### Build

The core of T1–T6 is straightforward build. The schedule extractor (T1), prompt specialization (T2), dedup (T3), and finish-takeoff walker (T5) are 1–5-day code projects each, on top of dependencies we already vendor (`pymupdf`, `rapidfuzz`, `pydantic`, `scikit-learn`, `sentence-transformers`). T4 is the most novel build but it's still a "use PyMuPDF's `get_drawings()` + a small polygon reconstructor" exercise rather than a research project. Total build budget for T1–T6 is **6–10 weeks of one engineer**.

### Buy

The commercial space worth surveying when (and only when) T1–T5 calibration plateaus:

- **Togal.AI** — vision model trained specifically on construction drawings; emits room polygons, finish takeoffs, count-based items. Subscription model, $300–600 / user / month typical. Would replace most of T4 + T5 if it works on our drawing sets. Real consideration if our polygon reconstruction in T4 doesn't clear the 70% area-accuracy bar.
- **Bluebeam Revu** — desktop, $200–400 / user / year; not an API but has scripted markups and a paid "Revu AI" add-on for measurements. Probably the worst fit (desktop tool, no headless / batch story).
- **STACK** — cloud takeoff platform, $1,800+ / user / year. Has APIs for project + drawing management; underlying takeoff is operator-driven not automated. Wrong category.
- **Hyperestimate / Beam.ai / Trunk.ai** — newer entrants. Pricing and API maturity vary; revisit when commercially relevant.

The decision rule: **buy** only if a vendor moves a specific accuracy band by ≥ 15 percentage points and the per-month cost is < 0.5% of a typical bid value we'd produce with the tool. Today we have no signal that T4 / T5 will fall short — start build, set go / no-go gates, revisit at T4 calibration.

### Partner (open-source ecosystem)

- **PaddleOCR** (Apache-2.0). Best-in-class for English + rotated text. Path-forward for T9.
- **layoutlmv3 / docling** (MIT / Apache). Document layout analysis. Useful for schedule-table detection on PDFs where PyMuPDF `find_tables()` misses (T1 fallback).
- **opencv-python** (Apache-2.0). Symbol detection on rendered plan pages — template-matching for fixture / receptacle / sprinkler-head symbols. Plausible path forward for the symbol-detection gap noted in Section 1.3, but out of scope until T6 ships.
- **GroundingDINO + SAM** (Apache-2.0). Vision-language object detection — could segment doors / fixtures from a rendered plan PNG with no fine-tuning. Compute-heavy (GPU desirable); revisit once T1–T5 establish the deterministic baseline they would augment.
- **ezdxf** (MIT). Read native AutoCAD DXF files. Would be the natural ingest path if the owner ever provides DXFs (see Open Question 1).

---

## 6. Recommended next step

**Start Phase T1 — Specialized schedule extraction.**

Why this phase:
- F3 already detects schedule tables deterministically (`page.find_tables()`); we're not building detection, we're building the typed extractor on top.
- Schedules are the highest-yield-per-effort category in the accuracy table (85–95%, Medium effort). Doors, fixtures, equipment, and panels are typically 60–80% of the count-based line items on a light-commercial bid.
- The codebase already has the right seams: `_build_from_prepass` is the obvious dispatch point, `TakeoffItem` is the right output schema, `_merge_takeoffs` is the right downstream consumer.
- No new runtime dependency. No new prompt to engineer. No new compute cost.
- It's the prerequisite for T3 (dedup needs schedule rows as ground truth), T5 (finish takeoff needs the finish schedule), and provides immediate value even if T2 / T3 / T4 don't ship.

Minimum viable shippable slice:
1. **Door schedules only.** Implement `extract_door_schedule(schedule: Schedule, specs: list[SpecSection]) -> list[TakeoffItem]` in `core/extraction/schedule_extractor.py`.
2. **Hook into `_build_from_prepass`.** When the prepass returns a schedule of kind `"door"`, run the door extractor and emit per-mark TakeoffItems plus an aggregated hardware-set line. Set `confidence = 0.92` on rows that have both `mark` and `type`; `0.80` when only `mark` is present (type inferred from spec cross-ref or defaulted).
3. **8 tests in `tests/test_schedule_extractor.py`.** Synthesized `Schedule` objects covering: standard door schedule, schedule with merged "WIDTH x HEIGHT" column, schedule with rating column, schedule with fire-protection notes, schedule referencing hardware sets HW-1..HW-N, schedule where `type` is null and spec cross-ref fills it, schedule with no spec available (defaults to "Door (type unspecified)"), schedule with > 100 rows for performance.
4. **One end-to-end calibration.** Run the slice against the Carr EFA Project Manual + drawings addendum (already in `inbox/opportunities/attachments/2026-05-21/`). Hand-count doors on the source PDF. Success bar: > 92% accuracy on the door-count, > 85% on the type breakdown (HM vs SC vs ALUM).
5. **Ship behind a feature flag.** `CORE_EXTRACTION_SCHEDULE_TAKEOFF_ENABLED=true` in `.env`, default `false` for one release. Flip to default-true after the calibration is clean.

Why door schedules first (and not finish or fixture):
- Highest single-category dollar value on a typical commercial TI bid (doors + hardware + frames often $30–80K on a $1M bid).
- Most schema-stable across offices (door schedule layout is the most standardized of all the architectural schedules).
- Has a clean spec cross-reference target (CSI 08 11 13, 08 14 16, 08 71 00 are well-defined and rarely conflated).

After the slice ships, fan out to window / finish / fixture / panel / equipment schedules in the same pattern — each is a 4-8 hour addition once the door-schedule pattern is in place.

---

## 7. Open questions for the user

These are the questions whose answers materially shift the roadmap. Five-to-eight, ordered by impact:

1. **Source-file mix.** In a typical month, what fraction of bids arrive as:
   - vector PDFs (text + lines, the happy path),
   - scanned PDFs ("scan of a scan", no text layer),
   - native CAD (`.dwg`, `.dxf`),
   - native BIM (`.ifc`, `.rvt`)?
   This sets the priority of Phase T9 (OCR), and whether an `ezdxf` ingest is worth adding earlier than backlog.

2. **Drawing-set quality.** When you do receive CAD-quality PDFs, how often are they "rasterized vector" (line art is vector but flattened to independent segments) vs "true vector" (clean polylines, layers)? This is the central risk on Phase T4 — `get_drawings()` only helps on the latter.

3. **Quantity provenance.** On a typical bid you submit, roughly what fraction of priced quantities ultimately come from schedules vs measured-off-the-plan? This bounds the maximum value of Phase T4 + T5 (geometric measurement) vs Phase T1 (schedule extraction). If schedules drive 80%+ of dollars, prioritize T1; if measured-off-the-plan drives 50%+, accelerate T4.

4. **Commercial OCR / CV budget.** What's your tolerance for a $300–600 / month per-seat subscription to a vendor (e.g. Togal.AI) if it materially raises Area or Linear accuracy? This is the decision rule for the build / buy gates after Phase T4.

5. **Human-in-the-loop tolerance.** When you review an estimate today, how many minutes per $100K of bid value do you spend reviewing line items? This calibrates the confidence bands in Phase T6 and tells us how aggressive the "auto-approve" threshold should be.

6. **Project type mix.** Of the bids you submitted in the last 12 months: what % were residential, light commercial / TI, K-12, government solicitations (USFWS / state / federal), other? The roadmap is calibrated against your stated USA-residential-plus-commercial scope, but the schedule extractor's per-office variants depend on which design firms you see most often.

7. **Estimator-correction round-trip.** Are you comfortable having your line-item corrections logged to `uploads/<project>/corrections.jsonl` for future reference (and eventually for fine-tuning), or is per-correction logging a confidentiality concern? This shapes Phase T6's persistence story.

8. **Native-file ingest from owners.** If the federal / state procurement portal can hand you `.ifc` or `.dxf` alongside the PDF (some can, some can't), would you prefer the tool to silently prefer the higher-fidelity file, or to keep the PDF as the canonical input for traceability with the bid documents? This shapes whether `ezdxf` / `ifcopenshell` are worth bringing into the dep tree.

---

**End of roadmap.**
