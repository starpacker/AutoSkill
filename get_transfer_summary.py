#!/usr/bin/env python3
"""Get transfer run_summary for da-12-4 -> da-17-1."""
import json

d = json.load(open("/data/yjh/skill-transfer-eval/transfer_pruned/da-17-1_pruned_transfer_da-12-4_to_da-17-1/logs/run_summary.json"))

# Print full JSON with limited depth
print(json.dumps(d, indent=2)[:5000])