#!/usr/bin/env python3
"""
generalize_skill.py — v2 (2026-08-25)

Use DeepSeek-V4-Flash (via gpugeek API) to generalize a source task's oracle skill
into a **task-agnostic**, **domain-abstracted skill** with explicit applicability scope.

CRITICAL: The LLM receives ONLY the source task's oracle skill. It does NOT know
anything about any target task. The goal is to distill the core domain knowledge
and analysis pattern into a reusable form that can transfer to other tasks.

Key improvements in v2:
- Each generalized skill includes an `## Applicability` section declaring:
  - ✅ Suitable task types (what the skill is designed for)
  - ❌ Unsuitable task types (what the skill is NOT for)
  - ⚠️ Caveats and limitations
- The YAML frontmatter now includes `source_task_type` for downstream filtering
- Better abstraction: more emphasis on domain-agnostic, method-level instructions
- Preserved operation structure for compatibility with existing deployment

Usage:
  python3 generalize_skill.py --source da-17-1
  python3 generalize_skill.py --all
  python3 generalize_skill.py --source da-17-1 --dry-run
"""

import json, os, sys, time, re, argparse
from pathlib import Path

# API Configuration. BioMniBench's launcher exports the gateway credentials as
# API_KEY/BASE_URL, while direct runs commonly use the Anthropic-compatible
# names. Resolve both forms so a live run uses exactly the same gateway as the
# harness (and never falls back to a checked-in secret).
_base_url = (
    os.environ.get("ANTHROPIC_BASE_URL")
    or os.environ.get("BASE_URL")
    or "https://api.gpugeek.com"
).rstrip("/")
if _base_url.endswith("/messages"):
    API_URL = _base_url
elif _base_url.endswith("/v1"):
    API_URL = f"{_base_url}/messages"
else:
    API_URL = f"{_base_url}/v1/messages"
API_KEY = (
    os.environ.get("ANTHROPIC_API_KEY")
    or os.environ.get("API_KEY")
    or os.environ.get("SKILL_TRANSFER_API_KEY", "")
)
MODEL = os.environ.get("SKILL_GEN_MODEL", "Vendor3/DeepSeek-V4-Flash")
MAX_TOKENS = 8000
MAX_RETRIES = 3

BUNDLES_DIR = Path(os.environ.get("ORACLE_BUNDLES_DIR", "runtime/oracle_bundles"))
OUTPUT_DIR = Path(os.environ.get("SKILL_TRANSFER_ROOT", "runtime")) / "generalized_skills"

# Source tasks that need generalization
SOURCE_TASKS = [
    "da-5-1",   # PDAC target prioritization
    "da-8-1",   # Bread-spiker classification
    "da-13-5",  # Sex-associated overlap
    "da-17-1",  # SLE ancestry composition
    "da-18-5",  # MAPK/ESR1 exclusivity
    "da-19-3",  # RUNX1 peak analysis
    "da-19-4",  # H3K27ac ChIP-seq
    "da-26-2",  # Biomarker identification
    "da-1-3",   # spatiotemporal single-cell
    "da-4-1",   # NSCLC single-cell atlas
    "da-4-6",   # NSCLC single-cell atlas
    "da-8-2",   # glycemic responses
    "da-13-1",  # plasma proteome
    "da-13-3",  # plasma proteome
    "da-14-1",  # immune dysregulation
    "da-14-3",  # immune dysregulation
    "da-15-1",  # ALS transcriptomic
    "da-15-2",  # ALS transcriptomic
    "da-18-1",  # breast cancer genomics
    "da-19-1",  # chromatin profiling
    "da-20-1",  # general biology
    "da-20-3",  # general biology
    "da-6-2",   # cardiovascular exercise dynamics
]

# ============================================================
# v2 System Prompt — Pure abstraction + Applicability scope
# ============================================================
SYSTEM_PROMPT = """You are an expert bioinformatics skill author. Given a **source task's oracle skill** (a structured set of domain knowledge operations), you must produce a **generalized, task-agnostic skill** that captures the core analytical pattern.

## Core Principle

You are given **only one task's skill**. You must NOT assume any specific target task. Instead, **abstract the domain knowledge** so it can be applied to other similar bioinformatics problems.

## What to Do: 4-Step Abstraction

### Step 1: Identify the Core Pattern
- What kind of analysis is this? (e.g., differential expression, GWAS, ChIP-seq peak calling, survival analysis, clustering, cell composition)
- What is the **statistical or computational method** at the heart of the analysis?
- What **data types** does it operate on? (e.g., gene expression matrices, peak files, variant calls, clinical tables)

### Step 2: Abstract the Operations
- Each operation should describe a **general analytical step**, not the specific task
- Replace concrete file names with generic placeholders
- Keep the **workflow structure** — order and dependency between operations

### Step 3: Preserve Transferable Methods
- **KEEP**: Statistical tests, thresholds, normalization methods, validation criteria
- **KEEP**: Rubric structure, evaluation criteria, quality checks
- **REMOVE**: Specific dataset names, gene lists, disease names, exact column names
- **REMOVE**: Task-specific biological context that doesn't generalize

### Step 4: Declare Applicability Scope
This is CRITICAL. After the operations, you MUST include an `## Applicability` section.

## Output Format

Use the same oracle-skill format with `<!-- ORACLE_OP_START op_XXX -->` and `<!-- ORACLE_OP_END op_XXX -->` anchors.

```yaml
---
name: generalized-{source_task}
description: Generalized skill for {analysis_pattern} — useful for similar tasks involving {domain}
source_task: {source_task}
source_task_type: {task_type if known, else "unknown"}
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
- Do NOT reference any specific task name, file, or dataset

## Applicability Section Requirements

After the operations, you MUST include this section. Be honest and precise:

```markdown
## Applicability

### ✅ Suitable For
- Task types: [list of task_type values this skill is appropriate for, e.g., "differential-expression, chromatin-profiling"]
- Analysis patterns: [description of the analytical pattern, e.g., "comparing two groups of samples to find differentially abundant features"]
- Data types: [what kind of input data this skill expects]

### ❌ NOT Suitable For
- Task types: [list of task_type values this skill is NOT appropriate for]
- Why: [brief explanation of the mismatch]
- Examples: [concrete counterexamples of tasks that would be misled by this skill]

### ⚠️ Caveats
- [Any limitations, assumptions, or conditions where this skill may be misleading]
- [Known failure modes: e.g., "This skill assumes normally distributed data — use with caution for count data"]
```

## Examples of Abstraction

| Specific (bad) | Generalized (good) |
|---|---|
| "Load `druggability_genes.csv`" | "Load the target gene/protein list (CSV format)" |
| "Filter to p-value < 0.05" | "Apply significance threshold (typical p-value < 0.05)" |
| "Run Fisher's exact test on 2×2 contingency table" | ✅ Keep — this is a transferable method |
| "Extract ESR1 LBD mutations from column 7" | "Extract mutation status from the relevant genomic column" |
| "Compare CBFβ-SMMHC vs Empty Vector" | "Compare treatment vs control conditions" |
| "Use MACS2 with q<0.05" | "Run peak caller with appropriate significance threshold" |

## Critical Warning

A skill that is **too specific** will mislead the agent when applied to a different task.
A skill that is **too vague** will be useless.
The goal is to be **just specific enough** about methods while being **fully generic** about the domain.

If the source skill is highly task-specific (e.g., "analyze CBFβ-SMMHC ChIP-seq data"), the generalized version should describe the **general ChIP-seq analysis workflow** without mentioning CBFβ-SMMHC or any specific cell line.
"""


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


def load_task_type(task_id):
    """Load task_type from task.toml."""
    task_dir = BUNDLES_DIR / task_id
    toml_path = task_dir / "task.toml"
    if not toml_path.exists():
        # Try biomnibench-organized
        alt_path = Path(f"/data/yjh/biomnibench-organized/{task_id}/task.toml")
        if alt_path.exists():
            toml_path = alt_path
        else:
            return "unknown"
    for line in toml_path.read_text().split("\n"):
        ls = line.strip()
        if ls.startswith("task_type"):
            return ls.split("=")[1].strip().strip('"\'')
    return "unknown"


# ============================================================
# Build Prompt — NO target task info!
# ============================================================
def build_user_prompt(source, task_type):
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

### Source Task Type: {task_type}

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

    prompt += f"""
## Task

Generalize this oracle skill into a **task-agnostic, domain-abstracted skill** with explicit applicability scope.

CRITICAL RULES:
1. You know NOTHING about any target task — this is a pure abstraction exercise.
2. Keep transferable methods (statistical tests, normalization, thresholds).
3. Replace task-specific details (filenames, specific columns, exact gene lists) with generic placeholders.
4. Preserve the operation structure, count, and ordering.
5. Each operation must be independently useful for a researcher working on a similar problem.
6. **MUST include an `## Applicability` section** (see system prompt for format).
7. Include `source_task_type: {task_type}` in the YAML frontmatter.
8. Output ONLY the SKILL.md content (with YAML frontmatter).
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


def validate_skill_md(skill_md, source_task):
    """Validate that the generated skill has required sections."""
    issues = []
    if "## Applicability" not in skill_md:
        issues.append("MISSING '## Applicability' section")
    if "Suitable For" not in skill_md and "suitable" not in skill_md.lower():
        issues.append("MISSING suitability description")
    if "NOT Suitable" not in skill_md and "not suitable" not in skill_md.lower():
        issues.append("MISSING 'NOT Suitable' section")
    if "source_task" not in skill_md:
        issues.append("MISSING 'source_task' in frontmatter")
    if issues:
        print(f"  ⚠ Validation issues: {', '.join(issues)}")
    return len(issues) == 0


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

    # Load task type
    task_type = load_task_type(source_task)

    print(f"  Source: {source['task_id']}")
    print(f"  Type: {task_type}")
    print(f"  Operations: {len(source['operations'])}")
    print(f"  SKILL.md: {len(source['skill_md'])} chars")
    print(f"  Resources: {len(source['resources'])} files")

    # Build prompt
    prompt = build_user_prompt(source, task_type)
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

    # Create backup of existing skill if present
    out_dir = OUTPUT_DIR / source_task
    if out_dir.exists():
        existing_skill = out_dir / "SKILL.md"
        if existing_skill.exists():
            ts = time.strftime("%Y%m%d_%H%M%S")
            backup_path = out_dir / f"SKILL.md.bak_{ts}"
            existing_skill.rename(backup_path)
            print(f"  📦 Backed up old skill: {backup_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    # Save SKILL.md
    skill_path = out_dir / "SKILL.md"
    skill_path.write_text(skill_md)
    print(f"  ✅ Saved: {skill_path} ({len(skill_md)} chars)")

    # Validate
    validate_skill_md(skill_md, source_task)

    # Save metadata
    metadata = {
        "source_task": source_task,
        "source_task_type": task_type,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "model": MODEL,
        "n_operations": len(source["operations"]),
        "skill_md_length": len(skill_md),
        "elapsed_seconds": round(elapsed, 1),
        "version": 2,
    }
    meta_path = out_dir / "metadata.json"
    meta_path.write_text(json.dumps(metadata, indent=2))

    # Save raw response for debugging
    (out_dir / "raw_response.txt").write_text(response)

    return True


def main():
    parser = argparse.ArgumentParser(description="Generalize BioMniBench skills (v2)")
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
        tasks = SOURCE_TASKS

    print(f"Tasks to generalize: {len(tasks)}")
    for t in tasks:
        print(f"  {t}")

    results = []
    for task in tasks:
        print(f"\n--- Processing: {task} ---")
        success = generalize(task, dry_run=args.dry_run)
        results.append({"task": task, "success": success})
        if not args.dry_run:
            time.sleep(3)  # Rate limit between calls

    successes = sum(1 for r in results if r["success"])
    print(f"\n{'='*60}")
    print(f"Complete: {successes}/{len(results)} succeeded")
    print(f"{'='*60}")
    return 0 if successes == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
