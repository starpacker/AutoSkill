#!/usr/bin/env python3
"""
Pipeline for Trajectory Few-shot Baseline:
1. prep_fewshot_data.py --gen-prompts  → Generate system prompt files + runner script
2. bash run_fewshot_baseline.sh        → Run experiments on server1
"""
import json, os, sys, glob, stat

BASE_DIR = "/data/yjh/skill-transfer-eval"
BASELINE_DIR = os.path.join(BASE_DIR, "baseline")
SKILLS_DIR = os.path.join(BASE_DIR, "generalized_skills")
PROMPT_DIR = os.path.join(BASE_DIR, "fewshot_prompts")
FEWSHOT_DIR = os.path.join(BASE_DIR, "fewshot_transfer")

# The 23 V10 experiment pairs (source, target, batch)
V10_PAIRS = [
    # Batch 1
    ("da-26-2", "da-10-1", 1),
    ("da-20-3", "da-12-2", 1),
    ("da-13-5", "da-13-6", 1),
    ("da-14-3", "da-15-7", 1),
    ("da-5-1",  "da-15-8", 1),
    ("da-19-4", "da-19-6", 1),
    ("da-20-3", "da-20-4", 1),
    ("da-13-3", "da-24-3", 1),
    ("da-18-5", "da-25-1", 1),
    ("da-26-2", "da-26-4", 1),
    ("da-19-3", "da-8-3",  1),
    ("da-4-6",  "da-9-1",  1),
    # Batch 2
    ("da-18-1", "da-25-1", 2),
    ("da-13-1", "da-8-3",  2),
    ("da-15-1", "da-8-3",  2),
    ("da-19-3", "da-19-6", 2),
    ("da-14-3", "da-24-3", 2),
    ("da-8-1",  "da-24-3", 2),
    # Batch 3
    ("da-8-1",  "da-15-7", 3),
    ("da-8-2",  "da-15-7", 3),
    ("da-19-1", "da-8-3",  3),
    ("da-18-1", "da-4-7",  3),
    ("da-6-2",  "da-9-1",  3),
]

def find_baseline_traj(source_task_id):
    pat = os.path.join(BASELINE_DIR, source_task_id + "_*_baseline_rep1/logs/trajectory.raw.jsonl")
    matches = sorted(glob.glob(pat))
    if matches:
        return matches[0]
    pat2 = os.path.join(BASELINE_DIR, source_task_id + "_*_baseline_rep2/logs/trajectory.raw.jsonl")
    matches2 = sorted(glob.glob(pat2))
    if matches2:
        return matches2[0]
    return None

def traj_to_markdown_compact(filepath, max_events=35):
    if not filepath or not os.path.exists(filepath):
        return None
    with open(filepath) as f:
        events = [json.loads(line) for line in f]
    
    lines = []
    selected = [ev for ev in events if ev.get("type") != "run_context" and ev.get("kind") != "run_context"]
    
    if len(selected) > max_events:
        keep = list(selected[:12])
        finalize_idx = None
        for i, ev in enumerate(selected):
            t = ev.get("type", ev.get("kind", ""))
            if t == "tool_call" and ev.get("tool") == "finalize_submission":
                finalize_idx = i
                break
        if finalize_idx and finalize_idx > 12:
            start_idx = max(12, finalize_idx - 8)
            keep.extend(selected[start_idx:])
        else:
            keep.extend(selected[-10:])
        selected = keep
        lines.append("> *(Trajectory truncated: " + str(len(events)) + " events)*\n")
    
    for ev in selected:
        t = ev.get("type", ev.get("kind", ""))
        r = ev.get("round", "?")
        
        if t == "assistant_text":
            text = ev.get("text", "").strip()
            if text:
                if len(text) > 300:
                    text = text[:300] + "..."
                lines.append("> **Round " + str(r) + " - Thinking:** " + text + "\n")
        
        elif t == "tool_call":
            tool = ev.get("tool", "?")
            inp = ev.get("input", {})
            if isinstance(inp, dict):
                if tool == "Read":
                    fp = inp.get("file_path", "")
                    lines.append("> **Round " + str(r) + " - Read:** `" + fp + "`\n")
                elif tool == "Bash":
                    cmd = inp.get("command", "")
                    if len(cmd) > 200:
                        cmd = cmd[:200] + "..."
                    lines.append("> **Round " + str(r) + " - Bash:** `" + cmd + "`\n")
                elif tool == "Write":
                    fp = inp.get("file_path", "")
                    lines.append("> **Round " + str(r) + " - Write:** `" + fp + "`\n")
                elif tool == "Edit":
                    fp = inp.get("file_path", "")
                    lines.append("> **Round " + str(r) + " - Edit:** `" + fp + "`\n")
                elif tool == "Skill":
                    args = str(inp.get("arguments", ""))[:100]
                    lines.append("> **Round " + str(r) + " - Skill Used:** " + args + "\n")
                elif tool == "finalize_submission":
                    lines.append("> **Round " + str(r) + " - FINALIZE SUBMISSION**\n")
                else:
                    lines.append("> **Round " + str(r) + " - " + tool + ":** " + str(inp)[:100] + "\n")
            else:
                lines.append("> **Round " + str(r) + " - " + tool + ":** " + str(inp)[:100] + "\n")
        
        elif t == "tool_result":
            ok = ev.get("ok", True)
            if not ok:
                err_text = str(ev.get("text", ""))[:200]
                lines.append("> **Error:** " + err_text + "\n")
        
        elif t == "skill_check":
            skill = ev.get("skill", "")
            status = ev.get("status", "")
            lines.append("> **Skill Check:** `" + skill + "` -> " + status + "\n")
    
    return "\n".join(lines)

def load_skill(source_task_id):
    f = os.path.join(SKILLS_DIR, source_task_id, "SKILL.md")
    if os.path.exists(f):
        with open(f) as fh:
            return fh.read()
    return None

def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--gen-prompts":
        os.makedirs(PROMPT_DIR, exist_ok=True)
        os.makedirs(FEWSHOT_DIR, exist_ok=True)
        
        print("=" * 70)
        print("Generating few-shot prompts for V10 experiment pairs")
        print("=" * 70)
        
        # Check data availability
        missing = 0
        for src, tgt, batch in V10_PAIRS:
            traj = find_baseline_traj(src)
            if not traj:
                print("  MISSING: B" + str(batch) + " " + src + " -> " + tgt + " - no baseline traj")
                missing += 1
        
        print("")
        experiments = []
        generated = 0
        
        for src, tgt, batch in V10_PAIRS:
            prefix = "B" + str(batch) + "_" + src + "_to_" + tgt
            traj_path = find_baseline_traj(src)
            skill = load_skill(src)
            
            if not traj_path:
                continue
            
            traj_md = traj_to_markdown_compact(traj_path)
            if not traj_md:
                continue
            
            # 1A: Raw trajectory
            prompt_1a = "# Reference: Example Problem-Solving Trajectory\n\n"
            prompt_1a += "Below is a trace of how a similar bioinformatics task was solved. "
            prompt_1a += "Use this as a reference for your approach.\n\n"
            prompt_1a += "**Source task**: " + src + "\n"
            prompt_1a += "**Target task**: " + tgt + "\n\n"
            prompt_1a += traj_md
            
            path_1a = os.path.join(PROMPT_DIR, prefix + "_1A_raw_traj.md")
            with open(path_1a, "w") as f:
                f.write(prompt_1a)
            experiments.append(("1A", src, tgt, prefix, path_1a))
            
            # 1B: Trajectory + Skills
            if skill:
                prompt_1b = "# Reference: Example Problem-Solving Trajectory (with Skills)\n\n"
                prompt_1b += "Below is a trace of how a similar bioinformatics task was solved, "
                prompt_1b += "along with the reusable skill extracted from this task.\n\n"
                prompt_1b += "**Source task**: " + src + "\n"
                prompt_1b += "**Target task**: " + tgt + "\n\n"
                prompt_1b += "## Source Skill\n\n"
                prompt_1b += "The following skill was extracted from the source task:\n\n"
                prompt_1b += "```markdown\n" + skill + "\n```\n\n"
                prompt_1b += "## Trajectory\n\n"
                prompt_1b += traj_md
                
                path_1b = os.path.join(PROMPT_DIR, prefix + "_1B_traj_plus_skill.md")
                with open(path_1b, "w") as f:
                    f.write(prompt_1b)
                experiments.append(("1B", src, tgt, prefix, path_1b))
            
            generated += 1
            print("  [" + str(generated) + "] " + prefix + ": 1A ok 1B " + ("ok" if skill else "no-skill"))
        
        print("\nGenerated " + str(generated) + " prompt pairs")
        print("Total experiments: " + str(len(experiments)) + " (1A: " + str(sum(1 for e in experiments if e[0]=="1A")) + " + 1B: " + str(sum(1 for e in experiments if e[0]=="1B")) + ")")
        
        # Generate runner script
        gen_runner(experiments)
        
    else:
        # Summary mode
        print("=" * 70)
        print("FEW-SHOT DATA PREPARATION - SUMMARY")
        print("=" * 70)
        print("")
        print("V10 experiment pairs: " + str(len(V10_PAIRS)))
        print("")
        print("Data availability:")
        for src, tgt, batch in V10_PAIRS:
            traj = find_baseline_traj(src)
            skill = load_skill(src)
            has_traj = "ok" if traj else "MISSING"
            has_skill = "ok" if skill else "MISSING"
            print("  B" + str(batch) + " " + src + " -> " + tgt + ": traj=" + has_traj + " skill=" + has_skill)
        
        print("")
        traj_ok = sum(1 for s,_,_ in V10_PAIRS if find_baseline_traj(s))
        skill_ok = sum(1 for s,_,_ in V10_PAIRS if load_skill(s))
        print("Trajectory available: " + str(traj_ok) + "/" + str(len(V10_PAIRS)))
        print("Skills available: " + str(skill_ok) + "/" + str(len(V10_PAIRS)))
        print("")
        print("Use --gen-prompts to generate prompt files and runner script.")

def gen_runner(experiments):
    """Generate bash runner script on server1."""
    script_path = "/tmp/run_fewshot_baseline.sh"
    
    lines = []
    lines.append("#!/bin/bash")
    lines.append("# Few-shot baseline runner for V10 experiment pairs")
    lines.append("set -euo pipefail")
    lines.append("")
    lines.append('HARNESS_DIR="/tmp/my_claude_biomnibench_fixed"')
    lines.append('TASKS_DIR="/data/yjh/biomnibench-organized"')
    lines.append('BUN_BIN="/tmp/bun_extract/bun-linux-x64/bun"')
    lines.append('MAX_ROUNDS=5')
    lines.append('TIMEOUT_SECONDS=7200')
    lines.append('CONCURRENCY=2')
    lines.append('BASE_DIR="/data/yjh/skill-transfer-eval"')
    lines.append('FEWSHOT_DIR="${BASE_DIR}/fewshot_transfer"')
    lines.append('PROMPT_DIR="${BASE_DIR}/fewshot_prompts"')
    lines.append('LOG_DIR="${BASE_DIR}/logs/fewshot_$(date +%Y%m%d_%H%M%S)"')
    lines.append('mkdir -p "$LOG_DIR" "$FEWSHOT_DIR"')
    lines.append("")
    lines.append('export ANTHROPIC_API_KEY="${ANTHROPIC_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
    lines.append('export ANTHROPIC_BASE_URL="${ANTHROPIC_BASE_URL:-https://api.gpugeek.com}"')
    lines.append('export ANTHROPIC_MODEL="${ANTHROPIC_MODEL:-Vendor3/DeepSeek-V4-Flash}"')
    lines.append('export QWEN_API_KEY="${QWEN_API_KEY:-00gcclg9l39y9p01000dhjzolag1q2hk00901kh1}"')
    lines.append('export QWEN_BASE_URL="${QWEN_BASE_URL:-https://api.gpugeek.com/v1}"')
    lines.append('export QWEN_MODEL="${QWEN_MODEL:-Vendor2/Gemini-3.1-pro}"')
    lines.append("")
    lines.append('echo "=============================================="')
    lines.append('echo "Few-shot Baseline Runner"')
    lines.append('echo "Concurrency: $CONCURRENCY"')
    lines.append('echo "Log dir: $LOG_DIR"')
    lines.append('echo "=============================================="')
    lines.append("")
    lines.append('START_TIME=$(date +%s)')
    lines.append('TOTAL=' + str(len(experiments)))
    lines.append('COMPLETED=0')
    lines.append('FAILED=0')
    lines.append("")
    lines.append('run_experiment() {')
    lines.append('  local mode="$1"')
    lines.append('  local source="$2"')
    lines.append('  local target="$3"')
    lines.append('  local prefix="$4"')
    lines.append('  local prompt_file="$5"')
    lines.append('  local ts="${prefix}_fewshot_${mode}"')
    lines.append('  local log_file="${LOG_DIR}/${prefix}_${mode}.log"')
    lines.append('  echo "[$(date +%H:%M:%S)] Starting: ${prefix} ${mode}"')
    lines.append('  cd "$HARNESS_DIR"')
    lines.append('  $BUN_BIN src/harness/evaluation/cli.ts \\')
    lines.append('    --task "$target" \\')
    lines.append('    --tasks-dir "$TASKS_DIR" \\')
    lines.append('    --runs-dir "$FEWSHOT_DIR" \\')
    lines.append('    --max-rounds "$MAX_ROUNDS" \\')
    lines.append('    --timeout-seconds "$TIMEOUT_SECONDS" \\')
    lines.append('    --concurrency 1 \\')
    lines.append('    --temperature 1 \\')
    lines.append('    --thinking disabled \\')
    lines.append('    --timestamp "$ts" \\')
    lines.append('    --system-prompt "$prompt_file" \\')
    lines.append('    --quiet \\')
    lines.append('    > "$log_file" 2>&1')
    lines.append('  local exit_code=$?')
    lines.append('  echo "[$(date +%H:%M:%S)] Done: ${prefix} ${mode} (exit=$exit_code)"')
    lines.append('  tail -5 "$log_file" 2>/dev/null')
    lines.append('  return $exit_code')
    lines.append('}')
    lines.append("")
    
    # Batch them: 2 at a time, ensure no same target in same batch
    batches = []
    current_batch = []
    current_targets = set()
    for mode, src, tgt, prefix, prompt_file in experiments:
        if tgt in current_targets and len(current_batch) >= 2:
            batches.append(list(current_batch))
            current_batch = []
            current_targets = set()
        # If already 2 in batch, start new batch
        if len(current_batch) >= 2:
            batches.append(list(current_batch))
            current_batch = []
            current_targets = set()
        current_batch.append((mode, src, tgt, prefix, prompt_file))
        current_targets.add(tgt)
    if current_batch:
        batches.append(list(current_batch))
    
    lines.append('# === Experiments: ' + str(len(experiments)) + ' total, ' + str(len(batches)) + ' batches ===')
    lines.append('')
    
    for bidx, batch in enumerate(batches):
        lines.append('# === Batch ' + str(bidx+1) + '/' + str(len(batches)) + ' ===')
        lines.append('PIDS=()')
        for mode, src, tgt, prefix, prompt_file in batch:
            lines.append('run_experiment "' + mode + '" "' + src + '" "' + tgt + '" "' + prefix + '" "' + prompt_file + '" &')
            lines.append('PIDS+=($!)')
        lines.append('')
        lines.append('  for pid in "${PIDS[@]}"; do')
        lines.append('    wait "$pid" 2>/dev/null && COMPLETED=$((COMPLETED + 1)) || FAILED=$((FAILED + 1))')
        lines.append('  done')
        lines.append('  echo "[$(date +%H:%M:%S)] Batch ' + str(bidx+1) + '/' + str(len(batches)) + ' done. $COMPLETED/$TOTAL, Failed: $FAILED"')
        lines.append('')
    
    lines.append('END_TIME=$(date +%s)')
    lines.append('echo ""')
    lines.append('echo "=============================================="')
    lines.append('echo "All experiments complete"')
    lines.append('echo "Total: $TOTAL | Completed: $COMPLETED | Failed: $FAILED"')
    lines.append('echo "Elapsed: $(( (END_TIME - START_TIME) / 60 ))m"')
    lines.append('echo "=============================================="')
    
    script = '\n'.join(lines)
    
    # Write locally first, then copy to server
    local_path = r'c:\Users\30670\Desktop\Autoskill\run_fewshot_baseline.sh'
    with open(local_path, 'w', newline='\n') as f:
        f.write(script)
    print("Runner script written: " + local_path)
    print("Copy to server and run: scp run_fewshot_baseline.sh server1:/tmp/ && ssh server1 'bash /tmp/run_fewshot_baseline.sh'")

if __name__ == "__main__":
    main()