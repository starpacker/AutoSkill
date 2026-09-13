# Server-side validation

The control layer was exercised on `server1` (host `s3090`) against the
external BioMniBench assets. The following commands completed successfully:

```text
python3 generalize_skill_v2.py --source da-17-1 --dry-run
  parsed oracle bundle: 9 operations, 9 resources, 19,815-character prompt

python3 extract_min_core_skills.py --task da-17-1 --dry-run
  read completed ablation_summary.json; identified 9 accepted drop operations

python3 -m skill_selector_v10.demo --local
  loaded 50 baselines, 16 P1 observations, 24 P2 neighbors,
  23 source-quality entries, and 50 task types; produced 18/50 recommendations

python3 run_transfer_skill_eval.py --mode within-domain --dry-run --reps 1
  enumerated all 27 within-domain transfer pairs
```

The live LLM generalization call was also attempted with the server-provided
environment credentials, but the provider returned HTTP 401. The pruning
renderer/evaluation runner requires the external Bun harness; only the
ablation-reading dry-run is therefore part of this repository validation.
These external prerequisites are deliberately not committed.
