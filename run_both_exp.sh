#!/bin/bash
cd /data/yjh/skill-transfer-eval
echo "Starting within-category experiment at $(date)"
nohup python3 /data/yjh/skill-transfer-eval/run_expand_within.py --max-concurrent 2 > /data/yjh/skill-transfer-eval/logs/expand_within_run.log 2>&1 &
WITHIN_PID=$!
echo "Within-category PID: $WITHIN_PID"
echo "Starting cross-category experiment at $(date)"
nohup python3 /data/yjh/skill-transfer-eval/run_expand_cross.py --max-concurrent 2 > /data/yjh/skill-transfer-eval/logs/expand_cross_run.log 2>&1 &
CROSS_PID=$!
echo "Cross-category PID: $CROSS_PID"
echo "Both experiments started. PIDs: $WITHIN_PID $CROSS_PID"
echo "$WITHIN_PID $CROSS_PID" > /data/yjh/skill-transfer-eval/logs/expand_pids.txt