"""Collect correct test results from all run dirs (use last run per task)."""
import json, os, glob, re

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/test_eval_10tasks'
dirs = sorted(glob.glob(base + '/test_eval_*/'))

# Group by task id
by_task = {}
for d in dirs:
    task = d.split('test_eval_')[1].split('_')[0]
    by_task.setdefault(task, []).append(d)

results = []
for task, task_dirs in sorted(by_task.items()):
    latest = task_dirs[-1]
    log = latest + '/harness.log'
    if os.path.exists(log):
        with open(log) as f:
            content = f.read()
        m = re.search(r'\"reward\": ([0-9.]+)', content)
        if m:
            reward = float(m.group(1))
            hard = 1 if reward >= 0.5 else 0
            em = re.search(r'Elapsed: ([0-9.]+)s', content)
            elapsed = float(em.group(1)) if em else 0
            results.append({'id': task, 'hard': hard, 'soft': reward, 'elapsed': elapsed})
            print(f'{task}: reward={reward:.3f} hard={hard} elapsed={elapsed:.0f}s')
        else:
            print(f'{task}: no reward found')
    else:
        print(f'{task}: no log')

# Save corrected results
out = os.path.join(base, 'results_corrected.json')
with open(out, 'w') as f:
    json.dump(results, f, indent=2)

print()
print('Summary:')
print(f'  Total: {len(results)} tasks')
if results:
    avg = sum(r['soft'] for r in results) / len(results)
    hard_count = sum(r['hard'] for r in results)
    print(f'  Avg soft: {avg:.3f}')
    print(f'  Hard pass: {hard_count}/{len(results)}')
print(f'Corrected results saved to: {out}')