import json, os, glob

base = "/data/yjh/skill-opt/repo/outputs/skillopt_biomnibench_gpt-5.5_20260830_165307"

print("=== ALL STEP RECORDS ===")
steps = sorted(glob.glob(os.path.join(base, "steps/step_*/step_record.json")),
               key=lambda x: int(x.split("step_")[1].split("/")[0]))
print("  Step | Ep | Epi | Action              | Score | Best | nP | Wall(s) | Skill")
print("  " + "-"*82)
for s in steps:
    d = json.load(open(s))
    patches = d.get("n_patches", 0)
    print("  %4d | %2d | %3d | %20s | %4s | %3s | %2d | %5d | %s" % (
        d["step"], d["epoch"], d["step_in_epoch"], d["action"],
        str(d["current_score"]), str(d["best_score"]),
        patches, int(d["wall_time_s"]), str(d["skill_len"])))

print()
print("=== SKILL SIZES ===")
for s in sorted(glob.glob(os.path.join(base, "skills/skill_v*.md"))):
    sz = os.path.getsize(s)
    print("  %s: %d bytes" % (os.path.basename(s), sz))

print()
print("=== SLOW_UPDATE ===")
for ep in sorted(glob.glob(os.path.join(base, "slow_update/epoch_*/"))):
    ep_name = os.path.basename(os.path.dirname(ep))
    rf = os.path.join(ep, "slow_result.json")
    if os.path.exists(rf):
        print("  %s: %s" % (ep_name, json.dumps(json.load(open(rf)))))
    else:
        print("  %s: no result yet" % ep_name)

print()
print("=== META_SKILL ===")
for ep in sorted(glob.glob(os.path.join(base, "meta_skill/epoch_*/"))):
    ep_name = os.path.basename(os.path.dirname(ep))
    rf = os.path.join(ep, "meta_skill_result.json")
    if os.path.exists(rf):
        print("  %s: %s" % (ep_name, json.dumps(json.load(open(rf)))))
    else:
        print("  %s: no result yet" % ep_name)

print()
print("=== BASELINE EVAL ===")
be = os.path.join(base, "selection_eval_baseline/runs")
if os.path.isdir(be):
    for d in sorted(os.listdir(be)):
        dp = os.path.join(be, d)
        if os.path.isdir(dp):
            for sub in sorted(os.listdir(dp)):
                sj = os.path.join(dp, sub, "logs/run_summary.json")
                if os.path.exists(sj):
                    rd = json.load(open(sj))
                    print("  %s: reward=%s status=%s" % (d, rd.get("reward"), rd.get("status")))

print()
print("=== TIME ===")
import time
print("  Current time: %s" % time.strftime("%Y-%m-%d %H:%M:%S"))