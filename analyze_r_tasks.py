"""Analyze BioDSBench_hf tasks - R vs Python distribution."""
import json, os, re

HF = "/data/yjh/BioDSBench_hf"

# Load Python tasks
py_tasks = [json.loads(l) for l in open(os.path.join(HF, "python_tasks_with_class.jsonl"))]
print(f"Python tasks: {len(py_tasks)}")
py_ids = set()
for t in py_tasks:
    sid = t.get("study_ids", "?")
    qid = t.get("question_ids", "?")
    py_ids.add(f"{sid}_{qid}")
print(f"Unique Python task IDs: {len(py_ids)}")

# Show analysis types distribution
from collections import Counter
py_atypes = Counter()
for t in py_tasks:
    for at in eval(t.get("analysis_types", "[]")):
        py_atypes[at] += 1
print(f"\nPython task analysis types ({len(py_atypes)}):")
for at, cnt in py_atypes.most_common():
    print(f"  {at}: {cnt}")

# Load R tasks
r_tasks = [json.loads(l) for l in open(os.path.join(HF, "R_tasks_with_class.jsonl"))]
print(f"\nR tasks: {len(r_tasks)}")
r_ids = set()
for t in r_tasks:
    sid = t.get("study_ids", "?")
    qid = t.get("question_ids", "?")
    r_ids.add(f"{sid}_{qid}")
print(f"Unique R task IDs: {len(r_ids)}")

r_atypes = Counter()
for t in r_tasks:
    for at in eval(t.get("analysis_types", "[]")):
        r_atypes[at] += 1
print(f"\nR task analysis types ({len(r_atypes)}):")
for at, cnt in r_atypes.most_common():
    print(f"  {at}: {cnt}")

# Check overlap with da-* tasks
print("\n" + "=" * 60)
print("COMPARISON WITH DA-* TASKS")
print("=" * 60)

da_tasks = set()
for tid in sorted(os.listdir("/data/yjh/biomnibench-organized")):
    if tid.startswith("da-") and os.path.isdir(os.path.join("/data/yjh/biomnibench-organized", tid)):
        da_tasks.add(tid)

print(f"da-* tasks in biomnibench-organized: {len(da_tasks)}")

# Check if da-* tasks map to python tasks
# da-* tasks use study_ids like "33176622" etc?
# Let's check by looking at skill.md files
for tid in sorted(list(da_tasks))[:3]:
    skill_file = f"/data/yjh/biomnibench-organized/{tid}/skill.md"
    if os.path.exists(skill_file):
        with open(skill_file) as f:
            c = f.read()[:300]
        print(f"\n{tid}: {c[:200]}")

# Check the R task table schemas
print(f"\n{'='*60}")
print("R TASK TABLE SCHEMAS")
print("="*60)
schemas = [json.loads(l) for l in open(os.path.join(HF, "R_task_table_schemas.jsonl"))]
print(f"Total R schemas: {len(schemas)}")
print(f"Sample: {json.dumps(schemas[0], indent=2)[:500]}")

# Check data_files
print(f"\n{'='*60}")
print("DATA FILES")
print("="*60)
data_dir = os.path.join(HF, "data_files")
for root, dirs, files in os.walk(data_dir):
    level = root.replace(data_dir, '').count(os.sep)
    indent = ' ' * 2 * level
    print(f"{indent}{os.path.basename(root)}/")
    subindent = ' ' * 2 * (level + 1)
    for f in files[:10]:
        size = os.path.getsize(os.path.join(root, f))
        print(f"{subindent}{f} ({size/1024:.0f}KB)")
    if len(files) > 10:
        print(f"{subindent}... and {len(files)-10} more files")