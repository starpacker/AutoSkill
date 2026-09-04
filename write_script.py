#!/usr/bin/env python3
"""Write run_skillopt.sh to the server."""
import base64, subprocess, sys

content = b"""#!/bin/bash
export ANTHROPIC_MODEL="Vendor3/DeepSeek-V4-Flash"
export ANTHROPIC_BASE_URL="https://api.gpugeek.com"
export ANTHROPIC_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export MODEL_NAME="Vendor3/DeepSeek-V4-Flash"
export OPENAI_COMPATIBLE_BASE_URL="https://api.gpugeek.com"
export OPENAI_COMPATIBLE_API_KEY="00gcclg9l39y9p01000dhjzolag1q2hk00901kh1"
export OPENAI_COMPATIBLE_MODEL="Vendor3/DeepSeek-V4-Flash"

cd /data/yjh/skill-opt/repo
source /data/yjh/skill-opt/venv/bin/activate
exec python scripts/train.py --config configs/biomnibench/default.yaml --cfg-options env.exec_timeout=600 "$@"
"""

encoded = base64.b64encode(content).decode()
cmd = f"echo '{encoded}' | base64 -d > /data/yjh/skill-opt/repo/run_skillopt.sh && chmod +x /data/yjh/skill-opt/repo/run_skillopt.sh"
result = subprocess.run(
    ["ssh", "yjh@10.128.247.28", cmd],
    capture_output=True, text=True, timeout=30
)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RC:", result.returncode)

# Verify
verify = subprocess.run(
    ["ssh", "yjh@10.128.247.28", "cat -A /data/yjh/skill-opt/repo/run_skillopt.sh | head -5"],
    capture_output=True, text=True, timeout=30
)
print("Verify:")
print(verify.stdout)