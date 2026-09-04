from __future__ import annotations

import argparse
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
SUBSTITUTION_COLUMNS = ["A>C", "A>G", "A>T", "C>A", "C>G", "C>T", "CC>TT", "Others"]
KNOWN_SUBSTITUTIONS = set(SUBSTITUTION_COLUMNS[:-1])


def _load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


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


def determine_substitution(reference: str, alternate: str) -> str | None:
    if reference == alternate:
        return None
    substitution = f"{reference}>{alternate}"
    return substitution if substitution in KNOWN_SUBSTITUTIONS else "Others"


def compute_reference_dataframe(input_dir: Path) -> pd.DataFrame:
    data_mutations = pd.read_csv(input_dir / "data_mutations.csv")
    data_mutations["Substitution1"] = data_mutations.apply(
        lambda row: determine_substitution(row["Reference_Allele"], row["Tumor_Seq_Allele1"]), axis=1
    )
    data_mutations["Substitution2"] = data_mutations.apply(
        lambda row: determine_substitution(row["Reference_Allele"], row["Tumor_Seq_Allele2"]), axis=1
    )
    data_mutations["Substitution"] = data_mutations["Substitution1"].combine_first(data_mutations["Substitution2"])
    data_mutations = data_mutations.dropna(subset=["Substitution"])
    ratios = data_mutations.groupby(["Tumor_Sample_Barcode", "Substitution"]).size().unstack(fill_value=0)
    ratios = ratios.reindex(columns=SUBSTITUTION_COLUMNS, fill_value=0)
    return ratios.div(ratios.sum(axis=1), axis=0)


def _load_submission_dataframe(script_path: Path, input_dir: Path) -> pd.DataFrame | None:
    if not script_path.exists():
        return None

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
    value = namespace.get("substitution_ratios")
    return value if isinstance(value, pd.DataFrame) else None


def _plot_heatmap(df: pd.DataFrame, out_path: Path, title: str, cmap: str = "magma") -> None:
    fig, ax = plt.subplots(figsize=(10, 12))
    image = ax.imshow(df.to_numpy(dtype=float), aspect="auto", cmap=cmap, vmin=0.0)
    ax.set_title(title)
    ax.set_xlabel("Substitution type")
    ax.set_ylabel("Tumor sample")
    ax.set_xticks(range(len(df.columns)))
    ax.set_xticklabels([str(x) for x in df.columns], rotation=45, ha="right")
    ax.set_yticks(range(len(df.index)))
    ax.set_yticklabels([str(x) for x in df.index], fontsize=7)
    fig.colorbar(image, ax=ax, label="Ratio")
    fig.tight_layout()
    fig.savefig(out_path, dpi=150)
    plt.close(fig)


def _plot_stacked(df: pd.DataFrame, out_path: Path, title: str) -> None:
    ax = df.plot(kind="bar", stacked=True, figsize=(14, 7), width=0.85)
    ax.set_title(title)
    ax.set_xlabel("Tumor sample")
    ax.set_ylabel("Ratio")
    ax.set_ylim(0.0, 1.02)
    ax.legend(title="Substitution", bbox_to_anchor=(1.02, 1.0), loc="upper left")
    ax.figure.tight_layout()
    ax.figure.savefig(out_path, dpi=150)
    plt.close(ax.figure)


def _submission_path(submission: Path, case_id: str) -> Path:
    if submission.suffix == ".py":
        return submission
    return submission / f"{case_id}.py"


def visualize_case(case: dict[str, Any], submission: Path, visible_root: Path, out_dir: Path) -> dict[str, Any]:
    case_id = case["id"]
    input_dir = visible_root / case["input_dir"]
    out_dir.mkdir(parents=True, exist_ok=True)

    ref_df = compute_reference_dataframe(input_dir)
    files: list[str] = []
    ref_heatmap = out_dir / "reference_substitution_heatmap.png"
    ref_stack = out_dir / "reference_substitution_stacked_bar.png"
    _plot_heatmap(ref_df, ref_heatmap, "Reference recomputed from visible data: substitution ratios")
    _plot_stacked(ref_df, ref_stack, "Reference recomputed from visible data: substitution ratio composition")
    files.extend([ref_heatmap.name, ref_stack.name])

    sub_df = _load_submission_dataframe(_submission_path(submission, case_id), input_dir)
    summary: dict[str, Any] = {"case_id": case_id, "files": files, "submission_found": sub_df is not None}
    if sub_df is not None:
        sub_df = sub_df.reindex(index=ref_df.index, columns=ref_df.columns)
        sub_heatmap = out_dir / "submitted_substitution_heatmap.png"
        error_heatmap = out_dir / "absolute_error_heatmap.png"
        _plot_heatmap(sub_df, sub_heatmap, "Agent submission: substitution ratios")
        _plot_heatmap((sub_df - ref_df).abs(), error_heatmap, "Absolute error: submitted vs recomputed reference", cmap="viridis")
        files.extend([sub_heatmap.name, error_heatmap.name])
        summary["max_abs_error"] = float((sub_df - ref_df).abs().max().max())
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Visualize 25303977_0 DataFrame-script outputs.")
    parser.add_argument("--submission", type=Path, default=Path("outputs"))
    parser.add_argument("--cases", type=Path, default=Path("visible_data/cases.json"))
    parser.add_argument("--eval-data", type=Path, default=Path("evaluation/data"), help="Unused compatibility argument.")
    parser.add_argument("--out-dir", type=Path, default=Path("visualization/case_000"))
    parser.add_argument("--case-id", default="case_000")
    args = parser.parse_args()

    cases_cfg = _load_json(args.cases)
    visible_root = args.cases.resolve().parent
    cases = [case for case in cases_cfg.get("cases", []) if args.case_id in {"all", case["id"]}]
    summaries = [visualize_case(case, args.submission, visible_root, args.out_dir if len(cases) == 1 else args.out_dir / case["id"]) for case in cases]
    args.out_dir.mkdir(parents=True, exist_ok=True)
    (args.out_dir / "summary.json").write_text(json.dumps({"cases": summaries}, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"cases": summaries}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
