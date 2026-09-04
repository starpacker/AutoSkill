"""Search for 120 in harness source code."""
import subprocess
import sys

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    try:
        result = subprocess.run(full_cmd, capture_output=True, timeout=60)
        return result.stdout.decode("utf-8", errors="replace")
    except Exception as e:
        return f"[ERROR: {e}]"

# 1. Search for hardcoded 120 or timeoutSeconds assignment
print("=== SEARCH for 120 in harness ===")
result = run_ssh("grep -rn '120' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/ --include='*.ts' 2>/dev/null")
print(result[:3000])

# 2. Search for timeoutSeconds =  or default timeout
print("\n=== SEARCH for timeoutSeconds assignment ===")
result2 = run_ssh("grep -rn 'timeoutSeconds' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/ --include='*.ts' 2>/dev/null")
print(result2[:3000])

# 3. Check the run harness log for the actual da-17-1 task
print("\n=== DA-17-1 harness.log ===")
result3 = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-17-1/da-17-1_skillopt_da-17-1_1787973901/harness.log 2>/dev/null")
print(result3[:3000])

# 4. Check if there's a default.yaml in skillopt base config with timeout
print("\n=== BASE DEFAULT.YAML ===")
result4 = run_ssh("cat /data/yjh/skill-opt/repo/configs/_base_/default.yaml 2>/dev/null")
print(result4[:3000])