# LLM skill generalization

`generalize_skill_v2.py` sends only a source task's oracle (or pruned) skill to the
configured LLM. The prompt requires a task-agnostic analytical pattern, generic
placeholders instead of filenames/gene lists, explicit applicability and
non-applicability sections, and preservation of operation structure. Target-task
information is deliberately withheld to avoid feedback leakage.

```bash
export SKILL_TRANSFER_API_KEY=...
export ORACLE_BUNDLES_DIR=/path/to/bundles
export GENERALIZED_SKILLS_DIR=$SKILL_TRANSFER_ROOT/generalized_skills
python generalize_skill_v2.py --source da-17-1
python generalize_skill_v2.py --all
python generalize_skill_v2.py --source da-17-1 --dry-run
```

`run_skill_transfer_pipeline.py` composes similarity, generalization, deployment,
and evaluation. Use the v2 generator for the current applicability-aware prompt.
