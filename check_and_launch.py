"""Check few-shot baseline and prepare skill-opt launch."""
import subprocess
import json
import os
import tempfile

def scp_file(local_content, remote_path):
    tmp = tempfile.mktemp(suffix='.py')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        result = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", tmp, f"server1:{remote_path}"],
            capture_output=True, timeout=30
        )
        return result.returncode == 0
    finally:
        try: os.unlink(tmp)
        except: pass

def run_ssh(cmd, timeout=60):
    result = subprocess.run(
        ["ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", "server1", cmd],
        capture_output=True, timeout=timeout
    )
    return result.stdout.decode("utf-8", errors="replace")

# 1. Check few-shot baseline - simple approach
print("=== FEW-SHOT BASELINE STATUS ===")
script = '''
import json, os
base = "/data/yjh/skill-transfer-eval/fewshot_transfer"
dirs = sorted(os.listdir(base))
total = len(dirs)
completed = 0
running = 0
failed = 0
for d in dirs:
    sp = os.path.join(base, d, "run_summary.json")
    if os.path.exists(sp):
        with open(sp) as f:
            s = json.load(f)
        status = s.get("status", "unknown")
        if status == "success":
            completed += 1
        elif status == "timeout":
            running += 1
        else:
            failed += 1
    else:
        running += 1
print(f"Total={total} Completed={completed} Running={running} Failed={failed}")
'''
scp_file(script, "/tmp/check_baseline.py")
stdout = run_ssh("python3 /tmp/check_baseline.py")
print(stdout)

# 2. Check train.py full for launch instructions
print("\n=== TRAIN.PY HELP ===")
stdout = run_ssh("cd /data/yjh/skill-opt/repo && /data/yjh/skill-opt/venv/bin/python scripts/train.py --help 2>&1 | head -80")
print(stdout[:3000])

# 3. Check the few-shot prompt files to understand the experiment setup
print("\n=== FEW-SHOT PROMPT EXAMPLE ===")
stdout = run_ssh("ls /data/yjh/skill-transfer-eval/fewshot_transfer/ | head -5")
print(stdout[:500])

# 4. Read the train.py remaining part to understand registry
print("\n=== TRAIN.PY REGISTRY ===")
stdout = run_ssh("cat -n /data/yjh/skill-opt/repo/scripts/train.py | sed -n '60,120p'")
print(stdout[:3000])