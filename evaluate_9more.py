"""Evaluate SkillOpt best_skill.md on 9 additional tasks that have V10+GT+BL data."""
import json, os, subprocess, sys, time, glob, re

# Config
OUT_ROOT = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458"
BEST_SKILL = os.path.join(OUT_ROOT, "best_skill.md")
EVAL_OUT = os.path.join(OUT_ROOT, "test_eval_9more")
HARNESS_DIR = "/tmp/my_claude_biomnibench_fixed"
BUN_BIN = "/tmp/bun_extract/bun-linux-x64/bun"
TASKS_DIR = "/data/yjh/biomnibench-organized"

# 9 tasks to evaluate (have V10+GT+BL, missing SkillOpt)
SELECTED_IDS = [
    "da-13-6",  # 0.60/1.00/1.00/0.60
    "da-15-7",  # 0.70/0.90/0.77/0.70
    "da-15-8",  # 0.63/0.73/0.80/0.63
    "da-20-4",  # 0.15/0.85/0.90/0.00
    "da-24-3",  # 0.25/0.80/1.00/1.00
    "da-25-1",  # 0.48/0.56/0.86/0.79
    "da-26-4",  # 0.54/0.90/0.75/0.64
    "da-8-3",   # 0.60/0.95/0.96/0.82
    "da-9-1",   # 0.49/1.00/0.83/0.66
]

# Read skill content
with open(BEST_SKILL) as f:
    skill_content = f.read()

print(f"Skill length: {len(skill_content)} chars")
print(f"Output dir: {EVAL_OUT}")
print(f"Tasks to evaluate: {SELECTED_IDS}")
print()

os.makedirs(EVAL_OUT, exist_ok=True)

# Check if any already have results
for task_id in SELECTED_IDS:
    existing = glob.glob(os.path.join(EVAL_OUT, f"test_eval_{task_id}_*", "harness.log"))
    if existing:
        # Check latest
        latest = sorted(existing)[-1]
        with open(latest) as f:
            c = f.read()
        m = re.search(r'"reward": ([0-9.]+)', c)
        if m:
            reward = float(m.group(1))
            print(f"  ⏭️  {task_id}: already has result reward={reward} (from {latest})")
            # Check if we should skip
            if reward > 0:
                print(f"     -> Skipping (already has non-zero result)")

# Filter to only tasks without results
to_run = []
for task_id in SELECTED_IDS:
    existing = glob.glob(os.path.join(EVAL_OUT, f"test_eval_{task_id}_*", "harness.log"))
    should_skip = False
    for ex in existing:
        with open(ex) as f:
            c = f.read()
        m = re.search(r'"reward": ([0-9.]+)', c)
        if m and float(m.group(1)) > 0:
            should_skip = True
            break
    if not should_skip:
        to_run.append(task_id)

print(f"\nTo run: {len(to_run)} tasks")
if not to_run:
    print("All tasks already have results!")
    sys.exit(0)

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

# Run sequentially
results = []
for i, task_id in enumerate(to_run):
    print(f"\n--- [{i+1}/{len(to_run)}] {task_id} ---")
    res = run_task(task_id)
    results.append(res)
    
    # Save intermediate results
    with open(os.path.join(EVAL_OUT, "results.json"), "w") as f:
        json.dump(results, f, indent=2)
    
    # Brief pause between tasks
    time.sleep(2)

# Final summary
print(f"\n{'='*60}")
print(f"{'FINAL RESULTS':^60}")
print(f"{'='*60}")
print(f"{'Task':<10} {'Reward':<10} {'Hard':<10} {'Elapsed':<10}")
print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10}")
for r in results:
    task = r.get("id", "?")
    reward = r.get("reward", 0)
    hard = r.get("hard", 0)
    elapsed = r.get("elapsed", 0)
    print(f"{task:<10} {reward:<10.3f} {hard:<10} {elapsed:<10.0f}s")

avg_reward = sum(r.get("reward", 0) for r in results) / len(results) if results else 0
print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10}")
print(f"{'AVG':<10} {avg_reward:<10.3f}")

# Save final
with open(os.path.join(EVAL_OUT, "results.json"), "w") as f:
    json.dump(results, f, indent=2)
print(f"\nResults saved to {EVAL_OUT}/results.json")