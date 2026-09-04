"""Find all tasks with overlapping V10, GT, and BL-RAW data, then identify which need SkillOpt eval."""
import json, os, glob, re

# =============================================
# 1. BL-RAW + WSKILL from all_results.json
# =============================================
summary = '/data/yjh/skill-transfer-eval/summary/all_results.json'
bl_raw = {}
wskill = {}
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    for e in data.get('tasks', []):
        tid = e.get('task_id', '')
        bl = [b.get('reward', 0) for b in e.get('baseline', [])]
        ws = [s.get('reward', 0) for s in e.get('with_skill', [])]
        if bl: bl_raw[tid] = sum(bl) / len(bl)
        if ws: wskill[tid] = sum(ws) / len(ws)

print(f"BL-RAW has {len(bl_raw)} tasks")
print(f"WSKILL has {len(wskill)} tasks")

# =============================================
# 2. V10 results from top-level dirs
# =============================================
v10_base = '/data/yjh/skill-transfer-eval'
v10_results = {}
for d in os.listdir(v10_base):
    dpath = os.path.join(v10_base, d)
    if os.path.isdir(dpath) and d.startswith('da-'):
        manifest = os.path.join(dpath, 'run_manifest.json')
        if os.path.exists(manifest):
            with open(manifest) as f:
                mdata = json.load(f)
            if isinstance(mdata, list):
                rewards = [m.get('reward', 0) for m in mdata if 'reward' in m]
                if rewards:
                    v10_results[d] = max(rewards)

# Also check fewshot_transfer and generalized
for src_dir in ['fewshot_transfer', 'generalized', 'transfer', 'with-skill']:
    sdir = os.path.join(v10_base, src_dir)
    if os.path.isdir(sdir):
        for d in os.listdir(sdir):
            dpath = os.path.join(sdir, d)
            if os.path.isdir(dpath):
                tid = d.split('_')[0] if '_' in d else d
                # Check for run_summary.json
                sf = os.path.join(dpath, 'logs', 'run_summary.json')
                if os.path.exists(sf):
                    with open(sf) as f:
                        sd = json.load(f)
                    r = sd.get('reward', 0)
                    if r > 0:
                        v10_results.setdefault(tid, []).append(r)
                # Check harness.log
                hl = os.path.join(dpath, 'harness.log')
                if os.path.exists(hl):
                    with open(hl) as f:
                        c = f.read()
                    m = re.search(r'"reward": ([0-9.]+)', c)
                    if m:
                        r = float(m.group(1))
                        v10_results.setdefault(tid, []).append(r)

# Also check the skill_selector_v10 outputs
v10_sel = '/data/yjh/skill-transfer-eval/skill_selector_v10'
if os.path.isdir(v10_sel):
    for root, dirs, files in os.walk(v10_sel):
        for f in files:
            if f == 'run_summary.json' or f == 'harness.log':
                fpath = os.path.join(root, f)
                # Walk up to find task ID
                parts = fpath.split('/')
                for p in parts:
                    if p.startswith('da-'):
                        tid = p.split('_')[0]
                        break
                else:
                    continue
                with open(fpath) as fh:
                    c = fh.read()
                if f == 'run_summary.json':
                    try:
                        sd = json.loads(c)
                        r = sd.get('reward', 0)
                        if r > 0:
                            v10_results.setdefault(tid, []).append(r)
                    except:
                        pass
                else:
                    m = re.search(r'"reward": ([0-9.]+)', c)
                    if m:
                        r = float(m.group(1))
                        if r > 0:
                            v10_results.setdefault(tid, []).append(r)

# Flatten v10_results (take max if list)
v10_best = {}
for tid, vals in v10_results.items():
    if isinstance(vals, list):
        v10_best[tid] = max(vals)
    else:
        v10_best[tid] = vals

print(f"V10 has {len(v10_best)} tasks: {sorted(v10_best.keys())}")

# =============================================
# 3. GT fewshot results
# =============================================
gt_base = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
gt_results = {}
for d in sorted(os.listdir(gt_base)):
    dpath = os.path.join(gt_base, d)
    if os.path.isdir(dpath):
        tid = d.split('_')[0]
        sf = os.path.join(dpath, 'logs', 'run_summary.json')
        if os.path.exists(sf):
            with open(sf) as f:
                sd = json.load(f)
            r = sd.get('reward', 0)
            gt_results.setdefault(tid, []).append(r)

gt_best = {tid: max(vals) for tid, vals in gt_results.items()}
print(f"GT has {len(gt_best)} tasks: {sorted(gt_best.keys())}")

# =============================================
# 4. Find overlap
# =============================================
all_tasks = set(bl_raw.keys()) | set(wskill.keys()) | set(v10_best.keys()) | set(gt_best.keys())
print(f"\n{'='*80}")
print(f"{'ALL TASKS COMPARISON':^80}")
print(f"{'='*80}")
print(f"{'Task':<10} {'BL-RAW':<10} {'WSKILL':<10} {'V10':<10} {'GT':<10} {'Overlap':<10}")
print(f"{'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10} {'-'*10}")

# Candidates: tasks with V10 + GT + BL-RAW (at least 3/4)
candidates = []
for tid in sorted(all_tasks):
    bl = bl_raw.get(tid, None)
    ws = wskill.get(tid, None)
    v10 = v10_best.get(tid, None)
    gt = gt_best.get(tid, None)
    
    present = sum(1 for x in [bl, ws, v10, gt] if x is not None)
    overlap = '4/4' if present == 4 else ('3/4' if present == 3 else f'{present}/4')
    
    bl_s = f'{bl:.2f}' if bl is not None else '-'
    ws_s = f'{ws:.2f}' if ws is not None else '-'
    v10_s = f'{v10:.2f}' if v10 is not None else '-'
    gt_s = f'{gt:.2f}' if gt is not None else '-'
    
    print(f"{tid:<10} {bl_s:<10} {ws_s:<10} {v10_s:<10} {gt_s:<10} {overlap:<10}")
    
    if present >= 3:
        candidates.append((tid, bl, ws, v10, gt))

print(f"\n=== CANDIDATES (3+ columns present) ===")
for tid, bl, ws, v10, gt in candidates:
    missing = []
    if bl is None: missing.append('BL')
    if ws is None: missing.append('WS')
    if v10 is None: missing.append('V10')
    if gt is None: missing.append('GT')
    print(f"  {tid}: missing={missing}")

# Tasks that need SkillOpt run (have V10+GT+BL but no SkillOpt yet)
# SkillOpt would be the 5th column
print(f"\n=== TASKS TO RUN SKILLOPT EVAL ON ===")
print(f"Tasks with V10+GT+BL that we could eval with SkillOpt best_skill.md:")
for tid, bl, ws, v10, gt in candidates:
    # Check if we already have SkillOpt result from the 10 test tasks
    print(f"  {tid}: BL={bl:.3f if bl else 0} WS={ws:.3f if ws else 0} V10={v10:.3f if v10 else 0} GT={gt:.3f if gt else 0}")

# Save full data
out = {
    'bl_raw': {k: round(v, 3) for k, v in bl_raw.items()},
    'wskill': {k: round(v, 3) for k, v in wskill.items()},
    'v10': {k: round(v, 3) for k, v in v10_best.items()},
    'gt_fewshot': {k: round(v, 3) for k, v in gt_best.items()},
}
out_path = os.path.join('/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/test_eval_10tasks', 'all_methods_data.json')
with open(out_path, 'w') as f:
    json.dump(out, f, indent=2)
print(f"\nSaved to {out_path}")