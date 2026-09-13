#!/usr/bin/env python3
"""
run_transfer_skill_eval.py

Batch runner for within-domain and cross-domain transfer-skill evaluations.

Usage:
  python3 run_transfer_skill_eval.py --mode within-domain    # Run within-domain evals
  python3 run_transfer_skill_eval.py --mode cross-domain     # Run cross-domain evals
  python3 run_transfer_skill_eval.py --mode all              # Run both
  python3 run_transfer_skill_eval.py --mode within-domain --dry-run  # Preview only
  python3 run_transfer_skill_eval.py --mode within-domain --max-concurrent 2  # Control parallelism
"""

import json, os, sys, subprocess, time, argparse, threading
from pathlib import Path
from datetime import datetime
from collections import defaultdict

BASE_DIR = Path("/data/yjh/skill-transfer-eval")
HARNESS_DIR = Path("/tmp/my_claude_biomnibench_fixed")
BUN = Path("/tmp/bun_extract/bun-linux-x64/bun")
TASKS_DIR = Path("/data/yjh/biomnibench-organized")
BUNDLES_DIR = Path("/data/yjh/biomnibench-skill-bundles")
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "generalized"

# Within-domain: (train_source, target_task, skill_name)
WITHIN_DOMAIN = [
    # da-1: train da-1-3 → test da-1-4
    ("da-1-3", "da-1-4", "generalized-transfer"),
    # da-4: train da-4-1, da-4-6 → test da-4-7
    ("da-4-1", "da-4-7", "generalized-transfer"),
    ("da-4-6", "da-4-7", "generalized-transfer"),
    # da-8: train da-8-1, da-8-2 → test da-8-3
    ("da-8-1", "da-8-3", "generalized-transfer"),
    ("da-8-2", "da-8-3", "generalized-transfer"),
    # da-13: train da-13-1, da-13-3 → test da-13-5, da-13-6
    ("da-13-1", "da-13-5", "generalized-transfer"),
    ("da-13-3", "da-13-5", "generalized-transfer"),
    ("da-13-1", "da-13-6", "generalized-transfer"),
    ("da-13-3", "da-13-6", "generalized-transfer"),
    # da-14: train da-14-1, da-14-3 → test da-14-8
    ("da-14-1", "da-14-8", "generalized-transfer"),
    ("da-14-3", "da-14-8", "generalized-transfer"),
    # da-15: train da-15-1, da-15-2 → test da-15-7, da-15-8
    ("da-15-1", "da-15-7", "generalized-transfer"),
    ("da-15-2", "da-15-7", "generalized-transfer"),
    ("da-15-1", "da-15-8", "generalized-transfer"),
    ("da-15-2", "da-15-8", "generalized-transfer"),
    # da-17: train da-17-1 → test da-17-3, da-17-5 (already deployed)
    ("da-17-1", "da-17-3", "generalized-transfer"),
    ("da-17-1", "da-17-5", "generalized-transfer"),
    # da-18: train da-18-1, da-18-5 → test da-18-7
    ("da-18-1", "da-18-7", "generalized-transfer"),
    ("da-18-5", "da-18-7", "generalized-transfer"),
    # da-19: train da-19-1, da-19-3 → test da-19-4, da-19-6
    ("da-19-1", "da-19-4", "generalized-transfer"),
    ("da-19-3", "da-19-4", "generalized-transfer"),
    ("da-19-1", "da-19-6", "generalized-transfer"),
    ("da-19-3", "da-19-6", "generalized-transfer"),
    # da-20: train da-20-1, da-20-3 → test da-20-4
    ("da-20-1", "da-20-4", "generalized-transfer"),
    ("da-20-3", "da-20-4", "generalized-transfer"),
    # da-26: train da-26-2 → test da-26-4 (already deployed)
    ("da-26-2", "da-26-4", "generalized-transfer"),
    # da-5: train da-5-1 → test da-5-3 (already deployed)
    ("da-5-1", "da-5-3", "generalized-transfer"),
]

# Cross-domain: (source, target, skill_name)
CROSS_DOMAIN = [
    ("da-5-1", "da-18-7", "generalized-cross-da-5-1"),
    ("da-6-2", "da-20-4", "generalized-cross-da-6-2"),
    ("da-8-1", "da-14-8", "generalized-cross-da-8-1"),
    ("da-13-5", "da-26-4", "generalized-cross-da-13-5"),
]

# Base environment
ENV = os.environ.copy()
ENV["ANTHROPIC_API_KEY"] = ENV.get("ANTHROPIC_API_KEY") or ENV.get("SKILL_TRANSFER_API_KEY", "")
ENV["ANTHROPIC_BASE_URL"] = "https://api.gpugeek.com"
ENV["ANTHROPIC_MODEL"] = "Vendor3/DeepSeek-V4-Flash"
ENV["QWEN_MODEL"] = "Vendor2/Gemini-3.1-pro"

TIMESTAMP = datetime.now().strftime("%Y%m%d_%H%M%S")
REPS = 2  # Number of repetitions per task


def get_skill_dir(target_task, skill_name):
    """Get the skills directory for a given target task and skill."""
    skill_path = SKILLS_DIR / target_task / "skills"
    if not (skill_path / skill_name / "SKILL.md").exists():
        return None
    return skill_path


def build_command(target_task, skill_name, rep):
    """Build the evaluation command for a single run."""
    skill_dir = get_skill_dir(target_task, skill_name)
    if not skill_dir:
        return None

    run_suffix = f"{TIMESTAMP}_{skill_name}_rep{rep}"

    cmd = [
        str(BUN),
        "src/harness/evaluation/cli.ts",
        "--task", target_task,
        "--tasks-dir", str(TASKS_DIR),
        "--runs-dir", str(OUTPUT_DIR),
        "--max-rounds", "5",
        "--timeout-seconds", "7200",
        "--concurrency", "1",
        "--temperature", "1",
        "--thinking", "disabled",
        "--timestamp", run_suffix,
        "--quiet",
        "--enable-skills",
        "--skills-dir", str(skill_dir),
        "--skill-name", skill_name,
        "--max-active-skills", "1",
    ]
    return cmd


def run_single_eval(cmd, task_label, results):
    """Run a single evaluation and record the result."""
    print(f"  Starting: {task_label}")
    start = time.time()
    try:
        result = subprocess.run(
            cmd,
            cwd=str(HARNESS_DIR),
            capture_output=True,
            text=True,
            timeout=7200 + 300,  # 2h + 5min buffer
            env=ENV,
        )
        elapsed = time.time() - start
        rc = result.returncode
        stdout_tail = result.stdout[-500:] if result.stdout else ""
        stderr_tail = result.stderr[-500:] if result.stderr else ""

        status = "OK" if rc == 0 else f"FAIL(rc={rc})"
        print(f"  ⏱ {elapsed:.0f}s {status}: {task_label}")

        results.append({
            "task_label": task_label,
            "returncode": rc,
            "elapsed": elapsed,
            "stdout_tail": stdout_tail,
            "stderr_tail": stderr_tail,
        })
    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"  ⏱ {elapsed:.0f}s TIMEOUT: {task_label}")
        results.append({
            "task_label": task_label,
            "returncode": -1,
            "elapsed": elapsed,
            "stdout_tail": "",
            "stderr_tail": "TIMEOUT",
        })
    except Exception as e:
        print(f"  ❌ ERROR: {task_label}: {e}")
        results.append({
            "task_label": task_label,
            "returncode": -2,
            "elapsed": 0,
            "stdout_tail": "",
            "stderr_tail": str(e),
        })


def run_batch(tasks, mode_name, max_concurrent=2):
    """Run a batch of evaluations with limited concurrency."""
    results = []
    threads = []
    lock = threading.Lock()

    def worker(task_item):
        source, target, skill_name, rep = task_item
        label = f"{source}→{target} ({skill_name}) rep{rep}"
        cmd = build_command(target, skill_name, rep)
        if cmd is None:
            print(f"  ⚠ SKIPPED (no skill file): {label}")
            with lock:
                results.append({
                    "task_label": label,
                    "returncode": -3,
                    "elapsed": 0,
                    "stdout_tail": "",
                    "stderr_tail": "SKIPPED: no skill file",
                })
            return
        run_single_eval(cmd, label, results)

    # Build task list
    task_items = []
    for source, target, skill_name in tasks:
        skill_dir = get_skill_dir(target, skill_name)
        if not skill_dir:
            print(f"  ⚠ Skill not found: {target} / {skill_name}")
            continue
        for rep in range(1, REPS + 1):
            task_items.append((source, target, skill_name, rep))

    print(f"\n{'='*70}")
    print(f"  {mode_name}: {len(task_items)} runs ({len(tasks)} unique tasks × {REPS} reps)")
    print(f"  Max concurrent: {max_concurrent}")
    print(f"{'='*70}\n")

    # Run with thread pool
    for i in range(0, len(task_items), max_concurrent):
        batch = task_items[i:i+max_concurrent]
        threads = []
        for item in batch:
            t = threading.Thread(target=worker, args=(item,))
            t.start()
            threads.append(t)
        for t in threads:
            t.join()

    # Print summary
    print(f"\n{'='*70}")
    print(f"  {mode_name} — Complete")
    print(f"{'='*70}")
    ok = sum(1 for r in results if r["returncode"] == 0)
    fail = sum(1 for r in results if r["returncode"] not in (0, -3))
    skip = sum(1 for r in results if r["returncode"] == -3)
    total = sum(1 for r in results if r["returncode"] != -3)
    avg_time = sum(r["elapsed"] for r in results if r["returncode"] == 0) / max(ok, 1)
    print(f"  OK: {ok}/{total} | Failed: {fail} | Skipped: {skip}")
    print(f"  Avg time per OK run: {avg_time:.0f}s")

    return results


def main():
    parser = argparse.ArgumentParser(description="Run transfer-skill evaluations")
    parser.add_argument("--mode", choices=["within-domain", "cross-domain", "all"], default="all")
    parser.add_argument("--max-concurrent", type=int, default=2, help="Max concurrent evaluations")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--reps", type=int, default=2, help="Repetitions per task")
    args = parser.parse_args()

    global REPS
    REPS = args.reps

    all_results = {}

    if args.mode in ("within-domain", "all"):
        all_results["within-domain"] = run_batch(WITHIN_DOMAIN, "Within-Domain Transfer", args.max_concurrent)

    if args.mode in ("cross-domain", "all"):
        all_results["cross-domain"] = run_batch(CROSS_DOMAIN, "Cross-Domain Transfer", args.max_concurrent)

    # Save results
    results_path = BASE_DIR / "summary" / f"transfer_eval_results_{TIMESTAMP}.json"
    results_path.parent.mkdir(parents=True, exist_ok=True)
    results_path.write_text(json.dumps(all_results, indent=2))
    print(f"\nResults saved to: {results_path}")

    return all_results


if __name__ == "__main__":
    main()
