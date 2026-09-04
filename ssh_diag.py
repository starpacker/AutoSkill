#!/usr/bin/env python3
"""SSH to server1 and run all diagnostic commands."""
import subprocess, json, sys

SSH = ['C:\\WINDOWS\\System32\\OpenSSH\\ssh.exe', '-o', 'StrictHostKeyChecking=no', 'yjh@10.128.247.28']

def run(cmd, timeout=60):
    r = subprocess.run(SSH + [cmd], capture_output=True, text=True, timeout=timeout)
    out = r.stdout
    if r.stderr:
        out += "\nSTDERR: " + r.stderr[:500]
    return out

# 1. Tmux capture
print("=" * 70)
print("=== 1. TMUX OUTPUT (last 200 lines) ===")
print("=" * 70)
out = run("tmux capture-pane -t skillopt -p -S -200")
print(out[-8000:] if len(out) > 8000 else out)
print()

# 2. Check the openai_compatible_backend.py
print("=" * 70)
print("=== 2. openai_compatible_backend.py ===")
print("=" * 70)
out = run("cat -n /data/yjh/skill-opt/repo/skillopt/model/openai_compatible_backend.py")
print(out)
print()

# 3. API endpoint tests
print("=" * 70)
print("=== 3. API endpoint tests ===")
print("=" * 70)
api_script = '''
import requests, json
base = 'https://api.gpugeek.com/v1'
headers = {'Authorization': 'Bearer 00gcclg9l39y9p01000dhjzolag1q2hk00901kh1', 'Content-Type': 'application/json'}

# Test 1: Vendor3/DeepSeek-V4-Flash
print('=== Test 1: Vendor3/DeepSeek-V4-Flash ===')
try:
    resp = requests.post(f'{base}/chat/completions', headers=headers, json={'model': 'Vendor3/DeepSeek-V4-Flash', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10}, timeout=10)
    print(f'Status: {resp.status_code}')
    print(f'Response: {resp.text[:300]}')
except Exception as e:
    print(f'Error: {e}')

# Test 2: Without vendor prefix
print()
print('=== Test 2: DeepSeek-V4-Flash (no vendor) ===')
try:
    resp = requests.post(f'{base}/chat/completions', headers=headers, json={'model': 'DeepSeek-V4-Flash', 'messages': [{'role': 'user', 'content': 'hi'}], 'max_tokens': 10}, timeout=10)
    print(f'Status: {resp.status_code}')
    print(f'Response: {resp.text[:300]}')
except Exception as e:
    print(f'Error: {e}')

# Test 3: List models
print()
print('=== Test 3: List models ===')
try:
    resp = requests.get(f'{base}/models', headers=headers, timeout=10)
    print(f'Status: {resp.status_code}')
    if resp.status_code == 200:
        models = resp.json().get('data', [])
        for m in models[:20]:
            print(f'  {m.get("id")}')
    else:
        print(f'Response: {resp.text[:500]}')
except Exception as e:
    print(f'Error: {e}')
'''
r = subprocess.run(SSH + ['bash', '-c', 'source /data/yjh/skill-opt/venv/bin/activate && python3 -c ' + repr(api_script)], capture_output=True, text=True, timeout=30)
print(r.stdout)
if r.stderr:
    print("STDERR:", r.stderr[:500])
print()

# 4. run_skillopt.sh
print("=" * 70)
print("=== 4. run_skillopt.sh ===")
print("=" * 70)
out = run("cat /data/yjh/skill-opt/repo/run_skillopt.sh")
print(out)
print()

# 5. Config
print("=" * 70)
print("=== 5. Config JSON ===")
print("=" * 70)
config_script = '''
import json
d = json.load(open('/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_114035/config.json'))
for k in ['optimizer_model', 'target_model', 'model', 'optimizer_backend', 'optimizer']:
    if k in d:
        print(f'{k}: {d[k]}')
print()
print('ALL KEYS:', list(d.keys()))
'''
out = run("python3 -c " + repr(config_script))
print(out)
print()

# 6. URL construction grep
print("=" * 70)
print("=== 6. URL construction patterns ===")
print("=" * 70)
out = run('grep -n "url\\|base_url\\|endpoint\\|chat/completions\\|/v1" /data/yjh/skill-opt/repo/skillopt/model/openai_compatible_backend.py | head -30')
print(out)