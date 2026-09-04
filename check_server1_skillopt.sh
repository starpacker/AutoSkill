#!/bin/bash
echo "=== 1. TMUX CAPTURE ==="
tmux capture-pane -t skillopt -p -S -40 2>/dev/null || echo "tmux session not found"

echo ""
echo "=== 2. STEPS DIRECTORY ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/ 2>/dev/null || echo "no steps dir"

echo ""
echo "=== 2b. ROLLOUT RUNS ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/step_0001/rollout/runs/ 2>/dev/null || echo "no rollout runs"

echo ""
echo "=== 3. RUN_SUMMARY FILES ==="
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/ -name "run_summary.json" 2>/dev/null | head -10

echo ""
echo "=== 3b. REWARDS ==="
for f in $(find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/ -name "run_summary.json" 2>/dev/null | head -10); do
    echo "=== $f ==="
    python3 -c "import json; d=json.load(open('$f')); print(f'status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo ""
echo "=== 4. JUDGE RESULTS ==="
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/ -name "judge_result_round_*.json" 2>/dev/null | head -10

echo ""
echo "=== 4b. JUDGE SCORES ==="
for f in $(find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/ -name "judge_result_round_*.json" 2>/dev/null | head -5); do
    echo "=== $(basename $(dirname $(dirname $f))) ==="
    python3 -c "import json; d=json.load(open('$f')); print(f'  score={d.get(\"total_score\")}/100, model={d.get(\"model\")}')" 2>/dev/null
done

echo ""
echo "=== 5. REFLECT DIR ==="
ls /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/steps/step_0001/reflect/ 2>/dev/null || echo "no reflect dir"

echo ""
echo "=== 6. RUNTIME STATE ==="
cat /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_022041/runtime_state.json 2>/dev/null || echo "no runtime state"

echo ""
echo "=== 7. BASELINE 3 PROGRESS ==="
ps aux | grep "gt_few" | grep -v grep | head -3
echo "---"
tail -5 /tmp/gt_fewshot_nohup.log 2>/dev/null || echo "no log"
echo "---"
echo "Transfer file count:"
ls /data/yjh/skill-transfer-eval/gt_fewshot_transfer/ 2>/dev/null | wc -l

echo ""
echo "=== 8. CONCURRENT ROLLOUTS ==="
ps aux | grep "bun.*cli.ts" | grep -v grep | wc -l