"""Build final comparison table: BL-RAW, WSKILL, V10, SkillOpt, Base3(GT) for 13 tasks with full coverage."""
import json, os, glob, re

# 13 tasks with all 4 columns (BL-RAW, WSKILL, V10, GT)
# plus SkillOpt being evaluated now
ALL_TASKS = [
    'da-10-1', 'da-12-2', 'da-13-6', 'da-15-7', 'da-15-8',
    'da-19-6', 'da-20-4', 'da-24-3', 'da-25-1', 'da-26-4',
    'da-4-7', 'da-8-3', 'da-9-1',
]

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458'

# =============================================
# 1. BL-RAW
# =============================================
summary = '/data/yjh/skill-transfer-eval/summary/all_results.json'
bl_raw = {}
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    for e in data.get('tasks', []):
        tid = e.get('task_id', '')
        if tid in ALL_TASKS:
            rewards = [b.get('reward', 0) for b in e.get('baseline', [])]
            if rewards:
                bl_raw[tid] = sum(rewards) / len(rewards)

# =============================================
# 2. WSKILL
# =============================================
ws = {}
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    for e in data.get('tasks', []):
        tid = e.get('task_id', '')
        if tid in ALL_TASKS:
            rewards = [s.get('reward', 0) for s in e.get('with_skill', [])]
            if rewards:
                ws[tid] = sum(rewards) / len(rewards)

# =============================================
# 3. V10 Selector (from generalized/ dirs - logs/run_summary.json)
# =============================================
v10_base = '/data/yjh/skill-transfer-eval/generalized'
v10_results = {}
for d in sorted(os.listdir(v10_base)):
    dp = os.path.join(v10_base, d)
    if os.path.isdir(dp):
        tid = d.split('_')[0]
        if tid not in ALL_TASKS:
            continue
        sf = os.path.join(dp, 'logs', 'run_summary.json')
        if os.path.exists(sf):
            try:
                with open(sf) as f:
                    sd = json.load(f)
                r = sd.get('reward', 0)
                if r > 0:
                    v10_results.setdefault(tid, []).append(r)
            except:
                pass

# =============================================
# 4. SkillOpt (from both test_eval_10tasks and test_eval_9more)
# =============================================
def read_skillopt(eval_dir):
    results = {}
    if not os.path.isdir(eval_dir):
        return results
    for tid in ALL_TASKS:
        task_dirs = sorted(glob.glob(os.path.join(eval_dir, f'test_eval_{tid}_*')))
        if task_dirs:
            latest = task_dirs[-1]
            log = os.path.join(latest, 'harness.log')
            if os.path.exists(log):
                with open(log) as f:
                    content = f.read()
                m = re.search(r'"reward": ([0-9.]+)', content)
                if m:
                    results[tid] = float(m.group(1))
    return results

skillopt_10 = read_skillopt(os.path.join(base, 'test_eval_10tasks'))
skillopt_9 = read_skillopt(os.path.join(base, 'test_eval_9more'))

# Merge: prefer 9more if available (newer), else use 10tasks
skillopt = {}
for tid in ALL_TASKS:
    if tid in skillopt_9:
        skillopt[tid] = skillopt_9[tid]
    elif tid in skillopt_10:
        skillopt[tid] = skillopt_10[tid]

# =============================================
# 5. Baseline3 (GT fewshot transfer - best per task)
# =============================================
gt_base = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
gt_results = {}
for task_dir in sorted(glob.glob(os.path.join(gt_base, '*'))):
    dname = os.path.basename(task_dir)
    tid = dname.split('_')[0]
    if tid in ALL_TASKS:
        sf = os.path.join(task_dir, 'logs', 'run_summary.json')
        if os.path.exists(sf):
            with open(sf) as f:
                sd = json.load(f)
            reward = sd.get('reward', 0)
            gt_results.setdefault(tid, []).append(reward)

gt_best = {tid: max(vals) for tid, vals in gt_results.items()}

# =============================================
# Print combined table
# =============================================
print(f"\n{'='*90}")
print(f"{'COMPARISON TABLE — 13 Tasks with Full Coverage':^90}")
print(f"{'='*90}")
print(f"{'Task':<10} {'BL-RAW':<10} {'WSKILL':<10} {'V10 Sel':<10} {'SkillOpt':<10} {'Base3(GT)':<10} {'Best':<10}")
print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

totals = {'bl': [], 'ws': [], 'v10': [], 'so': [], 'gt': []}
for tid in ALL_TASKS:
    bl = bl_raw.get(tid, None)
    w = ws.get(tid, None)
    v = max(v10_results[tid]) if tid in v10_results and v10_results[tid] else None
    so = skillopt.get(tid, None)
    g = gt_best.get(tid, None)
    
    # Find best among all methods
    candidates = [x for x in [w, v, so, g] if x is not None]
    best_val = max(candidates) if candidates else None
    best_s = f'{best_val:.2f}' if best_val is not None else '-'
    
    bl_s = f'{bl:.2f}' if bl is not None else '-'
    w_s = f'{w:.2f}' if w is not None else '-'
    v_s = f'{v:.2f}' if v is not None else '-'
    so_s = f'{so:.2f}' if so is not None else '-'
    g_s = f'{g:.2f}' if g is not None else '-'
    
    # Highlight best
    best_str = best_s
    if w is not None and w == best_val: best_str = 'WSKILL'
    elif v is not None and v == best_val: best_str = 'V10'
    elif so is not None and so == best_val: best_str = 'SkillOpt'
    elif g is not None and g == best_val: best_str = 'GT'
    
    print(f"{tid:<10} {bl_s:<10} {w_s:<10} {v_s:<10} {so_s:<10} {g_s:<10} {best_str:<10}")
    
    if bl is not None: totals['bl'].append(bl)
    if w is not None: totals['ws'].append(w)
    if v is not None: totals['v10'].append(v)
    if so is not None: totals['so'].append(so)
    if g is not None: totals['gt'].append(g)

print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")
def avg(lst):
    return f'{sum(lst)/len(lst):.3f}' if lst else '-'
print(f"{'AVG':<10} {avg(totals['bl']):<10} {avg(totals['ws']):<10} {avg(totals['v10']):<10} {avg(totals['so']):<10} {avg(totals['gt']):<10}")

# Delta vs BL-RAW
print(f"\n{'='*80}")
print(f"{'Δ vs BL-RAW':^80}")
print(f"{'='*80}")
print(f"{'Task':<10} {'WSKILL':<10} {'V10 Sel':<10} {'SkillOpt':<10} {'Base3(GT)':<10}")
for tid in ALL_TASKS:
    bl = bl_raw.get(tid, None)
    w = ws.get(tid, None)
    v = max(v10_results[tid]) if tid in v10_results and v10_results[tid] else None
    so = skillopt.get(tid, None)
    g = gt_best.get(tid, None)
    if bl is not None:
        w_s = f'{w-bl:+.2f}' if w is not None else '-'
        v_s = f'{v-bl:+.2f}' if v is not None else '-'
        so_s = f'{so-bl:+.2f}' if so is not None else '-'
        g_s = f'{g-bl:+.2f}' if g is not None else '-'
        print(f"{tid:<10} {w_s:<10} {v_s:<10} {so_s:<10} {g_s:<10}")

# Task descriptions
print(f"\n{'='*80}")
print(f"{'TASK DESCRIPTIONS':^80}")
print(f"{'='*80}")
desc = {
    'da-10-1': 'predictive-modeling (TCR-pMEC)',
    'da-12-2': 'pathway-enrichment (V(D)J-seq)',
    'da-13-6': 'motif-scanning (RNA-seq)',
    'da-15-7': 'co-expression-networks (RNA-seq)',
    'da-15-8': 'co-expression-networks (RNA-seq)',
    'da-19-6': 'chromatin-profiling (scATAC-seq)',
    'da-20-4': 'pathway-enrichment (Proteomics)',
    'da-24-3': 'peak-calling (Bulk-ATAC-seq)',
    'da-25-1': 'variant-calling (RNA-seq)',
    'da-26-4': 'peak-calling (scATAC-seq)',
    'da-4-7': 'tcr-repertoire (TCR)',
    'da-8-3': 'association-testing (Bulk-ATAC-seq)',
    'da-9-1': 'differential-accessibility (scATAC-seq)',
}
for tid in ALL_TASKS:
    print(f"  {tid}: {desc.get(tid, '?')}")

# Save JSON
out = {
    'test_tasks': ALL_TASKS,
    'bl_raw': {k: round(v, 3) for k, v in bl_raw.items()},
    'wskill': {k: round(v, 3) for k, v in ws.items()},
    'v10_selector': {tid: round(max(v10_results[tid]), 3) for tid in ALL_TASKS if tid in v10_results and v10_results[tid]},
    'skillopt': {k: round(v, 3) for k, v in skillopt.items()},
    'baseline3_gt': {k: round(v, 3) for k, v in gt_best.items()},
}
eval_dir = os.path.join(base, 'test_eval_9more')
out_path = os.path.join(eval_dir, 'comparison_data.json')
with open(out_path, 'w') as f:
    json.dump(out, f, indent=2)
print(f"\nSaved to {out_path}")