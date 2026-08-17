#!/usr/bin/env python3
"""
Run the approved 12-pair cross-category transfer screen with Gemini judge.

Solver: Vendor3/DeepSeek-V4-Flash
Judge:  Vendor2/Gemini-3.1-pro
Feedback to agent is handled by the harness and remains score-only.
"""

import argparse
import json
import os
import shutil
import subprocess
import threading
import time
from datetime import datetime
from pathlib import Path


BASE_DIR = Path("/data/yjh/skill-transfer-eval")
HARNESS_DIR = Path("/tmp/my_claude_biomnibench_fixed")
BUN = Path("/tmp/bun_extract/bun-linux-x64/bun")
TASKS_DIR = Path("/data/yjh/biomnibench-organized")
SKILLS_DIR = BASE_DIR / "skills"
GENERALIZED_SKILLS_DIR = BASE_DIR / "generalized_skills"
OUTPUT_DIR = BASE_DIR / "generalized"
LOGS_DIR = BASE_DIR / "logs"

SOLVER_MODEL = "Vendor3/DeepSeek-V4-Flash"
JUDGE_MODEL = "Vendor2/Gemini-3.1-pro"
SKILL_PREFIX = "generalized-cross-gemini"

PAIRS = [
    ("da-14-3", "da-17-5"),
    ("da-20-3", "da-17-3"),
    ("da-8-2", "da-13-6"),
    ("da-13-5", "da-17-5"),
    ("da-19-3", "da-13-6"),
    ("da-20-3", "da-4-7"),
    ("da-13-3", "da-15-7"),
    ("da-15-1", "da-17-3"),
    ("da-18-5", "da-19-6"),
    ("da-19-3", "da-26-4"),
    ("da-13-1", "da-20-4"),
    ("da-15-2", "da-18-7"),
]


def skill_name(source: str) -> str:
    return f"{SKILL_PREFIX}-{source}"


def deploy_skill(source: str, target: str) -> tuple[bool, str]:
    source_skill = GENERALIZED_SKILLS_DIR / source / "SKILL.md"
    if not source_skill.exists():
        return False, f"missing generalized skill: {source_skill}"

    name = skill_name(source)
    deploy_dir = SKILLS_DIR / target / "skills" / name
    deploy_dir.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source_skill, deploy_dir / "SKILL.md")

    metadata = {
        "source_task": source,
        "target_task": target,
        "deployed_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "generalized_skill_source": str(source_skill.parent),
        "unique_name": name,
        "judge_model": JUDGE_MODEL,
    }
    (deploy_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return True, str(deploy_dir)


def build_command(target: str, name: str, run_tag: str) -> list[str]:
    skill_dir = SKILLS_DIR / target / "skills"
    return [
        str(BUN),
        "src/harness/evaluation/cli.ts",
        "--task",
        target,
        "--tasks-dir",
        str(TASKS_DIR),
        "--runs-dir",
        str(OUTPUT_DIR),
        "--max-rounds",
        "5",
        "--timeout-seconds",
        "7200",
        "--concurrency",
        "1",
        "--temperature",
        "1",
        "--thinking",
        "disabled",
        "--timestamp",
        run_tag,
        "--quiet",
        "--enable-skills",
        "--skills-dir",
        str(skill_dir),
        "--skill-name",
        name,
        "--max-active-skills",
        "1",
    ]


def run_pair(source: str, target: str, timestamp: str, env: dict[str, str]) -> dict:
    name = skill_name(source)
    run_tag = f"{timestamp}_{name}_rep1"
    label = f"{source}->{target}"
    cmd = build_command(target, name, run_tag)
    started = time.time()

    print(f"[START] {label} skill={name}", flush=True)
    try:
        result = subprocess.run(
            cmd,
            cwd=str(HARNESS_DIR),
            env=env,
            text=True,
            capture_output=True,
            timeout=7500,
        )
        elapsed = round(time.time() - started, 1)
        status = "OK" if result.returncode == 0 else f"FAIL({result.returncode})"
        print(f"[DONE] {label} {status} elapsed={elapsed}s", flush=True)
        if result.stderr:
            print(f"[STDERR] {label} {result.stderr[-800:]}", flush=True)
        return {
            "source": source,
            "target": target,
            "skill_name": name,
            "run_tag": run_tag,
            "status": status,
            "returncode": result.returncode,
            "elapsed_seconds": elapsed,
        }
    except subprocess.TimeoutExpired:
        elapsed = round(time.time() - started, 1)
        print(f"[TIMEOUT] {label} elapsed={elapsed}s", flush=True)
        return {
            "source": source,
            "target": target,
            "skill_name": name,
            "run_tag": run_tag,
            "status": "TIMEOUT",
            "returncode": -1,
            "elapsed_seconds": elapsed,
        }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-concurrent", type=int, default=2)
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Cross-category Gemini screen")
    print(f"solver={SOLVER_MODEL}")
    print(f"judge={JUDGE_MODEL}")
    print(f"pairs={len(PAIRS)} max_concurrent={args.max_concurrent}")

    deployed = []
    for source, target in PAIRS:
        ok, message = deploy_skill(source, target)
        print(f"[DEPLOY] {source}->{target} {ok} {message}")
        if not ok:
            raise FileNotFoundError(message)
        deployed.append({"source": source, "target": target, "skill_name": skill_name(source)})

    if args.dry_run:
        print(json.dumps({"timestamp": timestamp, "pairs": deployed}, indent=2))
        return 0

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_API_KEY", "00gcclg9l39y9p01000dhjzolag1q2hk00901kh1")
    env["ANTHROPIC_BASE_URL"] = env.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
    env["ANTHROPIC_MODEL"] = SOLVER_MODEL
    env["QWEN_API_KEY"] = env.get("QWEN_API_KEY", env["ANTHROPIC_API_KEY"])
    env["QWEN_BASE_URL"] = env.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
    env["QWEN_MODEL"] = JUDGE_MODEL

    results = []
    lock = threading.Lock()
    queue = list(PAIRS)

    def worker() -> None:
        while True:
            with lock:
                if not queue:
                    return
                source, target = queue.pop(0)
            result = run_pair(source, target, timestamp, env)
            with lock:
                results.append(result)

    workers = [threading.Thread(target=worker, daemon=False) for _ in range(args.max_concurrent)]
    for thread in workers:
        thread.start()
    for thread in workers:
        thread.join()

    summary = {
        "timestamp": timestamp,
        "solver_model": SOLVER_MODEL,
        "judge_model": JUDGE_MODEL,
        "pairs": deployed,
        "results": results,
    }
    summary_path = LOGS_DIR / f"cross_gemini_12_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[SUMMARY] {summary_path}")
    return 0 if all(item["returncode"] == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
