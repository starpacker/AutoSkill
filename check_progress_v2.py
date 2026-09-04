import json, os, glob

base = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_gpt-5.5_20260830_165307"

print("=== OUTPUT DIR ===")
print(os.listdir(base))

print("\n=== STEPS ===")
steps_dir = os.path.join(base, "steps")
if os.path.isdir(steps_dir):
    for d in sorted(os.listdir(steps_dir)):
        dp = os.path.join(steps_dir, d)
        files = os.listdir(dp)
        print(f"  {d}/: {files}")

print("\n=== SKILLS ===")
skills_dir = os.path.join(base, "skills")
if os.path.isdir(skills_dir):
    print(f"  Files: {os.listdir(skills_dir)}")

print("\n=== SLOW_UPDATE ===")
su = os.path.join(base, "slow_update")
if os.path.isdir(su):
    print(f"  Content: {os.listdir(su)}")

print("\n=== META_SKILL ===")
ms = os.path.join(base, "meta_skill")
if os.path.isdir(ms):
    print(f"  Content: {os.listdir(ms)}")

print("\n=== RUNTIME STATE ===")
rs = os.path.join(base, "runtime_state.json")
if os.path.exists(rs):
    d = json.load(open(rs))
    print(json.dumps(d, indent=2))

print("\n=== BASELINE RUNS ===")
be = os.path.join(base, "selection_eval_baseline/runs")
if os.path.isdir(be):
    for d in sorted(os.listdir(be)):
        print(f"  {d}")

print("\n=== 1B MISSING RESULT ===")
sj = "/data/yjh/skill-transfer-eval/fewshot_transfer/da-15-7_B3_da-8-2_to_da-15-7_fewshot_1B/logs/run_summary.json"
if os.path.exists(sj):
    d = json.load(open(sj))
    print(f"  reward={d.get('reward')} status={d.get('status')}")
else:
    print("  Not yet finished")

print("\n=== PROCESS ===")
import subprocess
r = subprocess.run(["ps", "aux"], capture_output=True, text=True)
for line in r.stdout.split("\n"):
    if "train.py" in line and "grep" not in line:
        print(f"  train: {line.strip()}")
for line in r.stdout.split("\n"):
    if "bun src/harness" in line and "grep" not in line:
        print(f"  bun: {line.strip()}")