"""QA-2 subsystem 5 — confidence-aware pricing.

Worker YY-2 / Pair 25 / subsystem 5 of the QA decomposition. Covers:

* CWICR / seed-DB tier assignment (EXACT_MATCH / CATEGORY_MATCH / …)
* qty × price → combined_confidence multiplication and band assignment
* Unit-mismatch suppression (LF×SF guardrail from calibration v2 #4)
* Region multiplier baked into unit_cost
* Manual override on a MISSING-tier line → MANUAL_OVERRIDE tier,
  snapshot captured, combined_confidence rebanded
* T6.4.d snapshot store FIFO cap at MAX_OVERRIDE_SNAPSHOTS (10)
* CWICR similarity at the 0.75 / 0.92 boundaries — pinned

Every PASS scenario asserts standard behaviour. Surfaced bugs are
filed via ``pytest.mark.xfail(reason="QA-2 finding #N: …")`` per the
QA-2 brief — fixes are a separate slice. Cost DB stubbing is in-memory
(small JSON tempfile) per the brief. No CWICR network use — every CWICR
test injects a duck-typed ``FakeMatcher`` whose ``.match()`` returns a
canned :class:`CwicrCandidate`.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

import pytest

from core.estimator import (
    CostDatabase,
    apply_manual_override,
    price_takeoff,
    revert_last_override_in_estimate,
)
from core.pricing.cwicr_matcher import CwicrCandidate
from core.schemas import (
    COST_BAND_AUTO_THRESHOLD,
    COST_TIER_CATEGORY_THRESHOLD,
    COST_TIER_EXACT_THRESHOLD,
    COST_TIER_SEED_DB_PRICE_CONFIDENCE,
    MAX_OVERRIDE_SNAPSHOTS,
    CostBand,
    CostCategory,
    CostLine,
    CostSourceTier,
    Estimate,
    SiteInfo,
    TakeoffItem,
    band_for_confidence,
    price_confidence_from_similarity,
)
from core.takeoff import ProjectInfo, ProjectModel, ScopeMatrix


# ---------------------------------------------------------------------------
# Fixtures + helpers
# ---------------------------------------------------------------------------


def _project(takeoffs: list[TakeoffItem]) -> ProjectModel:
    return ProjectModel(
        rooms=[],
        doors=[],
        windows=[],
        structural=[],
        mep=[],
        spec_sections=[],
        site=SiteInfo(),
        takeoffs=takeoffs,
        sheet_summaries={},
        warnings=[],
        bid_packages=[],
        project_info=ProjectInfo(name="QA-2 Pricing"),
        scope_matrix=ScopeMatrix(
            packages=[], by_division={}, all_alternates=[], coverage_warnings=[]
        ),
        aggregated_inclusions=[],
        aggregated_exclusions=[],
        alternates=[],
    )


def _write_cost_db(tmp_path: Path, entries: dict) -> Path:
    """Persist a tiny in-memory cost-DB to disk so :class:`CostDatabase`
    can load it. Bundled seed DB is ~1.5MB; this fixture is < 1KB."""
    out = tmp_path / "stub_cost_db.json"
    out.write_text(json.dumps({"_meta": {"source": "qa-2 stub"}, **entries}))
    return out


@dataclass
class _FakeMatcher:
    """Duck-typed CwicrMatcher — returns one canned candidate per call.

    Mirrors :class:`core.pricing.cwicr_matcher.CwicrMatcher`'s ``.match()``
    surface (the only attribute :func:`price_takeoff` reads). Returns
    ``[]`` when ``candidate is None`` so tests can exercise the "no
    CWICR hit, fall through to seed DB" path.
    """

    candidate: CwicrCandidate | None

    def match(
        self,
        description: str,
        unit_hint: str | None = None,
        csi_hint: str | None = None,
        top_k: int = 1,
    ) -> list[CwicrCandidate]:
        return [self.candidate] if self.candidate is not None else []


def _candidate(
    *,
    similarity: float,
    unit: str = "SF",
    unit_price: float = 10.0,
    code: str = "CW-0001",
    description: str = "Interior latex paint",
) -> CwicrCandidate:
    return CwicrCandidate(
        code=code,
        description=description,
        unit=unit,
        unit_price=unit_price,
        labor_cost=4.0,
        material_cost=4.0,
        equipment_cost=2.0,
        region="usa_usd",
        year=2025,
        similarity=similarity,
        source_row_id=42,
    )


# ---------------------------------------------------------------------------
# Positive scenarios
# ---------------------------------------------------------------------------


class TestQAPricingPositive:
    """Two positive scenarios — happy paths through the headline pricing API."""

    def test_qa_pricing_p1_seed_db_exact_match_tier(
        self, tmp_path: Path
    ) -> None:
        """POS-1: a seed-DB hit produces tier=EXACT_MATCH at the canonical
        ``COST_TIER_SEED_DB_PRICE_CONFIDENCE`` (0.95) discount, with
        region_multiplier baked into unit_cost."""
        db_path = _write_cost_db(
            tmp_path,
            {
                "09 91 23": {
                    "unit": "SF",
                    "unit_cost": 4.00,
                    "waste_factor": 1.10,
                    "cost_category": "subcontractor",
                    "keywords": ["paint", "latex"],
                }
            },
        )
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="Interior latex paint, walls",
                    quantity=100.0,
                    unit="SF",
                    confidence=1.0,
                )
            ]
        )
        est = price_takeoff(
            project,
            project_name="QA-2 P1",
            region_multiplier=1.10,
            cost_db=CostDatabase(db_path),
            use_cwicr=False,
        )
        assert len(est.line_items) == 1
        line = est.line_items[0]
        assert line.cost_source_tier == CostSourceTier.EXACT_MATCH
        assert line.price_confidence == COST_TIER_SEED_DB_PRICE_CONFIDENCE
        # region_multiplier 1.10 baked into unit_cost (4.00 * 1.10 = 4.40)
        assert line.unit_cost == pytest.approx(4.40, abs=0.01)
        # quantity * waste_factor = 100 * 1.10 = 110, total = 110 * 4.40
        assert line.quantity == pytest.approx(110.0, abs=0.01)
        assert line.total_cost == pytest.approx(484.00, abs=0.01)
        # combined = 1.0 (qty) * 0.95 (price) = 0.95 → AUTO_APPROVE
        assert line.cost_band == CostBand.AUTO_APPROVE
        assert line.suppressed is False

    def test_qa_pricing_p2_manual_override_on_missing_tier(
        self, tmp_path: Path
    ) -> None:
        """POS-2: a MISSING-tier line (no-match $0 placeholder) becomes
        MANUAL_OVERRIDE after :func:`apply_manual_override`. The snapshot
        store captures the prior MISSING state for revert."""
        # Seed DB has nothing for this division → no-match → MISSING tier.
        db_path = _write_cost_db(tmp_path, {})
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="Mystery row no DB hit",
                    quantity=50.0,
                    unit="SF",
                    confidence=0.9,
                )
            ]
        )
        est = price_takeoff(
            project,
            project_name="QA-2 P2",
            cost_db=CostDatabase(db_path),
            use_cwicr=False,
        )
        assert est.line_items[0].cost_source_tier == CostSourceTier.MISSING
        assert est.line_items[0].total_cost == 0.0
        assert est.line_items[0].price_confidence == 0.0
        # Operator vouches → manual override.
        new_est = apply_manual_override(
            est, line_id=0, new_unit_cost=4.50, operator_note="vendor quote"
        )
        line = new_est.line_items[0]
        assert line.cost_source_tier == CostSourceTier.MANUAL_OVERRIDE
        assert line.price_confidence == 1.0
        assert line.unit_cost == 4.50
        assert line.total_cost == pytest.approx(225.0, abs=0.01)  # 50 * 4.50
        assert line.suppressed is False
        assert line.notes is not None and line.notes.startswith("[manual-override] ")
        # Snapshot store recorded one entry — the prior MISSING state.
        assert len(line.override_snapshots) == 1
        snap = line.override_snapshots[0]
        assert snap.cost_source_tier == CostSourceTier.MISSING
        assert snap.price_confidence == 0.0
        # Revert restores the line to MISSING, $0.
        reverted, popped = revert_last_override_in_estimate(new_est, 0)
        assert popped is not None
        rev_line = reverted.line_items[0]
        assert rev_line.cost_source_tier == CostSourceTier.MISSING
        assert rev_line.unit_cost == 0.0
        assert rev_line.override_snapshots == []


# ---------------------------------------------------------------------------
# Negative scenarios
# ---------------------------------------------------------------------------


class TestQAPricingNegative:
    """Two negative scenarios — invalid inputs / catastrophic states."""

    def test_qa_pricing_n1_unit_mismatch_lf_vs_sf_suppressed(
        self, tmp_path: Path
    ) -> None:
        """NEG-1: a takeoff in LF priced against a DB row in SF must
        suppress (calibration v2 finding #4 — the LF×TON $34,608 phantom
        line). ``total_cost`` zeroed, tier=MISSING, suppressed=True,
        cost_band=HAND_TAKEOFF."""
        db_path = _write_cost_db(
            tmp_path,
            {
                "09 91 23": {
                    "unit": "SF",  # DB is SF
                    "unit_cost": 4.00,
                    "waste_factor": 1.0,
                    "cost_category": "subcontractor",
                    "keywords": ["paint"],
                }
            },
        )
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="Interior paint",
                    quantity=100.0,
                    unit="LF",  # takeoff is LF — mismatch
                    confidence=0.9,
                )
            ]
        )
        est = price_takeoff(
            project,
            project_name="QA-2 N1",
            cost_db=CostDatabase(db_path),
            use_cwicr=False,
        )
        line = est.line_items[0]
        assert line.suppressed is True
        assert line.total_cost == 0.0
        assert line.unit_cost == 0.0
        assert line.cost_source_tier == CostSourceTier.MISSING
        assert line.price_confidence == 0.0
        assert line.cost_band == CostBand.HAND_TAKEOFF
        assert line.notes is not None and "unit mismatch" in line.notes
        # Headline subtotal must NOT include the suppressed phantom line.
        assert est.subtotal == 0.0
        assert est.total_hand_takeoff == 0.0  # zeroed cost rolls to 0

    def test_qa_pricing_n2_missing_cost_db_file_raises(
        self, tmp_path: Path
    ) -> None:
        """NEG-2: when the cost-DB JSON file is missing, the estimator
        raises a clear FileNotFoundError on construction. Exposes the
        contract — the brief asks for "graceful or clear message"; raising
        FileNotFoundError on init satisfies the latter."""
        bogus = tmp_path / "no_such_file.json"
        with pytest.raises(FileNotFoundError):
            CostDatabase(bogus)
        # And the use_seed=False escape hatch sidesteps it entirely so a
        # CWICR-only run still works without a seed DB present.
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="x",
                    quantity=1.0,
                    unit="SF",
                )
            ]
        )
        est = price_takeoff(
            project,
            project_name="QA-2 N2",
            use_cwicr=False,
            use_seed=False,
        )
        # Without seed DB and CWICR, every takeoff lands as MISSING.
        assert est.line_items[0].cost_source_tier == CostSourceTier.MISSING


# ---------------------------------------------------------------------------
# Edge scenarios
# ---------------------------------------------------------------------------


class TestQAPricingEdge:
    """Three edge scenarios — boundary inputs, deterministic outcomes."""

    def test_qa_pricing_e1_combined_confidence_at_auto_band_boundary(
        self,
    ) -> None:
        """EDGE-1: combined_confidence == 0.85 (the AUTO band threshold)
        must land in AUTO_APPROVE — the boundary is inclusive, pinned by
        :func:`band_for_confidence`."""
        # Direct contract pin.
        assert band_for_confidence(0.85) == CostBand.AUTO_APPROVE
        assert (
            band_for_confidence(COST_BAND_AUTO_THRESHOLD)
            == CostBand.AUTO_APPROVE
        )
        # And via the CostLine.combined_confidence property: qty=1.0,
        # price=0.85 → combined=0.85 (not 0.8499999 due to FP).
        line = CostLine(
            csi_division="09",
            csi_section="09 91 23",
            description="paint",
            quantity=1.0,
            unit="SF",
            unit_cost=10.0,
            total_cost=10.0,
            confidence=1.0,
            price_confidence=0.85,
        )
        assert line.combined_confidence == pytest.approx(0.85, abs=1e-9)
        assert band_for_confidence(line.combined_confidence) == CostBand.AUTO_APPROVE

    def test_qa_pricing_e2_snapshot_cap_drops_oldest_fifo(
        self, tmp_path: Path
    ) -> None:
        """EDGE-2: the T6.4.d snapshot store is bounded at
        :data:`MAX_OVERRIDE_SNAPSHOTS` (10). Apply 11 distinct overrides
        on one line and the oldest snapshot must drop FIFO; the most
        recent 10 stay."""
        db_path = _write_cost_db(
            tmp_path,
            {
                "09 91 23": {
                    "unit": "SF",
                    "unit_cost": 4.00,
                    "waste_factor": 1.0,
                    "cost_category": "subcontractor",
                    "keywords": ["paint"],
                }
            },
        )
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="paint",
                    quantity=10.0,
                    unit="SF",
                )
            ]
        )
        est = price_takeoff(
            project,
            project_name="QA-2 E2",
            cost_db=CostDatabase(db_path),
            use_cwicr=False,
        )
        # Apply 11 distinct overrides (different unit_costs so each
        # mutation is genuinely a new state and the snapshot is meaningful).
        current = est
        for i in range(MAX_OVERRIDE_SNAPSHOTS + 1):
            current = apply_manual_override(
                current, line_id=0, new_unit_cost=10.0 + i, operator_note=f"override #{i}"
            )
        line = current.line_items[0]
        assert len(line.override_snapshots) == MAX_OVERRIDE_SNAPSHOTS
        # Oldest snapshot (the priced default at unit_cost=4.00) must be gone;
        # the deepest remaining snapshot should be the unit_cost=10.0 state
        # (the result of the FIRST override, which became the prior of the
        # second). The very-pre-override state at $4 was popped FIFO.
        deepest = line.override_snapshots[0]
        assert deepest.unit_cost == pytest.approx(10.0, abs=0.01)
        # Top-of-stack snapshot is the state captured BEFORE the latest
        # override — i.e. unit_cost=10+9=19.
        top = line.override_snapshots[-1]
        assert top.unit_cost == pytest.approx(19.0, abs=0.01)
        # And the live line carries the most recent override (10+10=20).
        assert line.unit_cost == pytest.approx(20.0, abs=0.01)

    def test_qa_pricing_e3_cwicr_similarity_at_thresholds(self) -> None:
        """EDGE-3: pin the CWICR-similarity → tier boundary semantics.

        * sim == 0.92 → EXACT_MATCH (boundary inclusive)
        * sim == 0.75 → CATEGORY_MATCH (boundary inclusive)
        * sim == 0.7499 → INTERPOLATED
        Plus an end-to-end :func:`price_takeoff` pin via a fake matcher
        at sim=0.92 to confirm the tier round-trips through the build.
        """
        # Direct contract pins from price_confidence_from_similarity.
        tier_92, conf_92 = price_confidence_from_similarity(
            COST_TIER_EXACT_THRESHOLD
        )
        assert tier_92 == CostSourceTier.EXACT_MATCH
        assert conf_92 == pytest.approx(0.92, abs=1e-6)

        tier_75, conf_75 = price_confidence_from_similarity(
            COST_TIER_CATEGORY_THRESHOLD
        )
        assert tier_75 == CostSourceTier.CATEGORY_MATCH
        assert conf_75 == pytest.approx(0.75 * 0.85, abs=1e-3)

        tier_just_below = price_confidence_from_similarity(0.7499)
        assert tier_just_below[0] == CostSourceTier.INTERPOLATED

        # End-to-end: a CWICR candidate at exactly the EXACT threshold
        # (sim=0.92) routes through to a CostLine with EXACT_MATCH tier
        # and price_confidence = 0.92 (the similarity itself).
        project = _project(
            [
                TakeoffItem(
                    csi_division="09",
                    csi_section="09 91 23",
                    description="Interior latex paint",
                    quantity=100.0,
                    unit="SF",
                    confidence=1.0,
                )
            ]
        )
        matcher = _FakeMatcher(_candidate(similarity=0.92, unit="SF"))
        est = price_takeoff(
            project,
            project_name="QA-2 E3",
            cwicr_matcher=matcher,
            use_cwicr=True,
            use_seed=False,
        )
        line = est.line_items[0]
        assert line.cost_source_tier == CostSourceTier.EXACT_MATCH
        assert line.price_confidence == pytest.approx(0.92, abs=1e-3)
        assert line.cost_source.startswith("cwicr:")
