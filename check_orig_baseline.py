#!/usr/bin/env python3
"""Get the original baseline scores from all_results.json (pre-Gemini-rejudge)."""
import json

with open("/data/yjh/skill-transfer-eval/summary/all_results.json") as f:
    data = json.load(f)

# all_results.json is a dict with task_id keys
for tid, entry in data.items():
    for run in entry.get("baseline", []):
        rid = run.get("run_id", "")
        reward = run.get("reward", "?")
        score = run.get("total_score", "?")
        print(f"  {tid} ({rid}): reward={reward}, score={score}")