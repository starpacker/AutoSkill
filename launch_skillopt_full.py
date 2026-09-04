"""Launch full skill-opt experiment in tmux."""
import subprocess, os, tempfile

def scp_file(local_content, remote_path):
    tmp = tempfile.mktemp(suffix='.py')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', tmp, f'server1:{remote_path}'], capture_output=True, timeout=30)
        return True
    finally:
        try: os.unlink(tmp)
        except: pass

def run_ssh(cmd, timeout=60):
    result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'server1', cmd], capture_output=True, timeout=timeout)
    return result.stdout.decode('utf-8', errors='replace')

# Create launch script
launch_script = r'''#!/usr/bin/env bash
set -e

REPO_DIR="/data/yjh/skill-opt/repo"
VENV_DIR="/data/yjh/skill-opt/venv"
CONFIG="configs/biomnibench/default.yaml"
OUTPUT_DIR="/data/yjh/skill-opt/output/biomnibench_full"

mkdir -p "$OUTPUT_DIR"

cd "$REPO_DIR"

source "$VENV_DIR/bin/activate"

# Clean up any previous test run
echo "[$(date)] Starting skill-opt full experiment (23 train / 27 test)..."

# Run with:
# - config: biomnibench/default.yaml
# - limit 0 (use all tasks by default from split)
# - override num_epochs and batch_size
python scripts/train.py \
  --config "$CONFIG" \
  --output_dir "$OUTPUT_DIR" \
  --num_epochs 5 \
  --batch_size 4 \
  --seed 42 \
  2>&1

EXIT_CODE=$?
echo "[$(date)] Training finished with exit code $EXIT_CODE"
exit $EXIT_CODE
'''

scp_file(launch_script, "/data/yjh/skill-opt/launch_full_exp.sh")

# Make executable
stdout = run_ssh("chmod +x /data/yjh/skill-opt/launch_full_exp.sh && echo 'OK'")
print(f"Script created: {stdout}")

# Create tmux session command
tmux_cmd = "tmux new-session -d -s skillopt_full 'bash /data/yjh/skill-opt/launch_full_exp.sh'"
stdout = run_ssh(tmux_cmd, timeout=15)
print(f"Tmux launch: {stdout}")

# Verify
stdout = run_ssh("tmux list-sessions 2>/dev/null")
print(f"Sessions: {stdout}")

# Check output after a few seconds
import time
time.sleep(5)
stdout = run_ssh("tail -30 /data/yjh/skill-opt/output/biomnibench_full/log.txt 2>/dev/null || echo 'No log yet'; ls /data/yjh/skill-opt/output/biomnibench_full/ 2>/dev/null || echo 'No output dir yet'")
print(f"Initial output:\n{stdout[:2000]}")