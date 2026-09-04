#!/bin/bash
# Launch skill-opt full training in tmux session
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com
export OPENAI_COMPATIBLE_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
nohup python3 scripts/train.py \
  --config configs/biomnibench/default.yaml \
  --cfg-options env.exec_timeout=600 \
  > /data/yjh/skill-opt/launch_full.log 2>&1 &
echo "PID: $!"