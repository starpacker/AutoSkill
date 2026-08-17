#!/usr/bin/env python3
"""Get baseline run_summary for da-17-1."""
import json
d = json.load(open("/data/yjh/skill-transfer-eval/baseline/da-17-1_20260721_192248_baseline_rep1/logs/run_summary.json"))
print(json.dumps(d, indent=2)[:5000])