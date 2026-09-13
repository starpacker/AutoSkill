#!/usr/bin/env python3
"""
run_pruned_transfer_pipeline.py — Full pipeline for pruned-skill transfer evaluation.

Pipeline:
  1. Extract pruned skill bundles from ablation results (render command)
  2. Generalize pruned skills via LLM (task-agnostic abstraction)
  3. Deploy generalized pruned skills to target tasks
  4. Run transfer evaluation (16 pairs × pruned-skill arm)
  5. Collect results

Usage:
  python3 run_pruned_transfer_pipeline.py --step extract     # Step 1
  python3 run_pruned_transfer_pipeline.py --step generalize   # Step 2
  python3 run_pruned_transfer_pipeline.py --step deploy       # Step 3
  python3 run_pruned_transfer_pipeline.py --step evaluate     # Step 4
  python3 run_pruned_transfer_pipeline.py --step collect      # Step 5
  python3 run_pruned_transfer_pipeline.py --all               # All steps
"""

import argparse
import json
import os
import subprocess
import sys
import time
import re
from pathlib import Path

# ============================================================
# Configuration
# ============================================================
HARNESS = Path("/tmp/my_claude_biomnibench_fixed")
BUN = Path("/tmp/bun_extract/bun-linux-x64/bun")
BUNDLES = Path("/data/yjh/biomnibench-skill-bundles")
ABLATIONS = Path("/data/yjh/skill-transfer-eval/ablations")
PRUNED_BUNDLES = Path("/data/yjh/skill-transfer-eval/pruned_bundles")
GENERALIZED_DIR = Path("/data/yjh/skill-transfer-eval/generalized_skills_pruned")
DEPLOY_DIR = Path("/data/yjh/skill-transfer-eval/skills")
TRANSFER_DIR = Path("/data/yjh/skill-transfer-eval/transfer_pruned")
BASELINE_DIR = Path("/data/yjh/skill-transfer-eval/baseline")
SUMMARY_DIR = Path("/data/yjh/skill-transfer-eval/summary_pruned")
TASKS_DIR = Path("/data/yjh/biomnibench-organized")
LOG_DIR = Path("/data/yjh/skill-transfer-eval/logs")

# API config
API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("SKILL_TRANSFER_API_KEY", "")
API_URL = "https://api.gpugeek.com"
MODEL = "Vendor3/DeepSeek-V4-Flash"
JUDGE_MODEL = os.environ.get("QWEN_MODEL", "Vendor3/DeepSeek-V4-Flash")

# 16 transfer pairs (source → target)
TRANSFER_PAIRS = [
    ("da-5-1", "da-5-3"),
    ("da-18-5", "da-18-7"),
    ("da-19-4", "da-19-6"),
    ("da-9-1", "da-9-7"),
    ("da-14-8", "da-14-1"),
    ("da-15-2", "da-15-7"),
    ("da-17-5", "da-17-1"),
    ("da-13-6", "da-13-5"),
    ("da-12-4", "da-12-2"),
    ("da-4-7", "da-4-1"),
    ("da-10-3", "da-10-1"),
    ("da-11-1", "da-6-5"),
    ("da-26-4", "da-26-2"),
    ("da-4-1", "da-14-3"),
    ("da-25-1", "da-1-3"),
    ("da-10-1", "da-13-6"),
    ("da-17-5", "da-17-3"),
    ("da-15-2", "da-15-1"),
    ("da-13-6", "da-13-3"),
    ("da-19-4", "da-19-1"),
    ("da-18-5", "da-18-1"),
    ("da-10-1", "da-6-2"),

    # === Batch 2: 15 new diverse pairs (2026-07-27) ===
    # Same-category pairs (higher transfer chance)
    ("da-19-4", "da-19-3"),       # 0.6884 oncology/chromatin-profiling (same cat + same type!)
    ("da-17-5", "da-14-3"),       # 0.6474 immunology/cell-comp→association (same cat)
    ("da-13-6", "da-13-1"),       # 0.6024 metabolic/cross-cohort→diff-exp (same cat)
    ("da-4-7", "da-12-2"),        # 0.5817 oncology/tcr-repertoire→pathway (same cat)
    ("da-4-1", "da-12-2"),        # 0.5564 oncology/clustering→pathway (same cat)
    ("da-9-1", "da-1-4"),         # 0.4998 oncology/survival→association (same cat)
    ("da-15-2", "da-15-8"),       # 0.4923 neurology/co-exp→multi-omic (same cat)
    ("da-25-1", "da-18-7"),       # 0.4915 oncology/mutation→mutation (same cat + same type!)
    ("da-5-1", "da-26-2"),        # 0.4760 oncology/multi-omic→predictive (same cat)
    ("da-26-4", "da-12-2"),       # 0.4737 oncology/predictive→pathway (same cat)
    # Cross-category pairs (generalization test)
    ("da-12-4", "da-17-1"),       # 0.6063 oncology→immunology/survival→cell-comp
    ("da-14-8", "da-1-3"),        # 0.5450 immunology→oncology/association→cell-comp
    ("da-10-1", "da-6-5"),        # 0.5225 general-bio→cardiovascular/predictive→multi-omic
    ("da-11-1", "da-6-2"),        # 0.5068 immunology→cardiovascular/cell-cell→longitudinal
    ("da-10-3", "da-13-6"),       # 0.5006 general-bio→metabolic/predictive→cross-cohort
]


# ============================================================
# Step 1: Extract Pruned Skill Bundles
# ============================================================
def step_extract():
    """Extract pruned skill bundles from ablation results using render command."""
    print("=" * 70)
    print("Step 1: Extracting Pruned Skill Bundles")
    print("=" * 70)

    source_tasks = sorted(set(p[0] for p in TRANSFER_PAIRS))
    print(f"Source tasks: {len(source_tasks)}")
    for t in source_tasks:
        print(f"  {t}")

    success = 0
    skip = 0
    fail = 0

    for task in source_tasks:
        # Load ablation summary
        summary_path = ABLATIONS / task / "ablation_summary.json"
        if not summary_path.exists():
            print(f"  [SKIP] {task}: no ablation summary")
            skip += 1
            continue

        data = json.loads(summary_path.read_text())
        status = data.get("status", "")
        if status not in ("completed_all_candidates",):
            print(f"  [SKIP] {task}: ablation not completed (status={status})")
            skip += 1
            continue

        drop_ops = data.get("accepted_drop_ops", [])
        if not drop_ops:
            print(f"  [SKIP] {task}: no ops to prune")
            skip += 1
            continue

        # Check if already extracted (check variant_manifest.json)
        out_dir = PRUNED_BUNDLES / task
        if out_dir.exists() and (out_dir / "variant_manifest.json").exists():
            print(f"  [SKIP] {task}: already extracted at {out_dir}")
            skip += 1
            continue

        # Run render command
        bundle_dir = BUNDLES / task
        out_dir.mkdir(parents=True, exist_ok=True)
        variant_manifest_path = out_dir / "variant_manifest.json"

        cmd = [
            str(BUN),
            "src/oracle-skills/cli.ts", "render",
            "--bundle", str(bundle_dir),
            "--out", str(out_dir),
            "--drop-ops", ",".join(drop_ops),
            "--variant-manifest-out", str(variant_manifest_path),
        ]

        print(f"  [RUN] {task}: dropping {len(drop_ops)} ops...", end=" ", flush=True)
        result = subprocess.run(
            cmd, cwd=str(HARNESS),
            capture_output=True, text=True, timeout=120
        )

        # Check output files — render may exit non-zero despite creating files
        if variant_manifest_path.exists():
            v = json.loads(variant_manifest_path.read_text())
            skill_name = v.get("skill_name", "oracle")
            skill_dir = out_dir / "skills" / skill_name
            skill_md = skill_dir / "SKILL.md"
            if skill_md.exists():
                print(f"OK ({len(v['enabled_ops'])} ops kept)")
                print(f"    SKILL.md: {len(skill_md.read_text())} chars")
                success += 1
            else:
                print(f"PARTIAL: SKILL.md not found at {skill_md}")
                print(f"  skills dir: {list((out_dir/'skills').iterdir()) if (out_dir/'skills').exists() else 'N/A'}")
                fail += 1
        else:
            print(f"FAILED: no variant_manifest.json")
            print(f"  stderr: {result.stderr[:300]}")
            fail += 1

    print(f"\nResults: {success} extracted, {skip} skipped, {fail} failed")
    return fail == 0


# ============================================================
# Step 2: Generalize Pruned Skills via LLM
# ============================================================
SYSTEM_PROMPT = """You are an expert bioinformatics skill author. Given a **source task's oracle skill** (a structured set of domain knowledge operations), you must produce a **generalized, task-agnostic skill** that captures the core analytical pattern.

## Core Principle
You are given **only one task's skill**. You must NOT assume any specific target task. Instead, **abstract the domain knowledge** so it can be applied to other similar bioinformatics problems.

## What to Do
1. **Identify the core pattern**: What kind of analysis is this? (e.g., differential expression, GWAS, ChIP-seq peak calling, survival analysis, etc.)
2. **Abstract the operations**: Make each operation describe a **general analytical step**, not the specific task. Replace concrete file names with generic placeholders.
3. **Preserve the workflow structure**: The order and dependency between operations.
4. **Keep domain-specific methods**: Statistical tests, thresholds, normalization methods, etc. These are transferable.
5. **Remove task-specific details**: Replace specific column names, gene lists, filenames with generic descriptions.

## Output Format
Use the same oracle-skill format with `<!-- ORACLE_OP_START op_XXX -->` and `<!-- ORACLE_OP_END op_XXX -->` anchors.

```yaml
---
name: generalized-pruned-{source_task}
description: Generalized skill for {analysis_pattern} — useful for similar tasks involving {domain}
---

# Generalized Skill: {Abstract Title}

## 1. Operation Name

<!-- ORACLE_OP_START op_XXX_name -->
{generalized description of what this operation does, what methods to use, what to watch out for}
<!-- ORACLE_OP_END op_XXX_name -->
```

## Rules
- 8-12 operations, matching the source's structure
- Each operation must be self-contained and independently useful
- Use concrete, transferable methods (statistical tests, thresholds, normalization)
- Only use generic placeholders for data-specific details
- Do NOT reference any specific task name, file, or dataset"""


def load_pruned_skill(task_id):
    """Load the pruned skill bundle for a task from render output."""
    pruned_dir = PRUNED_BUNDLES / task_id

    # Check for render output (variant_manifest.json)
    variant_path = pruned_dir / "variant_manifest.json"
    manifest_path = pruned_dir / "oracle_skill_manifest.json"

    if variant_path.exists():
        # Render output format
        variant = json.loads(variant_path.read_text())
        skill_name = variant.get("skill_name", "oracle")
        skill_dir = pruned_dir / "skills" / skill_name

        skill_md = ""
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md = skill_md_path.read_text()

        # Read resources
        resources = {}
        for res_file in (skill_dir / "resources").glob("*.md"):
            resources[res_file.stem] = res_file.read_text()

        # Build operations list from variant
        operations = []
        for op_id in variant.get("enabled_ops", []):
            operations.append({"id": op_id, "kind": "enabled", "title": op_id})

        return {
            "task_id": task_id,
            "manifest": variant,
            "skill_md": skill_md,
            "resources": resources,
            "operations": operations,
            "skill_name": skill_name,
        }

    elif manifest_path.exists():
        # Original pruned bundle format (from extract_min_core_skills.py)
        manifest = json.loads(manifest_path.read_text())
        skill_name = manifest.get("skill_name", f"pruned-{task_id}")
        skill_dir = pruned_dir / "skills" / skill_name

        skill_md = ""
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md = skill_md_path.read_text()
        else:
            fallback = pruned_dir / "skills" / "oracle" / "SKILL.md"
            if fallback.exists():
                skill_md = fallback.read_text()

        resources = {}
        for op in manifest.get("operations", []):
            for res_rel in op.get("resources", []):
                res_path = skill_dir / res_rel
                if res_path.exists():
                    resources[op["id"]] = res_path.read_text()

        return {
            "task_id": task_id,
            "manifest": manifest,
            "skill_md": skill_md,
            "resources": resources,
            "operations": manifest.get("operations", []),
            "skill_name": skill_name,
        }

    # Fallback: use original oracle bundle (for tasks where no ops were pruned)
    bundle_dir = BUNDLES / task_id
    manifest_path = bundle_dir / "oracle_skill_manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text())
        skill_name = manifest.get("skill_name", f"oracle-{task_id}")
        skill_dir = bundle_dir / "skills" / skill_name
        skill_md = ""
        skill_md_path = skill_dir / "SKILL.md"
        if skill_md_path.exists():
            skill_md = skill_md_path.read_text()
        resources = {}
        for op in manifest.get("operations", []):
            for res_rel in op.get("resources", []):
                res_path = skill_dir / res_rel
                if res_path.exists():
                    resources[op["id"]] = res_path.read_text()
        return {
            "task_id": task_id,
            "manifest": manifest,
            "skill_md": skill_md,
            "resources": resources,
            "operations": manifest.get("operations", []),
            "skill_name": skill_name,
            "note": "Using full oracle bundle (no ops were pruned)"
        }

    return None


def call_llm(system_prompt, user_prompt):
    """Call DeepSeek-V4-Flash via gpugeek API."""
    import requests
    headers = {
        "Content-Type": "application/json",
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    }

    payload = {
        "model": MODEL,
        "max_tokens": 8000,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    MAX_RETRIES = 3
    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(f"{API_URL}/v1/messages", headers=headers, json=payload, timeout=300)
            resp.raise_for_status()
            data = resp.json()
            if "content" in data and len(data["content"]) > 0:
                return data["content"][0].get("text", "")
            raise ValueError(f"Unexpected response: {json.dumps(data)[:300]}")
        except Exception as e:
            if attempt < MAX_RETRIES - 1:
                wait = 2 ** (attempt + 3)
                print(f"  ⚠ Attempt {attempt+1} failed: {e}, retrying in {wait}s...")
                time.sleep(wait)
            else:
                raise


def build_generalize_prompt(source):
    """Build the user prompt with ONLY source skill info."""
    source_ops_text = ""
    for op in source["operations"]:
        source_ops_text += f"  - {op['id']}: {op.get('title', op['id'])}\n"

    # Format resources
    resources_text = ""
    for res_id, res_text in source["resources"].items():
        resources_text += f"\n#### {res_id}\n```\n{res_text[:2000]}\n```\n"

    prompt = f"""## Source Task: {source['task_id']}

### Source Pruned Skill: {source['skill_name']}

**Operations ({len(source['operations'])} total):**
{source_ops_text}

### Source SKILL.md:
```markdown
{source['skill_md']}
```

### Source Resources:
{resources_text}

## Task

Generalize this pruned oracle skill into a **task-agnostic, domain-abstracted skill**.

CRITICAL RULES:
1. You know NOTHING about any target task — this is a pure abstraction exercise.
2. Keep transferable methods (statistical tests, normalization, thresholds).
3. Replace task-specific details with generic placeholders.
4. Preserve the operation structure, count, and ordering.
5. Each operation must be independently useful.
6. Output ONLY the SKILL.md content (with YAML frontmatter).
"""
    return prompt


def parse_skill_md(text):
    """Extract SKILL.md content from LLM response."""
    yaml_pattern = r'^---\s*\n.*?\n---\s*\n'
    if re.search(yaml_pattern, text, re.DOTALL):
        return text
    code_match = re.search(r'```(?:yaml|markdown)?\s*\n(.*?)\n```', text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()
    return text.strip()


def generalize_pruned(source_task, dry_run=False):
    """Generalize a single pruned source skill."""
    print(f"\n{'='*60}")
    print(f"Generalizing pruned: {source_task}")
    print(f"{'='*60}")

    source = load_pruned_skill(source_task)
    if source is None:
        print(f"❌ No pruned bundle for {source_task}")
        return False

    print(f"  Source: {source['task_id']}")
    print(f"  Skill name: {source['skill_name']}")
    print(f"  Operations: {len(source['operations'])}")
    print(f"  SKILL.md: {len(source['skill_md'])} chars")
    print(f"  Resources: {len(source['resources'])} files")

    prompt = build_generalize_prompt(source)
    print(f"  Prompt: {len(prompt)} chars")

    if dry_run:
        print("\n⚠ DRY RUN — not calling API")
        return True

    print(f"\n  Calling DeepSeek-V4-Flash...")
    start = time.time()
    try:
        response = call_llm(SYSTEM_PROMPT, prompt)
        elapsed = time.time() - start
        print(f"  Response received: {len(response)} chars in {elapsed:.1f}s")
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

    skill_md = parse_skill_md(response)

    out_dir = GENERALIZED_DIR / source_task
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "SKILL.md").write_text(skill_md)
    print(f"  ✅ Saved: SKILL.md ({len(skill_md)} chars)")

    metadata = {
        "source_task": source_task,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL,
        "n_operations": len(source["operations"]),
        "skill_md_length": len(skill_md),
        "elapsed_seconds": round(elapsed, 1),
    }
    (out_dir / "metadata.json").write_text(json.dumps(metadata, indent=2))
    (out_dir / "raw_response.txt").write_text(response)

    return True


def step_generalize(dry_run=False):
    """Generalize all pruned skills."""
    print("=" * 70)
    print("Step 2: Generalizing Pruned Skills (task-agnostic)")
    print("=" * 70)

    source_tasks = sorted(set(p[0] for p in TRANSFER_PAIRS))
    print(f"Tasks to generalize: {len(source_tasks)}")
    for t in source_tasks:
        print(f"  {t}")

    results = []
    for task in source_tasks:
        success = generalize_pruned(task, dry_run=dry_run)
        results.append({"task": task, "success": success})
        if not dry_run:
            time.sleep(2)

    successes = sum(1 for r in results if r["success"])
    print(f"\nComplete: {successes}/{len(results)} succeeded")
    return successes == len(results)


# ============================================================
# Step 3: Deploy Generalized Pruned Skills
# ============================================================
def step_deploy():
    """Deploy generalized pruned skills to target tasks."""
    print("=" * 70)
    print("Step 3: Deploying Generalized Pruned Skills to Target Tasks")
    print("=" * 70)

    if not GENERALIZED_DIR.exists():
        print("❌ No generalized pruned skills found")
        return False

    n_deployed = 0
    for s, t in TRANSFER_PAIRS:
        gen_dir = GENERALIZED_DIR / s
        skill_path = gen_dir / "SKILL.md"
        if not skill_path.exists():
            print(f"  ⚠ No generalized skill for {s}, skipping {s}→{t}")
            continue

        deploy_target = DEPLOY_DIR / t / "skills" / "generalized-pruned-transfer"
        deploy_target.mkdir(parents=True, exist_ok=True)
        (deploy_target / "SKILL.md").write_text(skill_path.read_text())

        meta = {
            "source_task": s,
            "target_task": t,
            "deployed_at": time.strftime("%Y%m%d_%H%M%S"),
            "generalized_skill_source": str(gen_dir),
        }
        (deploy_target / "metadata.json").write_text(json.dumps(meta, indent=2))

        n_deployed += 1
        print(f"  ✅ {s} → {t}")

    print(f"\nDeployed: {n_deployed}/{len(TRANSFER_PAIRS)} skills")
    return n_deployed > 0


# ============================================================

# ============================================================
# Step 3.5: Compute Task Similarity (optional pre-filter)
# ============================================================
def step_similarity(threshold=0.4, use_llm=False, dry_run=False):
    """Compute task similarity for all 16 pairs and filter out low-similarity pairs."""
    print("=" * 70)
    print("Step 3.5: Computing Task Similarity")
    print("=" * 70)

    from compute_task_similarity import compute_similarity, read_task_readme, extract_task_features, compute_structural_similarity, OUTPUT_DIR

    SIM_DIR = OUTPUT_DIR
    SIM_DIR.mkdir(parents=True, exist_ok=True)

    print(f"Threshold: {threshold}")
    print(f"LLM-based: {use_llm}")
    print()

    results = []
    filtered_pairs = []

    for s, t in TRANSFER_PAIRS:
        sim = compute_similarity(s, t, use_llm=use_llm)
        cs = sim.get("combined_score", 0)
        if isinstance(cs, (int, float)) and cs >= threshold:
            verdict = "GO"
            filtered_pairs.append((s, t))
        else:
            verdict = "NO-GO"
        sim["verdict"] = verdict
        results.append(sim)

        print(f"  {s} -> {t}: structural={sim.get('structural_score',0):.3f} "
              f"llm={sim.get('llm_similarity', sim.get('structural_score',0)):.3f} "
              f"combined={cs:.3f} -> {verdict}")

    # Save results
    sim_file = SIM_DIR / "pipeline_similarity_filter.json"
    with open(sim_file, "w") as f:
        json.dump({
            "threshold": threshold,
            "use_llm": use_llm,
            "total_pairs": len(TRANSFER_PAIRS),
            "go_pairs": len(filtered_pairs),
            "no_go_pairs": len(TRANSFER_PAIRS) - len(filtered_pairs),
            "results": results,
            "filtered_pairs": filtered_pairs,
        }, f, indent=2)
    print(f"\nSimilarity results saved to: {sim_file}")
    print(f"GO: {len(filtered_pairs)} pairs | NO-GO: {len(TRANSFER_PAIRS) - len(filtered_pairs)} pairs")
    print(f"\nFILTERED TRANSFER PAIRS (will be evaluated):")
    for s, t in filtered_pairs:
        print(f"  {s} -> {t}")

    if filtered_pairs != TRANSFER_PAIRS:
        skipped = [p for p in TRANSFER_PAIRS if p not in filtered_pairs]
        print(f"\nSKIPPED PAIRS (below threshold):")
        for s, t in skipped:
            print(f"  {s} -> {t}")

    return filtered_pairs


# Step 4: Run Transfer Evaluation
# ============================================================
def step_evaluate(concurrency=4, reps=1, dry_run=False, filtered_pairs=None):
    """Run transfer evaluation for all 16 pairs."""
    print("=" * 70)
    print("Step 4: Running Transfer Evaluation")
    print("=" * 70)

    TRANSFER_DIR.mkdir(parents=True, exist_ok=True)
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    pairs_to_run = filtered_pairs if filtered_pairs is not None else TRANSFER_PAIRS
    n_total = len(pairs_to_run) * reps
    print(f"Total evaluations: {n_total} ({len(pairs_to_run)} pairs × {reps} rep{'s' if reps > 1 else ''})")
    print(f"Concurrency: {concurrency}")
    print(f"Model: {MODEL}")

    if dry_run:
        print("\n⚠ DRY RUN — showing launch commands only")
        for s, t in pairs_to_run:
            ts = f"pruned_transfer_{s}_to_{t}"
            skill_dir = DEPLOY_DIR / t / "skills" / "generalized-pruned-transfer"
            has_skill = "✓" if (skill_dir / "SKILL.md").exists() else "✗"
            print(f"  [{has_skill}] {s} → {t}: --timestamp {ts}")
        return True

    env = os.environ.copy()
    env["ANTHROPIC_API_KEY"] = API_KEY
    env["ANTHROPIC_BASE_URL"] = API_URL
    env["ANTHROPIC_MODEL"] = MODEL
    env["QWEN_API_KEY"] = API_KEY
    env["QWEN_BASE_URL"] = f"{API_URL}/v1"
    env["QWEN_MODEL"] = JUDGE_MODEL

    pids = {}
    completed = 0
    failed = 0

    for s, t in pairs_to_run:
        # Wait for slot
        while len(pids) >= concurrency:
            new_pids = {}
            for pid, info in pids.items():
                poll = subprocess.Popen.poll(pid)
                if poll is None:
                    new_pids[pid] = info
                else:
                    if poll != 0:
                        failed += 1
                        print(f"  [FAIL] {info['source']}→{info['target']}: exit={poll}")
                    else:
                        completed += 1
                        print(f"  [DONE] {info['source']}→{info['target']}")
            pids = new_pids
            if len(pids) >= concurrency:
                time.sleep(10)

        ts = f"pruned_transfer_{s}_to_{t}"
        run_dir = TRANSFER_DIR / f"{t}_{ts}"
        log_file = LOG_DIR / f"{ts}.log"

        skill_dir = DEPLOY_DIR / t / "skills" / "generalized-pruned-transfer"
        skill_args = []
        if (skill_dir / "SKILL.md").exists():
            skill_args = [
                "--enable-skills",
                "--skills-dir", str(DEPLOY_DIR / t / "skills"),
                "--skill-name", "generalized-pruned-transfer",
                "--max-active-skills", "1",
            ]
        else:
            print(f"  ⚠ {s}→{t}: no skill deployed, running vanilla")

        cmd = [
            str(BUN),
            "src/harness/evaluation/cli.ts",
            "--task", t,
            "--tasks-dir", str(TASKS_DIR),
            "--runs-dir", str(TRANSFER_DIR),
            "--max-rounds", "5",
            "--timeout-seconds", "7200",
            "--concurrency", "1",
            "--temperature", "1",
            "--thinking", "disabled",
            "--timestamp", ts,
            "--quiet",
        ] + skill_args

        print(f"  [LAUNCH] {s}→{t}", flush=True)
        proc = subprocess.Popen(
            cmd, cwd=str(HARNESS), env=env,
            stdout=open(log_file, 'w'), stderr=subprocess.STDOUT
        )
        pids[proc] = {"source": s, "target": t, "timestamp": ts}
        time.sleep(2)

    # Wait for all remaining
    while pids:
        new_pids = {}
        for pid, info in pids.items():
            poll = subprocess.Popen.poll(pid)
            if poll is None:
                new_pids[pid] = info
            else:
                if poll != 0:
                    failed += 1
                    print(f"  [FAIL] {info['source']}→{info['target']}: exit={poll}")
                else:
                    completed += 1
                    print(f"  [DONE] {info['source']}→{info['target']}")
        pids = new_pids
        if pids:
            time.sleep(30)

    print(f"\nComplete: {completed} done, {failed} failed out of {n_total}")
    return failed == 0


# ============================================================
# Step 5: Collect Results
# ============================================================
def step_collect():
    """Collect all transfer evaluation results."""
    print("=" * 70)
    print("Step 5: Collecting Results")
    print("=" * 70)

    SUMMARY_DIR.mkdir(parents=True, exist_ok=True)

    results = {"pairs": []}

    for s, t in TRANSFER_PAIRS:
        pattern = f"{t}_pruned_transfer_{s}_to_{t}*"
        run_dirs = sorted(TRANSFER_DIR.glob(pattern))

        rewards = []
        for rd in run_dirs:
            summary_file = rd / "logs" / "run_summary.json"
            if summary_file.exists():
                try:
                    data = json.loads(summary_file.read_text())
                    reward = data.get("reward", None)
                    if reward is not None:
                        rewards.append(reward)
                except:
                    pass

        print(f"  {s}→{t}: {len(rewards)} results, rewards={rewards}")

        results["pairs"].append({
            "source": s,
            "target": t,
            "pruned_transfer": rewards,
        })

    results_path = SUMMARY_DIR / "transfer_pruned_results.json"
    results_path.write_text(json.dumps(results, indent=2))
    print(f"\nSaved: {results_path}")
    return True


# ============================================================
# Main
# ============================================================
def main():
    parser = argparse.ArgumentParser(description="Pruned Skill Transfer Pipeline")
    parser.add_argument("--step", choices=["extract", "generalize", "deploy", "similarity", "evaluate", "collect"],
                        help="Which step to run")
    parser.add_argument("--all", action="store_true", help="Run all steps")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no API calls or evaluation")
    parser.add_argument("--concurrency", type=int, default=4, help="Max concurrent evaluations")
    parser.add_argument("--similarity", action="store_true", help="Compute similarity and filter before evaluate")
    parser.add_argument("--similarity-threshold", type=float, default=0.4, help="Minimum similarity score for GO decision")
    parser.add_argument("--similarity-llm", action="store_true", help="Use LLM for similarity (slower but more accurate)")
    parser.add_argument("--reps", type=int, default=1, help="Repetitions per pair")
    parser.add_argument("--pairs", type=str, default=None,
                        help='Comma-separated source:target list (e.g. da-5-1:da-5-3,da-18-5:da-18-7). Overrides TRANSFER_PAIRS if provided.')

    args = parser.parse_args()

    if args.all:
        step_extract() or sys.exit(1)
        step_generalize(dry_run=args.dry_run) or sys.exit(1)
        step_deploy() or sys.exit(1)
        if args.similarity:
            filtered = step_similarity(threshold=args.similarity_threshold, use_llm=args.similarity_llm)
            step_evaluate(concurrency=args.concurrency, reps=args.reps, dry_run=args.dry_run, filtered_pairs=filtered) or sys.exit(1)
        else:
            step_evaluate(concurrency=args.concurrency, reps=args.reps, dry_run=args.dry_run) or sys.exit(1)
        step_collect()
    elif args.step == "extract":
        step_extract()
    elif args.step == "generalize":
        step_generalize(dry_run=args.dry_run)
    elif args.step == "deploy":
        step_deploy()
    elif args.step == "similarity":
        step_similarity(threshold=args.similarity_threshold, use_llm=args.similarity_llm)
    elif args.step == "evaluate":
        filtered = None
        if args.pairs:
            filtered = []
            for pair in args.pairs.split(','):
                s, t = pair.split(':')
                filtered.append((s.strip(), t.strip()))
            print(f'Using custom pairs ({len(filtered)}): {filtered}')
        step_evaluate(concurrency=args.concurrency, reps=args.reps, dry_run=args.dry_run, filtered_pairs=filtered)
    elif args.step == "collect":
        step_collect()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
