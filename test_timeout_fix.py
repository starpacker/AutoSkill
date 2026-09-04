"""Test the timeout fix with a quick harness run."""
import subprocess, json, os, tempfile, time

def scp_file(local_content, remote_path):
    tmp = tempfile.mktemp(suffix='.sh')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', tmp, f'server1:{remote_path}'], capture_output=True, timeout=30)
        return True
    finally:
        try: os.unlink(tmp)
        except: pass

def run_ssh(cmd, timeout=60):
    result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'server1', cmd], capture_output=True, timeout=timeout)
    return result.stdout.decode('utf-8', errors='replace')

# Test: run a single task with the new timeout
test_script = '''#!/bin/bash
set -e
rm -rf /tmp/skillopt_timeout_test
mkdir -p /tmp/skillopt_timeout_test

cd /tmp/my_claude_biomnibench_fixed

echo "=== Test 1: timeout=300, single task ==="
timeout 360 /tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts \\
  --task da-20-4 \\
  --tasks-dir /data/yjh/biomnibench-organized \\
  --runs-dir /tmp/skillopt_timeout_test/runs \\
  --max-rounds 1 \\
  --timeout-seconds 300 \\
  --concurrency 1 \\
  --temperature 1 \\
  --thinking disabled \\
  --timestamp timeout_300_test \\
  --quiet 2>&1

echo "EXIT_CODE=$?"

# Check the event
EVENT_FILE=$(find /tmp/skillopt_timeout_test -name 'run_events.jsonl' 2>/dev/null | head -1)
if [ -n "$EVENT_FILE" ]; then
    python3 -c "import json; d=json.load(open('$EVENT_FILE')); print('timeoutSeconds=' + str(d['details']['timeoutSeconds']))"
fi

# Check summary
SUMMARY_FILE=$(find /tmp/skillopt_timeout_test -name 'run_summary.json' 2>/dev/null | head -1)
if [ -n "$SUMMARY_FILE" ]; then
    python3 -c "import json; d=json.load(open('$SUMMARY_FILE')); print('status=' + d.get('status','?'))"
fi

echo "=== DONE ==="
'''

scp_file(test_script, "/tmp/test_timeout_fix.sh")
run_ssh("chmod +x /tmp/test_timeout_fix.sh")

print("Running timeout fix test (waiting up to 360s)...")
stdout = run_ssh("bash /tmp/test_timeout_fix.sh", timeout=360)
print(stdout[:3000])