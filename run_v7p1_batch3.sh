#!/bin/bash
set -uo pipefail

HARNESS_DIR=/tmp/my_claude_biomnibench_fixed
TASKS_DIR=/data/yjh/biomnibench-organized
BUN_BIN=/tmp/bun_extract/bun-linux-x64/bun
TRANSFER_DIR=/data/yjh/skill-transfer-eval/transfer
SKILLS_BASE=/data/yjh/skill-transfer-eval/skills
LOG_DIR=/data/yjh/skill-transfer-eval/logs/v7p1_batch3

export ANTHROPIC_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export ANTHROPIC_BASE_URL=https://api.gpugeek.com
export ANTHROPIC_MODEL=Vendor3/DeepSeek-V4-Flash
export QWEN_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export QWEN_BASE_URL=https://api.gpugeek.com/v1
export QWEN_MODEL=Vendor2/Gemini-3-flash

echo "=============================================="
echo "V7.1 BATCH 3 STARTED at $(date)"
echo "10 targets, serial execution (concurrency=1)"
echo "=============================================="

run_target() {
    local t=$1
    echo ""
    echo "=============================================="
    echo "TARGET: $t at $(date)"
    echo "=============================================="
    local ts=$(date +%Y%m%d_%H%M%S)_v7p1_${t}
    local log_file=${LOG_DIR}/${t}.log
    echo "Timestamp: $ts"
    echo "Log: $log_file"

    local SKILL_DIR=${SKILLS_BASE}/${t}/skills

    $BUN_BIN $HARNESS_DIR/src/harness/evaluation/cli.ts \
      --task $t \
      --tasks-dir $TASKS_DIR \
      --runs-dir $TRANSFER_DIR \
      --max-rounds 5 \
      --timeout-seconds 7200 \
      --concurrency 1 \
      --temperature 1 \
      --thinking disabled \
      --timestamp $ts \
      --quiet \
      --enable-skills \
      --skills-dir $SKILL_DIR \
      --skill-name generalized-transfer \
      --max-active-skills 1 \
      > $log_file 2>&1

    local exit_code=$?
    echo "Target $t completed with exit code $exit_code at $(date)" >> $LOG_DIR/summary.log
    echo "---" >> $LOG_DIR/summary.log
    sleep 5
}

# Target 1: da-12-2 (bl=52, low)
run_target "da-12-2"

# Target 2: da-19-4 (bl=62, mid-low)
run_target "da-19-4"

# Target 3: da-8-2 (bl=64, mid-low)
run_target "da-8-2"

# Target 4: da-24-3 (bl=65, mid)
run_target "da-24-3"

# Target 5: da-26-4 (bl=68, mid)
run_target "da-26-4"

# Target 6: da-15-7 (bl=77, mid-high)
run_target "da-15-7"

# Target 7: da-10-1 (bl=80, high)
run_target "da-10-1"

# Target 8: da-18-1 (bl=80, high)
run_target "da-18-1"

# Target 9: da-17-3 (bl=83, high)
run_target "da-17-3"

# Target 10: da-1-4 (bl=85, high)
run_target "da-1-4"

echo ""
echo "=============================================="
echo "ALL TARGETS COMPLETED at $(date)"
echo "=============================================="