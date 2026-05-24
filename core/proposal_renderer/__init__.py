"""Proposal renderer — turn `bids/<slug>/proposal/` markdown trees into
submission-quality PDFs and pitch-deck PPTX files.

Public API:

    from core.proposal_renderer import (
        build_proposal_pdf,
        build_proposal_pptx,
        load_firm_profile,
        discover_sections,
    )

The renderer is intentionally pure-Python (markdown + xhtml2pdf + python-pptx)
so it works on a stock Windows venv with no Cairo / Pango / Chromium / GTK
runtime dependency.
"""

from __future__ import annotations

from .common import (
    Section,
    discover_sections,
    load_firm_profile,
    parse_bid_title,
    parse_solicitation_number,
)
from .pdf import build_proposal_pdf
from .pptx import build_proposal_pptx

__all__ = [
    "Section",
    "build_proposal_pdf",
    "build_proposal_pptx",
    "discover_sections",
    "load_firm_profile",
    "parse_bid_title",
    "parse_solicitation_number",
]
