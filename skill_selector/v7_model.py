"""
v7_model — Core statistical models for SmartSelector v7.

Isotonic regression (PAVA), James-Stein shrinkage, and the scoring formula.
All pure Python / stdlib, no external deps.

v7.1 updates:
- ALL data included (not just Gemini) — much larger training set
- Per-type offsets added — generalized-transfer gets a boost vs expand-within
- Reduced k (shrinkage) — less aggressive toward zero

Components:
  1. fit_baseline_curve()     — isotonic regression of baseline → delta
  2. compute_skill_residuals() — per-skill baseline-adjusted residuals
  3. shrink_estimates()       — James-Stein / Empirical Bayes shrinkage
  4. compute_type_offsets()   — per-transfer-type average delta offset
  5. predict_score()          — v7.1 scoring: f(bl) + shrink + type_offset
  6. Serialization            — model_to_json / model_from_json
"""

import json
from collections import defaultdict
from typing import Callable, Dict, List, Optional, Tuple


# ═════════════════════════════════════════════════════════════════════════
# 1. Isotonic Regression (PAVA)
# ═════════════════════════════════════════════════════════════════════════

def _pava_isotonic(x: List[float], y: List[float]) -> Callable[[float], float]:
    """Fit a monotone non-increasing isotonic regression using PAVA.

    Pool Adjacent Violators Algorithm: processes points left-to-right,
    merging blocks that violate the monotonicity constraint.

    Args:
        x: sorted predictor values (baselines).
        y: observed values (deltas).

    Returns:
        A callable f(x_new) -> isotonic prediction.
        Clamps x_new to the observed range (no extrapolation).
    """
    n = len(x)
    if n == 0:
        return lambda x_new: 0.0
    if n == 1:
        return lambda x_new: y[0]

    # Each block: (weight, sum_y, start_x, end_x)
    # We want non-increasing: y_i >= y_{i+1}
    weights = [1.0] * n
    blocks = [[1.0, y[i], x[i], x[i]] for i in range(n)]

    # PAVA: merge adjacent blocks that violate monotonicity
    changed = True
    while changed:
        changed = False
        new_blocks = [blocks[0]]
        for i in range(1, len(blocks)):
            prev = new_blocks[-1]
            curr = blocks[i]
            # Check if prev mean < curr mean (violates non-increasing)
            prev_mean = prev[1] / prev[0]
            curr_mean = curr[1] / curr[0]
            if prev_mean < curr_mean:
                # Merge: pool prev and curr
                merged_w = prev[0] + curr[0]
                merged_sum = prev[1] + curr[1]
                merged_x_min = min(prev[2], curr[2])
                merged_x_max = max(prev[3], curr[3])
                new_blocks[-1] = [merged_w, merged_sum, merged_x_min, merged_x_max]
                changed = True
            else:
                new_blocks.append(curr)
        blocks = new_blocks

    # Build interpolation function
    # Each block has constant fitted value = mean_y
    block_means = [b[1] / b[0] for b in blocks]
    block_x_min = [b[2] for b in blocks]
    block_x_max = [b[3] for b in blocks]

    def predict(x_new: float) -> float:
        # Clamp to observed range
        if x_new <= block_x_min[0]:
            return block_means[0]
        if x_new >= block_x_max[-1]:
            return block_means[-1]
        # Find which block x_new falls into
        for i in range(len(blocks)):
            if block_x_min[i] <= x_new <= block_x_max[i]:
                return block_means[i]
        # Between blocks: interpolate
        for i in range(len(blocks) - 1):
            if block_x_max[i] < x_new < block_x_min[i + 1]:
                # Linear interpolation between adjacent blocks
                x1, y1 = block_x_max[i], block_means[i]
                x2, y2 = block_x_min[i + 1], block_means[i + 1]
                if x2 == x1:
                    return (y1 + y2) / 2
                return y1 + (y2 - y1) * (x_new - x1) / (x2 - x1)
        return block_means[-1]

    return predict


def fit_baseline_curve(
    records: List,
    n_bins: int = 10,
) -> Callable[[float], float]:
    """Fit baseline effect curve f(baseline) = E[delta | baseline].

    Uses isotonic regression (non-increasing) with bin-based preprocessing
    to reduce noise.

    Args:
        records: List of objects with .baseline and .delta attributes.
        n_bins: Number of equal-frequency bins for preprocessing.

    Returns:
        Callable f(bl) -> predicted delta for that baseline level.
    """
    if not records:
        return lambda bl: 0.0

    # Extract (baseline, delta) pairs
    pairs = [(r.baseline, r.delta) for r in records]
    pairs.sort(key=lambda p: p[0])

    if len(pairs) < n_bins:
        # Too few points, use all directly
        x = [p[0] for p in pairs]
        y = [p[1] for p in pairs]
        return _pava_isotonic(x, y)

    # Bin-based preprocessing: group into n_bins equal-frequency bins
    bin_size = len(pairs) // n_bins
    bins_x = []
    bins_y = []
    for i in range(n_bins):
        start = i * bin_size
        end = start + bin_size if i < n_bins - 1 else len(pairs)
        bin_points = pairs[start:end]
        bins_x.append(sum(p[0] for p in bin_points) / len(bin_points))
        bins_y.append(sum(p[1] for p in bin_points) / len(bin_points))

    return _pava_isotonic(bins_x, bins_y)


# ═════════════════════════════════════════════════════════════════════════
# 2. Skill Residual Computation
# ═════════════════════════════════════════════════════════════════════════

def compute_skill_residuals(
    records: List,
    f_hat: Callable[[float], float],
    type_offsets: Optional[Dict[str, float]] = None,
) -> Dict[str, dict]:
    """Compute per-skill baseline-adjusted residuals.

    HIERARCHY: source residuals are computed AFTER removing type effects.
    residual_i = delta_i - f_hat(baseline_i) - type_offsets.get(tx_type, 0)

    Args:
        records: List of objects with .baseline, .delta, .tx_type attributes.
        f_hat: Baseline effect curve.
        type_offsets: Optional dict of per-type offsets. If provided,
                       source residuals are computed after removing type effects.

    Returns:
        Dict mapping source_name -> {n, raw_residual, var_residual, ...}
    """
    # Group by source
    source_residuals: Dict[str, List[float]] = defaultdict(list)
    source_deltas: Dict[str, List[float]] = defaultdict(list)

    for r in records:
        type_offset = (type_offsets or {}).get(r.tx_type, 0.0)
        residual = r.delta - f_hat(r.baseline) - type_offset
        source_residuals[r.source].append(residual)
        source_deltas[r.source].append(r.delta)

    stats = {}
    for src, residuals in source_residuals.items():
        n = len(residuals)
        mean_res = sum(residuals) / n
        var_res = sum((v - mean_res) ** 2 for v in residuals) / n
        std_res = var_res ** 0.5

        deltas = source_deltas[src]
        helpful = sum(1 for d in deltas if d > 0.05)
        harmful = sum(1 for d in deltas if d < -0.05)

        stats[src] = {
            'n': n,
            'raw_residual': round(mean_res, 4),
            'var_residual': round(var_res, 4),
            'std_residual': round(std_res, 4),
            'helpful_ratio': round(helpful / n, 3) if n > 0 else 0.0,
            'harmful_ratio': round(harmful / n, 3) if n > 0 else 0.0,
        }

    return stats


# ═════════════════════════════════════════════════════════════════════════
# 3. James-Stein Shrinkage
# ═════════════════════════════════════════════════════════════════════════

def shrink_estimates(
    skill_stats: Dict[str, dict],
    k: float = 8.0,
) -> Dict[str, float]:
    """Apply James-Stein shrinkage to per-skill residual estimates.

    shrunk_s = (n_s * raw_residual_s + k * 0) / (n_s + k)

    Shrinkage target is 0 (neutral prior: after baseline adjustment,
    average skill has no extra gain).

    Args:
        skill_stats: Output from compute_skill_residuals().
        k: Shrinkage strength. Higher k = more shrinkage toward 0.
           k=8 is optimal via LOTOCV (top-1=88.46%, gate=96.15%).

    Returns:
        Dict mapping source_name -> shrunk_residual.
    """
    shrunk = {}
    for src, st in skill_stats.items():
        n = st['n']
        raw = st['raw_residual']
        shrunk[src] = round((n * raw + k * 0.0) / (n + k), 4)
    return shrunk


# ═════════════════════════════════════════════════════════════════════════
# 4. Per-Type Offsets
# ═════════════════════════════════════════════════════════════════════════

def compute_type_offsets(
    records: List,
    f_hat: Callable[[float], float],
    k_type: float = 15.0,
    source_raw_residuals: Optional[Dict[str, float]] = None,
) -> Dict[str, float]:
    """Compute per-transfer-type offsets.

    HIERARCHY:
      1. f(bl) — baseline effect
      2. source_raw_residual — raw source effect (delta - f(bl), per source mean)
      3. type_offset — residual after baseline + source effect

    Args:
        records: List of TransferRecord objects.
        f_hat: Baseline effect curve.
        k_type: Shrinkage strength for type offsets.
        source_raw_residuals: Dict of source -> raw mean residual.
                              If provided, type_offset = delta - f(bl) - source_raw.
                              This prevents type_offset from stealing source signal.

    Returns:
        Dict mapping tx_type -> shrunk centered offset.
    """
    type_residuals: Dict[str, List[float]] = defaultdict(list)
    for r in records:
        residual = r.delta - f_hat(r.baseline)
        # Remove source effect if available
        if source_raw_residuals:
            residual -= source_raw_residuals.get(r.source, 0.0)
        type_residuals[r.tx_type].append(residual)

    # Apply James-Stein shrinkage to each type offset
    offsets = {}
    type_counts = {}
    for tx_type, residuals in type_residuals.items():
        n = len(residuals)
        type_counts[tx_type] = n
        raw_offset = sum(residuals) / n if n > 0 else 0.0
        shrunk = (n * raw_offset + k_type * 0.0) / (n + k_type) if n > 0 else 0.0
        offsets[tx_type] = shrunk

    # Center: weighted mean = 0
    total_n = sum(type_counts.values())
    if total_n > 0:
        weighted_mean = sum(offsets[t] * type_counts[t] for t in offsets) / total_n
        for t in offsets:
            offsets[t] = round(offsets[t] - weighted_mean, 4)
    else:
        for t in offsets:
            offsets[t] = round(offsets[t], 4)

    return offsets


# ═════════════════════════════════════════════════════════════════════════
# 5. Scoring with Type Awareness
# ═════════════════════════════════════════════════════════════════════════

def predict_score(
    baseline_t: float,
    f_hat: Callable[[float], float],
    shrink_residual: float,
    type_offset: float = 0.0,
) -> float:
    """Compute v7.1 score for a single (target, source, type) triple.

    score(t, s, type) = f_hat(baseline_t) + shrink_residual_s + type_offset[type]

    "No transfer" corresponds to score = 0.0 (no skill, no delta).

    Args:
        baseline_t: Target task's baseline score.
        f_hat: Baseline effect curve function.
        shrink_residual: James-Stein shrunk residual for this source.
        type_offset: Per-transfer-type offset (default 0.0 for backward compat).

    Returns:
        The predicted delta if this source skill is applied to the target.
    """
    return f_hat(baseline_t) + shrink_residual + type_offset


def select_best_skill(
    baseline_t: float,
    f_hat: Callable[[float], float],
    shrink_map: Dict[str, float],
    available_skills: Dict[str, str],
    type_offset: float = 0.0,
    min_score_threshold: float = 0.05,
) -> Tuple[Optional[str], float, float]:
    """Select the best skill for a target task using v7.1 scoring.

    "No transfer" is included as a candidate with score = 0.0.
    A minimum score threshold filters out noise-level predictions
    (below the smallest meaningful positive delta in training data).

    Args:
        baseline_t: Target baseline.
        f_hat: Baseline effect curve.
        shrink_map: shrunk_residual per source.
        available_skills: {source: path_to_skill}.
        type_offset: Per-transfer-type offset (default 0.0).
        min_score_threshold: Minimum score to recommend a skill.
                             Default 0.05 (hard rejection threshold).
                             Skills below this score are not deployed.

    Returns:
        Tuple of (best_source, best_score, no_transfer_score).
        best_source may be None if "no transfer" wins.
        no_transfer_score is always 0.0 for reference.
    """
    NO_TRANSFER_SCORE = 0.0
    best_source = None
    best_score = NO_TRANSFER_SCORE

    for src_name in available_skills:
        src_shrink = shrink_map.get(src_name, 0.0)
        score = predict_score(
            baseline_t=baseline_t,
            f_hat=f_hat,
            shrink_residual=src_shrink,
            type_offset=type_offset,
        )
        if score > best_score:
            best_score = score
            best_source = src_name

    if best_score <= NO_TRANSFER_SCORE:
        return None, NO_TRANSFER_SCORE, NO_TRANSFER_SCORE

    # Filter noise-level predictions
    if best_score < min_score_threshold:
        return None, NO_TRANSFER_SCORE, NO_TRANSFER_SCORE

    return best_source, best_score, NO_TRANSFER_SCORE


# ═════════════════════════════════════════════════════════════════════════
# 5. Pair History Extraction (from records)
# ═════════════════════════════════════════════════════════════════════════

def build_pair_history(records: List) -> Dict[str, Dict[str, List[float]]]:
    """Build pair history dict from records.

    Returns:
        {target: {source: [reward_1, reward_2, ...]}}
    """
    history: Dict[str, Dict[str, List[float]]] = {}
    for r in records:
        if r.target not in history:
            history[r.target] = {}
        if r.source not in history[r.target]:
            history[r.target][r.source] = []
        history[r.target][r.source].append(r.reward)
    return history


def build_pair_stats(records: List) -> Dict[Tuple[str, str], dict]:
    """Build per-pair statistics: n, mean_delta, std_delta.

    Returns:
        {(source, target): {n, mean_delta, std_delta}}
    """
    pair_data: Dict[Tuple[str, str], List[float]] = defaultdict(list)
    for r in records:
        pair_data[(r.source, r.target)].append(r.delta)

    stats = {}
    for (src, tgt), deltas in pair_data.items():
        n = len(deltas)
        mean_d = sum(deltas) / n
        var_d = sum((d - mean_d) ** 2 for d in deltas) / n
        stats[(src, tgt)] = {
            'n': n,
            'mean_delta': round(mean_d, 4),
            'std_delta': round(var_d ** 0.5, 4),
        }
    return stats


# ═════════════════════════════════════════════════════════════════════════
# 6. Serialization (cache model to JSON)
# ═════════════════════════════════════════════════════════════════════════

def model_to_json(f_hat_points: List[Tuple[float, float]],
                  shrink_map: Dict[str, float],
                  skill_stats: Dict[str, dict],
                  baselines: Dict[str, float],
                  params: dict,
                  type_offsets: Optional[Dict[str, float]] = None) -> dict:
    """Serialize the fitted model to a JSON-serializable dict.

    f_hat_points: List of (x, y) points sampled from the fitted curve.
    """
    out = {
        'f_hat_points': [[x, y] for x, y in f_hat_points],
        'shrink_map': shrink_map,
        'skill_stats': skill_stats,
        'baselines': baselines,
        'params': params,
    }
    if type_offsets:
        out['type_offsets'] = type_offsets
    return out


def sample_f_hat(f_hat: Callable[[float], float],
                 x_min: float = 0.0,
                 x_max: float = 1.0,
                 n_points: int = 100) -> List[Tuple[float, float]]:
    """Sample the f_hat curve at regular intervals for serialization."""
    points = []
    for i in range(n_points):
        x = x_min + (x_max - x_min) * i / (n_points - 1)
        y = f_hat(x)
        points.append((x, y))
    return points


def model_from_json(data: dict) -> Tuple:
    """Restore model from serialized JSON.

    Returns:
        (f_hat_function, shrink_map, skill_stats, baselines, params, type_offsets)
    """
    points = data['f_hat_points']
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]

    # Rebuild f_hat as a linear interpolation of sampled points
    min_x = min(xs)
    max_x = max(xs)

    def f_hat(bl: float) -> float:
        if bl <= min_x:
            return ys[0]
        if bl >= max_x:
            return ys[-1]
        # Linear interpolation
        for i in range(len(xs) - 1):
            if xs[i] <= bl <= xs[i + 1]:
                if xs[i + 1] == xs[i]:
                    return ys[i]
                t = (bl - xs[i]) / (xs[i + 1] - xs[i])
                return ys[i] + t * (ys[i + 1] - ys[i])
        return ys[-1]

    type_offsets = data.get('type_offsets', {})

    return (f_hat,
            data['shrink_map'],
            data['skill_stats'],
            data['baselines'],
            data['params'],
            type_offsets)


# ═════════════════════════════════════════════════════════════════════════
# 7. Main: Quick Test
# ═════════════════════════════════════════════════════════════════════════

if __name__ == '__main__':
    from .v7_data import load_records, print_data_summary

    records = load_records()
    print_data_summary(records)

    # Fit baseline curve
    print("\n--- Fitting baseline curve ---")
    f_hat = fit_baseline_curve(records, n_bins=10)
    for bl in [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        print(f"  f_hat({bl:.1f}) = {f_hat(bl):+.4f}")

    # Compute raw residuals (delta - f(bl))
    print("\n--- Raw skill residuals (delta - f(bl)) ---")
    raw_stats = compute_skill_residuals(records, f_hat)
    source_raw = {src: st['raw_residual'] for src, st in raw_stats.items()}
    for src, st in sorted(raw_stats.items()):
        print(f"  {src:>12s}: n={st['n']:2d} raw_res={st['raw_residual']:+.4f} "
              f"std={st['std_residual']:.4f}")

    # Type offsets (from delta - f(bl) - source_raw)
    print("\n--- Type offsets (after removing source effect) ---")
    type_offsets = compute_type_offsets(records, f_hat, k_type=15.0, source_raw_residuals=source_raw)
    for tx_type, offset in sorted(type_offsets.items()):
        print(f"  {tx_type:>25s}: offset={offset:+.4f}")

    # Skill residuals AFTER type removal
    print("\n--- Skill residuals (after type removal) ---")
    skill_stats = compute_skill_residuals(records, f_hat, type_offsets=type_offsets)
    for src, st in sorted(skill_stats.items()):
        print(f"  {src:>12s}: n={st['n']:2d} raw_res={st['raw_residual']:+.4f} "
              f"std={st['std_residual']:.4f}")

    # Shrink
    print("\n--- Shrunk estimates ---")
    for k in [1, 3, 5, 10]:
        shrunk = shrink_estimates(skill_stats, k=k)
        vals = [f"{src}={shrunk[src]:+.4f}" for src in sorted(shrunk)]
        print(f"  k={k:2d}: {' '.join(vals)}")