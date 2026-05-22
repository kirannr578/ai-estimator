"""Client-ready quote PDF builder (F12 + F15).

Public entry point: :func:`build_quote_pdf`.

We deliberately use ``reportlab`` (pure-Python, no system deps). The layout
favours Platypus flowables for body content and a custom ``Canvas`` subclass
for the running header / footer + "Page N of M" — the standard reportlab
recipe for page totals (you can't know N during the first pass, so the
canvas buffers pages, then stamps the total on a second pass).
"""

from __future__ import annotations

import logging
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.pdfgen.canvas import Canvas
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    Image,
    KeepTogether,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from .schemas import Estimate, QuoteConfig
from .takeoff import ProjectModel

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Page geometry + colors
# ---------------------------------------------------------------------------

PAGE_SIZE = LETTER
MARGIN = 0.75 * inch
CONTENT_WIDTH = PAGE_SIZE[0] - 2 * MARGIN

ACCENT = colors.HexColor("#1F4E78")        # matches the Excel header fill
ACCENT_LIGHT = colors.HexColor("#D9E1F2")
GREY_BORDER = colors.HexColor("#B8B8B8")
GREY_LIGHT = colors.HexColor("#F2F2F2")
TEXT_DIM = colors.HexColor("#555555")


# ---------------------------------------------------------------------------
# Numbered canvas: stamps "Page N of M" + running header/footer on every page
# ---------------------------------------------------------------------------


class _NumberedCanvas(Canvas):
    """Two-pass canvas: collects page state, then stamps totals on save."""

    def __init__(self, *args, header_left: str = "", footer_center: str = "", **kwargs):
        super().__init__(*args, **kwargs)
        self._saved_states: list[dict] = []
        self._header_left = header_left
        self._footer_center = footer_center

    def showPage(self) -> None:                 # noqa: N802 (reportlab API)
        self._saved_states.append(dict(self.__dict__))
        self._startPage()

    def save(self) -> None:
        total_pages = len(self._saved_states)
        for state in self._saved_states:
            self.__dict__.update(state)
            self._draw_header_footer(total_pages)
            super().showPage()
        super().save()

    def _draw_header_footer(self, total_pages: int) -> None:
        page_num = self._pageNumber
        w, h = PAGE_SIZE

        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(TEXT_DIM)

        # Header
        if self._header_left:
            self.drawString(MARGIN, h - 0.4 * inch, self._header_left)
        self.drawRightString(
            w - MARGIN,
            h - 0.4 * inch,
            f"Page {page_num} of {total_pages}",
        )
        self.setStrokeColor(GREY_BORDER)
        self.setLineWidth(0.3)
        self.line(MARGIN, h - 0.45 * inch, w - MARGIN, h - 0.45 * inch)

        # Footer
        self.line(MARGIN, 0.55 * inch, w - MARGIN, 0.55 * inch)
        self.drawCentredString(w / 2.0, 0.4 * inch, self._footer_center)

        self.restoreState()


def _canvas_factory(header_left: str, footer_center: str):
    """Return a Canvas subclass closed over the header/footer strings."""

    class _BoundCanvas(_NumberedCanvas):
        def __init__(self, *args, **kwargs):
            super().__init__(
                *args,
                header_left=header_left,
                footer_center=footer_center,
                **kwargs,
            )

    return _BoundCanvas


# ---------------------------------------------------------------------------
# Style helpers
# ---------------------------------------------------------------------------


def _styles() -> dict[str, ParagraphStyle]:
    base = getSampleStyleSheet()
    return {
        "title": ParagraphStyle(
            "Title",
            parent=base["Title"],
            fontName="Helvetica-Bold",
            fontSize=26,
            leading=30,
            textColor=ACCENT,
            alignment=TA_LEFT,
            spaceAfter=10,
        ),
        "h1": ParagraphStyle(
            "H1",
            parent=base["Heading1"],
            fontName="Helvetica-Bold",
            fontSize=16,
            leading=20,
            textColor=ACCENT,
            spaceBefore=14,
            spaceAfter=8,
        ),
        "h2": ParagraphStyle(
            "H2",
            parent=base["Heading2"],
            fontName="Helvetica-Bold",
            fontSize=12,
            leading=15,
            textColor=ACCENT,
            spaceBefore=8,
            spaceAfter=4,
        ),
        "body": ParagraphStyle(
            "Body",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            spaceAfter=6,
        ),
        "body_small": ParagraphStyle(
            "BodySmall",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=TEXT_DIM,
        ),
        "body_right": ParagraphStyle(
            "BodyRight",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=10,
            leading=13,
            alignment=TA_RIGHT,
        ),
        "big_money": ParagraphStyle(
            "BigMoney",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "tile_label": ParagraphStyle(
            "TileLabel",
            parent=base["BodyText"],
            fontName="Helvetica",
            fontSize=9,
            leading=11,
            textColor=TEXT_DIM,
            alignment=TA_CENTER,
        ),
        "tile_value": ParagraphStyle(
            "TileValue",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=ACCENT,
            alignment=TA_CENTER,
        ),
        "kicker": ParagraphStyle(
            "Kicker",
            parent=base["BodyText"],
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=14,
            textColor=ACCENT,
            spaceAfter=4,
        ),
    }


def _money(v: Optional[float]) -> str:
    if v is None:
        return ""
    return f"${v:,.2f}"


def _safe(s: Optional[str], placeholder: str = "—") -> str:
    s = (s or "").strip()
    return s if s else placeholder


def _resolve_quote_number(meta_quote_number: str, project_name: str) -> str:
    if meta_quote_number and meta_quote_number.upper() != "AUTO":
        return meta_quote_number
    slug = "".join(c if c.isalnum() else "-" for c in (project_name or "QUOTE")).strip("-")
    slug = slug[:20].upper() or "QUOTE"
    return f"{slug}-{date.today().strftime('%Y%m%d')}"


# ---------------------------------------------------------------------------
# Section builders
# ---------------------------------------------------------------------------


def _cover_page(
    estimate: Estimate,
    project: ProjectModel,
    cfg: QuoteConfig,
    styles: dict[str, ParagraphStyle],
    quote_number: str,
    valid_until: date,
) -> list:
    company = cfg.company
    client = cfg.client
    pi = project.project_info

    # Top band: logo (left) + company info (right)
    logo_cell: object = ""
    if company.logo_path:
        logo_path = Path(company.logo_path)
        if logo_path.is_file():
            try:
                logo_cell = Image(str(logo_path), width=1.6 * inch, height=1.0 * inch, kind="proportional")
            except Exception as exc:
                logger.warning("Could not load logo at %s: %s", logo_path, exc)
                logo_cell = ""
        else:
            logger.warning("Logo path does not exist, skipping: %s", logo_path)

    company_lines = [
        f"<b>{_safe(company.name)}</b>",
    ]
    if company.address_line_1:
        company_lines.append(company.address_line_1)
    if company.address_line_2:
        company_lines.append(company.address_line_2)
    if company.phone:
        company_lines.append(f"Phone: {company.phone}")
    if company.email:
        company_lines.append(f"Email: {company.email}")
    if company.website:
        company_lines.append(company.website)
    if company.license_number:
        company_lines.append(f"License #: {company.license_number}")
    company_block = Paragraph("<br/>".join(company_lines), styles["body_right"])

    header_table = Table(
        [[logo_cell, company_block]],
        colWidths=[CONTENT_WIDTH * 0.45, CONTENT_WIDTH * 0.55],
    )
    header_table.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                ("TOPPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )

    project_name = estimate.project_name or _safe(pi.name)

    project_rows = [
        ["Project:", _safe(project_name)],
        ["Project #:", _safe(pi.number)],
        ["Location:", _safe(pi.location)],
        ["Quote #:", quote_number],
        ["Issued:", date.today().strftime("%B %d, %Y")],
        ["Valid until:", valid_until.strftime("%B %d, %Y")],
    ]
    project_tbl = Table(project_rows, colWidths=[1.3 * inch, CONTENT_WIDTH - 1.3 * inch])
    project_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("TEXTCOLOR", (0, 0), (0, -1), TEXT_DIM),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ]
        )
    )

    client_lines = []
    if client.name:
        client_lines.append(f"<b>{client.name}</b>")
    if client.contact_name:
        client_lines.append(f"Attn: {client.contact_name}")
    if client.address_line_1:
        client_lines.append(client.address_line_1)
    if client.address_line_2:
        client_lines.append(client.address_line_2)
    if client.phone:
        client_lines.append(f"Phone: {client.phone}")
    if client.email:
        client_lines.append(f"Email: {client.email}")
    if not client_lines:
        client_lines.append("<i>Client information to be filled in.</i>")

    flow: list = [
        header_table,
        Spacer(1, 0.4 * inch),
        Paragraph("PROJECT PROPOSAL", styles["title"]),
        Spacer(1, 0.05 * inch),
        Paragraph(
            "Prepared in good faith based on the documents and scope shared "
            "to date. Subject to the terms and conditions on the final pages "
            "of this proposal.",
            styles["body_small"],
        ),
        Spacer(1, 0.35 * inch),
        Paragraph("Prepared for", styles["kicker"]),
        Paragraph("<br/>".join(client_lines), styles["body"]),
        Spacer(1, 0.25 * inch),
        Paragraph("Project details", styles["kicker"]),
        project_tbl,
    ]
    return flow


def _executive_summary(
    estimate: Estimate, cfg: QuoteConfig, styles: dict[str, ParagraphStyle]
) -> list:
    flow: list = [PageBreak(), Paragraph("Executive summary", styles["h1"])]

    flow.append(
        Paragraph(
            f"<b>Total contract value</b><br/>{_money(estimate.grand_total)}",
            styles["big_money"],
        )
    )
    flow.append(Spacer(1, 0.15 * inch))

    if cfg.quote_meta.scope_blurb:
        flow.append(Paragraph(cfg.quote_meta.scope_blurb, styles["body"]))
        flow.append(Spacer(1, 0.15 * inch))

    by_cat = estimate.by_cost_category
    tiles_data = [
        ("Labor", by_cat.get("labor", 0.0)),
        ("Material", by_cat.get("material", 0.0)),
        ("Subcontractor", by_cat.get("subcontractor", 0.0)),
    ]
    tile_cells = []
    for label, amount in tiles_data:
        tile_cells.append(
            [
                Paragraph(label.upper(), styles["tile_label"]),
                Paragraph(_money(amount), styles["tile_value"]),
            ]
        )
    # Render as a single row of 3 nested tables
    tiles_row = Table(
        [[Table([row], colWidths=[(CONTENT_WIDTH / 3) - 0.1 * inch]) for row in [
            [Paragraph(label.upper(), styles["tile_label"])] for label, _ in tiles_data
        ]]],
        colWidths=[CONTENT_WIDTH / 3] * 3,
    )
    # Simpler: build a single 3-column table where each cell stacks label/value
    cell_inner = []
    for label, amount in tiles_data:
        cell_inner.append(
            [
                Paragraph(label.upper(), styles["tile_label"]),
                Spacer(1, 4),
                Paragraph(_money(amount), styles["tile_value"]),
            ]
        )
    tiles_row = Table([cell_inner], colWidths=[CONTENT_WIDTH / 3] * 3, rowHeights=[0.85 * inch])
    tiles_row.setStyle(
        TableStyle(
            [
                ("BOX", (0, 0), (-1, -1), 0.5, GREY_BORDER),
                ("INNERGRID", (0, 0), (-1, -1), 0.5, GREY_BORDER),
                ("BACKGROUND", (0, 0), (-1, -1), GREY_LIGHT),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ALIGN", (0, 0), (-1, -1), "CENTER"),
                ("TOPPADDING", (0, 0), (-1, -1), 10),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
            ]
        )
    )
    flow.append(tiles_row)
    flow.append(Spacer(1, 0.15 * inch))

    # Project totals breakdown
    totals_rows = [
        ["Subtotal", _money(estimate.subtotal)],
        [f"Contingency ({estimate.contingency_pct:.1f}%)", _money(estimate.contingency)],
        [f"Overhead ({estimate.overhead_pct:.1f}%)", _money(estimate.overhead)],
        [f"Profit ({estimate.profit_pct:.1f}%)", _money(estimate.profit)],
        ["Grand total", _money(estimate.grand_total)],
    ]
    totals_tbl = Table(totals_rows, colWidths=[CONTENT_WIDTH * 0.7, CONTENT_WIDTH * 0.3])
    totals_tbl.setStyle(
        TableStyle(
            [
                ("FONTNAME", (0, 0), (-1, -2), "Helvetica"),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 10),
                ("ALIGN", (1, 0), (1, -1), "RIGHT"),
                ("LINEABOVE", (0, -1), (-1, -1), 1, ACCENT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
                ("TEXTCOLOR", (0, -1), (-1, -1), ACCENT),
            ]
        )
    )
    flow.append(Spacer(1, 0.1 * inch))
    flow.append(totals_tbl)
    return flow


def _csi_division_table(
    estimate: Estimate, csi_titles: dict[str, str], styles: dict[str, ParagraphStyle]
) -> list:
    flow: list = [
        PageBreak(),
        Paragraph("Cost breakdown by CSI division", styles["h1"]),
    ]
    by_div = estimate.by_division
    if not by_div:
        flow.append(Paragraph("No priced line items.", styles["body"]))
        return flow

    subtotal = estimate.subtotal or 0.0
    rows = [["Div", "Description", "Subtotal", "% of total"]]
    for div in sorted(by_div):
        total = by_div[div]
        pct = (total / subtotal * 100.0) if subtotal else 0.0
        rows.append([div, csi_titles.get(div, ""), _money(total), f"{pct:.1f}%"])
    rows.append(["", "Total", _money(subtotal), "100.0%"])

    col_widths = [
        0.7 * inch,
        CONTENT_WIDTH - 0.7 * inch - 1.4 * inch - 1.0 * inch,
        1.4 * inch,
        1.0 * inch,
    ]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (2, 1), (3, -1), "RIGHT"),
                ("ALIGN", (0, 0), (0, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.3, GREY_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GREY_LIGHT]),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), ACCENT_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    flow.append(tbl)
    return flow


def _cost_category_table(estimate: Estimate, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = [
        Spacer(1, 0.25 * inch),
        Paragraph("Cost breakdown by category", styles["h2"]),
    ]
    by_cat = estimate.by_cost_category
    if not by_cat:
        flow.append(Paragraph("No category data.", styles["body"]))
        return flow

    subtotal = estimate.subtotal or 0.0
    rows = [["Category", "Subtotal", "% of total"]]
    for cat, total in sorted(by_cat.items(), key=lambda kv: -kv[1]):
        pct = (total / subtotal * 100.0) if subtotal else 0.0
        rows.append([cat.title(), _money(total), f"{pct:.1f}%"])
    rows.append(["Total", _money(subtotal), "100.0%"])

    col_widths = [CONTENT_WIDTH - 2.4 * inch, 1.4 * inch, 1.0 * inch]
    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    tbl.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("ALIGN", (1, 1), (2, -1), "RIGHT"),
                ("GRID", (0, 0), (-1, -1), 0.3, GREY_BORDER),
                ("ROWBACKGROUNDS", (0, 1), (-1, -2), [colors.white, GREY_LIGHT]),
                ("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold"),
                ("BACKGROUND", (0, -1), (-1, -1), ACCENT_LIGHT),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    flow.append(tbl)
    return flow


def _scope_coverage(project: ProjectModel, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = [PageBreak(), Paragraph("Scope coverage", styles["h1"])]
    inc = list(getattr(project, "aggregated_inclusions", []) or [])
    exc = list(getattr(project, "aggregated_exclusions", []) or [])
    if not inc and not exc:
        flow.append(
            Paragraph(
                "Scope coverage not yet captured. Run the analyzer against the "
                "trade bid packages to populate aggregated inclusions / exclusions.",
                styles["body"],
            )
        )
        return flow

    flow.append(
        Paragraph(
            "Inclusions and exclusions are deduplicated across all trade bid "
            "packages analysed for this project.",
            styles["body_small"],
        )
    )
    flow.append(Spacer(1, 0.1 * inch))

    inc_cells = [Paragraph(f"\u2022 {it.text}", styles["body"]) for it in inc[:50]] or [
        Paragraph("<i>None recorded.</i>", styles["body_small"])
    ]
    exc_cells = [Paragraph(f"\u2022 {it.text}", styles["body"]) for it in exc[:50]] or [
        Paragraph("<i>None recorded.</i>", styles["body_small"])
    ]
    header_row = [
        Paragraph(f"<b>Inclusions ({len(inc)})</b>", styles["h2"]),
        Paragraph(f"<b>Exclusions ({len(exc)})</b>", styles["h2"]),
    ]
    body_row = [
        [*inc_cells],
        [*exc_cells],
    ]
    tbl = Table(
        [header_row, body_row],
        colWidths=[CONTENT_WIDTH / 2, CONTENT_WIDTH / 2],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, -1), 6),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT_LIGHT),
                ("BOX", (0, 0), (-1, -1), 0.5, GREY_BORDER),
                ("LINEAFTER", (0, 0), (0, -1), 0.5, GREY_BORDER),
            ]
        )
    )
    flow.append(tbl)

    truncated = max(0, len(inc) - 50) + max(0, len(exc) - 50)
    if truncated:
        flow.append(Spacer(1, 0.05 * inch))
        flow.append(
            Paragraph(
                f"<i>{truncated} additional line(s) omitted for brevity; see the "
                f"full Scope Coverage sheet in the Excel export.</i>",
                styles["body_small"],
            )
        )
    return flow


def _alternates_and_unit_prices(
    project: ProjectModel, styles: dict[str, ParagraphStyle]
) -> list:
    flow: list = []
    has_any = any(
        bool(p.alternates) or bool(p.unit_prices) for p in project.bid_packages
    )
    if not has_any:
        return flow

    flow.append(PageBreak())
    flow.append(Paragraph("Alternates and unit prices", styles["h1"]))

    for p in sorted(project.bid_packages, key=lambda x: x.package_number or x.pdf_name):
        if not (p.alternates or p.unit_prices):
            continue
        title_bits = []
        if p.package_number:
            title_bits.append(f"#{p.package_number}")
        if p.trade_name:
            title_bits.append(p.trade_name)
        title_bits.append(f"({p.pdf_name})")
        flow.append(Paragraph(" \u2022 ".join(title_bits), styles["h2"]))

        if p.alternates:
            rows = [["Alt #", "Description", "Add/Deduct", "Amount"]]
            for a in p.alternates:
                rows.append(
                    [
                        a.number or "",
                        Paragraph(a.description or "", styles["body"]),
                        a.add_or_deduct or "",
                        _money(a.amount) if a.amount is not None else "",
                    ]
                )
            tbl = Table(
                rows,
                colWidths=[0.7 * inch, CONTENT_WIDTH - 0.7 * inch - 1.1 * inch - 1.1 * inch, 1.1 * inch, 1.1 * inch],
                repeatRows=1,
            )
            tbl.setStyle(_grid_style())
            flow.append(tbl)
            flow.append(Spacer(1, 0.08 * inch))

        if p.unit_prices:
            rows = [["Description", "Unit", "Amount"]]
            for u in p.unit_prices:
                rows.append(
                    [
                        Paragraph(u.description or "", styles["body"]),
                        u.unit or "",
                        _money(u.amount) if u.amount is not None else "",
                    ]
                )
            tbl = Table(
                rows,
                colWidths=[CONTENT_WIDTH - 2.2 * inch, 1.1 * inch, 1.1 * inch],
                repeatRows=1,
            )
            tbl.setStyle(_grid_style())
            flow.append(tbl)
            flow.append(Spacer(1, 0.15 * inch))

    return flow


def _grid_style() -> TableStyle:
    return TableStyle(
        [
            ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
            ("GRID", (0, 0), (-1, -1), 0.3, GREY_BORDER),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, GREY_LIGHT]),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]
    )


def _payment_schedule(
    estimate: Estimate, cfg: QuoteConfig, styles: dict[str, ParagraphStyle]
) -> list:
    flow: list = [PageBreak(), Paragraph("Payment schedule", styles["h1"])]
    sched = cfg.payment_schedule
    contract_total = estimate.grand_total or 0.0

    if not sched.milestones:
        flow.append(Paragraph("No payment milestones configured.", styles["body"]))
        return flow

    if sched.mode == "percentage":
        rows = [["Milestone", "% of contract", "Amount", "Notes"]]
        running = 0.0
        for m in sched.milestones:
            pct = float(m.percentage or 0.0)
            amount = round(contract_total * pct / 100.0, 2)
            running += amount
            rows.append(
                [
                    Paragraph(m.label, styles["body"]),
                    f"{pct:.1f}%",
                    _money(amount),
                    Paragraph(m.notes or "", styles["body_small"]),
                ]
            )
        rows.append(["Total", "100.0%", _money(contract_total), ""])
        col_widths = [
            CONTENT_WIDTH * 0.30,
            CONTENT_WIDTH * 0.15,
            CONTENT_WIDTH * 0.20,
            CONTENT_WIDTH * 0.35,
        ]
    else:
        rows = [["Milestone", "Amount", "Notes"]]
        total_amt = 0.0
        for m in sched.milestones:
            amt = float(m.amount or 0.0)
            total_amt += amt
            rows.append(
                [
                    Paragraph(m.label, styles["body"]),
                    _money(amt),
                    Paragraph(m.notes or "", styles["body_small"]),
                ]
            )
        rows.append(["Total", _money(total_amt), ""])
        col_widths = [
            CONTENT_WIDTH * 0.35,
            CONTENT_WIDTH * 0.20,
            CONTENT_WIDTH * 0.45,
        ]

    tbl = Table(rows, colWidths=col_widths, repeatRows=1)
    style = _grid_style()
    style.add("FONTNAME", (0, -1), (-1, -1), "Helvetica-Bold")
    style.add("BACKGROUND", (0, -1), (-1, -1), ACCENT_LIGHT)
    tbl.setStyle(style)
    flow.append(tbl)

    # Validation warnings for milestone mode
    if sched.mode == "milestone":
        warnings = sched.validate_against_total(contract_total)
        for w in warnings:
            flow.append(Spacer(1, 0.05 * inch))
            flow.append(
                Paragraph(
                    f"<i>Note: {w}</i>",
                    styles["body_small"],
                )
            )

    terms = cfg.quote_meta.payment_terms_text
    if terms:
        flow.append(Spacer(1, 0.15 * inch))
        flow.append(Paragraph(terms, styles["body_small"]))
    return flow


def _terms_and_conditions(cfg: QuoteConfig, styles: dict[str, ParagraphStyle]) -> list:
    text = (cfg.terms_text or "").strip()
    if not text:
        return []
    flow: list = [PageBreak(), Paragraph("Terms and conditions", styles["h1"])]
    # Preserve blank-line paragraph breaks
    for chunk in text.split("\n\n"):
        chunk = chunk.strip()
        if not chunk:
            continue
        # Replace single newlines inside a paragraph with line breaks so the
        # author's intent is preserved.
        chunk_html = chunk.replace("\n", "<br/>")
        flow.append(Paragraph(chunk_html, styles["body"]))
    return flow


def _signature_block(cfg: QuoteConfig, styles: dict[str, ParagraphStyle]) -> list:
    flow: list = [
        PageBreak(),
        Paragraph("Acceptance and signatures", styles["h1"]),
        Paragraph(
            "By signing below, both parties agree to the scope, pricing, "
            "payment schedule, and terms set out in this proposal.",
            styles["body"],
        ),
        Spacer(1, 0.4 * inch),
    ]

    def _sig_column(heading: str, name_default: str = "") -> list:
        return [
            Paragraph(heading, styles["kicker"]),
            Spacer(1, 0.5 * inch),
            Paragraph("_______________________________", styles["body"]),
            Paragraph("Signature", styles["body_small"]),
            Spacer(1, 0.25 * inch),
            Paragraph("_______________________________", styles["body"]),
            Paragraph(f"Name{(' / ' + name_default) if name_default else ''}", styles["body_small"]),
            Spacer(1, 0.25 * inch),
            Paragraph("_______________________________", styles["body"]),
            Paragraph("Date", styles["body_small"]),
        ]

    company_col = _sig_column("Contractor", cfg.company.name or "")
    client_col = _sig_column("Client", cfg.client.name or "")

    tbl = Table(
        [[company_col, client_col]],
        colWidths=[CONTENT_WIDTH / 2 - 0.15 * inch, CONTENT_WIDTH / 2 - 0.15 * inch],
    )
    tbl.setStyle(
        TableStyle(
            [
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 0),
                ("RIGHTPADDING", (0, 0), (-1, -1), 0),
            ]
        )
    )
    flow.append(KeepTogether(tbl))
    return flow


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_quote_pdf(
    estimate: Estimate,
    project: ProjectModel,
    quote_config: QuoteConfig,
    out_path: Path,
    *,
    csi_titles: Optional[dict[str, str]] = None,
) -> Path:
    """Build a client-ready proposal PDF and return the written path.

    Args:
        estimate: priced estimate (totals + line items).
        project: reconciled project model (for scope coverage + alternates).
        quote_config: branding + payment schedule.
        out_path: where to write the PDF (parents are created if missing).
        csi_titles: optional CSI division titles for the breakdown table; if
            omitted, division codes are shown without descriptions.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    csi_titles = csi_titles or {}

    styles = _styles()
    valid_until = date.today() + timedelta(days=quote_config.quote_meta.valid_until_days)
    quote_number = _resolve_quote_number(
        quote_config.quote_meta.quote_number, estimate.project_name
    )

    story: list = []
    story.extend(
        _cover_page(estimate, project, quote_config, styles, quote_number, valid_until)
    )
    story.extend(_executive_summary(estimate, quote_config, styles))
    story.extend(_csi_division_table(estimate, csi_titles, styles))
    story.extend(_cost_category_table(estimate, styles))
    story.extend(_scope_coverage(project, styles))
    story.extend(_alternates_and_unit_prices(project, styles))
    story.extend(_payment_schedule(estimate, quote_config, styles))
    story.extend(_terms_and_conditions(quote_config, styles))
    story.extend(_signature_block(quote_config, styles))

    header_left = quote_config.company.name or estimate.project_name or ""
    footer_center = "Confidential — do not distribute"

    doc = BaseDocTemplate(
        str(out_path),
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN,
        rightMargin=MARGIN,
        topMargin=MARGIN,
        bottomMargin=MARGIN,
        title=f"Project Proposal — {estimate.project_name}",
        author=quote_config.company.name or "Estimator",
    )
    frame = Frame(
        MARGIN,
        MARGIN,
        CONTENT_WIDTH,
        PAGE_SIZE[1] - 2 * MARGIN,
        leftPadding=0,
        rightPadding=0,
        topPadding=0,
        bottomPadding=0,
        id="content",
    )
    doc.addPageTemplates([PageTemplate(id="main", frames=[frame])])
    doc.build(story, canvasmaker=_canvas_factory(header_left, footer_center))

    return out_path
