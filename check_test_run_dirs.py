"""Directly verify timeout behavior."""
import subprocess
import json
import time

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check the full list of directories in the test run output
print("=== TEST RUN DIR STRUCTURE ===")
r = run_ssh("find /tmp/skillopt_test_run/ -maxdepth 3 -type d 2>/dev/null | sort")
print(r[:3000])

# 2. Check run_events.jsonl for ALL tasks
print("\n=== ALL RUN_JSONL ===")
r = run_ssh("find /tmp/skillopt_test_run/ -name 'run_events.jsonl' 2>/dev/null")
print(r[:2000])

# 3. Check the run_events.jsonl content for the test run
print("\n=== COMPLETE FIRST EVENT ===")
r = run_ssh("python3 -c \"import json; d=json.load(open('/tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl')); print('timeout:', d['details']['timeoutSeconds']); print('maxRounds:', d['details']['maxRounds']); print('runDir:', d['details']['runDir'])\"")
print(r[:2000])

# 4. Check if the run directory was created by rollout.py or by something else
# Check the selection_eval_baseline directory
print("\n=== SELECTION EVAL BASELINE ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/selection_eval_baseline/ 2>/dev/null; echo '---'; ls -la /tmp/skillopt_test_run/selection_eval_baseline/runs/ 2>/dev/null")
print(r[:2000])

# 5. Check if there are other output directories
print("\n=== OTHER OUTPUTS ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/ 2>/dev/null")
print(r[:2000])

# 6. Check the git diff to see if cli.ts was modified
print("\n=== GIT DIFF ===")
r = run_ssh("cd /tmp/my_claude_biomnibench_fixed && git diff HEAD -- src/harness/evaluation/cli.ts 2>/dev/null | head -50")
print(r[:2000])

# 7. Check the git log for the last few commits
print("\n=== GIT LOG ===")
r = run_ssh("cd /tmp/my_claude_biomnibench_fixed && git log --oneline -5 2>/dev/null")
print(r[:2000])