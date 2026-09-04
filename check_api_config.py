"""Check API setup and launch skill-opt."""
import subprocess, json, os, tempfile

def scp_and_run(local_content, timeout=60):
    tmp = tempfile.mktemp(suffix='.py')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', tmp, 'server1:/tmp/check_launch.py'], capture_output=True, timeout=30)
        result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'server1', 'python3 /tmp/check_launch.py'], capture_output=True, timeout=timeout)
        return result.stdout.decode('utf-8', errors='replace')
    finally:
        try: os.unlink(tmp)
        except: pass

script = r'''
import os, json

# Check the venv activate script for API keys
activate_path = "/data/yjh/skill-opt/venv/bin/activate"
if os.path.exists(activate_path):
    with open(activate_path) as f:
        content = f.read()
    # Find env vars
    for line in content.split('\n'):
        if 'API_KEY' in line or 'BASE_URL' in line or 'OPENAI' in line or 'BACKEND' in line or 'MODEL' in line:
            val = line.strip()
            if '=' in val:
                key, val2 = val.split('=', 1)
                val2 = val2[:50] + "..." if len(val2) > 50 else val2
                print(f"  {key}={val2}")

# Check other env files
for p in ["/data/yjh/skill-opt/.env", "/data/yjh/skill-opt/repo/.env"]:
    if os.path.exists(p):
        print(f"\n{p}:")
        with open(p) as f:
            print(f.read()[:500])

# Check what model vars are set
print("\n--- Current env from shell ---")
for k in sorted(os.environ.keys()):
    if any(x in k.upper() for x in ['API_KEY', 'BASE_URL', 'OPENAI', 'MODEL', 'BACKEND']):
        v = os.environ[k]
        v = v[:60] + "..." if len(v) > 60 else v
        print(f"  {k}={v}")
'''

print("=== API CONFIG ===")
print(scp_and_run(script, timeout=30))

# Also check the train.py for the output/save dir
script2 = r'''
import os
# Check what output dir is used by default
# Look at the train script behavior
import subprocess
result = subprocess.run(
    ["/data/yjh/skill-opt/venv/bin/python", "-c", 
     "from skillopt.utils.common import get_output_dir; print(get_output_dir())"],
    capture_output=True, text=True, timeout=30,
    cwd="/data/yjh/skill-opt/repo"
)
print(f"Output dir: {result.stdout}")
print(f"Error: {result.stderr}")
'''

print("=== OUTPUT DIR ===")
print(scp_and_run(script2, timeout=30))