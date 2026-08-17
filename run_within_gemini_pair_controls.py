#!/usr/bin/env python3
"""Run paired within-category Gemini controls for generalized vs raw skills."""

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
GENERALIZED_SKILLS_DIR = BASE_DIR / "generalized_skills"
SKILLS_DIR = BASE_DIR / "skills"
OUTPUT_DIR = BASE_DIR / "generalized"
LOGS_DIR = BASE_DIR / "logs"

SOLVER_MODEL = "Vendor3/DeepSeek-V4-Flash"
JUDGE_MODEL = "Vendor2/Gemini-3.1-pro"
DEFAULT_ATTEMPTS = 6
RETRY_BACKOFF_SECONDS = 180
RETRYABLE_FAILURE_MARKERS = (
    "model is overloaded",
    "please try again later",
    "no available channel",
)

PAIRS = [
    ("da-8-1", "da-8-3"),
    ("da-4-1", "da-4-7"),
    ("da-13-1", "da-13-6"),
    ("da-13-1", "da-13-5"),
    ("da-15-1", "da-15-7"),
    ("da-18-5", "da-18-7"),
    ("da-19-3", "da-19-4"),
]


def raw_skill_dir(source: str) -> Path:
    return RAW_BUNDLES_DIR / source / "skills" / f"oracle-{source}"


def build_arms(source: str, target: str) -> list[dict]:
    return [
        {
            "source": source,
            "target": target,
            "control_type": "generalized",
            "skill_name": f"generalized-within-gemini-{source}",
            "source_dir": GENERALIZED_SKILLS_DIR / source,
        },
        {
            "source": source,
            "target": target,
            "control_type": "raw",
            "skill_name": f"raw-within-gemini-{source}",
            "source_dir": raw_skill_dir(source),
        },
    ]


def attempt_run_tag(timestamp: str, skill_name: str, control_type: str, attempt: int) -> str:
    stem = f"{timestamp}_{skill_name}_{control_type}"
    if attempt == 1:
        return f"{stem}_rep1"
    return f"{stem}_attempt{attempt}_rep1"


def is_retryable_failure_text(text: str) -> bool:
    lowered = text.lower()
    return any(marker in lowered for marker in RETRYABLE_FAILURE_MARKERS)


def deploy_arm(arm: dict) -> tuple[bool, str]:
    source_dir = Path(arm["source_dir"])
    if not (source_dir / "SKILL.md").exists():
        return False, f"missing skill: {source_dir / 'SKILL.md'}"

    deploy_dir = SKILLS_DIR / arm["target"] / "skills" / arm["skill_name"]
    deploy_dir.parent.mkdir(parents=True, exist_ok=True)
    if deploy_dir.exists():
        shutil.rmtree(deploy_dir)
    shutil.copytree(source_dir, deploy_dir)

    metadata = {
        "source_task": arm["source"],
        "target_task": arm["target"],
        "deployed_at": datetime.now().strftime("%Y%m%d_%H%M%S"),
        "skill_source": str(source_dir),
        "unique_name": arm["skill_name"],
        "solver_model": SOLVER_MODEL,
        "judge_model": JUDGE_MODEL,
        "control_type": f"within_{arm['control_type']}_skill",
    }
    (deploy_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    return True, str(deploy_dir)


def build_command(target: str, skill_name: str, run_tag: str) -> list[str]:
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
        str(SKILLS_DIR / target / "skills"),
        "--skill-name",
        skill_name,
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


def read_run_failure_text(target: str, run_tag: str) -> str:
    log_dir = OUTPUT_DIR / f"{target}_{run_tag}" / "logs"
    parts = []
    for name in ("trajectory.clean.jsonl", "run_summary.json", "run_events.jsonl"):
        path = log_dir / name
        if path.exists():
            parts.append(path.read_text(errors="replace"))
    return "\n".join(parts)


def run_arm(arm: dict, timestamp: str, env: dict[str, str], attempts: int) -> dict:
    label = f"{arm['source']}->{arm['target']}:{arm['control_type']}"
    last_result = {}
    for attempt in range(1, attempts + 1):
        run_tag = attempt_run_tag(timestamp, arm["skill_name"], arm["control_type"], attempt)
        started = time.time()
        print(f"[START] {label} skill={arm['skill_name']} attempt={attempt}/{attempts}", flush=True)
        try:
            result = subprocess.run(
                build_command(arm["target"], arm["skill_name"], run_tag),
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
                "source": arm["source"],
                "target": arm["target"],
                "control_type": arm["control_type"],
                "skill_name": arm["skill_name"],
                "run_tag": run_tag,
                "status": status,
                "returncode": result.returncode,
                "elapsed_seconds": elapsed,
                "attempt": attempt,
            }
            if result.returncode == 0:
                return last_result
            failure_text = "\n".join([result.stdout, result.stderr, read_run_failure_text(arm["target"], run_tag)])
            if attempt < attempts and is_retryable_failure_text(failure_text):
                print(f"[RETRY] {label} retryable overload; sleeping {RETRY_BACKOFF_SECONDS}s", flush=True)
                time.sleep(RETRY_BACKOFF_SECONDS)
                continue
            return last_result
        except subprocess.TimeoutExpired:
            elapsed = round(time.time() - started, 1)
            print(f"[TIMEOUT] {label} attempt={attempt}/{attempts} elapsed={elapsed}s", flush=True)
            return {
                "source": arm["source"],
                "target": arm["target"],
                "control_type": arm["control_type"],
                "skill_name": arm["skill_name"],
                "run_tag": run_tag,
                "status": "TIMEOUT",
                "returncode": -1,
                "elapsed_seconds": elapsed,
                "attempt": attempt,
            }
    return last_result


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-concurrent", type=int, default=2)
    parser.add_argument("--attempts", type=int, default=DEFAULT_ATTEMPTS)
    args = parser.parse_args()

    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    arms = [arm for pair in PAIRS for arm in build_arms(*pair)]

    print("Within-category Gemini paired controls")
    print(f"solver={SOLVER_MODEL}")
    print(f"judge={JUDGE_MODEL}")
    print(f"pairs={len(PAIRS)} arms={len(arms)} max_concurrent={args.max_concurrent} attempts={args.attempts}")

    deployed = []
    for arm in arms:
        ok, message = deploy_arm(arm)
        print(f"[DEPLOY] {arm['source']}->{arm['target']} {arm['control_type']} {ok} {message}", flush=True)
        if not ok:
            raise FileNotFoundError(message)
        deployed.append({k: arm[k] for k in ("source", "target", "control_type", "skill_name")})

    if args.dry_run:
        print(json.dumps({"timestamp": timestamp, "arms": deployed}, indent=2))
        return 0

    queue = list(arms)
    results = []
    lock = threading.Lock()
    env = make_env()

    def worker() -> None:
        while True:
            with lock:
                if not queue:
                    return
                arm = queue.pop(0)
            result = run_arm(arm, timestamp, env, args.attempts)
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
        "control_type": "within_category_paired_generalized_vs_raw",
        "pairs": PAIRS,
        "arms": deployed,
        "results": results,
    }
    summary_path = LOGS_DIR / f"within_gemini_pair_controls_summary_{timestamp}.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"[SUMMARY] {summary_path}", flush=True)
    return 0 if all(item["returncode"] == 0 for item in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
