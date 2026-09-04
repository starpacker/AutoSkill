import json
from collections import Counter

with open('/data/yjh/BioDSBench_hf/R_tasks_with_class.jsonl') as f:
    tasks = [json.loads(line) for line in f]
print('Total R tasks:', len(tasks))
print()

# Analysis type distribution
atype_counts = Counter()
for t in tasks:
    for a in t.get('analysis_types', []):
        atype_counts[a] += 1
print('Analysis type distribution:')
for k, v in sorted(atype_counts.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
print()

# Unique question IDs
qids = Counter()
for t in tasks:
    for q in t.get('unique_question_ids', []):
        qids[q] += 1
print('Unique question IDs:')
for k, v in sorted(qids.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
print()

# Study distribution
sids = Counter()
for t in tasks:
    for s in t.get('study_ids', []):
        sids[s] += 1
print('Study distribution (study_id -> num_tasks):')
for k, v in sorted(sids.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')
print()

# Sample test_cases
print('=== Sample task test_cases ===')
sample = tasks[0]
test_cases = sample.get('test_cases', [])
print(f'Number of test_cases: {len(test_cases)}')
for i, tc in enumerate(test_cases[:5]):
    if isinstance(tc, str):
        print(f'  TC {i}: {tc[:200]}')
    else:
        print(f'  TC {i}: {str(tc)[:200]}')
print()

# Check reference_answer length
print(f'Reference answer length: {len(sample.get("reference_answer", ""))}')
print(f'Code history entries: {len(sample.get("code_histories", []))}')
print()

# Check if tasks have tables info
has_tables = sum(1 for t in tasks if t.get('tables'))
print(f'Tasks with tables: {has_tables}/{len(tasks)}')
has_data_configs = sum(1 for t in tasks if t.get('study_data_configs'))
print(f'Tasks with data configs: {has_data_configs}/{len(tasks)}')
has_cot = sum(1 for t in tasks if t.get('cot_instructions'))
print(f'Tasks with COT instructions: {has_cot}/{len(tasks)}')
print()

# Sample a few task titles
print('=== Sample task titles ===')
for t in tasks[:5]:
    print(f'  study_id={t["study_ids"][0]}, qid={t["question_ids"][0]}, types={t["analysis_types"][:2]}')
    print(f'  title: {t.get("study_title", "N/A")[:100]}')
    print(f'  query[:200]: {t["queries"][0][:200]}')
    print()

# Check Python tasks for comparison
print('=== PYTHON tasks overview ===')
with open('/data/yjh/BioDSBench_hf/python_tasks_with_class.jsonl') as f:
    py_tasks = [json.loads(line) for line in f]
print(f'Total Python tasks: {len(py_tasks)}')
py_atype = Counter()
for t in py_tasks:
    for a in t.get('analysis_types', []):
        py_atype[a] += 1
print('Python analysis type distribution:')
for k, v in sorted(py_atype.items(), key=lambda x: -x[1]):
    print(f'  {k}: {v}')