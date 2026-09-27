#!/usr/bin/env python3
"""
Baseline3 for R→R Transfer: Use GT code from PASS tasks as few-shot for 6 FAIL tasks.
This is adapted for the R biodsbench tasks (not the original da-* tasks).
"""
import json, os, sys, time, subprocess as sp

# === CONFIG ===
R_JSONL = os.environ.get("R_JSONL",
    "/data/yjh/BioDSA/benchmarks/BioDSBench-R/dataset/R_tasks_with_class.jsonl")
R_TASKS_DIR = os.environ.get("R_TASKS_DIR",
    "/data/yjh/my_claude_biomnibench/tasks/biodsbench_r")
HARNESS = os.environ.get("HARNESS_DIR", "/data/yjh/my_claude_biomnibench")
BUN = os.path.expanduser("~/.bun/bin/bun")
TRANSFER_DIR = os.environ.get("SKILL_TRANSFER_DIR", "/data/yjh/skill-transfer-eval")
RUNS_DIR = TRANSFER_DIR + "/baseline3_runs"
LOG_DIR_BASE = TRANSFER_DIR + "/logs"
API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("API_KEY", "")
BASE_URL = os.environ.get("ANTHROPIC_BASE_URL", "https://api.gpugeek.com")
MODEL = os.environ.get("ANTHROPIC_MODEL", "Vendor3/DeepSeek-V4-Flash")
QWEN_API_KEY = os.environ.get("QWEN_API_KEY", API_KEY)
QWEN_BASE_URL = os.environ.get("QWEN_BASE_URL", "https://api.gpugeek.com/v1")
QWEN_MODEL = os.environ.get("QWEN_MODEL", "Vendor2/Gemini-3-flash")
TIMEOUT = int(os.environ.get("EVAL_TIMEOUT", "2400"))

EXPERIMENTS = [
    # (target_fail_task, source_pass_task)
    ("biodsbench_23502430_q5", "biodsbench_32211396_q2"),  # deg_filtering <- deg_filtering
    ("biodsbench_33176622_q3", "biodsbench_32211396_q0"),  # data_merge <- data_merge
    ("biodsbench_33176622_q4", "biodsbench_32211396_q1"),  # data_merge <- data_merge
    ("biodsbench_33746977_q6", "biodsbench_32211396_q6"),  # go_enrichment <- go_enrichment
    ("biodsbench_33746977_q7", "biodsbench_32211396_q6"),  # go_enrichment <- go_enrichment
    ("biodsbench_33761933_q8", "biodsbench_32211396_q6"),  # gsea_analysis <- go_enrichment
]

def load_r_jsonl():
    """Load R JSONL, return:
       - refs: dict uid -> {code, lang}
       - entries: raw entries
       - task_to_uid: (empty, mapping built in find_uid_for_task fallback)
    """
    if not API_KEY:
        raise RuntimeError("Set ANTHROPIC_API_KEY or API_KEY before running evaluations")
    with open(R_JSONL) as f:
        entries = [json.loads(line) for line in f]

    # Build mapping: uid -> {code, lang}
    refs = {}
    for e in entries:
        uid = e.get("unique_question_ids", "")
        code = e.get("reference_answer", "") or ""
        lang = e.get("language", "r").lower()
        if code.strip():
            refs[uid] = {"code": code, "language": lang}

    return refs, entries, {}

def find_uid_for_task(entries, task_id, task_to_uid=None):
    """Find which uid in JSONL corresponds to a given biodsbench task_id."""
    # Try pre-built mapping first
    if task_to_uid and task_id in task_to_uid:
        return task_to_uid[task_id]
    # Fallback: extract study_id and qnum from task_id
    # task_id = "biodsbench_STUDYID_qQNUM" -> uid = "STUDYID_QNUM"
    if task_id.startswith("biodsbench_"):
        rest = task_id[len("biodsbench_"):]  # "33176622_q3"
        parts = rest.split("_q")
        if len(parts) == 2:
            study_id, qnum = parts
            return "%s_%s" % (study_id, qnum)
    return None

def get_task_readme(task_id):
    """Get task description from README."""
    readme_path = os.path.join(R_TASKS_DIR, task_id, "README.md")
    if os.path.exists(readme_path):
        with open(readme_path) as f:
            return f.read()
    return "(No README available)"

def format_baseline3_prompt(target_task, source_task, gt_code, gt_lang, source_uid):
    """Format baseline3 prompt with GT code as few-shot."""
    # Get source task description
    task_desc = get_task_readme(source_task)

    lines = []
    lines.append("# Reference: Expert Solution for a Similar Task\n")
    lines.append("Below is a similar bioinformatics task and its expert-written solution (ground truth). ")
    lines.append("Study this carefully — it demonstrates the correct analytical approach in R. ")
    lines.append("Adapt it to solve your task.\n")
    lines.append(f"**Source task (GT)**: {source_task} (uid: {source_uid})")
    lines.append(f"**Target task**: {target_task}\n")
    lines.append("## Source Task Description\n")
    lines.append(task_desc.strip())
    lines.append(f"\n## Expert Solution Code (R)\n")
    lines.append("```r")
    lines.append(gt_code.strip())
    lines.append("```\n")
    lines.append("## Instructions\n")
    lines.append("1. Understand the task above and the expert's R solution")
    lines.append("2. Adapt this approach to solve YOUR target task")
    lines.append("3. The target task may have different data, columns, or requirements")
    lines.append("4. Write your solution in R and save to `outputs/submission.r`")
    return "\n".join(lines)


def main():
    print("=" * 70)
    print("  Baseline3: GT Code Few-Shot for 6 R→R Transfer Tasks")
    print("  (Adapted from baseline3.py for biodsbench R tasks)")
    print("=" * 70)

    # Step 1: Load R JSONL
    print("\n[1] Loading R JSONL references...")
    refs, entries, task_to_uid = load_r_jsonl()
    print(f"  Total entries: {len(entries)}")
    print(f"  Entries with reference_answer: {len(refs)}")
    if entries:
        print(f"  Sample uid: {entries[0].get('unique_question_ids','?')}")

    # Step 2: Find UIDs for our tasks
    print("\n[2] Mapping task IDs to JSONL uids...")
    task_uids = {}
    for src, tgt in EXPERIMENTS:
        for task_id in [src, tgt]:
            if task_id not in task_uids:
                uid = find_uid_for_task(entries, task_id, task_to_uid)
                task_uids[task_id] = uid
                status = "FOUND" if uid else "NOT FOUND"
                print(f"  {task_id} -> {uid} [{status}]")

    # Step 3: Build experiment list
    print("\n[3] Checking reference availability...")
    ready_experiments = []
    for target, source in EXPERIMENTS:
        src_uid = task_uids.get(source)
        if not src_uid:
            print(f"  SKIP {source} -> {target}: source UID not found")
            continue
        ref = refs.get(src_uid)
        if not ref:
            print(f"  SKIP {source} -> {target}: no reference_answer for {src_uid}")
            continue
        ready_experiments.append((target, source, src_uid, ref))
        print(f"  READY {source} -> {target}: {len(ref['code'])} chars GT code (lang={ref['language']})")

    if not ready_experiments:
        print("\nNO experiments ready! Check the JSONL path and task IDs.")
        sys.exit(1)

    # Step 4: Run experiments sequentially (with timeout)
    print(f"\n[4] Running {len(ready_experiments)} baseline3 experiments...")
    timestamp = time.strftime("%Y%m%d_%H%M%S")
    log_dir = LOG_DIR_BASE + "/baseline3_" + timestamp
    os.makedirs(log_dir, exist_ok=True)
    os.makedirs(RUNS_DIR, exist_ok=True)

    for i, (target, source, src_uid, ref) in enumerate(ready_experiments):
        print(f"\n{'='*60}")
        print(f"  [{i+1}/{len(ready_experiments)}] {target} <- {source}")
        print(f"{'='*60}")

        ts = f"bl3_{target}_from_{source}_{timestamp}"

        # Create prompt
        prompt = format_baseline3_prompt(target, source, ref["code"], ref["language"], src_uid)
        prompt_dir = TRANSFER_DIR + f"/p_bl3_{timestamp}"
        os.makedirs(prompt_dir, exist_ok=True)
        prompt_path = os.path.join(prompt_dir, f"{ts}_prompt.md")
        with open(prompt_path, "w") as f:
            f.write(prompt)

        # Run
        env_vars = (f"ANTHROPIC_API_KEY={API_KEY} ANTHROPIC_BASE_URL={BASE_URL} "
                    f"ANTHROPIC_MODEL={MODEL} "
                    f"QWEN_API_KEY={QWEN_API_KEY} QWEN_BASE_URL={QWEN_BASE_URL} "
                    f"QWEN_MODEL={QWEN_MODEL}")
        cmd = f"cd {HARNESS} && {env_vars} {BUN}"
        cmd += " src/harness/evaluation/cli.ts"
        cmd += f" --task {target}"
        cmd += f" --tasks-dir {R_TASKS_DIR}"
        cmd += f" --runs-dir {RUNS_DIR}"
        cmd += f" --max-rounds 5 --timeout-seconds {TIMEOUT} --concurrency 1 --temperature 1.0"
        cmd += " --thinking disabled"
        cmd += f" --timestamp {ts} --quiet"
        cmd += f" --system-prompt {prompt_path}"

        sys.stdout.flush()
        start = time.time()
        try:
            result = sp.run(cmd, shell=True, capture_output=True, text=True, timeout=TIMEOUT + 60)
            elapsed = time.time() - start
            print(f"  Done in {elapsed:.1f}s (rc={result.returncode})")
        except sp.TimeoutExpired:
            elapsed = time.time() - start
            print(f"  TIMEOUT after {elapsed:.1f}s")
            result = None
        sys.stdout.flush()

        # Save log
        log_file = os.path.join(log_dir, f"{i+1:03d}_{target}_from_{source}.log")
        with open(log_file, "w") as f:
            f.write(f"Target: {target}\nSource: {source}\nSourceUID: {src_uid}\nTimestamp: {ts}\n")
            f.write(f"Elapsed: {elapsed:.1f}s\nTimeout: {TIMEOUT}s\n\n")
            if result:
                f.write(f"Return code: {result.returncode}\n\nSTDOUT:\n{result.stdout}\n\n")
                f.write(f"STDERR:\n{result.stderr[:2000]}\n")
            else:
                f.write("Status: TIMEOUT\n")
        print(f"  Log: {log_file}")

    # Summary
    print(f"\n{'='*70}")
    print(f"  Baseline3 batch complete! {len(ready_experiments)} experiments.")
    print(f"  Log dir: {log_dir}")
    print(f"  Runs dir: {RUNS_DIR}")
    print(f"{'='*70}")

if __name__ == "__main__":
    main()