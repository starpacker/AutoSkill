"""Check adapter.py for encoding issues."""
with open("/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py", "rb") as f:
    data = f.read()
print(f"Length: {len(data)}")
print(f"First 100 bytes: {data[:100]}")
print(f"Has BOM: {data[:3] == b'\\xef\\xbb\\xbf'}")
null_pos = data.find(b"\\x00")
if null_pos >= 0:
    print(f"Null byte at position: {null_pos}")
print("First 10 lines:")
for i, line in enumerate(data.decode("utf-8").split("\\n")[:10]):
    print(f"  Line {i+1}: {repr(line[:80])}")