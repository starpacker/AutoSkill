import json, os, glob

results_dir = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
scores = []
failed = []

for task_dir in sorted(os.listdir(results_dir)):
    task_path = os.path.join(results_dir, task_dir)
    if not os.path.isdir(task_path):
        continue
    for fname in ['run_summary.json', 'summary.json', 'judge_result.json']:
        fpath = os.path.join(task_path, fname)
        if os.path.exists(fpath):
            try:
                d = json.load(open(fpath))
                score = d.get('reward') or d.get('total_score') or d.get('score') or d.get('soft')
                if score is not None:
                    scores.append((task_dir, float(score)))
                    break
                else:
                    print(f'{task_dir}: keys={list(d.keys())}, vals={d}')
                    failed.append(task_dir)
            except Exception as e:
                print(f'{task_dir}: error reading {fname}: {e}')
                failed.append(task_dir)
    else:
        json_files = glob.glob(os.path.join(task_path, '*.json'))
        if json_files:
            print(f'{task_dir}: no summary file, found: {[os.path.basename(x) for x in json_files]}')
        else:
            all_files = os.listdir(task_path)
            print(f'{task_dir}: no json files, contents: {all_files[:10]}')
        failed.append(task_dir)

if scores:
    print()
    print('='*60)
    print('BASELINE 3 (GT Code Few-Shot) RESULTS')
    print(f'Total completed: {len(scores)}/{len(scores)+len(failed)}')
    print(f'Failed: {len(failed)}')
    print()
    for task, score in scores:
        status = 'PASS' if score >= 0.5 else 'FAIL'
        print(f'  [{status}] {task}: {score:.4f}')
    print()
    mean_score = sum(s for _, s in scores) / len(scores)
    print(f'  MEAN SCORE: {mean_score:.4f}')
    print(f'  HARD ACC (>=0.5): {sum(1 for _, s in scores if s >= 0.5)}/{len(scores)} = {sum(1 for _, s in scores if s >= 0.5)/len(scores)*100:.1f}%')
    print('='*60)
else:
    print('No scores found!')