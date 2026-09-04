#!/usr/bin/env python3
"""Generate the few-shot baseline runner script on the server."""
import os, json

experiments = []
prompt_dir = "/data/yjh/skill-transfer-eval/fewshot_prompts"
for f in sorted(os.listdir(prompt_dir)):
    if f.endswith("_1A_raw_traj.md"):
        parts = f.replace("_1A_raw_traj.md", "").split("_to_")
        prefix = f.replace("_1A_raw_traj.md", "")
        src = parts[0].split("_", 1)[1]
        tgt = parts[1]
        experiments.append(("1A", src, tgt, prefix, os.path.join(prompt_dir, f)))
    elif f.endswith("_1B_traj_plus_skill.md"):
        parts = f.replace("_1B_traj_plus_skill.md", "").split("_to_")
        prefix = f.replace("_1B_traj_plus_skill.md", "")
        src = parts[0].split("_", 1)[1]
        tgt = parts[1]
        experiments.append(("1B", src, tgt, prefix, os.path.join(prompt_dir, f)))

# Batch: 2 at a time, avoid same target conflicts
batches = []
current_batch = []
current_targets = set()
for mode, src, tgt, prefix, prompt_file in experiments:
    if tgt in current_targets and len(current_batch) >= 1:
        batches.append(list(current_batch))
        current_batch = []
        current_targets = set()
    if len(current_batch) >= 2:
        batches.append(list(current_batch))
        current_batch = []
        current_targets = set()
    current_batch.append((mode, tgt, prefix, prompt_file))
    current_targets.add(tgt)
if current_batch:
    batches.append(list(current_batch))

# Write shell script
script_path = "/tmp/run_fewshot_baseline.sh"
with open(script_path, "w") as f:
    f.write("#!/bin/bash\n")
    f.write("# Few-shot baseline runner for V10 experiment pairs\n")
    f.write("set -euo pipefail\n")
    f.write("\n")
    f.write('HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"\n')
    f.write('TASKS_DIR="/data/yjh/biomnibench-organized"\n')
    f.write('BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"\n')
    f.write('MAX_ROUNDS=5\n')
    f.write('TIMEOUT_SECONDS=7200\n')
    f.write('CONCURRENCY=2\n')
    f.write('BASE_DIR="/data/yjh/skill-transfer-eval"\n')
    f.write('FEWSHOT_DIR="${BASE_DIR}/fewshot_transfer"\n')
    f.write('PROMPT_DIR="${BASE_DIR}/fewshot_prompts"\n')
    f.write('LOG_DIR="${BASE_DIR}/logs/fewshot_$(date +%Y%m%d_%H%M%S)"\n')
    f.write('mkdir -p "$LOG_DIR" "$FEWSHOT_DIR"\n')
    f.write("\n")
    f.write('export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"\n')
    f.write('export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"\n')
    f.write('export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor3/DeepSeek-V4-Flash}"\n')
    f.write('export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"\n')
    f.write('export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"\n')
    f.write('export QWEN_MODEL="${QWEN_MODEL:-Vendor2/Gemini-3.1-pro}"\n')
    f.write("\n")
    f.write('echo "=============================================="\n')
    f.write('echo "Few-shot Baseline Runner"\n')
    f.write('echo "Concurrency: $CONCURRENCY"\n')
    f.write('echo "Log dir: $LOG_DIR"\n')
    f.write('echo "=============================================="\n')
    f.write("\n")
    f.write('START_TIME=$(date +%s)\n')
    f.write('TOTAL=' + str(len(experiments)) + '\n')
    f.write('COMPLETED=0\n')
    f.write('FAILED=0\n')
    f.write("\n")
    f.write('run_experiment() {\n')
    f.write('  local mode="$1"\n')
    f.write('  local target="$2"\n')
    f.write('  local prefix="$3"\n')
    f.write('  local prompt_file="$4"\n')
    f.write('  local ts="${prefix}_fewshot_${mode}"\n')
    f.write('  local log_file="${LOG_DIR}/${prefix}_${mode}.log"\n')
    f.write('  echo "[$(date +%H:%M:%S)] Starting: ${prefix} ${mode}"\n')
    f.write('  cd "$HARNESS_DIR"\n')
    f.write('  $BUN_BIN src/harness/evaluation/cli.ts \\\n')
    f.write('    --task "$target" \\\n')
    f.write('    --tasks-dir "$TASKS_DIR" \\\n')
    f.write('    --runs-dir "$FEWSHOT_DIR" \\\n')
    f.write('    --max-rounds "$MAX_ROUNDS" \\\n')
    f.write('    --timeout-seconds "$TIMEOUT_SECONDS" \\\n')
    f.write('    --concurrency 1 \\\n')
    f.write('    --temperature 1 \\\n')
    f.write('    --thinking disabled \\\n')
    f.write('    --timestamp "$ts" \\\n')
    f.write('    --system-prompt "$prompt_file" \\\n')
    f.write('    --quiet \\\n')
    f.write('    > "$log_file" 2>&1\n')
    f.write('  local exit_code=$?\n')
    f.write('  echo "[$(date +%H:%M:%S)] Done: ${prefix} ${mode} (exit=$exit_code)"\n')
    f.write('  tail -5 "$log_file" 2>/dev/null\n')
    f.write('  return $exit_code\n')
    f.write('}\n')
    f.write("\n")
    f.write("# " + str(len(experiments)) + " experiments, " + str(len(batches)) + " batches\n")
    f.write("\n")
    
    for bidx, batch in enumerate(batches):
        f.write("# === Batch " + str(bidx+1) + "/" + str(len(batches)) + " ===\n")
        f.write("PIDS=()\n")
        for mode, tgt, prefix, prompt_file in batch:
            f.write('run_experiment "' + mode + '" "' + tgt + '" "' + prefix + '" "' + prompt_file + '" &\n')
            f.write("PIDS+=($!)\n")
        f.write("\n")
        f.write("  for pid in \"${PIDS[@]}\"; do\n")
        f.write("    wait \"$pid\" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))\n")
        f.write("  done\n")
        f.write('  echo "[$(date +%H:%M:%S)] Batch ' + str(bidx+1) + "/" + str(len(batches)) + ' done. $COMPLETED/$TOTAL, Failed: $FAILED"\n')
        f.write("\n")
    
    f.write('END_TIME=$(date +%s)\n')
    f.write('echo ""\n')
    f.write('echo "=============================================="\n')
    f.write('echo "All experiments complete"\n')
    f.write('echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED"\n')
    f.write('echo "Elapsed: $(( (END_TIME - START_TIME) / 60 ))m"\n')
    f.write('echo "=============================================="\n')

os.chmod(script_path, 0o755)
print("Script written: " + script_path)
print("Total experiments: " + str(len(experiments)))
print("Total batches: " + str(len(batches)))