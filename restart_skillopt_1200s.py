#!/usr/bin/env python3
"""Update timeout to 1200s and restart skill-opt on server1."""
import subprocess, time, base64, sys

SSH = ['C:\\WINDOWS\\System32\\OpenSSH\\ssh.exe', '-o', 'StrictHostKeyChecking=no', '-o', 'BatchMode=yes', 'yjh@10.128.247.28']

def run(cmd, timeout=120):
    full_cmd = SSH + [cmd]
    try:
        r = subprocess.run(full_cmd, capture_output=True, text=True, timeout=timeout)
        out = r.stdout + r.stderr
        if not out.strip():
            out = "(no output)"
        return out
    except subprocess.TimeoutExpired as e:
        return f'TIMEOUT ({timeout}s)'
    except Exception as e:
        return f'ERROR: {e}'

# Step 1: Wait
print('=== Step 1: Sleep 10s ===', flush=True)
time.sleep(10)

# Step 2: Kill old processes
print('=== Step 2: Kill old processes ===', flush=True)
print(run('pkill -f "scripts/train.py" 2>/dev/null; true'))
print(run('ps aux | grep "bun.*harness.*skillopt" | grep -v "grep" | awk "{print \\$2}" | xargs kill 2>/dev/null; true'))
time.sleep(2)
print(run('tmux kill-session -t skillopt 2>/dev/null; true'))

# Step 3: Verify kill
print('=== Step 3: Verify kill ===')
sys.stdout.flush()
print(run('ps aux | grep "train.py" | grep -v grep'))

# Step 4: Update wrapper script (base64 to avoid escaping issues)
print('=== Step 4: Update run_skillopt.sh ===')
sys.stdout.flush()
script_content = b"""#!/bin/bash
export ANTHROPIC_MODEL=Vendor3/DeepSeek-V4-Flash
export ANTHROPIC_BASE_URL=https://api.gpugeek.com
export ANTHROPIC_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export MODEL_NAME=Vendor3/DeepSeek-V4-Flash
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash

cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
exec python scripts/train.py --config configs/biomnibench/default.yaml --cfg-options env.exec_timeout=1200
"""
encoded = base64.b64encode(script_content).decode()
print(run('echo ' + encoded + ' | base64 -d > /data/yjh/skill-opt/repo/run_skillopt.sh && chmod +x /data/yjh/skill-opt/repo/run_skillopt.sh'))

# Step 5: Verify script
print('=== Step 5: Verify script ===')
sys.stdout.flush()
print(run('cat /data/yjh/skill-opt/repo/run_skillopt.sh'))

# Step 6: Clean old output dir
print('=== Step 6: Clean old output dir ===')
sys.stdout.flush()
print(run('rm -rf /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_032544'))

# Step 7: Restart in tmux
print('=== Step 7: Restart in tmux ===')
sys.stdout.flush()
print(run('tmux new-session -d -s skillopt'))
print(run('tmux send-keys -t skillopt "bash /data/yjh/skill-opt/repo/run_skillopt.sh" Enter'))

# Step 8: Wait and verify
print('=== Step 8: Wait 30s and verify ===')
sys.stdout.flush()
time.sleep(30)
print(run('tmux capture-pane -t skillopt -p -S -30'))
print(run('ps aux | grep "scripts/train.py" | grep -v grep | head -2'))

# Step 9: Check Baseline 3
print('=== Step 9: Check Baseline 3 ===')
sys.stdout.flush()
print(run('tail -5 /tmp/gt_fewshot_nohup.log'))
print(run('ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l'))

print('=== ALL DONE ===')