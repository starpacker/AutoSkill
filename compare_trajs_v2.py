#!/usr/bin/env python3
"""Compare baseline vs transfer trajectories - detailed analysis.
Outputs JSON for easier processing.
"""
import json, os, sys, glob

BASEDIR = "/data/yjh/skill-transfer-eval/baseline"
TRANSDIR = "/data/yjh/skill-transfer-eval/transfer_pruned"

baseline_dirs = {}
for d in os.listdir(BASEDIR):
    parts = d.split("_")
    if len(parts) >= 2:
        tid = parts[0]
        if tid not in baseline_dirs:
            baseline_dirs[tid] = d

def parse_traj(filepath):
    info = {
        "rounds": set(), "tool_calls": [], "tool_names": {},
        "errors": [], "bash_cmds": [], "file_reads": [], "file_writes": [],
        "skill_calls": 0
    }
    try:
        with open(filepath) as f:
            for line in f:
                d = json.loads(line)
                k = d.get("kind", "")
                r = d.get("round", 0)
                info["rounds"].add(r)
                if k == "tool_call":
                    tool = d.get("tool", "")
                    inp = d.get("input", {})
                    info["tool_calls"].append({"round": r, "tool": tool, "input": inp})
                    info["tool_names"][tool] = info["tool_names"].get(tool, 0) + 1
                    if tool == "Skill":
                        info["skill_calls"] += 1
                    elif tool == "Bash":
                        cmd = str(inp.get("command", ""))[:300]
                        info["bash_cmds"].append(cmd)
                    elif tool == "Read":
                        info["file_reads"].append(inp.get("file_path", ""))
                    elif tool in ("Write", "edit"):
                        info["file_writes"].append(inp.get("file_path", ""))
                elif k == "tool_result" and not d.get("ok", True):
                    info["errors"].append({"round": r, "msg": str(d.get("text", ""))[:300]})
    except Exception as e:
        info["parse_error"] = str(e)
    info["num_rounds"] = len(info["rounds"])
    info["num_tool_calls"] = len(info["tool_calls"])
    return info

def get_transfer_dir(source, target):
    candidates = glob.glob(os.path.join(TRANSDIR, f"{target}_pruned_transfer_{source}_to_{target}*"))
    return candidates[0] if candidates else None

# Define pairs
pairs = [
    ("da-19-4", "da-19-6", 0.69, 1.00, "SkillHelped"),
    ("da-4-7", "da-4-1", 0.61, 0.86, "SkillHelped"),
    ("da-14-8", "da-14-1", 0.80, 1.00, "SkillHelped"),
    ("da-13-6", "da-13-5", 0.70, 0.90, "SkillHelped"),
    ("da-10-1", "da-6-2", 0.72, 0.92, "SkillHelped"),
    ("da-19-4", "da-19-3", 0.75, 0.90, "SkillHelped"),
    ("da-18-5", "da-18-7", 0.85, 0.95, "SkillHelped"),
    ("da-10-3", "da-10-1", 0.94, 0.64, "SkillHarmed"),
    ("da-11-1", "da-6-5", 0.92, 0.67, "SkillHarmed"),
    ("da-26-4", "da-26-2", 0.87, 0.67, "SkillHarmed"),
    ("da-18-5", "da-18-1", 0.90, 0.72, "SkillHarmed"),
    ("da-13-6", "da-13-1", 0.95, 0.69, "SkillHarmed"),
    ("da-9-1", "da-9-7", 1.00, 0.93, "SkillHarmed"),
    ("da-19-4", "da-19-1", 0.72, 0.63, "SkillHarmed"),
    ("da-13-6", "da-13-3", 1.00, 0.87, "SkillHarmed"),
    ("da-17-5", "da-14-3", 0.85, 0.71, "SkillHarmed"),
    ("da-25-1", "da-18-7", 0.85, 0.70, "SkillHarmed"),
    ("da-5-1", "da-26-2", 0.87, 0.69, "SkillHarmed"),
    ("da-10-1", "da-6-5", 0.92, 0.67, "SkillHarmed"),
]

output = {}
for src, tgt, base_score, trans_score, verdict in pairs:
    pair_key = f"{src}->{tgt}"
    delta = round(trans_score - base_score, 2)
    entry = {"delta": delta, "verdict": verdict, "baseline": {}, "transfer": {}}
    
    # Baseline
    bdir = baseline_dirs.get(tgt)
    if bdir:
        bpath = os.path.join(BASEDIR, bdir, "logs", "trajectory.clean.jsonl")
        b_judge = os.path.join(BASEDIR, bdir, "judge_gemini", "judge_result_round_1.json")
        if os.path.exists(bpath):
            bi = parse_traj(bpath)
            entry["baseline"] = {
                "rounds": bi["num_rounds"],
                "tool_calls": bi["num_tool_calls"],
                "tools": bi["tool_names"],
                "errors": len(bi["errors"]),
                "read_files": len(set(bi["file_reads"])),
                "write_files": len(set(bi["file_writes"])),
                "bash_cmds": len(bi["bash_cmds"]),
            }
        if os.path.exists(b_judge):
            with open(b_judge) as f:
                j = json.load(f)
            crit = {}
            if isinstance(j, dict):
                for k, v in j.items():
                    if isinstance(v, (int, float)):
                        crit[k] = v
                    elif isinstance(v, list):
                        for item in v:
                            if isinstance(item, dict):
                                n = item.get("name", item.get("criterion", "?"))
                                lv = item.get("level", "?")
                                pt = item.get("points", item.get("score", "?"))
                                crit[n] = {"level": lv, "points": pt}
            entry["baseline"]["judge"] = crit
    
    # Transfer
    tdir = get_transfer_dir(src, tgt)
    if tdir:
        tpath = os.path.join(tdir, "logs", "trajectory.clean.jsonl")
        t_judge = os.path.join(tdir, "logs", "run_summary.json")
        if os.path.exists(tpath):
            ti = parse_traj(tpath)
            entry["transfer"] = {
                "rounds": ti["num_rounds"],
                "tool_calls": ti["num_tool_calls"],
                "tools": ti["tool_names"],
                "errors": len(ti["errors"]),
                "read_files": len(set(ti["file_reads"])),
                "write_files": len(set(ti["file_writes"])),
                "bash_cmds": len(ti["bash_cmds"]),
                "skill_calls": ti["skill_calls"],
            }
        if os.path.exists(t_judge):
            with open(t_judge) as f:
                j = json.load(f)
            crit = {}
            if isinstance(j, dict):
                fr = j.get("final_result", j)
                if isinstance(fr, dict):
                    for k, v in fr.items():
                        if isinstance(v, (int, float)):
                            crit[k] = v
                        elif isinstance(v, dict):
                            for sk, sv in v.items():
                                if isinstance(sv, dict):
                                    crit[f"{k}.{sk}"] = {sk2: sv2 for sk2, sv2 in sv.items() if isinstance(sv2, (str, int, float))}
            entry["transfer"]["judge"] = crit
    
    output[pair_key] = entry

print(json.dumps(output, indent=2, ensure_ascii=False))