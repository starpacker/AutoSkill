#!/usr/bin/env python3
"""Verify skill-opt restart and baseline 3 status after timeout update."""
import subprocess, time

SSH = ['C:\\WINDOWS\\System32\\OpenSSH\\ssh.exe', '-o', 'StrictHostKeyChecking=no', 'yjh@10.128.247.28']

def run(cmd, timeout=60):
    r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=timeout)
    return (r.stdout + r.stderr).strip() or '(no output)'

# Step 8: Wait and verify
print('=== Step 8: Wait 30s and verify ===', flush=True)
time.sleep(30)
print('--- tmux capture ---')
print(run('tmux capture-pane -t skillopt -p -S -30'))
print('--- train.py process ---')
print(run("ps aux | grep 'scripts/train.py' | grep -v grep | head -2"))

# Step 9: Check Baseline 3
print('=== Step 9: Check Baseline 3 ===', flush=True)
print('--- tail -5 /tmp/gt_fewshot_nohup.log ---')
print(run('tail -5 /tmp/gt_fewshot_nohup.log'))
print('--- gt_fewshot_transfer count ---')
print(run('ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l'))

print('=== ALL DONE ===', flush=True)