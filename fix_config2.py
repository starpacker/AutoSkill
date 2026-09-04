"""Fix YAML indentation for exec_timeout in biomnibench config."""
import re

cfg_path = "/data/yjh/skill-opt/repo/configs/biomnibench/default.yaml"
with open(cfg_path) as f:
    cfg = f.read()

# Remove the wrongly placed exec_timeout line
cfg = re.sub(r"\n\s*exec_timeout:\s*\d+", "", cfg)

# Add it properly under env: section with 4-space indent
# Find the line with "workers: 2" under env: and add after it
cfg = cfg.replace(
    "    workers: 2",
    "    workers: 2\n    exec_timeout: 300"
)

with open(cfg_path, "w") as f:
    f.write(cfg)

print("Fixed YAML indentation")
print(cfg)