# Server-side validation

The control layer was exercised on `server1` (host `s3090`) against the
external BioMniBench assets. The following commands completed successfully:

```text
python3 generalize_skill_v2.py --source da-17-1
  live gateway response 200; generated 13,142-character SKILL.md

python3 extract_min_core_skills.py --task da-17-1
  Bun renderer completed; generated pruned_bundles/da-17-1/skills/.../SKILL.md
  control-plane manifest was written beside (not inside) the solver skill

python3 -m skill_selector_v10.demo --local
  loaded 50 baselines, 16 P1 observations, 24 P2 neighbors,
  23 source-quality entries, and 50 task types; produced 18/50 recommendations
  selected da-19-3 for da-8-3 (P2, compatible tier, score 0.1293)
```

The selected V10 skill was deployed to
`skills/da-8-3/skills/v10-selector-da-19-3` and evaluated with the real Bun
harness. The agent completed the solver and produced `outputs/answer.txt` and
`outputs/trace.md`. The retry explicitly configured the requested
`Vendor3/DeepSeek-V4-Flash` judge (confirmed in `run_metadata`); that run
reached the agent/solver stage but timed out before judge scoring, with
`rounds=0` and `reward=0`. The earlier `Vendor2/Gemini-3-flash` attempt
returned provider error 400 (`Invalid token`). Neither outcome is reported as
a successful final reward.

A separate generalized `da-17-1 → da-17-3` run also entered the real solver but
hit the 900-second evaluation timeout while processing the 1.26-million-cell
single-cell dataset. These outcomes are recorded explicitly: framework launch,
skill injection, Bun execution, and solver entry were verified; final reward
requires the solver to finish within the configured timeout and then reach the
judge.
