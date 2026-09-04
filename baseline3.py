#!/usr/bin/env python3
"""
Baseline 3: GT Code Few-Shot - Full Pipeline

1. Build mapping: da-XX-YY -> unique_question_ids (by content-matching README vs JSONL queries)
2. Generate prompts: task description + reference_answer code as few-shot
3. Generate runner script

Usage:
  python3 /tmp/baseline3.py --gen-prompts    # Generate prompts + runner
  python3 /tmp/baseline3.py --summary         # Check data availability
"""

import json, os, sys, stat, re

TASKS_DIR = "/data/yjh/biomnibench-organized"
JSONL_PATH = "/data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl"
R_JSONL_PATH = "/data/yjh/BioDSA/benchmarks/BioDSBench-R/dataset/R_tasks_with_class.jsonl"
PROMPT_DIR = "/data/yjh/skill-transfer-eval/fewshot_prompts"
OUTPUT_DIR = "/data/yjh/skill-transfer-eval/gt_fewshot_transfer"

V10_PAIRS = [
    ("da-26-2", "da-10-1", 1), ("da-20-3", "da-12-2", 1),
    ("da-13-5", "da-13-6", 1), ("da-14-3", "da-15-7", 1),
    ("da-5-1",  "da-15-8", 1), ("da-19-4", "da-19-6", 1),
    ("da-20-3", "da-20-4", 1), ("da-13-3", "da-24-3", 1),
    ("da-18-5", "da-25-1", 1), ("da-26-2", "da-26-4", 1),
    ("da-19-3", "da-8-3",  1), ("da-4-6",  "da-9-1",  1),
    ("da-18-1", "da-25-1", 2), ("da-13-1", "da-8-3",  2),
    ("da-15-1", "da-8-3",  2), ("da-19-3", "da-19-6", 2),
    ("da-14-3", "da-24-3", 2), ("da-8-1",  "da-24-3", 2),
    ("da-8-1",  "da-15-7", 3), ("da-8-2",  "da-15-7", 3),
    ("da-19-1", "da-8-3",  3), ("da-18-1", "da-4-7",  3),
    ("da-6-2",  "da-9-1",  3),
]


def load_jsonl_tasks():
    """Load all tasks from original JSONL."""
    tasks = []
    with open(JSONL_PATH) as f:
        for line in f:
            r = json.loads(line)
            tasks.append(r)
    return tasks


def get_readme_text(task_id):
    """Get the README content for a task."""
    readme_path = os.path.join(TASKS_DIR, task_id, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path) as f:
            return f.read()
    return ""


def build_mapping_by_content():
    """
    Build da-XX-YY -> unique_question_ids mapping using naming convention.
    da-XX-YY = da-{study_index}-{question_index} where study_index is 1-based
    in the COMBINED Python+R sorted study_ids, question_index is 1-based
    in the question number sorted uids.
    """
    all_tids = sorted(set(s for s, t, b in V10_PAIRS) | set(t for s, t, b in V10_PAIRS))
    jsonl_tasks = load_jsonl_tasks()
    
    # Load R entries too
    R_JSONL_PATH = "/data/yjh/BioDSA/benchmarks/BioDSBench-R/dataset/R_tasks_with_class.jsonl"
    r_tasks = []
    if os.path.exists(R_JSONL_PATH):
        with open(R_JSONL_PATH) as f:
            for line in f:
                r_tasks.append(json.loads(line))
    
    all_entries = jsonl_tasks + r_tasks
    
    # Group by study_id
    from collections import defaultdict
    by_study = defaultdict(list)
    for e in all_entries:
        by_study[str(e["study_ids"])].append(e["unique_question_ids"])
    
    # Sort studies by study_id as integer
    sorted_studies = sorted(by_study.items(), key=lambda x: int(x[0]) if x[0].lstrip('-').isdigit() else x[0])
    
    def da_to_uid(da_id):
        m = re.match(r'da-(\d+)-(\d+)', da_id)
        if not m: return None
        paper_idx, q_idx = int(m.group(1)), int(m.group(2))
        if paper_idx < 1 or paper_idx > len(sorted_studies): return None
        _, study_uids = sorted_studies[paper_idx - 1]
        # Numeric sort by question number
        def qnum(uid):
            parts = uid.split('_')
            return int(parts[-1]) if len(parts) > 1 and parts[-1].isdigit() else 0
        sorted_by_qnum = sorted(study_uids, key=lambda u: qnum(u))
        if q_idx < 1 or q_idx > len(sorted_by_qnum): return None
        return sorted_by_qnum[q_idx - 1]
    
    mapping = {}
    for tid in all_tids:
        uid = da_to_uid(tid)
        if uid:
            mapping[tid] = uid
            print(f"  {tid} -> {uid}")
        else:
            print(f"  {tid} -> NO MATCH")
    
    return mapping


def load_reference_answers():
    """Load all reference_answers keyed by unique_question_ids from both Python and R JSONL.
    Returns dict: uid -> {"code": str, "language": str}"""
    refs = {}
    for jpath in [JSONL_PATH, R_JSONL_PATH]:
        if os.path.exists(jpath):
            with open(jpath) as f:
                for line in f:
                    r = json.loads(line)
                    uid = r["unique_question_ids"]
                    ref = r.get("reference_answer", "") or ""
                    lang = r.get("language", "python").lower()
                    if ref.strip():
                        refs[uid] = {"code": ref, "language": lang}
    return refs


def format_gt_prompt(source_task, target_task, gt_code, task_desc, language="python"):
    """Format the prompt: task description + GT code as few-shot reference."""
    lines = []
    lines.append("# Reference: Expert Solution for a Similar Task\n")
    lines.append("Below is a similar bioinformatics task and its expert-written solution. ")
    lines.append("Study this carefully — it demonstrates the correct analytical approach. ")
    lines.append("Use it as a reference for solving your task.\n")
    lines.append(f"**Source task**: {source_task}")
    lines.append(f"**Target task**: {target_task}\n")
    lines.append("## Source Task Description\n")
    lines.append(task_desc.strip())
    lines.append(f"\n## Expert Solution Code ({language.upper()})\n")
    lines.append(f"```{language}")
    lines.append(gt_code.strip())
    lines.append("```\n")
    lines.append("## Instructions\n")
    lines.append("1. Understand the task above and the expert's approach")
    lines.append("2. Adapt this approach to solve YOUR target task")
    lines.append("3. The target task may have different data, columns, or requirements")
    lines.append("4. Write your solution in `outputs/answer.py`")
    return "\n".join(lines)


def get_task_description(task_id):
    """Get task description from README."""
    readme = get_readme_text(task_id)
    if not readme:
        return ""
    
    # Remove HTML comments
    readme = re.sub(r'<!--.*?-->', '', readme, flags=re.DOTALL)
    
    # Extract the question/problem section
    q_match = re.search(r'## Question\s*\n(.*?)(?=\n##|\Z)', readme, re.DOTALL)
    if q_match:
        desc = q_match.group(1).strip()
    else:
        q_match = re.search(r'## Problem Description\s*\n(.*?)(?=\n##|\Z)', readme, re.DOTALL)
        if q_match:
            desc = q_match.group(1).strip()
        else:
            # Just use the whole README (first 1000 chars)
            desc = readme[:1000].strip()
    
    # Also include data description if available
    dd_match = re.search(r'## Data Description\s*\n(.*?)(?=\n##|\Z)', readme, re.DOTALL)
    if dd_match:
        desc += "\n\n### Data\n" + dd_match.group(1).strip()
    
    return desc


def gen_runner(experiments):
    """Generate bash runner script."""
    lines = []
    lines.append("#!/bin/bash")
    lines.append("# Baseline 3: GT code few-shot runner")
    lines.append("set -eo pipefail")
    lines.append("")
    lines.append('HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"')
    lines.append('TASKS_DIR="/data/yjh/biomnibench-organized"')
    lines.append('RUNS_DIR="/data/yjh/skill-transfer-eval/gt_fewshot_transfer"')
    lines.append('BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"')
    lines.append('PROMPT_DIR="/data/yjh/skill-transfer-eval/fewshot_prompts"')
    lines.append('MAX_ROUNDS=5')
    lines.append('TIMEOUT_SECONDS=7200')
    lines.append('CONCURRENCY=3')
    lines.append("")
    lines.append('export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
    lines.append('export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"')
    lines.append('export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor3/DeepSeek-V4-Flash}"')
    lines.append('export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-Vendor3/DeepSeek-V4-Flash}"')
    lines.append('export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
    lines.append('export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"')
    lines.append('export QWEN_MODEL="${QWEN_MODEL:-Vendor3/qwen3.5-plus}"')
    lines.append("")
    lines.append(f"TOTAL={len(experiments)}")
    lines.append("COMPLETED=0")
    lines.append("FAILED=0")
    lines.append("START_TIME=$(date +%s)")
    lines.append('LOG_DIR="/data/yjh/skill-transfer-eval/logs/gt_fewshot_$(date +%Y%m%d_%H%M%S)"')
    lines.append('mkdir -p "$LOG_DIR"')
    lines.append("")
    lines.append('echo "Baseline 3: GT Code Few-Shot Runner"')
    lines.append('echo "Total: $TOTAL | Concurrency: $CONCURRENCY"')
    lines.append("")
    # Batch by concurrency
    batch = []
    schedule = []
    for src, tgt, prefix, prompt_path in experiments:
        batch.append((src, tgt, prefix, prompt_path))
        if len(batch) >= 3:
            schedule.append(batch)
            batch = []
    if batch:
        schedule.append(batch)
    for batch_idx, batch in enumerate(schedule):
        lines.append("")
        lines.append(f"# === Batch {batch_idx+1}/{len(schedule)} ===")
        lines.append("PIDS=()")
        lines.append("")
        for (src, tgt, prefix, prompt_path) in batch:
            ts = f"gt3_{prefix}"
            lines.append(f"# {src} -> {tgt}")
            lines.append("(")
            lines.append(f'  mkdir -p "$RUNS_DIR"')
            lines.append(f'  cd "$HARNESS_DIR"')
            lines.append(f'  $BUN_BIN src/harness/evaluation/cli.ts \\')
            lines.append(f'    --task "{tgt}" \\')
            lines.append(f'    --tasks-dir "$TASKS_DIR" \\')
            lines.append(f'    --runs-dir "$RUNS_DIR" \\')
            lines.append(f'    --max-rounds "$MAX_ROUNDS" \\')
            lines.append(f'    --timeout-seconds "$TIMEOUT_SECONDS" \\')
            lines.append(f'    --temperature 1 \\')
            lines.append(f'    --thinking disabled \\')
            lines.append(f'    --timestamp "{ts}" \\')
            lines.append(f'    --quiet \\')
            lines.append(f'    --system-prompt "$PROMPT_DIR/{prefix}_3A_gt_code.md" \\')
            lines.append(f'    > "$LOG_DIR/{prefix}.log" 2>&1')
            lines.append(f'  EXIT_CODE=$?')
            lines.append(f'  if [ $EXIT_CODE -eq 0 ]; then')
            lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: OK {src} -> {tgt}"')
            lines.append(f'  else')
            lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: FAIL {src} -> {tgt} (exit=$EXIT_CODE)"')
            lines.append(f'  fi')
            lines.append(f'  exit $EXIT_CODE')
            lines.append(") &")
            lines.append("PIDS+=($!)")
            lines.append("")
        lines.append('  for pid in "${PIDS[@]}"; do')
        lines.append('    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))')
        lines.append('  done')
        lines.append(f'  echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)} done. So far: $COMPLETED/$TOTAL, Failed: $FAILED"')
    lines.append("")
    lines.append("END_TIME=$(date +%s)")
    lines.append("ELAPSED=$((END_TIME - START_TIME))")
    lines.append("ELAPSED_MIN=$((ELAPSED / 60))")
    lines.append('echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED | Elapsed: ${ELAPSED_MIN}m"')
    return "\n".join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gen-prompts":
        os.makedirs(PROMPT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("=" * 70)
        print("Baseline 3: GT Code Few-Shot - Generating Prompts")
        print("=" * 70)
        
        # Step 1: Build mapping
        print("\n[Step 1] Building task ID mapping...")
        mapping = build_mapping_by_content()
        print(f"\n  Mapped {len(mapping)} tasks")
        
        # Step 2: Load reference answers
        print("\n[Step 2] Loading reference answers...")
        refs = load_reference_answers()
        print(f"  Loaded {len(refs)} reference answers")
        
        # Step 3: Generate prompts
        print("\n[Step 3] Generating prompts...")
        experiments = []
        missing = 0
        generated = 0
        
        for src, tgt, batch in V10_PAIRS:
            prefix = f"B{batch}_{src}_to_{tgt}"
            
            src_uid = mapping.get(src)
            if not src_uid:
                print(f"  MISSING: {prefix} - no mapping for {src}")
                missing += 1
                continue
            
            gt_data = refs.get(src_uid)
            if not gt_data:
                print(f"  MISSING: {prefix} - no ref_answer for uid={src_uid}")
                missing += 1
                continue
            
            gt_code = gt_data["code"]
            gt_lang = gt_data["language"]
            
            task_desc = get_task_description(src)
            if not task_desc:
                print(f"  WARNING: {prefix} - no task description for {src}, using empty")
                task_desc = "(Source task description not available)"
            
            prompt = format_gt_prompt(src, tgt, gt_code, task_desc, language=gt_lang)
            prompt_path = os.path.join(PROMPT_DIR, f"{prefix}_3A_gt_code.md")
            with open(prompt_path, "w") as f:
                f.write(prompt)
            
            experiments.append((src, tgt, prefix, prompt_path))
            generated += 1
            print(f"  [{generated}] {prefix}: {len(gt_code)} chars code + {len(task_desc)} chars desc")
        
        print(f"\nGenerated {generated}, {missing} missing")
        print(f"Total experiments: {len(experiments)}")
        
        # Step 4: Generate runner
        print("\n[Step 4] Generating runner script...")
        runner = gen_runner(experiments)
        runner_path = "/tmp/run_gt_fewshot.sh"
        with open(runner_path, "w") as f:
            f.write(runner)
        os.chmod(runner_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        print(f"  Runner: {runner_path}")
        print(f"  To run: bash {runner_path}")
        print(f"  Or tmux: tmux new-session -s gt_fewshot 'bash {runner_path}'")
        
        print("\nDone!")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "--summary":
        print("=" * 70)
        print("Baseline 3: GT Code Few-Shot - Data Availability")
        print("=" * 70)
        
        mapping = build_mapping_by_content()
        refs = load_reference_answers()
        
        print(f"\nV10 pairs: {len(V10_PAIRS)}")
        print(f"Tasks mapped: {len(mapping)}")
        print(f"Reference answers loaded: {len(refs)}")
        print("")
        
        ok_count = 0
        for src, tgt, batch in V10_PAIRS:
            src_uid = mapping.get(src, "NO_MAP")
            has_ref = "OK" if src_uid in refs else "NO_GT"
            desc_len = len(get_task_description(src))
            if src_uid in refs:
                ok_count += 1
            gt_lang = refs.get(src_uid, {}).get("language", "?") if src_uid in refs else "?"
            print(f"  B{batch} {src:>10} -> {tgt:<10} | uid={src_uid} | ref={has_ref}({gt_lang}) | desc={desc_len}chars")
        
        print(f"\nReady: {ok_count}/{len(V10_PAIRS)} pairs")
        print("Use --gen-prompts to generate prompt files and runner")
        
    else:
        print("Usage:")
        print("  python3 baseline3.py --summary       # Check data availability")
        print("  python3 baseline3.py --gen-prompts   # Generate prompts + runner")


if __name__ == "__main__":
    main()