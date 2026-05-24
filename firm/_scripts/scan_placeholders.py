"""Scan bids/ for placeholder tokens and report counts per file & per workspace."""
from __future__ import annotations

import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BIDS = ROOT / "bids"

PATTERN = re.compile(
    r"\["
    r"(?P<token>"
    r"USER TO FILL[^\]]*"
    r"|USER TO PROVIDE[^\]]*"
    r"|TBD[^\]]*"
    r"|FILL[^\]]*"
    r"|BPC [^\]]+"
    r"|FIRM [^\]]+"
    r"|TO FILL[^\]]*"
    r"|INSERT[^\]]+"
    r"|YOUR [^\]]+"
    r"|RKR[^\]]*"
    r")"
    r"\]",
    re.IGNORECASE,
)


def main() -> int:
    by_workspace: dict[str, Counter] = defaultdict(Counter)
    by_file: dict[str, int] = {}
    unique_tokens: Counter = Counter()
    workspaces = sorted([p for p in BIDS.iterdir() if p.is_dir() and not p.name.startswith("_")])
    for ws in workspaces:
        for f in ws.rglob("*"):
            if not f.is_file():
                continue
            if f.suffix.lower() not in (".md", ".json"):
                continue
            try:
                text = f.read_text(encoding="utf-8", errors="replace")
            except Exception:
                continue
            matches = PATTERN.findall(text)
            if not matches:
                continue
            rel = f.relative_to(ROOT).as_posix()
            by_file[rel] = len(matches)
            for m in matches:
                by_workspace[ws.name][m.upper()] += 1
                unique_tokens[m.upper()] += 1

    out = {
        "totals": {ws: sum(c.values()) for ws, c in by_workspace.items()},
        "files": dict(sorted(by_file.items())),
        "top_tokens": unique_tokens.most_common(40),
    }
    print(json.dumps(out, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
