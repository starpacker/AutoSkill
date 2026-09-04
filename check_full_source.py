import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, text=True, timeout=60)
    return result.stdout

# Read the full cli.ts to understand the flow
print("=== FULL CLI.TS ===")
cli = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts")
print(cli[:8000])

# Also check the batchRunner worker creation flow
print("\n\n=== FULL BATCHRUNNER.TS ===")
br = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/batchRunner.ts")
print(br[:8000])