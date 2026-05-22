"""Deterministic pre-pass extractors that run before any LLM call.

The modules under `core.extraction` look at the raw PDF vector data and
pull out everything that is unambiguously present (title-block fields,
dimensions, schedule tables, etc.). When the deterministic snapshot is
confident enough, the downstream LLM extractor can skip its vision call
entirely; when it isn't, the snapshot is fed in as additional context so
the LLM doesn't re-extract what we already have.
"""

from .drawing_prepass import (
    Dimension,
    DrawingPrepassResult,
    Schedule,
    ScheduleRow,
    TitleBlockData,
    prepass_drawing_page,
    prepass_drawing_pdf,
)

__all__ = [
    "Dimension",
    "DrawingPrepassResult",
    "Schedule",
    "ScheduleRow",
    "TitleBlockData",
    "prepass_drawing_page",
    "prepass_drawing_pdf",
]
