"""Build initial skill for SkillOpt by concatenating 17 source tasks' generalized-transfer skills."""
import os
import sys

SKILL_DIR = "/data/yjh/skill-transfer-eval/skills"
SOURCE_TASKS = [
    "da-26-2", "da-20-3", "da-13-5", "da-14-3", "da-5-1",
    "da-19-4", "da-13-3", "da-18-5", "da-19-3", "da-4-6",
    "da-18-1", "da-13-1", "da-15-1", "da-8-1", "da-8-2",
    "da-19-1", "da-6-2"
]
OUTPUT = "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/skills/initial.md"

sections = []
sections.append("# BioMNIBench Agent Skill: Combined from 17 Source Tasks\n\n")
sections.append("This skill is a concatenation of generalized-transfer skills from all 17 source tasks. ")
sections.append("SkillOpt will optimize it through RL training.\n\n")
sections.append("---\n\n")

for task_id in SOURCE_TASKS:
    skill_path = os.path.join(SKILL_DIR, task_id, "skills", "generalized-transfer", "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path) as f:
            content = f.read()
        sections.append(f"## Source Task: {task_id}\n\n")
        sections.append(content)
        sections.append("\n\n---\n\n")
        print(f"  Added: {task_id} ({len(content)} bytes)")
    else:
        print(f"  MISSING: {task_id}")

combined = "".join(sections)
with open(OUTPUT, "w") as f:
    f.write(combined)
print(f"\nWritten {len(combined)} bytes to {OUTPUT}")