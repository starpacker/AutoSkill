#!/usr/bin/env python3
"""
run_r_v10_eval.py — Harder-split transfer eval using the V10-R selector WITH REJECT.

For each task in the (harder) test split, runs 3 arms:
  1. noskill  : vanilla harness (no skill)
  2. v10      : V10-R selector decides — inject the selected source skill, OR
                REJECT (=> run identical to noskill). This is the key arm: it
                tests whether the reject-capable selector adds net value.
  3. oracle   : the task's OWN pruned oracle skill (upper bound)

Reads:
  - r_skill_selections_v10.json  (from select_r_skills_v10.py; {tid:{source|null,...}})
  - generalized_r/{source}/SKILL.md  (selected train generalized skill)
  - output/biodsbench-lifecycle/{tid}/prune/baseline/variant/skills/oracle-{tid}/SKILL.md
  - splits/test_tasks.json  (the harder split)

Writes:
  - r_v10_eval/{arm}/{tid}_{ts}/  (harness run dirs)
  - r_v10_results.json

Usage:
  python3 run_r_v10_eval.py --arms noskill v10 oracle --concurrency 4 --tag v10a
  python3 run_r_v10_eval.py --collect-only --tag v10a
"""
import argparse
import json
import os
import shutil
import subprocess
import time
from pathlib import Path

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
TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "3000"))

EVAL_ROOT = TRANSFER_DIR / "r_v10_eval"
DEPLOY_ROOT = TRANSFER_DIR / "r_v10_skills"
GEN_DIR = TRANSFER_DIR / "generalized_r"
OUT_JSON = TRANSFER_DIR / "r_v10_results.json"


def find_own_oracle_skill(tid: str) -> Path:
    base = LIFECYCLE / tid / "prune" / "baseline" / "variant" / "skills" / f"oracle-{tid}" / "SKILL.md"
    if base.exists():
        return base
    vroot = LIFECYCLE / tid / "prune" / "variants"
    if vroot.exists():
        for v in sorted(vroot.iterdir()):
            cand = v / "skills" / f"oracle-{tid}" / "SKILL.md"
            if cand.exists():
                return cand
    return None


def stage_skill(tid: str, arm: str, skill_src: Path, skill_name: str) -> Path:
    skills_dir = DEPLOY_ROOT / arm / tid / "skills"
    target = skills_dir / skill_name
    target.mkdir(parents=True, exist_ok=True)
    shutil.copy2(skill_src, target / "SKILL.md")
    for sib in skill_src.parent.iterdir():
        if sib.name == "SKILL.md":
            continue
        if sib.is_dir():
            shutil.copytree(sib, target / sib.name, dirs_exist_ok=True)
        else:
            shutil.copy2(sib, target / sib.name)
    return skills_dir


def build_cmd(tid, arm, ts, runs_dir, skills_dir=None, skill_name=None):
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
        cmd += ["--enable-skills", "--skills-dir", str(skills_dir),
                "--skill-name", skill_name, "--max-active-skills", "1"]
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


def find_reward(arm, tid, ts):
    runs_dir = EVAL_ROOT / arm
    for ce in runs_dir.rglob("run_events.jsonl"):
        s = str(ce)
        if tid in s and ts in s:
            reward = status = None
            try:
                for line in open(ce):
                    line = line.strip()
                    if not line:
                        continue
                    ev = json.loads(line)
                    if ev.get("type") == "run_finished":
                        d = ev.get("details", {}) or {}
                        reward, status = d.get("reward"), d.get("status")
            except Exception as e:
                return None, f"parse_err:{e}"
            raw = ce.parent / "trajectory.raw.jsonl"
            if raw.exists() and ("authentication_failed" in raw.read_text(errors="ignore")):
                return None, "auth_failed"
            return reward, status
    return None, "no_events"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", nargs="+", default=["noskill", "v10", "oracle"],
                    choices=["noskill", "v10", "oracle"])
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--collect-only", action="store_true")
    ap.add_argument("--only-tasks", nargs="+", default=None)
    ap.add_argument("--tag", default="v10a")
    args = ap.parse_args()

    selections = json.load(open(TRANSFER_DIR / "r_skill_selections_v10.json"))
    test_tasks = json.load(open(TRANSFER_DIR / "splits" / "test_tasks.json"))
    if args.only_tasks:
        test_tasks = [t for t in test_tasks if t in args.only_tasks]

    # Build jobs
    jobs = []          # (tid, arm, skills_dir, skill_name, effective_arm_label)
    reject_tids = []
    for tid in test_tasks:
        sel = selections.get(tid, {"source": None})
        for arm in args.arms:
            if arm == "noskill":
                jobs.append((tid, arm, None, None))
            elif arm == "v10":
                src = sel.get("source")
                if src is None:
                    # REJECT => v10 arm runs identical to noskill (no skill injected)
                    reject_tids.append(tid)
                    jobs.append((tid, arm, None, None))
                else:
                    skill_src = GEN_DIR / src / "SKILL.md"
                    if not skill_src.exists():
                        print(f"  ⚠ {tid}: selected src skill missing {skill_src}; running v10 as noskill")
                        jobs.append((tid, arm, None, None))
                    else:
                        sd = stage_skill(tid, arm, skill_src, "v10-skill")
                        jobs.append((tid, arm, sd, "v10-skill"))
            elif arm == "oracle":
                skill_src = find_own_oracle_skill(tid)
                if not skill_src:
                    print(f"  ⚠ {tid}: no own oracle skill, skipping oracle arm")
                    continue
                sd = stage_skill(tid, arm, skill_src, f"oracle-{tid}")
                jobs.append((tid, arm, sd, f"oracle-{tid}"))

    print(f"Test tasks: {len(test_tasks)} | arms: {args.arms} | jobs: {len(jobs)} | "
          f"v10 rejects(noskill): {len(reject_tids)} | concurrency: {args.concurrency}", flush=True)

    if args.dry_run:
        for tid, arm, sd, sn in jobs:
            print(f"  [{arm}] {tid} skills_dir={sd} skill={sn}")
        return

    def collect_all():
        results = {}
        for tid in test_tasks:
            entry = {"selector": selections.get(tid, {})}
            for arm in args.arms:
                ts = f"rv10_{arm}_{tid}_{args.tag}"
                rw, st = find_reward(arm, tid, ts)
                entry[arm] = {"reward": rw, "status": st}
            results[tid] = entry
        return results

    if args.collect_only:
        results = collect_all()
        json.dump(results, open(OUT_JSON, "w"), indent=2)
        print(f"Saved {OUT_JSON}")
        return

    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    env = make_env()

    def run_pool(batch, attempt):
        eff = args.tag if attempt == 1 else f"{args.tag}r{attempt}"
        procs = {}
        done = fail = 0

        def reap(block=False):
            nonlocal done, fail
            while True:
                live = {}
                for p, info in procs.items():
                    rc = p.poll()
                    if rc is None:
                        live[p] = info
                    else:
                        if rc != 0:
                            fail += 1
                            print(f"  [FAIL] {info['arm']} {info['tid']} rc={rc}", flush=True)
                        else:
                            done += 1
                            print(f"  [DONE] {info['arm']} {info['tid']}", flush=True)
                procs.clear(); procs.update(live)
                if not block or len(procs) < args.concurrency:
                    return
                time.sleep(10)

        for tid, arm, sd, sn in batch:
            while len(procs) >= args.concurrency:
                reap(block=True)
            ts = f"rv10_{arm}_{tid}_{eff}"
            runs_dir = EVAL_ROOT / arm
            runs_dir.mkdir(parents=True, exist_ok=True)
            log_file = runs_dir / f"{ts}.log"
            cmd = build_cmd(tid, arm, ts, runs_dir, sd, sn)
            print(f"  [LAUNCH a{attempt}] {arm} {tid}", flush=True)
            p = subprocess.Popen(cmd, cwd=str(HARNESS), env=env,
                                 stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
            procs[p] = {"tid": tid, "arm": arm}
            time.sleep(2)
        while procs:
            reap(block=False)
            if procs:
                time.sleep(20)
        print(f"  attempt {attempt}: {done} done, {fail} failed of {len(batch)}", flush=True)
        return eff

    # Retry loop keyed by (tid,arm); reuse eff tag per attempt for run dir naming.
    def job_key(j):
        return (j[0], j[1])

    def reward_for(tid, arm, eff):
        ts = f"rv10_{arm}_{tid}_{eff}"
        return find_reward(arm, tid, ts)

    batch = list(jobs)
    good_tag = {}   # (tid,arm) -> tag holding good result
    for attempt in range(1, 5):
        if not batch:
            break
        print(f"\n=== Attempt {attempt}: {len(batch)} jobs ===", flush=True)
        eff = run_pool(batch, attempt)
        retry = []
        for j in batch:
            tid, arm = j[0], j[1]
            rw, st = reward_for(tid, arm, eff)
            if rw is None or st in ("auth_failed", "no_events"):
                retry.append(j)
            else:
                good_tag[(tid, arm)] = eff
        print(f"  after attempt {attempt}: {len(batch)-len(retry)} ok, {len(retry)} retry", flush=True)
        batch = retry

    # Final collect using each job's good tag
    results = {}
    for tid in test_tasks:
        entry = {"selector": selections.get(tid, {})}
        for arm in args.arms:
            eff = good_tag.get((tid, arm), args.tag)
            rw, st = reward_for(tid, arm, eff)
            entry[arm] = {"reward": rw, "status": st}
        results[tid] = entry
    json.dump(results, open(OUT_JSON, "w"), indent=2)
    print(f"\nSaved {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
