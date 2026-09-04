"""Check status of both experiments."""
import subprocess, json, os

script = r'''
import subprocess, json, os

# 1. skill-opt status
print("=== SKILL-OPT ===")
train_proc = subprocess.run(["ps", "aux"], capture_output=True, text=True).stdout
train_lines = [l for l in train_proc.splitlines() if "train.py" in l and "grep" not in l]
print(f"train.py procs: {len(train_lines)}")
for l in train_lines[:2]:
    parts = l.split()
    print(f"  PID={parts[1]} CPU={parts[2]} ELAPSED={parts[10]}")

state_path = "/tmp/skillopt_test_run/runtime_state.json"
if os.path.exists(state_path):
    state = json.load(open(state_path))
    print(f"  last_completed_step={state['last_completed_step']}")
    print(f"  current_score={state['current_score']}")
    print(f"  best_score={state['best_score']}")

print(f"  steps: {os.listdir('/tmp/skillopt_test_run/steps/') if os.path.isdir('/tmp/skillopt_test_run/steps/') else 'N/A'}")
print(f"  skills: {os.listdir('/tmp/skillopt_test_run/skills/') if os.path.isdir('/tmp/skillopt_test_run/skills/') else 'N/A'}")

# 2. Few-shot status
print("\n=== FEW-SHOT BASELINE ===")
# Check tmux
tmux_proc = subprocess.run(
    ["tmux", "capture-pane", "-t", "fewshot_baseline", "-p", "-S", "-30"],
    capture_output=True, text=True, timeout=5
)
if tmux_proc.returncode == 0:
    lines = tmux_proc.stdout.strip().splitlines()
    for line in lines[-15:]:
        print(f"  {line}")

# Count completed runs
transfer_dir = "/data/yjh/skill-transfer-eval/fewshot_transfer"
if os.path.isdir(transfer_dir):
    all_dirs = sorted(os.listdir(transfer_dir))
    print(f"\n  Total experiment dirs: {len(all_dirs)}")
    completed = 0
    rewards = []
    for d in all_dirs:
        summary_path = os.path.join(transfer_dir, d, "run_summary.json")
        if os.path.exists(summary_path):
            completed += 1
            try:
                r = json.load(open(summary_path))
                rewards.append(r.get("reward", 0))
            except:
                pass
    print(f"  Completed (with run_summary): {completed}")
    if rewards:
        print(f"  Avg reward: {sum(rewards)/len(rewards):.3f}")
        print(f"  Min reward: {min(rewards):.3f}")
        print(f"  Max reward: {max(rewards):.3f}")
        print(f"  Rewards >= 0.5: {sum(1 for r in rewards if r >= 0.5)}/{len(rewards)}")
'''

with open("/tmp/check_both.py", "w") as f:
    f.write(script)
'''

cmd = [
    "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=no", "server1",
    "python3", "-c", script
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])