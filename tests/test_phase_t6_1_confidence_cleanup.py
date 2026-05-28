"""Phase T6.1 — confidence-propagation cleanup tests.

Covers the four issues called out in the T6.1 brief:

* **Issue 1**: synth derived-item confidence inheritance — panel branch
  breakers, lighting lamps (non-LED), and HVAC disconnects must inherit
  the parent / primary row's confidence with a 5% per-step haircut and
  a 0.45 floor, instead of the pre-T6.1 hard-coded 0.85 / fixture
  default / 0.70 flat values.
* **Issue 2**: backfill chain-derivation decay helper — :func:`chain_decay`
  exposes the multipliers (×0.95 / ×0.90 / ×0.85 / floor 0.45) so
  forward N-from-one fan-outs can call into a single source of truth.
* **Issue 3a**: ``CWICR_MIN_SIMILARITY`` default raised from 0.55 to
  0.75 to align with the ``CATEGORY_MATCH`` boundary.
* **Issue 3b**: ``_combined_band``'s ``qty_confidence is None`` fallback
  raised from 0.70 to 0.80 (= ``LLM_DEFAULT_QTY_CONFIDENCE``) so a
  no-confidence-from-LLM line lands at the AUTO_APPROVE band boundary.

The MANUAL_OVERRIDE end-to-end coverage lives in the dedicated
``tests/test_manual_override.py`` file per the T6.1 brief.
"""

from __future__ import annotations

import pytest

from core.estimator import LLM_DEFAULT_QTY_CONFIDENCE, _combined_band
from core.extraction.takeoff_backfill import (
    CHAIN_DECAY_FLOOR,
    CHAIN_DECAY_MULTIPLIERS,
    chain_decay,
)
from core.extraction.takeoff_synthesis import (
    DERIVATION_FLOOR_CONFIDENCE,
    DERIVATION_HAIRCUT_MULTIPLIER,
    inherit_with_haircut,
    synthesize_hvac_takeoff_items,
    synthesize_lighting_takeoff_items,
    synthesize_panel_takeoff_items,
)
from core.pricing.cwicr_matcher import min_similarity_threshold
from core.schemas import (
    CircuitEntry,
    CostBand,
    HVACEquipmentRecord,
    LightingFixtureRecord,
    PanelRecord,
)


# ---------------------------------------------------------------------------
# Issue 1 — derivation-confidence inheritance helpers
# ---------------------------------------------------------------------------


def test_derivation_constants_match_t6_1_brief() -> None:
    """The 0.95 multiplier + 0.45 floor must be exposed for tests to pin."""
    assert DERIVATION_HAIRCUT_MULTIPLIER == 0.95
    assert DERIVATION_FLOOR_CONFIDENCE == 0.45


def test_inherit_with_haircut_high_confidence_source() -> None:
    """A 0.95 source produces a 0.9025 derivation (still AUTO_APPROVE-adjacent)."""
    assert inherit_with_haircut(0.95) == pytest.approx(0.9025)


def test_inherit_with_haircut_qty_published_lighting_source() -> None:
    """The lighting QTY-published 0.90 confidence yields ~0.855 lamp confidence."""
    assert inherit_with_haircut(0.90) == pytest.approx(0.855)


def test_inherit_with_haircut_hand_takeoff_source_floored_above_0_45() -> None:
    """A 0.55 hand-takeoff source yields 0.5225 (above the 0.45 floor)."""
    assert inherit_with_haircut(0.55) == pytest.approx(0.5225)


def test_inherit_with_haircut_low_source_clamped_to_floor() -> None:
    """A 0.30 source × 0.95 = 0.285 → clamps up to the 0.45 floor."""
    assert inherit_with_haircut(0.30) == pytest.approx(0.45)


def test_inherit_with_haircut_zero_source_returns_floor() -> None:
    assert inherit_with_haircut(0.0) == pytest.approx(0.45)


def test_inherit_with_haircut_one_source_just_below_one() -> None:
    """A perfect 1.0 source still gets the haircut: 0.95."""
    assert inherit_with_haircut(1.0) == pytest.approx(0.95)


def test_inherit_with_haircut_clamps_out_of_range_inputs() -> None:
    """Negative / above-1 inputs clamp into [0, 1] before multiplying."""
    assert inherit_with_haircut(-0.5) == pytest.approx(0.45)
    assert inherit_with_haircut(1.5) == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# Issue 1 — applied to synth functions (panel / lighting / HVAC)
# ---------------------------------------------------------------------------


def _panel(confidence: float = 0.85) -> PanelRecord:
    return PanelRecord(
        panel_id="PNL-A",
        voltage="120/208V",
        phase_count=3,
        main_breaker_amps=200,
        bus_amps=200,
        mcb_or_mlo="MCB",
        circuits=[
            CircuitEntry(circuit_number=str(i), breaker_amps=20,
                         load_description=f"ckt {i}")
            for i in range(1, 5)
        ],
        confidence=confidence,
    )


def test_panel_breaker_row_inherits_panel_confidence_with_haircut() -> None:
    """Pre-T6.1: 0.85 flat. Post-T6.1: 0.95 source → 0.9025 (AUTO)."""
    items = synthesize_panel_takeoff_items([_panel(confidence=0.95)])
    breaker = next(li for li in items if "Branch breakers" in li.description)
    assert breaker.confidence == pytest.approx(0.9025)


def test_panel_breaker_row_default_panel_lands_in_review_band() -> None:
    """Default 0.85 panel → 0.8075 breaker (still OPERATOR_REVIEW)."""
    items = synthesize_panel_takeoff_items([_panel(confidence=0.85)])
    breaker = next(li for li in items if "Branch breakers" in li.description)
    assert breaker.confidence == pytest.approx(0.8075)


def test_panel_breaker_row_low_panel_clamps_to_floor() -> None:
    """A 0.30 panel source clamps the breaker to the 0.45 derivation floor."""
    items = synthesize_panel_takeoff_items([_panel(confidence=0.30)])
    breaker = next(li for li in items if "Branch breakers" in li.description)
    assert breaker.confidence == pytest.approx(0.45)


def test_panel_enclosure_keeps_unmodified_panel_confidence() -> None:
    """The PRIMARY enclosure row is unaffected — only DERIVED breakers get
    the haircut."""
    items = synthesize_panel_takeoff_items([_panel(confidence=0.95)])
    enclosure = next(li for li in items if "Panelboard" in li.description)
    assert enclosure.confidence == pytest.approx(0.95)


def _fixture(
    *, quantity: int | None = None, confidence: float = 0.85,
    lamp_type: str = "FLUORESCENT",
) -> LightingFixtureRecord:
    return LightingFixtureRecord(
        fixture_tag="A1",
        description="2x4 fluorescent troffer",
        wattage=64.0,
        voltage="277V",
        lamp_type=lamp_type,
        mounting="RECESSED",
        quantity=quantity,
        confidence=confidence,
    )


def test_lighting_lamp_inherits_qty_published_fixture_row_with_haircut() -> None:
    """QTY-published fixture row sits at 0.90 → lamp lands at ~0.855 (REVIEW)."""
    items = synthesize_lighting_takeoff_items([_fixture(quantity=10)])
    lamp = next(li for li in items if "lamp/driver" in li.description.lower())
    assert lamp.confidence == pytest.approx(0.855)


def test_lighting_lamp_inherits_hand_takeoff_fixture_row_with_haircut() -> None:
    """No-QTY fixture row sits at 0.55 → lamp lands at 0.5225 (HAND)."""
    items = synthesize_lighting_takeoff_items([_fixture(quantity=None)])
    lamp = next(li for li in items if "lamp/driver" in li.description.lower())
    assert lamp.confidence == pytest.approx(0.5225)


def test_lighting_led_fixture_emits_no_lamp_row() -> None:
    """LED-integrated fixtures still skip the lamp row entirely."""
    items = synthesize_lighting_takeoff_items([
        _fixture(quantity=10, lamp_type="LED"),
    ])
    assert not any("lamp/driver" in li.description.lower() for li in items)


def _hvac(
    *, equipment_type: str = "AHU", quantity: int | None = None,
    confidence: float = 0.85,
) -> HVACEquipmentRecord:
    return HVACEquipmentRecord(
        equipment_tag=f"{equipment_type}-1",
        equipment_type=equipment_type,
        description=f"{equipment_type} unit",
        manufacturer="Trane",
        model_number="X1",
        capacity_value=2000.0,
        capacity_unit="CFM",
        motor_hp=5.0,
        voltage="480V/3φ",
        phase_count=3,
        quantity=quantity,
        confidence=confidence,
    )


def test_hvac_disconnect_inherits_qty_published_equipment_row_with_haircut() -> None:
    """QTY-published equipment row sits at 0.90 → disconnect at ~0.855."""
    items = synthesize_hvac_takeoff_items([_hvac(quantity=2)])
    disconnect = next(li for li in items if "Disconnect" in li.description)
    assert disconnect.confidence == pytest.approx(0.855)


def test_hvac_disconnect_inherits_hand_takeoff_equipment_row_with_haircut() -> None:
    """No-QTY equipment row sits at 0.55 → disconnect at 0.5225 (HAND)."""
    items = synthesize_hvac_takeoff_items([_hvac(quantity=None)])
    disconnect = next(li for li in items if "Disconnect" in li.description)
    assert disconnect.confidence == pytest.approx(0.5225)


def test_hvac_roughin_keeps_parametric_floor_regardless_of_equipment() -> None:
    """The MEP rough-in stays at 0.45 PARAMETRIC — its uncertainty isn't
    derivation-depth, it's that the operator must walk the plan to fill
    the real scope. Per T6.1 calibration notes, this stays as-is."""
    for qty in (None, 2):
        items = synthesize_hvac_takeoff_items([_hvac(quantity=qty)])
        roughin = next(
            li for li in items if "rough-in" in li.description.lower()
        )
        assert roughin.confidence == pytest.approx(0.45)


# ---------------------------------------------------------------------------
# Issue 2 — chain-decay helper
# ---------------------------------------------------------------------------


def test_chain_decay_constants_match_t6_1_brief() -> None:
    assert CHAIN_DECAY_MULTIPLIERS == (1.00, 0.95, 0.90, 0.85)
    assert CHAIN_DECAY_FLOOR == 0.45


def test_chain_decay_depth_zero_is_identity() -> None:
    assert chain_decay(0.92, 0) == pytest.approx(0.92)


def test_chain_decay_depth_one_first_step() -> None:
    assert chain_decay(0.92, 1) == pytest.approx(0.874)


def test_chain_decay_depth_two_second_step() -> None:
    assert chain_decay(0.92, 2) == pytest.approx(0.828)


def test_chain_decay_depth_three_third_step() -> None:
    assert chain_decay(0.92, 3) == pytest.approx(0.782)


def test_chain_decay_depth_four_clamps_to_third_step() -> None:
    """Depth ≥ 4 keeps the third-step multiplier (0.85) per the spec."""
    assert chain_decay(0.92, 4) == chain_decay(0.92, 3)
    assert chain_decay(0.92, 10) == chain_decay(0.92, 3)


def test_chain_decay_floors_at_0_45() -> None:
    """A 0.40 source × 0.85 = 0.34 → clamps up to the 0.45 floor."""
    assert chain_decay(0.40, 3) == pytest.approx(0.45)


def test_chain_decay_negative_depth_treated_as_zero() -> None:
    assert chain_decay(0.92, -3) == pytest.approx(0.92)


# ---------------------------------------------------------------------------
# Issue 3a — CWICR_MIN_SIMILARITY default
# ---------------------------------------------------------------------------


def test_cwicr_min_similarity_default_is_0_75(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Phase T6.1 raised the default from 0.55 → 0.75."""
    monkeypatch.delenv("CWICR_MIN_SIMILARITY", raising=False)
    assert min_similarity_threshold() == pytest.approx(0.75)


def test_cwicr_min_similarity_env_override_still_works(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Tests that need the legacy 0.55 floor set the env var explicitly."""
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "0.55")
    assert min_similarity_threshold() == pytest.approx(0.55)


def test_cwicr_min_similarity_env_invalid_falls_back_to_default(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "not-a-float")
    assert min_similarity_threshold() == pytest.approx(0.75)


def test_cwicr_min_similarity_env_clamped_to_0_1(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "1.5")
    assert min_similarity_threshold() == pytest.approx(1.0)
    monkeypatch.setenv("CWICR_MIN_SIMILARITY", "-0.3")
    assert min_similarity_threshold() == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# Issue 3b — LLM default qty bumped 0.70 → 0.80
# ---------------------------------------------------------------------------


def test_llm_default_qty_constant_is_0_80() -> None:
    """The runtime LLM-no-confidence fallback bumped from 0.70 → 0.80."""
    assert LLM_DEFAULT_QTY_CONFIDENCE == pytest.approx(0.80)


def test_combined_band_qty_none_uses_t6_1_default() -> None:
    """``qty_confidence=None`` × price_confidence=1.0 → 0.80 → OPERATOR_REVIEW.

    0.80 is the OPERATOR_REVIEW band boundary the BB calibration math
    targets: above the 0.65 REVIEW floor, below the 0.85 AUTO_APPROVE
    floor. The legacy 0.70 LLM default × 0.65 INTERPOLATED = 0.455 →
    HAND_TAKEOFF; 0.80 × 0.95 (seed-DB) = 0.76 → REVIEW (the BB-intended
    happy-path band). Pre-T6.1 the same call returned REVIEW too (0.70 ×
    1.0 = 0.70 → REVIEW), but the pre-T6.1 default flipped to HAND much
    earlier on degraded prices.
    """
    band = _combined_band(None, 1.0, suppressed=False)
    assert band == CostBand.OPERATOR_REVIEW


def test_combined_band_qty_none_with_seed_db_price_lands_at_review() -> None:
    """None × 0.95 (seed-DB EXACT) = 0.76 → OPERATOR_REVIEW."""
    band = _combined_band(None, 0.95, suppressed=False)
    assert band == CostBand.OPERATOR_REVIEW


def test_combined_band_qty_none_with_low_price_demotes_to_hand() -> None:
    """None × 0.5 = 0.40 → HAND_TAKEOFF (price-side dominates here)."""
    band = _combined_band(None, 0.5, suppressed=False)
    assert band == CostBand.HAND_TAKEOFF


# ---------------------------------------------------------------------------
# Calibration math — Worker BB's intent
# ---------------------------------------------------------------------------


def test_bb_calibration_default_llm_line_min_similarity_cwicr_lands_in_hand() -> None:
    """Per T6.1 calibration notes:
    qty=0.80 × price=(0.75 × 0.85) = 0.51 → HAND_TAKEOFF (still flagged
    for review, which is correct because BOTH defaults are at boundaries).
    """
    qty = 0.80  # T6.1 LLM default
    price = round(0.75 * 0.85, 4)  # CATEGORY_MATCH at min similarity
    combined = round(qty * price, 4)
    assert combined == pytest.approx(0.51)
    assert _combined_band(qty, price, suppressed=False) == CostBand.HAND_TAKEOFF


def test_bb_calibration_default_llm_line_seed_db_lands_in_review() -> None:
    """qty=0.80 × price=0.95 (seed-DB EXACT) = 0.76 → OPERATOR_REVIEW."""
    qty = 0.80
    price = 0.95
    assert _combined_band(qty, price, suppressed=False) == CostBand.OPERATOR_REVIEW


def test_bb_calibration_high_confidence_t1_t5_line_with_exact_cwicr_lands_in_auto() -> None:
    """qty=0.90 × price=0.95 (EXACT_MATCH) = 0.855 → AUTO_APPROVE.

    Confirms the post-T6.1 calibration still routes high-confidence
    typed-extractor lines (T1–T5.1 at 0.90+) plus exact-match CWICR
    into AUTO_APPROVE band.
    """
    qty = 0.90
    price = 0.95
    assert _combined_band(qty, price, suppressed=False) == CostBand.AUTO_APPROVE


def test_t6_default_07_line_still_lands_in_review() -> None:
    """The schema-level default 0.70 is preserved per the no-touch-schemas
    constraint — pre-T6.1 fixtures with explicit ``confidence=0.7``
    continue to band identically (0.70 × 0.95 = 0.665 → REVIEW).
    """
    qty = 0.70
    price = 0.95
    assert _combined_band(qty, price, suppressed=False) == CostBand.OPERATOR_REVIEW
