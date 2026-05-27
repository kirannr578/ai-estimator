"""Tests for Phase B (TX prevailing wage, GSA Schedule) + Phase C stubs.

Phase B parsers are exercised against synthetic text / CSV input — no
network, no real fixture PDF (those will be added in Phase B-full once the
TWC PDF auto-fetch ships and we have a permissively-licensed sample on hand).

Phase C tests confirm each stub adapter is importable, has the expected
fields, and returns an empty list (sentinel that the stub is wired but
intentionally non-functional).
"""

from __future__ import annotations

import pytest

from core.pricing.sources.construction_indexes import (
    AGCInflationAlertSource,
    ENRConstructionCostIndexSource,
    NAHBCostOfConstructingAHomeSource,
    TurnerBuildingCostIndexSource,
)
from core.pricing.sources.gsa_schedule import (
    GSAScheduleSource,
    _infer_csi_division,
    _parse_unit_from_description,
    parse_catalog_csv,
)
from core.pricing.sources.hd_pro_catalog import HDProCatalogSource
from core.pricing.sources.tx_prevailing_wage import (
    TXPrevailingWageSource,
    parse_wage_table_text,
)
from core.pricing.sources.tx_smartbuy_awards import TXSmartBuyAwardsSource


# --- Phase B: TX prevailing wage ---------------------------------------

SAMPLE_TWC_TEXT = """
TEXAS WORKFORCE COMMISSION
Tom Green County Prevailing Wage Rates — 2026

Classification                       Base    Fringe   Total
-----------------------------------------------------------
CARPENTER                            28.41   4.25     32.66
ELECTRICIAN, JOURNEYMAN              35.10   6.15     41.25
PLUMBER                              33.21   5.50     38.71
LABORER (Common)                     19.27   2.50     21.77
ROOFER                               24.50   3.10     27.60

Notes: Effective Jan 1, 2026. Reference only.
"""


def test_parse_wage_table_extracts_rows() -> None:
    snaps = parse_wage_table_text(SAMPLE_TWC_TEXT, county="Tom Green", year=2026)
    assert len(snaps) == 5
    by_trade = {s.label.split(" — ")[0]: s for s in snaps}
    assert "CARPENTER" in by_trade
    assert by_trade["CARPENTER"].value == pytest.approx(32.66)
    assert by_trade["CARPENTER"].unit == "USD/hr"
    assert by_trade["CARPENTER"].region == "TX-Tom Green"
    assert by_trade["CARPENTER"].soc_code == "47-2031"
    # Journeyman electrician still maps via partial keyword match.
    elec = next(s for s in snaps if "ELECTRICIAN" in s.label)
    assert elec.value == pytest.approx(41.25)
    assert elec.soc_code == "47-2111"
    # All snapshots carry the period and license.
    assert all(s.period == "2026" for s in snaps)
    assert all("Texas" in s.license for s in snaps)


def test_parse_wage_table_ignores_noise() -> None:
    snaps = parse_wage_table_text(
        "Something random\nNo numbers here\nAnother line\n",
        county="Bexar", year=2025,
    )
    assert snaps == []


def test_tx_prevailing_wage_source_fetch_is_noop_stub() -> None:
    src = TXPrevailingWageSource()
    src.close()
    assert src.default_series() == []
    assert src.fetch(["anything"]) == []


# --- Phase B: GSA Schedule ----------------------------------------------

SAMPLE_GSA_CSV = (
    "SIN,Manufacturer Part Number,Description,Price\n"
    "238120,W12X22-20FT,Steel beam W12x22 20-ft length,1850.50\n"
    "238120,W14X30-20FT,Steel beam W14x30 20-ft length,2425.00\n"
    "238330,ACT-2X4-FISSURED,Acoustic ceiling tile 2x4 SF,$5.45\n"
    "238330,ACT-2X4-NONFISSURED,,$0\n"   # invalid: no item/desc, 0 price
    "238220,EMT-1/2-10FT,EMT conduit 1/2 LF per 10-ft length,42.10\n"
)


def test_parse_catalog_csv_basic() -> None:
    snaps = parse_catalog_csv(SAMPLE_GSA_CSV, schedule_code="56V")
    # 5 input rows, 1 has price <= 0 and is dropped -> 4 snapshots.
    assert len(snaps) == 4
    beams = [s for s in snaps if "Steel beam" in s.label]
    assert len(beams) == 2
    assert beams[0].value == pytest.approx(1850.50)
    assert beams[0].csi_division == "05"
    assert beams[0].unit == "USD/EA"

    ceiling = next(s for s in snaps if "Acoustic" in s.label)
    assert ceiling.value == pytest.approx(5.45)
    assert ceiling.unit == "USD/SF"
    assert ceiling.csi_division == "09"

    conduit = next(s for s in snaps if "EMT" in s.label)
    assert conduit.unit == "USD/LF"
    assert conduit.csi_division == "23"


def test_infer_csi_division_falls_back_to_none() -> None:
    assert _infer_csi_division("999999") is None
    assert _infer_csi_division("") is None
    assert _infer_csi_division("238120") == "05"
    assert _infer_csi_division("332") == "05"


def test_parse_unit_from_description_heuristics() -> None:
    assert _parse_unit_from_description("Wire per LF") == "USD/LF"
    assert _parse_unit_from_description("Tile per SF") == "USD/SF"
    assert _parse_unit_from_description("Concrete per CY") == "USD/CY"
    assert _parse_unit_from_description("Sealant per GAL") == "USD/gallon"
    assert _parse_unit_from_description("Doors") == "USD/EA"


def test_gsa_schedule_source_fetch_is_noop_stub() -> None:
    src = GSAScheduleSource()
    src.close()
    assert src.default_series() == []
    assert src.fetch(["anything"]) == []
    assert "56V" in src.SUPPORTED_SCHEDULES


# --- Phase C stubs ------------------------------------------------------

@pytest.mark.parametrize("cls", [
    TXSmartBuyAwardsSource,
    HDProCatalogSource,
    ENRConstructionCostIndexSource,
    AGCInflationAlertSource,
    TurnerBuildingCostIndexSource,
    NAHBCostOfConstructingAHomeSource,
])
def test_phase_c_stub_is_importable_and_returns_empty(cls) -> None:
    src = cls()
    try:
        assert src.name
        assert src.license_str
        assert src.homepage_url.startswith("http")
        assert src.default_series() == []
        assert src.fetch(["x"]) == []
    finally:
        src.close()


@pytest.mark.integration
@pytest.mark.skip(reason="[Phase C — not yet implemented] requires live HTTP")
def test_tx_smartbuy_live() -> None:
    """Skipped integration test — kept as a placeholder for when Phase C ships."""
    src = TXSmartBuyAwardsSource()
    try:
        snaps = src.fetch(["any-rfp-number"])
        assert isinstance(snaps, list)
    finally:
        src.close()
