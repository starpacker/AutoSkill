import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    return result.stdout

# Read the main function of cli.ts to understand the flow
print("=== CLI.TS MAIN FUNCTION (lines 280+) ===")
cli = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts | tail -200")
print(cli[:6000])

# Check the rollout.py _run_harness to see how it calls the CLI
print("\n\n=== ROLLOUT.PY full ===")
rollout = run_ssh("cat -n /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py")
print(rollout[:4000])

# Check the run_events.jsonl for the da-17-1 task (which had harness.log)
print("\n\n=== DA-17-1 RUN EVENTS ===")
events = run_ssh("head -3 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-17-1/da-17-1_skillopt_da-17-1_1787973901/logs/run_events.jsonl 2>/dev/null; echo '---'; cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-17-1/da-17-1_skillopt_da-17-1_1787973901/logs/run_summary.json 2>/dev/null")
print(events[:2000])