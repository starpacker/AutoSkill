"""Check V10 results from generalized/ directory."""
import json, os

v10_base = "/data/yjh/skill-transfer-eval/generalized"
results = {}
for d in sorted(os.listdir(v10_base)):
    dp = os.path.join(v10_base, d)
    if os.path.isdir(dp):
        tid = d.split("_")[0]
        mf = os.path.join(dp, "run_manifest.json")
        if os.path.exists(mf):
            pd = os.path.join(dp, "public")
            if os.path.isdir(pd):
                for fn in os.listdir(pd):
                    if fn.endswith(".json"):
                        try:
                            with open(os.path.join(pd, fn)) as f:
                                sd = json.load(f)
                            r = sd.get("reward", 0)
                            if r > 0:
                                results.setdefault(tid, []).append(r)
                        except:
                            pass

for t in sorted(results):
    best = max(results[t])
    all_v = [round(v, 3) for v in results[t]]
    print(f"{t}: best={best}, all={all_v}")