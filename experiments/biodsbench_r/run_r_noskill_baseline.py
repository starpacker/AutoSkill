#!/usr/bin/env python3
"""
run_r_noskill_baseline.py — Measure per-task NOSKILL baseline reward for the
96 non-empty R tasks. Needed to (a) build a harder test split (noskill < 0.6)
and (b) power the V10 selector's baseline-gating / reject logic.

Runs each task once with a vanilla harness (no skill), collects reward from
run_events.jsonl (run_finished.details.reward), writes r_noskill_baselines.json.

Usage:
  python3 run_r_noskill_baseline.py --concurrency 12 --tag base1
  python3 run_r_noskill_baseline.py --collect-only   # just re-collect from existing runs
"""
import argparse
import json
import os
import subprocess
import time
from pathlib import Path

TRANSFER_DIR = Path(os.environ.get("SKILL_TRANSFER_DIR",
    "/data/yjh/my_claude_harness_biodsbench/skill_transfer"))
HARNESS = Path(os.environ.get("HARNESS_DIR",
    "/data/yjh/my_claude_harness_biodsbench"))
R_TASKS_DIR = os.environ.get("R_TASKS_DIR",
    "/data/yjh/my_claude_biomnibench/tasks/biodsbench_r")
BUN = os.environ.get("BUN_BIN", os.path.expanduser("~/.bun/bin/bun"))

API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
MODEL = os.environ.get("ANTHROPIC_MODEL", "Vendor3/DeepSeek-V4-Flash")
QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Vendor2/Gemini-3-flash")
TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "2400"))

BASE_ROOT = TRANSFER_DIR / "r_noskill_baseline"   # harness run dirs
OUT_JSON = TRANSFER_DIR / "r_noskill_baselines.json"


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


def build_cmd(tid: str, ts: str, runs_dir: Path):
    return [
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


def find_reward(tid: str, ts: str):
    """Parse run_events.jsonl under BASE_ROOT/<tid>_<ts>*/ for run_finished reward.
    Returns (reward, status). status may be 'auth_failed' if the run hit an auth error."""
    runs_dir = BASE_ROOT
    candidates = list(runs_dir.rglob("run_events.jsonl"))
    best = None
    for ce in candidates:
        s = str(ce)
        if tid in s and ts in s:
            best = ce
            break
    if best is None:
        for ce in candidates:
            if tid in str(ce):
                best = ce
    if best is None:
        return None, "no_events"
    reward = None
    status = None
    try:
        with open(best) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                except Exception:
                    continue
                if ev.get("type") == "run_finished":
                    d = ev.get("details", {}) or {}
                    reward = d.get("reward")
                    status = d.get("status")
    except Exception as e:
        return None, f"parse_err:{e}"
    # detect auth failure in the trajectory (unreliable reward if so)
    raw = best.parent / "trajectory.raw.jsonl"
    if raw.exists():
        try:
            txt = raw.read_text(errors="ignore")
            if "authentication_failed" in txt or "Not logged in" in txt:
                return None, "auth_failed"
        except Exception:
            pass
    return reward, status


def collect(tasks, tag):
    results = {}
    for tid in tasks:
        ts = f"rns_{tid}_{tag}"
        reward, status = find_reward(tid, ts)
        results[tid] = {"reward": reward, "status": status}
    return results


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--tag", default="base1")
    ap.add_argument("--collect-only", action="store_true")
    ap.add_argument("--only-tasks", nargs="+", default=None)
    args = ap.parse_args()

    with open(TRANSFER_DIR / "nonempty_pruned_tasks.json") as f:
        tasks = json.load(f)
    if args.only_tasks:
        tasks = [t for t in tasks if t in args.only_tasks]

    # Reuse existing noskill rewards from the prior transfer eval (the 24 test tasks)
    reused = {}
    prior = TRANSFER_DIR / "r_transfer_results.json"
    if prior.exists() and not args.only_tasks:
        try:
            pr = json.load(open(prior)).get("results", {})
            for tid, arms in pr.items():
                ns = arms.get("noskill", {})
                if ns.get("reward") is not None:
                    reused[tid] = {"reward": ns["reward"],
                                   "status": "reused_prior",
                                   "passed": ns.get("passed")}
        except Exception as e:
            print(f"  ⚠ could not reuse prior: {e}")
    todo = [t for t in tasks if t not in reused]
    print(f"Non-empty R tasks: {len(tasks)} | reused(prior noskill)={len(reused)} | "
          f"to-run={len(todo)} | concurrency={args.concurrency} | tag={args.tag}", flush=True)
    tasks = todo  # only run the ones without a prior noskill reward
    globals()["_REUSED"] = reused

    if args.collect_only:
        results = collect(tasks, args.tag)
        results.update(globals().get("_REUSED", {}))
        with open(OUT_JSON, "w") as f:
            json.dump(results, f, indent=2)
        n_hard = sum(1 for r in results.values() if (r["reward"] or 0) < 0.6)
        n_done = sum(1 for r in results.values() if r["reward"] is not None)
        print(f"Collected {n_done}/{len(results)} | hard(<0.6)={n_hard}")
        print(f"Saved {OUT_JSON}")
        return

    BASE_ROOT.mkdir(parents=True, exist_ok=True)
    env = make_env()

    def run_batch(batch, attempt):
        """Launch `batch` tasks pool-style at args.concurrency; return list of tids launched."""
        eff_tag = args.tag if attempt == 1 else f"{args.tag}r{attempt}"
        procs = {}
        done = 0
        fail = 0

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
                            print(f"  [FAIL] {info['tid']} rc={rc}", flush=True)
                        else:
                            done += 1
                            print(f"  [DONE] {info['tid']}", flush=True)
                procs.clear(); procs.update(live)
                if not block:
                    return
                if len(procs) < args.concurrency:
                    return
                time.sleep(10)

        for tid in batch:
            while len(procs) >= args.concurrency:
                reap(block=True)
            ts = f"rns_{tid}_{eff_tag}"
            log_file = BASE_ROOT / f"{ts}.log"
            cmd = build_cmd(tid, ts, BASE_ROOT)
            print(f"  [LAUNCH a{attempt}] {tid}", flush=True)
            p = subprocess.Popen(cmd, cwd=str(HARNESS), env=env,
                                 stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
            procs[p] = {"tid": tid, "ts": ts}
            time.sleep(2)

        while procs:
            reap(block=False)
            if procs:
                time.sleep(20)
        print(f"  attempt {attempt}: {done} done, {fail} failed of {len(batch)}", flush=True)
        return eff_tag

    # Retry loop: re-run tasks whose result is auth_failed or missing (transient).
    batch = list(tasks)
    max_attempts = 4
    task_tag = {t: args.tag for t in tasks}  # which tag holds each task's good result
    for attempt in range(1, max_attempts + 1):
        if not batch:
            break
        print(f"\n=== Attempt {attempt}: {len(batch)} tasks (concurrency={args.concurrency}) ===", flush=True)
        eff_tag = run_batch(batch, attempt)
        # re-collect using this attempt's tag and find which still need retry
        res = collect(batch, eff_tag)
        retry = []
        for t, r in res.items():
            if r["reward"] is None or r["status"] in ("auth_failed", "no_events"):
                retry.append(t)
            else:
                task_tag[t] = eff_tag  # remember the good tag
        print(f"  after attempt {attempt}: {len(batch)-len(retry)} ok, {len(retry)} need retry", flush=True)
        batch = retry

    # final collect over the full task set, using each task's good tag
    results = {}
    for t in tasks:
        reward, status = find_reward(t, f"rns_{t}_{task_tag[t]}")
        results[t] = {"reward": reward, "status": status}
    results.update(globals().get("_REUSED", {}))
    with open(OUT_JSON, "w") as f:
        json.dump(results, f, indent=2)
    n_hard = sum(1 for r in results.values()
                 if r.get("reward") is not None and r["reward"] < 0.6)
    n_done = sum(1 for r in results.values() if r.get("reward") is not None)
    n_auth = sum(1 for r in results.values() if r.get("status") == "auth_failed")
    print(f"\nDone. collected={n_done}/{len(results)} | hard(<0.6)={n_hard} | still_auth_failed={n_auth}")
    print(f"Saved {OUT_JSON}", flush=True)


if __name__ == "__main__":
    main()
