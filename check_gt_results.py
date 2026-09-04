"""Check all GT fewshot results for our 10 test tasks."""
import json, os, glob, sys

test_tasks = {'da-5-1', 'da-20-3', 'da-19-6', 'da-17-3', 'da-18-1', 
              'da-8-2', 'da-10-1', 'da-15-2', 'da-4-7', 'da-12-2'}

d = '/data/yjh/skill-transfer-eval/gt_fewshot_transfer'
for f in sorted(glob.glob(os.path.join(d, '*'))):
    dname = os.path.basename(f)
    tid = dname.split('_')[0]
    if tid in test_tasks or True:  # show all
        sf = os.path.join(f, 'logs', 'run_summary.json')
        if os.path.exists(sf):
            with open(sf) as fh:
                data = json.load(fh)
            reward = data.get('reward', '?')
            marker = ' <--' if tid in test_tasks else ''
            print(f"  {dname}: reward={reward}{marker}")
        else:
            print(f"  {dname}: no run_summary.json")