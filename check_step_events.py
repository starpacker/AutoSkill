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
    r = run_ssh(f"python3 -c \"import json; d=json.load(open('{line}')); print('{line}: timeout={d[\\\"details\\\"][\\\"timeoutSeconds\\\"]}')\" 2>/dev/null")
    if r:
        print(r.strip())

# Also check the harness.log in the skillopt dirs
print("\n=== HARNESS LOGS ===")
r = run_ssh("find /tmp/skillopt_test_run/ -maxdepth 3 -name 'harness.log' 2>/dev/null")
print(r[:2000])

# Check a harness.log
for line in r.strip().split('\n'):
    if not line:
        continue
    r2 = run_ssh(f"head -5 {line} 2>/dev/null; echo '---'")
    if r2:
        print(f"\n{line}:")
        print(r2[:500])