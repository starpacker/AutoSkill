import sys
sys.path.insert(0, '/data/yjh/skill-transfer-eval')
from skill_selector.v7_data import load_records
records = load_records()
print(f"Loaded {len(records)} records")
for r in records[:3]:
    print(r)
print(f"\nTypes: {set(r.tx_type for r in records)}")
print(f"Judges: {set(r.judge for r in records)}")