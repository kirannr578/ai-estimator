"""Phase T9.3 — wire-up between T9.1 session-state selection and T9.2 PDF.

Tests for the pure helpers added to ``app.py`` that resolve the
``alternates_config`` dict passed into
:func:`core.exporter_pdf.build_quote_pdf`:

* :func:`_resolve_alternates_config_for_pdf` — merges the operator's
  on-screen "Bid Alternates" tab selection (a ``set[str]`` in
  ``st.session_state["alternates_selected_ids"]``, populated by T9.1)
  with a base config dict (typically loaded from
  ``config/client_quote.json``'s ``alternates_section`` block).
* :func:`_load_alternates_section_config` — re-parses the raw JSON to
  surface the ``alternates_section`` block (which ``QuoteConfig``
  silently drops because the Pydantic model doesn't model it).

Plus one end-to-end smoke that runs the resolved config through the
real :func:`core.exporter_pdf.build_quote_pdf` and verifies the
rendered PDF reflects the operator's session selection — NOT the
estimate's persisted default — closing the T9 family loop.

Test pattern mirrors `tests/test_streamlit_alternates_ui.py` (T9.1):
pure helpers tested without a Streamlit runtime; a smoke that
imports `app` confirms the form-wiring parses cleanly.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from app import (
    _load_alternates_section_config,
    _resolve_alternates_config_for_pdf,
)


# ---------------------------------------------------------------------------
# _resolve_alternates_config_for_pdf — pure helper
# ---------------------------------------------------------------------------


class TestResolveAlternatesConfigForPdf:
    def test_empty_session_no_base_config(self) -> None:
        """Missing key in session, no base config → empty selection only."""
        out = _resolve_alternates_config_for_pdf({}, None)
        assert out == {"default_selection": []}

    def test_session_selection_no_base_config_sorted(self) -> None:
        """Selection from a set must round-trip to a deterministic sorted list."""
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": {"A2", "A1"}}, None
        )
        assert out == {"default_selection": ["A1", "A2"]}

    def test_session_selection_merges_with_base_config(self) -> None:
        """Operator selection wins; other base keys flow through."""
        base = {"enabled": True, "intro_paragraph": "Custom intro."}
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": {"A1"}}, base
        )
        assert out == {
            "enabled": True,
            "intro_paragraph": "Custom intro.",
            "default_selection": ["A1"],
        }

    def test_session_selection_overrides_base_default_selection(self) -> None:
        """Even if base_config carries default_selection, operator wins."""
        base = {"default_selection": ["A2", "A3"]}
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": {"A1"}}, base
        )
        assert out["default_selection"] == ["A1"]
        # Crucially, A2/A3 from the base config must NOT bleed through.
        assert "A2" not in out["default_selection"]
        assert "A3" not in out["default_selection"]

    def test_missing_key_in_session_returns_empty_selection(self) -> None:
        """``None`` session selection (key absent) → empty list, NO crash."""
        # Session state without the key at all.
        out = _resolve_alternates_config_for_pdf({"unrelated_key": 42}, None)
        assert out == {"default_selection": []}

    def test_none_session_state_does_not_crash(self) -> None:
        """A literal ``None`` session_state is tolerated (defensive)."""
        out = _resolve_alternates_config_for_pdf(None, None)
        assert out == {"default_selection": []}

    def test_frozenset_selection_coerced_to_sorted_list(self) -> None:
        """Defensive coercion — frozenset / tuple / list all work."""
        for selection in (frozenset({"B", "A"}), ("B", "A"), ["B", "A"]):
            out = _resolve_alternates_config_for_pdf(
                {"alternates_selected_ids": selection}, None
            )
            assert out == {"default_selection": ["A", "B"]}, (
                f"failed for {type(selection).__name__}"
            )

    def test_determinism_same_inputs_same_output(self) -> None:
        """Identical inputs → identical outputs (no set-iteration entropy)."""
        sel = {"Z1", "M5", "A2", "Q9"}
        base = {"enabled": True, "footer_note": "Note."}
        first = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": set(sel)}, dict(base)
        )
        for _ in range(10):
            again = _resolve_alternates_config_for_pdf(
                {"alternates_selected_ids": set(sel)}, dict(base)
            )
            assert again == first
        # And the list itself is sorted.
        assert first["default_selection"] == ["A2", "M5", "Q9", "Z1"]

    def test_empty_session_selection_is_authoritative(self) -> None:
        """Operator visited tab + deselected everything → empty list returned.

        This is the key T9.3 design choice: an empty session selection
        means "operator chose to render no alternates", NOT "fall back
        to estimate.alternates_selected_default". The PDF render must
        agree with the on-screen tally even when the operator picked
        zero alternates.
        """
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": set()}, None
        )
        assert out == {"default_selection": []}

    def test_base_config_preserves_extra_alternates_section_keys(self) -> None:
        """Unknown / future-proof keys flow through the merge."""
        base = {
            "enabled": True,
            "intro_paragraph": "X",
            "footer_note": "Y",
            "future_key": {"nested": "value"},
        }
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": {"A1"}}, base
        )
        assert out["future_key"] == {"nested": "value"}
        assert out["enabled"] is True
        assert out["intro_paragraph"] == "X"
        assert out["footer_note"] == "Y"
        assert out["default_selection"] == ["A1"]

    def test_input_dicts_not_mutated(self) -> None:
        """Mutation safety — caller's session_state and base_config untouched."""
        session = {"alternates_selected_ids": {"A1"}, "other": 1}
        base = {"enabled": True, "default_selection": ["A2"]}
        session_snapshot = {
            "alternates_selected_ids": {"A1"},
            "other": 1,
        }
        base_snapshot = {"enabled": True, "default_selection": ["A2"]}

        out = _resolve_alternates_config_for_pdf(session, base)

        assert session == session_snapshot
        assert base == base_snapshot
        # And the returned dict is a new object, not the same reference.
        assert out is not base
        # Mutating the output must not mutate the input base.
        out["default_selection"].append("HACK")
        assert base["default_selection"] == ["A2"]

    def test_non_iterable_selection_falls_back_to_empty(self) -> None:
        """A garbage non-iterable in session state → empty selection (defensive)."""
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": 42}, None
        )
        assert out == {"default_selection": []}

    def test_selection_with_non_string_items_coerced_to_str(self) -> None:
        """Defensive: non-string items in the session set are stringified.

        Should never happen in practice (T9.1 always populates with
        ``alternate_id: str``), but guarding against an upstream bug
        introducing an int / UUID is cheap and prevents a downstream
        ``TypeError`` from the PDF renderer's ``set[str]`` machinery.
        """
        out = _resolve_alternates_config_for_pdf(
            {"alternates_selected_ids": {"A1", 2, "A3"}}, None
        )
        assert out["default_selection"] == sorted(["A1", "2", "A3"])


# ---------------------------------------------------------------------------
# _load_alternates_section_config
# ---------------------------------------------------------------------------


class TestLoadAlternatesSectionConfig:
    def test_returns_dict_when_block_present(self) -> None:
        """Real ``config/client_quote.json`` carries the block (T9.2 added it)."""
        out = _load_alternates_section_config()
        assert isinstance(out, dict)
        # The shipped config has at least these keys (T9.2 bump).
        # We only check the type of the call's result; downstream
        # consumers (build_quote_pdf) tolerate any subset / superset.
        assert "enabled" in out

    def test_missing_file_returns_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """No config file on disk → empty dict, no crash."""
        import app as app_mod

        monkeypatch.setattr(
            app_mod, "CLIENT_QUOTE_CFG_PATH", tmp_path / "missing.json"
        )
        assert _load_alternates_section_config() == {}

    def test_invalid_json_returns_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Garbage JSON → empty dict (logs a warning, never raises)."""
        import app as app_mod

        bad = tmp_path / "bad.json"
        bad.write_text("{ this is : not json", encoding="utf-8")
        monkeypatch.setattr(app_mod, "CLIENT_QUOTE_CFG_PATH", bad)
        assert _load_alternates_section_config() == {}

    def test_missing_block_returns_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """JSON without ``alternates_section`` key → empty dict."""
        import app as app_mod

        cfg = tmp_path / "cfg.json"
        cfg.write_text(json.dumps({"company": {"name": "X"}}), encoding="utf-8")
        monkeypatch.setattr(app_mod, "CLIENT_QUOTE_CFG_PATH", cfg)
        assert _load_alternates_section_config() == {}

    def test_block_not_object_returns_empty_dict(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """``alternates_section`` set to a non-object → empty dict."""
        import app as app_mod

        cfg = tmp_path / "cfg.json"
        cfg.write_text(
            json.dumps({"alternates_section": "not-a-dict"}), encoding="utf-8"
        )
        monkeypatch.setattr(app_mod, "CLIENT_QUOTE_CFG_PATH", cfg)
        assert _load_alternates_section_config() == {}

    def test_full_block_round_trips(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A populated block round-trips through the loader unchanged."""
        import app as app_mod

        block = {
            "enabled": True,
            "intro_paragraph": "Custom intro.",
            "footer_note": "Custom footer.",
            "default_selection": ["X1"],
        }
        cfg = tmp_path / "cfg.json"
        cfg.write_text(
            json.dumps({"alternates_section": block, "company": {}}),
            encoding="utf-8",
        )
        monkeypatch.setattr(app_mod, "CLIENT_QUOTE_CFG_PATH", cfg)
        out = _load_alternates_section_config()
        assert out == block


# ---------------------------------------------------------------------------
# End-to-end smoke — resolved config drives a real PDF render.
# ---------------------------------------------------------------------------


reportlab = pytest.importorskip("reportlab")
fitz = pytest.importorskip("fitz")  # PyMuPDF, already a project dep


def test_e2e_session_selection_drives_pdf_tally(tmp_path: Path) -> None:
    """End-to-end: session_state selection → resolved config → rendered PDF.

    Builds a 3-alternate estimate with a persisted default selection of
    ``{"Alternate-2"}``, simulates an operator who deselected the default
    and selected ``{"Alternate-1"}`` instead via the T9.1 tab, runs the
    resolved alternates_config through the T9.2 renderer, and asserts
    the PDF's "Base + selected alternates" tally row reflects ONLY
    Alternate-1's $5,000 delta — NOT Alternate-2 ($3,000) or
    Alternate-3 ($1,000) or any combination thereof.

    This test pins the T9.3 wire-up contract end-to-end. If anyone
    later regresses the call site to drop the ``alternates_config``
    kwarg, this test fails with a clear "selection didn't reach the
    PDF" diagnostic.
    """
    from core.exporter_pdf import build_quote_pdf
    from core.schemas import (
        AlternateLineEstimate,
        AlternatePricingBasis,
        AlternateType,
        CostCategory,
        CostLine,
        Estimate,
        PaymentMilestone,
        PaymentSchedule,
        QuoteConfig,
        QuoteMeta,
        SiteInfo,
    )
    from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix

    alts = [
        AlternateLineEstimate(
            alternate_id="Alternate-1",
            alternate_type=AlternateType.ADDITIVE,
            description="Add option 1",
            cost_delta=5000.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        ),
        AlternateLineEstimate(
            alternate_id="Alternate-2",
            alternate_type=AlternateType.ADDITIVE,
            description="Add option 2",
            cost_delta=3000.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        ),
        AlternateLineEstimate(
            alternate_id="Alternate-3",
            alternate_type=AlternateType.ADDITIVE,
            description="Add option 3",
            cost_delta=1000.0,
            pricing_basis=AlternatePricingBasis.EXTRACTED_FROM_BID_FORM,
        ),
    ]
    estimate = Estimate(
        project_name="T9.3 Smoke",
        region_multiplier=1.0,
        line_items=[
            CostLine(
                csi_division="09",
                csi_section="09 91 23",
                description="Painting",
                quantity=100.0,
                unit="SF",
                unit_cost=100.0,
                total_cost=10_000.0,
                cost_category=CostCategory.SUBCONTRACTOR,
                confidence=0.92,
            )
        ],
        alternates=alts,
        # Estimate's persisted default — operator's session selection
        # MUST override this in the rendered PDF.
        alternates_selected_default={"Alternate-2"},
    )
    project = ProjectModel(
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
        bid_packages=[],
        project_info=ProjectInfo(
            name="T9.3 Smoke", number="2026-T93", location="Austin, TX"
        ),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=[],
    )
    quote_config = QuoteConfig(
        quote_meta=QuoteMeta(
            scope_blurb="T9.3 e2e scope.", payment_terms_text="Net 30."
        ),
        payment_schedule=PaymentSchedule(
            mode="percentage",
            milestones=[
                PaymentMilestone(label="Mobilization", percentage=30.0),
                PaymentMilestone(label="Rough", percentage=30.0),
                PaymentMilestone(label="Finish", percentage=30.0),
                PaymentMilestone(label="Retainage", percentage=10.0),
            ],
        ),
    )

    # Operator's on-screen selection: only Alternate-1.
    fake_session_state = {"alternates_selected_ids": {"Alternate-1"}}
    base_cfg = {"enabled": True}
    resolved = _resolve_alternates_config_for_pdf(fake_session_state, base_cfg)

    # The resolved config must surface the operator's pick.
    assert resolved == {"enabled": True, "default_selection": ["Alternate-1"]}

    out = tmp_path / "t9_3_smoke.pdf"
    build_quote_pdf(
        estimate=estimate,
        project=project,
        quote_config=quote_config,
        out_path=out,
        csi_titles={"09": "Finishes"},
        alternates_config=resolved,
    )
    assert out.is_file()

    with fitz.open(out) as doc:
        text = "\n".join(page.get_text() for page in doc)

    # The "Base + selected alternates" tally row must reflect ONLY
    # Alternate-1 (the operator's session selection), NOT Alternate-2
    # (the estimate's persisted default).
    assert "Base + selected alternates" in text

    # Selected delta = +$5,000.00 (Alt-1 only). Each alt's cost_delta
    # also appears in the alternates table, so we use a *count* check:
    # +$5,000.00 must appear at least TWICE (once in the table row
    # for Alt-1 + once as the selected-row delta). +$3,000.00 must
    # appear EXACTLY ONCE (only in the table row for Alt-2 — never as
    # the selected delta, which would mean the estimate's default
    # leaked through). Same for +$1,000.00 (Alt-3, never selected).
    assert text.count("+$5,000.00") >= 2, (
        f"Operator's session selection (Alt-1, +$5,000) didn't drive "
        f"the tally; count={text.count('+$5,000.00')}"
    )
    assert text.count("+$3,000.00") == 1, (
        f"Estimate default (Alt-2, +$3,000) leaked into selected tally; "
        f"count={text.count('+$3,000.00')}"
    )
    assert text.count("+$1,000.00") == 1, (
        f"Unselected Alt-3 leaked into tally; "
        f"count={text.count('+$1,000.00')}"
    )

    # Sanity: the "Base + all additive alternates" row's delta is the
    # sum of every additive ($5,000 + $3,000 + $1,000 = $9,000),
    # which must appear exactly once (in that row, NOT in the table
    # for any individual alt).
    assert "+$9,000.00" in text
    assert text.count("+$9,000.00") == 1
