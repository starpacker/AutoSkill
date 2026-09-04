#!/usr/bin/env python3
"""
Baseline 3: GT (Ground Truth) Code Few-Shot

Goal: Give the agent the expert-written reference_answer code from the source
task as a reference example for solving the target task.

Data flow:
  1. Read da-xx-yy task_id from V10_PAIRS
  2. Look up unique_question_ids from task.json on server
  3. Look up reference_answer from original JSONL dataset
  4. Generate system prompt with the GT code
  5. Generate runner script

Usage:
  python3 prep_gt_fewshot.py --gen-prompts     # Generate prompts + runner
  python3 prep_gt_fewshot.py --deploy          # SCP prompts to server
  python3 prep_gt_fewshot.py --summary         # Check data availability
"""

import json, os, sys, glob, stat, subprocess

# === Config ===
BASE_DIR = "/data/yjh/skill-transfer-eval"
TASKS_DIR = "/data/yjh/biomnibench-organized"
JSONL_PATH = "/data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl"
PROMPT_DIR = os.path.join(BASE_DIR, "fewshot_prompts")
OUTPUT_DIR = os.path.join(BASE_DIR, "gt_fewshot_transfer")
HARNESS_DIR = "/tmp/my_claude_biomnibench_fixed"
BUN_BIN = "/tmp/bun_extract/bun-linux-x64/bun"
MAX_ROUNDS = 5
TIMEOUT = 7200
CONCURRENCY = 3

# V10 experiment pairs (same as prep_fewshot_data.py)
V10_PAIRS = [
    # Batch 1
    ("da-26-2", "da-10-1", 1),
    ("da-20-3", "da-12-2", 1),
    ("da-13-5", "da-13-6", 1),
    ("da-14-3", "da-15-7", 1),
    ("da-5-1",  "da-15-8", 1),
    ("da-19-4", "da-19-6", 1),
    ("da-20-3", "da-20-4", 1),
    ("da-13-3", "da-24-3", 1),
    ("da-18-5", "da-25-1", 1),
    ("da-26-2", "da-26-4", 1),
    ("da-19-3", "da-8-3",  1),
    ("da-4-6",  "da-9-1",  1),
    # Batch 2
    ("da-18-1", "da-25-1", 2),
    ("da-13-1", "da-8-3",  2),
    ("da-15-1", "da-8-3",  2),
    ("da-19-3", "da-19-6", 2),
    ("da-14-3", "da-24-3", 2),
    ("da-8-1",  "da-24-3", 2),
    # Batch 3
    ("da-8-1",  "da-15-7", 3),
    ("da-8-2",  "da-15-7", 3),
    ("da-19-1", "da-8-3",  3),
    ("da-18-1", "da-4-7",  3),
    ("da-6-2",  "da-9-1",  3),
]


def load_uid_mapping() -> dict[str, str]:
    """Load da-xx-yy -> unique_question_ids mapping from task.json files."""
    mapping = {}
    for tid in set(s for s, t, b in V10_PAIRS) | set(t for s, t, b in V10_PAIRS):
        task_json_path = os.path.join(TASKS_DIR, tid, "task.json")
        if os.path.exists(task_json_path):
            with open(task_json_path) as f:
                tj = json.load(f)
            uid = tj.get("unique_question_ids", "")
            if uid:
                mapping[tid] = uid
    return mapping


def load_reference_answers() -> dict[str, str]:
    """Load all reference_answers from original JSONL, keyed by unique_question_ids."""
    refs = {}
    if not os.path.exists(JSONL_PATH):
        print(f"  WARNING: {JSONL_PATH} not found")
        return refs
    with open(JSONL_PATH) as f:
        for line in f:
            r = json.loads(line)
            uid = r["unique_question_ids"]
            ref = r.get("reference_answer", "") or ""
            if ref.strip():
                refs[uid] = ref
    return refs


def format_gt_prompt(source_task: str, target_task: str, gt_code: str) -> str:
    """Format the GT code as a system prompt."""
    lines = []
    lines.append("# Reference: Expert Solution Code\n")
    lines.append("Below is the expert-written solution code for a similar bioinformatics task. ")
    lines.append("Study this code carefully — it demonstrates the correct approach for this type of analysis. ")
    lines.append("Use it as a reference for solving your task.\n")
    lines.append(f"**Source task**: {source_task}")
    lines.append(f"**Target task**: {target_task}\n")
    lines.append("## Expert Solution Code\n")
    lines.append("```python")
    lines.append(gt_code.strip())
    lines.append("```\n")
    lines.append("## Instructions\n")
    lines.append("1. Study the expert solution code above carefully")
    lines.append("2. Understand the approach, methods, and key parameters used")
    lines.append("3. Adapt this approach to solve the target task")
    lines.append("4. Remember: the target task may have different data, columns, or requirements")
    lines.append("5. Write your solution in `outputs/answer.py`")
    return "\n".join(lines)


def gen_runner(experiments: list[tuple]) -> str:
    """Generate bash runner script."""
    lines = []
    lines.append("#!/bin/bash")
    lines.append("# GT code few-shot baseline runner for V10 experiment pairs")
    lines.append("set -euo pipefail")
    lines.append("")
    lines.append(f'HARNESS_DIR="{HARNESS_DIR}"')
    lines.append(f'TASKS_DIR="{TASKS_DIR}"')
    lines.append(f'RUNS_DIR="{OUTPUT_DIR}"')
    lines.append(f'BUN_BIN="{BUN_BIN}"')
    lines.append(f'PROMPT_DIR="{PROMPT_DIR}"')
    lines.append(f'MAX_ROUNDS={MAX_ROUNDS}')
    lines.append(f'TIMEOUT_SECONDS={TIMEOUT}')
    lines.append(f'CONCURRENCY={CONCURRENCY}')
    lines.append("")
    lines.append('# Export API config')
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
    lines.append('echo "=============================================="')
    lines.append('echo "GT Code Few-Shot Baseline Runner"')
    lines.append('echo "Total: $TOTAL | Concurrency: $CONCURRENCY"')
    lines.append('echo "Log dir: $LOG_DIR"')
    lines.append('echo "=============================================="')
    lines.append("")

    # Batch by concurrency
    batch = []
    schedule = []
    for src, tgt, prefix, prompt_path in experiments:
        batch.append((src, tgt, prefix, prompt_path))
        if len(batch) >= CONCURRENCY:
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
            log_file = f"$LOG_DIR/{prefix}.log"
            lines.append(f"# Exp: {src} -> {tgt}")
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
            lines.append(f'    > "$LOG_FILE" 2>&1')
            lines.append(f'  EXIT_CODE=$?')
            lines.append(f'  if [ $EXIT_CODE -eq 0 ]; then')
            lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: Completed {src} -> {tgt}"')
            lines.append(f'  else')
            lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: FAILED {src} -> {tgt} (exit=$EXIT_CODE)"')
            lines.append(f'  fi')
            lines.append(f'  exit $EXIT_CODE')
            lines.append(") &")
            lines.append("PIDS+=($!)")
            lines.append("")

        lines.append("  # Wait for this batch")
        lines.append('  for pid in "${PIDS[@]}"; do')
        lines.append('    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))')
        lines.append('  done')
        lines.append(f'  echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)} complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"')

    lines.append("")
    lines.append("END_TIME=$(date +%s)")
    lines.append("ELAPSED=$((END_TIME - START_TIME))")
    lines.append("ELAPSED_MIN=$((ELAPSED / 60))")
    lines.append("")
    lines.append('echo ""')
    lines.append('echo "=============================================="')
    lines.append('echo "All Done"')
    lines.append('echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED"')
    lines.append('echo "Elapsed: ${ELAPSED_MIN}m"')
    lines.append('echo "=============================================="')

    return "\n".join(lines)


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gen-prompts":
        os.makedirs(PROMPT_DIR, exist_ok=True)
        os.makedirs(OUTPUT_DIR, exist_ok=True)
        
        print("=" * 70)
        print("Baseline 3: GT Code Few-Shot - Generating Prompts")
        print("=" * 70)
        
        # Load mapping and reference answers
        uid_map = load_uid_mapping()
        refs = load_reference_answers()
        
        print(f"\nUnique task IDs mapped: {len(uid_map)}")
        print(f"Reference answers loaded: {len(refs)}")
        
        experiments = []
        missing = 0
        generated = 0
        
        for src, tgt, batch in V10_PAIRS:
            prefix = f"B{batch}_{src}_to_{tgt}"
            
            # Look up unique_question_ids for source task
            src_uid = uid_map.get(src)
            if not src_uid:
                print(f"  MISSING: {prefix} - no task.json mapping for source {src}")
                missing += 1
                continue
            
            # Look up reference_answer
            gt_code = refs.get(src_uid)
            if not gt_code:
                print(f"  MISSING: {prefix} - no reference_answer for uid={src_uid}")
                missing += 1
                continue
            
            # Generate 3A prompt
            prompt = format_gt_prompt(src, tgt, gt_code)
            prompt_path = os.path.join(PROMPT_DIR, f"{prefix}_3A_gt_code.md")
            with open(prompt_path, "w") as f:
                f.write(prompt)
            
            experiments.append((src, tgt, prefix, prompt_path))
            generated += 1
            print(f"  [{generated}] {prefix}: GT code ({len(gt_code)} chars)")
        
        print(f"\nGenerated {generated} prompts, {missing} missing")
        print(f"Total experiments: {len(experiments)}")
        
        # Generate runner script
        runner_script = gen_runner(experiments)
        runner_path = "/tmp/run_gt_fewshot.sh"
        with open(runner_path, "w") as f:
            f.write(runner_script)
        os.chmod(runner_path, stat.S_IRWXU | stat.S_IRGRP | stat.S_IROTH)
        print(f"Runner script: {runner_path}")
        print(f"  -> scp to server1: sudo scp {runner_path} server1:{runner_path}")
        print(f"  -> Then on server1: bash {runner_path}")
        print(f"  -> Or tmux: tmux new-session -s gt_fewshot 'bash {runner_path}'")
        
    elif len(sys.argv) > 1 and sys.argv[1] == "--summary":
        # Summary mode
        print("=" * 70)
        print("BASELINE 3 (GT Code Few-Shot) - DATA AVAILABILITY")
        print("=" * 70)
        
        uid_map = load_uid_mapping()
        refs = load_reference_answers()
        
        print(f"\nV10 pairs: {len(V10_PAIRS)}")
        print(f"Tasks with task.json mapping: {len(uid_map)}")
        print(f"Tasks with reference_answer: {len(refs)}")
        print("")
        
        print("Source task availability:")
        for src, tgt, batch in V10_PAIRS:
            src_uid = uid_map.get(src, "NO_MAPPING")
            has_ref = "OK" if src_uid in refs else "NO_GT"
            print(f"  B{batch} {src:>10} -> {tgt:<10} | uid={src_uid} | ref={has_ref}")
        
        print("")
        ok_count = sum(1 for s, t, b in V10_PAIRS if uid_map.get(s) in refs)
        print(f"Ready: {ok_count}/{len(V10_PAIRS)} pairs")
        print(f"Use --gen-prompts to generate prompt files and runner script")
        
    else:
        print(__doc__)


if __name__ == "__main__":
    main()