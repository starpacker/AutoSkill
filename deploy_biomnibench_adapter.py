#!/usr/bin/env python3
"""Upload BioMNIBench adapter files to server1 and register in skill-opt."""
import subprocess, base64, os, sys

def ssh(command):
    r = subprocess.run(["ssh", "-o", "BatchMode=yes", "-o", "ServerAliveInterval=5", "server1", command], capture_output=True, timeout=60)
    try: out = r.stdout.decode('utf-8', errors='replace').strip()
    except: out = r.stdout.decode('gbk', errors='replace').strip()
    if r.stderr.strip():
        try: print(f"  STDERR: {r.stderr.decode('utf-8', errors='replace')[:200]}")
        except: pass
    return out, r.returncode

def upload_file(local_path, remote_path):
    with open(local_path, 'rb') as f:
        content = f.read()
    encoded = base64.b64encode(content).decode()
    rp = remote_path.replace('\\', '/')
    parent = os.path.dirname(rp).replace('\\', '/')
    out, rc = ssh(f"mkdir -p '{parent}'")
    write_script = f"python3 -c \"import base64; open('{rp}','wb').write(base64.b64decode('{encoded}'))\""
    out, rc = ssh(write_script)
    if rc == 0:
        print(f"  OK: {rp}")
    else:
        print(f"  FAIL: {rp} (rc={rc})")
        print(f"  {out[:200]}")
        return False
    return True

base = os.path.join(os.path.dirname(os.path.abspath(__file__)), "skillopt_biomnibench")
repo = "/data/yjh/skill-opt/repo"
train_py = f"{repo}/scripts/train.py"
eval_py = f"{repo}/scripts/eval_only.py"

print("=" * 60)
print("UPLOADING BIOMNIBENCH ADAPTER FILES")
print("=" * 60)

files = [
    ("adapter.py", "skillopt/envs/biomnibench/adapter.py"),
    ("dataloader.py", "skillopt/envs/biomnibench/dataloader.py"),
    ("rollout.py", "skillopt/envs/biomnibench/rollout.py"),
    ("__init__.py", "skillopt/envs/biomnibench/__init__.py"),
    ("prompts/rollout_system.md", "skillopt/envs/biomnibench/prompts/rollout_system.md"),
    ("prompts/analyst_error.md", "skillopt/envs/biomnibench/prompts/analyst_error.md"),
    ("prompts/analyst_success.md", "skillopt/envs/biomnibench/prompts/analyst_success.md"),
    ("skills/initial.md", "skillopt/envs/biomnibench/skills/initial.md"),
]

init_path = os.path.join(base, "__init__.py")
if not os.path.exists(init_path):
    with open(init_path, "w") as f: f.write("")

all_ok = True
for local_rel, remote_rel in files:
    local_path = os.path.join(base, local_rel)
    remote_path = f"{repo}/{remote_rel}"
    if not os.path.exists(local_path):
        print(f"  SKIP (not found): {local_path}")
        continue
    if not upload_file(local_path, remote_path):
        all_ok = False

# Config
config_path = f"{repo}/configs/biomnibench/default.yaml"
config_content = '''_base_: ../_base_/default.yaml

env:
  name: biomnibench
  skill_init: skillopt/envs/biomnibench/skills/initial.md
  data_path: /data/yjh/biomnibench-organized
  split_dir: ""
  split_mode: ratio
  split_ratio: "2:1:7"
  workers: 2
  max_completion_tokens: 16384
  limit: 0

train:
  num_epochs: 3
  batch_size: 6
  accumulation: 1
  seed: 42

gradient:
  analyst_workers: 8
  minibatch_size: 4
  merge_batch_size: 4

optimizer:
  learning_rate: 4
  lr_scheduler: cosine
  use_slow_update: true
  use_meta_skill: true

evaluation:
  use_gate: true
  eval_test: true

model:
  backend: openai_compatible
  optimizer_backend: openai_compatible
  target_backend: openai_chat
  reasoning_effort: medium
'''
encoded = base64.b64encode(config_content.encode()).decode()
out, rc = ssh(f"mkdir -p {repo}/configs/biomnibench && python3 -c \"import base64; open('{config_path}','w').write(base64.b64decode('{encoded}').decode())\"")
if rc == 0:
    print(f"  OK: configs/biomnibench/default.yaml")
else:
    print(f"  FAIL: config (rc={rc})")
    all_ok = False

# Register in train.py
print("\n=== Registering in train.py ===")
out, rc = ssh(f"grep -n 'biomnibench' {train_py}")
if 'biomnibench' not in out:
    reg_code = '''
    try:
        from skillopt.envs.biomnibench.adapter import BioMNIBenchAdapter
        _ENV_REGISTRY["biomnibench"] = BioMNIBenchAdapter
    except ImportError:
        pass
'''
    out, rc = ssh(f"python3 << 'PYEOF'\nwith open('{train_py}','r') as f: content = f.read()\nmarker = 'except ImportError:\\n        pass\\n'\nlast_pos = content.rfind(marker)\nif last_pos > 0:\n    insert_pos = last_pos + len(marker)\n    content = content[:insert_pos] + {repr(reg_code)} + content[insert_pos:]\n    with open('{train_py}','w') as f: f.write(content)\n    print('REGISTERED')\nelse:\n    print('MARKER_NOT_FOUND')\nPYEOF")
    print(f"  train.py: {out[:200]}")
else:
    print("  Already registered in train.py")

# Register in eval_only.py
print("\n=== Registering in eval_only.py ===")
out, rc = ssh(f"grep -n 'biomnibench' {eval_py}")
if 'biomnibench' not in out:
    reg_code = '''
    try:
        from skillopt.envs.biomnibench.adapter import BioMNIBenchAdapter
        _ENV_REGISTRY["biomnibench"] = BioMNIBenchAdapter
    except ImportError:
        pass
'''
    out, rc = ssh(f"python3 << 'PYEOF'\nwith open('{eval_py}','r') as f: content = f.read()\nmarker = 'except ImportError:\\n        pass\\n'\nlast_pos = content.rfind(marker)\nif last_pos > 0:\n    insert_pos = last_pos + len(marker)\n    content = content[:insert_pos] + {repr(reg_code)} + content[insert_pos:]\n    with open('{eval_py}','w') as f: f.write(content)\n    print('REGISTERED')\nelse:\n    print('MARKER_NOT_FOUND')\nPYEOF")
    print(f"  eval_only.py: {out[:200]}")
else:
    print("  Already registered in eval_only.py")

# Verify
print("\n=== Verification ===")
for d in ["skillopt/envs/biomnibench", "skillopt/envs/biomnibench/prompts", "skillopt/envs/biomnibench/skills", "configs/biomnibench"]:
    out, rc = ssh(f"ls -la {repo}/{d}")
    print(f"  {d}: {out[:100]}")

print("\n=== Testing import ===")
out, rc = ssh(f"cd {repo} && /data/yjh/skill-opt/venv/bin/python3 -c 'from skillopt.envs.biomnibench.adapter import BioMNIBenchAdapter; a = BioMNIBenchAdapter(); print(\"IMPORT OK:\", type(a).__name__)'")
print(f"  {out[:200]}")
if all_ok:
    print("\n=== DEPLOYMENT SUCCESSFUL ===")
else:
    print("\n=== DEPLOYMENT PARTIAL ===")