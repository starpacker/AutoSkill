#!/usr/bin/env python3
"""Comprehensive judge model comparison across all runs."""
import json, os, glob

basedir = "/data/yjh/skill-transfer-eval/baseline"
wsdir = "/data/yjh/skill-transfer-eval/with_skill"
transdir = "/data/yjh/skill-transfer-eval/transfer_pruned"

def check_run(dirpath, label):
    f = os.path.join(dirpath, "logs/run_summary.json")
    if not os.path.exists(f):
        return
    d = json.load(open(f))
    fr = d.get("final_result", {})
    dirname = os.path.basename(dirpath)
    print(f"  [{label}] {dirname}: reward={d.get('reward')}, judge={fr.get('model')}, score={fr.get('total_score')}, status={d.get('status')}, rounds={d.get('rounds')}")

print("=" * 80)
print("ALL BASELINE RUNS (192248 batch)")
print("=" * 80)
for d in sorted(glob.glob(os.path.join(basedir, "*192248*"))):
    check_run(d, "BASELINE")

print("\n" + "=" * 80)
print("ALL BASELINE RUNS (160657 batch)")
print("=" * 80)
for d in sorted(glob.glob(os.path.join(basedir, "*160657*"))):
    check_run(d, "BASELINE")

print("\n" + "=" * 80)
print("ALL WITH_SKILL RUNS (192248 batch)")
print("=" * 80)
for d in sorted(glob.glob(os.path.join(wsdir, "*192248*"))):
    check_run(d, "SKILL")

print("\n" + "=" * 80)
print("ALL WITH_SKILL RUNS (160657 batch)")
print("=" * 80)
for d in sorted(glob.glob(os.path.join(wsdir, "*160657*"))):
    check_run(d, "SKILL")

print("\n" + "=" * 80)
print("ALL TRANSFER (PRUNED) RUNS")
print("=" * 80)
for d in sorted(glob.glob(os.path.join(transdir, "*"))):
    check_run(d, "TRANSFER")