"""Oracle-skill generation aligned with server1's oracle-skills bundle format."""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Optional

MAX_REFERENCE_FILES = 40
MAX_FILE_CHARS = 12_000


def _ignored(path: Path) -> bool:
    parts = {p.lower() for p in path.parts}
    return "__pycache__" in parts or path.name.startswith(".") or path.suffix.lower() in {".pyc", ".pyo", ".bak"}


def _source_index(std_code: Path) -> tuple[list[dict], str]:
    files = [p for p in std_code.rglob("*") if p.is_file() and not _ignored(p)]
    files = sorted(files, key=lambda p: p.as_posix())[:MAX_REFERENCE_FILES]
    entries, notes = [], []
    for path in files:
        content = path.read_bytes()
        rel = path.relative_to(std_code).as_posix()
        entries.append({"path": f"std_code/{rel}", "bytes": len(content),
                        "sha256": hashlib.sha256(content).hexdigest()})
        text = content.decode("utf-8", errors="replace")
        if len(text) > MAX_FILE_CHARS:
            text = text[:MAX_FILE_CHARS] + f"\n\n# [truncated after {MAX_FILE_CHARS} chars]\n"
        text = (text.replace("std_code", "reference implementation")
                    .replace(".judge_private", "judge-private-area")
                    .replace("private_judge", "judge area")
                    .replace("ground_truth", "target array"))
        language = "python" if path.suffix == ".py" else "json" if path.suffix == ".json" else ""
        notes.append(f"### {rel}\n\n```{language}\n{text}\n```")
    return entries, "\n\n".join(notes) or "No standard implementation source files were found."


def _ops() -> list[dict]:
    specs = [
        ("op_010_current_contract", "contract", "Current Task Contract", ["resources/op_010_current_contract.md"],
         "Read `resources/op_010_current_contract.md` before writing solver code."),
        ("op_020_io_and_data", "data_loading", "Data Loading And I/O", ["resources/op_020_io_and_data.md"],
         "Read `resources/op_020_io_and_data.md` and probe the visible files."),
        ("op_030_reference_knowledge", "domain_model", "Reference Implementation Knowledge", ["resources/op_030_reference_notes.md"],
         "Read `resources/op_030_reference_notes.md` and adapt the algorithm without importing external paths."),
        ("op_040_solver_flow", "solver", "Solver Flow", ["resources/op_040_solver_flow.md"],
         "Read `resources/op_040_solver_flow.md` and implement the stages in order."),
        ("op_050_output_validation", "validation", "Output Validation", ["resources/op_050_output_validation.md"],
         "Read `resources/op_050_output_validation.md` before finalizing outputs."),
    ]
    return [
        {"id": op_id, "kind": kind, "title": title, "skill_md_anchor": op_id,
         "resources": resources, "scripts": [], "depends_on": [],
         "ablation_priority": 100 - i, "enabled_by_default": True,
         "source_refs": []}
        for i, (op_id, kind, title, resources, _) in enumerate(specs)
    ]


def generate_template_bundle(task_dir: Path, out_dir: Path, skill_name: Optional[str] = None) -> dict:
    """Build a deterministic bundle from ``task_dir/std_code`` and public files."""
    task_dir, out_dir = task_dir.resolve(), out_dir.resolve()
    task_id = task_dir.name
    skill_name = skill_name or f"oracle-{task_id.lower().replace(' ', '-')}"
    std_code = task_dir / "std_code"
    entries, notes = _source_index(std_code)
    if out_dir.exists():
        import shutil
        shutil.rmtree(out_dir)
    skill_root = out_dir / "skills" / skill_name
    resources = skill_root / "resources"
    resources.mkdir(parents=True, exist_ok=True)
    ops = _ops()
    blocks = []
    text_by_op = {
        "op_010_current_contract": "- Read `resources/op_010_current_contract.md` before writing solver code.\n- Record input/output keys, shapes, dtypes, units, and case IDs.",
        "op_020_io_and_data": "- Read `resources/op_020_io_and_data.md` and inspect public files.\n- Probe keys, shapes, ranges, and finite status; keep outputs under `outputs/` and scratch under `workspace/`.",
        "op_030_reference_knowledge": "- Read `resources/op_030_reference_notes.md` for algorithm flow and formulas.\n- Recreate logic with run-local public paths; never import external task directories.",
        "op_040_solver_flow": "- Read `resources/op_040_solver_flow.md` and implement stages in order.\n- Run a cheap smoke test before the bounded full solve.",
        "op_050_output_validation": "- Read `resources/op_050_output_validation.md` before finalizing.\n- Check required files, schema, shapes, dtypes, and finite values.",
    }
    for op in ops:
        blocks += [f"<!-- ORACLE_OP_START {op['id']} -->", f"## {op['title']}", "", text_by_op[op["id"]], f"<!-- ORACLE_OP_END {op['id']} -->", ""]
    (skill_root / "SKILL.md").write_text(
        "---\n"
        f"name: {skill_name}\n"
        f"description: Oracle skill distilled from the {task_id} reference implementation\n"
        "---\n\n"
        f"# {task_id} Oracle Skill\n\n"
        "Apply the enabled operation sections in order. Prefer current public task files when they conflict with these notes.\n\n"
        + "\n".join(blocks), encoding="utf-8")
    readme = (task_dir / "README.md").read_text(encoding="utf-8") if (task_dir / "README.md").exists() else "(README.md was not found.)"
    schema = (task_dir / "output_schema.json").read_text(encoding="utf-8") if (task_dir / "output_schema.json").exists() else "{}"
    visible = (task_dir / "visible_data" / "cases.json").read_text(encoding="utf-8") if (task_dir / "visible_data" / "cases.json").exists() else "{}"
    (resources / "op_010_current_contract.md").write_text(f"# Current Task Contract\n\n## README\n\n{readme}\n\n## Output Schema\n\n```json\n{schema}\n```\n\n## Visible Cases\n\n```json\n{visible}\n```\n", encoding="utf-8")
    (resources / "op_020_io_and_data.md").write_text("# Data Loading And I/O Notes\n\n- Start from public files listed in the task.\n- Probe visible cases before choosing a solver.\n- Reconcile outputs with the schema and case IDs.\n", encoding="utf-8")
    (resources / "op_030_reference_notes.md").write_text("# Reference Implementation Notes\n\nThe excerpts below are evidence to adapt, not answers to copy.\n\n" + notes + "\n", encoding="utf-8")
    (resources / "op_040_solver_flow.md").write_text("# Solver Flow\n\n1. Extract the public contract.\n2. Recreate data loading with run-local public paths.\n3. Implement model, objective, solver, and post-processing.\n4. Run smoke test, then bounded full solve.\n5. Write outputs in the public schema.\n", encoding="utf-8")
    (resources / "op_050_output_validation.md").write_text("# Output Validation\n\n- Required outputs must exist under `outputs/`.\n- Arrays must be present, finite, and shaped/dtyped according to the public schema.\n", encoding="utf-8")
    manifest = {"schema_version": 1, "task_id": task_id, "skill_name": skill_name, "operations": ops, "source_index_path": "source_index.json"}
    (out_dir / "oracle_skill_manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    (out_dir / "source_index.json").write_text(json.dumps({"schema_version": 1, "task_id": task_id, "source_root": "std_code", "files": entries}, indent=2) + "\n", encoding="utf-8")
    return {"bundle_dir": str(out_dir), "skill_name": skill_name, "operation_ids": [op["id"] for op in ops], "mode": "template"}


def extract_oracle_skill(reference: Path, task_instruction: str = "", output: Optional[Path] = None) -> str:
    """Legacy single-file helper retained for small examples."""
    text = reference.read_text(encoding="utf-8")
    name = reference.stem.replace("_", " ").title()
    skill = f"# Oracle Skill: {name}\n\n## Task Understanding\n{task_instruction.strip() or 'Read the task carefully and identify the requested artifact.'}\n\n## Expert Workflow\n1. Inspect files and validate their schema.\n2. Recreate the reference decisions in a general form.\n3. Check intermediate values and edge cases.\n4. Save results using the required schema.\n"
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(skill, encoding="utf-8")
    return skill
