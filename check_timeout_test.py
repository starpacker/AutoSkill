"""Check the actual run_events.jsonl for the first event and trace the timeout."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check the actual run_events.jsonl for first event - full details
print("=== FIRST EVENT FULL ===")
r = run_ssh("head -1 /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/logs/run_events.jsonl")
print(r[:3000])

# 2. Check the git_commit to see if it's current
print("\n=== GIT COMMIT ===")
r = run_ssh("cd /tmp/my_claude_biomnibench_fixed && git log --oneline -3 2>/dev/null || echo 'Not a git repo or no git'")
print(r[:1000])

# 3. Check what the actual timeout is by running a quick test
print("\n=== QUICK TEST - run with timeout 300 ===")
test_cmd = "cd /tmp/my_claude_biomnibench_fixed && /tmp/bun_extract/bun-linux-x64/bun src/harness/evaluation/cli.ts --task da-20-4 --tasks-dir /data/yjh/biomnibench-organized --runs-dir /tmp/timeout_test/runs --max-rounds 1 --timeout-seconds 300 --concurrency 1 --temperature 1 --thinking disabled --timestamp timeout_test_300 --quiet 2>&1 | head -20"
r = run_ssh(test_cmd)
print(r[:2000])

# 4. Check the run_events.jsonl for this test
print("\n=== TEST RUN EVENTS ===")
r = run_ssh("find /tmp/timeout_test/ -name 'run_events.jsonl' 2>/dev/null | head -1 | xargs -I{} head -1 {} 2>/dev/null")
print(r[:2000])