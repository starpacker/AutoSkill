"""Build comparison table: BL-RAW, WSKILL, V10 Selector, SkillOpt, Baseline3(GT)"""
import json, os, glob, re

test_tasks = ['da-5-1', 'da-20-3', 'da-19-6', 'da-17-3', 'da-18-1', 
              'da-8-2', 'da-10-1', 'da-15-2', 'da-4-7', 'da-12-2']

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458'
eval_dir = os.path.join(base, 'test_eval_10tasks')

# =============================================
# 1. BL-RAW (baseline from skill-transfer-eval, no skill)
# =============================================
summary = '/data/yjh/skill-transfer-eval/summary/all_results.json'
bl_raw = {}
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    entries = data.get('tasks', [])
    for e in entries:
        tid = e.get('task_id', '')
        if tid in test_tasks:
            rewards = [b.get('reward', 0) for b in e.get('baseline', [])]
            if rewards:
                bl_raw[tid] = sum(rewards) / len(rewards)

# =============================================
# 2. WSKILL (with original skill from skill-transfer-eval)
# =============================================
ws = {}
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    entries = data.get('tasks', [])
    for e in entries:
        tid = e.get('task_id', '')
        if tid in test_tasks:
            rewards = [s.get('reward', 0) for s in e.get('with_skill', [])]
            if rewards:
                ws[tid] = sum(rewards) / len(rewards)

# =============================================
# 3. V10 Selector results
# =============================================
v10_base = '/data/yjh/skill-transfer-eval/skill_selector_v10'
v10_results = {}
if os.path.exists(v10_base):
    for task_dir in sorted(glob.glob(os.path.join(v10_base, '*'))):
        dname = os.path.basename(task_dir)
        tid = dname.split('_')[0]
        if tid in test_tasks:
            log = os.path.join(task_dir, 'harness.log')
            if os.path.exists(log):
                with open(log) as f:
                    content = f.read()
                m = re.search(r'"reward": ([0-9.]+)', content)
                if m:
                    reward = float(m.group(1))
                    if tid not in v10_results:
                        v10_results[tid] = []
                    v10_results[tid].append((dname, reward))

# =============================================
# 4. SkillOpt (our test evaluation)
# =============================================
skillopt = {}
for tid in test_tasks:
    task_dirs = sorted(glob.glob(os.path.join(eval_dir, f'test_eval_{tid}_*')))
    if task_dirs:
        latest = task_dirs[-1]
        log = os.path.join(latest, 'harness.log')
        if os.path.exists(log):
            with open(log) as f:
                content = f.read()
            m = re.search(r'"reward": ([0-9.]+)', content)
            if m:
                skillopt[tid] = float(m.group(1))

# =============================================
# 5. Baseline3 (GT fewshot transfer)
# =============================================
gt_base = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
gt_results = {}
for task_dir in sorted(glob.glob(os.path.join(gt_base, '*'))):
    dname = os.path.basename(task_dir)
    tid = dname.split('_')[0]
    if tid in test_tasks:
        log = os.path.join(task_dir, 'harness.log')
        if os.path.exists(log):
            with open(log) as f:
                content = f.read()
            m = re.search(r'"reward": ([0-9.]+)', content)
            if m:
                reward = float(m.group(1))
                if tid not in gt_results:
                    gt_results[tid] = []
                gt_results[tid].append((dname, reward))

gt_best = {}
for tid in test_tasks:
    if tid in gt_results:
        gt_best[tid] = max(gt_results[tid], key=lambda x: x[1])[1]

# =============================================
# Print combined table
# =============================================
print(f"\n{'='*80}")
print(f"{'COMPARISON TABLE':^80}")
print(f"{'='*80}")
print(f"{'Task':<10} {'BL-RAW':<10} {'WSKILL':<10} {'V10 Sel':<10} {'SkillOpt':<10} {'Base3(GT)':<10}")
print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

totals = {'bl': [], 'ws': [], 'v10': [], 'so': [], 'gt': []}
for tid in test_tasks:
    bl = bl_raw.get(tid, None)
    w = ws.get(tid, None)
    v = max(v10_results[tid], key=lambda x: x[1])[1] if tid in v10_results else None
    so = skillopt.get(tid, None)
    g = gt_best.get(tid, None)
    
    bl_s = f'{bl:.2f}' if bl is not None else '-'
    w_s = f'{w:.2f}' if w is not None else '-'
    v_s = f'{v:.2f}' if v is not None else '-'
    so_s = f'{so:.2f}' if so is not None else '-'
    g_s = f'{g:.2f}' if g is not None else '-'
    
    print(f"{tid:<10} {bl_s:<10} {w_s:<10} {v_s:<10} {so_s:<10} {g_s:<10}")
    
    if bl is not None: totals['bl'].append(bl)
    if w is not None: totals['ws'].append(w)
    if v is not None: totals['v10'].append(v)
    if so is not None: totals['so'].append(so)
    if g is not None: totals['gt'].append(g)

print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
def avg(lst):
    return f'{sum(lst)/len(lst):.3f}' if lst else '-'
print(f"{'AVG':<10} {avg(totals['bl']):<10} {avg(totals['ws']):<10} {avg(totals['v10']):<10} {avg(totals['so']):<10} {avg(totals['gt']):<10}")

# Delta vs BL-RAW
print(f"\n{'='*80}")
print(f"{'Δ vs BL-RAW':^80}")
print(f"{'='*80}")
print(f"{'Task':<10} {'WSKILL':<10} {'V10 Sel':<10} {'SkillOpt':<10} {'Base3(GT)':<10}")
for tid in test_tasks:
    bl = bl_raw.get(tid, None)
    w = ws.get(tid, None)
    v = max(v10_results[tid], key=lambda x: x[1])[1] if tid in v10_results else None
    so = skillopt.get(tid, None)
    g = gt_best.get(tid, None)
    
    if bl is not None:
        w_s = f'{w-bl:+.2f}' if w is not None else '-'
        v_s = f'{v-bl:+.2f}' if v is not None else '-'
        so_s = f'{so-bl:+.2f}' if so is not None else '-'
        g_s = f'{g-bl:+.2f}' if g is not None else '-'
        print(f"{tid:<10} {w_s:<10} {v_s:<10} {so_s:<10} {g_s:<10}")

# Save JSON
out = {
    'test_tasks': test_tasks,
    'bl_raw': {k: round(v, 3) for k, v in bl_raw.items()},
    'wskill': {k: round(v, 3) for k, v in ws.items()},
    'v10_selector': {tid: round(max(v10_results[tid], key=lambda x: x[1])[1], 3) for tid in test_tasks if tid in v10_results},
    'skillopt': {k: round(v, 3) for k, v in skillopt.items()},
    'baseline3_gt': {k: round(v, 3) for k, v in gt_best.items()},
}
out_path = os.path.join(eval_dir, 'comparison_data.json')
with open(out_path, 'w') as f:
    json.dump(out, f, indent=2)
print(f"\nSaved to {out_path}")