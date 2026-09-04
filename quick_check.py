"""Quick check of skill-opt training status via SSH."""
import subprocess
import sys

def ssh(cmd, timeout=30):
    try:
        r = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 
             '-o', 'ServerAliveInterval=5', 'server1', cmd],
            capture_output=True, timeout=timeout
        )
        return r.stdout.decode(), r.stderr.decode(), r.returncode
    except Exception as e:
        return "", str(e), -1

# Quick check
out, err, rc = ssh("tmux list-sessions 2>&1")
print("SESSIONS:", out.strip()[:200])

out, err, rc = ssh("tmux capture-pane -t skillopt_full -p -S -200 2>&1 | tail -60")
print("TMUX:", out.strip()[:2000] if out else err[:200])

out, err, rc = ssh("ls -la /data/yjh/skill-opt/output/biomnibench_full_20260829_155828/ 2>&1")
print("OUTDIR:", out.strip()[:300])

out, err, rc = ssh("ps aux | grep train.py | grep -v grep 2>&1")
print("PROC:", out.strip()[:200])