#!/usr/bin/env python3
import json

with open('/data/yjh/skill-transfer-eval/summary_pruned/transfer_pruned_results.json') as f:
    d = json.load(f)

for k, v in sorted(d.items()):
    status = v.get("status", "?")
    reward = v.get("reward", "?")
    skill = v.get("skill_status", "?")
    print(f"{k}: status={status} reward={reward} skill={skill}")