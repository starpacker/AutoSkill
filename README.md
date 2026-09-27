# AutoSkill

AutoSkill is a reproducible framework for extracting, compressing, generalizing,
and transferring agent skills across unseen biomedical analysis tasks. It keeps
the private `my_claude`/BioDSBench runtime behind a small public adapter, so the
repository contains the research framework without publishing benchmark data,
logs, private judges, or credentials.

## What is included

```text
my_claude/                 public task/skill/result contract and harness adapter
autoskill/
  oracle.py               reference-compatible oracle bundle generation
  prune.py               operation-aware variant rendering/pruning
  generalize.py          optional LLM generalization
  transfer.py            four evaluation arms and aggregation
  selector/              V10 SEL data, compatibility, training, selection
scripts/                  stable command-line entry points
tasks/example/            minimal task and skill example
tests/                    dependency-free smoke tests
```

The private `my_claude_biomnibench` runtime remains external. On `server1`, the
existing runtime can be used by setting `AUTOSKILL_HARNESS_DIR`; local commands
default to dry-run mode.

## Install and configure

```bash
git clone https://github.com/starpacker/AutoSkill.git
cd AutoSkill
python3 -m venv .venv
source .venv/bin/activate
cp .env.example .env
export PYTHONPATH="$PWD"
```

Only the optional LLM generalization step needs an API key:

```bash
export AUTOSKILL_LLM_API_KEY=...
export AUTOSKILL_LLM_BASE_URL=https://api.openai.com/v1
export AUTOSKILL_LLM_MODEL=gpt-4o-mini
```

Never put keys in source files, generated shell scripts, git remotes, or result
artifacts. The previously used GitHub token should be revoked and regenerated.

## Task format and my_claude framework

Each task is a directory with a JSON manifest, input files, and an evaluation
contract. See [`my_claude/task_schema.json`](my_claude/task_schema.json) and
[`tasks/example/task.json`](tasks/example/task.json). A task manifest identifies
the instruction, task type, maximum rounds, and judge/rubric. The external
my_claude harness executes the task and returns a reward-bearing run summary.

The adapter constructs the same command shape used by the server harness:

```bash
python -m scripts.run_eval \
  --task-id example \
  --task-dir tasks/example \
  --oracle-skill tasks/example/skill.md \
  --selected-skill tasks/example/skill.md \
  --output runs/example.json
```

This is a dry run unless `--execute` is supplied. Real execution requires
`AUTOSKILL_HARNESS_DIR`, `AUTOSKILL_BUN_BIN`, `AUTOSKILL_TASKS_DIR`, and a
working external harness installation.

## 1. No-skill baseline

Run a task with no system skill. This is the lower bound used to compute transfer
delta:

```bash
python -m scripts.run_eval --task-id example --task-dir tasks/example \
  --output runs/no_skill.json --execute
```

For a benchmark, repeat this for every target task and retain each normalized
`reward` in `results_index.json`.

## 2. Oracle skill (task-specific upper bound)

The reference implementation uses a task directory with `std_code/` as the
source root:

```text
tasks/<task-id>/
  README.md
  output_schema.json
  visible_data/
  std_code/                 # up to 40 non-ignored source files
```

Generate a bundle (including `oracle_skill_manifest.json`, `source_index.json`,
operation blocks, and resource notes) with:

```bash
python -m scripts.skill_pipeline generate-bundle \
  --task-dir tasks/task-001 \
  --output output/oracle-skills/task-001
```

The source path is therefore `tasks/task-001/std_code`, not a single
reference file. For a small standalone example, the legacy extractor remains:

```bash
python -m scripts.skill_pipeline extract \
  --reference reference_solution.py \
  --instruction "Analyze the expression matrix and report significant genes." \
  --output skills/task-001/SKILL.md
```

Evaluate the task with the generated skill as the oracle arm:

```bash
python -m scripts.run_eval --task-id task-001 --task-dir tasks/task-001 \
  --oracle-skill skills/task-001/SKILL.md --output runs/oracle.json --execute
```

## 3. Prune a skill

Pruning is operation ablation. It removes only explicit
`ORACLE_OP_START/END` operation blocks; it does not guess that headings such
as `Examples` or `Notes` are disposable:

```bash
python -m scripts.skill_pipeline render \
  --bundle output/oracle-skills/task-001 \
  --output output/oracle-skills/task-001-pruned \
  --drop-ops op_030_reference_knowledge op_040_solver_flow
```

The renderer validates operation IDs, renders the remaining blocks, copies only
their resources/scripts under stable aliases, strips internal operation
metadata, and writes a variant manifest and evaluation command. The full
server lifecycle evaluates the baseline first, optionally tries the author's
`likely_removable_ops` batch, then tests single-operation deletions in
descending `ablation_priority`; passing candidates are deleted and failing
candidates retained. Inconclusive failures may trigger the debug-skill gate.

For a standalone Markdown file, the compatibility command is:

```bash
python -m scripts.skill_pipeline prune \
  --input skills/task-001/SKILL.md \
  --output skills/task-001/SKILL.pruned.md \
  --drop-ops op_030_reference_knowledge \
  --max-lines 120
```

## 4. LLM skill generalization

Generalization rewrites a source skill for a target task family and explicitly
asks the model not to leak target answers. Without an API key, the command uses
a deterministic, safe fallback:

```bash
python -m scripts.skill_pipeline generalize \
  --input skills/task-001/SKILL.pruned.md \
  --target-type survival-analysis \
  --output skills/generalized/survival-analysis.md
```

Generated skills should be stored outside the git-tracked source tree when they
contain benchmark-specific material.

## 5. V10 SEL training and testing

V10 SEL uses three phases:

1. P1 direct observation: use a previously measured positive source-to-target
   transfer.
2. P2 nearest neighbor: reuse a source from the most similar known target.
3. P3 confidence fallback: combine baseline expectation, source quality, and
   compatibility tier.

Prepare these JSON files from held-out training runs:

```json
{"baselines": {"task-a": 42}, "transfers": [
  {"source": "task-a", "target": "task-b", "reward": 0.71,
   "type": "generalized-transfer"}
]}
```

Train the confidence model:

```bash
python -m scripts.train_selector \
  --results-index results_index.json \
  --output v7_model.json
```

Then select a skill for an unseen target. `skills.json` maps source task IDs to
their `SKILL.md` paths:

```bash
python -m scripts.select_skill \
  --target task-b \
  --skills skills.json \
  --results-index results_index.json \
  --similarity similarity_matrix.json \
  --model v7_model.json \
  --task-types task_types.json
```

The output includes the selected source and an explainable confidence score.
Compatibility groups are defined in
[`autoskill/selector/compatibility.py`](autoskill/selector/compatibility.py).
Add new task types there when adapting another benchmark.

## 6. GT few-shot and V10 transfer

The four comparison arms have a single normalized interface:

| Arm | Meaning |
| --- | --- |
| `no-skill` | Base model with no skill prompt |
| `oracle` | Task-specific oracle skill |
| `gt-few-shot` | Ground-truth source examples plus source skill |
| `v10-sel` | Skill chosen by V10 SEL for the unseen target |

Pass the selected skill to `scripts.run_eval` and aggregate outputs:

```bash
python -m scripts.run_eval --task-id task-b --task-dir tasks/task-b \
  --oracle-skill skills/task-b/SKILL.md \
  --selected-skill skills/generalized/task-b.md \
  --output runs/task-b.json --execute
python -m scripts.compare runs/task-b.json --output comparison_summary.json
```

For GT few-shot, place the source trajectory/examples in the skill file or in
the external harness's few-shot prompt directory; the public runner remains
agnostic to private data.

## End-to-end skill lifecycle

For a new source task and an unseen target, run the lifecycle in this order:

1. **Generate** an oracle skill from the trusted reference solution with
   `scripts.skill_pipeline extract`.
2. **Prune** redundant sections with `scripts.skill_pipeline prune` when prompt
   size or noise is a concern.
3. **Generalize** the pruned skill for the target task family with
   `scripts.skill_pipeline generalize`; configure `AUTOSKILL_LLM_API_KEY` for
   LLM rewriting or use the deterministic fallback.
4. **Migrate** the generalized skill to the unseen target by training V10 SEL
   on held-out baseline/transfer records (`scripts.train_selector`) and asking
   `scripts.select_skill` for the best source skill.
5. **Test** all four arms (`no-skill`, `oracle`, `gt-few-shot`, `v10-sel`) with
   `scripts.run_eval`, then summarize rewards with `scripts.compare`.

This separation prevents target answers from leaking into generalized skills and
makes every transfer decision auditable through its source task and score.

## Research artifacts and benchmark evaluations

This repository includes the reusable framework, benchmark adapters, selected
evaluation drivers, and the paper. It does not redistribute benchmark source
datasets, generated task bundles, private reference answers, run trajectories,
or model credentials. See [`experiments/README.md`](experiments/README.md) for
runner requirements and environment configuration. The [`research/`](research/)
directory contains result reports and the machine-readable
[`39-task aggregate`](research/biodsbench_r_39_aggregate.json).

| Benchmark/workflow | Included code | Evaluation scope |
| --- | --- | --- |
| BioDSBench-R | `experiments/biodsbench_r/` | No-skill, cross-benchmark SkillOpt transfer, V10 SEL, baseline3 GT few-shot, and native SkillOpt drivers |
| BioMNIBench | `skillopt_biomnibench/` | SkillOpt adapter, dataloader, and rollout integration |
| OfficeQA | `adapters/officeqa/build.py` | Task builder; private answer files and generated tasks are excluded |
| SearchQA | `adapters/searchqa/build.py` | Open-/closed-book task builder; source corpus and generated tasks are excluded |
| SpreadsheetBench | `adapters/spreadsheetbench/build.py` | Spreadsheet task builder; source workbooks and generated tasks are excluded |

The main BioDSBench-R comparison covers 39 tasks. The published grouping below
uses the primary analytical objective: generic data preparation and plotting
tasks are assigned to the downstream analysis they support, rather than kept
as broad standalone categories. $\Delta$ is the absolute pass-rate difference
in percentage points (pp).

| Task type | No Skill | SkillOpt | Ours (V10 SEL) | $\Delta$ (Ours - No Skill) |
| --- | ---: | ---: | ---: | ---: |
| Pathway enrichment | 6/10 | 8/10 | **10/10** | **+40.0 pp** |
| Expression analysis | 19/21 | 18/21 | **21/21** | **+9.5 pp** |
| Survival analysis | 2/3 | 2/3 | **3/3** | **+33.3 pp** |
| Clustering | 3/4 | 2/4 | **4/4** | **+25.0 pp** |
| Cross-cohort comparison | 0/1 | **1/1** | **1/1** | **+100.0 pp** |
| **All tasks** | **30/39 (76.9%)** | **31/39 (79.5%)** | **39/39 (100%)** | **+23.1 pp** |

Here, **SkillOpt** denotes the BioMNIBench-trained skill transferred to
BioDSBench; **Ours** denotes the BioDSBench-native V10 selector. A separate exploratory
native SkillOpt rerun scored 26/39 with 13 tasks timing out at the 3,000-second
limit after changing the model endpoint; it is not the SkillOpt transfer column
and should not be interpreted as a controlled head-to-head result.

The supplied manuscript is [`paper/Forgetting_Is_What_to_Learn__Verifier_Grounded_Minimal_Core_Skills_for_Self_Evolving_Agents.pdf`](paper/Forgetting_Is_What_to_Learn__Verifier_Grounded_Minimal_Core_Skills_for_Self_Evolving_Agents.pdf).

## Reproducing evaluations

The BioDSBench runners target an externally installed Bun/TypeScript harness
and benchmark task directory. Configure paths and credentials in the shell,
never in source files:

```bash
export SKILL_TRANSFER_DIR=/path/to/skill_transfer
export HARNESS_DIR=/path/to/my_claude_harness
export R_TASKS_DIR=/path/to/biodsbench_r/tasks
export ANTHROPIC_API_KEY=your_key
export ANTHROPIC_BASE_URL=https://api.example.com
export ANTHROPIC_MODEL=your_model
```

Use `--dry-run` where available before execution. The native disk-safe runner
supports `--workers`, `--tag`, and `--collect-only`; it checks free space before
each task, writes resumable JSON results, and removes per-task run workspaces
after collection. See [`experiments/biodsbench_r/README.md`](experiments/biodsbench_r/README.md)
for commands and prerequisites.

Benchmark data must be obtained from its original source and used under its
license/terms. Generated tasks and private judges are local evaluation assets,
not part of this public repository.

## Validation

```bash
python -m compileall -q my_claude autoskill scripts tests
python -m pytest -q tests
python -m scripts.skill_pipeline --help
python -m scripts.select_skill --help
git diff --check
```

Results are tied to the stated model endpoint, task split, harness version, and
judge. Re-run the complete evaluation under one fixed configuration before
using scores as a new controlled comparison.
