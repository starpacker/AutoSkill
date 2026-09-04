import json, os, glob

base = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_gpt-5.5_20260830_165307"

print("=== STEP 0001 ===")
r = json.load(open(os.path.join(base, "steps/step_0001/step_record.json")))
for k in ["step","epoch","step_in_epoch","action","current_score","best_score",
           "n_patches","n_failure_patches","n_success_patches","rollout_n","wall_time_s","skill_len"]:
    print(f"  {k}: {r.get(k)}")

print()
print("=== ALL STEPS ===")
steps = sorted(glob.glob(os.path.join(base, "steps/step_*/step_record.json")),
               key=lambda x: int(x.split("step_")[1].split("/")[0]))
if not steps:
    print("  No steps yet")
else:
    print(f"  Step | Ep | Epi | Action | Score | Best | Patches | Wall(s)")
    print(f"  " + "-"*65)
    for s in steps:
        d = json.load(open(s))
        print(f"  {d['step']:>4} | {d['epoch']:>2} | {d['step_in_epoch']:>3} | {d['action']:>20} | {d['current_score']:>4} | {d['best_score']:>3} | {d['n_patches']:>2} | {int(d['wall_time_s']):>5}")

print()
print("=== SKILLS ===")
skills = glob.glob(os.path.join(base, "skills/skill_v*.md"))
print(f"  Count: {len(skills)}")
for s in sorted(skills)[-3:]:
    sz = os.path.getsize(s)
    print(f"  {os.path.basename(s)}: {sz} bytes")

print()
print("=== BASELINE EVAL ===")
be = os.path.join(base, "selection_eval_baseline/runs")
if os.path.isdir(be):
    for d in sorted(os.listdir(be)):
        run_dir = os.path.join(be, d)
        if os.path.isdir(run_dir):
            for sub in sorted(os.listdir(run_dir)):
                sj = os.path.join(run_dir, sub, "logs/run_summary.json")
                if os.path.exists(sj):
                    rd = json.load(open(sj))
                    print(f"  {d}: reward={rd.get('reward')} status={rd.get('status')}")

print()
print("=== RUNTIME STATE ===")
rs = os.path.join(base, "runtime_state.json")
if os.path.exists(rs):
    d = json.load(open(rs))
    print(f"  last_completed_step: {d.get('last_completed_step')}")
    print(f"  current_score: {d.get('current_score')}")
    print(f"  best_score: {d.get('best_score')}")

print()
print("=== 1B MISSING RESULT ===")
sj = "/data/yjh/skill-transfer-eval/fewshot_transfer/da-15-7_B3_da-8-2_to_da-15-7_fewshot_1B/logs/run_summary.json"
if os.path.exists(sj):
    d = json.load(open(sj))
    print(f"  reward={d.get('reward')} status={d.get('status')}")
else:
    print("  Not yet finished")

print()
print("=== PROCESS ===")
import subprocess
result = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for line in result.stdout.split("\n"):
    if "train.py" in line and "grep" not in line:
        print(f"  train.py: {line.strip()}")
for line in result.stdout.split("\n"):
    if "bun src/harness" in line and "grep" not in line:
        print(f"  bun: {line.strip()}")