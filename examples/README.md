# BioMniBench example task

`da-17-1/` is a small, publishable task fixture containing the task metadata
and the shape of an oracle `SKILL.md`. It does not contain private datasets,
trajectories, judge outputs, or API credentials.

On a server with the external BioMniBench runtime and task bundles installed,
the following commands exercise the same control code used for the full
benchmark:

```bash
export SKILL_TRANSFER_ROOT=/data/yjh/skill-transfer-eval
export BIOMNIBENCH_TASKS_DIR=/data/yjh/biomnibench-organized
export ORACLE_BUNDLES_DIR=/data/yjh/biomnibench-skill-bundles
export BIOMNIBENCH_HARNESS_DIR=/data/yjh/my_claude_biomnibench
export BUN_BIN=bun

# Oracle skill generation is performed by the external my_claude harness.
# The checked-in control layer consumes the resulting oracle bundle.

# Pruning from completed ablation results:
python extract_min_core_skills.py --task da-17-1 --dry-run
python extract_min_core_skills.py --task da-17-1

# LLM generalization (requires a valid provider key):
python generalize_skill_v2.py --source da-17-1

# V10 SEL transfer selection and evaluation preview:
python -m skill_selector_v10.demo
python run_transfer_skill_eval.py --mode within-domain --dry-run --reps 1
```

The full data and harness remain external by design; this fixture is for
interface and workflow inspection, not a replacement benchmark dataset.
