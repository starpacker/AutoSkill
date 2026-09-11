import json
from pathlib import Path

from autoskill.prune import prune_skill
from autoskill.selector import SelectorConfig, V10Selector


def test_prune_removes_explicit_operation_block_only():
    text = (
        "# Skill\n\n"
        "<!-- ORACLE_OP_START op_010_contract -->\n"
        "keep this\n"
        "<!-- ORACLE_OP_END op_010_contract -->\n\n"
        "<!-- ORACLE_OP_START op_020_notes -->\n"
        "remove this\n"
        "<!-- ORACLE_OP_END op_020_notes -->"
    )
    result = prune_skill(text, drop_operation_ids=["op_020_notes"])
    assert "remove this" not in result
    assert "keep this" in result


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
