"""Phase T6.4.c.1 — ``app.py`` sub-quote / vendor-CSV apply wire-up tests.

T6.4.c shipped the backend plumbing for source-tag propagation into
``CostLine.notes``: new module-level constants
(:data:`SOURCE_TAG_VENDOR_CSV`, :data:`SOURCE_TAG_SUBQUOTE_TABULAR`,
:data:`SOURCE_TAG_SUBQUOTE_LLM`), a keyword-only ``source_tag`` kwarg
on :func:`~core.pricing.batch_override.apply_batch_plan`, and a thin
:func:`~core.pricing.subquote_parser.apply_subquote_plan` wrapper that
picks the right tag based on a boolean ``llm`` flag. T6.4.c.1 is the
follow-up that activates the wrapper in ``app.py``'s three apply call
sites so the tag actually reaches every overridden line's notes cell
end-to-end (T6.3 vendor CSV → ``[vendor-csv]``, T8.1 tabular sub-quote
→ ``[sub-quote]``, T8.2 LLM-vision sub-quote → ``[sub-quote-llm]``).

The Streamlit "Apply" call site is inside a runtime-conditional block
(``if sq_apply_clicked:`` etc.) so the tests follow a two-pronged
approach that mirrors ``tests/test_streamlit_alternates_pdf_wireup.py``
and ``tests/test_subquote_ui.py``:

* **Source-level pins** — read ``app.py`` itself and assert that the
  three apply call sites invoke the right function with the right
  ``source_tag`` / ``llm`` argument. This is the wire-up contract
  T6.4.c.1 specifically ships; downstream regression would silently
  re-introduce ``[batch]`` tags if these pins drift.
* **Backend round-trip** — call the apply functions directly with the
  same arguments ``app.py`` now passes and assert that the produced
  ``CostLine.notes`` field carries the canonical tag at position 0.
  Pins the end-to-end semantic, not just the call shape.

Streamlit-free — no ``streamlit.testing.v1`` runtime. The backend
functions are pure; the call-site checks read the source as text.
"""

from __future__ import annotations

import inspect
import re
from pathlib import Path

import app
from core.pricing.batch_override import (
    SOURCE_TAG_SUBQUOTE_LLM,
    SOURCE_TAG_SUBQUOTE_TABULAR,
    SOURCE_TAG_VENDOR_CSV,
    BatchOverrideRow,
    apply_batch_plan,
    format_batch_operator_note,
    match_cost_lines,
)
from core.pricing.subquote_parser import apply_subquote_plan
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
    description: str = "Lavatory P-1",
    unit_cost: float = 500.0,
    quantity: float = 10.0,
    csi_section: str = "22 41 00",
    notes: str | None = None,
) -> CostLine:
    """Build a single :class:`CostLine` fixture with sensible defaults.

    Mirrors the helper in :mod:`tests.test_subquote_t8_1_integration`
    so the round-trip tests below produce comparable post-apply
    ``CostLine.notes`` content.
    """
    return CostLine(
        csi_division=csi_section.split(" ", 1)[0],
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit="EA",
        unit_cost=unit_cost,
        total_cost=round(unit_cost * quantity, 2),
        cost_category=CostCategory.SUBCONTRACTOR,
        confidence=0.9,
        price_confidence=0.7,
        cost_source_tier=CostSourceTier.INTERPOLATED,
        cost_band=CostBand.OPERATOR_REVIEW,
        cost_source="cwicr:42",
        notes=notes or "",
    )


def _estimate(lines: list[CostLine]) -> Estimate:
    return Estimate(
        project_name="T6.4.c.1 wire-up",
        region_multiplier=1.0,
        contingency_pct=10.0,
        overhead_pct=10.0,
        profit_pct=5.0,
        line_items=lines,
    )


def _row(
    *,
    row_index: int = 2,
    description: str = "Lavatory P-1",
    unit_cost: float = 450.0,
    vendor: str | None = None,
    quote_ref: str | None = None,
    notes: str | None = None,
) -> BatchOverrideRow:
    return BatchOverrideRow(
        row_index=row_index,
        description=description,
        unit_cost=unit_cost,
        vendor=vendor,
        quote_ref=quote_ref,
        notes=notes,
    )


def _app_source() -> str:
    """Return the raw text of ``app.py`` for source-level pin checks.

    Using :func:`inspect.getsource` (rather than re-reading the file
    via ``Path``) means the source-level pins automatically follow any
    test-time monkeypatch of the import path. The two are equivalent
    in CI; the inspector form is the canonical pattern in the suite.
    """
    return inspect.getsource(app)


# ---------------------------------------------------------------------------
# Import-surface pins — T6.4.c.1 brings the new constants + the wrapper
# into ``app.py``'s top-level namespace. A regression that drops any of
# these imports would silently fall back to the legacy ``[batch]`` tag.
# ---------------------------------------------------------------------------


class TestImportSurface:
    def test_app_imports_apply_subquote_plan(self) -> None:
        """``app.py`` must expose ``apply_subquote_plan`` at module scope."""
        assert hasattr(app, "apply_subquote_plan")
        assert callable(app.apply_subquote_plan)

    def test_app_imports_source_tag_vendor_csv(self) -> None:
        """T6.3 vendor-CSV call site needs the canonical vendor-CSV tag."""
        assert hasattr(app, "SOURCE_TAG_VENDOR_CSV")
        assert app.SOURCE_TAG_VENDOR_CSV == "[vendor-csv]"

    def test_app_imports_subquote_source_tag_constants(self) -> None:
        """Both sub-quote tags must be importable for the inline literal swap."""
        assert hasattr(app, "SOURCE_TAG_SUBQUOTE_TABULAR")
        assert hasattr(app, "SOURCE_TAG_SUBQUOTE_LLM")
        assert app.SOURCE_TAG_SUBQUOTE_TABULAR == "[sub-quote]"
        assert app.SOURCE_TAG_SUBQUOTE_LLM == "[sub-quote-llm]"


# ---------------------------------------------------------------------------
# Source-level pins on the three apply call sites
# ---------------------------------------------------------------------------


class TestApplyCallSiteShape:
    def test_subquote_apply_calls_apply_subquote_plan_with_llm_flag(
        self,
    ) -> None:
        """Sub-quote section must call ``apply_subquote_plan(..., llm=...)``.

        T6.4.c.1's central contract: the sub-quote section is the path
        that needs ``[sub-quote]`` / ``[sub-quote-llm]`` tags. The
        wrapper picks the right tag based on the boolean ``llm`` flag.
        """
        source = _app_source()
        match = re.search(
            r"apply_subquote_plan\(\s*estimate,\s*sq_plan,\s*llm=",
            source,
        )
        assert match is not None, (
            "Expected the sub-quote apply call site to invoke "
            "apply_subquote_plan(estimate, sq_plan, llm=...). T6.4.c.1 "
            "ships this wrapper specifically; falling back to "
            "apply_batch_plan(...) at this call site stamps a "
            "[batch] tag instead of the correct sub-quote tag."
        )

    def test_subquote_apply_does_not_call_apply_batch_plan_directly(
        self,
    ) -> None:
        """The sub-quote section must NOT call ``apply_batch_plan`` directly.

        Defensive guard: if a future refactor accidentally reverts to
        ``apply_batch_plan(estimate, sq_plan, ...)`` the tag falls back
        to the legacy ``[batch]`` default. Detect that by searching for
        the exact pre-T6.4.c.1 call shape.
        """
        source = _app_source()
        legacy = re.search(
            r"apply_batch_plan\(\s*estimate,\s*sq_plan",
            source,
        )
        assert legacy is None, (
            "Found apply_batch_plan(estimate, sq_plan, ...) in app.py; "
            "T6.4.c.1 requires apply_subquote_plan(estimate, sq_plan, "
            "llm=...) at the sub-quote apply call site."
        )

    def test_vendor_csv_apply_passes_source_tag_vendor_csv(self) -> None:
        """T6.3 vendor-CSV call site must explicitly pass the vendor-csv tag.

        Without an explicit ``source_tag=`` the call falls back to the
        backward-compat default ``SOURCE_TAG_BATCH`` which is wrong
        provenance for a vendor-CSV ingest.
        """
        source = _app_source()
        match = re.search(
            r"apply_batch_plan\(\s*estimate,\s*plan,"
            r"[\s\S]{0,200}?source_tag=SOURCE_TAG_VENDOR_CSV",
            source,
        )
        assert match is not None, (
            "Expected the T6.3 vendor-CSV apply call site to pass "
            "source_tag=SOURCE_TAG_VENDOR_CSV. Default kwarg falls "
            "back to [batch] which is wrong provenance."
        )

    def test_inline_subquote_tag_literals_replaced_with_constants(
        self,
    ) -> None:
        """Inline ``"[sub-quote-llm]"`` / ``"[sub-quote]"`` literals are gone.

        T6.4.c.1 swaps the override_history-side
        ``format_batch_operator_note(...)`` call to use the canonical
        constants so the operator-history log and the
        ``CostLine.notes`` tag stay locked together (single source of
        truth). A lingering inline literal would drift on a rename.
        """
        source = _app_source()
        # Allow the literals inside the comment block (docstring) but
        # forbid them inside a Python expression (e.g. a ternary).
        # Easy heuristic: assert there is no ternary of the shape
        # ``"[sub-quote-llm]" if ... else "[sub-quote]"``.
        ternary = re.search(
            r'"\[sub-quote-llm\]"\s+if[^\n]*else\s+"\[sub-quote\]"',
            source,
        )
        assert ternary is None, (
            "Inline string-literal ternary for sub-quote tags found. "
            "Use SOURCE_TAG_SUBQUOTE_LLM / SOURCE_TAG_SUBQUOTE_TABULAR "
            "constants instead."
        )


# ---------------------------------------------------------------------------
# Backend round-trip — apply each path and verify CostLine.notes content
# ---------------------------------------------------------------------------


class TestApplyRoundTrip:
    def test_tabular_subquote_apply_stamps_sub_quote_tag_at_position_0(
        self,
    ) -> None:
        """``apply_subquote_plan(llm=False)`` → ``CostLine.notes`` starts ``[sub-quote] ``."""
        estimate = _estimate([_line(description="Lavatory P-1")])
        rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_subquote_plan(estimate, plan, llm=False)
        notes = new_est.line_items[0].notes or ""
        assert notes.startswith("[sub-quote] "), (
            f"Expected CostLine.notes to start with '[sub-quote] '; "
            f"got: {notes!r}"
        )
        # Defensive: the LLM tag must NOT appear when llm=False.
        assert "[sub-quote-llm]" not in notes

    def test_llm_subquote_apply_stamps_sub_quote_llm_tag_at_position_0(
        self,
    ) -> None:
        """``apply_subquote_plan(llm=True)`` → ``CostLine.notes`` starts ``[sub-quote-llm] ``."""
        estimate = _estimate([_line(description="Lavatory P-1")])
        rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_subquote_plan(estimate, plan, llm=True)
        notes = new_est.line_items[0].notes or ""
        assert notes.startswith("[sub-quote-llm] "), (
            f"Expected CostLine.notes to start with '[sub-quote-llm] '; "
            f"got: {notes!r}"
        )

    def test_vendor_csv_apply_stamps_vendor_csv_tag_at_position_0(
        self,
    ) -> None:
        """``apply_batch_plan(source_tag=SOURCE_TAG_VENDOR_CSV)`` → ``[vendor-csv] `` first."""
        estimate = _estimate([_line(description="Conduit 3/4")])
        rows = [_row(description="Conduit 3/4", unit_cost=4.25)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_batch_plan(
            estimate, plan, source_tag=SOURCE_TAG_VENDOR_CSV
        )
        notes = new_est.line_items[0].notes or ""
        assert notes.startswith("[vendor-csv] "), (
            f"Expected CostLine.notes to start with '[vendor-csv] '; "
            f"got: {notes!r}"
        )
        # Defensive: the legacy [batch] tag must NOT appear when an
        # explicit source_tag is provided.
        assert "[batch]" not in notes

    def test_round_trip_position_0_across_all_three_paths(self) -> None:
        """Round-trip on all three paths in one assertion block — pin the contract."""
        for tag, applier in (
            ("[sub-quote] ", lambda e, p: apply_subquote_plan(e, p, llm=False)),
            ("[sub-quote-llm] ", lambda e, p: apply_subquote_plan(e, p, llm=True)),
            (
                "[vendor-csv] ",
                lambda e, p: apply_batch_plan(
                    e, p, source_tag=SOURCE_TAG_VENDOR_CSV
                ),
            ),
        ):
            estimate = _estimate([_line(description="Lavatory P-1")])
            rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
            plan = match_cost_lines(rows, list(estimate.line_items))
            new_est, _ = applier(estimate, plan)
            notes = new_est.line_items[0].notes or ""
            assert notes.startswith(tag), (
                f"Expected notes to start with {tag!r} for the "
                f"current apply path; got: {notes!r}"
            )


# ---------------------------------------------------------------------------
# Override-history vs CostLine.notes — tag appears in each field exactly once
# ---------------------------------------------------------------------------


class TestOverrideHistoryTagConsistency:
    def test_history_operator_note_and_costline_notes_carry_same_tag(
        self,
    ) -> None:
        """The session-state log and the canonical notes cell agree on the tag.

        Both surfaces must start with the same canonical tag — that's
        the audit-trail symmetry T6.4.c.1 was designed for. The two
        fields don't carry byte-identical strings (the notes cell
        adds the ``operator override:`` sentinel + optional
        ``| previous: …`` suffix) but they share the leading tag.
        """
        estimate = _estimate([_line(description="Lavatory P-1")])
        rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_subquote_plan(estimate, plan, llm=True)

        history_note = format_batch_operator_note(
            rows[0], source_tag=SOURCE_TAG_SUBQUOTE_LLM
        )
        costline_notes = new_est.line_items[0].notes or ""
        assert history_note.startswith("[sub-quote-llm] ")
        assert costline_notes.startswith("[sub-quote-llm] ")

    def test_tag_appears_exactly_once_in_costline_notes(self) -> None:
        """No double-stamping inside ``CostLine.notes`` itself.

        The brief's concern was that, post-T6.4.c, both surfaces stamp
        the tag — but each surface must contain it exactly once. A
        regression that runs the rewrite helper twice (or adds a
        second leading tag) would double the count and the auto-sized
        Excel column would push real content out of view.
        """
        estimate = _estimate([_line(description="Lavatory P-1")])
        rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_subquote_plan(estimate, plan, llm=False)
        notes = new_est.line_items[0].notes or ""
        # The tag-with-trailing-space appears exactly once at the
        # start of the cell. ``str.count`` is the right counter here
        # (literal substring, no overlapping matches in this format).
        assert notes.count("[sub-quote] ") == 1

    def test_reapply_same_plan_preserves_single_tag(self) -> None:
        """Idempotency contract from T6.4.c — re-apply does NOT duplicate."""
        estimate = _estimate([_line(description="Lavatory P-1")])
        rows = [_row(description="Lavatory P-1", unit_cost=450.0)]
        plan = match_cost_lines(rows, list(estimate.line_items))
        once, _ = apply_subquote_plan(estimate, plan, llm=False)
        twice, _ = apply_subquote_plan(once, plan, llm=False)
        notes = twice.line_items[0].notes or ""
        assert notes.count("[sub-quote] ") == 1, (
            f"Re-apply duplicated the source tag; notes: {notes!r}"
        )


# ---------------------------------------------------------------------------
# Edge cases
# ---------------------------------------------------------------------------


class TestEdgeCases:
    def test_empty_plan_does_not_mutate_notes(self) -> None:
        """Empty sub-quote plan → ``CostLine.notes`` unchanged.

        Defensive guard for the apply path: when nothing matched,
        nothing should change on any line. Specifically, the canonical
        tag must NOT appear on any line that wasn't touched.
        """
        estimate = _estimate([_line(description="Lavatory P-1", notes="LL@$45/hr")])
        plan = match_cost_lines([], list(estimate.line_items))
        new_est, summary = apply_subquote_plan(estimate, plan, llm=False)
        for old, new in zip(
            estimate.line_items, new_est.line_items, strict=True
        ):
            assert old.notes == new.notes, (
                f"Empty plan mutated notes: {old.notes!r} → {new.notes!r}"
            )
        # An empty plan produces a header-only summary with no
        # per-row "APPLIED" / "SKIPPED" lines. Pinning the absence of
        # per-row activity is the right contract here; the header
        # line ("Batch override summary: 0 applied, ...") is incidental.
        per_row_activity = [
            line for line in summary
            if line.startswith("Row") and (
                "APPLIED" in line or "SKIPPED" in line
            )
        ]
        assert per_row_activity == []

    def test_mixed_source_within_single_apply_uses_caller_tag(self) -> None:
        """A single apply call uses ONE ``source_tag`` for every applied row.

        ``apply_subquote_plan`` doesn't accept a per-row tag; the
        whole plan rides one tag determined by the ``llm`` flag.
        Defensive pin that no future refactor sneaks in a per-row
        override and produces a mixed-tag notes field.
        """
        estimate = _estimate([
            _line(description="Lavatory P-1", unit_cost=500.0),
            _line(description="Water closet WC-1", unit_cost=600.0),
        ])
        rows = [
            _row(row_index=2, description="Lavatory P-1", unit_cost=450.0),
            _row(
                row_index=3,
                description="Water closet WC-1",
                unit_cost=525.0,
            ),
        ]
        plan = match_cost_lines(rows, list(estimate.line_items))
        new_est, _ = apply_subquote_plan(estimate, plan, llm=True)
        for line in new_est.line_items:
            notes = line.notes or ""
            assert notes.startswith("[sub-quote-llm] "), (
                f"Line {line.description!r} carried unexpected tag; "
                f"notes: {notes!r}"
            )
            # The OTHER sub-quote tag must NOT appear on any line.
            assert "[sub-quote]" not in notes.replace(
                "[sub-quote-llm]", "", 1
            )


# ---------------------------------------------------------------------------
# Import smoke
# ---------------------------------------------------------------------------


def test_app_module_imports_cleanly() -> None:
    """``import app`` must succeed post-wire-up.

    Catches the most common breakage mode: a missing import or a
    syntax error introduced by the call-site refactor. The other
    tests already exercised the imports; this one pins that running
    ``python -c "import app"`` succeeds at the module level.
    """
    import importlib

    importlib.reload(app)
    assert hasattr(app, "apply_subquote_plan")
    assert hasattr(app, "apply_batch_plan")


def test_app_py_file_is_readable_and_nonempty() -> None:
    """Sanity check — the source we asserted against above isn't empty.

    Belt-and-braces for the source-level pins: if ``inspect.getsource``
    ever returns an empty string under an unusual loader, the
    ``re.search`` calls would silently pass on the wrong assumption.
    """
    repo_root = Path(__file__).resolve().parent.parent
    text = (repo_root / "app.py").read_text(encoding="utf-8")
    assert len(text) > 1000, "app.py source unexpectedly small"
    assert "apply_subquote_plan" in text
    assert "SOURCE_TAG_VENDOR_CSV" in text
