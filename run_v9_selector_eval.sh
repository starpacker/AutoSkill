#!/bin/bash
# v9 Selector Evaluation — 5 targets with V9-recommended skills
# Judge: Gemini-3-flash via gpugeek API
# Worker: DeepSeek-V4-Flash

set -uo pipefail

MAX_ROUNDS=5
TIMEOUT_SECONDS=7200

HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"
TASKS_DIR="/data/yjh/biomnibench-organized"
BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

BASE_DIR="/data/yjh/skill-transfer-eval"
TRANSFER_DIR="${BASE_DIR}/transfer"
SKILLS_DIR="${BASE_DIR}/skills"
LOG_DIR="${BASE_DIR}/logs/v9_selector_${TIMESTAMP}"

mkdir -p "$LOG_DIR" "$TRANSFER_DIR"

# V9-selected targets with their recommended sources
declare -A TARGET_SOURCE
TARGET_SOURCE["da-25-1"]="v9-selector-da-18-5"   # mutation-analysis -> da-18-5 (mutation-analysis)
TARGET_SOURCE["da-24-3"]="v9-selector-da-13-3"   # gwas-eqtl -> da-13-3 (association-testing)
TARGET_SOURCE["da-13-6"]="v9-selector-da-13-5"   # cross-cohort-comparison -> da-13-5 (cross-cohort-comparison)
TARGET_SOURCE["da-20-4"]="v9-selector-da-20-3"   # pathway-enrichment -> da-20-3 (pathway-enrichment)
TARGET_SOURCE["da-8-3"]="v9-selector-da-19-3"    # differential-expression -> da-19-3 (chromatin-profiling)

TASKS=("da-25-1" "da-24-3" "da-13-6" "da-20-4" "da-8-3")

echo "============================================"
echo "v9 Selector Evaluation (5 targets, serial)"
echo "Started: $(date)"
echo "Logs: $LOG_DIR"
echo "Targets: ${TASKS[*]}"
echo "============================================"

# API keys and model config
export ANTHROPIC_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export ANTHROPIC_BASE_URL="https://api.gpugeek.com"
export ANTHROPIC_MODEL="Vendor3/DeepSeek-V4-Flash"
export QWEN_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export QWEN_BASE_URL="https://api.gpugeek.com/v1"
export QWEN_MODEL="Vendor2/Gemini-3-flash"

run_eval() {
  local target="$1"
  local skill_name="${TARGET_SOURCE[$target]}"
  local log_file="${LOG_DIR}/${target}.log"
  local ts="${TIMESTAMP}_v9_${target}"

  echo "[$(date +%H:%M:%S)] ===== STARTING: $target -> $skill_name ====="

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
    --skill-name "$skill_name" \
    --max-active-skills 1 \
    > "$log_file" 2>&1

  local exit_code=$?
  echo "[$(date +%H:%M:%S)] ===== DONE: $target (exit=$exit_code) ====="
  tail -5 "$log_file" 2>/dev/null
  echo "---"
  return $exit_code
}

for target in "${TASKS[@]}"; do
  run_eval "$target"
done

echo "[$(date +%H:%M:%S)] All 5 targets complete!"
echo "Logs: $LOG_DIR"