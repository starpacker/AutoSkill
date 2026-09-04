#!/bin/bash
OUTDIR=/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241

echo '=== 1. TMUX SESSION ==='
tmux capture-pane -t skillopt -p -S -50 2>/dev/null

echo ''
echo '=== 2. STEPS ==='
ls $OUTDIR/steps/ 2>/dev/null || echo 'no steps'

echo ''
echo '=== 3. PREDICTIONS ==='
ls $OUTDIR/steps/step_0001/rollout/predictions/ 2>/dev/null || echo 'no predictions'

echo ''
echo '=== 4. CONVERSATION.JSON FILES ==='
find $OUTDIR/ -name conversation.json 2>/dev/null | head -10

echo ''
echo '=== 5. RUN_SUMMARY REWARDS ==='
for f in $(find $OUTDIR/ -name run_summary.json 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo ''
echo '=== 6. JUDGE RESULTS ==='
for f in $(find $OUTDIR/ -name 'judge_result_round_*.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: score={d.get(\"total_score\")}/100')" 2>/dev/null
done

echo ''
echo '=== 7. STEP_RECORD ==='
cat $OUTDIR/steps/step_0001/step_record.json 2>/dev/null || echo 'no step_record'

echo ''
echo '=== 8. RUNTIME STATE ==='
cat $OUTDIR/runtime_state.json 2>/dev/null || echo 'no runtime'

echo ''
echo '=== 9. SKILLS ==='
ls -la $OUTDIR/skills/ 2>/dev/null

echo ''
echo '=== 10. HISTORY ==='
cat $OUTDIR/history.json 2>/dev/null | python3 -c '
import json,sys
d=json.load(sys.stdin)
if isinstance(d, list):
    for h in d:
        s = h.get("score", h.get("reflect_s", "?"))
        p = h.get("n_successful_patches", h.get("patches", "?"))
        print(f"step={h.get(\"step\",\"?\")}: action={h.get(\"action\",\"?\")}, score={s}, patches={p}")
elif isinstance(d, dict):
    print(json.dumps(d, indent=2)[:500])
' 2>/dev/null || echo 'no history'

echo ''
echo '=== 11. BASELINE 3 ==='
ps aux | grep gt_few | grep -v grep | head -3
tail -5 /tmp/gt_fewshot_nohup.log 2>/dev/null || echo 'no log'
ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l

echo ''
echo '=== ALL CHECKS COMPLETE ==='