# Reproducibility and scope

This repository is the public experiment/control layer extracted from the complete
server implementation. The BioMniBench task directories, oracle bundles, Claude
runtime, Bun binary, judge service, raw trajectories, and private evaluation files
are external inputs and are intentionally not published.

Set the paths before running:

```bash
cp .env.example .env
export SKILL_TRANSFER_ROOT=$PWD/runtime
export BIOMNIBENCH_TASKS_DIR=/external/biomnibench-organized
export ORACLE_BUNDLES_DIR=/external/biomnibench-skill-bundles
export BIOMNIBENCH_HARNESS_DIR=/external/my_claude_biomnibench
export BUN_BIN=/usr/local/bin/bun
```

Verification:

```bash
python -m compileall -q .
python -m pytest -q
git diff --check
```

For an exact rerun, record model names, pair lists, split seed, concurrency,
temperature, judge version, and the commit hash. Do not place API keys in shell
scripts, generated batch files, git remotes, or result artifacts.
