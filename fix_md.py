#!/usr/bin/env python3
"""Fix the markdown code block stripping in llm_judge_qwen.py"""
filepath = '/tmp/my_claude_biomnibench_fixed/llm_judge_qwen.py'

with open(filepath, 'r') as f:
    lines = f.readlines()

for i, line in enumerate(lines):
    stripped = line.rstrip('\n')
    if stripped.strip().startswith("if response_text.strip().startswith('`')"):
        lines[i] = '    if response_text.strip().startswith("```"):\n'
    elif "re.sub(r'^`(?:json)?\\s*'" in stripped:
        lines[i] = "        response_text = re.sub(r'^```(?:json)?\\s*', '', response_text.strip(), flags=re.MULTILINE)\n"
    elif "re.sub(r'`\\s*$'" in stripped:
        lines[i] = "        response_text = re.sub(r'```\\s*$', '', response_text.strip())\n"

with open(filepath, 'w') as f:
    f.writelines(lines)

print('Fixed markdown code block stripping')