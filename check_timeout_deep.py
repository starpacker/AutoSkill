import subprocess
import json
import sys
import os

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    try:
        result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
        return result.stdout
    except subprocess.TimeoutExpired:
        return "[TIMEOUT]"
    except Exception as e:
        return f"[ERROR: {e}]"

# Check the actual harness source code for timeout defaults
print("=== CLI.TS timeout default ===")
src = run_ssh("grep -n 'timeout' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts")
print(src[:2000])

# Check the batchRunner timeout
print("\n=== BATCHRUNNER.TS timeout ===")
src2 = run_ssh("grep -n 'timeout' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/batchRunner.ts")
print(src2[:2000])

# Check sourceTaskLoop timeout
print("\n=== SOURCETASKLOOP.TS timeout ===")
src3 = run_ssh("grep -n 'timeout' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/sourceTaskLoop.ts")
print(src3[:2000])

# Check the actual run_summary.json for the error
print("\n=== RUN SUMMARY ===")
summary = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/run_summary.json 2>/dev/null")
print(summary[:2000])

# Check the logs directory
print("\n=== LOG FILES ===")
logs = run_ssh("ls -la /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/ 2>/dev/null")
print(logs[:2000])

# Also check if there's a harness.log in the run directory
print("\n=== ALL FILES in run dir ===")
allf = run_ssh("find /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/ -type f -name '*.log' -o -name '*.json' -o -name '*.txt' 2>/dev/null")
print(allf[:2000])