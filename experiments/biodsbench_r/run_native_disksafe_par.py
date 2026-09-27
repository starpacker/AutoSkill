#!/usr/bin/env python3
"""run_native_disksafe_par.py — NATIVE SkillOpt eval, DISK-SAFE + PARALLEL.

Same disk-safety guarantees as run_native_disksafe.py but runs N tasks
concurrently via a thread pool. Each worker:
  - checks free space before starting a task (skip/disk_skip if too low),
  - runs one bun cli.ts rollout into its OWN per-task runs_dir,
  - reads the reward, then DELETES that runs_dir immediately.
Results are written incrementally to the SAME r_native_disksafe_results.json
(shared by run_native_disksafe.py) so it resumes/merges with the serial run.

Concurrency is intentionally modest (default 3) because the shared NFS has only
~2.4G free; each worker holds one small (~14MB) workspace + transient outputs.

Usage:
  python3 run_native_disksafe_par.py --tag natds1 --workers 3
  python3 run_native_disksafe_par.py --collect-only --tag natds1
"""
import argparse, json, os, subprocess, time, shutil, threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

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

BEST_SKILL = Path(os.environ.get("BEST_SKILL", "/data/yjh/skill-opt/repo/outputs/"
                  "skillopt_biodsbench_Vendor3-DeepSeek-V4-Flash_20260924_124128/best_skill.md"))
EVAL_ROOT = TRANSFER_DIR / "native_disksafe_eval"
OUT_JSON = TRANSFER_DIR / "r_native_disksafe_results.json"

MIN_FREE_MB = 800
WAIT_RETRIES = 8
WAIT_SECONDS = 30

_lock = threading.Lock()


def free_mb(path="/data"):
    st = os.statvfs(path)
    return (st.f_bavail * st.f_frsize) / (1024 * 1024)


def make_env():
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
        "--task", tid, "--tasks-dir", R_TASKS_DIR,
        "--runs-dir", str(runs_dir), "--max-rounds", "5",
        "--timeout-seconds", str(TIMEOUT), "--concurrency", "1",
        "--temperature", "1.0", "--thinking", "disabled",
        "--timestamp", ts, "--system-prompt", str(sys_prompt), "--quiet",
    ]


def read_reward_from_dir(runs_dir, tid, ts):
    reward = status = None
    summary = None
    for ce in Path(runs_dir).rglob("run_events.jsonl"):
        s = str(ce)
        if tid in s and ts in s:
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
                return None, f"parse_err:{e}", None
            raw = ce.parent / "trajectory.raw.jsonl"
            if raw.exists() and ("authentication_failed" in raw.read_text(errors="ignore")):
                return None, "auth_failed", None
            rs = ce.parent / "run_summary.json"
            if rs.exists():
                try:
                    summary = json.load(open(rs))
                except Exception:
                    summary = None
            return reward, status, summary
    return None, "no_events", None


def load_results():
    with _lock:
        if OUT_JSON.exists():
            try:
                return json.load(open(OUT_JSON))
            except Exception:
                return {}
        return {}


def update_result(tid, entry):
    with _lock:
        results = {}
        if OUT_JSON.exists():
            try:
                results = json.load(open(OUT_JSON))
            except Exception:
                results = {}
        results[tid] = entry
        tmp = str(OUT_JSON) + ".tmp"
        json.dump(results, open(tmp, "w"), indent=2)
        os.replace(tmp, OUT_JSON)


def run_one(tid, ts, sys_prompt, env, idx, total):
    # disk guard
    waited = 0
    while free_mb() < MIN_FREE_MB and waited < WAIT_RETRIES:
        print(f"  [disk-wait] {tid}: {free_mb():.0f}MB<{MIN_FREE_MB} ({waited+1}/{WAIT_RETRIES})", flush=True)
        time.sleep(WAIT_SECONDS)
        waited += 1
    if free_mb() < MIN_FREE_MB:
        print(f"  [disk-skip] {tid}: still low; skip", flush=True)
        update_result(tid, {"reward": None, "status": "disk_skip", "src": "disksafe_par"})
        return
    runs_dir = EVAL_ROOT / tid
    if runs_dir.exists():
        shutil.rmtree(runs_dir, ignore_errors=True)
    runs_dir.mkdir(parents=True, exist_ok=True)
    log_file = runs_dir / f"{ts}.log"
    cmd = build_cmd(tid, ts, runs_dir, sys_prompt)
    print(f"  [{idx}/{total}] RUN {tid} (free={free_mb():.0f}MB)", flush=True)
    t0 = time.time()
    rc = -1
    try:
        with open(log_file, "w") as lf:
            p = subprocess.Popen(cmd, cwd=str(HARNESS), env=env, stdout=lf, stderr=subprocess.STDOUT)
            rc = p.wait()
    except Exception as e:
        print(f"    {tid} launch error: {e}", flush=True)
    dt = time.time() - t0
    rw, st, summary = read_reward_from_dir(runs_dir, tid, ts)
    print(f"    -> {tid} rc={rc} reward={rw} status={st} ({dt:.0f}s)", flush=True)
    update_result(tid, {"reward": rw, "status": st, "rc": rc,
                        "seconds": round(dt), "src": "disksafe_par", "summary": summary})
    shutil.rmtree(runs_dir, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tag", default="natds1")
    ap.add_argument("--workers", type=int, default=3)
    ap.add_argument("--collect-only", action="store_true")
    args = ap.parse_args()

    evalset = json.load(open(TRANSFER_DIR / "splits" / "eval_expanded.json"))
    results = load_results()

    if args.collect_only:
        done = sum(1 for t in evalset if results.get(t, {}).get("reward") is not None)
        passes = sum(1 for t in evalset
                     if results.get(t, {}).get("reward") is not None and results[t]["reward"] >= 1.0)
        print(f"collected: done={done}/{len(evalset)} pass={passes}")
        for t in evalset:
            r = results.get(t, {})
            print(f"  {t}: reward={r.get('reward')} status={r.get('status')}")
        return

    EVAL_ROOT.mkdir(parents=True, exist_ok=True)
    sys_prompt = EVAL_ROOT / "native_best_skill.md"
    if not sys_prompt.exists():
        shutil.copy2(BEST_SKILL, sys_prompt)
    env = make_env()
    ts = f"soeval_{args.tag}"

    def needs_run(tid):
        r = results.get(tid, {})
        return r.get("reward") is None or r.get("status") in (None, "auth_failed", "no_events", "disk_skip")

    pending = [t for t in evalset if needs_run(t)]
    print(f"eval set: {len(evalset)} | done: {len(evalset)-len(pending)} | to run: {len(pending)} "
          f"| workers: {args.workers} | free: {free_mb():.0f}MB", flush=True)

    total = len(pending)
    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, tid, ts, sys_prompt, env, i, total): tid
                for i, tid in enumerate(pending, 1)}
        for f in as_completed(futs):
            try:
                f.result()
            except Exception as e:
                print(f"  worker error {futs[f]}: {e}", flush=True)

    results = load_results()
    done = sum(1 for t in evalset if results.get(t, {}).get("reward") is not None)
    passes = sum(1 for t in evalset
                 if results.get(t, {}).get("reward") is not None and results[t]["reward"] >= 1.0)
    print(f"\nSaved {OUT_JSON} | done={done}/{len(evalset)} pass={passes}", flush=True)


if __name__ == "__main__":
    main()
