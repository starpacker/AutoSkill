#!/usr/bin/env python3
"""Validate BioDSBench tasks packaged in an imaging-101-like layout."""

from __future__ import annotations

import argparse
import ast
import json
from pathlib import Path
from typing import Any

from build_biodsbench_imaging101 import collect_hyperparameters


REQUIRED_TASK_FILES = [
    "README.md",
    "main.py",
    "requirements.txt",
    "task.json",
    "data/meta_data.json",
    "evaluation/metrics.json",
    "evaluation/prefix.py",
    "evaluation/reference_answer.py",
    "evaluation/test_cases.py",
    "evaluation/run_reference.py",
]

DISALLOWED_META_KEYS = {
    "n_tables",
    "table_shapes",
    "n_assertions",
    "input_format",
    "workdir",
    "hyperparameters",
}


def parse_maybe_literal(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value


def load_rows(jsonl_path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with jsonl_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("analysis_types", "tables", "study_data_configs"):
                row[key] = parse_maybe_literal(row.get(key))
            if not isinstance(row.get("tables"), list):
                raise ValueError(f"{jsonl_path}:{line_number}: tables is not a list")
            if not row.get("unique_question_ids"):
                raise ValueError(f"{jsonl_path}:{line_number}: missing unique_question_ids")
            rows.append(row)
    return rows


def json_load(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def count_assertions(test_cases: str) -> int:
    return sum(1 for line in test_cases.splitlines() if line.lstrip().startswith("assert "))


def validate(root: Path, expected_jsonl: Path) -> list[str]:
    errors: list[str] = []
    rows = load_rows(expected_jsonl)
    expected_by_id = {str(row["unique_question_ids"]): row for row in rows}
    tasks_dir = root / "tasks"

    if not root.exists():
        return [f"Output root does not exist: {root}"]
    if not tasks_dir.is_dir():
        return [f"Missing tasks directory: {tasks_dir}"]

    actual_ids = sorted(path.name for path in tasks_dir.iterdir() if path.is_dir())
    expected_ids = sorted(expected_by_id)
    missing = sorted(set(expected_ids) - set(actual_ids))
    extra = sorted(set(actual_ids) - set(expected_ids))
    if missing:
        errors.append(f"Missing task directories: {missing[:10]} (total {len(missing)})")
    if extra:
        errors.append(f"Unexpected task directories: {extra[:10]} (total {len(extra)})")

    manifest_path = root / "manifest.json"
    if not manifest_path.is_file():
        errors.append(f"Missing manifest: {manifest_path}")
    else:
        manifest = json_load(manifest_path)
        if manifest.get("task_count") != len(rows):
            errors.append(
                f"manifest task_count={manifest.get('task_count')} but expected {len(rows)}"
            )

    for task_id in expected_ids:
        row = expected_by_id[task_id]
        task_dir = tasks_dir / task_id
        if not task_dir.is_dir():
            continue

        for relative in REQUIRED_TASK_FILES:
            path = task_dir / relative
            if not path.is_file():
                errors.append(f"{task_id}: missing {relative}")

        metadata_path = task_dir / "data" / "meta_data.json"
        metrics_path = task_dir / "evaluation" / "metrics.json"
        task_json_path = task_dir / "task.json"
        if metadata_path.is_file():
            metadata = json_load(metadata_path)
            disallowed_keys = sorted(set(metadata) & DISALLOWED_META_KEYS)
            if disallowed_keys:
                errors.append(
                    f"{task_id}: meta_data.json has non-imaging101 catalog keys {disallowed_keys}"
                )
            if "description" not in metadata:
                errors.append(f"{task_id}: meta_data.json missing key description")
            if not isinstance(metadata.get("description"), str) or not metadata.get("description", "").strip():
                errors.append(f"{task_id}: meta_data.json description must be a non-empty string")
            actual_parameters = {
                key: value for key, value in metadata.items() if key != "description"
            }
            expected_parameters = collect_hyperparameters(row)
            if actual_parameters != expected_parameters:
                errors.append(
                    f"{task_id}: meta_data.json parameters={actual_parameters!r} "
                    f"but expected {expected_parameters!r}"
                )
            if task_id == "28985567_3":
                if metadata.get("gain_threshold") != 0.2:
                    errors.append(f"{task_id}: missing gain_threshold=0.2 in meta_data.json")
                if metadata.get("loss_threshold") != -0.2:
                    errors.append(f"{task_id}: missing loss_threshold=-0.2 in meta_data.json")
            data_entries = sorted(path.name for path in (task_dir / "data").iterdir())
            if data_entries != ["meta_data.json"]:
                errors.append(f"{task_id}: data directory should only contain meta_data.json")
        if metrics_path.is_file():
            metrics = json_load(metrics_path)
            if metrics.get("evaluation_type") != "python_assertions":
                errors.append(f"{task_id}: metrics.json evaluation_type must be python_assertions")
            expected_assertions = count_assertions(str(row.get("test_cases", "")))
            if metrics.get("test_case_count") != expected_assertions:
                errors.append(
                    f"{task_id}: metrics test_case_count={metrics.get('test_case_count')} "
                    f"but expected {expected_assertions}"
                )
        if task_json_path.is_file():
            task_json = json_load(task_json_path)
            if task_json.get("unique_question_ids") != task_id:
                errors.append(f"{task_id}: task.json unique_question_ids mismatch")

        expected_tables = [Path(str(table)).name for table in row["tables"]]
        for filename in expected_tables:
            data_file = task_dir / "workdir" / filename
            if not data_file.is_file():
                errors.append(f"{task_id}: missing workdir/{filename}")
            elif data_file.stat().st_size == 0:
                errors.append(f"{task_id}: empty workdir/{filename}")

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", required=True, type=Path)
    parser.add_argument("--expected-jsonl", required=True, type=Path)
    args = parser.parse_args()

    errors = validate(args.root, args.expected_jsonl)
    if errors:
        print(f"VALIDATION FAILED: {len(errors)} issue(s)")
        for error in errors[:200]:
            print(f"- {error}")
        if len(errors) > 200:
            print(f"- ... {len(errors) - 200} more")
        return 1

    rows = load_rows(args.expected_jsonl)
    print(f"VALIDATION PASSED: {len(rows)} tasks packaged under {args.root}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
