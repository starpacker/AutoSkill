"""Simple check of timeout values in events."""
import subprocess
import json
import os

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# Just check the da-17-1 step_0001 event
r = run_ssh("head -1 /tmp/skillopt_test_run/steps/step_0001/rollout/runs/da-17-1/da-17-1_skillopt_da-17-1_1787974382/logs/run_events.jsonl")
print("Step 0001 da-17-1 event:")
print(r[:500])

# Check da-14-1
r2 = run_ssh("head -1 /tmp/skillopt_test_run/steps/step_0001/rollout/runs/da-14-1/da-14-1_skillopt_da-14-1_1787974502/logs/run_events.jsonl")
print("\nStep 0001 da-14-1 event:")
print(r2[:500])

# Check step_0002
r3 = run_ssh("head -1 /tmp/skillopt_test_run/steps/step_0002/rollout/runs/da-18-5/da-18-5_skillopt_da-18-5_1787974742/logs/run_events.jsonl")
print("\nStep 0002 da-18-5 event:")
print(r3[:500])

# Parse and extract timeout
for name, data in [("step1-da17", r), ("step1-da14", r2), ("step2-da18", r3)]:
    try:
        d = json.loads(data)
        print(f"\n{name}: timeoutSeconds={d['details']['timeoutSeconds']}, maxRounds={d['details']['maxRounds']}")
    except:
        pass