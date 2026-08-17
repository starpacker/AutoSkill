#!/usr/bin/env python3
"""Package BioDSBench Python tasks in an imaging-101-like task layout."""

from __future__ import annotations

import argparse
import ast
import csv
import json
import os
import re
import shutil
import textwrap
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


DEFAULT_REQUIREMENTS = [
    "pandas>=1.5",
    "numpy>=1.23",
    "scipy>=1.9",
    "matplotlib>=3.6",
    "seaborn>=0.12",
    "scikit-learn>=1.2",
    "statsmodels>=0.14",
    "lifelines>=0.27",
    "PyComplexHeatmap>=1.8",
]


RUN_REFERENCE_TEMPLATE = r'''#!/usr/bin/env python3
"""Run the BioDSBench reference answer and assertion tests for this task."""

from __future__ import annotations

import builtins
import json
import os
import runpy
from pathlib import Path
from typing import Any

import pandas as pd


TASK_ROOT = Path(__file__).resolve().parents[1]
DATA_WORKDIR = TASK_ROOT / "workdir"


def _redirect_workdir_path(path: Any) -> Any:
    if isinstance(path, os.PathLike):
        path = os.fspath(path)
    if isinstance(path, str):
        normalized = path.replace("\\", "/")
        if normalized == "/workdir":
            return str(DATA_WORKDIR)
        if normalized.startswith("/workdir/"):
            return str(DATA_WORKDIR / normalized[len("/workdir/"):])
        if normalized == "./workdir" or normalized == "workdir":
            return str(TASK_ROOT / "workdir")
        if normalized.startswith("./workdir/"):
            return str(TASK_ROOT / "workdir" / normalized[len("./workdir/"):])
        if normalized.startswith("workdir/"):
            return str(TASK_ROOT / "workdir" / normalized[len("workdir/"):])
    return path


_real_read_csv = pd.read_csv


def _read_csv_with_workdir_redirect(filepath_or_buffer: Any, *args: Any, **kwargs: Any) -> pd.DataFrame:
    return _real_read_csv(_redirect_workdir_path(filepath_or_buffer), *args, **kwargs)


pd.read_csv = _read_csv_with_workdir_redirect

_real_open = builtins.open


def _open_with_workdir_redirect(file: Any, *args: Any, **kwargs: Any) -> Any:
    return _real_open(_redirect_workdir_path(file), *args, **kwargs)


builtins.open = _open_with_workdir_redirect


def _preload_tables(namespace: dict[str, Any]) -> None:
    with (TASK_ROOT / "task.json").open("r", encoding="utf-8") as handle:
        metadata = json.load(handle)
    table_bindings = metadata.get("table_bindings", [])
    for binding in table_bindings:
        csv_path = DATA_WORKDIR / binding["output_file"]
        if not csv_path.exists():
            continue
        df = pd.read_csv(csv_path)
        names = {binding["variable_name"], Path(binding["output_file"]).stem}
        for name in names:
            if name and name.isidentifier():
                namespace[name] = df.copy()


def main() -> None:
    namespace: dict[str, Any] = {
        "__name__": "__biodsbench_reference__",
        "__file__": str(TASK_ROOT / "evaluation" / "reference_answer.py"),
    }
    _preload_tables(namespace)
    for filename in ("prefix.py", "reference_answer.py", "test_cases.py"):
        code_path = TASK_ROOT / "evaluation" / filename
        code = code_path.read_text(encoding="utf-8")
        exec(compile(code, str(code_path), "exec"), namespace)
    print("Reference answer and test cases executed successfully.")


if __name__ == "__main__":
    main()
'''


def parse_maybe_literal(value: Any) -> Any:
    if not isinstance(value, str):
        return value
    try:
        return ast.literal_eval(value)
    except (SyntaxError, ValueError):
        return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            for key in ("analysis_types", "tables", "study_data_configs"):
                row[key] = parse_maybe_literal(row.get(key))
            rows.append(row)
    return rows


def load_schema_map(path: Path) -> dict[str, list[str]]:
    schema_by_study: dict[str, list[str]] = {}
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if not line.strip():
                continue
            row = json.loads(line)
            schemas = parse_maybe_literal(row.get("table_schemas"))
            if isinstance(schemas, list):
                schema_by_study[str(row["study_ids"])] = [str(schema) for schema in schemas]
    return schema_by_study


def safe_task_id(task_id: str) -> str:
    if not re.fullmatch(r"[A-Za-z0-9_.-]+", task_id):
        raise ValueError(f"Unsafe task id: {task_id!r}")
    return task_id


def normalize_analysis_types(value: Any) -> list[str]:
    value = parse_maybe_literal(value)
    if isinstance(value, list):
        return [str(item) for item in value]
    if value is None:
        return []
    return [str(value)]


def normalize_tables(value: Any) -> list[str]:
    value = parse_maybe_literal(value)
    if not isinstance(value, list):
        raise ValueError(f"tables must be a list, got {type(value).__name__}")
    return [str(item) for item in value]


def find_source_file(study_dir: Path, source_filename: str) -> Path:
    matches = [
        path for path in study_dir.rglob(source_filename)
        if path.is_file() and ".tar" not in path.name
    ]
    if not matches:
        raise FileNotFoundError(f"Cannot find {source_filename} under {study_dir}")
    matches.sort(key=lambda path: (len(path.parts), str(path)))
    return matches[0]


def source_to_output_name(source_filename: str, variable_name: str, required_outputs: set[str]) -> str:
    source_stem = Path(source_filename).stem
    source_candidate = f"{source_stem}.csv"
    variable_candidate = f"{variable_name}.csv"
    if source_candidate in required_outputs:
        return source_candidate
    if variable_candidate in required_outputs:
        return variable_candidate
    return source_candidate


def convert_table_to_csv(source: Path, destination: Path, fmt: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    delimiter = "\t" if fmt.lower() == "tsv" else ","
    with source.open("r", encoding="utf-8", errors="replace", newline="") as src:
        reader = csv.reader(src, delimiter=delimiter)
        with destination.open("w", encoding="utf-8", newline="") as dst:
            writer = csv.writer(dst)
            for row in reader:
                writer.writerow(row)


def csv_shape(path: Path) -> list[int]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            header = next(reader)
        except StopIteration:
            return [0, 0]
        row_count = sum(1 for _ in reader)
    return [row_count, len(header)]


def link_or_copy(source: Path, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        destination.unlink()
    try:
        os.link(source, destination)
    except OSError:
        shutil.copy2(source, destination)


def count_assertions(test_cases: str) -> int:
    return sum(1 for line in test_cases.splitlines() if line.lstrip().startswith("assert "))


PARAMETER_NAME_RE = re.compile(
    r"(^|_)(threshold|cutoff|alpha|beta|gamma|lambda|seed|random_state|"
    r"pvalue|p_value|qvalue|q_value|fdr|ratio|weight|level|scale|range|"
    r"resolution|bin|bins|angle|angles|contrast|wavelength|na)(_|$)|"
    r"^(n|num|top|min|max)_",
    re.IGNORECASE,
)

CATEGORY_PARAMETER_NAME_RE = re.compile(
    r"(gene|mutation|response|categor|stage|status|type|group|risk|marker|"
    r"cohort|subtype|class|label)",
    re.IGNORECASE,
)

EXCLUDED_PARAMETER_NAMES = {
    "data_dir",
    "input_dir",
    "result",
    "results",
    "results_df",
    "kmf_curves",
}

EXCLUDED_PARAMETER_SUFFIXES = (
    "_path",
    "_paths",
    "_dir",
    "_dirs",
    "_file",
    "_files",
    "_df",
    "_dfs",
)


def to_jsonable_literal(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, tuple):
        return [to_jsonable_literal(item) for item in value]
    if isinstance(value, list):
        return [to_jsonable_literal(item) for item in value]
    if isinstance(value, dict):
        return {str(key): to_jsonable_literal(item) for key, item in value.items()}
    raise TypeError(f"Unsupported literal type: {type(value).__name__}")


def is_non_empty_literal(value: Any) -> bool:
    if isinstance(value, (list, tuple, dict)) and not value:
        return False
    return True


def is_path_like_literal(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    normalized = value.replace("\\", "/")
    if normalized in {"/workdir", "./workdir", "workdir"}:
        return True
    if normalized.startswith(("/workdir/", "./workdir/", "workdir/")):
        return True
    return normalized.lower().endswith((".csv", ".tsv", ".txt", ".xlsx", ".json"))


def should_keep_hyperparameter(name: str, value: Any) -> bool:
    lower_name = name.lower()
    if name.startswith("_") or lower_name in EXCLUDED_PARAMETER_NAMES:
        return False
    if lower_name.endswith(EXCLUDED_PARAMETER_SUFFIXES):
        return False
    if not is_non_empty_literal(value) or is_path_like_literal(value):
        return False

    if PARAMETER_NAME_RE.search(name):
        return True
    if CATEGORY_PARAMETER_NAME_RE.search(name):
        return True
    return isinstance(value, (int, float, bool)) and not isinstance(value, bool)


def extract_hyperparameters_from_code(code: str) -> dict[str, Any]:
    if not code.strip():
        return {}
    try:
        tree = ast.parse(code)
    except SyntaxError:
        return {}

    parameters: dict[str, Any] = {}
    for node in tree.body:
        targets: list[ast.expr]
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value_node = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value_node = node.value
            if value_node is None:
                continue
        else:
            continue

        try:
            literal_value = ast.literal_eval(value_node)
            jsonable_value = to_jsonable_literal(literal_value)
        except (SyntaxError, ValueError, TypeError):
            continue

        for target in targets:
            if not isinstance(target, ast.Name):
                continue
            if should_keep_hyperparameter(target.id, jsonable_value):
                parameters[target.id] = jsonable_value
    return parameters


def collect_hyperparameters(row: dict[str, Any]) -> dict[str, Any]:
    parameters: dict[str, Any] = {}
    for field in ("code_histories", "reference_answer"):
        parameters.update(extract_hyperparameters_from_code(str(row.get(field) or "")))
    return parameters


def make_meta_data(row: dict[str, Any]) -> dict[str, Any]:
    metadata = collect_hyperparameters(row)
    metadata["description"] = (
        "BioDSBench Python coding task using cBioPortal-style tabular data. "
        "Load CSV inputs from the task-level workdir directory, mounted as /workdir in a sandbox."
    )
    return metadata


def write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.rstrip() + "\n", encoding="utf-8")


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def render_readme(row: dict[str, Any], metadata: dict[str, Any]) -> str:
    task_id = str(row["unique_question_ids"])
    analysis_types = ", ".join(normalize_analysis_types(row.get("analysis_types"))) or "Unspecified"
    table_lines = "\n".join(
        f"| `{table['mount_path']}` | `{table['packaged_path']}` | `{table['variable_name']}` |"
        for table in metadata["table_bindings"]
    )
    question = str(row.get("queries", "")).strip()
    prefix_note = "Yes" if str(row.get("code_histories") or "").strip() else "No"
    return f"""# BioDSBench Python Task {task_id}

> Reproduce a biomedical data-science analysis task extracted from a real study and
> evaluated by executable Python assertions.

> Domain: Biomedical Data Science | Study Type: {row.get('study_types', '')} | Analysis: {analysis_types}

---

## Background

Study title: **{row.get('study_title', '')}**

Dataset URL: {row.get('dataset_url', '')}

The task uses cBioPortal-style patient, sample, mutation, copy-number,
structural-variant, timeline, or expression tables. The benchmark execution
environment should expose the task CSV files at `/workdir`.

## Problem Description

{question}

## Data Description

The canonical mount path is `/workdir`. This package stores the CSV files in
the task-level `workdir/` directory.

| Mount path | Packaged file | Suggested dataframe variable |
|---|---|---|
{table_lines}

`data/meta_data.json` stores extracted analysis parameters and a description.
Full BioDSBench provenance is stored separately in `task.json`.

## Evaluation

Evaluation type: Python assertions.

Run:

```bash
python main.py
```

The runner executes `evaluation/prefix.py` when present, then
`evaluation/reference_answer.py`, then `evaluation/test_cases.py`.

Prefix context required: {prefix_note}

## Files

- `data/meta_data.json`: compact parameters and description.
- `workdir/`: task CSV files to mount as `/workdir`.
- `evaluation/metrics.json`: assertion-count and pass-condition metadata.
- `evaluation/reference_answer.py`: expert reference answer from BioDSBench.
- `evaluation/test_cases.py`: executable checks for the generated answer.
"""


def render_main() -> str:
    return '''#!/usr/bin/env python3
"""Entry point for running this BioDSBench packaged task reference solution."""

from __future__ import annotations

import runpy
from pathlib import Path


if __name__ == "__main__":
    runpy.run_path(
        str(Path(__file__).resolve().parent / "evaluation" / "run_reference.py"),
        run_name="__main__",
    )
'''


def make_task_json(row: dict[str, Any], table_bindings: list[dict[str, Any]]) -> dict[str, Any]:
    payload = dict(row)
    payload["analysis_types"] = normalize_analysis_types(row.get("analysis_types"))
    payload["tables"] = normalize_tables(row.get("tables"))
    payload["study_data_configs"] = parse_maybe_literal(row.get("study_data_configs"))
    payload["table_bindings"] = table_bindings
    return payload


def build(args: argparse.Namespace) -> Path:
    rows = load_jsonl(args.tasks_jsonl)
    schema_by_study = load_schema_map(args.schema_jsonl)

    output_root = args.output
    if output_root.exists() and not args.force:
        raise FileExistsError(f"{output_root} exists; pass --force to replace via backup")

    tmp_root = output_root.with_name(f"{output_root.name}.tmp.{os.getpid()}")
    if tmp_root.exists():
        shutil.rmtree(tmp_root)
    tmp_root.mkdir(parents=True)

    converted_root = tmp_root / "_converted_data"
    converted_cache: dict[tuple[str, str], Path] = {}
    shape_cache: dict[tuple[str, str], list[int]] = {}
    manifest_tasks: list[dict[str, Any]] = []

    try:
        for row in rows:
            task_id = safe_task_id(str(row["unique_question_ids"]))
            study_id = str(row["study_ids"])
            question_id = str(row.get("question_ids", ""))
            task_tables = normalize_tables(row.get("tables"))
            required_outputs = {PurePosixPath(table).name for table in task_tables}
            study_config = parse_maybe_literal(row.get("study_data_configs"))
            if not isinstance(study_config, dict):
                raise ValueError(f"{task_id}: study_data_configs must be a dict")
            cfg_tables = study_config.get("tables")
            if not isinstance(cfg_tables, list):
                raise ValueError(f"{task_id}: study_data_configs.tables must be a list")

            study_dir = args.data_root / study_id
            task_dir = tmp_root / "tasks" / task_id
            table_bindings: list[dict[str, Any]] = []
            table_shapes: dict[str, list[int]] = {}
            output_to_source: dict[str, tuple[str, str, Path]] = {}

            for cfg in cfg_tables:
                if len(cfg) < 3:
                    raise ValueError(f"{task_id}: malformed table config: {cfg!r}")
                source_filename = str(cfg[0])
                variable_name = str(cfg[1])
                fmt = str(cfg[2])
                output_name = source_to_output_name(source_filename, variable_name, required_outputs)
                if output_name not in required_outputs:
                    continue
                source_path = find_source_file(study_dir, source_filename)
                output_to_source[output_name] = (source_filename, fmt, source_path)
                converted_key = (study_id, output_name)
                converted_path = converted_cache.get(converted_key)
                if converted_path is None:
                    converted_path = converted_root / study_id / output_name
                    convert_table_to_csv(source_path, converted_path, fmt)
                    converted_cache[converted_key] = converted_path
                    shape_cache[converted_key] = csv_shape(converted_path)
                table_shapes[output_name] = shape_cache[converted_key]
                link_or_copy(converted_path, task_dir / "workdir" / output_name)
                table_bindings.append(
                    {
                        "output_file": output_name,
                        "mount_path": f"/workdir/{output_name}",
                        "packaged_path": f"workdir/{output_name}",
                        "variable_name": variable_name,
                        "source_file": source_filename,
                        "source_format": fmt,
                        "source_path": str(source_path),
                    }
                )

            missing = sorted(required_outputs - set(output_to_source))
            if missing:
                raise FileNotFoundError(f"{task_id}: missing source mappings for {missing}")

            analysis_types = normalize_analysis_types(row.get("analysis_types"))
            table_schemas = schema_by_study.get(study_id, [])
            metadata = make_meta_data(row)

            metrics = {
                "evaluation_type": "python_assertions",
                "test_case_count": count_assertions(str(row.get("test_cases", ""))),
                "pass_condition": (
                    "Execute evaluation/prefix.py, evaluation/reference_answer.py, "
                    "and evaluation/test_cases.py in one Python namespace without assertion failures."
                ),
                "reference_answer_available": True,
            }

            write_json(task_dir / "data" / "meta_data.json", metadata)
            write_json(task_dir / "evaluation" / "metrics.json", metrics)
            task_json = make_task_json(row, table_bindings)
            task_json["table_schemas"] = table_schemas
            write_json(task_dir / "task.json", task_json)
            readme_context = {"table_bindings": table_bindings}
            write_text(task_dir / "README.md", render_readme(row, readme_context))
            write_text(task_dir / "requirements.txt", "\n".join(DEFAULT_REQUIREMENTS))
            write_text(task_dir / "main.py", render_main())
            write_text(task_dir / "evaluation" / "prefix.py", str(row.get("code_histories") or "# No prefix context.\n"))
            write_text(task_dir / "evaluation" / "reference_answer.py", str(row.get("reference_answer") or ""))
            write_text(task_dir / "evaluation" / "test_cases.py", str(row.get("test_cases") or ""))
            write_text(task_dir / "evaluation" / "run_reference.py", RUN_REFERENCE_TEMPLATE)
            write_text(
                task_dir / "evaluation" / "reference_outputs" / "README.md",
                "Reference outputs are generated when the task runner is executed.",
            )

            manifest_tasks.append(
                {
                    "task_id": task_id,
                    "study_id": study_id,
                    "question_id": question_id,
                    "study_type": str(row.get("study_types", "")),
                    "analysis_types": analysis_types,
                    "table_count": len(table_bindings),
                }
            )

        manifest = {
            "benchmark": "BioDSBench-Python",
            "layout": "imaging-101-compatible",
            "task_count": len(rows),
            "study_count": len({str(row["study_ids"]) for row in rows}),
            "created_at_utc": datetime.now(timezone.utc).isoformat(),
            "source_tasks_jsonl": str(args.tasks_jsonl),
            "source_schema_jsonl": str(args.schema_jsonl),
            "source_data_root": str(args.data_root),
            "notes": [
                "Notebook files are intentionally omitted.",
                "Each task contains data/meta_data.json and evaluation/metrics.json.",
                "Each task-level workdir directory contains the CSV files expected at /workdir during evaluation.",
            ],
            "tasks": manifest_tasks,
        }
        write_json(tmp_root / "manifest.json", manifest)
        write_text(
            tmp_root / "README.md",
            textwrap.dedent(
                f"""\
                # BioDSBench Python Imaging-101 Layout

                This directory packages {len(rows)} BioDSBench Python tasks in a task-per-directory
                layout aligned with `imaging-101/tasks/SSNP_ODT`.

                Each task has:

                - `README.md`
                - `main.py`
                - `requirements.txt`
                - `data/meta_data.json`
                - `workdir/*.csv`
                - `evaluation/metrics.json`
                - `evaluation/reference_answer.py`
                - `evaluation/test_cases.py`

                Notebook files are not included.
                """
            ),
        )

        if converted_root.exists():
            shutil.rmtree(converted_root)

        if output_root.exists():
            backup = output_root.with_name(
                f"{output_root.name}.bak.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            output_root.rename(backup)
            print(f"Existing output moved to {backup}")
        tmp_root.rename(output_root)
        return output_root
    except Exception:
        if tmp_root.exists():
            shutil.rmtree(tmp_root)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--tasks-jsonl", required=True, type=Path)
    parser.add_argument("--schema-jsonl", required=True, type=Path)
    parser.add_argument("--data-root", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    output = build(args)
    print(f"Packaged BioDSBench tasks at {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
