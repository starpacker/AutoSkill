"""
Ablation study for v7 components.

Tests each component independently to understand individual contributions.
"""
import json, sys, os
sys.path.insert(0, '/data/yjh/skill-transfer-eval')

from skill_selector.v7_data import load_records, lotocv_split, TransferRecord
from skill_selector.v7_model import (
    fit_baseline_curve, compute_skill_residuals, shrink_estimates,
    predict_score, select_best_skill, build_pair_history, build_pair_stats
)
from skill_selector.evaluate_v7 import run_lotocv, compute_metrics, print_metrics
from collections import defaultdict
from typing import Dict, List, Optional, Tuple, Callable

# Load data
records = load_records()
available_skills = {s: 'available' for s in set(r.source for r in records)}
print(f'Loaded {len(records)} records, {len(available_skills)} sources')

# ============================================================
# Ablation: run LOTOCV with different model configurations
# ============================================================

def run_ablation_lotocv(
    records, available_skills, k=3.0, tau=2.0, lambda_compat=0.0,
    use_fbl=True, use_shrink=True, use_pair=True, use_compat=False,
    label='', verbose=True
):
    """Run LOTOCV with selected components enabled."""
    folds = lotocv_split(records)
    all_predictions = []

    for fold_idx, (held_out_target, train_records, test_records) in enumerate(folds):
        # Fit baseline curve (if enabled)
        f_hat = fit_baseline_curve(train_records) if use_fbl else (lambda bl: 0.0)

        # Compute skill residuals
        skill_stats = compute_skill_residuals(train_records, f_hat)

        # Shrink (if enabled)
        if use_shrink:
            shrink_map = shrink_estimates(skill_stats, k=k)
        else:
            shrink_map = {src: st['raw_residual'] for src, st in skill_stats.items()}

        # Build pair history
        pair_history = build_pair_history(train_records)

        # Get baselines
        baselines = {r.target: r.baseline for r in train_records}

        for r in test_records:
            if r.source not in available_skills:
                continue

            compat_tag = 0.0  # Always 0 for LOTOCV
            target_bl = baselines.get(r.target, r.baseline)
            src_shrink = shrink_map.get(r.source, 0.0)

            target_pair = pair_history.get(r.target, {})
            train_rewards = target_pair.get(r.source, [])
            n_pair = len(train_rewards)
            pair_delta = (sum(train_rewards) / n_pair) - target_bl if n_pair > 0 else None

            if use_pair:
                predicted_score = predict_score(
                    baseline_t=target_bl, f_hat=f_hat,
                    shrink_residual=src_shrink,
                )
            else:
                # No pair boost: score = f(bl) + shrink
                predicted_score = f_hat(target_bl) + src_shrink

            actual_delta = r.delta
            all_predictions.append({
                'source': r.source, 'target': r.target,
                'baseline': target_bl, 'actual_delta': actual_delta,
                'predicted_delta': predicted_score,
                'shrink': src_shrink, 'n_pair': n_pair,
            })

    return compute_metrics(all_predictions, records)


# ============================================================
# Ablation variants
# ============================================================

variants = [
    # (label, k, tau, use_fbl, use_shrink, use_pair)
    ('Full v7 (k=3, τ=2)',       3, 2,  True,  True, True),
    ('Full v7 (k=15, τ=1)',      15, 1, True,  True, True),
    ('No f(bl) (k=3)',           3, 2,  False, True, True),
    ('No f(bl) (k=15)',          15, 1, False, True, True),
    ('No pair_boost (k=3)',      3, 2,  True,  True, False),
    ('No pair_boost (k=15)',     15, 1, True,  True, False),
    ('Shrink only (k=3)',        3, 2,  False, True, False),
    ('Shrink only (k=15)',       15, 1, False, True, False),
    ('Raw residual only',        999, 1, False, False, False),
    ('Global best (k=999)',      999, 1, False, True, False),
]

print(f'\n{"="*70}')
print(f'{"Ablation Study":^70}')
print(f'{"="*70}')
print(f'{"Method":<25} {"Top-1":>8} {"Spearman":>10} {"Gate":>8} {"RMSE":>8} {"Pearson":>8}')
print(f'{"-"*25} {"-"*8} {"-"*10} {"-"*8} {"-"*8} {"-"*8}')

results = []
for label, k, tau, use_fbl, use_shrink, use_pair in variants:
    m = run_ablation_lotocv(
        records, available_skills,
        k=k, tau=tau, lambda_compat=0.0,
        use_fbl=use_fbl, use_shrink=use_shrink, use_pair=use_pair,
        label=label, verbose=False,
    )
    results.append((label, m))
    print(f'{label:<25} {m["top1_accuracy"]:>7.2%} {m["spearman_avg"]:>10.4f} '
          f'{m["gate_accuracy"]:>7.2%} {m["rmse"]:>8.4f} {m["pearson_r"]:>8.4f}')

# ============================================================
# Also test: does f(bl) actually explain variance?
# ============================================================
print(f'\n{"="*70}')
print(f'{"Baseline Curve Analysis":^70}')
print(f'{"="*70}')

# Fit on ALL data
f_hat_full = fit_baseline_curve(records)

# Predict delta from baseline alone
preds = [f_hat_full(r.baseline) for r in records]
actuals = [r.delta for r in records]
n = len(preds)
residuals = [a - p for a, p in zip(actuals, preds)]
mse_bl = sum(r*r for r in residuals) / n
var_total = sum((a - sum(actuals)/n)**2 for a in actuals) / n
r2 = 1 - mse_bl / var_total if var_total > 0 else 0
print(f'  R² of f(bl) → delta: {r2:.4f}')
print(f'  MSE of f(bl):        {mse_bl:.4f}')
print(f'  Total variance:      {var_total:.4f}')

# Show f(bl) curve points
print(f'\n  f(bl) curve samples:')
for bl in [x/100 for x in range(0, 101, 10)]:
    print(f'    f({bl:.1f}) = {f_hat_full(bl):+.4f}')

# How much does each skill's shrunk residual vary?
print(f'\n  Skill shrunk residuals (k=3):')
skill_stats = compute_skill_residuals(records, f_hat_full)
shrink_map = shrink_estimates(skill_stats, k=3)
for src, val in sorted(shrink_map.items(), key=lambda x: -x[1]):
    st = skill_stats[src]
    print(f'    {src:<20} n={st["n"]:>2d}  raw={st["raw_residual"]:+.4f}  shrunk={val:+.4f}')

# ============================================================
# Pair history analysis
# ============================================================
print(f'\n{"="*70}')
print(f'{"Pair History Analysis":^70}')
print(f'{"="*70}')

pair_history = build_pair_history(records)
pair_stats = build_pair_stats(records)
pair_count = sum(len(v) for tgt in pair_history.values() for v in tgt.values())
print(f'  Total pairs in history: {pair_count}')

# For each target, how many sources have pair history?
for target, srcs in sorted(pair_history.items()):
    n_srcs = len(srcs)
    total_pairs = sum(len(v) for v in srcs.values())
    if total_pairs > 0:
        print(f'  {target:<20} {n_srcs:>2d} sources, {total_pairs:>2d} pairs')

# ============================================================
# Summary
# ============================================================
print(f'\n{"="*70}')
print(f'{"SUMMARY":^70}')
print(f'{"="*70}')

# Sort by Top-1 then RMSE
results.sort(key=lambda x: (-x[1]['top1_accuracy'], x[1]['rmse']))
print(f'{"Method":<25} {"Top-1":>8} {"Spearman":>10} {"Gate":>8} {"RMSE":>8} {"Pearson":>8}')
print(f'{"-"*25} {"-"*8} {"-"*10} {"-"*8} {"-"*8} {"-"*8}')
for label, m in results:
    print(f'{label:<25} {m["top1_accuracy"]:>7.2%} {m["spearman_avg"]:>10.4f} '
          f'{m["gate_accuracy"]:>7.2%} {m["rmse"]:>8.4f} {m["pearson_r"]:>8.4f}')