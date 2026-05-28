"""Phase T6.2 — Streamlit operator-override UI helpers.

The Streamlit ``AppTest`` harness does not yet cleanly support
form-submit round-trips on a heavy app like ``app.py`` (the analyze-
pipeline path requires real PDFs / LLM calls / pricing). Per the T6.2
brief, the override UI is structured as a thin Streamlit wrapper around
pure helper functions in ``app.py`` so the round-trip can be tested
without spinning up the full app:

* :func:`_format_operator_note` — vendor / quote-ref / free-text →
  one combined string (or ``None`` when all empty).
* :func:`_select_line_label` — human-readable dropdown label.
* :func:`_sort_lines_by_tier` — MANUAL_OVERRIDE first, then descending
  catalog quality.
* :func:`_format_override_delta` — old / new estimate diff string.
* :func:`_apply_operator_override` — pure wrapper around
  ``apply_manual_override`` that formats the operator note.
* :func:`_build_override_history_csv` — CSV serialisation for the audit-
  trail download button.

The Streamlit form itself (``st.form``, ``st.number_input``, etc.) is
unit-tested transitively by the helpers above; a smoke-import of
``app.py`` (in the verification step of the T6.2 worker brief) confirms
the form wiring parses cleanly.
"""

from __future__ import annotations

import csv
import io
from typing import Any

import pytest

import app as app_module
from app import (
    _apply_operator_override,
    _build_override_history_csv,
    _format_operator_note,
    _format_override_delta,
    _select_line_label,
    _sort_lines_by_tier,
)
from core.estimator import MANUAL_OVERRIDE_NOTE_PREFIX, apply_manual_override
from core.schemas import (
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _line(
    *,
    description: str = "Interior painting",
    csi_division: str = "09",
    csi_section: str = "09 91 23",
    quantity: float = 100.0,
    unit: str = "SF",
    unit_cost: float = 2.0,
    confidence: float = 0.92,
    price_confidence: float = 0.65,
    tier: CostSourceTier = CostSourceTier.INTERPOLATED,
    band: CostBand = CostBand.OPERATOR_REVIEW,
    cost_source: str = "cwicr:42",
    suppressed: bool = False,
    notes: str | None = None,
) -> CostLine:
    return CostLine(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit=unit,
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=confidence,
        price_confidence=price_confidence,
        cost_source_tier=tier,
        cost_band=band,
        suppressed=suppressed,
        cost_source=cost_source,
        notes=notes,
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.2 override UI",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


# ---------------------------------------------------------------------------
# _format_operator_note
# ---------------------------------------------------------------------------


def test_format_operator_note_all_three_fields() -> None:
    note = _format_operator_note(
        vendor="Ferguson Plumbing",
        quote_ref="Q-2026-0428",
        free_text="Direct supplier quote, includes delivery",
    )
    assert note == (
        "[vendor: Ferguson Plumbing] [quote-ref: Q-2026-0428] "
        "Direct supplier quote, includes delivery"
    )


def test_format_operator_note_vendor_only() -> None:
    assert _format_operator_note("Home Depot Pro", "", "") == "[vendor: Home Depot Pro]"


def test_format_operator_note_quote_ref_only() -> None:
    assert _format_operator_note("", "PO#12345", "") == "[quote-ref: PO#12345]"


def test_format_operator_note_free_text_only() -> None:
    assert _format_operator_note("", "", "Hand-priced from RSMeans 2025") == (
        "Hand-priced from RSMeans 2025"
    )


def test_format_operator_note_all_empty_returns_none() -> None:
    """Empty / whitespace-only inputs collapse to None — caller passes
    None to ``apply_manual_override`` which still stamps the sentinel."""
    assert _format_operator_note("", "", "") is None
    assert _format_operator_note("   ", "\t", "\n  ") is None
    assert _format_operator_note(None, None, None) is None


def test_format_operator_note_strips_whitespace() -> None:
    note = _format_operator_note("  Ferguson  ", "  Q-1  ", "  reason  ")
    assert note == "[vendor: Ferguson] [quote-ref: Q-1] reason"


def test_format_operator_note_skips_empty_field_in_middle() -> None:
    """Vendor + free-text but no quote-ref leaves no double-space gap."""
    note = _format_operator_note("Ferguson", "", "supplier quote")
    assert note == "[vendor: Ferguson] supplier quote"


# ---------------------------------------------------------------------------
# _select_line_label
# ---------------------------------------------------------------------------


def test_select_line_label_includes_index_description_cost_unit_tier() -> None:
    li = _line(
        description="Slab on grade",
        unit_cost=8.50,
        unit="SF",
        tier=CostSourceTier.EXACT_MATCH,
    )
    label = _select_line_label(3, li)
    assert "#3" in label
    assert "Slab on grade" in label
    assert "$8.50" in label
    assert "SF" in label
    assert "Exact Match" in label


def test_select_line_label_truncates_long_description() -> None:
    long_desc = "A" * 120
    li = _line(description=long_desc)
    label = _select_line_label(0, li)
    # Truncated to 57 chars + "..." = 60 chars total in the desc slot
    assert "..." in label
    assert len([c for c in label if c == "A"]) == 57


def test_select_line_label_handles_empty_description() -> None:
    li = _line(description="")
    label = _select_line_label(0, li)
    assert "(no description)" in label


def test_select_line_label_handles_empty_unit() -> None:
    li = _line(unit="")
    label = _select_line_label(0, li)
    assert "/?" in label


def test_select_line_label_includes_manual_override_tier_label() -> None:
    li = _line(tier=CostSourceTier.MANUAL_OVERRIDE)
    label = _select_line_label(7, li)
    assert "Manual Override" in label


# ---------------------------------------------------------------------------
# _sort_lines_by_tier
# ---------------------------------------------------------------------------


def test_sort_lines_by_tier_manual_override_first() -> None:
    lines = [
        _line(description="exact", tier=CostSourceTier.EXACT_MATCH),
        _line(description="manual", tier=CostSourceTier.MANUAL_OVERRIDE),
        _line(description="missing", tier=CostSourceTier.MISSING),
        _line(description="interp", tier=CostSourceTier.INTERPOLATED),
    ]
    sorted_pairs = _sort_lines_by_tier(lines)
    descs = [li.description for _, li in sorted_pairs]
    assert descs[0] == "manual"
    assert descs[-1] == "missing"


def test_sort_lines_by_tier_full_ordering() -> None:
    lines = [
        _line(description="parametric", tier=CostSourceTier.PARAMETRIC),
        _line(description="missing", tier=CostSourceTier.MISSING),
        _line(description="exact", tier=CostSourceTier.EXACT_MATCH),
        _line(description="manual", tier=CostSourceTier.MANUAL_OVERRIDE),
        _line(description="category", tier=CostSourceTier.CATEGORY_MATCH),
        _line(description="interp", tier=CostSourceTier.INTERPOLATED),
    ]
    sorted_pairs = _sort_lines_by_tier(lines)
    descs = [li.description for _, li in sorted_pairs]
    assert descs == [
        "manual",
        "exact",
        "category",
        "interp",
        "parametric",
        "missing",
    ]


def test_sort_lines_by_tier_preserves_index_in_pair() -> None:
    """Returned pairs carry the original index so the dropdown can map
    a label back to the canonical line position for ``apply_manual_override``."""
    lines = [
        _line(description="A", tier=CostSourceTier.EXACT_MATCH),
        _line(description="B", tier=CostSourceTier.MANUAL_OVERRIDE),
    ]
    pairs = _sort_lines_by_tier(lines)
    assert pairs[0][0] == 1  # B is at original index 1
    assert pairs[1][0] == 0


def test_sort_lines_by_tier_stable_within_tier() -> None:
    """Two rows in the same tier preserve their physical order."""
    lines = [
        _line(description="A", tier=CostSourceTier.EXACT_MATCH),
        _line(description="B", tier=CostSourceTier.EXACT_MATCH),
        _line(description="C", tier=CostSourceTier.EXACT_MATCH),
    ]
    pairs = _sort_lines_by_tier(lines)
    indices = [idx for idx, _ in pairs]
    assert indices == [0, 1, 2]


# ---------------------------------------------------------------------------
# _format_override_delta
# ---------------------------------------------------------------------------


def test_format_override_delta_shows_three_axes() -> None:
    est = _estimate([
        _line(quantity=100.0, unit_cost=2.0,
              confidence=0.92, price_confidence=0.95,
              tier=CostSourceTier.EXACT_MATCH,
              band=CostBand.AUTO_APPROVE),
    ])
    out = apply_manual_override(est, 0, new_unit_cost=5.0)
    delta = _format_override_delta(est, out, 0)
    assert "$2.00" in delta
    assert "$5.00" in delta
    # Line total: 200 -> 500
    assert "$200.00" in delta
    assert "$500.00" in delta


def test_format_override_delta_uses_arrow_glyph() -> None:
    est = _estimate([_line()])
    out = apply_manual_override(est, 0, new_unit_cost=3.0)
    delta = _format_override_delta(est, out, 0)
    # The function uses ``→`` (U+2192) to render the diff arrow.
    assert "\u2192" in delta


# ---------------------------------------------------------------------------
# _apply_operator_override
# ---------------------------------------------------------------------------


def test_apply_operator_override_round_trip_basic() -> None:
    est = _estimate([_line(unit_cost=2.0, quantity=100.0)])
    new_est, note = _apply_operator_override(
        est,
        line_idx=0,
        new_unit_cost=4.50,
        vendor="Ferguson",
        quote_ref="Q-1",
        free_text="rough-in supplier quote",
    )
    li = new_est.line_items[0]
    assert li.unit_cost == pytest.approx(4.50)
    assert li.total_cost == pytest.approx(450.0)
    assert li.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert li.price_confidence == pytest.approx(1.0)
    assert note == "[vendor: Ferguson] [quote-ref: Q-1] rough-in supplier quote"
    # The note prefix lands on the line's notes field via apply_manual_override.
    assert MANUAL_OVERRIDE_NOTE_PREFIX in (li.notes or "")
    assert "Ferguson" in (li.notes or "")


def test_apply_operator_override_no_attribution_passes_none_note() -> None:
    """All three attribution fields empty → ``apply_manual_override``
    still stamps the canonical T6.4.c.2 head: ``[manual-override]``
    tag at position 0, ``operator override`` sentinel, and the new
    ``unit_cost`` as a bracketed field. The wrapper passes ``None``
    as the history-row attribution note (no vendor / quote-ref /
    free-text), but the line's notes field still carries the
    canonical override-provenance head."""
    est = _estimate([_line(notes=None)])
    new_est, note = _apply_operator_override(
        est, line_idx=0, new_unit_cost=3.0,
        vendor="", quote_ref="", free_text="",
    )
    assert note is None
    li = new_est.line_items[0]
    assert li.notes == (
        f"[manual-override] {MANUAL_OVERRIDE_NOTE_PREFIX}: [unit_cost: $3.00]"
    )


def test_apply_operator_override_does_not_mutate_input_estimate() -> None:
    est = _estimate([_line(unit_cost=2.0)])
    _ = _apply_operator_override(
        est, line_idx=0, new_unit_cost=99.0,
        vendor="V", quote_ref="Q", free_text="t",
    )
    assert est.line_items[0].unit_cost == pytest.approx(2.0)
    assert est.line_items[0].cost_source_tier == CostSourceTier.INTERPOLATED


def test_apply_operator_override_propagates_value_error_on_negative() -> None:
    est = _estimate([_line()])
    with pytest.raises(ValueError, match="\u2265 0"):
        _apply_operator_override(
            est, line_idx=0, new_unit_cost=-1.0,
            vendor="", quote_ref="", free_text="",
        )


def test_apply_operator_override_propagates_value_error_on_bad_index() -> None:
    est = _estimate([_line()])
    with pytest.raises(ValueError, match="out of range"):
        _apply_operator_override(
            est, line_idx=99, new_unit_cost=5.0,
            vendor="", quote_ref="", free_text="",
        )


def test_apply_operator_override_zero_unit_cost_allowed() -> None:
    """Zero is a legitimate giveaway / cost-recovered value; the
    underlying ``apply_manual_override`` accepts it. We mirror that."""
    est = _estimate([_line(unit_cost=2.0)])
    new_est, _ = _apply_operator_override(
        est, line_idx=0, new_unit_cost=0.0,
        vendor="", quote_ref="", free_text="",
    )
    assert new_est.line_items[0].unit_cost == pytest.approx(0.0)
    assert new_est.line_items[0].total_cost == pytest.approx(0.0)


def test_apply_operator_override_recomputes_subtotal() -> None:
    est = _estimate([
        _line(quantity=10.0, unit_cost=1.0,
              confidence=0.92, price_confidence=0.95,
              tier=CostSourceTier.EXACT_MATCH,
              band=CostBand.AUTO_APPROVE),
    ])
    new_est, _ = _apply_operator_override(
        est, line_idx=0, new_unit_cost=5.0,
        vendor="", quote_ref="", free_text="",
    )
    assert est.subtotal == pytest.approx(10.0)
    assert new_est.subtotal == pytest.approx(50.0)


# ---------------------------------------------------------------------------
# _build_override_history_csv
# ---------------------------------------------------------------------------


def test_build_override_history_csv_empty_emits_header_only() -> None:
    csv_text = _build_override_history_csv([])
    reader = csv.DictReader(io.StringIO(csv_text))
    assert reader.fieldnames == [
        "timestamp",
        "line_index",
        "description",
        "csi_division",
        "csi_section",
        "original_unit_cost",
        "new_unit_cost",
        "operator_note",
    ]
    assert list(reader) == []


def test_build_override_history_csv_round_trip() -> None:
    rows: list[dict[str, Any]] = [
        {
            "timestamp": "2026-05-28T14:00:00",
            "line_index": 3,
            "description": "Interior painting",
            "csi_division": "09",
            "csi_section": "09 91 23",
            "original_unit_cost": 2.00,
            "new_unit_cost": 3.50,
            "operator_note": "[vendor: Sherwin] supplier quote",
        },
        {
            "timestamp": "2026-05-28T14:05:00",
            "line_index": 7,
            "description": "Slab on grade",
            "csi_division": "03",
            "csi_section": "03 30 00",
            "original_unit_cost": 8.00,
            "new_unit_cost": 9.25,
            "operator_note": "[quote-ref: Q-1] rebar add",
        },
    ]
    csv_text = _build_override_history_csv(rows)
    reader = csv.DictReader(io.StringIO(csv_text))
    parsed = list(reader)
    assert len(parsed) == 2
    assert parsed[0]["description"] == "Interior painting"
    assert parsed[0]["original_unit_cost"] == "2.0"
    assert parsed[1]["operator_note"] == "[quote-ref: Q-1] rebar add"


def test_build_override_history_csv_handles_extra_keys() -> None:
    """Extra dict keys (e.g. carried over from the in-memory history
    record) are silently dropped by ``extrasaction='ignore'`` — the
    fieldnames stay stable."""
    rows: list[dict[str, Any]] = [
        {
            "timestamp": "2026-05-28T14:00:00",
            "line_index": 0,
            "description": "test",
            "csi_division": "01",
            "csi_section": "",
            "original_unit_cost": 1.0,
            "new_unit_cost": 2.0,
            "operator_note": "",
            "EXTRA_FIELD_THAT_SHOULD_BE_DROPPED": "ignored",
        },
    ]
    csv_text = _build_override_history_csv(rows)
    assert "EXTRA_FIELD_THAT_SHOULD_BE_DROPPED" not in csv_text
    assert "ignored" not in csv_text


def test_build_override_history_csv_handles_commas_in_note() -> None:
    """A free-text note with embedded commas must round-trip via the
    csv module's quoting (default DictWriter uses QUOTE_MINIMAL)."""
    rows: list[dict[str, Any]] = [
        {
            "timestamp": "2026-05-28T14:00:00",
            "line_index": 0,
            "description": "test",
            "csi_division": "01",
            "csi_section": "",
            "original_unit_cost": 1.0,
            "new_unit_cost": 2.0,
            "operator_note": "a, b, c, with commas",
        },
    ]
    csv_text = _build_override_history_csv(rows)
    parsed = list(csv.DictReader(io.StringIO(csv_text)))
    assert parsed[0]["operator_note"] == "a, b, c, with commas"


# ---------------------------------------------------------------------------
# Edge / integration sanity
# ---------------------------------------------------------------------------


def test_full_helper_chain_simulates_streamlit_round_trip() -> None:
    """End-to-end simulation of what the Streamlit form does:

    1. Sort lines by tier for the dropdown.
    2. Format the selector label.
    3. Apply the override with vendor / quote-ref / free-text.
    4. Format the delta string for the success banner.
    5. CSV-serialise the resulting history row.

    All without touching ``streamlit`` or the form widget itself.
    """
    est = _estimate([
        _line(description="Old line", tier=CostSourceTier.INTERPOLATED,
              unit_cost=2.0, quantity=100.0),
        _line(description="Fresh line", tier=CostSourceTier.EXACT_MATCH,
              unit_cost=8.0, quantity=50.0,
              confidence=0.92, price_confidence=0.95,
              band=CostBand.AUTO_APPROVE),
    ])

    sorted_pairs = _sort_lines_by_tier(est.line_items)
    # EXACT_MATCH should sort ahead of INTERPOLATED.
    assert sorted_pairs[0][1].description == "Fresh line"

    label = _select_line_label(*sorted_pairs[1])
    assert "Old line" in label

    target_idx = sorted_pairs[1][0]
    new_est, note = _apply_operator_override(
        est,
        line_idx=target_idx,
        new_unit_cost=3.50,
        vendor="Sherwin Williams",
        quote_ref="Q-2026-0428",
        free_text="includes mobilisation",
    )
    assert new_est.line_items[target_idx].cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
    assert "[vendor: Sherwin Williams]" in note

    delta = _format_override_delta(est, new_est, target_idx)
    assert "$2.00" in delta and "$3.50" in delta

    csv_text = _build_override_history_csv([{
        "timestamp": "2026-05-28T14:00:00",
        "line_index": target_idx,
        "description": new_est.line_items[target_idx].description,
        "csi_division": new_est.line_items[target_idx].csi_division,
        "csi_section": new_est.line_items[target_idx].csi_section or "",
        "original_unit_cost": 2.0,
        "new_unit_cost": 3.5,
        "operator_note": note,
    }])
    assert "Old line" in csv_text
    assert "Sherwin Williams" in csv_text


def test_initialize_override_session_state_seeds_snapshot_and_history(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """``_initialize_override_session_state`` writes a deep-copied
    snapshot + an empty history into ``st.session_state``."""
    fake_state: dict[str, Any] = {}

    class _FakeStreamlit:
        session_state = fake_state

    monkeypatch.setattr(app_module, "st", _FakeStreamlit)
    est = _estimate([_line(unit_cost=2.0)])
    app_module._initialize_override_session_state(est)
    assert "estimate_original" in fake_state
    assert "override_history" in fake_state
    assert fake_state["override_history"] == []
    snap: Estimate = fake_state["estimate_original"]
    assert snap.line_items[0].unit_cost == pytest.approx(2.0)
    # Mutating the live estimate must not echo into the snapshot.
    out = apply_manual_override(est, 0, new_unit_cost=99.0)
    assert snap.line_items[0].unit_cost == pytest.approx(2.0)
    # And mutating the snapshot via the deep-copy guard must not echo
    # into the input estimate.
    assert out.line_items[0].unit_cost == pytest.approx(99.0)
