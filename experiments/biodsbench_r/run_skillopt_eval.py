#!/usr/bin/env python3
"""run_skillopt_eval.py — SkillOpt eval on the expanded BioDSBench eval set.

SkillOpt method: apply the BioMNIBench-trained `best_skill.md` as a FIXED
--system-prompt (cross-benchmark transfer). No per-task selection.

Reads:
  - splits/eval_expanded.json      (the 39-task eval set)
  - best_skill.md                  (BioMNIBench-trained SkillOpt skill)
Also reuses any already-completed runs from the prior R15 run
  (_skillopt_r15_results.json) so we don't re-run those.

Writes:
  - skillopt_eval/{tid}_{ts}/      (harness run dirs)
  - r_skillopt_eval_results.json

Usage:
  python3 run_skillopt_eval.py --concurrency 4 --tag so1
  python3 run_skillopt_eval.py --collect-only --tag so1
"""
import argparse, json, os, subprocess, time, glob, shutil
from pathlib import Path

TRANSFER_DIR = Path(os.environ.get("SKILL_TRANSFER_DIR",
    "/data/yjh/my_claude_harness_biodsbench/skill_transfer"))
HARNESS = Path(os.environ.get("HARNESS_DIR",
    "/data/yjh/my_claude_harness_biodsbench"))
R_TASKS_DIR = os.environ.get("R_TASKS_DIR",
    "/data/yjh/my_claude_biomnibench/tasks/biodsbench_r")
BUN = os.path.expanduser("~/.bun/bin/bun")

API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
MODEL = os.environ.get("ANTHROPIC_MODEL", "Vendor3/DeepSeek-V4-Flash")
QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Vendor2/Gemini-3-flash")
TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "3000"))

BEST_SKILL = Path(os.environ.get("BEST_SKILL",
    "/home/yjh/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260910_135818/best_skill.md"))
EVAL_ROOT = TRANSFER_DIR / "skillopt_eval"
OUT_JSON = TRANSFER_DIR / "r_skillopt_eval_results.json"
PRIOR_R15 = TRANSFER_DIR / "_skillopt_r15_results.json"


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


def build_cmd(tid, ts, runs_dir, sys_prompt):
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
        "--system-prompt", str(sys_prompt),
        "--quiet",
    ]


def find_reward(tid, ts):
    for ce in EVAL_ROOT.rglob("run_events.jsonl"):
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
    ap.add_argument("--concurrency", type=int, default=4)
    ap.add_argument("--tag", default="so1")
    ap.add_argument("--collect-only", action="store_true")
    ap.add_argument("--reuse-prior", action="store_true", default=True,
                    help="reuse completed tasks from prior R15 run")
    ap.add_argument("--only-tasks", nargs="+", default=None)
    args = ap.parse_args()

    evalset = json.load(open(TRANSFER_DIR / "splits" / "eval_expanded.json"))
    if args.only_tasks:
        evalset = [t for t in evalset if t in args.only_tasks]

    # prior R15 results (reuse completed pass/fail; skip re-run)
    prior = {}
    if args.reuse_prior and PRIOR_R15.exists():
        pr = json.load(open(PRIOR_R15))
        for tid, v in pr.items():
            if v.get("reward") is not None and v.get("status") not in ("no_events",):
                prior[tid] = v

    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    # stage system prompt locally
    sys_prompt = EVAL_ROOT / "best_skill.md"
    shutil.copy2(BEST_SKILL, sys_prompt)

    def collect_all():
        results = {}
        for tid in evalset:
            if tid in prior:
                results[tid] = {"reward": prior[tid]["reward"],
                                "status": prior[tid]["status"], "src": "prior_r15"}
                continue
            ts = f"soeval_{tid}_{args.tag}"
            rw, st = find_reward(tid, ts)
            results[tid] = {"reward": rw, "status": st, "src": "new"}
        return results

    if args.collect_only:
        results = collect_all()
        json.dump(results, open(OUT_JSON, "w"), indent=2)
        done = sum(1 for v in results.values() if v["reward"] is not None)
        passes = sum(1 for v in results.values() if v["reward"] is not None and v["reward"] >= 1.0)
        print(f"collected: done={done}/{len(evalset)} pass={passes}")
        print(f"Saved {OUT_JSON}")
        return

    # tasks to run = evalset minus prior-completed
    to_run = [t for t in evalset if t not in prior]
    print(f"eval set: {len(evalset)} | prior reused: {len(prior)} | to run: {len(to_run)} | "
          f"concurrency: {args.concurrency}", flush=True)
    for t in prior:
        print(f"  [reuse] {t} reward={prior[t]['reward']} ({prior[t]['status']})", flush=True)

    env = make_env()

    def run_pool(batch, attempt):
        eff = args.tag if attempt == 1 else f"{args.tag}r{attempt}"
        procs = {}
        def reap(block):
            while True:
                live = {}
                for p, info in procs.items():
                    if p.poll() is None:
                        live[p] = info
                    else:
                        print(f"  [end] {info['tid']} rc={p.returncode}", flush=True)
                procs.clear(); procs.update(live)
                if not block or len(procs) < args.concurrency:
                    return
                time.sleep(10)
        for tid in batch:
            while len(procs) >= args.concurrency:
                reap(True)
            ts = f"soeval_{tid}_{eff}"
            runs_dir = EVAL_ROOT / f"{tid}"
            runs_dir.mkdir(parents=True, exist_ok=True)
            log_file = runs_dir / f"{ts}.log"
            cmd = build_cmd(tid, ts, runs_dir, sys_prompt)
            print(f"  [LAUNCH a{attempt}] {tid}", flush=True)
            p = subprocess.Popen(cmd, cwd=str(HARNESS), env=env,
                                 stdout=open(log_file, "w"), stderr=subprocess.STDOUT)
            procs[p] = {"tid": tid}
            time.sleep(2)
        while procs:
            reap(False)
            if procs:
                time.sleep(20)
        return eff

    batch = list(to_run)
    good_tag = {}
    for attempt in range(1, 4):
        if not batch:
            break
        print(f"\n=== Attempt {attempt}: {len(batch)} tasks ===", flush=True)
        eff = run_pool(batch, attempt)
        retry = []
        for tid in batch:
            ts = f"soeval_{tid}_{eff}"
            rw, st = find_reward(tid, ts)
            if rw is None or st in ("auth_failed", "no_events"):
                retry.append(tid)
            else:
                good_tag[tid] = eff
                print(f"  [done] {tid} reward={rw} status={st}", flush=True)
        print(f"  after attempt {attempt}: {len(batch)-len(retry)} ok, {len(retry)} retry", flush=True)
        batch = retry

    # final collect
    results = {}
    for tid in evalset:
        if tid in prior:
            results[tid] = {"reward": prior[tid]["reward"], "status": prior[tid]["status"], "src": "prior_r15"}
        else:
            eff = good_tag.get(tid, args.tag)
            rw, st = find_reward(tid, eff and f"soeval_{tid}_{eff}" or f"soeval_{tid}_{args.tag}")
            results[tid] = {"reward": rw, "status": st, "src": "new"}
    json.dump(results, open(OUT_JSON, "w"), indent=2)
    passes = sum(1 for v in results.values() if v["reward"] is not None and v["reward"] >= 1.0)
    done = sum(1 for v in results.values() if v["reward"] is not None)
    print(f"\nSaved {OUT_JSON} | done={done}/{len(evalset)} pass={passes}", flush=True)


if __name__ == "__main__":
    main()
