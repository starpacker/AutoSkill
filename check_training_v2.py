"""Check skill-opt training status - runs on server1 via SSH."""
import subprocess

def ssh(cmd, timeout=60):
    try:
        r = subprocess.run(['ssh','-o','ConnectTimeout=15','-o','BatchMode=yes','-o','ServerAliveInterval=10','server1',cmd], 
                         capture_output=True, timeout=timeout)
        out = r.stdout.decode().strip()
        err = r.stderr.decode().strip()
        return out, err, r.returncode
    except subprocess.TimeoutExpired:
        return "TIMEOUT", "", -1
    except Exception as e:
        return f"ERROR: {e}", "", -1

# 1. Check tmux session
out, err, rc = ssh("tmux list-sessions 2>&1")
print(f"=== TMUX Sessions (rc={rc}) ===")
print(out or err)

# 2. Get full tmux pane content
out, err, rc = ssh("tmux capture-pane -t skillopt_full -p -S -500 2>&1 | tail -100")
print(f"\n=== Tmux skillopt_full (last 100 lines) ===")
print(out or err)

# 3. Check if launch script is still there
out, err, rc = ssh("cat /data/yjh/skill-opt/launch_full_exp.sh 2>&1")
print(f"\n=== Launch script (rc={rc}) ===")
print(out[:500] if out else err)

# 4. Check output dir contents
out, err, rc = ssh("find /data/yjh/skill-opt/output/biomnibench_full_20260829_155828/ -type f 2>&1 | head -30")
print(f"\n=== Output files ===")
print(out or err or "(empty)")

# 5. Check for any error in the output dir
out, err, rc = ssh("ls -la /data/yjh/skill-opt/output/biomnibench_full_20260829_155828/ 2>&1")
print(f"\n=== Output dir listing ===")
print(out or err)

# 6. Check if there's a nohup or log file elsewhere
out, err, rc = ssh("find /data/yjh/skill-opt/ -name '*.log' -o -name 'nohup.out' 2>/dev/null | head -10")
print(f"\n=== Log files in skill-opt ===")
print(out or "(none)")

# 7. Check if train.py is running
out, err, rc = ssh("ps aux | grep -E 'train\\.py|launch_full' | grep -v grep 2>&1 | head -20")
print(f"\n=== Running processes ===")
print(out or "(none - no python train.py running)")

# 8. Check tmux full history
out, err, rc = ssh("tmux capture-pane -t skillopt_full -p -S -2000 2>&1 | head -100")
print(f"\n=== Tmux full history (first 100 lines) ===")
print(out or err)