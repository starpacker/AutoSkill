"""Check cli.ts concurrency parsing and understand the 120s timeout."""
import subprocess

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# 1. Read cli.ts lines 180-260
print("=== CLI.TS lines 180-260 ===")
r = run_ssh("cat -n /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/cli.ts | sed -n '180,260p'")
print(r[:2000])

# 2. Check if there's a max_rounds default override in skillopt
print("\n=== SKILLOPT train.py or scripts ===")
r2 = run_ssh("grep -rn 'max_rounds\\|timeout' /data/yjh/skill-opt/repo/scripts/train.py 2>/dev/null | head -20")
print(r2[:2000])

# 3. Check the _run_harness call more carefully - the --concurrency 1
# If concurrency=1, then it's NOT batch mode, it's single task mode
# In single task mode (parsed.taskIds.length > 1 && !parsed.workerRun) is FALSE
# So it goes to runSourceTaskLoop directly with timeoutSeconds=7200
# But the run_events.jsonl shows timeoutSeconds:120...

# 4. Let me check if there's a configRunner that might override
print("\n=== configRunner.ts ===")
r4 = run_ssh("find /tmp/my_claude_biomnibench_fixed/src/harness/ -name '*.ts' -exec grep -l 'timeoutSeconds\\|configRunner' {} \\; 2>/dev/null")
print(r4[:2000])

# 5. Check if task-level config has timeout_seconds
print("\n=== task.toml for da-20-4 ===")
r5 = run_ssh("cat /data/yjh/biomnibench-organized/da-20-4/task.toml 2>/dev/null")
print(r5[:2000])

# 6. Check the taskEnvironment.ts for override
print("\n=== taskEnvironment.ts ===")
r6 = run_ssh("grep -n 'timeout' /tmp/my_claude_biomnibench_fixed/src/harness/evaluation/taskEnvironment.ts 2>/dev/null")
print(r6[:2000])