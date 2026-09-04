"""Check metadata for all tasks."""
import os, tomllib

base = "/data/yjh/biomnibench-organized"
for tid in sorted(os.listdir(base)):
    td = os.path.join(base, tid)
    if not os.path.isdir(td):
        continue
    tf = os.path.join(td, "task.toml")
    if os.path.exists(tf):
        with open(tf, "rb") as f:
            meta = tomllib.load(f)
        m = meta.get("metadata", {})
        cat = m.get("category", "?")
        dtype = m.get("difficulty", "?")
        ttype = m.get("task_type", "?")
        lang = m.get("language", "python")
        print(f"{tid}: cat={cat} diff={dtype} type={ttype} lang={lang}")
    else:
        print(f"{tid}: NO task.toml")