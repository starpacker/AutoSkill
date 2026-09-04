"""Check timeout values in step event files."""
import subprocess
import json

def run_ssh(cmd):
    full_cmd = [
        "ssh", "-o", "ConnectTimeout=15", "-o", "BatchMode=yes",
        "-o", "StrictHostKeyChecking=no", "server1", cmd
    ]
    result = subprocess.run(full_cmd, capture_output=True, timeout=60)
    return result.stdout.decode("utf-8", errors="replace")

# Use a simple script on the server to parse events
script = r"""
import json, os, glob

for f in glob.glob('/tmp/skillopt_test_run/steps/*/rollout/runs/*/*/logs/run_events.jsonl'):
    try:
        with open(f) as fh:
            first = json.loads(fh.readline())
        print(f"{os.path.dirname(os.path.dirname(os.path.dirname(f)))}: timeout={first['details']['timeoutSeconds']}")
    except Exception as e:
        print(f"{f}: error={e}")
"""

r = run_ssh(f"python3 -c \"{script}\"")
print(r[:3000])

# Also check the selection_eval_baseline events
script2 = r"""
import json, os, glob

for f in glob.glob('/tmp/skillopt_test_run/selection_eval_baseline/runs/*/*/logs/run_events.jsonl'):
    try:
        with open(f) as fh:
            first = json.loads(fh.readline())
        print(f"{os.path.basename(os.path.dirname(f))}: timeout={first['details']['timeoutSeconds']}, maxRounds={first['details']['maxRounds']}")
    except Exception as e:
        print(f"{f}: error={e}")
"""

r2 = run_ssh(f"python3 -c \"{script2}\"")
print(r2[:3000])

# Check test_eval and test_eval_baseline
script3 = r"""
import json, os, glob

for prefix in ['test_eval', 'test_eval_baseline', 'test_eval_final', 'final_selection_eval']:
    for f in glob.glob(f'/tmp/skillopt_test_run/{prefix}/runs/*/*/logs/run_events.jsonl'):
        try:
            with open(f) as fh:
                first = json.loads(fh.readline())
            print(f"{prefix}/{os.path.basename(os.path.dirname(f))}: timeout={first['details']['timeoutSeconds']}, maxRounds={first['details']['maxRounds']}")
        except Exception as e:
            print(f"{f}: error={e}")
"""

r3 = run_ssh(f"python3 -c \"{script3}\"")
print(r3[:3000])