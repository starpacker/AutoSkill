#!/bin/bash
# Check skill-opt progress - Run 6 (193458)
echo "=== 1. TMUX CAPTURE ==="
tmux capture-pane -t skillopt -p -S -80 2>/dev/null || echo "tmux session not found"

echo "=== 2. PROCESS ==="
ps aux | grep train.py | grep -v grep

echo "=== 3. ALL STEPS ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/steps/ 2>/dev/null
echo ""

echo "=== 4. STEP RECORDS ==="
for s in /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/steps/step_*/step_record.json; do
    [ -f "$s" ] || continue
    echo "--- $(basename $(dirname $s))"
    python3 -c "
import json
d=json.load(open('$s'))
print(f'  rollout_hard={d[\"rollout_hard\"]} rollout_soft={d[\"rollout_soft\"]}')
print(f'  selection_hard={d[\"selection_hard\"]} selection_soft={d[\"selection_soft\"]}')
print(f'  action={d[\"action\"]} n_patches={d[\"n_patches\"]}')
print(f'  wall_time={d[\"wall_time_s\"]}s')
" 2>/dev/null
done

echo "=== 5. SKILLS ==="
ls -la /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/skills/ 2>/dev/null

echo "=== 6. RUNTIME STATE ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/runtime_state.json 2>/dev/null || echo "no runtime state"

echo "=== 7. HISTORY ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_193458/history.json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
for h in d:
    action = h.get('action','?')
    hard = h.get('selection_hard', h.get('hard','?'))
    soft = h.get('selection_soft', h.get('soft','?'))
    print(f'  step={h.get(\"step\",\"?\")}: action={action}, hard={hard}, soft={soft}')
" 2>/dev/null || echo "no history"