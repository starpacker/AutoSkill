import sys
sys.path.insert(0, r'c:\Users\30670\Desktop\Autoskill')
from skill_selector.v7_data import load_records
records = load_records()
print(f"Loaded {len(records)} records")
types = set(r.tx_type for r in records)
print(f"Types: {types}")
judges = set(r.judge for r in records)
print(f"Judges: {judges}")
for r in records[:3]:
    print(r)