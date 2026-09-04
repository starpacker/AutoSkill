"""Write launch_skillopt.sh on server and launch it in tmux."""
import os
import sys

script = """#!/bin/bash
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
nohup python3 scripts/train.py \
  --config configs/biomnibench/default.yaml \
  --env biomnibench \
  --backend openai_compatible \
  --optimizer_backend openai_compatible \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --num_epochs 5 \
  --batch_size 4 \
  --split_ratio 23:2:27 \
  --data_path /data/yjh/biomnibench-organized \
  --exec_timeout 300 \
  --skill_init skillopt/envs/biomnibench/skills/initial.md \
  --out_root /data/yjh/skill-opt/outputs \
  --seed 42 \
  --workers 2 \
  > /data/yjh/skill-opt/launch_full.log 2>&1 &
echo "PID: $!"
"""

path = "/data/yjh/skill-opt/launch_skillopt.sh"
with open(path, "w") as f:
    f.write(script)
os.chmod(path, 0o755)
print(f"Written {path}")

# Also create a tmux-based launch script
tmux_script = """#!/bin/bash
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
python3 scripts/train.py \
  --config configs/biomnibench/default.yaml \
  --env biomnibench \
  --backend openai_compatible \
  --optimizer_backend openai_compatible \
  --target_backend openai_chat \
  --reasoning_effort medium \
  --num_epochs 5 \
  --batch_size 4 \
  --split_ratio 23:2:27 \
  --data_path /data/yjh/biomnibench-organized \
  --exec_timeout 300 \
  --skill_init skillopt/envs/biomnibench/skills/initial.md \
  --out_root /data/yjh/skill-opt/outputs \
  --seed 42 \
  --workers 2
"""

tmux_path = "/data/yjh/skill-opt/launch_tmux.sh"
with open(tmux_path, "w") as f:
    f.write(tmux_script)
os.chmod(tmux_path, 0o755)
print(f"Written {tmux_path}")
print("Done")