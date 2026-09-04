"""Debug and re-launch skill-opt experiment."""
import subprocess, time

def ssh(cmd, timeout=30):
    try:
        r = subprocess.run(
            ['ssh', '-o', 'ConnectTimeout=10', '-o', 'BatchMode=yes', 'server1', cmd],
            capture_output=True, timeout=timeout
        )
        return r.stdout.decode(), r.stderr.decode(), r.returncode
    except Exception as e:
        return "", str(e), -1

# Check repo dir
print("=== Check repo dir ===")
o, e, r = ssh("ls -d /data/yjh/skill-opt/repo 2>&1")
print(f"repo: {o[:200]} (rc={r})")

# Check venv
print("\n=== Check venv ===")
o, e, r = ssh("ls /data/yjh/skill-opt/venv/bin/activate 2>&1")
print(f"activate: {o[:200]} (rc={r})")

# Check config
print("\n=== Check config ===")
o, e, r = ssh("ls /data/yjh/skill-opt/repo/configs/biomnibench/default.yaml 2>&1")
print(f"config: {o[:200]} (rc={r})")

# Check the script
print("\n=== Check launch script ===")
o, e, r = ssh("cat /data/yjh/skill-opt/launch_full_exp.sh 2>&1")
print(o[:500])

# Kill old tmux session
print("\n=== Kill old session ===")
o, e, r = ssh("tmux kill-session -t skillopt_full 2>/dev/null; echo 'done'")
print(f"kill: {o}")

# Create a simpler test: just test if the script works outside tmux
print("\n=== Test bash execution ===")
o, e, r = ssh("bash -c 'echo hello; exit 0'", timeout=15)
print(f"bash test: {o} (rc={r})")

# Test the script directly
print("\n=== Test launch script ===")
o, e, r = ssh("bash /data/yjh/skill-opt/launch_full_exp.sh 2>&1", timeout=15)
print(f"stdout: {o[:1000]}")
print(f"stderr: {e[:500]}")
print(f"rc: {r}")