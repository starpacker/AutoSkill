import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    return result.stdout

# 1. Check run_summary.json
print("=== RUN SUMMARY ===")
summary = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_summary.json")
print(summary[:3000])

# 2. Check the step_record.json for the test run
print("\n=== STEP RECORD ===")
step = run_ssh("cat /tmp/skillopt_test_run/step_record.json 2>/dev/null")
print(step[:3000])

# 3. Check the run_events.jsonl for timeout events
print("\n=== RUN EVENTS (first and last) ===")
events = run_ssh("head -5 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl; echo '---LAST---'; tail -5 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl")
print(events[:3000])

# 4. Check if there's a log file inside the agent dir
print("\n=== AGENT LOG ===")
agent_log = run_ssh("ls -la /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/agent/ 2>/dev/null")
print(agent_log[:2000])

# 5. Check the trajectory raw for the last entries (to see the error)
print("\n=== TRAJECTORY LAST ===")
traj = run_ssh("tail -20 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/trajectory.raw.jsonl 2>/dev/null | python3 -c 'import sys,json; [print(json.dumps({k:v for k,v in json.loads(l).items() if k in [\"type\",\"status\",\"error\",\"message\",\"step\",\"duration\"]}, indent=2)) for l in sys.stdin]' 2>/dev/null")
print(traj[:3000])