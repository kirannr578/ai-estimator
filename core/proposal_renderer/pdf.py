"""Build the client-facing PDFs for a single bid workspace.

Produces two artifacts per bid:

1. `<slug>-client-executive-summary.pdf` — 6–12 page brochure-style
   document distilled from the client-facing markdown files: cover +
   project understanding + tech-approach phases + team + 3 past-perf
   highlights + price summary + Q&A/contact.

2. `<slug>-full-proposal.pdf` — 40–60 page styled full-proposal PDF
   that includes every client-facing markdown section verbatim, with
   a designed cover and section dividers.

Both use the `client-proposal.css` design system and run through the
`xhtml2pdf` engine (WeasyPrint preferred per brief, but its native
GTK/Pango libs aren't available on this Windows machine — see commit
message).

Placeholder handling:
* `show_placeholders=False` (default) — `[USER TO FILL …]` markers are
  rewritten to a neutral underline (`__________`) before HTML render so
  the client sees a fillable line, not a red audit callout.
* `show_placeholders=True` — markers are wrapped in
  `<span class="placeholder">` and rendered red, matching the internal
  workbook treatment, for the user's own QA review.
"""

from __future__ import annotations

import html as html_lib
import io
import logging
import re
from datetime import date
from pathlib import Path
from typing import Any

import markdown as md_lib

from .branding import LOGO_PATH
from .common import (
    PLACEHOLDER_PATTERNS,
    Section,
    collapse_whitespace,
    discover_sections,
    downgrade_wide_html_tables,
    find_h1_blocks,
    find_h2_blocks,
    find_section,
    first_paragraph,
    flatten_markdown_tables_to_definition_list,
    list_items,
    neutralize_placeholders_in_section,
    parse_bid_title,
    parse_solicitation_number,
    partition_sections,
    primary_personnel,
)

logger = logging.getLogger(__name__)

CSS_DIR = Path(__file__).with_name("css")
CLIENT_CSS_PATH = CSS_DIR / "client-proposal.css"

MD_EXTENSIONS = ["tables", "fenced_code", "attr_list", "sane_lists"]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_client_pdfs(
    bid_dir: Path,
    out_dir: Path,
    firm_profile: dict[str, Any],
    *,
    show_placeholders: bool = False,
    logo_path: Path | None = None,
) -> dict[str, Path]:
    """Build the executive-summary brochure + the full-proposal PDF for
    a single bid.

    Returns a dict mapping `"executive_summary"` and `"full_proposal"` to
    the resolved output paths. Both files are named
    `<slug>-client-executive-summary.pdf` / `<slug>-full-proposal.pdf`
    and dropped under `out_dir`.
    """
    bid_dir = Path(bid_dir).resolve()
    out_dir = Path(out_dir).resolve()
    proposal_dir = bid_dir / "proposal"
    if not proposal_dir.is_dir():
        raise FileNotFoundError(f"no proposal directory at {proposal_dir}")

    sections = discover_sections(proposal_dir)
    if not sections:
        raise FileNotFoundError(f"no proposal sections found in {proposal_dir}")

    bid_slug = bid_dir.name
    bid_title = parse_bid_title(proposal_dir, bid_slug)
    solicitation = parse_solicitation_number(bid_slug)

    client_sections, _internal_sections = partition_sections(sections)

    # Apply placeholder neutralization before rendering.
    rendered_sections = [
        neutralize_placeholders_in_section(s, show_placeholders=show_placeholders)
        for s in client_sections
    ]

    out_dir.mkdir(parents=True, exist_ok=True)
    logo = logo_path or LOGO_PATH

    full_path = out_dir / f"{bid_slug}-full-proposal.pdf"
    _render_full_proposal(
        out_path=full_path,
        bid_slug=bid_slug,
        bid_title=bid_title,
        solicitation=solicitation,
        sections=rendered_sections,
        firm_profile=firm_profile,
        logo_path=logo,
        show_placeholders=show_placeholders,
    )

    summary_path = out_dir / f"{bid_slug}-client-executive-summary.pdf"
    _render_executive_summary(
        out_path=summary_path,
        bid_slug=bid_slug,
        bid_title=bid_title,
        solicitation=solicitation,
        sections=rendered_sections,
        firm_profile=firm_profile,
        logo_path=logo,
        show_placeholders=show_placeholders,
    )

    return {"executive_summary": summary_path, "full_proposal": full_path}


# Backward-compatible single-PDF entrypoint kept for any external caller
# still importing `build_proposal_pdf` (the old name). Behavior maps to
# producing only the full proposal at the requested path.
def build_proposal_pdf(
    bid_dir: Path,
    out_path: Path,
    firm_profile: dict[str, Any],
    *,
    show_placeholders: bool = False,
    logo_path: Path | None = None,
) -> Path:
    """Render the full client-facing proposal PDF to `out_path`.

    Compatibility shim for the pre-tiering API. New code should call
    `build_client_pdfs` instead, which produces both the executive
    summary and the full proposal.
    """
    bid_dir = Path(bid_dir).resolve()
    out_path = Path(out_path).resolve()
    proposal_dir = bid_dir / "proposal"
    if not proposal_dir.is_dir():
        raise FileNotFoundError(f"no proposal directory at {proposal_dir}")
    sections = discover_sections(proposal_dir)
    if not sections:
        raise FileNotFoundError(f"no proposal sections found in {proposal_dir}")

    bid_slug = bid_dir.name
    bid_title = parse_bid_title(proposal_dir, bid_slug)
    solicitation = parse_solicitation_number(bid_slug)
    client_sections, _ = partition_sections(sections)
    rendered_sections = [
        neutralize_placeholders_in_section(s, show_placeholders=show_placeholders)
        for s in client_sections
    ]

    out_path.parent.mkdir(parents=True, exist_ok=True)
    _render_full_proposal(
        out_path=out_path,
        bid_slug=bid_slug,
        bid_title=bid_title,
        solicitation=solicitation,
        sections=rendered_sections,
        firm_profile=firm_profile,
        logo_path=logo_path or LOGO_PATH,
        show_placeholders=show_placeholders,
    )
    return out_path


# ---------------------------------------------------------------------------
# HTML builders
# ---------------------------------------------------------------------------


def _render_full_proposal(
    *,
    out_path: Path,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
    logo_path: Path,
    show_placeholders: bool,
) -> None:
    css = CLIENT_CSS_PATH.read_text(encoding="utf-8")

    cover_html = _render_cover(
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        bid_slug=bid_slug,
        document_tier="Full proposal",
    )
    toc_html = _render_toc(sections)

    def _build_html(*, flatten_tables: bool) -> str:
        body_chunks: list[str] = []
        for section in sections:
            body_chunks.append(
                _render_section_with_divider(section, flatten_tables=flatten_tables)
            )
        body_html = "\n".join(body_chunks)

        header_footer = _render_header_footer(bid_slug=bid_slug, bid_title=bid_title)

        return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>{html_lib.escape(bid_title)} — Full proposal</title>
<style>{css}</style>
</head>
<body>
{header_footer}
{cover_html}
{toc_html}
{body_html}
</body>
</html>
"""

    primary_html = _build_html(flatten_tables=False)
    fallback_html = _build_html(flatten_tables=True)
    _xhtml2pdf_render_with_fallback(
        primary_html,
        fallback_html,
        out_path,
        label=f"{bid_slug} / Full proposal ({out_path.name})",
    )


def _render_executive_summary(
    *,
    out_path: Path,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
    logo_path: Path,
    show_placeholders: bool,
) -> None:
    """Render a 6–12 page brochure distilled from the client-facing
    sections. Each brochure section is built from a small, hand-curated
    subset of the source markdown so it stays brief on purpose."""
    css = CLIENT_CSS_PATH.read_text(encoding="utf-8")

    cover_html = _render_cover(
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        bid_slug=bid_slug,
        document_tier="Executive summary",
    )

    pages = [
        _brochure_project_understanding(sections, firm_profile, bid_title),
        _brochure_technical_approach(sections),
        _brochure_team(sections, firm_profile),
        _brochure_past_performance(sections, firm_profile, bid_slug),
        _brochure_price_summary(sections),
        _brochure_qa(firm_profile, bid_slug),
    ]
    body_html = "\n".join(p for p in pages if p)

    header_footer = _render_header_footer(bid_slug=bid_slug, bid_title=bid_title)

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>{html_lib.escape(bid_title)} — Executive summary</title>
<style>{css}</style>
</head>
<body>
{header_footer}
{cover_html}
{body_html}
</body>
</html>
"""
    # Executive-summary brochures hand-craft small fixed-width tables —
    # they don't go through `_markdown_to_html`. The safety-net fallback
    # is identical to the primary; this still gives us a clean
    # `RuntimeError` (vs an opaque xhtml2pdf trace) with the bid slug if
    # any unexpected layout failure happens here.
    _xhtml2pdf_render_with_fallback(
        html,
        html,
        out_path,
        label=f"{bid_slug} / Executive summary ({out_path.name})",
    )


def _xhtml2pdf_render(html: str, out_path: Path) -> None:
    """Render `html` to a PDF at `out_path`. Raises on error.

    This is the bare engine call kept for callers that build a single
    HTML document and don't need the wide-table safety net. For the
    full / executive-summary builders (which can hit
    `PmlTable` negative-width crashes on wide tables), prefer
    :func:`_xhtml2pdf_render_with_fallback`.
    """
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from xhtml2pdf import pisa

    with out_path.open("wb") as fh:
        result = pisa.CreatePDF(
            io.StringIO(html),
            dest=fh,
            encoding="utf-8",
        )
    if result.err:
        raise RuntimeError(
            f"xhtml2pdf reported {result.err} errors rendering {out_path}"
        )


def _xhtml2pdf_attempt(html: str, out_path: Path) -> str | None:
    """Single attempt — returns an error string on failure, None on success."""
    out_path.parent.mkdir(parents=True, exist_ok=True)
    from xhtml2pdf import pisa

    try:
        with out_path.open("wb") as fh:
            result = pisa.CreatePDF(
                io.StringIO(html),
                dest=fh,
                encoding="utf-8",
            )
    except Exception as exc:
        return f"{type(exc).__name__}: {exc}"
    if result.err:
        return f"xhtml2pdf reported {result.err} errors"
    return None


def _xhtml2pdf_render_with_fallback(
    primary_html: str,
    fallback_html: str,
    out_path: Path,
    *,
    label: str,
) -> str:
    """Render `primary_html` to a PDF at `out_path`. If the primary
    render fails (e.g. `PmlTable` negative-width on a wide table),
    log a warning and re-attempt with `fallback_html` — which is
    expected to be the same content with every wide table flattened
    to a definition-list rendering so xhtml2pdf has no table-layout
    work to do.

    Returns `"primary"` on first-attempt success, `"fallback"` on
    safety-net success. Raises `RuntimeError` only if both renderings
    fail (no PDF is produced in that case).
    """
    err = _xhtml2pdf_attempt(primary_html, out_path)
    if err is None:
        return "primary"
    logger.warning(
        "wide-table safety-net engaged for %s: primary xhtml2pdf render "
        "failed (%s); retrying with markdown tables flattened to "
        "definition-list form.",
        label,
        err,
    )
    err2 = _xhtml2pdf_attempt(fallback_html, out_path)
    if err2 is None:
        return "fallback"
    raise RuntimeError(
        f"both primary and fallback renders failed for {label}: "
        f"primary={err!r}; fallback={err2!r}"
    )


# ---------------------------------------------------------------------------
# Cover + header/footer + section dividers
# ---------------------------------------------------------------------------


def _render_cover(
    *,
    bid_title: str,
    solicitation: str,
    firm_profile: dict[str, Any],
    bid_slug: str,
    document_tier: str,
) -> str:
    legal = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    uei = firm_profile.get("uei", "")
    cage = firm_profile.get("cage", "")
    person = primary_personnel(firm_profile)
    today = date.today().isoformat()

    # xhtml2pdf renders block-level backgrounds as separate per-block
    # rectangles, which leaves white gaps between sibling divs that share
    # a parent bg. To get a continuous navy cover panel, wrap content in
    # a single table cell with the navy background applied to the cell
    # itself. The cell sits inside the standard 6.8in × 9.3in body frame
    # (no full-bleed) — the surrounding 0.85in white margin frames the
    # navy panel cleanly and matches typical brochure covers.
    return f"""
<div class="cover-page">
  <table class="cover-table" style="width:6.8in; border-collapse:collapse;">
    <tr>
      <td class="cover-cell" style="background-color:#0B2545; color:#FFFFFF; padding:0.55in 0.55in 0.5in 0.55in; height:9.2in; vertical-align:top;">
        <p class="cover-eyebrow">BLUE PRINT CONSTRUCTS</p>
        <p class="cover-rule-row">&nbsp;</p>
        <p class="cover-bid-title">{html_lib.escape(bid_title)}</p>
        <p class="cover-solicitation">Solicitation: {html_lib.escape(solicitation or "—")}</p>
        <p class="cover-document-tier">{html_lib.escape(document_tier)}</p>
        <p class="cover-prepared-by-label">PREPARED BY</p>
        <p class="cover-firm-name">{html_lib.escape(dba or legal)}</p>
        <p class="cover-firm-meta">{html_lib.escape(legal)}</p>
        <p class="cover-firm-meta">UEI {html_lib.escape(uei)} &nbsp; · &nbsp; CAGE {html_lib.escape(cage)} &nbsp; · &nbsp; Submission date __________</p>
        <p class="cover-signer">{html_lib.escape(person.get('name', ''))}</p>
        <p class="cover-firm-meta">{html_lib.escape(person.get('title', ''))}</p>
        <p class="cover-firm-meta">{html_lib.escape(person.get('email', ''))} &nbsp; · &nbsp; {html_lib.escape(person.get('phone', ''))}</p>
        <p class="cover-document-stamp">Document prepared {html_lib.escape(today)} &nbsp; · &nbsp; bid-slug: {html_lib.escape(bid_slug)}</p>
      </td>
    </tr>
  </table>
</div>
"""


def _render_header_footer(*, bid_slug: str, bid_title: str) -> str:
    safe_slug = html_lib.escape(bid_slug)
    safe_title = html_lib.escape(_truncate(bid_title, 60))
    return f"""
<div id="header_content">
  <table class="header-row" style="border:0; width:100%; margin:0;">
    <tr style="border:0;">
      <td class="left" style="border:0; padding:0;">BLUE PRINT CONSTRUCTS</td>
      <td class="right" style="border:0; padding:0;">{safe_title}</td>
    </tr>
  </table>
</div>
<div id="footer_content">
  <table class="footer-row" style="border:0; width:100%; margin:0;">
    <tr style="border:0;">
      <td class="left" style="border:0; padding:0;">{safe_slug}</td>
      <td class="right" style="border:0; padding:0;">Page <pdf:pagenumber/> / <pdf:pagecount/></td>
    </tr>
  </table>
</div>
"""


def _render_toc(sections: list[Section]) -> str:
    rows: list[str] = []
    for section in sections:
        prefix = f"{section.prefix:02d}" if section.prefix is not None else "—"
        title = html_lib.escape(section.title)
        rows.append(
            f'<tr class="toc-row">'
            f'<td class="toc-num">{prefix}</td>'
            f'<td class="toc-title">{title}</td>'
            f'</tr>'
        )

    return f"""
<div class="toc">
  <h1>Table of Contents</h1>
  <table style="width:100%; border:0;">
    {"".join(rows)}
  </table>
</div>
"""


def _render_section_with_divider(section: Section, *, flatten_tables: bool = False) -> str:
    """Full proposal section: a navy section-divider page followed by
    the rendered markdown body.

    Same trick as the cover page — render the divider inside a single
    table cell with the navy background applied to the cell, since
    xhtml2pdf treats sibling-div backgrounds as discrete rectangles
    that leave white gaps between block children.
    """
    prefix = f"{section.prefix:02d}" if section.prefix is not None else "—"
    safe_title = html_lib.escape(section.title)
    safe_prefix = html_lib.escape(prefix)

    divider_html = f"""
<div class="section-divider">
  <table class="section-divider-table" style="width:6.8in; border-collapse:collapse;">
    <tr>
      <td class="section-divider-cell" style="background-color:#0B2545; color:#FFFFFF; padding:2.0in 0.55in 2.0in 0.55in; height:9.2in; vertical-align:top;">
        <p class="section-divider-eyebrow">SECTION {safe_prefix}</p>
        <p class="section-divider-num">{safe_prefix}</p>
        <p class="section-divider-rule-row">&nbsp;</p>
        <p class="section-divider-title">{safe_title}</p>
      </td>
    </tr>
  </table>
</div>
"""
    body_html = _markdown_to_html(section.body, flatten_tables=flatten_tables)
    return divider_html + f'<div class="section">{body_html}</div>'


def _markdown_to_html(body: str, *, flatten_tables: bool = False) -> str:
    """Render a markdown body to HTML, with wide-table hardening.

    `flatten_tables=False` (default): runs the normal Markdown→HTML
    pipeline, then wraps any rendered `<table>` that exceeds the
    wide-table thresholds in a compact-font `<div>` so xhtml2pdf has
    enough headroom to layout every column.

    `flatten_tables=True` (safety-net): rewrites every Markdown table
    block in the source as a flat definition-list (`**Header:** value`
    paragraphs) BEFORE the Markdown→HTML pass, so no `<table>` element
    reaches xhtml2pdf at all. Used by
    `_xhtml2pdf_render_with_fallback` after a primary render crash.
    """
    if flatten_tables:
        body = flatten_markdown_tables_to_definition_list(body, always=True)
    raw_html = md_lib.markdown(body, extensions=MD_EXTENSIONS, output_format="html5")
    raw_html = _highlight_placeholders_in_html(raw_html)
    raw_html = _shade_table_rows(raw_html)
    raw_html = downgrade_wide_html_tables(raw_html)
    return raw_html


# ---------------------------------------------------------------------------
# Executive-summary brochure builders — derive briefer content per page
# ---------------------------------------------------------------------------


def _brochure_project_understanding(
    sections: list[Section],
    firm_profile: dict[str, Any],
    bid_title: str,
) -> str:
    src = (
        find_section(sections, 1, slug_contains="executive-summary")
        or find_section(sections, 2, slug_contains="volume-II")
        or find_section(sections, 2, slug_contains="technical-acceptability")
    )
    paragraphs: list[str] = []
    if src is not None:
        # Pull the first 2-3 narrative paragraphs of the file (skipping
        # blockquote metadata banners and tables).
        seen_blocks = 0
        for h2_title, body in find_h2_blocks(src.body):
            tl = h2_title.lower()
            if any(k in tl for k in (
                "to ", "from", "date", "summary of price", "addenda",
                "signature",
            )):
                continue
            if any(k in tl for k in (
                "understanding", "intent", "scope", "overview", "approach",
                "executive summary",
            )):
                first = first_paragraph(body)
                if first and len(first) > 60:
                    paragraphs.append(_truncate(first, 600))
                    seen_blocks += 1
                if seen_blocks >= 2:
                    break
        if not paragraphs:
            first = first_paragraph(src.body)
            if first:
                paragraphs.append(_truncate(first, 700))

    if not paragraphs:
        paragraphs = [
            f"Blue Print Constructs is pleased to submit this proposal for "
            f"{html_lib.escape(bid_title)}."
        ]

    body_chunks = [
        f'<p>{html_lib.escape(p)}</p>' for p in paragraphs
    ]
    callout = (
        '<div class="brochure-callout">'
        'Blue Print Constructs delivers institutional and federal renovation '
        'work with a right-sized GC posture — direct principal involvement, '
        'self-perform breadth across finishes and remodel trades, and a HUB / '
        'MBE / SBE compliance posture aligned to Texas-state and federal '
        'set-aside scoring.'
        '</div>'
    )
    return f"""
<div class="brochure-section">
  <h1>Project understanding</h1>
  {''.join(body_chunks)}
  {callout}
</div>
"""


def _brochure_technical_approach(sections: list[Section]) -> str:
    src = (
        find_section(sections, 2, slug_contains="technical-approach")
        or find_section(sections, 2, slug_contains="volume-II")
        or find_section(sections, 2, slug_contains="technical-acceptability")
    )
    rows: list[str] = []
    if src is not None:
        for h2_title, body in find_h2_blocks(src.body):
            label = h2_title.split("—", 1)[0].strip()
            label = re.sub(r"^\d+\.?\s*", "", label).strip(":")
            if not label or len(label) < 3:
                continue
            tl = label.lower()
            if any(skip in tl for skip in (
                "appendix", "table of", "acronym", "reference"
            )):
                continue
            first = first_paragraph(body)
            summary = _truncate(first, 240) if first else ""
            rows.append(
                f'<tr><td style="width:1.6in; vertical-align:top;"><strong>{html_lib.escape(label)}</strong></td>'
                f'<td>{html_lib.escape(summary)}</td></tr>'
            )
            if len(rows) >= 7:
                break
    if not rows:
        rows = [
            '<tr><td colspan="2"><em>Technical-approach phases not detected '
            'in source markdown — see full proposal for narrative.</em></td></tr>'
        ]

    return f"""
<div class="brochure-section">
  <h1>Technical approach — phase overview</h1>
  <p>The execution plan is organized as a sequence of disciplined phases.
  Each phase has named deliverables, gated milestones, and explicit owner
  coordination touchpoints.</p>
  <table>
    <tr><th style="width:1.6in;">Phase</th><th>Summary</th></tr>
    {''.join(rows)}
  </table>
</div>
"""


def _brochure_team(
    sections: list[Section],
    firm_profile: dict[str, Any],
) -> str:
    src = find_section(sections, 3, slug_contains="project-team")
    rows: list[tuple[str, str]] = []
    if src is not None:
        for h2_title, body in find_h2_blocks(src.body):
            tl = h2_title.lower()
            if "key personnel" not in tl and "role" not in tl:
                continue
            role = re.sub(
                r"^[A-Z]\.\s*Key personnel\s*[—-]\s*", "", h2_title
            ).strip()
            role = re.sub(r"^Role\s+\d+\s*[—-]\s*", "", role).strip()
            name = ""
            m = re.search(r"\|\s*Name\s*\|\s*([^|]+?)\s*\|", body, re.IGNORECASE)
            if m:
                name = m.group(1).strip().strip("`")
            if not name or "USER TO FILL" in name.upper() or name.startswith("____"):
                # Neutralized placeholder or blank — show a fillable line.
                name = "____________________"
            rows.append((role, name))
            if len(rows) >= 6:
                break

    # Always seed the roster with Rocky if no rows derived from md.
    person = primary_personnel(firm_profile)
    if not rows and person.get("name"):
        rows.append((person.get("title", "Founder & Managing Director"), person["name"]))

    cards: list[str] = []
    for role, name in rows:
        cards.append(
            f'<div class="team-card">'
            f'<div class="team-role">{html_lib.escape(role)}</div>'
            f'<div class="team-name">{html_lib.escape(name)}</div>'
            f'</div>'
        )

    if not cards:
        cards = [
            '<div class="team-card">'
            '<div class="team-role">Project lead</div>'
            '<div class="team-name">____________________</div>'
            '</div>'
        ]

    return f"""
<div class="brochure-section">
  <h1>Project team</h1>
  <p>Senior, named personnel are assigned end-to-end. The team below is the
  point of accountability for schedule, budget, quality, and safety on this
  project.</p>
  <div class="team-grid">{''.join(cards)}</div>
</div>
"""


def _brochure_past_performance(
    sections: list[Section],
    firm_profile: dict[str, Any],
    bid_slug: str,
) -> str:
    """Pull the picks for this bid from `firm_profile` (the canonical
    selection rule) and emit a 3-card past-performance highlights page."""
    rules = firm_profile.get("past_project_selection_rules") or {}
    pick_names = (rules.get(bid_slug) or {}).get("picks") or []
    projects_by_name = {
        p.get("name", ""): p for p in (firm_profile.get("past_projects") or [])
    }

    cards: list[str] = []
    for name in pick_names:
        project = projects_by_name.get(name)
        if project is None:
            # Try a partial match — picks list uses short names.
            for k, v in projects_by_name.items():
                if name and name.split(" — ")[0] in k:
                    project = v
                    break
        if project is None:
            continue

        owner = project.get("owner", "")
        value = project.get("contract_value") or "—"
        completion = (
            project.get("actual_completion_date")
            or project.get("completion_date")
            or project.get("scheduled_substantial_completion")
            or "—"
        )
        scope = project.get("scope_summary") or ""
        scope = _truncate(scope, 320)

        cards.append(f"""
<div class="past-perf-card">
  <div class="pp-name">{html_lib.escape(project.get('name', name))}</div>
  <div class="pp-meta">Owner: {html_lib.escape(owner)} &nbsp; · &nbsp;
   Contract value: {html_lib.escape(value)} &nbsp; · &nbsp;
   Completion: {html_lib.escape(str(completion))}</div>
  <div class="pp-scope">{html_lib.escape(scope)}</div>
</div>
""")

    if not cards:
        cards = [
            '<p><em>No past-performance picks configured for this bid in '
            '<code>firm/firm-profile.json</code> — see full proposal '
            '04-past-performance for narrative.</em></p>'
        ]

    return f"""
<div class="brochure-section">
  <h1>Past performance — selected projects</h1>
  <p>Three projects most relevant to this scope, drawn from the firm's
  active past-performance roster.</p>
  {''.join(cards)}
</div>
"""


def _brochure_price_summary(sections: list[Section]) -> str:
    src = (
        find_section(sections, 10, slug_contains="price-proposal")
        or find_section(sections, 1, slug_contains="price-proposal")
        or find_section(sections, 1, slug_contains="volume-I")
    )
    total_line = ""
    bullets: list[str] = []
    if src is not None:
        # Look for explicit "Total bid price" or grand-total lines.
        money_re = re.compile(
            r"(grand total|total bid|total proposal|total price|base bid)[^|\n]*\$\s*([\d,_]+|_+)",
            re.IGNORECASE,
        )
        for line in src.body.splitlines():
            stripped = line.strip().lstrip("|").lstrip("-").strip()
            if not stripped:
                continue
            if money_re.search(stripped):
                bullets.append(_truncate(collapse_whitespace(stripped), 200))
            if len(bullets) >= 5:
                break
        if not bullets:
            first = first_paragraph(src.body)
            if first:
                bullets.append(_truncate(first, 320))
        # Best-guess total line — first bullet that mentions "total".
        for b in bullets:
            if "total" in b.lower():
                total_line = b
                break

    if not total_line:
        total_line = "Total proposed price: $____________________"

    bullet_html = "".join(
        f"<li>{html_lib.escape(b)}</li>" for b in bullets[:6]
    ) or "<li>Base bid: $____________________</li><li>Alternates: see full proposal</li><li>Unit prices: see full proposal</li>"

    return f"""
<div class="brochure-section">
  <h1>Price summary</h1>
  <div class="brochure-stat">
    <div class="stat-label">Total proposed price</div>
    <div class="stat-value">{html_lib.escape(total_line)}</div>
  </div>
  <p>Pricing detail — base bid, alternates, unit prices, allowances, and
  schedule-of-values structure — is provided in full in the price-proposal
  section of the full proposal PDF.</p>
  <ul>{bullet_html}</ul>
</div>
"""


def _brochure_qa(firm_profile: dict[str, Any], bid_slug: str) -> str:
    person = primary_personnel(firm_profile)
    legal = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    web = firm_profile.get("website", "")
    return f"""
<div class="brochure-section">
  <h1>Q&amp;A and contact</h1>
  <p>For questions on this proposal, contract negotiation, or post-award
  coordination, please direct correspondence to the named principal below.
  Blue Print Constructs commits to a 24-hour response window on RFIs and
  pre-award correspondence during the evaluation period.</p>
  <div class="brochure-callout">
    <div class="cover-firm-name">{html_lib.escape(dba or legal)}</div>
    <div class="cover-firm-meta">{html_lib.escape(legal)}</div>
    <div class="cover-firm-meta">{html_lib.escape(web)}</div>
    <div style="margin-top:8pt;">
      <strong>{html_lib.escape(person.get('name', ''))}</strong> &nbsp; — &nbsp;
      {html_lib.escape(person.get('title', ''))}<br/>
      {html_lib.escape(person.get('email', ''))} &nbsp; · &nbsp;
      {html_lib.escape(person.get('phone', ''))}
    </div>
  </div>
  <p style="font-size:9pt; color:#5C6A75; margin-top:16pt;">
    Bid identifier: {html_lib.escape(bid_slug)}
  </p>
</div>
"""


# ---------------------------------------------------------------------------
# HTML post-processors
# ---------------------------------------------------------------------------


def _highlight_placeholders_in_html(html: str) -> str:
    """Wrap any surviving placeholder-style markers in a styled span.

    When the caller has already neutralized markers (`show_placeholders=False`),
    this is a no-op. When the caller passed `show_placeholders=True`, the
    raw `[USER TO FILL …]` text is still present and we wrap it in red.
    """
    union = re.compile("|".join(p.pattern for p in PLACEHOLDER_PATTERNS))

    pieces: list[str] = []
    text_chunks: list[tuple[int, int]] = []
    cursor = 0
    i = 0
    while i < len(html):
        if html[i] == "<":
            if i > cursor:
                text_chunks.append((cursor, i))
            tag_end = html.find(">", i)
            if tag_end < 0:
                break
            cursor = tag_end + 1
            i = cursor
        else:
            i += 1
    if cursor < len(html):
        text_chunks.append((cursor, len(html)))

    cursor = 0
    for start, end in text_chunks:
        pieces.append(html[cursor:start])
        chunk = html[start:end]
        replaced = union.sub(
            lambda m: f'<span class="placeholder">{html_lib.escape(m.group(0))}</span>',
            chunk,
        )
        pieces.append(replaced)
        cursor = end
    pieces.append(html[cursor:])
    return "".join(pieces)


def _shade_table_rows(html: str) -> str:
    """Mark every other `<tr>` in tables with `class="alt"` so the CSS
    can apply alternating shading. Skip the header row."""
    out: list[str] = []
    pos = 0
    in_table = False
    row_index = 0

    table_re = re.compile(r"<table[^>]*>", re.IGNORECASE)
    end_table_re = re.compile(r"</table>", re.IGNORECASE)
    tr_re = re.compile(r"<tr(\s[^>]*)?>", re.IGNORECASE)

    while pos < len(html):
        if not in_table:
            m = table_re.search(html, pos)
            if not m:
                out.append(html[pos:])
                break
            out.append(html[pos:m.end()])
            pos = m.end()
            in_table = True
            row_index = 0
            continue
        m_tr = tr_re.search(html, pos)
        m_end = end_table_re.search(html, pos)
        if m_end and (not m_tr or m_end.start() < m_tr.start()):
            out.append(html[pos:m_end.end()])
            pos = m_end.end()
            in_table = False
            continue
        if not m_tr:
            out.append(html[pos:])
            break
        out.append(html[pos:m_tr.start()])
        row_index += 1
        if row_index > 1 and row_index % 2 == 0:
            existing_attrs = m_tr.group(1) or ""
            tr_html = f'<tr class="alt"{existing_attrs}>'
        else:
            tr_html = m_tr.group(0)
        out.append(tr_html)
        pos = m_tr.end()
    return "".join(out)


def _truncate(text: str, max_len: int) -> str:
    text = collapse_whitespace(text or "")
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"
