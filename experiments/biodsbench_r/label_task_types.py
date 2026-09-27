#!/usr/bin/env python3
"""
Reusable LLM-based task-type labeler for BioDSBench-style tasks.

Given a directory of task definitions (each containing README.md / public/README.md
and optionally std_code/solution.R), infer a `task_type` (and `category`) for every
task using an LLM, choosing from a fixed controlled vocabulary that matches the
V10 skill-selector COMPATIBILITY_GROUPS.

Reusable: point --tasks-dir at any future task set that lacks task_type metadata.

Output: JSON mapping {task_id: {"task_type": ..., "category": ..., "rationale": ...}}

Usage:
  python3 label_task_types.py \
      --tasks-dir /data/yjh/my_claude_biomnibench/tasks/biodsbench_r \
      --out /data/yjh/my_claude_harness_biodsbench/skill_transfer/r_task_types.json \
      --concurrency 8 \
      [--only-tasks task1,task2] [--limit N] [--overwrite]
"""
import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

# ── Controlled vocabulary (must match V10 compatibility.py groups) ──────────
TASK_TYPES = [
    "differential-expression",
    "chromatin-profiling",
    "pathway-enrichment",
    "association-testing",
    "gwas-eqtl",
    "cell-composition",
    "cell-cell-communication",
    "clustering",
    "predictive-modeling",
    "survival-analysis",
    "longitudinal-analysis",
    "co-expression-networks",
    "multi-omic-integration",
    "cross-cohort-comparison",
    "mutation-analysis",
    "tcr-repertoire",
    # data-wrangling / generic fallbacks for R tasks that are not clearly a
    # canonical bio-analysis type:
    "data-wrangling",
    "statistical-testing",
    "visualization",
    "dimensionality-reduction",
]

CATEGORIES = [
    "oncology", "immunology", "metabolic", "cardiovascular",
    "neuroscience", "general-biology", "genetics", "microbiology",
]

# ── API config (centralized) ────────────────────────────────────────────────
def _load_api():
    """Load API config from api_config.py if present, else env vars."""
    key = os.environ.get("API_KEY") or os.environ.get("ANTHROPIC_API_KEY", "")
    base = os.environ.get("API_BASE_URL", "https://api.gpugeek.com/v1")
    model = os.environ.get("API_MODEL", "Vendor3/DeepSeek-V4-Flash")
    # Try to import central config
    here = os.path.dirname(os.path.abspath(__file__))
    for cand in [here, os.path.join(here, ".."), "/data/yjh/skill-transfer-eval"]:
        cfg_path = os.path.join(cand, "api_config.py")
        if os.path.isfile(cfg_path):
            sys.path.insert(0, cand)
            try:
                import api_config  # type: ignore
                key = api_config.get_api_key() or key
                base = api_config.get_base_url() or base
                model = api_config.get_model_name() or model
            except Exception:
                pass
            break
    return key, base, model


API_KEY, BASE_URL, MODEL = _load_api()


def read_task_text(task_dir):
    """Gather README + solution.R text for a task (bounded length)."""
    parts = []
    for rel in ["public/README.md", "README.md"]:
        p = os.path.join(task_dir, rel)
        if os.path.isfile(p):
            try:
                parts.append("### " + rel + "\n" + open(p, encoding="utf-8", errors="replace").read()[:2500])
            except Exception:
                pass
    sol = os.path.join(task_dir, "std_code", "solution.R")
    if os.path.isfile(sol):
        try:
            parts.append("### solution.R\n" + open(sol, encoding="utf-8", errors="replace").read()[:2500])
        except Exception:
            pass
    return "\n\n".join(parts)


def build_prompt(task_id, text):
    return f"""You are a bioinformatics data-science task classifier. Classify the task below.

Choose exactly ONE task_type from this controlled vocabulary:
{", ".join(TASK_TYPES)}

Choose exactly ONE category (biomedical domain) from:
{", ".join(CATEGORIES)}

Task ID: {task_id}

--- TASK MATERIAL ---
{text}
--- END ---

Rules:
- task_type must be the single best analytical method/pattern the task performs.
- If the task is mostly data loading/reshaping/merging with no downstream stats, use "data-wrangling".
- If it is a plain statistical hypothesis test, use "statistical-testing".
- category is the biomedical domain of the data (guess from disease/tissue names; use "general-biology" if unclear).

Respond with ONLY a compact JSON object, no markdown, no explanation outside JSON:
{{"task_type": "<one-of-vocabulary>", "category": "<one-of-categories>", "rationale": "<=20 words"}}"""


def call_llm(prompt, retries=4):
    url = BASE_URL.rstrip("/") + "/chat/completions"
    body = {
        "model": MODEL,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 300,
    }
    data = json.dumps(body).encode()
    last_err = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(
                url, data=data,
                headers={
                    "Authorization": f"Bearer {API_KEY}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=90) as resp:
                obj = json.loads(resp.read().decode())
                return obj["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            last_err = f"HTTP {e.code}: {e.read().decode()[:200]}"
        except Exception as e:
            last_err = str(e)
        time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"LLM call failed after {retries} retries: {last_err}")


def parse_response(raw):
    """Extract JSON dict from LLM response."""
    s = raw.strip()
    # strip code fences
    if s.startswith("```"):
        s = s.split("```", 2)[1] if "```" in s[3:] else s
        s = s.replace("json", "", 1).strip("`").strip()
    # find first { .. last }
    a, b = s.find("{"), s.rfind("}")
    if a >= 0 and b > a:
        s = s[a:b + 1]
    d = json.loads(s)
    tt = d.get("task_type", "").strip()
    cat = d.get("category", "").strip()
    if tt not in TASK_TYPES:
        # fuzzy: pick closest by substring
        tt_low = tt.lower().replace(" ", "-")
        tt = next((t for t in TASK_TYPES if t == tt_low), "data-wrangling")
    if cat not in CATEGORIES:
        cat = "general-biology"
    return {"task_type": tt, "category": cat, "rationale": d.get("rationale", "")[:120]}


def label_one(task_id, task_dir):
    text = read_task_text(task_dir)
    if not text.strip():
        return task_id, {"task_type": "data-wrangling", "category": "general-biology",
                         "rationale": "no material found", "error": "empty"}
    prompt = build_prompt(task_id, text)
    raw = call_llm(prompt)
    result = parse_response(raw)
    return task_id, result


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tasks-dir", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--concurrency", type=int, default=8)
    ap.add_argument("--only-tasks", default="")
    ap.add_argument("--only-tasks-file", default="",
                    help="Path to a JSON file containing a list of task_ids to label.")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--overwrite", action="store_true")
    args = ap.parse_args()

    if not API_KEY:
        print("ERROR: no API key found (API_KEY / api_config.py)", file=sys.stderr)
        sys.exit(1)

    print(f"[labeler] model={MODEL} base={BASE_URL}", flush=True)

    tasks_dir = args.tasks_dir
    all_tasks = sorted(d for d in os.listdir(tasks_dir)
                       if os.path.isdir(os.path.join(tasks_dir, d)))
    if args.only_tasks_file:
        want = set(json.load(open(args.only_tasks_file)))
        all_tasks = [t for t in all_tasks if t in want]
    if args.only_tasks:
        want = set(t.strip() for t in args.only_tasks.split(",") if t.strip())
        all_tasks = [t for t in all_tasks if t in want]
    if args.limit:
        all_tasks = all_tasks[:args.limit]
    # resume support
    existing = {}
    if os.path.isfile(args.out) and not args.overwrite:
        try:
            existing = json.load(open(args.out))
            print(f"[labeler] resuming: {len(existing)} already labeled", flush=True)
        except Exception:
            existing = {}

    todo = [t for t in all_tasks if t not in existing]
    print(f"[labeler] {len(all_tasks)} total, {len(todo)} to label, concurrency={args.concurrency}", flush=True)

    results = dict(existing)
    done = 0
    with ThreadPoolExecutor(max_workers=args.concurrency) as ex:
        futs = {ex.submit(label_one, t, os.path.join(tasks_dir, t)): t for t in todo}
        for fut in as_completed(futs):
            t = futs[fut]
            try:
                tid, res = fut.result()
                results[tid] = res
                done += 1
                print(f"[{done}/{len(todo)}] {tid} -> {res['task_type']} / {res['category']}", flush=True)
            except Exception as e:
                results[t] = {"task_type": "data-wrangling", "category": "general-biology",
                              "rationale": "", "error": str(e)[:200]}
                done += 1
                print(f"[{done}/{len(todo)}] {t} -> ERROR {e}", flush=True)
            # incremental save
            if done % 5 == 0:
                json.dump(results, open(args.out, "w"), indent=2)

    json.dump(results, open(args.out, "w"), indent=2)
    print(f"[labeler] DONE. Wrote {len(results)} labels to {args.out}", flush=True)

    # summary
    from collections import Counter
    tc = Counter(v["task_type"] for v in results.values())
    cc = Counter(v["category"] for v in results.values())
    print("\n=== task_type distribution ===")
    for k, n in tc.most_common():
        print(f"  {k}: {n}")
    print("\n=== category distribution ===")
    for k, n in cc.most_common():
        print(f"  {k}: {n}")


if __name__ == "__main__":
    main()
