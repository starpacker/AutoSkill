import os, subprocess
result = subprocess.run(["grep", "-rn", "configure_openai_compatible", "/data/yjh/skill-opt/repo/scripts/", "/data/yjh/skill-opt/repo/skillopt/"], capture_output=True, text=True)
print("=== ALL RESULTS ===")
print(result.stdout)
print("=== CALLS ONLY (non-def, non-init) ===")
for line in result.stdout.splitlines():
    if "def " not in line and "__init__" not in line:
        print("CALL:", line)