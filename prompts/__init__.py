"""Prompt templates loaded by the extractors."""

from pathlib import Path

PROMPT_DIR = Path(__file__).parent


def load(name: str) -> str:
    """Read a prompt template by stem (e.g. 'classifier' -> classifier.txt)."""
    path = PROMPT_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")
