#!/bin/bash
echo '=== BASELINE JUDGE da-25-1 ==='
python3 -c "
import json
d = json.load(open('/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/selection_eval_baseline/runs/da-25-1/.judge_private/da-25-1_skillopt_da-25-1_1788205362/judge_result_round_1.json'))
print('total_score:', d.get('total_score'), '/100')
print('breakdown:', d.get('breakdown_score', '?'))
" 2>/dev/null
echo '=== BASELINE JUDGE da-9-1 ==='
python3 -c "
import json
d = json.load(open('/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/selection_eval_baseline/runs/da-9-1/.judge_private/da-9-1_skillopt_da-9-1_1788205705/judge_result_round_2.json'))
print('total_score:', d.get('total_score'), '/100')
print('breakdown:', d.get('breakdown_score', '?'))
" 2>/dev/null
echo '=== da-20-1 progress ==='
wc -l /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/steps/step_0001/rollout/runs/da-20-1/da-20-1_skillopt_da-20-1_1788206280/logs/trajectory.clean.jsonl 2>/dev/null
echo '=== run_events tail ==='
tail -5 /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/steps/step_0001/rollout/runs/da-20-1/da-20-1_skillopt_da-20-1_1788206280/logs/run_events.jsonl 2>/dev/null
echo '=== conversation.json check ==='
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/ -name conversation.json -type f 2>/dev/null | head -10
echo '=== run_summary check ==='
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/ -name run_summary.json -type f 2>/dev/null | head -10
echo '=== judge_result check ==='
find /data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_034241/ -name 'judge_result_round_*.json' -type f 2>/dev/null | head -10