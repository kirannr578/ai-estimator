"""Phase T9.1 — Bid Alternates session-state initialization + reset flows.

Tests for :func:`app._initialize_alternates_session_state` (and the
fingerprint helper that drives reset detection). The Streamlit
``session_state`` API behaves like a dict for our purposes, so we
monkey-patch it with a real dict per test and exercise the
init / re-visit / reset flows end-to-end without needing a Streamlit
runtime.

Covers the keys the T9.1 brief specifies:

* ``alternates_selected_ids``   (set[str])
* ``alternates_operator_notes`` (dict[str, str])
* ``alternates_operator_deltas`` (dict[str, float])

Plus the internal fingerprint key (``alternates_estimate_fingerprint``)
which drives the "new estimate clears session" semantics so a fresh
analyze run resets the operator's working scenario.
"""

from __future__ import annotations

import pytest

import app as app_module
from app import (
    _ALTERNATES_SS_DELTAS,
    _ALTERNATES_SS_ESTIMATE_FP,
    _ALTERNATES_SS_NOTES,
    _ALTERNATES_SS_SELECTED,
    _alternates_estimate_fingerprint,
    _initialize_alternates_session_state,
)
from core.schemas import (
    AlternateLineEstimate,
    AlternatePricingBasis,
    AlternateType,
    Estimate,
)


@pytest.fixture
def fake_session_state(monkeypatch):
    """Replace ``st.session_state`` with a plain dict for the test."""
    state: dict = {}
    monkeypatch.setattr(app_module.st, "session_state", state)
    return state


def _ale(
    alternate_id: str = "A1",
    *,
    cost_delta: float | None = 1000.0,
    alternate_type: AlternateType = AlternateType.ADDITIVE,
    pricing_basis: AlternatePricingBasis = AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
) -> AlternateLineEstimate:
    return AlternateLineEstimate(
        alternate_id=alternate_id,
        alternate_type=alternate_type,
        description=f"Alt {alternate_id}",
        cost_delta=cost_delta,
        pricing_basis=pricing_basis,
        confidence=0.85,
    )


def _estimate(
    *,
    project_name: str = "T9.1 session",
    line_count: int = 0,
    alternates: list[AlternateLineEstimate] | None = None,
    selected_default: set[str] | None = None,
) -> Estimate:
    from core.schemas import CostCategory, CostLine

    line_items = [
        CostLine(
            csi_division="09",
            csi_section="09 91 23",
            description=f"line-{i}",
            quantity=1.0,
            unit="EA",
            unit_cost=1.0,
            total_cost=1.0,
            cost_category=CostCategory.OTHER,
        )
        for i in range(line_count)
    ]
    return Estimate(
        project_name=project_name,
        line_items=line_items,
        alternates=alternates or [],
        alternates_selected_default=selected_default or set(),
    )


# ---------------------------------------------------------------------------
# First-visit initialization
# ---------------------------------------------------------------------------


def test_first_visit_seeds_three_keys_from_empty_session(fake_session_state) -> None:
    est = _estimate(alternates=[_ale("A1"), _ale("A2")])
    assert _ALTERNATES_SS_SELECTED not in fake_session_state
    _initialize_alternates_session_state(est)
    assert _ALTERNATES_SS_SELECTED in fake_session_state
    assert _ALTERNATES_SS_NOTES in fake_session_state
    assert _ALTERNATES_SS_DELTAS in fake_session_state


def test_first_visit_seeds_selected_from_alternates_selected_default(
    fake_session_state,
) -> None:
    """The default-selected set is whatever ``Estimate.alternates_selected_default``
    carries — populated by ``attach_alternates_to_estimate`` from any
    ``AlternateLine`` flagged ``included_by_default=True``."""
    est = _estimate(
        alternates=[_ale("A1"), _ale("A2")],
        selected_default={"A1"},
    )
    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == {"A1"}


def test_first_visit_with_no_default_seeds_empty_selection(fake_session_state) -> None:
    est = _estimate(alternates=[_ale("A1"), _ale("A2")])
    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == set()


def test_first_visit_seeds_empty_notes_and_deltas(fake_session_state) -> None:
    est = _estimate(alternates=[_ale("A1")])
    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_NOTES] == {}
    assert fake_session_state[_ALTERNATES_SS_DELTAS] == {}


# ---------------------------------------------------------------------------
# Idempotency — re-visit doesn't clobber operator state
# ---------------------------------------------------------------------------


def test_re_visit_preserves_in_progress_selection(fake_session_state) -> None:
    est = _estimate(alternates=[_ale("A1"), _ale("A2")])
    _initialize_alternates_session_state(est)
    fake_session_state[_ALTERNATES_SS_SELECTED] = {"A1", "A2"}
    fake_session_state[_ALTERNATES_SS_NOTES] = {"A1": "operator note"}
    fake_session_state[_ALTERNATES_SS_DELTAS] = {"A2": 500.0}

    _initialize_alternates_session_state(est)

    assert fake_session_state[_ALTERNATES_SS_SELECTED] == {"A1", "A2"}
    assert fake_session_state[_ALTERNATES_SS_NOTES] == {"A1": "operator note"}
    assert fake_session_state[_ALTERNATES_SS_DELTAS] == {"A2": 500.0}


def test_re_visit_with_same_estimate_object_is_noop(fake_session_state) -> None:
    """The fingerprint matches → no overwrite even of stamped keys."""
    est = _estimate(
        alternates=[_ale("A1")], selected_default={"A1"}
    )
    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == {"A1"}
    fake_session_state[_ALTERNATES_SS_SELECTED].clear()  # operator deselected
    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == set()  # not re-seeded


# ---------------------------------------------------------------------------
# Reset on a new estimate load
# ---------------------------------------------------------------------------


def test_new_estimate_load_clears_session(fake_session_state) -> None:
    """A fresh analyze run produces a NEW estimate object with a different
    fingerprint (line_items count or alternates list change), which
    triggers a session-state reset."""
    est_old = _estimate(alternates=[_ale("A1")], line_count=10)
    _initialize_alternates_session_state(est_old)
    fake_session_state[_ALTERNATES_SS_SELECTED] = {"A1"}
    fake_session_state[_ALTERNATES_SS_NOTES] = {"A1": "stale note"}

    est_new = _estimate(
        alternates=[_ale("B1"), _ale("B2")],
        line_count=20,
        selected_default={"B2"},
    )
    _initialize_alternates_session_state(est_new)

    assert fake_session_state[_ALTERNATES_SS_SELECTED] == {"B2"}
    assert fake_session_state[_ALTERNATES_SS_NOTES] == {}
    assert fake_session_state[_ALTERNATES_SS_DELTAS] == {}


def test_estimate_with_changed_alternates_triggers_reset(fake_session_state) -> None:
    """Even with the same project_name and line-item count, a different
    alternates list (different IDs or deltas) flips the fingerprint."""
    est_a = _estimate(alternates=[_ale("A1", cost_delta=1000.0)], line_count=5)
    _initialize_alternates_session_state(est_a)
    fake_session_state[_ALTERNATES_SS_SELECTED] = {"A1"}

    est_b = _estimate(alternates=[_ale("A1", cost_delta=2000.0)], line_count=5)
    _initialize_alternates_session_state(est_b)

    # Fingerprint changed → session reset to the (empty) default of est_b.
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == set()


# ---------------------------------------------------------------------------
# Toggle / operator entry persistence to session
# ---------------------------------------------------------------------------


def test_toggle_selection_updates_set_in_session(fake_session_state) -> None:
    """Adding to / removing from the selection set persists across re-init
    calls (which the Streamlit re-render triggers on every checkbox click)."""
    est = _estimate(alternates=[_ale("A1"), _ale("A2"), _ale("A3")])
    _initialize_alternates_session_state(est)

    sel = fake_session_state[_ALTERNATES_SS_SELECTED]
    sel.add("A1")
    sel.add("A3")

    _initialize_alternates_session_state(est)  # idempotent re-call
    assert fake_session_state[_ALTERNATES_SS_SELECTED] == {"A1", "A3"}


def test_operator_delta_persists_to_session(fake_session_state) -> None:
    """An operator-entered cost_delta lands in
    ``alternates_operator_deltas`` and survives a re-init."""
    est = _estimate(
        alternates=[
            _ale(
                "M1",
                cost_delta=None,
                pricing_basis=AlternatePricingBasis.MISSING,
            )
        ],
    )
    _initialize_alternates_session_state(est)

    fake_session_state[_ALTERNATES_SS_DELTAS]["M1"] = 1500.0
    fake_session_state[_ALTERNATES_SS_NOTES]["M1"] = "from vendor email"

    _initialize_alternates_session_state(est)
    assert fake_session_state[_ALTERNATES_SS_DELTAS] == {"M1": 1500.0}
    assert fake_session_state[_ALTERNATES_SS_NOTES] == {"M1": "from vendor email"}


# ---------------------------------------------------------------------------
# Fingerprint helper directly
# ---------------------------------------------------------------------------


def test_fingerprint_matches_for_identical_estimates() -> None:
    a = _estimate(alternates=[_ale("A1", cost_delta=10.0)], line_count=3)
    b = _estimate(alternates=[_ale("A1", cost_delta=10.0)], line_count=3)
    assert _alternates_estimate_fingerprint(a) == _alternates_estimate_fingerprint(b)


def test_fingerprint_differs_when_line_count_changes() -> None:
    a = _estimate(alternates=[_ale("A1")], line_count=5)
    b = _estimate(alternates=[_ale("A1")], line_count=6)
    assert _alternates_estimate_fingerprint(a) != _alternates_estimate_fingerprint(b)


def test_fingerprint_differs_when_alternate_delta_changes() -> None:
    a = _estimate(alternates=[_ale("A1", cost_delta=100.0)])
    b = _estimate(alternates=[_ale("A1", cost_delta=200.0)])
    assert _alternates_estimate_fingerprint(a) != _alternates_estimate_fingerprint(b)
