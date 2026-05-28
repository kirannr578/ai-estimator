"""Tests for the wide-table hardening added to the proposal renderer.

Day-1 ship: TAMU Wehner `04-scope-of-work.md` carried a wide trade-
detail table that crashed `xhtml2pdf`'s `PmlTable` with a negative
column width on cell(0,0). Both client PDFs failed; internal-workbook
and pitch-deck rendered fine.

Day-2 fix is two layers:
  1. Pre-process: `downgrade_wide_html_tables(html)` wraps wide
     rendered tables in a compact-font `<div>` so xhtml2pdf has enough
     headroom to compute positive column widths.
  2. Safety-net: if the primary render still fails,
     `_xhtml2pdf_render_with_fallback` retries with markdown tables
     flattened to `**Header:** value` definition-list paragraphs, so
     no `<table>` element reaches the layout engine at all.

These tests cover both layers in isolation, plus the end-to-end
behavior of the safety net.
"""

from __future__ import annotations

import logging
from pathlib import Path

import pytest

from core.proposal_renderer.common import (
    WIDE_TABLE_MAX_COLS,
    WIDE_TABLE_MAX_ROW_CHARS,
    downgrade_wide_html_tables,
    flatten_markdown_tables_to_definition_list,
    is_wide_html_table,
)
from core.proposal_renderer.pdf import (
    _markdown_to_html,
    _xhtml2pdf_render_with_fallback,
)


# ---------------------------------------------------------------------------
# Pre-process layer — is_wide_html_table / downgrade_wide_html_tables
# ---------------------------------------------------------------------------


def _build_html_table(rows: list[list[str]]) -> str:
    """Build a minimal HTML table from a list-of-lists. First row is
    treated as the header."""
    parts = ["<table>"]
    for i, row in enumerate(rows):
        tag = "th" if i == 0 else "td"
        cells = "".join(f"<{tag}>{c}</{tag}>" for c in row)
        parts.append(f"<tr>{cells}</tr>")
    parts.append("</table>")
    return "".join(parts)


def test_narrow_table_not_flagged_as_wide() -> None:
    """A 3-column / short-cell table is not considered wide."""
    table = _build_html_table([
        ["Item", "Qty", "Notes"],
        ["Door", "12", "Hardware included"],
        ["Window", "8", "Tempered"],
        ["Slab", "4", "4-inch"],
    ])
    assert not is_wide_html_table(table)


def test_many_columns_flagged_as_wide() -> None:
    """A 12-column table breaches the column-count threshold."""
    table = _build_html_table([
        [f"C{i}" for i in range(12)],
        [f"v{i}" for i in range(12)],
    ])
    assert is_wide_html_table(table)


def test_long_row_flagged_as_wide() -> None:
    """A 3-column table with very long cell text breaches the char
    threshold even though the column count is small."""
    table = _build_html_table([
        ["Area", "Description", "Trade"],
        [
            "First floor north wing",
            "Demolish existing CMU partitions and salvage casework where "
            "possible for re-use in storage build-out per spec 02 41 19",
            "General contractor self-performed demolition",
        ],
    ])
    assert is_wide_html_table(table)


def test_downgrade_wraps_only_wide_tables() -> None:
    """The downgrader leaves narrow tables alone and wraps wide ones in
    a compact-font div."""
    narrow = _build_html_table([
        ["A", "B"],
        ["1", "2"],
    ])
    wide = _build_html_table([
        [f"C{i}" for i in range(12)],
        [f"v{i}" for i in range(12)],
    ])
    html = f"<p>before</p>{narrow}<p>middle</p>{wide}<p>after</p>"
    out = downgrade_wide_html_tables(html)
    # Narrow table is verbatim (not wrapped)
    assert narrow in out
    # Wide table is wrapped in a compact-font div
    assert 'class="compact-table-wrap"' in out
    assert "font-size: 7pt" in out
    # Wide table HTML still present inside the wrapper
    assert wide in out


def test_downgrade_is_idempotent() -> None:
    """Running the downgrader twice doesn't double-wrap the table."""
    wide = _build_html_table([
        [f"C{i}" for i in range(8)],
        [f"v{i}" for i in range(8)],
    ])
    once = downgrade_wide_html_tables(wide)
    twice = downgrade_wide_html_tables(once)
    assert once.count('class="compact-table-wrap"') == 1
    assert twice.count('class="compact-table-wrap"') == 1


def test_thresholds_are_explicit_constants() -> None:
    """Anchor the thresholds the way the renderer documents them so a
    silent threshold change shows up in CI."""
    assert WIDE_TABLE_MAX_COLS == 5
    assert WIDE_TABLE_MAX_ROW_CHARS == 120


# ---------------------------------------------------------------------------
# Markdown pre-flatten — flatten_markdown_tables_to_definition_list
# ---------------------------------------------------------------------------


def test_flatten_skips_narrow_table_by_default() -> None:
    md = (
        "Intro paragraph.\n\n"
        "| Item | Qty |\n"
        "|------|----:|\n"
        "| Door |  12 |\n"
        "| Window | 8 |\n\n"
        "Outro paragraph.\n"
    )
    out = flatten_markdown_tables_to_definition_list(md)
    # Narrow table — kept verbatim
    assert "| Item | Qty |" in out
    assert "**Item Door**" not in out


def test_flatten_collapses_wide_table_by_default() -> None:
    """A 12-column table is automatically flattened even without
    `always=True`."""
    header = "| " + " | ".join(f"C{i}" for i in range(12)) + " |"
    sep = "|" + "|".join("---" for _ in range(12)) + "|"
    row = "| " + " | ".join(f"v{i}" for i in range(12)) + " |"
    md = f"{header}\n{sep}\n{row}\n"
    out = flatten_markdown_tables_to_definition_list(md)
    assert "**C0 v0**" in out
    assert "- **C1:** v1" in out
    # Original table syntax is gone
    assert "| C0 | C1 |" not in out


def test_flatten_always_collapses_every_table() -> None:
    """`always=True` flattens even a narrow `| K | V |` table — used
    by the safety-net fallback path."""
    md = (
        "| Key | Value |\n"
        "|-----|-------|\n"
        "| A | 1 |\n"
        "| B | 2 |\n"
    )
    out = flatten_markdown_tables_to_definition_list(md, always=True)
    assert "**Key A**" in out
    assert "- **Value:** 1" in out
    assert "**Key B**" in out
    assert "- **Value:** 2" in out


def test_flatten_handles_multiple_tables_in_one_doc() -> None:
    """Both tables in a single doc get flattened independently when
    `always=True`."""
    md = (
        "# Heading\n\n"
        "| A | B |\n"
        "|---|---|\n"
        "| 1 | 2 |\n\n"
        "Paragraph.\n\n"
        "| X | Y | Z |\n"
        "|---|---|---|\n"
        "| 7 | 8 | 9 |\n"
    )
    out = flatten_markdown_tables_to_definition_list(md, always=True)
    assert "**A 1**" in out
    assert "**X 7**" in out
    assert "- **Y:** 8" in out
    assert "- **Z:** 9" in out


def test_flatten_preserves_non_table_content() -> None:
    md = (
        "# Title\n\n"
        "Some prose with **bold** and `code`.\n\n"
        "| K | V |\n"
        "|---|---|\n"
        "| a | b |\n\n"
        "Closing line.\n"
    )
    out = flatten_markdown_tables_to_definition_list(md, always=True)
    assert "# Title" in out
    assert "Some prose with **bold** and `code`." in out
    assert "Closing line." in out


# ---------------------------------------------------------------------------
# Markdown-to-HTML pipeline — verifies the pre-process is wired in
# ---------------------------------------------------------------------------


def test_markdown_to_html_downgrades_wide_table_inline() -> None:
    """A markdown body containing a 12-col table comes out the
    `_markdown_to_html` pipeline already wrapped in compact-font."""
    header = "| " + " | ".join(f"C{i}" for i in range(12)) + " |"
    sep = "|" + "|".join("---" for _ in range(12)) + "|"
    row = "| " + " | ".join(f"v{i}" for i in range(12)) + " |"
    body = f"Some intro.\n\n{header}\n{sep}\n{row}\n\nClosing.\n"
    html = _markdown_to_html(body, flatten_tables=False)
    assert 'class="compact-table-wrap"' in html
    # Table cells survived the wrap
    assert "C0" in html and "v11" in html


def test_markdown_to_html_flatten_strips_all_tables() -> None:
    """`flatten_tables=True` rewrites every table — no `<table>` tag
    survives. This is the safety-net fallback shape."""
    body = (
        "| K | V |\n"
        "|---|---|\n"
        "| a | b |\n"
    )
    html = _markdown_to_html(body, flatten_tables=True)
    assert "<table" not in html.lower()
    assert "Key" in html or "<strong>K a</strong>" in html
    # The flattened form should contain the cell values somewhere
    assert "a" in html and "b" in html


# ---------------------------------------------------------------------------
# Safety-net renderer end-to-end
# ---------------------------------------------------------------------------


def test_safety_net_uses_primary_when_it_succeeds(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """When the primary HTML renders cleanly, the fallback is never
    invoked."""
    calls = {"n": 0}

    def fake_attempt(html: str, out_path: Path) -> str | None:
        calls["n"] += 1
        out_path.write_bytes(b"%PDF-1.4 fake\n%%EOF\n")
        return None

    monkeypatch.setattr(
        "core.proposal_renderer.pdf._xhtml2pdf_attempt", fake_attempt
    )

    out = tmp_path / "out.pdf"
    used = _xhtml2pdf_render_with_fallback(
        "<html><body>primary</body></html>",
        "<html><body>fallback</body></html>",
        out,
        label="unit-test",
    )
    assert used == "primary"
    assert calls["n"] == 1
    assert out.exists() and out.stat().st_size > 0


def test_safety_net_falls_back_when_primary_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """When the primary attempt errors (mimicking PmlTable negative
    width), the renderer logs a warning and produces the PDF from the
    fallback HTML."""
    seen: list[str] = []

    def fake_attempt(html: str, out_path: Path) -> str | None:
        seen.append(html)
        if "primary" in html:
            return "PmlTable: flowable given negative availWidth=-1.7e-15"
        out_path.write_bytes(b"%PDF-1.4 fallback\n%%EOF\n")
        return None

    monkeypatch.setattr(
        "core.proposal_renderer.pdf._xhtml2pdf_attempt", fake_attempt
    )

    out = tmp_path / "out.pdf"
    with caplog.at_level(logging.WARNING, logger="core.proposal_renderer.pdf"):
        used = _xhtml2pdf_render_with_fallback(
            "<html><body>primary table here</body></html>",
            "<html><body>fallback no-table</body></html>",
            out,
            label="some-bid / Full proposal (full-proposal.pdf)",
        )
    assert used == "fallback"
    assert len(seen) == 2
    assert out.exists() and out.stat().st_size > 0

    warnings = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert any(
        "wide-table safety-net engaged" in r.getMessage() for r in warnings
    )
    assert any(
        "some-bid / Full proposal" in r.getMessage() for r in warnings
    )


def test_safety_net_raises_when_both_fail(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both attempts fail → RuntimeError, no successful PDF claim."""
    def fake_attempt(html: str, out_path: Path) -> str | None:
        return "PmlTable: catastrophic failure"

    monkeypatch.setattr(
        "core.proposal_renderer.pdf._xhtml2pdf_attempt", fake_attempt
    )

    out = tmp_path / "out.pdf"
    with pytest.raises(RuntimeError) as exc:
        _xhtml2pdf_render_with_fallback(
            "<html>primary</html>",
            "<html>fallback</html>",
            out,
            label="explodes-bid / Full proposal",
        )
    msg = str(exc.value)
    assert "explodes-bid / Full proposal" in msg
    assert "primary" in msg
    assert "fallback" in msg


def test_synthetic_wide_table_renders_via_fallback_real_xhtml2pdf(
    tmp_path: Path,
) -> None:
    """End-to-end check that the full pipeline produces a non-empty PDF
    for a markdown body with a stress-test wide table.

    This is the regression guard for the original TAMU Wehner failure:
    if the primary render survives, we get a 'primary'-tier PDF; if
    xhtml2pdf still chokes, the safety-net flattens tables and produces
    a 'fallback'-tier PDF. Either outcome MUST end with a non-empty
    file on disk.
    """
    # Build a deliberately punishing 14-column / long-content table.
    header_cells = [
        "Trade", "CSI div", "Scope summary", "Sub", "Mfr", "Qty",
        "Unit", "Unit $", "Subtotal", "Labor hrs", "Lead time",
        "Status", "Inspection", "Notes",
    ]
    body_cells = [
        [
            f"Trade {i}",
            f"0{i} 00 00",
            "Demolish existing partitions and salvage casework where "
            "possible for re-use in storage build-out per spec.",
            f"Sub-{i}",
            f"Mfr-{i}",
            str(10 + i),
            "EA",
            "$1,250",
            f"${(10+i)*1250:,}",
            str(40 + i),
            "6 wk",
            "Pending submittal",
            "Owner walk required",
            "Coordinate with MEP",
        ]
        for i in range(1, 9)
    ]
    md_lines = ["| " + " | ".join(header_cells) + " |"]
    md_lines.append("|" + "|".join("---" for _ in header_cells) + "|")
    for row in body_cells:
        md_lines.append("| " + " | ".join(row) + " |")
    body_md = (
        "# Synthetic wide-table stress test\n\n"
        "Intro paragraph before the table.\n\n"
        + "\n".join(md_lines) + "\n\n"
        "Closing paragraph after the table.\n"
    )

    primary_html = (
        "<html><head><meta charset='utf-8'/></head><body>"
        f"{_markdown_to_html(body_md, flatten_tables=False)}"
        "</body></html>"
    )
    fallback_html = (
        "<html><head><meta charset='utf-8'/></head><body>"
        f"{_markdown_to_html(body_md, flatten_tables=True)}"
        "</body></html>"
    )

    out = tmp_path / "stress.pdf"
    used = _xhtml2pdf_render_with_fallback(
        primary_html,
        fallback_html,
        out,
        label="synthetic stress test",
    )
    assert used in {"primary", "fallback"}
    assert out.exists()
    assert out.stat().st_size > 1024, (
        f"PDF produced via {used} path is suspiciously small "
        f"({out.stat().st_size} bytes)"
    )
    # PDF magic bytes
    assert out.read_bytes().startswith(b"%PDF-"), (
        "Output file does not start with the PDF magic header"
    )
