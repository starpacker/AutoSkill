#!/usr/bin/env python3
import glob
import json
import os
import re
from pathlib import Path

base = Path("/data/yjh/skill-transfer-eval")
files = sorted(base.glob("generalized/.judge_private/*generalized-cross-gemini*/judge_result_round_*.json"))
latest = {}
for path in files:
    match = re.search(r"round_(\d+)", path.name)
    round_no = int(match.group(1)) if match else -1
    latest[path.parent.name] = (round_no, path)

print("judge_files", len(files))
print("runs_with_judge", len(latest))
for run_id, (round_no, path) in sorted(latest.items()):
    obj = json.loads(path.read_text())
    score = obj.get("total_score", obj.get("score"))
    model = obj.get("model", obj.get("judge_model", ""))
    print(f"{run_id}\tround={round_no}\tscore={score}\tmodel={model}")

print("\nrun_dirs")
for path in sorted(base.glob("generalized/*generalized-cross-gemini*")):
    print(path.name)

print("\nsummary_files")
for path in sorted(base.glob("logs/cross_gemini_12_summary_*.json"), key=os.path.getmtime, reverse=True)[:5]:
    print(path)
