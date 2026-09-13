#!/usr/bin/env python3
"""
BioDSBench Results Indexer
==========================
Scans all experiment results on the server and produces a comprehensive JSON index.
Usage: python3 /data/yjh/skill-transfer-eval/index_results.py
Output: /data/yjh/skill-transfer-eval/results_index.json
"""
import json, os, glob, re
from collections import defaultdict

BASE = '/data/yjh/skill-transfer-eval'
SUMMARY = os.path.join(BASE, 'summary')
GENERALIZED = os.path.join(BASE, 'generalized')
TRANSFER = os.path.join(BASE, 'transfer')
BASELINE_DIR = os.path.join(BASE, 'baseline')
WITH_SKILL = os.path.join(BASE, 'with-skill')
SKILL_BUNDLES = '/data/yjh/biomnibench-skill-bundles'

index = {
    "meta": {
        "generated": "2026-08-11",
        "server": "server1",
        "base_dir": BASE,
        "description": "BioDSBench skill transfer evaluation results index"
    },
    "baselines": {},      # task -> {deepseek, gemini} baseline scores
    "oracles": {},        # task -> {deepseek, gemini} oracle scores
    "pruned_skills": {},  # task -> {source, skill_summary, operations}
    "transfers": [],      # list of all transfer experiments
    "summary": {
        "baseline_avg_gemini": 0,
        "oracle_avg_gemini": 0,
        "total_transfer_runs": 0
    }
}

# ============================================================
# 1. BASELINE & ORACLE (from summary files)
# ============================================================

# Gemini baseline (0-100 scale)
gemini_file = os.path.join(SUMMARY, 'gemini_results.json')
if os.path.exists(gemini_file):
    gd = json.load(open(gemini_file))
    for r in gd.get('results', []):
        task = r['task']
        index['baselines'].setdefault(task, {})['gemini'] = r['baseline']
        index['oracles'].setdefault(task, {})['gemini'] = r['oracle']
    index['summary']['baseline_avg_gemini'] = gd.get('stats', {}).get('baseline_avg', 0)
    index['summary']['oracle_avg_gemini'] = gd.get('stats', {}).get('oracle_avg', 0)

# DeepSeek baseline (from all_results.json, 0-1 scale)
ds_file = os.path.join(SUMMARY, 'all_results.json')
if os.path.exists(ds_file):
    ds = json.load(open(ds_file))
    for task, data in ds.get('results', {}).items():
        bl = data.get('baseline', data.get('no_skill'))
        if bl is not None:
            index['baselines'].setdefault(task, {})['deepseek'] = round(bl, 3)
        orc = data.get('oracle', data.get('with_skill'))
        if orc is not None:
            index['oracles'].setdefault(task, {})['deepseek'] = round(orc, 3)

# ============================================================
# 2. PRUNED SKILLS (in skills/<task>/skills/generalized-pruned-transfer/)
# ============================================================
skills_root = os.path.join(BASE, 'skills')
if os.path.exists(skills_root):
    for task in sorted(os.listdir(skills_root)):
        task_skills_dir = os.path.join(skills_root, task, 'skills')
        if not os.path.exists(task_skills_dir):
            continue
        for skill_name in sorted(os.listdir(task_skills_dir)):
            skill_path = os.path.join(task_skills_dir, skill_name)
            if not os.path.isdir(skill_path):
                continue
            meta_file = os.path.join(skill_path, 'metadata.json')
            meta = {}
            if os.path.exists(meta_file):
                try:
                    meta = json.load(open(meta_file))
                except:
                    pass
            index['pruned_skills'].setdefault(task, []).append({
                "skill_name": skill_name,
                "skill_dir": skill_path,
                "source_task": meta.get('source_task', '?'),
                "target_task": meta.get('target_task', task),
                "deployed_at": meta.get('deployed_at', '?'),
                "generalized_source": meta.get('generalized_skill_source', '?'),
                "similarity": meta.get('similarity', None),
            })

# Also scan oracle skills (from skill bundles)
if os.path.exists('/data/yjh/biomnibench-skill-bundles'):
    for task in sorted(os.listdir('/data/yjh/biomnibench-skill-bundles')):
        bundle_skills = os.path.join('/data/yjh/biomnibench-skill-bundles', task, 'skills')
        if not os.path.exists(bundle_skills):
            continue
        for skill_name in sorted(os.listdir(bundle_skills)):
            skill_path = os.path.join(bundle_skills, skill_name)
            if not os.path.isdir(skill_path):
                continue
            # Check if we already have this task
            if task not in index['pruned_skills']:
                index['pruned_skills'][task] = []
            index['pruned_skills'][task].append({
                "skill_name": skill_name,
                "skill_dir": skill_path,
                "type": "oracle",
                "source_task": skill_name.replace('oracle-', ''),
                "target_task": task,
            })

# ============================================================
# 3. TRANSFER EXPERIMENTS
# ============================================================

# 3a. Old transfer results (from transfer/ dir)
old_transfer_file = os.path.join(SUMMARY, 'transfer_results.json')
if os.path.exists(old_transfer_file):
    td = json.load(open(old_transfer_file))
    for source, targets in td.get('results', {}).items():
        for target, data in targets.items():
            if isinstance(data, dict):
                index['transfers'].append({
                    "type": "old-transfer",
                    "source": source,
                    "target": target,
                    "reward": round(data.get('reward', 0), 3) if isinstance(data.get('reward'), (int, float)) else data.get('reward'),
                    "baseline": data.get('baseline'),
                    "oracle": data.get('oracle'),
                    "delta": round(data.get('delta', 0), 3) if isinstance(data.get('delta'), (int, float)) else data.get('delta'),
                    "dir": None
                })

# 3b. Generalized transfer experiments (from generalized/ dir)
exp_types = {
    'generalized-transfer': 'generalized-transfer',
    'generalized-cross': 'generalized-cross',
    'generalized-within': 'generalized-within',
    'raw-cross': 'raw-cross',
    'raw-within': 'raw-within',
    'expand-within': 'expand-within',
    'expand-cross': 'expand-cross',
}

if os.path.exists(GENERALIZED):
    for dname in sorted(os.listdir(GENERALIZED)):
        if dname == '.judge_private':
            continue
        rs = os.path.join(GENERALIZED, dname, 'logs/run_summary.json')
        if not os.path.exists(rs):
            continue
        try:
            data = json.load(open(rs))
        except:
            continue

        reward = data.get('reward')
        if isinstance(reward, (int, float)):
            reward = round(reward, 3)

        # Parse dir name
        parts = dname.split('_', 3)
        target = parts[0] if len(parts) > 0 else '?'
        date = parts[1] if len(parts) > 1 else '?'
        time = parts[2] if len(parts) > 2 else '?'
        exp_info = parts[3] if len(parts) > 3 else '?'

        # Detect experiment type
        etype = 'other'
        source = None
        for key, val in exp_types.items():
            if key in exp_info:
                etype = val
                break
        # Try to extract source
        src_match = re.search(r'da-[\d]+-[\d]+', exp_info.replace('generalized-transfer-da-', '').replace('generalized-transfer_', ''))
        if src_match:
            source = src_match.group(0)

        index['transfers'].append({
            "type": etype,
            "target": target,
            "source": source,
            "date": date,
            "time": time,
            "reward": reward,
            "dir": dname,
            "rounds": data.get('rounds', 0),
            "status": 'OK' if data.get('status') == 'finished' else (data.get('status', '?')),
        })

# ============================================================
# 4. SUMMARY STATS
# ============================================================
index['summary']['total_transfer_runs'] = len(index['transfers'])

# Group by type
by_type = defaultdict(list)
for t in index['transfers']:
    by_type[t['type']].append(t)

index['summary']['by_type'] = {}
for etype, items in sorted(by_type.items()):
    rewards = [it['reward'] for it in items if isinstance(it['reward'], (int, float))]
    index['summary']['by_type'][etype] = {
        "count": len(items),
        "avg_reward": round(sum(rewards)/len(rewards), 2) if rewards else None,
        "best_reward": round(max(rewards), 2) if rewards else None,
        "worst_reward": round(min(rewards), 2) if rewards else None,
    }

# Write output
out = os.path.join(BASE, 'results_index.json')
json.dump(index, open(out, 'w'), indent=2, ensure_ascii=False)
print(f"??Index written to {out}")
print(f"   - {len(index['baselines'])} tasks with baselines")
print(f"   - {len(index['oracles'])} tasks with oracles")
print(f"   - {len(index['pruned_skills'])} tasks with pruned skills")
print(f"   - {len(index['transfers'])} transfer runs")
print(f"   - Experiment types: {list(index['summary']['by_type'].keys())}")
