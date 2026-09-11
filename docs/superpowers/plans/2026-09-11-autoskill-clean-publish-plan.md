# AutoSkill Clean Publish Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build and publish a clean AutoSkill repository with the requested skill-transfer workflows.

**Architecture:** Keep the external `my_claude` runtime behind a small local adapter contract. Implement oracle, prune, generalization, V10 selection, transfer arms, and comparison aggregation as dependency-light Python modules with explicit CLI entry points.

**Tech Stack:** Python 3.9+, standard library, optional OpenAI-compatible HTTP API, external Bun/TypeScript harness for real evaluations.

---

### Task 1: Public repository skeleton

**Files:**
- Create: `README.md`, `.env.example`, `.gitignore`
- Create: `my_claude/`, `autoskill/`, `tasks/example/`, `scripts/`

- [ ] Add package markers and configuration documentation.
- [ ] Add a minimal example task manifest and skill schema.
- [ ] Verify all new files are ASCII and contain no secrets.

### Task 2: Harness contract

**Files:**
- Create: `my_claude/contract.py`
- Create: `my_claude/runner.py`
- Create: `my_claude/__init__.py`

- [ ] Define task, skill, and result dataclasses.
- [ ] Implement dry-run and external-harness command construction.
- [ ] Reject missing required configuration with clear errors.

### Task 3: Skill lifecycle

**Files:**
- Create: `autoskill/oracle.py`
- Create: `autoskill/prune.py`
- Create: `autoskill/generalize.py`
- Create: `scripts/skill_pipeline.py`

- [ ] Implement deterministic extraction fallback.
- [ ] Implement section-aware pruning.
- [ ] Implement optional OpenAI-compatible generalization.
- [ ] Add CLI subcommands for extract, prune, and generalize.

### Task 4: V10 SEL

**Files:**
- Create: `autoskill/selector/config.py`
- Create: `autoskill/selector/data.py`
- Create: `autoskill/selector/compatibility.py`
- Create: `autoskill/selector/v10.py`
- Create: `scripts/select_skill.py`

- [ ] Load baselines, transfer observations, similarity, and model JSON.
- [ ] Implement P1/P2/P3 selection and compatibility thresholds.
- [ ] Support local JSON and remote SSH reads without embedding paths.
- [ ] Add selection CLI with explainable output.

### Task 5: Evaluation arms and comparison

**Files:**
- Create: `autoskill/transfer.py`
- Create: `scripts/run_eval.py`
- Create: `scripts/compare.py`

- [ ] Implement no-skill, oracle, GT few-shot, and V10 SEL arm specs.
- [ ] Generate harness commands in dry-run mode.
- [ ] Execute only with explicit flag and collect normalized results.
- [ ] Aggregate a comparison CSV/JSON.

### Task 6: README and validation

**Files:**
- Modify: `README.md`
- Create: `tests/test_selector.py`

- [ ] Document installation, configuration, task schema, all workflows, V10 training/testing, and unseen transfer.
- [ ] Add smoke tests for compatibility, pruning, and selector behavior.
- [ ] Run compile, import, CLI, diff, and secret checks.
- [ ] Commit and push to `origin/main`.
