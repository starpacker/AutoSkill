"""Extract all step records from skill-opt training run."""
import json, os, glob

base = '/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458'

print("=== SKILL-OPT TRAINING STEP RECORDS ===")
for step_dir in sorted(glob.glob(os.path.join(base, 'steps', 'step_*'))):
    step_name = os.path.basename(step_dir)
    rec = os.path.join(step_dir, 'step_record.json')
    if os.path.exists(rec):
        with open(rec) as f:
            d = json.load(f)
        print(f"  {step_name}: "
              f"rollout_hard={d.get('rollout_hard','?'):<6} "
              f"rollout_soft={d.get('rollout_soft','?'):<8} "
              f"selection_hard={d.get('selection_hard','?'):<6} "
              f"selection_soft={d.get('selection_soft','?'):<8} "
              f"action={d.get('action','?'):<20} "
              f"best_score={d.get('best_score','?')}")

# Also check slow_update
print("\n=== SLOW UPDATE ===")
for epoch_dir in sorted(glob.glob(os.path.join(base, 'slow_update', 'epoch_*'))):
    epoch_name = os.path.basename(epoch_dir)
    for stage in ['rollout_curr', 'rollout_ref']:
        stage_dir = os.path.join(epoch_dir, stage)
        if os.path.exists(stage_dir):
            print(f"  {epoch_name}/{stage}: exists")
            # Check for any record files
            for f in os.listdir(stage_dir):
                if f.endswith('.json'):
                    print(f"    {f}")

print("\n=== SUMMARY DATA ===")

# Read all_results.json
summary = '/data/yjh/skill-transfer-eval/summary/all_results.json'
if os.path.exists(summary):
    with open(summary) as f:
        data = json.load(f)
    if isinstance(data, dict) and 'results' in data:
        results = data['results']
    elif isinstance(data, list):
        results = data
    else:
        results = [data]
    
    print(f"\nTotal entries in all_results.json: {len(results)}")
    for r in results:
        tid = r.get('task_id', '?')
        baselines = r.get('baseline', [])
        with_skill = r.get('with_skill', [])
        baseline_rewards = [b.get('reward', 0) for b in baselines]
        skill_rewards = [s.get('reward', 0) for s in with_skill]
        b_avg = sum(baseline_rewards) / len(baseline_rewards) if baselines else 0
        s_avg = sum(skill_rewards) / len(skill_rewards) if with_skill else 0
        print(f"  {tid}: baseline={b_avg:.3f} with_skill={s_avg:.3f} Δ={s_avg-b_avg:+.3f}")

# Read transfer_results.json
transfer = '/data/yjh/skill-transfer-eval/summary/transfer_results.json'
if os.path.exists(transfer):
    with open(transfer) as f:
        tdata = json.load(f)
    if isinstance(tdata, list):
        print(f"\nTransfer results: {len(tdata)} entries")
        for t in tdata:
            print(f"  {json.dumps(t, indent=2)[:200]}")
    else:
        print(f"\nTransfer results (dict): {json.dumps(tdata, indent=2)[:500]}")

# Read baseline3 / fewshot_transfer results
print("\n=== FEWSHOT TRANSFER RESULTS ===")
fewshot_base = '/data/yjh/skill-transfer-eval/fewshot_transfer'
for task_dir in sorted(glob.glob(os.path.join(fewshot_base, '*')))[:10]:
    task_name = os.path.basename(task_dir)
    # Check for harness.log
    log = os.path.join(task_dir, 'harness.log')
    if os.path.exists(log):
        with open(log) as f:
            content = f.read()
        import re
        m = re.search(r'"reward": ([0-9.]+)', content)
        if m:
            print(f"  {task_name}: reward={m.group(1)}")

# Check gt_fewshot_transfer
print("\n=== GT FEWSHOT TRANSFER (baseline3) ===")
gt_base = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
for task_dir in sorted(glob.glob(os.path.join(gt_base, '*')))[:15]:
    task_name = os.path.basename(task_dir)
    log = os.path.join(task_dir, 'harness.log')
    if os.path.exists(log):
        with open(log) as f:
            content = f.read()
        import re
        m = re.search(r'"reward": ([0-9.]+)', content)
        if m:
            print(f"  {task_name}: reward={m.group(1)}")

# Read the baseline (no skill) results from skill-transfer-eval
print("\n=== BASELINE (no skill) from skill-transfer-eval ===")
baseline_dir = '/data/yjh/skill-transfer-eval/baseline'
baseline_scores = {}
for task_dir in sorted(glob.glob(os.path.join(baseline_dir, '*'))):
    task_name = os.path.basename(task_dir)
    # Extract task ID
    tid = task_name.split('_')[0]
    log = os.path.join(task_dir, 'harness.log')
    if os.path.exists(log):
        with open(log) as f:
            content = f.read()
        import re
        m = re.search(r'"reward": ([0-9.]+)', content)
        if m:
            reward = float(m.group(1))
            if tid not in baseline_scores:
                baseline_scores[tid] = []
            baseline_scores[tid].append(reward)

for tid, rewards in sorted(baseline_scores.items()):
    avg = sum(rewards) / len(rewards)
    print(f"  {tid}: {rewards} avg={avg:.3f}")

print("\nDone!")