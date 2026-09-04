import subprocess, json, sys, os

cmd = ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "server1"]
cmd += ["head -1 /tmp/skillopt_test_run/steps/step_0001/rollout/runs/da-17-1/da-17-1_skillopt_da-17-1_1787974382/logs/run_events.jsonl"]

result = subprocess.run(cmd, capture_output=True, timeout=60)
print("STDOUT:", repr(result.stdout[:500]))
print("STDERR:", repr(result.stderr[:500]))
print("RC:", result.returncode)