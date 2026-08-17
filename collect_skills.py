#!/usr/bin/env python3
"""Collect skill files and baseline data for deep analysis."""
import json, os

os.chdir("/data/yjh/skill-transfer-eval")

# Skill files for source tasks
source_tasks = ["da-12-4", "da-17-5", "da-19-4", "da-4-7", "da-14-8", "da-13-6", "da-10-1", "da-18-5", "da-10-3", "da-11-1", "da-26-4", "da-5-1", "da-25-1", "da-9-1"]

for src in source_tasks:
    skill_path = "generalized_skills_pruned/" + src + "/SKILL.md"
    if os.path.exists(skill_path):
        with open(skill_path) as f:
            content = f.read()
        print("SKILLFILE|" + src + "|len=" + str(len(content)))
        print(content)
        print("ENDSKILLFILE")
    else:
        print("SKILLFILE|" + src + "|NOT_FOUND")

# Baseline data from all_results.json
print("BASELINE_DATA")
with open("summary/all_results.json") as f:
    data = json.load(f)
# Only show the tasks that are targets in our 37 pairs
targets = ["da-17-1", "da-19-6", "da-4-1", "da-14-1", "da-13-5", "da-6-2", "da-18-7", "da-19-3", "da-10-1", "da-6-5", "da-13-1", "da-26-2", "da-18-1", "da-5-3", "da-13-3", "da-1-3", "da-14-3", "da-19-1", "da-9-7", "da-18-7", "da-12-2", "da-1-4", "da-15-8", "da-15-7", "da-15-1", "da-17-3"]
for tid in targets:
    if tid in data:
        entry = data[tid]
        base = entry.get("baseline", [])
        oracle = entry.get("oracle", [])
        print("TASK|" + tid + "|baseline_reward=" + str([b.get("reward") for b in base]) + "|oracle_reward=" + str([o.get("reward") for o in oracle]))
        if base:
            print("  baseline_detail:", json.dumps(base[0])[:500])
        if oracle:
            print("  oracle_detail:", json.dumps(oracle[0])[:500])
    else:
        print("TASK|" + tid + "|NOT_FOUND")