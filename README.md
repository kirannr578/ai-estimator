# Construction Plan Estimator

An AI-powered tool that reads multi-PDF construction plan sets — drawings,
schedules, specifications, **and trade bid packages** — and produces a CSI
MasterFormat estimate plus a project-wide scope matrix, with full traceability
back to the source documents.

Designed for **residential and commercial** projects (light commercial, TI,
single & multi-family, K-12 and similar institutional).

---

## What it does

1. **Ingest** any number of PDFs from a folder or by upload.
2. **Auto-route by document type** (no manual sorting):
   - **Drawing sheets** → split per page, rendered, vision-LLM extraction
   - **Trade bid packages** (Beck-style scope/bid forms) → text-only,
     one LLM call per *whole PDF* (cheap & accurate)
   - **Project manuals / flyers / questionnaires** → quick summary +
     project-info pull
3. **Classify** every drawing sheet automatically (e.g. `A-101 Floor Plan`,
   `S-201 Foundation Plan`, `Door Schedule`).
4. **Extract** structured data with discipline-specific prompts:
   - Floor plans → rooms, areas, finishes, door/window counts
   - Elevations → exterior finishes and openings
   - Structural → footings, columns, beams, slab area
   - MEP → fixture counts, equipment, runs
   - Schedules → parsed door / window / finish / equipment tables
   - Specs → CSI section + key requirements
   - Bid packages → trade scope, inclusions, exclusions, alternates,
     unit prices, referenced drawings & specs
5. **Reconcile** across documents — the same room on a floor plan + finish
   schedule becomes one row; bid packages are merged into a project-level
   **scope matrix** keyed by CSI division.
6. **Detect project info** (name, number, location, GC, bid date) from the
   strongest cross-document signal, flagging template inconsistencies.
7. **Estimate** by applying an editable unit-cost database with overhead,
   profit, contingency, and a regional multiplier.
8. **Export** to Excel (Project Info, Bid Packages, Scope Matrix, Line Items,
   Rooms, Doors, Windows, Sheets, Warnings) and JSON.

---

## Quick start (Windows / PowerShell)

The fastest path is the bundled setup script:

```powershell
PowerShell -ExecutionPolicy Bypass -File .\setup.ps1
```

It detects (or tells you how to install) Python 3.10+, creates `.venv`,
installs all dependencies, and seeds your `.env`.

Then either run the **web UI**:

```powershell
.\.venv\Scripts\Activate.ps1
streamlit run app.py
```

Or run **headless on a folder of PDFs** (no UI, batch-friendly):

```powershell
.\.venv\Scripts\Activate.ps1

# Whole project, every PDF
python analyze.py "C:\path\to\GMP#003-Permit-Set" --recursive --out exports\full

# Cheap dry run: bid packages + small text PDFs only (skip large drawing sets)
python analyze.py "C:\path\to\GMP#003-Permit-Set" --recursive --no-drawings --out exports\dryrun

# Limit to N PDFs while you iterate
python analyze.py "C:\path\to\folder" --limit 5 --out exports\sample
```

Both modes write `estimate.xlsx` + `estimate.json` (and `run_log.txt` for
the CLI). The Streamlit UI also lets you point at a **local folder** in the
sidebar — useful when you have 50+ PDFs and don't want to drag-and-drop.

### Manual setup (if you don't want the script)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env       # then edit .env to add your API key
streamlit run app.py
```

---

## Choosing a model

| Provider  | Default model       | Strengths                                   |
| --------- | ------------------- | ------------------------------------------- |
| Anthropic | `claude-sonnet-4-5` | Best for careful, schema-strict extraction  |
| OpenAI    | `gpt-4o`            | Faster, cheaper, good general vision        |

Set whichever key you have in `.env`. If both are set, Anthropic wins by
default (override via the sidebar in the UI).

---

## Editing the cost database

Unit costs live in `config/cost_database.json`, keyed by CSI section. Every
entry has a `unit_cost`, `unit`, `description` and an optional `notes` field.
Edit the JSON directly or tweak values per-project from the **Costs** tab in
the UI.

A **regional multiplier** in `.env` (or the sidebar) scales every unit cost
(e.g. `1.18` for higher-cost metros, `0.92` for low-cost markets).

---

## Project layout

```
app.py                      Streamlit UI entrypoint
analyze.py                  Headless / CLI runner for batch jobs
setup.ps1                   One-shot Windows setup (Python check, venv, deps)
core/
  schemas.py                Pydantic models (Sheet, Room, BidPackage, Estimate, ...)
  pdf_processor.py          Splits PDFs - drawings -> sheets, text PDFs -> bundles
  llm_client.py             Provider-agnostic LLM (Anthropic + OpenAI)
  sheet_classifier.py       Identify discipline + sheet type for drawings
  extractors.py             Discipline-specific extractors + bid-package extractor
  takeoff.py                Cross-document reconcile + project-info + scope matrix
  estimator.py              Apply costs, OH&P, contingency
  exporter.py               Excel / JSON export
prompts/                    Versioned prompts per extractor
config/
  csi_divisions.json        CSI MasterFormat reference
  cost_database.json        Editable unit costs
```

## Deterministic drawing pre-pass (F3)

Before any vision-LLM call, every drawing page is run through
`core/extraction/drawing_prepass.py`, a pure-PyMuPDF pass that pulls
title-block fields, dimensions, and schedule tables straight out of the
PDF's vector text. The pre-pass computes a confidence score (0..1):

* `confidence ≥ 0.65` — the vision-LLM is **skipped entirely**; the
  `SheetExtraction` is built from the deterministic snapshot.
  `lm_skipped` is set to True so the UI / Excel exports can flag it.
* `confidence < 0.65` — the LLM runs as before, but receives the
  pre-pass result as a "deterministic context" block in the prompt so
  it doesn't re-extract what we already have.

The pre-pass result (`SheetExtraction.prepass`) is always persisted for
downstream debugging, regardless of which path was taken. The Streamlit
**Sheets** tab tags each sheet with ⚡ (prepass-only) or 🤖
(LLM-augmented) and the Excel **Summary** carries a one-line "Prepass
coverage" tile.

## Document types it understands

| Type                 | Detection                                   | Extractor                | LLM cost  |
| -------------------- | ------------------------------------------- | ------------------------ | --------- |
| Drawing sheet        | Default (per-page)                          | Vision, discipline-aware | per page  |
| **Bid package**      | Filename `NN.NN_-_*` or "BID PACKAGE" hits  | Text-only, whole PDF     | 1 call    |
| Project manual       | "GENERAL INSTRUCTIONS", "QUESTIONNAIRE", ...| Text summary, whole PDF  | 1 call    |
| Blank bid form       | Filename / "BLANK BID FORM"                 | Skipped (no LLM)         | 0         |
| `DO_NOT_USE.pdf`     | Filename                                    | Skipped                  | 0         |

This routing is what makes a 50-PDF Beck GMP set affordable to analyse:
the 45 bid packages cost ~45 cheap text calls instead of ~450 vision calls.

---

## How accurate is it?

Treat every output as a **first-pass takeoff** that an estimator should review.
The vision LLM is good at:

- Reading title blocks, sheet numbers, room labels
- Parsing schedules (door, window, finish, equipment)
- Counting fixtures and openings
- Identifying disciplines and routing to the right extractor

It is weaker at:

- Exact dimensions from drawings without callouts (it estimates from scale and
  context, not from vector geometry)
- Hand-drawn or extremely dense / overlapping drawings
- Symbols specific to an unfamiliar office standard

Every line item carries a `confidence` score and links to the sheets it came
from, so reviewers can quickly verify or adjust.

---

## Client-ready quote PDF (F12 + F15)

In addition to the estimator workbook, the app can produce a polished
proposal PDF for clients with payment schedule and signature block.

- **Config:** `config/client_quote.json` holds branding, client info, quote
  meta, payment schedule, and T&Cs. The defaults ship with placeholder
  strings only — fill them in before sending a real quote.
- **Edit in the UI:** the **Client Quote** tab loads the JSON, exposes form
  fields for every section (Company, Client, Quote Meta, Payment Schedule,
  Terms), atomically writes back on **Save configuration**, and produces
  a PDF on **Generate & download PDF**.
- **Payment schedule:** defaults to percentage mode (30/30/30/10
  mobilization → rough-in → finish → retainage). Switch to milestone mode
  for fixed-dollar billing — amounts must add up to the contract total
  (warning surfaced inline).
- **From the CLI:** `python analyze.py <path> --client-pdf --out exports\foo`
  writes `quote.pdf` next to `estimate.xlsx`. Missing config or missing
  `reportlab` are logged to `run_log.txt` rather than crashing the run.
- **Note:** the placeholder company name
  `RK Residential Homes and Commercial LLC` was inferred from a source zip
  filename — change it in the Client Quote tab before issuing a real proposal.

---

## Roadmap (easy adds)

- Vector-geometry takeoff (true polygon area / linework length from PDF
  vectors, not vision)
- Symbol-library training per office standard
- Built-in RSMeans / Gordian connector for live pricing
- Multi-project comparison view
- Bid-leveling export
