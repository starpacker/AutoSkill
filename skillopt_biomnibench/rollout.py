"""BioMNIBench rollout — calls the harness CLI as a subprocess for each task."""
from __future__ import annotations

import json
import os
import subprocess
import time

HARNESS_DIR = "/tmp/my_claude_biomnibench_fixed"
BUN_BIN = "/tmp/bun_extract/bun-linux-x64/bun"
TASKS_DIR = "/data/yjh/biomnibench-organized"


def _run_harness(
    task_id: str,
    skill_content: str,
    out_dir: str,
    *,
    max_rounds: int = 3,
    timeout_seconds: int = 7200,
    temperature: float = 1.0,
) -> dict:
    """Run harness CLI for a single task with skill injected as system prompt."""
    timestamp = f"skillopt_{task_id}_{int(time.time())}"
    run_dir = os.path.join(out_dir, timestamp)
    os.makedirs(run_dir, exist_ok=True)

    # Write skill content as a temporary system prompt file
    prompt_file = os.path.join(run_dir, "system_prompt.md")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(skill_content)

    # Create a unique runs-dir subfolder for this task
    runs_subdir = os.path.join(out_dir, "runs", task_id)
    os.makedirs(runs_subdir, exist_ok=True)

    log_file = os.path.join(run_dir, "harness.log")

    cmd = [
        BUN_BIN, "src/harness/evaluation/cli.ts",
        "--task", task_id,
        "--tasks-dir", TASKS_DIR,
        "--runs-dir", runs_subdir,
        "--max-rounds", str(max_rounds),
        "--timeout-seconds", str(timeout_seconds),
        "--concurrency", "1",
        "--temperature", str(temperature),
        "--thinking", "disabled",
        "--timestamp", timestamp,
        "--system-prompt", prompt_file,
        "--quiet",
    ]

    start = time.time()
    result = subprocess.run(
        cmd,
        cwd=HARNESS_DIR,
        capture_output=True,
        text=True,
        timeout=timeout_seconds + 60,
    )
    elapsed = time.time() - start

    # Save logs
    with open(log_file, "w", encoding="utf-8") as f:
        f.write(f"STDOUT:\n{result.stdout}\n\nSTDERR:\n{result.stderr}\n")
        f.write(f"\nExit code: {result.returncode}\nElapsed: {elapsed:.1f}s\n")

    # Find run_summary.json
    summary = _find_summary(runs_subdir, timestamp)

    if summary:
        return summary
    return {
        "id": task_id,
        "reward": 0.0,
        "hard": 0,
        "soft": 0.0,
        "error": f"harness exit={result.returncode}, no summary found",
        "elapsed": elapsed,
    }


def _find_summary(runs_dir: str, timestamp: str) -> dict | None:
    """Find run_summary.json for the given timestamp in runs_dir."""
    try:
        for entry in os.listdir(runs_dir):
            if timestamp in entry:
                summary_path = os.path.join(
                    runs_dir, entry, "logs", "run_summary.json"
                )
                if os.path.exists(summary_path):
                    with open(summary_path, "r") as f:
                        return json.load(f)
    except (FileNotFoundError, PermissionError):
        pass
    return None


def run_batch(
    items: list[dict],
    out_root: str,
    skill_content: str,
    *,
    max_rounds: int = 3,
    exec_timeout: int = 7200,
    temperature: float = 1.0,
    workers: int = 2,
) -> list[dict]:
    """Run a batch of BioMNIBench tasks with the given skill."""
    results = []
    for i, item in enumerate(items):
        task_id = item["id"]
        print(f"  [rollout {i+1}/{len(items)}] Running {task_id}...")
        try:
            summary = _run_harness(
                task_id=task_id,
                skill_content=skill_content,
                out_dir=out_root,
                max_rounds=max_rounds,
                timeout_seconds=exec_timeout,
                temperature=temperature,
            )

            reward = summary.get("reward", 0.0)
            hard = 1 if reward >= 0.5 else 0

            results.append({
                "id": task_id,
                "hard": hard,
                "soft": reward,
                "reward": reward,
                "summary": summary,
                "elapsed": summary.get("elapsed", 0),
            })
            print(f"  [rollout] {task_id}: reward={reward:.3f}, hard={hard}")

        except subprocess.TimeoutExpired:
            print(f"  [rollout] {task_id}: TIMEOUT ({exec_timeout}s)")
            results.append({
                "id": task_id,
                "hard": 0,
                "soft": 0.0,
                "reward": 0.0,
                "error": "timeout",
            })
        except Exception as e:
            print(f"  [rollout] {task_id}: ERROR: {e}")
            results.append({
                "id": task_id,
                "hard": 0,
                "soft": 0.0,
                "reward": 0.0,
                "error": str(e),
            })

    return results