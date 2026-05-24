"""Build the full-proposal PDF for a single bid workspace.

Public entry point: `build_proposal_pdf(bid_dir, out_path, firm_profile)`.

Pipeline:
  1. Discover the proposal sections (numerical-prefix order; drafts skipped).
  2. Convert each section's Markdown to HTML via `markdown` + `tables`,
     `fenced_code`, and `attr_list` extensions.
  3. Wrap with a cover page + auto-generated TOC.
  4. Stitch into one HTML document and feed to `xhtml2pdf` (`pisa`).

xhtml2pdf is pure Python; no GTK / Cairo / Chromium runtime needed. The
rendered PDF is US Letter, 1-inch margins, with bid-slug header + page X / Y
footer.

Placeholders (`[USER TO FILL ...]` and friends) are wrapped in
`<span class="placeholder">...</span>` so reviewers see them in red.
"""

from __future__ import annotations

import html as html_lib
import io
import re
from datetime import date
from pathlib import Path
from typing import Any

import markdown as md_lib

from .common import (
    DEFAULT_LOGO_PATH,
    PLACEHOLDER_PATTERNS,
    Section,
    discover_sections,
    parse_bid_title,
    parse_solicitation_number,
    primary_personnel,
)

CSS_PATH = Path(__file__).with_name("css") / "proposal.css"

MD_EXTENSIONS = ["tables", "fenced_code", "attr_list", "sane_lists"]


def build_proposal_pdf(
    bid_dir: Path,
    out_path: Path,
    firm_profile: dict[str, Any],
    *,
    logo_path: Path | None = None,
) -> Path:
    """Render `<bid_dir>/proposal/` to a single PDF at `out_path`.

    Returns the resolved output path.

    Raises `FileNotFoundError` if `<bid_dir>/proposal/` is missing or empty.
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

    html = _build_html(
        bid_slug=bid_slug,
        bid_title=bid_title,
        solicitation=solicitation,
        sections=sections,
        firm_profile=firm_profile,
        logo_path=logo_path or DEFAULT_LOGO_PATH,
    )

    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Render with xhtml2pdf. We import lazily so the package import is cheap
    # for code paths that only need section discovery.
    from xhtml2pdf import pisa

    with out_path.open("wb") as fh:
        result = pisa.CreatePDF(
            io.StringIO(html),
            dest=fh,
            encoding="utf-8",
        )
    if result.err:
        raise RuntimeError(f"xhtml2pdf reported {result.err} errors rendering {out_path}")

    return out_path


def _build_html(
    *,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
    logo_path: Path,
) -> str:
    css = CSS_PATH.read_text(encoding="utf-8")

    cover_html = _render_cover(
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        logo_path=logo_path,
        bid_slug=bid_slug,
    )

    toc_html = _render_toc(sections)

    body_chunks: list[str] = []
    for section in sections:
        body_chunks.append(_render_section(section))
    body_html = "\n".join(body_chunks)

    header_footer = _render_header_footer(bid_slug)

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>{html_lib.escape(bid_title)} — Proposal</title>
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
  <div class="header">{safe_slug}</div>
</div>
<div id="footer_content">
  <table class="footer-row" style="border:0; width:100%; margin:0;">
    <tr style="border:0;">
      <td class="left" style="border:0; padding:0;">Blue Print Constructs</td>
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
    logo_path: Path,
    bid_slug: str,
) -> str:
    person = primary_personnel(firm_profile)
    legal_name = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    uei = firm_profile.get("uei", "")
    cage = firm_profile.get("cage", "")
    today = date.today().isoformat()

    if logo_path and logo_path.exists():
        logo_block = (
            f'<div class="cover-logo">'
            f'<img src="{html_lib.escape(str(logo_path))}" />'
            f'</div>'
        )
    else:
        logo_block = (
            f'<div class="cover-brand">{html_lib.escape(dba or legal_name)}</div>'
        )

    return f"""
<div class="cover-page">
  {logo_block}
  <div class="cover-brand">{html_lib.escape(dba or legal_name)}</div>
  <div class="cover-tagline">Proposal — {html_lib.escape(today)}</div>

  <div class="cover-bid-title">{html_lib.escape(bid_title)}</div>
  <div class="cover-solicitation">Solicitation: {html_lib.escape(solicitation or "(see RFP)")}</div>

  <div class="cover-meta">Prepared by {html_lib.escape(legal_name)} dba {html_lib.escape(dba)}</div>
  <div class="cover-meta">UEI: {html_lib.escape(uei)} &nbsp;&nbsp; CAGE: {html_lib.escape(cage)}</div>

  <div class="cover-signature">
    <div class="label">Authorized signer</div>
    <div>{html_lib.escape(person.get("name", ""))}</div>
    <div>{html_lib.escape(person.get("title", ""))}</div>
    <div>{html_lib.escape(person.get("email", ""))}</div>
    <div>{html_lib.escape(person.get("phone", ""))}</div>
  </div>

  <div class="cover-footer">Confidential &mdash; Proposal &mdash; {html_lib.escape(bid_slug)}</div>
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


def _render_section(section: Section) -> str:
    raw_html = md_lib.markdown(section.body, extensions=MD_EXTENSIONS, output_format="html5")
    raw_html = _highlight_placeholders_in_html(raw_html)
    raw_html = _shade_table_rows(raw_html)
    return f'<div class="section">{raw_html}</div>'


def _highlight_placeholders_in_html(html: str) -> str:
    """Wrap placeholder runs in `<span class="placeholder">...</span>` so the
    CSS can render them red. Avoid touching content inside HTML tags by
    splitting on `<...>` boundaries.

    Inside `<code>` / `<pre>` blocks the replacement is also applied; rendering
    the bracketed marker in red there is fine because reviewers should still
    see the gap.
    """
    # Pre-compile a single union pattern from the placeholder regexes.
    union = re.compile("|".join(p.pattern for p in PLACEHOLDER_PATTERNS))

    out: list[str] = []
    cursor = 0
    in_tag = False
    tag_start = 0

    # Walk character-by-character, only highlighting outside HTML tags.
    pieces: list[str] = []
    text_chunks: list[tuple[int, int]] = []
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
        # Append everything up to this text chunk verbatim.
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
    """Mark every other `<tr>` in table bodies with `class="alt"` so the
    CSS can apply alternating-row shading. Skip the first row of each table
    (assumed to be the header).
    """
    out: list[str] = []
    cursor = 0
    in_table = False
    row_index = 0

    table_re = re.compile(r"<table[^>]*>", re.IGNORECASE)
    end_table_re = re.compile(r"</table>", re.IGNORECASE)
    tr_re = re.compile(r"<tr(\s[^>]*)?>", re.IGNORECASE)

    pos = 0
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
        # In table — find next tr or end of table
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
        # Append text up to this tr
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
