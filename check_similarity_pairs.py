#!/usr/bin/env python3
"""Check ranked similarity pairs on server1."""
import subprocess, json

SSH = ["C:\\WINDOWS\\System32\\OpenSSH\\ssh.exe", "-o", "StrictHostKeyChecking=no", "yjh@10.128.247.28"]

# Write a Python script to server
script = r'''
import json
with open('/data/yjh/skill-transfer-eval/similarity/ranked_pairs.json') as f:
    data = json.load(f)
print(f"Total pairs: {len(data)}")
print()
print(f"{'Rank':<6} {'Source':<12} {'Target':<12} {'CombinedScore':<15} {'Structural':<12}")
print("="*60)
# Only show pairs where source has a pruned skill bundle
# and the pair is NOT already in the 16
already_tested = set()
for p in data:
    already_tested.add((p['source'], p['target']))
count = 0
for p in data:
    cs = p.get('combined_score', 0)
    ss = p.get('structural_score', 0)
    if cs >= 0.4 and (p['source'], p['target']) not in already_tested:
        count += 1
        print(f"{count:<6} {p['source']:<12} {p['target']:<12} {cs:<15.3f} {ss:<12.3f}")
    if count >= 30:
        break
'''

result = subprocess.run(SSH + ["python3", "-c", script], capture_output=True, text=True, timeout=30)
print(result.stdout)
if result.stderr:
    print("STDERR:", result.stderr[:500])