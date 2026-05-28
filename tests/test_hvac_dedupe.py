"""Tests for ``dedupe_hvac_against_synthesis`` (Phase T2.8).

Mirrors the convention used by ``tests/test_lighting_dedupe.py`` and
``tests/test_panel_dedupe.py`` — builds a small synthetic TakeoffItem
list, runs the dedupe pass, asserts the right rows survive.
"""

from __future__ import annotations

from core.extraction.hvac_dedupe import dedupe_hvac_against_synthesis
from core.extraction.takeoff_synthesis import (
    SYNTHESIS_SOURCE_TAG_HVAC,
    synthesize_hvac_takeoff_items,
)
from core.schemas import HVACEquipmentRecord, TakeoffItem


def _llm_row(description: str, *, csi_division: str = "23",
               csi_section: str | None = None, unit: str = "EA",
               quantity: float = 1.0) -> TakeoffItem:
    """Helper: build a legacy-LLM-style TakeoffItem (no synthesis tag)."""
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=quantity,
        unit=unit,
        confidence=0.8,
        notes="source=llm_path",
    )


def _make_record(tag: str = "AHU-1", etype: str = "AHU") -> HVACEquipmentRecord:
    return HVACEquipmentRecord(
        equipment_tag=tag,
        equipment_type=etype,
        description="Indoor air handler",
        capacity_value=2000.0,
        capacity_unit="CFM",
        motor_hp=5.0,
        voltage="480V/3PH",
    )


def test_llm_ahu_install_row_suppressed_by_synthesis() -> None:
    """LLM ``"AHU-1 installation"`` row → suppressed when synthesis exists."""
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    llm = _llm_row("AHU-1 installation", csi_section="23 73 13")
    items = synthesis + [llm]
    result = dedupe_hvac_against_synthesis(items)
    descs = [i.description for i in result]
    assert "AHU-1 installation" not in descs
    # Synthesis rows are preserved
    assert any("Equipment AHU-1" in d for d in descs)


def test_llm_plumbing_row_not_suppressed() -> None:
    """A plumbing line (Division 22) must NEVER be touched by HVAC dedupe."""
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    plumbing = _llm_row(
        "Plumbing fixture - water closet",
        csi_division="22", csi_section="22 40 00",
    )
    items = synthesis + [plumbing]
    result = dedupe_hvac_against_synthesis(items)
    assert plumbing in result


def test_llm_lighting_row_not_suppressed() -> None:
    """A lighting line (CSI ``26 51``) must NEVER be touched by HVAC dedupe."""
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    lighting = _llm_row(
        "Light fixtures",
        csi_division="26", csi_section="26 51 13",
    )
    items = synthesis + [lighting]
    result = dedupe_hvac_against_synthesis(items)
    assert lighting in result


def test_llm_panel_row_not_suppressed() -> None:
    """An electrical panel line (``26 24``) must NEVER be touched."""
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    panel = _llm_row(
        "Panel PNL-A",
        csi_division="26", csi_section="26 24 16",
    )
    items = synthesis + [panel]
    result = dedupe_hvac_against_synthesis(items)
    assert panel in result


def test_empty_synthesis_preserves_all_llm_lines() -> None:
    """Safety rule: no synthesis on the project → input returned unchanged."""
    llm_rows = [
        _llm_row("HVAC equipment", csi_section="23 00 00"),
        _llm_row("Rooftop units", csi_section="23 74 13"),
        _llm_row("Mechanical Equipment", csi_section=None),
    ]
    result = dedupe_hvac_against_synthesis(llm_rows)
    assert result == llm_rows


def test_empty_input_returns_empty_list() -> None:
    """No-op on empty input."""
    assert dedupe_hvac_against_synthesis([]) == []


def test_aggregate_descriptions_dropped_when_synthesis_present() -> None:
    """LLM rollup descriptions (``"Mechanical Equipment"``) are dropped."""
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    rollups = [
        _llm_row("Mechanical Equipment: 5 EA", csi_section=None),
        _llm_row("RTU installation", csi_section="23 74 13"),
        _llm_row("Air handling units", csi_section=None),
    ]
    items = synthesis + rollups
    result = dedupe_hvac_against_synthesis(items)
    descs = [i.description for i in result]
    for desc in ("Mechanical Equipment: 5 EA", "RTU installation",
                  "Air handling units"):
        assert desc not in descs


def test_unrelated_division_23_row_preserved() -> None:
    """An unrelated Division-23 row (e.g. ``Pipe insulation``) is preserved.

    The aggregate-pattern regex is anchored — only the specific HVAC
    rollup forms are matched.  A line like ``"Pipe insulation"`` doesn't
    match any pattern, so it survives even though it shares the ``23``
    prefix.
    """
    synthesis = synthesize_hvac_takeoff_items([_make_record("AHU-1", "AHU")])
    other_23 = _llm_row(
        "Pipe insulation - mineral fiber 1\" thk", csi_section="23 07 13",
    )
    items = synthesis + [other_23]
    result = dedupe_hvac_against_synthesis(items)
    assert other_23 in result
