import json, glob, os

base = "/data/yjh/skill-transfer-eval/fewshot_transfer"

# Count 1A dirs
dirs_1a = sorted(glob.glob(os.path.join(base, "*1A*")))
dirs_1b = sorted(glob.glob(os.path.join(base, "*1B*")))

print(f"Total 1A dirs: {len(dirs_1a)}")
print(f"Total 1B dirs: {len(dirs_1b)}")

# Find completed 1A
completed_1a = []
for d in dirs_1a:
    sj = os.path.join(d, "logs", "run_summary.json")
    if os.path.exists(sj):
        r = json.load(open(sj))
        completed_1a.append((os.path.basename(d), r.get("reward"), r.get("status")))

print(f"\n=== 1A COMPLETED: {len(completed_1a)} ===")
for name, reward, status in sorted(completed_1a):
    print(f"  {name}: reward={reward} status={status}")

# Find completed 1B
completed_1b = []
for d in dirs_1b:
    sj = os.path.join(d, "logs", "run_summary.json")
    if os.path.exists(sj):
        r = json.load(open(sj))
        completed_1b.append((os.path.basename(d), r.get("reward"), r.get("status")))

print(f"\n=== 1B COMPLETED: {len(completed_1b)} ===")
for name, reward, status in sorted(completed_1b):
    print(f"  {name}: reward={reward} status={status}")

# Summary stats
rewards_1a = [r for _, r, _ in completed_1a if r is not None]
rewards_1b = [r for _, r, _ in completed_1b if r is not None]
if rewards_1a:
    print(f"\n1A avg reward: {sum(rewards_1a)/len(rewards_1a):.3f} (n={len(rewards_1a)})")
if rewards_1b:
    print(f"1B avg reward: {sum(rewards_1b)/len(rewards_1b):.3f} (n={len(rewards_1b)})")