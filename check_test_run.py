"""Check the test run directly."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check the full test run directory
print("=== TEST RUN DIR ===")
r = run_ssh("find /tmp/skillopt_test_run/ -name '*.json' -o -name '*.yaml' -o -name '*.log' -o -name '*.sh' 2>/dev/null | head -30")
print(r[:2000])

# 2. Check the run_events.jsonl for da-20-4
print("\n=== DA-20-4 run_events.jsonl (first event) ===")
r = run_ssh("head -1 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl 2>/dev/null")
print(r[:2000])

# 3. Check if the skillopt output dir has any logs
print("\n=== SKILLOPT OUTPUT ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/ 2>/dev/null; echo '---'; find /tmp/skillopt_test_run/ -name '*.json' -maxdepth 2 2>/dev/null")
print(r[:2000])

# 4. Check if the harness.log exists for da-20-4
print("\n=== DA-20-4 harness.log ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/ 2>/dev/null")
print(r[:2000])

# 5. Check if there's a da-17-1 run
print("\n=== DA-17-1 run dir ===")
r = run_ssh("ls -la /tmp/skillopt_test_run/selection_eval_baseline/runs/da-17-1/da-17-1_skillopt_da-17-1_1787973901/ 2>/dev/null || echo 'NOT FOUND'")
print(r[:2000])