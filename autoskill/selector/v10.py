from typing import Dict, Optional, Tuple

from .compatibility import score_params, tier
from .data import load_inputs


class V10Selector:
    """Three-phase selector: direct observation, nearest neighbor, confidence."""

    def __init__(self, config):
        self.config = config
        self.baselines, self.transfers, self.similarity, self.model, self.types = load_inputs(config)
        self.direct = {}
        for row in self.transfers:
            if row.get("type") not in (None, "generalized-transfer"):
                continue
            source, target = row.get("source"), row.get("target")
            if not source or not target:
                continue
            baseline = self.baselines.get(target, 0.5)
            delta = float(row.get("reward", 0)) - baseline
            if delta > 0.05 and (target not in self.direct or delta > self.direct[target][1]):
                self.direct[target] = (source, delta)

    def select(self, target: str, available: Dict[str, str]) -> Tuple[Optional[str], float]:
        if self.baselines.get(target, 0.5) > self.config.baseline_max:
            return None, 0.0
        if target in self.direct and self.direct[target][0] in available:
            source, delta = self.direct[target]
            bonus, _ = score_params(tier(source, target, self.types), self.config)
            if delta + bonus > 0:
                return source, delta + bonus

        candidates = []
        baseline = self.baselines.get(target, 0.5)
        points = self.model.get("isotonic_points", [[0.0, 0.0], [1.0, 0.0]])
        expected = min(points, key=lambda p: abs(float(p[0]) - baseline))[1]
        quality = self.model.get("source_shrink", {})
        for source in available:
            if source == target:
                continue
            kind = tier(source, target, self.types)
            bonus, threshold = score_params(kind, self.config)
            adjusted = float(expected) + float(quality.get(source, 0.0)) + bonus
            if adjusted >= threshold:
                candidates.append((0 if kind == "same" else 1, -adjusted, source, adjusted))
        if not candidates:
            return None, 0.0
        candidates.sort()
        _, _, source, value = candidates[0]
        return source, value
