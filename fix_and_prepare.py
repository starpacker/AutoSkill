"""Fix skill-opt timeout and prepare for full experiment run."""
import subprocess
import json
import os
import tempfile

def run_ssh(cmd, timeout=60):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=timeout)
    return result.stdout.decode("utf-8", errors="replace"), result.stderr.decode("utf-8", errors="replace"), result.returncode

def scp_file(local_content, remote_path):
    """Write a local content string to a remote file via temp file."""
    tmp = tempfile.mktemp(suffix='.py')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        result = subprocess.run(
            ["scp", "-o", "BatchMode=yes", "-o", "StrictHostKeyChecking=no", tmp, f"server1:{remote_path}"],
            capture_output=True, timeout=30
        )
        return result.returncode == 0
    finally:
        try:
            os.unlink(tmp)
        except:
            pass

# ============================================================
# STEP 1: Fix rollout.py timeout to 300s
# ============================================================
print("=== STEP 1: Fix rollout.py ===")
# Read current rollout.py
stdout, stderr, rc = run_ssh("cat -n /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py")
lines = stdout.split('\n')
# Print lines 1-30 to see the current state
for line in lines[:30]:
    print(line)

# Fix: change timeout_seconds from 7200 to 300
new_rollout = stdout.replace("timeout_seconds: int = 7200,", "timeout_seconds: int = 300,")
new_rollout = new_rollout.replace("exec_timeout: int = 7200,", "exec_timeout: int = 300,")
if scp_file(new_rollout, "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py"):
    print("rollout.py updated successfully")
else:
    print("FAILED to update rollout.py")

# ============================================================
# STEP 2: Fix adapter.py exec_timeout to 300s
# ============================================================
print("\n=== STEP 2: Fix adapter.py ===")
stdout, stderr, rc = run_ssh("cat -n /data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py")
for line in stdout.split('\n')[:20]:
    print(line)
    
new_adapter = stdout.replace("exec_timeout: int = 7200,", "exec_timeout: int = 300,")
if scp_file(new_adapter, "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py"):
    print("adapter.py updated successfully")
else:
    print("FAILED to update adapter.py")

# ============================================================
# STEP 3: Create meaningful initial skill
# ============================================================
print("\n=== STEP 3: Create initial skill ===")
initial_skill = """# BioMNIBench Agent Skill

## General Guidelines

As a bioinformatics data analysis agent, follow these guidelines:

### 1. Understand the Task
- Read the README.md completely before starting
- Identify the input data files and their formats
- Understand the expected output format and evaluation criteria

### 2. Data Analysis Approach
- Use Python (pandas, numpy, scipy) for data manipulation
- Use scanpy for single-cell data analysis
- Use matplotlib/seaborn for visualization when needed
- Write clean, well-documented Python scripts

### 3. Problem-Solving Strategy
- Break down complex analysis into manageable steps
- Verify intermediate results before proceeding
- Use appropriate statistical methods for biological data
- Handle edge cases (missing data, different file formats)

### 4. Submission
- Save results to the outputs/ directory
- Follow the exact output format specified in the task
- Create a trace.md summarizing your approach
- Create answer.txt with the final answer when specified

### 5. Code Quality
- Use proper error handling
- Add comments explaining key steps
- Use modular code with functions
- Avoid hardcoding paths
"""

if scp_file(initial_skill, "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/skills/initial.md"):
    print("Initial skill created successfully")
else:
    print("FAILED to create initial skill")

# ============================================================
# STEP 4: Update config for 23 train / 27 test
# ============================================================
print("\n=== STEP 4: Update config ===")
stdout, stderr, rc = run_ssh("cat -n /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml")
for line in stdout.split('\n'):
    print(line)

# Update the config
new_config = stdout.replace("split_ratio: \"2:1:7\"", "split_ratio: \"23:2:27\"")
# Also update batch_size and num_epochs for a proper run
new_config = new_config.replace("num_epochs: 3", "num_epochs: 5")
new_config = new_config.replace("batch_size: 6", "batch_size: 4")
new_config = new_config.replace("limit: 0", "limit: 0")

if scp_file(new_config, "/data/yjh/skill-opt/repo/configs/biomnibench/default.yaml"):
    print("Config updated successfully")
else:
    print("FAILED to update config")

print("\n=== ALL UPDATES COMPLETE ===")