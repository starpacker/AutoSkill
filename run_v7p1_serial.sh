#!/bin/bash
set -euo pipefail

MAX_ROUNDS=5
TIMEOUT_SECONDS=7200

HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"
TASKS_DIR="/data/yjh/biomnibench-organized"
BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

BASE_DIR="/data/yjh/skill-transfer-eval"
TRANSFER_DIR="${BASE_DIR}/transfer"
SKILLS_DIR="${BASE_DIR}/skills"
LOG_DIR="${BASE_DIR}/logs/v7p1_${TIMESTAMP}"

mkdir -p "$LOG_DIR" "$TRANSFER_DIR"
TASKS=("da-25-1" "da-13-6" "da-20-4" "da-4-1" "da-9-1")

echo "v7.1 Evaluation -- Batch 2 (5 targets, serial execution)"
echo "Targets: ${TASKS[*]}"
echo "Logs: $LOG_DIR"

export ANTHROPIC_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export ANTHROPIC_BASE_URL="https://api.gpugeek.com"
export ANTHROPIC_MODEL="Vendor3/DeepSeek-V4-Flash"
export QWEN_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export QWEN_BASE_URL="https://api.gpugeek.com/v1"
export QWEN_MODEL="Vendor2/Gemini-3-flash"

run_eval() {
  local target="$1"
  local log_file="${LOG_DIR}/${target}.log"
  local ts="${TIMESTAMP}_v7p1_${target}"
  local skill_dir="${SKILLS_DIR}/${target}/skills/generalized-transfer"
  if [[ ! -d "$skill_dir" ]]; then
    echo "[$(date +%H:%M:%S)] SKIP: No skill for $target"
    return 1
  fi
  echo "[$(date +%H:%M:%S)] Starting: $target"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "$target" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$TRANSFER_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --concurrency 1 \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$ts" \
    --quiet \
    --enable-skills \
    --skills-dir "${SKILLS_DIR}/${target}/skills" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$log_file" 2>&1
  local exit_code=$?
  echo "[$(date +%H:%M:%S)] Done: $target (exit=$exit_code)"
  tail -3 "$log_file" 2>/dev/null
  return $exit_code
}

for target in "${TASKS[@]}"; do
  run_eval "$target"
  echo "---"
done
echo "[$(date +%H:%M:%S)] All 5 targets complete!"