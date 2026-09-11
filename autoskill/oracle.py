"""Oracle-skill extraction from a reference solution."""

from pathlib import Path
from typing import Optional


def extract_oracle_skill(reference: Path, task_instruction: str = "",
                         output: Optional[Path] = None) -> str:
    """Create a deterministic skill when no LLM is configured.

    The reference solution is treated as evidence, not copied wholesale into
    the prompt. This keeps generated skills reusable and avoids leaking outputs.
    """
    text = reference.read_text(encoding="utf-8")
    name = reference.stem.replace("_", " ").title()
    skill = f"""# Oracle Skill: {name}

## Task Understanding
{task_instruction.strip() or "Read the task carefully and identify the requested artifact."}

## Expert Workflow
1. Inspect the available files and validate their schema.
2. Reproduce the reference solution's analysis decisions in a general form.
3. Check intermediate values and edge cases before writing final outputs.
4. Save results using the task's required filenames and schema.

## Reference Evidence
The reference solution used for extraction contains {len(text.splitlines())} lines.
Use it to infer methodology, not to copy task-specific answers or constants.
"""
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(skill, encoding="utf-8")
    return skill
