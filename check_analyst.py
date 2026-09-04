#!/usr/bin/env python3
"""Check why analyst returns 0 edits."""
import json, os, sys

OUT = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_Vendor3-DeepSeek-V4-Flash_20260901_174731"

# 1. Check conversation.json for da-20-1 (failure)
path = os.path.join(OUT, "steps/step_0001/rollout/predictions/da-20-1/conversation.json")
with open(path) as f:
    d = json.load(f)
print(f"=== da-20-1 conversation.json: {len(d)} entries ===")
for i, e in enumerate(d[:5]):
    print(f"  entry {i}: type={e.get('type','?')}, keys={list(e.keys())}")
print()

# 2. Check conversation.json for da-19-1 (success)
path2 = os.path.join(OUT, "steps/step_0001/rollout/predictions/da-19-1/conversation.json")
with open(path2) as f:
    d2 = json.load(f)
print(f"=== da-19-1 conversation.json: {len(d2)} entries ===")
for i, e in enumerate(d2[:5]):
    print(f"  entry {i}: type={e.get('type','?')}, keys={list(e.keys())}")
print()

# 3. Check if minibatch patches were saved
patch_dir = os.path.join(OUT, "steps/step_0001/patches")
if os.path.isdir(patch_dir):
    print(f"=== Patches dir: {os.listdir(patch_dir)} ===")
    for fname in sorted(os.listdir(patch_dir)):
        fpath = os.path.join(patch_dir, fname)
        with open(fpath) as f:
            data = json.load(f)
        patch = data.get("patch", {})
        edits = patch.get("edits", []) if patch else []
        reasoning = (patch.get("reasoning", "") or "")[:100] if patch else "N/A"
        print(f"  {fname}: source_type={data.get('source_type')}, edits={len(edits)}, reasoning={reasoning}")
else:
    print(f"Patches dir does not exist: {patch_dir}")

# 4. Check last few entries of da-20-1 conversation
print(f"\n=== da-20-1 last 3 entries ===")
for e in d[-3:]:
    print(f"  type={e.get('type','?')}, keys={list(e.keys())}")
    if "obs" in e:
        print(f"    obs[:200]={str(e.get('obs',''))[:200]}")

# 5. Check the rollout result dicts
print(f"\n=== Checking run_summary.json for da-20-1 ===")
rs_path = os.path.join(OUT, "steps/step_0001/rollout/runs/da-20-1/da-20-1_skillopt_da-20-1_1788258456/logs/run_summary.json")
with open(rs_path) as f:
    rs = json.load(f)
print(f"  keys: {list(rs.keys())}")
print(f"  hard: {rs.get('hard')}")
print(f"  fail_reason: {str(rs.get('fail_reason',''))[:200]}")
print(f"  n_turns: {rs.get('n_turns')}")
print(f"  task_type: {rs.get('task_type')}")

# 6. Check if rollout result items have the expected fields
print(f"\n=== Checking rollout results for failure detection ===")
# The results dict structure from the code is: r.get("hard") to detect failures
# Key insight: failures = [r for r in results if not r.get("hard") or float(r.get("hard", 0)) < 1e-9]
# This means "hard=0" items are failures, "hard=1" are successes.
# But da-20-1 has hard=0 — it's a failure. The conversation exists.
# The analyst is called, but returns None.
# 
# The env-specific prompt doesn't tell the model to output JSON!
# It says "Provide a concise analysis" but doesn't specify the format.
# The generic prompt says "Respond ONLY with a valid JSON object".
# So the env-specific prompt overrides the generic one, and the model
# gives prose instead of JSON, which extract_json fails to parse, returning None.
print("ROOT CAUSE: The biomnibench env-specific prompts (analyst_error.md and analyst_success.md)")
print("are plain-text prompts that DON'T specify JSON output format.")
print("They override the generic prompts which DO specify JSON format.")
print("The LLM returns prose analysis -> extract_json() returns None -> 0 patches.")