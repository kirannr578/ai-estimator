"""Phase T9.1 — Streamlit Bid Alternates review tab helpers.

The Streamlit ``AppTest`` harness can't round-trip the heavy
``app.py`` (analyze pipeline needs real PDFs / LLM / pricing). Per
the T9.1 brief the alternates review tab is a thin Streamlit wrapper
over pure helper functions, all unit-tested here without a Streamlit
runtime:

* :func:`_format_alternate_type_badge` — colour-coded markdown badge.
* :func:`_format_cost_delta` — signed dollar string + MISSING placeholder.
* :func:`_compute_alternates_summary` — by-type aggregates.
* :func:`_alternates_to_csv` — CSV serialization.
* :func:`_resolve_bid_package_title` — FK resolution.
* :func:`_apply_alternate_operator_entry` — OPERATOR_ENTERED transition
  with sign-mismatch soft-warn (mirrors T9.0 backend semantics).

The Streamlit form glue (``st.checkbox``, ``st.number_input``, ...)
is transitively unit-tested via the helpers; a smoke import of
``app.py`` (in the verification step of the worker brief) confirms
the form wiring parses cleanly.
"""

from __future__ import annotations

import csv
import io

import pytest

from app import (
    _alternate_basis_label,
    _alternate_type_label,
    _alternates_to_csv,
    _apply_alternate_operator_entry,
    _compute_alternates_summary,
    _format_alternate_type_badge,
    _format_cost_delta,
    _resolve_bid_package_title,
)
from core.schemas import (
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    BidPackage,
    SiteInfo,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _ale(
    *,
    alternate_id: str = "Alt 1",
    alternate_type: AlternateType = AlternateType.ADDITIVE,
    description: str = "Add foo",
    cost_delta: float | None = 5000.0,
    pricing_basis: AlternatePricingBasis = AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
    confidence: float = 0.85,
    bid_package_id: str | None = None,
    source_sheet: str | None = None,
    related_csi: list[str] | None = None,
    operator_notes: str | None = None,
    included_in_base: bool = False,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alternate_id,
        alternate_type=alternate_type,
        description=description,
        cost_delta=cost_delta,
        pricing_basis=pricing_basis,
        confidence=confidence,
        included_in_base=included_in_base,
        bid_package_id=bid_package_id,
        source_sheet=source_sheet,
        related_csi=related_csi or [],
        operator_notes=operator_notes,
    )


def _project(packages: list[BidPackage] | None = None) -> ProjectModel:
    pkgs = packages or []
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=[],
        sheet_summaries={},
        warnings=[],
        bid_packages=pkgs,
        project_info=ProjectInfo(name="T9.1 UI"),
        scope_matrix=ScopeMatrix(
            packages=pkgs, by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=[],
    )


# ---------------------------------------------------------------------------
# _alternate_type_label / _alternate_basis_label
# ---------------------------------------------------------------------------


def test_alternate_type_label_for_each_value() -> None:
    assert _alternate_type_label(AlternateType.ADDITIVE) == "Additive"
    assert _alternate_type_label(AlternateType.DEDUCTIVE) == "Deductive"
    assert _alternate_type_label(AlternateType.SUBSTITUTION) == "Substitution"
    assert _alternate_type_label(AlternateType.VE) == "Value Engineering"


def test_alternate_type_label_accepts_raw_string() -> None:
    assert _alternate_type_label("additive") == "Additive"
    assert _alternate_type_label("value_engineering") == "Value Engineering"


def test_alternate_basis_label_for_each_value() -> None:
    assert (
        _alternate_basis_label(AlternatePricingBasis.EXTRACTED_FROM_BID_FORM)
        == "Extracted (bid form)"
    )
    assert (
        _alternate_basis_label(AlternatePricingBasis.OPERATOR_ENTERED)
        == "Operator entered"
    )
    assert (
        _alternate_basis_label(AlternatePricingBasis.SYNTHESIZED_FROM_TAKEOFF)
        == "Synthesized (takeoff)"
    )
    assert (
        _alternate_basis_label(AlternatePricingBasis.MISSING) == "Missing — review"
    )


# ---------------------------------------------------------------------------
# _format_alternate_type_badge
# ---------------------------------------------------------------------------


def test_format_alternate_type_badge_additive_is_green() -> None:
    assert _format_alternate_type_badge(AlternateType.ADDITIVE) == ":green[Additive]"


def test_format_alternate_type_badge_deductive_is_red() -> None:
    assert _format_alternate_type_badge(AlternateType.DEDUCTIVE) == ":red[Deductive]"


def test_format_alternate_type_badge_substitution_is_orange() -> None:
    assert (
        _format_alternate_type_badge(AlternateType.SUBSTITUTION)
        == ":orange[Substitution]"
    )


def test_format_alternate_type_badge_ve_is_blue() -> None:
    assert (
        _format_alternate_type_badge(AlternateType.VE) == ":blue[Value Engineering]"
    )


def test_format_alternate_type_badge_unknown_falls_back_to_plain() -> None:
    assert _format_alternate_type_badge("not_a_real_type") == "[not_a_real_type]"


# ---------------------------------------------------------------------------
# _format_cost_delta
# ---------------------------------------------------------------------------


def test_format_cost_delta_positive() -> None:
    assert _format_cost_delta(1234.56, AlternateType.ADDITIVE) == "+$1,234.56"


def test_format_cost_delta_negative() -> None:
    assert _format_cost_delta(-2500.0, AlternateType.DEDUCTIVE) == "-$2,500.00"


def test_format_cost_delta_zero() -> None:
    assert _format_cost_delta(0.0, AlternateType.SUBSTITUTION) == "$0.00"


def test_format_cost_delta_none_returns_blank_placeholder() -> None:
    assert _format_cost_delta(None, AlternateType.ADDITIVE) == "$_____"
    assert _format_cost_delta(None, AlternateType.DEDUCTIVE) == "$_____"
    assert _format_cost_delta(None, None) == "$_____"


def test_format_cost_delta_handles_int() -> None:
    assert _format_cost_delta(42, AlternateType.ADDITIVE) == "+$42.00"


def test_format_cost_delta_thousands_separator() -> None:
    assert _format_cost_delta(1_234_567.89, AlternateType.ADDITIVE) == "+$1,234,567.89"


# ---------------------------------------------------------------------------
# _compute_alternates_summary
# ---------------------------------------------------------------------------


def test_compute_alternates_summary_empty_returns_zeros() -> None:
    summary = _compute_alternates_summary([])
    assert summary["all"] == {"count": 0, "total_delta": 0.0, "missing_count": 0}
    for t in AlternateType:
        assert summary[t.value] == {
            "count": 0,
            "total_delta": 0.0,
            "missing_count": 0,
        }


def test_compute_alternates_summary_counts_by_type() -> None:
    alts = [
        _ale(alternate_id="A1", alternate_type=AlternateType.ADDITIVE, cost_delta=1000.0),
        _ale(alternate_id="A2", alternate_type=AlternateType.ADDITIVE, cost_delta=2000.0),
        _ale(
            alternate_id="D1",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-500.0,
        ),
        _ale(
            alternate_id="VE1", alternate_type=AlternateType.VE, cost_delta=-3000.0
        ),
    ]
    summary = _compute_alternates_summary(alts)
    assert summary[AlternateType.ADDITIVE.value]["count"] == 2
    assert summary[AlternateType.ADDITIVE.value]["total_delta"] == 3000.0
    assert summary[AlternateType.DEDUCTIVE.value]["count"] == 1
    assert summary[AlternateType.DEDUCTIVE.value]["total_delta"] == -500.0
    assert summary[AlternateType.VE.value]["count"] == 1
    assert summary[AlternateType.VE.value]["total_delta"] == -3000.0
    assert summary["all"]["count"] == 4
    assert summary["all"]["total_delta"] == round(3000.0 - 500.0 - 3000.0, 2)


def test_compute_alternates_summary_skips_none_delta_in_total() -> None:
    """``cost_delta is None`` (MISSING basis) contributes 0 to total_delta."""
    alts = [
        _ale(alternate_id="A1", cost_delta=1000.0),
        _ale(
            alternate_id="A2",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        ),
    ]
    summary = _compute_alternates_summary(alts)
    assert summary["all"]["count"] == 2
    assert summary["all"]["total_delta"] == 1000.0
    assert summary["all"]["missing_count"] == 1


def test_compute_alternates_summary_missing_count_per_type() -> None:
    alts = [
        _ale(
            alternate_id="A1",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        ),
        _ale(
            alternate_id="A2",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        ),
        _ale(
            alternate_id="D1",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=-1.0,
        ),
    ]
    summary = _compute_alternates_summary(alts)
    assert summary[AlternateType.ADDITIVE.value]["missing_count"] == 2
    assert summary[AlternateType.DEDUCTIVE.value]["missing_count"] == 0
    assert summary["all"]["missing_count"] == 2


def test_compute_alternates_summary_substitution_signed() -> None:
    """SUBSTITUTION net delta can be either sign."""
    alts = [
        _ale(
            alternate_id="S1",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=750.0,
        ),
        _ale(
            alternate_id="S2",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=-1250.0,
        ),
    ]
    summary = _compute_alternates_summary(alts)
    assert summary[AlternateType.SUBSTITUTION.value]["count"] == 2
    assert summary[AlternateType.SUBSTITUTION.value]["total_delta"] == -500.0


# ---------------------------------------------------------------------------
# _alternates_to_csv
# ---------------------------------------------------------------------------


def test_alternates_to_csv_includes_expected_columns() -> None:
    csv_str = _alternates_to_csv([])
    reader = csv.reader(io.StringIO(csv_str))
    headers = next(reader)
    expected = [
        "alternate_id",
        "type",
        "description",
        "cost_delta",
        "pricing_basis",
        "confidence",
        "bid_package_id",
        "source_sheet",
        "related_csi",
        "selected",
        "operator_notes",
    ]
    assert headers == expected


def test_alternates_to_csv_round_trips_one_row() -> None:
    alts = [
        _ale(
            alternate_id="ALT-1",
            alternate_type=AlternateType.DEDUCTIVE,
            description="Deduct mech",
            cost_delta=-12345.67,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
            confidence=0.91,
            bid_package_id="pkg-mech",
            source_sheet="Bid Form p.3",
            related_csi=["23 00 00", "23 73 13"],
        )
    ]
    csv_str = _alternates_to_csv(alts, selected_ids={"ALT-1"})
    reader = csv.DictReader(io.StringIO(csv_str))
    rows = list(reader)
    assert len(rows) == 1
    row = rows[0]
    assert row["alternate_id"] == "ALT-1"
    assert row["type"] == "deductive"
    assert row["description"] == "Deduct mech"
    assert row["cost_delta"] == "-12345.67"
    assert row["pricing_basis"] == "extracted_from_bid_form"
    assert row["confidence"] == "0.91"
    assert row["bid_package_id"] == "pkg-mech"
    assert row["source_sheet"] == "Bid Form p.3"
    assert row["related_csi"] == "23 00 00, 23 73 13"
    assert row["selected"] == "yes"
    assert row["operator_notes"] == ""


def test_alternates_to_csv_selected_ids_filter_applies() -> None:
    alts = [
        _ale(alternate_id="A1"),
        _ale(alternate_id="A2"),
    ]
    csv_str = _alternates_to_csv(alts, selected_ids={"A1"})
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert {r["alternate_id"]: r["selected"] for r in rows} == {
        "A1": "yes",
        "A2": "no",
    }


def test_alternates_to_csv_handles_embedded_commas_in_description() -> None:
    """csv.writer must quote the field; a downstream csv.reader recovers it intact."""
    alts = [
        _ale(
            alternate_id="A1",
            description=(
                "Add epoxy floor coating to mechanical rooms 101, 102, and 103, "
                "including base molding"
            ),
        )
    ]
    csv_str = _alternates_to_csv(alts)
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert len(rows) == 1
    assert "101, 102" in rows[0]["description"]


def test_alternates_to_csv_missing_cost_delta_emits_empty() -> None:
    alts = [
        _ale(
            alternate_id="A1",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    csv_str = _alternates_to_csv(alts)
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert rows[0]["cost_delta"] == ""
    assert rows[0]["pricing_basis"] == "missing"


def test_alternates_to_csv_operator_notes_overlay_supersedes_disk() -> None:
    """Session-state notes overlay wins when present."""
    alts = [_ale(alternate_id="A1", operator_notes="from disk")]
    csv_str = _alternates_to_csv(
        alts, operator_notes_map={"A1": "in-session edit"}
    )
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert rows[0]["operator_notes"] == "in-session edit"


def test_alternates_to_csv_empty_list_emits_only_header() -> None:
    csv_str = _alternates_to_csv([])
    lines = csv_str.strip().splitlines()
    assert len(lines) == 1


def test_alternates_to_csv_default_selected_ids_is_empty() -> None:
    """No selected_ids → every row's ``selected`` column is ``"no"``."""
    alts = [_ale(alternate_id="A1"), _ale(alternate_id="A2")]
    csv_str = _alternates_to_csv(alts)
    rows = list(csv.DictReader(io.StringIO(csv_str)))
    assert all(r["selected"] == "no" for r in rows)


# ---------------------------------------------------------------------------
# _resolve_bid_package_title
# ---------------------------------------------------------------------------


def test_resolve_bid_package_title_with_pdf_name_match() -> None:
    pkg = BidPackage(
        pdf_name="03-concrete.pdf",
        package_number="03.00",
        trade_name="Turnkey Structural Concrete",
    )
    project = _project([pkg])
    assert (
        _resolve_bid_package_title("03-concrete.pdf", project)
        == "Turnkey Structural Concrete"
    )


def test_resolve_bid_package_title_with_package_number_match() -> None:
    pkg = BidPackage(
        pdf_name="07-roofing.pdf", package_number="07.00", trade_name="Roofing"
    )
    project = _project([pkg])
    assert _resolve_bid_package_title("07.00", project) == "Roofing"


def test_resolve_bid_package_title_falls_back_to_pdf_name() -> None:
    """Empty / None ``trade_name`` → pdf_name as the human label."""
    pkg = BidPackage(pdf_name="08-doors.pdf", package_number=None, trade_name=None)
    project = _project([pkg])
    assert _resolve_bid_package_title("08-doors.pdf", project) == "08-doors.pdf"


def test_resolve_bid_package_title_none_id_returns_general_marker() -> None:
    project = _project([])
    assert _resolve_bid_package_title(None, project) == "(general)"
    assert _resolve_bid_package_title("", project) == "(general)"


def test_resolve_bid_package_title_unknown_id_returns_unknown_marker() -> None:
    pkg = BidPackage(pdf_name="03-concrete.pdf", trade_name="Concrete")
    project = _project([pkg])
    out = _resolve_bid_package_title("ghost-id", project)
    assert out.startswith("(unknown:")
    assert "ghost-id" in out


def test_resolve_bid_package_title_none_project_returns_id() -> None:
    """Defensive: caller may pass ``None`` for the project."""
    assert _resolve_bid_package_title("some-pkg", None) == "some-pkg"


# ---------------------------------------------------------------------------
# _apply_alternate_operator_entry
# ---------------------------------------------------------------------------


def test_apply_operator_entry_flips_missing_to_operator_entered() -> None:
    alts = [
        _ale(
            alternate_id="M1",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, warning = _apply_alternate_operator_entry("M1", 1500.0, alts)
    assert warning is None
    assert len(out) == 1
    assert out[0].cost_delta == 1500.0
    assert out[0].pricing_basis == AlternatePricingBasis.OPERATOR_ENTERED


def test_apply_operator_entry_does_not_mutate_input_list() -> None:
    alts = [
        _ale(
            alternate_id="M1",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, _w = _apply_alternate_operator_entry("M1", 250.0, alts)
    assert alts[0].cost_delta is None
    assert alts[0].pricing_basis == AlternatePricingBasis.MISSING
    assert out is not alts


def test_apply_operator_entry_unknown_id_raises() -> None:
    alts = [_ale(alternate_id="A1")]
    with pytest.raises(ValueError, match="not found"):
        _apply_alternate_operator_entry("ghost", 100.0, alts)


def test_apply_operator_entry_empty_id_raises() -> None:
    with pytest.raises(ValueError, match="must be non-empty"):
        _apply_alternate_operator_entry("", 100.0, [_ale()])


def test_apply_operator_entry_non_numeric_raises() -> None:
    alts = [_ale(alternate_id="A1")]
    with pytest.raises(ValueError, match="must be numeric"):
        _apply_alternate_operator_entry("A1", "not a number", alts)  # type: ignore[arg-type]


def test_apply_operator_entry_additive_negative_emits_warning_and_applies() -> None:
    """Sign mismatch — soft warn (not error), entry still lands."""
    alts = [
        _ale(
            alternate_id="A1",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, warning = _apply_alternate_operator_entry("A1", -500.0, alts)
    assert warning is not None
    assert "ADDITIVE" in warning
    assert out[0].cost_delta == -500.0
    assert out[0].pricing_basis == AlternatePricingBasis.OPERATOR_ENTERED


def test_apply_operator_entry_deductive_positive_emits_warning_and_applies() -> None:
    """Sign mismatch — soft warn (not error), matches T9.0 backend behaviour."""
    alts = [
        _ale(
            alternate_id="D1",
            alternate_type=AlternateType.DEDUCTIVE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, warning = _apply_alternate_operator_entry("D1", 500.0, alts)
    assert warning is not None
    assert "DEDUCTIVE" in warning
    assert out[0].cost_delta == 500.0
    assert out[0].pricing_basis == AlternatePricingBasis.OPERATOR_ENTERED


def test_apply_operator_entry_substitution_either_sign_no_warning() -> None:
    alts = [
        _ale(
            alternate_id="S1",
            alternate_type=AlternateType.SUBSTITUTION,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out_pos, warn_pos = _apply_alternate_operator_entry("S1", 1000.0, alts)
    out_neg, warn_neg = _apply_alternate_operator_entry("S1", -1000.0, alts)
    assert warn_pos is None
    assert warn_neg is None
    assert out_pos[0].cost_delta == 1000.0
    assert out_neg[0].cost_delta == -1000.0


def test_apply_operator_entry_ve_either_sign_no_warning() -> None:
    """VE behaves numerically like DEDUCTIVE but type-tag is preserved
    and the soft sign-warn only fires for ADDITIVE / DEDUCTIVE."""
    alts = [
        _ale(
            alternate_id="V1",
            alternate_type=AlternateType.VE,
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, warn = _apply_alternate_operator_entry("V1", -500.0, alts)
    assert warn is None
    assert out[0].alternate_type == AlternateType.VE
    assert out[0].cost_delta == -500.0


def test_apply_operator_entry_overrides_existing_extracted_basis() -> None:
    """An operator can correct a parsed bid-form value — the basis flips."""
    alts = [
        _ale(
            alternate_id="A1",
            alternate_type=AlternateType.ADDITIVE,
            cost_delta=1000.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        )
    ]
    out, warning = _apply_alternate_operator_entry("A1", 1234.0, alts)
    assert warning is None
    assert out[0].cost_delta == 1234.0
    assert out[0].pricing_basis == AlternatePricingBasis.OPERATOR_ENTERED


def test_apply_operator_entry_only_target_alternate_changes() -> None:
    alts = [
        _ale(alternate_id="A1", cost_delta=1000.0),
        _ale(
            alternate_id="A2",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        ),
        _ale(alternate_id="A3", cost_delta=2000.0),
    ]
    out, _w = _apply_alternate_operator_entry("A2", 500.0, alts)
    assert out[0].cost_delta == 1000.0
    assert out[0].pricing_basis == AlternatePricingBasis.EXTRACTED_FROM_BID_FORM
    assert out[1].cost_delta == 500.0
    assert out[1].pricing_basis == AlternatePricingBasis.OPERATOR_ENTERED
    assert out[2].cost_delta == 2000.0
    assert out[2].pricing_basis == AlternatePricingBasis.EXTRACTED_FROM_BID_FORM


def test_apply_operator_entry_rounds_to_cents() -> None:
    alts = [
        _ale(
            alternate_id="A1",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
        )
    ]
    out, _w = _apply_alternate_operator_entry("A1", 1234.5678, alts)
    assert out[0].cost_delta == 1234.57


def test_apply_operator_entry_preserves_metadata_fields() -> None:
    """The metadata (description / bid_package_id / source_sheet / etc.)
    survives the operator entry so the audit trail is intact."""
    alts = [
        _ale(
            alternate_id="A1",
            description="Add epoxy",
            cost_delta=None,
            pricing_basis=AlternatePricingBasis.MISSING,
            bid_package_id="pkg-conc",
            source_sheet="Bid Form p.4",
            related_csi=["09 96 23"],
            operator_notes="from disk",
        )
    ]
    out, _w = _apply_alternate_operator_entry("A1", 300.0, alts)
    updated = out[0]
    assert updated.description == "Add epoxy"
    assert updated.bid_package_id == "pkg-conc"
    assert updated.source_sheet == "Bid Form p.4"
    assert updated.related_csi == ["09 96 23"]
    assert updated.operator_notes == "from disk"
