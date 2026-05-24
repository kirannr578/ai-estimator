"""One-shot reader: pulls plain text from BPC source files for the firm profile.

This script is intentionally bounded:
- PDFs: extract text with pymupdf (no rasterization, no images).
- DOCX: stdlib zipfile + xml parsing of word/document.xml.
- XLSX: openpyxl, but only sheet names + header row + first 3 data rows per sheet.

It writes plain-text dumps to firm/_scripts/_extracted/ for the agent to read.
Nothing about row contents of Records/*.xlsx is written — only tab + header inventory.
"""
from __future__ import annotations

import json
import re
import sys
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import fitz  # pymupdf
import openpyxl

ROOT = Path(r"C:\Users\rnuduru1\OneDrive\Blueprint Constructs")
OUT = Path(__file__).parent / "_extracted"
OUT.mkdir(exist_ok=True)

W_NS = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"


def docx_text(path: Path) -> str:
    """Extract paragraph text from a .docx file using stdlib only."""
    out: list[str] = []
    with zipfile.ZipFile(path) as z:
        try:
            xml = z.read("word/document.xml").decode("utf-8")
        except KeyError:
            return ""
    root = ET.fromstring(xml)
    for p in root.iter(f"{W_NS}p"):
        texts = [t.text or "" for t in p.iter(f"{W_NS}t")]
        line = "".join(texts).strip()
        if line:
            out.append(line)
    return "\n".join(out)


def pdf_text(path: Path, max_pages: int = 20) -> str:
    """Extract text from up to max_pages of a PDF."""
    out: list[str] = []
    with fitz.open(path) as doc:
        for i, page in enumerate(doc):
            if i >= max_pages:
                out.append(f"\n[--- truncated at {max_pages} pages of {len(doc)} ---]")
                break
            out.append(f"\n--- page {i+1} ---\n")
            out.append(page.get_text("text"))
    return "".join(out)


def xlsx_summary(path: Path, max_rows: int = 3, body_redacted: bool = False) -> str:
    """Open an xlsx and return either a structured summary or a tab+header inventory."""
    wb = openpyxl.load_workbook(path, data_only=True, read_only=True)
    out: list[str] = [f"# Workbook: {path.name}"]
    for ws in wb.worksheets:
        out.append(f"\n## Sheet: {ws.title}")
        try:
            rows_iter = ws.iter_rows(values_only=True)
        except Exception as e:
            out.append(f"(could not iterate sheet: {e})")
            continue
        header = next(rows_iter, None)
        if header is not None:
            cleaned = [str(c) if c is not None else "" for c in header]
            out.append("Headers: " + " | ".join(cleaned))
        if body_redacted:
            out.append("(rows intentionally not extracted — PII policy)")
            continue
        for n, row in enumerate(rows_iter):
            if n >= max_rows:
                break
            cleaned = [str(c) if c is not None else "" for c in row]
            out.append("Row %d: %s" % (n + 1, " | ".join(cleaned)))
    wb.close()
    return "\n".join(out)


def safe_write(name: str, content: str) -> None:
    p = OUT / name
    p.write_text(content, encoding="utf-8", errors="replace")
    print(f"  wrote {p.relative_to(OUT.parent)} ({len(content)} chars)")


def main() -> int:
    print("Extracting BPC corporate docs...")
    bpc = ROOT / "BPC"

    # DOCX
    for name in ["BPC info.docx", "Rocky Business Profile.docx"]:
        p = bpc / name
        if p.exists():
            safe_write(p.stem + ".txt", docx_text(p))

    # Key PDFs (corporate marketing + cert + bond + COI)
    pdfs = [
        "Blueprint Constructs Capability Statement.pdf",
        "BPC Profile.pdf",
        "Bond Letter_RK Residential Homes and Commercial Constructions, LLC dba Blue Print Constructs.pdf",
        "BPC COI.pdf",
        "RK Residential Homes and Commercial Constructions LLC.pdf",
        "RK Residential Homes and Commercial Constructions LLC DBA Blueprint Constructs-Commercial GL-SBCC-042443-00.pdf",
        "HUB.pdf",
        "MBE.pdf",
        "SBE.pdf",
        "SBE RKRes 2023.pdf",
        "Texas HUB_Vendor NIGP Updates & Certificate_2021-08-05.pdf",
        "MBDA Services -What is MBDA.pdf",
        "Filled W9 Form - BPC.pdf",
    ]
    for name in pdfs:
        p = bpc / name
        if p.exists():
            safe_write(p.stem + ".txt", pdf_text(p))

    # XLSX — BPC Details only (corporate); Contacts.xlsx might contain PII, do header-only
    details = bpc / "BPC Details.xlsx"
    if details.exists():
        safe_write("BPC Details.xlsx.txt", xlsx_summary(details, max_rows=10))
    contacts = bpc / "Contacts.xlsx"
    if contacts.exists():
        safe_write("BPC_Contacts_xlsx_headers_only.txt", xlsx_summary(contacts, body_redacted=True))

    # Records — header-only inventory (PII policy)
    print("\nInventorying Records/ (header-only)...")
    records = ROOT / "Records"
    for child in records.iterdir():
        if child.suffix.lower() == ".xlsx":
            safe_write(
                f"Records__{child.stem}__headers_only.txt",
                xlsx_summary(child, body_redacted=True),
            )

    # Dallas County
    print("\nExtracting Dallas County certs...")
    dc = ROOT / "Dallas County"
    for child in dc.iterdir():
        if child.suffix.lower() == ".pdf":
            safe_write(f"DallasCounty__{child.stem}.txt", pdf_text(child))

    # Past projects — extract only scope/cost docs, skip personal estimates
    print("\nExtracting past-project scope docs (PII-aware)...")
    past_projects = {
        "Hindu Temple of South Lake": [
            "Hindu Temple of South Lake - Scope of work.xlsx",  # via xlsx_summary
            "Hindu Partitions.pdf",
        ],
        "Lavon RV Park": [
            "Lavon RV Park Scope and contract.docx",
            "Lavon RV Park.docx",
        ],
        "Beck Group": [
            "Pre-Qual Beck Group.pdf",
        ],
    }
    for folder, files in past_projects.items():
        for fname in files:
            p = ROOT / folder / fname
            if not p.exists():
                continue
            stem = re.sub(r"[^\w\-]+", "_", folder + "__" + p.stem)
            if p.suffix.lower() == ".pdf":
                safe_write(stem + ".txt", pdf_text(p))
            elif p.suffix.lower() == ".docx":
                safe_write(stem + ".txt", docx_text(p))
            elif p.suffix.lower() == ".xlsx":
                safe_write(stem + ".txt", xlsx_summary(p, max_rows=5))

    print("\nDone.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
