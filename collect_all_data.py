#!/usr/bin/env python3
"""Comprehensive data collection for all 37 transfer pairs.
Collects:
1. Transfer results (scores, skill_application status, judge details)
2. Baseline real scores (checking judge_gemini for baseline=0 cases)
3. Skill file summary
"""
import json, os, glob

BASEDIR = "/data/yjh/skill-transfer-eval"
TRANSDIR = f"{BASEDIR}/transfer_pruned"
SKILLDIR = f"{BASEDIR}/generalized_skills_pruned"
TRANSRES = f"{BASEDIR}/summary_pruned/transfer_pruned_results.json"
ALLRES = f"{BASEDIR}/summary/all_results.json"
BASELINEDIR = f"{BASEDIR}/baseline"

# Load transfer results
trans_data = json.load(open(TRANSRES))
pairs = trans_data.get("pairs", trans_data)

results = []
for p in pairs:
    src = p["source"]
    tgt = p["target"]
    trans_score = p.get("pruned_transfer", [None])[0]
    
    pair_key = f"{tgt}_pruned_transfer_{src}_to_{tgt}"
    pair_dir = f"{TRANSDIR}/{pair_key}"
    
    entry = {
        "source": src,
        "target": tgt,
        "transfer_score": trans_score,
        "skill_app_status": "unknown",
        "skill_app_reason": "",
        "transfer_judge_score": None,
        "transfer_judge_criteria": {},
        "transfer_judge_overall": "",
        "transfer_model": "",
        "transfer_status": "unknown",
        "transfer_rounds": 0,
        "baseline_recorded": None,
        "baseline_real_score": None,
        "baseline_real_criteria": {},
        "baseline_overall": "",
        "baseline_status": "",
        "baseline_rounds": 0,
        "baseline_model": "",
        "skill_ops": [],
        "skill_desc": "",
    }
    
    # 1. Read transfer run_summary
    summary_file = f"{pair_dir}/logs/run_summary.json"
    if os.path.exists(summary_file):
        try:
            s = json.load(open(summary_file))
            entry["transfer_status"] = s.get("status", "unknown")
            entry["transfer_rounds"] = s.get("rounds", 0)
            fr = s.get("final_result", {})
            if fr:
                entry["transfer_judge_score"] = fr.get("total_score")
                entry["transfer_judge_criteria"] = {k: {"level": v.get("level"), "points": v.get("points")} for k, v in fr.get("criteria", {}).items()}
                entry["transfer_judge_overall"] = fr.get("overall_reasoning", "")[:200]
            entry["transfer_model"] = s.get("run_metadata", {}).get("model", "")
        except:
            pass
    
    # 2. Read skill_application.json
    for sa_path in [
        f"{pair_dir}/outputs/skill_application.json",
        f"{pair_dir}/workspace/skill_application.json",
    ]:
        if os.path.exists(sa_path):
            try:
                sa = json.load(open(sa_path))
                skills = sa.get("skills", [])
                if skills:
                    entry["skill_app_status"] = skills[0].get("status", "unknown")
                    entry["skill_app_reason"] = skills[0].get("reason", "")[:300]
            except:
                pass
    
    # 3. Read skill file
    skill_file = f"{SKILLDIR}/{src}/SKILL.md"
    if os.path.exists(skill_file):
        content = open(skill_file).read()
        # Count oracle operations
        ops = [line for line in content.split('\n') if 'ORACLE_OP_START' in line]
        entry["skill_ops"] = [o.split('op_')[-1].replace(' -->', '') for o in ops]
        # Get first line of description
        for line in content.split('\n'):
            line = line.strip()
            if line.startswith('#') and 'Skill' in line:
                entry["skill_desc"] = line.replace('#', '').strip()
                break
    
    # 4. Get baseline data from all_results.json
    all_data = json.load(open(ALLRES))
    tasks_list = all_data.get("tasks", all_data)
    if isinstance(tasks_list, list):
        task_dict = {t["task_id"]: t for t in tasks_list}
    else:
        task_dict = tasks_list
    
    if tgt in task_dict:
        baseline_runs = task_dict[tgt].get("baseline", [])
        if baseline_runs:
            br = baseline_runs[0]
            entry["baseline_recorded"] = br.get("reward")
            entry["baseline_status"] = br.get("status", "")
            entry["baseline_rounds"] = br.get("rounds", 0)
    
    # 5. For baseline=0 cases, check actual judge result
    if entry["baseline_recorded"] == 0.0 or entry["baseline_recorded"] is None:
        # Find baseline run directory
        base_runs = glob.glob(f"{BASELINEDIR}/{tgt}_*_baseline_*")
        for br_dir in sorted(base_runs):
            judge_file = f"{br_dir}/judge_gemini/judge_result_round_1.json"
            if os.path.exists(judge_file):
                try:
                    jd = json.load(open(judge_file))
                    entry["baseline_real_score"] = jd.get("total_score")
                    entry["baseline_real_criteria"] = {k: {"level": v.get("level"), "points": v.get("points")} for k, v in jd.get("criteria", {}).items()}
                    entry["baseline_overall"] = jd.get("overall_reasoning", "")[:200]
                    break
                except:
                    pass
    
    results.append(entry)

# Print summary table
print("=" * 200)
print(f"{'#':>3} | {'Source':>10} -> {'Target':>10} | {'Base_rec':>8} | {'Base_real':>9} | {'Trans':>6} | {'Δ_rec':>8} | {'Δ_real':>8} | {'SkillStat':>20} | {'Rounds':>6} | {'Skill Ops':>30}")
print("=" * 200)

for i, e in enumerate(results):
    base_rec = e["baseline_recorded"]
    base_real = e["baseline_real_score"]
    trans = e["transfer_score"]
    
    delta_rec = (trans - base_rec) if (base_rec is not None and trans is not None) else None
    delta_real = (trans - base_real) if (base_real is not None and trans is not None) else None
    
    base_rec_str = f"{base_rec:.2f}" if base_rec is not None else "N/A"
    base_real_str = f"{base_real}" if base_real is not None else "N/A"
    trans_str = f"{trans:.2f}" if trans is not None else "N/A"
    delta_rec_str = f"{delta_rec:+.2f}" if delta_rec is not None else "N/A"
    delta_real_str = f"{delta_real:+.2f}" if delta_real is not None else "N/A"
    
    # Determine if baseline is artifact
    if base_rec == 0.0 and base_real is not None and base_real > 0:
        base_rec_str = f"{base_rec:.2f}⚠️"
    
    skill_ops_str = ", ".join(e["skill_ops"][:3]) if e["skill_ops"] else "N/A"
    
    print(f"{i+1:>3} | {e['source']:>10} -> {e['target']:>10} | {base_rec_str:>8} | {base_real_str:>9} | {trans_str:>6} | {delta_rec_str:>8} | {delta_real_str:>8} | {e['skill_app_status']:>20} | {e['transfer_rounds']:>6} | {skill_ops_str:>30}")

print("=" * 200)
print("\n\n=== DETAILED CASES ===\n")

# Detailed output for each case
for e in results:
    print(f"=== {e['source']} -> {e['target']} ===")
    print(f"  Transfer: score={e['transfer_score']}, status={e['transfer_status']}, rounds={e['transfer_rounds']}, model={e['transfer_model']}")
    print(f"  Baseline: recorded={e['baseline_recorded']}, real={e['baseline_real_score']}, status={e['baseline_status']}, rounds={e['baseline_rounds']}")
    print(f"  Skill app: status={e['skill_app_status']}")
    if e['skill_app_reason']:
        print(f"  Skill reason: {e['skill_app_reason'][:200]}")
    print(f"  Skill ops ({len(e['skill_ops'])}): {e['skill_ops']}")
    if e['skill_desc']:
        print(f"  Skill desc: {e['skill_desc']}")
    if e['baseline_real_criteria']:
        print(f"  Baseline real criteria: {json.dumps(e['baseline_real_criteria'])}")
    if e['baseline_overall']:
        print(f"  Baseline overall: {e['baseline_overall'][:200]}")
    if e['transfer_judge_criteria']:
        print(f"  Transfer criteria: {json.dumps(e['transfer_judge_criteria'])}")
    if e['transfer_judge_overall']:
        print(f"  Transfer overall: {e['transfer_judge_overall'][:200]}")
    print()