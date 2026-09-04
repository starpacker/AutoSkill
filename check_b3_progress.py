#!/usr/bin/env python3
"""Check all Batch 3 results."""
import subprocess, json

SERVER = "server1"

def ssh(cmd, timeout=60):
    try:
        r = subprocess.run(
            ["ssh", "-o", "ConnectTimeout=15", "-o", "StrictHostKeyChecking=no", SERVER, cmd],
            capture_output=True, text=False, timeout=timeout
        )
        return r.stdout.decode("utf-8", errors="replace").strip()
    except Exception as e:
        return f"ERROR: {e}"

targets = ["da-12-2", "da-19-4", "da-8-2", "da-24-3", "da-26-4", 
           "da-15-7", "da-10-1", "da-18-1", "da-17-3", "da-1-4"]

baselines = {"da-12-2": 52, "da-19-4": 62, "da-8-2": 64, "da-24-3": 65, "da-26-4": 68,
             "da-15-7": 77, "da-10-1": 80, "da-18-1": 80, "da-17-3": 83, "da-1-4": 85}
oracles = {"da-12-2": 87, "da-19-4": 100, "da-8-2": 100, "da-24-3": 95, "da-26-4": 83,
           "da-15-7": 100, "da-10-1": 92, "da-18-1": 100, "da-17-3": 100, "da-1-4": 90}

print(f"{'Target':<10} {'BL':<6} {'Orc':<6} {'Reward':<8} {'Delta':<8} {'Rnd':<5} {'Judge':<8} {'Exit':<5} {'Status'}")
print("=" * 65)

results = []
for t in targets:
    out = ssh(f"tail -5 /data/yjh/skill-transfer-eval/logs/v7p1_batch3/{t}.log")
    lines = out.split("\n")
    
    reward = "?"
    rounds = "?"
    judge = "?"
    exit_code = "?"
    status = "?"
    
    try:
        full = ssh(f"cat /data/yjh/skill-transfer-eval/logs/v7p1_batch3/{t}.log")
        d = json.loads(full)
        reward = d.get("reward", "?")
        rounds = d.get("rounds", "?")
        judge = d.get("last_judge_status", "?")
        status = d.get("status", "?")
    except:
        pass
    
    for line in lines:
        if "exit code" in line:
            exit_code = line.split("exit code")[-1].strip().split()[0]
    
    bl = baselines[t]
    orc = oracles[t]
    
    if isinstance(reward, (int, float)):
        delta = reward - bl/100
        reward_str = f"{reward:.2f}"
        delta_str = f"{delta:+.2f}"
    else:
        delta_str = "?"
        reward_str = "?"
    
    print(f"{t:<10} {bl:<6} {orc:<6} {reward_str:<8} {delta_str:<8} {str(rounds):<5} {str(judge):<8} {exit_code}  {str(status)}")
    results.append((t, bl, orc, reward, rounds, judge, exit_code))

# Summary
print("\n" + "=" * 65)
print("SUMMARY")
print("=" * 65)
valid = [r for r in results if isinstance(r[3], (int, float))]
if valid:
    avg_reward = sum(r[3] for r in valid) / len(valid)
    pass_count = sum(1 for r in valid if r[5] == "pass")
    print(f"Completed: {len(valid)}/10 targets")
    print(f"Average Reward: {avg_reward:.3f}")
    print(f"Pass: {pass_count}/{len(valid)}")
    
    # Combined with existing 5 targets
    existing = [("da-25-1", 18, 86, 0.85, "pass"), ("da-13-6", 40, 100, 0.80, "pass"),
                ("da-20-4", 43, 85, 0.15, "fail"), ("da-4-1", 61, 100, 1.00, "pass"),
                ("da-9-1", 64, 100, 0.76, "pass")]
    all_rewards = [r[3] for r in valid] + [e[3] for e in existing]
    all_pass = pass_count + sum(1 for e in existing if e[4] == "pass")
    print(f"\n=== Combined 15-target ===")
    print(f"All 15 avg reward: {sum(all_rewards)/len(all_rewards):.3f}")
    print(f"All 15 pass: {all_pass}/15")