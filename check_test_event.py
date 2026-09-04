"""Check the event file from the test."""
import subprocess
import json

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace")

# Read the event file with python3 properly
cmd = "python3 -c \"import json; lines=open('/tmp/timeout_test/runs/da-20-4_timeout_test_300/logs/run_events.jsonl').readlines(); first=json.loads(lines[0]); print('timeoutSeconds=' + str(first['details']['timeoutSeconds'])); print('status=' + str(first['type']))\""
stdout = run_ssh(cmd, timeout=30)
print("Event file parse:")
print(stdout)

# Also check the run_summary.json
cmd2 = "cat /tmp/timeout_test/runs/da-20-4_timeout_test_300/logs/run_summary.json 2>/dev/null"
stdout2 = run_ssh(cmd2, timeout=30)
print("\nRun summary:")
print(stdout2[:2000])