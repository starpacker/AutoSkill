"""Check biomnibenchAdapter.ts and the actual run details."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check biomnibenchAdapter.ts
print("=== BIOMNIBENCH ADAPTER ===")
r = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/biomnibenchAdapter.ts 2>/dev/null")
print(r[:5000])

# 2. Check if run_events.jsonl exists and parse it
print("\n=== RUN EVENTS EXIST ===")
r2 = run_ssh("wc -l /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl 2>/dev/null")
print(r2[:1000])

# 3. Actually read the first event line
print("\n=== FIRST EVENT RAW ===")
r3 = run_ssh("head -c 2000 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl 2>/dev/null")
print(r3[:2000])

# 4. Check the last event 
print("\n=== LAST EVENT RAW ===")
r4 = run_ssh("tail -c 2000 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl 2>/dev/null")
print(r4[:2000])