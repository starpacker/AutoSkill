"""Check the full CLI parsing and timeout override."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Read the full cli.ts (lines 220-400)
print("=== CLI.TS lines 220-400 ===")
r = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts | sed -n '220,400p'")
print(r[:5000])

# 2. Check the RunSourceTaskLoopInput type
print("\n=== types.ts RunSourceTaskLoopInput ===")
r2 = run_ssh("grep -n -A30 'RunSourceTaskLoopInput' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/types.ts")
print(r2[:2000])

# 3. Check if taskEnvironment.ts reads timeout from task.toml
print("\n=== taskEnvironment.ts full ===")
r3 = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/taskEnvironment.ts")
print(r3[:5000])

# 4. Check the harness.log for da-20-4
print("\n=== DA-20-4 harness.log ===")
r4 = run_ssh("cat /tmp/skillopt_test_run/selection_eval_baseline/runs/da-20-4/da-20-4_skillopt_da-20-4_1787973901/harness.log 2>/dev/null")
print(r4[:2000])