"""Test timeout parameter passing properly."""
import subprocess
import json
import sys

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace"), result.stderr.decode("utf-8", errors="replace"), result.returncode

# Write a test script on the server
script = r"""#!/bin/bash
set -e
rm -rf /tmp/timeout_test
mkdir -p /tmp/timeout_test
cd /tmp/my_claude_biomnibench_fixed
/tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts \
  --task da-20-4 \
  --tasks-dir /data/yjh/biomnibench-organized \
  --runs-dir /tmp/timeout_test/runs \
  --max-rounds 1 \
  --timeout-seconds 300 \
  --concurrency 1 \
  --temperature 1 \
  --thinking disabled \
  --timestamp timeout_test_300 \
  --quiet &
BUN_PID=$!
sleep 6
EVENT_FILE=$(find /tmp/timeout_test -name 'run_events.jsonl' 2>/dev/null | head -1)
if [ -n "$EVENT_FILE" ]; then
    head -1 "$EVENT_FILE"
fi
kill $BUN_PID 2>/dev/null
wait $BUN_PID 2>/dev/null
echo "DONE"
"""

# Write script to server
py_code = f"""
import os
script = {json.dumps(script)}
with open('/tmp/test_timeout.sh', 'w') as f:
    f.write(script)
os.chmod('/tmp/test_timeout.sh', 0o755)
"""
cmd = ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "server1", f"python3 -c {json.dumps(py_code)}"]
subprocess.run(cmd, capture_output=True, timeout=30)

# Run the script
print("Running test...")
stdout, stderr, rc = run_ssh("bash /tmp/test_timeout.sh 2>&1")
print("STDOUT:", stdout[:2000])
if stderr:
    print("STDERR:", stderr[:500])
print("RC:", rc)