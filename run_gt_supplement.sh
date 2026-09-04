#!/bin/bash
# Auto-generated GT supplement experiment runner
# Total experiments: 55, concurrency: 3

# No set -e: background process failures handled by exit code checks

HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"
TASKS_DIR="/data/yjh/biomnibench-organized"
RUNS_DIR="/data/yjh/skill-transfer-eval/generalized"
SKILLS_BASE="/data/yjh/skill-transfer-eval/skills"
GENERALIZED_SKILLS="/data/yjh/skill-transfer-eval/generalized_skills"
BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"
MAX_ROUNDS=5
TIMEOUT_SECONDS=7200
CONCURRENCY=3

# Export API config
export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"
export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"
export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor2/Claude-4.7-opus}"
export ANTHROPIC_SMALL_FAST_MODEL="${ANTHROPIC_SMALL_FAST_MODEL:-Vendor3/DeepSeek-V4-Flash}"
export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"
export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"
export QWEN_MODEL="${QWEN_MODEL:-Vendor3/qwen3.5-plus}"

TOTAL=55
COMPLETED=0
FAILED=0
START_TIME=$(date +%s)
LOG_DIR="/data/yjh/skill-transfer-eval/logs/gt_supplement_$(date +%Y%m%d_%H%M%S)"
mkdir -p "$LOG_DIR"

echo "=============================================="
echo "GT Supplement Experiment Runner"
echo "Total: $TOTAL | Concurrency: $CONCURRENCY"
echo "Log dir: $LOG_DIR"
echo "=============================================="


# === Batch 1/19 ===
PIDS=()

# Exp 1: da-1-3 -> da-10-1
(
  mkdir -p "$SKILLS_BASE/da-10-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-1-3/SKILL.md" "$SKILLS_BASE/da-10-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-10-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-1-3",
    "target_task": "da-10-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_001_da-1-3_to_da-10-1"
  LOG_FILE="$LOG_DIR/001_da-1-3_to_da-10-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-10-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-10-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 1/19: Completed da-1-3 -> da-10-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 1/19: FAILED da-1-3 -> da-10-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 2: da-1-3 -> da-10-3
(
  mkdir -p "$SKILLS_BASE/da-10-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-1-3/SKILL.md" "$SKILLS_BASE/da-10-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-10-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-1-3",
    "target_task": "da-10-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_002_da-1-3_to_da-10-3"
  LOG_FILE="$LOG_DIR/002_da-1-3_to_da-10-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-10-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-10-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 1/19: Completed da-1-3 -> da-10-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 1/19: FAILED da-1-3 -> da-10-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 3: da-1-3 -> da-11-1
(
  mkdir -p "$SKILLS_BASE/da-11-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-1-3/SKILL.md" "$SKILLS_BASE/da-11-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-11-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-1-3",
    "target_task": "da-11-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_003_da-1-3_to_da-11-1"
  LOG_FILE="$LOG_DIR/003_da-1-3_to_da-11-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-11-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-11-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 1/19: Completed da-1-3 -> da-11-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 1/19: FAILED da-1-3 -> da-11-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 1/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 2/19 ===
PIDS=()

# Exp 4: da-13-1 -> da-1-3
(
  mkdir -p "$SKILLS_BASE/da-1-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-1/SKILL.md" "$SKILLS_BASE/da-1-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-1-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-1",
    "target_task": "da-1-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_004_da-13-1_to_da-1-3"
  LOG_FILE="$LOG_DIR/004_da-13-1_to_da-1-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-1-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-1-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 2/19: Completed da-13-1 -> da-1-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 2/19: FAILED da-13-1 -> da-1-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 5: da-13-3 -> da-12-2
(
  mkdir -p "$SKILLS_BASE/da-12-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-3/SKILL.md" "$SKILLS_BASE/da-12-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-12-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-3",
    "target_task": "da-12-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_005_da-13-3_to_da-12-2"
  LOG_FILE="$LOG_DIR/005_da-13-3_to_da-12-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-12-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-12-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 2/19: Completed da-13-3 -> da-12-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 2/19: FAILED da-13-3 -> da-12-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 6: da-13-3 -> da-12-4
(
  mkdir -p "$SKILLS_BASE/da-12-4/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-3/SKILL.md" "$SKILLS_BASE/da-12-4/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-12-4/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-3",
    "target_task": "da-12-4",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_006_da-13-3_to_da-12-4"
  LOG_FILE="$LOG_DIR/006_da-13-3_to_da-12-4.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-12-4" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-12-4/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 2/19: Completed da-13-3 -> da-12-4"
  else
    echo "[$(date +%H:%M:%S)] Batch 2/19: FAILED da-13-3 -> da-12-4 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 2/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 3/19 ===
PIDS=()

# Exp 7: da-13-3 -> da-13-1
(
  mkdir -p "$SKILLS_BASE/da-13-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-3/SKILL.md" "$SKILLS_BASE/da-13-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-13-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-3",
    "target_task": "da-13-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_007_da-13-3_to_da-13-1"
  LOG_FILE="$LOG_DIR/007_da-13-3_to_da-13-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-13-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-13-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 3/19: Completed da-13-3 -> da-13-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 3/19: FAILED da-13-3 -> da-13-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 9: da-13-5 -> da-14-1
(
  mkdir -p "$SKILLS_BASE/da-14-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-5/SKILL.md" "$SKILLS_BASE/da-14-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-14-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-5",
    "target_task": "da-14-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_009_da-13-5_to_da-14-1"
  LOG_FILE="$LOG_DIR/009_da-13-5_to_da-14-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-14-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-14-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 3/19: Completed da-13-5 -> da-14-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 3/19: FAILED da-13-5 -> da-14-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 10: da-13-5 -> da-14-3
(
  mkdir -p "$SKILLS_BASE/da-14-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-5/SKILL.md" "$SKILLS_BASE/da-14-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-14-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-5",
    "target_task": "da-14-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_010_da-13-5_to_da-14-3"
  LOG_FILE="$LOG_DIR/010_da-13-5_to_da-14-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-14-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-14-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 3/19: Completed da-13-5 -> da-14-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 3/19: FAILED da-13-5 -> da-14-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 3/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 4/19 ===
PIDS=()

# Exp 8: da-13-5 -> da-13-3
(
  mkdir -p "$SKILLS_BASE/da-13-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-13-5/SKILL.md" "$SKILLS_BASE/da-13-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-13-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-13-5",
    "target_task": "da-13-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_008_da-13-5_to_da-13-3"
  LOG_FILE="$LOG_DIR/008_da-13-5_to_da-13-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-13-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-13-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 4/19: Completed da-13-5 -> da-13-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 4/19: FAILED da-13-5 -> da-13-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 11: da-14-1 -> da-15-1
(
  mkdir -p "$SKILLS_BASE/da-15-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-14-1/SKILL.md" "$SKILLS_BASE/da-15-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-15-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-14-1",
    "target_task": "da-15-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_011_da-14-1_to_da-15-1"
  LOG_FILE="$LOG_DIR/011_da-14-1_to_da-15-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-15-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-15-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 4/19: Completed da-14-1 -> da-15-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 4/19: FAILED da-14-1 -> da-15-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 12: da-14-1 -> da-15-2
(
  mkdir -p "$SKILLS_BASE/da-15-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-14-1/SKILL.md" "$SKILLS_BASE/da-15-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-15-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-14-1",
    "target_task": "da-15-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_012_da-14-1_to_da-15-2"
  LOG_FILE="$LOG_DIR/012_da-14-1_to_da-15-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-15-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-15-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 4/19: Completed da-14-1 -> da-15-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 4/19: FAILED da-14-1 -> da-15-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 4/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 5/19 ===
PIDS=()

# Exp 13: da-14-3 -> da-16-1
(
  mkdir -p "$SKILLS_BASE/da-16-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-14-3/SKILL.md" "$SKILLS_BASE/da-16-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-16-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-14-3",
    "target_task": "da-16-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_013_da-14-3_to_da-16-1"
  LOG_FILE="$LOG_DIR/013_da-14-3_to_da-16-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-16-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-16-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 5/19: Completed da-14-3 -> da-16-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 5/19: FAILED da-14-3 -> da-16-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 14: da-14-3 -> da-17-1
(
  mkdir -p "$SKILLS_BASE/da-17-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-14-3/SKILL.md" "$SKILLS_BASE/da-17-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-17-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-14-3",
    "target_task": "da-17-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_014_da-14-3_to_da-17-1"
  LOG_FILE="$LOG_DIR/014_da-14-3_to_da-17-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-17-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-17-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 5/19: Completed da-14-3 -> da-17-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 5/19: FAILED da-14-3 -> da-17-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 15: da-14-3 -> da-18-1
(
  mkdir -p "$SKILLS_BASE/da-18-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-14-3/SKILL.md" "$SKILLS_BASE/da-18-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-18-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-14-3",
    "target_task": "da-18-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_015_da-14-3_to_da-18-1"
  LOG_FILE="$LOG_DIR/015_da-14-3_to_da-18-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-18-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-18-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 5/19: Completed da-14-3 -> da-18-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 5/19: FAILED da-14-3 -> da-18-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 5/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 6/19 ===
PIDS=()

# Exp 16: da-15-1 -> da-18-5
(
  mkdir -p "$SKILLS_BASE/da-18-5/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-15-1/SKILL.md" "$SKILLS_BASE/da-18-5/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-18-5/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-15-1",
    "target_task": "da-18-5",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_016_da-15-1_to_da-18-5"
  LOG_FILE="$LOG_DIR/016_da-15-1_to_da-18-5.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-18-5" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-18-5/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 6/19: Completed da-15-1 -> da-18-5"
  else
    echo "[$(date +%H:%M:%S)] Batch 6/19: FAILED da-15-1 -> da-18-5 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 17: da-15-2 -> da-19-1
(
  mkdir -p "$SKILLS_BASE/da-19-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-15-2/SKILL.md" "$SKILLS_BASE/da-19-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-19-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-15-2",
    "target_task": "da-19-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_017_da-15-2_to_da-19-1"
  LOG_FILE="$LOG_DIR/017_da-15-2_to_da-19-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-19-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-19-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 6/19: Completed da-15-2 -> da-19-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 6/19: FAILED da-15-2 -> da-19-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 18: da-15-2 -> da-19-3
(
  mkdir -p "$SKILLS_BASE/da-19-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-15-2/SKILL.md" "$SKILLS_BASE/da-19-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-19-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-15-2",
    "target_task": "da-19-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_018_da-15-2_to_da-19-3"
  LOG_FILE="$LOG_DIR/018_da-15-2_to_da-19-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-19-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-19-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 6/19: Completed da-15-2 -> da-19-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 6/19: FAILED da-15-2 -> da-19-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 6/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 7/19 ===
PIDS=()

# Exp 19: da-15-2 -> da-20-1
(
  mkdir -p "$SKILLS_BASE/da-20-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-15-2/SKILL.md" "$SKILLS_BASE/da-20-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-20-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-15-2",
    "target_task": "da-20-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_019_da-15-2_to_da-20-1"
  LOG_FILE="$LOG_DIR/019_da-15-2_to_da-20-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-20-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-20-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 7/19: Completed da-15-2 -> da-20-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 7/19: FAILED da-15-2 -> da-20-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 20: da-17-1 -> da-20-3
(
  mkdir -p "$SKILLS_BASE/da-20-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-17-1/SKILL.md" "$SKILLS_BASE/da-20-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-20-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-17-1",
    "target_task": "da-20-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_020_da-17-1_to_da-20-3"
  LOG_FILE="$LOG_DIR/020_da-17-1_to_da-20-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-20-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-20-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 7/19: Completed da-17-1 -> da-20-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 7/19: FAILED da-17-1 -> da-20-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 21: da-17-1 -> da-24-3
(
  mkdir -p "$SKILLS_BASE/da-24-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-17-1/SKILL.md" "$SKILLS_BASE/da-24-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-24-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-17-1",
    "target_task": "da-24-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_021_da-17-1_to_da-24-3"
  LOG_FILE="$LOG_DIR/021_da-17-1_to_da-24-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-24-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-24-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 7/19: Completed da-17-1 -> da-24-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 7/19: FAILED da-17-1 -> da-24-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 7/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 8/19 ===
PIDS=()

# Exp 22: da-17-1 -> da-25-1
(
  mkdir -p "$SKILLS_BASE/da-25-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-17-1/SKILL.md" "$SKILLS_BASE/da-25-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-25-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-17-1",
    "target_task": "da-25-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_022_da-17-1_to_da-25-1"
  LOG_FILE="$LOG_DIR/022_da-17-1_to_da-25-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-25-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-25-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 8/19: Completed da-17-1 -> da-25-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 8/19: FAILED da-17-1 -> da-25-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 23: da-18-1 -> da-26-2
(
  mkdir -p "$SKILLS_BASE/da-26-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-18-1/SKILL.md" "$SKILLS_BASE/da-26-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-26-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-18-1",
    "target_task": "da-26-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_023_da-18-1_to_da-26-2"
  LOG_FILE="$LOG_DIR/023_da-18-1_to_da-26-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-26-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-26-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 8/19: Completed da-18-1 -> da-26-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 8/19: FAILED da-18-1 -> da-26-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 24: da-18-1 -> da-3-4
(
  mkdir -p "$SKILLS_BASE/da-3-4/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-18-1/SKILL.md" "$SKILLS_BASE/da-3-4/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-3-4/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-18-1",
    "target_task": "da-3-4",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_024_da-18-1_to_da-3-4"
  LOG_FILE="$LOG_DIR/024_da-18-1_to_da-3-4.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-3-4" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-3-4/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 8/19: Completed da-18-1 -> da-3-4"
  else
    echo "[$(date +%H:%M:%S)] Batch 8/19: FAILED da-18-1 -> da-3-4 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 8/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 9/19 ===
PIDS=()

# Exp 25: da-18-1 -> da-3-5
(
  mkdir -p "$SKILLS_BASE/da-3-5/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-18-1/SKILL.md" "$SKILLS_BASE/da-3-5/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-3-5/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-18-1",
    "target_task": "da-3-5",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_025_da-18-1_to_da-3-5"
  LOG_FILE="$LOG_DIR/025_da-18-1_to_da-3-5.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-3-5" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-3-5/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 9/19: Completed da-18-1 -> da-3-5"
  else
    echo "[$(date +%H:%M:%S)] Batch 9/19: FAILED da-18-1 -> da-3-5 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 26: da-18-5 -> da-4-1
(
  mkdir -p "$SKILLS_BASE/da-4-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-18-5/SKILL.md" "$SKILLS_BASE/da-4-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-4-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-18-5",
    "target_task": "da-4-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_026_da-18-5_to_da-4-1"
  LOG_FILE="$LOG_DIR/026_da-18-5_to_da-4-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-4-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-4-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 9/19: Completed da-18-5 -> da-4-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 9/19: FAILED da-18-5 -> da-4-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 27: da-18-5 -> da-4-6
(
  mkdir -p "$SKILLS_BASE/da-4-6/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-18-5/SKILL.md" "$SKILLS_BASE/da-4-6/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-4-6/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-18-5",
    "target_task": "da-4-6",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_027_da-18-5_to_da-4-6"
  LOG_FILE="$LOG_DIR/027_da-18-5_to_da-4-6.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-4-6" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-4-6/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 9/19: Completed da-18-5 -> da-4-6"
  else
    echo "[$(date +%H:%M:%S)] Batch 9/19: FAILED da-18-5 -> da-4-6 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 9/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 10/19 ===
PIDS=()

# Exp 28: da-19-1 -> da-5-1
(
  mkdir -p "$SKILLS_BASE/da-5-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-1/SKILL.md" "$SKILLS_BASE/da-5-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-5-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-1",
    "target_task": "da-5-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_028_da-19-1_to_da-5-1"
  LOG_FILE="$LOG_DIR/028_da-19-1_to_da-5-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-5-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-5-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 10/19: Completed da-19-1 -> da-5-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 10/19: FAILED da-19-1 -> da-5-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 29: da-19-1 -> da-6-2
(
  mkdir -p "$SKILLS_BASE/da-6-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-1/SKILL.md" "$SKILLS_BASE/da-6-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-6-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-1",
    "target_task": "da-6-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_029_da-19-1_to_da-6-2"
  LOG_FILE="$LOG_DIR/029_da-19-1_to_da-6-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-6-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-6-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 10/19: Completed da-19-1 -> da-6-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 10/19: FAILED da-19-1 -> da-6-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 30: da-19-1 -> da-6-5
(
  mkdir -p "$SKILLS_BASE/da-6-5/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-1/SKILL.md" "$SKILLS_BASE/da-6-5/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-6-5/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-1",
    "target_task": "da-6-5",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_030_da-19-1_to_da-6-5"
  LOG_FILE="$LOG_DIR/030_da-19-1_to_da-6-5.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-6-5" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-6-5/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 10/19: Completed da-19-1 -> da-6-5"
  else
    echo "[$(date +%H:%M:%S)] Batch 10/19: FAILED da-19-1 -> da-6-5 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 10/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 11/19 ===
PIDS=()

# Exp 31: da-19-3 -> da-8-1
(
  mkdir -p "$SKILLS_BASE/da-8-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-3/SKILL.md" "$SKILLS_BASE/da-8-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-8-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-3",
    "target_task": "da-8-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_031_da-19-3_to_da-8-1"
  LOG_FILE="$LOG_DIR/031_da-19-3_to_da-8-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-8-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-8-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 11/19: Completed da-19-3 -> da-8-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 11/19: FAILED da-19-3 -> da-8-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 32: da-19-4 -> da-8-2
(
  mkdir -p "$SKILLS_BASE/da-8-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-4/SKILL.md" "$SKILLS_BASE/da-8-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-8-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-4",
    "target_task": "da-8-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_032_da-19-4_to_da-8-2"
  LOG_FILE="$LOG_DIR/032_da-19-4_to_da-8-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-8-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-8-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 11/19: Completed da-19-4 -> da-8-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 11/19: FAILED da-19-4 -> da-8-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 33: da-19-4 -> da-9-1
(
  mkdir -p "$SKILLS_BASE/da-9-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-4/SKILL.md" "$SKILLS_BASE/da-9-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-9-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-4",
    "target_task": "da-9-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_033_da-19-4_to_da-9-1"
  LOG_FILE="$LOG_DIR/033_da-19-4_to_da-9-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-9-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-9-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 11/19: Completed da-19-4 -> da-9-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 11/19: FAILED da-19-4 -> da-9-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 11/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 12/19 ===
PIDS=()

# Exp 34: da-19-4 -> da-9-7
(
  mkdir -p "$SKILLS_BASE/da-9-7/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-19-4/SKILL.md" "$SKILLS_BASE/da-9-7/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-9-7/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-19-4",
    "target_task": "da-9-7",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_034_da-19-4_to_da-9-7"
  LOG_FILE="$LOG_DIR/034_da-19-4_to_da-9-7.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-9-7" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-9-7/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 12/19: Completed da-19-4 -> da-9-7"
  else
    echo "[$(date +%H:%M:%S)] Batch 12/19: FAILED da-19-4 -> da-9-7 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 35: da-20-1 -> da-1-3
(
  mkdir -p "$SKILLS_BASE/da-1-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-20-1/SKILL.md" "$SKILLS_BASE/da-1-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-1-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-20-1",
    "target_task": "da-1-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_035_da-20-1_to_da-1-3"
  LOG_FILE="$LOG_DIR/035_da-20-1_to_da-1-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-1-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-1-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 12/19: Completed da-20-1 -> da-1-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 12/19: FAILED da-20-1 -> da-1-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 36: da-20-1 -> da-1-4
(
  mkdir -p "$SKILLS_BASE/da-1-4/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-20-1/SKILL.md" "$SKILLS_BASE/da-1-4/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-1-4/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-20-1",
    "target_task": "da-1-4",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_036_da-20-1_to_da-1-4"
  LOG_FILE="$LOG_DIR/036_da-20-1_to_da-1-4.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-1-4" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-1-4/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 12/19: Completed da-20-1 -> da-1-4"
  else
    echo "[$(date +%H:%M:%S)] Batch 12/19: FAILED da-20-1 -> da-1-4 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 12/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 13/19 ===
PIDS=()

# Exp 37: da-20-3 -> da-10-1
(
  mkdir -p "$SKILLS_BASE/da-10-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-20-3/SKILL.md" "$SKILLS_BASE/da-10-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-10-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-20-3",
    "target_task": "da-10-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_037_da-20-3_to_da-10-1"
  LOG_FILE="$LOG_DIR/037_da-20-3_to_da-10-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-10-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-10-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 13/19: Completed da-20-3 -> da-10-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 13/19: FAILED da-20-3 -> da-10-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 38: da-20-3 -> da-10-3
(
  mkdir -p "$SKILLS_BASE/da-10-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-20-3/SKILL.md" "$SKILLS_BASE/da-10-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-10-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-20-3",
    "target_task": "da-10-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_038_da-20-3_to_da-10-3"
  LOG_FILE="$LOG_DIR/038_da-20-3_to_da-10-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-10-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-10-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 13/19: Completed da-20-3 -> da-10-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 13/19: FAILED da-20-3 -> da-10-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 39: da-26-2 -> da-11-1
(
  mkdir -p "$SKILLS_BASE/da-11-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-26-2/SKILL.md" "$SKILLS_BASE/da-11-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-11-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-26-2",
    "target_task": "da-11-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_039_da-26-2_to_da-11-1"
  LOG_FILE="$LOG_DIR/039_da-26-2_to_da-11-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-11-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-11-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 13/19: Completed da-26-2 -> da-11-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 13/19: FAILED da-26-2 -> da-11-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 13/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 14/19 ===
PIDS=()

# Exp 40: da-26-2 -> da-12-2
(
  mkdir -p "$SKILLS_BASE/da-12-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-26-2/SKILL.md" "$SKILLS_BASE/da-12-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-12-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-26-2",
    "target_task": "da-12-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_040_da-26-2_to_da-12-2"
  LOG_FILE="$LOG_DIR/040_da-26-2_to_da-12-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-12-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-12-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 14/19: Completed da-26-2 -> da-12-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 14/19: FAILED da-26-2 -> da-12-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 41: da-4-1 -> da-12-4
(
  mkdir -p "$SKILLS_BASE/da-12-4/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-4-1/SKILL.md" "$SKILLS_BASE/da-12-4/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-12-4/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-4-1",
    "target_task": "da-12-4",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_041_da-4-1_to_da-12-4"
  LOG_FILE="$LOG_DIR/041_da-4-1_to_da-12-4.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-12-4" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-12-4/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 14/19: Completed da-4-1 -> da-12-4"
  else
    echo "[$(date +%H:%M:%S)] Batch 14/19: FAILED da-4-1 -> da-12-4 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 42: da-4-1 -> da-13-1
(
  mkdir -p "$SKILLS_BASE/da-13-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-4-1/SKILL.md" "$SKILLS_BASE/da-13-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-13-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-4-1",
    "target_task": "da-13-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_042_da-4-1_to_da-13-1"
  LOG_FILE="$LOG_DIR/042_da-4-1_to_da-13-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-13-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-13-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 14/19: Completed da-4-1 -> da-13-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 14/19: FAILED da-4-1 -> da-13-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 14/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 15/19 ===
PIDS=()

# Exp 43: da-4-6 -> da-13-3
(
  mkdir -p "$SKILLS_BASE/da-13-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-4-6/SKILL.md" "$SKILLS_BASE/da-13-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-13-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-4-6",
    "target_task": "da-13-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_043_da-4-6_to_da-13-3"
  LOG_FILE="$LOG_DIR/043_da-4-6_to_da-13-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-13-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-13-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 15/19: Completed da-4-6 -> da-13-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 15/19: FAILED da-4-6 -> da-13-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 44: da-4-6 -> da-14-1
(
  mkdir -p "$SKILLS_BASE/da-14-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-4-6/SKILL.md" "$SKILLS_BASE/da-14-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-14-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-4-6",
    "target_task": "da-14-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_044_da-4-6_to_da-14-1"
  LOG_FILE="$LOG_DIR/044_da-4-6_to_da-14-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-14-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-14-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 15/19: Completed da-4-6 -> da-14-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 15/19: FAILED da-4-6 -> da-14-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 45: da-4-6 -> da-14-3
(
  mkdir -p "$SKILLS_BASE/da-14-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-4-6/SKILL.md" "$SKILLS_BASE/da-14-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-14-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-4-6",
    "target_task": "da-14-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_045_da-4-6_to_da-14-3"
  LOG_FILE="$LOG_DIR/045_da-4-6_to_da-14-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-14-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-14-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 15/19: Completed da-4-6 -> da-14-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 15/19: FAILED da-4-6 -> da-14-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 15/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 16/19 ===
PIDS=()

# Exp 46: da-5-1 -> da-15-1
(
  mkdir -p "$SKILLS_BASE/da-15-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-5-1/SKILL.md" "$SKILLS_BASE/da-15-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-15-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-5-1",
    "target_task": "da-15-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_046_da-5-1_to_da-15-1"
  LOG_FILE="$LOG_DIR/046_da-5-1_to_da-15-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-15-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-15-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 16/19: Completed da-5-1 -> da-15-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 16/19: FAILED da-5-1 -> da-15-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 47: da-5-1 -> da-15-2
(
  mkdir -p "$SKILLS_BASE/da-15-2/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-5-1/SKILL.md" "$SKILLS_BASE/da-15-2/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-15-2/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-5-1",
    "target_task": "da-15-2",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_047_da-5-1_to_da-15-2"
  LOG_FILE="$LOG_DIR/047_da-5-1_to_da-15-2.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-15-2" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-15-2/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 16/19: Completed da-5-1 -> da-15-2"
  else
    echo "[$(date +%H:%M:%S)] Batch 16/19: FAILED da-5-1 -> da-15-2 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 48: da-6-2 -> da-16-1
(
  mkdir -p "$SKILLS_BASE/da-16-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-6-2/SKILL.md" "$SKILLS_BASE/da-16-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-16-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-6-2",
    "target_task": "da-16-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_048_da-6-2_to_da-16-1"
  LOG_FILE="$LOG_DIR/048_da-6-2_to_da-16-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-16-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-16-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 16/19: Completed da-6-2 -> da-16-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 16/19: FAILED da-6-2 -> da-16-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 16/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 17/19 ===
PIDS=()

# Exp 49: da-6-2 -> da-17-1
(
  mkdir -p "$SKILLS_BASE/da-17-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-6-2/SKILL.md" "$SKILLS_BASE/da-17-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-17-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-6-2",
    "target_task": "da-17-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_049_da-6-2_to_da-17-1"
  LOG_FILE="$LOG_DIR/049_da-6-2_to_da-17-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-17-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-17-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 17/19: Completed da-6-2 -> da-17-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 17/19: FAILED da-6-2 -> da-17-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 50: da-6-2 -> da-17-3
(
  mkdir -p "$SKILLS_BASE/da-17-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-6-2/SKILL.md" "$SKILLS_BASE/da-17-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-17-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-6-2",
    "target_task": "da-17-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_050_da-6-2_to_da-17-3"
  LOG_FILE="$LOG_DIR/050_da-6-2_to_da-17-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-17-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-17-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 17/19: Completed da-6-2 -> da-17-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 17/19: FAILED da-6-2 -> da-17-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 51: da-8-1 -> da-17-5
(
  mkdir -p "$SKILLS_BASE/da-17-5/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-8-1/SKILL.md" "$SKILLS_BASE/da-17-5/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-17-5/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-8-1",
    "target_task": "da-17-5",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_051_da-8-1_to_da-17-5"
  LOG_FILE="$LOG_DIR/051_da-8-1_to_da-17-5.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-17-5" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-17-5/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 17/19: Completed da-8-1 -> da-17-5"
  else
    echo "[$(date +%H:%M:%S)] Batch 17/19: FAILED da-8-1 -> da-17-5 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 17/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 18/19 ===
PIDS=()

# Exp 52: da-8-1 -> da-18-1
(
  mkdir -p "$SKILLS_BASE/da-18-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-8-1/SKILL.md" "$SKILLS_BASE/da-18-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-18-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-8-1",
    "target_task": "da-18-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_052_da-8-1_to_da-18-1"
  LOG_FILE="$LOG_DIR/052_da-8-1_to_da-18-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-18-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-18-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 18/19: Completed da-8-1 -> da-18-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 18/19: FAILED da-8-1 -> da-18-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 53: da-8-2 -> da-18-5
(
  mkdir -p "$SKILLS_BASE/da-18-5/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-8-2/SKILL.md" "$SKILLS_BASE/da-18-5/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-18-5/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-8-2",
    "target_task": "da-18-5",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_053_da-8-2_to_da-18-5"
  LOG_FILE="$LOG_DIR/053_da-8-2_to_da-18-5.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-18-5" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-18-5/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 18/19: Completed da-8-2 -> da-18-5"
  else
    echo "[$(date +%H:%M:%S)] Batch 18/19: FAILED da-8-2 -> da-18-5 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

# Exp 54: da-8-2 -> da-19-1
(
  mkdir -p "$SKILLS_BASE/da-19-1/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-8-2/SKILL.md" "$SKILLS_BASE/da-19-1/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-19-1/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-8-2",
    "target_task": "da-19-1",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_054_da-8-2_to_da-19-1"
  LOG_FILE="$LOG_DIR/054_da-8-2_to_da-19-1.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-19-1" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-19-1/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 18/19: Completed da-8-2 -> da-19-1"
  else
    echo "[$(date +%H:%M:%S)] Batch 18/19: FAILED da-8-2 -> da-19-1 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 18/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"

# === Batch 19/19 ===
PIDS=()

# Exp 55: da-8-2 -> da-19-3
(
  mkdir -p "$SKILLS_BASE/da-19-3/skills/generalized-transfer"
  cp "$GENERALIZED_SKILLS/da-8-2/SKILL.md" "$SKILLS_BASE/da-19-3/skills/generalized-transfer/SKILL.md"
  cat > "$SKILLS_BASE/da-19-3/skills/generalized-transfer/metadata.json" << METADATA
  {
    "source_task": "da-8-2",
    "target_task": "da-19-3",
    "deployed_at": "$(date +%Y%m%d_%H%M%S)"
  }
METADATA
  TS="gt_supp_055_da-8-2_to_da-19-3"
  LOG_FILE="$LOG_DIR/055_da-8-2_to_da-19-3.log"
  cd "$HARNESS_DIR"
  $BUN_BIN src/harness/evaluation/cli.ts \
    --task "da-19-3" \
    --tasks-dir "$TASKS_DIR" \
    --runs-dir "$RUNS_DIR" \
    --max-rounds "$MAX_ROUNDS" \
    --timeout-seconds "$TIMEOUT_SECONDS" \
    --temperature 1 \
    --thinking disabled \
    --timestamp "$TS" \
    --quiet \
    --enable-skills \
    --skills-dir "$SKILLS_BASE/da-19-3/skills/generalized-transfer" \
    --skill-name generalized-transfer \
    --max-active-skills 1 \
    > "$LOG_FILE" 2>&1
  EXIT_CODE=$?
  if [ $EXIT_CODE -eq 0 ]; then
    echo "[$(date +%H:%M:%S)] Batch 19/19: Completed da-8-2 -> da-19-3"
  else
    echo "[$(date +%H:%M:%S)] Batch 19/19: FAILED da-8-2 -> da-19-3 (exit=$EXIT_CODE)"
  fi
  exit $EXIT_CODE
) &
PIDS+=($!)

  # Wait for this batch
  for pid in "${PIDS[@]}"; do
    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))
  done
  echo "[$(date +%H:%M:%S)] Batch 19/19 complete. So far: $COMPLETED/$TOTAL, Failed: $FAILED"


END_TIME=$(date +%s)
ELAPSED=$((END_TIME - START_TIME))
ELAPSED_MIN=$((ELAPSED / 60))

echo ""
echo "=============================================="
echo "Batch Complete"
echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED"
echo "Elapsed: ${ELAPSED_MIN}m"
echo "=============================================="