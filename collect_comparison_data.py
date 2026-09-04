"""Collect all comparison data from skill-opt training run and skill-transfer-eval."""
import json, os, glob, re

# =============================================
# 1. Skill-Opt training step scores (Run 193458)
# =============================================
base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458'
steps_dir = os.path.join(base, 'steps')
skillopt_scores = {}
for step_dir in sorted(glob.glob(os.path.join(steps_dir, 'step_*'))):
    step_name = os.path.basename(step_dir)
    meta = os.path.join(step_dir, 'metadata.json')
    if os.path.exists(meta):
        with open(meta) as f:
            d = json.load(f)
        skillopt_scores[step_name] = {
            'hard': d.get('hard', '?'),
            'soft': d.get('soft', '?'),
            'accepted': d.get('accepted', '?'),
        }
        print(f"{step_name}: hard={d.get('hard','?')} soft={d.get('soft','?')} accepted={d.get('accepted','?')}")

print(f"\nTotal steps: {len(skillopt_scores)}")

# =============================================
# 2. Best skill (from slow_update or best checkpoint)
# =============================================
best_meta = os.path.join(base, 'best_skill_metadata.json')
if os.path.exists(best_meta):
    with open(best_meta) as f:
        bm = json.load(f)
    print(f"\nBest skill: {bm}")

# =============================================
# 3. Skill-Transfer-Eval results
# =============================================
transfer_base = '/data/yjh/skill-transfer-eval/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458'
if os.path.exists(transfer_base):
    transfer_results = {}
    for result_file in glob.glob(os.path.join(transfer_base, '**', 'results.json'), recursive=True):
        with open(result_file) as f:
            tr = json.load(f)
        for item in tr:
            tid = item.get('id', '?')
            transfer_results[tid] = item
            print(f"transfer {tid}: hard={item.get('hard','?')} soft={item.get('soft','?')}")
    print(f"\nTotal transfer results: {len(transfer_results)}")
else:
    print(f"\nNo transfer results at {transfer_base}")

# =============================================
# 4. All results from summary
# =============================================
summary = '/data/yjh/skill-transfer-eval/summary/all_results.json'
if os.path.exists(summary):
    with open(summary) as f:
        all_r = json.load(f)
    print(f"\nSummary all_results.json has {len(all_r)} entries")
    # Show first few
    for i, r in enumerate(all_r[:5]):
        print(f"  [{i}] {json.dumps(r, indent=2)[:200]}")
else:
    print(f"\nNo summary file at {summary}")

# =============================================
# 5. Check for baseline3 results
# =============================================
baseline3_dir = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
if os.path.exists(baseline3_dir):
    b3_results = {}
    for result_file in glob.glob(os.path.join(baseline3_dir, '**', 'results.json'), recursive=True):
        with open(result_file) as f:
            try:
                b3 = json.load(f)
                for item in (b3 if isinstance(b3, list) else [b3]):
                    tid = item.get('id', '?')
                    b3_results[tid] = item
            except:
                pass
    print(f"\nBaseline3 results: {len(b3_results)}")
    for tid, r in sorted(b3_results.items())[:10]:
        print(f"  {tid}: {r}")