#!/usr/bin/env python3
"""Collect results from all completed fewshot experiments on server1."""
import subprocess, json, re

def ssh(command):
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=5",
         "server1", command],
        capture_output=True, timeout=60
    )
    try:
        return result.stdout.decode('utf-8', errors='replace').strip()
    except:
        return result.stdout.decode('gbk', errors='replace').strip()

# List all experiment directories
out = ssh("ls -d /data/yjh/skill-transfer-eval/fewshot_transfer/*_fewshot_*/logs/run_summary.json 2>/dev/null")
if not out:
    print("No experiments found yet.")
    exit(0)

files = out.split('\n')
print(f"Found {len(files)} completed experiments")
print("=" * 70)
print(f"{'Experiment':<45} {'Reward':<8} {'Judge':<8}")
print("=" * 70)

results = []
for f in files:
    # Extract experiment name from path
    match = re.search(r'fewshot_transfer/(.+?)/logs/run_summary\.json', f)
    name = match.group(1) if match else f.split('/')[-3]
    
    # Read reward
    content = ssh(f"cat '{f}' 2>/dev/null")
    if content:
        try:
            data = json.loads(content)
            reward = data.get('reward', '?')
            judge = data.get('last_judge_status', '?')
            results.append({'name': name, 'reward': reward, 'judge': judge})
            print(f"{name:<45} {str(reward):<8} {str(judge):<8}")
        except:
            print(f"{name:<45} {'parse error':<16}")
    else:
        print(f"{name:<45} {'no data':<16}")

print("=" * 70)
if results:
    rewards = [r['reward'] for r in results if isinstance(r['reward'], (int, float))]
    if rewards:
        print(f"Avg reward: {sum(rewards)/len(rewards):.3f}  (n={len(rewards)})")
    print(f"Total: {len(results)} experiments completed")

# Also check running count
log_count = ssh("ls /data/yjh/skill-transfer-eval/logs/fewshot_20260829_002800/ 2>/dev/null | wc -l")
print(f"Log files: {log_count.strip()}")