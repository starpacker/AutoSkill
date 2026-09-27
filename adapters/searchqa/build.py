#!/usr/bin/env python3
"""Build SearchQA tasks for the my-claude-harness evaluation framework.

SearchQA: Jeopardy-style retrieval QA. Each row has:
  * question: the clue
  * answers:  list of acceptable answers (may include parenthetical variants,
              e.g. "(Harriet Beecher) Stowe")
  * context:  retrieved documents (with [DOC]/[TLE]/[PAR] markers)
  * key:      unique id

Task: the agent answers the clue and writes results.json.

Two modes:
  * OPEN-BOOK (default): context is provided at envs/data/context.txt. The gold
    answer usually appears verbatim in the context (SearchQA is a retrieval
    dataset), so the no-skill baseline saturates near reward=1.0. Useful only
    for sanity checks.
  * CLOSED-BOOK (--no-context): NO context file is written and the README does
    NOT mention any source documents. The agent must answer the Jeopardy clue
    from its own parametric knowledge. This eliminates answer leakage and gives
    the baseline real difficulty headroom, which is required for meaningful
    skill-pruning ablations and V10 SEL training.

Lessons applied from OfficeQA cleaning:
  * README.md carries the FULL clue + explicit output contract.
  * Golden answers stay private in evaluation/data/.
  * Judge is robust: lenient normalized match that tolerates parenthetical
    variants (a known SearchQA quirk).
  * Shared venv via symlink; backup existing task dir before overwrite.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import random
import shutil
import sys

REPO = pathlib.Path(__file__).resolve().parents[2]
BENCH = REPO / "bench_data" / "searchqa"
TASKS_DIR = REPO / "tasks" / "searchqa"
TASKS_DIR.mkdir(parents=True, exist_ok=True)

VENV_TARGET = os.environ.get("SEARCHQA_VENV", str(TASKS_DIR / ".shared_venv"))

OUTPUT_SCHEMA = {
    "type": "object",
    "required": ["answer"],
    "properties": {
        "answer": {"type": "string", "description": "The answer to the clue"}
    },
}

JUDGE_CODE = r'''#!/usr/bin/env python3
"""SearchQA judge - STRICT Exact Match (paper convention).

Scoring follows the standard open-domain QA metric: after light normalization
(lowercasing, article removal, punctuation stripping, whitespace collapse) the
agent answer must EXACTLY EQUAL one of the gold answers. The only tolerance is
for SearchQA's parenthetical variants like "(Harriet Beecher) Stowe" (we accept
either the full form or the parenthetical-stripped core as the gold form).

There is NO containment / partial-credit fallback: answering "University of
Hawaii at Manoa" when the gold is "Hawaii" is a MISS (reward 0.0), exactly as
Exact Match would score it in the literature.
"""
import argparse
import json
import os
import re


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


def write_result(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w") as f:
        json.dump(obj, f)
    print(json.dumps(obj))


def normalize(text):
    text = str(text).lower().strip()
    text = re.sub(r"^(the|a|an)\s+", "", text)
    text = re.sub(r"[^a-z0-9 ]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def strip_parens(text):
    no_paren = re.sub(r"\([^)]*\)", " ", text)
    return no_paren


def variants(gold):
    vs = set()
    g = str(gold)
    vs.add(normalize(g))
    vs.add(normalize(strip_parens(g)))
    vs.add(normalize(g.replace("(", " ").replace(")", " ")))
    return {v for v in vs if v}


def main():
    args = parse_args()
    eval_data = args.eval_data
    gold_path = os.path.join(eval_data, "answers.json")
    if not os.path.exists(gold_path):
        alt = os.path.join(eval_data, "answer.txt")
        if os.path.exists(alt):
            with open(alt, encoding="utf-8") as f:
                golds = [f.read().strip()]
        else:
            write_result(args.result, {
                "status": "error", "reward": 0.0,
                "feedback": "judge misconfigured: no gold answers found",
            })
            return
    else:
        with open(gold_path, encoding="utf-8") as f:
            golds = json.load(f)
        if isinstance(golds, str):
            golds = [golds]

    rp = os.path.join(args.submission, "results.json")
    if not os.path.exists(rp):
        write_result(args.result, {
            "status": "fail", "reward": 0.0,
            "feedback": "results.json not found in outputs/. Write "
                        "{\"answer\": \"...\"} to outputs/results.json.",
        })
        return

    try:
        with open(rp, encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        write_result(args.result, {
            "status": "fail", "reward": 0.0,
            "feedback": "results.json is not valid JSON: %s" % e,
        })
        return

    sub_raw = str(data.get("answer", ""))
    sub = normalize(sub_raw)
    sub_core = normalize(strip_parens(sub_raw))

    if not sub:
        write_result(args.result, {
            "status": "fail", "reward": 0.0,
            "feedback": "Incorrect: no answer was submitted. Write your "
                        "best single answer to outputs/results.json as "
                        "{\"answer\": \"...\"}.",
        })
        return

    # STRICT Exact Match: normalized answer must EQUAL a gold form
    # (full or parenthetical-stripped). No containment / partial credit.
    for g in golds:
        gforms = variants(g)
        for gf in gforms:
            if not gf:
                continue
            if sub == gf or sub_core == gf:
                write_result(args.result, {
                    "status": "pass", "reward": 1.0,
                    "feedback": "Exact match to gold '%s'." % g,
                })
                return

    write_result(args.result, {
        "status": "fail", "reward": 0.0,
        "feedback": "Incorrect. Your answer '%s' is not accepted. Do NOT "
                    "simply rephrase; re-read the clue and the source "
                    "documents and reconsider what the single best answer "
                    "is." % sub_raw,
    })


if __name__ == "__main__":
    main()
'''


def make_tid(row, index):
    key = row.get("key")
    if key:
        short = str(key)[:12]
    else:
        short = hashlib.md5(row["question"].encode("utf-8")).hexdigest()[:12]
    return f"searchqa-{short}"


def build_one_task(row, index, no_context=False):
    tid = make_tid(row, index)
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

    # Context handling:
    #  * OPEN-BOOK: envs/data/context.txt  (agent-visible, public)
    #  * CLOSED-BOOK: evaluation/data/context.txt  (private, judge/oracle-side
    #    only; the agent never sees it, so there is NO answer leakage, but the
    #    oracle-skill generator can still use it as ground-truth reference).
    context = row.get("context", "")
    if no_context:
        with open(task_dir / "evaluation" / "data" / "context.txt", "w", encoding="utf-8") as f:
            f.write(context)
    else:
        with open(task_dir / "envs" / "data" / "context.txt", "w", encoding="utf-8") as f:
            f.write(context)

    # Golden answers -> evaluation/data/answers.json (private)
    answers = row.get("answers", [])
    if isinstance(answers, str):
        answers = [answers]
    with open(task_dir / "evaluation" / "data" / "answers.json", "w", encoding="utf-8") as f:
        json.dump(list(answers), f, ensure_ascii=False, indent=2)

    # task_manifest.json - public bundle excludes context in closed-book mode
    public_bundle = [] if no_context else ["envs/data/"]
    manifest = {
        "version": 1,
        "task_id": tid,
        "closed_book": bool(no_context),
        "public_bundle": public_bundle,
        "entrypoints": {
            "judge": "evaluation/judge.py",
            "output_schema": "evaluation/output_schema.json",
            "environment": "envs/env_manifest.json",
        },
    }
    with open(task_dir / "task_manifest.json", "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)

    # env_manifest.json
    env_m = {
        "default_env": "runtime",
        "envs": {
            "runtime": {
                "python": {
                    "posix": "envs/runtime/.venv/bin/python",
                    "windows": "envs/runtime/.venv/Scripts/python.exe",
                }
            }
        },
    }
    with open(task_dir / "envs" / "env_manifest.json", "w", encoding="utf-8") as f:
        json.dump(env_m, f, indent=2, ensure_ascii=False)

    # README.md - the ONLY task statement the agent sees.
    question = row["question"]
    if no_context:
        readme = f"""# Task: Answer the Clue

You are given a Jeopardy-style clue. Determine the single best answer using
your own knowledge. No source documents are provided.

## Clue

{question}

## Output Format

Write a file called `results.json` to `outputs/`. It must contain:

```json
{{
  "answer": "<your concise answer here>"
}}
```

Give the most specific correct answer (typically a name, place, or short phrase).
Do not include the clue or extra explanation - just the answer value.
"""
    else:
        readme = f"""# Task: Answer the Clue

You are given a Jeopardy-style clue and a set of retrieved source documents.
Read the documents, then determine the single best answer to the clue.

## Clue

{question}

## Source Documents

The retrieved documents are available at `envs/data/context.txt`. They are
delimited with `[DOC]` (document), `[TLE]` (title), and `[PAR]` (passage)
markers. The answer to the clue can be found or inferred from these documents.

## Output Format

Write a file called `results.json` to `outputs/`. It must contain:

```json
{{
  "answer": "<your concise answer here>"
}}
```

Give the most specific correct answer (typically a name, place, or short phrase).
Do not include the clue or extra explanation - just the answer value.
"""
    with open(task_dir / "README.md", "w", encoding="utf-8") as f:
        f.write(readme)

    # output_schema.json
    with open(task_dir / "evaluation" / "output_schema.json", "w", encoding="utf-8") as f:
        json.dump(OUTPUT_SCHEMA, f, indent=2, ensure_ascii=False)

    # rubric.txt
    rubric = (
        f"Task: SearchQA - {tid}\n"
        f"Mode: {'closed-book' if no_context else 'open-book'}\n"
        f"Clue: {question}\n"
        f"Acceptable answers: {list(answers)}\n"
        f"Scoring: lenient normalized match (tolerates parenthetical variants).\n"
    )
    with open(task_dir / "evaluation" / "rubric.txt", "w", encoding="utf-8") as f:
        f.write(rubric)

    # judge.py
    with open(task_dir / "evaluation" / "judge.py", "w", encoding="utf-8") as f:
        f.write(JUDGE_CODE)

    # Shared venv symlink
    venv_link = task_dir / "envs" / "runtime" / ".venv"
    if not venv_link.exists():
        try:
            os.symlink(VENV_TARGET, str(venv_link), target_is_directory=True)
        except Exception:
            pass

    return task_dir


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--split", default="validation", choices=["validation", "train"])
    p.add_argument("--src", default=None,
                   help="Explicit source jsonl path (overrides --split lookup).")
    p.add_argument("--max-tasks", type=int, default=None)
    p.add_argument("--start", type=int, default=0)
    p.add_argument("--no-context", action="store_true",
                   help="Closed-book: do not write context.txt and remove the "
                        "source-documents section from the README. Eliminates "
                        "answer leakage and gives the baseline difficulty.")
    p.add_argument("--shuffle", action="store_true",
                   help="Shuffle the pool before selecting (uses --seed).")
    p.add_argument("--seed", type=int, default=1234)
    args = p.parse_args()

    if args.src:
        src = pathlib.Path(args.src)
        if not src.is_absolute():
            src = BENCH / args.src
    else:
        full = BENCH / f"{args.split}_full.jsonl"
        src = full if full.exists() else (BENCH / f"{args.split}.jsonl")
    if not src.exists():
        print(f"X SearchQA data not found: {src}")
        sys.exit(1)

    all_rows = []
    with open(src, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            all_rows.append(json.loads(line))
    print(f"Pool size in {src.name}: {len(all_rows)}")

    # Dedup by tid (key), keep first occurrence.
    seen = set()
    unique = []
    for r in all_rows:
        tid = make_tid(r, 0)
        if tid in seen:
            continue
        seen.add(tid)
        unique.append(r)
    if len(unique) != len(all_rows):
        print(f"After dedup by key: {len(unique)}")

    if args.shuffle:
        rnd = random.Random(args.seed)
        rnd.shuffle(unique)

    rows = unique[args.start:]
    if args.max_tasks:
        rows = rows[: args.max_tasks]

    mode = "CLOSED-BOOK (no leakage)" if args.no_context else "OPEN-BOOK"
    print(f"Building {len(rows)} SearchQA tasks [{mode}]...")
    built = 0
    for i, row in enumerate(rows):
        tid = make_tid(row, i)
        print(f"  [{i+1}/{len(rows)}] {tid}")
        if build_one_task(row, i, no_context=args.no_context):
            built += 1
    print(f"\nDone. Built: {built}  (mode={'closed-book' if args.no_context else 'open-book'})")


if __name__ == "__main__":
    main()
