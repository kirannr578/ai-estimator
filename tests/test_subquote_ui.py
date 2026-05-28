"""Phase T8.1 — ``app.py`` sub-quote UI helper tests.

Two helpers added to ``app.py`` by Phase T8.1:

* :func:`app._render_subquote_metadata` — renders a
  :class:`~core.pricing.subquote_parser.SubquoteMetadata` as a Markdown
  block.
* :func:`app._subquote_to_csv_preview` — produces a CSV-string preview
  of the parsed rows so an operator can save → re-import as CSV via
  the T6.3 uploader.

Plus a source-tag wiring test: confirming that a sub-quote-originated
override gets ``[sub-quote]`` in its operator note, NOT ``[batch]``.

Streamlit-free — the helpers are pure functions returning strings.
"""

from __future__ import annotations

import csv
import io

import pytest

from app import _render_subquote_metadata, _subquote_to_csv_preview
from core.pricing.batch_override import (
    BatchOverrideRow,
    format_batch_operator_note,
    parse_vendor_csv,
)
from core.pricing.subquote_parser import (
    SubquoteMetadata,
    SubquoteParseResult,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _row(
    *,
    row_index: int = 1,
    description: str = "Item A",
    unit_cost: float = 10.0,
    quantity: float | None = None,
    vendor: str | None = None,
    quote_ref: str | None = None,
    notes: str | None = None,
) -> BatchOverrideRow:
    return BatchOverrideRow(
        row_index=row_index,
        description=description,
        unit_cost=unit_cost,
        quantity=quantity,
        vendor=vendor,
        quote_ref=quote_ref,
        notes=notes,
    )


# ---------------------------------------------------------------------------
# _render_subquote_metadata
# ---------------------------------------------------------------------------


class TestRenderSubquoteMetadata:
    def test_renders_all_fields_when_populated(self) -> None:
        md = SubquoteMetadata(
            vendor_name="ABC Plumbing",
            quote_number="QT-100",
            quote_date="2026-05-28",
            project_reference="Riverside Office",
            total_quoted=12345.67,
            detected_pages=[1, 2],
            confidence=1.0,
        )
        text = _render_subquote_metadata(md)
        assert "**Sub-quote metadata**" in text
        assert "ABC Plumbing" in text
        assert "QT-100" in text
        assert "2026-05-28" in text
        assert "Riverside Office" in text
        assert "$12,345.67" in text
        assert "1, 2" in text
        assert "100%" in text

    def test_omits_missing_fields(self) -> None:
        md = SubquoteMetadata(vendor_name="ABC Co", confidence=0.2)
        text = _render_subquote_metadata(md)
        assert "ABC Co" in text
        assert "Quote #" not in text
        assert "Date:" not in text
        assert "Project:" not in text
        assert "Quote total" not in text

    def test_empty_metadata_only_shows_header_and_confidence(self) -> None:
        md = SubquoteMetadata()
        text = _render_subquote_metadata(md)
        assert "**Sub-quote metadata**" in text
        assert "0%" in text
        # No populated bullets.
        assert text.count("- ") == 1  # just the confidence line

    def test_returns_string(self) -> None:
        md = SubquoteMetadata()
        assert isinstance(_render_subquote_metadata(md), str)


# ---------------------------------------------------------------------------
# _subquote_to_csv_preview
# ---------------------------------------------------------------------------


class TestSubquoteToCsvPreview:
    def test_empty_result_returns_header_only(self) -> None:
        result = SubquoteParseResult(rows=[], metadata=SubquoteMetadata())
        csv_text = _subquote_to_csv_preview(result)
        reader = csv.DictReader(io.StringIO(csv_text))
        assert reader.fieldnames is not None
        assert "description" in reader.fieldnames
        assert "unit_cost" in reader.fieldnames
        # No data rows.
        assert list(reader) == []

    def test_single_row_round_trip(self) -> None:
        result = SubquoteParseResult(
            rows=[_row(description="Lavatory P-1", unit_cost=450.0, quantity=10.0)],
            metadata=SubquoteMetadata(),
        )
        csv_text = _subquote_to_csv_preview(result)
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        assert len(rows) == 1
        assert rows[0]["description"] == "Lavatory P-1"
        assert float(rows[0]["unit_cost"]) == 450.0
        assert float(rows[0]["quantity"]) == 10.0

    def test_roundtrip_through_csv_parser(self) -> None:
        """Output should be re-parseable by parse_vendor_csv."""
        result = SubquoteParseResult(
            rows=[
                _row(
                    row_index=2,
                    description="Item A",
                    unit_cost=15.50,
                    quantity=5.0,
                    vendor="ABC",
                    quote_ref="QT-1",
                    notes="FOB origin",
                ),
                _row(
                    row_index=3,
                    description="Item B",
                    unit_cost=22.0,
                    quantity=None,
                ),
            ],
            metadata=SubquoteMetadata(),
        )
        csv_text = _subquote_to_csv_preview(result)
        parsed_rows, errors = parse_vendor_csv(csv_text)
        assert errors == []
        assert len(parsed_rows) == 2
        assert parsed_rows[0].description == "Item A"
        assert parsed_rows[0].unit_cost == 15.50
        assert parsed_rows[0].vendor == "ABC"
        assert parsed_rows[0].quote_ref == "QT-1"
        assert parsed_rows[1].description == "Item B"
        assert parsed_rows[1].unit_cost == 22.0
        # Quantity preserved (or absent) on round-trip.
        assert parsed_rows[0].quantity == 5.0

    def test_optional_fields_remain_empty(self) -> None:
        result = SubquoteParseResult(
            rows=[_row(description="Bare item", unit_cost=1.0)],
            metadata=SubquoteMetadata(),
        )
        csv_text = _subquote_to_csv_preview(result)
        rows = list(csv.DictReader(io.StringIO(csv_text)))
        assert rows[0]["vendor"] == ""
        assert rows[0]["quote_ref"] == ""
        assert rows[0]["notes"] == ""
        assert rows[0]["quantity"] == ""

    def test_quantity_formatting_avoids_scientific(self) -> None:
        result = SubquoteParseResult(
            rows=[
                _row(quantity=100000.0),
                _row(row_index=2, quantity=0.5),
            ],
            metadata=SubquoteMetadata(),
        )
        csv_text = _subquote_to_csv_preview(result)
        # Should not contain '1e+05' or similar.
        assert "e+" not in csv_text
        assert "100000" in csv_text


# ---------------------------------------------------------------------------
# Source-tag wiring — confirm sub-quote uses [sub-quote] tag
# ---------------------------------------------------------------------------


class TestSourceTagWiring:
    def test_default_tag_is_batch(self) -> None:
        """Backwards compat — pre-T8.1 callers see [batch] unchanged."""
        row = _row(row_index=2, description="Item A", unit_cost=10.0)
        note = format_batch_operator_note(row)
        assert note.startswith("[batch]")
        assert "[sub-quote]" not in note

    def test_subquote_tag_replaces_batch(self) -> None:
        row = _row(row_index=2, description="Item A", unit_cost=10.0)
        note = format_batch_operator_note(row, source_tag="[sub-quote]")
        assert note.startswith("[sub-quote]")
        assert "[batch]" not in note
        assert "[csv-row: 2]" in note

    def test_subquote_tag_carries_optional_fields(self) -> None:
        row = _row(
            row_index=5,
            description="Item A",
            unit_cost=10.0,
            vendor="ABC Plumbing",
            quote_ref="QT-1234",
            notes="FOB origin",
        )
        note = format_batch_operator_note(row, source_tag="[sub-quote]")
        assert "[sub-quote]" in note
        assert "[vendor: ABC Plumbing]" in note
        assert "[quote-ref: QT-1234]" in note
        assert "[csv-row: 5]" in note
        assert "FOB origin" in note

    def test_arbitrary_tag_supported(self) -> None:
        """Helper accepts arbitrary tag strings (future provenance hooks)."""
        row = _row(description="Item A", unit_cost=10.0)
        note = format_batch_operator_note(row, source_tag="[experiment-x]")
        assert note.startswith("[experiment-x]")


# ---------------------------------------------------------------------------
# Imports + smoke
# ---------------------------------------------------------------------------


def test_helpers_importable_from_app() -> None:
    """The two helpers must be exposed at module scope on app.py."""
    import app
    assert callable(app._render_subquote_metadata)
    assert callable(app._subquote_to_csv_preview)
