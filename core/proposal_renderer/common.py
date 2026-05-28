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
# can see at a glance what is still missing in the rendered output. The
# client tier hides them (replaced with a neutral underline) unless the
# `--show-placeholders` flag is on; the internal-workbook tier always
# renders them in red.
PLACEHOLDER_PATTERNS = [
    re.compile(r"\[USER TO FILL[^\]]*\]"),
    re.compile(r"\[NOT FOUND IN BPC[^\]]*\]"),
    # `[PENDING e-BUILDER ACCESS: ...]` and similar — the lowercase token
    # after PENDING (`e-BUILDER`) means we can't insist on `[A-Z]` here.
    re.compile(r"\[PENDING [^\]]*\]", re.IGNORECASE),
    re.compile(r"\[TBD[^\]]*\]"),
    # Catch-all for `[X+30]` / `[X]` placeholders from schedule narrative.
    re.compile(r"\[X[+0-9]*\]"),
]

# File-routing rules — see the user brief.
# Always client-facing (kept in full proposal + executive summary inputs):
CLIENT_FACING_FILENAMES = {
    "00-readme.md",
    "01-executive-summary.md",
    "02-technical-approach.md",
    "02-volume-II-technical-acceptability.md",
    "02-technical-acceptability.md",
    "03-project-team.md",
    "03-volume-III-past-performance.md",
    "03-past-performance.md",
    "04-past-performance.md",
    "05-schedule-narrative.md",
    "06-quality-control-plan.md",
    "07-safety-plan.md",
    "10-price-proposal.md",
    "01-volume-I-price-proposal.md",
    "01-price-proposal.md",
}

# Internal-only patterns — go in the internal workbook PDF only.
INTERNAL_PATTERNS = [
    re.compile(r".*fill-guide\.md$", re.IGNORECASE),
    re.compile(r".*pull-guide\.md$", re.IGNORECASE),
    re.compile(r".*template\.md$", re.IGNORECASE),
    re.compile(r".*compliance.*\.md$", re.IGNORECASE),
    re.compile(r".*acknowledgment\.md$", re.IGNORECASE),
    re.compile(r".*memo\.md$", re.IGNORECASE),
    re.compile(r".*rfi.*\.md$", re.IGNORECASE),
    re.compile(r".*cover-letter\.md$", re.IGNORECASE),
    re.compile(r".*submission-checklist\.md$", re.IGNORECASE),
    re.compile(r".*bond.*\.md$", re.IGNORECASE),
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


def route_section(section: "Section") -> str:
    """Return `"client"` or `"internal"` for a given proposal section,
    using the rules in the user brief.

    A file is `internal` if it matches any of `INTERNAL_PATTERNS`. It is
    `client` if it appears in `CLIENT_FACING_FILENAMES`. Files that
    match neither default to `client` (per brief).
    """
    name = section.filename
    name_lc = name.lower()
    if name_lc in {n.lower() for n in CLIENT_FACING_FILENAMES}:
        return "client"
    for pat in INTERNAL_PATTERNS:
        if pat.match(name_lc):
            return "internal"
    return "client"


def partition_sections(
    sections: list["Section"],
) -> tuple[list["Section"], list["Section"]]:
    """Split sections into `(client_sections, internal_sections)`."""
    client: list[Section] = []
    internal: list[Section] = []
    for s in sections:
        if route_section(s) == "internal":
            internal.append(s)
        else:
            client.append(s)
    return client, internal


def neutralize_placeholders(text: str, *, underline_char: str = "_") -> str:
    """Replace `[USER TO FILL — ...]`-style markers with a neutral
    underline of comparable length. Used on client-facing tiers so the
    output looks like a fillable form rather than carrying red audit
    callouts. The underline is a sequence of underscore chars so both
    PDF and PPTX downstream renderers preserve length without needing
    a special font glyph.

    Length heuristic: clamp to [12, 60] characters so very short markers
    still look like a fillable line and very long ones don't run off the
    page.
    """
    if not text:
        return text

    def _replace(match: re.Match[str]) -> str:
        marker_len = match.end() - match.start()
        target = max(12, min(60, marker_len))
        return underline_char * target

    out = text
    for pat in PLACEHOLDER_PATTERNS:
        out = pat.sub(_replace, out)
    return out


def neutralize_placeholders_in_section(
    section: "Section", *, show_placeholders: bool
) -> "Section":
    """Return a copy of `section` with placeholder markers neutralized
    when `show_placeholders=False`, or returned unchanged when True."""
    if show_placeholders:
        return section
    new_body = neutralize_placeholders(section.body)
    if new_body == section.body:
        return section
    return Section(
        path=section.path,
        prefix=section.prefix,
        slug=section.slug,
        title=section.title,
        body=new_body,
    )


# ---------------------------------------------------------------------------
# Wide-table hardening (Day-2 fix)
# ---------------------------------------------------------------------------
#
# `xhtml2pdf`'s `PmlTable` auto-layout can produce a negative column width
# when a single row has enough character content that some columns get
# starved by an over-eager neighbour. The Day-1 symptom was a TAMU Wehner
# 4-col × 12-row table in `04-scope-of-work.md` that crashed both client
# PDFs with `flowable given negative availWidth=-1.77e-15` on cell(0,0).
#
# Defense in depth:
#
# 1. **Pre-process layer.** `downgrade_wide_html_tables(html)` finds each
#    rendered `<table>` block, measures column count + per-row text width,
#    and wraps "wide" tables in a compact-font `<div>` so xhtml2pdf has
#    enough headroom to fit every column without crushing one to 0pt.
#
# 2. **Safety net.** When the primary render still throws, the caller can
#    re-render with `flatten_markdown_tables_to_definition_list(text)`
#    applied first, which converts every markdown table to a flat
#    `**Header:** value` paragraph list. This is uglier than a table but
#    never triggers PmlTable layout at all.
#
# Thresholds are tuned conservatively against the live bid corpus —
# tables with ≤ 5 cols and ≤ 120 chars per row render fine and stay
# untouched.

WIDE_TABLE_MAX_COLS = 5
WIDE_TABLE_MAX_ROW_CHARS = 120
WIDE_TABLE_COMPACT_FONT_PT = 7

_HTML_TABLE_RE = re.compile(r"<table[^>]*>.*?</table>", re.DOTALL | re.IGNORECASE)
_HTML_ROW_RE = re.compile(r"<tr[^>]*>(.*?)</tr>", re.DOTALL | re.IGNORECASE)
_HTML_CELL_RE = re.compile(r"<t[dh][^>]*>(.*?)</t[dh]>", re.DOTALL | re.IGNORECASE)
_HTML_TAG_STRIP_RE = re.compile(r"<[^>]+>")


def _table_dimensions(table_html: str) -> tuple[int, int]:
    """Return (max_col_count, max_row_text_chars) for an HTML table."""
    rows = _HTML_ROW_RE.findall(table_html)
    max_cols = 0
    max_row_chars = 0
    for row in rows:
        cells = _HTML_CELL_RE.findall(row)
        if not cells:
            continue
        max_cols = max(max_cols, len(cells))
        row_text = " ".join(_HTML_TAG_STRIP_RE.sub("", c) for c in cells)
        max_row_chars = max(max_row_chars, len(row_text))
    return max_cols, max_row_chars


def is_wide_html_table(
    table_html: str,
    *,
    max_cols: int = WIDE_TABLE_MAX_COLS,
    max_row_chars: int = WIDE_TABLE_MAX_ROW_CHARS,
) -> bool:
    """Return True if a rendered HTML `<table>` would likely trigger
    `xhtml2pdf` auto-layout failures.

    A table is "wide" when either:
      * it has more columns than `max_cols`, OR
      * any single row's combined cell text exceeds `max_row_chars`.

    The defaults (5 cols / 120 chars) are tuned to the BPC proposal-
    template corpus — they leave the typical 2-col `| Field | Value |`
    tables, 3-col `| # | Item | Notes |` tables, and 6-col team /
    past-perf tables untouched while catching the Wehner Wk-by-Wk
    schedule and similar dense matrices.
    """
    cols, chars = _table_dimensions(table_html)
    return cols > max_cols or chars > max_row_chars


def downgrade_wide_html_tables(
    html: str,
    *,
    max_cols: int = WIDE_TABLE_MAX_COLS,
    max_row_chars: int = WIDE_TABLE_MAX_ROW_CHARS,
    font_pt: int = WIDE_TABLE_COMPACT_FONT_PT,
) -> str:
    """Wrap every "wide" `<table>` in `html` with a compact-font `<div>`
    so xhtml2pdf has room to lay out every column.

    Narrow tables are returned unchanged so the normal CSS styling
    (alternating row shading, header weight) keeps working on them.

    Idempotent — tables already sitting inside a `compact-table-wrap`
    div (from a previous pass) are not re-wrapped.
    """

    # Pre-compute the spans (start,end) of every existing wrap div so
    # we can skip tables that are already inside one. This keeps the
    # function idempotent without changing the markup signature.
    wrap_open_re = re.compile(
        r'<div class="compact-table-wrap"[^>]*>', re.IGNORECASE
    )
    wrap_spans: list[tuple[int, int]] = []
    for m in wrap_open_re.finditer(html):
        # Match the closing </div> that pairs with this open. Wraps are
        # single-table, single-div — find the very next </div>.
        end_m = re.search(r"</div>", html[m.end():], flags=re.IGNORECASE)
        if end_m is None:
            continue
        wrap_spans.append((m.start(), m.end() + end_m.end()))

    def _inside_existing_wrap(pos: int) -> bool:
        return any(start <= pos < end for start, end in wrap_spans)

    def _wrap(match: re.Match[str]) -> str:
        table = match.group(0)
        if _inside_existing_wrap(match.start()):
            return table
        if not is_wide_html_table(
            table, max_cols=max_cols, max_row_chars=max_row_chars,
        ):
            return table
        return (
            f'<div class="compact-table-wrap" '
            f'style="font-size: {font_pt}pt; line-height: 1.15;">'
            f"{table}"
            f"</div>"
        )

    return _HTML_TABLE_RE.sub(_wrap, html)


# Markdown table block: a header row + an alignment-separator row + 0+
# body rows, every line starts with `|`. We anchor on the separator row
# (`|---|---|` shape) because that's the unambiguous marker.
_MD_TABLE_BLOCK_RE = re.compile(
    r"(?m)"
    r"(?:^[ \t]*\|.+?\|[ \t]*\r?\n)"   # header row
    r"(?:^[ \t]*\|[\s\-:|]+\|[ \t]*\r?\n)"  # separator row
    r"(?:(?:^[ \t]*\|.+?\|[ \t]*(?:\r?\n|$))+)"  # one or more body rows
)


def _parse_md_table(block: str) -> tuple[list[str], list[list[str]]]:
    """Parse a markdown table block into (header_cells, body_rows).
    Each cell is whitespace-trimmed; backtick markers are kept."""
    lines = [ln for ln in block.splitlines() if ln.strip().startswith("|")]
    if len(lines) < 2:
        return [], []
    header = [c.strip() for c in lines[0].strip().strip("|").split("|")]
    # lines[1] is the separator row — skip it
    body_rows: list[list[str]] = []
    for raw in lines[2:]:
        cells = [c.strip() for c in raw.strip().strip("|").split("|")]
        # Pad to header width so flattened output stays consistent
        while len(cells) < len(header):
            cells.append("")
        body_rows.append(cells)
    return header, body_rows


def flatten_markdown_tables_to_definition_list(
    text: str,
    *,
    max_cols: int = WIDE_TABLE_MAX_COLS,
    max_row_chars: int = WIDE_TABLE_MAX_ROW_CHARS,
    always: bool = False,
) -> str:
    """Replace every "wide" markdown table in `text` with a flat
    definition-list rendering, leaving narrow tables untouched.

    Each row becomes a `**Row N** \u2014 *<first cell>*` line followed by
    `- **Header:** value` bullets for the remaining columns. Tables
    without a header still flatten (header columns get synthetic names
    `col 1`, `col 2`, ...).

    `always=True` forces every markdown table to flatten regardless of
    width — used by the safety-net fallback when even compact-font
    tables blew up.
    """

    def _flatten(match: re.Match[str]) -> str:
        block = match.group(0)
        header, body = _parse_md_table(block)
        if not header or not body:
            return block
        # Width check — operate on raw cell text widths, not HTML, since
        # this preprocessor runs before HTML render.
        max_row_chars_found = max(
            (sum(len(c) for c in row) + 2 * len(row) for row in body),
            default=0,
        )
        if not always and len(header) <= max_cols and max_row_chars_found <= max_row_chars:
            return block

        out_lines: list[str] = []
        for i, row in enumerate(body, start=1):
            first = row[0] if row else ""
            label = header[0] if header else "col 1"
            out_lines.append(f"**{label} {first}**")
            for h, v in zip(header[1:], row[1:]):
                out_lines.append(f"- **{h}:** {v}")
            out_lines.append("")
        # Make sure surrounding blank lines preserve the source block's
        # paragraph separation (the regex captured trailing newlines).
        flattened = "\n".join(out_lines).rstrip() + "\n"
        return flattened

    return _MD_TABLE_BLOCK_RE.sub(_flatten, text)


# ---------------------------------------------------------------------------


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
