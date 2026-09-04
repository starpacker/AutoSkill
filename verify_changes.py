"""Verify all changes were applied correctly."""
import subprocess
import json

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Verify rollout.py
print("=== VERIFY ROLLOUT.PY ===")
stdout = run_ssh("grep -n 'timeout\\|exec_timeout' /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py")
print(stdout)

# 2. Verify adapter.py
print("\n=== VERIFY ADAPTER.PY ===")
stdout = run_ssh("grep -n 'exec_timeout' /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py")
print(stdout)

# 3. Verify initial skill
print("\n=== VERIFY INITIAL SKILL ===")
stdout = run_ssh("cat /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/skills/initial.md")
print(stdout[:500])

# 4. Verify config
print("\n=== VERIFY CONFIG ===")
stdout = run_ssh("cat /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml")
print(stdout)

# 5. Check few-shot baseline status
print("\n=== FEW-SHOT BASELINE STATUS ===")
stdout = run_ssh("ls /data/yjh/skill-transfer-eval/fewshot_transfer/ 2>/dev/null | head -50")
print(stdout[:2000])

# 6. Check how many completed
print("\n=== COMPLETED BASELINE COUNT ===")
stdout = run_ssh("ls /data/yjh/skill-transfer-eval/fewshot_transfer/*/run_summary.json 2>/dev/null | wc -l")
print(f"Completed: {stdout.strip()}")

# 7. Check failed
print("\n=== FAILED BASELINE ===")
stdout = run_ssh("for f in /data/yjh/skill-transfer-eval/fewshot_transfer/*/run_summary.json; do if [ -f \"$f\" ]; then s=$(python3 -c \"import json; print(json.load(open('$f')).get('status','unknown'))\" 2>/dev/null); if [ \"$s\" != \"success\" ]; then echo \"$(basename $(dirname $(dirname $f))): $s\"; fi; fi; done 2>/dev/null")
print(stdout[:2000])

# 8. Check tmux status
print("\n=== TMUX STATUS ===")
stdout = run_ssh("tmux list-sessions 2>/dev/null || echo 'No tmux sessions'")
print(stdout[:2000])