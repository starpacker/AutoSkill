import unittest
from pathlib import Path

import run_within_gemini_pair_controls as runner


class WithinGeminiPairControlsTest(unittest.TestCase):
    def test_selects_seven_within_category_pairs(self):
        self.assertEqual(
            runner.PAIRS,
            [
                ("da-8-1", "da-8-3"),
                ("da-4-1", "da-4-7"),
                ("da-13-1", "da-13-6"),
                ("da-13-1", "da-13-5"),
                ("da-15-1", "da-15-7"),
                ("da-18-5", "da-18-7"),
                ("da-19-3", "da-19-4"),
            ],
        )
        for source, target in runner.PAIRS:
            self.assertEqual(source.split("-")[1], target.split("-")[1])

    def test_builds_both_paired_arms(self):
        arms = runner.build_arms("da-19-3", "da-19-4")
        self.assertEqual([arm["control_type"] for arm in arms], ["generalized", "raw"])
        self.assertEqual(arms[0]["skill_name"], "generalized-within-gemini-da-19-3")
        self.assertEqual(arms[1]["skill_name"], "raw-within-gemini-da-19-3")

    def test_uses_expected_models(self):
        self.assertEqual(runner.SOLVER_MODEL, "Vendor3/DeepSeek-V4-Flash")
        self.assertEqual(runner.JUDGE_MODEL, "Vendor2/Gemini-3.1-pro")

    def test_treats_missing_model_channel_as_retryable(self):
        self.assertTrue(
            runner.is_retryable_failure_text(
                "API Error: 400 no available channel for model: DeepSeek-V4-Flash"
            )
        )

    def test_raw_skill_path_uses_source_oracle_bundle(self):
        self.assertEqual(
            runner.raw_skill_dir("da-19-3"),
            Path("/data/yjh/biomnibench-skill-bundles/da-19-3/skills/oracle-da-19-3"),
        )


if __name__ == "__main__":
    unittest.main()
