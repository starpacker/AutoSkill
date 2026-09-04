import subprocess
import json
import sys

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60, encoding='utf-8', errors='replace')
        return result.stdout
    except Exception as e:
        return f"[ERROR: {e}]"

# 1. Get the full rollout.py  
print("=== ROLLOUT.PY ===")
rollout = run_ssh("cat -n /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py")
print(rollout[:5000])

# 2. Check the last 100 lines of cli.ts
print("\n\n=== CLI.TS LINES 430-440 (main exit) ===")
cli_end = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts | tail -20")
print(cli_end[:2000])