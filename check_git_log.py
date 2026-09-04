"""Check the actual test run details and timeouts."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check git log for recent changes to cli.ts
print("=== GIT LOG for cli.ts ===")
r = run_ssh("cd /tmp/my_claude_biomnibench_fixed && git log --oneline -10 -- src/harness/evaluation/cli.ts 2>/dev/null || echo 'No git log'")
print(r[:2000])

# 2. Check if taskEnvironment.ts exists
print("\n=== TASK ENVIRONMENT ===")
r = run_ssh("ls -la /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/taskEnvironment.ts 2>/dev/null || echo 'NOT FOUND'; find /tmp/my_claude_biomnibench_fixed/src/harness/ -name 'taskEnvironment*' 2>/dev/null")
print(r[:2000])

# 3. Check the run_events.jsonl for da-20-4's first event with python3 parsing
print("\n=== DA-20-4 FIRST EVENT PARSED ===")
r = run_ssh("python3 -c \"import json; d=json.load(open('/tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl')); print(json.dumps(d, indent=2))\" 2>/dev/null")
print(r[:3000])

# 4. Check the actual training script output to see what was passed
print("\n=== TRAINING OUTPUT ===")
r = run_ssh("find /tmp/skillopt_test_run/ -name '*.log' -o -name '*.txt' -o -name '*.out' 2>/dev/null | head -10")
print(r[:2000])

# 5. Check the skillopt output dir for the main log
print("\n=== SKILLOPT OUTPUT DIR ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/ 2>/dev/null")
print(r[:2000])

# 6. Check if the training script was run via python and what args
print("\n=== TRAINING CMD ===")
r = run_ssh("cat /tmp/skillopt_test_run/run_cmd.sh 2>/dev/null || cat /tmp/skillopt_test_run/cmd.txt 2>/dev/null || echo 'No cmd file'")
print(r[:2000])