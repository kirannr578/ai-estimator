"""Tests for the Phase T2.11 Security / Access-Control schedule extractor.

Builds synthetic PDFs against ``extract_security_schedule_from_page`` plus
a handful of unit-level tests against the cell / header parsers.  Mirrors
:mod:`tests.test_av_schedule` for the Security family.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.security_schedule import (
    SecurityDeviceRecord,
    SecurityScheduleResult,
    _classify_item_type,
    _looks_like_security_header,
    _parse_connection,
    _parse_mounting,
    _parse_power,
    _parse_quantity,
    _security_indices,
    detect_security_schedule_page,
    extract_security_schedule_from_page,
    to_schema,
)


# ---------------------------------------------------------------------------
# Synthetic-PDF helpers
# ---------------------------------------------------------------------------


def _add_page(
    doc: "fitz.Document",
    *,
    title_lines: list[str] | None = None,
    table: list[list[str]] | None = None,
    table_origin: tuple[float, float] = (40.0, 220.0),
    cell_size: tuple[float, float] = (110.0, 24.0),
) -> None:
    if table:
        n_cols = max(len(r) for r in table)
        needed_w = table_origin[0] + cell_size[0] * n_cols + 40.0
        width = max(900.0, needed_w)
    else:
        width = 900.0
    page = doc.new_page(width=width, height=720)
    if title_lines:
        y = 60.0
        for line in title_lines:
            page.insert_text((40, y), line, fontsize=12)
            y += 16
    if table:
        n_rows = len(table)
        n_cols = max(len(r) for r in table)
        x0, y0 = table_origin
        cell_w, cell_h = cell_size
        x1 = x0 + cell_w * n_cols
        y1 = y0 + cell_h * n_rows
        for i in range(n_rows + 1):
            page.draw_line((x0, y0 + i * cell_h), (x1, y0 + i * cell_h))
        for j in range(n_cols + 1):
            page.draw_line((x0 + j * cell_w, y0), (x0 + j * cell_w, y1))
        for i, row in enumerate(table):
            for j, val in enumerate(row):
                page.insert_text(
                    (x0 + j * cell_w + 4, y0 + i * cell_h + 16),
                    str(val), fontsize=9,
                )


def _build_pdf(tmp_path: Path, name: str, **kw) -> Path:
    doc = fitz.open()
    _add_page(doc, **kw)
    out = tmp_path / name
    doc.save(out)
    doc.close()
    return out


def _extract_one(pdf: Path) -> SecurityScheduleResult:
    with fitz.open(pdf) as d:
        return extract_security_schedule_from_page(d[0], 0)


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


def test_detect_page_with_security_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_sec.pdf",
        title_lines=["SECURITY SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["DR-1", "Card reader",  "WALL",     "PoE",   "Cat6",       "2"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


def test_detect_page_with_access_control_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_sec_ac.pdf",
        title_lines=["ACCESS CONTROL SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",  "DESCRIPTION",     "MOUNTING", "POWER",  "CONNECTION"],
            ["RDR-1", "Prox reader",    "WALL",     "PoE",    "Wiegand"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


def test_detect_page_with_cctv_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_sec_cctv.pdf",
        title_lines=["CCTV SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",  "MOUNTING", "POWER", "CONNECTION"],
            ["CAM-1", "PTZ camera",   "CEILING",  "PoE",   "Cat6"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


def test_detect_page_with_video_surveillance_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_sec_vs.pdf",
        title_lines=["VIDEO SURVEILLANCE SCHEDULE", "Sheet S2.0"],
        table=[
            ["TAG",   "DESCRIPTION",  "MOUNTING", "POWER", "CONNECTION"],
            ["CAM-1", "Dome camera",  "CEILING",  "PoE",   "Cat6"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


def test_detect_page_with_card_reader_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_sec_cr.pdf",
        title_lines=["CARD READER SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "MOUNTING", "POWER", "READER"],
            ["CR-1", "Prox reader", "WALL",   "PoE",   "Wiegand"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


def test_detect_rejects_av_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_av.pdf",
        title_lines=["AV SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION",  "MFR",     "SIZE",  "MOUNTING", "SIGNAL"],
            ["DISP-1", "LCD Display",  "Samsung", "75\"",  "WALL",     "HDMI"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is False


def test_detect_rejects_lighting_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_lighting.pdf",
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION", "WATTS", "LUMENS"],
            ["A1",  "LED troffer", "40",    "4000"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is False


# ---------------------------------------------------------------------------
# DOOR HARDWARE SCHEDULE guard (Phase T1 architectural cross-talk)
# ---------------------------------------------------------------------------


def test_detect_rejects_phase_t1_door_hardware_schedule(tmp_path: Path) -> None:
    """A pure Phase-T1 architectural ``DOOR HARDWARE SCHEDULE`` must NOT
    trigger the security detector — no security context tokens.
    """
    pdf = _build_pdf(
        tmp_path, "detect_reject_dh.pdf",
        title_lines=["DOOR HARDWARE SCHEDULE"],
        table=[
            ["MARK",  "HARDWARE", "OPERATION", "RATING", "FRAME"],
            ["HDW-1", "Mortise lock set", "PASSAGE", "20MIN", "HM"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is False


def test_detect_accepts_door_hardware_with_security_context(tmp_path: Path) -> None:
    """A ``DOOR HARDWARE SCHEDULE`` carrying ``ELECTRIFIED`` / security
    context is fair game for the security extractor.
    """
    pdf = _build_pdf(
        tmp_path, "detect_dh_sec.pdf",
        title_lines=["DOOR HARDWARE SCHEDULE", "ELECTRIFIED HARDWARE"],
        table=[
            ["TAG", "DESCRIPTION", "MOUNTING", "POWER", "CONNECTION"],
            ["ML-1", "Maglock", "DOOR FRAME", "24VDC", "RS-485"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_security_schedule_page(d[0]) is True


# ---------------------------------------------------------------------------
# Item-type classifier
# ---------------------------------------------------------------------------


def test_classify_card_reader_dr_prefix() -> None:
    assert _classify_item_type("DR-1") == "CARD_READER"


def test_classify_card_reader_rdr_prefix() -> None:
    assert _classify_item_type("RDR-2") == "CARD_READER"


def test_classify_card_reader_cr_prefix() -> None:
    assert _classify_item_type("CR-1") == "CARD_READER"


def test_classify_camera_security_context() -> None:
    # Bare CAM- with no AV keyword → security CAMERA (this module's
    # extractor accepts it).
    assert _classify_item_type("CAM-1") == "CAMERA"
    assert _classify_item_type("CAM-1", "PTZ surveillance camera") == "CAMERA"
    assert _classify_item_type("CAM-1", "CCTV dome camera") == "CAMERA"


def test_classify_camera_rejected_when_av_context() -> None:
    # CAM- with conference/lecture/webcam → REJECTED to OTHER so the
    # security synthesis does not claim a conference camera.
    assert _classify_item_type("CAM-1", "Conference camera") == "OTHER"
    assert _classify_item_type("CAM-1", "Lecture capture camera") == "OTHER"
    assert _classify_item_type("CAM-1", "Huddle room webcam") == "OTHER"


def test_classify_motion_sensor_ms_prefix() -> None:
    assert _classify_item_type("MS-1") == "MOTION_SENSOR"


def test_classify_motion_sensor_mot_prefix() -> None:
    assert _classify_item_type("MOT-1") == "MOTION_SENSOR"


def test_classify_motion_sensor_pir_prefix() -> None:
    assert _classify_item_type("PIR-1") == "MOTION_SENSOR"


def test_classify_door_contact_dc_prefix() -> None:
    assert _classify_item_type("DC-1") == "DOOR_CONTACT"


def test_classify_keypad_kp_prefix() -> None:
    assert _classify_item_type("KP-1") == "KEYPAD"


def test_classify_rte_prefix() -> None:
    assert _classify_item_type("RTE-1") == "REQUEST_TO_EXIT"


def test_classify_maglock_ml_prefix() -> None:
    assert _classify_item_type("ML-1") == "MAGLOCK"


def test_classify_maglock_mag_prefix() -> None:
    assert _classify_item_type("MAG-1") == "MAGLOCK"


def test_classify_unknown_prefix() -> None:
    assert _classify_item_type("ZZ-9") == "OTHER"


def test_classify_from_description_only() -> None:
    assert _classify_item_type("X", "Card reader") == "CARD_READER"
    assert _classify_item_type("X", "PTZ camera") == "CAMERA"
    assert _classify_item_type("X", "Magnetic lock") == "MAGLOCK"
    assert _classify_item_type("X", "Door contact") == "DOOR_CONTACT"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


def test_parse_power_poe() -> None:
    assert _parse_power("PoE") == "POE"
    assert _parse_power("PoE+") == "POE+"


def test_parse_power_12vdc() -> None:
    assert _parse_power("12VDC") == "12VDC"
    assert _parse_power("12 VDC") == "12VDC"


def test_parse_power_24vdc() -> None:
    assert _parse_power("24VDC") == "24VDC"


def test_parse_power_wiegand() -> None:
    assert _parse_power("Wiegand-power") == "WIEGAND-POWER"


def test_parse_power_dash_is_none() -> None:
    assert _parse_power("-") is None
    assert _parse_power("N/A") is None


def test_parse_connection_cat6() -> None:
    assert _parse_connection("Cat6") == "CAT6"
    assert _parse_connection("Cat 6") == "CAT6"


def test_parse_connection_rs485() -> None:
    assert _parse_connection("RS-485") == "RS-485"
    assert _parse_connection("RS485") == "RS-485"


def test_parse_connection_wiegand() -> None:
    assert _parse_connection("Wiegand") == "WIEGAND"


def test_parse_quantity() -> None:
    assert _parse_quantity("3") == 3
    assert _parse_quantity("12 EA") == 12
    assert _parse_quantity("abc") is None


def test_parse_mounting() -> None:
    assert _parse_mounting("WALL") == "WALL"
    assert _parse_mounting("CEILING") == "CEILING"
    assert _parse_mounting("DOOR FRAME") == "DOOR_FRAME"


# ---------------------------------------------------------------------------
# Header collision (TWO-PASS picker)
# ---------------------------------------------------------------------------


def test_header_collision_d_vs_description_vs_door() -> None:
    """``D`` short form does not steal ``DESCRIPTION`` / ``DOOR`` long forms."""
    headers = ["TAG", "DESCRIPTION", "DOOR", "D"]
    idx = _security_indices(headers)
    assert idx["desc"] == 1


def test_header_collision_c_vs_connection_vs_cable() -> None:
    """``C`` short form does not steal CONNECTION / CABLE long form."""
    headers = ["TAG", "DESCRIPTION", "CONNECTION", "C"]
    idx = _security_indices(headers)
    assert idx["connection"] == 2


def test_header_collision_c_vs_cable() -> None:
    """``CABLE`` long form claims the connection slot."""
    headers = ["TAG", "DESCRIPTION", "CABLE", "C"]
    idx = _security_indices(headers)
    assert idx["connection"] == 2


def test_header_collision_m_vs_model_vs_mounting() -> None:
    """``M`` short form does not collide with MODEL / MOUNTING long forms."""
    headers = ["TAG", "MODEL", "MOUNTING", "M"]
    idx = _security_indices(headers)
    assert idx["model"] == 1
    assert idx["mounting"] == 2


def test_header_collision_p_vs_power() -> None:
    """``P`` short form does not steal POWER long form."""
    headers = ["TAG", "DESCRIPTION", "POWER", "P"]
    idx = _security_indices(headers)
    assert idx["power"] == 2


def test_header_collision_q_vs_quantity() -> None:
    """``Q`` short form does not steal QUANTITY / QTY long form."""
    headers = ["TAG", "DESCRIPTION", "QUANTITY", "Q"]
    idx = _security_indices(headers)
    assert idx["qty"] == 2


def test_short_forms_picked_when_long_absent() -> None:
    """When only short forms are present, they claim their roles."""
    headers = ["TAG", "D", "M", "P", "C", "Q"]
    idx = _security_indices(headers)
    assert idx["desc"] == 1
    assert idx["mounting"] == 2
    assert idx["power"] == 3
    assert idx["connection"] == 4
    assert idx["qty"] == 5


# ---------------------------------------------------------------------------
# Header heuristic
# ---------------------------------------------------------------------------


def test_looks_like_security_header_positive() -> None:
    assert _looks_like_security_header(
        ["TAG", "DESCRIPTION", "READER", "POWER"]
    ) is True


def test_looks_like_security_header_rejects_door_hardware() -> None:
    """Pure door hardware schedule headers must be rejected."""
    assert _looks_like_security_header(
        ["MARK", "HARDWARE", "OPERATION", "RATING"]
    ) is False


def test_looks_like_security_header_rejects_av() -> None:
    assert _looks_like_security_header(
        ["TAG", "DESCRIPTION", "DISPLAY", "RESOLUTION", "SIGNAL"]
    ) is False


def test_looks_like_security_header_rejects_lighting() -> None:
    assert _looks_like_security_header(
        ["TAG", "DESCRIPTION", "WATTS", "LUMENS"]
    ) is False


# ---------------------------------------------------------------------------
# Full table parse
# ---------------------------------------------------------------------------


def test_extract_single_card_reader(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "single_cr.pdf",
        title_lines=["SECURITY SCHEDULE"],
        table=[
            ["TAG",  "DESCRIPTION",  "MFR",         "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["DR-1", "Card reader",  "HID",         "WALL",     "PoE",   "Wiegand",    "4"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    d = result.devices[0]
    assert d.tag == "DR-1"
    assert d.item_type == "CARD_READER"
    assert d.manufacturer == "HID"
    assert d.mounting == "WALL"
    assert d.power == "POE"
    assert d.connection == "WIEGAND"
    assert d.quantity == 4


def test_extract_multi_device(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "multi_sec.pdf",
        title_lines=["SECURITY DEVICE SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",     "MFR",   "MOUNTING",   "POWER", "CONNECTION", "QTY"],
            ["DR-1",  "Card reader",     "HID",   "WALL",       "PoE",   "Wiegand",    "4"],
            ["CAM-1", "Surveillance cam", "Axis", "CEILING",    "PoE",   "Cat6",       "8"],
            ["MS-1",  "Motion sensor",   "Bosch", "CEILING",    "12VDC", "RS-485",     "6"],
            ["ML-1",  "Maglock",         "HES",   "DOOR FRAME", "24VDC", "RS-485",     "2"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 4
    tags = [d.tag for d in result.devices]
    assert tags == ["DR-1", "CAM-1", "MS-1", "ML-1"]
    types = [d.item_type for d in result.devices]
    assert types == ["CARD_READER", "CAMERA", "MOTION_SENSOR", "MAGLOCK"]


def test_extract_cam_in_security_context(tmp_path: Path) -> None:
    """A ``CAM-`` row in a security-shaped schedule classifies as CAMERA."""
    pdf = _build_pdf(
        tmp_path, "sec_cam.pdf",
        title_lines=["CCTV SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "MFR",   "MOUNTING", "POWER", "CONNECTION"],
            ["CAM-1", "PTZ camera",  "Axis",  "CEILING",  "PoE",   "Cat6"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    assert result.devices[0].item_type == "CAMERA"


def test_extract_cam_rejected_in_av_context_via_description(tmp_path: Path) -> None:
    """A ``CAM-`` row with a conference-camera description gets pushed to
    ``OTHER`` so the AV extractor can claim it."""
    pdf = _build_pdf(
        tmp_path, "sec_cam_av_desc.pdf",
        title_lines=["SECURITY SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",       "MFR",  "MOUNTING", "POWER", "CONNECTION"],
            ["CAM-1", "Conference camera", "Logi", "WALL",     "USB",   "USB"],
        ],
    )
    result = _extract_one(pdf)
    if result.devices:
        assert result.devices[0].item_type == "OTHER"


def test_extract_quantity_aware(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "qty_aware.pdf",
        title_lines=["SECURITY SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",  "MOUNTING", "POWER", "CONNECTION", "QTY"],
            ["MS-1",  "Motion",       "CEILING",  "12VDC", "RS-485",     "12"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    assert result.devices[0].quantity == 12


def test_extract_no_quantity_column(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "no_qty.pdf",
        title_lines=["ACCESS CONTROL SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION", "MOUNTING", "POWER", "CONNECTION"],
            ["KP-1",  "Keypad",      "WALL",     "12VDC", "Wiegand"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    assert result.devices[0].quantity is None


# ---------------------------------------------------------------------------
# to_schema bridge
# ---------------------------------------------------------------------------


def test_to_schema_roundtrip() -> None:
    devices = [
        SecurityDeviceRecord(
            tag="DR-1", item_type="CARD_READER",
            description="Prox reader", manufacturer="HID",
            mounting="WALL", power="POE", connection="WIEGAND",
            quantity=2, confidence=0.9, source_page=3,
        ),
        SecurityDeviceRecord(
            tag="CAM-1", item_type="CAMERA",
            description="PTZ camera", manufacturer="Axis",
            mounting="CEILING", power="POE", connection="CAT6",
            quantity=4, confidence=0.85, source_page=3,
        ),
    ]
    internal = SecurityScheduleResult(
        pages=[3], devices=devices, confidence=0.9,
        raw_table_text="TAG | DESCRIPTION | MOUNTING | POWER | CONNECTION | QTY",
    )
    schema = to_schema(internal)
    assert schema.confidence == 0.9
    assert schema.pages == [3]
    assert len(schema.devices) == 2
    assert schema.devices[0].tag == "DR-1"
    assert schema.devices[0].item_type == "CARD_READER"
    assert schema.devices[0].connection == "WIEGAND"
    assert schema.devices[1].tag == "CAM-1"
    assert schema.devices[1].item_type == "CAMERA"
    assert schema.devices[1].connection == "CAT6"


# ---------------------------------------------------------------------------
# Empty result
# ---------------------------------------------------------------------------


def test_empty_result_when_no_security_table(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "empty.pdf",
        title_lines=["FLOOR PLAN — SHEET A1.0"],
    )
    result = _extract_one(pdf)
    assert result.devices == []
    assert result.confidence == 0.0
