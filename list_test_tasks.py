"""List test tasks from the generated split."""
import json

items = json.load(open("test_items.json"))
for i, item in enumerate(items):
    print(f"{i+1}. {item['id']}")