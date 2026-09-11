"""Build the lightweight V10 confidence model from observed transfers."""

import json
from pathlib import Path
from statistics import mean


def train_model(results_index: Path, output: Path) -> dict:
    idx = json.loads(results_index.read_text(encoding="utf-8"))
    baselines = idx.get("baselines", {})
    transfers = idx.get("transfers", [])
    source_deltas = {}
    points = []
    for row in transfers:
        target, source = row.get("target"), row.get("source")
        if not target or not source:
            continue
        base = baselines.get(target, 0)
        if isinstance(base, dict):
            base = next(iter(base.values()), 0)
        base = float(base) / 100 if float(base) > 1 else float(base)
        reward = float(row.get("reward", 0))
        source_deltas.setdefault(source, []).append(reward - base)
        points.append([base, reward])
    model = {
        "source_shrink": {s: mean(v) for s, v in source_deltas.items()},
        "isotonic_points": sorted(points),
        "training_rows": len(points),
    }
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(model, indent=2), encoding="utf-8")
    return model
