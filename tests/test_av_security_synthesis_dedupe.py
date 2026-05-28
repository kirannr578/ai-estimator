"""Tests for the Phase T2.11 AV + Security synthesis + dedupe wrappers.

Combined coverage for the two new synthesis functions
(:func:`synthesize_av_takeoff_items`,
:func:`synthesize_security_takeoff_items`) and their dedupe wrappers
(:func:`dedupe_av_against_synthesis`,
:func:`dedupe_security_against_synthesis`).

The dangerous case under audit is the CAM- cross-domain collision:
the AV dedupe must NOT catch security camera rows and the Security
dedupe must NOT catch AV camera rows, even though both schedules
use ``CAM-N`` tags.
"""

from __future__ import annotations

from core.extraction.av_dedupe import dedupe_av_against_synthesis
from core.extraction.security_dedupe import dedupe_security_against_synthesis
from core.extraction.takeoff_synthesis import (
    DERIVATION_HAIRCUT_MULTIPLIER,
    SYNTHESIS_SOURCE_TAG_AV,
    SYNTHESIS_SOURCE_TAG_SECURITY,
    inherit_with_haircut,
    synthesize_av_takeoff_items,
    synthesize_security_takeoff_items,
)
from core.schemas import (
    AVDeviceRecord,
    AVScheduleResult,
    CostBand,
    SecurityDeviceRecord,
    SecurityScheduleResult,
    TakeoffItem,
    band_for_confidence,
)


# ---------------------------------------------------------------------------
# Record builders — AV
# ---------------------------------------------------------------------------


def _av_display(*, qty: int | None = None, mfr: str | None = None,
                model: str | None = None) -> AVDeviceRecord:
    return AVDeviceRecord(
        tag="DISP-1", item_type="DISPLAY",
        description="LCD Display",
        manufacturer=mfr, model_number=model,
        size_or_resolution='75"', mounting="WALL", power="120V",
        signal_type="HDMI", quantity=qty,
    )


def _av_projector(*, qty: int | None = None, mfr: str | None = None,
                  model: str | None = None) -> AVDeviceRecord:
    return AVDeviceRecord(
        tag="PROJ-1", item_type="PROJECTOR",
        description="4K projector",
        manufacturer=mfr, model_number=model,
        size_or_resolution="4K", mounting="CEILING", power="120V",
        signal_type="HDMI", quantity=qty,
    )


def _av_control() -> AVDeviceRecord:
    return AVDeviceRecord(
        tag="CTRL-1", item_type="CONTROL_PROCESSOR",
        description="Control processor",
        mounting="RACK", power="120V", quantity=1,
    )


def _av_network_switch() -> AVDeviceRecord:
    return AVDeviceRecord(
        tag="SW-1", item_type="NETWORK_SWITCH",
        description="AV network switch",
        mounting="RACK", power="120V", quantity=1,
    )


def _av_cam_conference() -> AVDeviceRecord:
    return AVDeviceRecord(
        tag="CAM-1", item_type="CAMERA",
        description="Conference camera",
        mounting="WALL", power="USB", signal_type="USB", quantity=2,
    )


# ---------------------------------------------------------------------------
# Record builders — Security
# ---------------------------------------------------------------------------


def _sec_card_reader(*, qty: int | None = None) -> SecurityDeviceRecord:
    return SecurityDeviceRecord(
        tag="DR-1", item_type="CARD_READER",
        description="Prox card reader", manufacturer="HID",
        mounting="WALL", power="POE", connection="WIEGAND",
        quantity=qty,
    )


def _sec_camera() -> SecurityDeviceRecord:
    return SecurityDeviceRecord(
        tag="CAM-1", item_type="CAMERA",
        description="PTZ surveillance camera",
        manufacturer="Axis", model_number="Q3517",
        mounting="CEILING", power="POE", connection="CAT6",
        quantity=4,
    )


def _sec_motion() -> SecurityDeviceRecord:
    return SecurityDeviceRecord(
        tag="MS-1", item_type="MOTION_SENSOR",
        description="Motion sensor",
        mounting="CEILING", power="12VDC", connection="RS-485",
        quantity=6,
    )


def _sec_door_contact() -> SecurityDeviceRecord:
    return SecurityDeviceRecord(
        tag="DC-1", item_type="DOOR_CONTACT",
        description="Door contact",
        mounting="DOOR_FRAME", power="12VDC",
        quantity=8,
    )


def _sec_maglock() -> SecurityDeviceRecord:
    return SecurityDeviceRecord(
        tag="ML-1", item_type="MAGLOCK",
        description="Electromagnetic lock", manufacturer="HES",
        model_number="320-2",
        mounting="DOOR_FRAME", power="24VDC", connection="RS-485",
        quantity=2,
    )


def _llm(description: str, *, csi_section: str | None = "27 41 16",
         csi_division: str = "27", confidence: float = 0.7,
         qty: float = 1.0, unit: str = "EA") -> TakeoffItem:
    return TakeoffItem(
        csi_division=csi_division,
        csi_section=csi_section,
        description=description,
        quantity=qty,
        unit=unit,
        confidence=confidence,
    )


# ===========================================================================
# AV — synthesis shape + CSI mapping
# ===========================================================================


def test_synthesize_av_empty_returns_empty() -> None:
    assert synthesize_av_takeoff_items(None) == []
    assert synthesize_av_takeoff_items([]) == []
    assert synthesize_av_takeoff_items(
        AVScheduleResult(devices=[])
    ) == []


def test_synthesize_av_display_with_qty_emits_two_rows() -> None:
    """DISPLAY with QTY but no mfr+model → 2 rows (device + cabling)."""
    items = synthesize_av_takeoff_items([_av_display(qty=3)])
    assert len(items) == 2
    eq, cabling = items
    assert eq.unit == "EA"
    assert eq.quantity == 3.0
    assert eq.confidence == 0.90
    assert eq.csi_section == "27 41 16.51"
    assert cabling.unit == "LS"
    assert cabling.csi_section == "27 15 13.13"


def test_synthesize_av_display_with_mfr_model_emits_three_rows() -> None:
    """DISPLAY with QTY + mfr + model → 3 rows (device + cabling + programming)."""
    items = synthesize_av_takeoff_items([
        _av_display(qty=3, mfr="Samsung", model="QM75R"),
    ])
    assert len(items) == 3
    eq, cabling, prog = items
    assert eq.csi_section == "27 41 16.51"
    assert cabling.csi_section == "27 15 13.13"
    # Programming row inherits the device CSI section.
    assert prog.csi_section == "27 41 16.51"
    assert prog.unit == "LS"


def test_synthesize_av_projector_csi() -> None:
    items = synthesize_av_takeoff_items([_av_projector(qty=1)])
    assert items[0].csi_section == "27 41 16.31"
    assert items[1].csi_section == "27 15 13.13"


def test_synthesize_av_control_processor_always_gets_programming() -> None:
    """CONTROL_PROCESSOR ALWAYS gets a programming row regardless of mfr/model."""
    items = synthesize_av_takeoff_items([_av_control()])
    assert len(items) == 3
    eq, cabling, prog = items
    assert eq.csi_section == "27 41 19.13"
    assert prog.csi_section == "27 41 19.13"
    assert "programming" in (prog.description or "").lower()


def test_synthesize_av_network_switch_always_gets_programming() -> None:
    """NETWORK_SWITCH ALWAYS gets programming and Div-27 (not Div-26)."""
    items = synthesize_av_takeoff_items([_av_network_switch()])
    assert len(items) == 3
    eq, cabling, prog = items
    assert eq.csi_section == "27 21 33"
    assert eq.csi_division == "27"  # NOT Div 26 electrical
    assert prog.csi_section == "27 21 33"


def test_synthesize_av_microphone_csi() -> None:
    record = AVDeviceRecord(
        tag="MIC-1", item_type="MICROPHONE",
        description="Ceiling mic", quantity=4,
    )
    items = synthesize_av_takeoff_items([record])
    assert items[0].csi_section == "27 41 33.13"


def test_synthesize_av_speaker_csi() -> None:
    record = AVDeviceRecord(
        tag="SPK-1", item_type="SPEAKER",
        description="Loudspeaker", quantity=8,
    )
    items = synthesize_av_takeoff_items([record])
    assert items[0].csi_section == "27 41 33.16"


def test_synthesize_av_rack_csi() -> None:
    record = AVDeviceRecord(
        tag="RACK-1", item_type="RACK",
        description="AV rack", quantity=1,
    )
    items = synthesize_av_takeoff_items([record])
    assert items[0].csi_section == "27 11 26"


def test_synthesize_av_camera_csi() -> None:
    items = synthesize_av_takeoff_items([_av_cam_conference()])
    assert items[0].csi_section == "27 41 16.49"


def test_synthesize_av_other_falls_back_to_generic_section() -> None:
    record = AVDeviceRecord(
        tag="AV-9", item_type="OTHER", description="Misc AV",
    )
    items = synthesize_av_takeoff_items([record])
    assert items[0].csi_section == "27 41 16"


def test_synthesize_av_skips_blank_tags() -> None:
    record = AVDeviceRecord(
        tag="", item_type="DISPLAY", description="Unmarked",
    )
    assert synthesize_av_takeoff_items([record]) == []


def test_synthesize_av_no_qty_lands_in_hand_takeoff_band() -> None:
    items = synthesize_av_takeoff_items([_av_display(mfr="Samsung", model="QM75R")])
    eq = items[0]
    assert eq.confidence == 0.55
    assert band_for_confidence(eq.confidence) == CostBand.HAND_TAKEOFF


def test_synthesize_av_qty_lands_in_auto_approve_band() -> None:
    items = synthesize_av_takeoff_items([_av_display(qty=3)])
    eq = items[0]
    assert eq.confidence == 0.90
    assert band_for_confidence(eq.confidence) == CostBand.AUTO_APPROVE


def test_synthesize_av_cabling_inherits_haircut_from_parent() -> None:
    items = synthesize_av_takeoff_items([_av_display(qty=3)])
    _, cabling = items
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.95,
    )
    assert cabling.confidence == expected
    # 0.90 × 0.95 × 0.95 = 0.81225 → 0.8123 rounded.
    assert cabling.confidence < 0.90


def test_synthesize_av_programming_inherits_double_haircut() -> None:
    items = synthesize_av_takeoff_items([
        _av_display(qty=3, mfr="Samsung", model="QM75R"),
    ])
    _, _, prog = items
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.70,
    )
    assert prog.confidence == expected


def test_synthesize_av_notes_carry_source_tag() -> None:
    items = synthesize_av_takeoff_items([_av_display(qty=1)])
    for it in items:
        assert (it.notes or "").startswith(f"source={SYNTHESIS_SOURCE_TAG_AV}")


def test_synthesize_av_description_prefix_is_av_device() -> None:
    items = synthesize_av_takeoff_items([_av_display(qty=1)])
    for it in items:
        assert (it.description or "").lower().startswith("av device")


def test_synthesize_av_sheet_id_threads_into_source_sheet_ids() -> None:
    items = synthesize_av_takeoff_items(
        [_av_display(qty=1)], sheet_id="T2.0",
    )
    for it in items:
        assert "T2.0" in (it.source_sheet_ids or [])


# ===========================================================================
# Security — synthesis shape + CSI mapping
# ===========================================================================


def test_synthesize_security_empty_returns_empty() -> None:
    assert synthesize_security_takeoff_items(None) == []
    assert synthesize_security_takeoff_items([]) == []
    assert synthesize_security_takeoff_items(
        SecurityScheduleResult(devices=[])
    ) == []


def test_synthesize_security_card_reader_emits_three_rows() -> None:
    """CARD_READER → device + cabling + programming (always required)."""
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=4)])
    assert len(items) == 3
    eq, cabling, prog = items
    assert eq.csi_section == "28 13 23.13"
    assert cabling.csi_section == "28 05 13"
    assert prog.csi_section == "28 13 23.13"
    assert prog.unit == "LS"


def test_synthesize_security_camera_emits_two_rows() -> None:
    """CAMERA without mfr+model → device + cabling (no programming)."""
    record = SecurityDeviceRecord(
        tag="CAM-1", item_type="CAMERA",
        description="PTZ camera",
        mounting="CEILING", power="POE", connection="CAT6", quantity=4,
    )
    items = synthesize_security_takeoff_items([record])
    assert len(items) == 2
    eq, cabling = items
    assert eq.csi_section == "28 23 23"
    assert cabling.csi_section == "28 05 13"


def test_synthesize_security_camera_with_mfr_model_emits_three_rows() -> None:
    """CAMERA with mfr+model gets programming."""
    items = synthesize_security_takeoff_items([_sec_camera()])
    assert len(items) == 3


def test_synthesize_security_motion_csi() -> None:
    items = synthesize_security_takeoff_items([_sec_motion()])
    assert items[0].csi_section == "28 16 13.13"
    assert items[1].csi_section == "28 05 13"


def test_synthesize_security_door_contact_excludes_cabling() -> None:
    """DOOR_CONTACT is excluded from cabling rough-in (wired inside frame)."""
    items = synthesize_security_takeoff_items([_sec_door_contact()])
    assert len(items) == 1
    assert items[0].csi_section == "28 16 16.13"
    assert items[0].unit == "EA"


def test_synthesize_security_keypad_csi() -> None:
    record = SecurityDeviceRecord(
        tag="KP-1", item_type="KEYPAD",
        description="Keypad", mounting="WALL", power="12VDC",
        connection="WIEGAND", quantity=2,
    )
    items = synthesize_security_takeoff_items([record])
    assert items[0].csi_section == "28 13 23.16"


def test_synthesize_security_rte_csi() -> None:
    record = SecurityDeviceRecord(
        tag="RTE-1", item_type="REQUEST_TO_EXIT",
        description="REX device", mounting="WALL", quantity=2,
    )
    items = synthesize_security_takeoff_items([record])
    assert items[0].csi_section == "28 13 33.13"


def test_synthesize_security_maglock_csi_and_programming() -> None:
    """MAGLOCK → Div 28 (NOT Div 8) + ALWAYS-required programming."""
    items = synthesize_security_takeoff_items([_sec_maglock()])
    assert len(items) == 3
    eq, cabling, prog = items
    assert eq.csi_division == "28"  # NOT Div 8
    assert eq.csi_section == "28 13 43.13"
    assert cabling.csi_section == "28 05 13"
    assert prog.csi_section == "28 13 43.13"


def test_synthesize_security_other_falls_back_to_generic_section() -> None:
    record = SecurityDeviceRecord(
        tag="X-9", item_type="OTHER", description="Misc",
    )
    items = synthesize_security_takeoff_items([record])
    assert items[0].csi_section == "28 13 00"


def test_synthesize_security_skips_blank_tags() -> None:
    record = SecurityDeviceRecord(
        tag="", item_type="CARD_READER", description="Unmarked",
    )
    assert synthesize_security_takeoff_items([record]) == []


def test_synthesize_security_qty_lands_in_auto_approve_band() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=4)])
    eq = items[0]
    assert eq.confidence == 0.90
    assert band_for_confidence(eq.confidence) == CostBand.AUTO_APPROVE


def test_synthesize_security_no_qty_lands_in_hand_takeoff_band() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader()])
    eq = items[0]
    assert eq.confidence == 0.55
    assert band_for_confidence(eq.confidence) == CostBand.HAND_TAKEOFF


def test_synthesize_security_cabling_inherits_haircut_from_parent() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=4)])
    cabling = items[1]
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.95,
    )
    assert cabling.confidence == expected
    assert cabling.confidence < 0.90


def test_synthesize_security_programming_inherits_double_haircut() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=4)])
    prog = items[2]
    expected = inherit_with_haircut(
        0.90, multiplier=DERIVATION_HAIRCUT_MULTIPLIER * 0.70,
    )
    assert prog.confidence == expected


def test_synthesize_security_notes_carry_source_tag() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=1)])
    for it in items:
        assert (it.notes or "").startswith(
            f"source={SYNTHESIS_SOURCE_TAG_SECURITY}"
        )


def test_synthesize_security_description_prefix_is_security_device() -> None:
    items = synthesize_security_takeoff_items([_sec_card_reader(qty=1)])
    for it in items:
        assert (it.description or "").lower().startswith("security device")


# ===========================================================================
# AV dedupe — suppression
# ===========================================================================


def _synth_av_display() -> list[TakeoffItem]:
    return synthesize_av_takeoff_items([
        _av_display(qty=3, mfr="Samsung", model="QM75R"),
    ])


def test_dedupe_av_suppresses_av_equipment_aggregate() -> None:
    items = _synth_av_display() + [
        _llm("AV Equipment"),
        _llm("Audio Visual Equipment installation"),
        _llm("AV/IT System"),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "AV Equipment" not in descs
    assert "Audio Visual Equipment installation" not in descs
    assert "AV/IT System" not in descs


def test_dedupe_av_suppresses_per_mark_llm_row() -> None:
    items = _synth_av_display() + [
        _llm("DISP-1 75\" display installation"),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert all("DISP-1 75" not in (d or "") or "AV device" in (d or "")
                for d in descs)


def test_dedupe_av_no_op_when_no_synthesis_present() -> None:
    items = [
        _llm("AV Equipment"),
        _llm("Audio Visual Equipment"),
    ]
    survivors = dedupe_av_against_synthesis(items)
    assert len(survivors) == 2


# ===========================================================================
# AV dedupe — cross-domain safety
# ===========================================================================


def test_dedupe_av_does_not_catch_security_camera_rows() -> None:
    """A security CAMERA row at CSI 28 23 23 must NOT be touched by AV dedupe."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="28", csi_section="28 23 23",
            description="Security device CAM-1 — PTZ camera",
            quantity=4.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert any("Security device CAM-1" in (d or "") for d in descs)


def test_dedupe_av_does_not_catch_bare_cam_llm_row() -> None:
    """Bare ``CAM-1`` LLM row — neither tag-only form is matched."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="28", csi_section="28 23 23",
            description="CAM-1",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "CAM-1" in descs


def test_dedupe_av_does_not_catch_door_hardware() -> None:
    """Phase T1 door hardware rows (Div 8) must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal door 3'-0\" x 7'-0\"",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
        TakeoffItem(
            csi_division="08", csi_section="08 71 00",
            description="Door hardware set",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Hollow metal door 3'-0\" x 7'-0\"" in descs
    assert "Door hardware set" in descs


def test_dedupe_av_does_not_catch_panel_rows() -> None:
    """Panel schedule (T2.6 Div 26) rows must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="26", csi_section="26 24 16",
            description="Panel LP-1 — 42-circuit",
            quantity=1.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Panel LP-1 — 42-circuit" in descs


def test_dedupe_av_does_not_catch_lighting_rows() -> None:
    """Lighting fixture (T2.7 Div 26 51) rows must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="26", csi_section="26 51 13",
            description="LED downlight fixture",
            quantity=10.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "LED downlight fixture" in descs


def test_dedupe_av_does_not_catch_plumbing_rows() -> None:
    """Plumbing (T2.9 Div 22) rows must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="22", csi_section="22 41 16",
            description="Lavatory faucet",
            quantity=4.0, unit="EA", confidence=0.8,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Lavatory faucet" in descs


def test_dedupe_av_does_not_catch_kitchen_rows() -> None:
    """Kitchen equipment (T2.10 Div 11) rows must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="11", csi_section="11 40 13.13",
            description="Kitchen equipment RA-1 — 6-burner range",
            quantity=1.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Kitchen equipment RA-1 — 6-burner range" in descs


def test_dedupe_av_does_not_catch_lab_rows() -> None:
    """Lab casework (T2.10 Div 11/12) rows must survive."""
    items = _synth_av_display() + [
        TakeoffItem(
            csi_division="12", csi_section="12 35 53",
            description="Lab equipment BENCH-1 — epoxy bench",
            quantity=1.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_av_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Lab equipment BENCH-1 — epoxy bench" in descs


# ===========================================================================
# Security dedupe — suppression
# ===========================================================================


def _synth_sec_card_reader() -> list[TakeoffItem]:
    return synthesize_security_takeoff_items([_sec_card_reader(qty=4)])


def test_dedupe_security_suppresses_security_equipment_aggregate() -> None:
    items = _synth_sec_card_reader() + [
        _llm("Security Equipment", csi_section="28 13 00",
             csi_division="28"),
        _llm("Access Control System", csi_section="28 13 00",
             csi_division="28"),
        _llm("Card Reader System", csi_section="28 13 23.13",
             csi_division="28"),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Security Equipment" not in descs
    assert "Access Control System" not in descs
    assert "Card Reader System" not in descs


def test_dedupe_security_suppresses_per_mark_llm_row() -> None:
    items = _synth_sec_card_reader() + [
        _llm("DR-1 card reader installation",
             csi_section="28 13 23.13", csi_division="28"),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "DR-1 card reader installation" not in descs


def test_dedupe_security_no_op_when_no_synthesis_present() -> None:
    items = [
        _llm("Security Equipment", csi_section="28 13 00",
             csi_division="28"),
    ]
    survivors = dedupe_security_against_synthesis(items)
    assert len(survivors) == 1


# ===========================================================================
# Security dedupe — cross-domain safety
# ===========================================================================


def test_dedupe_security_does_not_catch_av_camera_rows() -> None:
    """An AV CAMERA row at CSI 27 41 16.49 must NOT be touched by Security dedupe."""
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="27", csi_section="27 41 16.49",
            description="AV device CAM-1 — Conference camera",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert any("AV device CAM-1" in (d or "") for d in descs)


def test_dedupe_security_does_not_catch_bare_cam_llm_row() -> None:
    """Bare ``CAM-1`` LLM row — neither tag-only form is matched."""
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="27", csi_section="27 41 16.49",
            description="CAM-1",
            quantity=1.0, unit="EA", confidence=0.7,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "CAM-1" in descs


def test_dedupe_security_does_not_catch_t1_door_hardware() -> None:
    """Phase T1 door hardware (Div 8 71 00) rows must survive — the
    Security dedupe scope is CSI ``28 ...`` only.
    """
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="08", csi_section="08 71 00",
            description="Door hardware set HDW-1",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="Hollow metal door 3'-0\" x 7'-0\"",
            quantity=2.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Door hardware set HDW-1" in descs
    assert "Hollow metal door 3'-0\" x 7'-0\"" in descs


def test_dedupe_security_does_not_catch_panel_rows() -> None:
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="26", csi_section="26 24 16",
            description="Panel LP-1 — 42-circuit",
            quantity=1.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "Panel LP-1 — 42-circuit" in descs


def test_dedupe_security_does_not_catch_lighting_rows() -> None:
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="26", csi_section="26 51 13",
            description="LED downlight fixture",
            quantity=10.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "LED downlight fixture" in descs


def test_dedupe_security_does_not_catch_av_rows() -> None:
    """AV Div 27 rows must survive Security dedupe pass."""
    av_synth = synthesize_av_takeoff_items([_av_display(qty=3)])
    items = _synth_sec_card_reader() + av_synth
    survivors = dedupe_security_against_synthesis(items)
    av_descs = [
        s.description for s in survivors
        if s.csi_division == "27"
    ]
    assert len(av_descs) == len(av_synth)


def test_dedupe_security_dr_n_mark_only_fires_inside_28_scope() -> None:
    """Per-mark DR-N regex fires only when the row is at CSI 28 OR has
    the ``Security device`` description anchor.  A Phase T1 row at CSI
    08 with description ``"DR-1"`` survives because the dedupe scope
    is CSI 28 only."""
    items = _synth_sec_card_reader() + [
        TakeoffItem(
            csi_division="08", csi_section="08 11 13",
            description="DR-1",  # Phase T1 door mark
            quantity=1.0, unit="EA", confidence=0.85,
        ),
    ]
    survivors = dedupe_security_against_synthesis(items)
    descs = [s.description for s in survivors]
    assert "DR-1" in descs
