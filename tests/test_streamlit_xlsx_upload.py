"""Phase T6.4.a — ``app.py`` xlsx upload wire-up tests.

T6.4.a extends the existing T6.3 vendor-CSV batch-override section of
``app.py`` to accept ``.xlsx`` workbooks in addition to ``.csv`` files.
Each sheet in an uploaded workbook is treated as a separate vendor
table; the operator picks which sheets to apply via an
``st.multiselect``, the per-sheet plans are merged via
:func:`core.pricing.xlsx_parser.merge_xlsx_plans`, and the downstream
T6.4.b matcher + T6.4.c source-tag-aware applier run unchanged.

Following the pattern in :mod:`tests.test_streamlit_subquote_apply_wireup`,
this file uses a **two-pronged approach** rather than spinning up the
``streamlit.testing.v1`` runtime (which is brittle, slow, and brings
its own version-dependent behaviour):

* **Source-level pins** — read ``app.py`` itself and assert the
  uploader's ``type=`` list, the branch on ``.xlsx``, the call to
  :func:`parse_vendor_xlsx`, the ``st.multiselect``, and the
  ``SOURCE_TAG_VENDOR_CSV`` propagation are all present. These pins
  catch silent drift (e.g. a refactor that drops ``.xlsx`` from the
  uploader's type list).
* **Backend round-trip** — invoke the same parse → merge → match →
  apply chain ``app.py`` runs at preview / apply time and assert the
  end-to-end semantic. Validates the wire-up actually works, not just
  the call shape.
"""

from __future__ import annotations

import io
import re
from pathlib import Path

import pytest
from openpyxl import Workbook

from core.pricing.batch_override import (
    SOURCE_TAG_VENDOR_CSV,
    apply_batch_plan,
    match_cost_lines,
)
from core.pricing.xlsx_parser import (
    merge_xlsx_plans,
    parse_vendor_xlsx,
)
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


APP_PY_PATH = Path(__file__).resolve().parent.parent / "app.py"
APP_PY_TEXT = APP_PY_PATH.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _workbook_bytes(
    sheets: list[tuple[str, list[list[object]]]],
) -> bytes:
    """Build an in-memory xlsx workbook for round-trip tests."""
    wb = Workbook()
    default_name = wb.active.title
    for sheet_name, rows in sheets:
        ws = wb.create_sheet(title=sheet_name)
        for row in rows:
            ws.append(list(row))
    del wb[default_name]
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def _line(
    *,
    description: str = "Interior latex paint walls",
    csi_section: str = "09 91 23",
    unit: str = "SF",
    unit_cost: float = 2.0,
) -> CostLine:
    return CostLine(
        csi_division=csi_section.split(" ", 1)[0],
        csi_section=csi_section,
        description=description,
        quantity=100.0,
        unit=unit,
        unit_cost=unit_cost,
        total_cost=round(unit_cost * 100.0, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.9,
        price_confidence=0.7,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        cost_source="cwicr:test",
        notes=None,
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.4.a wire-up",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# Source-level pins — file_uploader signature + branch + multiselect
# ---------------------------------------------------------------------------


class TestUploaderAcceptsCsvAndXlsx:
    def test_uploader_type_list_includes_xlsx(self) -> None:
        """The batch-override file uploader must accept ``.xlsx``."""
        # The exact contract: a ``type=["csv", "xlsx"]`` (or set order)
        # on the batch_override_csv_uploader. Match either ordering.
        pattern = re.compile(
            r'key="batch_override_csv_uploader"',
            re.DOTALL,
        )
        assert pattern.search(APP_PY_TEXT) is not None
        # And the type list near that key contains both extensions.
        uploader_block = re.search(
            r"st\.file_uploader\(\s*\".*?\",\s*type=\[(.*?)\],\s*"
            r'key="batch_override_csv_uploader"',
            APP_PY_TEXT,
            re.DOTALL,
        )
        assert uploader_block is not None, (
            "batch-override file_uploader call not found in app.py"
        )
        type_list = uploader_block.group(1)
        assert '"csv"' in type_list
        assert '"xlsx"' in type_list

    def test_app_imports_parse_vendor_xlsx_and_merge_xlsx_plans(self) -> None:
        """Pin the two public xlsx_parser symbols import."""
        assert "from core.pricing.xlsx_parser import" in APP_PY_TEXT
        assert "parse_vendor_xlsx" in APP_PY_TEXT
        assert "merge_xlsx_plans" in APP_PY_TEXT


class TestUploadBranchesOnExtension:
    def test_xlsx_branch_calls_parse_vendor_xlsx(self) -> None:
        """``app.py`` must call :func:`parse_vendor_xlsx` on the xlsx branch.

        Pre-T6.4.a the only parser was :func:`parse_vendor_csv`. The
        new branch must explicitly invoke ``parse_vendor_xlsx`` (the
        new public API) when the upload's filename ends with .xlsx.
        """
        # The call site must exist; the assertion is intentionally
        # loose on surrounding context so a refactor that renames a
        # local variable doesn't break the pin.
        assert "parse_vendor_xlsx(" in APP_PY_TEXT

    def test_csv_branch_still_calls_parse_vendor_csv(self) -> None:
        """T6.3 ``parse_vendor_csv`` is still called for the .csv branch."""
        assert "parse_vendor_csv(" in APP_PY_TEXT

    def test_branch_keys_off_filename_extension(self) -> None:
        """The branch must dispatch on the upload's filename extension.

        Pinning to ``.endswith(".xlsx")`` rather than e.g. content
        sniffing because the test surface is the visible code; future
        refactors that switch to content sniffing should drop this pin
        explicitly.
        """
        assert '.endswith(".xlsx")' in APP_PY_TEXT


class TestSheetMultiselectRenders:
    def test_app_uses_multiselect_for_sheet_selection(self) -> None:
        """An ``st.multiselect`` must surface the sheet selector."""
        # Match any st.multiselect call followed by something resembling
        # a sheet list — the exact label / key may evolve.
        pattern = re.compile(r"st\.multiselect\(", re.DOTALL)
        assert pattern.search(APP_PY_TEXT) is not None
        # Specifically, the multiselect must reference the xlsx_plans
        # state key (i.e. it's the sheet selector, not some unrelated
        # multiselect elsewhere in the app).
        assert "batch_override_xlsx_selected" in APP_PY_TEXT

    def test_multiselect_defaults_to_all_sheets(self) -> None:
        """Default selection should be every sheet, not an empty list.

        The contract is "all sheets selected by default; operator
        deselects the ones they don't want" — opposite of opt-in.
        """
        # Verify there's a default that ties to the sheet_names list
        # (a `default=...` kwarg, ultimately seeded from list(xlsx_plans.keys()))
        assert "default=" in APP_PY_TEXT
        assert "list(xlsx_plans.keys())" in APP_PY_TEXT

    def test_no_sheets_selected_shows_info_message(self) -> None:
        """A user-friendly ``st.info`` message must appear when no
        sheets are selected (no apply attempted)."""
        assert "No sheets selected" in APP_PY_TEXT


class TestApplyUsesVendorCsvTag:
    def test_apply_call_passes_source_tag_vendor_csv(self) -> None:
        """The apply call must pass ``source_tag=SOURCE_TAG_VENDOR_CSV``.

        Both the CSV and the xlsx branches route through the same
        existing apply block (because the xlsx path stores a normal
        ``BatchOverridePlan`` in session_state, same key as the CSV
        path) so a single ``apply_batch_plan(..., source_tag=...)``
        call site handles both. We pin that the apply uses the
        vendor-csv tag — the xlsx workbook is, semantically, vendor
        data.
        """
        assert "source_tag=SOURCE_TAG_VENDOR_CSV" in APP_PY_TEXT


# ---------------------------------------------------------------------------
# Backend round-trip — full chain that the UI fires at apply time
# ---------------------------------------------------------------------------


class TestBackendRoundTripCsvVsXlsx:
    def test_csv_text_routes_through_parse_vendor_csv(self) -> None:
        """A .csv upload routes through the CSV parser path.

        Pin: when the file extension is .csv the UI does NOT call
        ``parse_vendor_xlsx``. We verify this by importing both
        functions and confirming the CSV parser handles CSV text
        directly while the xlsx parser refuses non-xlsx bytes.
        """
        csv_text = (
            "description,unit_cost\n"
            "Interior paint,2.50\n"
        )
        # CSV parser succeeds.
        from core.pricing.batch_override import parse_vendor_csv
        rows, errors = parse_vendor_csv(csv_text)
        assert errors == []
        assert len(rows) == 1
        # xlsx parser rejects (would raise ValueError if accidentally
        # routed through the wrong branch).
        with pytest.raises(ValueError):
            parse_vendor_xlsx(csv_text.encode("utf-8"))

    def test_xlsx_bytes_route_through_parse_vendor_xlsx(self) -> None:
        """An .xlsx upload routes through the xlsx parser path."""
        wb = _workbook_bytes([
            ("Pricing", [
                ["description", "unit_cost"],
                ["Interior paint", 2.50],
            ]),
        ])
        plans = parse_vendor_xlsx(wb)
        assert list(plans.keys()) == ["Pricing"]


class TestThreeSheetSelectorRoundTrip:
    def _three_sheet_workbook(self) -> bytes:
        return _workbook_bytes([
            ("Mech", [
                ["description", "unit_cost"],
                ["AHU-1", 5000.0],
            ]),
            ("Elec", [
                ["description", "unit_cost"],
                ["Panelboard", 1200.0],
                ["Wire 12 AWG", 0.85],
            ]),
            ("Plumb", [
                ["description", "unit_cost"],
                ["Lavatory P-1", 450.0],
            ]),
        ])

    def test_three_sheets_default_selection_is_all(self) -> None:
        plans = parse_vendor_xlsx(self._three_sheet_workbook())
        # The default selection the UI builds at preview time:
        default_selection = list(plans.keys())
        assert default_selection == ["Mech", "Elec", "Plumb"]

    def test_three_sheets_summary_row_counts_match(self) -> None:
        """The sheet-summary table the UI renders should show the same
        row count the parser emits."""
        plans = parse_vendor_xlsx(self._three_sheet_workbook())
        counts = {name: plan.total_rows for name, plan in plans.items()}
        assert counts == {"Mech": 1, "Elec": 2, "Plumb": 1}

    def test_operator_deselects_one_sheet_merge_drops_those_rows(self) -> None:
        """Operator deselects 'Mech' → merge plan reflects only Elec+Plumb."""
        plans = parse_vendor_xlsx(self._three_sheet_workbook())
        # Simulate operator deselection of "Mech".
        selected = ["Elec", "Plumb"]
        filtered = {name: plans[name] for name in selected}
        merged = merge_xlsx_plans(filtered)
        # 2 (Elec) + 1 (Plumb) = 3 rows
        assert merged.total_rows == 3
        # AHU-1 (Mech) must NOT appear.
        descriptions = [r.row.description for r in merged.no_match]
        assert "AHU-1" not in descriptions
        assert "Panelboard" in descriptions
        assert "Lavatory P-1" in descriptions

    def test_operator_deselects_all_sheets_no_merge(self) -> None:
        """Operator deselects every sheet → merge raises (UI catches
        and shows the info message). The UI guard is the
        ``if not selected_sheets:`` branch in ``app.py``."""
        plans = parse_vendor_xlsx(self._three_sheet_workbook())
        empty_selection: dict = {}
        with pytest.raises(ValueError, match="zero plans"):
            merge_xlsx_plans(empty_selection)


class TestApplyEndToEndUsesVendorCsvTag:
    def test_xlsx_apply_round_trip_stamps_vendor_csv_tag(self) -> None:
        """End-to-end: build an xlsx → parse → merge → match → apply
        with ``source_tag=SOURCE_TAG_VENDOR_CSV`` (same kwarg the UI
        uses) → the line's notes must carry the canonical vendor-csv
        tag at position 0."""
        wb = _workbook_bytes([
            ("Pricing", [
                ["description", "unit_cost"],
                ["Interior latex paint walls", 3.50],
            ]),
        ])
        plans = parse_vendor_xlsx(wb)
        merged = merge_xlsx_plans(plans)
        rows = [r.row for r in merged.no_match]
        lines = [_line()]
        match_plan = match_cost_lines(rows, lines)
        est = _estimate(lines)
        new_est, _ = apply_batch_plan(
            est, match_plan, source_tag=SOURCE_TAG_VENDOR_CSV
        )
        notes = new_est.line_items[0].notes or ""
        assert notes.startswith("[vendor-csv] ")
