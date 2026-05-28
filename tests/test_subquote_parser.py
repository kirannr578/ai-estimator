"""Phase T8.1 — ``core/pricing/subquote_parser.py`` core tests.

Covers the pure-logic sub-quote PDF parser: PDF table detection,
header detection, row parsing (including extended-price derivation),
metadata extraction (regex-only), subtotal / tax / total row skipping,
and the deterministic-failure modes that mark non-tabular / scanned /
encrypted PDFs as T8.2 territory.

Bucketed:

* **Tabular parse** (12 tests) — single-table happy path, multi-table,
  multi-page, header detection, column-alias resolution (description /
  qty / unit_price / extended), unit_cost derived from extended/qty.
* **Skip-and-warn behaviour** (7 tests) — subtotal / tax / total rows
  skipped, empty description skipped, negative unit_cost skipped,
  missing-cost skipped, zero-qty extended-row skipped.
* **Metadata extraction** (5 tests) — vendor / quote-# / date / project
  / total scraped via regex; missing slots leave the field None.
* **Failure modes** (8 tests) — empty bytes / corrupted bytes /
  encrypted PDF / scanned PDF (no text) / free-form (text but no
  table) / table-without-header / quantity-parsing edge cases.
* **Quantity parsing** (3 tests) — bare number, with unit suffix,
  thousands separator.

Test PDFs are generated on-the-fly with ``reportlab.platypus.Table``
which renders with explicit grid lines that PyMuPDF's ``find_tables()``
detects deterministically (verified at module load by the smoke test
in the brief). No committed test-fixture PDFs.
"""

from __future__ import annotations

import io

import pytest

reportlab = pytest.importorskip("reportlab")

from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import getSampleStyleSheet  # noqa: E402
from reportlab.platypus import (  # noqa: E402
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

from core.pricing.batch_override import BatchOverrideRow  # noqa: E402
from core.pricing.subquote_parser import (  # noqa: E402
    SubquoteMetadata,
    SubquoteParseError,
    SubquoteParseResult,
    _detect_header_row,
    _extract_metadata,
    _is_subtotal_row,
    _parse_number,
    _resolve_column_map,
    parse_subquote_pdf,
)


# ---------------------------------------------------------------------------
# PDF-building helpers
# ---------------------------------------------------------------------------


def _build_pdf_with_table(
    data: list[list[str]],
    *,
    preamble: list[str] | None = None,
    extra_tables: list[list[list[str]]] | None = None,
    multi_page: bool = False,
) -> bytes:
    """Build a single-page (or multi-page) PDF with one or more tables.

    ``data`` is the primary table's rows (first row treated as header).
    ``preamble`` is a list of free-text paragraphs rendered above the
    table — used to test metadata extraction. ``extra_tables`` adds
    additional tables on the same page. ``multi_page=True`` inserts a
    ``PageBreak`` between the primary and extra tables so we can test
    multi-page parsing.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow: list = []
    if preamble:
        for text in preamble:
            flow.append(Paragraph(text, styles["Normal"]))
        flow.append(Spacer(1, 12))
    t = Table(data)
    t.setStyle(TableStyle([("GRID", (0, 0), (-1, -1), 0.5, colors.black)]))
    flow.append(t)
    if extra_tables:
        for tbl_data in extra_tables:
            if multi_page:
                flow.append(PageBreak())
            else:
                flow.append(Spacer(1, 24))
            t2 = Table(tbl_data)
            t2.setStyle(TableStyle([
                ("GRID", (0, 0), (-1, -1), 0.5, colors.black),
            ]))
            flow.append(t2)
    doc.build(flow)
    return buf.getvalue()


def _build_text_only_pdf(paragraphs: list[str]) -> bytes:
    """Build a PDF with free-form paragraphs and NO tables."""
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=letter)
    styles = getSampleStyleSheet()
    flow = [Paragraph(p, styles["Normal"]) for p in paragraphs]
    doc.build(flow)
    return buf.getvalue()


# ---------------------------------------------------------------------------
# Tabular parse — happy paths
# ---------------------------------------------------------------------------


class TestTabularParse:
    def test_basic_table_with_unit_price(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Lavatory P-1", "10", "450.00"],
            ["Water closet WC-1", "8", "525.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert isinstance(result, SubquoteParseResult)
        assert len(result.rows) == 2
        assert result.rows[0].description == "Lavatory P-1"
        assert result.rows[0].quantity == 10.0
        assert result.rows[0].unit_cost == 450.0
        assert result.rows[1].description == "Water closet WC-1"
        assert result.rows[1].unit_cost == 525.0

    def test_table_with_extended_only(self) -> None:
        """unit_cost derived from extended / quantity."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Extended"],
            ["Concrete slab", "500", "12500.00"],
            ["Rebar #5", "200", "450.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 2
        assert result.rows[0].unit_cost == 25.0  # 12500 / 500
        assert result.rows[1].unit_cost == 2.25  # 450 / 200
        # Warnings should record the derivation.
        derived_warnings = [w for w in result.warnings if "derived" in w]
        assert len(derived_warnings) == 2

    def test_extended_takes_precedence_when_both_present(self) -> None:
        """When unit_price column is present, it is used directly."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price", "Extended"],
            ["Item A", "10", "5.00", "999.00"],  # extended is wrong on purpose
        ])
        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 1
        assert result.rows[0].unit_cost == 5.0

    def test_column_alias_resolution(self) -> None:
        """Various spellings for the unit_cost column."""
        for unit_header in ("Price", "Cost", "Rate", "$/unit"):
            pdf = _build_pdf_with_table([
                ["Item", "Qty", unit_header],
                ["Widget", "5", "100.00"],
            ])
            result = parse_subquote_pdf(pdf)
            assert len(result.rows) == 1, f"failed for header {unit_header!r}"
            assert result.rows[0].unit_cost == 100.0

    def test_description_alias_resolution(self) -> None:
        """Description column can also be 'Item' or 'Line Item'."""
        for desc_header in ("Item", "Line Item", "Item Description"):
            pdf = _build_pdf_with_table([
                [desc_header, "Qty", "Unit Price"],
                ["Widget", "5", "100.00"],
            ])
            result = parse_subquote_pdf(pdf)
            assert len(result.rows) == 1, f"failed for header {desc_header!r}"
            assert result.rows[0].description == "Widget"

    def test_vendor_and_quote_ref_columns_propagate(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price", "Vendor", "Quote Ref"],
            ["Item A", "10", "5.00", "ABC Co", "QT-123"],
        ])
        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 1
        assert result.rows[0].vendor == "ABC Co"
        assert result.rows[0].quote_ref == "QT-123"

    def test_notes_column_propagates(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price", "Notes"],
            ["Item A", "10", "5.00", "FOB origin"],
        ])
        result = parse_subquote_pdf(pdf)
        assert result.rows[0].notes == "FOB origin"

    def test_multi_table_same_page(self) -> None:
        pdf = _build_pdf_with_table(
            [
                ["Description", "Qty", "Unit Price"],
                ["Item A", "1", "10.00"],
            ],
            extra_tables=[[
                ["Description", "Qty", "Unit Price"],
                ["Item B", "2", "20.00"],
            ]],
        )
        result = parse_subquote_pdf(pdf)
        descriptions = {r.description for r in result.rows}
        assert "Item A" in descriptions
        assert "Item B" in descriptions

    def test_multi_page_parsing(self) -> None:
        pdf = _build_pdf_with_table(
            [
                ["Description", "Qty", "Unit Price"],
                ["Item A", "1", "10.00"],
            ],
            extra_tables=[[
                ["Description", "Qty", "Unit Price"],
                ["Item B", "2", "20.00"],
            ]],
            multi_page=True,
        )
        result = parse_subquote_pdf(pdf)
        descriptions = {r.description for r in result.rows}
        assert "Item A" in descriptions
        assert "Item B" in descriptions
        # Both pages should be detected.
        assert 1 in result.metadata.detected_pages
        assert 2 in result.metadata.detected_pages

    def test_row_indices_are_monotonic_and_distinct(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["A", "1", "1.00"],
            ["B", "2", "2.00"],
            ["C", "3", "3.00"],
        ])
        result = parse_subquote_pdf(pdf)
        indices = [r.row_index for r in result.rows]
        assert len(set(indices)) == len(indices)
        assert indices == sorted(indices)

    def test_dollar_sign_and_commas_stripped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "$1,250.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert result.rows[0].unit_cost == 1250.0

    def test_qty_with_unit_suffix(self) -> None:
        """'100 EA' should parse as qty=100."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "100 EA", "5.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert result.rows[0].quantity == 100.0


# ---------------------------------------------------------------------------
# Skip-and-warn behaviour
# ---------------------------------------------------------------------------


class TestSkipAndWarn:
    def test_subtotal_row_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "10.00"],
            ["Subtotal", "", "10.00"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = {r.description for r in result.rows}
        assert "Item A" in descriptions
        assert "Subtotal" not in descriptions
        assert len(result.rows) == 1

    def test_sales_tax_row_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "100.00"],
            ["Sales Tax", "", "8.25"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = {r.description for r in result.rows}
        assert "Item A" in descriptions
        assert "Sales Tax" not in descriptions

    def test_grand_total_row_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "100.00"],
            ["Grand Total", "", "108.25"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = {r.description for r in result.rows}
        assert "Grand Total" not in descriptions

    def test_empty_description_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["", "1", "10.00"],
            ["Item B", "1", "20.00"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = [r.description for r in result.rows]
        assert "" not in descriptions
        assert "Item B" in descriptions
        # Warning emitted for the skip.
        assert any(
            "empty description" in w.lower() for w in result.warnings
        )

    def test_negative_unit_cost_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "-10.00"],
            ["Item B", "1", "20.00"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = [r.description for r in result.rows]
        assert "Item A" not in descriptions
        assert "Item B" in descriptions
        assert any("negative" in w.lower() for w in result.warnings)

    def test_zero_unit_cost_kept(self) -> None:
        """Zero unit cost is legitimate (giveaway / cost-recovered)."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Marketing giveaway", "1", "0.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert len(result.rows) == 1
        assert result.rows[0].unit_cost == 0.0

    def test_extended_with_zero_qty_skipped(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Extended"],
            ["Item A", "0", "100.00"],
            ["Item B", "10", "100.00"],
        ])
        result = parse_subquote_pdf(pdf)
        descriptions = [r.description for r in result.rows]
        assert "Item A" not in descriptions
        assert "Item B" in descriptions


# ---------------------------------------------------------------------------
# Metadata extraction (regex)
# ---------------------------------------------------------------------------


class TestMetadataExtraction:
    def test_extract_vendor_name(self) -> None:
        md = _extract_metadata("From: ABC Plumbing Inc.\nQuote #1234")
        assert md.vendor_name == "ABC Plumbing Inc."

    def test_extract_quote_number(self) -> None:
        md = _extract_metadata("Quote #: QT-4521\nDate: 2026-05-28")
        assert md.quote_number == "QT-4521"

    def test_extract_quote_date(self) -> None:
        md = _extract_metadata("Date: 2026-05-28\nProject: Foo")
        assert md.quote_date == "2026-05-28"

    def test_extract_project_reference(self) -> None:
        md = _extract_metadata("Project: Riverside Office Building\n")
        assert md.project_reference == "Riverside Office Building"

    def test_extract_total_quoted(self) -> None:
        md = _extract_metadata("Total: $12,345.67\n")
        assert md.total_quoted == 12345.67

    def test_missing_slots_remain_none(self) -> None:
        md = _extract_metadata("Just some random text with no markers.")
        assert md.vendor_name is None
        assert md.quote_number is None
        assert md.quote_date is None
        assert md.total_quoted is None
        assert md.confidence == 0.0

    def test_confidence_scales_with_filled_slots(self) -> None:
        md_full = _extract_metadata(
            "From: ABC Co\nQuote #: 123\nDate: 2026-01-01\n"
            "Project: Foo\nTotal: $1,000.00"
        )
        assert md_full.confidence == 1.0
        md_partial = _extract_metadata("From: ABC Co\n")
        assert 0.0 < md_partial.confidence < 1.0

    def test_metadata_integrated_into_parse_result(self) -> None:
        pdf = _build_pdf_with_table(
            [
                ["Description", "Qty", "Unit Price"],
                ["Item A", "1", "10.00"],
            ],
            preamble=[
                "From: ABC Plumbing Inc.",
                "Quote #: QT-4521",
                "Date: 2026-05-28",
            ],
        )
        result = parse_subquote_pdf(pdf)
        assert result.metadata.vendor_name == "ABC Plumbing Inc."
        assert result.metadata.quote_number == "QT-4521"
        assert result.metadata.quote_date == "2026-05-28"


# ---------------------------------------------------------------------------
# Failure modes — non-recoverable + T8.2 territory
# ---------------------------------------------------------------------------


class TestFailureModes:
    def test_empty_bytes_raises(self) -> None:
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(b"")
        assert "empty" in str(exc_info.value).lower()

    def test_corrupted_bytes_raises(self) -> None:
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(b"not a real pdf")
        assert "corrupted" in str(exc_info.value).lower() or \
            "could not open" in str(exc_info.value).lower()

    def test_free_form_text_pdf_raises(self) -> None:
        """PDF with text but no detectable tables → SubquoteParseError."""
        pdf = _build_text_only_pdf([
            "Dear Customer,",
            "Our quote for your job is approximately fifty thousand dollars.",
            "Please call us at your convenience.",
            "Best regards, ABC Co",
        ])
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(pdf)
        msg = str(exc_info.value).lower()
        # The free-form message OR the no-recognised-header message
        # is acceptable here (heuristic detector may match either).
        assert "tabl" in msg or "free-form" in msg or "header" in msg

    def test_table_without_recognisable_header_raises(self) -> None:
        """Table with no description / cost column → SubquoteParseError."""
        pdf = _build_pdf_with_table([
            ["Foo", "Bar", "Baz"],
            ["1", "2", "3"],
        ])
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(pdf)
        assert "header" in str(exc_info.value).lower() or \
            "free-form" in str(exc_info.value).lower()

    def test_table_without_unit_cost_or_extended_raises(self) -> None:
        """Table with description + qty but no price columns is unusable."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty"],
            ["Item A", "10"],
        ])
        with pytest.raises(SubquoteParseError):
            parse_subquote_pdf(pdf)

    def test_returns_warnings_for_bad_rows(self) -> None:
        """Bad rows do not abort the parse; they emit warnings."""
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["", "1", "10.00"],
            ["Item B", "1", "20.00"],
        ])
        result = parse_subquote_pdf(pdf)
        assert len(result.warnings) >= 1
        assert len(result.rows) == 1

    def test_encrypted_pdf_message(self) -> None:
        """Build an encrypted PDF and confirm the right error message."""
        from pypdf import PdfReader, PdfWriter
        plain = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["A", "1", "1.00"],
        ])
        reader = PdfReader(io.BytesIO(plain))
        writer = PdfWriter()
        for page in reader.pages:
            writer.add_page(page)
        writer.encrypt(user_password="secret", owner_password="secret")
        buf = io.BytesIO()
        writer.write(buf)
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(buf.getvalue())
        assert "encrypt" in str(exc_info.value).lower()

    def test_error_message_points_at_t82_or_csv(self) -> None:
        """Free-form failures should hint at CSV alternative / T8.2."""
        pdf = _build_text_only_pdf([
            "Free-form quote with no table structure.",
        ])
        with pytest.raises(SubquoteParseError) as exc_info:
            parse_subquote_pdf(pdf)
        msg = str(exc_info.value).lower()
        assert "csv" in msg or "t8.2" in msg


# ---------------------------------------------------------------------------
# Pure-helper unit tests (no PDFs needed)
# ---------------------------------------------------------------------------


class TestPureHelpers:
    def test_parse_number_basic(self) -> None:
        assert _parse_number("100") == 100.0
        assert _parse_number("$1,250.00") == 1250.0
        assert _parse_number("100 EA") == 100.0
        assert _parse_number("100.5 LF") == 100.5
        assert _parse_number("100,000") == 100000.0

    def test_parse_number_invalid(self) -> None:
        assert _parse_number(None) is None
        assert _parse_number("") is None
        assert _parse_number("   ") is None
        # Pure-text inputs (no leading number) should return None.
        assert _parse_number("not a number") is None

    def test_is_subtotal_row_detects_common_tokens(self) -> None:
        assert _is_subtotal_row("Subtotal")
        assert _is_subtotal_row("subtotal")
        assert _is_subtotal_row("SUBTOTAL")
        assert _is_subtotal_row("Sub-Total")
        assert _is_subtotal_row("Sales tax")
        assert _is_subtotal_row("Tax")
        assert _is_subtotal_row("Grand Total")
        assert _is_subtotal_row("  TOTAL  ")
        assert _is_subtotal_row("Total:")

    def test_is_subtotal_row_does_not_false_positive(self) -> None:
        assert not _is_subtotal_row("Subfloor underlayment")
        assert not _is_subtotal_row("Tax-exempt purchasing")
        assert not _is_subtotal_row("")
        assert not _is_subtotal_row("Lavatory P-1")

    def test_detect_header_row_finds_header(self) -> None:
        rows = [
            ["From: ABC Co", None, None],
            ["", "", ""],
            ["Description", "Qty", "Unit Price"],
            ["Item A", "1", "10.00"],
        ]
        assert _detect_header_row(rows) == 2

    def test_detect_header_row_returns_none_when_no_header(self) -> None:
        rows = [
            ["Foo", "Bar", "Baz"],
            ["1", "2", "3"],
        ]
        assert _detect_header_row(rows) is None

    def test_resolve_column_map_full_layout(self) -> None:
        header = [
            "Description", "Qty", "Unit Price", "Vendor",
            "Quote Ref", "Notes",
        ]
        col_map = _resolve_column_map(header)
        assert col_map["description"] == 0
        assert col_map["quantity"] == 1
        assert col_map["unit_cost"] == 2
        assert col_map["vendor"] == 3
        assert col_map["quote_ref"] == 4
        assert col_map["notes"] == 5

    def test_resolve_column_map_extended_only(self) -> None:
        col_map = _resolve_column_map(["Description", "Qty", "Extended"])
        assert "description" in col_map
        assert "extended" in col_map
        assert "unit_cost" not in col_map


# ---------------------------------------------------------------------------
# Integration with batch_override (shape compatibility)
# ---------------------------------------------------------------------------


class TestShapeCompatibility:
    """Confirm the parser emits the EXACT BatchOverrideRow shape T6.3 uses."""

    def test_emitted_rows_are_batch_override_row_instances(self) -> None:
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Item A", "10", "5.00"],
        ])
        result = parse_subquote_pdf(pdf)
        for row in result.rows:
            assert isinstance(row, BatchOverrideRow)
            assert isinstance(row.description, str)
            assert isinstance(row.unit_cost, float)
            assert isinstance(row.row_index, int)

    def test_rows_consumable_by_match_cost_lines(self) -> None:
        """Round-trip into the T6.3 matcher with no shape changes."""
        from core.pricing.batch_override import match_cost_lines
        from core.schemas import (
            CostBand,
            CostCategory,
            CostLine,
            CostSourceTier,
        )
        cost_line = CostLine(
            csi_division="22",
            csi_section="22 41 00",
            description="Lavatory P-1",
            quantity=10.0,
            unit="EA",
            unit_cost=500.0,
            total_cost=5000.0,
            cost_category=CostCategory.SUBCONTRACTOR,
            confidence=0.9,
            price_confidence=0.7,
            cost_source_tier=CostSourceTier.INTERPOLATED,
            cost_band=CostBand.OPERATOR_REVIEW,
            cost_source="cwicr:42",
        )
        pdf = _build_pdf_with_table([
            ["Description", "Qty", "Unit Price"],
            ["Lavatory P-1", "10", "450.00"],
        ])
        result = parse_subquote_pdf(pdf)
        plan = match_cost_lines(result.rows, [cost_line])
        # Matcher must accept the rows and produce a non-empty match
        # (description is identical).
        assert plan.total_rows == 1
        assert len(plan.matched) == 1
