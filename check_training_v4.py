import json, os, sys, glob

base = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260831_131414"

print("=== PROCESS ===")
os.system("ps aux | grep train.py | grep -v grep")

print("\n=== BASELINE EVAL ===")
be = os.path.join(base, "selection_eval_baseline/runs")
if os.path.isdir(be):
    for d in sorted(os.listdir(be)):
        dp = os.path.join(be, d)
        if os.path.isdir(dp):
            for sub in sorted(os.listdir(dp)):
                if sub.startswith(d):
                    sj = os.path.join(dp, sub, "logs/run_summary.json")
                    if os.path.exists(sj):
                        rd = json.load(open(sj))
                        print(f"  {d}: reward={rd.get('reward')} status={rd.get('status')}")
                    else:
                        print(f"  {d}: running (no summary yet)")

print("\n=== SKILLS ===")
sk = os.path.join(base, "skills")
for s in sorted(glob.glob(os.path.join(sk, "skill_v*.md"))):
    sz = os.path.getsize(s)
    print(f"  {os.path.basename(s)}: {sz} bytes")

print("\n=== STEPS ===")
steps_dir = os.path.join(base, "steps")
if os.path.isdir(steps_dir):
    steps = sorted(os.listdir(steps_dir))
    print(f"  {len(steps)} step(s): {steps}")
    for step in steps:
        sr = os.path.join(steps_dir, step, "step_record.json")
        if os.path.exists(sr):
            d = json.load(open(sr))
            print(f"    {step}: action={d.get('action')} score={d.get('current_score')} n_patches={d.get('n_patches')} wall={d.get('wall_time_s')}s")
else:
    print("  No steps directory yet")

print("\n=== RUNTIME STATE ===")
rs = os.path.join(base, "runtime_state.json")
if os.path.exists(rs):
    d = json.load(open(rs))
    print(f"  last_completed_step={d.get('last_completed_step')}")
    print(f"  current_score={d.get('current_score')}")
    print(f"  best_score={d.get('best_score')}")
    print(f"  current_origin={d.get('current_origin')}")

print("\n=== HISTORY COUNT ===")
h = os.path.join(base, "history.json")
if os.path.exists(h):
    hist = json.load(open(h))
    print(f"  {len(hist)} entries in history.json")
    if hist:
        last = hist[-1]
        print(f"  last entry: step={last.get('step')} action={last.get('action')} score={last.get('current_score')}")

print("\n=== TIME ===")
import time
print(f"  {time.strftime('%Y-%m-%d %H:%M:%S')}")