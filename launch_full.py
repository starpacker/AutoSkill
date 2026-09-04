"""Launch skill-opt full experiment and check baseline."""
import subprocess, json, os, tempfile, time

def run_ssh(cmd, timeout=60):
    try:
        result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'server1', cmd], capture_output=True, timeout=timeout)
        return result.stdout.decode('utf-8', errors='replace'), result.stderr.decode('utf-8', errors='replace'), result.returncode
    except subprocess.TimeoutExpired:
        return '', 'TIMEOUT', -1
    except Exception as e:
        return '', str(e), -1

def scp_file(local_content, remote_path):
    tmp = tempfile.mktemp(suffix='.sh')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', tmp, f'server1:{remote_path}'], capture_output=True, timeout=30)
        return True
    finally:
        try: os.unlink(tmp)
        except: pass

# ============================================================
# STEP 1: Check SSH is working
# ============================================================
print("=== STEP 1: Check SSH ===")
stdout, stderr, rc = run_ssh("echo OK", timeout=15)
print(f"SSH: {stdout} (rc={rc})")

if rc != 0:
    print("SSH not available, will retry later")
    exit(1)

# ============================================================
# STEP 2: Create the launch script
# ============================================================
print("\n=== STEP 2: Create launch script ===")

launch_script = r"""#!/bin/bash
set -e

REPO_DIR="/data/yjh/skill-opt/repo"
VENV_DIR="/data/yjh/skill-opt/venv"
CONFIG="configs/biomnibench/default.yaml"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
OUTPUT_DIR="/data/yjh/skill-opt/output/biomnibench_full_${TIMESTAMP}"

# Source venv to get API keys and model config
source "$VENV_DIR/bin/activate"

# Verify env
echo "[$(date)] MODEL: $OPENAI_COMPATIBLE_MODEL"
echo "[$(date)] Using config: $CONFIG"
echo "[$(date)] Output: $OUTPUT_DIR"

cd "$REPO_DIR"

mkdir -p "$OUTPUT_DIR"

# Run training
python scripts/train.py \
  --config "$CONFIG" \
  --output_dir "$OUTPUT_DIR" \
  --num_epochs 5 \
  --batch_size 4 \
  --seed 42 \
  2>&1 | tee "$OUTPUT_DIR/training.log"

EXIT_CODE=${PIPESTATUS[0]}
echo "[$(date)] Training finished with exit code $EXIT_CODE"
exit $EXIT_CODE
"""

scp_file(launch_script, "/data/yjh/skill-opt/launch_full_exp.sh")
stdout, stderr, rc = run_ssh("chmod +x /data/yjh/skill-opt/launch_full_exp.sh && echo 'Script ready'")
print(f"Script ready: {stdout}")

# ============================================================
# STEP 3: Launch in tmux
# ============================================================
print("\n=== STEP 3: Launch in tmux ===")

# Kill old session if exists
run_ssh("tmux kill-session -t skillopt_full 2>/dev/null; echo 'Cleaned'")

# Launch new session
tmux_cmd = "tmux new-session -d -s skillopt_full 'bash /data/yjh/skill-opt/launch_full_exp.sh'"
stdout, stderr, rc = run_ssh(tmux_cmd, timeout=15)
print(f"Launch: {stdout} (rc={rc})")

# Check session
time.sleep(2)
stdout, stderr, rc = run_ssh("tmux list-sessions 2>/dev/null")
print(f"Sessions: {stdout.strip()}")

# ============================================================
# STEP 4: Check initial output
# ============================================================
print("\n=== STEP 4: Check initial output ===")
time.sleep(5)
stdout, stderr, rc = run_ssh("ls -lt /data/yjh/skill-opt/output/ 2>/dev/null | head -5")
print(f"Output dirs: {stdout[:500]}")

# ============================================================
# STEP 5: Update NEXT_STEPS_TODO.md
# ============================================================
print("\n=== STEP 5: Update NEXT_STEPS_TODO.md ===")