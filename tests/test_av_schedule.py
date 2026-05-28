"""Tests for the Phase T2.11 AV / IT equipment schedule extractor.

Builds synthetic PDFs against ``extract_av_schedule_from_page`` plus
a handful of unit-level tests against the cell / header parsers.
Mirrors :mod:`tests.test_kitchen_schedule` for the AV family.
"""

from __future__ import annotations

from pathlib import Path

import fitz

from core.extraction.av_schedule import (
    AVDeviceRecord,
    AVScheduleResult,
    _av_indices,
    _classify_item_type,
    _looks_like_av_header,
    _parse_mounting,
    _parse_power,
    _parse_quantity,
    _parse_resolution,
    _parse_signal,
    _parse_wattage,
    detect_av_schedule_page,
    extract_av_schedule_from_page,
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


def _extract_one(pdf: Path) -> AVScheduleResult:
    with fitz.open(pdf) as d:
        return extract_av_schedule_from_page(d[0], 0)


# ---------------------------------------------------------------------------
# Page detection
# ---------------------------------------------------------------------------


def test_detect_page_with_av_schedule_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_av.pdf",
        title_lines=["AV SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION",    "MFR",      "SIZE",  "MOUNTING", "SIGNAL", "QTY"],
            ["DISP-1", "LCD Display",    "Samsung",  "75\"",  "WALL",     "HDMI",   "2"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is True


def test_detect_page_with_audio_visual_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_av_audio_visual.pdf",
        title_lines=["AUDIO VISUAL SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",    "DESCRIPTION",   "RESOLUTION", "POWER", "SIGNAL"],
            ["PROJ-1", "4K Projector",  "4K",         "120V",  "HDMI"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is True


def test_detect_page_with_av_equipment_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_av_eq.pdf",
        title_lines=["AV EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",   "MOUNTING", "SIGNAL"],
            ["MIC-1", "Ceiling mic",   "CEILING",  "USB"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is True


def test_detect_page_with_video_conferencing_phrase(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_av_vc.pdf",
        title_lines=["VIDEO CONFERENCING SCHEDULE", "Sheet T2.0"],
        table=[
            ["TAG",   "DESCRIPTION",    "RESOLUTION", "MOUNTING", "SIGNAL"],
            ["CAM-1", "Conference cam", "1080p",      "WALL",     "USB"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is True


def test_detect_rejects_security_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_security.pdf",
        title_lines=["SECURITY SCHEDULE", "Sheet S1.0"],
        table=[
            ["TAG",  "DESCRIPTION",  "MOUNTING", "POWER",  "CONNECTION"],
            ["DR-1", "Card reader",  "WALL",     "PoE",    "Cat6"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is False


def test_detect_rejects_lighting_schedule(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "detect_reject_lighting.pdf",
        title_lines=["LIGHTING FIXTURE SCHEDULE"],
        table=[
            ["TAG", "DESCRIPTION",  "WATTS", "LUMENS"],
            ["A1",  "LED troffer",  "40",    "4000"],
        ],
    )
    with fitz.open(pdf) as d:
        assert detect_av_schedule_page(d[0]) is False


# ---------------------------------------------------------------------------
# Item-type classifier
# ---------------------------------------------------------------------------


def test_classify_display_prefix() -> None:
    assert _classify_item_type("DISP-1") == "DISPLAY"
    assert _classify_item_type("DSP-2") == "DISPLAY"


def test_classify_projector_prefix() -> None:
    assert _classify_item_type("PROJ-1") == "PROJECTOR"
    assert _classify_item_type("PJ-2") == "PROJECTOR"


def test_classify_microphone_prefix() -> None:
    assert _classify_item_type("MIC-1") == "MICROPHONE"


def test_classify_speaker_prefix() -> None:
    assert _classify_item_type("SPK-1") == "SPEAKER"
    assert _classify_item_type("SP-2") == "SPEAKER"


def test_classify_rack_prefix() -> None:
    assert _classify_item_type("RACK-1") == "RACK"
    assert _classify_item_type("EQR-2") == "RACK"


def test_classify_control_prefix() -> None:
    assert _classify_item_type("CTRL-1") == "CONTROL_PROCESSOR"


def test_classify_network_switch_prefix() -> None:
    assert _classify_item_type("SW-1") == "NETWORK_SWITCH"


def test_classify_camera_av_context() -> None:
    # Bare CAM- prefix, no security keyword → classified as AV CAMERA.
    assert _classify_item_type("CAM-1", "Conference camera") == "CAMERA"
    assert _classify_item_type("CAM-1", "Lecture capture camera") == "CAMERA"
    assert _classify_item_type("CAM-1", "Huddle room webcam") == "CAMERA"


def test_classify_camera_rejected_when_security_context() -> None:
    # CAM- prefix with surveillance keyword → REJECTED to OTHER so
    # the AV synthesis does not claim a surveillance camera.
    assert _classify_item_type("CAM-1", "PTZ surveillance camera") == "OTHER"
    assert _classify_item_type("CAM-1", "CCTV dome camera") == "OTHER"
    assert _classify_item_type("CAM-1", "Fixed dome surveillance") == "OTHER"


def test_classify_unknown_prefix() -> None:
    assert _classify_item_type("ZZ-9") == "OTHER"


def test_classify_from_description_only() -> None:
    assert _classify_item_type("X", "LCD monitor") == "DISPLAY"
    assert _classify_item_type("X", "Loudspeaker pendant") == "SPEAKER"


# ---------------------------------------------------------------------------
# Cell parsers
# ---------------------------------------------------------------------------


def test_parse_resolution_4k() -> None:
    assert _parse_resolution("4K") == "4K"
    assert _parse_resolution("UHD") == "UHD"


def test_parse_resolution_1080p() -> None:
    assert _parse_resolution("1080p") == "1080P"


def test_parse_resolution_inches() -> None:
    assert _parse_resolution('75"') == '75"'
    assert _parse_resolution("85 inch") == "85INCH"


def test_parse_resolution_bare_diagonal() -> None:
    assert _parse_resolution("75") == '75"'


def test_parse_resolution_dash_is_none() -> None:
    assert _parse_resolution("-") is None
    assert _parse_resolution("N/A") is None


def test_parse_wattage_with_unit() -> None:
    assert _parse_wattage("40W") == 40.0
    assert _parse_wattage("40 W") == 40.0


def test_parse_wattage_plain_number() -> None:
    assert _parse_wattage("40") == 40.0
    assert _parse_wattage("12.5") == 12.5


def test_parse_power_120v() -> None:
    assert _parse_power("120V") == "120V"
    assert _parse_power("120 V") == "120V"


def test_parse_power_poe() -> None:
    assert _parse_power("PoE") == "POE"
    assert _parse_power("PoE+") == "POE+"


def test_parse_power_12vdc() -> None:
    assert _parse_power("12VDC") == "12VDC"


def test_parse_power_usb_c() -> None:
    assert _parse_power("USB-C") == "USB-C"


def test_parse_signal_hdmi() -> None:
    assert _parse_signal("HDMI") == "HDMI"


def test_parse_signal_sdi() -> None:
    assert _parse_signal("SDI") == "SDI"


def test_parse_signal_ip() -> None:
    assert _parse_signal("IP") == "IP"


def test_parse_signal_usb() -> None:
    assert _parse_signal("USB-C") == "USBC"


def test_parse_signal_displayport() -> None:
    assert _parse_signal("DisplayPort") == "DISPLAYPORT"


def test_parse_quantity() -> None:
    assert _parse_quantity("3") == 3
    assert _parse_quantity("12 EA") == 12
    assert _parse_quantity("abc") is None


def test_parse_mounting() -> None:
    assert _parse_mounting("WALL") == "WALL"
    assert _parse_mounting("CEILING") == "CEILING"
    assert _parse_mounting("RACK") == "RACK"


# ---------------------------------------------------------------------------
# Header collision (TWO-PASS picker)
# ---------------------------------------------------------------------------


def test_header_collision_d_vs_description() -> None:
    """``D`` short-form must not steal the ``DESCRIPTION`` long-form slot."""
    headers = ["TAG", "DESCRIPTION", "D", "MOUNTING"]
    idx = _av_indices(headers)
    # Long form claimed first; short ``D`` ends up unmapped against desc.
    assert idx["desc"] == 1


def test_header_collision_d_vs_display_vs_description() -> None:
    """Multiple D-collision sources resolve correctly via two-pass."""
    headers = ["TAG", "DESCRIPTION", "MFR", "MODEL", "DISPLAY", "D"]
    idx = _av_indices(headers)
    assert idx["desc"] == 1


def test_header_collision_m_vs_model_vs_mounting() -> None:
    """``M`` short form does not collide with MODEL or MOUNTING long forms."""
    headers = ["TAG", "MODEL", "MOUNTING", "M"]
    idx = _av_indices(headers)
    assert idx["model"] == 1
    assert idx["mounting"] == 2


def test_header_collision_p_vs_power_vs_projector() -> None:
    """``P`` short form does not steal POWER long form."""
    headers = ["TAG", "DESCRIPTION", "POWER", "P"]
    idx = _av_indices(headers)
    assert idx["power"] == 2


def test_header_collision_s_vs_signal_vs_size() -> None:
    """``S`` short form does not steal SIGNAL / SIZE long form."""
    headers = ["TAG", "SIZE", "SIGNAL", "S"]
    idx = _av_indices(headers)
    assert idx["size"] == 1
    assert idx["signal"] == 2


def test_header_collision_w_vs_wattage() -> None:
    """``W`` short form does not steal WATTAGE long form."""
    headers = ["TAG", "DESCRIPTION", "WATTAGE", "W"]
    idx = _av_indices(headers)
    assert idx["wattage"] == 2


def test_header_collision_q_vs_quantity() -> None:
    """``Q`` short form does not steal QUANTITY / QTY long form."""
    headers = ["TAG", "DESCRIPTION", "QUANTITY", "Q"]
    idx = _av_indices(headers)
    assert idx["qty"] == 2


def test_short_forms_picked_when_long_absent() -> None:
    """When only short forms are present, they claim their roles."""
    headers = ["TAG", "D", "M", "P", "S", "W", "Q"]
    idx = _av_indices(headers)
    assert idx["desc"] == 1
    assert idx["mounting"] == 2
    assert idx["power"] == 3
    assert idx["signal"] == 4
    assert idx["wattage"] == 5
    assert idx["qty"] == 6


# ---------------------------------------------------------------------------
# Full table parse
# ---------------------------------------------------------------------------


def test_extract_single_display(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "single_display.pdf",
        title_lines=["AV SCHEDULE"],
        table=[
            ["TAG",    "DESCRIPTION",  "MFR",       "SIZE",  "MOUNTING", "POWER", "QTY"],
            ["DISP-1", "LCD Display",  "Samsung",   "75\"",  "WALL",     "120V",  "2"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    d = result.devices[0]
    assert d.tag == "DISP-1"
    assert d.item_type == "DISPLAY"
    assert d.manufacturer == "Samsung"
    assert d.size_or_resolution == '75"'
    assert d.mounting == "WALL"
    assert d.power == "120V"
    assert d.quantity == 2


def test_extract_multi_device(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "multi_av.pdf",
        title_lines=["AV EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",    "DESCRIPTION",   "MFR",        "RESOLUTION", "MOUNTING", "POWER",  "SIGNAL", "QTY"],
            ["DISP-1", "Display",       "Samsung",    "4K",         "WALL",     "120V",   "HDMI",   "2"],
            ["PROJ-1", "Projector",     "Epson",      "1080p",      "CEILING",  "120V",   "HDMI",   "1"],
            ["MIC-1",  "Ceiling mic",   "Shure",      "",           "CEILING",  "PoE",    "USB",    "4"],
            ["SPK-1",  "Loudspeaker",   "JBL",        "",           "CEILING",  "12VDC",  "",       "8"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 4
    tags = [d.tag for d in result.devices]
    assert tags == ["DISP-1", "PROJ-1", "MIC-1", "SPK-1"]
    types = [d.item_type for d in result.devices]
    assert types == ["DISPLAY", "PROJECTOR", "MICROPHONE", "SPEAKER"]


def test_extract_control_and_switch(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "ctrl_sw.pdf",
        title_lines=["AV/IT SCHEDULE"],
        table=[
            ["TAG",    "DESCRIPTION",        "MFR",     "MOUNTING", "POWER", "SIGNAL"],
            ["CTRL-1", "Control processor",  "Crestron","RACK",     "120V",  "IP"],
            ["SW-1",   "PoE switch",         "Cisco",   "RACK",     "120V",  "IP"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 2
    assert result.devices[0].item_type == "CONTROL_PROCESSOR"
    assert result.devices[1].item_type == "NETWORK_SWITCH"


def test_extract_cam_av_context(tmp_path: Path) -> None:
    """CAM- in an AV schedule with conference keyword → AV CAMERA."""
    pdf = _build_pdf(
        tmp_path, "cam_av.pdf",
        title_lines=["VIDEO CONFERENCING SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",       "MFR",       "RESOLUTION", "POWER", "SIGNAL"],
            ["CAM-1", "Conference camera", "Logitech",  "1080p",      "PoE",   "IP"],
        ],
    )
    result = _extract_one(pdf)
    assert len(result.devices) == 1
    assert result.devices[0].item_type == "CAMERA"


def test_extract_cam_security_context_rejected(tmp_path: Path) -> None:
    """CAM- with surveillance keyword in description → OTHER (not AV CAMERA)."""
    pdf = _build_pdf(
        tmp_path, "cam_security.pdf",
        title_lines=["AV EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",   "DESCRIPTION",            "MFR",     "MOUNTING", "POWER", "SIGNAL"],
            ["CAM-1", "PTZ surveillance",       "Axis",    "CEILING",  "PoE",   "IP"],
        ],
    )
    result = _extract_one(pdf)
    # Detection still fires (AV header shape); classifier rejects.
    assert len(result.devices) == 1
    assert result.devices[0].item_type == "OTHER"


# ---------------------------------------------------------------------------
# to_schema round-trip
# ---------------------------------------------------------------------------


def test_to_schema_round_trip(tmp_path: Path) -> None:
    pdf = _build_pdf(
        tmp_path, "schema.pdf",
        title_lines=["AV EQUIPMENT SCHEDULE"],
        table=[
            ["TAG",    "DESCRIPTION",  "MFR",     "SIZE",  "MOUNTING", "POWER", "QTY"],
            ["DISP-1", "LCD Display",  "Samsung", "75\"",  "WALL",     "120V",  "3"],
        ],
    )
    dc_result = _extract_one(pdf)
    schema = to_schema(dc_result)
    assert schema.devices[0].tag == "DISP-1"
    assert schema.devices[0].item_type == "DISPLAY"
    assert schema.devices[0].manufacturer == "Samsung"
    assert schema.devices[0].size_or_resolution == '75"'
    assert schema.devices[0].quantity == 3


def test_empty_result_when_no_table(tmp_path: Path) -> None:
    pdf = _build_pdf(tmp_path, "empty.pdf",
                       title_lines=["AV SCHEDULE"])
    result = _extract_one(pdf)
    assert result.devices == []
    assert result.confidence == 0.0


# ---------------------------------------------------------------------------
# Header heuristic
# ---------------------------------------------------------------------------


def test_looks_like_av_header_positive() -> None:
    assert _looks_like_av_header(
        ["TAG", "DESCRIPTION", "MFR", "DISPLAY", "MOUNTING"]
    ) is True


def test_looks_like_av_header_rejects_security() -> None:
    """Headers carrying CCTV / WIEGAND tokens are NOT AV."""
    assert _looks_like_av_header(
        ["TAG", "DESCRIPTION", "WIEGAND", "MOUNTING"]
    ) is False


def test_looks_like_av_header_rejects_door() -> None:
    assert _looks_like_av_header(
        ["MARK", "HARDWARE", "FRAME"]
    ) is False
