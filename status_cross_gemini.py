#!/usr/bin/env python3
import glob
import json
import os
import re
from pathlib import Path

base = Path("/data/yjh/skill-transfer-eval")
run_dirs = sorted(base.glob("generalized/*generalized-cross-gemini*"))
judge_dirs = {p.name: p for p in (base / "generalized/.judge_private").glob("*generalized-cross-gemini*")}

print("run_count", len(run_dirs))
for run in run_dirs:
    latest_mtime = 0.0
    latest_file = ""
    for root, _, files in os.walk(run):
        for name in files:
            path = Path(root) / name
            try:
                mtime = path.stat().st_mtime
            except FileNotFoundError:
                continue
            if mtime > latest_mtime:
                latest_mtime = mtime
                latest_file = str(path.relative_to(base))

    judge_files = sorted(
        glob.glob(str(judge_dirs.get(run.name, Path("/missing")) / "judge_result_round_*.json")),
        key=lambda p: int(re.search(r"round_(\d+)", os.path.basename(p)).group(1)),
    )
    if judge_files:
        obj = json.loads(Path(judge_files[-1]).read_text())
        judge = f"round={len(judge_files)} score={obj.get('total_score', obj.get('score'))} model={obj.get('model', '')}"
    else:
        judge = "no_judge"

    summary = run / "logs/run_summary.json"
    if summary.exists():
        try:
            s = json.loads(summary.read_text())
            run_status = s.get("status", s.get("final_status", "summary"))
        except Exception as exc:
            run_status = f"summary_parse_error={exc}"
    else:
        run_status = "no_summary"

    latest_text = "none"
    if latest_file:
        latest_text = f"{Path(latest_file).name} age_sec={int(__import__('time').time() - latest_mtime)}"
    print(f"{run.name}\t{run_status}\t{judge}\tlatest={latest_text}")
