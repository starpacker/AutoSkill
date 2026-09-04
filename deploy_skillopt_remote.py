#!/usr/bin/env python3
"""Deploy skill-opt on server1 via SSH."""
import subprocess, sys, base64

def ssh(command):
    print(f"[SSH] {command[:120]}")
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=5",
         "server1", command],
        capture_output=True, timeout=600
    )
    try:
        out = result.stdout.decode('utf-8', errors='replace').strip()
        err = result.stderr.decode('utf-8', errors='replace').strip()
    except:
        out = result.stdout.decode('gbk', errors='replace').strip()
        err = result.stderr.decode('gbk', errors='replace').strip()
    if err:
        for line in err.split('\n')[:5]:
            print(f'  STDERR: {line}')
    for line in out.split('\n')[-10:]:
        print(f'  {line}')
    return out, err, result.returncode

# Write deploy script to server1
script = """#!/bin/bash
set -e
SKILLOPT_DIR="/data/yjh/skill-opt"
VENV_PYTHON="$SKILLOPT_DIR/venv/bin/python3"
VENV_PIP="$SKILLOPT_DIR/venv/bin/pip"
REPO_DIR="$SKILLOPT_DIR/repo"
echo "=== Step 1: Install pip ==="
curl -sL https://bootstrap.pypa.io/get-pip.py -o /tmp/get-pip.py
$VENV_PYTHON /tmp/get-pip.py --break-system-packages 2>&1 | tail -3
echo "=== Step 2: Install core deps ==="
$VENV_PIP install -r "$REPO_DIR/requirements.txt" 2>&1 | tail -10
echo "=== Step 3: Install skillopt ==="
cd "$REPO_DIR" && $VENV_PIP install -e . 2>&1 | tail -5
echo "=== Step 4: Verify ==="
$VENV_PIP list 2>&1 | head -15
echo "Python: $($VENV_PYTHON --version)"
echo "=== DONE ==="
"""

encoded = base64.b64encode(script.encode()).decode()
cmd = f"echo {encoded} | base64 -d > /tmp/dep.sh && chmod +x /tmp/dep.sh && bash /tmp/dep.sh 2>&1"
print("=" * 60)
print("DEPLOYING SKILL-OPT ON SERVER1")
print("=" * 60)
stdout, stderr, rc = ssh(cmd)
print(f"\nEXIT CODE: {rc}")
if rc == 0:
    print("DEPLOYMENT SUCCESSFUL!")
else:
    print("DEPLOYMENT FAILED!")
    sys.exit(1)