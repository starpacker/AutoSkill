"""Fix adapter.py and other files that have line number prefixes from cat -n output."""
import re
import os

files_to_fix = [
    "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/adapter.py",
    "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/dataloader.py",
    "/data/yjh/skill-opt/repo/skillopt/envs/biomnibench/rollout.py",
]

for path in files_to_fix:
    if not os.path.exists(path):
        print(f"NOT FOUND: {path}")
        continue
    with open(path, "rb") as f:
        data = f.read()
    
    # Check if first line has line number prefix
    text = data.decode("utf-8", errors="replace")
    lines = text.splitlines()
    
    fixed_lines = []
    had_linenumbers = False
    for line in lines:
        # Remove leading whitespace then line number prefix like "1  " or "    1  "
        # Pattern: optional whitespace, digits, whitespace, then actual code
        cleaned = re.sub(r"^\s*\d+\s+", "", line, count=1)
        if cleaned != line:
            had_linenumbers = True
        fixed_lines.append(cleaned)
    
    if had_linenumbers:
        new_text = "\n".join(fixed_lines)
        with open(path, "w", newline="\n") as f:
            f.write(new_text)
        print(f"FIXED: {path} (removed line numbers)")
    else:
        print(f"OK: {path} (no line numbers)")

print("\nAll files checked.")