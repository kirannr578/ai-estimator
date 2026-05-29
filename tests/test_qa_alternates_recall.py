"""T10 F-4 — bid-alternates extractor recall regression tests.

Closes the F-4 finding from the calibration v4 report at
``exports/calibration_v4/CALIBRATION_REPORT.md``: across the full 41-bundle
v4 corpus the alternates extractor surfaced **zero** alternates, including
on four strong RFCSP candidates that calibration flagged for manual
review:

* **Carr EFA RFCSP main** (`ESBD_516718_*_RFCSP.pdf`, 311 p — Angelo
  State University Texas-State CSP) — its specification page 42 lists
  three enumerated alternates under the CSI "01220 Schedule of
  Alternates" section header, all with placeholder descriptions of
  "N/A" because the architect deferred scoping. The deterministic
  regex already matches each line individually, but the section
  detector missed the "Schedule of Alternates" header so the page was
  never scanned end-to-end and the LLM-prompt didn't surface the rows.
* **Carr EFA Attachment A** (`ESBD_516718_*_Attachment A.pdf`, 4 p —
  Form of Proposal) — has the Base Proposal + a Schedule of Allowances
  block but **no enumerated alternates section**; this bundle should
  correctly emit zero alternates (it's the "expected-zero" / negative
  case for B2-1 hardening).
* **CHS Cafeteria RFCSP** (`ESBD_518571_*_RFCSP 2026-0608-01 CHS
  Cafeteria Serving Line Renovation.pdf`, 32 p — Cleburne ISD CSP) —
  has only narrative references to alternates ("Proposed Price
  including selected alternates, if applicable") and no enumerated
  alternates list; this bundle should correctly emit zero alternates
  AND the LLM-fallback predicate should fire so that the LLM gets to
  confirm there are no alternates.
* **PAIS Backcountry Cabin** (`Sol_140P6026Q0029.pdf`, 28 p — National
  Park Service federal RFQ) — its Price/Bid Schedule on page 5
  enumerates two alternates as **CLIN-Options under FAR 52.217-5**
  (``Option 001`` / ``Option 002``) without using the word
  "alternate" anywhere on the page. The deterministic regex missed
  this entirely until T10 F-4 added the dedicated CLIN-Option
  regex and section-detector heuristic.

Fixtures are text-only excerpts derived from the real PDFs; they preserve
the relevant header lines and the enumerated alternate rows so the
deterministic regex parser exercises the same code path that production
runs on the page-text the bundler hands it. **No LLM mocks** — the LLM
fallback predicate is asserted in isolation; the LLM call itself has
dedicated coverage in :mod:`tests.test_bid_form_alternates_extraction`.

The negative-class B2-1 false-positive guard remains pinned by
:mod:`tests.test_qa_alternates` (NEG-2) and is RE-pinned here on a
broader set of header / column-header tokens that T10 F-4 added to the
stopword list (PRICING, BID, PROPOSAL, OPTION, etc.) so future
extensions cannot regress the negative case.
"""

from __future__ import annotations

import pytest

from core.extraction.bid_form_alternates import (
    _is_valid_alternate_id_token,
    detect_alternates_section,
    extract_alternates_from_page,
    should_invoke_llm_fallback,
)
from core.schemas import AlternateType


# ---------------------------------------------------------------------------
# Fixture text — sanitized excerpts from the 4 calibration-v4 bundles
# ---------------------------------------------------------------------------
#
# Each fixture is a verbatim text-only excerpt from the relevant PDF page,
# captured via ``fitz.Page.get_text()`` then hand-trimmed to the parts that
# exercise the alternates extractor. No PII or vendor data is embedded —
# these are publicly-posted Texas-State and federal solicitations.


# ---------------------------------------------------------------------------
# Bundle 1 — Carr EFA RFCSP main (Angelo State University Texas-State CSP).
# Specification page 42 contains the "01220 Schedule of Alternates" CSI
# section with three placeholder-only alternate rows.
# ---------------------------------------------------------------------------

CARR_EFA_RFCSP_SCHEDULE_OF_ALTERNATES_PAGE = """\
Project Specifications
 CARR EFA DRESSING ROOM RENOVATION  FP&C #  26-007
RFCSP Page# 42


01220
Schedule of Alternates
Page 1 of 1
01220 Schedule of Alternates

(1 pages total)

IV.
DESCRIPTION OF REQUIREMENTS
Coordinate related work and modify or adjust adjacent work as required to
ensure that work affected by each accepted alternate is complete and fully
integrated into the project.
A "Schedule of Alternates" is included at the end of this section.
Specification sections referenced in the Schedule contain requirements for
materials and methods necessary to achieve the work described under each
alternate.
Include as part of each alternate, miscellaneous devices, appurtenances and
similar items incidental to or required for a complete installation whether
or not mentioned as part of the alternate.
V.
SCHEDULE OF ALTERNATES
Specification sections referenced in the Schedule contain requirements for
materials and methods necessary to achieve the work described under each
alternate. It is the responsibility of the Contractor, working with the
Design Professional to verify and ensure that, as part of each alternate,
miscellaneous devices, appurtenances and similar items incidental to or
required for a complete installation, whether or not mentioned on the
construction documents, are included in the delivery of each awarded
alternate(s).

Schedule of Alternates:
ALTERNATE NO. 1:  N/A
ALTERNATE NO. 2:  N/A
ALTERNATE NO. 3:  N/A

END OF SECTION
"""


# ---------------------------------------------------------------------------
# Bundle 2 — Carr EFA Attachment A "Form of Proposal" (Angelo State).
# This is the bid-form proposer-fills-in page. Has BASE PROPOSAL + a
# Schedule of Allowances block but NO enumerated alternates section.
# Expected-zero / negative case.
# ---------------------------------------------------------------------------

CARR_EFA_ATTACHMENT_A_FORM_OF_PROPOSAL = """\
Attachment A
FORM OF PROPOSAL
Tracie Howell
Director of Facilities Planning and Construction
ASU Station #10924
San Angelo, TX  76909

Subject:  Construction Services

Carr EFA Dressing Room Renovation, 26-007

Dear Financial Manager:

ADDENDA
We have received _______ Addenda prior to the submission of this Proposal.

HUB CONTRACTING COMMITMENT
... commits to use certified HUB Firms ... _______% of the Total Agreement
Amount.

TIME OF COMPLETION
______________________________consecutive calendar days

CONSTRUCTION SERVICES BASE PROPOSAL
We hereby propose to perform the Construction Services defined in the
aforementioned RFCSP for the amount listed below which includes all
applicable Federal, State, and Local taxes required for the performance and
completion of the work and any specified Allowances.

Figure (written out):  _______________________________________________ and ___/1.00 Dollars

Figure (numerical): $ ___________________________________________________________________________

ALLOWANCES
In accordance to Specification Section 01030 - Schedule of Allowances, the
following allowance is to be included in the Base Proposal:
Contract Allowance Number one (1): Include a cash/contingency allowance of
Twenty Five Thousand ($25,000.00 Dollars) for unforeseen scope of work.
Contractor shall not expend allowance without written authorization from
owner.

LIQUIDATED DAMAGES:
For each consecutive calendar day after the date at which the Parties have
contracted for Substantial Completion that Substantial Completion is not
accomplished, taking into consideration any extensions of time granted by
any Change Order, Contractor shall pay to ASU $250.00.

CERTIFICATIONS AND AFFIRMATIONS
Signing this proposal with a false statement is a material breach of
Contract.
"""


# ---------------------------------------------------------------------------
# Bundle 3 — CHS Cafeteria Serving Line Renovation RFCSP (Cleburne ISD).
# Page 14 contains the evaluation-criteria language ("Proposed Price
# including selected alternates, if applicable") — a *narrative*
# reference to alternates with no enumerated rows. Expected-zero from
# the deterministic parser; the LLM-fallback predicate SHOULD still
# fire because the page does contain "alternates" wording (the LLM is
# the one that decides whether there's a structured list present).
# ---------------------------------------------------------------------------

CHS_CAFETERIA_RFCSP_META_ALTERNATES_PAGE = """\
2
1
EVALUATION CRITERIA AND PROCEDURE
Proposals may be evaluated by an Evaluation Committee comprised of key
Cleburne ISD personnel in order to fairly evaluate all qualified proposals.
1. Proposed Price (including selected alternates, if applicable), 50 Points.
Lowest Price divided by Proposers Price > Multiply by 100 > Multiply by .5
(weight of Price Evaluation)
Pricing shall reflect all work within the defined project window from June
15, 2026 through August 3, 2026, and shall not contain exclusions or
qualifications that would render the total cost incomplete or unreliable
for purposes of comparison and best value determination.
2. Quality of Good and Services, 25 Points
3. Warranty Work, 10 Points
4. Project Experience, 10 Points
5. Reputation, 5 Points
6. Required forms completed and submitted (PASS/FAIL).
"""


# ---------------------------------------------------------------------------
# Bundle 4 — PAIS Backcountry Cabin (NPS federal SF18 RFQ). Page 5's
# "Price/Bid Schedule" enumerates three base CLINs (001 / 002 / 003)
# followed by TWO evaluation-options under FAR 52.217-5 named
# ``Option 001`` and ``Option 002`` — these are alternates by another
# name. Pre-T10-F-4 the regex missed both because the prefix
# alternation didn't include "option" and the section detector didn't
# fire on a page that lacks the word "alternate".
# ---------------------------------------------------------------------------

PAIS_CABIN_CLIN_OPTIONS_PAGE = """\
140P6026Q0029
 PAIS - Cabin Security and Improvements
Page 5 of 28
Part I - The Schedule
SECTION A - Solicitation/Contract Form
This solicitation is a Request for Quote (RFQ), in accordance with the
Specifications/Drawings and is issued on Standard Form (SF) SF18.
Special Notice for Contractors Submitting Quotes
SECTION B - Price/Bid Schedule
Quote pricing shall be provided in accordance with Section L and is
incorporated herein.
CLIN
DESCRIPTION
QUANTITY
UNIT PRICE
TOTAL
001
Repair Doors & Install Reinforcement
3
$
$
002
Repair Roof Leak (Marine-grade shingles, sealant, labor)
Lump Sum
$
$
003
Install CAT5 TDI Hurricane Bahama Shutters and Installation Labor for
Shutters
10 Units
$
$
Option 001
Construct Cabin Ramp Extension
Lump Sum
$
$
Option 002
Construct Breakaway Sand Control
Lump Sum
$
$
TOTAL:
$
SECTION C - Specifications/Drawings
Project work consists of, but is not limited to, the procurement and
improve physical security.
"""


# ---------------------------------------------------------------------------
# F-4 recall regression — per-bundle assertions
# ---------------------------------------------------------------------------


class TestF4RecallFromCalibrationV4:
    """One assertion class per bundle named in calibration-v4 finding F-4."""

    def test_carr_efa_rfcsp_extracts_three_na_alternates(self) -> None:
        """Bundle 1 — Carr EFA RFCSP main, page 42 (Schedule of Alternates).

        Pins recall on the Texas-State CSP layout where alternates are
        enumerated under the CSI "01220 Schedule of Alternates" section
        header with placeholder descriptions of "N/A". The
        deterministic regex matches each ``ALTERNATE NO. n:  N/A`` line
        individually; T10 F-4 extends ``_SECTION_KEYWORDS`` so the page
        is also recognised as an alternates section by
        :func:`detect_alternates_section` (it wasn't before because the
        page header is "Schedule of Alternates" rather than "BID
        ALTERNATES").
        """
        page = CARR_EFA_RFCSP_SCHEDULE_OF_ALTERNATES_PAGE
        # Section detection picks up the "Schedule of Alternates" CSI label.
        assert detect_alternates_section(page) is True
        alts = extract_alternates_from_page(page)
        # All three enumerated alternates are emitted, even though the
        # description is the placeholder "N/A". Downstream the queue
        # surfaces them as operator-review items.
        assert len(alts) == 3, [a.alternate_id for a in alts]
        ids = sorted(a.alternate_id for a in alts)
        assert ids == ["Alternate 1", "Alternate 2", "Alternate 3"]
        for alt in alts:
            assert alt.alternate_type == AlternateType.ADDITIVE
            assert alt.description == "N/A"
            # No printed dollar amount — the form is fillable.
            assert alt.cost_delta is None

    def test_carr_efa_attachment_a_correctly_emits_zero_alternates(self) -> None:
        """Bundle 2 — Carr EFA Attachment A (Form of Proposal).

        The Form of Proposal has BASE PROPOSAL + ALLOWANCES blocks but
        NO enumerated alternates section. The deterministic regex must
        emit zero alternates AND the LLM-fallback predicate must
        return False (no section detected) so the caller doesn't burn
        an LLM call on a page that doesn't carry alternates wording.
        """
        page = CARR_EFA_ATTACHMENT_A_FORM_OF_PROPOSAL
        # No "alternate" keyword anywhere on the form.
        assert detect_alternates_section(page) is False
        alts = extract_alternates_from_page(page)
        assert alts == []
        # And the predicate refuses to suggest LLM fallback for the
        # Form of Proposal — there's nothing alternates-shaped here.
        assert should_invoke_llm_fallback(page, alts) is False

    def test_chs_cafeteria_meta_reference_invokes_llm_but_no_phantoms(
        self,
    ) -> None:
        """Bundle 3 — CHS Cafeteria RFCSP, evaluation-criteria page.

        The page mentions "selected alternates" in narrative context
        only (no enumerated rows). The deterministic regex correctly
        returns zero, and the LLM-fallback predicate fires because the
        page does mention alternates wording — that's the right place
        for the LLM to make the final no-alternates call. **No phantom
        alternates** must be synthesised from the meta-reference
        wording (B2-1 false-positive guard, broadened in T10 F-4).
        """
        page = CHS_CAFETERIA_RFCSP_META_ALTERNATES_PAGE
        # Detection fires on the "alternates" substring in the
        # evaluation-criteria sentence.
        assert detect_alternates_section(page) is True
        # But the line-level regex finds nothing structured to parse.
        alts = extract_alternates_from_page(page)
        assert alts == []
        # LLM fallback is the right next step; it lets the model
        # confirm there really is no enumerated list.
        assert should_invoke_llm_fallback(page, alts) is True

    def test_pais_cabin_extracts_two_clin_options_as_alternates(self) -> None:
        """Bundle 4 — PAIS Cabin federal RFQ, Price/Bid Schedule page 5.

        The federal SF18 form enumerates two evaluation-options under
        FAR 52.217-5 as ``Option 001`` and ``Option 002`` rows in the
        Price/Bid Schedule. T10 F-4 adds:

        * ``_CLIN_OPTION_LINE_RE`` — a dedicated regex that matches
          ``Option <digit>`` rows (digit-required to avoid false
          matches on narrative phrases like "Option to extend").
        * ``_SECTION_REGEXES`` — a section-detector regex
          (``\\boption\\s+(?:no\\.?\\s*)?\\d``) so the page is
          recognised as an alternates section even though the word
          "alternate" never appears.
        * ``_normalize_alternate_id`` — preserves the "Option" family
          in the id (so "Option 001" and "Alternate 1" do not collide
          when both happen to appear on adjacent pages).
        """
        page = PAIS_CABIN_CLIN_OPTIONS_PAGE
        # Even though "alternate" is absent, the CLIN-Option regex
        # picks the page up.
        assert detect_alternates_section(page) is True
        alts = extract_alternates_from_page(page)
        assert len(alts) == 2, [a.alternate_id for a in alts]
        ids = sorted(a.alternate_id for a in alts)
        assert ids == ["Option 001", "Option 002"]
        # FAR 52.217-5 evaluation-options are ADDITIVE by default —
        # the Government adds them at award discretion.
        for alt in alts:
            assert alt.alternate_type == AlternateType.ADDITIVE
            # Descriptions are folded from the continuation lines that
            # followed each "Option NNN" header.
            assert alt.description, f"empty description on {alt.alternate_id}"
        opt1 = next(a for a in alts if a.alternate_id == "Option 001")
        assert "cabin ramp extension" in opt1.description.lower()
        opt2 = next(a for a in alts if a.alternate_id == "Option 002")
        assert "breakaway sand control" in opt2.description.lower()
        # Form is fillable — no printed dollar amounts.
        assert all(a.cost_delta is None for a in alts)


# ---------------------------------------------------------------------------
# B2-1 false-positive guard — re-pinned over the broader stopword set
# ---------------------------------------------------------------------------
#
# These cases each *would* match the prefix alternation in ``_ALT_LINE_RE``
# but the next token is a header / column-header fragment that the
# ``_ALT_ID_HEADER_STOPWORDS`` set rejects. The guard prevents the
# extractor from synthesising a phantom "Alternate SECTION" /
# "Alternate PRICING" / etc. record.


@pytest.mark.parametrize(
    "header_line",
    [
        "BID ALTERNATES SECTION",
        "BID ALTERNATE SCHEDULE",
        "BID ALTERNATES PRICING",
        "BID ALTERNATES TABLE",
        "BID ALTERNATES LIST",
        "ALTERNATE BIDS",
        "ALTERNATE BID",
        "ALTERNATE PROPOSALS",
        "ALTERNATIVE PRICING",
        "ALTERNATE OPTIONS",
        "ALTERNATE ITEM AMOUNT",
        "ALTERNATE FORM",
        "ALTERNATE PAGE",
        "ALTERNATIVE BIDDER",
        "ALTERNATIVE OFFEROR",
    ],
)
def test_b21_false_positive_header_alone_does_not_emit_alternate(
    header_line: str,
) -> None:
    """B2-1 negative-class regression — re-pinned in T10 F-4.

    The literal section-header / column-header line by itself must NOT
    synthesise a phantom alternate. Each parametrised value is the
    exact line that would otherwise pass through the prefix regex and
    capture a header-fragment token (SECTION, PRICING, BID, OPTIONS,
    etc.) as the alternate's id. The stopword guard rejects each.
    """
    alts = extract_alternates_from_page(header_line)
    assert alts == [], (
        f"phantom alternate emitted from header-only line {header_line!r}: "
        f"{[a.alternate_id for a in alts]}"
    )


# ---------------------------------------------------------------------------
# Positive-class id-validator coverage — letter-only / digit / mixed ids
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "raw_id, expected",
    [
        # Single-letter ids (common on Texas-State / federal bid forms).
        ("A", True),
        ("B", True),
        ("Z", True),
        # Digit-containing ids — always accepted.
        ("1", True),
        ("01", True),
        ("001", True),
        ("999", True),
        ("VE-3", True),
        ("1A", True),
        ("VE-1.2", True),
        # Multi-letter alphabetic ids that are NOT header fragments.
        ("ONE", True),
        ("TWO", True),
        ("ALPHA", True),
        ("BETA", True),
        # Header / column-header fragments — must be rejected.
        ("SECTION", False),
        ("SCHEDULE", False),
        ("FORM", False),
        ("PAGE", False),
        ("ITEM", False),
        ("ITEMS", False),
        ("ALTERNATE", False),
        ("ALTERNATES", False),
        # T10 F-4 stopword additions.
        ("ALTERNATIVE", False),
        ("ALTERNATIVES", False),
        ("PRICING", False),
        ("PRICE", False),
        ("PROPOSAL", False),
        ("PROPOSALS", False),
        ("BID", False),
        ("BIDS", False),
        ("TABLE", False),
        ("LIST", False),
        ("OPTION", False),
        ("OPTIONS", False),
        ("DESCRIPTION", False),
        ("AMOUNT", False),
        ("TOTAL", False),
        ("QUANTITY", False),
        ("UNIT", False),
        ("BIDDER", False),
        ("OFFEROR", False),
        # Pathological empties — must be rejected.
        ("", False),
        ("   ", False),
    ],
)
def test_alternate_id_validator_accepts_letter_only_ids_and_rejects_headers(
    raw_id: str, expected: bool
) -> None:
    """Positive + negative parametric coverage on the id validator.

    Pins that letter-only ids ("Alt A" / "Alternate ONE") still pass
    while every header / column-header fragment the T10 F-4 calibration
    surfaced is rejected. Failure on either side is a regression of
    the B2-1 fix (negatives) or of the recall fix (positives).
    """
    assert _is_valid_alternate_id_token(raw_id) is expected


# ---------------------------------------------------------------------------
# Positive end-to-end: letter-only-id alternates emit correctly
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "page_text, expected_count, expected_id_substr",
    [
        ("Alternate A: Replace VCT with LVT — $2,000", 1, "A"),
        ("Alternate B: Add roof ladder — $1,500", 1, "B"),
        ("Bid Alternate A: Substitute LVT in corridors. $2,300", 1, "A"),
        ("Add Alt 1: Provide additional epoxy — $1,250", 1, "1"),
        ("ALT-A: Optional skylight package $5,000", 1, "A"),
        ("Alternate One: Provide rooftop screening $4,000", 1, "ONE"),
        ("Option 001: Construct Cabin Ramp Extension $7,500", 1, "001"),
        ("Option No. 5: Construct Breakaway Sand Control $3,500", 1, "5"),
    ],
)
def test_letter_and_clin_option_ids_extract_correctly(
    page_text: str, expected_count: int, expected_id_substr: str
) -> None:
    """Positive parametric — each canonical id shape resolves into exactly
    one extracted alternate carrying the printed id token."""
    alts = extract_alternates_from_page(page_text)
    assert len(alts) == expected_count, (
        f"expected {expected_count} alternate(s) from "
        f"{page_text!r}, got {[a.alternate_id for a in alts]}"
    )
    assert expected_id_substr in alts[0].alternate_id.upper()


# ---------------------------------------------------------------------------
# Section-detector coverage on header variants surfaced in calibration v4
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "header",
    [
        "Schedule of Alternates",                    # CSI 01220 / TTUS RFCSP
        "SCHEDULE OF ALTERNATES",                    # uppercase variant
        "Section 01 23 00 - Alternates",             # CSI section reference
        "01 22 00 - Alternates",                     # alternate CSI numbering
        "Alternate Pricing",                         # column-style header
        "Alternative Bids",                          # municipal CSP variant
        "Alternate Proposal",                        # narrative-style header
        "Voluntary Alternates",                      # federal VE-style header
        "Option 001",                                # CLIN-Option pattern
        "Option No. 1",                              # explicit "No." form
        "CLIN Option 1",                             # explicit CLIN prefix
    ],
)
def test_detect_alternates_section_covers_t10_f4_header_variants(
    header: str,
) -> None:
    """Pin: each new section-header / CLIN-Option variant the T10 F-4
    fix added (in ``_SECTION_KEYWORDS`` or ``_SECTION_REGEXES``) is
    actually recognised by :func:`detect_alternates_section`."""
    assert detect_alternates_section(header) is True, (
        f"detect_alternates_section() missed header variant: {header!r}"
    )


def test_detect_alternates_section_does_not_fire_on_narrative_option_phrase(
    self_unused=None,  # keep param-less parametrize-friendly
) -> None:
    """Negative pin for the CLIN-Option regex: a narrative phrase like
    ``"option to extend the contract"`` must NOT trigger detection.
    Only ``option`` immediately followed by a digit is recognised."""
    narrative = (
        "The Government has the option to extend the contract for an "
        "additional one-year period under FAR 52.217-9 if mutually "
        "agreed. This Option to renew may be exercised at the sole "
        "discretion of the Contracting Officer."
    )
    assert detect_alternates_section(narrative) is False
