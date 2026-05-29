"""Inspect v5a estimate.json for F-1..F-6 verification metrics."""
import json
from pathlib import Path

d = json.load(open(Path(__file__).parent / "estimate.json", encoding="utf-8"))

print("=== F-1: dedupe (count from log: 17 drops) ===")
print(f"bid_packages count: {len(d.get('bid_packages', []))}")
print(f"  (v4: 41; v5a expected: ~25 after dedupe + drawings filter)")
print()

print("=== F-2: client PDF render ===")
quote = Path(__file__).parent / "quote.pdf"
print(f"quote.pdf size: {quote.stat().st_size if quote.exists() else 'MISSING'}")
print()

print("=== F-3: refusals (run.log says 0) ===")
warnings = d.get("warnings", [])
refused = [w for w in warnings if "refused" in str(w).lower() or "refusal" in str(w).lower()]
print(f"refusal warnings in estimate: {len(refused)}")
print()

print("=== F-4: bid alternates recall ===")
print(f"top-level alternates: {len(d.get('alternates', []))}")
print(f"project_alternates: {len(d.get('project_alternates', []))}")
total_alts = 0
for bp in d.get("bid_packages", []):
    alts = bp.get("alternates", [])
    if alts:
        total_alts += len(alts)
        name = (bp.get("pdf_name") or "?")[:70]
        print(f"  {name}: {len(alts)} alternates")
        for a in alts[:3]:
            num = a.get("number", "?")
            desc = (a.get("description") or "")[:60]
            print(f"    - {num} | {desc}")
print(f"Total alternates across all bundles: {total_alts}")
print()

print("=== F-5: drawings filter (run.log says 11 skipped) ===")
print(f"sheet_summaries: {len(d.get('sheet_summaries', {}))}")
print(f"  (v4: 49 vision-classified sheets; v5a expected: 0 since classifier filter is strict)")
print()

print("=== F-6: AUTO_APPROVE share (no drawings ran, so N/A) ===")
print(f"auto_approve_count: {d.get('auto_approve_count')}")
print(f"operator_review_count: {d.get('operator_review_count')}")
print(f"hand_takeoff_count: {d.get('hand_takeoff_count')}")
print(f"total_auto_approve: ${d.get('total_auto_approve', 0):,.2f}")
print(f"line_items: {len(d.get('line_items', []))}")
print(f"subtotal: ${d.get('subtotal', 0):,.2f}")
print()

print("=== Other surfaces ===")
print(f"warnings: {len(warnings)}")
print(f"aggregated_inclusions: {len(d.get('aggregated_inclusions', []))}")
print(f"aggregated_exclusions: {len(d.get('aggregated_exclusions', []))}")
print(f"supporting_documents: {len(d.get('supporting_documents', []))}")
