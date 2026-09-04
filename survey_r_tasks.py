"""Survey R tasks in biomnibench-organized and skill-transfer-eval."""
import json, os, glob

BASE = "/data/yjh/biomnibench-organized"
TRANSFER = "/data/yjh/skill-transfer-eval"

# =============================================
# 1. List all tasks with language info
# =============================================
print("=" * 70)
print("ALL TASKS IN biomnibench-organized")
print("=" * 70)
tasks = sorted(os.listdir(BASE))
print(f"Total tasks: {len(tasks)}")

# Categorize by language (check for .R files or r-scripts)
r_tasks = []
py_tasks = []
unknown = []

for tid in tasks:
    task_dir = os.path.join(BASE, tid)
    if not os.path.isdir(task_dir):
        continue
    
    # Check for R scripts
    r_files = []
    py_files = []
    for root, dirs, files in os.walk(task_dir):
        for f in files:
            if f.endswith('.R') or f.endswith('.r'):
                r_files.append(os.path.join(root, f))
            if f.endswith('.py'):
                py_files.append(os.path.join(root, f))
    
    # Check envs directory for clues
    env_dir = os.path.join(task_dir, 'envs')
    has_r = len(r_files) > 0
    has_py = len(py_files) > 0
    
    # Also check skill files
    skill_file = os.path.join(task_dir, 'skill.md')
    skill_content = ""
    if os.path.exists(skill_file):
        with open(skill_file) as f:
            skill_content = f.read()
    
    uses_r = 'R' in skill_content or 'r-' in skill_content or 'library(' in skill_content
    uses_py = 'python' in skill_content.lower() or 'import ' in skill_content or 'pip ' in skill_content
    
    if has_r and not has_py:
        r_tasks.append(tid)
    elif has_py and not has_r:
        py_tasks.append(tid)
    elif has_r and has_py:
        # Check which is primary
        if uses_r and not uses_py:
            r_tasks.append(tid)
        else:
            py_tasks.append(tid)
    else:
        # No files found, check skill
        if uses_r:
            r_tasks.append(tid)
        elif uses_py:
            py_tasks.append(tid)
        else:
            unknown.append(tid)

print(f"\nPython tasks: {len(py_tasks)}")
print(f"R tasks: {len(r_tasks)}")
print(f"Unknown: {len(unknown)}")

print(f"\n--- Python tasks ({len(py_tasks)}) ---")
for t in sorted(py_tasks):
    print(f"  {t}")
print(f"\n--- R tasks ({len(r_tasks)}) ---")
for t in sorted(r_tasks):
    print(f"  {t}")
if unknown:
    print(f"\n--- Unknown ({len(unknown)}) ---")
    for t in sorted(unknown):
        print(f"  {t}")

# =============================================
# 2. Check skill-transfer-eval data for R tasks
# =============================================
print("\n" + "=" * 70)
print("SKILL-TRANSFER-EVAL COVERAGE FOR R TASKS")
print("=" * 70)

# Summary file
summary_file = os.path.join(TRANSFER, 'summary', 'all_results.json')
r_in_summary = []
if os.path.exists(summary_file):
    with open(summary_file) as f:
        data = json.load(f)
    for e in data.get('tasks', []):
        tid = e.get('task_id', '')
        if tid in r_tasks:
            bl = [b.get('reward', 0) for b in e.get('baseline', [])]
            ws = [s.get('reward', 0) for s in e.get('with_skill', [])]
            bl_avg = sum(bl)/len(bl) if bl else '-'
            ws_avg = sum(ws)/len(ws) if ws else '-'
            r_in_summary.append(tid)
            print(f"  {tid}: BL-RAW={bl_avg}, WSKILL={ws_avg}")

print(f"R tasks in summary: {len(r_in_summary)}/{len(r_tasks)}")

# GT fewshot
gt_base = os.path.join(TRANSFER, 'gt_fewshot_transfer')
r_in_gt = []
if os.path.isdir(gt_base):
    for d in sorted(os.listdir(gt_base)):
        dp = os.path.join(gt_base, d)
        if os.path.isdir(dp):
            tid = d.split('_')[0]
            if tid in r_tasks:
                sf = os.path.join(dp, 'logs', 'run_summary.json')
                if os.path.exists(sf):
                    with open(sf) as f:
                        sd = json.load(f)
                    r = sd.get('reward', 0)
                    r_in_gt.append(tid)
                    print(f"  GT {tid}: reward={r}")

print(f"R tasks in GT: {len(set(r_in_gt))}/{len(r_tasks)}")

# V10 generalized
gen_base = os.path.join(TRANSFER, 'generalized')
r_in_v10 = []
if os.path.isdir(gen_base):
    for d in sorted(os.listdir(gen_base)):
        dp = os.path.join(gen_base, d)
        if os.path.isdir(dp):
            tid = d.split('_')[0]
            if tid in r_tasks:
                sf = os.path.join(dp, 'logs', 'run_summary.json')
                if os.path.exists(sf):
                    with open(sf) as f:
                        sd = json.load(f)
                    r = sd.get('reward', 0)
                    r_in_v10.append((tid, r))
                    print(f"  V10 {tid}: reward={r}")

print(f"R tasks in V10: {len(set(x[0] for x in r_in_v10))}/{len(r_tasks)}")

# =============================================
# 3. Check what categories exist
# =============================================
print("\n" + "=" * 70)
print("TASK CATEGORIES (from README or skill.md)")
print("=" * 70)
for tid in sorted(r_tasks)[:5]:
    skill_file = os.path.join(BASE, tid, 'skill.md')
    if os.path.exists(skill_file):
        with open(skill_file) as f:
            c = f.read()[:500]
        # Get first line with category
        lines = c.split('\n')
        for line in lines[:10]:
            if 'category' in line.lower() or '#' in line:
                print(f"  {tid}: {line.strip()[:80]}")
                break
        else:
            print(f"  {tid}: {lines[0].strip()[:80]}")