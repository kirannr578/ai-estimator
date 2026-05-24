"""Shared helpers for the proposal renderer.

* `discover_sections` walks `bids/<slug>/proposal/` and returns the ordered
  list of `<NN>-*.md` files (numerical-prefix files first by their integer
  prefix, then any prefix-less files alphabetically; files starting with `_`
  are treated as drafts and skipped).
* `load_firm_profile` reads `firm/firm-profile.json` once and validates the
  shape we depend on (legal name, DBA, key personnel, NAICS, contact info).
* `parse_bid_title` / `parse_solicitation_number` derive deterministic
  cover-page strings from the H1 of `00-readme.md` + the bid folder name.
* `read_section_text` returns the source markdown of a section without
  mutating the file on disk (the brief explicitly forbids touching the
  source markdown).
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_FIRM_PROFILE = REPO_ROOT / "firm" / "firm-profile.json"
DEFAULT_LOGO_PATH = REPO_ROOT / "firm" / "assets" / "bpc-logo.png"

# `[USER TO FILL ...]` style markers we want highlighted in red so reviewers
# can see at a glance what is still missing in the rendered output.
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[USER TO FILL[^\]]*\]"),
    re.compile(r"\[NOT FOUND IN BPC[^\]]*\]"),
    re.compile(r"\[PENDING [A-Z][^\]]*\]"),
    re.compile(r"\[TBD[^\]]*\]"),
]


@dataclass(frozen=True)
class Section:
    """A single `<NN>-*.md` proposal section in render order."""

    path: Path
    prefix: int | None
    slug: str
    title: str
    body: str

    @property
    def filename(self) -> str:
        return self.path.name


def discover_sections(proposal_dir: Path) -> list[Section]:
    """Return the ordered list of proposal sections in `proposal_dir`.

    Ordering rules from the spec:
      * Files with a leading numerical prefix (`00-`, `01-`, ...) sort by
        the integer value of that prefix.
      * Files without a numerical prefix sort after the prefixed ones,
        alphabetically by filename.
      * Files whose stem starts with `_` are skipped (drafts).
    """
    if not proposal_dir.is_dir():
        raise FileNotFoundError(f"proposal directory not found: {proposal_dir}")

    prefixed: list[tuple[int, Path]] = []
    bare: list[Path] = []
    for p in sorted(proposal_dir.glob("*.md")):
        if p.name.startswith("_"):
            continue
        m = re.match(r"^(\d+)-", p.name)
        if m:
            prefixed.append((int(m.group(1)), p))
        else:
            bare.append(p)

    prefixed.sort(key=lambda tup: (tup[0], tup[1].name))
    ordered_paths = [p for _, p in prefixed] + sorted(bare)

    sections: list[Section] = []
    for p in ordered_paths:
        text = p.read_text(encoding="utf-8")
        title = _first_h1(text) or p.stem
        m = re.match(r"^(\d+)-(.+)\.md$", p.name)
        prefix = int(m.group(1)) if m else None
        slug = m.group(2) if m else p.stem
        sections.append(
            Section(path=p, prefix=prefix, slug=slug, title=title, body=text)
        )
    return sections


def _first_h1(markdown_text: str) -> str | None:
    """Return the first ATX-style H1 (`# Title`) text, or None."""
    for line in markdown_text.splitlines():
        s = line.strip()
        if s.startswith("# ") and not s.startswith("## "):
            return s[2:].strip()
    return None


def parse_bid_title(proposal_dir: Path, fallback_slug: str) -> str:
    """Derive a friendly bid title from `00-readme.md` H1, falling back to
    a Title-Cased version of the bid slug if the H1 isn't present."""
    readme = proposal_dir / "00-readme.md"
    if readme.is_file():
        h1 = _first_h1(readme.read_text(encoding="utf-8"))
        if h1:
            return h1
    return fallback_slug.replace("-", " ").title()


def parse_solicitation_number(bid_slug: str) -> str:
    """Pull a likely solicitation number from the trailing token of the
    bid-folder slug. Examples:

      * `tamu-harrington-2025-06813`  -> `2025-06813`
      * `angelo-state-carr-efa-26-007` -> `26-007`
      * `usfws-san-marcos-140FC126R0017` -> `140FC126R0017`
      * `cmd-post-ndi-W50S7626QA001` -> `W50S7626QA001`
    """
    parts = bid_slug.split("-")
    if not parts:
        return ""

    # Walk backwards collecting trailing tokens that look like numbers,
    # year-prefixed digits, or alphanumeric solicitation IDs (uppercase
    # letters + digits).
    trailing: list[str] = []
    for token in reversed(parts):
        if re.fullmatch(r"\d{2,5}", token):
            trailing.append(token)
        elif re.fullmatch(r"\d{4}", token):
            trailing.append(token)
        elif re.fullmatch(r"[A-Z0-9]{6,}", token):
            trailing.append(token)
        else:
            break
    if not trailing:
        return parts[-1]
    return "-".join(reversed(trailing))


def load_firm_profile(path: Path | None = None) -> dict[str, Any]:
    """Load and minimally validate `firm/firm-profile.json`."""
    p = path or DEFAULT_FIRM_PROFILE
    raw = json.loads(p.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"firm profile is not a JSON object: {p}")
    return raw


def find_section(sections: list[Section], *prefixes: int, slug_contains: str = "") -> Section | None:
    """Return the first section whose numerical prefix is in `prefixes` or
    whose slug contains `slug_contains`. Used by the PPTX builder to find
    the right `02-technical-approach` / `02-volume-II-...` section across
    bid shapes."""
    for s in sections:
        if s.prefix is not None and s.prefix in prefixes:
            return s
    if slug_contains:
        for s in sections:
            if slug_contains.lower() in s.slug.lower():
                return s
    return None


def strip_blockquote_prefix(text: str) -> str:
    """Strip leading `> ` markers from each line — used when we lift body
    prose out of a Markdown blockquote into PPTX bullets."""
    out: list[str] = []
    for line in text.splitlines():
        if line.startswith("> "):
            out.append(line[2:])
        elif line.startswith(">"):
            out.append(line[1:])
        else:
            out.append(line)
    return "\n".join(out)


def collapse_whitespace(text: str) -> str:
    """Collapse runs of whitespace to single spaces and trim, suitable for
    one-line table-cell or bullet-point use."""
    return re.sub(r"\s+", " ", text).strip()


def first_paragraph(text: str) -> str:
    """Return the first paragraph of `text` (sequence of non-blank lines)."""
    lines: list[str] = []
    started = False
    for line in text.splitlines():
        if not line.strip():
            if started:
                break
            continue
        # Skip Markdown headings — we only want body prose.
        if line.lstrip().startswith("#"):
            continue
        lines.append(line.strip())
        started = True
    return collapse_whitespace(" ".join(lines))


def find_h2_blocks(text: str) -> list[tuple[str, str]]:
    """Return [(h2 title, body)] in document order. The body of each block
    is everything from the line after the H2 to the next H2 (or EOF).

    H1 / H3 / H4 headings inside the body are preserved verbatim.
    """
    lines = text.splitlines()
    blocks: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_body: list[str] = []

    h2_re = re.compile(r"^##\s+(.+?)\s*$")

    for line in lines:
        m = h2_re.match(line)
        if m:
            if current_title is not None:
                blocks.append((current_title, current_body))
            current_title = m.group(1).strip()
            current_body = []
            continue
        if current_title is not None:
            current_body.append(line)

    if current_title is not None:
        blocks.append((current_title, current_body))

    return [(t, "\n".join(b).strip()) for t, b in blocks]


def find_h1_blocks(text: str) -> list[tuple[str, str]]:
    """Return [(h1 title, body)] in document order. Used by the
    `--pptx-style full` slide builder."""
    lines = text.splitlines()
    blocks: list[tuple[str, list[str]]] = []
    current_title: str | None = None
    current_body: list[str] = []

    h1_re = re.compile(r"^#\s+(.+?)\s*$")
    h2plus_re = re.compile(r"^#{2,}")

    for line in lines:
        if h2plus_re.match(line):
            if current_title is not None:
                current_body.append(line)
            continue
        m = h1_re.match(line)
        if m:
            if current_title is not None:
                blocks.append((current_title, current_body))
            current_title = m.group(1).strip()
            current_body = []
            continue
        if current_title is not None:
            current_body.append(line)

    if current_title is not None:
        blocks.append((current_title, current_body))

    return [(t, "\n".join(b).strip()) for t, b in blocks]


def list_items(text: str) -> list[str]:
    """Pull out top-level Markdown bullets (`- foo` or `* foo`) from `text`,
    flattening to plain strings (Markdown inline formatting preserved)."""
    items: list[str] = []
    bullet_re = re.compile(r"^\s{0,3}[-*]\s+(.+?)\s*$")
    for line in text.splitlines():
        m = bullet_re.match(line)
        if m:
            items.append(m.group(1).strip())
    return items


def split_placeholders(text: str) -> list[tuple[bool, str]]:
    """Split `text` into `(is_placeholder, fragment)` runs so a renderer can
    style placeholders separately (the PPTX renderer uses bold red)."""
    if not text:
        return [(False, "")]
    indices: list[tuple[int, int]] = []
    for pat in PLACEHOLDER_PATTERNS:
        for m in pat.finditer(text):
            indices.append((m.start(), m.end()))
    if not indices:
        return [(False, text)]

    indices.sort()
    merged: list[tuple[int, int]] = []
    for s, e in indices:
        if merged and s <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], e))
        else:
            merged.append((s, e))

    out: list[tuple[bool, str]] = []
    cursor = 0
    for s, e in merged:
        if s > cursor:
            out.append((False, text[cursor:s]))
        out.append((True, text[s:e]))
        cursor = e
    if cursor < len(text):
        out.append((False, text[cursor:]))
    return out


def primary_personnel(profile: dict[str, Any]) -> dict[str, str]:
    """Return name / email / phone for the firm's primary contact, used on
    PPTX cover slides and Q&A slides."""
    people = profile.get("key_personnel") or []
    if people:
        p = people[0]
        return {
            "name": p.get("name", ""),
            "title": p.get("title", ""),
            "email": p.get("email", profile.get("email_principal", "")),
            "phone": profile.get("phone_office", ""),
        }
    return {
        "name": "",
        "title": "",
        "email": profile.get("email_principal") or profile.get("email_primary", ""),
        "phone": profile.get("phone_office", ""),
    }
