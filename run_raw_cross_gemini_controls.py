#!/usr/bin/env python3
"""
Run raw source-skill transfer controls for Gemini-scored cross-category pairs.

This copies the original oracle skill from each source task without
generalization, then evaluates it on the target task with the same solver,
judge, and feedback settings used by the generalized cross run.
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
RAW_BUNDLES_DIR = Path("/data/yjh/biomnibench-skill-bundles")
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "generalized"
LOGS_DIR = BASE_DIR / "logs"

SOLVER_MODEL = "Vendor3/DeepSeek-V4-Flash"
JUDGE_MODEL = "Vendor2/Gemini-3.1-pro"
SKILL_PREFIX = "raw-cross-gemini"
DEFAULT_ATTEMPTS = 3
RETRY_BACKOFF_SECONDS = 180
RETRYABLE_FAILURE_MARKERS = (
    "model is overloaded",
    "please try again later",
)

PAIRS = [
    ("da-14-3", "da-17-5"),
    ("da-19-3", "da-13-6"),
    ("da-13-5", "da-17-5"),
    ("da-13-3", "da-15-7"),
    ("da-15-1", "da-17-3"),
    ("da-18-5", "da-19-6"),
    ("da-20-3", "da-4-7"),
]


def skill_name(source: str) -> str:
    return f"{SKILL_PREFIX}-{source}"


def source_skill_path(source: str) -> Path:
    return RAW_BUNDLES_DIR / source / "skills" / f"oracle-{source}" / "SKILL.md"


def attempt_run_tag(timestamp: str, name: str, attempt: int) -> str:
    if attempt == 1:
        return f"{timestamp}_{name}_rep1"
    return f"{timestamp}_{name}_attempt{attempt}_rep1"


def is_retryable_failure_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in RETRYABLE_FAILURE_MARKERS)


def read_run_failure_text(target: str, run_tag: str) -> str:
    run_dir = OUTPUT_DIR / f"{target}_{run_tag}" / "logs"
    parts = []
    for filename in ("trajectory.clean.jsonl", "run_summary.json", "run_events.jsonl"):
        path = run_dir / filename
        if path.exists():
            try:
                parts.append(path.read_text(errors="replace"))
            except OSError as exc:
                parts.append(str(exc))
    return "\n".join(parts)


def deploy_skill(source: str, target: str) -> tuple[bool, str]:
    source_skill = source_skill_path(source)
    if not source_skill.exists():
        return False, f"missing raw source skill: {source_skill}"

    name = skill_name(source)
    deploy_dir = SKILLS_DIR / target / "skills" / name
    deploy_dir.parent.mkdir(parents=True, exist_ok=True)
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    shutil.copytree(source_skill.parent, deploy_dir)

    metadata = {
        "source_task": source,
        "target_task": target,
        "deployed_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "raw_skill_source": str(source_skill.parent),
        "unique_name": name,
        "solver_model": SOLVER_MODEL,
        "judge_model": JUDGE_MODEL,
        "control_type": "raw_source_oracle_skill",
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


def make_env() -> dict[str, str]:
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = env.get("ANTHROPIC_API_KEY", "00gcclg9l39y9p01000dhjzolag1q2hk00901kh1")
    env["ANTHROPIC_BASE_URL"] = env.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
    env["ANTHROPIC_MODEL"] = SOLVER_MODEL
    env["QWEN_API_KEY"] = env.get("QWEN_API_KEY", env["ANTHROPIC_API_KEY"])
    env["QWEN_BASE_URL"] = env.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
    env["QWEN_MODEL"] = JUDGE_MODEL
    return env


def run_pair(source: str, target: str, timestamp: str, env: dict[str, str], attempts: int) -> dict:
    name = skill_name(source)
    label = f"{source}->{target}"

    last_result = {}
    for attempt in range(1, attempts + 1):
        run_tag = attempt_run_tag(timestamp, name, attempt)
        print(f"[START] {label} skill={name} attempt={attempt}/{attempts}", flush=True)
        started = time.time()
        try:
            result = subprocess.run(
                build_command(target, name, run_tag),
                cwd=str(HARNESS_DIR),
                env=env,
                text=True,
                capture_output=True,
                timeout=7500,
            )
            elapsed = round(time.time() - started, 1)
            status = "OK" if result.returncode == 0 else f"FAIL({result.returncode})"
            print(f"[DONE] {label} {status} attempt={attempt}/{attempts} elapsed={elapsed}s", flush=True)
            if result.stderr:
                print(f"[STDERR] {label} {result.stderr[-800:]}", flush=True)
            last_result = {
                "source": source,
                "target": target,
                "skill_name": name,
                "run_tag": run_tag,
                "status": status,
                "returncode": result.returncode,
                "elapsed_seconds": elapsed,
                "attempt": attempt,
            }
            if result.returncode == 0:
                return last_result

            failure_text = "\n".join([result.stdout, result.stderr, read_run_failure_text(target, run_tag)])
            if attempt < attempts and is_retryable_failure_text(failure_text):
                print(f"[RETRY] {label} retryable overload failure; sleeping {RETRY_BACKOFF_SECONDS}s", flush=True)
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return last_result
        except subprocess.TimeoutExpired:
            elapsed = round(time.time() - started, 1)
            print(f"[TIMEOUT] {label} attempt={attempt}/{attempts} elapsed={elapsed}s", flush=True)
            last_result = {
                "source": source,
                "target": target,
                "skill_name": name,
                "run_tag": run_tag,
                "status": "TIMEOUT",
                "returncode": -1,
                "elapsed_seconds": elapsed,
                "attempt": attempt,
            }
            return last_result
    return last_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-concurrent", type=int, default=2)
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    print("Raw source-skill Gemini control")
    print(f"solver={SOLVER_MODEL}")
    print(f"judge={JUDGE_MODEL}")
    print(f"pairs={len(PAIRS)} max_concurrent={args.max_concurrent} attempts={args.attempts}")

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

    queue = list(PAIRS)
    results = []
    lock = threading.Lock()
    env = make_env()

    def worker() -> None:
        while True:
            with lock:
                if not queue:
                    return
                source, target = queue.pop(0)
            result = run_pair(source, target, timestamp, env, args.attempts)
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
        "control_type": "raw_source_oracle_skill",
        "pairs": deployed,
        "results": results,
    }
    summary_path = LOGS_DIR / f"raw_cross_gemini_controls_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[SUMMARY] {summary_path}")
    return 0 if all(item["returncode"] == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
