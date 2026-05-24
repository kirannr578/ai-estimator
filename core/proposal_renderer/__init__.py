"""Proposal renderer — turn `bids/<slug>/proposal/` markdown trees into
submission-quality, tier-appropriate deliverables.

Per-bid output (4 tiers):

* `<slug>-client-executive-summary.pdf` — 6–12 page brochure (client).
* `<slug>-full-proposal.pdf` — 40–60 page styled proposal (client).
* `<slug>-internal-workbook.pdf` — internal-only scaffolding files
  (form fill guides, RFI letters, submission checklist, etc.).
* `<slug>-pitch-deck.pptx` — 10–15 designed slides (client).

Public API:

    from core.proposal_renderer import (
        build_client_pdfs,
        build_internal_workbook,
        build_pitch_deck,
        load_firm_profile,
    )

The PDF engine is `xhtml2pdf` because WeasyPrint's GTK / Pango native
libraries aren't available on this Windows workstation. The CSS design
system is therefore tuned to xhtml2pdf 0.2.x's supported subset.

`build_proposal_pdf` and `build_proposal_pptx` are kept as
backward-compatible shims for any caller still on the pre-tiering API.
"""

from __future__ import annotations

from .common import (
    Section,
    discover_sections,
    load_firm_profile,
    parse_bid_title,
    parse_solicitation_number,
    partition_sections,
    route_section,
)
from .internal_workbook import build_internal_workbook
from .pdf import build_client_pdfs, build_proposal_pdf
from .pptx import build_pitch_deck, build_proposal_pptx

__all__ = [
    "Section",
    "build_client_pdfs",
    "build_internal_workbook",
    "build_pitch_deck",
    "build_proposal_pdf",
    "build_proposal_pptx",
    "discover_sections",
    "load_firm_profile",
    "parse_bid_title",
    "parse_solicitation_number",
    "partition_sections",
    "route_section",
]
