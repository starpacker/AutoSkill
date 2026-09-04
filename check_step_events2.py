"""Check step rollout events for timeout."""
import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# Check run_events.jsonl for step 1 rollout
steps = run_ssh("find /tmp/skillopt_test_run/steps/ -name 'run_events.jsonl' 2>/dev/null")
print("=== STEP RUN EVENTS ===")
print(steps[:2000])

# Check first event of each step run
for line in steps.strip().split('\n'):
    if not line:
        continue
    line = line.strip()
    cmd = "python3 -c \"import json; d=json.load(open('" + line + "')); print('timeout', d['details']['timeoutSeconds'])\""
    r = run_ssh(cmd + " 2>/dev/null")
    if r:
        print(f"\n{line}: {r.strip()}")

# Check the config.json
print("\n=== CONFIG.JSON ===")
r = run_ssh("cat /tmp/skillopt_test_run/config.json 2>/dev/null")
print(r[:3000])

# Check summary.json
print("\n=== SUMMARY.JSON ===")
r = run_ssh("cat /tmp/skillopt_test_run/summary.json 2>/dev/null")
print(r[:3000])

# Check history.json
print("\n=== HISTORY.JSON ===")
r = run_ssh("cat /tmp/skillopt_test_run/history.json 2>/dev/null")
print(r[:3000])