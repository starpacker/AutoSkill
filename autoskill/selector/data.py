import json
from pathlib import Path
from typing import Any, Dict


def load_json(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_inputs(cfg):
    idx, sim, model, types = map(load_json, [cfg.results_index, cfg.similarity,
                                               cfg.model, cfg.task_types])
    baselines = {}
    for task, value in idx.get("baselines", {}).items():
        if isinstance(value, dict):
            value = next(iter(value.values()), 0)
        baselines[task] = float(value) / 100.0 if float(value) > 1 else float(value)
    transfers = idx.get("transfers", [])
    return baselines, transfers, sim, model, types
