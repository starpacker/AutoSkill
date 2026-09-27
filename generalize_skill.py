#!/usr/bin/env python3
"""
generalize_skill.py

Use DeepSeek-V4-Flash (via gpugeek API) to generalize a source task's oracle skill
into a **task-agnostic**, **domain-abstracted** skill.

CRITICAL: The LLM receives ONLY the source task's oracle skill. It does NOT know
anything about any target task. The goal is to distill the core domain knowledge
and analysis pattern into a reusable form that can transfer to other tasks.

Usage:
  python3 generalize_skill.py --source da-17-1
  python3 generalize_skill.py --all                           # all source tasks
  python3 generalize_skill.py --source da-17-1 --dry-run      # preview only
"""

import json, os, sys, time, re, argparse
from pathlib import Path

# API Configuration
API_URL = "https://api.gpugeek.com/v1/messages"
API_KEY = os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("SKILL_TRANSFER_API_KEY", "")
MODEL = os.environ.get("SKILL_GEN_MODEL", "Vendor3/DeepSeek-V4-Flash")
MAX_TOKENS = 8000
MAX_RETRIES = 3

BUNDLES_DIR = Path(os.environ.get("ORACLE_BUNDLES_DIR", "runtime/oracle_bundles"))
OUTPUT_DIR = Path(os.environ.get("SKILL_TRANSFER_ROOT", "runtime")) / "generalized_skills"

# Source tasks that need generalization
SOURCE_TASKS = [
    # Existing pairs (all 8 already generated)
    "da-5-1",   # → da-5-3:  PDAC target prioritization
    "da-8-1",   # → da-8-3:  Bread-spiker classification
    "da-13-5",  # → da-13-6: Sex-associated overlap
    "da-17-1",  # → da-17-5: SLE ancestry composition
    "da-18-5",  # → da-18-7: MAPK/ESR1 exclusivity
    "da-19-3",  # → da-19-4: RUNX1 peak analysis
    "da-19-4",  # → da-19-6: H3K27ac ChIP-seq
    "da-26-2",  # → da-26-4: Biomarker identification
    # Within-domain new sources (training tasks for verification set)
    "da-1-3",   # → da-1-4:  spatiotemporal single-cell
    "da-4-1",   # → da-4-7:  NSCLC single-cell atlas
    "da-4-6",   # → da-4-7:  NSCLC single-cell atlas
    "da-8-2",   # → da-8-3:  glycemic responses
    "da-13-1",  # → da-13-5, da-13-6: plasma proteome
    "da-13-3",  # → da-13-5, da-13-6: plasma proteome
    "da-14-1",  # → da-14-8: immune dysregulation
    "da-14-3",  # → da-14-8: immune dysregulation
    "da-15-1",  # → da-15-7, da-15-8: ALS transcriptomic
    "da-15-2",  # → da-15-7, da-15-8: ALS transcriptomic
    "da-18-1",  # → da-18-7: breast cancer genomics
    "da-19-1",  # → da-19-4, da-19-6: chromatin profiling
    "da-20-1",  # → da-20-4: general biology
    "da-20-3",  # → da-20-4: general biology
    # Cross-domain sources
    "da-6-2",   # → da-20-4: cardiovascular exercise dynamics
]

# ============================================================
# System Prompt — Pure abstraction, no target task info
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

## Examples of Abstraction

| Specific (bad) | Generalized (good) |
|---|---|
| "Load `druggability_genes.csv`" | "Load the target gene/protein list (CSV format)" |
| "Filter to p-value < 0.05" | "Apply significance threshold (typical p-value < 0.05)" |
| "Run Fisher's exact test on 2×2 contingency table" | ✅ Keep — this is a transferable method |
| "Extract ESR1 LBD mutations from column 7" | "Extract mutation status from the relevant genomic column" |

## Output Format

Use the same oracle-skill format with `<!-- ORACLE_OP_START op_XXX -->` and `<!-- ORACLE_OP_END op_XXX -->` anchors.

```yaml
---
name: generalized-{source_task}
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


# ============================================================
# LLM API Call
# ============================================================
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
        "max_tokens": MAX_TOKENS,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }

    for attempt in range(MAX_RETRIES):
        try:
            resp = requests.post(API_URL, headers=headers, json=payload, timeout=300)
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


# ============================================================
# Load Source Skill
# ============================================================
def load_source_skill(task_id):
    """Load the source task's oracle skill bundle."""
    bundle_dir = BUNDLES_DIR / task_id
    manifest_path = bundle_dir / "oracle_skill_manifest.json"

    if not manifest_path.exists():
        raise FileNotFoundError(f"No manifest for {task_id}")

    manifest = json.loads(manifest_path.read_text())
    skill_name = manifest.get("skill_name", f"oracle-{task_id}")
    skill_dir = bundle_dir / "skills" / skill_name

    # Read SKILL.md
    skill_md = ""
    skill_md_path = skill_dir / "SKILL.md"
    if skill_md_path.exists():
        skill_md = skill_md_path.read_text()

    # Read all resources
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
    }


# ============================================================
# Build Prompt — NO target task info!
# ============================================================
def build_user_prompt(source):
    """Build the user prompt with ONLY source skill info."""
    # Format source operations
    source_ops_text = ""
    for op in source["operations"]:
        source_ops_text += f"  - {op['id']} ({op['kind']}): {op['title']}"
        for res_id, res_text in source["resources"].items():
            if res_id == op["id"]:
                source_ops_text += f" [{len(res_text)} chars]"
        source_ops_text += "\n"

    prompt = f"""## Source Task: {source['task_id']}

### Source Oracle Skill: {source['manifest'].get('skill_name', '')}

**Operations ({len(source['operations'])} total):**
{source_ops_text}

### Source SKILL.md:
```markdown
{source['skill_md']}
```

### Source Resources (per operation):
"""
    # Add resource content
    for op in source["operations"]:
        res_text = source["resources"].get(op["id"], "")
        if res_text:
            prompt += f"\n#### {op['id']} — {op['title']}\n```\n{res_text[:2000]}\n```\n"

    prompt += """
## Task

Generalize this oracle skill into a **task-agnostic, domain-abstracted skill**.

CRITICAL RULES:
1. You know NOTHING about any target task — this is a pure abstraction exercise.
2. Keep transferable methods (statistical tests, normalization, thresholds).
3. Replace task-specific details (filenames, specific columns, exact gene lists) with generic placeholders.
4. Preserve the operation structure, count, and ordering.
5. Each operation must be independently useful for a researcher working on a similar problem.
6. Output ONLY the SKILL.md content (with YAML frontmatter).
"""
    return prompt


# ============================================================
# Parse LLM Output
# ============================================================
def parse_skill_md(text):
    """Extract SKILL.md content from LLM response (may be wrapped in markdown code blocks)."""
    # Try to extract YAML frontmatter + content
    yaml_pattern = r'^---\s*\n.*?\n---\s*\n'
    match = re.search(yaml_pattern, text, re.DOTALL)
    if match:
        return text

    # Try code blocks
    code_match = re.search(r'```(?:yaml|markdown)?\s*\n(.*?)\n```', text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    return text.strip()


# ============================================================
# Main
# ============================================================
def generalize(source_task, dry_run=False):
    """Generalize a single source task."""
    print(f"\n{'='*60}")
    print(f"Generalizing: {source_task}")
    print(f"{'='*60}")

    # Load source skill
    try:
        source = load_source_skill(source_task)
    except FileNotFoundError as e:
        print(f"❌ {e}")
        return False

    print(f"  Source: {source['task_id']}")
    print(f"  Operations: {len(source['operations'])}")
    print(f"  SKILL.md: {len(source['skill_md'])} chars")
    print(f"  Resources: {len(source['resources'])} files")

    # Build prompt
    prompt = build_user_prompt(source)
    print(f"  Prompt: {len(prompt)} chars")

    if dry_run:
        print("\n⚠ DRY RUN — not calling API")
        return True

    # Call LLM
    print(f"\n  Calling DeepSeek-V4-Flash...")
    start = time.time()
    try:
        response = call_llm(SYSTEM_PROMPT, prompt)
        elapsed = time.time() - start
        print(f"  Response received: {len(response)} chars in {elapsed:.1f}s")
    except Exception as e:
        print(f"❌ API call failed: {e}")
        return False

    # Parse and save
    skill_md = parse_skill_md(response)

    out_dir = OUTPUT_DIR / source_task
    out_dir.mkdir(parents=True, exist_ok=True)

    # Save SKILL.md
    skill_path = out_dir / "SKILL.md"
    skill_path.write_text(skill_md)
    print(f"  ✅ Saved: {skill_path} ({len(skill_md)} chars)")

    # Save metadata
    metadata = {
        "source_task": source_task,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL,
        "n_operations": len(source["operations"]),
        "skill_md_length": len(skill_md),
        "elapsed_seconds": round(elapsed, 1),
    }
    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))

    # Save raw response for debugging
    (out_dir / "raw_response.txt").write_text(response)

    return True


def main():
    parser = argparse.ArgumentParser(description="Generalize BioMniBench skills")
    group = parser.add_mutually_exclusive_group()
    group.add_argument("--source", type=str, help="Single source task ID")
    group.add_argument("--all", action="store_true", help="Generalize all source tasks")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, no API calls")

    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.source:
        tasks = [args.source]
    elif args.all:
        tasks = SOURCE_TASKS
    else:
        # Default: all
        tasks = SOURCE_TASKS

    print(f"Tasks to generalize: {len(tasks)}")
    for t in tasks:
        print(f"  {t}")

    results = []
    for task in tasks:
        success = generalize(task, dry_run=args.dry_run)
        results.append({"task": task, "success": success})
        if not args.dry_run:
            time.sleep(2)  # Rate limit between calls

    successes = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}")
    print(f"Complete: {successes}/{len(results)} succeeded")
    print(f"{'='*60}")
    return 0 if successes == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
