import unittest
import tempfile
from pathlib import Path
from unittest import mock

import run_raw_cross_gemini_controls as runner


class RawCrossGeminiControlsTest(unittest.TestCase):
    def test_uses_raw_oracle_skill_name(self):
        self.assertEqual(runner.skill_name("da-14-3"), "raw-cross-gemini-da-14-3")

    def test_uses_source_oracle_bundle_path(self):
        expected = Path("/data/yjh/biomnibench-skill-bundles/da-14-3/skills/oracle-da-14-3/SKILL.md")
        self.assertEqual(runner.source_skill_path("da-14-3"), expected)

    def test_pairs_are_only_gemini_scored_generalized_pairs(self):
        self.assertEqual(
            runner.PAIRS,
            [
                ("da-14-3", "da-17-5"),
                ("da-19-3", "da-13-6"),
                ("da-13-5", "da-17-5"),
                ("da-13-3", "da-15-7"),
                ("da-15-1", "da-17-3"),
                ("da-18-5", "da-19-6"),
                ("da-20-3", "da-4-7"),
            ],
        )

    def test_model_settings_match_control_requirement(self):
        self.assertEqual(runner.SOLVER_MODEL, "Vendor3/DeepSeek-V4-Flash")
        self.assertEqual(runner.JUDGE_MODEL, "Vendor2/Gemini-3.1-pro")

    def test_detects_retryable_overloaded_model_failure(self):
        text = "API Error: 400 The model is overloaded. Please try again later."
        self.assertTrue(runner.is_retryable_failure_text(text))

    def test_attempt_run_tag_keeps_first_attempt_compatible(self):
        timestamp = "20260806_011026"
        name = "raw-cross-gemini-da-14-3"
        self.assertEqual(
            runner.attempt_run_tag(timestamp, name, 1),
            "20260806_011026_raw-cross-gemini-da-14-3_rep1",
        )
        self.assertEqual(
            runner.attempt_run_tag(timestamp, name, 2),
            "20260806_011026_raw-cross-gemini-da-14-3_attempt2_rep1",
        )

    def test_deploy_copies_raw_skill_resources(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source_dir = root / "bundles" / "da-1-1" / "skills" / "oracle-da-1-1"
            source_dir.mkdir(parents=True)
            (source_dir / "SKILL.md").write_text("Read `resources/op.md`.\n")
            (source_dir / "resources").mkdir()
            (source_dir / "resources" / "op.md").write_text("details\n")

            skills_dir = root / "deployed"
            with mock.patch.object(runner, "RAW_BUNDLES_DIR", root / "bundles"), mock.patch.object(
                runner, "SKILLS_DIR", skills_dir
            ):
                ok, message = runner.deploy_skill("da-1-1", "da-2-2")

            deployed = skills_dir / "da-2-2" / "skills" / "raw-cross-gemini-da-1-1"
            self.assertTrue(ok, message)
            self.assertTrue((deployed / "SKILL.md").exists())
            self.assertEqual((deployed / "resources" / "op.md").read_text(), "details\n")


if __name__ == "__main__":
    unittest.main()
