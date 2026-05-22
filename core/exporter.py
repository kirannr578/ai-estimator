"""Export the priced `Estimate` and supporting data to Excel and JSON."""

from __future__ import annotations

import json
from io import BytesIO
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

from .schemas import Estimate
from .takeoff import ProjectModel


HEADER_FILL = PatternFill("solid", fgColor="1F4E78")
HEADER_FONT = Font(bold=True, color="FFFFFF")
DIVISION_FILL = PatternFill("solid", fgColor="D9E1F2")
SUPPRESSED_FILL = PatternFill("solid", fgColor="F2F2F2")  # light grey for unit-mismatch rows
SUPPRESSED_FONT = Font(italic=True, color="808080")


def _autosize(ws, max_width: int = 60) -> None:
    for col in ws.columns:
        col_letter = get_column_letter(col[0].column)
        longest = max((len(str(c.value)) if c.value is not None else 0) for c in col)
        ws.column_dimensions[col_letter].width = min(max(longest + 2, 10), max_width)


def _write_header(ws, row: int, headers: list[str]) -> None:
    for i, h in enumerate(headers, start=1):
        cell = ws.cell(row=row, column=i, value=h)
        cell.fill = HEADER_FILL
        cell.font = HEADER_FONT
        cell.alignment = Alignment(vertical="center")


def export_estimate_xlsx(
    estimate: Estimate,
    project: ProjectModel,
    csi_titles: dict[str, str],
) -> bytes:
    wb = Workbook()

    # ----- Summary -----
    ws = wb.active
    ws.title = "Summary"
    ws["A1"] = "Project"
    ws["B1"] = estimate.project_name
    ws["A1"].font = Font(bold=True, size=14)

    ws["A3"] = "Region multiplier"
    ws["B3"] = estimate.region_multiplier

    ws["A5"] = "Subtotal";    ws["B5"] = estimate.subtotal;     ws["B5"].number_format = "$#,##0.00"
    ws["A6"] = f"Contingency ({estimate.contingency_pct:.1f}%)"
    ws["B6"] = estimate.contingency; ws["B6"].number_format = "$#,##0.00"
    ws["A7"] = f"Overhead ({estimate.overhead_pct:.1f}%)"
    ws["B7"] = estimate.overhead;    ws["B7"].number_format = "$#,##0.00"
    ws["A8"] = f"Profit ({estimate.profit_pct:.1f}%)"
    ws["B8"] = estimate.profit;      ws["B8"].number_format = "$#,##0.00"
    ws["A9"] = "GRAND TOTAL"
    ws["A9"].font = Font(bold=True, size=12)
    ws["B9"] = estimate.grand_total
    ws["B9"].number_format = "$#,##0.00"
    ws["B9"].font = Font(bold=True, size=12)

    ws["A11"] = "By CSI division"
    ws["A11"].font = Font(bold=True)
    _write_header(ws, 12, ["Div", "Title", "Subtotal"])
    row = 13
    for div in sorted(estimate.by_division):
        ws.cell(row=row, column=1, value=div)
        ws.cell(row=row, column=2, value=csi_titles.get(div, ""))
        c = ws.cell(row=row, column=3, value=estimate.by_division[div])
        c.number_format = "$#,##0.00"
        row += 1

    # By cost category rollup (labor / material / equipment / sub / other)
    row += 1
    by_cat = estimate.by_cost_category
    if by_cat:
        ws.cell(row=row, column=1, value="By cost category").font = Font(bold=True)
        row += 1
        _write_header(ws, row, ["Category", "Subtotal", "% of subtotal"])
        row += 1
        subtotal = estimate.subtotal or 0.0
        for cat, total in sorted(by_cat.items(), key=lambda kv: -kv[1]):
            ws.cell(row=row, column=1, value=cat.title())
            c_total = ws.cell(row=row, column=2, value=total)
            c_total.number_format = "$#,##0.00"
            pct = (total / subtotal * 100.0) if subtotal else 0.0
            c_pct = ws.cell(row=row, column=3, value=round(pct, 2))
            c_pct.number_format = "0.00\"%\""
            row += 1

    _autosize(ws)

    # ----- Line items -----
    ws = wb.create_sheet("Line Items")
    headers = [
        "Div", "CSI Section", "Category", "Description",
        "Raw Qty", "Waste", "Quantity", "Unit",
        "Unit Cost", "Total", "Suppressed", "Confidence", "Source Sheets",
        "Cost-DB Key", "Notes",
    ]
    _write_header(ws, 1, headers)

    last_div = None
    row = 2
    for li in estimate.line_items:
        if li.csi_division != last_div:
            ws.cell(row=row, column=1, value=f"Division {li.csi_division} - {csi_titles.get(li.csi_division, '')}").fill = DIVISION_FILL
            for col in range(2, len(headers) + 1):
                ws.cell(row=row, column=col).fill = DIVISION_FILL
            ws.cell(row=row, column=1).font = Font(bold=True)
            last_div = li.csi_division
            row += 1

        cat_val = li.cost_category.value if hasattr(li.cost_category, "value") else str(li.cost_category)
        ws.cell(row=row, column=1, value=li.csi_division)
        ws.cell(row=row, column=2, value=li.csi_section or "")
        ws.cell(row=row, column=3, value=cat_val)
        ws.cell(row=row, column=4, value=li.description)
        ws.cell(row=row, column=5, value=li.raw_quantity if li.raw_quantity is not None else li.quantity).number_format = "#,##0.00"
        ws.cell(row=row, column=6, value=li.waste_factor).number_format = "0.00"
        ws.cell(row=row, column=7, value=li.quantity).number_format = "#,##0.00"
        ws.cell(row=row, column=8, value=li.unit)
        ws.cell(row=row, column=9, value=li.unit_cost).number_format = "$#,##0.00"
        ws.cell(row=row, column=10, value=li.total_cost).number_format = "$#,##0.00"
        ws.cell(row=row, column=11, value="YES" if li.suppressed else "")
        ws.cell(row=row, column=12, value=li.confidence).number_format = "0.00"
        ws.cell(row=row, column=13, value=", ".join(li.source_sheet_ids))
        ws.cell(row=row, column=14, value=li.cost_source)
        ws.cell(row=row, column=15, value=li.notes or "")

        if li.suppressed:
            # Grey-shade the entire row and italicize so the reader sees at a
            # glance that this line did NOT roll into the totals below.
            for col in range(1, len(headers) + 1):
                cell = ws.cell(row=row, column=col)
                cell.fill = SUPPRESSED_FILL
                cell.font = SUPPRESSED_FONT
        row += 1

    ws.freeze_panes = "A2"
    _autosize(ws)

    # ----- Rooms -----
    if project.rooms:
        ws = wb.create_sheet("Rooms")
        headers = ["Number", "Name", "Area (SF)", "Perimeter (LF)", "Ceiling (FT)",
                   "Floor", "Base", "Walls", "Ceiling", "Source"]
        _write_header(ws, 1, headers)
        for i, r in enumerate(project.rooms, start=2):
            ws.cell(row=i, column=1, value=r.number or "")
            ws.cell(row=i, column=2, value=r.name)
            ws.cell(row=i, column=3, value=r.area_sqft).number_format = "#,##0.00"
            ws.cell(row=i, column=4, value=r.perimeter_ft).number_format = "#,##0.00"
            ws.cell(row=i, column=5, value=r.ceiling_height_ft)
            ws.cell(row=i, column=6, value=r.floor_finish or "")
            ws.cell(row=i, column=7, value=r.base_finish or "")
            ws.cell(row=i, column=8, value=r.wall_finish or "")
            ws.cell(row=i, column=9, value=r.ceiling_finish or "")
            ws.cell(row=i, column=10, value=r.source_sheet_id or "")
        ws.freeze_panes = "A2"
        _autosize(ws)

    # ----- Doors / Windows -----
    if project.doors:
        ws = wb.create_sheet("Doors")
        _write_header(ws, 1, ["Mark", "Type", "W (in)", "H (in)", "Rating", "Hardware", "Notes", "Source"])
        for i, d in enumerate(project.doors, start=2):
            ws.cell(row=i, column=1, value=d.mark)
            ws.cell(row=i, column=2, value=d.type or "")
            ws.cell(row=i, column=3, value=d.width_in)
            ws.cell(row=i, column=4, value=d.height_in)
            ws.cell(row=i, column=5, value=d.rating or "")
            ws.cell(row=i, column=6, value=d.hardware_set or "")
            ws.cell(row=i, column=7, value=d.notes or "")
            ws.cell(row=i, column=8, value=d.source_sheet_id or "")
        ws.freeze_panes = "A2"
        _autosize(ws)

    if project.windows:
        ws = wb.create_sheet("Windows")
        _write_header(ws, 1, ["Mark", "Type", "W (in)", "H (in)", "Glazing", "Notes", "Source"])
        for i, w in enumerate(project.windows, start=2):
            ws.cell(row=i, column=1, value=w.mark)
            ws.cell(row=i, column=2, value=w.type or "")
            ws.cell(row=i, column=3, value=w.width_in)
            ws.cell(row=i, column=4, value=w.height_in)
            ws.cell(row=i, column=5, value=w.glazing or "")
            ws.cell(row=i, column=6, value=w.notes or "")
            ws.cell(row=i, column=7, value=w.source_sheet_id or "")
        ws.freeze_panes = "A2"
        _autosize(ws)

    # ----- Project Info -----
    pi = project.project_info
    if pi and (pi.name or pi.number):
        ws = wb.create_sheet("Project Info", 0)
        ws["A1"] = "Project Information"
        ws["A1"].font = Font(bold=True, size=14)
        rows = [
            ("Project name",     pi.name or ""),
            ("Project number",   pi.number or ""),
            ("Location",         pi.location or ""),
            ("Owner",            pi.owner or ""),
            ("Contractor / GC",  pi.contractor or ""),
            ("Bid due",          pi.bid_due or ""),
            ("Source PDFs",      ", ".join(pi.sources or [])),
        ]
        for i, (k, v) in enumerate(rows, start=3):
            c1 = ws.cell(row=i, column=1, value=k); c1.font = Font(bold=True)
            ws.cell(row=i, column=2, value=v)
        _autosize(ws, max_width=80)

    # ----- Bid Packages -----
    if project.bid_packages:
        ws = wb.create_sheet("Bid Packages")
        headers = [
            "Pkg #", "Trade", "PDF", "Project", "Project #",
            "CSI Divs", "CSI Sections",
            "# Inclusions", "# Exclusions", "# Alternates", "# Unit Prices",
            "Refd Drawings", "Refd Specs", "Summary",
        ]
        _write_header(ws, 1, headers)
        for i, p in enumerate(sorted(project.bid_packages, key=lambda x: x.package_number or x.pdf_name), start=2):
            ws.cell(row=i, column=1, value=p.package_number or "")
            ws.cell(row=i, column=2, value=p.trade_name or "")
            ws.cell(row=i, column=3, value=p.pdf_name)
            ws.cell(row=i, column=4, value=p.project_name or "")
            ws.cell(row=i, column=5, value=p.project_number or "")
            ws.cell(row=i, column=6, value=", ".join(p.csi_divisions))
            ws.cell(row=i, column=7, value=", ".join(p.csi_sections))
            ws.cell(row=i, column=8, value=len(p.inclusions))
            ws.cell(row=i, column=9, value=len(p.exclusions))
            ws.cell(row=i, column=10, value=len(p.alternates))
            ws.cell(row=i, column=11, value=len(p.unit_prices))
            ws.cell(row=i, column=12, value=", ".join(p.referenced_drawings))
            ws.cell(row=i, column=13, value=", ".join(p.referenced_specs))
            ws.cell(row=i, column=14, value=p.summary or "").alignment = Alignment(wrap_text=True)
        ws.freeze_panes = "A2"
        _autosize(ws, max_width=80)

        # Detail sheet: one row per inclusion/exclusion/alternate/unit price
        ws = wb.create_sheet("Scope Matrix")
        _write_header(ws, 1, ["Pkg #", "Trade", "Type", "Detail", "Add/Deduct", "Unit", "Amount"])
        row = 2
        for p in sorted(project.bid_packages, key=lambda x: x.package_number or x.pdf_name):
            for inc in p.inclusions:
                ws.cell(row=row, column=1, value=p.package_number or "")
                ws.cell(row=row, column=2, value=p.trade_name or "")
                ws.cell(row=row, column=3, value="Inclusion")
                ws.cell(row=row, column=4, value=inc).alignment = Alignment(wrap_text=True)
                row += 1
            for exc in p.exclusions:
                ws.cell(row=row, column=1, value=p.package_number or "")
                ws.cell(row=row, column=2, value=p.trade_name or "")
                ws.cell(row=row, column=3, value="Exclusion")
                ws.cell(row=row, column=4, value=exc).alignment = Alignment(wrap_text=True)
                row += 1
            for a in p.alternates:
                ws.cell(row=row, column=1, value=p.package_number or "")
                ws.cell(row=row, column=2, value=p.trade_name or "")
                ws.cell(row=row, column=3, value=f"Alternate {a.number or ''}".strip())
                ws.cell(row=row, column=4, value=a.description).alignment = Alignment(wrap_text=True)
                ws.cell(row=row, column=5, value=a.add_or_deduct or "")
                if a.amount is not None:
                    ws.cell(row=row, column=7, value=a.amount).number_format = "$#,##0.00"
                row += 1
            for u in p.unit_prices:
                ws.cell(row=row, column=1, value=p.package_number or "")
                ws.cell(row=row, column=2, value=p.trade_name or "")
                ws.cell(row=row, column=3, value="Unit Price")
                ws.cell(row=row, column=4, value=u.description).alignment = Alignment(wrap_text=True)
                ws.cell(row=row, column=6, value=u.unit or "")
                if u.amount is not None:
                    ws.cell(row=row, column=7, value=u.amount).number_format = "$#,##0.00"
                row += 1
        ws.freeze_panes = "A2"
        _autosize(ws, max_width=100)

    # ----- Scope Coverage (aggregated inclusions / exclusions) -----
    agg_inc = getattr(project, "aggregated_inclusions", []) or []
    agg_exc = getattr(project, "aggregated_exclusions", []) or []
    if agg_inc or agg_exc:
        ws = wb.create_sheet("Scope Coverage")
        ws["A1"] = "Aggregated scope coverage"
        ws["A1"].font = Font(bold=True, size=14)
        ws["A2"] = (
            "Deduplicated across all bid packages. 'Source packages' shows "
            "every bid-package PDF whose inclusion/exclusion list contributed "
            "to this line."
        )
        ws["A2"].alignment = Alignment(wrap_text=True)

        row = 4
        ws.cell(row=row, column=1, value=f"Inclusions ({len(agg_inc)})").font = Font(bold=True, size=12)
        row += 1
        _write_header(ws, row, ["#", "Inclusion", "# Packages", "Source Packages"])
        row += 1
        for i, item in enumerate(agg_inc, start=1):
            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=2, value=item.text).alignment = Alignment(wrap_text=True)
            ws.cell(row=row, column=3, value=len(item.source_packages))
            ws.cell(row=row, column=4, value=", ".join(item.source_packages)).alignment = Alignment(wrap_text=True)
            row += 1

        row += 1
        ws.cell(row=row, column=1, value=f"Exclusions ({len(agg_exc)})").font = Font(bold=True, size=12)
        row += 1
        _write_header(ws, row, ["#", "Exclusion", "# Packages", "Source Packages"])
        row += 1
        for i, item in enumerate(agg_exc, start=1):
            ws.cell(row=row, column=1, value=i)
            ws.cell(row=row, column=2, value=item.text).alignment = Alignment(wrap_text=True)
            ws.cell(row=row, column=3, value=len(item.source_packages))
            ws.cell(row=row, column=4, value=", ".join(item.source_packages)).alignment = Alignment(wrap_text=True)
            row += 1

        _autosize(ws, max_width=100)

    # ----- Sheets analysed -----
    if project.sheet_summaries:
        ws = wb.create_sheet("Sheets")
        _write_header(ws, 1, ["Sheet", "Summary"])
        for i, (sid, summary) in enumerate(sorted(project.sheet_summaries.items()), start=2):
            ws.cell(row=i, column=1, value=sid)
            ws.cell(row=i, column=2, value=summary).alignment = Alignment(wrap_text=True)
        ws.freeze_panes = "A2"
        _autosize(ws, max_width=120)

    # ----- Warnings -----
    if project.warnings:
        ws = wb.create_sheet("Warnings")
        _write_header(ws, 1, ["#", "Warning"])
        for i, w in enumerate(project.warnings, start=2):
            ws.cell(row=i, column=1, value=i - 1)
            ws.cell(row=i, column=2, value=w).alignment = Alignment(wrap_text=True)
        _autosize(ws, max_width=120)

    out = BytesIO()
    wb.save(out)
    return out.getvalue()


def export_estimate_json(estimate: Estimate, project: ProjectModel) -> str:
    pi = project.project_info
    payload = {
        "project_name": estimate.project_name,
        "project_info": {
            "name":       pi.name,
            "number":     pi.number,
            "location":   pi.location,
            "owner":      pi.owner,
            "contractor": pi.contractor,
            "bid_due":    pi.bid_due,
            "sources":    pi.sources or [],
        },
        "region_multiplier": estimate.region_multiplier,
        "subtotal": estimate.subtotal,
        "contingency_pct": estimate.contingency_pct,
        "contingency": estimate.contingency,
        "overhead_pct": estimate.overhead_pct,
        "overhead": estimate.overhead,
        "profit_pct": estimate.profit_pct,
        "profit": estimate.profit,
        "grand_total": estimate.grand_total,
        "by_division": estimate.by_division,
        "by_cost_category": estimate.by_cost_category,
        "line_items": [li.model_dump() for li in estimate.line_items],
        "rooms":   [r.model_dump() for r in project.rooms],
        "doors":   [d.model_dump() for d in project.doors],
        "windows": [w.model_dump() for w in project.windows],
        "structural": [s.model_dump() for s in project.structural],
        "mep":        [m.model_dump() for m in project.mep],
        "spec_sections": [s.model_dump() for s in project.spec_sections],
        "site": project.site.model_dump(),
        "bid_packages": [p.model_dump() for p in project.bid_packages],
        "scope_matrix": {
            "by_division": {
                div: [p.pdf_name for p in pkgs]
                for div, pkgs in project.scope_matrix.by_division.items()
            },
            "all_alternates": [a.model_dump() for a in project.scope_matrix.all_alternates],
            "coverage_warnings": project.scope_matrix.coverage_warnings,
        },
        "aggregated_inclusions": [
            it.model_dump() for it in getattr(project, "aggregated_inclusions", []) or []
        ],
        "aggregated_exclusions": [
            it.model_dump() for it in getattr(project, "aggregated_exclusions", []) or []
        ],
        "sheet_summaries": project.sheet_summaries,
        "warnings": project.warnings,
    }
    return json.dumps(payload, indent=2, default=str)


def save_to_disk(content: bytes | str, path: str | Path) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, str):
        path.write_text(content, encoding="utf-8")
    else:
        path.write_bytes(content)
    return path
