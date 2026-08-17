#!/usr/bin/env python3
"""Extract and compare baseline vs transfer trajectories."""
import json, sys, os

def extract_trajectory(filepath, label):
    lines = []
    lines.append('')
    lines.append('=' * 80)
    lines.append('=== ' + label + ' ===')
    lines.append('=' * 80)
    try:
        with open(filepath) as f:
            for line in f:
                d = json.loads(line)
                t = d.get('type', '')
                if t == 'tool_call':
                    r = d.get('round', '?')
                    tool = d.get('tool', '')
                    inp = d.get('input', {})
                    cmd = ''
                    if isinstance(inp, dict):
                        for key in ['command', 'file_path', 'code', 'arguments']:
                            if key in inp:
                                cmd = str(inp[key]).replace('\n', ' ').replace('\r', '')[:200]
                                break
                    lines.append('R' + str(r) + ' ' + tool + ': ' + cmd)
                elif t == 'tool_result':
                    ok = d.get('ok', True)
                    if not ok:
                        text = str(d.get('text', '')).replace('\n', ' ').replace('\r', '')[:200]
                        lines.append('  -> FAILED: ' + text)
                elif t == 'assistant_text':
                    txt = d.get('text', '').replace('\n', ' ').replace('\r', '')[:200]
                    lines.append('  ASST: ' + txt)
                elif t == 'trajectory_warning':
                    code = d.get('code', '')
                    msg = d.get('message', '').replace('\n', ' ').replace('\r', '')[:200]
                    lines.append('  WARNING [' + code + ']: ' + msg)
                elif t == 'skill_check':
                    lines.append('  SKILL: ' + d.get('skill', '') + ' -> ' + d.get('status', ''))
                elif t == 'run_context':
                    lines.append('  TASK: ' + d.get('task_id', '') + ' RUN: ' + d.get('run_id', ''))
    except Exception as e:
        lines.append('  ERROR reading file: ' + str(e))
    return '\n'.join(lines)

if __name__ == '__main__':
    for arg in sys.argv[1:]:
        if os.path.exists(arg):
            print(extract_trajectory(arg, os.path.basename(os.path.dirname(os.path.dirname(arg)))))
        else:
            print('Not found: ' + arg)