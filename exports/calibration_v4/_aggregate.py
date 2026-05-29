"""Aggregate metrics for calibration v4 report. Read-only helper, not committed code."""

import json
import re
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).parent
EST = json.load((ROOT / "estimate.json").open("r", encoding="utf-8"))


def dump_bundles():
    bp = EST.get("bid_packages", [])
    print("=== ALL BUNDLES ===")
    print(f"  {'#':>3}  {'pdf_name':60s}  {'trade':20s}  {'kind':14s}  u  i  e  a  l")
    for i, b in enumerate(bp):
        pn = (b.get("pdf_name") or "unknown")[:60]
        tn = repr(b.get("trade_name"))[:20]
        dk = repr(b.get("document_kind"))[:14]
        u = len(b.get("unit_prices", []))
        ic = len(b.get("inclusions", []))
        ex = len(b.get("exclusions", []))
        al = len(b.get("alternates", []))
        lo = len(b.get("allowances", []))
        print(f"  {i:>3}  {pn:60s}  {tn:20s}  {dk:14s}  {u:>2} {ic:>2} {ex:>2} {al:>2} {lo:>2}")


def aggregate_lines():
    """Aggregate line_items: confidence bands, cost-source tiers, suppressed, notes-tag positions."""
    items = EST.get("line_items", [])
    print(f"\n=== LINE ITEMS ({len(items)}) ===")
    if not items:
        print("  (none)")
        return

    # Sample a line to see schema
    print("  sample line keys:", list(items[0].keys()))

    bands = Counter()
    tiers = Counter()
    notes_tags = Counter()
    suppressed = 0
    csi_divs = Counter()
    total_priced = 0.0
    total_suppressed = 0.0

    tag_re = re.compile(r"\[(?P<tag>[a-z\-]+)\]")

    for it in items:
        bands[it.get("cost_band")] += 1
        tiers[it.get("cost_source_tier")] += 1
        if it.get("suppressed"):
            suppressed += 1
            total_suppressed += float(it.get("total_cost") or 0.0)
        else:
            total_priced += float(it.get("total_cost") or 0.0)
        csi_divs[it.get("csi_division")] += 1

        # Notes tag at position 0
        notes_field = it.get("notes")
        first_note = ""
        if isinstance(notes_field, list) and notes_field:
            first_note = str(notes_field[0])
        elif isinstance(notes_field, str):
            first_note = notes_field
        m = tag_re.match(first_note.strip()) if first_note else None
        if m:
            notes_tags[m.group("tag")] += 1
        else:
            notes_tags["(no-tag)"] += 1

    print(f"  suppressed lines: {suppressed}")
    print(f"  priced total $: {total_priced:,.2f}")
    print(f"  suppressed contribution $: {total_suppressed:,.2f}")
    print(f"\n  Confidence-band distribution:")
    for k, v in bands.most_common():
        print(f"    {v:>3}  {k}")
    print(f"\n  Cost-source-tier distribution:")
    for k, v in tiers.most_common():
        print(f"    {v:>3}  {k}")
    print(f"\n  Notes[0] tag distribution:")
    for k, v in notes_tags.most_common():
        print(f"    {v:>3}  {k}")
    print(f"\n  CSI division distribution:")
    for k, v in csi_divs.most_common():
        print(f"    {v:>3}  {k}")


def aggregate_warnings():
    w = EST.get("warnings", [])
    print(f"\n=== TOP-LEVEL WARNINGS ({len(w)}) ===")
    sample = w[:5]
    for s in sample:
        print(f"  - {str(s)[:160]}")


def aggregate_alternates():
    bp = EST.get("bid_packages", [])
    print(f"\n=== ALTERNATES ===")
    n = 0
    for b in bp:
        for a in b.get("alternates", []):
            n += 1
            print(
                f"  {b.get('pdf_name')!r:50s}  id={a.get('alternate_id')!r}  type={a.get('alternate_type')!r}  cd={a.get('cost_delta')!r}  inc={a.get('included_by_default')!r}"
            )
    if n == 0:
        print("  (none — no alternates extracted)")


def aggregate_unit_prices():
    bp = EST.get("bid_packages", [])
    print(f"\n=== UNIT_PRICES (bundles with any) ===")
    total = 0
    for b in bp:
        up = b.get("unit_prices", []) or []
        if up:
            total += len(up)
            print(f"  {b.get('pdf_name')!r:50s}  | {len(up)} rows | trade={b.get('trade_name')!r}")
    print(f"  TOTAL unit_prices across run: {total}")


def aggregate_takeoffs_drawings():
    bp = EST.get("bid_packages", [])
    drawings = [b for b in bp if (b.get("document_kind") or "") == "drawing_sheet"]
    print(f"\n=== DRAWING SHEET BUNDLES: {len(drawings)} ===")

    # Top-level typed schedules
    for k in ("doors", "windows", "rooms", "mep", "structural", "site", "spec_sections", "sheet_summaries"):
        v = EST.get(k)
        if v is None:
            continue
        if isinstance(v, list):
            print(f"  top-level {k}: {len(v)} entries")
        elif isinstance(v, dict):
            print(f"  top-level {k}: dict with keys {list(v.keys())[:8]}")
        else:
            print(f"  top-level {k}: {type(v).__name__}")


def aggregate_scope_matrix():
    sm = EST.get("scope_matrix")
    if sm:
        if isinstance(sm, dict):
            print(f"\n=== SCOPE MATRIX (dict, {len(sm)} keys): {list(sm.keys())[:6]} ===")
            for k in list(sm.keys())[:3]:
                v = sm[k]
                if isinstance(v, list):
                    print(f"  {k}: list of {len(v)} entries; sample: {str(v[:2])[:200]}")
                else:
                    print(f"  {k}: {type(v).__name__}: {str(v)[:200]}")
        elif isinstance(sm, list):
            print(f"\n=== SCOPE MATRIX: {len(sm)} entries (sample) ===")
            for e in sm[:5]:
                print(f"  - {str(e)[:160]}")
    else:
        print(f"\n=== SCOPE MATRIX: (empty) ===")


def aggregate_duplicates():
    """Find duplicate PDF names in bundles (sign of corpus duplication across subfolders)."""
    bp = EST.get("bid_packages", [])
    names = Counter()
    for b in bp:
        names[b.get("pdf_name") or ""] += 1
    dups = {k: v for k, v in names.items() if v > 1}
    print(f"\n=== DUPLICATE PDF NAMES IN BUNDLES: {len(dups)} ===")
    for k, v in sorted(dups.items()):
        print(f"  {v}x  {k}")


def aggregate_lines_priced_sample():
    items = EST.get("line_items", [])
    priced = [it for it in items if not it.get("suppressed") and (it.get("cost_source_tier") or "") == "exact_match"]
    print(f"\n=== SAMPLE EXACT_MATCH PRICED LINES (top 10) ===")
    for it in priced[:10]:
        print(
            f"  div={it.get('csi_division')} sec={it.get('csi_section')} q={it.get('quantity')} {it.get('unit')} @ ${it.get('unit_cost')} = ${it.get('total_cost')} band={it.get('cost_band')} src={(it.get('cost_source') or '')[:50]}"
        )


def aggregate_top_level_warnings_pattern():
    w = EST.get("warnings") or []
    print(f"\n=== TOP-LEVEL WARNINGS ({len(w)}) — pattern analysis ===")
    cats = Counter()
    for s in w:
        s2 = str(s)
        if "I'm sorry" in s2 or "did not return JSON" in s2:
            cats["LLM-refused-json"] += 1
        elif "scale" in s2.lower():
            cats["scale-unknown"] += 1
        elif "dimension" in s2.lower() or "legible" in s2.lower():
            cats["dimensions-illegible"] += 1
        elif "quantities" in s2.lower():
            cats["quantities-not-given"] += 1
        elif "estimator" in s2.lower():
            cats["estimator-error"] += 1
        else:
            cats["other"] += 1
    for k, v in cats.most_common():
        print(f"  {v:>3}  {k}")


def aggregate_aggregated_scope():
    ai = EST.get("aggregated_inclusions", [])
    ae = EST.get("aggregated_exclusions", [])
    print(f"\n=== AGGREGATED INCLUSIONS: {len(ai)}, EXCLUSIONS: {len(ae)} ===")
    if ai:
        print("  inclusion samples:")
        for it in ai[:5]:
            print(f"    - {str(it)[:160]}")
    if ae:
        print("  exclusion samples:")
        for it in ae[:5]:
            print(f"    - {str(it)[:160]}")


if __name__ == "__main__":
    dump_bundles()
    aggregate_lines()
    aggregate_warnings()
    aggregate_top_level_warnings_pattern()
    aggregate_alternates()
    aggregate_unit_prices()
    aggregate_takeoffs_drawings()
    aggregate_scope_matrix()
    aggregate_aggregated_scope()
    aggregate_duplicates()
    aggregate_lines_priced_sample()
