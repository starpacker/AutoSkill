"""Fix timeout, build initial skill from 17 source tasks, and launch skill-opt."""
import subprocess
import sys

SSH = [
    "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
    "-o", "StrictHostKeyChecking=no", "server1"
]

def run(cmd_str):
    full = SSH + [cmd_str]
    print(f"Running: {cmd_str[:120]}...")
    r = subprocess.run(full, capture_output=True, text=True, timeout=60)
    if r.returncode != 0:
        print(f"STDERR: {r.stderr[:500]}")
    print(f"STDOUT: {r.stdout[:500]}")
    return r.stdout, r.returncode

# Step 1: Fix exec_timeout in biomnibench config
print("=" * 60)
print("STEP 1: Fix exec_timeout in biomnibench config")
print("=" * 60)

config_fix = """  exec_timeout: 300
  max_completion_tokens: 16384
  limit: 0
"""

# Check current config
out, _ = run("grep -n 'exec_timeout' /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml")
if "exec_timeout" not in out:
    # Add exec_timeout after workers line
    run("""sed -i 's/    workers: 2/    workers: 2\\n    exec_timeout: 300/' /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml""")
    print("Added exec_timeout: 300 to config")
else:
    # Update existing
    run("""sed -i 's/exec_timeout:.*/exec_timeout: 300/' /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml""")
    print("Updated exec_timeout to 300")

# Verify
out, _ = run("grep -n 'exec_timeout' /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml")
print(f"Config after fix: {out[:200]}")

# Step 2: Build initial skill from 17 source tasks' generalized-transfer skills
print("=" * 60)
print("STEP 2: Build initial skill from 17 source tasks")
print("=" * 60)

# The 17 source tasks (unique from V10 pairs)
SOURCE_TASKS = [
    "da-26-2", "da-20-3", "da-13-5", "da-14-3", "da-5-1",
    "da-19-4", "da-13-3", "da-18-5", "da-19-3", "da-4-6",
    "da-18-1", "da-13-1", "da-15-1", "da-8-1", "da-8-2",
    "da-19-1", "da-6-2"
]

# Build the concatenated skill via Python on server
build_script = f"""
import os

SKILL_DIR = "/data/yjh/skill-transfer-eval/skills"
SOURCE_TASKS = {SOURCE_TASKS}
OUTPUT = "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/skills/initial.md"

sections = []
sections.append("# BioMNIBench Agent Skill: Combined from 17 Source Tasks\\n\\n")
sections.append("This skill is a concatenation of generalized-transfer skills from all 17 source tasks. ")
sections.append("SkillOpt will optimize it through RL training.\\n\\n")
sections.append("---\\n\\n")

for task_id in SOURCE_TASKS:
    skill_path = os.path.join(SKILL_DIR, task_id, "skills", "generalized-transfer", "SKILL.md")
    if os.path.exists(skill_path):
        with open(skill_path) as f:
            content = f.read()
        sections.append(f"## Source Task: {task_id}\\n\\n")
        sections.append(content)
        sections.append("\\n\\n---\\n\\n")
        print(f"  Added: {task_id} ({len(content)} bytes)")
    else:
        print(f"  MISSING: {task_id}")

combined = "".join(sections)
with open(OUTPUT, "w") as f:
    f.write(combined)
print(f"\\nWritten {len(combined)} bytes to {OUTPUT}")
"""

# Write the script to server and run it
run(f"cat > /tmp/build_initial_skill.py << 'PYEOF'\n{build_script}\nPYEOF")
out, _ = run("python3 /tmp/build_initial_skill.py")
print(out)

# Verify
out, _ = run("wc -c /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/skills/initial.md")
print(f"Initial skill size: {out.strip()}")

# Step 3: Create launch script and start training
print("=" * 60)
print("STEP 3: Launch skill-opt training")
print("=" * 60)

launch_cmd = """cd /data/yjh/skill-opt/repo && source /data/yjh/skill-opt/venv/bin/activate && \\
OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com \\
OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ \\
OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash \\
python3 scripts/train.py \\
  --config configs/biomnibench/default.yaml \\
  --env biomnibench \\
  --backend openai_compatible \\
  --optimizer_backend openai_compatible \\
  --target_backend openai_chat \\
  --reasoning_effort medium \\
  --num_epochs 5 \\
  --batch_size 4 \\
  --split_ratio 23:2:27 \\
  --data_path /data/yjh/biomnibench-organized \\
  --exec_timeout 300 \\
  --skill_init skillopt/envs/biomnibench/skills/initial.md \\
  --out_root /data/yjh/skill-opt/outputs \\
  --seed 42 \\
  --workers 2
"""

# Write launch script to server
run(f"cat > /data/yjh/skill-opt/launch_full.sh << 'SCRIPTEOF'\n#!/bin/bash\ncd /data/yjh/skill-opt/repo\nsource /data/yjh/skill-opt/venv/bin/activate\nexport OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com\nexport OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ\nexport OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash\nnohup python3 scripts/train.py \\\n  --config configs/biomnibench/default.yaml \\\n  --env biomnibench \\\n  --backend openai_compatible \\\n  --optimizer_backend openai_compatible \\\n  --target_backend openai_chat \\\n  --reasoning_effort medium \\\n  --num_epochs 5 \\\n  --batch_size 4 \\\n  --split_ratio 23:2:27 \\\n  --data_path /data/yjh/biomnibench-organized \\\n  --exec_timeout 300 \\\n  --skill_init skillopt/envs/biomnibench/skills/initial.md \\\n  --out_root /data/yjh/skill-opt/outputs \\\n  --seed 42 \\\n  --workers 2 \\\n  > /data/yjh/skill-opt/launch_full.log 2>&1 &\necho "PID: $!"\nSCRIPTEOF""")
run("chmod +x /data/yjh/skill-opt/launch_full.sh")

# Launch in tmux
run("tmux new-session -d -s skillopt_full 'bash /data/yjh/skill-opt/launch_full.sh'")
print("Launched skill-opt in tmux session 'skillopt_full'")

# Check after 5 seconds
import time
time.sleep(5)
out, _ = run("tmux capture-pane -t skillopt_full -p -S -20 2>/dev/null; echo '---EXIT---'; ps aux | grep train.py | grep -v grep | head -3")
print(f"Status:\\n{out[:1000]}")

print("\\n" + "=" * 60)
print("ALL DONE")
print("=" * 60)