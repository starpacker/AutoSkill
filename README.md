# AutoSkill: BioMniBench skill transfer

This repository contains the clean control layer used to evaluate self-evolving
skills on BioMniBench. The source of truth is the server-side
`skill-transfer-eval` implementation; private benchmark data, trajectories,
judge outputs, and generated runs are intentionally excluded.

## Framework

1. **Oracle skill generation**: the external `my_claude`/BioMniBench harness
   generates a task-specific `SKILL.md` from successful trajectories.
2. **Generalization**: `generalize_skill.py` and `generalize_skill_v2.py` use an
   LLM to abstract one oracle skill into a task-agnostic skill. V2 adds an
   applicability section and source task type.
3. **Pruning**: `extract_min_core_skills.py` performs ablation-based deletion
   trials and keeps the smallest subset that preserves evaluation quality.
4. **Transfer**: the runners evaluate four arms: no-skill baseline, oracle-skill
   SOTA control, ground-truth few-shot transfer, and generalized/V10 SEL transfer.
5. **V10 SEL**: `skill_selector_v10/` implements P1 direct observations, P2
   nearest-neighbor transfer, and P3 quality/compatibility fallback.

## Layout

```text
generalize_skill*.py              LLM skill generalization
extract_min_core_skills.py        pruning by ablation
run_*transfer*.py                 transfer/evaluation runners
compute_*similarity.py            skill/task similarity
collect_results.py                result collection
skill_selector_v10/               V10 SEL selector and scripts
skillopt/envs/biomnibench/        optional SkillOpt adapter/reference
docs/                             protocol and reproducibility notes
```

## Reproduce

The benchmark harness and task data are external. Set paths and credentials
without committing them:

```bash
cp .env.example .env
export SKILL_TRANSFER_ROOT=/path/to/skill-transfer-eval
export BIOMNIBENCH_TASKS_DIR=/path/to/biomnibench-organized
export ORACLE_BUNDLES_DIR=/path/to/biomnibench-skill-bundles
export BIOMNIBENCH_HARNESS_DIR=/path/to/my_claude_biomnibench
export BUN_BIN=/path/to/bun
export ANTHROPIC_API_KEY=...
# BioMniBench launchers may instead export API_KEY and BASE_URL; the
# generalization runner accepts both naming conventions.
```

Typical commands:

```bash
python generalize_skill_v2.py --source da-17-1
python extract_min_core_skills.py --task da-17-1
python run_pruned_transfer_pipeline.py --help
python run_transfer_skill_eval.py --mode all --dry-run
python -m skill_selector_v10.demo --local   # on server1; omit --local from a workstation
python collect_results.py
```

See `docs/` for the exact pruning protocol, transfer arms, V10 SEL training
and testing split, and leakage-control notes.

## Reproducibility and scope

The repository publishes framework code and documentation only. It does not
publish raw trajectories, private judge data, generated outputs/logs, API
tokens, or the external BioMniBench runtime. The `skillopt` files are an
adapter/reference subset and require the upstream SkillOpt runtime for full
training.
