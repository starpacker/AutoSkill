#!/usr/bin/env python3
"""Regression tests for BioDSBench imaging-101 packaging helpers."""

from __future__ import annotations

import unittest
import json
import tempfile
from pathlib import Path

from build_biodsbench_imaging101 import (
    collect_hyperparameters,
    extract_hyperparameters_from_code,
    make_meta_data,
)
from validate_biodsbench_imaging101 import validate


class HyperparameterExtractionTests(unittest.TestCase):
    def test_extracts_thresholds_and_ignores_runtime_outputs(self) -> None:
        code = """
import pandas as pd

data_dir = "/workdir"
gain_threshold = 0.2
loss_threshold = -0.2
results_df = []
kmf_curves = {}
patient_cna.to_csv("patient_cna.csv")
"""

        self.assertEqual(
            extract_hyperparameters_from_code(code),
            {
                "gain_threshold": 0.2,
                "loss_threshold": -0.2,
            },
        )

    def test_collects_analysis_category_parameters_from_prefix_and_reference(self) -> None:
        row = {
            "code_histories": """
INPUT_DIR = "/workdir"
silent_mutations = ["Silent"]
missense_mutations = ["Missense_Mutation"]
gain_threshold = 0.1
""",
            "reference_answer": """
gain_threshold = 0.2
loss_threshold = -0.2
high_risk_genes = ["TP53", "KRAS", "CDKN2A"]
""",
        }

        self.assertEqual(
            collect_hyperparameters(row),
            {
                "silent_mutations": ["Silent"],
                "missense_mutations": ["Missense_Mutation"],
                "gain_threshold": 0.2,
                "loss_threshold": -0.2,
                "high_risk_genes": ["TP53", "KRAS", "CDKN2A"],
            },
        )

    def test_meta_data_uses_imaging101_style_top_level_parameters(self) -> None:
        row = {
            "code_histories": "",
            "reference_answer": """
gain_threshold = 0.2
loss_threshold = -0.2
""",
        }

        metadata = make_meta_data(row)

        self.assertEqual(metadata["gain_threshold"], 0.2)
        self.assertEqual(metadata["loss_threshold"], -0.2)
        self.assertIn("description", metadata)
        self.assertNotIn("hyperparameters", metadata)
        self.assertNotIn("n_tables", metadata)
        self.assertNotIn("table_shapes", metadata)


class ValidatorTests(unittest.TestCase):
    def test_accepts_top_level_parameter_meta_data(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "packaged"
            task_dir = root / "tasks" / "28985567_3"
            (task_dir / "data").mkdir(parents=True)
            (task_dir / "evaluation").mkdir()
            (task_dir / "workdir").mkdir()

            row = {
                "unique_question_ids": "28985567_3",
                "tables": ["data_log2_cna.csv"],
                "code_histories": "",
                "reference_answer": "gain_threshold = 0.2\nloss_threshold = -0.2\n",
                "test_cases": "assert True\n",
            }
            expected_jsonl = Path(tmp) / "python_tasks_with_class.jsonl"
            expected_jsonl.write_text(json.dumps(row) + "\n", encoding="utf-8")

            for relative in (
                "README.md",
                "main.py",
                "requirements.txt",
                "evaluation/prefix.py",
                "evaluation/reference_answer.py",
                "evaluation/test_cases.py",
                "evaluation/run_reference.py",
            ):
                (task_dir / relative).write_text("# placeholder\n", encoding="utf-8")

            (task_dir / "task.json").write_text(
                json.dumps({"unique_question_ids": "28985567_3"}),
                encoding="utf-8",
            )
            (task_dir / "evaluation" / "metrics.json").write_text(
                json.dumps(
                    {
                        "evaluation_type": "python_assertions",
                        "test_case_count": 1,
                    }
                ),
                encoding="utf-8",
            )
            (task_dir / "data" / "meta_data.json").write_text(
                json.dumps(
                    {
                        "gain_threshold": 0.2,
                        "loss_threshold": -0.2,
                        "description": "Synthetic cBioPortal-style task.",
                    }
                ),
                encoding="utf-8",
            )
            (task_dir / "workdir" / "data_log2_cna.csv").write_text(
                "Hugo_Symbol,Entrez_Gene_Id\nTP53,7157\n",
                encoding="utf-8",
            )
            (root / "manifest.json").write_text(
                json.dumps({"task_count": 1}),
                encoding="utf-8",
            )

            self.assertEqual(validate(root, expected_jsonl), [])


if __name__ == "__main__":
    unittest.main()
