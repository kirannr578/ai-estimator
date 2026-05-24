"""Build the internal-workbook PDF for a single bid.

The internal workbook collects the scaffolding files — SF-1442 fill
guides, HSP form fill guides, bid-bond letter templates, RFI cover
letters, submission checklists, Reps & Certs pull guides, DBA / SCA
compliance notes, and similar working documents — into a single PDF the
user fills in offline.

Design choices vs. the client-facing PDFs:

* `[USER TO FILL …]` markers are kept and rendered red — visibility is
  the whole point of this document.
* Styling is utilitarian (`internal-workbook.css`) — no designed cover
  band, no section dividers, just a clean, readable layout.
* Built with `xhtml2pdf` to avoid the WeasyPrint native-lib dependency
  (per fallback in the user brief).
"""

from __future__ import annotations

import html as html_lib
import io
from datetime import date
from pathlib import Path
from typing import Any

import markdown as md_lib

from .common import (
    Section,
    discover_sections,
    parse_bid_title,
    parse_solicitation_number,
    partition_sections,
    primary_personnel,
)
from .pdf import (
    _highlight_placeholders_in_html,
    _shade_table_rows,
)

CSS_PATH = Path(__file__).with_name("css") / "internal-workbook.css"

MD_EXTENSIONS = ["tables", "fenced_code", "attr_list", "sane_lists"]


def build_internal_workbook(
    bid_dir: Path,
    out_path: Path,
    firm_profile: dict[str, Any],
) -> Path:
    """Render the internal-only sections of `<bid_dir>/proposal/` to a
    single PDF at `out_path`. Placeholders are always rendered red.
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

    _client, internal_sections = partition_sections(sections)

    # If a workspace happens to have no internal-only files (rare), still
    # ship a one-page workbook with a "no scaffolding files routed here"
    # note so reviewers don't get a missing-file mystery.
    html = _build_html(
        bid_slug=bid_slug,
        bid_title=bid_title,
        solicitation=solicitation,
        sections=internal_sections,
        firm_profile=firm_profile,
    )

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
    return out_path


def _build_html(
    *,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
) -> str:
    css = CSS_PATH.read_text(encoding="utf-8")
    cover_html = _render_cover(
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        bid_slug=bid_slug,
    )
    toc_html = _render_toc(sections)

    body_chunks: list[str] = []
    for section in sections:
        body_chunks.append(_render_section(section))
    if not body_chunks:
        body_chunks = [
            '<div class="section">'
            '<h1>No internal-scaffolding files</h1>'
            '<p>No section in this workspace was routed to the internal '
            'workbook. All proposal sections are client-facing — see the '
            'full-proposal and executive-summary PDFs in this folder.</p>'
            '</div>'
        ]
    body_html = "\n".join(body_chunks)

    header_footer = _render_header_footer(bid_slug)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>{html_lib.escape(bid_title)} — Internal workbook</title>
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


def _render_header_footer(bid_slug: str) -> str:
    safe_slug = html_lib.escape(bid_slug)
    return f"""
<div id="header_content">
  <div class="header">{safe_slug} — internal workbook</div>
</div>
<div id="footer_content">
  <table class="footer-row" style="border:0; width:100%; margin:0;">
    <tr style="border:0;">
      <td class="left" style="border:0; padding:0;">Blue Print Constructs · Internal use only</td>
      <td class="right" style="border:0; padding:0;">Page <pdf:pagenumber/> / <pdf:pagecount/></td>
    </tr>
  </table>
</div>
"""


def _render_cover(
    *,
    bid_title: str,
    solicitation: str,
    firm_profile: dict[str, Any],
    bid_slug: str,
) -> str:
    legal = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    person = primary_personnel(firm_profile)
    today = date.today().isoformat()

    return f"""
<div class="cover-page">
  <div class="cover-tier-tag">Internal use only</div>
  <div class="cover-brand">{html_lib.escape(dba or legal)}</div>
  <div class="cover-tagline">Submission workbook — {html_lib.escape(today)}</div>

  <div class="cover-bid-title">{html_lib.escape(bid_title)}</div>
  <div class="cover-solicitation">Solicitation: {html_lib.escape(solicitation or "(see RFP)")}</div>

  <div class="cover-meta">Prepared by {html_lib.escape(legal)}</div>
  <div class="cover-meta">Bid: {html_lib.escape(bid_slug)}</div>

  <div class="cover-purpose">
    <strong>Purpose.</strong> This workbook collects the
    submission-scaffolding files for this bid: SF-1442 / CSP / HSP fill
    guides, bid-bond letter templates, RFI cover letters, Reps &amp;
    Certs pull guides, compliance acknowledgments, and the submission
    checklist. <strong>USER TO FILL</strong> markers are rendered red so
    you can audit gaps at a glance. This file is for internal use only —
    do not send it to the client. The client-facing
    executive-summary and full-proposal PDFs in this same folder are
    already placeholder-cleaned.
  </div>

  <div style="margin-top:0.4in; font-size:9pt; color:#666;">
    Lead: {html_lib.escape(person.get('name', ''))} ·
    {html_lib.escape(person.get('email', ''))} ·
    {html_lib.escape(person.get('phone', ''))}
  </div>
</div>
"""


def _render_toc(sections: list[Section]) -> str:
    if not sections:
        return ""
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
  <h1>Internal workbook contents</h1>
  <table style="width:100%; border:0;">
    {"".join(rows)}
  </table>
</div>
"""


def _render_section(section: Section) -> str:
    raw_html = md_lib.markdown(
        section.body, extensions=MD_EXTENSIONS, output_format="html5"
    )
    raw_html = _highlight_placeholders_in_html(raw_html)
    raw_html = _shade_table_rows(raw_html)
    return f'<div class="section">{raw_html}</div>'
