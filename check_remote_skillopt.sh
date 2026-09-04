#!/bin/bash
# Script to check skill-opt progress on server1
# Run via: ssh yjh@10.128.247.28 < this_script.sh

echo "=== 1. TMUX CAPTURE ==="
tmux capture-pane -t skillopt -p -S -50 2>/dev/null || echo "tmux session not found"

echo "=== 2. ROLLOUT RUNS ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/step_0001/rollout/runs/ 2>/dev/null || echo "no rollout runs"

echo "=== 3. RUN SUMMARIES ==="
for f in $(find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/ -name "run_summary.json" 2>/dev/null); do
    echo "--- $f"
    python3 -c "import json; d=json.load(open('$f')); print(f'status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo "=== 4. JUDGE RESULTS ==="
for f in $(find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/ -name "judge_result_round_*.json" 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  $task: score={d.get(\"total_score\")}/100, model={d.get(\"model\")}')" 2>/dev/null
done

echo "=== 5. REFLECT DIR ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/step_0001/reflect/ 2>/dev/null || echo "no reflect dir"

echo "=== 6. STEP RECORD ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/step_0001/step_record.json 2>/dev/null || echo "no step_record"

echo "=== 7. ALL STEPS ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/ 2>/dev/null

echo "=== 8. RUNTIME STATE ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/runtime_state.json 2>/dev/null || echo "no runtime state"

echo "=== 9. SKILLS DIR ==="
ls -la /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/skills/ 2>/dev/null

echo "=== 10. HISTORY ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/history.json 2>/dev/null | python3 -c "
import json,sys
d=json.load(sys.stdin)
if isinstance(d, list):
    for h in d:
        action = h.get('action','?')
        score = h.get('score', h.get('reflect_s', '?'))
        patches = h.get('n_successful_patches', h.get('patches', '?'))
        print(f'  step={h.get(\"step\",\"?\")}: action={action}, score={score}, patches={patches}')
elif isinstance(d, dict):
    print(json.dumps(d, indent=2)[:500])
" 2>/dev/null || echo "no history"

echo "=== 11. BASELINE 3 ==="
ps aux | grep "gt_few" | grep -v grep | head -3
echo "TAIL LOG:"
tail -5 /tmp/gt_fewshot_nohup.log 2>/dev/null || echo "no log"
echo "TRANSFER DIR:"
ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l