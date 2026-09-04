#!/usr/bin/env python3
import json, os, subprocess

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260831_131414'

# 1. Check history
with open(f'{base}/history.json') as f:
    h = json.load(f)
# history.json is a list of steps
print(f'History steps: {len(h)}')
for s in h[-3:]:
    print(f'  step {s.get("step")}: score={s.get("score")}, reflect_s={s.get("reflect_s")}')

# 2. Kill skillopt bun processes
r = subprocess.run(['bash', '-c', "ps aux | grep 'bun.*cli.ts.*skillopt' | grep -v grep | awk '{print $2}'"], capture_output=True, text=True)
if r.stdout.strip():
    pids = r.stdout.strip().split()
    print(f'Killing {len(pids)} skillopt bun processes: {pids}')
    for p in pids:
        try: os.kill(int(p), 9)
        except: pass
else:
    print('No skillopt bun processes to kill')

# 3. Check B3
print('---B3---')
b3 = subprocess.run(['tail', '-5', '/tmp/gt_fewshot_nohup.log'], capture_output=True, text=True)
print(b3.stdout)
print('B3 output dirs:', len(os.listdir('/data/yjh/skill-transfer-eval/gt_fewshot_transfer/')))

# 4. Check B3 bun
bun_b3 = subprocess.run(['bash', '-c', "ps aux | grep 'bun.*cli.ts.*gt3' | grep -v grep | wc -l"], capture_output=True, text=True)
print(f'B3 running bun: {bun_b3.stdout.strip()}')

# 5. Check runtime_state
with open(f'{base}/runtime_state.json') as f:
    rs = json.load(f)
print('---Runtime State---')
print(f'  last_completed_step: {rs.get("last_completed_step")}')
print(f'  current_score: {rs.get("current_score")}')
print(f'  best_score: {rs.get("best_score")}')

# 6. Check if main process exists
r2 = subprocess.run(['bash', '-c', "ps aux | grep -E 'skillopt_main|python.*skillopt' | grep -v grep | head -3"], capture_output=True, text=True)
print('---Main process---')
print(r2.stdout.strip() if r2.stdout.strip() else 'NO MAIN PROCESS RUNNING')