"""Brand constants for Blue Print Constructs proposal renderer.

Centralizes color hex strings, font stack, and asset paths so the PDF and
PPTX builders pull from a single source of truth. The PPTX renderer
re-imports the hex strings as `RGBColor` instances on its side.

Color palette derived from BPC's submission-package style guide:

* `BPC_NAVY`   — primary brand color, used on cover bands, slide title bars,
  table headers, H1/H2 type.
* `BPC_NAVY_DEEP` — darker fill used as a backstop on cover gradients.
* `BPC_SLATE`  — body-text gray (calmer than pure black for long reading).
* `BPC_GOLD`   — accent for callouts, key stats, "highlight" tags.
* `BPC_GRAY_BG` — alternating row shading for tables, callout backgrounds.
* `BPC_GRAY_LINE` — hairline rules.
"""

from __future__ import annotations

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]

LOGO_PATH = REPO_ROOT / "firm" / "assets" / "bpc-logo.png"
TEMPLATES_DIR = REPO_ROOT / "firm" / "assets" / "templates"
PHOTOS_DIR = REPO_ROOT / "firm" / "assets" / "past-project-photos"
FONTS_DIR = REPO_ROOT / "firm" / "assets" / "fonts"

PITCH_DECK_TEMPLATE = TEMPLATES_DIR / "bpc-pitch-deck-template.pptx"

BPC_NAVY = "#0B2545"
BPC_NAVY_DEEP = "#08182F"
BPC_NAVY_LINE = "#13355E"
BPC_SLATE = "#3A4750"
BPC_SLATE_SOFT = "#5C6A75"
BPC_GOLD = "#D4A017"
BPC_GOLD_SOFT = "#F5E1B4"
BPC_GRAY_BG = "#F4F6FA"
BPC_GRAY_BG_SOFT = "#F8F9FA"
BPC_GRAY_LINE = "#D7DCE4"
BPC_WHITE = "#FFFFFF"
BPC_NEAR_BLACK = "#1A1F26"

FONT_STACK = '"Segoe UI", "Helvetica Neue", Helvetica, Arial, sans-serif'
SERIF_STACK = '"Source Serif Pro", "Cambria", "Georgia", serif'

PPTX_FONT_HEADING = "Calibri"
PPTX_FONT_BODY = "Calibri"
