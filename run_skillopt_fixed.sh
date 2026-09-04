#!/bin/bash
echo "DEBUG: OPENAI_COMPATIBLE_BASE_URL=$OPENAI_COMPATIBLE_BASE_URL"
export ANTHROPIC_MODEL=Vendor3/DeepSeek-V4-Flash
export ANTHROPIC_BASE_URL=https://api.gpugeek.com
export ANTHROPIC_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export MODEL_NAME=Vendor3/DeepSeek-V4-Flash
export OPENAI_COMPATIBLE_BASE_URL=https://api.gpugeek.com/v1
export OPENAI_COMPATIBLE_API_KEY=00gcclg9l39y9p01000dhjzolag1q2hk00901kh1
export OPENAI_COMPATIBLE_MODEL=Vendor3/DeepSeek-V4-Flash
export OPTIMIZER_OPENAI_COMPATIBLE_MAX_TOKENS=64000
cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
exec python scripts/train.py --config configs/biomnibench/default.yaml --cfg-options env.exec_timeout=1200