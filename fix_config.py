"""Fix exec_timeout in biomnibench config."""
import os

cfg_path = "/data/yjh/skill-opt/repo/configs/biomnibench/default.yaml"
with open(cfg_path) as f:
    cfg = f.read()

if "exec_timeout" not in cfg:
    cfg = cfg.replace("workers: 2", "workers: 2\n    exec_timeout: 300")
    with open(cfg_path, "w") as f:
        f.write(cfg)
    print("Added exec_timeout: 300")
else:
    # Update existing
    import re
    cfg = re.sub(r"exec_timeout:\s*\d+", "exec_timeout: 300", cfg)
    with open(cfg_path, "w") as f:
        f.write(cfg)
    print("Updated exec_timeout to 300")

# Print final config
with open(cfg_path) as f:
    print(f.read())