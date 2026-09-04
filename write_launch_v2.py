"""Write correct launch script for skill-opt, using --cfg-options for env.exec_timeout."""
import os

script = """#!/bin/bash
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
nohup python3 scripts/train.py \
  --config configs/biomnibench/default.yaml \
  --cfg-options env.exec_timeout=300 \
  > /data/yjh/skill-opt/launch_full.log 2>&1 &
echo "PID: $!"
"""

path = "/data/yjh/skill-opt/launch_skillopt.sh"
with open(path, "w") as f:
    f.write(script)
os.chmod(path, 0o755)
print(f"Written {path}")

# Also create tmux version
tmux_script = """#!/bin/bash
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=gpugeek_sk_mDx3cn5MCqDo3DIqJXqPyQ
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
python3 scripts/train.py \
  --config configs/biomnibench/default.yaml \
  --cfg-options env.exec_timeout=300
"""

tmux_path = "/data/yjh/skill-opt/launch_tmux.sh"
with open(tmux_path, "w") as f:
    f.write(tmux_script)
os.chmod(tmux_path, 0o755)
print(f"Written {tmux_path}")
print("Done")