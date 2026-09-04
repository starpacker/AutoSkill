"""Check training status and update progress."""
import subprocess, time

def ssh(cmd, timeout=60):
    r = subprocess.run(['ssh','-o','ConnectTimeout=15','-o','BatchMode=yes','server1',cmd], capture_output=True, timeout=timeout)
    return r.stdout.decode()

# Wait for training to start
time.sleep(10)

# Check tmux output
print("=== Tmux capture ===")
out = ssh("tmux capture-pane -t skillopt_full -p -S -50 2>/dev/null | tail -30")
print(out[:2000])

# Check output dirs
print("\n=== Output dirs ===")
out = ssh("ls -la /data/yjh/skill-opt/output/ 2>/dev/null")
print(out[:500])

# Find training logs
print("\n=== Training logs ===")
out = ssh("find /data/yjh/skill-opt/output/ -name 'training.log' -o -name '*.log' 2>/dev/null | head -5")
print(out[:500])

# Check if training log exists and read it
out = ssh("cat /data/yjh/skill-opt/output/biomnibench_full_20260829_155828/training.log 2>/dev/null | tail -20")
print("\n=== Training log content ===")
print(out[:2000])