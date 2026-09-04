from __future__ import annotations

import argparse
import ast
import builtins
import json
from pathlib import Path
from typing import Any

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

_REAL_READ_CSV = pd.read_csv
_REAL_OPEN = builtins.open


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def _submission_path(submission: Path, case_id: str, schema: dict[str, Any], case: dict[str, Any]) -> Path:
    if submission.suffix == ".py":
        return submission
    template = schema.get("path_template") or case.get("expected_output") or "outputs/{case_id}.py"
    return submission / Path(template.format(case_id=case_id)).name


def _redirect_path(path: Any, input_dir: Path) -> Any:
    if not isinstance(path, (str, Path)):
        return path
    text = str(path).replace("\\", "/")
    for prefix in ("/workdir/", "./workdir/", "workdir/"):
        if text.startswith(prefix):
            return str(input_dir / text[len(prefix):])
    if text in {"/workdir", "./workdir", "workdir"}:
        return str(input_dir)
    return path


def _execute_submission(script_path: Path, input_dir: Path) -> dict[str, Any]:
    def read_csv_with_redirect(filepath_or_buffer: Any, *args: Any, **kwargs: Any) -> pd.DataFrame:
        return _REAL_READ_CSV(_redirect_path(filepath_or_buffer, input_dir), *args, **kwargs)

    def open_with_redirect(file: Any, *args: Any, **kwargs: Any) -> Any:
        return _REAL_OPEN(_redirect_path(file, input_dir), *args, **kwargs)

    namespace: dict[str, Any] = {"pd": pd, "__file__": str(script_path), "__name__": "__submission__"}
    old_read_csv = pd.read_csv
    old_open = builtins.open
    old_show = plt.show
    try:
        pd.read_csv = read_csv_with_redirect
        builtins.open = open_with_redirect
        plt.show = lambda *args, **kwargs: None
        exec(compile(script_path.read_text(encoding="utf-8"), str(script_path), "exec"), namespace)
    finally:
        pd.read_csv = old_read_csv
        builtins.open = old_open
        plt.show = old_show
    return namespace


def _run_test_cases(test_path: Path, namespace: dict[str, Any]) -> tuple[list[dict[str, Any]], list[str]]:
    source = test_path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=str(test_path))
    assertions: list[dict[str, Any]] = []
    errors: list[str] = []
    for node in tree.body:
        if not isinstance(node, ast.Assert):
            exec(compile(ast.Module(body=[node], type_ignores=[]), str(test_path), "exec"), namespace)
            continue
        text = ast.get_source_segment(source, node) or f"assertion_{len(assertions) + 1}"
        try:
            passed = bool(eval(compile(ast.Expression(node.test), str(test_path), "eval"), namespace))
        except Exception as exc:
            passed = False
            errors.append(f"{text}: {type(exc).__name__}: {exc}")
        if not passed and not any(text in err for err in errors):
            errors.append(f"{text}: assertion failed")
        assertions.append({"index": len(assertions) + 1, "passed": passed, "assertion": text})
    return assertions, errors


def evaluate_case(case: dict[str, Any], submission: Path, schema: dict[str, Any], public_root: Path, evaluation_root: Path) -> dict[str, Any]:
    case_id = case["id"]
    input_dir = public_root / "visible_data" / case["input_dir"]
    output_path = _submission_path(submission, case_id, schema, case)
    test_path = evaluation_root / "test_cases.py"
    result: dict[str, Any] = {"case_id": case_id, "status": "fail", "format": {"status": "pass"}, "passed": False, "assertions": [], "errors": []}

    if not output_path.exists():
        result["errors"].append(f"Missing submission script: {output_path}")
        return result
    if not input_dir.exists():
        result["errors"].append(f"Missing visible input directory: {input_dir}")
        return result
    if not test_path.exists():
        result["errors"].append(f"Missing test cases: {test_path}")
        return result

    try:
        namespace = _execute_submission(output_path, input_dir)
        value = namespace.get("substitution_ratios")
        if value is None:
            result["errors"].append("Submission did not define substitution_ratios")
            return result
        if not isinstance(value, pd.DataFrame):
            result["errors"].append("substitution_ratios must be a pandas DataFrame")
            return result
        assertions, errors = _run_test_cases(test_path, namespace)
        result["assertions"] = assertions
        result["errors"].extend(errors)
    except Exception as exc:
        result["errors"].append(f"Failed to evaluate submission: {type(exc).__name__}: {exc}")
        return result

    passed_count = sum(1 for item in result["assertions"] if item["passed"])
    total_count = len(result["assertions"])
    pass_rate = float(passed_count / total_count) if total_count else 0.0
    result["assertion_summary"] = {
        "assertions_passed": passed_count,
        "assertions_total": total_count,
        "assertion_pass_rate": pass_rate,
    }
    result["metrics"] = [
        {"name": "assertions_passed", "status": "pass" if passed_count == total_count else "fail", "value": passed_count, "threshold": total_count},
        {"name": "assertion_pass_rate", "status": "pass" if pass_rate >= 1.0 else "fail", "value": pass_rate, "threshold": 1.0},
    ]
    result["passed"] = total_count > 0 and passed_count == total_count and not result["errors"]
    result["status"] = "pass" if result["passed"] else "fail"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Judge 25303977_0 DataFrame-script submissions.")
    parser.add_argument("--submission", type=Path, default=Path("outputs"))
    parser.add_argument("--submission-dir", type=Path, default=None, help="Backward-compatible alias for --submission.")
    parser.add_argument("--cases", type=Path, default=Path("visible_data/cases.json"))
    parser.add_argument("--schema", type=Path, default=Path("output_schema.json"))
    parser.add_argument("--metrics", type=Path, default=Path("evaluation/metrics.json"))
    parser.add_argument("--eval-data", type=Path, default=Path("evaluation/data"), help="Unused compatibility argument.")
    parser.add_argument("--result", type=Path, default=Path("judge_result.json"))
    parser.add_argument("--feedback-level", default=None)
    args = parser.parse_args()

    submission = args.submission_dir if args.submission_dir is not None else args.submission
    public_root = args.cases.resolve().parents[1]
    evaluation_root = Path(__file__).resolve().parent
    cases_cfg = _load_json(args.cases)
    schema = _load_json(args.schema)
    case_results = [evaluate_case(case, submission, schema, public_root, evaluation_root) for case in cases_cfg.get("cases", [])]
    passed = bool(case_results) and all(case["passed"] for case in case_results)
    output = {
        "version": 1,
        "task_id": "25303977_0",
        "status": "pass" if passed else "fail",
        "passed": passed,
        "cases": case_results,
    }
    if args.result.parent != Path(""):
        args.result.parent.mkdir(parents=True, exist_ok=True)
    args.result.write_text(json.dumps(output, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(output, indent=2))
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
