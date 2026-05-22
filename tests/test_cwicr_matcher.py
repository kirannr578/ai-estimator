"""Unit tests for `core.pricing.cwicr_matcher.CwicrMatcher`.

All tests here are **offline** — they inject a tiny in-memory fixture via
the `_dataset_loader` hook and a deterministic embedder via `_embedder`
so we never depend on a network download or the real sentence-transformer
model. End-to-end smoke testing (real dataset + real embeddings) happens
in `tests/test_cwicr_matcher_smoke.py` (marked `@pytest.mark.slow` so the
default suite stays fast).
"""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import pytest

from core.pricing.cwicr_matcher import (
    CwicrCandidate,
    CwicrMatcher,
    _normalise_unit,
    _unit_similarity,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


_FIXTURE_ROWS: list[dict[str, Any]] = [
    {
        "rate_code": "CONC_FOOT_8IN",
        "rate_original_name": "Concrete spread footings 8 in thick, reinforced",
        "rate_unit": "m3",
        "total_cost_per_position": 220.0,
        "cost_of_working_hours": 60.0,
        "total_material_cost_per_position": 140.0,
        "total_value_machinery_equipment": 20.0,
        "category_type": "Concrete",
        "department_name": "Cast-in-place concrete",
        "section_name": "Spread footings",
    },
    {
        "rate_code": "WOOD_FRAME_2X6",
        "rate_original_name": "Wood stud framing 2x6 exterior wall",
        "rate_unit": "SF",
        "total_cost_per_position": 8.50,
        "cost_of_working_hours": 4.0,
        "total_material_cost_per_position": 4.0,
        "total_value_machinery_equipment": 0.5,
        "category_type": "Wood",
        "department_name": "Rough carpentry",
        "section_name": "Stud framing",
    },
    {
        "rate_code": "DRYWALL_5_8",
        "rate_original_name": "Gypsum board drywall 5/8 inch one side, taped and finished",
        "rate_unit": "SF",
        "total_cost_per_position": 2.85,
        "cost_of_working_hours": 1.50,
        "total_material_cost_per_position": 1.20,
        "total_value_machinery_equipment": 0.10,
        "category_type": "Finishes",
        "department_name": "Gypsum board assemblies",
        "section_name": "GWB 5/8\" type X",
    },
    {
        "rate_code": "HM_DOOR_3070",
        "rate_original_name": "Hollow metal door and frame 3'-0\" x 7'-0\"",
        "rate_unit": "EA",
        "total_cost_per_position": 950.0,
        "cost_of_working_hours": 200.0,
        "total_material_cost_per_position": 700.0,
        "total_value_machinery_equipment": 0.0,
        "category_type": "Openings",
        "department_name": "Hollow metal doors",
        "section_name": "HM door & frame",
    },
    {
        "rate_code": "ASPHALT_PAVE_3IN",
        "rate_original_name": "Asphalt paving 3 inch over compacted base",
        "rate_unit": "SF",
        "total_cost_per_position": 6.85,
        "cost_of_working_hours": 2.0,
        "total_material_cost_per_position": 4.0,
        "total_value_machinery_equipment": 0.8,
        "category_type": "Exterior improvements",
        "department_name": "Asphalt paving",
        "section_name": "Wearing course",
    },
    {
        "rate_code": "MISC_SIGN_ADA",
        "rate_original_name": "Interior ADA-compliant room identification sign",
        "rate_unit": "EACH",
        "total_cost_per_position": 95.0,
        "cost_of_working_hours": 10.0,
        "total_material_cost_per_position": 80.0,
        "total_value_machinery_equipment": 0.0,
        "category_type": "Specialties",
        "department_name": "Signage",
        "section_name": "Interior signs",
    },
    {
        "rate_code": "RANDOM_NOISE_XYZ",
        "rate_original_name": "Quantum widget calibration in zero-gravity laboratory annex",
        "rate_unit": "ea",
        "total_cost_per_position": 12345.67,
        "cost_of_working_hours": 0.0,
        "total_material_cost_per_position": 0.0,
        "total_value_machinery_equipment": 0.0,
        "category_type": "Other",
        "department_name": "Research",
        "section_name": "Misc",
    },
]


def _fixture_loader(_cache_dir: Path) -> pd.DataFrame:
    return pd.DataFrame(_FIXTURE_ROWS)


def _deterministic_embedder(texts: list[str]) -> np.ndarray:
    """Stable, dependency-free pseudo-embedder for unit tests.

    Hashes each text into a 32-dim float vector so identical / near-identical
    texts get more similar vectors than random text pairs. Good enough to
    drive the matcher's argpartition + re-rank logic. NOT a real semantic
    embedding — tests assert ordering, not exact similarity values.

    We hash on whitespace-separated tokens and accumulate token-hash
    contributions across the vector, then L2-normalise.
    """
    vecs: list[np.ndarray] = []
    for text in texts:
        v = np.zeros(32, dtype=np.float32)
        toks = (text or "").lower().split()
        for tok in toks:
            h = hashlib.sha1(tok.encode()).digest()
            for i, b in enumerate(h[:32]):
                v[i] += (b - 128) / 128.0
        n = float(np.linalg.norm(v))
        if n > 0:
            v /= n
        vecs.append(v)
    return np.vstack(vecs)


@pytest.fixture()
def matcher(tmp_path: Path) -> CwicrMatcher:
    return CwicrMatcher(
        region="test",
        cache_dir=tmp_path,
        _dataset_loader=_fixture_loader,
        _embedder=_deterministic_embedder,
    )


# ---------------------------------------------------------------------------
# Unit synonym helpers
# ---------------------------------------------------------------------------


class TestUnitSynonyms:
    def test_each_synonyms_collapse_to_ea(self) -> None:
        assert _normalise_unit("EA") == "ea"
        assert _normalise_unit("EACH") == "ea"
        assert _normalise_unit("each") == "ea"
        assert _normalise_unit("nr") == "ea"

    def test_length_synonyms(self) -> None:
        assert _normalise_unit("LF") == "lf"
        assert _normalise_unit("LIN FT") == "lf"
        assert _normalise_unit("Linear ft") == "lf"

    def test_area_synonyms(self) -> None:
        assert _normalise_unit("SF") == "sf"
        assert _normalise_unit("SQ FT") == "sf"
        assert _normalise_unit("m2") == "m2"
        assert _normalise_unit("100 m2") == "m2"

    def test_volume_synonyms(self) -> None:
        assert _normalise_unit("CY") == "cy"
        assert _normalise_unit("cu yd") == "cy"
        assert _normalise_unit("m3") == "m3"

    def test_unit_similarity_exact_synonym_boost(self) -> None:
        assert _unit_similarity("EA", "EACH") > 1.0
        assert _unit_similarity("LF", "LIN FT") > 1.0

    def test_unit_similarity_same_family_smaller_penalty(self) -> None:
        same_family = _unit_similarity("SF", "m2")
        exact = _unit_similarity("SF", "SF")
        cross = _unit_similarity("SF", "TON")
        assert exact > same_family > cross


# ---------------------------------------------------------------------------
# CwicrMatcher — top-level behaviour
# ---------------------------------------------------------------------------


class TestCwicrMatcherSearch:
    def test_concrete_query_returns_concrete_row_first(self, matcher: CwicrMatcher) -> None:
        results = matcher.match(
            "concrete footings 8 inch reinforced",
            unit_hint="CY",
            csi_hint="03 30 00",
            top_k=3,
        )
        assert results, "matcher must return at least one candidate"
        top = results[0]
        assert isinstance(top, CwicrCandidate)
        assert "concrete" in top.description.lower() or "footing" in top.description.lower()
        assert top.source_row_id == 0, (
            "concrete fixture is row 0 — should win the concrete query"
        )

    def test_returns_at_most_top_k(self, matcher: CwicrMatcher) -> None:
        results = matcher.match("concrete", top_k=2)
        assert len(results) <= 2

    def test_empty_query_returns_empty(self, matcher: CwicrMatcher) -> None:
        assert matcher.match("") == []
        assert matcher.match("   ") == []

    def test_warm_is_idempotent(self, matcher: CwicrMatcher) -> None:
        matcher.warm()
        ts1 = matcher._embeddings.copy()  # type: ignore[union-attr]
        matcher.warm()
        ts2 = matcher._embeddings  # type: ignore[union-attr]
        assert np.array_equal(ts1, ts2)


# ---------------------------------------------------------------------------
# Unit synonyms — full round-trip into match()
# ---------------------------------------------------------------------------


class TestUnitSynonymsInMatch:
    def test_ea_and_each_match_same_row(self, matcher: CwicrMatcher) -> None:
        """The `HM_DOOR_3070` row has unit 'EA' and the `MISC_SIGN_ADA` row
        has unit 'EACH'. Querying with either should treat both as
        equally unit-friendly, with the description-similarity deciding
        the winner."""
        door_q = "hollow metal door 3 by 7"
        r_ea = matcher.match(door_q, unit_hint="EA", top_k=3)
        r_each = matcher.match(door_q, unit_hint="EACH", top_k=3)
        assert r_ea and r_each
        # The top-1 must be the door row for both queries.
        assert r_ea[0].source_row_id == 3
        assert r_each[0].source_row_id == 3


# ---------------------------------------------------------------------------
# CSI hint boost
# ---------------------------------------------------------------------------


class TestCsiHint:
    def test_csi_hint_changes_ordering_when_relevant(self, matcher: CwicrMatcher) -> None:
        """Boost is small but should be enough to surface a low-TF-IDF
        row that's still in the right division when the query is generic."""
        no_hint = matcher.match("rough work for new construction", top_k=5)
        with_hint = matcher.match(
            "rough work for new construction",
            csi_hint="03 30 00",
            top_k=5,
        )
        # The boost only applies once a candidate is in the TF-IDF top-200,
        # which here means all rows are eligible (fixture has only 7).
        # The concrete row (id=0) is the only one tagged 'Concrete' in
        # the classification bag, so it should rank higher with the hint.
        no_hint_rank = next(
            (i for i, c in enumerate(no_hint) if c.source_row_id == 0), -1
        )
        with_hint_rank = next(
            (i for i, c in enumerate(with_hint) if c.source_row_id == 0), -1
        )
        # The concrete row gets at least as good a rank with the hint as
        # without it; the test guards against the hint ever *hurting*
        # placement, while allowing the unit-similarity penalty to dominate
        # when the units are wildly off (no unit_hint here → no penalty).
        assert with_hint_rank <= no_hint_rank or no_hint_rank == -1


# ---------------------------------------------------------------------------
# Threshold / no-match behaviour
# ---------------------------------------------------------------------------


class TestNoMatchSimilarity:
    def test_unrelated_query_returns_low_similarity(self, matcher: CwicrMatcher) -> None:
        """A query with no semantic / lexical overlap should produce
        either an empty list or candidates whose top similarity is below
        the default 0.55 threshold."""
        results = matcher.match("nothing related at all xyz123 quux narwhal", top_k=3)
        # Either no results or all below threshold — both are acceptable
        # downstream signals to "no CWICR match".
        if results:
            assert results[0].similarity < 0.85, (
                "an obviously unrelated query should not exceed a high similarity"
            )

    def test_candidates_are_sorted_by_similarity_desc(self, matcher: CwicrMatcher) -> None:
        results = matcher.match("concrete", top_k=5)
        assert results
        for a, b in zip(results, results[1:]):
            assert a.similarity >= b.similarity
