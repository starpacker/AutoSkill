#!/usr/bin/env python3
"""Find all task IDs in all_results.json, focus on 17-1."""
import json
data = json.load(open("/data/yjh/skill-transfer-eval/summary/all_results.json"))
tasks = data.get("tasks", data)
# If tasks is a list (from all_results.json), convert to dict
if isinstance(tasks, list):
    task_dict = {t["task_id"]: t for t in tasks}
else:
    task_dict = tasks

print("Total tasks:", len(task_dict))

# Get da-17-1
for tid in ["da-17-1", "da-17-5", "da-12-4"]:
    if tid in task_dict:
        entry = task_dict[tid]
        print(f"\n=== {tid} ===")
        for run_type in ["baseline", "with_skill"]:
            runs = entry.get(run_type, [])
            print(f"  {run_type} ({len(runs)} runs):")
            for r in runs:
                print(f"    reward={r.get('reward')}, total_score={r.get('total_score')}, status={r.get('status')}, rounds={r.get('rounds')}")
                # Print criteria if available
                crit = r.get("criteria", {})
                if crit:
                    print(f"    criteria: {json.dumps(crit, indent=6)[:600]}")
                overall = r.get("overall_reasoning", "")
                if overall:
                    print(f"    overall: {overall[:300]}")
    else:
        print(f"\n=== {tid} NOT FOUND in data ===")