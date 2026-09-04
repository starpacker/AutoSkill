#!/bin/bash
# V10 da-24-3 New Skill Transfer — da-8-2 -> da-24-3
# Generated 2026-08-27
# da-24-3 (gwas-eqtl) previously failed with 3 association sources (da-13-3, da-14-3, da-8-1).
# Trying da-8-2 (association-testing) as a new source - same compatibility group 2.

HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"
TASKS_DIR="/data/yjh/biomnibench-organized"
TRANSFER_DIR="/data/yjh/skill-transfer-eval/transfer"
SKILLS_BASE="/data/yjh/skill-transfer-eval/skills"
GENERALIZED_SKILLS="/data/yjh/skill-transfer-eval/generalized_skills"
BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"
MAX_ROUNDS=5
TIMEOUT_SECONDS=7200

export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor3/DeepSeek-V4-Flash}"
export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-Vendor3/DeepSeek-V4-Flash}"
export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"
export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"
export QWEN_MODEL="${QWEN_MODEL:-Vendor3/qwen3.5-plus}"

LOG_DIR="/data/yjh/skill-transfer-eval/logs/da24_3_new_skill_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "da-24-3 New Skill: da-8-2 -> da-24-3"
echo "Log dir: $LOG_DIR"
echo "=============================================="

# Deploy generalized skill
SOURCE="da-8-2"
TARGET="da-24-3"
SKILL_NAME="v10-da24-3-cross-${SOURCE}"
TS="v10_da24_3_cross_${SOURCE}_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${SOURCE}_to_${TARGET}.log"

echo "[1/1] Deploying: ${SOURCE} -> ${TARGET} as ${SKILL_NAME}"
mkdir -p "${SKILLS_BASE}/${TARGET}/skills"
rm -rf "${SKILLS_BASE}/${TARGET}/skills/${SKILL_NAME}"
ln -s "${GENERALIZED_SKILLS}/${SOURCE}" "${SKILLS_BASE}/${TARGET}/skills/${SKILL_NAME}"

echo "Running: ${TARGET} <- ${SOURCE} (skill=${SKILL_NAME})"
cd "$HARNESS_DIR"
$BUN_BIN src/harness/evaluation/cli.ts \
  --task "${TARGET}" \
  --tasks-dir "${TASKS_DIR}" \
  --runs-dir "${TRANSFER_DIR}" \
  --max-rounds "${MAX_ROUNDS}" \
  --timeout-seconds "${TIMEOUT_SECONDS}" \
  --concurrency 1 \
  --temperature 1 \
  --thinking disabled \
  --timestamp "${TS}" \
  --quiet \
  --enable-skills \
  --skills-dir "${SKILLS_BASE}/${TARGET}/skills" \
  --skill-name "${SKILL_NAME}" \
  --max-active-skills 1 \
  > "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "[$(date +%H:%M:%S)] ${SOURCE} -> ${TARGET} completed successfully"
else
  echo "[$(date +%H:%M:%S)] ${SOURCE} -> ${TARGET} FAILED (exit=$EXIT_CODE)"
fi

echo "=============================================="
echo "Experiment complete!"
echo "Log: $LOG_FILE"
echo "=============================================="