#!/bin/bash
# V10 Oracle Re-run Script — da-6-2 and da-6-5
# Generated 2026-08-27
# Re-runs oracle experiments for tasks that previously failed (oracle=0).

HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"
TASKS_DIR="/data/yjh/biomnibench-organized"
RUNS_DIR="/data/yjh/skill-transfer-eval/generalized"
SKILLS_BASE="/data/yjh/skill-transfer-eval/skills"
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

LOG_DIR="/data/yjh/skill-transfer-eval/logs/oracle_rerun_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "Oracle Re-run: da-6-2, da-6-5"
echo "Log dir: $LOG_DIR"
echo "=============================================="

# ── da-6-2 Oracle Re-run ─────────────────────────────────────────────────
TASK="da-6-2"
SKILL_NAME="oracle-da-6-2"
SKILL_DIR="/data/yjh/biomnibench-skill-bundles/${TASK}/skills/${SKILL_NAME}"
TS="oracle_rerun_${TASK}_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${TASK}_oracle_rerun.log"

echo "[1/2] Running oracle for ${TASK}..."
echo "  Skill: ${SKILL_DIR}"
echo "  Timestamp: ${TS}"

cd "$HARNESS_DIR"
$BUN_BIN src/harness/evaluation/cli.ts \
  --task "${TASK}" \
  --tasks-dir "${TASKS_DIR}" \
  --runs-dir "${RUNS_DIR}" \
  --max-rounds "${MAX_ROUNDS}" \
  --timeout-seconds "${TIMEOUT_SECONDS}" \
  --concurrency 1 \
  --temperature 1 \
  --thinking disabled \
  --timestamp "${TS}" \
  --quiet \
  --enable-skills \
  --skills-dir "${SKILL_DIR}" \
  --skill-name "${SKILL_NAME}" \
  --max-active-skills 1 \
  > "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "[$(date +%H:%M:%S)] da-6-2 oracle re-run completed successfully"
else
  echo "[$(date +%H:%M:%S)] da-6-2 oracle re-run FAILED (exit=$EXIT_CODE)"
fi

# ── da-6-5 Oracle Re-run ─────────────────────────────────────────────────
TASK="da-6-5"
SKILL_NAME="oracle-da-6-5"
SKILL_DIR="/data/yjh/biomnibench-skill-bundles/${TASK}/skills/${SKILL_NAME}"
TS="oracle_rerun_${TASK}_$(date +%Y%m%d_%H%M%S)"
LOG_FILE="$LOG_DIR/${TASK}_oracle_rerun.log"

echo "[2/2] Running oracle for ${TASK}..."
echo "  Skill: ${SKILL_DIR}"
echo "  Timestamp: ${TS}"

cd "$HARNESS_DIR"
$BUN_BIN src/harness/evaluation/cli.ts \
  --task "${TASK}" \
  --tasks-dir "${TASKS_DIR}" \
  --runs-dir "${RUNS_DIR}" \
  --max-rounds "${MAX_ROUNDS}" \
  --timeout-seconds "${TIMEOUT_SECONDS}" \
  --concurrency 1 \
  --temperature 1 \
  --thinking disabled \
  --timestamp "${TS}" \
  --quiet \
  --enable-skills \
  --skills-dir "${SKILL_DIR}" \
  --skill-name "${SKILL_NAME}" \
  --max-active-skills 1 \
  > "$LOG_FILE" 2>&1

EXIT_CODE=$?
if [ $EXIT_CODE -eq 0 ]; then
  echo "[$(date +%H:%M:%S)] da-6-5 oracle re-run completed successfully"
else
  echo "[$(date +%H:%M:%S)] da-6-5 oracle re-run FAILED (exit=$EXIT_CODE)"
fi

echo "=============================================="
echo "Both oracle re-runs complete!"
echo "Logs: $LOG_DIR"
echo "=============================================="