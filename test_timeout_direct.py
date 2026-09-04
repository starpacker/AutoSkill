"""Test timeout parameter passing and fix the issue."""
import subprocess
import json
import sys
import base64

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace"), result.stderr.decode("utf-8", errors="replace"), result.returncode

# Write a test script directly to the server
test_script = """#!/bin/bash
set -e
rm -rf /tmp/timeout_test
mkdir -p /tmp/timeout_test
cd /tmp/my_claude_biomnibench_fixed

# Run with timeout 120 and check the event
/tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts \\
  --task da-20-4 \\
  --tasks-dir /data/yjh/biomnibench-organized \\
  --runs-dir /tmp/timeout_test/runs \\
  --max-rounds 1 \\
  --timeout-seconds 120 \\
  --concurrency 1 \\
  --temperature 1 \\
  --thinking disabled \\
  --timestamp timeout_test_120 \\
  --quiet &
PID=$!
sleep 4
EVENT_FILE=$(find /tmp/timeout_test -name 'run_events.jsonl' 2>/dev/null | head -1)
if [ -n "$EVENT_FILE" ]; then
    TIMEOUT=$(python3 -c "import json; d=json.load(open('$EVENT_FILE')); print(d['details']['timeoutSeconds'])")
    echo "timeoutSeconds=$TIMEOUT"
fi
kill $PID 2>/dev/null
wait $PID 2>/dev/null
echo "TEST_120_DONE"
"""

# Write script to server
py_code = "import os; exec(open('/dev/stdin').read())"
encoded = base64.b64encode(test_script.encode()).decode()

# Use base64 to avoid quoting issues
cmd = f"echo {encoded} | base64 -d > /tmp/test_timeout.sh && chmod +x /tmp/test_timeout.sh && bash /tmp/test_timeout.sh"
stdout, stderr, rc = run_ssh(cmd, timeout=30)
print("STDOUT:", stdout[:2000])
if stderr:
    print("STDERR:", stderr[:500])
print("RC:", rc)