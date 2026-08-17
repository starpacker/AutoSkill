#!/usr/bin/env python3
import json, sys, os

def extract_trajectory(filepath, label):
    print(f"\n{'='*80}")
    print(f"=== {label} ===")
    print(f"{'='*80}")
    with open(filepath) as f:
        for line in f:
            d = json.loads(line)
            kind = d.get("kind","")
            if kind == "tool_call":
                r = d.get("round","?")
                t = d.get("tool","")
                inp = d.get("input",{})
                cmd = ""
                if isinstance(inp, dict):
                    if "command" in inp:
                        cmd = str(inp["command"])[:150]
                    elif "file_path" in inp:
                        cmd = str(inp["file_path"])[:150]
                    elif "code" in inp:
                        cmd = str(inp["code"])[:100]
                    elif "arguments" in inp:
                        cmd = str(inp["arguments"]).replace('\n',' ')[:150]
                print(f"R{r} {t}: {cmd}")
            elif kind == "tool_result":
                ok = d.get("ok",True)
                if not ok:
                    text = str(d.get("text",""))[:150]
                    print(f"  -> FAILED: {text}")
                elif d.get("is_retry",False):
                    print(f"  -> RETRY needed")
            elif kind == "assistant_text":
                txt = d.get("text","")[:150].replace('\n',' ')
                print(f"  ASST: {txt}")
            elif kind == "skill_check":
                print(f"  SKILL: {d.get('skill','')} -> {d.get('status','')}")
            elif kind == "run_context":
                print(f"  TASK: {d.get('task_id','')} RUN: {d.get('run_id','')}")

if __name__ == "__main__":
    for arg in sys.argv[1:]:
        if os.path.exists(arg):
            extract_trajectory(arg, os.path.basename(os.path.dirname(os.path.dirname(arg))))
        else:
            print(f"Not found: {arg}")