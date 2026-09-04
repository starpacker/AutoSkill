"""Deep dive into R task format and compare with da-* format."""
import json, os

HF = "/data/yjh/BioDSBench_hf"

# ============ R TASK SAMPLE ============
r_tasks = [json.loads(l) for l in open(os.path.join(HF, "R_tasks_with_class.jsonl"))]
t = r_tasks[0]
print("=== SAMPLE R TASK ===")
print(f"study_ids: {t.get('study_ids')}")
print(f"question_ids: {t.get('question_ids')}")
print(f"analysis_types: {t.get('analysis_types')}")
print(f"study_types: {t.get('study_types')}")
print(f"\nKeys: {list(t.keys())}")
print(f"\nquery[:500]: {t.get('queries','')[:500]}")
print(f"\nreference_answer[:500]: {t.get('reference_answer','')[:500]}")
print(f"\ntest_cases[:500]: {t.get('test_cases','')[:500]}")

# ============ DA-* TASK STRUCTURE ============
print("\n\n=== DA-* TASK STRUCTURE ===")
da_dir = "/data/yjh/biomnibench-da/da-1-3"
for root, dirs, files in os.walk(da_dir):
    level = root.replace(da_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for f in files:
        if f in ['task.toml', 'instruction.md']:
            fp = os.path.join(root, f)
            with open(fp) as fh:
                c = fh.read()
            print(f"{subindent}{f} (first 300 chars): {c[:300]}")

# ============ DA-1-3-CLEAN STRUCTURE ============
print("\n\n=== DA-1-3-CLEAN STRUCTURE ===")
da_clean = "/data/yjh/biomnibench-da/da-1-3-clean"
for root, dirs, files in os.walk(da_clean):
    level = root.replace(da_clean, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for f in files:
        if f in ['task_manifest.json', 'README.md', 'USAGE.md']:
            fp = os.path.join(root, f)
            with open(fp) as fh:
                c = fh.read()
            print(f"{subindent}{f} (first 300 chars): {c[:300]}")

# ============ TASK TYPE DISTRIBUTION ============
print("\n\n=== R TASK ID DISTRIBUTION ===")
print(f"Total R tasks: {len(r_tasks)}")
unique_studies = set()
for t in r_tasks:
    unique_studies.add(t.get('study_ids', '?'))
print(f"Unique studies: {len(unique_studies)}")

# analysis_types per task
from collections import Counter
r_atypes = Counter()
for t in r_tasks:
    for at in eval(t.get('analysis_types', '[]')):
        r_atypes[at] += 1
print(f"\nAnalysis type distribution:")
for at, cnt in r_atypes.most_common():
    print(f"  {at}: {cnt}")

# ============ PYTHON TASK DISTRIBUTION ============
py_tasks = [json.loads(l) for l in open(os.path.join(HF, "python_tasks_with_class.jsonl"))]
print(f"\n\n=== PYTHON TASK ID DISTRIBUTION ===")
print(f"Total Python tasks: {len(py_tasks)}")
py_atypes = Counter()
for t in py_tasks:
    for at in eval(t.get('analysis_types', '[]')):
        py_atypes[at] += 1
print(f"Analysis type distribution:")
for at, cnt in py_atypes.most_common():
    print(f"  {at}: {cnt}")