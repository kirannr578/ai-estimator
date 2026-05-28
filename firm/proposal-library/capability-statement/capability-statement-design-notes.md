# Capability Statement — Design / Layout Notes

> **How to use this template** — Design specification for the 1-page capability statement at [`capability-statement-1pg.md`](capability-statement-1pg.md). Use these notes when rendering the capability statement in Word, PowerPoint, InDesign, Figma, or any other layout tool. The design objective is **maximum scan-ability in 30 seconds** by a Contracting Officer; secondary objective is brand consistency with the rest of BPC's submission package. Search-and-replace `{{PLACEHOLDER}}` tokens in the body before render.

---

## Page setup

| Spec | Value |
|---|---|
| Page size | US Letter (8.5" × 11") portrait |
| Margins | **0.5" top / bottom / left / right** (tight; the template assumes the full content area is used) |
| Orientation | Portrait |
| Page count | **1** (hard limit; do not bleed onto page 2 — re-tighten content if it does) |
| Output format | PDF/A-2b for federal portal compatibility; embedded fonts; ≤ 2 MB |
| Filename convention | `Blueprint-Constructs-Capability-Statement-{{YYYYMMDD}}.pdf` |

## Brand colors

> Sourced to be visually consistent with the BPC logo and the rest of the submission package. If the firm later defines an authoritative brand-style guide, that guide supersedes these values.

| Color | Hex | Use |
|---|---|---|
| **BPC Navy** | `#1B2A4E` | Primary heading color, tagline, brand wordmark, footer accent |
| **BPC Gold** | `#C9A87A` | Accent for differentiator bullets, divider rules, callout backgrounds |
| **Charcoal** | `#23272F` | Body text |
| **Slate** | `#5A6473` | Sub-headings, table-row alternation |
| **Mist** | `#E9ECF1` | Section-divider hairlines, subtle background fills |
| **White** | `#FFFFFF` | Page background |
| **Footer grey** | `#8A8F99` | Footer text only (8pt) |

## Typography

> If BPC has not curated a font in `firm/assets/fonts/`, use system sans-serif fallbacks; do not embed a font that requires a license BPC does not hold.

| Style | Font | Size | Weight | Color |
|---|---|---|---|---|
| Wordmark "BLUEPRINT CONSTRUCTS" | Inter (or system sans, e.g. Segoe UI / Helvetica Neue) | **18 pt** | Bold | BPC Navy |
| Tagline | Inter | 11 pt | Regular italic | BPC Navy |
| Section headings (H2) — "Core competencies", etc. | Inter | **14 pt** | Bold | BPC Navy |
| Sub-section headings (H3) | Inter | **11 pt** | Bold | Slate |
| Body | Inter | **10–11 pt** (use 10pt only if 11pt overflows the page) | Regular | Charcoal |
| Bullet text | Inter | 10–11 pt | Regular | Charcoal |
| POC block + emphasis | Inter | 10–11 pt | Bold | BPC Navy |
| Footer | Inter | **8 pt** | Regular | Footer grey |

> **Font fallback rule** — if Inter is not available on the rendering machine, fall back to (in order): **Segoe UI** (Windows), **Helvetica Neue** (macOS), **system-ui**, **sans-serif**. Avoid Calibri (associated with Office defaults — visually undifferentiated).

> **Typography discipline** — at most **3 weight variations on the page** (Bold for headings + emphasis, Regular for body, Italic only for tagline). More weight variations look amateur; fewer reads better on print.

## Layout

### Vertical structure (top → bottom)

```
+--------------------------------------------------------------+
|  [Logo 1.0"]   BLUEPRINT CONSTRUCTS                          |  ← Header band
|                Building DFW's institutional + commercial...   |     (≈ 1.0" total height)
+--------------------------------------------------------------+
|                                                              |
|  Corporate identity   |   NAICS + SBA                        |  ← Two-column row 1
|  (UEI / CAGE / EIN /  |   (Primary NAICS / Secondary /       |     (≈ 1.5" height)
|   TX SOS / SAM)       |    SBA size standard)                |
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  Certifications                                              |  ← Single-column row
|  (TX HUB / MBE / SBE — with expiry flags)                    |     (≈ 0.7" height)
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  Core competencies          |   Differentiators              |  ← Two-column row 2
|  (5–8 bullets)              |   (3–5 bullets, gold accent)   |     (≈ 3.0" height)
|                                                              |
+--------------------------------------------------------------+
|                                                              |
|  Past performance (3 representative — 1-line each)           |  ← Single-column row
|                                                              |     (≈ 1.0" height)
+--------------------------------------------------------------+
|                                                              |
|  Point of contact                                            |  ← Single-column row
|  (POC + email + phone + address + website)                   |     (≈ 1.2" height)
|                                                              |
+--------------------------------------------------------------+
|  Footer (8pt grey, single line)                              |  ← Footer band (≈ 0.3")
+--------------------------------------------------------------+
```

### Horizontal structure (within two-column rows)

- Two equal columns split at the page midpoint
- 0.25" gutter between columns
- 1pt BPC Navy hairline rule between columns (optional)
- Column-content alignment: left-aligned text; bullets at 0.15" indent

## Logo

| Asset | Path |
|---|---|
| Raster (PNG) | `firm/assets/bpc-logo.png` |
| Vector source (Adobe Illustrator) | `BPC/Editable source file.ai` (OneDrive per `firm-profile.json → submission_assets.logo_source_ai`) |
| PDF logo | `BPC/BPC Logo.pdf` (OneDrive per `firm-profile.json → submission_assets.logo_pdf`) |

**Placement** — top-left, 1.0" wide, vertically centered with the wordmark + tagline to its right.

**Treatment** — logo on white background; do not place logo on a colored fill that compromises contrast.

## Asset references

| Asset | Path | Use |
|---|---|---|
| BPC logo (PNG) | [`firm/assets/bpc-logo.png`](../../assets/bpc-logo.png) | Header |
| BPC logo (vector) | `BPC/Editable source file.ai` (OneDrive — see `firm/firm-profile.json → submission_assets.logo_source_ai`) | High-resolution print |
| BPC pitch-deck template (PowerPoint) | [`firm/assets/templates/bpc-pitch-deck-template.pptx`](../../assets/templates/bpc-pitch-deck-template.pptx) | Reference for brand consistency |
| BPC business card | `BPC/BPC Business card.pdf` (OneDrive) | Reference for brand consistency |
| Existing capability statement (legacy reference) | `BPC/Blueprint Constructs Capability Statement.pdf` (OneDrive) | Reference for tone and content density |

> **Note** — when curating a fonts directory, place TTF / OTF files at `firm/assets/fonts/` and update this notes file to reference them. Until then, the system-fallback rule applies.

## Tone + content density

- **Tone:** professional, sober, evidence-based. No hyperbole. No words like "world-class", "premier", "industry-leading", "best-in-class" — these are tells of marketing copy that federal evaluators distrust.
- **Density:** every line earns its space. If a sentence does not differentiate BPC or convey hard fact, cut it.
- **Voice:** third-person institutional ("Blueprint Constructs is...", "BPC self-performs..."). Avoid first-person plural ("we") on the capability statement; reserved for cover letters and exec summaries.

## Versioning + revision

- Capability-statement revision date is in the footer (`v{{REVISION_DATE_YYYYMMDD}}`).
- Re-render the capability statement when any of the following change in `firm/firm-profile.json` or `firm/compliance/README.md`:
  - SAM.gov registration expiration date
  - HUB / MBE / SBE certification status
  - Any of the cited 3 past-performance projects (completion date, contract value, status)
  - POC information (email, phone, address)
  - Brand identity (logo, tagline, color palette)
- Keep prior versions in `bids/<slug>/01-overview-or-appendix/` of any submission they were attached to, for audit trail.

## Accessibility (PDF/UA conformance)

If the capability statement will be uploaded to a federal portal that screens for PDF/UA accessibility (some agencies do):

- Tag headings (H1, H2, H3) per the document outline
- Provide alt-text for the BPC logo (`"Blueprint Constructs logo"`)
- Define document language (`en-US`)
- Ensure 4.5:1 minimum color contrast for body text on background
- Avoid relying on color alone to convey meaning (e.g. don't use red-text-only for warnings)

## Print considerations

If the capability statement is also printed (industry day handouts, business-card carriers):

- Print on **80 lb cover stock** (matte) for premium feel; 32 lb bond minimum
- CMYK color values aligned with the hex above (`#1B2A4E` BPC Navy converts to roughly C100 M85 Y30 K35; verify with the print vendor's color management)
- Bleed 0.125" if printing edge-to-edge; otherwise 0.25" margin to printable area
