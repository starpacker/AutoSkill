import subprocess
import json
import sys

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    if result.returncode != 0:
        print(f"STDERR: {result.stderr}", file=sys.stderr)
    return result.stdout

# 1. Check run_manifest.json for actual timeout values
print("=== RUN MANIFEST ===")
manifest = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/run_manifest.json")
print(manifest[:3000])

# 2. Check harness.log to see the actual timeout error
print("\n=== HARNESS LOG ===")
log = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/harness.log 2>/dev/null | tail -50")
print(log[:2000])

# 3. Check the rollout.py to see how --timeout-seconds is passed
print("\n=== ROLLOUT.PY timeout arg ===")
rollout = run_ssh("grep -n 'timeout\\|timeout_seconds\\|timeout-seconds' /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py")
print(rollout[:2000])

# 4. Check the adapter.py 
print("\n=== ADAPTER.PY timeout arg ===")
adapter = run_ssh("grep -n 'timeout\\|exec_timeout' /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py")
print(adapter[:2000])

# 5. Check the default.yaml config
print("\n=== DEFAULT.YAML ===")
config = run_ssh("cat /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml")
print(config[:2000])