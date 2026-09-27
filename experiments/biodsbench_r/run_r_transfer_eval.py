#!/usr/bin/env python3
"""
run_r_transfer_eval.py — Transfer evaluation for R skill-transfer.

For each of the 24 test tasks, runs 3 arms:
  1. noskill  : vanilla harness (no skill)
  2. transfer : deploy top-1 selected train generalized skill
  3. oracle   : deploy the task's OWN pruned oracle skill (upper bound)

Reads:
  - r_skill_selections.json (from select_r_skills_simple.py)
  - generalized_r/{tid}/SKILL.md (train generalized skills)
  - output/biodsbench-lifecycle/{tid}/prune/baseline/variant/skills/oracle-{tid}/SKILL.md (own oracle)

Writes:
  - r_transfer_eval/{arm}/{tid}_{ts}/ (harness run dirs)
  - r_transfer_results.json (collected rewards)

Usage:
  python3 run_r_transfer_eval.py --arms noskill transfer oracle --concurrency 4
  python3 run_r_transfer_eval.py --dry-run
"""
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

# === CONFIG ===
TRANSFER_DIR = Path(os.environ.get("SKILL_TRANSFER_DIR",
    "/data/yjh/my_claude_harness_biodsbench/skill_transfer"))
HARNESS = Path(os.environ.get("HARNESS_DIR",
    "/data/yjh/my_claude_harness_biodsbench"))
R_TASKS_DIR = os.environ.get("R_TASKS_DIR",
    "/data/yjh/my_claude_biomnibench/tasks/biodsbench_r")
LIFECYCLE = HARNESS / "output" / "biodsbench-lifecycle"
BUN = os.environ.get("BUN_BIN", os.path.expanduser("~/.bun/bin/bun"))

API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
MODEL = os.environ.get("ANTHROPIC_MODEL", "Vendor3/DeepSeek-V4-Flash")
QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Vendor2/Gemini-3-flash")
TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "2400"))

EVAL_ROOT = TRANSFER_DIR / "r_transfer_eval"
DEPLOY_ROOT = TRANSFER_DIR / "r_transfer_skills"  # where we stage skill dirs


def find_own_oracle_skill(tid: str) -> Path:
    """Find the task's own pruned oracle SKILL.md (upper bound)."""
    base = LIFECYCLE / tid / "prune" / "baseline" / "variant" / "skills" / f"oracle-{tid}" / "SKILL.md"
    if base.exists():
        return base
    # fallback: any variant
    vroot = LIFECYCLE / tid / "prune" / "variants"
    if vroot.exists():
        for v in sorted(vroot.iterdir()):
            cand = v / "skills" / f"oracle-{tid}" / "SKILL.md"
            if cand.exists():
                return cand
    return None


def stage_skill(tid: str, arm: str, skill_src: Path, skill_name: str) -> Path:
    """Copy a SKILL.md into a staging skills dir. Returns the skills-dir path."""
    skills_dir = DEPLOY_ROOT / arm / tid / "skills"
    target = skills_dir / skill_name
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill_src, target / "SKILL.md")
    # copy any sibling resources (scripts/, references/)
    for sib in skill_src.parent.iterdir():
        if sib.name == "SKILL.md":
            continue
        if sib.is_dir():
            shutil.copytree(sib, target / sib.name, dirs_exist_ok=True)
        else:
            shutil.copy2(sib, target / sib.name)
    return skills_dir


def build_cmd(tid: str, arm: str, ts: str, runs_dir: Path,
              skills_dir: Path = None, skill_name: str = None):
    cmd = [
        BUN, "src/harness/evaluation/cli.ts",
        "--task", tid,
        "--tasks-dir", R_TASKS_DIR,
        "--runs-dir", str(runs_dir),
        "--max-rounds", "5",
        "--timeout-seconds", str(TIMEOUT),
        "--concurrency", "1",
        "--temperature", "1.0",
        "--thinking", "disabled",
        "--timestamp", ts,
        "--quiet",
    ]
    if skills_dir is not None:
        cmd += [
            "--enable-skills",
            "--skills-dir", str(skills_dir),
            "--skill-name", skill_name,
            "--max-active-skills", "1",
        ]
    return cmd


def make_env():
    if not API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY or API_KEY before running evaluations")
    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = API_KEY
    env["ANTHROPIC_BASE_URL"] = BASE_URL
    env["ANTHROPIC_MODEL"] = MODEL
    env["QWEN_API_KEY"] = API_KEY
    env["QWEN_BASE_URL"] = QWEN_BASE_URL
    env["QWEN_MODEL"] = QWEN_MODEL
    return env


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["noskill", "transfer", "oracle"],
                    choices=["noskill", "transfer", "oracle"])
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--only-tasks", nargs="+", default=None)
    ap.add_argument("--tag", default=time.strftime("%Y%m%d_%H%M%S"))
    args = ap.parse_args()

    # Load selections
    with open(TRANSFER_DIR / "r_skill_selections.json") as f:
        selections = json.load(f)

    test_tasks = list(selections.keys())
    if args.only_tasks:
        test_tasks = [t for t in test_tasks if t in args.only_tasks]

    print(f"Test tasks: {len(test_tasks)} | Arms: {args.arms} | Concurrency: {args.concurrency}")
    print(f"Tag: {args.tag}")

    # Build job list: (tid, arm, skills_dir, skill_name)
    jobs = []
    for tid in test_tasks:
        sel = selections[tid]
        for arm in args.arms:
            if arm == "noskill":
                jobs.append((tid, arm, None, None))
            elif arm == "transfer":
                picks = sel.get("selected", [])
                if not picks:
                    print(f"  ⚠ {tid}: no transfer skill selected, skipping transfer arm")
                    continue
                top = picks[0]
                skill_src = Path(top["path"])
                if not skill_src.exists():
                    print(f"  ⚠ {tid}: transfer skill missing {skill_src}")
                    continue
                skill_name = "transfer-skill"
                skills_dir = stage_skill(tid, arm, skill_src, skill_name)
                jobs.append((tid, arm, skills_dir, skill_name))
            elif arm == "oracle":
                skill_src = find_own_oracle_skill(tid)
                if not skill_src:
                    print(f"  ⚠ {tid}: no own oracle skill, skipping oracle arm")
                    continue
                skill_name = f"oracle-{tid}"
                skills_dir = stage_skill(tid, arm, skill_src, skill_name)
                jobs.append((tid, arm, skills_dir, skill_name))

    print(f"Total jobs: {len(jobs)}")

    if args.dry_run:
        for tid, arm, sd, sn in jobs:
            ts = f"rtr_{arm}_{tid}_{args.tag}"
            print(f"  [{arm}] {tid} | skills_dir={sd} skill={sn} ts={ts}")
        return

    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    env = make_env()

    procs = {}  # proc -> info
    completed = 0
    failed = 0

    def reap(block=False):
        nonlocal completed, failed
        while True:
            live = {}
            for p, info in procs.items():
                rc = p.poll()
                if rc is None:
                    live[p] = info
                else:
                    if rc != 0:
                        failed += 1
                        print(f"  [FAIL] {info['arm']} {info['tid']} rc={rc}", flush=True)
                    else:
                        completed += 1
                        print(f"  [DONE] {info['arm']} {info['tid']}", flush=True)
            procs.clear()
            procs.update(live)
            if not block:
                return
            if len(procs) < args.concurrency:
                return
            time.sleep(10)

    for tid, arm, skills_dir, skill_name in jobs:
        while len(procs) >= args.concurrency:
            reap(block=True)

        ts = f"rtr_{arm}_{tid}_{args.tag}"
        runs_dir = EVAL_ROOT / arm
        runs_dir.mkdir(parents=True, exist_ok=True)
        log_file = runs_dir / f"{ts}.log"

        cmd = build_cmd(tid, arm, ts, runs_dir, skills_dir, skill_name)
        print(f"  [LAUNCH] {arm} {tid}", flush=True)
        p = subprocess.Popen(cmd, cwd=str(HARNESS), env=env,
                             stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
        procs[p] = {"tid": tid, "arm": arm, "ts": ts}
        time.sleep(2)

    # wait remaining
    while procs:
        reap(block=False)
        if procs:
            time.sleep(20)

    print(f"\nComplete: {completed} done, {failed} failed of {len(jobs)}")
    print(f"Runs under: {EVAL_ROOT}")


if __name__ == "__main__":
    main()
