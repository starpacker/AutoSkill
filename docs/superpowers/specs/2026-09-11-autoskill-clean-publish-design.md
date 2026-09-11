# AutoSkill Clean Publish Design

## Goal

Publish a minimal, reproducible AutoSkill repository containing the `my_claude`
execution contract, oracle-skill extraction, pruning, LLM generalization,
unseen-task transfer, V10 SEL training/testing, and four comparison methods:
no-skill, oracle skill, GT few-shot, and V10 SEL.

## Scope

The public repository contains source code, a small task/schema example, CLI
entry points, configuration templates, and one end-to-end README. It excludes
experiment logs, result dumps, generated skills, private judges, benchmark
data, server-specific launch scripts, and credentials.

## Architecture

`my_claude/` defines a stable harness interface: a task directory contract,
skill loading, rollout invocation, and result schema. The actual private
`my_claude_biomnibench` runtime remains an external dependency and is selected
through `AUTOSKILL_HARNESS_DIR` and `AUTOSKILL_BUN_BIN`.

`autoskill/` contains pure-Python workflow components:

- `oracle.py`: extract a task skill from a reference solution, manually or
  through an OpenAI-compatible chat endpoint.
- `prune.py`: remove redundant/low-value sections while preserving the skill
  document contract.
- `generalize.py`: ask an LLM to rewrite a source skill for a target-task
  family without leaking target answers.
- `selector/`: V10 SEL data model, compatibility tiers, and three-phase
  selection (direct observation, nearest neighbor, confidence fallback).
- `transfer.py`: unified runners for the four evaluation arms and result
  indexing/comparison.

`scripts/` provides small command-line wrappers. All commands accept explicit
paths and use environment variables for secrets. `tasks/example/` documents the
task format without publishing private benchmark data.

## Data Flow

1. Convert or prepare tasks in the documented task schema.
2. Run the no-skill baseline through the harness adapter.
3. Extract and optionally prune an oracle skill; run the oracle arm.
4. Generalize source skills with an LLM and store only generated artifacts
   outside the source tree.
5. Build V10 training data from baseline/transfer records, train the selector,
   and select skills for unseen targets.
6. Run GT few-shot and V10 SEL transfer arms.
7. Aggregate rewards into a comparison table.

## Safety and Reproducibility

No source file contains API keys, personal access tokens, absolute server
paths, or private judge data. Missing credentials fail with an actionable
message. The default mode is dry-run for remote execution; real evaluation
requires an explicit `--execute` flag and a configured external harness.

## Validation

The publish gate is `git diff --check`, Python compilation/import checks,
CLI `--help` checks, a selector unit smoke test, and a repository secret scan.
