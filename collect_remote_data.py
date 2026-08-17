#!/usr/bin/env python3
import json, os, sys

cases = [
    ("da-12-4", "da-17-1"), ("da-17-5", "da-17-1"),
    ("da-19-4", "da-19-6"), ("da-4-7", "da-4-1"),
    ("da-14-8", "da-14-1"), ("da-13-6", "da-13-5"),
    ("da-10-1", "da-6-2"), ("da-18-5", "da-18-7"),
    ("da-19-4", "da-19-3"), ("da-10-3", "da-10-1"),
    ("da-11-1", "da-6-5"), ("da-13-6", "da-13-1"),
    ("da-26-4", "da-26-2"), ("da-18-5", "da-18-1"),
    ("da-5-1", "da-26-2"), ("da-13-6", "da-13-3"),
    ("da-25-1", "da-1-3"), ("da-17-5", "da-14-3"),
    ("da-19-4", "da-19-1"), ("da-9-1", "da-9-7"),
    ("da-25-1", "da-18-7"), ("da-11-1", "da-6-2"),
    ("da-10-1", "da-6-5"), ("da-12-4", "da-12-2"),
]

os.chdir("/data/yjh/skill-transfer-eval")

for src, tgt in cases:
    d = "transfer_pruned/" + tgt + "_pruned_transfer_" + src + "_to_" + tgt
    rs_path = d + "/logs/run_summary.json"
    if os.path.exists(rs_path):
        data = json.load(open(rs_path))
        print("DATA|" + src + "->" + tgt)
        print(json.dumps(data, indent=2))
        print("ENDDATA")
    else:
        found = False
        if os.path.isdir("transfer_pruned"):
            for x in os.listdir("transfer_pruned"):
                if tgt in x and src in x:
                    rs2 = "transfer_pruned/" + x + "/logs/run_summary.json"
                    if os.path.exists(rs2):
                        data = json.load(open(rs2))
                        print("DATA|" + src + "->" + tgt + "|ALT=" + x)
                        print(json.dumps(data, indent=2))
                        print("ENDDATA")
                        found = True
                        break
        if not found:
            print("DATA|" + src + "->" + tgt + "|NOT_FOUND")
            print("ENDDATA")