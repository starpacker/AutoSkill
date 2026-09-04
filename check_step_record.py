"""Check test run step_record and investigate the 120s timeout."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# Check for step_record.json in the test run output dir
print("=== STEP RECORD ===")
for loc in ["/tmp/skillopt_test_run/step_record.json",
             "/tmp/skillopt_test_run/step_record_0.json",
             "/tmp/skillopt_test_run/checkpoints/step_0/step_record.json",
             "/tmp/skillopt_test_run/checkpoints/step_1/step_record.json"]:
    r = run_ssh(f"cat {loc} 2>/dev/null || echo 'NOT FOUND: {loc}'")
    print(f"\n--- {loc} ---")
    print(r[:2000])

# Check da-17-1 harness.log
print("\n=== DA-17-1 harness.log ===")
r = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-17-1/da-17-1_skillopt_da-17-1_1787973901/harness.log 2>/dev/null")
print(r[:2000])

# Check the actual task toml
print("\n=== da-17-1 task.toml ===")
r = run_ssh("cat /data/yjh/biomnibench-organized/da-17-1/task.toml 2>/dev/null")
print(r[:2000])