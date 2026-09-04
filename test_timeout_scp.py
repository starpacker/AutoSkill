"""Test timeout parameter passing with scp."""
import subprocess
import json
import sys
import os
import tempfile
import base64

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace"), result.stderr.decode("utf-8", errors="replace"), result.returncode

# First verify the python3 subprocess.cmd approach works
print("=== Test basic SSH ===")
stdout, stderr, rc = run_ssh("echo HELLO_SERVER")
print(f"STDOUT: {stdout}")
print(f"RC: {rc}")

# Write the test script to the server via ssh and python3
write_script = """
import os
script = '''#!/bin/bash
set -e
rm -rf /tmp/timeout_test
mkdir -p /tmp/timeout_test
cd /tmp/my_claude_biomnibench_fixed
/tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts \\
  --task da-20-4 \\
  --tasks-dir /data/yjh/biomnibench-organized \\
  --runs-dir /tmp/timeout_test/runs \\
  --max-rounds 1 \\
  --timeout-seconds 300 \\
  --concurrency 1 \\
  --temperature 1 \\
  --thinking disabled \\
  --timestamp timeout_test_300 \\
  --quiet &
PID=$!
sleep 5
EVENT_FILE=$(find /tmp/timeout_test -name 'run_events.jsonl' 2>/dev/null | head -1)
if [ -n "$EVENT_FILE" ]; then
    python3 -c "import json; d=json.load(open('$EVENT_FILE')); print('timeoutSeconds=' + str(d['details']['timeoutSeconds']))"
fi
kill $PID 2>/dev/null
wait $PID 2>/dev/null
echo DONE
'''
with open('/tmp/test_timeout.sh', 'w') as f:
    f.write(script)
os.chmod('/tmp/test_timeout.sh', 0o755)
print('SCRIPT_WRITTEN_OK')
"""

# Use a temp file to avoid PowerShell quoting issues
tmpfile = os.path.join(tempfile.gettempdir(), "write_script.py")
with open(tmpfile, 'w', encoding='utf-8') as f:
    f.write(write_script)

# Run via scp + ssh
result = subprocess.run(
    ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", tmpfile, "server1:/tmp/write_script.py"],
    capture_output=True, timeout=30
)
print(f"SCP result: {result.returncode}")

# Now execute the write script on the server
stdout, stderr, rc = run_ssh("python3 /tmp/write_script.py", timeout=30)
print(f"Write result: {stdout}")
if stderr:
    print(f"Write stderr: {stderr}")

# Run the test script
stdout, stderr, rc = run_ssh("bash /tmp/test_timeout.sh", timeout=30)
print(f"\nTest result: {stdout}")
if stderr:
    print(f"Test stderr: {stderr}")
print(f"RC: {rc}")