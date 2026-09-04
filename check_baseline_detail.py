"""Check baseline more carefully - look at actual directory structure."""
import subprocess, json, os, tempfile

def scp_and_run(local_content, timeout=60):
    tmp = tempfile.mktemp(suffix='.py')
    try:
        with open(tmp, 'w', encoding='utf-8') as f:
            f.write(local_content)
        subprocess.run(['scp', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', tmp, 'server1:/tmp/check_baseline2.py'], capture_output=True, timeout=30)
        result = subprocess.run(['ssh', '-o', 'ConnectTimeout=15', '-o', 'BatchMode=yes', '-o', 'StrictHostKeyChecking=no', 'server1', 'python3 /tmp/check_baseline2.py'], capture_output=True, timeout=timeout)
        return result.stdout.decode('utf-8', errors='replace')
    finally:
        try: os.unlink(tmp)
        except: pass

script = r'''
import json, os, glob

base = "/data/yjh/skill-transfer-eval/fewshot_transfer"
dirs = sorted(os.listdir(base))
print(f"Total dirs: {len(dirs)}")

# Check one dir structure
if dirs:
    d = dirs[0]
    full = os.path.join(base, d)
    print(f"\nExample dir: {full}")
    print(f"Contents: {os.listdir(full)}")
    # Check for summary inside
    for root, dirs2, files in os.walk(full):
        for f in files:
            if f == "run_summary.json":
                p = os.path.join(root, f)
                with open(p) as fh:
                    s = json.load(fh)
                print(f"  Found at {p}: status={s.get('status')}, reward={s.get('reward')}")

# Count all run_summary.json files
all_summaries = glob.glob(os.path.join(base, "*", "*", "run_summary.json"))
print(f"\nTotal run_summary.json found: {len(all_summaries)}")

# Show status breakdown
statuses = {}
for sp in all_summaries[:20]:
    with open(sp) as fh:
        s = json.load(fh)
    st = s.get("status", "unknown")
    statuses[st] = statuses.get(st, 0) + 1
print(f"Status breakdown: {statuses}")

# Check if there's a results_index.json
idx_path = "/data/yjh/skill-transfer-eval/results_index.json"
if os.path.exists(idx_path):
    with open(idx_path) as fh:
        idx = json.load(fh)
    print(f"\nresults_index.json keys: {list(idx.keys())[:10]}")
    bl = idx.get("baselines", {})
    print(f"Baselines: {len(bl)} entries")
    for k, v in list(bl.items())[:5]:
        print(f"  {k}: {v}")
'''

print(scp_and_run(script, timeout=60))