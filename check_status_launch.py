"""Check few-shot baseline status and skill-opt train script."""
import subprocess
import json

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check few-shot baseline: count completed with run_summary that has status success
print("=== FEW-SHOT STATUS ===")
script = """
import json, glob, os

base = '/data/yjh/skill-transfer-eval/fewshot_transfer'
dirs = sorted(os.listdir(base))
total = len(dirs)
completed = 0
running = 0
failed = 0
for d in dirs:
    summary_path = os.path.join(base, d, 'run_summary.json')
    if os.path.exists(summary_path):
        with open(summary_path) as f:
            s = json.load(f)
        status = s.get('status', 'unknown')
        if status == 'success':
            completed += 1
            reward = s.get('reward', 0)
            print(f'  OK: {d} reward={reward}')
        elif status == 'timeout':
            running += 1
            print(f'  TIMEOUT: {d}')
        else:
            failed += 1
            print(f'  FAILED: {d} status={status}')
    else:
        running += 1
        print(f'  RUNNING: {d} (no summary)')

print(f'\\nTotal: {total}, Completed: {completed}, Running: {running}, Failed: {failed}')
"""
stdout = run_ssh(f"python3 -c {json.dumps(script)}")
print(stdout[:3000])

# 2. Check the train.py script to understand how to launch
print("\n=== TRAIN.PY LAUNCH ===")
stdout = run_ssh("cat -n /data/yjh/skill-opt/repo/scripts/train.py | head -60")
print(stdout[:3000])

# 3. Check the venv activation
print("\n=== VENV ===")
stdout = run_ssh("ls /data/yjh/skill-opt/venv/bin/activate 2>/dev/null && echo 'VENV OK' || echo 'NO VENV'")
print(stdout[:200])

# 4. Check if tmux is available
print("\n=== TMUX ===")
stdout = run_ssh("which tmux 2>/dev/null && echo 'TMUX OK' || echo 'NO TMUX'")
print(stdout[:200])

# 5. Check the current skill-opt venv python
print("\n=== VENV PYTHON ===")
stdout = run_ssh("/data/yjh/skill-opt/venv/bin/python --version 2>&1")
print(stdout[:200])

# 6. Check if skillopt is installed
print("\n=== SKILLOPT INSTALLED ===")
stdout = run_ssh("/data/yjh/skill-opt/venv/bin/python -c 'import skillopt; print(skillopt.__version__)' 2>&1")
print(stdout[:200])