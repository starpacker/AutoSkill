#!/usr/bin/env python3
"""Comprehensive analysis: compare baseline vs transfer trajectories for ALL 37 pairs."""
import json, os, sys

BASEDIR = "/data/yjh/skill-transfer-eval/baseline"
TRANSDIR = "/data/yjh/skill-transfer-eval/transfer_pruned"
RESULTS = "/data/yjh/skill-transfer-eval/summary/all_results.json"
TRANSRES = "/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json"

def get_traj_stats(filepath):
    """Get statistics from a trajectory file."""
    stats = {"calls": 0, "rounds": set(), "errors": 0, "warnings": 0, "skill_calls": 0, "finalize_calls": 0}
    try:
        with open(filepath) as f:
            for line in f:
                d = json.loads(line)
                t = d.get("type", "")
                if t == "tool_call":
                    stats["calls"] += 1
                    stats["rounds"].add(d.get("round", "?"))
                    if d.get("tool") == "Skill":
                        stats["skill_calls"] += 1
                    if d.get("tool") == "finalize_submission":
                        stats["finalize_calls"] += 1
                elif t == "tool_result" and not d.get("ok", True):
                    stats["errors"] += 1
                elif t == "trajectory_warning":
                    stats["warnings"] += 1
    except:
        pass
    stats["num_rounds"] = len(stats["rounds"])
    return stats

def get_score(results_dict, task_id, run_type="baseline"):
    """Get score from all_results.json."""
    for tid, entry in results_dict.items():
        if tid == task_id:
            for run in entry.get(run_type, []):
                return run.get("reward", None), run.get("total_score", None)
    return None, None

# Load results
with open(RESULTS) as f:
    all_results = json.load(f)

with open(TRANSRES) as f:
    trans_results = json.load(f)

# Build transfer mapping
transfer_scores = {}
for pair in trans_results.get("pairs", []):
    key = f"{pair['source']}->{pair['target']}"
    val = pair["pruned_transfer"][0] if pair.get("pruned_transfer") else None
    transfer_scores[key] = val

# Find baseline dirs
baseline_dirs = {}
for d in os.listdir(BASEDIR):
    parts = d.split("_")
    if len(parts) >= 2:
        task_id = parts[0]
        if task_id not in baseline_dirs:
            baseline_dirs[task_id] = d

print("=" * 100)
print("COMPREHENSIVE TRANSFER ANALYSIS REPORT")
print("=" * 100)

# Analyze each transfer pair
for pair in trans_results.get("pairs", []):
    source = pair["source"]
    target = pair["target"]
    key = f"{source}->{target}"
    trans_score = transfer_scores.get(key, None)
    
    # Get baseline score from all_results.json (correct source)
    base_reward, base_score = None, None
    if target in all_results:
        for run in all_results[target].get("baseline", []):
            base_reward = run.get("reward")
            base_score = run.get("total_score")
            if base_reward and base_reward > 0:
                break  # prefer non-zero score
    if base_reward is None:
        base_reward = 0
        base_score = 0
    
    delta = round(trans_score - base_reward, 2) if trans_score is not None and base_reward is not None else None
    
    # Find trajectory files
    base_dir = baseline_dirs.get(target)
    base_traj = os.path.join(BASEDIR, base_dir, "logs/trajectory.raw.jsonl") if base_dir else None
    
    # Find transfer dir
    trans_dir_name = None
    for d in os.listdir(TRANSDIR):
        if d.startswith(f"{target}_pruned_transfer_{source}_to_{target}"):
            trans_dir_name = d
            break
    
    trans_traj = os.path.join(TRANSDIR, trans_dir_name, "logs/trajectory.raw.jsonl") if trans_dir_name else None
    
    # Get stats
    base_stats = get_traj_stats(base_traj) if base_traj and os.path.exists(base_traj) else None
    trans_stats = get_traj_stats(trans_traj) if trans_traj and os.path.exists(trans_traj) else None
    
    # Print summary
    direction = "UP" if delta and delta > 0.05 else ("DOWN" if delta and delta < -0.05 else "SAME")
    print(f"\n{'='*80}")
    print(f" {key}")
    print(f" Baseline: {base_reward} | Transfer: {trans_score} | Delta: {delta:+.2f} [{direction}]")
    print(f"{'='*80}")
    
    if base_stats:
        print(f"  Baseline: {base_stats['calls']} calls, {base_stats['num_rounds']} rounds, {base_stats['errors']} errors, {base_stats['warnings']} warnings")
    if trans_stats:
        print(f"  Transfer: {trans_stats['calls']} calls, {trans_stats['num_rounds']} rounds, {trans_stats['errors']} errors, {trans_stats['warnings']} warnings, {trans_stats['skill_calls']} skill calls")
    
    # Check for skill_application.json
    skill_app_path = os.path.join(TRANSDIR, trans_dir_name, "workspace/skill_application.json") if trans_dir_name else None
    if skill_app_path and os.path.exists(skill_app_path):
        try:
            sa = json.load(open(skill_app_path))
            if sa.get("skills"):
                for s in sa["skills"]:
                    print(f"  Skill used: {s.get('skill')} -> {s.get('status')}")
                    print(f"    Reason: {s.get('reason', '')[:150]}")
        except:
            print(f"  Skill: APPLICATION FILE EXISTS (parse error)")

print("\n" + "=" * 100)
print("SUMMARY TABLE")
print("=" * 100)
print(f"{'Source->Target':<30} {'Base':<6} {'Trans':<6} {'Δ':<6} {'Dir':<5} {'Base Traj':<20} {'Trans Traj':<20}")
print("-" * 100)
for pair in trans_results.get("pairs", []):
    source = pair["source"]
    target = pair["target"]
    key = f"{source}->{target}"
    trans_score = transfer_scores.get(key, 0)
    
    base_reward = 0
    if target in all_results:
        for run in all_results[target].get("baseline", []):
            base_reward = run.get("reward", 0)
            if base_reward > 0:
                break
    base_reward = base_reward or 0
    
    delta = round(trans_score - base_reward, 2) if trans_score is not None else 0
    direction = "UP" if delta > 0.05 else ("DOWN" if delta < -0.05 else "SAME")
    
    base_dir = baseline_dirs.get(target)
    base_traj = os.path.join(BASEDIR, base_dir, "logs/trajectory.raw.jsonl") if base_dir else None
    base_stats = get_traj_stats(base_traj) if base_traj and os.path.exists(base_traj) else None
    base_info = f"{base_stats['calls']}c/{base_stats['num_rounds']}r" if base_stats else "N/A"
    
    trans_dir_name = None
    for d in os.listdir(TRANSDIR):
        if d.startswith(f"{target}_pruned_transfer_{source}_to_{target}"):
            trans_dir_name = d
            break
    trans_traj = os.path.join(TRANSDIR, trans_dir_name, "logs/trajectory.raw.jsonl") if trans_dir_name else None
    trans_stats = get_traj_stats(trans_traj) if trans_traj and os.path.exists(trans_traj) else None
    trans_info = f"{trans_stats['calls']}c/{trans_stats['num_rounds']}r" if trans_stats else "N/A"
    
    print(f"{key:<30} {base_reward:<6} {trans_score:<6} {delta:<+6} {direction:<5} {base_info:<20} {trans_info:<20}")