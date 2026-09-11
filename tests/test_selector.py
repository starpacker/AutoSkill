import json
from pathlib import Path

from autoskill.prune import prune_skill
from autoskill.selector import SelectorConfig, V10Selector


def test_prune_removes_reference_section():
    text = "# Skill\n\n## Workflow\nDo work.\n\n## Reference Evidence\nsecret"
    assert "secret" not in prune_skill(text)


def test_selector_direct_observation(tmp_path: Path):
    (tmp_path / "results.json").write_text(json.dumps({
        "baselines": {"target": 20}, "transfers": [
            {"source": "source", "target": "target", "reward": 0.8,
             "type": "generalized-transfer"}]}))
    (tmp_path / "sim.json").write_text("{}")
    (tmp_path / "model.json").write_text("{}")
    (tmp_path / "types.json").write_text(json.dumps({"source": "same", "target": "same"}))
    cfg = SelectorConfig(tmp_path / "results.json", tmp_path / "sim.json",
                         tmp_path / "model.json", tmp_path / "types.json")
    assert V10Selector(cfg).select("target", {"source": "skill.md"})[0] == "source"
