#!/usr/bin/env python3
"""Check all baseline rounds for da-17-1."""
import json, os, glob

basedir = "/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/judge_gemini"

for f in sorted(glob.glob(f"{basedir}/judge_result_round_*.json")):
    print(f"=== {os.path.basename(f)} ===")
    d = json.load(open(f))
    print(f"  total_score: {d.get('total_score')}, max_score: {d.get('max_score')}")
    for k, v in d.get("criteria", {}).items():
        print(f"  {k}: level={v.get('level')}, points={v.get('points')}, reason={v.get('reason','')[:100]}")
    print(f"  overall: {d.get('overall_reasoning','')[:300]}")
    print()

# Also check run_manifest.json
manifest = json.load(open("/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/run_manifest.json"))
print("=== MANIFEST ===")
print(json.dumps(manifest, indent=2)[:500])