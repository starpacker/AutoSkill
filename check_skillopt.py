"""Check skill-opt test run progress."""
import subprocess, json, os

cmd = [
    "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=no", "server1",
    "ps aux | grep 'train.py' | grep -v grep | awk '{print $2, $10, $11}'; "
    "echo '===RUNTIME==='; "
    "cat /tmp/skillopt_test_run/runtime_state.json 2>/dev/null; "
    "echo '===STEPS==='; "
    "ls -d /tmp/skillopt_test_run/steps/*/ 2>/dev/null | wc -l; "
    "echo '===ROLLOUT==='; "
    "ls /tmp/skillopt_test_run/steps/step_*/rollout/ 2>/dev/null | head -20; "
    "echo '===BUN_PROCS==='; "
    "ps aux | grep 'bun' | grep -v grep | wc -l"
]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])