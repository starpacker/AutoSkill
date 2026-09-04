"""Evaluate best_skill on selected test tasks for BioMNIBench."""
import json, os, subprocess, sys, time, glob

# Config
OUT_ROOT = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458"
BEST_SKILL = os.path.join(OUT_ROOT, "best_skill.md")
EVAL_OUT = os.path.join(OUT_ROOT, "test_eval_10tasks")
HARNESS_DIR = "/tmp/my_claude_biomnibench_fixed"
BUN_BIN = "/tmp/bun_extract/bun-linux-x64/bun"
TASKS_DIR = "/data/yjh/biomnibench-organized"
SPLIT_FILE = os.path.join(OUT_ROOT, "_generated_splits/biomnibench_23-2-27_seed42/test/items.json")

# Selected test tasks
SELECTED_IDS = [
    "da-5-1",   # multi-omic-integration
    "da-20-3",  # pathway-enrichment
    "da-19-6",  # chromatin-profiling
    "da-17-3",  # differential-expression
    "da-18-1",  # mutation-analysis
    "da-8-2",   # association-testing
    "da-10-1",  # predictive-modeling
    "da-15-2",  # co-expression-networks
    "da-4-7",   # tcr-repertoire
    "da-12-2",  # pathway-enrichment
]

# Read skill content
with open(BEST_SKILL) as f:
    skill_content = f.read()

print(f"Skill length: {len(skill_content)} chars")
print(f"Output dir: {EVAL_OUT}")
os.makedirs(EVAL_OUT, exist_ok=True)

def run_task(task_id: str) -> dict:
    timestamp = f"test_eval_{task_id}_{int(time.time())}"
    run_dir = os.path.join(EVAL_OUT, timestamp)
    os.makedirs(run_dir, exist_ok=True)

    prompt_file = os.path.join(run_dir, "system_prompt.md")
    with open(prompt_file, "w") as f:
        f.write(skill_content)

    runs_subdir = os.path.join(EVAL_OUT, "runs", task_id)
    os.makedirs(runs_subdir, exist_ok=True)

    log_file = os.path.join(run_dir, "harness.log")

    cmd = [
        BUN_BIN, "src/harness/evaluation/cli.ts",
        "--task", task_id,
        "--tasks-dir", TASKS_DIR,
        "--runs-dir", runs_subdir,
        "--max-rounds", "3",
        "--timeout-seconds", "1200",
        "--concurrency", "1",
        "--temperature", "1.0",
        "--thinking", "disabled",
        "--timestamp", timestamp,
        "--system-prompt", prompt_file,
        "--quiet",
    ]

    print(f"  [{task_id}] Starting...")
    start = time.time()
    try:
        result = subprocess.run(
            cmd, cwd=HARNESS_DIR, capture_output=True, text=True, timeout=1260
        )
        elapsed = time.time() - start
        with open(log_file, "w") as f:
            f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n")
            f.write(f"\nExit code: {result.returncode}\nElapsed: {elapsed:.1f}s\n")

        # Find summary
        summary = None
        for entry in os.listdir(runs_subdir):
            if timestamp in entry:
                sp = os.path.join(runs_subdir, entry, "logs", "run_summary.json")
                if os.path.exists(sp):
                    with open(sp) as f:
                        summary = json.load(f)
                    break

        if summary:
            reward = summary.get("reward", 0.0)
            hard = 1 if reward >= 0.5 else 0
            print(f"  [{task_id}] DONE: reward={reward:.3f}, hard={hard}, elapsed={elapsed:.0f}s")
            return {"id": task_id, "hard": hard, "soft": reward, "reward": reward, "elapsed": elapsed}
        else:
            print(f"  [{task_id}] DONE (no summary): exit={result.returncode}, elapsed={elapsed:.0f}s")
            return {"id": task_id, "hard": 0, "soft": 0.0, "reward": 0.0, "error": "no_summary", "elapsed": elapsed}

    except subprocess.TimeoutExpired:
        elapsed = time.time() - start
        print(f"  [{task_id}] TIMEOUT ({elapsed:.0f}s)")
        return {"id": task_id, "hard": 0, "soft": 0.0, "reward": 0.0, "error": "timeout", "elapsed": elapsed}
    except Exception as e:
        elapsed = time.time() - start
        print(f"  [{task_id}] ERROR: {e}")
        return {"id": task_id, "hard": 0, "soft": 0.0, "reward": 0.0, "error": str(e), "elapsed": elapsed}


# Run all tasks sequentially
results = []
for task_id in SELECTED_IDS:
    r = run_task(task_id)
    results.append(r)
    # Save intermediate results
    with open(os.path.join(EVAL_OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=2)

# Summary
print("\n" + "="*60)
print("RESULTS SUMMARY")
print("="*60)
total_hard = sum(r.get("hard", 0) for r in results)
total_soft = sum(r.get("soft", 0.0) for r in results)
n = len(results)
print(f"  Tasks: {n}")
print(f"  Hard score (avg): {total_hard/n:.3f} ({total_hard}/{n})")
print(f"  Soft score (avg): {total_soft/n:.3f}")
print(f"\n  Per-task:")
for r in results:
    print(f"    {r['id']}: hard={r.get('hard','?')} soft={r.get('soft',0):.3f} elapsed={r.get('elapsed',0):.0f}s")
print(f"\nFull results saved to: {os.path.join(EVAL_OUT, 'results.json')}")