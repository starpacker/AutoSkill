#!/usr/bin/env python3
"""
collect_results.py — Collect all BioMniBench evaluation results into a single summary.
Now also collects transfer evaluation results.

Usage:
  python3 collect_results.py                          # collect all results
  python3 collect_results.py --json                   # output as JSON only
  python3 collect_results.py --watch                  # show which tasks are still missing
  python3 collect_results.py --transfer               # collect transfer results only

Output:
  - summary/all_results.json          (machine-readable)
  - summary/results_table.txt         (human-readable table)
  - summary/missing_tasks.txt         (what's still missing)
  - summary/transfer_results.json     (transfer evaluation results)
  - summary/transfer_table.txt        (transfer results table)
"""

import json, os, sys, glob
from pathlib import Path

BASE_DIR = Path("/data/yjh/skill-transfer-eval")
BASELINE_DIR = BASE_DIR / "baseline"
SKILL_DIR = BASE_DIR / "with-skill"
TRANSFER_DIR = BASE_DIR / "transfer"
SUMMARY_DIR = BASE_DIR / "summary"

ALL_TASKS = [
    "da-1-3","da-1-4","da-10-1","da-10-3","da-11-1",
    "da-12-2","da-12-4","da-13-1","da-13-3","da-13-5",
    "da-13-6","da-14-1","da-14-3","da-14-8","da-15-1",
    "da-15-2","da-15-7","da-15-8","da-16-1","da-17-1",
    "da-17-3","da-17-5","da-18-1","da-18-5","da-18-7",
    "da-19-1","da-19-3","da-19-4","da-19-6","da-20-1",
    "da-20-3","da-20-4","da-24-3","da-25-1","da-26-2",
    "da-26-4","da-3-4","da-3-5","da-4-1","da-4-6",
    "da-4-7","da-5-1","da-5-3","da-6-2","da-6-5",
    "da-8-1","da-8-2","da-8-3","da-9-1","da-9-7",
]

# Source→Target pairs for transfer evaluation
TRANSFER_PAIRS = [
    ("da-5-1", "da-5-3"),
    ("da-8-1", "da-8-3"),
    ("da-13-5", "da-13-6"),
    ("da-17-1", "da-17-5"),
    ("da-18-5", "da-18-7"),
    ("da-19-3", "da-19-4"),
    ("da-19-4", "da-19-6"),
    ("da-26-2", "da-26-4"),
]

def get_run_summaries(runs_dir):
    """Gather results from .judge_private/ judge result files, round 1 only.

    Only round 1 is used because:
    - The original harness leaked judge reasoning text as feedback to the agent
      in multi-round runs (see FEEDBACK_LEAKAGE_FIX.md).
    - This means rounds 2+ are contaminated by rubric hints and are not valid
      measures of the model's unaided performance.
    - run_summary.json is also unreliable (reward field always 0.0).
    """
    results = {}
    if not runs_dir.is_dir():
        return results
    judge_private_dir = runs_dir / ".judge_private"
    if not judge_private_dir.is_dir():
        return results
    for run_dir in sorted(judge_private_dir.iterdir()):
        if not run_dir.is_dir():
            continue
        run_id = run_dir.name
        task = run_id.split("_")[0]
        if not task.startswith("da-"):
            continue

        # Try to find the first valid round result.
        # Round 1 is the preferred choice (no feedback leakage).
        # However, if round 1 failed with an API error (429, 400, etc.),
        # the model never received any feedback, so we fall back to the
        # first successful round. This avoids false negatives from
        # infrastructure issues.
        valid_result = None
        for round_file in sorted(run_dir.glob("judge_result_round_*.json")):
            try:
                data = json.loads(round_file.read_text())
                score = data.get("total_score", data.get("score"))
                error = data.get("error", "")
                if error:
                    # API error — skip this round, no feedback was given
                    continue
                if score is not None and isinstance(score, (int, float)) and score > 0:
                    valid_result = {
                        "data": data,
                        "score": score,
                        "round": round_file,
                    }
                    break  # Found first successful round
            except Exception:
                continue

        if valid_result is None:
            continue

        data = valid_result["data"]
        score = valid_result["score"]
        reward = score / 100.0
        status = "success" if reward >= 0.6 else "failed"

        if task not in results:
            results[task] = []
        results[task].append({
            "run_id": run_id,
            "reward": reward,
            "total_score": score,
            "status": status,
            "rounds": 1,
        })

    # Fallback: some runs have judge_gemini results but no .judge_private/ results
    # (e.g. da-1-3 with-skill rep1, da-16-1 with-skill rep1)
    for run_dir in sorted(runs_dir.iterdir()):
        if not run_dir.is_dir() or run_dir.name.startswith("."):
            continue
        run_id = run_dir.name
        task = run_id.split("_")[0]
        if not task.startswith("da-"):
            continue
        # Skip if already found via .judge_private
        if task in results and any(r["run_id"] == run_id for r in results[task]):
            continue
        # Check judge_gemini directory
        gemini_dir = run_dir / "judge_gemini"
        if not gemini_dir.is_dir():
            continue

        # Find first valid round (skip API errors — no feedback given)
        valid_result = None
        for round_file in sorted(gemini_dir.glob("judge_result_round_*.json")):
            try:
                data = json.loads(round_file.read_text())
                score = data.get("total_score", data.get("score"))
                error = data.get("error", "")
                if error:
                    continue
                if score is not None and isinstance(score, (int, float)) and score > 0:
                    valid_result = {"score": score}
                    break
            except Exception:
                continue

        if valid_result is None:
            continue

        score = valid_result["score"]
        reward = score / 100.0
        status = "success" if reward >= 0.6 else "failed"

        if task not in results:
            results[task] = []
        results[task].append({
            "run_id": run_id,
            "reward": reward,
            "total_score": score,
            "status": status,
            "rounds": 1,
        })

    return results

def collect_main():
    """Collect baseline and with-skill results."""
    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    baseline_results = get_run_summaries(BASELINE_DIR)
    skill_results = get_run_summaries(SKILL_DIR)

    all_results = {"tasks": []}
    missing_baseline = []
    missing_skill = []

    for task_id in ALL_TASKS:
        base = baseline_results.get(task_id, [])
        skill = skill_results.get(task_id, [])
        all_results["tasks"].append({
            "task_id": task_id,
            "baseline": base,
            "with_skill": skill,
        })
        if not base:
            missing_baseline.append(task_id)
        if not skill:
            missing_skill.append(task_id)

    # Save JSON
    json_path = SUMMARY_DIR / "all_results.json"
    json_path.write_text(json.dumps(all_results, indent=2))

    # Save table
    table_path = SUMMARY_DIR / "results_table.txt"
    with open(table_path, "w") as f:
        f.write(f"{'='*110}\n")
        f.write(f"{'BioMniBench — DeepSeek-V4 Evaluation Results':^110}\n")
        f.write(f"{'='*110}\n")
        f.write(f"{'Task':<12} {'Baseline (rewards)':<45} {'With-Skill (rewards)':<45}\n")
        f.write(f"{'-'*12} {'-'*45} {'-'*45}\n")

        for t in all_results["tasks"]:
            base_rewards = [r["reward"] for r in t["baseline"] if r["reward"] is not None]
            sk_rewards = [r["reward"] for r in t["with_skill"] if r["reward"] is not None]

            if base_rewards:
                avg = sum(base_rewards) / len(base_rewards)
                vals = ", ".join(f"{x:.2f}" for x in base_rewards)
                base_str = f"n={len(base_rewards)} avg={avg:.3f} [{vals}]"
            else:
                base_str = "⚠️ MISSING"

            if sk_rewards:
                avg = sum(sk_rewards) / len(sk_rewards)
                vals = ", ".join(f"{x:.2f}" for x in sk_rewards)
                sk_str = f"n={len(sk_rewards)} avg={avg:.3f} [{vals}]"
            else:
                sk_str = "⚠️ MISSING"

            f.write(f"{t['task_id']:<12} {base_str:<45} {sk_str:<45}\n")

    # Save missing tasks
    missing_path = SUMMARY_DIR / "missing_tasks.txt"
    with open(missing_path, "w") as f:
        f.write(f"Missing baseline ({len(missing_baseline)}):\n")
        for t in missing_baseline:
            f.write(f"  {t}\n")
        f.write(f"\nMissing with-skill ({len(missing_skill)}):\n")
        for t in missing_skill:
            f.write(f"  {t}\n")

    return all_results, missing_baseline, missing_skill

def collect_transfer():
    """Collect and display transfer evaluation results."""
    transfer_results = get_run_summaries(TRANSFER_DIR)

    # Load baseline and oracle-skill results for comparison
    baseline_results = get_run_summaries(BASELINE_DIR)
    skill_results = get_run_summaries(SKILL_DIR)

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    # Build transfer data
    transfer_data = {"pairs": []}
    for source, target in TRANSFER_PAIRS:
        base = baseline_results.get(target, [])
        oracle = skill_results.get(target, [])
        transfer = transfer_results.get(target, [])

        base_rewards = [r["reward"] for r in base if r["reward"] is not None]
        oracle_rewards = [r["reward"] for r in oracle if r["reward"] is not None]
        transfer_rewards = [r["reward"] for r in transfer if r["reward"] is not None]

        transfer_data["pairs"].append({
            "source": source,
            "target": target,
            "baseline": base_rewards,
            "oracle_skill": oracle_rewards,
            "generalized_transfer": transfer_rewards,
        })

    # Save JSON
    json_path = SUMMARY_DIR / "transfer_results.json"
    json_path.write_text(json.dumps(transfer_data, indent=2))

    # Save table
    table_path = SUMMARY_DIR / "transfer_table.txt"
    with open(table_path, "w") as f:
        f.write(f"{'='*120}\n")
        f.write(f"{'BioMniBench — Skill Transfer Evaluation Results':^120}\n")
        f.write(f"{'='*120}\n")
        f.write(f"{'Source':<12} {'Target':<12} {'Baseline':<20} {'Oracle':<20} {'Transfer':<20} {'Transfer-Base':<16} {'Transfer-Oracle':<16}\n")
        f.write(f"{'-'*12} {'-'*12} {'-'*20} {'-'*20} {'-'*20} {'-'*16} {'-'*16}\n")

        for p in transfer_data["pairs"]:
            def avg_str(vals):
                if not vals:
                    return "---"
                a = sum(vals) / len(vals)
                return f"{a:.3f} (n={len(vals)})"

            base_s = avg_str(p["baseline"])
            oracle_s = avg_str(p["oracle_skill"])
            transfer_s = avg_str(p["generalized_transfer"])

            # Compute deltas
            if p["baseline"] and p["generalized_transfer"]:
                b_avg = sum(p["baseline"]) / len(p["baseline"])
                t_avg = sum(p["generalized_transfer"]) / len(p["generalized_transfer"])
                delta_base = f"{t_avg - b_avg:+.3f}"
            else:
                delta_base = "---"

            if p["oracle_skill"] and p["generalized_transfer"]:
                o_avg = sum(p["oracle_skill"]) / len(p["oracle_skill"])
                t_avg = sum(p["generalized_transfer"]) / len(p["generalized_transfer"])
                delta_oracle = f"{t_avg - o_avg:+.3f}"
            else:
                delta_oracle = "---"

            f.write(f"{p['source']:<12} {p['target']:<12} {base_s:<20} {oracle_s:<20} {transfer_s:<20} {delta_base:<16} {delta_oracle:<16}\n")

    # Print summary
    print(f"\n{'='*100}")
    print(f"{'Skill Transfer Evaluation Results':^100}")
    print(f"{'='*100}")
    print(f"{'Source':<12} {'Target':<12} {'Baseline':<16} {'Oracle':<16} {'Transfer':<16} {'Δ vs Base':<12} {'Δ vs Oracle':<12}")
    print(f"{'-'*100}")

    for p in transfer_data["pairs"]:
        def avg_str(vals):
            if not vals:
                return "---"
            a = sum(vals) / len(vals)
            return f"{a:.3f}"

        base_s = avg_str(p["baseline"])
        oracle_s = avg_str(p["oracle_skill"])
        transfer_s = avg_str(p["generalized_transfer"])

        if p["baseline"] and p["generalized_transfer"]:
            b_avg = sum(p["baseline"]) / len(p["baseline"])
            t_avg = sum(p["generalized_transfer"]) / len(p["generalized_transfer"])
            delta_base = f"{t_avg - b_avg:+.3f}"
        else:
            delta_base = "---"

        if p["oracle_skill"] and p["generalized_transfer"]:
            o_avg = sum(p["oracle_skill"]) / len(p["oracle_skill"])
            t_avg = sum(p["generalized_transfer"]) / len(p["generalized_transfer"])
            delta_oracle = f"{t_avg - o_avg:+.3f}"
        else:
            delta_oracle = "---"

        print(f"{p['source']:<12} {p['target']:<12} {base_s:<16} {oracle_s:<16} {transfer_s:<16} {delta_base:<12} {delta_oracle:<12}")

    print(f"\nSaved: {json_path}")
    print(f"       {table_path}")

    return transfer_data

def main():
    if "--transfer" in sys.argv:
        collect_transfer()
    elif "--watch" in sys.argv:
        baseline_results = get_run_summaries(BASELINE_DIR)
        skill_results = get_run_summaries(SKILL_DIR)
        transfer_results = get_run_summaries(TRANSFER_DIR)
        missing_b = [t for t in ALL_TASKS if t not in baseline_results]
        missing_s = [t for t in ALL_TASKS if t not in skill_results]
        print(f"Missing baseline: {len(missing_b)} tasks")
        for t in missing_b:
            print(f"  {t}")
        print(f"\nMissing with-skill: {len(missing_s)} tasks")
        for t in missing_s:
            print(f"  {t}")
        print(f"\nTransfer results so far:")
        for t in sorted(transfer_results.keys()):
            runs = [r.get("reward", "?") for r in transfer_results[t]]
            print(f"  {t}: {runs}")
    elif "--json" in sys.argv:
        baseline_results = get_run_summaries(BASELINE_DIR)
        skill_results = get_run_summaries(SKILL_DIR)
        print(json.dumps({"tasks": [
            {"task_id": t, "baseline": baseline_results.get(t, []), "with_skill": skill_results.get(t, [])}
            for t in ALL_TASKS
        ]}, indent=2))
    else:
        all_results, missing_b, missing_s = collect_main()
        # Print summary table
        print(f"\n{'='*80}")
        print(f"{'Task':<12} {'Baseline avg':<20} {'Skill avg':<20} {'Delta':<20}")
        print(f"{'-'*80}")
        for t in all_results["tasks"]:
            base_rewards = [r["reward"] for r in t["baseline"] if r["reward"] is not None]
            sk_rewards = [r["reward"] for r in t["with_skill"] if r["reward"] is not None]
            base_avg = f"{sum(base_rewards)/len(base_rewards):.3f}" if base_rewards else "---"
            sk_avg = f"{sum(sk_rewards)/len(sk_rewards):.3f}" if sk_rewards else "---"
            if base_rewards and sk_rewards:
                delta = f"{sum(sk_rewards)/len(sk_rewards) - sum(base_rewards)/len(base_rewards):+.3f}"
            else:
                delta = "---"
            print(f"{t['task_id']:<12} {base_avg:<20} {sk_avg:<20} {delta:<20}")

if __name__ == "__main__":
    main()
