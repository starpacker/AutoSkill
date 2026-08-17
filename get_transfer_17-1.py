#!/usr/bin/env python3
"""Get transfer results for da-17-1 pairs."""
import json

data = json.load(open("/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json"))
pairs = data.get("pairs", data)

for d in pairs:
    src = d.get("source", "")
    tgt = d.get("target", "")
    if "17-1" in tgt or "17-1" in src:
        print(f"  {src} -> {tgt}: scores={d.get('pruned_transfer', [])}")