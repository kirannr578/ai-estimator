"""Apply firm-profile.json values to placeholders across bids/.

Strategy:
- Layer 1: bulk exact-string substitutions for unambiguous firm-identity tokens.
- Layer 2: regex line-context substitutions for tokens that mean different things
  in different contexts (e.g. the bare `[USER TO FILL]` after "Federal EIN:" means
  the EIN, the same bare token after a personnel-name field means a person's name
  which we don't have).
- Layer 3: per-workspace past-performance fills — the 3 most-relevant past projects
  per the firm-profile's `past_project_selection_rules`.

Idempotent: running twice on the same tree produces the same output. The script
records before/after counts and writes a report under firm/_scripts/_apply_report.json.
"""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIDS = ROOT / "bids"
PROFILE = ROOT / "firm" / "firm-profile.json"

profile = json.loads(PROFILE.read_text(encoding="utf-8"))

LEGAL = profile["legal_name"]
DBA = profile["dba"]
LEGAL_FULL = f"{LEGAL} dba {DBA}"
ADDR_STREET = "16283 Willowick Ln"
ADDR_CITY_ZIP = "Frisco, TX 75033"
ADDR_FULL = f"{ADDR_STREET}, {ADDR_CITY_ZIP}"
PHONE = profile["phone_office"]
EMAIL = profile["email_primary"]
WEBSITE = profile["website"]
EIN = profile["ein"]
TX_TAXID = profile["tx_taxpayer_id"]
UEI = profile["uei"]
CAGE = profile["cage"]
DUNS = profile["duns_legacy"]
SOS_FILE = profile["tx_sos_file_number"]
HUB_VID = "1874292998900"
MBE_NUM = "DL09279"
GL_CARRIER = profile["insurance"]["general_liability"]["carrier"]
GL_POLICY = profile["insurance"]["general_liability"]["policy_number"]
GL_OCC = profile["insurance"]["general_liability"]["each_occurrence_limit"]
GL_AGG = profile["insurance"]["general_liability"]["general_aggregate_limit"]
GL_EXP_FLAG = (
    "current/renewed COI required pre-submission — last carrier on file was "
    f"{GL_CARRIER} (policy {GL_POLICY}), $1M/$2M, expired 2024-09-25"
)
ROCKY = "Ravikiran (Rocky) Nudurupati"
ROCKY_TITLE = "Founder & Managing Director"
ROCKY_EMAIL = profile["key_personnel"][0]["email"]

NOT_IN_PROFILE = "[USER TO FILL \u2014 not found in BPC firm profile, needs current data]"

# Per-workspace past-project ordered picks (project key → display string)
PAST_PROJECT_BLURBS = {
    "Lavon RV Park": (
        "**Lavon RV Park** — Lavon Leisure 78 RV Park LLC (commercial owner); "
        "30-lot new-build RV park at County Road 597, Farmersville, TX 75442; "
        "$1,050,000 fixed-price AIA A101-2020 contract; start 2025-07-30, "
        "scheduled substantial completion 2026-04-30 (currently in execution); "
        "scope: mobilization + excavation, rough grade, driveway/culvert, "
        "utility trenching (electrical / plumbing / septic), meters per lot, "
        "septic + sewer lines, storm drain + detention, 6-ft cedar fencing + "
        "metal gate per lot, 8x8 storage shed per lot, 150-LF retaining wall, "
        "laundromat building; $1M performance bond procured per Article 8; "
        "delivery method: design-bid-build; role: GC. "
        "Reference contact: [USER TO FILL \u2014 Lavon Leisure 78 RV Park LLC owner POC].\n\n"
        "  Source: `Lavon RV Park/` on OneDrive."
    ),
    "Hindu Temple of Southlake": (
        "**Hindu Temple of Southlake** — North Texas Hindu Heritage Society (nonprofit "
        "religious owner); \u224810,700 SF Assembly A-3 (Place of Religious Worship) "
        "renovation at 595 South Kimball Avenue, Southlake, TX 76092; owner-side "
        "project # 2024-024; scope: demolition + finishes + phenolic toilet partitions "
        "+ partition framework; drawings dated 2025-06-20 (PDF), updated 2025-09-12 "
        "(Arch + Structural); in execution per material quote 2025-10-30; "
        "delivery method: negotiated lump-sum (owner direct); role: GC. "
        "Final contract value: [USER TO FILL \u2014 not in BPC source files]. "
        "Reference contact: [USER TO FILL \u2014 North Texas Hindu Heritage Society POC].\n\n"
        "  Source: `Hindu Temple of South Lake/` on OneDrive."
    ),
    "Holiday Inn (Hall Park)": (
        "**Holiday Inn (Hall Park, Frisco)** — Holiday Inn franchisee (hospitality "
        "owner); commercial renovation at Hall Park, Frisco, TX; "
        "role: GC. Contract value, scope detail, and completion date: "
        "[USER TO FILL \u2014 cited by name in `BPC/Rocky Business Profile.docx` "
        "but no project-folder source on OneDrive; reconstruct from project records]. "
        "Reference contact: [USER TO FILL \u2014 Holiday Inn Hall Park property POC]."
    ),
    "250-500+ single-family-home portfolio": (
        "**250\u2013500+ single-family-home portfolio (cumulative since 2022)** \u2014 "
        "executed primarily as a specialty trade sub through GC partners "
        "That 1 Painter, Touchmark, Bridge View Build, and Hill Design Build "
        "across the DFW metroplex; scope: interior + exterior painting, drywall "
        "(tape/bed/texture), flooring, tile, trims, roofing repairs; role: "
        "specialty sub. Reference contacts: [USER TO FILL \u2014 named contact "
        "at each of the four featured GC partners]."
    ),
}

SELECTION = profile["past_project_selection_rules"]


def picks_for(workspace: str) -> list[str]:
    rules = SELECTION.get(workspace)
    if not rules:
        return []
    return rules["picks"]


# -----------------------------------------------------------------------------
# Layer 1 — bulk exact-string and broad-regex substitutions for firm-identity
# tokens. These are safe to apply globally — the bracketed text describes the
# firm rather than any project-specific value.
# -----------------------------------------------------------------------------

# Exact-string pairs (case-sensitive)
BULK_EXACT = [
    # Bare template tokens (no USER TO FILL prefix; treat as fill-in variables)
    ("[FIRM LEGAL NAME]", LEGAL_FULL),
    ("[FIRM NAME]", DBA),
    ("[FIRM ADDRESS]", ADDR_FULL),
    ("[Firm legal name]", LEGAL_FULL),
    ("[Firm Legal Name]", LEGAL_FULL),
    ("[Firm name]", DBA),
    ("[Firm Name]", DBA),
    ("[Firm names of attendees]", f"{DBA} representatives (names: [USER TO FILL])"),
    ("[Firm address]", ADDR_FULL),
    ("[Firm Address]", ADDR_FULL),
    ("[firm legal name]", LEGAL_FULL),
    ("[firm name]", DBA),
    ("[UEI]", UEI),
    ("[CAGE]", CAGE),
    ("[DUNS]", DUNS),
    ("[Firm legal name as registered in SAM]", LEGAL_FULL),
    ("[Firm Name (Principal)]", LEGAL_FULL),
    ("[Firm Name as Principal]", LEGAL_FULL),
    # Filename templates — keep [Firm Name] in filenames as DBA-no-spaces
    ("[Firm Name + UEI]", f"Blue Print Constructs (UEI {UEI})"),
    # Escaped-bracket forms (appear in markdown table cells where pipe escape is needed)
    ("\\[Firm Name + UEI\\]", f"Blue Print Constructs (UEI {UEI})"),
    ("\\[Firm Name\\]", DBA),
    ("\\[Firm legal name\\]", LEGAL_FULL),
    ("\\[UEI\\]", UEI),
    ("\\[CAGE\\]", CAGE),
]

# Regex patterns where the inner text describes the firm (legal name, address,
# phone, etc.). Matches any [USER TO FILL: <descriptor>] where the descriptor
# uniquely identifies a firm-identity value.
BULK_REGEX: list[tuple[re.Pattern[str], str]] = [
    # legal name / legal entity name / firm legal name (various phrasings).
    # Carefully scoped to OUR firm only — must contain "firm", "entity",
    # "offeror", "proposer", "bidder", "respondent", "contractor", or
    # "principal" as the subject. Does NOT match "[USER TO FILL: owner legal
    # name]" or similar past-project-owner descriptors.
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:"
            r"firm(?:'s)?\s+(?:exact\s+|full\s+)?legal\s+name"
            r"|legal\s+entity\s+name"
            r"|legal\s+name\s+of\s+(?:firm|offeror|proposer|bidder|respondent|contractor|principal)"
            r"|(?:offeror|proposer|bidder|respondent|contractor|principal|prime)'?s?\s+legal\s+name"
            r"|legal\s+name\s+of\s+the\s+(?:firm|offeror|proposer|bidder|respondent|contractor|principal)"
            r"|full\s+firm\s+legal\s+name"
            r"|firm(?:'s)?\s+full\s+legal\s+name"
            r")[^\]]*\]",
            re.IGNORECASE,
        ),
        LEGAL_FULL,
    ),
    # firm name (DBA form)
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:firm\s+name|firm'?s?\s+name|name\s+of\s+firm"
            r"|firm\s+dba\s+name|dba)[^\]]*\]",
            re.IGNORECASE,
        ),
        DBA,
    ),
    # address forms
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:firm\s+address|address|street\s+address)"
            r"[^\]]*\]",
            re.IGNORECASE,
        ),
        ADDR_STREET,
    ),
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:city,?\s*state,?\s*(?:zip|ZIP)|city\s+state\s+zip)"
            r"[^\]]*\]",
            re.IGNORECASE,
        ),
        ADDR_CITY_ZIP,
    ),
    # phone | email | website
    (
        re.compile(
            r"\[USER TO FILL:\s*phone\s*\|\s*email\s*\|\s*website[^\]]*\]",
            re.IGNORECASE,
        ),
        f"{PHONE} | {EMAIL} | {WEBSITE}",
    ),
    (
        re.compile(
            r"\[USER TO FILL:\s*phone\s*\|\s*email[^\]]*\]",
            re.IGNORECASE,
        ),
        f"{PHONE} | {EMAIL}",
    ),
    # phone-only
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:firm\s+phone|phone|office\s+phone)[^\]]*\]",
            re.IGNORECASE,
        ),
        PHONE,
    ),
    # email-only
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:firm\s+email|email|primary\s+email)[^\]]*\]",
            re.IGNORECASE,
        ),
        EMAIL,
    ),
    # website
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:firm\s+website|website|url)[^\]]*\]",
            re.IGNORECASE,
        ),
        WEBSITE,
    ),
    # UEI variants
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:UEI|12-character\s+SAM\s+UEI|SAM\s+UEI"
            r"|unique\s+entity\s+id)[^\]]*\]",
            re.IGNORECASE,
        ),
        UEI,
    ),
    # CAGE variants
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:CAGE|CAGE\s+code|DLA\s+CAGE)[^\]]*\]",
            re.IGNORECASE,
        ),
        CAGE,
    ),
    # EIN variants
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:EIN|FEIN|Federal\s+EIN|Tax\s+ID"
            r"|Federal\s+Employer\s+ID)[^\]]*\]",
            re.IGNORECASE,
        ),
        EIN,
    ),
    # TX Comptroller Taxpayer ID
    (
        re.compile(
            r"\[USER TO FILL:\s*(?:Texas\s+(?:Comptroller\s+)?)?Taxpayer\s+ID"
            r"[^\]]*\]",
            re.IGNORECASE,
        ),
        TX_TAXID,
    ),
]

# -----------------------------------------------------------------------------
# Layer 2 — line-context substitutions via regex.
# Each entry is (regex, replacement template). The regex must match on a single
# line and capture surrounding context; the replacement uses that context.
# -----------------------------------------------------------------------------

LINE_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    # EIN — common labels
    (
        re.compile(
            r"((?:Federal\s+)?(?:EIN|FEIN|Fed\.?\s+Employer\s+I\.?D\.?\s+No|"
            r"Employer\s+I\.?D\.?(?:\s+No)?|Tax\s+Identification\s+(?:Number|No))"
            r"\s*[:\-\u2013]\s*[`']?)\[USER TO FILL(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>" + EIN + r"\g<2>",
    ),
    # TX taxpayer ID
    (
        re.compile(
            r"((?:Texas\s+(?:Comptroller\s+)?)?Taxpayer\s+ID(?:\s+#)?\s*[:\-\u2013]"
            r"\s*[`']?)\[USER TO FILL(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>" + TX_TAXID + r"\g<2>",
    ),
    # UEI
    (
        re.compile(
            r"(UEI(?:\s+\(SAM\.gov\))?\s*[:\-\u2013]\s*[`']?)\[USER TO FILL"
            r"(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>" + UEI + r"\g<2>",
    ),
    # CAGE
    (
        re.compile(
            r"(CAGE(?:\s+code|\s+Code|\s+\(DLA\))?\s*[:\-\u2013]\s*[`']?)"
            r"\[USER TO FILL(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>" + CAGE + r"\g<2>",
    ),
    # DUNS (legacy)
    (
        re.compile(
            r"(DUNS(?:\s+\(legacy\))?\s*[:\-\u2013]\s*[`']?)\[USER TO FILL"
            r"(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>" + DUNS + r"\g<2>",
    ),
    # TX HUB cert — many phrasings; carry the expired flag
    (
        re.compile(
            r"(TX\s+HUB(?:\s+Cert)?(?:\s+\(if\s+applicable\))?\s*[:\-\u2013]\s*[`']?)"
            r"\[USER TO FILL(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>VID "
        + HUB_VID
        + " \u2014 EXPIRED 2024-08-31 per source cert; user to confirm renewal"
        + r"\g<2>",
    ),
    # MBE cert number
    (
        re.compile(
            r"(MBE(?:\s+\u2014?\s*Certificate\s+number|\s+cert(?:ificate)?\s+(?:number|#))?"
            r"\s*[:\-\u2013]\s*[`']?)\[USER TO FILL(?:[^\]]*)\]([`']?)",
            re.IGNORECASE,
        ),
        r"\g<1>"
        + MBE_NUM
        + " (DFW MSDC) \u2014 EXPIRED 2024-08-31 per source cert; user to confirm renewal"
        + r"\g<2>",
    ),
]

# -----------------------------------------------------------------------------
# Layer 3 — per-workspace past-performance section fills.
# Heuristic: for each proposal/04-past-performance.md and similar files, replace
# the first three "Reference N — [USER TO FILL...]" headers with the picks for
# that workspace.
# -----------------------------------------------------------------------------

PAST_PERF_FILES = {
    "proposal/04-past-performance.md",
    "proposal/03-volume-III-past-performance.md",
    "proposal/03-past-performance.md",
}

# "## A. Reference 1 — [USER TO FILL: project name]" (TAMU / cmd-post shape)
REF_HEADER_RE_A = re.compile(
    r"^(## [A-Z]\.\s+Reference\s+\d+)\s*\u2014\s*`?\[USER TO FILL[^\]\n]*\]`?\s*$",
    re.MULTILINE,
)

# "## Project Reference #1 — `[USER TO FILL: project name]`" (angelo / usfws shape)
REF_HEADER_RE_B = re.compile(
    r"^(## (?:Optional\s+)?Project\s+Reference\s+#\d+)\s*\u2014\s*`?\[USER TO FILL[^\]\n]*\]`?\s*$",
    re.MULTILINE,
)

# Past-performance at-a-glance summary table rows. Pattern matches a row of the
# form: | N | `[USER TO FILL]` | `[USER TO FILL]` | ...
# Only the first three picks are filled — rows 4 and 5 are "optional".
AT_GLANCE_ROW_RE = re.compile(
    r"^\|\s*(?P<num>\d+)(?:\s*\(opt\))?\s*\|\s*`\[USER TO FILL\]`\s*\|\s*"
    r"`\[USER TO FILL\]`\s*\|\s*`\$\[USER TO FILL\]`\s*\|\s*"
    r"`\[USER TO FILL\]`\s*\|\s*`\[USER TO FILL[^\]]*\]`\s*\|\s*"
    r"`\[USER TO FILL[^\]]*\]`\s*\|\s*$",
    re.MULTILINE,
)


def _summarize_pick(project: str) -> dict[str, str]:
    """Pull a short summary tuple for a project pick (for at-a-glance rows)."""
    for proj in profile["past_projects"]:
        if proj["name"].startswith(project) or project in proj["name"]:
            owner = proj.get("owner") or "[USER TO FILL]"
            value = proj.get("contract_value") or "[NOT FOUND IN BPC]"
            comp = (proj.get("completion_date")
                    or proj.get("scheduled_substantial_completion")
                    or "[NOT FOUND IN BPC]")
            return {
                "name": proj["name"],
                "owner": owner,
                "value": value,
                "completion": str(comp),
                "scope": proj.get("scope_summary", "")[:80],
            }
    return {"name": project, "owner": "[USER TO FILL]", "value": "[USER TO FILL]",
            "completion": "[USER TO FILL]", "scope": ""}


PICKS_BANNER_MARK = "<!-- firm-profile:picks-banner -->"


def fill_past_perf_section(workspace: str, text: str) -> tuple[str, int]:
    picks = picks_for(workspace)
    if not picks:
        return text, 0
    filled = 0

    # Inject (once, idempotently) a banner at the top of the file that tells the
    # user which past projects firm-profile.json picked for this bid. Survives
    # rerun via PICKS_BANNER_MARK.
    if PICKS_BANNER_MARK not in text:
        banner_lines = [
            "",
            PICKS_BANNER_MARK,
            "> **Past-performance picks for this bid** (from "
            "`firm/firm-profile.json` \u2192 `past_project_selection_rules."
            f"{workspace}`):",
            "> ",
        ]
        for i, project in enumerate(picks, start=1):
            blurb = PAST_PROJECT_BLURBS.get(project, project)
            first_line = blurb.split("\n", 1)[0]
            banner_lines.append(f"> {i}. {first_line}")
        banner_lines.append("> ")
        banner_lines.append("> The per-project entry templates below have been "
                            "pre-filled for sections that match the standard "
                            "TAMU/ASU reference-header shape. Bid workspaces "
                            "with a different template shape (USACE / federal) "
                            "still need the user to copy the recommended pick "
                            "data manually into each Project N section.")
        banner_lines.append("")
        # Insert right after the first heading + its blank line.
        h1_match = re.search(r"^(# [^\n]+\n)", text)
        if h1_match:
            insert_at = h1_match.end()
            text = text[:insert_at] + "\n" + "\n".join(banner_lines) + "\n" + text[insert_at:]
        else:
            text = "\n".join(banner_lines) + "\n" + text
        filled += 1

    # Fill the at-a-glance summary rows (only the first 3 picks).
    def at_glance_sub(m: re.Match[str]) -> str:
        nonlocal filled
        try:
            idx = int(m.group("num")) - 1
        except ValueError:
            return m.group(0)
        if idx >= len(picks):
            return m.group(0)
        s = _summarize_pick(picks[idx])
        filled += 1
        return (
            f"| {idx + 1} | {s['name']} | {s['owner']} | {s['value']} | "
            f"{s['completion']} | [USER TO FILL \u2014 same-team confirmation] | "
            f"Selected per firm-profile past_project_selection_rules[{workspace}] |"
        )

    text = AT_GLANCE_ROW_RE.sub(at_glance_sub, text)

    # Fill the per-reference section headers.
    for header_re in (REF_HEADER_RE_A, REF_HEADER_RE_B):
        headers = list(header_re.finditer(text))
        if not headers:
            continue
        chunks: list[tuple[int, int, str]] = []
        for i, m in enumerate(headers):
            if i >= len(picks):
                break
            project = picks[i]
            blurb = PAST_PROJECT_BLURBS.get(project, project)
            replacement = f"{m.group(1)} \u2014 {project}\n\n{blurb}\n"
            chunks.append((m.start(), m.end(), replacement))
            filled += 1
        if chunks:
            out_parts: list[str] = []
            pos = 0
            for s, e, repl in chunks:
                out_parts.append(text[pos:s])
                out_parts.append(repl)
                pos = e
            out_parts.append(text[pos:])
            text = "".join(out_parts)

    return text, filled


# -----------------------------------------------------------------------------
# Driver
# -----------------------------------------------------------------------------

PLACEHOLDER_RE = re.compile(r"\[(?:USER TO FILL|TBD|FILL|FIRM [^\]]+|BPC [^\]]+)[^\]]*\]")


def process_file(path: Path, workspace: str) -> dict:
    text = path.read_text(encoding="utf-8")
    original = text
    before = len(PLACEHOLDER_RE.findall(text))
    layer_counts = Counter()

    # Layer 1a — exact-string firm-identity substitutions
    for needle, repl in BULK_EXACT:
        if needle in text:
            n = text.count(needle)
            text = text.replace(needle, repl)
            layer_counts["L1"] += n

    # Layer 1b — descriptor-based regex substitutions (still firm-identity only)
    for pat, repl in BULK_REGEX:
        text, n = pat.subn(repl, text)
        layer_counts["L1"] += n

    # Layer 2 — context-sensitive line patterns (label-then-placeholder)
    for pat, repl in LINE_PATTERNS:
        text, n = pat.subn(repl, text)
        layer_counts["L2"] += n

    # Layer 3 — only on known past-perf files
    rel = path.relative_to(BIDS / workspace).as_posix()
    if rel in PAST_PERF_FILES:
        text, n = fill_past_perf_section(workspace, text)
        layer_counts["L3"] += n

    after = len(PLACEHOLDER_RE.findall(text))
    changed = text != original
    if changed:
        path.write_text(text, encoding="utf-8")
    return {
        "rel": path.relative_to(ROOT).as_posix(),
        "before": before,
        "after": after,
        "L1": layer_counts["L1"],
        "L2": layer_counts["L2"],
        "L3": layer_counts["L3"],
        "changed": changed,
    }


def main() -> int:
    report = {
        "by_workspace": defaultdict(lambda: {"files_changed": 0, "before": 0, "after": 0, "L1": 0, "L2": 0, "L3": 0}),
        "files": [],
    }
    workspaces = sorted([p for p in BIDS.iterdir() if p.is_dir() and not p.name.startswith("_")])
    for ws in workspaces:
        for f in sorted(ws.rglob("*")):
            if not f.is_file() or f.suffix.lower() not in (".md", ".json"):
                continue
            r = process_file(f, ws.name)
            report["files"].append(r)
            bucket = report["by_workspace"][ws.name]
            bucket["before"] += r["before"]
            bucket["after"] += r["after"]
            bucket["L1"] += r["L1"]
            bucket["L2"] += r["L2"]
            bucket["L3"] += r["L3"]
            if r["changed"]:
                bucket["files_changed"] += 1

    out = ROOT / "firm" / "_scripts" / "_apply_report.json"
    out.write_text(json.dumps(report, indent=2, default=dict), encoding="utf-8")

    for ws, b in report["by_workspace"].items():
        delta = b["before"] - b["after"]
        print(
            f"{ws}: {b['files_changed']} files changed; "
            f"placeholders {b['before']} -> {b['after']} (-{delta}); "
            f"L1={b['L1']} L2={b['L2']} L3={b['L3']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
