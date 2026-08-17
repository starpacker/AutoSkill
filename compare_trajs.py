#!/usr/bin/env python3
"""Extract key trajectory events for all success cases."""
import json, os, sys

def get_trajectory_summary(filepath):
    """Return a compact summary of the trajectory."""
    events = []
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
                            cmd = str(inp[key]).replace('\n', ' ').replace('\r', '')[:150]
                            break
                events.append({'r': r, 'tool': tool, 'cmd': cmd, 'type': 'call'})
            elif t == 'tool_result':
                if not d.get('ok', True):
                    events.append({'r': d.get('round', '?'), 'tool': 'ERROR', 'cmd': str(d.get('text', ''))[:150], 'type': 'fail'})
            elif t == 'trajectory_warning':
                events.append({'r': d.get('round', '?'), 'tool': 'WARN', 'cmd': d.get('code', '') + ': ' + str(d.get('message', ''))[:100], 'type': 'warn'})
    return events

def count_rounds(filepath):
    rounds = set()
    with open(filepath) as f:
        for line in f:
            d = json.loads(line)
            r = d.get('round')
            if r is not None:
                rounds.add(r)
    return sorted(rounds)

def count_tool_calls_by_round(filepath):
    calls = {}
    with open(filepath) as f:
        for line in f:
            d = json.loads(line)
            if d.get('type') == 'tool_call':
                r = d.get('round', '?')
                if r not in calls:
                    calls[r] = []
                calls[r].append(d.get('tool', ''))
    return calls

# Pairs to analyze
pairs = [
    ("da-17-5", "da-17-1", "da-17-1_20260721_192248_baseline_rep1", "da-17-1_pruned_transfer_da-17-5_to_da-17-1"),
    ("da-19-4", "da-19-6", "da-19-6_20260721_192248_baseline_rep1", "da-19-6_pruned_transfer_da-19-4_to_da-19-6"),
    ("da-4-7", "da-4-1", "da-4-1_20260721_192248_baseline_rep1", "da-4-1_pruned_transfer_da-4-7_to_da-4-1"),
    ("da-14-8", "da-14-1", "da-14-1_20260721_192248_baseline_rep1", "da-14-1_pruned_transfer_da-14-8_to_da-14-1"),
    ("da-13-6", "da-13-5", "da-13-5_20260721_192248_baseline_rep1", "da-13-5_pruned_transfer_da-13-6_to_da-13-5"),
    ("da-10-1", "da-6-2", "da-6-2_20260721_192248_baseline_rep1", "da-6-2_pruned_transfer_da-10-1_to_da-6-2"),
    ("da-19-4", "da-19-3", "da-19-3_20260721_192248_baseline_rep1", "da-19-3_pruned_transfer_da-19-4_to_da-19-3"),
    ("da-18-5", "da-18-7", "da-18-7_20260721_192248_baseline_rep1", "da-18-7_pruned_transfer_da-18-5_to_da-18-7"),
    ("da-10-1", "da-13-6", "da-13-6_20260721_192248_baseline_rep1", "da-13-6_pruned_transfer_da-10-1_to_da-13-6"),
]

basedir = "/data/yjh/skill-transfer-eval/baseline"
transdir = "/data/yjh/skill-transfer-eval/transfer_pruned"

for source, target, base_run, trans_run in pairs:
    print(f"\n{'='*80}")
    print(f"=== PAIR: {source} -> {target} ===")
    print(f"{'='*80}")
    
    # Baseline
    base_path = os.path.join(basedir, base_run, "logs/trajectory.raw.jsonl")
    if os.path.exists(base_path):
        calls = count_tool_calls_by_round(base_path)
        rounds = count_rounds(base_path)
        first_tools = [calls[r][0] if r in calls else 'NONE' for r in sorted(rounds)[:3]]
        total_calls = sum(len(v) for v in calls.values())
        # Get key info
        errors = [e for e in get_trajectory_summary(base_path) if e['type'] == 'fail']
        warns = [e for e in get_trajectory_summary(base_path) if e['type'] == 'warn']
        print(f"  BASELINE: rounds={rounds}, total_calls={total_calls}")
        print(f"    First tools per round: {first_tools}")
        if warns:
            unique_warns = set(w['cmd'] for w in warns)
            for w in sorted(unique_warns):
                print(f"    WARN: {w[:100]}")
        if errors:
            for e in errors[:3]:
                print(f"    ERROR: {e['cmd'][:100]}")
    else:
        print(f"  BASELINE: NOT FOUND at {base_path}")
    
    # Transfer
    trans_path = os.path.join(transdir, trans_run, "logs/trajectory.raw.jsonl")
    if os.path.exists(trans_path):
        calls = count_tool_calls_by_round(trans_path)
        rounds = count_rounds(trans_path)
        total_calls = sum(len(v) for v in calls.values())
        first_tools = [calls[r][0] if r in calls else 'NONE' for r in sorted(rounds)[:3]]
        errors = [e for e in get_trajectory_summary(trans_path) if e['type'] == 'fail']
        print(f"  TRANSFER: rounds={rounds}, total_calls={total_calls}")
        print(f"    First tools per round: {first_tools}")
        if errors:
            for e in errors[:3]:
                print(f"    ERROR: {e['cmd'][:100]}")
    else:
        print(f"  TRANSFER: NOT FOUND at {trans_path}")