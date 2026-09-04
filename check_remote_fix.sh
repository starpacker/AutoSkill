#!/bin/bash
echo "=== 2. LATEST OUTPUT DIR ==="
ls /data/yjh/skill-opt/repo/outputs/ | grep Vendor3-DeepSeek | tail -1

BASE="/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241"
echo "=== 3. STEPS ==="
ls "$BASE/steps/" 2>/dev/null || echo "no steps"

echo "=== 4. PREDICTIONS ==="
ls "$BASE/steps/step_0001/rollout/predictions/" 2>/dev/null || echo "no predictions"

echo "=== 5. CONVERSATIONS ==="
find "$BASE/" -name "conversation.json" 2>/dev/null | head -10

echo "=== 6. RUN SUMMARIES ==="
for f in $(find "$BASE/" -name "run_summary.json" 2>/dev/null); do
    task=$(echo $f | grep -oP "da-\d+-\d+")
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo "=== 7. JUDGE RESULTS ==="
for f in $(find "$BASE/" -name "judge_result_round_*.json" 2>/dev/null); do
    task=$(echo $f | grep -oP "da-\d+-\d+")
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: score={d.get(\"total_score\")}/100')" 2>/dev/null
done

echo "=== 8. STEP RECORD ==="
cat "$BASE/steps/step_0001/step_record.json" 2>/dev/null || echo "no step_record"

echo "=== 9. RUNTIME STATE ==="
cat "$BASE/runtime_state.json" 2>/dev/null || echo "no runtime"

echo "=== 10. SKILLS ==="
ls -la "$BASE/skills/" 2>/dev/null

echo "=== 11. HISTORY ==="
python3 -c "
import json,sys
try:
    d=json.load(open('$BASE/history.json'))
    if isinstance(d, list):
        for h in d:
            step = h.get('step','?')
            action = h.get('action','?')
            score = h.get('score', h.get('reflect_s','?'))
            patches = h.get('n_successful_patches', h.get('patches','?'))
            print(f'step={step}: action={action}, score={score}, patches={patches}')
    elif isinstance(d, dict):
        import json as j; print(j.dumps(d, indent=2)[:500])
except Exception as e:
    print(f'no history: {e}')
"

echo "=== 12. BASELINE 3 ==="
ps aux | grep "gt_few" | grep -v grep | head -3
tail -5 /tmp/gt_fewshot_nohup.log 2>/dev/null || echo "no log"
ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l

echo "=== 13. TMUX LATEST ==="
tmux capture-pane -t skillopt -p -S -50

echo "=== ALL DONE ==="