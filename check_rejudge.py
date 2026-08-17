#!/usr/bin/env python3
"""Check re-evaluated baseline scores from ablation dirs."""
import json, os, glob

# Check da-17-1 ablation baseline run_summary
ablation_path = "/data/yjh/skill-transfer-eval/ablations/da-17-1/eval/v_fe5fbfc3e739/run/da-17-1_oracle_skill_ablation_run_run_20260724_004119_01/logs/run_summary.json"
if os.path.exists(ablation_path):
    d = json.load(open(ablation_path))
    fr = d.get("final_result", {})
    print(f"da-17-1 ablation baseline: reward={d.get('reward')}, judge={fr.get('model')}, score={fr.get('total_score')}")
    print(f"  criteria: {json.dumps(fr.get('criteria',{}), indent=2)[:500]}")
    print(f"  reasoning: {fr.get('overall_reasoning','')[:200]}")

# Also check the original with-skill for da-17-1
skill_path = "/data/yjh/skill-transfer-eval/with_skill/da-17-1_20260721_192248_with-skill_rep1/logs/run_summary.json"
if os.path.exists(skill_path):
    d = json.load(open(skill_path))
    fr = d.get("final_result", {})
    print(f"\nda-17-1 with-skill (original): reward={d.get('reward')}, judge={fr.get('model')}, score={fr.get('total_score')}")

# Check all ablations for baseline scores
print("\n\n=== ALL ABLATION BASELINE SCORES ===")
for task_dir in sorted(os.listdir("/data/yjh/skill-transfer-eval/ablations/")):
    ab_path = os.path.join("/data/yjh/skill-transfer-eval/ablations", task_dir, "ablation_summary.json")
    if os.path.exists(ab_path):
        d = json.load(open(ab_path))
        for r in d.get("records", []):
            if r.get("mode") == "baseline" and r.get("result_type") == "pass":
                reason = r.get("reason", "")
                # Extract reward from reason
                reward = reason.replace("continuous_reward_", "")
                print(f"  {task_dir} baseline: {reward}")

# Also check the all_results.json for the actual baseline scores (not just 0.0 from Gemini)
print("\n\n=== ALL_RESULTS.JSON BASELINE SCORES ===")
base_results = json.load(open("/data/yjh/skill-transfer-eval/summary/all_results.json"))
for entry in base_results:
    tid = entry.get("task_id", "")
    for run in entry.get("baseline", []):
        rid = run.get("run_id", "")
        reward = run.get("reward", "?")
        score = run.get("total_score", "?")
        if reward != 0.0 or score != 0:
            print(f"  {tid} ({rid}): reward={reward}, score={score}")