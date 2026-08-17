# BioDSBench Imaging-101 Packaging Notes

## Server Paths

- Packaged tasks: `/data/yjh/BioDSBench_imaging101_format`
- Packaging tools: `/data/yjh/biodsbench_packaging_tools`
- Python source tasks: `/data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl`
- Table schemas: `/data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_task_table_schemas.jsonl`
- Source data root: `/data/yjh/BioDSBench_hf/data_files/datasets`

## Required Layout

Each task should contain:

- `README.md`
- `main.py`
- `requirements.txt`
- `task.json`
- `data/meta_data.json`
- `workdir/*.csv`
- `evaluation/metrics.json`
- `evaluation/prefix.py`
- `evaluation/reference_answer.py`
- `evaluation/test_cases.py`
- `evaluation/run_reference.py`

`data/` should contain only `meta_data.json`. Do not recreate `data/workdir/`; task input CSVs live in the task-level `workdir/`.

## Meta-data Rule

Follow imaging-101 style: `data/meta_data.json` is a flat JSON object containing top-level analysis parameters plus `description`.

Do not put BioDSBench provenance/catalog fields in `meta_data.json`. Fields such as `n_tables`, `table_shapes`, `n_assertions`, `input_format`, `workdir`, `study_id`, `dataset_url`, or `analysis_types` belong in `task.json`, `metrics.json`, or the README.

Example:

```json
{
  "gain_threshold": 0.2,
  "loss_threshold": -0.2,
  "description": "BioDSBench Python coding task using cBioPortal-style tabular data. Load CSV inputs from the task-level workdir directory, mounted as /workdir in a sandbox."
}
```

## Hyperparameter Extraction

The build script extracts simple top-level literal assignments from `code_histories` and `reference_answer`.

Keep values that define analysis choices, for example:

- thresholds and cutoffs: `gain_threshold = 0.2`
- selected genes or gene sets: `high_risk_genes = ["TP53", "KRAS"]`
- mutation type sets or mappings
- response categories and disease stages

Exclude runtime plumbing and outputs, for example:

- path variables: `INPUT_DIR`, `data_dir`, `*_path`
- output containers: `results`, `results_df`, `kmf_curves`
- empty result lists such as `os_p_values = []`

For task `28985567_3`, the validator explicitly checks that `gain_threshold = 0.2` and `loss_threshold = -0.2` are present in `data/meta_data.json`.

## Commands

Run tests on the server:

```bash
cd /data/yjh/biodsbench_packaging_tools
python3 -m unittest test_biodsbench_imaging101
```

Regenerate the packaged dataset:

```bash
python3 /data/yjh/biodsbench_packaging_tools/build_biodsbench_imaging101.py \
  --tasks-jsonl /data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl \
  --schema-jsonl /data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_task_table_schemas.jsonl \
  --data-root /data/yjh/BioDSBench_hf/data_files/datasets \
  --output /data/yjh/BioDSBench_imaging101_format \
  --force
```

Validate the generated dataset:

```bash
python3 /data/yjh/biodsbench_packaging_tools/validate_biodsbench_imaging101.py \
  --root /data/yjh/BioDSBench_imaging101_format \
  --expected-jsonl /data/yjh/BioDSA/benchmarks/BioDSBench-Python/dataset/python_tasks_with_class.jsonl
```
