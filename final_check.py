"""Final check on training status."""
import subprocess

def ssh(cmd, timeout=60):
    try:
        r = subprocess.run(['ssh','-o','ConnectTimeout=15','-o','BatchMode=yes','server1',cmd], capture_output=True, timeout=timeout)
        return r.stdout.decode()
    except:
        return "SSH_FAILED"

# Check tmux sessions
print("=== TMUX Sessions ===")
print(ssh("tmux list-sessions 2>/dev/null || echo 'no sessions'", 15))

# Check skillopt session
print("\n=== Skillopt tmux output ===")
print(ssh("tmux capture-pane -t skillopt_full -p -S -200 2>/dev/null || echo 'no output'", 15))

# Check output dir
print("\n=== Output dir ===")
print(ssh("ls -laR /data/yjh/skill-opt/output/ 2>/dev/null | head -30", 15))

# Check fewshot baseline
print("\n=== Fewshot baseline ===")
print(ssh("tmux capture-pane -t fewshot_baseline -p -S -30 2>/dev/null | tail -15", 15))