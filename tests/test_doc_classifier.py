"""Regression tests for `core.pdf_processor._classify_document`.

The classifier is the gate that decides whether a PDF goes through the
text/bundle path (one LLM call per doc, ~$0.01) or the per-page sheet path
(one LLM call per page, ~35x cost amplifier on a typical solicitation).

Calibration v1 found 13/17 government RFPs in
`inbox/opportunities/attachments/2026-05-21/` were misrouted to the sheet
path because the original heuristics only knew about trade-specific
bid-package language (DISD/Beck style). These tests lock in the
government-RFP routing added afterwards so that a future tuning pass
cannot silently regress it.

Fixtures are inline string snippets so the suite stays fast and never
needs PyMuPDF or actual PDFs on disk.
"""

from __future__ import annotations

from core.pdf_processor import _classify_document
from core.schemas import SheetType


def _classify(name: str, text: str, page_count: int = 5) -> SheetType:
    """Run the classifier with avg-chars-per-page derived from the snippet,
    matching the real call site's first-3-pages-only sampling behaviour."""
    avg = len(text) / max(min(3, page_count), 1)
    return _classify_document(name, text, page_count, avg)


# --- legacy trade-specific bid packages must still classify correctly ------


def test_legacy_trade_bid_package_filename() -> None:
    """The DISD-style "NN.NN_-_Trade.pdf" filename pattern must still win."""
    assert _classify("03.00_-_Concrete.pdf", "boilerplate text", page_count=4) == SheetType.BID_PACKAGE


def test_legacy_bid_package_two_phrase_match() -> None:
    text = (
        "BID PACKAGE 03.00 - CONCRETE\n"
        "GENERAL INSTRUCTIONS TO BIDDERS\n"
        "SPECIFIC INCLUSIONS\n"
        "SPECIFIC EXCLUSIONS\n"
    )
    assert _classify("03_Concrete_no_dot.pdf", text) == SheetType.BID_PACKAGE


# --- government RFP / SAM.gov / TX-ESBD solicitations ----------------------


def test_sam_gov_sol_filename_routes_to_bundle() -> None:
    text = (
        "SOLICITATION NUMBER 140FC126R0017\n"
        "REQUEST FOR PROPOSALS\n"
        "STANDARD FORM 1442\n"
        "OFFEROR shall submit one (1) electronic copy.\n"
        "CONTRACTING OFFICER: Jane Doe.\n"
    )
    assert _classify("Sol_140FC126R0017.pdf", text, page_count=73) == SheetType.BID_PACKAGE


def test_esbd_rfcsp_routes_to_bundle() -> None:
    text = (
        "REQUEST FOR COMPETITIVE SEALED PROPOSAL\n"
        "RFCSP 26-007 Carr EFA Dressing Room Renovation\n"
        "ELECTRONIC STATE BUSINESS DAILY\n"
        "OFFERORS shall submit responses electronically.\n"
    )
    name = "ESBD_516718_1778880767322_26-007 Carr EFA Dressing Room Renocation RFCSP.pdf"
    assert _classify(name, text, page_count=311) == SheetType.BID_PACKAGE


def test_statement_of_work_routes_to_bundle() -> None:
    text = (
        "STATEMENT OF WORK\n"
        "Scope of Work for San Marcos ARC rehabilitation.\n"
        "Period of performance: 90 days from Notice to Proceed.\n"
    )
    name = "SOW_-_Final_-_San_Marcos_-_02192026_Word_r_1.pdf"
    assert _classify(name, text, page_count=17) == SheetType.BID_PACKAGE


def test_gov_rfp_body_text_alone_routes_to_bundle() -> None:
    """Even without a tell-tale filename, two government-RFP phrases is
    enough to route to BID_PACKAGE."""
    text = (
        "REQUEST FOR PROPOSALS\n"
        "Magnitude of Construction: between $500,000 and $1,000,000.\n"
        "SECTION L - Instructions to Offerors.\n"
        "SECTION M - Evaluation Factors.\n"
    )
    assert _classify("anonymous_solicitation.pdf", text, page_count=40) == SheetType.BID_PACKAGE


# --- supporting / boilerplate documents -> PROJECT_MANUAL ------------------


def test_davis_bacon_wage_determination_routes_to_manual() -> None:
    text = (
        "GENERAL DECISION TX20260254\n"
        "DAVIS-BACON WAGE DETERMINATION\n"
        "Hays County, Building Construction.\n"
    )
    name = "SAM_-_Davis-Bacon_Act_WD_TX20260254__Hays_County__Building.pdf"
    assert _classify(name, text, page_count=7) == SheetType.PROJECT_MANUAL


def test_solicitation_amendment_routes_to_manual_not_package() -> None:
    """`Sol_..._Amd_NNNN.pdf` shares the `Sol_` prefix with the parent
    solicitation but is an amendment, not the package itself. PROJECT_MANUAL
    routing must win."""
    text = "AMENDMENT TO SOLICITATION\nAmendment No. 0001"
    assert _classify("Sol_140P6026Q0029_Amd_0001.pdf", text, page_count=2) == SheetType.PROJECT_MANUAL


def test_uniform_general_conditions_routes_to_manual() -> None:
    text = (
        "UNIFORM GENERAL CONDITIONS for construction projects.\n"
        "Article 1: Definitions.\n"
    )
    name = "ESBD_516718_..._Attachment C - 2010 Uniform General Conditions and Supplementary General Conditions.pdf"
    assert _classify(name, text, page_count=109) == SheetType.PROJECT_MANUAL


def test_large_project_manual_above_old_30_page_cap() -> None:
    """The previous code capped PROJECT_MANUAL at 30 pages, which excluded
    every realistic government UGC / specifications exhibit. Confirm the
    lifted cap covers a 311-page manual."""
    # The body-text PROJECT_MANUAL rule requires avg_chars_per_page > 600,
    # so the fixture has to be reasonably dense (the real PyMuPDF text
    # extraction on a UGC exhibit produces ~2-4 kB/page).
    body = (
        "TABLE OF CONTENTS\nProject Requirements\nExhibit A — General Conditions.\n"
        + ("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 60)
    )
    assert _classify("big_exhibit_manual.pdf", body, page_count=311) == SheetType.PROJECT_MANUAL


# --- explicit bid forms ----------------------------------------------------


def test_bid_schedule_filename_routes_to_form() -> None:
    text = "BID SCHEDULE\nItem 1 ... Unit Price ... Quantity ..."
    name = "Bid_Schedule_San_Marcos_ARC__Rehabilitate_Shop___2_Stall_Garage_Build.pdf"
    assert _classify(name, text, page_count=1) == SheetType.BID_FORM


def test_hub_subcontracting_plan_routes_to_form() -> None:
    text = "HUB SUBCONTRACTING PLAN"
    name = "ESBD_516718_..._Attachment D - HSP (Historically Underutilized Businesses).pdf"
    assert _classify(name, text, page_count=9) == SheetType.BID_FORM


# --- drawing-set veto ------------------------------------------------------


def test_drawing_filename_overrides_solicitation_text() -> None:
    """A doc named '...Drawings.pdf' must fall through to per-page sheets
    even when the body has solicitation language (parent procurement is a
    solicitation; the doc itself is the drawing set)."""
    text = "SOLICITATION NUMBER B08-XYZ\nRequest for Proposals - drawing set attached."
    name = "B08_Solicitation_-_Att_2_-_Drawings.pdf"
    assert _classify(name, text, page_count=24) == SheetType.UNKNOWN


def test_drawing_titleblock_text_routes_to_sheet_path() -> None:
    """A pure architectural title-block snippet with no RFP language and a
    drawing-style filename should not be hijacked into bundle routing."""
    text = "A-101  FIRST FLOOR PLAN\n1/4\" = 1'-0\"\nSheet 1 of 24"
    assert _classify("A-101_floor_plan.pdf", text, page_count=24) == SheetType.UNKNOWN
