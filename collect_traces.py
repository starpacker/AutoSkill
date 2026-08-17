#!/usr/bin/env python3
"""Collect trace reports, skill files, and skill_application records for deep analysis."""
import json, os

os.chdir("/data/yjh/skill-transfer-eval")

# Key cases: those needing deeper analysis
key_cases = [
    # Case 2 - the one user specifically complained about
    ("da-12-4", "da-17-1", "Cross-domain baseline=0 rescue"),
    # Other success cases
    ("da-17-5", "da-17-1", "Same-type baseline=0 rescue"),
    ("da-19-4", "da-19-6", "Perfect match"),
    ("da-4-7", "da-4-1", "Cross-type framework reuse"),
    ("da-14-8", "da-14-1", "Cross-type framework reuse"),
    ("da-13-6", "da-13-5", "Same-type direct reuse"),
    ("da-10-1", "da-6-2", "Cross-domain generic"),
    # Top failures
    ("da-10-3", "da-10-1", "Worst failure -30%"),
    ("da-13-6", "da-13-1", "Failure -26%"),
    ("da-11-1", "da-6-5", "Cross-domain failure -25%"),
    ("da-26-4", "da-26-2", "Same-type failure -20%"),
    ("da-18-5", "da-18-1", "Failure -18%"),
]

for src, tgt, note in key_cases:
    d = "transfer_pruned/" + tgt + "_pruned_transfer_" + src + "_to_" + tgt
    print("=" * 80)
    print("CASE|" + src + "->" + tgt + "|" + note)
    print("=" * 80)
    
    # 1. Trace report
    trace_path = d + "/outputs/trace.md"
    if os.path.exists(trace_path):
        with open(trace_path) as f:
            content = f.read()
        print("TRACE|" + src + "->" + tgt + "|len=" + str(len(content)))
        print(content[:5000])
        print("...TRUNCATED..." if len(content) > 5000 else "")
        print("ENDTRACE")
    else:
        print("TRACE|NOT_FOUND")
    
    # 2. Skill application record
    sa_path = d + "/workspace/skill_application.json"
    if os.path.exists(sa_path):
        with open(sa_path) as f:
            content = f.read()
        print("SKILLAPP|" + src + "->" + tgt)
        print(content[:2000])
        print("ENDSKILLAPP")
    else:
        print("SKILLAPP|NOT_FOUND")
    
    # 3. Answer file
    ans_path = d + "/outputs/answer.txt"
    if os.path.exists(ans_path):
        with open(ans_path) as f:
            content = f.read()
        print("ANSWER|" + src + "->" + tgt + "|len=" + str(len(content)))
        print(content[:3000])
        print("...TRUNCATED..." if len(content) > 3000 else "")
        print("ENDANSWER")
    
    print()