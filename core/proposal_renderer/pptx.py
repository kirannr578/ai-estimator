"""Build a pitch-deck (default) or full-walkthrough PPTX for a single bid.

Public entry point: `build_proposal_pptx(bid_dir, out_path, firm_profile,
style="pitch_deck")`.

Two styles:

  * `pitch_deck` — 10–15 slides distilled from the proposal markdown:
    title, about, project understanding, technical approach, project team,
    past performance, schedule, quality + safety, price, submission status,
    why-BPC, Q&A. This is the primary deliverable.

  * `full` — one slide per H1 in the markdown source. Body prose is
    truncated and split if it exceeds ~400 chars. Useful for internal review
    walkthroughs.

Both styles use 16:9 widescreen with a dark-navy / white palette.
"""

from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import Any, Iterable

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.util import Emu, Inches, Pt

from .common import (
    DEFAULT_LOGO_PATH,
    Section,
    collapse_whitespace,
    discover_sections,
    find_h1_blocks,
    find_h2_blocks,
    find_section,
    first_paragraph,
    list_items,
    parse_bid_title,
    parse_solicitation_number,
    primary_personnel,
    split_placeholders,
    strip_blockquote_prefix,
)

NAVY = RGBColor(0x0F, 0x2A, 0x4A)
NEAR_BLACK = RGBColor(0x11, 0x11, 0x11)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
RED = RGBColor(0xC0, 0x00, 0x00)
LIGHT_GRAY = RGBColor(0xEE, 0xEE, 0xEE)

SLIDE_WIDTH = Inches(13.333)
SLIDE_HEIGHT = Inches(7.5)


def build_proposal_pptx(
    bid_dir: Path,
    out_path: Path,
    firm_profile: dict[str, Any],
    *,
    style: str = "pitch_deck",
    logo_path: Path | None = None,
) -> Path:
    """Render `<bid_dir>/proposal/` to a PPTX file at `out_path`.

    `style="pitch_deck"` (default) produces 10-15 distilled slides.
    `style="full"` produces one slide per H1 in the source markdown.
    """
    if style not in {"pitch_deck", "full"}:
        raise ValueError(f"style must be 'pitch_deck' or 'full', got {style!r}")

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

    prs = Presentation()
    prs.slide_width = SLIDE_WIDTH
    prs.slide_height = SLIDE_HEIGHT

    if style == "pitch_deck":
        _build_pitch_deck(
            prs=prs,
            bid_slug=bid_slug,
            bid_title=bid_title,
            solicitation=solicitation,
            sections=sections,
            firm_profile=firm_profile,
            logo_path=logo_path or DEFAULT_LOGO_PATH,
        )
    else:
        _build_full_deck(
            prs=prs,
            bid_slug=bid_slug,
            bid_title=bid_title,
            solicitation=solicitation,
            sections=sections,
            firm_profile=firm_profile,
            logo_path=logo_path or DEFAULT_LOGO_PATH,
        )

    out_path.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(out_path))
    return out_path


# ---------------------------------------------------------------------------
# Pitch-deck builder
# ---------------------------------------------------------------------------


def _build_pitch_deck(
    *,
    prs: Presentation,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
    logo_path: Path,
) -> None:
    _slide_title(
        prs,
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        logo_path=logo_path,
    )

    _slide_about_bpc(prs, firm_profile=firm_profile, bid_slug=bid_slug)

    _slide_project_understanding(
        prs, sections=sections, bid_slug=bid_slug, bid_title=bid_title
    )

    _slide_technical_approach(prs, sections=sections, bid_slug=bid_slug)

    _slide_project_team(prs, sections=sections, bid_slug=bid_slug)

    _slide_past_performance(prs, sections=sections, bid_slug=bid_slug)

    _slide_schedule(prs, sections=sections, bid_slug=bid_slug)

    _slide_quality_safety(prs, sections=sections, bid_slug=bid_slug)

    _slide_price(prs, sections=sections, bid_slug=bid_slug)

    _slide_submission_status(prs, sections=sections, bid_slug=bid_slug)

    _slide_why_bpc(prs, firm_profile=firm_profile, bid_slug=bid_slug)

    _slide_qa(prs, firm_profile=firm_profile, bid_slug=bid_slug)


# ---------------------------------------------------------------------------
# Full-deck builder
# ---------------------------------------------------------------------------


def _build_full_deck(
    *,
    prs: Presentation,
    bid_slug: str,
    bid_title: str,
    solicitation: str,
    sections: list[Section],
    firm_profile: dict[str, Any],
    logo_path: Path,
) -> None:
    _slide_title(
        prs,
        bid_title=bid_title,
        solicitation=solicitation,
        firm_profile=firm_profile,
        logo_path=logo_path,
    )

    for section in sections:
        for h1_title, body in find_h1_blocks(section.body) or [(section.title, section.body)]:
            chunks = _chunk_text_for_slide(body, max_chars=400)
            if not chunks:
                chunks = [""]
            for i, chunk in enumerate(chunks):
                title = h1_title if len(chunks) == 1 else f"{h1_title} ({i + 1}/{len(chunks)})"
                _body_slide(
                    prs,
                    title=title,
                    body_lines=[ln.strip() for ln in chunk.splitlines() if ln.strip()][:8],
                    bid_slug=bid_slug,
                )


# ---------------------------------------------------------------------------
# Slide builders
# ---------------------------------------------------------------------------


def _slide_title(
    prs: Presentation,
    *,
    bid_title: str,
    solicitation: str,
    firm_profile: dict[str, Any],
    logo_path: Path,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])  # blank
    _set_background(slide, NAVY)

    # Logo (centered top half)
    if logo_path and logo_path.exists():
        # 4 inches wide, height auto.
        try:
            slide.shapes.add_picture(
                str(logo_path),
                left=Inches(4.667),
                top=Inches(0.7),
                width=Inches(4.0),
            )
        except Exception:
            # Image add can fail on weird PNG metadata; skip silently.
            pass

    # Bid title
    _add_text(
        slide,
        text=bid_title,
        left=Inches(0.5), top=Inches(3.5), width=Inches(12.333), height=Inches(1.2),
        font_size=Pt(34), bold=True, color=WHITE, align=PP_ALIGN.CENTER,
    )

    # Solicitation
    if solicitation:
        _add_text(
            slide,
            text=f"Solicitation: {solicitation}",
            left=Inches(0.5), top=Inches(4.7), width=Inches(12.333), height=Inches(0.5),
            font_size=Pt(16), color=WHITE, align=PP_ALIGN.CENTER,
        )

    # Firm line
    legal = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    firm_line = (
        f"{dba} (legal: {legal})" if dba and legal and dba != legal else dba or legal
    )
    _add_text(
        slide,
        text=f"{firm_line} — Submission Date TBD by reviewer",
        left=Inches(0.5), top=Inches(5.5), width=Inches(12.333), height=Inches(0.5),
        font_size=Pt(13), color=WHITE, align=PP_ALIGN.CENTER, italic=True,
    )

    # Footer date
    _add_text(
        slide,
        text=f"Prepared {date.today().isoformat()}",
        left=Inches(0.5), top=Inches(6.7), width=Inches(12.333), height=Inches(0.4),
        font_size=Pt(10), color=WHITE, align=PP_ALIGN.CENTER,
    )


def _slide_about_bpc(
    prs: Presentation, *, firm_profile: dict[str, Any], bid_slug: str
) -> None:
    legal = firm_profile.get("legal_name", "")
    dba = firm_profile.get("dba", "")
    naics_codes = firm_profile.get("naics_codes") or []
    primary_naics = firm_profile.get("naics_primary_for_renovation_bids", "")
    uei = firm_profile.get("uei", "")
    cage = firm_profile.get("cage", "")
    sa = firm_profile.get("set_aside_eligibility") or {}
    self_perform = (firm_profile.get("trade_capabilities") or {}).get("self_perform") or []

    bullets = [
        (False, f"Legal name: {legal} dba {dba}"),
        (False,
         f"NAICS: primary {primary_naics} (Commercial & Institutional Building "
         f"Construction); {len(naics_codes)} codes registered total"),
        (False, f"UEI: {uei}   CAGE: {cage}   SAM.gov status: "
                f"{firm_profile.get('sam_status', 'TBD')}"),
        (False,
         "Set-aside posture: " + ", ".join(filter(None, [
             "small business" if sa.get("small_business") else "",
             "minority-owned" if sa.get("minority_owned") else "",
             f"MBE ({sa.get('mbe_status')})" if sa.get("mbe_status") else "",
             f"TX HUB ({sa.get('tx_hub_status')})" if sa.get("tx_hub_status") else "",
         ]))),
        (False,
         "Self-perform trades: " + (", ".join(self_perform[:6]) if self_perform else "—")),
    ]
    _body_slide(
        prs,
        title="About Blue Print Constructs",
        bullets=bullets,
        bid_slug=bid_slug,
    )


def _slide_project_understanding(
    prs: Presentation,
    *,
    sections: list[Section],
    bid_slug: str,
    bid_title: str,
) -> None:
    src = (
        find_section(sections, 1, slug_contains="executive-summary")
        or find_section(sections, 2, slug_contains="volume-II")
        or find_section(sections, 2, slug_contains="technical-acceptability")
    )
    bullets: list[tuple[bool, str]] = []
    if src is not None:
        # First find an "Executive summary" / "Project understanding" h2
        # block, else fall back to the document's first paragraph.
        for h2_title, body in find_h2_blocks(src.body):
            if any(
                key in h2_title.lower()
                for key in ("executive summary", "understanding", "overview", "scope at a glance")
            ):
                items = list_items(body)[:3]
                if items:
                    bullets.extend((False, _truncate(it, 220)) for it in items)
                    break
                first = first_paragraph(body)
                if first:
                    bullets.append((False, _truncate(first, 280)))
                    break
        if not bullets:
            text = first_paragraph(src.body)
            if text:
                bullets.append((False, _truncate(text, 280)))
    if not bullets:
        bullets = [(False, f"Project: {bid_title}")]
    while len(bullets) < 3:
        bullets.append((False, "(See proposal PDF — detail not surfaced as bullets here)"))
    bullets = bullets[:4]

    _body_slide(
        prs,
        title="Project understanding",
        bullets=bullets,
        bid_slug=bid_slug,
    )


def _slide_technical_approach(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    src = (
        find_section(sections, 2, slug_contains="technical-approach")
        or find_section(sections, 2, slug_contains="volume-II")
        or find_section(sections, 2, slug_contains="technical-acceptability")
    )
    bullets: list[tuple[bool, str]] = []
    if src is not None:
        for h2_title, body in find_h2_blocks(src.body):
            label = h2_title.split("—", 1)[0].strip()
            label = re.sub(r"^\d+\.\s*", "", label)
            label = label.strip(":") or h2_title
            first = first_paragraph(body)
            text = f"{label}: {_truncate(first, 200)}" if first else label
            bullets.append((False, _truncate(text, 240)))
            if len(bullets) >= 6:
                break
    if not bullets:
        bullets = [(False, "(Technical approach section not detected)")]
    _body_slide(
        prs,
        title="Technical approach",
        bullets=bullets,
        bid_slug=bid_slug,
        bold_first_phrase=True,
    )


def _slide_project_team(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    src = find_section(
        sections,
        3,
        slug_contains="project-team",
    )
    rows: list[tuple[str, str]] = []  # (role, name)
    if src is not None:
        # Look for "Role" / "Name" pairs in tables; fall back to text.
        for h2_title, body in find_h2_blocks(src.body):
            if "role" in h2_title.lower() or "résumé" in h2_title.lower() or "resume" in h2_title.lower():
                role = re.sub(r"^Role\s+\d+\s*[—-]\s*", "", h2_title).strip()
                name = ""
                m = re.search(
                    r"\|\s*Name\s*\|\s*([^|]+?)\s*\|", body, re.IGNORECASE
                )
                if m:
                    name = m.group(1).strip().strip("`")
                if not name:
                    name = "[USER TO FILL — name]"
                rows.append((role, name))
        if not rows:
            for h3_title, _ in find_h3_blocks(src.body):
                rows.append((h3_title, "[USER TO FILL — name]"))
        if not rows:
            rows.append(("Project lead", "(see project-team section)"))
    else:
        rows.append(("Project lead", "(no project-team section)"))

    rows = rows[:8]
    _table_slide(
        prs,
        title="Project team",
        headers=["Role", "Name"],
        rows=rows,
        bid_slug=bid_slug,
        col_widths=[Inches(5.0), Inches(7.0)],
    )


def _slide_past_performance(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    src = (
        find_section(sections, 4, slug_contains="past-performance")
        or find_section(sections, 3, slug_contains="past-performance")
        or find_section(sections, 3, slug_contains="volume-III")
    )
    headers = ["Project", "Owner", "Value", "Completion", "Scope summary"]
    rows: list[list[str]] = []
    if src is not None:
        rows = _extract_past_perf_rows(src.body, max_rows=3)
    if not rows:
        rows = [
            [
                "(No past performance rows extracted)",
                "—", "—", "—",
                "Renderer could not parse rows; see proposal PDF for the full file.",
            ]
        ]
    _table_slide(
        prs,
        title="Past performance",
        headers=headers,
        rows=rows,
        bid_slug=bid_slug,
        col_widths=[Inches(2.5), Inches(2.5), Inches(1.5), Inches(1.5), Inches(4.0)],
        font_size=Pt(10),
    )


def _slide_schedule(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    src = find_section(sections, 5, slug_contains="schedule")
    bullets: list[tuple[bool, str]] = []
    if src is not None:
        # Look for milestone bullets or a table with Milestone / Date columns.
        for h2_title, body in find_h2_blocks(src.body):
            if "milestone" in h2_title.lower() or "schedule" in h2_title.lower():
                items = list_items(body)
                for it in items[:8]:
                    bullets.append((False, _truncate(it, 200)))
                if bullets:
                    break
        if not bullets:
            for it in list_items(src.body)[:8]:
                bullets.append((False, _truncate(it, 200)))
        if not bullets:
            text = first_paragraph(src.body)
            if text:
                bullets.append((False, _truncate(text, 280)))
    if not bullets:
        bullets = [(False, "(Schedule section not detected)")]
    _body_slide(prs, title="Schedule", bullets=bullets, bid_slug=bid_slug)


def _slide_quality_safety(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    qc = find_section(sections, 6, slug_contains="quality")
    safety = find_section(sections, 7, slug_contains="safety")
    bullets: list[tuple[bool, str]] = []

    for label, src in (("QC: ", qc), ("Safety: ", safety)):
        if src is None:
            continue
        # Try to surface a "highlights" or "summary" h2 block.
        used = False
        for h2_title, body in find_h2_blocks(src.body):
            if any(
                k in h2_title.lower()
                for k in ("highlights", "summary", "philosophy", "overview", "objectives")
            ):
                first = first_paragraph(body)
                if first:
                    bullets.append((False, _truncate(label + first, 240)))
                    used = True
                    break
                items = list_items(body)
                if items:
                    bullets.append((False, _truncate(label + items[0], 240)))
                    used = True
                    break
        if not used:
            first = first_paragraph(src.body)
            if first:
                bullets.append((False, _truncate(label + first, 240)))

    if not bullets:
        bullets = [(False, "(Quality / safety highlights not detected)")]
    _body_slide(prs, title="Quality & safety", bullets=bullets, bid_slug=bid_slug)


def _slide_price(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    # RFCSP shape: 10-price-proposal. Federal: 01-volume-I-price-proposal /
    # 01-price-proposal.
    src = (
        find_section(sections, 10, slug_contains="price-proposal")
        or find_section(sections, 1, slug_contains="price-proposal")
        or find_section(sections, 1, slug_contains="volume-I")
    )
    bullets: list[tuple[bool, str]] = []
    if src is not None:
        # Pull the section's first paragraph; then surface any line that
        # looks like "Total bid price" or "Grand total" or "$..." as bullets.
        first = first_paragraph(src.body)
        if first:
            bullets.append((False, _truncate(first, 260)))
        money_re = re.compile(r"(Total[^|\n]*\$[^|\n]+)|(Grand total[^|\n]*\$[^|\n]+)")
        for line in src.body.splitlines():
            stripped = line.strip().lstrip("|").lstrip("-").strip()
            if not stripped:
                continue
            if money_re.search(stripped):
                bullets.append((False, _truncate(collapse_whitespace(stripped), 220)))
            elif "[USER TO FILL — $" in line or "[USER TO FILL: $" in line:
                bullets.append((False, _truncate(collapse_whitespace(stripped), 220)))
            if len(bullets) >= 5:
                break
    if not bullets:
        bullets = [(False, "(Price proposal section not detected)")]
    _body_slide(prs, title="Price proposal", bullets=bullets, bid_slug=bid_slug)


def _slide_submission_status(
    prs: Presentation, *, sections: list[Section], bid_slug: str
) -> None:
    src = (
        find_section(sections, 11, slug_contains="submission-checklist")
        or find_section(sections, 10, slug_contains="submission-checklist")
    )
    bullets: list[tuple[bool, str]] = []
    if src is not None:
        ready_count = 0
        partial_count = 0
        pending_count = 0
        for line in src.body.splitlines():
            s = line.strip()
            if re.match(r"^[-*]\s*\[x\]\s", s, re.IGNORECASE):
                ready_count += 1
            elif re.match(r"^[-*]\s*\[~\]\s", s):
                partial_count += 1
            elif re.match(r"^[-*]\s*\[\s\]\s", s):
                pending_count += 1
        total = ready_count + partial_count + pending_count
        if total:
            bullets = [
                (False, f"Ready: {ready_count} item(s)"),
                (False, f"Partial: {partial_count} item(s)"),
                (False, f"Pending: {pending_count} item(s)"),
            ]
        else:
            first = first_paragraph(src.body)
            if first:
                bullets.append((False, _truncate(first, 280)))
    if not bullets:
        bullets = [(False, "(Submission checklist section not detected)")]
    _body_slide(
        prs, title="Submission checklist status", bullets=bullets, bid_slug=bid_slug
    )


def _slide_why_bpc(
    prs: Presentation, *, firm_profile: dict[str, Any], bid_slug: str
) -> None:
    sa = firm_profile.get("set_aside_eligibility") or {}
    self_perform = (firm_profile.get("trade_capabilities") or {}).get("self_perform") or []
    sectors = (firm_profile.get("trade_capabilities") or {}).get("served_sectors") or []
    bullets = [
        (False, f"Texas-based small business — self-perform across {len(self_perform)} core trades"),
        (False, "Diverse-business posture: " + ", ".join(filter(None, [
            "TX HUB" if sa.get("tx_hub_status") else "",
            f"MBE ({sa.get('mbe_status')})" if sa.get("mbe_status") else "",
            "small business" if sa.get("small_business") else "",
            "minority-owned" if sa.get("minority_owned") else "",
        ])) or "—"),
        (False,
         "Sector breadth: "
         + (", ".join(s.split("—")[0].strip() for s in sectors[:4]) if sectors else "—")),
        (False,
         f"Founder-led PMP / CSM operator with 22 years delivery leadership — "
         f"{(firm_profile.get('key_personnel') or [{}])[0].get('name', '')}"),
    ]
    _body_slide(prs, title="Why Blue Print Constructs", bullets=bullets, bid_slug=bid_slug)


def _slide_qa(
    prs: Presentation, *, firm_profile: dict[str, Any], bid_slug: str
) -> None:
    person = primary_personnel(firm_profile)
    bullets = [
        (False, f"{person.get('name', '')} — {person.get('title', '')}"),
        (False, f"Email: {person.get('email', '')}"),
        (False, f"Phone: {person.get('phone', '')}"),
        (False, f"Web: {firm_profile.get('website', '')}"),
        (False, "Next steps: site walk, RFI consolidation, sub bid coordination, final pricing."),
    ]
    _body_slide(
        prs,
        title="Q&A / Next steps",
        bullets=bullets,
        bid_slug=bid_slug,
    )


# ---------------------------------------------------------------------------
# Slide-builder primitives
# ---------------------------------------------------------------------------


def _body_slide(
    prs: Presentation,
    *,
    title: str,
    bullets: list[tuple[bool, str]] | None = None,
    body_lines: list[str] | None = None,
    bid_slug: str,
    bold_first_phrase: bool = False,
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_background(slide, WHITE)

    # Title bar
    _add_title_bar(slide, title)

    # Body
    body = slide.shapes.add_textbox(
        left=Inches(0.5), top=Inches(1.4),
        width=Inches(12.333), height=Inches(5.4),
    ).text_frame
    body.word_wrap = True

    items = bullets if bullets is not None else [(False, ln) for ln in (body_lines or [])]
    if not items:
        items = [(False, "(no content)")]

    for i, (is_red, text) in enumerate(items):
        if i == 0:
            para = body.paragraphs[0]
        else:
            para = body.add_paragraph()
        para.alignment = PP_ALIGN.LEFT
        para.level = 0
        runs_added = False
        if bold_first_phrase and ":" in text:
            head, rest = text.split(":", 1)
            r1 = para.add_run()
            r1.text = head + ":"
            _style_run(r1, font_size=Pt(16), bold=True, color=NAVY)
            r2 = para.add_run()
            r2.text = rest
            _style_run(r2, font_size=Pt(16), color=NEAR_BLACK)
            runs_added = True
        else:
            for is_ph, frag in split_placeholders(text):
                if not frag:
                    continue
                r = para.add_run()
                r.text = frag
                _style_run(
                    r,
                    font_size=Pt(16),
                    bold=is_red or is_ph,
                    color=RED if (is_red or is_ph) else NEAR_BLACK,
                )
                runs_added = True
        if not runs_added:
            r = para.add_run()
            r.text = text
            _style_run(r, font_size=Pt(16), color=NEAR_BLACK)

    _add_footer(slide, bid_slug=bid_slug, slide_number=len(prs.slides))


def _table_slide(
    prs: Presentation,
    *,
    title: str,
    headers: list[str],
    rows: list[list[str]] | list[tuple[str, ...]],
    bid_slug: str,
    col_widths: list[Emu] | None = None,
    font_size: Pt = Pt(11),
) -> None:
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    _set_background(slide, WHITE)
    _add_title_bar(slide, title)

    n_cols = len(headers)
    rows_norm: list[list[str]] = []
    for r in rows:
        rl = list(r)
        while len(rl) < n_cols:
            rl.append("")
        rows_norm.append(rl[:n_cols])

    n_rows = len(rows_norm) + 1
    left = Inches(0.5)
    top = Inches(1.4)
    width = Inches(12.333)
    height = Inches(5.0)

    table_shape = slide.shapes.add_table(n_rows, n_cols, left, top, width, height)
    table = table_shape.table

    if col_widths and len(col_widths) == n_cols:
        for i, w in enumerate(col_widths):
            table.columns[i].width = w

    # Header row
    for c, h in enumerate(headers):
        cell = table.cell(0, c)
        cell.fill.solid()
        cell.fill.fore_color.rgb = NAVY
        tf = cell.text_frame
        tf.clear()
        tf.word_wrap = True
        para = tf.paragraphs[0]
        run = para.add_run()
        run.text = h
        _style_run(run, font_size=Pt(12), bold=True, color=WHITE)
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    for r_idx, row in enumerate(rows_norm, start=1):
        is_alt = (r_idx % 2 == 0)
        for c_idx, val in enumerate(row):
            cell = table.cell(r_idx, c_idx)
            cell.fill.solid()
            cell.fill.fore_color.rgb = LIGHT_GRAY if is_alt else WHITE
            tf = cell.text_frame
            tf.clear()
            tf.word_wrap = True
            para = tf.paragraphs[0]
            for is_ph, frag in split_placeholders(val):
                if not frag:
                    continue
                run = para.add_run()
                run.text = frag
                _style_run(
                    run,
                    font_size=font_size,
                    bold=is_ph,
                    color=RED if is_ph else NEAR_BLACK,
                )
            if not para.runs:
                run = para.add_run()
                run.text = ""

    _add_footer(slide, bid_slug=bid_slug, slide_number=len(prs.slides))


def _add_title_bar(slide, title: str) -> None:
    # Navy bar across the top
    bar = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left=Inches(0), top=Inches(0),
        width=SLIDE_WIDTH, height=Inches(1.0),
    )
    bar.fill.solid()
    bar.fill.fore_color.rgb = NAVY
    bar.line.fill.background()
    tf = bar.text_frame
    tf.margin_left = Inches(0.5)
    tf.vertical_anchor = MSO_ANCHOR.MIDDLE
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.LEFT
    run = para.add_run()
    run.text = title
    _style_run(run, font_size=Pt(24), bold=True, color=WHITE)


def _add_footer(slide, *, bid_slug: str, slide_number: int) -> None:
    box = slide.shapes.add_textbox(
        left=Inches(0.5), top=Inches(7.05),
        width=Inches(12.333), height=Inches(0.35),
    )
    tf = box.text_frame
    tf.margin_left = Inches(0)
    para = tf.paragraphs[0]
    para.alignment = PP_ALIGN.LEFT
    r1 = para.add_run()
    r1.text = bid_slug
    _style_run(r1, font_size=Pt(9), color=RGBColor(0x77, 0x77, 0x77))
    # Right-aligned slide number — easier to read with a tab + right align by
    # adding a separate trailing text box.
    box_r = slide.shapes.add_textbox(
        left=Inches(11.0), top=Inches(7.05),
        width=Inches(1.833), height=Inches(0.35),
    )
    tf_r = box_r.text_frame
    para_r = tf_r.paragraphs[0]
    para_r.alignment = PP_ALIGN.RIGHT
    r2 = para_r.add_run()
    r2.text = f"Slide {slide_number}"
    _style_run(r2, font_size=Pt(9), color=RGBColor(0x77, 0x77, 0x77))


def _add_text(
    slide,
    *,
    text: str,
    left: Emu, top: Emu, width: Emu, height: Emu,
    font_size: Pt = Pt(14),
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = NEAR_BLACK,
    align: PP_ALIGN = PP_ALIGN.LEFT,
) -> None:
    box = slide.shapes.add_textbox(left, top, width, height)
    tf = box.text_frame
    tf.word_wrap = True
    para = tf.paragraphs[0]
    para.alignment = align
    run = para.add_run()
    run.text = text
    _style_run(run, font_size=font_size, bold=bold, italic=italic, color=color)


def _style_run(
    run,
    *,
    font_size: Pt = Pt(14),
    bold: bool = False,
    italic: bool = False,
    color: RGBColor = NEAR_BLACK,
) -> None:
    run.font.size = font_size
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = color


def _set_background(slide, color: RGBColor) -> None:
    # python-pptx doesn't expose a direct "set slide background to RGB" API
    # without going through theme-color juggling; for our blank layout we
    # paint a full-bleed rectangle behind everything else.
    bg = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        left=Inches(0), top=Inches(0),
        width=SLIDE_WIDTH, height=SLIDE_HEIGHT,
    )
    bg.fill.solid()
    bg.fill.fore_color.rgb = color
    bg.line.fill.background()
    bg.shadow.inherit = False
    # Send to back so subsequently added shapes draw on top.
    spTree = bg._element.getparent()
    spTree.remove(bg._element)
    spTree.insert(2, bg._element)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _truncate(text: str, max_len: int) -> str:
    text = collapse_whitespace(strip_blockquote_prefix(text))
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip() + "…"


def _chunk_text_for_slide(body: str, *, max_chars: int) -> list[str]:
    body = strip_blockquote_prefix(body).strip()
    if not body:
        return []
    chunks: list[str] = []
    cursor = 0
    while cursor < len(body):
        end = min(cursor + max_chars, len(body))
        # Try not to cut in the middle of a sentence.
        if end < len(body):
            # Walk back to last period/newline within window.
            window = body[cursor:end]
            last_break = max(
                window.rfind(". "),
                window.rfind("\n"),
                window.rfind("; "),
            )
            if last_break > max_chars * 0.6:
                end = cursor + last_break + 1
        chunks.append(body[cursor:end].strip())
        cursor = end
    return chunks


def find_h3_blocks(text: str) -> list[tuple[str, str]]:
    lines = text.splitlines()
    blocks: list[tuple[str, list[str]]] = []
    cur_t: str | None = None
    cur_b: list[str] = []
    h3_re = re.compile(r"^###\s+(.+?)\s*$")
    for line in lines:
        m = h3_re.match(line)
        if m:
            if cur_t is not None:
                blocks.append((cur_t, cur_b))
            cur_t = m.group(1).strip()
            cur_b = []
            continue
        if cur_t is not None:
            cur_b.append(line)
    if cur_t is not None:
        blocks.append((cur_t, cur_b))
    return [(t, "\n".join(b).strip()) for t, b in blocks]


def _extract_past_perf_rows(text: str, *, max_rows: int = 3) -> list[list[str]]:
    """Try to surface up to `max_rows` past-performance rows from the file's
    "at-a-glance" Markdown table, falling back to per-`Project Reference N`
    headings."""
    rows: list[list[str]] = []

    # Find the at-a-glance table. We look for a line like
    # "| # | Project name | Owner | Contract value | Completion year |"
    table_start = -1
    lines = text.splitlines()
    for idx, line in enumerate(lines):
        s = line.lower()
        if "|" in line and "project name" in s and ("owner" in s or "value" in s):
            table_start = idx
            break

    if table_start >= 0:
        # Skip header + separator rows; collect data rows until blank/non-pipe.
        for line in lines[table_start + 2:]:
            if not line.strip().startswith("|"):
                break
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if not cells or all(not c for c in cells):
                continue
            # Common shape: # | name | owner | value | completion | ... | why
            if len(cells) >= 5:
                row = [
                    cells[1],  # project
                    cells[2],  # owner
                    cells[3],  # value
                    cells[4],  # completion
                    cells[-1] if len(cells) > 5 else "",  # why/scope
                ]
                rows.append(row)
            if len(rows) >= max_rows:
                break

    if rows:
        return rows[:max_rows]

    # Fallback: walk H2 blocks like "Project Reference #1 — Hindu Temple".
    for h2_title, body in find_h2_blocks(text):
        if not re.search(r"project\s*reference\b|reference\s*\d+", h2_title, re.IGNORECASE):
            continue
        name = re.sub(r"^.*?[—-]\s*", "", h2_title).strip()
        owner = _grep_field(body, "Owner") or ""
        value = _grep_field(body, "Contract value") or ""
        completion = _grep_field(body, "Actual completion") or _grep_field(body, "Completion") or ""
        scope = _truncate(first_paragraph(body) or "", 220)
        rows.append([name, owner, value, completion, scope])
        if len(rows) >= max_rows:
            break

    return rows[:max_rows]


def _grep_field(body: str, field: str) -> str | None:
    """Return the value of a `| **Field** | value |` Markdown table cell."""
    pat = re.compile(
        r"\|\s*\*?\*?" + re.escape(field) + r"\*?\*?\s*\|\s*([^|]+?)\s*\|",
        re.IGNORECASE,
    )
    m = pat.search(body)
    if not m:
        return None
    return collapse_whitespace(m.group(1).strip().strip("`"))
