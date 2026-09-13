# Skill pruning

Pruning is an ablation-driven reduction of an oracle bundle. For each operation in
the manifest, the ablation runner temporarily disables that operation and evaluates
the task. An operation is accepted for removal only when the measured score drop is
within the configured tolerance (the server experiments use the task-level
`ablation_summary.json`). The final bundle is rendered from the original manifest
minus `accepted_drop_ops`; ordering, resource references, and metadata are retained.

Run extraction with:

```bash
export SKILL_TRANSFER_ROOT=/path/to/runtime
export ORACLE_BUNDLES_DIR=/path/to/biomnibench-skill-bundles
export ABLATIONS_DIR=$SKILL_TRANSFER_ROOT/ablations
export PRUNED_BUNDLES_DIR=$SKILL_TRANSFER_ROOT/pruned_bundles
python extract_min_core_skills.py --task da-17-1 --dry-run
python extract_min_core_skills.py --all
```

The harness and Bun executable are external dependencies. This repository contains
the control logic, not private benchmark data or generated bundles.
