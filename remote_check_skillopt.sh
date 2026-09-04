#!/bin/bash
# Remote skillopt diagnostic script

OUTPUT_DIR="/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_174731"

echo "=========================================="
echo "1. TMUX SESSION CAPTURE"
echo "=========================================="
tmux capture-pane -t skillopt -p -S -80 2>/dev/null || echo "no tmux session"

echo ""
echo "=========================================="
echo "2. STEPS COMPLETED"
echo "=========================================="
ls "$OUTPUT_DIR/steps/" 2>/dev/null || echo "no steps dir"

echo ""
echo "=========================================="
echo "3. ALL RUN_SUMMARY REWARDS"
echo "=========================================="
for f in $(find "$OUTPUT_DIR/" -name "run_summary.json" 2>/dev/null); do
    task=$(echo $f | grep -oP 'da-\d+-\d+')
    python3 -c "import json; d=json.load(open('$f')); print(f'  $task: status={d.get(\"status\")}, reward={d.get(\"reward\")}')" 2>/dev/null
done

echo ""
echo "=========================================="
echo "4. STEP_RECORD FOR ALL STEPS"
echo "=========================================="
for d in $(ls -d "$OUTPUT_DIR/steps/step_*/" 2>/dev/null | sort); do
    echo "=== $(basename $d) ==="
    python3 -c "import json; d=json.load(open('$d/step_record.json')); print(f'  action={d.get(\"action\")}, n_patches={d.get(\"n_patches\")}, n_success={d.get(\"n_success_patches\")}, n_failure={d.get(\"n_failure_patches\")}, reflect_s={d.get(\"timing\",{}).get(\"reflect_s\")}')" 2>/dev/null || echo "  no step_record"
done

echo ""
echo "=========================================="
echo "5. SKILLS DIRECTORY"
echo "=========================================="
ls -la "$OUTPUT_DIR/skills/" 2>/dev/null || echo "no skills dir"

echo ""
echo "=========================================="
echo "6. PATCHES CHECK"
echo "=========================================="
for d in $(ls -d "$OUTPUT_DIR/steps/step_*/" 2>/dev/null | sort); do
    echo "=== $(basename $d) ==="
    if [ -d "$d/patches" ]; then
        count=$(ls -1 "$d/patches/" 2>/dev/null | wc -l)
        echo "  HAS PATCHES! Count: $count"
    else
        echo "  no patches"
    fi
done

echo ""
echo "=========================================="
echo "7. RUNTIME STATE"
echo "=========================================="
cat "$OUTPUT_DIR/runtime_state.json" 2>/dev/null || echo "no runtime_state.json"

echo ""
echo "=========================================="
echo "8. HISTORY"
echo "=========================================="
python3 -c "
import json, sys
try:
    d = json.load(open('$OUTPUT_DIR/history.json'))
    if isinstance(d, list):
        for h in d:
            step = h.get('step', '?')
            action = h.get('action', '?')
            score = h.get('score', h.get('reflect_s', '?'))
            patches = h.get('n_successful_patches', h.get('patches', '?'))
            print(f'  step={step}: action={action}, score={score}, patches={patches}')
    elif isinstance(d, dict):
        print(json.dumps(d, indent=2)[:500])
except Exception as e:
    print(f'  error: {e}')
" 2>/dev/null || echo "  no history"