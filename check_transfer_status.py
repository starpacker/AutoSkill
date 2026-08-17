#!/usr/bin/env python3
"""Check status of all transfer pairs on server1."""
import subprocess
import json
import sys

SSH = ["C:\\WINDOWS\\System32\\OpenSSH\\ssh.exe", "-o", "StrictHostKeyChecking=no", "yjh@10.128.247.28"]

def run_remote(cmd):
    result = subprocess.run(SSH + ["cd /data/yjh/skill-transfer-eval/transfer_pruned && " + cmd], 
                          capture_output=True, text=True, timeout=30)
    return result.stdout, result.stderr

# List all directories
out, err = run_remote("ls -d */")
dirs = [d.strip().rstrip('/') for d in out.strip().split('\n') if d.strip()]

print(f"{'DIR':<50} {'STATUS':<20} {'REWARD':<10} {'ROUNDS':<8}")
print("="*90)

for d in sorted(dirs):
    # Check skill_application.json
    sa_cmd = f"""python3 -c "
import json
try:
    with open('{d}/workspace/skill_application.json') as f:
        data = json.load(f)
        skills = data.get('skills', [])
        if skills:
            print(skills[0].get('status', '?'))
        else:
            print('empty_skills')
except:
    print('NO_FILE')
" 2>/dev/null"""
    
    # Check run_summary.json
    rs_cmd = f"""python3 -c "
import json
try:
    with open('{d}/logs/run_summary.json') as f:
        data = json.load(f)
        print(data.get('reward', '?'))
        print(data.get('rounds', '?'))
except:
    print('NO_FILE')
    print('?')
" 2>/dev/null"""
    
    out_sa, _ = run_remote(sa_cmd)
    status = out_sa.strip().split('\n')[0] if out_sa.strip() else 'UNKNOWN'
    
    out_rs, _ = run_remote(rs_cmd)
    lines = out_rs.strip().split('\n')
    reward = lines[0] if lines else '?'
    rounds = lines[1] if len(lines) > 1 else '?'
    
    print(f"{d:<50} {status:<20} {reward:<10} {rounds:<8}")

print("\nDone.")