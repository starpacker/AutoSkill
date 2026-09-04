#!/usr/bin/env python3
"""Fix markdown JSON code block stripping in llm_judge_qwen.py"""
import re

with open('/tmp/my_claude_biomnibench_fixed/llm_judge_qwen.py') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    if 'startswith' in line and "'`'" in line:
        lines[i] = '    if response_text.strip().startswith("```"):\n'
    elif "re.sub(r'^`" in line:
        lines[i] = "        response_text = re.sub(r'^```(?:json)?\\s*', '', response_text.strip(), flags=re.MULTILINE)\n"
    elif "re.sub(r'`\\s*$'" in line:
        lines[i] = "        response_text = re.sub(r'```\\s*$', '', response_text.strip())\n"

with open('/tmp/my_claude_biomnibench_fixed/llm_judge_qwen.py', 'w') as f:
    f.writelines(lines)

print('Fixed markdown stripping')