"""Quick test to verify timeout handling."""
import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=120)
    return result.stdout.decode("utf-8", errors="replace")

# Run a very quick test with timeout=300 and check the event
test_cmd = """
rm -rf /tmp/timeout_test && mkdir -p /tmp/timeout_test && \
cd /tmp/my_claude_biomnibench_fixed && \
/tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts \
  --task da-20-4 \
  --tasks-dir /data/yjh/biomnibench-organized \
  --runs-dir /tmp/timeout_test/runs \
  --max-rounds 1 \
  --timeout-seconds 300 \
  --concurrency 1 \
  --temperature 1 \
  --thinking disabled \
  --timestamp timeout_test_verify \
  --quiet 2>/dev/null &
sleep 3 && \
EVENT=$(head -1 /tmp/timeout_test/runs/da-20-4/timeout_test_verify/logs/run_events.jsonl 2>/dev/null) && \
echo "EVENT: $EVENT" && \
kill %1 2>/dev/null; wait 2>/dev/null
"""
r = run_ssh(test_cmd)
print(r[:3000])