"""Search for timeoutSeconds=120 origin."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Search for run_started event
print("=== run_started event source ===")
r1 = run_ssh("grep -rn 'run_started' /tmp/my_claude_biomnibench_fixed/src/harness/ --include='*.ts' 2>/dev/null")
print(r1[:2000])

# 2. Read sourceTaskLoop.ts to see how timeoutSeconds=120 gets set
print("\n=== sourceTaskLoop.ts lines 1-100 ===")
r2 = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/sourceTaskLoop.ts | head -100")
print(r2[:3000])

# 3. Check around line 374 where deadline is set
print("\n=== sourceTaskLoop.ts lines 360-420 ===")
r3 = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/sourceTaskLoop.ts | sed -n '360,420p'")
print(r3[:3000])

# 4. Check run context builder
print("\n=== run event creation ===")
r4 = run_ssh("grep -rn 'run_started\\|timeoutSeconds' /tmp/my_claude_biomnibench_fixed/src/harness/ --include='*.ts' 2>/dev/null | head -30")
print(r4[:3000])