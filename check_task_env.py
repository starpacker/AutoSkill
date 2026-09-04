"""Check taskEnvironment.ts and git log."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Read taskEnvironment.ts
print("=== TASK ENVIRONMENT ===")
r = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/taskEnvironment.ts 2>/dev/null")
print(r[:4000])

# 2. Check git log for cli.ts changes
print("\n=== GIT LOG ===")
r2 = run_ssh("cd /tmp/my_claude_biomnibench_fixed && git log --oneline -10 2>/dev/null")
print(r2[:2000])

# 3. Check if the first event JSON shows the full data
print("\n=== FIRST EVENT PARSED ===")
r3 = run_ssh("python3 -c \"import json; d=json.load(open('/tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl')); print(json.dumps(d['details'], indent=2))\" 2>/dev/null")
print(r3[:3000])