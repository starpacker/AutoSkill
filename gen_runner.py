#!/usr/bin/env python3
"""Generate experiment runner script for supplementary GT data collection."""
import json
from collections import defaultdict

# Load experiment plan
with open('gt_supplement_plan.json') as f:
    experiments = json.load(f)

HARNESS_DIR = '/tmp/my_claude_biomnibench_fixed'
TASKS_DIR = '/data/yjh/biomnibench-organized'
RUNS_DIR = '/data/yjh/skill-transfer-eval/generalized'
SKILLS_BASE = '/data/yjh/skill-transfer-eval/skills'
GENERALIZED_SKILLS = '/data/yjh/skill-transfer-eval/generalized_skills'
BUN_BIN = '/tmp/bun_extract/bun-linux-x64/bun'
MAX_ROUNDS = 5
TIMEOUT = 7200
CONCURRENCY = 3

# Build schedule: batches where no target repeats in a batch
schedule = []  # list of batches, each batch is list of (exp_num, source, target)
for i, (source, target) in enumerate(experiments):
    placed = False
    for batch in schedule:
        if len(batch) < CONCURRENCY:
            batch_targets = {e[1] for e in batch}
            if target not in batch_targets:
                batch.append((i, source, target))
                placed = True
                break
    if not placed:
        schedule.append([(i, source, target)])

# Build the script
def q(s):
    """Escape for f-string: double {{ for literal {."""
    return s.replace('{', '{{').replace('}', '}}')

lines = []
lines.append('#!/bin/bash')
lines.append('# Auto-generated GT supplement experiment runner')
lines.append(f'# Total experiments: {len(experiments)}, concurrency: {CONCURRENCY}')
lines.append('')
lines.append('# No set -e: background process failures handled by exit code checks')
lines.append('')
lines.append(f'HARNESS_DIR="{HARNESS_DIR}"')
lines.append(f'TASKS_DIR="{TASKS_DIR}"')
lines.append(f'RUNS_DIR="{RUNS_DIR}"')
lines.append(f'SKILLS_BASE="{SKILLS_BASE}"')
lines.append(f'GENERALIZED_SKILLS="{GENERALIZED_SKILLS}"')
lines.append(f'BUN_BIN="{BUN_BIN}"')
lines.append(f'MAX_ROUNDS={MAX_ROUNDS}')
lines.append(f'TIMEOUT_SECONDS={TIMEOUT}')
lines.append(f'CONCURRENCY={CONCURRENCY}')
lines.append('')
lines.append('# Export API config')
lines.append('export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
lines.append('export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"')
lines.append('export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor2/Claude-4.7-opus}"')
lines.append('export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-Vendor3/DeepSeek-V4-Flash}"')
lines.append('export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
lines.append('export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"')
lines.append('export QWEN_MODEL="${QWEN_MODEL:-Vendor3/qwen3.5-plus}"')
lines.append('')
lines.append('TOTAL=' + str(len(experiments)))
lines.append('COMPLETED=0')
lines.append('FAILED=0')
lines.append('START_TIME=$(date +%s)')
lines.append('LOG_DIR="/data/yjh/skill-transfer-eval/logs/gt_supplement_$(date +%Y%m%d_%H%M%S)"')
lines.append('mkdir -p "$LOG_DIR"')
lines.append('')
lines.append('echo "=============================================="')
lines.append('echo "GT Supplement Experiment Runner"')
lines.append('echo "Total: $TOTAL | Concurrency: $CONCURRENCY"')
lines.append('echo "Log dir: $LOG_DIR"')
lines.append('echo "=============================================="')
lines.append('')

for batch_idx, batch in enumerate(schedule):
    lines.append('')
    lines.append(f'# === Batch {batch_idx+1}/{len(schedule)} ===')
    lines.append('PIDS=()')
    lines.append('')
    for (exp_num, source, target) in batch:
        lines.append(f'# Exp {exp_num+1}: {source} -> {target}')
        lines.append('(')
        lines.append(f'  mkdir -p "$SKILLS_BASE/{target}/skills/generalized-transfer"')
        lines.append(f'  cp "$GENERALIZED_SKILLS/{source}/SKILL.md" "$SKILLS_BASE/{target}/skills/generalized-transfer/SKILL.md"')
        lines.append(f'  cat > "$SKILLS_BASE/{target}/skills/generalized-transfer/metadata.json" << METADATA')
        lines.append(f'  {{')
        lines.append(f'    "source_task": "{source}",')
        lines.append(f'    "target_task": "{target}",')
        lines.append(f'    "deployed_at": "$(date +%Y%m%d_%H%M%S)"')
        lines.append(f'  }}')
        lines.append(f'METADATA')
        ts = f'gt_supp_{exp_num+1:03d}_{source}_to_{target}'
        lines.append(f'  TS="{ts}"')
        log_file = f'$LOG_DIR/{exp_num+1:03d}_{source}_to_{target}.log'
        lines.append(f'  LOG_FILE="{log_file}"')
        lines.append(f'  cd "$HARNESS_DIR"')
        lines.append(f'  $BUN_BIN src/harness/evaluation/cli.ts \\')
        lines.append(f'    --task "{target}" \\')
        lines.append(f'    --tasks-dir "$TASKS_DIR" \\')
        lines.append(f'    --runs-dir "$RUNS_DIR" \\')
        lines.append(f'    --max-rounds "$MAX_ROUNDS" \\')
        lines.append(f'    --timeout-seconds "$TIMEOUT_SECONDS" \\')
        lines.append(f'    --temperature 1 \\')
        lines.append(f'    --thinking disabled \\')
        lines.append(f'    --timestamp "$TS" \\')
        lines.append(f'    --quiet \\')
        lines.append(f'    --enable-skills \\')
        lines.append(f'    --skills-dir "$SKILLS_BASE/{target}/skills/generalized-transfer" \\')
        lines.append(f'    --skill-name generalized-transfer \\')
        lines.append(f'    --max-active-skills 1 \\')
        lines.append(f'    > "$LOG_FILE" 2>&1')
        lines.append(f'  EXIT_CODE=$?')
        lines.append(f'  if [ $EXIT_CODE -eq 0 ]; then')
        lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: Completed {source} -> {target}"')
        lines.append(f'  else')
        lines.append(f'    echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)}: FAILED {source} -> {target} (exit=$EXIT_CODE)"')
        lines.append(f'  fi')
        lines.append(f'  exit $EXIT_CODE')
        lines.append(') &')
        lines.append('PIDS+=($!)')
        lines.append('')

    lines.append('  # Wait for this batch')
    lines.append('  for pid in "${PIDS[@]}"; do')
    lines.append('    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))')
    lines.append('  done')
    lines.append(f'  echo "[$(date +%H:%M:%S)] Batch {batch_idx+1}/{len(schedule)} complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"')

lines.append('')
lines.append('')
lines.append('END_TIME=$(date +%s)')
lines.append('ELAPSED=$((END_TIME - START_TIME))')
lines.append('ELAPSED_MIN=$((ELAPSED / 60))')
lines.append('')
lines.append('echo ""')
lines.append('echo "=============================================="')
lines.append('echo "Batch Complete"')
lines.append('echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED"')
lines.append('echo "Elapsed: ${ELAPSED_MIN}m"')
lines.append('echo "=============================================="')

script = '\n'.join(lines)

# Save
with open('run_gt_supplement.sh', 'w', newline='\n') as f:
    f.write(script)

print(f"Script written: run_gt_supplement.sh")
print(f"Experiments: {len(experiments)}, Batches: {len(schedule)}, Concurrency: {CONCURRENCY}")
print(f"Script size: {len(script)} bytes")
print(f"Est. wall time: ~{len(schedule) * 30} min = {len(schedule) * 30 / 60:.1f} hours")
print(f"Batch sizes: {[len(b) for b in schedule]}")