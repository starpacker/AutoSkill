#!/usr/bin/env python3
"""Build OfficeQA tasks for the evaluation framework."""
import argparse, datetime, json, os, pathlib, shutil, sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BENCH = REPO / "bench_data" / "officeqa"
RAW_SRC = BENCH / "raw" / "treasury_bulletins_parsed" / "transformed"
TRAIN_JSONL = BENCH / "train.jsonl"
TASKS_DIR = REPO / "tasks" / "officeqa"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

VENV_TARGET = os.environ.get("OFFICEQA_VENV", str(REPO / "tasks" / "officeqa" / ".shared_venv"))

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "properties": {
        "answer": {"type": "string", "description": "The answer to the question"}
    }
}

def build_one_task(row, index):
    uid = row["uid"]
    tid = f"officeqa-{uid.lower()}"
    task_dir = TASKS_DIR / tid

    if task_dir.exists():
        ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup = TASKS_DIR / f"{tid}.bak_{ts}"
        shutil.copytree(str(task_dir), str(backup))
        print(f"    Backup -> {backup.name}")
        shutil.rmtree(str(task_dir))

    (task_dir / "envs" / "data").mkdir(parents=True, exist_ok=True)
    (task_dir / "evaluation" / "data").mkdir(parents=True, exist_ok=True)
    (task_dir / "envs" / "runtime").mkdir(parents=True, exist_ok=True)

    source_files = [s.strip() for s in row["source_files"].split("\r\n") if s.strip()]
    for sf in source_files:
        src = RAW_SRC / sf
        if src.exists():
            shutil.copy2(str(src), str(task_dir / "envs" / "data" / sf))
        else:
            print(f"    Warning: Source file not found: {sf}")

    manifest = {
        "version": 1,
        "task_id": tid,
        "public_bundle": ["envs/data/"],
        "entrypoints": {
            "judge": "evaluation/judge.py",
            "output_schema": "evaluation/output_schema.json",
            "environment": "envs/env_manifest.json"
        }
    }
    with open(task_dir / "task_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    env_m = {"default_env": "runtime", "envs": {"runtime": {"python": {"posix": "envs/runtime/.venv/bin/python", "windows": "envs/runtime/.venv/Scripts/python.exe"}}}}
    with open(task_dir / "envs" / "env_manifest.json", "w", encoding="utf-8") as f:
        json.dump(env_m, f, indent=2, ensure_ascii=False)

    sf_list = "\n".join(f"  - `envs/data/{sf}`" for sf in source_files)
    readme = f"""# Task: Office Question Answering

Answer the following question based on the provided source document(s).

## Question

{row['question']}

## Source Documents

The following source files are available under `envs/data/`:
{sf_list}

## Output Format

Write a file called `results.json` to `outputs/`.
It must contain the following JSON structure:

```json
{{
  "answer": "<your concise answer here>"
}}
```

The answer should be a direct extract or calculation from the source document.
Be precise - include units only if the question asks for them.
"""
    with open(task_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    with open(task_dir / "evaluation" / "output_schema.json", "w", encoding="utf-8") as f:
        json.dump(OUTPUT_SCHEMA, f, indent=2, ensure_ascii=False)

    with open(task_dir / "evaluation" / "data" / "answer.txt", "w", encoding="utf-8") as f:
        f.write(row["answer"])

    rubric = f"Task: OfficeQA - {uid}\nDifficulty: {row['difficulty']}\nAnswer: {row['answer']}\nScoring: Exact string match after normalization\n"
    with open(task_dir / "evaluation" / "rubric.txt", "w", encoding="utf-8") as f:
        f.write(rubric)

    judge_code = '''#!/usr/bin/env python3
import argparse, json, os, re, html

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--submission", required=True)
    p.add_argument("--cases")
    p.add_argument("--schema")
    p.add_argument("--metrics")
    p.add_argument("--eval-data")
    p.add_argument("--result", required=True)
    p.add_argument("--feedback-level", default="metric_status")
    return p.parse_args()

def normalize(text):
    text = html.unescape(text)
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9%.,\\\\-]", "", text)
    return re.sub(r"\\\\s+", " ", text).strip()

def main():
    args = parse_args()
    rp = os.path.join(args.submission, "results.json")
    gp = os.path.join(args.eval_data, "answer.txt")
    err = {"status": "error", "reward": 0.0, "feedback": "results.json not found"}
    if not os.path.exists(rp):
        os.makedirs(os.path.dirname(args.result) or ".", exist_ok=True)
        with open(args.result, "w") as f: json.dump(err, f)
        print(json.dumps(err)); return
    with open(rp) as f: data = json.load(f)
    with open(gp) as f: gt = f.read().strip()
    sub = normalize(str(data.get("answer", "")))
    exp = normalize(gt)
    if sub == exp:
        r = {"status": "pass", "reward": 1.0, "feedback": f"Exact match" + ": " + gt}
    elif sub in exp or exp in sub:
        r = {"status": "pass", "reward": 0.8, "feedback": f"Partial match. Got: " + str(data.get("answer","")) + " vs " + gt}
    else:
        r = {"status": "fail", "reward": 0.0, "feedback": f"No match. Got: " + str(data.get("answer","")) + " vs " + gt}
    os.makedirs(os.path.dirname(args.result) or ".", exist_ok=True)
    with open(args.result, "w") as f: json.dump(r, f)
    print(json.dumps(r))

if __name__ == "__main__":
    main()
'''
    with open(task_dir / "evaluation" / "judge.py", "w", encoding="utf-8") as f:
        f.write(judge_code)

    venv_link = task_dir / "envs" / "runtime" / ".venv"
    if not venv_link.exists():
        try: os.symlink(VENV_TARGET, str(venv_link), target_is_directory=True)
        except: pass

    return task_dir

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--start", type=int, default=0)
    args = p.parse_args()

    if not TRAIN_JSONL.exists():
        print(f"X Train data not found: {TRAIN_JSONL}"); sys.exit(1)

    rows = [json.loads(l) for l in open(TRAIN_JSONL, encoding="utf-8")]
    if args.max_tasks:
        rows = rows[args.start:args.start + args.max_tasks]

    print(f"Building {len(rows)} OfficeQA tasks...")
    built = 0
    for i, row in enumerate(rows):
        uid = row["uid"]
        tid = f"officeqa-{uid.lower()}"
        td = TASKS_DIR / tid
        if td.exists() and next(td.iterdir(), None):
            print(f"  [{i+1}/{len(rows)}] {tid} - SKIP")
            continue
        print(f"  [{i+1}/{len(rows)}] {tid}")
        build_one_task(row, i)
        built += 1

    print(f"\nDone. Built: {built}")

if __name__ == "__main__":
    main()