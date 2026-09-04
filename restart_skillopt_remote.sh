#!/bin/bash
echo "=== Step 1: Killing old processes ==="
pkill -f "scripts/train.py" 2>/dev/null || true
ps aux | grep "bun.*harness" | grep -v "gt_few" | grep -v "grep" | awk "{print \$2}" | xargs kill 2>/dev/null || true
sleep 2
echo "=== Remaining train.py ==="
ps aux | grep "train.py" | grep -v grep
echo "---bun---"
ps aux | grep "bun.*harness" | grep -v grep | grep -v "gt_few"
echo "=== Step 1 DONE ==="

echo "=== Step 2: Cleaning output dir ==="
rm -rf /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041
echo "Cleanup done"
ls /data/yjh/skill-opt/repo/outputs/ 2>&1
echo "=== Step 2 DONE ==="

echo "=== Step 3: Verify fix ==="
grep -n "_save_conversation\|_trajectory_to_conversation" /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py
echo "=== Step 3 DONE ==="

echo "=== Step 4: Kill old tmux ==="
tmux kill-session -t skillopt 2>/dev/null || true
echo "=== Step 4 DONE ==="

echo "=== Step 5: Start fresh tmux ==="
tmux new-session -d -s skillopt
tmux send-keys -t skillopt "bash /data/yjh/skill-opt/repo/run_skillopt.sh" Enter
echo "Launched in tmux session skillopt"
echo "=== Step 5 DONE ==="