#!/bin/bash
OUTDIR=/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424

echo '=== 3. RUN_SUMMARY REWARDS ==='
for f in $(find $OUTDIR/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== 4. CONVERSATION FILES IN STEPS ==='
find $OUTDIR/steps/ -name 'conversation.json' 2>/dev/null | head -20

echo 'SEPARATOR'
echo '=== 5. STEP_RECORD FOR ALL STEPS ==='
for d in $(ls -d $OUTDIR/steps/step_*/ 2>/dev/null | sort); do
    echo '=== '$(basename $d)' ==='
    python3 -c "import json; d=json.load(open('$d/step_record.json')); print(f'  rollout_hard={d.get(\"rollout_hard\")}, rollout_soft={d.get(\"rollout_soft\")}, n_patches={d.get(\"n_patches\")}, n_failure_patches={d.get(\"n_failure_patches\")}, n_success_patches={d.get(\"n_success_patches\")}, action={d.get(\"action\")}, reflect_s={d.get(\"timing\",{}).get(\"reflect_s\")}')" 2>/dev/null || echo '  no step_record'
done

echo 'SEPARATOR'
echo '=== 6. SKILLS DIRECTORY ==='
ls -la $OUTDIR/skills/ 2>&1

echo 'SEPARATOR'
echo '=== 7. PATCHES ==='
for d in $(ls -d $OUTDIR/steps/step_*/ 2>/dev/null | sort); do
    echo '=== '$(basename $d)' ==='
    if [ -d $d/patches ] && [ "$(ls -A $d/patches/ 2>/dev/null)" ]; then
        echo '  HAS PATCHES! Count: '$(ls -1 $d/patches/ | wc -l)
    else
        echo '  no patches'
    fi
done

echo 'SEPARATOR'
echo '=== 8. RUNTIME STATE ==='
cat $OUTDIR/runtime_state.json 2>&1

echo 'SEPARATOR'
echo '=== 9. HISTORY ==='
python3 -c "import json,sys; d=json.load(open('$OUTDIR/history.json'))
if isinstance(d, list):
    for h in d:
        print(f'step={h.get(\"step\",\"?\")}: action={h.get(\"action\",\"?\")}, score={h.get(\"score\",h.get(\"reflect_s\",\"?\"))}, patches={h.get(\"n_successful_patches\",h.get(\"patches\",\"?\"))}')
elif isinstance(d, dict):
    print(json.dumps(d, indent=2)[:500])
" 2>/dev/null || echo 'no history'

echo 'SEPARATOR'
echo '=== 10. BASELINE EVAL SCORES ==='
for f in $(find $OUTDIR/selection_eval_baseline/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== RUN_SUMMARY IN ROLLOUTS ==='
for f in $(find $OUTDIR/steps/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== STEP_0003 RECORD ==='
cat $OUTDIR/steps/step_0003/step_record.json 2>/dev/null || echo 'no file'

echo 'SEPARATOR'
echo '=== SKILL SIZES ==='
wc -c $OUTDIR/skills/*.md

echo 'SEPARATOR'
echo '=== DIFF SKILL_V0000 vs V0001 ==='
diff $OUTDIR/skills/skill_v0000.md $OUTDIR/skills/skill_v0001.md | head -30

echo '---'
echo '=== DIFF SKILL_V0001 vs V0002 ==='
diff $OUTDIR/skills/skill_v0001.md $OUTDIR/skills/skill_v0002.md | head -30

echo 'SEPARATOR'
echo '=== STEP_0003 ROLLOUT STRUCTURE ==='
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/steps/step_0003/ -type f 2>/dev/null | head -30

echo 'SEPARATOR'
echo '=== STEP_0001 ROLLOUT JSON FILES ==='
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/steps/step_0001/ -type f -name '*.json' 2>/dev/null | head -30

echo 'SEPARATOR'
echo '=== BEST SKILL ==='
ls -la /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/best_skill.md 2>/dev/null
wc -c /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/best_skill.md 2>/dev/null

echo 'SEPARATOR'
echo '=== STEP_0003 rollout dir ==='
ls -la /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/steps/step_0003/rollout/ 2>/dev/null
echo '---'
ls -la /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424/steps/step_0003/rollout/predictions/ 2>/dev/null

echo 'SEPARATOR'
echo '=== PROGRESS: stack trace from tmux ==='
tmux capture-pane -t skillopt -p -S -300 2>&1 | tail -60

echo 'SEPARATOR'
echo '=== RUN_SUMMARY from step_0001 rollouts ==='
BASE=/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_145424
for f in $(find $BASE/steps/step_0001/rollout/runs/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== RUN_SUMMARY from step_0002 rollouts ==='
for f in $(find $BASE/steps/step_0002/rollout/runs/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== RUN_SUMMARY from step_0003 rollouts ==='
for f in $(find $BASE/steps/step_0003/rollout/runs/ -name 'run_summary.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== JUDGE RESULTS step_0001 ==='
for f in $(find $BASE/steps/step_0001/rollout/runs/ -name 'judge_result_round_1.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: score={d.get(\"total_score\",\"?\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== JUDGE RESULTS step_0002 ==='
for f in $(find $BASE/steps/step_0002/rollout/runs/ -name 'judge_result_round_1.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: score={d.get(\"total_score\",\"?\")}')" 2>/dev/null
done

echo 'SEPARATOR'
echo '=== JUDGE RESULTS step_0003 ==='
for f in $(find $BASE/steps/step_0003/rollout/runs/ -name 'judge_result_round_1.json' 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  {task}: score={d.get(\"total_score\",\"?\")}')" 2>/dev/null
done