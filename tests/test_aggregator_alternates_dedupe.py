"""Phase T9.0 — cross-bid-package alternates dedupe tests.

Covers :func:`core.takeoff.aggregate_alternates_across_packages` and
the inline dedupe inside :func:`core.takeoff.reconcile` — same
alternate appearing in two bid forms collapses to the most-detailed
instance; alternates from different bid packages stay separate;
alternates without a ``bid_package_id`` are grouped implicitly under
"general" via the id-only dedupe key.
"""

from __future__ import annotations

import pytest

from core.extraction.bid_form_alternates import _normalize_id_for_dedupe
from core.schemas import (
    Alternate,
    AlternateLine,
    AlternateType,
    BidPackage,
)
from core.takeoff import aggregate_alternates_across_packages


def _legacy_alt(
    number: str,
    description: str,
    add_or_deduct: str | None = None,
    amount: float | None = None,
) -> Alternate:
    return Alternate(
        number=number,
        description=description,
        add_or_deduct=add_or_deduct,
        amount=amount,
    )


def _pkg(pdf_name: str, alternates: list[Alternate]) -> BidPackage:
    return BidPackage(
        pdf_name=pdf_name,
        trade_name="Test",
        alternates=alternates,
    )


# ---------------------------------------------------------------------------
# Bridge from legacy Alternate shape
# ---------------------------------------------------------------------------


class TestLegacyAlternateBridge:
    def test_single_package_legacy_bridges_to_new_shape(self) -> None:
        pkg = _pkg(
            "bidform.pdf",
            [
                _legacy_alt("1", "Add epoxy floor", add_or_deduct="Add", amount=5000.0),
            ],
        )
        result = aggregate_alternates_across_packages([pkg])
        assert len(result) == 1
        assert result[0].alternate_type == AlternateType.ADDITIVE
        # ADD: amount positive; bridge keeps sign.
        assert result[0].cost_delta == 5000.0
        assert result[0].bid_package_id == "bidform.pdf"

    def test_legacy_deduct_flips_sign(self) -> None:
        pkg = _pkg(
            "bidform.pdf",
            [
                _legacy_alt(
                    "2", "Omit skylight", add_or_deduct="Deduct", amount=7500.0
                ),
            ],
        )
        result = aggregate_alternates_across_packages([pkg])
        assert result[0].alternate_type == AlternateType.DEDUCTIVE
        # Bridge applies sign convention: DEDUCT → negative.
        assert result[0].cost_delta == -7500.0


# ---------------------------------------------------------------------------
# Cross-package dedupe
# ---------------------------------------------------------------------------


class TestCrossPackageDedupe:
    def test_same_alternate_two_packages_dedupes_to_one(self) -> None:
        pkg_a = _pkg(
            "form_a.pdf",
            [_legacy_alt("1", "Add epoxy floor", "Add", 5000.0)],
        )
        pkg_b = _pkg(
            "form_b.pdf",
            [_legacy_alt("Alt 1", "Add epoxy floor coating", "Add", 5000.0)],
        )
        result = aggregate_alternates_across_packages([pkg_a, pkg_b])
        assert len(result) == 1, [r.alternate_id for r in result]

    def test_different_packages_different_ids_kept_separate(self) -> None:
        pkg_a = _pkg(
            "form_a.pdf",
            [_legacy_alt("1", "Add epoxy floor", "Add", 5000.0)],
        )
        pkg_b = _pkg(
            "form_b.pdf",
            [_legacy_alt("2", "Deduct skylight", "Deduct", 3000.0)],
        )
        result = aggregate_alternates_across_packages([pkg_a, pkg_b])
        assert len(result) == 2
        ids = {a.alternate_id for a in result}
        assert any("1" in i for i in ids)
        assert any("2" in i for i in ids)

    def test_dedupe_prefers_record_with_cost_delta(self) -> None:
        # Same Alternate #1, but only one has the dollar amount.
        pkg_a = _pkg(
            "form_a.pdf",
            [_legacy_alt("1", "Add epoxy floor", "Add", None)],
        )
        pkg_b = _pkg(
            "form_b.pdf",
            [_legacy_alt("1", "Add epoxy floor", "Add", 5000.0)],
        )
        result = aggregate_alternates_across_packages([pkg_a, pkg_b])
        assert len(result) == 1
        # The package_b record with the dollar amount wins.
        assert result[0].cost_delta == 5000.0


# ---------------------------------------------------------------------------
# Extra alternates parameter
# ---------------------------------------------------------------------------


class TestExtraAlternatesParameter:
    def test_extra_alternates_merge_with_package_alternates(self) -> None:
        pkg = _pkg(
            "form_a.pdf",
            [_legacy_alt("1", "Add epoxy", "Add", 5000.0)],
        )
        extra = [
            AlternateLine(
                alternate_id="Alt 2",
                description="Deduct skylight",
                alternate_type=AlternateType.DEDUCTIVE,
                cost_delta=-3000.0,
                bid_package_id="form_a.pdf",
            )
        ]
        result = aggregate_alternates_across_packages([pkg], extra)
        assert len(result) == 2

    def test_extra_dedupes_with_legacy_same_id(self) -> None:
        pkg = _pkg(
            "form_a.pdf",
            [_legacy_alt("1", "Add epoxy", "Add", None)],
        )
        extra = [
            AlternateLine(
                alternate_id="Alt 1",
                description="Add epoxy from extraction",
                alternate_type=AlternateType.ADDITIVE,
                cost_delta=5000.0,
                bid_package_id="form_a.pdf",
            )
        ]
        result = aggregate_alternates_across_packages([pkg], extra)
        # Dedupe collapses to one alternate.
        assert len(result) == 1
        # The record with cost_delta wins.
        assert result[0].cost_delta == 5000.0


# ---------------------------------------------------------------------------
# Bucketing
# ---------------------------------------------------------------------------


class TestGeneralBucket:
    def test_alternate_without_bid_package_id_is_kept(self) -> None:
        # Synthetic AlternateLine with no bid_package_id — should still
        # land in the output (grouped under "general" implicitly via
        # the id-only dedupe key).
        extra = [
            AlternateLine(
                alternate_id="Alt 99",
                description="Standalone alternate",
                cost_delta=100.0,
            )
        ]
        result = aggregate_alternates_across_packages([], extra)
        assert len(result) == 1
        assert result[0].bid_package_id is None


# ---------------------------------------------------------------------------
# Normalize-id behaviour pinned (sanity for dedupe key)
# ---------------------------------------------------------------------------


class TestNormalizeId:
    def test_collapses_alternate_variants(self) -> None:
        keys = [
            _normalize_id_for_dedupe("Alt #1"),
            _normalize_id_for_dedupe("Alternate No. 1"),
            _normalize_id_for_dedupe("Alternate 1"),
            _normalize_id_for_dedupe("Alternate #1"),
        ]
        assert len(set(keys)) == 1, keys

    def test_collapses_ve_variants(self) -> None:
        keys = [
            _normalize_id_for_dedupe("VE-3"),
            _normalize_id_for_dedupe("VE Item 3"),
            _normalize_id_for_dedupe("VE 3"),
        ]
        assert len(set(keys)) == 1, keys

    def test_ve_distinct_from_alternate(self) -> None:
        assert _normalize_id_for_dedupe("VE 1") != _normalize_id_for_dedupe("Alternate 1")
