"""Tests for the v2 cost-database expansion (~40 -> ~120 entries).

The seed `config/cost_database.json` was expanded from ~40 entries to ~120
covering five new trade families: food-service, restroom-historic,
roof-historic, security-fence-perimeter, and gymnasium multi-system. All
new entries are sourced from public-domain references (FEMA / GSA / NAHB
/ AGC / USACE / HUD) and cite the source in `notes`.

These tests act as guard-rails so future edits to `cost_database.json`
keep the file:

  * loadable as JSON, schema-conformant (unit + unit_cost on every row),
  * sized at the v2 floor (>= 120 priced entries beyond `_meta`),
  * tagged with valid `cost_category` values,
  * carrying plausible `waste_factor` values (1.00 - 1.20),
  * covering the divisions the capability library now relies on (CSI 11
    food-service equipment, CSI 32 exterior improvements, plus the
    incumbent divisions exercised by older priced takeoffs).

The test file deliberately does not pin individual unit prices — those
are expected to drift via `core/pricing/escalation.py` (BLS PPI). It
pins the *shape* and *coverage* of the database instead.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from core.estimator import CostDatabase
from core.schemas import CostCategory


COST_DB_PATH = Path(__file__).resolve().parent.parent / "config" / "cost_database.json"

# v2 floor — set so a single accidental entry deletion fails the test
# without preventing day-to-day additions. Bump alongside intentional
# expansions in future PRs.
V2_MIN_ENTRY_COUNT = 120

# Divisions the v2 expansion explicitly added scope-template coverage for.
# CSI 11 = equipment (food-service, scoreboard), CSI 32 = exterior
# (fencing), CSI 12 = furnishings (bleachers), CSI 06 = carpentry
# (historic roof + trim), CSI 22 = plumbing (ADA / historic restroom).
V2_REQUIRED_DIVISIONS = {"06", "09", "11", "12", "22", "23", "26", "32"}

VALID_COST_CATEGORIES = {c.value for c in CostCategory}

# Allow-list of units. The capability library trends toward dimensional
# units; the lump-sum unit "LS" is permitted but discouraged. The
# `_meta` row is not iterated.
ALLOWED_UNITS = {
    "LF", "SF", "CY", "CF", "EA", "TON", "GAL", "LS",
    "HR", "MO", "MBF", "DAY",
}


@pytest.fixture(scope="module")
def raw_db() -> dict:
    with COST_DB_PATH.open(encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture(scope="module")
def entries(raw_db: dict) -> dict[str, dict]:
    return {k: v for k, v in raw_db.items() if k != "_meta"}


# ---------------------------------------------------------------------------
# Shape & size
# ---------------------------------------------------------------------------


def test_database_loads_via_costdatabase():
    """The expanded DB still loads through `CostDatabase` (the production
    path). This catches an unparseable JSON edit before downstream
    pricing code blows up at runtime."""
    db = CostDatabase()
    assert len(db.entries) >= V2_MIN_ENTRY_COUNT, (
        f"CostDatabase loaded only {len(db.entries)} priced entries; v2 "
        f"floor is {V2_MIN_ENTRY_COUNT}. Did an edit accidentally drop "
        f"rows or rename a key that broke the loader's filter?"
    )


def test_entry_count_meets_v2_floor(entries: dict):
    assert len(entries) >= V2_MIN_ENTRY_COUNT, (
        f"Expected >= {V2_MIN_ENTRY_COUNT} entries (v2 floor); got "
        f"{len(entries)}."
    )


def test_meta_block_present(raw_db: dict):
    """`_meta` documents version + sourcing basis. Other tests strip it
    so it can't quietly disappear; this test makes the absence loud."""
    assert "_meta" in raw_db
    meta = raw_db["_meta"]
    for required in ("version", "currency", "basis", "matching", "cost_category", "waste_factor"):
        assert required in meta, f"_meta missing required key: {required}"


# ---------------------------------------------------------------------------
# Per-entry schema
# ---------------------------------------------------------------------------


def test_every_entry_has_required_fields(entries: dict):
    """Required fields: description, unit, unit_cost, cost_category,
    waste_factor, keywords. The loader hard-requires unit + unit_cost;
    the rest are required by the v2 contract."""
    missing: list[tuple[str, str]] = []
    for key, entry in entries.items():
        for field in ("description", "unit", "unit_cost", "cost_category", "waste_factor", "keywords"):
            if field not in entry:
                missing.append((key, field))
    assert not missing, f"Entries missing required fields: {missing[:10]}"


def test_every_entry_has_valid_cost_category(entries: dict):
    bad = [
        (k, v.get("cost_category"))
        for k, v in entries.items()
        if v.get("cost_category") not in VALID_COST_CATEGORIES
    ]
    assert not bad, (
        f"Entries with invalid cost_category (must be one of "
        f"{sorted(VALID_COST_CATEGORIES)}): {bad[:10]}"
    )


def test_every_entry_has_positive_unit_cost(entries: dict):
    """A $0 unit cost is almost always a stub. The v2 expansion sources
    every line from a public reference and prices it; if a row landed at
    $0 it's a wiring bug, not a real seed."""
    zero_or_negative = [
        (k, v.get("unit_cost"))
        for k, v in entries.items()
        if not (isinstance(v.get("unit_cost"), (int, float)) and v["unit_cost"] > 0)
    ]
    assert not zero_or_negative, (
        f"Entries with unit_cost <= 0 or non-numeric: {zero_or_negative[:10]}"
    )


def test_every_entry_has_plausible_waste_factor(entries: dict):
    """waste_factor convention: >= 1.00 (estimator clamps), <= 1.20 (any
    higher and a human should look at it)."""
    bad: list[tuple[str, float]] = []
    for k, v in entries.items():
        wf = v.get("waste_factor")
        if not isinstance(wf, (int, float)):
            bad.append((k, wf))
            continue
        if wf < 1.00 or wf > 1.20:
            bad.append((k, wf))
    assert not bad, (
        f"Entries with implausible waste_factor (expected 1.00 - 1.20): "
        f"{bad[:10]}"
    )


def test_every_entry_has_recognised_unit(entries: dict):
    bad = [
        (k, v.get("unit"))
        for k, v in entries.items()
        if v.get("unit") not in ALLOWED_UNITS
    ]
    assert not bad, (
        f"Entries with unrecognised unit (allowed: {sorted(ALLOWED_UNITS)}): "
        f"{bad[:10]}"
    )


def test_keywords_field_is_non_empty_list(entries: dict):
    bad = [
        k for k, v in entries.items()
        if not isinstance(v.get("keywords"), list) or not v["keywords"]
    ]
    assert not bad, f"Entries with empty / non-list keywords: {bad[:10]}"


# ---------------------------------------------------------------------------
# v2-specific source-attribution contract
# ---------------------------------------------------------------------------


def test_v2_additions_cite_a_public_source(entries: dict):
    """Every entry that carries a `notes` field must reference one of
    the approved public-domain sources. This pins the *intent* of the v2
    expansion (no internal historical pricing — all public references).

    Entries without `notes` are presumed pre-v2 (the original ~45-row
    seed) and are exempt — those rows were hand-seeded with national
    averages and never carried citations.
    """
    approved_tokens = (
        "fema", "gsa", "nahb", "agc", "usace", "hud", "bls", "epa",
        "nps", "bureau of reclamation", "nfpa",
    )
    bad: list[str] = []
    for k, v in entries.items():
        notes = v.get("notes")
        if not notes:
            continue
        if not isinstance(notes, str) or not notes.strip():
            bad.append(k)
            continue
        haystack = notes.lower()
        if not any(token in haystack for token in approved_tokens):
            bad.append(k)
    assert not bad, (
        f"v2 entries with notes that don't cite an approved public source "
        f"({approved_tokens}): {bad[:10]}"
    )


def test_v2_expansion_added_meaningful_volume(entries: dict):
    """At least 70 entries should carry source citations (the v2 floor
    is ~80 new entries, leaving headroom for one or two omissions)."""
    cited = [k for k, v in entries.items() if v.get("notes")]
    assert len(cited) >= 70, (
        f"Only {len(cited)} entries carry a source citation; expected "
        f">= 70 from the v2 expansion."
    )


# ---------------------------------------------------------------------------
# Division coverage
# ---------------------------------------------------------------------------


def test_required_divisions_covered(entries: dict):
    """Each capability-library scope template anchors on a specific CSI
    division. Confirm v2 added at least one row in every division the
    new templates rely on."""
    divisions = {k.split()[0] for k in entries.keys()}
    missing = V2_REQUIRED_DIVISIONS - divisions
    assert not missing, (
        f"Required CSI divisions missing from the cost DB: {sorted(missing)}. "
        f"Present: {sorted(divisions)}."
    )


def test_food_service_family_present(entries: dict):
    """CSI 11 40 series (food service) — confirm the family landed."""
    food_service = [
        k for k in entries.keys()
        if k.startswith("11 4") or k.startswith("11 41") or k.startswith("11 45")
    ]
    assert len(food_service) >= 8, (
        f"Expected >= 8 CSI 11 4x entries (food-service family); got "
        f"{len(food_service)}: {food_service}"
    )


def test_security_fence_family_present(entries: dict):
    """CSI 32 31 series (fencing) — confirm the family landed."""
    fence = [k for k in entries.keys() if k.startswith("32 31")]
    assert len(fence) >= 10, (
        f"Expected >= 10 CSI 32 31 entries (security-fence family); got "
        f"{len(fence)}: {fence}"
    )


def test_roof_historic_family_present(entries: dict):
    """CSI 07 31 / 07 41 / 07 62 / 07 72 — historic roofing material +
    flashing + vent rows."""
    keys = list(entries.keys())
    roof = [
        k for k in keys
        if k.startswith("07 31") or k.startswith("07 41") or k.startswith("07 62")
        or k.startswith("07 72") or k.startswith("07 25") or k.startswith("07 01")
    ]
    assert len(roof) >= 8, (
        f"Expected >= 8 historic-roof entries (CSI 07 family); got "
        f"{len(roof)}: {roof}"
    )


def test_restroom_historic_family_present(entries: dict):
    """CSI 22 41 ADA fixtures + 09 30 historic tile + 10 28 grab bars."""
    keys = list(entries.keys())
    ada_fixtures = [k for k in keys if k.startswith("22 41")]
    historic_tile = [k for k in keys if k.startswith("09 30")]
    grab_bars = [k for k in keys if k.startswith("10 28")]
    assert len(ada_fixtures) >= 3, f"Expected >= 3 ADA fixture entries; got: {ada_fixtures}"
    assert len(historic_tile) >= 2, f"Expected >= 2 historic-tile entries; got: {historic_tile}"
    assert len(grab_bars) >= 1, f"Expected >= 1 grab-bar entry; got: {grab_bars}"


def test_gymnasium_family_present(entries: dict):
    """CSI 09 64 / 09 65 sport floor, 12 66 telescoping bleachers,
    23 74 RTU, 26 51 high-bay LED — gym multi-system rows."""
    keys = list(entries.keys())
    sport_floor = [k for k in keys if k.startswith("09 64") or k.startswith("09 65 26") or k.startswith("09 65 66")]
    bleachers = [k for k in keys if k.startswith("12 66") or k.startswith("12 63")]
    assert len(sport_floor) >= 3, f"Expected >= 3 sport-floor entries; got: {sport_floor}"
    assert len(bleachers) >= 3, f"Expected >= 3 bleacher entries; got: {bleachers}"


# ---------------------------------------------------------------------------
# Sort order
# ---------------------------------------------------------------------------


def test_entries_sorted_by_csi(entries: dict):
    """The file is intended to read top-to-bottom in CSI division order
    for human auditing. JSON spec doesn't guarantee key order but every
    parser we use (incl. CPython 3.7+) preserves insertion order, so we
    can pin it."""
    keys = list(entries.keys())
    sorted_keys = sorted(keys)
    assert keys == sorted_keys, (
        f"Entries not sorted by CSI key. First out-of-order: "
        f"file={[k for k, s in zip(keys, sorted_keys) if k != s][:1]}, "
        f"expected={[s for k, s in zip(keys, sorted_keys) if k != s][:1]}"
    )
